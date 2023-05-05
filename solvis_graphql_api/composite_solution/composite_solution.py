"""The API schema for conposite solutions."""

import logging

import graphene

log = logging.getLogger(__name__)


class CompositeSolution(graphene.ObjectType):
    model_id = graphene.String()
    fault_systems = graphene.List(graphene.String)


class FilterRupturesArgsBase:
    """Defines filter arguments for Inversions analysis, must be subtyped"""

    model_id = graphene.String(required=True, description="The ID of NSHM model")

    fault_system = graphene.String(
        required=True,
        description="The fault systems [`HIK`, `PUY`, `CRU`]",
    )

    location_ids = graphene.List(
        graphene.String,
        required=False,
        default_value=[],
        description="Optional list of locations ids for proximity filtering e.g. `WLG,PMR,ZQN`",
    )

    radius_km = graphene.Int(required=False, description='The rupture/location intersection radius in km')

    minimum_rate = graphene.Float(
        required=False, description="Constrain to fault_sections having a annual rate above the value supplied."
    )
    maximum_rate = graphene.Float(
        required=False, description="Constrain to fault_sections having a annual rate below the value supplied."
    )
    minimum_mag = graphene.Float(
        required=False, description="Constrain to fault_sections having a magnitude above the value supplied."
    )
    maximum_mag = graphene.Float(
        required=False, description="Constrain to fault_sections having a magnitude below the value supplied."
    )


class FilterRupturesArgsInput(FilterRupturesArgsBase, graphene.InputObjectType):
    """Arguments passed as FilterRupturesArgs"""


class FilterRupturesArgs(FilterRupturesArgsBase, graphene.ObjectType):
    """Arguments FilterRupturesArgs"""
