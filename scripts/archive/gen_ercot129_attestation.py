"""Generate the ercot-129 keeper bundle's DOF ledger (CLAUDE.md rule 21).

Derives the new ERCOT keeper's ``calibration_attestation.json`` from the
outgoing ercot-115 keeper's, applying exactly one delta — the one the ercot-129
promotion makes.

The delta is **additive and measured**: the coal MINIMUM ONLINE CONFIGURATION
floor (``ScenarioConfig.ercot_coal_min_config_floor``) arms a new mechanism whose
level is a per-plant EIA-860 REGISTRATION value, ``min over units u of
Minimum Load (MW)``. It retires nothing from the fitted surface, so
``offer_curve_by_group`` is untouched at 111 free scalars; it adds one
``measured-physical`` entry carrying **zero** free scalars and zero residual
lineage. The mechanism is therefore DOF-neutral: the keeper gains real physics
without gaining a tunable.

**No governance block is written, and C6 stays UNATTESTED — deliberately, and
like-for-like with the outgoing keeper.** The C6 gate requires asserting all
four claims including ``levers_trace_to_measured_input``, which is FALSE for
this configuration: eight residual-identified DOF entries remain, exactly as
they did for ercot-115 (whose own generator records the same refusal). Arming
one measured mechanism is progress on that surface, not the end of it; asserting
otherwise to turn a gate green is the self-deception the rubric exists to catch.

Run from the repo root:
    python scripts/gen_ercot129_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO / "results" / "calibration" / "ercot115_coal_floor_only"
TARGET = REPO / "results" / "calibration" / "ercot129_conditional"


def build(source: dict) -> dict:
    """Return the new ledger: one measured entry added, nothing else moved."""
    out = json.loads(json.dumps(source))  # deep copy
    fp = out["free_parameters"]
    entries = fp["entries"]

    if any(e["name"].startswith("ercot_coal_min_config_floor") for e in entries):
        raise SystemExit(
            "the source attestation already carries the min-config entry — "
            "it is not the expected pre-promotion ercot-115 keeper"
        )

    entries.append(
        {
            "name": "ercot_coal_min_config_floor (coal minimum online configuration)",
            "where": (
                "ScenarioConfig.ercot_coal_min_config_floor -> "
                "data.fleet.coal_min_config -> "
                "data.fleet.arrays._compose_min_gen_floors (MECH_COAL_MIN_CONFIG)"
            ),
            "identification": "measured-physical",
            "lineage_solves": (
                "0 residual solves — every level is read from the frozen derive "
                "artifact and none was ever tuned against a residual (rule 23); "
                "the derive reads one registration file and takes a minimum, so "
                "it has no residual input by construction"
            ),
            "value": {
                "per_plant_min_config_mw": {
                    "Limestone": 300.0,
                    "W A Parish": 175.0,
                    "Martin Lake": 175.0,
                    "Coleto Creek": 175.0,
                    "Fayette": 156.0,
                    "Oak Grove": 348.0,
                    "San Miguel": 250.0,
                    "Major Oak": 95.0,
                    "J K Spruce": 130.0,
                    "Sandy Creek": 360.0,
                },
                "fleet_cap_weighted_frac": 0.1590,
                "capacity_exactly_representable": 0.9776,
            },
            "n_scalars": 0,
            "source": (
                "data/raw/_processed-legacy/coal_min_config_ERCOT.csv — per "
                "plant, min over its coal units of the EIA-860 registered "
                "'Minimum Load (MW)' (scripts/data/derive_eia860_coal_min_config.py, "
                "10 plants / 13,611 MW). A REGISTRATION filing by the operator, "
                "not measured operation and not an outcome of the dispatch being "
                "validated: it exists for any vintage and responds to condition "
                "(a retired unit leaves the file), so the same quantity "
                "regenerates for a forward year — the rule-13 admissibility "
                "test. Corroborated on an independent filing: the ERCOT COP LSL "
                "agrees EXACTLY on the three plants whose COP resources are "
                "whole units (Coleto Creek 175, Oak Grove 348, J K Spruce 130), "
                "and the fleet cap-weighted per-unit MinLoad/Cap of 0.3325 "
                "independently corroborates the ERCOT-127 §2 DAM-derived "
                "committed LSL/HSL p50 of 0.3636."
            ),
            "root_cause": (
                "NOT a free parameter at any point in its lineage. It removes a "
                "structural falsehood rather than closing a residual: the LP "
                "carries one variable per plant with no lower bound, so it could "
                "drive a coal plant to a level no combination of its units can "
                "physically deliver (ercot115 per-plant p05 loading 0.013-0.093 "
                "of declared against a real fleet whose floor is 0.106-0.261). "
                "Armed availability-CONDITIONALLY — the plant delivers its whole "
                "minimum configuration or nothing, since a minimum online "
                "configuration does not shrink when units go out — this cuts "
                "physically-impossible online plant-hours by 86 / 75 / 87 % "
                "against the availability-SCALED control "
                "(2026-07-28-ercot128-unit-grain-coal). The condition is "
                "evaluated on exogenous availability DATA, so it carries no "
                "integrality and does not touch the pure-LP rule."
            ),
        }
    )

    fp["n_entries"] = len(entries)
    fp["n_residual"] = sum(1 for e in entries if e["identification"] == "residual")
    fp["seeded"] = (
        str(fp.get("seeded", ""))
        + " | amended 2026-07-28 (ercot-129 promotion): coal minimum online "
        "configuration floor armed on the EIA-860 registered Minimum Load — "
        "ADDITIVE and measured, 0 new free scalars, offer_curve_by_group "
        "unchanged at 111"
    )
    return out


def main() -> None:
    """Write the new bundle's attestation from the outgoing keeper's."""
    src = json.loads((SOURCE / "calibration_attestation.json").read_text())
    out = build(src)
    path = TARGET / "calibration_attestation.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    fp = out["free_parameters"]
    print(f"wrote {path.relative_to(REPO)}")
    print(
        f"  entries {fp['n_entries']} (residual {fp['n_residual']}) — "
        "residual count UNCHANGED; the delta is additive and measured"
    )


if __name__ == "__main__":
    main()
