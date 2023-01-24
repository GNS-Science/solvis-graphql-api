"""Tests for `solvis_graphql_api` package."""

import unittest
import json
from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root  # , matched_rupture_sections_gdf
from solvis_graphql_api.solvis_graphql_api import create_app
from pathlib import Path
import geopandas as gpd


def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


QUERY = """
    query (
        $solution_id: ID!
        $location_codes: [String!]
        $radius_km: Int!
        )
    {
    analyse_solution(
        input: {
            solution_id: $solution_id
            location_codes: $location_codes
            radius_km: $radius_km
            }
        )
        {
            analysis {
                solution_id
                # fault_sections { fault_id}
                geojson
            }
        }
    }
"""


class TestFlaskApp(unittest.TestCase):
    """Tests the basic app create."""

    def test_create_app(self):
        app = create_app()
        print(app)
        assert app


@mock.patch('solvis_graphql_api.schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
class TestSolutionFaultsResolver(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_analysis(self, mock1):

        executed = self.client.execute(
            QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ['WLG'], "radius_km": 10},  # this is in PROD !
        )
        # print(executed)

        mock1.assert_called_once()
        mock1.assert_called_once_with('NANA', 'WLG', 10000, min_rate=1e-20, max_rate=None, min_mag=None, max_mag=None)

        self.assertTrue('analyse_solution' in executed['data'])
        self.assertTrue('analysis' in executed['data']['analyse_solution'])

    def test_get_analysis_geojson(self, mock1):

        executed = self.client.execute(
            QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ['WLG'], "radius_km": 10},  # this is in PROD !
        )

        gj = json.loads(executed['data']['analyse_solution']['analysis']['geojson'])

        self.assertTrue('features' in gj)
        # print(gj.get('features')[0])
        self.assertTrue('id' in gj['features'][0])
        self.assertTrue(gj['features'][0]['properties']['id'] == '5')
