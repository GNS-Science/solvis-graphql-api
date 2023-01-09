# solvis-graphql-api

GRAPHQL API for analysis of opensha modular Inversion Solutions.

Using Flask with Serverless framework to operate as a AWS Lambda API.

The API documentation is served by default from the service root.


## Getting started

```
poetry install
npm install --save serverless
npm install --save serverless-dynamodb-local
npm install --save serverless-python-requirements
npm install --save serverless-wsgi
sls dynamodb install
```

### WSGI

```
sls wsgi serve
```

### Run full stack locally
```
npx serverless dynamodb start --stage dev &\
SLS_OFFLINE=1 npx serverless offline-sns start &\
SLS_OFFLINE=1 npx serverless wsgi serve
```

### Unit tests

`TESTING=1 nosetests -v --nologcapture`

**TESTING** overrides **SLS_OFFLINE** to keep moto mockling happy
