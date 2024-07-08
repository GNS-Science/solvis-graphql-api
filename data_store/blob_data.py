"""
The object manager for File (and subclassed) schema objects
"""

# import json
import logging
# from datetime import datetime as dt
# from importlib import import_module

from .cloudwatch import ServerlessMetricWriter
from .config import CW_METRICS_RESOLUTION, STACK_NAME

# from .base_data import BaseDynamoDBData

logger = logging.getLogger(__name__)


db_metrics = ServerlessMetricWriter(
    lambda_name=STACK_NAME, metric_name="MethodDuration", resolution=CW_METRICS_RESOLUTION
)

class BlobData():
    pass

'''
class BlobData(BaseDynamoDBData):
    """
    BlobData provides the storage for BinaryLargeObject objects.

    BinaryLargeObject object have both a json metadata object, and a file object.
    """

    def update(self, id, updated_body):
        print('UPDATE', updated_body)
        self.transact_update(id, self._prefix, updated_body)
        return self.from_json(updated_body)

    def create(self, clazz_name, **kwargs):
        """
        create a new BinaryLargeObject object in the storage layer. This is two objects:

        - The json metadata will be stored in DyanamoDB.
        - a placeholder file object in S3, which should be replaced by the actual file conteent by the toshi client.

        Args:
         - clazz_name (String): the class name of schema object
         - kwargs (dict): the file metadata.

        Returns:
            BinaryLargeObject: the BinaryLargeObject object
        """
        logger.info(f"BlobData.create {kwargs}")
        new_instance = super().create(clazz_name, **kwargs)
        data_key = "%s/%s/%s" % (self._prefix, new_instance.id, new_instance.file_name)

        t0 = dt.utcnow()
        self.s3_bucket.put_object(Key=data_key, Body="placeholder_to_be_overwritten")
        parts = self.s3_client.generate_presigned_post(
            Bucket=self._bucket_name,
            Key=data_key,
            Fields={
                'acl': 'public-read',
                'Content-MD5': new_instance.md5_digest,
                'Content-Type': 'binary/octet-stream',
            },
            Conditions=[
                {"acl": "public-read"},
                ["starts-with", "$Content-Type", ""],
                ["starts-with", "$Content-MD5", ""],
            ],
        )

        db_metrics.put_duration(__name__, 'create[placeholder+generate-presigned-post]', dt.utcnow() - t0)

        new_instance.post_url = json.dumps(parts['fields'])
        return new_instance

    def get_one(self, file_id, expected_class="File"):
        """
        Args:
            file_id (string): the object id

        Returns:
            File: the File/* object
        """
        jsondata = self.get_one_raw(file_id)

        logger.debug(jsondata)

        # more migration hacks
        if not jsondata['clazz_name'] == expected_class:
            if expected_class == "InversionSolution":
                print(f"Upgrading {jsondata.get('clazz_name')} to InversionSolution")
                jsondata['clazz_name'] = expected_class

        return self.from_json(jsondata)

    def get_presigned_url(self, _id):
        """
        Args:
            _id (string): the object id

        Returns:
            string: a temporary URL that may be used to download the raw file data.
        """
        t0 = dt.utcnow()
        file = self.get_one(_id)
        key = "%s/%s/%s" % (self._prefix, _id, file.file_name)
        url = self.s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self._bucket_name,
                'Key': key,
            },
            ExpiresIn=3600,
        )
        db_metrics.put_duration(__name__, 'get_presigned_url', dt.utcnow() - t0)
        return url

    @staticmethod
    def from_json(jsondata):
        logger.debug("from_json: %s" % str(jsondata))

        # datetime comversions
        created = jsondata.get('created')
        if created:
            jsondata['created'] = dt.fromisoformat(created)

        clazz_name = jsondata.pop('clazz_name')
        clazz = getattr(import_module('graphql_api.schema'), clazz_name)

        logger.debug("from_json clazz: %s" % str(clazz))

        ## produced_by_id -> produced_by schema migration
        produced_by_id = jsondata.pop('produced_by_id', None)
        if produced_by_id and not jsondata.get('produced_by'):
            jsondata['produced_by'] = produced_by_id

        # table datetime conversions
        if jsondata.get('tables'):
            for tbl in jsondata.get('tables'):
                tbl['created'] = dt.fromisoformat(tbl['created'])

        return clazz(**jsondata)
'''