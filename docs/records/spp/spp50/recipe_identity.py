"""SPP-50: machine-verify that the run's RECIPE is keeper-3's, field for field.

The re-baseline's claim is that keeper-3's recipe is re-solved **byte for byte** and only
its INPUTS moved. That claim is checked here rather than asserted (the form SPP-43 used
for its own promotion): every ``meta.json`` key outside provenance and every
``run_config.scenario_config`` field is compared, and the differences are printed in full.

Exactly ONE `scenario_config` difference is expected and declared in
PRECOMMIT-spp-50 §1(b): ``f923_gas_price_plausibility_screen`` — the registered gate
SPP-49 landed default-ON, absent from keeper-3's pre-field recipe. Anything else is a
finding.

The shared-input fingerprints (``meta['shared_inputs']``) are printed beside each other
too: the EIA-923 / CAMPD / outage digests should be UNMOVED (neither seam rewrites those
source parquets — they act downstream, in the fuel-price resolver and the fleet frame).

usage: uv run python docs/handoffs/spp50/recipe_identity.py <new-bundle> [<keeper-bundle>]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
KEEPER = "results/calibration/spp43_screened_B"
#: meta.json keys that record WHEN/WHERE a run happened, not WHAT it solved.
PROVENANCE = {
    "run_id", "label", "date", "timestamp", "git_sha", "basis_sha", "out_dir",
    "elapsed_s", "elapsed", "host", "environment", "shared_inputs", "passes",
    "created", "created_at", "command", "argv", "solve_surface", "version",
}
#: The one declared recipe difference (PRECOMMIT §1 (b)) — the gate SPP-49 landed
#: default-ON, which keeper-3's pre-field config could not carry.
DECLARED = {"f923_gas_price_plausibility_screen"}
#: The four OTHER ScenarioConfig fields added since keeper-3's git_sha, every one of
#: them default-``False`` and classified INERT for SPP's backcast path in the G-DRIFT
#: audit (PRECOMMIT §2) BEFORE the solve. A field absent from keeper-3's config that
#: now reports its own default is the schema growing, not the recipe moving — which is
#: why the two cases are labelled apart rather than pooled.
NEW_SINCE_KEEPER = {
    "ercot_zonal_spread_ep_referenced",
    "netload_drag_layup_window_mask",
    "pjm_thermal_accreditation_vintage",
    "spp_gas_commitment_bridge",
}


def load(bundle: Path) -> tuple[dict, dict]:
    """Return (meta, scenario_config) for a bundle."""
    meta = json.loads((bundle / "meta.json").read_text())
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    return meta, cfg


def diff(a: dict, b: dict, skip: set[str]) -> list[tuple[str, object, object]]:
    """Return [(key, keeper_value, new_value)] for every key that differs."""
    return [
        (k, a.get(k), b.get(k))
        for k in sorted(set(a) | set(b))
        if k not in skip and a.get(k) != b.get(k)
    ]


def main() -> int:
    """Print the meta / config diffs and the shared-input fingerprint pairs."""
    new = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO / "results/calibration/spp50_rebaseline"
    old = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO / KEEPER
    if not new.is_absolute():
        new = REPO / new
    m_old, c_old = load(old)
    m_new, c_new = load(new)

    md = diff(m_old, m_new, PROVENANCE)
    print(f"meta.json: {len(m_old)} vs {len(m_new)} keys; "
          f"{len(md)} difference(s) outside provenance")
    for k, x, y in md:
        print(f"  {k}: {x!r} -> {y!r}")

    cd = diff(c_old, c_new, set())
    print(f"\nrun_config.scenario_config: {len(c_old)} vs {len(c_new)} fields; "
          f"{len(cd)} difference(s)")
    absent = [k for k, _, _ in cd if k not in c_old]
    for k, x, y in cd:
        if k in DECLARED:
            mark = "DECLARED SEAM GATE"
        elif k in NEW_SINCE_KEEPER and k not in c_old:
            mark = "new field at default, INERT per G-DRIFT"
        else:
            mark = "*** UNDECLARED RECIPE MOVE ***"
        print(f"  [{mark}] {k}: {x!r} -> {y!r}")
    moved = [k for k, _, _ in cd if k in c_old]
    print(f"  -> fields present in BOTH configs that differ: {len(moved)} {moved}")
    print(f"  -> fields absent from keeper-3 (schema growth): {len(absent)}")

    print("\nshared_inputs fingerprints:")
    si_o = m_old.get("shared_inputs", {}) or {}
    si_n = m_new.get("shared_inputs", {}) or {}
    for k in sorted(set(si_o) | set(si_n)):
        a, b = str(si_o.get(k)), str(si_n.get(k))
        print(f"  {k:20s} {'SAME' if a == b else 'MOVED'}  {a.split('/')[-1]}"
              f"{'' if a == b else ' -> ' + b.split('/')[-1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
