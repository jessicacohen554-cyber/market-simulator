"""Full-keeper A/B probe: NEISO in-LP energy+reserve co-optimization (all 3 train years).

Reproduces the current NEISO keeper's (2026-07-08-neiso-55-temp-derate,
bundle ``neiso55_tempderate``) exact solve configuration for 2023-2025 in one
bundle (rule 16) and flips only ``energy_reserve_coopt`` on — the ISO-NE
system-wide energy+reserve co-optimization with the published 3-level nested
RCPF demand curves (``reserve_config._neiso_design`` /
``NEISO_RCPF_PRODUCTS``: total-30-min 1,800 MW @ $1,000, total-10-min
1,200 MW @ $1,500, 10-min-spin 600 MW @ $50; ISO-NE Market Rule 1
§III.2.7A reserve constraint penalty factors), with storage
reserve-eligible (``storage_eligible=True``).

Why this probe: the keeper's two ledgered caveats (C3c 2025 scarcity tail
0h vs 12h DA >$300; C5b 2025 storage throughput −60.2%) are adjudicated as
one winter capacity-adequacy / scarcity-price-formation gap. The winter
fuel-security mechanism family is exhausted (G-24 STRUCK 2026-07-07:
Component A+B+coldsnap-derate adopted but DORMANT). The C5b ledger names
exactly one remaining structural path: "in-LP reserve co-optimization value
reaching storage". This is that probe — real ISO-NE market structure
(energy and reserves clear jointly; RCPF shortfall prices stack into the
LMP), a rule-13-admissible design input (published requirements + penalty
factors, regenerating forward unchanged), never before probed on NEISO.
Expected effects if the mechanism engages: reserve-short cold-snap hours
price the RCPF into the LMP (C3c tail formation above the dual-fuel
oil-parity cap), and reserve value reaches the Northfield/Bear Swamp
pumped-storage fleet (C5b). A dormant result (ample-headroom NEISO fleet
clears the nested requirements inertly — the caiso-59/MISO lesson) is a
legitimate finding too and is reported as such, per rule 1.

The keeper's ``calibration_flags`` (run_config.json) is a curated subset;
``meta.json`` records every ``solve_and_persist`` kwarg (mostly 1:1 by
name; a few renamed — see ``_RENAME``), so this probe builds its kwargs
from meta.json rather than hand-translating the keeper's recipe (the
validated ``_neiso_tempderate_ab.py`` pattern that produced the keeper).

Also runs the rule-20 zero-forcing ablation twin (mode "ablation").

Usage:
    python scripts/probes/_neiso_reserve_coopt_ab.py main
    python scripts/probes/_neiso_reserve_coopt_ab.py ablation
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "neiso55_tempderate"

# meta.json key -> solve_and_persist kwarg name, where they differ.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are recorded provenance/derived values, not
# solve_and_persist kwargs — plus the A/B variable, set explicitly below.
_SKIP = {
    "timestamp",
    "iso",
    "years",
    "hours",
    "passes",
    "commitment",  # set explicitly below (keeper value, unchanged)
    "gas_prices",  # re-derived internally from reference + years
    "coal_plant_monthly_pricing",  # derived from backcast_config, not a kwarg
    "td_loss_factor",  # derived from backcast_config, not a kwarg
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
    "shared_inputs",
    "git_sha",
    "highspy_version",
    "energy_reserve_coopt",  # the A/B variable (keeper records False)
}


def _keeper_kwargs() -> dict:
    meta = json.loads((KEEPER / "meta.json").read_text())
    sig = set(inspect.signature(solve_and_persist).parameters)
    kwargs = {}
    for key, value in meta.items():
        if key in _SKIP:
            continue
        pname = _RENAME.get(key, key)
        if pname not in sig:
            raise SystemExit(f"unmapped meta.json key: {key!r}")
        kwargs[pname] = value
    return kwargs


def main(mode: str) -> None:
    kwargs = _keeper_kwargs()
    ablate = mode == "ablation"
    out = ROOT / ("neiso56_reserve_coopt" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2023, 2024, 2025],
        "NEISO",
        8760,
        _load_reference(),
        run_dir=out,
        commitment=True,
        energy_reserve_coopt=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "neiso56_reserve_coopt").name if ablate else None,
        note=(
            f"reserve-coopt full-keeper {mode} -- 2026-07-08-neiso-55-temp-derate "
            "config + energy_reserve_coopt (ISO-NE 3-level RCPF nesting, "
            "storage reserve-eligible), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
