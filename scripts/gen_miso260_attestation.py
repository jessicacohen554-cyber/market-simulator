"""Write the miso-260 bundle's attestation — the 2020/2021 measured seam ladder.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL outright
instead of reclassifying to a ledgered CAVEAT under the rule-22 standing rule's
guard (b)), so this is generated AT the promotion and never typed by hand.

Pattern unchanged from ``gen_miso250_attestation.py`` (E10): the last COMMITTED
MISO attestation is carried verbatim, ``governance.attested_by`` is re-stamped
with THIS bundle's narrative, and every ``price_tail`` / ``price_mean``
exception magnitude is RE-MEASURED from this bundle's own scored records rather
than copied.

TWO DEPARTURES FROM THAT PATTERN, both stated rather than silent:

1. **The carried source is miso-255, not the incumbent keeper.** The incumbent
   ``2026-09-16-miso-259-coal-fuel`` **never committed a
   ``calibration_attestation.json`` at all** — its registration commit
   (``0333feb1``) carries only the bench parts, the sidecar, the payload and a
   compose probe, because its span bundle was gitignored in full. So on any
   fresh clone the current keeper scores **C6 UNATTESTED**. The last committed
   MISO attestation is ``miso255_sil_keeper``'s, recovered from git at
   ``61c726d0^`` (the commit that pruned it), and that is what this carries.
   This promotion also COMMITS its attestation, closing the gap.

2. **The DOF ledger is carried with NO new entry**, because this arm adds no
   ``ScenarioConfig`` field and no free parameter: every number in the two new
   ``MISO_SEAM_LADDER_BY_YEAR`` rows is a quantile of a measured series at a
   structurally fixed depth grid, emitted verbatim by the frozen
   ``scripts/data/derive_miso_seam_ladders.py``. The ledger is inherited rather
   than rebuilt for the reason ``gen_miso250_attestation.py`` records:
   ``scripts/build_dof_ledger.py`` silently drops the hand-declared MISO
   entries, and losing a declared free parameter at a promotion is a rule-21
   regression.

Usage::

    PYTHONPATH=.:src python scripts/gen_miso260_attestation.py \
        --bundle results/calibration/miso260_seam_span \
        --run-id 2026-09-16-miso-260-seam-ladder
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

#: The last MISO attestation that was ever COMMITTED (see departure 1 above).
CARRIED_REL = "results/calibration/miso255_sil_keeper/calibration_attestation.json"
#: Refs tried in order; `61c726d0^` is the commit before the prune that deleted it.
CARRIED_REFS = ("HEAD", "origin/main", "61c726d0^", "HEAD~1", "HEAD~2", "HEAD~3")

ATTESTED_BY = (
    "miso-260 KEEPER (2026-09-16): MISO'S MEASURED SEAM LADDER ARMED IN 2020 AND 2021, "
    "COMPLETING A BACK-FILL miso-252 COULD ONLY HALF-FINISH. The single delta against "
    "the incumbent keeper 2026-09-16-miso-259-coal-fuel is TWO ROWS ADDED TO THE "
    "MISO_SEAM_LADDER_BY_YEAR REGISTRY TABLE — no new ScenarioConfig field, no new CLI "
    "flag, no new free parameter (rules 21 [R-DOF] / 24 [R-REGISTRY]); the gate "
    "miso_seam_measured_ladder was already armed and already recorded in run_config, "
    "and what changes is only which years it reaches. The 2022-2025 rows are BYTE-"
    "IDENTICAL, so 2023-2025 solve exactly as the incumbent did and the CALIBRATED "
    "train tier cannot move by construction, not by measurement. "
    "RULE 23 [R-FROZEN-DERIVE] BASIS — THE SOURCE DATA UPDATED, and the trigger is "
    "cited rather than asserted: FINDING-miso252-seam-fallback-and-the-923-block-"
    "2026-09-10.md section 3(a) recorded 2020-2022 as blocked and named "
    "data/raw/eia-930-interchange/MISO interchange hourly.parquet ('2023-2025') the "
    "BINDING blocker. Both halves landed THREE DAYS LATER and nothing re-checked: "
    "f9259f91 (2026-09-13) landed MISO's 2020 and 2021 hourly DA/RT hub LMP (8,760 h "
    "each; 2021 DA 8,736 of 8,760) and 00249712 (same day) widened the interchange "
    "extract to 2020-2026. Those two series are the ONLY inputs to the primary Q-Q "
    "construction — the PJM western-border price is a diagnostic anchor for the "
    "neighbour OVERLAYS, not an input to the base ladder. Not re-derived because a "
    "residual moved. "
    "THE ESTIMATOR IS UNMODIFIED AND DEMONSTRABLY FAITHFUL: run at HEAD the frozen "
    "scripts/data/derive_miso_seam_ladders.py reproduces EVERY previously-committed "
    "entry at 256 of 256, max |derived - committed| = 0.0000, and with the two new rows "
    "the table reproduces at 384 of 384 — which the existing "
    "test_incumbent_registry_reproduces_the_frozen_derivation now enforces over the "
    "whole span at atol 0.005 with no exception list. "
    "WHAT IT REPLACES, measured off the INCUMBENT KEEPER'S OWN committed unit_hourly "
    "seam-band marginal costs: with no entry the injector returns at its first guard "
    "and every band takes the flat gas-elastic reference price, which in these two "
    "years is DEGENERATE ACROSS THE BAND GRID — 2021 South all eight import bands at "
    "$41.97 and all eight export bands at $37.97; 2021 Manitoba import AND export at "
    "the SAME $39.97, a same-seam wash the ladder's no-wash reconciliation forbids by "
    "construction; 2021 PJM import spanning $0.53 over eight bands against a measured "
    "$16.17 to $82.19; 2020 South all sixteen bands at $26.55 / $22.55. A band grid "
    "with no spread clears all-or-nothing, which is the bang-bang miso-252 section 2.4 "
    "measured (four 2021 PJM import bands within 1% of their own maximum in EVERY hour "
    "of the year), and it inverts the seam merit order (2021 prices PJM imports at "
    "$48.5 ABOVE their measured floor of $16.17 and South imports at $41.97 BELOW "
    "theirs of $65.86). "
    "THE MECHANISM'S OWN MEASURED FOOTPRINT, and why 2020 was the screen year: model "
    "net seam flow against the EIA-930 measured net, sum of |per-seam error| over the "
    "four seams — 2020 36.29 and 2021 25.41 TWh UNARMED, against 8.84 / 4.11 / 5.21 in "
    "the armed 2022 / 2023 / 2025 — with two seams carrying the WRONG SIGN (2021 SPP "
    "model -2.98 vs measured +2.15; 2021 South model +1.69 vs measured -7.66; 2020 "
    "South model +3.44 vs -2.93). The screen year was named in the PRECOMMIT BEFORE the "
    "screen ran, on that largest measured footprint and NEVER on the residual: 2021 "
    "carries the larger C3b miss and is not the screen year. "
    "THE SCREEN AND ITS FAILURE, STATED NOT BURIED. 2020, ARM vs CONTROL one commit "
    "apart, both solved by shards, parent zero LP. G-DIRECTION PASS (sum |per-seam err| "
    "36.302 -> 6.505 TWh, and the 2020 South seam's sign corrected +3.441 -> -0.083 "
    "against a measured -2.93). G-BALANCE PASS (slack and dump 0.0000 TWh in both "
    "arms). G-NOFLIP FAILED: C1 2020 COAL_BIT -7.00 -> -10.29 TWh, outside the +/-8 TWh "
    "band. Under the rule 29 [R-SCREEN] text this session STARTED from, that killed the "
    "arm: the span was not spent on the session's own authority and the session "
    "recommended against promotion. "
    "THAT RULE TEXT WAS ALREADY SUPERSEDED WHEN THE SCREEN RAN, and the correction is "
    "owed rather than convenient. Commit fa170333 (2026-09-16T06:47:56Z, owner "
    "instruction 'Get rid of the screen year rule altogether') REMOVED the screen-year "
    "regime — the one-year screen, the duty to name the screen year on the mechanism's "
    "footprint, the 'full span only if the screen clears' condition, and the STRUCTURAL "
    "STOP GATE itself with its 'may kill an arm' framing and its 'the remaining years "
    "are never spent' outcome. This session pushed its PRECOMMIT twelve minutes later "
    "(9d1322ad, 06:59:09Z) against a CLAUDE.md snapshot taken before the amendment, so "
    "it screened under a rule that no longer required a screen and then stopped on a "
    "gate that no longer had the authority to stop it. Under the amended rule the span "
    "was owed unconditionally (rule 34 [R-SHARD-PROMOTABLE] (c): a registrable run "
    "solves EVERY year the ISO carries), which is what this bundle is. The screen is "
    "therefore reported as EVIDENCE — it is a clean same-recipe A/B one commit apart and "
    "its numbers stand — and NOT as an authority that was overridden. "
    "WHY IT IS A KEEPER ANYWAY: the OWNER RULED (2026-09-16, verbatim: 'If structural "
    "integrity improves but gates regress that may still be a keeper'), which is trigger "
    "(i) of rule 31 [R-RETAIN] and the decision rule 29 reserves to the owner. The "
    "ruling is consistent with rule 14 [R-ACCURATE], which this arm is a textbook case "
    "of — a gas-elastic proxy FITTED ON THE 2023-2025 TRAINING WINDOW replaced by the "
    "seam's own measured revealed supply curve — and rule 14 says in terms that a "
    "measured input is KEPT when the fit worsens and the worse fit is treated as a "
    "discovered bug. The discovered bug is named and routed, not absorbed — and NOT as "
    "this session first named it. RESULT section 3 called it 'the standing gas deficit, "
    "13 to 35 TWh under in every year'; ADDENDUM B WITHDRAWS that, because those numbers "
    "are on the fuelRows per-fuel-family basis and miso-253 (2026-09-10) had already "
    "measured that basis against MISO's own EIA-930 telemetry — which reconciles to the "
    "BA's reported net generation to 0.0002% — and found 68.1 TWh of OFFSETTING "
    "per-family error: gas -33.526, other +23.111, coal +10.827. A bench under-"
    "attributing gas by 33.5 TWh makes the model's gas row read ~33 TWh low whatever the "
    "model does, so the two readings are indistinguishable on present evidence and "
    "settling them is intake work, not a solve. ON THE BASIS THAT ACTUALLY GATES — C1, "
    "per class, grid-delivered — the stable same-sign misses are COAL_BIT (negative in 5 "
    "of 6 years, mean -4.35 TWh, and the class THIS ARM pushed out of band in 2020), "
    "ST_CHP (6 of 6, sigma under 0.4 TWh) and ST_GAS (5 of 6). COAL_PRB oscillates while "
    "COAL_BIT is persistently short, which is an INTRA-COAL MERIT-ORDER SPLIT that "
    "survived miso-259's coal-LEVEL repair. That is the routed object. "
    "RULE 13 [R-MEASURED]: the ladder is a REVEALED SUPPLY CURVE, never a pinned "
    "outcome — the LP still clears every band economically hour by hour against its own "
    "internal price, nothing is forced, at price extremes even the base band backs off, "
    "and the forward story is the pooled multi-year ladder the derive script prints "
    "(forecast years keep the gas-elastic formula, the same two-track design as "
    "hr_by_year). RULE 25 [R-ISO-SCOPE]: MISO's own measured series only. "
    "Records: docs/RESULT-miso260-seam-ladder-screen-2026-09-16.md, "
    "docs/PRECOMMIT-miso260-seam-ladder-2020-2021-2026-09-16.md, probes "
    "scripts/probes/_miso260_seam_phase0.py and _miso260_compose_span.py."
)

DISCLOSURES_NOTE = (
    "miso-260 disclosures, reported rather than patched. "
    "(a) THE SESSION'S OWN SCREEN KILLED THIS ARM and it is promoted on the owner's "
    "ruling; the G-NOFLIP failure (C1 2020 COAL_BIT -7.00 -> -10.29 TWh) is the "
    "headline of the screen, not a footnote, and the span numbers in this bundle are "
    "where it is scored at full magnitude. "
    "(b) TWO OF MY FIVE PRE-REGISTERED STOP GATES FAILED ON TEXT I MIS-SPECIFIED, and "
    "they are retired on grounds INDEPENDENT of which way they went. G-FOOTPRINT "
    "asserted byte-identical non-seam `mc`, which this recipe's armed P0->P1 startup-"
    "markup amortization (tranche_startup_amortization + tranche_startup_conditional_"
    "runs) cannot deliver: 405 of 3,227 non-seam rows move, ALL gas (82 gas_cc / 252 "
    "gas_ct / 71 gas_st) and ZERO coal, hydro, nuclear or oil, with 362 of them also "
    "moving their P0 run pattern — a direct repricing leak would not respect that "
    "boundary. G-SPREAD counted DISPATCH pinning, and its premise is false in a screen "
    "year whose control has 0 pinned bands; the measured record says the PJM seam "
    "imports in ~100% of hours, so pinned cheap base bands are the target behaviour. "
    "G-NOFLIP is NOT retired: a gate dropped because it bit is the fitted-mechanism "
    "selection rule 1 [R-STRUCT] exists to forbid. "
    "(c) THE INCUMBENT KEEPER HAS NO COMMITTED ATTESTATION. "
    "2026-09-16-miso-259-coal-fuel's registration commit 0333feb1 carries only bench "
    "parts, the sidecar, the payload and a probe — its span bundle was gitignored in "
    "full — so on any fresh clone that keeper scores C6 UNATTESTED and its "
    "build_status output degrades to 'governance gate UNATTESTED'. This attestation is "
    "carried from miso255_sil_keeper (recovered from git at 61c726d0^) and IS "
    "committed, together with the rule-15 [R-DASHBOARD] hourly sidecars the incumbent "
    "also omitted. "
    "(d) MISO'S KEEPER IS TWO CONFIGS, NOT 'ONE RECIPE OVER TWO TIERS' as the keeper "
    "shard's config_partition.structure_note asserts: miso_measured_reserve_"
    "requirements and miso_reserve_online_gated are False in 2020-2022 and True in "
    "2023-2025. The partition is FORCED BY DATA, not chosen — "
    "load_miso_reserve_requirements HARD-ERRORS for 2020, 2021 and 2022 (verified; the "
    "measured cleared-reserve parquet starts in 2023) — so the benign reading is right "
    "and only the note's wording is wrong. Consequence for rule 32 [R-SHARD] (b): a "
    "single --years 2020..2025 invocation is IMPOSSIBLE for MISO, it would raise on its "
    "first year, and two invocations is the floor. This bundle is composed from exactly "
    "two partition legs and scripts/probes/_miso260_compose_span.py checks both halves "
    "of that partition before it writes anything. "
    "(e) THE COMPOSITE'S BASE run_config.json IS THE VALIDATION LEG'S and therefore "
    "records that leg's reserve flags for the whole span; run_config_<y>.json carries "
    "the truth and stamp_config_partition.py records it. "
    "(f) THE D-2 CT_PEAKER OVER-BUDGET ROW IS PRE-EXISTING, not this arm's — it fails "
    "in the screen CONTROL too (35.9%) — but this arm WORSENS it (50.6% in the 2020 "
    "screen) and adds a NEW D-1 failure (2020 COAL_PRB off-peak CV ratio 0.451 against "
    "a 0.5 bar). Both are scored on the span in this bundle's own "
    "legitimacy_diagnostics.json, which is REGENERATED over the composite rather than "
    "copied from a leg. "
    "(g) NO NEIGHBOUR OVERLAY FOR 2020/2021, the same data boundary 2022 already "
    "states: pjm_border_lmp_hourly_MISO.parquet and the SPP hub series both start in "
    "2023, so the overlay tables carry no 2020/2021 key and the code degrades to the "
    "base ladder — the documented behaviour of miso_seam_neighbour_*, never an unpriced "
    "seam, and never a new path. Landing those two series for 2020-2022 is a data-"
    "intake lane, routed and not shipped here."
)


def _carried_attestation() -> dict:
    """Return the last committed MISO attestation, from disk or from git."""
    src = REPO / CARRIED_REL
    if src.exists():
        return json.loads(src.read_text())
    for ref in CARRIED_REFS:
        got = subprocess.run(
            ["git", "show", f"{ref}:{CARRIED_REL}"],
            capture_output=True,
            text=True,
            cwd=REPO,
            check=False,
        )
        if got.returncode == 0 and got.stdout.strip():
            return json.loads(got.stdout)
    raise SystemExit(
        f"carried attestation not on disk at {src} and not in git at "
        f"{', '.join(CARRIED_REFS)} for {CARRIED_REL} — refusing to write an "
        "attestation without the DOF ledger it must carry (rule 21 [R-DOF])"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    if not bundle.is_absolute():
        bundle = REPO / bundle
    att = _carried_attestation()

    # calibration_verdict exits 1 on NOT-YET, which is exactly the state this
    # bundle is in BEFORE its attestation exists (an unattested C6). The JSON on
    # stdout is complete either way, so the exit status is deliberately unchecked.
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            args.run_id,
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
    scored = json.loads(proc.stdout)["criteria"]

    # RE-MEASURE every carried exception magnitude on THIS bundle's own scored
    # records; classification and reason are the standing MISO adjudications.
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
                "this run's own scored value (miso-260); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
            n_remeasured += 1

    # RULE 21 [R-DOF]: the ledger is carried VERBATIM with NO new entry, because
    # this arm adds no ScenarioConfig field and no free parameter — every number
    # in the two new registry rows is a quantile of a measured series at a
    # structurally fixed depth grid, emitted verbatim by the frozen derive. It is
    # deliberately NOT rebuilt by scripts/build_dof_ledger.py, which silently
    # drops the hand-declared MISO entries (see gen_miso250_attestation.py).
    att["free_parameters"]["carried_from"] = (
        f"{CARRIED_REL} — carried VERBATIM with no new entry: miso-260 adds no "
        "ScenarioConfig field and no free parameter (rules 21 [R-DOF] / 24 "
        "[R-REGISTRY])."
    )
    att["governance"]["attested_by"] = ATTESTED_BY
    att["disclosures"] = {"note": DISCLOSURES_NOTE}

    out = bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    print(
        f"  exceptions carried: {len(att['exceptions'])}, re-measured: {n_remeasured}"
    )
    print(
        f"  DOF ledger entries carried: {att['free_parameters']['n_entries']} "
        f"({att['free_parameters']['n_residual']} residual-identified), 0 added"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
