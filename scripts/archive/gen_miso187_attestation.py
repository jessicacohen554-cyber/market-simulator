"""Generate miso187_nuc_B's calibration attestation from the keeper's.

The arm is the miso-186 keeper recipe plus exactly one zero-residual-DOF
mechanism (the gen_miso186 attestation pattern): its attestation is the
keeper's with one MEASURED-identified ledger entry for the per-reactor
NRC-daily nuclear availability overlay (a published physical measurement
reconciled to the committed EIA-923 anchor, zero fitted scalars, zero
lineage solves), a rewritten ``governance.attested_by`` for the miso-187
A/B, and this session's disclosures appended AT FULL MAGNITUDE (the S-2
non-move included). ``n_residual`` is UNCHANGED. Exceptions carry unchanged.
"""

import json

SRC = "results/calibration/miso186_dir_B/calibration_attestation.json"
DST = "results/calibration/miso187_nuc_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "nuclear_unit_availability (boolean arm)",
        "where": (
            "ScenarioConfig.nuclear_unit_availability -> "
            "data/fleet/arrays.py::_nuclear_monthly -> "
            "data.outages.nuclear_unit_availability_series over "
            "data/raw/nuclear-availability-MISO.csv (derived by "
            "scripts/data/derive_nuclear_availability.py --iso MISO from the "
            "NRC daily Power Reactor Status reports, reconciled per-month to "
            "the committed EIA-923 anchor NUCLEAR_MONTHLY_CF_BY_YEAR['MISO'] "
            "with the sister-ISO deriver's frozen scalars: EVENT_RAW_MAX "
            "0.90, SCALE_CLIP 1.25, WEDGE_TOL 0.01 — rule 23, never re-tuned)"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0 (the candidate was named and its admissibility adjudicated by "
            "miso-186's pre-registered formation-input decomposition BEFORE "
            "any LP was spent on it — PREREG-miso186 §4 clauses (i)-(v) all "
            "cleared, static reach +0.299 GW 2025-scarce South / -0.075 GW "
            "Midwest, both direction-correct; left unarmed there only by the "
            "single-delta selection rule. No LMP, no residual, no tuned "
            "scalar anywhere in the path)"
        ),
        "value": (
            "True (the overlay carries no numeric parameter of its own; the "
            "13-reactor NRC_TO_EIA['MISO'] crosswalk is an identifier "
            "mapping. Replaces the uniform fleet-month smear — 0.897 "
            "capacity-weighted in the 2025 scarce set — with the measured "
            "per-reactor daily record: South 5-reactor fleet 0.954, Midwest "
            "0.885 (Callaway 68.9%, Clinton 77.2%, Monticello 86.8%). "
            "Monthly fleet energy is anchor-preserved in reconciled months; "
            "14 winter/shoulder months hit the thermal-vs-net wedge and keep "
            "the smear, per the deriver's documented fallback)"
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: nuclear_unit_availability=true. "
    "miso-187, 2026-08-25/26. PREREG "
    "results/calibration/PREREG-miso187-measured-nuclear-availability-"
    "2026-08-25.md was committed and pushed (db0f1d9) BEFORE any "
    "adjudicating quantity was computed; the candidate was named by "
    "miso-186's pre-registered decomposition and cleared all five "
    "admissibility clauses there. Both legs are replay_keeper re-solves of "
    "the 2026-08-25-miso-186-statusscope keeper's own recipe, --year 2023 "
    "2024 2025 in ONE invocation each, years sequential (rules 12/16); the "
    "arm's single delta rode the sanctioned replay_keeper --set channel. "
    "CONTROL VALUE-IDENTITY (S-0): 2026-08-25-miso-187-control reproduces "
    "the committed keeper with numeric max|diff|=0 on every scored sidecar "
    "of every year. STRUCTURAL GATES SPLIT: S-3 PASS (South boundary-complex "
    "net inflow +0.682 -> +0.385 GW scarce, +0.298 GW toward the measured "
    "-2.441 - matching the +0.299 GW ex-ante static reach almost exactly; "
    "balance-verified < 1 MW) but S-2 FAIL (2025 scarce N->S RDT binding "
    "7/47 -> 7/47, composition unchanged - the remaining binding hours are "
    "the adjudicated mc-idled/flat-stack model-class object, miso-186 §6). "
    "S-1 exactness PASS (Callaway 2025 scarce dispatch 1068 -> 615 MW, the "
    "South 5-reactor aggregate 4718 -> 5114 MW - both exactly as the NRC "
    "record predicted); S-4 PASS (zero D-4 conduct failures, zero new; C8 "
    "PASS); the charter kill SILENT (C3a-2025 did not improve). SCORED FACE "
    "AT FULL MAGNITUDE (S-5): C3a-2025 -12.3185% -> -12.3185% (UNCHANGED to "
    "4 dp), C3a-2024 -4.6749% -> -4.6440%, C3a-2023 +1.2177% -> +2.4049% "
    "(the sole regression, inside the +-10% band); ZERO criterion-status "
    "flips (C1 fuelmix CC_REGULAR 2024 stays FAIL and improves +8.089 -> "
    "+8.037 TWh vs the +-8.00 band); the S-5 escalation condition itself "
    "did not fire. PROMOTED under the owner's in-session directive "
    "(2026-08-25, verbatim: 'Is this a recommended keeper candidate? If so "
    "plz promote. If structural integrity improves but gates regress that "
    "may still be a keeper.') resolving the PREREG-miso187 §4 structural-"
    "split escalation, and rules 1/14: the control keeps a uniform "
    "fleet-month smear where an admissible measured per-reactor record "
    "exists (MISO was the ONLY multi-reactor ISO without the overlay all "
    "four sister ISOs carry), so the structurally faithful run is the arm. "
    "LOYO within 2023-2025: the mechanism carries ZERO fitted parameters "
    "and its identification (the NRC daily record reconciled to the EIA-923 "
    "anchor) is year-independent, so no year's parameter was identified "
    "against any year's outcome; per-year effects reported at full "
    "magnitude above. n_residual UNCHANGED. Rule 22: no year outside "
    "2023-2025 was solved, scored or registered; MISO holds neither marker "
    "and the holdout spend freeze is untouched."
)

d["disclosures"]["miso187_ab"] = (
    "A/B verdict record: results/calibration/_miso187_ab_gates.json "
    "(S-0..S-5 + the charter kill, which does NOT fire: C3a-2025 is "
    "unchanged while S-3 passes). Disclosures against interest: (1) the "
    "PREREG's charter framing repeated miso-186 §3's sub-claim that MISO "
    "had no NUCLEAR_MONTHLY_CF_BY_YEAR entry - FALSE at HEAD: the anchor "
    "exists (constants.py, with citation) and IS the active smear (scarce-"
    "set mean 0.8972 = the committed 0.897); the structural claim (uniform "
    "across reactors, no per-reactor layer) was correct and is what the arm "
    "repairs. Charter step 1 was therefore executed as a --check "
    "verification, which passed exactly. (2) The arm leg was killed once "
    "mid-solve on a misread log line - the assembly-stage arrays build "
    "logs '0 reactor(s)' because its generators list carries non-matching "
    "cache ids; the LP's own dispatch-fleet build applied 13/13 reactors "
    "in every year. The partial out-dir was deleted unread and the leg "
    "relaunched clean; S-0 control identity proves the assembly-stage "
    "build is output-inert. (3) The arm's run id carries date 2026-08-26 "
    "(the relaunched solve crossed midnight UTC), deviating from the "
    "PREREG's declared 2026-08-25-miso-187-nucavail - the id date is "
    "derived from the bundle timestamp, not chosen. (4) 14 winter/shoulder "
    "months 2023-2025 hit the deriver's thermal-vs-net wedge fallback and "
    "keep the smear (every Jun-Sep scarce-season month reconciles); the "
    "overlay's reach is therefore concentrated exactly where the charter "
    "aimed it. (5) S-2's non-move at unchanged composition 7/0/40 is the "
    "honest remainder: after this repair the direction object's formation "
    "is the adjudicated ~3.3 GW mc-idled/flat-stack model-class residual."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    f"wrote {DST} (n_entries={d['free_parameters']['n_entries']}, "
    f"n_residual={d['free_parameters']['n_residual']})"
)
