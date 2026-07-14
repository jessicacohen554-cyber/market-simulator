"""miso-66 candidate: MISO lane-1 regulated-coal conduct complement.

The miso-65 keeper recipe (miso-62 ``meta.json`` + ``miso_rpe_pricing`` +
``unit_outage_short_windows`` + ``class_aware_fuel_price_fallback`` on the
regenerated ``campd-unit-outages-MISO.csv``) with ONE reconciled swap: the
rank-scoped ``coal_bit_committed_takeorpay`` is replaced by the
conduct-scoped ``coal_committed_takeorpay_regulated`` (rule-19 reconcile —
RE-BIT plants are covered identically; NR-BIT merchants revert to the
economic bidding the SOM measures for them). See the frozen design +
probe evidence: ``docs/handoffs/miso-coal-conduct-design-2026-07.md``.

The mechanism discounts the ``_committed`` tranche of a coal plant in the
V1b conduct scope (EIA-860 Regulatory Status ``RE`` UNION > 0.5 Schedule-4
cost-of-service ownership by Entity Type I/M/C/P/S/F, operator entity type
for sparse-Schedule-4 plants) by ``1 - contract_share`` of its own measured
EIA-923 Schedule-5 take-or-pay share — the identical sunk-contract rule the
``_mustrun`` band and the BIT flag already use. Zero fitted scalars: a
boolean arming three measured inputs (SOM Table 7 conduct split, EIA-860
RegStatus/Schedule-4 x Entity Type, EIA-923 Schedule-5 shares, CAMPD
committed tranches). Closes the miso-65 C1-2024 conduct gap
({COAL_PRB -10.41, CT_PEAKER +8.30} FAILs) that the miso-65 availability
truth exposed (rule 15).

Twin (rule 20): the mechanism is a PRICING input (a discounted committed-band
bid, no min-gen row), so it stays ARMED in the zero-forcing twin — the
miso-62 precedent for pricing inputs; the twin only zeroes forcing floors.

Usage: python scripts/probes/_miso66_coalconduct.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"  # miso-65 = this meta + the recipe additions
OUT_NAME = "miso66_coalconduct"

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
    # Sanity: the base meta must carry the BIT flag we are about to replace
    # (confirms this is the miso-65 recipe base; rule-19 reconcile below).
    if not kwargs["prb_overrides"].get("coal_bit_committed_takeorpay"):
        raise SystemExit("miso-62 meta missing coal_bit_committed_takeorpay")
    # The miso-65 keeper's three recipe additions (all stay armed):
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    kwargs["prb_overrides"]["class_aware_fuel_price_fallback"] = True
    # Lane-1 conduct swap: replace the rank-scoped BIT flag with the
    # conduct-scoped regulated flag (V1b scope resolves inside fleet.py to
    # eia860_selfcommit_scope_plants; rule-19 reconcile — one mechanism per
    # phenomenon). ZERO fitted scalars.
    kwargs["prb_overrides"]["coal_bit_committed_takeorpay"] = False
    kwargs["prb_overrides"]["coal_committed_takeorpay_regulated"] = True

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
            f"miso-66 candidate ({mode}) -- MISO lane-1 regulated-coal conduct "
            "complement: the miso-65 keeper recipe (miso-62 meta.json + "
            "miso_rpe_pricing + unit_outage_short_windows + "
            "class_aware_fuel_price_fallback on the regenerated "
            "campd-unit-outages-MISO.csv) with the rank-scoped "
            "coal_bit_committed_takeorpay REPLACED by the conduct-scoped "
            "coal_committed_takeorpay_regulated (V1b scope = EIA-860 RegStatus "
            "RE UNION >0.5 Schedule-4 cost-of-service ownership x Entity Type). "
            "The _committed tranche of an in-scope coal plant passes "
            "(1-contract_share) of its measured EIA-923 Schedule-5 fuel; NR "
            "merchants bid full cost (SOM Table 7). Zero fitted scalars; closes "
            "the miso-65 C1-2024 conduct gap {COAL_PRB -10.41, CT_PEAKER +8.30} "
            "(rule 15). Pricing input -> ARMED in the zero-forcing twin "
            "(miso-62 precedent). Design: "
            "docs/handoffs/miso-coal-conduct-design-2026-07.md. Lane 1."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])
