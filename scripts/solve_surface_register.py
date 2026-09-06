#!/usr/bin/env python3
"""Declare solve-surface rows, and diff the surface between two trees.

Two jobs, both belonging to capx D79 (owner ruling Q54):

**``--declare NAME [NAME ...]`` / ``--declare-missing``** — append a name's LIVE
hash to ``src/market_sim/config/solve_surface_declared.py``. This is the
registration act: until a name is declared it cannot enter a cache key at all,
and once it is declared the frozen hash is what
:func:`market_sim.config.solve_surface.moved_rows` compares against forever. So
``--declare`` is for a name that has just been ADDED to a registry module (which
is why adding a table moves no key), NEVER for a name whose value has just
CHANGED — re-declaring a repaired table would restore its pre-repair key and
serve the pre-repair bundle, the exact hazard the fingerprint exists to close.
``scripts/check_cache_key_registration.py`` check 6 refuses an edited line, so
the mistake fails the PR rather than landing silently.

**``--diff <sha> [<sha>]``** — print the per-ISO changed rows between two trees
(second argument defaults to the working tree). This is the mechanised form of
the G-DRIFT audit's "``constants.py`` FIRST" step (rule 29 ``[R-SCREEN]`` (b),
D65-B-R Addendum C §1b): instead of reading a diff and judging which hunks are
solve-affecting, it says which NAMES moved and, for each, which ISOs' keys the
move reaches. Costs seconds and no LP.

The diff reconstructs each side with ``git archive`` of the surface modules into
a temp tree and imports them in a subprocess, so it never mutates the checkout
and never resolves a blob outside the seven files (partial-clone safe).

Usage::

    uv run python scripts/solve_surface_register.py --declare-missing
    uv run python scripts/solve_surface_register.py --declare DEMAND_GROWTH_RATES
    uv run python scripts/solve_surface_register.py --diff origin/main
    uv run python scripts/solve_surface_register.py --diff <sha> <sha>
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO / "src") not in sys.path:
    sys.path.insert(0, str(_REPO / "src"))

from market_sim.config.solve_surface import (  # noqa: E402
    SURFACE_ISOS,
    SURFACE_MODULES,
    surface_fingerprint,
)
from market_sim.config.solve_surface_declared import DECLARED  # noqa: E402

_DECLARED_REL = "src/market_sim/config/solve_surface_declared.py"
_ANCHOR = "DECLARED: dict[str, str | dict[str, str]] = {"

#: Files `git archive`d into the temp tree for a historical fingerprint: the
#: seven surface modules plus the package ``__init__`` files their absolute
#: imports need. Nothing else is read, so a blobless clone stays blobless.
#: ``solve_surface.py`` itself is deliberately NOT archived — the CURRENT
#: hashing code is copied over both sides, so a diff compares VALUES under one
#: rule instead of comparing two implementations of the rule (and so a ref that
#: predates this module still works).
_ARCHIVE_PATHS = tuple(
    f"src/{name.replace('.', '/')}.py" for name in SURFACE_MODULES
) + (
    "src/market_sim/__init__.py",
    "src/market_sim/config/__init__.py",
)


def _emit_line(name: str, value: str | dict[str, str]) -> str:
    """Render one ``DECLARED`` entry as a single source line."""
    if isinstance(value, dict):
        rows = ", ".join(f'"{iso}": "{value[iso]}"' for iso in sorted(value))
        return f'    "{name}": {{{rows}}},\n'
    return f'    "{name}": "{value}",\n'


def declare(names: list[str]) -> int:
    """Append declarations for ``names`` at their live hashes.

    Args:
        names: Surface names to declare. Already-declared names are refused
            (the ledger is append-only) and unknown names are refused (a typo
            would create a declaration nothing ever compares against).

    Returns:
        Process exit code.
    """
    live = surface_fingerprint()
    unknown = sorted(n for n in names if n not in live)
    already = sorted(n for n in names if n in DECLARED)
    if unknown:
        print(f"FAIL: not surface names: {', '.join(unknown)}")
        return 1
    if already:
        print(
            f"FAIL: already declared, and the ledger is APPEND-ONLY: "
            f"{', '.join(already)}\n"
            "  A name whose VALUE changed is not re-declared — leaving the "
            "frozen line put is what makes the changed row take its own key. "
            "Record the change as a PINNED_SURFACE_ROWS_BY_ISO cause block in "
            "tests/regression/test_persisted_identity.py instead."
        )
        return 1
    path = _REPO / _DECLARED_REL
    text = path.read_text()
    if _ANCHOR not in text:
        print(f"FAIL: cannot find the DECLARED anchor in {_DECLARED_REL}")
        return 1
    block = "".join(_emit_line(n, live[n]) for n in sorted(names))
    if text.rstrip().endswith("= {}"):
        text = text.replace(f"{_ANCHOR}}}\n", f"{_ANCHOR}\n{block}}}\n")
    else:
        head, _, tail = text.rpartition("}\n")
        text = head + block + "}\n" + tail
    path.write_text(text)
    # A wide by-ISO row does not fit 88 columns on one line, and CI runs
    # `ruff format --check .`, so the generator formats its own output rather
    # than leaving a red lint job (or an unformattable "one line per name").
    fmt = subprocess.run(["ruff", "format", str(path)], capture_output=True, text=True)
    if fmt.returncode != 0:
        print(f"warning: `ruff format {_DECLARED_REL}` failed:\n{fmt.stderr}")
    print(f"declared {len(names)} name(s) in {_DECLARED_REL}")
    return 0


def _paths_at(ref: str) -> list[str]:
    """The archive paths that exist at ``ref`` (trees only — no blob is read)."""
    present = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "--", *_ARCHIVE_PATHS],
        cwd=_REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    return [p for p in _ARCHIVE_PATHS if p in present]


def _fingerprint_at(ref: str | None) -> dict[str, object]:
    """Return the whole-surface fingerprint at ``ref`` (``None`` = worktree)."""
    if ref is None:
        return surface_fingerprint()
    with tempfile.TemporaryDirectory() as tmp:
        archive = subprocess.run(
            ["git", "archive", ref, *_paths_at(ref)],
            cwd=_REPO,
            capture_output=True,
            check=True,
        ).stdout
        subprocess.run(
            ["tar", "-x", "-C", tmp], input=archive, check=True, capture_output=True
        )
        here = Path(__file__).resolve().parents[1] / "src/market_sim/config"
        there = Path(tmp) / "src/market_sim/config"
        there.mkdir(parents=True, exist_ok=True)
        (there / "solve_surface.py").write_text((here / "solve_surface.py").read_text())
        out = subprocess.run(
            [
                sys.executable,
                "-c",
                "import json,sys;"
                "sys.path.insert(0, sys.argv[1]);"
                "from market_sim.config.solve_surface import surface_fingerprint;"
                "print(json.dumps(surface_fingerprint()))",
                str(Path(tmp) / "src"),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    return json.loads(out.stdout)


def _isos_reached(name: str, before, after) -> list[str]:
    """Which ISOs' keys a change to ``name`` reaches, using the live projection."""
    from market_sim.config.solve_surface import _iso_tokens

    if isinstance(before, dict) or isinstance(after, dict):
        before = before if isinstance(before, dict) else {}
        after = after if isinstance(after, dict) else {}
        return sorted(
            iso
            for iso in set(before) | set(after)
            if before.get(iso) != after.get(iso) and iso in SURFACE_ISOS
        )
    tokens = _iso_tokens(name)
    return sorted(tokens) if tokens else list(SURFACE_ISOS)


def diff(refs: list[str]) -> int:
    """Print the surface rows that moved between two trees.

    Args:
        refs: One or two git refs. With one, the second side is the working
            tree; with two, both sides are archived.

    Returns:
        Process exit code (0 always — this is a report, not a gate).
    """
    base = refs[0]
    head = refs[1] if len(refs) > 1 else None
    before = _fingerprint_at(base)
    after = _fingerprint_at(head)
    changed = sorted(
        name for name in set(before) | set(after) if before.get(name) != after.get(name)
    )
    added = [n for n in changed if n not in before]
    removed = [n for n in changed if n not in after]
    moved = [n for n in changed if n in before and n in after]

    label = head or "worktree"
    print(f"solve surface {base} -> {label}")
    print(
        f"  {len(before)} -> {len(after)} names; "
        f"{len(moved)} value(s) moved, {len(added)} added, {len(removed)} removed"
    )
    if added:
        print(f"  added (declare these; they move no key): {', '.join(added)}")
    if removed:
        print(f"  removed (declarations stay, rule 26): {', '.join(removed)}")
    if not moved:
        print("  NO VALUE MOVED — no ISO's key is reached by a registry change.")
        return 0
    print("  MOVED — each row below re-keys the ISOs named:")
    reach: dict[str, set[str]] = {iso: set() for iso in SURFACE_ISOS}
    for name in moved:
        isos = _isos_reached(name, before[name], after[name])
        for iso in isos:
            reach[iso].add(name)
        print(f"    {name}: {', '.join(isos) or '(no ISO)'}")
    print("  per-ISO totals: " + ", ".join(f"{i} {len(n)}" for i, n in reach.items()))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--declare", nargs="+", metavar="NAME")
    group.add_argument(
        "--declare-missing",
        action="store_true",
        help="declare every surface name that has no entry yet",
    )
    group.add_argument("--diff", nargs="+", metavar="SHA", help="base [head]")
    args = ap.parse_args(argv)

    if args.diff:
        if len(args.diff) > 2:
            print("FAIL: --diff takes one or two refs")
            return 1
        return diff(args.diff)
    names = (
        sorted(set(surface_fingerprint()) - set(DECLARED))
        if args.declare_missing
        else args.declare
    )
    if not names:
        print("ok: every surface name is already declared")
        return 0
    return declare(names)


if __name__ == "__main__":
    raise SystemExit(main())
