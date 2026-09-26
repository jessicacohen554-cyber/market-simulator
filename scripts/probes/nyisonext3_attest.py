"""NYISO-NEXT-3: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry (zero
scalars, measured-physical) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext3_attest.py --keeper results/calibration/nyisonext2_span \\
        --out results/calibration/nyisonext3_span --pin <PRECOMMIT sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "committed tranche share on the solve's own availability basis",
    "where": (
        "src/market_sim/data/fleet/campd_bins.py fleet_to_bins (the committed-share read now "
        "passes the merit_guard selector); data/raw/_processed-legacy/"
        "thermal_tranches-perunitmerit-NYISO.csv re-derived (frozen derive layer, rule 23)"
    ),
    "identification": "measured-physical",
    "lineage_solves": "1 (NYISO-NEXT-3, five year-isolated shards)",
    "value": {
        "repair": "one availability basis per LP (rule 19): committed_pct read from the "
        "'-perunitmerit-' artifact like every other tranche consumer; artifact re-derived on "
        "the current outage extract",
        "footprint": "pmax split committed<->econ at 7 ST_GAS + 5 CC plant-classes; plant totals, "
        "floor totals, heat rates, availability and offers unchanged",
    },
    "n_scalars": 0,
    "source": "CAMPD unit-level gross load and the merit-guarded outage extract (nyiso-192 + "
    "NYISO-NEXT-2 basis); Astoria committed 9.0 % vs measured median loading 9-15 % when on.",
    "root_cause": "not a residual closer: a selector omission read a stale unguarded artifact, and "
    "the guarded artifact had lagged two extract re-derivations (drift fully attributed: HEAD's "
    "deriver on the nyiso-187 extract reproduces the committed rows exactly). Zero free parameters; "
    "backcast-only (rule 13).",
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
        "session NYISO-NEXT-3 (2026-09-26), CORRECTNESS-REPAIR ARM of the incumbent keeper "
        "2026-09-26-nyisonext2-astoria-pair-span: ZERO scenario_config changes; the bin "
        "builder's committed share read on the full CAMPD artifact selector pair and the "
        "'-perunitmerit-' tranche artifact re-derived on the current outage basis (rules 19, 23). "
        f"Pre-registration: docs/PRECOMMIT-nyiso-next3-tranche-basis-2026-09-26.md, pushed at "
        f"{a.pin} before any solve. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-3"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)")


if __name__ == "__main__":
    main()
