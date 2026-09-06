"""capx D78-R2 key-invariance probe — zero LP.

STEP 0 of the D78-R2 charter deletes ``exempt_unit_ids`` from
:func:`apply_economic_retirements`. That is a **structural API parameter**,
not a ``ScenarioConfig`` field, so by construction it cannot move a cache
key. This probe asserts that empirically rather than by argument: it resolves

* the PJM T1-H hindcast recipe's control and arm keys through the harness
  path (``run_capacity_hindcast.build_config`` → ``apply_iso_scenario_defaults``
  → ``cache_key()``), and pins the control against the key the REGISTERED bare
  ``pjm-t1h`` sidecar carries (``frontend/data/hindcast/
  pjm-2021-2025-realized-t1h-d67arm.json`` ``meta.cache_key``); and
* one backcast key per ISO (all six) plus the global ``ScenarioConfig()``
  default key,

and writes them to ``keys_probe.json``. Run it in this tree and in a pristine
worktree at ``origin/main``; the two JSON files must be identical.

Rules 21 / 24: no field added, changed, or read that was not already read.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_capacity_hindcast import build_config  # noqa: E402

from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

# The key the registered bare ``pjm-t1h`` run carries (capx D67-ARM).
REGISTERED_PJM_T1H = "a9c66d8ea25acb9d"

BASE = dict(
    iso="PJM",
    start_year=2021,
    end_year=2025,
    variant="realized",
    vintage=2020,
    entry_screen_diagnostics=True,
)

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")


def hindcast_key(**over) -> str:
    kw = dict(BASE)
    kw.update(over)
    cfg = build_config(**kw)
    cfg = apply_iso_scenario_defaults(cfg, kw["iso"])
    return cfg.cache_key()


def backcast_key(iso: str, year: int = 2024) -> str:
    cfg = ScenarioConfig(iso=iso, mode="backcast", start_year=year, end_year=year)
    cfg = apply_iso_scenario_defaults(cfg, iso)
    return cfg.cache_key()


def main() -> None:
    out = {
        "scenario_config_default": ScenarioConfig().cache_key(),
        "pjm_t1h_control_2021_2025": hindcast_key(),
        "pjm_t1h_arm_2021_2025": hindcast_key(retirement_sector_gate=True),
        "backcast_2024_by_iso": {iso: backcast_key(iso) for iso in ISOS},
    }
    out["registered_pjm_t1h_key"] = REGISTERED_PJM_T1H
    out["control_matches_registered_pjm_t1h"] = (
        out["pjm_t1h_control_2021_2025"] == REGISTERED_PJM_T1H
    )
    out["arm_differs_from_control"] = (
        out["pjm_t1h_arm_2021_2025"] != out["pjm_t1h_control_2021_2025"]
    )
    dest = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).with_name("keys_probe.json")
    )
    dest.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
