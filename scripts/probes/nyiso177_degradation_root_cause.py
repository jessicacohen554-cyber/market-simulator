"""nyiso-177 phase-0 probe: root-cause the per-unit-attribution degradation.

Discharges PREREG-nyiso177 gates G1 (the rule-19 ``_FLEET_GROUP_OVERRIDE``
stack at Ravenswood) and G2 (is the arm's ST_GAS availability envelope
physically admissible), plus the phase-0 attribution reporting duty. Reads
committed artifacts only — NO SOLVE, no parameter touched.

Run: PYTHONPATH=.:src python scripts/probes/nyiso177_degradation_root_cause.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import outages

YEARS = (2023, 2024, 2025)
ISO = "NYISO"
OUT = Path("results/calibration/_nyiso177_root_cause_phase0.json")


def _legs() -> dict[str, dict[int, dict]]:
    """Return {leg: {year: {bin: mean availability}}} for the 2x2."""
    legs: dict[str, dict[int, dict]] = {}
    for name, per_unit, override in (
        ("L0_keeper_inc_ovr", False, True),
        ("L1_arm_pu_ovr", True, True),
        ("L2_pu_no_ovr", True, False),
        ("L3_inc_no_ovr", False, False),
    ):
        outages._FLEET_GROUP_OVERRIDE.clear()
        if override:
            outages._FLEET_GROUP_OVERRIDE[2500] = "ST_GAS"
        # The loader is lru_cache'd on its arguments and the override is module
        # state, so the cache MUST be dropped between legs or every leg after
        # the first silently returns the first leg's arrays.
        outages.unit_outage_derate_factors.cache_clear()
        legs[name] = {
            y: {
                k: float(np.mean(v))
                for k, v in outages.unit_outage_derate_factors(
                    y, iso=ISO, per_unit_crosswalk=per_unit
                ).items()
            }
            for y in YEARS
        }
    outages._FLEET_GROUP_OVERRIDE.clear()
    outages._FLEET_GROUP_OVERRIDE[2500] = "ST_GAS"  # restore committed state
    outages.unit_outage_derate_factors.cache_clear()
    return legs


def _booked_share(avail: dict, cap: dict, group: str) -> tuple[float, float]:
    """Nameplate-weighted mean (1 - availability) over one group's bins."""
    num = den = 0.0
    for (code, grp), mw in cap.items():
        if grp != group:
            continue
        den += mw
        num += mw * (1.0 - avail.get((code, grp), 1.0))
    return (num / den if den else 0.0), den


def main() -> None:
    legs = _legs()
    cap = outages._iso_plant_capacity(ISO, False, False)
    rec: dict = {"years": list(YEARS)}

    # ---- G1: the Ravenswood rule-19 stack -------------------------------
    g1 = {leg: {} for leg in legs}
    for leg, byyear in legs.items():
        for y in YEARS:
            g1[leg][y] = {
                "ST_GAS": byyear[y].get((2500, "ST_GAS"), 1.0),
                "CC_REGULAR": byyear[y].get((2500, "CC_REGULAR"), 1.0),
            }
    st_stable = all(
        abs(g1["L2_pu_no_ovr"][y]["ST_GAS"] - g1["L1_arm_pu_ovr"][y]["ST_GAS"]) <= 0.05
        for y in YEARS
    )
    cc_derated = any(g1["L2_pu_no_ovr"][y]["CC_REGULAR"] <= 0.95 for y in YEARS)
    cc_pinned = all(g1["L1_arm_pu_ovr"][y]["CC_REGULAR"] == 1.0 for y in YEARS)
    rec["G1"] = {
        "legs": g1,
        "st_gas_stable_within_0.05": st_stable,
        "cc_regular_derated_at_or_below_0.95": cc_derated,
        "cc_regular_pinned_at_1.0_under_override": cc_pinned,
        "verdict": "PASS" if (st_stable and cc_derated and cc_pinned) else "FAIL",
    }

    # ---- G2: is the arm's ST_GAS envelope admissible? -------------------
    g2 = {}
    for leg in ("L0_keeper_inc_ovr", "L1_arm_pu_ovr", "L2_pu_no_ovr"):
        g2[leg] = {}
        for y in YEARS:
            share, mw = _booked_share(legs[leg][y], cap, "ST_GAS")
            g2[leg][y] = {"booked_share": share, "bin_nameplate_mw": mw}
    over = any(g2["L1_arm_pu_ovr"][y]["booked_share"] > 0.40 for y in YEARS)
    rec["G2"] = {
        "metric": "nameplate-weighted mean (1 - availability) over NYISO ST_GAS bins",
        "norm_efor_plus_planned": "0.10-0.15",
        "threshold": 0.40,
        "by_leg": g2,
        "verdict": "OVER-BOOKED" if over else "WITHIN-BOUND",
    }

    # ---- phase-0 attribution: metered conduct of the moving plants ------
    movers = {}
    for y in YEARS:
        d = pd.read_parquet(f"data/raw/campd-unit-level/NY_{y}.parquet")
        d = d[d.facilityId == "2500"]
        g = d.groupby("unitId").agg(
            on_hours=("grossLoad", lambda x: int((x.fillna(0) > 1).sum())),
            gwh=("grossLoad", lambda x: float(x.fillna(0).sum() / 1e3)),
            pmax=("grossLoad", "max"),
        )
        movers[y] = {
            u: {
                "on_hours": int(r.on_hours),
                "gwh": round(float(r.gwh), 1),
                "pmax_mw": None if pd.isna(r.pmax) else float(r.pmax),
                "cf_of_pmax": (
                    None
                    if pd.isna(r.pmax) or not r.pmax
                    else round(float(r.gwh) * 1e3 / (float(r.pmax) * 8760), 4)
                ),
            }
            for u, r in g.iterrows()
        }
    rec["ravenswood_metered_conduct"] = movers

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({"G1": rec["G1"]["verdict"], "G2": rec["G2"]["verdict"]}, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
