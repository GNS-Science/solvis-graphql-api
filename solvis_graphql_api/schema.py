"""The main API schema."""

import logging

import geopandas as gpd
import graphene
from graphene import relay

# from nzshm_common.location import CodedLocation
from solvis_store.solvis_db_query import matched_rupture_sections_gdf

log = logging.getLogger(__name__)


class InversionSolutionRupture(graphene.ObjectType):
    fault_id = graphene.Int(description="Unique ID of the rupture within this solution")
    magnitude = graphene.Float(description='rupture magnitude')


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
    location_codes = graphene.List(
        graphene.String,
        required=False,
        description="Optional list of locations codes for proximity filtering e.g. `WLG,PMR,ZQN`",
    )
    radius_km = graphene.Int(required=False, description='The rupture/location intersection radius in km')
    minimum_rate = graphene.Float(
        required=False, description="Constrain to ruptures having a annual rate above the value supplied."
    )
    maximum_rate = graphene.Float(
        required=False, description="Constrain to ruptures having a annual rate below the value supplied."
    )
    minimum_mag = graphene.Float(
        required=False, description="Constrain to ruptures having a magnitude above the value supplied."
    )
    maximum_mag = graphene.Float(
        required=False, description="Constrain to ruptures having a magnitude below the value supplied."
    )


class FilterInversionSolution(graphene.ObjectType):
    analysis = graphene.Field(InversionSolutionAnalysis)


class QueryRoot(graphene.ObjectType):
    """This is the entry point for solvis graphql query operations"""

    node = relay.Node.Field()
    about = graphene.String(description='About this Solvis API ')
    analyse_solution = graphene.Field(
        FilterInversionSolution, input=graphene.Argument(InversionSolutionAnalysisArguments, required=True)
    )  # description='About this Solvis API ')

    def resolve_about(root, info, **args):
        return "Hello World, I am solvis_graphql_api!"

    def resolve_analyse_solution(root, info, input, **args):
        log.info('args: %s input:%s' % (args, input))
        rupture_sections_gdf = matched_rupture_sections_gdf(
            input['solution_id'],
            ','.join(input['location_codes']),  # convert to string
            input['radius_km'] * 1000,
            min_rate=input.get('minimum_rate') or 1e-20,
            max_rate=input.get('maximum_rate'),
            min_mag=input.get('minimum_mag'),
            max_mag=input.get('maximum_mag'),
        )
        log.info('rupture_sections_gdf %s' % rupture_sections_gdf)
        geojson = gpd.GeoDataFrame(rupture_sections_gdf).to_json(indent=2)
        return FilterInversionSolution(analysis=InversionSolutionAnalysis(geojson=geojson))


schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)
