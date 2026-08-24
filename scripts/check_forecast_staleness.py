#!/usr/bin/env python
"""WARN when the forecast board's evidence has gone stale behind HEAD (FR-21).

The forecast-readiness audit's FR-21: **the T1 gate evidence is stale and nothing
detects it.** FF-2D scored on 2026-07-20; over the ten days that followed ~20
keeper promotions landed, the pinned default config cache key moved twice
(``2a1cb710`` → ``edbc1b10`` → ``603c2498``) and was broken-and-restored once,
and the NYISO forecast orchestrator was rewired — a *backcast-only mechanism
family* found missing from the forecast path. No FC verdict was re-scored. The
board kept rendering the 07-20 verdicts as if they described the code.

Nothing detected it because nothing was looking. This check looks::

    python scripts/check_forecast_staleness.py

It reads the ``provenance`` stamps written by ``scripts/lib/forecast_provenance``
(on every forecast registry sidecar, run payload, verdict sidecar and the
manifest meta), takes the newest ``scored_at_sha`` **on the gate-evidence class**,
and counts the commits touching **solve-affecting paths** that have landed since.
Past the threshold it prints a warning.

**Per class, not one headline (FFR-3A).** The board holds several kinds of
stamped artifact and they go stale independently, so collapsing them into a
single "newest scored sha" lets a fresh artifact of one kind hide staleness in
another. Measured 2026-08-24: the board's newest scored stamp was a hindcast
sidecar re-registered on 2026-08-22, so the headline read fresh while 31 of the
32 verdict stamps were UNSCORED and FF-2D's verdicts dated from 2026-07-20 —
the FR-21 failure mode reproducing inside the FR-21 detector. The position is
now measured per class (:data:`CLASS_BY_INPUT`), rendered per class, and the
staleness warning is driven off :data:`GATING_CLASS` — the FC verdicts, which
are what gates (b) and (c) of the §2.1b board actually rest on. A hindcast
sidecar is an INPUT to a future verdict, never a substitute for one; when one is
scored more recently than the verdicts, that is reported as a separate
``FRESHER NON-GATE ARTIFACTS`` warning rather than being allowed to front them.
Partly-scored gate evidence is named too: one re-scored verdict beside thirty
unscored ones is not a scored board.

**WARN, never FAIL — by design.** Backcast calibration velocity must not be
blocked by forecast-board freshness: the two lanes run concurrently and the
backcast lane is the one producing the keepers that make the board stale in the
first place. This check exits 0 unless ``--fail-on-stale`` is passed explicitly
(it is not, in CI). What it buys is visibility, not a gate.

Two staleness signals, both reported:

1. **Commit distance** — solve-affecting commits between the newest scored sha
   and HEAD. Past ``--max-commits`` (default 10) this warns.
2. **Epoch spread** — the count of distinct ``cache_epoch`` values across the
   board. More than one means the board is comparing runs solved under different
   config identities; that is legitimate for a mixed-vintage board, so it is
   always reported and never on its own a warning.

An UNSCORED board (no stamp carries a ``scored_at_sha``) warns immediately and
says so plainly: absence of a scoring record is not evidence of freshness. That
is the board's state until FFR-3A re-scores the battery through the stamped
scorer.

A board that is simply **not in this tree** is reported separately, and this
distinction is load-bearing. The tracked board inputs are listed in
``BOARD_INPUTS_COMMITTED``; when one is absent the check says
``BOARD INPUT(S) MISSING`` and suppresses the "no stamps at all" claim, because
that claim would be false. Before this split, a checkout missing
``ff-verdicts.json`` and ``frontend/data/hindcast`` printed the alarming
"carries NO provenance stamps at all" for a board whose stamps were fully
intact — the reading that opened the FR-21 provenance-restore session, and which
one direct measurement (39 stamped / 8 scored on the same commit, from the
commit's own tree) refuted.

Stdlib-only (json/subprocess/argparse) so it runs on the bare ``python3`` the
stdlib CI jobs use — no numpy, no model import, no LP.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:  # resolve ``scripts.lib`` when run as a plain script
    sys.path.insert(0, str(REPO))

from scripts.lib import forecast_provenance as fp  # noqa: E402  (after sys.path)

#: Paths whose movement can change what a forecast solve produces — so a verdict
#: scored before they moved may no longer describe the code. ``src/market_sim``
#: is the model itself; the listed scripts are the schedulable forecast
#: instruments and the scorer that grades them. Deliberately NOT included:
#: ``docs/``, ``frontend/`` and the backcast-only calibration paths — churn there
#: cannot invalidate a forecast verdict, and including it would drown the signal.
SOLVE_AFFECTING_PATHS = (
    "src/market_sim",
    "scripts/run_full_horizon.py",
    "scripts/run_capacity_hindcast.py",
    "scripts/forecast_verdict.py",
    "scripts/check_forecast_invariants.py",
    "scripts/score_crossover.py",
)

#: Board artifacts carrying provenance stamps, split by whether THIS CHECKOUT is
#: expected to hold them. The split is the point: a stamp count of zero means two
#: entirely different things — "the board is unstamped" and "the board is not in
#: this tree" — and only the split can tell them apart.
#:
#: Tracked inputs, present in every checkout (plan §7.5). One missing means the
#: check is reading a tree that does not hold the board, so its counts describe
#: the tree and not the board. ``program-status.json`` is watched because it is
#: the file the records lane re-keys: watching it is what makes a re-key that
#: drops its stamp visible instead of silent.
BOARD_INPUTS_COMMITTED = (
    "frontend/data/forecast/ff-verdicts.json",
    "frontend/data/forecast/program-status.json",
    "frontend/data/hindcast",
)

#: Generated and gitignored — the Pages deploy is their single writer (plan
#: §7.5), and locally they exist only after ``register_forecast_run.py
#: --reindex``. Absence is the normal state and is never warned about.
BOARD_INPUTS_GENERATED = ("frontend/data/forecast/registry",)

#: Everything the check reads. Order is immaterial; the split above carries the
#: meaning.
BOARD_PATHS = BOARD_INPUTS_GENERATED + BOARD_INPUTS_COMMITTED

# --- artifact classes (FFR-3A) ---------------------------------------------
# The board holds several KINDS of stamped artifact, and they go stale
# independently. Collapsing them into one "newest scored sha" lets a fresh
# artifact of one kind hide staleness in another: measured 2026-08-24, the
# board's newest scored stamp was a hindcast sidecar refreshed 2026-08-22, so
# the headline read fresh while 31 of 32 verdict stamps were UNSCORED and
# FF-2D's verdicts dated from 2026-07-20. That is the FR-21 failure mode
# reproducing inside the FR-21 detector, so the position is now measured per
# class and the warning is driven off the class that actually carries the gate
# evidence.
BOARD_CLASS_VERDICTS = "verdicts"
BOARD_CLASS_HINDCAST = "hindcast sidecars"
BOARD_CLASS_SEED = "seed"
BOARD_CLASS_REGISTRY = "registry"
BOARD_CLASS_OTHER = "other"

#: Repo-relative path (or path prefix) -> artifact class. A path under a listed
#: directory inherits its class; anything unrecognised is ``other`` so a new
#: board input is visible as unclassified rather than silently folded into the
#: gate evidence.
CLASS_BY_INPUT = {
    "frontend/data/forecast/ff-verdicts.json": BOARD_CLASS_VERDICTS,
    "frontend/data/forecast/program-status.json": BOARD_CLASS_SEED,
    "frontend/data/forecast/registry": BOARD_CLASS_REGISTRY,
    "frontend/data/hindcast": BOARD_CLASS_HINDCAST,
}

#: The class whose freshness IS the gate evidence's freshness. Gates (b) and (c)
#: of the §2.1b board rest on FC verdicts; a hindcast sidecar is an INPUT to a
#: future verdict, never a substitute for one, so re-registering a hindcast run
#: must not make the gate evidence look re-scored. When the measured target set
#: holds no verdict artifact at all the whole board is used instead — a check
#: pointed at something other than the board should still report on what it was
#: given rather than silently find nothing.
GATING_CLASS = BOARD_CLASS_VERDICTS

#: Default commit-distance threshold. Set from the FR-21 incident itself rather
#: than picked round: the ten-day dark window carried well past this many
#: solve-affecting commits, so the observed failure would have tripped this
#: check. It is a reporting threshold on a WARN-only signal, not a model
#: parameter — tune it freely if it proves noisy.
DEFAULT_MAX_COMMITS = 10


def _git(*args: str) -> str | None:
    """Run a git command in the repo, returning stdout or ``None`` on any error."""
    try:
        out = subprocess.run(
            ["git", "-C", str(REPO), *args],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def solve_affecting_commits_since(sha: str) -> int | None:
    """Count commits touching :data:`SOLVE_AFFECTING_PATHS` in ``sha..HEAD``.

    ``None`` when git cannot answer — most often because ``sha`` is not in this
    checkout (a shallow CI clone, or a board scored on a branch that never
    merged). An unanswerable distance is reported as unknown, never as zero.
    """
    out = _git("rev-list", "--count", f"{sha}..HEAD", "--", *SOLVE_AFFECTING_PATHS)
    if out is None:
        return None
    try:
        return int(out)
    except ValueError:
        return None


def missing_inputs(targets: list[Path]) -> list[str]:
    """Return the board inputs in ``targets`` that are not in this tree.

    Paths in :data:`BOARD_INPUTS_GENERATED` are excluded: they are gitignored
    build products, so their absence is the normal state of a checkout and says
    nothing about the board. Everything else is a tracked input whose absence
    means the check is looking at a tree that does not hold the board.
    """
    optional = {REPO / g for g in BOARD_INPUTS_GENERATED}
    out = []
    for t in targets:
        if t in optional or t.exists():
            continue
        try:
            out.append(str(t.relative_to(REPO)))
        except ValueError:  # a path outside the repo (a test fixture tree)
            out.append(str(t))
    return out


def classify(path: Path) -> str:
    """Return the board artifact class ``path`` belongs to.

    Matches on the repo-relative path, so a file inside a classified directory
    (a hindcast sidecar, a generated registry entry) inherits that directory's
    class. Anything unrecognised — including a path outside the repo, which a
    test fixture tree is — reads :data:`BOARD_CLASS_OTHER` rather than being
    folded into the gate evidence.
    """
    try:
        rel = path.resolve().relative_to(REPO).as_posix()
    except ValueError:
        return BOARD_CLASS_OTHER
    for prefix, cls in CLASS_BY_INPUT.items():
        if rel == prefix or rel.startswith(prefix + "/"):
            return cls
    return BOARD_CLASS_OTHER


def _class_position(stamps: list[dict]) -> dict:
    """Summarize one class's stamps: how many, how many scored, and the newest.

    ``stamps`` is that class's stamp list; an empty list yields zero counts and
    ``None`` shas, never a fabricated position.
    """
    dated = [s for s in stamps if s.get("scored_at_date") and s.get("scored_at_sha")]
    newest = max(dated, key=lambda s: s["scored_at_date"], default=None)
    return {
        "n_stamps": len(stamps),
        "n_scored": len(dated),
        "newest_scored_at_sha": (newest or {}).get("scored_at_sha"),
        "newest_scored_at_date": (newest or {}).get("scored_at_date"),
    }


def board_position(paths: list[Path] | None = None) -> dict:
    """Summarize the board's staleness position from its provenance stamps.

    Also records which board inputs were readable. Without that, a board that is
    simply *absent from the tree* reads identically to a board that is present
    and unstamped — the FR-21 restore session's opening measurement was exactly
    that confusion, and it cost a full attribution pass to unwind.
    """
    targets = paths if paths is not None else [REPO / p for p in BOARD_PATHS]
    absent = missing_inputs(targets)
    found = fp.collect_stamps(targets)
    stamps = [s for _, s in found]
    by_class: dict[str, list[dict]] = {}
    for path, stamp in found:
        by_class.setdefault(classify(path), []).append(stamp)
    classes = {name: _class_position(rows) for name, rows in sorted(by_class.items())}
    # The gating position drives the staleness warning. It is the verdict class
    # whenever verdicts are among the measured artifacts; otherwise the whole
    # board, so a check pointed at some other tree still reports on what it was
    # given (see GATING_CLASS).
    gating = GATING_CLASS if GATING_CLASS in classes else None
    overall = _class_position(stamps)
    pos = {
        **overall,
        "cache_epochs": sorted(
            {s["cache_epoch"] for s in stamps if s.get("cache_epoch")}
        ),
        "head_sha": fp.head_sha(),
        "missing_inputs": absent,
        "by_class": classes,
        "gating_class": gating,
    }
    pos["gating"] = classes[gating] if gating else overall
    return pos


def evaluate(max_commits: int = DEFAULT_MAX_COMMITS, paths=None) -> dict:
    """Return the full staleness report: position, distance, and any warnings."""
    pos = board_position(paths)
    warnings: list[str] = []
    distance = None

    # Staleness is measured on the GATING class (the FC verdicts), not on the
    # whole board — see GATING_CLASS. ``gate`` falls back to the board-wide
    # position when no verdict artifact was measured, so every existing caller
    # that points the check at some other tree behaves exactly as before.
    gating = pos.get("gating_class")
    gate = pos.get("gating") or pos
    label = gating or "board"

    absent = pos.get("missing_inputs") or []
    if absent:
        # Reported FIRST and unconditionally: every count below is a property of
        # the tree, not of the board, once an input is missing.
        warnings.append(
            "BOARD INPUT(S) MISSING from this checkout: "
            + ", ".join(absent)
            + ". These are tracked files, so their absence means this check is "
            "reading a tree that does not hold the board — the stamp counts "
            "below measure the tree, not the board, and a zero here is a "
            "MEASUREMENT failure, NOT an unstamped board. Restore the checkout "
            "before reading anything into the numbers."
        )

    if not pos["n_stamps"] and not absent:
        warnings.append(
            "The forecast board carries NO provenance stamps at all — nothing on "
            "it records when or against what it was scored. Re-score through "
            "scripts/forecast_verdict.py (FFR-3A) to populate them."
        )
    elif not pos["n_stamps"]:
        pass  # already explained by the missing-input warning above
    elif not gate["newest_scored_at_sha"]:
        warnings.append(
            f"{gate['n_stamps']} {label} artifact(s) are stamped but NONE records "
            "a scored-at sha — every stamp is UNSCORED (predates the machinery, "
            "or its verdict was never re-scored through the stamped scorer). "
            "Absence of a scoring record is not evidence of freshness."
        )
    else:
        distance = solve_affecting_commits_since(gate["newest_scored_at_sha"])
        if distance is None:
            warnings.append(
                f"Cannot measure distance from the newest scored {label} sha "
                f"{gate['newest_scored_at_sha']} — it is not reachable in this "
                "checkout (shallow clone, or scored on an unmerged branch). "
                "Staleness is UNKNOWN, which is not the same as fresh."
            )
        elif distance > max_commits:
            warnings.append(
                f"The forecast board's newest {label} evidence was scored at "
                f"{gate['newest_scored_at_sha']} ({gate['newest_scored_at_date']}), "
                f"and {distance} solve-affecting commit(s) have landed since "
                f"(threshold {max_commits}). The verdicts on the board may no "
                "longer describe this code — this is the FR-21 'ten days dark' "
                "failure mode. Re-score the battery, or record why the drift is "
                "immaterial."
            )

    # The masking check (FFR-3A). Any class scored more recently than the gate
    # evidence would, under a single collapsed headline, make the board read as
    # fresh as its freshest artifact — which is how a hindcast sidecar
    # re-registered on 2026-08-22 came to front verdicts last scored 2026-07-20.
    if gating and gate["newest_scored_at_date"]:
        newer = [
            f"{name} ({p['newest_scored_at_sha']} @ {p['newest_scored_at_date']})"
            for name, p in pos["by_class"].items()
            if name != gating
            and p["newest_scored_at_date"]
            and p["newest_scored_at_date"] > gate["newest_scored_at_date"]
        ]
        if newer:
            warnings.append(
                f"FRESHER NON-GATE ARTIFACTS on the board: {', '.join(newer)} are "
                f"scored more recently than the {label} evidence "
                f"({gate['newest_scored_at_sha']} @ {gate['newest_scored_at_date']}). "
                "They are inputs to a future verdict, never a substitute for one, "
                "so they do NOT make the gate evidence fresher. The staleness "
                "reading above is driven off the verdict class alone."
            )

    # Unscored gate evidence is worth naming even when SOME of it is scored: a
    # single re-scored verdict beside thirty unscored ones is not a scored board.
    if gating and gate["n_stamps"] and gate["n_scored"] < gate["n_stamps"]:
        warnings.append(
            f"{gate['n_stamps'] - gate['n_scored']} of {gate['n_stamps']} {label} "
            "stamps record no scored-at date — those verdicts have never been "
            "re-scored through the stamped scorer, so their freshness is UNKNOWN "
            "regardless of what the newest scored one says."
        )

    if len(pos["cache_epochs"]) > 1:
        # Reported, never a warning on its own: a board spanning several waves
        # legitimately holds runs from several epochs.
        pos["epoch_spread_note"] = (
            f"{len(pos['cache_epochs'])} distinct config cache epochs on the "
            "board — runs are being compared across different config identities. "
            "Expected for a mixed-vintage board; check it is intended before "
            "reading any cross-run delta as a model effect."
        )

    return {
        "position": pos,
        "solve_affecting_commits_since_scored": distance,
        "max_commits": max_commits,
        "warnings": warnings,
        "stale": bool(warnings),
    }


def render(report: dict) -> str:
    """Human-readable report (the CI log surface)."""
    pos = report["position"]
    gating = pos.get("gating_class")
    gate = pos.get("gating") or pos
    lines = [
        "=" * 72,
        "FORECAST BOARD STALENESS (FR-21) — WARN-level, never blocking",
        "=" * 72,
        f"  HEAD                : {pos['head_sha']}",
        f"  gate evidence       : {gating or '(no verdict artifact — whole board)'}",
        f"  newest scored sha   : {gate['newest_scored_at_sha'] or '(none recorded)'}",
        f"  newest scored date  : {gate['newest_scored_at_date'] or '(none recorded)'}",
        f"  stamped / scored    : {pos['n_stamps']} stamped, {pos['n_scored']} scored"
        " (whole board)",
        "  solve-affecting Δ   : "
        + (
            "(unknown)"
            if report["solve_affecting_commits_since_scored"] is None
            else f"{report['solve_affecting_commits_since_scored']} commit(s) "
            f"(threshold {report['max_commits']})"
        ),
        f"  distinct epochs     : {len(pos['cache_epochs'])}",
        "  board inputs        : "
        + (
            "all present"
            if not pos.get("missing_inputs")
            else f"{len(pos['missing_inputs'])} MISSING "
            f"({', '.join(pos['missing_inputs'])})"
        ),
    ]
    # Per-class breakdown: the whole point of the FFR-3A split is that these
    # numbers move independently, so they are printed independently.
    by_class = pos.get("by_class") or {}
    if by_class:
        lines.append("  per class           :")
        for name, cls in by_class.items():
            marker = " <- gate evidence" if name == gating else ""
            lines.append(
                f"      {name:<20s} {cls['n_stamps']:>3d} stamped, "
                f"{cls['n_scored']:>3d} scored, newest "
                f"{cls['newest_scored_at_sha'] or '(none)'} "
                f"@ {cls['newest_scored_at_date'] or '(none)'}{marker}"
            )
    if pos.get("epoch_spread_note"):
        lines.append(f"  note: {pos['epoch_spread_note']}")
    lines.append("-" * 72)
    if report["warnings"]:
        for w in report["warnings"]:
            lines.append(f"  WARN: {w}")
    else:
        lines.append("  OK: the board's evidence is current with HEAD.")
    lines.append("=" * 72)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--max-commits",
        type=int,
        default=DEFAULT_MAX_COMMITS,
        help=f"solve-affecting commits tolerated past the newest scored sha "
        f"(default {DEFAULT_MAX_COMMITS})",
    )
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument(
        "--fail-on-stale",
        action="store_true",
        help="exit 1 when stale. NOT used in CI — this check is WARN-level so "
        "backcast velocity is never blocked by forecast-board freshness.",
    )
    args = ap.parse_args(argv)

    report = evaluate(args.max_commits)
    print(json.dumps(report, indent=2) if args.json else render(report))
    return 1 if (args.fail_on_stale and report["stale"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
