"""Phase 3 — in-process differential parity.

Runs the *same* query against the legacy Graphene schema and the new Strawberry schema and
asserts byte-identical ``data``. This proves runtime parity without hard-coding expected
values (the Phase 5 ``cli_ab_test`` does the same against live prod/test stages).
"""

from graphene.test import Client

from solvis_graphql_api.schema import schema_root
from solvis_graphql_api.strawberry_schema import schema as strawberry_schema


def _assert_parity(query: str, **variables):
    legacy = Client(schema_root).execute(query, variable_values=variables or None)
    straw = strawberry_schema.execute_sync(query, variable_values=variables or None)
    assert not straw.errors, f"strawberry errors: {straw.errors}"
    assert not legacy.get("errors"), f"legacy errors: {legacy.get('errors')}"
    assert straw.data == legacy["data"], f"\nlegacy={legacy['data']}\nstrawberry={straw.data}"


# --- light queries (no composite-solution archive needed) ---


def test_about_parity():
    _assert_parity("{ about }")


def test_locations_parity():
    _assert_parity("{ get_locations { location_id name latitude longitude } }")


def test_location_list_parity():
    _assert_parity('{ get_location_list(list_id: "NZ2") { list_id location_ids locations { location_id } } }')


def test_radii_parity():
    _assert_parity("{ get_radii_sets { radii_set_id radii } }")
    _assert_parity("{ get_radii_set(radii_set_id: 6) { radii_set_id radii } }")


def test_color_scale_parity():
    _assert_parity(
        '{ color_scale(name: "inferno" min_value: 5 max_value: 10 normalization: LIN)'
        " { name min_value max_value normalisation color_map { levels hexrgbs } } }"
    )


# --- archive-dependent queries (Phase 3 resolver implementations) ---


def test_locations_by_id_parity():
    # exercises the LocationDetail Node (global-id `id`) + radius_geojson (shapely, no archive)
    _assert_parity(
        '{ locations_by_id(location_ids: ["WLG", "ZQN"]) { total_count edges { node {'
        " id location_id name latitude longitude radius_geojson(radius_km: 50) } } } }"
    )


def test_parent_fault_names_parity(archive_fixture_tiny):
    _assert_parity('{ get_parent_fault_names(model_id: "NSHM_v1.0.4" fault_system: "CRU") }')


_FILTER_RUPTURES = """
query ($model_id: String! $location_ids: [String]! $fault_system: String! $radius_km: Int
       $minimum_mag: Float $minimum_rate: Float) {
  filter_ruptures(first: 3 filter: {
      model_id: $model_id fault_system: $fault_system location_ids: $location_ids
      radius_km: $radius_km minimum_mag: $minimum_mag minimum_rate: $minimum_rate}) {
    total_count
    pageInfo { hasNextPage endCursor }
    edges { cursor node { __typename id model_id rupture_index magnitude } }
  }
}
"""


def test_filter_ruptures_parity(archive_fixture):
    _assert_parity(
        _FILTER_RUPTURES,
        model_id="NSHM_v1.0.0",
        fault_system="HIK",
        location_ids=["WLG"],
        radius_km=5,
        minimum_mag=8.3,
        minimum_rate=1.0e-6,
    )


_SECTIONS = """
{ filter_rupture_sections(filter: {
    model_id: "NSHM_v1.0.4" location_ids: ["AKL"] fault_system: "CRU"
    radius_km: 100 minimum_rate: 1.0e-19 minimum_mag: 6.2 }) {
  model_id section_count max_magnitude min_magnitude max_participation_rate min_participation_rate
  mfd_histogram { bin_center rate cumulative_rate }
  fault_surfaces(style: { stroke_color: "silver" fill_color: "silver" fill_opacity: 0.2 })
} }
"""


def test_filter_rupture_sections_parity(archive_fixture_tiny):
    _assert_parity(_SECTIONS)


_SECTIONS_COLOUR = """
{ filter_rupture_sections(filter: {
    model_id: "NSHM_v1.0.4" location_ids: ["AKL"] fault_system: "CRU"
    radius_km: 100 minimum_rate: 1.0e-19 minimum_mag: 6.2 }) {
  color_scale(name: "inferno") { name min_value max_value normalisation color_map { levels hexrgbs } }
  fault_surfaces(color_scale: { name: "inferno" }
    style: { stroke_color: "silver" fill_color: "silver" fill_opacity: 0.2 })
  fault_traces(color_scale: { name: "inferno" } style: { stroke_color: "black" })
} }
"""


def test_filter_rupture_sections_colour_parity(archive_fixture_tiny):
    # exercises the colour paths the plain sections query skips: the section-level color_scale
    # participation-rate fallback, fault_surfaces + fault_traces with a color_scale (get_colour_values)
    _assert_parity(_SECTIONS_COLOUR)


def test_node_parity():
    # legacy defines no get_node, so node(id) resolves to null on both schemas
    _assert_parity('{ node(id: "Q29tcG9zaXRlUnVwdHVyZURldGFpbDpDUlU6NjYx") { id } }')


def test_composite_rupture_detail_parity(archive_fixture_tiny):
    # PUY:3 is a valid rupture in the tiny archive (rupture_detail resolves the rate/geometry cols)
    _assert_parity(
        '{ composite_rupture_detail(filter: {model_id: "NSHM_v1.0.4" fault_system: "PUY" rupture_index: 3})'
        " { id model_id fault_system rupture_index magnitude area length rake_mean"
        " rate_weighted_mean rate_max rate_min rate_count } }"
    )
