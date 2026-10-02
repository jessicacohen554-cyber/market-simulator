"""NYISO-NEXT-34: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the keeper bundle's attestation (``nyisonext26p_span`` / ``nyisonext26p_2021``), appends
this lane's DOF-ledger entry (zero scalars) and prepends the lane to
``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext34_attest.py --control results/calibration/nyisonext26p_span \\
        --out results/calibration/nyisonext34_span --pin <pin sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "Gas units priced at the plant-day measured gas/oil burn mix "
    "(dual_fuel_measured_oil_burn)",
    "where": (
        "data/fuel/dual_fuel.py::apply_measured_oil_burn_pricing: on a CAMPD-covered "
        "plant-day a gas tranche is priced at f*oil + (1-f)*gas in place of the parity "
        "cap (rule 19); ScenarioConfig.dual_fuel_measured_oil_burn=true (backcast only)"
    ),
    "identification": "measured physical input: the plant-day oil share of gas-unit heat "
    "input from the CAMPD CO2 / heat-input mixing identity, zero thresholds or scalars "
    "(scripts/data/derive_measured_oil_burn_days.py --iso NYISO); admitted under rule 13 "
    "as a backcast overlay by the soco-96 owner ruling 2026-09-30",
    "lineage_solves": "1 (NYISO-NEXT-34, five year-isolated shards)",
    "value": {"rule": "measured per plant-day; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EPA CAMPD hourly emissions (CO2 mass, heat input), NYISO gas plants; "
    "data/raw/_processed-legacy/campd_measured_oil_burn_days_NYISO.csv",
    "root_cause": "not a residual closer: the parity cap can only lower fuel cost, so oil "
    "burned while gas was cheaper (Feb 3-4 2023, fleet oil share 0.43/0.49) had no "
    "representation. Record: "
    "docs/records/nyiso/FINDING-nyiso-next34-feb2023-oilburn-phase0-2026-10-02.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next34-measured-oil-burn-2026-10-02.md.",
}


def main() -> None:
    """CLI."""
    ap = argparse.ArgumentParser(description=__doc__)
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
        "session NYISO-NEXT-34 (2026-10-02), the incumbent keeper "
        "2026-10-01-nyisonext26p-tslprint-span replayed with the recipe delta "
        "dual_fuel_measured_oil_burn=true. Pre-registration: "
        "docs/records/nyiso/PRECOMMIT-nyiso-next34-measured-oil-burn-2026-10-02.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-34"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
