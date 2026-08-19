"""``cc_reserve_duty_split`` — the reserve-duty (capacity-only) CC offer split.

nyiso-146: the duty-role mirror of ``cc_intermediate_split``. A CC plant in
the measured capacity-only cohort offers its whole dispatchable capacity at
the class curve's peak band; default OFF is byte-identical and the artifact
is not even read.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.data.fleet.campd_bins import _reserve_duty_cohort, fleet_to_bins


def _gen(code, name="P", pmax=100.0, hr=8.5):
    return Generator(
        unit_id=f"{name}{code}",
        name=name,
        zone="z",
        fuel_type="gas_cc",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=hr,
        eford=0.0,
        plant_group="CC_REGULAR",
        plant_code=code,
    )


class TestReserveDutySplit(unittest.TestCase):
    def setUp(self):
        _reserve_duty_cohort.cache_clear()

    def tearDown(self):
        _reserve_duty_cohort.cache_clear()

    def _bins(self, cfg, cohort):
        import market_sim.data.reserve_duty as seam

        gens = [_gen(1111), _gen(2222)]
        original = seam.load_reserve_duty_cc
        seam.load_reserve_duty_cc = lambda iso: frozenset(cohort)
        try:
            return fleet_to_bins(gens, "NYISO", cfg)
        finally:
            seam.load_reserve_duty_cc = original

    def test_default_off_is_byte_identical(self):
        base = self._bins(ScenarioConfig(iso="NYISO"), {1111})
        off = self._bins(
            ScenarioConfig(iso="NYISO").with_overrides(cc_reserve_duty_split=False),
            {1111},
        )
        for col in ("pct_mc", "pct_econ", "pct_peak"):
            np.testing.assert_array_equal(base[col].to_numpy(), off[col].to_numpy())

    def test_armed_routes_only_the_cohort_to_the_peak_band(self):
        cfg = ScenarioConfig(iso="NYISO").with_overrides(cc_reserve_duty_split=True)
        bins = self._bins(cfg, {1111}).set_index("Plant_Code")
        # The cohort plant's whole grid capacity is the peak band...
        self.assertEqual(float(bins.loc[1111, "pct_mc"]), 0.0)
        self.assertEqual(float(bins.loc[1111, "pct_econ"]), 0.0)
        self.assertAlmostEqual(
            float(bins.loc[1111, "pct_peak"] + bins.loc[1111, "pct_mr"]), 100.0
        )
        # ...priced at the class's existing peak multiplier...
        self.assertGreater(
            float(bins.loc[1111, "hr_peak"]), float(bins.loc[1111, "hr_econ"])
        )
        # ...and the non-cohort neighbour keeps the normal split.
        self.assertGreater(float(bins.loc[2222, "pct_econ"]), 0.0)

    def test_committed_artifact_carries_the_nyiso_cohort(self):
        from market_sim.data.reserve_duty import load_reserve_duty_cc

        codes = load_reserve_duty_cc("NYISO")
        # The four nyiso-145 defect-B plants qualify...
        for c in (50744, 54592, 54593, 7784):
            self.assertIn(c, codes)
        # ...and the cyclers deliberately do not (their over-run is an
        # offer/commitment question, not a membership one).
        for c in (50978, 56188, 7314, 2539):
            self.assertNotIn(c, codes)

    def test_unknown_iso_is_empty(self):
        from market_sim.data.reserve_duty import load_reserve_duty_cc

        self.assertEqual(load_reserve_duty_cc("NOSUCHISO"), frozenset())
