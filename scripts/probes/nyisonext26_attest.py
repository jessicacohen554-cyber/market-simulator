"""NYISO-NEXT-26: write a composed bundle's calibration_attestation.json from its control's (zero LP).

Copies the control bundle's attestation (arm A: the NEXT-21 keeper; arm B: NEXT-25 arm A),
appends this lane's DOF-ledger entry (zero scalars) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext26_attest.py --arm A --control results/calibration/nyisonext21_span \\
        --out results/calibration/nyisonext26_span --pin <pin sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "Zone-K published import security cap applied in every hour "
    "(nyiso_li_tsl_all_hours)",
    "where": (
        "model/interchange/nyiso.py::apply_nyiso_li_tsl_import_cap(all_hours=True): the "
        "published 940 MW N-1-1 limit on NYC>Long_Island in all hours, not HB14-21 only; "
        "ScenarioConfig.nyiso_li_tsl_all_hours=true"
    ),
    "identification": "the window follows the constraint's measured driver: NYISO DAM "
    "limiting constraints bind the Zone-K import security set in every season, 58-64 % of "
    "binding hours outside HB14-21 (rule 17); a published limit replaces the 1,650 MW "
    "Gold-Book seed off-window (rule 14)",
    "lineage_solves": "1 (NYISO-NEXT-26, five year-isolated shards per arm)",
    "value": {"rule": "window of an existing published constant; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "NYISO Locality Bulk Power Transmission Capability report, Long Island N-1-1 "
    "transmission security limit (data/raw/capacity-deliverability/nyiso/nyiso.csv); NYISO "
    "DAM limiting constraints (mis.nyiso.com DAMLimitingConstraints, diagnosis only).",
    "root_cause": "not a residual closer: a window narrower than its own driver. Record: "
    "docs/records/nyiso/FINDING-nyiso-next26-li-import-window-phase0-2026-10-01.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md.",
}
DELTA = {
    "A": "nyiso_li_tsl_all_hours=true",
    "B": "nyiso_gas_daily_print_level=true and nyiso_li_tsl_all_hours=true",
}


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(DELTA), required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pin", required=True)
    a = ap.parse_args()
    att = json.loads((a.control / "calibration_attestation.json").read_text())
    fp = att["free_parameters"]
    if not any(e.get("name") == ENTRY["name"] for e in fp["entries"]):
        fp["entries"].append(ENTRY)
    fp["n_entries"] = len(fp["entries"])
    g = att["governance"]
    head = (
        f"session NYISO-NEXT-26 arm {a.arm} (2026-10-01), the incumbent keeper "
        "2026-10-01-nyisonext21-astoria-hr-span replayed with the recipe delta "
        f"{DELTA[a.arm]}. Pre-registration: "
        "docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-26"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
