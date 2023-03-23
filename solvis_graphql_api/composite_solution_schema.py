"""The API schema for conposite solutions."""

import json
import logging
from typing import Dict, Iterator, Tuple, List
import os

import geopandas as gpd
import graphene
import pandas as pd
import shapely
import solvis
from nzshm_common.location.location import location_by_id
from functools import lru_cache

# from solvis import CompositeSolution
from pathlib import Path
import nzshm_model as nm

# from solvis_store.solvis_db_query import matched_rupture_sections_gdf

from .solution_schema import GeojsonLineStyleArguments, GeojsonAreaStyleArguments
from .solution_schema import apply_fault_trace_style, location_features_geojson, get_location_polygon

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4

class FaultSystemRuptures(graphene.ObjectType):
    fault_system = graphene.String(description="Unique ID of the fault system e.g. PUY")
    rupture_ids = graphene.List(graphene.Int)

class FaultSystemGeojson(graphene.ObjectType):
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    fault_traces = graphene.JSONString()
    fault_surfaces = graphene.JSONString()

class CompositeSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given composite solution or filtered solution"""

    model_id = graphene.ID()
    fault_system_ruptures = graphene.List(FaultSystemRuptures)
    location_geojson = graphene.JSONString()
    fault_system_geojson = graphene.List(FaultSystemGeojson)

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



@lru_cache
def get_composite_solution(model_id:str) -> solvis.CompositeSolution:
    assert nm.get_model_version(model_id)
    slt = nm.get_model_version(model_id).source_logic_tree()
    folder = Path("/home/chrisbc", 'SCRATCH')
    return solvis.CompositeSolution.from_archive(Path(folder, "NewCompositeSolution.zip"), slt)


@lru_cache
def matched_rupture_sections_gdf(model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union):
    """
    Query the solvis.CompositeSolution instance identified by model ID.


    This uses a CompositeSolution instance loaded from archive file, so location tests are slowed considerably compared to
    solvis_store query approach.

    return a dataframe of the rupture ids by fault_system.
    """

    def filter_solution(model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union):
        rupture_rates_df = None

        composite_solution = get_composite_solution(model_id)

        for fault_system in fault_systems:
            fss = composite_solution._solutions[fault_system]
            df0 = fss.ruptures_with_rates

            # attribute filters
            df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
            df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
            df0 = df0 if not max_rate else df0[df0.rate_weighted_mean <= max_rate]
            df0 = df0 if not min_rate else df0[df0.rate_weighted_mean > min_rate]

            # location filters
            if location_codes:
                rupture_ids = set()
                for loc_code in location_codes.split(','):
                    loc = location_by_id(loc_code)
                    # print(loc)
                    polygon = get_location_polygon(radius_km=radius_km, lon=loc['longitude'], lat=loc['latitude'])
                    rupture_ids = rupture_ids.union(set(fss.get_ruptures_intersecting(polygon)))
                    # print(fault_system, len(rupture_ids))
                # print('rupture_ids', rupture_ids)
                df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

            rupture_rates_df = df0 if rupture_rates_df is None else pd.concat([rupture_rates_df, df0], ignore_index=True)

        return rupture_rates_df

    df = filter_solution(model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union)

    return df


def fault_system_ruptures(rupture_sections_gdf, fault_systems: List[str]) -> Iterator[FaultSystemRuptures]:
    for fault_system in fault_systems:
        df0 = rupture_sections_gdf[rupture_sections_gdf.fault_system == fault_system]
        yield FaultSystemRuptures(
            fault_system = fault_system,
            rupture_ids = list(df0["Rupture Index"]))

def fault_system_geojson(model_id: str, rupture_sections_gdf:pd.DataFrame, fault_systems: List[str], fault_trace_style:Dict) -> Iterator[str]:
    composite_solution = get_composite_solution(model_id)
    for fault_system in fault_systems:
        df0 = rupture_sections_gdf[rupture_sections_gdf.fault_system == fault_system]


        traces_df = composite_solution._solutions[fault_system].fault_sections_with_rates

        traces_df = traces_df[traces_df['Rupture Index'].isin(df0["Rupture Index"])]

        yield  FaultSystemGeojson(
            fault_system = fault_system,
            fault_traces = apply_fault_trace_style(
                geojson=json.loads(gpd.GeoDataFrame(traces_df).to_json(indent=2)),
                style=fault_trace_style)
                )



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
        union=False
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
            fault_system_ruptures = fault_system_ruptures(rupture_sections_gdf, input['fault_systems']),
            fault_system_geojson = fault_system_geojson(
                input['model_id'],
                rupture_sections_gdf,
                fault_systems= input['fault_systems'],
                fault_trace_style= input.get('fault_trace_style')
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
