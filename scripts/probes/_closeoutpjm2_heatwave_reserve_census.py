"""closeout-PJM-2 step 4 (ZERO LP): June 23-25 2025 heat-wave reserve-scarcity census.

Readings pre-fixed in ``docs/records/pjm/PRECOMMIT-closeout-pjm-2-heatwave-reserve-census-2026-10-03.md``
(committed at 75c888f5 before this probe ran). Keeper ``w0_pjm_span``, 2025 leg.

* ``G(h)``: requirement-net model reserve headroom, Σ_pool min(cap_mw − mw, ramp10) − Σ requirement_mw;
  pool = ``RESERVE_FUEL_TYPES`` with ``ramp10 > 0`` (``model/reserves/spec.py``), from a fleet_only
  rebuild (w0 posture) joined to the committed ``unit_marginal_2025``.
* ``U_m(d)``: model unavailable MW (Σ pmax − cap_mw, thermal + nuclear + hydro) mean over the window hours.
* ``U_p(d)``: PJM ``gen_outages_by_type`` RTO lead-0 total (forced + maintenance + planned).
* R1 near-binding (median G over H* ≤ 2,000 MW); R2 availability CONFIRMED iff ΔU(d) ≥ G(h) in ≥ 50 %
  of H*; R3 offline / CT+oil share of the headroom (reported).

Writes ``results/phase0/pjm/_closeoutpjm2_heatwave_reserve_census.json``.
Run: ``.venv/bin/python scripts/probes/_closeoutpjm2_heatwave_reserve_census.py``
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

YEAR = 2025
BUNDLE = REPO / "results/calibration/w0_pjm_span"
DAYS = {"2025-06-23": 4152, "2025-06-24": 4176, "2025-06-25": 4200}
WINDOW = [
    d0 + h for d0 in DAYS.values() for h in range(12, 23)
]  # 12:00-22:00, 33 hours
REAL_HI = 400.0  # $/MWh, H* threshold (PRECOMMIT)
NEAR_BINDING_MW = 2000.0  # R1
UNAVAIL_FUELS = {"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil", "hydro"}
OUT = REPO / "results/phase0/pjm/_closeoutpjm2_heatwave_reserve_census.json"


def fleet() -> pd.DataFrame:
    """Per-unit pool membership, ramp10 and pmax from a fleet_only rebuild of the keeper's 2025 recipe."""
    logging.disable(logging.WARNING)
    from market_sim.model.reserves.spec import FUEL_TYPE_NAMES, RESERVE_FUEL_TYPES
    from scripts.build_fleet_census import rebuild_fleet

    r = rebuild_fleet(BUNDLE, YEAR, "w0", {"pjm_da_virtual_bids": False})
    fa = r["fleet_arrays"]
    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    ramp10 = np.asarray(fa.ramp10, dtype=float)
    return pd.DataFrame(
        {
            "unit_id": np.asarray(fa.unit_ids).astype(str),
            "fuel_fa": fuel,
            "group": np.asarray(fa.plant_group).astype(str),
            "pmax": np.asarray(fa.pmax, dtype=float),
            "ramp10": ramp10,
            "pool": np.isin(fuel, sorted(RESERVE_FUEL_TYPES)) & (ramp10 > 0.0),
        }
    )


def main() -> int:
    """Compute the census and write the JSON record."""
    f = fleet()
    um = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{YEAR}.parquet",
        columns=["hour", "unit_id", "mw", "cap_mw"],
        filters=[("hour", "in", WINDOW)],
    )
    um["unit_id"] = um.unit_id.astype(str)
    m = um.merge(f, on="unit_id", how="left")
    unmatched = float(m[m.fuel_fa.isna()].cap_mw.sum() / len(WINDOW))
    m = m[m.fuel_fa.notna()].copy()
    m["head"] = np.where(
        m["pool"].astype(bool),
        np.minimum(m.cap_mw - m.mw, m.ramp10).clip(lower=0.0),
        0.0,
    )
    m["offline"] = m.mw <= 0.5
    m["ctoil"] = m.group.isin(["CT_PEAKER", "CT_CHP"]) | (m.fuel_fa == "oil")
    m["unav"] = np.where(
        m.fuel_fa.isin(UNAVAIL_FUELS), (m.pmax - m.cap_mw).clip(lower=0.0), 0.0
    )

    rf = pd.read_parquet(BUNDLE / f"hourly/reserve_family_{YEAR}.parquet")
    rf = rf[(rf["pass"].astype(str) == "P1") & rf.hour.isin(WINDOW)]
    req = rf.groupby("hour").requirement_mw.sum()
    dual = rf.groupby("hour").dual.max()

    g = m.groupby("hour")
    head = g["head"].sum()
    G = head - req.reindex(head.index)
    U_m = g["unav"].sum()

    s = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    s = s[(s.zone.astype(str) != "PJM_external") & s.hour.isin(WINDOW)]
    z = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet"
    )
    z = z[(z.year == YEAR) & z.hour.isin(WINDOW)].merge(
        s.assign(zone=s.zone.astype(str))[["zone", "hour", "demand"]],
        on=["zone", "hour"],
    )
    real = (
        z.assign(x=z.rt * z.demand).groupby("hour").x.sum()
        / z.groupby("hour").demand.sum()
    )
    model = (
        s.assign(x=s.price * s.demand).groupby("hour").x.sum()
        / s.groupby("hour").demand.sum()
    )
    hstar = [h for h in WINDOW if real.get(h, 0.0) >= REAL_HI]

    po = pd.read_csv(
        REPO / f"data/raw/pjm-outages/by-year/gen_outages_by_type_{YEAR}.csv"
    )
    po = po[
        (po.lead_days == 0)
        & (po.region == "PJM RTO")
        & po.forecast_date.isin(list(DAYS))
    ]
    U_p = po.set_index("forecast_date")
    day_of = {h: d for d, d0 in DAYS.items() for h in range(d0, d0 + 24)}
    rows = []
    for h in WINDOW:
        d = day_of[h]
        um_d = float(U_m[[x for x in WINDOW if day_of[x] == d]].mean())
        up_d = float(U_p.loc[d, "total_outages_mw"])
        rows.append(
            {
                "hour": h,
                "ts": str(pd.Timestamp(f"{YEAR}-01-01") + pd.Timedelta(hours=h)),
                "real_rt": round(float(real.get(h, np.nan)), 1),
                "model_price": round(float(model.get(h, np.nan)), 1),
                "reserve_dual": float(dual.get(h, np.nan)),
                "requirement_mw": round(float(req.get(h, np.nan)), 0),
                "pool_headroom_mw": round(float(head[h]), 0),
                "G_mw": round(float(G[h]), 0),
                "U_m_day_mw": round(um_d, 0),
                "U_p_day_mw": up_d,
                "dU_day_mw": round(up_d - um_d, 0),
                "in_Hstar": h in hstar,
            }
        )
    t = pd.DataFrame(rows)
    ts = t[t.in_Hstar]
    hs = m[m.hour.isin(hstar)]
    tot = float(hs["head"].sum())
    r2_hits = int((ts.dU_day_mw >= ts.G_mw).sum())
    rec = {
        "window_hours": len(WINDOW),
        "hstar_hours": len(hstar),
        "unmatched_cap_mw_mean": round(unmatched, 1),
        "published_by_day": {
            d: {
                k: float(U_p.loc[d, k])
                for k in (
                    "total_outages_mw",
                    "planned_outages_mw",
                    "maintenance_outages_mw",
                    "forced_outages_mw",
                )
            }
            for d in DAYS
        },
        "R1": {
            "G_min": float(ts.G_mw.min()),
            "G_median": float(ts.G_mw.median()),
            "G_max": float(ts.G_mw.max()),
            "near_binding": bool(ts.G_mw.median() <= NEAR_BINDING_MW),
        },
        "R2": {
            "hits": r2_hits,
            "of": len(ts),
            "confirmed": bool(len(ts) and r2_hits / len(ts) >= 0.5),
            "dU_by_day": {
                d: float(t[t.ts.str.startswith(d)].dU_day_mw.iloc[0]) for d in DAYS
            },
        },
        "R3": {
            "offline_share": round(float(hs.loc[hs.offline, "head"].sum() / tot), 3)
            if tot
            else None,
            "ct_oil_share": round(float(hs.loc[hs.ctoil, "head"].sum() / tot), 3)
            if tot
            else None,
            "offline_ct_oil_share": round(
                float(hs.loc[hs.offline & hs.ctoil, "head"].sum() / tot), 3
            )
            if tot
            else None,
        },
        "hours": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if k != "hours"}, indent=1))
    print(t.to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
