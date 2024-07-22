import json

import pytest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root


QUERY = """
query {
  filter_rupture_sections(
      filter:{
          model_id: "NSHM_v1.0.4",
          corupture_fault_names: ["Pokeno"],
          location_ids: ["AKL"],
          fault_system: "CRU",
          radius_km: 100
          minimum_rate: 1.0e-9
          minimum_mag: 7.2
          filter_set_options: {
            multiple_locations:INTERSECTION
            multiple_faults: INTERSECTION
            locations_and_faults: INTERSECTION
            }
        }
  )
  {
        model_id
        section_count
        max_magnitude
        min_magnitude
        max_participation_rate
        min_participation_rate
        # GEOJSON # fault_surfaces
        # MFD # mfd_histogram
  }
}
"""


@pytest.fixture(scope='class')
def client():
    return Client(schema_root)


class TestFilterRptureSections:
    def test_get_fault_surfaces_styled(self, client, archive_fixture_tiny):
        executed = client.execute(
            QUERY.replace(
                "# GEOJSON",
                "fault_surfaces( style: { stroke_color: \"silver\" fill_color: \"silver\" fill_opacity:0.2 })",
            )
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_surfaces'] is not None

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])
        assert f1['features'][0]['properties']['fill'] == 'silver'
        assert f1['features'][0]['properties']['fill-opacity'] == 0.2
        assert f1['features'][0]['properties']['stroke'] == 'silver'

    def test_get_min_magnitude(self, client, archive_fixture_tiny):
        executed = client.execute(QUERY)
        print(executed)
        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.285887718200684

    def test_get_mfd_histogram(self, client, archive_fixture_tiny):

        executed = client.execute(
            QUERY.replace("# MFD", "mfd_histogram{ bin_center rate cumulative_rate}"),
        )

        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert 'mfd_histogram' in executed['data']['filter_rupture_sections']

        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['rate']) == 0.0
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['bin_center']) == 6.85
        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.285887718200684
        assert (
            pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
            == 3.237532655475661e-05
        )


class TestFilterRuptureSectionsTiny:
    def test_get_mfd_histogram_tiny(self, client, archive_fixture_tiny):
        QUERY = """
            query {
              filter_rupture_sections(
                  filter:{
                  model_id: "NSHM_v1.0.4",
                  corupture_fault_names: ["Pokeno"],
                  location_ids: [],
                  fault_system: "CRU",
                  radius_km: 100
                  minimum_rate: 1.0e-20
                  minimum_mag: 4.2
                  filter_set_options: {
                    multiple_locations:INTERSECTION
                    multiple_faults: INTERSECTION
                    locations_and_faults: INTERSECTION
                    }
                }
                # color_scale: { name: "inferno" }
              )
              {
                    model_id
                    section_count
                    max_magnitude
                    min_magnitude
                    max_participation_rate
                    min_participation_rate
                    # GEOJSON # fault_surfaces
                    mfd_histogram{ bin_center rate cumulative_rate}
              }
            }
        """
        executed = client.execute(QUERY)

        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert 'mfd_histogram' in executed['data']['filter_rupture_sections']

        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.285887718
        assert (
            pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
            == 3.237532655475661e-05
        )
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['rate']) == 0.0
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['bin_center']) == 6.85
