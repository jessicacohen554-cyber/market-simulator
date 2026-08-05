"""Generate the ercot-167 keeper attestation from the ercot165 base.

``results/calibration/ercot167_socreserve_B`` is the ercot165 keeper recipe
plus ONE mechanism delta — ``ercot_storage_as_soc_reserve=true`` (the matrix
§5.1 item-10 measured storage AS SOC reservation) — so its attestation is the
committed ercot165 attestation with: (a) one ADDED measured/published DOF-ledger
entry (n_scalars 0, ``free_parameters_added: 0``; the award series, the
published per-product durations and the measured product shares are all
source-data identified, rule 23); (b) the governance block re-attested for this
run; (c) the three rubric-v3.0 ``price_tail`` model-class exceptions entries
CARRIED FORWARD from the ercot165 keeper (the 2026-08-05 owner decision applies
to the ISO's keeper lane) with magnitudes updated to THIS run's counts.

Reads committed artifacts only; no solve. Run:
    python scripts/gen_ercot167_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = (
    REPO / "results/calibration/ercot165_unpooled_share_B/calibration_attestation.json"
)
DEST = REPO / "results/calibration/ercot167_socreserve_B/calibration_attestation.json"

MAGS = {
    2023: "model 61 h vs actual RT 181 h > $200/MWh (0.34x; band [0.5x, 2.0x])",
    2024: "model 25 h vs actual RT 53 h > $200/MWh (0.47x; band [0.5x, 2.0x])",
    2025: "model 3 h vs actual RT 31 h > $200/MWh (|delta| 28 > small-count 10)",
}

NEW_ENTRY = {
    "name": "ercot_storage_as_soc_reserve",
    "kind": "measured-published",
    "n_scalars": 0,
    "free_parameters_added": 0,
    "identification": (
        "Battery SOC floored at the MEASURED 60-Day DAM battery upward-AS award "
        "(the SAME committed by-restype 'storage' total storage_as_commitment "
        "power-docks - one award basis, both sides, rule 19) x the PUBLISHED "
        "per-product SOC durations (RegUp/RRS 1 h, ECRS 2 h, NonSpin 4 h - "
        "reserves.spec.ERCOT_AS_PRODUCT_DURATION_H, Nodal Protocols 3.17.3), "
        "per-product shares measured by scripts/data/derive_ercot_storage_as_products.py "
        "(reconstruction reproduces the committed total EXACTLY for 2023/2024). "
        "Deployment-netted (intra-day cumulative of the armed measured draw-down "
        "series - deployed AS energy leaves the tank) and clipped by the "
        "pin-reachability envelope (the unit's max-reachable SOC path under the "
        "model's own daily-pin scaffold and award-docked power; removes 0.16% of "
        "floor MWh - measured arrays only). Zero fitted scalars; forward runs "
        "price the split endogenously (ercot_storage_as_endogenous, G5 lane), so "
        "the measured record is backcast-only capability input, never a pinned "
        "outcome (rule 13). Identification record: "
        "docs/PRECOMMIT-ercot167-storage-as-soc-reserve-2026-08-05.md (gates "
        "pre-registered before any solve; two feasibility amendments, no gate "
        "touched) + results/calibration/FINDING-ercot167-storage-soc-reserve-ab-"
        "2026-08-05.md (the full A/B record)."
    ),
}


def main() -> None:
    """Emit the ercot167 attestation from the committed ercot165 base."""
    att = json.loads(BASE.read_text())
    fp = att["free_parameters"]
    assert not any(e.get("name") == NEW_ENTRY["name"] for e in fp["entries"]), (
        "entry already present"
    )
    fp["entries"].append(NEW_ENTRY)
    fp["n_entries"] = len(fp["entries"])
    gov = att["governance"]
    gov["attested_by"] = (
        "ercot-167 2026-08-05 (OWNER-PROMOTED on the standing structural standard) - "
        "the ercot165 keeper recipe with ONE delta: ercot_storage_as_soc_reserve=true "
        "(matrix 5.1 item 10, the ercot-162 s2 named successor, owner-chartered at "
        "ercot-166 and owner-directed for execution with a separate-2023-first "
        "sequencing). The session's own pre-registered A/B verdict was "
        "REJECTED-AS-ARMED - two kills fired and bound (hub-basis G4-2024 C3a +1.4pp, "
        "concentrated on the KNOWN maintenance-season fabricated-spike days "
        "FINDING-ercot166 s5 flags, on an April already +72% over in the CONTROL; "
        "G3-2025 one spurious hour, a $43 threshold graze at 2025-10-21 19h whose two "
        "NEIGHBOR hours are newly-captured REAL tail hours) - and the owner promoted "
        "on that surfaced record ('Promote', 2026-08-05), the standing standard "
        "being 'if structural integrity improves but gates regress that may still be "
        "a keeper'. CARRIED HONESTLY, NOT HIDDEN: on the scorer's rt_lw basis the "
        "arm also crosses the C3b-2024 band by 0.006 (0.206 vs <=0.20; the control "
        "scores 2023-only) - the same maintenance-season root, named in the reopen "
        "condition: re-gate the identical arm after the 2024 availability defect "
        "(handoff H4 item 4) lands. What the mechanism buys structurally: the 2023 "
        "scarcity-hour battery over-discharge closes 60% of its measured gap "
        "(666->520 MW vs the delivery-2023 SCED actual 423) with spurious tail DOWN "
        "and shed FLAT, and the 2025 evening net-discharge shape lands nearly on the "
        "930-BAT actual (18h 3,033 vs 2,995; the control ran +462 over). Zero new "
        "free parameters (n_entries 11->12, n_residual UNCHANGED at 6 - the added "
        "entry is measured/published)."
    )
    exceptions = att.get("exceptions", [])
    assert len(exceptions) == 3, "expected the three ercot165 model-class entries"
    for e in exceptions:
        e["magnitude"] = MAGS[int(e["year"])]
        e["reason"] += (
            " CARRIED ONTO THE ercot167 KEEPER at the 2026-08-05 owner promotion "
            "(magnitudes updated to this run's counts; the owner decision applies "
            "to the ERCOT keeper lane and the exhaustion record is unchanged - the "
            "ercot-167 quantity mechanism moved the counts 58/20/0 -> 61/25/3, "
            "nowhere near the [0.5x] band, exactly as the model-class limitation "
            "predicts)."
        )
    DEST.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {DEST.relative_to(REPO)} (n_entries {fp['n_entries']})")


if __name__ == "__main__":
    main()
