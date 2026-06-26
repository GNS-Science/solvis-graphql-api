"""Composite-solution data and compute helpers (graphene-free).

The legacy graphene schema types that this package used to re-export (CompositeRuptureDetail,
CompositeRuptureSections, FilterRupturesArgs, paginated_filtered_ruptures, ...) were removed at
the Strawberry cutover. Import the graphene-free helpers from their submodules directly:
``cached`` (data access + rupture_detail) and ``ruptures`` (auto_sorted_dataframe).
"""
