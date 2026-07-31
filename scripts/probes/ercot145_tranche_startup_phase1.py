"""ERCOT-145 Phase 1 — tranche_startup_amortization on ERCOT: is the A/B worth a solve?

No LP, no solve, no parameter changed. Matrix §5.1 item 5 chartered the
mid-merit/peak price-formation A/B: the PJM/MISO/NEISO fast-start tranche
startup amortization (``tranche_startup_amortization`` + measured-run v3)
against ERCOT's existing startup price formation, targeting the NON-TAIL
component of C3a-2024/25 and C3b. This probe runs the three Phase-1 legs the
charter pre-registered and decides in writing whether Phase 2 (the solve) is
licensed:

1. **OWNER** — enumerate what ERCOT's P1 already prices for startup, per class
   and tranche row, on the ``ercot144_perplant_arm`` keeper's own
   ``run_config.json`` (rule 19 ``[R-ONE-MECH]``: the current owner of
   startup-cost price formation must be enumerated before the tranche form is
   proposed).
2. **TARGET** — quantify the lane's object on the keeper's committed hourly
   sidecars: the load-quintile × actual-price-band decomposition of the
   sub-$200 residual, 2023/2024/2025, model demand-weighted hub vs the
   committed hourly RT actual
   (``data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet``).
3. **REACH** — the candidate's maximum price effect: the measured ERCOT CT
   run-length horizon (``campd_ct_run_lengths_ERCOT.csv``, produced this
   session by the frozen rule-23 derive from ERCOT's own CAMPD units,
   2023-2025 only) implies a $20/MW ÷ 4-6 h = **$3.3-5.0/MWh** fuel-invariant
   component, against the fitted CT band margins already on the same rows.

Usage::

    python scripts/probes/ercot145_tranche_startup_phase1.py \
        --bundle results/calibration/ercot144_perplant_arm

Rule notes: measurement only (rules 13/14 — measured conduct and committed
sidecars read as evidence, never fed back); ERCOT-scoped (rule 25); training
years 2023-2025 only (rule 22). The load-weighted decomposition here is an
HOURLY demand-weighted diagnostic instrument — the official C3a gate weights
zone ANNUAL means by zone demand, so the headline percentages differ from the
rubric's (-34.2/-9.0/-8.4 here vs -36.4/-14.8/-14.3 official); the
decomposition, not the headline, is the evidence.
"""

from __future__ import annotations

import argparse
import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent

# NREL/SR-5500-55433 start costs by class (fleet.eia860.BIN_STARTUP_COST_PER_MW).
CT_STARTUP_PER_MW = 20.0
# The keeper's resolved CT_PEAKER offer multipliers vs their recorded physical
# basis (run_config.json offer_curve_by_group; phys_* = measured marginal-HR
# basis rows carried in the same config).
FITTED_VS_PHYS = {
    "committed": (1.14, 1.022),
    "econ_low": (1.27, 0.723),
    "econ_high": (2.18, 0.727),
    "peak": (13.15, 1.0),
}


def hub_series(bundle: Path, year: int) -> pd.DataFrame:
    """Model demand-weighted hub price + system load + hourly RT actual."""
    sy = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sy = sy[sy["pass"] == "P1"]
    g = sy.groupby("hour")
    hub = g.apply(
        lambda x: np.average(x["price"], weights=np.maximum(x["demand"], 1e-9))
    )
    load = g["demand"].sum()
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    a = act[act["year"] == year].set_index("hour")["rt"].reindex(hub.index)
    df = pd.DataFrame({"model": hub, "act": a, "load": load}).dropna()
    df["q"] = pd.qcut(df["load"], 5, labels=False)
    return df


def leg1_owner(bundle: Path) -> None:
    """Enumerate the keeper's current startup price-formation owners."""
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]
    print("=" * 72)
    print("LEG 1 — the current owner of startup price formation (rule 19)")
    print("=" * 72)
    print(
        f"  tranche_startup_amortization={sc['tranche_startup_amortization']}  "
        f"measured_runs={sc['tranche_startup_measured_runs']}  "
        f"conditional_runs={sc['tranche_startup_conditional_runs']}"
    )
    print(
        f"  gas_st_startup_cost={sc['gas_st_startup_cost']}  "
        f"gas_st_startup_spread={sc['gas_st_startup_spread']}  "
        f"(ST_GAS committed row, May-Sep season-spread P1 markup)"
    )
    print(
        f"  ercot_gas_commitment_bridge={sc['ercot_gas_commitment_bridge']}  "
        f"bridge_startup={sc['ercot_gas_bridge_startup']}  "
        f"(gas-CC STATE leg, startup-restart inequality on P0 duals — not a bid)"
    )
    print(
        "  committed tranches (all CAMPD bins): NREL start cost amortized over\n"
        "    P0 monthly run lengths (compute_monthly_markup) — the P0->P1 seam.\n"
        "  CT_PEAKER/CT_CHP econ+peak, CC peak rows: NO explicit startup term;\n"
        "    priced by the FITTED offer_curve_by_group band multipliers\n"
        "    (residual-identified DOF, ledger row offer_curve_by_group)."
    )


def leg2_target(bundle: Path) -> None:
    """Decompose the sub-$200 residual by load quintile and actual band."""
    print("=" * 72)
    print("LEG 2 — the target, decomposed (hourly demand-weighted diagnostic)")
    print("=" * 72)
    for year in (2023, 2024, 2025):
        df = hub_series(bundle, year)
        lw = lambda v, w: np.average(v, weights=w)  # noqa: E731
        tot = df["load"].sum()
        sub, tail = df[df.act < 200], df[df.act >= 200]
        gap_sub = ((sub.model - sub.act) * sub.load).sum() / tot
        gap_tail = ((tail.model - tail.act) * tail.load).sum() / tot
        print(
            f"\n  {year}: lw model {lw(df.model, df.load):.2f} vs act "
            f"{lw(df.act, df.load):.2f} ({100 * (lw(df.model, df.load) / lw(df.act, df.load) - 1):+.1f}%)"
            f"  | lw gap $: sub-200 {gap_sub:+.2f}  tail(n={len(tail)}) {gap_tail:+.2f}"
        )
        t = df[(df.q == 4) & (df.act < 200)]
        for lo, hi in ((0, 30), (30, 50), (50, 100), (100, 200)):
            s = t[(t.act >= lo) & (t.act < hi)]
            if len(s):
                print(
                    f"    q4 & act in [{lo:>3},{hi:>3}): n={len(s):4d}  "
                    f"gap {(s.model - s.act).mean():+7.2f} $/MWh"
                )


def leg3_reach(bundle: Path) -> None:
    """Measured amortization component vs the fitted margins on the same rows."""
    print("=" * 72)
    print("LEG 3 — candidate reach vs the fitted occupant of the same rows")
    print("=" * 72)
    rl = pd.read_csv(
        REPO / "data/raw/_processed-legacy/campd_ct_run_lengths_ERCOT.csv"
    )
    fleet_rows = rl[rl.plant_code != 0]
    fallback = rl[rl.plant_code == 0]["median_run_hours"].iloc[0]
    q25, q50, q75 = fleet_rows["median_run_hours"].quantile([0.25, 0.5, 0.75])
    print(
        f"  measured ERCOT CT run medians: plant p25/p50/p75 = "
        f"{q25:.0f}/{q50:.0f}/{q75:.0f} h, class fallback {fallback:.0f} h "
        f"({len(fleet_rows)} plants; the >100 h rows are industrial cogens — "
        f"Air Liquide, Sweeny — quasi-baseload CT_CHP hosts, not peakers)"
    )
    print(
        f"  v3 amortization component: ${CT_STARTUP_PER_MW}/MW / {q75:.0f}-"
        f"{q25:.0f} h = ${CT_STARTUP_PER_MW / q75:.1f}-"
        f"${CT_STARTUP_PER_MW / q25:.1f}/MWh (fuel-invariant)"
    )
    b = pd.read_csv(REPO / "data/raw/reference/custom-bin-assignments.csv")
    ct = b[b["Plant_Group"] == "CT_PEAKER"].dropna(
        subset=["Plant_Avg_HR_MMBtu_MWh", "Nameplate_MW"]
    )
    bhr = np.average(ct["Plant_Avg_HR_MMBtu_MWh"], weights=ct["Nameplate_MW"])
    print(f"  CT_PEAKER cap-wt base HR {bhr:.2f} MMBtu/MWh; fitted margin on rows:")
    for band, (fit, phys) in FITTED_VS_PHYS.items():
        d = fit - phys
        print(
            f"    {band:10s} fitted {fit:6.2f} phys {phys:5.3f}  "
            f"=> +${d * bhr * 2.2:6.1f}/MWh @$2.2 gas, +${d * bhr * 3.4:6.1f} @$3.4"
        )


def leg2b_months(bundle: Path) -> None:
    """Monthly residual (the C3b object) for the amortization-signature check."""
    print("=" * 72)
    print("LEG 2b — monthly residual shape (C3b object)")
    print("=" * 72)
    mb = np.cumsum([0] + [calendar.monthrange(2023, m)[1] * 24 for m in range(1, 13)])
    for year in (2024, 2025):
        df = hub_series(bundle, year)
        mon = np.searchsorted(mb, df.index, side="right") - 1
        gap = (df.model - df.act).groupby(mon).mean()
        print(
            f"  {year}: "
            + " ".join(f"{m + 1}:{v:+.1f}" for m, v in gap.items())
        )


def main() -> None:
    """Run the three Phase-1 legs against a keeper bundle."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--bundle",
        default="results/calibration/ercot144_perplant_arm",
        help="keeper bundle directory (run_config.json + hourly/ sidecars)",
    )
    args = ap.parse_args()
    bundle = Path(args.bundle)
    leg1_owner(bundle)
    leg2_target(bundle)
    leg2b_months(bundle)
    leg3_reach(bundle)


if __name__ == "__main__":
    main()
