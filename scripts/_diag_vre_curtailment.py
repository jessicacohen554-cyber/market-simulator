"""Diagnostic: ERCOT VRE under-curtailment — dumping + storage-timing (step 2).

Reads a solved bundle (dispatch/system/flows/storage parquets) plus the measured
HSL parquets and answers:
  Q1  Does the model reach oversupply in the hours ERCOT really curtailed?
      (dump binding? model curtailment overlap? West export corridor saturation?)
  Q2  Is storage charging in the wrong hours (eating the hours curtailment would
      otherwise occur, or idle during the real curtailment hours)?

Pure read-only analysis — no solve, no writes to the bundle.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, "src")
import numpy as np
import pandas as pd

from market_sim.data.renewables import hsl_potential_mw, load_hsl_hourly

BUNDLE = Path(sys.argv[1])
YEARS = [int(y) for y in sys.argv[2:]] or [2023, 2024, 2025]
ISO = "ERCOT"
WEST = ("West", "Panhandle")
MWH_TWH = 1e6


def hod(T):
    return np.arange(T) % 24


for year in YEARS:
    print(f"\n{'=' * 72}\n{year}\n{'=' * 72}")
    disp = pd.read_parquet(BUNDLE / "dispatch" / f"{year}_P1.parquet")
    sysf = pd.read_parquet(BUNDLE / "system.parquet")
    sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == "P1")]
    flows = None
    fp = BUNDLE / "flows.parquet"
    if fp.exists():
        flows = pd.read_parquet(fp)
        flows = flows[(flows["year"] == year) & (flows["pass"] == "P1")]
    stor = None
    sp = BUNDLE / "storage.parquet"
    if sp.exists():
        stor = pd.read_parquet(sp)
        stor = stor[(stor["year"] == year) & (stor["pass"] == "P1")]

    hsl = load_hsl_hourly(ISO, year)
    T = 8760

    # --- model dispatched wind/solar per hour (system) ---
    model = {}
    for fuel in ("wind", "solar"):
        r = disp[disp["fuel"] == fuel]
        model[fuel] = (
            r.groupby("hour", observed=True)["mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy(float)
        )
    # per-zone dispatched (West/Panhandle)
    model_west = {}
    for fuel in ("wind", "solar"):
        r = disp[(disp["fuel"] == fuel) & (disp["zone"].isin(WEST))]
        model_west[fuel] = (
            r.groupby("hour", observed=True)["mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy(float)
        )

    print("\n[3e] model vs reported curtailment (potential = uncurtailed HSL):")
    print(
        f"  {'fuel':6s} {'pot TWh':>8s} {'mdl TWh':>8s} {'mdl curt':>9s} {'mdl%':>6s} {'rep curt':>9s} {'rep%':>6s}"
    )
    curt = {}
    for fuel in ("wind", "solar"):
        pot = np.maximum(hsl_potential_mw(ISO, year, fuel)[:T], 0.0)
        rep_pot = np.maximum(hsl[f"{fuel}_hsl_mw"].to_numpy(float)[:T], 0.0)
        deliv = np.minimum(
            np.maximum(hsl[f"{fuel}_gen_mw"].to_numpy(float)[:T], 0.0), rep_pot
        )
        mcurt = np.maximum(pot - model[fuel][:T], 0.0)
        rcurt = rep_pot - deliv
        curt[fuel] = {"model": mcurt, "reported": rcurt, "pot": pot, "rep_pot": rep_pot}
        print(
            f"  {fuel:6s} {pot.sum() / MWH_TWH:8.2f} {model[fuel].sum() / MWH_TWH:8.2f} "
            f"{mcurt.sum() / MWH_TWH:9.3f} {100 * mcurt.sum() / pot.sum():6.2f} "
            f"{rcurt.sum() / MWH_TWH:9.3f} {100 * rcurt.sum() / rep_pot.sum():6.2f}"
        )

    # --- Q1: does the model reach oversupply in the real curtailment hours? ---
    print("\nQ1  oversupply / dump behaviour:")
    dump_sys = (
        sysf.groupby("hour")["dump"]
        .sum()
        .reindex(range(T), fill_value=0)
        .to_numpy(float)
    )
    price_min = (
        sysf.groupby("hour")["price"].min().reindex(range(T)).to_numpy(float)
    )  # cheapest zone
    west_price = (
        sysf[sysf["zone"].isin(WEST)]
        .groupby("hour")["price"]
        .mean()
        .reindex(range(T))
        .to_numpy(float)
    )
    print(
        f"  system dump: total {dump_sys.sum() / MWH_TWH:.4f} TWh; hours>1MW {int((dump_sys > 1).sum())} "
        f"({100 * (dump_sys > 1).mean():.2f}%)"
    )
    print(
        f"  West zone price: <=$0 in {100 * (west_price <= 0).mean():.1f}% of hours; "
        f"<=$1 in {100 * (west_price <= 1).mean():.1f}%"
    )
    for fuel in ("wind", "solar"):
        rc = curt[fuel]["reported"]
        mc = curt[fuel]["model"]
        rep_hrs = rc > 50
        # in the hours ERCOT curtailed, what does the model do?
        mc_in_rep = mc[rep_hrs]
        frac_model_curt = 100 * (mc_in_rep > 50).mean() if rep_hrs.any() else 0
        wp_in_rep = west_price[rep_hrs]
        print(
            f"  {fuel}: reported-curt hours={int(rep_hrs.sum())}; "
            f"model also curtails(>50MW) in {frac_model_curt:.1f}% of them; "
            f"West price<=$1 in {100 * (wp_in_rep <= 1).mean():.1f}% of them; "
            f"model curt captured {100 * mc.sum() / max(rc.sum(), 1):.0f}% of reported vol"
        )

    # --- West export corridor saturation ---
    if flows is not None:
        print("\n  West/Panhandle export corridor saturation (flow at >=95% of TTC):")
        from market_sim.config.iso_configs import get_iso_config

        links = {(l.from_zone, l.to_zone): l.ttc_mw for l in get_iso_config(ISO).links}
        exp_links = [(f, t) for (f, t) in links if f in WEST and t not in WEST]
        tot_flow = np.zeros(T)
        tot_ttc = 0.0
        for f, t in exp_links:
            ttc = links[(f, t)]
            tot_ttc += ttc
            fl = flows[(flows["from_zone"] == f) & (flows["to_zone"] == t)]
            mw = (
                fl.set_index("hour")["mw"]
                .reindex(range(T), fill_value=0)
                .to_numpy(float)
            )
            tot_flow += mw
            print(
                f"    {f}->{t} (TTC {ttc:.0f}): flow>=95%TTC in {100 * (mw >= 0.95 * ttc).mean():5.1f}% of hours; "
                f"mean {mw.mean():.0f}, p95 {np.percentile(mw, 95):.0f}"
            )
        print(
            f"    AGGREGATE export (TTC {tot_ttc:.0f}): >=95% in {100 * (tot_flow >= 0.95 * tot_ttc).mean():.1f}% of hours; "
            f"mean {tot_flow.mean():.0f} p95 {np.percentile(tot_flow, 95):.0f} max {tot_flow.max():.0f}"
        )

    # --- Q2: storage timing vs reported curtailment ---
    if stor is not None and len(stor):
        print("\nQ2  storage charge timing vs reported curtailment:")
        chg_all = (
            stor.groupby("hour")["charge_mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy(float)
        )
        chg_west = (
            stor[stor["zone"].isin(WEST)]
            .groupby("hour")["charge_mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy(float)
        )
        dis_all = (
            stor.groupby("hour")["discharge_mw"]
            .sum()
            .reindex(range(T), fill_value=0)
            .to_numpy(float)
        )
        rc_tot = curt["wind"]["reported"] + curt["solar"]["reported"]
        rep_hrs = rc_tot > 50
        print(
            f"  storage charge: total {chg_all.sum() / MWH_TWH:.3f} TWh; West-zone {chg_west.sum() / MWH_TWH:.3f} TWh"
        )
        print(
            f"  mean charge in reported-curt hours {chg_all[rep_hrs].mean():.0f} MW vs "
            f"non-curt hours {chg_all[~rep_hrs].mean():.0f} MW"
        )
        # solar-midday alignment
        h = hod(T)
        mid = (h >= 10) & (h <= 16)
        print(
            f"  charge midday(10-16) share {100 * chg_all[mid].sum() / max(chg_all.sum(), 1):.0f}%; "
            f"discharge evening(17-21) share {100 * dis_all[(h >= 17) & (h <= 21)].sum() / max(dis_all.sum(), 1):.0f}%"
        )
