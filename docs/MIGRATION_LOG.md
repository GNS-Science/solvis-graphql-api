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
- [ ] Dump legacy Graphene SDL → `schema.legacy.graphql` (guard stdout→stderr — Model T1; `solvis`/`pyvista` print warnings)
- [ ] Vendor a client-query corpus (seed from `ab_test` checks: about, locations_by_id, location_list, parent_fault_names, radii_set, color_scale, filter_ruptures, filter_rupture_sections, composite_rupture_detail)
- [ ] Inventory `serverless.yml` (stages, ECR, IAM, warmup) + secrets (`TEST` env + repo keys)

### Phase 1 — Bootstrap (poetry→uv, FastAPI/Mangum, container)
- [ ] `poetry2uv` (dockerbash skill): drop poetry, generate `uv.lock`, ruff config, README/docs
- [ ] Add `strawberry-graphql`/`fastapi`/`mangum`/`pydantic`; keep legacy graphene/flask alongside until cutover
- [ ] New `app.py` (FastAPI + `GraphQLRouter` + Mangum); `StrawberryConfig(auto_camel_case=False)`
- [ ] Replace `handler.py` with Mangum; update `Dockerfile` CMD + serverless `image.command`; drop `serverless-wsgi` plugin + `custom.wsgi`
- [ ] `.yarnrc.yml`: add age gate + preapproved scopes; pin `packageManager`
- [ ] Verify container boots locally (`docker build` + invoke `{ __typename }`)

### Phase 2 — Data layer + schema migration
- [ ] `BinaryLargeObjectModel` (PynamoDB) → pydantic + boto3 CRUD; **preserve `BinaryLargeObject` wrapper API**; keep `migrate()`/`drop_tables()`
- [ ] Port ~25 graphene types across the 8 modules to Strawberry at SDL + runtime parity (relay node parity, nullability, `UNSET` args)
- [ ] Keep `cli` / `cli_ab_test` imports working
- [ ] SDL parity gate green

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

<!-- Append new dated entries above this line as the migration proceeds. -->
