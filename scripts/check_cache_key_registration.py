#!/usr/bin/env python3
"""CI guard — a new ``ScenarioConfig`` field must be registered in
``_CACHE_KEY_OPTIONAL_FIELDS``.

**The failure this prevents.** ``ScenarioConfig.cache_key()`` hashes every field,
so adding a field changes the DEFAULT key and orphans every on-disk cache — even
when the new field ships default-off and its own docstring promises
"byte-identical off". The one-line remedy is to list the field in
``_CACHE_KEY_OPTIONAL_FIELDS``, which drops it from the hash **at its default
value only** (an armed run still hashes distinct, which is correct: it is a
different scenario).

This has now happened **five times** — ``coal_committed_takeorpay_sunk_fixed``
(9df6be7), ``measured_ct_heat_rates`` (c45fed4), ``pjm_apsouth_interface_cut``,
``pjm_external_net_position_cut``, the ``temp_derate_*`` / ``ramp_limits`` pair,
and ``pjm_zonal_loss_surface`` (PR #3093, repaired by ERCOT-135 §7.1). Each time
the break surfaced only as a *pinned-literal test failure* in an unrelated
session, whose tempting and WRONG remedy is to re-pin the literal — which
silently accepts the orphaned cache instead of fixing it. This guard moves the
detection to the PR that adds the field and states the correct remedy inline.

Two checks:

**1. New-field registration (FAILS the PR).** Every ``ScenarioConfig`` field
present at HEAD but absent at the merge base must appear in
``_CACHE_KEY_OPTIONAL_FIELDS``. Skipped when no ``--base`` is given (local runs).

**2. Registry integrity (FAILS always).** Every name in
``_CACHE_KEY_OPTIONAL_FIELDS`` must be a real ``ScenarioConfig`` field. A typo or
a later rename makes the registration a silent no-op — the field re-enters the
hash and the same breakage returns with the guard showing green.

Stdlib only (``ast`` + ``git show``): no import of the package, no ``uv sync``,
runs in seconds and cannot itself be broken by a config-module import error.

Usage::

    python3 scripts/check_cache_key_registration.py                  # check 2 only
    python3 scripts/check_cache_key_registration.py --base <sha>     # checks 1 + 2
"""

from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_CONFIG_REL = "src/market_sim/config/scenarios.py"
_CLASS = "ScenarioConfig"
_REGISTRY = "_CACHE_KEY_OPTIONAL_FIELDS"


def _fields_and_registry(source: str) -> tuple[set[str], set[str]]:
    """Return (``ScenarioConfig`` field names, ``_CACHE_KEY_OPTIONAL_FIELDS``).

    Parsed with ``ast`` rather than imported so this runs against an arbitrary
    git blob and against a tree whose config module may not even import.
    """
    tree = ast.parse(source)
    fields: set[str] = set()
    registry: set[str] = set()

    for node in ast.walk(tree):
        # The dataclass' annotated assignments are its fields.
        if isinstance(node, ast.ClassDef) and node.name == _CLASS:
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    fields.add(stmt.target.id)
        # Module-level `_CACHE_KEY_OPTIONAL_FIELDS = (...)` of string literals.
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == _REGISTRY:
                    for elt in getattr(node.value, "elts", []):
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            registry.add(elt.value)
    return fields, registry


def _blob(ref: str, rel: str) -> str | None:
    """``git show ref:rel``, or None when the path does not exist at that ref."""
    try:
        return subprocess.run(
            ["git", "show", f"{ref}:{rel}"],
            cwd=_REPO,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return None


_REMEDY = f"""
    REMEDY (one line, do NOT re-pin the cache-key literal):
      add the field name to {_REGISTRY} in {_CONFIG_REL},
      with a comment citing why it is cache-neutral at its default.

    Re-pinning PINNED_DEFAULT_CACHE_KEY in the tests instead ACCEPTS an orphaned
    on-disk cache and silently breaks every prior run's key. That is the wrong
    fix and it has been applied before -- see this script's docstring."""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="merge-base sha; enables the new-field check")
    args = ap.parse_args(argv)

    head_src = (_REPO / _CONFIG_REL).read_text()
    head_fields, head_registry = _fields_and_registry(head_src)
    if not head_fields:
        print(f"FAIL: parsed 0 fields from {_CLASS} in {_CONFIG_REL}")
        return 1

    failures: list[str] = []

    # --- check 2: registry integrity (always) -------------------------------
    stale = sorted(head_registry - head_fields)
    if stale:
        failures.append(
            f"{_REGISTRY} lists {len(stale)} name(s) that are NOT "
            f"{_CLASS} fields -- the registration is a silent no-op and the "
            f"field re-enters the cache key:\n      "
            + "\n      ".join(stale)
            + "\n    REMEDY: fix the typo, or drop the stale name if the field "
            "was removed."
        )

    # --- check 1: new fields must be registered (PR only) -------------------
    if args.base:
        base_src = _blob(args.base, _CONFIG_REL)
        if base_src is None:
            print(f"note: {_CONFIG_REL} absent at {args.base}; new-field check skipped")
        else:
            base_fields, _ = _fields_and_registry(base_src)
            added = head_fields - base_fields
            unregistered = sorted(added - head_registry)
            if unregistered:
                failures.append(
                    f"{len(unregistered)} new {_CLASS} field(s) added in this PR "
                    f"are NOT in {_REGISTRY}, so the DEFAULT cache key moves and "
                    f"every on-disk cache is orphaned:\n      "
                    + "\n      ".join(unregistered)
                    + _REMEDY
                )
            elif added:
                print(
                    f"ok: {len(added)} new field(s), all registered: "
                    f"{', '.join(sorted(added))}"
                )
            else:
                print("ok: no new ScenarioConfig fields in this PR")

    if failures:
        print("\ncache-key registration guard FAILED\n")
        for i, f in enumerate(failures, 1):
            print(f"  [{i}] {f}\n")
        return 1

    print(
        f"ok: {len(head_fields)} {_CLASS} fields, "
        f"{len(head_registry)} registered in {_REGISTRY}, all resolve"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
