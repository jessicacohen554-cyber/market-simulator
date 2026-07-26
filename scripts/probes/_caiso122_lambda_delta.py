"""Compare CAISO demand-weighted λ between two solve bundles (caiso-122).

Reads each bundle's ``hourly/system_<year>.parquet`` sidecar (written by every
solve since 2026-07-19) and reports the CA-zone demand-weighted mean price, so a
HEAD control arm can be attributed against the committed keeper's own bytes
without replaying the keeper (CLAUDE.md rule 15 `[R-DASHBOARD]`).

CA zones are the three in-footprint CAISO zones; ``WECC_import`` is the seam
node and is reported separately rather than folded into the CA average.

Usage:
    python scripts/probes/_caiso122_lambda_delta.py BASE_BUNDLE ARM_BUNDLE \
        [--years 2025]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

# The three in-footprint CAISO load zones. WECC_import is the seam node (an
# import source, not CA load) and is summarised on its own line below.
CA_ZONES: tuple[str, ...] = ("NP15", "SP15", "SDGE")


def _system_frame(bundle: Path, year: int) -> pd.DataFrame:
    """Return a bundle's P1 system hourly frame for ``year``.

    Args:
        bundle: Calibration bundle directory holding an ``hourly/`` sidecar.
        year: Solve year to read.

    Returns:
        The P1-pass rows of ``hourly/system_<year>.parquet``.
    """
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df


def _weighted_lambda(df: pd.DataFrame, zones: tuple[str, ...]) -> float:
    """Return the demand-weighted mean price over ``zones``.

    Args:
        df: A P1 system hourly frame.
        zones: Zone names to include.

    Returns:
        Demand-weighted mean ``price`` in $/MWh.
    """
    sub = df[df["zone"].isin(zones)]
    return float((sub["price"] * sub["demand"]).sum() / sub["demand"].sum())


def main() -> None:
    """Print the per-year CA λ delta between two bundles."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base", type=Path, help="reference bundle (e.g. the keeper)")
    ap.add_argument("arm", type=Path, help="comparison bundle")
    ap.add_argument("--years", type=int, nargs="+", default=[2025])
    args = ap.parse_args()

    print(f"base = {args.base}")
    print(f"arm  = {args.arm}\n")
    header = f"{'year':>6} {'base CA λ':>11} {'arm CA λ':>11} {'Δ':>9} {'Δ%':>8}"
    print(header)
    print("-" * len(header))
    for yr in args.years:
        b = _system_frame(args.base, yr)
        a = _system_frame(args.arm, yr)
        bl = _weighted_lambda(b, CA_ZONES)
        al = _weighted_lambda(a, CA_ZONES)
        pct = (al - bl) / abs(bl) * 100.0
        print(f"{yr:>6} {bl:>11.4f} {al:>11.4f} {al - bl:>+9.4f} {pct:>+7.3f}%")

    # Seam node reported separately — it carries no CA load, so folding it into
    # the CA average would weight the import price by import volume.
    print()
    for yr in args.years:
        b = _system_frame(args.base, yr)
        a = _system_frame(args.arm, yr)
        for zone in ("WECC_import", *CA_ZONES):
            bz = b[b["zone"] == zone]["price"]
            az = a[a["zone"] == zone]["price"]
            if bz.empty or az.empty:
                continue
            print(
                f"{yr} {zone:>12}: base {bz.mean():>8.3f}  arm {az.mean():>8.3f}  "
                f"Δ {az.mean() - bz.mean():>+7.3f}"
            )


if __name__ == "__main__":
    main()
