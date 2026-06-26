"""SDL parity gate for the Graphene → Strawberry migration.

Dumps the new Strawberry SDL and diffs it (order-insensitive) against the committed
``schema.legacy.graphql`` baseline. Fails on any non-equivalent change — a missing field,
a changed nullability/default, a dropped description. Run:

    uv run python -m solvis_graphql_api.tools.schema_parity
"""

import contextlib
import difflib
import pathlib
import sys

from graphql import build_schema, lexicographic_sort_schema, print_schema

BASELINE = pathlib.Path(__file__).resolve().parents[2] / "schema.legacy.graphql"


def _normalise(sdl: str) -> str:
    # parse → sort lexicographically → reprint, so field/type ORDER is ignored but
    # every name / type / nullability / default / description still has to match.
    return print_schema(lexicographic_sort_schema(build_schema(sdl)))


def diff() -> str:
    with contextlib.redirect_stdout(sys.stderr):
        from solvis_graphql_api.schema import schema

        new_sdl = _normalise(schema.as_str())
    legacy_sdl = _normalise(BASELINE.read_text())
    if new_sdl == legacy_sdl:
        return ""
    return "\n".join(
        difflib.unified_diff(
            legacy_sdl.splitlines(),
            new_sdl.splitlines(),
            fromfile="schema.legacy.graphql",
            tofile="strawberry",
            lineterm="",
        )
    )


def main() -> int:
    d = diff()
    if not d:
        print("✓ SDL parity: Strawberry schema is byte-identical to schema.legacy.graphql")
        return 0
    print(d)
    print("\n✗ SDL parity FAILED — see diff above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
