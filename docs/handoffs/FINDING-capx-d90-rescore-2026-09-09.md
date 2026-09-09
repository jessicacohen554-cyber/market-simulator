# FINDING — capx D90: the `neiso-t3` re-score on D88-repaired code

**Lane:** capx D90-RESCORE · **Branch:** `claude/neiso-t3-d90-rescore-u4b5bw` · **Date:** 2026-09-09
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Authority:** OWNER RULING **Q63** (2026-09-08, capx ledger §0bg.3(a))
**Gates pre-registered:** `PRECOMMIT-capx-d90-rescore-2026-09-09.md` + Addenda A/B, **all pushed
before any LP was spent** (`cb7b4478`, `d5da94a7`, `09ef52a3`)

---

## 0. THE VERDICT TRANSITION

| | determination | FC-1…FC-8 |
|---|---|---|
| **OLD** (`neiso-2026-2050-t3-golden3-d60`, scored 2026-09-06) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT PASS PASS |
| **NEW** (re-solved on D88-repaired code, same recipe) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT **FAIL\*** PASS |

**\*** FC-7 moves for a reason that is **this lane's instrumentation, not the model and not D88** —
it moves **identically in the pre-D88 control**, which is the proof. Held against d60's own committed
DOF ledger it reads **PASS** and the board is unchanged in every category (PRECOMMIT Addendum B
pre-registered exactly this, before the solve).

**The one sentence: the repair neither helped nor hurt — measured against a same-container pre-D88
control, capx D88 moves ZERO of the 19 scored rows, and the determination is HOLD on every reading.**

**And the finding that matters more than the one it was chartered for:** the flagged defect was never
the main thing wrong with this record. **A different repair — capx D77 — moves the run far more than
D88 does**: CO2 in the CCS conversion window falls **>50 %** (2029: 14.021 → 6.795 Mt), while the
determination and every scored row still reproduce. The standing verdict's *scores* were sound; its
*underlying numbers* are stale, and **not because of the defect it was flagged for**. Attribution is
exact, not inferred — see §5.1.

---

## 1. THE GRADED PREDICTION (PRECOMMIT §5, fixed before the solve)

**5 hits, 3 misses, 3 partial. The headline prediction P1 is a MISS**, and the summary sentence I
declared is **half right**: the determination call was right, both mechanism calls were wrong.

| # | prediction | outcome | grade |
|---|---|---|---|
| **P1** | FC-2 row2 flips **PASS → FAIL**, final RM in [0.5 %, 4.5 %] | **PASS**, final RM **6.4 %** | **MISS** |
| **P2** | FC-2 row1 degrades to CAVEAT/FAIL (declared ~50/50) | **PASS**, unmoved | **MISS** |
| **P3** | FC-2 row3 stays FAIL, gas_cc count **≥ 13** | stays FAIL, but **gas_cc(7); gas_ct(4)** | **PARTIAL** |
| **P4** | row4 stays PASS, share rises, < 10 % | PASS, 0.5 % → **1.0 %** | **HIT** |
| **P5** | I3 stays FAIL, magnitudes move < 2 pp, **sign not called** | stays FAIL, **byte-identical** | **HIT** |
| **P6** | co2@2040 **falls below 8.559 Mt** (direction only, per A.3) | **4.214 Mt** | **HIT**, but see §1.1 |
| **P7** | FC-5 stays CAVEAT, divergence count moves ≤ 2 | CAVEAT, **26 → 26** (0) | **HIT** |
| **P8** | FC-3 / FC-4 unchanged — *provably* | unchanged | **HIT** |
| **P9** | FC-7 PASS, 8–9 entries, all IDENTIFIED | **9 entries, 2 UNIDENTIFIED**, row FAIL | **MISS** (pre-recorded in Addendum B) |
| **P10** | FC-8 PASS, wall 5–25 min | PASS, **31.1 min** | **PARTIAL** (bracket missed) |
| **P11** | determination **HOLD → HOLD** | HOLD → HOLD | **HIT** |

### 1.1 P6 is a hit on a technicality, and the honest reading is the opposite

P6 was graded against the **committed d60 baseline** (8.559 Mt), and the arm lands at 4.214 Mt — a
hit. But the pre-D88 control lands at **3.599 Mt**, so **D88's own contribution to co2@2040 is
+0.615 Mt — it makes emissions WORSE, not better.** The improvement my prediction "caught" is
entirely code drift. Recorded as a hit because that is what the pre-registered text says, and
immediately corrected, because reporting it as evidence that D88 improves emissions would be false.

### 1.2 Why P1 missed, stated as a diagnosis rather than an excuse

P1 reasoned from D88's measured **−3.88 pp** RM depression at 2040 against only **1.55 pp** of
headroom. Both halves were right in isolation — D88 *does* depress RM by 2.9–3.8 pp in the years it
touches (§3) — and the prediction still failed, for two reasons I did not anticipate:

1. **The baseline moved.** Code drift lifted the terminal RM from d60's 5.33 % to the control's
   **7.04 %**, so the headroom P1 was reasoning about no longer existed.
2. **2050 is not a year D88 much touches.** Its effect there is **−0.65 pp**, an order below its
   2036–2040 effect, because the retirements it re-times have largely washed through by then.

PRECOMMIT §A.4 recorded a caveat that would have made P1 *easier* to hit (the control's sawtooth RM
already dips below the floor at 2048). It did not save the prediction, and the caveat is not now
being reused to soften the miss.

---

## 2. THE RE-SCORE, EVERY LEG AT FULL MAGNITUDE

Three columns: the **committed d60** bundle (what the standing verdict was scored on), the
**same-container pre-D88 control**, and the **D88 arm**. Every carried input (FC-3 hindcast score,
FC-4 crossover score, FC-6 driver battery + paired invariants, FC-5 corridor + anchors) is held
**byte-identical** across all three, so only the solve can move a row.

| leg | row | d60 | pre-D88 control | **D88 arm** | D88's own effect |
|---|---|---|---|---|---|
| FC-1 | invariants I1–I14 | FAIL `['I3']` | FAIL `['I3']` | FAIL `['I3']` | **none** — detail string byte-identical |
| FC-2 | row1 RM band | PASS | PASS | PASS | none |
| FC-2 | row2 terminal RM | PASS 5.3 % | PASS **7.0 %** | PASS **6.4 %** | −0.65 pp, no gate |
| FC-2 | row3 cobweb | FAIL `gas_cc(13)` | FAIL `gas_cc(7); gas_ct(4)` | FAIL `gas_ct(4); gas_cc(7)` | **none** (same set) |
| FC-2 | row4 backstop | PASS 0.5 % | PASS 1.1 % | PASS 1.0 % | −0.1 pp, no gate |
| FC-3 | hindcast bands | FAIL (11 bands) | FAIL | FAIL | **none — provably** (§2.1) |
| FC-4 | quarantine | PASS | PASS | PASS | none |
| FC-4 | dispatch skill | FAIL | FAIL | FAIL | **none — provably** (§2.1) |
| FC-4 | input-gap ratio | PASS | PASS | PASS | none |
| FC-5 | corridor | CAVEAT, 26 divergences | CAVEAT, 26 | CAVEAT, 26 | **none** |
| FC-6 | battery / P1 / P2 / P3 | CAVEAT / PASS×3 | identical | identical | **none — carried, cannot move** (§2.2) |
| FC-7 | run_config | PASS | PASS | PASS | none |
| FC-7 | overlay-off | PASS | PASS | PASS | none |
| FC-7 | **dof ledger** | PASS (7/7) | **FAIL** (9, 2 UNIDENTIFIED) | **FAIL** (9, 2 UNIDENTIFIED) | **none — identical in the control** |
| FC-7 | attestation | PASS | PASS | PASS | none — but see §4.2 |
| FC-8 | runtime | PASS 6.7 min | PASS 31.7 min | PASS 31.1 min | none (never-blocking tier; 9 h budget) |

**Nineteen scored rows. D88 moves none of them.** The single row that moves against d60 moves
**identically in the pre-D88 control**, which is what identifies it as the lane's pins rather than
the repair.

### 2.1 FC-3 and FC-4 are carried, and the inertness is a PROOF, not a convenience

T1-H spans 2021–2025 and T1-X spans 2023–2027, both **entirely below**
`ccs_retrofit_available_year = 2028`. `ccs.py:187` and `ccs.py:366` each `return fleet, []` when
`year < config.ccs_retrofit_available_year`, so **no converted representative exists in either
window and no duplicate `unit_id` can arise.** D88 cannot reach them.

### 2.2 FC-6 is carried and is INCAPABLE of moving — so no FC-6 reading here is evidence about D88

Reproducing the standing verdict (PRECOMMIT §A.2) required `bau-d46`'s `paired_invariants.json` and
driver battery: **the standing d60 verdict already carried its FC-6 from d46 and never measured it on
d60's own solve.** This lane carries it identically so both sides stay symmetric. The pre-existing
staleness — d60's *and* the arm's FC-6 paired CO2/build rows are d46's numbers — is reported, not
absorbed, and re-measuring it is a separate lane's work.

---

## 3. WHAT D88 ACTUALLY DOES — isolated against the same-container control

**It is a retirement TIMING shift, exactly as D88 diagnosed — and this reproduces its signature on an
INDEPENDENT recipe**, which is a real corroboration of that lane's mechanism claim.

| year | retirements ctl → arm | retired MW ctl → arm |
|---|---|---|
| 2036 | 2 → **6** | 4.371 → **959.447** |
| 2038 | 4 → 3 | 955.076 → **1057.736** |
| 2041 | 3 → **0** | 1057.736 → **0.000** |
| 2048 | 4 → **7** | 828.635 → **1762.766** |

Cohorts move **earlier**: ~955 MW from 2038 → 2036, ~1058 MW from 2041 → 2038. Cumulative
retirements 2026–2050 go **6,727.120 → 7,661.251 MW**, and terminal `gas_cc_ccs` ends **934.1 MW
lower** (3,693.388 → 2,759.257 MW).

**The scored consequence, both directions, at full magnitude.** D88 moves 8 of 25 years
(2036–2040, 2048–2050): reserve margin **falls 2.9–3.8 pp** (2050: −0.65 pp) and CO2 **rises
+0.21 to +1.48 Mt**. **So the corrected trajectory is TIGHTER and DIRTIER than the uncorrected one.**
No gate is crossed in either direction.

**Its footprint is one unit, and that is why it is small here.** The re-mint is gated on the legacy
`gas_cc_{bin}_{zone}` form, but this recipe runs `use_campd_bins=True`, so nearly every converted
representative carries a CAMPD per-plant id (`CC_REGULAR_Boston_p60903_econ`) that the gate does not
match. Across the whole 25-year horizon **exactly one row is re-minted**:
`gas_cc_ccs_h_class_Central_r2031` — matching D88's own census for this bundle. One distinct id, and
934 MW of retirement re-timing follows from it.

**Rule 1 `[R-STRUCT]` disposition, unchanged by any of this.** The repair stays in because
duplicate-free fleet identity is structurally correct. It is *not* retained because it improved
anything — it did not — and it would not be reverted had it scored worse, which on adequacy and
emissions it in fact does.

---

## 4. TWO INSTRUMENT DEFECTS FOUND, NEITHER REPAIRED HERE

### 4.1 The cache-key registration is broken on `main` — 0 of 173 payloads reproduce

At this HEAD **no committed run payload in the repository reproduces its own recorded cache key**,
and the default key is off its pin (`72341e34fd261997` vs pinned `547053bdfccd4264`; the pin tests
are still RED, confirmed).

**Attributed to one field, by experiment.** Registering `pjm_seam_neighbour_hourly_ladder` (added by
`f2a834de` with no `_CACHE_KEY_OPTIONAL_FIELDS` entry, so it always enters the hash) at a frozen
`"False"`, in memory only:

| | before | after |
|---|---|---|
| payloads reproducing their key | **0 / 173** | **78 / 173** |
| `bau-d60` (this lane's target) | ✗ | ✓ **`f04fd06348e1623d`** |
| `bau-d65br` (D88's own control) | ✗ | ✓ **`0fc42cb56c24d544`** |

Reproducing **D88's own reported control key to the character** both corroborates that lane's audit
and dates the regression after its measurement. PJM-scoped and `False`, so **inert for a NEISO
forecast solve** — its only effect here is that the arm landed at `ae317e63263c8eef` instead of the
scored bundle's own key. **D91's to fix; measured and left alone.**

### 4.2 FC-7's attestation row cannot see a FALSE assertion — and it is blind in the form the program actually writes

`forecast_verdict.py:1708` tests `not block.get(a)`. Every golden attestation writes assertions in the
**nested** form `{"value": …, "read_from": …, "evidence": …}`, and a non-empty dict is **truthy**, so
`value: false` is never detected.

Demonstrated on this lane's own artifact: `dof_ledger_complete` is authored **`false`** (honestly —
the ledger really does carry 2 UNIDENTIFIED entries), and FC-7's attestation row nonetheless reads
**"all §5 checklist assertions present and true"**. Flattened, the same block flags it correctly.

**This is material**: FC-7's attestation row is rubric §5's gate for certifying a T3 deliverable, and
it is blind to exactly the failure it exists to catch. **Not repaired here** — it is `score_*`
infrastructure, and editing the scorer mid-re-score would contaminate this lane's own result.
**Routed to the forecast desk / rubric owner.** Had it read the nested form, FC-7's attestation row
would read **FAIL in both the arm and the control** — which changes no determination (already HOLD)
but is the honest reading, and is recorded here rather than left to be discovered later.

---

## 5. G-DRIFT: MY OWN AUDIT HAD A GAP, AND THE SOLVE FOUND IT

PRECOMMIT §3 audited four channels and cleared them: 29 new config fields all resolving to the
bundle-effective value; the D79 solve surface empty for NEISO (**an instrument proven live — it fires
`NUCLEAR_MONTHLY_CF_BY_YEAR` for ERCOT**, so the NEISO null is a measurement, not a dead check); six
ORDC/scarcity differences identified as NEISO's own `ISOConfig` overrides; and two genuinely LIVE
hunks (capx D65 Act A/B) **pinned out**, verified by a **zero-field diff** against the committed
`config.yaml` — reconfirmed post-hoc on the realized `run_config.json`.

**And it still missed the largest mover, because it audited CONFIG, not CODE.** The recorded-key
basis proves the *recipe* is identical; it cannot prove the *code* is. Between d60 and HEAD the
`ccs_retrofits` ledger gained nine keys (`capex_scale`, `fixed_cost_scale`, `old_emission_rate`, …)
and the conversion window's emissions changed by **>50 %**, none of it visible to any of the four
channels.

**T-REPRO caught it, which is why it was pre-registered.** 2027–2031 ledgers differed in years where
D88 is provably inert — 2027 by one row's `depth_usd_per_kw_yr` (24.84413 → 24.86779), 2028 by the
retrofit rows' new diagnostic keys with **identical unit_ids and zero shared-key value diffs**.
T-REPRO **FAILED**, rule 29(b)'s LIVE case fired, and the same-container pre-D88 control was solved —
in a throwaway git worktree with D88's three files reverted to `8c24cbf6` (none of which changed after
D88 merged), so **no file under `src/market_sim/` in this working tree was edited**.

### 5.1 THE DRIFT IS capx D77, AND THE ATTRIBUTION IS EXACT

Not "unattributed code drift" — it reproduces **capx D77's own published A/B to four decimals**. D77
(2026-09-06) repaired the CCS emission-rate seam, where `campd_bins.apply_plant_emission_rates_v2`
re-booked a converted unit's *uncaptured* host rate over its captured one in every forecast year:

| year | D77's published A/B | this lane's d60 → pre-D88 control |
|---|---|---|
| 2028 | 15.8562 → 12.9276 (−18.5 %) | 15.856 → 12.928 |
| 2029 | 14.0210 → 6.7954 (−51.5 %) | 14.021 → 6.795 |
| 2030 | 13.3680 → 6.9545 (−48.0 %) | 13.368 → 6.955 |

**Identical.** So the CO2 movement in this re-score is D77's repair landing on a bundle solved hours
before it, and the 2029/2030 retrofit-set reshuffle is D77's documented self-limiting effect (cheaper
correctly-rated CCS depresses the price that justifies the next retrofit). D77's own record predicted
this exact consequence — *"the three NEISO T3 verdicts' co2@2030/2035/2040 FC-5 rows and their FC-6
paired-P1 cumulative-CO2 row are the only SCORED cells mis-stated"* — and explicitly deferred the
re-solve to the D65-B batch. **This lane confirms that prediction on the `neiso-t3` record and closes
the measurement half of it**; the re-solve decision remains open (§7).

**It does not change anything above.** D88's isolation is against the same-container control, which
carries D77 on both sides, so every number in §2 and §3 stands exactly as reported.

**Generalising, for the audit board:** G-DRIFT form 4 on a recorded-key basis audits **config drift
only**. It sees neither derived-input drift (D88's §3 lesson) nor **non-config code drift** (this
lane's). Against a bundle months old, the control solve is not the fallback — **it is the only
instrument that isolates anything**, and its cost should be assumed, not avoided.

---

## 6. THE FLAG — replaced, per the pre-registered rule

The re-score **completed**, so PRECOMMIT §6 clause 1 applies: `provenance.known_defect` is **REMOVED**
from the `neiso-t3` record and replaced with a factual `provenance.rescored` block recording that the
defect is resolved, what D88 was measured to do, and that the determination and all 19 scored rows are
unchanged — plus the staleness in §0 that is *not* D88's and is routed rather than resolved.

**Verified, not asserted:** the edit is confined to that one key (round-tripped and compared: with
`rescored` removed and `known_defect` restored, the document is `==` the pre-edit document), the
serialization is reproduced exactly (`json.dumps(indent=1)` + newline, guarded before writing), all
106 records survive, and **`git diff --stat` is 1 insertion / 1 deletion**. `determination` stays
`HOLD`.

**What is NOT done, and why it is the owner's call.** The `neiso-t3` record still points at
`neiso-2026-2050-t3-golden3-d60`. Re-pointing it at this lane's arm would substitute a run carrying
two restoration pins that make it non-default at HEAD and give it an FC-7 `dof ledger` FAIL — a
board downgrade caused by instrumentation, not by the model. A genuinely clean successor is an
**unpinned re-solve at today's defaults**, which is a different run and outside this charter. §7
puts that question.

---

## 7. RULE 31 `[R-RETAIN]` — WHAT IS ON DISK, AND THE PROMOTION QUESTION

**Nothing solved in this session has been deleted.** Both bundles are on local disk:

| bundle | key | status |
|---|---|---|
| **arm** `results/ff-t3-neiso-golden/d90-rescore/` | `ae317e63263c8eef` | 25/25 yr, 31.1 min — slim files committed with this FINDING |
| **control** `results/ff-t3-neiso-golden/d90-pre-d88-control/` | `f9256ed2124ce37d` | 25/25 yr, 31.7 min — **gitignored** (rule 29(c) keeps a control out of `main`; rule 31 keeps it on disk) |

**THIS CONTAINER IS EPHEMERAL. Neither bundle survives it, and the gitignored control cannot be
recovered from git at all.** Reproducing the pair costs **~63 min of LP plus ~55 min of `data/clean`
rebuild** in a fresh container — the cost profile the ercot-255 incident was written about.

**THE PROMOTION QUESTION, ASKED EXPLICITLY:**

1. **Should `neiso-t3` be re-pointed at a re-solved run at all?** This lane's evidence says the d60
   verdict's *scores* are unaffected by the D88 defect, so nothing forces it. But its *numbers* are
   stale by >50 % on CO2 for unrelated reasons, which argues for a fresh solve on its own merits.
2. **If yes — pinned or unpinned?** This lane's arm is pinned to d60's recipe (correct for isolating
   D88, wrong as a going-forward record). An **unpinned re-solve at today's defaults** would be the
   honest successor and is ~31 min. I recommend the unpinned re-solve, as a new lane.
3. **Should the arm be registered on the forecast dashboard as its own run** (`neiso-t3-d90-rescore`),
   as evidence, rather than replacing `neiso-t3`? I did not do this unasked, because a run whose FC-7
   fails on its own instrumentation is a confusing board entry without the context in this document.

**Say the word on any of the three and I will act while the bundles are still alive.**

---

## 8. ROUTED ONWARD

1. **`pjm_seam_neighbour_hourly_ladder` is unregistered** and moves every cache key in the program
   (0/173 reproduce) → **D91** / the cache-key pin owner. §4.1 has the one-field attribution.
2. **FC-7's attestation row cannot detect a false nested assertion** → forecast desk / rubric owner.
   §4.2, with the demonstration.
3. **The `neiso-t3` record's underlying numbers are stale by >50 % on CO2 — attributed exactly to
   capx D77** (§5.1), whose own record deferred the re-solve to the D65-B batch → forecast desk. This
   lane closes the measurement half; the re-solve decision is open.
4. **G-DRIFT form 4 audits config, not code** → audit board, extending D88's §3 method note: against
   an aged bundle the control solve is the only isolating instrument.
5. **d60's — and every T3 golden's — FC-6 is carried, never measured on its own solve** → whichever
   lane owns FC-6 re-measurement. §2.2.
