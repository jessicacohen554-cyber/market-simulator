"""closeout-PJM-w2 phase 0 — reach of the L3 Elliott event-windowed outage overlay. ZERO LP.

Rule 32 ``[R-SHARD]``: the parent runs no LP. Reads only the PJM keeper's committed
``hourly/`` sidecars (``unit_marginal_2022``, ``system_2022``, ``reserve_family_2022``)
and the measured PJM ``gen_outages_by_type`` daily snapshot (RTO, lead 0), and asks
whether the most favourable admissible overlay form — the EVENT INCREMENT of published
forced outage over its 20–22 Dec 2022 baseline, net of the model's own unavailable-MW
rise, removed from in-LP headroom — can push any Elliott hour into reserve shortage or
up the merit order far enough to reach the plan §3.6 step-4 bar (Dec 23–24 mean
≥ $800/MWh, C3b ≤ 0.20).

Merit-order walk: each hour the increment is withdrawn from the cheapest headroom
first is NOT assumed; instead the residual stack is walked upward from the hour's own
cleared price by the increment MW (units with headroom, sorted by P1 offer ``mc``), so
the reported price is an upper bound of the energy-only move absent shortage.

Record: ``docs/records/pjm/closeout-pjm-w2/FINDING-closeout-pjm-w2-phase0-2026-10-03.md``.
Run: ``PYTHONPATH=. uv run python scripts/probes/_closeoutpjmw2_elliott_overlay_reach.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/closeout_pjm_nuc_full_span/hourly"
OUTAGES = REPO / "data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv"
REAL = REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_closeoutpjmw2_elliott_overlay_reach.json"
THERMAL = ["coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear"]
DOY0_WINDOW = (353, 362)  # 0-indexed day-of-year: 2022-12-20 .. 2022-12-28
BASE_DAYS = (20, 22)  # baseline days (December) for the event increment
EVENT_DAYS = (23, 24)  # plan §3.6 step-4 bar window


def main() -> int:
    """Write the reach JSON and print the day table."""
    u = pd.read_parquet(
        BUNDLE / "unit_marginal_2022.parquet",
        columns=["unit_id", "plant_group", "fuel", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    u = u[
        u.fuel.astype(str).isin(THERMAL)
        & (u.zone.astype(str) != "PJM_external")
        & ~u.plant_group.astype(str).str.startswith("VIRTUAL")
    ]
    inst = u.groupby("unit_id", observed=True).cap_mw.max()
    h0, h1 = DOY0_WINDOW[0] * 24, (DOY0_WINDOW[1] + 1) * 24
    w = u[(u.hour >= h0) & (u.hour < h1)].copy()
    w["unav"] = w.unit_id.map(inst).astype(float) - w.cap_mw
    w["hr"] = w.cap_mw - w.mw
    g = w.groupby("hour").agg(cap=("cap_mw", "sum"), gen=("mw", "sum"), unav=("unav", "sum"))
    g["headroom"] = g.cap - g.gen
    t = pd.Timestamp("2022-01-01") + pd.to_timedelta(g.index, unit="h")
    g["day"] = t.day
    o = pd.read_csv(OUTAGES)
    o = o[(o.region == "PJM RTO") & (o.lead_days == 0)]
    o = o[pd.to_datetime(o.forecast_date).dt.month == 12]
    pub = o.set_index(pd.to_datetime(o.forecast_date).dt.day).forced_outages_mw
    pub = pub[~pub.index.duplicated()]
    g["pub_forced"] = g.day.map(pub).astype(float)
    base = g[(g.day >= BASE_DAYS[0]) & (g.day <= BASE_DAYS[1])]
    g["increment"] = (g.pub_forced - base.pub_forced.mean()) - (g.unav - base.unav.mean())
    g["inc_pos"] = g.increment.clip(lower=0.0)
    g["resid_headroom"] = g.headroom - g.inc_pos

    s = pd.read_parquet(BUNDLE / "system_2022.parquet")
    s = s[(s["pass"] == "P1") & (s.zone.astype(str) != "PJM_external")]
    lw = s.assign(x=s.price * s.demand).groupby("hour")[["x", "demand"]].sum()
    g["price"] = (lw.x / lw.demand).reindex(g.index)
    g["demand"] = lw.demand.reindex(g.index)
    r = pd.read_parquet(BUNDLE / "reserve_family_2022.parquet")
    r = r[(r["pass"] == "P1") & (r.family == "pjm_primary")].groupby("hour").requirement_mw.sum()
    g["req"] = r.reindex(g.index)

    real = pd.read_parquet(REAL)
    real = real[real.year == 2022]
    sz = s.assign(zone=s.zone.astype(str))[["zone", "hour", "demand"]]
    real = real.merge(sz, on=["zone", "hour"])
    act = (real.rt * real.demand).groupby(real.hour).sum() / real.groupby("hour").demand.sum()
    g["actual"] = act.reindex(g.index)

    # Merit-order walk: units with headroom above the hour's cleared price, by mc.
    walk = {}
    for h, d in w[w.hr > 0].groupby("hour"):
        inc = float(g.at[h, "inc_pos"])
        if inc <= 0:
            walk[h] = float(g.at[h, "price"])
            continue
        d = d.sort_values("mc")
        above = d[d.mc >= g.at[h, "price"] - 1e-6]
        c = np.cumsum(above.hr.to_numpy(float))
        k = int(np.searchsorted(c, inc))
        walk[h] = float(above.mc.to_numpy(float)[min(k, len(above) - 1)]) if len(above) else np.nan
    g["walk_price"] = pd.Series(walk)

    ev = g[(g.day >= EVENT_DAYS[0]) & (g.day <= EVENT_DAYS[1])]
    day = g.groupby("day").agg(
        pub_forced=("pub_forced", "mean"),
        model_unav_mean=("unav", "mean"),
        increment_mean=("increment", "mean"),
        headroom_min=("headroom", "min"),
        resid_headroom_min=("resid_headroom", "min"),
        price_max=("price", "max"),
        walk_price_max=("walk_price", "max"),
        actual_max=("actual", "max"),
    )
    rec = {
        "probe": "closeout-PJM-w2 L3 Elliott overlay reach (zero LP)",
        "keeper": "2026-10-03-closeout-pjm-nuc-keeper",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "overlay_form": "event increment: (pub forced - mean(20-22 Dec)) - (model unav - mean(20-22 Dec)), clipped >= 0, removed from in-LP thermal headroom",
        "bar_plan_step4": "Dec 23-24 mean price >= $800/MWh; C3b <= 0.20",
        "hours_window": int(len(g)),
        "hours_resid_below_primary_req": int((g.resid_headroom < g.req).sum()),
        "hours_resid_below_req_plus_190": int((g.resid_headroom < g.req + 190).sum()),
        "hours_resid_below_zero": int((g.resid_headroom < 0).sum()),
        "min_resid_headroom_mw": round(float(g.resid_headroom.min()), 0),
        "event_mean_model_price": round(float(ev.price.mean()), 2),
        "event_mean_walk_price_upper_bound": round(float(ev.walk_price.mean()), 2),
        "event_mean_actual_zonal_rt": round(float(ev.actual.mean()), 2),
        "event_hours_actual_ge_800": int((ev.actual >= 800).sum()),
        "verdict": None,
        "by_day": {int(k): {c: round(float(v), 1) for c, v in row.items()} for k, row in day.iterrows()},
    }
    # Ceiling: C3a/C3b 2022 on the zonal load-weighted basis with Elliott (23-26 Dec) removed.
    full = s.assign(zone=s.zone.astype(str)).merge(
        pd.read_parquet(REAL).query("year == 2022")[["zone", "hour", "rt"]], on=["zone", "hour"]
    )
    yr = full.assign(x=full.price * full.demand, a=full.rt * full.demand).groupby("hour")[["x", "a", "demand"]].sum()
    ty = pd.Timestamp("2022-01-01") + pd.to_timedelta(yr.index, unit="h")
    yr["m"], yr["doy"] = ty.month, ty.dayofyear

    def c3(d: pd.DataFrame) -> tuple[float, float]:
        mm = d.groupby("m")[["x", "a", "demand"]].sum()
        pm, am = mm.x / mm.demand, mm.a / mm.demand
        return (
            round(100 * (d.x.sum() / d.a.sum() - 1), 2),
            round(float(np.sqrt(((pm - am) ** 2).mean()) / am.mean()), 3),
        )

    ell = (yr.doy >= 357) & (yr.doy <= 360)
    rec["c3a_c3b_2022_all"] = c3(yr)
    rec["c3a_c3b_2022_ex_elliott"] = c3(yr[~ell])
    rec["verdict"] = (
        "CLEARS" if rec["event_mean_walk_price_upper_bound"] >= 800 or rec["hours_resid_below_primary_req"] > 0
        else "NOT CHARTERED (no shortage hour; merit-order upper bound below the $800 bar)"
    )
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(day.round(0).to_string())
    print({k: v for k, v in rec.items() if k != "by_day"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
