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

* **HARD (exit non-zero).** The PAYLOAD fingerprint of the builder state that
  wrote the part — resolved from the ``meta.builderFingerprint`` it records,
  per ``scripts/lib/bench_stamp.part_payload_fingerprint`` — differs from
  HEAD's, or cannot be resolved at all (an unknown builder state, or a part
  predating the stamp). Either way the part cannot be shown to reproduce, so a
  C1 verdict scored against it is not reproducible. Fixing it means
  regenerating the part (``run_calibration_full.py --rebuild-benchmark
  <bundle>`` then ``dashboard_add_run.py``) and re-verifying that ISO's keeper.

  **The decision moved from the AGGREGATE to the PAYLOAD on 2026-09-06** (Y-17,
  director's option (a) on ``FINDING-y15-flipset-sweep-2026-09-06.md`` §3.5;
  this lane: ``FINDING-y17-bench-payload-fingerprint-2026-09-06.md``).
  ``bench_stamp.py`` is a member of its own ``BUILDER_SOURCES``, so an edit to
  the STAMPING logic moved the aggregate for every part in existence — which
  made the aggregate degenerate as a reproducibility test, unable to return
  "equal" for any part built before such an edit even when its payload sources
  were byte-identical to HEAD's. The aggregate is NOT deleted: it remains the
  recorded provenance stamp, the key the payload state is resolved from, and
  the identity the SOFT tier's drift is measured against. A part whose
  aggregate is superseded but whose payload resolves to HEAD's is reported as
  a ``notice`` — visible, never gating.
* **SOFT (reported, never gates).** The fingerprint matches but engine commits
  under ``src/market_sim/data|config`` have landed since the part was last
  committed. The builder imports the engine for the plant→class map, the CHP
  shares and the EIA-923 reconciliation, so those CAN move a part's numbers —
  but they move on nearly every lane's edit, and gating on them would mark every
  part stale within a week and train everyone to ignore the signal. It is
  reported as a count so a session can judge whether to regenerate before
  trusting a C1 verdict.

  **The SOFT leg's arithmetic was WRONG until 2026-09-01** (audit board
  checklist item 12; repair recorded in
  ``docs/FINDING-audit-gate-repairs-2026-09.md``). It compared the part's
  **author** date, truncated to a calendar day, against a ``--since`` filter
  that git applies to the **committer** date — a date-kind mismatch layered on
  day granularity, evaluated in the runner's local timezone. On the record the
  count read 6 → 0 → 20 across three consecutive readings with the ERCOT/NYISO
  bench bytes never touched, and one commit tripped it 38 minutes after it was
  authored. Both sides now use the committer instant in offset-bearing
  ISO-8601, so the comparison is between two absolute points in time and is
  reproducible from any container. Re-measured at ``6f6e9d11`` the same bytes
  read **20 of 20 parts with drift, not 19**: MISO/2023 read zero only because
  its bench commit shared calendar day 2026-08-31 with the engine commits, and
  the per-part counts were understated 5 → 8 on the other nineteen. The old
  reading was UNDERSTATED here; the direction is not fixed, though — a runner
  east of the commits' offset would have over-counted the same bytes.

Usage::

    python scripts/check_bench_freshness.py            # all ISOs
    python scripts/check_bench_freshness.py --iso NYISO
    python scripts/check_bench_freshness.py --warn-only # report, never exit 1
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.lib.backcast_artifacts import load_bench_part  # noqa: E402
from scripts.lib.bench_stamp import (  # noqa: E402
    builder_fingerprint,
    part_fingerprint,
    part_payload_fingerprint,
    payload_fingerprint,
    payload_origin,
)

BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench"

#: Engine paths the builder imports that can move a part's numbers. Reported,
#: never gated — see the module docstring.
ENGINE_PATHS: tuple[str, ...] = ("src/market_sim/data/", "src/market_sim/config/")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=False
    ).stdout.strip()


def _last_commit(rel: str) -> tuple[str, str]:
    """Return ``(short sha, committer instant)`` for the last commit touching ``rel``.

    ``%cI`` is the COMMITTER date in strict ISO-8601 **with the commit's own
    UTC offset**, e.g. ``2026-08-30T14:53:31-07:00``. Both properties are
    deliberate and both were wrong before 2026-09-01 (audit checklist item 12):

    * **Committer, not author.** This value is fed to ``git log --since``,
      which filters on the COMMITTER date. The old code read ``%ad`` (author
      date) and compared it against a committer-date filter — a date-KIND
      mismatch. A rebased or cherry-picked engine commit can carry an author
      date well before its committer date, which is how one commit tripped
      the drift signal 38 minutes after it was authored.
    * **A precise instant, not a calendar day.** The old code read
      ``--date=short`` and hand-appended ``23:59:59``, so the cutoff landed at
      the end of the bench part's calendar day *in the runner's local
      timezone* rather than at the moment the part was written. Every engine
      commit in the remainder of that day was silently discarded (measured
      2026-09-01 on a UTC runner: NYISO/2025 read 5 engine commits where the
      true count is 8), and the SAME bytes read differently from a container
      in another timezone — the 6 -> 0 -> 20 swing on the record.

    Args:
        rel: Repo-relative path of the bench part.

    Returns:
        ``(sha, instant)``; ``("", "")`` when the path has no commit (a part
        written but not yet committed).
    """
    out = _git("log", "-1", "--format=%h %cI", "--", rel)
    if not out:
        return ("", "")
    sha, _, instant = out.partition(" ")
    return sha, instant.strip()


def _engine_commits_since(instant: str, exclude_sha: str) -> int:
    """Count engine commits committed at or after ``instant``.

    ``instant`` is an offset-bearing ISO-8601 timestamp, so the comparison is
    between two absolute points in time and does not depend on the runner's
    timezone at all — the reading is reproducible from any container.

    ``--since`` is INCLUSIVE (verified 2026-09-01: a commit passed its own
    ``%cI`` matches itself), so a bench part whose own commit also touched an
    engine path would otherwise count itself. ``exclude_sha`` is what stops
    that, and it is the reason this takes the sha as well as the instant.

    Args:
        instant: The bench part's committer instant, from :func:`_last_commit`.
        exclude_sha: That commit's short sha, never counted as drift.

    Returns:
        The number of distinct engine commits since the part was committed.
    """
    if not instant:
        return 0
    out = _git("log", f"--since={instant}", "--format=%h", "--", *ENGINE_PATHS)
    return len([s for s in out.splitlines() if s and s != exclude_sha])


def _as_utc(instant: str) -> str:
    """Render an offset-bearing ISO instant in UTC, for a comparable report line.

    The stored value carries the committer's own offset, which differs commit
    to commit; printing it raw makes two parts written a minute apart look
    hours apart. Reporting in UTC keeps the human reading stable no matter
    where the part was written or where the check runs.

    Args:
        instant: An ISO-8601 timestamp with offset, or ``""``.

    Returns:
        ``YYYY-MM-DDTHH:MM:SSZ``, or the input unchanged if it will not parse.
    """
    try:
        return (
            datetime.fromisoformat(instant)
            .astimezone(timezone.utc)
            .strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    except ValueError:
        return instant


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
    current_payload = payload_fingerprint()
    print(f"builder fingerprint at HEAD: {current} (aggregate, recorded stamp)")
    print(f"payload fingerprint at HEAD: {current_payload} (decides STALE)")
    if not BENCH_DIR.exists():
        print("no bench parts on disk — nothing to check")
        return 0

    stale: list[str] = []
    soft: list[str] = []
    superseded: dict[str, list[str]] = {}
    for iso_dir in sorted(BENCH_DIR.iterdir()):
        if not iso_dir.is_dir():
            continue
        if args.iso and iso_dir.name != args.iso.upper():
            continue
        for part in sorted(iso_dir.glob("*.json.gz")):
            rel = str(part.relative_to(REPO))
            obj = load_bench_part(part)
            fp = part_fingerprint(obj)
            payload_fp = part_payload_fingerprint(obj)
            origin = payload_origin(obj)
            sha, instant = _last_commit(rel)
            if payload_fp != current_payload:
                stale.append(rel)
                print(
                    f"::error file={rel}::bench part is STALE — its builder's "
                    f"PAYLOAD fingerprint is "
                    f"{payload_fp or '(unresolvable: unknown builder state)'} "
                    f"but HEAD's is {current_payload} (recorded aggregate stamp: "
                    f"{fp or 'none: predates the stamp'}). Every {iso_dir.name} C1 "
                    f"verdict scored against it is not reproducible from the "
                    f"builder at HEAD. Regenerate (run_calibration_full.py "
                    f"--rebuild-benchmark <bundle>, then dashboard_add_run.py) and "
                    f"re-verify {iso_dir.name}'s keeper."
                )
                continue
            if origin == "historical":
                # The part predates HEAD's stamping logic but its PAYLOAD sources
                # were identical, so its numbers ARE what the builder at HEAD
                # would produce. Collected and reported ONCE per distinct stamp
                # below rather than annotated per part: an edit to bench_stamp.py
                # puts every part in this state at once, and 24 identical notices
                # is the kind of noise that trains a reader to skip the output —
                # the failure mode this gate exists to prevent (Y-17).
                superseded.setdefault(fp or "", []).append(rel)
            n = _engine_commits_since(instant, sha)
            if n:
                soft.append(rel)
                print(
                    f"::warning file={rel}::bench part reproduces at HEAD "
                    f"but {n} engine commit(s) under {', '.join(ENGINE_PATHS)} have "
                    f"landed since it was committed ({_as_utc(instant)}). Those can "
                    f"move the plant->class map, the CHP shares or the EIA-923 "
                    f"reconciliation. Not gated; regenerate before trusting a "
                    f"marginal C1 verdict."
                )

    for old, rels in sorted(superseded.items()):
        names = ", ".join(
            f"{Path(r).parent.name}/{Path(r).stem.split('.')[0]}" for r in sorted(rels)
        )
        print(
            f"::notice::{len(rels)} part(s) carry superseded aggregate stamp "
            f"{old or '(none: predates the stamp)'} (HEAD's is {current}) but their "
            f"builder's payload sources hash to {current_payload}, identical to "
            f"HEAD's — so their numbers ARE reproducible. Provenance note only; not "
            f"gated. Parts: {names}"
        )

    n_parts = sum(
        1
        for d in BENCH_DIR.iterdir()
        if d.is_dir() and (not args.iso or d.name == args.iso.upper())
        for _ in d.glob("*.json.gz")
    )
    n_superseded = sum(len(v) for v in superseded.values())
    print(
        f"bench freshness: {n_parts} part(s) checked, {len(stale)} STALE, "
        f"{n_superseded} on a superseded stamp with a reproducing payload, "
        f"{len(soft)} with engine drift"
    )
    if stale and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
