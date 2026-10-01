"""NYISO-NEXT-15: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext15_attest.py --keeper results/calibration/nyisonext14_span \\
        --out results/calibration/nyisonext15_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO pooled import node banded per landing link on the measured P-32 "
    "attributed schedule (nyiso_import_landing_band true)",
    "where": (
        "ScenarioConfig.nyiso_import_landing_band (default False) -- the keeper recipe "
        "flips False -> True; model/interchange/nyiso.py build_nyiso_import_landing_band "
        "+ model/lp/rows.py _build_import_link_rows REPLACE the pooled EIA-930 monthly "
        "band (rule 19: replaces, never stacks)"
    ),
    "identification": "structural (measured inputs, frozen formulas)",
    "lineage_solves": "1 (NYISO-NEXT-15, five year-isolated shards)",
    "value": {
        "rule": "per pooled border link and calendar month, the link's measured MIS P-32 "
        "attributed net schedule (published PAR split; NE AC row on its own node), "
        "+/- NYISO_IMPORT_RECON_BAND_FRAC (the existing 2 %)",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO MIS P-32 external schedules + the NY-NJ PAR interchange posting "
    "(data/nyiso_par_attribution.attributed_zone_net).",
    "root_cause": "not a residual closer: the pooled band pinned only the node's total, "
    "so the LP landed imports where the zonal price was highest -- downstate links at "
    "their p90 envelopes (+400-560 MW over their measured schedules) and Upstate_West "
    "264-375 MW short, every year -- a phantom import east of the Central-East cutset. "
    "Rule 14 alignment: pooled total EIA-930 -> P-32 sum (-2..+1 %). Record: "
    "docs/records/nyiso/PRECOMMIT-nyiso-next15-landing-band-2026-09-30.md.",
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
        "session NYISO-NEXT-15 (2026-09-30), the incumbent keeper "
        "2026-09-30-nyisonext14-total-east-span replayed with ONE recipe delta, "
        "nyiso_import_landing_band true (each pooled border link banded monthly on its "
        "own measured P-32 schedule; owner cards 'Build + test 5 yrs', 'P-32 per link'). "
        "Pre-registration: docs/records/nyiso/PRECOMMIT-nyiso-next15-landing-band-2026-09-30.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-15"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
