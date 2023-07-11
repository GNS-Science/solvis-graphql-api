"""The API schema for FilterSetLogicOptions."""

import graphene


class SetOperationEnum(graphene.Enum):
    UNION = 1
    INTERSECTION = 2
    DIFFERENCE = 3


class FilterSetLogicOptionsBase:
    """Let the user define how the result sets are combined"""

    multiple_locations = graphene.Field(SetOperationEnum, default_value=SetOperationEnum.INTERSECTION)
    multiple_faults = graphene.Field(SetOperationEnum, default_value=SetOperationEnum.UNION)
    locations_and_faults = graphene.Field(SetOperationEnum, default_value=SetOperationEnum.INTERSECTION)


class FilterSetLogicOptionsInput(FilterSetLogicOptionsBase, graphene.InputObjectType):
    pass


class FilterSetLogicOptions(FilterSetLogicOptionsBase, graphene.ObjectType):
    pass
