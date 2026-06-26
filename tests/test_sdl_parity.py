"""Run the SDL parity gate as a real test.

``tools/schema_parity.py`` asserts the Strawberry schema is byte-identical (order-insensitive)
to the frozen ``schema.legacy.graphql`` baseline. It was a standalone script; running it here
makes it a permanent CI gate (and covers the tool).
"""

from solvis_graphql_api.tools import schema_parity


def test_sdl_parity_matches_legacy_baseline():
    # the migrated Strawberry SDL must still equal the frozen graphene baseline
    assert schema_parity.diff() == ""
    assert schema_parity.main() == 0


def test_sdl_parity_reports_drift(tmp_path, monkeypatch):
    # point the baseline at a different (valid) SDL → the gate must flag the drift
    bad_baseline = tmp_path / "baseline.graphql"
    bad_baseline.write_text("type Query { somethingCompletelyDifferent: String }")
    monkeypatch.setattr(schema_parity, "BASELINE", bad_baseline)
    assert schema_parity.diff()  # non-empty unified diff
    assert schema_parity.main() == 1
