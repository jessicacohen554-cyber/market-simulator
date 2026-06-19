"""PJM reference-price interface run: one year -> its own bundle dir.

Reproduces the pjm_28 keeper's calibration_flags but swaps the interchange
treatment: instead of the measured tie-line schedule (the keeper's
priced_interchange=False), the seam is served by the forecast-grade
reference-price interface (reference_price_interface=True, which implies
priced_interchange=True). Every other offer-curve flag is the keeper's, so the
only change is the seam, isolating its effect on PJM's net export and LMP.

One year per invocation so the three years run as parallel background jobs to
separate out-dirs (claude.md #45); merge with scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_refprice_run.py <year> <out_dir>
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_28"


def main(year: int, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]  # not in calib_flags
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [year],
        "PJM",
        8760,
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
        coal_drop_pof=cf["coal_drop_pof"],
        coal_prb_passthrough_tiered=cf["coal_prb_passthrough_tiered"],
        prb_overrides=cf["coal_prb_sigmoid_overrides"],
        coal_bit_sigmoid=cf["coal_bit_passthrough_sigmoid"],
        bit_overrides=cf["coal_bit_sigmoid_overrides"],
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={
            "offer_curve_smoothing_n": None,
            "offer_curve_smoothing_exp": None,
            "offer_curve_smoothing_mid": 0.45,
        },
        priced_interchange=True,  # implied by the reference seam
        reference_price_interface=True,
        as_reserve_withholding=cf.get("as_reserve_withholding", False),
        note=f"pjm_30_refprice: keeper pjm_28 config + forecast-grade "
        f"reference-price interchange seam (replaces the measured "
        f"schedule with per-neighbor gas x HR x load-shape), {year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
