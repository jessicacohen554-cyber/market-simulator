"""Full-keeper A/B probe: NYISO measured dynamic reserve requirements (#1344).

Reproduces the current NYISO keeper's (2026-07-07-nyiso-56-measured-zonal,
bundle ``nyiso56_measuredshares``) exact solve configuration for 2023-2025 in
one bundle (rule 16) and flips only ``nyiso_dynamic_reserve_requirements`` on
— the measured hourly requirement series derived from the published LRR
schedule + logged Thunderstorm-Alert windows
(``data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_{year}.csv``,
``scripts/derive_nyiso_reserve_requirements_hourly.py``, Ask B of
``docs/handoffs/nyiso-data-asks-2026-07.md``) replacing the static published
requirements in the keeper's in-LP energy+reserve co-optimization
(``reserve_config._nyiso_design``).

Why this probe: the keeper's downstate reserve families are DORMANT at the
static requirements — NYC holds 2-3x the requirement even in the hours
reality prices >$300 (the ledgered C3c tail: 10/12/42 h actual vs ~0
modeled) — while the published SENY 30-minute requirement is an hourly step
schedule peaking at 1,800 MW, 500 MW above the static 1,300 the overlay
enforced, in every peak hour of 2023-2025. This is the exact NYISO analogue
of the NEISO Limb-A probe (``_neiso_dynamic_rr_ab.py``): a rule-13-admissible
market-design INPUT (regenerates forward as published-base + condition rules
on forward states), fitted to nothing — measured reserve PRICES stay
validation-only. Expected effects if the mechanism engages: SENY/NYC families
bind in peak hours and price their RCPF steps into the downstate LBMP (C3c
tail formation); TSA hours zero the NYC/SENY requirements by the published
rule. A still-dormant result is a legitimate finding and is reported and
registered as such (rule 1). The derived series is a documented LOWER BOUND
in non-TSA hours (the B1 condition-varying increments are request-only), so
residual tail shortfall is expected and ledgered, not tuned away.

The keeper's ``meta.json`` records every ``solve_and_persist`` kwarg (mostly
1:1 by name; a few renamed — ``_RENAME``), so this probe builds its kwargs
from meta.json rather than hand-translating the recipe — the validated
``_neiso_dynamic_rr_ab.py`` pattern.

Also runs the rule-20 zero-forcing ablation twin (mode "ablation").

Usage:
    python scripts/probes/_nyiso_dynamic_rr_ab.py main
    python scripts/probes/_nyiso_dynamic_rr_ab.py ablation
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "nyiso56_measuredshares"

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
    "commitment",  # set explicitly below (keeper value False, unchanged)
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
    "nyiso_dynamic_reserve_requirements",  # the A/B variable (absent in the
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
    out = ROOT / ("nyiso57_dynamic_rr" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2023, 2024, 2025],
        "NYISO",
        8760,
        _load_reference(),
        run_dir=out,
        commitment=False,
        energy_reserve_coopt=True,
        nyiso_dynamic_reserve_requirements=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "nyiso57_dynamic_rr").name if ablate else None,
        note=(
            f"dynamic-reserve-requirements full-keeper {mode} -- "
            "2026-07-07-nyiso-56-measured-zonal config + "
            "nyiso_dynamic_reserve_requirements (measured hourly LRR "
            "schedule + TSA windows replacing static requirements), "
            "2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
