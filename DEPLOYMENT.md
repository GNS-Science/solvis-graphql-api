# Container Image Support for AWS Lambda

This project has been switched to use the ECR as it's now too large to zip.

see https://www.serverless.com/blog/container-support-for-lambda

below are the deployment steps for local deployment

## login to aws ecr

```
chrisbc@MLX01 nshm-hazard-graphql-api % aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 461564345538.dkr.ecr.ap-southeast-2.amazonaws.com
Login Succeeded
```

## Get a base image

Using the AWS official python lambda image: `public.ecr.aws/lambda/python:3.12`

```
docker pull public.ecr.aws/lambda/python:3.12
3.12: Pulling from lambda/python
.....
Status: Downloaded newer image for public.ecr.aws/lambda/python:3.12
public.ecr.aws/lambda/python:3.12
```

### Update the requirements
poetry export --without-hashes --format=requirements.txt > requirements.txt

### test wsgi handlers

```
ENABLE_METRICS=0 poetry run yarn sls wsgi serve
```

## A Dockerfile

see [Dockerfile](./Dockerfile)

### build it
```
BUILDX_NO_DEFAULT_ATTESTATIONS=1 yarn sls package
```

### and/or just deploy it
```
BUILDX_NO_DEFAULT_ATTESTATIONS=1 yarn sls deploy --stage dev --region ap-southeast-2
```
