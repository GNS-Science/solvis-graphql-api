"""The API schema for conposite solutions."""

import json
import logging

import graphene

from solvis_graphql_api.color_scale import ColorScale, ColourScaleNormaliseEnum, get_colour_scale, get_colour_values

from .cached import fault_section_aggregates_gdf

log = logging.getLogger(__name__)


class CompositeRuptureSections(graphene.ObjectType):
    model_id = graphene.String()
    rupture_count = graphene.Int()
    section_count = graphene.Int()

    # these may be useful for calculating color scales
    max_magnitude = graphene.Float(description="maximum magnitude from contributing solutions")
    min_magnitude = graphene.Float(description="minimum magnitude from contributing solutions")
    max_participation_rate = graphene.Float(
        description="maximum section participation rate (sum of rate_weighted_mean.sum) over the contributing solutions"
    )
    min_participation_rate = graphene.Float(
        description="minimum section participation rate (sum of rate_weighted_mean.sum) over the contributing solutions"
    )

    fault_surfaces = graphene.Field(graphene.JSONString)

    color_scale = graphene.Field(
        ColorScale,
        name=graphene.Argument(graphene.String),
        normalization=graphene.Argument(ColourScaleNormaliseEnum, required=False),
        min_value=graphene.Argument(graphene.Float, required=False),
        max_value=graphene.Argument(graphene.Float, required=False),
    )

    def resolve_color_scale(root, info, name, **args):
        min_value = args.get('min_value') or root.min_participation_rate
        max_value = args.get('max_value') or root.max_participation_rate
        normalization = args.get('normalization') or ColourScaleNormaliseEnum.LOG.value

        log.debug("resolve_color_scale(name: %s args: %s)" % (name, args))
        return get_colour_scale(color_scale=name, color_scale_normalise=normalization, vmax=max_value, vmin=min_value)


def filtered_rupture_sections(filter_args, color_scale_args, surface_style_args, **kwargs) -> CompositeRuptureSections:

    log.info('filtered_rupture_sections args: %s filter_args:%s' % (kwargs, filter_args))

    min_rate = filter_args.get('minimum_rate') or 1e-20

    fault_sections_gdf = fault_section_aggregates_gdf(
        filter_args['model_id'],
        filter_args['fault_system'],
        tuple(filter_args['location_ids']),
        filter_args['radius_km'],
        min_rate=min_rate,
        max_rate=filter_args.get('maximum_rate'),
        min_mag=filter_args.get('minimum_mag'),
        max_mag=filter_args.get('maximum_mag'),
        union=False,
    )

    color_values = get_colour_values(
        color_scale=color_scale_args['name'],
        color_scale_vmax=color_scale_args.get('max_value') or fault_sections_gdf['rate_weighted_mean.sum'].max(),
        color_scale_vmin=color_scale_args.get('min_value') or fault_sections_gdf['rate_weighted_mean.sum'].min(),
        color_scale_normalise=color_scale_args.get('normalisation', ColourScaleNormaliseEnum.LOG.value),  # type: ignore
        values=tuple(fault_sections_gdf['rate_weighted_mean.sum'].tolist()),
    )

    log.debug('cacheable_hazard_map colour map ')  # % (t3 - t2))
    log.debug('get_colour_values cache_info: %s' % str(get_colour_values.cache_info()))

    fill_opacity = surface_style_args.get('fill_opacity', 0.5)
    stroke_width = surface_style_args.get('stroke_width', 1)
    stroke_opacity = surface_style_args.get('stroke_opacity', 1)

    fault_sections_gdf['fill'] = color_values
    fault_sections_gdf['fill-opacity'] = fill_opacity  # for n in values]
    fault_sections_gdf['stroke'] = color_values
    fault_sections_gdf['stroke-width'] = stroke_width
    fault_sections_gdf['stroke-opacity'] = stroke_opacity

    # print(fault_sections_gdf.info())
    """
    <class 'geopandas.geodataframe.GeoDataFrame'>
    Float64Index: 271 entries, 0.0 to 270.0
    Data columns (total 26 columns):
     #   Column                   Non-Null Count  Dtype
    ---  ------                   --------------  -----
     0   Magnitude.count          271 non-null    int64
     1   Magnitude.max            271 non-null    float32
     2   Magnitude.min            271 non-null    float32
     3   rate_weighted_mean.max   271 non-null    float32
     4   rate_weighted_mean.mean  271 non-null    float32
     5   rate_weighted_mean.min   271 non-null    float32
     6   rate_weighted_mean.sum   271 non-null    float32
     7   FaultID                  271 non-null    int64
     8   FaultName                271 non-null    object
     9   DipDeg                   271 non-null    float64
     10  Rake                     271 non-null    float64
     11  LowDepth                 271 non-null    float64
     12  UpDepth                  271 non-null    float64
     13  DipDir                   271 non-null    float64
     14  AseismicSlipFactor       271 non-null    float64
     15  CouplingCoeff            271 non-null    float64
     16  SlipRate                 271 non-null    float64
     17  ParentID                 271 non-null    int64
     18  ParentName               271 non-null    object
     19  SlipRateStdDev           271 non-null    float64
     20  geometry                 271 non-null    geometry
     21  fill                     271 non-null    object
     22  fill-opacity             271 non-null    float64
     23  stroke                   271 non-null    object
     24  stroke-width             271 non-null    int64
     25  stroke-opacity           271 non-null    int64
    dtypes: float32(6), float64(10), geometry(1), int64(5), object(4)
    memory usage: 50.8+ KB
    """

    fault_sections_gdf = fault_sections_gdf.drop(
        columns=[
            'rate_weighted_mean.max',
            'rate_weighted_mean.min',
            'rate_weighted_mean.mean',
            "SlipRate",
            "SlipRateStdDev",
        ]
    )
    # import solvis
    # solvis.export_geojson(fault_sections_gdf, 'q0.geojson', indent=2)

    return CompositeRuptureSections(
        model_id=filter_args.get('model_id'),
        fault_surfaces=json.loads(fault_sections_gdf.to_json()),
        section_count=fault_sections_gdf.shape[0],
        max_magnitude=fault_sections_gdf['Magnitude.max'].max(),
        min_magnitude=fault_sections_gdf['Magnitude.min'].min(),
        max_participation_rate=fault_sections_gdf['rate_weighted_mean.sum'].max(),
        min_participation_rate=fault_sections_gdf['rate_weighted_mean.sum'].min(),
    )
