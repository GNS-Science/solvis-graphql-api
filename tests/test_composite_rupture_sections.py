import json

import pytest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY = """
query {
  filter_rupture_sections(
    filter:{
      model_id: "NSHM_v1.0.4"
      location_ids: ["AKL"]
      fault_system: "CRU",
      radius_km: 100
      minimum_rate: 1.0e-19
      minimum_mag: 6.2
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

        # f0 = {"id": "3.0", "type": "Feature", "properties": {
        #     "Magnitude.count": 1, "Magnitude.max": 7.285887718200684, "Magnitude.mean": 7.285887718200684,
        #     "Magnitude.min": 7.285887718200684, "rate_weighted_mean.sum": 3.237532655475661e-05,
        #     "FaultID": 3, "FaultName": "Aka Aka, Subsection 0", "DipDeg": 65.0, "Rake": -90.0, "LowDepth": 18.56, "UpDepth": 0.0, "DipDir": 160.7,
        #     "AseismicSlipFactor": 0.0, "CouplingCoeff": 1.0, "ParentID": 1, "ParentName": "Aka Aka", "fill": "silver", "fill-opacity": 0.2, "stroke": "silver", "stroke-width": 1, "stroke-opacity": 1.0},
        #     "geometry": {"type": "Polygon", "coordinates": [[
        #     [174.8284, -37.2605], [174.8494, -37.2555], [174.8688, -37.2523],
        #     [174.8748529786847, -37.25034774563085], [174.90720244482776, -37.32380242434063],
        #     [174.90115030659854, -37.3257546783986], [174.88175168439054, -37.328954677888504], [174.8607538376275, -37.333954677091405],
        #     [174.8284, -37.2605]]]
        #     }
        # },
        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])
        assert f1['features'][0]['properties']['fill'] == 'silver'
        assert f1['features'][0]['properties']['fill-opacity'] == 0.2
        assert f1['features'][0]['properties']['stroke'] == 'silver'

    def test_get_fault_surfaces_scaled_styled(self, client, archive_fixture_tiny):
        executed = client.execute(
            QUERY.replace(
                "# GEOJSON", "fault_surfaces( style: { fill_opacity: 0.5 } color_scale: { name:\"inferno\" })"
            )
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_surfaces'] is not None

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_surfaces'])

        assert f1['features'][0]['properties']['fill'] == '#bf3952'
        assert f1['features'][0]['properties']['fill-opacity'] == 0.5
        assert f1['features'][0]['properties']['stroke'] == '#bf3952'

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
        assert (
            pytest.approx(executed['data']['filter_rupture_sections']['mfd_histogram'][0]['cumulative_rate'])
            == 3.23753265e-05
        )

    def test_get_fault_traces_no_style(self, client, archive_fixture_tiny):

        executed = client.execute(
            QUERY.replace("# GEOJSON", "fault_traces"),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])

        assert f1['features'][0]['properties'].get('fill') is None
        assert f1['features'][0]['properties'].get('fill-opacity') is None
        assert f1['features'][0]['properties'].get('stroke') is None

    def test_get_fault_traces_line_style(self, client, archive_fixture_tiny):

        executed = client.execute(
            QUERY.replace("# GEOJSON", "fault_traces(style: {stroke_color: \"purple\"})"),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])
        # assert f1['features'][0] == f0
        assert f1['features'][0]['properties']['stroke'] == 'purple'
        assert f1['features'][0]['properties']['stroke-width'] == 1
        assert f1['features'][0]['properties']['stroke-opacity'] == 1.0

    def test_get_fault_traces_color_scale_style(self, client, archive_fixture_tiny):

        executed = client.execute(
            QUERY.replace(
                "# GEOJSON",
                "fault_traces(style: {stroke_color: \"purple\"}, color_scale: {name:\"inferno\"})",
            ),
        )
        print(executed)

        assert 'filter_rupture_sections' in executed['data']
        assert executed['data']['filter_rupture_sections']['fault_traces'] is not None

        f1 = json.loads(executed['data']['filter_rupture_sections']['fault_traces'])
        assert f1['features'][0]['properties']['stroke'] == '#bf3952'
        assert f1['features'][0]['properties']['stroke-width'] == 1
        assert f1['features'][0]['properties']['stroke-opacity'] == 1.0
