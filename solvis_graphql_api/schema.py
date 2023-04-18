"""The main API schema."""

import logging

import graphene
import solvis_graphql_api
from graphene import relay
from nzshm_common.location.location import LOCATION_LISTS, LOCATIONS, location_by_id

from .composite_solution import (
    CompositeRuptureDetail,
    CompositeRuptureDetailArgs,
    CompositeSolution,
    FilterRupturesArgs,
    RuptureDetailConnection,
    SimpleSortRupturesArgs,
    cached,
    paginated_filtered_ruptures,
)
from .location_schema import LocationDetailConnection, get_location_detail_list
from .solution_schema import FilterInversionSolution, InversionSolutionAnalysisArguments, get_inversion_solution

log = logging.getLogger(__name__)


class RadiiSet(graphene.ObjectType):
    radii_set_id = graphene.Int(description='The unique radii_set_id')
    radii = graphene.List(graphene.Int, description="list of dimension in metres defined by the radii set.")


class Location(graphene.ObjectType):
    location_id = graphene.String(description='unique location location_id.')
    name = graphene.String(description='location name.')
    latitude = graphene.Float(description='location latitude.')
    longitude = graphene.Float(description='location longitude')


class LocationList(graphene.ObjectType):
    list_id = graphene.String(description='The unique location_list_id')
    location_ids = graphene.List(graphene.String, description="list of location codes.")
    locations = graphene.List(Location, description="the locations in this list.")

    def resolve_locations(root, info, **args):
        for loc_id in root.location_ids:
            loc = location_by_id(loc_id)
            yield Location(loc['id'], loc['name'], loc['latitude'], loc['longitude'])


RADII = [
    {'id': 1, 'radii': [10e3]},
    {'id': 2, 'radii': [10e3, 20e3]},
    {'id': 3, 'radii': [10e3, 20e3, 30e3]},
    {'id': 4, 'radii': [10e3, 20e3, 30e3, 40e3]},
    {'id': 5, 'radii': [10e3, 20e3, 30e3, 40e3, 50e3]},
    {'id': 6, 'radii': [10e3, 20e3, 30e3, 40e3, 50e3, 100e3]},
]


def get_one_location(location_id):
    for loc in LOCATIONS:
        if loc['id'] == location_id:
            return Location(loc['id'], loc['name'], loc['latitude'], loc['longitude'])
    raise IndexError("Location with id %s was not found." % location_id)


def get_one_location_list(location_list_id):
    ll = LOCATION_LISTS.get(location_list_id)
    if ll:
        return LocationList(location_list_id, ll['locations'])
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

    def resolve_about(root, info, **args):
        return f"Hello World, I am solvis_graphql_api! Version: {solvis_graphql_api.__version__}"

    inversion_solution = graphene.Field(
        FilterInversionSolution, filter=graphene.Argument(InversionSolutionAnalysisArguments, required=True)
    )

    def resolve_inversion_solution(root, info, filter, **args):
        return get_inversion_solution(filter, *args)

    locations_by_id = graphene.Field(
        LocationDetailConnection,
        location_ids=graphene.List(
            graphene.String,
            required=True,
            description="list of nzshm_common.location_ids e.g. `[\"WLG\",\"PMR\",\"ZQN\"]`",
        ),
    )

    def resolve_locations_by_id(root, info, location_ids, **args):
        return get_location_detail_list(location_ids, **args)

    composite_solution = graphene.Field(
        CompositeSolution,
        model_id=graphene.Argument(
            graphene.String, required=True, description="A valid NSHM model id e.g. `NSHM_1.0.0`"
        ),
    )

    def resolve_composite_solution(root, info, model_id, **args):
        log.info('resolve_composite_solution model_id: %s' % (model_id))
        solution = cached.get_composite_solution(model_id)
        return CompositeSolution(model_id=model_id, fault_systems=solution._solutions.keys())

    composite_rupture_detail = graphene.Field(
        CompositeRuptureDetail, filter=graphene.Argument(CompositeRuptureDetailArgs, required=True)
    )

    def resolve_composite_rupture_detail(root, info, filter, **args):
        log.info('resolve_composite_rupture_detail filter:%s' % filter)
        model_id = filter['model_id'].strip()
        fault_system = filter['fault_system']
        rupture_index = filter['rupture_index']
        return CompositeRuptureDetail(
            model_id=model_id,
            fault_system=fault_system,
            rupture_index=rupture_index,
        )

    # todo_advanced_filter_ruptures = graphene.ConnectionField(
    #     RuptureDetailConnection,
    #     filter=graphene.Argument(FilterRupturesArgs, required=True),
    #     sortby=graphene.Argument(graphene.List(SortRupturesArgs), default_value=[]),
    # )

    # def resolve_todo_advanced_filter_ruptures(root, info, filter, sortby, **kwargs):
    #     print('resolve_todo_advanced_filter_ruptures', filter, kwargs)
    #     return paginated_filtered_ruptures(filter, sortby, **kwargs)

    filter_ruptures = graphene.ConnectionField(
        RuptureDetailConnection,
        filter=graphene.Argument(FilterRupturesArgs, required=True),
        sortby=graphene.Argument(graphene.List(SimpleSortRupturesArgs), default_value=[]),
    )

    def resolve_filter_ruptures(root, info, filter, sortby, **kwargs):
        print('resolve_filter_ruptures', filter, kwargs)
        return paginated_filtered_ruptures(filter, sortby, **kwargs)

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
        location_id=graphene.Argument(
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

    def resolve_get_location(root, info, location_id, **args):
        log.info('resolve_get_location args: %s location_id:%s' % (args, location_id))
        return get_one_location(location_id)

    def resolve_get_locations(root, info, **args):
        log.info('resolve_get_locations args: %s' % args)
        return [Location(loc['id'], loc['name'], loc['latitude'], loc['longitude']) for loc in LOCATIONS]

    def resolve_get_location_list(root, info, list_id, **args):
        log.info('resolve_get_location args: %s list_id:%s' % (args, list_id))
        return get_one_location_list(list_id)

    def resolve_get_location_lists(root, info, **args):
        log.info('resolve_get_location_lists args: %s' % args)
        return [LocationList(key, ll['locations']) for key, ll in LOCATION_LISTS.items()]

    def resolve_get_radii_set(root, info, radii_set_id, **args):
        log.info('resolve_get_radii_set args: %s radii_set_id:%s' % (args, radii_set_id))
        return get_one_radii_set(radii_set_id)

    def resolve_get_radii_sets(root, info, **args):
        log.info('resolve_get_radii_sets args: %s' % args)
        return [RadiiSet(rad['id'], rad['radii']) for rad in RADII]


schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)
