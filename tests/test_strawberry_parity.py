"""Strawberry schema snapshot guard.

Originally an in-process *differential* test (ran each query through both the legacy Graphene
schema and the Strawberry schema, asserting identical ``data``). That differential proved the
migration byte-for-byte; with Graphene removed it is preserved here as a **snapshot** guard —
the same queries run through the Strawberry schema and their ``data`` is asserted against golden
JSON captured from the proven-identical schema. Regenerate snapshots with ``SNAPSHOT_UPDATE=1``.

Broad behavioural coverage of the migrated resolvers lives in the (formerly Graphene-Client)
``test_*`` suites, which now run against the Strawberry schema via ``tests._strawberry_client``.
"""

import json
import os
from pathlib import Path

import graphql_relay

from solvis_graphql_api.schema import schema as strawberry_schema

_SNAP_DIR = Path(__file__).parent / "__snapshots__" / "strawberry_parity"


def _run(query: str, **variables):
    result = strawberry_schema.execute_sync(query, variable_values=variables or None)
    assert not result.errors, f"strawberry errors: {result.errors}"
    return result.data


def _assert_snapshot(name: str, query: str, **variables):
    """Byte-exact golden-file guard. Use ONLY for queries whose output is deterministic across
    platforms — NOT for shapely-geometry / matplotlib-hex payloads, whose raw float digits
    differ macOS-vs-ubuntu (those use structural assertions below; cli_ab_test is the
    authoritative same-data geojson parity gate)."""
    data = _run(query, **variables)
    snap_path = _SNAP_DIR / f"{name}.json"
    if os.environ.get("SNAPSHOT_UPDATE"):
        snap_path.parent.mkdir(parents=True, exist_ok=True)
        snap_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    assert snap_path.exists(), f"missing snapshot {snap_path} — run with SNAPSHOT_UPDATE=1"
    expected = json.loads(snap_path.read_text())
    assert data == expected, f"snapshot mismatch for {name}:\nexpected={expected}\nactual={data}"


# --- light queries (no composite-solution archive needed) ---


def test_about_parity():
    _assert_snapshot("about", "{ about }")


def test_locations_parity():
    _assert_snapshot("locations", "{ get_locations { location_id name latitude longitude } }")


def test_location_list_parity():
    _assert_snapshot(
        "location_list",
        '{ get_location_list(list_id: "NZ2") { list_id location_ids locations { location_id } } }',
    )


def test_radii_parity():
    _assert_snapshot("radii_sets", "{ get_radii_sets { radii_set_id radii } }")
    _assert_snapshot("radii_set", "{ get_radii_set(radii_set_id: 6) { radii_set_id radii } }")


def test_color_scale_parity():
    _assert_snapshot(
        "color_scale",
        '{ color_scale(name: "inferno" min_value: 5 max_value: 10 normalization: LIN)'
        " { name min_value max_value normalisation color_map { levels hexrgbs } } }",
    )


# --- archive-dependent queries (Phase 3 resolver implementations) ---


def test_locations_by_id_parity():
    # LocationDetail Node (global-id `id`) + radius_geojson (shapely). The geojson coords are
    # raw floats (platform-fragile), so assert structurally — incl. the bug-prone global-id encoding.
    data = _run(
        '{ locations_by_id(location_ids: ["WLG", "ZQN"]) { total_count edges { node {'
        " id location_id name latitude longitude radius_geojson(radius_km: 50) } } } }"
    )
    conn = data["locations_by_id"]
    assert conn["total_count"] == 2
    nodes = [e["node"] for e in conn["edges"]]
    assert [n["location_id"] for n in nodes] == ["WLG", "ZQN"]
    for n in nodes:
        # global id must decode to ("LocationDetail", <location_id>) — graphene's encoding
        assert graphql_relay.from_global_id(n["id"]) == ("LocationDetail", n["location_id"])
        assert json.loads(n["radius_geojson"])["features"]  # non-empty geojson buffer


def test_parent_fault_names_parity(archive_fixture_tiny):
    _assert_snapshot(
        "parent_fault_names",
        '{ get_parent_fault_names(model_id: "NSHM_v1.0.4" fault_system: "CRU") }',
    )


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
    _assert_snapshot(
        "filter_ruptures",
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
    # aggregates + mfd + styled fault_surfaces geojson; geojson coords are platform-fragile floats,
    # so assert structurally (cli_ab_test byte-compares the live geojson against prod).
    sec = _run(_SECTIONS)["filter_rupture_sections"]
    assert sec["model_id"] == "NSHM_v1.0.4"
    assert sec["section_count"] > 0
    assert sec["max_magnitude"] >= sec["min_magnitude"] > 0
    assert sec["max_participation_rate"] >= sec["min_participation_rate"] > 0
    assert sec["mfd_histogram"] and all(
        {"bin_center", "rate", "cumulative_rate"} <= row.keys() for row in sec["mfd_histogram"]
    )
    surfaces = json.loads(sec["fault_surfaces"])
    assert surfaces["type"] == "FeatureCollection"
    assert len(surfaces["features"]) == sec["section_count"]
    # styling was applied to every feature
    assert all(f["properties"].get("fill") == "silver" for f in surfaces["features"])


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
    # colour paths the plain sections query skips: section-level color_scale participation-rate
    # fallback, fault_surfaces + fault_traces with a color_scale (get_colour_values). Colour hexes
    # and geojson coords are platform-fragile, so assert structurally.
    sec = _run(_SECTIONS_COLOUR)["filter_rupture_sections"]
    cs = sec["color_scale"]
    assert cs["name"] == "inferno"
    assert cs["normalisation"] == "LOG"  # the participation-rate fallback defaults to log
    levels, hexrgbs = cs["color_map"]["levels"], cs["color_map"]["hexrgbs"]
    assert len(levels) == len(hexrgbs) >= 4
    assert all(isinstance(h, str) and h.startswith("#") for h in hexrgbs)
    for key in ("fault_surfaces", "fault_traces"):
        gj = json.loads(sec[key])
        assert gj["type"] == "FeatureCollection" and gj["features"]
        # colour-mapped stroke applied per feature (a matplotlib hex, or "x000000" for None)
        assert all(f["properties"].get("stroke") for f in gj["features"])


def test_node_parity():
    # legacy defines no get_node, so node(id) resolves to null
    _assert_snapshot("node", '{ node(id: "Q29tcG9zaXRlUnVwdHVyZURldGFpbDpDUlU6NjYx") { id } }')


def test_composite_rupture_detail_parity(archive_fixture_tiny):
    # PUY:3 is a valid rupture in the tiny archive (rupture_detail resolves the rate/geometry cols)
    _assert_snapshot(
        "composite_rupture_detail",
        '{ composite_rupture_detail(filter: {model_id: "NSHM_v1.0.4" fault_system: "PUY" rupture_index: 3})'
        " { id model_id fault_system rupture_index magnitude area length rake_mean"
        " rate_weighted_mean rate_max rate_min rate_count } }",
    )
