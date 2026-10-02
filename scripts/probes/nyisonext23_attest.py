"""NYISO-NEXT-23: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a calendar-convention change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext23_attest.py --keeper results/calibration/nyisonext21_span \\
        --out results/calibration/nyisonext23_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO Transco Z6 NY daily prints placed on their gas FLOW day "
    "(nyiso_gas_flow_date)",
    "where": (
        "data/fuel/hubs.py::nyiso_transco_z6_flow_daily (reuses _flow_date_staircase), "
        "read by _nyiso_hub_daily_gas_prices and basis/nyiso.py::"
        "apply_nyiso_downstate_ct_gas_daily; ScenarioConfig.nyiso_gas_flow_date=true"
    ),
    "identification": "source convention (EIA daily spot is a next-day delivery index; "
    "Friday's trade prices the weekend/holiday package)",
    "lineage_solves": "1 (NYISO-NEXT-23, five year-isolated shards)",
    "value": {"rule": "calendar placement of a measured series; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EIA Natural Gas daily spot, Transco Zone 6 NY "
    "(data/raw/gas-prices/transco_z6_ny_daily.csv).",
    "root_cause": "not a residual closer: rule 14 on the source convention. Record: "
    "docs/records/nyiso/FINDING-nyiso-next23-c3a-2025-phase0-2026-10-01.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next23-z6-flow-date-2026-10-01.md.",
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
        "session NYISO-NEXT-23 (2026-10-01), the incumbent keeper "
        "2026-10-01-nyisonext21-astoria-hr-span replayed with ONE recipe delta, "
        "nyiso_gas_flow_date=true. Pre-registration: "
        "docs/records/nyiso/PRECOMMIT-nyiso-next23-z6-flow-date-2026-10-01.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-23"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
