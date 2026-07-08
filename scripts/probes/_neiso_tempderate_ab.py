"""Full-keeper A/B probe: NEISO temperature-dependent derate (all 3 train years).

Reproduces the current NEISO keeper's (2026-07-08-neiso-54-steamgas-ct,
bundle ``neiso54_steamgas_ct_drag``) exact solve configuration for 2023-2025
in one bundle (rule 16) and flips only ``temp_dependent_derate`` on -- the
flat EIA-860 net-summer / ``_SUMMER_CLASS_DERATE`` capacity treatment vs the
new per-class dry-bulb temperature curve (fleet.generators_to_fleet_arrays).

The keeper's ``calibration_flags`` (run_config.json) is a curated subset --
it is missing several keys this keeper actually uses non-default (e.g.
``reliability_floor``, ``scarcity_price_overlay``, ``neiso_gas_coldsnap_derate``,
``neiso_winter_fuel_inventory``, ``neiso_winter_fuel_mustrun``,
``tranche_startup_amortization``). ``meta.json`` records every
``solve_and_persist`` kwarg (mostly 1:1 by name; a few renamed -- see
``_RENAME`` below), so this probe builds its kwargs from meta.json rather
than hand-translating the keeper's CLI recipe
(``scripts/run_neiso54_steamgas_ct_drag.py``).

Also runs the rule-20 zero-forcing ablation twin (mode "ablation").

Usage:
    python scripts/probes/_neiso_tempderate_ab.py main
    python scripts/probes/_neiso_tempderate_ab.py ablation
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "neiso54_steamgas_ct_drag"

# meta.json key -> solve_and_persist kwarg name, where they differ.
_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# meta.json keys that are recorded provenance/derived values, not
# solve_and_persist kwargs.
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
    "temp_dependent_derate",  # set explicitly below (the A/B variable)
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
    out = ROOT / ("neiso55_tempderate" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2023, 2024, 2025],
        "NEISO",
        8760,
        _load_reference(),
        run_dir=out,
        commitment=True,
        temp_dependent_derate=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "neiso55_tempderate").name if ablate else None,
        note=(
            f"temp-derate full-keeper {mode} -- 2026-07-08-neiso-54-steamgas-ct "
            "config + temp_dependent_derate, 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
