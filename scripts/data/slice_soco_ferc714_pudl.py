#!/usr/bin/env python3
"""Slice SOCO's FERC Form 714 hourly planning-area demand out of PUDL's nightly parquet.

Reproduces, as a committed instrument, the slice lane SOCO-11 took by hand for
``data/raw/zone-specific-demand/SOCO/soco_ferc714_hourly_planning_area_demand_2023-2025.parquet``
(``docs/handoffs/FINDING-soco-11-2026-09-13.md`` §3; provenance
``data/raw/zone-specific-demand/SOCO/SOURCES.md``), so any further window —
the 2019-2022 backcast years first (I-SOCO, 2026-09-24) — is the same
construction and not a second hand-rolled one.

Construction (the source's own values; nothing added, nothing modified):

* PUDL ``out_ferc714__hourly_planning_area_demand`` rows for the eight
  respondents SOCO-11 carried (:data:`RESPONDENTS`), ``datetime_utc`` inside
  ``[<first>-01-01T00, <last>-12-31T23]`` UTC;
* ``respondent_name_ferc714`` and ``eia_code`` joined from
  ``core_ferc714__respondent_id``;
* the eight committed columns in the committed order and dtypes
  (categoricals for the two string families, ``Int64`` ids), sorted by
  ``(datetime_utc, respondent_id_ferc714)``.

FERC's own bulk host 403s this egress (SOCO-11 blocked table); PUDL is the
committed route. No key, no registration.

Usage::

    python scripts/data/slice_soco_ferc714_pudl.py --pudl-dir <dir with the two parquets> \
        --first-year 2019 --last-year 2022
    python scripts/data/slice_soco_ferc714_pudl.py --pudl-dir <dir> --first-year 2023 \
        --last-year 2025 --check   # prove the committed slice regenerates
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ZONE_DEMAND_DIR  # noqa: E402

PUDL_BASE = "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly"
DEMAND_TABLE = "out_ferc714__hourly_planning_area_demand.parquet"
RESPONDENT_TABLE = "core_ferc714__respondent_id.parquet"

# The eight FERC-714 respondents SOCO-11 landed (SOURCES.md "The eight
# respondents"): the three Southern operating companies, Southern Power,
# Oglethorpe, MEAG, and the two own-BA falsifiers PowerSouth and Tallahassee.
RESPONDENTS: tuple[int, ...] = (1, 2, 34, 107, 183, 184, 186, 210)

COLUMNS: tuple[str, ...] = (
    "datetime_utc",
    "respondent_id_ferc714",
    "respondent_name_ferc714",
    "eia_code",
    "timezone",
    "demand_reported_mwh",
    "demand_imputed_pudl_mwh",
    "demand_imputed_pudl_mwh_imputation_code",
)
_CATEGORICAL = (
    "respondent_name_ferc714",
    "timezone",
    "demand_imputed_pudl_mwh_imputation_code",
)


def out_path(first_year: int, last_year: int) -> Path:
    """Committed path for a ``[first_year, last_year]`` slice."""
    return (
        ZONE_DEMAND_DIR
        / "SOCO"
        / f"soco_ferc714_hourly_planning_area_demand_{first_year}-{last_year}.parquet"
    )


def build_slice(pudl_dir: Path, first_year: int, last_year: int) -> pd.DataFrame:
    """Return the SOCO respondents' hourly demand for the UTC window, committed layout."""
    dem = pd.read_parquet(
        pudl_dir / DEMAND_TABLE,
        columns=[
            "respondent_id_ferc714",
            "datetime_utc",
            "timezone",
            "demand_reported_mwh",
            "demand_imputed_pudl_mwh",
            "demand_imputed_pudl_mwh_imputation_code",
        ],
        filters=[("respondent_id_ferc714", "in", list(RESPONDENTS))],
    )
    lo = pd.Timestamp(f"{first_year}-01-01 00:00:00")
    hi = pd.Timestamp(f"{last_year}-12-31 23:00:00")
    dem = dem[(dem["datetime_utc"] >= lo) & (dem["datetime_utc"] <= hi)]
    rid = pd.read_parquet(pudl_dir / RESPONDENT_TABLE)[
        ["respondent_id_ferc714", "respondent_name_ferc714", "eia_code"]
    ]
    df = dem.merge(rid, on="respondent_id_ferc714", how="left", validate="many_to_one")
    df = df[list(COLUMNS)].sort_values(["datetime_utc", "respondent_id_ferc714"])
    df["datetime_utc"] = df["datetime_utc"].astype("datetime64[us]")
    df["respondent_id_ferc714"] = df["respondent_id_ferc714"].astype("Int64")
    df["eia_code"] = df["eia_code"].astype("Int64")
    for col in _CATEGORICAL:
        df[col] = df[col].astype(str).where(df[col].notna()).astype("category")
    return df.reset_index(drop=True)


def _values_equal(a: pd.DataFrame, b: pd.DataFrame) -> pd.Series:
    """Per-column count of cells that differ (NaN == NaN), rows keyed on (utc, respondent)."""
    key = ["datetime_utc", "respondent_id_ferc714"]
    m = a.merge(b, on=key, how="outer", suffixes=("_a", "_b"), indicator=True)
    out = {
        "rows_only_committed": int((m["_merge"] == "left_only").sum()),
        "rows_only_regenerated": int((m["_merge"] == "right_only").sum()),
    }
    both = m[m["_merge"] == "both"]
    for col in COLUMNS:
        if col in key:
            continue
        x = both[f"{col}_a"].astype(object)
        y = both[f"{col}_b"].astype(object)
        same = (x == y) | (x.isna() & y.isna())
        out[col] = int((~same).sum())
    return pd.Series(out)


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--pudl-dir",
        type=Path,
        required=True,
        help=f"directory holding {DEMAND_TABLE} and {RESPONDENT_TABLE} "
        f"(fetched from {PUDL_BASE}/)",
    )
    ap.add_argument("--first-year", type=int, required=True)
    ap.add_argument("--last-year", type=int, required=True)
    ap.add_argument(
        "--check",
        action="store_true",
        help="compare against the committed slice instead of writing",
    )
    a = ap.parse_args()
    df = build_slice(a.pudl_dir, a.first_year, a.last_year)
    path = out_path(a.first_year, a.last_year)
    if a.check:
        diff = _values_equal(pd.read_parquet(path), df)
        print(diff.to_string())
        sys.exit(0 if int(diff.sum()) == 0 else 1)
    df.to_parquet(path, index=False)
    print(
        f"wrote {path.relative_to(REPO)}: {len(df):,} rows, "
        f"{df['datetime_utc'].min()} .. {df['datetime_utc'].max()}"
    )
    print(df.groupby("respondent_id_ferc714", observed=True).size().to_string())


if __name__ == "__main__":
    main()
