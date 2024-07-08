"""
Basic tests for our dyanamodb BinaryLargeObject model
"""

import boto3
from moto import mock_dynamodb, mock_s3

from data_store import model
from data_store.config import REGION, S3_BUCKET_NAME


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
            object_id='ABC', object_type="MyObjectTypename", object_meta=dict(a=1, b=2), object_blob=b'0x1234'
        )
        myBlob.save()
        savedBlob = model.BinaryLargeObject.get('ABC')
        # assert 0
        print(savedBlob.to_json())
        assert savedBlob.to_json() == myBlob.to_json()
        assert savedBlob.object_blob == myBlob.object_blob
