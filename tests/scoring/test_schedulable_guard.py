"""The §2.1b window cap must refuse from EVERY schedulable entry point.

The forecast-readiness audit (2026-07-30, FR-25) found the cap enforced in 2 of
~6 entry points: ``run_full_horizon.py`` and ``run_ces_leg.py`` had it, while
``market-sim run/sweep/ensemble/matrix``, the PB-5 slice drivers and the
golden-fixture seed could each schedule a 15- or 25-solve-year campaign with no
refusal anywhere. FFR-1D extracted the guard to
:mod:`market_sim.config.schedulable` (re-exported by
``scripts/lib/schedulable.py``) and called it from all of them; this module is
the test that keeps it that way.

Every case here is pure argument parsing plus a config construction — the guard
raises BEFORE any solve, which is the whole point, so nothing here touches
HiGHS, the cache or the data root.
"""

from __future__ import annotations

import argparse

import pytest
import yaml

from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.schedulable import (
    MAX_UNAUTHORIZED_SOLVE_YEARS,
    assert_config_schedulable,
    assert_schedulable,
    config_horizon,
)

OVER_CAP = (2026, 2050)  # 25 solve-years — the default forecast horizon
AT_CAP = (2026, 2030)  # 5 solve-years — T1-F, the schedulable instrument


# --------------------------------------------------------------------------- #
# The pure guard
# --------------------------------------------------------------------------- #
def test_cap_is_five():
    """The cap literal is the §2.1b '10-hour rule' value, not a local guess."""
    assert MAX_UNAUTHORIZED_SOLVE_YEARS == 5


def test_window_at_cap_is_allowed():
    assert assert_schedulable(*AT_CAP, False) == 5


def test_window_over_cap_is_refused():
    with pytest.raises(SystemExit) as exc:
        assert_schedulable(*OVER_CAP, False)
    assert "§2.1b" in str(exc.value)
    assert "25 solve-years" in str(exc.value)


def test_window_over_cap_is_allowed_when_authorized():
    assert assert_schedulable(*OVER_CAP, True) == 25


def test_six_years_is_over_the_cap():
    """The boundary is > 5, not >= 5 — 2026-2031 is six solve-years."""
    with pytest.raises(SystemExit):
        assert_schedulable(2026, 2031, False)


def test_entry_point_is_named_in_the_refusal():
    with pytest.raises(SystemExit) as exc:
        assert_schedulable(*OVER_CAP, False, "market-sim matrix")
    assert "market-sim matrix" in str(exc.value)


# --------------------------------------------------------------------------- #
# The config-carried horizon (the CLIs with no year arguments)
# --------------------------------------------------------------------------- #
def test_config_with_no_years_resolves_the_module_default_horizon():
    """A YAML with no year fields inherits 2026-2050 — the audit's headline case."""
    start, end = config_horizon(ScenarioConfig(iso="PJM", mode="forecast"))
    assert end - start + 1 > MAX_UNAUTHORIZED_SOLVE_YEARS


def test_forecast_config_over_cap_is_refused():
    cfg = ScenarioConfig(iso="PJM", mode="forecast", start_year=2026, end_year=2050)
    with pytest.raises(SystemExit):
        assert_config_schedulable(cfg, False, "test")


def test_forecast_config_at_cap_is_allowed():
    cfg = ScenarioConfig(iso="PJM", mode="forecast", start_year=2026, end_year=2030)
    assert assert_config_schedulable(cfg, False, "test") == 5


def test_authorized_forecast_config_over_cap_is_allowed():
    cfg = ScenarioConfig(iso="PJM", mode="forecast", start_year=2026, end_year=2050)
    assert assert_config_schedulable(cfg, True, "test") == 25


def test_hindcast_harness_configs_are_still_capped():
    """mode='forecast', hindcast=True is the T1-H/T1-X harness — §2.1b sizes it."""
    cfg = ScenarioConfig(
        iso="PJM", mode="forecast", hindcast=True, start_year=2021, end_year=2030
    )
    with pytest.raises(SystemExit):
        assert_config_schedulable(cfg, False, "test")


def test_backcast_configs_are_out_of_scope():
    """§2.1b is the FORECAST cap; a backcast window is rule 22's holdout gate."""
    cfg = ScenarioConfig(iso="PJM", mode="backcast", start_year=2023, end_year=2025)
    assert assert_config_schedulable(cfg, False, "test") is None


# --------------------------------------------------------------------------- #
# Per-entry-point coverage: >5 unauthorized refused, 5 allowed, authorized 25 ok
# --------------------------------------------------------------------------- #
def _write_config(tmp_path, name, **fields):
    path = tmp_path / name
    path.write_text(yaml.safe_dump({"iso": "PJM", "mode": "forecast", **fields}))
    return str(path)


def _runner_main(argv):
    from market_sim import runner

    runner.main(argv)


class _Solved(Exception):
    """Raised by the stubs below when execution gets PAST the guard."""


@pytest.fixture
def no_solve(monkeypatch):
    """Replace every solve seam the CLIs reach so a pass-through is visible."""
    from market_sim import runner

    def _boom(*_a, **_k):
        raise _Solved()

    monkeypatch.setattr(runner, "run_scenario_iso", _boom)
    monkeypatch.setattr(runner, "run_sweep", _boom)
    return _boom


@pytest.mark.parametrize(
    "command,extra",
    [("run", []), ("sweep", []), ("ensemble", []), ("matrix", [])],
)
def test_market_sim_cli_refuses_over_cap(tmp_path, no_solve, command, extra):
    """Every market-sim subcommand refuses a 2026-2050 config (audit FR-25)."""
    cfg = _write_config(tmp_path, "base.yaml", start_year=2026, end_year=2050)
    sweep = tmp_path / "sweep.yaml"
    sweep.write_text(yaml.safe_dump({"cases": {"a": {}}}))
    argv = {
        "run": ["run", "--config", cfg],
        "sweep": ["sweep", "--sweep", str(sweep)],
        "ensemble": ["ensemble", "--config", cfg],
        "matrix": ["matrix", "--config", cfg, "--matrix", str(sweep)],
    }[command] + extra
    with pytest.raises(SystemExit) as exc:
        _runner_main(argv)
    assert "§2.1b" in str(exc.value)


@pytest.mark.parametrize("command", ["run", "ensemble", "matrix"])
def test_market_sim_cli_allows_five_years(tmp_path, no_solve, command):
    """A T1-F window passes the guard (and only then reaches the solve seam)."""
    cfg = _write_config(tmp_path, "base.yaml", start_year=2026, end_year=2030)
    sweep = tmp_path / "sweep.yaml"
    sweep.write_text(yaml.safe_dump({"cases": {"a": {}}}))
    argv = {
        "run": ["run", "--config", cfg],
        "ensemble": ["ensemble", "--config", cfg],
        "matrix": ["matrix", "--config", cfg, "--matrix", str(sweep)],
    }[command]
    with pytest.raises((_Solved, SystemExit)) as exc:
        _runner_main(argv)
    assert "§2.1b" not in str(exc.value)


@pytest.mark.parametrize("command", ["run", "ensemble", "matrix"])
def test_market_sim_cli_allows_authorized_twenty_five(tmp_path, no_solve, command):
    cfg = _write_config(tmp_path, "base.yaml", start_year=2026, end_year=2050)
    sweep = tmp_path / "sweep.yaml"
    sweep.write_text(yaml.safe_dump({"cases": {"a": {}}}))
    argv = {
        "run": ["run", "--config", cfg],
        "ensemble": ["ensemble", "--config", cfg],
        "matrix": ["matrix", "--config", cfg, "--matrix", str(sweep)],
    }[command] + ["--full-solve-authorized"]
    with pytest.raises((_Solved, SystemExit)) as exc:
        _runner_main(argv)
    assert "§2.1b" not in str(exc.value)


def test_every_market_sim_subcommand_carries_the_flag():
    """A subcommand without the flag is an unguarded entry point by definition."""
    from market_sim.runner import _build_parser

    parser = _build_parser()
    subparsers = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ][0]
    for name, sub in subparsers.choices.items():
        options = {opt for action in sub._actions for opt in action.option_strings}
        assert "--full-solve-authorized" in options, (
            f"market-sim {name} can schedule a forecast horizon but has no "
            "--full-solve-authorized flag — it is an unguarded entry point"
        )


@pytest.mark.parametrize(
    "module,attr",
    [
        ("scripts.pb5_member_slice", "main"),
        ("scripts.pb5_assemble", "main"),
        ("scripts.golden_forecast_bands", "main"),
        ("scripts.run_full_horizon", "main"),
    ],
)
def test_script_entry_points_import_the_shared_guard(module, attr):
    """Each schedulable script must route through the SHARED §2.1b guard.

    An entry point that grew its own copy of the cap is how the enforcement
    drifted to 2-of-6 in the first place, so the import itself is the invariant.
    """
    import importlib

    mod = importlib.import_module(module)
    assert hasattr(mod, attr)
    source = open(mod.__file__).read()
    assert "schedulable import" in source, (
        f"{module} schedules solve-years but does not import the shared §2.1b guard"
    )


def test_pb5_member_slice_refuses_over_cap(tmp_path, monkeypatch):
    """The PB-5 slice driver refuses before it samples a single draw."""
    from scripts import pb5_member_slice

    cfg = _write_config(tmp_path, "base.yaml", start_year=2026, end_year=2050)
    sampler = tmp_path / "sampler.yaml"
    sampler.write_text(yaml.safe_dump({"n": 2, "seed": 1}))
    monkeypatch.setattr(
        "sys.argv",
        ["pb5_member_slice", "--config", cfg, "--sampler", str(sampler)],
    )
    with pytest.raises(SystemExit) as exc:
        pb5_member_slice.main()
    assert "§2.1b" in str(exc.value)


def test_golden_seed_refuses_without_authorization(tmp_path, monkeypatch):
    """The 15-solve-year golden reseed refuses without the D-7 authorization."""
    from scripts import golden_forecast_bands as gfb

    monkeypatch.setattr(gfb, "_git_dirty", lambda: False)
    with pytest.raises(SystemExit) as exc:
        gfb.main(["seed", "--force", "--reason", "test"])
    assert "§2.1b" in str(exc.value)
