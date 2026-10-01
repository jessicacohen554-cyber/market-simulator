# FINDING — caiso-257: the CT-only OASIS class-partition repair is **PROMOTED TO KEEPER**, `2026-09-06-caiso-257-b1-ctonly`, **DETERMINATION CALIBRATED**, with **not one criterion flipping** and zero new parameters. The owner ruled the arm wanted and re-chartered S-1 onto a plant-deduplicated estimator; **the re-screen reproduced caiso-256's already-published +219.8 GWh to 0.038 GWh, so this session claims no out-of-sample surprise and none is anywhere in the record.** Two costs are reported at full magnitude and neither is a footnote: **C4-2025 lands exactly on its tolerance with zero margin left**, and the +220 GWh went to the wrong plants.

**Session caiso-257, 2026-09-06.** Branch
`claude/caiso-257-backcast-calibration-5kj8t9`. Keeper
**`2026-09-05-caiso-252-b1-notrim` → `2026-09-06-caiso-257-b1-ctonly`**
(bundle `caiso257_ctonly`). Pre-registration:
`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` (the owner's
grant of `FINDING-caiso254 §4` OPTION 1, merged) +
`ADDENDUM-caiso257-s1-recharter-2026-09-06.md` (`69d93250`, pushed **before**
the artifact pair was re-applied and before any LP). Rule 22 `[R-HOLDOUT]`:
2023–2025 only; no `complete`/`final` marker; freeze ACTIVE. **Two LP-years
spent** — one 2023 screen (bundle deleted, rule 29(c)) and the three-year
keeper bundle in ONE invocation (rule 16 `[R-ALLYEARS]`).

---

## §1 — THE TWO OWNER RULINGS, AND WHAT THEY DID NOT DO

`FINDING-caiso256-partition-screen §5` put two questions up. Both answered
2026-09-06:

1. **Is the arm wanted at all**, given that its +220 GWh lands on the three
   LA-basin/SDGE peakers and not on Panoche? → **YES, PURSUE.** The basis
   adopted: the repair is right about the **offer** (a measured
   de-contamination, rule 14 `[R-ACCURATE]`) while the **plant allocation** is
   a separate open object that `caiso-252 §7 #4` forbids reaching by
   re-pricing the class.
2. **Re-charter S-1 on a plant-deduplicated estimator?** → **YES.**

**Neither ruling re-scored caiso-256**, whose verdict stands as recorded: on
the estimator registered *then*, the arm died, and the artifact was reverted.
Neither relaxed S-2, S-3, S-4 or the exclusion of C3a, and neither changed the
promotion basis.

## §2 — THE ESTIMATOR: WHAT WAS WRONG, WHAT REPLACED IT, AND WHY THAT IS NOT SHOPPING

**The defect, measured.** `ADDENDUM-caiso256 §4` registered
`ΔE_implied = Σ_i pmax_i × #{t : mc_new_i ≤ λ_t < mc_old_i}` over the 784 of
828 CT_PEAKER tranches whose offer fell. Sibling tranches of one plant carry
bands that all contain the same hours — `p57482_econc00…04`, **five tranches,
all 115.73 MW, one zone**, 329–592 band-hours each — so the count charges one
plant's capacity five times in the same hour, while in the LP the first
tranche to clear lowers λ and the rest do not. Floor 311.8 GWh; measured rise
+219.8; **over-count 4.26×**.

**The replacement.** `ΔE_dedup = Σ_plants Σ_t max_{i ∈ plant, band ∋ λ_t}
pmax_i` — at most one tranche's worth of MW per (plant, hour). Already
implemented and committed as the `POST_HOC_` field in
`_caiso256_s1_implied_displacement.py`.

**The ground it is adopted on, which is the only admissible one:** a plant
cannot displace its capacity twice in one hour. That is a statement about the
LP's feasible set, true before any result existed. **It is not adopted
because it passes.**

**Its own bias, disclosed in the same breath and against interest.** The
`max`-per-(plant, hour) form is biased **LOW** against a reading in which
several tranches of one plant genuinely clear together and the whole plant
ramps — the true first-order displacement of such a plant-hour is the *sum*,
which this replaces with the maximum. So the registered count is biased high,
this one low, and **the truth is bracketed between them**. The factor of 3 was
carried unchanged, not widened. `ADDENDUM-caiso257 §8.3` forbids a **third**
estimator in advance, whatever any future screen returns.

## §3 — THE DISCLOSURE THAT GOVERNS THE WHOLE SESSION

**This re-screen could not surprise me and is not presented as though it
could.** `FINDING-caiso256 §1` published the arm's 2023 answer on every gate.
+219.8 sits inside `[87.2, 784.5]`. I knew that when I put the re-charter to
the owner; the owner knew it when granting it — `FINDING-caiso256 §2` says so
in as many words — and `ADDENDUM-caiso257 §3` says it at the top of the
document rather than in a footnote.

**What the re-charter bought, honestly:** a correct S-1 operand adopted by the
only party entitled to choose it after the fact; a fresh solve at the sha the
arm is actually solved at; and a reproduction check (§4), which is the one
thing here that could genuinely have failed.

**The evidence for the mechanism is unchanged from what
`PRECOMMIT-caiso255 §3.1` registered before the artifact existed, and it
contains no price:** G-BIMODAL (antimode **11.738** MMBtu/MWh inside the
pre-registered [10.9, 12.5] window fixed from published fleet heat rates,
never swept; **2.559 GW** above it inside [1.5, 4.5] GW) **plus the G1
capacity reconciliation** — the pooled CT bucket's **9,950 MW** against its
own published **7,616 MW** fleet, a **30 % excess**, collapsing to **7,391 MW
/ 3 %**. That would be the argument if the bands had moved up.

## §4 — THE GATES, SCORED

**Reproduction gates (`ADDENDUM-caiso257 §4`), the ones that could fail:**

| # | registered | measured | verdict |
|---|---|---|---|
| **R-1** | pair restores to `df277e89` blob shas byte-exactly | all three MATCH | **PASS** |
| **R-2** | S-1 probe reproduces ΔE_dedup 261.5 / 79 plants, ΔE_implied 935.5, 784-of-828 fallen, 0 risen | **261.461 / 79 / 935.462 / 784 / 0** — the artifact json came back **byte-identical in git**, stronger than the ±0.5 GWh registered | **PASS** |
| **R-3** | screen reproduces caiso-256's **+219.8 GWh ±5** | **+219.762**, \|diff\| **0.038**; P0 objective **3,681,906,464.8422**, digit-for-digit caiso-256's | **PASS** |

R-3 is the end-to-end confirmation of §6's G-DRIFT claim: the bit-identity
measurement said the code cannot move this solve, and the solve agrees.

**The 2023 screen (structural, STOP-only, target residual excluded):**

| gate | registered | measured | verdict |
|---|---|---|---|
| preconditions | `mic_partition`; hydro partition; outage/tranche sha256 | 16,055 MW; present, flag off; both identical; **"P1 route: COLD REBUILD"** | **PASS** |
| **S-1** | rise ∈ **[87.2, 784.5]** GWh | **+219.762** (1.6447 → 1.8645 TWh, **+13.4 %**) | **PASS** |
| S-2 | nuc/hydro/wind/solar each < 0.5 % | **0.0 / 0.0022 / 0.0 / 0.0027 %** | PASS |
| S-3 (C1 stop) | no class PASS → FAIL | none | PASS |
| S-4 (C4 stop) | gas r ≥ 0.70, NRMSE ≤ 0.30 | **0.879 / 0.287** vs keeper 0.880 / 0.285 | PASS |
| C3a | **EXCLUDED both ways** | +4.487 vs +4.650 % | reported only |

Screen bundle **deleted before merge** (rule 29(c)); every number it produced
is here and in `_caiso257_screen2023.json`.

## §5 — THE FULL SPAN, SCORED — AND NOT ONE CRITERION FLIPS

One `--years 2023 2024 2025` invocation. Both runs re-scored at the same HEAD
under rubric **v3.6**.

| criterion | tier | keeper | arm | verdict |
|---|---|---|---|---|
| C1 fuel-mix | LOAD | PASS 12/12 free 8/8 | **PASS** 12/12 free 8/8 | — |
| C2 system volume | LOAD | PASS | **PASS** | — |
| C3a mean LMP | LOAD | 56.69 / 37.78 / 37.47 | **56.60 / 37.73 / 37.42** (actual 54.17 / 34.65 / 34.42) | PASS→PASS |
| C3b shape | LOAD | 0.088 / 0.148 / 0.116 | **0.088 / 0.147 / 0.115** | PASS→PASS |
| C3c price tail | SUPP | CAVEAT 2024 | **CAVEAT 2024** (24 / 0 / 0 h vs 47 / 35 / 8) | single ledgered |
| **C4 dispatch corr** | SUPP | 0.880/0.285, 0.909/0.261, **0.877/0.297** | 0.879/0.287, 0.908/0.263, **0.875/0.300** | PASS→PASS, **§6** |
| C6 governance | PROT | PASS | **PASS** (attested at promotion) | — |
| C8 forced share | PROT | PASS | **PASS** | — |

**C1 detail.** CT_PEAKER **1.643 → 1.862 TWh** (2023) and **1.386 → 1.585**
(2024) against actuals 4.128 / 4.326 — toward the actual in both years.
Against interest: **CC_REGULAR moves marginally AWAY** (48.549 → 48.362 vs
51.837; 46.265 → 46.105 vs 45.992) and so does **ST_GAS-2023** (0.098 → 0.081
vs 1.308), while ST_GAS-2024 moves toward (0.205 → 0.173 vs 0.120).

**C3a is LOWER in all three years — the EIGHTH consecutive favourable
direction in this lane.** Declared in advance as unusable and **excluded from
the promotion basis in both directions.** It is reported here and is not
offered as evidence for anything.

**DOF ledger byte-identical to the keeper's at 9 entries / 6 residual**, and
the attestation declares **no `authorized_price_tuning` block**: no band
multiplier was chosen against a price, a residual or a gate. This is rules
13/14, not the rule-1 `[R-STRUCT]` tuning channel.

## §6 — THE HEADLINE COST: C4-2025 IS NOW EXACTLY ON ITS TOLERANCE

**Gas NRMSE 2025: keeper 0.297 → arm 0.300, against a ≤ 0.30 bound.** It
**PASSES** on the scorer's own arithmetic and it consumes **the entire
remaining margin in that cell**. 2023 (0.285 → 0.287) and 2024 (0.261 →
0.263) move the same way; r falls 0.880/0.909/0.877 → 0.879/0.908/0.875.

C4 is supporting-tier and was excluded from the promotion basis in both
directions before any solve, so it does not block — but stating it as a mere
"supporting-tier nudge" would be false. **The next arm in this lane has no
C4-2025 headroom left**, and that is a standing constraint on the queue, not a
footnote. Anyone proposing a CAISO offer- or import-side lever should treat
C4-2025 as a binding pre-solve check.

## §7 — THE SECOND COST: RIGHT OFFER, WRONG PLANTS

`FINDING-caiso256 §3`, unchanged and re-affirmed on the full span: the rise
lands on **p57482 462 / p57515 375 / p57555 281 GWh** — the three LA-basin /
SDGE peakers — against **Panoche 56803 at 172**. So the arm moves CT_PEAKER
toward its C1 actual **through the wrong plants** and **deepens** the
`caiso-252 §3.3` mis-allocation. The owner ruled it wanted on exactly that
record: it is right about the measured **offer** and silent about the
**plant**. **This keeper claims no closure of the CT volume miss** — the class
is still 2.27 / 2.74 TWh short in 2023 / 2024.

## §8 — G-DRIFT AND G-CTRL

`fa23c1f7 → solve sha`, **by measurement, not by reading**:
`_caiso255_gdrift_identity.py` rebuilt the keeper's LP inputs at both shas
with the artifact pair in its reverted state → **EVERY ARRAY BIT-IDENTICAL**
in all three years (1,662 / 1,656 / 1,661 units, plus the 7×8760 demand
matrix). Reported in full rather than as a bare verdict: **6 pre-existing
`ScenarioConfig` defaults changed** (5 path-registry relocations +
`ccs_retrofit_vom_adder`, a forecast-only field), **16 fields added** (all
absent from the recipe), **7 constants changed and 8 added** — each settled
empirically rather than argued. `_caiso257_gdrift_at_solve.json`.

**⇒ G-CTRL FORM 4. No control solve was spent.** The one LIVE hunk on the
chain (`results/emissions.py::import_co2_tons`) touches `co2` alone, which is
not in `CRITERIA`; **`co2` was never differenced.**
`MARKET_SIM_P1_BASIS_SEED=0` made the same-year P1 basis seed **unreached**
rather than asserted inert.

## §9 — DISCLOSURES AGAINST INTEREST

1. **The gate this arm passed is one I proposed replacing after seeing it
   fail.** The construction argument is sound and the owner made the call, but
   the sequence is what it is and §2/§3 state it rather than smoothing it.
2. **The re-screen carries no information the record did not already have.**
   Its value is a correct operand and a reproduction check, not a new test.
3. **C3a improved for the eighth consecutive time in this lane.** Excluded by
   rule, and I note the pattern because a lane whose every promotion moves the
   same residual favourably should be watched for exactly the selection this
   exclusion exists to prevent.
4. **C4-2025 at 0.300 is the least comfortable number in this session** and is
   §6 rather than a parenthesis.
5. **Two classes move away from their actuals** (CC_REGULAR both years,
   ST_GAS-2023) — §5.
6. The screen bundle's `legitimacy_diagnostics.json` reports D-4 FAIL rows for
   `chp_steam` exactly as the keeper's does; the CHP classes are D-2-exempt
   and C8 PASSES on the promoted bundle.
7. **What OPTION 1 does not repair, stated at the gate:** with no `ST_GAS`
   entry written, `backcast_config._ungrounded_source` still falls back to
   `"ST_GAS": "CT_PEAKER"`, so the ST_GAS multiplier remains **borrowed** —
   though no longer **circular**, since the bucket it borrows from no longer
   contains ST_GAS. Moot in the LP (`caiso-254 §3`: the whole CAISO ST_GAS
   fleet bypasses `offer_curve_by_group`), and it stays on the queue.
8. **The prune has a consequence a later session will hit.**
   `results/calibration/caiso252_b1_notrim` is off disk under rule 15
   keeper-only retention, so the form-4 control is now this bundle, and three
   probes hard-code the caiso-252 path (`_caiso256_screen2023.py`,
   `_caiso256_s1_implied_displacement.py`, `gen_caiso257_attestation.py`).
   They must be re-pointed before re-use; the caiso-252 bytes remain in git
   history.

## §10 — DO-NOT-REDO ADDS

1. **Never re-charter S-1 a second time.** Two estimators have now been
   registered on this object; a third would be shopping however it were
   dressed (`ADDENDUM-caiso257 §8.3`).
2. **Never quote this arm's C3a move, or its screen pass, as evidence for the
   mechanism.** C3a is excluded; the screen may kill and never promote; and
   the answer was public before the re-screen ran.
3. **Never propose a CAISO offer- or import-side lever without checking
   C4-2025 first** — it sits at 0.300 against a ≤ 0.30 bound with zero margin.
4. **Never read this keeper as closing the CT volume miss.** It moves CT
   energy through p57482 / p57515 / p57555, not Panoche, and deepens the
   caiso-252 §3.3 mis-allocation.
5. **Never re-point a caiso-252-bundle probe at the new keeper without
   re-reading it** — the control changed identity, not just path.
6. caiso-256 (partition) §7 and (storage) §6, caiso-255b §6, caiso-254 §6,
   caiso-253 §7, caiso-252 §7 and §12, caiso-251 §8, caiso-250 §7, caiso-249
   §7, caiso-248 §8, caiso-247 §8, caiso-246 §8, caiso-245 §7, caiso-244 §7,
   caiso-243 §10, caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8,
   caiso-230 §9, caiso-229 §10, caiso-169 §9, caiso-168 §8 stand in full.

## §11 — QUEUE

1. **C4-2025 has no margin.** Not an object in itself — a constraint on every
   future one.
2. **The hod 22–23 CC over-run** — still OPEN with **no named carrier**
   (import refused on admissibility at caiso-253; storage on the wrong side on
   **both** bases at caiso-255b / caiso-256).
3. **Panoche (56803) and the CT volume miss** — untouched, and this keeper
   deepened the mis-allocation around it.
4. **The borrowed ST_GAS multiplier** (§9.7) — moot in the LP, real on paper.
5. **The caiso-127 evening/overnight storage pin** (S2, DA/RT two-settlement),
   measured a fourth time at caiso-256, **unfunded** under caiso-201.
6. Carried, raised not granted: the **`complete` marker** (re-raised this
   session under rule 22, owner **again declined** — "not now, keep raising
   it"); the stale `program-status.json` CAISO keeper stamp (**not touched**);
   the C3a weight basis (caiso-247 §4.5); the per-zone storage/class sidecar;
   the DMM 2025 RA-import basis.

**Keeper PROMOTED. No `ScenarioConfig` field added, no DOF row added, no
`complete` declaration, no out-of-training year touched, freeze ACTIVE.**
