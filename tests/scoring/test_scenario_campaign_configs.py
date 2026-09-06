"""The scenario campaign's config surface (SCN-WS0 deliverable 4).

Covers the three things that can silently break a campaign before a single
LP runs: a base YAML that is not actually the reference posture, a case set
that does not load or does not separate cases by cache key, and a ``--set``
override that accepts something it should have refused.
"""

from __future__ import annotations

import unittest

from market_sim.config.iso_configs import SUPPORTED_ISOS
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from scripts.run_full_horizon import (
    apply_set_overrides,
    parse_set_overrides,
)
from tests.helpers import REPO_ROOT

CONFIGS = REPO_ROOT / "configs"
MATRIX = CONFIGS / "scenario_campaign_matrix.yaml"
HORIZONS = {"2026_2030": 2030, "2026_2050": 2050}


class TestScenarioBaseConfigs(unittest.TestCase):
    """One REF base per ISO per horizon, varying nothing but ISO and horizon."""

    def test_one_base_per_iso_per_horizon(self):
        for iso in SUPPORTED_ISOS:
            for span, end_year in HORIZONS.items():
                path = (
                    CONFIGS / "scenarios" / f"{iso.lower()}_scenario_base_{span}.yaml"
                )
                self.assertTrue(path.exists(), path)
                config = ScenarioConfig.from_yaml(path)
                self.assertEqual(config.iso, iso)
                self.assertEqual(config.mode, "forecast")
                self.assertEqual(config.start_year, 2026)
                self.assertEqual(config.end_year, end_year)

    def test_base_varies_nothing_but_iso_and_horizon(self):
        # REF is the SHIPPED posture (plan §3.0): every other field must equal
        # the ScenarioConfig default, or the campaign's deltas stop being
        # comparable across ISOs.
        import dataclasses

        exempt = {"iso", "start_year", "end_year", "mode"}
        for iso in SUPPORTED_ISOS:
            path = CONFIGS / "scenarios" / f"{iso.lower()}_scenario_base_2026_2050.yaml"
            config = ScenarioConfig.from_yaml(path)
            reference = ScenarioConfig(iso=iso, mode="forecast")
            for field in dataclasses.fields(ScenarioConfig):
                if field.name in exempt:
                    continue
                self.assertEqual(
                    getattr(config, field.name),
                    getattr(reference, field.name),
                    f"{iso} {field.name} is not the shipped default",
                )


class TestCampaignMatrix(unittest.TestCase):
    """The case set loads, separates, and only ever names live fields."""

    def setUp(self):
        self.sweep = SweepDefinition.from_yaml(MATRIX)

    def test_reference_case_is_present_and_empty(self):
        cases = self.sweep.cases
        self.assertIn("REF", cases)
        self.assertEqual(cases["REF"] or {}, {})

    def test_every_live_case_names_only_real_config_fields(self):
        import dataclasses

        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        for case, overrides in self.sweep.cases.items():
            for field in overrides or {}:
                self.assertIn(field, names, f"{case} names a missing field {field!r}")

    def test_cases_expand_and_carry_distinct_cache_keys(self):
        for iso in SUPPORTED_ISOS:
            base = ScenarioConfig.from_yaml(
                CONFIGS / "scenarios" / f"{iso.lower()}_scenario_base_2026_2030.yaml"
            )
            configs = self.sweep.case_configs(base)
            self.assertIn("REF", configs)
            keys = {case: c.cache_key() for case, c in configs.items()}
            self.assertEqual(
                len(set(keys.values())), len(keys), f"{iso} cases collide: {keys}"
            )

    def test_the_carbon_ladder_is_the_additive_delta_form(self):
        # G-C1 is live at this commit: an explicit carbon_price_path SUPPRESSES
        # the program trajectory, so a path-form ladder is a carbon CUT on
        # CAISO/NYISO/NEISO. The committed ladder must therefore be additive.
        for case in ("CARB-LO", "CARB-MID", "CARB-HI"):
            overrides = self.sweep.cases[case]
            self.assertIn("carbon_price_delta", overrides)
            self.assertNotIn("carbon_price_path", overrides)
            self.assertGreater(overrides["carbon_price_delta"], 0.0)

    def test_load_high_declares_its_datacenter_pairing(self):
        # G-L3: growth-high and DC-high are independent axes, so each high case
        # must state both rather than leave the pairing implicit.
        for case in ("LOAD-HI", "LOAD-HI-ORGANIC"):
            overrides = self.sweep.cases[case]
            self.assertEqual(overrides["demand_growth_path"], "high")
            self.assertIn("datacenter_load_path", overrides)
        self.assertNotEqual(
            self.sweep.cases["LOAD-HI"]["datacenter_load_path"],
            self.sweep.cases["LOAD-HI-ORGANIC"]["datacenter_load_path"],
        )

    def test_no_case_is_left_commented(self):
        # CES-T80 LEFT the commented list at SCN-LEVELS (2026-09-06); VOL-MID /
        # VOL-HI / CES-P20+VOL-HI / ALL-CLEAN at SCN-WS3b (2026-09-06); and
        # CAP-STATE-TIGHT, the last, at SCN-CAP (2026-09-06) under owner
        # ruling S12 on card D-2(c). Every plan §3.5 case is now live, so the
        # header's "STILL COMMENTED" note must say NOTHING and the case set
        # must carry all fourteen names.
        expected = {
            "REF",
            "CARB-LO",
            "CARB-MID",
            "CARB-HI",
            "CAP-STATE-TIGHT",
            "CES-P10",
            "CES-P20",
            "CES-P30",
            "CES-T80",
            "VOL-MID",
            "VOL-HI",
            "LOAD-HI",
            "LOAD-HI-ORGANIC",
            "CARB-MID+LOAD-HI",
            "CES-P20+VOL-HI",
            "ALL-CLEAN",
        }
        self.assertTrue(expected <= set(self.sweep.cases), set(self.sweep.cases))

    def test_cap_state_tight_is_live_at_the_committed_schedule(self):
        # Owner ruling S12 (2026-09-06, SCN-DESK r#12 am.1, card D-2(c)):
        # "Commit the 80 % slope and build the field." The schedule is
        # FINDING-scn-ws1a-2026-09-05.md §4.2 VERBATIM — a linear decline to
        # 20 % of the 2025 published per-state budget by 2050, CAISO anchored
        # to the model's REF-2026 CO2 because CARB publishes no power-sector
        # budget. This pins the ruled level to the numbers so it cannot drift
        # without a test saying so (the CES-T80 pin's construction).
        overrides = self.sweep.cases["CAP-STATE-TIGHT"]
        self.assertTrue(overrides["mass_cap_enabled"])
        self.assertEqual(overrides["mass_cap_program"], "co2")
        self.assertTrue(overrides["state_carbon_pricing"])
        self.assertEqual(overrides["carbon_price_path"], "zero")
        self.assertEqual(
            overrides["mass_cap_tons_by_year"],
            {
                "NYISO": {2026: 23.16e6, 2030: 20.2e6, 2040: 12.8e6, 2050: 4.6e6},
                "NEISO": {2026: 20.67e6, 2030: 18.0e6, 2040: 11.4e6, 2050: 4.1e6},
                "CAISO": {2026: 30.5e6, 2030: 26.5e6, 2040: 16.5e6, 2050: 6.1e6},
            },
        )
        # Every knot parsed as a NUMBER (PyYAML reads `23.16e6` as a string;
        # the file writes the signed-exponent form), and the schedule is the
        # 80 % decline it claims: last knot = 0.2 x first knot, to the
        # rounding WS-1a §4.2 wrote.
        for iso, knots in overrides["mass_cap_tons_by_year"].items():
            for year, tons in knots.items():
                self.assertIsInstance(year, int, f"{iso} {year!r}")
                self.assertIsInstance(tons, float, f"{iso} {year} {tons!r}")
            self.assertAlmostEqual(knots[2050] / knots[2026], 0.2, delta=0.002, msg=iso)
        # The scalar is NOT set beside the schedule: one budget source per
        # case (rule 19 [R-ONE-MECH]); the schedule already outranks it.
        self.assertNotIn("mass_cap_tons", overrides)
        # A program-ISO case: exactly the three program ISOs are scheduled.
        self.assertEqual(
            set(overrides["mass_cap_tons_by_year"]), {"CAISO", "NYISO", "NEISO"}
        )

    def test_cap_state_tight_resolves_to_nothing_on_the_no_program_isos(self):
        # ERCOT / MISO carry no cap-and-trade program, so the case resolves
        # to NO carbon program at all there — no row, no adder — and the LP is
        # byte-identical to REF's. PJM is deliberately NOT in this list: it
        # carries a partial RGGI program and falls through to the published
        # regional budget in 2027-2030 (a slack row), which
        # tests/unit/policy/test_mass_cap_schedule.py pins and
        # FINDING-scn-cap-2026-09-06.md §5 routes to the desk.
        from market_sim.policy.cap_and_trade import resolve_carbon_program
        from market_sim.policy.constraints import get_active_policy_constraints

        for iso in ("ERCOT", "MISO"):
            base = ScenarioConfig.from_yaml(
                CONFIGS / "scenarios" / f"{iso.lower()}_scenario_base_2026_2030.yaml"
            )
            configs = self.sweep.case_configs(base)
            ref, cap = configs["REF"], configs["CAP-STATE-TIGHT"]
            for year in range(2026, 2031):
                self.assertIsNone(resolve_carbon_program(ref, year), (iso, year))
                self.assertIsNone(resolve_carbon_program(cap, year), (iso, year))
                self.assertEqual(get_active_policy_constraints(cap, year), [])

    def test_cap_state_tight_binds_only_through_the_schedule_on_program_isos(self):
        # On the three program ISOs the case's budget is the SCHEDULE's number
        # in every horizon year — never the published fallback (which WS-1a
        # §4.1 measured wildly slack after 2025) and never a scalar.
        from market_sim.policy.cap_and_trade import (
            resolve_carbon_program,
            scheduled_power_sector_budget,
        )

        for iso in ("CAISO", "NYISO", "NEISO"):
            base = ScenarioConfig.from_yaml(
                CONFIGS / "scenarios" / f"{iso.lower()}_scenario_base_2026_2030.yaml"
            )
            cap = self.sweep.case_configs(base)["CAP-STATE-TIGHT"]
            self.assertEqual(cap.mode, "forecast")
            self.assertIsNotNone(cap.mass_cap_tons_by_year)
            for year in range(2026, 2031):
                res = resolve_carbon_program(cap, year)
                self.assertIsNotNone(res.cap_spec, (iso, year))
                self.assertIsNone(res.price_adder, (iso, year))
                self.assertAlmostEqual(
                    res.cap_spec.cap_tons,
                    scheduled_power_sector_budget(cap, year),
                    msg=(iso, year),
                )

    def test_voluntary_cases_are_live_on_the_one_field(self):
        # SCN-WS3b (2026-09-06): the four cases the plan §3.5 table lists on the
        # voluntary axis, each carrying the axis as a path label and nothing
        # else voluntary (levels live in constants.VOLUNTARY_*, never here).
        self.assertEqual(
            self.sweep.cases["VOL-MID"], {"voluntary_clean_demand_path": "mid"}
        )
        self.assertEqual(
            self.sweep.cases["VOL-HI"], {"voluntary_clean_demand_path": "high"}
        )
        combo = self.sweep.cases["CES-P20+VOL-HI"]
        self.assertEqual(combo["voluntary_clean_demand_path"], "high")
        self.assertEqual(combo["federal_ces_premium_usd_per_mwh"], 20.0)
        self.assertNotIn("federal_ces_target_by_year", combo)
        corner = self.sweep.cases["ALL-CLEAN"]
        self.assertEqual(corner["voluntary_clean_demand_path"], "high")
        self.assertEqual(corner["datacenter_load_path"], "high")
        self.assertEqual(corner["demand_growth_path"], "high")
        self.assertEqual(corner["federal_ces_acp_usd_per_mwh"], 50.0)
        self.assertEqual(corner["carbon_price_delta"], 25.0)
        for case in ("VOL-MID", "VOL-HI", "CES-P20+VOL-HI", "ALL-CLEAN"):
            for field in self.sweep.cases[case]:
                self.assertNotIn(
                    field,
                    ("voluntary_wtp_ceiling_usd_per_mwh", "voluntary_eligible_fuels"),
                )

    def test_ces_target_case_is_live_at_the_committed_level(self):
        # Owner card D-2 -> S3 (2026-09-06, SCN-DESK r#5 am.1): the plan's
        # §3.5 table is the committed default, CES target
        # {2026: <current>, 2035: 0.80, 2050: 1.00} with ACP $50. `<current>`
        # is resolved by the plan's own §3 WS-2 item 5 as 0.55, which is what
        # SCN-WS2a probed. This pins the LABEL ruling to the numbers, so the
        # committed level cannot drift without a test saying so.
        overrides = self.sweep.cases["CES-T80"]
        self.assertTrue(overrides["federal_ces_enabled"])
        self.assertEqual(
            overrides["federal_ces_target_by_year"],
            {2026: 0.55, 2035: 0.80, 2050: 1.00},
        )
        self.assertEqual(overrides["federal_ces_acp_usd_per_mwh"], 50.0)
        # Rule 19 [R-ONE-MECH]: the target row and a non-zero exogenous
        # premium are mutually exclusive, so the case must not name one.
        self.assertNotIn("federal_ces_premium_usd_per_mwh", overrides)


class TestSetOverride(unittest.TestCase):
    """``--set FIELD=VALUE`` validates against ScenarioConfig, never silently."""

    def test_parses_and_coerces_scalar_types(self):
        parsed = parse_set_overrides(
            [
                "carbon_price_delta=25",
                "federal_ces_enabled=true",
                "demand_growth_path=high",
                "end_year=2030",
            ]
        )
        self.assertEqual(parsed["carbon_price_delta"], 25.0)
        self.assertIsInstance(parsed["carbon_price_delta"], float)
        self.assertIs(parsed["federal_ces_enabled"], True)
        self.assertEqual(parsed["demand_growth_path"], "high")
        self.assertEqual(parsed["end_year"], 2030)

    def test_none_and_empty_are_no_ops(self):
        self.assertEqual(parse_set_overrides(None), {})
        self.assertEqual(parse_set_overrides([]), {})

    def test_unknown_field_is_a_hard_error(self):
        with self.assertRaises(SystemExit) as ctx:
            parse_set_overrides(["not_a_real_field=1"])
        self.assertIn("not a ScenarioConfig field", str(ctx.exception))

    def test_malformed_spec_rejected(self):
        with self.assertRaises(SystemExit):
            parse_set_overrides(["carbon_price_delta"])

    def test_repeated_field_rejected(self):
        with self.assertRaises(SystemExit):
            parse_set_overrides(["carbon_price_delta=1", "carbon_price_delta=2"])

    def test_uncoercible_value_rejected(self):
        with self.assertRaises(SystemExit):
            parse_set_overrides(["carbon_price_delta=not-a-number"])
        with self.assertRaises(SystemExit):
            parse_set_overrides(["federal_ces_enabled=maybe"])

    def test_apply_returns_an_overridden_config(self):
        base = ScenarioConfig(iso="NEISO", mode="forecast")
        out = apply_set_overrides(base, {"carbon_price_delta": 25.0})
        self.assertEqual(out.carbon_price_delta, 25.0)
        self.assertEqual(base.carbon_price_delta, 0.0)  # base untouched
        # A solve-affecting override must move the cache key, or an arm and its
        # control would collide on disk.
        self.assertNotEqual(out.cache_key(), base.cache_key())

    def test_apply_with_no_overrides_is_the_same_object(self):
        base = ScenarioConfig(iso="NEISO", mode="forecast")
        self.assertIs(apply_set_overrides(base, {}), base)


if __name__ == "__main__":
    unittest.main()
