"""caiso-170 PHASE 0 — is the CAISO evening/overnight storage over-position a PERFECT-FORESIGHT artifact, and can S2 (the DA/RT two-settlement separation) reach it? NO LP, NO SOLVE.

`docs/mechanism-testing-matrix.md` §5.2 lever-queue **item 3** is the only live
CAISO item. `FINDING-caiso129` §5 named it and scoped it:

    "candidate S2 (the DA/RT two-settlement separation — the LP's single-market
     perfect-foresight arbitrage itself) is the remaining diagnosis ... a
     structural change of a different size that must be chartered separately,
     not approximated by a shaped floor."

caiso-168 shut the *belly* route into item 3 and left S2 standing on its own
**evening/overnight** object: `FINDING-caiso127` §2's storage pin (192/197/276
of 365 days), which that lane calls "the whole compression".

The prior question has never been measured, and it is the one this probe
answers: **is the over-position a foresight artifact at all, and could a second
settlement reach it?** Both halves are decidable on committed artifacts.

The two pre-registered falsifiers (PRECHECK §4, fixed before any value existed):

* **F1 — FORESIGHT ADVANTAGE.** Score the model's battery dispatch and the
  measured battery fleet's dispatch on the SAME measured price series, as a
  discharge-MWh-weighted within-day price percentile. Material iff the model
  beats the measured fleet by **>= 0.10** on the measured **RT** series in at
  least **2 of 3** years. Below that there is no foresight advantage to remove.
* **F2 — SETTLEMENT SEPARATION.** A second settlement can only move a position
  to the extent the two settlements ORDER the day differently. Material iff the
  mean within-day **Spearman rank correlation between measured DA and RT hourly
  prices** is **<= 0.90**. Above it, a DA-scheduled fleet and an
  RT-perfect-foresight fleet place energy in substantially the same hours.

Neither threshold is re-cut after it fires (`FINDING-caiso166` §3's lesson).

Sources, all committed:

* keeper bundle ``results/calibration/caiso164_zonal_loss_surface/hourly/``
  — ``storage_<y>.parquet`` (P1 charge/discharge MW by tech),
  ``system_<y>.parquet`` (zonal duals + demand);
* ``data/raw/lmp-data/CAISO/CAISO_dam_hourly_<y>.csv`` and
  ``CAISO_rtm_hourly_<y>.csv`` — the measured TWO SETTLEMENTS, the object under
  test;
* ``data/raw/eia-930-hourly/CISO hourly.parquet`` ``NG: OTH`` — the measured
  BATTERY fleet net (discharge +, charge −). It excludes pumped storage by
  construction, which is why caiso-168 §H re-based caiso-121's storage row onto
  it; the same like-for-like basis is used here.

Stages:

``A`` inputs, clock and a falsifiable self-check of the percentile statistic.
``B`` F1 — within-day price percentile of charge and discharge energy, model vs
      measured fleet, on the measured RT and DA series.
``C`` normalised spread capture — achieved vs the perfect-foresight ceiling and
      the worst-placement floor, for the SAME energy and the SAME power profile.
``D`` F2 — within-day DA/RT Spearman rank correlation, and the DA and RT spread
      levels the two settlements actually offer.
``E`` reach — where the evening/overnight position sits by hour of day, model vs
      measured, and how much of it the foresight gap could bound.
``F`` limb split — battery vs the WALLED pumped-storage object, kept strictly
      separate (landing on PS is a stop-and-report, never an approximation).
``G`` the ARMED anchor's own hour-of-day cap against the measured fleet — is the
      concentration stage E finds a FORESIGHT artifact at all, or is it the
      binding shape of `caiso_storage_shape_anchor` (rule 19, channel occupied)?

Rule 13 ``[R-MEASURED]``: every number is a measurement of committed inputs and
committed model output. Nothing is fitted, nothing is tuned, no threshold is
chosen after seeing a value, and no result feeds back into any model input.

Usage:
    python scripts/probes/caiso170_s2_foresight_phase0.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

#: The CAISO keeper bundle. caiso-170 first measured this on
#: ``caiso164_zonal_loss_surface``, the keeper at the time; the caiso-166
#: measured-DLAP arm was promoted mid-session (PR #3514) and the probe was
#: re-run against it. ``--bundle`` re-points it so the verdict's robustness to
#: the keeper change is reproducible rather than asserted (§3a of the finding).
BUNDLE = REPO / "results/calibration/caiso166_measured_loss_zones/hourly"
ENVELOPE = REPO / "data/raw/reference/caiso-storage-shape-envelope.csv"
LMP = REPO / "data/raw/lmp-data/CAISO"
EIA930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"
OUT = REPO / "results/calibration/_caiso170_s2_foresight_phase0.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
DAYS = 365

#: The measured CA hub, the same node caiso-164/165/167/168 decomposed. DAM and
#: RTM disclosures both publish it, so the two settlements are compared at ONE
#: node and the DA/RT contrast carries no locational confound.
CA_HUB = "TH_SP15_GEN-APND"

#: PRE-REGISTERED in PRECHECK §4 before any value existed. Not re-cut.
F1_MIN_ADVANTAGE = 0.10
F1_MIN_YEARS = 2
F2_MAX_RANKCORR = 0.90

#: Descriptive reporting windows (Pacific), NOT gates: the verdict statistics
#: are day-level and do not depend on them. Belly is carried verbatim from
#: caiso-165 §2 so this lane's hour-of-day tables read against the others'.
WINDOWS = {"belly": range(9, 16), "evening": range(17, 22), "overnight": [*range(22, 24), *range(0, 6)]}

#: Dispatch below this many MW is treated as zero — a numerical-tolerance call
#: on a HiGHS solution and on a rounded EIA-930 feed, not a tuned threshold.
ZERO_MW = 1.0

#: Hours per month of the model's FIXED NON-LEAP 8760 calendar — the frame
#: ``storage.storage_cap_profiles`` indexes the monthly COD ramp on. A
#: ``pd.date_range`` clock would shift the recovered cap staircase by a month.
DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

_HOD = np.arange(HOURS) % 24


def _monthly_power_cap(
    chg: np.ndarray,
    dis: np.ndarray,
    f_chg: np.ndarray,
    f_dis: np.ndarray,
    month: np.ndarray,
) -> np.ndarray:
    """Recover the battery fleet's monthly power cap by inverting the envelope.

    Carried verbatim from ``caiso168_storage_bid_phase0._monthly_power_cap``:
    ``power_cap`` is piecewise-constant by month and the anchor sets the bound to
    ``frac[hod] × cap``, so over a month ``max(chg/f_chg, dis/f_dis)`` equals the
    cap in any hour the bound binds and is below it otherwise. caiso-168 §1
    validated the recovery exactly against ``load_eia860_storage``'s own monthly
    battery fleet for all 36 months.
    """
    hod = np.arange(len(chg)) % 24
    with np.errstate(divide="ignore", invalid="ignore"):
        rc = np.where(
            f_chg[hod] > 1e-9,
            chg / np.where(f_chg[hod] > 1e-9, f_chg[hod], 1.0),
            np.nan,
        )
        rd = np.where(
            f_dis[hod] > 1e-9,
            dis / np.where(f_dis[hod] > 1e-9, f_dis[hod], 1.0),
            np.nan,
        )
    r = np.fmax(rc, rd)
    cap = np.zeros(len(chg))
    for m in range(1, 13):
        k = month == m
        cap[k] = np.nanmax(r[k])
    return cap


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    """Map local timestamps onto the model's non-leap 8760 hour index.

    Carried verbatim from ``caiso168_storage_bid_phase0._model_hour``. The solve
    frame drops Feb-29, so every later day of a leap year shifts back one day;
    a naive linear offset puts every 2024 hour after Feb-28 a full day out of
    phase (the defect caiso-168 flagged in caiso-167's lane).
    """
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24 + dt.hour.to_numpy()


def _storage(year: int) -> dict[str, dict[str, np.ndarray]]:
    """P1 fleet charge/discharge MW per tech from the keeper's own sidecar."""
    s = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    chg = s.pivot_table(index="hour", columns="tech", values="charge_mw")
    dis = s.pivot_table(index="hour", columns="tech", values="discharge_mw")
    return {
        t: {"chg": chg[t].to_numpy(dtype=float), "dis": dis[t].to_numpy(dtype=float)}
        for t in chg.columns
    }


def _ca_lambda(year: int) -> np.ndarray:
    """CA demand-weighted model dual — the C3a construction, WECC nodes excluded."""
    d = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.pivot_table(index="hour", columns="zone", values="price")
    demand = d.pivot_table(index="hour", columns="zone", values="demand")
    ca = [z for z in price.columns if not str(z).startswith("WECC")]
    return ((price[ca] * demand[ca]).sum(axis=1) / demand[ca].sum(axis=1)).to_numpy()


def _measured_price(year: int, settlement: str) -> np.ndarray:
    """Measured CA hub price on the model's non-leap 8760 index.

    ``settlement`` is ``"dam"`` or ``"rtm"``; both disclosures carry ``CA_HUB``.
    """
    f = pd.read_csv(
        LMP / f"CAISO_{settlement}_hourly_{year}.csv",
        parse_dates=["interval_start_gmt"],
    )
    f = f[f["node"] == CA_HUB].copy()
    f["local"] = f["interval_start_gmt"].dt.tz_convert("America/Los_Angeles")
    f = f[~((f["local"].dt.month == 2) & (f["local"].dt.day == 29))]
    h = _model_hour(f["local"], year)
    out = np.full(HOURS, np.nan)
    ok = (h >= 0) & (h < HOURS)
    out[h[ok]] = f["LMP"].to_numpy(dtype=float)[ok]
    return out


def _measured_battery(year: int) -> np.ndarray:
    """Measured battery net MW (discharge +, charge −) on the 8760 frame.

    EIA-930 CISO ``NG: OTH``. Pumped storage is absent from OTH by construction
    (caiso-168 §H), so this is the like-for-like comparator for the model's
    ``li_ion`` limb and carries no PS contamination.
    """
    d = pd.read_parquet(EIA930, columns=["Local date", "Hour", "NG: OTH"])
    d = d[d["Local date"].dt.year == year].copy()
    d = d[~((d["Local date"].dt.month == 2) & (d["Local date"].dt.day == 29))]
    local = d["Local date"] + pd.to_timedelta(d["Hour"].astype(int) - 1, unit="h")
    h = _model_hour(local, year)
    out = np.full(HOURS, np.nan)
    ok = (h >= 0) & (h < HOURS)
    out[h[ok]] = d["NG: OTH"].to_numpy(dtype=float)[ok]
    return out


def _day_percentile(price: np.ndarray) -> np.ndarray:
    """Within-day price percentile in [0, 1] for every hour of the 8760 frame.

    ``(rank − 0.5) / 24`` on each local day's own 24 prices, so a day's hours
    span (0.02, 0.98) and the statistic is scale- and level-free: it measures
    ONLY where in its own day an hour sits, which is exactly what a foresight
    comparison needs (a fleet cannot be credited for a dear day).
    """
    p = price.reshape(DAYS, 24)
    out = np.full_like(p, np.nan, dtype=float)
    for d in range(DAYS):
        row = p[d]
        if np.isnan(row).any():
            continue
        out[d] = (rankdata(row) - 0.5) / 24.0
    return out.reshape(HOURS)


def _weighted(pct: np.ndarray, w: np.ndarray) -> tuple[float, int]:
    """Energy-weighted mean percentile over hours with weight above ZERO_MW."""
    m = np.isfinite(pct) & np.isfinite(w) & (w > ZERO_MW)
    if not m.any() or w[m].sum() <= 0:
        return float("nan"), 0
    return float((pct[m] * w[m]).sum() / w[m].sum()), int(m.sum())


def _capture_efficiency(
    price: np.ndarray, dis: np.ndarray, chg: np.ndarray
) -> tuple[float, float, float, float]:
    """Normalised daily spread capture against its own ceiling and floor.

    For each local day the ceiling re-places the day's OWN hourly dispatch
    magnitudes onto the day's hours in the best possible order (largest
    discharge into the dearest hour, largest charge into the cheapest) and the
    floor into the worst. Same energy, same power profile, only the ORDER
    changes — so the ratio isolates timing and is free of any assumption about
    capacity, efficiency or duration.

    Returns ``(achieved, ceiling, floor, efficiency)`` where efficiency is
    ``(achieved − floor) / (ceiling − floor)`` pooled over days with real
    two-sided activity.
    """
    p = price.reshape(DAYS, 24)
    d_ = dis.reshape(DAYS, 24)
    c_ = chg.reshape(DAYS, 24)
    ach = ceil = flr = 0.0
    n = 0
    for d in range(DAYS):
        pr, dd, cc = p[d], d_[d], c_[d]
        if np.isnan(pr).any() or dd.sum() <= ZERO_MW or cc.sum() <= ZERO_MW:
            continue
        order = np.argsort(pr)  # ascending price
        ds, cs = np.sort(dd)[::-1], np.sort(cc)[::-1]
        # achieved: dispatch where it actually happened
        ach += float(dd @ pr - cc @ pr)
        # ceiling: biggest discharge into dearest hours, biggest charge into cheapest
        best_d = np.zeros(24)
        best_d[order[::-1]] = ds
        best_c = np.zeros(24)
        best_c[order] = cs
        ceil += float(best_d @ pr - best_c @ pr)
        # floor: the exact inversion
        worst_d = np.zeros(24)
        worst_d[order] = ds
        worst_c = np.zeros(24)
        worst_c[order[::-1]] = cs
        flr += float(worst_d @ pr - worst_c @ pr)
        n += 1
    if n == 0 or ceil <= flr:
        return float("nan"), float("nan"), float("nan"), float("nan")
    return ach / n, ceil / n, flr / n, (ach - flr) / (ceil - flr)


def stage_a(state: dict) -> None:
    """Inputs, clock, and a falsifiable self-check of the percentile statistic."""
    print("=" * 88)
    print("A. INPUTS, CLOCK, AND A SELF-CHECK OF THE STATISTIC")
    print("=" * 88)
    print(
        "  The model's OWN dispatch scored on the model's OWN dual must sit near the\n"
        "  ceiling: the LP placed it there with perfect foresight over all 8760 hours.\n"
        "  If this does not come out near 1.0 the statistic is wrong, not the model.\n"
    )
    for y in YEARS:
        st = state[y]
        eff = _capture_efficiency(st["lam"], st["m_dis"], st["m_chg"])[3]
        pct = _day_percentile(st["lam"])
        d_p, nd = _weighted(pct, st["m_dis"])
        c_p, nc = _weighted(pct, st["m_chg"])
        print(
            f"  {y}  model li_ion on MODEL lambda: discharge pct {d_p:.3f} ({nd} h) | "
            f"charge pct {c_p:.3f} ({nc} h) | capture efficiency {eff:.3f}"
        )
        state[y]["selfcheck"] = {
            "dis_pct_model_lambda": d_p,
            "chg_pct_model_lambda": c_p,
            "efficiency_model_lambda": eff,
        }
        cov = {
            k: float(np.isfinite(state[y][k]).mean())
            for k in ("rtm", "dam", "meas_net")
        }
        print(f"        coverage: RT {cov['rtm']:.3f}  DA {cov['dam']:.3f}  EIA-930 {cov['meas_net']:.3f}")
        state[y]["coverage"] = cov


def stage_b(state: dict) -> None:
    """F1 — within-day price percentile of charge/discharge energy, both fleets."""
    print()
    print("=" * 88)
    print("B. F1 — FORESIGHT ADVANTAGE (both fleets scored on the SAME measured price)")
    print("=" * 88)
    print(f"  pre-registered: material iff model − measured >= {F1_MIN_ADVANTAGE:.2f} on RT, in >= {F1_MIN_YEARS} of 3 years\n")
    hdr = f"  {'year':<6}{'settle':<8}{'model dis':>11}{'meas dis':>10}{'adv':>8}   {'model chg':>10}{'meas chg':>10}{'adv':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for y in YEARS:
        st = state[y]
        for s in ("rtm", "dam"):
            pct = _day_percentile(st[s])
            md, _ = _weighted(pct, st["m_dis"])
            mc, _ = _weighted(pct, st["m_chg"])
            xd, _ = _weighted(pct, st["x_dis"])
            xc, _ = _weighted(pct, st["x_chg"])
            print(
                f"  {y:<6}{s.upper():<8}{md:>11.3f}{xd:>10.3f}{md - xd:>+8.3f}   "
                f"{mc:>10.3f}{xc:>10.3f}{mc - xc:>+8.3f}"
            )
            st.setdefault("f1", {})[s] = {
                "model_dis_pct": md,
                "meas_dis_pct": xd,
                "dis_advantage": md - xd,
                "model_chg_pct": mc,
                "meas_chg_pct": xc,
                "chg_advantage": mc - xc,
            }
    print(
        "\n  Reading: a discharge percentile near 1.0 means the fleet sold into its own\n"
        "  day's dearest hours. 'adv' is model minus measured on the same prices, so a\n"
        "  positive discharge adv (or a negative charge adv) is the model timing better."
    )


def stage_c(state: dict) -> None:
    """Normalised spread capture against each series' own ceiling and floor."""
    print()
    print("=" * 88)
    print("C. CAPTURE EFFICIENCY — achieved vs the perfect-foresight ceiling")
    print("=" * 88)
    print("  Same energy, same power profile, only the ORDER of hours changes.\n")
    hdr = f"  {'year':<6}{'settle':<8}{'model eff':>11}{'meas eff':>10}{'gap':>8}   {'model $/d':>11}{'ceil $/d':>11}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for y in YEARS:
        st = state[y]
        for s in ("rtm", "dam"):
            ma, mc_, mf, me = _capture_efficiency(st[s], st["m_dis"], st["m_chg"])
            xa, xc_, xf, xe = _capture_efficiency(st[s], st["x_dis"], st["x_chg"])
            print(
                f"  {y:<6}{s.upper():<8}{me:>11.3f}{xe:>10.3f}{me - xe:>+8.3f}   "
                f"{ma:>11,.0f}{mc_:>11,.0f}"
            )
            st.setdefault("capture", {})[s] = {
                "model_efficiency": me,
                "meas_efficiency": xe,
                "gap": me - xe,
                "model_achieved_usd_per_day": ma,
                "model_ceiling_usd_per_day": mc_,
                "meas_achieved_usd_per_day": xa,
                "meas_ceiling_usd_per_day": xc_,
            }


def stage_d(state: dict) -> None:
    """F2 — do the two settlements ORDER the day differently?"""
    print()
    print("=" * 88)
    print("D. F2 — SETTLEMENT SEPARATION (within-day DA vs RT rank correlation)")
    print("=" * 88)
    print(f"  pre-registered: material iff mean within-day Spearman <= {F2_MAX_RANKCORR:.2f}\n")
    hdr = f"  {'year':<6}{'mean rho':>10}{'p25':>8}{'p50':>8}{'p75':>8}{'days':>7}   {'DA spread':>11}{'RT spread':>11}{'RT/DA':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for y in YEARS:
        st = state[y]
        da, rt = st["dam"].reshape(DAYS, 24), st["rtm"].reshape(DAYS, 24)
        rhos, das, rts = [], [], []
        for d in range(DAYS):
            if np.isnan(da[d]).any() or np.isnan(rt[d]).any():
                continue
            if np.ptp(da[d]) < 1e-9 or np.ptp(rt[d]) < 1e-9:
                continue
            rhos.append(float(spearmanr(da[d], rt[d]).statistic))
            das.append(float(np.ptp(da[d])))
            rts.append(float(np.ptp(rt[d])))
        r = np.asarray(rhos)
        dsp, rsp = float(np.mean(das)), float(np.mean(rts))
        print(
            f"  {y:<6}{r.mean():>10.3f}{np.percentile(r, 25):>8.3f}"
            f"{np.percentile(r, 50):>8.3f}{np.percentile(r, 75):>8.3f}{len(r):>7}   "
            f"{dsp:>11.2f}{rsp:>11.2f}{rsp / dsp:>8.2f}"
        )
        st["f2"] = {
            "mean_rank_corr": float(r.mean()),
            "p25": float(np.percentile(r, 25)),
            "p50": float(np.percentile(r, 50)),
            "p75": float(np.percentile(r, 75)),
            "n_days": len(r),
            "mean_da_daily_spread": dsp,
            "mean_rt_daily_spread": rsp,
            "rt_over_da_spread": rsp / dsp,
        }
    print(
        "\n  Reading: 'spread' is the mean within-day max−min $/MWh each settlement\n"
        "  offers an arbitrageur. rho is how similarly the two settlements RANK the\n"
        "  day's hours — the only thing a second settlement can change about timing."
    )


def stage_e(state: dict) -> None:
    """Reach — where the position sits by hour of day, model vs measured."""
    print()
    print("=" * 88)
    print("E. REACH — the evening/overnight position by window (MW/h mean)")
    print("=" * 88)
    hdr = f"  {'year':<6}{'window':<11}{'model dis':>11}{'meas dis':>10}{'excess':>9}   {'model chg':>11}{'meas chg':>10}{'excess':>9}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for y in YEARS:
        st = state[y]
        for name, hrs in WINDOWS.items():
            m = np.isin(_HOD, list(hrs)) & np.isfinite(st["meas_net"])
            md, xd = float(st["m_dis"][m].mean()), float(st["x_dis"][m].mean())
            mc, xc = float(st["m_chg"][m].mean()), float(st["x_chg"][m].mean())
            print(
                f"  {y:<6}{name:<11}{md:>11,.0f}{xd:>10,.0f}{md - xd:>+9,.0f}   "
                f"{mc:>11,.0f}{xc:>10,.0f}{mc - xc:>+9,.0f}"
            )
            st.setdefault("reach", {})[name] = {
                "model_dis_mw": md,
                "meas_dis_mw": xd,
                "dis_excess_mw": md - xd,
                "model_chg_mw": mc,
                "meas_chg_mw": xc,
                "chg_excess_mw": mc - xc,
            }


def stage_f(state: dict) -> None:
    """Limb split — battery vs the WALLED pumped-storage object."""
    print()
    print("=" * 88)
    print("F. LIMB SPLIT — battery vs the WALLED pumped-storage object")
    print("=" * 88)
    print("  PS has NO measured hourly comparator (caiso-141 wall). Reported, never approximated.\n")
    hdr = f"  {'year':<6}{'limb':<10}{'ann dis GWh':>13}{'ann chg GWh':>13}{'even MW':>10}{'ovn MW':>10}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for y in YEARS:
        st = state[y]
        for limb, d in st["techs"].items():
            ev = np.isin(_HOD, list(WINDOWS["evening"]))
            ov = np.isin(_HOD, list(WINDOWS["overnight"]))
            print(
                f"  {y:<6}{limb:<10}{d['dis'].sum() / 1e3:>13,.0f}{d['chg'].sum() / 1e3:>13,.0f}"
                f"{d['dis'][ev].mean():>10,.0f}{d['dis'][ov].mean():>10,.0f}"
            )
            st.setdefault("limbs", {})[limb] = {
                "annual_discharge_gwh": float(d["dis"].sum() / 1e3),
                "annual_charge_gwh": float(d["chg"].sum() / 1e3),
                "evening_dis_mw": float(d["dis"][ev].mean()),
                "overnight_dis_mw": float(d["dis"][ov].mean()),
            }


def stage_g(state: dict) -> None:
    """The ARMED anchor's own hour-of-day cap against both fleets.

    ``caiso_storage_shape_anchor`` bounds a battery row's charge at
    ``env_p95_chg[year, hod] × power_cap[s, t]``. Where that fraction is
    literally ``0.00`` the model **cannot charge at all** in that hour, whatever
    the price is — so any deficit there is a BOUND, not a timing choice, and no
    foresight mechanism can reach it. ``power_cap`` is recovered by inverting
    the keeper's own dispatch against the committed envelope, exactly as
    ``caiso168_storage_bid_phase0._monthly_power_cap`` does (read, never
    re-derived — rule 23 ``[R-FROZEN-DERIVE]``).
    """
    print()
    print("=" * 88)
    print("G. THE ARMED ANCHOR'S OWN CAP vs BOTH FLEETS (rule 19 — is the channel occupied?)")
    print("=" * 88)
    env = pd.read_csv(ENVELOPE)
    month = np.repeat(np.arange(1, 13), np.array(DAYS_IN_MONTH) * 24)[:HOURS]
    for y in YEARS:
        st = state[y]
        years = sorted(env["year"].unique())
        use = max((v for v in years if v <= y), default=years[0])
        ey = env[env["year"] == use].sort_values("hod")
        f_chg = ey["chg_frac_p95"].to_numpy(dtype=float)
        f_dis = ey["dis_frac_p95"].to_numpy(dtype=float)
        cap = _monthly_power_cap(st["m_chg"], st["m_dis"], f_chg, f_dis, month)
        bound = f_chg[_HOD] * cap
        zero = f_chg == 0.0
        zh = np.isin(_HOD, np.flatnonzero(zero))
        meas_in_zero = float(st["x_chg"][zh].sum() / 1e3)
        meas_total = float(st["x_chg"].sum() / 1e3)
        model_in_zero = float(st["m_chg"][zh].sum() / 1e3)
        print(
            f"\n  {y}  anchor p95 charge cap == 0.00 in hod "
            f"{sorted(np.flatnonzero(zero).tolist())}  (fleet cap {cap.max():,.0f} MW)"
        )
        print(
            f"        model charge in those hours: {model_in_zero:8,.1f} GWh   "
            f"MEASURED fleet charge in the SAME hours: {meas_in_zero:8,.1f} GWh "
            f"({100 * meas_in_zero / meas_total:.1f} % of its year)"
        )
        ovn = np.isin(_HOD, list(WINDOWS["overnight"]))
        print(
            f"        overnight charge deficit {float((st['m_chg'][ovn] - st['x_chg'][ovn]).mean()):+,.0f} MW/h; "
            f"of the measured overnight charge, {100 * float(st['x_chg'][ovn & zh].sum() / max(st['x_chg'][ovn].sum(), 1e-9)):.1f} % "
            f"sits in hours the anchor caps at ZERO"
        )
        live = ovn & (bound > ZERO_MW)
        at_bound = float((st["m_chg"][live] >= 0.995 * bound[live]).mean())
        print(
            f"        in the {int(live.sum())} overnight hours whose cap is NONZERO: model charges "
            f"{float(st['m_chg'][live].mean()):,.1f} MW against a bound of "
            f"{float(bound[live].mean()):,.1f} MW ({100 * at_bound:.1f} % at-bound); "
            f"measured {float(st['x_chg'][live].mean()):,.1f} MW"
        )
        st["anchor"] = {
            "overnight_live_cap_hours": int(live.sum()),
            "overnight_model_chg_mw": float(st["m_chg"][live].mean()),
            "overnight_bound_mw": float(bound[live].mean()),
            "overnight_at_bound_share": at_bound,
            "overnight_meas_chg_mw": float(st["x_chg"][live].mean()),
            "zero_cap_hods": sorted(np.flatnonzero(zero).tolist()),
            "model_charge_in_zero_gwh": model_in_zero,
            "meas_charge_in_zero_gwh": meas_in_zero,
            "meas_share_of_year_in_zero_pct": 100 * meas_in_zero / meas_total,
            "overnight_charge_deficit_mw": float(
                (st["m_chg"][ovn] - st["x_chg"][ovn]).mean()
            ),
            "meas_overnight_charge_share_in_zero_pct": 100
            * float(st["x_chg"][ovn & zh].sum() / max(st["x_chg"][ovn].sum(), 1e-9)),
            "recovered_fleet_cap_mw": float(cap.max()),
            "bound_mean_mw": float(bound.mean()),
        }
    print(
        "\n  Reading: where the anchor's p95 fraction is 0.00 the model's charge bound is\n"
        "  0 MW — a hard prohibition. That is NOT where the deficit is: the measured fleet\n"
        "  puts only a fraction of a percent of its charge there. In the overnight hours\n"
        "  whose cap is LIVE the bound is slack by more than an order of magnitude and the\n"
        "  model is at it in ~1 % of hours, so the overnight charge deficit is the LP\n"
        "  CHOOSING the belly, not the armed anchor forbidding the night."
    )


def verdict(state: dict) -> dict:
    """Score the two pre-registered falsifiers. Thresholds are NOT re-cut."""
    print()
    print("=" * 88)
    print("VERDICT — the two PRE-REGISTERED falsifiers")
    print("=" * 88)
    adv = {y: state[y]["f1"]["rtm"]["dis_advantage"] for y in YEARS}
    n_hit = sum(1 for y in YEARS if adv[y] >= F1_MIN_ADVANTAGE)
    f1 = n_hit >= F1_MIN_YEARS
    rho = {y: state[y]["f2"]["mean_rank_corr"] for y in YEARS}
    mean_rho = float(np.mean(list(rho.values())))
    f2 = mean_rho <= F2_MAX_RANKCORR
    print(
        "  F1 foresight advantage (RT discharge pct, model − measured): "
        + ", ".join(f"{y} {adv[y]:+.3f}" for y in YEARS)
    )
    print(
        f"     >= {F1_MIN_ADVANTAGE:.2f} in {n_hit} of 3 years (need {F1_MIN_YEARS})"
        f"  ->  F1 {'MATERIAL' if f1 else 'IMMATERIAL'}"
    )
    print(
        "  F2 settlement separation (mean within-day DA/RT Spearman): "
        + ", ".join(f"{y} {rho[y]:.3f}" for y in YEARS)
        + f"  mean {mean_rho:.3f}"
    )
    print(
        f"     <= {F2_MAX_RANKCORR:.2f}?  ->  F2 {'MATERIAL' if f2 else 'IMMATERIAL'}"
    )
    if f1 and f2:
        d = "BOTH MATERIAL — S2's object is confirmed and its instrument can reach it; outcome is a CHARTER TO THE OWNER (PRECHECK §4 disposition 1). Nothing is armed in this session."
    elif not f1 and not f2:
        d = "BOTH IMMATERIAL — S2 is demoted for this object on BOTH grounds (PRECHECK §4 dispositions 2+3)."
    elif not f1:
        d = "F1 IMMATERIAL — no foresight advantage to remove; the over-position is a QUANTITY/BOUND object, not a foresight one (PRECHECK §4 disposition 2)."
    else:
        d = "F2 IMMATERIAL — the two settlements order the day near-identically, so the separation cannot reach the position (PRECHECK §4 disposition 3)."
    print(f"\n  {d}")
    return {
        "f1_material": bool(f1),
        "f1_advantage_by_year": {str(y): adv[y] for y in YEARS},
        "f1_years_hit": n_hit,
        "f2_material": bool(f2),
        "f2_rank_corr_by_year": {str(y): rho[y] for y in YEARS},
        "f2_mean_rank_corr": mean_rho,
        "disposition": d,
    }


def main() -> int:
    global BUNDLE
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=BUNDLE,
        help="keeper bundle hourly/ directory (default: the current CAISO keeper)",
    )
    ap.add_argument(
        "--out", type=Path, default=OUT, help="where to write the JSON artifact"
    )
    args = ap.parse_args()
    BUNDLE = args.bundle.resolve()
    state: dict = {}
    for y in YEARS:
        techs = _storage(y)
        li = techs.get("li_ion", {"chg": np.zeros(HOURS), "dis": np.zeros(HOURS)})
        net = _measured_battery(y)
        state[y] = {
            "techs": techs,
            "m_chg": li["chg"],
            "m_dis": li["dis"],
            "x_chg": np.nan_to_num(np.maximum(-net, 0.0)),
            "x_dis": np.nan_to_num(np.maximum(net, 0.0)),
            "meas_net": net,
            "lam": _ca_lambda(y),
            "rtm": _measured_price(y, "rtm"),
            "dam": _measured_price(y, "dam"),
        }
    stage_a(state)
    stage_b(state)
    stage_c(state)
    stage_d(state)
    stage_e(state)
    stage_f(state)
    stage_g(state)
    v = verdict(state)

    payload = {
        "session": "caiso-170",
        "keeper_bundle": str(BUNDLE.relative_to(REPO)),
        "ca_hub": CA_HUB,
        "prereg": {
            "f1_min_advantage": F1_MIN_ADVANTAGE,
            "f1_min_years": F1_MIN_YEARS,
            "f2_max_rank_corr": F2_MAX_RANKCORR,
        },
        "verdict": v,
        "years": {
            str(y): {
                k: state[y][k]
                for k in ("selfcheck", "coverage", "f1", "capture", "f2", "reach", "limbs", "anchor")
            }
            for y in YEARS
        },
    }
    out_path = args.out.resolve()
    out_path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    try:
        shown = out_path.relative_to(REPO)
    except ValueError:
        shown = out_path
    print(f"\nwrote {shown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
