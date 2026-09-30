"""NYISO-NEXT-17: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext17_attest.py --keeper results/calibration/nyisonext16_span \\
        --out results/calibration/nyisonext17_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO F/G re-partition: zone G in Lower_Hudson, TOTAL EAST as its two "
    "measured legs (nyiso_fg_split true)",
    "where": (
        "ScenarioConfig.nyiso_fg_split (default False; requires nyiso_total_east_cutset_ttc) "
        "-- the keeper recipe flips False -> True; config.topology_variant moves zone G "
        "from Capital_Hudson to Lower_Hudson in every membership map, and "
        "pipeline/ttc.py::apply_iso_monthly_ttc REPLACES the one-link cutset envelope with "
        "CENT EAST DAM TTC on Upstate_West->Capital_Hudson plus "
        "NYISO_TE_NONCE_ENVELOPE_BY_MONTH on the new Upstate_West->Lower_Hudson link "
        "(rule 19: replaces, never stacks)"
    ),
    "identification": "structural (published zone letters, posted limits, measured p90 "
    "envelope on the inherited construction)",
    "lineage_solves": "1 (NYISO-NEXT-17, five year-isolated shards)",
    "value": {
        "rule": "zone G counties/load/DR/PAR landings -> Lower_Hudson; UW->CH at the posted "
        "CENT EAST DAM TTC; UW->LH at the monthly p90 of measured TOTAL EAST minus CENTRAL "
        "EAST (25 MW rounding); border capability 1,600 CH re-split 600 CH / 1,000 LH",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO MIS P-32 interface flows/limits (TOTAL EAST, CENTRAL EAST - VC); NYISO "
    "A-K hourly load actuals; county -> load-zone assignment; NYISO Gold Book tie landings.",
    "root_cause": "not a residual closer: the five-zone model carried zone G's load and plants "
    "in a zone priced and scored as F (CAPITL), and carried the E->F CENTRAL EAST constraint "
    "only as a TOTAL EAST envelope. Record: docs/DESIGN-nyiso-next17-fg-split-2026-09-30.md, "
    "docs/PRECOMMIT-nyiso-next17-fg-split-2026-09-30.md.",
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
        "session NYISO-NEXT-17 (2026-09-30), the incumbent keeper "
        "2026-09-30-nyisonext16-winter-spread-span replayed with ONE recipe delta, "
        "nyiso_fg_split true (zone G to Lower_Hudson; TOTAL EAST as its two measured legs; "
        "owner card 'Build design A anyway'). "
        "Pre-registration: docs/PRECOMMIT-nyiso-next17-fg-split-2026-09-30.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-17"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
