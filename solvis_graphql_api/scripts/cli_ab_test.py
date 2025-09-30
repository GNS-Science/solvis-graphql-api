"""A cli script to check that two different APIs produce identical results.

For a 'no suprises' deployment we wil select the solvis queries as used by Kororaa
and we will supply a range of input values with generators to sweep them
The user must supply the API endpoint/API keys via a TOML config. 
"""
import io
import logging
import os
import pathlib
import sys
import time

import importlib.util
import click
import toml
import nzshm_model as nm

import sgqlc
from solvis_graphql_api import client

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

# from https://docs.python.org/3/library/importlib.html#importing-programmatically
def check_import(name: str):
    spec = importlib.util.find_spec(name)
    if spec:
        log.info('module %s has spec" %s ' % (name, spec))
    else:
        log.warning('unable to find_spec for module %s' % name)
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    if spec.loader:
        spec.loader.exec_module(module)
        log.info('library: "%s" was loaded' % module)
    else:
        log.warning('unable to find loader for spec %s' % name)
    return module

#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|
@click.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--a-key", "-A", default = 'prod')
@click.option("--b-key", "-B", default = 'test')
@click.option("--verbose", "-v", is_flag=True, default=False)
def cli(config_path, a_key, b_key, verbose):
    """
    Run A/B tests on two API endpoints

    CONFIG_PATH: path to the TOML config file.
    """
    with open(config_path) as f:
        conf = toml.load(f)

    if verbose:
        click.echo(f"config `{config_path}` has service keys: {conf['service'].keys()}")
        click.echo(f"using a-key: `{a_key}`, b-key: `{b_key}`")

    # print(dir(client))
    a_client = check_import( f"solvis_graphql_api.client.{a_key}_schema")
    b_client = check_import( f"solvis_graphql_api.client.{b_key}_schema")    
    print(a_client)
    print(b_client)
    # a_client = client[f"{a_key}_schema"]
    # b_client = client[f"{b_key}_schema"]
    # print(a_client)


    click.echo(f"solvis_graphql_api cli uploaded solvis composite solution {config_path} ")


if __name__ == "__main__":
    cli()  # pragma: no cover
