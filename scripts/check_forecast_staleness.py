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
manifest meta), takes the NEWEST ``scored_at_sha`` on the board, and counts the
commits touching **solve-affecting paths** that have landed since. Past the
threshold it prints a warning.

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

#: Board artifacts carrying provenance stamps (repo-relative).
BOARD_PATHS = (
    "frontend/data/forecast/registry",
    "frontend/data/forecast/ff-verdicts.json",
    "frontend/data/hindcast",
)

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


def board_position(paths: list[Path] | None = None) -> dict:
    """Summarize the board's staleness position from its provenance stamps."""
    targets = paths if paths is not None else [REPO / p for p in BOARD_PATHS]
    stamps = [s for _, s in fp.collect_stamps(targets)]
    dated = [s for s in stamps if s.get("scored_at_date") and s.get("scored_at_sha")]
    newest = max(dated, key=lambda s: s["scored_at_date"], default=None)
    epochs = sorted({s["cache_epoch"] for s in stamps if s.get("cache_epoch")})
    return {
        "n_stamps": len(stamps),
        "n_scored": len(dated),
        "newest_scored_at_sha": (newest or {}).get("scored_at_sha"),
        "newest_scored_at_date": (newest or {}).get("scored_at_date"),
        "cache_epochs": epochs,
        "head_sha": fp.head_sha(),
    }


def evaluate(max_commits: int = DEFAULT_MAX_COMMITS, paths=None) -> dict:
    """Return the full staleness report: position, distance, and any warnings."""
    pos = board_position(paths)
    warnings: list[str] = []
    distance = None

    if not pos["n_stamps"]:
        warnings.append(
            "The forecast board carries NO provenance stamps at all — nothing on "
            "it records when or against what it was scored. Re-score through "
            "scripts/forecast_verdict.py (FFR-3A) to populate them."
        )
    elif not pos["newest_scored_at_sha"]:
        warnings.append(
            f"{pos['n_stamps']} board artifact(s) are stamped but NONE records a "
            "scored-at sha — every stamp is UNSCORED (predates the machinery, or "
            "its verdict was never re-scored through the stamped scorer). Absence "
            "of a scoring record is not evidence of freshness."
        )
    else:
        distance = solve_affecting_commits_since(pos["newest_scored_at_sha"])
        if distance is None:
            warnings.append(
                f"Cannot measure distance from the newest scored sha "
                f"{pos['newest_scored_at_sha']} — it is not reachable in this "
                "checkout (shallow clone, or scored on an unmerged branch). "
                "Staleness is UNKNOWN, which is not the same as fresh."
            )
        elif distance > max_commits:
            warnings.append(
                f"The forecast board's newest evidence was scored at "
                f"{pos['newest_scored_at_sha']} ({pos['newest_scored_at_date']}), "
                f"and {distance} solve-affecting commit(s) have landed since "
                f"(threshold {max_commits}). The verdicts on the board may no "
                "longer describe this code — this is the FR-21 'ten days dark' "
                "failure mode. Re-score the battery, or record why the drift is "
                "immaterial."
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
    lines = [
        "=" * 72,
        "FORECAST BOARD STALENESS (FR-21) — WARN-level, never blocking",
        "=" * 72,
        f"  HEAD                : {pos['head_sha']}",
        f"  newest scored sha   : {pos['newest_scored_at_sha'] or '(none recorded)'}",
        f"  newest scored date  : {pos['newest_scored_at_date'] or '(none recorded)'}",
        f"  stamped / scored    : {pos['n_stamps']} stamped, {pos['n_scored']} scored",
        "  solve-affecting Δ   : "
        + (
            "(unknown)"
            if report["solve_affecting_commits_since_scored"] is None
            else f"{report['solve_affecting_commits_since_scored']} commit(s) "
            f"(threshold {report['max_commits']})"
        ),
        f"  distinct epochs     : {len(pos['cache_epochs'])}",
    ]
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
