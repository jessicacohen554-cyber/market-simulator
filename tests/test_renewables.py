"""Tests for wind and solar capacity-factor profile derivation."""

import numpy as np
import pytest

from market_sim.config.constants import (
    HOURS_PER_YEAR,
    RENEWABLE_AVG_CF,
    RENEWABLE_INSTALLED_MW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import load_eia_hourly_renewable_gen
from market_sim.data.renewables import (
    _distribute_by_eia860,
    _eia860_monthly_capacity,
    _eia860_zone_shares,
    _redistribute_preserving_total,
    _solar_zone_clearsky_shapes,
    _wind_zone_reanalysis_shapes,
    _zone_renewable_shapes,
    derive_cf_profile,
    load_hsl_hourly,
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
    np.testing.assert_allclose(wind_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["wind"])
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

    With ``mode="backcast"`` set the run is a historical backcast, so 2023
    solar must resolve to the EIA-860 year-end total (~14.9 GW) rather than
    the 38 GW forward-projection ``RENEWABLE_INSTALLED_MW`` constant.
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="ERCOT",
        mode="backcast",
        gas_price_override=2.54,
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

    The default ``mode="forecast"`` is a forward projection (the path a
    2026+ simulation year takes), so capacity stays anchored to the
    current-fleet ``RENEWABLE_INSTALLED_MW`` constants regardless of which
    weather year supplies the CF shape -- even when a gas-price sensitivity
    pins ``gas_price_override`` (which previously, and wrongly, flipped the
    loader into backcast mode).
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR, iso="ERCOT", gas_price_override=2.54
    )
    assert config.mode == "forecast"
    _, wind_cap, _, solar_cap = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, config
    )
    np.testing.assert_allclose(
        solar_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["solar"]
    )
    np.testing.assert_allclose(wind_cap.sum(), RENEWABLE_INSTALLED_MW["ERCOT"]["wind"])


def test_caiso_solar_allocated_to_trading_zones_not_import():
    """CAISO solar fills the NP15/ZP26/LA_BASIN/SDGE/SP15_rest trading zones, never WECC_import."""
    iso_config = get_iso_config("CAISO")
    config = ScenarioConfig(weather_year=_TEST_YEAR, iso="CAISO")
    _, _, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", _TEST_YEAR, iso_config, config
    )
    trading = [
        iso_config.zone_names.index(z)
        for z in ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
    ]
    wecc = iso_config.zone_names.index("WECC_import")

    # Solar capacity spreads across the trading zones (eGRID geography puts
    # the bulk in the SP15 (LA_BASIN/SDGE/SP15_rest) desert), and the import
    # node stays empty.
    assert solar_cap[trading].sum() > 0.0
    assert solar_cf[trading].sum() > 0.0
    assert np.all(solar_cf[wecc] == 0.0)
    assert solar_cap[wecc] == 0.0


def test_caiso_solar_zones_have_distinct_shapes():
    """Each CAISO solar zone gets its own clear-sky shape from its tracking mix.

    NP15 (NorCal) carries the most fixed-tilt solar and ZP26/SP15_rest the most
    tracking, so NP15's diurnal solar profile must peak more sharply (a higher
    midday peak-to-shoulder ratio) than the more-tracking southern zones — the
    spatial diversity the single ISO-wide shape erased.
    """
    iso_config = get_iso_config("CAISO")
    zones = iso_config.zone_names
    shapes = _solar_zone_clearsky_shapes("CAISO", "solar", zones, _TEST_YEAR)
    assert shapes is not None
    assert shapes.shape == (len(zones), HOURS_PER_YEAR)

    np15 = zones.index("NP15")
    sp15_rest = zones.index("SP15_rest")
    # The two trading-zone shapes are genuinely different, not a copy.
    assert not np.allclose(shapes[np15], shapes[sp15_rest])

    def peak_to_shoulder(shape: np.ndarray) -> float:
        diurnal = shape.reshape(365, 24).mean(axis=0)
        peak_hour = int(diurnal.argmax())
        shoulder = diurnal[peak_hour - 3]  # 3h before the midday peak
        return diurnal[peak_hour] / shoulder

    # More fixed-tilt -> a narrower, peakier midday belly.
    assert peak_to_shoulder(shapes[np15]) > peak_to_shoulder(shapes[sp15_rest])


def test_solar_zone_redistribution_preserves_aggregate():
    """Per-zone solar shaping is a pure spatial redistribution of the aggregate.

    The capacity-weighted sum of the shaped per-zone CFs must equal the input
    ISO-wide ``cf_profile`` every hour (to machine precision), so annual energy
    and the system duck curve are unchanged — only NP15-vs-southern-zones differ.
    """
    iso_config = get_iso_config("CAISO")
    zones = iso_config.zone_names
    monthly = _eia860_monthly_capacity("CAISO", "solar", zones, _TEST_YEAR)
    assert monthly is not None
    shapes = _solar_zone_clearsky_shapes("CAISO", "solar", zones, _TEST_YEAR)
    assert shapes is not None

    # A realistic, sun-correlated CF profile (proportional to the system sun).
    december = monthly[:, -1]
    share = december / december.sum()
    mean_shape = (share[:, None] * shapes).sum(axis=0)
    cf_profile = mean_shape / mean_shape.max() * 0.75
    installed = float(december.sum())

    shaped, cap = _distribute_by_eia860(
        cf_profile, installed, monthly, vintage_capacity_ramp=False, zone_shapes=shapes
    )
    flat, _ = _distribute_by_eia860(
        cf_profile, installed, monthly, vintage_capacity_ramp=False
    )

    share = cap / cap.sum()
    agg_shaped = (share[:, None] * shaped).sum(axis=0)
    # Hour-by-hour aggregate preserved, and annual energy identical to flat.
    np.testing.assert_allclose(agg_shaped, cf_profile, atol=1e-9)
    np.testing.assert_allclose(
        (cap[:, None] * shaped).sum(axis=0),
        (cap[:, None] * flat).sum(axis=0),
        atol=1e-6,  # summing 6 zones (post SP15-split) vs 4 adds float round-off
    )
    # The shaped split actually differs from flat in the trading zones.
    np15 = zones.index("NP15")
    assert not np.allclose(shaped[np15], flat[np15])


def test_solar_zone_shapes_noop_for_wind_and_single_zone():
    """Per-zone shaping is a no-op for wind, single-zone ISOs, and non-gated ISOs.

    Only gated multi-zone solar ISOs (CAISO) are reshaped; everything else
    keeps the legacy single-shape behaviour, returning ``None`` so the flat
    distribution path is used unchanged.
    """
    caiso_zones = get_iso_config("CAISO").zone_names
    ercot_zones = get_iso_config("ERCOT").zone_names
    # Wind is never reshaped, even for a gated ISO.
    assert _solar_zone_clearsky_shapes("CAISO", "wind", caiso_zones, _TEST_YEAR) is None
    # A non-gated ISO's solar is untouched.
    assert _solar_zone_clearsky_shapes("ERCOT", "solar", ercot_zones, _CAL_YEAR) is None


def test_redistribute_preserving_total_trivial_24h():
    """A trivial two-zone, 24-hour case preserves the system total exactly.

    One peaky zone and one flat zone split a single midday-bell system series;
    the capacity-weighted sum must reproduce the input every hour and the two
    zones must end up with different shapes.
    """
    hours = 24
    cap = np.array([100.0, 100.0])
    ramp_t = np.ones((2, hours))
    t = np.arange(hours)
    # A daytime bell, zero at night.
    bell = np.clip(np.sin((t - 6) / 12.0 * np.pi), 0.0, None)
    cf_profile = bell * 0.6
    # Zone 0 peaky (squared bell), zone 1 flat-ish (bell) -> distinct shapes.
    shapes = np.vstack([bell**2, bell])

    cf = _redistribute_preserving_total(cf_profile, cap, ramp_t, shapes)
    share = cap / cap.sum()
    agg = (share[:, None] * cf).sum(axis=0)
    np.testing.assert_allclose(agg, cf_profile, atol=1e-12)
    assert not np.allclose(cf[0], cf[1])
    # Night hours are zero everywhere (no sun to redistribute).
    night = bell == 0.0
    assert np.all(cf[:, night] == 0.0)


def test_miso_wind_zones_have_distinct_shapes():
    """MISO's six zones get distinct reanalysis wind shapes from the parquet.

    The upper-plains West (Great-Plains nocturnal jet) must have a measurably
    different diurnal wind signature than the lower-Midwest East — the spatial
    diversity the single ISO-wide wind profile erased, and the load-bearing
    check that the parquet carries a column for EVERY model zone (a missing
    column silently reverts to one ISO-wide shape). Built by
    scripts/data/build_miso_wind_shape.py.
    """
    zones = get_iso_config("MISO").zone_names
    shapes = _wind_zone_reanalysis_shapes("MISO", "wind", zones, _CAL_YEAR)
    assert shapes is not None
    assert shapes.shape == (len(zones), HOURS_PER_YEAR)

    west = zones.index("MISO-West")
    east = zones.index("MISO-East")
    assert not np.allclose(shapes[west], shapes[east])

    def night_to_afternoon(shape: np.ndarray) -> float:
        diurnal = shape.reshape(365, 24).mean(axis=0)
        return diurnal[0:6].mean() / diurnal[12:18].mean()

    # The plains West is relatively more nocturnal than the lower-Midwest
    # East (a higher night-to-afternoon wind ratio).
    assert night_to_afternoon(shapes[west]) > night_to_afternoon(shapes[east])


def test_zone_renewable_shapes_dispatch():
    """The shape dispatcher routes wind→reanalysis (MISO) and solar→clear-sky."""
    miso_zones = get_iso_config("MISO").zone_names
    caiso_zones = get_iso_config("CAISO").zone_names
    ercot_zones = get_iso_config("ERCOT").zone_names

    # MISO wind is reshaped; MISO solar (not a gated solar ISO) is not.
    assert _zone_renewable_shapes("MISO", "wind", miso_zones, _CAL_YEAR) is not None
    assert _zone_renewable_shapes("MISO", "solar", miso_zones, _CAL_YEAR) is None
    # CAISO solar is reshaped; CAISO wind (not a gated wind ISO) is not.
    assert _zone_renewable_shapes("CAISO", "solar", caiso_zones, _TEST_YEAR) is not None
    assert _zone_renewable_shapes("CAISO", "wind", caiso_zones, _TEST_YEAR) is None
    # A non-gated ISO is untouched for both fuels.
    assert _zone_renewable_shapes("ERCOT", "wind", ercot_zones, _CAL_YEAR) is None
    assert _zone_renewable_shapes("ERCOT", "solar", ercot_zones, _CAL_YEAR) is None


def test_wind_zone_redistribution_preserves_aggregate():
    """Per-zone MISO wind shaping is a pure spatial redistribution.

    The capacity-weighted sum of the shaped per-zone wind CFs must equal the
    input ISO-wide ``cf_profile`` every hour, so annual energy and the system
    wind series are unchanged — only the inter-zone split moves.
    """
    zones = get_iso_config("MISO").zone_names
    monthly = _eia860_monthly_capacity("MISO", "wind", zones, _CAL_YEAR)
    assert monthly is not None
    shapes = _wind_zone_reanalysis_shapes("MISO", "wind", zones, _CAL_YEAR)
    assert shapes is not None

    # A flat-ish 35% system wind CF profile is enough to test preservation.
    cf_profile = np.full(HOURS_PER_YEAR, 0.35)
    installed = float(monthly[:, -1].sum())

    shaped, cap = _distribute_by_eia860(
        cf_profile, installed, monthly, vintage_capacity_ramp=False, zone_shapes=shapes
    )
    flat, _ = _distribute_by_eia860(
        cf_profile, installed, monthly, vintage_capacity_ramp=False
    )
    share = cap / cap.sum()
    agg_shaped = (share[:, None] * shaped).sum(axis=0)
    np.testing.assert_allclose(agg_shaped, cf_profile, atol=1e-9)
    np.testing.assert_allclose(
        (cap[:, None] * shaped).sum(axis=0),
        (cap[:, None] * flat).sum(axis=0),
        atol=1e-9,
    )
    # The shaped split differs from flat in a capacity-bearing wind zone.
    west = zones.index("MISO-West")
    assert not np.allclose(shaped[west], flat[west])


def test_wind_zone_shapes_noop_for_solar_and_ungated():
    """The reanalysis wind shaper is a no-op outside gated MISO wind."""
    miso_zones = get_iso_config("MISO").zone_names
    ercot_zones = get_iso_config("ERCOT").zone_names
    # Solar is never reshaped by the wind shaper, even for MISO.
    assert _wind_zone_reanalysis_shapes("MISO", "solar", miso_zones, _CAL_YEAR) is None
    # A non-gated ISO's wind is untouched.
    assert _wind_zone_reanalysis_shapes("ERCOT", "wind", ercot_zones, _CAL_YEAR) is None
    # No calibration year -> no per-year parquet selection.
    assert _wind_zone_reanalysis_shapes("MISO", "wind", miso_zones, None) is None


def test_caiso_backcast_cf_profile_is_uncurtailed_potential():
    """A CAISO backcast builds its CF profile from the uncurtailed potential.

    With ``mode="backcast"`` set and the CAISO HSL-analogue parquet present
    (delivered EIA-930 generation + CAISO's reported curtailment, built by
    scripts/data/build_caiso_hsl.py), the profile is the *uncurtailed* potential —
    so the dispatch re-curtails CAISO's multi-TWh solar curtailment instead
    of inheriting it. CAISO is multi-zone, so the measured profile is
    distributed across the NP15/ZP26/LA_BASIN/SDGE/SP15_rest trading zones by
    EIA-860 capacity:
    the capacity-weighted sum across zones reconstructs the hourly HSL series
    (floored at zero — EIA-930 reports small negative night-time solar, and a
    CF cannot go negative), sits at or above delivered generation in every
    hour, and the implied profile mean equals the realized uncurtailed
    annual-average CF (potential / year-end capacity), slightly above the
    delivered EIA-923-style CF by the curtailment share.
    """
    iso_config = get_iso_config("CAISO")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="CAISO",
        mode="backcast",
        gas_price_override=3.0,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", _CAL_YEAR, iso_config, config
    )
    wecc = iso_config.zone_names.index("WECC_import")
    gen = load_eia_hourly_renewable_gen("CAISO", _CAL_YEAR)
    hsl = load_hsl_hourly("CAISO", _CAL_YEAR)
    assert hsl is not None

    for fuel, cf, cap in (
        ("wind", wind_cf, wind_cap),
        ("solar", solar_cf, solar_cap),
    ):
        # The WECC import node carries no in-footprint generation.
        assert cap[wecc] == 0.0
        assert np.all(cf[wecc] == 0.0)

        # Capacity-weighted CF across zones reconstructs the uncurtailed
        # hourly MW (zero-floored): same annual energy, same chronological
        # shape, and at or above the delivered series everywhere.
        potential = np.maximum(hsl[f"{fuel}_hsl_mw"].to_numpy(dtype=float), 0.0)
        reconstructed = (cap[:, None] * cf).sum(axis=0)
        np.testing.assert_allclose(reconstructed.sum(), potential.sum(), rtol=0.01)
        assert np.corrcoef(reconstructed, potential)[0, 1] > 0.999
        assert np.all(reconstructed >= gen[fuel] - 1e-6)

        # The capacity-weighted profile mean equals the realized uncurtailed
        # annual-average CF — at or a few percent above the delivered
        # (EIA-923-style) CF, by exactly the reported curtailment share.
        delivered_cf = gen[fuel].mean() / cap.sum()
        uncurtailed_cf = potential.mean() / cap.sum()
        weighted_cf = reconstructed.mean() / cap.sum()
        assert 0.0 < weighted_cf < 1.0
        np.testing.assert_allclose(weighted_cf, uncurtailed_cf, atol=0.01)
        assert delivered_cf <= weighted_cf <= delivered_cf * 1.10


def test_caiso_hsl_parquet_uncurtailed_at_least_delivered():
    """Every CAISO HSL parquet has HSL >= delivered in every single hour.

    The HSL analogue is delivered + reported curtailment, so the inequality
    holds by construction; this guards the builder against sign or alignment
    regressions. At least one covered year must exist (the 2023/2024
    workbooks are committed), and solar curtailment must be the documented
    multi-TWh wedge.
    """
    covered = [
        year
        for year in (2023, 2024, 2025)
        if load_hsl_hourly("CAISO", year) is not None
    ]
    assert 2023 in covered and 2024 in covered
    for year in covered:
        df = load_hsl_hourly("CAISO", year)
        assert len(df) == HOURS_PER_YEAR
        for fuel in ("wind", "solar"):
            gen = df[f"{fuel}_gen_mw"].to_numpy(dtype=float)
            hsl = df[f"{fuel}_hsl_mw"].to_numpy(dtype=float)
            assert np.all(hsl >= gen - 1e-6), (
                f"CAISO {year} {fuel}: HSL below delivered"
            )
        solar_curt_twh = (df["solar_hsl_mw"].sum() - df["solar_gen_mw"].sum()) / 1e6
        assert 1.0 < solar_curt_twh < 6.0


def test_ercot_2023_hsl_path_untouched_by_caiso_wiring():
    """The ERCOT 2023 HSL profile still reconstructs the consumed potential.

    The CAISO HSL lookup generalized the file resolution; ERCOT 2023 must keep
    its behavior — the HSL shape reconciled to the EIA-930 footprint
    (:func:`hsl_potential_mw`), with the fleet CF round-tripping back to that
    consumed potential at the raw series' hourly shape.
    """
    from market_sim.data.renewables import hsl_potential_mw

    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="ERCOT",
        mode="backcast",
        gas_price_override=2.54,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "ERCOT", _CAL_YEAR, iso_config, config
    )
    hsl = load_hsl_hourly("ERCOT", _CAL_YEAR)
    assert hsl is not None

    for fuel, cf, cap in (
        ("wind", wind_cf, wind_cap),
        ("solar", solar_cf, solar_cap),
    ):
        reconstructed = (cap[:, None] * cf).sum(axis=0)
        target_mwh = hsl_potential_mw("ERCOT", _CAL_YEAR, fuel).sum()
        np.testing.assert_allclose(reconstructed.sum(), target_mwh, rtol=0.01)
        raw = hsl[f"{fuel}_hsl_mw"].to_numpy(dtype=float)
        assert np.corrcoef(reconstructed, raw)[0, 1] > 0.999


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


def test_neiso_cf_profiles_match_annual_average_cf():
    """ISO-NE wind/solar resolve to their converted hourly extracts.

    The generalized loader is exercised directly: it must resolve NEISO→ISNE
    and return a full 8760-hour wind and solar series. Rescaling a series into
    an hourly CF profile yields a mean equal to the chosen annual-average CF
    for representative CFs below the clip ceiling.
    """
    gen = load_eia_hourly_renewable_gen("NEISO", _CAL_YEAR)
    assert gen is not None
    assert {"wind", "solar"} <= set(gen)
    assert all(len(gen[fuel]) == HOURS_PER_YEAR for fuel in ("wind", "solar"))

    mw = load_eia_hourly_renewable_gen("NEISO", _CAL_YEAR)["wind"]
    cf = derive_cf_profile(mw / mw.sum(), 0.30)
    assert cf.min() >= 0.0 and cf.max() <= 1.0
    np.testing.assert_allclose(cf.mean(), 0.30, atol=1e-5)


def test_neiso_backcast_eia930_zone_distribution():
    """NEISO backcast uses EIA-930 ISNE delivered gen, zone-shaped by EIA-860.

    With ``mode="backcast"`` ISO-NE wind/solar profiles come from the EIA-930
    ``ISNE hourly`` net-generation series and are distributed across the four
    in-footprint NEISO zones by EIA-860 plant-location capacity shares:

    * Wind — bulk in the North zone (ME/NH/VT onshore belt); mean CF
      benchmarks against the EIA-923 fleet average (~0.30, atol 0.10).
    * Solar — distributed across Connecticut and Central (CT + MA/RI);
      EIA-930 ISNE ``NG: SUN`` captures only grid-scale (non-BTM) wholesale
      solar (~800–1 600 GWh/yr).  ISO-NE's net-metered solar reduces load
      rather than appearing as generation, so the mean CF relative to EIA-860
      total installed capacity is ~0.04, much lower than the physical
      utility-PV value (~0.15).  The energy balance is correct because the
      EIA-930 net-load demand series already excludes BTM solar; the solar
      benchmark therefore checks the absolute annual GWh rather than the
      CF relative to total installed capacity.
    * HQ_import virtual node carries zero capacity and zero CF.
    * ERCOT/CAISO HSL paths are unaffected by NEISO wiring.
    """
    iso_config = get_iso_config("NEISO")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="NEISO",
        mode="backcast",
        gas_price_override=3.0,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "NEISO", _CAL_YEAR, iso_config, config
    )
    zones = iso_config.zone_names
    north = zones.index("North")
    central = zones.index("Central")
    ct = zones.index("Connecticut")
    hq = zones.index("HQ_import")

    # EIA-860 multi-zone distribution was used — at least two real zones carry
    # capacity; the virtual HQ_import node stays empty in both technologies.
    assert (wind_cap > 0.0).sum() >= 2, "wind should spread across ≥2 zones"
    assert wind_cap[hq] == 0.0
    assert solar_cap[hq] == 0.0
    assert np.all(wind_cf[hq] == 0.0)
    assert np.all(solar_cf[hq] == 0.0)

    # Wind bulk sits in the North zone (ME/NH/VT onshore wind belt).
    assert wind_cap[north] > 0.0
    assert wind_cap[north] == wind_cap.max()

    # Solar is distributed across Connecticut and/or Central — together they
    # hold the majority of in-footprint utility solar (CT farms + MA/RI PV).
    assert solar_cap[ct] + solar_cap[central] > 0.5 * solar_cap.sum()

    # CF arrays are (n_zones, HOURS_PER_YEAR) and physically bounded.
    assert wind_cf.shape == (iso_config.n_zones, HOURS_PER_YEAR)
    assert solar_cf.shape == (iso_config.n_zones, HOURS_PER_YEAR)
    assert wind_cf.min() >= 0.0 and wind_cf.max() <= 1.0
    assert solar_cf.min() >= 0.0 and solar_cf.max() <= 1.0

    wind_mw = (wind_cap[:, None] * wind_cf).sum(axis=0)
    solar_mw = (solar_cap[:, None] * solar_cf).sum(axis=0)

    # Benchmark wind mean CF vs EIA-923 fleet average (ISO-NE onshore wind
    # ~0.30; EIA Electric Power Monthly 2023).  This is a real data-quality
    # guard — the profile is derived from measured EIA-930 data, not from a
    # normalized distribution, so the mean won't be algebraically exact.
    mean_wind_cf = wind_mw.mean() / wind_cap.sum()
    np.testing.assert_allclose(
        mean_wind_cf,
        RENEWABLE_AVG_CF["NEISO"]["wind"],
        atol=0.10,
        err_msg="NEISO wind mean CF too far from EIA-923 fleet average",
    )

    # Benchmark solar against absolute annual GWh rather than mean CF.
    # EIA-930 ISNE NG:SUN = grid-scale wholesale solar only (~800–1 600 GWh).
    # The CF relative to EIA-860 total installed capacity is ~0.04 — not a
    # defect: BTM solar is already embedded in the EIA-930 net-load demand.
    solar_annual_gwh = solar_mw.sum() / 1e3
    assert 400 < solar_annual_gwh < 2000, (
        f"NEISO wholesale solar annual generation out of EIA-923 range: "
        f"{solar_annual_gwh:.0f} GWh (expected 400–2 000)"
    )

    # ERCOT and CAISO HSL paths must be unaffected by NEISO wiring.
    assert load_hsl_hourly("ERCOT", _CAL_YEAR) is not None
    assert load_hsl_hourly("CAISO", _CAL_YEAR) is not None
    assert load_hsl_hourly("NEISO", _CAL_YEAR) is None


# ---------------------------------------------------------------------------
# NYISO renewable profile tests (EIA-930 NYIS delivered-distribution path)
# ---------------------------------------------------------------------------


def test_nyiso_hsl_returns_none():
    """NYISO has no HSL parquet — curtailment path is stubbed.

    NYISO wind/solar curtailment is small (well under 1 TWh/yr per EIA-923)
    and NYISO does not publish hourly uncurtailed-potential data, so
    ``load_hsl_hourly`` must return ``None`` for every NYISO year and the
    backcast stays on the delivered EIA-930 path.  Confirming None also
    guards against accidentally placing a file in _NYISO_HSL_DIR that would
    silently divert the backcast onto a stub dataset.
    """
    for year in (2023, 2024, 2025):
        assert load_hsl_hourly("NYISO", year) is None, (
            f"Expected no NYISO HSL parquet for {year}; curtailment path must "
            "stay on the delivered EIA-930 default until real data is available"
        )


def test_nyiso_backcast_cf_profile_mean_matches_eia923():
    """NYISO backcast profile mean approximates the EIA-923 annual CF.

    Wind uses the NYIS BA hourly measured generation (EIA-930 ``NYIS
    hourly.parquet``); solar falls back to the EIA-930 distribution shape
    because EIA-930 NYIS does not separately report solar generation
    (``NG: SUN`` is all-zero for the BA extract). Both paths land within
    ±50 % of the EIA-923-calibrated ``RENEWABLE_AVG_CF["NYISO"]`` benchmark
    values (wind ~0.26, solar ~0.15), confirming the EIA-930 NYIS
    delivered-distribution path is wired correctly end-to-end.
    """
    iso_config = get_iso_config("NYISO")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="NYISO",
        mode="backcast",
        gas_price_override=2.54,
    )
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "NYISO", _CAL_YEAR, iso_config, config
    )

    assert wind_cf.shape == (iso_config.n_zones, HOURS_PER_YEAR)
    assert solar_cf.shape == (iso_config.n_zones, HOURS_PER_YEAR)
    assert np.all(wind_cf >= 0.0) and np.all(wind_cf <= 1.0)
    assert np.all(solar_cf >= 0.0) and np.all(solar_cf <= 1.0)

    for fuel, cf, cap in (
        ("wind", wind_cf, wind_cap),
        ("solar", solar_cf, solar_cap),
    ):
        total_cap = cap.sum()
        assert total_cap > 0.0, f"NYISO {fuel} capacity must be positive"
        # Capacity-weighted hourly mean reconstructs the delivered CF.
        weighted_mean = (cap[:, None] * cf).sum(axis=0).mean() / total_cap
        assert 0.0 < weighted_mean < 1.0, (
            f"NYISO {fuel} weighted mean CF must be in (0, 1); got {weighted_mean:.4f}"
        )
        # Benchmark: within ±50 % of the EIA-923-calibrated annual-average CF.
        # Wind mean ≈ 0.19 (measured 2023 NYIS hourly) vs benchmark 0.26;
        # solar mean ≈ 0.15 (EIA-930 distribution fallback, flat shape) vs 0.15.
        benchmark = RENEWABLE_AVG_CF["NYISO"][fuel]
        np.testing.assert_allclose(
            weighted_mean,
            benchmark,
            rtol=0.50,
            err_msg=(
                f"NYISO {fuel} backcast mean CF {weighted_mean:.3f} is outside "
                f"±50 % of EIA-923 benchmark {benchmark:.3f}"
            ),
        )


def test_nyiso_wind_concentrates_upstate():
    """NYISO wind capacity concentrates in the upstate zones.

    EIA-860 places virtually all NY utility wind in the upstate counties
    (zones A–E → Upstate_West and the A-E fringe of Capital_Hudson).  The
    downstate zones (Lower_Hudson, NYC, Long_Island) should hold little or no
    wind capacity, consistent with the physical resource geography.
    """
    iso_config = get_iso_config("NYISO")
    config = ScenarioConfig(
        weather_year=_CAL_YEAR,
        iso="NYISO",
        mode="backcast",
        gas_price_override=2.54,
    )
    _, wind_cap, _, _ = load_renewable_profiles("NYISO", _CAL_YEAR, iso_config, config)

    zone_names = iso_config.zone_names
    upstate_west = zone_names.index("Upstate_West")

    # Upstate_West holds the largest share of NYISO wind (Chautauqua /
    # Madison / Lewis / Jefferson / Steuben counties — the bulk of NY wind).
    assert wind_cap[upstate_west] == wind_cap.max(), (
        "Upstate_West should hold the most NYISO wind capacity"
    )
    # Downstate zones carry negligible wind capacity (< 5 % of the fleet).
    total = wind_cap.sum()
    for zone in ("Lower_Hudson", "NYC", "Long_Island"):
        idx = zone_names.index(zone)
        assert wind_cap[idx] / total < 0.05, (
            f"{zone} wind share {wind_cap[idx] / total:.1%} exceeds 5 % — "
            "unexpected downstate wind concentration"
        )


def test_ercot_caiso_hsl_paths_untouched_by_nyiso_wiring():
    """ERCOT and CAISO HSL lookups are unaffected by the NYISO stub.

    Adding the NYISO branch in ``_hsl_file`` must not disturb the existing
    ERCOT and CAISO dispatch paths.  ERCOT 2023 must still resolve to its NP6
    parquet; CAISO 2023 must still resolve to the delivered-plus-curtailment
    HSL analogue.
    """
    ercot_hsl = load_hsl_hourly("ERCOT", _CAL_YEAR)
    assert ercot_hsl is not None, "ERCOT 2023 HSL parquet must still load"
    assert len(ercot_hsl) == HOURS_PER_YEAR

    caiso_hsl = load_hsl_hourly("CAISO", _CAL_YEAR)
    assert caiso_hsl is not None, "CAISO 2023 HSL parquet must still load"
    assert len(caiso_hsl) == HOURS_PER_YEAR


def test_ercot_2019_renewable_profiles_resolve_end_to_end():
    """2026-07 weather-pool widening: a pre-2022 year resolves with no fallback.

    ERCOT 2019 has no HSL parquet, so this exercises the plain EIA-930
    delivered-generation CF path (``_eia_hourly_cf_profile``) for a year
    outside the original 2023-2025 backcast window -- confirming the widened
    pool (``constants.WEATHER_YEAR_POOL_BY_ISO["ERCOT"]``) is actually usable
    by the dispatch, not just present on disk. See
    docs/weather-pool-coverage-2026-07.md.
    """
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(iso="ERCOT", mode="backcast", weather_year=2019)
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "ERCOT", 2019, iso_config, config
    )
    n_zones = len(iso_config.zone_names)
    assert wind_cf.shape == (n_zones, HOURS_PER_YEAR)
    assert solar_cf.shape == (n_zones, HOURS_PER_YEAR)
    assert wind_cap.sum() > 0.0
    assert solar_cap.sum() > 0.0
    assert np.all(wind_cf >= 0.0) and np.all(wind_cf <= 1.0)
    assert np.all(solar_cf >= 0.0) and np.all(solar_cf <= 1.0)


@pytest.mark.parametrize("iso,year", [("CAISO", 2019), ("PJM", 2019), ("MISO", 2019)])
def test_2026_07_06_balance_backfill_renewables_resolve_end_to_end(iso, year):
    """2026-07-06 BALANCE-bulk backfill: CAISO/PJM/MISO renewables reach 2019.

    Their EIA-930 ``<BA> hourly`` extracts previously began at the 2021/2022
    boundary (api.eia.gov, needed to pull further back, is blocked in this
    sandbox). The six-month BALANCE bulk archive (a different, unblocked
    host) carries the same per-fuel generation series back to 2019 and was
    folded into the extracts by
    ``scripts/data/extend_eia930_hourly_from_balance.py``. This exercises the
    resulting wind+solar CF path exactly like the ERCOT 2019 case above --
    CAISO/PJM/MISO still have no HSL parquet for 2019, so this is the plain
    EIA-930 delivered-generation CF path. See
    docs/weather-pool-coverage-2026-07.md.
    """
    iso_config = get_iso_config(iso)
    config = ScenarioConfig(iso=iso, mode="backcast", weather_year=year)
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        iso, year, iso_config, config
    )
    n_zones = len(iso_config.zone_names)
    assert wind_cf.shape == (n_zones, HOURS_PER_YEAR)
    assert solar_cf.shape == (n_zones, HOURS_PER_YEAR)
    assert wind_cap.sum() > 0.0
    assert solar_cap.sum() > 0.0
    assert np.all(wind_cf >= 0.0) and np.all(wind_cf <= 1.0)
    assert np.all(solar_cf >= 0.0) and np.all(solar_cf <= 1.0)
