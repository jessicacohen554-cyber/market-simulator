"""NYISO-NEXT-25: write a composed bundle's calibration_attestation.json from its control's (zero LP).

Copies the control bundle's attestation (arm A: the NEXT-21 keeper; arm B: the NEXT-23 arm),
appends this lane's DOF-ledger entry (zero scalars) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext25_attest.py --arm A --control results/calibration/nyisonext21_span \\
        --out results/calibration/nyisonext25_span --pin <pin sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO daily gas priced at each day's own Transco Z6 NY print "
    "(nyiso_gas_daily_print_level)",
    "where": (
        "data/fuel/hubs.py::_nyiso_hub_daily_gas_prices (both branches: the day factor is "
        "print / trade-day print mean, not renormalised to a calendar-day mean); "
        "ScenarioConfig.nyiso_gas_daily_print_level=true"
    ),
    "identification": "the measured daily print is the day's price; the monthly hub level is "
    "a trade-day statistic, so no calendar-day re-centring (rule 14); one level for one "
    "commodity, as the downstate CTs already carry (rule 19)",
    "lineage_solves": "1 (NYISO-NEXT-25, five year-isolated shards per arm)",
    "value": {"rule": "construction of a measured series; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EIA Natural Gas daily spot, Transco Zone 6 NY "
    "(data/raw/gas-prices/transco_z6_ny_daily.csv).",
    "root_cause": "not a residual closer: a construction defect (trade-day level vs "
    "calendar-day factors). Record: "
    "docs/records/nyiso/FINDING-nyiso-next25-offcap-winter-gap-phase0-2026-10-01.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next25-print-level-2026-10-01.md.",
}
DELTA = {
    "A": "nyiso_gas_daily_print_level=true",
    "B": "nyiso_gas_flow_date=true and nyiso_gas_daily_print_level=true",
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
        f"session NYISO-NEXT-25 arm {a.arm} (2026-10-01), the incumbent keeper "
        "2026-10-01-nyisonext21-astoria-hr-span replayed with the recipe delta "
        f"{DELTA[a.arm]}. Pre-registration: "
        "docs/records/nyiso/PRECOMMIT-nyiso-next25-print-level-2026-10-01.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-25"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
