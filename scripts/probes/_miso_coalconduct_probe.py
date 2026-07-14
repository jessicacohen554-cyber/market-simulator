"""THROWAWAY A/B probe (rule 16 — never registered) for the lane-1
regulated-coal conduct mechanism ``coal_committed_takeorpay_regulated``.

Replays the miso-65 keeper recipe (miso-62 meta.json strict RENAME/SKIP +
miso_rpe_pricing + unit_outage_short_windows + class_aware_fuel_price_fallback
on the regenerated campd-unit-outages-MISO.csv) with exactly ONE change per
mode:

- ``reg``  : coal_bit_committed_takeorpay=False,
             coal_committed_takeorpay_regulated=True (the candidate: the
             committed-band sunk-contract discount rescoped from coal rank to
             EIA-860 Regulatory Status — RE plants discount, NR merchants
             revert to full-cost committed bids; SOM Table 7 conduct split).
- ``regb`` : identical flags to ``reg`` — a distinct out-dir tag for probes
             solved AFTER the pre-declared V1b scope refinement landed in
             fleet.py (eia860_selfcommit_scope_plants: RE ∪ cost-of-service
             majority ownership; design doc §4). The flag is the same; the
             scope-set derivation differs by commit.
- ``base`` : no change (a same-machine miso-65 replica year, the
             environment-drift control for the A/B readout).

Sizes the two-sided 2024 target (COAL_PRB −10.41 FAIL needs UP, CT_PEAKER
+8.30 FAIL needs DOWN) and the 2025 guard (PRB already +5.1 over on prelim
923; C3a-2025 −12.9% must not worsen materially; C3b stays PASS) before the
Phase B build (docs/handoffs/miso-coal-conduct-design-2026-07.md).

Usage:
  python scripts/probes/_miso_coalconduct_probe.py reg 2024
  python scripts/probes/_miso_coalconduct_probe.py reg 2023 2024 2025
  python scripts/probes/_miso_coalconduct_probe.py base 2024
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"  # miso-65 = this meta + three overrides

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


def main(mode: str, years: list[int]) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    ytag = "_".join(str(y) for y in years)
    out = ROOT / f"_probe_miso_coalconduct_{mode}_{ytag}"
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
    # The miso-64/65 keeper recipe (all stay armed in every mode):
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    kwargs["prb_overrides"]["class_aware_fuel_price_fallback"] = True
    if mode in ("reg", "regb"):
        # THE deliberate change: rescope the committed-band sunk-contract
        # discount from coal rank (BIT) to the measured cost-of-service set.
        kwargs["prb_overrides"]["coal_bit_committed_takeorpay"] = False
        kwargs["prb_overrides"]["coal_committed_takeorpay_regulated"] = True

    solve_and_persist(
        years,  # THROWAWAY diagnostic subset (rule 16); in-training years only
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        note=(
            f"THROWAWAY coal-conduct probe ({mode}, years {years}) -- miso-65 "
            "recipe replay; reg mode swaps coal_bit_committed_takeorpay for "
            "coal_committed_takeorpay_regulated (lane-1 conduct candidate, "
            "SOM Table 7 regulated/merchant split). NEVER register."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("reg", "regb", "base"):
        raise SystemExit(__doc__.splitlines()[-5])
    main(sys.argv[1], [int(y) for y in sys.argv[2:]])
