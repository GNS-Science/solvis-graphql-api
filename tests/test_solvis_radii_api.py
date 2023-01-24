"""Tests for `solvis_graphql_api` package."""

import unittest
import json
from unittest import mock
from graphene.test import Client

from solvis_graphql_api.schema import schema_root, RadiiSet
from solvis_graphql_api.solvis_graphql_api import create_app

def mock_radii_set(*args, **kwargs):
    return RadiiSet(6, [1,2,3])

QUERY_ALL = """
    query {
        get_radii_sets {
            radii_set_id
            radii
        }
    }
"""

QUERY_ONE = """
    query ($radii_set_id: Int!) {
        get_radii_set(radii_set_id: $radii_set_id) {
            radii_set_id
            radii
        }
    }
"""

class TestFlaskApp(unittest.TestCase):
    """Tests the basic app create."""

    def test_create_app(self):
        app = create_app()
        print(app)
        assert app


# @mock.patch('solvis_graphql_api.schema.get_one_radii_set', side_effect=mock_radii_set)
class TestRadiiResolvers(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_all_radii_set(self):
        executed = self.client.execute(
            QUERY_ALL,
            variable_values={},
        )
        print(executed)
        self.assertTrue('get_radii_sets' in executed['data'])
        self.assertTrue('radii_set_id' in executed['data']['get_radii_sets'][0])
        self.assertTrue('radii_set_id' in executed['data']['get_radii_sets'][0])
        self.assertEqual(6, executed['data']['get_radii_sets'][5]['radii_set_id'])

    def test_get_one_radii_set(self):

        executed = self.client.execute(
            QUERY_ONE,
            variable_values={'radii_set_id':6}
        )
        print(executed)
        self.assertTrue('get_radii_set' in executed['data'])
        self.assertTrue('radii_set_id' in executed['data']['get_radii_set'])
        self.assertEqual(executed['data']['get_radii_set']['radii_set_id'], 6)
        self.assertEqual(executed['data']['get_radii_set']['radii'],[10000, 20000, 30000, 40000, 50000, 100000] )

    def test_get_one_radii_set_miss(self):
        executed = self.client.execute(
            QUERY_ONE,
            variable_values={'radii_set_id':7}
        )
        print(executed)
        self.assertTrue('errors' in executed)
        self.assertTrue('message' in executed['errors'][0])
        self.assertTrue("7" in executed['errors'][0]['message'])
