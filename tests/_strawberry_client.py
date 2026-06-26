"""A ``graphene.test.Client`` drop-in backed by the Strawberry schema.

The legacy behavioural tests were written against the Graphene schema via
``graphene.test.Client(schema_root).execute(query)``. The Strawberry schema is byte-identical
(SDL parity gate) and runtime-identical (``test_strawberry_parity`` differential), so those
tests stay valuable — they cover the migrated resolvers (sorting, filter-set logic, pagination,
geojson) far beyond the parity corpus. This shim lets them run against Strawberry unchanged,
so Graphene can be removed.

``schema_root`` here is the Strawberry schema; ``Client.execute`` returns the same
``{"data": ..., "errors": [...]}`` dict shape graphene produced (``GraphQLError.formatted``
matches graphene's ``{message, locations, path}``).
"""

from solvis_graphql_api.schema import schema as schema_root  # noqa: F401  # re-exported for legacy tests


class Client:
    def __init__(self, schema):
        self._schema = schema

    def execute(self, query, variable_values=None, context_value=None, operation_name=None, **_ignored):
        result = self._schema.execute_sync(
            query,
            variable_values=variable_values,
            context_value=context_value,
            operation_name=operation_name,
        )
        response: dict = {"data": result.data}
        if result.errors:
            response["errors"] = [err.formatted for err in result.errors]
        return response
