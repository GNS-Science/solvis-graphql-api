"""Console script for solvis_graphql_api."""

import logging
import os
import pathlib
import sys
import time

import click
import nzshm_model as nm
from solvis import CompositeSolution
from solvis.inversion_solution.inversion_solution import BranchInversionSolution, InversionSolution

# from nzshm_common.location.location import location_by_id


# Get API key from AWS secrets manager
# API_URL = os.getenv('NZSHM22_SOLVIS_API_URL', "http://127.0.0.1:5000/graphql")
# API_KEY = os.getenv('NZSHM22_TOSHI_API_KEY', "")

DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
REGION = os.getenv('REGION', 'ap-southeast-2')  # SYDNEY


log = logging.getLogger()
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('solvis').setLevel(logging.INFO)

formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)

#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|


@click.command()
@click.argument('archive', type=click.Path(exists=True))
@click.argument('model_id')
def cli(archive, model_id):
    """
    Upload solvis composite solutions to service datastore.

    ARCHIVE: path to the CompostiSolutionArchive to be uploaded

    MODEL_ID: the model id
    """
    click.echo(f'archive: {archive}')
    click.echo(f'model : {model_id}')
    click.echo("solvis_graphql_api cli upload solvis composite solutions ")


if __name__ == "__main__":
    cli()  # pragma: no cover
