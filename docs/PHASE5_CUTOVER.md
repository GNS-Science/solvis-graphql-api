# Phase 5 — Cutover plan (`solvis-graphql-api` Graphene → Strawberry)

**In-place replacement.** Same CloudFormation stack, ECR function (`ecr-app`), routes
(`/{any+}` GET/POST `private: true`, OPTIONS), API-Gateway key, and URL. The container
image changes (Mangum entry + Strawberry schema); the deployed surface does not. Rollback =
redeploy the previous image (revert the merge).

Owner: @chrisbc · Epic: GNS-Science/nshm-toshi-api#359 · Tracking: #86 · Log: `MIGRATION_LOG.md`

> ⚠️ **Requires AWS credentials + an explicit prod go-ahead.** Everything below the "Deploy"
> heading is held until then. The engineering (Phases 0–4) is complete and merged-ready.

## §1 Validation strategy — reuse the built-in differential harness

Solvis already ships a cross-stage differential tester: **`cli_ab_test`**
(`solvis_graphql_api/scripts/cli_ab_test.py` + `ab_test/`). Its checks cover the exact
migrated surface: `about`, `color_scale`, `get_parent_fault_names`, `get_location_list`,
`get_radii_set`, `filter_ruptures`, `filter_rupture_sections`, `locations_by_id`,
`composite_rupture_detail`. **Reuse it — don't build a `drive_live.py`.**

In-process parity is already proven by `tests/test_strawberry_parity.py` (11 differential
checks, byte-identical `data`). `cli_ab_test` extends that proof to the live deployed stages.

## §2 Deploy to test

1. Capture a baseline: prod CloudWatch p50/p95 duration, error rate, `Max Memory Used` (confirm 2096 MB headroom). Screenshot it.
2. Merge the stack to `deploy-test` (see §5 on whether to land the cleanup before or after) → the `deploy-to-aws-uv.yml` workflow builds the image (uv → `requirements.txt` → Docker/ECR) and deploys. Deploy smoke `query QueryRoot{about}` must pass.
3. **`cli_ab_test WORK/ab.toml -A prod -B test -v`** — prod (legacy) vs test (new). **Every check must PASS.** (Keys/endpoints supplied out-of-band, never committed.)

## §3 Rollback

- **Pre-stage the revert PR** as a draft against `main`: title `revert: <promote-title>`, body
  containing `git revert <merge-sha>`, plus the trigger: *publish if 5xx rate > X% sustained
  > Y min, or `cli_ab_test` reports any mismatch.*
- Rollback = merge the revert → the workflow redeploys the previous image. Re-run
  `cli_ab_test` (or the deploy smoke) to confirm legacy behaviour restored.
- **Stateful note:** the migration adds **no new write shapes** — the `BinaryLargeObject`
  store is unchanged (pydantic+boto3 writes the same item/JSON). Rollback is image-only; no
  data migration to reverse.

## §4 Promote & watch

1. Promote `deploy-test → main` via PR (`release: promote solvis strawberry to prod`) — only after §2 passes.
2. `cli_ab_test ... -A prod -B test` once more post-promote isn't meaningful (both become new);
   instead run the deploy smoke + watch prod ~30 min: `aws logs tail /aws/lambda/<fn> --follow`
   + CloudWatch error rate / p95 vs the §2 baseline.
3. Comms at: deploy start, test validated, promote PR open, prod deploy, "healthy" (30 min), or rollback.

## §5 Post-healthy legacy cleanup (after prod is confirmed healthy)

Behaviour-neutral; do as its own validated PR. **Must come AFTER cutover** — the differential
tests + `CompositeRuptureSections` delegation still import the graphene schema, so it can't be
deleted until the new path is proven live.

- **Delete:** `solvis_graphql_api/schema.py` (graphene root) + `solvis_graphql_api.py` (Flask
  app) + `handler.py` (serverless-wsgi workaround) + the graphene type modules' Graphene
  classes (the **compute** helpers in `cached`, `color_scale`, `geojson_style`,
  `composite_solution/*` stay — Strawberry resolvers reuse them).
- **Rewire** `CompositeRuptureSections` off the graphene-delegation (`_GrapheneSections`) onto
  the retained compute helpers directly (or keep the helpers and drop only the graphene types).
- **Rename** `strawberry_schema.py` → `schema.py`; fix imports (`app.py`, tools, tests).
- **Drop deps:** `graphene`, `graphql-server`, `flask`, `flask-cors`, `serverless-wsgi`
  (python). **Keep** `graphql-relay` (global-id encoding) + the compute libs.
- **Tests:** `test_strawberry_parity.py` loses its legacy comparator → convert to assert against
  recorded expected values (or fold into the `cli_ab_test` corpus); `test_corpus_replay.py`
  already targets the Strawberry schema.
- Re-run `cli_ab_test` (prod vs the cleaned test stage) before promoting the cleanup.
