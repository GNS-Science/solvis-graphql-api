"""The API schema for FilterSetLogicOptions."""

from typing import Any, Tuple

import graphene
import solvis.inversion_solution.typing


def _solvis_join(filter_set_options: Tuple[Any], member: str) -> solvis.inversion_solution.typing.SetOperationEnum:
    """Helper: Convert a Graphene filter set option to Solvis native Enum type."""
    return solvis.inversion_solution.typing.SetOperationEnum(dict(filter_set_options)[member])


# Construct graphene Enum from native Solvis type.
SetOperationEnum = graphene.Enum.from_enum(solvis.inversion_solution.typing.SetOperationEnum)


class FilterSetLogicOptionsBase:
    """Let the user define how the result sets are combined"""

    multiple_locations = graphene.Field(
        SetOperationEnum, default_value=SetOperationEnum.INTERSECTION.value  # type: ignore
    )
    multiple_faults = graphene.Field(SetOperationEnum, default_value=SetOperationEnum.UNION.value)  # type: ignore
    locations_and_faults = graphene.Field(
        SetOperationEnum, default_value=SetOperationEnum.INTERSECTION.value  # type: ignore
    )


class FilterSetLogicOptionsInput(FilterSetLogicOptionsBase, graphene.InputObjectType):
    pass


class FilterSetLogicOptions(FilterSetLogicOptionsBase, graphene.ObjectType):
    pass
