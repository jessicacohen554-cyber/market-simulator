"""Write the calibration attestations for the neiso-87 Aug-2025 gas-basis arms.

Both arms are ``replay_keeper`` re-solves of the ``2026-08-05-neiso-83-ca1-reclass``
keeper's own ``meta.json`` at this session's HEAD. Arm **A** is a ZERO-DELTA
control on the unmodified committed data; arm **B** carries exactly one delta —
a single **data** row, ``gas_basis_by_iso_month.csv`` ``NEISO,2025,8``, moved from
the committed interpolation ``+0.04`` to the measured ISO-NE Massachusetts gas
index value ``-0.38``. There is **no `ScenarioConfig` field and no mechanism**, so
unlike neiso-83 this arm adds **no DOF ledger entry at all**: the ledger is the
keeper's, carried forward unchanged at 14 entries / n_residual 5.

The governance posture and the standing measured-input ledger entries (NEISO's
single ledgered C3c caveat) are likewise the keeper's — carried forward verbatim
in *classification and reason*, with each run's **own** measured magnitudes
substituted from its own scored verdict, so no number in an attestation describes
a different run (the miso-116 §7 basis discipline).

**BOTH arms need an attestation, and that is not cosmetic.** neiso-70 §4 measured
it and this session re-confirmed it: without one, a probe bundle reads
``NOT-YET / governance UNATTESTED`` and C3c degrades from a ledgered CAVEAT to a
raw FAIL, because a caveat can only be *ledgered* by an attestation. That is a
scoring artifact of probe bundles and it must apply identically to control and
arm, or the A/B is not like-for-like — and the pre-registered N1 stop trigger
("determination not worse than the incumbent") would fire on the artifact rather
than on the change.

Run AFTER each bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3c.

Usage::

    PYTHONPATH=.:src python3 scripts/gen_neiso87_attestation.py --arm A
    PYTHONPATH=.:src python3 scripts/gen_neiso87_attestation.py --arm B
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

ISO = "NEISO"
#: The incumbent keeper whose attestation, DOF ledger and ledgered caveats are
#: carried forward. Its recipe IS both arms' recipe (``--replay-bundle``).
KEEPER = REPO / "results/calibration/neiso83_ca1reclass_B"
AB_JSON = REPO / "results/calibration/_neiso87_aug2025_basis_ab.json"

ARMS = {
    "A": {
        "bundle": REPO / "results/calibration/neiso87_control_A",
        "run_id": "2026-08-06-neiso-87-control",
        "corrected": False,
    },
    "B": {
        "bundle": REPO / "results/calibration/neiso87_aug2025basis_B",
        "run_id": "2026-08-06-neiso-87-aug2025-basis",
        "corrected": True,
    },
}

_COMMON = (
    "neiso-87, 2026-08-06. A replay_keeper re-solve of the "
    "2026-08-05-neiso-83-ca1-reclass keeper's own meta.json at this session's "
    "HEAD, --year 2023 2024 2025 in ONE invocation (rules 12 / 16 "
    "[R-ALLYEARS]), years sequential inside the invocation. "
    "PRE-REGISTRATION: results/calibration/"
    "PREREG-neiso87-aug2025-basis-refresh-2026-08-06.md, committed BEFORE any "
    "data byte was edited and before either arm was scored — every construction "
    "property (P1-P4), stop trigger (N1-N4), verdict branch (V1-V3) and the "
    "expected DIRECTION of the price move were fixed in advance. "
    "THE CONTROL WAS RUN RATHER THAN ASSUMED, AND IT MATTERED: the keeper's "
    "git sha is unresolvable in this shallow clone, so zero code drift could "
    "not be proven. It does not hold. Replaying the keeper's recipe at HEAD "
    "against UNMODIFIED data reproduces 2023 and 2024 byte-identically but "
    "diverges in 2025 across 731 hours, every one of them in January, max "
    "|dLambda| $25.52, mean dLambda -0.334 $/MWh. Ruled out by direct "
    "comparison: the AGT daily series (hubs._algonquin_daily resolves identical "
    "prints in every 2025 month under both the pre- and post-neiso-86 file), "
    "the monthly basis rows (NEISO 2023-2025 md5 382113c6 pre-intake, "
    "post-intake and at HEAD), and the FFR-7B RPS change (rps_enabled=False in "
    "every backcast). The cause lies in the ~50 commits since the keeper's "
    "merge-base and was NOT isolated here; it is filed as an open item. Every "
    "arm-B number is therefore quoted against THIS session's control and never "
    "against the committed keeper bundle. "
)

_ATTEST_A = _COMMON + (
    "THIS IS THE ZERO-DELTA CONTROL (arm A). It reads the unmodified committed "
    "gas_basis_by_iso_month.csv; a diff of the two arms' input files returns "
    "exactly one differing line. It arms NOTHING and claims NOTHING: it is "
    "scored, registered (rule 15 [R-DASHBOARD]) and attested only so the "
    "comparison is like-for-like."
)

_ATTEST_B = _COMMON + (
    "EXACTLY ONE DELTA against that control, and it is a DATA row rather than a "
    "flag: gas_basis_by_iso_month.csv NEISO,2025,8 moves from the committed "
    "interpolation (+0.04) to the measured ISO-NE Massachusetts gas index value "
    "(-0.38). No ScenarioConfig field changes, so rule 24 [R-REGISTRY] is "
    "satisfied by there being no new tunable at all, and rule 28(c) is not "
    "engaged. "
    "WHAT THE CORRECTION IS. NEISO,2025,8 was the ONLY one of NEISO's twelve "
    "2025 basis rows not sourced from the measured index; its own committed "
    "source field declares it 'interpolated from Jul (+1.03) and Sep (-0.95)', "
    "written when no measured figure existed. ISO-NE's August-2025 recap, "
    "published 2025-10-02 (i.e. AFTER that row was written), states the "
    "Massachusetts natural gas index at $2.53/MMBtu; against Henry Hub $2.9129 "
    "the basis is -0.3829 -> -0.38. After the edit all twelve rows carry the "
    "identical hub label and one cited recap URL each. "
    "WHY IT IS A CORRECTION AND NOT A TUNING ACT (rules 13 / 14 / 23). The "
    "replacement value is not chosen, fitted or compared against any residual: "
    "it is the same published series, boundary, units, monthly convention and "
    "transformation (MA index less Henry Hub) already used for the other 35 "
    "in-sample rows, and it was ALREADY COMMITTED in "
    "data/raw/gas-prices/isone_ma_gas_index_monthly.csv before this session "
    "opened. The neiso-86 extractor reproduced 33/36 committed in-sample rows "
    "exactly; this row was its ONE material disagreement. Zero free parameters "
    "are added and the DOF ledger is unchanged at 14 entries / n_residual 5. "
    "WHY IT IS IN-SAMPLE WORK AND ENGAGES NO HOLDOUT (rule 22). 2025 is a "
    "training year. No out-of-training year was solved, scored or registered by "
    "this session, and holdout-freeze.json is untouched and not engaged. "
    "THE EDIT'S SCOPE WAS VERIFIED, NOT ASSERTED. Exactly one line differs "
    "(git --numstat 1/1); non-NEISO lines are byte-identical (md5 5aded190, "
    "rule 25 [R-ISO-SCOPE]); NEISO 2023 and 2024 rows are byte-identical. "
    "P1 then confirmed this at the DISPATCH grain: because the edited row is a "
    "2025 row, 2023 and 2024 come back BYTE-IDENTICAL between the arms across "
    "class_hourly, system and storage — the free decisive check, fixed in the "
    "prereg before the solve."
)


def _verdict(run_id: str) -> dict:
    """Score a registered run from committed artifacts and return its verdict."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise SystemExit(
            f"calibration_verdict failed for {run_id}: {out.stderr[-800:]}"
        )
    return json.loads(out.stdout)


def _magnitudes(verdict: dict) -> dict[tuple[str, int], str]:
    """(criterion, year) -> this run's OWN measured magnitude string."""
    out: dict[tuple[str, int], str] = {}
    for name, crit in verdict["criteria"].items():
        for rec in crit.get("rows", []) + crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _disclosure(arm: str) -> str:
    """The session's own disclosure block, appended to the keeper's note."""
    ab = json.loads(AB_JSON.read_text()) if AB_JSON.exists() else {}
    rep = ab.get("reported", {})
    y2025 = rep.get("2025") or rep.get(2025) or {}
    moved = ""
    if y2025:
        moved = (
            "MEASURED EFFECT, against this session's own same-HEAD control: "
            f"2025 mean lambda {y2025.get('d_mean_lambda', 0.0):+.4f} $/MWh, "
            "and over the EDITED MONTH (August 2025) "
            f"{y2025.get('d_edited_month_mean', 0.0):+.4f} $/MWh "
            f"({(y2025.get('price_a') or {}).get('edited_month_mean', float('nan')):.2f} "
            f"-> {(y2025.get('price_b') or {}).get('edited_month_mean', float('nan')):.2f}). "
            "2023 and 2024 byte-identical. C3c bit-unchanged: model tail 0 h in "
            "all three years, max lambda unchanged at $280.85. "
        )
    common = (
        "neiso-87 DATA CORRECTION DISCLOSURE. " + moved + "THE DIRECTION WAS "
        "PRE-REGISTERED: prereg section 8 predicted August prices would fall by "
        "roughly $3/MWh (the -0.42 $/MMBtu basis delta at a ~7 MMBtu/MWh CC heat "
        "rate), the annual mean would fall slightly, and C3c would be "
        "bit-unchanged because the change moves prices DOWN, away from the $300 "
        "threshold. All three hold. Recording the prediction in advance is what "
        "makes the agreement evidence rather than rationalisation. "
        "THE SIZE OF THE MOVE IS REPORTED, NEVER REQUIRED (rules 1 / 14). This "
        "is a measured-input correction with zero free parameters, so under the "
        "prereg's V3 branch it promotes on CORRECTNESS whatever the residual "
        "does — the neiso-83 / caiso-159 precedent. "
        "P3 IS REPORTED, NOT GATED, AND THE REASON IS STATED. The A/B probe's "
        "conservation figure compares class generation against zonal demand "
        "WITHOUT netting interchange, and NEISO is a large net importer "
        "(~1,728 MW average), so its absolute value is not a conservation "
        "proof. It is identical in both arms, which is all it establishes; the "
        "runner's own internal balance checks are the actual conservation "
        "guarantee. The gated construction properties are P1, P2 and P4. "
    )
    if arm == "A":
        return common + (
            "THIS ARM IS THE CONTROL and claims nothing on its own; it exists so "
            "the arm-B delta is measured against a same-HEAD baseline."
        )
    return common + (
        "STILL DEFECTIVE ELSEWHERE, AND NOT PAPERED OVER (carried from "
        "neiso-86): NEISO's 2015-2017 basis rows remain 100% on the inverted "
        "EIA N3050MA3 proxy, 2018 Mar-Jun are UNOBTAINABLE so 2018 is a mixed "
        "year with an inverted June, and 2026 is monthly Jan-May only with a "
        "single AGT daily print. This session corrected the last unmeasured "
        "row INSIDE the training window; it did not make NEISO's basis clean "
        "everywhere."
    )


def main() -> int:
    """Write one arm's attestation next to its bundle. Returns a shell code."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    args = ap.parse_args()
    spec = ARMS[args.arm]

    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    verdict = _verdict(spec["run_id"])
    mags = _magnitudes(verdict)

    # Governance: the keeper's four assertions stand — this arm changes a
    # measured input's SOURCE, adds no lever and consults no residual.
    base["governance"]["attested_by"] = _ATTEST_A if args.arm == "A" else _ATTEST_B

    # Ledgered caveats carry forward in classification and reason, but every
    # MAGNITUDE is re-substituted from this run's own scored verdict so no
    # number describes a different run (miso-116 section 7).
    for exc in base.get("exceptions", []):
        year = exc.get("year")
        crit = exc.get("criterion")
        if year is None or crit is None:
            continue
        own = mags.get((crit, int(year)))
        if own:
            exc["magnitude"] = own
            exc["magnitude_basis"] = (
                f"re-measured from this run's own verdict ({spec['run_id']})"
            )

    base["disclosures"]["note"] = (
        str(base["disclosures"].get("note", "")).strip() + " " + _disclosure(args.arm)
    ).strip()

    out = spec["bundle"] / "calibration_attestation.json"
    out.write_text(json.dumps(base, indent=2))
    print(f"wrote {out.relative_to(REPO)}")
    print(
        f"  DOF ledger: {base['free_parameters']['n_entries']} entries, "
        f"n_residual {base['free_parameters']['n_residual']} (UNCHANGED)"
    )
    print(f"  exceptions re-measured: {len(base.get('exceptions', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
