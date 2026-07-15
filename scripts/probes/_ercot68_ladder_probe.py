"""ERCOT-68 rule-16 throwaway ladder: the ERCOT-58 joint completion on the ercot66 base.

The exposed broad under-pricing lane (scarcity/offer formation at moderate
reserve levels): the v3 market-faithful composition — measured thermal
availability + measured-basis online-capacity envelope + realized-room
RTORPA (ORDC-only) — re-run now that the joint round's blocking +2.4 GW
supply-mix excess has lost its leading term (the ERCOT-66 storage re-basis,
the promoted keeper). Adjudication that binds
(docs/DIAGNOSIS-ercot58-joint-round-2026-07.md): v1 (in-LP total family) and
v2 (envelope as hard LP row) are REJECTED WITH CAUSE; v3 is plan-only AS
withholding + NO envelope LP row + POST-SOLVE realized-room RTORPA
(scarcity.ercot_ordc_realized_adder; RTSPP = SPP + RTORPA, Nodal Protocols
§6.5.7.5).

Rungs:

* ``keeper`` — zero-delta reconstruction of the promoted ercot66 keeper
  (2026-07-15-ercot66-storage-rebasis) from its meta.json; the ladder
  control (also dumps dispatch/floors for the STEP-1 ST_GAS binding-hour
  mask, _ercot61_stgas_binding_mask.py).
* ``legJ``   — + ercot_thermal_dam_availability=True
               + ercot_online_capacity_envelope_measured=True
               + ercot_ordc_only_scarcity=True
               (the additive-adder scarcity design is REPLACED, not stacked
               — rule 19: ercot_ordc_total_reserve / ercot_ordc_cap_dual_adder
               forced off, same as _ercot58_ab.py; the measured RTORDPA
               overlay stays — it is the reliability-DEPLOYMENT slice,
               additive to RTORPA by construction). The keeper's
               measured-award storage-AS stack is inherited (A-only keeper;
               never composed with ercot_storage_as_endogenous — its M4
               finding is a separate lane).

Decomposition arms (leg J-) via ``--set KEY=BOOL``, one delta at a time.

Isolation runs are SINGLE-YEAR throwaways: 2024 first (the moderate-tightness
formation test — May shoulders / Nov / Apr / C3c toward 68), then 2023 (the
phantom-channel cure + summer-window floor test). Score with
_ercot63_c3_proxy.py + monthly anatomy + _ercot66_summer_windows.py;
promotion decisions only ever from a full-span 2023-2025 bundle (rule 16).

EXPLICITLY-LABELLED DIAGNOSTIC (rules 13/16): single-year, NEVER registered,
never a keeper config; bundles are throwaways deleted at session end.

Usage::

    python scripts/probes/_ercot68_ladder_probe.py RUNG --years 2024
    # RUNG in {keeper, legJ}; add --set KEY=BOOL for decomposition arms
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _ercot61_stgas_drag_probe import build_kwargs  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
# The promoted ERCOT keeper (2026-07-15-ercot66-storage-rebasis).
KEEPER = ROOT / "ercot66_storage_rebasis_measuredas"

RUNGS = {
    "keeper": {},
    "legJ": {
        "ercot_thermal_dam_availability": True,
        "ercot_online_capacity_envelope_measured": True,
        "ercot_ordc_only_scarcity": True,
        # rule 19: the realized-room RTORPA REPLACES the keeper's in-LP ORDC
        # total family and its cap-dual adder (one RT reserve-scarcity price).
        "ercot_ordc_total_reserve": False,
        "ercot_ordc_cap_dual_adder": False,
    },
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("rung", choices=sorted(RUNGS))
    ap.add_argument("--years", type=int, nargs="+", default=[2024])
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=BOOL",
        help="override one solve_and_persist boolean kwarg (leg J- arms)",
    )
    ap.add_argument("--out-name", default=None)
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs.update(RUNGS[args.rung])
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["note"] = (
        f"ercot68 rule-16 throwaway (NEVER register): '{args.rung}' rung — "
        "ercot66-storage-rebasis keeper reconstructed from meta.json + deltas "
        f"{RUNGS[args.rung]!r} + overrides {args.overrides!r}. The ERCOT-58 "
        "joint completion (v3: plan-only withholding, pricing-only envelope, "
        "post-solve realized-room RTORPA) on the post-storage-re-basis base "
        "(docs/DIAGNOSIS-ercot58-joint-round-2026-07.md)."
    )

    ytag = "_".join(str(y) for y in args.years)
    out = ROOT / (args.out_name or f"ercot68_{args.rung}_{ytag}")
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
