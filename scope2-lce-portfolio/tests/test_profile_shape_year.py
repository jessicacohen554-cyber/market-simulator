"""Tests for PortfolioConfig.profile_shape_year resolution (real-run harness).

Data-free: exercises the fixture profile directory already used by
test_profiles_real.py / test_cli_real_profile.py (``tests/fixtures/profiles/
ERCOT_2024.parquet``), never the market-sim data tree.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.profiles import build_cf_matrix

from conftest import solar_only

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "profiles"


def test_profile_shape_year_defaults_to_none() -> None:
    """The field defaults to None (opt-in; prior behavior is unchanged)."""
    assert PortfolioConfig().profile_shape_year is None


def test_profile_shape_year_rejects_non_positive() -> None:
    """A zero/negative shape year is rejected on construction."""
    with pytest.raises(ValueError):
        PortfolioConfig(profile_shape_year=0)
    with pytest.raises(ValueError):
        PortfolioConfig(profile_shape_year=-2024)


def test_explicit_year_hit_is_required_and_succeeds() -> None:
    """required=True with a file present loads normally (no warning)."""
    res = solar_only()
    cf = build_cf_matrix(res, "ERCOT", 2024, profiles_dir=FIXTURE_DIR, required=True)
    assert cf.shape[1] == 8760


def test_missing_required_year_is_a_hard_error() -> None:
    """required=True with no matching file raises FileNotFoundError, no fallback."""
    res = solar_only()
    with pytest.raises(FileNotFoundError, match="required CF profile missing"):
        build_cf_matrix(res, "ERCOT", 2031, profiles_dir=FIXTURE_DIR, required=True)


def test_missing_optional_year_still_warns_and_falls_back() -> None:
    """required=False (the default) preserves the historical warn+synthetic path."""
    res = solar_only()
    with pytest.warns(UserWarning, match="falling back to synthetic"):
        cf = build_cf_matrix(res, "ERCOT", 2031, profiles_dir=FIXTURE_DIR)
    assert cf.shape[1] == 8760


def test_sample_iso_unaffected_by_required() -> None:
    """iso='SAMPLE' always takes the synthetic branch, even with required=True."""
    res = solar_only()
    cf = build_cf_matrix(res, "SAMPLE", 2031, profiles_dir=FIXTURE_DIR, required=True)
    assert cf.shape[1] == 8760


def _resolve_shape_year(cfg: PortfolioConfig) -> tuple[int, bool]:
    """Mirror the (year, required) pair `cli.run_one_iso` derives from config."""
    year = cfg.profile_shape_year if cfg.profile_shape_year is not None else cfg.year
    return year, cfg.profile_shape_year is not None


def test_resolution_none_falls_back_to_config_year() -> None:
    """profile_shape_year=None -> resolves to config.year, not required."""
    cfg = PortfolioConfig(iso="ERCOT", year=2031)
    year, required = _resolve_shape_year(cfg)
    assert (year, required) == (2031, False)


def test_resolution_set_pins_vintage_independent_of_config_year() -> None:
    """profile_shape_year=2024 wins over a different config.year (e.g. 2030)."""
    cfg = PortfolioConfig(iso="ERCOT", year=2030, profile_shape_year=2024)
    year, required = _resolve_shape_year(cfg)
    assert (year, required) == (2024, True)


# --- true integration: exercises cli.py's actual wiring, not a re-derivation ---


def _ercot_config(tmp_path, **overrides) -> Path:
    import json

    import numpy as np
    import pandas as pd

    from lce_portfolio.config import HOURS_PER_YEAR

    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    load = 500.0 + 150.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = 25.0 + 15.0 * np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)
    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    pd.DataFrame({"hour": hours, "iso": "ERCOT", "load_mwh": load}).to_csv(
        load_path, index=False
    )
    pd.DataFrame({"hour": hours, "iso": "ERCOT", "lmp": lmp}).to_csv(
        lmp_path, index=False
    )

    config_path = tmp_path / "run.json"
    payload = {
        "iso": "ERCOT",
        "load_file": str(load_path),
        "lmp_file": str(lmp_path),
        "active_resources": ["solar_pv", "onshore_wind"],
        "premium_deltas": [10.0],
        **overrides,
    }
    config_path.write_text(json.dumps(payload))
    return config_path


def test_cli_profile_shape_year_pinned_uses_fixture_regardless_of_year(
    tmp_path, monkeypatch
) -> None:
    """CLI end-to-end: year=2030 (no such fixture) but profile_shape_year=2024
    (the fixture vintage) -> solves successfully against the pinned shape."""
    monkeypatch.setattr("lce_portfolio.profiles.DEFAULT_PROFILES_DIR", FIXTURE_DIR)
    from lce_portfolio.cli import main

    config_path = _ercot_config(tmp_path, year=2030, profile_shape_year=2024)
    out_dir = tmp_path / "out"
    rc = main(["--config", str(config_path), "--out-dir", str(out_dir)])
    assert rc == 0
    assert (out_dir / "ERCOT_frontier.parquet").exists()


def test_cli_profile_shape_year_pinned_missing_file_is_a_hard_error(
    tmp_path, monkeypatch, capsys
) -> None:
    """CLI end-to-end: profile_shape_year pinned to a vintage with no fixture
    file -> clean CLI error (rc=1), never a silent synthetic solve."""
    monkeypatch.setattr("lce_portfolio.profiles.DEFAULT_PROFILES_DIR", FIXTURE_DIR)
    from lce_portfolio.cli import main

    config_path = _ercot_config(tmp_path, year=2030, profile_shape_year=2099)
    out_dir = tmp_path / "out"
    rc = main(["--config", str(config_path), "--out-dir", str(out_dir)])
    assert rc == 1
    assert not (out_dir / "ERCOT_frontier.parquet").exists()
    err = capsys.readouterr().err
    assert "required CF profile missing" in err
