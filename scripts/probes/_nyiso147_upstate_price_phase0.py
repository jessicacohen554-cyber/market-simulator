"""nyiso-147 phase 0 — decompose the 2023 upstate price-level object.

The nyiso-146 reserve-duty arm (cc_reserve_duty_split) was REJECTED partly
because C3a-2023 fires +9.0% -> +11.3% when ~1.4 TWh of phantom cheap upstate
CC energy leaves the merit order. This probe decomposes, from COMMITTED
artifacts only (no solve):

  1. C3a verification per year/arm — model load-weighted mean LMP (P1, five
     load zones, weights = the measured zonal demand the model dispatches)
     vs the bench rt_lw actual.
  2. The 2023 zone x month error matrix (control): model equal-hour monthly
     mean LMP per zone vs the derived actual reference's per-zone rt_mon
     (data/raw/_validation-source/actual_lmp.json, the eleven NYISO zonal
     LBMPs folded to the five model zones).
  3. Zonal spread (seam) analysis: model vs actual monthly spreads across the
     Central-East / into-NYC / into-LI cutsets.
  4. The phantom-energy price effect: reserve-duty arm minus control price by
     zone x month — i.e. exactly what the ~1.4 TWh of phantom energy BUYS in
     the control's 2023 price fit (the rule-14 discovered-bug quantification).

Inputs (committed): results/calibration/nyiso146_control/hourly/system_*.parquet,
results/calibration/nyiso146b_reserve_arm/hourly/system_*.parquet,
results/calibration/nyiso146c_state_arm/hourly/system_*.parquet,
data/raw/_validation-source/actual_lmp.json,
frontend/data/backcast/bench/NYISO/<year>.json.gz.

Output: results/calibration/_nyiso147_upstate_price_phase0.json + stdout tables.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "NYISO"
REF = REPO / "data" / "raw" / "_validation-source" / "actual_lmp.json"

ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
YEARS = [2023, 2024, 2025]
BUNDLES = {
    "control": CAL / "nyiso146_control",
    "keeper": CAL / "nyiso146c_state_arm",
    "reserve_arm": CAL / "nyiso146b_reserve_arm",
}


def load_system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))].copy()
    df["month"] = pd.Timestamp(f"{year}-01-01").month  # placeholder
    # hour 0..8759 -> month via the year's own calendar
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    df["month"] = idx.month.values[df["hour"].to_numpy()]
    return df


def lw_mean(df: pd.DataFrame) -> float:
    return float((df["price"] * df["demand"]).sum() / df["demand"].sum())


def zone_month_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Equal-hour monthly mean price per zone (like the actual's rt_mon)."""
    return df.groupby(["zone", "month"])["price"].mean().unstack("month")


def zone_month_lw(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(["zone", "month"]).apply(
        lambda x: (x["price"] * x["demand"]).sum() / x["demand"].sum(),
        include_groups=False,
    )
    return g.unstack("month")


def main() -> None:
    ref = json.loads(REF.read_text())["NYISO"]
    out: dict = {"session": "nyiso-147", "phase": 0, "zones": ZONES}

    # ── 1. C3a verification ────────────────────────────────────────────────
    c3a = {}
    for year in YEARS:
        bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]
        rt_lw = bench["avgLMP"]["rt_lw"]
        row = {"actual_rt_lw": rt_lw}
        for arm, bundle in BUNDLES.items():
            df = load_system(bundle, year)
            m = lw_mean(df)
            row[arm] = {"model_lw": round(m, 2), "err_pct": round(100 * (m / rt_lw - 1), 1)}
        c3a[year] = row
    out["c3a"] = c3a
    print("== C3a (system load-weighted mean LMP, model vs rt_lw) ==")
    for year, row in c3a.items():
        print(
            f"  {year}: actual {row['actual_rt_lw']:.2f} | "
            + " | ".join(
                f"{arm} {row[arm]['model_lw']:.2f} ({row[arm]['err_pct']:+.1f}%)"
                for arm in BUNDLES
            )
        )

    # ── 2. 2023 zone x month error matrix (control), equal-hour basis ──────
    print("\n== 2023 zone x month: model (control) minus actual RT, $/MWh ==")
    dfs = {arm: load_system(b, 2023) for arm, b in BUNDLES.items()}
    zm_ctl = zone_month_mean(dfs["control"])
    zone_err: dict = {}
    act23 = ref["2023"]["zones"]
    hdr = "zone            " + " ".join(f"{m:>6}" for m in range(1, 13)) + "    ann"
    print(hdr)
    for z in ZONES:
        act_mon = np.array(act23[z]["rt_mon"], dtype=float)
        mod_mon = zm_ctl.loc[z].to_numpy()
        diff = mod_mon - act_mon
        ann_act, ann_mod = float(np.mean(act_mon)), float(np.mean(mod_mon))
        zone_err[z] = {
            "model_mon": [round(v, 2) for v in mod_mon],
            "actual_rt_mon": [round(v, 2) for v in act_mon],
            "diff_mon": [round(v, 2) for v in diff],
            "annual_model_eqh": round(ann_mod, 2),
            "annual_actual_rt": round(act23[z]["rt"], 2),
            "annual_err_pct": round(100 * (ann_mod / act23[z]["rt"] - 1), 1),
        }
        print(
            f"{z:<15} "
            + " ".join(f"{d:+6.1f}" for d in diff)
            + f"  {ann_mod - act23[z]['rt']:+6.2f} ({zone_err[z]['annual_err_pct']:+.1f}%)"
        )
    out["zone_month_2023_control"] = zone_err

    # per-zone contribution to the system lw error (model demand weights)
    print("\n== 2023 contribution to the lw system error, by zone ==")
    ctl = dfs["control"]
    wz = ctl.groupby("zone")["demand"].sum()
    wz = wz / wz.sum()
    sys_act = c3a[2023]["actual_rt_lw"]
    contrib = {}
    for z in ZONES:
        dz = ctl[ctl["zone"] == z]
        mod_lw_z = lw_mean(dz)
        act_z = act23[z]["rt"]  # equal-hour actual (no lw zonal actual committed)
        contrib[z] = {
            "weight": round(float(wz[z]), 4),
            "model_lw_zone": round(mod_lw_z, 2),
            "actual_rt_eqh_zone": act_z,
            "gap": round(mod_lw_z - act_z, 2),
            "contribution_pp_of_sys": round(100 * float(wz[z]) * (mod_lw_z - act_z) / sys_act, 2),
        }
        print(
            f"  {z:<15} w={wz[z]:.3f} model_lw {mod_lw_z:7.2f} vs act_eqh {act_z:7.2f} "
            f"gap {mod_lw_z - act_z:+6.2f} -> {contrib[z]['contribution_pp_of_sys']:+5.2f} pp"
        )
    out["zone_contribution_2023"] = contrib

    # ── 3. spread / seam analysis (2023 monthly) ───────────────────────────
    print("\n== 2023 monthly spreads (model ctl vs actual RT), $/MWh ==")
    spreads = {
        "CE_CapitalHudson_minus_UpstateWest": ("Capital_Hudson", "Upstate_West"),
        "NYC_minus_UpstateWest": ("NYC", "Upstate_West"),
        "LI_minus_NYC": ("Long_Island", "NYC"),
    }
    spread_out = {}
    for name, (a, b) in spreads.items():
        mod = (zm_ctl.loc[a] - zm_ctl.loc[b]).to_numpy()
        act = np.array(act23[a]["rt_mon"]) - np.array(act23[b]["rt_mon"])
        spread_out[name] = {
            "model_mon": [round(v, 2) for v in mod],
            "actual_mon": [round(v, 2) for v in act],
            "model_ann": round(float(np.mean(mod)), 2),
            "actual_ann": round(float(np.mean(act)), 2),
        }
        print(f"  {name}: model ann {np.mean(mod):+.2f} vs actual ann {np.mean(act):+.2f}")
        print("    model : " + " ".join(f"{v:+6.1f}" for v in mod))
        print("    actual: " + " ".join(f"{v:+6.1f}" for v in act))
    out["spreads_2023"] = spread_out

    # ── 4. what the phantom energy buys (reserve arm minus control) ────────
    print("\n== 2023 price effect of REMOVING the phantom energy (reserve_arm - control), $/MWh ==")
    zm_arm = zone_month_mean(dfs["reserve_arm"])
    phantom = {}
    for z in ZONES:
        d = (zm_arm.loc[z] - zm_ctl.loc[z]).to_numpy()
        phantom[z] = {
            "delta_mon": [round(v, 2) for v in d],
            "delta_ann_eqh": round(float(np.mean(d)), 2),
        }
        print(f"  {z:<15} " + " ".join(f"{v:+6.1f}" for v in d) + f"  ann {np.mean(d):+.2f}")
    # lw system deltas per year
    sys_delta = {}
    for year in YEARS:
        a = lw_mean(load_system(BUNDLES["reserve_arm"], year))
        c = lw_mean(load_system(BUNDLES["control"], year))
        sys_delta[year] = round(a - c, 2)
    phantom["system_lw_delta_by_year"] = sys_delta
    print(f"  system lw delta by year: {sys_delta}")
    out["phantom_price_effect_2023"] = phantom

    # share of the control's 2023 fit bought by the phantom energy:
    # control err = model_ctl - actual; the phantom masks (model_arm - model_ctl).
    e_ctl = c3a[2023]["control"]["err_pct"]
    e_arm = c3a[2023]["reserve_arm"]["err_pct"]
    out["bought_fit_2023"] = {
        "control_err_pct": e_ctl,
        "true_structure_err_pct_reserve_arm": e_arm,
        "masked_pp": round(e_arm - e_ctl, 1),
        "masked_share_of_true_overpricing": round((e_arm - e_ctl) / e_arm, 3),
    }
    print(
        f"\n== bought fit: control {e_ctl:+.1f}% vs phantom-removed {e_arm:+.1f}% "
        f"-> {e_arm - e_ctl:.1f} pp ({100 * (e_arm - e_ctl) / e_arm:.0f}% of the true overpricing) is masked =="
    )

    dst = CAL / "_nyiso147_upstate_price_phase0.json"
    dst.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {dst}")


if __name__ == "__main__":
    main()
