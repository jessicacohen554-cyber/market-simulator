#!/usr/bin/env python3
"""miso-267 STEP 1: score a registered run against two bench roots and diff it all.

``calibration_verdict.determine`` reads the per-(ISO, year) bench parts from its
module-level ``BENCH_DIR``. Pointing that at a scratch root holding candidate
parts scores the run's COMMITTED model side against candidate actuals with
nothing under ``frontend/`` touched, so a bench refresh can be judged before it
is written. Reported at full magnitude, per the charter: the determination, the
grade summary, every criterion's status, and every per-(criterion, key, year)
record whose status, actual or model value moved.

Usage::

    .venv/bin/python scripts/probes/_miso267_rescore.py <run_id> \
        --candidate-bench <root> [--years 2023 2024 2025] [--out <json>]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))


def _score(run_id: str, bench_root: Path | None, years: list[int] | None) -> dict:
    """``determine(run_id)`` with ``BENCH_DIR`` optionally redirected."""
    import scripts.calibration_verdict as cv

    saved = cv.BENCH_DIR
    try:
        if bench_root is not None:
            cv.BENCH_DIR = bench_root
        with contextlib.redirect_stderr(io.StringIO()):
            return cv.determine(run_id, years=years)
    finally:
        cv.BENCH_DIR = saved


def _index(verdict: dict) -> dict[tuple, dict]:
    out = {}
    for crit, rec in verdict["criteria"].items():
        for r in rec.get("records", []):
            out[(crit, str(r.get("key")), r.get("year"))] = r
    return out


def diff(a: dict, b: dict) -> dict:
    """Everything that moved between two verdicts of the same run."""
    moved: dict = {
        "determination": [a["determination"], b["determination"]],
        "grade_summary": [a.get("grade_summary"), b.get("grade_summary")],
        "reasons": [a.get("reasons"), b.get("reasons")],
        "criteria": {},
        "records": [],
    }
    for crit in sorted(set(a["criteria"]) | set(b["criteria"])):
        sa = a["criteria"].get(crit, {}).get("status")
        sb = b["criteria"].get(crit, {}).get("status")
        moved["criteria"][crit] = [sa, sb]
    ia, ib = _index(a), _index(b)
    for k in sorted(set(ia) | set(ib), key=str):
        ra, rb = ia.get(k, {}), ib.get(k, {})
        fields = ("status", "actual", "model", "magnitude")
        if any(ra.get(f) != rb.get(f) for f in fields):
            moved["records"].append(
                {"criterion": k[0], "key": k[1], "year": k[2]}
                | {f: [ra.get(f), rb.get(f)] for f in fields}
            )
    return moved


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_id")
    ap.add_argument("--candidate-bench", type=Path, required=True)
    ap.add_argument("--years", nargs="+", type=int)
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    before = _score(args.run_id, None, args.years)
    after = _score(args.run_id, args.candidate_bench.resolve(), args.years)
    d = diff(before, after)
    span = "years " + " ".join(map(str, args.years)) if args.years else "full span"
    print(f"{args.run_id} ({span})")
    print(f"  determination : {d['determination'][0]} -> {d['determination'][1]}")
    print(f"  grade_summary : {d['grade_summary'][0]} -> {d['grade_summary'][1]}")
    for crit, (sa, sb) in d["criteria"].items():
        flag = "" if sa == sb else "   <-- MOVED"
        print(f"  {crit:14s}: {sa} -> {sb}{flag}")
    flips = [r for r in d["records"] if r["status"][0] != r["status"][1]]
    print(f"  records moved : {len(d['records'])} (status flips: {len(flips)})")
    for r in d["records"]:
        s = (
            ""
            if r["status"][0] == r["status"][1]
            else f"  STATUS {r['status'][0]} -> {r['status'][1]}"
        )
        print(
            f"    {r['criterion']:12s} {r['year']} {r['key']:14s} "
            f"actual {r['actual'][0]} -> {r['actual'][1]} | "
            f"{r['magnitude'][0]} -> {r['magnitude'][1]}{s}"
        )
    if args.out:
        args.out.write_text(json.dumps(d, indent=1, default=str) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
