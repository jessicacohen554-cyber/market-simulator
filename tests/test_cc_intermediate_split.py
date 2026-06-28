"""Tests for the MISO combined-cycle intermediate-duty offer-curve routing.

MISO's combined-cycle fleet runs baseload/intermediate (measured CAMPD median
CF 50-150 %), but the ``CC_REGULAR`` offer curve was fit to ERCOT's
duct-fire-heavy 2x1 peaker CCs: a rising start-cost-amortized econ ramp that
over-prices the upper operating range of an already-committed baseload CC and
under-runs the fleet (the 2023/2024 gas-CC under-run). When
``cc_intermediate_split`` is set, the measured median-CF >= threshold cohort
(:func:`~market_sim.data.fleet.cc_intermediate_plants`) routes to the flatter
``CC_INTERMEDIATE`` curve. Default off → CC_REGULAR (byte-identical). Mirrors the
CT/ST intermediate-split levers.
"""

import unittest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import _offer_curve_for_group, cc_intermediate_plants

_CURVES = {
    "CC_REGULAR": {
        "committed": 0.92,
        "econ_low": 1.06,
        "econ_high": 1.27,
        "peak": 2.25,
    },
    "CC_INTERMEDIATE": {
        "committed": 0.92,
        "econ_low": 0.95,
        "econ_high": 1.08,
        "peak": 2.25,
    },
}


class TestCcIntermediateCohort(unittest.TestCase):
    """The measured median-CF cohort is non-empty for MISO, empty off-scope."""

    def test_miso_cohort_nonempty(self):
        cohort = cc_intermediate_plants("MISO", 50.0)
        self.assertTrue(cohort)  # MISO's CC fleet measures baseload-duty
        self.assertTrue(all(isinstance(c, int) for c in cohort))

    def test_unmapped_iso_empty(self):
        # An ISO with no thermal_tranches CSV (e.g. ERCOT's hand-set bins) → empty.
        self.assertEqual(cc_intermediate_plants("NOTANISO", 50.0), frozenset())

    def test_higher_threshold_is_subset(self):
        lo = cc_intermediate_plants("MISO", 50.0)
        hi = cc_intermediate_plants("MISO", 65.0)
        self.assertTrue(hi <= lo)  # a stricter CF cut keeps fewer plants


class TestCcIntermediateRouting(unittest.TestCase):
    """``_offer_curve_for_group`` routes only the cohort, only when enabled."""

    def setUp(self):
        self.cohort_plant = next(iter(cc_intermediate_plants("MISO", 50.0)))

    def test_off_is_byte_identical(self):
        cfg = ScenarioConfig(iso="MISO", offer_curve_by_group=_CURVES)
        curve = _offer_curve_for_group("CC_REGULAR", self.cohort_plant, cfg)
        self.assertEqual(curve["econ_high"], 1.27)  # CC_REGULAR, unchanged

    def test_on_routes_cohort_to_intermediate(self):
        cfg = ScenarioConfig(
            iso="MISO", offer_curve_by_group=_CURVES, cc_intermediate_split=True
        )
        curve = _offer_curve_for_group("CC_REGULAR", self.cohort_plant, cfg)
        self.assertEqual(curve["econ_high"], 1.08)  # routed to CC_INTERMEDIATE
        # The physically-real duct-burner peak is unchanged (only the ramp moves).
        self.assertEqual(curve["peak"], _CURVES["CC_REGULAR"]["peak"])

    def test_on_leaves_noncohort_on_regular(self):
        cfg = ScenarioConfig(
            iso="MISO", offer_curve_by_group=_CURVES, cc_intermediate_split=True
        )
        # A plant code not in the measured cohort keeps the CC_REGULAR curve.
        curve = _offer_curve_for_group("CC_REGULAR", 999_999_999, cfg)
        self.assertEqual(curve["econ_high"], 1.27)

    def test_no_intermediate_curve_falls_back(self):
        # Flag on but no CC_INTERMEDIATE entry configured → CC_REGULAR (no crash).
        cfg = ScenarioConfig(
            iso="MISO",
            offer_curve_by_group={"CC_REGULAR": _CURVES["CC_REGULAR"]},
            cc_intermediate_split=True,
        )
        curve = _offer_curve_for_group("CC_REGULAR", self.cohort_plant, cfg)
        self.assertEqual(curve["econ_high"], 1.27)


if __name__ == "__main__":
    unittest.main()
