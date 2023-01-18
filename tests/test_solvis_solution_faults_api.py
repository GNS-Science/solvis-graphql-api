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

class TestSolutionFaultsResolver(unittest.TestCase):
    """
    A resolver returns info aobut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_about(self):

        QUERY = """
        query ($solution_id: ID!) {
          analyse_solution( input: {solution_id: $solution_id} )
            {
                analysis {
                    solution_id
                    # fault_sections { fault_id}
                }
            }
        }
        """

        executed = self.client.execute(QUERY, variable_values={"solution_id": "R2VuZXJhbFRhc2s6MQ=="})
        print(executed)
        self.assertTrue('analyse_solution' in executed['data'])

