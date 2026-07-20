"""Fast logic tests for the Tier-1 driver-battery harness.

These exercise the *scoring* plumbing of ``scripts/run_driver_battery.py`` — the
declarative expectation primitives, the ladder registry integrity, the dynamic
rung resolver (T1.2), and the per-ISO expectation split (T1.7) — WITHOUT solving
any LP (that is the minutes-scale job of the harness itself, and is smoked once
in the build session / run in full by P-1A). They are the per-PR guard that the
ladder table and scorer stay well-formed; the real solve path is covered by
``tests/test_driver_directionality.py``'s analytic LPs.
"""

from __future__ import annotations

import unittest

from scripts import run_driver_battery as B


class TestLadderRegistry(unittest.TestCase):
    def test_nine_ladders_unique_ids(self):
        lads = B.build_ladders()
        ids = [lad.test_id for lad in lads]
        self.assertEqual(len(ids), 9)
        self.assertEqual(sorted(ids), [f"T1.{i}" for i in range(1, 10)])

    def test_every_expectation_uses_a_known_rule(self):
        for lad in B.build_ladders():
            self.assertTrue(lad.expectations, f"{lad.test_id} has no expectations")
            for exp in lad.expectations:
                self.assertIn(exp.rule, B._RULES, (lad.test_id, exp.rule))

    def test_expectation_ids_carry_plan_test_id_prefix(self):
        # Each expectation id must start with its ladder's plan §2 test id, so a
        # ledger row is traceable to the pre-registered claim.
        for lad in B.build_ladders():
            for exp in lad.expectations:
                self.assertTrue(
                    exp.expr_id.startswith(lad.test_id),
                    f"{exp.expr_id} not under {lad.test_id}",
                )


class TestExpectationPrimitives(unittest.TestCase):
    def _rungs(self, metric, values):
        return [
            {"rung_label": f"r{i}", "status": "ok", "metrics": {metric: v}}
            for i, v in enumerate(values)
        ]

    def test_monotone_down_pass_and_fail(self):
        e = B.Expectation("X", "d", "m", "monotone_down")
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [3, 2, 1]))["status"], B.PASS
        )
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [1, 2, 3]))["status"], B.FAIL
        )

    def test_monotone_up_report_only_warns_not_fails(self):
        e = B.Expectation("X", "u", "m", "monotone_up", gate=False)
        row = B.evaluate_expectation(e, self._rungs("m", [3, 2, 1]))
        self.assertEqual(row["status"], B.WARN)  # violation, but report-only

    def test_le_target(self):
        e = B.Expectation("X", "le", "m", "le_target", target=1.0, tol=1e-3)
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [0.5, 1.0]))["status"], B.PASS
        )
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [0.5, 1.5]))["status"], B.FAIL
        )

    def test_approx_target_first(self):
        e = B.Expectation(
            "X", "cap", "mass_cap_price", "approx_target_first", target=25.0, tol=3.0
        )
        rungs = self._rungs("mass_cap_price", [24.0, 0.0])
        self.assertEqual(B.evaluate_expectation(e, rungs)["status"], B.PASS)
        rungs = self._rungs("mass_cap_price", [40.0])
        self.assertEqual(B.evaluate_expectation(e, rungs)["status"], B.FAIL)

    def test_all_equal(self):
        e = B.Expectation("X", "eq", "m", "all_equal", tol=1e-6)
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [2, 2, 2]))["status"], B.PASS
        )
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [2, 3, 2]))["status"], B.FAIL
        )

    def test_insufficient_rungs_skips(self):
        e = B.Expectation("X", "d", "m", "monotone_down")
        self.assertEqual(
            B.evaluate_expectation(e, self._rungs("m", [1]))["status"], B.SKIP
        )

    def test_missing_metric_skips(self):
        e = B.Expectation("X", "d", "absent_metric", "monotone_down")
        rungs = self._rungs("m", [3, 2, 1])
        self.assertEqual(B.evaluate_expectation(e, rungs)["status"], B.SKIP)


class TestDynamicRungResolver(unittest.TestCase):
    def test_mass_cap_from_anchor_sets_tons(self):
        lad = next(x for x in B.build_ladders() if x.test_id == "T1.2")
        solved = {
            "anchor_c25": {"status": "ok", "metrics": {"co2_mt_total": 10.0}},
        }
        resolved = B.resolve_dynamic_rungs(lad, solved)
        binding = next(r for r in resolved if r.label == "cap_binding")
        # 10 Mt x 1e6 x 1.0 multiplier -> 1e7 tons.
        self.assertAlmostEqual(binding.overrides["mass_cap_tons"], 1e7)
        self.assertNotIn("_mass_cap_from_anchor", binding.overrides)
        slack = next(r for r in resolved if r.label == "cap_slack")
        self.assertAlmostEqual(slack.overrides["mass_cap_tons"], 2e7)

    def test_missing_anchor_drops_dependent_rungs(self):
        lad = next(x for x in B.build_ladders() if x.test_id == "T1.2")
        resolved = B.resolve_dynamic_rungs(lad, {"anchor_c25": {"status": "failed"}})
        labels = [r.label for r in resolved]
        self.assertIn("anchor_c25", labels)
        self.assertNotIn("cap_binding", labels)


class TestExpectationSplitByIso(unittest.TestCase):
    def test_t17_monotone_gate_on_capacity_market_iso(self):
        lad = next(x for x in B.build_ladders() if x.test_id == "T1.7")
        pjm = [e.expr_id for e in B._expectations_for(lad, "PJM")]
        ercot = [e.expr_id for e in B._expectations_for(lad, "ERCOT")]
        self.assertEqual(pjm, ["T1.7a"])  # monotone-retirement gate
        self.assertEqual(ercot, ["T1.7b"])  # byte-identical negative control

    def test_t17a_scores_the_economic_channel_not_the_masked_total(self):
        # FF-2C §2.2 point 2: the cumulative total mixes in net-CONE-invariant
        # exogenous exits; the gate must score the economic component.
        lad = next(x for x in B.build_ladders() if x.test_id == "T1.7")
        a = next(e for e in lad.expectations if e.expr_id == "T1.7a")
        b = next(e for e in lad.expectations if e.expr_id == "T1.7b")
        self.assertEqual(a.metric, "economic_retired_thermal_gw")
        self.assertEqual(a.rule, "monotone_down")
        # The ERCOT negative control stays on the full capacity-drop total (the
        # strongest byte-identity check).
        self.assertEqual(b.metric, "retired_thermal_gw")
        self.assertEqual(b.rule, "all_equal")


class TestRetirementChannelSplit(unittest.TestCase):
    def test_splits_economic_from_exogenous_thermal_only(self):
        ledgers = {
            2027: {
                "retirements": [
                    {"fuel": "coal", "mw": 1000.0, "reason": "economic"},
                    {"fuel": "gas_ct", "mw": 500.0, "reason": "confirmed"},
                    {"fuel": "gas_cc", "mw": 300.0, "reason": "announced"},
                    {"fuel": "gas_st", "mw": 200.0, "reason": "known"},  # legacy
                    {"fuel": "solar", "mw": 999.0, "reason": "economic"},  # non-thermal
                ],
                "confirmed_derates": [
                    {"fuel": "coal", "derate_mw": 100.0},
                    {"fuel": "wind", "derate_mw": 50.0},  # non-thermal, ignored
                ],
            },
            2028: {
                "retirements": [{"fuel": "coal", "mw": 400.0, "reason": "economic"}]
            },
        }
        econ, exog = B._retirement_channel_split(ledgers)
        self.assertAlmostEqual(econ, 1.4)  # (1000 + 400) MW
        # confirmed 500 + announced 300 + known 200 + derate 100 = 1100 MW
        self.assertAlmostEqual(exog, 1.1)

    def test_empty_and_legacy_ledgers_are_safe(self):
        self.assertEqual(B._retirement_channel_split({}), (0.0, 0.0))
        # A ledger missing both keys (pre-RC-1B) contributes nothing, not a crash.
        self.assertEqual(B._retirement_channel_split({2027: {}}), (0.0, 0.0))


class TestNetConeScalarPatch(unittest.TestCase):
    """The T1.7 rig patch scales the channel a POST-FLIP curve ISO prices on."""

    def test_scale_market_design_scales_both_anchors_preserving_curve(self):
        from market_sim.config import constants as C

        base = C.MARKET_DESIGN["PJM"]
        scaled = B._scale_market_design(base, 2.0)
        self.assertAlmostEqual(scaled.net_cone_per_kw_yr, base.net_cone_per_kw_yr * 2.0)
        self.assertAlmostEqual(
            scaled.net_cone_curve_per_kw_yr, base.net_cone_curve_per_kw_yr * 2.0
        )
        # The curve SHAPE (dimensionless VRR points) is preserved untouched — only
        # the $ anchor scales.
        self.assertEqual(scaled.demand_curve, base.demand_curve)
        self.assertGreater(len(scaled.demand_curve), 0)

    def test_scale_market_design_scales_miso_seasonal_anchor(self):
        from market_sim.config import constants as C

        base = C.MARKET_DESIGN["MISO"]
        scaled = B._scale_market_design(base, 0.5)
        self.assertIsNotNone(scaled.seasonal_rbdc)
        self.assertAlmostEqual(
            scaled.seasonal_rbdc.daily_net_cone_per_mw_day,
            base.seasonal_rbdc.daily_net_cone_per_mw_day * 0.5,
        )
        # Season shapes/day-weights preserved.
        self.assertEqual(scaled.seasonal_rbdc.seasons, base.seasonal_rbdc.seasons)

    def test_scale_vintages_scales_every_vintage_anchor(self):
        from market_sim.config import constants as C

        base = C.MARKET_DESIGN_VINTAGES["PJM"]
        scaled = B._scale_vintages(base, 3.0)
        self.assertEqual(len(scaled), len(base))
        for sv, bv in zip(scaled, base):
            self.assertAlmostEqual(
                sv.net_cone_curve_per_kw_yr, bv.net_cone_curve_per_kw_yr * 3.0
            )
            self.assertEqual(sv.demand_curve, bv.demand_curve)  # shape preserved

    def test_apply_patches_is_effectively_inert_for_energy_only_ercot(self):
        # ERCOT is in MARKET_DESIGN as capacity_market=False with zero anchors, so
        # scaling produces an anchor-identical design and the pricing seam returns
        # 0 regardless — the negative control stays byte-identical across the
        # ladder. It carries no vintages, so that registry is untouched.
        from market_sim.config import constants as C
        from market_sim.model import capacity as cap

        before_vint = dict(C.MARKET_DESIGN_VINTAGES)
        saved_cap = cap.MARKET_DESIGN
        try:
            clean = B._apply_probe_patches({"_net_cone_scalar": 2.0}, "ERCOT")
            design = cap.MARKET_DESIGN["ERCOT"]
            self.assertFalse(design.capacity_market)
            self.assertEqual(design.net_cone_per_kw_yr, 0.0)
            self.assertEqual(design.net_cone_curve_per_kw_yr, 0.0)
            self.assertEqual(design.demand_curve, ())
            self.assertEqual(C.MARKET_DESIGN_VINTAGES, before_vint)  # no ERCOT vintage
            self.assertEqual(clean, {})  # the _-prefixed key is stripped
        finally:
            cap.MARKET_DESIGN = saved_cap

    def test_apply_patches_scales_registry_and_vintages_for_pjm(self):
        # _apply_probe_patches rebinds the capacity/constants module registries;
        # snapshot and restore so this in-process test does not contaminate others
        # (the real harness runs each rung in a fresh process, so it never does).
        from market_sim.config import constants as C
        from market_sim.model import capacity as cap

        base_curve = C.MARKET_DESIGN["PJM"].net_cone_curve_per_kw_yr
        base_vint0 = C.MARKET_DESIGN_VINTAGES["PJM"][0].net_cone_curve_per_kw_yr
        saved_cap = cap.MARKET_DESIGN
        saved_vint = C.MARKET_DESIGN_VINTAGES
        try:
            B._apply_probe_patches({"_net_cone_scalar": 2.0}, "PJM")
            self.assertAlmostEqual(
                cap.MARKET_DESIGN["PJM"].net_cone_curve_per_kw_yr, base_curve * 2.0
            )
            self.assertEqual(
                len(cap.MARKET_DESIGN["PJM"].demand_curve),
                len(C.MARKET_DESIGN["PJM"].demand_curve),
            )
            self.assertAlmostEqual(
                C.MARKET_DESIGN_VINTAGES["PJM"][0].net_cone_curve_per_kw_yr,
                base_vint0 * 2.0,
            )
        finally:
            cap.MARKET_DESIGN = saved_cap
            C.MARKET_DESIGN_VINTAGES = saved_vint


class TestRunLadderWithSeam(unittest.TestCase):
    """run_ladder end-to-end with an injected evaluate_fn (no real solve)."""

    def test_scored_ladder_from_fake_solves(self):
        lad = next(x for x in B.build_ladders() if x.test_id == "T1.1")

        # Fake worker: coal_twh and CO2 fall as carbon_price rises.
        def fake(spec_dict):
            carbon = spec_dict["overrides"].get("carbon_price", 0.0)
            coal = max(0.0, 100.0 - carbon)
            return {
                "rung_id": spec_dict["rung_id"],
                "test_id": spec_dict["test_id"],
                "iso": spec_dict["iso"],
                "rung_label": spec_dict["rung_label"],
                "overrides": spec_dict["overrides"],
                "status": "ok",
                "metrics": {
                    "coal_twh": coal,
                    "co2_mt_total": coal * 0.9,
                    "lw_price": 30.0 + carbon,
                },
                "cached": False,
            }

        result = B.run_ladder(
            lad,
            "ERCOT",
            2026,
            2026,
            cache_root="/tmp/none",
            metrics_root="/tmp/none",
            workers=1,
            evaluate_fn=fake,
        )
        by_id = {e["expr_id"]: e for e in result["expectations"]}
        self.assertEqual(by_id["T1.1a"]["status"], B.PASS)  # coal ↓
        self.assertEqual(by_id["T1.1b"]["status"], B.PASS)  # CO2 ↓
        self.assertEqual(by_id["T1.1c"]["status"], B.PASS)  # price ↑ (report)
        self.assertEqual(by_id["T1.1d"]["status"], B.PASS)  # coal moves


if __name__ == "__main__":
    unittest.main()
