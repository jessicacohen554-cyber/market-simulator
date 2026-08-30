#!/usr/bin/env python
"""FFR-9C-PROMOTE — declare and measure the ERCOT forecast lane's stage-B cache epoch.

Per-run probe / calibration record for owner card **D-30** (signed 2026-08-11,
sitting Addendum AK.8): promoting FFR-9C **stage B** (R-a + R-b + R-d, plus the
two capacity-screen control-recipe flags they were measured on top of) as the
ERCOT forecast default via ``ISOConfig.default_scenario_overrides`` — the D-29
seam from the same sitting (``scripts/probes/_arm3arm_cache_epoch.py`` is this
probe's model).

The promotion itself landed on ``main`` as ``a71fc84d`` (PR #3888), a commit
whose own subject read "[INCOMPLETE - do not push]" — merged before its author's
session could complete the rule-28 registration. Sitting Addendum AQ recorded
the consequence: **the epoch fired undeclared.** This probe is the declaration's
measured half; the pins live in
``tests/unit/config/test_ercot_stageb_arming.py``.

It computes cache keys off the LIVE config and solves nothing. Three reads:

* **The GLOBAL pin must not move.** ``ScenarioConfig().cache_key()`` is computed
  with no ISO override applied, and all five stage-B fields stay registered
  ``_CACHE_KEY_OPTIONAL_FIELDS`` members at their field defaults — so the pinned
  ``603c2498bf71d21d`` is unmoved by the arming. This is the CI verdict the
  lane waits on (``tests/regression/test_persisted_identity``).
* **The ERCOT forecast lane's resolved default key MOVES.** That move IS the
  declared cache epoch: ``062d440558103f81`` (pre-arm) →
  ``8d9ef77edb3e44cb`` (armed). Every ERCOT forecast/hindcast bundle produced
  under the pre-arm resolution — FH-5's ERCOT legs included — is superseded as
  a baseline, and none is silently re-used (each armed value differs from its
  registered field default and therefore ENTERS the digest).
* **No other ISO's resolution moves.** Rule 25 ``[R-ISO-SCOPE]``: the five
  non-ERCOT ISOs construct and resolve with both capacity screens ``False``,
  keys unchanged by the arming (``scenarios.py`` raises at construction for a
  non-ERCOT config that arms the restoration flag, so this is doubly held).

The pre-arm pole is reconstructed by ``dataclasses.replace``-ing the resolved
config's five stage-B fields back to their ``ScenarioConfig`` field defaults —
NOT by passing the default values to the constructor, which
``apply_iso_scenario_defaults`` would re-arm (a caller value equal to the field
default is indistinguishable from unset; see
``docs/handoffs/FINDING-ffr-9c-iso-override-precedence-2026-08-12.md``).

Usage::

    uv run python scripts/probes/_ffr9c_stageb_cache_epoch.py
    uv run python scripts/probes/_ffr9c_stageb_cache_epoch.py --json out.json
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_SRC = _ROOT / "src"
for _p in (str(_SRC), str(_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402
from market_sim.config.scenarios import (  # noqa: E402
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)

# The pinned default-config cache key (tests/regression/test_persisted_identity).
PINNED_DEFAULT_KEY = "603c2498bf71d21d"
# The D-30 epoch poles (PREREG-ffr-9c-promote-stageb-2026-08-12.md §1.6 / §2;
# re-verified 2026-08-13 at 9c52ea8 by the FFR-9C-PROMOTE continuation lane).
PRE_ARM_KEY = "062d440558103f81"
ARMED_KEY = "8d9ef77edb3e44cb"

# The five promoted fields and their D-30 values (PREREG §1.6).
STAGE_B = {
    "capacity_screen_unified_lookahead": True,
    "capacity_screen_scarcity_restoration": True,
    "entry_pipeline_aware_signal": True,
    "smr_available_year": 2030,
    "vre_procurement_additions_enabled": True,
}

# ERCOT armings that landed AFTER D-30 on the same seam. The D-30 poles above
# are declared relative to a resolution that carries stage B and NOTHING
# later, so the live resolved config is stripped of these before either pole
# is evaluated — otherwise this probe would falsely report the D-30 epoch
# broken every time a later arming moves the live key. Each entry cites its
# own epoch declaration; its probe owns the live pole.
#   D12-A (owner ruling Q15, 2026-08-30): entry_margin_exhaustion +
#   entry_forward_reserve_leg — 8d9ef77edb3e44cb -> 68a207068509f2b0,
#   declared by scripts/probes/_d12a_arming_cache_epoch.py.
POST_D30_ARMINGS = (
    "entry_margin_exhaustion",
    "entry_forward_reserve_leg",
)

OTHER_ISOS = ("CAISO", "MISO", "NYISO", "NEISO", "PJM")


def main() -> int:
    """Measure the three epoch reads and fail loudly on any mismatch."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", type=Path, default=None, help="write reads to JSON")
    args = parser.parse_args()

    failures: list[str] = []
    reads: dict[str, object] = {}

    # --- read 1: the GLOBAL pin is unmoved --------------------------------
    global_key = ScenarioConfig().cache_key()
    reads["global_pin"] = global_key
    if global_key != PINNED_DEFAULT_KEY:
        failures.append(f"GLOBAL pin moved: {global_key} != {PINNED_DEFAULT_KEY}")
    unregistered = [f for f in STAGE_B if f not in _CACHE_KEY_OPTIONAL_FIELDS]
    if unregistered:
        failures.append(
            f"stage-B fields missing from _CACHE_KEY_OPTIONAL_FIELDS: {unregistered}"
        )

    # --- read 2: the ERCOT epoch — resolved key moves between the poles ---
    live = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
    armed_values = {f: getattr(live, f) for f in STAGE_B}
    reads["ercot_resolved_values"] = armed_values
    if armed_values != STAGE_B:
        failures.append(f"ERCOT resolution wrong: {armed_values} != {STAGE_B}")

    # Evaluate the D-30 poles at the D-30 posture: strip the post-D-30
    # armings (see POST_D30_ARMINGS) from the live resolution first.
    defaults = ScenarioConfig(iso="ERCOT")
    resolved = dataclasses.replace(
        live, **{f: getattr(defaults, f) for f in POST_D30_ARMINGS}
    )
    armed_key = resolved.cache_key()
    pre_arm = dataclasses.replace(
        resolved, **{f: getattr(defaults, f) for f in STAGE_B}
    )
    pre_arm_key = pre_arm.cache_key()
    reads["ercot_armed_key"] = armed_key
    reads["ercot_pre_arm_key"] = pre_arm_key
    if armed_key != ARMED_KEY:
        failures.append(
            f"armed ERCOT key {armed_key} != declared epoch pole {ARMED_KEY}"
        )
    if pre_arm_key != PRE_ARM_KEY:
        failures.append(
            f"pre-arm ERCOT key {pre_arm_key} != declared pole {PRE_ARM_KEY}"
        )
    if armed_key == pre_arm_key:
        failures.append("epoch did not fire: armed and pre-arm keys collide")

    # --- read 3: no other ISO moves (rule 25) ------------------------------
    reads["other_isos"] = {}
    for iso in OTHER_ISOS:
        cfg = apply_iso_scenario_defaults(ScenarioConfig(iso=iso), iso)
        screens = (
            cfg.capacity_screen_unified_lookahead,
            cfg.capacity_screen_scarcity_restoration,
        )
        reads["other_isos"][iso] = {"screens": screens, "key": cfg.cache_key()}
        if screens != (False, False):
            failures.append(f"{iso} screens moved: {screens}")

    print(json.dumps(reads, indent=1, default=str))
    if args.json:
        args.json.write_text(json.dumps(reads, indent=1, default=str) + "\n")
        print(f"wrote {args.json}")

    if failures:
        for f in failures:
            print(f"FAIL: {f}", file=sys.stderr)
        return 1
    print("ALL EPOCH READS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
