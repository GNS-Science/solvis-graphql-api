"""
based on https://github.com/logandk/serverless-wsgi?tab=readme-ov-file#usage-without-serverless

needed because serverless-wsgi and ecr/image dont' play together in the package/deploy steps
"""

import logging

import serverless_wsgi

from solvis_graphql_api import solvis_graphql_api

logger = logging.getLogger(__name__)
logger.info(f"{__name__} module loaded")
# If you need to send additional content types as text, add then directly
# to the whitelist:
#
# serverless_wsgi.TEXT_MIME_TYPES.append("application/custom+json")


def handler(event, context):
    logger.info(f"{handler.__name__} call with event: {event}")
    return serverless_wsgi.handle_request(solvis_graphql_api.app, event, context)
