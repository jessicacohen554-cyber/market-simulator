#!/usr/bin/env python3
"""miso-276 phase 0 (zero LP): footprint of ``miso_winter_gas_daily_delivered`` on the keeper.

Rebuilds the keeper fleet (``run_year(fleet_only=True)``, keeper recipe via the
miso-271 helpers, KEEPER re-pointed at ``miso275_span``) with the flag off and
on, and compares the assembled gas fuel-price array (``fuel_prices``) per zone,
capacity-weighted, by winter month, and for Feb-2021 split into storm
(Feb 13-16) and non-storm days. Also asserts every non-winter cell is
byte-identical.

Usage::

    uv run python scripts/probes/_miso276_winter_gas_footprint.py --years 2019 2020 2021 2022 2023 2024 2025 \
        --out results/calibration/_miso276_winter_gas_footprint.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso275_span"
FLAG = {"miso_winter_gas_daily_delivered": True}


def build(year: int, hh: float, on: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], np.ndarray]:
    """(fuel_prices, pmax, zone_idx, zone_names, gas_mask) for the keeper fleet."""
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX
    from scripts.run_calibration import run_year  # type: ignore

    st = run_year(year, "MISO", 8760, hh, {}, fleet_only=True,
                  **dec.recipe(year, FLAG if on else {}))
    fa = st["fleet_arrays"]
    gas = np.isin(np.asarray(fa.fuel_type_idx), _GAS_FUEL_IDX)
    return (np.asarray(st["fuel_prices"], float), np.asarray(fa.pmax, float),
            np.asarray(fa.zone_idx), list(st["iso_config"].zone_names), gas)


def probe(year: int) -> dict:
    """Flag off vs on for one year."""
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    hh = _henry_hub_actual(_load_reference(), year)
    f0, pmax, zi, zn, gas = build(year, hh, False)
    f1, _, _, _, _ = build(year, hh, True)
    from market_sim.data.fuel._shared import _month_index

    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(f0.shape[1]), "h")
    # The MODEL's 365-day calendar (Feb = 672 h in every year), the one the
    # applier gates on — a leap-year pandas calendar would shift month edges.
    month = _month_index(f0.shape[1]) + 1
    winter = np.isin(month, (12, 1, 2))
    out: dict = {
        "non_winter_cells_identical": bool(np.array_equal(f0[:, ~winter], f1[:, ~winter])),
        "non_gas_rows_identical": bool(np.array_equal(f0[~gas], f1[~gas])),
        "zones": {},
    }
    for z, name in enumerate(zn):
        k = gas & (zi == z)
        if not k.any():
            continue
        w = pmax[k][:, None]

        def cw(arr: np.ndarray, cols: np.ndarray) -> float:
            return round(float((arr[k][:, cols] * w).sum() / (w.sum() * cols.sum())), 3)

        rec = {f"m{m:02d}": {"off": cw(f0, month == m), "on": cw(f1, month == m)}
               for m in (1, 2, 12)}
        if year == 2021:
            storm = (ts >= "2021-02-13") & (ts < "2021-02-17")
            calm = (month == 2) & ~storm
            rec["feb_storm"] = {"off": cw(f0, np.asarray(storm)), "on": cw(f1, np.asarray(storm))}
            rec["feb_calm"] = {"off": cw(f0, np.asarray(calm)), "on": cw(f1, np.asarray(calm))}
        out["zones"][name] = rec
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2021])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out_p = Path(args.out)
    res: dict = json.loads(out_p.read_text()) if out_p.exists() else {}
    for y in args.years:
        res[str(y)] = probe(y)
        print(y, json.dumps(res[str(y)]), flush=True)
        Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
