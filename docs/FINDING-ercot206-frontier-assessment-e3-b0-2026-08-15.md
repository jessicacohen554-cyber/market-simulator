# FINDING — ercot-206: the ERCOT-FRONTIER-1 assessment (three answers, cited), and the
# E3 reopen STOPPED AT B0 by its own pre-registered rule — the settled basis resolves
# FFR-8A's 2025 anomaly and leaves a clean YEAR-KEYED split that validates neither
# parameter set

**Session ercot-206, 2026-08-15. Dispatch ERCOT-FRONTIER-1. Doc-only Phase A + a
read-only measured-data Phase B0; NO LP, no year solved or scored, no run
registered, no matrix cell or row edit, keeper untouched at
`2026-08-15-ercot204-rule26-delete`.** Precommit (pushed before the probe ran):
`docs/PRECOMMIT-ercot206-e3-reopen-b0-2026-08-15.md`. Probe:
`scripts/probes/ercot206_e3_settled_reproduction.py` →
`results/calibration/ercot206_e3_settled_reproduction.json`.

---

## 1. PHASE A(1) — IS THE QUEUE ACTUALLY CLEARED? Yes of chartered executable work;
## the dispatch's two expected residues are both STALE as stated

The dispatch expected: "item 2 (C6 attestation — blocked on the 8
residual-identified DOF entries) and the un-chartered audit-grade item 7 open;
everything else closed or executed." The record confirms the OUTLINE (the queue
is cleared of chartered executable work — pack §A12.4: *"ERCOT's
owner-independent lever queue is therefore EMPTY of chartered work"*) and
REFUTES BOTH PARTICULARS:

* **Matrix §5.1 numbered queue 0–9 (+7b/7c/9b), every item**: 0 CC committed
  offer — executed/adopted (lineage ercot137 → ercot139 → ercot140, §5.1 +
  log ercot-140); 1 CLOSED-EXECUTED (ERCOT-137); 3 CLOSED (ERCOT-142→143,
  "DO NOT RE-OPEN"); 4 EXECUTED (ERCOT-145b, keeper); 5 CLOSED `G`
  (ERCOT-145); 6 CLOSED `I` (ERCOT-146); 7b/7c CLOSED (ERCOT-154/155);
  9 CHARTERED-EXECUTED-REJECTED (ERCOT-159, `U → R`); 9b's storage successor
  BUILT AND REFUTED `R` (ercot-162); top-block items 10–26 all
  DISCHARGED/CLOSED/EXECUTED (§5.1, per-item markers, through ercot-193).
* **Item 2 as written is DOUBLY stale.** Its text ("blocked only by the 8
  residual-identified DOF entries") predates two owner-recorded events:
  (i) **ERCOT-144** (2026-07-31) retired the coal-offer residual DOF onto
  measured per-plant curves — ledger `n_residual` **8 → 6**
  (COAL_SIGMOID_DEFAULTS[ERCOT] and coal_take_or_pay_tranches retired) — and
  **"C6 is ATTESTED and PASSES"** (§5.1 ERCOT-144 note; the C6 governance
  criterion is ALL-PASS on the current keeper's committed status shard);
  (ii) the C3c ledger disposition itself — the thing item 2 existed to route —
  was **owner-executed at ercot-166** (2026-08-05): *"C3c becomes a LEDGERED
  ACCEPTED MODEL-CLASS LIMITATION in all three years (rubric v3.0 owner
  amendment)"*, carried since in every gates line as "C3c the single ledgered
  CAVEAT ×3" (58/181, 22/53, 1/31 at the current keeper). The six DOF entries
  still residual-identified at the current keeper
  (`results/calibration/ercot204_rule26_delete/calibration_attestation.json`,
  n_entries 18 / n_residual 6), named individually:
  **`offer_curve_by_group`, `offer_curve_smoothing`, `wefor_multiplier`,
  `wefor_residual`, `battery_dispatch_adder`,
  `CHP_BTM_PCT_BY_SECTOR['merchant']`** — attested, and C6 passes WITH them
  attested; they block nothing.
* **Item 7 is not un-chartered — it was executed to promotion.** The data
  prerequisite at ERCOT-160, the identification at ERCOT-164, and the WP-B v2
  build/A/B at **ERCOT-165 — OWNER-PROMOTED keeper
  `2026-08-04-ercot165-unpooled-share`** (§5.1 item 7 block). The "un-chartered
  audit-grade item 7" phrasing traces to the ERCOT-144-era note (2026-07-31),
  stale by four sessions at the dispatch date.
* **What IS still open, enumerated with blockers** — all owner-side or
  data-gated, none chartered executable work:
  1. **Item 8 — CLOSED, REFUSED ON DATA**, sole reopen condition UN-RUN: the
     CME/NYMEX Waha/HSC basis-swap daily-settlement screen (free; needs its own
     rule-13 admissibility argument before item 8 can return — §5.1 item 8(b),
     owner decision 2026-08-04 "NO PAID DAILY GAS DATA"). Subsumes
     `winter_citygate_daily` (same intake, §5.1 item 8(b)/item 4 tail).
  2. **The regime-conditioning decision card** — AUTHORIZED doc-only at the
     V0-FAIL adjudication item (ii) (L-SCAR card foot, 2026-08-14) but **never
     assembled**: the REGIME-CARD lane died at provisioning (pack §2.10/§2.12),
     no card doc exists on main, and shorthands 199/200 sit unspent. Zero
     measured forward-regime anchors exist until the 2026 SOM (~mid-2027)
     regardless.
  3. **`gas_hh_monthly_shape` 26c row gap** — armed on the keeper, still no
     matrix row (mechanism-matrix.js:780 records the gap; owner ruling open,
     §5.1 item 4 tail).
  4. **The RTORPA formation/mechanism question** — ercot-198 filed it,
     ercot-204 §A measured it and handed it to the owner UN-CHARTERED ("where
     the ORDC pricing region sits relative to the model's reserve
     representation"); this dispatch chartered its diagnose-first slice (E3,
     §4 below), which STOPPED at B0 per its own rule — the mechanism question
     REMAINS with the owner, sharpened by §4–§5.
  5. **T-3a** (settlement-basis C3b scoring) — owner-only rubric question,
     merely recorded (ercot-197 sitting record; ercot-198 §3). ercot-203b adds:
     ercot-202 §4 item 3's requested ruling addresses a gap that does not exist
     and can be closed as answered.

## 2. PHASE A(2) — WHAT WOULD A COMPLETE DECLARATION REQUIRE, AND IS IT REACHABLE? It
## is NOT reachable by any rule-13-admissible mechanism, and the caveated-declaration
## route is REFUSED BY SIGNED RULING — the terminal state is R-A's honest NOT-YET

ERCOT holds **no `complete` and no `final` marker** (rule 22; R-A card scope
line; re-affirmed at ercot-205). Determination **NOT-YET by signed ruling R-A**
(`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`, RESOLUTIONS
2026-08-13) — not re-litigated here. Precisely what fails, on the current
keeper's committed scorecard (`frontend/data/backcast/status/ERCOT.js`,
re-scored at the ercot-205 promotion):

* **C3a-2023 (`price_mean`): FAIL, −33.2 %** (model $42.97 vs actual $64.32,
  load-weighted). (The dispatch's −32.8 % is the ercot-165-era figure the
  L-SCAR card §4.1 carries; the object is the same.)
* **C3b-2023 (`price_shape`): FAIL, NRMSE 0.604 vs ≤ 0.20.**
* C3c: CAVEAT (ledgered ×3), not a fail. C6: PASS. **C7 is retired from the
  determination rubric** (v3.1 amendment, `scripts/calibration_verdict.py`
  header: "the C7 criterion … was retired at v3.1"); the dispatch-cited
  COAL_LIGNITE-2023 profile r 0.769 vs 0.80 survives only as a CLOSED matrix
  target with its cause attributed outside the offer surface and "no
  rule-13-admissible mechanism available to carry it" (§5.1 C7-closure note,
  ERCOT-142→143). It cannot block a determination.

**The cause is one object, and it is Q-B-closed model-class**: Aug+Sep 2023
carries **96.2 %** of C3b-2023's squared monthly residual (R-A §2; counterfactual
"every month EXCEPT Aug+Sep perfect" still fails at 0.592 ≈ 3× the bar), and the
same months are ~72 % of the C3a-2023 gap — the realized-RT scarcity formation
the record adjudicated model-class (C3c ledger; ercot-181 offer-family
exhaustion; Q-B closing the last quantity face at ercot-191).

**Reachability, by the rubric's own arithmetic (R-A §1)**: any FAIL forces
NOT-YET; `LEDGERABLE_CRITERIA = {"price_tail"}` (v3.1) with
`MAX_LEDGERED_CAVEATS = 1` already spent by C3c; the v3.0 tier guard refuses
model-class classification on load-bearing criteria, fail-closed. **There is no
rubric-legal route by which C3a-2023 or C3b-2023 becomes a caveat, and no
rule-13-admissible mechanism that moves them** (Q-B closed C3a-2023 spend as
automatic-and-final; R-A §2 measured C3b-2023 to be the same object with a ~0.59
ceiling for any lever that does not move Aug/Sep-2023; option R-C — an
equilibrium-conduct layer — is named in the card as a *program* decision outside
the calibration lane, and nothing in the queue reaches it).

**Therefore: "complete" is UNREACHABLE by any rule-13-admissible mechanism, and
the dispatch's hypothesized fallback — "the C6 attestation + a caveated
declaration" — decomposes as follows.** The C6-attestation half is **already
executed and passing** (ERCOT-144; six residual entries named in §1, attested at
every registered run since). The caveated-declaration half is **refused by
signed ruling**: R-B (widening the ledger so the 2023 price criteria become
caveats → CALIBRATED-WITH-CAVEATS) was recommended against and **NOT signed**,
the owner having already once REVERSED a 4-fail ledger adoption in-session at
ERCOT-144 ("not calibrated with caveats with 4 fails"); even R-B's smallest
variant (standing one-object reporting text) was not signed. What remains is
exactly what R-A adopted: **NOT-YET as the honest public claim, re-charter ERCOT
sessions off the 2023 price criteria, dashboards reporting the misses at full
magnitude.** An accepted-limit declaration beyond that is an owner act the
current signed record declines — a fact to report, not a gap to close.

## 3. PHASE A(3) — FRONTIER RANK 2: RECOMMENDATION ONLY (re-classification is
## owner-only, charter §6)

Facts, cited: `frontend/data/forecast/program-status.json` `open_frontier` rank 2
("ERCOT screen revenue level + in-year scarcity", L-SCAR / G-20/G-22, residual
≈56–66 $/kW-yr to SOM) stays OPEN per the 2026-08-14 V0-FAIL adjudication item
(iii) — "NOT entered … with the two lanes above in flight" (L-SCAR card foot).
Both lanes are now dead or stopped: **L-1 dead at V0**
(FINDING-ercot195: 4/14 folds vs 14/14; the rent series is a REGIME series; item
(iv) makes V0 the DO-NOT-REDO adjudication for tightness-conditioned
identification) and **L-2 stopped at Phase 0** (FINDING-ercot201: the E1
dispersion surface superseded on main — FFR-8B decomposed the gap
screen-asymmetric with the storage-AS term dominant, FFR-9A's storage-seed fix
then collapsed the inflator and E1 now TRACKS measured RTOLCAP — and the
dispatch's identification route is verbatim the one FFR-8B §4 pre-registered as
barred, adjudicated CLEAN at ffr-owner-sitting Addendum AG.1). The third
carrier the adjudication authorized — the regime-conditioning card, item (ii) —
was **never assembled** (§1.4 above), so "open with lanes in flight" is no
longer a true description on any reading. FFR-9A §3.4/§4 measures the live
error the price object now tracks as the **FFR-4/5 VRE/storage entry objects**
(missing VRE build: solar 10.0 vs 25.1 GW, wind 5.5 vs 12.7; into-2024 screen
overshoots ~11× once the phantom storage seed is gone), and FINDING-ercot201
§5 already recommended route (b) — re-point — with re-charter only on a
record-informed signature.

**Recommendation (not taken here):** re-point rank 2 at the FFR-4/5
VRE/storage entry objects, CARRYING the honesty bound as an accepted-limit note
on the ERCOT side — the missing screen revenue is λ-led (FFR-8A §2.3: 149/184
of 2024's λ>$100 hours carried adders ≤$10), so any ERCOT-side E1/adder repair
stays bounded single-digit-to-~20 of the ~50–70 $/kW-yr gap — and re-dispatch
the regime-conditioning card as the doc-only remainder. That is ercot-201's
recommended (b) plus the L-0 row's honest content relocated into the rank-2
detail text; entering the L-0 `readiness_limits` row itself remains the owner's
call, noting that its 2026-08-14 decline rested on a lanes-in-flight premise
that has since emptied.

## 4. PHASE B0 — THE REPRODUCTION TEST ON THE SETTLED BASIS: **NEITHER** parameter
## set reproduces both years; E3 STAYS ESCALATED and the lane STOPPED at B0

Per the precommit §3–§4 (pushed first), the FFR-8A §1.1(b) test re-ran with the
measured side settlement-closed by the ercot-198 guard. Exactly **one** hour
trips the guard across all three years — 2025 h4334 (archive RTORPA $414.12/h vs
settled hub RTSPP $54.96, λ $41.61) — reproducing ercot-198's record precisely
(2023 and 2024: zero flagged hours). Full-magnitude table
(`results/calibration/ercot206_e3_settled_reproduction.json`):

| year | series | h>$1 | h>$10 | h>$100 | max $ | mean $ | top-50 mean $ | verdict |
|---|---|---|---|---|---|---|---|---|
| 2023* | measured, settled | 294 | 108 | 17 | 650.8 | 0.945 | 127.5 | — |
| 2023* | fallback (μ=0, σ=1400) | 308 | 118 | 20 | 575.9 | 1.032 | 137.5 | (0.93–1.08×) |
| 2023* | NP6-576-ER table | 463 | 229 | 53 | 1082.7 | 2.639 | 315.5 | (~2.5× over) |
| 2024 | measured, settled | 78 | 26 | 4 | 252.7 | 0.203 | 33.9 | — |
| 2024 | fallback | 48 | 18 | 6 | 279.0 | 0.181 | 31.5 | **REPRODUCES** |
| 2024 | NP6-576-ER table | 77 | 37 | 11 | 639.5 | 0.521 | 89.8 | fails (a),(c): 2.65× |
| 2025 | measured, settled | 14 | 2 | 0 | 36.1 | 0.014 | 2.32 | — |
| 2025 | fallback | 4 | 1 | 0 | 10.3 | 0.003 | 0.44 | fails (a),(b): 0.19–0.29× |
| 2025 | NP6-576-ER table | 15 | 3 | 0 | 44.5 | 0.014 | 2.23 | **REPRODUCES** |

*2023 = pre-declared context row, zero verdict weight, `floor_active_mask(2023)`
honoured.

**REPRODUCES-BOTH: fallback false, table false → the pre-registered NEITHER
branch: E3 stays escalated; STOP at B0.** No build, no `--set`, no LP, no year
solved or scored, no run registered, no matrix cell or row edit (rule 28(b)
attaches to a mechanism test; none occurred). Contingent B1/B2 not entered; the
named evictions were not consumed.

## 5. WHAT B0 SHARPENS (the E3 record), AND THE RECOMMENDATION

1. **FFR-8A's 2025 anomaly is fully attributed.** "BOTH under-produce the 2025
   top-50 (0.4 / 2.2 vs 10.6)" was an artifact of the single unsettled archive
   print: settled, the 2025 top-50 is **2.32**, and the table sits at **0.96×**
   of it with counts 15/14, 3/2, 0/0. The archive-vs-settled distinction was
   the whole of the 2025 discrepancy, exactly as the reopen evidence predicted.
2. **The mixed cross-year result is now a clean YEAR-KEYED split, not noise**:
   the flat fallback reproduces **2023 (context: 0.93–1.08× everywhere) and
   2024**; the published seasonal table reproduces **2025 exactly** and
   over-produces the 2023/2024 deep tail **~2.5–2.6×**. FFR-8A §3.3's candidate
   causes (table vintage vs operating year, seasonal blending, floor
   interactions) now have a measured shape to discriminate against: the
   pattern is consistent with the published NP6-576-ER parameter vintage
   matching the 2025 operating year only.
3. **The parameter set is NOT the dominant 2024 formation term.** Evaluated on
   the REAL reserve telemetry, even the as-shipped fallback produces 48 h>$1 /
   top-50 $31.5 in 2024 — while the keeper's endogenous dual fires in 2
   hours at ≤$0.15. The dominant term is therefore the **model-side reserve
   basis feeding the curve** (the co-opt held-reserve solution vs realized
   RTOLCAP dips) — precisely the mechanism question ercot-204 §A measured and
   handed to the owner un-chartered. In 2025 the count gap IS parameter-keyed
   on the real telemetry (fallback 4 vs 14). B0 changes the shape of the open
   object; it does not close it.
4. **Recommendation (owner sitting; nothing armed here):** keep E3 escalated as
   the rule requires. If the owner wants it landed, the record now supports a
   **year-scoped** parameter question ("does the published table's vintage
   apply from 2025?") — which needs its own admissibility charter (year-keyed
   curve parameters are a new DOF shape under rules 20/23) — and NOT a blanket
   table arming, which 2023/2024 refute at 2.5–2.6×. The senior object remains
   ercot-204 §A's reserve-basis question; any charter should sequence that
   first (rule 1). **Promotion recommendation: NONE — nothing was built and the
   keeper is untouched.**

## 6. GOVERNANCE

Fences honoured as pre-registered (precommit §6): **Q-B FINAL** and **R-A**
cited, never re-litigated — 2023 appears above only in ceiling citations and as
the probe's pre-declared zero-verdict-weight context row (measured-vs-measured,
no solve; rule 13 clean — actuals entered comparison only, never any model
input). **V0 and ercot-201 DO-NOT-REDO honoured**: no tightness-conditioned
identification, no E1 dispersion repair, no measured-RTOLCAP-distribution
parameterization — measured RTOLCAP entered only as the reproduction test's
evaluation series (FFR-8B §4's validate-never-parameterize role). L-SCAR §4
must-nots honoured by construction (no screen mechanism touched; no ORDC
double-count; no refused channel; rule 22 — solve/score set empty, {2023, 2024,
2025} read only, 2022 untouched, no marker sought; rule 25 ERCOT only). Rule 27:
edit-local, files pushed as exact bytes, blob-verified ≥300-line files. Rule 15:
nothing to register (no run produced). Rule 28: no cell verdict changed, no row
minted; `scripts/check_mechanism_matrix.py` exit 0 at landing. No workflow, no
cron. **HYGIENE executed in this session** (dispatch item 3): the owner sitting
record's claim restored to **ercot-197** (its original claim, pack §A10.1 / PR
#3931) — two tokens changed (heading + closing consumed-line), bodies otherwise
byte-identical; T1-EXEC's ercot-202 entry untouched; the ercot-204 record note's
duplicated-heading condition is resolved (199/200 remain unspent). Keeper at
session start AND end: `2026-08-15-ercot204-rule26-delete`. **No PR opened**
(push-and-stop; the owner merges).
