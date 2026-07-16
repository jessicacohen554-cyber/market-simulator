"""caiso-87 probe: south-corridor surplus-clean import depth on the caiso-84 keeper recipe.

RECIPE-IDENTICAL to the caiso-84 keeper
(`scripts/probes/_caiso84_gas_spot_level_ab.py` — the caiso-80 recipe +
`caiso_citygate_spot_level`). The single delta is ``caiso_dsw_surplus_clean=
True``: the measured surplus-hour WEIM clean import depth on the Palo Verde /
Path-46 corridor (FINDING-caiso82 §3 "measured clean DEPTH" lane;
FINDING-caiso86b closed the measured-ladder-PRICE alternative on its LOYO
gates). In hours whose measured Palo Verde hub price sits below the remote
gas-CCGT floor (HR 6.97 × measured SoCal citygate weekly + $2.5 VOM, no
carbon), a DSW_surplus_clean tranche (EF 0, Path-46 wheel, priced at the
measured hub by the per-hub injector) carries the corridor's measured
depth-in-surplus (p95 net import over trigger hours: 5,312/4,792/5,472 MW
2023/24/25; CV 0.056, LOYO ≤12.5%) net of the shaped firm block. Fossil rungs
unchanged (they price flow beyond the clean depth — secondary dispatch); the
corridor ATC envelope still caps delivered flow. Zero new fitted scalars
(trigger = existing coupling HR × measured gas print; depth = measured p95).

A2 attribution this mechanism answers (2026-07-16 session, caiso-84 replay):
model May-2023 λ matches the carbon-wedged DSW rungs in 43% of hours (+20%
PNW_midC) while the ACTUAL clears below every model offer in 69% of hours at
hub parity with no wedge; same signature across Apr-Jun 2024. The wedge
(wheel + border × EF: +$16-22) ≈ the +14-22 $/MWh morning/midday soft-month
gaps.

PRE-REGISTERED directions (BEFORE the solve):
1. Soft-month C3a closes toward actual: May-2023 monthly mean $29.5 → toward
   $15.5 actual (target ~$17); Jun-2023 $36.2 → toward $25.8 (~$27); the
   analogous 2024 Apr/May/Jun (+7.1/+11.5/+8.6) and 2025 soft months narrow.
   Full-year C3a improves from +11.9/+12.6/+19.3%.
2. Winter 2023 (Jan/Feb) ~unchanged: the trigger evaluates only on MEASURED
   hub hours and the Jan-Feb 2023 retention gap stays non-surplus; the
   winter gas-level lane (caiso-84) is closed and must not reopen.
3. C2 gas moves DOWN (the disclosed tension: cheaper clean imports displace
   gas burn; 2024/25 already -5..-7%). Reported honestly, never tuned around
   (rule 15). C1 CC_REGULAR 2024 (+6.67 TWh over) likely narrows for the
   same reason.
4. Midday net-import VOLUME may rise further above the measured TI (the
   model already over-imports midday ~+2 GW); reported honestly — the
   corridor ATC envelope is the physical bound.
5. C3c tail ~unchanged (the true-tail hours are corridor-capped — caiso-85
   proved median headroom 0 in scarcity-tail hours; this tranche adds no
   capability beyond the ATC cap).
6. C5a/C6/C7/C8 hold; no floor, no forcing, no D-2 row (a capability with
   pmin 0).
FAIL conditions (pre-registered): a load-bearing gate flips PASS→FAIL, or
the winter months reopen (Jan-2023 monthly gap grows past band-edge noise) —
then the trigger construction is re-examined against its own gates, never
tuned to the residual.

LOYO note: nothing is pooled — each year rides its own measured depth and
trigger series (the caiso-80/82/84 construction class), so the three
registered years ARE the per-year independent reads; the estimation-stage
CV/LOYO gates (FINDING-caiso86b §/ interchange_config block) are the
cross-year transfer check, already passed.

Registered as a PROBE, all three years in one invocation (rule 16), NO
zero-forcing ablation twin (rule 21 as amended 2026-07-14).

Usage: python scripts/probes/_caiso87_dsw_surplus_clean_ab.py main
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
            "caiso-87 carries no ablation twin (rule 21 amended 2026-07-14); "
            "run with 'main'."
        )
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    out = ROOT / "caiso87_dsw_surplus_clean"
    out.mkdir(parents=True, exist_ok=True)

    # The caiso-84 keeper recipe, unchanged, plus the SINGLE caiso-87 delta:
    # the measured surplus-clean import depth on the south corridor.
    overrides = dict(cf["coal_prb_sigmoid_overrides"])
    overrides["caiso_ra_bridge_startup_aware"] = True
    overrides["hydro_dispatch_envelope"] = True
    overrides["caiso_firm_import_shape"] = True
    overrides["caiso_demand_clock_realign"] = True
    overrides["caiso_firm_import_selfschedule"] = True
    overrides["caiso_supply_consistent_demand"] = True
    overrides["caiso_citygate_spot_level"] = True  # the caiso-84 keeper delta
    overrides["caiso_dsw_surplus_clean"] = True  # THE caiso-87 delta

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
            "caiso-87 surplus-clean import depth main -- caiso-84 keeper "
            "recipe + caiso_dsw_surplus_clean=True (measured WEIM surplus "
            "clean depth, south corridor; FINDING-caiso82 par.3 / "
            "FINDING-caiso86b), 2023-2025"
        ),
    )
    print(f"DONE main -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "main")
