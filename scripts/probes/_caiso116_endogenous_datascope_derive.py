"""caiso-116 DERIVE: why the endogenous WECC-West node (candidate a) cannot be
evening-scoped to keep the C3a guard while fixing C5a — the NW+SW data-scope gap.

Measurement-only, committed artifacts + raw EIA-930 + the wecc-west-supply clean
frame only, NO SOLVE. Reproduces the five measurements behind
FINDING-caiso116-endogenous-datascope-2026-07-23.md:

  1. Annual data-scope gap (Inv 1) — the modeled West (EIA-930 Region NW+SW) net
     exports only ~19 TWh/yr, but CAISO imports 29-36 TWh; the 9-17 TWh gap is
     CA importing from sources OUTSIDE the modeled West. L1b (caiso110_endog_B)
     matched CA's import volume (32/32/37 TWh) only by having the West
     over-generate that gap as gas exported at the intertie hub.
  2. Exportable-gas shape (Inv 2) — the West's exportable surplus is almost
     entirely gas, and it tracks the tie shape (~0 GW belly, +2 GW evening,
     +4 GW night), far BELOW CAISO's actual net import (0.7 belly, 3.3 evening,
     5.3 night GW). The West cannot supply CA's imports from its real surplus.
  3. Feasibility (Inv 3) — the modeled West itself NET-IMPORTS ~21-24% of hours
     (net generation < demand), from sources the CA-only tie cannot represent —
     so bounding the West to its measured supply (the fleet-bound evening
     scoping) is infeasible without an unphysical CA->West backstop.
  4. L1b verdict (Inv 4) — from the committed caiso110_endog_B metrics: the
     endogenous node fixes C5a (PASS) + C3c (PASS) but breaks C3a (FAIL), the
     empirical anchor of the coupling.
  5. min-hub under-fix (Inv 5) — the price-temper scoping (offer the West gas at
     min(MALIN, PALOVRDE) instead of the tie-weighted blend, the caiso-114 note
     option c) shaves only $1-7 off the evening vs the +$4-18 C3a break, so it
     under-fixes C3a.

Conclusion: C5a-fix and C3a-guard are COUPLED through the West's ~13-18 TWh
proxy over-export and cannot be separated within the NW+SW node. Both scopings
fail by derivation: fleet-bound (thermal-shaping) under-supplies CA -> over-
corrects C5a and is infeasible; price-temper (min-hub) under-fixes C3a.

Run:  PYTHONPATH=<repo> python scripts/probes/_caiso116_endogenous_datascope_derive.py
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

from scripts.lib.clean_io import read_clean

BELLY = [10, 11, 12, 13, 14]
EVENING = [17, 18, 19, 20, 21]
NIGHT = [0, 1, 2, 3, 4]
CISO_HOURLY = "data/raw/eia-930-hourly/CISO hourly.parquet"
L1B_METRICS = "results/calibration/caiso110_endog_B/metrics.json"


def _ciso_net_import() -> pd.DataFrame:
    """Raw EIA-930 CISO hourly with net import (+ = import) and local hour."""
    w = pd.read_parquet(CISO_HOURLY)
    w["lt"] = pd.to_datetime(w["Local time"])
    w["year"] = w["lt"].dt.year
    w["hod"] = w["lt"].dt.hour
    w["net_import"] = -pd.to_numeric(w["Total interchange"], errors="coerce")
    return w


def inv1_annual_gap() -> None:
    """West net-export capability vs CAISO net import — the data-scope gap."""
    print("\n" + "=" * 78)
    print("INV 1 — ANNUAL DATA-SCOPE GAP (modeled West net export vs CAISO import)")
    print("=" * 78)
    w = _ciso_net_import()
    for year in (2023, 2024, 2025):
        f = read_clean("wecc-west-supply", iso="CAISO", year=year)
        west_twh = f["net_export_mw"].mean() * 8760 / 1e6
        a = w[w["year"] == year]
        ca_twh = a["net_import"].mean() * len(a) / 1e6
        print(
            f"  {year}: West net-export {west_twh:5.1f} TWh | CAISO net import "
            f"{ca_twh:5.1f} TWh | GAP {ca_twh - west_twh:5.1f} TWh"
        )
    print("  READ: CA imports 9-17 TWh/yr BEYOND the modeled West (NW+SW). L1b")
    print("        (caiso110_endog_B) matched CA's 32/32/37 TWh import only by")
    print("        over-generating that gap as West gas exported at the intertie")
    print("        hub — the marginal unit that over-prices the evening (C3a).")


def inv2_exportable_gas() -> None:
    """West exportable-gas surplus by hod vs CAISO net import (the tie target)."""
    print("\n" + "=" * 78)
    print("INV 2 — WEST EXPORTABLE-GAS SURPLUS vs CAISO NET IMPORT (by block, GW)")
    print("=" * 78)
    w = _ciso_net_import()
    for year in (2023, 2024, 2025):
        f = read_clean("wecc-west-supply", iso="CAISO", year=year).copy()
        f["hod"] = f["interval_start_utc"].dt.tz_convert("US/Pacific").dt.hour
        nongas = (
            f[["solar_mw", "wind_mw", "hydro_mw", "nuclear_mw", "coal_mw"]]
            .fillna(0)
            .sum(axis=1)
        )
        # gas the West needs for its own load, and the surplus it can export.
        gas_for_load = np.clip(f["demand_mw"] - nongas, 0, None)
        export_gas = np.clip(f["gas_mw"] - gas_for_load, 0, None)
        a = w[w["year"] == year]
        ni = a.groupby("hod")["net_import"].mean()
        for lbl, hrs in (("belly", BELLY), ("evening", EVENING), ("night", NIGHT)):
            eg = export_gas[f["hod"].isin(hrs)].mean() / 1e3
            print(
                f"  {year} {lbl:8}: West export-gas {eg:4.1f} GW  |  "
                f"CAISO net import {ni.loc[hrs].mean() / 1e3:4.1f} GW"
            )
        print()
    print("  READ: the West's exportable surplus is almost all gas and tracks the")
    print("        tie shape (~0 belly, +2 evening, +4 night) but is FAR below")
    print("        CAISO's actual net import in every block — it cannot supply CA.")


def inv3_feasibility() -> None:
    """The modeled West itself net-imports ~21-24% of hours (net_gen < demand)."""
    print("\n" + "=" * 78)
    print("INV 3 — WEST FEASIBILITY: net generation < demand (net-import) hours")
    print("=" * 78)
    for year in (2023, 2024, 2025):
        f = read_clean("wecc-west-supply", iso="CAISO", year=year)
        net_imp_hrs = (f["net_export_mw"] < 0).mean() * 100
        worst = (f["demand_mw"] - f["net_generation_mw"]).max() / 1e3
        print(
            f"  {year}: West net-imports {net_imp_hrs:2.0f}% of hours "
            f"(worst shortfall {worst:.1f} GW)"
        )
    print("  READ: bounding the West to its measured supply (the fleet-bound")
    print("        evening scoping) is INFEASIBLE — the West itself imports from")
    print("        sources outside the CA tie ~1/4 of hours; no backstop can")
    print("        represent them without either over-inflating CA gas (CA->West)")
    print("        or under-pricing (cheap export). The gap bites both directions.")


def inv4_l1b_verdict() -> None:
    """The committed L1b (caiso110_endog_B) gate verdict — the empirical anchor."""
    print("\n" + "=" * 78)
    print("INV 4 — L1b (caiso110_endog_B) GATE VERDICT (committed metrics.json)")
    print("=" * 78)
    m = json.load(open(L1B_METRICS))
    crit = m.get("criteria", {})
    for key in ("co2", "price_tail", "price_mean", "price_shape", "dispatch_corr"):
        c = crit.get(key, {})
        print(f"  {c.get('label', key):32} [{c.get('tier', '?'):12}] {c.get('status')}")
    print("  READ: the endogenous node FIXES C5a (co2 PASS) + C3c (price_tail PASS)")
    print("        but BREAKS C3a (price_mean FAIL) — the coupling, empirically.")


def inv5_min_hub_underfix() -> None:
    """min(MALIN, PALOVRDE) vs the tie-weighted blend — the price-temper scoping."""
    print("\n" + "=" * 78)
    print("INV 5 — min-hub PRICE-TEMPER (caiso-114 note c): blend vs min by block")
    print("=" * 78)
    from market_sim.config.interchange_config import CAISO_IMPORT_TRANCHE_HUB
    from market_sim.data.eia930.envelopes import measured_import_hub_prices

    wt = {"MALIN": 4800.0, "PALOVRDE": 10623.0}
    for year in (2023, 2024, 2025):
        ts = measured_import_hub_prices("CAISO", year, 8760)
        hub: dict[str, np.ndarray] = {}
        for tr, s in (ts or {}).items():
            h = CAISO_IMPORT_TRANCHE_HUB.get(tr)
            if h in wt and h not in hub:
                hub[h] = np.asarray(s, dtype=float)
        if set(hub) != set(wt):
            print(f"  {year}: missing hub series {set(hub)}")
            continue
        blend = (wt["MALIN"] * hub["MALIN"] + wt["PALOVRDE"] * hub["PALOVRDE"]) / sum(
            wt.values()
        )
        mn = np.minimum(hub["MALIN"], hub["PALOVRDE"])
        hod = np.arange(8760) % 24
        ev = np.isin(hod, EVENING)
        print(
            f"  {year} evening: BLEND {blend[ev].mean():5.1f}  MIN {mn[ev].mean():5.1f}"
            f"  (min lowers the West offer by only {blend[ev].mean() - mn[ev].mean():.1f})"
        )
    print("  READ: min-hub shaves only $1-7 off the evening offer, vs the +$4-18")
    print("        C3a break (the break is the West gas BECOMING MARGINAL at the")
    print("        hub, not the hub's exact level) — so it under-fixes C3a.")


if __name__ == "__main__":
    inv1_annual_gap()
    inv2_exportable_gas()
    inv3_feasibility()
    inv4_l1b_verdict()
    inv5_min_hub_underfix()
