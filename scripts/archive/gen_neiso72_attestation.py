"""Write ``calibration_attestation.json`` for the neiso-72 hydro-window keeper.

Seeds from the outgoing ``neiso71_nucavail_B`` keeper's attestation and applies
exactly the changes neiso-72 earns (precedent:
``scripts/gen_neiso71_attestation.py``):

1. **Governance block** re-attested to this session, naming the single delta
   (the ``EIA930_PS_SPLIT_COMPLETE_FROM`` windowed pin refusal, design D) and
   the same-HEAD control it was scored against.
2. **Exceptions carried VERBATIM.** The C3c ``price_tail`` ledger entries
   describe the RT scarcity-formation model miss (winter oil-parity cap +
   summer RT-only formations); the arm moves the mean LMP by at most
   +$0.16/MWh and 2025 is bit-identical, so the entries' factual basis is
   unchanged. No new disposition is created and no ledger slot is spent.
3. **DOF ledger UNCHANGED** (``n_entries`` 12, ``n_residual`` 5). The delta
   REMOVES a measured overlay's applicability in two years (the EIA-930
   ``NG: WAT`` pin, refused for pre-split 2023/2024) and adds **zero**
   parameters: the registry constant is a measured data-admissibility guard
   (seam = first filed ``NG: PS`` hour, 2024-11-07), not a tunable (rule 21
   ``[R-DOF]`` / rule 24 ``[R-REGISTRY]``).

Usage::

    PYTHONPATH=.:src python3 scripts/gen_neiso72_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

SRC = REPO / "results/calibration/neiso71_nucavail_B/calibration_attestation.json"
DST = REPO / "results/calibration/neiso72_hy_window_B/calibration_attestation.json"

ATTESTED_BY = (
    "neiso-72 hydro-PS-window session 2026-07-31 (branch "
    "claude/neiso-72-hydro-ps-window-y2x9cw): the neiso-71 keeper recipe + ONE "
    "structural delta — constants.EIA930_PS_SPLIT_COMPLETE_FROM = {'NEISO': 2025} "
    "with data.hydro.eia930_wat_level_folded refusing the EIA-930 NG:WAT monthly "
    "hydro LEVEL pin PER-YEAR for years before NEISO's first wholly-split "
    "calendar year (first filed NG:PS hour 2024-11-07; the pre-split NG:WAT "
    "folds ~1.9 TWh/yr of pumped-storage gross discharge, measured four "
    "independent ways incl. the confound-free within-November-2024 seam test, "
    "probe scripts/probes/_neiso72_ps_window_audit.py). 2023/2024 hydro levels "
    "move to the units' own EIA-923 HY filings (builder budgets 8.5762/6.7144 "
    "TWh vs 8.7750/7.3942 pinned); 2025, the first wholly-split year, keeps the "
    "pin and is BIT-IDENTICAL to the control (class_hourly/system/storage "
    "sidecars .equals=True — the design-D wiring check). Zero fitted scalars: "
    "the registry is a measured data-admissibility guard and the refusal "
    "REMOVES a mechanism; the rejected alternatives (flat refusal, mid-year "
    "splice, 930-minus-estimated-PS) are adjudicated in "
    "PREREG-neiso72-hydro-ps-window-2026-07-31.md §4-§4a (owner design "
    "sign-off + promotion authorization on record in-session). Control "
    "neiso72_control_A reproduces the neiso-71 keeper at the same HEAD "
    "(10c624e) to 4 decimals (hydro 8.7038/7.3273/5.1064 TWh, LMP "
    "39.1030/43.8038/71.9708)."
)

NOTE = (
    "neiso-72 = the neiso-71 keeper recipe with the pumped-storage TIME-SPLIT "
    "level guard armed (design D, whole-year basis rule: a backcast year "
    "before the first wholly-split year refuses the NG:WAT pin, a wholly-split "
    "year keeps it — one source basis per year, never a mid-year splice). "
    "Every pre-registered check PASSES: control integrity (keeper reproduced "
    "to 4 decimals at the same HEAD), single delta (git changed_files = the "
    "registry constant + hydro.py + comment/tests only), liveness (max hourly "
    "|d class MW| 632/713 MW in 2023/2024, >>50), the 2025 bit-identity KILL "
    "check (all three hourly sidecars .equals=True), and the E1 sign "
    "(hydro -0.186/-0.654/0 TWh, CC_REGULAR +0.178/+0.583/0, load-weighted "
    "LMP +0.050/+0.159/0.000 $/MWh — declared before the solve). NEISO's "
    "pumped storage remains endogenous storage (1,865.0 MW, "
    "model/storage.py::load_eia860_pumped_storage); the refused pin had been "
    "double-representing its discharge as conventional river water on top of "
    "that. KNOWN bench-basis note: the C1 hydro benchmark actual for 2024 is "
    "itself the PS-folded EIA-930 series (7.3942 TWh exactly), so the "
    "corrected model's 2024 hydro ratio degrades ON PAPER against a "
    "contaminated actual — successor item, never a reason to re-contaminate "
    "the level (rule 14)."
)


def main() -> None:
    att = json.loads(SRC.read_text())
    att["governance"]["attested_by"] = ATTESTED_BY
    att["governance"]["note"] = NOTE
    DST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DST}")


if __name__ == "__main__":
    main()
