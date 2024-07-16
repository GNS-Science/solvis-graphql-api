"""The cached functions for CompositeSolutions"""

import io
import logging
import time
import warnings
from functools import lru_cache

# from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Iterable, List, Set, Tuple, Union

import geopandas as gpd
import nzshm_model
import solvis
from solvis.inversion_solution.typing import InversionSolutionProtocol

from data_store import model

from .filter_set_logic_options import _solvis_join

if TYPE_CHECKING:
    import shapely.geometry.polygon.Polygon
    from nzshm_model.source_logic_tree.logic_tree import SourceLogicTree
    from solvis.inversion_solution.typing import ModelLogicTreeBranch

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


@lru_cache
def get_location_polygon(radius_km: float, lon: float, lat: float) -> "shapely.geometry.polygon.Polygon":
    return solvis.geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


@lru_cache
def parent_fault_names(
    sol: InversionSolutionProtocol, sort: Union[None, Callable[[Iterable[str]], Iterable[str]]] = sorted
) -> List[str]:
    fault_names: List[str] = solvis.parent_fault_names(sol, sort)
    return fault_names


@lru_cache
def get_composite_solution(model_id: str) -> solvis.CompositeSolution:
    """
    Return a composite solution for the given model_id

    CompositeSolution zip file are stored/retrieved via the BinaryLargeObject class.
    """
    log.info('get_composite_solution: %s' % model_id)
    assert nzshm_model.get_model_version(model_id) is not None
    slt = nzshm_model.get_model_version(model_id).source_logic_tree
    blob = model.BinaryLargeObject.get(object_type="CompositeSolution", object_id=model_id)
    return solvis.CompositeSolution.from_archive(io.BytesIO(blob.object_blob), slt)


def get_branch_rupture_set_id(branch: 'ModelLogicTreeBranch') -> str:
    """
    Return a single rupture_set_id from an NZSHM Model logic tree branch (v1 or v2).
    Note:
        This distinction may go away in future versions, simplifying this issue:
        https://github.com/GNS-Science/nzshm-model/issues/81
    """
    for source in branch.sources:
        if isinstance(branch, nzshm_model.logic_tree.source_logic_tree.version2.logic_tree.Branch):
            # NZSHM Model 0.6: v2 branches take inversion ID from first InversionSource
            if source.type == "inversion":
                rupture_set_id = source.rupture_set_id
                break
            else:
                raise Exception("Could not find inversion solution ID for branch solution")
        else:
            # Fall back to v1 behaviour
            rupture_set_id = branch.rupture_set_id

    return rupture_set_id


def get_fault_system_solution_for_model(
    model_id: str, fault_system: str
) -> "nzshm_model.source_logic_tree.logic_tree.FaultSystemLogicTree":
    current_model = nzshm_model.get_model_version(model_id)
    slt = current_model.source_logic_tree

    def get_fss(
        slt: "SourceLogicTree", fault_system: str
    ) -> "nzshm_model.source_logic_tree.logic_tree.FaultSystemLogicTree":
        for fss in slt.fault_system_lts:
            if fss.short_name == fault_system:
                return fss

    # check the solutions in a given fault system have the same rupture_set
    fss = get_fss(slt, fault_system)
    assert fss is not None
    return fss


def get_rupture_ids_for_location_radius(
    fault_system_solution: InversionSolutionProtocol,
    location_ids: Iterable[str],
    radius_km: float,
    filter_set_options: Tuple[Any],
) -> Set[int]:
    """DEPRECATED: Now a redirect for fss.get_rupture_ids_for_location_radius."""
    warnings.warn(
        "Function moved: Use solvis InversionSolutionOperations.get_rupture_ids_for_location_radius method instead",
        DeprecationWarning,
    )
    location_join_type = _solvis_join(filter_set_options, "multiple_locations")
    return fault_system_solution.get_rupture_ids_for_location_radius(location_ids, radius_km, location_join_type)


@lru_cache
def get_rupture_ids_for_parent_fault(fault_system_solution: InversionSolutionProtocol, fault_name: str) -> Set[int]:
    return set(fault_system_solution.get_rupture_ids_for_parent_fault(fault_name))


def get_rupture_ids_for_fault_names(
    fault_system_solution: InversionSolutionProtocol,
    corupture_fault_names: Iterable[str],
    filter_set_options: Tuple[Any],
) -> Set[int]:
    """DEPRECATED: Now a redirect for fss.get_rupture_ids_for_fault_names."""
    warnings.warn(
        "Function moved: Use solvis InversionSolutionOperations.get_rupture_ids_for_fault_names method instead",
        DeprecationWarning,
    )
    fault_join_type = _solvis_join(filter_set_options, "multiple_faults")
    return fault_system_solution.get_rupture_ids_for_fault_names(corupture_fault_names, fault_join_type)


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

    tic0 = time.perf_counter()
    composite_solution = get_composite_solution(model_id)

    fss = composite_solution._solutions[fault_system]
    tic1 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time to load fault system solution: %2.3f seconds' % (tic1 - tic0))

    df0 = fss.ruptures_with_rupture_rates

    # attribute filters
    df0 = df0 if not max_mag else df0[df0.Magnitude <= max_mag]
    df0 = df0 if not min_mag else df0[df0.Magnitude > min_mag]
    df0 = df0 if not max_rate else df0[df0.rate_weighted_mean <= max_rate]
    df0 = df0 if not min_rate else df0[df0.rate_weighted_mean > min_rate]

    tic2 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time apply attribute filters: %2.3f seconds' % (tic2 - tic1))

    # co-rupture filter
    if corupture_fault_names and len(corupture_fault_names):
        fault_join_type = _solvis_join(filter_set_options, "multiple_faults")
        rupture_ids = fss.get_rupture_ids_for_fault_names(corupture_fault_names, fault_join_type)
        df0 = df0[df0["Rupture Index"].isin(list(rupture_ids))]

    tic3 = time.perf_counter()
    log.debug('matched_rupture_sections_gdf(): time apply co-rupture filter: %2.3f seconds' % (tic3 - tic2))

    # location filters
    if location_ids is not None and len(location_ids):
        location_join_type = _solvis_join(filter_set_options, "multiple_locations")
        rupture_ids = fss.get_rupture_ids_for_location_radius(location_ids, radius_km, location_join_type)
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

    fsr = fss.fault_sections_with_rupture_rates
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
