"""NYISO-NEXT-16: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext15_attest.py --keeper results/calibration/nyisonext15_span \\
        --out results/calibration/nyisonext16_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO zonal delivered gas on each zone's own measured hub-month level "
    "(nyiso_iroquois_winter_spread true)",
    "where": (
        "ScenarioConfig.nyiso_iroquois_winter_spread (default False) -- the keeper recipe "
        "flips False -> True; data/fuel/basis/nyiso.py nyiso_reconciled_reference_monthly + "
        "nyiso_zonal_gas_ratios_monthly REPLACE the flat annual additive zone offsets on "
        "the same seam (rule 19: replaces, never stacks)"
    ),
    "identification": "structural (measured inputs, frozen formulas)",
    "lineage_solves": "2 (nyiso-150 rejection under the coupled block; NYISO-NEXT-16, five "
    "year-isolated shards under the cutset link)",
    "value": {
        "rule": "Iroquois Z2 reference = Transco Z6 NY month + the SOM annual Iroquois-Transco "
        "spread allocated by the measured Algonquin basis, capped at the Algonquin Citygate "
        "month (annual preserved); NYC at Transco month; Upstate_West at its SOM Tenn Z4 "
        "annual on the Henry Hub within-year shape",
    },
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO SOM Figure A-6 zonal hub annuals (data/raw/nyiso_zonal_gas_hub.csv), "
    "EIA NGWU Transco Z6 NY, Henry Hub monthly, NEISO Algonquin basis rows.",
    "root_cause": "not a residual closer: the flat additive offset put Upstate_West gas on the "
    "Iroquois/New England winter shape (Jan 2022 9.67 vs 3.71 $/MMBtu on its own hub; 2025 "
    "summer 0.24-0.80 vs ~2.4). nyiso-150 refused it under rule 14's misalignment exception "
    "because the mainland priced as one coupled block; the NEXT-14 cutset link removed that "
    "premise. Record: docs/PRECOMMIT-nyiso-next16-winter-spread-2026-09-30.md.",
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
        "session NYISO-NEXT-16 (2026-09-30), the incumbent keeper "
        "2026-09-30-nyisonext15-landing-band-span replayed with ONE recipe delta, "
        "nyiso_iroquois_winter_spread true (each zone's delivered gas on its own measured "
        "hub-month level; owner card 'Re-test, 5 yrs'). "
        "Pre-registration: docs/PRECOMMIT-nyiso-next16-winter-spread-2026-09-30.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-16"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
