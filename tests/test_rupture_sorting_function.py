# test_sort_function.py

from unittest.mock import patch

import pytest  # noqa

from solvis_graphql_api.composite_solution import cached
from solvis_graphql_api.composite_solution.schema import auto_sorted_dataframe

MODEL_ID = "NSHM_v1.0.4"
FAULT_SYSTEM = "HIK"


@patch(
    'solvis_graphql_api.composite_solution.cached.get_location_radius_rupture_ids',
    lambda *args, **kwargs: [n for n in range(500)],
)
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
        filter_set_options=frozenset(dict(multiple_locations=1, multiple_faults=1, locations_and_faults=1).items()),
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
    print(sdf.loc[('HIK', 366)])
    assert pytest.approx(sdf.at[('HIK', 366), 'Magnitude']) == 7.556495


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
        filter_set_options=frozenset(dict(multiple_locations=1, multiple_faults=1, locations_and_faults=1).items()),
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
    assert pytest.approx(sdf.at[('HIK', 366), 'Magnitude']) == 7.556495


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
        filter_set_options=frozenset(dict(multiple_locations=1, multiple_faults=1, locations_and_faults=1).items()),
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
    assert pytest.approx(sdf.at[('HIK', 366), 'Magnitude']) == 7.556495
