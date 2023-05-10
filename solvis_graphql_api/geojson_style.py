import graphene
from typing import Dict


def apply_geojson_style(geojson: Dict, style: Dict) -> Dict:
    """ "merge each features properties dict with style dict"""
    new_dict = dict(geojson)
    for feature in new_dict['features']:
        current_props = feature.get("properties", {})
        feature['properties'] = {
            **current_props,
            **{
                "stroke-color": style.get('stroke_color'),
                "stroke-opacity": style.get('stroke_opacity'),
                "stroke-width": style.get('stroke_width'),
            },
        }
        # add fill attributes
        for extra in ['fill_color', 'fill_opacity']:
            if style.get(extra):
                feature['properties'][extra.replace('_', '-')] = style.get(extra)
    return new_dict


class GeojsonLineStyleArgumentsBase:
    """Defines styling arguments for geojson line features,

    ref https://academy.datawrapper.de/article/177-how-to-style-your-markers-before-importing-them-to-datawrapper
    """

    stroke_color = graphene.String(
        default_value='green',
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width = graphene.Int(default_value=1, description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(default_value=1.0, description="a number between 0 and 1.0")


class GeojsonAreaStyleArgumentsBase:
    """Defines styling arguments for geojson features"""

    stroke_color = graphene.String(
        default_value='green',
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width = graphene.Int(default_value=1, description="a number between 0 and 20.")
    stroke_opacity = graphene.Float(default_value=1.0, description="a number between 0 and 1.0")
    fill_color = graphene.String(
        default_value='green', description='fill colour as Hex code ("#cc0000") or HTML color names ("royalblue") )'
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
