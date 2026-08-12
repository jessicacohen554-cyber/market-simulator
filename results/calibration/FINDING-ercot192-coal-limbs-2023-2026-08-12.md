# FINDING — ercot-192: the two COAL limbs' 2023 application, re-adjudicated (signature B1)

**Session** ercot-192 · **ISO** ERCOT · **Years** 2023–2025 · **Date** 2026-08-12
**Charter** `docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` card B,
owner signature **B1** (2026-08-11): *"re-adjudicate under a fresh precommit
before any arm."* Sequenced after A1, which landed 2026-08-12 (PR #3887, keeper
`2026-08-12-run191-dam-deriver-regate`).
**Precommit** `docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md`
— pushed before any level was measured and before any solve.

---

## 0. WHAT THIS LANE IS NOT (stated first, per the precommit §0)

This is a **mechanism-correctness** lane under rules 1 `[R-STRUCT]` and 23
`[R-FROZEN-DERIVE]`. It is **NOT C3a-2023 spend**: card Q ruling **Q-B** was
signed final at ercot-191 and no further ERCOT C3a-2023 work is authorized;
ERCOT stands at NOT-YET on C3a-2023 as a model-class limit, item 11 **CLOSED**.
Every 2023 price movement below is **reported at full magnitude and was never
targeted**, is not a gate, and is not the promotion basis. No C3a-2023
improvement is claimed. The C3c ledger, the closed faces and item 11 are
untouched.

---

## 1. THE OBJECT

| limb | mechanism / constants | status entering the lane |
|---|---|---|
| **A** | `coal_offer_net_revenue_margin` — `COAL_OFFER_MARGIN_LEVEL_BY_ISO` 15.8807 (coal `_mustrun`) | 2023 application **CONFIRMED at ercot-171** |
| **C** | `coal_peak_offer_margin` — `COAL_PEAK_OFFER_LEVEL_BY_ISO` 35.1989 + `COAL_PEAK_OFFER_GAS_HR_BY_ISO` 10.4100 (coal `_peak`) | **NOT-IDENTIFIABLE-2023 CONFIRMED at ercot-171**; extrapolation note stands; no arm named |

Both are armed on the run191 keeper, so both are live in the 2023 solve.

**The measured defect (card B).** The delivery-2023 COAL corpus's two most common
submitted TOP steps are **$78.00** (21,677 intervals) and **$75.01** (17,869);
**$34.82** — the 2024/25 level — is a distant tenth. Limb C's own instrument
reads **p90 = 75.00 $/MWh** on the 2023 rows, i.e.
`level₂₀₂₃ = 75.00 − 10.4100 × (2.6012 − 2.2494) = 71.3378`, **+36.1389 = 14.42×
the ±$2.5062 band** above the armed 35.1989 — the armed constant is roughly
**half** the measured 2023 top.

**Identification source (rule 23 citation).** The committed **delivery-2023 SCED
60-Day NP3-965 corpus** (`data/raw/ercot/SCED`, 996 shards — the ercot-157
re-upload), whose landing is the rule-14/23 data-vintage trigger that dissolves
these constants' declared *"no 2023 SCED disclosure exists"* premise. No residual
is consulted anywhere in the derivation.

---

## 2. PHASE 0a — the instrument-structure read that shaped the charter

`scripts/probes/ercot192_coal_peak_structure_phase0a.py` →
`results/calibration/ercot192_coal_peak_structure.json`. Coverage and headroom
composition only — **no price of any kind was read**, so the precommit's decision
rule stayed genuinely pre-registered. Matched window (h11–22 CST):

| quantity | delivery-2023 | 2024/25 subsets (pooled) |
|---|---|---|
| `curve_share` (unweighted, the ercot-169/171 licensing quantity) | **0.97022** | 0.99623 |
| `a_offered` (headroom-weighted offered share) | **0.94775** | 0.99672 |
| share of RT headroom in no-curve rows | 0.05175 | 0.003–0.007 |
| of that: **(b) price-taking / self-schedule** | **0.98787** | 0.9876–0.9917 |
| of that: (e) genuine residual | 0.01213 | 0.008–0.012 |
| loading (netout/HSL) of the no-curve rows | 0.98047 | 0.954–0.984 |

Per resource: `MLSES_UNIT1/2/3` 0.7572 / 0.7611 / 0.7970, `WAP_WAP_G8` 0.9489,
`CALAVERS_JKS2` 0.9827; every other COAL resource ≥ 0.9984.

**Two candidate repairs were REFUSED on this read, before any level was
measured** — recorded in the pushed precommit §1c so neither can be revived:

* **Own-conduct imputation** — filling each no-curve interval with that
  resource's own modal curve would fix `curve_share` without dropping anyone.
  **Inadmissible**: 98.8 % of the missing headroom is price-taking at 98 %
  loading, so a self-schedule is a resource *making no incremental offer*.
  Imputing a curve would **invent an offer that was never submitted** — rule 13
  `[R-MEASURED]`.
* **Re-expressing the licence on the exposure-matched `a_offered`** — arguably
  the right quantity for an incremental-MW-weighted statistic. **Refused because
  it was measured first**: on 2023 `a_offered` is 0.94775, i.e. *worse* than
  `curve_share`. It would not rescue the limb, and a licensing quantity may never
  be chosen after seeing which one passes.

The 0.9876 floor is **not lowered**, no resource is dropped (ercot-171's S1), no
month is selected (S2).

---

## 3. PHASE 0 — the instrument: a coverage BOUND, not a coverage repair

ercot-171 closed with *"an instrument that does not select on the tail would need
its own charter."* B1 chartered it, and the route taken needs **no repair at
all**.

Both limbs are weighted quantiles, and the missing rows contribute **zero
weight**. So give that weight the most extreme admissible price in each direction
and recompute the **same** statistic:

```
append M at the bottom  ⇒  q_low  = α + (α − 1) · M/O
append M at the top     ⇒  q_high = α · (1 + M/O)
```

The true α-quantile then lies in `[Q(q_low), Q(q_high)]` **under ANY imputation
of the missing rows whatsoever**. It selects nothing, drops nothing, invents no
price, swaps no licensing quantity and moves no floor — and it is falsifiable: a
straddling interval is NOT-IDENTIFIABLE and stops the lane.

`M` is the no-curve rows' full incremental range `Σ(HSL − LSL)` for limb C (the
statistic's own denominator, hence **maximal** — a wider and therefore stricter
interval than the precommit's stated `h_rt`, which is reported alongside) and
their `HSL` for limb A. The harness imports
`scripts/lib/sced_corpus_instruments.py` verbatim and **asserts** that the bound
machinery reproduces the committed statistic at α before any bound is read.

### 3.1 G-FOOT — PASS

All eight committed subset-class reads reproduce **exactly**: `bot_p50`
16.86 / 16.37 / 15.00 / 15.00 and `p90` 34.82 / 34.82 / 43.00 / 48.01. The
ERCOT-138 §J fuel basis reconstructs (no LP) to **2.2129 / 3.2324** against the
committed 2.213 / 3.232, and COAL to 1.7481 / 1.6296 against 1.748 / 1.630.
*Provenance note:* ercot-169/171 read the fuel basis off `ercot168_yearcurves_B`,
which is no longer on disk; the **current keeper bundle** was substituted and the
substitution is **gated by G-FOOT, not assumed**.

**The gate caught a real defect first.** The initial run restricted the four
identification subsets to the matched window. They are probe-DAY frames read
whole by ercot-169/171, and restricting them moved `2025_ercot86_tail_days`
`bot_p50` 15.00 → 14.73 — G-FOOT FAILED and the restriction was removed. That is
the footing gate doing its job.

### 3.2 G-NEUT — PASS both limbs, under AMENDMENT 1

**AMENDMENT 1 (pre-solve, post-measurement) — the measurement exposed a defect in
the precommit's own gate, and it is recorded rather than quietly fixed.** The two
limbs' identifications pool the four subsets with **different arithmetics**:

* `coal_peak` (ERCOT-140) anchors **per subset** and pools the anchored levels —
  35.1989 / 35.1989 / 32.7711 / 37.7811 → 35.1989 res-hours-weighted, verbatim
  from `constants.py`.
* `coal_mustrun` (ERCOT-137) pools the **RAW `bot_p50` with no anchoring at
  all** — `derive_coal_offer_margin_anchor.derive_ercot`:
  `level = Σ res_hours·bot_p50 / Σ res_hours`.

The precommit's single-sentence G-NEUT applied limb C's arithmetic to both, so on
limb A it measured an **anchoring inconsistency in the committed ERCOT-137
derivation** rather than anything about the bound: the registered anchor 1.7387 is
the **three-year** mean while the pool sits at the 2024/25 res-hours mean fuel
≈1.7040, worth `10.9832 × 0.0347 ≈ +0.38` = **0.41× its band**. Inside the band,
so it changes no arming — but it is real, it pre-dates this lane, and it is now
carried in the DOF ledger (§6).

The gate was therefore split into the two things its own sentence
(*"must leave each constant inside its own band"*) actually asks for. **Neither
half is weakened, and the half that carries the 2023 verdict is the strict one:**

| | limb A | limb C |
|---|---|---|
| pooling arithmetic (the identification's own) | raw | anchored |
| **G-NEUT-a** footing Δ vs armed (tol $0.02) | **−0.002383** PASS | **+0.000026** PASS |
| **G-NEUT-b** displacement of the **LOWER** edge (the edge carrying the 2023 verdict) | **−0.0602 = 0.065× band** PASS | **0.0000 = 0.000× band** PASS |
| **G-NEUT-c** opposite edge, **REPORTED, non-gating** | 0.0000 = 0.000× band | **+6.6049 = 2.635× band** |

G-NEUT-c is the bound being honest, not buried: on the *licensed* subsets a p90
of a steep curve top admits a large **upward** excursion from even 0.3–0.7 %
missing weight. The 2023 verdict rests on the **lower** edge, whose displacement
is measured at exactly zero where the instrument is licensed.

### 3.3 G-BOUND + G-WINDOW — limb C REFUTED, limb A NOT-IDENTIFIABLE

Levels ($/MWh), each limb on its own instrument, fuel response removed:

| window | limb | point | bound interval | armed ± band | G-BOUND |
|---|---|---|---|---|---|
| matched h11–22 CST | `coal_mustrun` | 17.5211 | [16.5911, 17.8411] | 15.8807 ± 0.9300 | STRADDLES |
| matched h11–22 CST | **`coal_peak`** | **71.3378** | **[71.3378, 81.3678]** | 35.1989 ± 2.5062 | **REFUTED** |
| full day | `coal_mustrun` | 17.8311 | [17.2711, 17.8411] | 15.8807 ± 0.9300 | REFUTED |
| full day | **`coal_peak`** | **71.3378** | **[71.3378, 71.3578]** | 35.1989 ± 2.5062 | **REFUTED** |
| matched, raw-CPT clock | `coal_mustrun` | 17.5211 | [16.5911, 17.8411] | 15.8807 ± 0.9300 | STRADDLES |
| matched, raw-CPT clock | **`coal_peak`** | **71.3378** | **[71.3378, 96.3378]** | 35.1989 ± 2.5062 | **REFUTED** |

* **Limb C — REFUTED on all three windows.** The **lower** bound is **71.3378 in
  every window**: the 2023 level is **at least +36.1389 = 14.42 band-widths above
  the armed constant no matter what the missing rows would have said**. Card B's
  *"a 1.7 pp coverage shortfall cannot produce a 2× level shift"* is now
  **measured, not asserted** — which is precisely the gap the record had. The
  point estimate is window-invariant.
* **Limb A — NOT-IDENTIFIABLE-2023 under this instrument** (G-WINDOW fails:
  STRADDLES on the matched window, REFUTED full-day). The bound **does not
  contradict** ercot-171's CONFIRMED; it simply cannot sharpen it. **No arm, no
  change, no re-verdict.** ercot-171 stands.

Artifacts: `scripts/probes/ercot192_coal_limbs_bound_phase0.py` →
`results/calibration/ercot192_coal_limbs_bound.json`.

---

## 4. THE ARM — the only one the precommit permits

Per precommit §4 (option iii, the ercot-168 `coal_perplant_offer_yearly`
per-year precedent):

* `constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO = {"ERCOT": {2023: 71.3378}}`
* gate `ScenarioConfig.coal_peak_offer_yearly_level` (requires
  `coal_peak_offer_margin`; ISO absent from the registry hard-fails, rules 24/25)
* the **LEVEL only** swaps. `COAL_PEAK_OFFER_GAS_HR_BY_ISO` 10.4100 and the
  **shared** anchor `GAS_OFFER_MARGIN_ANCHOR_BY_ISO` 2.2494 are untouched — one
  year cannot identify a slope, and the anchor is the whole gas offer surface's
  single identification point (rule 19 `[R-ONE-MECH]`).
* a year **absent** from the table (2024, 2025) falls through **bit-identically**
  — the G-BIT kill's mechanism, unit-tested in
  `tests/unit/data/test_coal_peak_yearly_level.py` (8 tests).
* **`coal_perplant_offer_yearly` is not extended**; the `_peak` tranche keeps its
  ERCOT-140 owner. The armed value is the instrument's own point estimate and no
  value that moves a residual may be substituted for it.
* **Zero fitted scalars** (rule 23 `[R-DOF]`).

---

## 5. THE A/B

*(filled after the solves — see §5.1)*

---

## 6. THE DOF LEDGER — card B's standing item, discharged

Card B filed, and did not act on: the three margin constants
(`COAL_OFFER_MARGIN_LEVEL_BY_ISO`, `CC_COMMITTED_OFFER_LEVEL_BY_ISO`,
`COAL_PEAK_OFFER_LEVEL_BY_ISO` + `COAL_PEAK_OFFER_GAS_HR_BY_ISO`) are armed on
the keeper and carry **no dedicated DOF-ledger entries**. Zero fitted scalars
each, so this is bookkeeping rather than hidden freedom — but rule 23 says every
free parameter is listed with its identification source, and an armed
identification constant absent from the ledger is exactly what the rule exists to
surface.

`scripts/gen_ercot192_attestation.py` adds all three to **both** arms (the
omission is the keeper's, not this lane's), each carrying its identification and
its live 2023 status — including **limb B's ercot-169 verification** with its
boundary-coverage caveat, **limb A's ercot-171 verification** plus the newly
measured ERCOT-137 anchoring inconsistency, and limb C's neutrality read. The arm
additionally carries its own `coal_peak_offer_yearly_level` entry.
`n_residual` is unchanged by construction: every entry added is
`measured-physical` with zero fitted scalars.
