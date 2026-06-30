"""Compare two sets of dispatch result Parquet files for numeric regression.

Loads all ``year_*.parquet`` files from two result directories and compares
every numeric column with configurable tolerances. Reports PASS/FAIL per
column with the maximum deviation observed. Returns exit code 0 when all
columns pass, 1 when any column fails or files are missing.

Usage:
    python scripts/regression_check.py results/baseline results/refactored
    python scripts/regression_check.py --atol 1e-4 --rtol 1e-3 dir_a dir_b

Options:
    --atol   Absolute tolerance for MW quantities (default 1e-6).
    --rtol   Relative tolerance for price columns (default 1e-4).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Columns whose names contain any of these substrings are treated as price
# columns and compared with relative tolerance; everything else uses absolute.
_PRICE_INDICATORS = ("price", "lmp", "cost", "shadow", "dual", "rec_price")


def _is_price_column(col_name: str) -> bool:
    """Return True if the column should use relative tolerance."""
    lower = col_name.lower()
    return any(tag in lower for tag in _PRICE_INDICATORS)


def _compare_column(
    col: str,
    a: np.ndarray,
    b: np.ndarray,
    atol: float,
    rtol: float,
) -> tuple[bool, float, str]:
    """Compare one numeric column from two DataFrames.

    Returns (passed, max_deviation, metric_label).
    """
    if _is_price_column(col):
        denom = np.maximum(np.abs(a), np.abs(b))
        denom = np.where(denom == 0, 1.0, denom)
        rel_diff = np.abs(a - b) / denom
        max_dev = float(np.nanmax(rel_diff))
        return max_dev <= rtol, max_dev, "rel"
    else:
        abs_diff = np.abs(a - b)
        max_dev = float(np.nanmax(abs_diff))
        return max_dev <= atol, max_dev, "abs"


def compare_parquet(
    path_a: Path,
    path_b: Path,
    atol: float,
    rtol: float,
) -> list[tuple[str, bool, float, str]]:
    """Compare two Parquet files column by column.

    Returns a list of (column_name, passed, max_deviation, metric_label).
    """
    df_a = pd.read_parquet(path_a)
    df_b = pd.read_parquet(path_b)

    results = []
    numeric_cols = [c for c in df_a.columns if pd.api.types.is_numeric_dtype(df_a[c])]

    for col in numeric_cols:
        if col not in df_b.columns:
            results.append((col, False, float("inf"), "missing_in_b"))
            continue
        if not pd.api.types.is_numeric_dtype(df_b[col]):
            results.append((col, False, float("inf"), "type_mismatch"))
            continue

        a_vals = df_a[col].to_numpy(dtype=float)
        b_vals = df_b[col].to_numpy(dtype=float)

        if a_vals.shape != b_vals.shape:
            results.append((col, False, float("inf"), "shape_mismatch"))
            continue

        passed, max_dev, metric = _compare_column(col, a_vals, b_vals, atol, rtol)
        results.append((col, passed, max_dev, metric))

    extra_in_b = [
        c
        for c in df_b.columns
        if pd.api.types.is_numeric_dtype(df_b[c]) and c not in df_a.columns
    ]
    for col in extra_in_b:
        results.append((col, False, float("inf"), "missing_in_a"))

    return results


def run_check(dir_a: Path, dir_b: Path, atol: float, rtol: float) -> bool:
    """Compare all year_*.parquet files between two directories.

    Returns True if all comparisons pass.
    """
    files_a = sorted(dir_a.glob("year_*.parquet"))
    files_b = sorted(dir_b.glob("year_*.parquet"))

    names_a = {f.name for f in files_a}
    names_b = {f.name for f in files_b}

    all_passed = True

    missing_in_b = names_a - names_b
    missing_in_a = names_b - names_a

    if missing_in_b:
        for name in sorted(missing_in_b):
            print(f"FAIL  {name}  missing in {dir_b}")
        all_passed = False

    if missing_in_a:
        for name in sorted(missing_in_a):
            print(f"FAIL  {name}  missing in {dir_a}")
        all_passed = False

    common = sorted(names_a & names_b)
    if not common and not missing_in_a and not missing_in_b:
        print(f"FAIL  no year_*.parquet files found in {dir_a}")
        return False

    for name in common:
        results = compare_parquet(dir_a / name, dir_b / name, atol, rtol)
        file_passed = True
        for col, passed, max_dev, metric in results:
            status = "PASS" if passed else "FAIL"
            if not passed:
                file_passed = False
                all_passed = False
            tol_label = f"rtol={rtol}" if metric == "rel" else f"atol={atol}"
            print(
                f"  {status}  {name}:{col}  max_dev={max_dev:.2e} ({metric}, {tol_label})"
            )
        if file_passed:
            n_cols = len(results)
            print(f"  PASS  {name}  all {n_cols} numeric columns within tolerance")

    return all_passed


def main() -> int:
    """Entry point for the regression check script."""
    parser = argparse.ArgumentParser(
        description="Compare two result directories for numeric regression."
    )
    parser.add_argument("dir_a", type=Path, help="Baseline result directory")
    parser.add_argument("dir_b", type=Path, help="New result directory")
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-6,
        help="Absolute tolerance for MW quantities (default: 1e-6)",
    )
    parser.add_argument(
        "--rtol",
        type=float,
        default=1e-4,
        help="Relative tolerance for prices (default: 1e-4)",
    )
    args = parser.parse_args()

    if not args.dir_a.is_dir():
        print(f"ERROR: {args.dir_a} is not a directory")
        return 1
    if not args.dir_b.is_dir():
        print(f"ERROR: {args.dir_b} is not a directory")
        return 1

    passed = run_check(args.dir_a, args.dir_b, args.atol, args.rtol)
    print()
    print("RESULT:", "PASS" if passed else "FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
