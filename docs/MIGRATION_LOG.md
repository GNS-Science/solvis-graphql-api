# Graphene → Strawberry Migration Log — `solvis-graphql-api`

**This is the 4th and final sibling migration** (the hardest: container Lambda **+ PynamoDB ORM**), run after the toshi-api reference and the Model / Kororaa / Hazard siblings so the runbook is fully battle-tested.

**Authoritative runbook:** [`../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md`](../../nshm-toshi-api/docs/MIGRATION_RUNBOOK.md) (reference: `nshm-toshi-api`, completed 2026-06). Read it first — this log records only what is **specific to this repo** and **what actually happened**. Per the runbook's *Maintenance* rule, every surprise here must be folded back (one-line note or new trap), and this API MUST file at least one PR against it.

- **Owner:** Chris B Chamberlain (chrisbc@artisan.co.nz)
- **Migration branch:** `migrate/strawberry` (based on `deploy-test`)
- **Started:** 2026-06-24
- **Status:** Phase 0 — pre-flight inventory captured 🟡
- **Epic:** GNS-Science/nshm-toshi-api#359
- **Why last** (runbook §A4): container Lambda + **PynamoDB** ORM + `serverless-dynamodb`/`serverless-s3-local` local plugins. Biggest delta from toshi-api.

---

## Repo-specific facts (Phase 0 inventory)

Source: code exploration 2026-06-24 on `deploy-test` @ `93f6f62`. Version **0.9.2**.

### Current stack
- **Python** 3.12, **poetry** (`poetry.lock` present, `poetry-core` build backend — **still on poetry**, unlike Model). Node 22, **Yarn 4.10.3**.
- **GraphQL:** `graphene>=3.3` + `graphql-server==3.0.0b7` (same pinned pre-release as Model) served via **Flask + flask-cors**.
- **Data layer:** **PynamoDB >=6.0.0** (the big delta) + boto3/S3.
- **Heavy compute deps:** `matplotlib`, `solvis>=1.2.0` (pulls geo stack), `shapely` (used directly in 4 modules), `nzshm-model`, `nzshm-common`. Container is justified.
- **Serverless:** Framework **v4** (`serverless ^4.29.0`); plugins `serverless-wsgi` + `serverless-plugin-warmup`; dev plugins `serverless-dynamodb` + `serverless-s3-local` declared in `package.json`.
- **Deploy shape:** **container Lambda** via ECR. `provider.ecr.images.app_image_0` builds `Dockerfile` (`public.ecr.aws/lambda/python:3.12`). Function `ecr-app` uses `image.command: solvis_graphql_api.handler.handler`, entrypoint `/lambda-entrypoint.sh`. **memory 2096 MB, timeout 20 s.**
- **The `handler.py` workaround** (runbook §A3/§A4): `solvis_graphql_api/handler.py` wraps `serverless_wsgi.handle_request(...app...)` because "serverless-wsgi and ecr/image don't play together in package/deploy". **Mangum replaces this file entirely.**
- **Service:** `nzshm22-solvis-graphql-api`, region `ap-southeast-2`, SF org `gnssciencenshm` / app `solvis-graphql-api`.

### App / schema layout (`solvis_graphql_api/`)
| File | Role |
|---|---|
| `solvis_graphql_api.py` | Flask app factory; module-level `app` (WSGI target) |
| `handler.py` | container Lambda entry — serverless-wsgi wrapper (**→ Mangum**) |
| `schema.py` | root `QueryRoot`; `RadiiSet`, `Location`, `LocationList`, color-scale + composite wiring |
| `location_schema.py` | location detail connection (2 types) |
| `solution_schema.py` | inversion-solution analysis (5 types) — **mostly commented out** in root schema; verify if live |
| `composite_solution/schema.py` + `composite_rupture_detail.py` (6) + `composite_solution.py` (2) + `composite_rupture_sections.py` (2) | composite rupture/solution types |
| `color_scale/color_scale.py` (3) | matplotlib-backed colour scales |
| `data_store/model.py` | **PynamoDB** `BinaryLargeObjectModel` + `BinaryLargeObject` wrapper |
| `scripts/cli.py`, `scripts/cli_ab_test.py` | console scripts (`cli`, `cli_ab_test`) — import from package |
| `ab_test/` | cross-stage A/B differential client (prod/test/dev schemas) |

~25 graphene/relay types across 8 modules. Uses `graphene.relay` Node (watch the runbook's `GlobalID` vs `id: ID!` parity gotcha — Model correction C1).

### PynamoDB surface — small and contained
- **One model:** `BinaryLargeObjectModel(Model)` — 5 attrs (`hash_key`, `range_key`, `object_id`, `object_type`, `object_meta` JSON). Table `SGI-BinaryLargeObject-{STAGE}`, PAY_PER_REQUEST.
- Wrapped by `BinaryLargeObject` (hand-written) holding the S3 blob alongside the DynamoDB item: `get`/`save`/`exists`/`create_table`/`delete_table`/`to_json`, plus `migrate()`/`drop_tables()`.
- **Conversion target:** `BinaryLargeObjectModel` → a `pydantic.BaseModel` + thin boto3 CRUD, **keeping the `BinaryLargeObject` wrapper API stable** so `cli`/resolvers don't change. This is the only PynamoDB code — far smaller than the runbook's §A4 framing implies.

### Tests
- ~19 test files + `conftest.py` + `fixtures/`. Uses **`moto`** (mock_aws) for DynamoDB/S3 — no testcontainers needed (runbook Trap #10 N/A).
- Suite mirrors the A/B checks: locations, location lists, parent faults, radii, color scale, composite solution/ruptures, pagination, sorting, node-id fix.

### Deploy / CI / secrets
- **Auth:** API-Gateway **API key** (`SOLVIS_GRAPHQL_API_TempApiKey-${stage}`), `private: true` on GET+POST. Same posture as Model — **no `LEGACY_API_KEY` chain** (runbook §4.3 N/A; preserve the API-Gateway key).
- **Secrets (⚠️ delta from runbook §4.2, same as Model):** repo-level static `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY` + `SERVERLESS_ACCESS_KEY` + a single `TEST` environment (no env secrets). **Not** the `AWS_TEST`/`AWS_PROD` + OIDC split.
- **CI:** shared `GNS-Science/nshm-github-actions` workflows. `dev.yml` → `python-run-tests.yml` (**poetry**, not the `-uv` variant Model moved to); `deploy-to-aws.yaml` uses `docker: true` (container build), `node-pkg-manager: yarn2`, smoke `query QueryRoot{about}`.
- **⚠️ Trap #14:** `dev.yml` has `pull_request: branches: [main, deploy-test]` — stacked PRs get no CI. Remove it (and cascade onto every head branch — Model nuance).
- **⚠️ `.yarnrc.yml` is minimal** (`nodeLinker: node-modules` only) — **no age gate, no preapproved packages** (runbook §4.6). Add them.
- **Stages:** local/dev/test/prod. `serverless-dynamodb` (local) + `serverless-s3-local` configured for the `local` stage.

### Assets that de-risk this migration
1. **A ready-made differential validator.** `ab_test/` + `cli_ab_test` already diff prod-vs-test across 9 query functions (`MIGRATION_v0.9.md` shows them PASS). This **is** the runbook's Phase 5 "active differential validation" tool — reuse it instead of building a `drive_live.py`.
2. **Tiny PynamoDB footprint** — one model, already wrapped.
3. **moto-based tests already exist** — no testcontainers stand-up.
4. **Already on Serverless Framework v4** → built-in uv-aware python-requirements available (runbook §4.8); but note **container Lambda installs deps via the Dockerfile `pip install -r requirements.txt`**, not the SF requirements step — confirm which path packages deps here.

---

## Deltas from the runbook (what does / doesn't apply here)

| Runbook item | Applies? | Note |
|---|---|---|
| `StrawberryConfig(auto_camel_case=False)` (Trap #2) | ✅ Yes | snake_case schema today |
| FastAPI + Mangum, drop `serverless-wsgi` / `handler.py` | ✅ Yes | container entry → Mangum; update `Dockerfile` CMD + `image.command` |
| Drop poetry → uv (§Phase 1) | ✅ **Yes** | still on poetry — use dockerbash `poetry2uv` skill; switch CI to `-uv` workflows |
| Relay `Node` `GlobalID`/`id: ID!` parity (Model C1) | ⚠️ Likely | uses `graphene.relay`; `test_..._fix_node_id` hints at id sensitivity — check parity |
| Nullability / `UNSET` arg parity (Model T2/T3) | ✅ Yes | port carefully, SDL parity gate will catch |
| **PynamoDB → boto3 + Pydantic v2** (§A4) | ✅ **Yes — the headline** | but only `BinaryLargeObjectModel`; keep `BinaryLargeObject` API |
| Layered models / `_dispatch.py` (Traps #4–6) | ❔ Verify | no obvious polymorphic `clazz_name` dispatch; relay node lookup exists |
| `ClientIDMutation` payload (Phase 2 trap) | ❔ Verify | confirm whether any mutations exist (looks query-only) |
| `LEGACY_API_KEY` chain (Trap #11) | ❌ No | API-Gateway key only; preserve it |
| testcontainers / Java (Trap #10) | ❌ No | moto already used |
| Remove `branches:` filter (Trap #14) | ✅ Yes | present in `dev.yml`; cascade onto every head branch |
| Yarn `resolutions` / local-dev plugin traps (§4.7) | ⚠️ **High** | `serverless-s3-local` (s3rver) **and** `serverless-dynamodb` both load at boot — the exact §4.7 shape |
| `.yarnrc.yml` age gate + preapproved (§4.6) | ✅ **Add** | currently missing |
| SF v4 built-in python-requirements (§4.8) | ⚠️ Verify | container installs via Dockerfile `pip`, not SF requirements — confirm |
| Container image size (§A3) | ⚠️ Watch | matplotlib + solvis + shapely; multi-stage build, aim small |
| `cli` / `cli_ab_test` import from package (§A4) | ✅ Yes | add to test matrix; keep working across any layout change |
| SDL parity + query corpus replay | ✅ Yes | seed corpus from the A/B test query set |
| 24h soak vs differential validation (Phase 5) | ✅ Differential | reuse `cli_ab_test` (prod-vs-new) |

---

## Planned phase checklist (tailored)

> Full detail in the runbook. Tick as completed; append dated notes under "Log entries".

### Phase 0 — Pre-flight 🟡
- [x] Repo inventory captured (this doc)
- [x] Dump legacy Graphene SDL → `schema.legacy.graphql` (449 lines, 29 types). Tool: `solvis_graphql_api/tools/dump_legacy_sdl.py`, stdout→stderr guard **confirmed needed** (`pyvista` warns on import)
- [x] Vendor a client-query corpus → `tests/fixtures/corpus/` (14 queries) + `test_corpus_replay.py` validation gate
  - test-sourced (11): `about`, locations, location-lists, radii, parent-faults, color-scale, filter-ruptures, filter-rupture-sections
  - kororaa-sourced (3): transformed gateway → solvis-native (real frontend traffic)
- [ ] Inventory `serverless.yml` (stages, ECR, IAM, warmup) + secrets (`TEST` env + repo keys)

### Phase 1 — Bootstrap (poetry→uv, FastAPI/Mangum, container) ✅
- [x] `poetry2uv` (external run, PR #87): poetry→uv, ruff, age gate, CI→`-uv`
- [x] Add `strawberry-graphql` 0.316 / `fastapi` 0.137 / `mangum` 0.21 / `pydantic` 2.13; legacy graphene/flask kept alongside until cutover
- [x] New `app.py` (FastAPI + `GraphQLRouter` + Mangum + CORS); `strawberry_schema.py` minimal `QueryRoot.about`, `StrawberryConfig(auto_camel_case=False)`
- [x] Container entry → Mangum: `serverless.yml` `image.command` = `solvis_graphql_api.app.handler`; dropped `serverless-wsgi` plugin + `custom.wsgi`; `Dockerfile` CMD = `app.handler` (removed bogus `/bin/bash -c` entrypoint). `handler.py` left in place (unused; deleted at cutover)
- [x] `.yarnrc.yml`: tracked + age gate + preapproved scopes (`packageManager` already pinned `yarn@4.10.3`)
- [x] Container verified locally: amd64 `docker build` OK; `app.handler` imports inside the image; `uvicorn` TestClient `{ about }` byte-matches legacy. Removed `branches:` filter (Trap #14) so the stack gets CI.

### Phase 2 — Data layer + schema migration 🟡
- [x] `BinaryLargeObjectModel` (PynamoDB) → `pydantic` + `boto3` CRUD behind the **unchanged** `BinaryLargeObject` wrapper; `migrate()`/`drop_tables()` kept; **`pynamodb` dependency removed**
- [x] Port the ~25 graphene types (8 modules) to Strawberry — **SDL byte-identical**; custom `Node` interface (`id: ID!`), nullability + `UNSET`-arg traps, partial style-arg defaults all matched
- [x] `cli` / `cli_ab_test` still import (graphene path untouched)
- [x] SDL parity gate green (`tools/schema_parity.py`); corpus replay re-pointed at the Strawberry schema
- [ ] **Runtime parity for archive-dependent fields → Phase 3** (rupture field computes, pagination, sections geojson/mfd/colour, `node()` dispatch — need the tiny-archive fixtures + test-suite conversion)

### Phase 3 — Tests
- [ ] Convert suite to drive Strawberry (keep moto); parametrize legacy+strawberry where useful
- [ ] SDL parity + corpus replay in CI; switch `dev.yml`/deploy to `-uv` workflows; remove `branches:` filter

### Phase 4 — Deploy / CI / deps
- [ ] Validate container build + dep install path (Dockerfile vs SF requirements); image-size pass (multi-stage)
- [ ] Yarn resolutions hygiene — validate `serverless-s3-local` + `serverless-dynamodb` plugin chain loads (`node -e "require('s3rver')"`, `yarn sls package --stage dummy`)
- [ ] vuln audit (pip-audit) — bumps via `pyup`
- [ ] memory watch (keep 2096 unless evidence)

### Phase 5 — Cutover
- [ ] Deploy to test stage; **`cli_ab_test` prod-vs-new** differential validation (the built-in harness)
- [ ] Pre-stage rollback PR; promote `deploy-test → main`; ~30-min prod watch
- [ ] Post-healthy cleanup: delete legacy Flask/graphene + `handler.py`; file runbook feedback PR

---

## Log entries

### 2026-06-24 — kickoff + Phase 0 inventory
- Created branch `migrate/strawberry` off `deploy-test` (@ `93f6f62`).
- Captured the inventory above. Headline findings: PynamoDB surface is a **single** wrapped model (much smaller than §A4 implies); the repo ships its **own cross-stage differential validator** (`cli_ab_test`) — reuse it for Phase 5; still on **poetry** and **missing the yarn age gate**; container entry is the serverless-wsgi `handler.py` workaround (→ Mangum); both `serverless-s3-local` + `serverless-dynamodb` load at boot (§4.7 risk).
- **Next:** Phase 0 artifacts — baseline legacy SDL (guard stdout) + vendor the A/B query set as the corpus.

### 2026-06-24 — poetry2uv merged + Phase 0 SDL baseline
- **poetry2uv landed** (external run, PR #87): poetry → uv (`uv.lock`, hatchling backend, `[dependency-groups]`), flake8/black/isort → **ruff** (`E,F,I,B,UP`; `G004` deferred), `[tool.uv]` age gate (`exclude-newer = "1 week"`, nzshm* exempt), CI switched to `python-run-tests-uv.yml`. Pulled to local; **verified green: `uv sync --frozen` ok, `ruff check` clean, 62 passed / 10 skipped.**
- Still TODO (poetry2uv didn't cover): `dev.yml` still has the `branches: [main, deploy-test]` filter (**Trap #14** — remove + cascade); ruff `select` is narrower than toshi-api's (no `UP047`/`PLC0415`/`G004`) — fine for now.
- **Phase 0 SDL baseline:** added `tools/dump_legacy_sdl.py`, committed `schema.legacy.graphql` (449 lines, 29 types). **Model T1 confirmed live** — `pyvista` prints a warning to stdout on import; the stdout→stderr guard kept the SDL clean (0 warnings leaked).
- **Next:** vendor the query corpus from the test suite's inline queries; then Phase 1 (FastAPI/Mangum scaffold + container `handler.py` → Mangum).

### 2026-06-24 — query corpus vendored (test + kororaa) + a stale-checkout lesson
- **Test-sourced corpus (11 queries)** lifted from `tests/test_*` into `tests/fixtures/corpus/`; `test_corpus_replay.py` **validates** each against `schema_root` (no data fixtures — re-points to the Strawberry schema later to catch drift). The A/B harness (`cli_ab_test`) can't be vendored as text — it builds ops via `sgqlc`.
- **kororaa UI corpus (3 queries):** kororaa is a **Relay** app hitting a **stitched gateway**, not solvis directly — its ops use `SOLVIS_`-prefixed root fields and root type `Query`. Transformed to solvis-native (`SOLVIS_<f>`→`<f>`, `on Query`→`on QueryRoot`) and validated; only the **pure-solvis** ops vendored (`RuptureAnimationPageQuery`, `…PaginationQuery`, `ComboInfoPanelComponentQuery`). The `ComboRuptureMap*` ops are multi-API (`KORORAA_textual_content` CMS fields) so not vendorable standalone. These add real coverage the tests lack: `locations_by_id` + `radius_geojson(style:)`, rich rupture node fields.
- **⚠️ Lesson — verify sibling checkouts are current.** The local `UI/kororaa` was **32 commits / ~9 months stale**; it showed a live `FaultModelPage` querying `SOLVIS_inversion_solution`/`analyse_solution` — which set off a false parity alarm (solvis has those commented out in `solution_schema.py`). After `git pull`, those views/fields are **gone**: the commented-out `solution_schema.py` is **correctly retired**; current parity target = current schema. *(Runbook feedback candidate: Phase 0 client-query survey must `git pull` each client repo first — a stale checkout invents phantom parity obligations.)*
- All green: corpus gate 15 passed; full suite **77 passed / 10 skipped**; ruff clean.
- **Next:** Phase 1 — FastAPI/Mangum scaffold + container `handler.py` → Mangum (verify via local `docker build`), `.yarnrc` age gate, drop `serverless-wsgi`.

### 2026-06-24 — Phase 1 bootstrap (FastAPI/Mangum + container swap)
- **Stack added** alongside legacy: `strawberry-graphql` 0.316, `fastapi` 0.137, `mangum` 0.21, `pydantic` 2.13 (`uv lock`/`sync` clean). `app.py` = FastAPI + `GraphQLRouter` + Mangum + CORS; `strawberry_schema.py` = minimal `QueryRoot.about` at SDL parity (`auto_camel_case=False`, `about: String` nullable, description matches).
  - **Root type named `QueryRoot`** (not Strawberry's default `Query`) — legacy is `query: QueryRoot` and the vendored kororaa corpus fragments are `on QueryRoot` (Model G4/relay-parity territory).
  - **`<pkg>/schema.py` collision** (Model G4): legacy Graphene `schema_root` occupies `solvis_graphql_api.schema`, so the new schema is `strawberry_schema.py`; rename at cutover.
- **Container entry → Mangum.** `serverless.yml` `functions.ecr-app.image.command` = `solvis_graphql_api.app.handler`; dropped `serverless-wsgi` plugin + `custom.wsgi`; `Dockerfile` CMD = `app.handler` (and removed the bogus `ENTRYPOINT ["/bin/bash","-c"]` — the base image's `/lambda-entrypoint.sh` RIC stands). `handler.py` (the serverless-wsgi container workaround) is now unused — deleted at cutover.
- **Verified the container for real** (your steer): `requirements.txt` regenerated from `uv.lock` (`uv export --no-dev`, gitignored); **amd64 `docker build` succeeded**; `docker run … python -c "import solvis_graphql_api.app"` → Mangum handler + FastAPI app import clean inside the image. Local `uvicorn`/TestClient: `{ about }` byte-matches legacy. Full legacy suite still **77 passed / 10 skipped**; ruff clean.
- **CI:** removed the `dev.yml` `branches:` filter so stacked PRs get CI (Trap #14); added `.yarnrc.yml` age gate (§4.6).
- **Next:** Phase 2 — the headline work: `BinaryLargeObjectModel` (PynamoDB) → pydantic + boto3 behind the `BinaryLargeObject` wrapper, then port the ~25 graphene types to Strawberry at SDL parity.

### 2026-06-24 — Phase 2a: PynamoDB → pydantic + boto3 (data layer)
- Converted the **only** PynamoDB usage — `BinaryLargeObjectModel(Model)` → a `pydantic.BaseModel` (`BinaryLargeObjectItem`) + thin `boto3` DynamoDB CRUD (`describe`/`create`/`delete`/`put`/`get_item`). The public **`BinaryLargeObject` wrapper API is unchanged** (`get`/`save`/`exists`/`create_table`/`delete_table`/`to_json`/`set_s3_client_args`/`object_*` props), so `cli` and `composite_solution.cached` are untouched. `tables`/`migrate()`/`drop_tables()` preserved (`create_table(wait=True)` → boto3 `table_exists` waiter).
- **Faithful to `JSONAttribute`:** `object_meta` is stored as a JSON string (not a native DynamoDB Map), so values round-trip as ints — avoids the `Decimal` skew a native Map would introduce, and keeps `to_json()` byte-equal.
- **Did not "improve" the wrapper** — kept the TODO-flagged `get()` shape as-is (no contract change mid-migration).
- **`pynamodb` dependency dropped** from `pyproject.toml`; `uv lock`/`sync` (164 pkgs); no lingering imports.
- Verified: the moto contract `data_store/test/test_model.py` **4/4**; full suite **77 passed / 10 skipped**; ruff + mypy clean. Container entry/Dockerfile untouched, so the Phase 1 build proof still holds.
- **Next:** Phase 2b — port the ~25 graphene types (8 modules) to Strawberry at SDL parity; re-point the parity gate + corpus replay at the new schema.

### 2026-06-24 — Phase 2b: Graphene → Strawberry schema port (SDL byte-identical)
- **`strawberry_schema.py`** now defines the full schema — 29 types — and **`tools/schema_parity.py`** confirms it is **byte-identical** to `schema.legacy.graphql` (order-insensitive normalise + diff). `app.py` already serves it.
- **Parity traps cleared** (runbook + Model feedback in action):
  - root type **`QueryRoot`** (not Strawberry's `Query`); **custom `Node` interface** `id: ID!` (Model C1 — NOT `strawberry.relay`/`GlobalID`); `auto_camel_case=False` with relay `PageInfo` fields kept camelCase via `name=`.
  - **nullability**: every nullable-with-default input field needs `X | None` or Strawberry emits `!` (a broad version of Model T2).
  - **`UNSET` vs `null`** (Model T3): optional args with no SDL default use `strawberry.UNSET`; only `ColorScaleArgsInput.normalisation` keeps `= null` (`= None`).
  - **partial style-arg default**: legacy `style = {stroke_color, stroke_width, stroke_opacity}` (3 keys, no fill) reproduced by a default input instance with `fill_*` set to `strawberry.UNSET` (so they neither render nor apply).
  - `<pkg>/schema.py` name clash (Model G4) → file is `strawberry_schema.py`, rename at cutover.
- **Compute reused, not rewritten**: resolvers call the existing Graphene-free helpers (`cached.*`, `color_scale.get_colour_scale`, `apply_geojson_style`, `get_location_detail_list`). Light query-root resolvers **verified executing** vs legacy values (about, get_locations, radii as ints, colour-scale matplotlib output, location lists).
- **mypy**: added the `strawberry.ext.mypy_plugin`; new code is clean (TYPE_CHECKING aliases for the `JSONString` scalar + `SetOperationEnum`; 2 targeted `[misc]` ignores for the `id` resolver overriding the interface field — Model also accepted a scalar ignore). The 29 remaining errors are **pre-existing** in the legacy graphene modules (`follow_untyped_imports` config, deleted at cutover), not from this change, and mypy isn't the PR test gate.
- Corpus replay (14 queries) now validates against the Strawberry schema: **15 passed**. Full suite **77 passed / 10 skipped**; ruff clean.
- **Deferred** (benign): `strawberry.scalar()` class-form DeprecationWarning on `JSONString` (same one the Model pilot deferred; changing it risks the scalar's SDL name/description).
- **Next:** Phase 3 — convert the test suite to drive the Strawberry schema (moto + tiny-archive fixtures), implement the archive-dependent resolvers to runtime parity, wire CI.

<!-- Append new dated entries above this line as the migration proceeds. -->
