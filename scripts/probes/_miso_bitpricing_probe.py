"""THROWAWAY diagnostic probe (rule 16 — NEVER registered): does the grounded
contract-share bituminous committed-band bid discount close COAL_BIT?

Owner-selected lane (2026-07-13): the COAL_BIT −15.7 TWh 2023/2024 residual is
a take-or-pay BID-PRICING phenomenon (both commitment candidates refuted — see
docs/handoffs/miso-coal-offpeak-hold-2026-07.md). MISO coal is ~100% contracted
(coal_takeorpay_MISO.csv), so real bituminous baseload bids BELOW delivered
spot cost (sunk contracted fuel) to hold against cheap gas; the model bids the
`_committed` band at full delivered cost (coal_bit_passthrough_sigmoid off) and
BIT is priced out.

Mechanism (grounded, rule 1/13): coal_bit_committed_takeorpay — the `_committed`
tranche of a bituminous plant in the measured take-or-pay map passes
``1 - contract_share`` of its fuel (the same sunk-contract rule as `_mustrun`),
so the contracted baseload holds against cheap gas while econ*/peak keep full
cost (coal_econ_srmc_bound, already on in miso-60). No fitted sigmoid; the
discount is the plant's own EIA-923 Schedule-5 share.

This probe A/Bs it on the single train year 2024 vs the scored miso-60 baseline:
does COAL_BIT rise toward actual (~53 TWh; +15.7 needed), does CT_PEAKER fall,
and does the aggregate stay sane (no coal over-shoot, no gas collapse).

THROWAWAY: 2024-only, non-registrable dir (rule 16). If it closes COAL_BIT
cleanly → promote to a full 2023-2024-2025 keeper build.

Usage: python scripts/probes/_miso_bitpricing_probe.py
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso60_stgas_vlr"
OUT_NAME = "miso_probe_bitpricing_2024"  # throwaway, NOT a dashboard slug

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


def main() -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    out = ROOT / OUT_NAME
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

    # The deliberate change vs miso-60: the grounded committed-BIT take-or-pay
    # discount, injected through the generic with_overrides channel (miso-59/60
    # pattern). coal_takeorpay_from_data is already on for MISO (the share map),
    # and coal_econ_srmc_bound already clamps econ*/peak to full cost.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("st_gas_mustrun_per_plant"):
        raise SystemExit("miso-60 meta missing st_gas_mustrun_per_plant — wrong base?")
    kwargs["prb_overrides"]["coal_bit_committed_takeorpay"] = True

    solve_and_persist(
        [2024],  # THROWAWAY single-year diagnostic (rule 16); in-training year
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        zero_forcing_ablation=False,
        ablation_of=None,
        note=(
            "THROWAWAY BIT-pricing probe (rule 16, 2024-only, never registered) "
            "-- miso-60 replay + coal_bit_committed_takeorpay=True (grounded "
            "committed-BIT take-or-pay discount, 1-contract_share): does it "
            "close the COAL_BIT -15.7 TWh residual."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    main()
