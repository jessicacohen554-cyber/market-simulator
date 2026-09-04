"""miso-212 — THE SOUTH GAS DELIVERED-COST BASIS (phase 0, zero-solve).

Executes ``PREREG-miso212-south-gas-cost-basis-2026-09-04.md`` (pushed blind at
``db893e8e``): in the hours MISO's RDT bound South->North (miso-211), decompose
the keeper's South gas marginal cost tranche by tranche —

    mc_base = HR_tr x F + VOM + markup_hr x anchor ;  bid_P1 = mc_base + startup

— and put each leg beside its measured counterpart: F against Henry Hub daily
spot, split into the plant's EIA-923 print and the zonal-basis increment (each
isolated by re-running ``resolve_fuel_prices`` with that overlay off on the
SAME fleet arrays); HR against the plant's CAMPD burn (sum heat / sum gross,
same hours); the P1 startup adder against the base. Then the static
counterfactuals: how much of the model's idle South gas becomes economic at the
model's own South price under each MEASURED correction. Finally the market's
own declarations: the South region's RT offered supply curve (masked offer
corpus, outcome columns dropped at curation) against the model's whole South
supply curve at the same hours.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso212_south_gas_cost_basis.py

Record: ``results/calibration/_miso212_south_gas_cost_basis.json``.
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso211_rdt_binding_state as p  # noqa: E402  (re-points to the miso-210 keeper)
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

OUT = REPO / "results/calibration/_miso212_south_gas_cost_basis.json"
HOURS = p.HOURS
GAS = set(p.GAS_CLASSES)
IDLE_BAND = 20.0
EPS = 1e-6
E923 = RAW_DATA_DIR / "_processed-legacy" / "eia923_monthly_fuel_costs.parquet"
HH_DAILY = RAW_DATA_DIR / "gas-prices" / "henry_hub_daily.csv"
MODEL_TZ = "Etc/GMT+6"


def _band(unit_id: str) -> str:
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", unit_id)
    suf = m.group(2) if m else ""
    for k in ("mustrun", "sync", "committed", "econ", "peak"):
        if suf.startswith(k):
            return k
    return suf or "?"


def hh_daily_on_clock(year: int) -> np.ndarray:
    """Henry Hub daily spot on the model clock (weekends/holidays forward-filled)."""
    h = pd.read_csv(HH_DAILY, parse_dates=["date"]).sort_values("date")
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    s = h.set_index("date")["price_usd_mmbtu"].reindex(days).ffill().bfill()
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    return np.repeat(s.to_numpy(float), 24)[:HOURS]


def campd_plant_hr(
    year: int, hours_idx: np.ndarray, states: list[str]
) -> dict[int, float]:
    """Plant-level burn heat rate (sum heat / sum gross) over ``hours_idx`` (MMBtu/MWh)."""
    df = campd.load_campd_hourly(states, [year])
    df = df[df["hour_of_year"].isin(set(hours_idx.tolist()))]
    g = df.groupby("plant_id")[["heat_mmbtu", "gross_mw"]].sum()
    g = g[g["gross_mw"] > 0]
    return {int(k): float(v) for k, v in (g["heat_mmbtu"] / g["gross_mw"]).items()}


def offer_stack_south(
    year: int, hours_idx: np.ndarray
) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Per model hour: (sorted offer prices, cumulative offered MW) for Region South, RT."""
    if not clean_io.clean_exists("energy-offers", iso="MISO", year=year, market="RT"):
        return {}
    df = clean_io.read_clean("energy-offers", iso="MISO", year=year, market="RT")
    df = df[df["region"].astype(str).str.lower() == "south"]
    ts = pd.to_datetime(df["interval_start_utc"], utc=True).dt.tz_convert(MODEL_TZ)
    hoy = np.array(
        [
            p._nonleap_hour(t.year, t.month, t.day, t.hour) if t.year == year else -1
            for t in ts
        ]
    )
    df = df.assign(hoy=hoy)
    want = set(hours_idx.tolist())
    df = df[df["hoy"].isin(want)]
    out: dict[int, tuple[np.ndarray, np.ndarray]] = {}
    for h, sub in df.groupby("hoy"):
        sub = sub.sort_values(["unit_code", "step_idx"])
        # step_mw is cumulative within a unit; the increment is the block at that price
        inc = sub.groupby("unit_code")["step_mw"].diff().fillna(sub["step_mw"])
        inc = inc.clip(lower=0.0).to_numpy(float)
        price = sub["step_price_usd_per_mwh"].to_numpy(float)
        ok = np.isfinite(price) & np.isfinite(inc)
        order = np.argsort(price[ok])
        out[int(h)] = (price[ok][order], np.cumsum(inc[ok][order]))
    return out


def _price_at(stack: tuple[np.ndarray, np.ndarray], q_mw: float) -> float:
    price, cum = stack
    j = int(np.searchsorted(cum, q_mw))
    return float(price[min(j, len(price) - 1)]) if len(price) else float("nan")


def _mw_at(stack: tuple[np.ndarray, np.ndarray], price_cap: float) -> float:
    price, cum = stack
    j = int(np.searchsorted(price, price_cap, side="right"))
    return float(cum[j - 1]) if j > 0 else 0.0


def main() -> None:  # noqa: PLR0915
    cfg0 = keeper_config()
    anchor = float(cfg0.gas_offer_margin_anchor)
    mon = p.m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    e923 = pd.read_parquet(E923)
    e923 = e923[e923["fuel_group"] == "Natural Gas"]
    rep: dict = {
        "charter": "miso-212 phase 0 — the South gas delivered-cost basis; zero-solve.",
        "prereg": "results/calibration/PREREG-miso212-south-gas-cost-basis-2026-09-04.md @ db893e8e",
        "keeper": "2026-09-04-miso-210-clock",
        "anchor_usd_mmbtu": anchor,
        "years": {},
    }
    for year in p.YEARS:
        ind_act, south_act = p.actual_hubs(year)
        price, _lw, _dem_s, _slack = p.zone_prices(year)
        south_price = price["MISO-South"].to_numpy()
        pbc = p.pbc_hourly(year, "RDT_SO_MW")
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        pops = {"SHOULDER": shoulder, "TAIL": tail}

        # ---- the keeper's own chain, and the fuel overlays isolated
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
        fp_noplant = np.asarray(
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
        hh = hh_daily_on_clock(year)
        labels = np.array([p.m207.class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        uids = np.array([str(g.unit_id) for g in fleet], dtype=object)
        bands = np.array([_band(u) for u in uids], dtype=object)
        groups = np.array([str(g.plant_group or "") for g in fleet], dtype=object)
        plants = np.array([int(getattr(g, "plant_code", 0) or 0) for g in fleet])
        hr = np.array([float(g.heat_rate) for g in fleet])
        vom = np.array([float(g.vom) for g in fleet])
        mk = np.array([float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet])
        avail = np.asarray(arrays.availability, float)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        cap = np.asarray(arrays.pmax, float)[:, None] * avail
        sel = (zones == "MISO-South") & np.isin(labels, list(GAS))

        # P1 bid from unit_hourly (the mc the LP actually saw)
        uh = pd.read_parquet(
            p.KEEPER / f"hourly/unit_hourly_{year}.parquet",
            columns=["unit_id", "zone", "hour", "mc"],
        )
        uh = uh[uh["zone"] == "MISO-South"]
        bid = uh.pivot_table(index="unit_id", columns="hour", values="mc").reindex(
            columns=range(HOURS)
        )
        bid_by_uid = {str(k): bid.loc[k].to_numpy(float) for k in bid.index}
        matched = sum(1 for u in uids[sel] if u in bid_by_uid)

        yrec: dict = {
            "n_south_gas_tranches": int(sel.sum()),
            "unit_hourly_bid_matched": matched,
            "fuel_overlays_isolated": "F (keeper) vs F_nobasis (miso_zonal_gas_basis off) vs F_noplant (+ gas_plant_monthly_fuel_pricing off)",
        }
        # identity check of the decomposition on the South gas rows (all hours)
        recon = (
            hr[sel][:, None] * fp[sel] + vom[sel][:, None] + mk[sel][:, None] * anchor
        )
        yrec["mc_identity_max_abs_resid_all_hours"] = round(
            float(np.nanmax(np.abs(recon - mc[sel]))), 4
        )

        states = [
            s for s in campd.states_for_iso("MISO") if s in ("LA", "AR", "MS", "TX")
        ]
        for k, idx in pops.items():
            rb = idx[pbc["any"][idx]]
            if rb.size == 0:
                continue
            ps = south_price[rb]
            # per tranche-hour arrays on the binding hours
            C = cap[sel][:, rb]
            F = fp[sel][:, rb]
            F_nb = fp_nobasis[sel][:, rb]
            F_np = fp_noplant[sel][:, rb]
            HHh = hh[rb][None, :]
            MCb = mc[sel][:, rb]
            BID = np.vstack(
                [bid_by_uid.get(u, np.full(HOURS, np.nan))[rb] for u in uids[sel]]
            )
            BID = np.where(np.isnan(BID), MCb, BID)
            fuel_leg = hr[sel][:, None] * F
            markup_leg = (mk[sel] * anchor)[:, None] * np.ones_like(F)
            vom_leg = vom[sel][:, None] * np.ones_like(F)
            start_leg = BID - MCb
            basis_inc = F - F_nb
            print_excess = (
                F_nb - HHh
            )  # the plant's 923-print premium over spot (fallback incl.)
            traj_vs_hh = F_np - HHh

            def cw(x, w):
                w = np.asarray(w, float)
                return float((x * w).sum() / w.sum()) if w.sum() > 0 else float("nan")

            # the idle-within-$20 block on the P1 bid
            idle = (
                (C > EPS) & (BID > ps[None, :] + EPS) & (BID <= ps[None, :] + IDLE_BAND)
            )
            econ = (C > EPS) & (BID <= ps[None, :] + EPS)
            Cidle = np.where(idle, C, 0.0)
            block_gw = float(Cidle.sum(axis=0).mean()) / 1e3
            comp_class = {
                c: round(float(Cidle[labels[sel] == c].sum(axis=0).mean()) / 1e3, 3)
                for c in sorted(set(labels[sel]))
            }
            comp_band = {
                b: round(float(Cidle[bands[sel] == b].sum(axis=0).mean()) / 1e3, 3)
                for b in sorted(set(bands[sel]))
            }
            legs_block = {
                "bid_p1": round(cw(BID, Cidle), 3),
                "mc_base": round(cw(MCb, Cidle), 3),
                "fuel_leg": round(cw(fuel_leg, Cidle), 3),
                "vom": round(cw(vom_leg, Cidle), 3),
                "markup_leg": round(cw(markup_leg, Cidle), 3),
                "startup_leg": round(cw(start_leg, Cidle), 3),
                "heat_rate_tr": round(
                    cw(np.broadcast_to(hr[sel][:, None], C.shape), Cidle), 3
                ),
                "F_delivered": round(cw(F, Cidle), 4),
                "F_minus_HH": round(cw(F - HHh, Cidle), 4),
                "basis_increment": round(cw(basis_inc, Cidle), 4),
                "print_excess_over_HH": round(cw(print_excess, Cidle), 4),
                "trajectory_minus_HH": round(cw(traj_vs_hh, Cidle), 4),
                "usd_per_mwh_basis_increment": round(
                    cw(hr[sel][:, None] * basis_inc, Cidle), 3
                ),
                "usd_per_mwh_print_excess": round(
                    cw(hr[sel][:, None] * print_excess, Cidle), 3
                ),
                "usd_per_mwh_fuel_vs_HH": round(
                    cw(hr[sel][:, None] * (F - HHh), Cidle), 3
                ),
                "south_price_mean": round(float(ps.mean()), 3),
                "hh_spot_mean": round(float(hh[rb].mean()), 4),
            }
            # whole South gas fleet fuel comparison (capacity-weighted, all available)
            Cav = np.where(C > EPS, C, 0.0)
            fleet_fuel = {
                "F_delivered_capw": round(cw(F, Cav), 4),
                "F_minus_HH_capw": round(cw(F - HHh, Cav), 4),
                "basis_increment_capw": round(cw(basis_inc, Cav), 4),
                "print_excess_capw": round(cw(print_excess, Cav), 4),
            }
            # Midwest gas for contrast
            selm = (
                (zones != "MISO-South")
                & ~np.char.startswith(zones.astype(str), "MISO_external")
                & np.isin(labels, list(GAS))
            )
            Cm = np.where(cap[selm][:, rb] > EPS, cap[selm][:, rb], 0.0)
            midwest_fuel = {
                "F_minus_HH_capw": round(cw(fp[selm][:, rb] - HHh, Cm), 4),
                "basis_increment_capw": round(
                    cw((fp[selm] - fp_nobasis[selm])[:, rb], Cm), 4
                ),
                "print_excess_capw": round(cw((fp_nobasis[selm][:, rb] - HHh), Cm), 4),
            }

            # ---- heat rates vs CAMPD burn, plant level, same hours
            campd_hr = campd_plant_hr(year, rb, states)
            d = pd.read_parquet(
                p.KEEPER / f"dispatch/{year}_P1.parquet",
                columns=["unit_id", "plant_code", "zone", "hour", "mw"],
            )
            d = d[(d["zone"] == "MISO-South") & d["hour"].isin(set(rb.tolist()))]
            hr_by_uid = dict(zip(uids, hr))
            d = d.assign(hr=d["unit_id"].astype(str).map(hr_by_uid))
            d = d[d["hr"].notna() & (d["mw"] > 0)]
            g = d.groupby("plant_code").apply(
                lambda s: pd.Series(
                    {
                        "disp_mwh": s["mw"].sum(),
                        "hr_dw": (s["mw"] * s["hr"]).sum() / s["mw"].sum(),
                    }
                )
            )
            hr_rows = []
            for code, row in g.iterrows():
                code = int(code)
                if code in campd_hr and code in set(plants[sel].tolist()):
                    hr_rows.append(
                        {
                            "plant": code,
                            "group": str(groups[plants == code][0])
                            if (plants == code).any()
                            else "",
                            "model_hr_dispatch_weighted": round(float(row["hr_dw"]), 3),
                            "campd_hr_burn": round(campd_hr[code], 3),
                            "ratio_model_over_campd": round(
                                float(row["hr_dw"]) / campd_hr[code], 4
                            ),
                            "model_disp_gwh": round(float(row["disp_mwh"]) / 1e3, 2),
                        }
                    )
            hr_df = pd.DataFrame(hr_rows)
            hr_summary = {}
            if not hr_df.empty:
                for grp, sub in hr_df.groupby("group"):
                    w = sub["model_disp_gwh"].to_numpy()
                    hr_summary[grp] = {
                        "plants": int(len(sub)),
                        "ratio_model_over_campd_dispw": round(
                            float((sub["ratio_model_over_campd"] * w).sum() / w.sum()),
                            4,
                        )
                        if w.sum()
                        else None,
                        "ratio_median": round(
                            float(sub["ratio_model_over_campd"].median()), 4
                        ),
                    }
            ratio_by_plant = {
                int(r["plant"]): float(r["ratio_model_over_campd"]) for r in hr_rows
            }

            # ---- static counterfactuals: capacity economic at the South price
            def econ_gw(bid_cf):
                e = (C > EPS) & (bid_cf <= ps[None, :] + EPS)
                return float(np.where(e, C, 0.0).sum(axis=0).mean()) / 1e3

            base_econ = econ_gw(BID)
            hr_ratio = np.array(
                [ratio_by_plant.get(int(pc), 1.0) for pc in plants[sel]]
            )
            cfs = {
                "baseline": BID,
                "a_fuel_to_HH_spot": BID - hr[sel][:, None] * (F - HHh),
                "b_basis_increment_removed": BID - hr[sel][:, None] * basis_inc,
                "c_hr_to_campd_burn": BID
                - hr[sel][:, None]
                * F
                * (1.0 - 1.0 / np.where(hr_ratio > 0, hr_ratio, 1.0))[:, None],
                "d_markup_zero (not measured)": BID - markup_leg,
                "e_startup_zero (not measured)": BID - start_leg,
                "a+b+c measured combined": BID
                - hr[sel][:, None] * (F - HHh)
                - hr[sel][:, None]
                * F
                * (1.0 - 1.0 / np.where(hr_ratio > 0, hr_ratio, 1.0))[:, None],
                "all legs (d+e too)": MCb - markup_leg - hr[sel][:, None] * (F - HHh),
            }
            model_gas = float(np.where(econ, C, 0.0).sum(axis=0).mean()) / 1e3
            meas_gas = (
                float(
                    np.nan_to_num(
                        p.regional_series(year, "gen", "South", fuel="Gas")[rb]
                    ).mean()
                )
                / 1e3
            )
            counterfactuals = {
                name: {
                    "economic_gw_at_south_price": round(econ_gw(b), 3),
                    "recovered_gw_vs_baseline": round(econ_gw(b) - base_econ, 3),
                }
                for name, b in cfs.items()
            }

            # mc of the marginal MW at the measured gas level, per counterfactual
            def mc_at_measured(bid_cf):
                vals = []
                for j in range(rb.size):
                    order = np.argsort(bid_cf[:, j])
                    cum = np.cumsum(C[order, j])
                    jj_ = int(np.searchsorted(cum, meas_gas * 1e3))
                    vals.append(float(bid_cf[order, j][min(jj_, len(order) - 1)]))
                return float(np.median(vals))

            for name, b in cfs.items():
                counterfactuals[name]["bid_p50_at_measured_gas_level"] = round(
                    mc_at_measured(b), 2
                )

            # ---- the market's own South stack (RT offers, Region South)
            stacks = offer_stack_south(year, rb)
            offer_block = {"hours_with_offers": len(stacks)}
            if stacks:
                gen_s = p.regional_series(year, "gen", "South")
                # the model's whole South supply curve (all fuels) in the same hours
                sel_s = zones == "MISO-South"
                p_at_meas, p_at_meas_model, mw_at_price, mw_at_price_model = (
                    [],
                    [],
                    [],
                    [],
                )
                for h in rb:
                    if int(h) not in stacks:
                        continue
                    st = stacks[int(h)]
                    q = float(np.nan_to_num(gen_s[h]))
                    p_at_meas.append(_price_at(st, q))
                    mw_at_price.append(_mw_at(st, float(south_price[h])))
                    order = np.argsort(mc[sel_s, h])
                    cum = np.cumsum(cap[sel_s, h][order])
                    jq = int(np.searchsorted(cum, q))
                    p_at_meas_model.append(
                        float(mc[sel_s, h][order][min(jq, len(order) - 1)])
                    )
                    mw_at_price_model.append(
                        float(cap[sel_s, h][mc[sel_s, h] <= south_price[h] + EPS].sum())
                    )
                offer_block.update(
                    {
                        "measured_south_gen_gw_mean": round(
                            float(np.nanmean(gen_s[rb])) / 1e3, 3
                        ),
                        "offer_price_at_measured_gen_p50": round(
                            float(np.median(p_at_meas)), 2
                        ),
                        "offer_price_at_measured_gen_mean": round(
                            float(np.mean(p_at_meas)), 2
                        ),
                        "model_mc_at_measured_gen_p50": round(
                            float(np.median(p_at_meas_model)), 2
                        ),
                        "offered_mw_at_model_south_price_gw_mean": round(
                            float(np.mean(mw_at_price)) / 1e3, 3
                        ),
                        "model_capability_at_model_south_price_gw_mean": round(
                            float(np.mean(mw_at_price_model)) / 1e3, 3
                        ),
                        "actual_south_hubs_mean": round(
                            float(np.nanmean(south_act[rb])), 2
                        ),
                        "model_south_price_mean": round(float(ps.mean()), 2),
                    }
                )

            yrec[k] = {
                "hours_real_s2n": int(rb.size),
                "model_south_gas_economic_gw": round(model_gas, 3),
                "measured_south_gas_gw": round(meas_gas, 3),
                "idle_within_20_block_gw": round(block_gw, 3),
                "block_composition_by_class_gw": comp_class,
                "block_composition_by_band_gw": comp_band,
                "block_legs_capw": legs_block,
                "south_gas_fleet_fuel_capw": fleet_fuel,
                "midwest_gas_fleet_fuel_capw": midwest_fuel,
                "heat_rate_vs_campd_by_group": hr_summary,
                "heat_rate_plants": hr_rows[:40],
                "counterfactuals": counterfactuals,
                "market_offers_south": offer_block,
            }
            print(
                year,
                k,
                json.dumps(
                    {
                        kk: yrec[k][kk]
                        for kk in (
                            "idle_within_20_block_gw",
                            "block_composition_by_class_gw",
                            "block_composition_by_band_gw",
                            "block_legs_capw",
                        )
                    },
                    default=str,
                )[:1500],
                flush=True,
            )
            print(
                year, k, "fleet fuel", fleet_fuel, "midwest", midwest_fuel, flush=True
            )
            print(year, k, "HR", json.dumps(hr_summary), flush=True)
            print(
                year,
                k,
                "CF",
                json.dumps(counterfactuals, default=str)[:1200],
                flush=True,
            )
            print(
                year,
                k,
                "OFFERS",
                json.dumps(offer_block, default=str)[:800],
                flush=True,
            )
        rep["years"][year] = yrec
        OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
