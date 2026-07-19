"""Unified measured reserve-requirement loaders — per-ISO spec-table module.

This is the single home for the three per-ISO *measured* reserve-requirement
loaders that were previously siloed in ``data.nyiso_reserve_requirements``,
``data.neiso_reserve_requirements``, and ``data.miso_reserve_requirements``
(now thin facades that re-export from here). Each ISO's loader, module-level
constants, data source, and EXACT hard-error semantics are preserved
byte-for-byte — this is a code-motion consolidation (CLAUDE.md rules 23/25),
not a re-derivation. The per-ISO family mappings and sources are unchanged and
never merged into a generic default (rule 24).

Every loader returns ``{name: (hours,) float array of requirement MW}`` on the
model's non-leap 8760 hour clock, and hard-errors (never silently falls back to
the static requirements it replaces) when its measured source is absent — the
condition-varying requirement channel for the in-LP energy+reserve
co-optimization (``config.reserve_config``), activated per ISO by its
``ScenarioConfig`` flag (see :data:`RESERVE_REQUIREMENT_SPECS`). Measured
reserve *prices* are the validation target and are NEVER read here.

Per-ISO provenance and data contracts follow, verbatim from the original
modules.

============================================================================
NYISO — Measured NYISO hourly locational reserve-requirement series (issue #1344)
============================================================================

The condition-varying requirement channel for the NYISO in-LP energy+reserve
co-optimization (``config.reserve_config._nyiso_design``): each reserve
family's static published requirement is replaced, when
``ScenarioConfig.nyiso_dynamic_reserve_requirements`` is on, by the MEASURED
as-enforced hourly requirement NYISO actually scheduled into RTD/RTC for that
(region, product). The measured series is a market-design *input* (CLAUDE.md
rule #13 admissible: it regenerates for a forward year as the published static
base plus the published condition rules — thunderstorm alerts, gas
contingencies, largest-source changes — applied to forward states, and it
responds to changed conditions). The measured reserve *prices*
(``data/raw/NYISO-AS/NYISO_as_{rt,da}_{year}.csv``) are the validation target
and are NEVER read here.

Data contract (the Ask-B intake, ``docs/handoffs/nyiso-data-asks-2026-07.md``):

* ``data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{year}.csv``
* columns: ``Time Stamp`` (Eastern wall-clock, hour-beginning — the same
  convention as the processed AS price CSVs), ``region`` (``NYCA`` / ``East``
  / ``SENY`` / ``NYC``), ``product`` (``30min_total`` / ``10min_total`` /
  ``10min_spin``), ``requirement_mw``.
* sub-hourly rows are aggregated to the hour-beginning mean; each present
  (region, product) series must cover the full year (no silent gap-filling
  beyond the hour-mean aggregation).

The loader raises when the file is absent — the flag must never quietly solve
on the static requirements it claims to replace (no silent fallback,
CLAUDE.md rule #23's no-off-registry-channels spirit). A (region, product)
absent from the file keeps its static published value in the design (partial
coverage is expected: e.g. only the downstate regions may be measured).

============================================================================
NEISO — Measured ISO-NE hourly reserve-requirement series (NEISO Limb A)
============================================================================

The condition-varying requirement channel for the NEISO in-LP energy+reserve
co-optimization (``config.reserve_config._neiso_design``): each reserve
family's static published requirement is replaced, when
``ScenarioConfig.neiso_dynamic_reserve_requirements`` is on, by the MEASURED
as-enforced hourly requirement ISO-NE actually enforced in real time for that
(location, product) — the ISO Express "Hourly Reserve Requirements" report,
the exact ISO-NE analogue of the NYISO issue-#1344 Ask-B intake
(``data.nyiso_reserve_requirements``). The measured series is a market-design
*input* (CLAUDE.md rule #13 admissible: it regenerates for a forward year as
the published static base plus ISO-NE's published condition rules — largest
first/second contingency, cold-weather and gas-contingency events — applied
to forward states, and it responds to changed conditions). The measured
reserve *prices* are the validation target and are NEVER read here.

Data contract (the ``reserve-requirements`` clean datatype):

* raw: ``data/raw/NEISO-AS/requirements/requirements_<start>_<end>.csv``
  (gitignored window CSVs; ``scripts/data/fetch_neiso_reserve_requirements.py``
  regenerates them from the public report)
* clean: ``data/clean/reserve-requirements/NEISO/<year>/`` via
  ``scripts/data/curate_reserve_requirements.py`` (schema
  ``data/dictionary/schema/reserve-requirements.schema.yaml``)

The loader raises when the clean partition is absent — the flag must never
quietly solve on the static requirements it claims to replace (no silent
fallback; CLAUDE.md rule #23's no-off-registry-channels spirit). A family
absent from the measured mapping keeps its static published value in the
design (partial coverage is expected: the local reserve zones SWCT/CT/
NEMABSTN publish a 30-minute total with no in-LP family today).

============================================================================
MISO — Measured MISO hourly operating-reserve requirement series (Lane-2, miso-56)
============================================================================

The condition-varying requirement channel for the MISO in-LP energy+reserve
co-optimization (``config.reserve_config._miso_design``), the MISO analogue of
the NYISO issue-#1344 intake (``data.nyiso_reserve_requirements``): when
``ScenarioConfig.miso_measured_reserve_requirements`` is on, the market-wide
RBDC family's flat fleet-MSSC + regulating estimate and the South zonal
family's static within-zone-MSSC estimate are replaced by the MEASURED hourly
reserve MW MISO actually cleared, from the masked real-time cleared-offers
market report (``data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet``,
``scripts/data/fetch_miso_asm.py``).

The loader also emits a ``"MISO-Midwest"`` leg (cleared sum over the two
Midwest ASM regions {North, Central}) — the measured basis of the Midwest
sub-regional reserve-holding family (``ScenarioConfig.
miso_midwest_subregional_reserves``, the engagement-depth lane, miso-71). It is
the same measured-cleared construction, clock, and admissibility as the
market-wide and South legs; measured Midwest + measured South = measured
market by construction (the sum over regions IS the market leg).

Admissibility (CLAUDE.md rule #13): the cleared reserve MW is a measured
ancillary-service power reservation — a procurement *quantity*, never a
price — with a forward analogue: forecast years keep the existing
MSSC + regulating formula (the flag is backcast-only by construction, like
every measured overlay). Rule #14 makes the swap mandatory: the measured
series shows the flat market-wide estimate (fleet MSSC + 400 MW ≈ 3.4 GW)
overstates real procurement (~2.3-3.1 GW, hourly-varying with event-evening
increases), and the South static (within-zone MSSC ≈ 2.2 GW) overstates the
measured South reservation (~0.3-0.5 GW) several-fold — the within-zone-MSSC
reading of BPM-002 §3.3.2 fabricates ~1.8 GW of South withholding the real
market never held.

Known basis caveats (documented, not hidden):

* The series is *cleared* MW, not the requirement itself: in a genuine
  shortage interval cleared < requirement, so the requirement is understated
  in exactly those (rare — the IMM counts a handful of intervals per year)
  hours. MISO does not publish the historical hourly requirement series; the
  cleared series is the closest measured quantity. Quantified on the Midwest
  leg (miso-71 design §3): the cleared series dips to 957 MW (Jun-23/24-2025)
  and 851 MW (Jul-28/29-2025) against a ~2,165 MW 2025 mean — the deep-window
  event hours where cleared understates the true requirement. Any construction
  that undoes the dip (trailing-max smoothing, window-scoped floors) would be
  residual-fitting around a shortage and is refused (rules 1/13); the
  understatement is a ledgered lower-bound caveat, not "fixed" here.
* The report is real-time (the adopted basis). MISO DOES publish a day-ahead
  cleared-offers report at hourly grain (``YYYYMMDD_asm_da_co.zip``, per-unit
  RegMW/SpinMW/SuppMW/STRMW + MCPs by region, EST) — correcting the stale
  miso-56 caveat that claimed no hourly DA series exists. A DA-basis intake is
  a possible future refinement of the SAME cleared-basis family; the RT basis
  is retained as adopted (switching it is out of the miso-71 lane's scope — it
  would re-litigate miso-56 and change all three legs at once).
* Products summed are ``reg + spin + supp`` — the Market-wide Operating
  Reserve construct (regulating + contingency, BPM-002). Short-Term Reserve
  (``str``) is a separate 30-minute product outside the OR requirement and is
  deliberately excluded.

Clock: the source files are Hour-Ending 1-24, Eastern Standard Time
year-round (MISO market reports never observe DST) — the model's fixed
non-leap 8760 local-standard-time clock. A leap year's Feb 29 is dropped
(``data.eia_loader`` convention); small posting gaps (single missing
hours) are forward-filled and the loader hard-errors when coverage is
worse than ``_MAX_MISSING_HOURS``.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

# ==========================================================================
# NYISO — measured hourly locational reserve-requirement series (issue #1344)
# ==========================================================================

#: Drop zone for the Ask-B intake (docs/handoffs/nyiso-data-asks-2026-07.md).
NYISO_RESERVE_REQUIREMENTS_DIR: Path = RAW_DATA_DIR / "NYISO-AS" / "requirements"

#: (region, product) -> in-LP reserve family name (reserve_config._nyiso_design).
#: Keys mirror the published NYISO reserve regions/products the design builds
#: from NYISO_RCPF_PRODUCTS (NYCA tier) and NYISO_RCPF_LOCATIONAL (East ⊃ SENY
#: ⊃ NYC); the synchronised-reserve scaffold families (nyc_spin_*) are
#: deliberately absent — they have no published measured requirement series.
FAMILY_BY_REGION_PRODUCT: dict[tuple[str, str], str] = {
    ("NYCA", "30min_total"): "nyca_30min_total",
    ("NYCA", "10min_total"): "nyca_10min_total",
    ("NYCA", "10min_spin"): "nyca_10min_spin",
    ("East", "10min_total"): "east_10min_total",
    ("SENY", "30min_total"): "seny_30min_total",
    ("NYC", "30min_total"): "nyc_30min_total",
    ("NYC", "10min_total"): "nyc_10min_total",
}


def requirements_path(year: int) -> Path:
    """Return the on-disk path of the measured requirement CSV for ``year``."""
    return NYISO_RESERVE_REQUIREMENTS_DIR / f"NYISO_reserve_requirements_{year}.csv"


def load_nyiso_reserve_requirements(
    year: int,
    hours: int,
    path: Path | None = None,
) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve-requirement series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series is trimmed/validated
            to exactly this many hour-beginning values.
        path: Optional explicit CSV path (tests); defaults to
            :func:`requirements_path`.

    Returns:
        ``{family_name: (hours,) float array of requirement MW}`` for every
        (region, product) present in the file, keyed per
        :data:`FAMILY_BY_REGION_PRODUCT`.

    Raises:
        FileNotFoundError: The intake file is absent — the
            ``nyiso_dynamic_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static requirements (see the Ask-B
            data ask, ``docs/handoffs/nyiso-data-asks-2026-07.md``).
        ValueError: Unknown (region, product) rows, or a present series that
            does not cover the full horizon.
    """
    src = path if path is not None else requirements_path(year)
    if not src.exists():
        raise FileNotFoundError(
            f"nyiso_dynamic_reserve_requirements=True but the measured "
            f"requirement series is absent: {src}. This is the Ask-B external "
            f"data intake (docs/handoffs/nyiso-data-asks-2026-07.md); the flag "
            f"must not solve on the static requirements it claims to replace."
        )

    df = pd.read_csv(src)
    required_cols = {"Time Stamp", "region", "product", "requirement_mw"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"{src}: missing column(s) {sorted(missing)}; expected "
            f"{sorted(required_cols)}"
        )

    unknown = set(map(tuple, df[["region", "product"]].drop_duplicates().values))
    unknown -= set(FAMILY_BY_REGION_PRODUCT)
    if unknown:
        raise ValueError(
            f"{src}: unknown (region, product) pairs {sorted(unknown)}; known "
            f"pairs are {sorted(FAMILY_BY_REGION_PRODUCT)}"
        )

    df = df.copy()
    ts = pd.to_datetime(df["Time Stamp"])
    # Hour-beginning aggregation: sub-hourly postings mean to their hour, the
    # same convention scripts/data/process_nyiso_as.py uses for the price CSVs.
    df["_hour"] = ts.dt.floor("h")

    out: dict[str, np.ndarray] = {}
    for (region, product), grp in df.groupby(["region", "product"], sort=False):
        family = FAMILY_BY_REGION_PRODUCT[(str(region), str(product))]
        hourly = grp.groupby("_hour", sort=True)["requirement_mw"].mean().to_numpy()
        if hourly.shape[0] < hours:
            raise ValueError(
                f"{src}: series {region}/{product} covers {hourly.shape[0]} "
                f"hours < horizon {hours} — a present series must cover the "
                f"full year (no silent gap-filling)."
            )
        series = np.asarray(hourly[:hours], dtype=float)
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(
                f"{src}: series {region}/{product} contains non-finite or "
                f"negative requirement values."
            )
        out[family] = series
    return out


# ==========================================================================
# NEISO — measured ISO-NE hourly reserve-requirement series (Limb A)
# ==========================================================================

#: (location, product) -> in-LP reserve family name
#: (reserve_config._neiso_design / NEISO_RCPF_PRODUCTS). ROS is the
#: system-wide requirement row; the local reserve zones (SWCT, CT, NEMABSTN)
#: are deliberately absent — the NEISO design carries no locational reserve
#: families (the model's 4-zone topology has no SWCT boundary).
FAMILY_BY_LOCATION_PRODUCT: dict[tuple[str, str], str] = {
    ("ROS", "30min_total"): "ne_30min_total",
    ("ROS", "10min_total"): "ne_10min_total",
    ("ROS", "10min_spin"): "ne_10min_spin",
}


def _import_clean_io():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the
    repo root is put on ``sys.path`` the way the curation scripts do. Done
    lazily so only the opt-in dynamic-requirements path pays the cost.
    """
    import sys

    from market_sim.config import paths

    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io  # noqa: E402

    return clean_io


def load_neiso_reserve_requirements(year: int, hours: int) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve-requirement series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series is trimmed/validated
            to exactly this many values on the model's hour clock (row 0 =
            the year's first local hour, UTC-ordered, local Feb 29 dropped in
            a leap year — the ``eia_loader`` convention).

    Returns:
        ``{family_name: (hours,) float array of requirement MW}`` for every
        (location, product) in :data:`FAMILY_BY_LOCATION_PRODUCT`.

    Raises:
        FileNotFoundError: The clean partition is absent — the
            ``neiso_dynamic_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static requirements. Regenerate
            with ``scripts/data/fetch_neiso_reserve_requirements.py`` then
            ``scripts/data/curate_reserve_requirements.py``.
        ValueError: A mapped series is missing from the clean data, does not
            cover the full horizon, or contains non-finite/negative values.
    """
    clean_io = _import_clean_io()
    if not clean_io.clean_exists("reserve-requirements", iso="NEISO", year=int(year)):
        raise FileNotFoundError(
            f"neiso_dynamic_reserve_requirements=True but the measured "
            f"requirement series is absent: no clean partition "
            f"reserve-requirements/NEISO/{year}. Regenerate raw with "
            f"scripts/data/fetch_neiso_reserve_requirements.py, then curate with "
            f"scripts/data/curate_reserve_requirements.py — the flag must not "
            f"solve on the static requirements it claims to replace."
        )
    df = clean_io.read_clean("reserve-requirements", iso="NEISO", year=int(year))

    # Model hour clock: UTC-sorted local year with a leap year's local
    # Feb 29 dropped (see data.eia_loader._eia_hourly_frame).
    local = df["interval_start_local"]
    df = df[~((local.dt.month == 2) & (local.dt.day == 29))]

    out: dict[str, np.ndarray] = {}
    for (location, product), family in FAMILY_BY_LOCATION_PRODUCT.items():
        sub = df[(df["location"] == location) & (df["product"] == product)]
        sub = sub.sort_values("interval_start_utc")
        series = sub["requirement_mw"].to_numpy(dtype=float)
        if series.shape[0] < int(hours):
            raise ValueError(
                f"reserve-requirements NEISO {year}: series {location}/"
                f"{product} covers {series.shape[0]} hours < horizon {hours} "
                f"— a mapped series must cover the full year (no silent "
                f"gap-filling)."
            )
        series = series[: int(hours)]
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(
                f"reserve-requirements NEISO {year}: series {location}/"
                f"{product} contains non-finite or negative values."
            )
        out[family] = series
    return out


# ==========================================================================
# MISO — measured hourly operating-reserve requirement series (Lane-2, miso-56)
# ==========================================================================

#: Source directory of the fetched ASM rollups (fetch_miso_asm.py).
MISO_AS_DIR: Path = RAW_DATA_DIR / "MISO-AS"

#: Products summed into the Market-wide Operating Reserve requirement
#: (regulating + contingency = reg + spin + supp; STR deliberately excluded —
#: a separate 30-minute product outside the OR construct).
OR_PRODUCTS: tuple[str, ...] = ("reg", "spin", "supp")

#: Model zone name of the MISO-South zonal reserve family
#: (reserve_config.MISO_ZONAL_RESERVE_DEFAULT_ZONES) and its source region
#: label in the cleared-offers report.
SOUTH_ZONE: str = "MISO-South"
SOUTH_REGION: str = "South"

#: The two ASM cleared-offers regions that make up the Midwest sub-region
#: (reserve_config.MISO_MIDWEST_ZONES): North + Central. The Midwest leg's
#: measured OR reservation is their cleared reg+spin+supp sum — the basis of
#: the miso_midwest_subregional_reserves family (miso-71 design §2a).
MIDWEST_REGIONS: tuple[str, ...] = ("North", "Central")
MIDWEST_ZONE: str = "MISO-Midwest"

#: Hard error above this many missing hours per series (posting gaps in the
#: source are 1-2 hours/year; anything larger is a data problem, not a gap).
_MAX_MISSING_HOURS: int = 168


def cleared_mw_path(year: int) -> Path:
    """Return the on-disk path of the cleared-reserve parquet for ``year``."""
    return MISO_AS_DIR / f"asm_rt_cleared_mw_{year}.parquet"


def _to_model_hour(dates: pd.Series, hour_end: pd.Series, year: int) -> np.ndarray:
    """Map (date, HE 1-24 EST) rows onto the fixed non-leap 8760 clock.

    Returns the hour-of-year index per row; a leap year's Feb 29 rows map to
    ``-1`` (dropped), matching the ``data.eia_loader`` non-leap convention.
    """
    ts = pd.to_datetime(dates)
    doy = ts.dt.dayofyear.to_numpy(dtype=int)
    if calendar.isleap(year):
        feb29 = (ts.dt.month == 2) & (ts.dt.day == 29)
        # Days after Feb 29 shift back one slot on the non-leap clock.
        doy = np.where(ts.dt.dayofyear.to_numpy() > 60, doy - 1, doy)
        doy = np.where(feb29.to_numpy(), 0, doy)  # sentinel, dropped below
    idx = (doy - 1) * 24 + (hour_end.to_numpy(dtype=int) - 1)
    if calendar.isleap(year):
        idx = np.where(feb29.to_numpy(), -1, idx)
    return idx


def load_miso_reserve_requirements(
    year: int,
    hours: int,
    path: Path | None = None,
) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series covers exactly this
            many hours of the fixed non-leap clock.
        path: Optional explicit parquet path (tests); defaults to
            :func:`cleared_mw_path`.

    Returns:
        ``{"market": (hours,) array, "MISO-South": (hours,) array,
        "MISO-Midwest": (hours,) array}`` — the measured market-wide (all
        regions summed), South-region, and Midwest (North+Central summed) OR
        reservation MW (``reg + spin + supp``). By construction
        ``MISO-Midwest + MISO-South == market`` in every fully-covered hour.

    Raises:
        FileNotFoundError: The intake parquet is absent — the
            ``miso_measured_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static estimates it replaces.
        ValueError: Missing columns/products, or coverage gaps larger than
            the posting-gap tolerance.
    """
    src = path if path is not None else cleared_mw_path(year)
    if not src.exists():
        raise FileNotFoundError(
            f"miso_measured_reserve_requirements=True but the measured cleared-"
            f"reserve series is absent: {src}. Regenerate with "
            f"scripts/data/fetch_miso_asm.py --years {year}; the flag must not solve "
            f"on the static estimates it claims to replace."
        )

    df = pd.read_parquet(src)
    required_cols = {"date", "hour_end_est", "region", "product", "cleared_mw"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"{src}: missing column(s) {sorted(missing)}; expected "
            f"{sorted(required_cols)}"
        )
    df = df[df["product"].isin(OR_PRODUCTS)].copy()
    if df.empty:
        raise ValueError(f"{src}: no OR product rows ({OR_PRODUCTS}) present")

    df["_hour"] = _to_model_hour(df["date"], df["hour_end_est"], year)
    df = df[df["_hour"] >= 0]  # drop a leap year's Feb 29

    out: dict[str, np.ndarray] = {}
    for key, sub in (
        ("market", df),
        (SOUTH_ZONE, df[df["region"] == SOUTH_REGION]),
        (MIDWEST_ZONE, df[df["region"].isin(MIDWEST_REGIONS)]),
    ):
        series = np.full(int(hours), np.nan)
        hourly = sub.groupby("_hour")["cleared_mw"].sum()
        idx = hourly.index.to_numpy(dtype=int)
        keep = idx < int(hours)
        series[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
        n_missing = int(np.isnan(series).sum())
        if n_missing > _MAX_MISSING_HOURS:
            raise ValueError(
                f"{src}: {key} series missing {n_missing} hours "
                f"(> {_MAX_MISSING_HOURS} tolerance) — a present series must "
                f"cover the year up to posting gaps."
            )
        if n_missing:
            # Forward/backward fill single posting gaps (pandas limit-free
            # ffill then bfill for a leading gap) — documented tolerance.
            s = pd.Series(series).ffill().bfill()
            series = s.to_numpy(dtype=float)
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(f"{src}: {key} series non-finite or negative")
        out[key] = series
    return out


# ==========================================================================
# Per-ISO spec table
# ==========================================================================


@dataclass(frozen=True)
class ReserveRequirementSpec:
    """One ISO's measured reserve-requirement channel.

    Attributes:
        iso: ISO identifier.
        loader: The per-ISO loader — ``loader(year, hours)`` returns
            ``{family_or_leg_name: (hours,) MW array}`` for the measured
            series (each loader also accepts extra test-only params such as
            ``path=``).
        flag: The ``ScenarioConfig`` boolean field that activates the measured
            series in the in-LP co-optimization (``config.reserve_config``).
        source: Human-readable provenance of the measured input.
    """

    iso: str
    loader: Callable[..., dict[str, np.ndarray]]
    flag: str
    source: str


#: Per-ISO measured reserve-requirement registry — the single introspectable
#: index over the three loaders housed above (replacing the siloed
#: data.{nyiso,neiso,miso}_reserve_requirements modules, now facades). The
#: solve path (config.reserve_config._{nyiso,neiso,miso}_design) still imports
#: each loader by name; this table is the registry for data-dictionary /
#: ISO-add introspection and the :func:`load_reserve_requirements` dispatcher.
RESERVE_REQUIREMENT_SPECS: dict[str, ReserveRequirementSpec] = {
    "NYISO": ReserveRequirementSpec(
        iso="NYISO",
        loader=load_nyiso_reserve_requirements,
        flag="nyiso_dynamic_reserve_requirements",
        source=(
            "NYISO issue-#1344 Ask-B measured hourly locational requirement CSV "
            "(data/raw/NYISO-AS/requirements/)."
        ),
    ),
    "NEISO": ReserveRequirementSpec(
        iso="NEISO",
        loader=load_neiso_reserve_requirements,
        flag="neiso_dynamic_reserve_requirements",
        source=(
            "ISO-NE Express Hourly Reserve Requirements, reserve-requirements "
            "clean datatype (data/clean/reserve-requirements/NEISO/)."
        ),
    ),
    "MISO": ReserveRequirementSpec(
        iso="MISO",
        loader=load_miso_reserve_requirements,
        flag="miso_measured_reserve_requirements",
        source=(
            "MISO real-time ASM cleared-offers OR reservation "
            "(data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet)."
        ),
    ),
}


def load_reserve_requirements(iso: str, year: int, hours: int) -> dict[str, np.ndarray]:
    """Dispatch to the per-ISO measured reserve-requirement loader.

    A thin registry lookup over :data:`RESERVE_REQUIREMENT_SPECS`; the per-ISO
    ``load_<iso>_reserve_requirements`` functions are the canonical
    implementations (and what ``config.reserve_config`` imports by name for the
    solve path). Additive convenience for callers that dispatch by ISO.

    Args:
        iso: ISO identifier (must be a key of :data:`RESERVE_REQUIREMENT_SPECS`).
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T.

    Returns:
        ``{name: (hours,) float array of requirement MW}`` — the ISO's measured
        series (family- or leg-keyed per that ISO's loader).

    Raises:
        KeyError: ``iso`` has no measured reserve-requirement channel.
    """
    return RESERVE_REQUIREMENT_SPECS[iso].loader(int(year), int(hours))
