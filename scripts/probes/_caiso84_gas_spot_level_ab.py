"""caiso-84 probe: measured daily-spot gas LEVEL on the caiso-80 keeper recipe.

RECIPE-IDENTICAL to the caiso-80 keeper
(`scripts/probes/_caiso80_supply_consistent_demand_ab.py`) — same flags, same
measured inputs, zero new free parameters. The single delta is
``caiso_citygate_spot_level=True``: the CAISO gas hub overlay
(`gas_hub_basis_overlay`, default-on for CAISO) is re-levelled from the EIA
N3050CA3 monthly citygate *survey* (an LDC portfolio *acquisition cost*) onto
the measured California Composite Average daily citygate *spot* series the
marginal cost-based DEB actually bids at (`data/raw/gas-prices/
caiso_citygate_daily.csv`), keeping BOTH within-month shape and monthly level
on the daily series (`fuel._caiso_hub_daily_gas_prices(spot_level=True)`); the
+$0.46 CAISO_CITYGATE_TRANSPORT_ADDER still applies, coverage is unchanged
(survey-uncovered months stay on the base EIA-923 series). Rule-15 swap of one
measured EIA series for another whose boundary matches the marginal-offer
representation (FINDING-caiso-winter-gas-level-2026-07-15).

PRE-REGISTERED directions (FINDING §1/§4): 2023 Jan lambda ~$222 -> ~$130-145;
Feb ~$96 -> ~$66-72; Mar/Oct-2023 move UP toward actual (the wedge reverses
sign there — a fit-chasing knob could not do this); C3a-2023 +32.5% -> low
teens or better; C3b 0.562 -> <=~0.25; C3c 667 -> low hundreds or less; C4
improves; C2 gas under-shoot narrows (cheaper gas -> more burn); model imports
may fall somewhat. C1/C6/C7/C8 must hold.

Registered as a PROBE, all three years in one invocation (rule 16), NO
zero-forcing ablation twin (rule 21 as amended 2026-07-14). Mechanism-change
verdict flips are scored leave-one-year-out within 2023-2025 before promotion
(the construction is per-year measured data — each year rides its own series).

Usage: python scripts/probes/_caiso84_gas_spot_level_ab.py main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "caiso65_seam_envelope_clock"


def main(mode: str) -> None:
    if mode != "main":
        raise SystemExit(
            "caiso-84 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso84_gas_spot_level"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-80 keeper recipe, unchanged, plus the SINGLE caiso-84 delta:
    # the measured daily-spot gas LEVEL swap.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # THE caiso-84 delta

    solve_and_persist(
        cf["years"],  # all three years in one call (rule 16)
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
        prb_overrides=overrides,
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
        # Standing measured hydro budget correction (caiso-76, rules 1/14).
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags (caiso-69/70/73/74/75/76/77 script docstrings).
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
        ct_netload_drag=False,
        note=(
            "caiso-84 measured daily-spot gas LEVEL main -- caiso-80 keeper "
            "recipe + caiso_citygate_spot_level=True (survey->daily-spot level "
            "swap, FINDING-caiso-winter-gas-level-2026-07-15), 2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
