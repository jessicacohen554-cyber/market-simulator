"""p2_state versioned envelope + stale-config rebuild (run_calibration_full).

Covers the A4 hardening of the P2 post-process path:

* ``_save_p2_state`` writes a v2 envelope (``format_version`` / ``git_sha`` /
  ``state``); ``_load_p2_state`` unwraps it and treats a bare dict as v1.
* ``_rebuild_p2_config`` reconstructs a current ``ScenarioConfig`` from a stale
  pickled one. The committed 2026-era pickles carry a config missing fields
  added since, so the old ``with_overrides`` (``dataclasses.replace``) call
  raised ``AttributeError``. We prove the rebuild path works AND that the naive
  ``with_overrides`` on the stale instance still fails (the bug it fixes).
* ``replay_keeper.build_kwargs`` ignores the new ``environment`` meta key.
"""

from __future__ import annotations

import dataclasses
import gzip
import pickle
from pathlib import Path

import pytest

from market_sim.config.scenarios import ScenarioConfig
from scripts import run_calibration_full as rcf


def _stale_config() -> ScenarioConfig:
    """A current config mutated to look like a stale pickle.

    Drops a ``default_factory`` field (simulating a field added since the
    pickle was written — ``dataclasses.replace`` can't read it off the instance)
    and adds a since-removed attribute.
    """
    cfg = ScenarioConfig()
    factory_fields = [
        f.name
        for f in dataclasses.fields(ScenarioConfig)
        if f.default_factory is not dataclasses.MISSING
    ]
    assert factory_fields, "expected at least one default_factory field"
    del cfg.__dict__[
        factory_fields[0]
    ]  # a field the current __init__ has, pickle lacks
    cfg.__dict__["removed_old_field_xyz"] = 123  # a since-removed field
    return cfg


def test_naive_with_overrides_raises_on_stale_config() -> None:
    """The pre-fix path (`with_overrides` on the stale instance) still raises."""
    stale = _stale_config()
    with pytest.raises(AttributeError):
        stale.with_overrides(commitment_enabled=True, commitment_screen_coal=False)


def test_rebuild_p2_config_recovers_a_valid_config() -> None:
    """`_rebuild_p2_config` rebuilds a valid config + applies P2 overrides."""
    stale = _stale_config()
    cfg = rcf._rebuild_p2_config(stale, screen_coal=True)
    assert isinstance(cfg, ScenarioConfig)
    assert cfg.commitment_enabled is True
    assert cfg.commitment_screen_coal is True
    # Dropped field came back with its default; removed field did not survive.
    assert not hasattr(cfg, "removed_old_field_xyz")
    assert cfg.cache_key()  # a fully-valid config hashes without error


def test_save_load_p2_state_v2_envelope_roundtrips(tmp_path: Path) -> None:
    """`_save_p2_state` writes a v2 envelope; `_load_p2_state` returns state."""
    state = {"year": 2024, "config": ScenarioConfig(), "hello": "world"}
    rcf._save_p2_state(tmp_path, 2024, state)
    written = tmp_path / "p2_state" / "2024.pkl.gz"
    assert written.is_file()

    with gzip.open(written, "rb") as fh:
        raw = pickle.load(fh)
    assert raw["format_version"] == rcf._P2_STATE_FORMAT_VERSION
    assert "git_sha" in raw
    assert raw["state"] == state

    loaded = rcf._load_p2_state(written)
    assert loaded == state


def test_load_p2_state_treats_bare_dict_as_v1(tmp_path: Path) -> None:
    """A pre-envelope (bare-dict) pickle loads unchanged as v1."""
    state = {"year": 2023, "config": ScenarioConfig()}
    path = tmp_path / "v1.pkl.gz"
    with gzip.open(path, "wb") as fh:
        pickle.dump(state, fh, protocol=pickle.HIGHEST_PROTOCOL)
    assert rcf._load_p2_state(path) == state


def test_rebuild_from_committed_pickle_if_present() -> None:
    """End-to-end: the smallest committed p2_state pickle rebuilds cleanly."""
    bundles = (
        "stgas_netload_drag_v1",
        "ctharcut_3yr",
        "ctharcut_pp_3yr",
        "coalprb_foll078_3yr",
    )
    repo = Path(__file__).resolve().parent.parent
    candidates = [
        p
        for b in bundles
        for p in (repo / "results" / "calibration" / b / "p2_state").glob("*.pkl.gz")
        if p.is_file()
    ]
    if not candidates:
        pytest.skip("no committed p2_state pickles on disk (sparse checkout)")
    pkl = min(candidates, key=lambda p: p.stat().st_size)
    state = rcf._load_p2_state(pkl)  # bare dict -> v1 passthrough
    cfg = rcf._rebuild_p2_config(state["config"], screen_coal=False)
    assert cfg.commitment_enabled is True
    assert cfg.commitment_screen_coal is False


def test_build_kwargs_ignores_environment_key() -> None:
    """`replay_keeper.build_kwargs` treats `environment` as provenance."""
    from scripts.replay_keeper import build_kwargs

    meta = {
        "iso": "MISO",
        "years": [2023],
        "hours": 8760,
        "passes": ["P1"],
        "gas_prices": {"2023": 3.0},
        "environment": {"python_version": "3.11.9", "packages": {"numpy": "1.99"}},
    }
    kwargs = build_kwargs(meta)  # must not raise "keys not bound"
    assert "environment" not in kwargs
