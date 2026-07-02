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


def test_cli_results_rerun_failure_preserves_previous_run(
    tmp_path, monkeypatch, capsys
) -> None:
    """A failed ``--results`` re-run leaves the previous run intact (IO-7/CL-3).

    Regression: the CLI used to ``rmtree`` ``results/<run-id>/`` before
    solving, so a re-run that failed on input validation destroyed the
    previous good results and left nothing behind. Runs now write to a
    scratch sibling and swap in only on success.
    """
    load_path, lmp_path = _write_fixtures(tmp_path)
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "active_resources": ["solar_pv"],
                "premium_deltas": [5.0],
            }
        )
    )
    argv = [
        "--load",
        str(load_path),
        "--config",
        str(config_path),
        "--results",
        "--run-id",
        "keeper",
    ]

    assert main(argv + ["--lmp", str(lmp_path)]) == 0
    run_dir = tmp_path / "results" / "keeper"
    assert (run_dir / "report.json").exists()

    # Second run with a broken LMP path fails cleanly — and must not have
    # touched the previous run directory.
    rc = main(argv + ["--lmp", str(tmp_path / "missing_lmp.csv")])
    assert rc == 1
    captured = capsys.readouterr()
    assert "error:" in captured.err
    assert (run_dir / "report.json").exists()
    assert (run_dir / "SAMPLE_frontier.parquet").exists()


# --- CLI/config audit regressions (CL-1/4/5/6/7/8/9/13/14) --------------------


def test_cli_flags_override_config_file(tmp_path) -> None:
    """Explicit sweep flags override --config values (CL-1).

    Regression: --deltas/--targets/--sensitivity/--load-growth-* were
    silently discarded whenever --config was given.
    """
    from lce_portfolio.cli import build_config
    import argparse

    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {"iso": "SAMPLE", "premium_deltas": [3.0], "lcoe_sensitivity": "mid"}
        )
    )

    def parse(extra):
        ns = argparse.Namespace(
            config=str(config_path),
            iso=None,
            deltas=None,
            targets=None,
            sensitivity=None,
            load_growth_rate=None,
            load_growth_years=None,
        )
        ns.__dict__.update(extra)
        return ns

    # File alone: the file's values stand.
    cfg = build_config(parse({}))
    assert cfg.premium_deltas == (3.0,)
    assert cfg.lcoe_sensitivity == "mid"

    # Explicit flags beat the file.
    cfg = build_config(parse({"deltas": [50.0], "sensitivity": "high"}))
    assert cfg.premium_deltas == (50.0,)
    assert cfg.lcoe_sensitivity == "high"

    # --targets switches the mode even against a premium-cap config file.
    cfg = build_config(parse({"targets": [0.5]}))
    assert cfg.mode == "matching_target"
    assert cfg.matching_targets == (0.5,)


def test_cli_all_infeasible_flagged_and_nonzero_exit(tmp_path, capsys) -> None:
    """A run where every setpoint fails must not exit 0 quietly (CL-4)."""
    load_path, lmp_path = _write_fixtures(tmp_path)
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps(
            {
                "iso": "SAMPLE",
                "mode": "matching_target",
                "matching_targets": [1.0],
                "strict_hourly_matching": True,
                "active_resources": ["solar_pv"],
                "resource_caps_mw": {"solar_pv": 0.0},  # guaranteed infeasible
            }
        )
    )

    rc = main(
        [
            "--config",
            str(config_path),
            "--load",
            str(load_path),
            "--lmp",
            str(lmp_path),
            "--out-dir",
            str(tmp_path / "out"),
            "--no-report",
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "no solution" in captured.out  # summarize() row flag
    assert "no setpoint solved" in captured.err


def test_config_from_file_type_validation(tmp_path, capsys) -> None:
    """Wrong-typed config values are clean, named errors (CL-5/CL-14).

    Regression: "1,2,5" for premium_deltas was a raw TypeError traceback and
    the string "false" silently enabled strict hourly matching.
    """
    from lce_portfolio.config import PortfolioConfig

    cases = [
        ({"premium_deltas": "1,2,5"}, "must be a list"),
        ({"premium_deltas": 5}, "must be a list"),
        ({"discount_rate": "0.07"}, "must be a number"),
        ({"strict_hourly_matching": "false"}, "boolean"),
        ({"resource_caps_mw": {"solar_pv": "many"}}, "mapping"),
    ]
    for payload, expected in cases:
        p = tmp_path / "c.json"
        p.write_text(json.dumps(payload))
        with pytest.raises(ValueError, match=expected):
            PortfolioConfig.from_file(p)

    # Parse errors and empty files name the file (CL-14).
    empty = tmp_path / "empty.json"
    empty.write_text("")
    with pytest.raises(ValueError, match="empty.json"):
        PortfolioConfig.from_file(empty)
    empty_yaml = tmp_path / "empty.yaml"
    empty_yaml.write_text("")
    with pytest.raises(ValueError, match="empty.yaml"):
        PortfolioConfig.from_file(empty_yaml)

    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text("iso: [unclosed")
    with pytest.raises(ValueError, match="invalid YAML"):
        PortfolioConfig.from_file(bad_yaml)

    # And through the CLI they are one clean line, not a traceback (CL-6).
    rc = main(["--config", str(bad_yaml), "--iso", "SAMPLE"])
    assert rc == 1
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "invalid YAML" in captured.err


def test_cli_all_isos_continues_past_failing_iso(tmp_path, capsys) -> None:
    """--all-isos solves the good ISOs, reports the bad, exits nonzero (CL-7)."""
    hours = np.arange(HOURS_PER_YEAR)
    load = pd.DataFrame(
        {
            "hour": np.tile(hours, 2),
            "iso": ["AAA"] * HOURS_PER_YEAR + ["BBB"] * HOURS_PER_YEAR,
            "load_mwh": 100.0,
        }
    )
    lmp = pd.DataFrame({"hour": hours, "iso": "AAA", "lmp": 30.0})  # no BBB
    load_path = tmp_path / "load.csv"
    lmp_path = tmp_path / "lmp.csv"
    load.to_csv(load_path, index=False)
    lmp.to_csv(lmp_path, index=False)
    config_path = tmp_path / "run.json"
    config_path.write_text(
        json.dumps({"active_resources": ["solar_pv"], "premium_deltas": [5.0]})
    )
    out_dir = tmp_path / "out"

    rc = main(
        [
            "--config",
            str(config_path),
            "--load",
            str(load_path),
            "--lmp",
            str(lmp_path),
            "--all-isos",
            "--out-dir",
            str(out_dir),
        ]
    )

    assert rc == 1  # a failure happened...
    assert (out_dir / "AAA_frontier.parquet").exists()  # ...but AAA solved
    assert (out_dir / "report.json").exists()  # and got its report
    captured = capsys.readouterr()
    assert "BBB" in captured.err and "FAILED" in captured.err
    assert "1 of 2 ISO(s) failed" in captured.err
    # KeyError messages carry no spurious repr quotes (CL-8).
    assert 'error: "' not in captured.err


def test_cli_empty_load_file_is_named_error(tmp_path, capsys) -> None:
    """A header-only load file errors naming the file — never a silent
    exit-0 no-op (CL-9)."""
    load_path = tmp_path / "empty_load.csv"
    load_path.write_text("hour,iso,load_mwh\n")
    _, lmp_path = _write_fixtures(tmp_path)

    rc = main(
        [
            "--load",
            str(load_path),
            "--lmp",
            str(lmp_path),
            "--all-isos",
            "--no-report",
            "--out-dir",
            str(tmp_path / "out"),
        ]
    )

    assert rc == 1
    captured = capsys.readouterr()
    assert "no data rows" in captured.err
    assert "Traceback" not in captured.err


def test_cli_directory_as_load_is_clean_error(tmp_path, capsys) -> None:
    """--load pointing at a directory is a clean error, not a raw
    IsADirectoryError traceback (CL-13)."""
    _, lmp_path = _write_fixtures(tmp_path)
    rc = main(
        [
            "--load",
            str(tmp_path),
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
