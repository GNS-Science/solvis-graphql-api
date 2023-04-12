# test_sort_function.py

import pytest  # noqa
from solvis_graphql_api.composite_solution import cached
from solvis_graphql_api.composite_solution.schema import auto_sorted_dataframe

MODEL_ID = "NSHM_1.0.0"
FAULT_SYSTEM = "HIK"


# @pytest.mark.skip('WIP')
def test_cached_ruptures():

    rupture_sections_gdf = cached.matched_rupture_sections_gdf(
        MODEL_ID,
        tuple([FAULT_SYSTEM]),
        "WLG",  # convert to string
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


# @pytest.mark.skip('WIP')
def test_cached_ruptures_no_location():

    rupture_sections_gdf = cached.matched_rupture_sections_gdf(
        MODEL_ID,
        tuple([FAULT_SYSTEM]),
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
