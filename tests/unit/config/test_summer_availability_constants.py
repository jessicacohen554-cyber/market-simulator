"""Guard the seasonal-availability constants re-homed by miso-91.

``SUMMER_WEFOR_SHARE`` and ``SUMMER_CLASS_DERATE`` were module-private literals
in ``data/fleet/arrays.py``, which put them outside every governance channel at
once: ``scripts/validate_parameters.py`` scans only ``vars(constants)`` plus
``ScenarioConfig`` defaults and skips private/non-uppercase names, so the
constants were uncited (CLAUDE.md rule 5 ``[R-NO-MAGIC]``), unregistered and
off-registry (rule 20 ``[R-REGISTRY]``). miso-91 moved them to
``config/fuel_trajectories.py`` beside the ``THERMAL_AVAILABILITY`` table they
modify, with values unchanged.

These tests pin the three things a future edit could silently undo:

1. the VALUES, so neither is re-tuned (rule 24 ``[R-ANSWER-KEY]`` — both are
   declared free parameters in the MISO keeper's DOF ledger with open root
   causes, and ``SUMMER_WEFOR_SHARE`` governs capability at the same order of
   magnitude as the ledgered C3b caveat);
2. the HOME, so neither is re-privatised back out of registry coverage, and the
   ``data.fleet`` aliases keep resolving to the canonical objects rather than to
   a second literal that could drift;
3. the BRANCH MAP — which plant groups the summer WEFOR reallocation actually
   reaches under the MISO keeper's flags, including that COAL is exempt.
"""

import unittest

import numpy as np

from market_sim.config import constants
from market_sim.config.fuel_trajectories import (
    SUMMER_CLASS_DERATE,
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import arrays as fleet_arrays
from market_sim.data.fleet import Generator, generators_to_fleet_arrays

# The four flags that decide which availability branch a class takes, read from
# results/calibration/miso88_egrid_hr/run_config.json (the MISO keeper).
KEEPER_FLAGS = dict(
    # mode="backcast": outage_source="historic" is the ISO's MEASURED outage
    # record, a backcast-only overlay (FFR-1D rule-13 guard, audit FR-11) — and
    # the keeper these flags are read from is a backcast, so saying so here just
    # makes the fixture honest about the run it mirrors.
    mode="backcast",
    outage_source="historic",
    wefor_residual=None,
    coal_drop_pof=True,
    cc_nameplate_summer_derate=False,
    maintenance_monthly_shape=False,
)

# Every non-coal thermal group reaches the seasonal WEFOR split; COAL does not,
# because coal_drop_pof=True routes it to a branch that drops summer WEFOR
# outright (arrays.py, the `drop_coal_pof and fuel_type == "coal"` branch).
GOVERNED_GROUPS = {
    "CC_REGULAR": "gas_cc",
    "CC_CHP": "gas_cc",
    "ST_GAS": "gas_st",
    "ST_CHP": "gas_st",
    "CT_PEAKER": "gas_ct",
    "CT_CHP": "gas_ct",
}
EXEMPT_GROUPS = {"COAL": "coal"}

_JULY_H = 4400


def _summer_availability(group, fuel, share, online_year=2005):
    """Mid-July availability of one unit, with the share patched to ``share``."""
    original = fleet_arrays._SUMMER_WEFOR_SHARE
    fleet_arrays._SUMMER_WEFOR_SHARE = share
    try:
        gen = Generator(
            unit_id="g1",
            name="g1",
            zone="North",
            fuel_type=fuel,
            pmax_mw=100.0,
            pmin_mw=0.0,
            heat_rate=8.0,
            vom=2.0,
            emission_rate_co2=0.4,
            online_year=online_year,
            plant_group=group,
            efficiency_bin=group,
        )
        fa = generators_to_fleet_arrays(
            [gen], ["North"], config=ScenarioConfig(weather_year=2023, **KEEPER_FLAGS)
        )
        return float(fa.availability[0, _JULY_H])
    finally:
        fleet_arrays._SUMMER_WEFOR_SHARE = original


class TestSummerAvailabilityConstantValues(unittest.TestCase):
    """The values themselves — a change here is a re-tune, not a refactor."""

    def test_summer_wefor_share_value(self):
        self.assertEqual(SUMMER_WEFOR_SHARE, 0.30)

    def test_summer_class_derate_values(self):
        self.assertEqual(
            SUMMER_CLASS_DERATE,
            {
                "CC_REGULAR": 0.10,
                "CC_CHP": 0.10,
                "CT_PEAKER": 0.125,
                "CT_CHP": 0.125,
            },
        )

    def test_share_is_a_strict_reduction(self):
        # A share of 1.0 would mean "no seasonal reallocation"; > 1.0 would
        # invert the mechanism into a summer PENALTY without saying so.
        self.assertGreater(SUMMER_WEFOR_SHARE, 0.0)
        self.assertLess(SUMMER_WEFOR_SHARE, 1.0)


class TestSummerAvailabilityConstantHome(unittest.TestCase):
    """Registry coverage: public, uppercase, and reachable from constants."""

    def test_exported_from_constants(self):
        # validate_parameters.py only sees vars(constants); losing these
        # re-exports silently drops them out of the citation registry.
        self.assertIs(constants.SUMMER_WEFOR_SHARE, SUMMER_WEFOR_SHARE)
        self.assertIs(constants.SUMMER_CLASS_DERATE, SUMMER_CLASS_DERATE)

    def test_names_are_registry_visible(self):
        # The gate skips anything private or non-uppercase.
        for name in ("SUMMER_WEFOR_SHARE", "SUMMER_CLASS_DERATE"):
            self.assertFalse(name.startswith("_"), name)
            self.assertTrue(name.isupper(), name)

    def test_fleet_aliases_resolve_to_the_canonical_constants(self):
        # The private aliases are kept so the availability builder, the fleet
        # package's re-export contract and scarcity.py are untouched by the
        # move. They must stay references, never a second literal.
        self.assertEqual(fleet_arrays._SUMMER_WEFOR_SHARE, SUMMER_WEFOR_SHARE)
        self.assertIs(fleet_arrays._SUMMER_CLASS_DERATE, SUMMER_CLASS_DERATE)

    def test_fleet_package_still_reexports_them(self):
        from market_sim.data.fleet import (
            _SUMMER_CLASS_DERATE,
            _SUMMER_WEFOR_SHARE,
        )

        self.assertEqual(_SUMMER_WEFOR_SHARE, SUMMER_WEFOR_SHARE)
        self.assertIs(_SUMMER_CLASS_DERATE, SUMMER_CLASS_DERATE)


class TestSummerWeforBranchMap(unittest.TestCase):
    """Which classes the share actually governs under the MISO keeper's flags.

    miso-91 measured this because the miso-90 finding had scoped the parameter
    to CT_PEAKER alone; it in fact reaches all six non-coal thermal groups.
    """

    def test_all_non_coal_thermal_groups_are_governed(self):
        for group, fuel in GOVERNED_GROUPS.items():
            with self.subTest(group=group):
                shipped = _summer_availability(group, fuel, SUMMER_WEFOR_SHARE)
                neutral = _summer_availability(group, fuel, 1.0)
                # The share RAISES summer availability relative to the
                # no-reallocation baseline.
                self.assertGreater(shipped, neutral, group)

    def test_coal_is_exempt(self):
        for group, fuel in EXEMPT_GROUPS.items():
            with self.subTest(group=group):
                shipped = _summer_availability(group, fuel, SUMMER_WEFOR_SHARE)
                neutral = _summer_availability(group, fuel, 1.0)
                self.assertAlmostEqual(shipped, neutral, places=12, msg=group)

    def test_governed_delta_matches_the_closed_form(self):
        # delta = (1 - share) * wefor(age) * (1 - class_derate). Pinning the
        # closed form means a change to the seasonal mechanism cannot pass
        # unnoticed as a refactor.
        age = 2023 - 2005
        for group, fuel in GOVERNED_GROUPS.items():
            with self.subTest(group=group):
                _pof, w_base, w_rate, w_onset, *_ = THERMAL_AVAILABILITY[group]
                wefor = w_base + max(0.0, age - w_onset) * w_rate
                expected = (
                    (1.0 - SUMMER_WEFOR_SHARE)
                    * wefor
                    * (1.0 - SUMMER_CLASS_DERATE.get(group, 0.0))
                )
                actual = _summer_availability(
                    group, fuel, SUMMER_WEFOR_SHARE
                ) - _summer_availability(group, fuel, 1.0)
                self.assertAlmostEqual(actual, expected, places=10, msg=group)

    def test_st_gas_carries_the_largest_share_of_the_dof(self):
        # ST_GAS has the highest GADS WEFOR base (0.21) in the table, so it
        # takes the biggest single slice of this free parameter (+14.70 pp).
        # Recorded so the ranking is visible if the table is ever re-derived.
        deltas = {
            group: _summer_availability(group, fuel, SUMMER_WEFOR_SHARE)
            - _summer_availability(group, fuel, 1.0)
            for group, fuel in GOVERNED_GROUPS.items()
        }
        self.assertEqual(max(deltas, key=lambda g: deltas[g]), "ST_GAS")
        self.assertAlmostEqual(deltas["ST_GAS"], 0.147, places=4)

    def test_annual_outage_energy_is_conserved_by_the_reallocation(self):
        # The stated design claim: only the seasonal SHAPE moves. Checked on
        # ST_GAS, which carries no summer class derate to confound the mean.
        original = fleet_arrays._SUMMER_WEFOR_SHARE
        means = []
        try:
            for share in (SUMMER_WEFOR_SHARE, 1.0):
                fleet_arrays._SUMMER_WEFOR_SHARE = share
                gen = Generator(
                    unit_id="g1",
                    name="g1",
                    zone="North",
                    fuel_type="gas_st",
                    pmax_mw=100.0,
                    pmin_mw=0.0,
                    heat_rate=8.0,
                    vom=2.0,
                    emission_rate_co2=0.4,
                    online_year=2005,
                    plant_group="ST_GAS",
                    efficiency_bin="ST_GAS",
                )
                fa = generators_to_fleet_arrays(
                    [gen],
                    ["North"],
                    config=ScenarioConfig(weather_year=2023, **KEEPER_FLAGS),
                )
                means.append(float(np.mean(fa.availability[0])))
        finally:
            fleet_arrays._SUMMER_WEFOR_SHARE = original
        self.assertAlmostEqual(means[0], means[1], places=4)


if __name__ == "__main__":
    unittest.main()
