"""
common test config and fixtures
"""
import pathlib

import pytest
import solvis_graphql_api.composite_solution.cached  # for cache_clear


def clear_caches():
    solvis_graphql_api.composite_solution.cached.matched_rupture_sections_gdf.cache_clear()
    solvis_graphql_api.composite_solution.cached.get_composite_solution.cache_clear()


@pytest.fixture
def archive_fixture(monkeypatch, scope='function'):
    """
    setup the archive path - will be replaced once data_store is in use
    """
    clear_caches()
    archive_path = pathlib.Path(__name__).parent.parent / "WORKING" / "NSHM_v1.0.4_CompositeSolution.zip"
    assert archive_path.exists()
    monkeypatch.setenv("COMPOSITE_ARCHIVE_PATH", str(archive_path))
    yield archive_path


@pytest.fixture
def archive_fixture_tiny(monkeypatch, scope='function'):
    clear_caches()
    archive_path = pathlib.Path(__name__).parent.parent / "data_store/test/fixtures" / "TinyCompositeSolution.zip"
    assert archive_path.exists()
    monkeypatch.setenv("COMPOSITE_ARCHIVE_PATH", str(archive_path))
    yield archive_path
