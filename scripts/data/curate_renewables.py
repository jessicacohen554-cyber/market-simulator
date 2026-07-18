"""Curate the ``renewables`` clean datatype (hourly output, HSL & curtailment).

Reconciles the renewable-availability sources into the long, schema-validated
``renewables`` table (one row per ``iso`` / ``zone`` / ``fuel`` / hour):

* ``data/raw/caiso-hsl/caiso_<year>_hsl_hourly.parquet`` and
  ``data/raw/ercot-hsl/ercot_<year>_hsl_hourly.parquet`` — the per-technology
  *wide* HSL frames (``hour``, ``wind_gen_mw``, ``wind_hsl_mw``,
  ``solar_gen_mw``, ``solar_hsl_mw``). These are the model's GEN/HSL pair:
  delivered generation vs the uncurtailed high-sustained-limit potential.
* ``data/raw/caiso-curtailment/productionandcurtailmentsdata_<year>.xlsx`` —
  CAISO's 5-minute wind/solar curtailment workbook. This is the *upstream
  provenance* of the CAISO HSL frame: ``scripts/data/build_caiso_hsl.py`` builds
  ``wind_hsl_mw = delivered + hourly-aggregated curtailment`` (and likewise for
  solar), so ``hsl_mw - generation_mw`` reproduces that aggregated 5-minute
  curtailment exactly. This script aggregates the workbook independently and
  asserts the hour-by-hour reconciliation as a cross-check.

Transformation (per the schema contract, renewables.schema.yaml):

* UNPIVOT the wide per-tech columns to long, keyed on ``fuel`` (wind/solar):
  ``*_gen_mw`` -> ``generation_mw``, ``*_hsl_mw`` -> ``hsl_mw``.
* ``curtailment_mw = hsl_mw - generation_mw`` where ``hsl_mw`` is reported.
* ``zone = "SYSTEM"`` — these are ISO-wide system totals, not zone-resolved.

The ``hour`` column -> ``interval_start_utc`` mapping
-----------------------------------------------------
The HSL ``hour`` is a 0-based index on the model's fixed **non-leap 8760-hour
clock** in the balancing authority's **local standard time** (see
``scripts/data/build_caiso_hsl.py`` and ``market_sim.data.eia_loader``):

* ``hour == 0`` is ``{year}-01-01 00:00`` in the BA's local clock;
* the index advances 24 hours per calendar day and **drops Feb 29** in a leap
  year, so both 2023 and 2024 are exactly 8760 rows (the 2024 file's index
  still labels Mar 1 onward with their true 2024 dates — Feb 29 is simply
  absent).

``interval_start_local`` is therefore reconstructed by walking that non-leap
calendar from ``{year}-01-01 00:00`` (a tz-naive wall clock), and
``interval_start_utc`` by shifting it by the BA's **standard-time** UTC offset
(CAISO Pacific = UTC-8 -> +8 h; ERCOT Central = UTC-6 -> +6 h) and localizing
to UTC. A fixed standard offset — rather than a DST-aware IANA zone — is the
faithful choice here: the model clock is a fixed 8760-hour grid with no
spring-forward gap or fall-back fold, and ``eia_loader`` itself anchors its
UTC<->local offsets on standard time (its comments note "both ends are on
standard time, so the offsets are exact even mid-DST"). The documented
trade-off is that summer (DST) local hours, whose true offset is one hour less,
carry a UTC stamp one hour early; this is internally consistent with the model
clock the GEN/HSL series live on and is recorded here so the convention is
explicit.

Output is partitioned by ``iso`` then ``year``
(``data/clean/renewables/<ISO>/renewables_<year>.parquet``) and every file is
written through ``scripts.lib.clean_io.write_clean`` and round-trip checked
with ``validate_clean``.

Idempotent and re-runnable: reads only ``data/raw`` and overwrites its clean
outputs in place.

Run:
    python scripts/data/curate_renewables.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
# Repo root (for ``scripts.lib`` / ``scripts.data.build_caiso_hsl``) and ``src`` (for
# ``market_sim``) on the path, so the module imports whether run as a script or
# collected by pytest.
for _p in (REPO_ROOT, REPO_ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from market_sim.config.paths import (  # noqa: E402
    CAISO_HSL_DIR,
    ERCOT_HSL_DIR,
    RAW_DATA_DIR,
)
from scripts.lib import clean_io  # noqa: E402

# The renewable fuels carried in the wide HSL frames, unpivoted to ``fuel``.
FUELS: tuple[str, ...] = ("wind", "solar")

# Wide columns every HSL parquet must carry before the unpivot.
_HSL_WIDE_COLUMNS: tuple[str, ...] = (
    "hour",
    "wind_gen_mw",
    "wind_hsl_mw",
    "solar_gen_mw",
    "solar_hsl_mw",
)

# Reconciliation tolerance (MW) for the CAISO 5-minute curtailment cross-check.
# The HSL frame is built as delivered + aggregated curtailment, so hsl - gen
# equals the re-aggregated workbook to floating-point noise.
_CURTAILMENT_RECONCILE_TOL_MW = 1e-6


@dataclass(frozen=True)
class IsoSource:
    """One ISO's raw HSL inputs and the local-standard-time UTC offset."""

    iso: str
    hsl_dir: Path
    file_prefix: str  # "caiso" / "ercot"
    std_offset_hours: int  # local standard time -> UTC (PST=8, CST=6)
    # CAISO only: the 5-minute curtailment workbook directory (cross-check).
    curtailment_dir: Path | None = None

    def hsl_path(self, year: int) -> Path:
        return self.hsl_dir / f"{self.file_prefix}_{year}_hsl_hourly.parquet"

    def curtailment_path(self, year: int) -> Path | None:
        if self.curtailment_dir is None:
            return None
        return self.curtailment_dir / f"productionandcurtailmentsdata_{year}.xlsx"


ISO_SOURCES: tuple[IsoSource, ...] = (
    IsoSource(
        iso="CAISO",
        hsl_dir=CAISO_HSL_DIR,
        file_prefix="caiso",
        std_offset_hours=8,  # Pacific Standard Time = UTC-8
        curtailment_dir=RAW_DATA_DIR / "caiso-curtailment",
    ),
    IsoSource(
        iso="ERCOT",
        hsl_dir=ERCOT_HSL_DIR,
        file_prefix="ercot",
        std_offset_hours=6,  # Central Standard Time = UTC-6
    ),
)


def reconstruct_interval_starts(
    hour: np.ndarray, year: int, std_offset_hours: int
) -> tuple[pd.Series, pd.Series]:
    """Map the HSL ``hour`` index to ``(interval_start_utc, interval_start_local)``.

    ``hour`` is a 0-based index on the fixed non-leap 8760-hour clock in the
    BA's local standard time (see the module docstring). The wall-clock local
    start is the year's hourly calendar with Feb 29 dropped; UTC is that shifted
    by the standard-time offset. ``hour`` must be the contiguous ``0..len-1``
    range, which both shipped HSL builders emit.

    Returns ``(utc, local)`` as a tz-aware UTC series and a tz-naive local
    series, both aligned to ``hour``.
    """
    n = len(hour)
    expected = np.arange(n, dtype=hour.dtype)
    if not np.array_equal(hour, expected):
        raise ValueError(
            f"HSL 'hour' is not a contiguous 0..{n - 1} index; got "
            f"min={hour.min()} max={hour.max()} (n={n})"
        )

    # Local wall clock on the non-leap calendar: 24 h/day, Feb 29 dropped.
    rng = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left"
    )
    rng = rng[~((rng.month == 2) & (rng.day == 29))]
    if len(rng) != n:
        raise ValueError(
            f"non-leap calendar for {year} has {len(rng)} hours but the HSL "
            f"frame has {n} rows"
        )

    local = pd.Series(rng, name="interval_start_local").astype("datetime64[ns]")
    utc = (
        (local + pd.Timedelta(hours=std_offset_hours))
        .dt.tz_localize("UTC")
        .rename("interval_start_utc")
    )
    return utc, local


def unpivot_to_long(
    wide: pd.DataFrame, iso: str, year: int, std_offset_hours: int
) -> pd.DataFrame:
    """Unpivot a wide HSL frame to the long ``renewables`` schema.

    ``*_gen_mw`` -> ``generation_mw``, ``*_hsl_mw`` -> ``hsl_mw`` keyed on
    ``fuel``; ``curtailment_mw = hsl_mw - generation_mw``; ``zone = "SYSTEM"``.
    """
    missing = [c for c in _HSL_WIDE_COLUMNS if c not in wide.columns]
    if missing:
        raise ValueError(f"{iso} {year} HSL frame missing columns: {missing}")

    wide = wide.sort_values("hour").reset_index(drop=True)
    utc, local = reconstruct_interval_starts(
        wide["hour"].to_numpy(), year, std_offset_hours
    )

    frames: list[pd.DataFrame] = []
    for fuel in FUELS:
        gen = wide[f"{fuel}_gen_mw"].astype("float64")
        hsl = wide[f"{fuel}_hsl_mw"].astype("float64")
        frames.append(
            pd.DataFrame(
                {
                    "interval_start_utc": utc.to_numpy(),
                    "interval_start_local": local.to_numpy(),
                    "iso": pd.array([iso] * len(wide), dtype="string"),
                    "zone": pd.array(["SYSTEM"] * len(wide), dtype="string"),
                    "fuel": pd.array([fuel] * len(wide), dtype="string"),
                    "generation_mw": gen.to_numpy(),
                    "hsl_mw": hsl.to_numpy(),
                    # curtailment where HSL is reported (hsl always present here).
                    "curtailment_mw": (hsl - gen).to_numpy(),
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


def reconcile_caiso_curtailment(long: pd.DataFrame, workbook: Path, year: int) -> None:
    """Cross-check ``hsl_mw - generation_mw`` against the 5-minute workbook.

    Re-aggregates CAISO's ``productionandcurtailmentsdata_<year>.xlsx`` to the
    hourly curtailment series (reusing ``build_caiso_hsl``'s loader) and asserts
    it matches the long frame's ``curtailment_mw`` per fuel and hour, confirming
    the HSL frame's ``hsl = delivered + curtailment`` provenance.
    """
    # Local import: pulls in build_caiso_hsl's module-level deps only when the
    # cross-check actually runs (CAISO years with the workbook present).
    from scripts.data.build_caiso_hsl import load_reported_curtailment_hourly

    wind_curt, solar_curt, last_month = load_reported_curtailment_hourly(workbook)
    if last_month < 12:
        # A partial-year workbook can't reconcile a full-year HSL frame; the
        # HSL builder skips such years, so we should never reach here, but
        # guard rather than assert on incomplete provenance.
        print(
            f"  CAISO {year}: workbook ends in month {last_month}; "
            "skipping curtailment cross-check."
        )
        return

    reported = {"wind": wind_curt, "solar": solar_curt}
    for fuel in FUELS:
        derived = long.loc[long["fuel"] == fuel, "curtailment_mw"].to_numpy(dtype=float)
        max_diff = float(np.abs(derived - reported[fuel]).max())
        if max_diff > _CURTAILMENT_RECONCILE_TOL_MW:
            raise AssertionError(
                f"CAISO {year} {fuel}: hsl-gen curtailment disagrees with the "
                f"5-minute workbook by {max_diff:.6g} MW "
                f"(tol {_CURTAILMENT_RECONCILE_TOL_MW:g})"
            )
        print(
            f"  CAISO {year} {fuel}: curtailment cross-check OK "
            f"(annual {reported[fuel].sum() / 1e6:.3f} TWh, "
            f"max hourly diff {max_diff:.2g} MW)"
        )


def _provenance(path: Path) -> str:
    """Repo-relative path string for provenance, falling back to absolute.

    Real raw inputs live under the repo; synthetic test fixtures may not.
    """
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def curate_iso_year(spec: IsoSource, year: int) -> Path:
    """Curate one ``(iso, year)`` HSL frame to a clean ``renewables`` parquet.

    Reads the wide HSL parquet, unpivots to long, runs the CAISO curtailment
    cross-check when the workbook is available, writes through
    ``clean_io.write_clean`` (partitioned by iso + year), and round-trip
    validates the written file. Returns the written path.
    """
    hsl_path = spec.hsl_path(year)
    wide = pd.read_parquet(hsl_path)
    long = unpivot_to_long(wide, spec.iso, year, spec.std_offset_hours)

    sources = [_provenance(hsl_path)]
    workbook = spec.curtailment_path(year)
    if workbook is not None and workbook.exists():
        reconcile_caiso_curtailment(long, workbook, year)
        sources.append(_provenance(workbook))

    out = clean_io.write_clean(
        long,
        "renewables",
        iso=spec.iso,
        year=year,
        source="; ".join(sources),
    )
    clean_io.validate_clean(out)
    print(
        f"  wrote {out} ({len(long)} rows, "
        f"{long['fuel'].nunique()} fuels) [schema-valid]"
    )
    return out


def discover_years(spec: IsoSource) -> list[int]:
    """Return the sorted years for which ``spec`` has an HSL parquet on disk."""
    years: list[int] = []
    for path in sorted(spec.hsl_dir.glob(f"{spec.file_prefix}_*_hsl_hourly.parquet")):
        stem = path.stem  # e.g. "caiso_2023_hsl_hourly"
        parts = stem.split("_")
        if len(parts) >= 2 and parts[1].isdigit():
            years.append(int(parts[1]))
    return sorted(set(years))


def main() -> int:
    """Curate every ISO-year with a raw HSL parquet under ``data/raw``."""
    written = 0
    for spec in ISO_SOURCES:
        years = discover_years(spec)
        if not years:
            print(f"{spec.iso}: no HSL parquets under {spec.hsl_dir}; skipping.")
            continue
        print(f"{spec.iso}: curating years {years}")
        for year in years:
            curate_iso_year(spec, year)
            written += 1
    print(f"\nDone: wrote {written} clean renewables file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
