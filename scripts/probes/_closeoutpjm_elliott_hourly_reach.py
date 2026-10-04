"""closeout-PJM-elliott phase 0 — reach of the hourly measured Elliott outage overlay. ZERO LP.

Owner ruling R-64 (2026-10-04): PJM's Winter Storm Elliott Event Analysis hourly
forced-outage profile (Figure 30, GADS, digitised by
``scripts/data/digitise_pjm_elliott_forced_outages.py``) is admissible as a windowed
measured backcast outage overlay. This probe reads only the PJM keeper's committed
``hourly/`` sidecars and that raw CSV and asks what the overlay can reach before any
build: per event hour, the measured rise over a pre-event baseline net of the model's
own unavailable-MW rise is withdrawn from in-LP thermal headroom; the hour's price is
then estimated from the keeper's own stack and the PJM reserve curve the LP carries
(``pjm_ordc_curve.csv`` $850 / $300 steps; VOLL from the PJM ISOConfig).

Two baselines (declared in the PRECOMMIT before the numbers): A (desk form) — the
published eDART RTO forced-outage daily snapshot, 20–22 Dec mean, against the model's
20–22 Dec mean; B (same-source) — the figure's own pre-front bars 23 Dec 00:00–04:00
against the model's same hours.

Record: ``docs/records/pjm/closeout-pjm-elliott/``.
Run: ``PYTHONPATH=. uv run python scripts/probes/_closeoutpjm_elliott_hourly_reach.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/closeout_pjm_nuc_full_span/hourly"
FIG = REPO / "data/raw/pjm-elliott-forced-outages/figure30_digitised.csv"
EDART = REPO / "data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv"
REAL = REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_elliott_hourly_reach.json"
THERMAL = ["coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear"]
STEP1, STEP2, STEP2_WIDTH = 850.0, 300.0, 190.0  # pjm_ordc_curve.csv (M11 §4.3.3)
DEC23_ROW = 356 * 24  # 0-indexed doy 356 = 23 Dec 2022; row = doy0*24 + hour-beginning


def _voll() -> float:
    """PJM VOLL from the ISO config (no literal)."""
    from market_sim.config.iso_configs import get_iso_config

    return float(get_iso_config("PJM").voll)


FUEL_GROUPS = {
    "gas": ("gas_cc", "gas_ct", "gas_st"),
    "coal": ("coal",),
    "oil": ("oil",),
    "nuclear": ("nuclear",),
}


def measured_hourly(fuel: str | None = None) -> pd.Series:
    """Hourly GADS forced outage (MW) on model rows, 23 Dec 00:00 .. 25 Dec 23:00.

    ``fuel=None`` is the bar total; otherwise that fuel's digitised segment.
    Odd hours are linearly interpolated; 25 Dec 23:00 holds 22:00.
    """
    f = pd.read_csv(FIG)
    if fuel is None:
        f = f.drop_duplicates("hour_beginning_ept").assign(v=lambda d: d.bar_total_mw)
    else:
        f = f[f.fuel == fuel].assign(v=lambda d: d.forced_outage_mw)
    t = pd.to_datetime(f.hour_beginning_ept)
    rows = DEC23_ROW + ((t - pd.Timestamp("2022-12-23")) / pd.Timedelta("1h")).astype(
        int
    )
    s = pd.Series(f.v.to_numpy(float), index=rows.to_numpy())
    full = pd.Series(np.nan, index=np.arange(DEC23_ROW, DEC23_ROW + 72))
    full.loc[s.index] = s.to_numpy()
    return full.interpolate(limit_area="inside").ffill()


def main() -> int:
    """Write the reach JSON and print the headline."""
    u = pd.read_parquet(
        BUNDLE / "unit_marginal_2022.parquet",
        columns=[
            "unit_id",
            "plant_group",
            "fuel",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    u = u[
        u.fuel.astype(str).isin(THERMAL)
        & (u.zone.astype(str) != "PJM_external")
        & ~u.plant_group.astype(str).str.startswith("VIRTUAL")
    ]
    inst = u.groupby("unit_id", observed=True).cap_mw.max()
    w = u[(u.hour >= 353 * 24) & (u.hour < 360 * 24)].copy()  # 20..26 Dec
    w["unav"] = w.unit_id.map(inst).astype(float) - w.cap_mw
    w["hr"] = w.cap_mw - w.mw
    g = w.groupby("hour").agg(
        cap=("cap_mw", "sum"), gen=("mw", "sum"), unav=("unav", "sum")
    )
    g["headroom"] = g.cap - g.gen
    fuel_unav = {
        k: w[w.fuel.astype(str).isin(v)].groupby("hour").unav.sum()
        for k, v in FUEL_GROUPS.items()
    }

    s = pd.read_parquet(BUNDLE / "system_2022.parquet")
    s = s[(s["pass"] == "P1") & (s.zone.astype(str) != "PJM_external")].assign(
        zone=lambda d: d.zone.astype(str)
    )
    r = pd.read_parquet(BUNDLE / "reserve_family_2022.parquet")
    req = (
        r[(r["pass"] == "P1") & (r.family == "pjm_primary")]
        .groupby("hour")
        .requirement_mw.sum()
    )

    meas = measured_hourly()
    ev = meas.index
    e = pd.read_csv(EDART)
    e = e[(e.region == "PJM RTO") & (e.lead_days == 0)]
    e = e[pd.to_datetime(e.forecast_date).between("2022-12-20", "2022-12-22")]
    base_rows_a = range(353 * 24, 356 * 24)
    base_rows_b = range(DEC23_ROW, DEC23_ROW + 5)
    baselines = {
        "A_desk_edart_20_22": (
            float(e.forced_outages_mw.mean()),
            float(g.unav.loc[base_rows_a].mean()),
        ),
        "B_same_source_23dec_00_04": (
            float(meas.loc[base_rows_b].mean()),
            float(g.unav.loc[base_rows_b].mean()),
        ),
    }

    real = (
        pd.read_parquet(REAL)
        .query("year == 2022")[["zone", "hour", "rt"]]
        .merge(s[["zone", "hour", "demand", "price"]], on=["zone", "hour"])
    )
    yr = (
        real.assign(x=real.price * real.demand, a=real.rt * real.demand)
        .groupby("hour")[["x", "a", "demand"]]
        .sum()
    )
    yr["m"] = (pd.Timestamp("2022-01-01") + pd.to_timedelta(yr.index, unit="h")).month

    def c3(d: pd.DataFrame) -> list[float]:
        mm = d.groupby("m")[["x", "a", "demand"]].sum()
        pm, am = mm.x / mm.demand, mm.a / mm.demand
        return [
            round(100 * (d.x.sum() / d.a.sum() - 1), 2),
            round(float(np.sqrt(((pm - am) ** 2).mean()) / am.mean()), 3),
        ]

    voll = _voll()
    rec = {
        "probe": "closeout-PJM-elliott hourly measured outage overlay reach (zero LP)",
        "keeper": "2026-10-03-closeout-pjm-nuc-keeper",
        "measured": str(FIG.relative_to(REPO)),
        "event_hours": [int(ev[0]), int(ev[-1])],
        "voll": voll,
        "c3a_c3b_2022_keeper": c3(yr),
        "variants": {},
    }
    hr_units = w[w.hr > 0]
    incs = {
        name: ((meas - pub0) - (g.unav.reindex(ev) - mod0)).clip(lower=0.0)
        for name, (pub0, mod0) in baselines.items()
    }
    # C: the build form — fuel grain, same-source baseline (23 Dec 00:00-04:00).
    inc_c = 0.0
    for k in FUEL_GROUPS:
        m = measured_hourly(k)
        mu = fuel_unav[k].reindex(g.index)
        inc_c = inc_c + (
            (m - m.loc[base_rows_b].mean())
            - (mu.reindex(ev) - mu.loc[base_rows_b].mean())
        ).clip(lower=0.0)
    incs["C_fuel_grain_same_source"] = inc_c
    baselines["C_fuel_grain_same_source"] = baselines["B_same_source_23dec_00_04"]
    for name, inc in incs.items():
        pub0, mod0 = baselines[name]
        resid = g.headroom.reindex(ev) - inc
        sysp = (yr.x / yr.demand).reindex(ev)
        est = {}
        for h in ev:
            d = hr_units[hr_units.hour == h].sort_values("mc")
            above = d[d.mc >= sysp[h] - 1e-6]
            c = np.cumsum(above.hr.to_numpy(float))
            k = int(np.searchsorted(c, inc[h]))
            walk = (
                float(above.mc.to_numpy(float)[min(k, len(above) - 1)])
                if len(above)
                else float(sysp[h])
            )
            q = float(req.get(h, 0.0))
            if resid[h] < 0:
                p = voll
            elif resid[h] < q:
                p = min(voll, walk + STEP1)
            elif resid[h] < q + STEP2_WIDTH:
                p = min(voll, walk + STEP2)
            else:
                p = walk
            est[h] = max(p, float(sysp[h]))
        est = pd.Series(est)
        cf = yr.copy()
        cf.loc[ev, "x"] = est.to_numpy() * cf.loc[ev, "demand"].to_numpy()
        d2324 = ev[(ev >= DEC23_ROW) & (ev < DEC23_ROW + 48)]
        rec["variants"][name] = {
            "baseline_pub_mw": round(pub0, 0),
            "baseline_model_unav_mw": round(mod0, 0),
            "increment_max_mw": round(float(inc.max()), 0),
            "increment_mean_23_24_mw": round(float(inc.loc[d2324].mean()), 0),
            "hours_resid_lt_0": int((resid < 0).sum()),
            "hours_resid_lt_req": int((resid < req.reindex(ev).fillna(0)).sum()),
            "hours_resid_lt_req_plus_190": int(
                (resid < req.reindex(ev).fillna(0) + STEP2_WIDTH).sum()
            ),
            "min_resid_headroom_mw": round(float(resid.min()), 0),
            "dec23_24_mean_est_price": round(
                float(np.average(est.loc[d2324], weights=yr.demand.loc[d2324])), 2
            ),
            "dec23_24_mean_actual": round(
                float(yr.a.loc[d2324].sum() / yr.demand.loc[d2324].sum()), 2
            ),
            "c3a_c3b_2022_est": c3(cf),
            "est_unserved_mwh_upper": round(float((-resid).clip(lower=0).sum()), 0),
        }
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
