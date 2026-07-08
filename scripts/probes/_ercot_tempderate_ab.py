"""One-off A/B probe: ERCOT 2023 net-summer vs temperature-dependent derate.

Reproduces the ercot46_clock_steamgas keeper's exact calibration_flags (read
from its run_config.json) for the single 2023 year and flips only
``temp_dependent_derate`` -- the flat EIA-860 net-summer/_SUMMER_CLASS_DERATE
capacity treatment vs the new per-class dry-bulb temperature curve
(fleet.generators_to_fleet_arrays). ERCOT zone dry-bulb TMAX hits 42-44 C in
summer 2023 (well above the CT/CC 15 C ISO reference), so this is a strong
test of whether the reshape recovers missed scarcity hours/price-tail shape.

Single-year, never registered on the dashboard: a throwaway diagnostic probe
per CLAUDE.md rule 15, not a keeper (which must cover 2023-2025).

Usage: python scripts/probes/_ercot_tempderate_ab.py {off|on}
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot46_clock_steamgas"


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    temp_on = mode == "on"
    out = ROOT / ("ercot_tempderate23_on" if temp_on else "ercot_tempderate23_off")
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2023],
        "ERCOT",
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
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.45,
        },
        priced_interchange=cf["priced_interchange"],
        temp_dependent_derate=temp_on,
        note=(
            f"temp-derate A/B ({mode}) — keeper ercot46_clock_steamgas config, "
            "2023 only (summer TMAX 42-44 C zones / scarcity-tail probe)"
        ),
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
