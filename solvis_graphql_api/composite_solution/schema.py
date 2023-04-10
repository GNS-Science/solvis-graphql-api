"""The API schema for conposite solutions."""

import logging

import geopandas as gpd
import graphene
import graphql_relay

# import numpy as np
import pandas as pd
from graphene import relay

from .cached import matched_rupture_sections_gdf
from .composite_rupture_detail import CompositeRuptureDetail, RuptureDetailConnection

log = logging.getLogger(__name__)


def paginated_filtered_ruptures(input, sortby, **kwargs) -> RuptureDetailConnection:
    ### query that accepts both the rupture filter args and the pagination args
    log.info('paginated_ruptures args: %s input:%s' % (kwargs, input))

    rupture_sections_gdf = matched_rupture_sections_gdf(
        input['model_id'],
        tuple([input['fault_system']]),
        ','.join(input['location_codes']),  # convert to string
        input['radius_km'],
        min_rate=input.get('minimum_rate') or 1e-20,
        max_rate=input.get('maximum_rate'),
        min_mag=input.get('minimum_mag'),
        max_mag=input.get('maximum_mag'),
        union=False,
    )

    if sortby:

        def build_bins(start: float, step: float, until: float):
            _bin = start
            bins = [_bin]
            while _bin < until + step:
                _bin += step
                bins.append(_bin)
            return bins

        by = []
        ascending = []
        binning = []
        for itm in sortby:
            byval = CompositeRuptureDetail.ATTRIBUTE_COLUMN_MAP.get(itm['attribute'], itm['attribute'])
            if w := itm.get('bin_width'):
                byval = byval + "_binned"
                binning.append(w)
            else:
                binning.append(None)
            by.append(byval)
            ascending.append(itm.get('ascending', True))

        # handle binning
        for idx, itm in enumerate(sortby):
            if width := itm.get('bin_width'):
                column = CompositeRuptureDetail.ATTRIBUTE_COLUMN_MAP.get(itm['attribute'], itm['attribute'])
                # bins = list(range(0, int(rupture_sections_gdf[column].max())+1, int(width)))
                bins = build_bins(start=0, step=width, until=rupture_sections_gdf[column].max())
                print('BINS', bins)
                rupture_sections_gdf[column + "_binned"] = pd.cut(
                    rupture_sections_gdf[column], bins=bins, labels=bins[1:]
                )
                # np.searchsorted(bins, rupture_sections_gdf[column].values)

        rupture_sections_gdf = rupture_sections_gdf.sort_values(by=by, ascending=ascending)
        # print(">>>>")
        # print(rupture_sections_gdf.info())
        # print(rupture_sections_gdf[["Magnitude", "Magnitude_binned", 'rate_weighted_mean']])
        # print(">>>>")

    first = kwargs.get('first', 5)  # how many to fetch
    after = kwargs.get('after')  # cursor of last page, or none
    log.info(f'paginated_filtered_ruptures ruptures : first={first}, after={after}')

    return build_ruptures_connection(
        rupture_sections_gdf,
        model_id=input['model_id'],
        fault_system=input['fault_system'],
        first=first,
        after=after,
    )


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

    print(nodes)
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

    # print(int(graphql_relay.from_global_id(edges[-1].cursor)[1]), total_count, has_next )

    connection_field.total_count = total_count
    connection_field.page_info = relay.PageInfo(
        end_cursor=edges[-1].cursor
        if edges
        else None,  # graphql_relay.to_global_id("CompositeRuptureDetail", str(cursor_offset+first)),
        has_next_page=has_next,
    )
    connection_field.edges = edges
    return connection_field
