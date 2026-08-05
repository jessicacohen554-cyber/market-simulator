"""neiso-85 Phase 0 — attribution of the 2022 price residual to the gas-basis defect.

NO LP, NO SOLVE, NO SCORING. Three measurements:

  A. ATTRIBUTION. Is the model's 2022 monthly price residual consistent in
     SIGN and MAGNITUDE with the measured delivered-gas input error, at a
     single constant heat rate? This is a diagnostic decomposition of an
     already-committed residual, NOT a re-score and NOT a tuned correction —
     no parameter is fitted and nothing is written back into any config.
  B. THE DUAL-FUEL TELL. The inverted basis prices summer gas above oil
     parity, so the winter fuel-security switch should fire in SUMMER.
  C. BLAST RADIUS. Which ISOs and which years draw on the defective proxy
     source, and which ISOs arm the overlay that consumes it.

Usage:
    python scripts/probes/_neiso85_attribution.py
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT
from market_sim.config.scenarios import ScenarioConfig

ROOT = REPO_ROOT
TOUCHPOINT = ROOT / "results/calibration/neiso2022_touchpoint"
OUT = ROOT / "results/calibration/_neiso85_attribution.json"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
SCORED_PASS = "P2"

# Actual NEISO 2022 RT load-weighted LMP by month, as quoted in the neiso-85
# charter (its own restatement of the touchpoint scoring). Used here only as
# the reference the residual is measured against — nothing is fitted to it.
ACTUAL_RT_2022 = [148.7, 108.7, 66.4, 59.4, 74.8, 71.7,
                  90.7, 96.0, 61.4, 52.3, 67.4, 121.5]

# NEISO marginal gas heat rate. NOT fitted here: it is the committed
# cap-weighted CC_REGULAR p50 quoted in the NEISO keeper shard's neiso-83
# block ("cap-weighted p50 7.340"), used as a single constant across all 12
# months so the attribution has zero free parameters.
MARGINAL_HEAT_RATE = 7.340


def hour_to_month(hours: int = 8760) -> np.ndarray:
    """Return a ``(hours,)`` 1-indexed calendar month for a non-leap 8760 year."""
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.repeat(np.arange(1, 13), [d * 24 for d in days])[:hours]


def main() -> None:
    out: dict = {}
    chain = json.loads((ROOT / "results/calibration/_neiso85_gas_chain.json").read_text())
    stage3 = chain["stages"]["3_monthly_actuals"]["2022"]   # measured EIA-923 ISO-month
    stage4 = chain["stages"]["4_hub_overlay"]["2022"]       # what the LP actually used

    sysdf = pd.read_parquet(TOUCHPOINT / "hourly/system_2022.parquet")
    sysdf = sysdf[sysdf["pass"] == SCORED_PASS].copy()
    sysdf["month"] = hour_to_month()[sysdf["hour"].to_numpy()]
    model_lmp = sysdf.groupby("month").apply(
        lambda d: np.average(d["price"], weights=d["demand"].clip(lower=1e-9)),
        include_groups=False,
    )

    print("=" * 96)
    print("A. ATTRIBUTION — does the measured gas-input error explain the price residual?")
    print(f"   single constant heat rate = {MARGINAL_HEAT_RATE} MMBtu/MWh (committed "
          f"CC_REGULAR cap-wtd p50), zero fitted parameters")
    print("=" * 96)
    print(f"{'mon':>4} {'gas_used':>9} {'gas_923':>9} {'d_gas':>8} "
          f"{'HR*d_gas':>9} | {'model':>8} {'actual':>8} {'resid':>8} "
          f"{'explained':>10} {'unexpl':>8}")
    rows = []
    for i, m in enumerate(MONTHS):
        used, meas = stage4[m], stage3[m]
        dgas = used - meas
        expl = dgas * MARGINAL_HEAT_RATE
        model = float(model_lmp.loc[i + 1])
        actual = ACTUAL_RT_2022[i]
        resid = model - actual
        unexpl = resid - expl
        rows.append(dict(month=m, gas_used=used, gas_923=meas, d_gas=dgas,
                         explained=expl, model=model, actual=actual,
                         residual=resid, unexplained=unexpl))
        print(f"{m:>4} {used:9.2f} {meas:9.2f} {dgas:8.2f} {expl:9.1f} | "
              f"{model:8.1f} {actual:8.1f} {resid:8.1f} {expl:10.1f} {unexpl:8.1f}")

    resid_arr = np.array([r["residual"] for r in rows])
    expl_arr = np.array([r["explained"] for r in rows])
    unexpl_arr = np.array([r["unexplained"] for r in rows])
    print()
    print(f"  MAE of residual   (model vs actual)      : {np.abs(resid_arr).mean():7.2f} $/MWh")
    print(f"  MAE after removing the gas-input error   : {np.abs(unexpl_arr).mean():7.2f} $/MWh")
    print(f"  share of monthly |residual| explained    : "
          f"{100 * (1 - np.abs(unexpl_arr).sum() / np.abs(resid_arr).sum()):6.1f} %")
    print(f"  corr(residual, explained)                : "
          f"{np.corrcoef(resid_arr, expl_arr)[0, 1]:7.3f}")
    out["attribution"] = {
        "heat_rate_mmbtu_per_mwh": MARGINAL_HEAT_RATE,
        "rows": [{k: (round(v, 4) if isinstance(v, float) else v)
                  for k, v in r.items()} for r in rows],
        "mae_residual": round(float(np.abs(resid_arr).mean()), 4),
        "mae_unexplained": round(float(np.abs(unexpl_arr).mean()), 4),
        "share_explained_pct": round(
            float(100 * (1 - np.abs(unexpl_arr).sum() / np.abs(resid_arr).sum())), 2),
        "corr_residual_explained": round(float(np.corrcoef(resid_arr, expl_arr)[0, 1]), 4),
    }

    print()
    print("=" * 96)
    print("B. THE DUAL-FUEL TELL — the winter fuel-security switch firing in SUMMER")
    print("=" * 96)
    ch = pd.read_parquet(TOUCHPOINT / "hourly/class_hourly_2022.parquet")
    ch = ch[ch["pass"] == SCORED_PASS].copy()
    ch["month"] = hour_to_month()[ch["hour"].to_numpy()]
    piv = ch.pivot_table(index="month", columns="klass", values="mw", aggfunc="sum") / 1e6
    cfg_blob = json.loads((TOUCHPOINT / "run_config.json").read_text())["scenario_config"]
    oil_parity_note = {
        k: cfg_blob.get(k) for k in
        ("dual_fuel_switching", "dual_fuel_oil_reattribution", "neiso_oil_burn_budget")
    }
    print("  flags:", oil_parity_note)
    print()
    print(f"{'mon':>4} {'gas_used':>9} {'oil_TWh':>9} {'CC_REG_TWh':>11}")
    for i, m in enumerate(MONTHS):
        print(f"{m:>4} {stage4[m]:9.2f} {float(piv.loc[i + 1, 'oil']):9.4f} "
              f"{float(piv.loc[i + 1, 'CC_REGULAR']):11.4f}")
    oil_by_month = {m: round(float(piv.loc[i + 1, "oil"]), 5) for i, m in enumerate(MONTHS)}
    summer_oil = sum(oil_by_month[m] for m in ["Jun", "Jul", "Aug", "Sep"])
    winter_oil = sum(oil_by_month[m] for m in ["Jan", "Feb", "Dec"])
    print()
    print(f"  oil energy Jun-Sep = {summer_oil:.4f} TWh   vs   Jan/Feb/Dec = {winter_oil:.4f} TWh")
    print(f"  ratio summer:winter = {summer_oil / max(winter_oil, 1e-9):,.0f} : 1")
    out["dual_fuel_tell"] = {
        "oil_twh_by_month": oil_by_month,
        "summer_jun_sep_twh": round(summer_oil, 5),
        "winter_jan_feb_dec_twh": round(winter_oil, 5),
    }

    print()
    print("=" * 96)
    print("C. BLAST RADIUS — who draws on the defective proxy source")
    print("=" * 96)
    basis = pd.read_csv(ROOT / "data/raw/gas_basis_by_iso_month.csv")
    # A row USES the proxy only when its source STARTS with the EIA series
    # citation. Rows that merely mention "N3050" in prose are the ones that
    # REJECTED it (NEISO Aug-2025 interpolates the measured index instead and
    # says so), so a bare substring test mis-flags them as defective.
    basis["is_proxy"] = basis["source"].str.strip().str.startswith("EIA N3050", na=False)
    tab = basis.pivot_table(index="iso", columns="year", values="is_proxy", aggfunc="mean")
    print("  fraction of each (iso, year)'s rows sourced from the EIA N3050 retail proxy:")
    print(tab.round(2).to_string())
    print()
    # Seasonality sign of the basis itself: winter (Jan/Feb/Dec) minus summer (Jun-Aug).
    print("  basis seasonality  winter(Jan,Feb,Dec) - summer(Jun,Jul,Aug), $/MMBtu")
    print("  (NEGATIVE = INVERTED: the proxy makes summer gas dearer than winter)")
    seas = {}
    for (iso, yr), g in basis.groupby(["iso", "year"]):
        mm = g.set_index("month")["basis_usd_mmbtu"]
        if not {1, 2, 12}.issubset(mm.index) or not {6, 7, 8}.issubset(mm.index):
            continue
        seas[(iso, yr)] = mm.loc[[1, 2, 12]].mean() - mm.loc[[6, 7, 8]].mean()
    sdf = pd.Series(seas).unstack()
    print(sdf.round(2).to_string())
    out["blast_radius"] = {
        "proxy_fraction": {str(i): {str(c): (None if pd.isna(v) else round(float(v), 3))
                                    for c, v in r.items()} for i, r in tab.iterrows()},
        "basis_seasonality_winter_minus_summer": {
            str(i): {str(c): (None if pd.isna(v) else round(float(v), 3))
                     for c, v in r.items()} for i, r in sdf.iterrows()},
    }

    OUT.write_text(json.dumps(out, indent=2))
    print()
    print("wrote", OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()
