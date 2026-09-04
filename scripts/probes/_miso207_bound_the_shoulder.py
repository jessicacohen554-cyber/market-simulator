"""miso-207 phase 0 — BOUND THE SHOULDER: every live lever re-bounded against the
p75-p99 Jun-Jul population AND the 15-hour tail (zero-solve).

miso-206 §8 established, on the C3a comparator (INDIANA.HUB RT on the model's
fixed-CST clock), that the Jun-Jul 2025 gap is HALF a 15-hour tail and HALF a
351-hour p75-p99 daytime SHOULDER, and that every bound argued "at the object's
own hours" since miso-202 was argued against the tail half only.  This probe
measures, per population and per year, what the keeper's OWN stack looks like
there — the price-setting tranche, the idle capability priced just above the
clearing price, the reserve margins, the seam import excess, the ramp, the DA
share of the gap — so each of the charter's four items can be bounded against
the population it would actually have to reach.

Instrument: the production fleet chain at HEAD through
``_miso134_ct_night_order_screen.build_year`` (BUNDLE re-pointed to the
miso-202 keeper, ``weather_year`` pinned to the solve year — the miso-153 T-6
repair), interrogated against the keeper's committed ``hourly/`` sidecars.
Two caveats, stated in the PREREG and carried on every number: ``mc_base`` is
the P0 base cost (the P1 startup markup is absent), and the chain passes ``[]``
for the retiree-channel units and import generators — so T-6 feasibility is
asserted per population and violations are reported, never hidden.

PREREG ``results/calibration/PREREG-miso207-bound-the-shoulder-2026-09-04.md``,
pushed at ``e5f179d8`` BEFORE any statistic on the shoulder population.
Every input is a committed artifact or a production loader; **no LP is
solved**.  Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso207_bound_the_shoulder.py
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

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso202_unitclip_B"
_m134.BUNDLE = KEEPER  # T-1: re-point BEFORE any helper runs
from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)

ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
ANATOMY = REPO / "results/calibration/_miso202_c3a_2025_anatomy.json"
M205 = REPO / "results/calibration/_miso205_ge_repaired_clock.json"
MARGINS = REPO / "results/calibration/_miso203_summer_peak_anchor_phase0.json"
OUT = REPO / "results/calibration/_miso207_bound_the_shoulder.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
SCORING_HUB = "INDIANA.HUB"
CARRY_ZONES = (
    "MISO-East",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-Plains",
    "MISO-South",
    "MISO-West",
)
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "COAL")
COAL_POOL = "COAL_FAMILY"
ARMED_CLASSES = ("CT_PEAKER", "CC_REGULAR")
NON_THERMAL = ("wind", "solar", "hydro", "nuclear", "import", "biomass", "oil", "OTHER")
MONTH_LENS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
IDLE_BANDS = (20.0, 50.0, 100.0)
TOPN = 200
# miso-153 headline, the N-4 bridge.
M153_CT_TOP200 = {2023: 40.0, 2024: 42.6, 2025: 66.0}
M205_THRESHOLDS = {2023: 121.43, 2024: 159.01, 2025: 373.02}
T6_CELL_TOL = 0.01
T6_MAG_TOL = 0.02
LICENSE_LINE = 0.25


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month per hour on the model's FIXED non-leap 8760 clock."""
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(MONTH_LENS)])[
        :hours
    ]


def _stamp(year: int, h: int) -> str:
    doy, hod = divmod(int(h), 24)
    m = 0
    while doy >= MONTH_LENS[m]:
        doy -= MONTH_LENS[m]
        m += 1
    return f"{year}-{m + 1:02d}-{doy + 1:02d} HE{hod + 1:02d}"


def _band_of(unit_id: str) -> str:
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", unit_id)
    return m.group(2) if m else ""


def _band_family(suffix: str) -> str:
    for key in ("mustrun", "committed", "econ", "peak"):
        if suffix.startswith(key):
            return key
    return suffix or "?"


def class_label(g) -> str:
    """The class_hourly klass of one assembled generator; coal POOLED."""
    group = str(g.plant_group or "")
    return COAL_POOL if group == "COAL" else group


def hub_series(zon: pd.DataFrame, year: int, col: str) -> np.ndarray:
    s = zon[(zon.year == year) & (zon.hub == SCORING_HUB)].sort_values("hour")
    arr = np.full(HOURS, np.nan)
    idx = s["hour"].to_numpy(int)
    keep = idx < HOURS
    arr[idx[keep]] = s[col].to_numpy(float)[keep]
    return arr


def keeper_class_hourly(year: int) -> pd.DataFrame:
    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    wide = ch.pivot_table(
        index="klass", columns="hour", values="mw", observed=True, aggfunc="sum"
    ).fillna(0.0)
    full = pd.DataFrame(0.0, index=wide.index, columns=np.arange(HOURS))
    full.loc[:, wide.columns] = wide
    present = [c for c in COAL_CLASSES if c in full.index]
    if present:
        pooled = full.loc[present].sum(axis=0)
        full = full.drop(index=present)
        full.loc[COAL_POOL] = pooled
    return full


def reserve_frame(year: int) -> pd.DataFrame:
    rf = pd.read_parquet(KEEPER / f"hourly/reserve_family_{year}.parquet")
    return rf[rf["pass"] == "P1"]


def _gap_block(idx, price_lw, price_zm, rt, da) -> dict:
    m_rt = float(rt[idx].mean())
    m_da = float(np.nanmean(da[idx]))
    m_lw = float(price_lw[idx].mean())
    gap = m_lw - m_rt
    return {
        "n_hours": int(idx.size),
        "actual_rt_mean": round(m_rt, 2),
        "actual_da_mean": round(m_da, 2),
        "model_lw_mean": round(m_lw, 2),
        "model_zone_mean": round(float(price_zm[idx].mean()), 2),
        "gap_lw_minus_rt": round(gap, 3),
        "gap_lw_minus_da": round(m_lw - m_da, 3),
        "da_minus_rt": round(m_da - m_rt, 3),
        "da_foreseen_share_of_gap": (
            round((m_lw - m_da) / gap, 4) if abs(gap) > 1e-9 else None
        ),
        "actual_rt_p50": round(float(np.median(rt[idx])), 2),
        "actual_rt_min": round(float(rt[idx].min()), 2),
        "actual_rt_max": round(float(rt[idx].max()), 2),
        "model_lw_p50": round(float(np.median(price_lw[idx])), 2),
        "model_lw_max": round(float(price_lw[idx].max()), 2),
        "hour_of_day_mean": round(float((idx % 24).mean()), 2),
    }


def _setter_and_cushion(
    idx, mc, avail_mw, labels, suffix, zones, price_df, rt_series
) -> dict:
    """The miso-153 D-3 construction over one population, per carry zone."""
    setter: dict[str, float] = {}
    n_obs = 0
    price_gap: list[float] = []
    dearest_mc: list[float] = []
    actual_over_dearest = 0
    idle: dict[float, dict[str, float]] = {b: {} for b in IDLE_BANDS}
    idle_total: dict[float, np.ndarray] = {b: np.zeros(idx.size) for b in IDLE_BANDS}
    zone_hours = 0
    for z in CARRY_ZONES:
        zsel = zones == z
        if not zsel.any() or z not in price_df.columns:
            continue
        mc_z = mc[zsel][:, idx]
        av_z = avail_mw[zsel][:, idx]
        lab_z = labels[zsel]
        suf_z = suffix[zsel]
        p_z = price_df[z].to_numpy()[idx][None, :]
        in_merit = (mc_z <= p_z + 1e-6) & (av_z > 1e-6)
        masked = np.where(in_merit, mc_z, -np.inf)
        top = masked.argmax(axis=0)
        has = np.isfinite(masked[top, np.arange(idx.size)])
        for h in range(idx.size):
            zone_hours += 1
            if not has[h]:
                continue
            key = f"{lab_z[top[h]]}|{suf_z[top[h]]}"
            setter[key] = setter.get(key, 0.0) + 1.0
            n_obs += 1
            price_gap.append(float(p_z[0, h] - mc_z[top[h], h]))
            dearest_mc.append(float(mc_z[top[h], h]))
            if rt_series[idx[h]] > mc_z[top[h], h] + 20.0:
                actual_over_dearest += 1
        for b in IDLE_BANDS:
            band = (mc_z > p_z + 1e-6) & (mc_z <= p_z + b) & (av_z > 1e-6)
            for k in np.unique(lab_z):
                m = band[lab_z == k]
                mw = np.where(m, av_z[lab_z == k], 0.0).sum(axis=0)
                idle[b][k] = idle[b].get(k, 0.0) + float(mw.mean())
                idle_total[b] += mw
    census = (
        {
            k: round(v / n_obs, 4)
            for k, v in sorted(setter.items(), key=lambda kv: -kv[1])
        }
        if n_obs
        else {}
    )
    by_class: dict[str, float] = {}
    for key, share in census.items():
        k = key.split("|")[0]
        by_class[k] = round(by_class.get(k, 0.0) + share, 4)
    return {
        "n_zone_hour_obs": n_obs,
        "n_zone_hours": zone_hours,
        "setter_class_share": dict(sorted(by_class.items(), key=lambda kv: -kv[1])),
        "setter_band_share_top8": dict(list(census.items())[:8]),
        "price_minus_setter_mc_mean": round(float(np.mean(price_gap)), 3)
        if price_gap
        else None,
        "setter_mc_mean": round(float(np.mean(dearest_mc)), 2) if dearest_mc else None,
        "setter_mc_p90": round(float(np.percentile(dearest_mc, 90)), 2)
        if dearest_mc
        else None,
        "share_zone_hours_actual_rt_over_setter_mc_by_20": (
            round(actual_over_dearest / n_obs, 4) if n_obs else None
        ),
        "idle_mw_within_band_above_price_by_class": {
            str(int(b)): dict(sorted(idle[b].items(), key=lambda kv: -kv[1]))
            for b in IDLE_BANDS
        },
        "idle_gw_within_band_above_price_total_mean": {
            str(int(b)): round(float(idle_total[b].mean()) / 1000.0, 3)
            for b in IDLE_BANDS
        },
        "idle_gw_within_band_above_price_total_min": {
            str(int(b)): round(float(idle_total[b].min()) / 1000.0, 3)
            for b in IDLE_BANDS
        },
    }


def _margins(idx, avail_mw, labels, ch, rf) -> dict:
    thermal = [k for k in np.unique(labels) if k in GAS_CLASSES or k == COAL_POOL]
    av_tot = np.zeros(idx.size)
    dp_tot = np.zeros(idx.size)
    av_armed = np.zeros(idx.size)
    dp_armed = np.zeros(idx.size)
    for k in thermal:
        av = avail_mw[labels == k][:, idx].sum(axis=0)
        dp = ch.loc[k, idx].to_numpy() if k in ch.index else np.zeros(idx.size)
        av_tot += av
        dp_tot += dp
        if k in ARMED_CLASSES:
            av_armed += av
            dp_armed += dp
    req = np.zeros(idx.size)
    for _fam, g in rf.groupby("family", observed=True):
        r = g.set_index("hour")["requirement_mw"].reindex(idx).fillna(0.0).to_numpy()
        req += r
    broad = av_tot - dp_tot - req
    armed = av_armed - dp_armed
    return {
        "thermal_avail_gw_mean": round(float(av_tot.mean()) / 1000.0, 3),
        "thermal_dispatch_gw_mean": round(float(dp_tot.mean()) / 1000.0, 3),
        "reserve_requirement_gw_mean": round(float(req.mean()) / 1000.0, 3),
        "margin_broad_gw_mean": round(float(broad.mean()) / 1000.0, 3),
        "margin_broad_gw_min": round(float(broad.min()) / 1000.0, 3),
        "idle_armed_classes_gw_mean": round(float(armed.mean()) / 1000.0, 3),
        "idle_armed_classes_gw_min": round(float(armed.min()) / 1000.0, 3),
    }


def _t6(idx, avail_mw, labels, ch) -> dict:
    thermal = [k for k in np.unique(labels) if k in GAS_CLASSES or k == COAL_POOL]
    cells = viol = 0
    worst = 0.0
    worst_k = ""
    per = {}
    for k in thermal:
        av = avail_mw[labels == k][:, idx].sum(axis=0)
        dp = ch.loc[k, idx].to_numpy() if k in ch.index else np.zeros(idx.size)
        over = dp - av
        cap = float(avail_mw[labels == k].max(axis=1).sum()) or 1.0
        nv = int((over > 1e-6).sum())
        mx = float(over.max() / cap)
        per[k] = {"violations": nv, "max_viol_share_of_cap": round(mx, 5)}
        cells += idx.size
        viol += nv
        if mx > worst:
            worst, worst_k = mx, k
    return {
        "cells": cells,
        "violations": viol,
        "violation_share": round(viol / cells, 5) if cells else None,
        "max_viol_share_of_cap": round(worst, 5),
        "worst_class": worst_k,
        "PASS": bool(
            (viol / cells if cells else 0) <= T6_CELL_TOL and worst <= T6_MAG_TOL
        ),
        "per_class": per,
    }


def _reserve_binding(idx, rf) -> dict:
    out = {}
    for fam, g in rf.groupby("family", observed=True):
        g = g.set_index("hour")
        d = g["dual"].reindex(idx).fillna(0.0).to_numpy()
        s = g["shortfall_mw"].reindex(idx).fillna(0.0).to_numpy()
        out[str(fam)] = {
            "bind_hours": int((np.abs(d) > 0.01).sum()),
            "short_hours": int((s > 1e-6).sum()),
            "dual_max": round(float(np.abs(d).max()), 2),
        }
    return out


def _seam_reprice(idx, mc, avail_mw, zones, price_df, import_excess_mw) -> dict:
    """P4: re-price the population's import excess up the model's own idle
    census (ISO-wide, carry zones pooled): the price after removing X MW of
    supply is the mc of the X-th idle MW above the current price."""
    lifts = []
    for h_i, h in enumerate(idx):
        col_mc = []
        col_av = []
        for z in CARRY_ZONES:
            zsel = zones == z
            if not zsel.any() or z not in price_df.columns:
                continue
            p = float(price_df[z].to_numpy()[h])
            m = mc[zsel, h]
            a = avail_mw[zsel, h]
            sel = (m > p + 1e-6) & (a > 1e-6)
            col_mc.append(m[sel])
            col_av.append(a[sel])
        m_all = np.concatenate(col_mc) if col_mc else np.zeros(0)
        a_all = np.concatenate(col_av) if col_av else np.zeros(0)
        order = np.argsort(m_all)
        cum = np.cumsum(a_all[order])
        p_now = float(
            np.mean(
                [
                    price_df[z].to_numpy()[h]
                    for z in CARRY_ZONES
                    if z in price_df.columns
                ]
            )
        )
        k = int(np.searchsorted(cum, import_excess_mw))
        p_new = float(m_all[order][min(k, len(order) - 1)]) if len(order) else p_now
        lifts.append(max(0.0, p_new - p_now))
    lifts = np.asarray(lifts)
    return {
        "import_excess_mw_repriced": round(float(import_excess_mw), 1),
        "lift_usd_mean": round(float(lifts.mean()), 3),
        "lift_usd_p50": round(float(np.median(lifts)), 3),
        "lift_usd_p90": round(float(np.percentile(lifts, 90)), 3),
    }


def _night_hole(idx, mc, avail_mw, labels, ch, demand, rt) -> dict:
    """P5: the model's in-merit thermal supply at the ACTUAL night price plus
    its own non-thermal dispatch, against demand — the overnight supply hole."""
    thermal_sel = np.isin(labels, list(GAS_CLASSES) + [COAL_POOL])
    holes = []
    for h in idx:
        p_act = float(rt[h])
        m = mc[thermal_sel, h]
        a = avail_mw[thermal_sel, h]
        in_merit = float(a[m <= p_act].sum())
        non_thermal = float(sum(ch.loc[k, h] for k in NON_THERMAL if k in ch.index))
        # storage discharge is in class_hourly? not a klass — read separately
        holes.append(float(demand[h]) - in_merit - non_thermal)
    holes = np.asarray(holes)
    return {
        "hole_gw_mean": round(float(holes.mean()) / 1000.0, 3),
        "hole_gw_p10": round(float(np.percentile(holes, 10)) / 1000.0, 3),
        "hole_gw_p90": round(float(np.percentile(holes, 90)) / 1000.0, 3),
        "note": (
            "demand minus (thermal capability priced at or below the ACTUAL "
            "INDIANA.HUB RT price + the keeper's own non-thermal dispatch incl. "
            "import); positive = the model cannot clear at the actual price"
        ),
    }


def main() -> None:  # noqa: PLR0915
    zon = pd.read_parquet(ZONAL)
    anat = json.loads(ANATOMY.read_text())
    m205 = json.loads(M205.read_text())["years"]
    margins203 = json.loads(MARGINS.read_text())["g_d_reserve_binding"]
    cfg0 = keeper_config()
    mon = _hour_month()
    jj_mask = np.isin(mon, (6, 7))
    jj = np.where(jj_mask)[0]
    hod = np.arange(HOURS) % 24

    report: dict = {
        "charter": "miso-207 phase 0 — bound the shoulder; zero-solve; nothing armed.",
        "prereg": "results/calibration/PREREG-miso207-bound-the-shoulder-2026-09-04.md @ e5f179d8",
        "keeper": "2026-09-03-miso-202-unitclip",
        "instrument": (
            "fleet via _miso134.build_year re-pointed to miso202_unitclip_B, "
            "weather_year pinned per year; mc_base = P0 base cost (no P1 startup "
            "markup); [] retirees / import generators (T-6 asserted per population)"
        ),
        "years": {},
    }

    for year in YEARS:
        y: dict = {}
        rt = hub_series(zon, year, "rt")
        da = hub_series(zon, year, "da")
        price_df, demand = keeper_prices(year)
        price_df = price_df.reindex(range(HOURS))
        carry = [z for z in CARRY_ZONES if z in price_df.columns]
        sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
        den = sysd.groupby("hour")["demand"].sum()
        price_lw = (num / den).reindex(range(HOURS)).to_numpy()
        price_zm = price_df[carry].mean(axis=1).to_numpy()
        ch = keeper_class_hourly(year)
        rf = reserve_frame(year)

        # ---- populations --------------------------------------------------
        a = rt[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        body_low = jj[rank < 50.0]
        night = body_low[np.isin(hod[body_low], range(0, 6))]
        other_jj_for_shoulder = np.array(sorted(set(jj) - set(shoulder) - set(tail)))
        day_other = other_jj_for_shoulder[
            np.isin(hod[other_jj_for_shoulder], range(10, 21))
        ]
        bands = {
            "p75-90": jj[(rank >= 75.0) & (rank < 90.0)],
            "p90-95": jj[(rank >= 90.0) & (rank < 95.0)],
            "p95-99": jj[(rank >= 95.0) & (a < thr99)],
        }
        pops = {
            "SHOULDER": shoulder,
            "TAIL": tail,
            "BODY_LOW": body_low,
            "NIGHT": night,
        }
        stamps = [_stamp(year, h) for h in sorted(tail.tolist())]
        y["n1_tail_reproduces_miso205"] = {
            "threshold": round(thr99, 2),
            "miso205_threshold": M205_THRESHOLDS[year],
            "n_tail": int(tail.size),
            "n_shoulder": int(shoulder.size),
            "stamps_match": bool(
                m205[str(year)]["n1_reproduces_miso204_object_set"].get("stamps")
                in (None, stamps)
            ),
        }
        # N-2: band contributions reproduce the anatomy's a2b
        a2b = anat["a2_distribution"][str(year)][
            "a2b_band_contributions__POSTHOC_miso206"
        ]["indiana_hub__model_load_weighted"]
        mine = {}
        for lo, hi in ((0, 50), (50, 75), (75, 90), (90, 95), (95, 99), (99, 100)):
            sel = (rank >= lo) & (rank < hi) if hi < 100 else rank >= lo
            mine[f"p{lo}-{hi}"] = round(
                float((price_lw[jj][sel] - a[sel]).sum() / len(a)), 3
            )
        y["n2_band_contributions_reproduce_a2b"] = {
            "mine": mine,
            "a2b": {k: a2b[k] for k in mine},
            "max_abs_diff": round(max(abs(mine[k] - a2b[k]) for k in mine), 4),
        }

        # ---- gaps per population -----------------------------------------
        y["gaps"] = {
            k: _gap_block(v, price_lw, price_zm, rt, da) for k, v in pops.items()
        }
        y["gaps_shoulder_bands"] = {
            k: _gap_block(v, price_lw, price_zm, rt, da) for k, v in bands.items()
        }
        # T4: DA-defined shoulder overlap with the RT-defined one
        d = da[jj]
        rank_da = (np.nan_to_num(d, nan=-1).argsort().argsort() / len(d)) * 100.0
        sh_da = jj[(rank_da >= 75.0) & (rank_da < 99.0)]
        y["t4_da_defined_shoulder_overlap"] = {
            "n_da_shoulder": int(sh_da.size),
            "n_overlap_with_rt_shoulder": int(
                len(set(sh_da.tolist()) & set(shoulder.tolist()))
            ),
        }
        y["shoulder_hour_of_day_histogram"] = {
            str(int(x)): int(c)
            for x, c in zip(*np.unique(hod[shoulder], return_counts=True))
        }
        y["shoulder_n_distinct_days"] = int(len(set((shoulder // 24).tolist())))

        # ---- the fleet, production chain ----------------------------------
        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, dtype=np.float64)
        labels = np.array([class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        suffix = np.array(
            [_band_family(_band_of(str(g.unit_id))) for g in fleet], dtype=object
        )
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        pmax = np.asarray(arrays.pmax, dtype=np.float64)
        avail_mw = pmax[:, None] * avail

        # ---- N-3 T-6 per population; N-4 the miso-153 bridge --------------
        y["n3_t6_feasibility"] = {
            k: _t6(v, avail_mw, labels, ch) for k, v in pops.items()
        }
        top200 = np.sort(np.argsort(demand)[::-1][:TOPN])
        n4 = _setter_and_cushion(
            top200, mc, avail_mw, labels, suffix, zones, price_df, rt
        )
        y["n4_top200_demand_setter_census"] = {
            "setter_class_share": n4["setter_class_share"],
            "ct_peaker_share_pct": round(
                100.0 * n4["setter_class_share"].get("CT_PEAKER", 0.0), 1
            ),
            "miso153_ct_peaker_pct": M153_CT_TOP200[year],
            "price_minus_setter_mc_mean": n4["price_minus_setter_mc_mean"],
        }

        # ---- setter census + cushion per population and per band ----------
        y["setter_and_cushion"] = {
            k: _setter_and_cushion(v, mc, avail_mw, labels, suffix, zones, price_df, rt)
            for k, v in pops.items()
        }
        y["setter_and_cushion_shoulder_bands"] = {
            k: _setter_and_cushion(v, mc, avail_mw, labels, suffix, zones, price_df, rt)
            for k, v in bands.items()
        }
        # ---- margins ------------------------------------------------------
        y["margins"] = {
            k: _margins(v, avail_mw, labels, ch, rf) for k, v in pops.items()
        }
        y["margins"]["TAIL"]["miso203_broad_min_mw"] = margins203[str(year)][
            "margin_broad_mw_min_scarce"
        ]
        y["margins"]["TAIL"]["miso203_armed_idle_mw"] = margins203[str(year)][
            "idle_armed_classes_mw_mean_scarce"
        ]

        # ---- reserve binding ---------------------------------------------
        y["reserve_binding"] = {k: _reserve_binding(v, rf) for k, v in pops.items()}
        y["reserve_binding"]["ALL_JUN_JUL"] = _reserve_binding(jj, rf)

        # ---- item 1: the seam in the shoulder ----------------------------
        imp = ch.loc["import"].to_numpy() if "import" in ch.index else np.zeros(HOURS)
        seam = {}
        for k, v in pops.items():
            other = np.array(sorted(set(jj) - set(v)))
            seam[k] = {
                "import_mean_mw": round(float(imp[v].mean()), 1),
                "other_jun_jul_mean_mw": round(float(imp[other].mean()), 1),
                "excess_mw": round(float(imp[v].mean() - imp[other].mean()), 1),
            }
        y["item1_seam_import"] = seam
        ex_sh = max(0.0, seam["SHOULDER"]["excess_mw"])
        ex_tl = max(0.0, seam["TAIL"]["excess_mw"])
        y["item1_seam_reprice"] = {
            "SHOULDER": _seam_reprice(shoulder, mc, avail_mw, zones, price_df, ex_sh),
            "TAIL": _seam_reprice(tail, mc, avail_mw, zones, price_df, ex_tl),
        }
        for k in ("SHOULDER", "TAIL"):
            g = abs(y["gaps"][k]["gap_lw_minus_rt"])
            y["item1_seam_reprice"][k]["lift_share_of_gap"] = (
                round(y["item1_seam_reprice"][k]["lift_usd_mean"] / g, 4) if g else None
            )

        # ---- item 3: the night side --------------------------------------
        y["item3_night_hole"] = _night_hole(night, mc, avail_mw, labels, ch, demand, rt)
        y["item3_night_hour_profile_gap"] = {
            str(h): round(
                float(
                    (
                        price_lw[body_low[hod[body_low] == h]]
                        - rt[body_low[hod[body_low] == h]]
                    ).mean()
                ),
                2,
            )
            for h in range(24)
            if (hod[body_low] == h).any()
        }

        # ---- item 4: ramp ------------------------------------------------
        wind = ch.loc["wind"].to_numpy() if "wind" in ch.index else np.zeros(HOURS)
        solar = ch.loc["solar"].to_numpy() if "solar" in ch.index else np.zeros(HOURS)
        netload = demand - wind - solar
        ramp3 = np.full(HOURS, np.nan)
        ramp3[3:] = netload[3:] - netload[:-3]
        r_sh = float(np.nanmean(np.abs(ramp3[shoulder])))
        r_day = float(np.nanmean(np.abs(ramp3[day_other])))
        y["item4_ramp"] = {
            "shoulder_abs_3h_ramp_mean_mw": round(r_sh, 0),
            "other_jun_jul_daytime_abs_3h_ramp_mean_mw": round(r_day, 0),
            "ratio": round(r_sh / r_day, 3) if r_day else None,
            "shoulder_signed_3h_ramp_mean_mw": round(
                float(np.nanmean(ramp3[shoulder])), 0
            ),
            "tail_signed_3h_ramp_mean_mw": round(float(np.nanmean(ramp3[tail])), 0),
        }

        # ---- per-shoulder-hour table (T6) ---------------------------------
        rows = []
        for h in sorted(shoulder.tolist()):
            rows.append(
                {
                    "hour": int(h),
                    "stamp": _stamp(year, h),
                    "rt": round(float(rt[h]), 2),
                    "da": round(float(da[h]), 2) if np.isfinite(da[h]) else None,
                    "model_lw": round(float(price_lw[h]), 2),
                    "demand": round(float(demand[h]), 0),
                    "import_mw": round(float(imp[h]), 0),
                }
            )
        y["shoulder_hours"] = rows
        report["years"][str(year)] = y
        del mc, avail_mw, avail, arrays, fleet

    # ---- verdicts against the PREREG rules ----------------------------------
    d25 = report["years"]["2025"]
    sh = d25["setter_and_cushion"]["SHOULDER"]
    mg = d25["margins"]["SHOULDER"]
    report["verdict"] = {
        "P1_shoulder_gap_lw_minus_rt_2025": d25["gaps"]["SHOULDER"]["gap_lw_minus_rt"],
        "P1_da_foreseen_share_2025": d25["gaps"]["SHOULDER"][
            "da_foreseen_share_of_gap"
        ],
        "P2_shoulder_setter_2025": sh["setter_class_share"],
        "P2_setter_differs_from_tail_by_20pp": bool(
            abs(
                sh["setter_class_share"].get("CT_PEAKER", 0.0)
                - d25["setter_and_cushion"]["TAIL"]["setter_class_share"].get(
                    "CT_PEAKER", 0.0
                )
            )
            >= 0.20
        ),
        "P3_idle_gw_within_20_50_100_2025": sh[
            "idle_gw_within_band_above_price_total_mean"
        ],
        "P3_margin_broad_gw_mean_min_2025": [
            mg["margin_broad_gw_mean"],
            mg["margin_broad_gw_min"],
        ],
        "P4_seam_lift_share_of_shoulder_gap_2025": d25["item1_seam_reprice"][
            "SHOULDER"
        ]["lift_share_of_gap"],
        "P4_refuse_as_lever": bool(
            (d25["item1_seam_reprice"]["SHOULDER"]["lift_share_of_gap"] or 0.0)
            < LICENSE_LINE
        ),
        "P5_night_hole_gw_2025": d25["item3_night_hole"]["hole_gw_mean"],
        "P5_night_is_supply_quantity_object": bool(
            d25["item3_night_hole"]["hole_gw_mean"] >= 2.0
        ),
        "P6_ramp_ratio_2025": d25["item4_ramp"]["ratio"],
        "P6_refuse_ramp": bool(
            (d25["item4_ramp"]["ratio"] or 0.0) < 1.5
            and sum(
                v["bind_hours"] for v in d25["reserve_binding"]["SHOULDER"].values()
            )
            <= 10
        ),
        "P9_nothing_reaches_the_shoulder": None,
    }
    report["verdict"]["P9_nothing_reaches_the_shoulder"] = bool(
        report["verdict"]["P4_refuse_as_lever"] and report["verdict"]["P6_refuse_ramp"]
    )
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    for yy in YEARS:
        d = report["years"][str(yy)]
        print(
            f"{yy}: N-1 thr {d['n1_tail_reproduces_miso205']['threshold']} stamps {d['n1_tail_reproduces_miso205']['stamps_match']} | "
            f"N-2 max|diff| {d['n2_band_contributions_reproduce_a2b']['max_abs_diff']} | "
            f"T-6 {[d['n3_t6_feasibility'][k]['PASS'] for k in ('SHOULDER', 'TAIL', 'BODY_LOW', 'NIGHT')]} | "
            f"N-4 CT {d['n4_top200_demand_setter_census']['ct_peaker_share_pct']} vs {d['n4_top200_demand_setter_census']['miso153_ct_peaker_pct']}"
        )
        for k in ("SHOULDER", "TAIL", "NIGHT"):
            g = d["gaps"][k]
            s = d["setter_and_cushion"][k]
            m = d["margins"][k]
            print(
                f"   {k:8s} n={g['n_hours']} rt {g['actual_rt_mean']} da {g['actual_da_mean']} model {g['model_lw_mean']} gap {g['gap_lw_minus_rt']} DAshare {g['da_foreseen_share_of_gap']} | "
                f"setter {dict(list(s['setter_class_share'].items())[:3])} p-mc {s['price_minus_setter_mc_mean']} actual>mc+20 {s['share_zone_hours_actual_rt_over_setter_mc_by_20']} | "
                f"idle20/50/100 {s['idle_gw_within_band_above_price_total_mean']} | broad {m['margin_broad_gw_mean']}/{m['margin_broad_gw_min']} armed {m['idle_armed_classes_gw_mean']} | "
                f"seam {d['item1_seam_import'][k]['excess_mw']}"
            )
        print(
            f"   seam reprice {d['item1_seam_reprice']} | night hole {d['item3_night_hole']['hole_gw_mean']} | ramp {d['item4_ramp']} | binding {d['reserve_binding']['SHOULDER']}"
        )
    print(json.dumps(report["verdict"], indent=1))


if __name__ == "__main__":
    main()
