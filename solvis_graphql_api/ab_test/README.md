## Intro

This package is used for full stack A/B tests with expectations based on the Kororaa Client.

It uses the [sgqlc](https://sgqlc.readthedocs.io/en/latest/) python library to produce a python client API from the 
API schema. So there's no hand-crafted graphql to be seen here.

## API Schema workflow

This follows the guidance at [sgqlc/README.md#code-generator](https://github.com/profusion/sgqlc#code-generator).

These schema should be updated to reflect the current state of the API enpoints you're testing. Don't assume that the 
current version in `ab_test/client` matches your deployed API.

### 1. Download the schema as json
```
$ poetry run python3 -m sgqlc.introspection \
     --exclude-deprecated \
     --exclude-description \
     -H "Authorization: x-api-key ${API_TOKEN}" \
     https://my-dev-api.com/graphql \
     dev_schema.json
```

### 2. build/update the python schema

```
$ poetry run sgqlc-codegen schema dev_schema.json solvis_graphql_api/ab _test/client/dev_schema.py
```

## API Testing

Now we can use the `cli_ab_test` script to excute test against the updated schema.

## 1. Set up a `toml` config file. 

Here's an example `ab.toml`with redacted credentials...

```
[service.prod]
endpoint = "https://42ncm9rc71.execute-api.ap-southeast-2.amazonaws.com/prod/graphql"
token = "..."

[service.test]
endpoint = "https://ciied31tx2.execute-api.ap-southeast-2.amazonaws.com/test/graphql"
token = "..."

[service.dev]
endpoint = "https://ld3pqmtvaa.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
token = "..."
```

## 2. Run the A/B tests

```
% poetry run cli_ab_test WORK/ab.toml -A dev -B dev -v
WARNING: optional `toshi` dependencies are not installed.
Running without `toshi` options
config `WORK/ab.toml` has service keys: dict_keys(['prod', 'test', 'dev'])
using a-key: `dev`, b-key: `dev`
%
```

**TIP:** the about ab_test will display the 2 API versions as reported by the endpoints. e.g. 

```
2025-10-06 16:42:29 WARNING  function: check_about, attribute: about: a/b test failed
2025-10-06 16:42:29 INFO     a: `Hello World, I am solvis_graphql_api! Version: 0.9.0` vs b: `Hello World, I am solvis_graphql_api! Version: 0.9.1`
```


