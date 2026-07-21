"""CAISO-111 R1 instrument: full belly energy-balance attribution, model vs
actual, from committed artifacts + raw EIA-930/HSL only. NO SOLVE.

Settles the fresh-look R1 questions:
  (a) demand basis — quantify scored (supply-consistent) demand vs raw 930
      Demand cell vs NetGen-TI identity. EIA-930 CISO metered demand is
      already NET of ~15+ GW BTM PV; the keeper feeds the supply-consistent
      (caiso-80) reconstruction of it and models only FRONT-of-meter solar, so
      BTM is single-netted, not double-netted or missing (code trace in the
      FINDING; this prints the annual numbers).
  (b) solar over-actual — attribute the P0 "+2.5-3 TWh model solar over" to
      under-curtailment (HSL potential vs delivered vs model dispatch) by
      month and hour-of-day. Lever-D (caiso_solar_deliverability) is ON in the
      keeper yet the model curtails ~0.03-0.63 TWh vs actual 2.5-3.5 TWh.
  (c) belly component ledger + EXPORT-FLOOR — for the belly window the
      model-minus-actual delta of every energy-balance component, PLUS the
      export-floor check: reality net-EXPORTS in ~9-14 % of hours (mostly the
      belly), but the model's WECC_import node is inject-only (min net import
      = 0), so it imports where reality exports. Decomposes the belly import
      wedge into an export-hours part (the sign/topology gap) and an
      import-hours part (the depth/pricing gap).

Model hourlies come from the keeper-proxy bundle ``caiso104_m1_B`` (gas within
0.25 % of keeper ``2026-07-19-caiso-102-hourfix``; solar 47.18 vs 47.2 TWh),
the same proxy caiso-109 P0 used. Gas model/actual reuse the caiso-109
instrument's CEMS-basis reconstruction.

Run: PYTHONPATH=. .venv/bin/python scripts/probes/_caiso111_belly_attribution.py
Backs FINDING-caiso111-belly-drivers-and-field-survey.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia930.frames import _eia_hourly_frame_filled
from scripts.lib.backcast_artifacts import decode_run_js
from scripts.probes._caiso109_econ_vs_physical import _model_actual_gas

ROOT = Path(__file__).resolve().parents[2]
PROXY = ROOT / "results/calibration/caiso104_m1_B/hourly"
KEEPER_JS = ROOT / "frontend/data/backcast/runs/2026-07-19-caiso-102-hourfix.js"
SCD_DIR = ROOT / "data/raw/reference/caiso-supply-consistent-demand"
HSL_DIR = ROOT / "data/raw/caiso-hsl"
T = 8760
YEARS = (2023, 2024, 2025)
BELLY = np.isin(np.arange(T) % 24, range(10, 16))  # local hod 10-15 interval-beginning
EVE = np.isin(np.arange(T) % 24, range(17, 22))


def main() -> None:
    pay = decode_run_js(KEEPER_JS.read_text())
    for year in YEARS:
        f = _eia_hourly_frame_filled("CISO", year)
        assert f is not None
        raw_dem = f["Demand"].interpolate().bfill().ffill().to_numpy(dtype=float)
        netgen = f["Net generation"].interpolate().bfill().ffill().to_numpy(dtype=float)
        ti = f["Total interchange"].interpolate().bfill().ffill().to_numpy(dtype=float)

        def col(name: str) -> np.ndarray:
            s = f[name]
            if s.notna().sum() < T // 2:  # NG: GEO absent 2023/24 (folded in OTH)
                return np.zeros(T)
            return s.interpolate().bfill().ffill().to_numpy(dtype=float)

        act = {
            "solar": col("NG: SUN"),
            "wind": col("NG: WND"),
            "hydro": col("NG: WAT"),
            "nuclear": col("NG: NUC"),
            # NG: OTH in the CISO extract EMBEDS battery storage (verified: the
            # hod profile swings -5.3 GW midday / +5.6 GW evening by 2025; the
            # BALANCE battery split column is all-NaN for CISO), so geo/other
            # and storage are compared as ONE combined row.
            "oth_batt": col("NG: GEO") + col("NG: OTH") + col("NG: OIL") + col("NG: COL"),
            "net_import": -ti,
        }
        scd = pd.read_csv(SCD_DIR / f"caiso_supply_consistent_demand_{year}.csv")[
            "demand_mw"
        ].to_numpy(dtype=float)
        hsl = pd.read_parquet(HSL_DIR / f"caiso_{year}_hsl_hourly.parquet")

        # model hourlies from the keeper-proxy bundle
        cls = pd.read_parquet(PROXY / f"class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        m = {
            k: cls[cls["klass"] == k].set_index("hour")["mw"].reindex(range(T)).fillna(0).to_numpy(dtype=float)
            for k in cls["klass"].unique()
        }
        sysdf = pd.read_parquet(PROXY / f"system_{year}.parquet")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        dem_m = sysdf.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy(dtype=float)
        dump = sysdf.groupby("hour")["dump"].sum().reindex(range(T)).fillna(0).to_numpy(dtype=float)
        slack = sysdf.groupby("hour")["slack"].sum().reindex(range(T)).fillna(0).to_numpy(dtype=float)
        gen_total = sum(m.values())
        # LP balance: gen + (dis-chg) + slack - dump = demand
        # => stor_m = (dis - chg): >0 net discharge, <0 net charge.
        stor_m = dem_m + dump - slack - gen_total
        gas_m, gas_a, _ = _model_actual_gas(year, pay)

        def tw(x: np.ndarray, mask=None) -> float:
            return float((x if mask is None else x[mask]).sum() / 1e6)

        def gw(x: np.ndarray, mask) -> float:
            return float(x[mask].mean() / 1e3)

        print(f"\n================ {year} ================")
        print("-- (a) demand basis (annual TWh) --")
        print(
            f"raw 930 Demand {tw(raw_dem):.1f} | NetGen-TI {tw(netgen - ti):.1f} | "
            f"scored supply-consistent {tw(scd):.1f} | model served {tw(dem_m):.1f}"
        )
        print("-- (b) solar/wind: potential vs delivered vs model (annual TWh) --")
        s_hsl, s_del = hsl["solar_hsl_mw"].to_numpy(float), hsl["solar_gen_mw"].to_numpy(float)
        w_hsl, w_del = hsl["wind_hsl_mw"].to_numpy(float), hsl["wind_gen_mw"].to_numpy(float)
        print(
            f"solar: HSL {tw(s_hsl):.2f} del {tw(s_del):.2f} model {tw(m['solar']):.2f} "
            f"| curt actual {tw(s_hsl) - tw(s_del):.2f} model {tw(s_hsl) - tw(m['solar']):.2f} "
            f"| model-over-delivered {tw(m['solar']) - tw(s_del):+.2f}"
        )
        print(
            f"wind:  HSL {tw(w_hsl):.2f} del {tw(w_del):.2f} model {tw(m['wind']):.2f} "
            f"| curt actual {tw(w_hsl) - tw(w_del):.2f} model {tw(w_hsl) - tw(m['wind']):.2f}"
        )
        curt_hod = pd.Series((s_hsl - m["solar"]) / 1e3).groupby(np.arange(T) % 24).mean()
        acurt_hod = pd.Series((s_hsl - s_del) / 1e3).groupby(np.arange(T) % 24).mean()
        print("belly curtailment hod10-15 (GW): model",
              [round(curt_hod[h], 2) for h in range(10, 16)], "actual",
              [round(acurt_hod[h], 2) for h in range(10, 16)])

        print("-- (c) BELLY (hod 10-15) component ledger: model - actual, GW mean --")
        rows = {
            "solar": m["solar"] - act["solar"],
            "wind": m["wind"] - act["wind"],
            "hydro": m["hydro"] - act["hydro"],
            "nuclear": m["nuclear"] - act["nuclear"],
            "gas(CEMS)": gas_m - gas_a,
            "net_import": m["import"] - act["net_import"],
            "stor+geo/other": (
                m.get("OTHER", 0) + m.get("biomass", 0) + m.get("oil", 0)
                + m.get("COAL", 0) + stor_m
            ) - act["oth_batt"],
            "dump(model curtail extra)": -dump,
        }
        for k, v in rows.items():
            print(f"  {k:26s} belly {gw(np.asarray(v, float), BELLY):+.2f}  evening {gw(np.asarray(v, float), EVE):+.2f}")
        print(f"  demand (scored-vs-model)   belly {gw(scd - dem_m, BELLY):+.2f} (must be ~0)")

        # ---- export-floor decomposition ----
        act_imp = act["net_import"]
        imp_m = m["import"]
        wedge = imp_m - act_imp
        exp_h = act_imp < 0
        b = BELLY
        w_exp = np.where(exp_h, wedge, 0.0)[b].mean()
        w_exp_floor = np.where(exp_h, np.minimum(-act_imp, wedge), 0.0)[b].mean()
        w_imp = np.where(~exp_h, wedge, 0.0)[b].mean()
        print("-- EXPORT-FLOOR --")
        print(
            f"  actual net-EXPORT hours {int(exp_h.sum())} ({100 * exp_h.mean():.1f}%), "
            f"belly-export hrs {int((exp_h & b).sum())}, export mean {act_imp[exp_h].mean():.0f} MW "
            f"| model min net import {imp_m.min():.0f} MW (can-export: {bool((imp_m < 0).any())})"
        )
        print(
            f"  belly wedge {wedge[b].mean() / 1e3:+.2f} GW = export-hrs {w_exp / 1e3:+.2f} "
            f"(floor<0 part {w_exp_floor / 1e3:+.2f}) + import-hrs {w_imp / 1e3:+.2f}"
        )
        if (b & exp_h).any():
            print(
                f"  in belly export-hours: actual {act_imp[b & exp_h].mean() / 1e3:+.2f} GW "
                f"vs model {imp_m[b & exp_h].mean() / 1e3:+.2f} GW"
            )
        month = pd.date_range(f"{year}-01-01", periods=T, freq="h").month
        exp_month = pd.Series(exp_h.astype(float)).groupby(month).sum()
        print("  export hours by month:", {int(k): int(v) for k, v in exp_month.items()})
        print(f"  model dump all-zones {tw(dump):.2f} TWh (belly {gw(dump, BELLY):.2f} GW)")


if __name__ == "__main__":
    main()
