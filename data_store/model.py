import logging
import boto3
import io
from pynamodb.attributes import JSONAttribute, UnicodeAttribute

from pynamodb.models import Model, Condition

from typing import Dict, Any, Optional, Sequence

from .config import DEPLOYMENT_STAGE, IS_OFFLINE, REGION, TESTING, S3_BUCKET_NAME

log = logging.getLogger(__name__)


class BinaryLargeObjectModel(Model):
    class Meta:
        billing_mode = 'PAY_PER_REQUEST'
        table_name = f"SGI-BinaryLargeObject-{DEPLOYMENT_STAGE}"
        region = REGION
        if IS_OFFLINE and not TESTING:
            host = "http://localhost:8000"

    object_id = UnicodeAttribute(hash_key=True)
    object_type = UnicodeAttribute()
    object_meta = JSONAttribute()

    """
    The following is an attempt to intercept the Model classmethods used to read/write models

    save works ok - it's a normal instance method
    get fails bechase the  Model. class (where get is defined, assumes some attributes to exist in the class)

    def save(self, condition: Optional[Condition] = None, *args, add_version_condition: bool = True) -> Dict[str, Any]:
        print("save", self._hash_key_attribute().attr_name, self.object_id)
        return super().save(*args, condition=condition, add_version_condition=add_version_condition)

    @classmethod
    def get(cls, hash_key: Any, range_key: Optional[Any] = None, consistent_read: bool = False, attributes_to_get: Optional[Sequence[str]] = None) -> 'BinaryLargeObject':
        print(cls, cls)
        result = Model.get(hash_key=hash_key, range_key=None)
        print('get', result)
        return result
    """
    object_meta = JSONAttribute()  # the json string


class BinaryLargeObject():
    """
    A class wrapping BinaryLargeObjectModel so that we can intercept the save/get operations

    TODO: maybe we can use Model directly but we have issues with the get() classmethod
    """

    def __init__(self, object_id, object_type, object_meta, object_blob, client_args = None):
        self._model_instance = BinaryLargeObjectModel(
            object_id=object_id,
            object_type=object_type,
            object_meta=object_meta
        )
        self._object_blob = object_blob
        self._bucket_name = S3_BUCKET_NAME
        self._s3_bucket = None
        self._s3_conn = None
        self._s3_client = None
        self._aws_client_args = client_args or {}

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

    @property
    def object_id(self):
        return self._model_instance.object_id

    @property
    def object_type(self):
        return self._model_instance.object_type

    @property
    def object_meta(self):
        return self._model_instance.object_meta

    @property
    def object_blob(self):
        return self._object_blob

    def to_json(self):
        mijson = self._model_instance.to_simple_dict()
        print(mijson)
        mijson['object_blob'] = self._object_blob
        return mijson

    @classmethod
    def exists(cls) -> Dict[str, Any]:
        return BinaryLargeObjectModel.exists()

    @classmethod
    def create_table(cls) -> Dict[str, Any]:
        return BinaryLargeObjectModel.create_table()

    @classmethod
    def delete_table(cls) -> Dict[str, Any]:
        return BinaryLargeObjectModel.delete_table()

    def save(self) -> Dict[str, Any]:
        self.s3_bucket.put_object(Key=self.object_id, Body=self.object_blob)
        return self._model_instance.save()

    @classmethod
    def get(cls, hash_key: Any, range_key: Optional[Any] = None, consistent_read: bool = False, attributes_to_get: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        model_instance = BinaryLargeObjectModel.get(hash_key, range_key, consistent_read, attributes_to_get)

        instance = cls(
            model_instance.object_id,
            model_instance.object_type,
            model_instance.object_meta,
            None
        )

        file_object = io.BytesIO()
        instance.s3_bucket.download_fileobj(instance.object_id, file_object)
        file_object.seek(0)
        instance._object_blob = file_object.read()
        return instance

tables = [BinaryLargeObjectModel]

def migrate():
    log.info(f'migrate() stage: {DEPLOYMENT_STAGE} offline: {IS_OFFLINE} region: {REGION} testing: {TESTING}')
    for table in tables:
        if not table.exists():
            table.create_table(wait=True)
            print(f"Migrate created table: {table}")

def drop_tables():
    for table in tables:
        if table.exists():
            table.delete_table()
            print(f'deleted table: {table}')
