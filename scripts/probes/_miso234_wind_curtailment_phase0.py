"""miso-234 phase 0 part C — WHY IS MISO WIND OVERPRODUCING? Zero LP.

The keeper's wind is +4.720 / +5.057 / +5.096 TWh over the EIA-930 delivered
actual in 2023 / 2024 / 2025 — the largest single-class C1 residual after
CC_REGULAR, and remarkably stable across years, which is the signature of a
CONSTRUCTION, not of a dispatch accident.

MISO wind takes the ``forecast_uncurtailed`` reference-rate gross-up
(``data/renewables.py``): MISO publishes no hourly HSL/curtailment series, so the
delivered EIA-930 profile is grossed up to an uncurtailed potential by the
Potomac Economics (MISO IMM) measured annual wind curtailment rate, and the LP is
then expected to RE-CURTAIL endogenously under the modelled transmission limits.

This probe tests the hypothesis that the LP re-curtails NOTHING — i.e. that the
whole overproduction IS the gross-up, delivered in full — and, if so, measures
the congestion the re-curtailment would have to come from.

Usage: python3 scripts/probes/_miso234_wind_curtailment_phase0.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso233_sppseam_K"
OUT = REPO / "results/calibration/_miso234_wind_curtailment_phase0.json"
YEARS = (2023, 2024, 2025)


def main() -> int:
    from market_sim.data.renewables import _miso_wind_reference_curtailment_rate

    rate, ref_year = _miso_wind_reference_curtailment_rate()
    grossup = 1.0 / (1.0 - rate)

    report = {
        "probe": "miso-234 phase 0 part C — MISO wind overproduction",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "reference_curtailment_rate": round(rate, 6),
        "reference_rate_latest_year": ref_year,
        "implied_grossup_factor": round(grossup, 6),
        "years": {},
    }
    years_out = {}

    for year in YEARS:
        act = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz"))
        act = act["bench"]["classFull"]
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        mod = cls.groupby("klass")["mw"].sum() / 1e6

        wind_act = float(act["wind"])
        wind_mod = float(mod["wind"])
        potential = wind_act * grossup
        curtailed_model = potential - wind_mod

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        pz = {z: g.sort_values("hour")["price"].to_numpy(float)
              for z, g in sysf.groupby("zone")}
        internal = [z for z in pz if z.startswith("MISO-")]
        stack = np.vstack([pz[z] for z in internal])
        spread_hourly = stack.max(0) - stack.min(0)

        z = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet")
        zy = z[z["year"] == year]
        mz = zy.groupby(["zone", "hour"])["da"].mean().unstack(0)
        mz = mz.reindex(range(8760)).interpolate(limit=3).ffill().bfill()
        meas_spread = (mz.max(axis=1) - mz.min(axis=1)).to_numpy(float)

        years_out[str(year)] = {
            "wind_actual_TWh": round(wind_act, 4),
            "wind_model_TWh": round(wind_mod, 4),
            "wind_residual_TWh": round(wind_mod - wind_act, 4),
            "uncurtailed_potential_TWh": round(potential, 4),
            "model_curtailment_TWh": round(curtailed_model, 4),
            "model_curtailment_pct_of_potential": round(100 * curtailed_model / potential, 3),
            "reported_curtailment_pct": round(100 * rate, 3),
            "residual_explained_by_grossup_pct": round(
                100 * (potential - wind_act) / (wind_mod - wind_act), 2
            ),
            "solar_residual_TWh": round(float(mod["solar"]) - float(act["solar"]), 4),
            "model_max_minus_min_zonal_price_mean": round(float(spread_hourly.mean()), 2),
            "measured_max_minus_min_zonal_price_mean": round(float(meas_spread.mean()), 2),
            "zonal_spread_compression_ratio": round(
                float(spread_hourly.mean() / meas_spread.mean()), 3
            ),
            "model_hours_all_zones_within_1_usd_pct": round(
                float(100 * (spread_hourly < 1.0).mean()), 1
            ),
            "measured_hours_all_zones_within_1_usd_pct": round(
                float(100 * (meas_spread < 1.0).mean()), 1
            ),
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")
    print(f"MISO IMM reference wind-curtailment rate: {100*rate:.3f} % "
          f"(latest contributing year {ref_year}); gross-up x{grossup:.5f}\n")
    for year in YEARS:
        y = years_out[str(year)]
        print(f"================== {year} ==================")
        print(f"  wind actual (EIA-930 delivered)  {y['wind_actual_TWh']:9.4f} TWh")
        print(f"  wind uncurtailed potential       {y['uncurtailed_potential_TWh']:9.4f} TWh"
              f"   (= actual x {grossup:.5f})")
        print(f"  wind MODEL                       {y['wind_model_TWh']:9.4f} TWh")
        print(f"  -> model re-curtailment          {y['model_curtailment_TWh']:+9.4f} TWh"
              f"   = {y['model_curtailment_pct_of_potential']:.3f} % of potential"
              f"   (reported {y['reported_curtailment_pct']:.3f} %)")
        print(f"  -> wind residual                 {y['wind_residual_TWh']:+9.4f} TWh;"
              f" {y['residual_explained_by_grossup_pct']:.1f} % of it IS the gross-up")
        print(f"  solar residual (delivered-pinned, control) {y['solar_residual_TWh']:+.4f} TWh")
        print(f"  internal zonal price spread (max-min, mean $/MWh):"
              f" model {y['model_max_minus_min_zonal_price_mean']:.2f}"
              f"  vs measured {y['measured_max_minus_min_zonal_price_mean']:.2f}"
              f"   (compression {y['zonal_spread_compression_ratio']:.3f})")
        print(f"  hours with every zone within $1: model"
              f" {y['model_hours_all_zones_within_1_usd_pct']:.1f} %"
              f"  vs measured {y['measured_hours_all_zones_within_1_usd_pct']:.1f} %")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
