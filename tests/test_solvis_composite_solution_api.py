import unittest
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pytest

from graphene.test import Client
from solvis_graphql_api.schema import schema_root


def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


def empty_dataframe(*args, **kwargs):
    return pd.DataFrame()


QUERY = """
    query (
        $model_id: String!
        )
    {
    composite_solution(
        model_id: $model_id

        )
        {
            model_id
            fault_systems
        }
    }
"""


# @mock.patch('solvis_graphql_api.composite_solution_schema.matched_rupture_sections_gdf', side_effect=mock_dataframe)
class TestAnalyseCompositeSolutionResolver(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    @pytest.mark.slow('loads archive file, should use mock instead')
    def test_get_analysis_with_rupture_ids(self):

        executed = self.client.execute(
            QUERY.replace("# FSR", "fault_system_ruptures {fault_system, rupture_ids }"),
            variable_values={"model_id": "NSHM_v1.0.0"},
        )
        print(executed)

        # mock1.assert_called_once()
        # mock1.assert_called_once_with('NSHM_v1.0.0', ["HIK", "CRU", "PUY"], 'WLG', 10000,
        #   min_rate=1e-20, max_rate=None, min_mag=None, max_mag=None)
        self.assertTrue('composite_solution' in executed['data'])
        self.assertTrue('fault_systems' in executed['data']['composite_solution'])
