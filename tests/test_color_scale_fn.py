"""Tests for `solvis_graphql_api` package."""

import pytest

from solvis_graphql_api.color_scale.compute import compute_colour_scale as get_colour_scale
from solvis_graphql_api.color_scale.compute import log_intervals

TEST_ARGS = [
    (0.00967, 0.0042171),  # PUY_ALL
    (8.5435, 3.0995778388387407e-7),  # CRU_ALL
    (0.0008977324469015002, 3.2937376598254063e-18),  # HAW 200KM
]


@pytest.mark.parametrize("vmax, vmin", TEST_ARGS)
def test_color_scale_lengths(vmax, vmin):

    res = get_colour_scale(color_scale="inferno", color_scale_normalise="log", vmax=vmax, vmin=vmin)

    print(res)

    print(res.levels)
    print(res.hexrgbs)

    assert 4 <= len(res.levels) <= 10
    assert 4 <= len(res.hexrgbs) <= 10
    assert len(res.levels) == len(res.hexrgbs)


@pytest.mark.parametrize("vmax, vmin", TEST_ARGS)
def test_intervals_lengths(vmax, vmin):

    res = log_intervals(vmax=vmax, vmin=vmin)
    assert 4 <= len(res) <= 10
    print(res)
