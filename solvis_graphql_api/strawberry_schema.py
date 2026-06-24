"""Strawberry schema — migration scaffold.

Phase 1 stands up a **minimal** Query so the FastAPI/Mangum app boots and serves a real
field at SDL parity; the full type port lands in Phase 2.

Named ``strawberry_schema.py`` (not ``schema.py``) because the legacy Graphene schema
occupies the ``solvis_graphql_api.schema`` module path during the migration — a Phase 1
trap surfaced by the Model pilot. Rename to ``schema.py`` at cutover once the Graphene
schema is removed.
"""

import strawberry
from strawberry.schema.config import StrawberryConfig

import solvis_graphql_api


@strawberry.type
class QueryRoot:
    # root type MUST be named QueryRoot — legacy schema is `query: QueryRoot`, and the
    # vendored kororaa corpus fragments are `on QueryRoot`
    @strawberry.field(description="About this Solvis API ")
    def about(self) -> str | None:
        # nullable (-> str | None) to match graphene's nullable String (Model T2)
        return f"Hello World, I am solvis_graphql_api! Version: {solvis_graphql_api.__version__}"


schema = strawberry.Schema(
    query=QueryRoot,
    # legacy schema is auto_camelcase=False — required for snake_case field parity (Trap #2)
    config=StrawberryConfig(auto_camel_case=False),
)
