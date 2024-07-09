# solvis-graphql-api

GRAPHQL API for analysis of opensha modular Inversion Solutions.

Using Flask with Serverless framework to operate as a AWS Lambda API.

The API documentation is served by default from the service root.


## Getting started

```
poetry install
npm install
```

### Run full stack locally

```
npx serverless dynamodb start --stage local &\
npx serverless s3 start &\
SLS_OFFLINE=1 npx serverless wsgi serve
```

### Unit tests

`poetry run pytest` note that some environment variables are set in `setup.cfg`.

