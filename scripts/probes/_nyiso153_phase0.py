#!/usr/bin/env python3
"""nyiso-153 phase-0: would the in-city commitment obligation bind or flood?

Measures, on the COMMITTED keeper bundle (`nyiso152_armSE` ≡
`2026-08-22-nyiso-152-duty-complete`), what arming
``nyiso_incity_commitment_obligation`` (measured rho 0.3014, admissible since
the RHO_CLIP ruling) would demand of the keeper's own dispatch:

1. **Deficit incidence** — hours where ``rho × ΣP(in-pocket obligation
   fleet)`` < the family requirement (`nyc_10min_total` / `li_10min_total`,
   the two families the flag re-classes to the online-gated class 2, whose
   row counts ONLY online output — no idle credit, no storage,
   `reserve_rows.py` gated branch).
2. **Inducement arithmetic** — the gated row's only commitment channel is the
   effective-offer subsidy ``rho × μ_fam``, and μ_fam is capped by the NYC
   RCPF's published flat $25 band (`nyiso_nyc_rcpf_step_curve`, armed) — so
   the maximum inducement is ``0.3014 × 25 ≈ $7.53/MWh``. Per unit, the
   revealed offer proxy is the 5th percentile of its zone LMP over its own
   on-hours; capacity is "flippable" in an hour if it is offline and the zone
   LMP is within the subsidy of that threshold. The gate-relevant statistic:
   in how many deficit hours does flippable capacity cover the additional
   online MW the requirement needs (``req/rho − ΣP``)?

No solve, no holdout spend (2023–2025 only). Output:
``results/calibration/_nyiso153_phase0.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
B = ROOT / "results" / "calibration" / "nyiso152_armSE"
OUT = ROOT / "results" / "calibration" / "_nyiso153_phase0.json"

RHO = 0.301384269761953  # campd_online_reserve_rho_NYISO.csv, incity_obligation
NYC_RCPF = 25.0  # published NYC flat band (nyiso_nyc_rcpf_step_curve)
SUBSIDY = RHO * NYC_RCPF
YEARS = (2023, 2024, 2025)
FAMILIES = (("NYC", "nyc_10min_total"), ("Long_Island", "li_10min_total"))
MIN_ON_HOURS = 20  # below this a unit's revealed offer is unidentifiable


def zone_year(uh: pd.DataFrame, lmp: np.ndarray, req: float, zone: str) -> dict:
    """Deficit + flippable-capacity statistics for one (zone, year)."""
    z = uh[uh["zone"] == zone]
    on_p = (
        z.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0).to_numpy()
    )
    deficit = RHO * on_p < req
    need = np.maximum(0.0, req / RHO - on_p)

    flip_mw = np.zeros(8760)
    unknown_mw = np.zeros(8760)
    for _, g in z.groupby("unit_id"):
        g = g.sort_values("hour")
        mw = g["mw"].to_numpy(dtype=float)
        cap = g["cap_mw"].to_numpy(dtype=float)
        off = mw <= 1e-3
        on = ~off
        if on.sum() < MIN_ON_HOURS:
            unknown_mw += np.where(off, cap, 0.0)
            continue
        thr = float(np.percentile(lmp[on], 5))
        flip_mw += np.where(off & (lmp >= thr - SUBSIDY), cap, 0.0)

    d = np.flatnonzero(deficit)
    closed = flip_mw[d] >= need[d]
    return {
        "requirement_mw": req,
        "online_p_mw": {
            "p10": float(np.percentile(on_p, 10)),
            "p50": float(np.percentile(on_p, 50)),
            "p90": float(np.percentile(on_p, 90)),
        },
        "deficit_hours": int(deficit.sum()),
        "need_online_mw_p50": float(np.percentile(need[d], 50)) if len(d) else 0.0,
        "flippable_mw_p50": float(np.percentile(flip_mw[d], 50)) if len(d) else 0.0,
        "deficit_hours_closable": int(closed.sum()),
        "closable_frac": float(closed.mean()) if len(d) else 0.0,
        "unknown_offer_mw_p50": (
            float(np.percentile(unknown_mw[d], 50)) if len(d) else 0.0
        ),
    }


def main() -> None:
    out: dict = {
        "probe": "nyiso153_phase0",
        "bundle": B.name,
        "rho": RHO,
        "max_inducement_per_mwh": SUBSIDY,
        "years": {},
    }
    for year in YEARS:
        rf = pd.read_parquet(B / "hourly" / f"reserve_family_{year}.parquet")
        rf = rf[rf["pass"] == "P1"]
        sysdf = pd.read_parquet(B / "hourly" / f"system_{year}.parquet")
        sysdf = sysdf[sysdf["pass"] == "P1"]
        lmp = {
            z: g.sort_values("hour")["price"].to_numpy()
            for z, g in sysdf.groupby("zone")
        }
        uh = pd.read_parquet(
            B / "hourly" / f"unit_hourly_{year}.parquet",
            columns=[
                "pass", "zone", "fuel", "plant_group", "unit_id", "hour", "mw",
                "cap_mw",
            ],
            filters=[("pass", "==", "P1")],
        )
        ob = uh[
            (uh["fuel"].isin(["gas_ct", "oil"])) | (uh["plant_group"] == "ST_GAS")
        ]
        yr = {}
        for zone, fam in FAMILIES:
            g = rf[rf["family"] == fam]
            req = float(g["requirement_mw"].mean())
            rec = zone_year(ob, lmp[zone], req, zone)
            rec["family"] = fam
            rec["family_dual_pos_hours_today"] = int((g["dual"] > 1e-6).sum())
            yr[zone] = rec
        out["years"][str(year)] = yr
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
