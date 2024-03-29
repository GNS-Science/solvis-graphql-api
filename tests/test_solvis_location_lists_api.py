"""Tests for `solvis_graphql_api` package."""

import unittest

from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY_ALL = """
    query {
        get_location_lists {
            list_id
            location_ids
        }
    }
"""

QUERY_ONE = """
    query ($list_id: String!) {
        get_location_list(list_id: $list_id) {
            list_id
            location_ids
            locations { location_id }
        }
    }
"""


class TestLocationResolvers(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_one_location_list(self):
        executed = self.client.execute(QUERY_ONE, variable_values={'list_id': 'NZ2'})
        print(executed)
        self.assertTrue('get_location_list' in executed['data'])
        self.assertEqual(executed['data']['get_location_list']['list_id'], 'NZ2')
        assert sorted(executed['data']['get_location_list']['location_ids']) == [
            'AKL',
            'CHC',
            'DUD',
            'HLZ',
            'NPL',
            'ROT',
            'WLG',
        ]

    def test_get_one_location_list_miss(self):
        executed = self.client.execute(QUERY_ONE, variable_values={'list_id': 'USA'})
        print(executed)
        self.assertTrue('errors' in executed)
        self.assertTrue('message' in executed['errors'][0])
        self.assertTrue("USA" in executed['errors'][0]['message'])

    def test_get_all_location_lists(self):
        executed = self.client.execute(
            QUERY_ALL,
            variable_values={},
        )
        print(executed)
        self.assertTrue('get_location_lists' in executed['data'])
        self.assertTrue('list_id' in executed['data']['get_location_lists'][0])
        self.assertTrue('list_id' in executed['data']['get_location_lists'][0])
        self.assertEqual('ALL', executed['data']['get_location_lists'][-1]['list_id'])
