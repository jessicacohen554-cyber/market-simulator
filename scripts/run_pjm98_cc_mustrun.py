"""Driver: PJM 98 — eastern CC/CT local-reliability commitment (must-run) floor.

G-20 follow-up to the pjm-97 keeper (`2026-07-10-pjm-97-measured-interfaces`),
building the fix its attestation and the G-20 diagnosis recommended
(docs/handoffs/pjm-eastern-ccct-underrun-g20-2026-07.md §5): the eastern MAAC
CC/CT UNDER-RUN (Dominion CC −81%, EMAAC CT −83%, SWMAAC CC −93% worst cells)
is not closable by any admissible seam / deliverability / commitment-posture
lever — every one wheels corridor power through the pockets because CC_REGULAR
carries ~0 min-gen floor and its committed tranche is a low-PRICE offer, not a
forced QUANTITY.

**Mechanism** (``ScenarioConfig.cc_mustrun_per_plant``): each merchant
CC_REGULAR / CT_PEAKER committed tranche — already sized to the plant's CEMS
minimum stable load (thermal_tranches_PJM.csv ``committed_pct``) — is forced on
as a min-gen floor in the plant's measured committed window: its top
``online_frac`` fraction of hours ranked by system load (the artifact's
measured CEMS synchronization fraction, same estimator the coal step-3a
forcing uses). This is the real PJM out-of-market local reliability commitment
(LDA/voltage RMR, paid via bid-cost recovery so the hub LMP is untouched).
Rule 13: both parameters are measured, multi-year pooled, forward-regenerating.
Rule 18: self-targeting by the measurement — western CCs that already run
economically see a non-binding bound. Rule 19: the EXISTING committed tranche
becomes a forced quantity (offer price unchanged) — no stacked second floor.
Zero fitted scalars in this delta, so the rule-22 LOO-before-promotion clause
(which cross-validates TUNED changes) is vacuous, as it was for pjm-97's flip.

Everything else is the pjm-97 keeper recipe VERBATIM (replayed byte-faithfully
from its committed meta.json via replay_keeper.build_kwargs). Full span
2023-2025 one bundle (rule 16), years sequential (rule 1/12). MEMORY: run with
MALLOC_ARENA_MAX=2 (~12 GB peak per year on a 15 GB host).

``--ablation`` solves the D-3 zero-forcing twin instead (rule 20): identical
config, every merchant floor — including this new one, via its
MECH_ABLATION_FIELDS entry — neutralized; registered alongside the keeper
candidate so the per-class delta quantifies what the floor buys.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO))

from scripts.replay_keeper import build_kwargs  # noqa: E402
from scripts.run_calibration_full import (  # noqa: E402
    _load_reference,
    report_run,
    solve_and_persist,
)

_KEEPER_BUNDLE = _REPO / "results" / "calibration" / "pjm97_measured_interfaces"

_NOTE = (
    "PJM 98: pjm-97 keeper recipe (byte-faithful replay off its meta.json) + "
    "cc_mustrun_per_plant=True — the G-20-recommended eastern CC/CT "
    "out-of-market local-reliability commitment floor (per-plant CEMS "
    "committed tranche forced on in its measured top-online_frac system-load "
    "window; docs/handoffs/pjm-eastern-ccct-underrun-g20-2026-07.md §5). "
    "Zero fitted scalars in the delta."
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--ablation",
        action="store_true",
        help="solve the D-3 zero-forcing ablation twin instead",
    )
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    name = "pjm98_cc_mustrun" + ("-ablation" if args.ablation else "")
    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else (_REPO / "results" / "calibration" / name)
    )

    meta = json.loads((_KEEPER_BUNDLE / "meta.json").read_text())
    kwargs = build_kwargs(meta)
    kwargs["years"] = [2023, 2024, 2025]
    kwargs["iso"] = "PJM"
    kwargs["hours"] = 8760
    kwargs["reference"] = _load_reference()
    kwargs["run_dir"] = out_dir
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"]["cc_mustrun_per_plant"] = True
    kwargs["note"] = _NOTE
    if args.ablation:
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = "pjm98_cc_mustrun"
        kwargs["note"] = (
            "D-3 zero-forcing ablation twin of pjm98_cc_mustrun (rule 20): "
            "identical config, every merchant floor/bridge/drag neutralized "
            "via ScenarioConfig.as_zero_forcing_ablation (off-list from the "
            "D-2 mechanism registry, incl. the new MECH_CC_MUSTRUN_PER_PLANT)."
        )

    run_dir = solve_and_persist(**kwargs)
    report_run(run_dir)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
