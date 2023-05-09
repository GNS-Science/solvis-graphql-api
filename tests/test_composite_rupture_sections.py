from unittest.mock import patch

import pytest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY = """
query {
  filter_rupture_sections(
    filter:{
      model_id: "NSHM_v1.0.4"
      location_ids: ["MRO", "WLG"]
      fault_system: "CRU",
      radius_km: 100
      minimum_rate: 1.0e-9
      minimum_mag: 7.2
    }
    color_scale: { name: "inferno" }
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


def notest_get_analysis_with_rupture_ids(self, client):

    executed = client.execute(
        QUERY.replace("# FSR", "fault_system_ruptures {fault_system, rupture_ids }"),
        variable_values={"model_id": "NSHM_v1.0.0"},
    )
    print(executed)

    self.assertTrue('composite_solution' in executed['data'])
    self.assertTrue('fault_systems' in executed['data']['composite_solution'])


@patch(
    'solvis_graphql_api.composite_solution.cached.get_rupture_ids', lambda *args, **kwargs: [n for n in range(300, 400)]
)
@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', False)
def test_get_mfd_histogram(client):
    executed = client.execute(
        QUERY.replace("# MFD", "mfd_histogram{ bin_center rate cumulative_rate}"),
    )

    print(executed)

    assert 'filter_rupture_sections' in executed['data']
    assert 'mfd_histogram' in executed['data']['filter_rupture_sections']

    assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 8.0981178283691
    assert (
        pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
        == 2.03907688955951e-06
    )
    assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['rate']) == 0.0
    assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['bin_center']) == 6.85
