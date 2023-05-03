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


COLOR_SCALE_NORMALISE_LOG = 'log' if os.getenv('COLOR_SCALE_NORMALISATION', '').upper() == 'LOG' else 'lin'


class HexRgbValueMapping(graphene.ObjectType):
    levels = graphene.List(graphene.Float)
    hexrgbs = graphene.List(graphene.String)


class ColorScaleArgs(graphene.InputObjectType):
    name = graphene.String(required=True)
    min_value = graphene.Float()
    max_value = graphene.Float()
    normalisation = graphene.Field(ColourScaleNormaliseEnum)


class ColorScale(graphene.ObjectType):
    name = graphene.String()
    min_value = graphene.Float()
    max_value = graphene.Float()
    normalisation = graphene.Field(ColourScaleNormaliseEnum)
    color_map = graphene.Field(HexRgbValueMapping)


@lru_cache
def get_normaliser(color_scale_vmax: float, color_scale_vmin: float, color_scale_normalise: str):

    if color_scale_normalise == ColourScaleNormaliseEnum.LOG.value:  # type: ignore
        log.debug("resolve_hazard_map using LOG normalized colour scale")
        return mpl.colors.LogNorm(vmin=color_scale_vmin, vmax=color_scale_vmax)
    if color_scale_normalise == ColourScaleNormaliseEnum.LIN.value:  # type: ignore
        color_scale_vmin = color_scale_vmin or 0
        log.debug("resolve_hazard_map using LIN normalized colour scale")
        return mpl.colors.Normalize(vmin=color_scale_vmin, vmax=color_scale_vmax)
    raise RuntimeError("unknown normalisation option: %s " % color_scale_normalise)


def log_intervals(vmin, vmax):
    min_exponent = int(math.floor(math.log10(abs(vmin))))  # e.g. -7 for 0.5e-6
    max_exponent = int(math.floor(math.log10(abs(vmax))))  # e.g. 1 fpr 22.5 , 0 for 9.5
    for power in range(min_exponent + 1, max_exponent + 1):
        for interval in [0.1, 0.2, 0.5]:
            yield interval * math.pow(10, power)
    yield math.pow(10, power)


@lru_cache
def get_colour_scale(color_scale: str, color_scale_normalise: str, vmax: float, vmin: float) -> ColorScale:
    # build the colour_scale
    log.debug(
        'get_colour_scale(color_scale:%s normalize: %s vmin: %s vmax: %s'
        % (color_scale, color_scale_normalise, vmin, vmax)
    )

    levels, hexrgbs = [], []
    cmap = mpl.colormaps[color_scale]
    norm = get_normaliser(vmax, vmin, color_scale_normalise)
    if color_scale_normalise == ColourScaleNormaliseEnum.LOG.value:  # type: ignore
        for level in log_intervals(vmin, vmax):
            levels.append(level)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level))))
    elif color_scale_normalise == ColourScaleNormaliseEnum.LIN.value:  # type: ignore
        assert vmax * 2 == int(vmax * 2)  # make sure we have a value on a 0.5 interval
        for level in range(int(vmin * 10), int(vmax * 10) + 1):
            levels.append(level / 10)
            hexrgbs.append(mpl.colors.to_hex(cmap(norm(level / 10))))
    else:
        raise RuntimeError("unknown normalisation option: %s " % color_scale_normalise)

    hexrgb = HexRgbValueMapping(levels=levels, hexrgbs=hexrgbs)
    return ColorScale(
        name=color_scale, min_value=vmin, max_value=vmax, normalisation=color_scale_normalise, color_map=hexrgb
    )


@lru_cache
def get_colour_values(
    color_scale: str,
    color_scale_vmax: float,
    color_scale_vmin: float,
    color_scale_normalise: str,
    values: Tuple[Union[float, None]],
) -> Iterable[str]:

    log.debug('color_scale_vmax: %s' % color_scale_vmax)
    norm = get_normaliser(color_scale_vmax, color_scale_vmin, color_scale_normalise)
    cmap = mpl.colormaps[color_scale]
    colors = []
    # set any missing values to black
    for i, v in enumerate(values):
        if v is None:
            colors.append("x000000")
        else:
            colors.append(mpl.colors.to_hex(cmap(norm(v)), keep_alpha=True))
    return colors
