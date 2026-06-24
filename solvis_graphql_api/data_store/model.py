"""DynamoDB + S3 blob store for the CompositeSolution archive.

Migration note: the DynamoDB item was a PynamoDB ``Model``; it is now a ``pydantic``
model + thin ``boto3`` CRUD. The public ``BinaryLargeObject`` wrapper API is unchanged
(``get`` / ``save`` / ``exists`` / ``create_table`` / ``delete_table`` / ``to_json`` /
``set_s3_client_args`` / the ``object_*`` properties), so ``cli`` and the resolvers
(``composite_solution.cached``) are untouched. ``object_meta`` is stored as a JSON string
to reproduce PynamoDB's ``JSONAttribute`` exactly (values round-trip as ints, not Decimals).
"""

import io
import json
import logging
from collections.abc import Sequence
from typing import Any

import boto3
import botocore
from pydantic import BaseModel

from .config import DB_ENDPOINT, DEPLOYMENT_STAGE, IS_OFFLINE, REGION, S3_BUCKET_NAME, TESTING

log = logging.getLogger(__name__)

TABLE_NAME = f"SGI-BinaryLargeObject-{DEPLOYMENT_STAGE}"

log.info(f"configuring BinaryLargeObject store with IS_OFFLINE: {IS_OFFLINE} TESTING: {TESTING}")

S3_CLIENT_ARGS = (
    dict(
        aws_access_key_id="S3RVER",
        aws_secret_access_key="S3RVER",
        endpoint_url="http://localhost:4569",
    )
    if not TESTING and IS_OFFLINE
    else {}
)


def _dynamodb_resource() -> Any:
    kwargs: dict[str, Any] = dict(region_name=REGION)
    if DB_ENDPOINT:  # set when running offline (serverless-dynamodb local)
        kwargs["endpoint_url"] = DB_ENDPOINT
    return boto3.resource("dynamodb", **kwargs)


class BinaryLargeObjectItem(BaseModel):
    """The DynamoDB item shape (was the PynamoDB model attributes)."""

    hash_key: str
    range_key: str
    object_id: str
    object_type: str
    object_meta: dict

    def to_simple_dict(self) -> dict[str, Any]:
        # name/shape preserved from the PynamoDB Model.to_simple_dict() it replaces
        return self.model_dump()


class BinaryLargeObject:
    """
    A class wrapping the DynamoDB item so that we can intercept the save/get operations
    and carry the S3 blob alongside the item.

    TODO: maybe we can use the item model directly but we have issues with the get() classmethod
    """

    def __init__(
        self, object_id, object_type, object_meta, object_blob, client_args=None
    ):
        self._item = BinaryLargeObjectItem(
            hash_key=f"{object_type}:{object_id}",
            range_key=f"{object_type}:{object_id}",
            object_id=object_id,
            object_type=object_type,
            object_meta=object_meta,
        )
        self._object_blob = object_blob
        self._bucket_name = S3_BUCKET_NAME
        self._aws_client_args = S3_CLIENT_ARGS
        self._s3_bucket = None
        self._s3_conn = None
        self._s3_client = None

    def set_s3_client_args(self, client_args: dict) -> "BinaryLargeObject":
        """
        When testing with S3 offline we will need to override boto3 defaults
        """
        self._aws_client_args = client_args
        return self

    @property
    def s3_client(self):
        if not self._s3_client:
            self._s3_client = boto3.client(
                "s3", **self._aws_client_args, region_name=REGION
            )
        return self._s3_client

    @property
    def s3_connection(self):
        if not self._s3_conn:
            self._s3_conn = boto3.resource("s3")
            # self._connection = Connection(region=REGION)
        return self._s3_conn

    @property
    def s3_bucket(self):
        if not self._s3_bucket:
            self._s3_bucket = self.s3_connection.Bucket(
                self._bucket_name, client=self.s3_client
            )
        return self._s3_bucket

    @property
    def object_id(self):
        return self._item.object_id

    @property
    def object_type(self):
        return self._item.object_type

    @property
    def object_meta(self):
        return self._item.object_meta

    @property
    def object_blob(self):
        if self._object_blob:
            return self._object_blob

        log.info(f"get object_blob from bucket {self}")
        try:
            file_object = io.BytesIO()
            self.s3_bucket.download_fileobj(
                f"{self.object_type}/{self.object_id}", file_object
            )
            file_object.seek(0)
            self._object_blob = file_object.read()
        except botocore.exceptions.ClientError as err:
            if "(404)" not in str(err):
                log.error("object not found")
                raise
            log.debug("object has no blob data")
        return self._object_blob

    def to_json(self):
        mijson = self._item.to_simple_dict()
        print(mijson)
        mijson["object_blob"] = self._object_blob
        return mijson

    @classmethod
    def exists(cls) -> bool:
        client = _dynamodb_resource().meta.client
        try:
            client.describe_table(TableName=TABLE_NAME)
            return True
        except client.exceptions.ResourceNotFoundException:
            return False

    @classmethod
    def create_table(cls, wait: bool = False) -> dict[str, Any]:
        client = _dynamodb_resource().meta.client
        resp = client.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {"AttributeName": "hash_key", "KeyType": "HASH"},
                {"AttributeName": "range_key", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "hash_key", "AttributeType": "S"},
                {"AttributeName": "range_key", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        if wait:
            client.get_waiter("table_exists").wait(TableName=TABLE_NAME)
        return resp

    @classmethod
    def delete_table(cls) -> dict[str, Any]:
        client = _dynamodb_resource().meta.client
        return client.delete_table(TableName=TABLE_NAME)

    def save(self) -> dict[str, Any]:
        if self._object_blob:
            log.info("put the blob ")
            self.s3_bucket.put_object(
                Key=f"{self.object_type}/{self.object_id}",
                Body=io.BytesIO(self._object_blob),
            )
        table = _dynamodb_resource().Table(TABLE_NAME)
        item = self._item.model_dump()
        item["object_meta"] = json.dumps(item["object_meta"])  # JSONAttribute parity
        return table.put_item(Item=item)

    @classmethod
    def get(
        cls,
        object_type: str,
        object_id: str,
        range_key: Any | None = None,
        consistent_read: bool = False,
        attributes_to_get: Sequence[str] | None = None,
    ) -> Any:
        log.info(f"{cls}.get() called")
        hash_key = f"{object_type}:{object_id}"
        table = _dynamodb_resource().Table(TABLE_NAME)
        response = table.get_item(
            Key={"hash_key": hash_key, "range_key": hash_key},
            ConsistentRead=consistent_read,
        )
        if "Item" not in response:
            raise KeyError(f"BinaryLargeObject {hash_key} does not exist")
        record = response["Item"]
        return cls(
            record["object_id"],
            record["object_type"],
            json.loads(record["object_meta"]),
            None,
        )


tables = [BinaryLargeObject]


def migrate():
    log.info(
        f"migrate() stage: {DEPLOYMENT_STAGE} offline: {IS_OFFLINE} region: {REGION} testing: {TESTING}"
    )
    for table in tables:
        if not table.exists():
            table.create_table(wait=True)
            print(f"Migrate created table: {table}")


def drop_tables():
    for table in tables:
        if table.exists():
            table.delete_table()
            print(f"deleted table: {table}")
