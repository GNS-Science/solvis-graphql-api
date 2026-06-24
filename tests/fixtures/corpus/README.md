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
- **kororaa UI** (`UI/kororaa`) — real generated frontend queries _(to be added; the
  highest-value source — actual production traffic)._

Refresh = an explicit PR. One query per file; filename = the root field exercised.
