"""miso-213 — THE RULE-19 ZONAL-BASIS LAYERING ON 923-PRICED CELLS (phase 0, zero-solve).

Executes ``results/calibration/PREREG-miso213-zonal-basis-layering-2026-09-05.md``
(pushed blind at ``a1a4a48``) on the miso-210 keeper's own fleet chain. No LP
is solved. Print-derived cells are identified WITHOUT touching production
code: ``resolve_fuel_prices`` is re-run on the SAME fleet arrays with the
zonal basis off (``F_nobasis``) and with both the basis and the EIA-923 print
path off (``F_noplant``); a cell where the two differ was set by the print
path (own print or the nearby pool). Own-print months come from
``eia923.plant_month_price_grid`` on the production F923 table.

  L-1  population: per zone and class, the capacity share of gas cells that
       are own-print / pool-filled / trajectory, and the increment each
       category receives (F − F_nobasis, i.e. the basis AFTER the dual-fuel
       oil-parity cap — the effect the LP actually saw);
  L-2  per-plant (923 print − HH daily spot) in the real S→N RDT-binding
       hours, South and Midwest, capacity-weighted p10/p50/p90;
  L-3  the arm's STATIC reach at fixed prices: the increment removed on
       print-derived cells ONLY (trajectory cells keep it), on the IMPLIED
       heat rate (mc − VOM − markup_hr × anchor)/F (miso-212 §6). South: GW of
       the idle block made economic at the keeper's South price in the real
       S→N binding shoulder + tail hours; the miso-212 (b) all-cell removal is
       recomputed on the same instrument so the ratio is like-for-like.
       Midwest mirror: signed GW change in economic Midwest gas at each
       unit's own zone price and at the Indiana price;
  L-4  genealogy: the print path is a HARNESS default for every non-ERCOT
       ISO (pipeline/backcast_config.py), not a CLI flag, so it was on when
       the basis was armed at gate 2; the basis rows are the N3045 state
       series minus Henry Hub — gross of the prints, never net.

INSTRUMENT LIMITATION, DISCLOSED: the keeper's ``hourly/unit_hourly_<year>``
sidecars are gitignored and absent in this container, so L-3 is computed on
the base cost ``mc_base`` (no P1 startup adder). miso-212's (b) number
(0.78 GW) was on the P1 bid; the same-instrument all-cell removal is reported
beside the arm's reach so the RATIO is exact even though the level is not.

Usage::

    PYTHONPATH=src .venv/bin/python scripts/probes/_miso213_basis_layering_phase0.py

Record: ``results/calibration/_miso213_basis_layering.json``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso211_rdt_binding_state as p  # noqa: E402  (re-points to the miso-210 keeper)
import _miso212_south_gas_cost_basis as q  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from market_sim.data.eia923 import plant_month_price_grid  # noqa: E402
from market_sim.data.fuel import (  # noqa: E402
    miso_zonal_gas_basis_by_zone,
    resolve_fuel_prices,
)
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402

OUT = REPO / "results/calibration/_miso213_basis_layering.json"
HOURS = p.HOURS
GAS = set(p.GAS_CLASSES)
EPS = 1e-6
IDLE_BAND = 20.0
SOUTH = "MISO-South"
INDIANA = "MISO-Indiana"


def _wq(x: np.ndarray, w: np.ndarray, qs=(0.10, 0.50, 0.90)) -> dict[str, float]:
    """Capacity-weighted quantiles of ``x`` (NaN-safe)."""
    ok = np.isfinite(x) & (w > 0)
    if not ok.any():
        return {f"p{int(q * 100)}": float("nan") for q in qs}
    x, w = x[ok], w[ok]
    order = np.argsort(x)
    x, w = x[order], w[order]
    cw = np.cumsum(w) / w.sum()
    return {f"p{int(q * 100)}": round(float(x[np.searchsorted(cw, q)]), 4) for q in qs}


def _cw(x: np.ndarray, w: np.ndarray) -> float:
    w = np.asarray(w, float)
    return float((x * w).sum() / w.sum()) if w.sum() > 0 else float("nan")


def main() -> None:  # noqa: PLR0915
    cfg0 = keeper_config()
    anchor = float(cfg0.gas_offer_margin_anchor)
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    month_idx = mon - 1
    costs = _load_monthly_cache(None)
    assert costs is not None, "F923 monthly table absent"
    rep: dict = {
        "charter": "miso-213 phase 0 — the rule-19 zonal-basis layering on 923-priced cells; zero-solve.",
        "prereg": "results/calibration/PREREG-miso213-zonal-basis-layering-2026-09-05.md @ a1a4a48",
        "keeper": "2026-09-04-miso-210-clock",
        "anchor_usd_mmbtu": anchor,
        "instrument": {
            "print_cell_identification": "F_nobasis (miso_zonal_gas_basis off) != F_noplant (basis off + gas_plant_monthly_fuel_pricing off) on the same FleetArrays; own-print months from eia923.plant_month_price_grid on the production F923 table; pool = print-derived minus own-print",
            "increment": "F_keeper - F_nobasis: the basis AFTER the dual-fuel oil-parity cap, i.e. what the LP saw",
            "L3_bid_basis": "mc_base from build_year (NO P1 startup adder: the keeper's unit_hourly sidecars are gitignored and absent here). The miso-212 (b) all-cell removal is recomputed on the same instrument; the arm's reach is reported as a RATIO of it as well as a level.",
            "heat_rate": "implied (mc - VOM - markup_hr x anchor) / F per cell (miso-212 §6)",
        },
        "keeper_flags": {
            "gas_plant_monthly_fuel_pricing": bool(cfg0.gas_plant_monthly_fuel_pricing),
            "nearby_fuel_price_fallback": bool(cfg0.nearby_fuel_price_fallback),
            "class_aware_fuel_price_fallback": bool(
                cfg0.class_aware_fuel_price_fallback
            ),
            "nearby_fuel_price_min_state_plants": int(
                cfg0.nearby_fuel_price_min_state_plants
            ),
            "miso_zonal_gas_basis": bool(cfg0.miso_zonal_gas_basis),
            "dual_fuel_switching": bool(cfg0.dual_fuel_switching),
            "gas_daily_shape": bool(cfg0.gas_daily_shape),
        },
        "years": {},
    }
    for year in p.YEARS:
        ind_act, _south_act = p.actual_hubs(year)
        price, _lw, _dem_s, _slack = p.zone_prices(year)
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        pops = {
            "SHOULDER": shoulder[pbc["any"][shoulder]],
            "TAIL": tail[pbc["any"][tail]],
        }

        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, fp, mc, zone_names = build_year(cfg, year)
        fp = np.asarray(fp, float)
        mc = np.asarray(mc, float)
        fp_nb = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(cfg, miso_zonal_gas_basis=False), arrays, year
            ),
            float,
        )
        fp_np = np.asarray(
            resolve_fuel_prices(
                dataclasses.replace(
                    cfg,
                    miso_zonal_gas_basis=False,
                    gas_plant_monthly_fuel_pricing=False,
                ),
                arrays,
                year,
            ),
            float,
        )
        hh = q.hh_daily_on_clock(year)
        labels = np.array([p.m207.class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        uids = np.array([str(g.unit_id) for g in fleet], dtype=object)
        bands = np.array([q._band(u) for u in uids], dtype=object)
        plants = np.array([int(getattr(g, "plant_code", 0) or 0) for g in fleet])
        vom = np.array([float(g.vom) for g in fleet])
        mk = np.array([float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet])
        pmax = np.asarray(arrays.pmax, float)
        avail = np.asarray(arrays.availability, float)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        cap = pmax[:, None] * avail
        gas = np.isin(labels, list(GAS))
        external = np.char.startswith(zones.astype(str), "MISO_external")
        midwest = gas & ~external & (zones != SOUTH)
        south = gas & (zones == SOUTH)

        # ---- cell categories
        printed = ~np.isclose(fp_nb, fp_np, rtol=0, atol=1e-9) & gas[:, None]
        grid = plant_month_price_grid(costs, year, "Natural Gas")
        own_month = np.zeros((len(fleet), 12), dtype=bool)
        for g in np.nonzero(gas)[0]:
            own = grid.get(int(plants[g])) if plants[g] > 0 else None
            if own is not None:
                own_month[g] = ~np.isnan(own)
        own_cell = own_month[:, month_idx] & printed
        pool_cell = printed & ~own_cell
        traj_cell = gas[:, None] & ~printed
        inc = fp - fp_nb  # the increment the LP saw (post oil-parity cap)

        # ---- the zone spread as the applier computes it (for the record)
        basis = miso_zonal_gas_basis_by_zone(year) or {}
        gas_rows = np.nonzero(gas)[0]
        gen_basis = np.array([basis.get(z, 0.0) for z in zones[gas_rows]])
        wmean = _cw(gen_basis, pmax[gas_rows])
        zone_spread = {
            z: round(float(basis.get(z, 0.0) - wmean), 4)
            for z in zone_names
            if z in basis
        }

        # ---- L-1 population, pmax x hour-share weighted
        def _pop(sel: np.ndarray, hours: np.ndarray) -> dict:
            w = pmax[sel][:, None] * np.ones((1, hours.size))
            tot = float(w.sum())
            if tot <= 0:
                return {}
            return {
                "gas_capacity_gw": round(float(pmax[sel].sum()) / 1e3, 3),
                "share_own_print": round(
                    float((w * own_cell[sel][:, hours]).sum() / tot), 4
                ),
                "share_pool": round(
                    float((w * pool_cell[sel][:, hours]).sum() / tot), 4
                ),
                "share_trajectory": round(
                    float((w * traj_cell[sel][:, hours]).sum() / tot), 4
                ),
                "inc_capw_own_print": round(
                    _cw(
                        inc[sel][:, hours][own_cell[sel][:, hours]],
                        w[own_cell[sel][:, hours]],
                    ),
                    4,
                ),
                "inc_capw_pool": round(
                    _cw(
                        inc[sel][:, hours][pool_cell[sel][:, hours]],
                        w[pool_cell[sel][:, hours]],
                    ),
                    4,
                ),
                "inc_capw_trajectory": round(
                    _cw(
                        inc[sel][:, hours][traj_cell[sel][:, hours]],
                        w[traj_cell[sel][:, hours]],
                    ),
                    4,
                ),
                "inc_capw_all": round(_cw(inc[sel][:, hours], w), 4),
            }

        all_h = np.arange(HOURS)
        l1: dict = {
            "zone_spread_after_mean": zone_spread,
            "capw_mean_removed": round(wmean, 4),
        }
        for hk, hrs in (("all_hours", all_h), ("jun_jul", jj)):
            blk: dict = {"ISO": _pop(gas & ~external, hrs)}
            for z in zone_names:
                s = gas & (zones == z)
                if s.any():
                    blk[z] = _pop(s, hrs)
            by_class: dict = {}
            for c in sorted(GAS):
                s = gas & ~external & (labels == c)
                if s.any():
                    by_class[c] = _pop(s, hrs)
            blk["by_class"] = by_class
            zc: dict = {}
            for z in (
                SOUTH,
                INDIANA,
                "MISO-West",
                "MISO-Plains",
                "MISO-Illinois",
                "MISO-East",
            ):
                for c in sorted(GAS):
                    s = gas & (zones == z) & (labels == c)
                    if s.any():
                        zc[f"{z}:{c}"] = _pop(s, hrs)
            blk["by_zone_class"] = zc
            l1[hk] = blk

        # ---- L-2 per-plant print − HH in the binding hours
        l2: dict = {}
        for k, rb in pops.items():
            if rb.size == 0:
                continue
            blk = {
                "hours_real_s2n": int(rb.size),
                "hh_spot_mean": round(float(hh[rb].mean()), 4),
            }
            for reg, sel in (("South", south), ("Midwest", midwest)):
                rows = np.nonzero(sel)[0]
                per_plant: dict[int, list] = {}
                for g in rows:
                    m_own = own_cell[g, rb]
                    m_pool = pool_cell[g, rb]
                    pc = int(plants[g])
                    per_plant.setdefault(pc, [0.0, 0.0, 0.0, 0.0, 0.0])
                    if m_own.any():
                        per_plant[pc][0] += float(
                            ((fp_nb[g, rb] - hh[rb]) * cap[g, rb])[m_own].sum()
                        )
                        per_plant[pc][1] += float(cap[g, rb][m_own].sum())
                    if m_pool.any():
                        per_plant[pc][2] += float(
                            ((fp_nb[g, rb] - hh[rb]) * cap[g, rb])[m_pool].sum()
                        )
                        per_plant[pc][3] += float(cap[g, rb][m_pool].sum())
                    per_plant[pc][4] += float(pmax[g])
                own_x, own_w, pool_x, pool_w = [], [], [], []
                for pc, (sx, sw, px, pw, _pm) in per_plant.items():
                    if sw > 0:
                        own_x.append(sx / sw)
                        own_w.append(sw / rb.size)
                    if pw > 0:
                        pool_x.append(px / pw)
                        pool_w.append(pw / rb.size)
                own_x, own_w = np.array(own_x), np.array(own_w)
                pool_x, pool_w = np.array(pool_x), np.array(pool_w)
                # print premium vs the zone increment those plants receive
                inc_sel = _cw(
                    inc[sel][:, rb],
                    np.where(cap[sel][:, rb] > EPS, cap[sel][:, rb], 0.0),
                )
                blk[reg] = {
                    "own_print_plants": int(own_x.size),
                    "own_print_capw_gw": round(float(own_w.sum()) / 1e3, 3),
                    "own_print_minus_hh": _wq(own_x, own_w),
                    "own_print_minus_hh_capw_mean": round(_cw(own_x, own_w), 4),
                    "pool_plants": int(pool_x.size),
                    "pool_capw_gw": round(float(pool_w.sum()) / 1e3, 3),
                    "pool_minus_hh": _wq(pool_x, pool_w),
                    "pool_minus_hh_capw_mean": round(_cw(pool_x, pool_w), 4),
                    "basis_increment_received_capw": round(inc_sel, 4),
                }
            l2[k] = blk

        # ---- L-3 static reach on the implied heat rate
        with np.errstate(divide="ignore", invalid="ignore"):
            hr_impl = np.where(
                fp > 0, (mc - vom[:, None] - (mk * anchor)[:, None]) / fp, 0.0
            )
        hr_impl = np.where(gas[:, None], hr_impl, 0.0)
        bid0 = mc
        bid_arm = mc - hr_impl * np.where(
            printed, inc, 0.0
        )  # increment removed on print cells only
        bid_all = mc - hr_impl * np.where(
            gas[:, None], inc, 0.0
        )  # miso-212 (b) analogue

        def _econ_gw(sel, b, pz, rb):
            C = cap[sel][:, rb]
            e = (C > EPS) & (b[sel][:, rb] <= pz[None, :] + EPS)
            return float(np.where(e, C, 0.0).sum(axis=0).mean()) / 1e3

        def _idle_gw(sel, b, pz, rb):
            C = cap[sel][:, rb]
            i = (
                (C > EPS)
                & (b[sel][:, rb] > pz[None, :] + EPS)
                & (b[sel][:, rb] <= pz[None, :] + IDLE_BAND)
            )
            return float(np.where(i, C, 0.0).sum(axis=0).mean()) / 1e3

        l3: dict = {}
        for k, rb in pops.items():
            if rb.size == 0:
                continue
            ps = price[SOUTH].to_numpy()[rb]
            pind = price[INDIANA].to_numpy()[rb]
            base_s = _econ_gw(south, bid0, ps, rb)
            arm_s = _econ_gw(south, bid_arm, ps, rb)
            all_s = _econ_gw(south, bid_all, ps, rb)
            Cs = cap[south][:, rb]
            sel_cells = printed[south][:, rb] & (Cs > EPS)
            by_class = {}
            for c in sorted(set(labels[south])):
                s = south & (labels == c)
                by_class[c] = {
                    "base_econ_gw": round(_econ_gw(s, bid0, ps, rb), 3),
                    "arm_delta_gw": round(
                        _econ_gw(s, bid_arm, ps, rb) - _econ_gw(s, bid0, ps, rb), 3
                    ),
                    "all_removed_delta_gw": round(
                        _econ_gw(s, bid_all, ps, rb) - _econ_gw(s, bid0, ps, rb), 3
                    ),
                }
            by_band = {}
            for b_ in sorted(set(bands[south])):
                s = south & (bands == b_)
                by_band[b_] = {
                    "base_econ_gw": round(_econ_gw(s, bid0, ps, rb), 3),
                    "arm_delta_gw": round(
                        _econ_gw(s, bid_arm, ps, rb) - _econ_gw(s, bid0, ps, rb), 3
                    ),
                }
            # Midwest mirror: own zone price and the Indiana price
            pz_own = np.vstack([price[z].to_numpy()[rb] for z in zones[midwest]])

            def _econ_gw_ownp(b):
                C = cap[midwest][:, rb]
                e = (C > EPS) & (b[midwest][:, rb] <= pz_own + EPS)
                return float(np.where(e, C, 0.0).sum(axis=0).mean()) / 1e3

            mw_base_own, mw_arm_own = _econ_gw_ownp(bid0), _econ_gw_ownp(bid_arm)
            mw_base_ind = _econ_gw(midwest, bid0, pind, rb)
            mw_arm_ind = _econ_gw(midwest, bid_arm, pind, rb)
            mw_by_zone = {}
            for z in sorted(set(zones[midwest])):
                s = midwest & (zones == z)
                pz = price[z].to_numpy()[rb]
                mw_by_zone[z] = {
                    "base_econ_gw": round(_econ_gw(s, bid0, pz, rb), 3),
                    "arm_delta_gw_own_price": round(
                        _econ_gw(s, bid_arm, pz, rb) - _econ_gw(s, bid0, pz, rb), 3
                    ),
                    "inc_capw_print_cells": round(
                        _cw(
                            inc[s][:, rb][printed[s][:, rb]],
                            cap[s][:, rb][printed[s][:, rb]],
                        ),
                        4,
                    ),
                    "share_print_cells_capw": round(
                        float(
                            (cap[s][:, rb] * printed[s][:, rb]).sum()
                            / max(cap[s][:, rb].sum(), 1e-9)
                        ),
                        4,
                    ),
                }
            l3[k] = {
                "hours_real_s2n": int(rb.size),
                "south_price_mean": round(float(ps.mean()), 3),
                "indiana_price_mean": round(float(pind.mean()), 3),
                "south": {
                    "base_econ_gw_mc_base": round(base_s, 3),
                    "idle_within_20_gw_mc_base": round(
                        _idle_gw(south, bid0, ps, rb), 3
                    ),
                    "arm_923_only_removed_delta_gw": round(arm_s - base_s, 3),
                    "all_cells_removed_delta_gw_miso212b_analogue": round(
                        all_s - base_s, 3
                    ),
                    "arm_over_all_ratio": round((arm_s - base_s) / (all_s - base_s), 4)
                    if abs(all_s - base_s) > 1e-9
                    else None,
                    "share_print_cells_capw": round(
                        float((Cs * printed[south][:, rb]).sum() / max(Cs.sum(), 1e-9)),
                        4,
                    ),
                    "inc_capw_print_cells": round(
                        _cw(inc[south][:, rb][sel_cells], Cs[sel_cells]), 4
                    ),
                    "usd_per_mwh_removed_capw_print_cells": round(
                        _cw(
                            (hr_impl[south][:, rb] * inc[south][:, rb])[sel_cells],
                            Cs[sel_cells],
                        ),
                        3,
                    ),
                    "implied_hr_capw_print_cells": round(
                        _cw(hr_impl[south][:, rb][sel_cells], Cs[sel_cells]), 3
                    ),
                    "by_class": by_class,
                    "by_band": by_band,
                },
                "midwest": {
                    "base_econ_gw_own_zone_price": round(mw_base_own, 3),
                    "arm_delta_gw_own_zone_price": round(mw_arm_own - mw_base_own, 3),
                    "base_econ_gw_indiana_price": round(mw_base_ind, 3),
                    "arm_delta_gw_indiana_price": round(mw_arm_ind - mw_base_ind, 3),
                    "by_zone": mw_by_zone,
                },
            }
            print(
                year,
                k,
                "L3 south",
                json.dumps(l3[k]["south"], default=str)[:700],
                flush=True,
            )
            print(
                year,
                k,
                "L3 midwest",
                json.dumps(
                    {kk: v for kk, v in l3[k]["midwest"].items() if kk != "by_zone"}
                ),
                flush=True,
            )

        rep["years"][year] = {
            "n_gas_rows": int(gas.sum()),
            "n_gas_rows_carry": int((gas & ~external).sum()),
            "L1": l1,
            "L2": l2,
            "L3": l3,
        }
        print(year, "L1 ISO all_hours", json.dumps(l1["all_hours"]["ISO"]), flush=True)
        print(
            year, "L1 South jun_jul", json.dumps(l1["jun_jul"].get(SOUTH)), flush=True
        )
        print(year, "L2", json.dumps(l2.get("SHOULDER"), default=str)[:900], flush=True)
        OUT.write_text(json.dumps(rep, indent=1, default=str))

    rep["L4_genealogy"] = {
        "print_path_arming": "pipeline/backcast_config.py: gas_plant_monthly_fuel_pricing=(iso != 'ERCOT') — a HARNESS default for every non-ERCOT ISO, not a CLI flag (run_calibration_full.py has no --gas-plant-monthly flag). The gate-2 recipe (docs/multi-iso/miso-zonal-gate2.md) lists --miso-zonal-gas-basis explicitly and states every other flag is an argparse/harness default, so the print path was ON when the basis was armed.",
        "basis_identification": "data/raw/miso_zonal_gas_hub.csv source column: '<ST> delivered-to-electric-power (EIA N3045<ST>3) minus Henry Hub monthly mean' (scripts/data/fetch_eia_delivered_gas.py: mean over published months of N3045/1.036 − HH). The N3045 series is the state aggregate of the same EIA-923 receipts the prints report — the basis is GROSS of the prints, never identified NET of them.",
        "keeper_carries_both": bool(
            cfg0.gas_plant_monthly_fuel_pricing and cfg0.miso_zonal_gas_basis
        ),
        "conclusion": "The layering has been in every MISO keeper since the basis was armed (gate 2). Neither kill condition of PREREG §4 holds: the print path does not exclude basis-carrying cells (L-1), and the basis was not identified net of the prints.",
    }
    OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
