"""Tests for ``market_sim.policy.ira`` -- §45U, §45Y/§48E, and the policy bundle."""

import unittest

from market_sim.config.scenarios import ScenarioConfig, resolve_policy_bundle
from market_sim.policy.ira import (
    SECTION_45U_BASE_CREDIT_CENTS_PER_KWH,
    SECTION_45U_PREVAILING_WAGE_MULTIPLIER,
    ira_phaseout_fraction,
    section_45u_applicable_amounts_cents_per_kwh,
    section_45u_credit_per_mwh,
)

# Sale year whose §45U(c)(1) applicable amounts are the NOMINAL statutory
# 0.3c/2.5c pair (the 2024 factor is 1.0000 by construction). The
# d28-45u-composition-memo-2026-08-08 §2.3 table is nominal-amount
# arithmetic, so its rows are pinned at this year; the inflation-adjusted
# years are pinned separately in TestSection45UInflationAdjustment.
_NOMINAL_AMOUNT_YEAR = 2024


class TestSection45UCredit(unittest.TestCase):
    """IRA §45U existing-nuclear PTC as a $/MWh retirement-screen revenue input."""

    def test_full_credit_below_gross_receipts_threshold(self):
        # Below the gross-receipts threshold no phase-down applies, so the
        # credit is the full wage-compliant 5 x 0.3 = 1.5 cents/kWh.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 20.0, config)
        self.assertAlmostEqual(
            credit,
            SECTION_45U_PREVAILING_WAGE_MULTIPLIER
            * SECTION_45U_BASE_CREDIT_CENTS_PER_KWH
            * 10.0,
        )  # $15/MWh

    def test_zero_credit_after_expiry_year(self):
        config = ScenarioConfig()  # ira_45u_last_year = 2032
        self.assertGreater(section_45u_credit_per_mwh(2032, 20.0, config), 0.0)
        self.assertEqual(section_45u_credit_per_mwh(2033, 20.0, config), 0.0)

    def test_phases_down_above_gross_receipts_threshold(self):
        # avg_price = 30 $/MWh = 3.0 cents/kWh. 2026 threshold is 2.6 cents
        # (Notice 2026-41), so excess = 0.4 cents; reduction = 0.16 x 0.4 =
        # 0.064 cents; subsection-(a) net = 0.3 - 0.064 = 0.236 cents;
        # §45U(d)(1) 5x => 1.18 cents/kWh = $11.80/MWh.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 30.0, config)
        self.assertAlmostEqual(credit, 11.80)

    def test_credit_floors_at_zero_at_high_gross_receipts(self):
        # An extremely high average price fully exhausts the credit rather
        # than going negative -- §45U(b)(2)(A)'s "lesser of" cap.
        config = ScenarioConfig()
        credit = section_45u_credit_per_mwh(2026, 10_000.0, config)
        self.assertEqual(credit, 0.0)


class TestSection45UStatutoryOrdering(unittest.TestCase):
    """§45U(d)(1)'s 5x multiplies the subsection-(a) NET, not the 0.3c rate.

    Finding F-1 of docs/handoffs/d28-45u-composition-memo-2026-08-08.md.
    §45U(a) is already `0.3c x kWh - reduction amount`, and §45U(d)(1)
    multiplies "the amount of the credit determined under subsection (a)"
    by 5. Folding the 5x into the rate and then subtracting an unmultiplied
    §45U(b)(2)(A) reduction leaves the phase-down slope 5x too shallow.
    """

    def test_credit_zeroes_out_at_43_75_not_118_75_usd_per_mwh(self):
        # Statutory curve: 5 x max(0, 0.3 - 0.16 x max(0, GR - 2.5)) cents.
        # The credit dies where 0.16 x (GR - 2.5c) = 0.3c, i.e. at
        # GR = 2.5 + 1.875 = 4.375 cents/kWh = $43.75/MWh.
        #
        # The pre-fix ordering (1.5c rate less an UNMULTIPLIED reduction)
        # died at 1.5 / 0.16 + 2.5 = 11.875 cents/kWh = $118.75/MWh, and was
        # still paying ~$0.02/MWh a cent below it. Both numbers are pinned:
        # $43.75 is now the boundary, and $118.75 is deep inside the dead
        # zone rather than on its edge.
        config = ScenarioConfig()
        year = _NOMINAL_AMOUNT_YEAR
        self.assertAlmostEqual(section_45u_credit_per_mwh(year, 43.75, config), 0.0)
        self.assertGreater(section_45u_credit_per_mwh(year, 43.74, config), 0.0)
        self.assertAlmostEqual(section_45u_credit_per_mwh(year, 118.75, config), 0.0)
        self.assertAlmostEqual(section_45u_credit_per_mwh(year, 118.74, config), 0.0)

    def test_phase_down_slope_is_80_cents_per_dollar_of_gross_receipts(self):
        # 5 x 0.16 = 0.80 $/$ above the threshold, not 0.16 $/$.
        config = ScenarioConfig()
        year = _NOMINAL_AMOUNT_YEAR
        above = section_45u_credit_per_mwh(year, 30.0, config)
        further = section_45u_credit_per_mwh(year, 31.0, config)
        self.assertAlmostEqual(above - further, 0.80)

    def test_memo_table_d0_rows_at_miso_committed_prices(self):
        # d28-45u-composition-memo-2026-08-08 §2.3, the D=0 (no clean dual)
        # rows of composition column (c), at MISO's committed RT ATC prices:
        #   P = $30.80 (2024): 5 x (0.3 - 0.16 x 0.58) = 1.036c = $10.36/MWh
        #   P = $42.85 (2025): 5 x (0.3 - 0.16 x 1.785) = 0.072c = $0.72/MWh
        # The pre-fix values were $14.07 and $12.14 -- the $11.42/MWh gap at
        # the 2025 price is the ~$90/kW-yr the memo scores against the
        # $130/kW-yr nuclear going-forward bar.
        config = ScenarioConfig()
        year = _NOMINAL_AMOUNT_YEAR
        self.assertAlmostEqual(section_45u_credit_per_mwh(year, 30.80, config), 10.36)
        self.assertAlmostEqual(section_45u_credit_per_mwh(year, 42.85, config), 0.72)


class TestSection45UInflationAdjustment(unittest.TestCase):
    """§45U(c)(1)-(2) applicable amounts, as printed in the IRS notices.

    Finding F-3 of the same memo. Base calendar year 2023; the (a)(1)(A)
    0.3c amount rounds to 0.05c and the (b)(2)(A)(ii)(II)(aa) 2.5c amount
    to 0.1c.
    """

    def test_published_applicable_amounts_match_the_notices(self):
        # 2024: no notice (factor 1.0000 by construction) -> nominal amounts.
        # 2025: Notice 2025-37 (IRB 2025-30), factor 1.0242 -> 0.3c / 2.6c.
        # 2026: Notice 2026-41 (IRB 2026-29) §3.01, factor 1.0539 -> 0.3c / 2.6c.
        self.assertEqual(section_45u_applicable_amounts_cents_per_kwh(2024), (0.3, 2.5))
        self.assertEqual(section_45u_applicable_amounts_cents_per_kwh(2025), (0.3, 2.6))
        self.assertEqual(section_45u_applicable_amounts_cents_per_kwh(2026), (0.3, 2.6))

    def test_years_outside_the_published_notices_hold_the_nearest_pair(self):
        # No factor is published for a forward year, so the last published
        # pair HOLDS -- deterministic, zero DOF, and one-sided conservative.
        for year in (2027, 2030, 2032, 2050):
            self.assertEqual(
                section_45u_applicable_amounts_cents_per_kwh(year), (0.3, 2.6)
            )
        # Pre-2024 years are outside §45U's own effective date; hold the
        # earliest published pair rather than extrapolating backwards.
        self.assertEqual(section_45u_applicable_amounts_cents_per_kwh(2023), (0.3, 2.5))

    def test_2026_threshold_lifts_the_credit_by_80_cents_per_mwh(self):
        # Memo §2.3's sensitivity note: the $25 -> $26/MWh threshold shifts
        # the credit by +0.16 x 1.0 x 5 = +$0.80/MWh wherever it is live and
        # unphased. At the 2025 MISO price, $0.72 -> $1.52/MWh.
        config = ScenarioConfig()
        nominal = section_45u_credit_per_mwh(_NOMINAL_AMOUNT_YEAR, 42.85, config)
        adjusted = section_45u_credit_per_mwh(2026, 42.85, config)
        self.assertAlmostEqual(nominal, 0.72)
        self.assertAlmostEqual(adjusted, 1.52)

    def test_full_credit_is_unchanged_by_the_threshold_adjustment(self):
        # The (a)(1)(A) rate rounds back to 0.3c under both published
        # factors, so the unphased credit stays $15/MWh in every year.
        config = ScenarioConfig()
        for year in (2024, 2025, 2026, 2030):
            self.assertAlmostEqual(section_45u_credit_per_mwh(year, 20.0, config), 15.0)

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
