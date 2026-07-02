"""Tests for examples/run_real_sweep.py's LMP-source resolution precedence.

Data-free and solve-free: exercises resolve_lmp_path() directly against
tmp_path fixture files, not a real sweep run (no LP solve).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

_EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
if str(_EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(_EXAMPLES_DIR))

from run_real_sweep import resolve_lmp_path  # noqa: E402


def _touch(path: Path, age_offset_s: float = 0.0) -> Path:
    """Create an empty file and (optionally) back-date its mtime by ``age_offset_s``."""
    path.write_text("hour,iso,lmp\n")
    if age_offset_s:
        t = time.time() - age_offset_s
        import os

        os.utime(path, (t, t))
    return path


def test_explicit_lmp_wins_over_everything(tmp_path) -> None:
    """--lmp is honored even when real/dummy files exist in inputs_dir."""
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    _touch(inputs_dir / "bau_lmp_2030.csv")
    explicit = tmp_path / "custom_lmp.csv"
    _touch(explicit)

    path, info = resolve_lmp_path("ERCOT", explicit, inputs_dir, 2030)
    assert path == explicit
    assert info["source"] == "explicit"
    assert info["is_synthetic"] is False


def test_explicit_dummy_named_lmp_is_flagged_synthetic(tmp_path) -> None:
    """An explicit path is still labeled synthetic if it's a *_dummy.csv file."""
    explicit = tmp_path / "bau_lmp_2030_dummy.csv"
    _touch(explicit)
    path, info = resolve_lmp_path("ERCOT", explicit, tmp_path / "inputs", 2030)
    assert path == explicit
    assert info["is_synthetic"] is True


def test_missing_explicit_lmp_raises(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        resolve_lmp_path("ERCOT", tmp_path / "nope.csv", tmp_path / "inputs", 2030)


def test_real_file_preferred_over_dummy(tmp_path) -> None:
    """No --lmp: a non-dummy bau_lmp_*.csv beats an existing dummy file."""
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    dummy = _touch(inputs_dir / "bau_lmp_2030_dummy.csv")
    real = _touch(inputs_dir / "bau_lmp_2030.csv")

    path, info = resolve_lmp_path("ERCOT", None, inputs_dir, 2030)
    assert path == real
    assert info["source"] == "real"
    assert info["is_synthetic"] is False
    assert dummy != path  # sanity: the dummy file was indeed present but not chosen


def test_newest_real_file_chosen_when_multiple(tmp_path) -> None:
    """Among several real files, the newest by mtime wins."""
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    older = _touch(inputs_dir / "bau_lmp_2026.csv", age_offset_s=100.0)
    newer = _touch(inputs_dir / "bau_lmp_2030.csv", age_offset_s=0.0)

    path, info = resolve_lmp_path("ERCOT", None, inputs_dir, 2030)
    assert path == newer
    assert older != newer


def test_falls_back_to_dummy_when_no_real_file(tmp_path) -> None:
    """No real file: the newest dummy COVERING the ISO is used (CL-12).

    Regression: dummy files were not ISO-keyed and resolve_lmp_path ignored
    its ``iso`` argument, so the documented run-ERCOT-then-PJM workflow
    reused ERCOT's dummy for PJM and crashed in intake. An ISO-keyed dummy
    matches by filename; a legacy un-keyed dummy is peeked and reused only
    if its ``iso`` column contains the requested ISO.
    """
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    keyed = _touch(inputs_dir / "bau_lmp_ERCOT_2030_dummy.csv")

    path, info = resolve_lmp_path("ERCOT", None, inputs_dir, 2030)
    assert path == keyed
    assert info["source"] == "dummy_existing"
    assert info["is_synthetic"] is True

    # Another ISO must NOT silently reuse ERCOT's dummy.
    path, info = resolve_lmp_path("PJM", None, inputs_dir, 2030)
    assert path is None
    assert info["source"] == "none"

    # A legacy un-keyed dummy is reused only when its iso column covers the
    # requested ISO.
    legacy = inputs_dir / "bau_lmp_2030_dummy.csv"
    legacy.write_text("hour,iso,lmp\n0,PJM,25.0\n")
    path, info = resolve_lmp_path("PJM", None, inputs_dir, 2030)
    assert path == legacy
    assert info["source"] == "dummy_existing"


def test_no_files_returns_none_for_caller_to_generate(tmp_path) -> None:
    """Nothing found (and inputs_dir may not even exist) -> (None, info)."""
    path, info = resolve_lmp_path("ERCOT", None, tmp_path / "does_not_exist", 2030)
    assert path is None
    assert info["source"] == "none"
    assert info["is_synthetic"] is True
