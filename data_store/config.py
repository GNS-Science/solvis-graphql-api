"""
This module exports comfiguration for the current package
"""

import os


def boolean_env(environ_name, default='FALSE'):
    return bool(os.getenv(environ_name, default).upper() in ["1", "Y", "YES", "TRUE"])


IS_OFFLINE = boolean_env('SLS_OFFLINE')  # set by serverless-wsgi plugin
TESTING = boolean_env('TESTING')

if IS_OFFLINE:
    DB_ENDPOINT = "http://localhost:8000"
else:
    DB_ENDPOINT = os.getenv("DB_ENDPOINT", '')

REGION = os.getenv('REGION', 'us-east-1')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
STACK_NAME = os.getenv('STACK_NAME')
CW_METRICS_RESOLUTION = os.getenv('CW_METRICS_RESOLUTION', 60)  # 1 for high resolution or 60
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', "nzshm22-solvis-graphql-api-local")

LOGGING_CFG = os.getenv('LOGGING_CFG', 'logging_aws.yaml')
