#!/usr/bin/env python3
"""miso-298 attestation amendment (ZERO LP): stamp the composed span's governance block.

The composed span inherits the keeper's ``calibration_attestation.json`` (each
leg is a ``replay_keeper`` of ``miso280_span``). This probe rewrites it for the
miso-298 arm exactly as PRECOMMIT-miso298 §7 declares:

* ``governance.mechanism_armed`` -> nested under
  ``governance.mechanism_armed_inherited`` (keyed by the keeper's lane) and
  replaced by the miso-298 block (the two owner-ruled gas fields, zero fitted
  scalars, DOF +0);
* ``governance.attested_by`` prefixed with the miso-298 statement (the keeper's
  text follows as "Inherited: ...");
* ``authorized_price_tuning`` UNCHANGED (the K table is not touched);
* a top-level ``miso298`` block: precommit, pin, delta, ruling (verbatim), legs
  (year -> shard commit SHA), control, dof_added 0, measured_inputs.

Usage (repo root)::

    .venv/bin/python scripts/probes/_miso298_attest.py \\
        --bundle results/calibration/miso298_span --pin <40-char> \\
        --leg 2019=<sha> --leg 2020=<sha> ... --leg 2025=<sha>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso280_span/calibration_attestation.json"
PRECOMMIT = "docs/records/miso/PRECOMMIT-miso298-gas-form-alone-2026-10-01.md"
RULING = (
    "owner ruling 2026-10-01 (miso-297 decision card 'What should miso-298 do?'): "
    "'Gas form alone, full span (Recommended)' -- 7 shards of the owner-ruled "
    "convention only (hub + measured variable transport, no coal change). Settles "
    "the two O cells over 2019-2025. Convention ruled 2026-09-06 (miso-225 "
    "PRECOMMIT s1): MISO gas = marginal commodity (zone's measured daily hub) PLUS "
    "measured variable transport"
)


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--pin", required=True)
    ap.add_argument("--leg", action="append", default=[], metavar="YEAR=SHA")
    args = ap.parse_args()
    if len(args.pin) != 40:
        raise SystemExit("--pin must be the full 40-char SHA")
    bundle = REPO / args.bundle
    path = bundle / "calibration_attestation.json"
    src = path if path.exists() else KEEPER
    att = json.loads(src.read_text())
    gov = att["governance"]
    if "miso298" in att:
        raise SystemExit("already stamped (miso298 block present)")
    inherited = dict(gov.get("mechanism_armed_inherited") or {})
    prev = gov.get("mechanism_armed")
    if prev is not None:
        inherited["miso280_and_earlier"] = prev
    gov["mechanism_armed_inherited"] = inherited
    gov["mechanism_armed"] = {
        "field": "miso_gas_marginal_commodity_pricing + miso_gas_variable_transport",
        "value": {
            "miso_gas_marginal_commodity_pricing": True,
            "miso_gas_variable_transport": True,
        },
        "level": (
            "NO LEVEL PARAMETER. Fuel = the zone's measured daily hub (Chicago "
            "Citygate flow-day for the Chicago/MidCon zones, Henry Hub for "
            "MISO-South) + the plant's measured variable transport (frozen derive "
            "data/raw/reference/miso_gas_variable_transport.csv: own-plant rung, "
            "else zone|group / group / MISO-wide $0.5036); zero fitted scalars"
        ),
        "free_parameters_added": 0,
        "basis": (
            "rules 13/14 [R-MEASURED]/[R-ACCURATE]: a traded hub and a per-plant "
            "transport rate (forward analogue = the forecast path's hub + basis); "
            + RULING
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: supersedes on every MISO gas row the EIA-923 "
            "average print, the winter shape overlay, the winter daily-delivered "
            "form (miso_winter_gas_daily_delivered stays true in the recipe and is "
            "inert under this field) and the zonal basis increment"
        ),
        "window": "all hours, all years 2019-2025",
        "control": (
            "the committed keeper results/calibration/miso280_span (rule 29(b) form "
            "4); G-DRIFT 8f765fef..pin 0 LIVE (GDRIFT-miso297 + GDRIFT-miso298); "
            "solve_surface_register --diff: MISO moved rows 0"
        ),
        "prereg": f"{PRECOMMIT} @ {args.pin}, pushed BEFORE any shard",
    }
    gov["attested_by"] = (
        f"miso-298 (2026-10-01) -- keeper 2026-09-28-miso-280-splitremap recipe PLUS "
        "miso_gas_marginal_commodity_pricing=true and miso_gas_variable_transport=true "
        "(the owner-ruled MISO gas convention: zone's measured daily hub + measured "
        "per-plant variable transport; no coal change; offer_curve_by_group "
        f"byte-identical; zero free parameters; PRECOMMIT pinned {args.pin[:8]}). "
        "Inherited: " + str(gov.get("attested_by", ""))
    )
    legs = {}
    for spec in args.leg:
        y, _, sha = spec.partition("=")
        legs[y] = sha
    att["miso298"] = {
        "precommit": PRECOMMIT,
        "pin": args.pin,
        "delta": (
            "keeper 2026-09-28-miso-280-splitremap recipe + "
            "miso_gas_marginal_commodity_pricing=true + miso_gas_variable_transport=true"
        ),
        "ruling": RULING,
        "legs": legs,
        "control": (
            "keeper bundle miso280_span (G-DRIFT 8f765fef..pin: every hunk INERT; "
            "rule 29(b) form 4)"
        ),
        "dof_added": 0,
        "measured_inputs": (
            "Chicago Citygate and Henry Hub daily spot (data/raw/gas-prices/"
            "miso_citygate_daily.csv, henry_hub_daily.csv); zone->hub map "
            "data/raw/miso_zonal_gas_hub.csv; per-plant variable transport derived "
            "from EIA-923 plant receipts (frozen derive, rule 23)"
        ),
    }
    path.write_text(json.dumps(att, indent=2) + "\n")
    print(f"stamped {path.relative_to(REPO)} (legs: {sorted(legs)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
