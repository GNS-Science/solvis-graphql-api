"""The main API schema."""

import json
import logging
from functools import lru_cache
from typing import Dict, Iterator, Tuple

import geopandas as gpd
import graphene
import shapely
import solvis
from nzshm_common.location.location import location_by_id

# from solvis_store.solvis_db_query import matched_rupture_sections_gdf
from solvis_graphql_api.composite_solution.cached import matched_rupture_sections_gdf
from solvis_graphql_api.geojson_style import (
    GeojsonAreaStyleArgumentsInput,
    GeojsonLineStyleArgumentsInput,
    apply_geojson_style,
)

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return solvis.geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


def location_features(
    locations: Tuple[str], radius_km: int, style: Dict
) -> Iterator[Dict]:
    for loc in locations:
        log.debug(f"LOC {loc}")
        item = location_by_id(loc)
        # polygon = solvis.circle_polygon(radius_km * 1000, lat=item.get('latitude'), lon=item.get('longitude'))
        polygon = get_location_polygon(
            radius_km, lat=item.get("latitude"), lon=item.get("longitude")
        )
        feature = dict(
            id=loc,
            type="Feature",
            geometry=shapely.geometry.mapping(polygon),
            properties={
                "title": item.get("name"),
                "stroke-color": style.get("stroke_color"),
                "stroke-opacity": style.get("stroke_opacity"),
                "stroke-width": style.get("stroke_width"),
                "fill-color": style.get("fill_color"),
                "fill-opacity": style.get("fill_opacity"),
            },
        )
        yield feature


def location_features_geojson(
    locations: Tuple[str], radius_km: int, style: Dict
) -> Dict:
    return dict(
        type="FeatureCollection",
        features=list(location_features(locations, radius_km, style)),
    )


# class InversionSolutionRupture(graphene.ObjectType):
#     fault_id = graphene.Int(description="Unique ID of the rupture within this solution")
#     magnitude = graphene.Float(description='rupture magnitude')

# class InversionSolutionFaultSection(graphene.ObjectType):
#     fault_id = graphene.String(description="Unique ID of the fault section eg WHV1")


class InversionSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given solution or filtered solution"""

    solution_id = graphene.ID()
    fault_sections_geojson = graphene.JSONString()
    location_geojson = graphene.JSONString()


class InversionSolutionAnalysisArguments(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    solution_id = graphene.ID(
        required=True, description="The ID of the InversionSolution"
    )
    location_ids = graphene.List(
        graphene.String,
        required=False,
        default_value=[],
        description="Optional list of locations codes for proximity filtering e.g. `WLG,PMR,ZQN`",
    )
    radius_km = graphene.Int(
        required=False, description="The rupture/location intersection radius in km"
    )
    minimum_rate = graphene.Float(
        required=False,
        description="Constrain to fault_sections having a annual rate above the value supplied.",
    )
    maximum_rate = graphene.Float(
        required=False,
        description="Constrain to fault_sections having a annual rate below the value supplied.",
    )
    minimum_mag = graphene.Float(
        required=False,
        description="Constrain to fault_sections having a magnitude above the value supplied.",
    )
    maximum_mag = graphene.Float(
        required=False,
        description="Constrain to fault_sections having a magnitude below the value supplied.",
    )

    fault_trace_style = GeojsonLineStyleArgumentsInput(
        required=False,
        description="feature style for rupture trace geojson.",
        default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
    )

    location_area_style = GeojsonAreaStyleArgumentsInput(
        required=False,
        description="feature style for location polygons.",
        default_value=dict(
            stroke_color="lightblue",
            stroke_width=1,
            stroke_opacity=1.0,
            fill_color="lightblue",
            fill_opacity=0.7,
        ),
    )


class FilterInversionSolution(graphene.ObjectType):
    analysis = graphene.Field(InversionSolutionAnalysis)


def get_inversion_solution(input, **args):
    log.info("analyse_solution args: %s input:%s" % (args, input))
    rupture_sections_gdf = matched_rupture_sections_gdf(  # noqa
        input["solution_id"],
        ",".join(input["location_ids"]),  # convert to string
        input["radius_km"] * 1000,
        min_rate=input.get("minimum_rate") or 1e-20,
        max_rate=input.get("maximum_rate"),
        min_mag=input.get("minimum_mag"),
        max_mag=input.get("maximum_mag"),
    )
    section_count = (
        rupture_sections_gdf.shape[0] if rupture_sections_gdf is not None else 0
    )
    log.info(
        "rupture_sections_gdf %s has %s sections"
        % (rupture_sections_gdf, section_count)
    )

    if section_count > FAULT_SECTION_LIMIT:
        raise ValueError(
            "Too many fault sections satisfy the filter, please try more selective values."
        )
    elif section_count == 0:
        raise ValueError("No fault sections satisfy the filter.")

    print(rupture_sections_gdf)

    return FilterInversionSolution(
        analysis=InversionSolutionAnalysis(
            solution_id=input["solution_id"],
            fault_sections_geojson=apply_geojson_style(
                geojson=json.loads(
                    gpd.GeoDataFrame(rupture_sections_gdf).to_json(indent=2)
                ),
                style=input.get("fault_trace_style"),
            ),
            location_geojson=location_features_geojson(
                tuple(input["location_ids"]),
                input["radius_km"],
                style=input.get("location_area_style"),
            ),
        )
    )
