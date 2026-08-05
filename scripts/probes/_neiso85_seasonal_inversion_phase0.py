"""neiso-85 Phase 0 — the 2022 seasonal price inversion, measured from committed artifacts.

NO LP IS BUILT AND NO YEAR IS SOLVED. This probe reads (a) the committed
touchpoint sidecars for 2022, (b) the committed keeper sidecars for the tuned
years, and (c) the fuel-price resolution chain evaluated as a pure function of
``(config, year)`` — which is data inspection, not dispatch. The holdout spend
freeze (``frontend/data/backcast/holdout-freeze.json``) is respected: 2022 is
read, never re-solved and never re-scored.

Phase-0 questions, from the neiso-85 charter:
  1. Decompose the summer leg: what is the model running at the margin in
     May-Oct 2022, and how does that compare with the in-sample summers?
  2. Test the fuel-price confound FIRST: is the summer over-pricing gas
     passthrough on a mis-resolved 2022 gas price, or a real merit-order error?
  3. Winter leg: measure whether the dormant winter mechanisms would have bound
     in 2022 (reserve shortfall / duals in Jan/Feb/Dec).
  4. One object or two (rule 19 ``[R-ONE-MECH]``).

Usage:
    python scripts/probes/_neiso85_seasonal_inversion_phase0.py
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fuel.trajectories import _gas_series
from market_sim.data.fuel.resolve import resolve_annual_gas_price

ROOT = REPO_ROOT
TOUCHPOINT = ROOT / "results/calibration/neiso2022_touchpoint"
OUT = ROOT / "results/calibration/_neiso85_phase0.json"

# The touchpoint bundle persists two passes and is SCORED on the later one
# (neiso-84 §3: the recipe carries commitment=true, so run_year's legacy pass
# runs and the dispatch it returns is what the run was rendered from).
SCORED_PASS = "P2"

MONTH_NAMES = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]


def hour_to_month(hours: int = 8760) -> np.ndarray:
    """Return a ``(hours,)`` 1-indexed calendar month for a non-leap 8760 year."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:hours]


def load_config(run_config_path: Path) -> ScenarioConfig:
    """Rebuild the exact ScenarioConfig a run was solved under."""
    blob = json.loads(run_config_path.read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in blob.items() if k in fields})


def resolved_gas_monthly(config: ScenarioConfig, year: int) -> pd.Series:
    """Return the model's own delivered gas series ($/MMBtu), averaged by month.

    ``_gas_series`` is the exact chain the merit order prices gas at:
    annual level -> generic seasonal shape -> EIA-923 measured ISO-month
    -> hub-basis overlay -> (daily HH shape is applied by resolve_fuel_prices
    on top, mean-preserving per month, so the monthly mean here is the level
    the gas units bid at).
    """
    cfg = dataclasses.replace(config, hours=8760)
    series = _gas_series(cfg, year, 8760)
    months = hour_to_month(8760)
    return pd.Series(series).groupby(months).mean()


def main() -> None:
    out: dict = {}

    cfg2022 = load_config(TOUCHPOINT / "run_config.json")
    print("=" * 78)
    print("A. RESOLVED DELIVERED GAS ($/MMBtu), model's own chain, by month")
    print("=" * 78)
    gas = {}
    for yr in (2022, 2023, 2024, 2025):
        try:
            gas[yr] = resolved_gas_monthly(cfg2022, yr)
        except Exception as exc:  # pragma: no cover - diagnostic
            print(f"  {yr}: FAILED {exc!r}")
    tab = pd.DataFrame(gas)
    tab.index = [MONTH_NAMES[i - 1] for i in tab.index]
    print(tab.round(3).to_string())
    print()
    print("annual mean:", {y: round(float(s.mean()), 3) for y, s in gas.items()})
    print("annual override resolve_annual_gas_price:",
          {y: round(float(resolve_annual_gas_price(cfg2022, y)), 4)
           for y in (2022, 2023, 2024, 2025)})
    out["resolved_gas_monthly"] = {
        str(y): {MONTH_NAMES[i - 1]: round(float(v), 4) for i, v in s.items()}
        for y, s in gas.items()
    }

    print()
    print("=" * 78)
    print("B. 2022 MODEL PRICES from the committed touchpoint sidecar")
    print("=" * 78)
    sysdf = pd.read_parquet(TOUCHPOINT / "hourly/system_2022.parquet")
    print("passes present:", sorted(sysdf["pass"].unique()))
    sysdf = sysdf[sysdf["pass"] == SCORED_PASS].copy()
    sysdf["month"] = hour_to_month()[sysdf["hour"].to_numpy()]
    # Load-weighted LMP across zones, the C3a basis.
    grp = sysdf.groupby("month").apply(
        lambda d: np.average(d["price"], weights=d["demand"].clip(lower=1e-9)),
        include_groups=False,
    )
    simple = sysdf.groupby("month")["price"].mean()
    print(pd.DataFrame({"load_wtd": grp.round(2), "simple": simple.round(2)}).to_string())
    out["model_2022_monthly_lmp_loadwtd"] = {
        MONTH_NAMES[i - 1]: round(float(v), 3) for i, v in grp.items()
    }

    print()
    print("=" * 78)
    print("C. RESERVE FAMILIES 2022 — is any hour reserve-short? (winter leg)")
    print("=" * 78)
    rf = pd.read_parquet(TOUCHPOINT / "hourly/reserve_family_2022.parquet")
    rf = rf[rf["pass"] == SCORED_PASS].copy()
    rf["month"] = hour_to_month()[rf["hour"].to_numpy()]
    print("total family-hours:", len(rf))
    print("shortfall_mw: max =", float(rf["shortfall_mw"].max()),
          " nonzero count =", int((rf["shortfall_mw"] > 0).sum()))
    print("dual:          max =", float(rf["dual"].max()),
          " nonzero count =", int((rf["dual"].abs() > 1e-9).sum()))
    winter = rf[rf["month"].isin([1, 2, 12])]
    print("WINTER (Jan/Feb/Dec) family-hours:", len(winter),
          " shortfall>0:", int((winter["shortfall_mw"] > 0).sum()),
          " |dual|>1e-9:", int((winter["dual"].abs() > 1e-9).sum()))
    out["reserve_2022"] = {
        "family_hours": int(len(rf)),
        "shortfall_max_mw": float(rf["shortfall_mw"].max()),
        "shortfall_nonzero_hours": int((rf["shortfall_mw"] > 0).sum()),
        "dual_abs_max": float(rf["dual"].abs().max()),
        "winter_shortfall_nonzero": int((winter["shortfall_mw"] > 0).sum()),
    }

    print()
    print("=" * 78)
    print("D. CLASS DISPATCH 2022 by month (TWh) — the marginal-class decomposition")
    print("=" * 78)
    ch = pd.read_parquet(TOUCHPOINT / "hourly/class_hourly_2022.parquet")
    ch = ch[ch["pass"] == SCORED_PASS].copy()
    ch["month"] = hour_to_month()[ch["hour"].to_numpy()]
    piv = ch.pivot_table(index="month", columns="klass", values="mw", aggfunc="sum") / 1e6
    piv.index = [MONTH_NAMES[i - 1] for i in piv.index]
    print(piv.round(4).to_string())
    out["class_twh_2022_by_month"] = {
        k: {m: round(float(v), 5) for m, v in piv[k].items()} for k in piv.columns
    }

    OUT.write_text(json.dumps(out, indent=2))
    print()
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
