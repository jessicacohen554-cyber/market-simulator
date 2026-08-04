"""Tests for the T1-FF full-forward hindcast instrument (FH-1).

Trivial-first, no LP solve — the full-forward *contract* is verified at each
seam (``docs/hindcast-forward-plan-2026-07.md`` §2, §4 rows 2/7/11/12, §5):

* the config predicate (``ScenarioConfig.is_full_forward_hindcast``), the Arm R
  weather-posture field's validation, the relaxed forward-gas validation, and
  cache-key byte-stability at the defaults;
* the harness (``--forward-from-base`` window rules, arm wiring, the as-known
  intake hard error, the holdout-policy parity);
* the four FH-1 leak closures — planned-additions vintage bound, emission-rate
  as-of window + T1-FF quarantine trim, hydro climatology as-of trim, and the
  §4-row-7 gas back-hold trap;
* the generalized ``assert_forward_drivers`` guard covering EVERY solve year;
* the scorer's symmetric ``< 2023`` refusal (rule 22 both bounds).
"""

from __future__ import annotations

import unittest

import pandas as pd
import pytest

from market_sim import runner
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.emission_rates import (
    QUARANTINE_RATE_BASIS_FROM,
    QUARANTINED_RATE_BASIS_YEARS,
    measured_plant_rates,
)
from market_sim.data.fleet import EIA860_OPERABLE_VINTAGE, operable_vintage_year
from market_sim.data.fuel import resolve_annual_gas_price
from market_sim.data.hydro import full_forward_climatology_years
from scripts import run_capacity_hindcast as H
from scripts import run_calibration_full as RCF
from scripts.lib import holdout_policy


def _t1ff_config(**overrides) -> ScenarioConfig:
    """A minimal ERCOT full-forward config (base 2023, Arm R)."""
    base = ScenarioConfig(
        iso="ERCOT",
        mode="forecast",
        hindcast=True,
        start_year=2023,
        end_year=2025,
        eia860_vintage_year=2023,
        gas_price_path="hindcast_realized",
        crossover_forward_year=2023,
        crossover_forward_gas_path="hindcast_realized",
        crossover_solve_year_weather=True,
        weather_year=2023,
    )
    return base.with_overrides(**overrides) if overrides else base


# --------------------------------------------------------------------------- #
# Config predicate + validation + cache-key stability
# --------------------------------------------------------------------------- #
class TestFullForwardConfig(unittest.TestCase):
    def test_predicate_boundary_at_start(self):
        c = _t1ff_config()
        self.assertTrue(c.is_full_forward_hindcast)
        for y in (2023, 2024, 2025):
            self.assertTrue(c.is_crossover_forward_year(y))

    def test_predicate_false_for_crossover_and_plain(self):
        x = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2023,
            end_year=2027,
            crossover_forward_year=2026,
        )
        self.assertFalse(x.is_full_forward_hindcast)
        plain = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
        self.assertFalse(plain.is_full_forward_hindcast)
        self.assertFalse(ScenarioConfig().is_full_forward_hindcast)

    def test_solve_year_weather_requires_full_forward(self):
        with pytest.raises(ValueError, match="full-forward"):
            ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                hindcast=True,
                start_year=2023,
                end_year=2027,
                crossover_forward_year=2026,
                crossover_solve_year_weather=True,
            )

    def test_hindcast_gas_path_full_forward_only(self):
        # Full-forward: hindcast_* forward gas is legal.
        self.assertEqual(_t1ff_config().crossover_forward_gas_path, "hindcast_realized")
        # Plain crossover: still AEO-only (byte-identical contract).
        with pytest.raises(ValueError, match="AEO path"):
            ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                hindcast=True,
                start_year=2023,
                end_year=2027,
                crossover_forward_year=2026,
                crossover_forward_gas_path="hindcast_realized",
            )

    def test_cache_key_neutral_at_default_distinct_when_armed(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
        explicit = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            crossover_solve_year_weather=False,
        )
        self.assertEqual(base.cache_key(), explicit.cache_key())
        armed = _t1ff_config()
        off = _t1ff_config(crossover_solve_year_weather=False)
        self.assertNotEqual(armed.cache_key(), off.cache_key())


# --------------------------------------------------------------------------- #
# Harness: window rules, arm wiring, governance parity
# --------------------------------------------------------------------------- #
class TestHarness(unittest.TestCase):
    def test_window_rules(self):
        H._validate_window(2023, 2025, False, True)  # Phase A
        H._validate_window(2021, 2025, False, True)  # Phase B (2022 bridged)
        with pytest.raises(SystemExit):
            H._validate_window(2023, 2026, False, True)  # end past 2025
        with pytest.raises(SystemExit):
            H._validate_window(2020, 2025, False, True)  # below demand floor
        with pytest.raises(SystemExit):
            H._validate_window(2023, 2027, True, True)  # both modes at once

    def test_build_config_arm_r(self):
        c = H.build_config(
            "ERCOT",
            2023,
            2025,
            "realized",
            vintage=2023,
            forward_from_base=True,
            arm="realized",
        )
        self.assertTrue(c.is_full_forward_hindcast)
        self.assertEqual(c.crossover_forward_year, 2023)
        self.assertEqual(c.gas_price_path, "hindcast_realized")
        self.assertEqual(c.crossover_forward_gas_path, "hindcast_realized")
        self.assertEqual(c.weather_year, 2023)
        self.assertTrue(c.crossover_solve_year_weather)
        self.assertEqual(c.hindcast_fuel_variant, "realized")

    def test_build_config_arm_k_base_2021(self):
        c = H.build_config(
            "ERCOT",
            2021,
            2025,
            "realized",
            vintage=2020,
            forward_from_base=True,
            arm="asknown",
        )
        self.assertEqual(c.gas_price_path, "hindcast_asknown_aeo2021")
        self.assertEqual(c.crossover_forward_gas_path, "hindcast_asknown_aeo2021")
        self.assertEqual(c.weather_year, 2021)
        self.assertFalse(c.crossover_solve_year_weather)

    def test_arm_k_base_2023_intake_landed(self):
        # FH-3 landed the AEO2023 Reference vintage, so Arm K at base 2023
        # resolves instead of refusing (this is what unblocked Phase A's Arm K).
        self.assertEqual(
            H.full_forward_gas_path("asknown", 2023), "hindcast_asknown_aeo2023"
        )

    def test_arm_k_missing_intake_hard_errors(self):
        # The refusal itself must survive the intake: a base year whose AEO
        # vintage has NOT been intaken still hard-errors rather than falling
        # back to a different-vintage path (rule 13). 2022 is such a base — no
        # hindcast solves it (rule-22 bridge), so no AEO2022 path exists.
        with pytest.raises(SystemExit, match="hindcast_asknown_aeo2022"):
            H.full_forward_gas_path("asknown", 2022)

    def test_policy_parity(self):
        self.assertEqual(
            holdout_policy.HINDCAST_BRIDGE_YEARS, runner.HINDCAST_BRIDGE_YEARS
        )
        self.assertEqual(H.ALLOWED_SOLVE_YEARS, holdout_policy.HINDCAST_SOLVE_YEARS)
        self.assertEqual(
            holdout_policy.HINDCAST_SOLVE_YEARS,
            holdout_policy.CALIBRATION_YEARS | holdout_policy.HINDCAST_SEED_YEARS,
        )
        self.assertEqual(holdout_policy.FREEZE_FILE, RCF.HOLDOUT_FREEZE_FILE)
        # The emission-rate quarantine trim mirrors the bridge set.
        self.assertEqual(
            QUARANTINED_RATE_BASIS_YEARS | {QUARANTINE_RATE_BASIS_FROM},
            holdout_policy.HINDCAST_BRIDGE_YEARS,
        )

    def test_policy_fails_closed(self):
        v = holdout_policy.hindcast_solve_year_violations([2020, 2022, 2023])
        self.assertEqual(len(v), 2)  # 2020 + 2022 refused, 2023 fine
        self.assertTrue(any("2020" in s for s in v))
        self.assertTrue(any("2022" in s for s in v))


# --------------------------------------------------------------------------- #
# Leak 2: vintage-derived operable bound (plan §4 row 2)
# --------------------------------------------------------------------------- #
class TestOperableVintage(unittest.TestCase):
    def test_vintage_dir_maps_to_its_year(self):
        self.assertEqual(operable_vintage_year("data/raw/eia-860/vintage_2021"), 2021)
        self.assertEqual(operable_vintage_year("data/raw/eia-860/vintage_2023"), 2023)

    def test_top_level_maps_to_constant(self):
        self.assertEqual(
            operable_vintage_year("data/raw/eia-860"), EIA860_OPERABLE_VINTAGE
        )


# --------------------------------------------------------------------------- #
# Leak 12: emission-rate as-of window + quarantine trim (plan §4 row 12)
# --------------------------------------------------------------------------- #
class TestEmissionRateWindow(unittest.TestCase):
    def _v2(self) -> pd.DataFrame:
        rows = []
        for y in range(2019, 2027):
            rows.append(
                {
                    "iso": "PJM",
                    "year": y,
                    "plant_id": 1,
                    "primary_fuel": "gas",
                    # Rate encodes the year so the selected basis is readable
                    # off the result: mean over selected (400 + y - 2019).
                    "co2_kg": float(400 + y - 2019),
                    "net_mwh": 1.0,
                }
            )
        return pd.DataFrame(rows)

    def _basis_sum(self, target, **kw) -> float:
        r = measured_plant_rates(self._v2(), "PJM", target, "forecast", window=3, **kw)
        return round(r[(1, "gas")] * 1000 * 3 - 3 * 400, 6)

    def test_forecast_lane_unbounded_is_unchanged(self):
        # as_of None (the plain forecast lane): last-3-in-artifact basis
        # {2024, 2025, 2026} regardless of target — byte-identical to pre-FH-1.
        self.assertEqual(self._basis_sum(2024), 5 + 6 + 7)

    def test_as_of_bound(self):
        # Hindcast lane, target 2023: basis {2021, 2022, 2023}.
        self.assertEqual(self._basis_sum(2023, as_of_year=2023), 2 + 3 + 4)

    def test_t1ff_quarantine_trim(self):
        # T1-FF: 2022 leaves the basis -> {2020, 2021, 2023}; asserting no
        # quarantined year can enter (2026 is excluded by the same trim).
        self.assertEqual(
            self._basis_sum(2023, as_of_year=2023, exclude_quarantined=True),
            1 + 2 + 4,
        )

    def test_backcast_branch_untouched(self):
        r = measured_plant_rates(self._v2(), "PJM", 2023, "backcast")
        self.assertAlmostEqual(r[(1, "gas")] * 1000, 404.0)


# --------------------------------------------------------------------------- #
# Leak 11: hydro climatology as-of trim (plan §4 row 11)
# --------------------------------------------------------------------------- #
class TestHydroClimatology(unittest.TestCase):
    def test_base_2023_window(self):
        self.assertEqual(full_forward_climatology_years(2023), (2021, 2023))

    def test_base_2021_window_is_thin_not_widened(self):
        # A single water year — the disclosed Phase-B thinness finding; the
        # window regenerates from the as-of date, it is never widened by hand.
        self.assertEqual(full_forward_climatology_years(2021), (2021,))

    def test_2022_never_enters(self):
        for base in (2022, 2023, 2024, 2025):
            self.assertNotIn(2022, full_forward_climatology_years(base))


# --------------------------------------------------------------------------- #
# Leak 7 guard: gas back-hold trap (plan §4 row 7)
# --------------------------------------------------------------------------- #
class TestGasBackHoldTrap(unittest.TestCase):
    def test_full_forward_below_earliest_knot_raises(self):
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
            crossover_forward_gas_path="mid",  # knots start 2023
        )
        with pytest.raises(ValueError, match="back-hold"):
            resolve_annual_gas_price(c, 2021)

    def test_full_forward_covered_trajectory_resolves(self):
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
        )
        self.assertGreater(resolve_annual_gas_price(c, 2021), 0.0)

    def test_plain_crossover_unaffected(self):
        x = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            start_year=2023,
            end_year=2027,
            gas_price_path="hindcast_realized",
            crossover_forward_year=2026,
        )
        self.assertGreater(resolve_annual_gas_price(x, 2026), 0.0)


# --------------------------------------------------------------------------- #
# Generalized forward-driver guard
# --------------------------------------------------------------------------- #
class TestAssertForwardDrivers(unittest.TestCase):
    def test_t1ff_arm_r_clean(self):
        c = H.build_config(
            "ERCOT",
            2023,
            2025,
            "realized",
            vintage=2023,
            forward_from_base=True,
            arm="realized",
        )
        self.assertEqual(H.assert_forward_drivers(c, 2023, 2025), [])

    def test_t1ff_base_2021_bridge_skipped_and_clean(self):
        c = H.build_config(
            "ERCOT",
            2021,
            2025,
            "realized",
            vintage=2020,
            forward_from_base=True,
            arm="realized",
        )
        self.assertEqual(H.assert_forward_drivers(c, 2021, 2025), [])

    def test_back_hold_surfaces_as_violation(self):
        # A hand-built full-forward config on an AEO path that cannot cover
        # its window: the guard reports the trap instead of crashing.
        c = _t1ff_config(
            start_year=2021,
            end_year=2025,
            crossover_forward_year=2021,
            weather_year=2021,
            eia860_vintage_year=2020,
            gas_price_path="mid",
            crossover_forward_gas_path="mid",
            crossover_solve_year_weather=False,
        )
        v = H.assert_forward_drivers(c, 2021, 2025)
        self.assertTrue(any("back-hold" in s for s in v), v)

    def test_plain_hindcast_noop(self):
        c = H.build_config("ERCOT", 2021, 2025, "realized")
        self.assertEqual(H.assert_forward_drivers(c, 2021, 2025), [])


# --------------------------------------------------------------------------- #
# Scorer: symmetric lower bound (rule 22 both sides)
# --------------------------------------------------------------------------- #
class TestScorerBounds(unittest.TestCase):
    def test_lower_and_upper_refusals(self):
        from scripts import score_crossover as SC

        for y in (2019, 2021, 2022):
            with pytest.raises(ValueError, match="below the scoring window"):
                SC._assert_scoreable_year(y)
        for y in (2026, 2027):
            with pytest.raises(ValueError, match="quarantined"):
                SC._assert_scoreable_year(y)
        for y in (2023, 2024, 2025):
            self.assertEqual(SC._assert_scoreable_year(y), y)


# --------------------------------------------------------------------------- #
# FFR-3U: the bridge/un-bridge seam (owner decision D-11, sitting Addendum L)
#
# FFR-3Q's base-2021 T1-FF window SOLVED 2022 — a validation-tier holdout year —
# under an active freeze, because two predicates disagreed about what a
# "forward year" is: the runner un-bridged any year at/above
# ``crossover_forward_year`` (which T1-FF points at its OWN base year), while
# the guard computed its solve set from the ``--crossover`` CLI flag and so
# never policy-checked the year at all. These tests are the ones that would
# have caught it before the solve.
# --------------------------------------------------------------------------- #
class TestBridgeSeam(unittest.TestCase):
    """The FFR-3U seam: one predicate, checked at every posture."""

    # -- (a) the instance: base 2021 must BRIDGE 2022 -------------------- #
    def test_base_2021_bridges_2022(self):
        c = H.build_config(
            "ERCOT", 2021, 2025, "realized", vintage=2020, forward_from_base=True
        )
        self.assertEqual(c.crossover_forward_year, 2021)  # the T1-FF pointing
        # The runner's predicate, at the boundary the config actually carries.
        self.assertTrue(
            runner.is_hindcast_bridge_year(
                2022,
                hindcast=c.hindcast,
                crossover_forward_year=c.crossover_forward_year,
                start_year=c.start_year,
            )
        )
        self.assertFalse(c.is_crossover_unbridged_year(2022))
        # ... and the realized solve set excludes it.
        self.assertNotIn(
            2022,
            runner.hindcast_solve_years(
                2021, 2025, crossover_forward_year=c.crossover_forward_year
            ),
        )
        self.assertEqual(
            runner.hindcast_solve_years(
                2021, 2025, crossover_forward_year=c.crossover_forward_year
            ),
            [2021, 2023, 2024, 2025],
        )

    def test_forward_stack_and_bridge_legality_are_different_questions(self):
        """The separation the defect collapsed (and why the clause is scoped).

        2022 IS a forward year for its *drivers* on a base-2021 T1-FF run (no
        measured overlays, growth-scaled demand) and is STILL a quarantined
        bridge year for rule 22. One predicate answering both is the bug.
        """
        c = H.build_config(
            "ERCOT", 2021, 2025, "realized", vintage=2020, forward_from_base=True
        )
        self.assertTrue(c.is_crossover_forward_year(2022))  # input stack
        self.assertFalse(c.is_crossover_unbridged_year(2022))  # rule-22 legality

    # -- (c) the 2026 analogue: locked-test tier ------------------------- #
    def test_base_2021_bridges_2026(self):
        """The exposure nothing has reached yet — closed at the predicate."""
        c = H.build_config(
            "ERCOT", 2021, 2025, "realized", vintage=2020, forward_from_base=True
        )
        self.assertFalse(c.is_crossover_unbridged_year(2026))
        self.assertTrue(
            runner.is_hindcast_bridge_year(
                2026,
                hindcast=True,
                crossover_forward_year=c.crossover_forward_year,
                start_year=c.start_year,
            )
        )
        # And the window guard still refuses to be pointed at it at all.
        with pytest.raises(SystemExit):
            H._validate_window(2021, 2026, False, True)

    def test_genuine_crossover_still_unbridges_2026(self):
        """The clause is SCOPED, not deleted: T1-X is unchanged."""
        c = H.build_config("ERCOT", 2023, 2027, "realized", crossover=True)
        self.assertEqual(c.crossover_forward_year, 2026)
        self.assertTrue(c.is_crossover_unbridged_year(2026))
        self.assertTrue(c.is_crossover_unbridged_year(2027))
        self.assertEqual(
            runner.hindcast_solve_years(
                2023, 2027, crossover_forward_year=c.crossover_forward_year
            ),
            [2023, 2024, 2025, 2026, 2027],
        )

    def test_plain_hindcast_unchanged(self):
        c = H.build_config("ERCOT", 2021, 2025, "realized")
        self.assertIsNone(c.crossover_forward_year)
        self.assertFalse(c.is_crossover_unbridged_year(2022))
        self.assertEqual(
            runner.hindcast_solve_years(2021, 2025, crossover_forward_year=None),
            [2021, 2023, 2024, 2025],
        )

    # -- (b) the CLASS-level test: guard set == realized set ------------- #
    def test_guard_and_runner_agree_on_every_posture(self):
        """PARITY — the whole family, not this instance.

        For every CLI posture the harness accepts, the set ``_validate_window``
        policy-checks must equal the set the runner will realize. The runner's
        set is rebuilt here from the config ``build_config`` actually produces
        — CLI args -> config -> runner predicate — so re-pointing the boundary,
        or re-deriving either side from a different flag, breaks this test
        rather than a holdout year.
        """
        postures = [
            # (start, end, crossover, forward_from_base, vintage)
            (2021, 2025, False, False, None),  # plain T1-H
            (2023, 2025, False, False, None),  # plain, short
            (2021, 2025, False, True, 2020),  # T1-FF base 2021 (the breach)
            (2023, 2025, False, True, 2023),  # T1-FF base 2023
            (2024, 2025, False, True, 2023),  # T1-FF base 2024
            (2023, 2027, True, False, 2023),  # T1-X crossover
            (2023, 2026, True, False, 2023),  # T1-X, short
        ]
        for start, end, crossover, ffb, vintage in postures:
            with self.subTest(start=start, end=end, crossover=crossover, ffb=ffb):
                H._validate_window(start, end, crossover, ffb)  # legal, no raise
                guard = H.window_solve_years(start, end, crossover, ffb)
                cfg = H.build_config(
                    "ERCOT",
                    start,
                    end,
                    "realized",
                    vintage=vintage,
                    crossover=crossover,
                    forward_from_base=ffb,
                    arm="realized" if ffb else "realized",
                )
                realized = [
                    y
                    for y in range(start, end + 1)
                    if not runner.is_hindcast_bridge_year(
                        y,
                        hindcast=cfg.hindcast,
                        crossover_forward_year=cfg.crossover_forward_year,
                        start_year=cfg.start_year,
                    )
                ]
                self.assertEqual(guard, realized)
                # A quarantined year may survive into the solve set ONLY as a
                # genuine crossover forward year (2026 on a T1-X); 2022 never.
                for y in realized:
                    if y in runner.HINDCAST_BRIDGE_YEARS:
                        self.assertTrue(crossover, f"{y} solved on a non-crossover")
                        self.assertGreaterEqual(y, H.CROSSOVER_FORWARD_YEAR)

    def test_guard_checks_the_boundary_the_config_carries(self):
        """The exact gap FFR-3Q fell through: guard flag vs config boundary."""
        for start, end, crossover, ffb, vintage in [
            (2021, 2025, False, True, 2020),
            (2023, 2025, False, True, 2023),
            (2023, 2027, True, False, 2023),
            (2021, 2025, False, False, None),
        ]:
            with self.subTest(start=start, crossover=crossover, ffb=ffb):
                cfg = H.build_config(
                    "ERCOT",
                    start,
                    end,
                    "realized",
                    vintage=vintage,
                    crossover=crossover,
                    forward_from_base=ffb,
                    arm="realized",
                )
                self.assertEqual(
                    H.window_forward_boundary(start, crossover, ffb),
                    cfg.crossover_forward_year,
                )

    # -- (4) the banner cannot lie -------------------------------------- #
    def test_banner_and_completion_assertion_share_the_predicate(self):
        """Source-level: the launch promise and the completion check are tied.

        The FFR-3Q run printed a governance banner promising 2022 was bridged
        and then solved it, with nothing comparing the two. The banner is now
        derived from ``window_solve_years`` and re-asserted against the
        realized evolution ledgers, so it cannot be true at launch and false at
        completion.
        """
        import inspect

        src = inspect.getsource(H.main)
        self.assertIn("promised_solve_years = window_solve_years(", src)
        self.assertIn("SOLVE-YEAR PARITY FAILURE", src)
        self.assertIn("promised_solve_years", src.split("solved = sorted")[1])

    def test_no_second_predicate_at_either_site(self):
        """Rule 19 ``[R-ONE-MECH]`` applied to the guard itself.

        The runner's bridge branch and the harness guard must both route
        through ``is_hindcast_bridge_year``; neither may re-derive bridging
        from ``is_crossover_forward_year`` (the input-stack predicate) or from
        the ``--crossover`` flag.
        """
        import inspect

        runner_src = inspect.getsource(runner.run_scenario_iso)
        bridge_stmt = runner_src.split("is_bridge = ")[1].split("\n\n")[0]
        self.assertIn("is_hindcast_bridge_year(", bridge_stmt)
        self.assertNotIn("is_crossover_forward_year", bridge_stmt)

        guard_src = inspect.getsource(H._validate_window)
        self.assertIn("window_solve_years(", guard_src)
        # The guard must not rebuild a solve set from the CLI flag.
        self.assertNotIn("for y in range(start_year, end_year + 1)", guard_src)

    def test_boundary_constant_is_single_sourced(self):
        from market_sim.config import scenarios as S

        self.assertEqual(H.CROSSOVER_FORWARD_YEAR, S.CROSSOVER_FORWARD_BOUNDARY_YEAR)

    # -- D-11 condition 2: the contaminated keys are uncacheable --------- #
    def test_contaminated_cache_keys_refuse_a_present_bundle(self):
        """The condition that actually protects the tier (owner D-11(b)).

        The seam fix moves no cache key, so the config that solved 2022 still
        hashes to FFR-3Q's two keys. A bundle sitting at one of them must be a
        hard error rather than a silent cache hit; an absent bundle stays a
        no-op so the eventual re-probe can re-solve on a clean tree.
        """
        import tempfile

        from market_sim.results import cache as cachemod

        self.assertEqual(
            set(cachemod.CONTAMINATED_CACHE_KEYS),
            {"b99600bceb8cb6b8", "5c352508039513da"},
        )
        with tempfile.TemporaryDirectory() as tmp:
            with cachemod.cache_root(tmp):
                for key in cachemod.CONTAMINATED_CACHE_KEYS:
                    # Absent bundle: no-op, so a clean re-solve is unaffected.
                    cachemod.assert_cache_key_uncontaminated("ERCOT", key)
                    self.assertFalse(cachemod.is_cached("ERCOT", key, 2022))
                    # Present bundle: refused at the single path seam, so every
                    # read AND write is refused with it.
                    (cachemod.CACHE_ROOT / "ERCOT" / key).mkdir(parents=True)
                    with pytest.raises(RuntimeError, match="QUARANTINED"):
                        cachemod.get_cache_path("ERCOT", key, 2022)
                    with pytest.raises(RuntimeError, match="QUARANTINED"):
                        cachemod.is_cached("ERCOT", key, 2022)
                # An uncontaminated key is untouched.
                (cachemod.CACHE_ROOT / "ERCOT" / "603c2498bf71d21d").mkdir(parents=True)
                self.assertFalse(cachemod.is_cached("ERCOT", "603c2498bf71d21d", 2023))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(unittest.main())
