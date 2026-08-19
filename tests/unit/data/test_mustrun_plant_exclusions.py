"""Tests for the per-plant must-run floors' lay-up MEMBERSHIP correction.

``ScenarioConfig.mustrun_plant_exclusions`` (miso-170) drops economically
laid-up plants from ``cc_mustrun_per_plant`` / ``st_gas_mustrun_per_plant``
(the ``st_gas_mustrun_p25_level`` swap included). It is the MUST-RUN FLOORS'
half of a correction that previously existed only on the reliability floor
(``reliability_floor_plant_exclusions``, nyiso-140) and the NYISO commitment
bridge (``nyiso_gas_bridge_plant_exclusions``, nyiso-144): all three floor the
same merchant thermal plants, so each earlier fix repaired one MECHANISM rather
than the plant (rule 19 ``[R-ONE-MECH]``).

Contract: default OFF is byte-identical and never even opens the census;
armed, a listed plant loses its floor entirely while its unlisted neighbours
keep exactly the floor they had. The population is the SAME mechanism-blind
CAMPD lay-up census the bridge reads (rule 19 — lay-up is a property of the
site, so one identification serves every mechanism that floors it), so no
class-name tuple and no new parameter is involved.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_CC_MUSTRUN_PER_PLANT,
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
)

ZONES = ["MISO-South"]
_HOURS = 8760
# Nine Mile Point — carries a measured ST_GAS online_frac / p25_cf in the
# committed thermal_tranches_MISO.csv, so the p25-level path has a real row.
_KEEP_CODE = 1403
# Gerald Andrus — a real MISO lay-up census member (median gross load zero in
# every (year, 4 h block) cell of 2023-2025).
_DROP_CODE = 8054


def _config(**kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso="MISO", weather_year=2024, mode="backcast", hours=_HOURS, **kw
    )


def _gen(code: int, group: str, pmin_mw: float, frac: float) -> Generator:
    """One committed tranche carrying the measured must-run floor."""
    return Generator(
        unit_id=f"{group}_MISO-South_p{code}_committed",
        name=f"plant {code} committed",
        zone="MISO-South",
        fuel_type="gas_st" if group == "ST_GAS" else "gas_cc",
        pmax_mw=100.0,
        plant_group=group,
        plant_code=code,
        is_campd_bin=True,
        cc_mustrun_pmin_mw=pmin_mw,
        cc_mustrun_online_frac=frac,
    )


def _arrays(gens, cfg, stub_codes=None):
    """Build the arrays, optionally stubbing the census at its source module."""
    # The consuming import is function-local, so the SOURCE module is what a
    # stub has to replace — patching the caller's namespace would miss it.
    import market_sim.data.bridge_layup_exclusions as seam

    load = np.arange(_HOURS, 0, -1, dtype=float)
    if stub_codes is None:
        return generators_to_fleet_arrays(
            gens, ZONES, hours=_HOURS, iso="MISO", config=cfg, load_shape=load
        )
    original = seam.load_layup_exclusions
    seam.load_layup_exclusions = lambda iso: frozenset(stub_codes)
    try:
        return generators_to_fleet_arrays(
            gens, ZONES, hours=_HOURS, iso="MISO", config=cfg, load_shape=load
        )
    finally:
        seam.load_layup_exclusions = original


class TestCommittedTrancheLeg(unittest.TestCase):
    """The ``cc_mustrun``/``st_gas_mustrun`` committed-tranche floor."""

    def _fleet(self):
        return [
            _gen(_KEEP_CODE, "ST_GAS", 50.0, 0.25),
            _gen(_DROP_CODE, "ST_GAS", 50.0, 0.25),
        ]

    def test_default_off_is_byte_identical(self):
        """Off, the census is never read, so a stub cannot change anything."""
        base = _arrays(self._fleet(), _config())
        off = _arrays(
            self._fleet(), _config(mustrun_plant_exclusions=False), [_DROP_CODE]
        )
        self.assertIsNotNone(base.min_gen)
        np.testing.assert_array_equal(base.min_gen, off.min_gen)
        np.testing.assert_array_equal(base.min_gen_mechanism, off.min_gen_mechanism)

    def test_armed_drops_only_the_listed_plant(self):
        base = _arrays(self._fleet(), _config())
        armed = _arrays(
            self._fleet(), _config(mustrun_plant_exclusions=True), [_DROP_CODE]
        )
        self.assertGreater(float(base.min_gen[1].sum()), 0.0)
        self.assertEqual(float(armed.min_gen[1].sum()), 0.0)
        # The neighbour keeps exactly the floor it had, mechanism id included.
        np.testing.assert_array_equal(base.min_gen[0], armed.min_gen[0])
        np.testing.assert_array_equal(
            base.min_gen_mechanism[0], armed.min_gen_mechanism[0]
        )
        self.assertTrue((armed.min_gen_mechanism[1] == 0).all())

    def test_cc_leg_uses_the_same_gate(self):
        """The correction is per PLANT, not per class (rule 19)."""
        gens = [
            _gen(_KEEP_CODE, "CC_REGULAR", 50.0, 0.25),
            _gen(_DROP_CODE, "CC_REGULAR", 50.0, 0.25),
        ]
        armed = _arrays(gens, _config(mustrun_plant_exclusions=True), [_DROP_CODE])
        self.assertGreater(float(armed.min_gen[0].sum()), 0.0)
        self.assertEqual(float(armed.min_gen[1].sum()), 0.0)
        kept = armed.min_gen_mechanism[0]
        self.assertTrue(
            (kept[armed.min_gen[0] > 0.0] == MECH_CC_MUSTRUN_PER_PLANT).all()
        )


class TestP25LevelLeg(unittest.TestCase):
    """The ``st_gas_mustrun_p25_level`` swap — the level MISO actually arms.

    The p25 block reads the measured artifact directly rather than the
    generator's ``cc_mustrun_online_frac``, so it needs its own membership gate;
    without one the exclusion would be silently inert on the MISO keeper.
    """

    def _cfg(self, **kw):
        return _config(
            st_gas_mustrun_per_plant=True, st_gas_mustrun_p25_level=True, **kw
        )

    def _fleet(self):
        # pmin/frac are irrelevant here: the p25 block reads the artifact.
        return [
            _gen(_KEEP_CODE, "ST_GAS", 0.0, 0.0),
            _gen(_DROP_CODE, "ST_GAS", 0.0, 0.0),
        ]

    def test_both_plants_are_floored_unarmed(self):
        base = _arrays(self._fleet(), self._cfg())
        self.assertIsNotNone(base.min_gen)
        for i in (0, 1):
            self.assertGreater(
                float(base.min_gen[i].sum()),
                0.0,
                "both plants carry a measured p25 row — the fixture is stale",
            )
            floored = base.min_gen[i] > 0.0
            self.assertTrue(
                (
                    base.min_gen_mechanism[i][floored] == MECH_ST_GAS_MUSTRUN_PER_PLANT
                ).all()
            )

    def test_default_off_is_byte_identical(self):
        base = _arrays(self._fleet(), self._cfg())
        off = _arrays(
            self._fleet(), self._cfg(mustrun_plant_exclusions=False), [_DROP_CODE]
        )
        np.testing.assert_array_equal(base.min_gen, off.min_gen)

    def test_armed_drops_only_the_listed_plant(self):
        base = _arrays(self._fleet(), self._cfg())
        armed = _arrays(
            self._fleet(), self._cfg(mustrun_plant_exclusions=True), [_DROP_CODE]
        )
        self.assertEqual(float(armed.min_gen[1].sum()), 0.0)
        np.testing.assert_array_equal(base.min_gen[0], armed.min_gen[0])


class TestMisoCensus(unittest.TestCase):
    """The committed MISO census is what an armed MISO run actually reads."""

    def test_census_holds_the_identified_layups(self):
        from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

        codes = load_layup_exclusions("MISO")
        # The seven D-4-flagged plants the census selects WITHOUT being shown
        # any D-4 verdict (miso-170 §2).
        for code in (1104, 1131, 1702, 1891, 3992, 8054, 8056):
            self.assertIn(code, codes)
        # Little Gypsy is a cycler (6/18 zero cells, P(on)=0.51) and is
        # deliberately NOT excluded — its forcing is a window defect, and
        # burying it in a membership list is what rules 1/14 forbid.
        self.assertNotIn(1402, codes)

    def test_unknown_iso_is_empty(self):
        from market_sim.data.bridge_layup_exclusions import load_layup_exclusions

        self.assertEqual(load_layup_exclusions("NOSUCHISO"), frozenset())


if __name__ == "__main__":
    unittest.main()
