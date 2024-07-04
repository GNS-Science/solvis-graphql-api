import json
import unittest
from unittest.mock import patch

import pytest
from graphene.test import Client
from graphql_relay import from_global_id, to_global_id

from solvis_graphql_api.schema import schema_root

@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', True)
class TestRupturePagination(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)
        self.query = """
            query (
                    $model_id: String!
                    $location_ids: [String]!
                    $fault_system: String!
                    $radius_km: Int
                    )
                {
              filter_ruptures(
                first:3
                # AFTER
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
                  }
                }
              }
            }

        """

    def test_get_page_one(self):

        print(self.query)
        executed = self.client.execute(
            self.query,
            variable_values={
                "model_id": "NSHM_v1.0.0",
                "fault_system": "HIK",
                "location_ids": ['WLG'],
                "minimum_mag": 8.3,
                "minimum_rate": 1.0e-6,
                "radius_km": 5,
            },
        )

        print(executed)

        rupts = executed['data']['filter_ruptures']
        self.assertTrue('edges' in rupts)

        # paginated
        # - https://relay.dev/graphql/connections.htm
        # - https://graphql.org/learn/pagination/
        # -
        assert rupts['edges'][0]['node']['rupture_index'] == 661
        assert rupts['edges'][0]['node']['__typename'] == 'CompositeRuptureDetail'
        assert len(rupts['edges']) == 3

        print('cursor 0: ', from_global_id(rupts['edges'][0]['cursor']))
        print('endCursor: ', from_global_id(rupts['pageInfo']['endCursor']))

        assert rupts['pageInfo']['hasNextPage'] is True
        # assert 0

    def test_get_page_two(self):

        query = self.query.replace("# AFTER", "after: \"%s\"" % to_global_id("RuptureDetailConnectionCursor", str(3)))

        print(query)
        executed = self.client.execute(
            query,
            variable_values={
                "model_id": "NSHM_v1.0.0",
                "fault_system": "HIK",
                "location_ids": ['WLG'],
                "minimum_mag": 8.3,
                "minimum_rate": 1.0e-6,
                "radius_km": 5,
            },
        )

        print(executed)

        rupts = executed['data']['filter_ruptures']
        assert 'edges' in rupts
        assert len(rupts['edges']) == 3
        assert from_global_id(rupts['edges'][0]['cursor']) == ("RuptureDetailConnectionCursor", "4")

@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', True)
class TestRuptureDetailResolver(unittest.TestCase):
    def setUp(self):

        self.query = """
        query QRY_000 {
            composite_rupture_detail (
            filter: {
                model_id: model_id_000
                fault_system: fault_system_000
                rupture_index: rupture_index_000
                })
            {
                id # this is a NODE
                model_id
                fault_system
                fault_surfaces

                rupture_index
                magnitude
                rake_mean
                length
                area
                rate_count
                rate_max
                rate_min
                rate_weighted_mean
            }
        }
        """

        self.batch_query = """
        QRY_000: composite_rupture_detail (
            filter: {
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
            self.query.replace("model_id_000", '"NSHM_v1.0.0"')
            .replace("fault_system_000", '"HIK"')
            .replace("rupture_index_000", str(5))
        )

        print(qry)

        executed = self.client.execute(qry)
        print(executed)

        crd = executed['data']['composite_rupture_detail']

        assert crd['id'] == to_global_id("CompositeRuptureDetail", 'HIK:5')

        assert isinstance(crd['rate_weighted_mean'], float)
        assert isinstance(crd['rate_max'], float)
        assert isinstance(crd['rate_min'], float)
        assert isinstance(crd['rate_count'], int)
        assert isinstance(crd['area'], float)
        assert isinstance(crd['length'], float)
        assert isinstance(crd['magnitude'], float)
        assert isinstance(crd['rake_mean'], float)

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
                .replace("model_id_000", '"NSHM_v1.0.0"')
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
