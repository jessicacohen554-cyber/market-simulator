"""NYISO-NEXT-21: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext21_attest.py --keeper results/calibration/nyisonext18_span \\
        --out results/calibration/nyisonext21_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO Astoria 8906 measured ST_GAS heat rate on the merged CEMS "
    "stack-duplicate meter (campd_st_heat_rates_NYISO.csv re-derived)",
    "where": (
        "scripts/data/derive_campd_gas_st_heat_rates.py::merge_stack_duplicates -> "
        "data/raw/_processed-legacy/campd_st_heat_rates_NYISO.csv (read under the "
        "keeper's existing measured_st_heat_rates); zero ScenarioConfig change"
    ),
    "identification": "measured (CAMPD unit-level heatInput / grossLoad, each split-boiler "
    "pair summed per hour with gross load counted once; campd.CAMPD_STACK_DUPLICATE_UNITS)",
    "lineage_solves": "1 (NYISO-NEXT-21, five year-isolated shards)",
    "value": {"rule": "per-plant CAMPD operating heat rate; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EPA CAMPD unit-level hourly 2019-2025 (NY); eGRID plant rate 11.75 as "
    "independent corroboration.",
    "root_cause": "not a residual closer: the derive scored Astoria's two monitored paths "
    "per boiler (31RH/32SH, 51RH/52SH) as separate units, each dividing half the fuel by "
    "the full repeated gross load; the per-hour band kept a biased 264-464 h sample -> "
    "9.449 net vs the merged meter's 11.645. Same defect nyiso-192 repaired in the outage "
    "panel. Record: docs/records/nyiso/FINDING-nyiso-next21-d4-rows-and-astoria-heat-rate-2026-10-01.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next21-astoria-heat-rate-2026-10-01.md.",
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
        "session NYISO-NEXT-21 (2026-10-01), the incumbent keeper "
        "2026-09-30-nyisonext18-retiree-carry-span replayed with ZERO recipe deltas on the "
        "re-derived campd_st_heat_rates_NYISO.csv (Astoria 8906 9.449 -> 11.18-12.07). "
        "Pre-registration: docs/records/nyiso/PRECOMMIT-nyiso-next21-astoria-heat-rate-2026-10-01.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-21"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
