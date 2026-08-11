"""Guards for the rule-28(c) SHARED-field ratchet (nyiso-115).

The ISO-scoped ratchet only ever looks at ``<iso>_*`` fields, so a SHARED
mechanism armed on a designated keeper with no matrix row anywhere is invisible
to it — the same 227-3 shape, one class wider. nyiso-114 closed NYISO's
ISO-scoped column to 0/0/0 while twelve shared fields sat armed on its keeper
with zero matrix mention.

Two producers have to agree about what "registered" means:
``scripts/mechanism_matrix_gap_sweep.py`` (imports the live ``ScenarioConfig``
and WRITES the baseline) and ``scripts/check_mechanism_matrix.py`` (stdlib-only,
ENFORCES it in CI). nyiso-114 shipped a ratchet whose two halves disagreed on
seven fields — ``\\b`` vs substring matching — leaving a baseline that could
never be satisfied. These tests pin the invariant that prevents a repeat: **the
checker may never be stricter than the sweep.**
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import MISSING as _MISSING
from dataclasses import fields as _dc_fields
from pathlib import Path

import pytest


def sweep_fields():
    """The live ``ScenarioConfig`` dataclass fields (shipped defaults)."""
    from market_sim.config.scenarios import ScenarioConfig  # noqa: PLC0415

    return _dc_fields(ScenarioConfig)


REPO = Path(__file__).resolve().parents[3]
BASELINE = REPO / "docs/codebase-site/data/mechanism-matrix-gaps.json"


def _load(name: str, relpath: str):
    """Import a scripts/ module by path (they are not an installed package)."""
    spec = importlib.util.spec_from_file_location(name, REPO / relpath)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def checker():
    return _load("cm_check", "scripts/check_mechanism_matrix.py")


@pytest.fixture(scope="module")
def sweep():
    return _load("cm_sweep", "scripts/mechanism_matrix_gap_sweep.py")


@pytest.fixture(scope="module")
def baseline():
    return json.loads(BASELINE.read_text(encoding="utf-8"))


class TestBaselineShape:
    """The committed baseline carries both censuses and its own exclusions."""

    def test_baseline_has_both_blocks_for_all_six_isos(self, baseline, sweep):
        for block in ("absent", "shared_armed_on_keeper"):
            assert block in baseline, block
            assert set(baseline[block]) == set(sweep.ISO_INDEX)

    def test_exclusions_are_single_sourced_from_the_sweep(self, baseline, sweep):
        # The checker is stdlib-only and cannot import the sweep, so the sweep
        # WRITES its exclusions into the baseline and the checker READS them
        # there. A second hand-maintained copy would be free to drift.
        assert baseline["shared_census_exclusions"] == sweep.SHARED_CENSUS_EXCLUSIONS, (
            "run scripts/mechanism_matrix_gap_sweep.py --write-baseline"
        )

    def test_every_exclusion_states_a_reason(self, sweep):
        # An exemption from a rule-28(c) duty with no written justification is
        # the off-registry channel rule 24 [R-REGISTRY] exists to close.
        for field, reason in sweep.SHARED_CENSUS_EXCLUSIONS.items():
            assert isinstance(reason, str) and len(reason) > 40, field


class TestCheckerIsNeverStricterThanTheSweep:
    """The invariant whose violation made the nyiso-114 baseline unsatisfiable."""

    def test_shared_ratchet_is_satisfied_by_the_committed_baseline(self, checker):
        matrix = checker.matrix_all_text()  # base + every ISO shard (2026-08-11)
        source = (REPO / checker.SCENARIOS_PATH).read_text("utf-8")
        assert checker.shared_gap_ratchet(matrix, source) == []

    def test_iso_scoped_ratchet_is_satisfied_by_the_committed_baseline(self, checker):
        matrix = checker.matrix_all_text()  # base + every ISO shard (2026-08-11)
        source = (REPO / checker.SCENARIOS_PATH).read_text("utf-8")
        assert checker.gap_ratchet(matrix, source) == []

    def test_default_parser_is_conservative_not_wrong(self, checker):
        # The checker parses defaults out of source text (no import available in
        # CI). It may parse FEWER fields than the sweep sees — that only makes
        # the gate weaker, which is safe — but the ones it does parse must be
        # correct, or it would demand a baseline the sweep cannot write.
        source = (REPO / checker.SCENARIOS_PATH).read_text("utf-8")
        parsed = checker._scenarioconfig_defaults(source)
        # Compare against the SHIPPED dataclass defaults — the same thing the
        # sweep reads — not against a constructed instance, whose required
        # fields (`iso`) carry the caller's argument rather than the default.
        live = {
            f.name: f.default
            for f in sweep_fields()
            if f.default is not _MISSING and not callable(f.default)
        }
        checked = 0
        for field, value in parsed.items():
            if field not in live:
                continue
            actual = live[field]
            actual = list(actual) if isinstance(actual, tuple) else actual
            expected = list(value) if isinstance(value, tuple) else value
            assert actual == expected, f"{field}: parsed {expected!r}, live {actual!r}"
            checked += 1
        assert checked > 400, f"parser degenerated to {checked} fields"


class TestRatchetActuallyBites:
    """A ratchet that cannot fail is not a ratchet."""

    def test_an_unregistered_keeper_armed_shared_field_fails(self, checker, tmp_path):
        # Strip one genuinely-armed shared field from BOTH the matrix text and
        # the baseline and the gate must fire for the ISO whose keeper arms it.
        matrix = checker.matrix_all_text()  # base + every ISO shard (2026-08-11)
        source = (REPO / checker.SCENARIOS_PATH).read_text("utf-8")
        field = "cc_nameplate_summer_derate"
        assert field in matrix, "fixture field must start registered"
        errors = checker.shared_gap_ratchet(matrix.replace(field, "zz_removed"), source)
        assert any(field in e for e in errors), errors

    def test_an_excluded_field_never_fires(self, checker, sweep):
        # weather_year is non-default on essentially every backcast bundle by
        # construction; it must stay silent even though it is never registered.
        matrix = checker.matrix_all_text()  # base + every ISO shard (2026-08-11)
        source = (REPO / checker.SCENARIOS_PATH).read_text("utf-8")
        assert "weather_year" in sweep.SHARED_CENSUS_EXCLUSIONS
        assert not any(
            "`weather_year`" in e for e in checker.shared_gap_ratchet(matrix, source)
        )


class TestNyisoColumnStaysClosed:
    """nyiso-115 closed NYISO's shared column; keep it closed."""

    def test_nyiso_has_no_shared_gap_in_the_baseline(self, baseline):
        assert baseline["shared_armed_on_keeper"]["NYISO"] == []

    def test_nyiso_iso_scoped_column_stays_closed(self, baseline):
        # Closed by nyiso-114; a regression here means a new nyiso_* field
        # landed without its row (rule 28c).
        assert baseline["absent"]["NYISO"] == []
