"""Full-keeper A/B probe: CAISO net-summer vs temperature-dependent derate.

Reproduces the caiso65_seam_envelope_clock keeper's exact configuration
(calibration_flags dict + the CAISO-specific structural flags that keeper
carries but does not surface in calibration_flags -- capacity_deliverability_
limits, the RA must-offer/bridge suite, per-hub intertie) for ALL THREE train
years (2023-2025, rule 16) and flips only ``temp_dependent_derate`` -- the
flat EIA-860 net-summer/_SUMMER_CLASS_DERATE capacity treatment vs the new
per-class dry-bulb temperature curve (fleet.generators_to_fleet_arrays).

caiso_ra_mustoffer, caiso_ra_min_load_frac, caiso_gas_floor_frac,
caiso_solar_deliverability and caiso_solar_endogenous_spill are already the
backcast_config per-ISO default for CAISO (pipeline/backcast_config.py) and
would reproduce even if omitted; they are passed explicitly anyway so this
script fully documents the keeper's config rather than relying on an
implicit default. capacity_deliverability_limits, caiso_ra_startup_bridge,
caiso_ra_bridge_decommit, caiso_per_hub_intertie and caiso_perhub_firm_base
are NOT backcast_config defaults -- they are genuine keeper-specific choices
and must be passed explicitly or the repro silently drops them.

Registered as a PROBE (caiso-68), never a keeper -- promotion is a separate
owner decision after reviewing results across all six ISOs (temp-derate
keeper-rerun playbook, docs/handoffs/temp-derate-keeper-rerun-playbook-2026-07.md).

Usage: python scripts/probes/_caiso_tempderate_ab.py {main|ablation}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    ablate = mode == "ablation"
    out = ROOT / ("caiso68_tempderate" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        cf["years"],  # all three years in one call (rule 16) -- not [year]
        cf["iso"],
        cf["hours"],
        _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        retiree_cems_cap=cf["retiree_cems_cap"],
        ct_mustrun_per_plant=cf["ct_mustrun_per_plant"],
        ct_mustrun_floor_frac=cf["ct_mustrun_floor_frac"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        ercot_rtordpa_overlay=cf["ercot_rtordpa_overlay"],
        ercot_dam_as_overlay=cf["ercot_dam_as_overlay"],
        ercot_dam_as_overlay_from_year=cf["ercot_dam_as_overlay_from_year"],
        ercot_dam_as_scarcity_threshold=cf["ercot_dam_as_scarcity_threshold"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": 6,
            "offer_curve_smoothing_exp": 1.0,
            "offer_curve_smoothing_mid": None,
        },
        priced_interchange=cf["priced_interchange"],
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags -- read from run_config.json's
        # scenario_config (see module docstring).
        capacity_deliverability_limits=True,
        caiso_ra_mustoffer=True,
        caiso_ra_min_load_frac=0.26,
        caiso_ra_startup_bridge=True,
        caiso_ra_bridge_decommit=True,
        caiso_gas_floor_frac=0.8,
        caiso_solar_deliverability=True,
        caiso_solar_endogenous_spill=True,
        caiso_per_hub_intertie=True,
        caiso_perhub_firm_base=True,
        caiso_corridor_flow_limit=True,
        temp_dependent_derate=True,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "caiso68_tempderate").name if ablate else None,
        note=(
            f"temp-derate full-keeper {mode} -- caiso65_seam_envelope_clock "
            "config + temp_dependent_derate, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
