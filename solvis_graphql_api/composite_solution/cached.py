"""The API schema for conposite solutions."""

import logging
import os
from functools import lru_cache
from pathlib import Path

import nzshm_model as nm
import pandas as pd
import solvis
from nzshm_common.location.location import location_by_id

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


@lru_cache
def get_location_polygon(radius_km, lon, lat):
    return solvis.geometry.circle_polygon(radius_m=radius_km * 1000, lon=lon, lat=lat)


@lru_cache
def get_composite_solution(model_id: str) -> solvis.CompositeSolution:

    # print(model_id)
    # print(nm.get_model_version(model_id))
    assert nm.get_model_version(model_id) is not None
    slt = nm.get_model_version(model_id).source_logic_tree()

    # needed for local testing only, so we can move ZIP file out of inotify scope
    # so it doesn't cause reloading loop on wsgi_serve
    COMPOSITE_ARCHIVE_PATH = os.getenv('COMPOSITE_ARCHIVE_PATH')

    if COMPOSITE_ARCHIVE_PATH is None:
        folder = Path(os.path.realpath(__file__)).parent
        COMPOSITE_ARCHIVE_PATH = str(Path(folder, "NewCompositeSolution.zip"))
        log.warning("Loading DEFAULT composite solution: %s" % COMPOSITE_ARCHIVE_PATH)
    else:
        log.info("Loading composite solution: %s" % COMPOSITE_ARCHIVE_PATH)
    return solvis.CompositeSolution.from_archive(Path(COMPOSITE_ARCHIVE_PATH), slt)


@lru_cache
def matched_rupture_sections_gdf(
    model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union
):
    """
    Query the solvis.CompositeSolution instance identified by model ID.


    This uses a CompositeSolution instance loaded from archive file, so location tests are
    slowed considerably compared to solvis_store query approach.

    return a dataframe of the rupture ids by fault_system.
    """

    def filter_solution(
        model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union
    ):
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
            if location_codes is not None:
                rupture_ids = set()
                for loc_code in location_codes.split(','):
                    loc = location_by_id(loc_code)
                    # print(loc)
                    polygon = get_location_polygon(radius_km=radius_km, lon=loc['longitude'], lat=loc['latitude'])
                    rupture_ids = rupture_ids.union(set(fss.get_ruptures_intersecting(polygon)))
                    # print(fault_system, len(rupture_ids))
                # print('rupture_ids', rupture_ids)
                df0 = df0[df0["Rupture Index"].isin(rupture_ids)]

            rupture_rates_df = (
                df0 if rupture_rates_df is None else pd.concat([rupture_rates_df, df0], ignore_index=True)
            )

        return rupture_rates_df

    df = filter_solution(
        model_id, fault_systems, location_codes, radius_km, min_rate, max_rate, min_mag, max_mag, union
    )

    return df
