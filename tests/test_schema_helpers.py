"""Unit coverage for small Strawberry-schema helper branches.

The trivial empty/None branches of the input-coercion helpers and the null-sortby skip aren't
reached by the parity/behavioural queries (which always supply styles, filter_set_options and
non-null sortby items), so exercise them directly.
"""

from solvis_graphql_api.schema import _fso_dict, _style_dict, schema


def test_style_dict_none_returns_empty():
    assert _style_dict(None) == {}


def test_fso_dict_falsy_returns_empty():
    assert _fso_dict(None) == {}


_FILTER_RUPTURES_NULL_SORTBY = """
query ($model_id: String! $location_ids: [String]! $fault_system: String!) {
  filter_ruptures(first: 1 sortby: [null] filter: {
      model_id: $model_id fault_system: $fault_system location_ids: $location_ids
      radius_km: 5 minimum_mag: 8.3 minimum_rate: 1.0e-6}) {
    total_count
  }
}
"""


def test_filter_ruptures_skips_null_sortby_item(archive_fixture):
    # a null element in the sortby list must be skipped (not crash the resolver)
    result = schema.execute_sync(
        _FILTER_RUPTURES_NULL_SORTBY,
        variable_values={"model_id": "NSHM_v1.0.0", "fault_system": "HIK", "location_ids": ["WLG"]},
    )
    assert not result.errors
    assert result.data["filter_ruptures"]["total_count"] >= 0
