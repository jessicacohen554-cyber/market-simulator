"""caiso-90 probe: citygate flow-date placement on the caiso-89 keeper recipe.

RECIPE-IDENTICAL to the caiso-89 keeper
(`scripts/probes/_caiso89_chp_steam_floor_ab.py` — the caiso-87 recipe +
``chp_steam_floor_p25``). The single delta is ``caiso_citygate_flow_date=
True``: the measured daily citygate prints the spot-level overlay reads
(caiso-84) are placed on their gas FLOW days (trade + 1, weekend/holiday
packages carried on a forward-fill staircase) instead of their trade days
(Lane B / C3c winter tail, 2026-07-16 handoff). The CA Composite daily spot
is a NEXT-DAY-delivery index (NGI Daily GPI via the EIA NG Weekly compact
table): a print keyed to trade day T fuels burns on T+1, and Friday's trade
covers the whole Sat-through-Monday weekend package.

Measured evidence the trade-dated placement mis-days the winter tail:
* 2023 — the model's ONLY >$200 day is Jan-12 (the $24.29 print's trade day,
  16 h, flat committed-CC repricing), a day the actual DA tail does NOT
  contain; the actual tail day Jan-13 (8 h) is that print's flow day. The
  Jan-17 $21.82 print pairs with the actual Jan-18 tail (8 h) the same way.
* 2024 — the Fri Jan-12 $17.34 print (HH $13.08 — the national freeze) is
  exactly the MLK-weekend package covering Sat Jan-13 → Tue Jan-16 flow; the
  actual DA tail is 28 h on Jan-15/16. Trade-dated linear interpolation
  instead decays Jan-13..16 toward the $5.00 Jan-16 print ($8-11/MMBtu),
  pricing the storm days at less than half their measured fuel cost.

Pure calendar-semantics correction of an already-intaken measured input
(rules 13/15): zero new scalars, no level re-tune (the closed caiso-84
winter-level lane is untouched — same prints, same months, same fallbacks;
only the day each print lands on changes), regenerates for any year from the
same EIA series, forecast path untouched. Flag-off is byte-identical
(verified). Coverage caveat carried honestly: the EIA archive has a
holiday-gap (no Dec-29-2022 / Jan-5-2023 issues), so trading days
Dec-22-2022..Jan-4-2023 do not exist in the source and the actual Jan-3..6
2023 tail cluster (22 h) remains out of reach of ANY placement of this
series — a data-source gap, not a placement defect.

PRE-REGISTERED directions (BEFORE the solve):
1. C3c-2023: the 16-h tail MOVES from Jan-12 onto Jan-13 (an actual tail
   day); Jan-18 lifts ~$177-183 -> ~$195-205 (borderline). Count stays FAIL
   (< 40 of the [40,160] band) — the win claimed is the DAYS, not the count.
2. C3c-2024: from 0 h to a tail concentrated on the Jan-13..16 flow days of
   the $17.34 package (actual: 28 h on Jan-15/16); morning/evening
   (solar-less) hours where a CT/ST rung is marginal cross $200. If the
   count reaches 26+ the year enters the PASS band.
3. C3c-2025: stays ~0 (must stay <= 10; no 2025 winter spike prints).
4. WATCH Jan-2024 (-4.9 under-priced) NARROWS (mid-Jan gas rises to the
   measured package price). Jan/Feb-2023 (+6.0/+2.5 over) must not deepen
   materially (placement, not level: monthly means move only by
   staircase-vs-interpolation resampling).
5. C1/C2 annual volumes ~unchanged; C4-Jan gas shape should improve
   (gas dispatch now spikes on the measured spike days).
FAIL conditions (pre-registered): a load-bearing gate flips PASS->FAIL, the
WATCH months deepen materially, the 2025 tail exceeds 10 h, or the moved
tail lands on days the actual tail does not contain — then the construction
is re-examined against its own evidence, never tuned to the residual.

LOYO note: year-invariant code-level calendar semantics (the caiso-78/85
precedent) — no per-year parameter is introduced; each year rides its own
measured prints.

Registered as a PROBE, all three years in one invocation (rule 16), NO
zero-forcing ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso90_citygate_flow_date_ab.py main
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
            "caiso-90 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso90_citygate_flow_date"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-89 keeper recipe, unchanged, plus the SINGLE caiso-90 delta:
    # flow-date placement of the measured daily citygate prints.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # the caiso-84 keeper delta
    overrides["caiso_dsw_surplus_clean"] = True  # the caiso-87 keeper delta
    overrides["chp_steam_floor_p25"] = True  # the caiso-89 keeper delta
    overrides["caiso_citygate_flow_date"] = True  # THE caiso-90 delta

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
            "caiso-90 citygate flow-date main -- caiso-89 keeper recipe + "
            "caiso_citygate_flow_date=True (measured daily citygate prints "
            "placed on their gas FLOW days: trade+1, weekend packages "
            "forward-filled; Lane B C3c winter tail, 2026-07-16 handoff), "
            "2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
