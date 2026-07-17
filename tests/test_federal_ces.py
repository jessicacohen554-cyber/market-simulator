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
from types import SimpleNamespace

import numpy as np

from market_sim.config.constants import CO2_RATES
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_new_entry,
    apply_economic_retirements,
)
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy.eac import (
    apply_eac_to_mc,
    compute_eac_dispatch_credits,
    get_eac_price_for_new_entry,
)
from market_sim.policy.federal_ces import (
    effective_eac_price_for_tech,
    effective_eac_price_for_unit,
    effective_unit_eac_prices,
    federal_ces_suppresses_state_rps,
    premium_for_year,
    tech_credit_fraction,
    unit_credit_fraction,
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
        # Default 0.95 — the owner's target capture rate (Q4, plan §11;
        # flipped from the pre-Q4 0.90 in W2-A task 0).
        config = ScenarioConfig(federal_ces_enabled=True)
        fleet = _fleet(["gas_cc_ccs"], emission_rates=[0.036])
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [0.95]))
        # The 0.90 labeled sensitivity flows through the field.
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_ccs_capture_fraction=0.90
        )
        self.assertTrue(np.array_equal(unit_credit_fractions(config, fleet), [0.90]))

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
        # Default 0.95 (owner Q4 target rate); 0.90 the labeled sensitivity.
        config = ScenarioConfig(federal_ces_enabled=True)
        self.assertEqual(tech_credit_fraction(config, "gas_cc_ccs"), 0.95)
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_ccs_capture_fraction=0.90
        )
        self.assertEqual(tech_credit_fraction(config, "gas_cc_ccs"), 0.90)

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
        # Abated gas earns premium × capture fraction: 20 × 0.95 = 19.
        self.assertAlmostEqual(
            effective_eac_price_for_tech(config, "gas_cc_ccs", 2030), 19.0
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
        self.assertTrue(np.allclose(prices, [17.0, 9.5, 0.0, 10.0]))


# ---------------------------------------------------------------------------
# W2-A consumer wiring (plan §5.3): dispatch cost vector, retirement screen,
# new-entry screens, and the state-RPS suppression predicate. Trivial scale
# throughout (1-5 gens / ≤24 h — repo testing pattern; no full-year LP).
# ---------------------------------------------------------------------------


def _no_renewables(n_zones, hours):
    """Zero wind/solar inputs for a thermal-only ``solve_dispatch`` call."""
    return dict(
        wind_cf=np.zeros((n_zones, hours)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, hours)),
        solar_cap=np.zeros(n_zones),
    )


class TestUnitCreditFractionScalarParity(unittest.TestCase):
    """The scalar unit_credit_fraction mirrors the array resolver exactly."""

    def test_scalar_matches_array_across_fuels_and_modes(self):
        fuels = [
            "nuclear",
            "wind",
            "hydro",
            "gas_cc",
            "gas_cc",
            "gas_cc_ccs",
            "coal",
            "gas_ct",
            "biomass",
        ]
        rates = [0.0, 0.0, 0.0, 0.37, 0.50, 0.041, 0.95, 0.55, 0.10]
        fleet = _fleet(fuels, emission_rates=rates)
        for mode in ("clean_capture", "cesa_ci"):
            config = ScenarioConfig(
                federal_ces_enabled=True, federal_ces_crediting=mode
            )
            arr = unit_credit_fractions(config, fleet)
            for i, (fuel, rate) in enumerate(zip(fuels, rates)):
                self.assertAlmostEqual(
                    unit_credit_fraction(config, fuel, rate),
                    arr[i],
                    msg=f"{mode}:{fuel}@{rate}",
                )

    def test_scalar_zero_when_disabled(self):
        self.assertEqual(unit_credit_fraction(ScenarioConfig(), "nuclear", 0.0), 0.0)


class TestEffectiveUnitPrice(unittest.TestCase):
    """effective_eac_price_for_unit — the retirement-screen seam."""

    def test_cesa_ci_credits_unabated_cc_on_its_own_ci(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_crediting="cesa_ci",
            federal_ces_premium_usd_per_mwh=10.0,
        )
        self.assertAlmostEqual(
            effective_eac_price_for_unit(config, "gas_cc", 0.37, 2030),
            10.0 * (1.0 - 0.37 / 0.82),
        )
        # Above the 0.45 eligibility line: no credit, whatever the formula
        # would give.
        self.assertEqual(
            effective_eac_price_for_unit(config, "gas_cc", 0.50, 2030), 0.0
        )

    def test_legacy_pass_through_allows_no_year(self):
        # CES off: exactly the legacy per-fuel scalar, even for legacy
        # callers that never threaded a year.
        config = ScenarioConfig(eac_price_nuclear=17.0)
        self.assertEqual(
            effective_eac_price_for_unit(config, "nuclear", 0.0, None), 17.0
        )

    def test_max_of_legacy_and_premium(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=20.0,
            eac_price_nuclear=17.0,
        )
        self.assertEqual(
            effective_eac_price_for_unit(config, "nuclear", 0.0, 2030), 20.0
        )

    def test_enabled_without_year_raises(self):
        config = ScenarioConfig(federal_ces_enabled=True)
        with self.assertRaises(ValueError):
            effective_eac_price_for_unit(config, "nuclear", 0.0, None)


class TestDispatchWiringApplyEacToMc(unittest.TestCase):
    """apply_eac_to_mc consumes the year-aware effective unit prices."""

    def test_ces_off_matches_legacy_bytes(self):
        # Neutrality: with the CES disabled the year-aware call produces
        # byte-identical mc to the legacy (year-less) call.
        config = ScenarioConfig(eac_price_nuclear=17.0, eac_price_gas_cc_ccs=10.0)
        fleet = _fleet(["nuclear", "gas_cc_ccs", "gas_cc"])
        legacy = np.full((3, 24), 30.0)
        apply_eac_to_mc(legacy, fleet, config)
        wired = np.full((3, 24), 30.0)
        apply_eac_to_mc(wired, fleet, config, 2030)
        self.assertEqual(legacy.tobytes(), wired.tobytes())
        self.assertTrue(np.allclose(legacy[0], 13.0))  # nuclear -17
        self.assertTrue(np.allclose(legacy[1], 20.0))  # ccs -10
        self.assertTrue(np.allclose(legacy[2], 30.0))  # unabated untouched

    def test_premium_lowers_every_credited_fuel(self):
        # clean_capture $20: f=1.0 fuels bid $20 lower, abated gas ×0.95,
        # unabated gas untouched.
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=20.0
        )
        fleet = _fleet(["nuclear", "hydro", "hydrogen_ccgt", "gas_cc_ccs", "gas_cc"])
        mc = np.full((5, 24), 30.0)
        apply_eac_to_mc(mc, fleet, config, 2030)
        self.assertTrue(np.allclose(mc[0], 10.0))
        self.assertTrue(np.allclose(mc[1], 10.0))
        self.assertTrue(np.allclose(mc[2], 10.0))
        self.assertTrue(np.allclose(mc[3], 11.0))  # 30 − 20×0.95
        self.assertTrue(np.allclose(mc[4], 30.0))

    def test_max_of_legacy_and_premium_never_sum(self):
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=10.0,
            eac_price_nuclear=17.0,
        )
        fleet = _fleet(["nuclear"])
        mc = np.full((1, 24), 10.0)
        apply_eac_to_mc(mc, fleet, config, 2030)
        # 10 − max(17, 10) = −7, never 10 − (17+10) = −17.
        self.assertTrue(np.allclose(mc, -7.0))

    def test_cesa_ci_credits_efficient_ccgt_zeroes_above_line(self):
        # Acceptance case (plan §8 W2-A): an efficient CCGT at CI 0.37
        # bids premium × (1 − 0.37/0.82) lower; a unit above the 0.45
        # line is untouched.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_crediting="cesa_ci",
            federal_ces_premium_usd_per_mwh=10.0,
        )
        fleet = _fleet(["gas_cc", "gas_cc"], emission_rates=[0.37, 0.50])
        mc = np.full((2, 24), 30.0)
        apply_eac_to_mc(mc, fleet, config, 2030)
        self.assertTrue(np.allclose(mc[0], 30.0 - 10.0 * (1.0 - 0.37 / 0.82)))
        self.assertTrue(np.allclose(mc[1], 30.0))

    def test_enabled_without_year_raises(self):
        # An enabled CES with no year is a wiring bug, not a silent no-op
        # (the ERCOT-65 silently-dead-channel lesson).
        config = ScenarioConfig(
            federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=10.0
        )
        fleet = _fleet(["nuclear"])
        with self.assertRaises(ValueError):
            apply_eac_to_mc(np.zeros((1, 24)), fleet, config)
        with self.assertRaises(ValueError):
            compute_eac_dispatch_credits(config)


class TestDispatchWiringCredits(unittest.TestCase):
    """compute_eac_dispatch_credits: wind/solar/storage effective prices."""

    def test_ces_off_legacy_tuple(self):
        config = ScenarioConfig(eac_price_wind=8.0, eac_price_solar=6.0)
        self.assertEqual(compute_eac_dispatch_credits(config), (8.0, 6.0, 0.0))
        self.assertEqual(compute_eac_dispatch_credits(config, 2030), (8.0, 6.0, 0.0))

    def test_premium_max_and_storage_gate(self):
        # wind: legacy 15 beats premium 12; solar: premium 12; storage:
        # owner D5 default — no certificate for discharge.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=12.0,
            eac_price_wind=15.0,
        )
        self.assertEqual(compute_eac_dispatch_credits(config, 2030), (15.0, 12.0, 0.0))
        # federal_ces_storage_eligible opts discharge in.
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=12.0,
            federal_ces_storage_eligible=True,
        )
        self.assertEqual(compute_eac_dispatch_credits(config, 2030), (12.0, 12.0, 12.0))


class TestTwoSolvedYearsEscalation(unittest.TestCase):
    """Year escalation visible across two solved dispatch years (1 zone/4 h)."""

    def test_premium_path_moves_clearing_price_between_years(self):
        # A marginal credited unit sets the zonal dual at its
        # premium-lowered bid, so the knot path {2030: 2, 2040: 8} must
        # move the clearing price by exactly the premium delta between
        # two solved years. (The bids stay positive so the marginal MWh
        # is real demand, not the ε-priced dump sink.)
        T = 4
        config = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_by_year={2030: 2.0, 2040: 8.0},
        )
        prices_by_year = {}
        for year in (2030, 2040):
            fleet = _fleet(["nuclear", "gas_cc"], hours=T, pmax=200.0)
            mc = np.vstack([np.full(T, 10.0), np.full(T, 30.0)])
            apply_eac_to_mc(mc, fleet, config, year)
            demand = np.full((1, T), 80.0)
            result = solve_dispatch(
                fleet, demand, mc=mc, T=T, voll=5000.0, **_no_renewables(1, T)
            )
            self.assertEqual(result.status, "Optimal")
            # Nuclear is marginal (80 < 200 MW), so the dual is its bid.
            prices_by_year[year] = float(result.prices[0, 0])
        self.assertAlmostEqual(prices_by_year[2030], 8.0, places=4)
        self.assertAlmostEqual(prices_by_year[2040], 2.0, places=4)


class TestRetirementWiring(unittest.TestCase):
    """The premium moves a retention decision in apply_economic_retirements."""

    T = 10

    def _survivors(self, config, fuel, emission_rate):
        gens = [
            Generator(
                unit_id="U0",
                name="U0",
                zone="Z0",
                fuel_type=fuel,
                pmax_mw=100.0,
                pmin_mw=0.0,
                emission_rate_co2=emission_rate,
                eford=0.0,
            )
        ]
        arrays = generators_to_fleet_arrays(gens, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), 10.0))
        # Year 2040: past ira_45u_last_year (2032), so the §45U nuclear
        # credit is expired and cannot rescue the no-CES control case —
        # the retention below is attributable to the premium alone.
        survivors, _, _ = apply_economic_retirements(
            gens, arrays, dispatch, prices, config, {}, peak_demand=0.0, year=2040
        )
        return survivors

    def test_premium_retains_nuclear_clean_capture(self):
        # Gross energy revenue 10 $/MWh × 10 MW × 10 h = $1,000 against a
        # $2,000 going-forward cost (0.02 $/kW-yr × 100 MW × 1000): the
        # unit retires without the CES and is retained with a $15 premium
        # ($15 × 100 MWh = $1,500 attribute revenue → $2,500 > $2,000).
        base = dict(retirement_years_nuclear=1, fixed_om_nuclear=0.02)
        without = ScenarioConfig(**base)
        self.assertEqual(self._survivors(without, "nuclear", 0.0), [])
        with_ces = ScenarioConfig(
            federal_ces_enabled=True,
            federal_ces_premium_usd_per_mwh=15.0,
            **base,
        )
        kept = self._survivors(with_ces, "nuclear", 0.0)
        self.assertEqual([g.unit_id for g in kept], ["U0"])

    def test_cesa_ci_retains_credited_cc_but_not_above_line(self):
        # Same construction for unabated gas CC under cesa_ci: an
        # efficient unit (CI 0.37, f ≈ 0.549) earns 40 × 0.549 × 100 MWh
        # ≈ $2,195 and is retained; a unit above the 0.45 line earns 0
        # and still retires — the premium credits the unit's own CI.
        base = dict(retirement_years_gas_cc=1, fixed_om_gas_cc=0.02)
        without = ScenarioConfig(**base)
        self.assertEqual(self._survivors(without, "gas_cc", 0.37), [])
        with_ces_cfg = dict(
            federal_ces_enabled=True,
            federal_ces_crediting="cesa_ci",
            federal_ces_premium_usd_per_mwh=40.0,
            **base,
        )
        kept = self._survivors(ScenarioConfig(**with_ces_cfg), "gas_cc", 0.37)
        self.assertEqual([g.unit_id for g in kept], ["U0"])
        gone = self._survivors(ScenarioConfig(**with_ces_cfg), "gas_cc", 0.50)
        self.assertEqual(gone, [])


class TestNewEntryWiring(unittest.TestCase):
    """nuclear_smr and hydrogen earn the premium in the entry screens."""

    T = 10

    def _rows(self, config, year):
        prices = np.full((1, self.T), 60.0)
        ledger: list[dict] = []
        apply_economic_new_entry(
            [],
            prices,
            year,
            config,
            "ERCOT",
            gas_price_per_mmbtu=3.5,
            screen_ledger=ledger,
        )
        return {row["tech"]: row for row in ledger}

    def test_premium_reaches_smr_and_hydrogen_candidates(self):
        # 2036 ≥ h2_available_year (2035) so both hydrogen turbines are
        # screened alongside the classic candidates.
        off = self._rows(ScenarioConfig(), 2036)
        on = self._rows(
            ScenarioConfig(
                federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=30.0
            ),
            2036,
        )
        # Previously-zero attribute techs now see the full premium…
        for tech in ("nuclear_smr", "hydrogen_ct", "hydrogen_ccgt"):
            self.assertEqual(off[tech]["attribute_price"], 0.0, tech)
            self.assertEqual(on[tech]["attribute_price"], 30.0, tech)
            self.assertGreater(on[tech]["attribute_revenue_per_mw_yr"], 0.0, tech)
        # …abated gas at the capture fraction (30 × 0.95)…
        self.assertAlmostEqual(on["gas_cc_ccs"]["attribute_price"], 28.5)
        # …and unabated thermal candidates earn nothing (clean_capture).
        self.assertEqual(on["gas_cc"]["attribute_revenue_per_mw_yr"], 0.0)

    def test_premium_moves_the_entry_margin_exactly(self):
        # Same candidate, same prices: the margin delta is exactly the
        # attribute revenue the premium added (energy and cost unchanged).
        off = self._rows(ScenarioConfig(), 2036)
        on = self._rows(
            ScenarioConfig(
                federal_ces_enabled=True, federal_ces_premium_usd_per_mwh=30.0
            ),
            2036,
        )
        for tech in ("nuclear_smr", "hydrogen_ccgt"):
            self.assertAlmostEqual(
                on[tech]["margin_per_mw_yr"] - off[tech]["margin_per_mw_yr"],
                on[tech]["attribute_revenue_per_mw_yr"],
                places=4,
                msg=tech,
            )


class TestStateRpsSuppression(unittest.TestCase):
    """federal_ces_replaces_state_rps predicate (runner RPS-row seam)."""

    def test_predicate_requires_both_gates(self):
        self.assertFalse(federal_ces_suppresses_state_rps(ScenarioConfig()))
        # The replaces flag without the master gate is inert…
        self.assertFalse(
            federal_ces_suppresses_state_rps(
                ScenarioConfig(federal_ces_replaces_state_rps=True)
            )
        )
        # …and the master gate alone leaves state RPS rows in place.
        self.assertFalse(
            federal_ces_suppresses_state_rps(ScenarioConfig(federal_ces_enabled=True))
        )
        self.assertTrue(
            federal_ces_suppresses_state_rps(
                ScenarioConfig(
                    federal_ces_enabled=True, federal_ces_replaces_state_rps=True
                )
            )
        )


if __name__ == "__main__":
    unittest.main()
