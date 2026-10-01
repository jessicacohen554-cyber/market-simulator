# PRE-COMMIT — ERCOT-144: the coal mid-band onto MEASURED PER-PLANT offer levels (DOF-retirement lane)

**Date** 2026-07-31 · **ISO** ERCOT · **Lane** ercot144-coal-perplant-offer ·
**Phase** 2 (mechanism + full-span arm) ·
**Keeper under test** `2026-07-30-ercot140-coal-peak-offer`
(bundle `results/calibration/ercot140_coal_peak_arm`) ·
**Chartered by** ERCOT-143's per-plant measurement
(`docs/DIAGNOSIS-ercot143-lignite-offer-slope-2026-07-30.md` §2), owner-issued
as the ERCOT-144 DOF lane serving C6 (matrix §5.1 queue item 2 — NOT a gate
chase) · **Phase 1** `scripts/probes/ercot144_coal_perplant_offer.py`
(artifact `results/calibration/_ercot144_scratch/phase1_full.json`) ·
**Derive** `scripts/data/derive_coal_perplant_offer.py` ·
**Precommit pushed BEFORE any solve** (rule 15/26b discipline).

This document is fixed before the LP runs. Its predictions and decision rule
are the falsifier; the run is scored against what is written here.

---

## 0. The objective, stated so it is not misread

Success is **RETIRING RESIDUAL DOF ENTRIES** (the keeper's
`calibration_attestation.json` carries `n_residual = 8`; the target is 6),
which is what unblocks C6 and the determination. It is **NOT** moving
C3a/C3b/C3c/C7. Rule 1 `[R-STRUCT]` governs: a measured, structurally-correct
offer form stays in even if gates regress, and must not be rejected because
the residual did not move. Conversely C6 is not attested to buy a
determination while residual entries stand — they are retired here, by
measured replacement (rule 21).

## 1. Phase 1 — the per-plant quantification (no LP), and the decision

Measured per plant on the pooled 60-Day SCED `Submitted TPO` corpus (modal
curves; ERCOT-136 section_b's construction) against the current keeper's own
curve at the LP seam, all 10 coal plants, mid-band (committed+econ)
cap-weighted, 2024 (the fully-measured year):

| plant | model capw | measured level | Δ (model − measured) |
|---|---|---|---|
| Oak Grove | 15.68 | 9.07 | **+6.61** |
| JK Spruce | 22.30 | 17.74 | **+4.55** |
| Coleto Creek | 21.01 | 17.96 | **+3.05** |
| W A Parish | 21.52 | 18.92 | +2.60 |
| Limestone | 20.35 | 18.51 | +1.84 |
| Major Oak | 16.46 | 14.73 | +1.73 |
| Martin Lake | 20.52 | 21.79 | −1.27 |
| San Miguel | 35.76 | 42.99 | **−7.23** |
| Sandy Creek | 19.66 | 35.28 | **−15.62** |
| Fayette | 21.33 | 50.94 | **−29.61** |

The model's per-plant dispersion is wrong **in both directions** — too dear on
the plants ERCOT-142/143 studied (Oak Grove +6.6), far too cheap on the
jointly-owned plants whose co-owner blocks really are offered at $100–150
(Fayette J02 resources) and $27–65 (Sandy Creek). The ERCOT-138 fleet-aggregate
exoneration (−1.6..+3.9 $/MWh through the crossing band) holds **because these
errors cancel** — 138 measured the fleet, 143/144 measure the plants; the two
facts are not in conflict and this lane is not an ERCOT-138 re-run (rule 26a).

**Decision: a per-plant identification is admissible and worth an arm.** The
measured object is each plant's own merged modal submitted supply curve —
verbatim conduct, zero fitted parameters, time-stable across subsets AND years
(Oak Grove's modal curve repeats identically ×1436; Major Oak ×2730/×2784 at
$14.73 in both years; Martin Lake, Sandy Creek J01/J03, Parish G5 likewise
stable). Stability is the license for a **LEVEL** identification; the corpus
**forbids** any hourly/seasonal/diurnal identification (h11–h22-only in three
of four subsets, pooled h0–h8 = 8.44 %, no 2023 disclosure — ERCOT-143 §3).

## 2. The arm — ONE mechanism, one bundle

`coal_perplant_offer_level` (new `ScenarioConfig` gate, default off,
ERCOT-scoped registry `constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO`): every
CAMPD coal `_committed`/`_econ*` tranche is repriced to the capacity-weighted
measured price of its capacity window mapped onto its own plant's merged modal
TPO curve, applied on the BASE cost at the ERCOT-137/140 seam
(`legacy_bins.apply_coal_tranches`), exiting before the fuel-frac discount.

* **Fuel-invariant BY MEASUREMENT (mid-band only).** The measured mid-band
  levels did not co-move with delivered gas (+46 % 2024→2025 while Oak
  Grove/Major Oak/Sandy Creek J01/J03 repeat identical curves) or with coal.
  The curve's bottom (`_mustrun`, ERCOT-137 coal-anchored) and top (`_peak`,
  ERCOT-140 gas-anchored) keep their own measured fuel responses — the offer
  surface retains fuel response at both ends in a forecast.
* **The San Miguel −$249 block** (220 MW at the offer floor) is a price-taker
  self-schedule signal, not a marginal cost: it is excluded from window level
  statistics (`COAL_PERPLANT_SELF_SCHED_FLOOR`), never ported into an LP bid.
  Its committed/econ windows sit above the block and price at the measured
  $42–43.
* **`_mustrun` and `_peak` are UNTOUCHED** — ERCOT-137 and ERCOT-140 are
  measured keeper mechanisms and each end of the curve keeps its own owner.
  Resulting non-monotonicities (e.g. Oak Grove committed $9.32 below mustrun
  $13.14; Fayette econ $80 above peak $39–45) are declared, not smoothed — the
  LP dispatches on price regardless of stacking order.

### 2.1 Rule 19 `[R-ONE-MECH]` — REPLACEMENT, enumerated from the keeper's own config

Owners of the CAMPD coal committed/econ rows in the ercot140 keeper:

| mechanism | touches these rows? | disposition |
|---|---|---|
| `offer_curve_by_group` COAL_* band multipliers (25 scalars) | YES — set the band HRs | **REPLACED — groups STRIPPED from the armed config** |
| PRB/lignite gas-keyed supply sigmoids (`COAL_SIGMOID_DEFAULTS[ERCOT]`, 8 scalars) | YES — fuel-frac discount | **REPLACED — flags disarmed in the armed config** |
| `coal_econ_marginal_hr_bound` | YES — clamps econ multipliers UP | **stands down (nothing left to clamp) — disarmed** |
| `offer_curve_smoothing_*` | structure-only on coal (econ slicing) | with groups stripped the coal econ block is a single tranche; smoothing stays armed for gas |
| `coal_offer_net_revenue_margin` (ERCOT-137) | no — `_mustrun` only | untouched |
| `coal_peak_offer_margin` (ERCOT-140) | no — `_peak` only | untouched |
| `coal_tranche_{1,2,3}_*` (`coal_take_or_pay_tranches` ledger entry) | **NO — legacy split_coal_tranches only; dead code under `use_campd_bins`** (verified: all coal rows carry CAMPD suffixes in all three years; sole consumer `offer_curves.py:72`) | ledger entry re-scoped to legacy-path configs (the C-12 false-positive pattern) |

Pre-solve verification ran the armed config to the seam (no LP): sigmoids off,
HR-floor off, COAL groups stripped, all 20 committed/econ tranches across all
10 plants land exactly on their measured window levels, `_mustrun`/`_peak`
bit-typical of the keeper forms. Nothing re-armable remains in the recorded
config (rule 26 spirit).

### 2.2 The DOF ledger — the lane's actual scorecard

`build_dof_ledger.py` on the armed bundle must show `n_residual` **8 → 6**:

* `COAL_SIGMOID_DEFAULTS[ERCOT]` — retired (flags off; replaced by the
  measured registry, rule 21).
* `coal_take_or_pay_tranches` — retired as a CAMPD-config false positive
  (§2.1; the same correction the builder's C-12 note records).
* `offer_curve_by_group` — remains (gas groups), with its COAL_* 25 scalars
  deleted from the config (n_scalars 132 → 107).
* A new **measured-physical** row records the replacement
  (`coal_perplant_offer_curves`).

## 3. Predictions — fixed before the solve

1. **The offer surface** (direct target): the armed coal mid-band lands on
   the Phase-1 measured table above, per plant, all three years (2023 is the
   declared extrapolation). Verified pre-solve at the seam; the solve's
   mechanism log must show 20 tranches / 10 plants repriced.
2. **C1/C2** — direction genuinely uncertain and PARTIALLY OFFSETTING:
   ~4.3 GW of mid-band capability gets cheaper (Oak Grove −6.6, JK Spruce
   −4.6, Coleto −3.0, Parish −2.6, Limestone −1.8, Major Oak −1.7) while
   ~3.9 GW gets dearer (Fayette +30 with its top ~36 % effectively out of
   merit at $100–150, Sandy Creek +16, San Miguel +7, Martin Lake +1.3).
   The keeper's coal over-run is +1.8/+4.5/+4.3 TWh; the cheap-side moves
   push coal UP (the pre-registered risk), the dear side pushes it DOWN.
   **A C1 or C2 PASS→FAIL flip in any year is an ordinary rejection** (§4).
3. **C7 will NOT improve and may worsen** — established ex ante at ERCOT-143:
   the accurate Oak Grove curve is lower and flatter, hence strictly more
   inframarginal overnight. A C7 regression is NOT a refutation of this lane
   and nothing is tuned to avoid it (rule 1).
4. **C3a/C3b** — reported as they fall; mid-band repricing moves marginal
   price-setting hours in both directions (Martin Lake's 2.5 GW at a flat
   measured $20.9–22.3 replaces a $18.6–25.1 model ramp). No gate claim.
5. **C3c** — predicted ≈unchanged (the repriced mid-band tops at $43 for San
   Miguel — deep inframarginal at the scarcity wall; Fayette's $100–150
   blocks are real submitted supply that could add depth near $100–150,
   which if anything REMOVES cheap depth at scarcity). Guarded (§4).

## 4. Pre-registered failure modes — the decision rule, fixed now

1. **Zero-spurious guard** (ERCOT-89/91): the count of hours where the model
   settles >$200 while RT actual ≤$200 must not increase over the keeper in
   any year ⇒ else ORDINARY REJECTION.
2. **C3c no-drain guard**: scarcity-tail hours must not drain below the
   keeper's 47/6/0 ⇒ else ORDINARY REJECTION.
3. **C1/C2 held**: any year's C1 class-volume or C2 flip PASS→FAIL ⇒
   ORDINARY REJECTION (the handoff's pre-registered natural failure mode).
4. **LOYO within 2023–2025** (rule 22): the mechanism-driven changes are
   scored leave-one-year-out; 2023 (the extrapolation year, no SCED
   disclosure) is the gated year — a 2023-only catastrophic degradation
   (C1/C2 flip localized to 2023) rejects the extrapolation, not the
   mechanism, and is reported as such.
5. **Guards intact ⇒ KEEPER CANDIDATE** on the rule-1 structural standard
   with the DOF retirement as the deliverable; registered keeper-or-rejected
   either way, matrix cell stamped, same session (rules 15/26b).
6. Nothing in this arm is swept or tunable: the curves are the measured
   registry verbatim (rule 23). If they are wrong the source disclosure is
   wrong.

## 5. Honest limits, declared before it runs

1. **2023 is an extrapolation** — no 2023 SCED disclosure exists; the
   time-stability evidence (identical modal curves across 2024/2025) is the
   bridge, exactly as ERCOT-137/139/140 declared, LOYO-gated per §4.4.
2. **Fuel-invariance is corpus-scoped**: San Miguel's priced block moved
   $43→$53 and Coleto $18→$24.2 between the 2024 and 2025 subsets (partial
   gas tracking the flat pooled-modal level does not carry). The pooled modal
   is the strongest single measured object; per-year levels would be the
   audit-L7 year-keyed pattern and are not taken.
3. **Capacity-partition bound**: with the COAL groups stripped, the coal econ
   block is a single CAMPD tranche, so within-window measured dispersion is
   capacity-weight averaged (Fayette's econ window straddles $16→$150 and
   prices at its weighted $80.13; Limestone's $16/$22.8 step averages to
   $20.86). The measured curve is the sole price source; the tranche grain is
   the model's CAMPD partition.
4. **Joint-owner conduct read as plant conduct**: Fayette/Sandy Creek
   per-owner resources are merged capacity-wise — the merged curve is the
   plant's actual aggregate offer, but the model's single-plant LP unit
   cannot represent per-owner dispatch.

## 6. Scope

Full span `--year 2023 2024 2025` in ONE bundle (rule 16), single-delta
replay off `ercot140_coal_peak_arm`. Holdouts (2022/2019/≤2021/H1-2026)
untouched (rule 22) — the derive enumerates only the four committed 2024–25
subsets; the `*_2026_*` files are never opened. ERCOT-scoped (rule 25):
`COAL_PERPLANT_OFFER_CURVE_BY_ISO` carries ERCOT only, other ISOs hard-fail.
No residual-tuned value (rule 13); measured data preferred even if fit
worsens (rule 14 — the whole point). New `ScenarioConfig` fields
(`coal_perplant_offer_level`, `coal_perplant_offer_curves`) registered in
`_CACHE_KEY_OPTIONAL_FIELDS` (default key verified byte-stable at
`603c2498bf71d21d`; armed key distinct) and carrying their mechanism-matrix
row in the same push (rule 26c). No GitHub Actions workflow. CLOSED lanes
honoured: the fleet-aggregate coal offer level (ercot138), the DAM rebasis
(ercot122/132-legB), the lignite slope + C7 offer lane (ercot143), the C3a
trough lane (ercot141), reserve-side scarcity (ercot107/108), West/Panhandle
topology (ercot117); P2 ARCHIVED.

## 7. Open owner rulings surfaced (NOT decided here)

1. Carried: delete vs leave inert the retired `coal_tranche_1_fuel_passthrough`
   + legacy `split_coal_tranches` `_t1/_t2/_t3` path (rule 26 `[R-DELETE]`).
   This lane makes the deletion natural — the ledger now scopes the
   `coal_take_or_pay_tranches` entry to legacy-path configs — but the code
   deletion remains the owner's call.
2. Carried: `ercot_offer_hrmult_ep_rebasis`/`_bands` still carry no
   mechanism-matrix row (rule 26c gap, now predating eight lanes).
3. Carried from ERCOT-143: Martin Lake (EIA 6146) burns lignite but sits
   outside the model's COAL_LIGNITE class — class-composition question, not
   touched (its measured curve is in this lane's registry either way).
