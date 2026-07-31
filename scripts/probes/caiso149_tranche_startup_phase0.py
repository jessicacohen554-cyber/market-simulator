"""caiso-149 Phase 0 — ``tranche_startup_amortization`` on CAISO: is the A/B licensed?

No LP, no solve, no parameter changed. Matrix §5.2 item 4 lists the lever as
untested in CAISO (cell ``U``); the handoff requires the two standing
adjudications — NYISO ``R`` (nyiso-96, rule 1) and ERCOT ``G`` (ERCOT-145,
rule 19, ex ante) — to be read first and CAISO's difference from both stated
before anything is armed. This probe runs the four Phase-0 legs and decides in
writing whether Phase 1 (the solve) is licensed:

1. **OWNER (rule 19 [R-ONE-MECH])** — enumerate what CAISO's P1 already prices
   on the rows the mechanism would mark up (CT_PEAKER / CT_CHP ``econ*`` +
   ``peak*``, CC_REGULAR / CC_CHP ``peak*``), and size the fuel-invariant
   $/MWh margin those rows already carry, per plant, on the keeper's own
   ``run_config.json`` + the committed measured heat-rate artifact.
2. **REACH** — the candidate's maximum price effect, from CAISO's OWN measured
   CT start-to-stop run lengths (``campd_ct_run_lengths_CAISO.csv``, derived
   this session by the frozen rule-23 deriver from CAISO's CAMPD units,
   2023-2025 only) crossed with the NREL class start costs the mechanism
   amortizes (``constants.CT_COMMITMENT_PARAMS``).
3. **PROVENANCE** — whether the incumbent on those rows is a FITTED value (the
   ERCOT regime: retirable in principle, which is why ERCOT-145 named a reopen
   condition) or a MEASURED one (nothing to retire; rule 14 [R-ACCURATE] runs
   the other way).
4. **DIRECTION** — the sign the arm would push the class the CAISO lane's own
   diagnosis says is under-produced, from the keeper's committed class hourlies
   against the CAMPD/EIA benchmark.

Usage::

    python scripts/probes/caiso149_tranche_startup_phase0.py \
        --bundle results/calibration/caiso148_nucavail_B

Rule notes: measurement only (rules 13/14 — measured conduct and committed
sidecars are read as evidence, never fed back); CAISO-scoped (rule 25 — every
number is derived from CAISO's own fleet, bids and CEMS, and no ERCOT/NYISO
value is transferred); training years 2023-2025 only (rule 22 — CAISO holds no
calibration-complete marker).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import CT_COMMITMENT_PARAMS  # noqa: E402

#: Groups whose ``econ*`` tranches the mechanism marks up (assembly.py ``_fsp_econ``).
FSP_ECON_GROUPS = ("CT_PEAKER", "CT_CHP")
#: Groups whose ``peak*`` tranches the mechanism marks up (assembly.py ``_fsp_peak``).
FSP_PEAK_GROUPS = ("CT_PEAKER", "CT_CHP", "CC_REGULAR", "CC_CHP")

BINS = REPO / "data/raw/_processed-legacy/bin_assignments_CAISO.csv"
CT_HR = REPO / "data/raw/_processed-legacy/campd_ct_heat_rates_CAISO.csv"
CHP_HR = REPO / "data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv"
RUNS = REPO / "data/raw/_processed-legacy/campd_ct_run_lengths_CAISO.csv"
MEASURED_OFFER = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"


def base_heat_rates() -> pd.DataFrame:
    """Per-plant base heat rate as the keeper resolves it.

    The curated CAMPD sheet's ``Plant_Avg_HR_MMBtu_MWh`` overlaid by the two
    measured-heat-rate swaps the keeper arms (``measured_ct_heat_rates``,
    caiso-146; ``measured_chp_heat_rates``, caiso-147) — so the base HR every
    band multiplier scales is the one the solve actually used.
    """
    fleet = pd.read_csv(BINS)[
        [
            "Plant_Code",
            "Plant_Name",
            "Plant_Group",
            "Nameplate_MW",
            "Plant_Avg_HR_MMBtu_MWh",
            "Pct_Must_Run",
            "Pct_Committed",
            "Pct_Economic",
            "Pct_Peaking",
        ]
    ].rename(columns={"Plant_Avg_HR_MMBtu_MWh": "base_hr"})
    for path, col in ((CT_HR, "heat_rate"), (CHP_HR, "heat_rate")):
        if not path.exists():
            continue
        meas = pd.read_csv(path)
        meas = meas[meas.get("flag", "ok").eq("ok")][["plant_code", col]]
        meas = meas.rename(columns={"plant_code": "Plant_Code", col: "_meas"})
        fleet = fleet.merge(meas, on="Plant_Code", how="left")
        fleet["base_hr"] = fleet["_meas"].fillna(fleet["base_hr"])
        fleet = fleet.drop(columns="_meas")
    return fleet


def leg1_owner(bundle: Path) -> pd.DataFrame:
    """Enumerate + size the incumbent owners of the target rows (rule 19)."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    curve = sc["offer_curve_by_group"]
    anchor = float(sc["gas_offer_margin_anchor"])

    print("=" * 78)
    print("LEG 1 — who already prices the target rows (rule 19 [R-ONE-MECH])")
    print("=" * 78)
    print(
        f"  tranche_startup_amortization={sc['tranche_startup_amortization']}  "
        f"measured_runs={sc['tranche_startup_measured_runs']}  "
        f"conditional_runs={sc['tranche_startup_conditional_runs']}"
    )
    print(
        f"  caiso_offer_surface_measured={sc['caiso_offer_surface_measured']}   "
        f"caiso_offer_surface_conditional={sc['caiso_offer_surface_conditional']}"
    )
    print(
        f"  gas_offer_net_revenue_margin={sc['gas_offer_net_revenue_margin']}  "
        f"anchor={anchor:.4f} $/MMBtu"
    )
    print(
        "\n  Row-by-row incumbents on the tranches the mechanism would mark up:\n"
        "    CT_PEAKER econ_low/econ_high/peak  -> caiso_offer_surface_measured\n"
        "        (CAISO's OWN DAM Public Bid Data medians, carbon/VOM-netted)\n"
        "        + gas_offer_net_revenue_margin (fixed $/MWh fuel-invariant margin)\n"
        "    CC_REGULAR peak                    -> same pair\n"
        "    CT_CHP econ/peak, CC_CHP peak      -> band multipliers (not measured)\n"
        "        + gas_offer_net_revenue_margin\n"
        "    every _committed tranche           -> compute_monthly_markup already\n"
        "        amortizes the NREL start cost over P0 runs (the P0->P1 seam)"
    )

    fleet = base_heat_rates()
    rows = []
    for _, p in fleet.iterrows():
        grp = p["Plant_Group"]
        offer = curve.get(grp)
        if offer is None or p["base_hr"] <= 0:
            continue
        bands = []
        if grp in FSP_ECON_GROUPS:
            bands += [("econ_low", "Pct_Economic"), ("econ_high", "Pct_Economic")]
        if grp in FSP_PEAK_GROUPS:
            bands += [("peak", "Pct_Peaking")]
        for band, pct_col in bands:
            mult, phys = offer.get(band), offer.get(f"phys_{band}")
            if mult is None or phys is None:
                continue
            share = float(p[pct_col]) / 100.0
            if band == "econ_low":
                share *= float(offer.get("econ_low_share", 0.5))
            elif band == "econ_high":
                share *= 1.0 - float(offer.get("econ_low_share", 0.5))
            markup_hr = p["base_hr"] * max(0.0, float(mult) - float(phys))
            rows.append(
                {
                    "plant": p["Plant_Name"],
                    "group": grp,
                    "band": band,
                    "cap_mw": float(p["Nameplate_MW"]) * share,
                    "base_hr": p["base_hr"],
                    "mult": float(mult),
                    "phys": float(phys),
                    "markup_hr": markup_hr,
                    "margin_usd_mwh": markup_hr * anchor,
                }
            )
    tr = pd.DataFrame(rows)

    print("\n  Fuel-invariant $/MWh margin ALREADY on the target rows")
    print("  (markup_hr x anchor; capacity-weighted over the band's own MW):\n")
    print(
        f"    {'group':<11}{'band':<10}{'MW':>9}{'mult':>7}{'phys':>7}"
        f"{'$/MWh':>9}{'min':>8}{'max':>8}"
    )
    for (grp, band), g in tr.groupby(["group", "band"], sort=False):
        w = g["cap_mw"].clip(lower=1e-9)
        print(
            f"    {grp:<11}{band:<10}{g['cap_mw'].sum():>9.0f}"
            f"{g['mult'].iloc[0]:>7.3f}{g['phys'].iloc[0]:>7.3f}"
            f"{(g['margin_usd_mwh'] * w).sum() / w.sum():>9.2f}"
            f"{g['margin_usd_mwh'].min():>8.2f}{g['margin_usd_mwh'].max():>8.2f}"
        )
    return tr


def leg2_reach() -> pd.DataFrame:
    """Size the candidate's own effect from CAISO's measured run lengths."""
    print("\n" + "=" * 78)
    print("LEG 2 — the candidate's reach, on CAISO's own measured CT runs")
    print("=" * 78)
    runs = pd.read_csv(RUNS)
    # The curated sheet carries one row per (plant, class); a mixed facility
    # appears more than once. The run-length artifact is CT-scoped, so collapse
    # to the plant's CT row (capacity-weighted HR if a plant carries both).
    fleet = base_heat_rates()
    fleet = fleet[fleet["Plant_Group"].isin(FSP_ECON_GROUPS)]
    fleet = (
        fleet.assign(_w=fleet["Nameplate_MW"].clip(lower=1e-9))
        .groupby("Plant_Code")
        .apply(
            lambda g: pd.Series(
                {
                    "base_hr": (g["base_hr"] * g["_w"]).sum() / g["_w"].sum(),
                    "Nameplate_MW": g["Nameplate_MW"].sum(),
                }
            ),
            include_groups=False,
        )
    )
    pooled = runs[runs.plant_code == 0].iloc[0]
    print(
        f"  artifact: {len(runs) - 1} plants + pooled class fallback, "
        f"{int(pooled['n_runs']):,} runs, 2023-2025\n"
        f"  class median run {pooled['median_run_hours']:.1f} h  "
        f"mean {pooled['mean_run_hours']:.2f} h  p90 {pooled['p90_run_hours']:.1f} h"
    )
    print(
        "  NREL CT start cost (constants.CT_COMMITMENT_PARAMS, $/MW): "
        + ", ".join(
            f"HR<={c} -> {p['startup_per_mw']}" for c, p in CT_COMMITMENT_PARAMS
        )
    )
    out = []
    for _, r in runs[runs.plant_code != 0].iterrows():
        if r["plant_code"] not in fleet.index:
            continue
        hr = float(fleet.at[r["plant_code"], "base_hr"])
        start = next(p["startup_per_mw"] for c, p in CT_COMMITMENT_PARAMS if hr <= c)
        cap = float(fleet.at[r["plant_code"], "Nameplate_MW"])
        out.append(
            {
                "plant": r["plant_name"],
                "cap_mw": cap,
                "median_run_h": r["median_run_hours"],
                "start_per_mw": start,
                "amort_usd_mwh": start / max(r["median_run_hours"], 1e-9),
            }
        )
    df = pd.DataFrame(out)
    w = df["cap_mw"].clip(lower=1e-9)
    print(
        f"\n  amortized start component over the MEASURED horizon, {len(df)} plants:\n"
        f"    capacity-weighted {(df['amort_usd_mwh'] * w).sum() / w.sum():.2f} $/MWh"
        f"   median {df['amort_usd_mwh'].median():.2f}"
        f"   range {df['amort_usd_mwh'].min():.2f}-{df['amort_usd_mwh'].max():.2f}"
    )
    return df


def leg3_provenance() -> None:
    """State whether the incumbent on the target rows is fitted or measured."""
    print("\n" + "=" * 78)
    print("LEG 3 — provenance of the incumbent (the CAISO-vs-ERCOT difference)")
    print("=" * 78)
    doc = json.loads(MEASURED_OFFER.read_text())
    prov = doc["_provenance"]
    print(f"  source     : {prov['source']}")
    print(f"  gas basis  : {prov['gas_basis']}")
    print(
        f"  carbon     : netted at {prov['carbon_basis']['co2_factor_t_per_mmbtu']} t/MMBtu"
    )
    print(f"  VOM netted : {prov['vom_usd_per_mwh']}")
    per_year = prov["per_year_band_mults"]["CT_PEAKER"]
    print("\n  CT_PEAKER measured DAM bid multipliers, per trade year:")
    for band in ("committed", "econ_low", "econ_high", "peak"):
        vals = per_year[band]
        print(
            f"    {band:<10}"
            + "  ".join(f"{y}: {v:.3f}" for y, v in sorted(vals.items()))
        )
    print(
        "\n  => the econ/peak rows the mechanism targets carry a MEASUREMENT of the\n"
        "     CAISO CT fleet's own submitted DAM energy bid, not a fitted value."
    )


def leg4_direction(bundle: Path) -> None:
    """Report the class the arm would move, against its own benchmark."""
    print("\n" + "=" * 78)
    print("LEG 4 — direction, on the keeper's own committed class hourlies")
    print("=" * 78)
    for year in (2023, 2024, 2025):
        path = bundle / "hourly" / f"class_hourly_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        if "pass" in df.columns:
            df = df[df["pass"] == "P1"]
        tot = df.groupby("klass")["mw"].sum() / 1e6
        for cls in ("CT_PEAKER", "CT_CHP", "CC_REGULAR"):
            if cls in tot.index:
                print(f"  {year} {cls:<12} model {tot[cls]:7.3f} TWh")


def main() -> None:
    """Run the four Phase-0 legs and print the adjudication inputs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, type=Path)
    args = ap.parse_args()
    tr = leg1_owner(args.bundle)
    amort = leg2_reach()
    leg3_provenance()
    leg4_direction(args.bundle)

    print("\n" + "=" * 78)
    print("ADJUDICATION INPUT — incumbent margin vs candidate component")
    print("=" * 78)
    w = amort["cap_mw"].clip(lower=1e-9)
    cand = (amort["amort_usd_mwh"] * w).sum() / w.sum()
    for (grp, band), g in tr.groupby(["group", "band"], sort=False):
        if grp not in FSP_ECON_GROUPS and band != "peak":
            continue
        ww = g["cap_mw"].clip(lower=1e-9)
        inc = (g["margin_usd_mwh"] * ww).sum() / ww.sum()
        ratio = inc / cand if cand else float("inf")
        print(
            f"  {grp:<11}{band:<10} incumbent {inc:7.2f} $/MWh   "
            f"candidate {cand:5.2f}   ratio {ratio:5.2f}x"
        )


if __name__ == "__main__":
    main()
