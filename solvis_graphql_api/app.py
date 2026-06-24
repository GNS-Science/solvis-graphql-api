"""FastAPI + Mangum entry point — migration scaffold.

Replaces the Flask + ``serverless-wsgi`` container entry (``handler.py``). Mangum is
packaging-agnostic, so it runs inside the ECR container without the serverless-wsgi
workaround that ``handler.py`` exists for. Serves the Strawberry schema at ``/graphql``.

The Lambda handler is ``solvis_graphql_api.app.handler`` (wired in ``serverless.yml``
``functions.ecr-app.image.command`` and the ``Dockerfile`` CMD). The legacy Flask app
(``solvis_graphql_api.solvis_graphql_api:app``) stays importable until cutover.
"""

import logging
import logging.config
import os

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from strawberry.fastapi import GraphQLRouter

from solvis_graphql_api.strawberry_schema import schema

LOGGING_CFG = os.getenv("LOGGING_CFG", "solvis_graphql_api/logging_aws.yaml")
logger = logging.getLogger(__name__)


def _configure_logging() -> None:
    if os.path.exists(LOGGING_CFG):  # pragma: no cover
        with open(LOGGING_CFG) as f:
            logging.config.dictConfig(yaml.safe_load(f.read()))
    else:  # pragma: no cover
        logging.basicConfig(level=logging.INFO)


_configure_logging()

app = FastAPI()
# mirror the legacy flask_cors CORS(app) default (allow all origins)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
app.include_router(GraphQLRouter(schema), prefix="/graphql")

handler = Mangum(app)
