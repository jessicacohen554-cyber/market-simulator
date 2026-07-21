"""CAISO-109 P1-A derive-first: does a WECC-neighbor surplus QUANTITY stabilize
the belly import depth where caiso-107's CA *price* observables failed?

caiso-106/107 established the belly over-import (+2.6 GW) is REAL but its depth is
NOT year-stable on any CAISO observable (net-load CV 0.33-0.37; PaloVerde hub
LEVEL CV 0.49-1.62; hub-CA basis CV 0.71-0.89) — caiso-107 §2 root cause: the CA
belly transfer depends on the full WEST-WIDE surplus QUANTITY (WECC solar+load),
which no CA price summarizes, and caiso-107 tested only PRICE observables. This
probe tests the one un-refuted lever class: condition the measured belly TOTAL
net import on a measured WEST-WIDE surplus QUANTITY (EIA-930 BALANCE neighbor-BA
solar / solar-penetration / net-generation surplus) and run the SAME caiso-106
honesty gate (per-band cross-year CV ≤ 0.20 + LOYO ≤ 0.25).

PASS (a signal whose bands are year-stable) => admissible, build the LP form.
FAIL (all signals unstable) => file the kill, no mechanism (derive-first, rule 1).

NO SOLVE, NO LP, NO fitted throttle. Pure raw EIA-930 BALANCE (all 66 BAs,
already on disk) + the caiso-106 measured CISO belly net import.

Usage: PYTHONPATH=. .venv/bin/python scripts/probes/_caiso109_westwide_surplus.py
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
BAL = sorted(glob.glob(str(REPO / "data/raw/eia-930/EIA930_BALANCE_*.parquet")))
YEARS = (2023, 2024, 2025)
BELLY_HOD = (10, 11, 12, 13, 14)  # caiso-106 BELLY window (CISO local, end-of-hour label)
CV_MAX = 0.20                      # caiso-81/86/87 estimation-stage gate
LOYO_MAX = 0.25
# WECC neighbors: EIA-930 Region NW + SW (the western interconnect surplus that
# exports into CAISO's WECC_PNW / WECC_DSW corridors). CISO excluded by region.
WEST_REGIONS = ("NW", "SW")


def _read_balance_file(path: str) -> pd.DataFrame:
    """Load one BALANCE file, normalizing the heterogeneous solar schema."""
    names = set(pq.ParquetFile(path).schema.names)
    want = [
        "Balancing Authority", "Region", "UTC Time at End of Hour",
        "Local Time at End of Hour", "Demand (MW) (Adjusted)",
        "Net Generation (MW) (Adjusted)", "Total Interchange (MW) (Adjusted)",
    ]
    # solar: old single column OR new split with/without integrated battery
    solar_cols = [c for c in names if c.startswith("Net Generation (MW) from Solar")
                  and "(Adjusted)" in c and "Imputed" not in c]
    df = pd.read_parquet(path, columns=[c for c in want if c in names] + solar_cols)
    df["solar"] = df[solar_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0).sum(axis=1)
    for c in ("Demand (MW) (Adjusted)", "Net Generation (MW) (Adjusted)",
              "Total Interchange (MW) (Adjusted)"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["UTC"] = pd.to_datetime(df["UTC Time at End of Hour"], utc=True)
    df["LOCAL"] = pd.to_datetime(df["Local Time at End of Hour"])
    return df


def load_balance() -> pd.DataFrame:
    files = [f for f in BAL if any(str(y) in f for y in YEARS)]
    return pd.concat([_read_balance_file(f) for f in files], ignore_index=True)


def build_series(d: pd.DataFrame):
    """Per-year (belly net import, west-surplus signals) aligned by UTC."""
    d = d.copy()
    d["yr"] = d["UTC"].dt.year
    # CISO measured net import (MW) = -Total Interchange; belly by CISO local hod
    ciso = d[d["Balancing Authority"] == "CISO"].copy()
    ciso["net_import"] = -ciso["Total Interchange (MW) (Adjusted)"]
    ciso["hod"] = ciso["LOCAL"].dt.hour
    ciso = ciso[["UTC", "yr", "hod", "net_import"]].dropna(subset=["net_import"])
    # West aggregate by UTC hour
    west = d[d["Region"].isin(WEST_REGIONS) & (d["Balancing Authority"] != "CISO")]
    agg = west.groupby("UTC").agg(
        west_solar=("solar", "sum"),
        west_dem=("Demand (MW) (Adjusted)", "sum"),
        west_ng=("Net Generation (MW) (Adjusted)", "sum"),
    ).reset_index()
    agg["west_solpen"] = agg["west_solar"] / agg["west_dem"].replace(0, np.nan)
    agg["west_surplus"] = agg["west_ng"] - agg["west_dem"]  # net export capability
    m = ciso.merge(agg, on="UTC", how="inner")
    return m[np.isin(m["hod"], BELLY_HOD)].copy()


def _fixed_bands(vals: np.ndarray, n=6):
    """Fixed absolute bands (pooled quantiles) so a band = the same physical
    west-wide state in every year (the caiso-106 NL_BANDS_GW discipline)."""
    qs = np.nanpercentile(vals, np.linspace(0, 100, n + 1))
    qs[0], qs[-1] = -np.inf, np.inf
    return list(zip(qs[:-1], qs[1:]))


def gate_signal(m: pd.DataFrame, col: str, label: str, pct: int = 50) -> bool:
    bands = _fixed_bands(m[col].to_numpy())
    print(f"\n=== SIGNAL: {label} ({col}) — belly net import p{pct} by fixed band ===")
    print("  band" + "".join(f"{y:>10}" for y in YEARS) + "     CV    LOYOmax  gate")
    all_pass = True
    for lo, hi in bands:
        pv = {}
        for y in YEARS:
            sel = m[(m.yr == y) & (m[col] >= lo) & (m[col] < hi)]
            pv[y] = float(np.nanpercentile(sel["net_import"], pct)) if len(sel) >= 20 else np.nan
        arr = np.array([pv[y] for y in YEARS])
        if np.isnan(arr).any():
            print(f"  [{lo:8.0f},{hi:8.0f}) " + "".join(f"{pv[y]:>10.0f}" for y in YEARS) + "   sparse")
            continue
        mean = np.mean(arr)
        cv = np.std(arr) / abs(mean) if abs(mean) > 50 else np.std(arr) / 50.0  # near-zero: ±MW/50
        loyo = max(abs(np.mean([pv[y] for y in YEARS if y != h]) - pv[h]) /
                   (abs(pv[h]) if abs(pv[h]) > 50 else 50.0) for h in YEARS)
        ok = cv <= CV_MAX and loyo <= LOYO_MAX
        mono = (arr[0] < arr[1] < arr[2]) or (arr[0] > arr[1] > arr[2])
        all_pass = all_pass and ok
        print(f"  [{lo:8.0f},{hi:8.0f}) " + "".join(f"{pv[y]:>10.0f}" for y in YEARS)
              + f"   {cv:5.2f}  {loyo:6.1%}  {'PASS' if ok else 'FAIL'}"
              + ("  (monotone yr-trend)" if mono else ""))
    print(f"  --> {label} p{pct}: {'STABLE (admissible)' if all_pass else 'UNSTABLE (fails gate)'}")
    return all_pass


def joint_check(m: pd.DataFrame) -> None:
    """Condition west surplus WITHIN CAISO's own deep-belly-surplus state
    (CISO local hod 11-13, the solar peak) — the joint two-sided surplus the
    caiso-107 §2 root cause named. If even the joint state year-drifts, the
    non-stationarity is not an observable-choice problem."""
    core = m[np.isin(m.hod, (11, 12, 13))]
    print("\n=== JOINT: west surplus WITHIN CAISO solar-peak hours (hod 11-13) ===")
    gate_signal(core, "west_surplus", "West surplus | CA solar-peak", pct=50)


def main() -> None:
    d = load_balance()
    m = build_series(d)
    print(f"belly-hour samples per year: " +
          ", ".join(f"{y}={int((m.yr==y).sum())}" for y in YEARS))
    print(f"belly measured net import mean by year (MW): " +
          ", ".join(f"{y}={m[m.yr==y].net_import.mean():+.0f}" for y in YEARS))
    results = {
        "west_solar p50": gate_signal(m, "west_solar", "West aggregate SOLAR"),
        "west_solpen p50": gate_signal(m, "west_solpen", "West solar PENETRATION"),
        "west_surplus p50": gate_signal(m, "west_surplus", "West NET-GEN SURPLUS (NG-D)"),
        "west_surplus p95": gate_signal(m, "west_surplus", "West SURPLUS ceiling", pct=95),
    }
    joint_check(m)
    print("\n================= VERDICT =================")
    for k, v in results.items():
        print(f"  {k:22s} -> {'STABLE' if v else 'unstable'}")
    print("  A signal that PASSES => the west-wide surplus QUANTITY stabilizes the belly")
    print("  depth (where caiso-107 price observables failed) => admissible LP form.")


if __name__ == "__main__":
    main()
