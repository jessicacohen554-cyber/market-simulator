"""CAISO-109 P0 instrument: economic-vs-physical diagnosis of the gas
under-dispatch, plus the import decomposition (pinned firm floor vs economic
belly/daytime clean-import depth).

NO SOLVE. Reconstructs model & actual gas hourly ENTIRELY from committed
artifacts — the keeper's own per-plant model dispatch (payload ``plants[].m``,
b64 CF%), the CAISO CEMS bench (``plants[].campd``, same basis as
``calibration_verdict._cems_gas_hourly_fit``), and the near-identical
keeper-proxy bundle ``caiso104_m1_B`` (gas within 0.25 % of the keeper) for the
hourly LMP + total-import series the keeper payload does not carry.

Run:
    PYTHONPATH=. .venv/bin/python scripts/probes/_caiso109_econ_vs_physical.py

Backs FINDING-caiso109-gas-underdispatch-economic-2026-07-21.md §1/§2/§4.
"""
from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import STATE_CARBON_PRICE_BY_ISO
from market_sim.config.interchange_config import (
    CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR,
    IMPORT_EFORD,
)
from market_sim.data.eia930.envelopes import measured_firm_import_shape
from scripts.lib.backcast_artifacts import decode_run_js, load_bench_part

ROOT = Path(__file__).resolve().parents[2]
KEEPER_JS = ROOT / "frontend/data/backcast/runs/2026-07-19-caiso-102-hourfix.js"
PROXY = ROOT / "results/calibration/caiso104_m1_B/hourly"
GAS_CLASSES = {
    "CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "OTHER_FOSSIL",
}
T = 8760

# CA gas MC inputs (delivered = Henry Hub hindcast_realized + measured citygate basis)
HH = {2023: 2.54, 2024: 2.19, 2025: 3.53}
HR_CC_H, HR_CC_F = 6.3, 6.7          # h-class (cheapest) / f-class (marginal) CCGT
CO2_PER_MMBTU, VOM = 0.057, 3.0
# firm totals = IMPORT_TRANCHES_BY_YEAR PNW_hydro_base + DSW_solar_PV
FIRM = {2023: 1072 + 1251, 2024: 1558 + 1813, 2025: 1566 + 1805}
ACT_IMP_TWH = {2023: 28.87, 2024: 32.38, 2025: 36.16}


def _gas_basis(year: int) -> float:
    df = pd.read_csv(ROOT / "data/raw/caiso_zonal_gas_hub.csv")
    return float(df[df.year == year].basis_vs_hh_usd_mmbtu.mean())


def _model_actual_gas(year: int, pay: dict):
    """Model & actual gas hourly (MW), CEMS basis, from committed artifacts."""
    yp = pay["years"][str(year)]
    bench = load_bench_part(ROOT / f"frontend/data/backcast/bench/CAISO/{year}.json.gz")["bench"]
    bplants, pplants = bench["plants"], yp["plants"]
    cogen = (bench.get("e930") or {}).get("gas_cogen_grid") or 0.0
    model = np.zeros(T)
    act = np.zeros(T)
    npl_sum = btm_twh = 0.0
    for code, bp in bplants.items():
        if bp.get("group") not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        cb, pp = bp.get("campd"), pplants.get(str(code))
        if cap <= 0 or not cb or not pp or not pp.get("m"):
            continue
        s = cap / 100.0
        act += np.frombuffer(base64.b64decode(cb)[:T], dtype=np.uint8).astype(float) * s
        model += np.frombuffer(base64.b64decode(pp["m"])[:T], dtype=np.uint8).astype(float) * s
        npl_sum += cap
        btm_twh += float(bp.get("btm") or 0.0)
    btm_mw = btm_twh * 1e6 / T
    gas_row = next(r for r in yp["fuelRows"] if r["fuel"] == "gas")
    fill = (gas_row["m"] - (model.sum() / 1e6 - btm_twh)) * 1e6 / T
    return model - btm_mw + fill, act - btm_mw + cogen * 1e6 / T, npl_sum


def main() -> None:
    pay = decode_run_js(KEEPER_JS.read_text())
    for year in (2023, 2024, 2025):
        model, act, npl = _model_actual_gas(year, pay)
        under = model < act
        gp = HH[year] + _gas_basis(year)
        mc_h = HR_CC_H * gp + VOM + CO2_PER_MMBTU * HR_CC_H * STATE_CARBON_PRICE_BY_ISO["CAISO"][year]
        mc_f = HR_CC_F * gp + VOM + CO2_PER_MMBTU * HR_CC_F * STATE_CARBON_PRICE_BY_ISO["CAISO"][year]

        sysdf = pd.read_parquet(PROXY / f"system_{year}.parquet")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        piv = sysdf.pivot_table(index="hour", columns="zone", values="price")
        dem = sysdf.pivot_table(index="hour", columns="zone", values="demand")
        lmp = ((piv * dem).sum(axis=1) / dem.sum(axis=1)).reindex(range(T)).to_numpy()
        cls = pd.read_parquet(PROXY / f"class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        imp = cls[cls["klass"] == "import"].set_index("hour")["mw"].reindex(range(T)).to_numpy()

        shape = measured_firm_import_shape("CAISO", year, T)
        firm_floor = shape * FIRM[year] * (1 - IMPORT_EFORD["CAISO"])
        actual_imp = shape * (ACT_IMP_TWH[year] * 1e6 / T)
        hod = np.arange(T) % 24

        print(f"\n================= {year} =================")
        print("  -- §1 PHYSICAL --  gas peak %.1f / %.1f GW nameplate (%.0f%% headroom); "
              "under-hrs at >90%% peak = %.1f%%; reality/model gas in under-hrs = %.2fx"
              % (model.max() / 1e3, npl / 1e3, 100 * (1 - model.max() / npl),
                 100 * (model[under] > 0.9 * model.max()).mean(), act[under].mean() / model[under].mean()))
        print("  -- §1 ECONOMIC -- under-disp %d hrs (%.0f%%); LMP<cheapest CCGT($%.0f) in %.0f%%; "
              "CA gas MC $%.0f-$%.0f/MWh (gas $%.2f/MMBtu)"
              % (under.sum(), 100 * under.mean(), mc_h, 100 * (lmp[under] < mc_h).mean(),
                 mc_h, mc_f, gp))
        print("  -- §2 SUBSTITUTION -- gas gap %+.1f TWh  import over %+.2f TWh (~1:1, CEMS basis)"
              % ((act.sum() - model.sum()) / 1e6, (imp.sum() - actual_imp.sum()) / 1e6))
        for lbl, hrs in [("overnight22-6", list(range(22, 24)) + list(range(0, 7))),
                         ("belly10-15", list(range(10, 16))), ("evening16-21", list(range(16, 22)))]:
            m = np.isin(hod, hrs)
            print("       §4 %-13s over-import %+.2f GW | firm floor %.2f GW | belly gas gap %+.2f GW"
                  % (lbl, (imp[m] - actual_imp[m]).mean() / 1e3, firm_floor[m].mean() / 1e3,
                     (act[m] - model[m]).mean() / 1e3))
        print("       firm floor annual %.1f TWh = %.0f%% of actual imports (PINNED, not the culprit)"
              % (firm_floor.sum() / 1e6, 100 * firm_floor.sum() / actual_imp.sum()))
        print("       daytime-clean depth capability %.0f MW (belly filler)"
              % CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR[year])


if __name__ == "__main__":
    main()
