"""Dump the legacy Graphene SDL as the Strawberry-migration parity baseline.

    uv run python -m solvis_graphql_api.tools.dump_legacy_sdl > schema.legacy.graphql

Importing the schema pulls in ``solvis``/``pyvista``, which print warnings to
**stdout** ("WARNING: optional `toshi` dependencies ...", "geometry.section_distance()
uses ... pyvista"). Those would pollute the SDL file, so we redirect stdout to stderr
for the duration of the import (runbook Phase 0 trap; surfaced by the Model pilot).
"""

import contextlib
import sys

with contextlib.redirect_stdout(sys.stderr):
    from solvis_graphql_api.schema import schema_root

print(str(schema_root))
