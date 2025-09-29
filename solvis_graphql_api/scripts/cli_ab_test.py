"""A script to check that two different APIs produce identical results

For a 'no suprises' deployment we wil select the solvis queries used by Kororaa
and we will supply a range of input values with generators to sweep them
The user must supply the API endpoint/API keys via a TOML config.  
"""
import io
import logging
import os
import pathlib
import sys
import time

import click
import toml
import nzshm_model as nm


log = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.INFO)
# logging.getLogger('solvis').setLevel(logging.INFO)
# logging.getLogger('solvis_graphql_api').setLevel(logging.DEBUG)

formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)

import os

import boto3
import botocore

import solvis_graphql_api.data_store.model
from solvis_graphql_api.data_store.config import (
    IS_OFFLINE,
    REGION,
    S3_BUCKET_NAME,
    TESTING,
)

credentials = boto3.Session().get_credentials() if not IS_OFFLINE else None
s3_client_args = (
    dict(
        aws_access_key_id="S3RVER",
        aws_secret_access_key="S3RVER",
        endpoint_url="http://localhost:4569",
    )
    if not TESTING and IS_OFFLINE
    else {}
)


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|
@click.command()
@click.argument("config", type=click.Path(exists=True))
def cli(config_path, model_id, ensure_table, read_back):
    """
    Run A/B tests on two API isntances
    CONFIG: path to the toml config
    """
    click.echo(f"solvis_graphql_api cli uploaded solvis composite solution {config_path} ")


if __name__ == "__main__":
    cli()  # pragma: no cover
