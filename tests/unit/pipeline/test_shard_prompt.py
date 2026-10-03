"""Guards for scripts/shard_prompt.py — the emitted SOLVE-SHARD prompt.

R-50 (closeout-PJM-nuc, 2026-10-03): swap is bounded by free disk, so the
prompt must run ``prepare_solve_container.py`` before every data step, and a
PJM recipe that arms ``pjm_da_virtual_bids`` must fetch the gitignored
DA-virtuals parquets instead of hard-stopping on their absence.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts import shard_prompt as sp

SHA = "a" * 40


def _bundle(tmp_path: Path, scenario: dict) -> str:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    (bundle / "run_config.json").write_text(json.dumps({"scenario_config": scenario}))
    return str(bundle)  # absolute: REPO / abs == abs


def _render(iso: str, bundle: str, sets: list[str] | None = None) -> str:
    return sp.render(iso, 2021, SHA, "lane-x", bundle, sets or [], None, 90)


def test_prepare_solve_container_runs_before_every_data_step(tmp_path: Path) -> None:
    text = _render("PJM", _bundle(tmp_path, {"pjm_da_virtual_bids": True}))
    prep = text.index("python3 scripts/prepare_solve_container.py`")
    for step in ("hydrate_data.py", "regenerate_clean.py", "fetch_pjm_da_virtuals.py"):
        assert prep < text.index(step), step
    # The env-pin eval stays where the solve runs, right before replay_keeper.
    solve = text.split("SOLVE (sequential", 1)[1]
    assert solve.index("--emit-exports") < solve.index("replay_keeper.py")


@pytest.mark.parametrize(
    ("iso", "scenario", "sets", "expected"),
    [
        ("PJM", {"pjm_da_virtual_bids": True}, [], True),
        ("PJM", {"pjm_da_virtual_bids": False}, [], False),
        ("PJM", {}, ["pjm_da_virtual_bids=true"], True),
        ("PJM", {"pjm_da_virtual_bids": True}, ["pjm_da_virtual_bids=false"], False),
        ("MISO", {"pjm_da_virtual_bids": True}, [], False),
    ],
)
def test_da_virtuals_fetch_line_follows_the_recipe(
    tmp_path: Path, iso: str, scenario: dict, sets: list[str], expected: bool
) -> None:
    text = _render(iso, _bundle(tmp_path, scenario), sets)
    line = "fetch_pjm_da_virtuals.py --years 2021 --feeds hrl_da_incs_decs"
    assert (line in text) is expected
    if expected:
        assert "gitignored" in text and "never commit" in text
