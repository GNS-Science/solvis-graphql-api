"""The main API schema."""

import logging
from typing import List

import graphene
import shapely
from graphene import relay
from nzshm_common.location.location import location_by_id

from solvis_graphql_api.composite_solution import cached
from solvis_graphql_api.geojson_style import (
    GeojsonAreaStyleArgumentsInput,
    apply_geojson_style,
)

log = logging.getLogger(__name__)


class LocationDetail(graphene.ObjectType):
    """Represents the internal details of a given location"""

    class Meta:
        interfaces = (relay.Node,)

    location_id = graphene.String()
    name = graphene.String()
    latitude = graphene.Float()
    longitude = graphene.Float()

    radius_geojson = graphene.Field(
        graphene.JSONString,
        radius_km=graphene.Argument(
            graphene.Int, required=True, description="polygon radius (km)."
        ),
        style=graphene.Argument(
            GeojsonAreaStyleArgumentsInput,
            required=False,
            description="feature style for the geojson.",
            default_value=dict(
                stroke_color="black", stroke_width=1, stroke_opacity=1.0
            ),
        ),
    )

    def resolve_id(root, info, *args, **kwargs):
        log.info("resolve_id")
        # print(root)
        return root.location_id

    def resolve_location_id(root, info):
        log.info("resolve_location_id")
        return root.location_id

    def resolve_radius_geojson(root, info, radius_km, style, *args, **kwargs):
        polygon = cached.get_location_polygon(
            radius_km, lat=root.latitude, lon=root.longitude
        )
        features = dict(
            features=[
                dict(
                    id=root.location_id,
                    type="Feature",
                    geometry=shapely.geometry.mapping(polygon),
                )
            ]
        )
        # return features
        return apply_geojson_style(features, style)


class LocationDetailConnection(relay.Connection):
    class Meta:
        node = LocationDetail

    total_count = graphene.Int()


def get_location_detail_list(
    location_ids: List[str], **kwarg
) -> LocationDetailConnection:
    log.info("get_location_detail_list: %s" % location_ids)

    nodes = [
        LocationDetail(
            location_id=loc["id"],
            name=loc["name"],
            latitude=loc["latitude"],
            longitude=loc["longitude"],
        )
        for loc in [location_by_id(location_id) for location_id in location_ids]
    ]

    print(nodes)
    edges = [LocationDetailConnection.Edge(node=node) for idx, node in enumerate(nodes)]

    # REF https://stackoverflow.com/questions/46179559/custom-connectionfield-in-graphene
    connection_field = relay.ConnectionField.resolve_connection(
        LocationDetailConnection, {}, edges
    )
    connection_field.total_count = len(edges)
    connection_field.edges = edges
    return connection_field
