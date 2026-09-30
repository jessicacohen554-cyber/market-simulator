"""Validation of the PJM gas commitment bridge (lane PJM-NEXT-16).

Covers :func:`market_sim.pipeline.commitment.build_pjm_gas_bridge_p1_prep` and
its floor :func:`market_sim.pipeline.commitment._pjm_gas_bridge_floor` — the PJM
leg of the P1-native committed-state bridge family (the SPP leg's construction
on PJM's own measured statistics). Contract:

* flag off / non-PJM ⇒ ``None`` (byte-identical P1); the field is registered in
  the cache-key drop set at its declared default so the default key is unmoved;
* only ``gas_cc`` (CC_REGULAR) is offered, at ``constants.PJM_GAS_BRIDGE_MIN_LOAD_FRAC``
  / ``_MIN_RUN_HOURS``; gas steam, CTs and cogens are never floored;
* rule 19: it REPLACES ``cc_mustrun_per_plant`` and cannot share the P1
  fleet-prep slot with PJM's commitment-scoped reserve hook — both refused;
* D-2 attribution: floored gen-hours tagged ``MECH_PJM_GAS_COMMITMENT_BRIDGE``,
  named and ablation-covered.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    PJM_GAS_BRIDGE_MIN_LOAD_FRAC,
    PJM_GAS_BRIDGE_MIN_RUN_HOURS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_ABLATION_FIELDS,
    MECH_NAMES,
    MECH_PJM_GAS_COMMITMENT_BRIDGE,
    MECH_SPP_GAS_COMMITMENT_BRIDGE,
    assert_ablation_coverage,
)
from market_sim.pipeline.commitment import (
    _pjm_bridge_min_run_hours,
    _pjm_gas_bridge_floor,
    build_pjm_gas_bridge_p1_prep,
)

_HOURS = 72


def _gen(unit_id, fuel, plant_group, pmax=300.0, heat_rate=7.0):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=heat_rate,
        eford=0.0,
        plant_group=plant_group,
    )


def _fleet():
    """One CC, one gas steamer, one CT and one cogen CC."""
    gens = [
        _gen("cc1", "gas_cc", "CC_REGULAR", pmax=400.0, heat_rate=7.0),
        _gen("st1", "gas_st", "ST_GAS", pmax=500.0, heat_rate=11.0),
        _gen("ct1", "gas_ct", "CT_PEAKER", pmax=100.0, heat_rate=10.5),
        _gen("chp1", "gas_cc", "CC_CHP", pmax=200.0, heat_rate=7.0),
    ]
    return gens, generators_to_fleet_arrays(gens, ["z"], _HOURS)


def _rich_p0(fa):
    """Every unit runs h0-24 and h40-72; prices far above MC."""
    d = np.zeros((len(fa.pmax), _HOURS))
    d[:, :24] = fa.pmax[:, None]
    d[:, 40:] = fa.pmax[:, None]
    return d, np.full((1, _HOURS), 500.0), np.full(d.shape, 20.0)


class _R0:
    def __init__(self, dispatch, prices):
        self.dispatch = dispatch
        self.prices = prices


def _pjm(**over):
    return ScenarioConfig(iso="PJM").with_overrides(**over)


class TestPjmBridge(unittest.TestCase):
    def test_measured_constants(self):
        # campd_gas_commitment_params_plant_PJM.csv (CAMPD 2023-2025, plant
        # basis): CC_REGULAR HSL-weighted p50 0.436, cap-weighted p25 run 11 h.
        self.assertEqual(PJM_GAS_BRIDGE_MIN_LOAD_FRAC, {"gas_cc": 0.436})
        self.assertEqual(PJM_GAS_BRIDGE_MIN_RUN_HOURS, {"gas_cc": 11.0})

    def test_min_run_vector_is_cc_only(self):
        gens, _fa = _fleet()
        mr = _pjm_bridge_min_run_hours(gens)
        self.assertEqual(mr.tolist(), [11.0, 0.0, 0.0, 0.0])

    def test_only_the_cc_is_floored_at_its_measured_fraction(self):
        gens, fa = _fleet()
        d, prices, mc = _rich_p0(fa)
        floor = _pjm_gas_bridge_floor(gens, fa, d, prices, mc)
        self.assertIsNotNone(floor)
        self.assertTrue(np.allclose(floor[0, 24:40], 0.436 * 400.0))
        self.assertTrue(np.all(floor[1:] == 0.0))

    def test_gate_and_iso_scope(self):
        gens, fa = _fleet()
        mc = np.zeros((len(gens), _HOURS))
        off = ScenarioConfig(iso="PJM")
        self.assertIsNone(build_pjm_gas_bridge_p1_prep(off, "PJM", gens, fa, mc))
        on = _pjm(pjm_gas_commitment_bridge=True, cc_mustrun_per_plant=False)
        self.assertIsNone(build_pjm_gas_bridge_p1_prep(on, "SPP", gens, fa, mc))
        prep = build_pjm_gas_bridge_p1_prep(on, "PJM", gens, fa, mc)
        d, prices, _mc = _rich_p0(fa)
        fa_p1 = prep(_R0(d, prices))
        mech = np.asarray(fa_p1.min_gen_mechanism)
        self.assertTrue(np.all(mech[0, 24:40] == MECH_PJM_GAS_COMMITMENT_BRIDGE))
        self.assertTrue(np.all(mech[1:] != MECH_PJM_GAS_COMMITMENT_BRIDGE))

    def test_rule19_refusals(self):
        with self.assertRaises(ValueError):
            _pjm(pjm_gas_commitment_bridge=True, cc_mustrun_per_plant=True)
        with self.assertRaises(ValueError):
            ScenarioConfig(iso="SPP").with_overrides(pjm_gas_commitment_bridge=True)
        with self.assertRaises(ValueError):
            _pjm(
                pjm_gas_commitment_bridge=True,
                cc_mustrun_per_plant=False,
                energy_reserve_coopt=True,
                pjm_reserve_commitment_scoped=True,
            )

    def test_default_key_unmoved_and_armed_key_distinct(self):
        base = ScenarioConfig(iso="PJM")
        explicit = base.with_overrides(pjm_gas_commitment_bridge=False)
        self.assertEqual(base.cache_key(), explicit.cache_key())
        armed = base.with_overrides(
            pjm_gas_commitment_bridge=True, cc_mustrun_per_plant=False
        )
        self.assertNotEqual(
            base.with_overrides(cc_mustrun_per_plant=False).cache_key(),
            armed.cache_key(),
        )

    def test_mechanism_named_distinct_and_ablated(self):
        self.assertNotEqual(
            MECH_PJM_GAS_COMMITMENT_BRIDGE, MECH_SPP_GAS_COMMITMENT_BRIDGE
        )
        self.assertEqual(
            MECH_NAMES[MECH_PJM_GAS_COMMITMENT_BRIDGE], "pjm_gas_commitment_bridge"
        )
        self.assertEqual(
            MECH_ABLATION_FIELDS[MECH_PJM_GAS_COMMITMENT_BRIDGE],
            {"pjm_gas_commitment_bridge": False},
        )
        assert_ablation_coverage()


if __name__ == "__main__":
    unittest.main()
