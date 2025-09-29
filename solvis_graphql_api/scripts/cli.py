"""Console script for solvis_graphql_api."""

# flake8: noqa this is a WIP
import io
import logging
import os
import pathlib
import sys
import time

import click
import nzshm_model as nm
import solvis

# from solvis.inversion_solution.inversion_solution import (
#     BranchInversionSolution,
#     InversionSolution,
# )

log = logging.getLogger()
logging.getLogger("solvis_graphql_api.data_store.model").setLevel(logging.DEBUG)
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
@click.argument("archive", type=click.Path(exists=True))
@click.argument("model_id")
@click.option(
    "--ensure_table",
    "-T",
    is_flag=True,
    default=False,
    help="optionally ensure our table exists()",
)
@click.option(
    "--read_back",
    "-R",
    is_flag=True,
    default=False,
    help="read back and verify the stored object",
)
def cli(archive, model_id, ensure_table, read_back):
    """
    Upload solvis composite solutions to service datastore.

    ARCHIVE: path to the CompostiSolutionArchive to be uploaded

    MODEL_ID: the model id
    """
    click.echo(f"archive: {archive}")
    click.echo(f"model : {model_id}")

    if ensure_table:
        log.debug(f"creds {s3_client_args}")
        if not solvis_graphql_api.data_store.model.BinaryLargeObject.exists():
            solvis_graphql_api.data_store.model.BinaryLargeObject.create_table()
            click.echo("created table")
    # try:
    #     s3_client = boto3.client('s3', **s3_client_args)
    #     res = s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
    #     log.info(res)
    #     click.echo("bucket created")
    # except (botocore.exceptions.ClientError) as err:
    #     pass

    model = nm.get_model_version(model_id)
    solution = solvis.CompositeSolution.from_archive(archive, model.source_logic_tree)
    assert isinstance(solution, solvis.CompositeSolution)

    with open(archive, "rb") as arc:
        blob_data = arc.read()
        newBlob = solvis_graphql_api.data_store.model.BinaryLargeObject(
            object_id=model_id,
            object_type="CompositeSolution",
            object_meta=dict(filename=pathlib.Path(archive).name),
            object_blob=blob_data,
            # client_args=s3_client_args,
        )
        newBlob.save()

    if read_back:
        obj = solvis_graphql_api.data_store.model.BinaryLargeObject.get(
            object_id=model_id,
            object_type="CompositeSolution",
        )
        # .set_s3_client_args(s3_client_args)

        # print(obj.object_blob)
        assert obj.object_blob == blob_data, "read back object is different"
        click.echo(f"compared blob OK for {model_id}, ")

    click.echo(f"solvis_graphql_api cli uploaded solvis composite solution {newBlob} ")


if __name__ == "__main__":
    cli()  # pragma: no cover
