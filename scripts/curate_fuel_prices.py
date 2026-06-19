#!/usr/bin/env python3
"""Curate the ``fuel-prices`` clean datatype from ``data/raw/gas-prices``.

Reconciles the raw fuel-price benchmark downloads onto the canonical
``fuel-prices`` schema (``data/dictionary/schema/fuel-prices.schema.yaml``):
each benchmark's per-file price column becomes ``price_usd_per_mmbtu``, with the
``fuel`` and ``hub`` keys distinguishing the series, and a daily price *date*
becoming ``interval_start_utc`` at 00:00 UTC (tz-aware) plus a tz-naive
``interval_start_local`` wall-clock of the same date.

Every output is written through the shared, frozen
:func:`scripts.lib.clean_io.write_clean` seam and round-trip checked with
:func:`scripts.lib.clean_io.validate_clean`. The script reads only ``data/raw``
and is idempotent: re-running rebuilds the same clean Parquet from the same raw.

Partitioning
------------
Fuel prices are national hub benchmarks (no ISO partition), so this writes a
**single combined file** — ``data/clean/fuel-prices/fuel-prices.parquet`` —
holding every ``(fuel, hub)`` series rather than one file per fuel. With a
single fuel present today the distinction is moot; a combined file keeps the
whole cross-hub series queryable in one read and matches the schema's
``(fuel, hub, interval_start_utc)`` key.

Sources reconciled
------------------
Of the files under ``data/raw/gas-prices`` only the Henry Hub **daily** spot
series is an absolute delivered price in $/MMBtu, so it is the only benchmark
curated today:

  * ``henry_hub_daily.csv`` (date, price_usd_mmbtu) -> fuel=gas, hub=henry_hub

The citygate / basis / coal / oil benchmarks anticipated by the schema are not
yet present in ``data/raw/gas-prices``; when they land, add a row to
:data:`BENCHMARKS` and they flow through unchanged. ``henry_hub_monthly.csv`` is
deliberately *excluded*: it is the monthly mean of the same (gas, henry_hub)
daily series (see ``scripts/fetch_eia_gas_prices.py``), so folding it in would
duplicate the ``(fuel, hub, interval_start_utc)`` key on first-of-month dates —
the closed schema has no frequency dimension to separate daily from monthly.

Alignment with ``scripts/fetch_eia_gas_prices.py``
-------------------------------------------------
That fetcher writes ``henry_hub_daily.csv`` directly from EIA series RNGWHHD as
``(date, price_usd_mmbtu)`` with the value rounded to 4 decimals. This curation
carries that exact price column verbatim into ``price_usd_per_mmbtu`` (a rename,
no transform), so the curated value equals the raw/fetched value to the file's
full precision; the only added columns are the derived ``interval_start_utc`` /
``interval_start_local`` from the ``date`` and the constant ``fuel`` / ``hub``.

Usage:
    python scripts/curate_fuel_prices.py
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

# Allow ``python scripts/curate_fuel_prices.py`` (run as a file, not ``-m``):
# put the repo root on sys.path so the ``scripts`` package imports below resolve.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

DATATYPE = "fuel-prices"


@dataclass(frozen=True)
class Benchmark:
    """One raw benchmark file and how it maps onto the canonical schema."""

    filename: str          # file under data/raw/gas-prices
    fuel: str              # canonical fuel key (gas, coal, oil)
    hub: str               # canonical hub / region key
    price_col: str         # the per-file price column (in $/MMBtu)
    date_col: str = "date"  # the per-file daily price-date column


# Benchmarks curated today. Add a row when a new absolute-$/MMBtu benchmark
# (citygate / coal / oil) lands under data/raw/gas-prices — no other change is
# needed. henry_hub_monthly.csv is intentionally absent (see module docstring).
BENCHMARKS: tuple[Benchmark, ...] = (
    Benchmark(
        filename="henry_hub_daily.csv",
        fuel="gas",
        hub="henry_hub",
        price_col="price_usd_mmbtu",
    ),
)


def _repo_rel(path: Path) -> str:
    """Provenance string: path relative to the repo root when it lives under it."""
    try:
        return str(path.resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def reconcile_benchmark(path: Path, bench: Benchmark) -> pd.DataFrame:
    """Read one daily benchmark CSV and reconcile it onto the canonical columns.

    ``date`` -> ``interval_start_utc`` (00:00 UTC, tz-aware) + tz-naive
    ``interval_start_local`` wall-clock of the same date; the per-file price
    column -> ``price_usd_per_mmbtu``; ``fuel`` / ``hub`` set per ``bench``.
    """
    raw = pd.read_csv(path)
    missing = {bench.date_col, bench.price_col} - set(raw.columns)
    if missing:
        raise ValueError(
            f"{path}: missing expected column(s) {sorted(missing)}; "
            f"found {list(raw.columns)}"
        )

    local = pd.to_datetime(raw[bench.date_col])            # tz-naive wall-clock
    out = pd.DataFrame(
        {
            "interval_start_utc": local.dt.tz_localize("UTC"),
            "interval_start_local": local,
            "fuel": pd.array([bench.fuel] * len(raw), dtype="string"),
            "hub": pd.array([bench.hub] * len(raw), dtype="string"),
            "price_usd_per_mmbtu": raw[bench.price_col].astype("float64"),
        }
    )
    return out


def build_clean(gas_dir: Path) -> pd.DataFrame:
    """Reconcile every present benchmark under ``gas_dir`` into one frame.

    Returns the combined, de-duplicated, key-sorted frame. Benchmark files that
    are not present are skipped (the registry is forward-looking).
    """
    frames: list[pd.DataFrame] = []
    for bench in BENCHMARKS:
        path = gas_dir / bench.filename
        if not path.is_file():
            continue
        frames.append(reconcile_benchmark(path, bench))

    if not frames:
        raise FileNotFoundError(
            f"no curatable fuel-price benchmarks found under {gas_dir} "
            f"(expected one of: {[b.filename for b in BENCHMARKS]})"
        )

    df = pd.concat(frames, ignore_index=True)
    key = ["fuel", "hub", "interval_start_utc"]
    df = (
        df.drop_duplicates(subset=key, keep="last")
        .sort_values(key)
        .reset_index(drop=True)
    )
    return df


def curate(gas_dir: Path | None = None) -> Path:
    """Curate fuel prices from ``gas_dir`` into the clean tree; return the path.

    Writes a single combined Parquet through :func:`write_clean` and asserts it
    round-trips via :func:`validate_clean`. ``gas_dir`` defaults to the real
    ``data/raw/gas-prices``; tests pass a synthetic directory.
    """
    gas_dir = gas_dir or paths.GAS_PRICES_DIR
    df = build_clean(gas_dir)

    sources = ", ".join(
        _repo_rel(gas_dir / b.filename)
        for b in BENCHMARKS
        if (gas_dir / b.filename).is_file()
    )
    out = write_clean(df, DATATYPE, source=sources)
    validate_clean(out)
    return out


def main() -> None:
    out = curate()
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
