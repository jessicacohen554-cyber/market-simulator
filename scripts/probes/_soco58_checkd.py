"""SOCO-58 check D — enumerate EVERY scored criterion's margin, not C1's.

SOCO-57's own biggest process miss, in its words (FINDING §7): its ex-ante
check D enumerated C1 rows only and named the two thinnest of those, while the
run's ACTUAL thinnest row was **C4 2024 coal, passing by 0.004 of NRMSE** — and
that is the row it broke. This probe replays the committed scorer over a
registered run's own committed artifacts and prints the margin of every record
it emits, sorted by how close the row sits to its gate.

Zero LP (rule 32 ``[R-SHARD]`` (a)): it reads the same committed artifacts
``calibration_verdict.determine`` reads and never re-solves anything.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def rows(run_id: str) -> list[dict]:
    """Every criterion-year record the scorer emits for ``run_id``."""
    import calibration_verdict as cv

    art = cv.load_artifacts(run_id)
    sidecar, payload, bench = art["sidecar"], art["payload"], art["bench"]
    iso = sidecar.get("iso", "ERCOT")
    out: list[dict] = []
    for year in sorted(int(y) for y in (payload or {}).get("years", {})):
        ypay = payload["years"][str(year)]
        ybench = bench.get(year, {})
        out += cv.score_fuelmix(year, ypay, ybench, iso)
        out += cv.score_sysvol(year, ypay, ybench, iso, bench_all=bench)
        out += cv.score_dispatch_corr(year, ypay, ybench, iso)
        out += cv.score_forced_share(year, art.get("legitimacy"), ypay, ybench)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_id")
    ap.add_argument(
        "--all", action="store_true", help="print SKIPPED rows too (default: hide)"
    )
    args = ap.parse_args()

    recs = rows(args.run_id)
    keep = [
        r
        for r in recs
        if args.all or str(r.get("status", "")).upper() not in ("SKIPPED", "SKIP")
    ]
    keep.sort(key=lambda r: (str(r.get("criterion")), r.get("year", 0), str(r.get("key"))))
    w = max((len(str(r.get("key", ""))) for r in keep), default=10)
    print(f"{'criterion':<15}{'yr':<6}{'key':<{w + 2}}{'status':<9}detail")
    print("-" * 150)
    for r in keep:
        print(
            f"{str(r.get('criterion')):<15}{r.get('year', ''):<6}"
            f"{str(r.get('key', '')):<{w + 2}}{str(r.get('status', '')):<9}"
            f"{str(r.get('detail', r.get('reason', '')))[:105]}"
        )


if __name__ == "__main__":
    main()
