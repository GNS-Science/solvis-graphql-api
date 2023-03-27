"""The API schema for conposite solutions."""

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterator, List

import geopandas as gpd
import graphene
from graphene import relay
import nzshm_model as nm
import pandas as pd
import solvis

from solvis_graphql_api.solution_schema import (
    GeojsonAreaStyleArguments,
    GeojsonLineStyleArguments,
    apply_fault_trace_style,
)

log = logging.getLogger(__name__)

FAULT_SECTION_LIMIT = 1e4


class FaultSystemRuptures(graphene.ObjectType):
    fault_system = graphene.String(description="Unique ID of the fault system e.g. PUY")
    rupture_ids = graphene.List(graphene.Int)


class CompositeRuptureDetail(graphene.ObjectType):
    class Meta:
        interfaces = (relay.Node, )

    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    rupture_index = graphene.Int()

    fault_traces = graphene.JSONString()
    fault_surfaces = graphene.JSONString()

    # def resolve_fault_surfaces(root, info, *args, **kwargs):
    #     model_id = kwargs.get('model_id')
    #     fault_system = kwargs.get('fault_system')  # cursor of last page, or none

    #     log.info(f'resolve resolve_fault_surfaces : {model_id}, {fault_system}')
    #     return ""

class CompositeRuptureDetailArguments(graphene.InputObjectType):
    model_id = graphene.String()
    fault_system = graphene.String(description="Unique ID of the fault system e.g. `PUY`")
    rupture_index = graphene.Int()

    fault_trace_style = GeojsonLineStyleArguments(
        required=False,
        description="feature style for rupture trace geojson.",
        default_value=dict(stroke_color="black", stroke_width=1, stroke_opacity=1.0),
    )
