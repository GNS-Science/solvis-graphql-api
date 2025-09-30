import sgqlc.types
import sgqlc.types.relay


prod_schema = sgqlc.types.Schema()


# Unexport Node/PageInfo, let schema re-declare them
prod_schema -= sgqlc.types.relay.Node
prod_schema -= sgqlc.types.relay.PageInfo



########################################################################
# Scalars and Enumerations
########################################################################
Boolean = sgqlc.types.Boolean

class ColourScaleNormaliseEnum(sgqlc.types.Enum):
    __schema__ = prod_schema
    __choices__ = ('LIN', 'LOG')


Float = sgqlc.types.Float

ID = sgqlc.types.ID

Int = sgqlc.types.Int

class JSONString(sgqlc.types.Scalar):
    __schema__ = prod_schema


class SetOperationEnum(sgqlc.types.Enum):
    __schema__ = prod_schema
    __choices__ = ('DIFFERENCE', 'INTERSECTION', 'UNION')


String = sgqlc.types.String


########################################################################
# Input Objects
########################################################################
class ColorScaleArgsInput(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('name', 'min_value', 'max_value', 'normalisation')
    name = sgqlc.types.Field(String, graphql_name='name')
    min_value = sgqlc.types.Field(Float, graphql_name='min_value')
    max_value = sgqlc.types.Field(Float, graphql_name='max_value')
    normalisation = sgqlc.types.Field(ColourScaleNormaliseEnum, graphql_name='normalisation')


class CompositeRuptureDetailArgs(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'fault_system', 'rupture_index')
    model_id = sgqlc.types.Field(String, graphql_name='model_id')
    fault_system = sgqlc.types.Field(String, graphql_name='fault_system')
    rupture_index = sgqlc.types.Field(Int, graphql_name='rupture_index')


class FilterRupturesArgsInput(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'fault_system', 'corupture_fault_names', 'location_ids', 'radius_km', 'filter_set_options', 'minimum_rate', 'maximum_rate', 'minimum_mag', 'maximum_mag')
    model_id = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='model_id')
    fault_system = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='fault_system')
    corupture_fault_names = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='corupture_fault_names')
    location_ids = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='location_ids')
    radius_km = sgqlc.types.Field(Int, graphql_name='radius_km')
    filter_set_options = sgqlc.types.Field('FilterSetLogicOptionsInput', graphql_name='filter_set_options')
    minimum_rate = sgqlc.types.Field(Float, graphql_name='minimum_rate')
    maximum_rate = sgqlc.types.Field(Float, graphql_name='maximum_rate')
    minimum_mag = sgqlc.types.Field(Float, graphql_name='minimum_mag')
    maximum_mag = sgqlc.types.Field(Float, graphql_name='maximum_mag')


class FilterSetLogicOptionsInput(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('multiple_locations', 'multiple_faults', 'locations_and_faults')
    multiple_locations = sgqlc.types.Field(SetOperationEnum, graphql_name='multiple_locations')
    multiple_faults = sgqlc.types.Field(SetOperationEnum, graphql_name='multiple_faults')
    locations_and_faults = sgqlc.types.Field(SetOperationEnum, graphql_name='locations_and_faults')


class GeojsonAreaStyleArgumentsInput(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('stroke_color', 'stroke_width', 'stroke_opacity', 'fill_color', 'fill_opacity')
    stroke_color = sgqlc.types.Field(String, graphql_name='stroke_color')
    stroke_width = sgqlc.types.Field(Int, graphql_name='stroke_width')
    stroke_opacity = sgqlc.types.Field(Float, graphql_name='stroke_opacity')
    fill_color = sgqlc.types.Field(String, graphql_name='fill_color')
    fill_opacity = sgqlc.types.Field(Float, graphql_name='fill_opacity')


class GeojsonLineStyleArgumentsInput(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('stroke_color', 'stroke_width', 'stroke_opacity')
    stroke_color = sgqlc.types.Field(String, graphql_name='stroke_color')
    stroke_width = sgqlc.types.Field(Int, graphql_name='stroke_width')
    stroke_opacity = sgqlc.types.Field(Float, graphql_name='stroke_opacity')


class InversionSolutionAnalysisArguments(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('solution_id', 'location_ids', 'radius_km', 'minimum_rate', 'maximum_rate', 'minimum_mag', 'maximum_mag', 'fault_trace_style', 'location_area_style')
    solution_id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='solution_id')
    location_ids = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='location_ids')
    radius_km = sgqlc.types.Field(Int, graphql_name='radius_km')
    minimum_rate = sgqlc.types.Field(Float, graphql_name='minimum_rate')
    maximum_rate = sgqlc.types.Field(Float, graphql_name='maximum_rate')
    minimum_mag = sgqlc.types.Field(Float, graphql_name='minimum_mag')
    maximum_mag = sgqlc.types.Field(Float, graphql_name='maximum_mag')
    fault_trace_style = sgqlc.types.Field(GeojsonLineStyleArgumentsInput, graphql_name='fault_trace_style')
    location_area_style = sgqlc.types.Field(GeojsonAreaStyleArgumentsInput, graphql_name='location_area_style')


class SimpleSortRupturesArgs(sgqlc.types.Input):
    __schema__ = prod_schema
    __field_names__ = ('attribute', 'ascending')
    attribute = sgqlc.types.Field(String, graphql_name='attribute')
    ascending = sgqlc.types.Field(Boolean, graphql_name='ascending')



########################################################################
# Output Objects and Interfaces
########################################################################
class Node(sgqlc.types.Interface):
    __schema__ = prod_schema
    __field_names__ = ('id',)
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')


class ColorScale(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('name', 'min_value', 'max_value', 'normalisation', 'color_map')
    name = sgqlc.types.Field(String, graphql_name='name')
    min_value = sgqlc.types.Field(Float, graphql_name='min_value')
    max_value = sgqlc.types.Field(Float, graphql_name='max_value')
    normalisation = sgqlc.types.Field(ColourScaleNormaliseEnum, graphql_name='normalisation')
    color_map = sgqlc.types.Field('HexRgbValueMapping', graphql_name='color_map')


class CompositeRuptureSections(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'rupture_count', 'section_count', 'filter_arguments', 'max_magnitude', 'min_magnitude', 'max_participation_rate', 'min_participation_rate', 'fault_surfaces', 'fault_traces', 'mfd_histogram', 'color_scale')
    model_id = sgqlc.types.Field(String, graphql_name='model_id')
    rupture_count = sgqlc.types.Field(Int, graphql_name='rupture_count')
    section_count = sgqlc.types.Field(Int, graphql_name='section_count')
    filter_arguments = sgqlc.types.Field('FilterRupturesArgs', graphql_name='filter_arguments')
    max_magnitude = sgqlc.types.Field(Float, graphql_name='max_magnitude')
    min_magnitude = sgqlc.types.Field(Float, graphql_name='min_magnitude')
    max_participation_rate = sgqlc.types.Field(Float, graphql_name='max_participation_rate')
    min_participation_rate = sgqlc.types.Field(Float, graphql_name='min_participation_rate')
    fault_surfaces = sgqlc.types.Field(JSONString, graphql_name='fault_surfaces', args=sgqlc.types.ArgDict((
        ('color_scale', sgqlc.types.Arg(ColorScaleArgsInput, graphql_name='color_scale', default=None)),
        ('style', sgqlc.types.Arg(GeojsonAreaStyleArgumentsInput, graphql_name='style', default=None)),
))
    )
    fault_traces = sgqlc.types.Field(JSONString, graphql_name='fault_traces', args=sgqlc.types.ArgDict((
        ('color_scale', sgqlc.types.Arg(ColorScaleArgsInput, graphql_name='color_scale', default=None)),
        ('style', sgqlc.types.Arg(GeojsonLineStyleArgumentsInput, graphql_name='style', default=None)),
))
    )
    mfd_histogram = sgqlc.types.Field(sgqlc.types.list_of('MagFreqDist'), graphql_name='mfd_histogram')
    color_scale = sgqlc.types.Field(ColorScale, graphql_name='color_scale', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(String, graphql_name='name', default=None)),
        ('normalization', sgqlc.types.Arg(ColourScaleNormaliseEnum, graphql_name='normalization', default=None)),
        ('min_value', sgqlc.types.Arg(Float, graphql_name='min_value', default=None)),
        ('max_value', sgqlc.types.Arg(Float, graphql_name='max_value', default=None)),
))
    )


class CompositeSolution(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'fault_systems')
    model_id = sgqlc.types.Field(String, graphql_name='model_id')
    fault_systems = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='fault_systems')


class FilterInversionSolution(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('analysis',)
    analysis = sgqlc.types.Field('InversionSolutionAnalysis', graphql_name='analysis')


class FilterRupturesArgs(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'fault_system', 'corupture_fault_names', 'location_ids', 'radius_km', 'filter_set_options', 'minimum_rate', 'maximum_rate', 'minimum_mag', 'maximum_mag')
    model_id = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='model_id')
    fault_system = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='fault_system')
    corupture_fault_names = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='corupture_fault_names')
    location_ids = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='location_ids')
    radius_km = sgqlc.types.Field(Int, graphql_name='radius_km')
    filter_set_options = sgqlc.types.Field('FilterSetLogicOptions', graphql_name='filter_set_options')
    minimum_rate = sgqlc.types.Field(Float, graphql_name='minimum_rate')
    maximum_rate = sgqlc.types.Field(Float, graphql_name='maximum_rate')
    minimum_mag = sgqlc.types.Field(Float, graphql_name='minimum_mag')
    maximum_mag = sgqlc.types.Field(Float, graphql_name='maximum_mag')


class FilterSetLogicOptions(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('multiple_locations', 'multiple_faults', 'locations_and_faults')
    multiple_locations = sgqlc.types.Field(SetOperationEnum, graphql_name='multiple_locations')
    multiple_faults = sgqlc.types.Field(SetOperationEnum, graphql_name='multiple_faults')
    locations_and_faults = sgqlc.types.Field(SetOperationEnum, graphql_name='locations_and_faults')


class HexRgbValueMapping(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('levels', 'hexrgbs')
    levels = sgqlc.types.Field(sgqlc.types.list_of(Float), graphql_name='levels')
    hexrgbs = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='hexrgbs')


class InversionSolutionAnalysis(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('solution_id', 'fault_sections_geojson', 'location_geojson')
    solution_id = sgqlc.types.Field(ID, graphql_name='solution_id')
    fault_sections_geojson = sgqlc.types.Field(JSONString, graphql_name='fault_sections_geojson')
    location_geojson = sgqlc.types.Field(JSONString, graphql_name='location_geojson')


class Location(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('location_id', 'name', 'latitude', 'longitude')
    location_id = sgqlc.types.Field(String, graphql_name='location_id')
    name = sgqlc.types.Field(String, graphql_name='name')
    latitude = sgqlc.types.Field(Float, graphql_name='latitude')
    longitude = sgqlc.types.Field(Float, graphql_name='longitude')


class LocationDetailConnection(sgqlc.types.relay.Connection):
    __schema__ = prod_schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null('PageInfo'), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('LocationDetailEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class LocationDetailEdge(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('LocationDetail', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class LocationList(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('list_id', 'location_ids', 'locations')
    list_id = sgqlc.types.Field(String, graphql_name='list_id')
    location_ids = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='location_ids')
    locations = sgqlc.types.Field(sgqlc.types.list_of(Location), graphql_name='locations')


class MagFreqDist(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('bin_center', 'rate', 'cumulative_rate')
    bin_center = sgqlc.types.Field(Float, graphql_name='bin_center')
    rate = sgqlc.types.Field(Float, graphql_name='rate')
    cumulative_rate = sgqlc.types.Field(Float, graphql_name='cumulative_rate')


class PageInfo(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('has_next_page', 'has_previous_page', 'start_cursor', 'end_cursor')
    has_next_page = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='hasNextPage')
    has_previous_page = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='hasPreviousPage')
    start_cursor = sgqlc.types.Field(String, graphql_name='startCursor')
    end_cursor = sgqlc.types.Field(String, graphql_name='endCursor')


class QueryRoot(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('color_scale', 'node', 'about', 'inversion_solution', 'locations_by_id', 'composite_solution', 'composite_rupture_detail', 'filter_ruptures', 'filter_rupture_sections', 'get_parent_fault_names', 'get_radii_set', 'get_radii_sets', 'get_location', 'get_locations', 'get_location_list', 'get_location_lists')
    color_scale = sgqlc.types.Field(ColorScale, graphql_name='color_scale', args=sgqlc.types.ArgDict((
        ('name', sgqlc.types.Arg(String, graphql_name='name', default=None)),
        ('min_value', sgqlc.types.Arg(Float, graphql_name='min_value', default=None)),
        ('max_value', sgqlc.types.Arg(Float, graphql_name='max_value', default=None)),
        ('normalization', sgqlc.types.Arg(ColourScaleNormaliseEnum, graphql_name='normalization', default=None)),
))
    )
    node = sgqlc.types.Field(Node, graphql_name='node', args=sgqlc.types.ArgDict((
        ('id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='id', default=None)),
))
    )
    about = sgqlc.types.Field(String, graphql_name='about')
    inversion_solution = sgqlc.types.Field(FilterInversionSolution, graphql_name='inversion_solution', args=sgqlc.types.ArgDict((
        ('filter', sgqlc.types.Arg(sgqlc.types.non_null(InversionSolutionAnalysisArguments), graphql_name='filter', default=None)),
))
    )
    locations_by_id = sgqlc.types.Field(LocationDetailConnection, graphql_name='locations_by_id', args=sgqlc.types.ArgDict((
        ('location_ids', sgqlc.types.Arg(sgqlc.types.non_null(sgqlc.types.list_of(String)), graphql_name='location_ids', default=None)),
))
    )
    composite_solution = sgqlc.types.Field(CompositeSolution, graphql_name='composite_solution', args=sgqlc.types.ArgDict((
        ('model_id', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='model_id', default=None)),
))
    )
    composite_rupture_detail = sgqlc.types.Field('CompositeRuptureDetail', graphql_name='composite_rupture_detail', args=sgqlc.types.ArgDict((
        ('filter', sgqlc.types.Arg(sgqlc.types.non_null(CompositeRuptureDetailArgs), graphql_name='filter', default=None)),
))
    )
    filter_ruptures = sgqlc.types.Field('RuptureDetailConnection', graphql_name='filter_ruptures', args=sgqlc.types.ArgDict((
        ('filter', sgqlc.types.Arg(sgqlc.types.non_null(FilterRupturesArgsInput), graphql_name='filter', default=None)),
        ('sortby', sgqlc.types.Arg(sgqlc.types.list_of(SimpleSortRupturesArgs), graphql_name='sortby', default=())),
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    filter_rupture_sections = sgqlc.types.Field(CompositeRuptureSections, graphql_name='filter_rupture_sections', args=sgqlc.types.ArgDict((
        ('filter', sgqlc.types.Arg(sgqlc.types.non_null(FilterRupturesArgsInput), graphql_name='filter', default=None)),
))
    )
    get_parent_fault_names = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='get_parent_fault_names', args=sgqlc.types.ArgDict((
        ('model_id', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='model_id', default=None)),
        ('fault_system', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='fault_system', default=None)),
))
    )
    get_radii_set = sgqlc.types.Field('RadiiSet', graphql_name='get_radii_set', args=sgqlc.types.ArgDict((
        ('radii_set_id', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='radii_set_id', default=None)),
))
    )
    get_radii_sets = sgqlc.types.Field(sgqlc.types.list_of('RadiiSet'), graphql_name='get_radii_sets')
    get_location = sgqlc.types.Field(Location, graphql_name='get_location', args=sgqlc.types.ArgDict((
        ('location_id', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='location_id', default=None)),
))
    )
    get_locations = sgqlc.types.Field(sgqlc.types.list_of(Location), graphql_name='get_locations')
    get_location_list = sgqlc.types.Field(LocationList, graphql_name='get_location_list', args=sgqlc.types.ArgDict((
        ('list_id', sgqlc.types.Arg(sgqlc.types.non_null(String), graphql_name='list_id', default=None)),
))
    )
    get_location_lists = sgqlc.types.Field(sgqlc.types.list_of(LocationList), graphql_name='get_location_lists')


class RadiiSet(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('radii_set_id', 'radii')
    radii_set_id = sgqlc.types.Field(Int, graphql_name='radii_set_id')
    radii = sgqlc.types.Field(sgqlc.types.list_of(Int), graphql_name='radii')


class RuptureDetailConnection(sgqlc.types.relay.Connection):
    __schema__ = prod_schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null(PageInfo), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('RuptureDetailEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class RuptureDetailEdge(sgqlc.types.Type):
    __schema__ = prod_schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('CompositeRuptureDetail', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class CompositeRuptureDetail(sgqlc.types.Type, Node):
    __schema__ = prod_schema
    __field_names__ = ('model_id', 'fault_system', 'rupture_index', 'magnitude', 'area', 'length', 'rake_mean', 'rate_weighted_mean', 'rate_max', 'rate_min', 'rate_count', 'fault_traces', 'fault_surfaces')
    model_id = sgqlc.types.Field(String, graphql_name='model_id')
    fault_system = sgqlc.types.Field(String, graphql_name='fault_system')
    rupture_index = sgqlc.types.Field(Int, graphql_name='rupture_index')
    magnitude = sgqlc.types.Field(Float, graphql_name='magnitude')
    area = sgqlc.types.Field(Float, graphql_name='area')
    length = sgqlc.types.Field(Float, graphql_name='length')
    rake_mean = sgqlc.types.Field(Float, graphql_name='rake_mean')
    rate_weighted_mean = sgqlc.types.Field(Float, graphql_name='rate_weighted_mean')
    rate_max = sgqlc.types.Field(Float, graphql_name='rate_max')
    rate_min = sgqlc.types.Field(Float, graphql_name='rate_min')
    rate_count = sgqlc.types.Field(Int, graphql_name='rate_count')
    fault_traces = sgqlc.types.Field(JSONString, graphql_name='fault_traces')
    fault_surfaces = sgqlc.types.Field(JSONString, graphql_name='fault_surfaces', args=sgqlc.types.ArgDict((
        ('style', sgqlc.types.Arg(GeojsonAreaStyleArgumentsInput, graphql_name='style', default={'stroke_color': 'black', 'stroke_width': 1, 'stroke_opacity': 1})),
))
    )


class LocationDetail(sgqlc.types.Type, Node):
    __schema__ = prod_schema
    __field_names__ = ('location_id', 'name', 'latitude', 'longitude', 'radius_geojson')
    location_id = sgqlc.types.Field(String, graphql_name='location_id')
    name = sgqlc.types.Field(String, graphql_name='name')
    latitude = sgqlc.types.Field(Float, graphql_name='latitude')
    longitude = sgqlc.types.Field(Float, graphql_name='longitude')
    radius_geojson = sgqlc.types.Field(JSONString, graphql_name='radius_geojson', args=sgqlc.types.ArgDict((
        ('radius_km', sgqlc.types.Arg(sgqlc.types.non_null(Int), graphql_name='radius_km', default=None)),
        ('style', sgqlc.types.Arg(GeojsonAreaStyleArgumentsInput, graphql_name='style', default={'stroke_color': 'black', 'stroke_width': 1, 'stroke_opacity': 1})),
))
    )



########################################################################
# Unions
########################################################################

########################################################################
# Schema Entry Points
########################################################################
prod_schema.query_type = QueryRoot
prod_schema.mutation_type = None
prod_schema.subscription_type = None

