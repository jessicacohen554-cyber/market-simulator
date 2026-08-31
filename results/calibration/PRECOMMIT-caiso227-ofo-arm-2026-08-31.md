# PRECOMMIT — caiso-227: the SoCalGas OFO gas-deliverability ARM (the caiso-131 A3 mechanism round) — trigger class, admissibility line, posture, gates and falsifiers fixed EX ANTE, before any solve (2026-08-31)

**Status: PRE-REGISTRATION ONLY. Nothing here is built.** caiso-226 was
chartered *intake-only, zero solves*: it landed the `gas-ofo-events` datatype
and its rule-13 adjudication
(`FINDING-caiso226-ofo-intake-2026-08-31.md`). This document fixes the future
arm's design **before** its yield is known, so that the arm session cannot
choose its trigger by what clears a gate. It adds **no `ScenarioConfig`
field, no mechanism, no matrix row, and runs no solve** — those are the arm
session's own deliverables, and arming remains a separate owner act (rule 1
`[R-STRUCT]`).

**Why pre-register at all.** caiso-131 §10 makes "derive a citygate threshold
that makes C3c-2024 clear" a binding DO-NOT-REDO, because the only non-arbitrary
threshold tried reached 17 tail hours against 18 needed and *moving it until
2024 clears* is a value fitted to the residual (rules 13 `[R-MEASURED]` / 24
`[R-DOF]`). The OFO record removes the price threshold but **multiplies the
dials** — side, stage, tolerance band, waived flag, run length, utility. Fixing
the definition ex ante is the only thing that stops this intake from becoming a
richer answer key than the one it replaced.

---

## §1 — What the arm would gate (ONE mechanism, rule 19 `[R-ONE-MECH]`)

A single gated CAISO-only `ScenarioConfig` field (default **False**, rule 25
`[R-ISO-SCOPE]`) that makes **gas deliverability** a represented commodity on
declared-OFO gas days, and is **inert on every other day by construction**.

The object it gates is a **quantity-side gas-supply limit**, not a price:

- On a gas day carrying a qualifying SoCalGas low OFO, the SP15 gas-fired
  fleet's *deliverable fuel* is constrained, so a subset of that fleet is
  unavailable or capacity-limited for the day's hours.
- The mechanism is therefore an **availability/derate overlay keyed to a
  measured physical event** — structurally the same object as the CAMPD unit
  outage windows, on the fuel-delivery side rather than the unit side.

**Explicitly NOT in scope for the arm**, each already refuted or forbidden:
- **No offer-curve, offer-rung or heat-rate work** — caiso-131 §10: the stack
  already carries $687–$1,632 rungs and 108–9,570 MW above $200 in the tail
  hours; the rungs are not the constraint.
- **No adder, uplift or scarcity price** applied on OFO days. A price-side
  response is what the LP must *produce*, never what it is handed.
- **No re-arming `caiso_endogenous_wecc_node`**, no AS-family lever, no
  allocation floor — all CLOSED by prior findings.

**The known headwind, stated up front and NOT argued away.** caiso-131 §5
measures the (λ, $200] band at **12.6–12.8 GW**, ~52 % of the available gas
fleet, spread across three gas classes and imports, and §10 makes "any
quantity-side derate / availability / deliverability mechanism aimed at
reaching λ > $200" a DO-NOT-REDO **on the caiso-129 §3(a) scale-invariance
grounds**. This precommit does not overturn that. It confines the arm to the
one thing the DO-NOT-REDO does not cover: a derate whose size is **identified
from the gas system's own published physics** rather than chosen to reach a
price. If that physically-identified derate is smaller than the band — which
§4's D1 will show *before* any solve — the arm **dies at D1 with no solve
run**, and C3c stays ledgered. That is a pre-registered acceptable outcome,
not a failure of the intake.

## §2 — The trigger definition, fixed NOW, on tariff grounds only

The trigger is defined **before** its coverage of the measured tail is known.
caiso-226 deliberately did not compute that coverage (FINDING §6) precisely so
this section could be written blind.

**Definition (pre-registered):** a qualifying gas day is one carrying a
**SoCalGas LOW OFO** (`side = "low"`) in `gas-ofo-events`.

Justification, entirely from what the instrument *is*:
- The **low** side is the under-delivery instrument: it is declared when the
  system cannot support shippers taking more gas than they deliver — i.e.
  exactly the physical condition "gas is hard to get to the burner tip." The
  **high** side is the linepack-surplus converse and is physically irrelevant
  to generation scarcity; it is excluded on meaning, not on yield.
- **`stage` is NOT used to rank severity.** FINDING §3.3 measures that `stage`
  and `tolerance_pct` are **not monotone in each other** (the widest bands sit
  at Stage 1; Stage 3.2 is uniformly −5). Since neither is a clean severity
  scale, selecting a stage cut would be selecting a *dial*, and the only
  available basis for choosing among the eight stages would be the residual.
  **Forbidden.** The arm uses the binary declaration.
- **`waived` days are INCLUDED.** A waiver relieves the *noncompliance charge*
  after the fact; it does not retract the physical condition that caused the
  declaration. Excluding them would be a second free choice.
- **The record is SoCalGas-only, so the overlay is SP15-only.** PG&E's NP15
  ledger is `DATA NEEDED` (FINDING §1). The arm must scope its overlay to the
  SoCalGas-served fleet and say so; applying an SP15 event to NP15 units
  because it helps is a fabricated input.

**Any deviation from this definition by the arm session must be justified in
writing from gas-system physics or tariff mechanics, and must be recorded
BEFORE the solve that tests it.** A definition changed after seeing a gate
result is a fitted parameter under rule 24 and voids the round.

## §3 — Posture: backcast vs forecast

**Backcast (2023–2025).** The overlay reads the committed `gas-ofo-events`
partition directly. This is rule-13 admissible as adjudicated in FINDING §4:
a published physical availability event, not a market outcome, in the same
class as the CAMPD outage windows the model already applies in backcast mode.

**Forecast.** The forward year holds no OFO ledger, so the overlay **cannot**
ship into the forecast lane reading this table. It needs the regeneration story
FINDING §4(d) names and deliberately leaves open (an OFO-day climatology, or an
OFO hazard conditioned on forward gas-system state). **Ordering, pre-registered
as gate D3:** the forecast analogue must be *specified and shown to regenerate*
before the backcast overlay is proposed for promotion to a keeper. A
backcast-only overlay with no forward analogue is a measured input that fails
rule 13's forward test, and under rule 13 it may exist **only** as an
explicitly-labelled, default-**off** diagnostic probe — never enabled in a
keeper, never quoted as forecast skill.

## §4 — Derive-first gates, in order. Each is a KILL, not a hurdle.

**D0 — coverage, measured but NOT used to choose.** With the §2 definition
frozen, measure how many of the keeper's measured tail hours fall on qualifying
gas days, per year, from the committed keeper sidecars (no solve). This is
reported as *evidence*, and the definition may **not** be revised in response
to it. If coverage is inadequate the arm dies here.

**D1 — the physical derate, identified independently of the residual.** Derive
the MW of SP15 gas capacity a low OFO actually curtails, from gas-system
quantities only (published sendout vs. capacity, the declared tolerance applied
to measured gas burn, storage/receipt constraints) — never from the MW needed
to move λ. **Kill criterion:** if the physically-identified derate is not
material against caiso-131 §5's 12.6–12.8 GW band, the arm **stops with no
solve** and reports that the deliverability story, though real, cannot reach
the tail — which is itself a publishable answer to caiso-131 A3.

**D2 — one mechanism (rule 19).** Enumerate what already limits the same fleet
on the same hours (CAMPD outage windows, availability, must-offer floors) and
**reconcile or replace** — never stack an OFO derate on top of an existing
limit's unexplained residual.

**D3 — the forward analogue (§3).** Specified, and shown to regenerate for a
forward year from forward drivers, before promotion is proposed.

**D4 — window (rule 17 `[R-FLOOR-WINDOW]`).** The overlay binds only on
qualifying gas days, with the SoCalGas 07:00–07:00 Pacific gas-day offset
applied to reach operating hours (the schema flags this; a midnight-to-midnight
mapping is a bug). A `D4_WINDOWS` entry is cited in
`scripts/legitimacy_diagnostics.py` in the same session.

## §5 — Pass / fail criteria, stated before any solve

Judged on **structural fidelity first** (rule 1): a faithful mechanism stays in
even if the residual does not move, and an unfaithful one is rejected even if
it does.

| # | criterion | PASS | FAIL |
|---|---|---|---|
| **G1** | **Structural fidelity** | the derate is identified at D1 from gas-system physics, with zero parameters tuned to any electricity-market residual (DOF ledger clean) | any value chosen because it moved a gate |
| **G2** | **2025 no-harm** — *the criterion this intake's own record forces* | C3a-2025, CAISO's **sole open gate**, does not degrade | C3a-2025 degrades |
| **G3** | **C3c direction, 2023/2024** | tail hours move toward the 24/18 requirement | reported honestly if not; a null is a null |
| **G4** | **Band discipline** | 2023/2024 stay inside the caiso-131 §1 headroom (+$3.67 / +$0.69) | exceeded |
| **G5** | **Rule 22 LOYO** | leave-one-year-out within 2023–2025 before any promotion | in-sample gain with held-out degradation ⇒ overfit, reject |
| **G6** | **Rule 20 `[R-FORCED-BUDGET]`** | no material class pushed over its forced-energy cap, or grounded on D-4 + D-1 | otherwise |

**G2 is the criterion caiso-226 discovered and the reason this precommit
exists.** caiso-131 §6 valued a gas trigger partly for being *inert in 2025 by
construction* — 2025's citygate never exceeds $5.61/MMBtu. **The OFO record has
no such property:** SoCalGas declared **25 low OFOs in 2025**, 9 in January
(FINDING §5). The §2 trigger therefore **fires in 2025**, the year whose C3c
already PASSES and whose C3a is the only thing keeping CAISO at NOT-YET. G2 is
consequently a **hard gate, not a courtesy check**, and the arm may not satisfy
it by adding a 2025 exclusion — that would be a year-keyed fitted term (rule 13)
and voids the round.

## §6 — Pre-registered outcomes, including the honest nulls

All four are acceptable results. Naming them now is what stops the arm from
needing a win:

1. **Dies at D1** — the physically-identified derate cannot reach the 12.6–12.8
   GW band. No solve. C3c stays ledgered; caiso-131 A3 is answered *negatively
   but conclusively*, which is worth more than an open ask.
2. **Dies at G2** — the mechanism is faithful but degrades C3a-2025. Rejected,
   cell marked `R` in the CAISO shard with the evidence citation.
3. **Passes G1/G2 and yields little on G3** — a structurally-correct mechanism
   with a small tail effect. Under rule 1 this is a **candidate on its merits**,
   judged as structure, not on whether the residual moved; C3c may stay
   ledgered regardless.
4. **Passes throughout** — full round with rule-16 all-years bundle, dashboard
   registration (rule 15), matrix row + cell (rule 26), DOF ledger (rule 24).
   Promotion is still a separate owner act.

**C3c stays the keeper's single ledgered caveat in every one of these
outcomes.** Under rubric v3.3 a lone ledgered C3c does not downgrade a
determination, so **this arm is root-cause work, never a gate need** — and it
must never be argued for as one.

## §7 — Standing prohibitions carried into the arm session

- Everything in caiso-131 §10 and caiso-226 FINDING §6.
- **The trigger definition (§2) is frozen ex ante.** Revising it after seeing a
  gate result voids the round.
- **No stage/tolerance/waived cut selected by yield** (§2).
- **No 2025 exclusion, no year-keyed term, no per-hour fitted magnitude** (§5).
- **No re-tuning the DMM caps; no re-running the caiso-225 watch sweep before
  its dated trigger** (Order-881 effective ≤ 2026-12-01, or the next DMM
  publication).
- Keeper, keeper shards, `calibration-complete.json`, `holdout-freeze.json` and
  every other ISO's files: **UNTOUCHED**. Solve/score reads stay 2023–2025.
