"""Build ERCOT uncurtailed renewable potential (HSL) hourly profiles.

For each requested year, writes system-wide hourly wind/solar delivered
generation (GEN) and uncurtailed potential (HSL) to
``data/raw/ercot-hsl/ercot_<year>_hsl_hourly.parquet``.

HSL is the uncurtailed generation *potential*: the most a resource could have
produced given wind/sun at that moment. Delivered generation is

    GEN = HSL - curtailment

so the GEN/HSL ratio yields the endogenous curtailment that a transmission-
constrained dispatch model should be able to reproduce, and ``HSL - GEN`` is
ERCOT's *reported* curtailment that the calibration report benchmarks the
modeled curtailment against.

Two source paths, by year:

* **Published NP6 (preferred, any year)** — ERCOT MIS wind/solar
  power-production reports (the NP6 HSL upload) placed under
  ``data/raw/ercot-hsl/np6/``, as ``.csv`` or ``.zip`` of CSVs, flat or
  in per-year subdirectories. Accepted report families (both carry system-wide
  actual GEN and system-wide actual HSL):
    - NP4-732-CD / NP4-737-CD  Wind / Solar Power Production — Hourly
      Averaged Actual and Forecasted Values
    - NP4-733-CD / NP4-738-CD  Wind / Solar Power Production — Actual
      5-Minute Averaged Values
  Files are matched to wind vs solar by filename or column signature, and
  rows lacking an actual value (the reports' forward-forecast rows) are
  dropped. This is the authoritative full-footprint potential, so the
  renewables loader consumes it directly (no coverage reconciliation).

* **2023 fallback** — when no NP6 upload covers 2023, the UMass
  nodal-curtailment dataset (derived from ERCOT's 60-Day SCED Disclosure
  Reports), cloned from GitHub and aggregated from per-plant 15-minute series:
      https://github.com/codecexp/nodal-curtailment-analysis
      Maji, Irwin, Shenoy, Sitaraman (UMass Amherst), ACM e-Energy 2025.
  This is a *partial-footprint* reconstruction whose delivered undercounts the
  EIA-930 system total; the renewables loader reconciles it up to that level
  preserving its measured curtailment ratio (``renewables.hsl_potential_mw``).
  Drop the published 2023 NP4-732/737 reports into ``np6/`` to supersede it.

For any year with neither source the year is skipped with a data-needed
message — curtailment is never fabricated.

Alongside the system-wide parquet, any NP6 upload carrying per-region columns
also yields a **zonal sidecar**
``data/raw/ercot-hsl/ercot_<year>_hsl_zonal_hourly.parquet`` (long format:
``hour``, ``fuel``, ``region``, ``gen_mw``, ``hsl_mw``). Region-resolved
report families:

* NP4-742-CD / NP4-745-CD "... by Geographical Region" (GEO) — wind regions
  PANHANDLE/COASTAL/SOUTH/WEST/NORTH, solar regions CenterWest/NorthWest/
  FarWest/FarEast/SouthEast/CenterEast;
* the plain NP4-732-CD wind report's load-zone columns —
  LZ_SOUTH_HOUSTON/LZ_WEST/LZ_NORTH.

Per-region delivered GEN is the report's actual; the per-region potential is
the report's **COP HSL** (aggregated operating-plan HSLs of On-Line
resources) — no report family publishes a per-region *telemetered* actual
HSL, so zonal ``hsl_mw`` is COP-based (the same series the system-wide 2023
``hsl_mw`` uses, the GEO uploads carrying no actual-HSL column). A region
vocabulary posted for only part of the year (e.g. the lone 2024-09 wind GEO
upload) keeps NaN outside its covered span — month-scale holes are never
interpolated. ``--zonal-only`` refreshes the zonal sidecar without rewriting
the committed system-wide parquet.

The output series sit on the model's fixed non-leap 8760-hour clock keyed to
ERCOT-local **standard** time (CST, UTC-6, no DST) — matching the ``ERCO
hourly`` demand clock (see eia_loader). ERCOT report timestamps are Central
*Prevailing* Time (CPT: CDT in summer), so they are converted CPT -> CST
before placement (:func:`_prevailing_to_standard`); the repeated fall-back
hour is disambiguated by the reports' DSTFLAG and the spring-forward hour is
absent by construction, so the CST clock is covered with no DST gap. Feb 29
of a leap year is dropped.

Run:
    python scripts/data/build_ercot_hsl.py                 # all buildable years
    python scripts/data/build_ercot_hsl.py --year 2024 2025
    python scripts/data/build_ercot_hsl.py --year 2024 2025 --zonal-only
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

UMASS_REPO_URL = "https://github.com/codecexp/nodal-curtailment-analysis"
UMASS_YEAR = 2023
HOURS_PER_YEAR = 8760
INTERVALS_PER_HOUR = 4  # 15-minute SCED telemetry (UMass dataset)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import (  # noqa: E402
    CALIBRATION_DIR,
    ERCOT_HSL_DIR,
)
from market_sim.data.eia_loader import load_eia_hourly_renewable_gen  # noqa: E402

# Output HSL parquets and the NP6 upload drop zone resolve through
# config/paths.py (the single raw root under data/raw/ after the W1
# relocation).
OUT_DIR = ERCOT_HSL_DIR
# NP6 HSL upload drop zone for 2024+ (ERCOT MIS power-production reports).
NP6_DIR = OUT_DIR / "np6"

# Years built when --year is not given. Extend as backcast years are added.
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Calendar month per hour of the fixed non-leap 8760-hour clock (Feb 29 is
# dropped from leap years, so this mapping holds for every model year).
_MONTH_OF_HOUR: np.ndarray = pd.date_range(
    "2023-01-01", periods=HOURS_PER_YEAR, freq="h"
).month.to_numpy()

# Largest hole (hours) interpolated when placing NP6 report series on the
# 8760-hour clock. The DST spring-forward gap is 1 hour; anything beyond a
# day of missing telemetry means the upload is incomplete and is rejected.
_MAX_GAP_HOURS = 24

# Cited ERCOT-source data-quality defects: contiguous windows where the
# published NP6 report's system-wide ACTUAL/HSL columns carry physically
# impossible values (orders of magnitude above the installed fleet), baked
# identically into every later repost of the rolling window -- i.e. a
# defect in ERCOT's own source file, not an artifact of this builder or of
# this repo's own estimate. Confirmed 2026-07: 2024-08-20..23 system-wide
# wind AND solar actual+HSL both spike 3-10x above plausible ceilings (e.g.
# ACTUAL_LZ_WEST wind = 276,466 MW at 2024-08-23 HE1, vs. ERCOT's entire
# West-zone wind fleet far below that). These hours are excluded (treated
# as missing telemetry, then interpolated) rather than ingested as
# measured — an explicit, narrow exception to the general "too many
# missing hours -> reject" guard below, which stays unweakened for every
# other window/year/upload.
_KNOWN_BAD_NP6_WINDOWS: dict[int, list[tuple[str, str]]] = {
    2024: [("2024-08-20", "2024-08-23")],
}


def _known_bad_mask(index: pd.MultiIndex, year: int) -> np.ndarray:
    """Return a mask over ``(month, day, hour)`` for cited known-bad ERCOT
    NP6 telemetry windows in ``year`` (see ``_KNOWN_BAD_NP6_WINDOWS``)."""
    windows = _KNOWN_BAD_NP6_WINDOWS.get(year, [])
    if not windows:
        return np.zeros(len(index), dtype=bool)
    dates = pd.to_datetime(
        pd.DataFrame(
            {
                "year": year,
                "month": index.get_level_values("month"),
                "day": index.get_level_values("day"),
            }
        )
    )
    mask = np.zeros(len(index), dtype=bool)
    for start, end in windows:
        mask |= (dates >= pd.Timestamp(start)).to_numpy() & (
            dates <= pd.Timestamp(end)
        ).to_numpy()
    return mask


# EIA-930 (Hourly Grid Monitor) reference totals for the ERCOT balancing
# authority, 2023, used only as a sanity check on the aggregated GEN series
# when data/raw/_validation-source/calibration_reference.json is unavailable.
# Texas-wide wind/solar (~108 / ~32 TWh, EIA Today in Energy id=66464) is
# larger than the ERCOT BA alone because it also counts SPP Panhandle wind
# that lies outside ERCOT, so the ERCOT-only comparison is approximate.
EIA_REFERENCE_TWH: dict[int, dict[str, float]] = {
    2023: {"wind": 105.0, "solar": 32.0},
}

REFERENCE_PATH = CALIBRATION_DIR / "calibration_reference.json"


def out_file(year: int) -> Path:
    """Return the output parquet path for ``year``."""
    return OUT_DIR / f"ercot_{year}_hsl_hourly.parquet"


def zonal_out_file(year: int) -> Path:
    """Return the zonal (per-region) sidecar parquet path for ``year``."""
    return OUT_DIR / f"ercot_{year}_hsl_zonal_hourly.parquet"


def clone_dataset(dest: Path) -> Path:
    """Shallow-clone the UMass nodal-curtailment dataset.

    Args:
        dest: Directory into which the repository is cloned.

    Returns:
        Path to the cloned repository's ``data`` directory.

    Raises:
        subprocess.CalledProcessError: if the ``git clone`` fails.
    """
    print(f"Cloning {UMASS_REPO_URL} ...")
    subprocess.run(
        ["git", "clone", "--depth", "1", UMASS_REPO_URL, str(dest)],
        check=True,
        capture_output=True,
    )
    return dest / "data"


def aggregate_umass_hourly(data_dir: Path) -> pd.DataFrame:
    """Aggregate the 2023 per-plant 15-minute series into hourly totals.

    For each of wind and solar, the per-plant HSL and curtailment CSVs are
    summed across plants at each 15-minute timestamp, then averaged over
    each block of four consecutive intervals to form an hourly MW series
    (an average of MW over an hour equals MWh of energy).

    The CSV timestamps are ERCOT local (Central) time and so contain a DST
    spring-forward gap and a fall-back repeat. Grouping by clock hour would
    yield 8759 distinct hours; instead the intervals are grouped positionally
    (four-at-a-time over the chronologically sorted rows), giving a clean,
    continuous 8760-hour sequence indexed 0..8759. Delivered generation is
    ``HSL - curtailment``, floored at zero and capped at HSL to absorb
    telemetry noise.

    Args:
        data_dir: The dataset's ``data`` directory holding the ERCOT CSVs.

    Returns:
        A DataFrame of 8760 rows with columns ``hour``, ``wind_gen_mw``,
        ``wind_hsl_mw``, ``solar_gen_mw``, ``solar_hsl_mw`` and a ``month``
        helper column (1-12).

    Raises:
        AssertionError: if a fuel does not aggregate to exactly 8760 hours.
    """

    def hourly_sum(csv_name: str) -> np.ndarray:
        """Sum a per-plant CSV across plants and average to hourly MW."""
        df = pd.read_csv(data_dir / csv_name)
        ts = pd.to_datetime(df["datetime"], format="%m/%d/%Y %H:%M:%S")
        system = df.drop(columns=["datetime"]).sum(axis=1)
        # Sort chronologically, then collapse each block of four 15-minute
        # intervals into one hour by position (DST-safe; see docstring).
        system = system[ts.argsort(kind="stable").to_numpy()].to_numpy()
        n_hours = len(system) // INTERVALS_PER_HOUR
        assert n_hours == HOURS_PER_YEAR, (
            f"{csv_name} has {len(system)} intervals -> {n_hours} hours, "
            f"expected {HOURS_PER_YEAR}"
        )
        return system.reshape(n_hours, INTERVALS_PER_HOUR).mean(axis=1)

    fuels = {}
    for fuel, hsl_csv, curt_csv in (
        (
            "wind",
            "ercotWindHSLByPlant-2023.csv",
            "ercotWindCurtailmentByPlant-2023.csv",
        ),
        (
            "solar",
            "ercotSolarHSLByPlant-2023.csv",
            "ercotSolarCurtailmentByPlant-2023.csv",
        ),
    ):
        hsl = hourly_sum(hsl_csv)
        curt = hourly_sum(curt_csv)
        gen = np.minimum(np.clip(hsl - curt, 0.0, None), hsl)
        fuels[fuel] = {"hsl": hsl, "gen": gen}

    return _assemble_frame(fuels)


def _assemble_frame(fuels: dict[str, dict[str, np.ndarray]]) -> pd.DataFrame:
    """Return the output frame from per-fuel ``{"gen": ..., "hsl": ...}``."""
    out = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "wind_gen_mw": fuels["wind"]["gen"],
            "wind_hsl_mw": fuels["wind"]["hsl"],
            "solar_gen_mw": fuels["solar"]["gen"],
            "solar_hsl_mw": fuels["solar"]["hsl"],
        }
    )
    # Calendar month per hour for the monthly curtailment breakdown, on the
    # fixed non-leap clock shared by every model year.
    out["month"] = _MONTH_OF_HOUR
    return out


# ---------------------------------------------------------------------------
# NP6 upload ingestion (2024+)
# ---------------------------------------------------------------------------

# Column-name fragments identifying a report's fuel when the filename does
# not: the wind reports carry STWPF/WGRPP forecast columns, the solar
# reports STPPF/PVGRPP.
_WIND_SIGNATURES = ("STWPF", "WGRPP")
_SOLAR_SIGNATURES = ("STPPF", "PVGRPP")

# Candidate single-column interval timestamps (5-minute report family).
_TIMESTAMP_COLUMNS = (
    "SCED_TIMESTAMP",
    "SCED_TIME_STAMP",
    "INTERVAL_ENDING",
    "TIME_STAMP",
    "TIMESTAMP",
    "DATETIME",
)


def _np6_files(year: int) -> list[Path]:
    """Return candidate NP6 upload files for ``year`` (csv or zip)."""
    roots = [NP6_DIR, NP6_DIR / str(year)]
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if path.suffix.lower() in (".csv", ".zip") and path.is_file():
                files.append(path)
    return files


def _read_csvs(path: Path) -> list[tuple[str, pd.DataFrame]]:
    """Read ``path`` into ``(name, frame)`` pairs, expanding zips of CSVs.

    ERCOT's monthly NP6 download is a zip of zips: one outer zip per month,
    each entry itself a per-posting zip (ERCOT posts a new rolling-window
    report roughly hourly) containing exactly one CSV. This recurses through
    nested zip entries to any depth so both that archive shape and a flat
    zip-of-CSVs are handled identically.
    """
    if path.suffix.lower() == ".csv":
        return [(path.name, pd.read_csv(path))]

    out: list[tuple[str, pd.DataFrame]] = []

    def _walk(zf: zipfile.ZipFile, prefix: str) -> None:
        for info in zf.infolist():
            name = f"{prefix}:{info.filename}"
            if info.filename.lower().endswith(".csv"):
                with zf.open(info) as fh:
                    out.append((name, pd.read_csv(io.BytesIO(fh.read()))))
            elif info.filename.lower().endswith(".zip"):
                with zf.open(info) as fh:
                    with zipfile.ZipFile(io.BytesIO(fh.read())) as inner_zf:
                        _walk(inner_zf, name)

    with zipfile.ZipFile(path) as zf:
        _walk(zf, path.name)
    return out


def _fuel_of(name: str, columns: list[str]) -> str | None:
    """Identify a report's fuel from its filename or column signature."""
    lowered = name.lower()
    if "wind" in lowered or "wpp" in lowered:
        return "wind"
    if "solar" in lowered or "spp" in lowered or "pvgr" in lowered:
        return "solar"
    joined = " ".join(columns)
    if any(sig in joined for sig in _WIND_SIGNATURES):
        return "wind"
    if any(sig in joined for sig in _SOLAR_SIGNATURES):
        return "solar"
    return None


def _pick_column(
    columns: list[str], require: tuple[str, ...], exclude: tuple[str, ...] = ()
) -> str | None:
    """Return the first column containing every ``require`` fragment."""
    for col in columns:
        if all(r in col for r in require) and not any(e in col for e in exclude):
            return col
    return None


def _prevailing_to_standard(ts: pd.Series, dst_flag: pd.Series | None) -> pd.Series:
    """Convert Central-*Prevailing*-Time report stamps to the fixed CST clock.

    ERCOT market reports are stamped in Central Prevailing Time (CPT): the
    labels jump forward one hour at the DST spring transition (HE 3 absent on
    the transition day) and repeat one hour at fall-back (HE 2 twice, the
    second occurrence flagged ``DSTFLAG == 'Y'``). The model's fixed non-leap
    8760-hour clock — and the EIA-930 demand/renewable series the dispatch
    joins these bounds against — is local **standard** time (CST, UTC-6, no
    DST), so CPT labels placed on it unconverted land one hour late for the
    entire mid-Mar–early-Nov DST window. That defect put the 2024/25 wind and
    solar potential one hour late through every scarcity season (verified
    against EIA-930: Jan best lag 0 / Jul best lag +1, r = 1.0000 at both —
    the same series, shifted), handing the dispatch multi-GW phantom solar
    potential in the post-sunset scarcity hours.

    ``dst_flag`` disambiguates the repeated fall-back hour (``'Y'`` = second
    occurrence, already back on CST). Without a flag column the ambiguous
    repeat and any nonexistent spring-forward stamp become ``NaT`` (dropped
    upstream) rather than guessed.
    """
    if dst_flag is not None:
        # True = first occurrence (DST still in effect) for the repeated hour.
        ambiguous = dst_flag.astype(str).str.strip().str.upper().ne("Y").to_numpy()
    else:
        ambiguous = "NaT"
    local = ts.dt.tz_localize("US/Central", ambiguous=ambiguous, nonexistent="NaT")
    # Etc/GMT+6 is fixed UTC-6 (POSIX sign convention) == CST year-round.
    return local.dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)


def _report_timestamps(name: str, df: pd.DataFrame) -> pd.Series:
    """Return a report frame's hourly stamps on the model's fixed CST clock.

    ``df`` must already carry stripped/upper-cased column names. Handles both
    report layouts: hourly ``DELIVERY_DATE`` + ``HOUR_ENDING`` (with a DST
    flag for the repeated fall-back hour) and the 5-minute single
    interval-timestamp column. Timestamps are Central Prevailing Time in both
    and are converted via :func:`_prevailing_to_standard`.

    Raises:
        ValueError: when no timestamp column can be found.
    """
    columns = list(df.columns)
    dst_flag = df["DSTFLAG"] if "DSTFLAG" in columns else None

    if "DELIVERY_DATE" in columns and "HOUR_ENDING" in columns:
        date = pd.to_datetime(df["DELIVERY_DATE"])
        # HOUR_ENDING is 1-24 (sometimes "HH:00"); hour-beginning = HE - 1.
        he = df["HOUR_ENDING"].astype(str).str.split(":").str[0].astype(int)
        return _prevailing_to_standard(
            date + pd.to_timedelta(he - 1, unit="h"), dst_flag
        )
    ts_col = next((c for c in _TIMESTAMP_COLUMNS if c in columns), None)
    if ts_col is None:
        raise ValueError(
            f"{name}: no DELIVERY_DATE/HOUR_ENDING pair and none of "
            f"{_TIMESTAMP_COLUMNS} present (columns: {columns[:8]}...)"
        )
    ts = pd.to_datetime(df[ts_col])
    # 5-minute stamps are interval-ending when the year's first stamp
    # does not sit on an hour boundary; shift by one second before
    # flooring so the interval lands in the hour it covers.
    if (ts.dt.minute != 0).any():
        ts = ts - pd.Timedelta(seconds=1)
    return _prevailing_to_standard(ts.dt.floor("h"), dst_flag)


def _parse_report(name: str, df: pd.DataFrame) -> pd.DataFrame:
    """Reduce one report frame to ``(ts, gen_mw, hsl_mw)`` rows on the CST clock.

    Handles both report families: the hourly NP4-732/737 layout
    (``DELIVERY_DATE`` + ``HOUR_ENDING``, with a DST flag for the repeated
    fall-back hour) and the 5-minute NP4-733/738 layout (a single interval
    timestamp column). Timestamps are Central Prevailing Time in both
    families and are converted to the model's fixed CST clock
    (:func:`_report_timestamps`). The GEN column is the system-wide
    actual; the HSL column is the system-wide actual HSL, preferred over the
    COP HSL when both are present (COP HSLs aggregate only On-Line resources'
    operating plans; the actual HSL is the telemetered potential).

    Raises:
        ValueError: when the timestamp, GEN or HSL column cannot be found.
    """
    df = df.rename(columns=lambda c: str(c).strip().upper())
    columns = list(df.columns)
    ts = _report_timestamps(name, df)

    gen_col = _pick_column(
        columns, ("ACTUAL", "SYSTEM"), exclude=("HSL",)
    ) or _pick_column(columns, ("SYSTEM_WIDE",), exclude=("HSL",))
    hsl_col = (
        _pick_column(columns, ("ACTUAL", "SYSTEM", "HSL"))
        or _pick_column(columns, ("SYSTEM", "HSL"), exclude=("COP",))
        or _pick_column(columns, ("SYSTEM", "HSL"))
        or _pick_column(columns, ("HSL",))
    )
    if gen_col is None or hsl_col is None:
        raise ValueError(
            f"{name}: could not locate system-wide GEN/HSL columns (columns: {columns})"
        )

    out = pd.DataFrame(
        {
            "ts": ts,
            "gen_mw": pd.to_numeric(df[gen_col], errors="coerce"),
            "hsl_mw": pd.to_numeric(df[hsl_col], errors="coerce"),
        }
    )
    # Forecast-only rows (the rolling future window of the hourly reports)
    # carry no actuals; drop them rather than treating them as telemetry. A
    # NaT ts is a CPT stamp that could not be placed on the CST clock (an
    # unflagged fall-back repeat / malformed spring-forward row) — dropped,
    # then covered by the overlapping rolling-window postings or interpolated.
    return out.dropna(subset=["ts", "gen_mw", "hsl_mw"])


# Per-region column prefix shared by every region-resolved NP6 report family
# (wind GEO NP4-742, solar GEO NP4-745, and the plain NP4-732 wind report's
# load-zone columns): the region vocabulary is the set of COP_HSL_<REGION>
# suffixes other than SYSTEM_WIDE.
_GEO_REGION_HSL_PREFIX = "COP_HSL_"


def _parse_report_regions(name: str, df: pd.DataFrame) -> pd.DataFrame | None:
    """Reduce one region-resolved report to long ``(ts, region, gen_mw, hsl_mw)``.

    Returns ``None`` when the report carries no per-region columns (the
    system-wide-only report families). Regions are the ``COP_HSL_<REGION>``
    suffixes other than ``SYSTEM_WIDE``; the delivered column is
    ``ACTUAL_<REGION>`` (wind GEO, 2024 load-zone wind) or ``GEN_<REGION>``
    (solar GEO, 2025 load-zone wind). The per-region potential is the
    report's COP HSL — the aggregated operating-plan HSLs of On-Line
    resources — because no NP6 family publishes a per-region *telemetered*
    actual HSL (the same limitation the system-wide series has for GEO-only
    years). Region names are emitted lower-cased, preserving the source
    vocabulary (``panhandle``/``coastal``/... for wind GEO,
    ``centerwest``/... for solar GEO, ``lz_west``/... for load-zone wind).
    """
    df = df.rename(columns=lambda c: str(c).strip().upper())
    columns = list(df.columns)
    regions = [
        c[len(_GEO_REGION_HSL_PREFIX) :]
        for c in columns
        if c.startswith(_GEO_REGION_HSL_PREFIX) and not c.endswith("SYSTEM_WIDE")
    ]
    if not regions:
        return None
    ts = _report_timestamps(name, df)
    parts: list[pd.DataFrame] = []
    for region in regions:
        gen_col = next(
            (c for c in (f"ACTUAL_{region}", f"GEN_{region}") if c in columns),
            None,
        )
        if gen_col is None:
            continue
        part = pd.DataFrame(
            {
                "ts": ts,
                "region": region.lower(),
                "gen_mw": pd.to_numeric(df[gen_col], errors="coerce"),
                "hsl_mw": pd.to_numeric(
                    df[f"{_GEO_REGION_HSL_PREFIX}{region}"], errors="coerce"
                ),
            }
        )
        # Same drop rules as _parse_report: forecast-only rows and
        # unplaceable CPT stamps carry no telemetry.
        parts.append(part.dropna(subset=["ts", "gen_mw", "hsl_mw"]))
    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


def _to_model_clock(rows: pd.DataFrame, year: int, fuel: str) -> pd.DataFrame:
    """Place ``(ts, gen_mw, hsl_mw)`` rows on the non-leap 8760-hour clock.

    Rows are filtered to ``year`` with Feb 29 dropped, then averaged by
    local ``(month, day, hour)`` — which collapses sub-hourly intervals and
    overlapping rolling-window postings (timestamps are already on the CST
    clock, so DST needs no handling here) — and reindexed onto the fixed
    non-leap hourly calendar. Any cited known-bad ERCOT source window
    (``_KNOWN_BAD_NP6_WINDOWS``) is then nulled out and refilled from the
    measured EIA-930 hourly delivered series (``gen`` and ``hsl`` both — a
    no-curtailment assumption for those hours, since the corrupt NP6 window
    carries no usable curtailment signal; EIA-930 is already this builder's
    delivered-total cross-check source). Linear interpolation is only valid
    for the scattered sub-day telemetry gaps it was written for — across a
    multi-day window it destroys the diurnal cycle outright (a night-bounded
    hole interpolates SOLAR to identically zero: the 2024-08-20..23 window
    shipped ~810 GWh of missing August solar and 17 phantom scarcity-tail
    hours before this fill existed). Remaining small holes are linearly
    interpolated as before.

    Raises:
        ValueError: when more than ``_MAX_GAP_HOURS`` hours are missing and
            unexplained by a cited known-bad window.
    """
    ts = rows["ts"]
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = rows[keep]
    grouped = rows.groupby([ts[keep].dt.month, ts[keep].dt.day, ts[keep].dt.hour])[
        ["gen_mw", "hsl_mw"]
    ].mean()
    grouped.index.names = ["month", "day", "hour"]

    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    full_index = pd.MultiIndex.from_arrays(
        [calendar.month, calendar.day, calendar.hour],
        names=["month", "day", "hour"],
    )
    aligned = grouped.reindex(full_index)

    known_bad = _known_bad_mask(full_index, year)
    aligned.loc[known_bad, ["gen_mw", "hsl_mw"]] = np.nan

    missing = aligned["gen_mw"].isna().to_numpy()
    unexplained = int((missing & ~known_bad).sum())
    if unexplained > _MAX_GAP_HOURS:
        raise ValueError(
            f"{year}: {unexplained} of {HOURS_PER_YEAR} hours missing after "
            f"aggregation (max {_MAX_GAP_HOURS}, beyond the "
            f"{int(known_bad.sum())} hours already excluded by a cited "
            "known-bad window) — the NP6 upload looks incomplete"
        )
    if known_bad.any():
        eia = load_eia_hourly_renewable_gen("ERCOT", year)
        if eia is None or fuel not in eia:
            raise ValueError(
                f"{year}: cited known-bad NP6 window needs the EIA-930 "
                f"ERCO hourly {fuel} series to fill it, and none is available"
            )
        fill = np.asarray(eia[fuel], dtype=float)[known_bad]
        aligned.loc[known_bad, "gen_mw"] = fill
        # No usable curtailment signal inside the corrupt source window:
        # carry the measured delivered MW as the potential too (HSL = GEN,
        # zero curtailment) rather than fabricating headroom.
        aligned.loc[known_bad, "hsl_mw"] = fill
    aligned = aligned.interpolate(limit_direction="both")
    return aligned.reset_index(drop=True)


def _interpolate_short_gaps(values: pd.Series, max_gap: int) -> pd.Series:
    """Linearly fill NaN runs of at most ``max_gap`` hours interior to coverage.

    Longer holes and the uncovered edges of a partial-year series stay NaN —
    interpolating across a month-scale hole would fabricate telemetry (a
    night-bounded hole interpolates solar to identically zero; see
    :func:`_to_model_clock`'s known-bad-window rationale).
    """
    missing = values.isna()
    if not missing.any():
        return values
    # Run length of each NaN run: consecutive NaNs after a non-NaN share a
    # group id under the cumulative count of non-NaN values.
    run_id = (~missing).cumsum()
    run_len = missing.groupby(run_id).transform("sum")
    fill = values.interpolate(limit_area="inside")
    out = values.copy()
    short = missing & (run_len <= max_gap)
    out[short] = fill[short]
    return out


def _region_to_model_clock(rows: pd.DataFrame, year: int) -> pd.DataFrame:
    """Place one region's ``(ts, gen_mw, hsl_mw)`` rows on the 8760-hour clock.

    Same ``(month, day, hour)`` averaging and non-leap reindex as
    :func:`_to_model_clock`, with two differences for the region-resolved
    report families: coverage may be partial (a vocabulary posted for only
    some months — e.g. the lone 2024-09 wind GEO upload — keeps NaN outside
    its covered span; only interior gaps of at most ``_MAX_GAP_HOURS`` are
    interpolated, never month-scale holes or uncovered edges), and cited
    known-bad source windows (``_KNOWN_BAD_NP6_WINDOWS``) are nulled without
    the system-wide EIA-930 fill — EIA-930 publishes no per-region series,
    so those hours simply stay missing.
    """
    ts = rows["ts"]
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = rows[keep]
    grouped = rows.groupby([ts[keep].dt.month, ts[keep].dt.day, ts[keep].dt.hour])[
        ["gen_mw", "hsl_mw"]
    ].mean()
    grouped.index.names = ["month", "day", "hour"]

    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    full_index = pd.MultiIndex.from_arrays(
        [calendar.month, calendar.day, calendar.hour],
        names=["month", "day", "hour"],
    )
    aligned = grouped.reindex(full_index)
    known_bad = _known_bad_mask(full_index, year)
    aligned.loc[known_bad, ["gen_mw", "hsl_mw"]] = np.nan
    for column in ("gen_mw", "hsl_mw"):
        aligned[column] = _interpolate_short_gaps(aligned[column], _MAX_GAP_HOURS)
    return aligned.reset_index(drop=True)


# Zonal-only extra roots: region-resolved GEO uploads parked as redundant for
# the SYSTEM-wide series (their months are already covered by the primary
# uploads, so they must not perturb the committed system-wide parquets) still
# contribute per-region rows the primary files lack.
_ZONAL_EXTRA_DIRS: tuple[Path, ...] = (NP6_DIR / "unused-redundant",)


def _zonal_extra_files() -> list[Path]:
    """Return candidate zonal-only upload files (csv or zip) from the
    redundant-for-system-wide drop zones (``_ZONAL_EXTRA_DIRS``)."""
    files: list[Path] = []
    for root in _ZONAL_EXTRA_DIRS:
        if not root.is_dir():
            continue
        for path in sorted(root.iterdir()):
            if path.suffix.lower() in (".csv", ".zip") and path.is_file():
                files.append(path)
    return files


def aggregate_np6_hourly(
    year: int,
) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Aggregate the year's NP6 uploads into ``(system, zonal)`` hourly frames.

    ``system`` is the system-wide 8760-hour output frame (``None``, with a
    data-needed message, when no usable wind+solar report files for ``year``
    are found under ``data/raw/ercot-hsl/np6/``). ``zonal`` is the long
    per-region frame (``hour``, ``fuel``, ``region``, ``gen_mw``,
    ``hsl_mw``; ``None`` when no upload carries per-region columns) built in
    the same pass from the region-resolved report families
    (:func:`_parse_report_regions`), plus any GEO uploads parked under the
    zonal-only extra roots (``_ZONAL_EXTRA_DIRS``) — those are redundant for
    the system-wide series and contribute region rows only.

    GEN is floored at zero, and HSL is floored at GEN: the reports'
    telemetry occasionally shows actual output a shade above the recorded
    potential, and flooring HSL (rather than capping GEN) preserves the
    delivered totals the EIA-930 cross-check validates while keeping
    reported curtailment ``HSL - GEN`` non-negative. The same flooring is
    applied per region (over covered hours) in the zonal frame.
    """
    per_fuel: dict[str, list[pd.DataFrame]] = {"wind": [], "solar": []}
    region_rows: dict[str, list[pd.DataFrame]] = {"wind": [], "solar": []}

    def _collect(path: Path, regions_only: bool) -> None:
        for name, raw in _read_csvs(path):
            fuel = _fuel_of(name, list(raw.columns.astype(str).str.upper()))
            if fuel is None:
                print(f"  skipping {name}: cannot identify wind vs solar")
                continue
            if not regions_only:
                parsed = _parse_report(name, raw)
                in_year = parsed[parsed["ts"].dt.year == year]
                if not in_year.empty:
                    per_fuel[fuel].append(in_year)
            regions = _parse_report_regions(name, raw)
            if regions is not None:
                r_in_year = regions[regions["ts"].dt.year == year]
                if not r_in_year.empty:
                    region_rows[fuel].append(r_in_year)

    for path in _np6_files(year):
        _collect(path, regions_only=False)
    for path in _zonal_extra_files():
        _collect(path, regions_only=True)

    missing = [f for f, frames in per_fuel.items() if not frames]
    if missing:
        np6 = (
            NP6_DIR.relative_to(REPO_ROOT)
            if NP6_DIR.is_relative_to(REPO_ROOT)
            else NP6_DIR
        )
        print(
            f"\n{year}: no NP6 {'/'.join(missing)} report data found under "
            f"{np6}/ — skipping.\n"
            "  Upload ERCOT wind/solar power-production reports covering the "
            "year\n"
            "  (NP4-732-CD/NP4-737-CD hourly actuals, or NP4-733-CD/"
            "NP4-738-CD 5-minute\n"
            "  actuals; csv or zip), then re-run. Curtailment is never "
            "fabricated from\n"
            "  delivered-generation data."
        )
        return None, None

    fuels: dict[str, dict[str, np.ndarray]] = {}
    for fuel, frames in per_fuel.items():
        hourly = _to_model_clock(pd.concat(frames, ignore_index=True), year, fuel)
        gen = np.clip(hourly["gen_mw"].to_numpy(dtype=float), 0.0, None)
        hsl = np.maximum(hourly["hsl_mw"].to_numpy(dtype=float), gen)
        fuels[fuel] = {"gen": gen, "hsl": hsl}
    return _assemble_frame(fuels), _assemble_zonal_frame(region_rows, year)


def _assemble_zonal_frame(
    region_rows: dict[str, list[pd.DataFrame]], year: int
) -> pd.DataFrame | None:
    """Return the long zonal frame (``hour``, ``fuel``, ``region``, ``gen_mw``,
    ``hsl_mw``) from collected per-region report rows, or ``None`` when no
    report carried per-region columns.

    Each ``(fuel, region)`` series is placed on the fixed 8760-hour clock
    with partial-year coverage preserved as NaN
    (:func:`_region_to_model_clock`); over covered hours GEN is floored at
    zero and HSL floored at GEN, matching the system-wide convention.
    """
    parts: list[pd.DataFrame] = []
    hours = np.arange(HOURS_PER_YEAR, dtype="int64")
    for fuel in ("wind", "solar"):
        frames = region_rows[fuel]
        if not frames:
            continue
        rows = pd.concat(frames, ignore_index=True)
        for region, sub in rows.groupby("region", sort=True):
            hourly = _region_to_model_clock(sub, year)
            gen = hourly["gen_mw"].to_numpy(dtype=float, copy=True)
            hsl = hourly["hsl_mw"].to_numpy(dtype=float, copy=True)
            covered = ~np.isnan(gen)
            if not covered.any():
                continue
            gen[covered] = np.clip(gen[covered], 0.0, None)
            hsl[covered] = np.maximum(hsl[covered], gen[covered])
            parts.append(
                pd.DataFrame(
                    {
                        "hour": hours,
                        "fuel": fuel,
                        "region": str(region),
                        "gen_mw": gen,
                        "hsl_mw": hsl,
                    }
                )
            )
    if not parts:
        return None
    return pd.concat(parts, ignore_index=True)


# ---------------------------------------------------------------------------
# Validation + output
# ---------------------------------------------------------------------------


def _eia_reference_twh(year: int) -> tuple[dict[str, float], str] | None:
    """Return ``(totals, source)`` for the EIA delivered cross-check.

    Prefers the EIA-923 totals in calibration_reference.json (the ERCOT-BA
    benchmark the backcasts calibrate against); falls back to the hardcoded
    Texas-wide approximations for years predating the reference file.
    """
    if REFERENCE_PATH.exists():
        ref = json.loads(REFERENCE_PATH.read_text())
        gen = (
            ref.get("isos", {})
            .get("ERCOT", {})
            .get(str(year), {})
            .get("generation_twh", {})
        )
        if "wind" in gen and "solar" in gen:
            totals = {"wind": float(gen["wind"]), "solar": float(gen["solar"])}
            return totals, "EIA-923 (calibration reference)"
    fallback = EIA_REFERENCE_TWH.get(year)
    if fallback is None:
        return None
    return fallback, "EIA-930 Texas-wide (approximate)"


def print_validation(df: pd.DataFrame, year: int) -> None:
    """Print annual totals, peaks, monthly curtailment and the EIA check.

    Args:
        df: The aggregated hourly DataFrame (including the ``month``
            column) from :func:`aggregate_umass_hourly` or
            :func:`aggregate_np6_hourly`.
        year: The calendar year the frame covers.
    """
    print(f"\n=== ERCOT {year} uncurtailed renewable potential (HSL) ===")
    print(f"Rows: {len(df)} (expected {HOURS_PER_YEAR})")

    for fuel in ("wind", "solar"):
        gen = df[f"{fuel}_gen_mw"]
        hsl = df[f"{fuel}_hsl_mw"]
        gen_twh = gen.sum() / 1e6
        hsl_twh = hsl.sum() / 1e6
        curt_pct = 100.0 * (1.0 - gen.sum() / hsl.sum())
        print(
            f"\n{fuel.capitalize()}:"
            f"\n  GEN  annual = {gen_twh:7.2f} TWh   peak = "
            f"{gen.max() / 1000:6.2f} GW"
            f"\n  HSL  annual = {hsl_twh:7.2f} TWh   peak = "
            f"{hsl.max() / 1000:6.2f} GW"
            f"\n  annual curtailment = {curt_pct:.2f}%"
        )

    print("\nMonthly curtailment rate (%):")
    print(f"  {'month':>5} {'wind':>8} {'solar':>8}")
    for month in range(1, 13):
        m = df[df["month"] == month]
        w = 100.0 * (1.0 - m["wind_gen_mw"].sum() / m["wind_hsl_mw"].sum())
        s = 100.0 * (1.0 - m["solar_gen_mw"].sum() / m["solar_hsl_mw"].sum())
        print(f"  {month:>5} {w:>8.2f} {s:>8.2f}")

    reference = _eia_reference_twh(year)
    if reference is None:
        print(
            "\nEIA cross-check skipped: no reference totals for "
            f"{year} (see data/raw/_validation-source/calibration_reference.json)."
        )
        return
    totals, source = reference
    print(f"\nEIA cross-check (delivered generation, vs {source}):")
    for fuel in ("wind", "solar"):
        gen_twh = df[f"{fuel}_gen_mw"].sum() / 1e6
        ref = totals[fuel]
        diff = 100.0 * (gen_twh - ref) / ref
        print(
            f"  {fuel:>5}: HSL-source {gen_twh:6.2f} TWh vs EIA "
            f"~{ref:.0f} TWh ({diff:+.1f}%)"
        )
    if source.startswith("EIA-930"):
        print(
            "  Note: EIA Texas-wide totals include SPP Panhandle wind outside"
            "\n  ERCOT, so the ERCOT-only nodal total is expected to run "
            "lower."
        )


# Complete region vocabularies per report family, for the sum-of-regions
# cross-check: when every region of a vocabulary has (near-)full coverage,
# the regions' delivered generation must reproduce the system-wide total.
_REGION_VOCABULARIES: dict[str, tuple[str, tuple[str, ...]]] = {
    "NP4-742 wind GEO": (
        "wind",
        ("panhandle", "coastal", "south", "west", "north"),
    ),
    "NP4-732 wind LZ": ("wind", ("lz_south_houston", "lz_west", "lz_north")),
    "NP4-745 solar GEO": (
        "solar",
        (
            "centerwest",
            "northwest",
            "farwest",
            "fareast",
            "southeast",
            "centereast",
        ),
    ),
}


def print_zonal_validation(
    zonal: pd.DataFrame, system: pd.DataFrame | None, year: int
) -> None:
    """Print per-region coverage/totals and the sum-of-regions cross-check.

    Args:
        zonal: The long zonal frame from :func:`_assemble_zonal_frame`.
        system: The system-wide frame from the same pass (``None`` skips the
            sum-of-regions vs system-wide comparison).
        year: The calendar year the frames cover.
    """
    print(f"\n=== ERCOT {year} per-region (zonal) HSL sidecar ===")
    print(
        f"  {'fuel':>5} {'region':>18} {'coverage':>9} {'GEN TWh':>9} "
        f"{'HSL TWh':>9} {'curt %':>7}"
    )
    for (fuel, region), sub in zonal.groupby(["fuel", "region"], sort=True):
        covered = sub["gen_mw"].notna()
        cov_pct = 100.0 * covered.mean()
        gen_twh = sub["gen_mw"].sum() / 1e6
        hsl_twh = sub["hsl_mw"].sum() / 1e6
        curt = 100.0 * (1.0 - gen_twh / hsl_twh) if hsl_twh > 0 else float("nan")
        print(
            f"  {fuel:>5} {region:>18} {cov_pct:>8.1f}% {gen_twh:>9.2f} "
            f"{hsl_twh:>9.2f} {curt:>7.2f}"
        )

    if system is None:
        return
    for family, (fuel, regions) in _REGION_VOCABULARIES.items():
        pivot = zonal[zonal["fuel"] == fuel].pivot(
            index="hour", columns="region", values="gen_mw"
        )
        if not set(regions).issubset(pivot.columns):
            continue
        block = pivot[list(regions)]
        full = block.notna().all(axis=1)
        if full.mean() < 0.99:
            continue
        region_sum = block.loc[full].sum().sum()
        system_sum = system.loc[full.to_numpy(), f"{fuel}_gen_mw"].sum()
        if system_sum > 0:
            ratio = region_sum / system_sum
            print(
                f"  {family}: sum-of-regions / system-wide delivered = "
                f"{ratio:.4f} (over {int(full.sum())} covered hours)"
            )


_NP6_SOURCE = (
    "ERCOT MIS wind/solar power production reports "
    "(NP4-732/733-CD wind, NP4-737/738-CD solar), uploaded to "
    "data/raw/ercot-hsl/np6/"
)


def _write_zonal(zonal: pd.DataFrame, year: int) -> None:
    """Write the zonal sidecar parquet for ``year``."""
    table = pa.Table.from_pandas(
        zonal[["hour", "fuel", "region", "gen_mw", "hsl_mw"]],
        preserve_index=False,
    )
    table = table.replace_schema_metadata(
        {
            "source": _NP6_SOURCE
            + " (region-resolved families: NP4-742/745-CD GEO reports and "
            "the NP4-732-CD load-zone columns)",
            "description": (
                f"ERCOT {year} per-region hourly wind/solar delivered "
                "generation (report actual) and COP-HSL potential "
                "(aggregated operating-plan HSLs of On-Line resources — no "
                "NP6 family publishes a per-region telemetered actual HSL), "
                "long format by (fuel, region). Region names preserve the "
                "source vocabulary: NP4-742 wind geographical regions "
                "(panhandle/coastal/south/west/north), NP4-745 solar "
                "geographical regions (centerwest/northwest/farwest/fareast/"
                "southeast/centereast), NP4-732 wind load zones "
                "(lz_south_houston/lz_west/lz_north). Hours outside a "
                "region's posted coverage are NaN — never interpolated "
                "across month-scale holes."
            ),
            "units": "MW (hourly-average; numerically equal to MWh per hour)",
            "year": str(year),
        }
    )
    path = zonal_out_file(year)
    pq.write_table(table, path)
    print(f"Wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.1f} KiB)")


def build_year(year: int, zonal_only: bool = False) -> bool:
    """Build and write one year's HSL parquet(s). Returns True on success.

    Any year prefers the authoritative ERCOT NP4-732/737 power-production
    reports (full-footprint published HSL) when an upload is present under
    ``np6/``. 2023 additionally falls back to the UMass nodal reconstruction
    when no NP6 upload exists — a partial-footprint source the renewables
    loader reconciles up to the EIA-930 delivered level (see
    ``renewables.hsl_potential_mw``); drop the published 2023 reports into
    ``np6/`` to supersede it and retire the reconciliation entirely.

    NP6 uploads carrying per-region columns additionally yield the zonal
    sidecar (:func:`zonal_out_file`); with ``zonal_only`` the system-wide
    parquet is left untouched and only the sidecar is (re)written — the
    UMass fallback carries no per-region data, so NP6 uploads are required
    and a region-less year returns ``False``.
    """
    df, zonal = aggregate_np6_hourly(year)
    if df is not None:
        source = _NP6_SOURCE
        description = (
            f"ERCOT {year} system-wide hourly wind/solar HSL (uncurtailed "
            "potential) and delivered generation, aggregated from ERCOT "
            "MIS power-production reports (system-wide actual GEN and HSL)."
        )
    elif year == UMASS_YEAR and not zonal_only:
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = clone_dataset(Path(tmp) / "nodal-curtailment-analysis")
            df = aggregate_umass_hourly(data_dir)
        source = UMASS_REPO_URL
        description = (
            "ERCOT 2023 system-wide hourly wind/solar HSL (uncurtailed "
            "potential) and delivered generation, aggregated from the "
            "UMass nodal-curtailment dataset (60-Day SCED Disclosure). "
            "Partial-footprint reconstruction — superseded by a published "
            "NP4-732/737 upload in np6/ when available."
        )
    else:
        return False

    if not zonal_only:
        print_validation(df, year)

        table = pa.Table.from_pandas(
            df[["hour", "wind_gen_mw", "wind_hsl_mw", "solar_gen_mw", "solar_hsl_mw"]],
            preserve_index=False,
        )
        table = table.replace_schema_metadata(
            {
                "source": source,
                "description": description,
                "units": "MW (hourly-average; numerically equal to MWh per hour)",
                "year": str(year),
            }
        )
        path = out_file(year)
        pq.write_table(table, path)
        print(
            f"\nWrote {path.relative_to(REPO_ROOT)} "
            f"({path.stat().st_size / 1024:.1f} KiB)"
        )

    if zonal is not None:
        print_zonal_validation(zonal, df, year)
        _write_zonal(zonal, year)
    elif zonal_only:
        print(
            f"\n{year}: NP6 uploads carry no per-region columns — no zonal "
            "sidecar written."
        )
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    """Build the requested ERCOT HSL hourly parquets."""
    parser = argparse.ArgumentParser(
        prog="build_ercot_hsl",
        description="Build ERCOT hourly wind/solar HSL (uncurtailed "
        "potential) parquets.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help="Years to build (default: %(default)s). 2023 downloads the "
        "UMass dataset; later years need NP6 report uploads under "
        "data/raw/ercot-hsl/np6/.",
    )
    parser.add_argument(
        "--zonal-only",
        action="store_true",
        help="(Re)write only the per-region zonal sidecar parquet, leaving "
        "the committed system-wide parquet untouched. Requires NP6 uploads "
        "with per-region columns (the UMass fallback has none).",
    )
    args = parser.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    built = [year for year in args.year if build_year(year, zonal_only=args.zonal_only)]
    skipped = sorted(set(args.year) - set(built))
    if skipped:
        print(f"\nSkipped (no source data): {skipped}")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
