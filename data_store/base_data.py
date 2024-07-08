"""
BaseData is the base class for AWS_S3 data handlers
"""

import enum

import logging
import random
from collections import namedtuple
from datetime import datetime as dt
from importlib import import_module
from typing import Dict

import backoff
import boto3
import pynamodb.exceptions
from pynamodb.connection.base import Connection
from pynamodb.exceptions import DoesNotExist
from pynamodb.transactions import TransactWrite

# import graphql_api.dynamodb
from .cloudwatch import ServerlessMetricWriter
from .config import (
    CW_METRICS_RESOLUTION,
    DB_ENDPOINT,
    IS_OFFLINE,
    REGION,
    S3_BUCKET_NAME,
    STACK_NAME,
    TESTING,
)
# from graphql_api.dynamodb.models import ToshiIdentity

db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

logger = logging.getLogger(__name__)

_ALPHABET = list("23456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")


ObjectIdentityRecord = namedtuple("ObjectIdentityRecord", "object_type, object_id")


def append_uniq(size):
    uniq = ''.join(random.choice(_ALPHABET) for _ in range(5))
    return str(size) + uniq


def replace_enums(kwargs: Dict) -> Dict:
    new_kwargs = kwargs.copy()
    for key, value in kwargs.items():
        if isinstance(value, enum.Enum):
            new_kwargs[key] = value.value
    return new_kwargs


class BaseData:
    """
    BaseData is the base class for data handlers
    """

    def __init__(self, client_args, db_manager):
        """Args:
        client_args (dict): optional)arguments for the boto3 client
        db_manager (DataManager): reference to the singleton DataManager object
        """
        self._aws_client_args = client_args or {}
        self._prefix = self.__class__.__name__
        self._db_manager = db_manager
        self._s3_conn = None
        self._s3_client = None
        self._s3_bucket = None
        # self._connection = None
        self._bucket_name = S3_BUCKET_NAME

    def get_one_raw(self, _id: str):
        """
        Args:
            _id: the object id

        Returns:
            File: the File object json
        """
        obj = self._read_object(_id)
        return obj

    def get_one(self, _id: str):
        """Summary

        Args:
            _id: id for an object

        Raises:
            NotImplementedError: must override
        """
        raise NotImplementedError("method needs to be defined by sub-class")

    @property
    def prefix(self):
        return self._prefix

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = boto3.client('s3', **self._aws_client_args)
        return self._s3_client

    @property
    def s3_connection(self):
        if not self._s3_conn:
            self._s3_conn = boto3.resource('s3')
            # self._connection = Connection(region=REGION)
        return self._s3_conn

    @property
    def s3_bucket(self):
        if not self._s3_bucket:
            self._s3_bucket = self.s3_connection.Bucket(self._bucket_name, client=self.s3_client)
        return self._s3_bucket

    def get_all_in(self, _id_list):
        pass
        # TODO


def backoff_hdlr(details):
    logger.debug(
        "Backoff {wait:0.1f} seconds after {tries} tries "
        "calling function {target} with args {args} and kwargs "
        "{kwargs}".format(**details)
    )


class BaseDynamoDBData(BaseData):
    def __init__(self, client_args, db_manager, model, connection=Connection(region=REGION)):
        super().__init__(client_args, db_manager)
        self._model = model
        self._connection = connection
        if not TESTING and IS_OFFLINE:
            self._connection = Connection(host=DB_ENDPOINT)

    @property
    def model(self):
        return self._model

    def get_object(self, object_id):
        """get a pynamodb model instance from  DynamoDB.

        Args:
            object_id int: unique ID of the obect
        Returns:
            pynamodb model object
        """
        t0 = dt.utcnow()
        logger.debug('get dynamo key: %s for model %s' % (object_id, self._model))
        obj = self._model.get(str(object_id))
        db_metrics.put_duration(__name__, 'get_object', dt.utcnow() - t0)
        return obj

    def get_next_id(self) -> str:
        """
        Returns:
                int: the next available id
        """
        t0 = dt.utcnow()
        try:
            identity = ToshiIdentity.get(self._prefix)
        except DoesNotExist:
            # very first use of the identity
            logger.debug(f'get_next_id setting initial ID; table_name={self._prefix}, object_id={FIRST_DYNAMO_ID}')
            identity = ToshiIdentity(table_name=self._prefix, object_id=FIRST_DYNAMO_ID)
            identity.save()
        db_metrics.put_duration(__name__, 'get_next_id', dt.utcnow() - t0)
        return identity.object_id

    def _read_object(self, object_id):
        """read object contents from the DynamoDB

        Args:
            object_id int): unique iD of the obect

        Returns:
            dict: object data deserialised from the json object
        """
        t0 = dt.utcnow()
        key = "%s/%s" % (self._prefix, object_id)
        logger.debug(f'_read_object; key: {key}, prefix {self._prefix}')

        obj = self.get_object(object_id)
        db_metrics.put_duration(__name__, '_read_object', dt.utcnow() - t0)
        return obj.object_content


    @backoff.on_exception(backoff.expo, pynamodb.exceptions.TransactWriteError, max_time=60, on_backoff=backoff_hdlr)
    def _write_object(self, object_id, object_type, body):
        """write object contents to the DynamoDB table.

        Args:
            object_id (int): unique iD of the obect
            body (dict): dict to be serialised to JSON
        """

        t0 = dt.utcnow()
        identity = ToshiIdentity.get(self._prefix)  # first time round is handled in get_next_id()

        # TODO: make a transacion conditional check (maybe)
        if not identity.object_id == object_id:
            raise graphql_api.dynamodb.DynamoWriteConsistencyError(
                F"object ids are not consistent!) {(identity.object_id, object_id)}"
            )

        toshi_object = self._model(object_id=str(object_id), object_type=body['clazz_name'], object_content=body)

        # Note that we won't see any json serialisatoin errors here, body seriaze is called
        logger.debug(f"toshi_object: {toshi_object}")

        # print(dir(toshi_object))
        # print(toshi_object.to_json())

        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(identity, actions=[ToshiIdentity.object_id.add(1)])
            transaction.save(toshi_object)

        logger.info(f"toshi_object: object_id {object_id} object_type: {body['clazz_name']}")

        db_metrics.put_duration(__name__, '_write_object', dt.utcnow() - t0)
        es_key = f"{self._prefix}_{object_id}"
        self._db_manager.search_manager.index_document(es_key, body)

    @backoff.on_exception(backoff.expo, pynamodb.exceptions.TransactWriteError, max_time=60, on_backoff=backoff_hdlr)
    def transact_update(self, object_id, object_type, body):
        t0 = dt.utcnow()
        logger.info("%s.update: %s : %s" % (object_type, object_id, str(body)))

        model = self._model.get(object_id)
        assert model.object_type == body.get('clazz_name')
        with TransactWrite(connection=self._connection) as transaction:
            transaction.update(model, actions=[self._model.object_content.set(replace_enums(body))])

        es_key = f"{self._prefix}_{object_id}"
        self._db_manager.search_manager.index_document(es_key, body)
        db_metrics.put_duration(__name__, 'transact_update', dt.utcnow() - t0)

    # @backoff.on_exception(
    #     backoff.expo, graphql_api.dynamodb.DynamoWriteConsistencyError, max_time=60, on_backoff=backoff_hdlr
    # )
    def create(self, clazz_name, **kwargs):
        """
        Args:
            clazz_name (String): the class name of schema object
            **kwargs: the field data

        Returns:
            Table: a new instance of the clazz_name

        Raises:
            ValueError: invalid data exception
        """
        logger.info(f"create() {clazz_name} {kwargs}")

        clazz = getattr(import_module('graphql_api.schema'), clazz_name)
        next_id = self.get_next_id()

        # TODO: this whole approach sucks !@#%$#
        # consider the ENUM problem, and datatime serialisation
        # mayby graphene o
        # cant we just use the graphene classes json serialisation ??

        def new_body(next_id, kwargs):
            new = clazz(next_id, **kwargs)
            body = new.__dict__.copy()
            body['clazz_name'] = clazz_name
            if body.get('created'):
                body['created'] = body['created'].isoformat()
            return body

        object_instance = clazz(next_id, **kwargs)

        try:
            self._write_object(next_id, self._prefix, new_body(next_id, replace_enums(kwargs)))
        except Exception as err:
            logger.error(F"faild to write {clazz_name} {kwargs} {err}")
            raise

        logger.info(f"create() object_instance: {object_instance}")
        return object_instance

    def get_all(self, object_type, limit: int, after: str):
        t0 = dt.utcnow()
        after = after or "-1"
        logger.info(f"get_all, {self._model} {self.prefix} {object_type} after {after}")
        for object_meta in self._model.model_id_index.query(
            object_type, self._model.object_id > after, limit=limit  # range condition
        ):
            yield ObjectIdentityRecord(object_meta.object_type, object_meta.object_id)

        db_metrics.put_duration(__name__, 'get_all', dt.utcnow() - t0)
