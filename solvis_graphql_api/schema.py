"""The main API schema."""

import logging

import graphene
from graphene import relay
from nzshm_common.location.location import LOCATION_LISTS, LOCATIONS, location_by_id

from .composite_solution import (
    CompositeRuptureDetail,
    CompositeRuptureDetailArguments,
    CompositeSolutionAnalysisArguments,
    FilterCompositeSolution,
    analyse_composite_solution,
    composite_rupture_detail,
)
from .solution_schema import FilterInversionSolution, InversionSolutionAnalysisArguments, analyse_solution

log = logging.getLogger(__name__)


class RadiiSet(graphene.ObjectType):
    radii_set_id = graphene.Int(description='The unique radii_set_id')
    radii = graphene.List(graphene.Int, description="list of dimension in metres defined by the radii set.")


class Location(graphene.ObjectType):
    code = graphene.String(description='unique location code.')
    name = graphene.String(description='location name.')
    latitude = graphene.Float(description='location latitude.')
    longitude = graphene.Float(description='location longitude')


class LocationList(graphene.ObjectType):
    list_id = graphene.String(description='The unique location_list_id')
    location_codes = graphene.List(graphene.String, description="list of location codes.")
    locations = graphene.List(Location, description="the locations in this list.")

    def resolve_locations(root, info, **args):
        for code in root.location_codes:
            loc = location_by_id(code)
            yield Location(loc['id'], loc['name'], loc['latitude'], loc['longitude'])


RADII = [
    {'id': 1, 'radii': [10e3]},
    {'id': 2, 'radii': [10e3, 20e3]},
    {'id': 3, 'radii': [10e3, 20e3, 30e3]},
    {'id': 4, 'radii': [10e3, 20e3, 30e3, 40e3]},
    {'id': 5, 'radii': [10e3, 20e3, 30e3, 40e3, 50e3]},
    {'id': 6, 'radii': [10e3, 20e3, 30e3, 40e3, 50e3, 100e3]},
]


def get_one_location(location_code):
    for loc in LOCATIONS:
        if loc['id'] == location_code:
            return Location(loc['id'], loc['name'], loc['latitude'], loc['longitude'])
    raise IndexError("Location with id %s was not found." % location_code)


def get_one_location_list(location_list_id):
    locs = []
    for loc_list in LOCATION_LISTS:
        if loc_list['id'] == location_list_id:
            for location in LOCATIONS:
                if location['id'] in loc_list['locations']:
                    locs.append(location['id'])
            return LocationList(location_list_id, locs)
    raise IndexError("LocationList with id %s was not found." % location_list_id)


def get_one_radii_set(radii_set_id):
    for rad in RADII:
        if rad['id'] == radii_set_id:
            return RadiiSet(radii_set_id, rad['radii'])
    raise IndexError("Radii set with id %s was not found." % radii_set_id)


class QueryRoot(graphene.ObjectType):
    """This is the entry point for solvis graphql query operations"""

    node = relay.Node.Field()
    about = graphene.String(description='About this Solvis API ')
    analyse_solution = graphene.Field(
        FilterInversionSolution, input=graphene.Argument(InversionSolutionAnalysisArguments, required=True)
    )  # description='About this Solvis API ')

    analyse_composite_solution = graphene.Field(
        FilterCompositeSolution, input=graphene.Argument(CompositeSolutionAnalysisArguments, required=True)
    )  # description='About this Solvis API ')

    composite_rupture_detail = graphene.Field(
        CompositeRuptureDetail, input=graphene.Argument(CompositeRuptureDetailArguments, required=True)
    )

    # radii fields
    get_radii_set = graphene.Field(
        RadiiSet,
        radii_set_id=graphene.Argument(
            graphene.Int, required=True, description="the integer ID for the desired radii_set"
        ),
        description="Return ad single radii_set for the id passed in",
    )
    get_radii_sets = graphene.Field(graphene.List(RadiiSet), description="Return all the available radii_set")

    # location fields
    get_location = graphene.Field(
        Location,
        location_code=graphene.Argument(
            graphene.String, required=True, description="the location code of the desired location"
        ),
        description="Return a single location.",
    )
    get_locations = graphene.Field(graphene.List(Location), description="Return all the available locations")

    get_location_list = graphene.Field(
        LocationList,
        list_id=graphene.Argument(graphene.String, required=True, description="the id of the desired location_list"),
        description="Return a single location list.",
    )

    get_location_lists = graphene.Field(
        graphene.List(LocationList), description="Return all the available location lists"
    )

    def resolve_get_location(root, info, location_code, **args):
        log.info('resolve_get_location args: %s location_code:%s' % (args, location_code))
        return get_one_location(location_code)

    def resolve_get_locations(root, info, **args):
        log.info('resolve_get_locations args: %s' % args)
        return [Location(loc['id'], loc['name'], loc['latitude'], loc['longitude']) for loc in LOCATIONS]

    def resolve_get_location_list(root, info, list_id, **args):
        log.info('resolve_get_location args: %s list_id:%s' % (args, list_id))
        return get_one_location_list(list_id)

    def resolve_get_location_lists(root, info, **args):
        log.info('resolve_get_location_lists args: %s' % args)
        return [LocationList(ll['id'], ll['locations']) for ll in LOCATION_LISTS]

    def resolve_get_radii_set(root, info, radii_set_id, **args):
        log.info('resolve_get_radii_set args: %s radii_set_id:%s' % (args, radii_set_id))
        return get_one_radii_set(radii_set_id)

    def resolve_get_radii_sets(root, info, **args):
        log.info('resolve_get_radii_sets args: %s' % args)
        return [RadiiSet(rad['id'], rad['radii']) for rad in RADII]

    def resolve_about(root, info, **args):
        return "Hello World, I am solvis_graphql_api!"

    def resolve_analyse_solution(root, info, input, **args):
        return analyse_solution(input, *args)

    def resolve_analyse_composite_solution(root, info, input, **args):
        return analyse_composite_solution(input, *args)

    def resolve_composite_rupture_detail(root, info, input, **args):
        return composite_rupture_detail(input, *args)


schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)
