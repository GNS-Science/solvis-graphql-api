"""The API schema for conposite solutions."""

import json
import logging

import graphene
from graphene import relay

from solvis_graphql_api.solution_schema import GeojsonAreaStyleArguments, GeojsonLineStyleArguments

from .cached import get_composite_solution

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


class CompositeRuptureDetail(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node,)

    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    rupture_index = graphene.Int()

    fault_traces = graphene.JSONString()
    fault_surfaces = graphene.JSONString()

    def resolve_id(root, info, *args, **kwargs):
        return f'{root.fault_system}:{root.rupture_index}'

    def resolve_fault_surfaces(root, info, *args, **kwargs):
        log.info(f'resolve resolve_fault_surfaces : {root.model_id}, {root.fault_system}')
        composite_solution = get_composite_solution(root.model_id)
        rupture_surface = composite_solution._solutions[root.fault_system].rupture_surface(root.rupture_index)
        return json.loads(rupture_surface.to_json(indent=2)) if rupture_surface is not None else None


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
