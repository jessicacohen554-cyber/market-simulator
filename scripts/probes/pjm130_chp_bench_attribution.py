"""pjm-130 — why does a committed PJM benchmark carry a NEGATIVE metered volume?

**No LP, no solve.** Reconstructs, from committed inputs only, the two halves of
the dashboard benchmark's grid-delivered CHP cell:

    classFull[k] = e923_bench[k] - btm[k]

where ``e923_bench`` is :func:`run_calibration_full._benchmark_eia923_frame` (the
bundle's ``eia923.parquet``) and ``btm`` is
:func:`run_calibration_full._btm_frame` (the bundle's ``btm.parquet``).

The committed `frontend/data/backcast/bench/PJM/2025.json.gz` reads
``classFull.CT_CHP = -0.3726 TWh`` against ``co2.btmClass.CT_CHP = 2.0959`` —
i.e. the benchmark asserts PJM's CT_CHP fleet delivered *negative* energy to the
grid in 2025. A metered volume cannot be negative; the subtrahend has escaped
its own minuend.

pjm-129 §6 surfaced the cell and was forbidden from touching it. This probe
localizes it. It answers ONE question:

    Is ``btm[k] <= e923_bench[k]`` violated because the two sides bucket the
    same plant's energy into DIFFERENT classes?

Both sides are supposed to be keyed on the same per-(plant, class) EIA-923
totals, so the invariant ``btm[k] <= e923_bench[k]`` should hold for every class
k by construction (the host share is a fraction <= 1). This prints, per CHP
class: both sides, the residual, and — when the invariant breaks — the per-plant
decomposition showing which plants contribute BTM to a class they contribute no
benchmark energy to.

Usage
-----
    PYTHONPATH=. .venv/bin/python scripts/probes/pjm130_chp_bench_attribution.py \
        --iso PJM --years 2023 2024 2025 \
        --json-out results/calibration/pjm130_chp_bench_attribution.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

CHP_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP")
_MWH_PER_TWH = 1e6


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="PJM")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out")
    args = ap.parse_args()

    import run_calibration_full as rcf
    from market_sim.data.campd import load_campd_unit_data
    from market_sim.data.eia923 import load_monthly_generation

    generation = load_monthly_generation()
    out: dict = {"iso": args.iso, "years": {}}

    for year in args.years:
        group_by_code = rcf._fleet_group_by_code(args.iso, year)
        try:
            campd_year = load_campd_unit_data(args.iso, year)
        except Exception as exc:  # pragma: no cover - diagnostic
            print(f"[{year}] campd unavailable ({exc}); backfill side skipped")
            campd_year = None

        # --- benchmark side (the classFull minuend) -------------------------
        e923_bench = rcf._benchmark_eia923_frame(
            year, generation, args.iso, campd_year, group_by_code, None
        )
        bench_cls = (
            e923_bench.groupby("klass")["annual_mwh"].sum() / _MWH_PER_TWH
        ).to_dict()

        # --- BTM side (the subtrahend) --------------------------------------
        btm = rcf._btm_frame(
            year,
            "P1",
            generation,
            iso=args.iso,
            group_by_code=group_by_code,
        )
        btm_cls = dict(zip(btm["klass"], btm["btm_twh"])) if not btm.empty else {}

        # --- the invariant ---------------------------------------------------
        rows = []
        for k in CHP_CLASSES:
            b = float(bench_cls.get(k, 0.0))
            m = float(btm_cls.get(k, 0.0))
            rows.append(
                {
                    "class": k,
                    "e923_bench_twh": round(b, 4),
                    "btm_twh": round(m, 4),
                    "classFull_twh": round(b - m, 4),
                    "invariant_ok": bool(m <= b + 1e-9),
                }
            )

        print(f"\n===== {args.iso} {year} =====")
        print(f"{'class':<10}{'e923_bench':>12}{'btm':>10}{'classFull':>12}  inv")
        for r in rows:
            print(
                f"{r['class']:<10}{r['e923_bench_twh']:>12.4f}{r['btm_twh']:>10.4f}"
                f"{r['classFull_twh']:>12.4f}  {'ok' if r['invariant_ok'] else 'BROKEN'}"
            )

        # --- per-plant decomposition for any broken class -------------------
        broken = [r["class"] for r in rows if not r["invariant_ok"]]
        detail: dict = {}
        if broken:
            # raw per-(plant, class) 923 totals — what _btm_frame keys off
            f923 = generation[generation["year"] == year].copy()
            f923["klass"] = [
                rcf._classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
                for f, pm, c, pid in zip(
                    f923["fuel_type"],
                    f923["prime_mover"],
                    f923["chp"],
                    f923["plant_id"],
                )
            ]
            raw = f923.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
            # benchmark per-(plant, class) — what classFull sums
            bench_pp = e923_bench.groupby(["plant_id", "klass"])["annual_mwh"].sum()
            for k in broken:
                members = [c for c, g in group_by_code.items() if g == k]
                recs = []
                for code in members:
                    r_raw = float(raw.get((int(code), k), 0.0)) / _MWH_PER_TWH
                    r_bench = float(bench_pp.get((int(code), k), 0.0)) / _MWH_PER_TWH
                    if r_raw <= 0.0 and r_bench <= 0.0:
                        continue
                    recs.append(
                        {
                            "plant_id": int(code),
                            "raw923_twh": round(r_raw, 5),
                            "bench923_twh": round(r_bench, 5),
                            "delta_twh": round(r_raw - r_bench, 5),
                        }
                    )
                recs.sort(key=lambda r: -abs(r["delta_twh"]))
                detail[k] = recs
                print(f"\n  {k}: plants where the BTM key and the benchmark disagree")
                print(f"  {'plant':>8}{'raw923':>12}{'bench923':>12}{'delta':>12}")
                for r in recs[:15]:
                    print(
                        f"  {r['plant_id']:>8}{r['raw923_twh']:>12.5f}"
                        f"{r['bench923_twh']:>12.5f}{r['delta_twh']:>12.5f}"
                    )
                tot = sum(r["delta_twh"] for r in recs)
                print(f"  {'TOTAL':>8}{'':>12}{'':>12}{tot:>12.5f}")

        out["years"][str(year)] = {"rows": rows, "detail": detail}

    if args.json_out:
        p = REPO / args.json_out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
