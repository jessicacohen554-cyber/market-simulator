#!/usr/bin/env python3
"""THROWAWAY DIAGNOSTIC PROBE (not a keeper). Re-price the CAISO priced-import
ladder to a lower, neighbor-realistic level and re-solve, to measure how much of
the +$22 body overprice is set by the static import ladder (sensitivity dLMP/dladder).

This does NOT ground the prices in measured hub data — it is a sensitivity test
only. The grounded keeper prices imports at measured Malin/Palo-Verde intertie
LMPs (separate workstream). Usage:
    python scripts/probes/_caiso_import_probe.py <out_dir> [--shift -15]
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
    ap.add_argument(
        "--shift",
        type=float,
        default=-15.0,
        help="$/MWh shift applied to the marginal (non-scarcity) import blocks",
    )
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    base = C.IMPORT_TRANCHES["CAISO"]
    # shift the marginal blocks (PNW/Mid-C/DSW_solar/DSW_CCGT); leave the deep
    # peak/scarcity blocks (DSW_CT, WECC_scarcity) so the ceiling is unchanged.
    shifted = []
    for name, cap, price in base:
        if name in ("DSW_CT", "WECC_scarcity"):
            shifted.append((name, cap, price))
        else:
            shifted.append((name, cap, max(0.0, price + args.shift)))
    C.IMPORT_TRANCHES["CAISO"] = shifted
    print("PROBE import ladder:", shifted)

    ref = _load_reference()

    solve_and_persist(
        years=[args.year],
        iso="CAISO",
        hours=8760,
        reference=ref,
        commitment=True,
        screen_coal=True,
        run_dir=args.out_dir,
        priced_interchange=True,
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        outage_source="historic",
    )


if __name__ == "__main__":
    main()
