"""Tests for the sensitivity/tornado diagnostic runner (PP-3.1).

The real forward solve is never invoked: the orchestration, ranking, report
rendering, and metric-extraction math are exercised with an injected fake
evaluator or patched cache/runner seams, mirroring ``tests/test_runner.py``.
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

# The runner lives in scripts/ (not an installed package); load it by path.
_SPEC = importlib.util.spec_from_file_location(
    "run_sensitivity_tornado", REPO / "scripts" / "run_sensitivity_tornado.py"
)
tornado = importlib.util.module_from_spec(_SPEC)
sys.modules["run_sensitivity_tornado"] = tornado
_SPEC.loader.exec_module(tornado)

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402


class TestRegistry(unittest.TestCase):
    """Every registered band must produce a valid ScenarioConfig."""

    def test_registry_nonempty_and_has_forecast_and_dispatch(self):
        reg = tornado.build_registry()
        self.assertGreaterEqual(len(reg), 15)
        cats = {p.category for p in reg}
        self.assertIn("forecast", cats)
        self.assertIn("dispatch", cats)

    def test_every_band_yields_a_valid_config(self):
        reg = tornado.build_registry()
        base = ScenarioConfig(iso="ERCOT", use_campd_bins=False)
        for p in reg:
            for direction, overrides in (
                ("low", p.low_overrides),
                ("high", p.high_overrides),
            ):
                with self.subTest(param=p.key, direction=direction):
                    # with_overrides runs __post_init__ validation.
                    cfg = base.with_overrides(**overrides)
                    self.assertIsInstance(cfg, ScenarioConfig)

    def test_param_keys_unique(self):
        keys = [p.key for p in tornado.build_registry()]
        self.assertEqual(len(keys), len(set(keys)))


class TestMakeSpecs(unittest.TestCase):
    """make_specs emits one base spec plus a low/high pair per parameter."""

    def test_spec_shape(self):
        reg = tornado.build_registry()
        specs = tornado.make_specs(
            "ERCOT", reg, {"use_campd_bins": False}, 2026, 2028, "/tmp/x"
        )
        self.assertEqual(len(specs), 1 + 2 * len(reg))
        base = specs[0]
        self.assertEqual(base.direction, "base")
        self.assertEqual(base.overrides, {})
        directions = {(s.param_key, s.direction) for s in specs[1:]}
        for p in reg:
            self.assertIn((p.key, "low"), directions)
            self.assertIn((p.key, "high"), directions)

    def test_base_overrides_propagate(self):
        specs = tornado.make_specs(
            "ERCOT",
            tornado.build_registry()[:1],
            {"use_campd_bins": False},
            2026,
            2027,
            "/tmp/x",
        )
        for s in specs:
            self.assertEqual(s.base_overrides, {"use_campd_bins": False})
            self.assertEqual(s.start_year, 2026)
            self.assertEqual(s.end_year, 2027)


def _fake_metrics(co2_final, co2_total, price, retired):
    """Build an evaluate_fn result dict with the given headline metrics."""

    def _fn(spec_dict):
        return {
            "variant_id": spec_dict["variant_id"],
            "param_key": spec_dict["param_key"],
            "direction": spec_dict["direction"],
            "status": "ok",
            "co2_mt_final": co2_final(spec_dict),
            "co2_mt_total": co2_total(spec_dict),
            "avg_price": price(spec_dict),
            "retired_thermal_gw": retired(spec_dict),
            "retired_by_fuel": {},
            "per_year": [],
            "error": None,
        }

    return _fn


class TestRunTornadoInjection(unittest.TestCase):
    """run_tornado with an injected evaluator runs in-process, no solves."""

    def test_all_variants_collected(self):
        reg = tornado.build_registry()[:3]
        specs = tornado.make_specs("ERCOT", reg, {}, 2026, 2027, "/tmp/x")
        fake = _fake_metrics(
            lambda s: 100.0, lambda s: 200.0, lambda s: 25.0, lambda s: 0.0
        )
        results = tornado.run_tornado(specs, evaluate_fn=fake)
        self.assertEqual(len(results), len(specs))
        self.assertIn("base", results)
        for p in reg:
            self.assertEqual(results[f"{p.key}:low"].status, "ok")
            self.assertEqual(results[f"{p.key}:high"].status, "ok")


class TestRanking(unittest.TestCase):
    """rank_results computes high-low deltas and sorts by magnitude."""

    def _run(self, per_variant):
        reg = tornado.build_registry()[:2]
        specs = tornado.make_specs("ERCOT", reg, {}, 2026, 2027, "/tmp/x")

        def fake(spec_dict):
            vid = spec_dict["variant_id"]
            m = per_variant.get(vid, {})
            return {
                "variant_id": vid,
                "param_key": spec_dict["param_key"],
                "direction": spec_dict["direction"],
                "status": m.get("status", "ok"),
                "co2_mt_final": m.get("co2", 0.0),
                "co2_mt_total": m.get("co2", 0.0),
                "avg_price": m.get("price", 0.0),
                "retired_thermal_gw": m.get("retired", 0.0),
                "retired_by_fuel": {},
                "per_year": [],
                "error": m.get("error"),
            }

        results = tornado.run_tornado(specs, evaluate_fn=fake)
        return reg, tornado.rank_results(reg, results)

    def test_delta_and_ordering(self):
        reg = tornado.build_registry()[:2]
        k0, k1 = reg[0].key, reg[1].key
        per = {
            f"{k0}:low": {"co2": 100.0},
            f"{k0}:high": {"co2": 110.0},  # delta 10
            f"{k1}:low": {"co2": 100.0},
            f"{k1}:high": {"co2": 130.0},  # delta 30 (bigger)
            "base": {"co2": 105.0},
        }
        _, ranking = self._run(per)
        rows = ranking["ranked"]["co2_mt_final"]
        self.assertEqual(rows[0]["key"], k1)  # biggest swing first
        self.assertEqual(rows[0]["delta"], 30.0)
        self.assertEqual(rows[1]["key"], k0)
        self.assertEqual(rows[1]["delta"], 10.0)

    def test_negative_delta_ranked_by_magnitude(self):
        reg = tornado.build_registry()[:2]
        k0, k1 = reg[0].key, reg[1].key
        per = {
            f"{k0}:low": {"co2": 100.0},
            f"{k0}:high": {"co2": 60.0},  # delta -40
            f"{k1}:low": {"co2": 100.0},
            f"{k1}:high": {"co2": 120.0},  # delta +20
        }
        _, ranking = self._run(per)
        rows = ranking["ranked"]["co2_mt_final"]
        self.assertEqual(rows[0]["key"], k0)  # |-40| > |20|
        self.assertEqual(rows[0]["abs_delta"], 40.0)

    def test_failed_band_excluded(self):
        reg = tornado.build_registry()[:2]
        k0, k1 = reg[0].key, reg[1].key
        per = {
            f"{k0}:low": {"co2": 100.0},
            f"{k0}:high": {"status": "failed", "error": "boom"},
            f"{k1}:low": {"co2": 100.0},
            f"{k1}:high": {"co2": 120.0},
        }
        _, ranking = self._run(per)
        self.assertIn(k0, ranking["failed"])
        keys = {r["key"] for r in ranking["ranked"]["co2_mt_final"]}
        self.assertNotIn(k0, keys)
        self.assertIn(k1, keys)


class TestRenderReport(unittest.TestCase):
    """render_report emits the expected sections."""

    def test_report_sections(self):
        reg = tornado.build_registry()[:3]
        specs = tornado.make_specs(
            "ERCOT", reg, {"use_campd_bins": False}, 2026, 2028, "/tmp/x"
        )
        fake = _fake_metrics(
            lambda s: 100.0, lambda s: 300.0, lambda s: 25.0, lambda s: 1.0
        )
        results = tornado.run_tornado(specs, evaluate_fn=fake)
        ranking = tornado.rank_results(reg, results)
        report = tornado.render_report(
            "ERCOT",
            2026,
            2028,
            {"use_campd_bins": False},
            reg,
            results,
            ranking,
            "2026-07-04",
        )
        self.assertIn("# Sensitivity tornado — ERCOT", report)
        self.assertIn("## Run configuration", report)
        self.assertIn("### Base case", report)
        self.assertIn("## Tornado rankings", report)
        self.assertIn("CO2 final year (Mt)", report)
        self.assertIn("## Parameter bands", report)
        self.assertIn("## DOF-ledger feed", report)
        self.assertIn("legacy equal-width bins", report)


class TestEvaluateVariant(unittest.TestCase):
    """evaluate_variant's extraction math and failure handling (no real LP)."""

    def _spec(self, **kw):
        base = dict(
            variant_id="base",
            param_key="base",
            direction="base",
            iso="ERCOT",
            base_overrides={"use_campd_bins": False},
            overrides={},
            start_year=2026,
            end_year=2027,
            cache_root="/tmp/tornado_test_cache",
        )
        base.update(kw)
        return base

    def test_failure_is_captured_not_raised(self):
        with patch(
            "market_sim.runner.run_scenario_iso", side_effect=RuntimeError("infeasible")
        ):
            out = tornado.evaluate_variant(self._spec())
        self.assertEqual(out["status"], "failed")
        self.assertIn("infeasible", out["error"])
        self.assertIsNone(out["co2_mt_final"])

    def test_metric_extraction_and_retirement_math(self):
        # Per-year synthetic summaries: coal retires 2 GW between 2026 and 2027.
        summaries = {
            2026: {
                "emissions_mt": 100.0,
                "avg_price": 20.0,
                "capacity_gw": {"coal": 10.0, "gas_cc": 5.0, "wind": 3.0},
            },
            2027: {
                "emissions_mt": 90.0,
                "avg_price": 22.0,
                "capacity_gw": {"coal": 8.0, "gas_cc": 5.0, "wind": 4.0},
            },
        }

        def fake_summarize(dispatch_result, context):
            # dispatch_result is the year sentinel we return from load_result.
            return summaries[dispatch_result]

        with (
            patch("market_sim.runner.run_scenario_iso", return_value="KEY"),
            patch(
                "market_sim.results.cache.load_result",
                side_effect=lambda iso, key, year: year,
            ),
            patch(
                "market_sim.results.cache.load_fleet_context",
                side_effect=lambda iso, key, year: None,
            ),
            patch(
                "market_sim.results.export._summarize_year", side_effect=fake_summarize
            ),
        ):
            out = tornado.evaluate_variant(self._spec())

        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["co2_mt_final"], 90.0)
        self.assertEqual(out["co2_mt_total"], 190.0)
        self.assertAlmostEqual(out["avg_price"], 21.0)
        # wind is not thermal; coal drop of 2 GW is the only retirement.
        self.assertEqual(out["retired_by_fuel"], {"coal": 2.0})
        self.assertAlmostEqual(out["retired_thermal_gw"], 2.0)


if __name__ == "__main__":
    unittest.main()
