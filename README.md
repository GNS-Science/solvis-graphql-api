# solvis-graphql-api

GRAPHQL API for analysis of opensha modular Inversion Solutions.

Using Flask with Serverless framework to operate as a AWS Lambda API.

The API documentation is served by default from the service root.


## Getting started

Java is required .

 ```nvm current``` wanting node 22
 
 ### ensure yarn 2
 ```
 corepack enable
 yarn set version berry
 yarn --version
 ```
 
 ### upgrade to yarn
 ```
 yarn install
 yarn npm audit
 ```


 ```
poetry install
poetry lock
poetry shell
```

Make sure the dynamodb plugin for local tests is installed
```
yarn sls dynamodb install
```

### Run full stack locally

```
npx serverless dynamodb start --stage local &\
npx serverless s3 start &\
SLS_OFFLINE=1 poetry run yarn sls wsgi serve
```

then

```
AWS_PROFILE=*** SLS_OFFLINE=1 poetry run python .\solvis_graphql_api\scripts\cli.py WORKING/NSHM_v1.0.4_CompositeSolution.zip NSHM_v1.0.4 -R --ensure_table
```

### Unit tests

`poetry run pytest` note that some environment variables are set in `setup.cfg`.


### Push a composite solution

```
AWS_PROFILE=*** REGION=ap-southeast-4 DEPLOYMENT_STAGE=dev S3_BUCKET_NAME=nzshm22-solvis-graphql-api-dev poetry run python .\solvis_graphql_api\scripts\cli.py WORKING/NSHM_v1.0.4_CompositeSolution.zip NSHM_v1.0.4 -R
```
