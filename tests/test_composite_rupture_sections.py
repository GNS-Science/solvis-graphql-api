import json
from unittest.mock import patch

import pytest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY = """
query {
  filter_rupture_sections(
    filter:{
      model_id: "NSHM_v1.0.0"
      location_ids: ["MRO", "WLG"]
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
    'solvis_graphql_api.composite_solution.cached.get_location_radius_rupture_ids',
    lambda *args, **kwargs: [n for n in range(300, 400)],
)
@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', True)
class TestFilterRptureSections:
    def test_get_fault_surfaces_styled(self, client, archive_fixture):

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
            "id": "5.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 40,
                "Magnitude.max": 8.225152015686035,
                "Magnitude.mean": 7.9513068199157715,
                "Magnitude.min": 7.600510597229004,
                "rate_weighted_mean.sum": 0.0001145526985055767,
                "FaultID": 5,
                "FaultName": "Akatarawa, Subsection 0",
                "DipDeg": 75.0,
                "Rake": 160.0,
                "LowDepth": 20.0,
                "UpDepth": 0.0,
                "DipDir": 299.6,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 2,
                "ParentName": "Akatarawa",
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
                        [175.0372, -41.1225],
                        [175.0698, -41.1007],
                        [175.08914675459422, -41.07156421641177],
                        [175.03358204398168, -41.04774561448366],
                        [175.0142106677956, -41.07688138436491],
                        [174.9815922217239, -41.098681374101105],
                        [175.0372, -41.1225],
                    ]
                ],
            },
        }
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])
        assert f1['features'][0] == f0

    def test_get_fault_surfaces_scaled_styled(self, client, archive_fixture):

        executed = client.execute(
            QUERY.replace(
                "# GEOJSON", "fault_surfaces( style: { fill_opacity: 0.5 } color_scale: { name:\"inferno\" })"
            )
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_surfaces'] is not None

        f0 = {
            "id": "5.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 40,
                "Magnitude.max": 8.225152015686035,
                "Magnitude.mean": 7.9513068199157715,
                "Magnitude.min": 7.600510597229004,
                "rate_weighted_mean.sum": 0.0001145526985055767,
                "FaultID": 5,
                "FaultName": "Akatarawa, Subsection 0",
                "DipDeg": 75.0,
                "Rake": 160.0,
                "LowDepth": 20.0,
                "UpDepth": 0.0,
                "DipDir": 299.6,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 2,
                "ParentName": "Akatarawa",
                "fill": "#fcffa4",
                "fill-opacity": 0.5,
                "stroke": "#fcffa4",
                "stroke-width": 1,
                "stroke-opacity": 1.0,
            },
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [175.0372, -41.1225],
                        [175.0698, -41.1007],
                        [175.08914675459422, -41.07156421641177],
                        [175.03358204398168, -41.04774561448366],
                        [175.0142106677956, -41.07688138436491],
                        [174.9815922217239, -41.098681374101105],
                        [175.0372, -41.1225],
                    ]
                ],
            },
        }
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])
        assert f1['features'][0] == f0

    def test_get_min_magnitude(self, client, archive_fixture):

        executed = client.execute(QUERY)
        print(executed)
        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.205872535705566

    def test_get_mfd_histogram(self, client, archive_fixture):
        executed = client.execute(
            QUERY.replace("# MFD", "mfd_histogram{ bin_center rate cumulative_rate}"),
        )

        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert 'mfd_histogram' in executed['data']['filter_rupture_sections']

        assert pytest.approx(executed['data']['filter_rupture_sections']['min_magnitude']) == 7.205872535705566
        assert (
            pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
            == 0.004330548457801342
        )
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['rate']) == 0.0
        assert pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['bin_center']) == 6.85

    def test_get_fault_traces_no_style(self, client, archive_fixture):

        executed = client.execute(
            QUERY.replace("# GEOJSON", "fault_traces"),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f0 = {
            "id": "5.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 40,
                "Magnitude.max": 8.225152015686035,
                "Magnitude.mean": 7.9513068199157715,
                "Magnitude.min": 7.600510597229004,
                "rate_weighted_mean.sum": 0.0001145526985055767,
                "FaultID": 5,
                "FaultName": "Akatarawa, Subsection 0",
                "DipDeg": 75.0,
                "Rake": 160.0,
                "LowDepth": 20.0,
                "UpDepth": 0.0,
                "DipDir": 299.6,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 2,
                "ParentName": "Akatarawa",
                # "fill": "green",
                # "fill-opacity": "0.5",
                # "stroke": "green",
                # "stroke-width": 1,
                # "stroke-opacity": 1.0,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[175.0372, -41.1225], [175.0698, -41.1007], [175.08914675459422, -41.07156421641177]],
            },
        }
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])
        assert f1['features'][0] == f0

    def test_get_fault_traces_line_style(self, client, archive_fixture):

        executed = client.execute(
            QUERY.replace("# GEOJSON", "fault_traces(style: {stroke_color: \"purple\"})"),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f0 = {
            "id": "5.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 40,
                "Magnitude.max": 8.225152015686035,
                "Magnitude.mean": 7.9513068199157715,
                "Magnitude.min": 7.600510597229004,
                "rate_weighted_mean.sum": 0.0001145526985055767,
                "FaultID": 5,
                "FaultName": "Akatarawa, Subsection 0",
                "DipDeg": 75.0,
                "Rake": 160.0,
                "LowDepth": 20.0,
                "UpDepth": 0.0,
                "DipDir": 299.6,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 2,
                "ParentName": "Akatarawa",
                "stroke": "purple",
                "stroke-width": 1,
                "stroke-opacity": 1.0,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[175.0372, -41.1225], [175.0698, -41.1007], [175.08914675459422, -41.07156421641177]],
            },
        }
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])
        assert f1['features'][0] == f0

    def test_get_fault_traces_color_scale_style(self, client, archive_fixture):

        executed = client.execute(
            QUERY.replace(
                "# GEOJSON",
                "fault_traces(style: {stroke_color: \"purple\"}, color_scale: {name:\"inferno\"})",
            ),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f0 = {
            "id": "5.0",
            "type": "Feature",
            "properties": {
                "Magnitude.count": 40,
                "Magnitude.max": 8.225152015686035,
                "Magnitude.mean": 7.9513068199157715,
                "Magnitude.min": 7.600510597229004,
                "rate_weighted_mean.sum": 0.0001145526985055767,
                "FaultID": 5,
                "FaultName": "Akatarawa, Subsection 0",
                "DipDeg": 75.0,
                "Rake": 160.0,
                "LowDepth": 20.0,
                "UpDepth": 0.0,
                "DipDir": 299.6,
                "AseismicSlipFactor": 0.0,
                "CouplingCoeff": 1.0,
                "ParentID": 2,
                "ParentName": "Akatarawa",
                "stroke": "#fcffa4",
                "stroke-width": 1,
                "stroke-opacity": 1.0,
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[175.0372, -41.1225], [175.0698, -41.1007], [175.08914675459422, -41.07156421641177]],
            },
        }
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])
        assert f1['features'][0] == f0
