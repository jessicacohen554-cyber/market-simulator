#!/usr/bin/env python3
"""miso-91 replay: register the seasonal-availability constants and declare
them in the MISO keeper's DOF ledger.

Run from the repo root, AFTER applying
``docs/handoffs/patches/miso-91-summer-wefor-dof-src.patch`` (which re-homes
``SUMMER_WEFOR_SHARE`` / ``SUMMER_CLASS_DERATE`` into
``config/fuel_trajectories.py``). Exists because the miso-91 session could not
``git push`` -- the git proxy rejects ``git-receive-pack`` by policy -- so the
derived artifacts are shipped as a deterministic replay rather than as patches
into a 1.5 MB JSON whose hunk offsets would rot.

Idempotent: re-running changes nothing. Does three things.

1. Adds the five registry entries (``summer_wefor_share`` +
   ``summer_class_derate.*``) to ``frontend/data/parameters.json`` and
   re-renders ``docs/parameter-citations.md`` from the result.

   It deliberately does NOT call ``generate_parameter_registry.build_registry()``:
   that would additionally sweep in the 48 parameters already missing citations
   on main, auto-registering other lanes' gaps as ``needs-citation`` stubs and
   marking them documented without anyone having sourced them. After this
   script, ``validate_parameters.py`` returns to exactly its pre-existing 48 --
   the backlog is neither added to nor papered over.

2. Adds the two DOF ledger entries to the keeper attestation
   (26 -> 28 entries, 2 -> 4 residual), each with an open ``root_cause`` so
   ``audit_keepers.py`` E8 passes.

3. Appends a dated addendum to the attestation's ``governance.note``, whose
   opening "DETERMINATION NOT-YET" was overtaken by miso-90's re-gate to
   CALIBRATED-WITH-CAVEATS. miso-88's prose is left as written; no assertion is
   modified.

Preserves the bundle JSON convention: ``json.dumps(indent=2)``, ASCII-escaped,
NO trailing newline.

Verify afterwards:
    python scripts/validate_parameters.py          # -> FAIL: 48 (unchanged baseline)
    python scripts/calibration_verdict.py results/calibration/miso88_egrid_hr
    python scripts/audit_keepers.py --iso MISO     # -> PASS / 0
    python scripts/build_status.py --iso MISO      # regenerates the status shard
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

ATTESTATION = REPO / "results/calibration/miso88_egrid_hr/calibration_attestation.json"

# --------------------------------------------------------------------------
# 1. registry entries
# --------------------------------------------------------------------------

SHARE_SOURCE = (
    "UNCITED A-PRIORI HEURISTIC - declared, not sourced. Fraction of a unit's "
    "WEFOR (forced-outage rate, THERMAL_AVAILABILITY) applied during the summer "
    "peak (Jun-Sep); the remaining (1 - share) is redistributed into the "
    "shoulder months, conserving annual outage energy. Winter keeps flat WEFOR. "
    "No primary source, derivation, sweep or calibration lineage exists for the "
    "0.30: market-sim-build-plan.md records it as the 'flat per-plant-group POF "
    "heuristic' awaiting a data-derived replacement. It was NOT fitted to a "
    "residual. Note the WEFOR MAGNITUDE is GADS-cited (see "
    "thermal_availability.*); only this SEASONAL REALLOCATION of it is uncited. "
    "PHYSICS TENSION: for PLANNED outages, shifting maintenance off the peak is "
    "well-founded (the POF side is separately grounded by the measured "
    "MAINTENANCE_MONTHLY_SHAPE); for FORCED outages the reallocation runs "
    "OPPOSITE to the physics, since forced outages correlate POSITIVELY with "
    "heat and high load. Unverified directional argument, not a citation. "
    "MATERIALITY: governs all six non-coal thermal classes (COAL is exempt "
    "under coal_drop_pof) - ~3.9-5.8 GW of MISO summer-peak capability "
    "depending on fleet age, the same order as the ~10 GW under-derate ledgered "
    "as the MISO C3b caveat. DO NOT re-tune against a residual (rule 24): a "
    "hand-set value here would be an answer key for an already-ledgered miss. "
    "Replaceable ONLY by a measured seasonal forced-outage shape clearing "
    "docs/handoffs/miso-outage-grain-data-ask-2026-07.md, and per rule 23 that "
    "commit must cite the data change. Declared in the MISO keeper DOF ledger "
    "(miso-91, 2026-07-26)."
)

DERATE_SOURCE = (
    "UNCITED FLAT APPROXIMATION of a real, well-established physical effect. "
    "Additional summer (Jun-Sep) capacity derate modeling the "
    "ambient-temperature output loss gas turbines suffer in heat (gas-turbine "
    "mass flow falls as inlet air temperature rises; simple-cycle CTs lose more "
    "than combined-cycle, whose steam bottoming cycle partially compensates). "
    "The EFFECT is sound; the specific magnitudes 0.10 (CC) / 0.125 (CT) are "
    "not derived from a primary source - they are consistent with, but not "
    "fitted to, the 10-30% typical CT summer derate the repo's own capacity "
    "audit records against EIA-860 net-summer ratings "
    "(docs/capacity-audit-860-923-campd.md). A MEASURED per-class dry-bulb "
    "alternative exists as scenario.temp_dependent_derate (default-off, "
    "probe-refuted for the ERCOT gas fleet 2026-07-09); its MISO sibling "
    "scenario.gt_ambient_derate is measured PROVABLY INERT (MISO zone-mean TMAX "
    "clears its 35 C reference in 0 h at summer peak in 2023-2025). So rule 11 "
    "'prefer the measured input' is not engaged - the measured alternatives "
    "were tried and adjudicated, not skipped. Re-homed from "
    "data/fleet/arrays.py to config/fuel_trajectories.py (miso-91, 2026-07-26) "
    "for registry coverage; values unchanged."
)

REG_NOTES = (
    "Registered by miso-91 (2026-07-26) when the constant was re-homed from "
    "data/fleet/arrays.py to config/fuel_trajectories.py so "
    "scripts/validate_parameters.py covers it (that gate scans only "
    "vars(constants) + ScenarioConfig defaults and skips private/non-uppercase "
    "names, so the prior private literal was invisible to it three ways over - "
    "CLAUDE.md rule 20 [R-REGISTRY]). Value unchanged by the move."
)


def registry_entries():
    entries = [
        {
            "param_id": "summer_wefor_share",
            "display_name": "Summer WEFOR Share",
            "value": 0.3,
            "unit": "fraction of annual WEFOR",
            "domain": "Reliability",
            "tier": 3,
            "source": SHARE_SOURCE,
            "source_date": "",
            "page_or_table": "",
            "url": "",
            "notes": REG_NOTES,
            "old_repo_location": (
                "src/market_sim/data/fleet/arrays.py::_SUMMER_WEFOR_SHARE"
            ),
            "last_verified": "",
            "flags": ["needs-citation", "modeled", "residual-identified"],
        }
    ]
    for grp, val in (
        ("CC_REGULAR", 0.1),
        ("CC_CHP", 0.1),
        ("CT_PEAKER", 0.125),
        ("CT_CHP", 0.125),
    ):
        entries.append(
            {
                "param_id": f"summer_class_derate.{grp}",
                "display_name": (
                    f"Summer Class Derate / {grp.title().replace('_', ' ')}"
                ),
                "value": val,
                "unit": "fraction of capacity",
                "domain": "Reliability",
                "tier": 3,
                "source": DERATE_SOURCE,
                "source_date": "",
                "page_or_table": "",
                "url": "",
                "notes": REG_NOTES,
                "old_repo_location": (
                    "src/market_sim/data/fleet/arrays.py::_SUMMER_CLASS_DERATE"
                ),
                "last_verified": "",
                "flags": ["needs-citation", "modeled"],
            }
        )
    return entries


def do_registry():
    from generate_parameter_registry import (
        CITATIONS_MD,
        REGISTRY_PATH,
        render_markdown,
    )

    registry = json.loads(REGISTRY_PATH.read_text())
    have = {e["param_id"] for e in registry["parameters"]}
    added = [e for e in registry_entries() if e["param_id"] not in have]
    if added:
        registry["parameters"].extend(added)
        REGISTRY_PATH.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False) + "\n"
        )
        CITATIONS_MD.write_text(render_markdown(registry))
    print(
        f"[1] registry: added {len(added)} entries "
        f"({len(registry['parameters'])} total)"
    )


# --------------------------------------------------------------------------
# 2 + 3. DOF ledger + attestation addendum
# --------------------------------------------------------------------------

ROOT_CAUSE = (
    "OPEN ROOT CAUSE - no measured source resolves a seasonal forced-outage "
    "shape at the grain this parameter needs. Standing data ask: "
    "docs/handoffs/miso-outage-grain-data-ask-2026-07.md (acceptance test part 1 "
    "- the source must declare CAPABILITY, not output, which is what rejects "
    "CAMPD, EIA-923 and every derivative of either). The class where it binds "
    "hardest and is least recoverable is CT_PEAKER: CT down-windows cannot be "
    "certified forced-outage vs out-of-merit-at-peak, so every output-derived "
    "instrument inherits the defect (adjudicated NO-BUILD on identification "
    "grounds, results/calibration/"
    "FINDING-miso90-ct-availability-identification-2026-07.md). Until such a "
    "source exists the honest disposition is to DECLARE and stop (rule 24), "
    "NOT to tune. Re-derivation must cite the data change, never a residual "
    "(rule 23 [R-FROZEN-DERIVE])."
)

SHARE_ENTRY = {
    "name": "SUMMER_WEFOR_SHARE",
    "where": (
        "config/fuel_trajectories.py::SUMMER_WEFOR_SHARE (re-homed by miso-91 "
        "from data/fleet/arrays.py::_SUMMER_WEFOR_SHARE; consumed by "
        "data.fleet.arrays._apply_thermal_availability)"
    ),
    "identification": "residual",
    "lineage_solves": (
        "NONE - no sweep, derivation or calibration lineage exists for the 0.30"
    ),
    "value": {"SUMMER_WEFOR_SHARE": 0.30},
    "n_scalars": 1,
    "source": (
        "UNCITED A-PRIORI HEURISTIC, declared as such. Fraction of a unit's "
        "WEFOR applied in the summer peak (Jun-Sep); the remaining (1 - share) "
        "is redistributed into the shoulder months, conserving annual outage "
        "energy. market-sim-build-plan.md records it as the 'flat "
        "per-plant-group POF heuristic' awaiting a data-derived replacement. "
        "IMPORTANT ON THE LABEL: it was NEVER FITTED to a residual. It is "
        "classified 'residual' because that is the strictest existing "
        "enforcement category - audit_keepers.py E8 requires every residual "
        "entry to carry an open root cause - NOT because it was tuned. Read it "
        "as 'unidentified', which is if anything weaker than residual-fitted: "
        "there is no lineage at all. The WEFOR MAGNITUDE it reallocates IS "
        "GADS-cited (THERMAL_AVAILABILITY, 'Source: NERC GADS by unit type and "
        "age'); only the seasonal reallocation is uncited. MATERIALITY "
        "(measured by miso-91, no LP): it governs all SIX non-coal thermal "
        "classes under this keeper's flags - COAL is exempt because "
        "coal_drop_pof=True routes it to a branch that drops summer WEFOR "
        "entirely (measured delta 0.0000). Per-class summer availability the "
        "0.30 adds vs a flat-WEFOR baseline: ST_GAS +14.70 pp, ST_CHP +5.60, "
        "CT_PEAKER +4.29, CC_REGULAR +3.15, CT_CHP +3.06, CC_CHP +2.52. "
        "Against the committed per-class nameplates (FINDING-miso89 sec.5) that "
        "is ~3.9 GW of MISO summer-peak capability at a uniform fleet age of "
        "18 y, ~4.6 GW at 28 y, ~5.8 GW at 38 y. NOTE this corrects the "
        "miso-90 finding, which scoped the parameter to CT_PEAKER alone. "
        "PHYSICS TENSION: for PLANNED outages, shifting maintenance off the "
        "peak is well-founded (and the POF side is separately grounded by the "
        "measured MAINTENANCE_MONTHLY_SHAPE); for FORCED outages the "
        "reallocation runs OPPOSITE to the physics, since forced outages "
        "correlate POSITIVELY with heat and high load. Recorded as an "
        "unverified directional argument, not a citation."
    ),
    "root_cause": ROOT_CAUSE,
    "forecast_risk": (
        "Reproduces in a forecast year by construction (it is a fixed fraction "
        "applied to the age-escalated GADS WEFOR), so it is forward-runnable - "
        "but it does NOT respond to changed conditions: it carries no weather, "
        "load or temperature driver, so a hotter forecast year gets the same "
        "70% summer-outage relief as a mild one. That is the forecast-side cost "
        "of the missing measured shape."
    ),
    "prohibition": (
        "DO NOT re-tune against a residual (rule 24). Its ~3.9-5.8 GW blast "
        "radius is the same order as the ~10 GW summer-peak fossil under-derate "
        "ledgered as the C3b caveat, so a hand-set value here would be an "
        "answer key for an already-ledgered miss. The C3b ledger explicitly "
        "does not license a fitted availability number."
    ),
}

DERATE_ENTRY = {
    "name": "SUMMER_CLASS_DERATE",
    "where": (
        "config/fuel_trajectories.py::SUMMER_CLASS_DERATE (re-homed by miso-91 "
        "from data/fleet/arrays.py::_SUMMER_CLASS_DERATE)"
    ),
    "identification": "residual",
    "lineage_solves": "NONE - no derivation lineage for the 0.10 / 0.125 magnitudes",
    "value": {
        "CC_REGULAR": 0.10,
        "CC_CHP": 0.10,
        "CT_PEAKER": 0.125,
        "CT_CHP": 0.125,
    },
    "n_scalars": 2,
    "source": (
        "UNCITED FLAT APPROXIMATION of a real, well-established physical "
        "effect: gas-turbine output falls as inlet air temperature rises, and "
        "simple-cycle CTs lose more than combined-cycle (whose steam bottoming "
        "cycle partially compensates). The EFFECT is sound and the sign/ordering "
        "are right; the SPECIFIC magnitudes are not traced to a primary source "
        "- they are consistent with, but not derived from, the 10-30% typical CT "
        "summer derate the repo's own capacity audit records against EIA-860 "
        "net-summer ratings (docs/capacity-audit-860-923-campd.md). Two "
        "distinct scalars (0.10 CC, 0.125 CT) over four class keys. Labelled "
        "'residual' for the same enforcement reason as SUMMER_WEFOR_SHARE: it "
        "was never fitted, but it is unidentified and must carry an open root "
        "cause."
    ),
    "root_cause": (
        "OPEN but LOWER PRIORITY than SUMMER_WEFOR_SHARE, because the measured "
        "alternatives have already been built and adjudicated rather than "
        "skipped - so rule 11 [R-ACCURATE] is not engaged. "
        "scenario.temp_dependent_derate is a measured per-class dry-bulb curve "
        "and is default-off, probe-refuted for the ERCOT gas fleet 2026-07-09. "
        "Its MISO sibling scenario.gt_ambient_derate is measured PROVABLY INERT: "
        "MISO zone-mean TMAX clears its 35 C reference in 0 h at summer peak in "
        "any of 2023-2025 (FINDING-miso89 sec.8). Closing this needs a primary "
        "OEM/NREL ambient-derate citation for the two magnitudes, not a new "
        "mechanism."
    ),
}

SEEDED_SUFFIX = (
    " | miso-91 2026-07-26: added SUMMER_WEFOR_SHARE + SUMMER_CLASS_DERATE, the "
    "seasonal-availability constants re-homed from data/fleet/arrays.py to "
    "config/fuel_trajectories.py so scripts/validate_parameters.py covers them "
    "(CLAUDE.md rules 5 / 20 / 21). Values UNCHANGED by that move - declaration "
    "only, no solve, no re-tune."
)

ADDENDUM = (
    " || ADDENDUM 2026-07-26 (miso-91), correcting a stale statement of fact in "
    "the text above, which is otherwise left as miso-88 wrote it: the opening "
    "'DETERMINATION NOT-YET' is NO LONGER CURRENT. miso-90 re-gated MISO to "
    "CALIBRATED-WITH-CAVEATS by SCORING ALONE (no solve, keeper unchanged) when "
    "the owner ledgered C3b-2025 as an instrument-blocked measurement gap on "
    "2026-07-26. The two crossings named above are unchanged in magnitude; what "
    "changed is that C3b is now a ledgered caveat rather than an unledgered "
    "model miss, taking the non-protective ledgered-caveat budget to 3/3 "
    "(C3a, C3b, C3c) - saturated. No assertion in this block is modified by "
    "this addendum."
)


def do_attestation():
    raw = ATTESTATION.read_bytes()
    d = json.loads(raw)
    fp = d["free_parameters"]
    have = {e.get("name") for e in fp["entries"]}
    added = 0
    for entry in (SHARE_ENTRY, DERATE_ENTRY):
        if entry["name"] not in have:
            fp["entries"].append(entry)
            added += 1
    if added:
        fp["n_entries"] = len(fp["entries"])
        fp["n_residual"] = sum(
            1 for e in fp["entries"] if e.get("identification") == "residual"
        )
        if SEEDED_SUFFIX not in fp["seeded"]:
            fp["seeded"] += SEEDED_SUFFIX
    if ADDENDUM not in d["governance"]["note"]:
        d["governance"]["note"] += ADDENDUM
    ATTESTATION.write_bytes(json.dumps(d, indent=2).encode("ascii"))
    print(
        f"[2] DOF ledger: added {added} entries -> "
        f"{fp['n_entries']} entries, {fp['n_residual']} residual"
    )
    print("[3] governance.note addendum present")


if __name__ == "__main__":
    do_registry()
    do_attestation()
