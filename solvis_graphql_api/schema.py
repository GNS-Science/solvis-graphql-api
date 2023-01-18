"""The main API schema."""

import logging

import graphene
from graphene import relay

from nzshm_common.location import CodedLocation

log = logging.getLogger(__name__)


class InversionSolutionRupture(graphene.ObjectType):
    fault_id = graphene.Int(description="Unique ID of the rupture within this solution")
    magnitude = graphene.Float(description='rupture magnitude' )

class InversionSolutionFaultSection(graphene.ObjectType):
    fault_id = graphene.String(description="Unique ID of the fault section eg WHV1")

class InversionSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given solution or filtered solution"""

    solution_id = graphene.ID()
    fault_sections = graphene.List(InversionSolutionFaultSection)
    ruptures = graphene.List(InversionSolutionRupture)
    geojson = graphene.JSONString()

class InversionSolutionAnalysisArguments(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    solution_id = graphene.ID(required=True, description="The ID of the InversionSolution")
    location_codes = graphene.List(graphene.String, required=False, description="Optional list of locations codes for proximity filtering e.g. `WLG,PMR,ZQN`")
    proximity_km = graphene.Int( required=False, description = 'The rupture/location intersection radius in km')
    min_rate = graphene.Float(required=False, description="Constrain to ruptures having a annual rate above the value supplied.")
    max_rate = graphene.Float(required=False, description="Constrain to ruptures having a annual rate below the value supplied.")
    min_mag = graphene.Float(required=False, description="Constrain to ruptures having a magnitude above the value supplied.")
    max_mag = graphene.Float(required=False, description="Constrain to ruptures having a magnitude below the value supplied.")


class FilterInversionSolution(graphene.ObjectType):

    class Arguments:
        input = InversionSolutionAnalysisArguments(required=True)

    analysis = graphene.Field(InversionSolutionAnalysis)

    @staticmethod
    def resolve_analysis(root, info, **args):
        log.info("FilterInversionSolution.resolve_analysis args: %s" % args)
        return InversionSolutionAnalysis("ABC", [], [], "" )


class QueryRoot(graphene.ObjectType):
    """This is the entry point for solvis graphql query operations"""

    node = relay.Node.Field()
    about = graphene.String(description='About this Solvis API ')
    analyse_solution = graphene.Field(FilterInversionSolution, input=graphene.Argument(InversionSolutionAnalysisArguments, required=True)) # description='About this Solvis API ')

    def resolve_about(root, info, **args):
        return "Hello World, I am solvis_graphql_api!"

    def resolve_analyse_solution(root, info, input, **args):
        log.info('args: %s input:%s' % (args, input))
        return FilterInversionSolution()
        return "Hello World, I am solvis_graphql_api!"

schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)