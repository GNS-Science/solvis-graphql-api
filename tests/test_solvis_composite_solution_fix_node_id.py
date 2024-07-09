import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

# from unittest import mock
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id

from solvis_graphql_api.schema import schema_root  # , matched_rupture_sections_gdf


def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


def empty_dataframe(*args, **kwargs):
    return pd.DataFrame()


@pytest.fixture(autouse=True)
def configure_archive(archive_fixture):
    pass


QUERY = """
    query (
        $model_id: String!
        $location_codes: [String]!
        $fault_systems: [String]!
        $radius_km: Int
        )
    {
    analyse_composite_solution(
        filter: {
            model_id: $model_id
            location_codes: $location_codes
            fault_systems: $fault_systems
            radius_km: $radius_km
            minimum_rate: 1.0e-6
            minimum_mag: 7.83
            }
        )
        {
            analysis {
                model_id
                # FSR
                # FSS
                # location_geojson
            }
        }
    }
"""


# @mock.patch('solvis_graphql_api.composite_solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)

# TODO Remove t
class TestCompositeSolutionRupturePagination(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def notest_get_page_one_fault_system_rupture_connection(self):

        query = QUERY.replace(
            "# FSR",
            """fault_system_ruptures {
                    ruptures(
                        first: 10
                        # after:
                        )
                         {
                            total_count
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                            edges {
                                cursor
                                node {
                                    __typename
                                    ... on CompositeRuptureDetail {
                                        id
                                        fault_system
                                        rupture_index
                                    }
                            }}}
                    }
                """,
        )
        print(query)
        executed = self.client.execute(
            query,
            variable_values={
                "model_id": "NSHM_1.0.0",
                "fault_systems": ["HIK", "PUY"],
                "location_codes": ['WLG'],
                "minimum_mag": 8.3,
                "minimum_rate": 1.0e-6,
                "radius_km": 5,
            },
        )

        print(executed)
        self.assertTrue('analysis' in executed['data']['analyse_composite_solution'])

        fss = executed['data']['analyse_composite_solution']['analysis']['fault_system_ruptures'][0]
        self.assertTrue('ruptures' in fss)

        assert fss['ruptures']['edges'][0]['node']['rupture_index'] == 661
        assert len(fss['ruptures']['edges']) == 10

        print('cursor 0: ', from_global_id(fss['ruptures']['edges'][0]['cursor']))
        print('endCursor: ', from_global_id(fss['ruptures']['pageInfo']['endCursor']))

        assert not fss['ruptures']['edges'][0]['node']['id'] == fss['ruptures']['edges'][9]['node']['id']
        node = fss['ruptures']['edges'][0]['node']
        assert node['id'] == to_global_id('CompositeRuptureDetail', f'{node["fault_system"]}:{node["rupture_index"]}')
