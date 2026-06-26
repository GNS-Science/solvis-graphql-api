"""Graphene-free geojson styling helper.

The pure dict-merge extracted out of the legacy graphene ``geojson_style`` module so the
Strawberry schema can style geojson without importing graphene. The graphene module
re-exports this during the transition; it (and its graphene style types) are deleted at cutover.
"""


def apply_geojson_style(geojson: dict, style: dict) -> dict:
    """ "merge each features properties dict with style dict"""
    new_dict = dict(geojson)
    for feature in new_dict["features"]:
        current_props = feature.get("properties", {})
        feature["properties"] = {
            **current_props,
            **{
                "stroke-color": style.get("stroke_color"),
                "stroke-opacity": style.get("stroke_opacity"),
                "stroke-width": style.get("stroke_width"),
            },
        }
        # add fill attributes
        for extra in ["fill_color", "fill_opacity"]:
            if style.get(extra):
                feature["properties"][extra.replace("_", "-")] = style.get(extra)
    return new_dict
