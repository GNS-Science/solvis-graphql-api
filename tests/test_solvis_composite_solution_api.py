import unittest
import json

# from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root  # , matched_rupture_sections_gdf
from pathlib import Path
import geopandas as gpd
import pandas as pd
import pytest

from graphql_relay import from_global_id, to_global_id


def mock_dataframe(*args, **kwargs):
    with open(Path(Path(__file__).parent, 'fixtures', 'geojson.json'), 'r') as geojson:
        return gpd.read_file(geojson)


def empty_dataframe(*args, **kwargs):
    return pd.DataFrame()


QUERY = """
    query (
        $model_id: String!
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
                # FSR
                # FSS
                # location_geojson
            }
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
            variable_values={
                "model_id": "NSHM_1.0.0",
                "fault_systems": ["HIK", "PUY"],
                "location_codes": ['WLG'],
                "radius_km": 5,
            },
        )
        print(executed)

        # mock1.assert_called_once()
        # mock1.assert_called_once_with('NSHM_1.0.0', ["HIK", "CRU", "PUY"], 'WLG', 10000,
        #   min_rate=1e-20, max_rate=None, min_mag=None, max_mag=None)

        self.assertTrue('analyse_composite_solution' in executed['data'])
        self.assertTrue('analysis' in executed['data']['analyse_composite_solution'])

    def test_get_analysis_fault_system_summaries(self):

        executed = self.client.execute(
            QUERY.replace("# FSS", "fault_system_summaries {fault_system, fault_traces}"),
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

        fss = executed['data']['analyse_composite_solution']['analysis']['fault_system_summaries'][0]

        self.assertTrue('fault_traces' in fss)
        traces = json.loads(fss['fault_traces'])
        print(traces.keys())
        self.assertTrue('id' in traces['features'][0])
        # print(traces['features'][0]['properties'].keys())
        # self.assertTrue(traces['features'][0]['properties']['id'] == '5')


class TestCompositeSolutionRupturePagination(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_page_one_fault_system_rupture_connection(self):

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
                                        rupture_index
                                        fault_surfaces
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

        # paginated
        # - https://relay.dev/graphql/connections.htm
        # - https://graphql.org/learn/pagination/
        # -
        assert fss['ruptures']['edges'][0]['node']['rupture_index'] == 661
        assert fss['ruptures']['edges'][0]['node']['__typename'] == 'CompositeRuptureDetail'
        assert len(fss['ruptures']['edges']) == 10

        print('cursor 0: ', from_global_id(fss['ruptures']['edges'][0]['cursor']))
        print('endCursor: ', from_global_id(fss['ruptures']['pageInfo']['endCursor']))

        assert fss['ruptures']['pageInfo']['hasNextPage'] is True
        # assert 0

    def test_get_page_two_fault_system_rupture_connection(self):

        query = QUERY.replace(
            "# FSR",
            """fault_system_ruptures {
                    rupture_ids
                    ruptures(
                        first: 10
                        after: "%s"
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
                                        rupture_index
                                        fault_system
                                    }
                            }}}
                    }
                """
            % to_global_id("CompositeRuptureDetail", str(9)),
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

        # paginated
        assert fss['ruptures']['edges'][0]['node']['rupture_index'] == 2857
        assert fss['ruptures']['edges'][0]['node']['__typename'] == 'CompositeRuptureDetail'
        assert len(fss['ruptures']['edges']) == 10

        # last edge cursor and page endCursor must agree
        assert (
            from_global_id(fss['ruptures']['edges'][-1]['cursor'])[1]
            == from_global_id(fss['ruptures']['pageInfo']['endCursor'])[1]
        )
        assert from_global_id(fss['ruptures']['edges'][-1]['cursor'])[1] == '19'
        assert from_global_id(fss['ruptures']['pageInfo']['endCursor'])[1] == '19'

        # assert 0


class TestRuptureDetailResolver(unittest.TestCase):
    def setUp(self):

        self.query = """
        query QRY_000 {
            composite_rupture_detail (
            input: {
                model_id: model_id_000
                fault_system: fault_system_000
                rupture_index: rupture_index_000
                })
            {
                model_id
                fault_system
                rupture_index
                fault_surfaces
            }
        }
        """

        self.batch_query = """
        QRY_000: composite_rupture_detail (
            input: {
                model_id: model_id_000
                fault_system: fault_system_000
                rupture_index: rupture_index_000
                })
            {
                model_id
                fault_system
                rupture_index
                fault_surfaces
            }
        """

        self.client = Client(schema_root)

    @pytest.mark.slow('loads archive file, should use mock instead')
    def test_get_single_rupture(self):

        qry = (
            self.query.replace("model_id_000", '"NSHM_1.0.0"')
            .replace("fault_system_000", '"HIK"')
            .replace("rupture_index_000", str(5))
        )

        print(qry)

        executed = self.client.execute(qry)
        print(executed)

        crd = executed['data']['composite_rupture_detail']

        self.assertTrue('fault_surfaces' in crd)
        traces = json.loads(crd['fault_surfaces'])

        self.assertTrue('id' in traces['features'][0])
        assert traces['features'][0]['id'] == "(\'HIK\', 5)"

    @pytest.mark.slow('loads archive file, should use mock instead')
    def test_get_batched_rupture(self):

        qry = ''
        for n in range(5, 8):
            qry += (
                self.batch_query.replace("QRY_000", f"QRY_{n}")
                .replace("model_id_000", '"NSHM_1.0.0"')
                .replace("fault_system_000", '"HIK"')
                .replace("rupture_index_000", str(n))
            )

        qry = "query BATCHED {\n" + qry + "\n}"

        print(qry)

        executed = self.client.execute(qry)

        print(executed)

        crd = executed['data']['QRY_5']

        self.assertTrue('fault_surfaces' in crd)
        traces = json.loads(crd['fault_surfaces'])

        self.assertTrue('id' in traces['features'][0])
        assert traces['features'][0]['id'] == "(\'HIK\', 5)"

        # assert 0
