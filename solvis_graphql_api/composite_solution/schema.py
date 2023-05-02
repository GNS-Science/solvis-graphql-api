"""The API schema for conposite solutions."""

import logging
import math
from typing import Dict
import json
import geopandas as gpd
import graphene
import graphql_relay


import numpy as np
import pandas as pd
from graphene import relay

from .cached import matched_rupture_sections_gdf, fault_section_aggregates_gdf
from .composite_rupture_detail import CompositeRuptureDetail, RuptureDetailConnection
from solvis_graphql_api.color_scale import ColourScaleNormaliseEnum, get_colour_values

log = logging.getLogger(__name__)


# def sorted_dataframe(dataframe: gpd.GeoDataFrame, sortby_args: Dict, min_rate: float):
#     """Sort the dataframe by the argument specifications

#     Manually set bins according to sortby_args.
#     """
#     def build_bins(start: float, step: float, until: float, logarithmic: bool):
#         if logarithmic:
#             return np.logspace(np.log10(step), np.log10(1.0), 100)
#         else:
#             _bin = start
#             bins = [_bin]
#             while _bin < until + step:
#                 _bin += step
#                 bins.append(_bin)
#         return bins

#     by = []
#     ascending = []
#     for itm in sortby_args:
#         column = CompositeRuptureDetail.column_name(itm['attribute'])
#         if width := itm.get('bin_width'):  # handle binning
#             print(itm)
#             bins = build_bins(
#                 start=0, step=width, until=dataframe[column].max(), logarithmic=itm.get('log_bins', False)
#             )
#             print(bins)
#             dataframe[column + "_binned"] = pd.cut(dataframe[column], bins=bins, labels=bins[1:])
#             column = column + "_binned"

#         by.append(column)
#         ascending.append(itm.get('ascending', True))

#     return dataframe.sort_values(by=by, ascending=ascending)


def auto_sorted_dataframe(dataframe: gpd.GeoDataFrame, sortby_args: Dict, min_rate: float):
    """Sort the dataframe by the argument specifications

    Automatically set bins for Mag or rate-based columns using simple heuristics.
    """
    by = []
    ascending = []
    # print('sortby_args', sortby_args)
    # print()
    for idx, itm in enumerate(sortby_args):
        column = CompositeRuptureDetail.column_name(itm['attribute'])
        if len(sortby_args) == 1:
            by.append(column)
            ascending.append(itm.get('ascending', True))
            continue

        if idx == 0:
            if itm['attribute'] == 'magnitude':
                bins = np.logspace(np.log10(5.0), np.log10(10.0), 50)  # 50 bins at M0.1 spacing
                print(f"Bin setup magnitude logspace for {itm['attribute']}")
                # continue
            else:
                # all others are rate values, so take min rate and
                places = abs(math.floor(math.log10(min_rate) + 1))
                # print('places:', places)
                bins = np.logspace(np.log10(min_rate), np.log10(1.0), 10 * places)
            # print(bins)
            dataframe[column + "_binned"] = pd.cut(dataframe[column], bins=bins, labels=bins[1:])
            column = column + "_binned"

        by.append(column)
        ascending.append(itm.get('ascending', True))

    print("by", by, "ascending", ascending)
    return dataframe.sort_values(by=by, ascending=ascending)


def build_ruptures_connection(
    rupture_sections_gdf: gpd.GeoDataFrame, model_id: str, fault_system: str, first: int, after: graphene.ID = None
):
    # stolen from FaultSystemRuptures resolver....
    cursor_offset = int(graphql_relay.from_global_id(after)[1]) + 1 if after else 0

    rupture_ids = list(rupture_sections_gdf["Rupture Index"])
    nodes = [
        CompositeRuptureDetail(model_id=model_id, fault_system=fault_system, rupture_index=rid)
        for rid in rupture_ids[cursor_offset : cursor_offset + first]
    ]

    # based on https://gist.github.com/AndrewIngram/b1a6e66ce92d2d0befd2f2f65eb62ca5#file-pagination-py-L152
    edges = [
        RuptureDetailConnection.Edge(
            node=node, cursor=graphql_relay.to_global_id("RuptureDetailConnectionCursor", str(cursor_offset + idx))
        )
        for idx, node in enumerate(nodes)
    ]

    # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
    connection_field = relay.ConnectionField.resolve_connection(RuptureDetailConnection, {}, edges)

    total_count = len(rupture_ids)
    has_next = total_count > 1 + int(graphql_relay.from_global_id(edges[-1].cursor)[1]) if edges else False

    connection_field.total_count = total_count
    connection_field.page_info = relay.PageInfo(
        end_cursor=edges[-1].cursor
        if edges
        else None,  # graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
        has_next_page=has_next,
    )
    connection_field.edges = edges
    return connection_field


def paginated_filtered_ruptures(filter_args, sortby_args, **kwargs) -> RuptureDetailConnection:
    ### query that accepts both the rupture filter & sortby_args args and the pagination args
    log.info('paginated_ruptures args: %s filter_args:%s' % (kwargs, filter_args))

    min_rate = filter_args.get('minimum_rate') or 1e-20

    rupture_sections_gdf = matched_rupture_sections_gdf( # is this working in both scenarios?
        filter_args['model_id'],
        filter_args['fault_system'],
        tuple(filter_args['location_ids']),
        filter_args['radius_km'],
        min_rate=min_rate,
        max_rate=filter_args.get('maximum_rate'),
        min_mag=filter_args.get('minimum_mag'),
        max_mag=filter_args.get('maximum_mag'),
        union=False,
    )

    if sortby_args:
        rupture_sections_gdf = auto_sorted_dataframe(rupture_sections_gdf, sortby_args, min_rate)

    first = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none
    log.info(f'paginated_filtered_ruptures ruptures : first={first}, after={after}')

    return build_ruptures_connection(
        rupture_sections_gdf,
        model_id=filter_args['model_id'],
        fault_system=filter_args['fault_system'],
        first=first,
        after=after,
    )

class CompositeRuptureSections(graphene.ObjectType):
    model_id = graphene.String()

    rupture_count = graphene.Int()
    section_count = graphene.Int()

    #these are useful for calculating color scales
    max_magnitude = graphene.Float(description="maximum magnitude from contributing solutions")
    min_magnitude = graphene.Float(description="minimum magnitude from contributing solutions")
    max_participation_rate = graphene.Float(description="maximum section participation rate (sum of rate_weighted_mean.sum) over the contributing solutions")
    min_participation_rate = graphene.Float(description="minimum section participation rate (sum of rate_weighted_mean.sum) over the contributing solutions")

    fault_surfaces = graphene.Field(
        graphene.JSONString,
    )

def filtered_rupture_sections(filter_args, **kwargs) -> CompositeRuptureSections:
    ### query that accepts both the rupture filter
    log.info('filtered_rupture_sections_map args: %s filter_args:%s' % (kwargs, filter_args))

    min_rate = filter_args.get('minimum_rate') or 1e-20

    fault_sections_gdf = fault_section_aggregates_gdf(
        filter_args['model_id'],
        filter_args['fault_system'],
        tuple(filter_args['location_ids']),
        filter_args['radius_km'],
        min_rate=min_rate,
        max_rate=filter_args.get('maximum_rate'),
        min_mag=filter_args.get('minimum_mag'),
        max_mag=filter_args.get('maximum_mag'),
        union=False,
    )


    # print(fault_sections_gdf.columns)
    # print(fault_sections_gdf.index)
    # log.debug('color_scale_normalise %s' % color_scale_normalise)
    color_scale='inferno'
    color_values = get_colour_values(
        color_scale=color_scale,
        color_scale_vmax=fault_sections_gdf['rate_weighted_mean.sum'].max(),
        color_scale_vmin=fault_sections_gdf['rate_weighted_mean.sum'].min(),
        color_scale_normalise=ColourScaleNormaliseEnum.LOG.name,
        values=tuple(fault_sections_gdf['rate_weighted_mean.sum'].tolist())
    )

    # t3 = dt.utcnow()
    log.debug('cacheable_hazard_map colour map ') # % (t3 - t2))
    log.debug('get_colour_values cache_info: %s' % str(get_colour_values.cache_info()))

    fill_opacity = 0.75
    stroke_width = 1
    stroke_opacity = 1

    fault_sections_gdf['fill'] = color_values
    fault_sections_gdf['fill-opacity'] = fill_opacity # for n in values]
    fault_sections_gdf['stroke'] = color_values
    fault_sections_gdf['stroke-width'] = stroke_width
    fault_sections_gdf['stroke-opacity'] = stroke_opacity

    #print(fault_sections_gdf)

    #import solvis
    #solvis.export_geojson(fault_sections_gdf, 'q0.geojson', indent=2)

    return CompositeRuptureSections(
        model_id=filter_args.get('model_id'),
        fault_surfaces = json.loads(fault_sections_gdf.to_json()),
        section_count = fault_sections_gdf.shape[0],
        max_magnitude = fault_sections_gdf['Magnitude.max'].max(),
        min_magnitude = fault_sections_gdf['Magnitude.min'].min(),
        max_participation_rate = fault_sections_gdf['rate_weighted_mean.sum'].max(),
        min_participation_rate = fault_sections_gdf['rate_weighted_mean.sum'].min(),
)

