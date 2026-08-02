"""Tests for the golden-scenario band regression (W2-P5, plan §2.3).

Two things this module guards:

* **Fixture presence (always runs, per-PR):** the golden fixture
  (``tests/golden/ercot_2026_2040.json``) and its ``run_config.json``
  provenance sidecar exist and are well-formed. Cheap, no solve.
* **Band regression (`test_golden_bands_hold`, gated `RUN_GOLDEN_FORECAST=1`):**
  a fresh solve of the pinned reference scenario (real HiGHS, 15 ERCOT LP
  years, 2026-2040) stays within every banded quantity's tolerance from
  plan §2.3.
  Weekly CI tier, never per-PR -- mirrors
  ``tests/regression/test_forecast_invariants.py``'s ``RUN_SLOW_FORECAST`` gate.

A FAIL here is a finding, never grounds to auto-regenerate -- see
``scripts/golden_forecast_bands.py``'s ``REGEN_POLICY`` and plan §2.3.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import tempfile
from pathlib import Path

import pytest

from market_sim.config.scenarios import ScenarioConfig
from scripts import golden_forecast_bands as G

STALENESS_WAIVER_PATH = G.GOLDEN_DIR / "staleness_waiver.json"


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


def _config_identity_drift() -> tuple[str, str, dict[str, tuple]]:
    """Return ``(seeded_key, current_key, {field: (seeded, current)})``.

    The seeded ``run_config.json`` stores the FULL ``asdict`` of the config
    that produced the golden plus its ``cache_key``; rebuilding
    ``REFERENCE_SCENARIO_KWARGS`` today and re-hashing it therefore answers
    exactly "has any cache-key-affecting default moved since the seed?". The
    key is path-invariant (``ScenarioConfig.cache_key`` folds checkout-absolute
    paths to sentinels), so this is stable across checkouts and CI runners.
    """
    run_config = json.loads(G.RUN_CONFIG_PATH.read_text())
    seeded_fields = run_config["scenario_config"]
    current = ScenarioConfig(**G.REFERENCE_SCENARIO_KWARGS)
    gone = "<field deleted since seed>"
    added = "<field did not exist at seed>"
    drift = {
        name: (seeded_fields[name], getattr(current, name, gone))
        for name in sorted(seeded_fields)
        if seeded_fields[name] != getattr(current, name, gone)
    }
    # Fields ADDED to ScenarioConfig since the seed are drift too — the seeded
    # payload simply has no entry for them.
    for name in sorted(set(vars(current)) - set(seeded_fields)):
        drift[name] = (added, getattr(current, name))
    return run_config["cache_key"], current.cache_key(), drift


def test_golden_fixture_config_identity_is_current():
    """The golden fixture must still describe the config the code produces today.

    FR-26 of the forecast-readiness audit (2026-07-30): the band check is
    ``slow``- and env-gated, so a golden seeded at an obsolete config identity
    produced **no red anywhere** — it silently stopped being a regression
    guard. This test is the staleness expiry that makes the drift loud.

    A drift is NOT a licence to reseed: reseeding solves 15 forecast years and
    is owner-decision D-7 (audit §4 Phase 2), so a known, dated,
    owner-routed drift may be carried in ``tests/golden/staleness_waiver.json``
    — and this test hard-FAILS once that waiver expires, or immediately if the
    drift is undeclared. The waiver names the SEEDED key (the stable side), so
    an unrelated default flip in a parallel session does not turn this red;
    what the waiver buys is a deadline, not silence.
    """
    seeded_key, current_key, drift = _config_identity_drift()
    drift_report = "\n".join(
        f"  {name}: seed={seeded!r} -> now={now!r}"
        for name, (seeded, now) in drift.items()
    )

    if current_key == seeded_key:
        assert not STALENESS_WAIVER_PATH.exists(), (
            f"{STALENESS_WAIVER_PATH} declares the golden fixture stale, but "
            f"the reference scenario now hashes to the seeded key {seeded_key} "
            "again — the waiver is dead scaffolding, delete it (rule 26)."
        )
        return

    assert STALENESS_WAIVER_PATH.exists(), (
        "The golden fixture is STALE: a fresh "
        f"ScenarioConfig(**REFERENCE_SCENARIO_KWARGS) hashes to {current_key}, "
        f"but tests/golden/ercot_2026_2040.run_config.json was seeded at "
        f"{seeded_key}. {len(drift)} cache-key-affecting field(s) moved:\n"
        f"{drift_report}\n"
        "The golden bands therefore no longer describe this code. Either "
        "reseed under the D-7 owner authorization "
        "(scripts/golden_forecast_bands.py REGEN_POLICY), or record the "
        "staleness in tests/golden/staleness_waiver.json with an expiry date."
    )
    waiver = json.loads(STALENESS_WAIVER_PATH.read_text())
    assert waiver.get("seeded_cache_key") == seeded_key, (
        f"{STALENESS_WAIVER_PATH} waives seeded key "
        f"{waiver.get('seeded_cache_key')!r}, but the committed fixture was "
        f"seeded at {seeded_key!r} — the waiver does not describe this fixture."
    )
    expires = dt.date.fromisoformat(waiver["expires"])
    assert dt.date.today() <= expires, (
        f"The golden-fixture staleness waiver EXPIRED on {expires}. The fixture "
        f"has been stale since it was seeded at {seeded_key} (now {current_key}; "
        f"{len(drift)} field(s) moved):\n{drift_report}\n"
        f"{waiver.get('on_expiry', '')}"
    )


@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("RUN_GOLDEN_FORECAST") != "1",
    reason="set RUN_GOLDEN_FORECAST=1 to solve the real 15-year ERCOT reference forecast (2026-2040)",
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
