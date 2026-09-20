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
import yaml

from market_sim import runner
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline import solve as pipeline_solve
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from tests.helpers.base import CleanDirTestCase


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

    def export_cross_year_basis(self):
        """No basis to hand forward — the fake has no LP.

        Reached since the D-9 flip (``forecast_xyear_warmstart`` default ON):
        the forecast year loop now threads a real ``xyear_cache``, so the shared
        solve core asks each year's model for its optimal basis. ``None`` means
        "nothing to carry", which the core already handles — the next year then
        starts cold, which is exactly right for a model that never solved an LP.
        """
        return None

    def apply_cross_year_basis(self, prev):
        """Decline any prior basis (nothing to install into). Mirrors the real
        ``DispatchModel``'s ``False`` return for a skipped warm start."""
        return False


class _HermeticCleanDir(CleanDirTestCase):
    """CLEAN_DIR redirect + an empty confirmed-retirements datatype root.

    CI parity: data/clean is derived and gitignored, so on a fresh checkout
    (and on every CI run) it does not exist. Since the W2-E fail-loud wiring
    (8aa7e14 + 652c2a8, 2026-07-17) the default forecast path calls
    ``load_confirmed_exits(iso, required=True)``, which raises on a
    never-curated checkout. Carrying the empty datatype ROOT selects the
    loader's documented curated-root/zero-row degrade path instead, so these
    tests exercise the orchestrator hermetically — exactly what they did
    before the wiring — rather than requiring a local curation run.
    """

    def setUp(self):
        super().setUp()
        (self.clean_dir / "confirmed-retirements").mkdir(parents=True)


class RunnerTestBase(_HermeticCleanDir):
    """Base fixture redirecting the cache root to a temp directory."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)
        _FakeDispatchModel.n_solves = 0

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()
        super().tearDown()


class TestRunScenarioIso(RunnerTestBase):
    """A scenario run solves and caches every simulation year once."""

    def test_three_years_create_three_cache_files(self):
        config = ScenarioConfig(iso="ERCOT")
        with (
            patch.object(runner, "END_YEAR", 2028),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        # The run is cached under the requested ISO, not the config's.
        self.assertTrue(cache.is_cached("ERCOT", key, 2026))
        self.assertTrue((cache.CACHE_ROOT / "ERCOT" / key).is_dir())
        self.assertFalse((cache.CACHE_ROOT / "CAISO").exists())

    def test_miso_forecast_reaches_first_solve(self):
        # BLK-1 regression: build_default_storage(iso_config, config) is
        # called unconditionally in run_scenario_iso, and used to raise
        # ValueError for MISO (the one ISO missing from STORAGE_BASE_FLEET_MW)
        # before any dispatch solve ran. mode="forecast" is the ScenarioConfig
        # default, so this reproduces the exact reported crash path.
        config = ScenarioConfig(iso="MISO", start_year=2026, end_year=2026)
        self.assertEqual(config.mode, "forecast")
        with (
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            key = runner.run_scenario_iso(config, "MISO")

        self.assertTrue(cache.is_cached("MISO", key, 2026))


class TestCachedBundleConfigCheck(RunnerTestBase):
    """A bundle whose stored config disagrees is REFUSED and re-solved.

    capx D24 option (c′), owner ruling Q20: the cache key drops every registered
    field at its default, so a bundle sitting at this run's key is not proof it
    was solved under this run's config -- D24 §4 demonstrated two committed pairs
    at one key with different postures. The seam in ``run_scenario_iso`` compares
    the stored ``config.yaml`` before serving, and treats a disagreement as a
    logged MISS, never an exception.
    """

    def _solve_once(self, config):
        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            return runner.run_scenario_iso(config, "ERCOT")

    def test_a_disagreeing_stored_config_forces_a_re_solve(self):
        config = ScenarioConfig(iso="ERCOT", start_year=2026, end_year=2026)
        key = self._solve_once(config)
        self.assertEqual(_FakeDispatchModel.n_solves, 2)  # P0 + P1, one year

        # Simulate the collision: the bundle on disk was solved under the
        # OPPOSITE storage-entry posture, which the key cannot see because both
        # runs dropped the field at whatever was the default on their own day.
        config_path = cache.get_config_path("ERCOT", key, 2026)
        stored = yaml.safe_load(config_path.read_text())
        stored["storage_entry_availability_gate"] = not stored[
            "storage_entry_availability_gate"
        ]
        config_path.write_text(yaml.safe_dump(stored, sort_keys=True))

        with self.assertLogs("market_sim.runner", level="WARNING") as logged:
            self._solve_once(config)
        # Re-solved rather than served, and the log names the field.
        self.assertEqual(_FakeDispatchModel.n_solves, 4)
        self.assertTrue(
            any("storage_entry_availability_gate" in line for line in logged.output),
            msg=logged.output,
        )
        # save_result rewrote the sidecar, so the bundle is servable again.
        self._solve_once(config)
        self.assertEqual(_FakeDispatchModel.n_solves, 4)

    def test_an_agreeing_stored_config_is_still_served(self):
        # The other half: the check must not turn every hit into a miss.
        config = ScenarioConfig(iso="ERCOT", start_year=2026, end_year=2026)
        self._solve_once(config)
        self.assertEqual(_FakeDispatchModel.n_solves, 2)
        self._solve_once(config)
        self.assertEqual(_FakeDispatchModel.n_solves, 2)


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

        config = ScenarioConfig(iso="ERCOT", datacenter_load_path="off")
        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
            patch.object(runner, "evolve_fleet", side_effect=spy),
        ):
            runner.run_scenario_iso(config, "ERCOT")

        # The 2027 evolution sees 2027's deterministic peak, one compound
        # growth step ahead of the prior (2026) peak it used to lag on —
        # i.e. peak_demand_next == _scale_demand(base, config, 2027).max
        # while prior_results carried _scale_demand(..., 2026).max.
        self.assertIn(2027, captured)
        got = captured[2027]
        # The pure compound-growth relation holds only when the peak is the raw
        # _scale_demand output. Since FF-1F the DC block defaults to "mid" and
        # RELOCATES a year-specific energy fraction (flattening each year's peak
        # by a different amount), so pin it "off" here to isolate the
        # peak-foresight TIMING this test targets (DC relocation is covered by
        # test_datacenter.py). config is DC-off below.
        expected = got["prior_peak"] * (1.0 + resolve_demand_growth_rate(config, 2026))
        self.assertAlmostEqual(got["peak_demand_next"], expected, places=6)


class TestPriceSignalByteIdentity(RunnerTestBase):
    """With lookahead pinned off, econ_prices pass through unchanged.

    ``entry_lookahead_reprice`` defaulted OFF when this test was written; the
    FF-2A owner sign-off (2026-07-18) flipped the forecast default ON, so the
    pass-through premise now needs the flag pinned — the same treatment
    e0a2e20 gave ``datacenter_load_path`` in this file for the FF-1F flip.
    Since the D12-A arming (owner ruling Q15, 2026-08-30) ERCOT's ISO
    overrides also arm ``entry_margin_exhaustion`` +
    ``entry_forward_reserve_leg``, both of which ``__post_init__`` refuses
    without the reprice, so disarming the reprice now requires pinning the
    pair off WITH it (the dependency wall
    ``test_ercot_stageb_arming.py::TestD12AArming`` pins deliberately).
    The assertion itself is unchanged.
    """

    def test_price_signal_is_econ_prices_object_at_defaults(self):
        captured = []
        original = runner.PriorYearResults

        def spy(**kwargs):
            captured.append(kwargs)
            return original(**kwargs)

        config = ScenarioConfig(
            iso="ERCOT",
            entry_lookahead_reprice=False,
            entry_margin_exhaustion=False,
            entry_forward_reserve_leg=False,
        )
        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
        # A schedulable T1-F window. Without explicit years the config inherits
        # the 2026-2050 module default, which the §2.1b cap now refuses before
        # the subcommand reaches run_scenario_iso (FFR-1D, audit FR-25) — that
        # refusal has its own coverage in tests/scoring/test_schedulable_guard.py;
        # these cases are about argument parsing.
        overrides.setdefault("start_year", 2026)
        overrides.setdefault("end_year", 2030)
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
        _dispatch_fleet,
        _zone_names,
        *,
        hours,
        iso,
        config,
        load_shape,
        year=None,
        **_kw,
    ):
        # ``**_kw`` so this fake tolerates OPTIONAL kwargs the real builder
        # gains later (SPP-66 added ``netload_shape``). This helper exists to
        # observe the outage overlay and the binning path, NOT to pin the
        # fleet-build call surface — without the catch-all it fails with a
        # TypeError on every such addition, which reads like a runner
        # regression and is not one. Matches ``fake_demand``/``fake_renewables``
        # above, which already take ``**_kw``.
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


class TestCampdBinningGate(_HermeticCleanDir):
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


class TestHistoricOutageOverlayDefault(_HermeticCleanDir):
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


class TestStrictDemandProfileWiring(unittest.TestCase):
    """``ScenarioConfig.strict_demand_profile`` reaches ``load_demand``."""

    def _captured_kwarg(self, strict: bool) -> bool:
        captured = {}

        def fake_demand(_iso, _wy, iso_config, **kwargs):
            captured["strict_demand_profile"] = kwargs.get("strict_demand_profile")
            raise _StopAfterFleetArrays

        config = ScenarioConfig(iso="ERCOT", hours=8, strict_demand_profile=strict)
        with patch.object(runner, "load_demand", side_effect=fake_demand):
            try:
                runner.run_scenario_iso(config, "ERCOT")
            except _StopAfterFleetArrays:
                pass
        return captured["strict_demand_profile"]

    def test_true_reaches_loader(self):
        self.assertTrue(self._captured_kwarg(True))

    def test_false_reaches_loader(self):
        self.assertFalse(self._captured_kwarg(False))


class TestDemandGrowth(unittest.TestCase):
    """Piecewise demand growth: near-term vs long-term rates by era."""

    # Rates read from the constant so these era-selection mechanic tests survive
    # a currency refresh (FF-1C: ERCOT mid near 0.05 -> 0.085, long 0.025 held).
    def test_near_term_year_uses_near_rate(self):
        from market_sim.config.constants import DEMAND_GROWTH_RATES

        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        near = DEMAND_GROWTH_RATES["ERCOT"]["mid"]["near"]
        self.assertAlmostEqual(runner._get_growth_rate(config, 2028), near)

    def test_long_term_year_uses_long_rate(self):
        from market_sim.config.constants import DEMAND_GROWTH_RATES

        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        long = DEMAND_GROWTH_RATES["ERCOT"]["mid"]["long"]
        self.assertAlmostEqual(runner._get_growth_rate(config, 2035), long)

    def test_transition_boundary(self):
        # 2030 is the last near-term year; 2031 is the first long-term year.
        from market_sim.config.constants import DEMAND_GROWTH_RATES

        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        near = DEMAND_GROWTH_RATES["ERCOT"]["mid"]["near"]
        long = DEMAND_GROWTH_RATES["ERCOT"]["mid"]["long"]
        self.assertAlmostEqual(runner._get_growth_rate(config, 2030), near)
        self.assertAlmostEqual(runner._get_growth_rate(config, 2031), long)

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
        from market_sim.config.constants import DEMAND_GROWTH_RATES

        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        # Read the rates from the constant so this mechanic test survives a
        # currency refresh (FF-1C moved ERCOT mid near 0.05 -> 0.085).
        near = 1.0 + DEMAND_GROWTH_RATES["ERCOT"]["mid"]["near"]
        long = 1.0 + DEMAND_GROWTH_RATES["ERCOT"]["mid"]["long"]
        base = np.full((1, 8), 100.0)
        # 2026: two near-rate years of growth (2024, 2025).
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2026), base * near**2
        )
        # 2028: four years of the near rate (2024-2027).
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2028), base * near**4
        )
        # 2032: seven near years (2024-2030) then one long year (2031).
        expected = base * near**7 * long**1
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
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
        # use_plant_emission_rates_v2 defaults to True (scenarios.py), so both
        # sources must be disabled explicitly to exercise the empty path.
        config = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            use_plant_emission_rates=False,
            use_plant_emission_rates_v2=False,
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


class _RecordingDispatchModel(_FakeDispatchModel):
    """``_FakeDispatchModel`` that records each year's demand array reaching the LP.

    One instance is built per simulation year (build-once / re-cost), so
    ``demands`` holds exactly the demand vector the LP saw for each year — the
    object we assert the data-center block did (or did not) modify.
    """

    demands: list = []

    def __init__(self, fleet, demand, **kwargs):
        super().__init__(fleet, demand, **kwargs)
        type(self).demands.append(demand)


class TestDatacenterBlockWiring(RunnerTestBase):
    """G-34: add_datacenter_block is wired into runner demand assembly.

    Default-off is byte-identical (the DC block returns the same array object,
    so the demand reaching the LP is the exact _scale_demand output); a forecast
    run with a non-off path lands the per-ISO DC MW trajectory in the demand
    vector.
    """

    def _run_capture(self, config):
        """Run a single forecast year (2026) capturing per-year _scale_demand
        outputs and the demand arrays reaching the LP."""
        _RecordingDispatchModel.demands = []
        scale_out: dict = {}
        orig_scale = runner._scale_demand

        def _rec_scale(base, cfg, yr):
            out = orig_scale(base, cfg, yr)
            scale_out[yr] = out  # seam-2 (LP) call is the last write per year
            return out

        with (
            patch.object(runner, "END_YEAR", 2026),
            patch.object(runner, "_scale_demand", side_effect=_rec_scale),
            patch.object(pipeline_solve, "DispatchModel", _RecordingDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
        ):
            runner.run_scenario_iso(config, "ERCOT")
        return scale_out, list(_RecordingDispatchModel.demands)

    def test_off_path_demand_is_scale_demand_object_byte_identical(self):
        # datacenter_load_path="off" => add_datacenter_block returns the SAME
        # array object, so the demand reaching the LP is the identical
        # _scale_demand output (no copy, no addition): byte-identical. "off" is
        # no longer the default (FF-1F flipped it to "mid"), so pin it here.
        config = ScenarioConfig(iso="ERCOT", datacenter_load_path="off")
        scale_out, demands = self._run_capture(config)
        self.assertEqual(len(demands), 1)  # one DispatchModel per year (2026)
        self.assertIs(demands[0], scale_out[2026])

    def test_forecast_path_relocates_datacenter_mw_in_demand(self):
        # A forecast run with a non-off DC path RELOCATES the published per-ISO
        # DC MW block (FF-1C double-count fix): because the near-era growth rate
        # is DC-inclusive, the block scales the grown peaky demand down by its
        # energy fraction and adds it back flat -- total energy INVARIANT, peak
        # flattened -- and the demand reaching the LP is a NEW array.
        from market_sim.data.datacenter import resolve_datacenter_mw

        config = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
        scale_out, demands = self._run_capture(config)
        self.assertEqual(len(demands), 1)
        lp_demand = demands[0]
        base = scale_out[2026]

        # New array, not the byte-identical off-path object.
        self.assertIsNot(lp_demand, base)

        block_mw = (
            resolve_datacenter_mw(config, "ERCOT", 2026) * config.datacenter_load_factor
        )
        self.assertGreater(block_mw, 0.0)  # ERCOT mid is nonzero in 2026
        base_energy = float(base.sum())
        dc_energy = block_mw * base.shape[1]
        self.assertLess(dc_energy, base_energy)  # relocate regime
        scale = 1.0 - dc_energy / base_energy

        # Total energy is invariant (the double-count is removed, not stacked).
        self.assertAlmostEqual(float(lp_demand.sum()), base_energy, places=1)
        # Peak flattens to base_peak*scale + block_mw, strictly below base+block.
        base_peak = float(base.sum(axis=0).max())
        self.assertAlmostEqual(
            float(lp_demand.sum(axis=0).max()),
            base_peak * scale + block_mw,
            places=3,
        )
        self.assertLess(float(lp_demand.sum(axis=0).max()), base_peak + block_mw)


class TestCapacityMarketClearingWiring(RunnerTestBase):
    """The runner threads the CR-1 reserve position into evolve_fleet (P-1B)."""

    def _run_capturing_reserve_position(self, config):
        captured = {}
        original = runner.evolve_fleet

        def spy(fleet, prior_results, year, config, loss_tracker, **kw):
            captured[year] = kw.get("reserve_position")
            return original(fleet, prior_results, year, config, loss_tracker, **kw)

        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
            patch.object(runner, "evolve_fleet", side_effect=spy),
        ):
            runner.run_scenario_iso(config, config.iso)
        return captured

    def test_reserve_position_none_when_gate_off(self):
        # Default (gate off): no reserve position is computed or threaded, so
        # the screens keep the fixed capacity price (byte-identical path).
        captured = self._run_capturing_reserve_position(ScenarioConfig(iso="ERCOT"))
        self.assertIn(2027, captured)
        self.assertIsNone(captured[2027])

    def test_reserve_position_threaded_when_gate_on(self):
        # Gate on: the runner computes the entering-fleet reserve position once
        # and threads a real float into evolve_fleet for every evolved year.
        captured = self._run_capturing_reserve_position(
            ScenarioConfig(iso="ERCOT", capacity_market_clearing=True)
        )
        self.assertIn(2027, captured)
        self.assertIsInstance(captured[2027], float)
        self.assertGreater(captured[2027], 0.0)


class TestJointSignalVolumePosture(RunnerTestBase):
    """The C-1 joint posture: dual-based level + margin-exhaustion walk.

    Owner ruling R-B (2026-08-31), charter
    ``docs/PRECOMMIT-c1-joint-wind-2026-08-31.md`` §1.3. The lookahead seam's
    AVAILABILITY arms on ``entry_lookahead_reprice or
    entry_margin_exhaustion``, while every CONSUMPTION of its level stays
    gated on ``entry_lookahead_reprice`` alone -- so with the reprice
    disarmed and the walk armed the screens keep the raw prior-year zonal
    duals as their price object *and* get a live repricer for the walk's
    within-year delta.
    """

    def _run_capturing_priors(self, config):
        """Run a short scenario, returning every PriorYearResults built."""
        captured = []
        original = runner.PriorYearResults

        def spy(**kwargs):
            obj = original(**kwargs)
            captured.append((kwargs, obj))
            return obj

        with (
            patch.object(runner, "END_YEAR", 2027),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
            patch.object(runner, "PriorYearResults", side_effect=spy),
        ):
            runner.run_scenario_iso(config, "ERCOT")
        self.assertGreaterEqual(len(captured), 2)
        return captured

    # Ruling Q15 (2026-08-30) arms entry_margin_exhaustion AND
    # entry_forward_reserve_leg as ERCOT forecast defaults via
    # ISOConfig.default_scenario_overrides, so a reprice-disarmed ERCOT config
    # must pin BOTH to express its posture: the D12 leg's own refusal (which
    # this lane did not touch) makes a disarmed leg carrying it
    # unconstructible, and an unpinned exhaustion would silently arm and turn
    # the "disarm alone" control into the joint posture. Same pins the A/B's
    # two arms carry (charter Amendment 1).
    def test_joint_posture_consumes_duals_and_builds_a_walk(self):
        captured = self._run_capturing_priors(
            ScenarioConfig(
                iso="ERCOT",
                entry_lookahead_reprice=False,
                entry_margin_exhaustion=True,
                entry_forward_reserve_leg=False,
            )
        )
        for kwargs, _ in captured:
            # The disarm property is preserved exactly: the screens' price
            # object IS the prices array, never the repriced level.
            self.assertIs(kwargs["price_signal"], kwargs["prices"])
        # ...and the walk is nonetheless live (the whole point of the joint
        # posture -- lifting the config refusal alone would leave it None).
        self.assertTrue(
            any(obj.entry_reprice is not None for _, obj in captured),
            "joint posture built no margin-exhaustion walk",
        )

    def test_disarm_alone_builds_no_walk(self):
        """The widening must not leak into the plain disarm posture."""
        captured = self._run_capturing_priors(
            ScenarioConfig(
                iso="ERCOT",
                entry_lookahead_reprice=False,
                entry_margin_exhaustion=False,
                entry_forward_reserve_leg=False,
            )
        )
        for kwargs, obj in captured:
            self.assertIs(kwargs["price_signal"], kwargs["prices"])
            self.assertIsNone(obj.entry_reprice)

    def test_armed_reprice_still_consumes_the_repriced_level(self):
        """The shipped default posture is untouched by the widening."""
        captured = self._run_capturing_priors(ScenarioConfig(iso="ERCOT"))
        self.assertTrue(
            any(
                kwargs["price_signal"] is not kwargs["prices"] for kwargs, _ in captured
            )
        )


if __name__ == "__main__":
    unittest.main()
