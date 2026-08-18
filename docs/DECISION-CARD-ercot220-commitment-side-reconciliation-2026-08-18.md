# DECISION CARD — ercot-220: the commitment-side aggregate capability reconciliation (B-2) — DRAFT AWAITING SIGNATURE; the session RECOMMENDS **DO NOT SIGN**; NOTHING armed or built

> Drafted 2026-08-18 in the ercot-220 Phase-0 session, per the dispatch's
> closure clause ("write it up as a closure and escalate to the owner for a
> card — never arm it") and the ercot-219 §6 handback. Status: **DRAFT
> AWAITING SIGNATURE — AND CARRYING A MEASURED EX-ANTE KILL.** No
> `ScenarioConfig` field exists for it, no LP has run, no matrix cell is
> minted. Keeper at drafting: `2026-08-17-ercot215-arm-decontam` (NOT-YET,
> fail set {C3a-2023 −40.1 %, C3b-2023 0.736}, C3c ledgered CAVEAT ×3).
> Evidence base: `docs/FINDING-ercot220-stage1-capability-object-phase0-2026-08-18.md`
> + `results/calibration/ercot220_stage1_basis_phase0.json`.

## 0. WHAT THIS CARD IS, AND WHY IT EXISTS UNSIGNED

ercot-219 executed B-1 (the availability-side aggregate reconciliation) and
refuted it dimensionally; its §6 named the only dimensionally-coherent
successor — reconcile the model's **committed/online** capability to the
telemetered online aggregate `T_tel`, constraining commitment rather than
availability — and declined to propose it because it is the ercot-163-refuted
commitment-state route, requiring its own licence. The ercot-220 Phase-0
measured the full stage-1 candidate space and confirmed this is the ONLY
instrument that reproduces the firing margins (every admissible
availability-side basis is measured unable to reach the object even in the
ideal PRC limit — finding §6). Program discipline requires the instrument to
be put to the owner rather than silently dropped: this card is that
escalation. It is drafted **complete enough to sign** and carries the
session's recommendation **not to sign it**.

## 1. THE DECISION TEXT (for the owner to sign verbatim, as **B-2**)

> **B-2 (owner):** The ERCOT backcast may carry a measured
> **commitment-side aggregate reconciliation**: per backcast hour, the
> model's committed/online thermal capability (the set of units the LP may
> hold online, dispatch free within it; the rule-18 fast-start set exempt)
> is bounded so its aggregate matches the published telemetered online
> aggregate (`T_tel` = `rtolhsl` − wind/solar HSL − storage capability, the
> committed NP6-905 quantity columns — never a price column), applied
> consistently across all backcast years. I acknowledge what this signature
> spends: ERCOT-159/163 adjudicated telemetered-capability pinning as
> rule-13-forbidden because realized telemetry embeds realized commitment,
> and this instrument consumes exactly that information — the backcast's
> commitment state would no longer be the model's own. Runs carrying it are
> marked `commitment-reconciled` on their attestation and determination
> basis; the C6 attestation must name this signature; the forecast lane is
> untouched (no forward analogue of `T_tel` exists or is fabricated).

Sign-off line: `B-2 SIGNED (owner, date): ______`

**If B-2 is not signed, the ercot-220 closure stands unchanged: the ERCOT
backcast lane RESTS, stages 2–3 stay built and default-off, and Door D
(2026 SOM RTC+B-era anchors, ~mid-2027) is the floor for the 2023 price
object.**

## 2. THE MEASURED EX-ANTE KILL — why the session recommends NOT signing

Pre-registered facts, all from committed artifacts (finding §3/§6), that no
Phase-1 build can change because they precede any solve:

1. **Incidence.** Any basis reproducing the `T_tel` margins fires LOLP ≥ 0.5
   in **1,557 / 336 / 63** hours and ≥ $1,000 reservation offers in
   **5,780 / 4,270 / 2,270** hours against **181 / 53 / 31** actual tail
   hours — precision 11.3 % / 3.1 % in 2023. The ercot-219 G-SPUR blowout
   (9→273 / 11→671 / 1→1,239 against a +5 bar) was not shed contamination;
   it is the basis's own pre-solve arithmetic. The inherited gate table
   kills any arm built on these margins, by prediction rather than by test.
2. **Off-window mass.** 48 % of 2023's exhaustion population is off-season
   (November 187 h vs 3 tail hours; 572 h pre-ECRS-go-live vs 15) — the
   online margin is thin in slack months because units are economically
   de-committed, so the mechanism binds far outside any driver window it
   could declare (the rule-17 discipline applied to an offer channel).
3. **No admissible repair.** Discriminating the "really scarce" thin-margin
   hours from the abundance-thin ones requires either realized commitment
   at finer grain (more of what rule 13 forbids) or conditioning on the
   residual (forbidden outright). The discrimination the object needs is
   the conduct layer's adaptive expectation — measured NOT-TRANSFERABLE ×3
   and model-free non-identifiable at hour grain (ercot-210/211/218).
4. **What signing would actually buy:** the 2023 exhaustion *calendar* at
   the cost of a predicted four-gate kill and a spent rule-13 exception —
   against a standing adjudication that the residual is model-class and a
   dated data route (Door D) that resolves it structurally.

## 3. IF SIGNED ANYWAY — the execution constraints this card binds

One Phase-1 session (Opus/Fable, rule 27; `DATA PROFILE: ercot`; pinned
solve env, venv outside the repo): precommit pushed and blob-verified before
any solve, pinning the committed-set construction (P0-seam, rule-18
fast-start exemption, the ercot-219 Amendment-1 telemetry-spike guard
inherited, the 2024-01 MIS gap and post-RTC+B NaN tail carried as
reconciliation-inert), the rule-19 single-owner resolution against the
commitment bridges and the DAM availability rescale, and the card-§4 table
of DECISION-CARD-ercot218b verbatim (G-CAP / G-SPUR 9-11-1 +5 / G-SHED
0-1-0 / G-OWNER / G-BAT / G-DOF / G-D2 / G-REPRO, LOYO declared) plus a
**G-D4-OFFWINDOW leg**: the arm fails if stage-3 offers ≥ $1,000 bind
outside the declared sequestration-summer window at more than the
control's incidence. A/B on the ercot-215 keeper recipe, full span
2023–2025 in one bundle per member, years sequential, both members
registered with payloads (rules 12/15/16). Promotion remains a separate
owner decision on the recorded verdict.

## 4. WHAT THIS CARD DOES NOT REOPEN

B-1 / the availability-side aggregate route (`R`, ercot-219 — the
DO-NOT-REDO stands whether or not B-2 is signed); `rtolcap` in any role
beyond the armed reserve-supply cap; Door A fitted conduct functions
(NOT-TRANSFERABLE ×3); `ercot_storage_rt_offer_surface` (R); item 11's
per-unit crosswalk (Q-B FINAL); the mid-band spill lane (CLOSED ercot-215);
the regime lane (CLOSED ercot-217 — the instrument carries no year key);
ercot-206 B0 (the LOLP table stays out of the price channel); Q-B FINAL /
R-A reporting discipline.

---
*Drafted ercot-220 session, branch `claude/ercot-220-lever-phase0-je3znm`,
on the session's own Phase-0 measurement. The recommendation is the
session's; the decision is the owner's, on this record.*
