# test_sort_function.py

import pytest  # noqa
from solvis_graphql_api.composite_solution import cached
from solvis_graphql_api.composite_solution.schema import auto_sorted_dataframe
from unittest.mock import patch

MODEL_ID = "NSHM_v1.0.0"
FAULT_SYSTEM = "HIK"


@patch('solvis_graphql_api.composite_solution.cached.get_rupture_ids', lambda *args, **kwargs: [n for n in range(500)])
@patch('solvis_graphql_api.composite_solution.cached.RESOLVE_LOCATIONS_INTERNALLY', False)
def test_cached_ruptures_with_store():

    rupture_sections_gdf = cached.matched_rupture_sections_gdf(
        MODEL_ID,
        FAULT_SYSTEM,
        ("WLG",),
        20,
        min_rate=1e-10,
        max_rate=1,
        min_mag=6,
        max_mag=9.5,
        union=False,
    )

    print(rupture_sections_gdf.columns)

    sdf = auto_sorted_dataframe(
        rupture_sections_gdf,
        sortby_args=[
            dict(attribute="rate_max", bin_width=1e-10, log_bins=True, ascending=False),
            dict(attribute="magnitude", ascending=False),
        ],
        min_rate=1e-10,
    )
    print(sdf[['rate_max', 'Magnitude']].tail(20))


def test_cached_ruptures_without_store():

    rupture_sections_gdf = cached.matched_rupture_sections_gdf(
        MODEL_ID,
        FAULT_SYSTEM,
        ("WLG",),
        20,
        min_rate=1e-10,
        max_rate=1,
        min_mag=6,
        max_mag=9.5,
        union=False,
    )

    print(rupture_sections_gdf.columns)

    sdf = auto_sorted_dataframe(
        rupture_sections_gdf,
        sortby_args=[
            dict(attribute="rate_max", bin_width=1e-10, log_bins=True, ascending=False),
            dict(attribute="magnitude", ascending=False),
        ],
        min_rate=1e-10,
    )
    print(sdf[['rate_max', 'Magnitude']].tail(20))


def test_cached_ruptures_no_location():

    rupture_sections_gdf = cached.matched_rupture_sections_gdf(
        MODEL_ID,
        FAULT_SYSTEM,
        None,  # convert to string
        20,
        min_rate=1e-10,
        max_rate=1,
        min_mag=6,
        max_mag=9.5,
        union=False,
    )

    print(rupture_sections_gdf.columns)

    sdf = auto_sorted_dataframe(
        rupture_sections_gdf,
        sortby_args=[
            dict(attribute="rate_max", bin_width=1e-10, log_bins=True, ascending=False),
            dict(attribute="magnitude", ascending=False),
        ],
        min_rate=1e-10,
    )

    print(sdf[['rate_max', 'Magnitude']].tail(20))
    # assert 0
