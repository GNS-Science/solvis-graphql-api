"""The API schema for conposite solutions."""

import json
import logging

import graphene
from graphene import relay

from solvis_graphql_api.solution_schema import (  # GeojsonAreaStyleArguments,; apply_fault_trace_style,
    GeojsonLineStyleArguments,
)

from .helpers import get_composite_solution

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
        # model_id = kwargs.get('model_id')
        # fault_system = kwargs.get('fault_system')  # cursor of last page, or none

        log.info(f'resolve resolve_fault_surfaces : {root.model_id}, {root.fault_system}')

        composite_solution = get_composite_solution(root.model_id)
        rupture_surface = composite_solution._solutions[root.fault_system].rupture_surface(root.rupture_index)
        # print(rupture_surface)
        return json.loads(rupture_surface.to_json(indent=2)) if rupture_surface is not None else None


class CompositeRuptureDetailArguments(graphene.InputObjectType):
    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    rupture_index = graphene.Int()

    fault_trace_style = GeojsonLineStyleArguments(
        required=False,
        description="feature style for rupture trace geojson.",
        default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
    )


class RuptureDetailConnection(relay.Connection):
    class Meta:
        node = CompositeRuptureDetail

    total_count = graphene.Int()

    def resolve_edges(root, info, *args, **kwargs):
        print('RuptureDetailConnection.resolve_edges', args, kwargs)
        print(root, root.edges)
        # assert 0
        return root.edges
