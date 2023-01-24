"""Tests for `solvis_graphql_api` package."""

import unittest
import json
from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root, RadiiSet
from solvis_graphql_api.solvis_graphql_api import create_app

QUERY_ALL = """
    query {
        get_locations {
            code
            name
        }
    }
"""

QUERY_ONE = """
    query ($location_code: String!) {
        get_location(location_code: $location_code) {
            code
            name
            latitude
            longitude
        }
    }
"""

class TestLocationResolvers(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_one_location(self):
        executed = self.client.execute(
            QUERY_ONE,
            variable_values={'location_code':'ZQN'}
        )
        print(executed)
        self.assertTrue('get_location' in executed['data'])
        self.assertEqual(executed['data']['get_location'], {'code': 'ZQN', 'name': 'Queenstown', 'latitude': -45.02, 'longitude': 168.69})

    def test_get_one_location_miss(self):
        executed = self.client.execute(
            QUERY_ONE,
            variable_values={'location_code':'ZOG'}
        )
        print(executed)
        self.assertTrue('errors' in executed)
        self.assertTrue('message' in executed['errors'][0])
        self.assertTrue("ZOG" in executed['errors'][0]['message'])

    def test_get_all_locations(self):
        executed = self.client.execute(
            QUERY_ALL,
            variable_values={},
        )
        print(executed)
        self.assertTrue('get_locations' in executed['data'])
        self.assertTrue('code' in executed['data']['get_locations'][0])
        self.assertTrue('code' in executed['data']['get_locations'][0])
        self.assertEqual('GMN', executed['data']['get_locations'][5]['code'])