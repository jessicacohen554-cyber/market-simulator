"""NYISO-NEXT-9: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars, a measured-input derivation correction) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext8_attest.py --keeper results/calibration/nyisonext8_span \\
        --out results/calibration/nyisonext9_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO HQ_hydro always-on 900 MW firm-import floor REMOVED (nyiso_firm_imports false)",
    "where": (
        "ScenarioConfig.nyiso_firm_imports (existing field, default False) -- the keeper "
        "recipe flips True -> False; model/interchange/nyiso.py inject_nyiso_firm_imports "
        "and spec.py NYISO_FIRM_IMPORT_FLOOR_FRAC no longer reached"
    ),
    "identification": "structural-removal",
    "lineage_solves": "1 (NYISO-NEXT-9, five year-isolated shards)",
    "value": {
        "rule": "HQ_hydro becomes an ordinary economic rung at its measured Q-Q price; "
        "the monthly import level stays set by nyiso_import_reconciliation (measured "
        "EIA-930 band)",
        "footprint": "D-2 firm_import 7.884 TWh/yr -> 0; arm hours with import < 900 MW "
        "0/0/52/162/172 (2021-2025); annual import TWh unchanged to <= 0.006",
    },
    "n_scalars": 0,
    "removed_scalars": 1,
    "source": "no published HQ firm energy quantity exists for 2021-2025 (Gold Book "
    "Table V-1 is aggregate ICAP; Table III-3d is realized GWh); the 900 MW level was "
    "an outcome percentile of measured net import (rule 13) with no window (rule 17).",
    "root_cause": "not a residual closer: an unledgered, windowless, outcome-level floor "
    "removed on structure (rules 13/17/19). Record: "
    "docs/PRECOMMIT-nyiso-next9-hq-floor-2026-09-28.md.",
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
        "session NYISO-NEXT-9 (2026-09-28), the incumbent keeper "
        "2026-09-27-nyisonext8-hq-dedupe-span replayed with ONE recipe delta, "
        "nyiso_firm_imports false (the 900 MW HQ_hydro always-on floor removed). "
        "Pre-registration: "
        f"docs/PRECOMMIT-nyiso-next9-hq-floor-2026-09-28.md; arm pinned at {a.pin}. "
        "Offer curves byte-identical to the keeper (rule 1(c)); no multiplier tuned; "
        "zero free parameters added, one outcome-level floor removed. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-9"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
