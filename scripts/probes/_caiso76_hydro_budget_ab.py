"""caiso-76 probe: measured 2025 hydro energy budget on the caiso-75 recipe.

Single-delta A/B against caiso-75 (`scripts/probes/_caiso75_demand_clock_ab.py`):
the caiso-65 keeper config on the SP15-split topology with
``ct_netload_drag=False``, ``caiso_ra_bridge_startup_aware=True``,
``hydro_dispatch_envelope=True``, ``caiso_firm_import_shape=True`` and
``caiso_demand_clock_realign=True``, plus ONE mechanism:
``hydro_backfill_year=2024`` + ``hydro_eia930_monthly=True`` — the measured
conventional-hydro budget correction
(FINDING-caiso76-hydro-budget-2026-07-11.md).

THE STEP-0 ROOT CAUSE of the C2 2025 gas excess (+6.5%, the promotion
blocker): the 2025 EIA-923 vintage is a monthly-survey-only early release
carrying 26 of ~185 CAISO hydro plants, 12.32 of the measured 21.32 TWh
(EIA-930 ``NG: WAT``). The missing 9.0 TWh of zero-carbon inflow energy is
served by gas (+4.4 TWh vs the deflated EIA-930 family actual), imports
(model 40.7 vs measured 35.9 TWh) and un-curtailed solar (+3.6 TWh vs 930),
and drives the C5a 2025 CO2 blowout (+46%) and the flat off-peak CC posture
(model CC overnight +1.2-1.7 GW, belly +0.9-2.0 GW vs CAMPD, evening ramp
LATE at h17). 2023/2024 ride final annual vintages and match 930 within
0.5/1.2 TWh.

The fix is the existing early-release machinery built for exactly this
failure mode (NEISO-2025 precedent in the flag help): carry plants that
reported in 2024 but not in the early 2025 vintage at their 2024 monthly
generation (per-plant coverage + MW envelope), then repin every year's
monthly budget to the measured EIA-930 ``NG: WAT`` total (2023
23.90->24.40, 2024 21.48->22.68, 2025 12.32->21.32 TWh). Rule-13/14
admissible: a measured physical inflow input with a forward analogue by
construction (the forecast path keeps its climatology budget; the
correction regenerates for any future backcast year on the same
early-release cadence and dies when the final 923 file lands).

Pre-registered directions (rubric v2.4, all three train years):
  - 2025 (the delta year): gas family falls toward the +-2.5% band from
    +6.5%; imports fall toward the measured 35.9 TWh; C5a 2025 (+46%)
    falls materially but is NOT expected to clear the 10% target band —
    the committed bench CO2 actual (21.68 Mt) is itself derived off the
    same preliminary-923 class generation and is understated (DISCLOSED
    bench-vintage caveat, an intake follow-up, never a tuning target).
    Off-peak CC flatness eases (hydro peak-shaves); C4 gas r rises;
    C7/C8 protective gates must hold.
  - 2024: budget +1.2 TWh -> gas falls ~1 TWh; C1 CC_REGULAR (+7.64 TWh)
    eases, direction firm, magnitude small.
  - 2023: budget +0.5 TWh; near-neutral. With backfill_year=2024, five
    plants reporting in 2024 but not in 2023's FINAL vintage are carried
    in (+0.42 TWh pre-repin); the 930 repin rescales the total back to
    the measured 24.40 TWh so only per-plant shares shift (DISCLOSED).
  - CISO 930 ``NG: WAT`` includes pumped-storage net output (no separate
    PS series), so the repin target slightly understates conventional
    hydro by PS pumping losses — the same like-for-like note as the
    hydro_dispatch_envelope cap (DISCLOSED, documented approximation).

Registered as PROBES (main + zero-forcing ablation twin). The budget
correction is a measured input and survives the zero-forcing ablation by
construction. Evening-CC commitment design (docs/handoffs/
caiso-evening-cc-commitment-design-2026-07.md) is NOT built: its §0
re-measure gate on the caiso-75 line returned +1.7/+1.1/+0.3 GW evening
(2023/24/25) with the 2025 gap under the 0.5 GW threshold and the 2025
belly flipped to model-OVER (-0.8 GW) — re-measure again on this line.

Usage: python scripts/probes/_caiso76_hydro_budget_ab.py {main|ablation}
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
    out = ROOT / ("caiso76_hydro_budget" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    # caiso-75 recipe (startup-aware bridge + hydro envelope + firm import
    # shape + demand clock) via the generic scenario-override channel
    # (caiso-66/70/72/73/74/75 precedent); the caiso-76 delta rides the
    # dedicated solve_and_persist hydro kwargs.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True

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
        # THE caiso-76 DELTA: measured conventional-hydro budget correction.
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
        # CAISO-specific structural flags carried by the keeper but absent
        # from calibration_flags (caiso-69/70/73/74/75 script docstrings).
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
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "caiso76_hydro_budget").name if ablate else None,
        note=(
            f"caiso-76 measured 2025 hydro budget correction {mode} -- "
            "caiso-75 recipe + hydro_backfill_year=2024 + "
            "hydro_eia930_monthly=True single delta, 2023-2025"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
