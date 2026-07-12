"""ERCOT-63 full-span candidate + zero-forcing ablation twin (2023-2025).

The registered-run launcher for the ERCOT-63 keeper candidate: the promoted
ercot59-storage-deploy recipe + ONE structural delta,
``ercot_gas_commitment_bridge`` (the gas-CC committed-state bridge — bridge
ALONE per the 2023 probe-ladder adjudication; ``ercot_offer_surface_lowcurve``
stays default-off). Full 2023-2025 span in one invocation (rule 16, years
sequential) and, with ``--twin``, the zero-forcing ablation twin (rule 20 —
every merchant floor/bridge including the new one neutralized).

Unlike the ladder probes these bundles ARE registered (calibration-report).

Usage::

    python scripts/probes/_ercot63_fullspan.py            # the candidate
    python scripts/probes/_ercot63_fullspan.py --twin     # the ablation twin
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
KEEPER = ROOT / "ercot_storage_deploy"
CANDIDATE = "ercot63_gas_bridge"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--twin", action="store_true")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))
    # ercot59's own defining delta is missing from its pre-fix meta.json
    # (recorded in run_config.json) — see the ERCOT-63 meta-writer fix.
    kwargs.setdefault("ercot_storage_as_deployment", True)
    kwargs.setdefault("ercot_storage_as_deployment_from_year", 2023)
    kwargs["ercot_gas_commitment_bridge"] = True

    if args.twin:
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = CANDIDATE
        name = f"{CANDIDATE}_ablation"
        kwargs["note"] = (
            "ercot63 zero-forcing ablation twin (rule 20 / D-3) of "
            f"{CANDIDATE}: every merchant floor/bridge neutralized via the "
            "D-2 mechanism registry — including the new "
            "ercot_gas_commitment_bridge — keeping only structural must-run "
            "(nuclear / CHP-steam / coal take-or-pay)."
        )
    else:
        name = CANDIDATE
        kwargs["note"] = (
            "ercot63 keeper candidate: the promoted ercot59-storage-deploy "
            "recipe + ONE structural delta, ercot_gas_commitment_bridge "
            "(P1-native gas-CC committed-state bridge; CC-only scope, "
            "measured committed-CC LSL/HSL cap-weighted p50 min-load 0.574, "
            "economic leg on the startup-restart inequality bounded to one "
            "DA operating day, no startup-aware screen — adjudications "
            "recorded at the ScenarioConfig field and in the 2026-07-12 "
            "ERCOT-63 calibration-log entry). ercot_offer_surface_lowcurve "
            "stays OFF: the 2023 probe ladder showed the composition "
            "re-instates the markdown's spread-compression signature "
            "(diagnosis §5) while the bridge alone moves every "
            "storage/spread circle target the right way."
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
