"""THROWAWAY 2025-only A/B probe (rule 16 — never registered): the short
(< 5-day) baseload-coal unit-outage channel on top of the miso-62 keeper.

Target: the July 2025 LMP miss (model 39.48 vs DA actual 58.79 Indiana-basis;
docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md). The measured diagnosis: at the
Jul 28-29 peak block ~2.8 GW of baseload-coal capability that ran elsewhere in
July was offline invisibly to the >= 5-day outage overlay (the own-fleet
temp-capability envelope is flat — MISO loses discrete units under stress, it
does not derate smoothly), leaving the model's stack with 14-20 GW of
headroom at hours reality priced $200-433.

Config: the miso-62 keeper's exact meta.json replay (strict RENAME/SKIP, the
_miso62_bitpricing.py pattern) + prb_overrides["unit_outage_short_windows"] =
True (the generic ScenarioConfig override channel), 2025 ONLY — a diagnostic
probe to size the channel's July/tail/N-S effect before any full 2023-2025
keeper-candidate run. Compare against the registered keeper payload's 2025
block (same solve path, byte-comparable artifacts).

Usage: python scripts/probes/_miso_shortout_probe.py
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"
OUT_NAME = "_probe_miso_shortout_2025"

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
    if not meta.get("miso_rdt_tcdc"):
        raise SystemExit("miso-62 meta missing miso_rdt_tcdc — wrong base?")

    # Sanity: the keeper base must already carry the miso-62 mechanism.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("coal_bit_committed_takeorpay"):
        raise SystemExit("miso-62 meta missing coal_bit_committed_takeorpay")
    # THE deliberate change: arm the short-window availability channel.
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True

    solve_and_persist(
        [2025],  # 2025-only DIAGNOSTIC (rule 16: throwaway, never registered)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        note=(
            "THROWAWAY 2025-only probe: miso-62 keeper replay + "
            "unit_outage_short_windows=True (< 5-day baseload-coal CEMS "
            "windows, campd-unit-outages-short-MISO.csv). Sizes the July-2025 "
            "LMP effect (tail, N-S separation, coal TWh) before any full "
            "3-year candidate. NEVER register this bundle."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    main()
