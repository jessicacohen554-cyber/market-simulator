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
    ap.add_argument(
        "--backfill-from",
        type=int,
        default=None,
        help="also compute the BTM frame with --btm-backfill-year set to this "
             "vintage (the incomplete-923 repair path)",
    )
    ap.add_argument("--json-out")
    args = ap.parse_args()

    import run_calibration_full as rcf
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia923 import load_monthly_generation

    generation = load_monthly_generation()
    parasitic_factors = rcf._parasitic_factor_map()
    iso_config = get_iso_config(args.iso)
    out: dict = {"iso": args.iso, "years": {}}

    for year in args.years:
        # NOTE: (iso, iso_config, year) -- the year selects that vintage's
        # EIA-860 CHP designation, which is what buckets a plant CC_CHP vs
        # CT_CHP. Dropping it silently loads the default vintage.
        group_by_code = rcf._fleet_group_by_code(args.iso, iso_config, year)
        campd_year = rcf._campd_hourly_frame(year, args.iso, parasitic_factors, 8760)

        campd_active = None
        if campd_year is not None:
            _bp = campd_year.groupby("plant_id")["net_mw"].sum()
            campd_active = set(_bp[_bp > 0.0].index.astype(int))

        # --- benchmark side (the classFull minuend) -------------------------
        # UNREPAIRED: no donor backfill on the minuend -- the pre-fix path.
        e923_bench = rcf._benchmark_eia923_frame(
            year, generation, args.iso, campd_year, group_by_code, None
        )
        bench_cls = (
            e923_bench.groupby("klass")["annual_mwh"].sum() / _MWH_PER_TWH
        ).to_dict()

        # REPAIRED: the same donor backfill the BTM side gets (the fix).
        bench_bf_cls: dict[str, float] = {}
        if args.backfill_from is not None:
            _eb = rcf._benchmark_eia923_frame(
                year,
                generation,
                args.iso,
                campd_year,
                group_by_code,
                None,
                btm_backfill_year=args.backfill_from,
                campd_active=campd_active,
            )
            bench_bf_cls = (
                _eb.groupby("klass")["annual_mwh"].sum() / _MWH_PER_TWH
            ).to_dict()

        btm = rcf._btm_frame(
            year,
            "P1",
            generation,
            iso=args.iso,
            group_by_code=group_by_code,
        )
        btm_cls = dict(zip(btm["klass"], btm["btm_twh"])) if not btm.empty else {}

        # Same frame WITH the prior-vintage BTM backfill armed (the
        # --btm-backfill-year path). The backfill lifts the SUBTRAHEND only:
        # `classFull`'s minuend `_benchmark_eia923_frame` has no matching
        # CHP repair (its CAMPD backfill is explicitly non-CHP), so any plant
        # the backfill carries in enters the subtraction without entering the
        # thing being subtracted from.
        btm_bf_cls: dict[str, float] = {}
        if args.backfill_from is not None:
            _bf = rcf._btm_frame(
                year,
                "P1",
                generation,
                btm_backfill_year=args.backfill_from,
                campd_active=campd_active,
                iso=args.iso,
                group_by_code=group_by_code,
            )
            btm_bf_cls = dict(zip(_bf["klass"], _bf["btm_twh"])) if not _bf.empty else {}

        # --- the invariant ---------------------------------------------------
        rows = []
        for k in CHP_CLASSES:
            b = float(bench_cls.get(k, 0.0))
            m = float(btm_cls.get(k, 0.0))
            mb = float(btm_bf_cls.get(k, 0.0)) if btm_bf_cls else None
            bb = float(bench_bf_cls.get(k, 0.0)) if bench_bf_cls else None
            rows.append(
                {
                    "class": k,
                    "e923_bench_twh": round(b, 4),
                    "btm_twh": round(m, 4),
                    "classFull_twh": round(b - m, 4),
                    "invariant_ok": bool(m <= b + 1e-9),
                    "btm_backfilled_twh": round(mb, 4) if mb is not None else None,
                    # PRE-FIX: repaired subtrahend against an unrepaired minuend
                    "classFull_backfilled_twh": (
                        round(b - mb, 4) if mb is not None else None
                    ),
                    "invariant_ok_backfilled": (
                        bool(mb <= b + 1e-9) if mb is not None else None
                    ),
                    # POST-FIX: both sides repaired from the same donor
                    "e923_bench_repaired_twh": round(bb, 4) if bb is not None else None,
                    "classFull_repaired_twh": (
                        round(bb - mb, 4) if (bb is not None and mb is not None) else None
                    ),
                    "invariant_ok_repaired": (
                        bool(mb <= bb + 1e-9)
                        if (bb is not None and mb is not None)
                        else None
                    ),
                }
            )

        print(f"\n===== {args.iso} {year} =====")
        print(
            f"{'class':<10}{'e923':>10}{'btm':>9}{'classFull':>11}  inv "
            f"| PRE-FIX {'btmBF':>9}{'cFull':>9} {'inv':>6} "
            f"| POST-FIX {'e923R':>9}{'cFullR':>9} {'inv':>6}"
        )
        for r in rows:
            _bf = r.get("btm_backfilled_twh")
            _cf = r.get("classFull_backfilled_twh")
            _er = r.get("e923_bench_repaired_twh")
            _cr = r.get("classFull_repaired_twh")
            line = (
                f"{r['class']:<10}{r['e923_bench_twh']:>10.4f}{r['btm_twh']:>9.4f}"
                f"{r['classFull_twh']:>11.4f}  {'ok' if r['invariant_ok'] else 'BROKEN':>6}"
            )
            if _bf is not None:
                line += (
                    f" |          {_bf:>9.4f}{_cf:>9.4f} "
                    f"{'ok' if r['invariant_ok_backfilled'] else 'BROKEN':>6}"
                )
            if _er is not None:
                line += (
                    f" |           {_er:>9.4f}{_cr:>9.4f} "
                    f"{'ok' if r['invariant_ok_repaired'] else 'BROKEN':>6}"
                )
            print(line)

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
