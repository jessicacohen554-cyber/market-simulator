"""Tests for the CLI: config-driven load/LMP wiring and clean error surfacing."""

import json

import numpy as np
import pandas as pd
import pytest

from lce_portfolio.config import HOURS_PER_YEAR
from lce_portfolio.cli import main


def _write_fixtures(tmp_path):
    """Minimal-resource, single-ISO 8760 load + LMP fixtures for a fast solve."""
    hours = np.arange(HOURS_PER_YEAR)
    hod = hours % 24
    load = 100.0 + 20.0 * np.clip(np.sin((hod - 8) / 24.0 * 2 * np.pi), 0, None)
    lmp = 25.0 + 10.0 * np.clip(np.sin((hod - 9) / 24.0 * 2 * np.pi), 0, None)

    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "load_mwh": load}).to_csv(
        load_path, index=False
    )
    pd.DataFrame({"hour": hours, "iso": "SAMPLE", "lmp": lmp}).to_csv(
        lmp_path, index=False
    )
    return load_path, lmp_path


def test_cli_config_load_lmp_end_to_end(tmp_path) -> None:
    """A config with load_file/lmp_file runs the real-data path end-to-end."""
    load_path, lmp_path = _write_fixtures(tmp_path)
    out_dir = tmp_path / "out"
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "load_file": str(load_path),
                "lmp_file": str(lmp_path),
                "active_resources": ["solar_pv"],
                "premium_deltas": [10.0],
            }
        )
    )

    rc = main(["--config", str(config_path), "--out-dir", str(out_dir)])

    assert rc == 0
    assert (out_dir / "SAMPLE_frontier.parquet").exists()
    assert (out_dir / "SAMPLE_build_mix.parquet").exists()


def test_cli_missing_load_file_is_clean_error(tmp_path, capsys) -> None:
    """A load path that does not exist surfaces as a clean CLI message."""
    _, lmp_path = _write_fixtures(tmp_path)

    rc = main(
        [
            "--load",
            str(tmp_path / "does_not_exist.csv"),
            "--lmp",
            str(lmp_path),
            "--iso",
            "SAMPLE",
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "Traceback" not in captured.err


def test_cli_bad_schema_is_clean_error(tmp_path, capsys) -> None:
    """A load file missing required columns surfaces as a clean CLI message."""
    _, lmp_path = _write_fixtures(tmp_path)
    load_path = tmp_path / "bad_load.csv"
    pd.DataFrame({"hour": [0, 1], "iso": ["SAMPLE", "SAMPLE"]}).to_csv(
        load_path, index=False
    )

    rc = main(
        [
            "--load",
            str(load_path),
            "--lmp",
            str(lmp_path),
            "--iso",
            "SAMPLE",
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert "missing columns" in captured.err
    assert "Traceback" not in captured.err


def test_cli_requires_load_or_config(capsys) -> None:
    """Neither --load nor a config load_file is a clean usage error, not a crash."""
    with pytest.raises(SystemExit):
        main(["--iso", "SAMPLE", "--lmp", "nonexistent.csv"])
    captured = capsys.readouterr()
    assert "--load" in captured.err
