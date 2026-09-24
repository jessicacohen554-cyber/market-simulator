#!/usr/bin/env python3
"""miso-269 phase 0: what does the OWNER-RULED gas convention do to the two held-out objects?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Nothing is solved. For each year the
designated keeper's fleet/offer arrays are rebuilt twice with
``run_year(..., fleet_only=True)`` — the keeper's own recipe (control) and the
same recipe with the owner-ruled MISO gas convention armed
(``miso_gas_marginal_commodity_pricing`` + ``miso_gas_variable_transport``,
ruling of 2026-09-06 on miso-212 §8 / miso-224 §5: "marginal commodity PLUS
variable transport"). The per-row, per-hour offer difference ``dmc`` is the
measured array difference, never a formula.

STATIC RE-MERIT (a magnitude report, NOT a decision input — rule 1). In every
internal zone-hour the keeper's P1 dual is matched to the live rows whose
control ``mc`` lies within ``TOL`` of it (zone-local first, else pooled), and
the zone-hour's predicted price move is the mean ``dmc`` of those rows. That
ignores re-dispatch, so it is an upper bound on the price move: miso-225
measured the LP realizing 64 % of its static on 2023.

WHAT IT REPORTS per year: the keeper's and the static-armed load-weighted
annual price error against zonal RT (the C3a quantity), the monthly
load-weighted NRMSE (the C3b quantity), the hour-of-day error profile (the
overnight object), the monthly error, and the matched share. Also the
capacity-weighted gas price per month, control vs armed, for the gas rows.

Usage::

    uv run python scripts/probes/_miso269_transport_static_phase0.py --years 2020 2021 2023
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.fuel.basis.miso import _GAS_FUEL_IDX  # noqa: E402
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results/calibration/miso268_yard_span"
OUT = REPO / "results/calibration/_miso269_transport_static_phase0.json"
ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")
INTERNAL = (
    "MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South",
)
#: Price-match tolerance, $/MWh — the miso-264 value, fixed, never swept.
TOL = 0.05
ARM = {"miso_gas_marginal_commodity_pricing": True, "miso_gas_variable_transport": True}


def rebuild(year: int, armed: bool) -> dict:
    """Keeper fleet_only state for ``year``; ``armed`` adds the ruled gas convention."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(KEEPER, year))
    cfg = json.loads((KEEPER / f"run_config_{year}.json").read_text())
    sc = cfg.get("scenario_config", cfg)
    if armed:
        po = dict(kw.get("prb_overrides") or {})
        po.update(ARM)
        kw["prb_overrides"] = po
    gas = sc.get("gas_price_override", meta.get("gas_price"))
    return run_year(year, "MISO", 8760, gas, {}, fleet_only=True, **kw)


def actual_rt(year: int) -> np.ndarray:
    """(zone, T) zonal RT hub-mean LMP on :data:`INTERNAL`'s order."""
    df = pd.read_parquet(ACTUALS)
    df = df[df["year"] == year]
    pv = df.groupby(["hour", "zone"])["rt"].mean().unstack()
    pv["MISO-Plains"] = df[df["hub"].isin(PLAINS_PROXY)].groupby("hour")["rt"].mean()
    pv = pv.reindex(range(8760))
    return pv[list(INTERNAL)].to_numpy(float).T


def stats(price: np.ndarray, act: np.ndarray, dem: np.ndarray) -> dict:
    """C3a-like annual LW error, C3b-like monthly NRMSE, hour/month profiles."""
    ok = np.isfinite(act)
    w = np.where(ok, dem, 0.0)
    m_lw = (price * w).sum() / w.sum()
    a_lw = (np.nan_to_num(act) * w).sum() / w.sum()
    month = (pd.Timestamp("2021-01-01") + pd.to_timedelta(np.arange(8760), "h")).month.to_numpy() - 1
    hod = np.arange(8760) % 24
    mm, am = [], []
    for m in range(12):
        k = (month == m)[None, :] & ok
        ww = np.where(k, dem, 0.0)
        mm.append((price * ww).sum() / ww.sum())
        am.append((np.nan_to_num(act) * ww).sum() / ww.sum())
    mm, am = np.array(mm), np.array(am)
    err_h = []
    for h in range(24):
        k = (hod == h)[None, :] & ok
        ww = np.where(k, dem, 0.0)
        err_h.append(float(((price - np.nan_to_num(act)) * ww).sum() / ww.sum()))
    return {
        "lw_model": round(float(m_lw), 3), "lw_actual": round(float(a_lw), 3),
        "c3a_pct": round(float(100 * (m_lw - a_lw) / a_lw), 2),
        "c3b_monthly_nrmse": round(float(np.sqrt(np.mean((mm - am) ** 2)) / am.mean()), 4),
        "monthly_model": [round(float(x), 2) for x in mm],
        "monthly_actual": [round(float(x), 2) for x in am],
        "hod_error": [round(x, 2) for x in err_h],
        "daily_lw": [round(float(x), 2) for x in daily_lw(price, dem, ok)],
        "daily_lw_actual": [round(float(x), 2) for x in daily_lw(np.nan_to_num(act), dem, ok)],
    }


def daily_lw(p: np.ndarray, dem: np.ndarray, ok: np.ndarray) -> np.ndarray:
    """Load-weighted daily mean over zones and hours (365 days)."""
    w = np.where(ok, dem, 0.0)
    day = np.arange(p.shape[1]) // 24
    return np.bincount(day, weights=(p * w).sum(0))[:365] / np.bincount(day, weights=w.sum(0))[:365]


def probe(year: int) -> dict:
    """Control vs armed static re-merit for one year."""
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    price = sysd.pivot(index="hour", columns="zone", values="price")[list(INTERNAL)].to_numpy(float).T
    dem = sysd.pivot(index="hour", columns="zone", values="demand")[list(INTERNAL)].to_numpy(float).T

    ctl = rebuild(year, False)
    ids_c = list(ctl["fleet_arrays"].unit_ids)
    mc_c = np.asarray(ctl["mc_base"], float)
    fa = ctl["fleet_arrays"]
    fp_c = np.asarray(ctl["fuel_prices"], float)
    zone = np.array([str(getattr(g, "zone", "") or "") for g in ctl["fleet"]])
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    gas = np.isin(fa.fuel_type_idx, _GAS_FUEL_IDX)
    del ctl
    gc.collect()
    arm = rebuild(year, True)
    assert list(arm["fleet_arrays"].unit_ids) == ids_c, "row order moved"
    dmc = np.asarray(arm["mc_base"], float) - mc_c
    fp_a = np.asarray(arm["fuel_prices"], float)
    del arm
    gc.collect()

    pred = price.copy()
    matched = 0.0
    for zi, zz in enumerate(INTERNAL):
        for scope in ("local", "pooled"):
            gi = np.where(zone == zz)[0] if scope == "local" else np.arange(zone.size)
            live = cap[gi] > 1e-6
            hit = live & (np.abs(mc_c[gi] - price[zi][None, :]) <= TOL)
            n = hit.sum(0)
            has = n > 0
            if scope == "pooled":
                has &= ~done
            d = (np.where(hit, dmc[gi], 0.0).sum(0) / np.maximum(n, 1))
            pred[zi, has] = price[zi, has] + d[has]
            matched += float(dem[zi, has].sum())
            done = has if scope == "local" else done | has
    act = actual_rt(year)
    capg = np.asarray(fa.pmax, float)[gas]
    month = (pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month.to_numpy()
    gas_m = []
    for m in range(1, 13):
        k = month == m
        gas_m.append({
            "month": m,
            "ctl": round(float((fp_c[gas][:, k].mean(1) * capg).sum() / capg.sum()), 3),
            "arm": round(float((fp_a[gas][:, k].mean(1) * capg).sum() / capg.sum()), 3),
        })
    frac_gas_rows_moved = float((np.abs(dmc[gas]).max(1) > 1e-6).mean())
    res = {
        "year": year,
        "matched_share": round(matched / dem.sum(), 4),
        "gas_rows": int(gas.sum()), "gas_rows_moved_share": round(frac_gas_rows_moved, 4),
        "non_gas_rows_moved": int((np.abs(dmc[~gas]).max(1) > 1e-6).sum()),
        "keeper": stats(price, act, dem),
        "static_armed": stats(pred, act, dem),
        "gas_price_capw_by_month": gas_m,
    }
    return res


def main() -> int:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=[2020, 2021, 2023])
    a = ap.parse_args()
    prev = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in a.years:
        r = probe(y)
        prev[str(y)] = r
        OUT.write_text(json.dumps(prev, indent=1))
        k, s = r["keeper"], r["static_armed"]
        print(f"{y}: matched {r['matched_share']}  C3a {k['c3a_pct']} -> {s['c3a_pct']}  "
              f"C3b {k['c3b_monthly_nrmse']} -> {s['c3b_monthly_nrmse']}  nongas_moved {r['non_gas_rows_moved']}")
        print("  hod ctl", k["hod_error"])
        print("  hod arm", s["hod_error"])
        print("  mon mdl", k["monthly_model"])
        print("  mon arm", s["monthly_model"])
        print("  mon act", k["monthly_actual"])
        print("  gas", [(g["ctl"], g["arm"]) for g in r["gas_price_capw_by_month"]])
        gc.collect()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
