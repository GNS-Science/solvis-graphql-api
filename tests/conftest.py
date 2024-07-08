"""
common test config and fixtures
"""
import pathlib

import pytest


@pytest.fixture
def archive_fixture(monkeypatch):
    """
    setup the archive path - will be replaced once data_store is in use
    """
    # archive_path = pathlib.Path(__name__).parent.parent / "data_store/test/fixtures" / "TinyCompositeSolution.zip"
    archive_path = pathlib.Path(__name__).parent.parent / "WORKING" / "NSHM_v1.0.4_CompositeSolution.zip"
    assert archive_path.exists()
    monkeypatch.setenv("COMPOSITE_ARCHIVE_PATH", str(archive_path))
    yield archive_path
