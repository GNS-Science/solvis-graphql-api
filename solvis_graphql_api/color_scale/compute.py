"""Graphene-free colour-scale compute.

The matplotlib maths extracted out of the legacy graphene `color_scale.py` so the Strawberry
schema can build colour scales without importing graphene. The graphene module imports these
during the transition; it (and its graphene types) are deleted at cutover.
"""

import logging
import math
from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache

import matplotlib as mpl

log = logging.getLogger(__name__)


@dataclass
class ColourScaleResult:
    name: str
    min_value: float
    max_value: float
    normalisation: str  # "log" | "lin"
    levels: list[float]
    hexrgbs: list[str]


@lru_cache
def get_normaliser(color_scale_vmax: float, color_scale_vmin: float, color_scale_normalise: str):
    if color_scale_normalise == "log":
        return mpl.colors.LogNorm(vmin=color_scale_vmin, vmax=color_scale_vmax)
    if color_scale_normalise == "lin":
        color_scale_vmin = color_scale_vmin or 0
        return mpl.colors.Normalize(vmin=color_scale_vmin, vmax=color_scale_vmax)
    raise RuntimeError(f"unknown normalisation option: {color_scale_normalise} ")


@lru_cache
def log_intervals(vmin, vmax):
    """get a manageable set of sensible levels between upper and lower exponential bounds"""
    min_exponent = int(math.floor(math.log10(abs(vmin))))
    max_exponent = int(math.floor(math.log10(abs(vmax))))
    if min_exponent == max_exponent:
        max_exponent += 1

    intervals = [math.pow(10, power) for power in range(min_exponent, max_exponent + 1)]
    max_val = intervals[-1]
    MIN_LEN = 6
    MAX_LEN = 8

    def interpolate(intervals):
        new_intervals = intervals.copy()
        for sub_interval in [0.5, 0.2, 0.1]:
            for interval in intervals:
                new_interval = interval * sub_interval
                if intervals[0] < new_interval < intervals[-1]:
                    new_intervals.append(round(new_interval, abs(min_exponent)))
            if len(new_intervals) >= MIN_LEN:
                return new_intervals
        return new_intervals

    def slim(new_intervals, max):
        while len(new_intervals) > MAX_LEN:
            new_intervals = new_intervals[::2]
        new_intervals = sorted(new_intervals)
        # unreachable: the sole caller passes `max=intervals[0]` (the minimum), so the largest
        # element is never < it. Faithfully ported dead branch from the legacy color_scale.py.
        if new_intervals[-1] < max:  # pragma: no cover
            new_intervals.append(max)
        return new_intervals

    def ensure_max(intervals, max_value):
        if max_value not in intervals:
            intervals.append(max_value)
        return intervals

    if len(intervals) > MAX_LEN:
        intervals = ensure_max(slim(intervals, intervals[0]), max_val)
    if len(intervals) < MIN_LEN:
        intervals = ensure_max(interpolate(intervals), max_val)
    return sorted(intervals)


@lru_cache
def compute_colour_scale(color_scale: str, color_scale_normalise: str, vmax: float, vmin: float) -> ColourScaleResult:
    levels: list[float] = []
    hexrgbs: list[str] = []
    cmap = mpl.colormaps[color_scale]
    if color_scale_normalise == "log":
        intervals = log_intervals(vmin, vmax)
        norm = get_normaliser(max(intervals), min(intervals), color_scale_normalise)
        for level in intervals:
            levels.append(level)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level))))
    elif color_scale_normalise == "lin":
        assert vmax * 2 == int(vmax * 2)  # make sure we have a value on a 0.5 interval
        norm = get_normaliser(vmax, vmin, color_scale_normalise)
        for level in range(int(vmin * 10), int(vmax * 10) + 1):
            levels.append(level / 10)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level / 10))))
    else:
        raise RuntimeError(f"unknown normalisation option: {color_scale_normalise} ")
    return ColourScaleResult(
        name=color_scale, min_value=vmin, max_value=vmax, normalisation=color_scale_normalise,
        levels=levels, hexrgbs=hexrgbs,
    )


@lru_cache
def get_colour_values(
    color_scale: str, color_scale_vmax: float, color_scale_vmin: float, color_scale_normalise: str,
    values: tuple[float | None],
) -> Iterable[str]:
    intervals = log_intervals(color_scale_vmin, color_scale_vmax)
    norm = get_normaliser(max(intervals), min(intervals), color_scale_normalise)
    cmap = mpl.colormaps[color_scale]
    colors = []
    for v in values:
        colors.append("x000000" if v is None else mpl.colors.to_hex(cmap(norm(v)), keep_alpha=False))
    return colors
