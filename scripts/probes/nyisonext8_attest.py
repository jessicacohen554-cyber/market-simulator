"""NYISO-NEXT-8: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars, a measured-input derivation correction) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext8_attest.py --keeper results/calibration/nyisonext6_span \\
        --out results/calibration/nyisonext8_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO import ladder: HQ accounting duplicate removed from the derivation",
    "where": (
        "scripts/data/derive_nyiso_import_tranches.py EXTERNAL_SEAMS (imports "
        "nyiso_par_attribution.ACCOUNTING_DUPLICATE); src/market_sim/model/interchange/"
        "spec.py IMPORT_TRANCHES['NYISO'] and IMPORT_TRANCHES_BY_YEAR['NYISO'] 2018-2025"
    ),
    "identification": "measured-physical",
    "lineage_solves": "1 (NYISO-NEXT-8, five year-isolated shards)",
    "value": {
        "rule": "same frozen total-net Q-Q formula, with SCH - HQ_IMPORT_EXPORT (an "
        "accounting duplicate of SCH - HQ - NY) no longer summed into the net import",
        "footprint": "keeper-live rungs IESO_Ontario / PJM_shoulder / eastern_mid prices "
        "and the import_scarcity capacity (SIL retired); PJM_west / ISONE_tie / "
        "import_scarcity prices are overwritten by nyiso_import_hub_prices",
    },
    "n_scalars": 0,
    "source": "NYISO MIS P-32 ExternalLimitsFlows (hourly seam flows) and the measured "
    "NYISO DA zonal-mean LBMP -- unchanged sources, one duplicate row removed.",
    "root_cause": "not a residual closer: a derivation defect (HQ counted twice; corr "
    "0.955-0.993 in every year 2018-2025), corrected under rule 14 and cited under rule "
    "23. Record: docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md.",
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
        "session NYISO-NEXT-8 (2026-09-27), the incumbent keeper "
        "2026-09-27-nyisonext6-li-cap-span replayed unchanged on the HQ-deduped NYISO "
        "import ladder (a rule-14 derivation correction, no new field). Pre-registration: "
        f"docs/records/nyiso/PRECOMMIT-nyiso-next8-hq-dedupe-2026-09-27.md; arm pinned at {a.pin}. "
        "Offer curves byte-identical to the keeper (rule 1(c)); no multiplier tuned; "
        "zero free parameters. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-8"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
