"""The API schema for conposite solutions."""

import logging

import graphene

log = logging.getLogger(__name__)


class FaultSystemSolution(graphene.ObjectType):
    """
    The aggregation of the inversion solutionson a given Source LogicTreeBranch
    model_id
    short_name
    long_name
    """

    model_id = graphene.String()
    short_name = graphene.String()
    long_name = graphene.String()


class CompositeSolution(graphene.ObjectType):
    """
    A complete NSHM model comprising at least on FaultSystemSolution
    """

    model_id = graphene.String()
    fault_systems = graphene.List(graphene.String)  # FaultSystemSolution)
    file_url = graphene.String(description="get a URL so one can download the file")
