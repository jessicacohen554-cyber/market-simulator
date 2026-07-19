"""Curate the ``validation`` clean datatype from ``data/raw/_validation-source``.

STATUS: PARKED (curated, not yet consumed) — 2026-07-19.
    This datatype is *written* here and round-trips through the schema/clean
    contract, but a repo-wide scan finds **no reader**: nothing calls
    ``read_clean("validation")`` on any solve, scoring, or reporting path (the
    scorer still reads the legacy ``calibration_reference.json`` that
    ``build_calibration_reference.py`` emits, via
    ``run_calibration.py::_load_reference``). It is deliberately kept as the
    curated, schema-validated *replacement* for that JSON reference (see below),
    staged for the migration but not wired in.

    The tee'd-up next step (owner's pick) is to teach
    ``run_calibration.py::_load_reference`` to reconstruct the reference dict
    from ``read_clean("validation")`` behind a **default-off** flag, gated by a
    parity test asserting the reconstructed reference equals the current JSON
    output byte-for-byte (the docstring below notes the two are "byte-aligned
    with the builder by construction"). Until that flip lands, treat this script
    as a data-contract fixture, not a live input.

The backcast calibrates against a heterogeneous pile of reference benchmarks —
EIA-860 renewable capacity, EIA-923 by-fuel net generation, EPA eGRID 2023
emissions, EIA-930 demand totals, the measured Henry Hub gas price, and the
historical day-ahead LMP. This script reconciles all of them into the single
tidy long form the ``validation`` schema declares::

    (iso, zone, year, month, fuel) -> metric, value, unit, source

so one contract covers every benchmark. Conventions: ``month=0`` for annual
(non-monthly) targets, ``zone="SYSTEM"`` for ISO-wide totals, ``fuel="ALL"``
when a metric is not fuel-specific. The ``source`` column carries the publisher;
the raw input path(s) are embedded as parquet provenance via ``write_clean``.

This is the curated replacement for ``scripts/data/build_calibration_reference.py``
output (``calibration_reference.json`` + the per-year ``*_renewable_capacity``
CSVs). Rather than re-deriving from EIA-860/923/930 + the eGRID workbook (which
``build_calibration_reference`` does), this script reads only the already
materialised raw artefacts under ``data/raw/_validation-source`` and reshapes
them, so the numbers stay byte-aligned with the builder by construction.

Reconciled benchmarks (one metric each, no key collisions):

* ``capacity_mw``               EIA-860 operable renewable capacity, per
                                zone/month/fuel  (from the renewable_capacity CSVs)
* ``generation_mwh``            EIA-923 by-fuel net generation, annual SYSTEM total
* ``co2_kg``                    EPA eGRID 2023 by-fuel CO2, annual SYSTEM total
* ``demand_mwh`` / ``peak_demand_mw`` / ``min_demand_mw`` / ``avg_demand_mw``
                                EIA-930 demand totals, annual SYSTEM (fuel=ALL)
* ``henry_hub_usd_per_mmbtu``   measured Henry Hub gas spot price, annual (fuel=gas)
* ``avg_price_usd_per_mwh``     historical day-ahead LMP, annual + monthly SYSTEM

Writes are partitioned by ``iso`` + ``year`` (one parquet per ISO-year), which
mirrors the per-ISO-year structure of every raw source.

Run: ``python scripts/data/curate_validation.py``
"""

from __future__ import annotations

import json
import logging
import math
import re
from pathlib import Path

import pandas as pd

from scripts.lib.clean_io import paths, validate_clean, write_clean

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("curate_validation")

# Default raw source directory (overridable so tests can point at a fixture).
DEFAULT_RAW_DIR: Path = paths.DATA_ROOT / "data" / "raw" / "_validation-source"

CALIBRATION_REFERENCE_JSON = "calibration_reference.json"
ACTUAL_LMP_JSON = "actual_lmp.json"
_RENEWABLE_CSV_RE = re.compile(
    r"^(?P<iso>[A-Z]+)_(?P<year>\d{4})_renewable_capacity\.csv$"
)

# Unit conversions. EIA-923/eGRID report TWh and metric "Mt" (million tonnes);
# the schema standardises on MWh and kg.
_TWH_TO_MWH: float = 1.0e6
_MT_TO_KG: float = 1.0e9  # 1 Mt = 1e6 tonnes * 1e3 kg

# Publisher labels for the `source` column (provenance of each benchmark).
_SRC_CAPACITY = "EIA-860"
_SRC_GENERATION = "EIA-923"
# An incomplete current-year EIA-923 vintage has its variable renewables sourced
# from EIA-930 grid telemetry by the upstream builder (see build_calibration_reference).
_SRC_GENERATION_PARTIAL = "EIA-923/930"
_SRC_EMISSIONS = "EPA eGRID 2023"
_SRC_DEMAND = "EIA-930"
_SRC_HENRY_HUB = "EIA Henry Hub"

# EIA-930 demand block field -> (metric, unit). total_twh is the TWh echo of
# total_mwh and is dropped (the schema keeps energy in MWh).
_DEMAND_METRICS: dict[str, tuple[str, str]] = {
    "total_mwh": ("demand_mwh", "mwh"),
    "peak_mw": ("peak_demand_mw", "mw"),
    "min_mw": ("min_demand_mw", "mw"),
    "avg_mw": ("avg_demand_mw", "mw"),
}

_SYSTEM = "SYSTEM"
_ALL = "ALL"

_COLUMNS = ["iso", "zone", "year", "month", "fuel", "metric", "value", "unit", "source"]


def _row(iso, zone, year, month, fuel, metric, value, unit, source) -> dict:
    """Build one tidy long-form row."""
    return {
        "iso": iso,
        "zone": zone,
        "year": int(year),
        "month": int(month),
        "fuel": fuel,
        "metric": metric,
        "value": float(value),
        "unit": unit,
        "source": source,
    }


def _is_missing(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def _relpath(p: Path) -> str:
    """Path relative to the repo root when possible (for readable provenance)."""
    try:
        return str(p.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(p)


def _capacity_rows(csv_path: Path) -> list[dict]:
    """capacity_mw rows from a per-ISO-year renewable_capacity CSV (EIA-860)."""
    df = pd.read_csv(csv_path)
    rows: list[dict] = []
    for r in df.itertuples(index=False):
        rows.append(
            _row(
                r.iso,
                r.zone,
                r.year,
                r.month,
                r.fuel,
                "capacity_mw",
                r.capacity_mw,
                "mw",
                _SRC_CAPACITY,
            )
        )
    return rows


def _generation_rows(iso: str, year: int, block: dict) -> list[dict]:
    """generation_mwh rows (EIA-923 by-fuel annual SYSTEM total)."""
    gen = block.get("generation_twh") or {}
    src = _SRC_GENERATION_PARTIAL if block.get("eia923_incomplete") else _SRC_GENERATION
    return [
        _row(
            iso, _SYSTEM, year, 0, fuel, "generation_mwh", twh * _TWH_TO_MWH, "mwh", src
        )
        for fuel, twh in sorted(gen.items())
    ]


def _emissions_rows(iso: str, year: int, egrid: dict) -> list[dict]:
    """co2_kg rows (EPA eGRID by-fuel annual SYSTEM total) for the benchmark year."""
    if int(egrid.get("benchmark_year", -1)) != int(year):
        return []
    co2_mt = egrid.get("co2_mt") or {}
    return [
        _row(
            iso, _SYSTEM, year, 0, fuel, "co2_kg", mt * _MT_TO_KG, "kg", _SRC_EMISSIONS
        )
        for fuel, mt in sorted(co2_mt.items())
    ]


def _demand_rows(iso: str, year: int, block: dict) -> list[dict]:
    """EIA-930 demand totals (fuel=ALL, SYSTEM, annual)."""
    demand = block.get("demand") or {}
    rows: list[dict] = []
    for field, (metric, unit) in _DEMAND_METRICS.items():
        if field in demand and not _is_missing(demand[field]):
            rows.append(
                _row(
                    iso,
                    _SYSTEM,
                    year,
                    0,
                    _ALL,
                    metric,
                    demand[field],
                    unit,
                    _SRC_DEMAND,
                )
            )
    return rows


def _henry_hub_rows(iso: str, year: int, block: dict) -> list[dict]:
    """Measured Henry Hub gas spot price (annual, fuel=gas)."""
    hh = block.get("henry_hub_actual")
    if _is_missing(hh):
        return []
    return [
        _row(
            iso,
            _SYSTEM,
            year,
            0,
            "gas",
            "henry_hub_usd_per_mmbtu",
            hh,
            "usd_per_mmbtu",
            _SRC_HENRY_HUB,
        )
    ]


def _price_rows(iso: str, year: int, lmp_block: dict) -> list[dict]:
    """avg_price_usd_per_mwh rows from the historical day-ahead LMP benchmark.

    Annual mean (``da``) at month=0 plus the monthly means (``da_mon``) — for
    the SYSTEM row and, when the ISO's block carries the per-model-zone
    ``zones`` sub-dict (NYISO/NEISO constituent-zone means; MISO named-hub
    means per scope decision D6, whose ``zones_src`` documents the
    MISO-Plains hub proxy), one row set per zone. Some ISO-years carry only
    real-time prices (no ``da``); those contribute nothing.
    """
    src = lmp_block.get("src", "actual LMP")
    zone_src = lmp_block.get("zones_src", src)
    rows: list[dict] = []

    def _emit(zone: str, block: dict, source: str) -> None:
        da = block.get("da")
        if not _is_missing(da):
            rows.append(
                _row(
                    iso,
                    zone,
                    year,
                    0,
                    _ALL,
                    "avg_price_usd_per_mwh",
                    da,
                    "usd_per_mwh",
                    source,
                )
            )
        for i, v in enumerate(block.get("da_mon") or [], start=1):
            if not _is_missing(v):
                rows.append(
                    _row(
                        iso,
                        zone,
                        year,
                        i,
                        _ALL,
                        "avg_price_usd_per_mwh",
                        v,
                        "usd_per_mwh",
                        source,
                    )
                )

    _emit(_SYSTEM, lmp_block, src)
    for zone, zblock in (lmp_block.get("zones") or {}).items():
        _emit(zone, zblock, zone_src)
    return rows


def _load_json(raw_dir: Path, name: str) -> dict:
    path = raw_dir / name
    if not path.is_file():
        return {}
    return json.loads(path.read_text())


def _iso_year_index(raw_dir: Path) -> dict[tuple[str, int], dict]:
    """Index every (iso, year) present across the raw sources -> the inputs to use.

    Each value is ``{"csv": Path|None, "calib": dict|None, "lmp": dict|None}``.
    """
    calib = _load_json(raw_dir, CALIBRATION_REFERENCE_JSON)
    lmp = _load_json(raw_dir, ACTUAL_LMP_JSON)
    index: dict[tuple[str, int], dict] = {}

    def slot(iso: str, year: int) -> dict:
        return index.setdefault((iso, year), {"csv": None, "calib": None, "lmp": None})

    for csv_path in sorted(raw_dir.glob("*_renewable_capacity.csv")):
        m = _RENEWABLE_CSV_RE.match(csv_path.name)
        if m:
            slot(m["iso"], int(m["year"]))["csv"] = csv_path

    for iso, years in calib.get("isos", {}).items():
        for year_str, block in years.items():
            slot(iso, int(year_str))["calib"] = block

    for iso, years in lmp.items():
        for year_str, block in years.items():
            slot(iso, int(year_str))["lmp"] = block

    return index


def _build_frame(
    iso: str, year: int, inputs: dict, egrid: dict
) -> tuple[pd.DataFrame, list[str]]:
    """Assemble the long-form frame for one ISO-year and the raw paths it drew on."""
    rows: list[dict] = []
    sources: list[str] = []

    if inputs["csv"] is not None:
        rows.extend(_capacity_rows(inputs["csv"]))
        sources.append(_relpath(inputs["csv"]))

    block = inputs["calib"]
    if block is not None:
        before = len(rows)
        rows.extend(_generation_rows(iso, year, block))
        rows.extend(_emissions_rows(iso, year, egrid.get(iso, {})))
        rows.extend(_demand_rows(iso, year, block))
        rows.extend(_henry_hub_rows(iso, year, block))
        if len(rows) > before:
            sources.append(f"{CALIBRATION_REFERENCE_JSON}#isos.{iso}.{year}")

    lmp_block = inputs["lmp"]
    if lmp_block is not None:
        before = len(rows)
        rows.extend(_price_rows(iso, year, lmp_block))
        if len(rows) > before:
            sources.append(f"{ACTUAL_LMP_JSON}#{iso}.{year}")

    df = pd.DataFrame(rows, columns=_COLUMNS)
    if not df.empty:
        df = df.astype({"year": "int64", "month": "int64", "value": "float64"})
    return df, sources


def curate(raw_dir: Path | str = DEFAULT_RAW_DIR) -> list[Path]:
    """Reconcile the raw validation benchmarks into clean ``validation`` parquet.

    Idempotent and re-runnable; reads only ``raw_dir``. Writes one parquet per
    ISO-year through :func:`clean_io.write_clean`, round-trip-validates each, and
    returns the paths written.
    """
    raw_dir = Path(raw_dir)
    egrid = _load_json(raw_dir, CALIBRATION_REFERENCE_JSON).get("egrid_benchmark", {})
    index = _iso_year_index(raw_dir)

    written: list[Path] = []
    for iso, year in sorted(index):
        df, sources = _build_frame(iso, year, index[(iso, year)], egrid)
        if df.empty:
            logger.warning("no validation benchmarks for %s %d; skipping", iso, year)
            continue
        path = write_clean(
            df, "validation", iso=iso, year=year, source=", ".join(sources)
        )
        validate_clean(path)
        logger.info("wrote %s (%d rows)", _relpath(path), len(df))
        written.append(path)

    logger.info("curated %d ISO-year validation files", len(written))
    return written


if __name__ == "__main__":
    curate()
