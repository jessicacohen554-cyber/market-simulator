"""closeout-CAISO-w5 D4: physics-only RA must-offer bridge eligibility (rule 18).

``caiso_ra_mustoffer_physics_eligibility`` admits long-start gas steam to the
SAME CAISO bridge detector at its own measured minimum load
(``caiso_ra_st_min_load_frac``). Off, the call is byte-identical. Trivial case:
one zone, a CC + a steam unit + a fast-start CT, 24 hours.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import MECH_RA_MUSTOFFER
from market_sim.pipeline.commitment import caiso_ra_p1_floor_fleet

T = 24


def _fleet():
    zone = "NP15"
    gens = [
        Generator(
            unit_id="CC",
            name="cc",
            zone=zone,
            fuel_type="gas_cc",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=7.0,
            eford=0.0,
            plant_group="CC_REGULAR",
        ),
        Generator(
            unit_id="ST",
            name="st",
            zone=zone,
            fuel_type="gas_st",
            pmax_mw=400.0,
            pmin_mw=0.0,
            heat_rate=10.5,
            eford=0.0,
            plant_group="ST_GAS",
        ),
        Generator(
            unit_id="CT",
            name="ct",
            zone=zone,
            fuel_type="gas_ct",
            pmax_mw=100.0,
            pmin_mw=0.0,
            heat_rate=10.5,
            eford=0.0,
            plant_group="CT_PEAKER",
        ),
    ]
    fa = generators_to_fleet_arrays(gens, [zone], hours=T)
    return gens, fa


def _p0():
    """Every unit runs 0-9 and 13-23, idle 10-12 (3 h < CC 6 h / ST 8 h min-down)."""
    p0 = np.zeros((3, T))
    p0[:, :10] = [[300.0], [400.0], [100.0]]
    p0[:, 13:] = [[300.0], [400.0], [100.0]]
    return p0


def _floor(config):
    gens, fa = _fleet()
    prices = np.full((1, T), 40.0)
    mc = np.full((3, T), 39.0)
    return caiso_ra_p1_floor_fleet(config, "CAISO", gens, fa, _p0(), prices, mc), fa


def test_off_is_byte_identical_and_steam_unbridged():
    """Default: the steam unit is outside the bridge, the CC is bridged."""
    floored, fa = _floor(ScenarioConfig(hours=T, caiso_ra_mustoffer=True))
    assert floored is not None
    assert floored.min_gen[1].max() == 0.0
    expected_cc = ScenarioConfig().caiso_ra_min_load_frac * fa.pmax[0]
    assert np.allclose(floored.min_gen[0, 10:13], expected_cc)


def test_on_bridges_steam_at_its_own_measured_min_load():
    """Armed: the steam gap is floored at caiso_ra_st_min_load_frac, the CC unchanged."""
    cfg = ScenarioConfig(
        hours=T, caiso_ra_mustoffer=True, caiso_ra_mustoffer_physics_eligibility=True
    )
    floored, fa = _floor(cfg)
    assert np.allclose(
        floored.min_gen[1, 10:13], cfg.caiso_ra_st_min_load_frac * fa.pmax[1]
    )
    assert floored.min_gen[1, :10].max() == 0.0 and floored.min_gen[1, 13:].max() == 0.0
    assert np.all(floored.min_gen_mechanism[1, 10:13] == MECH_RA_MUSTOFFER)
    assert np.allclose(
        floored.min_gen[0, 10:13], cfg.caiso_ra_min_load_frac * fa.pmax[0]
    )


def test_fast_start_ct_never_bridged_either_way():
    """Physics, not class: the 1 h min-down CT is never held across the gap."""
    for gate in (False, True):
        cfg = ScenarioConfig(
            hours=T,
            caiso_ra_mustoffer=True,
            caiso_ra_mustoffer_physics_eligibility=gate,
        )
        floored, _ = _floor(cfg)
        assert floored.min_gen[2].max() == 0.0


def test_cc_floor_identical_on_and_off():
    """The gate moves only the steam row: the CC row is the same array on and off."""
    off, _ = _floor(ScenarioConfig(hours=T, caiso_ra_mustoffer=True))
    on, _ = _floor(
        ScenarioConfig(
            hours=T,
            caiso_ra_mustoffer=True,
            caiso_ra_mustoffer_physics_eligibility=True,
        )
    )
    assert np.array_equal(off.min_gen[0], on.min_gen[0])
    assert np.array_equal(off.min_gen[2], on.min_gen[2])
