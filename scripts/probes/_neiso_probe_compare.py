"""Ad-hoc drift check: compare two NEISO calibration bundles on the metrics the
probe panel keys on — per-class P1 TWh and the demand-weighted P1 price.

Usage:
    python scripts/probes/_neiso_probe_compare.py BUNDLE_A BUNDLE_B [--year 2024]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ROOT = REPO / "results" / "calibration"


def class_twh(bundle: str, year: int) -> pd.Series:
    df = pd.read_parquet(
        ROOT / bundle / "dispatch" / f"{year}_P1.parquet", columns=["klass", "mw"]
    )
    return df.groupby("klass", observed=True)["mw"].sum() / 1.0e6


def dw_price(bundle: str, year: int) -> float:
    s = pd.read_parquet(ROOT / bundle / "system.parquet")
    s = s[(s["pass"] == "P1") & (s["year"] == year)]
    return float((s["price"] * s["demand"]).sum() / s["demand"].sum())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--year", type=int, default=2024)
    args = ap.parse_args()

    ta, tb = class_twh(args.a, args.year), class_twh(args.b, args.year)
    cmp = pd.DataFrame({"A_TWh": ta, "B_TWh": tb}).fillna(0.0)
    cmp["dTWh"] = cmp["B_TWh"] - cmp["A_TWh"]
    cmp = cmp.sort_values("A_TWh", ascending=False)
    pd.set_option("display.float_format", "{:.4f}".format)
    print(f"per-class P1 TWh ({args.year}):  A={args.a}  B={args.b}")
    print(cmp.to_string())
    print(f"\nmax |dTWh| = {cmp['dTWh'].abs().max():.4f}")
    pa, pb = dw_price(args.a, args.year), dw_price(args.b, args.year)
    print(
        f"\ndemand-weighted P1 price:  A={pa:.2f}  B={pb:.2f}  d={pb - pa:+.3f} $/MWh"
    )


if __name__ == "__main__":
    main()
