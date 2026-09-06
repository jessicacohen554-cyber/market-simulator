"""SCN-WS1c zero-LP verification: the D-1 FLOOR repair (owner ruling S2).

Runs identically before and after the code change, so `--tag before` / `--tag after`
produce two JSON snapshots the gate compares. Evaluates the LIVE resolver chain
(resolve_policy_bundle -> apply_iso_scenario_defaults -> resolve_carbon_price), the
same chain SCN-WS1a's committed phase-0 instrument evaluated, plus cache_key()
stability and the committed-run_config posture census.

Gates (PRECOMMIT-scn-ws1c-2026-09-06.md section 4):
  G1  after == the committed phase-0 `floor` column, all 450 cells
  G2  after differs from `head` in exactly the 3 x 25 CAISO/NYISO/NEISO x tight cells
  G3  every cache_key identical before -> after; 0 of 90 committed run_configs on the
      changed branch
"""
import json
import subprocess
import sys

sys.path.insert(0, "src")

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from market_sim.config.scenario_resolvers import resolve_policy_bundle
from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy.carbon import resolve_carbon_price

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]
BUNDLES = ["current", "tight", "rollback"]
YEARS = list(range(2026, 2051))


def snapshot() -> dict:
    """Resolved carbon $/t and cache_key per ISO x bundle, plus the default key."""
    out = {"trajectory": {}, "cache_keys": {}, "default_cache_key": ScenarioConfig().cache_key()}
    for iso in ISOS:
        out["trajectory"][iso] = {}
        for bundle in BUNDLES:
            raw = ScenarioConfig(iso=iso, mode="forecast", policy_bundle=bundle)
            cfg = apply_iso_scenario_defaults(resolve_policy_bundle(raw), iso)
            out["trajectory"][iso][bundle] = {
                str(y): round(resolve_carbon_price(cfg, y), 2) for y in YEARS
            }
            out["cache_keys"][f"{iso}/{bundle}"] = cfg.cache_key()
        # backcast keeper posture (path "zero", state pricing on) - the keeper lane
        keeper = ScenarioConfig(iso=iso, mode="backcast")
        out["cache_keys"][f"{iso}/backcast-keeper"] = keeper.cache_key()
        out["trajectory"][iso]["backcast"] = {
            str(y): round(resolve_carbon_price(keeper, y), 2) for y in (2023, 2024, 2025)
        }
    return out


def run_config_census() -> dict:
    """Every tracked run_config.json: does any reach the changed branch?"""
    files = sorted(
        subprocess.run(
            ["git", "ls-files", "*run_config.json"], capture_output=True, text=True
        ).stdout.split()
    )
    on_changed_branch, keys = [], {}
    for f in files:
        d = json.load(open(f))
        sc = d.get("scenario_config", d)
        key = d.get("cache_key") or sc.get("cache_key")
        if key:
            keys[f] = key
        if (
            sc.get("mode") != "backcast"
            and sc.get("carbon_price_path") not in ("zero", None)
            and sc.get("state_carbon_pricing", True)
        ):
            on_changed_branch.append(f)
    return {"n_files": len(files), "n_keys": len(keys), "keys": keys,
            "on_changed_branch": on_changed_branch}


if __name__ == "__main__":
    tag = sys.argv[sys.argv.index("--tag") + 1] if "--tag" in sys.argv else "run"
    payload = {"tag": tag, "snapshot": snapshot(), "run_configs": run_config_census()}
    path = f"docs/handoffs/scn-ws1c/verify-floor-{tag}.json"
    json.dump(payload, open(path, "w"), indent=1)
    print(f"wrote {path}")
    print(f"  default cache_key      : {payload['snapshot']['default_cache_key']}")
    print(f"  tracked run_configs    : {payload['run_configs']['n_files']} "
          f"({payload['run_configs']['n_keys']} with a recorded key)")
    print(f"  ON THE CHANGED BRANCH  : {len(payload['run_configs']['on_changed_branch'])}")
    for iso in ISOS:
        t = payload["snapshot"]["trajectory"][iso]
        print(f"  {iso:6s} tight 2030/2050 = {t['tight']['2030']:8.2f} / {t['tight']['2050']:8.2f}"
              f"   current 2030/2050 = {t['current']['2030']:8.2f} / {t['current']['2050']:8.2f}")
