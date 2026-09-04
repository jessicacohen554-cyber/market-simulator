"""miso-212 follow-up — the mc-identity residual, located and the counterfactuals re-run on the IMPLIED heat rate (disclosed, post-hoc).

The first pass (``_miso212_south_gas_cost_basis.py``) reconstructed the
keeper's gas marginal cost as ``HR_tr × F + VOM + markup_hr × anchor`` and
recorded a max identity residual of 230 / 739 / 1,525 $/MWh (2023 / 2024 /
2025) against the ``mc`` the LP actually saw. This script (1) LOCATES that
residual — which tranches, which classes, how large inside the Jun–Jul
binding hours — and (2) re-runs the measured counterfactuals (a) fuel → HH
spot, (b) zonal-basis increment removed, (c) heat rate → CAMPD burn, and the
combination, with the tranche's IMPLIED heat rate
``HR_impl = (mc − VOM − markup_hr × anchor) / F`` in place of the offer heat
rate ``HR_tr`` the first pass used. Where ``HR_tr`` overstates the fuel
sensitivity of a tranche's bid (the CT peak tranches, whose LP ``mc`` moves
with a lower heat rate than their 4.0× offer heat rate), the first pass
OVERSTATED the GW a fuel correction recovers; this is the corrected number.
Recorded under ``post_hoc`` in the miso-212 JSON. No threshold moved,
nothing armed.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso212_followup.py
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

import _miso211_rdt_binding_state as p  # noqa: E402  (re-points to the miso-210 keeper)
import _miso212_south_gas_cost_basis as q  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402

HOURS = p.HOURS
GAS = set(p.GAS_CLASSES)
EPS = 1e-6
IDLE_BAND = 20.0


def main() -> None:
    rec = json.loads(q.OUT.read_text())
    anchor = float(rec["anchor_usd_mmbtu"])
    cfg0 = keeper_config()
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    post: dict = {
        "disclosure": (
            "Computed AFTER the first pass. The first pass's mc identity "
            "HR_tr x F + VOM + markup_hr x anchor does not reproduce the LP's mc on "
            "every South gas tranche: the residual is located here by tranche/class, "
            "and the measured counterfactuals (a)/(b)/(c)/(a+b+c) are re-run with the "
            "IMPLIED heat rate (mc - VOM - markup_hr x anchor) / F, which is the fuel "
            "sensitivity the LP's bid actually carries. No threshold changed."
        ),
        "years": {},
    }
    for year in p.YEARS:
        ind_act, _south_act = p.actual_hubs(year)
        price, _lw, _dem_s, _slack = p.zone_prices(year)
        south_price = price["MISO-South"].to_numpy()
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        pops = {"SHOULDER": shoulder, "TAIL": tail}

        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, float)
        fp = np.asarray(fp, float)
        fp_nobasis = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(cfg, miso_zonal_gas_basis=False), arrays, year
            ),
            float,
        )
        hh = q.hh_daily_on_clock(year)
        labels = np.array([p.m207.class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        uids = np.array([str(g.unit_id) for g in fleet], dtype=object)
        bands = np.array([q._band(u) for u in uids], dtype=object)
        plants = np.array([int(getattr(g, "plant_code", 0) or 0) for g in fleet])
        hr = np.array([float(g.heat_rate) for g in fleet])
        vom = np.array([float(g.vom) for g in fleet])
        mk = np.array([float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet])
        avail = np.asarray(arrays.availability, float)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        cap = np.asarray(arrays.pmax, float)[:, None] * avail
        sel = (zones == "MISO-South") & np.isin(labels, list(GAS))

        uh = pd.read_parquet(
            p.KEEPER / f"hourly/unit_hourly_{year}.parquet",
            columns=["unit_id", "zone", "hour", "mc"],
        )
        uh = uh[uh["zone"] == "MISO-South"]
        bid = uh.pivot_table(index="unit_id", columns="hour", values="mc").reindex(
            columns=range(HOURS)
        )
        bid_by_uid = {str(k): bid.loc[k].to_numpy(float) for k in bid.index}

        # ---- (1) locate the residual
        recon = (
            hr[sel][:, None] * fp[sel] + vom[sel][:, None] + mk[sel][:, None] * anchor
        )
        res = recon - mc[sel]
        ab = np.abs(res)
        rows_bad = ab.max(axis=1) > 1.0
        hr_impl = (
            mc[sel] - vom[sel][:, None] - (mk[sel] * anchor)[:, None]
        ) / np.where(fp[sel] > EPS, fp[sel], np.nan)
        hr_impl = np.nan_to_num(hr_impl, nan=0.0)
        hr_impl = np.maximum(hr_impl, 0.0)
        ratio_impl = hr_impl / hr[sel][:, None]
        yrec: dict = {
            "tranches_with_abs_resid_gt_1": int(rows_bad.sum()),
            "tranches_total": int(sel.sum()),
            "max_abs_resid_all_hours": round(float(ab.max()), 3),
            "max_abs_resid_jun_jul": round(float(ab[:, jj].max()), 3),
            "sign": "recon > mc on every residual tranche"
            if bool((res[rows_bad] >= -1.0).all())
            else "mixed",
            "residual_tranches_by_class": {
                c: int((labels[sel][rows_bad] == c).sum())
                for c in sorted(set(labels[sel][rows_bad]))
            },
            "residual_tranches_by_band": {
                b: int((bands[sel][rows_bad] == b).sum())
                for b in sorted(set(bands[sel][rows_bad]))
            },
            "implied_over_offer_hr_ratio_jun_jul_median_by_class_band": {},
        }
        for c in sorted(set(labels[sel])):
            for b in sorted(set(bands[sel])):
                m = (labels[sel] == c) & (bands[sel] == b)
                if m.any():
                    yrec["implied_over_offer_hr_ratio_jun_jul_median_by_class_band"][
                        f"{c}:{b}"
                    ] = round(float(np.nanmedian(ratio_impl[m][:, jj])), 4)

        # ---- (2) counterfactuals on the implied heat rate
        ratio_by_plant = {}
        for popk in ("SHOULDER", "TAIL"):
            src = rec["years"][str(year)].get(popk, {}).get("heat_rate_plants", [])
            for r in src:
                ratio_by_plant.setdefault(popk, {})[int(r["plant"])] = float(
                    r["ratio_model_over_campd"]
                )
        for k, idx in pops.items():
            rb = idx[pbc["any"][idx]]
            if rb.size == 0:
                continue
            ps = south_price[rb]
            C = cap[sel][:, rb]
            F = fp[sel][:, rb]
            F_nb = fp_nobasis[sel][:, rb]
            HHh = hh[rb][None, :]
            MCb = mc[sel][:, rb]
            BID = np.vstack(
                [bid_by_uid.get(u, np.full(HOURS, np.nan))[rb] for u in uids[sel]]
            )
            BID = np.where(np.isnan(BID), MCb, BID)
            HRi = hr_impl[:, rb]
            basis_inc = F - F_nb
            idle = (
                (C > EPS) & (BID > ps[None, :] + EPS) & (BID <= ps[None, :] + IDLE_BAND)
            )
            Cidle = np.where(idle, C, 0.0)
            hr_ratio = np.array(
                [ratio_by_plant.get(k, {}).get(int(pc), 1.0) for pc in plants[sel]]
            )
            hrfac = (1.0 - 1.0 / np.where(hr_ratio > 0, hr_ratio, 1.0))[:, None]

            def econ_gw(bid_cf):
                e = (C > EPS) & (bid_cf <= ps[None, :] + EPS)
                return float(np.where(e, C, 0.0).sum(axis=0).mean()) / 1e3

            def cw(x, w):
                return float((x * w).sum() / w.sum()) if w.sum() > 0 else float("nan")

            base = econ_gw(BID)
            cfs = {
                "a_fuel_to_HH_spot": BID - HRi * (F - HHh),
                "b_basis_increment_removed": BID - HRi * basis_inc,
                "c_hr_to_campd_burn": BID - HRi * F * hrfac,
                "a+b+c measured combined": BID - HRi * (F - HHh) - HRi * F * hrfac,
            }
            meas_gas = (
                float(
                    np.nan_to_num(
                        p.regional_series(year, "gen", "South", fuel="Gas")[rb]
                    ).mean()
                )
                / 1e3
            )

            def mc_at_measured(bid_cf):
                vals = []
                for j in range(rb.size):
                    order = np.argsort(bid_cf[:, j])
                    cum = np.cumsum(C[order, j])
                    jj_ = int(np.searchsorted(cum, meas_gas * 1e3))
                    vals.append(float(bid_cf[order, j][min(jj_, len(order) - 1)]))
                return float(np.median(vals))

            first = rec["years"][str(year)][k]["counterfactuals"]
            yrec[k] = {
                "hours_real_s2n": int(rb.size),
                "block_implied_hr_capw": round(cw(HRi, Cidle), 3),
                "block_offer_hr_capw": round(
                    cw(np.broadcast_to(hr[sel][:, None], C.shape), Cidle), 3
                ),
                "block_usd_per_mwh_fuel_vs_HH_implied_hr": round(
                    cw(HRi * (F - HHh), Cidle), 3
                ),
                "block_usd_per_mwh_basis_increment_implied_hr": round(
                    cw(HRi * basis_inc, Cidle), 3
                ),
                "counterfactuals_implied_hr": {
                    name: {
                        "economic_gw_at_south_price": round(econ_gw(b), 3),
                        "recovered_gw_vs_baseline": round(econ_gw(b) - base, 3),
                        "bid_p50_at_measured_gas_level": round(mc_at_measured(b), 2),
                        "first_pass_recovered_gw": first.get(name, {}).get(
                            "recovered_gw_vs_baseline"
                        ),
                    }
                    for name, b in cfs.items()
                },
            }
        post["years"][year] = yrec
        print(year, json.dumps(yrec, default=str)[:2500], flush=True)
    rec["post_hoc"] = post
    q.OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"updated {q.OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
