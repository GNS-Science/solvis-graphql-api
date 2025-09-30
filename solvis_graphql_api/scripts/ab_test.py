import logging

log = logging.getLogger(__name__)


def check_query_about(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    def run_query(operation, endpoint):
        operation.about()
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint)
    b_res = run_query(b_op, b_endpoint)

    if not a_res.about == b_res.about:
        log.warning(f"about: `{a_res.about}` !== `{b_res.about}`")
    return a_res.about == b_res.about


def check_query_color_scale(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    kwargs = dict(name="inferno", min_value=5, max_value=10, normalization="LIN")

    def run_query(operation, endpoint, kwargs):
        operation.color_scale(**kwargs).color_map()
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).color_scale.color_map
    b_res = run_query(b_op, b_endpoint, kwargs).color_scale.color_map

    if not a_res.levels == b_res.levels:
        log.warning(f"color_scale.levels: `{a_res.levels}` !== `{b_res.levels}`")

    if not a_res.hexrgbs == b_res.hexrgbs:
        log.warning(f"color_scale.hexrgbs: `{a_res.hexrgbs}` !== `{b_res.hexrgbs}`")

    return (a_res.levels == b_res.levels) and (a_res.hexrgbs == b_res.hexrgbs)


def check_get_parent_fault_names(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(model_id="NSHM_v1.0.4", fault_system="CRU")

    def run_query(operation, endpoint, kwargs):
        operation.get_parent_fault_names(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).get_parent_fault_names
    b_res = run_query(b_op, b_endpoint, kwargs).get_parent_fault_names

    if not a_res == b_res:
        log.warning(f"get_parent_fault_name: `{a_res}` !== `{b_res}`")
    return a_res == b_res


def check_get_location_list(a_op, a_endpoint, b_op, b_endpoint) -> bool:

    kwargs = dict(list_id="NZ")

    def run_query(operation, endpoint, kwargs):
        operation.get_location_list(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).get_location_list
    b_res = run_query(b_op, b_endpoint, kwargs).get_location_list

    if not a_res.location_ids == b_res.location_ids:
        log.warning(
            f"get_get_location_list: `{a_res.location_ids}` !== `{b_res.location_ids}`"
        )

    # check location details
    for idx, locn in enumerate(a_res.locations):
        if (
            not (b_res.locations[idx].latitude == locn.latitude)
            and (b_res.locations[idx].longitude == locn.longitude)
            and (b_res.locations[idx].location_id == locn.location_id)
            and (b_res.locations[idx].name == locn.name)
        ):
            log.warning(
                f"get_get_location_list.locations[{idx}]: `{locn}` !== `{b_res.locations[idx]}`"
            )
            assert 0

    return a_res.location_ids == b_res.location_ids


def check_get_radii_set(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(radii_set_id=7)

    def run_query(operation, endpoint, kwargs):
        operation.get_radii_set(**kwargs)
        data = endpoint(operation)
        return operation + data

    a_res = run_query(a_op, a_endpoint, kwargs).get_radii_set
    b_res = run_query(b_op, b_endpoint, kwargs).get_radii_set

    if not a_res.radii == b_res.radii:
        log.warning(f"get_radii_set: `{a_res.radii}` !== `{b_res.radii}`")
    return a_res.radii == b_res.radii


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

    if not a_res.total_count == b_res.total_count:
        log.warning(
            f"filter_ruptures.total_count: `{a_res.total_count}` !== `{b_res.total_count}`"
        )
        assert 0

    for idx, edge in enumerate(a_res.edges):
        # print(edge)
        if not (edge.node.rupture_index == b_res.edges[idx].node.rupture_index):
            log.warning(
                f"filter_ruptures.edges: `{edge.node.rupture_index}` !== `{b_res.edges[idx].node.rupture_index}`"
            )
            assert 0
        if not (edge.node.magnitude == b_res.edges[idx].node.magnitude):
            log.warning(
                f"filter_ruptures.edges: `{edge.node.magnitude}` !== `{b_res.edges[idx].node.magnitude}`"
            )
            assert 0
        if not (
            edge.node.rate_weighted_mean == b_res.edges[idx].node.rate_weighted_mean
        ):
            log.warning(
                f"filter_ruptures.edges: `{edge.node.rate_weighted_mean}` !== `{b_res.edges[idx].node.rate_weighted_mean}`"
            )
            # assert 0
    return True


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

    if not a_res.section_count == b_res.section_count:
        log.warning(
            f"filter_rupture_sections.section_count: `{a_res.section_count}` !== `{b_res.section_count}`"
        )
    if not a_res.color_scale.color_map.levels == b_res.color_scale.color_map.levels:
        log.warning(
            f"color_scale.color_map.levels: `{a_res.color_scale.color_map.levels}` !== `{b_res.color_scale.color_map.levels}`"
        )

    if not a_res.color_scale.color_map.hexrgbs == b_res.color_scale.color_map.hexrgbs:
        log.warning(
            f"color_scale.color_map.hexrgbs: `{a_res.color_scale.color_map.hexrgbs}` !== `{b_res.color_scale.color_map.hexrgbs}`"
        )

    return True
