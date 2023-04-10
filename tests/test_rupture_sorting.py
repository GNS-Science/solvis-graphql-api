from graphene.test import Client
from solvis_graphql_api.schema import schema_root
from dataclasses import dataclass
from typing import List
import pytest


@pytest.fixture(scope='module')
def client():
    return Client(schema_root)


@pytest.fixture(scope='module')
def query():
    return """
            query (
                    $model_id: String!
                    $location_codes: [String]!
                    $fault_system: String!
                    $radius_km: Int
                    )
                {
              filter_ruptures(
                first: 20
                # SORT_BY
                filter:{
                    model_id: $model_id
                    location_codes: $location_codes
                    fault_system: $fault_system
                    radius_km: $radius_km
                    minimum_rate: 1.0e-6
                    minimum_mag: 7.83
                    }
                ) {
                total_count
                pageInfo {
                    endCursor
                    hasNextPage
                }
                edges {
                  cursor
                  node {
                    __typename
                    model_id
                    rupture_index
                    magnitude
                    rate_weighted_mean
                  }
                }
              }
            }

        """


@pytest.fixture(scope='module')
def variable_values():
    return {
        "model_id": "NSHM_1.0.0",
        "fault_system": "HIK",
        "location_codes": ['WLG'],
        "minimum_mag": 8.3,
        "minimum_rate": 1.0e-6,
        "radius_km": 5,
    }


@dataclass
class SortedField:
    field_name: str
    ascending: bool
    binned: bool


def verify_sorted_edges(edges: List[object], fields: List[SortedField]):
    """check the list of edges is sorted as expected"""
    field_map = dict()
    field_vals = dict()
    new_vals = dict()

    for i, fld in enumerate(fields):
        field_map[fld.field_name] = fld
        field_vals[fld.field_name] = 0 if field_map[fld.field_name].ascending else float('inf')

    for rupt in edges:
        reset = False
        for fld in field_vals.keys():
            new_vals[fld] = rupt['node'][fld]
            if field_map[fld].binned:
                reset = reset or not (field_vals[fld] == new_vals[fld])  # reset_field_value(new_vals, field_vals, fld)

            if reset:
                field_vals[fld] = new_vals[fld]

            if field_map[fld].ascending:
                assert new_vals[fld] >= field_vals[fld]
            else:
                assert new_vals[fld] <= field_vals[fld]

        field_vals[fld] = new_vals[fld]


@pytest.mark.parametrize(
    "sort_expr,expected",
    [
        ('sortby: [{attribute: "magnitude"}]', [SortedField('magnitude', ascending=True, binned=False)]),
        (
            'sortby: [{attribute: "magnitude" ascending: false}]',
            [SortedField('magnitude', ascending=False, binned=False)],
        ),
        (
            """sortby: [{attribute: "magnitude" ascending: false bin_width:0.25},
                {attribute: "rate_weighted_mean" ascending: false}]""",
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=False, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "magnitude" ascending: false bin_width:0.2}, {attribute: "rate_weighted_mean"}]',
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=True, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "magnitude" bin_width:0.2}, {attribute: "rate_weighted_mean"}]',
            [
                SortedField('magnitude', ascending=True, binned=True),
                SortedField('rate_weighted_mean', ascending=True, binned=False),
            ],
        ),
    ],
)
def test_sorting_and_binning_magnitude(client, query, variable_values, sort_expr, expected):
    print(query)
    executed = client.execute(
        query.replace("# SORT_BY", sort_expr),
        variable_values=variable_values,
    )

    print(executed)
    rupts = executed['data']['filter_ruptures']
    verify_sorted_edges(rupts['edges'], expected)
    assert rupts['pageInfo']['hasNextPage'] is True
