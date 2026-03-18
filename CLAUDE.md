# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A GraphQL API for querying and analyzing NZSHM (New Zealand Seismic Hazard Model) composite inversion solutions. Built with Flask + Graphene, deployed as an AWS Lambda function via the Serverless Framework using Docker/ECR containers.

## Common Commands

### Setup
```bash
corepack enable && yarn set version berry
yarn install
poetry install
yarn sls dynamodb install   # requires Java
```

### Running Locally
```bash
# Start local DynamoDB and S3 (separate terminals or backgrounded)
npx serverless dynamodb start --stage local
npx serverless s3 start

# Start the API server
SLS_OFFLINE=1 poetry run yarn sls wsgi serve
```

### Testing
```bash
poetry run pytest                                          # all tests
poetry run pytest tests/test_file.py                       # single file
poetry run pytest tests/test_file.py::test_function_name   # single test
poetry run pytest -m "not slow"                            # skip slow tests
poetry run tox                                             # full test suite via tox
```

### Linting & Formatting
```bash
poetry run tox -e lint      # flake8 + mypy
poetry run tox -e format    # isort + black
poetry run tox -e audit     # pip-audit security scan
```

### Deploy
```bash
poetry export --without-hashes --format=requirements.txt > requirements.txt
BUILDX_NO_DEFAULT_ATTESTATIONS=1 yarn sls deploy --stage dev --region ap-southeast-2
```

## Architecture

### Request Flow
```
API Gateway (API key auth) → Lambda handler (handler.py)
  → Flask app (solvis_graphql_api.py) → GraphQL schema (schema.py, QueryRoot)
    → Resolvers → cached.py (LRU-cached data loading) → solvis/nzshm libraries
    → DynamoDB (metadata via pynamodb) + S3 (binary blobs via boto3)
```

### Key Modules

- **`solvis_graphql_api/schema.py`** — Root GraphQL schema (`QueryRoot`). All top-level query fields defined here.
- **`solvis_graphql_api/composite_solution/`** — Core domain logic:
  - `schema.py` — Pagination (relay cursors), filtering orchestration, connection builders
  - `cached.py` — LRU-cached functions for loading CompositeSolution archives and running filtered queries. Performance-critical.
  - `filtered_ruptures_args.py` — GraphQL input types for filtering
  - `filter_set_logic_options.py` — Union/Intersection set operations for combining location and fault filters
- **`solvis_graphql_api/data_store/`** — DynamoDB + S3 dual-storage layer. `BinaryLargeObject` stores metadata in DynamoDB and binary data in S3.
- **`solvis_graphql_api/color_scale/`** — Matplotlib-based color scale generation for visualization
- **`solvis_graphql_api/scripts/cli.py`** — CLI for uploading composite solution archives to DynamoDB/S3

### Domain Dependencies
- **solvis** — Inversion solution analysis (rupture filtering, geometry, fault sections)
- **nzshm-model** — Source logic trees and model version data
- **nzshm-common** — Location database and shared utilities

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `SLS_OFFLINE` | Set to `1` for local serverless | — |
| `TESTING` | Set to `1` for test environment | — |
| `REGION` | AWS region | `us-east-1` |
| `DEPLOYMENT_STAGE` | Stage name (local/dev/test/prod) | `LOCAL` |
| `S3_BUCKET_NAME` | S3 bucket for blob storage | `nzshm22-solvis-graphql-api-local` |
| `LOGGING_CFG` | Path to logging YAML config | — |

## CI/CD

GitHub Actions workflow (`.github/workflows/dev.yml`) runs on PRs to `main` and `deploy-test`. Uses shared workflow from `GNS-Science/nshm-github-actions` for Python 3.12 test runs.
