# Client query corpus

Vendored real queries, committed as a controlled snapshot (runbook Phase 0). The
Strawberry migration must keep every one of these valid + behaviourally equivalent.

`test_corpus_replay.py` **validates** each `.graphql` against the live schema (no data
fixtures needed). Re-pointing it at the new Strawberry schema later catches any
field/type/argument drift the SDL parity gate might miss.

## Sources

- **Test suite** — real queries lifted from `tests/test_*` (the A/B harness in
  `solvis_graphql_api/ab_test/` can't be vendored as text; it builds operations via `sgqlc`):
  `about`, `get_locations`, `get_location`, `get_location_lists`, `get_location_list`,
  `get_radii_sets`, `get_radii_set`, `get_parent_fault_names`, `color_scale`,
  `filter_ruptures`, `filter_rupture_sections`.
- **kororaa UI** (`UI/kororaa`, files prefixed `kororaa__`) — real generated frontend
  queries (Relay), the highest-value source. Kororaa hits a **stitched gateway**, so the
  raw queries use `SOLVIS_`-prefixed root fields and root type `Query`; they're transformed
  to solvis-native here (`SOLVIS_<field>` → `<field>`, `on Query` → `on QueryRoot`). Only
  **pure-solvis** queries are vendored — `RuptureAnimationPageQuery`,
  `RuptureAnimationPagePaginationQuery`, `ComboInfoPanelComponentQuery`. These add coverage
  the tests lack: `locations_by_id` + `radius_geojson(style:)`, and the rich rupture node
  selections (`fault_surfaces`, `magnitude`, `rate_weighted_mean`, `area`, `length`).
  - **Not vendored:** the `ComboRuptureMap*` queries are **multi-API** — they also fetch
    `KORORAA_textual_content` (CMS) fields, so they aren't valid standalone solvis queries.
  - **⚠️ Check kororaa is current before harvesting.** A stale checkout showed long-removed
    `inversion_solution` / `analyse_solution` usage (now retired). `git -C UI/kororaa pull`
    first.

Refresh = an explicit PR. One query per file; filename = the source op / root field.
