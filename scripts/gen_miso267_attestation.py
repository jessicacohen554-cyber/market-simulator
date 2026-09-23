"""Write the miso-267 bundle's attestation — the dispatched-bin derate denominator.

The composite needs a C6 attestation: ``replay_keeper --out-dir`` does not carry
``calibration_attestation.json``, and an unattested C6 makes C3c FAIL outright
instead of reclassifying to its ledgered CAVEAT under the rule-22 ``[R-C3C]``
standing rule's guard (b). So this is generated AT the registration and never
typed by hand.

Pattern of ``gen_miso264_attestation.py``: the incumbent keeper's own committed
attestation (``hydro5_miso_ror_span``) is carried, ``governance.attested_by`` is
re-stamped with this run's narrative, and every ``price_tail`` / ``price_mean``
exception magnitude is RE-MEASURED from this run's own scored records.

RULE 21 ``[R-DOF]``: the ledger is carried VERBATIM with NO new entry, and is
deliberately NOT rebuilt by ``scripts/build_dof_ledger.py``, which drops the
hand-declared MISO entries. ``unit_outage_dispatched_bin_denominator`` is a
registered boolean (miso-266) that replaces one reconstructed capacity with the
capacity the LP already holds; it adds no free parameter. The rule-1 authorized
price-tuning channel is asserted untouched: ``offer_curve_by_group`` must be
byte-identical to the keeper's or this refuses to write.

Usage::

    PYTHONPATH=.:src python scripts/gen_miso267_attestation.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CAL = REPO / "results" / "calibration"
BUNDLE = CAL / "miso267_dbd_span"
KEEPER = CAL / "hydro5_miso_ror_span"
RUN_ID = "2026-09-23-miso-267-dispatched-bin"
KEEPER_ID = "2026-09-22-hydro-5-miso-ror"
FLAG = "unit_outage_dispatched_bin_denominator"
PRECOMMIT = "docs/PRECOMMIT-miso267-dispatched-bin-on-hydro5-2026-09-23.md"
RESULT = "docs/RESULT-miso267-dispatched-bin-on-hydro5-2026-09-23.md"
FINDING = "docs/FINDING-miso267-the-oil-reattribution-was-one-sided-2026-09-23.md"
PINNED = "3ea64fa5110254df85b7a40cb6d4521414d08242"

ATTESTED_BY = (
    f"miso-267 (2026-09-23) -- keeper {KEEPER_ID}'s recipe replayed UNCHANGED via "
    "scripts/replay_keeper.py, ONE YEAR PER SHARD (rule 36), with exactly one "
    f"registered ScenarioConfig flag added: {FLAG}=true. Every leg was verified "
    "keeper-recipe-plus-one-flag (per-year overlay included) and hydro-classifier "
    "identical by scripts/probes/_miso267_shard_check.py, its resolved_inputs and "
    "static shared-input captures byte-identical to the keeper's, and the six legs "
    "re-checked by scripts/probes/_miso266_compose_span.py (12 must-agree fields, "
    "one solve-surface fingerprint) before composition. Zero LP in the parent. "
    f"Pre-registered in {PRECOMMIT} (pinned {PINNED[:8]}) before any shard "
    f"launched; record {RESULT}. NOT promoted: the promotion is the owner's (rule 31)."
)

DISCLOSURES = (
    "(a) THE BENCH IS THE REGENERATED ONE, AND THIS REGISTRATION MOVED NOTHING. "
    f"miso-267 STEP 1 regenerated MISO's bench parts ONCE through a repaired builder "
    f"({FINDING}); the keeper was re-scored on them with 0 status flips. This run and "
    "the keeper are scored on the SAME parts, and registering this run left all 44 "
    "committed bench parts sha256-identical. The keeper attestation's former note (a) "
    "- that the bench moves at HEAD - is superseded by that regeneration.\n"
    "(b) THE PRE-REGISTERED ADVERSE MOVES HAPPENED. C1 2022 COAL_PRB +7.67 -> +10.04 "
    "and C1 2022 CC_REGULAR -7.69 -> -8.99 TWh both cross the 8 TWh band, and C3a 2022 "
    "-9.5 % -> -10.2 % crosses 10 %; C1 2020 COAL_BIT -10.76 -> -6.79 leaves the fail "
    "set. The failing criterion SET is unchanged; the failing cells move from 2020 to "
    "2022. Reported at full magnitude; not a reason to narrow the mechanism.\n"
    "(c) WHAT THIS DOES NOT FIX: the C3a price body (a flat +$6-8/MWh across RT "
    "deciles 0-7, carried by CALIBRATED 2023 too), the coal fleet's trough surplus "
    "(commitment side), 84.5 % of the availability-ceiling contradiction "
    "(PRECOMMIT-miso266 section 3.3) and C3b 2021. All routed, none absorbed.\n"
    "(d) INHERITED FROM THE KEEPER, UNCHANGED: the D-2 CT_PEAKER forced share is over "
    "its 15 % cap in every year on both runs and C8 reaches its verdict through rule "
    "18's grounded route; the frozen gas-offer anchor's 2.7 % in-window gap stays "
    "routed (RESULT-miso264 section 9)."
)


def _offer_sha(bundle: Path) -> str:
    cfg = json.loads((bundle / "run_config.json").read_text())["scenario_config"]
    blob = json.dumps(cfg.get("offer_curve_by_group") or {}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _scored_criteria() -> dict:
    # calibration_verdict exits 1 on NOT-YET, which is this bundle's state before
    # its attestation exists; the JSON on stdout is complete either way.
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            RUN_ID,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
        check=False,
    )
    if not proc.stdout.strip():
        raise SystemExit(
            f"calibration_verdict produced no JSON:\n{proc.stderr[-2000:]}"
        )
    return json.loads(proc.stdout)["criteria"]


def main() -> int:
    """Write the attestation; refuse if the price-tuning channel moved."""
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    sha, ksha = _offer_sha(BUNDLE), _offer_sha(KEEPER)
    if sha != ksha:
        raise SystemExit(f"offer_curve_by_group {sha} != keeper {ksha}")
    years = sorted(
        int(p.stem.rsplit("_", 1)[1]) for p in BUNDLE.glob("run_config_*.json")
    )
    for y in years:
        sc = json.loads((BUNDLE / f"run_config_{y}.json").read_text())[
            "scenario_config"
        ]
        if sc.get(FLAG) is not True:
            raise SystemExit(f"{y}: {FLAG} is not armed")

    scored = _scored_criteria()
    measured: dict[tuple[str, int], str] = {}
    for crit in ("price_tail", "price_mean"):
        for rec in scored.get(crit, {}).get("records", []):
            if rec.get("key") or rec.get("year") is None:
                continue
            measured[(crit, int(rec["year"]))] = rec["magnitude"]
    n_remeasured = 0
    for exc in att["exceptions"]:
        key = (str(exc.get("criterion")), int(exc.get("year", 0)))
        if key in measured:
            exc["magnitude"] = measured[key]
            exc["magnitude_basis"] = (
                "this run's own scored value (miso-267); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
            n_remeasured += 1

    fp = att["free_parameters"]
    fp["carried_from"] = (
        f"{KEEPER.relative_to(REPO)}/calibration_attestation.json -- carried VERBATIM "
        f"with no new entry: miso-267 adds no ScenarioConfig field and no free "
        f"parameter. {FLAG} replaces a year-independent reconstruction of a bin's "
        "capacity with the capacity the LP already dispatches (rules 21 [R-DOF] / "
        "24 [R-REGISTRY])."
    )
    gov = att["governance"]
    gov["attested_by_inherited"] = gov.get("attested_by")
    gov["attested_by"] = ATTESTED_BY
    apt = gov.get("authorized_price_tuning")
    if isinstance(apt, dict):
        apt["years_held"] = years
        apt["years_held_basis"] = (
            f"miso-267 (2026-09-23): this run's own solved years {years}. "
            f"offer_curve_by_group SHA-256 {sha} is byte-identical to keeper "
            f"{KEEPER_ID}'s; this lane passed only --set {FLAG}=true. No band, class "
            "or value moved and nothing was swept (rule 1 condition (c))."
        )
    gov["mechanism_armed_inherited"] = gov.get("mechanism_armed")
    gov["mechanism_armed"] = {
        "field": FLAG,
        "value": True,
        "level": (
            "NO LEVEL PARAMETER. The derate denominator becomes the LP fleet's own "
            "per-bin pmax, summed off the generators the overlay is applied to; the "
            "CHP bins keep their incumbent denominator (miso-266 section 2.1)"
        ),
        "free_parameters_added": 0,
        "basis": (
            "rule 14 [R-ACCURATE] / rule 1 [R-STRUCT]: _iso_plant_capacity returned "
            "50,365.4 MW of MISO coal in every year 2020-2025 while the LP's own coal "
            "fell 54,238.1 -> 53,391.6 MW; at the contradicted plants denom/cap_LP was "
            "0.414-0.695, so one unit's outage removed up to 2.4x its share"
        ),
        "one_mechanism": (
            "rule 19 [R-ONE-MECH]: replaces the denominator of the existing outage "
            "derate; mutually exclusive with unit_outage_lp_capacity_basis and "
            "unit_outage_extract_basis_share (both refused, not stacked)"
        ),
        "window": "every hour a measured outage event covers (the derate's own window)",
        "control": (
            f"the committed keeper {KEEPER.relative_to(REPO)} (rule 29(b) form 4); "
            f"G-DRIFT {PRECOMMIT} section 3 classified every solve-path hunk INERT"
        ),
        "prereg": f"{PRECOMMIT}, pushed at {PINNED} BEFORE any shard was launched",
    }
    att["disclosures"] = {"note": DISCLOSURES}
    att["miso267"] = {
        "result": RESULT,
        "finding_step1": FINDING,
        "legs": {
            "2020": "b14d04407995df14db17ea63a6ac2e2eed81747c",
            "2021": "856c2a0828d6632088178c593273e926bbd922d9",
            "2022": "f70fac80af0dd06789cc6e1318051b2ecc23ccd9",
            "2023": "2aa8a9c50da3a6de9a98b73b77336387cd8f24b8",
            "2024": "80036e25f34b201af9dc6d1a6934c376ab088470",
            "2025": "034dadb290009aa0ebf14629eb1d903c480bc1a5",
        },
    }
    out = BUNDLE / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(REPO)} years={years}")
    print(
        f"  exceptions carried: {len(att['exceptions'])}, re-measured: {n_remeasured}"
    )
    print(
        f"  DOF ledger entries carried: {fp['n_entries']} "
        f"({fp['n_residual']} residual-identified), 0 added"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
