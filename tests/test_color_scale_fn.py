"""Tests for `solvis_graphql_api` package."""

import pytest

from solvis_graphql_api.color_scale.color_scale import get_colour_scale, log_intervals

TEST_ARGS = [
    (0.00967, 0.0042171),  # PUY_ALL
    (8.5435, 3.0995778388387407e-7),  # CRU_ALL
    (0.0008977324469015002, 3.2937376598254063e-18),  # HAW 200KM
]


@pytest.mark.parametrize('vmax, vmin', TEST_ARGS)
def test_color_scale_lengths(vmax, vmin):

    res = get_colour_scale(color_scale='inferno', color_scale_normalise='log', vmax=vmax, vmin=vmin)

    print(res)

    print(res.color_map.levels)
    print(res.color_map.hexrgbs)

    assert 4 <= len(res.color_map.levels) <= 10
    assert 4 <= len(res.color_map.hexrgbs) <= 10
    assert len(res.color_map.levels) == len(res.color_map.hexrgbs)


@pytest.mark.parametrize('vmax, vmin', TEST_ARGS)
def test_intervals_lengths(vmax, vmin):

    res = log_intervals(vmax=vmax, vmin=vmin)
    assert 4 <= len(res) <= 10
    print(res)
