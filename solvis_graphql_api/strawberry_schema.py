"""Strawberry schema — Graphene parity port.

Reproduces the legacy Graphene SDL (``schema.legacy.graphql``) one-for-one. Type shapes
live here; the heavy compute is reused from the existing Graphene-free helpers
(``composite_solution.cached``, ``color_scale``, ``geojson_style``, ``schema`` pagination).

Parity traps honoured:
- root type is ``QueryRoot`` (not Strawberry's default ``Query``)
- a **custom** ``Node`` interface (``id: ID!``), NOT ``strawberry.relay`` (which emits ``GlobalID``)
- ``auto_camel_case=False``; relay ``PageInfo``/edge fields keep their camelCase names explicitly
- optional args with no SDL default use ``strawberry.UNSET`` (suppresses ``= null``); only
  ``ColorScaleArgsInput.normalisation`` keeps an explicit ``= null`` (``= None``)
"""

import enum
import json
from types import SimpleNamespace
from typing import TYPE_CHECKING, Annotated, Any, NewType

import graphql_relay
import solvis.solution.typing
import strawberry
from nzshm_common.location.location import LOCATION_LISTS, LOCATIONS, location_by_id
from strawberry.schema.config import StrawberryConfig

import solvis_graphql_api
from solvis_graphql_api.color_scale.compute import compute_colour_scale, get_colour_values
from solvis_graphql_api.composite_solution import cached
from solvis_graphql_api.composite_solution.cached import rupture_detail
from solvis_graphql_api.geojson_style_util import apply_geojson_style

RADII: list[dict[str, Any]] = [
    {"id": 1, "radii": [10e3]},
    {"id": 2, "radii": [10e3, 20e3]},
    {"id": 3, "radii": [10e3, 20e3, 30e3]},
    {"id": 4, "radii": [10e3, 20e3, 30e3, 40e3]},
    {"id": 5, "radii": [10e3, 20e3, 30e3, 40e3, 50e3]},
    {"id": 6, "radii": [10e3, 20e3, 30e3, 40e3, 50e3, 100e3]},
    {"id": 7, "radii": [10e3, 20e3, 30e3, 40e3, 50e3, 100e3, 200e3]},
]

# --------------------------------------------------------------------------- scalars

if TYPE_CHECKING:
    # mypy: treat the custom scalar as an opaque value type (it can't infer a NewType-backed
    # strawberry.scalar() assignment as a usable type — the classic `valid-type` gotcha)
    JSONString = object
else:
    JSONString = strawberry.scalar(
        NewType("JSONString", object),
        serialize=lambda v: v if isinstance(v, str) else json.dumps(v),
        parse_value=lambda v: json.loads(v),
        description=(
            "Allows use of a JSON String for input / output from the GraphQL schema.\n\n"
            "Use of this type is *not recommended* as you lose the benefits of having a defined, static\n"
            "schema (one of the key benefits of GraphQL)."
        ),
    )

# --------------------------------------------------------------------------- interfaces


@strawberry.interface(description="An object with an ID")
class Node:
    # default UNSET so implementing types (which override `id` with a resolver) don't carry
    # it as a required __init__ arg; the SDL stays `id: ID!`.
    id: strawberry.ID = strawberry.field(default=strawberry.UNSET, description="The ID of the object")


# --------------------------------------------------------------------------- enums


@strawberry.enum
class ColourScaleNormaliseEnum(enum.Enum):
    LOG = "log"
    LIN = "lin"


if TYPE_CHECKING:
    # a concrete stub so mypy treats SetOperationEnum as a usable type even when solvis is
    # untyped (ignore_missing_imports); member names match the real solvis enum.
    class SetOperationEnum(enum.Enum):
        UNION = "UNION"
        INTERSECTION = "INTERSECTION"
        DIFFERENCE = "DIFFERENCE"
        SYMMETRIC_DIFFERENCE = "SYMMETRIC_DIFFERENCE"
else:
    SetOperationEnum = strawberry.enum(
        solvis.solution.typing.SetOperationEnum, description=solvis.solution.typing.SetOperationEnum.__doc__
    )

# --------------------------------------------------------------------------- input types


@strawberry.input(description="Defines styling arguments for geojson features")
class GeojsonAreaStyleArgumentsInput:
    stroke_color: str | None = strawberry.field(
        default="green",
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width: int | None = strawberry.field(default=1, description="a number between 0 and 20.")
    stroke_opacity: float | None = strawberry.field(default=1.0, description="a number between 0 and 1.0")
    fill_color: str | None = strawberry.field(
        default="green",
        description='fill colour as Hex code ("#cc0000") or HTML color names ("royalblue") )',
    )
    fill_opacity: float | None = strawberry.field(default=1.0, description="0-1.0")


@strawberry.input(description="Defines styling arguments for geojson features")
class GeojsonLineStyleArgumentsInput:
    stroke_color: str | None = strawberry.field(
        default="green",
        description='stroke (line) colour as hex code ("#cc0000") or HTML color name ("royalblue")',
    )
    stroke_width: int | None = strawberry.field(default=1, description="a number between 0 and 20.")
    stroke_opacity: float | None = strawberry.field(default=1.0, description="a number between 0 and 1.0")


@strawberry.input(description="Arguments passed as ColorScaleArgsInput")
class ColorScaleArgsInput:
    name: str | None = "inferno"
    min_value: float | None = strawberry.UNSET
    max_value: float | None = strawberry.UNSET
    normalisation: ColourScaleNormaliseEnum | None = None


@strawberry.input
class FilterSetLogicOptionsInput:
    multiple_locations: SetOperationEnum | None = SetOperationEnum.INTERSECTION
    multiple_faults: SetOperationEnum | None = SetOperationEnum.UNION
    locations_and_faults: SetOperationEnum | None = SetOperationEnum.INTERSECTION


@strawberry.input
class CompositeRuptureDetailArgs:
    model_id: str | None = strawberry.UNSET
    fault_system: str | None = strawberry.field(
        default=strawberry.UNSET, description="Unique ID of the fault system e.g. `PUY`"
    )
    rupture_index: int | None = strawberry.UNSET


@strawberry.input
class SimpleSortRupturesArgs:
    attribute: str | None = strawberry.UNSET
    ascending: bool | None = strawberry.UNSET


@strawberry.input(description="Arguments passed as FilterRupturesArgs")
class FilterRupturesArgsInput:
    model_id: str = strawberry.field(description="The ID of NSHM model")
    fault_system: str = strawberry.field(description="The fault systems [`HIK`, `PUY`, `CRU`]")
    corupture_fault_names: list[str | None] | None = strawberry.field(
        default_factory=list,
        description="Optional list of parent fault names. Result will only include ruptures that include parent "
        "fault sections",
    )
    location_ids: list[str | None] | None = strawberry.field(
        default_factory=list,
        description="Optional list of locations ids for proximity filtering e.g. `WLG,PMR,ZQN`",
    )
    radius_km: int | None = strawberry.field(
        default=strawberry.UNSET, description="The rupture/location intersection radius in km"
    )
    filter_set_options: FilterSetLogicOptionsInput | None = strawberry.field(
        # a plain mapping (not an input instance) so the SDL default renders AND graphql-core
        # coerces it at execution — an instance default trips strawberry's argument coercion
        default_factory=lambda: {
            "multiple_locations": SetOperationEnum.INTERSECTION,
            "multiple_faults": SetOperationEnum.UNION,
            "locations_and_faults": SetOperationEnum.INTERSECTION,
        }
    )
    minimum_rate: float | None = strawberry.field(
        default=strawberry.UNSET,
        description="Constrain to fault_sections having a annual rate above the value supplied.",
    )
    maximum_rate: float | None = strawberry.field(
        default=strawberry.UNSET,
        description="Constrain to fault_sections having a annual rate below the value supplied.",
    )
    minimum_mag: float | None = strawberry.field(
        default=strawberry.UNSET,
        description="Constrain to fault_sections having a magnitude above the value supplied.",
    )
    maximum_mag: float | None = strawberry.field(
        default=strawberry.UNSET,
        description="Constrain to fault_sections having a magnitude below the value supplied.",
    )


# the legacy arg default is a *partial* 3-key style ({stroke_color, stroke_width, stroke_opacity}),
# expressed as a plain mapping (as graphene did) so graphql-core renders it in the SDL AND coerces
# it cleanly at execution when the arg is omitted (an input *instance* default trips coercion).
_AREA_STYLE_ARG_DEFAULT: Any = {"stroke_color": "black", "stroke_width": 1, "stroke_opacity": 1}


def _style_dict(style) -> dict:
    if style is None:
        return {}
    d = style if isinstance(style, dict) else strawberry.asdict(style)
    return {k: v for k, v in d.items() if v is not strawberry.UNSET}


# --------------------------------------------------------------------------- output types


@strawberry.type
class HexRgbValueMapping:
    levels: list[float | None] | None = None
    hexrgbs: list[str | None] | None = None


@strawberry.type
class ColorScale:
    name: str | None = None
    min_value: float | None = None
    max_value: float | None = None
    normalisation: ColourScaleNormaliseEnum | None = None
    color_map: HexRgbValueMapping | None = None


@strawberry.type(
    description="The Relay compliant `PageInfo` type, containing data necessary to paginate this connection."
)
class PageInfo:
    has_next_page: bool = strawberry.field(
        name="hasNextPage", description="When paginating forwards, are there more items?"
    )
    has_previous_page: bool = strawberry.field(
        name="hasPreviousPage", description="When paginating backwards, are there more items?"
    )
    start_cursor: str | None = strawberry.field(
        name="startCursor", default=None, description="When paginating backwards, the cursor to continue."
    )
    end_cursor: str | None = strawberry.field(
        name="endCursor", default=None, description="When paginating forwards, the cursor to continue."
    )


@strawberry.type(description="Represents the internal details of a given location")
class LocationDetail(Node):
    location_id: str | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @strawberry.field(description="The ID of the object")  # type: ignore[misc]  # resolver overrides Node.id field
    def id(self) -> strawberry.ID:
        # graphene relay encodes the node id as base64("LocationDetail:<id>") — reproduce it
        return strawberry.ID(graphql_relay.to_global_id("LocationDetail", self.location_id or ""))

    @strawberry.field
    def radius_geojson(
        self,
        radius_km: Annotated[int, strawberry.argument(description="polygon radius (km).")],
        style: Annotated[
            GeojsonAreaStyleArgumentsInput | None,
            strawberry.argument(description="feature style for the geojson."),
        ] = _AREA_STYLE_ARG_DEFAULT,
    ) -> JSONString | None:
        import shapely

        polygon = cached.get_location_polygon(radius_km, lat=self.latitude, lon=self.longitude)
        features = dict(
            features=[dict(id=self.location_id, type="Feature", geometry=shapely.geometry.mapping(polygon))]
        )
        return apply_geojson_style(features, _style_dict(style))


@strawberry.type(description="A Relay edge containing a `LocationDetail` and its cursor.")
class LocationDetailEdge:
    node: LocationDetail | None = strawberry.field(description="The item at the end of the edge", default=None)
    cursor: str = strawberry.field(description="A cursor for use in pagination")


@strawberry.type
class LocationDetailConnection:
    page_info: PageInfo = strawberry.field(name="pageInfo", description="Pagination data for this connection.")
    edges: list[LocationDetailEdge | None] = strawberry.field(description="Contains the nodes in this connection.")
    total_count: int | None = None


@strawberry.type(description="A complete NSHM model comprising at least one FaultSystemSolution")
class CompositeSolution:
    model_id: str | None = None
    fault_systems: list[str | None] | None = None
    file_url: str | None = strawberry.field(default=None, description="get a URL so one can download the file")


@strawberry.type
class CompositeRuptureDetail(Node):
    model_id: str | None = None
    fault_system: str | None = strawberry.field(default=None, description="Unique ID of the fault system e.g. `PUY`")
    rupture_index: int | None = None
    fault_traces: JSONString | None = None

    def _rupt(self):
        return rupture_detail(self.model_id, self.fault_system, self.rupture_index)

    @strawberry.field(description="The ID of the object")  # type: ignore[misc]  # resolver overrides Node.id field
    def id(self) -> strawberry.ID:
        gid = graphql_relay.to_global_id("CompositeRuptureDetail", f"{self.fault_system}:{self.rupture_index}")
        return strawberry.ID(gid)

    @strawberry.field
    def magnitude(self) -> float | None:
        return round(float(self._rupt()["Magnitude"].iloc[0]), 3)

    @strawberry.field(description="Rupture length in kilometres^2")
    def area(self) -> float | None:
        return round(float(self._rupt()["Area (m^2)"].iloc[0] / 1e6), 0)

    @strawberry.field(description="Rupture length in kilometres)")
    def length(self) -> float | None:
        return round(float(self._rupt()["Length (m)"].iloc[0] / 1e3), 0)

    @strawberry.field(description="average rake angle (degrees) of the entire rupture")
    def rake_mean(self) -> float | None:
        return round(float(self._rupt()["Average Rake (degrees)"].iloc[0]), 1)

    @strawberry.field(description="mean of `rate` * `branch weight` of the contributing solutions")
    def rate_weighted_mean(self) -> float | None:
        return float(self._rupt()["rate_weighted_mean"].iloc[0])

    @strawberry.field(description="maximum rate from contributing solutions")
    def rate_max(self) -> float | None:
        return float(self._rupt()["rate_max"].iloc[0])

    @strawberry.field(description="minimum rate from contributing solutions")
    def rate_min(self) -> float | None:
        return float(self._rupt()["rate_min"].iloc[0])

    @strawberry.field(description="count of model solutions that include this rupture")
    def rate_count(self) -> int | None:
        return int(self._rupt()["rate_count"].iloc[0])

    @strawberry.field
    def fault_surfaces(
        self,
        style: Annotated[
            GeojsonAreaStyleArgumentsInput | None,
            strawberry.argument(description="feature style for rupture trace geojson."),
        ] = _AREA_STYLE_ARG_DEFAULT,
    ) -> JSONString | None:
        return _rupture_fault_surfaces(self.model_id, self.fault_system, self.rupture_index, _style_dict(style))


@strawberry.type(description="A Relay edge containing a `RuptureDetail` and its cursor.")
class RuptureDetailEdge:
    node: CompositeRuptureDetail | None = strawberry.field(
        description="The item at the end of the edge", default=None
    )
    cursor: str = strawberry.field(description="A cursor for use in pagination")


@strawberry.type
class RuptureDetailConnection:
    page_info: PageInfo = strawberry.field(name="pageInfo", description="Pagination data for this connection.")
    edges: list[RuptureDetailEdge | None] = strawberry.field(description="Contains the nodes in this connection.")
    total_count: int | None = None


@strawberry.type
class FilterSetLogicOptions:
    multiple_locations: SetOperationEnum | None = None
    multiple_faults: SetOperationEnum | None = None
    locations_and_faults: SetOperationEnum | None = None


@strawberry.type(description="Arguments FilterRupturesArgs")
class FilterRupturesArgs:
    model_id: str = strawberry.field(description="The ID of NSHM model")
    fault_system: str = strawberry.field(description="The fault systems [`HIK`, `PUY`, `CRU`]")
    corupture_fault_names: list[str | None] | None = strawberry.field(
        default=None,
        description="Optional list of parent fault names. Result will only include ruptures that include parent "
        "fault sections",
    )
    location_ids: list[str | None] | None = strawberry.field(
        default=None,
        description="Optional list of locations ids for proximity filtering e.g. `WLG,PMR,ZQN`",
    )
    radius_km: int | None = strawberry.field(
        default=None, description="The rupture/location intersection radius in km"
    )
    filter_set_options: FilterSetLogicOptions | None = None
    minimum_rate: float | None = strawberry.field(
        default=None, description="Constrain to fault_sections having a annual rate above the value supplied."
    )
    maximum_rate: float | None = strawberry.field(
        default=None, description="Constrain to fault_sections having a annual rate below the value supplied."
    )
    minimum_mag: float | None = strawberry.field(
        default=None, description="Constrain to fault_sections having a magnitude above the value supplied."
    )
    maximum_mag: float | None = strawberry.field(
        default=None, description="Constrain to fault_sections having a magnitude below the value supplied."
    )


@strawberry.type
class MagFreqDist:
    bin_center: float | None = None
    rate: float | None = None
    cumulative_rate: float | None = None


@strawberry.type(
    description=(
        "A collection of ruptures and their fault sections that have a geojson represention.  They also\n"
        "have a set of attributes derived from the composite solution e.g. rate_weighted_mean etc\n\n"
        "Key attributes:\n"
        " - filter_arguments contains the filter criteria used to find the ruptures.\n"
        " - fault_surfaces is a geojson feature file based on the geometry from the undelying rutpure set.\n"
        "   It may by styled by some attribute of the faults section.\n"
        " - mfd_histogram is the MFD table summarise the set of ruptures."
    )
)
class CompositeRuptureSections:
    model_id: str | None = None
    rupture_count: int | None = None
    filter_arguments: FilterRupturesArgs | None = None
    # the strawberry filter input; the resolvers below do all the compute graphene-free
    filter_input: strawberry.Private[Any] = None

    @strawberry.field
    def section_count(self) -> int | None:
        return _fault_section_aggregates(self.filter_input).shape[0]

    @strawberry.field(description="maximum rupture magnitude from the contributing solutions.")
    def max_magnitude(self) -> float | None:
        return _fault_section_aggregates(self.filter_input)["Magnitude.max"].max()

    @strawberry.field(description="minimum rupture magnitude from the contributing solutions.")
    def min_magnitude(self) -> float | None:
        return _fault_section_aggregates(self.filter_input)["Magnitude.min"].min()

    @strawberry.field(
        description="maximum section participation rate (sum of rate_weighted_mean.sum) over the contributing "
        "solutions."
    )
    def max_participation_rate(self) -> float | None:
        return _fault_section_aggregates(self.filter_input)["rate_weighted_mean.sum"].max()

    @strawberry.field(
        description="minimum section participation rate (sum of rate_weighted_mean.sum) over the contributing "
        "solutions."
    )
    def min_participation_rate(self) -> float | None:
        return _fault_section_aggregates(self.filter_input)["rate_weighted_mean.sum"].min()

    @strawberry.field
    def fault_surfaces(
        self,
        color_scale: ColorScaleArgsInput | None = strawberry.UNSET,
        style: GeojsonAreaStyleArgumentsInput | None = strawberry.UNSET,
    ) -> JSONString | None:
        return _fault_surfaces_geojson(self.filter_input, _legacy_color_scale_args(color_scale), _v(style))

    @strawberry.field
    def fault_traces(
        self,
        color_scale: ColorScaleArgsInput | None = strawberry.UNSET,
        style: GeojsonLineStyleArgumentsInput | None = strawberry.UNSET,
    ) -> JSONString | None:
        return _fault_traces_geojson(self.filter_input, _legacy_color_scale_args(color_scale), _v(style))

    @strawberry.field(description="magnitude frequency distribution of the filtered rutpures.")
    def mfd_histogram(self) -> list[MagFreqDist | None] | None:
        return [
            MagFreqDist(bin_center=r.bin_center, rate=r.rate, cumulative_rate=r.cumulative_rate)
            for r in _mfd_histogram_rows(self.filter_input)
        ]

    @strawberry.field
    def color_scale(
        self,
        name: str | None = strawberry.UNSET,
        normalization: ColourScaleNormaliseEnum | None = strawberry.UNSET,
        min_value: float | None = strawberry.UNSET,
        max_value: float | None = strawberry.UNSET,
    ) -> ColorScale | None:
        f = self.filter_input
        # legacy default: a falsy min/max falls back to the participation-rate extremes
        vmin = _v(min_value) or _fault_section_aggregates(f)["rate_weighted_mean.sum"].min()
        vmax = _v(max_value) or _fault_section_aggregates(f)["rate_weighted_mean.sum"].max()
        norm = (normalization.value if normalization not in (None, strawberry.UNSET) else None) or "log"
        cs = compute_colour_scale(color_scale=_v(name), color_scale_normalise=norm, vmax=vmax, vmin=vmin)
        return _to_strawberry_color_scale(cs)


@strawberry.type
class RadiiSet:
    radii_set_id: int | None = strawberry.field(default=None, description="The unique radii_set_id")
    radii: list[int | None] | None = strawberry.field(
        default=None, description="list of dimension in metres defined by the radii set."
    )


@strawberry.type
class Location:
    location_id: str | None = strawberry.field(default=None, description="unique location location_id.")
    name: str | None = strawberry.field(default=None, description="location name.")
    latitude: float | None = strawberry.field(default=None, description="location latitude.")
    longitude: float | None = strawberry.field(default=None, description="location longitude")


@strawberry.type
class LocationList:
    list_id: str | None = strawberry.field(default=None, description="The unique location_list_id")
    location_ids: list[str | None] | None = strawberry.field(default=None, description="list of location codes.")

    @strawberry.field(description="the locations in this list.")
    def locations(self) -> list[Location | None] | None:
        out: list[Location | None] = []
        for loc_id in self.location_ids or []:
            loc = location_by_id(loc_id) if loc_id else None
            if loc:
                out.append(
                    Location(
                        location_id=loc["id"], name=loc["name"], latitude=loc["latitude"], longitude=loc["longitude"]
                    )
                )
        return out


# --------------------------------------------------------------------------- compute adapters


def _to_strawberry_color_scale(cs) -> ColorScale:
    norm = {"log": ColourScaleNormaliseEnum.LOG, "lin": ColourScaleNormaliseEnum.LIN}.get(cs.normalisation)
    levels = cs.levels
    hexrgbs = cs.hexrgbs
    return ColorScale(
        name=cs.name,
        min_value=cs.min_value,
        max_value=cs.max_value,
        normalisation=norm,
        color_map=HexRgbValueMapping(levels=list(levels), hexrgbs=list(hexrgbs)),
    )


def _v(value):
    """strawberry.UNSET -> None (the legacy graphene inputs use None for absent optionals)."""
    return None if value is strawberry.UNSET else value


# field-name → dataframe-column map (was CompositeRuptureDetail.ATTRIBUTE_COLUMN_MAP in graphene)
_ATTRIBUTE_COLUMN_MAP = {
    "rupture_index": "Rupture Index",
    "magnitude": "Magnitude",
    "rake_mean": "Average Rake (degrees)",
    "area": "Area (m^2)",
    "length": "Length (m)",
}


def _auto_sorted(dataframe, sortby_args, min_rate):
    """graphene-free port of composite_solution.schema.auto_sorted_dataframe."""
    import math

    import numpy as np
    import pandas as pd

    by, ascending = [], []
    for idx, itm in enumerate(sortby_args):
        column = _ATTRIBUTE_COLUMN_MAP.get(itm["attribute"], itm["attribute"])
        if len(sortby_args) == 1:
            by.append(column)
            ascending.append(itm.get("ascending", True))
            continue
        if idx == 0:
            if itm["attribute"] == "magnitude":
                bins = np.logspace(np.log10(5.0), np.log10(10.0), 50).tolist()
            else:
                places = abs(math.floor(math.log10(min_rate) + 1))
                bins = np.logspace(np.log10(min_rate), np.log10(1.0), 10 * places).tolist()
            dataframe[column + "_binned"] = pd.cut(dataframe[column], bins=bins, labels=bins[1:])
            column = column + "_binned"
        by.append(column)
        ascending.append(itm.get("ascending", True))
    return dataframe.sort_values(by=by, ascending=ascending)


def _matched_rupture_sections(f: "FilterRupturesArgsInput"):
    """graphene-free wrapper over cached.matched_rupture_sections_gdf using the strawberry input."""
    return cached.matched_rupture_sections_gdf(
        f.model_id,
        f.fault_system,
        tuple(f.location_ids or []),
        _v(f.radius_km),
        min_rate=_v(f.minimum_rate) or 1e-20,
        max_rate=_v(f.maximum_rate),
        min_mag=_v(f.minimum_mag),
        max_mag=_v(f.maximum_mag),
        filter_set_options=frozenset(_fso_dict(f.filter_set_options).items()),
        corupture_fault_names=tuple(f.corupture_fault_names or []),
    )


def _fault_section_aggregates(f: "FilterRupturesArgsInput", trace_only=False):
    """graphene-free port of composite_rupture_sections.get_fault_section_aggregates."""
    return cached.fault_section_aggregates_gdf(
        f.model_id,
        f.fault_system,
        tuple(f.location_ids or []),
        _v(f.radius_km),
        min_rate=_v(f.minimum_rate) or 1e-20,
        max_rate=_v(f.maximum_rate),
        min_mag=_v(f.minimum_mag),
        max_mag=_v(f.maximum_mag),
        filter_set_options=frozenset(_fso_dict(f.filter_set_options).items()),
        trace_only=trace_only,
        corupture_fault_names=tuple(f.corupture_fault_names or []),
    )


# columns dropped from both fault_surfaces and fault_traces geojson output
_SECTION_GEOJSON_DROP_COLUMNS = [
    "rate_weighted_mean.max",
    "rate_weighted_mean.min",
    "rate_weighted_mean.mean",
    "Target Slip Rate",
    "Target Slip Rate StdDev",
]


def _mfd_histogram_rows(f: "FilterRupturesArgsInput"):
    """graphene-free port of CompositeRuptureSections.resolve_mfd_histogram (build_mfd)."""
    import pandas as pd

    df0 = _matched_rupture_sections(f)
    bins = [round(x / 100, 2) for x in range(500, 1000, 10)]
    df = pd.DataFrame({"rate": df0["rate_weighted_mean"], "magnitude": df0["Magnitude"]})
    df["bins"] = pd.cut(df["magnitude"], bins=bins)
    df["bin_center"] = df["bins"].apply(lambda x: x.mid)
    df = df.drop(columns=["magnitude"])
    df = pd.DataFrame(df.groupby(df.bin_center, observed=False).sum(numeric_only=True))
    df["cumulative_rate"] = df.loc[::-1, "rate"].cumsum()[::-1]
    df = df.reset_index()
    df.bin_center = pd.to_numeric(df.bin_center)
    df = df[df.bin_center.between(6.8, 9.8)]
    return list(df.itertuples())


def _fault_surfaces_geojson(f, color_scale_args, style_args):
    """graphene-free port of CompositeRuptureSections.resolve_fault_surfaces."""
    gdf = _fault_section_aggregates(f)
    if color_scale_args:
        color_values = get_colour_values(
            color_scale=color_scale_args.name,
            color_scale_vmax=color_scale_args.max_value or gdf["rate_weighted_mean.sum"].max(),
            color_scale_vmin=color_scale_args.min_value or gdf["rate_weighted_mean.sum"].min(),
            color_scale_normalise=color_scale_args.normalisation or "log",
            values=tuple(gdf["rate_weighted_mean.sum"].tolist()),
        )
    else:
        color_values = None

    if style_args or color_scale_args:
        gdf["fill"] = color_values or style_args.fill_color
        gdf["fill-opacity"] = style_args.fill_opacity or 0.5
        gdf["stroke"] = color_values or style_args.stroke_color
        gdf["stroke-width"] = style_args.stroke_width or 1
        gdf["stroke-opacity"] = style_args.stroke_opacity or 1

    gdf = gdf.drop(columns=_SECTION_GEOJSON_DROP_COLUMNS)
    return json.loads(gdf.to_json())


def _fault_traces_geojson(f, color_scale_args, style_args):
    """graphene-free port of CompositeRuptureSections.resolve_fault_traces."""
    gdf = _fault_section_aggregates(f, trace_only=True)
    color_values = None
    if color_scale_args:
        color_values = get_colour_values(
            color_scale=color_scale_args.name,
            color_scale_vmax=color_scale_args.max_value or gdf["rate_weighted_mean.sum"].max(),
            color_scale_vmin=color_scale_args.min_value or gdf["rate_weighted_mean.sum"].min(),
            color_scale_normalise=color_scale_args.normalisation or "log",
            values=tuple(gdf["rate_weighted_mean.sum"].tolist()),
        )

    if style_args or color_scale_args:
        gdf["stroke"] = color_values if color_scale_args else style_args.stroke_color
        gdf["stroke-width"] = style_args.stroke_width if style_args else 1
        gdf["stroke-opacity"] = style_args.stroke_opacity if style_args else 1

    gdf = gdf.drop(columns=_SECTION_GEOJSON_DROP_COLUMNS)
    return json.loads(gdf.to_json())


def _paginated_ruptures(f: "FilterRupturesArgsInput", sortby_args, first, after):
    """graphene-free port of paginated_filtered_ruptures + build_ruptures_connection.

    Returns plain data: (list of (rupture_index, cursor), total_count, end_cursor, has_next_page).
    """
    min_rate = _v(f.minimum_rate) or 1e-20
    gdf = _matched_rupture_sections(f)
    if sortby_args:
        gdf = _auto_sorted(gdf, sortby_args, min_rate)
    cursor_offset = int(graphql_relay.from_global_id(after)[1]) + 1 if after else 0
    rupture_ids = list(gdf["Rupture Index"])
    seeds = [
        (int(rid), graphql_relay.to_global_id("RuptureDetailConnectionCursor", str(cursor_offset + idx)))
        for idx, rid in enumerate(rupture_ids[cursor_offset : cursor_offset + first])
    ]
    total = len(rupture_ids)
    end_cursor = seeds[-1][1] if seeds else None
    has_next = (total > 1 + int(graphql_relay.from_global_id(seeds[-1][1])[1])) if seeds else False
    return seeds, total, end_cursor, has_next


def _fso_dict(fso) -> dict:
    if not fso:
        return {}

    def val(x):
        return x.value if x is not None else None

    return {
        "multiple_locations": val(fso.multiple_locations),
        "multiple_faults": val(fso.multiple_faults),
        "locations_and_faults": val(fso.locations_and_faults),
    }


def _legacy_color_scale_args(cs):
    """A namespace the legacy section resolvers can read, with `normalisation` as its string
    value (`log`/`lin`) rather than the strawberry enum member."""
    if cs is None or cs is strawberry.UNSET:
        return None
    return SimpleNamespace(
        name=cs.name,
        min_value=_v(cs.min_value),
        max_value=_v(cs.max_value),
        normalisation=(cs.normalisation.value if cs.normalisation else None),
    )


def _rupture_fault_surfaces(model_id, fault_system, rupture_index, style):
    composite_solution = cached.get_composite_solution(model_id)
    gdf = composite_solution._solutions[fault_system].rupture_surface(rupture_index)
    gdf = gdf.drop(
        columns=[
            "key_0", "fault_system", "Rupture Index", "rate_max", "rate_min", "rate_count",
            "rate_weighted_mean", "Magnitude", "Average Rake (degrees)", "Area (m^2)", "Length (m)",
        ]
    )
    return apply_geojson_style(json.loads(gdf.to_json(indent=2)), style) if gdf is not None else None


_DEFAULT_SORTBY: list = []  # module-level so it renders `= []` without a B006 mutable-default warning

# --------------------------------------------------------------------------- query root


@strawberry.type(description="This is the entry point for solvis graphql query operations")
class QueryRoot:
    @strawberry.field
    def color_scale(
        self,
        name: str | None = strawberry.UNSET,
        min_value: float | None = strawberry.UNSET,
        max_value: float | None = strawberry.UNSET,
        normalization: ColourScaleNormaliseEnum | None = strawberry.UNSET,
    ) -> ColorScale | None:
        cs = compute_colour_scale(
            color_scale=name or None,
            color_scale_normalise=normalization.value if normalization else None,
            vmax=max_value or None,
            vmin=min_value or None,
        )
        return _to_strawberry_color_scale(cs)

    @strawberry.field
    def node(
        self, id: Annotated[strawberry.ID, strawberry.argument(description="The ID of the object")]
    ) -> Node | None:
        # parity: the legacy graphene schema defines no `get_node`, so `node(id)` always
        # resolves to null (verified differentially) — nothing to dispatch.
        return None

    @strawberry.field(description="About this Solvis API ")
    def about(self) -> str | None:
        return f"Hello World, I am solvis_graphql_api! Version: {solvis_graphql_api.__version__}"

    @strawberry.field
    def locations_by_id(
        self,
        location_ids: Annotated[
            list[str | None],
            strawberry.argument(description='list of nzshm_common.location_ids e.g. `["WLG","PMR","ZQN"]`'),
        ],
    ) -> LocationDetailConnection | None:
        locs = [location_by_id(lid) for lid in (location_ids or [])]
        edges: list[LocationDetailEdge | None] = [
            LocationDetailEdge(
                node=LocationDetail(
                    location_id=loc["id"], name=loc["name"], latitude=loc["latitude"], longitude=loc["longitude"]
                ),
                cursor=graphql_relay.offset_to_cursor(i),  # matches graphene relay's array cursors
            )
            for i, loc in enumerate(locs)
        ]
        return LocationDetailConnection(
            page_info=PageInfo(has_next_page=False, has_previous_page=False),
            edges=edges,
            total_count=len(edges),
        )

    @strawberry.field
    def composite_solution(
        self,
        model_id: Annotated[str, strawberry.argument(description="A valid NSHM model id e.g. `NSHM_1.0.0`")],
    ) -> CompositeSolution | None:
        solution = cached.get_composite_solution(model_id)
        return CompositeSolution(model_id=model_id, fault_systems=list(solution._solutions.keys()))

    @strawberry.field
    def composite_rupture_detail(self, filter: CompositeRuptureDetailArgs) -> CompositeRuptureDetail | None:
        return CompositeRuptureDetail(
            model_id=filter.model_id.strip() if filter.model_id else filter.model_id,
            fault_system=filter.fault_system,
            rupture_index=filter.rupture_index,
        )

    @strawberry.field
    def filter_ruptures(
        self,
        filter: FilterRupturesArgsInput,
        sortby: list[SimpleSortRupturesArgs | None] | None = _DEFAULT_SORTBY,
        before: str | None = strawberry.UNSET,
        after: str | None = strawberry.UNSET,
        first: int | None = strawberry.UNSET,
        last: int | None = strawberry.UNSET,
    ) -> RuptureDetailConnection | None:
        sortby_args = [
            {"attribute": s.attribute, "ascending": s.ascending}
            for s in (sortby or [])
            if s is not None
        ]
        seeds, total, end_cursor, has_next = _paginated_ruptures(
            filter,
            sortby_args,
            first=(first if first is not strawberry.UNSET else 5),
            after=(after if after is not strawberry.UNSET else None),
        )
        edges: list[RuptureDetailEdge | None] = [
            RuptureDetailEdge(
                node=CompositeRuptureDetail(
                    model_id=filter.model_id, fault_system=filter.fault_system, rupture_index=rid
                ),
                cursor=cursor,
            )
            for rid, cursor in seeds
        ]
        return RuptureDetailConnection(
            page_info=PageInfo(
                has_next_page=has_next, has_previous_page=False, start_cursor=None, end_cursor=end_cursor
            ),
            edges=edges,
            total_count=total,
        )

    @strawberry.field
    def filter_rupture_sections(self, filter: FilterRupturesArgsInput) -> CompositeRuptureSections | None:
        return CompositeRuptureSections(model_id=filter.model_id, filter_input=filter)

    @strawberry.field
    def get_parent_fault_names(
        self,
        model_id: Annotated[str, strawberry.argument(description="A valid NSHM model id e.g. `NSHM_1.0.0`")],
        fault_system: Annotated[str, strawberry.argument(description="A valid FSS name CRU, PUY, HIK")],
    ) -> list[str | None] | None:
        composite_solution = cached.get_composite_solution(model_id)
        fss = composite_solution._solutions[fault_system]
        return list(cached.parent_fault_names(fss))

    @strawberry.field(description="Return ad single radii_set for the id passed in")
    def get_radii_set(
        self,
        radii_set_id: Annotated[int, strawberry.argument(description="the integer ID for the desired radii_set")],
    ) -> RadiiSet | None:
        for rad in RADII:
            if rad["id"] == radii_set_id:
                return RadiiSet(radii_set_id=radii_set_id, radii=[int(r) for r in rad["radii"]])
        raise IndexError(f"Radii set with id {radii_set_id} was not found.")

    @strawberry.field(description="Return all the available radii_set")
    def get_radii_sets(self) -> list[RadiiSet | None] | None:
        return [RadiiSet(radii_set_id=r["id"], radii=[int(x) for x in r["radii"]]) for r in RADII]

    @strawberry.field(description="Return a single location.")
    def get_location(
        self,
        location_id: Annotated[str, strawberry.argument(description="the location code of the desired location")],
    ) -> Location | None:
        for loc in LOCATIONS:
            if loc["id"] == location_id:
                return Location(
                    location_id=loc["id"], name=loc["name"], latitude=loc["latitude"], longitude=loc["longitude"]
                )
        raise IndexError(f"Location with id {location_id} was not found.")

    @strawberry.field(description="Return all the available locations")
    def get_locations(self) -> list[Location | None] | None:
        return [
            Location(location_id=loc["id"], name=loc["name"], latitude=loc["latitude"], longitude=loc["longitude"])
            for loc in LOCATIONS
        ]

    @strawberry.field(description="Return a single location list.")
    def get_location_list(
        self,
        list_id: Annotated[str, strawberry.argument(description="the id of the desired location_list")],
    ) -> LocationList | None:
        ll = LOCATION_LISTS.get(list_id)
        if ll:
            return LocationList(list_id=list_id, location_ids=ll["locations"])
        raise IndexError(f"LocationList with id {list_id} was not found.")

    @strawberry.field(description="Return all the available location lists")
    def get_location_lists(self) -> list[LocationList | None] | None:
        return [LocationList(list_id=key, location_ids=v["locations"]) for key, v in LOCATION_LISTS.items()]


schema = strawberry.Schema(
    query=QueryRoot,
    types=[LocationDetail, CompositeRuptureDetail],
    config=StrawberryConfig(auto_camel_case=False),
)
