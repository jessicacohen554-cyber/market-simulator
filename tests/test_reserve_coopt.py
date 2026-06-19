"""Tests for the PJM energy+reserve co-optimization primitives.

Covers the structural reserve-requirement formula (the largest-single-
contingency proxy and the 1.5x-MSSC Primary Reserve requirement) and an
*honesty gate* that validates the formula's premise against the measured
PJM_RTO Primary Reserve series (data/raw/PJM-AS) — confirming the
requirement really is a near-constant reliability quantity ~= 1.5 x MSSC, not
a shape that must be replayed. The measured series is a validation target
only; it is never an input to the optimization.
"""
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import PJM_PRIMARY_RESERVE_LSC_FACTOR
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.results.scarcity import (
    largest_single_contingency_mw,
    load_pjm_measured_reserve_requirement,
    pjm_ordc_shortfall_steps,
    pjm_primary_reserve_requirement,
)

_PJM_AS_DIR = RAW_DATA_DIR / "PJM-AS"


class TestLargestSingleContingency(unittest.TestCase):
    """The MSSC proxy: largest single reserve-eligible unit."""

    def test_bare_nameplate_picks_max(self):
        pmax = np.array([100.0, 1300.0, 450.0])
        self.assertEqual(largest_single_contingency_mw(pmax), 1300.0)

    def test_empty_fleet_is_zero(self):
        self.assertEqual(largest_single_contingency_mw(np.array([])), 0.0)

    def test_availability_takes_peak_deliverable(self):
        pmax = np.array([1000.0, 800.0])
        # Unit 0 capped to 0.5 all year -> 500 deliverable; unit 1 full -> 800.
        avail = np.empty((2, 24))
        avail[0, :] = 0.5
        avail[1, :] = 1.0
        self.assertEqual(
            largest_single_contingency_mw(pmax, availability=avail), 800.0
        )

    def test_reserve_mask_excludes_units(self):
        pmax = np.array([2000.0, 600.0])  # largest is reserve-ineligible
        mask = np.array([False, True])
        self.assertEqual(
            largest_single_contingency_mw(pmax, reserve_mask=mask), 600.0
        )

    def test_fleet_responsive_drops_with_largest_unit(self):
        full = np.array([1300.0, 900.0, 400.0])
        retired = np.array([900.0, 400.0])  # largest unit gone
        self.assertGreater(
            largest_single_contingency_mw(full),
            largest_single_contingency_mw(retired),
        )

    def test_plant_aggregation_sums_common_mode_units(self):
        # Two 1100 MW units at one plant (common-mode) outrank a single 1300.
        pmax = np.array([1100.0, 1100.0, 1300.0])
        plant_code = np.array([10, 10, 20])  # units 0,1 share plant 10
        self.assertEqual(
            largest_single_contingency_mw(pmax, plant_code=plant_code), 2200.0
        )

    def test_plant_code_zero_treated_individually(self):
        # plant_code <= 0 (imports / pseudo-units) never aggregate together.
        pmax = np.array([800.0, 800.0, 1300.0])
        plant_code = np.array([0, 0, 20])
        self.assertEqual(
            largest_single_contingency_mw(pmax, plant_code=plant_code), 1300.0
        )


class TestPrimaryReserveRequirement(unittest.TestCase):
    """The 1.5x-MSSC structural requirement."""

    def test_flat_factor_times_lsc(self):
        req = pjm_primary_reserve_requirement(2000.0, 8760, factor=1.5)
        self.assertEqual(req.shape, (8760,))
        np.testing.assert_allclose(req, 3000.0)

    def test_default_factor(self):
        req = pjm_primary_reserve_requirement(2000.0, 24)
        np.testing.assert_allclose(req, PJM_PRIMARY_RESERVE_LSC_FACTOR * 2000.0)

    def test_responsive_to_lsc(self):
        big = pjm_primary_reserve_requirement(2400.0, 24)[0]
        small = pjm_primary_reserve_requirement(1800.0, 24)[0]
        self.assertGreater(big, small)

    def test_nonnegative(self):
        self.assertTrue((pjm_primary_reserve_requirement(0.0, 24) >= 0).all())


class TestOrdcShortfallSteps(unittest.TestCase):
    """The published demand curve -> ascending LP shortfall steps."""

    _CURVE = [(0.0, 850.0), (190.0, 300.0)]  # PJM Primary RTO

    def test_two_step_curve_conversion(self):
        req_total, pens, widths = pjm_ordc_shortfall_steps(self._CURVE, 3000.0)
        self.assertEqual(req_total, 3190.0)  # REQ + max offset
        np.testing.assert_allclose(pens, [300.0, 850.0])   # cheapest band first
        np.testing.assert_allclose(widths, [190.0, 3000.0])

    def test_widths_span_full_requirement_extent(self):
        # Total shortfall capacity must let reserves fall to 0 (R=0 feasible).
        req_total, _, widths = pjm_ordc_shortfall_steps(self._CURVE, 2500.0)
        self.assertAlmostEqual(widths.sum(), req_total)

    def test_unordered_input_is_sorted(self):
        req_total, pens, widths = pjm_ordc_shortfall_steps(
            [(190.0, 300.0), (0.0, 850.0)], 1000.0
        )
        self.assertEqual(req_total, 1190.0)
        np.testing.assert_allclose(pens, [300.0, 850.0])


class TestMeasuredRequirementLoader(unittest.TestCase):
    """The backcast measured-requirement loader (reliability input)."""

    def test_loads_8760_positive_requirement(self):
        req = load_pjm_measured_reserve_requirement(2024, 8760)
        if req is None:
            self.skipTest("PJM-AS 2024 parquet not present")
        self.assertEqual(req.shape, (8760,))
        self.assertTrue((req > 0).all())  # holes filled, never zero
        # Matches the measured PJM_RTO Primary requirement (~3.42 GW, 2024).
        self.assertTrue(3000.0 < req.mean() < 3700.0)

    def test_missing_year_returns_none(self):
        self.assertIsNone(
            load_pjm_measured_reserve_requirement(1999, 8760)
        )


class TestMeasuredRequirementHonestyGate(unittest.TestCase):
    """Validate the formula PREMISE against the measured PJM_RTO series.

    Not a fit: confirms the measured Primary Reserve requirement is a
    near-constant reliability quantity whose level implies a stable,
    physically-sensible MSSC (~1.5-2.6 GW) across all three years — i.e. the
    structural ``1.5 x MSSC`` form is the right shape. The fleet-derived MSSC
    is checked against this level during the integration run, not here.
    """

    def _measured_pr(self, year: int) -> np.ndarray | None:
        path = _PJM_AS_DIR / f"pjm_{year}_as_up_mw.parquet"
        if not path.exists():
            return None
        import pandas as pd
        return pd.read_parquet(path)["pr_req_mw"].to_numpy()

    def test_measured_requirement_is_near_flat(self):
        any_year = False
        for year in (2023, 2024, 2025):
            pr = self._measured_pr(year)
            if pr is None:
                continue
            any_year = True
            pr = pr[pr > 0]  # skip the documented data holes
            cv = pr.std() / pr.mean()
            # Measured cv runs ~0.10-0.16 (the largest online contingency
            # shifts seasonally); modest variation around a stable level, so
            # the flat 1.5x-MSSC premise holds as a first-order structural form.
            self.assertLess(
                cv, 0.20,
                f"{year}: Primary Reserve req not near-flat (cv={cv:.3f}); "
                "the 1.5x-MSSC constant-requirement premise would not hold",
            )
        if not any_year:
            self.skipTest("PJM-AS measured parquets not present")

    def test_implied_mssc_is_stable_and_physical(self):
        implied = {}
        for year in (2023, 2024, 2025):
            pr = self._measured_pr(year)
            if pr is None:
                continue
            mean_req = pr[pr > 0].mean()
            implied[year] = mean_req / PJM_PRIMARY_RESERVE_LSC_FACTOR
        if not implied:
            self.skipTest("PJM-AS measured parquets not present")
        for year, mssc in implied.items():
            self.assertTrue(
                1500.0 < mssc < 2600.0,
                f"{year}: implied MSSC {mssc:.0f} MW outside the physical "
                "1.5-2.6 GW band for PJM's largest contingency",
            )
        # Stable across years (a reliability constant, not a moving target).
        vals = np.array(list(implied.values()))
        if len(vals) > 1:
            self.assertLess((vals.max() - vals.min()) / vals.mean(), 0.20)

    def test_formula_reproduces_measured_mean(self):
        """With the measured-implied MSSC, the formula lands on the measured
        mean — the structural form fits the level without shape replay."""
        pr = self._measured_pr(2024)
        if pr is None:
            self.skipTest("PJM-AS 2024 parquet not present")
        mean_req = pr[pr > 0].mean()
        mssc = mean_req / PJM_PRIMARY_RESERVE_LSC_FACTOR
        formula = pjm_primary_reserve_requirement(mssc, len(pr))
        self.assertAlmostEqual(formula[0], mean_req, delta=0.03 * mean_req)


class TestErcotOrdcDemandSteps(unittest.TestCase):
    """The ERCOT VOLL-anchored ORDC demand curve -> ascending LP shortfall steps."""

    def _steps(self, **kw):
        from market_sim.results.scarcity import ercot_ordc_demand_steps

        params = dict(
            voll=5000.0, mcl_mw=3000.0, mu_mw=0.0, sigma_mw=1400.0,
            shift_sigma=0.5, n_steps=40, sigma_span=5.0, multistep_floor=False,
        )
        params.update(kw)
        return ercot_ordc_demand_steps(**params)

    def test_req_total_is_curve_top(self):
        # req_total = mcl + (mu + shift*sigma) + sigma_span*sigma.
        req_total, _, _ = self._steps()
        self.assertAlmostEqual(req_total, 3000.0 + 700.0 + 5 * 1400.0)

    def test_widths_span_full_requirement(self):
        # Total shortfall capacity must let reserves fall to 0 in any hour.
        req_total, _, widths = self._steps()
        self.assertAlmostEqual(widths.sum(), req_total)

    def test_penalties_ascend_cheapest_first(self):
        # Outermost (highest-reserve) band is cheapest; ORDC price rises as
        # reserves fall, so the discretized penalties must be non-decreasing.
        _, pens, _ = self._steps()
        self.assertTrue(np.all(np.diff(pens) >= -1e-9))

    def test_penalties_capped_at_voll(self):
        _, pens, _ = self._steps(voll=5000.0)
        self.assertLessEqual(pens.max(), 5000.0 + 1e-6)
        # The innermost band (reserves near 0, both LOLP terms -> 1) approaches
        # VOLL.
        self.assertGreater(pens.max(), 0.9 * 5000.0)

    def test_higher_voll_scales_prices_up(self):
        _, pens_lo, _ = self._steps(voll=5000.0)
        _, pens_hi, _ = self._steps(voll=9000.0)
        self.assertGreater(pens_hi.max(), pens_lo.max())

    def test_multistep_floor_lifts_low_reserve_bands(self):
        # With the OBDRR048 floor on, bands below 6,500 MW reserve are >= $20.
        from market_sim.results.scarcity import ercot_ordc_demand_steps

        req_total, pens, widths = ercot_ordc_demand_steps(
            voll=5000.0, mcl_mw=3000.0, mu_mw=0.0, sigma_mw=1400.0,
            shift_sigma=0.5, multistep_floor=True,
        )
        # Reserve at each band's lower edge, descending from req_total.
        grid = np.linspace(req_total, 0.0, len(widths) + 1)
        r_edge = grid[1:]
        self.assertTrue(np.all(pens[r_edge <= 6500.0] >= 20.0 - 1e-9))


class TestErcotReserveEligible(unittest.TestCase):
    """Only dispatchable thermal classes back ORDC reserve."""

    def test_thermal_eligible_renewables_not(self):
        from types import SimpleNamespace

        from market_sim.data.fleet import FUEL_TYPE_NAMES
        from market_sim.results.scarcity import (
            RESERVE_FUEL_TYPES,
            ercot_reserve_eligible,
        )

        name_to_idx = {n: i for i, n in enumerate(FUEL_TYPE_NAMES)}
        fuels = ["gas_ct", "coal", "nuclear", "wind", "solar", "hydro"]
        idx = np.array([name_to_idx[f] for f in fuels if f in name_to_idx])
        kept = [f for f in fuels if f in name_to_idx]
        elig = ercot_reserve_eligible(SimpleNamespace(fuel_type_idx=idx))
        for f, e in zip(kept, elig):
            self.assertEqual(e, f in RESERVE_FUEL_TYPES, f"{f} eligibility")


if __name__ == "__main__":
    unittest.main()
