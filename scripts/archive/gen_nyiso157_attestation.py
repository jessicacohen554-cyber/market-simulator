"""Emit the nyiso-157 A/B arms' ``calibration_attestation.json`` (C6 governance gate).

nyiso-157 is the Leg-1 execution of the 2026-08-30 owner ruling
(`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md` §1): the
eastern-seam PAR attribution re-test under the STANDING preregs
(`PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md` + the two nyiso-127
addenda), K6 re-specified per
`EXECNOTE-nyiso157-leg1-execution-2026-08-30.md` §3, plus the iroquois
companion re-test on its recorded nyiso-150 re-open condition
(`PREREG-nyiso157-iroquois-companion-2026-08-30.md`). Three bundles:

* **Control** (``nyiso157_parctl_A``) — the committed keeper
  ``2026-08-25-nyiso-155-hydro-repair`` recipe replayed ZERO-DELTA at HEAD;
  ledger carried VERBATIM.
* **Seam arm** (``nyiso157_pararm_B``) — + ``nyiso_seam_par_attribution``:
  one DOF entry appended (published shares x published availability x
  published landings; ZERO scalars; ``n_residual`` UNCHANGED — the addendum-2
  §4 kill condition).
* **Companion arm** (``nyiso157_iroq_C``) — additionally
  ``nyiso_iroquois_winter_spread``: one further zero-scalar entry (three
  reconciled measured series).

THE GENERATOR IS THE SOURCE OF TRUTH: editing the emitted JSON by hand is
reverted by the next run of this script.

Usage:
    python scripts/gen_nyiso157_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results" / "calibration" / "nyiso155_hydro_repair"
CONTROL = REPO / "results" / "calibration" / "nyiso157_parctl_A"
ARM = REPO / "results" / "calibration" / "nyiso157_pararm_B"
COMPANION = REPO / "results" / "calibration" / "nyiso157_iroq_C"

PREREGS = (
    "results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md + "
    "PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md + "
    "PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md + "
    "EXECNOTE-nyiso157-leg1-execution-2026-08-30.md"
)

CONTROL_ATTESTED_BY = (
    "session nyiso-157 (2026-08-30). ZERO-DELTA CONTROL of the Leg-1 "
    f"eastern-seam A/B ({PREREGS}; EXECNOTE pushed and blob-verified BEFORE "
    "any solve): the committed keeper 2026-08-25-nyiso-155-hydro-repair "
    "recipe replayed unchanged at HEAD 5ce92f4 via scripts/replay_keeper.py. "
    "No lever, no parameter, no mechanism change — the ledger is the "
    "keeper's own, carried verbatim. K6 (re-specified) PASSES: C3a "
    "+6.81/-1.74/-10.82 vs the committed +6.8/-1.7/-10.8, and the control "
    "is BIT-IDENTICAL to the committed keeper in zonal prices in all three "
    "years (max |dprice| 0.0 — the nyiso-155 G1 reshuffle is absent at this "
    "HEAD)."
)

ARM_ATTESTED_BY = (
    "session nyiso-157 (2026-08-30). SEAM ARM of the Leg-1 A/B "
    f"({PREREGS}), against same-HEAD control 2026-08-30-nyiso-157-par-"
    "control: --set nyiso_seam_par_attribution=true, the nyiso-127 "
    "construction re-tested at the nyiso-155 HEAD under the 2026-08-30 "
    "owner ruling (the R adjudicated 2026-08-05 predates the nyiso-128/129 "
    "solar-basis repair that moved the exact K3 quantity; K3 does NOT "
    "re-fire — C1 14/14 free 10/10 on BOTH arms). ZERO free parameters: "
    "eight published percentages, eight published PTID identities (P-33 "
    "outSched), one published outage state, published tie landings, and the "
    "definitional NYISO_SEAM_FLOW_PERCENTILE — nothing swept, nothing "
    "chosen in a bracket. Supersedes nyiso_seam_deliverability_envelope at "
    "runtime (rule 19; exactly one of the two applies — the envelope's "
    "ledger entry describes a flag the attribution now shadows). Gates: "
    "every standing kill gate silent (_nyiso157_par_ab_gates.json; two "
    "scorer-instrument artifacts documented there: the K1 dual-channel echo "
    "and a K5 conservation leg penalizing the arm for landing CLOSER to "
    "the measured annual net than the control). REPORTED AT FULL "
    "MAGNITUDE: C3a-2023 +6.8 -> +1.0; C3a-2025 -10.8 -> -12.0 (P3 "
    "confirmed: the seam alone was never predicted to close 2025); "
    "C3b-2025 NRMSE 0.197 -> 0.203 crosses the 0.20 bar (a knife-edge "
    "PASS->FAIL); C3c bit-identical 1/0/0; the west->east cutset binds "
    "(Jan+Feb-2025 spread-hours 34 -> 435; NYC-UW winter gradient 0.24 -> "
    "4.60 vs measured 14.83)."
)

COMPANION_ATTESTED_BY = (
    "session nyiso-157 (2026-08-30). COMPANION ARM: --set "
    "nyiso_iroquois_winter_spread=true ON TOP OF the seam arm, under "
    "PREREG-nyiso157-iroquois-companion-2026-08-30.md (pushed and "
    "blob-verified before this solve) — the nyiso-150 R-cell re-opened on "
    "its own recorded condition ('re-test as the companion of a locational "
    "mechanism that lets the west->east cutset bind — never alone'), the "
    "condition established by this session's seam A/B. Gates: nyiso-150 §4 "
    "W-gates verbatim, control re-based to the seam arm "
    "(_nyiso157_iroq_gates.json). Zero fitted scalars (three reconciled "
    "measured series: SOM annual + AGT scarcity shape + Algonquin ceiling)."
)

SEAM_DOF_ENTRY = {
    "name": "nyiso_seam_par_attribution",
    "where": (
        "ScenarioConfig.nyiso_seam_par_attribution -> "
        "data.nyiso_par_attribution (PAR_REGISTRY, INTERFACE_ZONE, "
        "SEAM_ROW_ZONE, zone_shares, nyiso_par_attributed_ttc_hourly)"
    ),
    "identification": "published",
    "lineage_solves": (
        "nyiso-127 A/B (2026-08-05, REJECTED on K3 at the nyiso-125 HEAD; "
        "PRs #3570/#3582/#3584/#3586); nyiso-157 re-test A/B (2026-08-30, "
        "owner ruling of that date; K3 does not re-fire at the nyiso-155 "
        "HEAD)"
    ),
    "value": {
        "shares": {"ramapo": 0.32, "jk": 0.15, "abc": 0.21, "west": 0.32},
        "n_scalars": 0,
        "note": (
            "NY-NJ PAR posting table 1 (published percentages, effective "
            "5/1/2017; OBF 0 since 11/1/2019) x P-33 outSched published "
            "availability windows (ABC-B/C out 100 % of 2023-2025, so the "
            "hourly split is ~46/7/47, never the nameplate 47/21/32) x "
            "published tie landings (Gold Book / Operating Study). "
            "Regenerates forward from the standing JOA convention and "
            "forward PAR availability (rule 13). Supersedes the "
            "nyiso_seam_deliverability_envelope two-link mechanism at "
            "runtime (rule 19): exactly one of the two applies."
        ),
    },
}

IROQ_DOF_ENTRY = {
    "name": "nyiso_iroquois_winter_spread",
    "where": (
        "ScenarioConfig.nyiso_iroquois_winter_spread -> "
        "data.fuel.basis.nyiso.nyiso_reconciled_reference_monthly / "
        "nyiso_zonal_gas_ratios_monthly"
    ),
    "identification": "measured",
    "lineage_solves": (
        "nyiso-122 construction gates (annual conservation Delta=0.00000 "
        "x3); nyiso-150 standalone A/B (2026-08-22, REJECTED-AS-ARMED on "
        "the coupled block); nyiso-157 companion A/B (2026-08-30, on the "
        "recorded re-open condition)"
    ),
    "value": {
        "n_scalars": 0,
        "note": (
            "Reconciliation of three measured series — the SOM annual "
            "Iroquois-Transco spread (preserved exactly), the measured "
            "Algonquin monthly basis (the New England scarcity shape that "
            "physically causes the premium), and the Algonquin Citygate "
            "monthly ceiling — no fitted constant, nothing reads a model "
            "output; forward years regenerate from the forward basis "
            "seasonality (rule 13)."
        ),
    },
}


def _emit(bundle: Path, attested_by: str, extra_entries: list[dict]) -> None:
    """Write one bundle's attestation from the keeper's committed one."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    doc = json.loads(json.dumps(base))
    doc["governance"]["attested_by"] = attested_by
    # The keeper base's governance.note describes ITS promoted mechanism (the
    # nyiso-152 duty-role text, carried through 155) — stale for these bundles
    # (keeper-auditor flag, nyiso-157). Re-stamp it to this session's chain;
    # the note's mechanism story is superseded by attested_by's specifics.
    doc["governance"]["note"] = (
        "nyiso-157 chain (2026-08-30): the nyiso-155 keeper recipe, plus (arm "
        "bundles only) the eastern-seam PAR attribution and, on the companion, "
        "the iroquois winter spread — see attested_by for this bundle's exact "
        "role and evidence. The prior keeper lineage's mechanism notes "
        "(duty-role cohort, hydro repair) live in their own bundles' "
        "attestations and the keeper shard's promotion-note chain."
    )
    fp = doc["free_parameters"]
    names = [e.get("name") for e in fp["entries"]]
    for entry in extra_entries:
        if entry["name"] not in names:
            fp["entries"].append(entry)
    fp["n_entries"] = len(fp["entries"])
    # n_residual UNCHANGED: every appended entry carries zero scalars and a
    # published/measured identification (rule 21 [R-DOF]; the addendum-2 §4
    # kill condition is exactly that n_residual stays at 6).
    (bundle / "calibration_attestation.json").write_text(
        json.dumps(doc, indent=1) + "\n"
    )
    print(
        f"wrote {bundle / 'calibration_attestation.json'} "
        f"(n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


def main() -> None:
    """Write the three nyiso-157 bundles' attestations."""
    _emit(CONTROL, CONTROL_ATTESTED_BY, [])
    _emit(ARM, ARM_ATTESTED_BY, [SEAM_DOF_ENTRY])
    if (COMPANION / "meta.json").exists():
        _emit(COMPANION, COMPANION_ATTESTED_BY, [SEAM_DOF_ENTRY, IROQ_DOF_ENTRY])
    else:
        print(f"skip {COMPANION.name}: not solved yet")


if __name__ == "__main__":
    main()
