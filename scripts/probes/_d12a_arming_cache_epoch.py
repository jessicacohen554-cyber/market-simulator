#!/usr/bin/env python
"""D12-A — declare and measure the ERCOT forecast lane's entry-pair cache epoch.

Per-run probe / calibration record for owner ruling **Q15** (r#18 sitting,
2026-08-30, ``docs/handoffs/capx-director-ledger-2026-08.md`` §3): arming
``entry_margin_exhaustion`` + ``entry_forward_reserve_leg`` as the ERCOT
forecast default via ``ISOConfig.default_scenario_overrides`` — the Q10
confirm-then-arm protocol's execution on a D12-C record the owner judged
confirming-in-substance per that finding's own §4.3 clause
(``docs/handoffs/FINDING-capx-d12c-confirm-pair-2026-08-30.md``; lane record
``docs/handoffs/FINDING-capx-d12a-arming-2026-08-30.md``).
``scripts/probes/_ffr9c_stageb_cache_epoch.py`` is this probe's model.

It computes cache keys off the LIVE config and solves nothing. Four reads:

* **The GLOBAL pin must not move.** ``ScenarioConfig().cache_key()`` is
  computed with no ISO override applied, and both pair fields stay registered
  ``_CACHE_KEY_OPTIONAL_FIELDS`` members at their ``False`` field defaults —
  so the pinned ``603c2498bf71d21d`` is unmoved by the arming.
* **The ERCOT forecast lane's resolved default key MOVES.** That move IS the
  declared cache epoch: ``8d9ef77edb3e44cb`` (the D-30 stage-B pole) →
  ``68a207068509f2b0`` (D12-A armed). Every ERCOT forecast/hindcast bundle
  produced under the pre-D12-A resolution is historical record and never a
  post-epoch baseline; none is silently re-used (each armed value differs
  from its registered field default and therefore ENTERS the digest).
* **The bare T1-H construction resolves to the REGISTERED ARMED BUNDLE's
  key.** ``build_config("ERCOT", 2021, 2025, "realized")`` + resolution
  reproduces ``f061b2646bfaac8b`` — the committed
  ``ercot-2021-2025-realized-t1h-d12c-armed`` ``run_config.json`` key — so
  the registered armed bundle IS the record of the new default posture (no
  re-solve, no re-registration; the D12-C control ``28cef3500ec1fd9e`` is
  now the explicit ``--no-*`` control arm's key).
* **No other ISO's resolution moves.** Rule 25 ``[R-ISO-SCOPE]``: the five
  sister ISOs construct and resolve with both pair fields ``False``, keys
  unchanged by the arming.

The pre-arm pole is reconstructed by ``dataclasses.replace``-ing the resolved
config's pair fields back to their ``ScenarioConfig`` field defaults — NOT by
passing the default values to the constructor, which would be an EXPLICIT
control arm under the OVERRIDE-FIX precedence (a valid posture, but not the
"unset" pole this epoch declares).

Usage::

    uv run python scripts/probes/_d12a_arming_cache_epoch.py
    uv run python scripts/probes/_d12a_arming_cache_epoch.py --json out.json
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
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
# The D12-A epoch poles (measured at arming, 2026-08-30; pinned by
# tests/unit/config/test_ercot_stageb_arming.py::TestD12AArming).
PRE_ARM_KEY = "8d9ef77edb3e44cb"  # the D-30 stage-B pole
ARMED_KEY = "68a207068509f2b0"
# The registered D12-C pair's committed run_config keys (the T1-H surface).
T1H_CONTROL_KEY = "28cef3500ec1fd9e"
T1H_ARMED_KEY = "f061b2646bfaac8b"

# The two armed fields and their Q15 values (the D12-C single logical delta).
PAIR = {
    "entry_margin_exhaustion": True,
    "entry_forward_reserve_leg": True,
}

OTHER_ISOS = ("CAISO", "MISO", "NYISO", "NEISO", "PJM")


def _build_config_module():
    """Import the hindcast harness by path (a script, not a package module)."""
    path = _ROOT / "scripts" / "run_capacity_hindcast.py"
    spec = importlib.util.spec_from_file_location("run_capacity_hindcast_probe", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    """Measure the four epoch reads and fail loudly on any mismatch."""
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
    unregistered = [f for f in PAIR if f not in _CACHE_KEY_OPTIONAL_FIELDS]
    if unregistered:
        failures.append(
            f"pair fields missing from _CACHE_KEY_OPTIONAL_FIELDS: {unregistered}"
        )

    # --- read 2: the ERCOT epoch — resolved key moves between the poles ---
    resolved = apply_iso_scenario_defaults(ScenarioConfig(iso="ERCOT"), "ERCOT")
    armed_values = {f: getattr(resolved, f) for f in PAIR}
    reads["ercot_resolved_values"] = armed_values
    if armed_values != PAIR:
        failures.append(f"ERCOT resolution wrong: {armed_values} != {PAIR}")

    armed_key = resolved.cache_key()
    defaults = ScenarioConfig(iso="ERCOT")
    pre_arm = dataclasses.replace(resolved, **{f: getattr(defaults, f) for f in PAIR})
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

    # --- read 3: the bare T1-H construction = the registered armed bundle -
    rch = _build_config_module()
    t1h = apply_iso_scenario_defaults(
        rch.build_config("ERCOT", 2021, 2025, "realized"), "ERCOT"
    )
    t1h_key = t1h.cache_key()
    t1h_control = dataclasses.replace(t1h, **{f: getattr(defaults, f) for f in PAIR})
    reads["t1h_bare_key"] = t1h_key
    reads["t1h_control_key"] = t1h_control.cache_key()
    if t1h_key != T1H_ARMED_KEY:
        failures.append(
            f"bare T1-H key {t1h_key} != registered armed bundle {T1H_ARMED_KEY}"
        )
    if t1h_control.cache_key() != T1H_CONTROL_KEY:
        failures.append(
            f"T1-H pair-off key {t1h_control.cache_key()} != registered "
            f"control bundle {T1H_CONTROL_KEY}"
        )

    # --- read 4: no other ISO moves (rule 25) ------------------------------
    reads["other_isos"] = {}
    for iso in OTHER_ISOS:
        cfg = apply_iso_scenario_defaults(ScenarioConfig(iso=iso), iso)
        pair = (cfg.entry_margin_exhaustion, cfg.entry_forward_reserve_leg)
        reads["other_isos"][iso] = {"pair": pair, "key": cfg.cache_key()}
        if pair != (False, False):
            failures.append(f"{iso} pair moved: {pair}")

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
