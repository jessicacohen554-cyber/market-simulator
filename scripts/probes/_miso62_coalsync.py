"""miso-62: coal synchronization hold — the COAL_BIT off-peak-hold lane's
mechanism (miso-60 handoff lane 1, re-selected on 2026-07-13 diagnosis).

Diagnosis (docs/handoffs/miso-coal-offpeak-hold-2026-07.md): COAL_BIT
under-generates ~15.7 TWh 2023/2024 with a committed-band min-load-HOLD
signature — D-1 model off-peak CV 0.104 vs actual 0.041 (cv_ratio 2.50): the
model sags/cycles coal through the overnight trough where reality holds it
flat, displacing to CT_PEAKER (+11.2 in 2024). CAMPD shows coal's physical
min-down is short (p10 off-window ~5h; bridgeable short-gap volume ~1 TWh ≪
15.7), so a min-down gap-bridge cannot supply the deficit — the phenomenon is
a min-load hold through long committed runs, not gap-bridging.

Mechanism (rule 20 — the existing owner of the phenomenon, never MISO-tried):
coal_sync_srmc_tranche + coal_mustrun_online_pmin + coal_takeorpay_from_data.
The coal min-load band (sized to the measured online-net-MW Pmin) is split by
the measured EIA-923 take-or-pay contract share into a fuel-free contracted
floor (_mustrun) + a spot remainder priced at full SRMC (_sync), both forced
on and online%-scaled by the measured synchronization fraction (supercritical
→ held all 8760h; cycler → top-load hours only). Zero new scalars: every
input is measured (online Pmin, contract share, online frac). Coal HOLDS
volume at min-load instead of price-following to zero while the dispatchable
tranches above still back down in cheap hours.

Window (rule 12): the measured synchronization window (online frac by load
rank). Driver: take-or-pay contracted fuel is sunk + measured min-load Pmin.
Forward story (rule 13): online Pmin + EIA-923 Sch-5 contract share +
online-frac regenerate for a forward year and respond to changed conditions
(rare-binding in high-gas 2025 where the model already exceeds the window).

Twin (rule 20): MECH_COAL_MUSTRUN is D-2 exempt / MECH_ABLATION_KEPT
(structural take-or-pay must-run, like nuclear) — it stays ARMED in the
zero-forcing twin. The twin still disarms the merchant floors
(st_gas_mustrun_per_plant auto-disarms via MECH_ABLATION_FIELDS). [If the
rubric wants the _sync spot band ablated as merchant, that is a
MECH_ABLATION_FIELDS change adjudicated separately.]

Usage: python scripts/probes/_miso62_coalsync.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso60_stgas_vlr"
OUT_NAME = "miso62_coalsync"

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
    # Base recipe sanity (same guards as the miso-60/61 drivers).
    if not (kwargs.get("prb_overrides") or {}).get("st_gas_mustrun_per_plant"):
        raise SystemExit("miso-60 meta missing st_gas_mustrun_per_plant — wrong base?")
    if not meta.get("miso_rdt_tcdc"):
        raise SystemExit("miso-60 meta missing miso_rdt_tcdc — wrong base?")

    # The deliberate change vs miso-60: coal synchronization hold (Thread-D
    # layer 2). Zero new scalars — all measured inputs.
    kwargs["coal_sync_srmc_tranche"] = True
    kwargs["coal_mustrun_online_pmin"] = True
    kwargs["coal_takeorpay_from_data"] = True

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
            f"miso-62 coal synchronization hold ({mode}) -- miso-60 meta.json "
            "replay + coal_sync_srmc_tranche + coal_mustrun_online_pmin + "
            "coal_takeorpay_from_data (the measured Thread-D layer-2 coal "
            "min-load hold: online Pmin split by EIA-923 take-or-pay share "
            "into a fuel-free contracted floor + full-SRMC spot remainder, "
            "both forced on and online%-scaled by the measured synchronization "
            "fraction). Closes the COAL_BIT off-peak-hold residual (D-1 "
            "cv_ratio 2.50; model sags coal overnight where reality holds it "
            "flat, displacing to CT_PEAKER); zero new scalars."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])
