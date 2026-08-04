"""The FF-2D emit helper refuses to overwrite, and sources the config dump (FFR-3X).

FFR-3K made both harnesses write their own ``run_config.json`` from the solved
config, demoting ``scripts/_ff2d_emit_run_config.py`` to a HISTORICAL-bundle
helper — but run on a post-fix bundle it would silently OVERWRITE the
producer-written artifact with a reconstruction: a provenance downgrade, the
exact record-provenance defect class FFR-3R closed structurally. And its
hindcast arm read ``meta.json`` — a ~30-key harness record the scorer then
treated as THE ScenarioConfig, the FFR-2E propagation channel, with the second
edge that a config field the meta omits reads as absent downstream (FC-2 row 4
branches on ``"reserve_margin_build_enabled" in sc``; FC-7 row 1 scores the
flag-surface size). FFR-3R §6.1, closed here.

These tests pin both halves:

* the guard — the helper ERRORS (never skips quietly, never writes) when
  ``run_config.json`` already exists, and the existing bytes are untouched;
* the source — the hindcast arm emits the bundle's own ``run_config.yaml``
  (the harness's full ScenarioConfig dump) verbatim, never the meta, and a
  bundle with no dump is refused rather than reconstructed from meta.

Without the FFR-3X change this file fails wholesale: the pre-fix helper was
top-level argv code (no ``main``), overwrote unconditionally, and merged
``meta.json`` into its output.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from market_sim.config.scenarios import ScenarioConfig
from scripts import _ff2d_emit_run_config as EMIT
from scripts import forecast_verdict as FV

#: Planted only in the on-disk run_config.yaml (never a ScenarioConfig field),
#: so its presence in the output proves a verbatim read of THAT file — a
#: re-derived or meta-merged payload cannot carry it.
SENTINEL = {"resolution_sentinel": "bundle-run-config-yaml"}

#: A realistic hindcast meta.json: harness labels + run outcome, ~30 keys in
#: real bundles. None of the non-config keys may leak into the emitted config.
META = {
    "iso": "PJM",
    "kind": "hindcast",
    "bundle": "pjm-2021-2025-fixture",
    "cache_key": "deadbeefcafe0123",
    "solved_years": [2021, 2022],
    "variant": "realized",
    "capacity_market_clearing": True,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_config_dump(path: Path) -> None:
    """Write a real full ScenarioConfig dump (+ sentinel) at ``path``."""
    ScenarioConfig(mode="forecast", hindcast=True).to_yaml_full(path)
    full = yaml.safe_load(path.read_text())
    full.update(SENTINEL)
    path.write_text(yaml.safe_dump(full, sort_keys=True))


def _producer_artifact() -> str:
    """A producer-written run_config.json body (the write_run_config shape)."""
    return (
        json.dumps(
            {
                "scenario_config_source": "results/hindcast/x/PJM/key/config.yaml",
                "scenario_config": {"iso": "PJM", "mode": "forecast"},
                "run_dir": "results/hindcast/x/PJM/key",
            },
            indent=2,
        )
        + "\n"
    )


def _hindcast_bundle(tmp_path: Path, *, existing_json: bool) -> Path:
    """A hindcast bundle with meta + config dump, optionally pre-carrying the artifact."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "meta.json").write_text(json.dumps(META, indent=2))
    _write_config_dump(bundle / "run_config.yaml")
    if existing_json:
        (bundle / "run_config.json").write_text(_producer_artifact())
    return bundle


def _summary_dir(tmp_path: Path, *, existing_json: bool) -> Path:
    """A full-horizon out-dir whose summary points at a cache run_dir."""
    out_dir = tmp_path / "fh"
    run_dir = tmp_path / "cache" / "PJM" / "deadbeefcafe0123"
    run_dir.mkdir(parents=True)
    out_dir.mkdir()
    _write_config_dump(run_dir / "config.yaml")
    (out_dir / "full_horizon_summary.json").write_text(
        json.dumps({"iso": "PJM", "run_dir": str(run_dir)})
    )
    if existing_json:
        (out_dir / "run_config.json").write_text(_producer_artifact())
    return out_dir


# ===========================================================================
# The guard: refuse-if-exists, loudly, bytes untouched
# ===========================================================================
def test_hindcast_refuses_existing_run_config_json(tmp_path):
    bundle = _hindcast_bundle(tmp_path, existing_json=True)
    target = bundle / "run_config.json"
    before = _sha256(target)

    with pytest.raises(SystemExit) as exc:
        EMIT.main(["hindcast", str(bundle)])

    msg = str(exc.value)
    assert "REFUSING" in msg, "the refusal must be loud, not a quiet skip"
    assert str(bundle) in msg, "the refusal must name the bundle"
    assert _sha256(target) == before, "the existing artifact must be byte-untouched"


def test_summary_refuses_existing_run_config_json(tmp_path):
    out_dir = _summary_dir(tmp_path, existing_json=True)
    target = out_dir / "run_config.json"
    before = _sha256(target)

    with pytest.raises(SystemExit) as exc:
        EMIT.main(["summary", str(out_dir / "full_horizon_summary.json")])

    assert "REFUSING" in str(exc.value)
    assert _sha256(target) == before


def test_refusal_names_no_override_flag(tmp_path):
    """The refusal offers no in-band overwrite path — deletion is the only, manual one."""
    bundle = _hindcast_bundle(tmp_path, existing_json=True)
    with pytest.raises(SystemExit) as exc:
        EMIT.main(["hindcast", str(bundle)])
    assert "no override flag" in str(exc.value)
    assert "--" not in str(exc.value), "must not advertise a flag that does not exist"


# ===========================================================================
# FFR-3R §6.1: the hindcast arm's source is run_config.yaml, never meta.json
# ===========================================================================
def test_hindcast_sources_run_config_yaml_never_meta(tmp_path):
    bundle = _hindcast_bundle(tmp_path, existing_json=False)

    out = EMIT.main(["hindcast", str(bundle)])

    written = json.loads(out.read_text())
    # Verbatim from the dump: the sentinel only that file carries.
    assert written["resolution_sentinel"] == SENTINEL["resolution_sentinel"]
    # The dump natively carries what the old arm hand-added as literals.
    assert written["mode"] == "forecast"
    assert written["hindcast"] is True
    # The §6.1 omission edge: a real config field a meta never contains.
    assert "reserve_margin_build_enabled" in written
    # No meta leakage: harness-label / run-outcome keys must not appear.
    assert "bundle" not in written
    assert "cache_key" not in written
    assert "solved_years" not in written
    # The full flag surface FC-7 row 1 scores (a ~30-key meta cannot reach it).
    assert len(written) >= FV.CONFIG_FULL_SURFACE_MIN_KEYS


def test_emitted_artifact_passes_fc7_row1_through_scorer_loader(tmp_path):
    bundle = _hindcast_bundle(tmp_path, existing_json=False)
    out = EMIT.main(["hindcast", str(bundle)])

    art = {"run_config": FV._load_config(str(out))}
    row = next(r for r in FV.score_fc7(art, "t1h", "PJM") if r["row"] == "run_config")
    assert row["status"] == FV.PASS, row["detail"]


def test_hindcast_refuses_bundle_without_config_dump(tmp_path):
    """No run_config.yaml -> refuse; reconstructing from meta.json is the defect."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "meta.json").write_text(json.dumps(META, indent=2))

    with pytest.raises(SystemExit) as exc:
        EMIT.main(["hindcast", str(bundle)])

    assert "run_config.yaml" in str(exc.value)
    assert not (bundle / "run_config.json").exists(), "nothing may be written"


# ===========================================================================
# The legitimate path still works
# ===========================================================================
def test_summary_arm_still_writes_when_absent(tmp_path):
    out_dir = _summary_dir(tmp_path, existing_json=False)

    out = EMIT.main(["summary", str(out_dir / "full_horizon_summary.json")])

    assert out == out_dir / "run_config.json"
    written = json.loads(out.read_text())
    assert written["resolution_sentinel"] == SENTINEL["resolution_sentinel"]
    assert written["mode"] == "forecast"
