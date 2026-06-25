import graphene

# moved to the graphene-free geojson_style_util; re-exported here for the legacy graphene
# modules that still import it from this module (all deleted at cutover).
from solvis_graphql_api.geojson_style_util import apply_geojson_style  # noqa: F401


class GeojsonLineStyleArgumentsBase:
    """Defines styling arguments for geojson line features,

    ref https://academy.datawrapper.de/article/177-how-to-style-your-markers-before-importing-them-to-datawrapper
    """

    stroke_color = graphene.String(
        default_value="green",
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width = graphene.Int(default_value=1, description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(default_value=1.0, description="a number between 0 and 1.0")


class GeojsonAreaStyleArgumentsBase:
    """Defines styling arguments for geojson features"""

    stroke_color = graphene.String(
        default_value="green",
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width = graphene.Int(default_value=1, description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(default_value=1.0, description="a number between 0 and 1.0")
    fill_color = graphene.String(
        default_value="green",
        description='fill colour as Hex code ("#cc0000") or HTML color names ("royalblue") )',
    )
    fill_opacity = graphene.Float(description="0-1.0", default_value=1.0)


class GeojsonLineStyleArgumentsInput(GeojsonLineStyleArgumentsBase, graphene.InputObjectType):
    """Defines styling arguments for geojson features"""


class GeojsonLineStyleArguments(GeojsonLineStyleArgumentsBase, graphene.ObjectType):
    """Defines styling arguments for geojson features"""


class GeojsonAreaStyleArgumentsInput(GeojsonAreaStyleArgumentsBase, graphene.InputObjectType):
    """Defines styling arguments for geojson features"""


class GeojsonAreaStyleArguments(GeojsonAreaStyleArgumentsBase, graphene.ObjectType):
    """Defines styling arguments for geojson features"""
