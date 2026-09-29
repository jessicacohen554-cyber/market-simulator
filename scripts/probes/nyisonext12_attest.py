"""NYISO-NEXT-12: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars, a structural seam node) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext12_attest.py --keeper results/calibration/nyisonext9_span \\
        --out results/calibration/nyisonext12_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO NE AC tie on its own two-way node (nyiso_ne_ac_node true)",
    "where": (
        "ScenarioConfig.nyiso_ne_ac_node (default False) -- the keeper recipe flips "
        "False -> True; model/interchange/spec.py NYISO_NE_AC_LADDER_BY_YEAR / "
        "NYISO_IMPORT_TRANCHES_NE_SPLIT_BY_YEAR / build_nyiso_ne_ac_node_gens, "
        "model/interchange/nyiso.py split_nyiso_ne_ac_node / "
        "inject_nyiso_ne_ac_node_prices / nyiso_ne_ac_posted_ttc_hourly, "
        "data/nyiso_par_attribution.py exclude_rows, pipeline/commitment.py node sink mask"
    ),
    "identification": "structural (measured inputs, frozen formulas)",
    "lineage_solves": "1 (NYISO-NEXT-12, five year-isolated shards)",
    "value": {
        "rule": "8 import + 8 export bands on node NYISO_NE_AC (one link to "
        "Capital_Hudson), sized on the year's median P-32 posted limit, priced "
        "Roseton DA(t) + frozen Q-Q offset_k; link bounded hourly at the posted "
        "limits; NE row removed from the pooled ladder, the pooled Capital_Hudson "
        "PAR envelope and the pooled hub repricing (rule 19)",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO P-32 SCH - NE - NY hourly flow and posted limits; ISO-NE "
    ".I.ROSETON 345 1 DA LMP and NYISO CAPITL DA (seam-neighbour-price intake); "
    "offsets are the PJM neighbour-hourly Q-Q coupling transferred in kind "
    "(scripts/data/derive_nyiso_ne_ac_ladder.py). Band size = median posted limit "
    "is a declared construction choice fixed ex ante (PRECOMMIT sec. 3).",
    "root_cause": "not a residual closer: the pooled NYISO_external node cannot hold "
    "NE's measured net export and HQ/IESO's import at once; the seam is placed "
    "where it physically lands (rules 14/19). Owner ruling Q-a 2026-09-28: promote "
    "on structure only, never on C3a. Record: "
    "docs/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md.",
}


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pin", required=True)
    a = ap.parse_args()
    att = json.loads((a.keeper / "calibration_attestation.json").read_text())
    fp = att["free_parameters"]
    if not any(e.get("name") == ENTRY["name"] for e in fp["entries"]):
        fp["entries"].append(ENTRY)
    fp["n_entries"] = len(fp["entries"])
    g = att["governance"]
    head = (
        "session NYISO-NEXT-12 (2026-09-29), the incumbent keeper "
        "2026-09-28-nyisonext9-hq-floor-span replayed with ONE recipe delta, "
        "nyiso_ne_ac_node true (the NE AC tie on its own two-way node). "
        "Pre-registration: "
        f"docs/PRECOMMIT-nyiso-next11-ne-ac-node-2026-09-28.md; arm pinned at {a.pin}. "
        "Offer curves byte-identical to the keeper (rule 1(c)); no multiplier tuned; "
        "zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-12"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
