"""Tests for `solvis_graphql_api` package."""

import unittest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root
from solvis_graphql_api.solvis_graphql_api import create_app


class TestFlaskApp(unittest.TestCase):
    """Tests the basic app create."""

    def test_create_app(self):
        app = create_app()
        print(app)
        assert app


class TestSchemaAboutResolver(unittest.TestCase):
    """
    A simple `About` resolver returns some metadata about the API.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_about(self):

        QUERY = """
        query {
            about
        }
        """

        executed = self.client.execute(QUERY)
        print(executed)
        self.assertTrue('Hello World' in executed['data']['about'])