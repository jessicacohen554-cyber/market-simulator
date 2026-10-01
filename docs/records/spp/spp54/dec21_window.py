"""SPP-54 design (C) leg C-3 (PRECOMMIT-spp-54 §4): the Dec-21-2025 window, itemised per zone
from the on-recipe `run_year(fleet_only=True)` LP inputs (keeper-3's recipe + the three-zone
topology) — demand, wind / solar potential, thermal + hydro capability net of the recipe's
own availability (outage) arrays — and the regional feasibility arithmetic for the South + SPS
region behind the N->S 3,400 MW link: own available capability + wind + solar + 3,400 >= demand.
Beside it, the same arithmetic with the TWO-zone wind split (docs/handoffs/spp54/
dec21_window_2025_wind.csv, from wind_reconcile.py), so the STOP condition — an hour the
three-zone INPUTS make infeasible that the two-zone inputs left feasible — is read directly.
Zero LP.

usage: uv run python docs/handoffs/spp54/dec21_window.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO))
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

YEAR = 2025
WINDOW = list(range(8496, 8521))
bundle = REPO / "results/calibration/spp43_screened_B"
meta = json.loads((bundle / "meta.json").read_text())
kw = run_year_kwargs(meta)
kw.update(derived_run_year_inputs(bundle, YEAR))
r = run_year(
    YEAR, "SPP", 8760, float(meta["gas_prices"][str(YEAR)]), {}, fleet_only=True, **kw
)
print("run_year(fleet_only) keys:", sorted(r.keys()))
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

zones = list(get_iso_config("SPP").zone_names)
iN, iS, iP = (zones.index(z) for z in ("SPP-North", "SPP-South", "SPP-SPS"))
fleet = r["fleet"]
zone_of = np.array([zones.index(g.zone) for g in fleet])
pmax = np.array([g.pmax_mw for g in fleet], dtype=float)
avail = None
for key in ("availability", "avail", "availability_matrix", "outage_availability"):
    if key in r and r[key] is not None:
        avail = np.asarray(r[key], dtype=float)
        print(f"availability array found under '{key}', shape {avail.shape}")
        break
if avail is None:
    fa = r.get("fleet_arrays")
    for attr in ("availability", "avail"):
        if fa is not None and hasattr(fa, attr):
            avail = np.asarray(getattr(fa, attr), dtype=float)
            print(f"availability from fleet_arrays.{attr}, shape {avail.shape}")
            break
dem = np.asarray(r["demand"])
wcf, wcap = np.asarray(r["wind_cf"]), np.asarray(r["wind_cap"])
scf, scap = np.asarray(r["solar_cf"]), np.asarray(r["solar_cap"])
wind = wcf * (wcap[:, None] if wcap.ndim == 1 else wcap)
solar = scf * (scap[:, None] if scap.ndim == 1 else scap)
two = pd.read_csv(REPO / "docs/handoffs/spp54/dec21_window_2025_wind.csv").set_index(
    "hour"
)
NS_TTC = 3400.0
rows = []
print(
    "\n  h   | demand N / S / SPS | thermal+hydro available S / SPS (nameplate S / SPS) | wind S / SPS | solar S+SPS |"
    " region S+SPS: supply3z (incl. 3,400) - demand | with two-zone wind | STOP?"
)
for h in WINDOW:
    if avail is not None and avail.ndim == 2:
        cap_h = pmax * avail[:, h]
    elif avail is not None and avail.ndim == 1:
        cap_h = pmax * avail
    else:
        cap_h = pmax
    th = np.array([cap_h[zone_of == z].sum() for z in range(len(zones))])
    th_name = np.array([pmax[zone_of == z].sum() for z in range(len(zones))])
    d = dem[:, h]
    w = wind[:, h]
    s = solar[:, h]
    reg_dem = d[iS] + d[iP]
    reg_sup3 = th[iS] + th[iP] + w[iS] + w[iP] + s[iS] + s[iP] + NS_TTC
    reg_sup2 = th[iS] + th[iP] + float(two.loc[h, "south_2z"]) + s[iS] + s[iP] + NS_TTC
    stop = (reg_sup3 < reg_dem) and (reg_sup2 >= reg_dem)
    print(
        f"  {h} | {d[iN]:7.0f} / {d[iS]:7.0f} / {d[iP]:6.0f} | {th[iS]:7.0f} / {th[iP]:6.0f} ({th_name[iS]:6.0f} / {th_name[iP]:5.0f}) | "
        f"{w[iS]:6.0f} / {w[iP]:5.0f} | {s[iS] + s[iP]:5.0f} | {reg_sup3:8.0f} - {reg_dem:7.0f} = {reg_sup3 - reg_dem:+8.0f} | {reg_sup2 - reg_dem:+8.0f} | {'STOP' if stop else 'ok'}"
    )
    rows.append(
        {
            "hour": h,
            "demand_north": d[iN],
            "demand_south": d[iS],
            "demand_sps": d[iP],
            "thermal_hydro_avail_south": th[iS],
            "thermal_hydro_avail_sps": th[iP],
            "wind_south": w[iS],
            "wind_sps": w[iP],
            "solar_region": s[iS] + s[iP],
            "region_margin_3z": reg_sup3 - reg_dem,
            "region_margin_2z": reg_sup2 - reg_dem,
            "stop": stop,
        }
    )
df = pd.DataFrame(rows)
df.to_csv(REPO / "docs/handoffs/spp54/dec21_window_2025.csv", index=False)
print(
    f"\nC-3: hours the three-zone inputs make infeasible while the two-zone inputs were feasible: {int(df['stop'].sum())} "
    f"-> {'STOP' if df['stop'].any() else 'PASS'}; min regional margin 3z {df['region_margin_3z'].min():+.0f} MW (2z {df['region_margin_2z'].min():+.0f})"
)
# the SPS pocket alone (no link yet): own available capability + wind + solar vs its own demand
pocket = []
for h in WINDOW:
    cap_h = pmax * (avail[:, h] if (avail is not None and avail.ndim == 2) else 1.0)
    pocket.append(cap_h[zone_of == iP].sum() + wind[iP, h] + solar[iP, h] - dem[iP, h])
print(
    f"SPS pocket own margin (available thermal + wind + solar - demand) over the window: min {min(pocket):+.0f} max {max(pocket):+.0f} MW"
)
# the stuck-demand run (FINDING-spp-42 R-9), as the zonal series inherit it
sys_dem = dem.sum(axis=0)
run = [h for h in range(8300, 8760) if abs(sys_dem[h] - 37455.0) < 1.0]
print(
    f"system demand == 37,455 MW (the stuck run) at {len(run)} hours in h8300-h8759; first {run[:1]} last {run[-1:]}"
)
