"""miso-64 candidate: the miso-63 keeper composed with the class-aware F923
gap-fill donor (``class_aware_fuel_price_fallback``) — the lane-1(b) measured
fix from docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6.

The change is a zero-fitted-parameter donor-pool correction, not a price
lever: the "nearby plant" fuel-cost fallback's state/zone pools are
quantity-weighted and fuel-group-wide, so for gas they are CC-burn-dominated
(~$2.6/MMBtu) while MISO CT filers measurably pay $4.13/MMBtu cap-weighted
(2024 F923). The ~33% of CT capacity without its own filing was inheriting
the CC price, ~$16-20/MWh below its measured class cost — feeding the 2024
CT_PEAKER +7.1 TWh economic over-run at PRB's expense AND July-2025's
too-cheap North margin. With the gate on, a gap-filled month is priced from
same-class reporting plants first (state, then zone), the class-blind pools
remaining the fallback. No-LP wiring check on the 2024 fleet
(_miso_classdonor_wiring.py): 12.0 GW of gap-filled CT_PEAKER moves
$3.62 -> $4.48/MMBtu cap-wtd; CC_REGULAR -$0.06; CT_CHP (industrial
contracts) -$0.26; everything else byte-identical.

Twin (rule 20): the donor is a fuel-price INPUT (not a merchant floor), so it
stays ARMED in the zero-forcing twin, like the passthrough sigmoids and the
outage overlays (the miso-63 pattern).

Usage: python scripts/probes/_miso64_classdonor.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"  # miso-63 = this meta + the two overrides
OUT_NAME = "miso64_classdonor"

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
        raise SystemExit("miso-62 meta missing miso_rdt_tcdc — wrong base?")

    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("coal_bit_committed_takeorpay"):
        raise SystemExit("miso-62 meta missing coal_bit_committed_takeorpay")
    # The miso-63 keeper's two additions (both stay armed):
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    # THE deliberate change vs the miso-63 keeper:
    kwargs["prb_overrides"]["class_aware_fuel_price_fallback"] = True

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
            f"miso-64 candidate ({mode}) -- miso-63 keeper replay (miso-62 "
            "meta.json + miso_rpe_pricing + unit_outage_short_windows) + "
            "class_aware_fuel_price_fallback: the F923 nearby-donor pools "
            "consult same-class reporting plants first (measured basis: MISO "
            "2024 CT filers $4.13/MMBtu cap-wtd vs CC $2.57; the class-blind "
            "quantity-weighted pool handed non-filing CTs the CC-dominated "
            "~$2.6 price). Zero fitted parameters; "
            "docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md §6 lane 1(b)."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])
