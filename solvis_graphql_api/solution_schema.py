"""The main API schema."""

import json
import logging
from typing import Dict, Iterator, Tuple

import geopandas as gpd
import graphene
import shapely
import solvis
from functools import lru_cache
from nzshm_common.location.location import location_by_id
from solvis_store.solvis_db_query import matched_rupture_sections_gdf

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4

@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return solvis.geometry.circle_polygon(radius_m=radius_km*1000, lon=lon, lat=lat)

def location_features(locations: Tuple[str], radius_km: int, style: Dict) -> Iterator[Dict]:
    for loc in locations:
        log.debug(f'LOC {loc}')
        item = location_by_id(loc)
        # polygon = solvis.circle_polygon(radius_km * 1000, lat=item.get('latitude'), lon=item.get('longitude'))
        polygon = get_location_polygon(radius_km, lat=item.get('latitude'), lon=item.get('longitude'))
        feature = dict(
            id=loc,
            type="Feature",
            geometry=shapely.geometry.mapping(polygon),
            properties={
                "title": item.get('name'),
                "stroke-color": style.get('stroke_color'),
                "stroke-opacity": style.get('stroke_opacity'),
                "stroke-width": style.get('stroke_width'),
                "fill-color": style.get('fill_color'),
                "fill-opacity": style.get('fill_opacity'),
            },
        )
        yield feature

def location_features_geojson(locations: Tuple[str], radius_km: int, style: Dict) -> Dict:
    return dict(type="FeatureCollection", features=list(location_features(locations, radius_km, style)))


# class InversionSolutionRupture(graphene.ObjectType):
#     fault_id = graphene.Int(description="Unique ID of the rupture within this solution")
#     magnitude = graphene.Float(description='rupture magnitude')

# class InversionSolutionFaultSection(graphene.ObjectType):
#     fault_id = graphene.String(description="Unique ID of the fault section eg WHV1")


class InversionSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given solution or filtered solution"""

    solution_id = graphene.ID()
    # fault_sections = graphene.List(InversionSolutionFaultSection)
    # fault_sections = graphene.List(InversionSolutionRupture)
    fault_sections_geojson = graphene.JSONString()
    location_geojson = graphene.JSONString()


class GeojsonLineStyleArguments(graphene.InputObjectType):
    """Defines styling arguments for geojson features,

    ref https://academy.datawrapper.de/article/177-how-to-style-your-markers-before-importing-them-to-datawrapper"""

    stroke_color = graphene.String(
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")'
    )
    stroke_width = graphene.Int(description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(description="a number between 0 and 1.0")


class GeojsonAreaStyleArguments(graphene.InputObjectType):
    """Defines styling arguments for geojson features,
    ref https://academy.datawrapper.de/article/177-how-to-style-your-markers-before-importing-them-to-datawrapper"""

    stroke_color = graphene.String(
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")'
    )
    stroke_width = graphene.Int(description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(description="a number between 0 and 1.0")
    fill_color = graphene.String(
        description='fill colour as Hex code ("#cc0000") or HTML color names ("royalblue") )', default_value='green'
    )
    fill_opacity = graphene.Float(description="0-1.0", default_value=1.0)


class InversionSolutionAnalysisArguments(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    solution_id = graphene.ID(required=True, description="The ID of the InversionSolution")
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


class FilterInversionSolution(graphene.ObjectType):
    analysis = graphene.Field(InversionSolutionAnalysis)


def apply_fault_trace_style(geojson: Dict, style: Dict) -> Dict:
    """ "merge each features properties dict with style dict"""
    new_dict = dict(geojson)
    for feature in new_dict['features']:
        current_props = feature.get("properties", {})
        feature['properties'] = {
            **current_props,
            **{
                "stroke-color": style.get('stroke_color'),
                "stroke-opacity": style.get('stroke_opacity'),
                "stroke-width": style.get('stroke_width'),
            },
        }
    return new_dict


def analyse_solution(input, **args):
    log.info('analyse_solution args: %s input:%s' % (args, input))
    rupture_sections_gdf = matched_rupture_sections_gdf(
        input['solution_id'],
        ','.join(input['location_codes']),  # convert to string
        input['radius_km'] * 1000,
        min_rate=input.get('minimum_rate') or 1e-20,
        max_rate=input.get('maximum_rate'),
        min_mag=input.get('minimum_mag'),
        max_mag=input.get('maximum_mag'),
    )
    section_count = rupture_sections_gdf.shape[0] if rupture_sections_gdf is not None else 0
    log.info('rupture_sections_gdf %s has %s sections' % (rupture_sections_gdf, section_count))

    if section_count > FAULT_SECTION_LIMIT:
        raise ValueError("Too many fault sections satisfy the filter, please try more selective values.")
    elif section_count == 0:
        raise ValueError("No fault sections satisfy the filter.")

    print(rupture_sections_gdf)

    return FilterInversionSolution(
        analysis=InversionSolutionAnalysis(
            solution_id=input['solution_id'],
            fault_sections_geojson=apply_fault_trace_style(
                geojson=json.loads(gpd.GeoDataFrame(rupture_sections_gdf).to_json(indent=2)),
                style=input.get('fault_trace_style'),
            ),
            location_geojson=location_features_geojson(
                tuple(input['location_codes']), input['radius_km'], style=input.get('location_area_style')
            ),
        )
    )
