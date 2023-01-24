# solvis-graphql-api

GRAPHQL API for analysis of opensha modular Inversion Solutions.

Using Flask with Serverless framework to operate as a AWS Lambda API.

The API documentation is served by default from the service root.


## Getting started

```
poetry install
npm install --save serverless
npm install --save serverless-python-requirements
npm install --save serverless-wsgi
npm install --save serverless-plugin-warmup
```

### WSGI

```
sls wsgi serve
```

### Run full stack locally

```
SLS_OFFLINE=1 npx serverless wsgi serve
```

### Unit tests

`poetry run pytest` note that some environment variables are set in `setup.cfg`.

