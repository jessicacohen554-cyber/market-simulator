"""Tests for ``market_sim.policy.ira`` -- §45U, §45Y/§48E, and the policy bundle."""

import unittest

from market_sim.config.scenarios import ScenarioConfig, resolve_policy_bundle
from market_sim.policy.ira import (
    SECTION_45U_CREDIT_CENTS_PER_KWH,
    ira_phaseout_fraction,
    section_45u_credit_per_mwh,
)


class TestSection45UCredit(unittest.TestCase):
    """IRA §45U existing-nuclear PTC as a $/MWh retirement-screen revenue input."""

    def test_full_credit_below_gross_receipts_threshold(self):
        # Below the 2.5-cents/kWh ($25/MWh) threshold, no phase-down applies.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 20.0, config)
        self.assertAlmostEqual(
            credit, SECTION_45U_CREDIT_CENTS_PER_KWH * 10.0
        )  # $15/MWh

    def test_zero_credit_after_expiry_year(self):
        config = ScenarioConfig()  # ira_45u_last_year = 2032
        self.assertGreater(section_45u_credit_per_mwh(2032, 20.0, config), 0.0)
        self.assertEqual(section_45u_credit_per_mwh(2033, 20.0, config), 0.0)

    def test_phases_down_above_gross_receipts_threshold(self):
        # avg_price = 30 $/MWh = 3.0 cents/kWh; excess over 2.5 = 0.5 cents;
        # reduction = 0.16 * 0.5 = 0.08 cents/kWh; credit = 1.5 - 0.08 = 1.42
        # cents/kWh = $14.20/MWh.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 30.0, config)
        self.assertAlmostEqual(credit, 14.2)

    def test_credit_floors_at_zero_at_high_gross_receipts(self):
        # An extremely high average price fully exhausts the credit rather
        # than going negative.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 10_000.0, config)
        self.assertEqual(credit, 0.0)

    def test_bundle_offset_shifts_45u_expiry_with_other_ira_cliffs(self):
        # The "tight" bundle applies a uniform +5yr IRA offset; §45U's
        # expiry year must move with it so all cliffs shift coherently.
        config = ScenarioConfig(policy_bundle="tight")
        resolved = resolve_policy_bundle(config)
        self.assertEqual(resolved.ira_45u_last_year, 2032 + 5)
        self.assertGreater(section_45u_credit_per_mwh(2037, 20.0, resolved), 0.0)
        self.assertEqual(section_45u_credit_per_mwh(2038, 20.0, resolved), 0.0)


class TestIRAPhaseoutFraction(unittest.TestCase):
    """§45Y/§48E tech-neutral (non-wind/solar) construction-begin-year step schedule."""

    def test_statute_triangulated_step_schedule(self):
        config = ScenarioConfig()
        self.assertEqual(ira_phaseout_fraction(2033, config), 1.0)
        self.assertAlmostEqual(ira_phaseout_fraction(2034, config), 0.75)
        self.assertAlmostEqual(ira_phaseout_fraction(2035, config), 0.50)
        self.assertEqual(ira_phaseout_fraction(2036, config), 0.0)
        self.assertEqual(ira_phaseout_fraction(2050, config), 0.0)

    def test_bundle_offset_shifts_all_four_breakpoints_together(self):
        # "rollback" pulls every ira_*_last_year field -2yr uniformly; the
        # new 75pct/50pct breakpoints must move with the existing two so the
        # step schedule's shape (100/75/50/0 in consecutive years) survives
        # the shift.
        config = ScenarioConfig(policy_bundle="rollback")
        resolved = resolve_policy_bundle(config)
        self.assertEqual(resolved.ira_other_clean_last_full_year, 2033 - 2)
        self.assertEqual(resolved.ira_other_clean_75pct_year, 2034 - 2)
        self.assertEqual(resolved.ira_other_clean_50pct_year, 2035 - 2)
        self.assertEqual(resolved.ira_other_clean_phaseout_end, 2036 - 2)
        self.assertEqual(ira_phaseout_fraction(2031, resolved), 1.0)
        self.assertAlmostEqual(ira_phaseout_fraction(2032, resolved), 0.75)
        self.assertAlmostEqual(ira_phaseout_fraction(2033, resolved), 0.50)
        self.assertEqual(ira_phaseout_fraction(2034, resolved), 0.0)


if __name__ == "__main__":
    unittest.main()
