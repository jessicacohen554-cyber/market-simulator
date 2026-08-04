"""nyiso-123 — the model's zonal price identity, month by month, for all three training years.

nyiso-122 measured that the keeper prices its four mainland zones **identically in
100.0 %** of Jan+Feb 2025 hours while the market ran a **$44.28** all-5 zonal
spread, and concluded the winter half of the C3a-2025 miss is **locational, not
fuel**.  It measured Jan+Feb only.  The brief for this session asks the obvious
leave-one-year-out question: **is the identity share ~100 % in 2023 and 2024 too?**
If it is, 2025 fails for a reason other than a newly-appeared locational defect.

This probe answers that across all twelve months of all three training years, and
adds the number a topology-split charter would actually be pre-registered against.

## The analytical trap this probe is built to avoid

A **pure redistribution** of price across zones that holds the load-weighted mean
fixed does **not** move C3a -- C3a *is* the load-weighted mean.  So "the model has
no zonal spread" is not, on its own, an explanation of a *mean* miss, and this
probe must not be read as asserting that it is.

The mechanism by which a locational failure becomes a mean failure is specific:
the model prices every zone at the **unconstrained upstate** marginal cost, and
~65 % of NYISO load sits **downstate** of the constraint.  The counterfactual
therefore anchors on upstate and adds the *observed* basis,

    m*[z,k] = m[Upstate_West,k] + (a[z,k] - a[Upstate_West,k])

at monthly grain (the committed per-zone actuals are monthly), load-weighted with
the model's own demand so both sides share one basis.  It is a **diagnostic bound
only**: the observed basis is a measured OUTCOME and under rule 13 ``[R-MEASURED]``
it may never enter a solve.  Nothing here does, and no mechanism is proposed that
would consume it.

Reads only COMMITTED artifacts -- the keeper bundle's ``hourly/`` sidecars (rule 15),
the committed per-zone monthly actuals ``data/raw/_validation-source/actual_lmp.json``
and the committed hourly actual (for the hub cross-check only).  No LP, no derive,
no solve.

Rule 22: TRAINING YEARS ONLY; ``YEARS`` is a hard filter and the loaders raise.

Outputs ``results/calibration/_nyiso123_zonal_identity_allyears.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

YEARS: tuple[int, ...] = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]
HOURS = 8760

# The five model load zones.  NYISO_external is the import node, not a load zone,
# and carries no benchmarked actual, so it is excluded from every spread here.
ZONES = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island")
MAINLAND = ("Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC")
# The unconstrained reference zone.  nyiso-122 measured Upstate_West January 2025
# accurate to -0.35 $/MWh while every downstate zone was $29-45 short, so upstate
# is where the model's marginal energy cost is right and the basis is what is
# missing.  The counterfactual anchors here for that reason, not by convention.
REFERENCE_ZONE = "Upstate_West"
IDENTICAL_TOL = 0.01  # $/MWh -- the tolerance nyiso-122 used for "priced identically"

# Cold months.  Named for the seasonal VIEW only; the per-month rows are the
# measurement and this grouping never replaces them.
COLD = (12, 1, 2)

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/nyiso120_c119_scopegate"
ACTUAL_JSON = REPO / "data/raw/_validation-source/actual_lmp.json"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
OUT = REPO / "results/calibration/_nyiso123_zonal_identity_allyears.json"

# The model's fixed non-leap 8760-hour clock, keyed to 2023 and shared by every
# model year (build_ercot_as_withholding._CALENDAR).  See the sibling probe's note.
MONTH_OF_HOUR = pd.date_range("2023-01-01", periods=HOURS, freq="h").month.to_numpy()


def _model(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """P1 zonal ``(price, demand)`` frames for ``year``, indexed hour x zone."""
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    if df["pass"].nunique() > 1:  # P1 is the scored pass (spec section 1.6)
        df = df[df["pass"] == df["pass"].max()]
    df = df[df["zone"].isin(ZONES)]
    price = df.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(HOURS)
    )[list(ZONES)]
    dem = df.pivot_table(index="hour", columns="zone", values="demand").reindex(
        range(HOURS)
    )[list(ZONES)]
    return price, dem


def _actual_zonal_monthly(year: int) -> dict[str, np.ndarray]:
    """Committed per-zone monthly actual RT LMP for ``year``, 12 values per zone."""
    if year not in YEARS:  # rule 22 -- fail closed
        raise SystemExit(f"REFUSED: {year} is out-of-training for NYISO (rule 22)")
    z = json.loads(ACTUAL_JSON.read_text())["NYISO"][str(year)]["zones"]
    return {k: np.asarray(z[k]["rt_mon"], dtype=float) for k in ZONES}


def _actual_hub_lw(year: int, dem_tot: np.ndarray) -> float:
    """Hub hourly actual, load-weighted on the model's demand -- the C3a basis."""
    if year not in YEARS:
        raise SystemExit(f"REFUSED: {year} is out-of-training for NYISO (rule 22)")
    df = pd.read_parquet(ACTUAL_HOURLY)
    df = df[df["year"] == year]
    a = np.full(HOURS, np.nan)
    hr = df["hour"].to_numpy(int)
    keep = hr < HOURS
    a[hr[keep]] = df["rt"].to_numpy(float)[keep]
    ok = np.isfinite(a) & np.isfinite(dem_tot) & (dem_tot > 0)
    return float(np.average(a[ok], weights=dem_tot[ok]))


def measure(year: int) -> dict:
    """Per-month zonal identity, actual spread, and the zonal-basis counterfactual."""
    price, dem = _model(year)
    pm, dm = price.to_numpy(float), dem.to_numpy(float)
    act = _actual_zonal_monthly(year)
    zi = {z: i for i, z in enumerate(ZONES)}
    main_ix = [zi[z] for z in MAINLAND]

    # ---- per-hour cross-zone spreads ---------------------------------------
    spread_all5 = np.nanmax(pm, axis=1) - np.nanmin(pm, axis=1)
    spread_main = np.nanmax(pm[:, main_ix], axis=1) - np.nanmin(pm[:, main_ix], axis=1)

    total_load = float(np.nansum(dm))
    months, cf_num, base_num, act_num = [], 0.0, 0.0, 0.0

    for k in range(1, 13):
        hk = MONTH_OF_HOUR == k
        if not hk.any():
            continue
        wk = dm[hk]  # hours x zones demand in month k
        wz = np.nansum(wk, axis=0)  # per-zone load in month k
        # demand-weighted monthly model price per zone
        mz = np.nansum(pm[hk] * wk, axis=0) / wz
        az = np.array([act[z][k - 1] for z in ZONES], dtype=float)

        # THE COUNTERFACTUAL: keep the model's own upstate level, add the
        # observed basis of every other zone against upstate.  Diagnostic only.
        basis = az - az[zi[REFERENCE_ZONE]]
        mz_cf = mz[zi[REFERENCE_ZONE]] + basis

        base_num += float(np.sum(wz * mz))
        cf_num += float(np.sum(wz * mz_cf))
        act_num += float(np.sum(wz * az))

        months.append(
            {
                "month": k,
                "load_share_pct": round(100 * float(wz.sum()) / total_load, 3),
                # ---- the identity fact, per month ----
                "mainland4_identical_pct": round(
                    100 * float(np.mean(spread_main[hk] < IDENTICAL_TOL)), 2
                ),
                "all5_identical_pct": round(
                    100 * float(np.mean(spread_all5[hk] < IDENTICAL_TOL)), 2
                ),
                "model_mainland4_spread_mean": round(float(np.nanmean(spread_main[hk])), 3),
                "model_all5_spread_mean": round(float(np.nanmean(spread_all5[hk])), 3),
                # ---- what the market did over the same month ----
                "actual_all5_spread": round(float(az.max() - az.min()), 2),
                "actual_nyc_minus_upstate": round(
                    float(az[zi["NYC"]] - az[zi[REFERENCE_ZONE]]), 2
                ),
                "model_nyc_minus_upstate": round(
                    float(mz[zi["NYC"]] - mz[zi[REFERENCE_ZONE]]), 2
                ),
                # ---- per-zone monthly gap ----
                "zone_gap": {z: round(float(mz[zi[z]] - az[zi[z]]), 2) for z in ZONES},
                "reference_zone_gap": round(
                    float(mz[zi[REFERENCE_ZONE]] - az[zi[REFERENCE_ZONE]]), 2
                ),
                # load-weighted contribution of month k to the ANNUAL gap, on the
                # zonal-actual basis
                "gap_contrib": round(
                    float(np.sum(wz * (mz - az))) / total_load, 3
                ),
                "cf_gap_contrib": round(
                    float(np.sum(wz * (mz_cf - az))) / total_load, 3
                ),
            }
        )

    base_lw, cf_lw, act_lw = (
        base_num / total_load,
        cf_num / total_load,
        act_num / total_load,
    )
    hub_lw = _actual_hub_lw(year, np.nansum(dm, axis=1))

    # ---- THE IDENTITY ------------------------------------------------------
    # Substituting m*[z,k] into the load-weighted mean, the a[z,k] terms cancel
    # exactly and the counterfactual error collapses to ONE quantity:
    #
    #   cf_lw - act_lw = sum_k sum_z w[z,k](m_up[k] + a[z,k] - a_up[k] - a[z,k]) / W
    #                  = sum_k W[k](m_up[k] - a_up[k]) / W
    #                  = the model's REFERENCE-ZONE pricing error, weighted by TOTAL load.
    #
    # So a model that reproduced the observed basis perfectly would carry exactly
    # the C3a error of its own unconstrained upstate price -- no more, no less.
    # That makes the reference-zone gap the charter's real target, and it is
    # asserted here rather than left to be re-derived by a reader.
    ref_gap_lw = sum(
        (r["load_share_pct"] / 100.0) * r["reference_zone_gap"] for r in months
    )
    assert abs((cf_lw - act_lw) - ref_gap_lw) < 0.05, (
        f"{year}: counterfactual identity broken "
        f"({cf_lw - act_lw:.4f} vs {ref_gap_lw:.4f})"
    )

    # cold-months-only variant: apply the observed basis in Dec/Jan/Feb only
    cold_cf = sum(r["cf_gap_contrib"] for r in months if r["month"] in COLD)
    cold_base = sum(r["gap_contrib"] for r in months if r["month"] in COLD)
    cf_cold_lw = base_lw + (cold_cf - cold_base)

    return {
        "year": year,
        "months": months,
        "annual": {
            # every figure below is on the ZONAL-ACTUAL basis unless named otherwise
            "model_lw_monthly_grain": round(base_lw, 2),
            "actual_lw_zonal_monthly": round(act_lw, 2),
            "actual_lw_hub_hourly": round(hub_lw, 2),
            "basis_difference_zonal_minus_hub": round(act_lw - hub_lw, 2),
            "err_pct_baseline": round(100 * (base_lw - act_lw) / act_lw, 2),
            "cf_model_lw": round(cf_lw, 2),
            "cf_err_pct": round(100 * (cf_lw - act_lw) / act_lw, 2),
            "cf_lift_usd_mwh": round(cf_lw - base_lw, 2),
            "cf_cold_only_model_lw": round(cf_cold_lw, 2),
            "cf_cold_only_err_pct": round(100 * (cf_cold_lw - act_lw) / act_lw, 2),
            # the identity above: what the whole counterfactual reduces to
            "reference_zone_gap_lw": round(ref_gap_lw, 2),
            "reference_zone_gap_pct": round(100 * ref_gap_lw / act_lw, 2),
        },
        "identity": {
            "mainland4_identical_pct_year": round(
                100 * float(np.mean(spread_main < IDENTICAL_TOL)), 2
            ),
            "all5_identical_pct_year": round(
                100 * float(np.mean(spread_all5 < IDENTICAL_TOL)), 2
            ),
            "model_mainland4_spread_mean_year": round(float(np.nanmean(spread_main)), 3),
        },
    }


def main() -> None:
    res = {
        "probe": "nyiso-123 -- zonal identity by month + zonal-basis counterfactual, all training years (no LP)",
        "keeper": "2026-08-04-nyiso-120-c119-scope",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "reference_zone": REFERENCE_ZONE,
        "years": list(YEARS),
        "counterfactual_note": (
            "DIAGNOSTIC BOUND ONLY (rule 13 [R-MEASURED]). m*[z,k] = m[Upstate_West,k] + "
            "(a[z,k] - a[Upstate_West,k]) at monthly grain, load-weighted on the model's own "
            "demand. The observed basis is a measured OUTCOME and never enters a solve; no "
            "mechanism is proposed that would consume it."
        ),
        "results": [measure(y) for y in YEARS],
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")

    for r in res["results"]:
        a = r["annual"]
        print(f"\n=== {r['year']}   mainland-4 priced IDENTICALLY in "
              f"{r['identity']['mainland4_identical_pct_year']:.2f}% of all hours "
              f"(all-5 {r['identity']['all5_identical_pct_year']:.2f}%)")
        print(f"  {'mo':>3}{'main4 id%':>11}{'all5 id%':>10}{'act spread':>12}"
              f"{'act NYC-UP':>12}{'mod NYC-UP':>12}{'UP gap':>9}{'NYC gap':>9}{'contrib':>9}")
        for x in r["months"]:
            print(
                f"  {x['month']:3d}{x['mainland4_identical_pct']:11.1f}"
                f"{x['all5_identical_pct']:10.1f}{x['actual_all5_spread']:12.2f}"
                f"{x['actual_nyc_minus_upstate']:12.2f}{x['model_nyc_minus_upstate']:12.2f}"
                f"{x['reference_zone_gap']:+9.2f}{x['zone_gap']['NYC']:+9.2f}"
                f"{x['gap_contrib']:+9.3f}"
            )
        print(f"  baseline model {a['model_lw_monthly_grain']:.2f} vs zonal-actual "
              f"{a['actual_lw_zonal_monthly']:.2f} -> {a['err_pct_baseline']:+.2f}%"
              f"   (hub-hourly actual {a['actual_lw_hub_hourly']:.2f}, basis diff "
              f"{a['basis_difference_zonal_minus_hub']:+.2f})")
        print(f"  COUNTERFACTUAL observed basis, all year: {a['cf_model_lw']:.2f} "
              f"({a['cf_err_pct']:+.2f}%), lift {a['cf_lift_usd_mwh']:+.2f} $/MWh")
        print(f"  COUNTERFACTUAL cold months (Dec/Jan/Feb) only: "
              f"{a['cf_cold_only_model_lw']:.2f} ({a['cf_cold_only_err_pct']:+.2f}%)")

    print("\n=== CROSS-YEAR SUMMARY")
    print(f"  {'year':>6}{'main4 id%':>11}{'C3a base%':>11}{'C3a cf%':>10}{'cf lift$':>10}"
          f"{'UP gap $':>10}{'UP gap %':>10}")
    for r in res["results"]:
        a = r["annual"]
        print(f"  {r['year']:6d}{r['identity']['mainland4_identical_pct_year']:11.2f}"
              f"{a['err_pct_baseline']:+11.2f}{a['cf_err_pct']:+10.2f}"
              f"{a['cf_lift_usd_mwh']:+10.2f}{a['reference_zone_gap_lw']:+10.2f}"
              f"{a['reference_zone_gap_pct']:+10.2f}")
    print(
        "\n  IDENTITY: the counterfactual error EQUALS the load-weighted "
        f"{REFERENCE_ZONE} gap.\n"
        "  A model reproducing the observed basis perfectly would score exactly its own\n"
        "  unconstrained-zone pricing error -- so that gap, not the basis, is what caps\n"
        "  what a topology split can deliver in each year."
    )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
