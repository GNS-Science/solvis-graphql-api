"""Graphene-free rupture compute helpers.

``auto_sorted_dataframe`` was moved out of the legacy graphene ``composite_solution.schema``
so the Strawberry schema (and the function-level unit tests) can sort filtered ruptures without
importing graphene. The ``CompositeRuptureDetail.column_name`` lookup it used is inlined here as
``ATTRIBUTE_COLUMN_MAP``.
"""

import logging
import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

# field-name → dataframe-column map (was CompositeRuptureDetail.ATTRIBUTE_COLUMN_MAP in graphene)
ATTRIBUTE_COLUMN_MAP = {
    "rupture_index": "Rupture Index",
    "magnitude": "Magnitude",
    "rake_mean": "Average Rake (degrees)",
    "area": "Area (m^2)",
    "length": "Length (m)",
}


def column_name(field_name: str) -> str:
    return ATTRIBUTE_COLUMN_MAP.get(field_name, field_name)


def auto_sorted_dataframe(dataframe, sortby_args, min_rate: float):
    """Sort the dataframe by the argument specifications.

    Automatically set bins for Mag or rate-based columns using simple heuristics.
    """
    by: list = []
    ascending: list = []
    for idx, itm in enumerate(sortby_args):
        column: str = column_name(itm["attribute"])
        if len(sortby_args) == 1:
            by.append(column)
            ascending.append(itm.get("ascending", True))
            continue

        bins: Sequence
        if idx == 0:
            if itm["attribute"] == "magnitude":
                bins = np.logspace(np.log10(5.0), np.log10(10.0), 50).tolist()  # 50 bins at M0.1 spacing
            else:
                # all others are rate values, so take min rate and bin logarithmically
                places = abs(math.floor(math.log10(min_rate) + 1))
                bins = np.logspace(np.log10(min_rate), np.log10(1.0), 10 * places).tolist()
            dataframe[column + "_binned"] = pd.cut(dataframe[column], bins=bins, labels=bins[1:])
            column = column + "_binned"

        by.append(column)
        ascending.append(itm.get("ascending", True))

    log.debug(f"sort by {by}, ascending {ascending}")
    return dataframe.sort_values(by=by, ascending=ascending)
