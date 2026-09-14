"""capx D76: the capacity-screen seam peak on the MEASURED hindcast load.

The defect the gate repairs (``FINDING-capx-d76-2026-09-06.md``): ``runner.py``
builds the capacity screens' peak at the top of its year loop from
``_scale_demand`` over the once-loaded weather-year base -- the GROWTH path --
while the LP's own ``year_demand``, 500 lines further down, takes the measured
hindcast branch. With ``weather_year`` 2024 and no per-solve-year weather
rebind, every non-weather hindcast year therefore hands the retirement
reliability floor, the reserve-margin backstop, the entry screen, the
accreditation census and the CR-1 position a SYNTHESIZED peak while the same
year's LP dispatches the measured one.

These tests pin all four halves of the repair: armed, the screens see the
measured peak; unarmed, the growth path is byte-identical to the pre-gate
behaviour; the measured year is loaded exactly ONCE (the screens and the LP
share one array, rule 19 ``[R-ONE-MECH]``); and the gate is inert wherever
there is no measured load to read -- a forecast run and a crossover FORWARD
year -- so the growth path remains the forecast methodology (rule 13
``[R-MEASURED]``).

Since capx D76-ARM-B (owner ruling Q58, 2026-09-07) the gate is ARMED BY
DEFAULT, in two halves, and the tests pin both: the dataclass default is ``True``
and the bare hindcast recipe therefore takes the ARMED key while an explicit
``False`` keeps the pre-flip one, and ``__post_init__`` coerces the field back to
its frozen declaration on any NON-hindcast config. The second half is why the
inertness tests set the flag on the RESOLVED config rather than through the
constructor -- otherwise the coercion would satisfy them trivially and they
would stop being claims about the seam at all.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from market_sim import runner
from market_sim.config.iso_configs import apply_iso_scenario_defaults, get_iso_config
from market_sim.config.scenarios import (
    _CAPACITY_SCREEN_PEAK_FROZEN_DECLARATION,
    ScenarioConfig,
    cache_key_drop_defaults,
)
from market_sim.pipeline import commitment as pipeline_commitment
from market_sim.pipeline import solve as pipeline_solve
from market_sim.results import cache
from tests.unit.pipeline.test_runner import (
    _FakeDispatchModel,
    _fake_solve,
    _HermeticCleanDir,
)

ISO = "ERCOT"
HOURS = 8760
# A recognizable system peak per year, so a captured peak names the year and
# the path that produced it without any tolerance argument.
PEAK_BY_YEAR = {
    2022: 60_000.0,
    2023: 70_000.0,
    2024: 90_000.0,
    2025: 110_000.0,
    2026: 120_000.0,
}


def _stub_demand(iso, year, iso_config, **kwargs):
    """Flat zonal demand whose system total is ``PEAK_BY_YEAR[year]``."""
    n = len(iso_config.zone_names)
    return np.full((n, HOURS), PEAK_BY_YEAR[year] / n, dtype=float)


class _SeamCase(_HermeticCleanDir):
    """Runs one year of the orchestrator with the LP and the loader faked."""

    def setUp(self):
        super().setUp()
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()
        super().tearDown()

    def run_seam(self, *, armed, hindcast=True, crossover_forward_year=None):
        """Return ``({year: screen_peak}, demand_load_years)`` for the window.

        ``screen_peak`` is the ``peak_demand_next`` ``evolve_fleet`` received --
        the seam quantity every capacity screen consumes. The window runs
        2023-2025 because the screens do not bind in the window's FIRST year
        (``runner.py`` guards the block on ``prior_results is not None``), and
        it straddles the weather year so 2024 is a built-in zero-delta control
        and 2025 carries the gap.
        """
        overrides = dict(
            iso=ISO,
            hindcast=hindcast,
            start_year=2023,
            end_year=2025,
            weather_year=2024,
            eia860_vintage_year=2020,
            datacenter_load_path="off",
        )
        if crossover_forward_year is not None:
            overrides["crossover_forward_year"] = crossover_forward_year
        config = ScenarioConfig(**overrides)
        # THE FLAG IS SET ON THE RESOLVED CONFIG, DELIBERATELY (capx D76-ARM-B /
        # owner ruling Q58). Half 2 of the arm coerces the field to its frozen
        # declaration whenever ``not self.hindcast``, so passing ``armed`` to the
        # constructor would silently drop it on the ``hindcast=False`` arm and
        # turn the forecast inertness test below into a tautology -- both arms
        # unarmed, equal for a reason that has nothing to do with the seam.
        # Assigning afterwards bypasses ``__post_init__`` (the dataclass is not
        # frozen), so what is compared is the RUNNER'S OWN BRANCH with the flag
        # genuinely on, which is the claim worth making: the seam is inert where
        # there is no measured load even if the flag reaches it. The coercion is
        # asserted separately and on its own terms by TestNonHindcastCoercion.
        config.capacity_screen_peak_measured_hindcast = armed

        captured, loaded = {}, []
        original = runner.evolve_fleet

        def spy(fleet, prior_results, year, config, loss_tracker, **kw):
            captured[year] = kw.get("peak_demand_next")
            return original(fleet, prior_results, year, config, loss_tracker, **kw)

        def counting_loader(iso, year, iso_config, **kwargs):
            loaded.append(year)
            return _stub_demand(iso, year, iso_config, **kwargs)

        with (
            patch.object(runner, "load_demand", side_effect=counting_loader),
            patch.object(pipeline_solve, "DispatchModel", _FakeDispatchModel),
            patch.object(pipeline_solve, "solve_dispatch", side_effect=_fake_solve),
            patch.object(
                pipeline_commitment, "solve_dispatch", side_effect=_fake_solve
            ),
            patch.object(runner, "evolve_fleet", side_effect=spy),
        ):
            runner.run_scenario_iso(config, ISO)
        return captured, loaded


class TestHindcastMeasuredDemandHelper(unittest.TestCase):
    """The ONE construction of a hindcast year's measured load (rule 19)."""

    def test_forwards_the_loader_options_and_truncates_to_config_hours(self):
        iso_config = get_iso_config(ISO)
        config = ScenarioConfig(iso=ISO, hours=24, td_loss_factor=0.03)
        seen = {}

        def loader(iso, year, cfg, **kwargs):
            seen.update(iso=iso, year=year, **kwargs)
            return np.ones((len(cfg.zone_names), HOURS))

        with patch.object(runner, "load_demand", side_effect=loader):
            out = runner._hindcast_measured_demand(config, ISO, iso_config, 2023, [])

        self.assertEqual(seen["year"], 2023)
        self.assertEqual(seen["td_loss_factor"], 0.03)
        # An empty import fleet means no import NODE, so interchange is folded
        # into zonal demand -- the LP branch's own convention.
        self.assertTrue(seen["include_interchange"])
        self.assertEqual(out.shape[1], 24)

    def test_import_node_iso_excludes_interchange(self):
        iso_config = get_iso_config(ISO)
        config = ScenarioConfig(iso=ISO)
        seen = {}

        def loader(iso, year, cfg, **kwargs):
            seen.update(kwargs)
            return np.ones((len(cfg.zone_names), HOURS))

        with patch.object(runner, "load_demand", side_effect=loader):
            runner._hindcast_measured_demand(
                config, ISO, iso_config, 2023, ["an-import-unit"]
            )
        self.assertFalse(seen["include_interchange"])


class TestSeamPeakArmed(_SeamCase):
    """Armed, the screens test the year's own measured peak."""

    def test_armed_hindcast_screens_see_the_measured_peak(self):
        peaks, _ = self.run_seam(armed=True)
        for year in (2024, 2025):
            with self.subTest(year=year):
                self.assertAlmostEqual(peaks[year], PEAK_BY_YEAR[year], places=6)

    def test_unarmed_hindcast_screens_see_the_GROWN_weather_peak(self):
        """The pre-gate behaviour, pinned so the repair cannot be silent."""
        peaks, _ = self.run_seam(armed=False)
        config = ScenarioConfig(iso=ISO, weather_year=2024, datacenter_load_path="off")
        base = np.full((1, HOURS), PEAK_BY_YEAR[2024])
        expected = float(runner._scale_demand(base, config, 2025).sum(axis=0).max())
        self.assertAlmostEqual(peaks[2025], expected, places=6)
        # ... and that is NOT the load the same year's LP dispatches.
        self.assertNotAlmostEqual(peaks[2025], PEAK_BY_YEAR[2025], places=3)
        # The weather year is the one year the two paths agree by construction,
        # which is the probe's own faithfulness check.
        self.assertAlmostEqual(peaks[2024], PEAK_BY_YEAR[2024], places=6)

    def test_arming_adds_no_demand_read(self):
        """The screens and the LP share ONE array (rule 19), not two reads.

        The contract is stated as an equality against the unarmed run rather
        than as "once per year": the runner already reads the weather-year base
        in its preamble and reads again on the results path, so the absolute
        count is not 1 and never was. What must hold -- and what would break if
        the seam re-loaded instead of reusing -- is that arming adds NOTHING.
        """
        _, armed_loads = self.run_seam(armed=True)
        _, off_loads = self.run_seam(armed=False)
        self.assertEqual(sorted(armed_loads), sorted(off_loads))


class TestSeamPeakInertWhereThereIsNoMeasuredLoad(_SeamCase):
    """Forecast years keep the growth path -- rule 13's forward test."""

    def test_forecast_run_is_byte_identical_armed_and_unarmed(self):
        armed, _ = self.run_seam(armed=True, hindcast=False)
        off, _ = self.run_seam(armed=False, hindcast=False)
        self.assertEqual(armed, off)

    def test_crossover_forward_year_keeps_the_growth_path(self):
        """A year at/after the boundary has no measured load to read."""
        armed, _ = self.run_seam(armed=True, crossover_forward_year=2025)
        off, _ = self.run_seam(armed=False, crossover_forward_year=2025)
        self.assertEqual(armed[2025], off[2025])
        self.assertNotAlmostEqual(armed[2025], PEAK_BY_YEAR[2025], places=3)
        # ... and the boundary, not the gate, is what turned it off: the arm
        # still takes the measured branch in the PRE-boundary year. (2024 is the
        # weather year, where the two paths agree by construction, so it cannot
        # discriminate -- only the forward year above can, which is the point.)
        self.assertAlmostEqual(armed[2024], PEAK_BY_YEAR[2024], places=6)
        # The un-bounded arm DOES move 2025, which is what makes the equality
        # above a real inertness claim rather than a vacuous one.
        unbounded, _ = self.run_seam(armed=True)
        self.assertAlmostEqual(unbounded[2025], PEAK_BY_YEAR[2025], places=6)


class TestCacheKeyRegistration(unittest.TestCase):
    """Unarmed keys byte-stable in all six ISOs; an armed run keys distinctly."""

    ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM")

    def _key(self, iso, **over):
        return apply_iso_scenario_defaults(
            ScenarioConfig(
                iso=iso, hindcast=True, start_year=2021, end_year=2025, **over
            ),
            iso,
        ).cache_key()

    def test_bare_hindcast_key_is_the_ARMED_key_and_explicit_off_moves_it(self):
        """The POST-flip invariant (capx D76-ARM-B / owner ruling Q58).

        Before the arm this read ``bare == off`` and ``bare != on``. The flip
        inverts it, and the inversion is the whole point of the (b'-1) route:
        the bare hindcast recipe now resolves the ARMED default, so it takes the
        armed key -- which is what stops a post-flip armed run being served the
        pre-flip unarmed bundle -- while an EXPLICIT ``False`` still equals the
        frozen declaration, is dropped from the hash, and therefore keeps the
        PRE-flip key and its bundle. That second half is not a formality: one
        committed artifact already exercises it
        (``results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm``).
        """
        for iso in self.ISOS:
            with self.subTest(iso=iso):
                bare = self._key(iso)
                off = self._key(iso, capacity_screen_peak_measured_hindcast=False)
                on = self._key(iso, capacity_screen_peak_measured_hindcast=True)
                self.assertEqual(on, bare)
                self.assertNotEqual(off, bare)

    def test_non_hindcast_forecast_key_is_untouched(self):
        """Half 2's own key claim: a forecast run the gate cannot reach.

        The backcast case below was true before the arm and stays true; THIS one
        is true only because of the ``__post_init__`` coercion, and it is the
        assertion that keeps 83 committed forecast configs from re-keying for
        byte-identical behaviour.
        """
        for iso in self.ISOS:
            with self.subTest(iso=iso):
                base = apply_iso_scenario_defaults(
                    ScenarioConfig(iso=iso, hindcast=False), iso
                )
                off = base.with_overrides(capacity_screen_peak_measured_hindcast=False)
                self.assertEqual(off.cache_key(), base.cache_key())

    def test_backcast_key_is_untouched(self):
        """A backcast runs no capacity evolution; its key must not move."""
        for iso in self.ISOS:
            with self.subTest(iso=iso):
                base = apply_iso_scenario_defaults(
                    ScenarioConfig(iso=iso, mode="backcast"), iso
                )
                off = base.with_overrides(capacity_screen_peak_measured_hindcast=False)
                self.assertEqual(off.cache_key(), base.cache_key())


class TestNonHindcastCoercion(unittest.TestCase):
    """Half 2 of the arm (capx D76-ARM-B / owner ruling Q58), on its own terms.

    The gate's runtime branch is ``config.hindcast and not
    config.is_crossover_forward_year(year)``, so a run with no measured load to
    read is inert for its WHOLE horizon. ``__post_init__`` makes that structural:
    on any non-hindcast config the field is forced back to its FROZEN
    declaration -- not to the dataclass default, which after the flip is the
    ARMED value and would make the coercion a no-op.
    """

    ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM", "SPP", "NWPP", "SOCO")

    def test_the_dataclass_default_is_armed(self):
        """The flip itself, read off the field rather than a resolved instance."""
        self.assertIs(
            ScenarioConfig.__dataclass_fields__[
                "capacity_screen_peak_measured_hindcast"
            ].default,
            True,
        )

    def test_coerced_off_on_every_non_hindcast_config(self):
        for iso in self.ISOS:
            for mode in ("forecast", "backcast"):
                with self.subTest(iso=iso, mode=mode):
                    cfg = apply_iso_scenario_defaults(
                        ScenarioConfig(iso=iso, mode=mode, hindcast=False), iso
                    )
                    self.assertFalse(cfg.capacity_screen_peak_measured_hindcast)

    def test_an_explicit_true_does_not_survive_a_non_hindcast_config(self):
        """The coercion is unconditional, not a default-only fallback."""
        cfg = ScenarioConfig(
            iso="ERCOT",
            hindcast=False,
            capacity_screen_peak_measured_hindcast=True,
        )
        self.assertFalse(cfg.capacity_screen_peak_measured_hindcast)

    def test_a_hindcast_config_keeps_both_values(self):
        """The coercion must not reach the runs the gate governs."""
        for iso in self.ISOS:
            with self.subTest(iso=iso):
                armed = ScenarioConfig(iso=iso, hindcast=True)
                self.assertTrue(armed.capacity_screen_peak_measured_hindcast)
                off = ScenarioConfig(
                    iso=iso,
                    hindcast=True,
                    capacity_screen_peak_measured_hindcast=False,
                )
                self.assertFalse(off.capacity_screen_peak_measured_hindcast)

    def test_the_coercion_target_is_the_frozen_declaration(self):
        """Rule 24: the coerced value tracks the ledger, not a literal.

        If the frozen declaration ever moved, the coercion would move with it --
        which is the property that makes ``__post_init__`` and ``cache_key``
        agree on what "unarmed" means, and therefore the property that makes the
        non-hindcast keys stable.
        """
        self.assertEqual(
            _CAPACITY_SCREEN_PEAK_FROZEN_DECLARATION,
            cache_key_drop_defaults()["capacity_screen_peak_measured_hindcast"],
        )


if __name__ == "__main__":
    unittest.main()
