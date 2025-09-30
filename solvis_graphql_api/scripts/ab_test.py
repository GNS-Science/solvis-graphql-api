import logging

log = logging.getLogger(__name__)


def check_query_about(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    # evaluate comparisons
    a_op.about()
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).about

    b_op.about()
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).about
    if not a_res == b_res:
        log.warning(f"about: `{a_res}` !== `{b_res}`")
    return a_res == b_res


def check_query_color_scale(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    # evaluate comparisons
    kwargs = dict(name="inferno", min_value=5, max_value=10, normalization="LIN")
    csa = a_op.color_scale(**kwargs)
    csa.color_map()
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).color_scale.color_map

    csb = b_op.color_scale(**kwargs)
    csb.color_map()
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).color_scale.color_map

    if not a_res.levels == b_res.levels:
        log.warning(f"color_scale.levels: `{a_res.levels}` !== `{b_res.levels}`")

    if not a_res.hexrgbs == b_res.hexrgbs:
        log.warning(f"color_scale.hexrgbs: `{a_res.hexrgbs}` !== `{b_res.hexrgbs}`")

    return (a_res.levels == b_res.levels) and (a_res.hexrgbs == b_res.hexrgbs)


def check_get_parent_fault_names(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(model_id="NSHM_v1.0.4", fault_system="CRU")
    a_op.get_parent_fault_names(**kwargs)
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).get_parent_fault_names

    b_op.get_parent_fault_names(**kwargs)
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).get_parent_fault_names
    if not a_res == b_res:
        log.warning(f"get_parent_fault_name: `{a_res}` !== `{b_res}`")
    return a_res == b_res


def check_get_location_list(a_op, a_endpoint, b_op, b_endpoint) -> bool:
    kwargs = dict(list_id="NZ")
    a_op.get_location_list(**kwargs)
    a_data = a_endpoint(a_op)

    b_op.get_location_list(**kwargs)
    b_data = b_endpoint(b_op)

    a_res = (a_op + a_data).get_location_list
    b_res = (b_op + b_data).get_location_list

    # check ids
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
    a_op.get_radii_set(**kwargs)
    a_data = a_endpoint(a_op)
    a_res = (a_op + a_data).get_radii_set

    b_op.get_radii_set(**kwargs)
    b_data = b_endpoint(b_op)
    b_res = (b_op + b_data).get_radii_set
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

    conn_a = a_op.filter_ruptures(**kwargs)
    conn_b = b_op.filter_ruptures(**kwargs)
    # setup queries
    conn_a.total_count()
    conn_b.total_count()
    conn_a.edges.node.__fields__(__exclude__=("fault_traces", "fault_surfaces"))
    conn_b.edges.node.__fields__(__exclude__=("fault_traces", "fault_surfaces"))

    a_data = a_endpoint(a_op)
    b_data = b_endpoint(b_op)

    a_res = (a_op + a_data).filter_ruptures
    b_res = (b_op + b_data).filter_ruptures

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
            assert 0
    return True
