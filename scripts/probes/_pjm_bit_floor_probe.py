"""Curve-retune probe: PJM bituminous cheap-gas discount (2024 coal/gas split).

Re-solves one year off the pjm_27_aswh structural baseline (withholding on) with
a deeper PJM bituminous sigmoid floor, to pull 2024 coal up toward EIA-930 under
cheap gas without regressing 2023/2025. Bit sigmoid is gas-keyed, so a lower
floor self-targets the cheapest-gas year. Structural grounding: bituminous coal
bids toward its take-or-pay/avoidable cost to hold merit when gas is cheap.

Usage: python scripts/probes/_pjm_bit_floor_probe.py <year> <floor> <out_dir>
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "pjm_26"


def main(year: int, floor: float, out: Path) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    meta = json.loads((KEEPER / "meta.json").read_text())
    cf["gas_monthly_actuals"] = meta["gas_monthly_actuals"]
    bit_over = dict(cf["coal_bit_sigmoid_overrides"] or {})
    bit_over["coal_bit_passthrough_floor"] = floor  # deeper cheap-gas discount
    out.mkdir(parents=True, exist_ok=True)

    solve_and_persist(
        [year], "PJM", 8760, _load_reference(),
        commitment=cf["commitment"], screen_coal=cf["commitment_screen_coal"],
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
        bit_overrides=bit_over,
        gas_monthly_actuals=cf["gas_monthly_actuals"],
        offer_curve_overrides=cf["offer_curve_overrides"],
        offer_curve_deltas=cf["offer_curve_deltas"],
        curve_smoothing={"offer_curve_smoothing_n": None,
                         "offer_curve_smoothing_exp": None,
                         "offer_curve_smoothing_mid": 0.45},
        priced_interchange=cf["priced_interchange"],
        as_reserve_withholding=True,
        note=f"bit-floor probe {floor} on pjm_27_aswh baseline, {year}",
    )
    print(f"DONE {year} floor={floor} -> {out}")


if __name__ == "__main__":
    main(int(sys.argv[1]), float(sys.argv[2]), Path(sys.argv[3]))
