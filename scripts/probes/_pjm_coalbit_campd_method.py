"""Compare CAMPD->net-MWh conversion methods for the PJM bituminous fleet,
scored against EIA-923 net generation (the class-total truth).

Methods (annual net MWh per plant, then fleet sum):
  gross_only            : sum(grossLoad)                       (parasitic=1)
  gross_parasitic       : sum(grossLoad) * parasitic_factor    (dashboard method A)
  gross_paras+heatproxy : + heat->MWh for grossLoad-blank coal (dashboard PJM pipe)
  heat_physHR           : sum(heatInput) / physical_HR
  heat_minus_steam      : (sum(heatInput) - steam_fuel) / physical_HR
Scored vs EIA-923 combustion net for the same plants.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve()
ROOT = Path("/home/user/market-simulator")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data import campd
from market_sim.data.eia923 import load_monthly_generation
from market_sim.data.coal import coal_supply_class
from market_sim.data.zone_assignment import build_zone_lookup

ISO = "PJM"
YEARS = [2023, 2024, 2025]
KLB_USEFUL_MMBTU = 1.19  # ~saturated steam enthalpy, MMBtu per 1000 lb
BOILER_EFF = 0.80  # fuel basis: useful steam / boiler efficiency
PHYS_HR_DEFAULT = 10.0  # bituminous steam ~10 MMBtu/MWh gross typical

states = campd.states_for_iso(ISO)
zone_lookup = build_zone_lookup(ISO)  # ORIS -> zone (the ISO fleet)
iso_plants = set(zone_lookup)

# Bituminous fleet = PJM plants classified bituminous.
bit_plants = {p for p in iso_plants if coal_supply_class(p) == "bituminous"}
print(f"PJM bituminous plants (coal_supply_class): {len(bit_plants)}")

gen = load_monthly_generation()
# Curated physical heat rates from the bin sheet, if present.
try:
    from market_sim.config.scenarios import ScenarioConfig

    bins = pd.read_csv(ScenarioConfig().campd_bins_path)
    phys_hr = dict(
        zip(
            bins["Plant_Code"].astype(int),
            pd.to_numeric(bins["Plant_Avg_HR_MMBtu_MWh"], errors="coerce"),
        )
    )
except Exception as e:
    print("no bin HR:", e)
    phys_hr = {}

df_all = campd.load_campd_hourly(states, YEARS)
# parasitic factors (net/gross) reconciled to EIA-923, pooled.
campd_ann = campd.annual_plant_totals(df_all)
e923_net = campd.eia923_combustion_net(gen)
groups = {p: "COAL" for p in bit_plants}  # all bituminous -> COAL class default
paras = campd.compute_parasitic_factors(campd_ann, e923_net, groups)
fmap = campd.pooled_factor_map(paras)

for year in YEARS:
    g = gen[gen["year"] == year]
    # EIA-923 combustion net per bituminous plant (truth).
    fuels = g["fuel_type"].astype(str).str.upper()
    comb = g[~fuels.isin(campd._NON_COMBUSTION_FUELS)]
    e923_by = comb.groupby("plant_id")["netgen_annual_mwh"].sum()
    truth = {p: float(e923_by.get(p, 0.0)) for p in bit_plants}
    truth_tot = sum(truth.values())

    df = df_all[df_all["year"] == year]
    # heat-proxy fill (the dashboard PJM pipeline).
    dfp, proxy_ids = campd.fill_heatinput_proxy(df, gen, year)

    rows = []
    method_tot = {
        k: 0.0
        for k in [
            "gross_only",
            "gross_paras",
            "gross_paras_proxy",
            "heat_physHR",
            "heat_minus_steam",
        ]
    }
    n_campd = n_missing = 0
    for p in sorted(bit_plants):
        sub = df[df["plant_id"] == p]
        subp = dfp[dfp["plant_id"] == p]
        gross = np.nansum(sub["gross_mw"].to_numpy())
        heat = np.nansum(sub["heat_mmbtu"].to_numpy())
        steam = np.nansum(sub["steam_load"].to_numpy())  # klb/hr summed over hrs
        f = float(fmap.get(p, 0.93))
        hr = phys_hr.get(p)
        hr = float(hr) if hr and np.isfinite(hr) and hr > 0 else PHYS_HR_DEFAULT
        gross_proxy = np.nansum(subp["gross_mw"].to_numpy())  # incl heat-proxy fill
        fproxy = 1.0 if p in proxy_ids else f
        m = {
            "gross_only": gross,
            "gross_paras": gross * f,
            "gross_paras_proxy": gross_proxy * fproxy,
            "heat_physHR": heat / hr,
            "heat_minus_steam": max(0.0, heat - steam * KLB_USEFUL_MMBTU / BOILER_EFF)
            / hr,
        }
        for k in method_tot:
            method_tot[k] += m[k]
        has_campd = (gross > 0) or (heat > 0)
        if has_campd:
            n_campd += 1
        elif truth[p] > 0:
            n_missing += 1
        if truth[p] > 5e4 or gross > 5e4:
            rows.append(
                (
                    p,
                    truth[p] / 1e3,
                    m["gross_paras"] / 1e3,
                    m["gross_paras_proxy"] / 1e3,
                    m["heat_physHR"] / 1e3,
                    steam > 0,
                    p in proxy_ids,
                )
            )

    print(
        f"\n===== {year}  (truth EIA-923 bit-fleet net = {truth_tot / 1e6:.2f} TWh) ====="
    )
    print(
        f" plants with CAMPD data: {n_campd}/{len(bit_plants)};  "
        f"in 923 but NO CAMPD: {n_missing};  heat-proxy filled: {len(proxy_ids & bit_plants)}"
    )
    print(f" {'method':<22}{'TWh':>8}{'vs923 %':>10}")
    for k, v in method_tot.items():
        pct = 100 * (v - truth_tot) / truth_tot if truth_tot else float("nan")
        print(f" {k:<22}{v / 1e6:>8.2f}{pct:>+9.1f}%")
    # top plants
    rows.sort(key=lambda r: -r[1])
    print(
        f"  {'plant':>6}{'923TWh':>8}{'gxp':>8}{'gxp+px':>8}{'heat/HR':>8}  steam proxy"
    )
    for p, t, gp, gpp, h, hs, px in rows[:12]:
        print(
            f"  {p:>6}{t:>8.2f}{gp:>8.2f}{gpp:>8.2f}{h:>8.2f}  {str(hs):>5} {str(px):>5}"
        )
