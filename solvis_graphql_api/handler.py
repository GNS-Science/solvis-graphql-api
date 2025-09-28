"""
based on https://github.com/logandk/serverless-wsgi?tab=readme-ov-file#usage-without-serverless

needed because serverless-wsgi and ecr/image dont' play together in the pacakge/deploy steps
"""

import serverless_wsgi

from solvis_graphql_api import solvis_graphql_api

# If you need to send additional content types as text, add then directly
# to the whitelist:
#
# serverless_wsgi.TEXT_MIME_TYPES.append("application/custom+json")

def handler(event, context):
    return serverless_wsgi.handle_request(solvis_graphql_api.app, event, context)
