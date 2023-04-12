"""Tests for `solvis_graphql_api` package."""

import unittest

from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY_ONE = """
    query ($location_ids: [String]!) {
      locations_by_id(location_ids: $location_ids) {
        total_count
        edges {
          node {
            ... on LocationDetail {
              id
              location_id
              name
              longitude
              latitude
              # GEO

        }
      }
    }
  }
}
"""


class TestLocationResolver(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_locations(self):
        executed = self.client.execute(QUERY_ONE, variable_values={'location_ids': ["WLG", "MRO"]})
        print(executed)
        assert 'locations_by_id' in executed['data']
        assert executed['data']['locations_by_id']['edges'][0]['node'] == {
            'id': 'TG9jYXRpb25EZXRhaWw6V0xH',
            "location_id": "WLG",
            "name": "Wellington",
            "longitude": 174.78,
            "latitude": -41.3,
        }

    def test_get_locations_with_geojson(self):
        qry = QUERY_ONE.replace(
            "# GEO",
            """radius_geojson(
            radius_km:10
            style:{stroke_color: "royalblue" stroke_width: 3 stroke_opacity: 0.5 }
          )
        """,
        )

        executed = self.client.execute(qry, variable_values={'location_ids': ["WLG"]})

        assert 'locations_by_id' in executed['data']
        assert executed['data']['locations_by_id']['edges'][0]['node']['radius_geojson'] is not None
