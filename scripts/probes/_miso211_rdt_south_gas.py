"""miso-211 follow-up 2 — the South gas gap: UNAVAILABLE or PRICED OUT? (disclosed, post-hoc)

The corrected R-2b (``_miso211_rdt_followup.py``) puts the model's South
shortfall in the real S->N binding hours on GAS (-3.3 GW in 2025; -3.2 / -2.7
in 2024 / 2023). Before the successor is named this asks the one question that
decides its kind: in those hours, does the model's South gas fleet have the
CAPABILITY to run at the measured 18.9 GW (then the gap is COST: the marginal
South gas is offered above the model's South price), or not (then it is
AVAILABILITY, the miso-186 class)?

Reads the keeper's own fleet chain (``build_year``: availability-derated pmax
and the bid basis ``mc``), the zone-resolved dispatch parquet, and the
regional sr_gfm Gas series. Recorded under ``post_hoc.south_gas`` in the
miso-211 JSON. No threshold; nothing armed.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso211_rdt_south_gas.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso211_rdt_binding_state as p  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402

HOURS = p.HOURS
GAS = set(p.GAS_CLASSES)


def main() -> None:
    rec = json.loads(p.OUT.read_text())
    cfg0 = keeper_config()
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    out: dict = {
        "disclosure": (
            "Post-hoc, computed after the first pass and the R-2b correction; asks whether "
            "the South gas shortfall in the real S->N binding hours is availability or cost. "
            "No threshold; nothing armed."
        ),
        "years": {},
    }
    for year in p.YEARS:
        ind_act, south_act = p.actual_hubs(year)
        price, lw, _dem_s, _slack = p.zone_prices(year)
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        pops = {"SHOULDER": shoulder, "TAIL": tail}

        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, dtype=np.float64)
        labels = np.array([p.m207.class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        cap = np.asarray(arrays.pmax, dtype=np.float64)[:, None] * avail
        sel = (zones == "MISO-South") & np.isin(labels, list(GAS))
        cap_s_gas = cap[sel]  # (n_units, HOURS)
        mc_s_gas = mc[sel]
        south_price = price["MISO-South"].to_numpy()

        d = pd.read_parquet(
            p.KEEPER / f"dispatch/{year}_P1.parquet",
            columns=["klass", "zone", "hour", "mw"],
        )
        d = d[(d["zone"] == "MISO-South") & d["klass"].astype(str).isin(GAS)]
        disp_gas = (
            d.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy()
        )
        meas_gas = p.regional_series(year, "gen", "South", fuel="Gas")

        yrec: dict = {}
        for k, idx in pops.items():
            rb = idx[pbc["any"][idx]]
            if rb.size == 0:
                continue
            cap_h = cap_s_gas[:, rb].sum(axis=0)
            disp_h = disp_gas[rb]
            meas_h = np.nan_to_num(meas_gas[rb])
            idle_h = cap_h - disp_h
            # the mc of the marginal MW needed to lift model South gas to the measured level
            mc_needed = np.full(rb.size, np.nan)
            idle_within = {b: np.zeros(rb.size) for b in (10.0, 20.0, 50.0)}
            for i, h in enumerate(rb):
                m_h = mc_s_gas[:, h]
                c_h = cap_s_gas[:, h]
                ps = float(south_price[h])
                order = np.argsort(m_h)
                cum = np.cumsum(c_h[order])
                need = meas_h[i]
                j = int(np.searchsorted(cum, need))
                mc_needed[i] = (
                    float(m_h[order][min(j, len(order) - 1)]) if len(order) else np.nan
                )
                idle_sel = c_h > 1e-6
                for b in idle_within:
                    band = idle_sel & (m_h > ps + 1e-6) & (m_h <= ps + b)
                    idle_within[b][i] = float(c_h[band].sum())
            yrec[k] = {
                "hours_real_s2n": int(rb.size),
                "model_south_gas_available_gw_mean": round(
                    float(cap_h.mean()) / 1e3, 3
                ),
                "model_south_gas_dispatch_gw_mean": round(
                    float(disp_h.mean()) / 1e3, 3
                ),
                "measured_south_gas_gw_mean": round(float(meas_h.mean()) / 1e3, 3),
                "model_idle_south_gas_gw_mean": round(float(idle_h.mean()) / 1e3, 3),
                "hours_measured_exceeds_model_available": int((meas_h > cap_h).sum()),
                "capability_short_of_measured_gw_mean": round(
                    float(np.maximum(0.0, meas_h - cap_h).mean()) / 1e3, 3
                ),
                "model_south_price_mean": round(float(np.nanmean(south_price[rb])), 3),
                "actual_south_hubs_mean": round(float(np.nanmean(south_act[rb])), 3),
                "actual_indiana_mean": round(float(np.nanmean(ind_act[rb])), 3),
                "mc_of_marginal_mw_at_measured_gas_level_mean": round(
                    float(np.nanmean(mc_needed)), 3
                ),
                "mc_of_marginal_mw_at_measured_gas_level_p50": round(
                    float(np.nanmedian(mc_needed)), 3
                ),
                "idle_south_gas_within_usd_of_south_price_gw_mean": {
                    str(int(b)): round(float(v.mean()) / 1e3, 3)
                    for b, v in idle_within.items()
                },
            }
        out["years"][year] = yrec
        print(year, json.dumps(yrec, default=str)[:1200], flush=True)
    rec.setdefault("post_hoc", {})["south_gas"] = out
    p.OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"updated {p.OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
