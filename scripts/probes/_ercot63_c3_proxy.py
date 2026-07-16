"""ERCOT-63 C3 proxies for unregistered probe bundles (rule-16 diagnostic).

Reproduces the three C3 scores the rubric gates registered runs on, straight
from a probe bundle's ``system.parquet`` and the committed bench part —
same constructions as ``scripts/calibration_verdict.py`` (v2.4 basis):

* C3a — system demand-weighted mean settled price vs the committed ``rt_lw``;
* C3b — monthly demand-weighted price NRMSE vs ``rt_lw_mon``;
* C3c — settled-price tail hours (max zonal settled > $200) vs the committed
  DA-expressible actual tail.

Usage::

    python scripts/probes/_ercot63_c3_proxy.py BUNDLE [BUNDLE ...] [--year 2023]
"""

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def settled(df: pd.DataFrame) -> pd.Series:
    # The bundle's ``price`` column IS the gated settlement basis: it
    # reproduces the registered ercot59 keeper byte-for-byte (C3a +3.9%,
    # C3c 171h on the 2023 reconstruction). The rtordpa_overlay /
    # ordc_adder columns are report-side diagnostics, NOT in the gated lw.
    return df["price"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+")
    ap.add_argument("--year", type=int, default=2023)
    args = ap.parse_args()

    bench = json.loads(
        gzip.open(
            REPO / f"frontend/data/backcast/bench/ERCOT/{args.year}.json.gz"
        ).read()
    )["bench"]["avgLMP"]
    rt_lw, rt_lw_mon = bench["rt_lw"], bench["rt_lw_mon"]
    tails = json.load(open(REPO / "frontend/data/backcast/tail/actual_tail.json"))
    tail_rec = (tails.get("isos") or {}).get("ERCOT", {}).get(str(args.year))
    da_tail = tail_rec.get("da_gt") if tail_rec else None
    # Rubric v2.6 (2026-07-16): ERCOT's C3c gates on the RT hourly tail; the
    # DA count stays printed as the diagnostic companion.
    rt_tail = tail_rec.get("rt_gt") if tail_rec else None

    month_of_hour = pd.date_range(
        f"{args.year}-01-01", periods=8760, freq="h"
    ).month.to_numpy()

    for name in args.bundles:
        b = REPO / "results" / "calibration" / name
        df = pd.read_parquet(b / "system.parquet")
        df = df[(df["pass"] == "P1") & (df["year"] == args.year)].copy()
        df["settled"] = settled(df)
        # C3a: total demand-weighted mean over all zone-hours.
        c3a_model = float((df["settled"] * df["demand"]).sum() / df["demand"].sum())
        c3a = (c3a_model - rt_lw) / rt_lw
        # C3b: monthly demand-weighted lw price NRMSE vs rt_lw_mon.
        df["month"] = month_of_hour[df["hour"].to_numpy()]
        g = df.groupby("month").apply(
            lambda d: (d["settled"] * d["demand"]).sum() / d["demand"].sum(),
            include_groups=False,
        )
        model_mon = g.reindex(range(1, 13)).to_numpy()
        act = np.array([v if v is not None else np.nan for v in rt_lw_mon])
        mask = ~np.isnan(act) & ~np.isnan(model_mon)
        nrmse = float(
            np.sqrt(np.mean((model_mon[mask] - act[mask]) ** 2)) / np.mean(act[mask])
        )
        # C3c: hours max zonal settled > $200. Gated vs RT (v2.6); DA printed
        # as the diagnostic companion.
        tail = int((df.groupby("hour")["settled"].max() > 200.0).sum())
        tail_s = f"{tail}h"
        if rt_tail is not None:
            tail_s += f" vs RT {rt_tail} (gated)"
        if da_tail is not None:
            tail_s += f" / DA {da_tail} (diag)"
        print(
            f"{name:32s} C3a {c3a * 100:+.1f}% (model {c3a_model:.2f} vs rt_lw "
            f"{rt_lw:.2f})  C3b {nrmse:.3f}  C3c {tail_s}"
        )


if __name__ == "__main__":
    main()
