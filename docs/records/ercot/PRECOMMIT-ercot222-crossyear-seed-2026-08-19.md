# PRECOMMIT — ercot-222: the CROSS-YEAR-SEEDED expectation variant, Phase-0 (read-only — NO LP, NO solve, NO arming) — seed form, instrument and gates pinned BEFORE any evaluation

**Session ercot-222 (owner-dispatched into the ercot-220/221 session window),
2026-08-19, branch `claude/ercot-220-lever-phase0-je3znm`.** Pushed and
blob-verified BEFORE the probe computes anything.

## 0. PREMISE CORRECTIONS AGAINST HEAD (recorded so the record is exact)

The dispatch text predates the merge reconciliation: at HEAD the keeper is
**`2026-08-19-ercot221-arm-adaptive`** — `ercot_storage_adaptive_expectation`
is **ARMED ON THE KEEPER** (cell **K**, promoted on the owner's standing
structural standard OVER the mechanical REJECTED-AS-ARMED on G-SHED; the
parallel session's R stamp and decline recommendation stand beside it,
reconciled at merge). This Phase-0 therefore adjudicates the seed term as a
**delta on the ARMED mechanism**. Second correction, owed by this session's
own records: the G-SHED kill hour 2024 h3066 is **May 8, 2024, HE18** (day
127 × 24 + 18), not "the Jan-2024 storm" as this session's finding/log/matrix
texts wrote — corrected in this session's edits.

## 1. THE VARIANT (pinned)

**What it models:** the fleet's expectation state does not reset at calendar
year boundaries — the measured evidence is the ercot-221 Amendment-1
disclosure (Jan–Feb 2023 evening asks parked at $5,000: post-Uri winter
memory) and RESEARCH-ercot221prep §2 M-2 (the Uri-inclusive 36-month
trailing statistic lands the 2023 offer level within ~11 % and the
2023→2024 direction).

**The pinned analytic fact that dictates the form:** under the armed
mechanism's frozen half-life (30 d), a Jan-1 *state* seed decays 2^7 ≈ 128×
by August — a state seed is structurally unable to reach the Aug–Sep object.
The only seed form the M-2 evidence supports is the statistic as a
**year-scale memory level** whose within-year decay is carried by the
rolling window's own composition (Uri exits a 36-month window in early
2024), with **zero new fitted scalars**:

- **Seed statistic (fixed ex ante; the M-2 scan already spent this
  selection freedom and is disclosed as such):** the mean of the top-100
  evening (HE17–22) hourly RT prices over the trailing 36 months. M-2
  scanned six candidates post hoc and this one was selected there — this
  precommit inherits that choice verbatim and spends no further freedom.
- **Purity convention (primary):** the window **ends Jan-1 of the solve
  year** — no solve-year measured price enters the seed. (M-2's as-scanned
  windows ended June-1 of the delivery year, which reads 5 months of
  solve-year measured prices; that form is computed and REPORTED as a
  fidelity check only, never the verdict basis.)
- **Within-year decay (no new parameter):** `P_seed(d)` = the same
  statistic over the span `[d − 36 months, Jan-1-of-solve-year]` — the
  history is frozen at Jan-1 (purity) while the window start rolls forward
  with d, so the seed decays exactly as the real memory's data ages out
  (Uri drops out during early 2024 by the calendar, not by a constant).
  If the span holds < 100 evening hours the statistic uses all of them; an
  empty span gives 0.
- **Composition (pinned):** `P_hat(d) = clip(max(P_seed(d)/VOLL,
  β·P_trail(d)), 0, 1)` — the carried pre-year expectation is a FLOOR under
  the within-year model-path memory (max, never sum: no double-count; the
  armed mechanism's event basis, half-life 30 d, β 3.0077, window h17–20,
  and every other convention UNCHANGED).
- **Forward analogue (the rule-13 argument, §4):** in a forecast, `P_seed`
  is computed from the model's OWN prior solved years' price paths (the
  sequential year loop already carries prior-year results); the measured
  version is the backcast overlay of the same quantity.

## 2. THE INSTRUMENT (pinned; all committed data, no solve)

- Measured response: the ercot-221 committed daily evening surface
  (`results/calibration/ercot221_daily_surface_2023.json`, the ERCOT-154/161
  discipline) → monthly implied-P p50s for 2023; the ercot-210 committed
  p98-tightness p50s ($2,714 / $1,281 / $990) as the 2023/2024/2025
  year-level anchors.
- Measured seed inputs: hourly actual RT (`_validation-source`, held
  2018–2026) — **2020-01-01 through 2024-12-31 only** as seed history
  (2020–2022 reads are DOF-ledgered per the dispatch; **2019 enters NO
  statistic**; 2025 measured prices enter no seed — 2025's seed window ends
  Jan-1-2025).
- Model-side feasibility inputs: the COMMITTED `ercot221_adaptive_B`
  sidecars (`adaptive_<yr>.parquet` for the armed P_hat/floors;
  `system_<yr>.parquet` for the May-8-2024 h3066/3067 shed context) and the
  keeper's own path for `P_trail`.
- Known data blocker, recorded (not re-checked): the 2022 NP3-965 offer
  corpus is UNRECOVERABLE from MIS (FINDING-ercot221-ab §7), so the 2022
  offer level cannot discriminate memory-vs-competition; this Phase-0 does
  not attempt it.

## 3. GATES (pre-registered; ALL must pass for the PASS branch; any FAIL ⇒ the negative branch — recorded at full magnitude, no card drafted beyond the negative record)

| gate | rule (numeric bar) |
|---|---|
| **G-R (reach, 2023)** | seeded `P_hat` monthly p50 on in-window days within ±35 % of the measured monthly implied-P in ≥ 5 of the admissible months INCLUDING both Aug and Sep; AND the Aug–Sep mean in-window seeded floor ≥ **$2,200** (the measured implied 0.67 × VOLL = $3,350 with the −35 % edge at $2,178; the starved arm topped at $1,850 mean-max) |
| **G-WINTER** | the disclosed motivating evidence must be reproduced: Jan–Feb 2023 seeded `P_hat` p50 ≥ 0.65 (measured evening asks parked at cap, implied 1.0; ±35 % edge) |
| **G-C (within-regime year control, decisive)** | the seed's year-level predictions vs the measured p98-cut anchors: 2024 within ±35 % of $1,281 AND 2025 within ±35 % of $990. (M-2's as-scanned June-1 values were +27 % and **+68 %** — the 2025 leg is the known-likely kill, pre-registered anyway: memory-alone flattening is M-2's own caveat and THE honest discriminator.) |
| **G-S24 (shed feasibility, committed sidecars)** | on the keeper's own 2024 path, the seeded floor schedule must (i) keep ≥ 95 % of all 8,760 hours at floor ≤ vom+$100 (the G-SAFE bar unchanged) AND (ii) NOT EXCEED the ercot-221 arm's floor at the known kill hours (May-8-2024 h3066 ± the evening window) — the arm's $878-max floor already manufactured 17.9 MW of shed there; any increase is the predicted kill |
| **G-S25 (self-extinction)** | 2025: ≥ 95 % of hours at floor ≤ vom+$100 (the armed mechanism's 2025 is byte-inert; the seed must not resurrect floors in a year whose measured level is $990 and whose keeper passes everything) |
| **LOYO** | structurally N/A, declared: the variant carries ZERO new fitted scalars (a pinned statistic + the frozen ercot-221 constants); the per-year seed values ARE the out-of-year predictions and G-C is their test |
| **STOP rule** | any gate FAIL ⇒ Phase-0 NEGATIVE: record at full magnitude, update the `ercot_storage_adaptive_expectation` cell evidence (no new row), Door D stands as the recorded floor, ERCOT bandwidth returns to the R-A re-pointed queue. ALL gates pass ⇒ STOP (no build, no arm) and draft the Phase-1 owner card: ONE change (the seed term) through the same seam, the rule-13 argument BOTH ways for the owner's decision, the ercot-221 §4 kill table unchanged with h3066 NOT grandfathered, and the ercot-162/G-BAT confrontation stated |

## 4. THE RULE-13 QUESTION (to be argued BOTH ways in the finding; the owner decides via the card — never this session)

**For admissibility:** the seed is an expectation INITIAL CONDITION, not a
target — a measured information-state of market participants (the market's
memory of realized prices is as real and measurable as a delivered fuel
price), entering formulaically, regenerating for a forward year from the
model's own prior solved paths, and responding to changed conditions (a
counterfactual 2021 without Uri produces a different seed). **Against:** the
seed is a statistic of measured PRICE OUTCOMES feeding the solve of adjacent
years — the quantity rule 13 most jealously guards; its forward analogue is
computed from a different object (model paths ≠ measured paths — this
Phase-0's own starvation result is the proof they differ 3×), so the
backcast "fit" with measured seeds would partly measure the seed's answer
content, not forward skill. Both arguments go to the owner unresolved.

## 5. FENCES

Read-only: no LP, no solve, no year scored, no run registered, no
`ScenarioConfig` field, no arming. Rule 22: 2020–2024 measured prices as
identification inputs only (data-not-score; DOF-ledgered in the finding);
2019 untouched by every statistic; no out-of-training year solved or scored
(the `complete` block is empty). Rule 25: ERCOT only. Rule 27: local edits,
blob-verify ≥300-line pushed files. Rule 28(b): the Phase-0 outcome lands as
evidence on the existing `ercot_storage_adaptive_expectation` cell (no new
row — no new field exists). DO-NOT-REDO honoured: the armed family's cell
adjudication (same basis/constants) is not re-run; Door A ×3, item 11 (Q-B),
the mid-band and regime lanes, B-2, and the ercot-219 aggregate route all
stand; the M-2 selection freedom is inherited-and-disclosed, not re-spent.
