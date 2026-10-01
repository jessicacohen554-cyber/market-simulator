# PRECOMMIT — ercot-168: per-year 2023 re-identification of `coal_perplant_offer_curves` from the delivery-2023 SCED corpus

Committed BEFORE any solve (the ercot-162/165/167 discipline). Charter:
mechanism-testing-matrix §5.1 **item 12** (owner-chartered at ercot-166; owner-adjudicated
2026-08-05 — **OPTION A selected**). Governance basis, quoted from the adjudication, not
re-litigated: *a rule-14/23 data-vintage fix of an armed K mechanism (the ercot-157 corpus
re-upload dissolves ERCOT-143's closure premise "no 2023 SCED exists"), NOT a claim that "2023
bid differently" — same modal derive, fed the year's own rows, zero new DOF.* No commodity
backing is claimed for the lignite repricing (Oak Grove measured fuel ~$14.5/MWh vs its $60-class
top; §1f). OPTION B (spread-regime-conditional offer top) stays DEFERRED as the forecast-side
successor.

## 0. Mechanism (single delta; zero fitted scalars)

`coal_perplant_offer_yearly=true` (new gate, default off; requires `coal_perplant_offer_level`
armed — it refines that mechanism and hard-errors without it) resolves
`constants.COAL_PERPLANT_OFFER_CURVE_YEARLY_BY_ISO[iso]` — a **year-keyed** per-plant measured
curve table `{year: {plant: ((months, hours, curve), …)}}` — into the new config field
`coal_perplant_offer_curves_yearly`. Consumption (`fleet.legacy_bins.apply_coal_tranches`, which
gains an optional `year` argument): for a solve year PRESENT in the table, each CAMPD coal
`_committed`/`_econ*` tranche of a listed plant is priced per (month × hour-window) cell at the
capacity-weighted measured price of its capacity window on that cell's plant curve — the SAME
window mapping as `_coal_perplant_levels`, evaluated per cell; `mc[g, t]` gets the cell level on
the cell's hours (window slice-adds on the 8760 axis; no per-hour Python loop, rule 2).
`_mustrun` (ERCOT-137 measured margin) and `_peak` (ERCOT-140 gas-parity margin) rows stay
UNTOUCHED — each end of the curve keeps its own measured owner (rule 19). A solve year ABSENT
from the table (2024, 2025 — the table carries **only 2023**) falls through to the armed static
`coal_perplant_offer_curves` exactly as today: **2024/2025 are unchanged BY CONSTRUCTION and
verified by kill gate G-BIT, never assumed.** Levels remain all-in (fuel/VOM folded in,
emissions adders on top), so any fuel-embedded share of a measured level move rides the measured
level itself — no composition with the monthly fuel channel on these rows (one owner per row).

**The identification (frozen derive, rule 23 — re-run cite: the ercot-157 delivery-2023 corpus
landing).** `scripts/data/derive_coal_perplant_offer.py` gains a `--year 2023` mode reading
`data/raw/ercot/SCED/` (315 shards, publication-month-keyed, delivery = filename − 2; the
delivery-year filter drops the 2022-12-31/2024-01-* bleed) under the ercot-123/144 row filters
(CLLIG, ONLINE, HSL>0, HSL>LSL, HASL & net-output non-null). Timestamps are converted CPT →
fixed CST **at derivation** so emitted hour windows sit on the model's own clock (the
ercot-166 DST-defect class, closed at the source; Aug–Oct are fully inside DST, so the measured
CPT h0–h9 overnight block lands as CST h23–h8).

Construction, one sentence, applied uniformly to every resource and month with no scope
carve-outs: **the effective curve of (resource, month, hour) is the hour's modal price-tuple
curve iff that key repeats on a strict majority (>0.5) of the month's live days at that hour,
else the month's pooled modal curve** — the ercot-144 modal/time-stability principle
(most-submitted real curve; "repeats identically ×1436" was its license) applied at the corpus's
own submission grain (TPOs are hourly operating-hour objects) with the mode's own day-grain
dominance convention. Identical adjacent cells merge into `(months, hours, curve)` windows;
resources merge to plants per `merge_plant_curve` per cell; a plant with zero live resources in
a month (Coleto Mar–Apr outage) carries its year-pooled 2023 curve for that month (level is
moot under its outage availability). Provenance JSON records every admitted hour cell WITH its
day-share (the convention-boundary disclosure: §1e).

**Phase-0 grain amendment, recorded before any solve (the ercot-167 amendment pattern).** The
charter's menu was month- vs season-resolved, decided FROM THE DATA. The data's answer (§1c):
at month grain the modal construction returns the flat day curve for Oak Grove in EVERY month —
the Aug–Oct repricing is a **within-day submission regime** (overnight rows ~90 % share carry
the $60-class curve; day rows keep the standing curve), so the chartered month/season menu
cannot reach the chartered C7 object at all. The construction above is the same modal derive at
the offer's native grain with a day-majority stability license. ERCOT-143 §3's "the corpus
forbids any hourly/seasonal/diurnal identification" was **coverage-scoped to the 2024/25
probe-day corpus** (h0–h8 = 8.44 %, single subset, no 2023) and does not bind the full-year
delivery-2023 corpus (35.8 M rows, 365 days × 24 h); the ERCOT-143 SLOPE closure itself is not
reopened — no within-plant slope is transplanted, no fleet pooling occurs, every curve is the
plant's own verbatim submission (2023's own rows only).

## 1. Phase-0 measured facts (all from committed corpora, no solve)

- **(a) Corpus.** All 315 delivery-2023 shards on disk carry the FULL 188-column schema
  including `Submitted TPO-MW/Price 1..10` (the ercot-157 log's slim was measured but its push
  413'd; the owner landed the raw shards — verified directly against the parquet schema).
- **(b) Month-grain modal tops (per resource, delivery month).** Real year-specific levels the
  keeper's 2024/25 extrapolation cannot see: Martin Lake units step **+$1.9** at Aug 1
  (19.55/20.38/19.13 → 21.41/22.29/20.95) and STAY there through Dec; San Miguel steps 20.00 →
  41–43 at May and stays; Major Oak steps 10.01 → 13.01 at Jun (→ 26.35/27.33 Dec); Oak Grove's
  month-modal top is $4.49/$4.17–4.19 in EVERY month (the flat ~$4.4 line — vs the keeper's
  extrapolated $8.37–9.64 curve); Parish/Limestone/Coleto/Spruce/Fayette month-modals move at
  the $1 scale around their keeper levels.
- **(c) The Aug–Oct object (the C7 driver).** Oak Grove, both units, delivery Aug/Sep/Oct ONLY:
  a clean two-curve within-day regime — overnight (CST h23–h8, = CPT 00:00–09:59) modal
  `[(0, 3.16), (348, 60.26), (825, 60.26), (880, 60.26)]` (unit 2: step at 455; October:
  **$61.46**) at 0.77–1.00 of overnight rows; day (h9–h22) keeps the standing $4.4x curve at
  ~1.00. The step boundary 348/455 MW = the units' LSLs — under the derive's step convention
  the merged plant curve overnight is ~all-capacity @ $60.26, so committed/econ window levels
  land at $60.26 while `_mustrun` (45 % = 808 MW ≈ the measured LSL floor, ERCOT-142) keeps its
  ERCOT-137 owner: at ~$20 overnight LMPs the LP holds exactly the mustrun block — the measured
  two-shift, executed through price formation; the Aug 15–19 pause reproduces endogenously
  (those scarcity nights price ≫ $60). **The $60-class top PERSISTS through delivery-Oct
  ($61.46) and reverts at Nov (0 % high-top rows)** — the month-vs-season question, answered:
  the regime is month-resolved {Aug, Sep, Oct} × within-day windowed. November through
  December: standing curve. May/Jun carry a faint sub-majority overnight trial (8–22 % of
  rows) — the mode correctly refuses it.
- **(d) Fleet check.** NO other plant runs a $60-class overnight regime in Aug–Oct. The
  sub-bit two-shift (Martin Lake 1,254 night / 2,122 day, FINDING-ercot166 §4) is carried by
  the +$1.9 LEVEL step (its top moved from just-below to just-above the ~$21.3 overnight LMP —
  SCED backs it down at the margin), not by a repricing spike. JKS/LEG/WAP/Fayette-J02 carry
  year-round noisy high-top VARIANTS (modal shares 0.08–0.5 — sub-majority, refused by the
  construction, disclosed in provenance); TNP runs a real overnight $10.01 / day $13.01 split
  Oct–Dec (admitted; dispatch-inert at ~$20 LMPs); Calaveras/Sandy-Creek carry a handful of
  admitted majority cells (§1e).
- **(e) Convention-boundary disclosure.** Of 643 (resource, month, hour) cells whose hour-modal
  differs from the month-modal, 486 sit at day-share ≤ 0.5 (refused) and 157 above (admitted).
  The Oak Grove target cells sit at 0.55–0.97 — robust across any majority-band reading. ~15
  admitted cells sit in (0.5, 0.55] (JKS2-Sep, WAP-G5/G6-Dec/Jan, SCES-J01 single hours) — the
  cells a stricter convention would flip; they are single-hour, small-plant, shoulder-month
  objects, and every one is recorded with its day-share in the derive provenance. The
  convention (>0.5 = strict day-majority) is the mode's own dominance definition, not a tuned
  threshold; it is declared here as a construction convention, with this sensitivity record.
- **(f) Fuel decomposition (charter Phase 0c).** F923 2023 delivered coal receipts exist for
  only Fayette (1.72–1.77 $/MMBtu Aug–Oct, flat), JK Spruce (1.82–1.90, flat) and San Miguel
  (volatile captive series, no Aug step; its offer step was May); Oak Grove / Martin Lake /
  Parish / Limestone / Coleto / Sandy Creek / Major Oak have NO 2023 receipt rows (mine-mouth —
  model fallback LIGNITE_PRICE_2023_25 = 1.45 $/MMBtu ≈ $14.5/MWh at Oak Grove's heat rate,
  verified against the EIA Annual Coal Report at ERCOT-142). **No measured fuel series moves at
  any offer step: the Aug–Oct repricing is conduct, not commodity** — per the owner
  adjudication, no commodity backing is claimed; the fuel side stays wholly owned by the armed
  `coal_plant_monthly_pricing` channel, and the all-in level replacement on committed/econ rows
  composes with it nowhere (one owner per row).
- **(g) Baseline (the ercot167b keeper, scorer basis).** Determination NOT-YET on {C3a 2023
  −32.2 %, C3b 2023 0.603 + 2024 0.206, C7 2023 COAL_LIGNITE cv_ratio 0.331 (profile_r 0.897
  passes; model_offpeak_cv 0.019 vs actual 0.057)}; C3c ledgered CAVEAT ×3 (61/181, 25/53,
  3/31); spurious tail 3/7/1; shed hours 4/2/0; C1/C2/C4/C6/C8 PASS; D-1 COAL_PRB 2023
  cv 0.737 / r 0.996.

## 2. The runs (rule 16 full-span A/B; rule 12 sequential — 15 GB box, ~10 GB/solve)

1. **PROBE (2023-only, THROWAWAY diagnostic — rule 16: never registered):**
   `python scripts/replay_keeper.py results/calibration/ercot167_socreserve_B
   --out-dir results/calibration/_ercot168_probe23 --years 2023
   --set coal_perplant_offer_yearly=true` — validates engagement (the applied-windows log
   line), LP feasibility, the C7 direction, and the shed count on the distinct-design year
   before spending the full span.
2. **Run A — control, fresh same-HEAD replay** (ercot150-K2 lesson): full span
   `--years 2023 2024 2025`, config UNCHANGED,
   `--out-dir results/calibration/ercot168_control_A`.
3. **Run B — arm**: same, plus `--set coal_perplant_offer_yearly=true`,
   `--out-dir results/calibration/ercot168_yearcurves_B`.
   Both A and B are registered on the dashboard whatever the outcome (rule 15; a rejected arm
   is marked "(PROBE)").

## 3. Pre-registered gates (verdicts read A→B; kill gates bind, no post-hoc softening)

- **G-BIT (KILL — the charter's own kill):** 2024 and 2025 solve outputs BYTE-IDENTICAL A→B
  (sha256 over the per-year hourly sidecars and price series). The yearly registry carries only
  2023, so any 2024/25 divergence is a wiring leak and kills the arm. Verified, not assumed.
- **G-TGT (target, 2023):** C7 COAL_LIGNITE cv_ratio moves UP from 0.331 toward the ≥0.5 gate
  (report the value; a full clear flips the keeper's C7 cell). Success is the cv-leg clearing
  with **G-SHAPE** holding; a non-reaching improvement is reported honestly, not spun.
- **G-SHAPE (KILL):** 2023 COAL_LIGNITE profile_r stays ≥ 0.80 (baseline 0.897) — the cv fix
  must not buy its ratio by breaking the shape correlation (the ERCOT-142 feasibility lesson:
  too much backdown breaks the r-leg).
- **G-NEWROWS (KILL):** C7/D-1 gains no NEW failing (year, class) rows in any year — protects
  COAL_PRB 2023 (cv 0.737, r 0.996) against the Martin Lake +$1.9 effect, and every other
  gated class.
- **G-NOREG (KILL):** C1 (both coal classes and all free classes), C2, C4, C6, C8 hold PASS in
  B in all three years; 2023 C3a within ±1.0 pp and C3b within ±0.02 NRMSE of A in the WORSE
  direction (improvements unbounded). 2024/2025 are covered by G-BIT (exact zero movement).
- **G-SPUR (KILL — zero-spurious):** 2023 spurious tail hours (model settlement > $200 where
  actual RT ≤ $200) do NOT increase A→B (A expected ≈ 3).
- **G-SHED (KILL — no fabricated shed):** 2023 hours with system slack > 1 MW do not increase
  A→B (A expected 4).
- **Report-only:** the 2023 Aug/Sep monthly load-weighted bias movement (the charter expects a
  MODEST belly lift — coal is marginal in a bounded overnight hour set; this does NOT close the
  −32 %, whose tail mass stays the rubric-v3.0 C3c model-class ledger); C3c counts per year;
  lignite/PRB class TWh and D-1 rows; the admitted-cell effects outside Oak Grove (TNP/JKS/SCES
  cells — expected dispatch-inert or small).
- **DOF ledger:** free_parameters_added = 0 (every curve a verbatim submitted object; windows
  from the data's own modal dominance; months/hours calendar objects; no swept scalar). The
  existing `coal_perplant_offer_curves` ledger entry's "2023 application is a declared
  extrapolation" note is RETIRED by this measured replacement when the arm lands; the
  day-majority convention is declared with its §1e sensitivity record. LOYO (rule 22): the 2023
  table consumes only 2023 rows and the 2024/25 identification is untouched — leave-one-year-out
  reduces to the per-year gate table above; any promotion decision reads it per-year.
- **Forward story (rule 13):** the yearly table is a backcast-year measured market input in the
  F923 delivered-fuel pattern — it regenerates for any year whose disclosure corpus exists and
  responds to that year's market conditions; forecast years carry the standing (latest-corpus)
  identification unchanged. The regime's forward driver (OPTION B, a spread-regime-conditional
  top) is the deferred forecast-side successor and is NOT armed here.

## 4. DO-NOT-REDO honored

Lignite offer SLOPE stays closed as adjudicated on 2024/25 conduct (ERCOT-143 — nothing here
identifies a within-plant slope; verbatim per-plant curves only); `coal_min_load_floor` both
grains stays rejected (no floor is added — the backdown is priced, not forced); lignite daily
unit commitment stays refuted (continuous turndown through the LP's own dispatch);
coal seasonal LEVEL split stays refuted (no model-side seasonal reweighting — measured curves
only); `coal_offer_level_rebasis` stays R; `tranche_startup_amortization` stays G; NO extension
to CTs (ERCOT-147's refusal stands — coal's modal identity ×1,436 vs CT 11/160 is exactly the
license line this derive lives on).
