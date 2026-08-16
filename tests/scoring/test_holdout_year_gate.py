"""G-18: the holdout year gate on run_calibration_full.py's entry point.

CLAUDE.md rule 22 / docs/handoffs/holdout-policy-memo-2026-07.md (b)(2): a
direct ``--year 2022``/``--year 2026`` invocation solved with no code-level
gate — only the GH-Actions workflow_dispatch wrapper (calibration-run.yml)
validated the year. ``enforce_holdout_year_gate`` closes that at the script
entry point: any --year outside {2023, 2024, 2025} hard-fails unless BOTH
--holdout-authorized is passed and the target ISO already carries a
calibration-complete marker.
"""

import importlib.util
import json
from pathlib import Path

import pytest
from scripts.lib import holdout_policy
from tests.helpers import REPO_ROOT

_SPEC = importlib.util.spec_from_file_location(
    "run_calibration_full",
    REPO_ROOT / "scripts" / "run_calibration_full.py",
)
_RCF = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RCF)


def _repo_with_marker(
    tmp_path: Path, complete: dict | None = None, final: dict | None = None
) -> Path:
    marker_dir = tmp_path / "frontend" / "data" / "backcast"
    marker_dir.mkdir(parents=True)
    (marker_dir / "calibration-complete.json").write_text(
        json.dumps({"complete": complete or {}, "final": final or {}})
    )
    return tmp_path


class TestHoldoutYearGate:
    def test_in_window_years_pass_unconditionally(self, tmp_path):
        """2023-2025 (any subset) never trips the gate, authorized or not."""
        root = _repo_with_marker(tmp_path)
        _RCF.enforce_holdout_year_gate([2023, 2024, 2025], "ERCOT", False, root)
        _RCF.enforce_holdout_year_gate([2024], "PJM", False, root)

    def test_holdout_year_without_flag_hard_fails(self, tmp_path):
        root = _repo_with_marker(tmp_path)
        with pytest.raises(SystemExit, match="2022.*ERCOT"):
            _RCF.enforce_holdout_year_gate([2022], "ERCOT", False, root)

    def test_holdout_year_with_flag_but_no_marker_hard_fails(self, tmp_path):
        """--holdout-authorized alone is not enough without the ISO marker.

        2026 is LOCKED-tier, so the unmet block named is ``final``.
        """
        root = _repo_with_marker(tmp_path)
        with pytest.raises(SystemExit, match=r"locked_test-tier.*'final' block"):
            _RCF.enforce_holdout_year_gate([2026], "ERCOT", True, root)

    def test_marker_alone_without_flag_hard_fails(self, tmp_path):
        """The calibration-complete marker alone doesn't bypass the flag."""
        root = _repo_with_marker(tmp_path, complete={"ERCOT": {"declared": "x"}})
        with pytest.raises(SystemExit, match="--holdout-authorized not passed"):
            _RCF.enforce_holdout_year_gate([2022], "ERCOT", False, root)

    def test_flag_and_marker_together_authorize(self, tmp_path):
        """Both --holdout-authorized and the ISO marker authorize the solve."""
        root = _repo_with_marker(tmp_path, complete={"ERCOT": {"declared": "x"}})
        _RCF.enforce_holdout_year_gate([2022], "ERCOT", True, root)

    def test_marker_is_iso_scoped(self, tmp_path):
        """A different ISO's marker doesn't authorize this ISO's holdout."""
        root = _repo_with_marker(tmp_path, complete={"CAISO": {"declared": "x"}})
        with pytest.raises(SystemExit, match=r"ERCOT is not in the 'complete' block"):
            _RCF.enforce_holdout_year_gate([2022], "ERCOT", True, root)

    def test_missing_marker_file_treated_as_no_iso_complete(self, tmp_path):
        """No calibration-complete.json at all behaves like an empty marker map."""
        with pytest.raises(SystemExit, match=r"not in the 'complete' block"):
            _RCF.enforce_holdout_year_gate([2022], "ERCOT", True, tmp_path)

    def test_mixed_years_gate_on_the_out_of_window_subset(self, tmp_path):
        root = _repo_with_marker(tmp_path)
        with pytest.raises(SystemExit, match=r"\[2022\]"):
            _RCF.enforce_holdout_year_gate([2023, 2022], "ERCOT", False, root)

    def test_calibration_years_parity_with_legitimacy_diagnostics(self):
        """The locally-duplicated year set must agree with D6_CALIBRATION_YEARS
        (this repo's convention: separate literals per script, parity-tested —
        see test_legitimacy_diagnostics.py::TestD6Quarantine::test_audit_keepers_parity)."""
        from scripts.legitimacy_diagnostics import D6_CALIBRATION_YEARS

        assert _RCF.HOLDOUT_CALIBRATION_YEARS == D6_CALIBRATION_YEARS


# ---------------------------------------------------------------------------
# Two-tier markers (CLAUDE.md rule 22, owner decision 2026-07-31)
#
# Before the split, ONE `complete` entry authorized every out-of-training year:
# the iterable 2022 validation ladder AND the touch-once 2019 / H1-2026 locked
# test. Rule 22 said so itself ("the CI gate is tier-agnostic"). That made the
# least reversible spend in the policy reachable on the cheapest declaration.
# These tests pin the separation at the gate that actually blocks a solve.
# ---------------------------------------------------------------------------


class TestHoldoutMarkerTiers:
    VAL_ONLY = {"NYISO": {"declared": "2026-07-31"}}

    def test_complete_authorizes_validation_but_not_locked_test(self, tmp_path):
        """The whole point: `complete` must NOT buy 2019 / H1-2026."""
        root = _repo_with_marker(tmp_path, complete=self.VAL_ONLY)
        # Validation tier — authorized.
        _RCF.enforce_holdout_year_gate([2022], "NYISO", True, root)
        # Locked tier — blocked, on the SAME marker that just authorized 2022.
        for locked_year in (2019, 2026):
            with pytest.raises(SystemExit, match=r"locked_test-tier.*'final' block"):
                _RCF.enforce_holdout_year_gate([locked_year], "NYISO", True, root)

    def test_final_authorizes_the_locked_test(self, tmp_path):
        root = _repo_with_marker(
            tmp_path, complete=self.VAL_ONLY, final={"NYISO": {"declared": "x"}}
        )
        _RCF.enforce_holdout_year_gate([2019], "NYISO", True, root)
        _RCF.enforce_holdout_year_gate([2026], "NYISO", True, root)

    def test_final_alone_does_not_authorize_validation(self, tmp_path):
        """The blocks are independent, not nested — `final` is not a superset."""
        root = _repo_with_marker(tmp_path, final={"NYISO": {"declared": "x"}})
        with pytest.raises(SystemExit, match=r"not in the 'complete' block"):
            _RCF.enforce_holdout_year_gate([2022], "NYISO", True, root)

    def test_mixed_tier_years_need_both_markers(self, tmp_path):
        root = _repo_with_marker(tmp_path, complete=self.VAL_ONLY)
        with pytest.raises(SystemExit, match=r"\[2019\] are locked_test-tier"):
            _RCF.enforce_holdout_year_gate([2022, 2019], "NYISO", True, root)

    def test_absent_final_block_fails_closed(self, tmp_path):
        """A marker file with no `final` key at all authorizes no locked test."""
        marker_dir = tmp_path / "frontend" / "data" / "backcast"
        marker_dir.mkdir(parents=True)
        (marker_dir / "calibration-complete.json").write_text(
            json.dumps({"complete": self.VAL_ONLY})  # no `final` key
        )
        with pytest.raises(SystemExit, match=r"'final' block"):
            _RCF.enforce_holdout_year_gate([2019], "NYISO", True, tmp_path)

    def test_unenumerated_year_falls_to_the_strictest_tier(self, tmp_path):
        """Fail closed: an unanticipated year must not be spendable on `complete`."""
        from scripts.lib import holdout_policy

        assert holdout_policy.tier_for_year(2027) == holdout_policy.TIER_LOCKED
        assert holdout_policy.tier_for_year(2015) == holdout_policy.TIER_LOCKED
        root = _repo_with_marker(tmp_path, complete=self.VAL_ONLY)
        with pytest.raises(SystemExit, match=r"'final' block"):
            _RCF.enforce_holdout_year_gate([2027], "NYISO", True, root)

    def test_rule22_tier_membership_matches_the_rule_text(self):
        """2022+ladder = validation; 2019 and H1-2026 = locked test.

        2018 was DROPPED from the ladder by owner decision 2026-08-06 (the
        program's working span is 2019-2025), so it must fall through to the
        fail-closed default and read as locked-test tier rather than validation.
        """
        from scripts.lib import holdout_policy as hp

        assert hp.LOCKED_TEST_YEARS == frozenset({2019, 2026})
        assert {2020, 2021, 2022} <= hp.VALIDATION_YEARS
        assert 2018 not in hp.VALIDATION_YEARS
        assert hp.tier_for_year(2018) == hp.TIER_LOCKED
        assert not (hp.VALIDATION_YEARS & hp.LOCKED_TEST_YEARS)
        assert not (hp.VALIDATION_YEARS & hp.CALIBRATION_YEARS)
        assert not (hp.LOCKED_TEST_YEARS & hp.CALIBRATION_YEARS)

    def test_freeze_still_outranks_both_markers(self, tmp_path):
        """A freeze suspends every tier's authorization, marker or not."""
        root = _repo_with_marker(
            tmp_path, complete=self.VAL_ONLY, final={"NYISO": {"declared": "x"}}
        )
        (root / "frontend/data/backcast/holdout-freeze.json").write_text(
            json.dumps({"active": True, "declared": "2026-07-25", "by": "owner"})
        )
        for year in (2022, 2019):
            with pytest.raises(SystemExit, match="ACTIVE HOLDOUT SPEND FREEZE"):
                _RCF.enforce_holdout_year_gate([year], "NYISO", True, root)


_TAIL_SPEC = importlib.util.spec_from_file_location(
    "derive_actual_tail",
    REPO_ROOT / "scripts" / "data" / "derive_actual_tail.py",
)
_TAIL = importlib.util.module_from_spec(_TAIL_SPEC)
_TAIL_SPEC.loader.exec_module(_TAIL)


class TestActualTailTierGate:
    """The tail deriver is the FOURTH rule-22 gate and must be tier-aware too.

    It read only the ``complete`` block, so a validation-tier marker also
    unlocked H1-2026 — a LOCKED-tier year. That was not hypothetical: the
    committed ``actual_tail.json`` carried a NYISO 2026 row (49.6 % coverage,
    the H1 window) emitted on a validation-only declaration, withdrawn
    2026-07-31. See the register's §PJM note N-P4.
    """

    _VALIDATION_ONLY = {"complete": {"PJM": {}}, "final": {}}

    def test_train_years_always_emit(self):
        for year in (2023, 2024, 2025):
            assert _TAIL._year_emittable("ERCOT", year, {})

    def test_validation_marker_unlocks_2022(self):
        assert _TAIL._year_emittable("PJM", 2022, self._VALIDATION_ONLY)

    def test_validation_marker_does_not_unlock_the_locked_tier(self):
        """The leak this closes: `complete` must never reach 2026 or 2019."""
        for year in (2019, 2026):
            assert not _TAIL._year_emittable("PJM", year, self._VALIDATION_ONLY)

    def test_final_marker_unlocks_h1_2026(self):
        doc = {"complete": {}, "final": {"PJM": {}}}
        assert _TAIL._year_emittable("PJM", 2026, doc)

    def test_unmarked_iso_gets_no_out_of_training_year(self):
        for year in (2018, 2019, 2020, 2021, 2022, 2026):
            assert not _TAIL._year_emittable("MISO", year, self._VALIDATION_ONLY)

    def test_validation_ladder_rungs_follow_the_marker(self):
        """2020/2021 emit for a `complete` ISO and are refused for an unmarked one.

        REWRITTEN at neiso-89 (2026-08-07) with the deletion of the deriver's
        second ladder ``CONSIDERED_HOLDOUT_YEARS``. It previously asserted the
        opposite — that a `complete` ISO is still refused 2020/2021 because that
        tuple withheld them on top of the tier gate. Rule 22's 2026-08-06
        rewrite removed the premise: "WHAT IS HELD OUT IS THE *SCORE*, NEVER THE
        *DATA*", and the touchpoint loop makes 2020-2022 the ITERABLE rungs a
        `complete` marker exists to authorize. The tier marker is now the sole
        gate, so what this asserts is that the gate DISCRIMINATES — marker in,
        marker out — rather than that a second constant blanket-refuses.
        """
        unmarked = {"complete": {"NEISO": {}}, "final": {}}
        for year in (2020, 2021):
            assert holdout_policy.tier_for_year(year) == holdout_policy.TIER_VALIDATION
            assert _TAIL._year_emittable("PJM", year, self._VALIDATION_ONLY)
            assert not _TAIL._year_emittable("PJM", year, unmarked)

    def test_2018_is_dropped_and_held_by_the_stricter_default(self):
        """2018 left the ladder on 2026-08-06 and must be MORE restricted, not less.

        This is the case the deleted ``CONSIDERED_HOLDOUT_YEARS`` was NOT what
        protected: 2018 is absent from every enumerated set, so
        :func:`holdout_policy.tier_for_year` fails closed to the locked tier and
        a `complete` marker cannot reach it. Deleting the second ladder leaves
        that protection exactly where it was.
        """
        assert holdout_policy.tier_for_year(2018) == holdout_policy.TIER_LOCKED
        assert not _TAIL._year_emittable("PJM", 2018, self._VALIDATION_ONLY)
        assert not _TAIL._year_emittable("PJM", 2018, {"complete": {"PJM": {}}})

    def test_the_second_ladder_is_deleted_not_zeroed(self):
        """rule 26 ``[R-DELETE]``: a deprecated gate must not still parse.

        ``CONSIDERED_HOLDOUT_YEARS`` was the deriver's private year ladder,
        duplicating :mod:`scripts.lib.holdout_policy`'s tier sets. An emptied or
        widened tuple left in place would be a re-armable second control point;
        it is removed outright.
        """
        assert not hasattr(_TAIL, "CONSIDERED_HOLDOUT_YEARS")

    def test_locked_tier_still_needs_final_after_the_deletion(self):
        """The deletion must not have made 2019 / H1-2026 reachable on `complete`."""
        for year in (2019, 2026):
            assert holdout_policy.tier_for_year(year) == holdout_policy.TIER_LOCKED
            assert not _TAIL._year_emittable("NEISO", year, {"complete": {"NEISO": {}}})

    def test_empty_marker_doc_fails_closed(self):
        for year in (2018, 2019, 2022, 2026):
            assert not _TAIL._year_emittable("PJM", year, {})


# ---------------------------------------------------------------------------
# B1 (third-party audit 2026-08, gap register): scripts/run_calibration.py was
# the ONE solve entry point outside the three-gate enforcement — a direct
# `--year 2022` there solved with no code-level gate. The fix wires the same
# single-home gate (run_calibration_full.enforce_holdout_year_gate, which the
# tests above already pin) into that CLI's main() ahead of any data access.
# These tests pin the WIRING, not the gate logic.
# ---------------------------------------------------------------------------

_RC_SPEC = importlib.util.spec_from_file_location(
    "run_calibration_b1_gate_probe",
    REPO_ROOT / "scripts" / "run_calibration.py",
)
_RC = importlib.util.module_from_spec(_RC_SPEC)
_RC_SPEC.loader.exec_module(_RC)


class _ReachedDataLoad(Exception):
    """Sentinel: main() got past the holdout gate to its first data read."""


class TestRunCalibrationCliGate:
    def _arm_sentinel(self, monkeypatch):
        """Make the first post-gate data access loud instead of loading files."""

        def _boom():
            raise _ReachedDataLoad()

        monkeypatch.setattr(_RC, "_load_reference", _boom)

    def test_out_of_window_year_blocks_before_any_data_access(self, monkeypatch):
        """`--year 2022` exits at the gate (live repo freeze/marker state) —
        the SystemExit fires before _load_reference is ever reached, and both
        of the gate's refusal messages (freeze-active / unauthorized) cite
        rule 22, so the assertion is robust to the freeze's current state."""
        self._arm_sentinel(monkeypatch)
        with pytest.raises(SystemExit, match="rule 22"):
            _RC.main(["--year", "2022"])

    def test_in_window_years_pass_the_gate(self, monkeypatch):
        """2023-2025 sail through the gate and stop only at the sentinel."""
        self._arm_sentinel(monkeypatch)
        with pytest.raises(_ReachedDataLoad):
            _RC.main(["--year", "2023", "2024", "2025"])

    def test_gate_receives_years_iso_and_flag(self, monkeypatch):
        """The wiring forwards --year, the upcased --iso and --holdout-authorized."""
        import scripts.run_calibration_full as rcf_mod

        calls = []

        def _recorder(years, iso, authorized, repo=None):
            calls.append((list(years), iso, authorized))

        monkeypatch.setattr(rcf_mod, "enforce_holdout_year_gate", _recorder)
        self._arm_sentinel(monkeypatch)
        with pytest.raises(_ReachedDataLoad):
            _RC.main(["--year", "2022", "--iso", "pjm", "--holdout-authorized"])
        assert calls == [([2022], "PJM", True)]
