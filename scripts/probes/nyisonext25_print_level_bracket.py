"""NYISO-NEXT-25 phase 0 (ZERO LP): offer-array delta and price bracket for ``nyiso_gas_daily_print_level``.

Fleet-only rebuild of the keeper recipe with the flag off and on (dual-fuel cap ON, so the
oil-parity clip is respected). Reports the delivered-gas delta by zone/class and two price
brackets per zone against NYISO DA:

* ``lo``: the zone's MW-weighted CC heat rate x the zone's CC gas delta (a CC sets price);
* ``hi``: the keeper price x the zone's CC gas ratio (every $ of price scales with fuel).

A bracket, not a solve: the LP is the test (rule 13; nothing here feeds a solve).

Usage: uv run python scripts/probes/nyisonext25_print_level_bracket.py --out <json>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes.nyisonext25_offcap_winter_gap import (  # noqa: E402
    ZONAL,
    _bundle,
    _hourly_price,
    fleet_state,
)

ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")
CC = ("CC_REGULAR", "CC_CHP")


def bracket(year: int) -> dict:
    """Delta and bracket for one year."""
    from market_sim.data.fuel.dual_fuel import _GAS_FUEL_IDX

    off = fleet_state(year, {})
    on = fleet_state(year, {"nyiso_gas_daily_print_level": True})
    assert on["config"].nyiso_gas_daily_print_level
    fa = off["fleet_arrays"]
    zn = list(off["iso_config"].zone_names)
    f0 = np.asarray(off["fuel_prices"], float)[:, :8760]
    f1 = np.asarray(on["fuel_prices"], float)[:, :8760]
    pg = np.asarray(fa.plant_group).astype(str)
    gas = np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX)
    mw = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    a = pd.read_parquet(ZONAL)
    a = a[a.year == year]
    kb = _bundle(year) / "hourly" / f"system_{year}.parquet"
    mon = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month.to_numpy()
    win = np.isin(mon, (1, 2, 12))
    out = {"year": year, "rows_changed": int((np.abs(f1 - f0) > 1e-9).any(1).sum())}
    out["max_abs_gas_delta"] = round(float(np.abs(f1 - f0).max()), 3)
    zrec = {}
    for z in ZONES:
        sel = gas & (np.asarray(fa.zone_idx) == zn.index(z)) & np.isin(pg, CC)
        if mw[sel].sum() == 0:
            continue
        w = mw[sel]
        g0 = (f0[sel] * w[:, None]).sum(0) / w.sum()
        g1 = (f1[sel] * w[:, None]).sum(0) / w.sum()
        hcc = float(np.average(hr[sel], weights=w))
        p = _hourly_price(kb, year, z)
        d = a[a.zone == z].sort_values("hour").da.to_numpy()[:8760]
        lo = p + hcc * (g1 - g0)
        hi = p * np.where(g0 > 0, g1 / g0, 1.0)
        rec = {"cc_hr": round(hcc, 2)}
        for nm, k in (("annual", np.ones(8760, bool)), ("winter", win)):
            rec[nm] = {
                "gas_off": round(float(g0[k].mean()), 3),
                "gas_on": round(float(g1[k].mean()), 3),
                "da": round(float(d[k].mean()), 2),
                "keeper": round(float(p[k].mean()), 2),
                "bracket_lo": round(float(lo[k].mean()), 2),
                "bracket_hi": round(float(hi[k].mean()), 2),
                "err_pct_keeper": round(
                    float(100 * (p[k].mean() / d[k].mean() - 1)), 1
                ),
                "err_pct_lo": round(float(100 * (lo[k].mean() / d[k].mean() - 1)), 1),
                "err_pct_hi": round(float(100 * (hi[k].mean() / d[k].mean() - 1)), 1),
            }
        rec["by_month_gas_ratio"] = {
            int(m): round(float(g1[mon == m].mean() / g0[mon == m].mean()), 3)
            for m in range(1, 13)
        }
        zrec[z] = rec
    out["zones"] = zrec
    return out


def main() -> None:
    """Run 2021-2025 and write JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2021, 2022, 2023, 2024, 2025])  # fmt: skip
    a = ap.parse_args()
    res = [bracket(y) for y in a.years]
    Path(a.out).write_text(json.dumps(res, indent=1))
    for r in res:
        print(r["year"], r["rows_changed"], r["max_abs_gas_delta"])
        for z, v in r["zones"].items():
            print("  ", z, "annual", v["annual"], "\n      winter", v["winter"])
            print("      ratio", v["by_month_gas_ratio"])


if __name__ == "__main__":
    main()
