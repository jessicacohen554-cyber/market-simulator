"""Renewable resource profiles (wind and solar capacity factors).

Derives hourly capacity-factor (CF) profiles for wind and solar from the
EIA-930 normalized generation distributions. The EIA ``value`` column for a
given ``(iso, year, fuel)`` group is a probability distribution that sums to
roughly 1.0 across the 8760 hours of the year; multiplying by the fleet's
annual-average CF and by the hour count rescales it into an hourly CF series
whose mean equals that annual-average CF.

Because the EIA generation series reflect *delivered* output, they already
embed real-world curtailment (roughly 5% for wind and solar in ERCOT and
CAISO), so for most ISO-years the derived CF profiles inherit that
curtailment and the dispatch does not separately re-curtail.

The exceptions are the backcasts with an hourly uncurtailed-potential (HSL)
dataset, where the CF profile is built from that instead (see
:func:`_hsl_cf_profile`) so the dispatch is handed the *uncurtailed*
potential and re-curtails wind and solar under the modeled transmission
limits, and the calibration report can compare the modeled curtailment
against the reported ``HSL - GEN``:

* ERCOT — years with a built NP6 HSL parquet
  (scripts/build_ercot_hsl.py; 2023 from the UMass 60-Day-SCED dataset,
  2024+ from uploaded ERCOT NP6 wind/solar production reports);
* CAISO 2023/2024 — EIA-930 delivered generation plus CAISO's reported
  5-minute wind/solar curtailment (scripts/build_caiso_hsl.py). CAISO solar
  curtailment is multi-TWh, so without this the model cannot re-curtail.
  CAISO years without a full-year curtailment workbook (2025 today) keep
  the delivered EIA-930 profile fallback — see the data-needed marker in
  scripts/build_caiso_hsl.py.

All other ISOs use the delivered ``<BA> hourly`` net-generation series from
the EIA-930 hourly extract (see :func:`_eia_hourly_cf_profile`).  For NEISO
in particular, ISO-NE reported curtailment is sub-1 % of potential, so the
delivered EIA-930 ``ISNE hourly`` series is the documented default and no
uncurtailed-potential (HSL) parquet is built.  NEISO wind/solar profiles are
zone-shaped by EIA-860 plant-location capacity shares: ME/NH/VT onshore wind
concentrates in the North zone; CT and MA/RI utility solar distribute across
Connecticut and Central.

**NEISO solar accounting note** — ISO-NE's extensive net-metered solar
(rooftop + small commercial) is reported as a *reduction in net load* rather
than as explicit generation, so the EIA-930 ``ISNE hourly NG: SUN`` column
captures only grid-scale wholesale solar (~800–1 600 GWh/yr) while the
EIA-860 operable schedule includes all utility-scale plants ≥ 1 MW
(including distribution-connected, ~2.7 GW in 2023).  As a result the
mean CF of the EIA-930-derived solar profile relative to the EIA-860 total
installed capacity is approximately 0.04 — well below the physical
utility-PV CF of ~0.15 — but the dispatch energy balance is correct because
the EIA-930 net-load demand series already excludes BTM solar.  The wind
profile is unaffected (all NEISO wind is grid-connected), and its mean CF
benchmarks against the EIA-923 fleet average (~0.30).

If ISO-NE ever publishes granular curtailment data, a dedicated HSL parquet
can be built following the CAISO pattern in scripts/build_caiso_hsl.py — see
:func:`_hsl_file` for the data-needed marker.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    HOURS_PER_YEAR,
    OFFSHORE_WIND_MIN_CF,
    OFFSHORE_WIND_PARAMS,
    OFFSHORE_WIND_SMOOTHING_HOURS,
    RENEWABLE_AVG_CF,
    RENEWABLE_INSTALLED_MW,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import (
    DATA_DIR,
    load_eia_hourly_renewable_gen,
    load_generation_profiles,
)
from market_sim.data.fleet import (
    EIA_860_DIR,
    FUEL_TYPE_MAP,
    FleetArrays,
    _hour_to_month_index,
)

# Capacity factors are physically bounded to the closed interval [0, 1].
_CF_MIN: float = 0.0
_CF_MAX: float = 1.0

# Renewable fuels for which CF profiles are derived, matching the ``fuel``
# values in the EIA-930 generation-profiles parquet.
_RENEWABLE_FUELS: tuple[str, str] = ("wind", "solar")

# Fallback single-zone allocation, by ISO and fuel. Used only when EIA-860
# plant-location data is unavailable for the ISO; otherwise capacity is
# distributed across zones from EIA-860 (see :func:`_eia860_zone_shares`).
# Each technology is assigned to the zone holding the bulk of its installed
# capacity; every other zone receives an all-zero profile.
# Source: ERCOT CDR Dec 2024 (West Texas wind/solar belt; offshore wind off
# the Houston/Galveston coast). CAISO zones follow the EIA-860 capacity
# distribution: onshore wind concentrates in ZP26 (the Tehachapi/Kern belt,
# ~52% of CISO wind), solar in SP15 (the southern desert, ~63% of CISO
# solar), and the BOEM offshore-wind lease areas (Morro Bay / Humboldt) sit
# on the NP15 coast.
RENEWABLE_ZONE_ALLOCATION: dict[str, dict[str, str]] = {
    "ERCOT": {"wind": "West", "solar": "West", "offshore_wind": "Houston"},
    "CAISO": {
        "wind": "ZP26",
        "solar": "SP15",
        "offshore_wind": "NP15",
    },
    # Eastern-ISO siting zones: Tier 3, the zone holding the bulk of each
    # technology's current fleet / pipeline. PJM wind sits in the western
    # (ComEd, IL/IN belt) zone, PJM solar in Dominion (the VA build wave),
    # PJM offshore off the NJ coast (EMAAC). MISO wind is the IA/MN belt
    # (North); SPP wind the OK/KS belt (South). NYISO utility wind/solar
    # are upstate-west; offshore is the NY Bight off Long Island. NEISO
    # wind is Maine (North), solar CT, offshore the MA/RI lease areas.
    "PJM": {
        "wind": "PJM_ComEd",
        "solar": "PJM_Dominion",
        "offshore_wind": "PJM_EMAAC",
    },
    "MISO": {"wind": "MISO-North", "solar": "MISO-Central"},
    "SPP": {"wind": "SPP-South", "solar": "SPP-South"},
    "NYISO": {
        "wind": "Upstate_West",
        "solar": "Upstate_West",
        "offshore_wind": "Long_Island",
    },
    "NEISO": {
        "wind": "North",
        "solar": "Connecticut",
        "offshore_wind": "Boston",
    },
}

# EIA-860 operable wind/solar generator parquets, used to distribute
# renewable capacity across ISO zones and to build the vintage monthly
# capacity ramp from each plant's commercial-operation date.
# Source: EIA-860 2024 (Generator_Operable, wind and solar schedules).
_EIA860_OPERABLE_FILES: dict[str, str] = {
    "wind": "eia860_wind_operable.parquet",
    "solar": "eia860_solar_operable.parquet",
}

# Proposed-plant file with planned commercial-operation dates. Used to
# include future-year wind/solar additions that are not yet in the
# operable schedule (e.g. 2025 plants not present in the Sep-2024
# operable snapshot). Filtered to high-confidence statuses below.
_EIA860_PROPOSED_FILE: str = "eia860_generator_proposed.parquet"

# EIA-860 status codes treated as high-confidence (likely to come online
# by the planned effective date). ``U`` / ``V`` are under construction
# (<50% / >50% complete), ``TS`` is test-mode pre-commercial, ``P`` is
# planned-with-permits. ``L`` (regulatory approvals only) and ``T``
# (regulatory pending) are excluded as paper-only proposals.
_PROPOSED_HIGH_CONFIDENCE: frozenset[str] = frozenset({"U", "V", "TS", "P"})

# Year the operable EIA-860 snapshot was last refreshed; proposed plants
# with an ``Effective Year`` strictly greater than this are pulled in as
# augmentations to the operable schedule. Single source of truth lives in
# data/fleet.py next to the thermal planned-additions loader.
from market_sim.data.fleet import EIA860_OPERABLE_VINTAGE as _EIA860_OPERABLE_VINTAGE  # noqa: E501

_TECHNOLOGY_TO_FUEL: dict[str, str] = {
    "Solar Photovoltaic": "solar",
    "Onshore Wind Turbine": "wind",
}

# Home-state filter for proposed-plant augmentation. The lat/lon zone
# rules in :mod:`market_sim.data.zone_assignment` will happily assign
# any point in the country to one of the ISO's zones; the state
# allowlist is what actually bounds the proposed-plant pool to the
# ISO's geographic footprint. Only ISOs listed here support the
# augmentation; others fall back to the operable schedule only.
_ISO_HOME_STATES: dict[str, frozenset[str]] = {
    "ERCOT": frozenset({"TX"}),
}

_MONTHS_PER_YEAR: int = 12

# ERCOT uncurtailed renewable potential (High Sustained Limit), one parquet
# per backcast year (``ercot_<year>_hsl_hourly.parquet``). When a year's file
# is present, the ERCOT backcast builds its CF profiles from the hourly HSL
# series rather than from EIA-930 delivered generation, so the dispatch
# re-curtails under modeled transmission limits. Built by
# scripts/build_ercot_hsl.py (2023 from the UMass 60-Day-SCED dataset;
# 2024+ from uploaded ERCOT NP6 wind/solar production reports).
_ERCOT_HSL_DIR: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "ercot-hsl"
)

# Columns every per-year HSL parquet must carry (hourly MW series).
_HSL_COLUMNS: tuple[str, ...] = (
    "hour", "wind_gen_mw", "wind_hsl_mw", "solar_gen_mw", "solar_hsl_mw",
)

# CAISO uncurtailed renewable potential (the HSL analogue: EIA-930 delivered
# + CAISO's reported wind/solar curtailment), one parquet per covered year
# with the same schema as the ERCOT file. Built by scripts/build_caiso_hsl.py;
# a year without a full-year curtailment workbook has no parquet here and
# falls back to the delivered EIA-930 hourly profile.
_CAISO_HSL_DIR: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "caiso-hsl"
)


def _hsl_file(iso: str, year: int) -> Path | None:
    """Return the uncurtailed-potential parquet for ``(iso, year)``, or ``None``.

    ``None`` when no HSL-style dataset covers the pair — the backcast then
    uses the delivered EIA-930 hourly profile (which embeds the historical
    curtailment) instead of an uncurtailed potential.
    """
    if iso == "ERCOT":
        return _ercot_hsl_path(year)
    if iso == "CAISO":
        return _CAISO_HSL_DIR / f"caiso_{year}_hsl_hourly.parquet"
    # NEISO: ISO-NE reported curtailment is sub-1 % of potential — the
    # delivered EIA-930 ISNE series is the documented default; no uncurtailed-
    # potential parquet is built.  To add one, follow the CAISO pattern in
    # scripts/build_caiso_hsl.py and wire a ``_NEISO_HSL_DIR`` constant above.
    # data-needed: requires ISO-NE to publish granular curtailment data.
    return None

# The raw ERCOT 2023 wind HSL series sums below the EIA-930 delivered total
# (~104 vs 108 TWh) — impossible, since HSL is the uncurtailed potential and
# must be at least the delivered. Rescale the series (preserving its hourly
# shape) up to the delivered EIA-930 annual total so the dispatch starts from a
# physically consistent potential. Keyed by (iso, year, fuel) -> annual TWh.
# Targets are set above the EIA-930 delivered totals (wind 108, solar 31.9) to
# offset the dispatch's economic re-curtailment, so the *delivered* output lands
# on the actuals: wind ~1.8% curtailed -> 110, solar ~0.5% -> 32.0.
# Years without an entry use the raw HSL series unrescaled — only add an
# entry when build_ercot_hsl.py's EIA-930 cross-check shows the year's HSL
# source is biased low against delivered generation.
_HSL_RESCALE_TWH: dict[tuple[str, int, str], float] = {
    ("ERCOT", 2023, "wind"): 110.0,
    ("ERCOT", 2023, "solar"): 32.0,
}


def _ercot_hsl_path(year: int) -> Path:
    """Return the per-year ERCOT HSL parquet path (which may not exist)."""
    return _ERCOT_HSL_DIR / f"ercot_{year}_hsl_hourly.parquet"


def load_ercot_hsl_hourly(year: int) -> pd.DataFrame | None:
    """Return the ERCOT hourly HSL/GEN frame for ``year``, or ``None``.

    The frame is the per-year parquet built by ``scripts/build_ercot_hsl.py``,
    sorted by ``hour`` (the model's fixed non-leap 8760-hour clock): delivered
    generation (``<fuel>_gen_mw``) and uncurtailed potential
    (``<fuel>_hsl_mw``) for wind and solar, so ERCOT's *reported* curtailment
    is ``hsl - gen``. Returns ``None`` when the year's parquet is missing or
    malformed, signaling callers to fall back (profiles to EIA-930 delivered
    generation; calibration reports to a model-only curtailment table).
    Thin ERCOT wrapper over the ISO-generic :func:`load_hsl_hourly`.
    """
    return load_hsl_hourly("ERCOT", year)


def hsl_potential_mw(iso: str, year: int, fuel: str) -> np.ndarray | None:
    """Return the hourly uncurtailed potential (MW) the dispatch consumes.

    This is the year's HSL-style series (ERCOT NP6 HSL, or the CAISO
    delivered-plus-reported-curtailment analogue) with the per-year rescale
    of :data:`_HSL_RESCALE_TWH` applied — exactly the MW series that
    :func:`_hsl_cf_profile` turns into the dispatch's CF profile, so
    calibration reports can reconstruct the model's hourly renewable
    potential (e.g. for the modeled-vs-reported curtailment metric) without
    re-deriving the fleet. Returns ``None`` when no HSL parquet covers
    ``(iso, year)``.
    """
    df = load_hsl_hourly(iso, year)
    if df is None:
        return None
    column = f"{fuel}_hsl_mw"
    if column not in df.columns:
        return None
    hsl_mw = df[column].to_numpy(dtype=float)
    target_twh = _HSL_RESCALE_TWH.get((iso, year, fuel))
    if target_twh is not None and hsl_mw.sum() > 0:
        # Scale the series to the target annual total, preserving its shape.
        hsl_mw = hsl_mw * (target_twh * 1.0e6 / hsl_mw.sum())
    return hsl_mw


def _as_float(value: object) -> float | None:
    """Coerce ``value`` to a float, returning ``None`` for blanks or NaN."""
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return None if result != result else result


def _as_int(value: object) -> int | None:
    """Coerce ``value`` to an int, returning ``None`` for blanks or NaN."""
    result = _as_float(value)
    return None if result is None else int(result)


def _eia860_monthly_capacity(
    iso: str,
    fuel: str,
    zone_names: list[str],
    cal_year: int | None,
    data_dir: Path = EIA_860_DIR,
) -> np.ndarray | None:
    """Return an ``(n_zones, 12)`` array of operable capacity (MW) by month.

    Each EIA-860 operable wind/solar plant is placed in a model zone via the
    eGRID ORIS->zone lookup (see :mod:`market_sim.data.zone_assignment`) and
    contributes its nameplate capacity to the months it was online:

    * ``operating_year < cal_year`` -- online all twelve months;
    * ``operating_year == cal_year`` -- online from ``operating_month`` on;
    * ``operating_year > cal_year`` -- not yet online (zero).

    When ``cal_year`` is ``None`` every operable plant is treated as online
    in all twelve months (no vintage ramp).

    Source: EIA-860 2024, Generator_Operable sheet, ``Operating Month`` /
    ``Operating Year`` columns.

    Returns ``None`` when the EIA-860 parquet is missing or the ISO has no
    eGRID geographic zone rules, signaling the caller to fall back to the
    hardcoded single-zone allocation.
    """
    file_name = _EIA860_OPERABLE_FILES.get(fuel)
    if file_name is None:
        return None
    path = Path(data_dir) / file_name
    if not path.exists():
        return None

    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return None
    if not zone_lookup:
        return None

    df = pd.read_parquet(path)
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status == "OP"]

    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    monthly = np.zeros((len(zone_names), _MONTHS_PER_YEAR), dtype=float)

    plant_code = df["Plant Code"].to_numpy()
    capacity = pd.to_numeric(
        df["Nameplate Capacity (MW)"], errors="coerce"
    ).to_numpy()
    op_year = pd.to_numeric(df["Operating Year"], errors="coerce").to_numpy()
    op_month = pd.to_numeric(df["Operating Month"], errors="coerce").to_numpy()

    for code, cap, oy, om in zip(plant_code, capacity, op_year, op_month):
        oris = _as_int(code)
        zone = zone_lookup.get(oris) if oris is not None else None
        z_idx = zone_to_idx.get(zone) if zone is not None else None
        if z_idx is None:
            continue
        if cap is None or cap != cap or cap <= 0.0:  # None / NaN / non-positive
            continue
        operating_year = _as_int(oy)
        if (
            cal_year is not None
            and operating_year is not None
            and operating_year > cal_year
        ):
            continue
        if cal_year is not None and operating_year == cal_year:
            month = _as_int(om) or 1
            start = min(max(month, 1), _MONTHS_PER_YEAR)
            monthly[z_idx, start - 1:] += cap
        else:
            monthly[z_idx, :] += cap

    # Augment with high-confidence EIA-860 proposed plants when the
    # calibration year is past the operable snapshot vintage (Sep 2024).
    # These are 2025-and-later commercial-operation dates not yet
    # reflected in the operable file. We use plant lat/lon (rather than
    # the eGRID ORIS lookup, which doesn't cover newly-assigned plant
    # codes) to assign each plant to a model zone.
    if cal_year is not None and cal_year > _EIA860_OPERABLE_VINTAGE:
        _add_proposed_capacity(
            monthly, iso, fuel, zone_to_idx, cal_year, data_dir
        )

    if monthly.sum() <= 0.0:
        return None
    return monthly


def _add_proposed_capacity(
    monthly: np.ndarray,
    iso: str,
    fuel: str,
    zone_to_idx: dict[str, int],
    cal_year: int,
    data_dir: Path,
) -> None:
    """Add EIA-860 proposed wind/solar plants to the monthly capacity tally.

    Each proposed plant (status ``U``/``V``/``TS``/``P``, the high-
    confidence subset) located in the ISO's home state(s), with an
    ``Effective Year`` strictly after the operable snapshot vintage and
    at-or-before ``cal_year``, contributes its nameplate capacity from
    its ``Effective Month`` onward (or all twelve months when the
    effective year is earlier than ``cal_year``). Plants are placed in
    a model zone from their lat/lon in ``eia860_plant.parquet`` via
    :func:`market_sim.data.zone_assignment.assign_zone_by_coords`.

    Only ISOs whose home state(s) are known here are augmented. State
    filtering is what bounds the proposed-plant pool to the ISO's
    geographic footprint; without it the lat/lon zone rule would
    incorrectly drag in projects from other regions of the country.
    """
    iso_states = _ISO_HOME_STATES.get(iso)
    if iso_states is None:
        return

    proposed_path = Path(data_dir) / _EIA860_PROPOSED_FILE
    if not proposed_path.exists():
        return
    from market_sim.data.zone_assignment import assign_zone_by_coords

    df = pd.read_parquet(proposed_path)
    df = df[df["State"].isin(iso_states)]
    df = df[df["Technology"].map(_TECHNOLOGY_TO_FUEL) == fuel]
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status.isin(_PROPOSED_HIGH_CONFIDENCE)]
    eff_year = pd.to_numeric(df["Effective Year"], errors="coerce")
    df = df[(eff_year > _EIA860_OPERABLE_VINTAGE) & (eff_year <= cal_year)]
    if df.empty:
        return

    plant_path = Path(data_dir) / "eia860_plant.parquet"
    if not plant_path.exists():
        return
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Latitude", "Longitude"]
    ].drop_duplicates("Plant Code")
    df = df.merge(plants, on="Plant Code", how="left")

    for _, row in df.iterrows():
        cap = _as_float(row["Nameplate Capacity (MW)"])
        if cap is None or cap <= 0.0:
            continue
        lat = _as_float(row["Latitude"])
        lon = _as_float(row["Longitude"])
        if lat is None or lon is None:
            continue
        zone = assign_zone_by_coords(lat, lon, "ERCOT")
        z_idx = zone_to_idx.get(zone)
        if z_idx is None:
            continue
        # Effective Year already filtered to (vintage, cal_year]. For an
        # earlier year, the plant is online all 12 months of cal_year;
        # for ``cal_year`` itself, online from Effective Month onward.
        e_year = _as_int(row["Effective Year"])
        if e_year is not None and e_year < cal_year:
            monthly[z_idx, :] += cap
            continue
        month = _as_int(row["Effective Month"]) or 1
        start = min(max(month, 1), _MONTHS_PER_YEAR)
        monthly[z_idx, start - 1:] += cap


def _eia860_zone_shares(
    iso: str, fuel_code: str, cal_year: int | None = None
) -> dict[str, float]:
    """Return ``{zone_name: fraction}`` of renewable capacity from EIA-860.

    Shares are the December (year-end) capacity of each model zone, derived
    from EIA-860 operable wind/solar plant locations. When ``cal_year`` is
    given, only plants online by the end of that year are counted; a plant
    commissioned during ``cal_year`` still contributes its full capacity to
    the December total, so late-year additions are reflected in the share.

    Source: EIA-860 2024 (``eia860_wind_operable`` / ``eia860_solar_operable``),
    zone assigned via :mod:`market_sim.data.zone_assignment` using the
    eGRID PLNT23 lat/lon/FIPS geography.

    Returns an empty dict when EIA-860 data is unavailable for the ISO.
    """
    zone_names = get_iso_config(iso).zone_names
    monthly = _eia860_monthly_capacity(iso, fuel_code, zone_names, cal_year)
    if monthly is None:
        return {}
    december = monthly[:, -1]
    total = december.sum()
    if total <= 0.0:
        return {}
    return {
        zone_names[i]: float(december[i] / total)
        for i in range(len(zone_names))
    }


def get_renewable_zone(iso: str, fuel: str) -> str:
    """Return the zone that absorbs new ``fuel`` capacity for ``iso``.

    New wind and solar built by capacity evolution are routed to the same
    single zone that holds the existing fleet (see
    :data:`RENEWABLE_ZONE_ALLOCATION`), so the build increments that zone's
    ``wind_cap`` / ``solar_cap`` rather than entering as a thermal unit.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        fuel: Renewable fuel, ``"wind"`` or ``"solar"``.

    Returns:
        The target zone name.

    Raises:
        KeyError: if ``iso`` or ``fuel`` has no allocation entry.
    """
    return RENEWABLE_ZONE_ALLOCATION[iso][fuel]


def derive_cf_profile(
    generation_values: np.ndarray, avg_cf: float
) -> np.ndarray:
    """Convert an EIA generation distribution into an hourly CF profile.

    The EIA ``value`` series is a probability distribution summing to ~1.0
    over the year. Scaling it by the annual-average capacity factor and by
    ``HOURS_PER_YEAR`` rescales the distribution so that its hourly mean
    equals ``avg_cf``. The result is clipped to the physical CF bounds
    ``[0, 1]`` to guard against rounding noise and high-output outliers.

    Args:
        generation_values: A ``(HOURS_PER_YEAR,)`` array of normalized EIA
            generation values for one ISO/year/fuel group.
        avg_cf: Annual-average capacity factor of the fleet (fraction).

    Returns:
        A ``(HOURS_PER_YEAR,)`` array of hourly capacity factors in
        ``[0, 1]``.
    """
    cf = generation_values * avg_cf * HOURS_PER_YEAR
    return np.clip(cf, _CF_MIN, _CF_MAX)


def _mw_to_cf(
    hourly_mw: np.ndarray, monthly_capacity: np.ndarray
) -> np.ndarray:
    """Convert an hourly system-wide MW series into a CF profile.

    Each hour's MW is divided by the capacity online in that hour's month
    (summed across zones in ``monthly_capacity``), giving a capacity factor
    per MW of online capacity. Passed to :func:`_distribute_by_eia860` with
    the vintage ramp, this reproduces the system MW total exactly while
    distributing it across zones by each zone's month-by-month capacity.
    """
    online_cap = monthly_capacity.sum(axis=0)[
        _hour_to_month_index(HOURS_PER_YEAR)
    ]
    cf = np.divide(
        hourly_mw, online_cap, out=np.zeros_like(hourly_mw),
        where=online_cap > 0.0,
    )
    return np.clip(cf, _CF_MIN, _CF_MAX)


def load_hsl_hourly(iso: str, year: int) -> pd.DataFrame | None:
    """Return the hourly GEN/HSL frame for ``(iso, year)``, or ``None``.

    The frame carries ``hour``, ``wind_gen_mw``, ``wind_hsl_mw``,
    ``solar_gen_mw`` and ``solar_hsl_mw`` — delivered generation and
    uncurtailed potential on the calibration's chronological clock — sorted
    by hour. ``hsl - gen`` is therefore the *reported* curtailment, the
    benchmark the calibration report compares modeled curtailment against.

    Returns ``None`` when no HSL-style parquet covers the pair or the file
    is not a clean full year.
    """
    path = _hsl_file(iso, year)
    if path is None or not path.exists():
        return None
    df = pd.read_parquet(path)
    if not set(_HSL_COLUMNS).issubset(df.columns) or len(df) != HOURS_PER_YEAR:
        return None
    return df.sort_values("hour").reset_index(drop=True)


def _hsl_cf_profile(
    iso: str, year: int, fuel: str, monthly_capacity: np.ndarray
) -> np.ndarray | None:
    """Return an hourly uncurtailed-potential CF profile, or ``None``.

    An HSL-style dataset records the hourly wind/solar output available
    *before* curtailment — ERCOT's NP6 High Sustained Limit (per-year
    parquets), and the CAISO delivered-plus-reported-curtailment analogue
    (see :func:`_hsl_file`). Feeding that to the dispatch (rather than
    delivered generation) lets it re-curtail under the modeled transmission
    limits. Each series is chronological by the BA's local time on the fixed
    non-leap 8760-hour clock, matching the ``<BA> hourly`` demand.

    Returns ``None`` when no HSL data covers ``(iso, year, fuel)``.
    """
    hsl_mw = hsl_potential_mw(iso, year, fuel)
    if hsl_mw is None:
        return None
    return _mw_to_cf(hsl_mw, monthly_capacity)


def _eia_hourly_cf_profile(
    iso: str, year: int, fuel: str, monthly_capacity: np.ndarray
) -> np.ndarray | None:
    """Return a delivered-generation CF profile from the BA's hourly extract.

    For a backcast year the EIA-930 ``<BA> hourly`` net generation — resolved
    from the ISO to its balancing-authority extract by
    :func:`load_eia_hourly_renewable_gen` — supplies a wind/solar profile on
    the same chronological clock as the demand and interchange. It is
    delivered (already curtailed) output, so — like the EIA-930 generation
    distributions — the dispatch does not separately re-curtail it.

    Returns ``None`` when the ISO has no mapped hourly extract or no data
    covers the ``(year, fuel)`` pair.
    """
    gen = load_eia_hourly_renewable_gen(iso, year)
    if gen is None or fuel not in gen:
        return None
    return _mw_to_cf(gen[fuel], monthly_capacity)


def _extract_fuel_values(profiles: pd.DataFrame, fuel: str) -> np.ndarray:
    """Return the hour-ordered EIA generation values for one fuel.

    Args:
        profiles: Generation-profile rows for a single ISO and year, as
            returned by :func:`load_generation_profiles`.
        fuel: Fuel identifier to extract, e.g. ``"wind"`` or ``"solar"``.

    Returns:
        A ``(HOURS_PER_YEAR,)`` array of normalized generation values,
        ordered by hour.

    Raises:
        AssertionError: if the fuel does not have a full year of hours.
    """
    rows = profiles[profiles["fuel"] == fuel].sort_values("hour")
    assert len(rows) == HOURS_PER_YEAR, (
        f"Expected {HOURS_PER_YEAR} hours for fuel '{fuel}', got {len(rows)}"
    )
    return rows["value"].to_numpy(dtype=float)


def _allocate_to_zones(
    cf_profile: np.ndarray,
    installed_mw: float,
    zone_names: list[str],
    target_zone: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Place a single CF profile and its capacity onto one ISO zone.

    All renewable output for the technology is assigned to ``target_zone``;
    every other zone receives a zero CF row and zero capacity.

    Args:
        cf_profile: A ``(HOURS_PER_YEAR,)`` hourly CF series.
        installed_mw: Installed nameplate capacity (MW) of the technology.
        zone_names: Ordered zone names of the ISO.
        target_zone: Name of the zone that absorbs the full fleet.

    Returns:
        A tuple ``(cf, cap)`` where ``cf`` is a ``(n_zones, HOURS_PER_YEAR)``
        array of hourly capacity factors and ``cap`` is a ``(n_zones,)``
        array of installed capacity in MW.

    Raises:
        ValueError: if ``target_zone`` is not among ``zone_names``.
    """
    if target_zone not in zone_names:
        raise ValueError(
            f"Allocation target zone '{target_zone}' not in ISO zones "
            f"{zone_names}"
        )
    n_zones = len(zone_names)
    cf = np.zeros((n_zones, HOURS_PER_YEAR), dtype=float)
    cap = np.zeros(n_zones, dtype=float)
    idx = zone_names.index(target_zone)
    cf[idx] = cf_profile
    cap[idx] = installed_mw
    return cf, cap


def _distribute_by_eia860(
    cf_profile: np.ndarray,
    installed_mw: float,
    monthly_capacity: np.ndarray,
    vintage_capacity_ramp: bool,
) -> tuple[np.ndarray, np.ndarray]:
    """Spread one ISO-wide CF profile across zones using EIA-860 capacity.

    The total ISO ``installed_mw`` is split across zones in proportion to
    each zone's December (year-end) capacity from ``monthly_capacity`` (see
    :func:`_eia860_monthly_capacity`); that December split is returned as the
    static per-zone capacity array.

    When ``vintage_capacity_ramp`` is ``True`` the shared CF profile is
    scaled, per zone and per month, by the fraction of year-end capacity
    that was online that month::

        effective_cf[z, t] = cf_profile[t] * monthly_cap[z, month(t)]
                                            / december_cap[z]

    so a zone's modeled output ramps up as its plants reach commercial
    operation. When ``False`` every zone with capacity uses the flat profile.

    Args:
        cf_profile: A ``(HOURS_PER_YEAR,)`` ISO-wide hourly CF series.
        installed_mw: Total ISO installed nameplate capacity (MW).
        monthly_capacity: ``(n_zones, 12)`` operable capacity by month.
        vintage_capacity_ramp: Whether to apply the monthly capacity ramp.

    Returns:
        A tuple ``(cf, cap)`` where ``cf`` is ``(n_zones, HOURS_PER_YEAR)``
        and ``cap`` is ``(n_zones,)`` December capacity in MW.
    """
    n_zones = monthly_capacity.shape[0]
    hours = cf_profile.shape[0]
    december = monthly_capacity[:, -1]
    cap = installed_mw * december / december.sum()

    cf = np.zeros((n_zones, hours), dtype=float)
    if vintage_capacity_ramp:
        month_idx = _hour_to_month_index(hours)
        for z in range(n_zones):
            if december[z] <= 0.0:
                continue
            ramp = monthly_capacity[z] / december[z]
            cf[z] = cf_profile * ramp[month_idx]
    else:
        for z in range(n_zones):
            if december[z] > 0.0:
                cf[z] = cf_profile
    return cf, cap


def load_renewable_profiles(
    iso: str,
    year: int,
    iso_config: ISOConfig,
    config: ScenarioConfig,
    data_dir: Path = DATA_DIR,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load zonal wind and solar CF profiles and capacities for an ISO.

    Hourly CF profiles are derived from the EIA-930 generation
    distributions (see :func:`derive_cf_profile` and the module docstring),
    scaled by the calibration knob ``config.renewable_cf_adjustment`` and
    re-clipped to ``[0, 1]``. Backcasts instead use measured hourly profiles
    on the calibration's chronological clock: an uncurtailed HSL-style series
    where one covers the ISO-year — ERCOT years with a built NP6 HSL
    parquet, CAISO's delivered-plus-reported-curtailment analogue — so the
    dispatch re-curtails (see :func:`_hsl_cf_profile`), and otherwise the
    delivered ``<BA> hourly`` net generation for the ISO's balancing
    authority (see :func:`_eia_hourly_cf_profile`).

    Each technology's installed capacity is distributed across the ISO's
    zones from EIA-860 plant locations (see :func:`_eia860_zone_shares`),
    with the same ISO-wide CF profile applied to every zone holding
    capacity. When ``config.vintage_capacity_ramp`` is enabled, that profile
    is additionally scaled month-by-month so a zone's output ramps up as its
    plants reach their EIA-860 commercial-operation dates. For ISOs without
    EIA-860 geographic data the loader falls back to the single-zone
    :data:`RENEWABLE_ZONE_ALLOCATION` mapping. Zones with no capacity —
    including CAISO's ``WECC_import`` node — receive zero CF and zero
    capacity.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load; also the calibration year for the
            EIA-860 vintage capacity ramp.
        iso_config: Topology configuration supplying the ordered zones.
        config: Scenario configuration; ``renewable_cf_adjustment`` scales
            every derived CF and ``vintage_capacity_ramp`` toggles the
            month-varying capacity ramp.
        data_dir: Directory containing the EIA-930 parquet extracts.

    Returns:
        A tuple ``(wind_cf, wind_cap, solar_cf, solar_cap)`` where ``wind_cf``
        and ``solar_cf`` are ``(n_zones, HOURS_PER_YEAR)`` arrays of hourly
        capacity factors and ``wind_cap`` and ``solar_cap`` are
        ``(n_zones,)`` arrays of installed capacity in MW. All arrays are
        ordered to match ``iso_config.zones``.

    Raises:
        ValueError: if no EIA data matches ``(iso, year)`` or if a zone
            allocation target is unknown for the ISO.
    """
    zone_names = iso_config.zone_names
    profiles: pd.DataFrame | None = None

    def _eia930_cf(fuel: str) -> np.ndarray:
        """Build the EIA-930 delivered-generation CF profile for one fuel."""
        nonlocal profiles
        if profiles is None:
            profiles = load_generation_profiles(iso, year, data_dir)
        values = _extract_fuel_values(profiles, fuel)
        cf = derive_cf_profile(values, RENEWABLE_AVG_CF[iso][fuel])
        return np.clip(cf * config.renewable_cf_adjustment, _CF_MIN, _CF_MAX)

    allocated: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for fuel in _RENEWABLE_FUELS:
        monthly = _eia860_monthly_capacity(iso, fuel, zone_names, year)
        if monthly is not None:
            # A calibration backcast (config.mode == "backcast", set
            # explicitly — never inferred from gas_price_override) is
            # pinned to a historical year, so the installed capacity is
            # that year's EIA-860 year-end total rather than
            # RENEWABLE_INSTALLED_MW — the current-fleet base used as the
            # starting point for forward projections.
            is_backcast = config.mode == "backcast"
            if is_backcast:
                installed_mw = float(monthly[:, -1].sum())
            else:
                installed_mw = RENEWABLE_INSTALLED_MW[iso][fuel]
            # A backcast prefers a measured hourly profile on the
            # calibration's chronological clock: an uncurtailed HSL-style
            # series where one exists (ERCOT years with a built HSL parquet,
            # CAISO covered years); otherwise the ISO's delivered
            # ``<BA> hourly`` net generation is used. Both are normalized per
            # MW of online capacity, so the vintage ramp distributes them
            # across zones, and neither takes the CF knob tuned to EIA-930 data.
            measured_cf = None
            if is_backcast:
                measured_cf = _hsl_cf_profile(iso, year, fuel, monthly)
                if measured_cf is None:
                    measured_cf = _eia_hourly_cf_profile(
                        iso, year, fuel, monthly
                    )
            if measured_cf is not None:
                cf_profile = measured_cf
                vintage_ramp = True
            else:
                cf_profile = _eia930_cf(fuel)
                vintage_ramp = config.vintage_capacity_ramp
            allocated[fuel] = _distribute_by_eia860(
                cf_profile, installed_mw, monthly, vintage_ramp
            )
        else:
            allocated[fuel] = _allocate_to_zones(
                _eia930_cf(fuel),
                RENEWABLE_INSTALLED_MW[iso][fuel],
                zone_names,
                RENEWABLE_ZONE_ALLOCATION[iso][fuel],
            )

    wind_cf, wind_cap = allocated["wind"]
    solar_cf, solar_cap = allocated["solar"]
    return wind_cf, wind_cap, solar_cf, solar_cap


def derive_offshore_wind_profile(
    onshore_wind_cf: np.ndarray,
    target_avg_cf: float,
    smoothing_hours: int = OFFSHORE_WIND_SMOOTHING_HOURS,
    min_cf: float = OFFSHORE_WIND_MIN_CF,
) -> np.ndarray:
    """Derive an hourly offshore wind CF profile from the onshore wind profile.

    Offshore wind differs from onshore in three physical ways captured here:
    1. Less gusty — ocean fetch smooths out rapid variations. Applied as a
       centered rolling-mean window of ``smoothing_hours`` (default 6h).
    2. Rarely zero — there is almost always some wind offshore. Applied as
       a floor of ``min_cf`` (default 0.08).
    3. Higher average CF — stronger, more consistent resource. The smoothed
       and floored profile is rescaled so its mean matches ``target_avg_cf``.

    The onshore profile encodes real temporal patterns (diurnal, synoptic,
    seasonal) from EIA-930 data. Smoothing preserves these patterns while
    reducing the variance, which is physically correct for offshore.

    Args:
        onshore_wind_cf: (T,) hourly onshore wind CF profile for the ISO.
            This is the single-zone profile from the zone that holds wind
            (e.g. ERCOT West).
        target_avg_cf: Desired annual-average CF for offshore wind.
        smoothing_hours: Rolling-mean window width in hours. Larger values
            produce a smoother (less variable) profile. Default 6.
        min_cf: Minimum hourly CF floor — offshore rarely drops to zero.
            Default 0.08 (~8% of rated). Source: NREL offshore wind studies.

    Returns:
        (T,) hourly offshore wind CF profile, clipped to [0, 1].
    """
    kernel = np.ones(smoothing_hours, dtype=float) / smoothing_hours
    smoothed = np.convolve(onshore_wind_cf, kernel, mode="same")
    floored = np.maximum(smoothed, min_cf)
    rescaled = floored * (target_avg_cf / floored.mean())
    return np.clip(rescaled, _CF_MIN, _CF_MAX)


def inject_offshore_wind_availability(
    fleet_arrays: FleetArrays,
    onshore_wind_cf: np.ndarray,
    config: ScenarioConfig,
    iso: str,
) -> None:
    """Overwrite availability for offshore wind generators with hourly profiles.

    After :func:`generators_to_fleet_arrays` builds the fleet with flat
    availability, this function replaces the availability rows for any
    ``offshore_wind`` generators with a derived hourly profile.

    Modifies ``fleet_arrays.availability`` IN PLACE. If no offshore wind
    generators exist in the fleet, this is a no-op.

    Args:
        fleet_arrays: The vectorized fleet — availability is (n_gen, T).
        onshore_wind_cf: (n_zones, T) onshore wind CF array. The profile
            from the wind-holding zone is used as the basis.
        config: Scenario config for offshore CF override.
        iso: ISO identifier for zone allocation lookup.
    """
    offshore_code = FUEL_TYPE_MAP["offshore_wind"]
    offshore_idx = np.flatnonzero(fleet_arrays.fuel_type_idx == offshore_code)
    if offshore_idx.size == 0:
        return

    # Wind is allocated to a single zone (see RENEWABLE_ZONE_ALLOCATION), so
    # the wind-holding zone is the only non-zero row of onshore_wind_cf.
    wind_zone_idx = int(np.argmax(onshore_wind_cf.sum(axis=1)))
    onshore_profile = onshore_wind_cf[wind_zone_idx]

    key = "floating" if iso == "CAISO" else "fixed_bottom"
    target_cf = OFFSHORE_WIND_PARAMS[key]["base_cf"]
    if config.offshore_wind_cf_override is not None:
        target_cf = config.offshore_wind_cf_override

    offshore_profile = derive_offshore_wind_profile(onshore_profile, target_cf)
    for g_idx in offshore_idx:
        fleet_arrays.availability[g_idx, :] = offshore_profile
