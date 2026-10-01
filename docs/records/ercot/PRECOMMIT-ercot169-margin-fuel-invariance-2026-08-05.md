# PRECOMMIT — ercot-169: the fuel-invariance claim of the three armed ERCOT margin identifications, tested on the delivery-2023 SCED corpus

Committed BEFORE any derive is run (the ercot-162/165/167/168 discipline). Charter:
mechanism-testing-matrix §5.1 **item 13**, owner-chartered by the ercot-169 handoff on the
ercot-168 FINDING §4 named-successor list. **PHASE 0 — NO LP, no solve, no keeper file touched,
no `ScenarioConfig` field written.** 2023 is a training year (rule 22 `[R-HOLDOUT]`); no year
outside {2023, 2024, 2025} is read.

## 0. The object

Three armed identifications each carry the SAME declared-extrapolation note in their
`constants.py` block: *"2023 application is a declared extrapolation (no 2023 SCED disclosure
exists) — the margin is fuel-invariant by construction."* The ercot-157 delivery-2023 corpus
re-upload dissolves that premise — the same rule-14/23 data-vintage trigger ercot-168 executed
for `coal_perplant_offer_curves`.

Unlike ercot-168 these are **margin forms**: 2023 is reached as `level + HR × (fuel₂₀₂₃ −
anchor)`. So the corpus does not merely enable re-derivation — **it tests the invariance claim
itself.** Three independent limbs, three independent verdicts:

| limb | constant (ERCOT) | armed value | applied form | fuel basis |
|---|---|---|---|---|
| **A** | `COAL_OFFER_MARGIN_LEVEL_BY_ISO` (ERCOT-137, coal `_mustrun`) | **15.8807** $/MWh | `HR_g × (coal_fuel(t) − 1.7387) + emis + level` | delivered COAL, `ercot135_coal_merit_order.json` `A_model_offer[y].per_plant` |
| **B** | `CC_COMMITTED_OFFER_LEVEL_BY_ISO` (ERCOT-139, gas-CC `_committed`) | **10.354** $/MWh, `HR_implied` **7.8521** | `HR_implied × (gas − 2.2494) + … + level` | delivered GAS, `ercot138_coal_gas_ranking.json` `J_physical_vs_markup` CC `fuel_capwtd` |
| **C** | `COAL_PEAK_OFFER_LEVEL_BY_ISO` + `COAL_PEAK_OFFER_GAS_HR_BY_ISO` (ERCOT-140, coal `_peak`) | **35.1989** $/MWh, `GAS_HR` **10.4100** | `GAS_HR × (gas_cc(t) − 2.2494) + emis + level` | same GAS basis as B |

All three reuse the shared gas anchor `GAS_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] = 2.2494`
(B, C) or `COAL_OFFER_MARGIN_ANCHOR_BY_ISO['ERCOT'] = 1.7387` (A) — rule 19, never re-derived
here.

**Identification reproduced from the committed artifacts before pre-registering** (footing, no
2023 data touched): limb A pools to 15.8807 exactly (res-hours-weighted over 16.86 / 16.37 /
15.00 / 15.00, weights 22949 / 20807 / 19193 / 17889); limb B's anchored subsets 10.1158 /
10.6358 / 9.6745 / 11.0145 pool to 10.354 exactly; limb C's 35.1989 / 35.1989 / 32.7711 /
37.7811 pool to 35.1989 exactly on the `B_measured` COAL weights (23021 / 20807 / 19265 /
18113). The three derives are reproducible as committed.

## 1. Instruments — reconstructed, never re-invented

Each limb's 2023 statistic is the SAME instrument on the SAME construction, **imported from the
probe that built it** (the ercot-136-imports-ercot-123 discipline), fed delivery-2023 rows:

* **Limbs A and B — ERCOT-136 §B1 `bot_p50`.** Per online resource-interval, `p_bot` = the
  minimum finite `Submitted TPO-Price{k}` (min over columns, not column 1 — robust to
  out-of-order submission); the statistic is the **HSL-capacity-weighted p50** of `p_bot`
  (`_wq`: interpolated quantile on the cumulative HSL weight), over rows carrying a curve.
* **Limb C — ERCOT-138 `measured_curves` incremental-bid p90.** Each curve STEP contributes its
  own MW at its own price, with the cumulative MW clipped into `[LSL, HSL]` so the min-load
  block is not double-counted; the statistic is the **incremental-MW-weighted p90** of the step
  prices. (ERCOT-138 §5.6's "above-min-load cap-weighted p90".)

**Row filters, identical to ercot-123/144** (no relaxation, no addition): class map
`CLLIG → COAL`, `CCGT90 / CCLE90 → CC`; `Telemetered Resource Status ∈ ONLINE`; numeric
coercion; `HSL > 0`; `HSL > LSL`; `HASL` and `Telemetered Net Output` non-null; delivery-year
filter `ts.year == 2023` (drops the publication-window bleed — the corpus is
publication-month-keyed, delivery = filename − 2, shards 2023-03 … 2024-03).

**Clock.** Timestamps convert CPT → fixed CST **at derivation** (`America/Chicago` →
`Etc/GMT+6`, `ambiguous=False`, `nonexistent="shift_forward"`) — the ercot-166 DST class, closed
at source, exactly as `derive_coal_perplant_offer.load_corpus_coal` does it.

**Harness.** The three frozen derives (`derive_coal_offer_margin_anchor.py`,
`derive_cc_committed_offer_margin.py`, `derive_coal_peak_offer_margin.py`) each gain a
`--year` mode in the ercot-168 pattern, over one shared corpus-instrument module that imports
the ERCOT-136 / ERCOT-138 constructions. **No new construction is authored.** Rule-23 re-run
cite: the ercot-157 delivery-2023 corpus landing.

### 1a. Hour-window matching — the primary statistic is MATCHED, and why

The identification's own sampling, measured from its four committed subsets before
pre-registering: **three of the four sample CST h11–22 only** (2024 tail 25 days, 2024 control
22 days, 2025 control 22 days); only 2025 tail (10 days) is full-day. Those three carry
**77.9 %** of limb A/C's pooled COAL res-hours and **75.0 %** of limb B's pooled CC res-hours.

* **T1 — PRIMARY, GATING: delivery-2023, all days, hours 11–22 CST.** Same instrument, same
  window. This is the fuel-invariance test: an unmatched window would confound a fuel-invariance
  failure with an hour-coverage difference.
* **T2 — SECONDARY, REPORTED, NON-GATING: delivery-2023 full-day.** This is the *application*
  read (the constant is applied at all 8760 hours). **Pre-registered in advance:** if T1
  CONFIRMS and T2 lands outside the band, that is an **hour-coverage finding**, reported and
  named — it does NOT by itself refute the invariance claim, and it does not license any arm.

Also reported, non-gating: the 2023 instrument by month (within-year dispersion, the analogue of
the identification's cross-subset dispersion), and a raw-CPT (unconverted) hour-window read
bounding the clock convention's effect.

### 1b. Coverage licensing — per limb, the ERCOT-138 §3.4 test, bar NOT lowered

The licensing quantity is `curve_share` (the ERCOT-123 decomposition: the share of RT-dispatchable
headroom carried into SCED by a submitted curve), reconstructed on the 2023 rows on the same
convention. Pre-registered thresholds — **each class's own minimum over the identification
subsets it was licensed on**:

| limb | class | subset range | **2023 threshold** |
|---|---|---|---|
| A, C | COAL | 0.9876 … 1.0000 | `curve_share ≥ 0.9876` |
| B | CC | 0.9505 … 0.9798 | `curve_share ≥ 0.9505` |

A limb whose 2023 coverage falls below its threshold is **NOT-IDENTIFIABLE-2023**: reported as
such, verdict withheld. **The bar is not lowered to rescue a limb.**

### 1c. Fuel-basis footing gate — limbs B and C only

Limbs B and C need `gas₂₀₂₃` on the **same basis** as the identification's `gas₂₀₂₄ = 2.2130` /
`gas₂₀₂₅ = 3.2320` (ERCOT-138 §J: `fuel_capwtd = Σ pmax·fuel_price / Σ pmax` over CC_REGULAR
`committed`+`econ` rows, `fuel_price` = the row's annual mean delivered fuel captured at the
`apply_coal_tranches` seam). No committed artifact carries a 2023 value and the ERCOT-138-era
bundle `ercot137_margin_arm` is not on disk, so it is reconstructed **no-LP** from the current
keeper bundle `results/calibration/ercot168_yearcurves_B` via
`scripts.lib.bundle_fleet.reconstruct_bundle_fleet` for 2023, 2024 and 2025 on the ERCOT-138 §J
construction.

* **FOOTING GATE:** the reconstruction's 2024 and 2025 values must reproduce **2.213 / 3.232
  within ±$0.02/MMBtu**. Pass ⇒ the 2023 value is basis-consistent and limbs B/C proceed on it.
* **Pre-registered fallback if the footing FAILS** (a live possibility: `ercot-150`'s zonal gas
  basis and the West net-load shaping landed *after* ERCOT-139/140, and both move the delivered
  array): the basis moved. Then (i) the Δ is reported as a **basis-drift finding on the armed
  constants, independent of the 2023 test**; and (ii) the test is re-run as a disclosed
  **basis re-expression** — all four identification subsets' anchored levels recomputed on the
  current keeper's own `fuel_capwtd` year values, re-pooled with the same weights to
  `level_current_basis` and its band recomputed the same way, with 2023 tested against that.
  Both readings are reported side by side. No residual is consulted at any point (rule 23): it
  is the identical formula evaluated on a consistently-measured fuel series.
* If the reconstruction cannot be run at all, limbs B and C are **NOT-IDENTIFIABLE-2023 on basis
  grounds**. **Limb A is unaffected either way** — its fuel basis (1.8169 / 1.7556 / 1.6436) and
  its heat rate are both committed in `ercot135_coal_merit_order.json` and already include 2023.

## 2. Predictions and bands — PRE-REGISTERED, computed before measuring

The test statistic per limb is the **anchored 2023 level**, i.e. the measured 2023 instrument
with the form's own fuel response removed at 2023's own delivered fuel — algebraically identical
to comparing the measured instrument against the armed constant's anchored prediction, and
stated in the constants' own units:

```
limb A:  level₂₀₂₃ = bottom₂₀₂₃      − 10.9832 × (1.8169 − 1.7387)   vs  15.8807
limb B:  level₂₀₂₃ = bottom_CC₂₀₂₃   −  7.8521 × (gas₂₀₂₃ − 2.2494)  vs  10.354
limb C:  level₂₀₂₃ = p90₂₀₂₃         − 10.4100 × (gas₂₀₂₃ − 2.2494)  vs  35.1989
```

Limb A's heat rate is the ERCOT-137 derive's own `hr_capwtd` = **10.9832** MMBtu/MWh, and the
ERCOT coal fleet is static across the training window (per-year cap-weighted HR is 10.9832 in
each of 2023/2024/2025 — no year-choice ambiguity exists). Its fuel term is therefore fixed at
**+$0.8589/MWh**, giving the **prediction 16.7396 $/MWh** for the measured 2023 bottom.

**Bands — each limb's own cited cross-subset dispersion**, on the derives' own construction
`100 × (max − min) / (2 × level)` (a half-range about the level):

| limb | cited band | as $/MWh | CONFIRMED window on `level₂₀₂₃` |
|---|---|---|---|
| **A** | **±5.86 %** (raw half-range, (16.86 − 15.00)/(2 × 15.8807)) | **±0.9300** | 14.9507 … 16.8107 (⇔ measured bottom 15.8096 … 17.6696) |
| **B** | **±6.47 %** anchored (the value cited in the constants block) | **±0.6699** | 9.6841 … 11.0239 |
| **C** | **±7.12 %** anchored (the value cited in the constants block) | **±2.5062** | 32.6927 … 37.7051 |

**Limb A's band, stated from the ERCOT-136/137 record before measuring** (the handoff's explicit
requirement). The ERCOT-137 identification pooled the four subset bottoms **raw** — no fuel
response was removed — so it has no `dispersion_anchored_pct`; its band is the raw half-range
above, **±5.86 % = ±$0.9300**. The record carries a second, independent statement of the same
tolerance: ERCOT-137 precommit **P7**, *"the resolved coal `_mustrun` band … lands within
**±$1.00** of the measured TPO-Price1 cap-wtd p50 per year (2024: 16.63; 2025: 15.00)"*. The two
agree to seven cents. **Pre-registered: the gating band is the TIGHTER one, ±$0.9300** — the
half-range construction, uniform with limbs B and C. A result landing in the
**$0.9300 – $1.0000 marginal zone** is declared in advance as **CONFIRMED-MARGINAL**, reported
with both readings stated explicitly and never rounded into a clean pass.

## 3. The decision rule — PRE-REGISTERED, per limb, independent

**CONFIRMED** — `|level₂₀₂₃ − armed constant| ≤ band` (T1, licensing passed, footing passed).
> Consequence: **the extrapolation note is retired BY VERIFICATION.** Update that constant's
> `constants.py` comment (the block's comment IS its identification record), the DOF ledger
> entry, and the matrix cell + citation. **NO solve, NO new mechanism, NO new DOF, keeper
> UNCHANGED.** This is a full, successful session outcome.

**REFUTED** — outside the band.
> Consequence: record the discrepancy with its magnitude and sign. A year-keyed 2023 block
> becomes a **NAMED CANDIDATE ARM** — **building or arming it is a SEPARATE owner adjudication.**
> Surface the measurement and **STOP**, unless the owner directs execution in-session. If so
> directed: same harness shape as ercot-168 (default-off gate, 2023-only table, static
> fall-through), gates pre-registered before any solve **including G-BIT byte-identity on
> 2024/2025**, full-span sequential A/B off the run168b keeper via `scripts/replay_keeper.py`,
> both runs registered (rules 15/16), **zero fitted scalars**.

**NOT-IDENTIFIABLE-2023** — the limb's 2023 coverage fails §1b, or its fuel basis fails §1c with
no admissible fallback.
> Consequence: report it as such. **Do not lower the bar**, do not substitute a looser
> instrument, do not fill the gap with the 2024/25 value and call it verified.

No amendment softens a band, a threshold or an instrument after measurement. Any construction
detail that must be amended is recorded in this document **before** the derive runs (the
ercot-167/168 amendment pattern).

## 4. Scope fences and DO-NOT-REDO honored

* **Rule 13 `[R-MEASURED]` / rule 1 `[R-STRUCT]`:** nothing here is tuned and nothing is fitted.
  Every number is a measured corpus read on an already-accepted convention, or a committed
  artifact read back. No residual is consulted, in either verdict branch.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the re-run cite is the ercot-157 delivery-2023 corpus landing
  — a source-data change, not a residual move.
* **Rule 19 `[R-ONE-MECH]`:** each end of the coal curve keeps its own measured owner —
  `_mustrun` (A), `_committed`/`_econ` (`coal_perplant_offer_*`, untouched here), `_peak` (C).
  No limb is stacked onto another's residual.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-identified from ERCOT conduct; nothing crosses an ISO
  boundary in either direction.
* **DO-NOT-REDO, all standing and untouched:** per-year CT re-identification REFUSED at
  ERCOT-147 (modal identity 11/160) — **this lane is not extended to CTs**; lignite offer SLOPE
  (ERCOT-143 as adjudicated); `coal_min_load_floor` both grains; lignite daily unit commitment;
  coal seasonal LEVEL split; `coal_offer_level_rebasis` (`R`); `tranche_startup_amortization`
  (`G`); ercot-168's **OPTION B** (spread-regime-conditional top) stays **DEFERRED** — not
  touched here; the ercot-167 SOC-reserve re-gate waits on the H4-item-4 2024 maintenance-season
  availability defect, not on this lane; §5.1 **item 11** (CC headroom/capability crosswalk)
  stays chartered and untouched.
* **No GitHub Actions.** No `--year` outside 2023–2025. Every push touching a ≥300-line file is
  blob-verified (rule 27).
