"""miso-62: grounded bituminous committed-band take-or-pay bid discount —
the COAL_BIT under-generation lane's mechanism (owner-selected 2026-07-13).

Diagnosis + two refutations (docs/handoffs/miso-coal-offpeak-hold-2026-07.md):
the COAL_BIT −15.7 TWh 2023/2024 free-C1 residual is a take-or-pay BID-PRICING
phenomenon, not commitment (the min-down bridge and coal_sync were both
refuted). MISO coal is ~100% contracted (coal_takeorpay_MISO.csv); real
bituminous baseload bids BELOW delivered spot cost (sunk contracted fuel) to
hold against cheap gas, which the model omitted (coal_bit_passthrough_sigmoid
off → committed BIT bids full delivered cost → priced out).

Mechanism (grounded, rule 1/13; zero fitted parameters):
coal_bit_committed_takeorpay — the `_committed` tranche of a bituminous plant
in the measured take-or-pay map passes ``1 − contract_share`` of its fuel (the
same sunk-contract rule already on `_mustrun`), so contracted baseload holds
against cheap gas while econ*/peak keep full delivered cost
(coal_econ_srmc_bound, already on) and BIT price-follows above the committed
band. coal_takeorpay_from_data is already on for MISO (the share map). The
discount is each plant's own EIA-923 Schedule-5 contract share — no residual
tuning, no sigmoid.

Throwaway 2024 A/B (rule 16): COAL_BIT 37.66 → 53.44 TWh (+15.78), landing
onto the measured ~53.4; CT_PEAKER −4.1. This full run scores all three train
years to confirm COAL_BIT closes without breaking other criteria (esp. that
COAL_PRB stays in tolerance under the BIT/PRB redistribution).

Twin (rule 20): coal_bit_committed_takeorpay is a PRICING input (a bid
discount), not a merchant floor — it forces no energy, so like the passthrough
sigmoids and miso_rpe_pricing it stays ARMED in the zero-forcing twin (which
disarms only merchant floors, e.g. st_gas_mustrun_per_plant).

Usage: python scripts/probes/_miso62_bitpricing.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso60_stgas_vlr"
OUT_NAME = "miso62_bitpricing"

RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
SKIP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "timestamp",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "highspy_version",
    "shared_inputs",
    "commitment",
    "commitment_screen_coal",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}


def main(mode: str) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    ablate = mode == "ablation"
    out = ROOT / (OUT_NAME + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    sig = inspect.signature(solve_and_persist).parameters
    kwargs = {}
    unmapped = []
    for k, v in meta.items():
        if k in SKIP:
            continue
        mapped = RENAME.get(k, k)
        if mapped in sig:
            kwargs[mapped] = v
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(f"meta.json keys not bound to solve_and_persist: {unmapped}")
    if not meta.get("miso_rdt_tcdc"):
        raise SystemExit("miso-60 meta missing miso_rdt_tcdc — wrong base?")

    # The deliberate change vs miso-60, through the generic with_overrides
    # channel (miso-59/60/61 pattern). coal_takeorpay_from_data + econ bound
    # already on in the miso-60 recipe.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("st_gas_mustrun_per_plant"):
        raise SystemExit("miso-60 meta missing st_gas_mustrun_per_plant — wrong base?")
    kwargs["prb_overrides"]["coal_bit_committed_takeorpay"] = True

    solve_and_persist(
        meta["years"],  # 2023 2024 2025 — one bundle (rule 16)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(OUT_NAME if ablate else None),
        note=(
            f"miso-62 grounded bituminous committed take-or-pay bid discount "
            f"({mode}) -- miso-60 meta.json replay + "
            "coal_bit_committed_takeorpay=True (the _committed tranche of a "
            "bituminous plant in the measured take-or-pay map passes "
            "1-contract_share of its fuel -- contracted baseload is sunk, so it "
            "holds against cheap gas while econ*/peak keep full delivered cost). "
            "Closes the COAL_BIT -15.7 TWh 2023/2024 free-C1 residual "
            "(re-diagnosed as bid-pricing, not commitment; both commitment "
            "candidates refuted). Grounded by each plant's EIA-923 Schedule-5 "
            "share (rule 1/13); zero fitted parameters."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])
