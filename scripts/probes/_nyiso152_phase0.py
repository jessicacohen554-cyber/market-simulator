#!/usr/bin/env python3
"""nyiso-152 phase-0: measure what actually holds Allegany (7784) on, from committed artifacts.

Owner charter (nyiso-151 sitting, 2026-08-22): before any RAMP10-seams arm is
designed, phase-0 must (a) measure which reserve family binds in Allegany's
mid-load hours, (b) establish whether a hydro deliverability envelope or a
nyca/east 10-min family drives the demand, and (c) settle whether the hydro
RAMP10 seams as recorded are even the right repair, given the discovery that
NYISO's default reserve path is class-level headroom rows with no ramp10
filter.

Everything here reads the COMMITTED nyiso151_armHC (bit-identical to the
registered 2026-08-22-nyiso-150-reserve-rearm) and nyiso151_control
(bit-identical to the keeper 2026-08-22-nyiso-151-identity-hr) bundles — no
solve, no holdout spend (years 2023-2025 only).

Structural facts this probe quantifies against (verified at HEAD, cited in the
finding doc):

* reserve_rows._build_reserve_rows: non-gated shared headroom is
  ``sum P + R[c,z] <= sum cap`` per (class, zone, hour) — IDLE capacity backs
  reserve; online output only CONSUMES headroom. Reserve demand cannot hold a
  unit on in this design.
* spec.QUICK_START_FUEL_TYPES = {gas_ct, oil}: a gas CC is not class-1
  (10-minute) eligible at all; with nyiso_hydro_reserve_eligible armed, hydro
  joins BOTH classes at full cap*avail headroom (no ramp10 term anywhere).
* floors npz mechanism 20 = MECH_NYISO_GAS_COMMITMENT_BRIDGE.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "results" / "calibration"
OUT = RES / "_nyiso152_phase0.json"

PLANT = 7784  # Allegany (EIA); eGRID 10619 — the nyiso-151 identity pair
UNIT = "CC_REGULAR_Upstate_West_p7784_peak"
ZONE = "Upstate_West"
YEARS = (2023, 2024, 2025)
# Quick-start (class-1) fuels per model/reserves/spec.py; hydro joins via the
# armed nyiso_hydro_reserve_eligible union. Storage backs every class.
CLASS1_FUELS = {"gas_ct", "oil", "hydro"}
FLOOR_TOL_MW = 0.05  # |mw - min_gen| below this = riding the floor
MID_LO, MID_HI = 5.0, 45.0  # the nyiso-151 SS3 "mid-load" band
DUAL_TOL = 1e-6


def allegany_year(bundle: Path, year: int) -> dict:
    """Measure Allegany's dispatch/floor/reserve coincidence for one year."""
    fl = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
    i = np.flatnonzero(fl["plant_code"] == PLANT)
    assert len(i) >= 1, (bundle, year)
    # Plant-level: sum floors across the plant's LP tranches (the armHC duty
    # split routes everything to one `_peak` unit; the control keeps the
    # normal tranche split).
    min_gen = fl["min_gen"][i].astype(float).sum(axis=0)  # (8760,)
    mech = fl["mechanism"][i].max(axis=0)
    unit_ids = fl["unit_ids"][i].tolist()

    uh = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        filters=[("plant_code", "==", PLANT)],
    )
    by_h = uh.groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
    mw = by_h["mw"].to_numpy(dtype=float)
    cap = by_h["cap_mw"].to_numpy(dtype=float)
    T = len(mw)

    on = mw > 1e-3
    floored = min_gen > 0.0
    riding = floored & (np.abs(mw - min_gen) <= FLOOR_TOL_MW)
    above = on & ~riding
    mid = on & (mw >= MID_LO) & (mw <= MID_HI)
    full = on & (mw > MID_HI)

    # Which reserve families have a positive balance dual in Allegany's hours?
    rf = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"] if "pass" in rf.columns else rf
    fam_rows = {}
    for fam, g in rf.groupby("family"):
        g = g.sort_values("hour")
        dual = g["dual"].to_numpy(dtype=float)
        short = g["shortfall_mw"].to_numpy(dtype=float)
        assert len(dual) == T, (fam, len(dual))
        pos = dual > DUAL_TOL
        fam_rows[fam] = {
            "zones": g["zones"].iloc[0],
            "reserve_class": (
                int(g["reserve_class"].iloc[0])
                if "reserve_class" in g.columns
                else None
            ),
            "dual_pos_hours": int(pos.sum()),
            "dual_pos_in_riding": int((pos & riding).sum()),
            "dual_pos_in_above_floor_on": int((pos & above).sum()),
            "dual_pos_in_mid": int((pos & mid).sum()),
            "shortfall_hours": int((short > 1e-3).sum()),
            "mean_dual_when_pos": float(dual[pos].mean()) if pos.any() else 0.0,
        }

    return {
        "lp_units": unit_ids,
        "hours": {
            "on": int(on.sum()),
            "mid_load_5_45": int(mid.sum()),
            "full_gt45": int(full.sum()),
            "floored": int(floored.sum()),
            "floor_riding": int(riding.sum()),
            "riding_and_mid": int((riding & mid).sum()),
            "mid_not_floored": int((mid & ~floored).sum()),
            "above_floor_on": int(above.sum()),
        },
        "floor_mech_codes": sorted(set(mech[floored].tolist())),
        "min_gen_range_mw": (
            [float(min_gen[floored].min()), float(min_gen[floored].max())]
            if floored.any()
            else None
        ),
        "energy_gwh": {
            "total": float(mw.sum() / 1e3),
            "floor_riding": float(mw[riding].sum() / 1e3),
            "above_floor": float(mw[above].sum() / 1e3),
        },
        "cap_mw_range": [float(cap.min()), float(cap.max())],
        "families": fam_rows,
    }


def zone_class1_headroom(bundle: Path, year: int, riding: np.ndarray) -> dict:
    """Class-1 (10-min) eligible cap vs dispatch in Allegany's zone.

    Measures headroom abundance from unit_hourly (thermal quick-start + hydro;
    storage is additionally class-eligible, so this UNDERSTATES supply).
    """
    uh = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        filters=[("zone", "==", ZONE)],
        columns=["unit_id", "fuel", "hour", "mw", "cap_mw"],
    )
    q = uh[uh["fuel"].isin(sorted(CLASS1_FUELS))]
    by_h = q.groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
    head = (by_h["cap_mw"] - by_h["mw"]).to_numpy(dtype=float)
    hyd = q[q["fuel"] == "hydro"].groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
    hyd_head = (hyd["cap_mw"] - hyd["mw"]).to_numpy(dtype=float)
    return {
        "class1_elig_cap_mean_mw": float(by_h["cap_mw"].mean()),
        "class1_headroom_mw": {
            "min": float(head.min()),
            "p05": float(np.percentile(head, 5)),
            "mean": float(head.mean()),
        },
        "class1_headroom_in_riding_min_mw": (
            float(head[riding].min()) if riding.any() else None
        ),
        "hydro_headroom_mw": {
            "min": float(hyd_head.min()),
            "mean": float(hyd_head.mean()),
        },
    }


def main() -> None:
    out: dict = {"probe": "nyiso152_phase0", "plant": PLANT, "unit": UNIT}
    for tag, bundle in (
        ("armHC", RES / "nyiso151_armHC"),
        ("control", RES / "nyiso151_control"),
    ):
        per_year = {}
        for y in YEARS:
            rec = allegany_year(bundle, y)
            # Recompute the riding mask for the headroom cross.
            fl = np.load(bundle / "floors" / f"{y}_P1.npz", allow_pickle=True)
            i = np.flatnonzero(fl["plant_code"] == PLANT)
            min_gen = fl["min_gen"][i].astype(float).sum(axis=0)
            uh = pd.read_parquet(
                bundle / "hourly" / f"unit_hourly_{y}.parquet",
                filters=[("plant_code", "==", PLANT)],
                columns=["hour", "mw"],
            )
            mw = uh.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)
            riding = (min_gen > 0) & (np.abs(mw - min_gen) <= FLOOR_TOL_MW)
            rec["zone_class1"] = zone_class1_headroom(bundle, y, riding)
            per_year[str(y)] = rec
        out[tag] = per_year
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
