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
