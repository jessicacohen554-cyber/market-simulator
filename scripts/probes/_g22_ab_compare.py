"""G-22 A/B compare: price formation + virtual clearing, probe vs baseline.

For each solved year of two bundles (baseline first), print the pjm-99
finding's price table (all-hours LW mean, top-150 LW, p99, max vs the
actual DA) plus — when the probe carries the DA virtual-bid layer — the
cleared DEC/INC volumes at the top-150 hours (the endogenous-clearing
sanity check: reality cleared net +7-11 GW at the 2024 top hours).

Pure diagnostic (rule 16): prints tables, writes nothing.

Usage:
    python scripts/probes/_g22_ab_compare.py \
        results/calibration/pjm98_baseline_20260712 \
        results/calibration/pjm100_da_virtual_bids [--years 2023 2024 2025]
        [--top 150]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.interchange_config import IMPORT_ZONE  # noqa: E402

CAL_DIR = REPO / "data" / "raw" / "_validation-source"


def _actual_da(year: int, hours: int) -> np.ndarray:
    df = pd.read_parquet(CAL_DIR / "actual_lmp_hourly_PJM.parquet")
    df = df[df["year"] == year]
    out = np.full(hours, np.nan)
    idx = df["hour"].to_numpy(dtype=int)
    keep = (idx >= 0) & (idx < hours)
    out[idx[keep]] = df["da"].to_numpy(dtype=float)[keep]
    return out


def _prices(bundle: Path, year: int, ext_zone: str) -> tuple[np.ndarray, np.ndarray]:
    sysf = pd.read_parquet(bundle / "system.parquet")
    sysf = sysf[(sysf["year"] == year) & (sysf["pass"] == "P1")]
    internal = sysf[sysf["zone"] != ext_zone]
    load = internal.groupby("hour")["demand"].sum()
    pxd = (internal["price"] * internal["demand"]).groupby(internal["hour"]).sum()
    return (pxd / load).to_numpy(), load.to_numpy()


def _virtual_cleared(bundle: Path, year: int, top: np.ndarray) -> dict | None:
    path = bundle / "dispatch" / f"{year}_P1.parquet"
    d = pd.read_parquet(path, columns=["unit_id", "klass", "hour", "mw"])
    v = d[d["klass"].isin(["VIRTUAL_DEC", "VIRTUAL_INC"])]
    if v.empty:
        return None
    per = v.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
    ).reindex(columns=["VIRTUAL_DEC", "VIRTUAL_INC"], fill_value=0.0)
    # DEC rows dispatch NEGATIVE mw (export-sink form): cleared DEC = -sum.
    dec = -per["VIRTUAL_DEC"].reindex(range(int(d["hour"].max()) + 1), fill_value=0.0)
    inc = per["VIRTUAL_INC"].reindex(range(int(d["hour"].max()) + 1), fill_value=0.0)
    return {
        "dec_top_gw": float(dec.iloc[top].mean() / 1e3),
        "inc_top_gw": float(inc.iloc[top].mean() / 1e3),
        "dec_all_gw": float(dec.mean() / 1e3),
        "inc_all_gw": float(inc.mean() / 1e3),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("baseline", type=Path)
    ap.add_argument("probe", type=Path)
    ap.add_argument("--years", type=int, nargs="+", default=None)
    ap.add_argument("--top", type=int, default=150)
    args = ap.parse_args()

    meta = json.loads((args.baseline / "meta.json").read_text())
    ext_zone = IMPORT_ZONE.get(meta["iso"], "")
    years = args.years or meta["years"]
    rows = []
    for year in years:
        year = int(year)
        have = all(
            (b / "dispatch" / f"{year}_P1.parquet").exists()
            for b in (args.baseline, args.probe)
        )
        if not have:
            print(f"{year}: not solved in both bundles — skipping")
            continue
        lw_b, load = _prices(args.baseline, year, ext_zone)
        lw_p, _ = _prices(args.probe, year, ext_zone)
        da = _actual_da(year, len(lw_b))
        top = np.argsort(load)[-args.top :]
        top = top[np.isfinite(da[top])]
        rows.append(
            {
                "year": year,
                "base LW": np.mean(lw_b),
                "probe LW": np.mean(lw_p),
                "actual LW": np.nanmean(da),
                "base top150": lw_b[top].mean(),
                "probe top150": lw_p[top].mean(),
                "actual top150": np.nanmean(da[top]),
                "base max": lw_b.max(),
                "probe max": lw_p.max(),
                "actual max": np.nanmax(da),
            }
        )
        v = _virtual_cleared(args.probe, year, top)
        if v:
            print(
                f"{year} virtual clearing: top-{len(top)} DEC {v['dec_top_gw']:.1f} GW "
                f"/ INC {v['inc_top_gw']:.1f} GW (net {v['dec_top_gw'] - v['inc_top_gw']:+.1f}); "
                f"all-year DEC {v['dec_all_gw']:.1f} / INC {v['inc_all_gw']:.1f} GW"
            )
    if rows:
        print()
        print(
            pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.2f}")
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
