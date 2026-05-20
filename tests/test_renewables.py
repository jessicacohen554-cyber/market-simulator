"""Tests for wind and solar capacity-factor profile derivation."""

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR, RENEWABLE_INSTALLED_MW
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import load_eia_hourly_renewable_gen
from market_sim.data.renewables import (
    _eia860_monthly_capacity,
    _eia860_zone_shares,
    derive_cf_profile,
    load_renewable_profiles,
)

_TEST_YEAR = 2024

# EIA-860 plant-location data is keyed to a calibration year; ERCOT 2023 is
# the year the zone distribution and vintage ramp were calibrated against.
_CAL_YEAR = 2023


def test_derive_cf_profile_known_values():
    """CF equals generation value times avg CF times the hour count."""
    values = np.array([1.0e-4, 2.0e-4, 1.5e-4])
    avg_cf = 0.35
    result = derive_cf_profile(values, avg_cf)
    expected = values * avg_cf * HOURS_PER_YEAR
    np.testing.assert_allclose(result, expected)


def test_derive_cf_profile_clipped_to_unit_interval():
    """High generation values clip to 1.0 and all CFs stay in [0, 1]."""
    values = np.array([0.0, 1.0e-4, 0.5])
    result = derive_cf_profile(values, 0.35)
    assert result.min() >= 0.0
    assert result.max() <= 1.0
    # 0.5 * 0.35 * 8760 far exceeds 1.0 and must clip to the CF ceiling.
    assert result[-1] == 1.0


def test_renewable_cf_adjustment_scales_cfs():
    """A 1.1 CF adjustment scales the (unclipped) wind CFs by 10%."""
    iso_config = get_iso_config("ERCOT")
    base = ScenarioConfig(weather_year=_TEST_YEAR, iso="ERCOT")
    adjusted = base.with_overrides(renewable_cf_adjustment=1.1)

    wind_cf_base, _, _, _ = load_renewable_profiles(
        "ERCOT", _TEST_YEAR, iso_config, base
    )
    wind_cf_adj, _, _, _ = load_renewable_profiles(
        "ERCOT", _TEST_YEAR, iso_config, adjusted
    )
    np.testing.assert_allclose(wind_cf_adj, wind_cf_base * 1.1)


def test_zone_distribution_from_eia860():
    """Wind/solar capacity is distributed across zones from EIA-860 data."""
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(weather_year=_CAL_YEAR, iso="ERCOT")
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, config
    )
    assert wind_cf.shape == (iso_config.n_zones, HOURS_PER_YEAR)

    # The full ISO fleet is spread across every zone, not parked in one.
    np.testing.assert_allclose(
        wind_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["wind"]
    )
    np.testing.assert_allclose(
        solar_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["solar"]
    )
    assert (wind_cap > 0.0).sum() >= 3
    assert (solar_cap > 0.0).sum() >= 3

    # West holds the largest share of both wind and solar in ERCOT.
    west = iso_config.zone_names.index("West")
    assert wind_cap[west] == wind_cap.max()
    assert solar_cap[west] == solar_cap.max()

    # Per-zone capacity tracks the EIA-860 zone shares.
    wind_shares = _eia860_zone_shares("ERCOT", "wind", _CAL_YEAR)
    for i, zone in enumerate(iso_config.zone_names):
        expected = RENEWABLE_INSTALLED_MW["ERCOT"]["wind"] * wind_shares[zone]
        np.testing.assert_allclose(wind_cap[i], expected)

    # Every zone holding capacity carries a non-zero CF profile.
    for i in range(iso_config.n_zones):
        if wind_cap[i] > 0.0:
            assert wind_cf[i].sum() > 0.0
        else:
            assert np.all(wind_cf[i] == 0.0)


def test_vintage_monthly_ramp():
    """Month-varying capacity reflects COD dates from EIA-860."""
    zone_names = get_iso_config("ERCOT").zone_names
    monthly = _eia860_monthly_capacity("ERCOT", "solar", zone_names, _CAL_YEAR)
    assert monthly is not None
    assert monthly.shape == (len(zone_names), 12)

    # ERCOT added solar through 2023, so year-end capacity exceeds January.
    jan_total = monthly[:, 0].sum()
    dec_total = monthly[:, -1].sum()
    assert dec_total > jan_total
    # Capacity only accumulates over the year — never decreases month to month.
    assert np.all(np.diff(monthly, axis=1) >= -1e-9)

    # With the ramp on, modeled solar output in January is below the
    # ramp-off (flat year-end capacity) baseline; the two agree in December.
    iso_config = get_iso_config("ERCOT")
    ramp_on = ScenarioConfig(weather_year=_CAL_YEAR, iso="ERCOT")
    ramp_off = ramp_on.with_overrides(vintage_capacity_ramp=False)
    _, _, solar_cf_on, _ = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, ramp_on
    )
    _, _, solar_cf_off, _ = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, ramp_off
    )
    west = iso_config.zone_names.index("West")
    jan_hours = slice(0, 31 * 24)
    dec_hours = slice(HOURS_PER_YEAR - 31 * 24, HOURS_PER_YEAR)
    assert solar_cf_on[west, jan_hours].sum() < solar_cf_off[west, jan_hours].sum()
    np.testing.assert_allclose(
        solar_cf_on[west, dec_hours], solar_cf_off[west, dec_hours]
    )


def test_calibration_backcast_uses_eia860_actual_capacity():
    """A calibration backcast resolves capacity to the EIA-860 year-end actual.

    With ``gas_price_override`` set the run is a historical backcast, so 2023
    solar must resolve to the EIA-860 year-end total (~14.9 GW) rather than
    the 38 GW forward-projection ``RENEWABLE_INSTALLED_MW`` constant.
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR, iso="ERCOT", gas_price_override=2.54
    )
    _, wind_cap, _, solar_cap = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, config
    )
    # EIA-860 ERCOT year-end 2023: ~14.9 GW solar, ~36.7 GW wind.
    assert 13_000.0 < solar_cap.sum() < 17_000.0
    assert solar_cap.sum() < RENEWABLE_INSTALLED_MW["ERCOT"]["solar"]
    assert 34_000.0 < wind_cap.sum() < 39_000.0


def test_forward_run_uses_renewable_installed_mw():
    """A forward run keeps the RENEWABLE_INSTALLED_MW projection base.

    Without ``gas_price_override`` the run is a forward projection (the path a
    2026+ simulation year takes), so capacity stays anchored to the
    current-fleet ``RENEWABLE_INSTALLED_MW`` constants regardless of which
    weather year supplies the CF shape.
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(weather_year=_CAL_YEAR, iso="ERCOT")
    assert config.gas_price_override is None
    _, wind_cap, _, solar_cap = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, config
    )
    np.testing.assert_allclose(
        solar_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["solar"]
    )
    np.testing.assert_allclose(
        wind_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["wind"]
    )


def test_caiso_solar_allocated_to_trading_zones_not_import():
    """CAISO solar fills the NP15/ZP26/SP15 trading zones, never WECC_import."""
    iso_config = get_iso_config("CAISO")
    config = ScenarioConfig(weather_year=_TEST_YEAR, iso="CAISO")
    _, _, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", _TEST_YEAR, iso_config, config
    )
    trading = [
        iso_config.zone_names.index(z) for z in ("NP15", "ZP26", "SP15")
    ]
    wecc = iso_config.zone_names.index("WECC_import")

    # Solar capacity spreads across the trading zones (eGRID geography puts
    # the bulk in SP15's desert), and the import node stays empty.
    assert solar_cap[trading].sum() > 0.0
    assert solar_cf[trading].sum() > 0.0
    assert np.all(solar_cf[wecc] == 0.0)
    assert solar_cap[wecc] == 0.0


def test_caiso_backcast_cf_profile_matches_realized_annual_cf():
    """A CAISO backcast builds its CF profile from the CISO hourly extract.

    With ``gas_price_override`` set the run is a historical backcast, so the
    profile is built from the EIA-930 ``CISO hourly`` net generation (the new
    per-BA file-resolution path generalized from the ERCOT-only loader), not
    the EIA-930 distribution. CAISO is multi-zone, so the measured profile is
    distributed across the NP15/ZP26/SP15 trading zones by EIA-860 capacity:
    the capacity-weighted sum across zones reconstructs the delivered hourly
    generation (only the measured path does this — the distribution path would
    produce a different shape), and the implied profile mean equals the
    realized annual-average CF (delivered generation / year-end capacity).
    """
    iso_config = get_iso_config("CAISO")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR, iso="CAISO", gas_price_override=3.0
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", _CAL_YEAR, iso_config, config
    )
    wecc = iso_config.zone_names.index("WECC_import")
    gen = load_eia_hourly_renewable_gen("CAISO", _CAL_YEAR)

    for fuel, cf, cap in (
        ("wind", wind_cf, wind_cap),
        ("solar", solar_cf, solar_cap),
    ):
        # The WECC import node carries no in-footprint generation.
        assert cap[wecc] == 0.0
        assert np.all(cf[wecc] == 0.0)

        # Capacity-weighted CF across zones reconstructs the delivered hourly
        # MW: same annual energy and same chronological shape.
        reconstructed = (cap[:, None] * cf).sum(axis=0)
        np.testing.assert_allclose(
            reconstructed.sum(), gen[fuel].sum(), rtol=0.01
        )
        assert np.corrcoef(reconstructed, gen[fuel])[0, 1] > 0.999

        # Hence the capacity-weighted profile mean equals the realized
        # annual-average CF = delivered generation / year-end capacity.
        realized_cf = gen[fuel].mean() / cap.sum()
        weighted_cf = reconstructed.mean() / cap.sum()
        assert 0.0 < weighted_cf < 1.0
        np.testing.assert_allclose(weighted_cf, realized_cf, atol=0.01)


def test_miso_cf_profile_mean_matches_annual_average_cf():
    """MISO wind/solar resolve to the converted MISO hourly extract.

    MISO is mapped only for hourly file resolution (it has no full ``ISOConfig``
    yet), so the generalized loader is exercised directly: it must resolve
    MISO→MISO and return a full 8760-hour wind and solar series. Rescaling
    each into an hourly CF profile yields a mean equal to the chosen
    annual-average CF — the profile is a normalized distribution times that CF
    — for representative CFs that sit below the clip ceiling.
    """
    gen = load_eia_hourly_renewable_gen("MISO", _CAL_YEAR)
    assert gen is not None
    assert {"wind", "solar"} <= set(gen)
    # Representative MISO annual-average CFs (EIA Electric Power Monthly 2023:
    # MISO wind ~0.40, utility-scale solar ~0.20); both below the clip ceiling.
    for fuel, avg_cf in (("wind", 0.40), ("solar", 0.20)):
        mw = gen[fuel]
        assert len(mw) == HOURS_PER_YEAR
        cf = derive_cf_profile(mw / mw.sum(), avg_cf)
        assert cf.min() >= 0.0 and cf.max() <= 1.0
        np.testing.assert_allclose(cf.mean(), avg_cf, atol=1e-5)


def test_spp_and_neiso_cf_profiles_match_annual_average_cf():
    """SPP and ISO-NE wind/solar resolve to their converted hourly extracts.

    Like MISO, neither has a full ``ISOConfig`` yet, so the generalized loader
    is exercised directly: it must resolve SPP→SWPP and NEISO→ISNE and return
    a full 8760-hour wind and solar series. Rescaling a series into an hourly
    CF profile yields a mean equal to the chosen annual-average CF for
    representative CFs below the clip ceiling.
    """
    for iso in ("SPP", "NEISO"):
        gen = load_eia_hourly_renewable_gen(iso, _CAL_YEAR)
        assert gen is not None
        assert {"wind", "solar"} <= set(gen)
        assert all(len(gen[fuel]) == HOURS_PER_YEAR for fuel in ("wind", "solar"))

    # Clip-free (iso, fuel, representative annual CF) cases for an exact mean.
    # SPP wind carries a known EIA outlier hour, so its solar series is used.
    for iso, fuel, avg_cf in (("SPP", "solar", 0.15), ("NEISO", "wind", 0.30)):
        mw = load_eia_hourly_renewable_gen(iso, _CAL_YEAR)[fuel]
        cf = derive_cf_profile(mw / mw.sum(), avg_cf)
        assert cf.min() >= 0.0 and cf.max() <= 1.0
        np.testing.assert_allclose(cf.mean(), avg_cf, atol=1e-5)
