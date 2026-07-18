#!/usr/bin/env python3
"""Curate ALL fuel price data into clean Parquet partitions.

Reads raw CSVs from ``data/raw`` and writes schema-validated Parquet through
the frozen :func:`scripts.lib.clean_io.write_clean` seam.  Every output is
idempotent: re-running rebuilds the same clean Parquet from the same raw
inputs.

Datatypes curated
-----------------
``fuel-prices`` (extended)
    Henry Hub daily + Transco Z6 NY daily + Algonquin Citygate daily + CA
    Composite Average citygate daily hub prices, combined into one file:
    ``data/clean/fuel-prices/fuel-prices.parquet``

``fuel-hub-monthly``
    Henry Hub monthly averages (EIA RNGWHHDm):
    ``data/clean/fuel-hub-monthly/fuel-hub-monthly.parquet``

``fuel-basis``
    Per-ISO monthly gas basis vs Henry Hub (winter overlay; Algonquin for
    NEISO, Transco Z6/Iroquois for NYISO when filled):
    ``data/clean/fuel-basis/fuel-basis.parquet``

``fuel-zonal-hub``
    Per-ISO zonal gas-hub annual prices/basis, ISO-partitioned:
    ``data/clean/fuel-zonal-hub/<ISO>/fuel-zonal-hub.parquet``
    for ERCOT, NYISO, PJM, MISO.

``fuel-ercot-ep-gas``
    Monthly EIA N3045TX3 (TX delivered-to-electric-power gas price, $/Mcf):
    ``data/clean/fuel-ercot-ep-gas/fuel-ercot-ep-gas.parquet``

``fuel-takeorpay``
    Per-plant ERCOT gas spot share fractions from EIA-923 Schedule-5:
    ``data/clean/fuel-takeorpay/fuel-takeorpay.parquet``

Usage::

    python scripts/data/curate_fuel_prices.py           # curate all datatypes
    python scripts/data/curate_fuel_prices.py --only fuel-prices fuel-basis
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

# ---------------------------------------------------------------------------
# fuel-prices: daily hub spot prices (Henry Hub, Transco Z6, Algonquin)
# ---------------------------------------------------------------------------

DATATYPE = "fuel-prices"


@dataclass(frozen=True)
class Benchmark:
    """One raw benchmark file mapped onto the canonical fuel-prices schema."""

    filename: str
    fuel: str
    hub: str
    price_col: str
    date_col: str = "date"


BENCHMARKS: tuple[Benchmark, ...] = (
    Benchmark(
        filename="henry_hub_daily.csv",
        fuel="gas",
        hub="henry_hub",
        price_col="price_usd_mmbtu",
    ),
    Benchmark(
        filename="transco_z6_ny_daily.csv",
        fuel="gas",
        hub="transco_z6",
        price_col="transco_z6_ny_usd_mmbtu",
    ),
    Benchmark(
        filename="algonquin_citygate_daily.csv",
        fuel="gas",
        hub="algonquin",
        price_col="algonquin_citygate_usd_mmbtu",
    ),
    Benchmark(
        filename="caiso_citygate_daily.csv",
        fuel="gas",
        hub="ca_composite",
        price_col="ca_composite_usd_mmbtu",
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

    Converts ``date`` -> ``interval_start_utc`` (00:00 UTC, tz-aware) and
    tz-naive ``interval_start_local``; renames the per-file price column to
    ``price_usd_per_mmbtu``; sets ``fuel`` / ``hub`` from ``bench``.
    Extra columns in the raw CSV (e.g. ``source``, ``henry_hub_usd_mmbtu``)
    are dropped so the output conforms to the closed schema.
    """
    raw = pd.read_csv(path)
    missing = {bench.date_col, bench.price_col} - set(raw.columns)
    if missing:
        raise ValueError(
            f"{path}: missing expected column(s) {sorted(missing)}; "
            f"found {list(raw.columns)}"
        )

    local = pd.to_datetime(raw[bench.date_col])
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


def build_clean_hub_daily(gas_dir: Path) -> pd.DataFrame:
    """Reconcile every present daily benchmark under ``gas_dir`` into one frame."""
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
    """Curate fuel-prices (daily hub benchmarks) from ``gas_dir``; return path.

    Writes a single combined Parquet through :func:`write_clean` and asserts
    it round-trips via :func:`validate_clean`. ``gas_dir`` defaults to the
    real ``data/raw/gas-prices``; tests pass a synthetic directory.
    """
    gas_dir = gas_dir or paths.GAS_PRICES_DIR
    df = build_clean_hub_daily(gas_dir)

    sources = ", ".join(
        _repo_rel(gas_dir / b.filename)
        for b in BENCHMARKS
        if (gas_dir / b.filename).is_file()
    )
    out = write_clean(df, DATATYPE, source=sources)
    validate_clean(out)
    return out


# ---------------------------------------------------------------------------
# fuel-hub-monthly: monthly hub averages (Henry Hub)
# ---------------------------------------------------------------------------

_HUB_MONTHLY_DATATYPE = "fuel-hub-monthly"


def build_clean_hub_monthly(monthly_csv: Path) -> pd.DataFrame:
    """Reconcile henry_hub_monthly.csv onto the fuel-hub-monthly schema.

    The raw CSV has ``year, month, price_usd_mmbtu`` (per-file column name).
    The canonical schema uses ``price_usd_per_mmbtu`` and adds ``fuel``/``hub``
    keys so additional monthly hubs can coexist in the same file.
    """
    raw = pd.read_csv(monthly_csv)
    required = {"year", "month", "price_usd_mmbtu"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{monthly_csv}: missing columns {sorted(missing)}; found {list(raw.columns)}"
        )
    df = pd.DataFrame(
        {
            "fuel": pd.array(["gas"] * len(raw), dtype="string"),
            "hub": pd.array(["henry_hub"] * len(raw), dtype="string"),
            "year": raw["year"].astype("int64"),
            "month": raw["month"].astype("int64"),
            "price_usd_per_mmbtu": raw["price_usd_mmbtu"].astype("float64"),
        }
    )
    return df.sort_values(["fuel", "hub", "year", "month"]).reset_index(drop=True)


def curate_hub_monthly(gas_dir: Path | None = None) -> Path:
    """Curate fuel-hub-monthly from henry_hub_monthly.csv; return path written."""
    gas_dir = gas_dir or paths.GAS_PRICES_DIR
    csv_path = gas_dir / "henry_hub_monthly.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"henry_hub_monthly.csv not found under {gas_dir}")
    df = build_clean_hub_monthly(csv_path)
    out = write_clean(df, _HUB_MONTHLY_DATATYPE, source=_repo_rel(csv_path))
    validate_clean(out)
    return out


# ---------------------------------------------------------------------------
# fuel-basis: per-ISO monthly gas basis (winter overlay)
# ---------------------------------------------------------------------------

_BASIS_DATATYPE = "fuel-basis"


def build_clean_basis(basis_csv: Path) -> pd.DataFrame:
    """Reconcile gas_basis_by_iso_month.csv onto the fuel-basis schema.

    The raw CSV has ``iso, year, month, hub, basis_usd_mmbtu, source``; the
    ``source`` column is provenance metadata and is stripped on curation.
    """
    raw = pd.read_csv(basis_csv)
    required = {"iso", "year", "month", "hub", "basis_usd_mmbtu"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{basis_csv}: missing columns {sorted(missing)}; found {list(raw.columns)}"
        )
    df = pd.DataFrame(
        {
            "iso": raw["iso"].astype("string"),
            "year": raw["year"].astype("int64"),
            "month": raw["month"].astype("int64"),
            "hub": raw["hub"].astype("string"),
            "basis_usd_mmbtu": raw["basis_usd_mmbtu"].astype("float64"),
        }
    )
    return df.sort_values(["iso", "year", "month", "hub"]).reset_index(drop=True)


def curate_basis(raw_dir: Path | None = None) -> Path:
    """Curate fuel-basis from gas_basis_by_iso_month.csv; return path written."""
    raw_dir = raw_dir or paths.RAW_DATA_DIR
    csv_path = raw_dir / "gas_basis_by_iso_month.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"gas_basis_by_iso_month.csv not found under {raw_dir}")
    df = build_clean_basis(csv_path)
    out = write_clean(df, _BASIS_DATATYPE, source=_repo_rel(csv_path))
    validate_clean(out)
    return out


# ---------------------------------------------------------------------------
# fuel-zonal-hub: per-ISO zonal gas-hub annual data
# ---------------------------------------------------------------------------

_ZONAL_HUB_DATATYPE = "fuel-zonal-hub"


# Per-ISO CSV filenames and the columns each contributes.
# basis_col: annual mean basis vs Henry Hub ($/MMBtu), or None for NYISO.
# price_col: absolute annual hub price ($/MMBtu), or None for non-NYISO.
# extra_cols: additional model-needed columns (e.g. neg_day_freq for ERCOT).
@dataclass(frozen=True)
class ZonalHubSpec:
    """Specification for one ISO's zonal-gas-hub CSV."""

    iso: str
    filename: str
    basis_col: str | None
    price_col: str | None
    extra_float_cols: tuple[str, ...] = ()


_ZONAL_HUB_SPECS: tuple[ZonalHubSpec, ...] = (
    ZonalHubSpec(
        iso="ERCOT",
        filename="ercot_zonal_gas_hub.csv",
        basis_col="basis_vs_hh_usd_mmbtu",
        price_col=None,
        extra_float_cols=("neg_day_freq",),
    ),
    ZonalHubSpec(
        iso="NYISO",
        filename="nyiso_zonal_gas_hub.csv",
        basis_col=None,
        price_col="hub_usd_mmbtu",
    ),
    ZonalHubSpec(
        iso="PJM",
        filename="pjm_zonal_gas_hub.csv",
        basis_col="basis_vs_hh_usd_mmbtu",
        price_col=None,
    ),
    ZonalHubSpec(
        iso="MISO",
        filename="miso_zonal_gas_hub.csv",
        basis_col="basis_vs_hh_usd_mmbtu",
        price_col=None,
    ),
)


def build_clean_zonal_hub(csv_path: Path, spec: ZonalHubSpec) -> pd.DataFrame:
    """Reconcile one ISO's zonal-hub CSV onto the fuel-zonal-hub schema.

    Adds the ``iso`` column; strips ``source``, ``hub`` (raw name varies), and
    any other provenance-only columns.  Only the columns declared in the
    schema are written (``iso``, ``zone``, ``year``, ``hub``,
    ``basis_vs_hh_usd_mmbtu``, ``hub_usd_mmbtu``, ``neg_day_freq`` where
    present in the source).
    """
    raw = pd.read_csv(csv_path)
    required = {"zone", "year", "hub"}
    if spec.basis_col:
        required.add(spec.basis_col)
    if spec.price_col:
        required.add(spec.price_col)
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{csv_path}: missing columns {sorted(missing)}; found {list(raw.columns)}"
        )

    cols: dict[str, pd.Series] = {
        "iso": pd.array([spec.iso] * len(raw), dtype="string"),
        "zone": raw["zone"].astype("string"),
        "year": raw["year"].astype("int64"),
        "hub": raw["hub"].astype("string"),
    }
    if spec.basis_col and spec.basis_col in raw.columns:
        cols["basis_vs_hh_usd_mmbtu"] = raw[spec.basis_col].astype("float64")
    if spec.price_col and spec.price_col in raw.columns:
        cols["hub_usd_mmbtu"] = raw[spec.price_col].astype("float64")
    for extra in spec.extra_float_cols:
        if extra in raw.columns:
            cols[extra] = raw[extra].astype("float64")

    df = pd.DataFrame(cols)
    return df.sort_values(["iso", "zone", "year", "hub"]).reset_index(drop=True)


def curate_zonal_hub(raw_dir: Path | None = None) -> list[Path]:
    """Curate fuel-zonal-hub for all ISOs; return list of paths written."""
    raw_dir = raw_dir or paths.RAW_DATA_DIR
    written: list[Path] = []
    for spec in _ZONAL_HUB_SPECS:
        csv_path = raw_dir / spec.filename
        if not csv_path.is_file():
            continue
        df = build_clean_zonal_hub(csv_path, spec)
        out = write_clean(
            df,
            _ZONAL_HUB_DATATYPE,
            iso=spec.iso,
            source=_repo_rel(csv_path),
        )
        validate_clean(out)
        written.append(out)
    if not written:
        raise FileNotFoundError(
            f"no zonal-hub CSVs found under {raw_dir} "
            f"(expected: {[s.filename for s in _ZONAL_HUB_SPECS]})"
        )
    return written


# ---------------------------------------------------------------------------
# fuel-ercot-ep-gas: TX delivered-to-electric-power gas price ($/Mcf)
# ---------------------------------------------------------------------------

_ERCOT_EP_GAS_DATATYPE = "fuel-ercot-ep-gas"


def build_clean_ercot_ep_gas(csv_path: Path) -> pd.DataFrame:
    """Reconcile ercot_electric_power_gas_price.csv onto the schema.

    The raw CSV has ``year, month, price_usd_mcf, source``; ``source`` is
    stripped as provenance metadata.
    """
    raw = pd.read_csv(csv_path)
    required = {"year", "month", "price_usd_mcf"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{csv_path}: missing columns {sorted(missing)}; found {list(raw.columns)}"
        )
    df = pd.DataFrame(
        {
            "year": raw["year"].astype("int64"),
            "month": raw["month"].astype("int64"),
            "price_usd_mcf": raw["price_usd_mcf"].astype("float64"),
        }
    )
    return df.sort_values(["year", "month"]).reset_index(drop=True)


def curate_ercot_ep_gas(raw_dir: Path | None = None) -> Path:
    """Curate fuel-ercot-ep-gas from ercot_electric_power_gas_price.csv; return path."""
    raw_dir = raw_dir or paths.RAW_DATA_DIR
    csv_path = raw_dir / "ercot_electric_power_gas_price.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"ercot_electric_power_gas_price.csv not found under {raw_dir}"
        )
    df = build_clean_ercot_ep_gas(csv_path)
    out = write_clean(df, _ERCOT_EP_GAS_DATATYPE, source=_repo_rel(csv_path))
    validate_clean(out)
    return out


# ---------------------------------------------------------------------------
# fuel-takeorpay: ERCOT per-plant gas spot share fractions
# ---------------------------------------------------------------------------

_TAKEORPAY_DATATYPE = "fuel-takeorpay"


def build_clean_takeorpay(csv_path: Path) -> pd.DataFrame:
    """Reconcile gas_takeorpay_ERCOT.csv onto the fuel-takeorpay schema.

    The raw CSV has ``plant_code, spot_share, contract_share, total_mmbtu,
    n_receipts, source, breakdown``; only ``plant_code``, ``spot_share``, and
    ``total_mmbtu`` are retained (the rest are provenance or redundant).
    """
    raw = pd.read_csv(csv_path)
    required = {"plant_code", "spot_share", "total_mmbtu"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{csv_path}: missing columns {sorted(missing)}; found {list(raw.columns)}"
        )
    df = pd.DataFrame(
        {
            "plant_code": raw["plant_code"].astype("int64"),
            "spot_share": raw["spot_share"].astype("float64"),
            "total_mmbtu": raw["total_mmbtu"].astype("float64"),
        }
    )
    return df.sort_values("plant_code").reset_index(drop=True)


def curate_takeorpay(processed_dir: Path | None = None) -> Path:
    """Curate fuel-takeorpay from gas_takeorpay_ERCOT.csv; return path written."""
    processed_dir = processed_dir or paths.PROCESSED_DIR
    csv_path = processed_dir / "gas_takeorpay_ERCOT.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(
            f"gas_takeorpay_ERCOT.csv not found under {processed_dir}"
        )
    df = build_clean_takeorpay(csv_path)
    out = write_clean(df, _TAKEORPAY_DATATYPE, source=_repo_rel(csv_path))
    validate_clean(out)
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_ALL_TARGETS = (
    "fuel-prices",
    "fuel-hub-monthly",
    "fuel-basis",
    "fuel-zonal-hub",
    "fuel-ercot-ep-gas",
    "fuel-takeorpay",
)


def main(argv: list[str] | None = None) -> None:
    """Curate all (or selected) fuel-price datatypes from raw inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="DATATYPE",
        choices=_ALL_TARGETS,
        help="curate only the listed datatypes (default: all)",
    )
    args = parser.parse_args(argv)
    targets = frozenset(args.only) if args.only else frozenset(_ALL_TARGETS)

    if "fuel-prices" in targets:
        out = curate()
        print(f"fuel-prices       → {out} ({out.stat().st_size:,} bytes)")

    if "fuel-hub-monthly" in targets:
        out = curate_hub_monthly()
        print(f"fuel-hub-monthly  → {out} ({out.stat().st_size:,} bytes)")

    if "fuel-basis" in targets:
        out = curate_basis()
        print(f"fuel-basis        → {out} ({out.stat().st_size:,} bytes)")

    if "fuel-zonal-hub" in targets:
        outs = curate_zonal_hub()
        for out in outs:
            print(f"fuel-zonal-hub    → {out} ({out.stat().st_size:,} bytes)")

    if "fuel-ercot-ep-gas" in targets:
        out = curate_ercot_ep_gas()
        print(f"fuel-ercot-ep-gas → {out} ({out.stat().st_size:,} bytes)")

    if "fuel-takeorpay" in targets:
        out = curate_takeorpay()
        print(f"fuel-takeorpay    → {out} ({out.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
