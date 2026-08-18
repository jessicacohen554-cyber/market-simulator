# DECISION CARD — ercot-218b: a structural model of ERCOT-2023 artificial-shortage price formation (OPTION B — for owner signature; NOTHING armed or built until signed)

> Drafted 2026-08-18 in the ercot-218 session on the owner's instruction
> ("Do it" → option **b**), from
> `docs/RESEARCH-ercot218b-why-2023-prices-2026-08-18.md` §5. Status:
> **DRAFT AWAITING SIGNATURE.** No `ScenarioConfig` field exists, no LP has
> run, no matrix cell is minted. The Phase-1 session that executes this card
> pushes its own precommit before any solve, per program discipline. Keeper
> at drafting: `2026-08-17-ercot215-arm-decontam` (NOT-YET, fail set
> {C3a-2023 −40.1 %, C3b-2023 0.736}, C3c ledgered CAVEAT ×3).

## 0. WHAT SIGNING THIS DOES

It authorizes ONE scoped exception to the current adjudication record — a
**measured aggregate-capability reconciliation** for the ERCOT backcast —
and charters, under a pre-registered direction-blind kill-gate table, a
three-stage structural mechanism whose other two stages introduce **zero
fitted scalars** and violate no existing rule. It does NOT re-open Door A
(fitted conduct functions), does NOT re-open ercot-162 (measured offer
surfaces fed verbatim), does NOT re-open item 11's per-unit crosswalk
(Q-B stands), and does NOT touch the forecast lane's methodology (the
mechanism self-extinguishes outside the pre-reform ORDC regime by
construction — its driver collapses when the sequestration design ends).

## 1. THE DECISION TEXT (for the owner to sign verbatim, as **B-1**)

> **B-1 (owner):** The ERCOT backcast may carry a measured
> **aggregate-capability reconciliation**: the fleet's hourly dispatchable
> capability is reconciled to ERCOT's published real-time telemetered
> aggregate (the committed NP6-905 quantity columns, `rtolhsl`/`rtolcap` —
> never a price column), applied **consistently across all backcast years**
> as a measured availability input under rule 14's reconciled-real-data
> clause. I acknowledge the standing tension this signature resolves:
> ERCOT-159/163 adjudicated per-hour telemetered-capability caps as
> rule-13-forbidden because realized telemetry embeds realized commitment.
> I accept the reconciliation on the rule-14 ground that the accurate
> aggregate is measured, the per-unit identification twice failed its
> licence (item 11), and the model's current aggregate is demonstrably less
> reflective of reality (the ~2.7 GW responsive wedge, ercot-170/191,
> term A = 102 % of the gap). Runs carrying it are marked
> `capability-reconciled` on their attestation and determination basis, and
> the C6 governance attestation must name this signature. The exception
> covers the AGGREGATE reconciliation only; every per-unit and per-price
> form stays closed.

Sign-off line: `B-1 SIGNED (owner, date): ______`

**If B-1 is not signed, this card is void and the ercot-218 close-out
(Door D floor, lane resting) stands unchanged.**

## 2. THE MECHANISM — three stages, all from parts the model already owns

**Stage 1 — capability reconciliation (the keystone; the only part needing
B-1).** A backcast availability overlay in the existing measured-overlay
family (CAMPD outages, DAM availability rescale): for each backcast hour,
scale ERCOT thermal availability so the model's aggregate online
dispatchable capability matches the published telemetered aggregate. The
Phase-1 precommit pins the exact basis (`rtolhsl` vs `rtolcap`), the scaled
population (merchant thermal; nuclear/must-run excluded), and the
reconciliation arithmetic (single hourly scalar on availability, floor at
the CAMPD-outage-derated level so it can only tighten, never resurrect an
outaged unit), each with citations. Rule-19 duty: this overlay and the
existing thermal DAM availability rescale must be reconciled into ONE
owner of the phenomenon — the precommit states which subsumes which, and
the D-2 attribution carries it.

**Stage 2 — the exhaustion expectation (zero new scalars).** Per hour, the
probability that the model's own dispatchable stack exhausts within the
remainder of the operating day:
`P_exhaust(t) = max over h in [t..end-of-day] of LOLP(H(h))`, where
`H(h)` = reconciled dispatchable capability − load − sequestered AS MW
(the armed ECRS/RRS withholding families), and `LOLP(·)` is the model's
OWN registered curve (`resolve_lolp_params`, `ordc_lolp_mu_mw`,
`ordc_lolp_sigma_mw`, `ordc_mcl_mw`) evaluated at the exhaustion margin.
Every constant already exists in `ScenarioConfig` with citations; the only
new choices are conventions (the within-day window; the load basis), pinned
in the precommit as conventions, not parameters. Forward-computable by
construction: in a forecast year it regenerates from the model's own state,
and it collapses post-reform (release trigger) and at RTC+B (sequestration
retired), so the mechanism self-extinguishes with the design that caused it.

**Stage 3 — the storage reservation-price offer (zero new scalars).** In
**P1 only**, through the existing `mc_bid_adjust` seam (the P1-only offer
channel every ERCOT offer mechanism since ERCOT-86 rides), storage
discharge is offered at
`max(ε, P_exhaust(t) × ordc_voll)` — the textbook reservation price of
stored energy: probability of the cap event times the cap. P0 (commitment
discovery) is untouched; both factors are the model's own quantities. The
measured August-2023 anchor is evidence, never an input: realized daily
P(≥$1,000 spike) 0.52 vs the measured offer-implied 0.67
(RESEARCH-ercot218b §5). The adaptive/backward-expectation extension
(June/July cap-parking, September's August-informed pricing) is **out of
scope** — it would carry real DOF; it may be proposed only as its own
future card.

## 3. IDENTIFICATION / DOF LEDGER (target: zero fitted scalars)

| quantity | source | fitted? |
|---|---|---|
| aggregate capability series | published NP6-905 telemetry, committed, quantity-only | no — measured (B-1) |
| sequestered AS MW | measured ASPLANNP433 plan + armed withholding families | no — already keeper inputs |
| LOLP μ/σ, MCL | registered `ordc_lolp_*`, `ordc_mcl_mw` (published ORDC basis) | no — existing cited constants |
| cap | `ordc_voll` = $5,000 (16 TAC 25.509) | no |
| window / load-basis conventions | precommit-pinned conventions with citations | no (conventions, disclosed) |

Any quantity that cannot be sourced this way during the build is a STOP —
the mechanism is not built with a fitted stand-in (rules 5/13/23).

## 4. KILL GATES — direction-blind, pre-registered, inherited baselines

The Phase-1 A/B (control = the ercot-215 keeper recipe, replayed;
arm = control + stages 1–3) is judged ONLY by this table, never by the sign
of any residual move (the ercot-204/213/215 discipline):

| gate | rule |
|---|---|
| G-CAP | 0 protocol-cap violations (λ + adders ≤ VOLL) in all 26,280 hours |
| G-SPUR | spurious mid-band hours vs the 9/11/1 energy-made baseline, bar +5/yr (ercot-213 §3 inheritance) |
| G-SHED | no new load-shed hours vs the keeper's 0/1/0; identical-hour-list check |
| G-OWNER | C3a-2024 PASS, C3a-2025 PASS, C3b-2024 ≤ 0.20 all retained |
| G-BAT | storage net discharge at actual-tail hours within ±25 % of measured EIA-930 BAT where the series exists (2024/2025) — the ercot-162 collapse falsifier |
| G-EXH | reported, not gated: the count and calendar of model exhaustion-regime hours per year (the 2023-vs-2024/25 contrast is the mechanism's own signature) |
| G-DOF | ledger delta = the B-1 series only; zero fitted scalars; n_residual not increased |
| G-D2 | no new D-4 off-window rows; stage-1/stage-3 attribution rows present with declared windows (rules 17/19/20) |
| G-REPRO | control replays the keeper's committed determination before the arm is read |
| LOYO | parameter-free rule → structurally N/A, declared pre-solve; per-year deltas stand in its place (ercot-173/213 precedent). If ANY scalar ends up identified, full LOYO 2023–2025 before promotion |

Verdict rule: any gate FAIL ⇒ REJECTED-AS-ARMED at full magnitude,
recorded unrewritten; owner promotion over a mechanical kill remains an
explicit owner act (the ercot-188/213/215 pattern), never the session's.

## 5. EXECUTION PLAN AND COST

One Phase-1 session (Opus/Fable, rule 27; `DATA PROFILE: ercot`; the pinned
solve env, venv outside the repo): precommit pushed first (exact stage-1
basis and conventions, this gate table verbatim) → build behind three new
default-off `ScenarioConfig` booleans (matrix rows in the same PR, rule
28c) → seam proof (gate-off byte-identity ×3 years; cross-ISO byte-identity
— stages are ERCOT-gated) → control replay + armed solve, years sequential
→ gates → register the A/B pair per rule 15 → matrix cells + log in the
same session. Promotion is a separate owner decision on the recorded
verdict. Estimated cost: one full 3-year A/B (two solves × 3 years, several
hours wall-clock) plus the overlay derive.

## 6. WHAT THIS CARD DOES NOT REOPEN

Door A fitted conduct functions (ercot-210/211/218 NOT-TRANSFERABLE ×3);
`ercot_storage_rt_offer_surface` (R); item 11's per-unit crosswalk (Q-B
FINAL — B-1 is the aggregate route precisely because the per-unit route is
closed); the mid-band spill lane (CLOSED, ercot-215); the regime lane
(CLOSED, ercot-217 — stages 1–3 add no regime parameter; the 2023
distinction emerges from carried inputs); Q-B/R-A reporting discipline
(2023 numbers in the A/B are side-effect reporting at full magnitude,
never a basis — the gate table contains no 2023 price criterion).

## 7. OPEN CHOICES THE PHASE-1 PRECOMMIT MUST PIN (with citations, before any solve)

1. Stage-1 basis: `rtolhsl` vs `rtolcap`, and the 2025 post-RTC+B tail
   handling (the series' 648 null hours).
2. The scaled population and the outage-floor interaction with the CAMPD
   overlay and the DAM availability rescale (the rule-19 single-owner
   resolution).
3. Stage-2 window convention (remainder-of-day vs fixed evening block) and
   load basis (same-hour actual load, already a backcast input).
4. Whether stage 3 also floors storage AS-product opportunity cost (out of
   scope by default; energy-only in this card).

---
*Drafted ercot-218 session, branch `claude/ercot-218-direct-driver-5ckiur`.
Awaiting B-1. If the owner prefers option C instead (the crosswalk data
intake that needs no rule change), say so and the data-spec card will be
drafted in its place.*
