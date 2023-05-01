"""The API schema for conposite solutions."""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Iterator, Tuple

import geopandas as gpd
import nzshm_model
import solvis
from nzshm_common.location.location import location_by_id
from solvis_store.config import DEPLOYMENT_STAGE
from solvis_store.solvis_db_query import get_rupture_ids

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4

RESOLVE_LOCATIONS_INTERNALLY = False if DEPLOYMENT_STAGE == 'TEST' else True


@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return solvis.geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


@lru_cache
def get_composite_solution(model_id: str) -> solvis.CompositeSolution:

    # print(model_id)
    log.info('get_composite_solution: %s' % model_id)
    assert nzshm_model.get_model_version(model_id) is not None
    slt = nzshm_model.get_model_version(model_id).source_logic_tree()

    # needed for local testing only, so we can move ZIP file out of inotify scope
    # so it doesn't cause reloading loop on wsgi_serve
    COMPOSITE_ARCHIVE_PATH = os.getenv('COMPOSITE_ARCHIVE_PATH')

    if COMPOSITE_ARCHIVE_PATH is None:
        folder = Path(os.path.realpath(__file__)).parent
        COMPOSITE_ARCHIVE_PATH = str(Path(folder, "NSHM_v1.0.4_CompositeSolution.zip"))
        log.warning("Loading DEFAULT composite solution: %s" % COMPOSITE_ARCHIVE_PATH)
    else:
        log.info("Loading composite solution: %s" % COMPOSITE_ARCHIVE_PATH)
    return solvis.CompositeSolution.from_archive(Path(COMPOSITE_ARCHIVE_PATH), slt)


def filter_dataframe_by_radius(fault_system_solution, dataframe, location_ids, radius_km):
    log.info('filter_dataframe_by_radius: %s %s %s' % (fault_system_solution, radius_km, location_ids))
    rupture_ids = set()
    for loc_id in location_ids:
        loc = location_by_id(loc_id)
        # print("LOC:", loc)
        polygon = get_location_polygon(radius_km=radius_km, lon=loc['longitude'], lat=loc['latitude'])
        rupture_ids = rupture_ids.union(set(fault_system_solution.get_ruptures_intersecting(polygon)))
        # print(fault_system, len(rupture_ids))
    # print('rupture_ids', rupture_ids)
    return dataframe[dataframe["Rupture Index"].isin(rupture_ids)]


def filter_dataframe_by_radius_stored(model_id, fault_system, df0, location_ids, radius_km, union) -> Iterator[int]:
    log.info('filter_dataframe_by_radius_stored: %s %s %s %s' % (model_id, fault_system, radius_km, location_ids))
    current_model = nzshm_model.get_model_version(model_id)
    slt = current_model.source_logic_tree()

    def get_fss(slt, fault_system):
        for fss in slt.fault_system_lts:
            if fss.short_name == fault_system:
                return fss

    # check the solutions in a given fault system have the same rupture_set
    fss = get_fss(slt, fault_system)
    assert fss is not None

    ruptset_ids = list(set([branch.rupture_set_id for branch in fss.branches]))
    assert len(ruptset_ids) == 1
    rupture_set_id = ruptset_ids[0]

    print("filter_dataframe_by_radius_stored", radius_km)
    return get_rupture_ids(rupture_set_id=rupture_set_id, locations=location_ids, radius=radius_km, union=union)


@lru_cache
def matched_rupture_sections_gdf(
    model_id: str,
    fault_system: str,
    location_ids: Tuple[str],
    radius_km: int,
    min_rate: float,
    max_rate: float,
    min_mag: float,
    max_mag: float,
    union: bool = False,
) -> gpd.GeoDataFrame:
    """
    Query the solvis.CompositeSolution instance identified by model ID.

    return a dataframe of the matched ruptures.
    """

    composite_solution = get_composite_solution(model_id)

    fss = composite_solution._solutions[fault_system]
    df0 = fss.ruptures_with_rates

    # attribute filters
    df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
    df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
    df0 = df0 if not max_rate else df0[df0.rate_weighted_mean <= max_rate]
    df0 = df0 if not min_rate else df0[df0.rate_weighted_mean > min_rate]

    # location filters
    if location_ids is not None and len(location_ids):
        if RESOLVE_LOCATIONS_INTERNALLY:
            df0 = filter_dataframe_by_radius(fss, df0, location_ids, radius_km)
        else:
            rupture_ids = list(
                filter_dataframe_by_radius_stored(model_id, fault_system, df0, location_ids, radius_km, union)
            )
            df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

    return df0
