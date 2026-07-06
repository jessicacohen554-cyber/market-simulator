"""Tests for the simulation runner and its command-line interface.

The dispatch LP is mocked throughout: ``solve_dispatch`` is patched to
return a synthetic :class:`DispatchResult` so the tests exercise the
runner's orchestration -- fleet evolution, caching, sweeps and CLI
parsing -- without the cost of solving a full-year model.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd

from market_sim import runner
from market_sim.pipeline import solve as pipeline_solve
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache


def _fake_solve(fleet, demand, *args, **kwargs):
    """Return a synthetic ``DispatchResult`` sized to the fleet and demand."""
    n_gen = fleet.n_gen
    T = demand.shape[1]
    n_zones = demand.shape[0]
    return DispatchResult(
        dispatch=np.full((n_gen, T), 5.0),
        wind_dispatched=np.zeros((n_zones, T)),
        solar_dispatched=np.zeros((n_zones, T)),
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=np.full((n_zones, T), 30.0),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


class _FakeDispatchModel:
    """Counting stand-in for the build-once / re-cost ``DispatchModel``.

    The runner's default P0/P1 path builds one model per year and re-costs it
    (intra-year warm-start), so the orchestration tests mock the model rather
    than the one-shot ``solve_dispatch``. Each ``solve`` returns a synthetic
    result sized to the fleet/demand and bumps a class counter so a test can
    assert "two solves (P0, P1) per simulated year".
    """

    n_solves = 0

    def __init__(self, fleet, demand, **kwargs):
        self._fleet = fleet
        self._demand = demand

    def solve(self, mc=None, **kwargs):
        type(self).n_solves += 1
        return _fake_solve(self._fleet, self._demand)


class RunnerTestBase(unittest.TestCase):
    """Base fixture redirecting the cache root to a temp directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)
        _FakeDispatchModel.n_solves = 0

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()


class TestRunScenarioIso(RunnerTestBase):
    """A scenario run solves and caches every simulation year once."""

    def test_three_years_create_three_cache_files(self):
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2028),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        # Two solves per simulated year (P0 base-cost, P1 bid-cost warm-started
        # off P0), 2026-2028. P2 commitment is off by default.
        self.assertEqual(_FakeDispatchModel.n_solves, 6)
        for year in (2026, 2027, 2028):
            self.assertTrue(cache.is_cached("ERCOT", key, year))

        parquets = sorted((cache.CACHE_ROOT / "ERCOT" / key).glob("year_*.parquet"))
        self.assertEqual(len(parquets), 3)

    def test_rerun_skips_all_cached_years(self):
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2028),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            runner.run_scenario_iso(config, "ERCOT")
            # Two solves (P0, P1) per year, 2026-2028.
            self.assertEqual(_FakeDispatchModel.n_solves, 6)

            # Re-running the identical scenario solves nothing new: every
            # year is loaded from the cache instead.
            runner.run_scenario_iso(config, "ERCOT")
            self.assertEqual(_FakeDispatchModel.n_solves, 6)

    def test_iso_argument_overrides_config_iso(self):
        config = ScenarioConfig(iso="CAISO")
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        # The run is cached under the requested ISO, not the config's.
        self.assertTrue(cache.is_cached("ERCOT", key, 2026))
        self.assertTrue((cache.CACHE_ROOT / "ERCOT" / key).is_dir())
        self.assertFalse((cache.CACHE_ROOT / "CAISO").exists())


class TestKnownYearPeakForesight(RunnerTestBase):
    """Capacity screens test the entering year's known peak (plan §2.3.1)."""

    def test_evolve_fleet_receives_entering_year_peak(self):
        from market_sim.config.scenarios import resolve_demand_growth_rate

        captured = {}
        original = runner.evolve_fleet

        def spy(fleet, prior_results, year, config, loss_tracker, **kw):
            captured[year] = {
                "peak_demand_next": kw.get("peak_demand_next"),
                "prior_peak": prior_results["peak_demand"],
            }
            return original(fleet, prior_results, year, config, loss_tracker, **kw)

        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "evolve_fleet", side_effect=spy),
        ):
            runner.run_scenario_iso(config, "ERCOT")

        # The 2027 evolution sees 2027's deterministic peak, one compound
        # growth step ahead of the prior (2026) peak it used to lag on —
        # i.e. peak_demand_next == _scale_demand(base, config, 2027).max
        # while prior_results carried _scale_demand(..., 2026).max.
        self.assertIn(2027, captured)
        got = captured[2027]
        expected = got["prior_peak"] * (1.0 + resolve_demand_growth_rate(config, 2026))
        self.assertAlmostEqual(got["peak_demand_next"], expected, places=6)


class TestPriceSignalByteIdentity(RunnerTestBase):
    """Defaults (alpha=1.0, lookahead off) pass econ_prices through unchanged."""

    def test_price_signal_is_econ_prices_object_at_defaults(self):
        captured = []
        original = runner.PriorYearResults

        def spy(**kwargs):
            captured.append(kwargs)
            return original(**kwargs)

        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "PriorYearResults", side_effect=spy),
        ):
            runner.run_scenario_iso(config, "ERCOT")

        self.assertGreaterEqual(len(captured), 2)
        for kwargs in captured:
            # Byte-identical: the signal IS the prices array object (plan
            # §8.2 — hash of price_signal vs econ_prices).
            self.assertIs(kwargs["price_signal"], kwargs["prices"])


class TestP2CommitmentLegacyWarning(RunnerTestBase):
    """P2 commitment (commitment_enabled=True) is a legacy, opt-in path."""

    def test_commitment_enabled_logs_deprecation_warning(self):
        config = ScenarioConfig(iso="ERCOT", commitment_enabled=True)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            self.assertLogs(runner.logger, level="WARNING") as logs,
        ):
            runner.run_scenario_iso(config, "ERCOT")

        self.assertTrue(
            any(
                "legacy" in msg and "energy_reserve_coopt" in msg for msg in logs.output
            )
        )

    def test_commitment_disabled_logs_no_deprecation_warning(self):
        config = ScenarioConfig(iso="ERCOT", commitment_enabled=False)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            self.assertNoLogs(runner.logger, level="WARNING"),
        ):
            runner.run_scenario_iso(config, "ERCOT")


class TestScarcityOverlayGeneralization(RunnerTestBase):
    """The post-solve ORDC scarcity overlay is gated by config, not ISO."""

    def test_ercot_overlay_invoked_when_scarcity_pricing_enabled(self):
        config = ScenarioConfig(iso="ERCOT", scarcity_pricing_enabled=True)
        self.assertTrue(config.scarcity_price_overlay is False)  # before ISO defaults
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "scarcity_prices") as mock_scarcity,
        ):
            mock_scarcity.return_value = {"scarcity_adder": np.zeros(config.hours)}
            runner.run_scenario_iso(config, "ERCOT")

        # ERCOT's ISOConfig.default_scenario_overrides turns scarcity_price_overlay
        # on, so the overlay still runs without the caller setting it explicitly.
        mock_scarcity.assert_called()

    def test_caiso_overlay_skipped_even_with_master_flag_enabled(self):
        config = ScenarioConfig(iso="CAISO", scarcity_pricing_enabled=True)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "scarcity_prices") as mock_scarcity,
        ):
            runner.run_scenario_iso(config, "CAISO")

        # CAISO has no scarcity_price_overlay default override, so the overlay
        # is skipped even though the master scarcity_pricing_enabled flag is on.
        mock_scarcity.assert_not_called()

    def test_overlay_skipped_when_both_flags_off_by_default(self):
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "scarcity_prices") as mock_scarcity,
        ):
            runner.run_scenario_iso(config, "ERCOT")

        # scarcity_pricing_enabled defaults False, so even ERCOT's overlay
        # default does not fire the overlay on its own.
        mock_scarcity.assert_not_called()


class TestRunSweep(RunnerTestBase):
    """A sweep runs every expanded config and caches each independently."""

    def test_two_configs_create_two_cache_dirs(self):
        sweep = SweepDefinition(sweep={"carbon_price": [0.0, 50.0]})
        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            keys = runner.run_sweep(sweep, workers=1)

        self.assertEqual(len(keys), 2)
        self.assertEqual(len(set(keys)), 2)

        cache_dirs = [d for d in (cache.CACHE_ROOT / "ERCOT").iterdir() if d.is_dir()]
        self.assertEqual(len(cache_dirs), 2)
        self.assertEqual({d.name for d in cache_dirs}, set(keys))


class TestMainCLI(RunnerTestBase):
    """The ``run`` subcommand parses its arguments correctly."""

    def _write_config(self, **overrides) -> Path:
        config = ScenarioConfig(**overrides)
        path = Path(self._tmp.name) / "scenario.yaml"
        config.to_yaml(path)
        return path

    def test_run_subcommand_parses_config_and_iso(self):
        cfg_path = self._write_config(iso="CAISO", carbon_price=12.0)
        with patch.object(runner, "run_scenario_iso") as run:
            runner.main(["run", "--config", str(cfg_path), "--iso", "ERCOT"])

        run.assert_called_once()
        called_config, called_iso = run.call_args[0]
        self.assertEqual(called_iso, "ERCOT")
        self.assertEqual(called_config.carbon_price, 12.0)
        self.assertEqual(called_config.iso, "CAISO")

    def test_run_subcommand_defaults_iso_to_config(self):
        cfg_path = self._write_config(iso="CAISO")
        with patch.object(runner, "run_scenario_iso") as run:
            runner.main(["run", "--config", str(cfg_path)])

        _, called_iso = run.call_args[0]
        self.assertEqual(called_iso, "CAISO")


class _StopAfterFleetArrays(Exception):
    """Raised by the traced fleet-array build to halt the run early."""


def _trace_fleet_build(iso: str, *, historic_overlay: bool = True) -> dict:
    """Run ``run_scenario_iso`` just far enough to observe the fleet build.

    The data loaders, storage builder and downstream collaborators are
    patched so the run reaches the per-plant-vs-legacy binning decision and
    the fleet-array build for *any* ISO without real input data or a solve.
    Returns the per-plant bins source (``"ercot_sheet"`` via load_campd_bins,
    ``"synth"`` via fleet_to_bins, or ``None``), which fleet builder ran
    (``"campd"`` per-plant tranches vs ``"legacy"`` aggregate_fleet), and the
    historic-outage overlay the fleet build actually received.
    """
    rec = {"bins_source": None, "builder": None, "overlay": None}

    def fake_demand(_iso, _wy, iso_config, **_kw):
        return np.full((len(iso_config.zone_names), 8), 1000.0)

    def fake_renewables(_iso, _wy, iso_config, _config):
        z = len(iso_config.zone_names)
        return np.zeros((z, 8)), np.zeros(z), np.zeros((z, 8)), np.zeros(z)

    def fake_load_campd_bins(*_a, **_k):
        rec["bins_source"] = "ercot_sheet"
        return "BINS"  # ERCOT's curated sheet; not indexed in this branch

    def fake_fleet_to_bins(*_a, **_k):
        rec["bins_source"] = "synth"
        # A non-empty frame carrying the columns the runner's binned-set
        # filter reads, so the synthesized CAMPD path is taken.
        return pd.DataFrame({"Plant_Code": [1], "Plant_Group": ["CC_REGULAR"]})

    def fake_bins_to_fleet(*_a, **_k):
        rec["builder"] = "campd"
        return [], {}

    def fake_aggregate_fleet(*_a, **_k):
        rec["builder"] = "legacy"
        return []

    def fake_fleet_arrays(
        _dispatch_fleet, _zone_names, *, hours, iso, config, load_shape, year=None
    ):
        rec["overlay"] = config.historic_outage_overlay
        raise _StopAfterFleetArrays

    config = ScenarioConfig(iso=iso, hours=8, historic_outage_overlay=historic_overlay)
    with (
        patch.object(runner, "load_demand", side_effect=fake_demand),
        patch.object(runner, "load_renewable_profiles", side_effect=fake_renewables),
        patch.object(runner, "load_planned_additions", return_value=[]),
        patch.object(runner, "build_default_storage", return_value=[]),
        # The CAMPD-vs-legacy binning primitives now live in
        # market_sim.data.fleet, called internally by
        # load_or_synthesize_bins / build_base_fleet / build_dispatch_fleet
        # -- patch them there so the fake implementations are observed
        # regardless of which unified helper invokes them.
        patch("market_sim.data.fleet.load_fleet_from_csv", return_value=[]),
        patch(
            "market_sim.data.fleet.load_campd_bins", side_effect=fake_load_campd_bins
        ),
        patch("market_sim.data.fleet.fleet_to_bins", side_effect=fake_fleet_to_bins),
        patch("market_sim.data.fleet.bins_to_fleet", side_effect=fake_bins_to_fleet),
        patch(
            "market_sim.data.fleet.aggregate_fleet", side_effect=fake_aggregate_fleet
        ),
        patch("market_sim.data.fleet.campd_tranche_fuel_frac", return_value=1.0),
        patch(
            "market_sim.data.fleet.split_coal_tranches",
            side_effect=lambda f, c, *_a, **_k: (list(f), [1.0] * len(f)),
        ),
        patch("market_sim.data.fleet.apply_plant_emission_rates"),
        patch.object(
            runner, "generators_to_fleet_arrays", side_effect=fake_fleet_arrays
        ),
    ):
        try:
            runner.run_scenario_iso(config, iso)
        except _StopAfterFleetArrays:
            pass
    return rec


class TestCampdBinningGate(unittest.TestCase):
    """The per-plant CAMPD binning path unlocks per-ISO by bin artifact."""

    def test_ercot_takes_campd_path(self):
        # Parity: ERCOT must still read its curated bin sheet and build the
        # fleet from per-plant tranches (bins_to_fleet), never aggregate_fleet.
        rec = _trace_fleet_build("ERCOT")
        self.assertEqual(rec["bins_source"], "ercot_sheet")
        self.assertEqual(rec["builder"], "campd")

    def test_artifact_isos_take_campd_path(self):
        # CAISO/NEISO/NYISO/PJM/MISO now follow ERCOT onto the per-plant path,
        # with their bins synthesized from the CAMPD thermal-tranche artifact.
        for iso in ("CAISO", "NEISO", "NYISO", "PJM", "MISO"):
            with self.subTest(iso=iso):
                rec = _trace_fleet_build(iso)
                self.assertEqual(rec["bins_source"], "synth")
                self.assertEqual(rec["builder"], "campd")

    def test_gate_membership(self):
        from market_sim.config.constants import CAMPD_BINNING_ISOS

        for iso in ("ERCOT", "CAISO", "NEISO", "NYISO", "PJM", "MISO"):
            self.assertIn(iso, CAMPD_BINNING_ISOS)


class TestHistoricOutageOverlayDefault(unittest.TestCase):
    """The historic-outage overlay default is resolved per ISO."""

    def test_ercot_overlay_true(self):
        # ERCOT's facility-summed overlay is the primary layer: stays True.
        self.assertTrue(_trace_fleet_build("ERCOT")["overlay"])

    def test_pjm_overlay_false(self):
        # PJM's unit-level file is the complete source: overlay defaults False
        # even though the global ScenarioConfig default is True.
        self.assertFalse(_trace_fleet_build("PJM")["overlay"])

    def test_unlisted_iso_uses_config_flag(self):
        # An ISO absent from the registry keeps the explicit config flag.
        self.assertTrue(_trace_fleet_build("MISO", historic_overlay=True)["overlay"])
        self.assertFalse(_trace_fleet_build("MISO", historic_overlay=False)["overlay"])


class TestDemandGrowth(unittest.TestCase):
    """Piecewise demand growth: near-term vs long-term rates by era."""

    def test_near_term_year_uses_near_rate(self):
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2028), 0.05)

    def test_long_term_year_uses_long_rate(self):
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2035), 0.025)

    def test_transition_boundary(self):
        # 2030 is the last near-term year; 2031 is the first long-term year.
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2030), 0.05)
        self.assertAlmostEqual(runner._get_growth_rate(config, 2031), 0.025)

    def test_flat_override_when_no_structured_path(self):
        # An ISO/path with no structured rates falls back to the scalar.
        config = ScenarioConfig(
            iso="ERCOT",
            demand_growth_path="nonexistent",
            demand_growth_rate=0.07,
        )
        self.assertAlmostEqual(runner._get_growth_rate(config, 2028), 0.07)
        self.assertAlmostEqual(runner._get_growth_rate(config, 2040), 0.07)

    def test_scale_demand_compounds_from_weather_year(self):
        # base_demand is the *weather year's* actual load (2024 default),
        # so the first simulated year already carries two years of growth.
        # Compounding from START_YEAR instead silently presented 2024
        # actuals as 2026 demand (peer review C1).
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        base = np.full((1, 8), 100.0)
        # 2026: two near-rate years of growth (2024, 2025).
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2026), base * 1.05**2
        )
        # 2028: four years of the near rate (2024-2027).
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2028), base * 1.05**4
        )
        # 2032: seven near years (2024-2030) then one long year (2031).
        expected = base * 1.05**7 * 1.025**1
        np.testing.assert_allclose(runner._scale_demand(base, config, 2032), expected)

    def test_scale_demand_backcast_year_is_unscaled(self):
        # A backcast solves the weather year itself: factor exactly 1.
        config = ScenarioConfig(
            iso="ERCOT", weather_year=2023, demand_growth_path="mid"
        )
        base = np.full((1, 8), 100.0)
        np.testing.assert_allclose(runner._scale_demand(base, config, 2023), base)


class _CapturingDispatchModel(_FakeDispatchModel):
    """``_FakeDispatchModel`` that records the kwargs passed at construction."""

    captured_kwargs: list[dict] = []

    def __init__(self, fleet, demand, **kwargs):
        super().__init__(fleet, demand, **kwargs)
        type(self).captured_kwargs.append(kwargs)


class TestStorageDischargeCostWiring(RunnerTestBase):
    """``storage_discharge_cost`` reaches the forecast dispatch path."""

    def setUp(self):
        super().setUp()
        _CapturingDispatchModel.captured_kwargs = []
        _CapturingDispatchModel.n_solves = 0

    def test_battery_dispatch_adder_reaches_dispatch_kwargs(self):
        config = ScenarioConfig(iso="ERCOT", battery_dispatch_adder=7.5)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _CapturingDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            runner.run_scenario_iso(config, "ERCOT")

        self.assertTrue(_CapturingDispatchModel.captured_kwargs)
        kw = _CapturingDispatchModel.captured_kwargs[0]
        sdc = kw.get("storage_discharge_cost")
        self.assertIsNotNone(sdc, "storage_discharge_cost missing from dispatch kwargs")
        # Every battery unit's vom should be the adder (7.5); PS has 0.
        import numpy as np

        sdc_arr = np.asarray(sdc)
        self.assertTrue(
            (sdc_arr >= 0.0).all(),
            "storage_discharge_cost should be non-negative",
        )
        # At least one entry equals the battery adder.
        self.assertTrue(
            np.any(np.isclose(sdc_arr, 7.5)),
            "battery_dispatch_adder=7.5 not found in storage_discharge_cost",
        )

    def test_zero_adder_leaves_dispatch_cost_zero(self):
        config = ScenarioConfig(iso="ERCOT", battery_dispatch_adder=0.0)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _CapturingDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            runner.run_scenario_iso(config, "ERCOT")

        kw = _CapturingDispatchModel.captured_kwargs[0]
        sdc = kw.get("storage_discharge_cost")
        self.assertIsNotNone(sdc, "storage_discharge_cost missing from dispatch kwargs")

        self.assertTrue(
            np.allclose(np.asarray(sdc), 0.0),
            "default adder=0 should yield all-zero storage_discharge_cost",
        )


class TestMassCapPerUnitMembershipWiring(RunnerTestBase):
    """The mass-cap row's per-generator coefficients use per-unit membership.

    End-to-end (real PJM fleet + EIA-860 plant-state lookup, mocked dispatch
    solve) check that runner.py's cap_coeffs computation
    (per_generator_membership, not the raw zone broadcast) runs cleanly and
    produces a coefficient vector with the expected shape/sign.
    """

    def setUp(self):
        super().setUp()
        _CapturingDispatchModel.captured_kwargs = []
        _CapturingDispatchModel.n_solves = 0

    def test_pjm_cap_coeffs_reach_dispatch_kwargs(self):
        config = ScenarioConfig(iso="PJM", mass_cap_enabled=True, mass_cap_tons=1.0e6)
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _CapturingDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(runner, "solve_dispatch", side_effect=_fake_solve),
        ):
            runner.run_scenario_iso(config, "PJM")

        self.assertTrue(_CapturingDispatchModel.captured_kwargs)
        kw = _CapturingDispatchModel.captured_kwargs[0]
        coeffs = kw.get("mass_cap_coeffs")
        self.assertIsNotNone(coeffs, "mass_cap_coeffs missing from dispatch kwargs")
        coeffs = np.asarray(coeffs)
        self.assertEqual(coeffs.ndim, 2)
        self.assertEqual(coeffs.shape[0], 1)
        # Every coefficient is non-negative (membership in [0,1] times a
        # non-negative emission rate).
        self.assertTrue((coeffs >= 0.0).all())
        self.assertEqual(kw.get("mass_cap_rhs").tolist(), [1.0e6])


class TestChpMeasuredCo2Inputs(unittest.TestCase):
    """R5: the CHP BTM rate source mirrors the grid tranches' source."""

    def test_legacy_source_returns_pooled_rates(self):
        # use_plant_emission_rates (default) -> BTM books the legacy pooled rate,
        # the same rate the grid tranches use.
        config = ScenarioConfig(iso="ERCOT", mode="backcast")
        rates, _cf, _btm_share = runner._chp_measured_co2_inputs(config, "ERCOT", 2024)
        self.assertTrue(rates, "legacy pooled artifact should yield a rate map")
        self.assertTrue(all(v > 0 for v in rates.values()))

    def test_both_sources_off_returns_empty(self):
        # No plant-rate override -> empty maps -> caller keeps the fuel-class
        # default rate and the flat must_run_cf (no behaviour change).
        config = ScenarioConfig(
            iso="ERCOT", mode="backcast", use_plant_emission_rates=False
        )
        rates, cf, btm_share = runner._chp_measured_co2_inputs(config, "ERCOT", 2024)
        self.assertEqual(rates, {})
        self.assertEqual(cf, {})
        self.assertEqual(
            btm_share, {}, "backcast mode must not source measured BTM share"
        )

    def test_forecast_mode_sources_measured_btm_share(self):
        # Forecast mode resolves the measured chp-btm-share artifact when
        # present; with no clean partition on disk it degrades to empty (the
        # caller's pct_mr fallback), never raising.
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        _rates, _cf, btm_share = runner._chp_measured_co2_inputs(config, "ERCOT", 2030)
        self.assertIsInstance(btm_share, dict)


if __name__ == "__main__":
    unittest.main()
