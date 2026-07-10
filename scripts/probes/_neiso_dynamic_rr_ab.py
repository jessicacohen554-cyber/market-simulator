"""Full-keeper A/B probe: NEISO measured dynamic reserve requirements (Limb A).

Reproduces the current NEISO keeper's (2026-07-09-neiso-56-reserve-coopt,
bundle ``neiso56_reserve_coopt``) exact solve configuration for 2023-2025 in
one bundle (rule 16) and flips only ``neiso_dynamic_reserve_requirements`` on
— the measured as-enforced ISO-NE hourly reserve requirements (ISO Express
"Hourly Reserve Requirements", the ``reserve-requirements`` clean datatype)
replacing the static published 1,800/1,200/600 MW in the keeper's in-LP
energy+reserve co-optimization (``reserve_config._neiso_design``).

Why this probe: the keeper's co-opt is DORMANT at the static requirements
(reserve dual $0.00 in all 26,280 train hours) while the measured system
30-minute requirement EXCEEDS the static 1,800 MW in every one of those
hours (mean ~2,300 MW; peak 3,167 MW in the Jan-2025 cold snap that carries
the C3c 12h >$300 DA tail). This is the exact NEISO analogue of the NYISO
issue-#1344 measured-requirement channel: a rule-13-admissible market-design
INPUT (regenerates forward as published-static-base + condition rules on
forward states), fitted to nothing — measured reserve PRICES stay
validation-only. Expected effects if the mechanism engages: reserve-short
cold-snap hours price the RCPF into the LMP (C3c tail formation above the
dual-fuel oil-parity cap) and reserve/spread value reaches the
Northfield/Bear Swamp pumped-storage fleet (C5b). A still-dormant result is
a legitimate finding and is reported and registered as such (rule 1).

The keeper's ``meta.json`` records every ``solve_and_persist`` kwarg (mostly
1:1 by name; a few renamed — ``_RENAME``), so this probe builds its kwargs
from meta.json rather than hand-translating the recipe — the validated
``_neiso_reserve_coopt_ab.py`` pattern that produced the keeper.

Also runs the rule-20 zero-forcing ablation twin (mode "ablation").

Usage:
    python scripts/probes/_neiso_dynamic_rr_ab.py main
    python scripts/probes/_neiso_dynamic_rr_ab.py ablation
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "neiso56_reserve_coopt"

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
    "energy_reserve_coopt",  # keeper value True, set explicitly below
    "neiso_dynamic_reserve_requirements",  # the A/B variable (absent in the
    # keeper's pre-flag meta; skipped defensively for re-runs)
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
    out = ROOT / ("neiso57_dynamic_rr" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2023, 2024, 2025],
        "NEISO",
        8760,
        _load_reference(),
        run_dir=out,
        commitment=True,
        energy_reserve_coopt=True,
        neiso_dynamic_reserve_requirements=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "neiso57_dynamic_rr").name if ablate else None,
        note=(
            f"dynamic-reserve-requirements full-keeper {mode} -- "
            "2026-07-09-neiso-56-reserve-coopt config + "
            "neiso_dynamic_reserve_requirements (measured ISO-NE hourly "
            "requirements replacing static 1800/1200/600), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
