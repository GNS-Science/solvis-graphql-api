# color_scale.py

import logging
import math
import os
from functools import lru_cache
from typing import Iterable, Tuple, Union

import graphene
import matplotlib as mpl

# from solvis_graphql_api.cloudwatch import ServerlessMetricWriter

log = logging.getLogger(__name__)

# db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")


class ColourScaleNormaliseEnum(graphene.Enum):
    LOG = "log"
    LIN = "lin"


COLOR_SCALE_NORMALISE_LOG = (
    "log" if os.getenv("COLOR_SCALE_NORMALISATION", "").upper() == "LOG" else "lin"
)


class HexRgbValueMapping(graphene.ObjectType):
    levels = graphene.List(graphene.Float)
    hexrgbs = graphene.List(graphene.String)


class ColorScaleArgsBase:
    name = graphene.String(default_value="inferno")
    min_value = graphene.Float()
    max_value = graphene.Float()
    normalisation = graphene.Field(ColourScaleNormaliseEnum)


class ColorScaleArgsInput(ColorScaleArgsBase, graphene.InputObjectType):
    """Arguments passed as ColorScaleArgsInput"""


class ColorScaleArgs(ColorScaleArgsBase, graphene.ObjectType):
    """Arguments ColorScaleArgs"""


class ColorScale(graphene.ObjectType):
    name = graphene.String()
    min_value = graphene.Float()
    max_value = graphene.Float()
    normalisation = graphene.Field(ColourScaleNormaliseEnum)
    color_map = graphene.Field(HexRgbValueMapping)


@lru_cache
def get_normaliser(
    color_scale_vmax: float, color_scale_vmin: float, color_scale_normalise: str
):

    if color_scale_normalise == ColourScaleNormaliseEnum.LOG.value:  # type: ignore
        log.debug("resolve_hazard_map using LOG normalized colour scale")
        return mpl.colors.LogNorm(vmin=color_scale_vmin, vmax=color_scale_vmax)
    if color_scale_normalise == ColourScaleNormaliseEnum.LIN.value:  # type: ignore
        color_scale_vmin = color_scale_vmin or 0
        log.debug("resolve_hazard_map using LIN normalized colour scale")
        return mpl.colors.Normalize(vmin=color_scale_vmin, vmax=color_scale_vmax)
    raise RuntimeError("unknown normalisation option: %s " % color_scale_normalise)


@lru_cache
def log_intervals(vmin, vmax):
    """
    get a manageable set of sensible levels between upper and lower exponential bounds
    """
    min_exponent = int(math.floor(math.log10(abs(vmin))))  # e.g. -7 for 0.5e-6
    max_exponent = int(math.floor(math.log10(abs(vmax))))  # e.g. 1 fpr 22.5 , 0 for 9.5
    if min_exponent == max_exponent:
        max_exponent += 1

    intervals = [math.pow(10, power) for power in range(min_exponent, max_exponent + 1)]

    max_val = intervals[-1]
    MIN_LEN = 6
    MAX_LEN = 8

    def interpolate(intervals):
        # print('interpolate', intervals)
        new_intervals = intervals.copy()
        sub_intervals = [0.5, 0.2, 0.1]
        for sub_interval in sub_intervals:
            # print('sub_interval', sub_interval)
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
        if new_intervals[-1] < max:
            new_intervals.append(max)
        return new_intervals

    def ensure_max(intervals, max_value):
        # return intervals
        if max_value not in intervals:
            intervals.append(max_value)
        return intervals

    if len(intervals) > MAX_LEN:
        intervals = ensure_max(slim(intervals, intervals[0]), max_val)

    if len(intervals) < MIN_LEN:
        intervals = ensure_max(interpolate(intervals), max_val)

    return sorted(intervals)


'''
def log_intervals(vmin, vmax):
    """
    get at least 4 and no more than 7 intervals between upper and lower exponential bounds
    """
    min_exponent = int(math.floor(math.log10(abs(vmin))))  # e.g. -7 for 0.5e-6
    max_exponent = int(math.floor(math.log10(abs(vmax))))  # e.g. 1 fpr 22.5 , 0 for 9.5
    return np.logspace(min_exponent, max_exponent, 10)
'''


@lru_cache
def get_colour_scale(
    color_scale: str, color_scale_normalise: str, vmax: float, vmin: float
) -> ColorScale:
    # build the colour_scale
    log.debug(
        "get_colour_scale(color_scale:%s normalize: %s vmin: %s vmax: %s"
        % (color_scale, color_scale_normalise, vmin, vmax)
    )

    levels, hexrgbs = [], []
    cmap = mpl.colormaps[color_scale]
    if color_scale_normalise == ColourScaleNormaliseEnum.LOG.value:  # type: ignore
        intervals = log_intervals(vmin, vmax)
        norm = get_normaliser(max(intervals), min(intervals), color_scale_normalise)
        for level in intervals:
            levels.append(level)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level))))
    elif color_scale_normalise == ColourScaleNormaliseEnum.LIN.value:  # type: ignore
        assert vmax * 2 == int(vmax * 2)  # make sure we have a value on a 0.5 interval
        norm = get_normaliser(vmax, vmin, color_scale_normalise)
        for level in range(int(vmin * 10), int(vmax * 10) + 1):
            levels.append(level / 10)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level / 10))))
    else:
        raise RuntimeError("unknown normalisation option: %s " % color_scale_normalise)

    hexrgb = HexRgbValueMapping(levels=levels, hexrgbs=hexrgbs)
    return ColorScale(
        name=color_scale,
        min_value=vmin,
        max_value=vmax,
        normalisation=color_scale_normalise,
        color_map=hexrgb,
    )


@lru_cache
def get_colour_values(
    color_scale: str,
    color_scale_vmax: float,
    color_scale_vmin: float,
    color_scale_normalise: str,
    values: Tuple[Union[float, None]],
) -> Iterable[str]:

    log.debug("color_scale_vmax: %s" % color_scale_vmax)
    intervals = log_intervals(color_scale_vmin, color_scale_vmax)
    norm = get_normaliser(max(intervals), min(intervals), color_scale_normalise)
    cmap = mpl.colormaps[color_scale]
    colors = []
    # set any missing values to black
    for i, v in enumerate(values):
        if v is None:
            colors.append("x000000")
        else:
            colors.append(mpl.colors.to_hex(cmap(norm(v)), keep_alpha=False))
    return colors
