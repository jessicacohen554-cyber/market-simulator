"""Tests for the golden-scenario band regression (W2-P5, plan §2.3).

Two things this module guards:

* **Fixture presence (always runs, per-PR):** the golden fixture
  (``tests/golden/ercot_2026_2032.json``) and its ``run_config.json``
  provenance sidecar exist and are well-formed. Cheap, no solve.
* **Band regression (`test_golden_bands_hold`, gated `RUN_GOLDEN_FORECAST=1`):**
  a fresh solve of the pinned reference scenario (real HiGHS, ~7 ERCOT LP
  years) stays within every banded quantity's tolerance from plan §2.3.
  Weekly CI tier, never per-PR -- mirrors
  ``tests/test_forecast_invariants.py``'s ``RUN_SLOW_FORECAST`` gate.

A FAIL here is a finding, never grounds to auto-regenerate -- see
``scripts/golden_forecast_bands.py``'s ``REGEN_POLICY`` and plan §2.3.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from scripts import golden_forecast_bands as G


def test_golden_fixture_present_and_well_formed():
    """The golden fixture and its run_config sidecar must exist and parse."""
    if not G.GOLDEN_PATH.exists():
        pytest.fail(
            f"{G.GOLDEN_PATH} is missing -- seed it with "
            "`python scripts/golden_forecast_bands.py seed --reason ...` "
            "(see docs/handoffs/forecast-validation-program-2026-07.md §2.3)."
        )
    payload = json.loads(G.GOLDEN_PATH.read_text())
    for key in ("scenario", "provenance", "bands", "golden"):
        assert key in payload, f"golden fixture missing top-level key {key!r}"
    assert payload["provenance"].get("seeded_git_sha"), (
        "golden fixture missing provenance.seeded_git_sha"
    )
    assert G.RUN_CONFIG_PATH.exists(), (
        f"{G.RUN_CONFIG_PATH} (full config provenance) must be committed "
        "alongside the golden fixture"
    )
    run_config = json.loads(G.RUN_CONFIG_PATH.read_text())
    assert run_config["git_sha"] == payload["provenance"]["seeded_git_sha"], (
        "run_config.json's git_sha must match the golden fixture's "
        "provenance.seeded_git_sha -- they are seeded together"
    )
    assert "scenario_config" in run_config


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("RUN_GOLDEN_FORECAST") != "1",
    reason="set RUN_GOLDEN_FORECAST=1 to solve the real 7-year ERCOT reference forecast",
)
def test_golden_bands_hold():
    """Solve the pinned reference scenario fresh and check every golden band.

    A failure means the current code moved a banded quantity (annual CO2,
    end-year capacity by fuel, annual load-weighted price, total system cost,
    or cumulative builds by tech) outside its tolerance versus the golden
    seeded at ``provenance.seeded_git_sha``. Per the regeneration policy
    (plan §2.3; CLAUDE.md rule 23's frozen-against-residuals spirit applied
    to a forecast fixture): this is a finding to root-cause, never a reason
    to widen a band or silently re-seed. If the movement is the intended
    consequence of a landed change, regenerate explicitly and cite it:
    ``python scripts/golden_forecast_bands.py seed --force --reason "..."``,
    then commit the new golden alongside that change.
    """
    if not G.GOLDEN_PATH.exists():
        pytest.skip(f"no golden fixture at {G.GOLDEN_PATH}; seed it first")
    payload = json.loads(G.GOLDEN_PATH.read_text())

    with tempfile.TemporaryDirectory(prefix="golden-forecast-bands-test-") as tmp:
        run, _run_dir, _config = G.solve_reference(Path(tmp))
        computed = G.compute_metrics(run)

    violations = G.check_bands(payload["golden"], computed)
    assert not violations, (
        f"{len(violations)} golden-band violation(s) vs golden seeded at "
        f"{payload['provenance']['seeded_git_sha']}:\n"
        + "\n".join(violations)
        + f"\n{G.REGEN_POLICY}"
    )
