# flake8: noqa
"""
Test schema operations
"""
# import datetime
import unittest
from io import BytesIO
from unittest import mock

# import boto3
import botocore
import pytest

# from botocore.exceptions import ClientError
from dateutil.tz import tzutc
from graphene.test import Client
from moto import mock_dynamodb, mock_s3

# from graphql_api import __version__
# from graphql_api.schema import , root_schema

orig = botocore.client.BaseClient._make_api_call


@pytest.mark.skip('TODO')
@mock_s3
@mock_dynamodb
class TestCreateDataFile(unittest.TestCase):
    def setUp(self):
        # data.setup()
        # migrate()
        self.client = Client(root_schema)
        self.mock_all = lambda x: []
        self.mock_create = lambda x, y, **z: None

    @mock.patch('graphql_api.data.BaseDynamoDBData._write_object', lambda self, object_id, object_type, body: None)
    @mock.patch('graphql_api.data.BaseDynamoDBData.get_next_id', lambda self: 0)
    # @mock.patch('graphql_api.data.BaseData._read_object', lambda self, object_id: None)
    # @mock.patch('graphql_api.data.BaseDynamoDBData.transact_update', lambda self, object_id, object_type, body: None)
    def test_upload(self):
        qry = '''
            mutation ($digest: String!, $file_name: String!, $file_size: BigInt!) {
              create_file(
                  md5_digest: $digest
                  file_name: $file_name
                  file_size: $file_size
              ) {
              ok
              file_result { id, file_name, file_size, md5_digest, post_url }
              }
            }'''

        # from hashlib import sha256, md5

        filedata = BytesIO("a line\nor two".encode())
        digest = "sha256(filedata.read()).hexdigest()"
        filedata.seek(0)  # important!
        size = len(filedata.read())
        filedata.seek(0)  # important!
        variables = dict(file=filedata, digest=digest, file_name="alineortwo.txt", file_size=size)

        def mock_make_api_call(self, operation_name, kwarg):
            if operation_name in ['ListObjects', 'PutObject']:
                return {}
            raise ValueError("got unmocked operation: ", operation_name)

        # TODO mock out the presigned URL calls
        with mock.patch('graphql_api.data.BaseData.get_all', new=self.mock_all):
            with mock.patch('botocore.client.BaseClient._make_api_call', new=mock_make_api_call):
                # with mock.patch('graphql_api.data.DataFileData.create', new=self.mock_create):
                executed = self.client.execute(qry, variable_values=variables)
                print(executed)
                assert executed['data']['create_file']['ok'] == True
