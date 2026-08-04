"""The capacity-hindcast harness emits the artifact FC-7 reads (FFR-3K).

``forecast_verdict.score_fc7`` row 1 requires ``<bundle>/run_config.json``.
The harness wrote only ``run_config.yaml``, so every T1-H / T1-X / T1-FF leg
FAILed FC-7 *"run_config.json absent"* BY CONSTRUCTION — the unfixed analogue
of the FFR-3D blocker-7 defect in ``run_full_horizon.py`` (writer added at
``34c2f25``, its call-site binding fixed at ``ea7cd5d``). Both historical
defects shipped green because no test exercised the RUNNER'S OWN TAIL: the
FFR-3D suite called the writer with a test-invented kwarg shape, and the
hindcast harness had no artifact-emission test at all.

These tests therefore drive ``main()`` end to end — argparse, build_config,
the governance prints, the meta assembly, the write site — with only the
solve seam stubbed (``run_scenario`` and the post-solve guards), and then
assert against the artifact THROUGH THE SCORER'S OWN LOADER. A regression
that renames, relocates, or stops emitting the artifact fails here even if a
helper function still behaves.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from market_sim.results import cache as cachemod
from scripts import forecast_verdict as FV
from scripts import run_capacity_hindcast as H

#: One argv per structurally distinct tier the harness produces, with the
#: rubric tier its bundle is scored under (``None`` = not a battery-named
#: tier here; the full-forward leg still must emit the artifact).
TIER_LEGS = {
    "t1h_plain_hindcast": ([], "t1h"),
    "t1x_crossover": (["--crossover"], "t1x"),
    "t1ff_full_forward": (
        [
            "--forward-from-base",
            "--arm",
            "realized",
            "--vintage",
            "2023",
            "--start-year",
            "2023",
            "--end-year",
            "2025",
        ],
        None,
    ),
}

STUB_KEY = "deadbeefcafe0123"


def _run_main(tmp_path: Path, monkeypatch, extra_argv: list[str]) -> Path:
    """Run ``main()`` with the solve seam stubbed; return the bundle root.

    The stub ``run_scenario`` writes the resolved ``config.yaml`` exactly where
    ``results.cache.save_result`` would, plus a sentinel key no request object
    carries — so the tests can prove the artifact is sourced from the BUNDLE'S
    dump (the resolution), never re-dumped from the pre-solve request.
    """
    out_dir = tmp_path / "bundle"

    def fake_run_scenario(config, iso):
        run_dir = out_dir / iso / STUB_KEY
        run_dir.mkdir(parents=True, exist_ok=True)
        config.to_yaml_full(run_dir / "config.yaml")
        resolved = yaml.safe_load((run_dir / "config.yaml").read_text())
        resolved["resolution_sentinel"] = "bundle-config-yaml"
        (run_dir / "config.yaml").write_text(yaml.safe_dump(resolved))
        return STUB_KEY

    # main() re-points the global cache root at the out-dir; registering the
    # current value with monkeypatch restores it for the rest of the session.
    monkeypatch.setattr(cachemod, "CACHE_ROOT", cachemod.CACHE_ROOT)
    monkeypatch.setattr(H, "run_scenario", fake_run_scenario)
    monkeypatch.setattr(
        H,
        "load_ledgers_for_run",
        lambda bundle: {2022: {"bridge": True}, 2023: {}},
    )
    monkeypatch.setattr(H, "assert_pipeline_from_vintage", lambda *a, **k: [])
    monkeypatch.setattr(H, "assert_forward_drivers", lambda *a, **k: [])

    rc = H.main(["--iso", "ERCOT", "--out-dir", str(out_dir), *extra_argv])
    assert rc == 0
    return out_dir


@pytest.mark.parametrize("leg", sorted(TIER_LEGS))
def test_bundle_root_carries_the_artifact_fc7_reads(tmp_path, monkeypatch, leg):
    """After a run, ``run_config.json`` exists at the bundle root and parses."""
    extra_argv, _ = TIER_LEGS[leg]
    out_dir = _run_main(tmp_path, monkeypatch, extra_argv)

    path = out_dir / "run_config.json"
    assert path.exists(), (
        "run_config.json missing at the bundle root — FC-7 row 1 reads exactly "
        "this path and FAILs 'run_config.json absent' without it (FFR-3K)"
    )
    payload = json.loads(path.read_text())

    # Sourced VERBATIM from the bundle's own resolved config.yaml — the
    # sentinel exists only in the on-disk resolution, never in the request.
    sc = payload["scenario_config"]
    assert sc["resolution_sentinel"] == "bundle-config-yaml"
    assert sc["mode"] == "forecast"
    assert payload["scenario_config_source"].endswith("config.yaml")
    assert payload["run_dir"] == str(out_dir / "ERCOT" / STUB_KEY)

    # Run-outcome keys mirror the meta's vocabulary.
    assert payload["iso"] == "ERCOT"
    assert payload["cache_key"] == STUB_KEY
    assert payload["solved_years"] == [2023]
    assert payload["bridged_years"] == [2022]
    assert payload["kind"] == json.loads((out_dir / "meta.json").read_text())["kind"]

    # The request-side YAML dump stays: build_forecast_dof_ledger still falls
    # back to it (FFR-3K kept it deliberately — this pin makes removal loud).
    assert (out_dir / "run_config.yaml").exists()


@pytest.mark.parametrize(
    "leg", [k for k, (_, tier) in sorted(TIER_LEGS.items()) if tier]
)
def test_score_fc7_row1_passes_on_the_emitted_artifact(tmp_path, monkeypatch, leg):
    """FC-7 row 1 PASSes when fed the artifact through the scorer's own loader.

    This is the end-to-end contract the bug broke: the battery invokes
    ``forecast_verdict`` with ``--run-config <bundle>/run_config.json``, whose
    loader feeds ``score_fc7``. Before FFR-3K that path FAILed on every leg of
    both tiers, carrying no information about leg quality.
    """
    extra_argv, tier = TIER_LEGS[leg]
    out_dir = _run_main(tmp_path, monkeypatch, extra_argv)

    rc = FV._load_config(out_dir / "run_config.json")
    rows = FV.score_fc7({"run_config": rc}, tier, "ERCOT")
    (row1,) = [r for r in rows if r["row"] == "run_config"]
    assert row1["status"] == FV.PASS, row1
