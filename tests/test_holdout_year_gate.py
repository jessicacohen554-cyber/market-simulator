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

_SPEC = importlib.util.spec_from_file_location(
    "run_calibration_full",
    Path(__file__).resolve().parents[1] / "scripts" / "run_calibration_full.py",
)
_RCF = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_RCF)


def _repo_with_marker(tmp_path: Path, complete: dict | None = None) -> Path:
    marker_dir = tmp_path / "frontend" / "data" / "backcast"
    marker_dir.mkdir(parents=True)
    (marker_dir / "calibration-complete.json").write_text(
        json.dumps({"complete": complete or {}})
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
        """--holdout-authorized alone is not enough without the ISO marker."""
        root = _repo_with_marker(tmp_path)
        with pytest.raises(SystemExit, match="calibration-complete marker"):
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
        with pytest.raises(SystemExit, match="calibration-complete marker"):
            _RCF.enforce_holdout_year_gate([2022], "ERCOT", True, root)

    def test_missing_marker_file_treated_as_no_iso_complete(self, tmp_path):
        """No calibration-complete.json at all behaves like an empty marker map."""
        with pytest.raises(SystemExit, match="calibration-complete marker"):
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
