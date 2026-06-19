#!/usr/bin/env python3
"""Derive the per-plant CC capacity reconciliation for ERCOT (backcast).

Several grid-serving combined cycles produced **more** than their curated bin
nameplate in the CEMS record — the cold-weather (winter) over-rating an F-class
CC delivers when the air is dense, which the standard nameplate omits — so the
LP cannot reach the output the real plant did and logs zero hours in its top CF
band (see `docs/cc-high-cf-investigation.md`, Freestone). This script writes a
**raise-only** reconciliation: each CC_REGULAR plant's LP capacity is lifted to
the larger of its current nameplate and its **demonstrated CAMPD peak**
(99.9th percentile of net MW across the backcast years, robust to single-hour
glitches). It never lowers a nameplate — a plant that simply never dispatched
to its rating keeps it; only demonstrated, measured headroom is added. EIA-860
winter capacity is carried alongside as corroborating provenance.

Output: `data/raw/_processed-legacy/cc_capacity_reconcile_ERCOT.csv`
(`plant_code, plant_name, current_mw, campd_p999_mw, eia860_winter_mw,
reconciled_mw, delta_pct, source`), consumed by `load_campd_bins` under
`ScenarioConfig.cc_capacity_reconcile`.

    uv run python scripts/derive_cc_capacity_reconcile.py \
        --campd results/calibration/run115b_ccduct_prb73_relief06/campd.parquet
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
# Minimum fractional change to bother writing a row (avoid float noise).
_MIN_DELTA = 0.01


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--campd",
        type=Path,
        default=REPO
        / "results/calibration/run115b_ccduct_prb73_relief06"
        / "campd.parquet",
        help="a calibration bundle's campd.parquet (CEMS net MW, all years)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=REPO / "data/raw/_processed-legacy/cc_capacity_reconcile_ERCOT.csv",
    )
    args = ap.parse_args()

    csv = pd.read_csv(REPO / "data/raw/reference/custom-bin-assignments.csv")
    cc = csv[csv["Plant_Group"] == "CC_REGULAR"]

    campd = pd.read_parquet(args.campd)
    # Demonstrated peak = 99.9th pct of net MW across every backcast year,
    # so a plant that only hit its cold-weather rating in one year still
    # gets credited for it.
    p999 = campd.groupby("plant_id")["net_mw"].quantile(0.999)

    e860 = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    e860["Winter Capacity (MW)"] = pd.to_numeric(
        e860["Winter Capacity (MW)"], errors="coerce"
    )
    winter = e860.groupby("Plant Code")["Winter Capacity (MW)"].sum()

    rows = []
    for _, r in cc.iterrows():
        code = int(r["Plant_Code"])
        cur = float(r["Nameplate_MW"])
        peak = float(p999.get(code, np.nan))
        win = float(winter.get(code, np.nan))
        if np.isnan(peak):
            continue
        reconciled = max(cur, peak)
        delta = (reconciled - cur) / cur
        if delta < _MIN_DELTA:  # raise-only; skip no-ops and (never) cuts
            continue
        rows.append(
            {
                "plant_code": code,
                "plant_name": str(r["Plant_Name"]),
                "current_mw": round(cur, 1),
                "campd_p999_mw": round(peak, 1),
                "eia860_winter_mw": round(win, 1) if not np.isnan(win) else "",
                "reconciled_mw": round(reconciled, 1),
                "delta_pct": round(100 * delta, 1),
                "source": "campd_demonstrated_peak",
            }
        )

    out = pd.DataFrame(rows).sort_values("delta_pct", ascending=False)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(args.out, index=False)
    print(f"wrote {args.out}  ({len(out)} CC_REGULAR plants raised)")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
