"""A cli script to check that two different APIs produce identical results.

For a 'no suprises' deployment we wil select the solvis queries as used by Kororaa
and we will supply a range of input values with generators to sweep them
The user must supply the API endpoint/API keys via a TOML config.
"""

import importlib.util
import io
import logging
import os
import pathlib
import sys
import time

import click
import nzshm_model as nm
import sgqlc
import toml
from sgqlc.endpoint.http import HTTPEndpoint
from sgqlc.operation import Operation

from solvis_graphql_api import client

log = logging.getLogger()
logging.getLogger("botocore").setLevel(logging.INFO)

formatter = logging.Formatter(
    fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
screen_handler = logging.StreamHandler(stream=sys.stdout)
screen_handler.setFormatter(formatter)
log.addHandler(screen_handler)


# from https://docs.python.org/3/library/importlib.html#importing-programmatically
def check_import(name: str):
    spec = importlib.util.find_spec(name)
    if spec:
        log.info('module %s has spec" %s ' % (name, spec))
    else:
        log.warning("unable to find_spec for module %s" % name)
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    if spec.loader:
        spec.loader.exec_module(module)
        log.info('library: "%s" was loaded' % module)
    else:
        log.warning("unable to find loader for spec %s" % name)
    return module


def get_endpoint(url: str, token: str):
    headers = {"x-api-key": token}
    return HTTPEndpoint(url, headers)


def call_api(query: str, url: str, token: str):
    endpoint = get_endpoint(url, token)
    data = endpoint(query, {})
    return data


#  _ __ ___   __ _(_)_ __
# | '_ ` _ \ / _` | | '_ \
# | | | | | | (_| | | | | |
# |_| |_| |_|\__,_|_|_| |_|
@click.command()
@click.argument("config_path", type=click.Path(exists=True))
@click.option("--a-key", "-A", default="prod")
@click.option("--b-key", "-B", default="test")
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

    # get the schema
    a_schema = getattr(
        check_import(f"solvis_graphql_api.client.{a_key}_schema"), f"{a_key}_schema"
    )
    b_schema = getattr(
        check_import(f"solvis_graphql_api.client.{b_key}_schema"), f"{b_key}_schema"
    )

    # get the service configs
    svc_a = conf["service"][a_key]
    svc_b = conf["service"][b_key]

    # configure the query operations / endpoints
    a_op = Operation(a_schema.QueryRoot)
    a_endpoint = get_endpoint(url=svc_a["endpoint"], token=svc_a["token"])
    b_op = Operation(b_schema.QueryRoot)
    b_endpoint = get_endpoint(url=svc_b["endpoint"], token=svc_b["token"])

    ##################
    # Run the tests
    ##################

    check_get_parent_fault_names(a_op, a_endpoint, b_op, b_endpoint)
    check_query_color_scale(a_op, a_endpoint, b_op, b_endpoint)
    check_query_about(a_op, a_endpoint, b_op, b_endpoint)


def check_query_about(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    # evaluate comparisons
    a_op.about()
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).about

    b_op.about()
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).about
    if not a_res == b_res:
        log.warning(f"about: `{a_res}` !== `{b_res}`")
    return a_res == b_res


def check_query_color_scale(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    # evaluate comparisons
    kwargs = dict(name="inferno", min_value=5, max_value=10, normalization="LIN")
    csa = a_op.color_scale(**kwargs)
    csa.color_map()
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).color_scale.color_map

    csb = b_op.color_scale(**kwargs)
    csb.color_map()
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).color_scale.color_map

    if not a_res.levels == b_res.levels:
        log.warning(f"color_scale.levels: `{a_res.levels}` !== `{b_res.levels}`")

    if not a_res.hexrgbs == b_res.hexrgbs:
        log.warning(f"color_scale.hexrgbs: `{a_res.hexrgbs}` !== `{b_res.hexrgbs}`")

    return (a_res.levels == b_res.levels) and (a_res.hexrgbs == b_res.hexrgbs)


def check_get_parent_fault_names(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(model_id="NSHM_v1.0.4", fault_system="CRU")
    a_op.get_parent_fault_names(**kwargs)
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).get_parent_fault_names

    b_op.get_parent_fault_names(**kwargs)
    b_data = a_endpoint(b_op)
    b_res = (b_op + b_data).get_parent_fault_names
    if not a_res == b_res:
        log.warning(f"get_parent_fault_name: `{a_res}` !== `{b_res}`")
    return a_res == b_res


if __name__ == "__main__":
    cli()  # pragma: no cover
