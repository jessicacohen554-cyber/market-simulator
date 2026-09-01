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

Three checks:

**1. New-field registration (FAILS the PR).** Every ``ScenarioConfig`` field
present at HEAD but absent at the merge base must appear in
``_CACHE_KEY_OPTIONAL_FIELDS``. Skipped when no ``--base`` is given (local runs).

**2. Registry integrity (FAILS always).** Every name in
``_CACHE_KEY_OPTIONAL_FIELDS`` must be a real ``ScenarioConfig`` field. A typo or
a later rename makes the registration a silent no-op — the field re-enters the
hash and the same breakage returns with the guard showing green.

**3. Declared default (FAILS always) — the default-flip hazard.** A registration
is only meaningful relative to a fixed default, because ``cache_key()`` drops a
registered field when it equals the **LIVE** default. Move that default and the
new-default run hashes identically to the old-default run it supersedes: a
silent same-key collision, invisible to every other surface. This has already
happened — the D-1/D-2 flips left ``cache_key(ScenarioConfig())`` at
``603c2498bf71d21d`` across a behavioral change, and the signed packet asserted
the opposite. FFR-3A recorded it and closed with *"it will silently recur on the
next default flip; structural, needs a decision not a patch."*

So every registered field's live default must match its declared entry in
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``, and the two collections must cover each
other exactly. A default flip then cannot land silently: this check stops it
until the flip is declared, and the declaring commit is where the operator
decides whether the same-key collision is acceptable (a byte-identical flip) or
needs a cache-epoch entry plus a purge (a behavioral flip — see the ledger in
``src/market_sim/results/cache.py``). Unlike check 1 this needs no ``--base``, so
it fires on every CI run and every local run — a lane cannot rely on a later
session noticing.

**4. Append-only ledger (FAILS the PR; needs ``--base``).** Since 2026-09-01
``cache_key()`` drops a registered field at its DECLARED default rather than its
live one (capx D24 option (b′-1), owner ruling Q20), so each
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` entry is the FROZEN value that field's
absence is equivalent to — editing one silently re-keys every config that
carries the field. The ledger is therefore APPEND-ONLY: a new field adds a line,
an existing line is never edited, and a line disappears only with the field
itself (rule 26 ``[R-DELETE]``, which parks the value in
``_CACHE_KEY_RETIRED_FIELDS``). A DEFAULT FLIP is declared by appending to
``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`` instead, which check 3 then compares
the live default against — so a flip still cannot land silently, and the frozen
drop value stays put, which is the whole point of (b′-1).

Defaults are compared as ``ast.unparse``-normalized SOURCE TEXT, so reformatting
and comment churn are invisible, and any default form (a literal, a
``field(default_factory=...)``, an expression) is expressible.

Stdlib only (``ast`` + ``git show``): no import of the package, no ``uv sync``,
runs in seconds and cannot itself be broken by a config-module import error.

Usage::

    python3 scripts/check_cache_key_registration.py                  # checks 2 + 3
    python3 scripts/check_cache_key_registration.py --base <sha>     # checks 1 + 2 + 3
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
_DECLARED = "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS"
_FLIPS = "_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS"
_RETIRED = "_CACHE_KEY_RETIRED_FIELDS"
_EPOCH_LEDGER_REL = "src/market_sim/results/cache.py"


def _norm(expr: str) -> str:
    """Normalize a default expression to comparable source text.

    Round-tripped through ``ast`` so formatting, line breaks and quote style
    cannot make an unchanged default look moved (or a moved one look
    unchanged). Unparseable text is returned verbatim, which then fails the
    comparison loudly rather than silently matching.
    """
    try:
        return ast.unparse(ast.parse(expr, mode="eval").body)
    except SyntaxError:
        return expr


def _fields_and_registry(
    source: str,
) -> tuple[dict[str, str], set[str], dict[str, str]]:
    """Return (field → default source, ``_CACHE_KEY_OPTIONAL_FIELDS``, declared).

    Parsed with ``ast`` rather than imported so this runs against an arbitrary
    git blob and against a tree whose config module may not even import.

    ``field → default source`` maps every ``ScenarioConfig`` annotated
    assignment to its ``ast.unparse``d default expression; a field declared
    with no default maps to ``""``. ``declared`` is
    ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS``, likewise normalized, and is empty
    for a blob predating that ledger.
    """
    tree = ast.parse(source)
    fields: dict[str, str] = {}
    registry: set[str] = set()
    declared: dict[str, str] = {}

    for node in ast.walk(tree):
        # The dataclass' annotated assignments are its fields.
        if isinstance(node, ast.ClassDef) and node.name == _CLASS:
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(
                    stmt.target, ast.Name
                ):
                    fields[stmt.target.id] = (
                        ast.unparse(stmt.value) if stmt.value is not None else ""
                    )
        # Module-level `_CACHE_KEY_OPTIONAL_FIELDS = (...)` of string literals,
        # and `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS = {name: "<default src>"}`.
        if isinstance(node, ast.Assign):
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            if _REGISTRY in targets:
                for elt in getattr(node.value, "elts", []):
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        registry.add(elt.value)
        # The ledger carries an annotation, so it is an AnnAssign at module level.
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            tgts = (
                [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)
            )
            if any(isinstance(t, ast.Name) and t.id == _DECLARED for t in tgts):
                val = node.value
                if isinstance(val, ast.Dict):
                    for k, v in zip(val.keys, val.values):
                        if (
                            isinstance(k, ast.Constant)
                            and isinstance(k.value, str)
                            and isinstance(v, ast.Constant)
                            and isinstance(v.value, str)
                        ):
                            declared[k.value] = _norm(v.value)
    return fields, registry, declared


def _declared_flips(source: str) -> list[tuple[str, str]]:
    """Return ``[(field, new default source)]`` from ``_CACHE_KEY_..._FLIPS``.

    The flips ledger is a tuple of ``(date, field, new default source text)``
    triples, appended one line per default flip and never edited. Order is
    preserved, so the LAST entry for a field is its current declaration. Empty
    for a blob predating the ledger (2026-09-01).
    """
    flips: list[tuple[str, str]] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tgts = [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)
        if not any(isinstance(t, ast.Name) and t.id == _FLIPS for t in tgts):
            continue
        for elt in getattr(node.value, "elts", []):
            parts = [
                e.value
                for e in getattr(elt, "elts", [])
                if isinstance(e, ast.Constant) and isinstance(e.value, str)
            ]
            if len(parts) == 3:
                flips.append((parts[1], _norm(parts[2])))
    return flips


def _retired(source: str) -> set[str]:
    """Return the ``_CACHE_KEY_RETIRED_FIELDS`` names (fields deleted, rule 26)."""
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        tgts = [node.target] if isinstance(node, ast.AnnAssign) else list(node.targets)
        if not any(isinstance(t, ast.Name) and t.id == _RETIRED for t in tgts):
            continue
        if isinstance(node.value, ast.Dict):
            names.update(
                k.value
                for k in node.value.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            )
    return names


def append_only_violations(
    base_declared: dict[str, str],
    head_declared: dict[str, str],
    head_fields: set[str],
    head_retired: set[str],
) -> list[str]:
    """Return the append-only breaches between two ledger states.

    Pure, so the tests can drive it on synthetic source with no git. Two
    breaches, and only two — adding an entry for a NEW field is the append the
    ledger is for:

    * an existing entry whose declared default was EDITED (the frozen drop
      value moved, silently re-keying every config carrying that field);
    * an entry REMOVED while its field still exists at HEAD and is not retired
      (deleting a field under rule 26 ``[R-DELETE]`` legitimately drops its
      line, and ``_CACHE_KEY_RETIRED_FIELDS`` preserves the value).

    Args:
        base_declared: The ledger at the merge base.
        head_declared: The ledger at HEAD.
        head_fields: ``ScenarioConfig`` field names at HEAD.
        head_retired: ``_CACHE_KEY_RETIRED_FIELDS`` names at HEAD.

    Returns:
        Human-readable breach descriptions, empty when the change is an append.
    """
    breaches: list[str] = []
    for name, was in sorted(base_declared.items()):
        if name not in head_declared:
            if name in head_fields and name not in head_retired:
                breaches.append(
                    f"{name}: entry REMOVED while the field still exists "
                    f"(declared {was})"
                )
            continue
        if head_declared[name] != was:
            breaches.append(f"{name}: {was} -> {head_declared[name]} (EDITED)")
    return breaches


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


_FLIP_REMEDY = f"""
    WHY THIS FAILS (it is not bookkeeping). cache_key() drops a registered field
    when it equals the LIVE default. Moving that default makes a NEW-default run
    hash IDENTICALLY to the OLD-default run it supersedes -- a silent same-key
    collision, so the flipped config re-uses the pre-flip bundle. Nothing else in
    the codebase can see this; that is why the guard exists.

    REMEDY (in the SAME commit as the flip):
      1. APPEND a (date, field, new default source) line to {_FLIPS}
         ({_CONFIG_REL}) -- this is the declaration. Do NOT edit the field's
         entry in {_DECLARED}: since capx D24 option (b'-1) that
         entry is the FROZEN value the cache key drops the field at, so leaving
         it put is what makes the post-flip config take its own key instead of
         colliding with the pre-flip bundle. Check 4 fails an edit;
      2. decide, and record, what the collision means:
         * BYTE-IDENTICAL flip (no solve output moves) -> say so in the commit
           message and in the entry's comment; nothing further is needed.
         * BEHAVIORAL flip -> the collision is a same-key invalidation. Add a
           dated cache-epoch ledger entry in {_EPOCH_LEDGER_REL}
           naming what is invalidated, and purge/segregate the affected caches.

    Do NOT "fix" this by removing the field from {_REGISTRY}: that
    re-enters it into the hash at every value and orphans every historical key."""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", help="merge-base sha; enables the new-field check")
    args = ap.parse_args(argv)

    head_src = (_REPO / _CONFIG_REL).read_text()
    head_fields, head_registry, head_declared = _fields_and_registry(head_src)
    # The CURRENT declaration of a field's live default: its frozen ledger entry,
    # overridden by the newest appended flip. Check 3 compares the live default
    # against this; the frozen entry itself is what the cache key drops at, and
    # check 4 keeps it frozen.
    head_current = dict(head_declared)
    for name, new_default in _declared_flips(head_src):
        head_current[name] = new_default
    if not head_fields:
        print(f"FAIL: parsed 0 fields from {_CLASS} in {_CONFIG_REL}")
        return 1

    failures: list[str] = []

    # --- check 2: registry integrity (always) -------------------------------
    stale = sorted(head_registry - set(head_fields))
    if stale:
        failures.append(
            f"{_REGISTRY} lists {len(stale)} name(s) that are NOT "
            f"{_CLASS} fields -- the registration is a silent no-op and the "
            f"field re-enters the cache key:\n      "
            + "\n      ".join(stale)
            + "\n    REMEDY: fix the typo, or drop the stale name if the field "
            "was removed."
        )

    # --- check 3: a registered field's default may not move silently --------
    missing_decl = sorted(head_registry - set(head_declared))
    extra_decl = sorted(set(head_declared) - head_registry)
    moved = sorted(
        (name, _norm(head_fields[name]), head_current[name])
        for name in head_registry & set(head_current)
        if name in head_fields and _norm(head_fields[name]) != head_current[name]
    )
    stale_flips = sorted(
        name for name, _ in _declared_flips(head_src) if name not in head_registry
    )
    if missing_decl:
        failures.append(
            f"{len(missing_decl)} field(s) in {_REGISTRY} have no entry in "
            f"{_DECLARED}, so their registration has no recorded default and a "
            f"flip of it could not be detected:\n      "
            + "\n      ".join(missing_decl)
            + f"\n    REMEDY: add each to {_DECLARED} in {_CONFIG_REL} with the "
            "source text of its current default."
        )
    if extra_decl:
        failures.append(
            f"{len(extra_decl)} entr(y/ies) in {_DECLARED} are not in "
            f"{_REGISTRY} -- a stale declaration protects nothing:\n      "
            + "\n      ".join(extra_decl)
            + "\n    REMEDY: drop the stale entry, or re-register the field."
        )
    if moved:
        failures.append(
            f"{len(moved)} registered field(s) had their DEFAULT MOVED without "
            f"declaring it in {_DECLARED}:\n      "
            + "\n      ".join(
                f"{n}: declared {d} -> now {live}" for n, live, d in moved
            )
            + _FLIP_REMEDY
        )
    if stale_flips:
        failures.append(
            f"{len(stale_flips)} entr(y/ies) in {_FLIPS} name a field that is not "
            f"in {_REGISTRY} -- a flip declared for an unregistered field "
            f"protects nothing:\n      "
            + "\n      ".join(stale_flips)
            + "\n    REMEDY: register the field, or drop the stale flip line."
        )

    # --- check 1 + 4: PR-only, need the merge base --------------------------
    if args.base:
        base_src = _blob(args.base, _CONFIG_REL)
        if base_src is None:
            print(f"note: {_CONFIG_REL} absent at {args.base}; new-field check skipped")
        else:
            base_fields, _, base_declared = _fields_and_registry(base_src)
            breaches = append_only_violations(
                base_declared,
                head_declared,
                set(head_fields),
                _retired(head_src),
            )
            if breaches:
                failures.append(
                    f"{len(breaches)} {_DECLARED} entr(y/ies) changed in this PR; "
                    f"the ledger is APPEND-ONLY:\n      "
                    + "\n      ".join(breaches)
                    + f"""
    WHY THIS FAILS. Since capx D24 option (b'-1) the entry is the FROZEN value
    cache_key() DROPS the field at, not a description of the live default.
    Editing it re-keys every config carrying the field -- silently, because the
    key is the only address a bundle has.

    REMEDY:
      * declaring a DEFAULT FLIP -> APPEND a (date, field, new default source)
        line to {_FLIPS} and leave the frozen entry alone;
      * deleting the field (rule 26 [R-DELETE]) -> drop its {_REGISTRY} and
        {_DECLARED} lines TOGETHER and record its value in {_RETIRED};
      * fixing a genuinely WRONG frozen value -> that moves cache keys. It needs
        a measured key-move count and an owner decision, not this guard."""
                )
            added = set(head_fields) - set(base_fields)
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
        f"{len(head_registry)} registered in {_REGISTRY}, all resolve; "
        f"{len(head_declared)} declared defaults all match HEAD"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
