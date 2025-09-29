"""
Basic tests for our dyanamodb BinaryLargeObject model
"""

import boto3
from moto import mock_dynamodb, mock_s3

from solvis_graphql_api.data_store import model
from solvis_graphql_api.data_store.config import REGION, S3_BUCKET_NAME


@mock_s3
@mock_dynamodb
class TestBinaryLargeObject:
    def test_create_blob_table(self):
        model.BinaryLargeObject.create_table()
        assert model.BinaryLargeObject.exists()

    def test_drop_blob_table(self):
        self.test_create_blob_table()
        model.BinaryLargeObject.delete_table()
        assert not model.BinaryLargeObject.exists()

    def test_create_blob_object(self):

        conn = boto3.resource("s3", region_name=REGION)
        conn.create_bucket(Bucket=S3_BUCKET_NAME)

        model.BinaryLargeObject.create_table()
        myBlob = model.BinaryLargeObject(
            object_id="ABC",
            object_type="MyObjectTypename",
            object_meta=dict(a=1, b=2),
            object_blob=b"0x1234",
        )
        myBlob.save()
        savedBlob = model.BinaryLargeObject.get("MyObjectTypename", "ABC")
        # assert 0
        # savedBlob.set_s3_client_args({})

        assert savedBlob.object_blob == myBlob.object_blob
        assert savedBlob.to_json() == myBlob.to_json()
        print(savedBlob.to_json())

    def test_create_blob_object_no_data(self):

        conn = boto3.resource("s3", region_name=REGION)
        conn.create_bucket(Bucket=S3_BUCKET_NAME)

        model.BinaryLargeObject.create_table()
        myBlob = model.BinaryLargeObject(
            object_id="1001",
            object_type="MyObjectTypename",
            object_meta=dict(a=1, b=2),
            object_blob=None,
        )
        myBlob.save()
        savedBlob = model.BinaryLargeObject.get(
            "MyObjectTypename", object_id="1001"
        ).set_s3_client_args({})

        assert savedBlob.object_blob == myBlob.object_blob
        assert savedBlob.to_json() == myBlob.to_json()
        print(savedBlob.to_json())
