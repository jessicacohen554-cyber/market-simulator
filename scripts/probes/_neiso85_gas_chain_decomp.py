"""neiso-85 Phase 0 — stage-by-stage decomposition of NEISO's delivered-gas chain.

NO LP, NO SOLVE. Pure evaluation of the fuel-price resolution chain as a
function of ``(config, year)``, to identify WHICH stage produces the 2022
seasonal inversion and whether the tuned years are shaped by a different
stage than 2022 is.

The chain (``data/fuel/trajectories._gas_series``):
    1. ``resolve_annual_gas_price``            -> flat annual level
    2. ``* gas_seasonal_shape``                -> generic seasonality
    3. ``iso_monthly_gas_prices`` overwrite    -> measured EIA-923 ISO-month
    4. ``_hub_overlay_series``                 -> measured hub spot (Algonquin)

Usage:
    python scripts/probes/_neiso85_gas_chain_decomp.py
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel import trajectories as traj
from market_sim.data.fuel.resolve import resolve_annual_gas_price
from market_sim.data.fuel.trajectories import gas_seasonal_shape

ROOT = REPO_ROOT
TOUCHPOINT = ROOT / "results/calibration/neiso2022_touchpoint"
OUT = ROOT / "results/calibration/_neiso85_gas_chain.json"
YEARS = (2022, 2023, 2024, 2025)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def hour_to_month(hours: int = 8760) -> np.ndarray:
    """Return a ``(hours,)`` 1-indexed calendar month for a non-leap 8760 year."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:hours]


def load_config() -> ScenarioConfig:
    """Rebuild the touchpoint's exact ScenarioConfig."""
    blob = json.loads((TOUCHPOINT / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in blob.items() if k in fields})


def monthly(series: np.ndarray) -> pd.Series:
    """Collapse an 8760 hourly series to its 12 monthly means."""
    return pd.Series(np.asarray(series, dtype=float)).groupby(hour_to_month()).mean()


def main() -> None:
    cfg = dataclasses.replace(load_config(), hours=8760)
    T = 8760
    rows: dict[str, dict[int, pd.Series]] = {
        "1_annual": {}, "2_seasonal": {}, "3_monthly_actuals": {}, "4_hub_overlay": {}
    }
    coverage: dict[str, dict] = {}

    for yr in YEARS:
        lvl = resolve_annual_gas_price(cfg, yr)
        s1 = np.full(T, lvl, dtype=float)
        s2 = lvl * gas_seasonal_shape(cfg, yr, T)

        measured = traj._pkg_ns().iso_monthly_gas_prices(cfg, yr)
        s3 = s2.copy()
        if measured is not None:
            hm = traj._expand_monthly_to_hourly(np.asarray(measured, dtype=float), T)
            s3 = np.where(np.isnan(hm), s2, hm)
        n_months_measured = (
            0 if measured is None
            else int(np.sum(~np.isnan(np.asarray(measured, dtype=float))))
        )

        s4 = traj._hub_overlay_series(s3.copy(), cfg, yr, T)
        n_hub_hours = int(np.sum(~np.isclose(s4, s3)))

        rows["1_annual"][yr] = monthly(s1)
        rows["2_seasonal"][yr] = monthly(s2)
        rows["3_monthly_actuals"][yr] = monthly(s3)
        rows["4_hub_overlay"][yr] = monthly(s4)
        coverage[str(yr)] = {
            "annual_level": round(float(lvl), 4),
            "eia923_months_with_receipts": n_months_measured,
            "eia923_monthly_values": (
                None if measured is None
                else [None if np.isnan(v) else round(float(v), 4)
                      for v in np.asarray(measured, dtype=float)]
            ),
            "hub_overlay_hours_changed": n_hub_hours,
            "hub_overlay_pct_of_year": round(100.0 * n_hub_hours / T, 2),
        }

    for stage, per_year in rows.items():
        tab = pd.DataFrame(per_year)
        tab.index = MONTHS
        print("=" * 74)
        print(f"STAGE {stage}  ($/MMBtu, monthly mean)")
        print("=" * 74)
        print(tab.round(3).to_string())
        print("  annual mean:", {y: round(float(s.mean()), 3) for y, s in per_year.items()})
        print()

    print("=" * 74)
    print("COVERAGE — which stage actually has data, per year")
    print("=" * 74)
    for yr, c in coverage.items():
        print(f"  {yr}: annual={c['annual_level']}  "
              f"EIA923 months with receipts={c['eia923_months_with_receipts']}/12  "
              f"hub-overlay hours={c['hub_overlay_hours_changed']} "
              f"({c['hub_overlay_pct_of_year']}% of year)")

    print()
    print("=" * 74)
    print("WINTER/SUMMER RATIO of the FINAL series (winter = Jan,Feb,Dec; summer = Jun-Aug)")
    print("=" * 74)
    for yr in YEARS:
        f = rows["4_hub_overlay"][yr]
        w = float(f.loc[[1, 2, 12]].mean())
        s = float(f.loc[[6, 7, 8]].mean())
        print(f"  {yr}: winter {w:7.3f}   summer {s:7.3f}   winter/summer = {w / s:6.3f}"
              f"   {'INVERTED (summer dearer)' if w < s else 'normal (winter dearer)'}")

    OUT.write_text(json.dumps(
        {
            "coverage": coverage,
            "stages": {
                st: {str(y): {MONTHS[i - 1]: round(float(v), 4) for i, v in s.items()}
                     for y, s in per_year.items()}
                for st, per_year in rows.items()
            },
        },
        indent=2,
    ))
    print()
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
