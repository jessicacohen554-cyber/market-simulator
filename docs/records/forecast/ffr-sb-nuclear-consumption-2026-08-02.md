# FFR-SB — How the FF-G5 nuclear license/SLR registry enters the exit path (design memo)

**Date:** 2026-08-03 · **Session:** FFR-SB [FABLE] · **Branch:**
`claude/ff-g5-nuclear-exit-design-ecgmie` · **Charter:** FR-18 / BLK-9 consumption design,
**MEMO ONLY** — no code, no solve, no default change, no dashboard registration, no
mechanism-matrix cell change (nothing is tested here; rule 28 duty (b) does not fire).
**Hard constraint honored throughout: NO second exit mechanism** (rule 19
`[R-ONE-MECH]`) — every candidate is graded on whether it composes with the existing
screen + registries or smuggles in a parallel exit path.

Predecessor: `docs/handoffs/ff-g5-nuclear-registry-2026-07.md` (the registry — 59 units,
loader `data/nuclear_license.py`, consumed by NOTHING in the solve path) and its §2 design
memo (DB-1…DB-6, unresolved). This memo re-derives the design **against the PIPELINE
retirement rule** (owner D-1, signed 2026-08-02,
`docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum C; executed by FFR-3A), which the
FF-G5 memo predates, and grades the three chartered candidates against rules 13
`[R-MEASURED]`, 19 `[R-ONE-MECH]`, 23 `[R-FROZEN-DERIVE]`.

## 1. Verified state this design must compose with

All verified against `origin/main` HEAD `5e934b8` (2026-08-03) unless cited otherwise.

1. **One exit path, three mechanisms** —
   `src/market_sim/model/capacity_evolution/retirements.py`: step 0
   `apply_confirmed_exits` (instrument-dated, any fuel, **bypasses the reliability
   floor**, the ONLY exogenous fossil channel), step 1 `apply_announced_retirements`
   (EIA-860 self-reported dates; fossil default no-op; non-fossil honored only within
   `vintage + NONFOSSIL_ANNOUNCED_HORIZON_YEARS` unless the plant is in
   `confirmed_plant_codes`; `reversed_plant_codes` supersession), step 3 the economic
   screen.
2. **The retirement rule is flipping legacy → pipeline** (owner D-1). The pipeline rule
   (`_apply_pipeline_retirements`, retirements.py:1181) replaces **only the step-3
   internals** — uniform decision bar, adequacy-capped joint entry, soft latch, measured
   per-fuel execution lags (`retirement_execution_lag_nuclear` among them). Steps 0 and 1
   are untouched by the flip. Pipeline state **prunes unit ids that left the fleet
   through another channel** (retirements.py:1250-1253: "confirmed exit, retrofit rename,
   re-aggregation — nothing to execute or reverse"), so an exit landed by step 0/1 while
   a unit is pipelined is already handled.
3. **BLK-9 status has moved since FF-G5.** The flat-payment arithmetic that inverted the
   screen onto nuclear (0.60×–0.82× FOM coverage, PJM hindcast false-retiring 4.1 GW,
   100 % false) is no longer the active default for PJM/MISO/CAISO/NEISO
   (`capacity_market_clearing` curve-ON, FF-2C 2026-07-20); **fixed-mode BLK-9 persists
   for NYISO only** (gap register §3.9). The successor pathology is the curve-ON
   over-retirement wave (BLK-10), which the pipeline rule measurably reduces (FFR-2B:
   PJM I6 12.68→8.55 %). Sequencing consequences in §7 / DB-D.
4. **The adequacy ledger accredits nameplate, not availability.** `_thermal_firm_mw`
   (retirements.py:987-995) is `pmax_mw × thermal_accreditation_fraction(...)`; no
   availability term exists anywhere in the accreditation chain, and
   `capacity_revenue_per_mw_yr` prices through the same single resolver (rule 19, one
   seam). This is the decisive code fact against candidate (a) (§4).
5. **FR-18** (`docs/forecast-readiness-audit-2026-07.md` §3.4): the confirmed-retirements
   registry horizon ends 2032, so 2033–2050 exits ride the economic screen alone; §3.3
   lists the FF-G5 registry as "consumed by nothing." This memo is the audit's Phase-5
   consumption design.
6. **Registry contents** (FF-G5 §1): 59 units; 11 `slr_granted_80` (expiries mostly past
   2050); 2 SLR under review; 2 announced intent; 2 on original licenses (Perry 2026,
   Clinton 2027 — initial renewals pending); 44 `renewed_60` with no SLR pathway yet
   (expiries 2032–2053); 2 restarts in progress; Diablo Canyon's exit lives in
   `confirmed-retirements` (SB 846), cross-referenced not duplicated.

## 2. The phenomenon, and the two legal facts that frame it

The licensed-life ceiling is the **latest date a unit may legally operate**, not a
decision to retire (FF-G5 §2.1, reaffirmed). Two NRC-law facts sharpen the grading below;
both are instrument-grounded and were not in the FF-G5 memo:

- **Renewal terms are a fixed 20-year statutory parameter.** 10 CFR 54.31(b): a renewed
  license issues for up to 20 years beyond the current expiry. The "80-yr" SLR ceiling is
  not a modeling estimate — it is `current_expiry + 20` under a published rule. This is
  what makes an assumed-SLR ceiling *derivable* rather than tuned (§6, parameter P2).
- **Timely renewal keeps an "expired" license alive.** 10 CFR 2.109(b): a renewal
  application filed ≥5 years before expiry keeps the existing license in effect until the
  NRC acts. So a bare expiry date with a pending renewal (Perry 2026, Clinton 2027; NMP1
  and Ginna's SLRs under review) is **legally not a shutdown date at all**. Any design
  that force-retires on the printed expiry while a renewal is pending misstates the
  instrument itself — the strongest single argument against candidate (b) as a broad
  channel (§5).

## 3. Field survey (research step): license horizon vs economic exit

All three major planning models treat a US nuclear unit's forward life as its
**license/age clock, exogenous**, with economics at most an accelerant — none lets an
economic screen be the primary determinant of nuclear lifetime:

- **EPA IPM (Post-IRA 2022 Reference Case):** existing nuclear has a **prespecified
  life and is no longer endogenously retired**; life-extension costs let units run over
  an extended **80-year** life (basis: Sargent & Lundy 2017). Sources:
  [EPA Platform v6 Post-IRA 2022 Reference Case](https://www.epa.gov/system/files/documents/2023-03/EPA%20Platform%20v6%20Post-IRA%202022%20Reference%20Case.pdf),
  [documentation page](https://www.epa.gov/power-sector-modeling/documentation-post-ira-2022-reference-case).
  This supersedes the FF-G5 methodology-doc §6 "verify at next intake" flag on IPM: the
  current reference case is *more* exogenous than FF-G5 assumed (prespecified life, not
  merely renewal-aware).
- **NREL ReEDS:** age-based nuclear retirement with scenario lifetimes 50–80 yr; the
  80-yr-lifetime case sees **no age-based nuclear retirements before 2050**
  (e.g. [NREL 2019 standard-scenarios report](https://docs.nrel.gov/docs/fy19osti/72217.pdf);
  ReEDS documentation). Decarbonization analyses default to 80 yr.
- **EIA AEO/EMM (NEMS):** broad life extension via the 40→60→80 ladder
  (FF-G5 methodology doc §6, unchanged).
- **NRC's own framing** of the 40→60→80 ladder:
  [license-renewal backgrounder](https://www.nrc.gov/reading-rm/doc-collections/fact-sheets/fs-reactor-license-renewal),
  [From 40 to 60 to 80 Years (ML22286A004)](https://www.nrc.gov/docs/ML2228/ML22286A004.pdf).

Consequence for the grading: ceiling semantics with an assume-SLR base case is the field
consensus, and IPM's "prespecified, not endogenously retired" posture is notable — this
model's economic screen retaining *accelerant* power over nuclear (via the pipeline rule)
is already **more** endogenous than IPM. Nothing in the survey supports treating a bare
license expiry as a confirmed-exit-grade decision.

## 4. Candidate (a) — license ceiling as an AVAILABILITY horizon: **NON-VIABLE**

**Design:** keep the unit in the fleet; zero (or floor) its `availability[g,t]` for solve
years past the resolved license ceiling, via the outage/availability layer.

**Grading:**

- **Rule 19 `[R-ONE-MECH]` — FAIL, and it is the hard constraint.** This *is* a second
  exit mechanism wearing outage clothing: it creates a "retired-but-present" terminal
  state that no other channel produces, adjudicated inside the availability model instead
  of the one exit path. Every downstream consumer then disagrees about whether the unit
  exists: dispatch says no, the fleet list says yes.
- **Structural corruption (rule 1):** the adequacy ledger accredits `pmax_mw` with **no
  availability term** (§1 fact 4), and the capacity payment prices through the same
  resolver. A license-dead unit would therefore (i) keep counting toward the PRM floor —
  phantom firm capacity suppressing the entry backstop and rescuing other units from the
  floor; (ii) keep earning capacity revenue in curve-ON ISOs; (iii) show zero energy
  margin, so the pipeline rule would *decide* it and re-exit it `lag` years after its
  legal death — a double-retirement of one unit by two mechanisms, the exact D-2
  attribution mess rule 19 exists to prevent. "Fixing" (i)–(iii) means teaching the
  accreditation chain, the floor, the payment, and the ledger about the new state — i.e.
  re-implementing retirement inside availability.
- **Rule 13 `[R-MEASURED]` — input admissible, representation not.** The license date
  itself passes the test, but a lapsed license is a legal prohibition, not a forced-outage
  process; encoding law as EFOR misstates the physics the availability model is
  identified on (and lands in the FR-7/FR-8 weather-year-keyed availability seam the
  audit already flags as fragile).
- **Rule 23 `[R-FROZEN-DERIVE]`** — moot given the above.
- **What it would re-open:** the entire accreditation/adequacy invariant set (I4/I7),
  outage-model identification, capacity-payment integrity.

**Verdict: out of scope by construction under the task's hard constraint — recorded here
so it is not re-proposed.** (No mechanism-matrix cell is written for it: nothing was
tested, and no ScenarioConfig field is being added. An implementer who ever revives it
owes the matrix row and this memo's rebuttal.)

## 5. Candidate (b) — a confirmed-exit-grade INSTRUMENT: **viable only as a narrow
sub-case that needs no new mechanism at all**

**Design:** map license expiries into `confirmed-retirements` rows so step 0 force-retires
them (floor-bypassing, any fuel).

**Grading, broad form (all 44 no-SLR-pathway units):**

- **Rule 13 — FAIL on semantics, not on regeneration.** The registry re-queries each
  vintage, and an SLR grant would update the row, so the *data* responds to changed
  conditions. What fails is the embedded outcome assumption: treating "no SLR filed yet"
  as "will never renew" contradicts the measured behaviour the registry itself documents
  (11/59 already SLR-granted, 4 in flight, ~0 actual retirements, 2 restarts) **and**
  contradicts the instrument's own law — under 10 CFR 2.109(b) a timely renewal means the
  printed expiry never binds (§2). A forced exit at the 60-yr date is a measured *date*
  carrying an unmeasured *decision*; the forward analogue (units overwhelmingly renew) is
  the opposite.
- **Rule 19 — FAIL on phenomenon identity.** The confirmed channel's phenomenon is "an
  enforceable instrument *decided* this unit's exit" — which is why it bypasses the
  reliability floor (a consent decree does not care about the model's reserve margin) and
  why its `confirmation_class` vocabulary (rto_deactivation / consent_decree / statute /
  regulatory_order / rmr_end) deliberately has no "license expiry" member
  (`confirmed-retirement-plan-2026-07.md` §4.1; FF-G5 §2.2(i)). A ceiling is not a
  decision; folding it in conflates two phenomena inside the one channel whose floor
  bypass makes mistakes irreversible.
- **Rule 23 — pass** (rows re-derive from source instruments only), but irrelevant given
  the two failures above.
- **What the broad form would re-open:** the closed `confirmation_class` vocabulary
  (schema change), the floor-bypass semantics, and the FFR-PA quarterly re-query burden
  (+44 rows whose supersession events — SLR filings — are exactly the high-frequency kind
  the cadence memo warns about).

**The narrow sub-case that IS correct — and already has a home:** when non-renewal itself
becomes instrumented — a licensee files a certification of permanent cessation
(10 CFR 50.82), publicly withdraws a renewal application with a stated shutdown date, or
a statute/order caps operation (Diablo Canyon, SB 846) — that *is* a confirmed-exit-grade
instrument, and it belongs in `confirmed-retirements` **under the existing channel and
(for statutes/orders) the existing vocabulary**. Diablo Canyon already demonstrates the
pattern; the registry's `confirmed_retirement_ref` column exists precisely for this
cross-reference. The only open question is vocabulary: whether a filed 50.82 certification
enters as `regulatory_order` or warrants a new closed-vocab member
(e.g. `cessation_certification`) — an owner call (DB-C), and a **schema/data question,
zero mechanism code either way**. Today this sub-case is empty (no operating unit in the
six ISOs has a live non-renewal instrument), so nothing blocks on it.

**Verdict: rejected as the base mechanism (reaffirming FF-G5 §2.2(i) with the 2.109(b)
strengthening); adopted as the standing rule for the instrumented-non-renewal sub-case,
which uses the existing channel as-is.**

## 6. Candidate (c) — an announced-retirement DATE source with ceiling semantics:
**RECOMMENDED**

**Design (the FF-G5 DB-1 synthesis, re-verified against the pipeline rule):** the
registry-resolved license ceiling **replaces the EIA-860 self-report as the nuclear
input to step 1** (`apply_announced_retirements`), with:

1. **Ceiling semantics by construction.** Step 1 drops a unit only when the simulation
   year reaches its date; the economic screen (pipeline rule) can still execute an exit
   earlier. Since step 1 and step 3 act independently and the earliest wins, the
   composition is `exit = min(pipeline_execution, license_ceiling)` with **zero new code
   paths** — the same shape as the confirmed channel's `min(economic, confirmed_date)`.
   No force-retire-before-ceiling, no floor bypass (a ceiling exit is a legal fact, but
   every ceiling in the registry is ≥2032 with the near ones renewal-pending, so the
   floor question never arises before DB-B's base case resolves it — see open question
   OQ-2).
2. **Horizon-gate lift for nuclear, justified by the instrument.** The
   `NONFOSSIL_ANNOUNCED_HORIZON_YEARS` gate exists because EIA-860 self-reports are
   speculative past ~vintage+5. An NRC license date is not speculative; the gate's
   *reason* does not apply. Mechanically this is the existing
   `confirmed_plant_codes`-style exemption generalized: the implementer passes the set of
   instrument-dated nuclear plants (or an equivalent per-unit ceiling map) so their dates
   are honored beyond the horizon — an input upgrade to an existing argument, not a new
   gate.
3. **SLR resolution before the date enters.** The consumed date is the *resolved
   ceiling*, not the raw expiry: `slr_granted_80` → expiry as printed (mostly >2050,
   i.e. outside the horizon — inert); pending renewals/SLRs under the base case (DB-B)
   → extended per 10 CFR 54.31(b)/2.109(b); `renewed_60` with no pathway → per DB-B.
4. **Restarts and uprates stay where FF-G5 put them** (planned-additions channel;
   deferred reverse-derate) — out of this memo's exit-path scope, unchanged (DB-3/DB-4
   of FF-G5).

**Grading:**

- **Rule 13 `[R-MEASURED]` — PASS.** The admissibility test both ways: the ceiling
  regenerates for a forward year by re-querying the same NRC pages at each intake vintage
  (fetch script + sha256-pinned snapshots already exist), and it responds to changed
  conditions — an SLR grant, a timely renewal filing, or a new cessation certification
  moves the resolved ceiling at the next vintage, exactly as the confirmed registry's
  counter-instruments do. Nothing is pinned to an outcome; no residual can reach it.
- **Rule 19 `[R-ONE-MECH]` — PASS, and it is the only candidate that adds zero
  mechanisms.** Step 1 already *is* "the one place a dated, non-economic, non-fossil
  retirement lives." This design upgrades that step's nuclear input (a better-grounded
  date) and its gate rationale — no new step, no new floor, no new state. The pipeline
  flip does not disturb this: D-1 replaced step-3 internals only, and pipeline state
  already prunes a unit that step 1 removed (§1 fact 2), so even a
  pipelined-then-ceiling-expired unit resolves cleanly with no code change.
- **Rule 23 `[R-FROZEN-DERIVE]` — PASS.** Every parameter re-derives only from source
  instruments (below); a nuclear-retirement residual moving is *never* grounds to touch
  the resolution rule, the base case, or any row (FF-G5 §2.5's rule-1/11 guard, carried
  forward verbatim).

**Parameter identification (the complete DOF list — nothing else is free):**

| # | Parameter | Identification | Regenerates from |
|---|---|---|---|
| P1 | Per-unit ceiling date | The unit's NRC license expiry, primary citation per registry row | NRC pages re-query at each intake vintage |
| P2 | SLR/renewal extension term (+20 yr) | 10 CFR 54.31(b) (renewal term), with 2.109(b) timely-renewal continuation | Statute — fixed unless the CFR changes |
| P3 | Base-case SLR assumption (`assume` vs `none`) | Scenario knob (DB-B), identified from measured renewal behaviour (11/59 granted, ~0 retirements) + field consensus (§3); **never residual-tuned** | Owner decision; per-unit registry override |
| P4 | Date→exit-year convention | Mirror `_confirmed_effective_year` (month ≤6 → year, else year+1) — the annual-grain convention both existing channels share | Fixed convention |

**Config surface (rule 24):** two ScenarioConfig fields as FF-G5 DB-6 proposed —
`nuclear_license_ceiling_enabled` (default **off**) + `nuclear_slr_base_case` — and
nothing else. **Rule 28 note: this memo proposes but does not add these fields; the
implementing session owes the mechanism-matrix row in the same PR that adds them**
(CI enforces the ScenarioConfig half). Arming the default later is a cache-key /
cache-epoch event (audit §3.2 precondition) owned by the arming session.

**What it re-opens (honestly):**

- The fleet-loader/step-1 seam for how the per-unit ceiling reaches
  `apply_announced_retirements` (a ceiling map argument vs overriding
  `Generator.retirement_year` for nuclear at fleet build) — implementer's choice; either
  stays inside the one mechanism. The known `bins_to_fleet`-drops-dates finding
  (confirmed-retirement plan §3) is latent-only here (nuclear is never binned), but the
  implementer should assert it in a test.
- DB-B itself (§8) — the one genuinely open modeling decision.
- Nothing else: no schema change, no vocabulary change, no floor semantics, no
  accreditation change.

## 7. Sequencing vs BLK-9/BLK-10 (updates FF-G5 §2.5/DB-5 to the current state)

FF-G5's warning — the ceiling is necessary-not-sufficient and must never mask the
economic screen's nuclear pathology — **stands, with its factual basis updated**: the
flat-payment inversion is now confined to NYISO (curve-ON elsewhere), and the pipeline
rule measurably reduces the successor over-retirement wave (FFR-2B). The residual risks
the ceiling must not paper over are (i) NYISO's fixed-mode BLK-9 arithmetic, and (ii) any
remaining curve-ON over-retirement touching nuclear after FFR-3A lands. Consequence:
implement default-off any time after FFR-3A merges; **arm only after a post-flip
evidence check shows the pipeline rule is not false-retiring nuclear** (a T1-F probe
reading the pipeline event ledger's nuclear rows — decided/executed/reversed — against
the registry; no new instrument needed, the ledger already attributes per unit). If
nuclear still false-retires, the fix is the screen/accreditation chain, never the
ceiling, a haircut, or the base case (rules 1/11/13).

## 8. Owner-decision box

> **DB-A — Primary design.** Adopt candidate (c): the registry-resolved license ceiling
> enters as the nuclear DATE source for `apply_announced_retirements` (replacing the
> EIA-860 self-report), horizon gate lifted for instrument-dated nuclear, ceiling
> semantics (`min(pipeline_execution, license_ceiling)`), zero new mechanisms.
> Candidate (a) is rejected as a second exit mechanism corrupting the adequacy ledger
> (§4); candidate (b) broad form is rejected on 10 CFR 2.109(b) + phenomenon-identity
> grounds (§5). **Recommended: adopt (c). This confirms FF-G5 DB-1, now re-verified
> against the pipeline rule.**

> **DB-B — Base-case SLR/renewal assumption** (carries FF-G5 DB-2, extended to initial
> renewals). For a unit whose resolved ceiling falls in-horizon with
> `slr_status ∈ {none, under_review, announced_intent}` — and for the two
> original-license units with renewals pending (Perry, Clinton) — does the base case
> assume renewal (+20 yr per 10 CFR 54.31(b)) or honor the printed expiry?
> **Recommended: assume-renewal default** (field consensus §3; measured behaviour;
> 2.109(b) makes pending-renewal expiries legally non-binding anyway), per-unit
> overridable, with retire-at-printed-expiry as the downside scenario. A scenario knob,
> never a tuned value.

> **DB-C — Instrumented non-renewal vocabulary** (narrow candidate-(b) sub-case, §5).
> When a licensee files permanent cessation (10 CFR 50.82) or withdraws a renewal with a
> shutdown date, the row goes in `confirmed-retirements`. Enter it under the existing
> `regulatory_order` class, or add a closed-vocab member (`cessation_certification`)?
> **Recommended: decide only when the first such row exists (today: zero candidates);
> default to reusing `regulatory_order` to avoid a schema bump.** Data/schema question
> only — no mechanism code either way.

> **DB-D — Sequencing and arming** (updates FF-G5 DB-5). Implement default-off after
> FFR-3A lands; arm only after a post-flip nuclear-false-retire check on the pipeline
> event ledger (§7), with the cache-epoch bump on arming. NYISO's fixed-mode BLK-9
> remains a standing caveat until its curve flip or successor fix.
> **Recommended: confirm this ordering.**

> **DB-E — Chartering.** The implementing session (Opus/Fable — core infrastructure,
> rule 27) is chartered from DB-A…DB-D once signed: seam wiring, the two ScenarioConfig
> fields + mechanism-matrix row (same PR, rule 28), tests (ceiling exit at resolved
> date; SLR extension; pipeline executes earlier when economics say so; pipelined unit
> pruned on ceiling exit; default-off byte-identity; nuclear-never-binned assertion),
> and leave-one-year-out scoring for any verdict-flipping change (rule 22).

## 9. Open questions (sourced-claim gaps, not assumptions)

- **OQ-1 — IPM life-extension cost treatment.** IPM attaches life-extension *costs* to
  the 80-yr life (S&L 2017). This model's analogue would be a nuclear FOM step at the
  SLR boundary — not designed here, not required for the exit path, and any such value
  must come from a published basis (rule 5/13), never a residual. Flagged for the
  implementer as explicitly out of scope.
- **OQ-2 — Floor interaction at a ceiling exit.** A step-1 exit does not bypass the
  reliability floor the way step 0 does — but step 1 exits are unconditional drops (the
  floor only guards step 3), so in code the ceiling *does* bind regardless of adequacy.
  That is the legally correct behaviour; stated here so nobody reads the "no floor
  bypass" contrast in §6 as meaning the floor can rescue a license-dead unit. Verified
  against `apply_announced_retirements` (unconditional drop) — no change needed.
- **OQ-3 — Registry staleness cadence.** The nuclear registry has no re-query cadence
  analogous to FFR-PA's proposed quarterly confirmed-retirements pass. SLR grants move
  ceilings by 20 years; adopting the same (still owner-pending) cadence for this
  registry is a natural rider on that decision.
