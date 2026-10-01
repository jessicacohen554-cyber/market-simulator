#!/usr/bin/env python3
"""FAIL a PR that changes an ISO's keeper but leaves that promotion's records behind.

THE DEFECT (audit lane Y-29, 2026-09-24; owner ruling R-BF, director board v43,
2026-09-25). Every guard a promotion owes already exists and already runs in
CI: ``check_gate_a_provenance`` (FR-21), ``check_forecast_parity`` (FR-22) and
``audit_keepers`` (E13, rule 35 ``[R-PROMOTE]`` (f)). Debt piled up anyway. On
2026-09-24 six gate-(a) rows cited superseded keepers, SOCO carried an E13
orphan, and FR-22 had three unaccounted fields. A day later five more gate-(a)
rows had gone stale behind that day's promotions.

There were two causes. First, ``main`` is ``protected: false`` (owner ruling
R-BG keeps it off), so a red check blocks nothing. Second, each guard checks
the WHOLE tree, so its red shows up on whichever PR happens to run next,
usually an unrelated one, and not on the PR that caused it.

This script targets the second cause. It is scoped to **the ISOs whose
``frontend/data/backcast/keepers/<ISO>.json`` ``keeper`` changed against the PR
base**. That puts the failure on the promoter's own PR, where the promoter is
the one reading it. For each such ISO it requires, in the resulting tree:

(a) ``check_gate_a_provenance`` passes for that ISO. The forecast board's
    gate-(a) row cites the new keeper and states the right marker. An ISO with
    no board row (NWPP and SOCO today) is noted, not failed, because the board
    carries no row for it to re-key.
(b) If the ISO holds ``complete``, ``complete.<ISO>.keeper`` in
    ``calibration-complete.json`` names the new keeper.
(c) ``check_forecast_parity`` shows 0 UNACCOUNTED fields, and no sweep error,
    for that ISO's keeper posture.
(d) ``audit_keepers`` E13 is clean for that ISO. Every registered run is the
    keeper or stamped to it, meaning the outgoing keeper was pruned.
(e) The new keeper's bundle COMMITS ``hourly/unit_hourly_<year>.parquet`` for
    every year its registry sidecar declares (CLAUDE.md rule 15 ``[R-DASHBOARD]``,
    owner instruction 2026-10-01: "Moving forward for all ISOs"). The per-unit
    hourly layer (``mw``, ``cap_mw``, the P1 offer ``mc``, HiGHS ``red_cost``) is
    the only artifact that names the LP's own marginal units; without it every
    unit-grain question costs one diagnostic keeper replay per year (PJM-NEXT-14
    and PJM-NEXT-18 each paid that bill). ~1-2 MB per ISO-year since the
    DELTA_BINARY_PACKED ``hour`` encoding (``.gitignore`` note, nyiso-116).
    Prospective only: the leg runs for ISOs whose keeper CHANGED against
    ``--base``; a ``--iso``-forced check notes it as not applicable, so keepers
    designated before this leg existed are re-checked when their ISO next
    promotes, never retroactively.

WHAT IT DOES NOT DO. It never reads, recomputes or asserts a DETERMINATION;
each leg reuses the existing checker's own function, so there is still exactly
one instrument per question. It does not check ISOs whose keeper did not
change: the whole-tree jobs already cover those. And it changes no gate: with
branch protection OFF (R-BG) a red here is advisory in effect, a signal the
promoter reads on its own PR.

Usage::

    python3 scripts/check_promotion_completeness.py --base <PR base sha>
    python3 scripts/check_promotion_completeness.py --iso NYISO   # force one ISO

Exit codes: 0 clean (or no keeper changed), 1 on any failing leg, 2 when the
base ref cannot be read.

Stdlib-only (json/argparse/subprocess plus the three stdlib checkers it reuses),
so it runs on the bare ``python3`` of the data-free CI jobs. No uv sync, no LP,
no data fetch.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts import audit_keepers  # noqa: E402  (after sys.path insert)
from scripts import check_forecast_parity  # noqa: E402
from scripts import check_gate_a_provenance as gate_a  # noqa: E402

KEEPERS_REL = "frontend/data/backcast/keepers"
REGISTRY_REL = "frontend/data/backcast/registry"
COMPLETE_REL = "frontend/data/backcast/calibration-complete.json"
PROGRAM_STATUS_REL = "frontend/data/forecast/program-status.json"

#: Non-ISO files in the keeper store.
NON_ISO_SHARDS = gate_a.NON_ISO_SHARDS


def _load(path: Path) -> dict:
    """Read a JSON file, returning ``{}`` when it is absent."""
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def head_keepers(repo: Path) -> dict[str, str]:
    """Return ``{ISO: keeper id}`` from the working tree's keeper shards.

    Args:
        repo: Repository root.

    Returns:
        One entry per shard that carries a string ``keeper``.
    """
    return gate_a.designated_keepers(repo / KEEPERS_REL)


def base_keeper(repo: Path, base: str, iso: str) -> str | None:
    """Return the ISO's keeper id at ``base``, or ``None`` if the shard was absent.

    Args:
        repo: Repository root.
        base: Git revision of the PR base.
        iso: ISO code.

    Returns:
        The base ``keeper`` string, or ``None`` when the shard did not exist
        there (a newly registered ISO counts as a keeper change).

    Raises:
        RuntimeError: ``git`` could not resolve ``base`` at all.
    """
    rev = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "rev-parse",
            "--verify",
            "--quiet",
            f"{base}^{{commit}}",
        ],
        capture_output=True,
        text=True,
    )
    if rev.returncode != 0:
        raise RuntimeError(f"cannot resolve base revision {base!r}")
    show = subprocess.run(
        ["git", "-C", str(repo), "show", f"{base}:{KEEPERS_REL}/{iso}.json"],
        capture_output=True,
        text=True,
    )
    if show.returncode != 0:
        return None
    keeper = json.loads(show.stdout).get("keeper")
    return keeper if isinstance(keeper, str) and keeper else None


def changed_isos(repo: Path, base: str) -> dict[str, tuple[str | None, str]]:
    """Return the ISOs whose designated keeper differs from the PR base.

    Args:
        repo: Repository root.
        base: Git revision of the PR base.

    Returns:
        ``{ISO: (base keeper or None, head keeper)}`` for each changed ISO.
    """
    out: dict[str, tuple[str | None, str]] = {}
    for iso, keeper in sorted(head_keepers(repo).items()):
        before = base_keeper(repo, base, iso)
        if before != keeper:
            out[iso] = (before, keeper)
    return out


def leg_a_gate(
    iso: str, keeper: str, status_doc: dict, complete_doc: dict
) -> tuple[list[str], list[str]]:
    """Leg (a): the ISO's forecast gate-(a) row passes ``check_gate_a_provenance``.

    Args:
        iso: ISO code.
        keeper: The ISO's new designated keeper.
        status_doc: Parsed ``program-status.json``.
        complete_doc: Parsed ``calibration-complete.json``.

    Returns:
        ``(problems, notes)``. An ISO with no board row yields a note only.
    """
    row = (((status_doc.get("isos") or {}).get(iso) or {}).get("gate") or {}).get(
        gate_a.GATE_A_KEY
    )
    if not isinstance(row, dict):
        return [], [
            f"{iso}: no gate.{gate_a.GATE_A_KEY} row on the forecast board — leg (a) not applicable"
        ]
    membership = gate_a.marker_membership(complete_doc).get(iso, (False, False))
    problems = gate_a.check_iso(iso, row, keeper, membership)
    return [f"(a) {p}" for p in problems], []


def leg_b_marker(iso: str, keeper: str, complete_doc: dict) -> list[str]:
    """Leg (b): a ``complete`` entry, if the ISO holds one, names the new keeper.

    Args:
        iso: ISO code.
        keeper: The ISO's new designated keeper.
        complete_doc: Parsed ``calibration-complete.json``.

    Returns:
        Problems; empty when the ISO holds no ``complete`` entry or it is current.
    """
    entry = (complete_doc.get("complete") or {}).get(iso)
    if not isinstance(entry, dict):
        return []
    named = entry.get("keeper")
    if named != keeper:
        return [
            f"(b) {iso}: calibration-complete.json complete.{iso}.keeper names "
            f"{named!r}, not the new keeper {keeper!r}. Re-key the marker in the "
            f"promoting PR, or withdraw it if the new keeper cannot carry it (Q5)."
        ]
    return []


def leg_c_parity(iso: str, repo: Path) -> list[str]:
    """Leg (c): ``check_forecast_parity`` shows 0 UNACCOUNTED for the ISO's keeper.

    Args:
        iso: ISO code.
        repo: Repository root.

    Returns:
        Problems: every UNACCOUNTED field and every sweep error for the ISO.
    """
    reports, _registry_failures = check_forecast_parity.run(repo, [iso])
    problems: list[str] = []
    for rep in reports:
        if rep.iso != iso:
            continue
        for err in rep.errors:
            problems.append(f"(c) {iso}: forecast-parity sweep error: {err}")
        for v in rep.by_status("UNACCOUNTED"):
            problems.append(
                f"(c) {iso}: {v.field} is armed in keeper {rep.run_id} with no "
                f"forecast-orchestrator consumer and no registry declaration "
                f"(scripts/lib/forecast_parity_registry.py)"
            )
    return problems


def leg_d_e13(iso: str, keeper: str, registry_dir: Path) -> list[str]:
    """Leg (d): ``audit_keepers`` E13 is clean, so the outgoing keeper was pruned.

    Args:
        iso: ISO code.
        keeper: The ISO's new designated keeper.
        registry_dir: Registry sidecar directory.

    Returns:
        Problems, one per orphan registered run.
    """
    findings, _years = audit_keepers.orphan_run_findings(iso, keeper, registry_dir)
    return [f"(d) E13 {f}" for f in findings]


def leg_e_unit_hourly(keeper: str, repo: Path) -> list[str]:
    """Leg (e): the new keeper's bundle commits ``unit_hourly`` for every year.

    Args:
        keeper: The ISO's new designated keeper.
        repo: Repository root.

    Returns:
        Problems: a missing sidecar/bundle, or one line naming every year whose
        ``hourly/unit_hourly_<year>.parquet`` is absent from the bundle.
    """
    side = _load(repo / REGISTRY_REL / f"{keeper}.json")
    bundle_rel, years = side.get("bundle"), side.get("years") or []
    if not bundle_rel:
        return [f"(e) {keeper}: registry sidecar names no bundle"]
    hourly = repo / bundle_rel / "hourly"
    missing = [
        int(y)
        for y in years
        if not (hourly / f"unit_hourly_{int(y)}.parquet").is_file()
    ]
    if missing:
        return [
            f"(e) {keeper}: {bundle_rel}/hourly/ lacks unit_hourly_<year>.parquet for "
            f"{missing}. A keeper bundle commits the per-unit hourly layer for every "
            f"year it carries (rule 15); compose it from the solve legs' bundles."
        ]
    return []


def check_iso(
    iso: str, keeper: str, repo: Path, promoted: bool = False
) -> tuple[list[str], list[str]]:
    """Run all five legs for one promoted ISO.

    Args:
        iso: ISO code.
        keeper: The ISO's new designated keeper.
        repo: Repository root.
        promoted: The keeper changed against the PR base; arms leg (e).

    Returns:
        ``(problems, notes)``.
    """
    status_doc = _load(repo / PROGRAM_STATUS_REL)
    complete_doc = _load(repo / COMPLETE_REL)
    problems, notes = leg_a_gate(iso, keeper, status_doc, complete_doc)
    problems += leg_b_marker(iso, keeper, complete_doc)
    problems += leg_c_parity(iso, repo)
    problems += leg_d_e13(iso, keeper, repo / REGISTRY_REL)
    if promoted:
        problems += leg_e_unit_hourly(keeper, repo)
    else:
        notes.append(
            f"{iso}: keeper unchanged vs base — leg (e) unit_hourly not applied"
        )
    return problems, notes


def main(argv: list[str] | None = None) -> int:
    """CLI entry point (see the module docstring)."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", type=Path, default=REPO, help="repo root")
    ap.add_argument(
        "--base", default=None, help="PR base revision to diff keepers against"
    )
    ap.add_argument(
        "--iso",
        action="append",
        default=[],
        help="check these ISOs regardless of the diff (repeatable)",
    )
    args = ap.parse_args(argv)
    repo = args.repo.resolve()

    targets: dict[str, tuple[str | None, str]] = {}
    if args.base:
        try:
            targets.update(changed_isos(repo, args.base))
        except RuntimeError as exc:
            print(f"promotion completeness: {exc}", file=sys.stderr)
            return 2
    keepers = head_keepers(repo)
    for iso in args.iso:
        iso = iso.upper()
        if iso not in keepers:
            print(f"promotion completeness: no keeper shard for {iso}", file=sys.stderr)
            return 2
        targets.setdefault(iso, (None, keepers[iso]))
    if not args.base and not args.iso:
        ap.error("pass --base <rev> (PR mode) or --iso <ISO>")

    if not targets:
        print(
            "promotion completeness: no ISO's designated keeper changed — nothing to check"
        )
        return 0

    all_problems: list[str] = []
    promoted = set(targets) if args.base else set()
    for iso, (before, keeper) in sorted(targets.items()):
        problems, notes = check_iso(iso, keeper, repo, promoted=iso in promoted)
        print(f"{iso}: keeper {before or '(none)'} -> {keeper}")
        for n in notes:
            print(f"  note: {n}")
        if problems:
            for p in problems:
                print(f"  FAIL {p}")
        else:
            print(
                "  OK   (a) gate-(a) row  (b) complete marker  (c) FR-22 parity  (d) E13"
                + ("  (e) unit_hourly" if iso in promoted else "")
            )
        all_problems += problems

    if all_problems:
        print(
            f"\npromotion completeness FAILED: {len(all_problems)} problem(s). A promotion "
            f"PR re-keys gate (a) and the `complete` marker, accounts for every armed "
            f"field under FR-22, and prunes the outgoing keeper (rule 35) and commits the keeper's "
            f"per-unit hourly layer (rule 15) in the SAME PR (owner ruling R-BF).",
            file=sys.stderr,
        )
        return 1
    print("\npromotion completeness OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
