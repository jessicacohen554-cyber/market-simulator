"""ERCOT-66 full-span candidate (2023-2025): storage capability re-basis + endogenous split.

The registered-run launcher for the ERCOT-66 keeper candidate: the promoted
ercot63-gas-bridge recipe + TWO structural deltas adjudicated by the 2023
probe ladder (`_ercot66_ladder_probe.py`):

* ``ercot_storage_capability_measured=True`` — the battery power basis
  follows the 60-Day disclosure registered non-OUT PWRSTR/ESR HSL (leg A:
  C3a +3.1 -> -2.0 %, C3b 0.131 -> 0.065, the whole price correction inside
  the June/Sep-2023 scarcity-formation driver window).
* ``ercot_storage_as_endogenous=True`` — the LP chooses the battery
  energy-vs-AS split on the full measured cap (leg B; M1 cap-subtraction,
  M2 requirement netting and the measured-award deployment floor all off;
  the post-solve additive ORDC adder gates off — scarcity is priced by the
  co-opt's internalized duals + the measured RTORDPA overlay).

Full 2023-2025 span in ONE invocation (rule 16, years sequential — rule 12).
No zero-forcing ablation twin (rule 20 as amended 2026-07-14). This bundle
IS registered (calibration-report) whatever the verdict — keeper candidate
or rejected probe (rule 15).

Usage::

    python scripts/probes/_ercot66_fullspan.py [--years 2023 2024 2025]
    python scripts/probes/_ercot66_fullspan.py --no-endog   # leg-A-only fallback
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
KEEPER = ROOT / "ercot63_gas_bridge"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-endog",
        action="store_true",
        help="leg-A-only fallback recipe (measured capability, keep the "
        "measured-award M1/M2/deployment stack)",
    )
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    kwargs["ercot_storage_capability_measured"] = True
    if args.no_endog:
        name = "ercot66_storage_rebasis_measuredas"
        deltas = "ercot_storage_capability_measured"
    else:
        kwargs["ercot_storage_as_endogenous"] = True
        kwargs["ercot_storage_as_deployment"] = False
        name = "ercot66_storage_rebasis"
        deltas = (
            "ercot_storage_capability_measured + ercot_storage_as_endogenous "
            "(deployment floor cleared — mutually exclusive)"
        )
    kwargs["note"] = (
        f"ercot66 full-span candidate: ercot63-gas-bridge recipe + {deltas}. "
        "Charter: docs/DIAGNOSIS-ercot-summer-availability-audit-2026-07.md §2 "
        "(storage capability basis is the phantom-evening defect; the "
        "disclosure registered non-OUT HSL replaces the EIA-860 power ramp in "
        "backcast)."
    )

    out = ROOT / name
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
