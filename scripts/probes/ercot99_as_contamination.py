"""ERCOT-99: is the cleared-share ladder contaminated by AS-committed capacity?

The cleared-share wall's ladder (derive_ercot_dam_cleared_share) is the MW-weighted
quantile of the OFFERED-BUT-UNCLEARED energy-curve segments — the capacity above each
resource's ENERGY award.  But a unit awarded energy + ancillary services carries its
(cheap) energy offer on capacity that is actually doing reserves, so that AS-committed MW
lands in the ladder as cheap "uncleared energy" and pulls the wall down.

This probe re-derives, for the top net-load bins, the CC/CT ladder two ways from the 2023
60-Day DAM disclosure:
  * ABOVE-ENERGY-AWARD  (the current derive's basis), and
  * ABOVE-(ENERGY+AS)-AWARD — the genuinely-uncommitted capacity, excluding MW held for
    RegUp/RRS(PFR/FFR/UFR)/NonSpin/ECRS.
If the AS-excluded ladder is materially higher, the wall is measured-cheap because of AS
contamination, and decontaminating the derive is a measured, forward-regenerable fix.

No solve.  Usage: python -m scripts.probes.ercot99_as_contamination [--year 2023]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    CLASS_OF_RESTYPE,
    HCAP_USD_MWH,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)

_MW = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
_PR = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
_AS = ["RegUp Awarded", "RRSPFR Awarded", "RRSFFR Awarded", "RRSUFR Awarded",
       "NonSpin Awarded", "ECRSSD Awarded"]


def _load(year: int) -> pd.DataFrame:
    import glob

    import pyarrow.parquet as pq
    cols = (["Delivery Date", "Hour Ending", "Resource Type", "HSL",
             "Awarded Quantity", "Resource Status"] + _MW + _PR + _AS)
    frames = []
    for f in sorted(glob.glob(str(REPO / f"data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{year}_*.parquet"))):
        present = set(pq.ParquetFile(f).schema.names)
        df = pd.read_parquet(f, columns=[c for c in cols if c in present])
        for c in _AS:  # backfill AS columns absent in pre-ECRS vintages
            if c not in df.columns:
                df[c] = 0.0
        frames.append(df[df["Resource Type"].isin(CLASS_OF_RESTYPE)].copy())
    return pd.concat(frames, ignore_index=True)


def _ladder(df: pd.DataFrame, year: int, exclude_as: bool):
    """Return per-bin ladder for CC and CT (above energy-award, optionally +AS)."""
    dt = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
    mo, dy, he = dt.dt.month.to_numpy(), dt.dt.day.to_numpy(), df["Hour Ending"].astype(int).to_numpy()
    keep = ~((mo == 2) & (dy == 29)) & (dt.dt.year.to_numpy() == year)
    df = df[keep].copy()
    hoy = _MONTH_START_HOUR[mo[keep] - 1] + (dy[keep] - 1) * 24 + (he[keep] - 1)
    df["hoy"] = hoy
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    gas = _gas_day_series().reindex(dt[keep].dt.normalize()).to_numpy(float)
    as_mw = df[[c for c in _AS if c in df.columns]].fillna(0.0).to_numpy().sum(1)
    award = df["Awarded Quantity"].fillna(0.0).clip(lower=0).to_numpy()
    avail = np.where(df["Resource Status"].eq("OUT"), 0.0, df["HSL"].to_numpy(float))
    lo = award + (as_mw if exclude_as else 0.0)

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hbin = np.searchsorted(edges, pct, side="right")
    df_bin = hbin[np.clip(df["hoy"].to_numpy(int), 0, len(pct) - 1)]

    MW = df[_MW].to_numpy(float); PR = df[_PR].to_numpy(float)
    seg_mw, seg_mult, seg_bin, seg_cls = [], [], [], []
    prev = np.zeros(len(df))
    for k in range(10):
        q, p = MW[:, k], np.minimum(PR[:, k], HCAP_USD_MWH)
        valid = ~np.isnan(q) & ~np.isnan(p) & (gas > 0)
        loo = np.maximum(prev, lo)
        hi = np.minimum(q, avail)
        mw = np.where(valid, np.maximum(hi - loo, 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg_mw.append(mw[take]); seg_mult.append(p[take] / gas[take])
            seg_bin.append(df_bin[take]); seg_cls.append(df["cls"].to_numpy()[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    seg = pd.DataFrame({"mw": np.concatenate(seg_mw), "mult": np.concatenate(seg_mult),
                        "bin": np.concatenate(seg_bin), "cls": np.concatenate(seg_cls)})
    out = {}
    for cls in ("CC", "CT"):
        rows = {}
        for b in (5, 6):  # p90-97 and >=p97 (the scarcity bins)
            g = seg[(seg["cls"] == cls) & (seg["bin"] == b)]
            qs = _weighted_quantiles(g["mult"].to_numpy(float), g["mw"].to_numpy(float), LADDER_QUANTILES)
            rows[b] = (qs, float(g["mw"].sum()))
        out[cls] = rows
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="ercot99_as_contamination")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args(argv)
    df = _load(args.year)
    gas = _gas_day_series()
    gas_med = float(gas.median())
    print(f"[gas] median gas_day {args.year}: ${gas_med:.2f}/MMBtu (mult x this ~ $/MWh)\n")
    base = _ladder(df, args.year, exclude_as=False)
    deas = _ladder(df, args.year, exclude_as=True)
    binlbl = {5: "p90-97", 6: ">=p97"}
    for cls in ("CC", "CT"):
        print(f"=== {cls} above-boundary ladder (mult x gas; $ at median gas) ===")
        for b in (5, 6):
            qb, mwb = base[cls][b]; qd, mwd = deas[cls][b]
            print(f"  bin {b} ({binlbl[b]}):")
            print(f"    ABOVE-ENERGY-AWARD (current): " +
                  " ".join(f"{q:.0f}%=${m*gas_med:.0f}" for q, m in zip([10,30,50,70,90], qb)) +
                  f"  [{mwb/1e3:.0f} GWh seg]")
            print(f"    ABOVE-ENERGY+AS  (decontam) : " +
                  " ".join(f"{q:.0f}%=${m*gas_med:.0f}" for q, m in zip([10,30,50,70,90], qd)) +
                  f"  [{mwd/1e3:.0f} GWh seg]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
