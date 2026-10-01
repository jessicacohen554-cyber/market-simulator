"""SPP-54 design (A)/(D) exit (the SPP-57b instrument re-pointed): the on-recipe
`run_year(fleet_only=True)` census per zone (plants, MW by class, wind / solar MW and
potential, demand TWh) for 2023-2025 on the CONTROL keeper's recipe (keeper-3,
results/calibration/spp43_screened_B meta.json via replay_keeper.run_year_kwargs +
derived_run_year_inputs) — i.e. the three-zone arm's LP inputs, before any solve.
Also the residual-blind bounds B_plaus / B_hard per zone (PRECOMMIT-spp-54 §2.3 / §3.4:
zone capability minus its minimum hourly load) and the hourly zonal-share identity.
Zero LP.

usage: uv run python docs/handoffs/spp54/census.py
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

bundle = REPO / "results/calibration/spp43_screened_B"
meta = json.loads((bundle / "meta.json").read_text())
kw = run_year_kwargs(meta)
print(
    "recipe kwargs:",
    {k: v for k, v in kw.items() if v not in (None, False, 0, 1.0, "", {}, [])},
)
pd.set_option("display.width", 250)
out = []
bounds = []
for year in (2023, 2024, 2025):
    kw_y = dict(kw)
    kw_y.update(derived_run_year_inputs(bundle, year))
    r = run_year(
        year,
        "SPP",
        8760,
        float(meta["gas_prices"][str(year)]),
        {},
        fleet_only=True,
        **kw_y,
    )
    from market_sim.config.iso_configs import get_iso_config

    zones = list(get_iso_config("SPP").zone_names)
    fleet = r["fleet"]
    df = pd.DataFrame(
        {
            "zone": [g.zone for g in fleet],
            "klass": [g.plant_group or g.fuel_type for g in fleet],
            "fuel": [g.fuel_type for g in fleet],
            "pmax": [g.pmax_mw for g in fleet],
            "plant": [g.plant_code for g in fleet],
        }
    )
    tab = (
        df.pivot_table(index="klass", columns="zone", values="pmax", aggfunc="sum")
        .fillna(0)
        .round(0)
    )
    plants = df.groupby("zone")["plant"].nunique()
    units = df.groupby("zone").size()
    wcap = np.asarray(r["wind_cap"])
    scap = np.asarray(r["solar_cap"])
    wcf = np.asarray(r["wind_cf"])
    scf = np.asarray(r["solar_cf"])
    dem = np.asarray(r["demand"])
    print(f"\n===== {year}: zones {zones}; LP units {len(df)}")
    print(tab.to_string())
    # hourly zonal-share identity (the curated / raw-fallback shares, as the LP sees them)
    shares = dem / dem.sum(axis=0, keepdims=True)
    print(
        f"  hourly zonal shares: mean {dict(zip(zones, shares.mean(axis=1).round(4)))}; "
        f"max|sum-1| {np.abs(shares.sum(axis=0) - 1.0).max():.3e}"
    )
    for i, z in enumerate(zones):
        wc = float(wcap[i].max()) if wcap.ndim == 2 else float(wcap[i])
        sc = float(scap[i].max()) if scap.ndim == 2 else float(scap[i])
        wpot = float((wcf[i] * (wcap[i] if wcap.ndim == 2 else wcap[i])).sum() / 1e6)
        spot = float((scf[i] * (scap[i] if scap.ndim == 2 else scap[i])).sum() / 1e6)
        gas_mw = float(df[(df.zone == z) & df.fuel.str.startswith("gas")].pmax.sum())
        nongas_mw = float(tab[z].sum()) - gas_mw
        capability = float(tab[z].sum()) + wc + sc
        b_plaus = (
            nongas_mw + wc + sc - float(dem[i].min())
        )  # non-gas capability - min load
        b_hard = capability - float(dem[i].min())
        print(
            f"  {z:10s} plants {int(plants.get(z, 0)):4d} units {int(units.get(z, 0)):4d} thermal+hydro MW {tab[z].sum():9.0f} "
            f"(gas {gas_mw:7.0f}) wind cap {wc:8.0f} MW potential {wpot:6.2f} TWh | solar cap {sc:7.0f} MW potential {spot:5.2f} TWh | "
            f"demand {dem[i].sum() / 1e6:7.2f} TWh (min {dem[i].min():7.0f} max {dem[i].max():7.0f} MW) | "
            f"B_plaus {b_plaus:8.0f} B_hard {b_hard:8.0f}"
        )
        out.append(
            {
                "year": year,
                "zone": z,
                "plants": int(plants.get(z, 0)),
                "units": int(units.get(z, 0)),
                "thermal_hydro_mw": float(tab[z].sum()),
                "gas_mw": gas_mw,
                "wind_cap_mw": wc,
                "wind_potential_twh": wpot,
                "solar_cap_mw": sc,
                "solar_potential_twh": spot,
                "demand_twh": float(dem[i].sum() / 1e6),
                "demand_min_mw": float(dem[i].min()),
                "demand_max_mw": float(dem[i].max()),
                "demand_share": float(dem[i].sum() / dem.sum()),
                "b_plaus_mw": b_plaus,
                "b_hard_mw": b_hard,
            }
        )
    print(
        "  demand total TWh",
        round(float(dem.sum() / 1e6), 2),
        " wind potential total",
        round(float((wcf * wcap).sum() / 1e6), 2) if wcap.ndim == 2 else "",
    )
pd.DataFrame(out).to_csv(REPO / "docs/handoffs/spp54/census.csv", index=False)
