"""SPP close-out 0b (zero LP): is the flat SUMMER_CLASS_DERATE a double count on SPP's CT/CC pmax?

Charter: closeout-SPP wave 1, plan §3.4 row 0b (`DESIGN-spp-104` §-end side observation (c)); the
finding is routed to the W0 lane (plan §2.1 row 2, E.1: "the flat class derate is deleted for
plant-level fleets"), never fixed here.

The keeper recipe (`spp100_arm_span/run_config_<Y>.json`): `plant_level_fleet=True`,
`summer_derate_basis_aware=False`, `cc_nameplate_summer_derate=False`, `temp_dependent_derate=False`,
and SPP is absent from `CAMPD_BINNING_ISOS`, so its thermal fleet is the per-plant EIA-860 loader
(`eia860.py` `pmax = net_summer_capacity_mw, else nameplate`) and `arrays.py` multiplies Jun-Sep
availability of CT_PEAKER / CT_CHP by 0.875 and CC_REGULAR / CC_CHP by 0.90 on top of it.

Per vintage year this probe loads the keeper's fleet (`load_fleet_from_csv("SPP", year=Y)`, the
same loader the solve calls, with the keeper's heat-rate flags irrelevant to capacity) and, per
flat-derate class, reports:
  * carried pmax (MW) and how much of it equals the EIA-860 net-summer rating vs nameplate,
  * the plants the CC guard clipped onto a nameplate-like basis (`cc_pmax_reconciled_plants`),
  * the EIA-860 measured nameplate -> net-summer gap of the same plants (the ambient loss the
    flat derate is meant to represent),
  * the summer MW the flat derate removes on top of a net-summer basis (the double count).

Usage: uv run python scripts/probes/_spp_closeout_ct_pmax_basis.py
Writes results/phase0/spp/_spp_closeout_ct_pmax_basis.json.
"""

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.constants import SUMMER_CLASS_DERATE  # noqa: E402
from market_sim.config.paths import active_eia860_dir, set_eia860_vintage  # noqa: E402
from market_sim.data.fleet.eia860 import (  # noqa: E402
    cc_pmax_reconciled_plants,
    load_fleet_from_csv,
)

OUT = REPO / "results/phase0/spp/_spp_closeout_ct_pmax_basis.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
TOL = 0.01  # carried pmax within 1 % of a published rating counts as that basis


def eia860_plant_ratings() -> pd.DataFrame:
    """Per-plant summed nameplate / net-summer over the active vintage's operable gas CT/CC rows."""
    df = pd.read_parquet(
        active_eia860_dir() / "eia860_generator_operable.parquet",
        columns=["Plant Code", "Technology", "Nameplate Capacity (MW)", "Summer Capacity (MW)"],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()].copy()
    df = df[df["Technology"].astype(str).str.contains("Natural Gas Fired Com|Combustion Turbine|Internal Comb", regex=True)]
    df["plant_code"] = df["Plant Code"].astype(float).astype(int)
    df["np"] = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    df["ns"] = pd.to_numeric(df["Summer Capacity (MW)"], errors="coerce")
    return df.groupby("plant_code")[["np", "ns"]].sum(min_count=1)


def year_row(year: int) -> dict:
    """One vintage year's class table."""
    set_eia860_vintage(year)
    gens = load_fleet_from_csv("SPP", year=year)
    rat = eia860_plant_ratings()
    clipped = set(cc_pmax_reconciled_plants("SPP"))
    rows = [
        {"plant": int(g.plant_code), "cls": g.plant_group, "pmax": float(g.pmax_mw)}
        for g in gens
        if g.plant_group in SUMMER_CLASS_DERATE
    ]
    df = pd.DataFrame(rows)
    out: dict = {}
    for cls, grp in df.groupby("cls"):
        pp = grp.groupby("plant")["pmax"].sum().to_frame().join(rat, how="left")
        on_ns = (pp["ns"] > 0) & ((pp["pmax"] - pp["ns"]).abs() <= TOL * pp["ns"])
        on_np = ~on_ns & (pp["np"] > 0) & ((pp["pmax"] - pp["np"]).abs() <= TOL * pp["np"])
        is_clip = pp.index.isin(list(clipped))
        matched = pp["np"].notna() & pp["ns"].notna()
        d = SUMMER_CLASS_DERATE[cls]
        gap = float((pp.loc[matched, "np"] - pp.loc[matched, "ns"]).sum() / pp.loc[matched, "np"].sum())
        out[cls] = {
            "plants": int(len(pp)),
            "pmax_mw": round(float(pp["pmax"].sum()), 1),
            "pmax_on_net_summer_mw": round(float(pp.loc[on_ns, "pmax"].sum()), 1),
            "pmax_on_nameplate_mw": round(float(pp.loc[on_np, "pmax"].sum()), 1),
            "pmax_other_mw": round(float(pp.loc[~on_ns & ~on_np, "pmax"].sum()), 1),
            "pmax_cc_guard_clipped_mw": round(float(pp.loc[is_clip, "pmax"].sum()), 1),
            "share_on_net_summer": round(float(pp.loc[on_ns, "pmax"].sum() / pp["pmax"].sum()), 4),
            "flat_derate": d,
            "measured_np_to_ns_gap": round(gap, 4),
            "summer_mw_removed_on_ns_basis": round(d * float(pp.loc[on_ns & ~is_clip, "pmax"].sum()), 1),
        }
    out["total_double_count_mw"] = round(
        sum(v["summer_mw_removed_on_ns_basis"] for k, v in out.items() if isinstance(v, dict)), 1
    )
    return out


def main() -> None:
    """Compute and write the per-year basis table."""
    res = {y: year_row(y) for y in YEARS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1))
    for y, r in res.items():
        print(y, "total double-count MW (Jun-Sep):", r["total_double_count_mw"])
        for cls, v in r.items():
            if isinstance(v, dict):
                print("   ", cls, v)


if __name__ == "__main__":
    main()
