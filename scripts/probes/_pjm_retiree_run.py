"""PJM retiree-thread run: pjm_36 (refconvex) config + within-window retiree
measured-availability cap. One year -> bundle.

Same recipe as ``_pjm_refconvex_run.py`` (pjm_28 config + forecast-grade
reference-price interchange seam + neighbor price-vs-load convexity) with the
within-window retiree CEMS cap engaged (``retiree_cems_cap=True``): each
within-window retiree plant is limited to its measured monthly CAMPD CEMS
envelope, so a winding-down/retired unit the cost-based LP would otherwise hold
at its coal must-run floor as baseload is dispatched only up to what it actually
ran (zero after it stops). Combined with the per-unit COD retirement already in
cod_ramp, this closes the Homer City (3122) over: model ~4.1 / 2.8 TWh in
2023 / 2024 against CEMS 1.2 / 0.0.

Nothing is tuned to PJM's coal/net-MWh target (claude.md #11) — the cap is the
plant's own measured CEMS operation.

One year per invocation; merge with scripts/probes/_pjm_aswh_merge.py.

Usage: python scripts/probes/_pjm_retiree_run.py <year> <out_dir>
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
        retiree_cems_cap=True,  # the probe lever: cap within-window retirees to
        #   their measured monthly CAMPD CEMS envelope
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
        note=f"pjm_37_retiree: pjm_36 refconvex config + within-window retiree "
        f"CEMS measured-availability cap (retiree_cems_cap=True) — each retiree "
        f"plant limited to its measured monthly CAMPD envelope, closing the "
        f"Homer City phantom-baseload over without tuning to the coal target, "
        f"{year} only",
    )
    print(f"DONE {year} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), Path(sys.argv[2]))
