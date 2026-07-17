"""Tests for the national CES federal EAC-premium resolver (Wave 1-A).

``policy/federal_ces.py`` resolves the federal clean-energy-standard
premium path and per-unit / per-tech credit fractions, joining the legacy
``eac_price_*`` scalars via ``max()`` (one certificate per MWh, sold
once). As of Wave 1-A the module has no consumers, so these tests pin the
solver-inert contract: disabled ⇒ all-zero fractions and exact legacy
pass-through, and the new ScenarioConfig fields leave the default
``cache_key`` byte-identical. Trivial scale first (1 gen / 24 h — repo
testing pattern), then small multi-fuel fleets.
"""

import unittest
from dataclasses import asdict

import numpy as np

from market_sim.config.constants import CO2_RATES
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.policy.eac import get_eac_price_for_new_entry
from market_sim.policy.federal_ces import (
    effective_eac_price_for_tech,
    effective_unit_eac_prices,
    premium_for_year,
    tech_credit_fraction,
    unit_credit_fractions,
)

# Every ScenarioConfig field Wave 1-A introduced (plan §5.1).
_NEW_FIELDS = (
    "federal_ces_enabled",
    "federal_ces_premium_usd_per_mwh",
    "federal_ces_premium_escalation_real",
    "federal_ces_premium_by_year",
    "federal_ces_crediting",
    "federal_ces_ccs_capture_fraction",
    "federal_ces_ci_benchmark_t_per_mwh",
    "federal_ces_unabated_ci_threshold_t_per_mwh",
    "federal_ces_eligible_fuels",
    "federal_ces_storage_eligible",
    "federal_ces_replaces_state_rps",
)


def _fleet(fuel_types, emission_rates=None, hours=24, pmax=100.0):
    """Build ``FleetArrays`` with one generator per entry of ``fuel_types``.

    ``emission_rates`` optionally sets each unit's CO2 rate in tCO2/MWh
    (the cesa_ci crediting input); default 0.0.
    """
    if emission_rates is None:
        emission_rates = [0.0] * len(fuel_types)
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone="Z0",
            fuel_type=ft,
            pmax_mw=pmax,
            pmin_mw=0.0,
            emission_rate_co2=er,
            eford=0.0,
        )
        for i, (ft, er) in enumerate(zip(fuel_types, emission_rates))
    ]
    return generators_to_fleet_arrays(gens, ["Z0"], hours=hours)


class TestDisabledNeutrality(unittest.TestCase):
    """federal_ces_enabled=False ⇒ zeros / exact legacy pass-through."""

    def test_premium_zero_when_disabled(self):
        # Even with a premium level, escalation AND knots configured, the
        # master gate zeroes the premium path.
        config = ScenarioConfig(
            federal_ces_premium_usd_per_mwh=25.0,
            federal_ces_premium_escalation_real=0.05,
            federal_ces_premium_by_year={2030: 40.0},
        )
        for year in (2026, 2030, 2050):
            self.assertEqual(premium_for_year(config, year), 0.0)

    def test_unit_fractions_all_zero_when_disabled(self):
        # 1 gen / 24 h trivial case first.
        fleet = _fleet(["nuclear"])
        config = ScenarioConfig()
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [0.0]))
        # Then a multi-fuel fleet, both crediting modes.
        fleet = _fleet(["nuclear", "wind", "gas_cc_ccs", "gas_cc", "coal"])
        for mode in ("clean_capture", "cesa_ci"):
            config = ScenarioConfig(federal_ces_crediting=mode)
            self.assertTrue(
                np.array_equal(unit_credit_fractions(config, fleet), np.zeros(5))
            )

    def test_tech_fraction_zero_when_disabled(self):
        config = ScenarioConfig()
        for tech in ("nuclear_smr", "wind", "gas_cc_ccs", "hydrogen_ct"):
            self.assertEqual(tech_credit_fraction(config, tech), 0.0)

    def test_effective_tech_price_is_legacy_pass_through(self):
        config = ScenarioConfig(eac_price_nuclear=17.0, eac_price_wind=8.0)
        for tech in ("nuclear", "wind", "solar", "gas_cc_ccs", "storage"):
            self.assertEqual(
                effective_eac_price_for_tech(config, tech, 2030),
                get_eac_price_for_new_entry(tech, config),
            )

    def test_effective_unit_prices_are_legacy_broadcast(self):
        # Legacy per-fuel scalars land on their units; everything else 0.
        config = ScenarioConfig(eac_price_nuclear=17.0, eac_price_gas_cc_ccs=10.0)
        fleet = _fleet(["nuclear", "gas_cc_ccs", "gas_cc", "coal"])
        prices = effective_unit_eac_prices(config, fleet, 2030)
        self.assertTrue(np.array_equal(prices, [17.0, 10.0, 0.0, 0.0]))


class TestCacheKeyNeutrality(unittest.TestCase):
    """The W1-A fields never perturb existing cache keys at defaults."""

    def test_all_new_fields_are_cache_key_optional(self):
        for name in _NEW_FIELDS:
            self.assertIn(name, _CACHE_KEY_OPTIONAL_FIELDS)

    def test_new_fields_drop_out_of_default_cache_payload(self):
        # Reproduce cache_key()'s payload construction: at defaults every
        # federal_ces_* key must drop out of the hashed dict, so the
        # default key is byte-identical to the pre-W1-A key.
        defaults = ScenarioConfig()
        payload = asdict(defaults)
        for name in _CACHE_KEY_OPTIONAL_FIELDS:
            if payload.get(name) == getattr(defaults, name):
                payload.pop(name, None)
        leaked = [k for k in payload if k.startswith("federal_ces_")]
        self.assertEqual(leaked, [])

    def test_non_default_value_enters_the_key(self):
        base = ScenarioConfig().cache_key()
        self.assertNotEqual(ScenarioConfig(federal_ces_enabled=True).cache_key(), base)
        self.assertNotEqual(
            ScenarioConfig(federal_ces_premium_usd_per_mwh=10.0).cache_key(), base
        )


class TestConfigGuards(unittest.TestCase):
    """__post_init__ registration guards (plan G8 / rule 13)."""

    def test_backcast_mode_with_ces_enabled_raises(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(mode="backcast", federal_ces_enabled=True)

    def test_backcast_mode_with_ces_disabled_is_fine(self):
        ScenarioConfig(mode="backcast")

    def test_invalid_crediting_mode_raises(self):
        # The v1 "binary" mode was dropped by owner decision D1.
        for bad in ("binary", "CLEAN_CAPTURE", ""):
            with self.assertRaises(ValueError):
                ScenarioConfig(federal_ces_crediting=bad)

    def test_both_crediting_modes_accepted(self):
        ScenarioConfig(federal_ces_crediting="clean_capture")
        ScenarioConfig(federal_ces_crediting="cesa_ci")


class TestPremiumForYear(unittest.TestCase):
    """Premium path: flat, escalated, and knot-overridden."""

    def test_flat_real_premium(self):
        # Owner default D3: 0%/yr real escalation — flat in every year.
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=10.0
        )
        for year in (2026, 2035, 2050):
            self.assertEqual(premium_for_year(config, year), 10.0)

    def test_real_escalation_compounds_from_2026(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            federal_ces_premium_escalation_real=0.02,
        )
        self.assertAlmostEqual(premium_for_year(config, 2026), 10.0)
        self.assertAlmostEqual(premium_for_year(config, 2030), 10.0 * 1.02**4)

    def test_knots_override_base_and_escalation(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=99.0,
            federal_ces_premium_escalation_real=0.10,
            federal_ces_premium_by_year={2026: 5.0, 2030: 15.0},
        )
        # Exact knot years return the knot values (not base×escalation).
        self.assertEqual(premium_for_year(config, 2026), 5.0)
        self.assertEqual(premium_for_year(config, 2030), 15.0)
        # Linear interpolation between knots.
        self.assertAlmostEqual(premium_for_year(config, 2028), 10.0)
        # Edge-held outside the knot span.
        self.assertEqual(premium_for_year(config, 2024), 5.0)
        self.assertEqual(premium_for_year(config, 2045), 15.0)

    def test_string_knot_keys_coerced(self):
        # YAML round-trips stringify mapping keys; resolution must be
        # identical to the int-keyed config.
        int_keyed = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_by_year={2026: 5.0, 2030: 15.0},
        )
        str_keyed = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_by_year={"2026": 5.0, "2030": 15.0},
        )
        for year in (2024, 2026, 2028, 2030, 2045):
            self.assertEqual(
                premium_for_year(str_keyed, year), premium_for_year(int_keyed, year)
            )

    def test_empty_knots_fall_back_to_base(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            federal_ces_premium_by_year={},
        )
        self.assertEqual(premium_for_year(config, 2030), 10.0)


class TestUnitCreditFractionsCleanCapture(unittest.TestCase):
    """clean_capture: eligible clean 1.0, abated gas = capture fraction."""

    def test_single_nuclear_unit(self):
        # 1 gen / 24 h trivial case.
        config = ScenarioConfig(federal_ces_enabled=True)
        fleet = _fleet(["nuclear"])
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [1.0]))

    def test_eligible_clean_fuels_credit_one(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        fuels = [
            "wind",
            "solar",
            "hydro",
            "geothermal",
            "offshore_wind",
            "hydrogen_ct",
            "hydrogen_ccgt",
        ]
        fleet = _fleet(fuels)
        self.assertTrue(
            np.array_equal(unit_credit_fractions(config, fleet), np.ones(len(fuels)))
        )

    def test_abated_gas_credits_capture_fraction(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        fleet = _fleet(["gas_cc_ccs"], emission_rates=[0.036])
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [0.90]))
        # The 0.95 owner sensitivity flows through the field.
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_ccs_capture_fraction=0.95
        )
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [0.95]))

    def test_unabated_fossil_credits_zero(self):
        # Unabated fossil earns 0 in clean_capture mode — even an
        # efficient CCGT under the cesa_ci threshold (mode subsumes the
        # dropped v1 unabated_fossil_eligible boolean).
        config = ScenarioConfig(federal_ces_enabled=True)
        fleet = _fleet(
            ["gas_cc", "gas_ct", "coal", "oil", "gas_st", "biomass"],
            emission_rates=[0.37, 0.55, 0.95, 0.80, 0.55, 0.10],
        )
        self.assertTrue(
            np.array_equal(unit_credit_fractions(config, fleet), np.zeros(6))
        )

    def test_unknown_eligible_fuel_raises(self):
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_eligible_fuels=["nuclearr"]
        )
        with self.assertRaises(ValueError):
            unit_credit_fractions(config, _fleet(["nuclear"]))


class TestUnitCreditFractionsCesaCi(unittest.TestCase):
    """cesa_ci: clip(1 − CI/0.82, 0, 1), unabated CC gated at 0.45."""

    def _config(self, **overrides):
        return ScenarioConfig(
            federal_ces_enabled=True, federal_ces_crediting="cesa_ci", **overrides
        )

    def test_single_zero_carbon_unit_credits_one(self):
        # 1 gen / 24 h trivial case: CI = 0 ⇒ fraction 1.0.
        fleet = _fleet(["nuclear"])
        self.assertTrue(
            np.array_equal(unit_credit_fractions(self._config(), fleet), [1.0])
        )

    def test_efficient_unabated_ccgt_earns_cesa_fraction(self):
        # Plan §1: an efficient CCGT at ~0.37 t/MWh earns ~0.55 — the
        # benchmark formula, NOT computed against the 0.45 threshold.
        fleet = _fleet(["gas_cc"], emission_rates=[0.37])
        fractions = unit_credit_fractions(self._config(), fleet)
        self.assertAlmostEqual(fractions[0], 1.0 - 0.37 / 0.82)

    def test_ccgt_just_below_and_above_the_line(self):
        fleet = _fleet(
            ["gas_cc", "gas_cc", "gas_cc"], emission_rates=[0.44, 0.45, 0.46]
        )
        fractions = unit_credit_fractions(self._config(), fleet)
        self.assertAlmostEqual(fractions[0], 1.0 - 0.44 / 0.82)
        # The line is inclusive (CI ≤ threshold credits)...
        self.assertAlmostEqual(fractions[1], 1.0 - 0.45 / 0.82)
        # ...and just above it the unit earns 0 regardless of the
        # benchmark formula (which would give a positive fraction).
        self.assertEqual(fractions[2], 0.0)

    def test_abated_gas_earns_formula_on_residual_ci(self):
        # ≈0.955 at a 90%-capture residual of h-class gas CC (plan §1).
        residual = min(CO2_RATES["gas_cc"].values()) * 0.10
        fleet = _fleet(["gas_cc_ccs"], emission_rates=[residual])
        fractions = unit_credit_fractions(self._config(), fleet)
        self.assertAlmostEqual(fractions[0], 1.0 - residual / 0.82)

    def test_eligible_fuel_above_benchmark_clips_to_zero(self):
        # clip() floor: an eligible fuel whose CI exceeds the benchmark
        # earns 0, never a negative fraction.
        fleet = _fleet(["gas_cc_ccs"], emission_rates=[0.90])
        self.assertTrue(
            np.array_equal(unit_credit_fractions(self._config(), fleet), [0.0])
        )

    def test_other_unabated_fossil_stays_zero(self):
        # The threshold pathway is unabated gas CC ONLY — a coal or gas_ct
        # unit under 0.45 t/MWh still earns 0.
        fleet = _fleet(["coal", "gas_ct", "gas_st"], emission_rates=[0.40, 0.44, 0.30])
        self.assertTrue(
            np.array_equal(unit_credit_fractions(self._config(), fleet), np.zeros(3))
        )

    def test_threshold_field_moves_the_line(self):
        fleet = _fleet(["gas_cc"], emission_rates=[0.46])
        tight = self._config()
        loose = self._config(federal_ces_unabated_ci_threshold_t_per_mwh=0.50)
        self.assertEqual(unit_credit_fractions(tight, fleet)[0], 0.0)
        self.assertAlmostEqual(
            unit_credit_fractions(loose, fleet)[0], 1.0 - 0.46 / 0.82
        )


class TestTechCreditFraction(unittest.TestCase):
    """Candidate-tech table (plan §5.1)."""

    def test_full_credit_candidate_techs(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        for tech in (
            "nuclear_smr",
            "hydrogen_ct",
            "hydrogen_ccgt",
            "wind",
            "solar",
            "geothermal",
            "offshore_wind",
            "nuclear",
            "hydro",
        ):
            self.assertEqual(tech_credit_fraction(config, tech), 1.0, tech)

    def test_gas_cc_ccs_clean_capture_uses_policy_fraction(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        self.assertEqual(tech_credit_fraction(config, "gas_cc_ccs"), 0.90)
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_ccs_capture_fraction=0.95
        )
        self.assertEqual(tech_credit_fraction(config, "gas_cc_ccs"), 0.95)

    def test_gas_cc_ccs_cesa_ci_uses_residual_class_ci(self):
        # Mirrors the capacity.py new-entrant construction: best-bin
        # unabated gas-CC CO2 × (1 − engineering ccs_capture_rate).
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_crediting="cesa_ci"
        )
        residual = min(CO2_RATES["gas_cc"].values()) * (1.0 - config.ccs_capture_rate)
        self.assertAlmostEqual(
            tech_credit_fraction(config, "gas_cc_ccs"), 1.0 - residual / 0.82
        )

    def test_non_eligible_techs_zero(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        for tech in ("gas_cc", "gas_ct", "coal", "oil", "biomass", "import"):
            self.assertEqual(tech_credit_fraction(config, tech), 0.0, tech)

    def test_storage_gated_by_its_own_toggle(self):
        # Owner D5 default: storage discharge earns no certificate.
        config = ScenarioConfig(federal_ces_enabled=True)
        self.assertEqual(tech_credit_fraction(config, "storage"), 0.0)
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_storage_eligible=True
        )
        self.assertEqual(tech_credit_fraction(config, "storage"), 1.0)

    def test_eligibility_list_drives_the_table(self):
        # Removing a fuel from the eligibility list zeroes its tech credit.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_eligible_fuels=["nuclear"],
        )
        self.assertEqual(tech_credit_fraction(config, "wind"), 0.0)
        self.assertEqual(tech_credit_fraction(config, "nuclear"), 1.0)


class TestEffectivePrices(unittest.TestCase):
    """max() against the legacy eac_price_* values — never a sum."""

    def test_tech_price_max_of_legacy_and_premium(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=20.0,
            eac_price_nuclear=17.0,
        )
        # Premium clears higher: max(17, 20×1.0) = 20 — not 37.
        self.assertEqual(effective_eac_price_for_tech(config, "nuclear", 2030), 20.0)
        # Legacy clears higher.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=20.0,
            eac_price_nuclear=25.0,
        )
        self.assertEqual(effective_eac_price_for_tech(config, "nuclear", 2030), 25.0)

    def test_tech_price_applies_credit_fraction(self):
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=20.0
        )
        # Abated gas earns premium × capture fraction: 20 × 0.90 = 18.
        self.assertAlmostEqual(
            effective_eac_price_for_tech(config, "gas_cc_ccs", 2030), 18.0
        )
        # Non-credited tech stays at its (zero) legacy price.
        self.assertEqual(effective_eac_price_for_tech(config, "gas_cc", 2030), 0.0)

    def test_tech_price_follows_premium_path(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_by_year={2026: 10.0, 2030: 20.0},
        )
        self.assertAlmostEqual(effective_eac_price_for_tech(config, "wind", 2028), 15.0)

    def test_unit_prices_elementwise_max(self):
        # 1 gen / 24 h trivial case: premium wins over a lower legacy ZEC.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=20.0,
            eac_price_nuclear=17.0,
        )
        fleet = _fleet(["nuclear"])
        self.assertTrue(
            np.array_equal(effective_unit_eac_prices(config, fleet, 2030), [20.0])
        )
        # Multi-fuel: legacy wins where higher, premium × fraction where
        # higher, zero where neither credits.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            eac_price_nuclear=17.0,
        )
        fleet = _fleet(["nuclear", "gas_cc_ccs", "gas_cc", "wind"])
        prices = effective_unit_eac_prices(config, fleet, 2030)
        self.assertTrue(np.allclose(prices, [17.0, 9.0, 0.0, 10.0]))


if __name__ == "__main__":
    unittest.main()
