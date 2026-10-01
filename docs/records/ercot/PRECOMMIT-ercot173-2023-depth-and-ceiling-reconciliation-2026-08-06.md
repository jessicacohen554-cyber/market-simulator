# PRECOMMIT — ercot-173: the 2023 depth object (Phase 0) + the ercot-172 C1+C2 ceiling reconciliation (limb 1)

**Session ercot-173, 2026-08-06. Charter: the owner directive of 2026-08-06 —
THE OBJECT IS 2023 LMP (C3a-2023 −29.9 % hub / −32.2 % scorer), it is a PRICING
problem, no fleet/volume lanes, no coal offer-curve work, ONE LP run
(control + arm, full span, one bundle each).** This document is committed and
pushed **before** any Phase-0 measurement, derive or capture runs. Every
threshold, coverage bar, verdict branch, gate assignment and prediction below
is fixed here and may not be moved after measurement, in either direction
(the ercot-162/165/167/168/169/170/171/172 discipline). The kill gates are
**inherited verbatim from `docs/PRECOMMIT-ercot172-maintenance-season-availability-2026-08-06.md`
§5 and are not renegotiable** (owner directive); this document assigns them,
it does not restate or amend them.

## 0. Objects — identified from COMMITTED artifacts before this document was written

All from the keeper `2026-08-05-run168b-year-curves` (bundle
`results/calibration/ercot168_yearcurves_B`, committed `hourly/` sidecars),
`data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`, and the
committed `results/calibration/ercot172_addendum_2023_topofstack.json`.
Reproduced exactly in-session before writing this document (object
identification, not attribution): actual 2023 RT >$200 = **181 h**, model
caught = **58**, **missed = 123**, model max over the missed set = **$196.5**
(demand-weighted zonal mean of the P1 system sidecar — the addendum's own
construction, to the cent). Actual >$1000 = **61 h**. Missed-hour calendar:
Aug 60, Sep 20, Jul 11, Jun 8, May 6, Mar 6, Oct 4, Nov 3, Jan/Dec 2 each,
Apr 1.

**The 2023 phantom shed census (the (c) object), keeper sidecar, P1:**

| model hour | timestamp (CST) | shed MW | model $/MWh | actual RT $/MWh |
|---|---|---|---|---|
| 4097 | 2023-06-20 17:00 | 213.0 | 4,993.4 | 3,288.78 |
| 5490 | 2023-08-17 18:00 | 555.9 | 5,051.3 | 5,046.42 |
| 5682 | 2023-08-25 18:00 | 1,266.0 | 5,000.0 | 4,314.08 |
| 5802 | 2023-08-30 18:00 | 1,428.7 | 5,027.7 | 4,844.59 |

Recorded honestly BEFORE measuring: unlike 2024's two fabricated spikes
(+$375 / +$227 day-mean error), these four sit on evenings where the actual
price itself is $3.3k–5.0k — at 5490 the model is high by **$4.9**. All four
are among the 58 caught tail hours. **A correction that clears these sheds can
therefore LOSE caught tail hours if the post-fix price falls through $200/$1000
— G-C3c and the tail counts will bind exactly as written; this is stated now so
the gate cannot be read as renegotiated later.**

**The 2024 limb-1 object is ercot-172's, unchanged**: h2827 (2024-04-28 19:00,
shed 565.1) and h3067 (2024-05-08 19:00, shed 550.3), attributed at MW grain in
`FINDING-ercot172` §3.

## 1. Instruments — imported verbatim, never re-implemented

* **`scripts/probes/ercot148_availability_capture.py` UNMODIFIED, as a
  subprocess** (the ercot-172 construction). Captures on the keeper bundle:
  **A_y** = keeper config verbatim (y ∈ {2023, 2024, 2025} as needed); **B_y** =
  only `ercot_dam_availability_{coal,gas}_event_cap=false` via `--set`; after
  the limb-1 build, **R_y** = keeper + the new reconciliation flag, for the
  seam proof and the no-LP per-limb attribution. `E = A − B` per plant is the
  event cap's removal, exact (the ercot-172 identity, G-EXACT/G-SEAM
  semantics).
* **`scripts/lib/sced_corpus_instruments.py`** (`load_corpus_year`,
  `restrict_hours`) + the committed
  `scripts/probes/ercot172_addendum_2023_topofstack.py` construction (SCED1
  curve MW/price columns, ONLINE status set, delivery = filename − 2) for the
  market side, widened from the addendum's Aug+Sep scope to **all 12
  delivery-2023 months** so the full 123-hour set is covered (scope stated,
  not silent).
* **`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`** on
  `ercot168_yearcurves_B` (2023) + the committed markup composition
  (`scripts/probes/ercot161_afternoon_wall_phase0._compose_markups`) for the
  model's P1 bid matrix — the ercot-163 model-side reconstruction, pointed at
  the current keeper, no LP.
* **`market_sim.data.outages`** — `ercot_thermal_dam_availability_hourly_series`
  (class-hour COP fraction) and the site-hourly parquet
  `data/raw/ercot-thermal-dam-availability-site-hourly.parquet` (live/rating
  MW) for the measured availability basis; `unit_outage_derate_factors` /
  `partial_outage_derate_factors` (the armed layers); CAMPD hourly
  (`data/raw/campd-unit-level/`) for f_CEMS at the four shed hours (the
  ercot-172 K-COP / K-CEMS certificates, both reported, never selected on).
* **Keeper committed sidecars** for model dispatch/prices. **Clock**: model
  fixed non-leap CST throughout; 2023 is a non-leap year so the ercot-172
  leap-label defect cannot recur, and any 2024 label is re-verified against
  the raw settlement series before use.
* Rule 22 `[R-HOLDOUT]`: 2023–2025 only. No year outside the training span is
  read, solved or scored. ERCOT holds no `complete` marker; 2022 and locked
  years stay quarantined.

## 2. Phase 0 — the attribution identities, fixed HERE

Scope set **S** = the thermal classes {COAL*, CC_REGULAR, CC_CHP, ST_GAS,
CT_PEAKER, CT_CHP}. Storage is OUT OF SCOPE (`ercot_storage_rt_offer_surface`
R, ercot-162 — structural, corroborated by ercot-172 §7, not re-litigated).
Renewables/nuclear are out of scope (verified elsewhere; reported if seen,
never attributed). Hour sets: **H123** (the missed set) and **H61** (actual
>$1000); every statistic below is reported on both.

**(a) The ceiling.** At each h ∈ H123: the model's energy-marginal offer
b*(h) = system price minus that hour's scarcity adders (sidecar
`reserve_price` / `ordc_adder` / `rtordpa_overlay` columns), and the marginal
tranche(s) = tranches with P1 bid within $2 of b*(h), named by class. The
cleared stack by class from `class_hourly_2023.parquet`. This is descriptive
(no gate) — it names what sets $196.5.

**(b) The depth split.** Per class c ∈ S at h:

```
V_m,c(h) = model capability with P1 bid < $200      (avail × pmax, capture A + bid matrix)
W_m,c(h) = model capability with P1 bid ≥ $200      (A_model,c − V_m,c)
A_model,c(h) = Σ avail × pmax                        (capture A)
A_mkt,c(h)  = Σ live_mw                              (COP site-hourly, class aggregate)
V_r,c(h) = market capability offered < $200          (SCED online HSL under the inc-curve
                                                      below $200, + OFFQS/OFFNS priced < $200)
W_r,c(h) = A_mkt,c(h) − V_r,c(h)                     (market capability priced ≥ $200)
X_c(h)   = V_m,c(h) − V_r,c(h)                       (the class's sub-$200 EXCESS depth)
         = [A_model,c − A_mkt,c] + [W_r,c − W_m,c]   (exact: AVAILABILITY face + OFFER face)
```

`M(h)` = the model's total undispatched sub-$200 capability over S
(cheapest-first fill against the sidecar class dispatch — the ercot-163 §2
construction) — the MW that must not be there for the price to cross $200.
`X(h) = Σ_c X_c(h)`. The construction-check identity `X_c = ΔA_c + (W_r,c −
W_m,c)` must close to 0.01 GW per class (stop-the-session if not).

**(c) The shed-hour face.** The ercot-172 tables reproduced at the four 2023
shed hours: per plant, E (the event cap's removal, captures A−B), f_window,
f_partial, f_ceiling, f_COP, f_CEMS, both certificates. Verdict per hour:
**SAME-DEFECT** iff E(h) ≥ shed(h) and the named plants' ceilings sit below
their same-hour CEMS (the ercot-172 signature); **OPPOSITE/OTHER** otherwise.

## 3. Licensing and neutrality — fixed here

* **L1 (corpus)** — the SCED corpus resolves ≥1 online row of S at **≥ 0.90**
  of H123. Below: the OFFER face is unlicensed (magnitudes may be surfaced,
  no verdict rests on them).
* **L2 (COP)** — the class-hour COP series is finite at **≥ 0.90** of H123 for
  a class, else THAT CLASS's availability face is unlicensed (the Oct-2023
  disclosure hole is known; 4 of 123 hours are October).
* **L3 (CEMS)** — for (c), every plant with E_p ≥ 25 MW must resolve in CAMPD
  hourly; unresolved plants are reported as one residual line and count
  against SAME-DEFECT (never silently dropped).
* **G-NEUT** — no population restriction is proposed by either limb; C1 and C2
  are year-agnostic, class-agnostic reconciliations of how existing layers
  compose, so the ercot-171 §3 / ercot-172 §3c gate is **not reached**. If
  Phase 0 were to produce a correction that restricts a population, it must
  clear G-NEUT (all three clauses) before it may be built — no exception.

## 4. Phase 0 decision rule — PRE-REGISTERED, branches in order, first to fire wins

The actionability fractions, stated before measuring (the handoff's demand):

1. **FILED-UNLICENSED** — L1/L2/L3 fail for the face a verdict would rest on.
   Name the blocking data; the unlicensed face yields no arm.
2. **FILED-REDIRECTED** — licensed, but **median over H123 of X(h)/M(h) <
   0.60**: the measured excess depth does not principally own the sub-$200
   ceiling; name which term does (demand, renewables, storage — all closed or
   out of scope — or the residual), re-point, and ship limb 1 alone.
3. **ACTIONABLE** — median X/M ≥ 0.60 **and** ONE face (availability ΔA or
   offer W_r − W_m, summed over S) carries **≥ 0.60 of median X** **and** that
   face resolves to a **named, zero-DOF** construction repair of an EXISTING
   armed mechanism (rule 19) or a fully-measured verbatim-conduct input in the
   ercot-168 pattern — subject to the standing hard fences (§6). Then:
   * buildable in-session → **limb 2 FOLDS into the same arm** (owner
     directive): the arm is declared **2-delta** pre-solve, per-limb
     attribution from flag-toggled NO-LP captures (the ercot-172 method),
     never a third solve;
   * not buildable in-session → **ACTIONABLE-SPECIFIED**: the correction and
     its kill gates are specified for a successor charter (the ercot-172
     pattern), and limb 1 ships alone, saying so.
4. **FILED-NULL** — otherwise. Real, not attributable to a single admissible
   correction on committed data. Ship limb 1 alone and say so.

Why 0.60 twice: the majority-plus-margin standard of ercot-170/171/172 — below
it a mechanism premise rests on an unattributed aggregate (the ERCOT-163 §3
prohibition), and a "correction" would be tuned to a residual, not a measured
fault (rule 13).

## 5. Limb 1 — the arm, its predictions, and the seam proof, fixed BEFORE the build

**Mechanism** (`ercot_dam_availability_event_cap_reconciliation`, ONE new
`ScenarioConfig` gate, default **False**, matrix row in the same PR; zero
fitted scalars): inside the existing ERCOT-148/149 event-cap block only —

* **C1 (grain repair)**: `partial_outage_derate_factors` keys by the extract's
  own `(oris_code, plant_group)` instead of `oris_code` alone, under the gate,
  in both ERCOT consumers (the apply block and the cap block).
* **C2 (rule-19 reconciliation)**: the cap ceiling composes its measured
  layers by `np.minimum(...)` instead of the product — two resolutions of one
  phenomenon reconciled, exactly the way the cap itself already composes with
  the COP layer.

Never two cap layers; the ERCOT-148/149 precedence is reconciled, not
repealed.

**Pre-solve predictions, recorded now:**

* **P-C1-INERT**: enumeration of the committed bins sheet shows **no
  partial-extract plant code carries more than one `plant_group` bin** (W A
  Parish's gas units live under split code 34702), so C1 changes **no bin's
  factor on the current fleet** — it is wiring correctness, and the whole
  measured movement is C2's. Asserted programmatically in the seam proof.
* **P-2024**: from the committed FINDING-ercot172 §3 tables, C2 raises
  h2827 ceilings at W A Parish (0.2539→0.3630), Martin Lake (0.3347→0.5020),
  Guadalupe (0.2410→0.4820), J K Spruce (0.0791→0.2080); restored capability
  ≈ **+0.9 to +1.3 GW ≥ shed 565** → the 2024-04-28 shed is predicted to
  CLEAR. At h3067 only Martin Lake moves (0.1673→0.3158, COP-capped);
  restored ≈ **+0.3 to +0.5 GW < shed 550** → the 2024-05-08 shed is
  predicted to SHRINK and may persist. G-SHED (2024 count must FALL) is
  predicted 2 → ≤1.
* **P-C3a-2023** (the owner's object, reported FIRST in the write-up
  whatever it does): availability can only rise under C2, so the 2023 price
  moves **≤ 0** (down or unchanged). Movement concentrates on the four shed
  hours (J K Spruce's partial windows cover 2023-06-20 and 2023-08-30; none
  cover Aug 17/25 — those two are predicted UNTOUCHED by limb 1). Each
  cleared VOLL hour removes ≈ $0.5–0.6 from the annual model mean ⇒ predicted
  **C3a-2023 delta: 0 to roughly −1.5 pp (more negative)** from limb 1 alone.
  Limb 1 is NOT the 2023 lever; per rule 1 it is judged on structural
  fidelity and the pre-registered gates, not on C3a-2023 flipping.
* **P-2025**: 2025 carries the same window/plateau overlaps (Limestone,
  Parish, Martin Lake, Fayette, Spruce); C2 raises in-window ceilings there
  too. G-SPAN's 0.5 % class-energy leg and G-COAL148's 0.5 TWh bound are live
  and will decide; no prediction is made that they pass.

**SEAM PROOF (no-LP, BEFORE the solve; stop-the-line on failure):**

* **SP-1** — capture R_y (arm) equals, on every scoped tranche,
  `min(B_y, ceil_min)` where `ceil_min` is the min-composed class-grain
  ceiling computed independently from the loaders (tolerance 1e-6, float32
  save; y = 2023 and 2024).
* **SP-2** — every tranche outside `_evcap_scope` is byte-identical A_y vs
  R_y.
* **SP-3** — C1-inertness: class-grain and plant-grain partial dicts induce
  identical per-bin factors on the current bins sheet (P-C1-INERT asserted).
* **SP-4** — gate-off no-op: with the new flag at its default the composed
  availability is byte-identical to capture A_y (the flag is registered in
  the cache-key default-drop list, the ERCOT-148/149 treatment).

**Gate assignment (inherited verbatim, PRECOMMIT-ercot172 §5):** **G-BIT is
declared N/A NOW, pre-solve** — the correction is a year-agnostic rule
touching all three years (§3c(a) forbids a year scope), so **G-SPAN** replaces
it, exactly as ercot-172 fixed. Live gates on the FULL arm: G-SPAN, G-SHED,
G-SPUR, G-C3c (61/181, 25/53, 3/31 must not degrade), **G-COAL148** (coal
dispatch above the measured product-ceiling may not rise > 0.5 TWh in any
year, scored with the committed ercot-149 probe machinery against the
INCUMBENT product ceiling — the comparability basis of the 4.36/4.98/5.01 TWh
record), G-DOF (zero new fitted scalars), G-D2, LOYO (recorded: the rule is
parameter-free — nothing is identified on any year — so leave-one-year-out
has no fit to hold out; per-year deltas are reported in its place). Failing
any live gate ⇒ **REJECTED-AS-ARMED**, reported as such, run still registered.

**One LP run** (owner directive): control (fresh same-HEAD keeper replay) +
arm, each `--year 2023 2024 2025`, one bundle each, both registered whatever
the outcome (rules 15/16). If limb 2 folds, the arm is 2-delta and per-limb
attribution is by flag-toggled no-LP captures only.

## 6. Hard fences (standing; none renegotiated)

Whatever Phase 0 measures, this session will NOT propose: a per-hour
telemetered-HSL or COP cap on dispatch (rule 13); an aggregate capability cap
(`energy_online_capability_cap` R, ercot-159); any storage offer surface
(ercot-162 R, structural); any coal offer-curve change (owner fence — every
coal offer lane closed; the only coal touched is AVAILABILITY at
scarcity/shed hours, which is the price path); re-pricing of cheap CC
(ERCOT-152 no-op, ERCOT-158 upheld); per-year CT re-identification (ERCOT-147
REFUSED); the West/Panhandle topology split (CLOSED); any re-arm of
`ercot_storage_rt_offer_surface`; any repeal of the ERCOT-148/149 precedence.
The CC-headroom per-unit crosswalk stays FILED-UNLICENSED (ercot-170); its
extreme-hour CLASS-AGGREGATE face is exactly what §2(b) measures and is NOT
blocked. ercot-172's C3 (ceiling floored at contemporaneous output) stays
REFUSED under rule 13.

## 7. The ercot-167 SOC-reserve re-gate — a RE-SCORE, not a re-arm

`ercot_storage_as_soc_reserve` is ALREADY ARMED on the keeper (owner-promoted
at ercot-167); it is in both control and arm. Nothing is built for it. Its two
fired kills are re-scored on this session's A/B, definitions fixed now:

* **RG-1 (was G4-2024)**: CLEARS iff on the arm (i) both 2024 spike days'
  day-mean |model − actual| falls vs control, (ii) C3a-2024 does not degrade
  more than +1.0 pp A→B, and (iii) G-SHED holds (the kill's named root — the
  maintenance-season fabricated spikes — is then corrected with the SOC
  reserve still armed).
* **RG-2 (was G3-2025)**: the 2025 spurious count on the arm vs control, with
  hour 2025-10-21 19:00 reported by name. Honest pre-statement: this kill was
  a $43 threshold graze adjacent to newly-captured real hours and never
  localized to the 2024 defect; it is NOT expected to clear via limb 1, and
  will be reported at whatever it reads.

## 8. Governance

Rule 25: ERCOT-scoped throughout. Rule 15/16: every run registered, all three
years in one bundle, never a single-year keeper. Rule 22: training span only.
Rule 23: no derive re-run; the frozen extracts are read as they stand. Rule
27: every push touching a ≥300-line file is blob-verified; no bulk rewrite of
core files. Rule 28(b)/(c): the new gate's matrix row lands in the same PR;
matrix §5.1 and the two event-cap cells (carrying ercot-172's open-root-cause
note) are re-stamped with this session's outcome, and the
`ercot_storage_as_soc_reserve` cell gets the re-gate result;
`check_mechanism_matrix.py` exit 0 and `node --check` on the matrix JS before
push. Environment: GTC clean partition regenerated before any solve; years
sequential within an invocation (rule 12), control/arm as separate
invocations, sequential if memory requires (~10 GB RSS each on a 15 GB box).

**Next shorthand: ercot-174.**
