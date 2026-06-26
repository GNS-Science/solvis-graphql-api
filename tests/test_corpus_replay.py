"""Phase 0 corpus replay — validate vendored client queries against the schema.

Each ``.graphql`` in ``fixtures/corpus/`` is a real query (sourced from the test suite
and the kororaa UI). We *validate* (not execute) against the schema, so the gate needs
no data fixtures. Running the same corpus against the new Strawberry schema later catches
any field/type/argument drift — the runtime equivalence is covered separately by the A/B
differential check (``cli_ab_test``).
"""

import pathlib

import pytest
from graphql import build_schema, parse, validate

from solvis_graphql_api.schema import schema as strawberry_schema

CORPUS_DIR = pathlib.Path(__file__).parent / "fixtures" / "corpus"
CORPUS = sorted(CORPUS_DIR.glob("*.graphql"))

# re-pointed at the new Strawberry schema (Phase 2b) — the migration target. Since the SDL
# is byte-identical to the legacy baseline, every query that validated against Graphene must
# still validate here; any future field/type drift in the port fails this gate.
_GQL_SCHEMA = build_schema(strawberry_schema.as_str())


def test_corpus_is_non_empty():
    assert CORPUS, "no corpus queries found in fixtures/corpus/"


@pytest.mark.parametrize("query_path", CORPUS, ids=lambda p: p.name)
def test_corpus_query_validates(query_path):
    query = query_path.read_text()
    errors = validate(_GQL_SCHEMA, parse(query))
    assert not errors, f"{query_path.name}: {[str(e) for e in errors]}"
