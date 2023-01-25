"""The main API schema."""

import json
import logging
from typing import Dict, Iterator, Tuple

import geopandas as gpd
import graphene
import shapely

# from nzshm_common.location import CodedLocation
import solvis
from nzshm_common.location.location import location_by_id
from solvis_store.solvis_db_query import matched_rupture_sections_gdf

log = logging.getLogger(__name__)

RUPTURE_SECTION_LIMIT = 1e4


def location_features(locations: Tuple[str], radius_km: int) -> Iterator[Dict]:
    for loc in locations:
        log.debug(f'LOC {loc}')
        item = location_by_id(loc)
        polygon = solvis.circle_polygon(radius_km * 1000, lat=item.get('latitude'), lon=item.get('longitude'))
        feature = dict(
            id=loc,
            type="Feature",
            geometry=shapely.geometry.mapping(polygon),
            properties={
                "title": item.get('name'),
                "stroke": "#555555",
                "stroke-opacity": 1.0,
                "stroke-width": 2,
                "fill": "#555555",
            },
        )
        yield feature


def location_features_geojson(locations: Tuple[str], radius_km: int) -> Dict:
    return dict(type="FeatureCollection", features=list(location_features(locations, radius_km)))


class InversionSolutionRupture(graphene.ObjectType):
    fault_id = graphene.Int(description="Unique ID of the rupture within this solution")
    magnitude = graphene.Float(description='rupture magnitude')


class InversionSolutionFaultSection(graphene.ObjectType):
    fault_id = graphene.String(description="Unique ID of the fault section eg WHV1")


class InversionSolutionAnalysis(graphene.ObjectType):
    """Represents the internal details of a given solution or filtered solution"""

    solution_id = graphene.ID()
    fault_sections = graphene.List(InversionSolutionFaultSection)
    ruptures = graphene.List(InversionSolutionRupture)
    geojson = graphene.JSONString()
    location_geojson = graphene.JSONString()


class InversionSolutionAnalysisArguments(graphene.InputObjectType):
    """Defines filter arguments for Inversions analysis"""

    solution_id = graphene.ID(required=True, description="The ID of the InversionSolution")
    location_codes = graphene.List(
        graphene.String,
        required=False,
        description="Optional list of locations codes for proximity filtering e.g. `WLG,PMR,ZQN`",
    )
    radius_km = graphene.Int(required=False, description='The rupture/location intersection radius in km')
    minimum_rate = graphene.Float(
        required=False, description="Constrain to ruptures having a annual rate above the value supplied."
    )
    maximum_rate = graphene.Float(
        required=False, description="Constrain to ruptures having a annual rate below the value supplied."
    )
    minimum_mag = graphene.Float(
        required=False, description="Constrain to ruptures having a magnitude above the value supplied."
    )
    maximum_mag = graphene.Float(
        required=False, description="Constrain to ruptures having a magnitude below the value supplied."
    )


class FilterInversionSolution(graphene.ObjectType):
    analysis = graphene.Field(InversionSolutionAnalysis)


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

    if section_count > RUPTURE_SECTION_LIMIT:
        raise ValueError("Too many rupture sections satisfy the filter, please try more selective values.")
    elif section_count == 0:
        raise ValueError("No ruptures satisfy the filter.")

    ruptures_geojson = json.loads(gpd.GeoDataFrame(rupture_sections_gdf).to_json(indent=2))
    return FilterInversionSolution(
        analysis=InversionSolutionAnalysis(
            geojson=ruptures_geojson,
            location_geojson=location_features_geojson(tuple(input['location_codes']), input['radius_km']),
        )
    )
