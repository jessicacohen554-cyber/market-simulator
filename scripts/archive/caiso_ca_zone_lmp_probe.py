"""CAISO CA-zone LMP validation — demand-weighted avg LMP + hours>$200.

Computes the CA-zone (NP15 / ZP26 / SP15) demand-weighted average LMP per year
and the count of CA hours over $200, from a bundle's ``system.parquet`` (per-zone
hourly ``price`` + ``demand``). The WECC import node and any non-CA zone are
excluded. Used to validate the caiso 37 offer-curve change against the caiso 35
keeper and the measured CA-zone average (2023 43.8 / 2024 33.0 / 2025 33.6).

Usage::

    .venv/bin/python scripts/archive/caiso_ca_zone_lmp_probe.py BUNDLE_DIR \\
        [--year 2023 2024 2025] [--pass P1]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

CA_ZONES = ("NP15", "ZP26", "SP15")
ACTUAL = {2023: 43.8, 2024: 33.0, 2025: 33.6}


def _ca_zone_metrics(bundle: Path, year: int, pass_label: str):
    """Return (demand-weighted avg LMP, hours>$200) for the CA zones, one year."""
    df = pd.read_parquet(bundle / "system.parquet")
    df = df[(df["year"] == year) & (df["pass"] == pass_label)]
    df = df[df["zone"].isin(CA_ZONES)].copy()
    if df.empty:
        return None, None
    # Demand-weighted average over all CA zone-hours.
    w = df["demand"].clip(lower=0.0)
    avg = float((df["price"] * w).sum() / w.sum())
    # Hours over $200: count hours where the CA-zone demand-weighted hourly LMP
    # (load-weighted across the three CA hubs) exceeds $200.
    hourly = df.groupby("hour").apply(
        lambda g: (
            (g["price"] * g["demand"].clip(lower=0.0)).sum()
            / max(g["demand"].clip(lower=0.0).sum(), 1e-9)
        )
    )
    over200 = int((hourly > 200.0).sum())
    return avg, over200


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--year", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--pass", dest="pass_label", default="P1")
    args = ap.parse_args()

    print(f"CA-zone (NP15/ZP26/SP15) LMP — {args.bundle}  pass={args.pass_label}")
    print(f"{'year':>6} {'avg_LMP':>9} {'actual':>8} {'err%':>7} {'hrs>$200':>9}")
    for y in args.year:
        avg, over200 = _ca_zone_metrics(args.bundle, y, args.pass_label)
        if avg is None:
            print(f"{y:>6}  (no data)")
            continue
        act = ACTUAL.get(y)
        errpct = f"{100 * (avg - act) / act:+6.1f}" if act else "   n/a"
        actstr = f"{act:8.1f}" if act else "     n/a"
        print(f"{y:>6} {avg:9.1f} {actstr} {errpct:>7} {over200:>9}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
