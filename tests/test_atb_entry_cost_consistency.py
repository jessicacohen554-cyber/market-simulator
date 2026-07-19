"""FF-1E source-consistency: NEW_ENTRY_COSTS / TECH_COST_MULTIPLIERS vs ATB.

Asserts the ATB-derived entries of ``constants.NEW_ENTRY_COSTS`` and
``constants.TECH_COST_MULTIPLIERS`` equal what
``scripts/data/derive_entry_costs_from_atb.py`` computes from the committed
NREL ATB 2024 extract (CLAUDE.md rule 23 — the constants are a deterministic,
tested function of a real data source, not hand-set numbers that can silently
drift). Reads only the committed raw extract, so it runs in CI with no
clean-build step.

Scope: capex_per_kw + fom_per_kw_yr for the seven ATB-mapped entry techs, and
the low/high capex_per_kw multipliers. base_cf / learning_rate / lifetime_yr and
the learning_rate multipliers are intentionally excluded (not ATB CAPEX/FOM
quantities — see the derive module docstring). gas_cc_ccs uses ATB's 95 % CCS
class as its cost proxy (the model's 90 % capture has no ATB variant); its
dispatch physics stay 90 % via CCUS_PARAMS.
"""

import unittest

from market_sim.config.constants import NEW_ENTRY_COSTS, TECH_COST_MULTIPLIERS
from scripts.data import derive_entry_costs_from_atb as derive


class TestAtbEntryCostConsistency(unittest.TestCase):
    def test_new_entry_costs_match_atb_derivation(self) -> None:
        derived = derive.derive_new_entry_costs()
        # Every ATB-mapped tech is present in the constants and matches exactly.
        self.assertEqual(set(derived), set(derive.ENTRY_TECH_MAP))
        for tech, vals in derived.items():
            self.assertIn(tech, NEW_ENTRY_COSTS, tech)
            for param, value in vals.items():
                self.assertEqual(
                    NEW_ENTRY_COSTS[tech][param],
                    value,
                    f"NEW_ENTRY_COSTS[{tech!r}][{param!r}] drifted from the ATB "
                    f"derivation ({NEW_ENTRY_COSTS[tech][param]} != {value}) — "
                    f"re-run scripts/data/derive_entry_costs_from_atb.py",
                )

    def test_tech_cost_multiplier_capex_bracket_atb_ratios(self) -> None:
        # Since the capacity-cost-grounding session (2026-07-19) the committed
        # low/high capex multipliers are the cross-source literature envelope
        # (min/max over ATB's cases + the verified benchmark rows — exact
        # equality asserted in tests/test_cost_benchmark_envelope.py). The
        # ATB-internal ratios derived here remain envelope MEMBERS, so the
        # committed bounds must bracket them: this guards the FF-1E invariant
        # that the lever can never be narrower than ATB's own case spread.
        derived = derive.derive_tech_cost_multipliers()
        for tech, cases in derived.items():
            self.assertIn(tech, TECH_COST_MULTIPLIERS, tech)
            self.assertLessEqual(
                TECH_COST_MULTIPLIERS[tech]["low"]["capex_per_kw"],
                cases["low"]["capex_per_kw"],
                f"{tech}: committed low above the ATB Advanced ratio",
            )
            self.assertGreaterEqual(
                TECH_COST_MULTIPLIERS[tech]["high"]["capex_per_kw"],
                cases["high"]["capex_per_kw"],
                f"{tech}: committed high below the ATB Conservative ratio",
            )
            self.assertEqual(
                TECH_COST_MULTIPLIERS[tech]["mid"]["capex_per_kw"],
                cases["mid"]["capex_per_kw"],
                f"{tech}: mid must stay the exact ATB Moderate no-op (1.0)",
            )

    def test_gas_cc_ccs_uses_atb_95pct_ccs_class(self) -> None:
        # gas_cc_ccs is mapped to ATB's 95 % CCS class (nearest to the model's
        # 90 % capture) so its cost basis matches the ATB-derived host gas_cc;
        # the 90 % capture physics live in CCUS_PARAMS, not here.
        self.assertIn("gas_cc_ccs", derive.ENTRY_TECH_MAP)
        _, techdetail, _ = derive.ENTRY_TECH_MAP["gas_cc_ccs"]
        self.assertIn("95% CCS", techdetail)
        # A CCS plant must cost more per kW than its unabated host.
        self.assertGreater(
            NEW_ENTRY_COSTS["gas_cc_ccs"]["capex_per_kw"],
            NEW_ENTRY_COSTS["gas_cc"]["capex_per_kw"],
        )

    def test_ccus_params_operative_cost_matches_new_entry_costs(self) -> None:
        # CCUS_PARAMS is what capacity._emerging_lcoe actually screens new CCS on
        # (NEW_ENTRY_COSTS["gas_cc_ccs"] feeds only compute_lcoe). Both must carry
        # the same ATB 95%-CCS cost so the forecast CCS-vs-gas_cc competition is
        # on one basis (rule 1 — not the pre-FF-1E $2,500/$22 that made the
        # capture island look nearly free).
        from market_sim.config.constants import CCUS_PARAMS

        self.assertEqual(
            CCUS_PARAMS["gas_cc_ccs_90"]["capex_kw"],
            NEW_ENTRY_COSTS["gas_cc_ccs"]["capex_per_kw"],
        )
        self.assertEqual(
            CCUS_PARAMS["gas_cc_ccs_90"]["fom_kw_yr"],
            NEW_ENTRY_COSTS["gas_cc_ccs"]["fom_per_kw_yr"],
        )

    def test_per_tech_wacc_default_off_is_byte_identical(self) -> None:
        # The per-tech-WACC option (FF-1E §3.6) defaults off: every tech's
        # discount rate is the single real_discount_rate, so LCOE and the cache
        # key are unchanged from a bare config.
        from market_sim.config.scenarios import (
            ScenarioConfig,
            resolve_real_discount_rate,
        )
        from market_sim.model.capacity import compute_lcoe

        base = ScenarioConfig()
        self.assertFalse(base.per_tech_wacc_enabled)
        for tech in ("wind", "solar", "gas_cc", "nuclear_large"):
            self.assertEqual(
                resolve_real_discount_rate(base, tech), base.real_discount_rate
            )
            self.assertEqual(
                compute_lcoe(tech, 2030, base),
                compute_lcoe(tech, 2030, ScenarioConfig()),
            )
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(per_tech_wacc_enabled=False).cache_key(),
        )

    def test_per_tech_wacc_on_uses_atb_values(self) -> None:
        from market_sim.config.constants import ATB_TECH_WACC_REAL
        from market_sim.config.scenarios import (
            ScenarioConfig,
            resolve_real_discount_rate,
        )

        wacc = ScenarioConfig(per_tech_wacc_enabled=True)
        for tech, rate in ATB_TECH_WACC_REAL.items():
            self.assertEqual(resolve_real_discount_rate(wacc, tech), rate)
        # A tech ATB does not finance-differentiate falls back to the single rate.
        self.assertEqual(
            resolve_real_discount_rate(wacc, "hydrogen_ct"), wacc.real_discount_rate
        )
        # Enabling it is a distinct scenario (enters the cache key).
        self.assertNotEqual(ScenarioConfig().cache_key(), wacc.cache_key())

    def test_inflation_factor_uses_model_convention(self) -> None:
        # The 2022$->2026$ deflator is the model's own INFLATION_RATE over the
        # ATB-edition-to-model dollar-year gap (no external CPI series).
        from market_sim.config.constants import (
            INFLATION_RATE,
            REAL_DOLLAR_BASE_YEAR,
        )

        expected = (1.0 + INFLATION_RATE) ** (
            REAL_DOLLAR_BASE_YEAR - derive.ATB_DOLLAR_YEAR
        )
        self.assertAlmostEqual(derive.inflation_factor(), expected, places=12)


if __name__ == "__main__":
    unittest.main()
