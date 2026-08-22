"""``chp_layup_duty_curve`` — the graded price-conditional lay-up offer.

nyiso-149: the successor to the single-band ``chp_layup_duty_split`` (rejected
nyiso-148 — bang-bang where the meters are graded). A frozen-census plant
offers its measured duty — ``pct_econ`` of model capacity at the class econ
band, ``pct_peak`` at the class peak band — and WITHHOLDS the remainder from
the offer entirely. These tests pin BOTH seams (the fleet_to_bins frame AND
the load-bearing ``bins_to_fleet`` cap override — the seam whose omission made
two sibling arms inert), the default-off byte identity, the rule-19 mutual
exclusion, and the committed artifact's own invariants.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.data.fleet.campd_bins import (
    _chp_duty_curve,
    _chp_layup_cohort,
    _reserve_duty_cohort,
    fleet_to_bins,
)
from market_sim.data.fleet.assembly import bins_to_fleet

COHORT = 1111
OTHER = 2222
# The duty tuple is a MW quantity (econ_mw, peak_mw) — PREREG-nyiso149 §7:
# the first solve treated it as a pct of one capacity basis applied to
# another and over-offered by the basis ratio (caught by gate F-K2).
DUTY = {COHORT: (20.0, 10.0)}  # econ_mw, peak_mw


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


class TestChpLayupDutyCurve(unittest.TestCase):
    def setUp(self):
        _chp_layup_cohort.cache_clear()
        _chp_duty_curve.cache_clear()
        _reserve_duty_cohort.cache_clear()
        import market_sim.data.chp_layup as seam

        self._orig_census = seam.load_chp_layup_census
        self._orig_curve = seam.load_chp_duty_curve
        seam.load_chp_layup_census = lambda iso: frozenset({COHORT})
        seam.load_chp_duty_curve = lambda iso: dict(DUTY)

    def tearDown(self):
        import market_sim.data.chp_layup as seam

        seam.load_chp_layup_census = self._orig_census
        seam.load_chp_duty_curve = self._orig_curve
        _chp_layup_cohort.cache_clear()
        _chp_duty_curve.cache_clear()
        _reserve_duty_cohort.cache_clear()

    def _bins(self, cfg, gens=None):
        gens = gens or [_gen(COHORT), _gen(OTHER)]
        return fleet_to_bins(gens, "NYISO", cfg)

    def test_default_off_is_byte_identical(self):
        base = self._bins(ScenarioConfig(iso="NYISO"))
        off = self._bins(
            ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_curve=False)
        )
        for col in ("pct_mc", "pct_econ", "pct_peak"):
            np.testing.assert_array_equal(base[col].to_numpy(), off[col].to_numpy())

    def test_frame_seam_writes_the_measured_fractions(self):
        cfg = ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_curve=True)
        bins = self._bins(cfg).set_index("Plant_Code")
        self.assertEqual(float(bins.loc[COHORT, "pct_mc"]), 0.0)
        self.assertAlmostEqual(float(bins.loc[COHORT, "pct_econ"]), 20.0)
        self.assertAlmostEqual(float(bins.loc[COHORT, "pct_peak"]), 10.0)
        # the non-census plant keeps its class split
        self.assertGreater(float(bins.loc[OTHER, "pct_econ"]), 30.0)

    def test_load_bearing_seam_withholds_the_remainder(self):
        """bins_to_fleet: offered tranches sum to econ+peak, NOT to capacity.

        The econ residual re-absorbing the withheld share is exactly how a
        pct-level override would silently fail — the caps must shrink.
        """
        cfg = ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_curve=True)
        bins = self._bins(cfg)
        fleet, _ = bins_to_fleet(bins, ["z"], cfg)
        cohort_units = [g for g in fleet if g.plant_code == COHORT]
        other_units = [g for g in fleet if g.plant_code == OTHER]
        self.assertTrue(cohort_units)
        offered = sum(g.pmax_mw for g in cohort_units)
        self.assertAlmostEqual(offered, 100.0 * (20.0 + 10.0) / 100.0, places=3)
        self.assertFalse(any("_committed" in g.unit_id for g in cohort_units))
        peak = sum(g.pmax_mw for g in cohort_units if "_peak" in g.unit_id)
        self.assertAlmostEqual(peak, 10.0, places=3)
        # the non-census plant offers (essentially) its whole capacity
        self.assertGreater(sum(g.pmax_mw for g in other_units), 95.0)

    def test_flag_off_bins_to_fleet_is_unchanged(self):
        cfg_off = ScenarioConfig(iso="NYISO")
        bins = self._bins(cfg_off)
        fleet, _ = bins_to_fleet(bins, ["z"], cfg_off)
        offered = sum(g.pmax_mw for g in fleet if g.plant_code == COHORT)
        self.assertGreater(offered, 95.0)

    def test_mutual_exclusion_with_the_split(self):
        cfg = ScenarioConfig(iso="NYISO").with_overrides(
            chp_layup_duty_curve=True, chp_layup_duty_split=True
        )
        with self.assertRaises(ValueError):
            self._bins(cfg)

    def test_membership_stays_with_the_census(self):
        """A plant in the artifact but NOT the census is never re-banded."""
        import market_sim.data.chp_layup as seam

        seam.load_chp_layup_census = lambda iso: frozenset()  # census empty
        _chp_layup_cohort.cache_clear()
        cfg = ScenarioConfig(iso="NYISO").with_overrides(chp_layup_duty_curve=True)
        bins = self._bins(cfg).set_index("Plant_Code")
        self.assertGreater(float(bins.loc[COHORT, "pct_econ"]), 30.0)


class TestCommittedArtifact(unittest.TestCase):
    def test_artifact_covers_exactly_the_census_and_offers_are_sane(self):
        from market_sim.data.chp_layup import (
            load_chp_duty_curve,
            load_chp_layup_census,
        )

        import csv

        from market_sim.config.paths import PROCESSED_DIR

        curve = load_chp_duty_curve("NYISO")
        census = load_chp_layup_census("NYISO")
        self.assertEqual(set(curve), set(census))
        with (PROCESSED_DIR / "chp_duty_curve_NYISO.csv").open(newline="") as fh:
            rows = {int(r["plant_code"]): r for r in csv.DictReader(fh)}
        for code, (pe_mw, pp_mw) in curve.items():
            self.assertGreaterEqual(pe_mw, 0.0, code)
            self.assertGreaterEqual(pp_mw, 0.0, code)
            # the whole point: a graded, PARTIAL offer — the offered MW never
            # reaches the plant's own observed HSL, let alone its capacity
            hsl = float(rows[code]["hsl_mw"])
            pmax = float(rows[code]["pmax_mw"])
            self.assertLess(pe_mw + pp_mw, hsl, code)
            self.assertLess(pe_mw + pp_mw, pmax, code)
        # the graded signature that rejected the single band: every plant
        # carries a non-trivial econ leg (the split had zero)
        self.assertTrue(all(pe > 1.0 for pe, _ in curve.values()))

    def test_unknown_iso_is_empty(self):
        from market_sim.data.chp_layup import load_chp_duty_curve

        self.assertEqual(load_chp_duty_curve("NOSUCHISO"), {})


if __name__ == "__main__":
    unittest.main()
