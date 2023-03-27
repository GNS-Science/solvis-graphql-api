"""The API schema for conposite solutions."""

import json
import logging
import os

from .helpers import matched_rupture_sections_gdf, get_composite_solution
from .composite_solution_schema import (
    FilterCompositeSolution,
    CompositeSolutionAnalysis,
    fault_system_ruptures,
    fault_system_summaries,
)
from .composite_rupture_detail import CompositeRuptureDetail

from solvis_graphql_api.solution_schema import (
    apply_fault_trace_style,
    location_features_geojson,
)

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
            fault_system_ruptures=fault_system_ruptures(rupture_sections_gdf, input['fault_systems']),
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
