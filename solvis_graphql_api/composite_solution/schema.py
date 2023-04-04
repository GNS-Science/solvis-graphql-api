"""The API schema for conposite solutions."""

import json
import logging
import graphql_relay
import graphene
from graphene import relay
import geopandas as gpd

from solvis_graphql_api.solution_schema import apply_fault_trace_style, location_features_geojson

from .composite_rupture_detail import CompositeRuptureDetail
from .composite_solution_schema import (
    CompositeSolutionAnalysis,
    FilterCompositeSolution,
    RuptureDetailConnection,
    fault_system_ruptures,
    fault_system_summaries,
)
from .helpers import get_composite_solution, matched_rupture_sections_gdf

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4

def analyse_composite_solution(input, **args):
    log.info('analyse_composite_solution args: %s input:%s' % (args, input))
    rupture_sections_gdf = matched_rupture_sections_gdf(
        input['model_id'],
        tuple(input['fault_systems']),
        ','.join(input['location_codes']),  # convert to string
        input['radius_km'],
        min_rate=input.get('minimum_rate') or 1e-20,
        max_rate=input.get('maximum_rate'),
        min_mag=input.get('minimum_mag'),
        max_mag=input.get('maximum_mag'),
        union=False,
    )

    section_count = rupture_sections_gdf.shape[0] if rupture_sections_gdf is not None else 0
    log.info('rupture_sections_gdf has %s sections' % (section_count))

    if section_count > FAULT_SECTION_LIMIT:
        raise ValueError("Too many fault sections satisfy the filter, please try more selective values.")
    elif section_count == 0:
        raise ValueError("No fault sections satisfy the filter.")

    return FilterCompositeSolution(
        analysis=CompositeSolutionAnalysis(
            model_id=input['model_id'],
            fault_system_ruptures=fault_system_ruptures(
                rupture_sections_gdf, model_id=input['model_id'], fault_systems=input['fault_systems']
            ),
            fault_system_summaries=fault_system_summaries(
                input['model_id'],
                rupture_sections_gdf,
                fault_systems=input['fault_systems'],
                fault_trace_style=input.get('fault_trace_style'),
            ),
            # fault_sections_geojson=apply_fault_trace_style(
            #     geojson=json.loads(gpd.GeoDataFrame(rupture_sections_gdf).to_json(indent=2)),
            #     style=input.get('fault_trace_style'),
            # ),
            location_geojson=location_features_geojson(
                tuple(input['location_codes']), input['radius_km'], style=input.get('location_area_style')
            ),
        )
    )


def composite_rupture_detail(input, **args):
    log.info('composite_rupture_detail args: %s input:%s' % (args, input))

    model_id = input['model_id'].strip()
    fault_system = input['fault_system']
    rupture_index = input['rupture_index']
    fault_trace_style = input['fault_trace_style']

    composite_solution = get_composite_solution(model_id)

    rupture_surface = composite_solution._solutions[fault_system].rupture_surface(rupture_index)  #
    return CompositeRuptureDetail(
        model_id=model_id,
        fault_system=fault_system,
        rupture_index=rupture_index,
        fault_surfaces=apply_fault_trace_style(
            geojson=json.loads(rupture_surface.to_json(indent=2)), style=fault_trace_style
        ),
    )


def paginated_filtered_ruptures(input, **kwargs) -> RuptureDetailConnection:
    ### query that accepts both the rupture filter args and the pagination args

    log.info('paginated_ruptures args: %s input:%s' % (kwargs, input))

    rupture_sections_gdf = matched_rupture_sections_gdf(
        input['model_id'],
        tuple(input['fault_systems']),
        ','.join(input['location_codes']),  # convert to string
        input['radius_km'],
        min_rate=input.get('minimum_rate') or 1e-20,
        max_rate=input.get('maximum_rate'),
        min_mag=input.get('minimum_mag'),
        max_mag=input.get('maximum_mag'),
        union=False,
    )
    first = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none
    log.info(f'resolve ruptures : first={first}, after={after}')

    return build_ruptures_connection(rupture_sections_gdf, model_id=input['model_id'], fault_system=input['fault_systems'][0], first=first, after=after)

def build_ruptures_connection(rupture_sections_gdf: gpd.GeoDataFrame, model_id:str, fault_system:str, first: int, after: graphene.ID = None):
    # stolen from FaultSystemRuptures resolver....

    cursor_offset = int(graphql_relay.from_global_id(after)[1]) + 1 if after else 0

    rupture_ids=list(rupture_sections_gdf["Rupture Index"])
    nodes = [
        CompositeRuptureDetail(model_id=model_id, fault_system=fault_system, rupture_index=rid)
        for rid in rupture_ids[cursor_offset : cursor_offset + first]
    ]

    print(nodes)
    # based on https://gist.github.com/AndrewIngram/b1a6e66ce92d2d0befd2f2f65eb62ca5#file-pagination-py-L152
    edges = [
        RuptureDetailConnection.Edge(
            node=node, cursor=graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset + idx))
        )
        for idx, node in enumerate(nodes)
    ]

    # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
    connection_field = relay.ConnectionField.resolve_connection(RuptureDetailConnection, {}, edges)

    total_count = len(rupture_ids)
    has_next = total_count > 1 + int(graphql_relay.from_global_id(edges[-1].cursor)[1]) if edges else False

    # print(int(graphql_relay.from_global_id(edges[-1].cursor)[1]), total_count, has_next )

    connection_field.total_count = total_count
    connection_field.page_info = relay.PageInfo(
        end_cursor=edges[-1].cursor
        if edges
        else None,  # graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
        has_next_page=has_next,
    )
    connection_field.edges = edges
    return connection_field



