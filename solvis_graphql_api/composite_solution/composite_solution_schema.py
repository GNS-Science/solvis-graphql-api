"""The API schema for conposite solutions."""

import logging

import graphene

log = logging.getLogger(__name__)


class CompositeSolution(graphene.ObjectType):
    model_id = graphene.String()
    fault_systems = graphene.List(graphene.String)
