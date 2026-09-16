#!/usr/bin/env python3
"""Curate the ``coal-receipts`` clean datatype.

Reads ONLY ``data/raw/coal-receipts/coal_receipts_<year>.csv`` (the coal subset
of EIA-923 "Page 5 Fuel Receipts and Costs" — see
``scripts/data/fetch_eia923_coal_receipts.py``) and writes one schema-validated
Parquet per year through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

A raw Page 5 row is one receipt LOT — one (plant, month, rank, purchase type,
mine, supplier, transport mode) delivery — so the sheet carries no unique key.
This script sums lots onto the schema's declared key
``(plant_id, energy_source, year, month, purchase_type,
primary_transportation_mode)``: a sum of physically identical tons, with the
heat content and delivered cost carried as QUANTITY-WEIGHTED means over the lots
summed. Nothing a fuel budget reads is lost — purchase type survives so a
contracted-tonnage-only delivery rate stays constructible, and transport mode
survives so a rail/logistics construction does too.

National grain by design: the burning ISO is resolved at read time from the
plant registry (:mod:`market_sim.data.coal_receipts`), never partitioned here,
so one curation serves every coal ISO without a per-ISO branch (rule 25
``[R-ISO-SCOPE]``).

Idempotent and re-runnable: everything derives from raw and the clean output is
overwritten in place.

Usage:
    python scripts/data/curate_coal_receipts.py
    python scripts/data/curate_coal_receipts.py --years 2020 2021 2022
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

_DATATYPE = "coal-receipts"

#: EIA files a synthetic plant, id 999999 "State-Fuel Level Increment", holding
#: its IMPUTED residual for plants below the reporting threshold. It is not a
#: plant and it is excluded here for the same reason ``curate_coal_stocks.py``
#: excludes it: this datatype's grain is a real plant the fleet can join to, and
#: a state residual summed in would be deliveries to no modelled unit.
_SYNTHETIC_PLANT_ID_FLOOR = 999000

#: Sentinel for a blank transport mode. The column is a KEY column, so it cannot
#: be null; EIA leaves it blank on a minority of lots (self-produced /
#: on-site coal, and some older vintages). "UNK" keeps those tons in the total
#: instead of dropping a real delivery for a missing provenance field.
_UNKNOWN_MODE = "UNK"

#: Raw column -> clean column. Present in every published vintage; a missing one
#: is a hard error rather than a silently-null column.
_PASSTHROUGH: dict[str, str] = {
    "Plant Id": "plant_id",
    "ENERGY_SOURCE": "energy_source",
    "YEAR": "year",
    "MONTH": "month",
    "Purchase Type": "purchase_type",
    "Primary Transportation Mode": "primary_transportation_mode",
    "QUANTITY": "quantity_tons",
    "Average Heat Content": "heat_content_mmbtu_per_ton",
    "FUEL_COST": "fuel_cost_cents_per_mmbtu",
    "Plant Name": "plant_name",
    "Plant State": "plant_state",
}

#: Columns EIA added part-way through the published record. Nullable in the
#: schema and provenance-only (ISO membership comes from the plant registry), so
#: an older vintage curates cleanly with the column left null.
_OPTIONAL_PASSTHROUGH: dict[str, str] = {
    "Balancing Authority Code": "balancing_authority_code",
}

_KEY = [
    "plant_id",
    "energy_source",
    "year",
    "month",
    "purchase_type",
    "primary_transportation_mode",
]


def raw_dir(raw_root: Path | None = None) -> Path:
    """Return the ``coal-receipts`` raw directory under ``raw_root``."""
    return (raw_root or paths.RAW_DATA_DIR) / "coal-receipts"


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _numeric(series: pd.Series) -> pd.Series:
    """Coerce an EIA numeric column to float, treating '.'/'W'/'' as absent.

    EIA writes withheld or not-applicable cells as ``.`` or ``W``. Neither is a
    zero, and neither may be read as one: a withheld delivered cost is not a
    free delivery and a withheld tonnage is not an absent one, so both become
    NaN. A row with no ``QUANTITY`` is dropped; a row with no heat content or
    cost is kept with those fields null, because its TONS are still real.
    """
    return pd.to_numeric(
        series.astype("string").str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """Quantity-weighted mean of ``values``, ignoring rows with no value.

    Returns NaN when every contributing lot withheld the value or the
    contributing weight is zero — never 0.0, which would read as a real
    measurement of zero heat content or zero cost.
    """
    mask = values.notna() & weights.notna()
    if not mask.any():
        return float("nan")
    w = weights[mask].astype(float)
    v = values[mask].astype(float)
    total = float(w.sum())
    if total <= 0.0:
        # All-zero-tonnage lots still carry a real reported heat content; fall
        # back to the unweighted mean rather than dividing by zero.
        return float(v.mean())
    return float((v * w).sum() / total)


def _tidy_year(path: Path, year: int) -> pd.DataFrame:
    """Aggregate one raw year CSV of receipt lots onto the schema's grain."""
    raw = pd.read_csv(path, dtype="string")
    raw.columns = [" ".join(str(c).split()) for c in raw.columns]

    missing = [c for c in _PASSTHROUGH if c not in raw.columns]
    if missing:
        raise ValueError(f"{path.name}: missing expected column(s) {missing}")

    df = raw[list(_PASSTHROUGH)].rename(columns=_PASSTHROUGH)
    for src, dst in _OPTIONAL_PASSTHROUGH.items():
        df[dst] = raw[src] if src in raw.columns else pd.NA

    for col in (
        "quantity_tons",
        "heat_content_mmbtu_per_ton",
        "fuel_cost_cents_per_mmbtu",
    ):
        df[col] = _numeric(df[col])
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    # The sheet stamps YEAR/MONTH on every row; trust the file's own year over
    # a stray row so a mis-stamped record cannot land in the wrong partition.
    df["month"] = pd.to_numeric(df["month"], errors="coerce")
    df["year"] = year

    for col in (
        "energy_source",
        "purchase_type",
        "primary_transportation_mode",
        "plant_name",
        "plant_state",
        "balancing_authority_code",
    ):
        df[col] = df[col].astype("string").str.strip()
    df["primary_transportation_mode"] = (
        df["primary_transportation_mode"].replace("", pd.NA).fillna(_UNKNOWN_MODE)
    )

    df = df.dropna(subset=["plant_id", "energy_source", "month", "quantity_tons"])
    df = df[df["plant_id"] < _SYNTHETIC_PLANT_ID_FLOOR]
    df = df[df["purchase_type"].notna() & (df["purchase_type"] != "")]
    df["plant_id"] = df["plant_id"].astype("int64")
    df["month"] = df["month"].astype("int64")
    df["year"] = df["year"].astype("int64")

    grouped = df.groupby(_KEY, as_index=False, dropna=False).apply(
        lambda g: pd.Series(
            {
                "quantity_tons": float(g["quantity_tons"].sum()),
                "heat_content_mmbtu_per_ton": _weighted_mean(
                    g["heat_content_mmbtu_per_ton"], g["quantity_tons"]
                ),
                "fuel_cost_cents_per_mmbtu": _weighted_mean(
                    g["fuel_cost_cents_per_mmbtu"], g["quantity_tons"]
                ),
                "plant_name": g["plant_name"].iloc[0],
                "plant_state": g["plant_state"].iloc[0],
                "balancing_authority_code": g["balancing_authority_code"].iloc[0],
            }
        ),
        include_groups=False,
    )
    out = grouped.reset_index(drop=True)
    out["quantity_tons"] = out["quantity_tons"].astype("float64")
    for col in ("heat_content_mmbtu_per_ton", "fuel_cost_cents_per_mmbtu"):
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out["heat_content_mmbtu_per_ton"] = out["heat_content_mmbtu_per_ton"].replace(
        [np.inf, -np.inf], np.nan
    )
    for col in (
        "energy_source",
        "purchase_type",
        "primary_transportation_mode",
        "plant_name",
        "plant_state",
        "balancing_authority_code",
    ):
        out[col] = out[col].astype("string")
    for col in ("plant_id", "year", "month"):
        out[col] = out[col].astype("int64")

    dupes = int(out.duplicated(subset=_KEY).sum())
    if dupes:  # pragma: no cover - the groupby makes the key unique by design
        raise ValueError(f"{path.name}: {dupes} duplicate key rows after aggregation")
    return out.sort_values(_KEY).reset_index(drop=True)


def curate(raw_root: Path | None = None, years: list[int] | None = None) -> list[Path]:
    """Curate each available raw year; return the written clean paths."""
    rdir = raw_dir(raw_root)
    if not rdir.is_dir():
        raise FileNotFoundError(
            f"{_repo_rel(rdir)} not found — run "
            "scripts/data/fetch_eia923_coal_receipts.py first"
        )
    written: list[Path] = []
    for csv_path in sorted(rdir.glob("coal_receipts_*.csv")):
        year = int(csv_path.stem.rsplit("_", 1)[1])
        if years and year not in years:
            continue
        df = _tidy_year(csv_path, year)
        out = write_clean(
            df,
            _DATATYPE,
            year=year,
            source=f"EIA-923 Page 5 Fuel Receipts and Costs via {_repo_rel(csv_path)}",
        )
        validate_clean(out)
        print(
            f"  {year}: {len(df):>6} rows, {df.plant_id.nunique():>4} plants, "
            f"{df.quantity_tons.sum() / 1e6:>7.2f} Mt -> {_repo_rel(out)}"
        )
        written.append(out)
    if not written:
        raise FileNotFoundError(f"no coal_receipts_*.csv under {_repo_rel(rdir)}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=None)
    args = ap.parse_args()
    curate(years=args.years)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
