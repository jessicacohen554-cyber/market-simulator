"""nyiso-219 §Q1/Q3 — how many HOURS of pondage does NYISO's hydro fleet actually hold?

The owner funded the NID intake (Q1: "fund the full intake") and ruled Q3
**"Undecided — measure it"**: the shaping horizon must be established from licence
operating ranges, **not** from ORNL EHA's categorical ``Mode`` label. This probe is
that measurement, and it is deliberately built as an **UPPER BOUND**, because an
upper bound is logically sufficient:

    if even the most generous reading of a plant's storage holds far less than a
    month of generation, then a MONTHLY budget period overstates its intertemporal
    freedom -- and no refinement of the operating range can rescue the month.

**Every choice is made in the generous direction**, so the bound cannot be accused
of being tuned to reach a conclusion:

* **full reservoir volume**, not the licensed operating range (the range is a
  *band* inside this volume, so the true usable figure is strictly smaller --
  the charter named this overstatement in advance);
* both ``Normal`` and ``Max`` storage reported, ``Max`` being the larger;
* **turbine/generator efficiency = 1.0** -- a strict physical bound. Any real
  efficiency (~0.85-0.92) only *reduces* the hours;
* where NID's ``Hydraulic Height`` is absent, ``Dam Height`` stands in as a
  **labelled proxy**, and the direction of its error is reported per plant rather
  than assumed away.

Energy of a stored volume, from first principles and with **zero free parameters**::

    E(J)    = rho * g * V * H
    E(MWh)  = 1000 * 9.81 * V(m^3) * H(m) / 3.6e9
            = 1.0245e-3 * V(acre-ft) * H(ft)          [eta = 1.0]

    pondage_hours = E(MWh) / pmax(MW)

Sources, both committed: ``data/raw/hilarri/HILARRI_v4.csv`` (plant -> dam) and
``data/raw/nid/nid_nyiso_hydro_dams.csv`` (USACE National Inventory of Dams,
vintage 2026-08-28, the matched subset -- see that directory's README for the
source URL and checksum).

ZERO LP. Nothing armed, no ``ScenarioConfig`` field, keeper untouched.
Charter: ``docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

HILARRI = REPO / "data" / "raw" / "hilarri" / "HILARRI_v4.csv"
NID = REPO / "data" / "raw" / "nid" / "nid_nyiso_hydro_dams.csv"
OUT_JSON = REPO / "results" / "calibration" / "_nyiso219_pondage_duration.json"

# E(MWh) per (acre-foot x foot of head) at eta = 1.0. Derivation in the module
# docstring: rho*g*V*H / 3.6e9 with 1 acre-ft = 1233.4818 m^3 and 1 ft = 0.3048 m.
_MWH_PER_ACREFT_FOOT: float = 1000.0 * 9.81 * 1233.4818 * 0.3048 / 3.6e9

# The budget periods a shortened hydro row could use, for the comparison table.
_PERIOD_HOURS = {"day": 24.0, "week": 168.0, "month (the LP today)": 730.0}


def _num(frame: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(frame.get(column), errors="coerce")


def main() -> None:
    from market_sim.data.hydro import _load_hydro_nameplate

    nameplate = _load_hydro_nameplate("NYISO")
    fleet_mw = float(sum(nameplate.values()))

    hil = pd.read_csv(HILARRI, low_memory=False)
    hil["eia_ptid"] = pd.to_numeric(hil["eia_ptid"], errors="coerce")
    hil = hil[hil.eia_ptid.isin(nameplate.keys())][["eia_ptid", "nidid"]].dropna()
    hil["nidid"] = hil.nidid.astype(str).str.strip()

    nid = pd.read_csv(NID, low_memory=False)
    nid["NID ID"] = nid["NID ID"].astype(str).str.strip()
    # A NID ID names a PROJECT, and a project can list several structures -- the
    # St. Lawrence project (NY00678) carries its main dam plus six dikes, and all
    # seven rows repeat the SAME project storage (750,000 / 803,000 acre-ft).
    # So storage must be taken ONCE PER PROJECT (max across its rows, never a sum,
    # which would multiply it by the structure count), while head is the best
    # figure any of the project's structures reports. Collapsing with
    # ``drop_duplicates`` instead keeps an arbitrary first row and silently
    # discards the informative one: it kept "South Forebay Dike" (no hydraulic
    # height) over "Robert Moses - St. Lawrence" (81 ft), putting 19.5 % of fleet
    # MW on the dam-height proxy that did not need it.
    nid = nid.groupby("NID ID").agg(
        {
            "Normal Storage (Acre-Ft)": "max",
            "Max Storage (Acre-Ft)": "max",
            "Hydraulic Height (Ft)": "max",
            "Dam Height (Ft)": "max",
        }
    )

    rows = []
    for plant_id, group in hil.groupby(hil.eia_ptid.astype(int)):
        dams = [d for d in group.nidid.unique() if d in nid.index]
        if not dams:
            continue
        recs = nid.loc[dams]
        pmax = float(nameplate[plant_id])
        if pmax <= 0:
            continue
        # A plant fed by several dams may draw on all of their storage.
        normal = float(_num(recs, "Normal Storage (Acre-Ft)").fillna(0).sum())
        maximum = float(_num(recs, "Max Storage (Acre-Ft)").fillna(0).sum())
        hyd = _num(recs, "Hydraulic Height (Ft)").max()
        dam_h = _num(recs, "Dam Height (Ft)").max()
        head_ft = float(hyd) if pd.notna(hyd) and hyd > 0 else float(dam_h or 0.0)
        head_basis = "hydraulic_height" if pd.notna(hyd) and hyd > 0 else "dam_height_PROXY"
        if head_ft <= 0:
            continue
        rows.append(
            {
                "plant_id": plant_id,
                "pmax_mw": pmax,
                "pct_fleet_mw": 100.0 * pmax / fleet_mw,
                "n_dams": len(dams),
                "normal_storage_acreft": normal,
                "max_storage_acreft": maximum,
                "head_ft": head_ft,
                "head_basis": head_basis,
                "pondage_hours_normal": _MWH_PER_ACREFT_FOOT * normal * head_ft / pmax,
                "pondage_hours_max": _MWH_PER_ACREFT_FOOT * maximum * head_ft / pmax,
            }
        )

    frame = pd.DataFrame(rows).sort_values("pmax_mw", ascending=False)
    covered_mw = float(frame.pmax_mw.sum())

    def mw_share_under(hours: float) -> float:
        """Share of the COVERED MW whose generous bound is under `hours`."""
        hit = frame[frame.pondage_hours_max < hours]
        return round(100.0 * float(hit.pmax_mw.sum()) / covered_mw, 2)

    record = {
        "session": "nyiso-219",
        "charter": "docs/CHARTER-nyiso219-hydro-budget-period-2026-09-07.md",
        "owner_rulings": {
            "Q1": "fund the full intake",
            "Q2": "decide the rule-19 posture at phase 0",
            "Q3": "undecided — measure the shaping horizon, not the Mode label",
        },
        "construction": {
            "upper_bound": True,
            "efficiency_assumed": 1.0,
            "storage_basis": "FULL reservoir volume, NOT the licensed operating "
            "range — the true usable figure is strictly smaller",
            "mwh_per_acreft_foot": round(_MWH_PER_ACREFT_FOOT, 9),
            "free_parameters": 0,
        },
        "coverage": {
            "plants_scored": int(len(frame)),
            "pct_fleet_mw_scored": round(100.0 * covered_mw / fleet_mw, 2),
            "pct_scored_mw_on_hydraulic_height": round(
                100.0
                * float(frame[frame.head_basis == "hydraulic_height"].pmax_mw.sum())
                / covered_mw,
                2,
            ),
        },
        "headline_mw_share_under": {
            f"{name} ({hours:.0f} h)": mw_share_under(hours)
            for name, hours in _PERIOD_HOURS.items()
        },
        "dominant_plants": [
            {
                "plant_id": int(r.plant_id),
                "pmax_mw": round(r.pmax_mw, 1),
                "pct_fleet_mw": round(r.pct_fleet_mw, 2),
                "normal_storage_acreft": round(r.normal_storage_acreft, 1),
                "head_ft": round(r.head_ft, 1),
                "head_basis": r.head_basis,
                "pondage_hours_normal": round(r.pondage_hours_normal, 3),
                "pondage_hours_max": round(r.pondage_hours_max, 3),
            }
            for r in frame.head(6).itertuples()
        ],
        "distribution_pondage_hours_max": {
            "mw_weighted_mean": round(
                float(np.average(frame.pondage_hours_max, weights=frame.pmax_mw)), 3
            ),
            "median_plant": round(float(frame.pondage_hours_max.median()), 3),
            "p90_plant": round(float(frame.pondage_hours_max.quantile(0.90)), 3),
            "max_plant": round(float(frame.pondage_hours_max.max()), 3),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
