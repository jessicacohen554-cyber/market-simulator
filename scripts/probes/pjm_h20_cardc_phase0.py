"""pjm-h20 phase 0 — Card C: locate the CC-marginal overshoot and size the CT shelf. ZERO LP.

Rule 32 ``[R-SHARD]`` (a): the parent runs no LP. For each year a ``fleet_only``
rebuild of the PJM keeper recipe (``pjm_h19_dbs_{span,touchpoint}``, through the
sanctioned ``replay_keeper.run_year_kwargs``) supplies the SAME ``mc_base`` the LP
solved on. Three bid objects are then built with the model's OWN builders:

* ``floor``  — the keeper's armed mid-curve markup (``pjm_offer_midcurve_segments =
  ('LONG_RUN','CC_LIKE')``, FLOOR form: raise-only toward PJM's published offer);
* ``level``  — the same builder with ``pjm_offer_midcurve_level_segments =
  ('CC_LIKE',)`` in a LOCAL config copy (LEVEL form: the CC econ rung IS the
  measured offer, so a fitted rung above measured comes DOWN onto it);
* ``ct_tgt`` — ``build_pjm_ct_measured_max_target`` with
  ``pjm_ct_measured_max_reprice`` flipped on in a LOCAL config copy.

Nothing is armed, swept or constructed; every flip lives in this probe's copy.

The hour classification is pjm-h18's (``pjm_h18_marginal_family_phase0.py``):
the marginal class-band of an hour is the partially-loaded band whose
capacity-weighted ``mc_base`` is nearest the load-weighted system price.

STATED LIMITS, not buried:
1. The P1 bid also carries the startup amortization, which needs the P0
   dispatch (an LP) — so keeper bids here are ``mc_base + floor`` WITHOUT it.
   For CC econ rows the level form REPLACES the fitted rung (the markup is
   ``target - mc_base``), so the amortization still adds on top in both arms
   and the arm-vs-keeper DELTA is exact; the absolute keeper bid is a lower
   bound. For CT the max() seam is taken against the full P1 bid, so the CT
   lift reported here (``target - mc_base``) is an UPPER BOUND (pjm-h17 §5).
2. Net load for the surface's conditioning is demand minus wind/solar
   potential (pjm-h17's construction), not the LP-served net load.
3. A static price read ("the marginal band's bid under the arm") ignores
   redispatch; it is a direction and footprint, never a predicted C3a.

Run: ``python3 scripts/probes/pjm_h20_cardc_phase0.py 2020 2021 2022 2023 2024 2025``
Writes ``results/calibration/_pjm_h20_cardc_phase0.json``.
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
sys.path.insert(0, str(REPO / "src"))

CC = ("CC_REGULAR", "CC_CHP")
CT = ("CT_PEAKER", "CT_CHP")


def _bundle(y: int) -> Path:
    """Return the keeper bundle that carries year ``y``."""
    return REPO / "results/calibration" / (
        "pjm_h19_dbs_span" if y >= 2023 else "pjm_h19_dbs_touchpoint"
    )


def main() -> None:
    """Run the Card C phase 0 for the requested years and write the JSON."""
    logging.disable(logging.CRITICAL)
    from market_sim.data.fleet.offer_surfaces import (
        build_pjm_ct_measured_max_target,
        build_pjm_offer_midcurve_conditional_markup,
    )
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    act = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet")
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or [2020, 2021, 2022, 2023, 2024, 2025]:
        B = _bundle(y)
        meta = json.loads((B / "meta.json").read_text())
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(B, y))
        kw["pjm_da_virtual_bids"] = False  # declared simplification, pjm-h8 §2
        r = run_year(y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
        cfg, fleet, fa = r["config"], r["fleet"], r["fleet_arrays"]
        mc = np.asarray(r["mc_base"], float)
        if mc.ndim == 1:
            mc = mc[:, None] * np.ones((1, 8760))
        T = mc.shape[1]
        net = np.asarray(
            r["demand"].sum(axis=0)
            - (r["solar_cap"][:, None] * r["solar_cf"]).sum(axis=0)
            - (r["wind_cap"][:, None] * r["wind_cf"]).sum(axis=0),
            float,
        )
        assert tuple(cfg.pjm_offer_midcurve_segments) == ("LONG_RUN", "CC_LIKE")
        assert not getattr(cfg, "pjm_offer_midcurve_level_segments", None)
        assert not getattr(cfg, "pjm_ct_measured_max_reprice", False)
        floor = build_pjm_offer_midcurve_conditional_markup(fa, fleet, mc, net, cfg, y)
        floor = np.zeros_like(mc) if floor is None else floor
        cfg_l = cfg.with_overrides(pjm_offer_midcurve_level_segments=("CC_LIKE",))
        level = build_pjm_offer_midcurve_conditional_markup(fa, fleet, mc, net, cfg_l, y)
        cfg_c = cfg.with_overrides(pjm_ct_measured_max_reprice=True)
        ct_tgt = build_pjm_ct_measured_max_target(fa, fleet, mc, net, cfg_c, y)
        ct_tgt = np.zeros_like(mc) if ct_tgt is None else ct_tgt

        cls = np.asarray(fa.plant_group).astype(str)
        band = np.array([u.rsplit("_", 1)[-1] for u in fa.unit_ids])
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, T))
        av = np.asarray(fa.pmax, float)[:, None] * avail
        key = np.char.add(np.char.add(cls, "|"), band)

        # ---- pjm-h18 marginal-band classification (keeper hourlies) ----
        cb = pd.read_parquet(B / "hourly" / f"class_band_hourly_{y}.parquet")
        cb = cb[cb["pass"] == "P1"]
        cb["key"] = cb.klass.astype(str).str.replace(r"^COAL_.*", "COAL", regex=True) + "|" + cb.band.astype(str)
        disp = cb.pivot_table(index="key", columns="hour", values="mw", aggfunc="sum").reindex(columns=range(T)).fillna(0.0)
        s = pd.read_parquet(B / "hourly" / f"system_{y}.parquet")
        s = s[(s["pass"] == "P1") & (s.zone != "PJM_external")]
        s = s.assign(pdm=s.price * s.demand).groupby("hour")[["pdm", "demand"]].sum()
        p = (s.pdm / s.demand).reindex(range(T)).to_numpy()
        w = s.demand.reindex(range(T)).to_numpy()
        a = act[act.year == y].sort_values("hour").rt.to_numpy(float)[:T]
        uk = [k for k in np.unique(key) if k in disp.index]
        capk = np.vstack([av[key == k].sum(0) for k in uk])
        mck = np.vstack([(mc[key == k] * av[key == k]).sum(0) / np.maximum(av[key == k].sum(0), 1e-9) for k in uk])
        u = disp.loc[uk].to_numpy() / np.maximum(capk, 1e-9)
        part = (u > 0.02) & (u < 0.98) & (capk > 50)
        dist = np.where(part, np.abs(mck - p[None, :]), np.inf)
        j = np.argmin(dist, axis=0)
        marg = np.where(np.isfinite(dist.min(0)), np.array(uk)[j], "none|none")
        mcls = np.array([m.split("|")[0] for m in marg])
        mband = np.array([m.split("|")[1] for m in marg])

        def bandbid(arr: np.ndarray, k: str, hrs: np.ndarray) -> np.ndarray:
            """Capacity-weighted value of ``arr`` over rows of band ``k`` in ``hrs``."""
            m = key == k
            return (arr[m][:, hrs] * av[m][:, hrs]).sum(0) / np.maximum(av[m][:, hrs].sum(0), 1e-9)

        yr: dict = {"n_hours": T}
        # ---- CC half ----
        ccm = np.isin(mcls, CC)
        econ = np.char.startswith(mband, "econ")
        yr["cc_marginal_share"] = float(ccm.mean())
        yr["cc_marginal_band_mix"] = {b: float((ccm & (mband == b)).sum() / max(ccm.sum(), 1)) for b in np.unique(mband[ccm])}
        reach = ccm & econ
        yr["cc_marginal_reachable_share"] = float(reach.sum() / max(ccm.sum(), 1))
        kb_keep, kb_lvl, kb_meas = np.full(T, np.nan), np.full(T, np.nan), np.full(T, np.nan)
        lvl_bid = mc + (level if level is not None else 0.0)
        keep_bid = mc + floor
        for k in np.unique(marg[reach]):
            hrs = np.where(marg == k)[0]
            kb_keep[hrs] = bandbid(keep_bid, k, hrs)
            kb_lvl[hrs] = bandbid(lvl_bid, k, hrs)
        h = np.where(reach)[0]
        W = w[h].sum()
        yr["cc_reach_lw"] = {
            "model_price": float((p[h] * w[h]).sum() / W),
            "actual_price": float((a[h] * w[h]).sum() / W),
            "keeper_band_bid_ex_amort": float((kb_keep[h] * w[h]).sum() / W),
            "level_band_bid_ex_amort": float((kb_lvl[h] * w[h]).sum() / W),
            "static_delta_level_minus_keeper": float(((kb_lvl[h] - kb_keep[h]) * w[h]).sum() / W),
        }
        hc = np.where(ccm)[0]
        yr["cc_all_lw"] = {
            "model_price": float((p[hc] * w[hc]).sum() / w[hc].sum()),
            "actual_price": float((a[hc] * w[hc]).sum() / w[hc].sum()),
            "overshoot_pct": float(((p[hc] - a[hc]) * w[hc]).sum() / (a[hc] * w[hc]).sum() * 100),
        }
        # CC econ fleet: fitted-above-measured census (the rule-14 identification)
        cce = np.isin(cls, CC) & np.char.startswith(band, "econ")
        if level is not None:
            tgt_cc = mc[cce] + level[cce]  # == measured target where finite
            fitted = mc[cce]
            wcc = av[cce]
            yr["cc_econ_census"] = {
                "mw": float(np.asarray(fa.pmax, float)[cce].sum()),
                "fitted_above_measured_mwh_share": float((wcc * (fitted > tgt_cc + 1e-9)).sum() / wcc.sum()),
                "capwtd_fitted": float((fitted * wcc).sum() / wcc.sum()),
                "capwtd_measured": float((tgt_cc * wcc).sum() / wcc.sum()),
                "capwtd_keeper_floor_bid": float(((mc + floor)[cce] * wcc).sum() / wcc.sum()),
            }
        # ---- CT half ----
        ctm = np.isin(mcls, CT)
        ctr = np.isin(cls, CT) & (ct_tgt.any(axis=1))
        lift = np.maximum(0.0, ct_tgt - mc)
        wct = av[ctr]
        yr["ct_census"] = {
            "rows": int(ctr.sum()),
            "mw": float(np.asarray(fa.pmax, float)[ctr].sum()),
            "capwtd_mc_base": float((mc[ctr] * wct).sum() / wct.sum()),
            "capwtd_target": float((ct_tgt[ctr] * wct).sum() / wct.sum()),
            "ub_lift_capwtd": float((lift[ctr] * wct).sum() / wct.sum()),
            "target_gt_mcbase_mwh_share": float((wct * (ct_tgt[ctr] > mc[ctr])).sum() / wct.sum()),
        }
        ht = np.where(ctm)[0]
        if ht.size:
            yr["ct_marginal_lw"] = {
                "share": float(ctm.mean()),
                "model_price": float((p[ht] * w[ht]).sum() / w[ht].sum()),
                "actual_price": float((a[ht] * w[ht]).sum() / w[ht].sum()),
            }
        # ---- the whole-year error by family (reproduces pjm-h18 §3 on this keeper) ----
        Wy = w.sum()
        fam = np.where(np.char.startswith(mcls, "COAL"), "coal", np.where(np.isin(mcls, CC), "cc", np.where(np.isin(mcls, CT), "ct", np.where(np.isin(mcls, ["ST_GAS", "ST_CHP"]), "st", "other"))))
        yr["err_contrib"] = {f: float(((p - a) * w)[fam == f].sum() / Wy) for f in ["coal", "cc", "ct", "st", "other"]}
        yr["c3a_pct"] = float(((p * w).sum() / Wy) / ((a * w).sum() / Wy) * 100 - 100)
        # ---- by actual-price region, the arm's static bid delta on the MARGINAL band ----
        dl = np.zeros(T)
        dl[h] = kb_lvl[h] - kb_keep[h]
        lo = a <= np.median(a)
        top = a >= np.quantile(a, 0.95)
        yr["static_cc_delta_by_region"] = {
            "bottom50": float((dl * w)[lo].sum() / Wy),
            "p50_p95": float((dl * w)[~lo & ~top].sum() / Wy),
            "top5": float((dl * w)[top].sum() / Wy),
        }
        out["years"][str(y)] = yr
        print(y, json.dumps(yr)[:2500], flush=True)
    dest = REPO / "results/calibration/_pjm_h20_cardc_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
