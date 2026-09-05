"""Tests for the shared per-year phase-timing line (``pipeline/timing.py``).

The line is a **parsed wire format**: ``docs/handoffs/wallclock-baseline-2026-07.md``
and every before/after wall-clock capture read
``data_prep / solve_p0 / markup / solve_p1 / results_write / total`` out of it.
Both orchestrators (``runner.run_scenario_iso`` and
``scripts/run_calibration_full.py::solve_and_persist``) now emit it through this
one helper, so what these tests pin is that the six frozen fields keep their
exact spelling, order and position — and that the ``results_write``
sub-instrumentation is strictly *additive* (a trailing clause that a parser of
the six fields never sees).
"""

from __future__ import annotations

import logging
import re
import unittest

from market_sim.pipeline.timing import (
    format_phase_parts,
    format_results_write_parts,
    log_year_cached_timing,
    log_year_phase_timing,
)
from tests.helpers import REPO_ROOT

# The frozen six-field prefix, as a wall-clock capture parses it.
FROZEN_RE = re.compile(
    r"year (\d+) phase timing: data_prep=([\d.]+)s solve_p0=([\d.]+)s "
    r"markup=([\d.]+)s solve_p1=([\d.]+)s results_write=([\d.]+)s "
    r"total=([\d.]+)s"
)

# The 2023 ERCOT row of the baseline doc, so the assertion is against a real
# recorded line rather than an invented one.
BASELINE_2023 = dict(
    data_prep=53.5,
    solve_p0=174.7,
    markup=5.4,
    solve_p1=25.0,
    results_write=13.1,
    total=271.7,
)


class _CapturingHandler(logging.Handler):
    """Collect formatted records so the emitted text can be asserted on."""

    def __init__(self):
        super().__init__()
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage())


class TimingLineTestBase(unittest.TestCase):
    """Attach a capturing handler to a throwaway logger."""

    def setUp(self):
        self.logger = logging.getLogger(f"test_timing.{self.id()}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.handler = _CapturingHandler()
        self.logger.addHandler(self.handler)
        self.addCleanup(self.logger.removeHandler, self.handler)

    @property
    def message(self) -> str:
        self.assertEqual(len(self.handler.messages), 1)
        return self.handler.messages[0]


class TestFrozenFormat(TimingLineTestBase):
    """The six fields are byte-identical to the pre-helper inline line."""

    def test_no_breakdown_reproduces_the_recorded_line(self):
        log_year_phase_timing(self.logger, 2023, **BASELINE_2023)
        self.assertEqual(
            self.message,
            "year 2023 phase timing: data_prep=53.5s solve_p0=174.7s "
            "markup=5.4s solve_p1=25.0s results_write=13.1s total=271.7s",
        )

    def test_frozen_fields_parse(self):
        log_year_phase_timing(self.logger, 2023, **BASELINE_2023)
        m = FROZEN_RE.match(self.message)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "2023")
        self.assertEqual(m.group(6), "13.1")  # results_write
        self.assertEqual(m.group(7), "271.7")  # total

    def test_cached_line_unchanged(self):
        log_year_cached_timing(self.logger, 2024, total=3.2)
        self.assertEqual(
            self.message,
            "year 2024 phase timing: data_prep=3.2s cached=True total=3.2s",
        )


class TestResultsWriteBreakdown(TimingLineTestBase):
    """The breakdown is additive: it never moves or renames a frozen field."""

    PARTS = {"state": 0.4, "frames": 6.2, "parquet": 4.9, "bench": 1.6}

    def test_frozen_prefix_still_parses_with_breakdown(self):
        log_year_phase_timing(
            self.logger, 2023, **BASELINE_2023, results_write_parts=self.PARTS
        )
        m = FROZEN_RE.match(self.message)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(6), "13.1")
        self.assertEqual(m.group(7), "271.7")

    def test_breakdown_is_a_trailing_clause(self):
        log_year_phase_timing(
            self.logger, 2023, **BASELINE_2023, results_write_parts=self.PARTS
        )
        self.assertTrue(
            self.message.endswith(
                " (results_write: state=0.4s frames=6.2s parquet=4.9s bench=1.6s)"
            )
        )

    def test_prefix_is_identical_with_and_without_parts(self):
        log_year_phase_timing(self.logger, 2023, **BASELINE_2023)
        bare = self.handler.messages[0]
        self.handler.messages.clear()
        log_year_phase_timing(
            self.logger, 2023, **BASELINE_2023, results_write_parts=self.PARTS
        )
        self.assertTrue(self.handler.messages[0].startswith(bare))

    def test_empty_or_missing_parts_emit_no_clause(self):
        self.assertEqual(format_results_write_parts(None), "")
        self.assertEqual(format_results_write_parts({}), "")

    def test_component_order_is_the_callers(self):
        self.assertEqual(
            format_results_write_parts({"b": 2.0, "a": 1.0}),
            " (results_write: b=2.0s a=1.0s)",
        )


class TestMarkupBreakdown(TimingLineTestBase):
    """The ``markup`` clause is additive too, and sits BEFORE ``results_write``.

    ``markup`` is a residual, not a measured phase (``pipeline/solve.py``), so
    its breakdown is the only way to say what the phase actually is. Its clause
    is emitted first so a parser anchored on ``(results_write:`` — or one that
    reads that clause to end-of-line — is unaffected.
    """

    MARKUP_PARTS = {
        "setup": 1.2,
        "p0_build": 96.4,
        "p0_post": 61.0,
        "markup": 5.4,
        "seam": 2.1,
        "p1_post": 58.7,
        "tail": 0.0,
        "other": 0.1,
    }
    WRITE_PARTS = {"state": 0.4, "frames": 6.2, "parquet": 4.9, "bench": 1.6}

    def test_frozen_prefix_still_parses_with_markup_breakdown(self):
        log_year_phase_timing(
            self.logger, 2023, **BASELINE_2023, markup_parts=self.MARKUP_PARTS
        )
        m = FROZEN_RE.match(self.message)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(4), "5.4")  # markup, unmoved
        self.assertEqual(m.group(7), "271.7")  # total

    def test_markup_clause_precedes_results_write_clause(self):
        log_year_phase_timing(
            self.logger,
            2023,
            **BASELINE_2023,
            markup_parts=self.MARKUP_PARTS,
            results_write_parts=self.WRITE_PARTS,
        )
        msg = self.message
        self.assertLess(msg.index("(markup:"), msg.index("(results_write:"))
        # A parser anchored on the results_write clause still reads it whole.
        self.assertTrue(
            msg.endswith(
                " (results_write: state=0.4s frames=6.2s parquet=4.9s bench=1.6s)"
            )
        )

    def test_prefix_is_identical_with_and_without_markup_parts(self):
        log_year_phase_timing(self.logger, 2023, **BASELINE_2023)
        bare = self.handler.messages[0]
        self.handler.messages.clear()
        log_year_phase_timing(
            self.logger, 2023, **BASELINE_2023, markup_parts=self.MARKUP_PARTS
        )
        self.assertTrue(self.handler.messages[0].startswith(bare))

    def test_empty_or_missing_parts_emit_no_clause(self):
        self.assertEqual(format_phase_parts("markup", None), "")
        self.assertEqual(format_phase_parts("markup", {}), "")

    def test_component_order_is_the_callers(self):
        self.assertEqual(
            format_phase_parts("markup", {"b": 2.0, "a": 1.0}),
            " (markup: b=2.0s a=1.0s)",
        )

    def test_results_write_renderer_delegates_to_the_shared_one(self):
        parts = {"state": 0.4}
        self.assertEqual(
            format_results_write_parts(parts),
            format_phase_parts("results_write", parts),
        )


class TestMarkupPartsAreExhaustive(unittest.TestCase):
    """``run_energy_solve``'s components sum to the residual the callers report.

    The residual is ``energy_solve_wall - build_s - r0.solve_time -
    p1.solve_time`` where — since PERF-B session 3 (charter C-2) — ``build_s``
    is EVERY matrix build of the pass, not ``p1.build_time``. That is what
    makes the identity close on every routing: on the warm path the one build
    is the P0 model's; when P1 cold-rebuilds there are two, and under
    ``MARKET_SIM_WARMSTART=0`` the P0 build sits inside the P0 pass instead of
    the setup. This replays the assembly arithmetic on synthetic segment walls
    for all three, so a future edit to the segment boundaries cannot silently
    stop summing — and pins that no ``p0_build`` residual component is needed
    any more (the build it named is now accounted).
    """

    def _parts(self, *, warm: bool, warm_p1: bool):
        """Replay the assembly arithmetic on synthetic segment walls."""
        # Interior wall segments [_t0.._t6] and the two HiGHS run times.
        t = [0.0, 100.0, 260.0, 265.0, 267.0, 430.0, 431.0]
        s0, s1 = 60.0, 55.0
        build_setup = 96.0 if warm else 0.0  # the warm P0 model's build
        build_p0 = 0.0 if warm else 96.0  # the cold P0 model (WARMSTART=0)
        p1_cold = not (warm and warm_p1)
        build_p1 = 94.0 if p1_cold else 0.0  # the second model, cold P1 only
        build_s = build_setup + build_p0 + build_p1
        parts = {
            "setup": (t[1] - t[0]) - build_setup,
            "p0_post": (t[2] - t[1]) - s0 - build_p0,
            "markup": t[3] - t[2],
            "seam": t[4] - t[3],
            "p1_post": (t[5] - t[4]) - s1 - build_p1,
            "tail": t[6] - t[5],
        }
        # What the orchestrator subtracts: EVERY build, both solves.
        residual = (t[6] - t[0]) - build_s - s0 - s1
        return parts, residual, build_s

    def test_sums_to_residual_on_the_warm_p1_path(self):
        parts, residual, build_s = self._parts(warm=True, warm_p1=True)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        self.assertEqual(build_s, 96.0)

    def test_sums_to_residual_on_the_cold_p1_rebuild_path(self):
        parts, residual, build_s = self._parts(warm=True, warm_p1=False)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        # BOTH builds are subtracted — the first is no longer in the residual.
        self.assertEqual(build_s, 96.0 + 94.0)

    def test_sums_to_residual_on_the_two_cold_solves_path(self):
        parts, residual, build_s = self._parts(warm=False, warm_p1=False)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        self.assertEqual(build_s, 96.0 + 94.0)

    def test_solve_module_defines_the_same_component_names(self):
        import inspect

        from market_sim.pipeline import solve as solve_mod

        src = inspect.getsource(solve_mod.run_energy_solve)
        for name in (
            "setup",
            "p0_post",
            "markup",
            "seam",
            "p1_post",
            "tail",
        ):
            self.assertIn(f'"{name}":', src, f"markup_parts lost the {name} component")
        # The unaccounted-build component is retired: the build it named is now
        # inside ``build_s`` and subtracted by both orchestrators (C-2).
        self.assertNotIn('"p0_build":', src)

    def test_result_carries_the_pass_totals(self):
        from dataclasses import fields

        from market_sim.pipeline.solve import EnergySolveResult

        names = {f.name for f in fields(EnergySolveResult)}
        self.assertTrue({"build_s", "solve_p0_s", "solve_p1_s"} <= names)


class TestMultiPassAggregation(unittest.TestCase):
    """A year with more than one energy solve must not lose the earlier passes.

    On an ercot-221 two-pass year (or an ercot-230 fixed point) ``energy_solve_s``
    spans every pass, so the three subtrahends must too. Since PERF-B session 3
    (charter C-2) ``_aggregate_pass_timing`` SUMS ``build_s`` / ``solve_p0_s`` /
    ``solve_p1_s`` over the per-pass log, so every pass's build and both HiGHS
    runs are subtracted and no ``prior_build`` / ``prior_solve`` residual
    component exists; this pins that the identity still closes.
    """

    per_pass = dict(
        build_s=90.0,
        solve_p0_s=260.0,
        solve_p1_s=250.0,
        parts={
            "setup": 1.0,
            "p0_post": 40.0,
            "markup": 0.2,
            "seam": 3.0,
            "p1_post": 38.0,
            "tail": 0.0,
        },
    )

    def _fill_log(self, n_passes: int):
        from market_sim.pipeline import solve as solve_mod

        solve_mod.reset_pass_timing_log()
        for _ in range(n_passes):
            solve_mod._PASS_TIMING_LOG.append(
                {**self.per_pass, "parts": dict(self.per_pass["parts"])}
            )

    def _residual_and_totals(self, n_passes: int):
        """Replay ``_aggregate_pass_timing`` and the caller's residual."""
        from market_sim.pipeline import solve as solve_mod

        self._fill_log(n_passes)
        passes = solve_mod.take_pass_timing_log()
        parts: dict[str, float] = {}
        for entry in passes:
            for name, seconds in entry["parts"].items():
                parts[name] = parts.get(name, 0.0) + seconds
        totals = {
            "build_s": sum(e["build_s"] for e in passes),
            "solve_p0_s": sum(e["solve_p0_s"] for e in passes),
            "solve_p1_s": sum(e["solve_p1_s"] for e in passes),
        }
        # What the orchestrator sees: the whole bracket wall, minus the SUMMED
        # three fields. Interior wall of one pass = its parts + its own
        # build + its two solves (the parts arithmetic, pinned above).
        one_wall = (
            sum(self.per_pass["parts"].values())
            + self.per_pass["build_s"]
            + self.per_pass["solve_p0_s"]
            + self.per_pass["solve_p1_s"]
        )
        bracket = one_wall * n_passes
        residual = (
            bracket - totals["build_s"] - totals["solve_p0_s"] - totals["solve_p1_s"]
        )
        return residual, parts, totals

    def test_single_pass(self):
        residual, parts, totals = self._residual_and_totals(1)
        self.assertNotIn("prior_build", parts)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        self.assertEqual(totals["build_s"], 90.0)

    def test_two_pass_year_is_still_exhaustive(self):
        residual, parts, totals = self._residual_and_totals(2)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        # The extra pass's build and both solves are in the three fields, so
        # the residual is the two passes' interiors and nothing else.
        self.assertAlmostEqual(totals["build_s"], 180.0, places=9)
        self.assertAlmostEqual(totals["solve_p0_s"], 520.0, places=9)
        self.assertAlmostEqual(totals["solve_p1_s"], 500.0, places=9)
        self.assertAlmostEqual(
            residual, 2 * sum(self.per_pass["parts"].values()), places=9
        )

    def test_four_pass_year_is_still_exhaustive(self):
        residual, parts, totals = self._residual_and_totals(4)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)

    def test_the_orchestrator_helper_sums_every_pass(self):
        """The real ``_aggregate_pass_timing`` returns the summed fields."""
        import ast

        from market_sim.pipeline import solve as solve_mod

        spec_path = REPO_ROOT / "scripts" / "run_calibration.py"
        # Importing the 6k-line orchestrator module is heavy; pull the helper's
        # own source out and exec it against the real pass log instead.
        tree = ast.parse(spec_path.read_text())
        fn = next(
            n
            for n in tree.body
            if isinstance(n, ast.FunctionDef) and n.name == "_aggregate_pass_timing"
        )
        ns = {"take_pass_timing_log": solve_mod.take_pass_timing_log}
        exec(compile(ast.Module([fn], type_ignores=[]), str(spec_path), "exec"), ns)
        self._fill_log(3)
        out = ns["_aggregate_pass_timing"](final=None)
        self.assertEqual(out["n_passes"], 3)
        self.assertAlmostEqual(out["build_s"], 270.0, places=9)
        self.assertAlmostEqual(out["solve_p0_s"], 780.0, places=9)
        self.assertAlmostEqual(out["solve_p1_s"], 750.0, places=9)
        self.assertNotIn("prior_build", out["markup_parts"])
        self.assertAlmostEqual(
            sum(out["markup_parts"].values()),
            3 * sum(self.per_pass["parts"].values()),
            places=9,
        )
        # An empty log falls back to the final result's own fields (one pass).
        solve_mod.reset_pass_timing_log()

        class _Final:
            build_s, solve_p0_s, solve_p1_s, markup_parts = 7.0, 8.0, 9.0, {"a": 1.0}

        fallback = ns["_aggregate_pass_timing"](final=_Final())
        self.assertEqual(
            (fallback["build_s"], fallback["solve_p0_s"], fallback["solve_p1_s"]),
            (7.0, 8.0, 9.0),
        )
        self.assertEqual(fallback["n_passes"], 1)

    def test_take_drains_the_log(self):
        from market_sim.pipeline import solve as solve_mod

        solve_mod.reset_pass_timing_log()
        solve_mod._PASS_TIMING_LOG.append(
            {"build_s": 1.0, "solve_p0_s": 0.0, "solve_p1_s": 0.0, "parts": {}}
        )
        self.assertEqual(len(solve_mod.take_pass_timing_log()), 1)
        self.assertEqual(solve_mod.take_pass_timing_log(), [])

    def test_the_log_is_bounded(self):
        from market_sim.pipeline import solve as solve_mod

        self.assertIsNotNone(solve_mod._PASS_TIMING_LOG.maxlen)

    def test_the_backcast_orchestrator_aggregates(self):
        # The helper lives in the backcast orchestrator; pin that it exists,
        # that _timing reads the summed fields from it, and that the retired
        # residual components are gone, so the wiring cannot be dropped silently.
        text = (REPO_ROOT / "scripts" / "run_calibration.py").read_text()
        self.assertIn("def _aggregate_pass_timing(", text)
        self.assertIn("_pass_timing = _aggregate_pass_timing(energy_solve)", text)
        self.assertNotIn('parts["prior_build"]', text)
        self.assertNotIn("energy_solve.p1.build_time", text)
        self.assertIn("reset_pass_timing_log()", text)
        runner = (REPO_ROOT / "src" / "market_sim" / "runner.py").read_text()
        self.assertIn("energy_solve.build_s", runner)
        self.assertNotIn("energy_solve.p1.build_time", runner)


class TestOrchestratorsUseTheHelper(unittest.TestCase):
    """Both orchestrators route through this module (no drifting second copy).

    Guards the reason the helper exists: it shipped with zero consumers, so the
    two inline copies were still free to diverge.
    """

    def test_runner_imports_the_helper(self):
        from market_sim import runner

        self.assertIs(runner.log_year_phase_timing, log_year_phase_timing)
        self.assertIs(runner.log_year_cached_timing, log_year_cached_timing)

    def test_no_inline_format_string_remains(self):

        repo = REPO_ROOT
        needle = "phase timing: data_prep="
        for rel in ("src/market_sim/runner.py", "scripts/run_calibration_full.py"):
            text = (repo / rel).read_text()
            self.assertNotIn(needle, text, f"{rel} still carries an inline copy")


if __name__ == "__main__":
    unittest.main()
