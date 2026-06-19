#!/usr/bin/env python3
"""THROWAWAY DIAGNOSTIC PROBE (not a keeper). Test the SRMC thesis: price BOTH
the CAISO gas offer near cost (flatten the econ markup) AND the cheap import
blocks lower, to see whether the body collapses toward the actual ~$34 median
(super-additive — confirming gas+import substitution) or only marginally.

This is a sensitivity test, NOT a grounded keeper. Usage:
    python scripts/probes/_caiso_srmc_probe.py <out_dir> [--import-shift -15]
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import market_sim.config.constants as C
from scripts.run_calibration_full import solve_and_persist
from scripts.run_calibration import _load_reference


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", type=Path)
    ap.add_argument("--import-shift", type=float, default=-15.0)
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    # 1) imports: lower the marginal blocks
    base = C.IMPORT_TRANCHES["CAISO"]
    C.IMPORT_TRANCHES["CAISO"] = [
        (
            n,
            c,
            p if n in ("DSW_CT", "WECC_scarcity") else max(0.0, p + args.import_shift),
        )
        for n, c, p in base
    ]

    # 2) gas offer near cost: flatten the rising econ markup to ~SRMC (mult 1.0),
    #    keep the committed band slightly below cost (must-run willingness).
    flat = {"committed": 0.95, "econ_low": 1.0, "econ_high": 1.0}
    overrides = {
        "CC_REGULAR": flat,
        "CC_CHP": flat,
        "CT_PEAKER": {"committed": 1.0, "econ_low": 1.0, "econ_high": 1.05},
        "ST_GAS": flat,
    }
    print("PROBE import ladder:", C.IMPORT_TRANCHES["CAISO"])
    print("PROBE gas offer overrides:", overrides)

    solve_and_persist(
        years=[args.year],
        iso="CAISO",
        hours=8760,
        reference=_load_reference(),
        commitment=True,
        screen_coal=True,
        run_dir=args.out_dir,
        priced_interchange=True,
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        outage_source="historic",
        offer_curve_overrides=overrides,
    )


if __name__ == "__main__":
    main()
