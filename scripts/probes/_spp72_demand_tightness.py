"""SPP-72 (card R-bf): is the model's own demand tight in the hours the market priced highest?

Zero-LP measurement, pre-registered in
``docs/handoffs/PRECOMMIT-spp-72-demand-tightness-2026-09-22.md`` (pushed before any number was
read). For each year: take the top-1 % hours by MEASURED RT price (the C3c benchmark), and
compare the percentile-within-own-year of the LP's dispatch demand (committed
``hourly/system_<year>.parquet``, summed over zones) with that of measured EIA-930 SWPP load
read from an INDEPENDENT file (``data/raw/SWPP_region.parquet``) aligned onto the model clock
here, not by the loader. Also runs the trap-(e) alignment checks (half-year lag scan, peak hour).

Usage: ``uv run python scripts/probes/_spp72_demand_tightness.py --out <json>``
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

RUNG = "spp71_ensemble_rung"  # keeper-15 rung, 2019-2022
SPAN = "spp71_ensemble_span"  # keeper 15, 2023-2025
YEARS = range(2019, 2026)
N_TOP = 88  # top 1 % of 8,760 (PRECOMMIT §3)
N_TOP10 = 876  # top 10 % robustness read (PRECOMMIT §3, descriptive)
CST_OFFSET_H = 6  # model clock = fixed CST (UTC-6), frames.py:278-337
# 2024 benchmark seam: price drops GMT Feb 29, demand drops CST Feb 29 (PRECOMMIT §4)
SEAM_2024 = set(range(1410, 1416))
# Physical ceiling guard, trap (f): SPP load never approaches 100 GW
LOAD_CEILING_MW = 100_000.0


def model_clock_index(year: int) -> pd.DatetimeIndex:
    """Hour-beginning UTC timestamps of the model's 8,760 slots (CST Feb 29 dropped)."""
    start = pd.Timestamp(f"{year}-01-01 {CST_OFFSET_H:02d}:00", tz="UTC")
    idx = pd.date_range(start, periods=8784 if year % 4 == 0 else 8760, freq="h")
    local = idx - pd.Timedelta(hours=CST_OFFSET_H)
    keep = ~((local.month == 2) & (local.day == 29))
    idx = idx[keep]
    assert len(idx) == 8760
    return idx


def measured_series(region: pd.DataFrame, typ: str, year: int) -> np.ndarray:
    """EIA-930 SWPP series on the model clock; ``period`` is hour-ENDING UTC."""
    s = region[region["type"] == typ].set_index("period")["value_mwh"]
    s.index = s.index - pd.Timedelta(hours=1)  # hour-ending -> hour-beginning
    s = s[~s.index.duplicated()]
    out = s.reindex(model_clock_index(year)).astype(float)
    if typ == "D":
        out[(out > LOAD_CEILING_MW) | (out <= 0)] = np.nan
    return out.interpolate(limit_direction="both").to_numpy()


def pct_rank(x: np.ndarray) -> np.ndarray:
    """Percentile rank 0-100 within the array (average ranks for ties)."""
    return pd.Series(x).rank(pct=True, method="average").to_numpy() * 100.0


def model_demand(year: int) -> np.ndarray:
    """LP dispatch demand, P1, summed over zones, from the committed sidecar."""
    bundle = RUNG if year <= 2022 else SPAN
    s = pd.read_parquet(
        REPO_ROOT / "results/calibration" / bundle / f"hourly/system_{year}.parquet"
    )
    s = s[s["pass"] == "P1"]
    return s.groupby("hour")["demand"].sum().sort_index().to_numpy()


def lag_scan(a: np.ndarray, b: np.ndarray, half: slice) -> int:
    """Lag (-3..+3 h) maximising corr(a[t], b[t+lag]) over one half-year."""
    best, arg = -2.0, None
    for lag in range(-3, 4):
        i = np.arange(8760)[half]
        j = i + lag
        ok = (j >= 0) & (j < 8760)
        r = np.corrcoef(a[i[ok]], b[j[ok]])[0, 1]
        if r > best:
            best, arg = r, lag
    return arg


def main() -> None:
    """Run the pre-registered test and the alignment checks; write a JSON blob."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    region = pd.read_parquet(RAW_DATA_DIR / "SWPP_region.parquet")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    res = {}
    for y in YEARS:
        mod = model_demand(y)
        load = measured_series(region, "D", y)
        ti = measured_series(region, "TI", y)  # export-positive
        rt = lmp[lmp["year"] == y].sort_values("hour")["rt"].to_numpy(dtype=float)
        assert len(mod) == len(load) == len(rt) == 8760
        valid = np.isfinite(rt)
        order = np.argsort(-np.where(valid, rt, -np.inf), kind="stable")
        top = order[:N_TOP]
        seam_hits = sorted(set(top.tolist()) & SEAM_2024) if y == 2024 else []
        if seam_hits:
            top = np.array([h for h in order if h not in SEAM_2024][:N_TOP])
        top10 = order[:N_TOP10]
        p_mod, p_meas, p_req = pct_rank(mod), pct_rank(load), pct_rank(load + ti)
        d = np.nan_to_num(load)
        align = {
            "lag_H1": lag_scan(mod, load, slice(0, 4380)),
            "lag_H2": lag_scan(mod, load, slice(4380, 8760)),
            "r_all": float(np.corrcoef(mod, load)[0, 1]),
            "peak_hour_model": int(np.argmax(mod)),
            "peak_hour_meas": int(np.argmax(d)),
        }
        med = lambda a, h: float(np.median(a[h]))  # noqa: E731
        res[y] = {
            "top1": {
                "median_p_meas": med(p_meas, top),
                "median_p_mod": med(p_mod, top),
                "delta": med(p_meas, top) - med(p_mod, top),
                "median_p_load_plus_netexport": med(p_req, top),
                "median_abs_pair_diff": float(
                    np.median(np.abs(p_meas[top] - p_mod[top]))
                ),
                "rt_min_in_set": float(rt[top].min()),
                "mean_load_mw": float(load[top].mean()),
                "mean_model_mw": float(mod[top].mean()),
                "mean_netexport_mw": float(ti[top].mean()),
                "share_meas_ge_p90": float((p_meas[top] >= 90).mean()),
            },
            "top10": {
                "median_p_meas": med(p_meas, top10),
                "median_p_mod": med(p_mod, top10),
                "delta": med(p_meas, top10) - med(p_mod, top10),
            },
            "annual": {
                "load_mean_mw": float(load.mean()),
                "model_mean_mw": float(mod.mean()),
                "netexport_mean_mw": float(ti.mean()),
                "load_peak_mw": float(load.max()),
                "model_peak_mw": float(mod.max()),
            },
            "alignment": align,
            "seam_hits_2024": seam_hits,
        }
        t = res[y]["top1"]
        dlt = t["delta"]
        res[y]["verdict"] = (
            "EXONERATED" if abs(dlt) <= 5 else "SHAVED" if dlt > 10 else "INCONCLUSIVE"
        )
        print(
            f"{y}: p_meas {t['median_p_meas']:.1f} p_mod {t['median_p_mod']:.1f} "
            f"delta {dlt:+.1f} -> {res[y]['verdict']} | lag H1/H2 {align['lag_H1']}/"
            f"{align['lag_H2']} r {align['r_all']:.4f} peak {align['peak_hour_model']}/"
            f"{align['peak_hour_meas']}"
        )
    with open(args.out, "w") as f:
        json.dump(res, f, indent=1)


if __name__ == "__main__":
    main()
