from unittest.mock import patch

import pytest
import json
from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY = """
query {
  filter_rupture_sections(
      filter:{
      model_id: "NSHM_v1.0.4",
      corupture_parent_fault_name: "Masterton",
      location_ids: [],
      fault_system: "CRU",
      radius_km: 100
      minimum_rate: 1.0e-9
      minimum_mag: 7.2
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
        # MFD # mfd_histogram
  }
}
"""


@pytest.fixture(scope='class')
def client():
    return Client(schema_root)


@patch(
    'solvis_graphql_api.composite_solution.cached.get_rupture_ids', lambda *args, **kwargs: [n for n in range(300, 400)]
)
@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', False)
class TestFilterRptureSections:
    def test_get_fault_surfaces_styled(self, client):

        executed = client.execute(
            QUERY.replace(
                "# GEOJSON",
                "fault_surfaces( style: { stroke_color: \"silver\" fill_color: \"silver\" fill_opacity:0.2 })",
            )
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_surfaces'] is not None

        f0 = {
            "id": "260.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 2,
                "Magnitude.max": 7.532549858093262,
                "Magnitude.mean": 7.515434741973877,
                "Magnitude.min": 7.498319625854492,
                "rate_weighted_mean.sum": 7.619245934620267e-06,
                "FaultID": 260,
                "FaultName": "Carterton, Subsection 0",
                "DipDeg": 75.0,
                "Rake": -160.0,
                "LowDepth": 13.76,
                "UpDepth": 0.0,
                "DipDir": 165.3,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 62,
                "ParentName": "Carterton",
                "fill": "silver",
                "fill-opacity": 0.2,
                "stroke": "silver",
                "stroke-width": 1,
                "stroke-opacity": 1.0,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [176.1166, -40.8611],
                        [176.0965, -40.8776],
                        [176.072, -40.8914],
                        [176.05144719857643, -40.8961126443576],
                        [176.06258379770742, -40.92818455855194],
                        [176.08313580497375, -40.92347191428335],
                        [176.10763348053365, -40.90967191454394],
                        [176.12773070343263, -40.89317191485537],
                        [176.1166, -40.8611],
                    ]
                ],
            },
        }

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])
        assert f1['features'][0] == f0

    def test_get_min_magnitude(self, client):

        executed = client.execute(QUERY)
        print(executed)
        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.240527629852295

    def test_get_mfd_histogram(self, client):
        executed = client.execute(
            QUERY.replace("# MFD", "mfd_histogram{ bin_center rate cumulative_rate}"),
        )

        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert 'mfd_histogram' in executed['data']['filter_rupture_sections']

        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.240527629852295
        assert (
            pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
            == 0.00018954463303089142
        )
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['rate']) == 0.0
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['bin_center']) == 6.85
