"""SCN-WS5A-POLICY-NYISO zero-LP instrument.

Reproduce (zero LP, THE PIN's code, no worktree and no blob fetch):

    PIN=$(mktemp -d)
    git archive bdfb3095e9fa0cd2bec3f4e843f320b42588c72b src configs scripts \
        | tar -x -C "$PIN"
    PYTHONPATH="$PIN/src:$PIN" uv run python <this file> "$PIN"

Committed output beside this file as the matching .txt (SCN-WS5A-POLICY-NYISO
ADDENDUM 2, 2026-09-07).
"""
from __future__ import annotations
import sys
from pathlib import Path
PIN = Path(sys.argv[1]); sys.path.insert(0, str(PIN / "src")); sys.path.insert(0, str(PIN))
from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition, resolve_policy_bundle
from market_sim.config.topology_variant import set_caiso_fsno_partition
from market_sim.matrix import matrix_configs
from scripts.run_full_horizon import apply_set_overrides, parse_set_overrides
ISO = "NYISO"
def resolve(cfg):
    if cfg.iso != ISO: cfg = cfg.with_overrides(iso=ISO)
    cfg = resolve_policy_bundle(cfg); set_caiso_fsno_partition(False)
    return apply_iso_scenario_defaults(cfg, ISO)
base = ScenarioConfig.from_yaml(PIN / "configs/scenarios/nyiso_scenario_base_2026_2030.yaml")
if base.iso != ISO: base = base.with_overrides(iso=ISO)
cfgs = matrix_configs(base, SweepDefinition.from_yaml(PIN / "configs/scenario_campaign_matrix.yaml"))
cfgs["CES-P60"] = apply_set_overrides(cfgs["CES-P30"], parse_set_overrides(["federal_ces_premium_usd_per_mwh=60.0"]))
EXPECT = {"REF":"f10cc93084b4c0db","LOAD-HI":"c2ceaefa4afafcda","CES-P10":"3c96d694c18e5547",
 "CES-P20":"9da7c76372c98406","CES-P30":"89a70dd1140c6731","CES-T80":"eb1b0e1df942db47",
 "VOL-MID":"9528d708b81b5074","VOL-HI":"893acae55a1a898f","CES-P20+VOL-HI":"566335c8ca37dc17",
 "ALL-CLEAN":"e13b0d801b1ffce1","CAP-STATE-TIGHT":"76c60ac152400146","CES-P60":None}
for case, exp in EXPECT.items():
    k = resolve(cfgs[case]).cache_key()
    mark = "NEW" if exp is None else ("OK " if k == exp else "MISMATCH")
    print(f"{case:16s} {k}  {mark}")
