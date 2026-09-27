"""SPP-88 Card B, phase 0 (ZERO LP): WHERE in the year does the keeper's wind excess sit?

SPP-67 showed the keeper's wind excess over EIA-930 is 100 % CF LEVEL: the ISO bound is
``EIA-930 delivered_h x 1/(1-r)`` in EVERY hour, so the curtailment headroom is placed
PROPORTIONAL TO DELIVERED WIND. Real curtailment is not proportional to delivery; it
concentrates where the wind offer (PTC-backed, below zero) is above the nodal LMP.

This probe measures, from committed artifacts only:
  * headroom_h = delivered_h x (f - 1)                 (what the keeper added)
  * excess_h   = model_h - delivered_h                 (what it failed to curtail)
bucketed by the ACTUAL RT hub LMP (min of North/South hub) and by the actual North-hub
congestion component (MCC), a locational curtailment signal the hub LMP can hide.

Reads: keeper bundle hourly sidecars, data/raw/SWPP_fueltype.parquet,
data/raw/_validation-source/actual_lmp_{hourly_zonal,components_hourly_zonal}_SPP.parquet.
Writes: results/calibration/_spp88_wind_headroom_placement.json (gitignored scratch).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "probes"))
import _spp68_ceiling_phase0 as p68  # noqa: E402  (reuse its validated 930 alignment)

BUNDLE = ROOT / "results/calibration/spp86_arm_span"
YEARS = range(2019, 2026)
BUCKETS = [(-np.inf, 0.0), (0.0, 15.0), (15.0, 30.0), (30.0, np.inf)]


def model_wind(year: int) -> np.ndarray:
    """Keeper P1 wind MW, ISO total, flat 8760."""
    f = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    f = f[(f["pass"] == "P1") & (f["klass"] == "wind")]
    return f.groupby("hour")["mw"].sum().sort_index().to_numpy(float)


def model_price(year: int) -> np.ndarray:
    """Keeper P1 load-weighted system price."""
    f = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    f = f[f["pass"] == "P1"]
    w = (f["price"] * f["demand"]).groupby(f["hour"]).sum()
    return (w / f.groupby("hour")["demand"].sum()).sort_index().to_numpy(float)


def actual_hub(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(min-of-hubs RT LMP, North-hub RT MCC) on the model clock."""
    z = pd.read_parquet(ROOT / "data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet")
    z = z[z["year"] == year].pivot(index="hour", columns="zone", values="rt").sort_index()
    c = pd.read_parquet(ROOT / "data/raw/_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    c = c[(c["year"] == year) & (c["market"] == "rt") & (c["zone"] == "SPPNORTH_HUB")]
    mcc = c.set_index("hour")["mcc"].reindex(z.index)
    return z.min(axis=1).to_numpy(float), mcc.to_numpy(float)


def main() -> None:
    """Print and dump the placement table."""
    out = {}
    for y in YEARS:
        rate, fac, src = p68.gross_factor(y)
        dl, _ = p68.eia930(y, "WND")
        dl = dl.to_numpy(float)
        mw, mp = model_wind(y), model_price(y)
        lmp, mcc = actual_hub(y)
        n = min(len(dl), len(mw), len(lmp))
        dl, mw, mp, lmp, mcc = dl[:n], mw[:n], mp[:n], lmp[:n], mcc[:n]
        head = dl * (fac - 1.0)
        exc = mw - dl
        row = {"rate": rate, "factor": fac, "src": src, "n": n,
               "headroom_twh": head.sum() / 1e6, "excess_twh": exc.sum() / 1e6,
               "actual_neg_hours": int((lmp < 0).sum()),
               "model_neg_hours": int((mp < 0).sum()), "buckets": {}}
        for lo, hi in BUCKETS:
            m = (lmp >= lo) & (lmp < hi)
            row["buckets"][f"{lo}..{hi}"] = {
                "hours": int(m.sum()),
                "headroom_twh": head[m].sum() / 1e6,
                "excess_twh": exc[m].sum() / 1e6,
                "spent_twh": (head[m] - exc[m]).sum() / 1e6,
            }
        # locational signal: positive hub price but North hub congestion strongly negative
        # (MCC < -10 $/MWh) -- export-constrained wind the hub LMP hides.
        loc = (lmp >= 0) & (mcc < -10.0)
        row["pos_price_north_congested"] = {
            "hours": int(loc.sum()), "excess_twh": exc[loc].sum() / 1e6,
            "headroom_twh": head[loc].sum() / 1e6}
        clean = (lmp >= 15.0) & ~(mcc < -10.0)
        row["no_curtail_signal"] = {
            "hours": int(clean.sum()), "excess_twh": exc[clean].sum() / 1e6,
            "headroom_twh": head[clean].sum() / 1e6,
            "delivered_twh": dl[clean].sum() / 1e6}
        # counterpart leg: what the extra wind displaces, per actual-price bucket
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"].pivot_table(
            index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
        ).sort_index().iloc[:n]
        gas_m = ch[[c for c in ch.columns if str(c).startswith(("CC", "CT", "ST_GAS"))]].sum(axis=1).to_numpy()
        coal_m = ch[[c for c in ch.columns if str(c).startswith("COAL")]].sum(axis=1).to_numpy()
        ng = p68.eia930(y, "NG")[0].to_numpy(float)
        col = p68.eia930(y, "COL")[0].to_numpy(float)
        k = min(n, len(ng), len(col))
        for lo, hi in BUCKETS:
            m = (lmp[:k] >= lo) & (lmp[:k] < hi)
            bk = row["buckets"][f"{lo}..{hi}"]
            bk["gas_model_minus_930_twh"] = (gas_m[:k] - ng[:k])[m].sum() / 1e6
            bk["coal_model_minus_930_twh"] = (coal_m[:k] - col[:k])[m].sum() / 1e6
            bk["model_price_median"] = float(np.median(mp[:k][m])) if m.any() else None
        out[y] = row
        b = row["buckets"]
        print(f"{y} r={rate:.4f}({src}) head {row['headroom_twh']:6.2f} exc {row['excess_twh']:6.2f} "
              f"| negH act {row['actual_neg_hours']:4d} mod {row['model_neg_hours']:4d} | "
              + " ".join(f"[{k}] h{v['hours']} exc{v['excess_twh']:.2f}" for k, v in b.items())
              + f" | noSignal h{clean.sum()} exc{row['no_curtail_signal']['excess_twh']:.2f}"
              f" | locCong h{loc.sum()} exc{row['pos_price_north_congested']['excess_twh']:.2f}")
        print("      " + " ".join(
            f"[{kk}] gas {v['gas_model_minus_930_twh']:+.2f} coal {v['coal_model_minus_930_twh']:+.2f}"
            f" modelP~{v['model_price_median']:.1f}" for kk, v in b.items()))
    (ROOT / "results/calibration/_spp88_wind_headroom_placement.json").write_text(
        json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
