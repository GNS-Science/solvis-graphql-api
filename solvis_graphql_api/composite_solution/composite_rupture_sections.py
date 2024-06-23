"""The API schema for composite solutions."""

import json
import logging

import graphene
import pandas as pd

from solvis_graphql_api.color_scale import (
    ColorScale,
    ColorScaleArgsInput,
    ColourScaleNormaliseEnum,
    get_colour_scale,
    get_colour_values,
)
from solvis_graphql_api.geojson_style import GeojsonAreaStyleArgumentsInput, GeojsonLineStyleArgumentsInput

from .cached import fault_section_aggregates_gdf, matched_rupture_sections_gdf
from .composite_solution import FilterRupturesArgs

log = logging.getLogger(__name__)


def get_fault_section_aggregates(filter_args, trace_only=False):
    return fault_section_aggregates_gdf(
        filter_args.model_id,
        filter_args.fault_system,
        tuple(filter_args.location_ids),
        filter_args.radius_km,
        min_rate=filter_args.minimum_rate or 1e-20,
        max_rate=filter_args.maximum_rate,
        min_mag=filter_args.minimum_mag,
        max_mag=filter_args.maximum_mag,
        filter_set_options=frozenset(dict(filter_args.filter_set_options).items()),
        trace_only=trace_only,
        corupture_fault_names=tuple(filter_args.corupture_fault_names),
    )


class MagFreqDist(graphene.ObjectType):
    bin_center = graphene.Float()
    rate = graphene.Float()
    cumulative_rate = graphene.Float()


class CompositeRuptureSections(graphene.ObjectType):
    """
    A collection of ruptures and their fault sections that have a geojson represention.  They also
    have a set of attributes derived from the composite solution e.g. rate_weighted_mean etc

    Key attributes:
     - filter_arguments contains the filter criteria used to find the ruptures.
     - fault_surfaces is a geojson feature file based on the geometry from the undelying rutpure set.
       It may by styled by some attribute of the faults section.
     - mfd_histogram is the MFD table summarise the set of ruptures.

    """

    model_id = graphene.String()
    rupture_count = graphene.Int()
    section_count = graphene.Int()
    filter_arguments = graphene.Field(FilterRupturesArgs)

    # these may be useful for calculating color scales
    max_magnitude = graphene.Float(description="maximum rupture magnitude from the contributing solutions.")
    min_magnitude = graphene.Float(description="minimum rupture magnitude from the contributing solutions.")
    max_participation_rate = graphene.Float(
        description="maximum section participation rate (sum of rate_weighted_mean.sum) over the contributing"
        " solutions."
    )
    min_participation_rate = graphene.Float(
        description="minimum section participation rate (sum of rate_weighted_mean.sum) over the contributing"
        " solutions."
    )

    fault_surfaces = graphene.Field(
        graphene.JSONString,
        color_scale=graphene.Argument(
            ColorScaleArgsInput,
            required=False,
            # default_value=ColorScaleArgs()
        ),
        style=graphene.Argument(
            GeojsonAreaStyleArgumentsInput,
            required=False,
            # default_value=GeojsonAreaStyleArguments()
        ),
    )

    fault_traces = graphene.Field(
        graphene.JSONString,
        color_scale=graphene.Argument(
            ColorScaleArgsInput,
            required=False,
            # default_value=ColorScaleArgs()
        ),
        style=graphene.Argument(
            GeojsonLineStyleArgumentsInput,
            required=False,
            # default_value=GeojsonLineStyleArguments()
        ),
    )

    mfd_histogram = graphene.List(MagFreqDist, description="magnitude frequency distribution of the filtered rutpures.")

    color_scale = graphene.Field(
        ColorScale,
        name=graphene.Argument(graphene.String),
        normalization=graphene.Argument(ColourScaleNormaliseEnum, required=False),
        min_value=graphene.Argument(graphene.Float, required=False),
        max_value=graphene.Argument(graphene.Float, required=False),
    )

    def resolve_color_scale(root, info, name, **args):
        min_value = args.get('min_value') or CompositeRuptureSections.resolve_min_participation_rate(root, info)
        max_value = args.get('max_value') or CompositeRuptureSections.resolve_max_participation_rate(root, info)
        normalization = args.get('normalization') or ColourScaleNormaliseEnum.LOG.value

        log.debug("resolve_color_scale(name: %s args: %s)" % (name, args))
        return get_colour_scale(color_scale=name, color_scale_normalise=normalization, vmax=max_value, vmin=min_value)

    def resolve_mfd_histogram(root, info, *args, **kwargs):
        filter_args = root.filter_arguments

        df0 = matched_rupture_sections_gdf(
            filter_args.model_id,
            filter_args.fault_system,
            tuple(filter_args.location_ids),
            filter_args.radius_km,
            min_rate=filter_args.minimum_rate or 1e-20,
            max_rate=filter_args.maximum_rate,
            min_mag=filter_args.minimum_mag,
            max_mag=filter_args.maximum_mag,
            filter_set_options=frozenset(dict(filter_args.filter_set_options).items()),
            corupture_fault_names=tuple(filter_args.corupture_fault_names),
        )

        # TODO - move this function into solvis (see solvis.mfd_hist)
        def build_mfd(
            fault_sections_gdf: pd.DataFrame,
            rate_col: str,
            magnitude_col: str,
            min_mag: float = 6.8,
            max_mag: float = 9.8,
        ) -> pd.DataFrame:
            bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
            df = pd.DataFrame({"rate": fault_sections_gdf[rate_col], "magnitude": fault_sections_gdf[magnitude_col]})

            df["bins"] = pd.cut(df["magnitude"], bins=bins)
            df["bin_center"] = df["bins"].apply(lambda x: x.mid)
            df = df.drop(columns=["magnitude"])
            # df.groupby "observed" parameter default will change to True in
            # later Pandas versions, so marking it as explicitly False to
            # maintain existing behaviour.
            #
            # See:
            # - https://pandas.pydata.org/pandas-docs/stable/whatsnew/v2.1.0.html#deprecations
            # - https://github.com/pandas-dev/pandas/issues/43999
            df = pd.DataFrame(df.groupby(df.bin_center, observed=False).sum(numeric_only=True))

            # reverse cumsum
            df['cumulative_rate'] = df.loc[::-1, 'rate'].cumsum()[::-1]
            df = df.reset_index()
            df.bin_center = pd.to_numeric(df.bin_center)
            df = df[df.bin_center.between(min_mag, max_mag)]
            return df

        df = build_mfd(df0, "rate_weighted_mean", "Magnitude")
        for row in df.itertuples():
            yield row

    def resolve_min_magnitude(root, info):
        filter_args = root.filter_arguments
        fault_sections_gdf = get_fault_section_aggregates(filter_args)
        return fault_sections_gdf['Magnitude.min'].min()

    def resolve_max_magnitude(root, info):
        filter_args = root.filter_arguments
        fault_sections_gdf = get_fault_section_aggregates(filter_args)
        return fault_sections_gdf['Magnitude.max'].max()

    def resolve_min_participation_rate(root, info):
        filter_args = root.filter_arguments
        fault_sections_gdf = get_fault_section_aggregates(filter_args)
        return fault_sections_gdf['rate_weighted_mean.sum'].min()

    def resolve_max_participation_rate(root, info):
        filter_args = root.filter_arguments
        fault_sections_gdf = get_fault_section_aggregates(filter_args)
        return fault_sections_gdf['rate_weighted_mean.sum'].max()

    def resolve_section_count(root, info):
        filter_args = root.filter_arguments
        fault_sections_gdf = get_fault_section_aggregates(filter_args)
        return fault_sections_gdf.shape[0]

    def resolve_fault_surfaces(root, info, *args, **kwargs):
        filter_args = root.filter_arguments
        color_scale_args = kwargs.get('color_scale')
        style_args = kwargs.get('style')

        log.info('resolve_fault_surfaces args: %s filter_args:%s' % (kwargs, filter_args))

        fault_sections_gdf = get_fault_section_aggregates(filter_args)

        if color_scale_args:
            color_values = get_colour_values(
                color_scale=color_scale_args.name,
                color_scale_vmax=color_scale_args.max_value or fault_sections_gdf['rate_weighted_mean.sum'].max(),
                color_scale_vmin=color_scale_args.min_value or fault_sections_gdf['rate_weighted_mean.sum'].min(),
                color_scale_normalise=color_scale_args.normalisation
                or ColourScaleNormaliseEnum.LOG.value,  # type: ignore
                values=tuple(fault_sections_gdf['rate_weighted_mean.sum'].tolist()),
            )

            log.debug('cacheable_hazard_map colour map ')  # % (t3 - t2))
            log.debug('get_colour_values cache_info: %s' % str(get_colour_values.cache_info()))
        else:
            color_values = None

        if style_args or color_scale_args:
            fill_color = style_args.fill_color
            stroke_color = style_args.stroke_color
            fill_opacity = style_args.fill_opacity or 0.5
            stroke_width = style_args.stroke_width or 1
            stroke_opacity = style_args.stroke_opacity or 1

            fault_sections_gdf['fill'] = color_values or fill_color
            fault_sections_gdf['fill-opacity'] = fill_opacity  # for n in values]
            fault_sections_gdf['stroke'] = color_values or stroke_color
            fault_sections_gdf['stroke-width'] = stroke_width
            fault_sections_gdf['stroke-opacity'] = stroke_opacity

        log.debug(f"columns: {fault_sections_gdf.columns}")
        fault_sections_gdf = fault_sections_gdf.drop(
            columns=[
                'rate_weighted_mean.max',
                'rate_weighted_mean.min',
                'rate_weighted_mean.mean',
                'Target Slip Rate',
                'Target Slip Rate StdDev',
            ]
        )
        # import solvis
        # solvis.export_geojson(fault_sections_gdf, 'fault_surfaces.geojson', indent=2)

        return json.loads(fault_sections_gdf.to_json())

    def resolve_fault_traces(root, info, *args, **kwargs):
        filter_args = root.filter_arguments
        color_scale_args = kwargs.get('color_scale')  # root.color_scale_arguments
        style_args = kwargs.get('style')

        log.info('resolve_fault_surfaces args: %s filter_args:%s' % (kwargs, filter_args))

        fault_sections_gdf = get_fault_section_aggregates(filter_args, trace_only=True)

        if color_scale_args:
            color_values = get_colour_values(
                color_scale=color_scale_args.name,
                color_scale_vmax=color_scale_args.max_value or fault_sections_gdf['rate_weighted_mean.sum'].max(),
                color_scale_vmin=color_scale_args.min_value or fault_sections_gdf['rate_weighted_mean.sum'].min(),
                color_scale_normalise=color_scale_args.normalisation
                or ColourScaleNormaliseEnum.LOG.value,  # type: ignore
                values=tuple(fault_sections_gdf['rate_weighted_mean.sum'].tolist()),
            )

            log.debug('cacheable_hazard_map colour map ')  # % (t3 - t2))
            log.debug('get_colour_values cache_info: %s' % str(get_colour_values.cache_info()))

        if style_args or color_scale_args:
            stroke_width = style_args.stroke_width if style_args else 1
            stroke_opacity = style_args.stroke_opacity if style_args else 1

            fault_sections_gdf['stroke'] = color_values if color_scale_args else style_args.stroke_color
            fault_sections_gdf['stroke-width'] = stroke_width
            fault_sections_gdf['stroke-opacity'] = stroke_opacity
            # fault_sections_gdf['fill-opacity'] = stroke_opacity  # TODO remove again
            # fault_sections_gdf['fill'] = color_values if color_scale_args else style_args.stroke_color

        fault_sections_gdf = fault_sections_gdf.drop(
            columns=[
                'rate_weighted_mean.max',
                'rate_weighted_mean.min',
                'rate_weighted_mean.mean',
                'Target Slip Rate',
                'Target Slip Rate StdDev',
            ]
        )
        # import solvis
        # solvis.export_geojson(fault_sections_gdf, 'fault_traces.geojson', indent=2)

        return json.loads(fault_sections_gdf.to_json())
