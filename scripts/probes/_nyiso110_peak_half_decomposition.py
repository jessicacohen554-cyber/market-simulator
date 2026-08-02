#!/usr/bin/env python3
"""nyiso-110 — no-LP decomposition of the PEAK half of NYISO's compressed price
distribution, on the keeper's own committed sidecars.

nyiso-109 fixed the TROUGH half (zonal gas anchor) and named the PEAK half as
its successor: the model reproduces 69/49/45 % of the measured trough->peak
swing, with the peak under-priced in 2024/2025 and C3a-2025 at -9.64 %. xiso-1
then measured the same compression at all 36 ISO-year-benchmark cells (NYISO
hod amplitude 52.0/50.9/44.5 % vs DA), so NYISO's peak half is the local face
of a SYSTEMIC defect. Before any lever is proposed, rule 19 ``[R-ONE-MECH]``
requires decomposing the NYISO miss into what each candidate mechanism family
could own:

* **R — reserve/scarcity formation**: the reserve-price content of the real
  peak LMP vs the model's own co-opt reserve dual (the pjm-138 construction,
  derived on NYISO's own published AS prices per rule 25).
* **L — offer-surface level**: is the actual peak price WITHIN the model's own
  offer stack (reachable by traversal), and how much capacity is priced in
  the band between the model's clearing price and the actual price?
* **X — the systemic amplitude signature**: the broad, all-days, sign-symmetric
  flat-stack compression xiso-1 measured (within-day offer sigma = 0, same
  econ family marginal at both ends — nyiso-109 §8).

**No LP is solved.** Measurements A-D read only committed artifacts (keeper
``hourly/`` sidecars, ``actual_lmp_hourly_NYISO.parquet``, the committed
``NYISO_as_{da,rt}_<year>.csv`` zonal AS prices, EIA-930 NYIS hourly).
Measurement E replays ``meta.json`` -> ``run_year(fleet_only=True)`` for the
keeper's exact offer arrays (fleet built, LP never constructed) — pass
``--no-fleet`` to skip it.

Measurements
------------
* **A — the target statistic** on the committed full-year hub actual (DA and
  RT): trough/peak window means, swing share reproduced, trough/peak errors,
  plus the xiso-1 hour-of-day amplitude for reconciliation.
* **B — reserve formation**: measured zonal spin_10 (top of the posted cascade,
  the co-opt opportunity-cost proxy) load-weighted onto model zones, vs the
  model's ``reserve_price`` sidecar column (sum of family duals, folded into
  the energy price by construction). Peak window, trough control, DA and RT.
* **C — where the peak miss lives**: distribution of the per-hour peak-window
  miss (share of hours, concentration in the top decile, seasonal split,
  $200-censored robustness per miso-89).
* **D — day-level swing**: per-calendar-day model share of the actual swing
  (median vs mean; share of days with inverted model swing).
* **E — offer-stack anatomy at peak** (fleet replay): top-of-stack vs actual
  peak price (share of peak hours the actual exceeds ANY model offer),
  headroom capacity priced between the model's clearing price and the actual
  price, marginal census at the peak window on the keeper's own offers, and
  the model-vs-measured thermal volume at peak (EIA-930 ``NG: NG`` + ``NG: OIL``,
  zero-dropout-screened per the nyiso-98 lesson).

Usage
-----
    PYTHONPATH=.:src python scripts/probes/_nyiso110_peak_half_decomposition.py \
        --bundle results/calibration/nyiso109_zonalanchor_B \
        --out results/calibration/_nyiso110_peak_half_decomposition.json
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

YEARS = (2023, 2024, 2025)
HOURS = 8760

#: nyiso-109 windows, kept verbatim for comparability of the swing statistic.
TROUGH = (1, 2, 3, 4, 5)
PEAK = (17, 18, 19)

MODEL_ZONES = (
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
)

#: Representative NYISO settlement zone per model zone (verbatim from
#: ``scripts/data/derive_nyiso_rcpf_overlay._MODEL_ZONE_TO_NYISO_AS``).
MODEL_ZONE_TO_NYISO_AS = {
    "Upstate_West": "WEST",
    "Capital_Hudson": "CAPITL",
    "Lower_Hudson": "DUNWOD",
    "NYC": "N.Y.C.",
    "Long_Island": "LONGIL",
}

#: Month-start hour offsets on the model's non-leap 8760 clock (verbatim from
#: ``scripts/data/process_nyiso_as.py``).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])

TRANCHE_FAMILIES = ("mustrun", "sync", "committed", "econ", "peak")
EPS = 1.0  # pjm-122 / pjm-138 §4.1 marginal-set tolerance, $/MWh


class _FleetCaptured(Exception):
    """Control-flow signal: the fleet arrays are built, unwind before the LP."""


# ── committed-artifact loaders ──────────────────────────────────────────────


def _actual_hub(year: int) -> pd.DataFrame:
    """Committed hub-mean hourly DA/RT on the model 8760 clock (xiso-1 basis)."""
    p = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
    df = pd.read_parquet(p)
    df = df[df["year"] == year].set_index("hour").reindex(range(HOURS))
    return df[["da", "rt"]]


def _model_system(bundle: Path, year: int) -> pd.DataFrame:
    """Keeper P1 load-weighted system price, demand and reserve dual, per hour."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["zone"].isin(MODEL_ZONES)]
    if "pass" in sysf.columns and "P1" in set(sysf["pass"]):
        sysf = sysf[sysf["pass"] == "P1"]
    price = sysf.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand", aggfunc="mean")
    rp = sysf.pivot_table(index="hour", columns="zone", values="reserve_price", aggfunc="mean")
    w = dem[list(MODEL_ZONES)].to_numpy(float)
    out = pd.DataFrame(
        {
            "model": np.average(price[list(MODEL_ZONES)].to_numpy(float), weights=w, axis=1),
            "load": w.sum(axis=1),
            # reserve_price is written as a system-wide broadcast; the zone mean
            # recovers the (T,) series exactly.
            "reserve_model": rp[list(MODEL_ZONES)].to_numpy(float).mean(axis=1),
        },
        index=price.index,
    ).reindex(range(HOURS))
    out["zone_demand"] = list(dem[list(MODEL_ZONES)].reindex(range(HOURS)).to_numpy(float))
    return out


def _as_prices(year: int, market: str) -> pd.DataFrame | None:
    """Per-model-zone measured AS product prices on the model 8760 clock.

    Reads the committed ``NYISO_as_{market}_<year>.csv`` (Eastern wall-clock,
    hour-beginning; Feb-29 dropped to the model's non-leap calendar — the
    ``process_nyiso_as.build_reference`` mapping, reproduced verbatim).
    Returns one row per hour with ``spin10_<zone>`` (the top of the posted
    cascade — a spin provider's price internalizes the lower products, so this
    is the correct single-product opportunity-cost proxy for a reserve-capable
    marginal unit) and ``stack_<zone>`` (spin+nonsync+op30, the repo's RCPF
    validation convention, reported for cross-reference only).
    """
    p = REPO / "data" / "raw" / "NYISO-AS" / f"NYISO_as_{market}_{year}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    ts = pd.to_datetime(df["Time Stamp"])
    keep = ~((ts.dt.month == 2) & (ts.dt.day == 29))
    df, ts = df[keep], ts[keep]
    hoy = (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    df = df.assign(hour=hoy, stack=df[["spin_10", "nonsync_10", "op_30"]].sum(axis=1))
    out = pd.DataFrame(index=pd.RangeIndex(HOURS, name="hour"))
    for zone, nz in MODEL_ZONE_TO_NYISO_AS.items():
        sub = df[df["Name"] == nz].groupby("hour")[["spin_10", "stack"]].mean()
        out[f"spin10_{zone}"] = sub["spin_10"].reindex(range(HOURS))
        out[f"stack_{zone}"] = sub["stack"].reindex(range(HOURS))
    return out


def _lw_zone_series(per_zone: pd.DataFrame, prefix: str, zone_w: np.ndarray) -> np.ndarray:
    """Load-weighted cross-zone mean of ``<prefix>_<zone>`` columns."""
    mat = np.column_stack(
        [per_zone[f"{prefix}_{z}"].to_numpy(float) for z in MODEL_ZONES]
    )
    w = np.where(np.isfinite(mat), zone_w, 0.0)
    tot = w.sum(axis=1)
    with np.errstate(invalid="ignore"):
        return np.where(tot > 0, np.nansum(mat * w, axis=1) / tot, np.nan)


# ── A: the target statistic ─────────────────────────────────────────────────


def _target(bundle: Path, year: int) -> dict:
    """Swing + amplitude statistics on the committed full-year hub actual."""
    sysd = _model_system(bundle, year)
    hub = _actual_hub(year)
    hod = np.arange(HOURS) % 24
    t, p = np.isin(hod, TROUGH), np.isin(hod, PEAK)
    out: dict = {}
    for basis in ("da", "rt"):
        a = hub[basis].to_numpy(float)
        m = sysd["model"].to_numpy(float)
        ok = np.isfinite(a) & np.isfinite(m)
        mt, mp = float(m[ok & t].mean()), float(m[ok & p].mean())
        at, ap = float(a[ok & t].mean()), float(a[ok & p].mean())
        # xiso-1 hour-of-day amplitude: mean-by-hod range, model / actual.
        prof_m = np.array([m[ok & (hod == h)].mean() for h in range(24)])
        prof_a = np.array([a[ok & (hod == h)].mean() for h in range(24)])
        out[basis] = {
            "model_trough": round(mt, 3),
            "model_peak": round(mp, 3),
            "actual_trough": round(at, 3),
            "actual_peak": round(ap, 3),
            "model_swing": round(mp - mt, 3),
            "actual_swing": round(ap - at, 3),
            "share_reproduced": round((mp - mt) / (ap - at), 4) if ap != at else None,
            "trough_error": round(mt - at, 3),
            "peak_error": round(mp - ap, 3),
            "hod_amplitude_model": round(float(prof_m.max() - prof_m.min()), 3),
            "hod_amplitude_actual": round(float(prof_a.max() - prof_a.min()), 3),
            "hod_amplitude_share": round(
                float((prof_m.max() - prof_m.min()) / (prof_a.max() - prof_a.min())), 4
            ),
            "hod_peak_hour_model": int(prof_m.argmax()),
            "hod_peak_hour_actual": int(prof_a.argmax()),
        }
    return out


# ── B: reserve/scarcity formation ───────────────────────────────────────────


def _reserve_formation(bundle: Path, year: int) -> dict:
    """Measured reserve-price content vs the model's co-opt reserve dual."""
    sysd = _model_system(bundle, year)
    hub = _actual_hub(year)
    m = sysd["model"].to_numpy(float)
    zone_w = np.stack(sysd["zone_demand"].to_numpy())
    hod = np.arange(HOURS) % 24
    t, p = np.isin(hod, TROUGH), np.isin(hod, PEAK)
    rm = sysd["reserve_model"].to_numpy(float)

    out: dict = {
        "model_reserve_dual": {
            "share_hours_gt0": round(float((rm > 1e-9).mean()), 4),
            "hours_gt0": int((rm > 1e-9).sum()),
            "mean_peak_window": round(float(rm[p].mean()), 4),
            "mean_trough_window": round(float(rm[t].mean()), 4),
            "mean_all": round(float(rm.mean()), 4),
            "max": round(float(rm.max()), 2),
        }
    }
    for market in ("da", "rt"):
        asp = _as_prices(year, market)
        if asp is None:
            out[f"measured_{market}"] = None
            continue
        spin = _lw_zone_series(asp, "spin10", zone_w)
        stack = _lw_zone_series(asp, "stack", zone_w)
        ok = np.isfinite(spin)
        rec = {
            "covered_hours": int(ok.sum()),
            "spin10_lw_mean_all": round(float(np.nanmean(spin)), 4),
            "spin10_lw_mean_peak": round(float(np.nanmean(spin[p])), 4),
            "spin10_lw_mean_trough": round(float(np.nanmean(spin[t])), 4),
            "spin10_share_gt1_peak": round(float(np.nanmean(spin[p] > 1.0)), 4),
            "spin10_share_gt10_peak": round(float(np.nanmean(spin[p] > 10.0)), 4),
            "spin10_p50_peak": round(float(np.nanpercentile(spin[p], 50)), 4),
            "spin10_p90_peak": round(float(np.nanpercentile(spin[p], 90)), 4),
            "stack_lw_mean_peak_crossref": round(float(np.nanmean(stack[p])), 4),
            # The reserve-formation gap this market's prices support: measured
            # spin content at peak minus the model's own dual at peak. An upper
            # bound on the miss share reserve formation can own — the measured
            # spin price passes into the energy LMP only where a reserve-capable
            # unit is marginal (co-opt arbitrage), so the true content is <= this.
            "reserve_gap_peak": round(
                float(np.nanmean(spin[p]) - float(rm[p].mean())), 4
            ),
            "reserve_gap_trough_control": round(
                float(np.nanmean(spin[t]) - float(rm[t].mean())), 4
            ),
        }
        # Censored variant: does the measured reserve content survive removing
        # scarcity-event hours (spin > $200), or is it event-driven?
        spin_c = np.where(spin > 200.0, np.nan, spin)
        rec["spin10_lw_mean_peak_censored200"] = round(float(np.nanmean(spin_c[p])), 4)
        rec["share_peak_hours_spin_gt200"] = round(float(np.nanmean(spin[p] > 200.0)), 5)

        # B2 — the ENERGY-BASIS restatement, the decomposition's pivot: subtract
        # the measured reserve content from the actual price (a bounding
        # construction — the spin price passes into the LMP only where a
        # reserve-capable unit is marginal, so this removes AT MOST the true
        # content) and subtract the model's own folded dual from its price.
        # What remains on both sides is the energy-only clearing level.
        a = hub[market].to_numpy(float)
        a_e = a - np.where(np.isfinite(spin), spin, 0.0)
        m_e = m - rm
        okb = np.isfinite(a_e) & np.isfinite(m_e)
        ok_raw = np.isfinite(a) & np.isfinite(m)
        missing_swing = float(
            (a[ok_raw & p].mean() - a[ok_raw & t].mean())
            - (m[ok_raw & p].mean() - m[ok_raw & t].mean())
        )
        rd = float(np.nanmean(spin[p]) - np.nanmean(spin[t]))
        rec["B2_energy_basis"] = {
            "trough_error_energy": round(float((m_e - a_e)[okb & t].mean()), 3),
            "peak_error_energy": round(float((m_e - a_e)[okb & p].mean()), 3),
            "model_energy_swing": round(
                float(m_e[okb & p].mean() - m_e[okb & t].mean()), 3
            ),
            "actual_energy_swing": round(
                float(a_e[okb & p].mean() - a_e[okb & t].mean()), 3
            ),
            "energy_swing_share": round(
                float(
                    (m_e[okb & p].mean() - m_e[okb & t].mean())
                    / (a_e[okb & p].mean() - a_e[okb & t].mean())
                ),
                4,
            ),
            "reserve_differential_peak_minus_trough": round(rd, 3),
            "missing_swing": round(missing_swing, 3),
            "share_of_missing_swing_owned_by_reserve": round(rd / missing_swing, 4)
            if missing_swing
            else None,
        }
        out[f"measured_{market}"] = rec
    return out


# ── C: where the peak miss lives ────────────────────────────────────────────


def _miss_anatomy(bundle: Path, year: int) -> dict:
    """Distributional anatomy of the per-hour peak-window miss (DA and RT)."""
    sysd = _model_system(bundle, year)
    hub = _actual_hub(year)
    hod = np.arange(HOURS) % 24
    p = np.isin(hod, PEAK)
    mon = np.repeat(np.arange(1, 13), np.array(_DAYS_IN_MONTH) * 24)
    season = np.where(np.isin(mon, (12, 1, 2)), "DJF",
                      np.where(np.isin(mon, (6, 7, 8)), "JJA", "shoulder"))
    out: dict = {}
    m = sysd["model"].to_numpy(float)
    for basis in ("da", "rt"):
        a = hub[basis].to_numpy(float)
        ok = np.isfinite(a) & np.isfinite(m) & p
        miss = a[ok] - m[ok]
        srt = np.sort(miss)[::-1]
        top_dec = srt[: max(1, len(srt) // 10)].sum()
        rec = {
            "peak_hours": int(ok.sum()),
            "mean_miss": round(float(miss.mean()), 3),
            "p50_miss": round(float(np.percentile(miss, 50)), 3),
            "share_hours_miss_gt0": round(float((miss > 0).mean()), 4),
            "share_hours_miss_gt10": round(float((miss > 10.0).mean()), 4),
            "top_decile_share_of_total_positive": round(
                float(top_dec / miss[miss > 0].sum()), 4
            )
            if (miss > 0).any()
            else None,
            "mean_miss_censored200": round(
                float((np.minimum(a[ok], 200.0) - m[ok]).mean()), 3
            ),
            "by_season": {
                s: {
                    "hours": int((season[ok] == s).sum()),
                    "mean_miss": round(float(miss[season[ok] == s].mean()), 3),
                }
                for s in ("DJF", "JJA", "shoulder")
            },
        }
        out[basis] = rec
    return out


# ── D: day-level swing ──────────────────────────────────────────────────────


def _day_swing(bundle: Path, year: int) -> dict:
    """Per-calendar-day trough->peak swing, model vs actual (DA basis)."""
    sysd = _model_system(bundle, year)
    hub = _actual_hub(year)
    hod = np.arange(HOURS) % 24
    day = np.arange(HOURS) // 24
    m = sysd["model"].to_numpy(float)
    out: dict = {}
    for basis in ("da", "rt"):
        a = hub[basis].to_numpy(float)
        rows_m, rows_a = [], []
        for d in range(365):
            k = day == d
            kt, kp = k & np.isin(hod, TROUGH), k & np.isin(hod, PEAK)
            if not (np.isfinite(a[kt]).all() and np.isfinite(a[kp]).all()):
                continue
            rows_m.append(m[kp].mean() - m[kt].mean())
            rows_a.append(a[kp].mean() - a[kt].mean())
        ms, As = np.array(rows_m), np.array(rows_a)
        pos = As > 1.0  # days with a real measured swing
        share = ms[pos] / As[pos]
        out[basis] = {
            "days": int(len(ms)),
            "days_actual_swing_gt1": int(pos.sum()),
            "median_day_share": round(float(np.median(share)), 4),
            "mean_day_share": round(float(share.mean()), 4),
            "share_days_model_lt_half": round(float((share < 0.5).mean()), 4),
            "share_days_model_inverted": round(float((ms[pos] < 0).mean()), 4),
        }
    return out


# ── E: offer-stack anatomy at peak (fleet replay) ───────────────────────────


def _keeper_fleet(bundle: Path, year: int) -> dict:
    """Rebuild the EXACT fleet/offer arrays the keeper solved against — no LP.

    Verbatim reuse of ``_nyiso109_trough_offer_stack._keeper_fleet``.
    """
    spec = importlib.util.spec_from_file_location(
        "_replay_keeper", REPO / "scripts" / "replay_keeper.py"
    )
    rk = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(rk)

    from scripts import run_calibration
    from scripts import run_calibration_full as rcf

    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [year]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", HOURS))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = bundle

    captured: dict = {}
    real_run_year = run_calibration.run_year

    def _intercept(*args, **kw):
        kw["fleet_only"] = True
        captured["state"] = real_run_year(*args, **kw)
        raise _FleetCaptured

    run_calibration.run_year = _intercept
    rcf.run_year = _intercept
    try:
        rcf.solve_and_persist(**kwargs)
    except _FleetCaptured:
        pass
    finally:
        run_calibration.run_year = real_run_year
        rcf.run_year = real_run_year

    if "state" not in captured:
        raise SystemExit("fleet reconstruction did not reach run_year")
    return captured["state"]


def _tranche_of(unit_id: str) -> str:
    """Tranche family from an LP ``unit_id`` suffix, longest-prefix-first."""
    suffix = str(unit_id).rsplit("_", 1)[-1]
    for family in sorted(TRANCHE_FAMILIES, key=len, reverse=True):
        if suffix.startswith(family):
            return family
    return "_unbinned"


def _stack_anatomy(bundle: Path, year: int) -> dict:
    """Top-of-stack, headroom band, marginal census and thermal volume at peak."""
    state = _keeper_fleet(bundle, year)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], HOURS, axis=1)
    avail = np.asarray(fa.pmax, dtype=float)[:, None] * np.asarray(
        fa.availability, dtype=float
    )
    if avail.ndim == 1:
        avail = np.repeat(avail[:, None], HOURS, axis=1)
    groups = np.array(
        [str(g) if g else "?" for g in np.asarray(fa.plant_group, dtype=object)],
        dtype=object,
    )
    unit_ids = np.asarray(fa.unit_ids, dtype=object)
    tranches = np.array([_tranche_of(u) for u in unit_ids], dtype=object)
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    heat_rate = np.asarray(fa.heat_rate, dtype=float)
    vom = np.asarray(fa.vom, dtype=float)
    fuel_px = np.asarray(state.get("fuel_prices"), dtype=float)
    if fuel_px.ndim == 1:
        fuel_px = np.repeat(fuel_px[:, None], HOURS, axis=1)

    # Thermal = fuel-burning plant groups; excludes renewables/nuclear/hydro/
    # storage/import rows, which never set the thermal top-of-stack.
    thermal_groups = {
        "CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP",
        "COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "OIL_ST", "OIL_CT",
    }
    is_thermal = np.isin(groups, sorted(thermal_groups))
    n_zones = len(MODEL_ZONES)
    internal = zone_idx < n_zones
    rows = internal & is_thermal

    sysd = _model_system(bundle, year)
    hub = _actual_hub(year)
    m = sysd["model"].to_numpy(float)
    hod = np.arange(HOURS) % 24
    p = np.isin(hod, PEAK)

    # Per-zone duals for the marginal census.
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[(sysf["zone"].isin(MODEL_ZONES)) & (sysf["pass"] == "P1")]
    duals = (
        sysf.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")[
            list(MODEL_ZONES)
        ]
        .reindex(range(HOURS))
        .to_numpy(float)
        .T
    )
    row_dual = np.full(mc.shape, np.nan)
    row_dual[internal] = duals[zone_idx[internal]]

    out: dict = {"n_lp_rows": int(mc.shape[0]), "n_internal_thermal_rows": int(rows.sum())}

    # E1 — top-of-stack vs the actual peak price, and the headroom band.
    live = rows[:, None] & (avail > 1.0)
    mc_live = np.where(live, mc, -np.inf)
    top = mc_live.max(axis=0)  # (T,) most expensive available thermal offer
    for basis in ("da", "rt"):
        a = hub[basis].to_numpy(float)
        ok = p & np.isfinite(a) & np.isfinite(m)
        band = np.where(
            live & (mc > m[None, :] + EPS) & (mc <= np.maximum(a, m)[None, :]),
            avail,
            0.0,
        ).sum(axis=0)
        above_actual = np.where(live & (mc > np.maximum(a, m)[None, :]), avail, 0.0).sum(axis=0)
        miss = a[ok] - m[ok]
        pos = miss > EPS
        out[f"E1_{basis}"] = {
            "peak_hours": int(ok.sum()),
            "share_actual_above_top_of_stack": round(float((a[ok] > top[ok]).mean()), 4),
            "mean_unreachable_excess": round(
                float(np.maximum(a[ok] - top[ok], 0.0).mean()), 4
            ),
            "top_of_stack_mean_peak": round(float(top[ok].mean()), 3),
            "mean_gw_in_band_model_to_actual": round(float(band[ok][pos].mean()) / 1000.0, 4)
            if pos.any()
            else None,
            "p50_gw_in_band_model_to_actual": round(float(np.percentile(band[ok][pos], 50)) / 1000.0, 4)
            if pos.any()
            else None,
            "mean_gw_priced_above_actual": round(float(above_actual[ok].mean()) / 1000.0, 4),
        }

    # E2 — marginal census in the peak window on the keeper's own offers.
    window = p
    live_all = internal[:, None] & window[None, :] & (avail > 0.0)
    marginal = live_all & (np.abs(mc - row_dual) <= EPS)
    wgt = np.where(marginal, avail, 0.0)
    tot = float(wgt.sum())
    decomp = None
    if tot > 0:
        burn = heat_rate[:, None] * fuel_px
        decomp = {
            "cap_weighted_offer": round(float((mc * wgt).sum() / tot), 4),
            "cap_weighted_burn": round(float((burn * wgt).sum() / tot), 4),
            "cap_weighted_vom": round(
                float((np.broadcast_to(vom[:, None], mc.shape) * wgt).sum() / tot), 4
            ),
            "cap_weighted_residual_markup": round(
                float(((mc - burn - vom[:, None]) * wgt).sum() / tot), 4
            ),
        }
    by_tranche: dict[str, int] = {}
    by_pair: dict[str, int] = {}
    for fam in list(TRANCHE_FAMILIES) + ["_unbinned"]:
        by_tranche[fam] = int(marginal[tranches == fam].sum())
    for g in sorted(set(groups)):
        for fam in list(TRANCHE_FAMILIES) + ["_unbinned"]:
            sel = (groups == g) & (tranches == fam)
            n = int(marginal[sel].sum())
            if n:
                by_pair[f"{g}:{fam}"] = n
    total = sum(by_tranche.values())
    out["E2_peak_marginal_census"] = {
        "share_by_tranche": {k: round(v / total, 4) for k, v in by_tranche.items() if total},
        "top_pairs": dict(sorted(by_pair.items(), key=lambda kv: -kv[1])[:8]),
        "detection_rate": round(
            float((marginal.any(axis=0) & window).sum()) / max(int(window.sum()), 1), 4
        ),
        "marginal_offer_decomposition": decomp,
    }

    cls_hourly = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls_hourly = cls_hourly[cls_hourly["pass"] == "P1"]

    # E4 — the caiso-144-pattern EX-ANTE dormancy census for any ONLINE-scoped
    # spin construction (the nyiso-84 "widened gate" prerequisite). The
    # keeper arms nyiso_hydro_reserve_eligible, and holding reserve spends no
    # water (reserves/spec.py: the budget bounds dispatched energy only), so
    # every MW of online hydro headroom is a ZERO-opportunity-cost spinning
    # provider — in reality too (NYPA hydro is a certified NYISO reserve
    # supplier). If hydro headroom alone covers the published 655 MW NYCA spin
    # requirement in ~every hour, every optimum of ANY widened online-gated
    # spin family carries zero reserve dual, and the mechanism is dormant
    # ex-ante — no solve needed.
    fuel_names = np.asarray(
        [str(f) for f in np.asarray(getattr(fa, "fuel_type_names", []))], dtype=object
    )
    if fuel_names.size != mc.shape[0]:
        from market_sim.data.fleet.models import FUEL_TYPE_NAMES

        fuel_names = np.array(
            [FUEL_TYPE_NAMES[i] for i in np.asarray(fa.fuel_type_idx, dtype=int)],
            dtype=object,
        )
    hydro_rows = internal & (fuel_names == "hydro")
    hydro_cap = np.where(hydro_rows[:, None], avail, 0.0).sum(axis=0)  # (T,)
    hy = (
        cls_hourly[cls_hourly["klass"] == "hydro"]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(HOURS))
        .to_numpy(float)
        if "hydro" in set(cls_hourly["klass"])
        else np.zeros(HOURS)
    )
    hy_f = np.where(np.isfinite(hy), hy, 0.0)
    hydro_headroom = hydro_cap - hy_f
    # Conservative zero-cost supply bound: BOTH the aggregate headroom and the
    # class-2 online-gate term rho*P must cover the requirement; rho is taken
    # at its 0.5 clip floor (the machinery's own lower bound), so this
    # understates the gated supply rather than overstating it.
    zero_cost_supply = np.minimum(hydro_headroom, 0.5 * hy_f)
    SPIN_REQ = 655.0  # NYCA 10-min spin, published + measured (flat all years)
    out["E4_spin_dormancy_census"] = {
        "spin_requirement_mw": SPIN_REQ,
        "hydro_cap_mean_peak_gw": round(float(hydro_cap[p].mean()) / 1000.0, 4),
        "hydro_headroom_mean_peak_gw": round(float(hydro_headroom[p].mean()) / 1000.0, 4),
        "hydro_headroom_p05_peak_gw": round(
            float(np.percentile(hydro_headroom[p], 5)) / 1000.0, 4
        ),
        "share_all_hours_hydro_headroom_covers_req": round(
            float((hydro_headroom >= SPIN_REQ).mean()), 4
        ),
        "share_peak_hours_hydro_headroom_covers_req": round(
            float((hydro_headroom[p] >= SPIN_REQ).mean()), 4
        ),
        "hours_hydro_headroom_short": int((hydro_headroom < SPIN_REQ).sum()),
        "share_all_hours_conservative_zero_cost_covers_req": round(
            float((zero_cost_supply >= SPIN_REQ).mean()), 4
        ),
        "hours_conservative_zero_cost_short": int((zero_cost_supply < SPIN_REQ).sum()),
    }

    # E3 — thermal volume at peak, model vs EIA-930 (zero-dropout screened).
    cls = cls_hourly
    thermal_cls = sorted(
        set(cls["klass"]) & {g for g in thermal_groups} | ({"oil"} & set(cls["klass"]))
    )
    model_th = (
        cls[cls["klass"].isin(thermal_cls)]
        .pivot_table(index="hour", values="mw", aggfunc="sum")
        .reindex(range(HOURS))["mw"]
        .to_numpy(float)
    )
    e930 = pd.read_parquet(REPO / "data" / "raw" / "eia-930-hourly" / "NYIS hourly.parquet")
    ts = pd.to_datetime(e930["Local time"])
    e930 = e930[(ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))]
    ts = pd.to_datetime(e930["Local time"])
    hoy = (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )
    gas = e930.groupby(hoy)["NG: NG"].mean().reindex(range(HOURS)).to_numpy(float)
    oil = e930.groupby(hoy)["NG: OIL"].mean().reindex(range(HOURS)).to_numpy(float)
    meas_th = gas + np.where(np.isfinite(oil), oil, 0.0)
    # nyiso-98 zero-dropout screen: exactly-0.0 gas hours are benchmark
    # artifacts for a fleet this size, never real.
    suspect = gas == 0.0
    okv = p & np.isfinite(meas_th) & ~suspect
    out["E3_thermal_volume_peak"] = {
        "suspect_zero_gas_hours": int(suspect.sum()),
        "model_mean_gw": round(float(model_th[okv].mean()) / 1000.0, 4),
        "measured_mean_gw": round(float(meas_th[okv].mean()) / 1000.0, 4),
        "ratio": round(float(model_th[okv].mean() / meas_th[okv].mean()), 4),
        "classes": thermal_cls,
    }

    del state, fa, mc, avail, row_dual
    gc.collect()
    return out


def main(argv: list[str] | None = None) -> int:
    """Run every measurement and write the machine-readable result."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/nyiso109_zonalanchor_B")
    ap.add_argument(
        "--out", default="results/calibration/_nyiso110_peak_half_decomposition.json"
    )
    ap.add_argument("--no-fleet", action="store_true", help="skip E (no fleet build)")
    args = ap.parse_args(argv)
    bundle = Path(args.bundle)

    out: dict = {
        "bundle": str(bundle),
        "trough_hours": list(TROUGH),
        "peak_hours": list(PEAK),
        "eps": EPS,
        "years": {},
    }
    for year in YEARS:
        rec: dict = {
            "A_target": _target(bundle, year),
            "B_reserve_formation": _reserve_formation(bundle, year),
            "C_miss_anatomy": _miss_anatomy(bundle, year),
            "D_day_swing": _day_swing(bundle, year),
        }
        if not args.no_fleet:
            rec["E_stack_anatomy"] = _stack_anatomy(bundle, year)
        out["years"][str(year)] = rec
        print(f"[nyiso-110] {year} done", flush=True)

    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
