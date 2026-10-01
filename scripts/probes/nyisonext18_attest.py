"""NYISO-NEXT-18: write a composed bundle's calibration_attestation.json from the keeper's (zero LP).

Copies the incumbent keeper bundle's attestation, appends this lane's DOF-ledger entry
(zero scalars; a band-scope change) and prepends the lane to ``governance.attested_by``.

Usage::

    python3 scripts/probes/nyisonext17_attest.py --keeper results/calibration/nyisonext16_span \\
        --out results/calibration/nyisonext18_span --pin <arm sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ENTRY = {
    "name": "NYISO mid-vintage retiree carry: Indian Point 3 restored Jan-Apr 2021 in "
    "Lower_Hudson (mid_vintage_exit_carry + fleet_zone_vintage_coords + "
    "retiree_vintage_status_scope true)",
    "where": (
        "ScenarioConfig.mid_vintage_exit_carry / fleet_zone_vintage_coords / "
        "retiree_vintage_status_scope (all default False) -- the keeper recipe flips each "
        "False -> True; data/fleet/eia860.py::load_retired_within_window injects the plants "
        "the solve year's own EIA-860 vintage drops because they retired during that year, "
        "drops a retiree its contemporaneous vintage marks non-OP, and "
        "_assign_zones zones a plant eGRID 2023 lacks from the active vintage's coordinates"
    ),
    "identification": "measured (EIA-860 retirement month, generator status and plant "
    "coordinates of the solve year's own vintage)",
    "lineage_solves": "1 (NYISO-NEXT-18, five year-isolated shards)",
    "value": {"rule": "membership and zone from EIA-860; no scalar"},
    "n_scalars": 0,
    "removed_scalars": 0,
    "source": "EIA-860 vintages 2021-2025 (Retired and Canceled sheet, generator status, "
    "plant latitude/longitude); NYISO RT fuel mix for the G-3 check.",
    "root_cause": "not a residual closer: Indian Point 3 (1,039 MW, zone H) retired "
    "2021-04-30 and so sat in neither sheet the retiree channel reads under "
    "eia860_vintage_tracks_solve_year; the keeper was ~1,058 MW short of measured NYCA "
    "nuclear in Jan-Apr 2021. Record: "
    "docs/records/nyiso/FINDING-nyiso-next18-upstate-price-phase0-2026-09-30.md, "
    "docs/records/nyiso/PRECOMMIT-nyiso-next18-retiree-carry-2026-09-30.md.",
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
        "session NYISO-NEXT-18 (2026-09-30), the incumbent keeper "
        "2026-09-30-nyisonext16-winter-spread-span replayed with THREE recipe deltas, "
        "mid_vintage_exit_carry, fleet_zone_vintage_coords and retiree_vintage_status_scope "
        "true (Indian Point 3 restored Jan-Apr 2021 in Lower_Hudson). "
        "Pre-registration: docs/records/nyiso/PRECOMMIT-nyiso-next18-retiree-carry-2026-09-30.md; arm "
        f"pinned at {a.pin}. Offer curves byte-identical to the keeper (rule 1(c)); no "
        "multiplier tuned; zero free parameters added. PRIOR: "
    )
    if not g["attested_by"].startswith("session NYISO-NEXT-18"):
        g["attested_by"] = head + g["attested_by"]
    (a.out / "calibration_attestation.json").write_text(
        json.dumps(att, indent=1) + "\n"
    )
    print(
        f"wrote {a.out / 'calibration_attestation.json'} ({fp['n_entries']} DOF entries)"
    )


if __name__ == "__main__":
    main()
