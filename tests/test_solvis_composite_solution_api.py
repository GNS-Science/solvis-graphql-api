import unittest
import json
from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root  # , matched_rupture_sections_gdf
from pathlib import Path
import geopandas as gpd
import pandas as pd
import solvis_graphql_api.composite_solution_schema
import pytest

def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


def empty_dataframe(*args, **kwargs):
    return pd.DataFrame()


QUERY = """
    query (
        $model_id: ID!
        $location_codes: [String]!
        $fault_systems: [String]!
        $radius_km: Int
        )
    {
    analyse_composite_solution(
        input: {
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
                fault_system_ruptures {fault_system, rupture_ids }
                # fault_system_geojson {fault_system, fault_traces}
                location_geojson
            }
        }
    }
"""


# @mock.patch('solvis_graphql_api.composite_solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
class TestSolutionFaultsResolver(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    @pytest.mark.slow('loads archive file, should use mock instead')
    def test_get_analysis(self):

        executed = self.client.execute(
            QUERY,
            variable_values={"model_id": "NSHM_1.0.0", "fault_systems": ["HIK", "PUY"], "location_codes": ['WLG'], "radius_km": 5},  # this is in PROD !
        )
        print(executed)

        # mock1.assert_called_once()
        # mock1.assert_called_once_with('NSHM_1.0.0', ["HIK", "CRU", "PUY"], 'WLG', 10000, min_rate=1e-20, max_rate=None, min_mag=None, max_mag=None)

        self.assertTrue('analyse_composite_solution' in executed['data'])
        self.assertTrue('analysis' in executed['data']['analyse_composite_solution'])

    # def test_get_analysis_geojson(self, mock1):

    #     executed = self.client.execute(
    #         QUERY,
    #         variable_values={"solution_id": "NANA", "location_codes": ['WLG'], "radius_km": 10},  # this is in PROD !
    #     )

    #     gj = json.loads(executed['data']['analyse_solution']['analysis']['fault_sections_geojson'])

    #     self.assertTrue('features' in gj)
    #     # print(gj.get('features')[0])
    #     self.assertTrue('id' in gj['features'][0])
    #     self.assertTrue(gj['features'][0]['properties']['id'] == '5')

    # def test_default_style(self, mock1):
    #     executed = self.client.execute(
    #         QUERY,
    #         variable_values={"solution_id": "NANA", "location_codes": ["WLG"], "radius_km": 10},
    #     )
    #     gj = json.loads(executed['data']['analyse_solution']['analysis']['fault_sections_geojson'])
    #     self.assertEqual(gj['features'][0]['properties']['stroke-color'], 'black')

    # def test_get_analysis_geojson_without_location_filter(self, mock1):
    #     executed = self.client.execute(
    #         QUERY,
    #         variable_values={"solution_id": "NANA", "location_codes": [], "radius_km": 0},  # this is in PROD !
    #     )
    #     print(executed)
    #     gj = json.loads(executed['data']['analyse_solution']['analysis']['fault_sections_geojson'])

    #     self.assertTrue('features' in gj)
    #     # print(gj.get('features')[0])
    #     self.assertTrue('id' in gj['features'][0])
    #     self.assertTrue(gj['features'][0]['properties']['id'] == '5')


