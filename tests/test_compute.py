"""Unit tests for the graphene-free colour-scale compute (extracted at the de-graphene cleanup).

Covers the maths and the error/edge branches directly, so the new `color_scale/compute.py`
module is exercised without going through the schema.
"""

import pytest

from solvis_graphql_api.color_scale import compute as C


def test_get_normaliser_log_lin_and_error():
    assert C.get_normaliser(10.0, 1.0, "log") is not None
    assert C.get_normaliser(10.0, 0.0, "lin") is not None
    with pytest.raises(RuntimeError):
        C.get_normaliser(10.0, 1.0, "bogus")


@pytest.mark.parametrize(
    "vmin, vmax",
    [
        (1.0e-6, 1.0),  # wide multi-decade span -> slim() path
        (0.0042171, 0.00967),  # narrow span -> interpolate() path
        (3.2937376598254063e-18, 0.0008977324469015002),  # very wide -> slim + ensure_max
        (1.0e-20, 1.0e-11),  # slim path where ensure_max appends the boundary
    ],
)
def test_log_intervals_lengths(vmin, vmax):
    iv = C.log_intervals(vmin, vmax)
    assert 4 <= len(iv) <= 10
    assert iv == sorted(iv)


def test_log_intervals_same_decade():
    # min_exponent == max_exponent branch (max_exponent += 1)
    iv = C.log_intervals(1.2, 3.4)
    assert len(iv) >= 4


def test_compute_colour_scale_log():
    res = C.compute_colour_scale("inferno", "log", 1.0, 1.0e-3)
    assert res.normalisation == "log"
    assert len(res.levels) == len(res.hexrgbs) >= 4
    assert all(h.startswith("#") for h in res.hexrgbs)


def test_compute_colour_scale_lin():
    res = C.compute_colour_scale("inferno", "lin", 10.0, 0.0)
    assert res.normalisation == "lin"
    assert len(res.levels) == len(res.hexrgbs)
    assert all(h.startswith("#") for h in res.hexrgbs)


def test_compute_colour_scale_unknown_normalisation():
    with pytest.raises(RuntimeError):
        C.compute_colour_scale("inferno", "bogus", 10.0, 1.0)


def test_get_colour_values_includes_none_sentinel():
    vals = list(C.get_colour_values("inferno", 1.0, 1.0e-3, "log", (1.0e-3, 1.0e-2, None)))
    assert vals[-1] == "x000000"  # None maps to the sentinel, not a hex
    assert all(v.startswith("#") for v in vals[:2])
