# solvis-graphql-api

GRAPHQL API for analysis of opensha modular Inversion Solutions.

Using Flask with Serverless framework to operate as a AWS Lambda API.

The API documentation is served by default from the service root.


## Getting started

```
poetry env use python3.10
poetry install
npm install
serverless dynamodb install
```

### Run full stack locally

```
npx serverless dynamodb start --stage local &\
npx serverless s3 start &\
SLS_OFFLINE=1 poetry run npx serverless wsgi serve
```

then

```
AWS_PROFILE=*** SLS_OFFLINE=1 poetry run cli WORKING/NSHM_v1.0.4_CompositeSolution.zip NSHM_v1.0.4 -R --ensure_table
```

### Unit tests

`poetry run pytest` note that some environment variables are set in `setup.cfg`.


### Push a composite solution

```
AWS_PROFILE=*** REGION=ap-southeast-4 DEPLOYMENT_STAGE=dev S3_BUCKET_NAME=nzshm22-solvis-graphql-api-dev cli WORKING/NSHM_v1.0.4_CompositeSolution.zip NSHM_v1.0.4 -R
```