"""``chp_layup_duty_split`` — the CHP lay-up (capacity-only cogen) offer split.

nyiso-148: the cogeneration sibling of ``cc_reserve_duty_split``, disjoint
from it by class scope. A CHP plant in the measured lay-up census offers its
whole dispatchable capacity at the class curve's peak band; default OFF is
byte-identical and the census artifact is not even read.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.data.fleet.campd_bins import (
    _chp_layup_cohort,
    _reserve_duty_cohort,
    fleet_to_bins,
)


def _gen(code, group="CC_CHP", name="P", pmax=100.0, hr=8.5):
    return Generator(
        unit_id=f"{name}{code}{group}",
        name=name,
        zone="z",
        fuel_type="gas_cc",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=hr,
        eford=0.0,
        plant_group=group,
        plant_code=code,
    )


class TestChpLayupDutySplit(unittest.TestCase):
    def setUp(self):
        _chp_layup_cohort.cache_clear()
        _reserve_duty_cohort.cache_clear()

    def tearDown(self):
        _chp_layup_cohort.cache_clear()
        _reserve_duty_cohort.cache_clear()

    def _bins(self, cfg, cohort, gens=None):
        import market_sim.data.chp_layup as seam

        gens = gens or [_gen(1111), _gen(2222)]
        original = seam.load_chp_layup_census
        seam.load_chp_layup_census = lambda iso: frozenset(cohort)
        try:
            return fleet_to_bins(gens, "NYISO", cfg)
        finally:
            seam.load_chp_layup_census = original

    def test_default_off_is_byte_identical(self):
        base = self._bins(ScenarioConfig(iso="NYISO"), {1111})
        off = self._bins(
            ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_split=False),
            {1111},
        )
        for col in ("pct_mc", "pct_econ", "pct_peak"):
            np.testing.assert_array_equal(base[col].to_numpy(), off[col].to_numpy())

    def test_armed_routes_only_the_cohort_to_the_peak_band(self):
        cfg = ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_split=True)
        bins = self._bins(cfg, {1111}).set_index("Plant_Code")
        self.assertEqual(float(bins.loc[1111, "pct_mc"]), 0.0)
        self.assertEqual(float(bins.loc[1111, "pct_econ"]), 0.0)
        self.assertAlmostEqual(
            float(bins.loc[1111, "pct_peak"] + bins.loc[1111, "pct_mr"]), 100.0
        )
        self.assertGreater(
            float(bins.loc[1111, "hr_peak"]), float(bins.loc[1111, "hr_econ"])
        )
        self.assertGreater(float(bins.loc[2222, "pct_econ"]), 0.0)

    def test_scope_is_the_chp_classes_only(self):
        """A census code that is ALSO a CC_REGULAR row must not be re-banded.

        The two duty splits are disjoint by class (rule 19 [R-ONE-MECH]); this
        pins that the CHP leg cannot reach a non-CHP tranche even when the
        plant code is in its census.
        """
        cfg = ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_split=True)
        gens = [_gen(1111, "CC_CHP"), _gen(1111, "CC_REGULAR")]
        bins = self._bins(cfg, {1111}, gens).set_index("Plant_Group")
        self.assertEqual(float(bins.loc["CC_CHP", "pct_econ"]), 0.0)
        self.assertGreater(float(bins.loc["CC_REGULAR", "pct_econ"]), 0.0)

    def test_committed_census_carries_the_nyiso_cohort_and_abstains(self):
        from market_sim.data.chp_layup import load_chp_layup_census

        codes = load_chp_layup_census("NYISO")
        # The seven measured laid-up cogens qualify (Selkirk + Lockport are
        # the material ones; the five Indeck/Beaver Falls plants are already
        # heavily derated by the outage envelope)...
        for c in (10725, 54041, 10617, 54076, 50450, 50451, 50449):
            self.assertIn(c, codes)
        # ...the CAMPD-INVISIBLE plants are ABSTAINED ON, not convicted — a
        # silent meter is no evidence (identically-zero CAMPD series against
        # 439-950 GWh of EIA-923 net)...
        for c in (10025, 54099, 50368):
            self.assertNotIn(c, codes)
        # ...and the operating cogens are untouched.
        for c in (54547, 50006, 56259, 2493, 54914, 50458):
            self.assertNotIn(c, codes)

    def test_disjoint_from_the_cc_reserve_duty_cohort(self):
        """Rule 19 [R-ONE-MECH]: the two censuses can never overlap."""
        from market_sim.data.chp_layup import load_chp_layup_census
        from market_sim.data.reserve_duty import load_reserve_duty_cc

        self.assertEqual(
            load_chp_layup_census("NYISO") & load_reserve_duty_cc("NYISO"),
            frozenset(),
        )

    def test_unknown_iso_is_empty(self):
        from market_sim.data.chp_layup import load_chp_layup_census

        self.assertEqual(load_chp_layup_census("NOSUCHISO"), frozenset())


if __name__ == "__main__":
    unittest.main()
