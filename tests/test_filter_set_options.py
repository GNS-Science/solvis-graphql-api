import pytest
from graphene.test import Client

from solvis_graphql_api.schema import schema_root

QUERY = """
query {
  filter_rupture_sections(
      filter:{
      model_id: "NSHM_v1.0.4",
      corupture_fault_names: [],
      location_ids: [],
      fault_system: "CRU",
      radius_km: 100
      ### filter_set_options: ###
    }
  )
  {
        model_id
        section_count
        rupture_count
        max_magnitude
        min_magnitude
  }
}
"""


@pytest.fixture(scope='class')
def client():
    return Client(schema_root)


@pytest.fixture(autouse=True)
def configure_archive(archive_fixture_tiny):
    pass


class TestFaultSurfaceFilterSetOptions:
    def test_get_fault_default_union(self, client):
        q = QUERY.replace(
            "corupture_fault_names: []",
            "corupture_fault_names: [\"Pokeno\", \"Aka Aka\", \"Mangatangi\"]",
        )
        print(q)
        executed = client.execute(q)
        print(executed)
        assert executed['data']['filter_rupture_sections']['section_count'] == 8

    def test_get_fault_union(self, client):
        q = QUERY.replace(
            "corupture_fault_names: []",
            "corupture_fault_names: [\"Pokeno\", \"Aka Aka\", \"Mangatangi\"]",
        )
        q = q.replace(
            "### filter_set_options: ###",
            '''filter_set_options: {
                multiple_locations:INTERSECTION
                multiple_faults: UNION
                locations_and_faults: INTERSECTION
            }''',
        )
        print(q)
        executed = client.execute(q)
        print(executed)
        assert executed['data']['filter_rupture_sections']['section_count'] == 8

    def test_get_fault_intersection(self, client):
        q = QUERY.replace(
            "corupture_fault_names: []",
            "corupture_fault_names: [\"Pokeno\", \"Aka Aka\", \"Mangatangi\"]",
        )
        q = q.replace(
            "### filter_set_options: ###",
            '''filter_set_options: {
                multiple_locations:INTERSECTION
                multiple_faults: INTERSECTION
                locations_and_faults: INTERSECTION
            }''',
        )
        print(q)
        executed = client.execute(q)
        print(executed)

        assert executed['data']['filter_rupture_sections']['section_count'] == 8

    def test_get_location_default_intersection(self, client):
        q = QUERY.replace("location_ids: []", "location_ids: [\"AKL\", \"HLZ\"]")
        print(q)
        executed = client.execute(q)
        print(executed)
        assert executed['data']['filter_rupture_sections']['section_count'] == 8

    def test_get_location_intersection(self, client):
        q = QUERY.replace("location_ids: []", "location_ids: [\"AKL\", \"HLZ\"]")
        q = q.replace(
            "### filter_set_options: ###",
            '''filter_set_options: {
                multiple_locations:INTERSECTION
                multiple_faults: INTERSECTION
                locations_and_faults: INTERSECTION
            }''',
        )

        print(q)
        executed = client.execute(q)
        print(executed)
        assert executed['data']['filter_rupture_sections']['section_count'] == 8

    def test_get_location_union(self, client):
        q = QUERY.replace("location_ids: []", "location_ids: [\"AKL\", \"HLZ\"]")
        q = q.replace(
            "### filter_set_options: ###",
            '''filter_set_options: {
                multiple_locations:UNION
                multiple_faults: INTERSECTION
                locations_and_faults: INTERSECTION
            }''',
        )

        print(q)
        executed = client.execute(q)
        print(executed)
        assert executed['data']['filter_rupture_sections']['section_count'] == 8


QUERY_B = """
query {
  filter_ruptures (
    filter:{
    model_id: "NSHM_v1.0.4"
    fault_system: "CRU"
    corupture_fault_names: []
    location_ids: []
    radius_km: 20
    ### filter_set_options: ###
    })
  {
    total_count
  }
}
"""


# @patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', True)
class TestRupturesFilterSetOptions:
    pass
    # def test_get_fault_default_union(self, client):
    #     q = QUERY_B.replace(
    #         "corupture_fault_names: []",
    #         "corupture_fault_names: [\"Pokeno\", \"Aka Aka\", \"Kerepehi Awaiti\"]",
    #     )
    #     print(q)
    #     executed = client.execute(q)
    #     print(executed)
    #     assert executed['data']['filter_ruptures']['total_count'] == 129

    # def test_get_fault_union(self, client):
    #     q = QUERY_B.replace(
    #         "corupture_fault_names: []",
    #         "corupture_fault_names: [\"Masterton\", \"Wairarapa: 2\"]",
    #     )
    #     q = q.replace(
    #         "### filter_set_options: ###",
    #         '''filter_set_options: {
    #             multiple_locations:INTERSECTION
    #             multiple_faults: UNION
    #             locations_and_faults: INTERSECTION
    #         }''',
    #     )
    #     print(q)
    #     executed = client.execute(q)
    #     print(executed)
    #     assert executed['data']['filter_ruptures']['total_count'] == 129

    # def test_get_fault_intersection(self, client):
    #     q = QUERY_B.replace(
    #         "corupture_fault_names: []",
    #         "corupture_fault_names: [\"Masterton\", \"Wairarapa: 2\"]",
    #     )
    #     q = q.replace(
    #         "### filter_set_options: ###",
    #         '''filter_set_options: {
    #             multiple_locations:INTERSECTION
    #             multiple_faults: INTERSECTION
    #             locations_and_faults: INTERSECTION
    #         }''',
    #     )
    #     print(q)
    #     executed = client.execute(q)
    #     print(executed)
    #     assert executed['data']['filter_ruptures']['total_count'] == 15
