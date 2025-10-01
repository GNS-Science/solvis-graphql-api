import functools
import json
import logging
import pprint

from deepdiff import DeepDiff  # , Delta, parse_path
from deepdiff.helper import COLORED_VIEW

log = logging.getLogger(__name__)


def rgetattr(obj, attr, *args):
    """recursive getattr"""

    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


def ab_check_failure(fn_name: str, label: str, a_obj, b_obj, precision=None) -> bool:
    """helper to check/log any differences"""
    a_value = rgetattr(a_obj, label)
    b_value = rgetattr(b_obj, label)

    if precision:
        log.debug(f"original values: {a_value} {b_value}")
        a_value = round(a_value, precision)
        b_value = round(b_value, precision)
        log.debug(f"rounded values: {a_value} {b_value} with precision: {precision}")

    if not a_value == b_value:
        log.warning(f"function: {fn_name}, attribute: {label}: a/b test failed")
        log.debug(
            f"function: {fn_name}, attribute: {label}: `{a_value}` !== `{b_value}`"
        )
        return True
    return False  # no fail


def check_about(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    def run_query(operation, endpoint):
        operation.about()
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint)
    b_res = run_query(b_op, b_endpoint)

    failure: bool = False
    fn_name = check_about.__name__
    failure = failure or ab_check_failure(fn_name, "about", a_res, b_res)
    if not failure:
        log.info(f"function: {fn_name}, a/b tests PASS")
    else:
        log.info(f"a: `{a_res.about}` vs b: `{b_res.about}`")
    return failure


def check_color_scale(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    kwargs = dict(name="inferno", min_value=5, max_value=10, normalization="LIN")

    def run_query(operation, endpoint, kwargs):
        operation.color_scale(**kwargs).color_map()
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs)
    b_res = run_query(b_op, b_endpoint, kwargs)

    failure: bool = False
    fn_name = check_color_scale.__name__
    failure = failure or ab_check_failure(
        fn_name, "color_scale.color_map.levels", a_res, b_res
    )
    failure = failure or ab_check_failure(
        fn_name, "color_scale.color_map.hexrgbs", a_res, b_res
    )
    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_get_parent_fault_names(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(model_id="NSHM_v1.0.4", fault_system="CRU")

    def run_query(operation, endpoint, kwargs):
        operation.get_parent_fault_names(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs)
    b_res = run_query(b_op, b_endpoint, kwargs)

    failure: bool = False
    fn_name = check_get_parent_fault_names.__name__
    failure = failure or ab_check_failure(
        fn_name, "get_parent_fault_names", a_res, b_res
    )
    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_get_location_list(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    kwargs = dict(list_id="NZ")

    def run_query(operation, endpoint, kwargs):
        operation.get_location_list(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).get_location_list
    b_res = run_query(b_op, b_endpoint, kwargs).get_location_list

    failure: bool = False
    fn_name = check_get_location_list.__name__
    failure = failure or ab_check_failure(fn_name, "location_ids", a_res, b_res)
    for idx, locn_a in enumerate(a_res.locations):
        locn_b = b_res.locations[idx]
        failure = failure or ab_check_failure(fn_name, "latitude", locn_a, locn_b)
        failure = failure or ab_check_failure(fn_name, "longitude", locn_a, locn_b)
        failure = failure or ab_check_failure(fn_name, "location_id", locn_a, locn_b)
        failure = failure or ab_check_failure(fn_name, "name", locn_a, locn_b)

    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_get_radii_set(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(radii_set_id=7)

    def run_query(operation, endpoint, kwargs):
        operation.get_radii_set(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).get_radii_set
    b_res = run_query(b_op, b_endpoint, kwargs).get_radii_set

    failure: bool = False
    fn_name = check_get_radii_set.__name__
    failure = failure or ab_check_failure(fn_name, "radii", a_res, b_res)
    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_filter_ruptures(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    """
    SOLVIS_filter_ruptures(
      first: $first
      after: $after
      filter: {
        model_id: $model_id
        fault_system: $fault_system
        location_ids: $location_ids
        radius_km: $radius_km
        corupture_fault_names: $corupture_fault_names
        minimum_mag: $minimum_mag
        maximum_mag: $maximum_mag
        minimum_rate: $minimum_rate
        maximum_rate: $maximum_rate
      }
      sortby: $sortby
    ) {
      total_count
    }
    """
    kwargs = dict(
        filter=dict(
            model_id="NSHM_v1.0.4",
            fault_system="CRU",
            location_ids=["WLG", "MRO"],
            radius_km=20,
        ),
        first=3,
    )

    def run_query(operation, endpoint, kwargs):
        conn = operation.filter_ruptures(**kwargs)
        conn.total_count()
        conn.edges.node.__fields__(__exclude__=("fault_traces", "fault_surfaces"))
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).filter_ruptures
    b_res = run_query(b_op, b_endpoint, kwargs).filter_ruptures

    failure: bool = False
    fn_name = check_filter_ruptures.__name__
    failure = failure or ab_check_failure(fn_name, "total_count", a_res, b_res)
    for idx, a_edge in enumerate(a_res.edges):
        b_edge = b_res.edges[idx]
        failure = failure or ab_check_failure(
            fn_name, "node.rupture_index", a_edge, b_edge
        )
        failure = failure or ab_check_failure(fn_name, "node.magnitude", a_edge, b_edge)
        failure = failure or ab_check_failure(
            fn_name, "node.rate_weighted_mean", a_edge, b_edge, precision=10
        )

    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_filter_rupture_sections(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    """
    SOLVIS_filter_rupture_sections(
      filter: {
        model_id: $model_id
        location_ids: $location_ids
        fault_system: $fault_system
        corupture_fault_names: $corupture_fault_names
        radius_km: $radius_km
        minimum_mag: $minimum_mag
        maximum_mag: $maximum_mag
        minimum_rate: $minimum_rate
        maximum_rate: $maximum_rate
      }
    ) {
      model_id
      section_count
      fault_surfaces(style: { stroke_color: "silver", fill_color: "silver", fill_opacity: 0.25 })
      fault_traces(color_scale: { name: "inferno" }, style: { stroke_width: 5 })
      color_scale(name: "inferno") {
        name
        min_value
        max_value
        color_map {
          levels
          hexrgbs
        }
      }
      mfd_histogram {
        bin_center
        rate
        cumulative_rate
      }
    }
    """
    kwargs = dict(
        filter=dict(
            model_id="NSHM_v1.0.4",
            fault_system="CRU",
            location_ids=["WLG", "MRO"],
            radius_km=20,
        )
    )

    def run_query(operation, endpoint, kwargs):
        conn = operation.filter_rupture_sections(**kwargs)
        conn.__fields__(__exclude__=("fault_traces", "fault_surfaces", "color_scale"))
        conn.color_scale(name="inferno").color_map().__fields__()
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).filter_rupture_sections
    b_res = run_query(b_op, b_endpoint, kwargs).filter_rupture_sections

    failure: bool = False
    fn_name = check_filter_rupture_sections.__name__
    failure = failure or ab_check_failure(fn_name, "section_count", a_res, b_res)
    failure = failure or ab_check_failure(
        fn_name, "color_scale.color_map.levels", a_res, b_res
    )
    failure = failure or ab_check_failure(
        fn_name, "color_scale.color_map.hexrgbs", a_res, b_res
    )
    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_locations_by_id(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    """
    SOLVIS_locations_by_id(location_ids: $location_ids) {
      edges {
        node {
          location_id
          name
          radius_geojson(
            radius_km: $radius_km
            style: {
              stroke_color: "royalblue"
              stroke_width: 3
              stroke_opacity: 1
              fill_opacity: 0.01
              fill_color: "royalblue"
            }
          )
        }
      }
    }
    """
    kwargs = dict(
        location_ids=["WLG", "MRO"],
        radius_km=20,
    )

    def run_query(operation, endpoint, kwargs):
        conn = operation.locations_by_id(location_ids=kwargs["location_ids"])
        node = conn.edges().node()
        node.__fields__(__exclude__=("radius_geojson"))
        node.radius_geojson(radius_km=kwargs["radius_km"])
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).locations_by_id
    b_res = run_query(b_op, b_endpoint, kwargs).locations_by_id

    # print(a_res)
    failure: bool = False
    fn_name = check_locations_by_id.__name__
    for idx, a_edge in enumerate(a_res.edges):
        b_edge = b_res.edges[idx]
        failure = failure or ab_check_failure(
            fn_name, "node.location_id", a_edge, b_edge
        )

        if ab_check_failure(fn_name, "node.radius_geojson", a_edge, b_edge):
            print("diff for property `node.radius_geojson`")
            print("---------------------------------------")
            ddiff = DeepDiff(
                json.loads(a_edge.node.radius_geojson),
                json.loads(b_edge.node.radius_geojson),
                view=COLORED_VIEW,
            )
            # threshold_to_diff_deeper=0)
            print(ddiff)
            print()
            failure = True

    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure


def check_composite_rupture_detail(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    """
    SOLVIS_composite_rupture_detail(
      filter: { model_id: $model_id, fault_system: $fault_system, rupture_index: $rupture_index }
    ) {
      __typename
      magnitude
      length
      area
      rupture_index
      rate_max
      rate_min
      rate_count
      rake_mean
      fault_surfaces
    }
    """
    kwargs = dict(
        filter=dict(model_id="NSHM_v1.0.4", fault_system="CRU", rupture_index=3),
    )

    def run_query(operation, endpoint, kwargs):
        conn = operation.composite_rupture_detail(**kwargs)
        conn.__fields__("magnitude", "length", "fault_surfaces")
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).composite_rupture_detail
    b_res = run_query(b_op, b_endpoint, kwargs).composite_rupture_detail

    failure: bool = False
    fn_name = check_composite_rupture_detail.__name__
    failure = failure or ab_check_failure(fn_name, "magnitude", a_res, b_res)
    failure = failure or ab_check_failure(fn_name, "length", a_res, b_res)
    if ab_check_failure(fn_name, "fault_surfaces", a_res, b_res):
        print("diff for property `fault_surfaces`")
        print("----------------------------------")
        ddiff = DeepDiff(
            json.loads(a_res.fault_surfaces),
            json.loads(b_res.fault_surfaces),
            view=COLORED_VIEW,
        )
        print(ddiff)
        failure = True

    log.info(f"function: {fn_name}, a/b tests PASS") if not failure else None
    return failure
