from .blob_data import BlobData
from .model import BinaryLargeObject

dm_instance = None


def get_data_manager():
    return dm_instance


class DataManager:
    """DataManager provides the entry point to the data handlers"""

    def __init__(self, client_args=None):
        _args = client_args or {}
        self._blob_data = BlobData(_args, self, BinaryLargeObject)

        # set up the singleton
        global dm_instance
        dm_instance = self

    @property
    def blob_data(self):
        return self._blob_data
