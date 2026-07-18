#!/usr/bin/env python3
"""Derive the reference-price-interface seam limits from PJM's published flows.

The ``interface_limit_mw`` of each neighbor in
:data:`market_sim.config.constants.INTERFACE_NEIGHBORS` bounds the seam flow in
every LP hour, so it must be a real, reproducible *transfer rating* — never a
value tuned to the net-MWh target (claude.md rule #11). This script derives it
from PJM's OWN published per-tie interchange (the Data Miner
``import_export_act_sch_interchange`` extract,
``data/raw/iso-specific-transmission/PJM_<year>_import_export_act_sch_interchange.csv``):

  * each external tie is mapped to the registry seam it lands on (MISO, NYISO,
    Carolinas);
  * the per-tie hourly ``actual_flow`` is summed within a seam to the
    *simultaneous* seam transfer (ties don't all peak at once, so this is below
    the sum of individual tie maxima the old 10/3/3.5 GW envelopes used);
  * the limit is the **p99.5 of |simultaneous seam flow|** pooled across the
    available years — the firm continuous transfer capability (the duration
    curve's upper envelope minus the top ~0.5% transient/loop-flow hours).

p99.5, not the raw max, because a transfer *rating* is a sustainable capability
rather than a single demonstrated hour; and a flow envelope rather than the mean
because the mean would be fitting the limit to the realized net export. The
result is regenerable for a forward year and responsive to changed flows, so it
stays forecast-native.

PJM's ``actual_flow`` sign convention: negative = export from PJM (the all-tie
sum is -40.0 TWh in 2023, matching the EIA-930 +40 TWh net export). Ties to the
TVA/LGEE south-west (net *imports* to PJM) are not part of any registry seam in
the current three-seam PJM build and are reported under "unmapped" for context.

Run from the repo root::

    python scripts/data/derive_interface_limits.py
    python scripts/data/derive_interface_limits.py --check   # assert constants match
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

DATA_DIR = Path("data/raw/iso-specific-transmission")
YEARS = (2023, 2024, 2025)
PCTL = 0.995  # firm-continuous upper envelope (trims top ~0.5% transient hours)

# PJM external tie -> registry seam. Carolinas is the Duke/Progress group the
# registry's DUK-anchored seam represents (border PJM_Dominion). TVA and LGEE are
# the south-west ties PJM net-*imports* over, now their own registry seams; only
# LAGN (measured flow ~0) remains unmapped.
SEAM_TIES: dict[str, list[str]] = {
    "MISO": [
        "ALTE",
        "ALTW",
        "AMIL",
        "CWLP",
        "IPL",
        "MEC",
        "MECS",
        "NIPS",
        "SIGE",
        "WEC",
        "MDU",
        "CIN",
    ],
    "NYISO": ["NYIS", "HUDS", "NEPT", "LIND"],
    "Carolinas": ["CPLE", "CPLW", "DUK"],
    "TVA": ["TVA"],
    "LGEE": ["LGEE"],
}
# LAGN's measured flow is ~0; it remains unmapped.
UNMAPPED = ["LAGN"]

# The committed INTERFACE_NEIGHBORS["PJM"] limits this script derives, rounded
# to the nearest 100 MW. Kept here so --check can assert the constants table
# still matches the published flows after a Data Miner refresh.
COMMITTED_MW: dict[str, float] = {
    "MISO": 7300.0,
    "NYISO": 3900.0,
    "Carolinas": 2400.0,
    "TVA": 1600.0,
    "LGEE": 1100.0,
}


def _seam_flow() -> pd.DataFrame:
    """Return pooled hourly simultaneous seam flow (MW), one column per seam."""
    tie_to_seam = {t: s for s, ts in SEAM_TIES.items() for t in ts}
    frames = []
    for year in YEARS:
        path = DATA_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
        if not path.exists():
            continue
        df = pd.read_csv(
            path, usecols=["datetime_beginning_utc", "tie_line", "actual_flow"]
        )
        df["seam"] = df["tie_line"].map(tie_to_seam)
        df["year"] = year
        frames.append(df)
    if not frames:
        raise SystemExit(f"no PJM interchange CSVs found under {DATA_DIR}")
    alldf = pd.concat(frames, ignore_index=True)
    mapped = alldf.dropna(subset=["seam"])
    return mapped.pivot_table(
        index=["year", "datetime_beginning_utc"],
        columns="seam",
        values="actual_flow",
        aggfunc="sum",
    )


def derive() -> dict[str, float]:
    piv = _seam_flow()
    limits: dict[str, float] = {}
    print(
        f"PJM Data Miner per-tie actual flow, pooled {YEARS} (export = negative MW):\n"
    )
    print(
        f"{'seam':10s} {'export_max':>10s} {'p99.5|flow|':>11s} "
        f"{'mean':>8s} {'export_hr%':>10s} -> limit_mw"
    )
    for seam in SEAM_TIES:
        x = piv[seam].dropna()
        limit = round(x.abs().quantile(PCTL) / 100.0) * 100.0
        limits[seam] = limit
        print(
            f"{seam:10s} {(-x).clip(lower=0).max():10.0f} "
            f"{x.abs().quantile(PCTL):11.0f} {x.mean():8.0f} "
            f"{100 * (x < 0).mean():10.0f} -> {limit:.0f}"
        )
    return limits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="assert the committed constants match the data",
    )
    args = ap.parse_args()

    limits = derive()

    if args.check:
        bad = {
            s: (limits[s], COMMITTED_MW[s])
            for s in COMMITTED_MW
            if limits[s] != COMMITTED_MW[s]
        }
        if bad:
            raise SystemExit(
                f"interface limits drifted from committed constants: {bad}"
            )
        print("\nOK: derived limits match COMMITTED_MW.")


if __name__ == "__main__":
    main()
