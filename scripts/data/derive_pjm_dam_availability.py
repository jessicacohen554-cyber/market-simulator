"""Process the raw PJM generation-outage pull into the committed parquet.

Reads the immutable raw Data Miner 2 pull
(``data/raw/pjm-outages/gen_outages_by_type.csv``, written by
``scripts/data/fetch_pjm_outages.py``) and writes the tidy, analysis-ready
parquet ``data/raw/pjm-dam-availability.parquet`` that the backcast consumes
(``market_sim.data.pjm_outages.pjm_dam_availability_series``).

This is the PJM analogue of ``derive_ercot_thermal_dam_availability.py``: PJM's
market-operator-published, DAM-horizon generation-outage forecast is the
capacity-availability measurement that stands in for the statistical
WEFOR/EFOR estimate of the same quantity in a PJM backcast — a CLAUDE.md
rule-13-admissible measured/forecast *input* (it regenerates for a forward day
and responds to conditions), never a fitted answer pinned to actuals.

Output schema (``data/dictionary/schema/pjm-outages.schema.yaml``), one tidy row
per (execution-date, forecast-date, region):

    forecast_execution_date : date the outage forecast was posted (EPT)
    forecast_date           : delivery date the MW pertains to (EPT)
    lead_days               : forecast_date - forecast_execution_date, 0..6
                              (lead_days == 0 is the current-day *actual* outage)
    region                  : "Mid Atlantic - Dominion" | "Western" | "PJM RTO"
                              (RTO == the two sub-regions summed, exactly)
    total_outages_mw        : all active/approved outages
    planned_outages_mw      : scheduled (incl. nuclear refuel + fossil maint.)
    maintenance_outages_mw  : maintenance outages
    forced_outages_mw       : unplanned (forced) outages

Outputs (both written from the same tidy frame):

* ``data/raw/pjm-dam-availability.parquet`` — the efficient columnar artifact
  (all years, one file). This is the "process into parquets" deliverable and the
  fast path the loader prefers when present. It is **gitignored** (not committed)
  because the repo's API-only push path cannot round-trip a binary blob; it
  regenerates deterministically from the committed per-year CSVs (or the raw
  pull) below.
* ``data/raw/pjm-outages/by-year/gen_outages_by_type_<YEAR>.csv`` — the
  **committed**, portable per-year CSVs the loader falls back to on a fresh
  clone. To keep the in-repo copy small and text-diffable (and pushable over the
  API-only path), these carry only the **current-day actual** rows
  (``lead_days == 0``) — the slice the backcast overlay consumes — for all three
  regions and all four MW columns. The forward six-day horizon (``lead_days``
  1..6) is dropped from the committed copy but retained in the parquet and
  re-fetchable from the raw pull. Identical tidy schema otherwise.

FROZEN AGAINST RESIDUALS (CLAUDE.md rule 23): re-derive only when the raw PJM
source is re-pulled; never because a residual moved.

Usage::

    python scripts/data/derive_pjm_dam_availability.py \
        [--raw data/raw/pjm-outages/gen_outages_by_type.csv] \
        [--out data/raw/pjm-dam-availability.parquet] \
        [--byyear-dir data/raw/pjm-outages/by-year]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DEFAULT_RAW = REPO / "data" / "raw" / "pjm-outages" / "gen_outages_by_type.csv"
DEFAULT_OUT = REPO / "data" / "raw" / "pjm-dam-availability.parquet"
DEFAULT_BYYEAR_DIR = REPO / "data" / "raw" / "pjm-outages" / "by-year"

_MW_COLS = [
    "total_outages_mw",
    "planned_outages_mw",
    "maintenance_outages_mw",
    "forced_outages_mw",
]
_REGIONS = ("Mid Atlantic - Dominion", "Western", "PJM RTO")


def build(raw_path: Path) -> pd.DataFrame:
    """Return the tidy PJM outage frame from the raw Data Miner 2 CSV."""
    return build_from_frame(pd.read_csv(raw_path))


def build_from_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Return the tidy PJM outage frame from a raw-shaped DataFrame.

    Split from :func:`build` so tests can exercise the reshaping / invariant
    checks on an in-memory fixture without a CSV on disk.
    """
    exec_dt = pd.to_datetime(df["forecast_execution_date_ept"]).dt.normalize()
    fc_dt = pd.to_datetime(df["forecast_date"]).dt.normalize()
    out = pd.DataFrame(
        {
            "forecast_execution_date": exec_dt.dt.date.astype("string"),
            "forecast_date": fc_dt.dt.date.astype("string"),
            "lead_days": (fc_dt - exec_dt).dt.days.astype("int64"),
            "region": df["region"].astype("string"),
        }
    )
    for c in _MW_COLS:
        out[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    out = out.sort_values(
        ["forecast_execution_date", "region", "lead_days"]
    ).reset_index(drop=True)
    _sanity(out)
    return out


def _sanity(df: pd.DataFrame) -> None:
    """Assert the structural invariants of the PJM outage feed."""
    bad_region = set(df["region"].unique()) - set(_REGIONS)
    if bad_region:
        raise ValueError(f"unexpected region(s): {bad_region}")
    if df[_MW_COLS].isna().any().any():
        raise ValueError("NaN outage MW after coercion")
    # total / planned / forced are always non-negative; maintenance carries
    # occasional small negatives (104 rows, min -1232 MW) — a PJM reconciliation
    # artifact where MW is reclassified between categories. The published values
    # are preserved verbatim (rule 11: never silently alter measured data); the
    # real integrity invariant is that the three components sum to total, checked
    # below, so any negative in one category is absorbed by the others.
    for c in ("total_outages_mw", "planned_outages_mw", "forced_outages_mw"):
        if (df[c] < 0).any():
            raise ValueError(f"negative {c}")
    resid_sum = (
        df["total_outages_mw"]
        - df["planned_outages_mw"]
        - df["maintenance_outages_mw"]
        - df["forced_outages_mw"]
    ).abs()
    if resid_sum.max() > 1.0:
        raise ValueError(f"components do not sum to total (max {resid_sum.max()})")
    if not df["lead_days"].between(0, 6).all():
        raise ValueError("lead_days outside 0..6")
    # RTO must equal the two sub-regions summed, per delivery (exec, fc) pair.
    piv = df.pivot_table(
        index=["forecast_execution_date", "forecast_date"],
        columns="region",
        values="total_outages_mw",
        aggfunc="first",
    ).dropna()
    resid = (piv["PJM RTO"] - piv["Mid Atlantic - Dominion"] - piv["Western"]).abs()
    if resid.max() > 1.0:
        raise ValueError(f"RTO != sub-region sum (max resid {resid.max()} MW)")


def write_byyear_csvs(df: pd.DataFrame, byyear_dir: Path) -> list[Path]:
    """Write one tidy CSV per execution-date year; return the paths written.

    These are the committed, portable per-year copies (the parquet is
    gitignored). Only the current-day actual rows (``lead_days == 0``) are
    written — the slice the backcast overlay consumes — to keep each file small
    and API-pushable; the full forward horizon stays in the parquet.
    Deterministic: rows are already sorted by build_from_frame, so re-running is
    byte-idempotent.
    """
    byyear_dir.mkdir(parents=True, exist_ok=True)
    lead0 = df[df["lead_days"] == 0]
    years = pd.to_datetime(lead0["forecast_execution_date"]).dt.year
    written: list[Path] = []
    for yr in sorted(years.unique()):
        path = byyear_dir / f"gen_outages_by_type_{int(yr)}.csv"
        lead0.loc[years == yr].to_csv(path, index=False)
        written.append(path)
    return written


def main() -> None:
    """CLI entry point: build the tidy frame; write the parquet + per-year CSVs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--byyear-dir", type=Path, default=DEFAULT_BYYEAR_DIR)
    args = ap.parse_args()

    df = build(args.raw)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)
    paths = write_byyear_csvs(df, args.byyear_dir)
    n0 = int((df["lead_days"] == 0).sum())
    yrs = pd.to_datetime(df["forecast_execution_date"]).dt.year
    print(
        f"wrote {len(df):,} rows ({n0:,} current-day actuals) "
        f"[{yrs.min()}..{yrs.max()}] -> {args.out}\n"
        f"wrote {len(paths)} per-year CSV(s) -> {args.byyear_dir}"
    )


if __name__ == "__main__":
    main()
