"""NYISO-NEXT-13: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext13_attest.py --keeper results/calibration/nyisonext12_span \\
        --out results/calibration/nyisonext13_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO NE AC node detached from the monthly net-interchange band "
    "(nyiso_ne_ac_recon_detach true)",
    "where": (
        "ScenarioConfig.nyiso_ne_ac_recon_detach (default False) -- the keeper recipe "
        "flips False -> True; model/interchange/nyiso.py "
        "detach_nyiso_ne_ac_from_reconciliation / load_nyiso_ne_ac_measured_flow; "
        "scripts/run_calibration.py after build_import_node_reconciliation"
    ),
    "identification": "structural (measured inputs, frozen formulas)",
    "lineage_solves": "1 (NYISO-NEXT-13, five year-isolated shards)",
    "value": {
        "rule": "the 16 NE AC node rows leave the monthly band; the band target "
        "becomes EIA-930 net import minus the measured P-32 SCH - NE - NY monthly "
        "schedule; half-width re-taken at the same NYISO_IMPORT_RECON_BAND_FRAC",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EIA-930 NYIS net interchange (the band's existing target) and NYISO "
    "P-32 SCH - NE - NY hourly flow (the node's existing posted-limit source).",
    "root_cause": "not a residual closer: the band pinned the node together with the "
    "pooled seams and, as the band's only export-capable row, the node was moved off "
    "its own bands by the band's dual (phase 0: 34-63 % of hours on its bands). "
    "Detaching pins strictly fewer measured outcomes (rule 13) and leaves one "
    "mechanism setting the node's flow (rule 19). Record: "
    "docs/PRECOMMIT-nyiso-next13-ne-ac-recon-detach-2026-09-29.md.",
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
        "session NYISO-NEXT-13 (2026-09-29), the incumbent keeper "
        "2026-09-29-nyisonext12-neac-node-span replayed with ONE recipe delta, "
        "nyiso_ne_ac_recon_detach true (the NE AC node out of the monthly "
        "net-interchange band). Pre-registration: "
        "docs/PRECOMMIT-nyiso-next13-ne-ac-recon-detach-2026-09-29.md; arm pinned at "
        f"{a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-13"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
