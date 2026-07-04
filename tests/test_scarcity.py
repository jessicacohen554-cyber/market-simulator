"""Tests for the ERCOT ORDC scarcity-pricing overlay (results.scarcity)."""

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.results.scarcity import (
    effective_reliability_deployment_mw,
    ercot_market_regime,
    floor_active_mask,
    load_lolp_params,
    lolp,
    ordc_adder,
    reserve_headroom,
    scarcity_prices,
    season_of_hour,
    tod_block_of_hour,
)


def test_market_regime_auto_gates_at_rtcb_golive():
    c = ScenarioConfig()  # ercot_market_design defaults "auto"
    assert ercot_market_regime(2023, c) == "ordc"
    assert ercot_market_regime(2025, c) == "ordc"
    assert ercot_market_regime(2026, c) == "rtcb"
    assert ercot_market_regime(2040, c) == "rtcb"


def test_market_regime_explicit_override():
    assert (
        ercot_market_regime(2030, ScenarioConfig(ercot_market_design="ordc")) == "ordc"
    )
    assert (
        ercot_market_regime(2023, ScenarioConfig(ercot_market_design="rtcb")) == "rtcb"
    )
    with pytest.raises(ValueError):
        ercot_market_regime(2030, ScenarioConfig(ercot_market_design="bogus"))


def test_reliability_offset_contained_to_rtcb_regime():
    # The fitted ORDC-era RTORDPA offset was DELETED (2026-07-04, CLAUDE.md
    # rule 26): the ORDC regime carries no offset, and the deleted knob no
    # longer parses — a zeroed deprecated knob is a re-armable answer key.
    assert effective_reliability_deployment_mw(2023, ScenarioConfig()) == 0.0
    with pytest.raises(TypeError):
        ScenarioConfig(ordc_reliability_deployment_mw=2500.0)
    # The forward RTC+B scenario knob remains, and only fires under RTC+B.
    recur = ScenarioConfig(rtcb_reliability_deployment_mw=1500.0)
    assert effective_reliability_deployment_mw(2023, recur) == 0.0
    assert effective_reliability_deployment_mw(2030, recur) == 1500.0


def test_lolp_pins_to_one_at_or_below_mcl():
    r = np.array([0.0, 2999.0, 3000.0, 3001.0, 50000.0])
    out = lolp(r, mu_mw=0.0, sigma_mw=1400.0, mcl_mw=3000.0)
    assert out[0] == 1.0 and out[1] == 1.0 and out[2] == 1.0
    assert 0.0 < out[3] < 1.0
    assert out[4] < 1e-9


def test_lolp_monotone_decreasing_in_reserves():
    r = np.linspace(0, 30000, 500)
    out = lolp(r, 0.0, 1400.0, 3000.0, shift_sigma=0.5)
    assert (np.diff(out) <= 1e-12).all()


def test_lolp_shift_raises_lolp_at_given_reserves():
    r = np.array([6000.0])
    base = lolp(r, 0.0, 1400.0, 3000.0, shift_sigma=0.0)
    shifted = lolp(r, 0.0, 1400.0, 3000.0, shift_sigma=0.5)
    assert shifted[0] > base[0]


def test_adder_pins_to_voll_minus_lambda_below_mcl():
    r = np.array([1000.0])
    lam = np.array([80.0])
    adder = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=1400.0,
        multistep_floor=False,
    )
    # Both half-hour LOLP terms are 1 below the MCL -> full VOLL - lambda.
    assert adder[0] == pytest.approx(5000.0 - 80.0)


def test_adder_capped_so_price_never_exceeds_voll():
    r = np.array([0.0])
    lam = np.array([4900.0])
    adder = ordc_adder(r, lam, voll=5000.0, mcl_mw=3000.0, mu_mw=0.0, sigma_mw=1400.0)
    assert adder[0] <= 100.0 + 1e-9
    # lambda above VOLL (LP slack hour): adder clamps to zero, not negative.
    adder2 = ordc_adder(
        np.array([0.0]),
        np.array([6000.0]),
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=1400.0,
    )
    assert adder2[0] == 0.0


def test_adder_near_zero_at_comfortable_reserves():
    adder = ordc_adder(
        np.array([20000.0]),
        np.array([25.0]),
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=1400.0,
        multistep_floor=False,
    )
    assert adder[0] < 0.01


def test_multistep_floor_steps_and_gating():
    lam = np.zeros(3)
    r = np.array([6400.0, 6900.0, 7500.0])
    adder = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=100.0,
        multistep_floor=True,
        floor_active=True,
    )
    # sigma tiny -> unfloored adder ~0; the OBDRR048 steps must hold.
    assert adder[0] == pytest.approx(20.0)
    assert adder[1] == pytest.approx(10.0)
    assert adder[2] == pytest.approx(0.0, abs=1e-9)
    # Floor inactive (pre-2023-11-01 hours) -> no floor.
    adder_off = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=100.0,
        multistep_floor=True,
        floor_active=False,
    )
    assert adder_off[0] == pytest.approx(0.0, abs=1e-9)


def test_floor_active_mask_dates():
    m2023 = floor_active_mask(2023, 8760)
    assert not m2023[304 * 24 - 1] and m2023[304 * 24]
    assert floor_active_mask(2024, 8760).all()
    assert not floor_active_mask(2022, 8760).any()


def test_voll_scenario_moves_tail_up():
    """A $9,000 pre-Uri VOLL must scale the deep-scarcity adder up."""
    r = np.array([2500.0, 5000.0])
    lam = np.array([100.0, 100.0])
    a5 = ordc_adder(
        r,
        lam,
        voll=5000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=1400.0,
        multistep_floor=False,
    )
    a9 = ordc_adder(
        r,
        lam,
        voll=9000.0,
        mcl_mw=3000.0,
        mu_mw=0.0,
        sigma_mw=1400.0,
        multistep_floor=False,
    )
    assert (a9 > a5).all()


def test_season_and_tod_blocks():
    hours = np.array([0, 23, 31 * 24, 181 * 24 + 14])  # Jan, Jan, Feb, Jul
    assert list(season_of_hour(hours)) == ["winter", "winter", "winter", "summer"]
    assert list(tod_block_of_hour(np.array([0, 3, 4, 12, 23]))) == [1, 1, 2, 4, 6]


def test_load_lolp_params_roundtrip(tmp_path):
    rows = ["season,tod_block,mu_mw,sigma_mw"]
    for season in ("winter", "spring", "summer", "fall"):
        for block in range(1, 7):
            rows.append(f"{season},{block},{100 + block},{1000 + block}")
    p = tmp_path / "lolp.csv"
    p.write_text("\n".join(rows))
    mu, sigma = load_lolp_params(p, hours=8760)
    assert mu.shape == (8760,) and sigma.shape == (8760,)
    # Hour 0 = winter block 1; hour 12 = winter block 4.
    assert mu[0] == 101 and sigma[0] == 1001
    assert mu[12] == 104 and sigma[12] == 1004

    p2 = tmp_path / "missing.csv"
    p2.write_text("\n".join(rows[:-1]))  # drop fall block 6
    with pytest.raises(ValueError, match="missing"):
        load_lolp_params(p2, hours=8760)


def _toy_fleet_arrays(t: int = 4) -> FleetArrays:
    pmax = np.array([100.0, 50.0, 30.0])
    avail = np.ones((3, t))
    avail[0, 0] = 0.5  # derated hour 0
    return FleetArrays(
        pmax=pmax,
        pmin=np.zeros(3),
        heat_rate=np.full(3, 7.0),
        vom=np.zeros(3),
        emission_rate=np.zeros(3),
        nox_rate=np.zeros(3),
        so2_rate=np.zeros(3),
        zone_idx=np.zeros(3, dtype=int),
        fuel_type_idx=np.array(
            [
                FUEL_TYPE_MAP["gas_cc"],
                FUEL_TYPE_MAP["coal"],
                FUEL_TYPE_MAP["hydro"],  # excluded from reserves
            ]
        ),
        availability=avail,
        unit_ids=["g1", "g2", "h1"],
        efficiency_bin=np.zeros(3),
        plant_code=np.zeros(3, dtype=int),
    )


def test_reserve_headroom_composition():
    fa = _toy_fleet_arrays()
    dispatch = np.zeros((3, 4))
    dispatch[0] = [50.0, 80.0, 100.0, 100.0]
    dispatch[1] = [50.0, 50.0, 50.0, 50.0]
    dispatch[2] = [30.0, 30.0, 0.0, 0.0]  # hydro: must not enter headroom
    cap = np.array([20.0])
    chg = np.array([[10.0, 0.0, 0.0, 0.0]])
    dis = np.array([[0.0, 0.0, 20.0, 0.0]])
    r_online, r_offline = reserve_headroom(
        fa,
        dispatch,
        cap,
        chg,
        dis,
        as_plan_mw=10.0,
        renewable_headroom=np.array([0.0, 0.0, 0.0, 5.0]),
    )
    # g1 (gas_cc) and g2 (coal) are dispatched every hour, so both are online
    # and neither is quick-start (only gas_ct/oil are) — the offline (non-spin)
    # tier is zero throughout and r_online matches the old single-tier sum.
    assert (r_offline == 0.0).all()
    # Hour 0: thermal headroom = (50-50)+(50-50)=0; storage 20 - 0 + 10 = 30;
    # minus AS 10 => 20.
    assert r_online[0] == pytest.approx(20.0)
    # Hour 1: thermal headroom (100-80)+(50-50)=20; storage 20; -10 => 30.
    assert r_online[1] == pytest.approx(30.0)
    # Hour 2: thermal headroom 0; storage 20 - 20 = 0; -10 => -10.
    assert r_online[2] == pytest.approx(-10.0)
    # Hour 3: thermal headroom 0; storage 20; -10 + renewables 5 => 15.
    assert r_online[3] == pytest.approx(15.0)


def _split_fleet_arrays(t: int = 2) -> FleetArrays:
    """gas_cc (slow-start) + gas_ct (quick-start), one plant each."""
    return FleetArrays(
        pmax=np.array([100.0, 40.0]),
        pmin=np.zeros(2),
        heat_rate=np.full(2, 7.0),
        vom=np.zeros(2),
        emission_rate=np.zeros(2),
        nox_rate=np.zeros(2),
        so2_rate=np.zeros(2),
        zone_idx=np.zeros(2, dtype=int),
        fuel_type_idx=np.array([FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]]),
        availability=np.ones((2, t)),
        unit_ids=["cc", "ct"],
        efficiency_bin=np.zeros(2),
        plant_code=np.array([10, 20]),
    )


def test_online_offline_split_excludes_cold_slowstart():
    fa = _split_fleet_arrays()
    # Hour 0: both offline (dispatch 0). Hour 1: both online.
    dispatch = np.array([[0.0, 60.0], [0.0, 10.0]])
    cap = np.zeros(0)  # no storage
    r_online, r_offline = reserve_headroom(
        fa, dispatch, cap, None, None, as_plan_mw=0.0
    )
    # Hour 0: gas_cc offline+slow-start -> excluded entirely; gas_ct offline
    # but quick-start -> its 40 MW backs the offline (non-spin) tier only.
    assert r_online[0] == pytest.approx(0.0)
    assert r_offline[0] == pytest.approx(40.0)
    # Hour 1: both online -> spinning headroom (100-60)+(40-10)=70 online,
    # nothing in the offline tier.
    assert r_online[1] == pytest.approx(70.0)
    assert r_offline[1] == pytest.approx(0.0)


def test_offline_split_raises_adder_vs_legacy_single_tier():
    """A scarce online tier with offline backup prices above RTOFFCAP=0."""
    r_online = np.array([3500.0])
    r_offline = np.array([4000.0])
    lam = np.array([100.0])
    kw = dict(
        voll=5000.0, mcl_mw=3000.0, mu_mw=0.0, sigma_mw=1400.0, multistep_floor=False
    )
    split = ordc_adder(r_online + r_offline, lam, reserves_online_mw=r_online, **kw)
    legacy = ordc_adder(r_online + r_offline, lam, **kw)  # both tiers = full
    # The first-half term sees only the tight online tier, so the split adder
    # is strictly higher than treating all reserve as online (RTOFFCAP=0).
    assert split[0] > legacy[0]


def test_reserve_headroom_accepts_hourly_as_plan():
    fa = _split_fleet_arrays()
    dispatch = np.array([[60.0, 60.0], [10.0, 10.0]])
    r_online, _ = reserve_headroom(
        fa, dispatch, np.zeros(0), None, None, as_plan_mw=np.array([0.0, 50.0])
    )
    # Spinning headroom 70 both hours; hour 1 nets a 50 MW hourly AS plan.
    assert r_online[0] == pytest.approx(70.0)
    assert r_online[1] == pytest.approx(20.0)


def test_scarcity_prices_wrapper_backcast_floor_gating():
    cfg = ScenarioConfig(
        mode="backcast", scarcity_pricing_enabled=True, ordc_lolp_sigma_mw=100.0
    )
    t = 8760
    reserves = np.full(t, 6900.0)
    lam = np.zeros(t)
    out = scarcity_prices(cfg, 2023, reserves, lam)
    adder = out["scarcity_adder"]
    # Before Nov 1 2023 no floor; after, the $10 step at 6,900 MW.
    assert adder[0] == pytest.approx(0.0, abs=1e-6)
    assert adder[304 * 24] == pytest.approx(10.0)
    assert set(out) == {"reserves_mw", "reserves_online_mw", "lolp", "scarcity_adder"}


def test_scarcity_price_overlay_defaults_false():
    """The ISO-eligibility gate for the post-solve overlay defaults off.

    ERCOT opts back in via ISOConfig.default_scenario_overrides (see
    test_iso_config.py); a bare ScenarioConfig() — used for any ISO that has
    not opted in — must not run the overlay.
    """
    assert ScenarioConfig().scarcity_price_overlay is False


def test_scarcity_prices_accepts_generic_iso_parameters():
    """scarcity_prices()/ordc_adder()/reserve_headroom() take config-driven
    LOLP/ORDC parameters, not ERCOT-hardcoded constants, so any ISO can use
    them once scarcity_price_overlay is enabled and its own ordc_* fields
    are calibrated."""
    cfg = ScenarioConfig(
        iso="CAISO",
        scarcity_pricing_enabled=True,
        scarcity_price_overlay=True,
        ordc_voll=2000.0,
        ordc_mcl_mw=500.0,
        ordc_lolp_mu_mw=10.0,
        ordc_lolp_sigma_mw=50.0,
    )
    t = 24
    reserves = np.full(t, 100.0)
    lam = np.full(t, 20.0)
    out = scarcity_prices(cfg, 2030, reserves, lam)
    assert np.all(out["scarcity_adder"] >= 0.0)
    assert np.all(out["scarcity_adder"] <= cfg.ordc_voll - lam)
