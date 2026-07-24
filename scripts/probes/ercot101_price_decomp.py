"""ERCOT-101 Lane B/A — first-hour C3a gap decomposition on the EXACT scorer basis.

Reproduces the official load-weighted C3a (model zonal energy-LP dual, demand-
weighted over zones+hours, vs the zonal settlement-LZ actual on the SAME measured
demand weights — the rubric-v2.4 rt_lw basis), then decomposes the mean-price gap
by ACTUAL price band to show which band carries the under-prediction. Also emits a
congestion diagnostic: hub (HB_HUBAVG) vs load-zone settlement actual at the tail,
to separate an offer-depth bound from a network-representation bound.

No LP. Reads the committed keeper system sidecar + the committed zonal actual
archive. Usage: python -m scripts.probes.ercot101_price_decomp <bundle> [--year Y...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# Model zone -> settlement LZ(s) (mirrors derive_actual_lmp.ERCOT_MODEL_ZONE_TO_LZ)
ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}
BANDS = [(-1e9, 0), (0, 30), (30, 80), (80, 200), (200, 300), (300, 1000),
         (1000, 1e9)]


def _zonal_actual(year: int) -> dict[str, np.ndarray]:
    from market_sim.config.paths import CALIBRATION_DIR
    df = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_zonal_ERCOT.parquet")
    df = df[df["year"] == year]
    out: dict[str, np.ndarray] = {}
    for sp, g in df.groupby("settlement_point"):
        arr = np.full(8760, np.nan)
        arr[g["hour"].to_numpy()] = g["rt"].to_numpy()
        out[str(sp)] = arr
    return out


def run(bundle: Path, year: int) -> None:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = s[s["pass"] == "P1"]
    zones = list(p1["zone"].unique())
    pmod = p1.pivot(index="hour", columns="zone", values="price")
    dem = p1.pivot(index="hour", columns="zone", values="demand")
    zones = [z for z in pmod.columns]
    P = pmod.to_numpy()            # (T, Z) model energy dual
    D = dem.to_numpy()            # (T, Z) measured demand
    act = _zonal_actual(year)

    # actual per model-zone = simple mean of its LZ series
    A = np.full_like(P, np.nan)
    for j, z in enumerate(zones):
        lzs = ZONE_TO_LZ.get(z)
        if not lzs:
            continue
        stack = np.vstack([act[l] for l in lzs if l in act])
        A[:, j] = np.nanmean(stack, axis=0)

    Wtot = D.sum()
    model_lw = float((P * D).sum() / Wtot)
    # actual lw on model-demand weights (scorer uses measured zonal demand ==
    # model demand in backcast); mask hours/zones with NaN actual
    va = ~np.isnan(A)
    actual_lw = float((A[va] * D[va]).sum() / D[va].sum())
    gap = model_lw - actual_lw
    print(f"\n=== {year} ===")
    print(f"  model_lw ${model_lw:.2f}  actual_lw(zonal) ${actual_lw:.2f}  "
          f"C3a {100 * gap / actual_lw:+.1f}%  gap ${gap:+.2f}/MWh")

    # per-hour system prices (demand-weighted over zones)
    Dh = D.sum(1)
    model_h = (P * D).sum(1) / Dh
    Aw = np.where(va, A, 0.0)
    actual_h = (Aw * D).sum(1) / np.where(va, D, 0.0).sum(1)

    # decompose the annual gap contribution by ACTUAL system-price band
    print(f"  {'band ($/MWh)':>14} | {'hrs':>5} | {'act mean':>8} | "
          f"{'mod mean':>8} | {'gap contrib $/MWh':>17} | {'% of gap':>8}")
    contribs = []
    for lo, hi in BANDS:
        sel = (actual_h >= lo) & (actual_h < hi) & ~np.isnan(actual_h)
        if not sel.any():
            contribs.append(0.0)
            continue
        w = Dh[sel]
        # contribution to (model_lw - actual_lw): sum over band of
        # (model_h-actual_h)*Dh / Wtot_hours
        contrib = float(((model_h[sel] - actual_h[sel]) * w).sum() / Dh.sum())
        contribs.append(contrib)
        am = float((actual_h[sel] * w).sum() / w.sum())
        mm = float((model_h[sel] * w).sum() / w.sum())
        print(f"  {f'[{lo:g},{hi:g})':>14} | {int(sel.sum()):>5} | {am:>8.1f} | "
              f"{mm:>8.1f} | {contrib:>17.2f} | {100 * contrib / gap:>7.1f}%")
    print(f"  {'TOTAL':>14} | {'':>5} | {actual_lw:>8.1f} | {model_lw:>8.1f} | "
          f"{sum(contribs):>17.2f} | {100 * sum(contribs) / gap:>7.1f}%")

    # congestion diagnostic: at the >$200 actual tail hours, hub vs LZ spread
    hub = act.get("HB_HUBAVG")
    tail = (actual_h > 200) & ~np.isnan(actual_h)
    if hub is not None and tail.any():
        lz_tail = actual_h[tail]
        hub_tail = hub[tail]
        vv = ~np.isnan(hub_tail)
        spread = lz_tail[vv] - hub_tail[vv]
        print(f"  congestion @ actual>$200 ({int(tail.sum())} h): "
              f"LZ-lw p50 ${np.nanmedian(lz_tail):.0f} vs HB_HUBAVG p50 "
              f"${np.nanmedian(hub_tail):.0f}; (LZ−hub) p50 ${np.nanmedian(spread):+.0f} "
              f"mean ${np.nanmean(spread):+.0f}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot101_price_decomp")
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args(argv)
    b = Path(args.bundle) if Path(args.bundle).is_absolute() else REPO / args.bundle
    for y in args.year:
        run(b, y)
    return 0


if __name__ == "__main__":
    sys.exit(main())
