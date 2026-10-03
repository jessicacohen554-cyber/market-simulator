"""``persist.env_solve_choices`` records the LIVE env solve knobs at effect.

Owner ruling 2026-10-03 (audit A5, ``docs/audit/2026-10/G4-env-knobs.md``):
every environment variable that can move the returned LP vertex is recorded in
the run's ``run_config.json`` / ``meta.json`` ``environment`` block at the value
the solve path derived from it. Zero-LP: no model is built.
"""

from __future__ import annotations

import json

import yaml

from market_sim.pipeline.persist import (
    ENV_SOLVE_KNOBS,
    env_solve_choices,
    environment_block,
)
from scripts.lib.run_record import write_run_config


def _clear_env(monkeypatch) -> None:
    for name in ENV_SOLVE_KNOBS:
        monkeypatch.delenv(name, raising=False)


def test_unset_records_the_solve_path_defaults(monkeypatch):
    _clear_env(monkeypatch)
    rec = env_solve_choices()
    assert rec["warmstart"] is True
    assert rec["warmstart_xyear"] is False
    assert rec["p1_basis_seed"] is False
    assert rec["p1_floor_inplace"] is False
    assert rec["p0_cache"] is False
    assert rec["highs_lean"] is False
    assert rec["highs_presolve"] == "off"
    assert rec["use_clean"] is False
    assert isinstance(rec["highs_threads"], int)
    assert isinstance(rec["highs_simplex_scale_strategy"], int)
    assert rec["highs_simplex_scale_strategy"] != 0


def test_set_knobs_record_their_effective_option_values(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("MARKET_SIM_HIGHS_LEAN", "1")
    monkeypatch.setenv("MARKET_SIM_HIGHS_THREADS", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "1")
    monkeypatch.setenv("MARKET_SIM_P0_CACHE", "on")
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "0")
    rec = env_solve_choices()
    # The HiGHS option VALUE is recorded, not the env string.
    assert rec["highs_simplex_scale_strategy"] == 0
    assert rec["highs_lean"] is True
    assert rec["highs_threads"] == 1
    assert rec["warmstart_xyear"] is True
    assert rec["warmstart"] is False
    # Switch on AND single-thread pin held -> the P0 cache is effective.
    assert rec["p0_cache"] is True


def test_p0_cache_needs_the_determinism_pin(monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("MARKET_SIM_P0_CACHE", "1")
    assert env_solve_choices()["p0_cache"] is False


def test_run_config_carries_the_block(tmp_path, monkeypatch):
    _clear_env(monkeypatch)
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "1")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "config.yaml").write_text(yaml.safe_dump({"iso": "ERCOT"}))
    assert environment_block()["env_solve_choices"]["p1_basis_seed"] is True
    path = write_run_config(tmp_path, run_dir, iso="ERCOT")
    payload = json.loads(path.read_text())
    assert payload["environment"]["env_solve_choices"]["p1_basis_seed"] is True
    assert set(ENV_SOLVE_KNOBS) >= {"MARKET_SIM_P1_BASIS_SEED"}
