"""The API schema for conposite solutions."""

import logging
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, List, Set, Tuple, Union

import geopandas as gpd
import nzshm_model
import solvis
from nzshm_common.location.location import location_by_id
from solvis.inversion_solution.typing import InversionSolutionProtocol
from solvis_store.config import DEPLOYMENT_STAGE
from solvis_store.solvis_db_query import get_rupture_ids

from .filter_set_logic_options import SetOperationEnum

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4

RESOLVE_LOCATIONS_INTERNALLY = False if DEPLOYMENT_STAGE == 'TEST' else True


@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return solvis.geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


# TODO: this is here temporarily until we can get solvis published (GHA problems)
@lru_cache
def parent_fault_names(
    sol: InversionSolutionProtocol, sort: Union[None, Callable[[Iterable], List]] = sorted
) -> List[str]:
    if sort:
        return sort(sol.fault_sections.ParentName.unique())
    return list(sol.fault_sections.ParentName.unique())


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


def filter_dataframe_by_radius(
    fault_system_solution, location_ids, radius_km, filter_set_options: Tuple[Any]
)  -> Set[int]:
    log.info('filter_dataframe_by_radius: %s %s %s' % (fault_system_solution, radius_km, location_ids))
    filter_set_options_dict = dict(filter_set_options)
    first = True
    rupture_ids: Set[int]
    for loc_id in location_ids:
        loc = location_by_id(loc_id)
        # print("LOC:", loc)
        polygon = get_location_polygon(radius_km=radius_km, lon=loc['longitude'], lat=loc['latitude'])
        location_rupture_ids = set(fault_system_solution.get_ruptures_intersecting(polygon))

        if first:
            rupture_ids = location_rupture_ids
            first = False
        else:
            log.debug(
                'filter_set_options_dict["multiple_locations"] %s' % filter_set_options_dict["multiple_locations"]
            )
            if filter_set_options_dict["multiple_locations"] == SetOperationEnum.INTERSECTION:
                rupture_ids = rupture_ids.intersection(location_rupture_ids)
            elif filter_set_options_dict["multiple_locations"] == SetOperationEnum.UNION:
                rupture_ids = rupture_ids.union(location_rupture_ids)
            else:
                raise ValueError("unsupported SetOperation")
    return rupture_ids

def filter_dataframe_by_radius_stored(model_id: str, fault_system: str, location_ids: List[str], radius_km: int, filter_set_options: Tuple[Any]) -> Iterator[int]:
    log.info('filter_dataframe_by_radius_stored: %s %s %s %s' % (model_id, fault_system, radius_km, location_ids))
    current_model = nzshm_model.get_model_version(model_id)
    slt = current_model.source_logic_tree()

    filter_set_options_dict = dict(filter_set_options)

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
    union = False if filter_set_options_dict["multiple_locations"] == SetOperationEnum.INTERSECTION else True
    print("filter_dataframe_by_radius_stored", radius_km)
    return get_rupture_ids(rupture_set_id=rupture_set_id, locations=location_ids, radius=radius_km, union=union)

@lru_cache
def get_rupture_ids_for_parent_fault(fault_system_solution: InversionSolutionProtocol, fault_name: str) -> Set[int]:
    return set(fault_system_solution.get_ruptures_for_parent_fault(fault_name))


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
    filter_set_options: Tuple[Any],
    union: bool = False,
    corupture_fault_names: Union[None, Tuple[str]] = None,
) -> gpd.GeoDataFrame:
    """
    Query the solvis.CompositeSolution instance identified by model ID.

    return a dataframe of the matched ruptures.
    """
    log.debug('matched_rupture_sections_gdf()  filter_set_options: %s' % filter_set_options)
    filter_set_options_dict = dict(filter_set_options)

    tic0 = time.perf_counter()
    composite_solution = get_composite_solution(model_id)

    fss = composite_solution._solutions[fault_system]
    tic1 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time to load fault system solution: %2.3f seconds' % (tic1 - tic0))

    df0 = fss.ruptures_with_rates

    # attribute filters
    df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
    df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
    df0 = df0 if not max_rate else df0[df0.rate_weighted_mean <= max_rate]
    df0 = df0 if not min_rate else df0[df0.rate_weighted_mean > min_rate]

    tic2 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time apply attribute filters: %2.3f seconds' % (tic2 - tic1))

    # co-rupture filter
    if corupture_fault_names and len(corupture_fault_names):
        first = True
        rupture_ids: Set[int]
        for fault_name in corupture_fault_names:
            if fault_name not in parent_fault_names(fss):
                raise ValueError("Invalid fault name: %s" % fault_name)
            tic22 = time.perf_counter()
            fault_rupture_ids = get_rupture_ids_for_parent_fault(fss, fault_name)
            tic23 = time.perf_counter()
            log.debug('fss.get_ruptures_for_parent_fault %s: %2.3f seconds' % (fault_name, (tic23 - tic22)))

            if first:
                rupture_ids = fault_rupture_ids
                first = False
            else:
                log.debug('filter_set_options_dict["multiple_faults"] %s' % filter_set_options_dict["multiple_faults"])
                if filter_set_options_dict["multiple_faults"] == SetOperationEnum.INTERSECTION:
                    rupture_ids = rupture_ids.intersection(fault_rupture_ids)
                elif filter_set_options_dict["multiple_faults"] == SetOperationEnum.UNION:
                    rupture_ids = rupture_ids.union(fault_rupture_ids)
                else:
                    raise ValueError("AWHAAA")

        df0 = df0[df0["Rupture Index"].isin(list(rupture_ids))]

    tic3 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time apply co-rupture filter: %2.3f seconds' % (tic3 - tic2))

    # location filters
    if location_ids is not None and len(location_ids):
        if RESOLVE_LOCATIONS_INTERNALLY:
            rupture_ids = set( filter_dataframe_by_radius(fss, location_ids, radius_km, filter_set_options))
        else:
            rupture_ids = set(
                filter_dataframe_by_radius_stored(model_id, fault_system, location_ids, radius_km, filter_set_options)
            )
        df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

    tic4 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time apply location filters: %2.3f seconds' % (tic4 - tic3))

    return df0


@lru_cache
def fault_section_aggregates_gdf(
    model_id: str,
    fault_system: str,
    location_ids: Tuple[str],
    radius_km: int,
    min_rate: float,
    max_rate: float,
    min_mag: float,
    max_mag: float,
    filter_set_options: Tuple[Any],
    union: bool = False,
    trace_only: bool = False,
    corupture_fault_names: Union[None, Tuple[str]] = None,
) -> gpd.GeoDataFrame:

    tic0 = time.perf_counter()
    composite_solution = get_composite_solution(model_id)
    fss = composite_solution._solutions[fault_system]

    tic1 = time.perf_counter()
    log.debug('fault_section_aggregates_gdf(): time to load fault system solution: %2.3f seconds' % (tic1 - tic0))

    df0 = matched_rupture_sections_gdf(
        model_id,
        fault_system,
        location_ids,
        radius_km,
        min_rate,
        max_rate,
        min_mag,
        max_mag,
        filter_set_options,
        union,
        corupture_fault_names,
    )

    tic2 = time.perf_counter()
    log.debug('fault_section_aggregates_gdf(): time to filter rupture sections: %2.3f seconds' % (tic2 - tic1))

    fsr = fss.fault_sections_with_rates
    fsr = fsr[fsr['Rupture Index'].isin(df0['Rupture Index'].unique())]

    tic3 = time.perf_counter()
    log.debug('fault_section_aggregates_gdf(): time to filter fault sections: %2.3f seconds' % (tic3 - tic2))

    section_aggregates = fsr.pivot_table(
        index=['section'],
        aggfunc=dict(rate_weighted_mean=['sum', 'min', 'max', 'mean'], Magnitude=['count', 'min', 'max', 'mean']),
    )

    tic4 = time.perf_counter()
    log.debug('fault_section_aggregates_gdf(): time to aggregate fault sections: %2.3f seconds' % (tic4 - tic3))

    section_aggregates.columns = [".".join(a) for a in section_aggregates.columns.to_flat_index()]

    if trace_only:
        rupture_sections_gdf = gpd.GeoDataFrame(
            section_aggregates.join(fss.fault_sections, 'section', how='inner', rsuffix='_R')
        )
    else:
        # if fault_surfaces ...
        section_aggregates_detail = section_aggregates.join(fss.fault_surfaces(), 'section', how='inner', rsuffix='_R')
        rupture_sections_gdf = gpd.GeoDataFrame(section_aggregates_detail)
        tic5 = time.perf_counter()
        log.debug('fault_section_aggregates_gdf(): time to build fault surfaces: %2.3f seconds' % (tic5 - tic4))

    section_count = rupture_sections_gdf.shape[0] if rupture_sections_gdf is not None else 0
    if section_count == 0:
        raise ValueError("No fault sections satisfy the filter.")

    return rupture_sections_gdf
