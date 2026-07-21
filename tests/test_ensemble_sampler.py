"""Tests for the sampler-driven ensemble path (PB-2) in ``market_sim.ensemble``.

Exercises config expansion, the worker-default cap, and the §4.1 output surface
(draws/metrics/bands parquet + ensemble_meta.json) against seeded fake member
results on a redirected cache root -- no solves.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.ensemble import (
    _config_year_range,
    _default_workers,
    compute_bands,
    export_sampler_ensemble,
    sample_ensemble_configs,
)
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from market_sim.results.outputs import FleetContext
from market_sim.uncertainty import GasMarginal, UncertaintySpec


def _spec(n=6, seed=3):
    return UncertaintySpec(
        n=n,
        seed=seed,
        gas=GasMarginal(sigma_front=0.35, sigma_back=0.41),
        spearman=((1.0, 0.3, 0.0), (0.3, 1.0, 0.0), (0.0, 0.0, 1.0)),
        discrete_weights={
            "weather": {2023: 1 / 3, 2024: 1 / 3, 2025: 1 / 3},
            "hydro": {"dry": 0.25, "normal": 0.5, "wet": 0.25},
            "policy": {"current": 0.5, "tight": 0.25, "rollback": 0.25},
        },
    )


def _make_result(seed):
    rng = np.random.default_rng(seed)
    T, n_gen, n_zones = 24, 3, 2
    return DispatchResult(
        dispatch=rng.random((n_gen, T)) * 100.0,
        wind_dispatched=rng.random((n_zones, T)) * 50.0,
        solar_dispatched=rng.random((n_zones, T)) * 40.0,
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=rng.random((n_zones, T)) * 80.0,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=1.0,
        status="Optimal",
        build_time=0.1,
        solve_time=0.1,
        emissions=None,
    )


def _make_context():
    return FleetContext(
        fuel_types=["gas_cc", "gas_ct", "coal"],
        pmax_mw=[400.0, 150.0, 600.0],
        emission_rate=[0.38, 0.6, 1.0],
        efficiency_bins=["h_class", "aero", "older"],
        heat_rates=[6.4, 9.8, 10.2],
        zones=["North", "South", "North"],
        unit_ids=["G0", "G1", "G2"],
        wind_cap_mw=10000.0,
        solar_cap_mw=8000.0,
        wind_potential_mwh=1.0e7,
        solar_potential_mwh=5.0e6,
        storage_energy_cap_mwh=0.0,
    )


class TestSampleEnsembleConfigs(unittest.TestCase):
    def test_expands_to_n_configs_with_draw_ids(self):
        configs, drawset = sample_ensemble_configs(ScenarioConfig(), _spec(n=8))
        self.assertEqual(len(configs), 8)
        self.assertEqual(len(drawset), 8)
        self.assertEqual(list(configs), [d.draw_id for d in drawset])
        for draw_id, cfg in configs.items():
            self.assertTrue(draw_id.startswith("draw-"))
            self.assertEqual(cfg.mode, "forecast")

    def test_backcast_base_rejected(self):
        with self.assertRaises(ValueError):
            sample_ensemble_configs(ScenarioConfig(mode="backcast"), _spec())


class TestDefaultWorkers(unittest.TestCase):
    def test_default_capped_at_two(self):
        with mock.patch("market_sim.ensemble.cpu_count", return_value=32):
            self.assertEqual(_default_workers(None), 2)

    def test_default_never_below_one(self):
        with mock.patch("market_sim.ensemble.cpu_count", return_value=1):
            self.assertEqual(_default_workers(None), 1)

    def test_explicit_workers_honoured(self):
        with mock.patch("market_sim.ensemble.cpu_count", return_value=32):
            self.assertEqual(_default_workers(8), 8)


class TestComputeBands(unittest.TestCase):
    def test_hf7_and_bootstrap_and_n(self):
        # Ten members, one year, one metric.
        values = {START_YEAR: {"emissions_mt": list(range(1, 11))}}
        rows = compute_bands(values, seed=1, quantiles=(0.1, 0.5, 0.9))
        self.assertEqual(len(rows), 3)
        by_q = {r["quantile"]: r for r in rows}
        # Type-7 median of 1..10 is 5.5; P10 is 1.9, P90 is 9.1 (numpy default).
        self.assertAlmostEqual(by_q[0.5]["value"], 5.5)
        self.assertAlmostEqual(by_q[0.1]["value"], 1.9)
        self.assertAlmostEqual(by_q[0.9]["value"], 9.1)
        for r in rows:
            self.assertEqual(r["n"], 10)
            self.assertEqual(r["layer"], "parametric")
            self.assertLessEqual(r["bootstrap_lo"], r["value"] + 1e-9)
            self.assertGreaterEqual(r["bootstrap_hi"], r["value"] - 1e-9)

    def test_bootstrap_deterministic_in_seed(self):
        values = {START_YEAR: {"m": [float(x) for x in range(20)]}}
        a = compute_bands(values, seed=42)
        b = compute_bands(values, seed=42)
        self.assertEqual(
            [(r["bootstrap_lo"], r["bootstrap_hi"]) for r in a],
            [(r["bootstrap_lo"], r["bootstrap_hi"]) for r in b],
        )


class TestExportSamplerEnsemble(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name) / "cache"
        self.iso = "ERCOT"
        self.spec = _spec(n=5)
        self.configs, self.drawset = sample_ensemble_configs(
            ScenarioConfig(iso=self.iso), self.spec
        )
        # Seed every member-year on disk and record its cache key.
        self.members = {}
        for i, (draw_id, cfg) in enumerate(self.configs.items()):
            for year in range(START_YEAR, END_YEAR + 1):
                cache.save_result(
                    _make_result(seed=i * 1000 + year),
                    cfg,
                    iso=self.iso,
                    year=year,
                    context=_make_context(),
                )
            self.members[draw_id] = cfg.cache_key()

    def tearDown(self):
        cache.CACHE_ROOT = self._orig_root
        self._tmp.cleanup()

    def test_writes_all_four_artifacts(self):
        out = Path(self._tmp.name) / "ensemble"
        paths = export_sampler_ensemble(
            ScenarioConfig(iso=self.iso),
            self.spec,
            self.iso,
            self.members,
            self.drawset,
            self.configs,
            out,
        )
        for key in ("draws", "metrics", "bands", "meta"):
            self.assertTrue(paths[key].exists())

        draws = pd.read_parquet(paths["draws"])
        self.assertEqual(len(draws), 5)
        for col in (
            "draw_id",
            "gas_price_factor",
            "demand_growth_percentile",
            "tech_cost_percentile",
            "weather_year",
            "hydro_year",
            "policy_bundle",
            "cache_key",
            "config_hash",
        ):
            self.assertIn(col, draws.columns)

        metrics = pd.read_parquet(paths["metrics"])
        self.assertEqual(set(metrics.columns), {"draw_id", "year", "metric", "value"})
        # emissions_mt is the first metric emitted per (draw, year).
        first = metrics[
            (metrics.draw_id == self.drawset[0].draw_id) & (metrics.year == START_YEAR)
        ].iloc[0]
        self.assertEqual(first["metric"], "emissions_mt")
        self.assertIn("generation_twh:gas_cc", set(metrics.metric))

        bands = pd.read_parquet(paths["bands"])
        self.assertEqual(
            set(bands.columns),
            {
                "year",
                "metric",
                "layer",
                "quantile",
                "value",
                "n",
                "bootstrap_lo",
                "bootstrap_hi",
            },
        )
        self.assertTrue((bands.n == 5).all())
        self.assertTrue((bands.layer == "parametric").all())
        self.assertEqual(
            sorted(bands.year.unique()), list(range(START_YEAR, END_YEAR + 1))
        )

    def test_meta_carries_spec_and_label(self):
        out = Path(self._tmp.name) / "ensemble"
        paths = export_sampler_ensemble(
            ScenarioConfig(iso=self.iso),
            self.spec,
            self.iso,
            self.members,
            self.drawset,
            self.configs,
            out,
        )
        meta = json.loads(paths["meta"].read_text())
        self.assertEqual(meta["iso"], "ERCOT")
        self.assertEqual(meta["sampler"]["seed"], self.spec.seed)
        self.assertEqual(meta["spec"]["n"], self.spec.n)
        self.assertIn("dispatch-conditional", meta["label"])
        self.assertIn("Hyndman-Fan type 7", meta["quantile_estimator"])
        self.assertEqual(set(meta["members"]), set(self.members))

    def test_structural_prior_adds_published_layer(self):
        """PB-3: folding a prior appends the published emissions layer (§4.1)."""
        from market_sim.structural_prior import STRUCTURAL_LAYER, fit_prior

        prior = fit_prior(
            {"ERCOT": {2023: 120.0, 2024: 122.0, 2025: 121.0}},
            {"ERCOT": {2023: 100.0, 2024: 100.0, 2025: 100.0}},
        )
        out = Path(self._tmp.name) / "ensemble_pub"
        base = self.spec
        # Parametric-only reference to prove the point forecast never moves.
        ref = Path(self._tmp.name) / "ensemble_ref"
        export_sampler_ensemble(
            ScenarioConfig(iso=self.iso),
            base,
            self.iso,
            self.members,
            self.drawset,
            self.configs,
            ref,
        )
        paths = export_sampler_ensemble(
            ScenarioConfig(iso=self.iso),
            base,
            self.iso,
            self.members,
            self.drawset,
            self.configs,
            out,
            prior=prior,
        )
        bands = pd.read_parquet(paths["bands"])
        self.assertIn(STRUCTURAL_LAYER, set(bands.layer))
        struct = bands[bands.layer == STRUCTURAL_LAYER]
        # Only emissions carries the structural layer.
        self.assertEqual(set(struct.metric), {"emissions_mt"})

        # Point forecast unchanged: parametric emissions P50 byte-identical.
        ref_bands = pd.read_parquet(ref / "bands.parquet")

        def p50(df):
            m = (
                (df.layer == "parametric")
                & (df.metric == "emissions_mt")
                & (df.quantile == 0.5)
            )
            return df[m].set_index("year")["value"]

        pd.testing.assert_series_equal(p50(bands), p50(ref_bands))

        meta = json.loads(paths["meta"].read_text())
        self.assertIn(STRUCTURAL_LAYER, meta["layers_present"])
        self.assertIn("structural_prior", meta)
        self.assertTrue(meta["structural_prior"]["dispatch_conditional"])
        self.assertIn("dispatch-conditional", meta["label"])


class TestConfigYearRange(unittest.TestCase):
    def test_none_bounds_default_to_module_horizon(self):
        self.assertEqual(_config_year_range(ScenarioConfig()), (START_YEAR, END_YEAR))

    def test_absent_config_defaults_to_module_horizon(self):
        self.assertEqual(_config_year_range(None), (START_YEAR, END_YEAR))

    def test_uses_config_bounds_when_set(self):
        cfg = ScenarioConfig(start_year=2026, end_year=2030)
        self.assertEqual(_config_year_range(cfg), (2026, 2030))


class TestShortHorizonAggregation(unittest.TestCase):
    """A T1-window ensemble must aggregate over its own solved horizon.

    Regression for the short-horizon band gap: a member solved only over
    2026-2028 (``start_year``/``end_year`` set) has no cached result past 2028,
    so the old hardcoded ``range(START_YEAR, END_YEAR + 1)`` raised
    ``FileNotFoundError`` at 2029. The aggregation must read the config horizon.
    """

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._orig_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name) / "cache"
        self.iso = "ERCOT"
        self.start, self.end = 2026, 2028
        self.spec = _spec(n=4)
        self.base = ScenarioConfig(
            iso=self.iso, start_year=self.start, end_year=self.end
        )
        self.configs, self.drawset = sample_ensemble_configs(self.base, self.spec)
        # The sampler must preserve the base horizon on every member.
        for cfg in self.configs.values():
            self.assertEqual((cfg.start_year, cfg.end_year), (self.start, self.end))
        self.members = {}
        for i, (draw_id, cfg) in enumerate(self.configs.items()):
            for year in range(self.start, self.end + 1):
                cache.save_result(
                    _make_result(seed=i * 1000 + year),
                    cfg,
                    iso=self.iso,
                    year=year,
                    context=_make_context(),
                )
            self.members[draw_id] = cfg.cache_key()

    def tearDown(self):
        cache.CACHE_ROOT = self._orig_root
        self._tmp.cleanup()

    def test_aggregates_over_solved_horizon_only(self):
        out = Path(self._tmp.name) / "ensemble"
        paths = export_sampler_ensemble(
            self.base,
            self.spec,
            self.iso,
            self.members,
            self.drawset,
            self.configs,
            out,
        )
        years = [self.start, self.start + 1, self.start + 2]
        bands = pd.read_parquet(paths["bands"])
        self.assertEqual(sorted(bands.year.unique()), years)
        metrics = pd.read_parquet(paths["metrics"])
        self.assertEqual(sorted(metrics.year.unique()), years)
        self.assertTrue((bands.n == 4).all())


if __name__ == "__main__":
    unittest.main()
