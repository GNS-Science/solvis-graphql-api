from graphene.test import Client
from solvis_graphql_api.schema import schema_root
from dataclasses import dataclass
from typing import List, Dict
import pytest


@pytest.fixture(scope='module')
def client():
    return Client(schema_root)


@pytest.fixture(scope='module')
def query():
    return """
            query (
                    $model_id: String!
                    $location_ids: [String]!
                    $fault_system: String!
                    $radius_km: Int
                    )
                {
              filter_ruptures(
                first: #FIRST
                # SORT_BY
                filter:{
                    model_id: $model_id
                    location_ids: $location_ids
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
                    rate_max
                  }
                }
              }
            }

        """


@pytest.fixture(scope='module')
def variable_values():
    return {
        "model_id": "NSHM_v1.0.0",
        "fault_system": "HIK",
        "location_ids": ['WLG'],
        "minimum_mag": 8.3,
        "minimum_rate": 1.0e-6,
        "radius_km": 5,
    }


@dataclass
class SortedField:
    field_name: str
    ascending: bool
    binned: bool


def verify_sorted_edges(edges: List[Dict], fields: List[SortedField]):
    """check the list of edges is sorted as expected"""
    field_map: Dict[str, SortedField] = dict()
    field_vals: Dict[str, float] = dict()
    new_vals: Dict[str, float] = {}

    for i, sorted_fld in enumerate(fields):
        field_map[sorted_fld.field_name] = sorted_fld
        field_vals[sorted_fld.field_name] = 0 if field_map[sorted_fld.field_name].ascending else float('inf')

    for rupt in edges:
        reset = False
        for fld in field_vals.keys():
            # fld = str(key)
            # print(rupt['node'][fld])
            new_vals[fld] = float(rupt['node'][fld])
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
            """sortby: [{attribute: "magnitude" ascending: false},
                {attribute: "rate_weighted_mean" ascending: false}]""",
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=False, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "magnitude" ascending: false }, {attribute: "rate_weighted_mean"}]',
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=True, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "magnitude" }, {attribute: "rate_weighted_mean"}]',
            [
                SortedField('magnitude', ascending=True, binned=True),
                SortedField('rate_weighted_mean', ascending=True, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "magnitude" ascending: false }, {attribute: "rate_weighted_mean" ascending: false}]',
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=False, binned=False),
            ],
        ),
        # RATE_MAX sorting
        (
            'sortby: [{attribute: "rate_max"}]',
            [
                SortedField('rate_max', ascending=True, binned=False),
            ],
        ),
        (
            'sortby: [{attribute: "rate_max" ascending: false}, {attribute: "magnitude" ascending:false}]',  # 0.25e-4
            [
                SortedField('rate_max', ascending=False, binned=True),
                SortedField('magnitude', ascending=False, binned=False),
            ],
        ),
    ],
)
def test_sorting_and_binning_magnitude(client, query, variable_values, sort_expr, expected):
    print(query)
    executed = client.execute(
        query.replace("# SORT_BY", sort_expr).replace("#FIRST", "30"),
        variable_values=variable_values,
    )

    print(executed)
    rupts = executed['data']['filter_ruptures']
    verify_sorted_edges(rupts['edges'], expected)
    assert rupts['pageInfo']['hasNextPage'] is True


@pytest.mark.parametrize(
    "sort_expr,expected",
    [
        (
            'sortby: [{attribute: "magnitude" ascending: false }, {attribute: "rate_weighted_mean" ascending: false}]',
            [
                SortedField('magnitude', ascending=False, binned=True),
                SortedField('rate_weighted_mean', ascending=False, binned=False),
            ],
        )
    ],
)
@pytest.mark.skip("use this for test hacking")
def test_magnitude_binning(client, query, variable_values, sort_expr, expected):
    print(query)

    LIMIT = 200
    variable_values = {
        "model_id": "NSHM_1.0.0",
        "fault_system": "HIK",
        "location_ids": ['WLG'],
        "minimum_mag": 7,
        "minimum_rate": 1.0e-9,
        "radius_km": 50,
    }

    executed = client.execute(
        query.replace("# SORT_BY", sort_expr).replace("#FIRST", f"{LIMIT}"),
        variable_values=variable_values,
    )

    # print(executed)

    rupts = executed['data']['filter_ruptures']
    # print()
    # for idx, rupt in enumerate(rupts['edges']):
    #     if idx < LIMIT-10:
    #         continue
    #     # for fld in field_vals.keys():
    #     print( rupt['node']['magnitude'], rupt['node']['rate_weighted_mean'] )
    #     # if idx > 20:
    #     #     break

    # print()
    # print(executed)
    verify_sorted_edges(rupts['edges'], expected)
    assert 0
