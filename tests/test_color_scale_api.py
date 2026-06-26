"""Tests for `solvis_graphql_api` package."""

import unittest

from graphene.test import Client

from solvis_graphql_api.schema import schema_root


class TestColorScaleResolvers(unittest.TestCase):
    """
    A resolver returns info abut faults in a given solution inversion (via SolvisStore.
    """

    def setUp(self):
        self.client = Client(schema_root)

    def test_get_colorscale_linear(self):
        QUERY_ONE = """
            query ($name: String!) {
                color_scale(name: $name
                    min_value: 5
                    max_value: 10
                    normalization: LIN
                ) {
                    name
                    min_value
                    color_map {
                        levels
                        hexrgbs
                    }
                }
            }
        """
        executed = self.client.execute(QUERY_ONE, variable_values={"name": "inferno"})
        print(executed)
        assert "color_scale" in executed["data"]
        assert executed["data"]["color_scale"]["name"] == "inferno"

        color_map = executed["data"]["color_scale"]["color_map"]
        assert color_map["levels"][0] == 5.0
        assert color_map["levels"][-1] == 10.0

        assert color_map["hexrgbs"][0] == "#000004"
        assert color_map["hexrgbs"][-1][:2] == "#f"

    def test_get_colorscale_log(self):
        QUERY_ONE = """
            query ($name: String!) {
                color_scale(name: $name
                    min_value: 0.5e-6
                    max_value: 1.0e-3
                    normalization: LOG
                ) {
                    name
                    min_value
                    color_map {
                        levels
                        hexrgbs
                    }
                }
            }
        """
        colors = "inferno"
        executed = self.client.execute(QUERY_ONE, variable_values={"name": colors})
        print(executed)
        assert "color_scale" in executed["data"]
        assert executed["data"]["color_scale"]["name"] == colors

        color_map = executed["data"]["color_scale"]["color_map"]
        assert color_map["levels"][0] == 1.0e-7
        assert color_map["levels"][-1] == 1.0e-3

        assert color_map["hexrgbs"][0] == "#000004"
        assert color_map["hexrgbs"][-1][:2] == "#f"
