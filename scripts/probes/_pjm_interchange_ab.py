"""One-off A/B probe: PJM 2024 priced vs measured interchange.

Reproduces the pjm_26 keeper's exact calibration_flags (read from its
run_config.json) for a single year and flips only ``priced_interchange``.
The priced variant validates fidelity against pjm_26 2024; the measured
variant tests how much the peak-coincident measured tie-line schedule lifts
the afternoon LMP shape.

Usage: python scripts/probes/_pjm_interchange_ab.py {priced|measured}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_26"


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]  # not in calib_flags
    priced = mode == "priced"
    out = ROOT / ("pjm_repro24" if priced else "pjm_measix24")
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [2024], "PJM", 8760, _load_reference(),
        commitment=cf["commitment"],
        screen_coal=cf["commitment_screen_coal"],
        run_dir=out,
        coal_lignite_mustrun=cf["coal_lignite_mustrun"],
        coal_prb_mustrun=cf["coal_prb_mustrun"],
        coal_prb_passthrough=cf["coal_prb_passthrough"],
        outage_source=cf["outage_source"],
        coal_prb_passthrough_sigmoid=cf["coal_prb_passthrough_sigmoid"],
        coal_mustrun_per_plant=cf["coal_mustrun_per_plant"],
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={"offer_curve_smoothing_n": None,
                         "offer_curve_smoothing_exp": None,
                         "offer_curve_smoothing_mid": 0.45},
        priced_interchange=priced,
        note=f"interchange A/B ({mode}) — keeper pjm_26 config, 2024 only",
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
