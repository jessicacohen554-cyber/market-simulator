# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization Program) track.
Maintained by the director session on branch `claude/capx-director-ledger`; one refresh = one
commit when anything changes. The director charters sessions and tracks state — it never runs
solves, never edits `src/market_sim/`, and never charters backcast-calibration work (that track
is the owner's own CAISO/ERCOT/MISO sessions, watched here for deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-08-30 (refresh #9) ·
**HEAD at refresh:** `a53b7b3` · **Owner cards A/B/C SIGNED 2026-08-25; Q5/Q6/signal/S-123 RULED at the r#8 sitting** (§3)
**Handoff prompt for a successor director session:** `docs/handoffs/capx-director-handoff-2026-08-26.md`

---

## 0f. Refresh #9 (2026-08-30, HEAD `a53b7b3`) — freeze goes TIER-SCOPED (card 6 executed); rubric v3.5 determination-neutral; still no capx lane started

**1. THE HOLDOUT SPEND FREEZE IS NOW TIER-SCOPED** (owner ruling 2026-08-26 card 6, executed
2026-08-30, `0589b6f`; record `docs/FINDING-holdout-governance-2026-08-26.md`): `active: true`
with `scope.tiers = ["locked_test"]` — the VALIDATION tier (2020–2022) is lifted from the freeze
and governed by the `complete` marker + `--holdout-authorized` alone, so the diagnostic
touchpoint loop is actually runnable for {NEISO, NYISO, PJM}; the locked test (2019/H1-2026)
stays frozen for every ISO and `final` stays EMPTY. Card 7 (`3643318`) added the standing
scheduling precondition to rule 22: an ISO is *eligible to be considered* for `final` only after
its 2020–2022 touchpoints have run and the loop has stopped surfacing repairs — eligibility is
never a grant. The CAMPD economic-layup charter is CLOSED WITH CAUSE in the same ruling (the
detector question stays open as a documented seam every keeper's availability envelope inherits).
**Director consequence: every pack prompt's freeze guardrail is updated to the tier-scoped
phrasing this refresh** — a capx lane touches neither tier, but this track does not quote stale
governance state. **Nothing else changes for capx lanes**: forecast-mode 2026+ stays
unrestricted, and no capx lane ever solves an out-of-training backcast year.

**2. RUBRIC v3.5 RESOLVED THE STANDING WATCH ITEM HARMLESSLY.** The xiso-6 diurnal
price-amplitude decision card (watched since r#6 as "could touch six determinations") was ruled
option (B): amplitude added REPORTED-ONLY and BAND-FREE — measured, published, no status, no
budget — and **re-verified determination-neutral over the 2026-08-30 six-keeper roster**
(`rule-history.md` changes table, 2026-08-30). Watch item CLOSED.

**3. BACKCAST MOVEMENT:** CAISO keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (the caiso-200
recipe replayed on the now-ACTIVE measured membership crosswalk — caiso-200 no longer reproduces
at HEAD; promoted by owner act on the pre-registered rule; CAISO holds no marker, no re-key due).
**miso-190 is in flight** (branch open: the partial-plant mid-window exit carry, miso-188's
named-not-built successor; PREREG frozen before the mechanism exists — the lane keeps validating
the S-123 hold). NYISO Leg-1 (eastern-seam PAR attribution) branch still open, nyiso-157 A/B
gate scorer filed before its solves. ERCOT: the O7 P0-seam Phase-0 landed ("restoration
escalates, exposure is inherent") plus two governance rulings (G-SPUR lidless count; the ≥$1,000
band-count 59 → 61 correction) — no ERCOT branch currently open. Forecast namespace:
**byte-unchanged**; board still NYISO (a) PASS · (b) PASS · (c) fail · (d) none, all others HOLD.

**4. CAPX LANES: none started** (no `capx-*` branch at `a53b7b3`). The r#8 batch stands: D10 +
D11-R + S-4 to dispatch (all light). S-5 ready — its heavy re-score self-gates on a free slot,
so it is safe to start as a fourth session any time. **S-123: the owner's hold-until-r#9 expired
and the r#9 start-time check FAILS** (miso-190 in flight) — it stays held on the check itself,
re-run every refresh; no new owner decision needed.

## 0e. Refresh #8 (2026-08-30) — no capx lane started; NYISO winter intake AUTHORIZED (backcast track); D11 RE-SCOPED to the D-1 volume rule

**1. NONE OF THE FIVE STANDING PROMPTS HAS BEEN STARTED.** `git ls-remote` at `d8d08ac`: no
`capx-*` branch exists. D10, D11, S-123, S-4 and S-5 all stand written in the pack. The board,
verdicts, markers and freeze are unchanged from refresh #7: NYISO (a) PASS · (b) PASS ·
(c) fail · (d) none, everyone else HOLD on FC-1; `complete` = {NEISO, NYISO, PJM}; `final` EMPTY;
holdout spend freeze ACTIVE. (Keepers: MISO moved mid-refresh — item 4.)

**2. BACKCAST MOVEMENT — nyiso-156b: the owner RULED the nyiso-156 card's Q1 as OPTION A, the
winter locational identification intake is AUTHORIZED** (PR #4295, `ab0513e`; spec
`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`). Two legs: **Leg 1** — the
eastern-seam PAR attribution from NYISO's own published NY-NJ PAR interchange percentages
(**session-executable, the owner gate on PREREG-nyiso126 is LIFTED**; adds an ABC→NYC AC border
path the model does not carry); **Leg 2** — MyNYISO as-enforced AORR access (owner-executable,
fail-closed). The ruling also corrected the stale "seam unidentifiable" record: nyiso-125's
refusal was discharged on identification by nyiso-126 the same day; the leg was
authorization-blocked, not identification-blocked. **Why this track cares — it bears directly on
Q5**: the card's §4 measures that closing the winter face alone (−$3.92/MWh of the annual lw mean)
returns C3a-2025 to ≈ −5.3 % (in band), whereupon C3c reverts to the lone failure, the standing
rule reclassifies it, and the determination returns **CALIBRATED**. Q5's tension (a `complete`
marker on a NOT-YET keeper) now has a live structural resolution path through the owner's own
backcast lane; the precedent-reconciliation question stays worth writing regardless (§3).
Also landed: the bench-fingerprint adjudication (PR #4293 — 11 "stale" bench parts adjudicated
UNLABELLED-not-wrong, measured over the complete builder-drift commit set; backcast dashboard
hygiene, no gate contact).

**3. D11 IS RE-SCOPED TO D11-R — THE D-1 BANG-BANG VOLUME RULE — and the pro-forma signal build
is HELD IN ABEYANCE.** Recorded under the remit refresh #7 claimed (the B-C signature chartered
the OBJECT — what the entry screen is meant to represent — not a particular lane). The evidence
that forces it: `FINDING-entry-signal-forward-expectation-2026-08-25.md` §3 — three signal
constructions spanning a ~$200/MWh swing in the entering-2024 mean produce one trajectory
(terminal RM 25.19 / 40.24 / 40.38 %), *"D-1 owns the trajectory; the signal lane should not be
re-chartered against it"* — and its §7 adjudication recommends exactly this: **"(b) first — rest
the signal lane and charter D-1's volume rule."** The construction is already named and
pre-measured: L-1b's **margin-exhaustion closure** (`FINDING-entry-signal-l1-2026-08.md` §2,
probe `scripts/probes/entry_signal_l1b_allocator_counterfactual.py`) — *build until the screen's
own repriced margin is exhausted, bounded by the same caps* — is the zero-DOF candidate, measured
offline at terminal RM 18.7 % vs the shipped 25.2 % with the B-2 cobweb surviving (real market
dynamics, NOT the target). D11-R productionizes it behind a NEW default-OFF ScenarioConfig field
and A/Bs it on an ERCOT T1-F leg. Margin exhaustion **is** the allocator half of the developer
pro-forma, so this stays inside the B-C charter. The signal-lane successor rung — the
scarcity-consistent delta basis, §4's named successor for the two-scarcity-objects defect — is
**queued as D12**, to run only if the owner continues the signal lane; the owner can override
either disposition at the finding's §7 escalation, which remains open.

**4. DECONFLICTION — THREE BACKCAST BRANCHES WERE IN FLIGHT** at `d8d08ac`
(`claude/caiso-c3a-overrun-closure-5n84mn`, `claude/ercot-backcast-calibration-9wkxrg`,
`claude/miso-188-rubric-failure-tuning-m1ph17`) — **and the MISO one MERGED MID-REFRESH**
(`212308b`, PR #4296): **miso-188 promoted a new MISO keeper, `2026-08-30-miso-188-rvsscope`**
(full-span, single delta `retiree_vintage_status_scope=true` — a NEW gated default-off field with
its rule-28c matrix row + cells minted; drops 28 dark retiree-channel units / 1,434 MW after the
phase-0 audit caught Grand Tower dispatching 4.8 TWh while CAMPD-dark for three years;
**C1 CC_REGULAR-2024 +8.037 → +6.820 PASS; determination narrows to NOT-YET on {C3a-2025}
ALONE**, promoted on the PREREG's own rule). Consequences: CAISO and ERCOT branches remain in
flight, so the ≤2-heavy cap must still be checked before any capx solve launches and D11-R's
deconfliction note stays sharp (ERCOT backcast live). **S-123's hold is DOWNGRADED to a
start-time check**: the MISO backcast lane is momentarily between sessions, so S-123 may start
whenever no new MISO backcast branch is in flight, its optional re-measure still gated on a free
heavy slot (MISO = 9.6 GB no-co-run). The batch issued this refresh stays deliberately all-light:
**D10** (NYISO T1-X, 2.82 GB), **D11-R** (Phase-0 zero-solve first), **S-4** (NEISO, 9.2 min).
S-5 stands ready (PJM quiet on the backcast side) for the next free heavy slot; S-6 strictly
after it.

**5. OWNER SITTING AT REFRESH #8 (2026-08-30, in-session decision cards) — FOUR RULINGS:**
- **Q5 → WAIT FOR WINTER INTAKE.** The precedent conflict (CAISO withdrawal vs nyiso-155
  structural-integrity promotion) is left standing unreconciled; the nyiso-156 winter-intake path
  is the designated resolution route (measured: winter-face closure alone returns the keeper to
  CALIBRATED). No marker moves; gate (a) stays PASS on the literal test. If the fact pattern
  recurs before the intake resolves it, the reconciliation question returns to the owner.
- **Q6 → HOLD, NO ACTION.** No direction is issued to the ERCOT backcast lane; revisit when it
  goes quiet. Gate (a) keeps failing on both counts meanwhile — recorded, not escalated further.
- **SIGNAL LANE → D11-R RATIFIED, D12 QUEUED.** The refresh-#8 re-scope is ratified at the
  finding's §7 escalation: volume rule first; D12 (scarcity-consistent delta basis) is chartered
  only after D11-R reports. The §7 escalation is now RESOLVED — (b) first, (a) queued behind it.
- **S-123 → HOLD UNTIL NEXT REFRESH.** This SUPERSEDES item 4's mid-refresh downgrade to a
  start-time check: the owner holds S-123 one more cycle to see whether a new MISO backcast
  session starts. Re-present at r#9.

**5b. POST-SITTING BURST (same day, `212308b` → `5ce92f4`) — two rulings validated within the
hour:** PR #4298 merged this ledger's refresh-#8 commit; PR #4297 merged the CAISO backcast
branch (caiso-220 records — CAISO no longer in flight); **PR #4299 merged miso-189** (phase-0
zero-solve refuting the Illinois scarce delivered-gas candidate) — a NEW MISO backcast session
did start immediately, exactly what the S-123 hold-until-r#9 ruling anticipated; PR #4301 landed
an ERCOT governance correction (≥$1,000 band count 59 → 61, owner ruling 2026-08-26); and
**PR #4300 shows nyiso-156 LEG 1 (the eastern-seam PAR attribution) ALREADY EXECUTING** —
nyiso-157 filed its A/B gate scorer (K1–K9) before the solves — so the Q5 wait-for-winter-intake
path is in motion, not hypothetical. ERCOT's backcast branch remains the one still in flight
alongside the NYISO Leg-1 branch.

**6. PACK CORRECTIONS with the reissue:** D10's WHY cited keeper
`2026-08-22-nyiso-152-duty-complete, CALIBRATED` — stale since the nyiso-155 promotion; now cites
the NOT-YET keeper with the Q5 posture stated (gate (a) taken as PASS on the literal test, not
re-read downward). Its guardrail "CALIBRATED with an owner-ratified frontier" likewise corrected
(frontier returned to the owner at the promotion). D7's row moves to LANDED (`ca8b749`, PR #4289
— was recorded in §0d but the scoreboard row still read ISSUED).

## 0d. Refresh #7 (2026-08-26) — D7 LANDED; ERCOT is CALIBRATED but 2023-ONLY; D11's premise is undercut

**1. D7 LANDED** (PR #4289, `ca8b749`) — the first dispatched capx lane to complete. Records-only,
two files, no solve. It carried the NYISO re-score onto the board **with the source finding's own
honesty note attached** (the 2026 leg was also flipped by −341.4 MW of epoch demand drift and would
have passed by a thin +332.9 MW without the intake, so the 2,749.9 MW credit buys structural margin,
not the sign), applied the signed card-A leg-(c) harmonisation, and carried the base-year I7
scoring instruction into the board's prose. **It re-read NYISO's four legs against the criteria
rather than asserting them** — including verifying full-span at the keeper's registry years — and
**recorded the Q5 tension while leaving the verdict unmoved**, exactly as chartered.
**NYISO's board gate now reads (a) PASS · (b) PASS · (c) fail · (d) none, `open: false`. No gate
opened; leg (d) is byte-unchanged for all six ISOs.**

**2. ERCOT IS NOW `CALIBRATED` — AND ITS KEEPER IS 2023-ONLY.** Keeper
`2026-08-25-236-swcap-clip-k33` (−7.3 % / 0.102 / 180) scores **CALIBRATED with an EMPTY failing
set** — the 2023 price object that card Y held open on 2026-08-24 has closed. But
`registry/2026-08-25-236-swcap-clip-k33.json` declares **`years: [2023]`**.
→ **Gate (a) now fails for ERCOT on TWO independent counts**: it is absent from `complete`, *and*
§2.1b(2)(a) requires a **FULL-SPAN** keeper (rule 16), which a 2023-only run is not. **This is the
note from refresh #6 becoming load-bearing.** A CALIBRATED determination is necessary but not
sufficient: **declaring ERCOT `complete` would NOT open its gate (a) while the designated keeper
covers one year.** ERCOT would need a full-span (2023–2025) keeper carrying the swcap-clip recipe
first. That is an owner-tier sequencing point, not a director action — **Q6**.

**3. D11's PREMISE IS SUBSTANTIALLY UNDERCUT by a lane I did not charter.** The ERCOT
`entry_forward_expectation_signal` A/B (`94463db`) built and measured a **THIRD** entry-signal
construction. Its result: P1 CONFIRMED (iron_air 3,000 MW enters all four steps), P2 CONFIRMED
(wind 1,092.2 MW enters), but **P3 OVERSHOOT SURVIVES — terminal RM 40.38 % vs disarm 40.24 % vs
control 25.19 %** — and its adjudication is the finding that matters:
**"the trajectory is invariant across all three measured signal constructions and D-1's bang-bang
volume rule owns it."** It also surfaced an unpredicted measured defect: *S_current's pro-forma tail
and the duals' realized overlay are two different scarcity objects*, making the entering-2024
composed level unphysical (mean −$48.22/MWh; solar capture −$185/MWh). Cell stays `O`;
owner decides the next rung.
→ **D11 as chartered would build a FOURTH signal construction against evidence that the signal is
not what owns the outcome.** Its Phase 0 must now absorb this: either re-point at **D-1's bang-bang
volume rule** (the thing measured to own the trajectory) or justify in writing why a pro-forma
construction still earns a session. The B-C signature chartered *the object*, not a particular
lane; re-scoping it on new measured evidence is within the director's remit and is recorded here.
**The "two scarcity objects" defect is itself a strong candidate lane** — it is a physical-coherence
problem in the entry screen's own inputs, not a signal-shape question.

**4. Also landed:** `audit_keepers` gained **check E11 — keeper-lineage recipe fidelity over the
full `solve_and_persist` kwarg surface**, which closes the "silently lost from the keeper lineage"
class that the nyiso-155 hydro repair was a victim of. MISO keeper re-keyed to
`2026-08-26-miso-187-nucavail` (NOT-YET, fuelmix + price_mean; `nuclear_unit_availability` U→K).
CAISO's caiso-220 replay is mid-solve (checkpoints only). ercot-237 Phase-0 band-swap
characterization is zero-solve.

---

## 0c. Refresh #6 — no lane started; three keeper promotions, and NYISO's gate-(a) BASIS moved under us

**1. NONE OF THE SIX PROMPTS HAS BEEN STARTED.** `git ls-remote` at `6af12ee`: no `capx-*` branch
exists except this ledger. D7, D10, D11, S-123, S-4 and S-5 all stand as written
(`docs/handoffs/capx-director-prompt-pack-2026-08.md`); the only thing that moved under them is
`main` (`99c8cf5` → `6af12ee`), which every prompt already handles by fetching fresh.

**2. NYISO'S KEEPER IS NOW NOT-YET, AND IT STILL HOLDS `complete`.** Promoted 2026-08-25:
**`2026-08-25-nyiso-155-hydro-repair`** (the hydro truncated-vintage repair pair
`hydro_backfill_year=2024` + `hydro_eia930_monthly=true`, zero fitted scalars), **NOT-YET on
price_mean + price_tail**. Promoted BY OWNER RULING on structural integrity over gate regression,
with **the D-5(b) worse-determination stop FIRED, ESCALATED, and resolved by that ruling**; the
determination is written explicitly into the marker (nyiso-120 precedent). C3a-2025 −8.1 → −10.8 %
because the truncation had been **masking ~2.7 pp of the real 2025 offer-level object**. **Frontier
status returned to the owner** — the 2026-08-23 ratification's CALIBRATED premise no longer holds.

→ **This moves the BASIS under my refresh-#5 headline, and I state it plainly rather than let it
stand.** Gate (a)'s literal test (charter §2.1b(2)(a)) is *a designated full-span keeper AND an
entry in the `complete` block*, and NYISO still satisfies both, so **gate (a) reads pass on the
test as written**. But the marker now rests on a NOT-YET keeper — **precisely the fact pattern that
withdrew CAISO's marker on 2026-08-06** ("a `complete` marker cannot stand on a NOT-YET keeper").
The two are reconciled only by the owner's explicit ruling. **That is an owner-tier question, not
mine: it is Q5.** Leg (b) is untouched — it is the forecast `nyiso-t1f` verdict
(PROMOTE-WITH-CAVEATS), which no backcast promotion can move.

**3. THE HYDRO TRUNCATION DOES NOT REACH OUR I7 PASS — verified, not assumed.** The backcast repair
fixes a 2025 hydro census truncated to **3 plants of ~147**. The forecast accreditation was already
immune by construction: `modelled_hydro_nameplate_mw` clamps the census to
`EIA923_LATEST_FINAL_VINTAGE`, and its docstring names this exact hazard — *"vintages after it are
monthly early releases carrying only the large reporters … so an unclamped year would accredit a
partial fleet."* So NYISO's forecast hydro credit (1,763.3 MW) was never computed on the 3-plant
vintage, and the extcap I7 PASS stands. **Also verified: the NYISO extcap registry entry survives
intact** at `capacity_market.py:2574` (`3_168.5 * (1.0 - 0.1321)`); the only change to that file
this cycle was CAISO's AS-revenue row.
**A consistency item for D7/D10, flagged not resolved:** the backcast now consumes the *repaired*
hydro input (147 plants, EIA-930 monthly pin) while the forecast consumes the *clamped complete
census*. Two constructions of one physical quantity. Not a defect I have established — a question
worth one paragraph in the next NYISO lane.

**4. ERCOT's keeper is now 2023-ONLY** — `2026-08-25-235-2023-discrete-k24`, NOT-YET on price_mean
(C3a-2023) alone, and **the first ERCOT run with C3b-2023 AND C3c-2023 both PASS**. It is registered
under the **rule-16 waiver the owner granted 2026-08-23, now SPENT**. No gate reading changes
(ERCOT fails gate (a) on the marker regardless) — but note for any future ERCOT declaration that
gate (a) also requires a **full-span** keeper, which a 2023-only keeper is not.

---

## 0. Refresh #5 — NYISO CLEARS FC-1. The program has its first ISO with legs (a) and (b) both passing.

**1. D2-NYISO-INTAKE LANDED and it worked** (PR #4259). NYISO added to
`ADEQUACY_EXTERNAL_TIE_FIRM_MW` on its **own published** external capacity — 2026 Gold Book
Table V-1, Summer-2026 net capacity purchases from external control areas, **3,168.5 MW ICAP,
sha-verified source** — converted to the model's UCAP requirement basis with the **same published
NYCA ICAP→UCAP factor the requirement side applies** (rule 19, one basis): 3,168.5 × (1 − 0.1321)
= **2,749.9 MW**. Corroborated against NYISO 2025 SOM Fig. A-97. Deliberately NOT the 900 MW HQ
dispatch floor, NOT the 4,350 MW Simultaneous Import Limit.
**The pre-declared honesty test passed: the value overshoots the 35.7 MW residual ~77×** — a real
accreditation, not a number tuned to the invariant.
**Re-scored leg `nyiso-2026-2030-extcap-capxd2`: 5/5 years, 14/14 invariants PASS.
FC-1 FAIL['I7'] → PASS. FC-2 CAVEAT → PASS. Determination HOLD → PROMOTE-WITH-CAVEATS.**
The 2026 accredited firm reproduced the pre-solve prediction to the digit (32,085.5 + 2,749.9 =
34,835.4 MW). Honest decomposition disclosed in the finding: HEAD demand drift since the FFR-3A-2
epoch (−341.4 MW peak) alone would have passed 2026 by a thin +333 MW; **the intake moves every
year to a structural +2.9–4.2 GW surplus.** Only remaining caveat is FC-7 — the program-wide
missing DOF-ledger instrument (lane D8).

**2. NYISO's §2.1b gate now reads (a) PASS · (b) PASS · (c) `fail` · (d) none.** *(Leg (c) was
`na` at refresh time; the owner's card-A signature harmonised it to `fail` — §3.)*
`frontend/data/forecast/program-status.json` was last touched 2026-08-24 05:55 and still carries
NYISO as FC-1 FAIL / gate (b) fail. **This is the D7 trigger, and it is immediate.** NYISO is the
first ISO in the program to clear both legs that depend on model quality; what remains is leg (c),
now chartered as a run (**D10**), and leg (d), owner authorization.

**3. D2-B LANDED** (PR #4258) and is the most substantial diagnosis this track has produced.
Three of four legs reproduced from committed artifacts with no solve — MISO 2026 and CAISO
2026–2030 **to the MW**, NEISO to the verdict's own rounding. Headlines:

- **MISO IS THE SECOND NYISO.** It credits **zero** external firm capacity while the forecast path
  floors a **1,400 MW Manitoba firm-hydro block at 100 % in every hour, default-on**. The registry
  now omits **exactly the two ISOs** that fail I7 with a default-on firm-import floor behind the
  miss. The registry's failure mode is **coverage, not basis** — every populated entry is
  accreditation-based and consistent with dispatch.
- **A second MISO defect, provable from the repo's own citation blocks:** the fallback requirement
  multiplies the **PY 2024-25** ICAP PRM (0.179) by the **PY 2025-26** ICAP→UCAP ratio, and that
  ratio's own cited source publishes ICAP 15.7 % / UCAP 7.9 % — contradicting the PRM it is
  multiplied with. Same-document PY 2025-26 pairing puts the requirement **2,637.4 MW lower = 44 %
  of MISO's 6,037 MW gap.** Correctly NOT shipped (solve-affecting, shares machinery with the
  backcast-reachable retirement floor), and routed with its expected effect stated in advance so it
  cannot be back-fitted.
- **NEISO's hydro fallback is load-bearing and decides the verdict's sign.** The generic
  `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50` (no ISO-published NEISO factor exists — an FFR-1C
  open item) contributes **949.75 MW against a 218 MW gap — 4.4×**. A class factor of 0.39 flips
  2027 to FAIL; 0.62 clears 2028 outright. **NEISO 2028 is not decidable at current input
  fidelity** and must be read as "within input uncertainty", not as a capacity-evolution defect.
- **PJM's 366 MW is an UNDERSTATEMENT, and my "PJM is the shortest path to T2" thesis is REFUTED.**
  The requirement factor falls **discontinuously at the published-FPR table edge** (2028→2029):
  beyond delivery year 2028/29 the model falls back to a composite whose IRM half is two vintages
  stale, dropping the bar **3.18 % of peak = 5,492 MW** at the 2030 peak. Against a hold-last-FPR
  requirement — the convention `forward_net_cone_anchor` already establishes elsewhere — 2030's miss
  is **~5.9 GW, not 366 MW, and 2029 plausibly fails too.** Every correction on both sides runs
  against leniency. PJM's supply side is **the one leg no committed artifact can reproduce.**
  *(Owner signed C-A 2026-08-25: hold-last-FPR is now the declared convention — §3.)*
- **CAISO's forks were already adjudicated by FFR-3P** and stand: fork 2 (fleet-snapshot vintage)
  dominates — base-year battery fleet 8,000 MW against a published **14,131 MW NDC**, ≥5,933 MW =
  **90 % of the base-year deficit**. D2-B adds the horizon evidence: the **14,043.6 MW
  administrative-CT backstop ladder and the 65.5 % backstop share are DOWNSTREAM artifacts of the
  input-vintage deficit, not independent defects.** Fix B-1 and most of the ladder never fires.
- **Program-wide:** no base-year I7 leg is a capacity-evolution defect, and neither backstop tuning
  nor floor relaxation is ever the answer to one. Carried into D7 as a scoring instruction.

**4. Method note worth carrying:** an evolution ledger's exits live in **two keys** —
`retirements` *plus* `confirmed_derates`. CAISO 2027 reads 1,491.0 MW in the first and 1,333.0 MW
in the second; summing only `retirements` under-counts the exit wave by 47 %. That is the repaired
I4/A1 leak working as designed — but any decomposition that forgets the second key mis-attributes
the gap.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **D1 BOARD-REFRESH** | Board vs live verdict records; A1/I4 cross-ISO | **LANDED** `c02f766` | `capx-d1-board-refresh-nfb31y` | Opus | 36 fields, 0 gates moved. |
| **D2-NYISO** | Root-cause NYISO I7 | **LANDED** `0a2238c` | `capx-d2-adequacy-nyiso-yxv6v0` | Opus | Adjudicated; shipped no fix, deliberately. |
| **D2-NYISO-INTAKE** | Gold Book external capacity | **LANDED — I7 CLEARED** `3786191` | `capx-d2-nyiso-extcap-sewmyx` | Fable | §0.1. First FC-1 PASS in the program. |
| **D2-B I7 LEDGER DECOMPOSITION** | Reproduce/decompose MISO, CAISO, NEISO, PJM | **LANDED** `5dda152` | `capx-d2b-i7-ledger-xaakeu` | Fable | §0.3. Six successor lanes named (S-1..S-6). |
| **D7-NYISO GATE RE-SCORE** | Refresh the board to the extcap re-score; re-read NYISO's four legs; **apply the card-A leg-(c) harmonisation** (CAISO + NYISO `na`→`fail`, `"c"` into both `closed_on`) | **LANDED** `ca8b749` (PR #4289) | `claude/capx-d7-nyiso-gate` | Opus | §0d.1. Board re-scored, no gate moved, Q5 tension recorded verbatim. |
| **D10 NYISO T1-X CROSSOVER** | Run NYISO's T1-X so gate leg (c) closes on a measured FC-4 | **REISSUED r#8** (pack corrected for the nyiso-155 keeper state) | `claude/capx-d10-nyiso-t1x` | Fable | The signature's own consequence: the lead ISO's blocker becomes a run rather than an ambiguity. |
| **D11-R ENTRY VOLUME RULE (D-1)** | Productionize the L-1b margin-exhaustion closure — the measured zero-DOF volume rule — behind a default-OFF field; A/B on ERCOT T1-F | **RE-SCOPED + ISSUED r#8; RATIFIED BY OWNER 2026-08-30** (was D11 pro-forma signal) | `claude/capx-d11r-entry-volume-rule` | Fable | §0e.3/§0e.5. Trajectory invariance (fwd-expectation §3) + the finding's own §7(b) recommendation. Pro-forma build held in abeyance; B-C object charter intact. |
| **D12 SCARCITY-CONSISTENT DELTA BASIS** | The fwd-expectation §4 named successor: both `S` evaluations on one scarcity basis, exact arithmetic on existing objects | QUEUED — **owner-ratified sequencing (r#8 sitting): charter only after D11-R reports** | — | Fable | §7 escalation RESOLVED: (b) first, (a) behind it. The two-scarcity-objects defect (composed entering-2024 mean −$48.22/MWh, solar capture −$185/MWh) is its evidence. |
| **S-123 MISO ADEQUACY PACKAGE** | S-1 requirement re-vintage + S-2 external-capacity intake + S-3 ledger differencing | **ISSUED 2026-08-25 — r#9 start-time check FAILED (miso-190 in flight); held on the check, re-run every refresh** | `claude/capx-s123-miso-adequacy` | Fable | D2-B's own top recommendation: three independent published-source terms, none sized against the residual. Rides with **D9** (SOCO forecast fallback). The owner's r#8 hold-until-r#9 is discharged; the check itself now governs. |
| **S-4 NEISO HYDRO ACCREDITATION** | Per-resource ISO-NE SCC → class factor, replacing the generic 0.50 | **ISSUED 2026-08-25** | `claude/capx-s4-neiso-hydro` | Fable | Decides NEISO 2028's sign. Until it lands, 2028 reads within-input-uncertainty. |
| **S-5 PJM REQUIREMENT HORIZON-EDGE** | Implement hold-last-FPR + the D-1 checker repair; re-score PJM's T1-F leg | **UNBLOCKED by card C (C-A), 2026-08-25 — charter next** | — | Fable | Convention is now declared, so this is implementation + a scorer/governance round, not a decision. Expect PJM's I7 miss to restate 366 MW → ~5.9 GW with 2029 plausibly joining. |
| **S-6 PJM T1-F LEDGER RUN** | The minimum run that makes PJM's supply side observable | QUEUED — **strictly after S-5** | — | Fable | Solo heavy slot (8.8 GB, no co-run). Running it before S-5 would measure against a bar we already know is wrong. |
| **D5 FC-4 CO2 CROSSOVER** | Attribute the crossover CO2 miss | **RE-SCOPED, still not started** | `claude/capx-d5-crossover-co2` | Fable | **Its PJM-first rationale is refuted** (§0.3): PJM is no longer closest. Re-point to the ISO whose gate is actually live, or run it as a three-ISO derivation question (ERCOT 43–50 %, PJM 43–58 %, MISO 63–76 %). |
| **D3 MISO RETIREMENT / G3** | G3 cap-grain `retire.total_gw` t1h regression | QUEUED | — | Fable | I13 cobweb half confirmed superseded. |
| **D4-I3 ERCOT** | I3 scarcity-slack invariant (net-revenue half HELD) | QUEUED at half scope | — | Fable | Q1 answered: card Y signed **Y-C**, arc stays open. |
| **D6 FC-3 CURVE-ON OVER-FIRE** | Four T1-H curve legs | QUEUED | — | Fable | — |
| **D8 FORECAST PROVENANCE DEBT** | Bundles tracking no `run_config.json` → FC-7 FAIL | QUEUED — **now NYISO's only caveat** | — | Fable | Promoted in relevance: FC-7 is the sole remaining caveat on the program's best ISO. |
| **D9 MISO SOCO FORECAST FALLBACK** | `ba_code="SOCO"` live only in the forecast path | QUEUED — **rides with S-123** | — | Fable | Handed in by miso-183. |
| **D2-REMEASURE** | — | **RETIRED unrun** | — | — | Premise refuted at refresh #4. |

## 2. Backcast-track watch (last seen 2026-08-30 @ `a53b7b3`, refresh #9)

| item | state |
|---|---|
| Governance (r#9) | **Freeze TIER-SCOPED** (card 6 executed `0589b6f`): validation 2020–2022 lifted for `complete` ISOs, locked test frozen for all, `final` EMPTY. Card 7 standing precondition on any `final` grant (touchpoints run + loop quiescent). CAMPD layup charter closed with cause. Rubric **v3.5** (diurnal amplitude REPORTED-ONLY) verified determination-neutral over all six keepers — the xiso-6 watch item CLOSES. |
| CAISO (r#9) | Keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (caiso-200 recipe replayed on the active measured membership crosswalk; owner-act promotion on the pre-registered rule; no marker, no re-key due). |
| Branches in flight (r#9) | `miso-190-backcast-calibration-okt1cn` (partial-plant mid-window exit carry — miso-188's named successor; PREREG-first) · `nyiso-eastern-seam-par-leg1-w7s8mm` (Leg 1 executing; nyiso-157 gate scorer filed) · `holdout-governance-rulings-0826` (records lane). No ERCOT branch open; ERCOT landed O7 P0-seam Phase-0 + two governance rulings (G-SPUR lidless count, band count 59→61). |
| Branches in flight (r#8) | `caiso-c3a-overrun-closure-5n84mn` · `ercot-backcast-calibration-9wkxrg` still open; `miso-188-rubric-failure-tuning-m1ph17` MERGED mid-refresh (PR #4296). Heavy-slot deconfliction live for ERCOT/CAISO capx work; S-123 releasable on a start-time check (no new MISO branch in flight). |
| MISO (r#8, mid-refresh) | **Keeper → `2026-08-30-miso-188-rvsscope`** (full-span; NOT-YET narrowed to **{C3a-2025} alone**; single delta `retiree_vintage_status_scope=true`, new gated default-off field, matrix row + cells minted per rule 28c; 28 dark retiree-channel units / 1,434 MW dropped on the EIA-860 vintage-status oracle; promoted on the PREREG's own rule, keeper-auditor PASS). Named-not-built successor: the partial-plant mid-window exit gap (5.93 TWh 2023). |
| NYISO (r#8) | **nyiso-156b: Q1 ruled OPTION A — winter locational identification intake AUTHORIZED** (`ab0513e`, spec `INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`; Leg 1 session-executable, Leg 2 owner-executable fail-closed). Measured expectation: winter-face closure alone returns the keeper to CALIBRATED via the C3c standing rule — the live path through Q5 (§0e.2). Seam "unidentifiable" record corrected (authorization-blocked, not identification-blocked). |
| Dashboard hygiene (r#8) | Bench-fingerprint adjudication landed (PR #4293): 11 "stale" bench parts = UNLABELLED, not wrong; measured over the full builder-drift commit set. |
| Keepers (refresh #7 — MISO since superseded by the r#8 row above) | **ERCOT `2026-08-25-236-swcap-clip-k33` — CALIBRATED, empty fail set, but `years: [2023]` (2023-ONLY; see §0d.2 / Q6)** · CAISO `2026-08-17-caiso-200-h1-memberpanel` (caiso-220 replay mid-solve) · **MISO `2026-08-26-miso-187-nucavail`** (NOT-YET) · NEISO `2026-08-17-neiso-99-joint-p1` · NYISO `2026-08-25-nyiso-155-hydro-repair` (NOT-YET) · PJM `2026-08-15-pjm-162-inputclock` |
| Keepers (refresh #6 — superseded) | **ERCOT `2026-08-25-235-2023-discrete-k24`** (NOT-YET, price_mean; **2023-ONLY**, rule-16 waiver SPENT) · CAISO `2026-08-17-caiso-200-h1-memberpanel` (unchanged) · **MISO `2026-08-25-miso-186-statusscope`** (NOT-YET, **fuelmix + price_mean** — two criteria, was C3a-2025 alone) · NEISO `2026-08-17-neiso-99-joint-p1` (unchanged) · **NYISO `2026-08-25-nyiso-155-hydro-repair`** (NOT-YET, price_mean + price_tail) · PJM `2026-08-15-pjm-162-inputclock` (unchanged) |
| Markers / freeze | `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; freeze **TIER-SCOPED since r#9** (locked test frozen for all; validation by marker + `--holdout-authorized`) — was blanket-ACTIVE through r#8 |
| Gate (a) | pass on the literal test: PJM, NYISO, NEISO. fail on marker: ERCOT, CAISO, MISO. **NYISO's BASIS CHANGED** — its marker now rests on a NOT-YET keeper (§0c.2, Q5). |
| Other refresh-#6 movement | xiso-6 opened a **DECISION CARD on the diurnal price-amplitude rubric** (a cross-ISO rubric question — watch it, it could touch six determinations). CAISO AS-revenue registry row populated (storage 14.82 $/kW-yr @ ref 5.517 GW). xiso-5/6 landed a thermal-tranche vintage sidecar + an arm-over-gap guard at the `bins_to_fleet` seam. |
| ERCOT | Card Y signed **Y-C** (hold open). Card Z signed **Z-A**: crosswalk repair — **EASTEX (East Texas GTC) replaces the mis-attributed NE_LOB** on Northeast→North, static 1300 → 2300. ercot-234 also re-pointed the official scorer's validation gate at the ercot-231 keeper (stale since promotion). |
| MISO | miso-184 **V-DEFECT-COUPLING** (matrix cell R). miso-185 **V-NEG-ABSENT** — the §6b firm-export re-open data does not exist (698 EQR seller-quarter reports, no qualifying firm-export obligation); re-open narrowed to contract-grain. **~1.3 GW scarce-export model-class concession** is the honest residual; a D-4 posture question goes to the owner. |
| CAISO | Quiet this cycle. |

**Deconfliction: clean.** D2-B explicitly stopped at a FINDING on the one MISO root cause that
reaches shared solve machinery (S-1), per its charter.

## 3. Owner-tier questions — ALL SIX NOW ANSWERED (Q5/Q6 ruled at the r#8 sitting, 2026-08-30)

Full signature record and the consequences adopted:
**`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5.**

| # | question | resolution |
|---|---|---|
| ~~Q1~~ | ERCOT 2023 arc settled? | **ANSWERED** — card Y signed **Y-C**, hold open ⇒ D4 = I3-invariant half only. |
| ~~Q2~~ | Leg-(c) consistency (card A) | **SIGNED 2026-08-25 — (A-A), at the recommendation.** CAISO + NYISO move `na`→`fail`, `"c"` into both `closed_on`; NEISO unchanged. **NYISO T1-X chartered (D10)** so leg (c) closes on a measured FC-4. No gate opened; leg (d) untouched. |
| ~~Q3~~ | `entry_lookahead_reprice` disarm default (card B) | **SIGNED 2026-08-25 — (B-C), at the recommendation.** Shipped default HOLDS, cell stays `O`, no verdict minted. **Developer-pro-forma construction chartered (D11).** Neither known-wrong object is ratified. |
| ~~Q4~~ | PJM beyond-last-FPR convention (card C) | **SIGNED 2026-08-25 — (C-A), at the recommendation.** **Hold-last-FPR adopted**, bundled with the D-1 checker repair. PJM's I7 miss restates **366 MW → ~5.9 GW**, 2029 plausibly joining — a worse reported result, taken as the more honest bar. S-5 unblocked; S-6 strictly after. 2029/30 parameters intaken on publication (rule 23). |
| ~~Q5~~ | NYISO marker on NOT-YET keeper | **RULED 2026-08-30 (r#8 sitting) — WAIT FOR WINTER INTAKE.** Precedents left unreconciled; the nyiso-156 intake is the resolution route. No marker moves; gate (a) stays PASS on the literal test. Returns to the owner only if the fact pattern recurs first. |
| ~~Q6~~ | ERCOT CALIBRATED but 2023-only | **RULED 2026-08-30 (r#8 sitting) — HOLD, NO ACTION.** No direction to the ERCOT backcast lane; revisit when it goes quiet. Gate (a) keeps failing on both counts meanwhile. |

**None of the four signatures** touched a backcast keeper, marker or matrix cell, lifted the
holdout freeze, authorized a §2.1b full-solve, or opened any ISO's gate.

### Q6 (refresh #7) — ERCOT is CALIBRATED but its keeper is 2023-only

**RULED 2026-08-30 (r#8 sitting): HOLD, NO ACTION** — no direction to the ERCOT backcast lane;
revisit when it goes quiet. The analysis below is preserved as the record the ruling was made on. `2026-08-25-236-swcap-clip-k33` scores **CALIBRATED with an empty failing
set**, closing the 2023 price object card Y held open two days earlier. But its registry declares
`years: [2023]`, so gate (a) fails on **two** counts: ERCOT is absent from `complete`, and
§2.1b(2)(a) requires a **full-span** keeper (rule 16), which this is not. **Declaring ERCOT
`complete` would therefore NOT open its gate (a).** To convert the CALIBRATED result into forecast
progress ERCOT needs a **full-span 2023–2025 keeper carrying the swcap-clip recipe**. Director
recommendation: **before spending any `complete` declaration, have the ERCOT lane re-solve the
swcap-clip recipe full-span** — the rule-16 waiver that licensed the 2023-only form was for the
backcast lane's regime argument and was never a forecast-gate instrument. Sequencing only; no
determination is questioned here.

### Q5 (refresh #6) — NYISO's `complete` marker now rests on a NOT-YET keeper

**RULED 2026-08-30 (r#8 sitting): WAIT FOR WINTER INTAKE** — the precedents are left standing
unreconciled and the nyiso-156 intake is the designated resolution route; no marker moves and
gate (a) stays PASS on the literal test. The analysis below is preserved as the record the
ruling was made on. NYISO's keeper moved to `2026-08-25-nyiso-155-hydro-repair` (NOT-YET on
price_mean + price_tail) and the marker was re-keyed to it, with the D-5(b) worse-determination
stop fired, escalated and resolved by an explicit owner ruling on structural integrity over gate
regression. **On 2026-08-06 the identical fact pattern — a `complete` marker whose keeper scored
NOT-YET — withdrew CAISO's marker outright**, on the reading that "a `complete` marker cannot stand
on a NOT-YET keeper". Both are now on the record and they point opposite ways.

**Why this track cares:** gate (a) is the only §2.1b leg that reads off the backcast marker, and
NYISO is the program's lead ISO — the one ISO whose legs (a) and (b) both pass. On the charter's
literal test (*designated full-span keeper AND an entry in `complete`*) gate (a) still passes, and
this director is NOT re-reading it downward on its own initiative. But the question of whether the
marker is sound is the owner's, and its answer decides whether NYISO's lead position is real.
**Director recommendation: state the reconciliation explicitly** — either (i) affirm that the
owner's structural-integrity standard permits a `complete` marker on a NOT-YET keeper, which
distinguishes the CAISO withdrawal on its own facts (CAISO's was a rubric re-score with no
compensating structural gain), or (ii) apply the CAISO precedent uniformly and withdraw. Option (i)
is the more defensible on this record, but either way the reconciliation should be **written**,
because the two precedents currently contradict each other and gate (a) hangs on which governs.
NYISO's **frontier** status has already returned to the owner on the same promotion.

*Refresh-#8 addendum:* the nyiso-156b ruling (winter intake AUTHORIZED, §0e.2) gives Q5 a live
structural resolution path — the card's §4 measures that winter-face closure alone returns the
keeper to CALIBRATED, which would re-key the marker onto a CALIBRATED keeper and dissolve the
tension prospectively. The written reconciliation of the two precedents remains worth having (it
governs the next time this fact pattern appears), but Q5 no longer blocks anything this track is
doing: gate (a) is taken as PASS on the literal test throughout.

## 4. Prompt issuance record

| date | lane | branch | model | profile | outcome |
|---|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `capx-d1-board-refresh` | Opus | code | **LANDED** |
| 2026-08-23 | D2 ADEQUACY — NYISO | `capx-d2-adequacy-nyiso` | Fable→Opus | nyiso | **LANDED** |
| 2026-08-24 | D2-REMEASURE | `capx-d2-remeasure-t1f` | Fable | all | **RETIRED unrun** |
| 2026-08-24 | D2-B I7 LEDGER | `capx-d2b-i7-ledger` | Fable | code | **LANDED** |
| 2026-08-24 | D2-NYISO-INTAKE | `capx-d2-nyiso-extcap-intake` | Fable | nyiso | **LANDED — I7 CLEARED** |
| 2026-08-24 | D5 CROSSOVER CO2 | `capx-d5-crossover-co2` | Fable | pjm | not started; **re-scoped r#5** |
| 2026-08-25 | **D7-NYISO GATE RE-SCORE** | `capx-d7-nyiso-gate` | Opus | code | issued (now also carries A-A) |
| 2026-08-25 | **S-123 MISO ADEQUACY PACKAGE** | `capx-s123-miso-adequacy` | Fable | miso | issued |
| 2026-08-25 | **S-4 NEISO HYDRO ACCREDITATION** | `capx-s4-neiso-hydro` | Fable | neiso | issued |
| 2026-08-25 | **D10 NYISO T1-X** | — | Fable | nyiso | chartered by card A; prompt written 2026-08-25 |
| 2026-08-25 | **D11 ENTRY-SIGNAL PRO-FORMA** | — | Fable | ercot | chartered by card B; prompt written 2026-08-25; **superseded by D11-R at r#8, never run** |
| 2026-08-25 | **S-5 PJM HORIZON-EDGE** | — | Fable | pjm | unblocked by card C; prompt written 2026-08-25; stands ready (heavy, solo slot) |
| 2026-08-30 | **D10 NYISO T1-X (reissued)** | `claude/capx-d10-nyiso-t1x` | Fable | nyiso | r#8 batch — pack corrected for nyiso-155 keeper state |
| 2026-08-30 | **D11-R ENTRY VOLUME RULE** | `claude/capx-d11r-entry-volume-rule` | Fable | ercot | r#8 batch — re-scoped per §0e.3 |
| 2026-08-30 | **S-4 NEISO HYDRO (reissued)** | `claude/capx-s4-neiso-hydro` | Fable | neiso | r#8 batch — unchanged from 2026-08-25 issue |

## 5. History (compacted)

- **Refresh #1 (08-23):** charter; first state read; D1 + D2-NYISO issued.
- **Refresh #2 (08-24):** D1 landed. Director hypothesised the I7 verdicts sat on a pre-FFR-1C
  HEAD; chartered D2-REMEASURE on it. **Later refuted — see #4.**
- **Refresh #3 (08-24):** no lane started; ercot-233 opened card Y; D9 handed in by miso-183.
- **Refresh #4 (08-24):** Q1 answered (Y-C). D2-NYISO landed and **refuted the pre-fix-HEAD
  hypothesis** — FFR-1C hydro was already inside the FFR-3A-2 verdicts (1,763.3 MW; pre-hydro
  ledger 30,322.2 MW = the board's stale "30.3 GW"). D2-REMEASURE retired unrun; D2-B and
  D2-NYISO-INTAKE issued in its place. Recorded against interest.
- **Refresh #5 (08-25):** D2-NYISO-INTAKE and D2-B landed; **NYISO cleared FC-1**. Cards A/B/C put
  to the owner and **all three signed at the recommendation** the same day (§3).
