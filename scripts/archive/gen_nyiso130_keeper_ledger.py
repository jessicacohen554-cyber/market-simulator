"""Add the owner-authorized C3c-2023 exception to the NYISO keeper's ledger.

The designated keeper is unchanged — ``2026-08-06-nyiso-128-solar-basis``
(bundle ``results/calibration/nyiso128_treatment``). nyiso-130's A/B on the
published Zone-K transfer limit was **rejected as armed** (its own pre-registered
kill gate K6 fired), so the incumbent stays. Nothing in the keeper's *results*
is touched by this script: it writes one entry into the ledger, which is the
artifact owner-authorized caveats live in.

**What this resolves.** nyiso-129 WITHHELD the C3c-2023 exception rather than
laundering it: the inherited caveat's own classification reads "five-zone
representation *cannot form* the sub-zonal scarcity", an UNDER-production, while
2023 fails in the OPPOSITE direction (22 h against a measured 10 h, 2.20x
OVER-produced). The exception was missing an authorization, not a justification.

**The authorization, given in session nyiso-130, 2026-08-06, verbatim:**

    "After this run if the only outstanding issue is c3c scarcity tail of +12
    hours in 2023 I want NYISO registered as calibrated with caveats. C3c is an
    acceptable gate failure as a ledgered caveat."

The condition is met exactly as stated: on this keeper C3c is the SOLE failing
criterion (C1/C2/C3a/C3b/C4/C6/C8 all PASS at HEAD under rubric v3.1) and the
2023 miss is +12 hours (22 vs 10). This supplies the IN-TRAINING authorization
CLAUDE.md rule 22's C3c standing rule does not reach — that rule is
out-of-training only.

**Two disciplines are kept, not waived.** (1) The 2023 entry carries its OWN
correctly-signed classification naming the over-production; it does NOT ride
under the 2024 under-production caveat, and the withheld block is preserved as
``_withheld_exception_history`` so the record shows the exception was authorized
rather than quietly widened. (2) The magnitude is recorded at full size.

Run: ``python scripts/gen_nyiso130_keeper_ledger.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/nyiso128_treatment"
ATTESTATION = KEEPER / "calibration_attestation.json"

OWNER_DIRECTIVE_VERBATIM = (
    "After this run if the only outstanding issue is c3c scarcity tail of +12 "
    "hours in 2023 I want NYISO registered as calibrated with caveats. C3c is "
    "an acceptable gate failure as a ledgered caveat."
)

ENTRY_2023 = {
    "criterion": "price_tail",
    "year": 2023,
    "metric": (
        "hours RT-expressible LMP > $300/MWh (C3c scarcity tail, actual RT hourly gate)"
    ),
    "magnitude": (
        "model 22 h > $300/MWh against RT actual 10 h (2.20x, +12 h; gate band "
        "[5, 20] h). Recorded at FULL magnitude and NOT softened. This is an "
        "OVER-production — the opposite sign to the 2024 entry."
    ),
    "classification": (
        "MODEL MISS (structural, OVER-production) — ACCEPTED MODEL-CLASS "
        "LIMITATION under the owner directive below. The 2023 miss is NOT the "
        "miss the 2024 caveat licenses and does not ride under it: that entry's "
        "classification reads 'five-zone representation CANNOT FORM the "
        "sub-zonal NYC/LI load-pocket scarcity', an UNDER-production. "
        "nyiso-130 IDENTIFIED the over-production's owner and it is now a "
        "diagnosed defect rather than an unexplained residual: 100 % of the "
        "model's C3c tail hours in ALL THREE years are Long Island, inside the "
        "HB14-21 window, with BOTH Zone-K import paths at their bound — so the "
        "whole modelled tail is formed at the in-window cap on "
        "NYC>Long_Island, and its COUNT is set by how tightly Zone K is bounded "
        "rather than by a sub-zonal pocket the five-zone model lacks."
    ),
    "reason": (
        'OWNER DIRECTIVE, session nyiso-130, 2026-08-06, verbatim: "'
        + OWNER_DIRECTIVE_VERBATIM
        + "\" The directive's own condition is met exactly as stated: C3c is "
        "the SOLE failing criterion on this keeper (C1/C2/C3a/C3b/C4/C6/C8 all "
        "PASS at HEAD under rubric v3.1, C3a +8.8 / +0.8 / -3.2 %) and the 2023 "
        "miss is +12 hours. This supplies the IN-TRAINING authorization rule "
        "22's C3c standing rule does not reach (that rule is out-of-training "
        "only), and it resolves the exception nyiso-129 deliberately withheld — "
        "an authorization was what that entry lacked, not a justification. "
        "THE LANE IS NOT EXHAUSTED AND THIS IS NOT A CLOSURE: nyiso-130 both "
        "identified the object AND tested the obvious fix, which FAILED its own "
        "pre-registered kill gate. NYISO publishes, in TABLE 1 note 2 of the "
        "Locality Bulk Power Transmission Capability Reports (identical in the "
        "2024-25, 2025-26 and 2026-27 editions), that the Zone-K 'Locality "
        "Limit' the cap uses is the transfer limit NET of a 660 MW generation "
        "loss-of-source: 'The true N-1-1 Transmission Security Limit is 940 in "
        "this scenario, the Bulk Transfer Limit accounts for the loss-of-source "
        "of 660 MW'. Arming the published 940 MW (nyiso-130 A/B, run "
        "2026-08-06-nyiso-130-n11-tsl) collapses the tail to 2 / 0 / 5 h "
        "against 10 / 12 / 42 — C3c then fails all three years UNDER-produced, "
        "2024 forming ZERO scarcity hours — and fires kill gate K6: the "
        "downstate ST_GAS reliability floor takes up the slack, forcing "
        "+0.22 / +0.42 / +0.23 TWh more (share 20.4->22.2 / 22.0->26.0 / "
        "15.4->17.0 %). So Zone-K reliability in this model is carried by TWO "
        "proxies — a too-tight transfer bound and a min_gen floor — and "
        "relieving one loads the other. The successor is a JOINT reconciliation "
        "of both under rule 19 [R-ONE-MECH], not a bare number swap; it needs "
        "its own charter and pre-registration. Evidence: "
        "results/calibration/FINDING-nyiso130-li-transfer-security-limit-"
        "2026-08-06.md, PREREG-nyiso130-li-transfer-security-limit-2026-08-06"
        ".md, _nyiso130_li_tsl_identification.json, _nyiso130_ab_gates.json."
    ),
}


# The rule-20 [R-DOF] provenance defect nyiso-127 §1.4 found and flagged but did
# not edit: a ledger entry whose cited symbol does not exist at HEAD. The owner
# authorized the removal in session nyiso-130, choosing "fix it now in the
# generator" over bundling it with the frontier disposition.
PHANTOM_ENTRY = "GAS_AVAILABILITY_FACTOR[NYISO]"
PHANTOM_SYMBOL = "GAS_AVAILABILITY_FACTOR"


def _symbol_is_absent(symbol: str) -> bool:
    """True when *symbol* appears nowhere under ``src/market_sim/``.

    Checked at runtime rather than asserted, so the removal below can never
    delete a ledger entry that has since been wired in — if someone implements
    the R2 disposition of issue #1349, this returns False and the entry stays.
    """
    for path in (REPO / "src" / "market_sim").rglob("*.py"):
        if symbol in path.read_text(encoding="utf-8", errors="ignore"):
            return False
    return True


def _drop_phantom_entry(obj: dict) -> dict | None:
    """Remove the phantom DOF entry, or return ``None`` if there is nothing to do.

    Rule 26 ``[R-DELETE]``: a dead entry is REMOVED, not zeroed. The entry's own
    ``note`` already recorded it as orphaned ("not read anywhere in
    src/market_sim ... either wire it in ... or delete it as dead code",
    issue #1349); this takes the delete branch.

    ``n_residual`` is deliberately UNCHANGED: the entry's ``identification`` is
    ``"published"`` (NERC GADS Brochure 3), so it never counted toward the
    residual-identified total. The correction is an OVER-count being removed — a
    listed parameter that cannot bind a solve, never an unlisted one that can.
    """
    fp = obj["free_parameters"]
    keep = [e for e in fp["entries"] if e.get("name") != PHANTOM_ENTRY]
    if len(keep) == len(fp["entries"]):
        return None
    if not _symbol_is_absent(PHANTOM_SYMBOL):
        print(f"{PHANTOM_SYMBOL} now resolves under src/market_sim — entry KEPT")
        return None
    dropped = next(e for e in fp["entries"] if e.get("name") == PHANTOM_ENTRY)
    n_prev, n_res = int(fp["n_entries"]), int(fp["n_residual"])
    fp["entries"] = keep
    fp["n_entries"] = n_prev - 1
    obj.setdefault("_ledger_corrections", []).append(
        {
            "date": "2026-08-06",
            "session": "nyiso-130",
            "correction": (
                f"REMOVED the ledger entry {PHANTOM_ENTRY}: a rule 20 [R-DOF] "
                "provenance defect found by nyiso-127 §1.4 and flagged rather "
                f"than edited. Its `where` cites 'constants.py {PHANTOM_SYMBOL}' "
                "but the symbol exists NOWHERE in src/market_sim/ (verified at "
                "generation time by this script, not asserted); its only other "
                "occurrence in the repo is market-sim-build-plan.md, the "
                "PRE-EXTRACTION manifest of the legacy lmp_engine.py — i.e. a "
                "symbol never carried into the current engine, ledgered forward "
                "through the NYISO attestation lineage. The entry's own note "
                "already recorded it as orphaned and named the two dispositions "
                "(wire it in, or delete as dead code, issue #1349); the OWNER "
                "took the delete branch in session nyiso-130. Rule 26 "
                "[R-DELETE]: removed, not zeroed."
            ),
            "n_entries": f"{n_prev} -> {n_prev - 1}",
            "n_residual": (
                f"UNCHANGED at {n_res} — the entry's identification was "
                "'published' (NERC GADS Brochure 3), so it never counted toward "
                "the residual-identified total. This corrects an OVER-count: a "
                "listed parameter that cannot bind a solve, not an unlisted one "
                "that can."
            ),
            "removed_entry": dropped,
        }
    )
    return dropped


# The inherited 2024/2025 classification, and its replacement. The old text made
# TWO claims that are false at HEAD and that the owner's 2026-08-06 decision to
# CLEAR NYISO's frontier status specifically rejects: an exhaustion claim ("every
# admissible mechanism tried on record") and an absolute one ("cannot form").
# Leaving them would let the keeper's own ledger re-assert what was just cleared.
_STALE_MARKER = "every admissible mechanism tried on record"
_REFRESHED_CLASSIFICATION = (
    "MODEL MISS (structural, UNDER-production — the five-zone representation "
    "under-forms the sub-zonal NYC/LI load-pocket scarcity that sets NYISO's real "
    "RT tail). CORRECTED 2026-08-06 (nyiso-130), in the same act as the owner's "
    "decision to CLEAR NYISO's frontier status, because the inherited text made "
    "two claims that are false at HEAD. (1) It said 'every admissible mechanism "
    "tried on record' — an EXHAUSTION claim. nyiso-130 opened a new named object "
    "and chartered its successor, so the lane is NOT exhausted and no ledger entry "
    "may say it is. (2) It said the representation 'CANNOT FORM' the scarcity — an "
    "absolute now falsified in the opposite direction: on this same keeper 2023 "
    "OVER-produces (22 h against 10), and 100 % of the modelled tail in all three "
    "years forms at one in-window Zone-K transfer bound. What survives, and all "
    "that is claimed here, is the measured under-production in THIS year. The "
    "chartered successor is a JOINT reconciliation of the Zone-K transfer bound "
    "and the downstate ST_GAS min_gen floor under rule 19 [R-ONE-MECH] — see the "
    "2023 entry's reason for why the bare number swap was tested and rejected."
)


# The inherited `reason` carries a long, VALUABLE adjudication record (nine
# candidates closed on the record) and one claim that is now false — that the
# lever queue is EXHAUSTED. The record is kept; the claim is superseded in place
# by a prepended notice, so nothing about the history is destroyed.
_STALE_REASON_MARKER = "EXHAUSTED lever queue"
_REASON_SUPERSEDE = (
    "SUPERSEDED IN PART, 2026-08-06 (nyiso-130) — READ THIS FIRST. The "
    "adjudication record below is accurate and is retained in full, but its "
    "claim that NYISO's C3c lever queue is EXHAUSTED is NO LONGER TRUE and must "
    "not be quoted forward. nyiso-130 opened a new named object the record does "
    "not contain: NYISO's own TABLE 1 note 2 (Locality Bulk Power Transmission "
    "Capability Reports) shows the Zone-K 'Locality Limit' the model applies as "
    "an hourly bound is the transfer limit NET of a 660 MW generation "
    "loss-of-source, and 100 % of the modelled C3c tail in all three years forms "
    "at that bound. The bare number swap was pre-registered, tested and REJECTED "
    "on its own kill gate (the downstate ST_GAS floor absorbs the relief), so the "
    "successor is a CHARTERED joint reconciliation of the transfer bound and the "
    "min_gen floor under rule 19 [R-ONE-MECH]. The owner CLEARED NYISO's frontier "
    "status on the same day and for the same reason. Also correct in the record "
    "below but worth flagging: its stated RE-OPEN CONDITION (a Capital_Hudson -> "
    "Zone-F/Zone-G topology split) was falsified as written by nyiso-124 at G0. "
    "--- ORIGINAL REASON, RETAINED VERBATIM: "
)


def _supersede_exhaustion_claim(obj: dict) -> list[int]:
    """Prepend a supersede notice to any inherited reason claiming exhaustion.

    Idempotent: an entry whose reason already opens with the notice is skipped.
    """
    fixed: list[int] = []
    for e in obj.get("exceptions", []):
        reason = str(e.get("reason", ""))
        if reason.startswith("SUPERSEDED IN PART, 2026-08-06"):
            continue
        if _STALE_REASON_MARKER in reason:
            e["reason"] = _REASON_SUPERSEDE + reason
            fixed.append(int(e["year"]))
    return fixed


def _refresh_inherited_classifications(obj: dict) -> list[int]:
    """Strip the exhaustion / 'cannot form' claims from inherited C3c entries.

    Returns the years corrected. Idempotent: an entry already carrying the
    refreshed text has no stale marker and is skipped.
    """
    fixed: list[int] = []
    for e in obj.get("exceptions", []):
        text = str(e.get("classification", ""))
        # The replacement QUOTES the stale marker (it explains what it removed),
        # so a bare substring test would re-match its own output forever. Compare
        # against the replacement itself for the idempotency guard.
        if text == _REFRESHED_CLASSIFICATION:
            continue
        if _STALE_MARKER in text:
            e["classification"] = _REFRESHED_CLASSIFICATION
            fixed.append(int(e["year"]))
    return fixed


def main() -> int:
    """Write the owner-authorized 2023 entry into the keeper's ledger."""
    obj = json.loads(ATTESTATION.read_text())

    superseded = _supersede_exhaustion_claim(obj)
    if superseded:
        obj.setdefault("_ledger_corrections", []).append(
            {
                "date": "2026-08-06",
                "session": "nyiso-130",
                "correction": (
                    "SUPERSEDED the exhaustion claim in the inherited C3c reason for "
                    + ", ".join(str(y) for y in superseded)
                    + ". The nine-candidate adjudication record is RETAINED VERBATIM — "
                    "it is accurate and valuable — but its 'EXHAUSTED lever queue' "
                    "claim is prefixed with a supersede notice, because nyiso-130 "
                    "opened a new named object and chartered its successor, and the "
                    "owner cleared NYISO's frontier status the same day for the same "
                    "reason. Nothing is deleted."
                ),
            }
        )
        ATTESTATION.write_text(json.dumps(obj, indent=1))
        print(f"exhaustion claim superseded for: {superseded}")

    refreshed = _refresh_inherited_classifications(obj)
    if refreshed:
        obj.setdefault("_ledger_corrections", []).append(
            {
                "date": "2026-08-06",
                "session": "nyiso-130",
                "correction": (
                    "REWROTE the C3c classification for "
                    + ", ".join(str(y) for y in refreshed)
                    + ": removed the exhaustion claim ('every admissible mechanism "
                    "tried on record') and the absolute 'cannot form', both false at "
                    "HEAD and both rejected by the owner's same-day decision to clear "
                    "NYISO's frontier status. The measured under-production each year "
                    "actually shows is retained; nothing is softened."
                ),
            }
        )
        ATTESTATION.write_text(json.dumps(obj, indent=1))
        print(f"classification refreshed for: {refreshed}")

    dropped = _drop_phantom_entry(obj)
    if dropped is not None:
        fp = obj["free_parameters"]
        print(
            f"ledger correction: removed {PHANTOM_ENTRY}; "
            f"n_entries -> {fp['n_entries']}, n_residual {fp['n_residual']} (unchanged)"
        )
        ATTESTATION.write_text(json.dumps(obj, indent=1))

    existing = {int(e["year"]): e for e in obj.get("exceptions", [])}
    if 2023 in existing:
        print("2023 exception already present — nothing to do")
        return 0

    withheld = obj.pop("_withheld_exception", None)
    if withheld is not None:
        obj["_withheld_exception_history"] = {
            "resolved_by": (
                "OWNER DIRECTIVE, session nyiso-130, 2026-08-06 (quoted in the "
                "2023 exception's reason). The block below is PRESERVED, not "
                "deleted: the record must show the exception was AUTHORIZED, "
                "not quietly widened under the 2024 caveat's classification. "
                "The withheld-exception guard itself stays in force for any "
                "future wrong-sign miss (scripts/gen_nyiso130_attestation.py)."
            ),
            "withheld_block_as_written_by_nyiso_129": withheld,
        }

    obj["exceptions"] = sorted(
        list(obj.get("exceptions", [])) + [ENTRY_2023], key=lambda e: int(e["year"])
    )
    ATTESTATION.write_text(json.dumps(obj, indent=1))
    print(
        f"keeper ledger: {len(obj['exceptions'])} C3c exception(s) "
        f"({', '.join(str(e['year']) for e in obj['exceptions'])}); "
        f"withheld block preserved as history: {withheld is not None}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
