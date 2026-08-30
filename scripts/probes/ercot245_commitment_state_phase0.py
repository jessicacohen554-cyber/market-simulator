"""ercot-245 Phase-0: zero-solve census of the PER-CLASS commitment-state
(slow-start reachability) bound against the FORWARD keeper's committed
sidecars, the delivery-2023 all-resource SCED corpus, and the 2025 tail-day
extract.

Executes exactly the constructions, V-0 anchors, transfer tests and kills
declared ex ante in ``docs/PRECOMMIT-ercot245-commitment-state-phase0-
2026-08-30.md`` (pushed and blob-verified 104e87e3 before this ran).
ZERO-SOLVE: committed sidecars + committed actuals + measured series + a
fidelity-guarded no-LP fleet reconstruction. No lever, no config change, no
matrix verdict move.

Run (keeper-pinned venv, outside the project dir):
    /root/ercot245-venv/bin/python scripts/probes/ercot245_commitment_state_phase0.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data",
           Path(__file__).resolve().parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results" / "calibration" / "ercot234_eastex_identity"
ACTUALS = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
EIA_WIDE = REPO / "data/raw/eia-930-hourly/ERCO hourly.parquet"
MEASURED_ORDC = REPO / "data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
EXTRACT_2025 = (REPO / "data/raw/ercot/60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_"
                       "Resource_Data_2025_ercot86_tail_days.parquet")
OUT_JSON = REPO / "results/calibration/ercot245_commitment_state_phase0.json"

SCORED_YEARS = (2024, 2025)
REPORT_YEAR = 2023

# Precommit §1: committed ercot-244 populations (V-0 a, exact).
V0_MODEL_TAIL = {2024: 22, 2025: 1}
V0_ACTUAL_TAIL = {2024: 53, 2025: 31}
V0_MISSED = {2023: 115, 2024: 36, 2025: 31}
V0_RTOLHSL_EVENING_GW = {2023: 58.87, 2024: 62.64, 2025: 67.81}
V0_E163_CC_CAPREF_GW = 35.2601  # committed _ercot163_cc_commitment.json

# Precommit §2a: the four census classes.
CENSUS = {
    "CC":   {"restypes": ("CCGT90", "CCLE90"), "klass": ("CC_REGULAR",),
             "groups": ("CC_REGULAR",)},
    "ST":   {"restypes": ("GSREH", "GSNONR", "GSSUP"), "klass": ("ST_GAS",),
             "groups": ("ST_GAS",)},
    "COAL": {"restypes": ("CLLIG",), "klass": ("COAL_PRB", "COAL_LIGNITE"),
             "groups": ("COAL",)},
    "NUC":  {"restypes": ("NUC",), "klass": ("NUCLEAR",),
             "groups": ("NUCLEAR",)},
}
SLOW_RESTYPES = tuple(t for c in CENSUS.values() for t in c["restypes"])
CHP_KLASS = {"CC": ("CC_CHP",), "ST": ("ST_CHP",), "COAL": (), "NUC": ()}

# Precommit §2b: state buckets.
ONLINE_STATES = ("ONLINE", "ONTEST", "TRANSITION")
STARTABLE_STATES = ("OFFLINE_STARTABLE",)
COLD_STATES = ("OFFLINE_OTHER", "OTHER")
NOT_AVAIL_STATES = ("OUT",)  # + ABSENT (implicit: never telemetered)

# ercot-244 conventions reused verbatim.
FAST_PRODUCTS = ("RegUp", "RRS", "ECRS")
FAST_FAMILY_NAMES = tuple(
    n for p in FAST_PRODUCTS for n in (p, f"{p}_withheld", f"{p}_released"))
EIA_KEEP = {"NG: NG", "NG: COL", "NG: NUC"}
ORDINARY_BAR = 150.0
TAIL_BAR = 200.0

# Precommit §2d / §5 / §6 declared constants.
N_BINS = 10
T1_MEDREL_BAND = 0.15
T2_FRAC_BAR = 0.05
T2_P95_OVERSHOOT_MW = 2000.0
T3_AGREE_FLOOR = 0.60
T3_COVERAGE_FLOOR = 16  # of 31 M_2025 hours
KB_REACH_FLOOR = 0.20
KC_ORDINARY_BAR = 150
KA_CAP_LE0_BAR = 24
KA_MASS_FRAC = 0.25
UNIVERSE_BAND = (0.80, 1.60)

_READ_COLS = ["SCED Time Stamp", "Resource Name", "Resource Type",
              "Telemetered Resource Status", "HSL"]


def _sidecar(name: str, year: int) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"{name}_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df[df["year"] == year] if "year" in df.columns else df


def _eia_year(year: int) -> pd.DataFrame:
    """EIA-930 wide extract mapped to the local 8760 — ercot-243/244 verbatim."""
    df = pd.read_parquet(EIA_WIDE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    local = utc.dt.tz_convert("America/Chicago").dt.tz_localize(None)
    hour_ending = local - pd.Timedelta(hours=1)
    keep = (hour_ending.dt.year == year) & ~(
        (hour_ending.dt.month == 2) & (hour_ending.dt.day == 29))
    out = df[keep].assign(_utc=utc[keep]).sort_values("_utc").reset_index(drop=True)
    assert len(out) == 8760, f"EIA-930 local-{year} rows = {len(out)} != 8760"
    return out


def _q(arr: np.ndarray, p: float) -> float:
    return float(np.quantile(arr, p)) if arr.size else float("nan")


def _nan0(a) -> np.ndarray:
    return np.nan_to_num(np.asarray(a, dtype=float))


# --------------------------------------------------------------------------
# Model side (ercot-244 verbatim reads)
# --------------------------------------------------------------------------

def model_year(year: int) -> dict:
    rng = range(8760)
    sys_df = _sidecar("system", year)
    g = sys_df.groupby("hour")

    def _s(series: pd.Series) -> np.ndarray:
        return series.reindex(rng).to_numpy(float)

    maxz = np.nan_to_num(_s(g["price"].max()), nan=-np.inf)
    num = (sys_df["price"] * sys_df["demand"]).groupby(sys_df["hour"]).sum()
    model_dw = np.nan_to_num(_s(num / g["demand"].sum()))
    mdl_dem = np.nan_to_num(_s(g["demand"].sum()))

    a_df = pd.read_parquet(ACTUALS)
    actual = a_df[a_df["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]
    assert actual.size == 8760, f"actuals {year}: {actual.size} rows"

    ch = _sidecar("class_hourly", year)
    have = {str(k).upper(): str(k) for k in ch["klass"].unique()}
    f_by_class, f_chp = {}, {}
    for cname, spec in CENSUS.items():
        resolved = [have[k] for k in spec["klass"] if k in have]
        assert len(resolved) == len(spec["klass"]), (
            f"klass resolution FAIL {year}/{cname}: {spec['klass']} vs {sorted(have)}")
        f_by_class[cname] = np.nan_to_num(
            _s(ch[ch["klass"].isin(resolved)].groupby("hour")["mw"].sum()))
        chp = [have[k] for k in CHP_KLASS[cname] if k in have]
        f_chp[cname] = np.nan_to_num(
            _s(ch[ch["klass"].isin(chp)].groupby("hour")["mw"].sum())
        ) if chp else np.zeros(8760)

    rf = _sidecar("reserve_family", year)
    held_fast = np.nan_to_num(
        _s(rf[rf["family"].isin(FAST_FAMILY_NAMES)].groupby("hour")["held_mw"].sum()))

    missed = (actual > TAIL_BAR) & ~(maxz > TAIL_BAR)
    hit = (actual > TAIL_BAR) & (maxz > TAIL_BAR)
    return {"maxz": maxz, "model_dw": model_dw, "mdl_dem": mdl_dem,
            "actual": actual, "F": f_by_class, "F_chp": f_chp,
            "held_fast": held_fast, "missed": missed, "hit": hit,
            "ordinary": actual < ORDINARY_BAR}


# --------------------------------------------------------------------------
# Measured side — delivery-2023 corpus scan (precommit §2b)
# --------------------------------------------------------------------------

def scan_corpus_2023() -> dict:
    """One pass over the ERCOT-157 shards: hourly per-class state series,
    per-train HSL lists (cap_ref), per-train hourly state occupancy."""
    from derive_ercot_sced_offer_wall import _delivery_year_rows, _sced_source_files
    import ercot163_cc_commitment_state_census as e163

    files = _sced_source_files(2023)
    assert files, "no delivery-2023 SCED corpus shards"

    restype_of_class = {t: c for c, s in CENSUS.items() for t in s["restypes"]}
    online_hsl = {c: np.zeros(8760) for c in CENSUS}     # Σ HSL, online-ish rows
    startable_hsl = {c: np.zeros(8760) for c in CENSUS}  # Σ HSL, OFFQS/OFFNS rows
    total_online_hsl = np.zeros(8760)                    # ALL restypes (V-0 d)
    n_iv = np.zeros(8760, dtype=np.int64)                # distinct SCED stamps
    hsl_lists: dict[str, list[np.ndarray]] = {}          # train -> HSL rows (slow)
    train_class: dict[str, str] = {}
    occ: dict[str, dict[str, np.ndarray]] = {}           # train -> bucket counts
    t0 = time.time()
    for i, path in enumerate(files):
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, 2023)
        if df.empty:
            continue
        df = df.copy()
        df["hoy"] = e163._hoy(df["SCED Time Stamp"])
        df = df[(df["hoy"] >= 0) & (df["hoy"] < 8760)]
        df["HSL"] = pd.to_numeric(df["HSL"], errors="coerce")
        df["state"] = e163._state_of(df["Telemetered Resource Status"])
        hoy = df["hoy"].to_numpy(int)
        # distinct intervals per hoy (a delivery day lives in one shard)
        ts_h = df.groupby("SCED Time Stamp", observed=True)["hoy"].first()
        np.add.at(n_iv, ts_h.to_numpy(int), 1)
        # all-restype online HSL (V-0 d reconciliation)
        m_on = np.isin(df["state"].to_numpy(object), ONLINE_STATES)
        np.add.at(total_online_hsl, hoy[m_on], _nan0(df["HSL"])[m_on])
        # slow-universe rows
        sl = df[df["Resource Type"].isin(SLOW_RESTYPES)]
        if sl.empty:
            continue
        cls = sl["Resource Type"].map(restype_of_class).to_numpy(object)
        st = sl["state"].to_numpy(object)
        h = sl["hoy"].to_numpy(int)
        hslv = _nan0(sl["HSL"])
        for c in CENSUS:
            mc = cls == c
            m1 = mc & np.isin(st, ONLINE_STATES)
            np.add.at(online_hsl[c], h[m1], hslv[m1])
            m2 = mc & np.isin(st, STARTABLE_STATES)
            np.add.at(startable_hsl[c], h[m2], hslv[m2])
        # per-train accumulators (cap_ref + occupancy)
        sl = sl.assign(train=sl["Resource Name"].map(e163._train))
        for name, d in sl.groupby("train", observed=True):
            nm = str(name)
            hsl_lists.setdefault(nm, []).append(d["HSL"].to_numpy(float))
            train_class[nm] = restype_of_class[str(d["Resource Type"].iloc[0])]
            b = occ.setdefault(nm, {})
            dst = d["state"].to_numpy(object)
            dh = d["hoy"].to_numpy(int)
            for bucket, states in (("avail", None), ("cold", COLD_STATES)):
                if states is None:  # not OUT (ABSENT is implicit-never-seen)
                    m = ~np.isin(dst, NOT_AVAIL_STATES)
                else:
                    m = np.isin(dst, states)
                if m.any():
                    arr = b.setdefault(bucket, np.zeros(8760, dtype=np.int32))
                    np.add.at(arr, dh[m], 1)
        if (i + 1) % 30 == 0:
            print(f"  corpus scan {i+1}/{len(files)} shards "
                  f"({time.time()-t0:.0f}s)", flush=True)

    # cap_ref: e163 construction, widened universe (exact p98, all rows)
    cap_ref = {n: float(np.nanpercentile(np.concatenate(v), 98))
               for n, v in hsl_lists.items()
               if np.isfinite(np.concatenate(v)).any()}
    niv = np.maximum(n_iv, 1).astype(float)
    covered = n_iv > 0
    out = {"n_iv": n_iv, "covered": covered,
           "total_online_hsl": total_online_hsl / niv,
           "cap_ref": cap_ref, "train_class": train_class}
    for c in CENSUS:
        onl = online_hsl[c] / niv
        stb = startable_hsl[c] / niv
        avail = np.zeros(8760)
        cold = np.zeros(8760)
        for nm, b in occ.items():
            if train_class.get(nm) != c or nm not in cap_ref:
                continue
            if "avail" in b:
                avail += cap_ref[nm] * np.minimum(b["avail"] / niv, 1.0)
            if "cold" in b:
                cold += cap_ref[nm] * np.minimum(b["cold"] / niv, 1.0)
        out[c] = {"online_hsl": onl, "startable_hsl": stb,
                  "cap_meas": onl + stb, "avail_ref": avail, "cold_ref": cold}
    return out


# --------------------------------------------------------------------------
# Measured side — the 2025 tail-day extract (precommit §1/§2b)
# --------------------------------------------------------------------------

def scan_extract_2025() -> dict:
    import ercot163_cc_commitment_state_census as e163

    cols = _READ_COLS + ["Base Point"]
    raw = pd.read_parquet(EXTRACT_2025)
    have = [c for c in cols if c in raw.columns]
    df = raw[have].copy()
    del raw
    restype_of_class = {t: c for c, s in CENSUS.items() for t in s["restypes"]}
    ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    df["day"] = ts.dt.strftime("%Y-%m-%d")
    days, excluded = [], []
    for day, d in df.groupby("day"):
        ok = all(c in d.columns and d[c].notna().mean() >= 0.9
                 for c in ("Telemetered Resource Status", "HSL"))
        (days if ok else excluded).append(day)
    df = df[df["day"].isin(days)].copy()
    df["hoy"] = e163._hoy(df["SCED Time Stamp"])
    df = df[(df["hoy"] >= 0) & (df["hoy"] < 8760)]
    df["HSL"] = pd.to_numeric(df["HSL"], errors="coerce")
    df["bp"] = pd.to_numeric(df.get("Base Point"), errors="coerce")
    df["state"] = e163._state_of(df["Telemetered Resource Status"])

    n_iv = np.zeros(8760, dtype=np.int64)
    ts_h = df.groupby("SCED Time Stamp", observed=True)["hoy"].first()
    np.add.at(n_iv, ts_h.to_numpy(int), 1)
    niv = np.maximum(n_iv, 1).astype(float)
    covered = n_iv > 0

    out = {"days": sorted(days), "excluded_days": sorted(excluded),
           "covered": covered, "n_iv": n_iv}
    sl = df[df["Resource Type"].isin(SLOW_RESTYPES)]
    cls = sl["Resource Type"].map(restype_of_class).to_numpy(object)
    st = sl["state"].to_numpy(object)
    h = sl["hoy"].to_numpy(int)
    hslv = _nan0(sl["HSL"])
    bpv = _nan0(sl["bp"])
    for c in CENSUS:
        mc = cls == c
        onl = np.zeros(8760)
        stb = np.zeros(8760)
        bps = np.zeros(8760)
        m1 = mc & np.isin(st, ONLINE_STATES)
        np.add.at(onl, h[m1], hslv[m1])
        np.add.at(bps, h[m1], bpv[m1])
        m2 = mc & np.isin(st, STARTABLE_STATES)
        np.add.at(stb, h[m2], hslv[m2])
        out[c] = {"online_hsl": onl / niv, "startable_hsl": stb / niv,
                  "cap_meas": (onl + stb) / niv, "basepoint": bps / niv}
    return out


# --------------------------------------------------------------------------
# Model available capability (no-LP reconstruction, precommit §2c)
# --------------------------------------------------------------------------

def avail_model(year: int) -> dict[str, np.ndarray]:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=True)
    fa, fleet = state["fleet_arrays"], state["fleet"]
    grp = np.array([str(getattr(g, "plant_group", "") or "").upper() for g in fleet])
    # Implementation note (precommit §7 amendment convention, recorded in the
    # FINDING): the fleet carries nuclear units with an EMPTY plant_group —
    # their fleet-grain selector is fuel_type == "nuclear". The construction
    # (the model's nuclear units' pmax x availability) is unchanged.
    fuel = np.array([str(getattr(g, "fuel_type", "") or "").upper() for g in fleet])
    grp = np.where((grp == "") & (fuel == "NUCLEAR"), "NUCLEAR", grp)
    pmax = np.asarray(fa.pmax, dtype=float)
    av = np.asarray(fa.availability, dtype=float)
    if av.ndim == 1:
        av = av[:, None] * np.ones((1, 8760))
    out = {}
    for c, spec in CENSUS.items():
        idx = np.flatnonzero(np.isin(grp, [g.upper() for g in spec["groups"]]))
        assert idx.size, f"no fleet units for census class {c} ({spec['groups']})"
        out[c] = (pmax[idx, None] * av[idx, :8760]).sum(axis=0)
    return out


# --------------------------------------------------------------------------
# Census + kills
# --------------------------------------------------------------------------

def bind_census(F: dict, CAP: dict, valid: np.ndarray, my: dict) -> dict:
    """Per-class + union bind census on one grain (precommit §5)."""
    missed, hit, ordinary = my["missed"], my["hit"], my["ordinary"]
    away_base = my["model_dw"] >= my["actual"]
    per, b_union = {}, np.zeros(8760, dtype=bool)
    for c in CENSUS:
        cap = CAP[c]
        ok = valid & np.isfinite(cap)
        b = ok & (F[c] > cap)
        d = F[c] - cap
        per[c] = {
            "binds": int(b.sum()),
            "binds_missed": int((b & missed).sum()),
            "binds_hit": int((b & hit).sum()),
            "binds_ordinary": int((b & ordinary).sum()),
            "depth_missed_p50_mw": round(_q(d[b & missed], 0.5), 1),
            "depth_ordinary_p50_mw": round(_q(d[b & ordinary], 0.5), 1),
            "depth_ordinary_p90_mw": round(_q(d[b & ordinary], 0.9), 1),
            "cap_le0_hours": int((ok & (cap <= 0)).sum()),
            "mass_frac_bind": round(float(b.sum() / max(ok.sum(), 1)), 4),
        }
        b_union |= b
    m_cov = missed & valid
    rec = []
    for t in np.flatnonzero(b_union & (missed | hit)):
        rec.append({
            "hour": int(t), "set": "missed" if missed[t] else "hit",
            "actual": round(float(my["actual"][t]), 2),
            "model_maxz": round(float(my["maxz"][t]), 2),
            "classes": {c: {"F": round(float(F[c][t]), 1),
                            "cap": round(float(CAP[c][t]), 1)}
                        for c in CENSUS if np.isfinite(CAP[c][t])
                        and F[c][t] > CAP[c][t]},
        })
    return {
        "per_class": per,
        "union": {
            "binds": int(b_union.sum()),
            "binds_missed": int((b_union & missed).sum()),
            "binds_hit": int((b_union & hit).sum()),
            "binds_ordinary": int((b_union & ordinary).sum()),
            "away_binds": int((b_union & away_base).sum()),
            "reach_frac_missed": round(
                float((b_union & missed).sum() / m_cov.sum()), 4)
            if m_cov.sum() else None,
            "missed_covered": int(m_cov.sum()),
            "valid_hours": int(valid.sum()),
        },
        "bind_hours_missed_hit": rec,
        "_b_union": b_union,
    }


def main() -> None:
    out: dict = {
        "probe": "ercot245_commitment_state_phase0",
        "precommit": "docs/PRECOMMIT-ercot245-commitment-state-phase0-2026-08-30.md",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "scored_years": list(SCORED_YEARS),
    }
    # ---- model side + V-0(a/b) ------------------------------------------
    my = {y: model_year(y) for y in (REPORT_YEAR, *SCORED_YEARS)}
    v0: dict = {}
    for y in (REPORT_YEAR, *SCORED_YEARS):
        m = my[y]
        mt, at = int((m["maxz"] > TAIL_BAR).sum()), int((m["actual"] > TAIL_BAR).sum())
        nm = int(m["missed"].sum())
        v0[str(y)] = {"model_tail": mt, "actual_tail": at, "missed": nm}
        if y in SCORED_YEARS:
            assert mt == V0_MODEL_TAIL[y], f"V-0(a) FAIL {y}: model tail {mt}"
            assert at == V0_ACTUAL_TAIL[y], f"V-0(a) FAIL {y}: actual tail {at}"
        assert nm == V0_MISSED[y], f"V-0(a) FAIL {y}: |M|={nm} != {V0_MISSED[y]}"
    # ---- V-0(b/c): EIA alignment + rtolhsl evening means ----------------
    eia = {y: _eia_year(y) for y in (REPORT_YEAR, *SCORED_YEARS)}
    rtolhsl = {}
    for y in (REPORT_YEAR, *SCORED_YEARS):
        act_d = eia[y]["Demand"].to_numpy(float)
        lags = {}
        for lag in (-1, 0, 1):
            x, y_ = my[y]["mdl_dem"][3:-3], act_d[3 + lag: 8757 + lag]
            ok = np.isfinite(x) & np.isfinite(y_)
            lags[lag] = float(np.corrcoef(x[ok], y_[ok])[0, 1])
        assert max(lags, key=lags.get) == 0, f"V-0(b) alignment FAIL {y}: {lags}"
        mo = pd.read_parquet(str(MEASURED_ORDC).format(year=y)).sort_values("hour")
        r = mo["rtolhsl"].to_numpy(float)[:8760]
        rtolhsl[y] = r
        hod = np.arange(8760) % 24
        eve = np.isfinite(r) & (hod >= 17) & (hod <= 21)
        gw = float(np.nanmean(r[eve]) / 1e3)
        assert abs(gw - V0_RTOLHSL_EVENING_GW[y]) <= 3.0, (
            f"V-0(c) FAIL {y}: rtolhsl evening {gw:.2f} GW")
        v0[str(y)]["rtolhsl_evening_gw"] = round(gw, 2)
        v0[str(y)]["demand_lag_corr"] = {str(k): round(v, 4) for k, v in lags.items()}
    print("V-0(a/b/c) anchors PASS", flush=True)

    # ---- corpus scan (2023) + V-0(d/e) ----------------------------------
    print("scanning delivery-2023 corpus ...", flush=True)
    corp = scan_corpus_2023()
    cov23 = corp["covered"]
    tot = corp["total_online_hsl"]
    fin = cov23 & np.isfinite(rtolhsl[2023])
    corr_d = float(np.corrcoef(tot[fin], rtolhsl[2023][fin])[0, 1])
    gap_med = float(np.median(tot[fin] - rtolhsl[2023][fin]))
    v0["corpus_recon"] = {"corr": round(corr_d, 4),
                          "median_gap_mw": round(gap_med, 1),
                          "covered_hours": int(cov23.sum())}
    assert corr_d >= 0.985, f"V-0(d) FAIL: corpus-vs-rtolhsl corr {corr_d:.4f}"
    assert abs(gap_med) <= 3000.0, f"V-0(d) FAIL: median gap {gap_med:.0f} MW"
    cr_tot = {c: sum(v for n, v in corp["cap_ref"].items()
                     if corp["train_class"].get(n) == c) for c in CENSUS}
    v0["cap_ref_totals_gw"] = {c: round(v / 1e3, 3) for c, v in cr_tot.items()}
    cc_dev = abs(cr_tot["CC"] / 1e3 - V0_E163_CC_CAPREF_GW) / V0_E163_CC_CAPREF_GW
    assert cc_dev <= 0.02, (
        f"V-0(e) FAIL: CC cap_ref {cr_tot['CC']/1e3:.3f} GW vs committed "
        f"{V0_E163_CC_CAPREF_GW} (dev {cc_dev:.3%})")
    print(f"V-0(d/e) PASS: recon corr {corr_d:.4f}, CC cap_ref "
          f"{cr_tot['CC']/1e3:.2f} GW", flush=True)

    # ---- extract scan (2025) + V-0(f) -----------------------------------
    ext = scan_extract_2025()
    m25_cov = my[2025]["missed"] & ext["covered"]
    v0["extract"] = {"days": ext["days"], "excluded_days": ext["excluded_days"],
                     "n_days": len(ext["days"]),
                     "covered_hours": int(ext["covered"].sum()),
                     "missed_2025_covered": int(m25_cov.sum())}
    t3_gradeable = int(m25_cov.sum()) >= T3_COVERAGE_FLOOR
    print(f"V-0(f): extract {len(ext['days'])} days, M_2025 covered "
          f"{int(m25_cov.sum())}/31 (T-3 gradeable: {t3_gradeable})", flush=True)

    # ---- model available capability (no LP; sequential) -----------------
    am = {}
    for y in (REPORT_YEAR, *SCORED_YEARS):
        print(f"reconstructing fleet {y} (no LP) ...", flush=True)
        am[y] = avail_model(y)
    universe = {}
    for c in CENSUS:
        r = float(np.mean(corp[c]["avail_ref"][cov23]) /
                  max(np.mean(am[REPORT_YEAR][c][cov23]), 1.0))
        universe[c] = {
            "avail_ref_2023_gw": round(float(np.mean(corp[c]["avail_ref"][cov23]) / 1e3), 3),
            "avail_model_2023_gw": round(float(np.mean(am[REPORT_YEAR][c][cov23]) / 1e3), 3),
            "ratio": round(r, 3),
            "inside_band": bool(UNIVERSE_BAND[0] <= r <= UNIVERSE_BAND[1]),
        }
    out["universe_anchors"] = universe
    print("universe anchors:", json.dumps(universe), flush=True)

    # ---- transfer structure (precommit §2d) -----------------------------
    def _nl(y: int) -> np.ndarray:
        e = eia[y]
        return (_nan0(e["Demand"]) - _nan0(e["NG: WND"]) - _nan0(e["NG: SUN"]))

    nl23 = _nl(2023)
    edges = np.quantile(nl23, np.linspace(0, 1, N_BINS + 1))
    edges[0], edges[-1] = -np.inf, np.inf

    def _bin(nl: np.ndarray) -> np.ndarray:
        return np.clip(np.searchsorted(edges, nl, side="right") - 1, 0, N_BINS - 1)

    b23 = _bin(nl23)
    c_k = {}
    for c in CENSUS:
        num = np.zeros(N_BINS)
        den = np.zeros(N_BINS)
        np.add.at(num, b23[cov23], corp[c]["cap_meas"][cov23])
        np.add.at(den, b23[cov23], corp[c]["avail_ref"][cov23])
        c_k[c] = num / np.maximum(den, 1.0)
    out["transfer_structure"] = {
        "nl_bin_edges_mw": [round(float(x), 1) for x in
                            np.quantile(nl23, np.linspace(0, 1, N_BINS + 1))],
        "c_k": {c: [round(float(x), 4) for x in c_k[c]] for c in CENSUS},
    }
    cap_hat = {y: {c: c_k[c][_bin(_nl(y))] * am[y][c] for c in CENSUS}
               for y in SCORED_YEARS}

    # ---- transfer validation (T-1 / T-2 / T-3) --------------------------
    t1 = {}
    for c in CENSUS:  # T-1 is the extract grain
        m = ext["covered"] & (ext[c]["cap_meas"] > 0)
        rel = np.abs(cap_hat[2025][c][m] - ext[c]["cap_meas"][m]) / ext[c]["cap_meas"][m]
        t1[c] = {"median_rel_err": round(float(np.median(rel)), 4),
                 "n_hours": int(m.sum()),
                 "pass": bool(np.median(rel) <= T1_MEDREL_BAND)}
    t1_pass = all(v["pass"] for v in t1.values())

    t2 = {}
    for y in SCORED_YEARS:
        e = eia[y]
        fuel_cols = [c for c in e.columns if c.startswith("NG: ") and c not in EIA_KEEP]
        nonthermal = np.zeros(8760)
        for c in fuel_cols:
            nonthermal += _nan0(e[c])
        cap_agg = rtolhsl[y] - nonthermal
        finy = np.isfinite(cap_agg)
        shat = np.sum([cap_hat[y][c] for c in CENSUS], axis=0)
        over = finy & (shat > cap_agg)
        ovr_mag = (shat - cap_agg)[over]
        t2[str(y)] = {
            "frac_over": round(float(over.sum() / finy.sum()), 4),
            "p95_overshoot_mw": round(_q(ovr_mag, 0.95), 1) if over.any() else 0.0,
            "corr_reported": round(float(np.corrcoef(shat[finy], cap_agg[finy])[0, 1]), 4),
            "pass": bool(over.sum() / finy.sum() <= T2_FRAC_BAR
                         and (not over.any() or _q(ovr_mag, 0.95) <= T2_P95_OVERSHOOT_MW)),
        }
    t2_pass = all(t2[str(y)]["pass"] for y in SCORED_YEARS)

    # direct + transferred censuses ---------------------------------------
    census: dict = {}
    census["direct_2023_DV3"] = bind_census(
        my[2023]["F"], {c: corp[c]["cap_meas"] for c in CENSUS}, cov23, my[2023])
    census["direct_2025_extract"] = bind_census(
        my[2025]["F"], {c: ext[c]["cap_meas"] for c in CENSUS},
        ext["covered"], my[2025])
    for y in SCORED_YEARS:
        census[f"transferred_{y}"] = bind_census(
            my[y]["F"], cap_hat[y], np.ones(8760, dtype=bool), my[y])

    t3: dict = {"gradeable": t3_gradeable}
    if t3_gradeable:
        bd = census["direct_2025_extract"]["_b_union"]
        bt = census[f"transferred_2025"]["_b_union"]
        agree = float((bd[m25_cov] == bt[m25_cov]).mean())
        t3.update({"agreement": round(agree, 4),
                   "pass": bool(agree >= T3_AGREE_FLOOR)})
    t3_pass = bool(t3.get("pass", True))  # N/A-coverage-limited never kills
    out["transfer_validation"] = {"T1": t1, "T2": t2, "T3": t3}

    # ---- diagnostics ----------------------------------------------------
    diags: dict = {}
    for y in SCORED_YEARS:  # D-V1: held-attribution variant (report-only)
        slow_tot = np.maximum(np.sum([my[y]["F"][c] for c in CENSUS], axis=0), 1.0)
        Fh = {c: my[y]["F"][c] + my[y]["held_fast"] * my[y]["F"][c] / slow_tot
              for c in CENSUS}
        cen = bind_census(Fh, cap_hat[y], np.ones(8760, dtype=bool), my[y])
        diags[f"DV1_held_attributed_{y}"] = {
            "union": {k: v for k, v in cen["union"].items()}}
    for y in SCORED_YEARS:  # D-V2: class-whole (CHP added) variant
        Fw = {c: my[y]["F"][c] + my[y]["F_chp"][c] for c in CENSUS}
        cen = bind_census(Fw, cap_hat[y], np.ones(8760, dtype=bool), my[y])
        diags[f"DV2_class_whole_{y}"] = {
            "union": {k: v for k, v in cen["union"].items()}}
    # D-V4: per-class headroom decomposition at covered M_2025 hours
    hrs = np.flatnonzero(m25_cov)
    dv4 = []
    for t in hrs:
        row = {"hour": int(t), "actual": round(float(my[2025]["actual"][t]), 2),
               "model_maxz": round(float(my[2025]["maxz"][t]), 2), "classes": {}}
        for c in CENSUS:
            row["classes"][c] = {
                "F": round(float(my[2025]["F"][c][t]), 1),
                "avail_model": round(float(am[2025][c][t]), 1),
                "spare_model": round(float(am[2025][c][t] - my[2025]["F"][c][t]), 1),
                "online_meas": round(float(ext[c]["online_hsl"][t]), 1),
                "bp_meas": round(float(ext[c]["basepoint"][t]), 1),
                "spare_meas": round(float(ext[c]["cap_meas"][t]
                                          - ext[c]["basepoint"][t]), 1),
                "cap_meas": round(float(ext[c]["cap_meas"][t]), 1),
            }
        dv4.append(row)
    diags["DV4_headroom_at_M2025"] = dv4
    # D-V5: reality-side per-class online share, events vs same-bin ordinary
    b25 = _bin(_nl(2025))
    dv5 = {}
    ord_ext = my[2025]["ordinary"] & ext["covered"]
    for c in CENSUS:
        cr23 = max(cr_tot[c], 1.0)
        ev_share = float(np.mean(ext[c]["cap_meas"][m25_cov]) / cr23) if m25_cov.any() else None
        bins_ev = set(b25[m25_cov].tolist())
        m_ord = ord_ext & np.isin(b25, list(bins_ev))
        od_share = float(np.mean(ext[c]["cap_meas"][m_ord]) / cr23) if m_ord.any() else None
        dv5[c] = {"event_share_of_capref":
                  round(ev_share, 4) if ev_share is not None else None,
                  "samebin_ordinary_share":
                  round(od_share, 4) if od_share is not None else None,
                  "n_ordinary_samebin_hours": int(m_ord.sum())}
    diags["DV5_reality_shares"] = dv5
    out["diagnostics"] = diags

    # ---- kills (precommit §6) -------------------------------------------
    ka_flags = {}
    for c in CENSUS:
        d23 = census["direct_2023_DV3"]["per_class"][c]
        ka_flags[c] = {
            "cap_le0_gt24": d23["cap_le0_hours"] > KA_CAP_LE0_BAR,
            "mass_gt25pct": d23["mass_frac_bind"] > KA_MASS_FRAC,
        }
    ka = any(v["cap_le0_gt24"] or v["mass_gt25pct"] for v in ka_flags.values())
    per_kill = {}
    for y in SCORED_YEARS:
        u = census[f"transferred_{y}"]["union"]
        m = int(my[y]["missed"].sum())
        per_kill[str(y)] = {
            "K_B_reach_below_020": (u["binds_missed"] / m) < KB_REACH_FLOOR,
            "K_C_ordinary_gt150": u["binds_ordinary"] > KC_ORDINARY_BAR,
            "K_C_ordinary_gt_missed": u["binds_ordinary"] > u["binds_missed"],
            "K_C_away_gt_third": u["away_binds"] > u["binds"] / 3.0,
        }
    kb = all(per_kill[str(y)]["K_B_reach_below_020"] for y in SCORED_YEARS)
    kc = any(per_kill[str(y)]["K_C_ordinary_gt150"]
             or per_kill[str(y)]["K_C_ordinary_gt_missed"]
             or per_kill[str(y)]["K_C_away_gt_third"] for y in SCORED_YEARS)
    kt = not (t1_pass and t2_pass and t3_pass)
    out["verdict"] = {
        "K_A": {"fires": ka, "per_class": ka_flags},
        "K_B": {"fires": kb, "per_year": {y: per_kill[str(y)]["K_B_reach_below_020"]
                                          for y in map(str, SCORED_YEARS)}},
        "K_C": {"fires": kc, "per_year": per_kill},
        "K_T": {"fires": kt, "T1_pass": t1_pass, "T2_pass": t2_pass,
                "T3": t3},
        "any_kill_fires": ka or kb or kc or kt,
        "phase1_licensed": not (ka or kb or kc or kt),
    }
    out["v0"] = v0
    out["census"] = {k: {kk: vv for kk, vv in v.items() if kk != "_b_union"}
                     for k, v in census.items()}
    OUT_JSON.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["verdict"], indent=1, default=str))
    print(f"wrote {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
