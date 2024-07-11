"""
common test config and fixtures
"""
import os
import pathlib

import nzshm_model
import pytest
import solvis

BASEPATH = os.path.realpath(__file__)


@pytest.fixture(scope='module')
def source_logic_tree():
    model_id = "NSHM_v1.0.4"
    assert nzshm_model.get_model_version(model_id) is not None
    yield nzshm_model.get_model_version(model_id).source_logic_tree


@pytest.fixture(scope='module')
def full_composite_solution(source_logic_tree):
    archive_path = pathlib.Path(BASEPATH).parent / "fixtures/NSHM_v1.0.4_CompositeSolution.zip"
    yield lambda model_id: solvis.CompositeSolution.from_archive(archive_path, source_logic_tree)


@pytest.fixture(scope='module')
def tiny_composite_solution(source_logic_tree):
    archive_path = pathlib.Path(BASEPATH).parent / "fixtures/TinyCompositeSolution.zip"
    yield lambda model_id: solvis.CompositeSolution.from_archive(archive_path, source_logic_tree)


@pytest.fixture
def archive_fixture(monkeypatch, full_composite_solution):
    monkeypatch.setattr('solvis_graphql_api.composite_solution.cached.get_composite_solution', full_composite_solution)
    monkeypatch.setattr(
        'solvis_graphql_api.composite_solution.composite_rupture_detail.get_composite_solution', full_composite_solution
    )


@pytest.fixture
def archive_fixture_tiny(monkeypatch, tiny_composite_solution):
    monkeypatch.setattr('solvis_graphql_api.composite_solution.cached.get_composite_solution', tiny_composite_solution)
    monkeypatch.setattr(
        'solvis_graphql_api.composite_solution.composite_rupture_detail.get_composite_solution', tiny_composite_solution
    )
