"""miso-176 Phase 0 — the M2M/CMP seam-class binding-reality measurement.

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``): every number is a measurement of the curated
``miso-m2m-flowgates`` record against the committed keeper artifacts and
measured actuals, written to a JSON record for the finding. Gates, kills and
the verdict mapping were fixed in
``PREREG-miso176-m2m-seam-class-adjudication-2026-08-22.md`` (commit 75b8488)
BEFORE this probe first ran.

Stages:
  0 V-KEY    — verify the settlement file's clock by joining MISO-monitored
               M2M flowgates to ``2025_rt_bc_HIST`` on NERC ID and
               correlating hourly shadow series under key shifts −3..+3.
  1 sets     — the miso-174 hour sets on the CURRENT keeper
               (``miso175_hourkey``); V-SETS n-check; V-VINTAGE drift of the
               ``miso169_gated_A`` per-seam split vs the keeper.
  2 A-1/A-2  — coordination presence and binding elevation at MISO stress,
               per seam per year (count and Σ-shadow bases), with the ±1 h
               key-robustness re-run.
  3 A-3      — association of PJM-seam binding with the MEASURED seam flow
               (summer r + the top-quartile-binding vs zero-binding split).
  4 A-4      — entitlement headroom (D = mkt_flow − ffe) distributions per
               seam per hour set; model gross import context
               (vintage-disclosed). No flowgate-MW↔seam-MW claim.
  5 A-5      — verbatim scarce-hour binding census (the naming evidence).

Run:  python3 scripts/probes/_miso176_m2m_seam_binding.py
"""

from __future__ import annotations

import gzip
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402

CAL = ROOT / "results" / "calibration"
KEEPER = CAL / "miso175_hourkey" / "hourly"            # current keeper
UNITBUNDLE = CAL / "miso169_gated_A" / "hourly"        # only MISO bundle with unit_hourly
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
E930_REGION = ROOT / "data" / "raw" / "MISO_region.parquet"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
CLEAN_M2M = ROOT / "data" / "clean" / "miso-m2m-flowgates" / "MISO"
BC_HIST_2025 = ROOT / "data" / "raw" / "transfer-constraint-binding" / "MISO" / "2025_rt_bc_HIST.csv.gz"
OUT = CAL / "_miso176_m2m_seam_binding.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
SCARCE_RT = 200.0    # miso-167 §1 scarcity line
FORESEEN_DA = 150.0  # miso-167 §5 DA-foreseen line
TOPN = 47            # top-load scarce set size
DIBA_SHIFT_H = -1    # the keeper-armed hour-ending correction (miso-175, DO-NOT-REDO)
SEAMS = ("PJM", "SWPP")

# PREREG §5-§6 fixed lines (kept as named constants so the console verdicts
# cite the registered numbers, not re-typed ones).
VKEY_MIN_POOLED_R = 0.8
VKEY_MIN_PAIRS = 3
VKEY_MIN_SHARED_BINDING_H = 100
A1_PARTIAL_REACH_SHARE = 0.80
A2_CNT_COMOVES = 1.5
A2_SSP_COMOVES = 2.0
A2_CNT_REFUTED = 1.2
A2_SSP_REFUTED = 1.5
A3_SPLIT_GW = 0.3


# --------------------------------------------------------------------------
# keeper / actuals loaders (the miso-174 constructions, keeper re-pointed)
# --------------------------------------------------------------------------
def model_system(year: int) -> pd.DataFrame:
    """Load-weighted P1 system price and total demand per hour."""
    d = pd.read_parquet(KEEPER / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    d["pw"] = d["price"] * d["demand"]
    g = d.groupby("hour").agg(pw=("pw", "sum"), demand=("demand", "sum"))
    g["price"] = g["pw"] / g["demand"]
    return g.drop(columns="pw").reset_index()


def model_net_import(year: int) -> pd.Series:
    """P1 net interchange per hour (MW) = the signed ``import`` class total."""
    cls = pd.read_parquet(KEEPER / f"class_hourly_{year}.parquet")
    cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
    return cls.groupby("hour")["mw"].sum().reindex(range(HOURS), fill_value=0.0)


def actual_lmp(year: int) -> pd.DataFrame:
    """MISO's measured RT and DA hub LMP for ``year``, on the model hour key."""
    a = pd.read_parquet(ACTUAL)
    return a[a["year"] == year][["hour", "rt", "da"]].reset_index(drop=True)


def e930_balance(year: int) -> pd.DataFrame:
    """EIA-930 MISO demand (D) and total interchange (TI) on the CST hour key."""
    d = pd.read_parquet(E930_REGION)
    d = d[d["type"].isin(["D", "TI"])].copy()
    d["cst"] = d["period"] - pd.Timedelta(hours=6)
    d = d[d["cst"].dt.year == year]
    d = d[~((d["cst"].dt.month == 2) & (d["cst"].dt.day == 29))]
    w = d.pivot_table(index="cst", columns="type", values="value_mwh", aggfunc="first").sort_index()
    w["hour"] = np.arange(len(w))
    return w.reset_index()[["hour", "D", "TI"]]


def _model_hour_index(ts: pd.DatetimeIndex, year: int) -> tuple[np.ndarray, np.ndarray]:
    """Map CST hour-beginning stamps onto the fixed non-leap 8760 clock.

    Returns (keep_mask, hour_index). Feb 29 is dropped and later days shift
    back one, so a leap year maps onto the same 8760 positions (the
    miso-174 ``diba_wide`` recipe).
    """
    keep = (ts.year == year) & ~((ts.month == 2) & (ts.day == 29))
    tk = ts[keep]
    doy = tk.dayofyear.to_numpy()
    if bool(pd.Timestamp(f"{year}-12-31").dayofyear == 366):
        doy = np.where(doy > 60, doy - 1, doy)  # Feb 29 is day-of-year 60
    hour = (doy - 1) * 24 + tk.hour.to_numpy()
    return np.asarray(keep), hour


def diba_pjm_net_import(year: int) -> np.ndarray:
    """Measured PJM-seam net import (MW, + = MISO imports), keeper key (−1 h)."""
    d = pd.read_parquet(E930_DIBA).copy()
    ts = pd.DatetimeIndex(d["local_time"]) + pd.Timedelta(hours=DIBA_SHIFT_H)
    keep, hour = _model_hour_index(ts, year)
    d = d[keep].assign(hour=hour)
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)]
    cols = set(MISO_SEAM_DIBA["PJM"])
    d = d[d["diba"].astype(str).isin(cols)]
    w = d.pivot_table(index="hour", columns="diba", values="mw", aggfunc="first")
    return (-w.sum(axis=1, min_count=1)).reindex(range(HOURS)).to_numpy()


def model_seam_flows(year: int):
    """Per-seam model gross import/export (MW) from the priced-seam rows."""
    d = pd.read_parquet(
        UNITBUNDLE / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "fuel", "hour", "mw"],
    )
    d = d[(d["pass"] == "P1") & (d["fuel"].astype(str) == "import")]
    uid = d["unit_id"].astype(str)
    seam = uid.str.extract(r"_ref(?:imp|exp)_([A-Za-z]+)#", expand=False)
    side = np.where(uid.str.contains("_refimp_"), "imp", "exp")
    work = pd.DataFrame({"seam": seam.to_numpy(), "side": side,
                         "hour": d["hour"].to_numpy(), "mw": d["mw"].to_numpy()})
    net = work.pivot_table(index="hour", columns="seam", values="mw", aggfunc="sum")
    by_side = work.pivot_table(index="hour", columns=["seam", "side"], values="mw", aggfunc="sum")
    return (net.reindex(range(HOURS)).fillna(0.0),
            by_side.reindex(range(HOURS)).fillna(0.0))


def hour_sets(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """The miso-174 scored hour sets as boolean masks over the 8760 clock."""
    su = (df["hour"] >= SUMMER[0]) & (df["hour"] < SUMMER[1])
    scarce = su & (df["rt"] > SCARCE_RT)
    top = np.zeros(len(df), dtype=bool)
    idx = df.loc[su].nlargest(TOPN, "demand").index
    top[idx] = True
    return {
        "annual": np.ones(len(df), dtype=bool),
        "summer": su.to_numpy(),
        "summer_scarce_rt200": scarce.to_numpy(),
        "summer_top47_load": top,
        "scarce_da_foreseen": (scarce & (df["da"] > FORESEEN_DA)).to_numpy(),
        "scarce_rt_only": (scarce & (df["da"] <= FORESEEN_DA)).to_numpy(),
    }


# --------------------------------------------------------------------------
# M2M record on the model clock
# --------------------------------------------------------------------------
def m2m_frame(year: int, key_shift_h: int = 0) -> pd.DataFrame:
    """The curated M2M record for ``year`` mapped onto the model hour key.

    ``key_shift_h`` perturbs the documented key (0) for the V-KEY sweep and
    the pre-registered ±1 h robustness re-run. Model CST hour-beginning =
    EST hour-beginning − 1 h (+ shift). The year's first CST hour
    (Dec 31 23:00 CST of year−1 under the documented key) sits in the
    previous partition and the last is uncovered by construction — a
    one-winter-hour boundary effect, disclosed in the record.
    """
    d = pd.read_parquet(CLEAN_M2M / f"miso-m2m-flowgates_{year}.parquet")
    est = pd.DatetimeIndex(d["interval_start_est"])
    cst = est + pd.Timedelta(hours=-1 + key_shift_h)
    keep, hour = _model_hour_index(cst, year)
    d = d[keep].assign(hour=hour)
    d = d[(d["hour"] >= 0) & (d["hour"] < HOURS)].copy()
    mon = d["monitoring_rto"].to_numpy()
    miso_sp = d["miso_shadow_price_usd_mwh"].fillna(0.0).to_numpy()
    cp_sp = d["cp_shadow_price_usd_mwh"].fillna(0.0).to_numpy()
    d["mon_sp"] = np.where(mon == "MISO", miso_sp,
                           np.where(np.isin(mon, ("PJM", "SWPP")), cp_sp,
                                    np.maximum(miso_sp, cp_sp)))  # tiny NO-RTO class
    d["binding"] = d["mon_sp"] > 0.0
    d["binding_either"] = (miso_sp > 0.0) | (cp_sp > 0.0)
    d["d_miso"] = d["miso_mkt_flow_mw"] - d["miso_ffe_mw"]
    d["d_cp"] = d["cp_mkt_flow_mw"] - d["cp_ffe_mw"]
    return d


def seam_hourly(d: pd.DataFrame, seam: str) -> pd.DataFrame:
    """Per-model-hour coordination/binding intensity series for one seam."""
    g = d[d["seam_rto"] == seam].groupby("hour")
    out = pd.DataFrame({
        "n_coord": g.size(),
        "n_bind": g["binding"].sum(),
        "n_bind_either": g["binding_either"].sum(),
        "ssp": g.apply(lambda x: float(x.loc[x["binding"], "mon_sp"].sum())),
    })
    return out.reindex(range(HOURS), fill_value=0.0)


# --------------------------------------------------------------------------
# stage 0 — V-KEY
# --------------------------------------------------------------------------
def stage0_vkey() -> dict:
    """Verify the settlement clock against rt_bc_HIST on the NERC-ID join."""
    raw = gzip.open(BC_HIST_2025, "rb").read().decode("utf-8", errors="replace")
    bc = pd.read_csv(io.StringIO(raw), skiprows=2, dtype=str, on_bad_lines="skip")
    bc = bc.rename(columns={c: c.strip() for c in bc.columns})
    bc = bc[["Market Date", "Flowgate NERCID", "Hour of Occurrence",
             "Preliminary Shadow Price"]].dropna(subset=["Market Date", "Flowgate NERCID"])
    bc = bc[bc["Flowgate NERCID"].str.fullmatch(r"\d+", na=False)].copy()
    bc["fg"] = bc["Flowgate NERCID"].astype(int)
    date = pd.to_datetime(bc["Market Date"], format="%m/%d/%Y", errors="coerce")
    tod = bc["Hour of Occurrence"].str.extract(r"^(\d{1,2}):(\d{2})$")
    ok = date.notna() & tod[0].notna()
    bc = bc[ok]
    # interval-START labels 00:00..23:55 EST (the PBC/bc_HIST convention).
    est = (pd.DatetimeIndex(date[ok])
           + pd.to_timedelta(tod.loc[ok, 0].astype(int), unit="h"))
    sp = (bc["Preliminary Shadow Price"].str.replace(r"[$,()]", "", regex=True)
          .astype(float))  # accounting negatives; magnitude is what we use
    cst = pd.DatetimeIndex(est) - pd.Timedelta(hours=1)
    keep, hour = _model_hour_index(cst, 2025)
    work = pd.DataFrame({"fg": bc["fg"].to_numpy()[keep], "hour": hour,
                         "absp": np.abs(sp.to_numpy()[keep])})
    work = work[(work["hour"] >= 0) & (work["hour"] < HOURS)]
    # hourly MEAN over all 12 intervals (absent intervals are zero).
    bc_hr = work.groupby(["fg", "hour"])["absp"].sum() / 12.0

    m2m = m2m_frame(2025, 0)
    miso_mon = m2m[m2m["monitoring_rto"] == "MISO"]
    cand = (miso_mon[miso_mon["binding"]].groupby("flowgate_id").size()
            .sort_values(ascending=False))
    cand = cand[cand >= 300]
    pairs, per_pair = [], {}
    for fg in cand.index:
        if fg not in bc_hr.index.get_level_values(0):
            continue
        b = bc_hr.loc[fg].reindex(range(HOURS), fill_value=0.0).to_numpy()
        shared = int(((b > 0)
                      & miso_mon[miso_mon["flowgate_id"] == fg]
                      .set_index("hour")["binding"].reindex(range(HOURS), fill_value=False)
                      .to_numpy()).sum())
        if shared < VKEY_MIN_SHARED_BINDING_H:
            continue
        pairs.append(fg)
        per_pair[int(fg)] = {"bc_binding_hours": int((b > 0).sum()), "shared_binding_hours": shared}
        if len(pairs) >= 8:
            break

    shifts = {}
    for shift in range(-3, 4):
        mm = m2m_frame(2025, shift) if shift else m2m
        mmm = mm[mm["monitoring_rto"] == "MISO"]
        rs = []
        for fg in pairs:
            a = (mmm[mmm["flowgate_id"] == fg].set_index("hour")["miso_shadow_price_usd_mwh"]
                 .reindex(range(HOURS), fill_value=0.0).to_numpy())
            b = bc_hr.loc[fg].reindex(range(HOURS), fill_value=0.0).to_numpy()
            if a.std() > 0 and b.std() > 0:
                rs.append(float(np.corrcoef(a, b)[0, 1]))
        shifts[str(shift)] = {"mean_r": float(np.mean(rs)) if rs else float("nan"),
                              "n_pairs": len(rs)}
    best = max(shifts, key=lambda k: (shifts[k]["mean_r"]
                                      if np.isfinite(shifts[k]["mean_r"]) else -9))
    r0 = shifts["0"]["mean_r"]
    verdict = ("PASS" if best == "0" and np.isfinite(r0) and r0 >= VKEY_MIN_POOLED_R
               else ("FALLBACK-STRUCTURAL" if len(pairs) < VKEY_MIN_PAIRS else "FAIL"))
    return {"pairs": [int(f) for f in pairs], "per_pair": per_pair,
            "shift_sweep": shifts, "best_shift": int(best), "r_at_0": r0,
            "verdict": verdict}


# --------------------------------------------------------------------------
def build_frames() -> dict[int, pd.DataFrame]:
    """One per-hour frame per year joining keeper output to measured actuals."""
    frames = {}
    for y in YEARS:
        df = model_system(y).merge(actual_lmp(y), on="hour").merge(
            e930_balance(y), on="hour", how="left")
        df["model_net"] = model_net_import(y).to_numpy()
        frames[y] = df
    return frames


def _mean(a: np.ndarray, m: np.ndarray) -> float:
    return float(np.nanmean(a[m])) if m.sum() else float("nan")


def stage1_sets(frames) -> dict:
    """Hour sets + V-SETS + V-VINTAGE drift of the unit_hourly proxy."""
    out: dict = {}
    for y, df in frames.items():
        sets = hour_sets(df)
        net, by_side = model_seam_flows(y)
        proxy = net.sum(axis=1).to_numpy()
        keeper = df["model_net"].to_numpy()
        out[str(y)] = {
            "n": {k: int(m.sum()) for k, m in sets.items()},
            "v_vintage_drift_gw": {
                k: {"proxy": _mean(proxy, m) / 1000, "keeper": _mean(keeper, m) / 1000,
                    "drift": _mean(proxy - keeper, m) / 1000}
                for k, m in sets.items() if m.sum()},
        }
    vsets = all(out[str(y)]["n"]["summer_scarce_rt200"] == n
                for y, n in zip(YEARS, (11, 14, 47)))
    return {"per_year": out, "v_sets_n_match": bool(vsets)}


def stage2_binding(frames, key_shift_h: int = 0) -> dict:
    """A-1 presence + A-2 elevation, per seam per year, at one key shift."""
    out: dict = {}
    for y, df in frames.items():
        d = m2m_frame(y, key_shift_h)
        sets = hour_sets(df)
        su, sc = sets["summer"], sets["summer_scarce_rt200"]
        row: dict = {}
        for seam in SEAMS:
            h = seam_hourly(d, seam)
            n_coord = h["n_coord"].to_numpy()
            n_bind = h["n_bind"].to_numpy()
            n_be = h["n_bind_either"].to_numpy()
            ssp = h["ssp"].to_numpy()
            per_set = {}
            for name, m in sets.items():
                if not m.sum():
                    continue
                per_set[name] = {
                    "n": int(m.sum()),
                    "share_hours_any_coord": float(np.mean(n_coord[m] > 0)),
                    "share_hours_any_binding": float(np.mean(n_bind[m] > 0)),
                    "mean_n_coord": float(np.mean(n_coord[m])),
                    "mean_n_bind": float(np.mean(n_bind[m])),
                    "mean_n_bind_either": float(np.mean(n_be[m])),
                    "mean_ssp": float(np.mean(ssp[m])),
                    "max_ssp": float(np.max(ssp[m])),
                }
            r_cnt = (per_set["summer_scarce_rt200"]["mean_n_bind"]
                     / max(per_set["summer"]["mean_n_bind"], 1e-9))
            r_ssp = (per_set["summer_scarce_rt200"]["mean_ssp"]
                     / max(per_set["summer"]["mean_ssp"], 1e-9))
            r_cnt_e = (per_set["summer_scarce_rt200"]["mean_n_bind_either"]
                       / max(per_set["summer"]["mean_n_bind_either"], 1e-9))
            row[seam] = {"sets": per_set,
                         "a2_ratio_count": float(r_cnt),
                         "a2_ratio_ssp": float(r_ssp),
                         "a2_ratio_count_either": float(r_cnt_e),
                         "a1_scarce_share_any_coord":
                             per_set["summer_scarce_rt200"]["share_hours_any_coord"],
                         "a1_scarce_share_any_binding":
                             per_set["summer_scarce_rt200"]["share_hours_any_binding"]}
        out[str(y)] = row
    return out


def stage3_association(frames) -> dict:
    """A-3: binding vs the MEASURED PJM-seam net import, summer hours."""
    out: dict = {}
    for y, df in frames.items():
        d = m2m_frame(y, 0)
        h = seam_hourly(d, "PJM")
        meas = diba_pjm_net_import(y)
        sets = hour_sets(df)
        su = sets["summer"]
        ok = su & np.isfinite(meas)
        nb, ssp = h["n_bind"].to_numpy(), h["ssp"].to_numpy()
        r_nb = float(np.corrcoef(meas[ok], nb[ok])[0, 1]) if ok.sum() > 10 else float("nan")
        r_ssp = float(np.corrcoef(meas[ok], ssp[ok])[0, 1]) if ok.sum() > 10 else float("nan")
        # directional split: top-quartile-binding (by SSP among binding hours)
        # vs zero-binding summer hours.
        bind_hours = ok & (nb > 0)
        zero_hours = ok & (nb == 0)
        if bind_hours.sum() >= 8:
            q75 = float(np.quantile(ssp[bind_hours], 0.75))
            top = bind_hours & (ssp >= q75)
        else:
            top = bind_hours
        out[str(y)] = {
            "n_summer": int(ok.sum()), "n_binding_hours": int(bind_hours.sum()),
            "n_zero_binding_hours": int(zero_hours.sum()), "n_top_quartile": int(top.sum()),
            "r_meas_import_vs_n_bind": r_nb, "r_meas_import_vs_ssp": r_ssp,
            "mean_meas_import_top_binding_gw": _mean(meas, top) / 1000,
            "mean_meas_import_zero_binding_gw": _mean(meas, zero_hours) / 1000,
            "mean_meas_import_summer_gw": _mean(meas, ok) / 1000,
            "split_gw": (_mean(meas, top) - _mean(meas, zero_hours)) / 1000,
        }
    return out


def stage4_headroom(frames) -> dict:
    """A-4: entitlement state distributions per seam per hour set."""
    out: dict = {}
    for y, df in frames.items():
        d = m2m_frame(y, 0)
        _, by_side = model_seam_flows(y)
        sets = hour_sets(df)
        row: dict = {}
        for seam in SEAMS:
            ds = d[d["seam_rto"] == seam]
            per_set = {}
            for name, m in sets.items():
                if not m.sum():
                    continue
                hours = np.flatnonzero(m)
                sub = ds[ds["hour"].isin(hours)]
                bind = sub[sub["binding"]]
                dm = sub["d_miso"].dropna()
                dmb = bind["d_miso"].dropna()
                # CP entitlement state exists only on MISO-monitored rows.
                cpb = bind[bind["monitoring_rto"] == "MISO"]["d_cp"].dropna()
                gross_imp = (by_side[(seam, "imp")].to_numpy()
                             if (seam, "imp") in by_side.columns else np.zeros(HOURS))
                per_set[name] = {
                    "n_hours": int(m.sum()),
                    "n_coord_rows": int(len(sub)),
                    "n_binding_rows": int(len(bind)),
                    "n_distinct_binding_fg": int(bind["flowgate_id"].nunique()),
                    "d_miso_mean_mw": float(dm.mean()) if len(dm) else float("nan"),
                    "d_miso_p90_mw": float(dm.quantile(0.9)) if len(dm) else float("nan"),
                    "d_miso_max_mw": float(dm.max()) if len(dm) else float("nan"),
                    "share_binding_rows_miso_over_ffe":
                        float((dmb > 0).mean()) if len(dmb) else float("nan"),
                    "share_binding_rows_cp_over_ffe":
                        float((cpb > 0).mean()) if len(cpb) else float("nan"),
                    "model_gross_import_gw": _mean(gross_imp, m) / 1000,
                }
            row[seam] = per_set
        out[str(y)] = row
    return out


def stage5_census(frames) -> dict:
    """A-5: verbatim binding census of the 72 scarce hours (PJM seam)."""
    out: dict = {}
    for y, df in frames.items():
        d = m2m_frame(y, 0)
        sets = hour_sets(df)
        rows = []
        dp = d[(d["seam_rto"] == "PJM") & d["binding"]]
        dsw = d[(d["seam_rto"] == "SWPP") & d["binding"]]
        for h in np.flatnonzero(sets["summer_scarce_rt200"]):
            sub = dp[dp["hour"] == h].sort_values("mon_sp", ascending=False)
            rows.append({
                "hour": int(h),
                "actual_rt": float(df.loc[df["hour"] == h, "rt"].iloc[0]),
                "n_swpp_binding": int((dsw["hour"] == h).sum()),
                "pjm_binding": [
                    {"fg": int(r.flowgate_id), "name": str(r.flowgate_name)[:60],
                     "mon": str(r.monitoring_rto), "sp": round(float(r.mon_sp), 1),
                     "d_miso_mw": (round(float(r.d_miso), 1)
                                   if np.isfinite(r.d_miso) else None)}
                    for r in sub.itertuples()],
            })
        out[str(y)] = rows
    return out


def stage6_exploratory(frames) -> dict:
    """EXPLORATORY (post-registration context, NOT a gate — added after the
    pre-registered gates first resolved on this record's stage-2/3 values):
    within the scarce hours, does the measured seam pull-back concentrate in
    the hours where PJM-seam M2M flowgates were actually binding?
    """
    out: dict = {}
    for y, df in frames.items():
        d = m2m_frame(y, 0)
        h = seam_hourly(d, "PJM")
        nb = h["n_bind"].to_numpy()
        meas = diba_pjm_net_import(y)
        sets = hour_sets(df)
        sc, su = sets["summer_scarce_rt200"], sets["summer"]
        okm = np.isfinite(meas)
        b = sc & (nb > 0) & okm
        nbnd = sc & (nb == 0) & okm
        out[str(y)] = {
            "n_scarce_binding": int(b.sum()), "n_scarce_nonbinding": int(nbnd.sum()),
            "meas_import_scarce_binding_gw": _mean(meas, b) / 1000,
            "meas_import_scarce_nonbinding_gw": _mean(meas, nbnd) / 1000,
            "meas_import_summer_mean_gw": _mean(meas, su & okm) / 1000,
        }
    return out


# --------------------------------------------------------------------------
def main() -> None:
    """Run all stages, write the JSON record, print the gate verdicts."""
    vkey = stage0_vkey()
    frames = build_frames()
    s1 = stage1_sets(frames)
    s2 = {"shift_0": stage2_binding(frames, 0),
          "shift_-1": stage2_binding(frames, -1),
          "shift_+1": stage2_binding(frames, +1)}
    s3 = stage3_association(frames)
    s4 = stage4_headroom(frames)
    s5 = stage5_census(frames)
    s6 = stage6_exploratory(frames)

    rec = {
        "session": "miso-176",
        "prereg": "PREREG-miso176-m2m-seam-class-adjudication-2026-08-22.md @ 75b8488",
        "keeper_bundle": "miso175_hourkey",
        "unit_hourly_bundle": "miso169_gated_A",
        "m2m_clock_note": ("documented key: hour-ending 1..24 fixed-EST -> "
                           "hour-beginning EST -> CST = -1 h; one winter "
                           "boundary hour per year uncovered by construction"),
        "stage0_vkey": vkey,
        "stage1_sets": s1,
        "stage2_binding": s2,
        "stage3_association": s3,
        "stage4_headroom": s4,
        "stage5_census": s5,
        "stage6_exploratory_postreg": s6,
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}")

    print(f"\n== V-KEY: {vkey['verdict']} (best shift {vkey['best_shift']:+d}, "
          f"r(0) = {vkey['r_at_0']:.4f}, {len(vkey['pairs'])} pairs) ==")
    print(f"== V-SETS n match: {s1['v_sets_n_match']} ==")
    for y in YEARS:
        r = s2["shift_0"][str(y)]["PJM"]
        print(f"\n{y} PJM seam: A-1 coord {r['a1_scarce_share_any_coord']*100:.0f}% / "
              f"binding {r['a1_scarce_share_any_binding']*100:.0f}% of scarce hours; "
              f"A-2 R_cnt {r['a2_ratio_count']:.2f} R_ssp {r['a2_ratio_ssp']:.2f} "
              f"(scarce mean_n_bind {r['sets']['summer_scarce_rt200']['mean_n_bind']:.2f} "
              f"vs summer {r['sets']['summer']['mean_n_bind']:.2f})")
        a3 = s3[str(y)]
        print(f"     A-3: r(imp,nb) {a3['r_meas_import_vs_n_bind']:+.3f}  "
              f"split top-binding {a3['mean_meas_import_top_binding_gw']:+.2f} vs "
              f"zero-binding {a3['mean_meas_import_zero_binding_gw']:+.2f} GW "
              f"(delta {a3['split_gw']:+.2f})")


if __name__ == "__main__":
    main()
