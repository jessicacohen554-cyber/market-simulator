"""THROWAWAY diagnostic probe (rule 16 — NEVER registered): does the existing
coal-synchronization mechanism close the COAL_BIT off-peak-hold residual?

Diagnosis (2026-07-13 session, this lane): COAL_BIT under-generates ~15.7 TWh
in 2023/2024 with a clear commitment-hold signature — D-1 shows the miso-60
model's COAL_BIT off-peak CV 0.104 vs actual 0.041 (cv_ratio 2.5): the model
sags/cycles coal through the overnight trough where reality holds it flat,
displacing energy to peakers (CT_PEAKER +11.2 in 2024). CAMPD shows coal's
physical min-DOWN is short (p10 off-window ~5h; total bridgeable short-gap
volume ~1 TWh), so a min-down gap-bridge cannot supply the deficit — the
phenomenon is a committed-band min-load HOLD, not gap-bridging.

coal_sync_srmc_tranche is the existing (never-MISO-tried) mechanism built for
exactly this ("coal HOLDS volume at min-load instead of price-following all
the way down (the step-2 residual: 2024 coal under)"). Rule 20 (one mechanism
per phenomenon) says reconcile with it before building a parallel floor. This
probe A/Bs it on the single train year 2024 against the scored miso-60
baseline: does coal rise, does the off-peak flatten (model_offpeak_cv toward
actual), does CT_PEAKER fall, is the honesty behaviour sane.

THROWAWAY: 2024-only, output to a non-registrable dir, never on the dashboard
(rule 16). If directionally right → promote to a full 2023-2024-2025 keeper
build; if the load-rank sync window is wrong-shaped → refine with the CAMPD
run-length measurement (the lane's rule-23 deliverable).

Usage: python scripts/probes/_miso_coalsync_probe.py
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso60_stgas_vlr"
OUT_NAME = "miso_probe_coalsync_2024"  # throwaway, NOT a dashboard slug

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

    # The deliberate change vs miso-60: turn on the coal synchronization
    # mechanism (Thread-D layer 2). Requires the online-Pmin sizing + the
    # measured take-or-pay contract share (mechanism docstring).
    kwargs["coal_sync_srmc_tranche"] = True
    kwargs["coal_mustrun_online_pmin"] = True
    kwargs["coal_takeorpay_from_data"] = True

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
            "THROWAWAY coal_sync probe (rule 16, 2024-only, never registered) "
            "-- miso-60 replay + coal_sync_srmc_tranche + "
            "coal_mustrun_online_pmin + coal_takeorpay_from_data: does the "
            "existing coal-synchronization mechanism close the COAL_BIT "
            "off-peak-hold residual (D-1 cv_ratio 2.5)."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    main()
