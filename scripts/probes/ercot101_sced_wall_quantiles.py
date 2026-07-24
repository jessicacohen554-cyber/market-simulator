"""ERCOT-101 Lane A — measure the 2024/2025 SCED online-spare offer wall at
EXTENDED quantiles (p90..p99.9 + max), to test whether a measured wall exists
ABOVE the frozen ladder's p90 cap at the top net-load bins (the missed-tail band).

Reuses the committed derive machinery (derive_ercot_sced_offer_wall) verbatim for
the spare-segment construction + net-load binning; the ONLY change is the quantile
grid. Prints, per (class x net-load bin), the MW-weighted spare-offer wall as both
an effective-HR multiplier and a $/MWh (x delivered-gas p50), so an under-reach vs
the model marginal tranche (~$70-130 at the missed hours) is directly visible.

Rule 13/23 note: this is a MEASUREMENT of the same posted-offer corpus the ladder
already reads, at finer quantiles — not a residual fit. It only tells us whether
the ladder's p90 truncation drops a real measured wall.

No LP. Usage: python -m scripts.probes.ercot101_sced_wall_quantiles [--years 2024 2025]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_sced_offer_wall import (  # noqa: E402
    _chunk_segments,
    _coerce_sced_numeric,
    _delivery_year_rows,
    _sced_source_files,
    CLASS_OF_RESTYPE,
    _READ_COLS,
)
from derive_ercot_dam_cleared_share import (  # noqa: E402
    NETLOAD_PCT_EDGES,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)
import pandas as pd  # noqa: E402

QGRID = [0.5, 0.9, 0.95, 0.97, 0.99, 0.995, 0.999]
# representative delivered-gas $/MMBtu for the $/MWh conversion (keeper gas)
GAS = {2023: 2.54, 2024: 2.19, 2025: 3.52}


def measure(year: int, gas_day: pd.Series) -> None:
    files = _sced_source_files(year)
    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")
    n_bins = len(edges) + 1
    mult_acc: dict = {}
    mw_acc: dict = {}
    for path in files:
        df = pd.read_parquet(path, columns=[c for c in _READ_COLS if c])
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = _coerce_sced_numeric(df[stat.str.startswith("ON")].copy())
        seg = _chunk_segments(df, gas_day, hour_bin)
        del df
        if seg.empty:
            continue
        for (cls, b), grp in seg.groupby(["cls", "bin"], sort=False):
            key = (cls, int(b))
            mult_acc.setdefault(key, []).append(grp["mult"].to_numpy())
            mw_acc.setdefault(key, []).append(grp["mw"].to_numpy())
    g = GAS[year]
    print(f"\n=== {year} (gas ${g}/MMBtu; source files: "
          f"{[p.name for p in files]}) ===")
    hdr = "  ".join(f"p{int(q*1000)/10:g}" for q in QGRID)
    for cls in ("CC", "CT"):
        print(f"  {cls} spare-offer wall $/MWh by net-load bin "
              f"(quantiles {hdr}):")
        for b in range(n_bins):
            key = (cls, b)
            if key not in mult_acc:
                continue
            mult = np.concatenate(mult_acc[key]).astype(float)
            mw = np.concatenate(mw_acc[key]).astype(float)
            qs = _weighted_quantiles(mult, mw, QGRID)
            usd = [q * g for q in qs]
            row = "  ".join(f"${u:6.0f}" for u in usd)
            binlbl = f"bin{b}" + ("(TOP)" if b == n_bins - 1 else "")
            print(f"    {binlbl:>10}: {row}   [spare {mw.sum()/1e3:6.1f} GWh]")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot101_sced_wall_quantiles")
    ap.add_argument("--years", type=int, nargs="+", default=[2024, 2025])
    args = ap.parse_args(argv)
    gas_day = _gas_day_series()
    for y in args.years:
        measure(y, gas_day)
    return 0


if __name__ == "__main__":
    sys.exit(main())
