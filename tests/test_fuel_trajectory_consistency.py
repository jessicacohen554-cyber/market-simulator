"""Derivation-lock the AEO-grounded fuel-price trajectory constants.

The FF-G2 vintage refresh (2026-07-20) re-derives ``HENRY_HUB_TRAJECTORIES``,
``COAL_PRICE_TRAJECTORIES`` and ``OIL_PRICE_TRAJECTORIES`` from AEO2026 via
``scripts/data/derive_fuel_trajectories.py``. These tests assert the committed
constants EQUAL that derivation, so a future edit that hand-touches a value (or
a stale re-paste) fails CI -- the same paste-from-derive-script discipline the
cost-benchmark envelope carries (``test_cost_benchmark_envelope.py``).

Key structural facts these tests pin (see the FF-G2 methodology doc and the
constants comment blocks):

* Gas keeps 2023/2024/2025 as measured **historical actuals** (2.54 / 2.19 /
  3.52), NOT AEO projections -- the backcast neighbor-price seam reads these
  <=2025 values, so they are held fixed across vintage bumps for byte-identity.
  Only the FORECAST years 2026-2050 come from AEO2026.
* Coal and oil are FORECAST-ONLY (backcast uses the flat escalation /
  ``OIL_PRICE_PER_MMBTU``), so their whole tables are re-vintaged to AEO2026,
  starting at 2025 (AEO2026's first year).
* Nuclear fuel is UNCHANGED by the AEO bump (its EIA-UMAR source did not
  update), staying in real 2024$.
"""

from __future__ import annotations

import pytest

from market_sim.config.constants import (
    COAL_PRICE_TRAJECTORIES,
    HENRY_HUB_TRAJECTORIES,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_TRAJECTORIES,
)

derive = pytest.importorskip("scripts.data.derive_fuel_trajectories")

_AEO_YEAR = 2026
_PATHS = ("low", "mid", "high")
# Gas 2023/2024/2025 are measured historical actuals held fixed across vintages.
_GAS_HISTORICAL_ACTUALS = {2023: 2.54, 2024: 2.19, 2025: 3.52}
_FORECAST_YEARS = tuple(range(2026, 2051))


def _load():
    try:
        aeo = derive._load_aeo(_AEO_YEAR)
    except FileNotFoundError:
        pytest.skip(f"AEO{_AEO_YEAR} raw fuel-price CSV not present in this env")
    s2p = derive._SCENARIO_TO_PATH_BY_AEO[_AEO_YEAR]
    return aeo, s2p


def test_gas_forecast_years_match_aeo2026_derivation():
    """HENRY_HUB_TRAJECTORIES[path][2026..2050] == derive_gas_trajectory."""
    aeo, s2p = _load()
    derived = derive.derive_gas_trajectory(aeo, s2p)
    for path in _PATHS:
        for year in _FORECAST_YEARS:
            assert HENRY_HUB_TRAJECTORIES[path][year] == derived[path][year], (
                path,
                year,
            )


def test_gas_historical_actuals_are_fixed():
    """The <=2025 historical actuals are the measured spot averages, unchanged
    across the vintage bump (backcast neighbor-price seam reads them)."""
    for path in _PATHS:
        for year, value in _GAS_HISTORICAL_ACTUALS.items():
            assert HENRY_HUB_TRAJECTORIES[path][year] == value, (path, year)


def test_gas_2025_actual_not_aeo_base_year():
    """The measured 2025 ($3.52) is kept, NOT AEO2026's own 2025 base value
    ($3.47) -- proving the forecast splice never overwrote the actual."""
    aeo, s2p = _load()
    derived = derive.derive_gas_trajectory(aeo, s2p)
    for path in _PATHS:
        assert derived[path][2025] == pytest.approx(3.47)  # AEO2026 base year
        assert HENRY_HUB_TRAJECTORIES[path][2025] == 3.52  # measured actual kept


def test_gas_hindcast_paths_preserved():
    """The backcast/hindcast gas paths are untouched by the forecast refresh."""
    for path in ("hindcast_realized", "hindcast_asknown_aeo2021"):
        assert path in HENRY_HUB_TRAJECTORIES


def test_coal_trajectory_matches_aeo2026_derivation():
    """COAL_PRICE_TRAJECTORIES == derive_coal_trajectory (whole table, 2025+)."""
    aeo, s2p = _load()
    derived = derive.derive_coal_trajectory(aeo, s2p)
    for path in _PATHS:
        assert COAL_PRICE_TRAJECTORIES[path] == derived[path], path


def test_oil_trajectory_matches_aeo2026_derivation():
    """OIL_PRICE_TRAJECTORIES == derive_oil_trajectory (whole table, 2025+)."""
    aeo, s2p = _load()
    derived = derive.derive_oil_trajectory(aeo, s2p)
    for path in _PATHS:
        assert OIL_PRICE_TRAJECTORIES[path] == derived[path], path


def test_coal_and_oil_anchor_year_is_2025():
    """AEO2026 starts at 2025 (AEO2025 started 2024): the coal ratio anchor and
    the oil first-knot are both 2025 now (methodology-doc delta ledger)."""
    for path in _PATHS:
        assert min(COAL_PRICE_TRAJECTORIES[path]) == 2025
        assert min(OIL_PRICE_TRAJECTORIES[path]) == 2025


def test_nuclear_unchanged_by_aeo_bump():
    """Nuclear fuel is NOT re-derived by the AEO edition change (EIA-UMAR source
    unchanged); the committed table still matches its own derivation and ends
    at its 2024 real-dollar knot."""
    derived = derive.derive_nuclear_fuel_trajectory()
    assert NUCLEAR_FUEL_PRICE_HISTORICAL == derived
    assert max(NUCLEAR_FUEL_PRICE_HISTORICAL) == 2024


def test_all_series_are_2025_dollars():
    """The fetched AEO2026 raw series are published in real 2025$ (was 2024$
    for AEO2025) -- the dollar-year basis change the vintage bump carries."""
    aeo, _ = _load()
    gas = aeo[(aeo["fuel"] == "gas") & (aeo["metric"] == "henry_hub_spot")]
    assert (gas["unit"] == "2025 $/MMBtu").all()


def test_low_below_mid_below_high_gas_2050():
    """Path ordering holds under the new vintage (low < mid < high at 2050)."""
    y = 2050
    assert (
        HENRY_HUB_TRAJECTORIES["low"][y]
        < HENRY_HUB_TRAJECTORIES["mid"][y]
        < HENRY_HUB_TRAJECTORIES["high"][y]
    )
