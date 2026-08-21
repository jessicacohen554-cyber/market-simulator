#!/usr/bin/env python3
"""Fail when a committed benchmark part predates the builder that produces it.

THE DEFECT (nyiso-148, 2026-08-21; owner ruling "sweep and fix the mechanism").
The shared per-(ISO, year) benchmark part under
``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` is refreshed only when a
registering bundle happens to carry the benchmark inputs. Parts are
byte-deterministic, so a part that has gone un-refreshed shows NO git diff and
NO warning — it simply keeps scoring every run of that ISO against numbers the
current builder would not reproduce. NYISO's part went un-refreshed from
2026-08-17; regenerating it moved CC_REGULAR-2024's metered actual by ~4 TWh
and flipped EVERY registered NYISO run to NOT-YET, the keeper included
(``results/calibration/FINDING-nyiso148-bench-regeneration-instability-2026-08-21.md``).

WHAT THIS CHECKS, in two tiers:

* **HARD (exit non-zero).** The part's ``meta.builderFingerprint`` differs from
  the fingerprint of the builder sources at HEAD — or is ABSENT, which means the
  part predates the stamp. Either way the part provably was not written by the
  builder that would run now, so a C1 verdict scored against it is not
  reproducible. Fixing it means regenerating the part
  (``run_calibration_full.py --rebuild-benchmark <bundle>`` then
  ``dashboard_add_run.py``) and re-verifying that ISO's keeper.
* **SOFT (reported, never gates).** The fingerprint matches but engine commits
  under ``src/market_sim/data|config`` have landed since the part was last
  committed. The builder imports the engine for the plant→class map, the CHP
  shares and the EIA-923 reconciliation, so those CAN move a part's numbers —
  but they move on nearly every lane's edit, and gating on them would mark every
  part stale within a week and train everyone to ignore the signal. It is
  reported as a count so a session can judge whether to regenerate before
  trusting a C1 verdict.

Usage::

    python scripts/check_bench_freshness.py            # all ISOs
    python scripts/check_bench_freshness.py --iso NYISO
    python scripts/check_bench_freshness.py --warn-only # report, never exit 1
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.lib.backcast_artifacts import load_bench_part  # noqa: E402
from scripts.lib.bench_stamp import builder_fingerprint, part_fingerprint  # noqa: E402

BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench"

#: Engine paths the builder imports that can move a part's numbers. Reported,
#: never gated — see the module docstring.
ENGINE_PATHS: tuple[str, ...] = ("src/market_sim/data/", "src/market_sim/config/")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
    ).stdout.strip()


def _last_commit(rel: str) -> tuple[str, str]:
    out = _git("log", "-1", "--format=%h %ad", "--date=short", "--", rel)
    if not out:
        return ("", "")
    sha, _, date = out.partition(" ")
    return sha, date


def _engine_commits_since(date: str, exclude_sha: str) -> int:
    if not date:
        return 0
    out = _git(
        "log", f"--since={date} 23:59:59", "--format=%h", "--", *ENGINE_PATHS
    )
    return len([s for s in out.splitlines() if s and s != exclude_sha])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default=None, help="check one ISO only")
    ap.add_argument(
        "--warn-only",
        action="store_true",
        help="report staleness but always exit 0 (for a non-gating context)",
    )
    args = ap.parse_args()

    current = builder_fingerprint()
    print(f"builder fingerprint at HEAD: {current}")
    if not BENCH_DIR.exists():
        print("no bench parts on disk — nothing to check")
        return 0

    stale: list[str] = []
    soft: list[str] = []
    for iso_dir in sorted(BENCH_DIR.iterdir()):
        if not iso_dir.is_dir():
            continue
        if args.iso and iso_dir.name != args.iso.upper():
            continue
        for part in sorted(iso_dir.glob("*.json.gz")):
            rel = str(part.relative_to(REPO))
            fp = part_fingerprint(load_bench_part(part))
            sha, date = _last_commit(rel)
            if fp != current:
                stale.append(rel)
                print(
                    f"::error file={rel}::bench part is STALE — carries builder "
                    f"fingerprint {fp or '(none: predates the stamp)'} but HEAD's "
                    f"is {current}. Every {iso_dir.name} C1 verdict scored against "
                    f"it is not reproducible from the builder at HEAD. Regenerate "
                    f"(run_calibration_full.py --rebuild-benchmark <bundle>, then "
                    f"dashboard_add_run.py) and re-verify {iso_dir.name}'s keeper."
                )
                continue
            n = _engine_commits_since(date, sha)
            if n:
                soft.append(rel)
                print(
                    f"::warning file={rel}::bench part matches the builder at HEAD "
                    f"but {n} engine commit(s) under {'/'.join(ENGINE_PATHS)} have "
                    f"landed since it was written ({date}). Those can move the "
                    f"plant->class map, the CHP shares or the EIA-923 "
                    f"reconciliation. Not gated; regenerate before trusting a "
                    f"marginal C1 verdict."
                )

    n_parts = sum(
        1
        for d in BENCH_DIR.iterdir()
        if d.is_dir() and (not args.iso or d.name == args.iso.upper())
        for _ in d.glob("*.json.gz")
    )
    print(
        f"bench freshness: {n_parts} part(s) checked, {len(stale)} STALE, "
        f"{len(soft)} with engine drift"
    )
    if stale and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
