"""The API schema for conposite solutions."""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, List

import geopandas as gpd
import graphene
from graphene import relay
import graphql_relay

import nzshm_model as nm
import pandas as pd
import solvis
from nzshm_common.location.location import location_by_id

from solvis_graphql_api.solution_schema import (
    GeojsonAreaStyleArguments,
    GeojsonLineStyleArguments,
    apply_fault_trace_style,
    get_location_polygon,
    location_features_geojson,
)
from .helpers import matched_rupture_sections_gdf, get_composite_solution
from .composite_rupture_detail import CompositeRuptureDetail

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


class RuptureDetailConnection(relay.Connection):
    class Meta:
        node = CompositeRuptureDetail
        # cursor = graphene.String

    # class Edge:
    #     other = String()

    total_count = graphene.Int()
    #page_info = relay.PageInfo()

class FaultSystemRuptures(graphene.ObjectType):
    fault_system = graphene.String(description="Unique ID of the fault system e.g. PUY")
    rupture_ids = graphene.List(graphene.Int)
    ruptures = graphene.ConnectionField(RuptureDetailConnection)

    def resolve_ruptures(root, info, *args, **kwargs):

        # print('resolve_ruptures', args, kwargs)

        first = kwargs.get('first') # how many to fetch
        after = kwargs.get('after')  # cursor of last page, or none

        log.info(f'resolve ruptures : first={first}, after={after}')

        cursor_offset = int(graphql_relay.from_global_id(after)[1]) if after else 0


        edges = [CompositeRuptureDetail(
                 rupture_index=rid) for rid in root.rupture_ids[cursor_offset:cursor_offset+first]]

        # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
        connection_field = relay.ConnectionField.resolve_connection(
            RuptureDetailConnection,
            {},
            edges
        )
        connection_field.total_count = len(root.rupture_ids)
        connection_field.page_info = relay.PageInfo(
            end_cursor=graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
            has_next_page=True)
        return connection_field

        # return [CompositeRuptureDetail(
        #          rupture_index=rid) for rid in root.rupture_ids[:first]]
        # return RuptureDetailConnection(
        #     # total_count=len(root.rupture_ids),
        #     cursor = 'asd',
        #     edges = [CompositeRuptureDetail(
        #         rupture_index=rid) for rid in root.rupture_ids[:first]]
        #     )


class FaultSystemSummary(graphene.ObjectType):
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    fault_traces = graphene.JSONString()
    fault_surfaces = graphene.JSONString()


class CompositeSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given composite solution or filtered solution"""

    model_id = graphene.ID()
    fault_system_ruptures = graphene.List(FaultSystemRuptures)
    location_geojson = graphene.JSONString()
    fault_system_summaries = graphene.List(FaultSystemSummary)

    # fault_sections = graphene.List(InversionSolutionFaultSection)
    # fault_sections = graphene.List(InversionSolutionRupture)
    # fault_sections_geojson = graphene.JSONString()


class CompositeSolutionAnalysisArguments(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    model_id = graphene.ID(required=True, description="The ID of the InversionSolution")
    fault_systems = graphene.List(
        graphene.String,
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

    location_area_style = GeojsonAreaStyleArguments(
        required=False,
        description="feature style for location polygons.",
        default_value=dict(
            stroke_color="lightblue", stroke_width=1, stroke_opacity=1.0, fill_color='lightblue', fill_opacity=0.7
        ),
    )


class FilterCompositeSolution(graphene.ObjectType):
    analysis = graphene.Field(CompositeSolutionAnalysis)


def fault_system_ruptures(rupture_sections_gdf, fault_systems: List[str]) -> Iterator[FaultSystemRuptures]:
    for fault_system in fault_systems:
        df0 = rupture_sections_gdf[rupture_sections_gdf.fault_system == fault_system]
        yield FaultSystemRuptures(fault_system=fault_system, rupture_ids=list(df0["Rupture Index"]))


def fault_system_summaries(
    model_id: str, rupture_sections_gdf: pd.DataFrame, fault_systems: List[str], fault_trace_style: Dict
) -> Iterator[FaultSystemSummary]:
    composite_solution = get_composite_solution(model_id)
    for fault_system in fault_systems:
        df0 = rupture_sections_gdf[rupture_sections_gdf.fault_system == fault_system]

        traces_df = composite_solution._solutions[fault_system].fault_sections_with_rates

        traces_df = traces_df[traces_df['Rupture Index'].isin(df0["Rupture Index"])]

        yield FaultSystemSummary(
            fault_system=fault_system,
            fault_traces=apply_fault_trace_style(
                geojson=json.loads(gpd.GeoDataFrame(traces_df).to_json(indent=2)), style=fault_trace_style
            ),
        )
