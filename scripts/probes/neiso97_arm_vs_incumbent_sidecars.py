"""Measure the neiso-97 DST-repair arm's dispatch against the incumbent's sidecars.

The repaired instrument is a SCORING TARGET, not a NEISO solve input (the
keeper recipe arms no LMP-consuming flag), so the arm's dispatch is predicted
IDENTICAL to the incumbent keeper's — and per the neiso-91 reproducibility
record that prediction is worth measuring, never assuming. Compares the arm
bundle's ``hourly/`` sidecars against the incumbent's committed ones, per
year and pass:

* ``system_<year>.parquet``  — zone-hour price/demand/slack grid;
* ``class_hourly_<year>.parquet`` — per-class dispatch;
* ``reserve_family_<year>.parquet`` — the per-family reserve rows.

Output: ``results/calibration/_neiso97_arm_vs_incumbent_sidecars.json``.
NO YEAR IS SOLVED; this reads two bundles' committed/produced artifacts.

Usage:
    uv run python scripts/probes/neiso97_arm_vs_incumbent_sidecars.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CAL = REPO / "results" / "calibration"
INC = CAL / "neiso93_envelope_A" / "hourly"
ARM = CAL / "neiso97_dstrepair_A" / "hourly"
OUT = REPO / "results" / "calibration" / "_neiso97_arm_vs_incumbent_sidecars.json"

YEARS = (2023, 2024, 2025)


def compare(name: str, year: int) -> dict:
    """Cell-for-cell comparison of one sidecar file across the two bundles."""
    a = pd.read_parquet(INC / f"{name}_{year}.parquet")
    b = pd.read_parquet(ARM / f"{name}_{year}.parquet")
    rec: dict = {"rows": (len(a), len(b)), "identical_grid": False}
    if list(a.columns) != list(b.columns) or len(a) != len(b):
        rec["note"] = "column/row grid differs"
        return rec
    rec["identical_grid"] = True
    num = [c for c in a.columns if np.issubdtype(a[c].dtype, np.number)]
    other = [c for c in a.columns if c not in num]
    rec["nonnumeric_identical"] = all(a[c].equals(b[c]) for c in other)
    diffs = {}
    for c in num:
        x, y = a[c].to_numpy(dtype=float), b[c].to_numpy(dtype=float)
        neq = ~((x == y) | (np.isnan(x) & np.isnan(y)))
        if neq.any():
            diffs[c] = {
                "cells": int(neq.sum()),
                "max_abs_delta": float(np.nanmax(np.abs(x[neq] - y[neq]))),
            }
    rec["numeric_diff_columns"] = diffs
    rec["bit_identical"] = rec["nonnumeric_identical"] and not diffs
    return rec


def main() -> int:
    res: dict = {}
    all_ident = True
    for year in YEARS:
        res[year] = {}
        for name in ("system", "class_hourly", "reserve_family"):
            if not (INC / f"{name}_{year}.parquet").exists():
                res[year][name] = {"note": "incumbent sidecar absent"}
                continue
            rec = compare(name, year)
            res[year][name] = rec
            all_ident = all_ident and rec.get("bit_identical", False)
    res["all_bit_identical"] = all_ident
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({str(y): {n: r.get("bit_identical", r.get("note")) for n, r in res[y].items()} for y in YEARS}, indent=1))
    print("ALL BIT-IDENTICAL:", all_ident)
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
