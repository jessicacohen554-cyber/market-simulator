"""ercot-244 Phase-0: zero-solve census of the rtolhsl-based energy-side
online-capability ceiling against the FORWARD keeper's committed sidecars.

Executes exactly the constructions, V-0 anchors, priors and kills declared ex
ante in ``docs/PRECOMMIT-ercot244-online-cap-phase0-2026-08-30.md`` (pushed and
blob-verified before this ran). ZERO-SOLVE: reads the committed
``results/calibration/ercot234_eastex_identity`` sidecars, the committed
actuals, the EIA-930 wide extract and the measured ORDC/reserves series.
No lever, no config change, no matrix verdict move.

Run:
    python scripts/probes/ercot244_online_cap_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "ercot234_eastex_identity"
ACTUALS = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
EIA_WIDE = REPO / "data" / "raw" / "eia-930-hourly" / "ERCO hourly.parquet"
MEASURED_ORDC = REPO / "data" / "raw" / "ercot" / "ercot_{year}_ordc_reserves_hourly.parquet"
OUT_JSON = REPO / "results" / "calibration" / "ercot244_online_cap_phase0.json"

SCORED_YEARS = (2024, 2025)
REPORT_YEARS = (2023,)

# Precommit §1: registered official anchors (V-0 a/b).
V0_MODEL_TAIL = {2024: 22, 2025: 1}
V0_ACTUAL_TAIL = {2024: 53, 2025: 31}
# Precommit §5 V-0(d): the card's rtolhsl evening means (GW), soft ±3 GW.
V0_RTOLHSL_EVENING_GW = {2023: 58.87, 2024: 62.64, 2025: 67.81}

# Precommit §2: the model-side fast-tier point (the ercot-159 census formula).
SLOW_CLASSES = {
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "ST_CHP",
    "COAL_PRB",
    "COAL_LIGNITE",
    "NUCLEAR",
}
# The three fast products. A product year straddling its rigid-release gate is
# split into time-DISJOINT `X_withheld` / `X_released` window families
# (model/reserves/spec.py ~1620); an un-straddled year carries `X` or
# `X_withheld` alone. The product's full-year held series is therefore the sum
# over every family variant — implementation repair recorded in the FINDING,
# construction ("held over the three fast products") unchanged.
FAST_PRODUCTS = ("RegUp", "RRS", "ECRS")
FAST_FAMILY_NAMES = tuple(
    n for p in FAST_PRODUCTS for n in (p, f"{p}_withheld", f"{p}_released")
)
# Precommit §2: EIA-930 categories NOT subtracted from rtolhsl.
EIA_KEEP = {"NG: NG", "NG: COL", "NG: NUC"}

ORDINARY_BAR = 150.0  # actual < $150 = ordinary (ercot-159 convention)
TAIL_BAR = 200.0  # official C3c line (strictly greater)


def _sidecar(name: str, year: int) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"{name}_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df[df["year"] == year] if "year" in df.columns else df


def _eia_year(year: int) -> pd.DataFrame:
    """EIA-930 wide extract mapped to the local 8760 — the ercot-243
    convention, reused verbatim (precommit §2)."""
    df = pd.read_parquet(EIA_WIDE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    local = utc.dt.tz_convert("America/Chicago").dt.tz_localize(None)
    hour_ending = local - pd.Timedelta(hours=1)
    keep = (hour_ending.dt.year == year) & ~(
        (hour_ending.dt.month == 2) & (hour_ending.dt.day == 29)
    )
    out = df[keep].assign(_utc=utc[keep]).sort_values("_utc").reset_index(drop=True)
    assert len(out) == 8760, f"EIA-930 local-{year} rows = {len(out)} != 8760"
    return out


def _q(arr: np.ndarray, p: float) -> float:
    return float(np.quantile(arr, p)) if arr.size else float("nan")


def _year_census(year: int) -> dict:
    rng = range(8760)
    sys_df = _sidecar("system", year)
    g = sys_df.groupby("hour")

    def _s(series: pd.Series) -> np.ndarray:
        return series.reindex(rng).to_numpy(float)

    # Official C3c model basis: MAX ZONAL price, NaN -> -inf (scorer rule).
    maxz = np.nan_to_num(_s(g["price"].max()), nan=-np.inf)
    num = (sys_df["price"] * sys_df["demand"]).groupby(sys_df["hour"]).sum()
    den = g["demand"].sum()
    model_dw = np.nan_to_num(_s(num / den))
    mdl_dem = np.nan_to_num(_s(g["demand"].sum()))

    a_df = pd.read_parquet(ACTUALS)
    actual = a_df[a_df["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]
    assert actual.size == 8760, f"actuals {year}: {actual.size} rows"

    # ---- V-0 anchors -------------------------------------------------------
    model_tail_n = int((maxz > TAIL_BAR).sum())
    actual_tail_n = int((actual > TAIL_BAR).sum())
    v0 = {"model_tail_gt200": model_tail_n, "actual_tail_gt200": actual_tail_n}
    if year in SCORED_YEARS:
        assert model_tail_n == V0_MODEL_TAIL[year], (
            f"V-0(a) FAIL {year}: model tail {model_tail_n} != {V0_MODEL_TAIL[year]}"
        )
        assert actual_tail_n == V0_ACTUAL_TAIL[year], (
            f"V-0(b) FAIL {year}: actual tail {actual_tail_n} != {V0_ACTUAL_TAIL[year]}"
        )

    eia = _eia_year(year)
    act_d = eia["Demand"].to_numpy(float)
    lags = {}
    for lag in (-1, 0, 1):
        x, y_ = mdl_dem[3:-3], act_d[3 + lag : 8757 + lag]
        ok = np.isfinite(x) & np.isfinite(y_)
        lags[lag] = float(np.corrcoef(x[ok], y_[ok])[0, 1])
    assert max(lags, key=lags.get) == 0, f"V-0(c) alignment FAIL {year}: {lags}"
    v0["demand_lag_corr"] = {str(k): v for k, v in lags.items()}

    mo = pd.read_parquet(str(MEASURED_ORDC).format(year=year)).sort_values("hour")
    rtolhsl = mo["rtolhsl"].to_numpy(float)[:8760]
    rtolcap = mo["rtolcap"].to_numpy(float)[:8760]
    hod = np.arange(8760) % 24
    eve = np.isfinite(rtolhsl) & (hod >= 17) & (hod <= 21)
    eve_gw = float(np.nanmean(rtolhsl[eve]) / 1000.0)
    v0["rtolhsl_evening_mean_gw"] = eve_gw
    assert abs(eve_gw - V0_RTOLHSL_EVENING_GW[year]) <= 3.0, (
        f"V-0(d) FAIL {year}: rtolhsl hod17-21 mean {eve_gw:.2f} GW vs card "
        f"{V0_RTOLHSL_EVENING_GW[year]} (±3)"
    )

    # ---- The ceiling (precommit §2) ---------------------------------------
    fuel_cols = [c for c in eia.columns if c.startswith("NG: ") and c not in EIA_KEEP]
    nonthermal = np.zeros(8760)
    for c in fuel_cols:
        nonthermal = nonthermal + np.nan_to_num(eia[c].to_numpy(float))
    cap = rtolhsl - nonthermal  # NaN rtolhsl -> NaN cap (excluded below)

    # ---- The model-side fast-tier point (precommit §2) --------------------
    ch = _sidecar("class_hourly", year)
    have = {str(k).upper(): str(k) for k in ch["klass"].unique()}
    resolved = [have[k] for k in sorted(SLOW_CLASSES) if k in have]
    assert len(resolved) == 7, (
        f"slow-class resolution FAIL {year}: resolved {resolved} from {sorted(have)}"
    )
    p_slow = np.nan_to_num(
        _s(ch[ch["klass"].isin(resolved)].groupby("hour")["mw"].sum())
    )
    rf = _sidecar("reserve_family", year)
    fams = set(map(str, rf["family"].unique()))
    for p in FAST_PRODUCTS:
        assert any(f in fams for f in (p, f"{p}_withheld", f"{p}_released")), (
            f"family resolution FAIL {year}: no {p} family in {sorted(fams)}"
        )
    held_fast = np.nan_to_num(
        _s(rf[rf["family"].isin(FAST_FAMILY_NAMES)].groupby("hour")["held_mw"].sum())
    )
    f_point = p_slow + held_fast

    # ---- Census (precommit §5) --------------------------------------------
    finite = np.isfinite(cap)
    n_nan = int((~finite).sum())
    binds = finite & (f_point > cap)
    depth = f_point - cap

    missed = (actual > TAIL_BAR) & ~(maxz > TAIL_BAR)
    hit = (actual > TAIL_BAR) & (maxz > TAIL_BAR)
    ordinary = actual < ORDINARY_BAR
    buffer = (actual >= ORDINARY_BAR) & (actual <= TAIL_BAR)
    away = binds & (model_dw >= actual)

    n_b = int(binds.sum())
    n_bm = int((binds & missed).sum())
    n_bh = int((binds & hit).sum())
    n_bord = int((binds & ordinary).sum())
    n_bbuf = int((binds & buffer).sum())
    n_away = int(away.sum())

    hours_rec = []
    for t in np.flatnonzero(binds & (missed | hit)):
        hours_rec.append(
            {
                "hour": int(t),
                "set": "missed" if missed[t] else "hit",
                "actual": round(float(actual[t]), 2),
                "model_maxz": round(float(maxz[t]), 2),
                "model_dw": round(float(model_dw[t]), 2),
                "F_mw": round(float(f_point[t]), 1),
                "cap_mw": round(float(cap[t]), 1),
                "depth_mw": round(float(depth[t]), 1),
            }
        )

    # ---- Disclosed diagnostics (report-only) ------------------------------
    dv1 = None
    try:
        import sys

        sys.path.insert(0, str(REPO))
        sys.path.insert(0, str(REPO / "src"))
        from market_sim.results.scarcity import (
            ercot_load_resource_reserve_mw,
            ercot_storage_as_reserve_mw,
        )

        lr = np.asarray(ercot_load_resource_reserve_mw(year, 8760), dtype=float)
        sto = np.asarray(ercot_storage_as_reserve_mw(year, 8760), dtype=float)
        cap1 = cap + lr + sto
        b1 = finite & (f_point > cap1)
        dv1 = {
            "binds": int(b1.sum()),
            "binds_missed": int((b1 & missed).sum()),
            "binds_ordinary": int((b1 & ordinary).sum()),
            "lr_mean_mw": round(float(np.mean(lr)), 1),
            "sto_mean_mw": round(float(np.mean(sto)), 1),
        }
    except Exception as e:  # diagnostic only, never gating
        dv1 = {"unavailable": str(e)[:200]}

    dv2_cols = [c for c in fuel_cols if c not in ("NG: OTH", "NG: WAT")]
    nt2 = np.zeros(8760)
    for c in dv2_cols:
        nt2 = nt2 + np.nan_to_num(eia[c].to_numpy(float))
    cap2 = rtolhsl - nt2
    b2 = finite & (f_point > cap2)
    dv2 = {
        "binds": int(b2.sum()),
        "binds_missed": int((b2 & missed).sum()),
        "binds_ordinary": int((b2 & ordinary).sum()),
    }

    # D-V3: how far the armed (credit-netted) reserve cap is from owning the
    # same margin at the binding hours: slack = rtolcap_net - held_fast.
    dv3 = None
    if isinstance(dv1, dict) and "unavailable" not in dv1:
        rtolcap_net = rtolcap - (lr + sto)
        slack = (rtolcap_net - held_fast)[binds & np.isfinite(rtolcap)]
        dv3 = {
            "reserve_cap_slack_at_B_p10_mw": round(_q(slack, 0.10), 1),
            "reserve_cap_slack_at_B_p50_mw": round(_q(slack, 0.50), 1),
            "reserve_cap_slack_at_B_p90_mw": round(_q(slack, 0.90), 1),
        }

    return {
        "v0": v0,
        "eia_subtracted_columns": fuel_cols,
        "slow_classes_resolved": resolved,
        "populations": {
            "missed": int(missed.sum()),
            "hit": int(hit.sum()),
            "ordinary": int(ordinary.sum()),
            "nan_cap_hours": n_nan,
        },
        "census": {
            "binds": n_b,
            "binds_missed": n_bm,
            "binds_hit": n_bh,
            "binds_ordinary": n_bord,
            "binds_buffer": n_bbuf,
            "away_binds": n_away,
            "reach_frac_missed": round(n_bm / missed.sum(), 4) if missed.sum() else None,
            "depth_missed_p50_mw": round(_q(depth[binds & missed], 0.50), 1),
            "depth_missed_p90_mw": round(_q(depth[binds & missed], 0.90), 1),
            "depth_ordinary_p50_mw": round(_q(depth[binds & ordinary], 0.50), 1),
            "depth_ordinary_p90_mw": round(_q(depth[binds & ordinary], 0.90), 1),
            "F_minus_cap_p50_all_mw": round(_q(depth[finite], 0.50), 1),
            "F_minus_cap_p99_all_mw": round(_q(depth[finite], 0.99), 1),
            "p_slow_gt_cap_hours": int((finite & (p_slow > cap)).sum()),
            "cap_le0_hours": int((finite & (cap <= 0)).sum()),
        },
        "levels_gw": {
            "cap_mean": round(float(np.nanmean(cap) / 1e3), 2),
            "cap_evening_mean": round(float(np.nanmean(cap[eve]) / 1e3), 2),
            "F_mean": round(float(np.mean(f_point) / 1e3), 2),
            "F_evening_mean": round(float(np.mean(f_point[eve]) / 1e3), 2),
            "p_slow_mean": round(float(np.mean(p_slow) / 1e3), 2),
            "held_fast_mean": round(float(np.mean(held_fast) / 1e3), 2),
        },
        "bind_hours_missed_hit": hours_rec,
        "diagnostics": {"D_V1_credit_augmented": dv1, "D_V2_no_othwat": dv2, "D_V3_reserve_nesting": dv3},
    }


def _grade(res: dict) -> dict:
    """Precommit §6 kills, graded on the scored years only."""
    kills = {}
    for y in SCORED_YEARS:
        c = res[str(y)]["census"]
        m = res[str(y)]["populations"]["missed"]
        nonnan = 8760 - res[str(y)]["populations"]["nan_cap_hours"]
        kills[str(y)] = {
            "K_A_cap_le0": c["cap_le0_hours"] > 24,
            "K_A_pslow_gt_cap": c["p_slow_gt_cap_hours"] > 0.08 * nonnan,
            "K_B_reach_below_020": (c["binds_missed"] / m if m else 0.0) < 0.20,
            "K_C_ordinary_gt150": c["binds_ordinary"] > 150,
            "K_C_ordinary_gt_missed": c["binds_ordinary"] > c["binds_missed"],
            "K_C_away_gt_third": c["away_binds"] > c["binds"] / 3.0,
        }
    ka = any(kills[str(y)]["K_A_cap_le0"] or kills[str(y)]["K_A_pslow_gt_cap"] for y in SCORED_YEARS)
    kb = all(kills[str(y)]["K_B_reach_below_020"] for y in SCORED_YEARS)
    kc = any(
        kills[str(y)]["K_C_ordinary_gt150"]
        or kills[str(y)]["K_C_ordinary_gt_missed"]
        or kills[str(y)]["K_C_away_gt_third"]
        for y in SCORED_YEARS
    )
    return {
        "per_year": kills,
        "K_A_fires": ka,
        "K_B_fires": kb,
        "K_C_fires": kc,
        "any_kill_fires": ka or kb or kc,
        "phase1_licensed": not (ka or kb or kc),
    }


def main() -> None:
    out: dict = {
        "probe": "ercot244_online_cap_phase0",
        "precommit": "docs/PRECOMMIT-ercot244-online-cap-phase0-2026-08-30.md",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "scored_years": list(SCORED_YEARS),
        "report_years": list(REPORT_YEARS),
    }
    for y in (*REPORT_YEARS, *SCORED_YEARS):
        out[str(y)] = _year_census(y)
        print(f"--- {y}: {json.dumps(out[str(y)]['census'])}")
    for y in SCORED_YEARS:
        pm = out[str(y)]["populations"]["missed"]
        assert 15 <= pm <= 80, f"population-prior breach {y}: |M|={pm} outside [15, 80]"
    out["verdict"] = _grade(out)
    OUT_JSON.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["verdict"], indent=1))
    print(f"wrote {OUT_JSON.relative_to(REPO)}")


if __name__ == "__main__":
    main()
