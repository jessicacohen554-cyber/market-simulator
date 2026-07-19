"""Curate the ``generation`` clean datatype (generation by fuel, long form).

Reconciles three raw layouts onto the one canonical fuel vocabulary declared in
``data/dictionary/schema/generation.schema.yaml`` -- one row per
``(iso, zone, fuel, interval_start_utc)``:

* **EIA-930 hourly** (``data/raw/eia-930-hourly/<BA> hourly.parquet``): wide
  ``NG: <CODE>`` columns per balancing authority. The wide fuel columns are
  *unpivoted* to the long ``(fuel, generation_mw)`` form. Each BA that is an
  ISO/RTO becomes ISO-wide totals at ``zone="SYSTEM"``. ``is_renewable`` is
  unknown for this source and left null.
* **PJM** (``data/raw/ISO-specific-gen-data/PJM_<year>_gen_by_fuel.csv``):
  already long (``datetime_beginning_utc, fuel_type, mw, is_renewable``). PJM's
  own feed is preferred over EIA-930's PJM BA because it carries the
  ``is_renewable`` flag; the EIA-930 ``PJM`` file is therefore skipped.
* **NYISO** (``data/raw/NYISO/fuel-mix/NYISO_fuelmix_hourly_<year>.csv.gz``):
  NYISO's own hourly-aggregated Real-Time Fuel Mix (P-63) in seven native fuel
  classes. Preferred over the EIA-930 ``NYIS`` BA (same reason as PJM -- it is
  NYISO's own posting, and the class split is native rather than EIA-estimated),
  so the EIA-930 ``NYIS`` file is skipped. See ``fetch_nyiso_fuel_mix.py``.
* **CAISO** production-by-technology (``data/raw/caiso-curtailment/*.xlsx``,
  ``Production`` sheet) is **not** used here: its buckets do not separate
  cleanly onto the canonical vocabulary (``Thermal`` lumps gas/coal/oil, and
  ``Renewables`` overlaps ``Solar``/``Wind`` while bundling biomass/biogas/
  geothermal/small-hydro -- see the sheet's ``Read_me``). CAISO generation is
  taken from the clean EIA-930 ``CISO`` BA instead, whose ``NG:`` codes (incl.
  ``GEO``) map 1:1 onto the canonical fuels.

Canonical fuel vocabulary (schema): ``coal, gas, nuclear, hydro, solar, wind,
geothermal, oil, storage, other``.

Every output is written through ``clean_io.write_clean(df, "generation",
iso=..., year=...)`` (partitioned by ISO + UTC year) and round-tripped through
``clean_io.validate_clean``. The script reads only ``data/raw`` and is
idempotent / re-runnable. ``data/clean`` is gitignored -- regenerate with::

    python -m scripts.data.curate_generation
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from market_sim.config import paths
from scripts.lib import clean_io

# ---------------------------------------------------------------------------
# Raw source locations (read-only)
# ---------------------------------------------------------------------------
EIA_930_HOURLY_DIR: Path = paths.EIA_HOURLY_DIR
PJM_GEN_DIR: Path = paths.RAW_DIR / "ISO-specific-gen-data"
NYISO_GEN_DIR: Path = paths.RAW_DIR / "NYISO" / "fuel-mix"

# ---------------------------------------------------------------------------
# Reconciliation maps
# ---------------------------------------------------------------------------
# EIA-930 balancing-authority code -> ISO/RTO code. Only BAs that *are* an
# ISO/RTO are curated (the ``iso`` column is an ISO/RTO code); the BAs that are
# plain utilities/regions (SOCO = Southern Company, FLA = Florida) are skipped.
# PJM is intentionally absent: its dedicated CSV feed (with is_renewable) is the
# authoritative PJM source, so the EIA-930 ``PJM`` BA is not double-counted.
# NYIS is intentionally absent: NYISO's own Real-Time Fuel Mix feed is the
# authoritative NYISO source (curate_nyiso), so the EIA-930 ``NYIS`` BA is not
# double-counted (same policy as PJM).
EIA_BA_TO_ISO: dict[str, str] = {
    "CISO": "CAISO",
    "ERCO": "ERCOT",
    "ISNE": "NEISO",
    "MISO": "MISO",
}

# EIA-930 ``NG: <CODE>`` energy-source code -> canonical fuel bucket. The five
# storage-family codes (battery, pumped storage, solar+storage, unknown/other
# energy storage) collapse onto ``storage``; charging shows as negative MW.
EIA_FUEL_MAP: dict[str, str] = {
    "COL": "coal",
    "NG": "gas",
    "NUC": "nuclear",
    "WAT": "hydro",
    "SUN": "solar",
    "WND": "wind",
    "GEO": "geothermal",
    "OIL": "oil",
    "OTH": "other",
    "BAT": "storage",
    "PS": "storage",
    "SNB": "storage",
    "UES": "storage",
    "OES": "storage",
}

# PJM ``fuel_type`` -> canonical fuel bucket. PJM's renewable-rollup buckets
# ("Other Renewables") and "Multiple Fuels" have no dedicated canonical home and
# fold into ``other`` (their is_renewable flag is preserved per-row before the
# rollup; see _aggregate_to_canonical).
PJM_FUEL_MAP: dict[str, str] = {
    "Coal": "coal",
    "Gas": "gas",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
    "Solar": "solar",
    "Wind": "wind",
    "Oil": "oil",
    "Storage": "storage",
    "Other": "other",
    "Other Renewables": "other",
    "Multiple Fuels": "other",
}

# NYISO Real-Time Fuel Mix category -> canonical fuel bucket. NYISO reports
# seven native classes; the reconciliation onto the coarse canonical vocabulary
# (CLAUDE.md rule 11 -- document the misalignment, prefer the real data):
#   * "Dual Fuel" folds into ``gas`` alongside "Natural Gas": these units burn
#     gas the overwhelming majority of hours (oil only in winter gas-curtailment
#     events), and lumping both as gas matches how the EIA-930 ``NG`` code (which
#     this feed replaces) already represented NYISO gas. The dual-fuel/oil
#     distinction is preserved in the committed raw csv.gz, not this coarse view.
#   * "Other Fossil Fuels" -> ``oil``: NYISO coal is ~0 post-2020 (Somerset/
#     Cayuga retired), so this residual fossil class is oil/kerosene-dominant;
#     mapping to ``oil`` keeps it distinct from the renewable "other" bucket.
#   * "Other Renewables" -> ``other`` (biomass/methane/refuse/small-solar rollup;
#     NYISO carries no standalone solar class in this feed).
NYISO_FUEL_MAP: dict[str, str] = {
    "Natural Gas": "gas",
    "Dual Fuel": "gas",
    "Nuclear": "nuclear",
    "Hydro": "hydro",
    "Wind": "wind",
    "Other Renewables": "other",
    "Other Fossil Fuels": "oil",
}

# is_renewable by NYISO category (unambiguous from the class name).
NYISO_RENEWABLE: dict[str, bool] = {
    "Natural Gas": False,
    "Dual Fuel": False,
    "Nuclear": False,
    "Hydro": True,
    "Wind": True,
    "Other Renewables": True,
    "Other Fossil Fuels": False,
}

# Final canonical column order (matches the schema).
_COLUMNS = [
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "zone",
    "fuel",
    "generation_mw",
    "is_renewable",
]


def _map_or_raise(codes: set[str], mapping: dict[str, str], *, source: str) -> None:
    """Fail loudly on an unmapped source fuel code rather than dropping it.

    A genuinely new fuel code with no canonical home is a contract question for
    the schema, not something to silently swallow in a curation branch.
    """
    unknown = sorted(codes - set(mapping))
    if unknown:
        raise ValueError(
            f"{source}: unmapped fuel code(s) {unknown}; extend the fuel map or "
            f"raise a generation.schema.yaml contract change before curating."
        )


def _aggregate_to_canonical(long: pd.DataFrame) -> pd.DataFrame:
    """Collapse a long ``(fuel, generation_mw, is_renewable)`` frame onto keys.

    Several source codes can map to one canonical fuel (e.g. PJM "Other" +
    "Other Renewables" -> ``other``; EIA battery + pumped storage -> ``storage``),
    so generation_mw is summed per ``(iso, zone, fuel, interval_start_utc)``.
    ``is_renewable`` is kept only when every contributing row agrees; a mix
    (renewable + non-renewable folded into the same bucket) collapses to null.
    """

    def _reduce_renewable(s: pd.Series) -> object:
        vals = s.dropna().unique()
        if len(vals) == 1:
            return bool(vals[0])
        return pd.NA

    grouped = (
        long.groupby(
            ["interval_start_utc", "interval_start_local", "iso", "zone", "fuel"],
            dropna=False,
            sort=False,
        )
        .agg(
            generation_mw=("generation_mw", "sum"),
            is_renewable=("is_renewable", _reduce_renewable),
        )
        .reset_index()
    )
    return grouped


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce dtypes to the canonical schema and order columns."""
    out = pd.DataFrame(
        {
            "interval_start_utc": pd.to_datetime(df["interval_start_utc"], utc=True),
            "interval_start_local": pd.to_datetime(df["interval_start_local"]).astype(
                "datetime64[ns]"
            ),
            "iso": df["iso"].astype("string"),
            "zone": df["zone"].astype("string"),
            "fuel": df["fuel"].astype("string"),
            "generation_mw": df["generation_mw"].astype("float64"),
            "is_renewable": df["is_renewable"].astype("boolean"),
        }
    )
    return (
        out[_COLUMNS]
        .sort_values(["interval_start_utc", "iso", "zone", "fuel"])
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Per-source curation
# ---------------------------------------------------------------------------
def curate_eia930_ba(path: Path, iso: str) -> pd.DataFrame:
    """Unpivot one EIA-930 BA hourly parquet to the canonical long frame.

    ``zone="SYSTEM"`` (ISO-wide totals); ``is_renewable`` is null (EIA-930 has
    no renewable flag). UTC timestamps become tz-aware UTC; the BA's local wall
    clock is carried as ``interval_start_local``.
    """
    raw = pd.read_parquet(path)
    fuel_cols = {c: c[len("NG: ") :] for c in raw.columns if c.startswith("NG: ")}
    _map_or_raise(set(fuel_cols.values()), EIA_FUEL_MAP, source=f"EIA-930 {path.name}")

    base = pd.DataFrame(
        {
            "interval_start_utc": pd.to_datetime(raw["UTC time"]).dt.tz_localize("UTC"),
            "interval_start_local": pd.to_datetime(raw["Local time"]),
        }
    )
    melted = (
        raw[list(fuel_cols)]
        .rename(columns=fuel_cols)
        .set_axis(base.index)
        .join(base)
        .melt(
            id_vars=["interval_start_utc", "interval_start_local"],
            var_name="code",
            value_name="generation_mw",
        )
    )
    melted = melted.dropna(subset=["generation_mw"])
    melted["fuel"] = melted["code"].map(EIA_FUEL_MAP)
    melted["iso"] = iso
    melted["zone"] = "SYSTEM"
    melted["is_renewable"] = pd.NA
    return _aggregate_to_canonical(melted.drop(columns="code"))


def curate_pjm(paths_in: list[Path]) -> pd.DataFrame:
    """Curate the PJM gen-by-fuel CSVs to the canonical long frame.

    PJM is already long; ``zone="SYSTEM"``. The ``is_renewable`` flag is carried
    through (collapsed to null only where a canonical bucket mixes renewable and
    non-renewable source fuels). UTC timestamps become tz-aware UTC; the Eastern
    ``datetime_beginning_ept`` clock is carried as ``interval_start_local``.
    """
    frames = []
    for p in sorted(paths_in):
        df = pd.read_csv(
            p,
            usecols=[
                "datetime_beginning_utc",
                "datetime_beginning_ept",
                "fuel_type",
                "mw",
                "is_renewable",
            ],
        )
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    _map_or_raise(set(raw["fuel_type"]), PJM_FUEL_MAP, source="PJM gen_by_fuel")

    fmt = "%m/%d/%Y %I:%M:%S %p"
    long = pd.DataFrame(
        {
            "interval_start_utc": pd.to_datetime(
                raw["datetime_beginning_utc"], format=fmt
            ).dt.tz_localize("UTC"),
            "interval_start_local": pd.to_datetime(
                raw["datetime_beginning_ept"], format=fmt
            ),
            "iso": "PJM",
            "zone": "SYSTEM",
            "fuel": raw["fuel_type"].map(PJM_FUEL_MAP),
            "generation_mw": raw["mw"].astype("float64"),
            "is_renewable": raw["is_renewable"].astype("boolean"),
        }
    )
    return _aggregate_to_canonical(long)


def curate_nyiso(paths_in: list[Path]) -> pd.DataFrame:
    """Curate the NYISO Real-Time Fuel Mix CSV.GZ files to the canonical frame.

    Already long and hourly-aggregated (``interval_start_utc``,
    ``interval_start_local``, ``fuel_category``, ``gen_mw``, ``n_intervals``);
    ``zone="SYSTEM"`` (NYCA-wide totals). NYISO's seven native classes fold onto
    the canonical vocabulary via ``NYISO_FUEL_MAP`` (Dual Fuel + Natural Gas ->
    ``gas``, Other Fossil Fuels -> ``oil``, Other Renewables -> ``other``); the
    per-class ``is_renewable`` flag is set from ``NYISO_RENEWABLE``. The
    ``n_intervals`` column (measured-vs-gap-filled marker) is a raw-only
    diagnostic and is dropped here.
    """
    frames = []
    for p in sorted(paths_in):
        frames.append(pd.read_csv(p, compression="gzip"))
    raw = pd.concat(frames, ignore_index=True)
    _map_or_raise(set(raw["fuel_category"]), NYISO_FUEL_MAP, source="NYISO fuel mix")

    long = pd.DataFrame(
        {
            "interval_start_utc": pd.to_datetime(raw["interval_start_utc"], utc=True),
            "interval_start_local": pd.to_datetime(raw["interval_start_local"]),
            "iso": "NYISO",
            "zone": "SYSTEM",
            "fuel": raw["fuel_category"].map(NYISO_FUEL_MAP),
            "generation_mw": raw["gen_mw"].astype("float64"),
            "is_renewable": raw["fuel_category"].map(NYISO_RENEWABLE).astype("boolean"),
        }
    )
    return _aggregate_to_canonical(long)


# ---------------------------------------------------------------------------
# Writing
# ---------------------------------------------------------------------------
def write_by_year(df: pd.DataFrame, iso: str, source: str) -> list[Path]:
    """Validate, write (one parquet per UTC year) and round-trip-check ``df``."""
    final = _finalize(df)
    written: list[Path] = []
    for year, part in final.groupby(final["interval_start_utc"].dt.year):
        year = int(year)
        out = clean_io.write_clean(
            part.reset_index(drop=True),
            "generation",
            iso=iso,
            year=year,
            source=source,
        )
        schema = clean_io.validate_clean(out)
        assert schema.datatype == "generation", out
        written.append(out)
        print(f"  wrote {out}  ({len(part):,} rows)")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    written: list[Path] = []

    # EIA-930 BAs that are ISOs (CAISO incl.) -> SYSTEM totals.
    for ba, iso in EIA_BA_TO_ISO.items():
        path = EIA_930_HOURLY_DIR / f"{ba} hourly.parquet"
        if not path.is_file():
            print(f"[skip] EIA-930 {ba}: {path} not found")
            continue
        print(f"[EIA-930] {ba} -> {iso}: {path}")
        df = curate_eia930_ba(path, iso)
        written += write_by_year(df, iso, source=str(path.relative_to(paths.REPO_ROOT)))

    # PJM from its dedicated gen-by-fuel feed (carries is_renewable).
    pjm_csvs = sorted(PJM_GEN_DIR.glob("PJM_*_gen_by_fuel.csv"))
    if pjm_csvs:
        print(f"[PJM] {len(pjm_csvs)} gen-by-fuel CSV(s) -> PJM")
        df = curate_pjm(pjm_csvs)
        src = ", ".join(str(p.relative_to(paths.REPO_ROOT)) for p in pjm_csvs)
        written += write_by_year(df, "PJM", source=src)
    else:
        print(f"[skip] PJM: no CSVs under {PJM_GEN_DIR}")

    # NYISO from its own Real-Time Fuel Mix feed (native 7-class split).
    nyiso_csvs = sorted(NYISO_GEN_DIR.glob("NYISO_fuelmix_hourly_*.csv.gz"))
    if nyiso_csvs:
        print(f"[NYISO] {len(nyiso_csvs)} fuel-mix CSV.GZ -> NYISO")
        df = curate_nyiso(nyiso_csvs)
        src = ", ".join(str(p.relative_to(paths.REPO_ROOT)) for p in nyiso_csvs)
        written += write_by_year(df, "NYISO", source=src)
    else:
        print(f"[skip] NYISO: no CSV.GZ under {NYISO_GEN_DIR}")

    print(f"\nDone: {len(written)} generation file(s) written + validated.")


if __name__ == "__main__":
    main()
