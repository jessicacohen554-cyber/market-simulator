"""ERCOT-61 rule-16 throwaway B: the ercot56-nucwin keeper reconstructed from
its meta.json with ONE delta — the pre-drag residual-fitted ST_GAS offer
markdowns REMOVED (rule-19 reconciliation counterfactual), 2023 only.

The ERCOT-61 mask (``_ercot61_stgas_binding_mask.py`` over the zero-delta
probe) showed the binding-hour ST_GAS excess is ECONOMIC dispatch above the
``st_netload_drag`` floor, not the floor itself; the keeper's ST_GAS deltas
(econ_low −0.13 / econ_high −0.35 / peak −1.0) PREDATE the drag (present in
ercot42), and the drag's derive doc (``docs/ercot-st-gas-netload-drag-2026-06
.md``) states the mechanism "removes the need for ST_GAS offer markdowns
fitted to the residual" — they were never reconciled when the floor landed
(rule 19: replace or reconcile, never stack). The measured 60-Day DAM
evidence (``scripts/derive_ct_offer_surface.py`` design note) shows ST_GAS
offers ≈ marginal cost, flat in net-load — i.e. no markdown below the
physical rising HR curve.

This probe removes the ST_GAS entry from ``offer_curve_deltas`` (bands revert
to the base 0.91/1.15/1.55/4.20) and changes NOTHING else — the drag hinge
stays frozen (rule 23). NEVER registered (rule 16).

Usage::

    python scripts/probes/_ercot61b_stgas_nodeltas_probe.py [OUT_NAME] [--years 2023]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot56_nucwin"

RENAMED = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
DERIVED_ONLY = {
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}
HANDLED = {"years", "iso", "hours", "commitment", "gas_prices", "passes"}
BOOKKEEPING = {"timestamp", "git_sha", "highspy_version", "shared_inputs"}


def build_kwargs(meta: dict, sig_params: set) -> dict:
    """Map the keeper's meta.json onto solve_and_persist kwargs."""
    kwargs = {}
    for k, v in meta.items():
        if k in HANDLED or k in DERIVED_ONLY or k in BOOKKEEPING:
            continue
        if k in RENAMED:
            kwargs[RENAMED[k]] = v
        elif k in sig_params:
            kwargs[k] = v
        else:
            raise ValueError(f"meta.json key {k!r} has no solve_and_persist home")
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("out_name", nargs="?", default="ercot61b_stgas_nodeltas_2023")
    ap.add_argument("--years", type=int, nargs="+", default=[2023])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    # THE one delta: drop the pre-drag ST_GAS offer markdowns (bands revert to
    # the base ERCOT curve). Everything else — the drag hinge included — is
    # byte-identical to the keeper.
    deltas = dict(kwargs.get("offer_curve_deltas") or {})
    removed = deltas.pop("ST_GAS", None)
    kwargs["offer_curve_deltas"] = deltas
    kwargs["note"] = (
        "ercot61b rule-16 throwaway (NEVER register): ercot56_nucwin keeper "
        f"config minus the pre-drag ST_GAS offer markdowns {removed} — the "
        "rule-19 reconciliation counterfactual for the binding-regime ST_GAS "
        "lane (drag floor untouched)."
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE -> {out}")


if __name__ == "__main__":
    main()
