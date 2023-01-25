"""Tests for `solvis_graphql_api` package."""

import unittest
import json
from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root  # , matched_rupture_sections_gdf
from pathlib import Path
import geopandas as gpd
import pandas as pd
import solvis_graphql_api.solution_schema


def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


def empty_dataframe(*args, **kwargs):
    return pd.DataFrame()


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
                ruptures_geojson
            }
        }
    }
"""


@mock.patch('solvis_graphql_api.solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
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

        gj = json.loads(executed['data']['analyse_solution']['analysis']['ruptures_geojson'])

        self.assertTrue('features' in gj)
        # print(gj.get('features')[0])
        self.assertTrue('id' in gj['features'][0])
        self.assertTrue(gj['features'][0]['properties']['id'] == '5')


@mock.patch('solvis_graphql_api.solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
class TestSolutionLocationsResolver(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

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
                    location_geojson
                }
            }
        }
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_analysis_location_features(self, mock1):
        executed = self.client.execute(
            TestSolutionLocationsResolver.QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ["WLG"], "radius_km": 10},
        )

        loc_gj = json.loads(executed['data']['analyse_solution']['analysis']['location_geojson'])
        print(loc_gj)
        self.assertTrue('features' in loc_gj)
        # print(loc_gj.get('features')[0])
        self.assertTrue('id' in loc_gj['features'][0])
        self.assertTrue(loc_gj['features'][0]['id'] == 'WLG')
        self.assertTrue(
            loc_gj['features'][0]['geometry']['coordinates'][0][0] == [174.8997077027642, -41.299937994600704]
        )

    def test_location_features_default_style(self, mock1):
        executed = self.client.execute(
            TestSolutionLocationsResolver.QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ["WLG"], "radius_km": 10},
        )
        loc_gj = json.loads(executed['data']['analyse_solution']['analysis']['location_geojson'])
        print(loc_gj)
        self.assertTrue(loc_gj['features'][0]['properties']['stroke-color'] == 'lightblue')

    def test_get_analysis_location_features_100km(self, mock1):
        executed = self.client.execute(
            TestSolutionLocationsResolver.QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ['WLG', "LVN"], "radius_km": 100},
        )
        print(executed)
        loc_gj = json.loads(executed['data']['analyse_solution']['analysis']['location_geojson'])
        print(loc_gj)

        self.assertTrue('features' in loc_gj)
        # print(loc_gj.get('features')[0])
        self.assertTrue('id' in loc_gj['features'][0])
        self.assertTrue(loc_gj['features'][0]['id'] == 'WLG')
        self.assertTrue(
            loc_gj['features'][0]['geometry']['coordinates'][0][0] == [175.97700192517442, -41.29379987785121]
        )


class TestSolutionFaultsResolverExceptions(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    @mock.patch('solvis_graphql_api.solution_schema.matched_rupture_sections_gdf', side_effect=empty_dataframe)
    def test_get_analysis_empty_dataframe(self, mock1):
        executed = self.client.execute(
            QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ['WLG'], "radius_km": 10},  # this is in PROD !
        )
        self.assertTrue('errors' in executed)
        self.assertTrue('message' in executed['errors'][0])
        self.assertTrue("No ruptures satisfy the filter" in executed['errors'][0]['message'])

    @mock.patch('solvis_graphql_api.solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
    def test_get_analysis_large_dataframe(self, mock1):
        default_limit = int(solvis_graphql_api.solution_schema.RUPTURE_SECTION_LIMIT)
        solvis_graphql_api.solution_schema.RUPTURE_SECTION_LIMIT = 30

        executed = self.client.execute(
            QUERY,
            variable_values={"solution_id": "NANA", "location_codes": ['WLG'], "radius_km": 10},  # this is in PROD !
        )

        solvis_graphql_api.solution_schema.RUPTURE_SECTION_LIMIT = default_limit

        self.assertTrue('errors' in executed)
        self.assertTrue('message' in executed['errors'][0])
        self.assertTrue("Too many rupture sections" in executed['errors'][0]['message'])
