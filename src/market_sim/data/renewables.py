"""Renewable resource profiles (wind and solar capacity factors).

Derives hourly capacity-factor (CF) profiles for wind and solar from the
EIA-930 normalized generation distributions. The EIA ``value`` column for a
given ``(iso, year, fuel)`` group is a probability distribution that sums to
roughly 1.0 across the 8760 hours of the year; multiplying by the fleet's
annual-average CF and by the hour count rescales it into an hourly CF series
whose mean equals that annual-average CF.

Because the EIA generation series reflect *delivered* output, they already
embed real-world curtailment (roughly 5% for wind and solar in ERCOT and
CAISO). The derived CF profiles therefore inherit that curtailment as a
built-in conservatism: modeled renewable energy is modestly lower than the
unconstrained resource potential, which is the desired behavior for a
dispatch model that does not separately re-curtail these resources.
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
from market_sim.config.iso_configs import ISOConfig
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import DATA_DIR, load_generation_profiles
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays

# Capacity factors are physically bounded to the closed interval [0, 1].
_CF_MIN: float = 0.0
_CF_MAX: float = 1.0

# Renewable fuels for which CF profiles are derived, matching the ``fuel``
# values in the EIA-930 generation-profiles parquet.
_RENEWABLE_FUELS: tuple[str, str] = ("wind", "solar")

# Zone that absorbs the entire ISO wind/solar fleet, by ISO and fuel. Each
# technology is assigned to the zone holding the bulk of its installed
# capacity; every other zone receives an all-zero profile.
# TODO: distribute CF and capacity across zones when sub-zonal generation
# data becomes available.
# Source: ERCOT CDR Dec 2024 (West wind belt, South solar corridor),
# CAISO annual report 2024 (single in-footprint load zone).
RENEWABLE_ZONE_ALLOCATION: dict[str, dict[str, str]] = {
    "ERCOT": {"wind": "West", "solar": "South", "offshore_wind": "Houston"},
    "CAISO": {
        "wind": "CAISO_main",
        "solar": "CAISO_main",
        "offshore_wind": "CAISO_main",
    },
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
    re-clipped to ``[0, 1]``. Because the EIA series reflect delivered
    output, the resulting profiles embed roughly 5% of real-world
    curtailment as a built-in conservatism — modeled renewable energy is
    slightly below the unconstrained resource potential.

    Each technology's full ISO fleet is assigned to a single zone (see
    :data:`RENEWABLE_ZONE_ALLOCATION`): all wind to the zone with the most
    wind and all solar to the zone with the most solar. Every other zone —
    including CAISO's ``WECC_import`` node — receives zero CF and zero
    capacity.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        year: Calendar year to load.
        iso_config: Topology configuration supplying the ordered zones.
        config: Scenario configuration; ``renewable_cf_adjustment`` scales
            every derived CF.
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
    profiles = load_generation_profiles(iso, year, data_dir)
    zone_names = iso_config.zone_names

    allocated: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for fuel in _RENEWABLE_FUELS:
        values = _extract_fuel_values(profiles, fuel)
        cf_profile = derive_cf_profile(values, RENEWABLE_AVG_CF[iso][fuel])
        cf_profile = np.clip(
            cf_profile * config.renewable_cf_adjustment, _CF_MIN, _CF_MAX
        )
        allocated[fuel] = _allocate_to_zones(
            cf_profile,
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
