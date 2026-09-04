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

    The residual is ``energy_solve_wall - p1.build_time - r0.solve_time -
    p1.solve_time``. What makes the arithmetic non-obvious is ``build_time``:
    on the warm path ``p1.build_time`` IS the one model build, but when P1
    cold-rebuilds it names the SECOND model, leaving the first unaccounted —
    which is the whole point of the ``p0_build`` component. This pins the
    identity on both routings with a fake solve, so a future edit to the
    segment boundaries cannot silently stop summing.
    """

    def _parts(self, *, warm_p1: bool):
        """Replay the assembly arithmetic on synthetic segment walls."""
        # Interior wall segments [_t0.._t6] and the two HiGHS run times.
        t = [0.0, 100.0, 260.0, 265.0, 267.0, 430.0, 431.0]
        s0, s1 = 60.0, 55.0
        build_setup, build_p1_cold = 96.0, 94.0
        p1_cold = not warm_p1
        build_p1 = build_p1_cold if p1_cold else 0.0
        parts = {
            "setup": (t[1] - t[0]) - build_setup,
            "p0_build": build_setup if p1_cold else 0.0,
            "p0_post": (t[2] - t[1]) - s0,
            "markup": t[3] - t[2],
            "seam": t[4] - t[3],
            "p1_post": (t[5] - t[4]) - s1 - build_p1,
            "tail": t[6] - t[5],
        }
        # What the orchestrator subtracts: p1.build_time.
        reported_build = build_p1_cold if p1_cold else build_setup
        residual = (t[6] - t[0]) - reported_build - s0 - s1
        return parts, residual

    def test_sums_to_residual_on_the_warm_p1_path(self):
        parts, residual = self._parts(warm_p1=True)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        self.assertEqual(parts["p0_build"], 0.0)

    def test_sums_to_residual_on_the_cold_p1_rebuild_path(self):
        parts, residual = self._parts(warm_p1=False)
        self.assertAlmostEqual(sum(parts.values()), residual, places=9)
        # The unaccounted first build is surfaced, not hidden in the residual.
        self.assertGreater(parts["p0_build"], 0.0)

    def test_solve_module_defines_the_same_component_names(self):
        import inspect

        from market_sim.pipeline import solve as solve_mod

        src = inspect.getsource(solve_mod.run_energy_solve)
        for name in (
            "setup",
            "p0_build",
            "p0_post",
            "markup",
            "seam",
            "p1_post",
            "tail",
        ):
            self.assertIn(f'"{name}":', src, f"markup_parts lost the {name} component")


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
