"""Phase 0 corpus replay — validate vendored client queries against the schema.

Each ``.graphql`` in ``fixtures/corpus/`` is a real query (sourced from the test suite
and the kororaa UI). We *validate* (not execute) against the schema, so the gate needs
no data fixtures. Running the same corpus against the new Strawberry schema later catches
any field/type/argument drift — the runtime equivalence is covered separately by the A/B
differential check (``cli_ab_test``).
"""

import pathlib

import pytest
from graphql import parse, validate

from solvis_graphql_api.schema import schema_root

CORPUS_DIR = pathlib.Path(__file__).parent / "fixtures" / "corpus"
CORPUS = sorted(CORPUS_DIR.glob("*.graphql"))


def test_corpus_is_non_empty():
    assert CORPUS, "no corpus queries found in fixtures/corpus/"


@pytest.mark.parametrize("query_path", CORPUS, ids=lambda p: p.name)
def test_corpus_query_validates(query_path):
    query = query_path.read_text()
    errors = validate(schema_root.graphql_schema, parse(query))
    assert not errors, f"{query_path.name}: {[str(e) for e in errors]}"
