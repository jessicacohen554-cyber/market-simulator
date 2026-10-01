"""NYISO-NEXT-6: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry (zero
scalars, measured-physical) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext6_attest.py --keeper results/calibration/nyisonext3_span \\
        --out results/calibration/nyisonext6_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "Long Island seam posted-limit sub-clip",
    "where": (
        "src/market_sim/data/nyiso_seam_envelope.py nyiso_li_posted_limit_cap, applied in "
        "scripts/run_calibration.py run_year after the armed seam envelope "
        "(ScenarioConfig.nyiso_li_seam_posted_limit_cap)"
    ),
    "identification": "measured-physical",
    "lineage_solves": "1 (NYISO-NEXT-6, five year-isolated shards)",
    "value": {
        "rule": "Long_Island import cap_h = min(envelope_h, posted import limit of "
        "SCH - PJM_NEPTUNE + SCH - NPX_CSC + SCH - NPX_1385 in hour h)",
        "footprint": "860 / 1,468 / 1,688 / 969 / 1,734 hours and 0.160 / 0.343 / 0.268 / "
        "0.269 / 0.308 TWh of cap removed 2021-2025; no other link moves",
    },
    "n_scalars": 0,
    "source": "NYISO MIS P-32 ExternalLimitsFlows posted positive limits (the same committed "
    "file the envelope reads); a line on outage posts 0.",
    "root_cause": "not a residual closer: the p90 envelope pools each (month x hour) bin's "
    "outage days with its in-service days, so it let the model import over a tie posting 0. "
    "Zero free parameters; backcast-only, outage-window class (rule 13). Bounded ex ante at "
    "~+0.15 $/MWh of system C3a (PRECOMMIT-nyiso-next5 sec. 4).",
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
        "session NYISO-NEXT-6 (2026-09-27), ONE-FLAG ARM of the incumbent keeper "
        "2026-09-26-nyisonext3-tranche-basis-span: + nyiso_li_seam_posted_limit_cap (a clip "
        "inside the armed seam envelope, rule 19). Pre-registration: "
        "docs/records/nyiso/PRECOMMIT-nyiso-next5-li-tie-posted-limit-2026-09-27.md sec. 6-7 and its sec. 9 "
        f"addendum; arm pinned at {a.pin}. Offer curves byte-identical to the keeper "
        "(rule 1(c)); no multiplier tuned; zero free parameters. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-6"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
