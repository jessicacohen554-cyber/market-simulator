"""NYISO-NEXT-14: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext14_attest.py --keeper results/calibration/nyisonext13_span \\
        --out results/calibration/nyisonext14_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO Upstate_West -> Capital_Hudson link capped at the measured TOTAL EAST "
    "cutset envelope (nyiso_total_east_cutset_ttc true)",
    "where": (
        "ScenarioConfig.nyiso_total_east_cutset_ttc (default False) -- the keeper recipe "
        "flips False -> True; pipeline/ttc.py apply_iso_monthly_ttc selects "
        "constants.NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH in place of "
        "NYISO_INTERFACE_TTC_BY_MONTH on that one link (rule 19: replaces, never stacks)"
    ),
    "identification": "structural (measured inputs, frozen formulas)",
    "lineage_solves": "2 (nyiso-224 2022 screen; NYISO-NEXT-14, five year-isolated shards)",
    "value": {
        "rule": "per calendar month, the p90 of the directionally-clipped measured MIS "
        "P-32 TOTAL EAST flow, rounded to 25 MW (the nyiso-125 border-link construction)",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO MIS P-32 TOTAL EAST posted hourly flow "
    "(scripts/data/derive_nyiso_total_east_envelope.py).",
    "root_cause": "not a residual closer: the model's one Upstate_West -> Capital_Hudson "
    "link is the A-E -> east cutset (TOTAL EAST) but was capped at the CENTRAL EAST "
    "sub-cutset, which the measured cutset flow exceeds in 60-99 % of hours; the "
    "upstate surplus then cleared at the pooled node price, <= $0 for up to 3,110 h/yr "
    "against 0 h measured. Rule 14 misalignment exception. Record: "
    "docs/PRECOMMIT-nyiso-next14-total-east-cutset-2026-09-30.md.",
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
        "session NYISO-NEXT-14 (2026-09-30), the incumbent keeper "
        "2026-09-29-nyisonext13-recon-detach-span replayed with ONE recipe delta, "
        "nyiso_total_east_cutset_ttc true (the upstate->east link at the measured "
        "TOTAL EAST cutset envelope; owner card 'Re-test all 5 years'). Pre-registration: "
        "docs/PRECOMMIT-nyiso-next14-total-east-cutset-2026-09-30.md; arm pinned at "
        f"{a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-14"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
