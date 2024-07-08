"""The API schema for conposite solutions."""

import logging

import graphene

from .filter_set_logic_options import FilterSetLogicOptions, FilterSetLogicOptionsInput, SetOperationEnum

log = logging.getLogger(__name__)


class FilterRupturesArgsBase:
    """Defines filter arguments for Inversions analysis, must be subtyped"""

    model_id = graphene.String(required=True, description="The ID of NSHM model")

    fault_system = graphene.String(
        required=True,
        description="The fault systems [`HIK`, `PUY`, `CRU`]",
    )

    corupture_fault_names = graphene.List(
        graphene.String,
        required=False,
        default_value=[],
        description="Optional list of parent fault names. Result will only include ruptures that include parent "
        "fault sections",
    )

    location_ids = graphene.List(
        graphene.String,
        required=False,
        default_value=[],
        description="Optional list of locations ids for proximity filtering e.g. `WLG,PMR,ZQN`",
    )

    radius_km = graphene.Int(required=False, description='The rupture/location intersection radius in km')

    filter_set_options = graphene.Field(FilterSetLogicOptions)

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

    # DEFAULT_LOCATION_OPTION: SetOperationEnum = SetOperationEnum.INTERSECTION.value

    filter_set_options = graphene.Field(
        FilterSetLogicOptionsInput,
        required=False,
        default_value=dict(
            multiple_locations=SetOperationEnum.INTERSECTION.value,  # type: ignore
            multiple_faults=SetOperationEnum.UNION.value,  # type: ignore
            locations_and_faults=SetOperationEnum.INTERSECTION.value,  # type: ignore
        ),
    )


class FilterRupturesArgs(FilterRupturesArgsBase, graphene.ObjectType):
    """Arguments FilterRupturesArgs"""

    filter_set_options = graphene.Field(FilterSetLogicOptions)
