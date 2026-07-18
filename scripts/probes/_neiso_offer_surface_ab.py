"""Full-keeper A/B probe: NEISO condition-responsive fast-start offer surface (Limb B).

Reproduces the current NEISO keeper's (2026-07-09-neiso-56-reserve-coopt,
bundle ``neiso56_reserve_coopt``) exact solve configuration for 2023-2025 in
one bundle (rule 16), keeps Limb A on (``neiso_dynamic_reserve_requirements``
— real structure that fires in the right event, per the 2026-07-10 neiso-57
log entry), and flips ``neiso_offer_surface_conditional`` on — the MEASURED
ISO-NE fast-start DA offer surface (per-asset median top-of-curve heat-rate
multipliers, condition-binned by within-year net-load percentile, derived
once by ``scripts/data/derive_neiso_offer_surface.py`` from the public masked DA
Energy Market historical offer data; ``docs/handoffs/
neiso-limb-b-offer-surface-2026-07.md``).

Why this probe: after Limb A the C3c 2025 tail is 1h vs DA 12h >$300 — the
remaining 11 actual tail hours are summer heat-wave evening peaks where the
model's fast-start offers sit at ``HR x gas + VOM`` while the real fleet's
fast-start assets offer themselves out of the money in anticipated-tight
hours (the ERCOT G-22 "phantom sub-$200 spare" anatomy). The surface
reprices the CT_PEAKER peak band into 5 equal-capacity rungs at the measured
bin/rung multipliers, P1-only, clamped ratio >= 1 (loose hours
byte-identical). Rule-13-admissible: every parameter traces to the measured
offers conditioned on a forward-reproducible driver; nothing is fitted to a
price or volume residual, and the pre-committed honesty gate (handoff §4)
binds this probe's adjudication whatever the outcome.

The keeper's ``meta.json`` records every ``solve_and_persist`` kwarg (mostly
1:1 by name; a few renamed — ``_RENAME``), so this probe builds its kwargs
from meta.json rather than hand-translating the recipe — the validated
``_neiso_dynamic_rr_ab.py`` pattern that produced neiso-57.

Also runs the rule-20 zero-forcing ablation twin (mode "ablation").

Usage:
    python scripts/probes/_neiso_offer_surface_ab.py main
    python scripts/probes/_neiso_offer_surface_ab.py ablation
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
# solve_and_persist kwargs — plus the A/B variables, set explicitly below.
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
    "neiso_dynamic_reserve_requirements",  # Limb A, kept ON explicitly below
    "neiso_offer_surface_conditional",  # the A/B variable (absent in the
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
    out = ROOT / ("neiso58_offer_surface" + ("-ablation" if ablate else ""))
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
        neiso_offer_surface_conditional=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "neiso58_offer_surface").name if ablate else None,
        note=(
            f"conditional-offer-surface full-keeper {mode} -- "
            "2026-07-09-neiso-56-reserve-coopt config + "
            "neiso_dynamic_reserve_requirements (Limb A) + "
            "neiso_offer_surface_conditional (measured ISO-NE fast-start DA "
            "offer surface, net-load condition-binned, Limb B), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
