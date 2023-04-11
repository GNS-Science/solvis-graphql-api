"""The API schema for conposite solutions."""

import json
import logging
from functools import lru_cache

import graphene
from graphene import relay

from solvis_graphql_api.solution_schema import (
    GeojsonAreaStyleArguments,
    GeojsonLineStyleArguments,
    apply_fault_trace_style,
)

from .cached import get_composite_solution

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


@lru_cache
def rupture_detail(model_id: str, fault_system: str, rupture_index: int):
    sr = get_composite_solution(model_id)._solutions[fault_system].ruptures_with_rates
    return sr[sr['Rupture Index'] == rupture_index]


# class SortRupturesArgs(graphene.InputObjectType):
#     attribute = graphene.String()
#     ascending = graphene.Boolean()
#     bin_width = graphene.Float(optional=True)
#     log_bins = graphene.Boolean(optional=True)


class SimpleSortRupturesArgs(graphene.InputObjectType):
    attribute = graphene.String()
    ascending = graphene.Boolean()


class CompositeRuptureDetail(graphene.ObjectType):

    ATTRIBUTE_COLUMN_MAP = dict(
        rupture_index="Rupture Index",
        magnitude='Magnitude',
        rake_mean='Average Rake (degrees)',
        area='Area (m^2)',
        length='Length (m)',
    )

    @staticmethod
    def column_name(field_name: str):
        return CompositeRuptureDetail.ATTRIBUTE_COLUMN_MAP.get(field_name, field_name)

    class Meta:
        interfaces = (relay.Node,)

    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")

    # rupture properties
    rupture_index = graphene.Int()
    magnitude = graphene.Float()
    area = graphene.Float(description="Rupture length in kilometres^2")  # 'Area (m^2)',
    length = graphene.Float(description="Rupture length in kilometres)")  # 'Length (m)',
    rake_mean = graphene.Float(
        description="average rake angle (degrees) of the entire rupture"
    )  # 'Average Rake (degrees)',

    # rupture rate properties
    rate_weighted_mean = graphene.Float(description="mean of `rate` * `branch weight` of the contributing solutions")
    rate_max = graphene.Float(description="maximum rate from contributing solutions")
    rate_min = graphene.Float(description="minimum rate from contributing solutions")
    rate_count = graphene.Int(description="count of model solutions that include this rupture")

    # geojson props
    fault_traces = graphene.JSONString()
    fault_surfaces = graphene.Field(
        graphene.JSONString,
        style=graphene.Argument(
            GeojsonAreaStyleArguments,
            required=False,
            description="feature style for rupture trace geojson.",
            default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
        ),
    )

    def resolve_id(root, info, *args, **kwargs):
        return f'{root.fault_system}:{root.rupture_index}'

    def resolve_magnitude(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['Magnitude']), 3)

    def resolve_area(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['Area (m^2)'] / 1e6), 0)

    def resolve_length(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['Length (m)'] / 1e3), 0)

    def resolve_rake_mean(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['Average Rake (degrees)']), 1)

    def resolve_rate_weighted_mean(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['rate_weighted_mean']), 9)

    def resolve_rate_max(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['rate_max']), 9)

    def resolve_rate_min(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['rate_min']), 9)

    def resolve_rate_count(root, info, *args, **kwargs):
        rupt = rupture_detail(root.model_id, root.fault_system, root.rupture_index)
        return round(float(rupt['rate_count']), 9)

    def resolve_fault_surfaces(root, info, style, *args, **kwargs):
        log.info(f'resolve resolve_fault_surfaces : {root.model_id}, {root.fault_system} style: {style}')
        composite_solution = get_composite_solution(root.model_id)
        rupture_surface_gdf = composite_solution._solutions[root.fault_system].rupture_surface(root.rupture_index)

        rupture_surface_gdf = rupture_surface_gdf.drop(
            columns=[
                'key_0',
                'fault_system',
                'Rupture Index',
                'rate_max',
                'rate_min',
                'rate_count',
                'rate_weighted_mean',
                'Magnitude',
                'Average Rake (degrees)',
                'Area (m^2)',
                'Length (m)',
            ]
        )

        return (
            apply_fault_trace_style(json.loads(rupture_surface_gdf.to_json(indent=2)), style)
            if rupture_surface_gdf is not None
            else None
        )


class RuptureDetailConnection(relay.Connection):
    class Meta:
        node = CompositeRuptureDetail

    total_count = graphene.Int()


class CompositeRuptureDetailArgs(graphene.InputObjectType):
    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    rupture_index = graphene.Int()

    fault_trace_style = GeojsonLineStyleArguments(
        required=False,
        description="feature style for rupture trace geojson.",
        default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
    )


class FilterRupturesArgs(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    model_id = graphene.String(required=True, description="The ID of NSHM model")

    fault_system = graphene.String(
        required=True,
        description="One or more fault systems to consider from [`HIK`, `PUY`, `CRU`]",
    )

    location_codes = graphene.List(
        graphene.String,
        required=False,
        default_value=[],
        description="Optional list of locations codes for proximity filtering e.g. `WLG,PMR,ZQN`",
    )

    radius_km = graphene.Int(required=False, description='The rupture/location intersection radius in km')

    minimum_rate = graphene.Float(
        required=False, description="Constrain to fault_sections having a annual rate above the value supplied."
    )
    maximum_rate = graphene.Float(
        required=False, description="Constrain to fault_sections having a annual rate below the value supplied."
    )
    minimum_mag = graphene.Float(
        required=False, description="Constrain to fault_sections having a magnitude above the value supplied."
    )
    maximum_mag = graphene.Float(
        required=False, description="Constrain to fault_sections having a magnitude below the value supplied."
    )

    fault_trace_style = GeojsonLineStyleArguments(
        required=False,
        description="feature style for rupture trace geojson.",
        default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
    )

    fault_surface_style = GeojsonAreaStyleArguments(
        required=False,
        description="feature style for rupture surface geojson.",
        default_value=dict(
            stroke_color="black", stroke_width=1, stroke_opacity=1.0, fill_color="lightblue", fill_opacity="0.5"
        ),
    )
