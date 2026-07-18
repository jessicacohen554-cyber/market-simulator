"""caiso-99 B-leg: caiso-97 keeper recipe + measured battery dispatch-shape envelope.

CAISO-99 Mechanism B (FINDING-caiso98 §7B, owner-authorized): the keeper
already dispatches the measured EIA-860 per-vintage battery fleet with the
intra-year COD ramp live (the CAISO-99 discovery — `storage_vintage_ramp=True`
rides the `backcast_config` CAISO base, so caiso-98's Mechanism-A flag-flip was
True->True and byte-identical), yet it charge-arbitrages that fleet at up to
nameplate in the midday belly and rides its own charging demand up the supply
curve (belly over-price +10.9/+9.0/+8.4, ENTIRELY in model-charging hours) and
over-discharges the 2023/24 evening. The measured fleet never runs fleet-wide
near nameplate: its p95 hod rate is ~0.43-0.55 charging / ~0.48-0.66
discharging (EIA-930 CISO ``NG: OTH`` ÷ EIA-860 monthly fleet).

This B-leg is the SAME caiso-97 keeper recipe with the ONLY delta
`caiso_storage_shape_anchor=True`: battery Chg/Dis capped at
env_p95[year, hod] × power_cap[s, t] (committed rule-23 derivation
`data/raw/reference/caiso-storage-shape-envelope.csv`; pumped storage exempt).
Measured anchor only — no residual-tuned scalar (rule 25); replaces nothing and
stacks on nothing (rule 19 — the caiso-74 AS reservation stays off, its holdback
is EMBEDDED in the measured envelope). Adjudicated A/B against the same-machine
`caiso99_repro_A` (FINDING-caiso92b protocol). Pre-registered report-back
(FINDING-caiso98 §7 gates + B-specific): C1 12/12 holds; overnight lambda no
new under-price; C3c unchanged; C7/C8 PASS; belly over-price falls with NO
overshoot (belly resid must not go negative); evening under-price toward 0 with
NO cross above actual; C5a improves or holds. Registered whatever the result
(rule 15).

Usage: python scripts/probes/_caiso99_shape_B.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _caiso95_repro_A import BASE, _keeper_overrides  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"


def main() -> None:
    cf = json.loads((BASE / "run_config.json").read_text())["calibration_flags"]
    overrides = _keeper_overrides(cf)
    overrides["caiso_ra_startup_trajectory"] = True  # caiso-96 (owner carry ruling)
    overrides["caiso_dsw_daytime_evening_trim"] = True  # caiso-97 (the WP-2 delta)
    overrides["caiso_storage_shape_anchor"] = (
        True  # caiso-99 Mechanism B (the ONLY delta)
    )
    out = ROOT / "caiso99_shape_B"
    out.mkdir(parents=True, exist_ok=True)
    note = (
        "caiso-99 Mechanism B -- caiso-97 KEEPER recipe + caiso_storage_shape_anchor "
        "(measured EIA-930 NG:OTH p95 diurnal charge/discharge envelope on the "
        "battery fleet; FINDING-caiso98 s7B measured shape anchor, rule-25 "
        "measured-anchor-only), 2023-2025"
    )

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
        hydro_backfill_year=2024,
        hydro_eia930_monthly=True,
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
        caiso_offer_surface_measured=True,
        caiso_offer_surface_conditional=True,
        note=note,
    )
    print(f"DONE shape B-leg -> {out}")


if __name__ == "__main__":
    main()
