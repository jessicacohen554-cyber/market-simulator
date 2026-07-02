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


def test_cli_emissions_file_threads_residual_co2_to_outputs(tmp_path) -> None:
    """--emissions wires the hourly rate through to residual_co2_tons (ADR 0013).

    Restricted to a single active resource (via --config, mirroring
    test_cli_config_load_lmp_end_to_end) instead of the CLI default
    active_minimal resource set: the intake path still hard-requires the full
    8760-hour calendar (ADR 0010), but a 1-resource LP solves in a fraction of
    the time of the multi-resource default and exercises the same emissions
    wiring (grid_buy_mwh/residual_co2_tons come from the LP dual/reporting
    layer, not from resource count).
    """
    load_path, lmp_path = _write_fixtures(tmp_path)
    hours = np.arange(HOURS_PER_YEAR)
    emissions_path = tmp_path / "rates.csv"
    pd.DataFrame(
        {
            "hour": hours,
            "iso": "SAMPLE",
            "fossil_avg_co2_rate": np.where(hours % 24 < 12, 0.5, 0.3),
        }
    ).to_csv(emissions_path, index=False)
    out_dir = tmp_path / "out"
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "load_file": str(load_path),
                "lmp_file": str(lmp_path),
                "emissions_file": str(emissions_path),
                "active_resources": ["solar_pv"],
                "premium_deltas": [1.0],
            }
        )
    )

    rc = main(["--config", str(config_path), "--out-dir", str(out_dir)])

    assert rc == 0
    frontier = pd.read_parquet(out_dir / "SAMPLE_frontier.parquet")
    # A $1 cap leaves unmatched hours, so the hourly rate yields a residual > 0.
    assert (frontier["grid_buy_mwh"] > 0.0).all()
    assert (frontier["residual_co2_tons"] > 0.0).all()


def test_run_id_validation_rejects_unsafe_ids() -> None:
    """Unsafe run ids never reach ``RESULTS_ROOT / run_id`` (IO-1/CL-2).

    The results store deletes ``results/<run-id>/`` before rewriting it, so a
    run id that is not a single safe path component (absolute path, ``..``
    traversal, separators, whitespace, leading dot) must raise at validation.
    """
    from lce_portfolio.cli import validate_run_id

    assert validate_run_id("SAMPLE_premium_cap_20260702-171842") == (
        "SAMPLE_premium_cap_20260702-171842"
    )
    assert validate_run_id("my.run-1_x") == "my.run-1_x"
    for bad in (
        "/abs/path/victim",
        "../escape",
        "a/b",
        "a\\b",
        "..",
        ".hidden",
        "has space",
        "has\nnewline",
        "",
    ):
        with pytest.raises(ValueError, match="invalid --run-id"):
            validate_run_id(bad)


def test_cli_results_traversal_run_id_is_clean_error_and_deletes_nothing(
    tmp_path, monkeypatch, capsys
) -> None:
    """``--results --run-id <absolute path>`` errors cleanly, victim untouched.

    Regression for audit findings IO-1/CL-2: previously the CLI composed
    ``results / run_id`` (which discards ``results/`` for an absolute id) and
    ``shutil.rmtree``'d it before any input validation, deleting an arbitrary
    user-writable directory on a typo'd run id.
    """
    monkeypatch.chdir(tmp_path)
    victim = tmp_path / "victim_dir"
    victim.mkdir()
    (victim / "marker.txt").write_text("keep me")

    rc = main(
        [
            "--iso",
            "SAMPLE",
            "--load",
            "unused_load.csv",
            "--lmp",
            "unused_lmp.csv",
            "--results",
            "--run-id",
            str(victim),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "invalid --run-id" in captured.err
    assert "Traceback" not in captured.err
    assert (victim / "marker.txt").exists()
