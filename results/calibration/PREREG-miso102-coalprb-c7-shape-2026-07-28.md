# PRE-REGISTRATION miso-102 — the C7 COAL_PRB off-peak CV failure is the off-peak PRICE wave, and the committed-band take-or-pay discount is what flattens it

**Committed BEFORE either arm was solved.** Lane: C7 diurnal shape (D-1
`cv_ratio`, `COAL_PRB`) — the SOLE criterion standing between MISO and a
CALIBRATED determination, failing 3/3 years on keeper
`2026-07-28-miso-101b-tempgrain` (0.467 / 0.476 / 0.318 against a ≥ 0.50 bound).

Runs: `2026-07-28-miso-102a-control` (`miso102_control_A`) /
`2026-07-28-miso-102b-sunkfixed` (`miso102_sunkfixed_B`), both 2023–2025 in one
bundle (rule 16 `[R-ALLYEARS]`).

---

## 1. Diagnosis (committed artifacts only — NO LP re-solve)

Scored from the keeper's run payload (per-plant model MW), the CAMPD bench
(`frontend/data/backcast/bench/MISO/<year>.json.gz`), the keeper's
`legitimacy_diagnostics.json` / `hourly/` sidecars,
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet` and
EIA-930 `MISO_fueltype.parquet`.

**Four of the four candidate hypotheses are refuted or reframed:**

| hypothesis | verdict | evidence |
|---|---|---|
| (b) right plants held too flat by a **floor** | **REFUTED** | D-2: MISO coal carries exactly ONE mechanism, `reliability_floor`, at **0.31 / 0.35 / 0.19 %** of class energy. Rule 17 has nothing to bite on. |
| (c) **mix effect** — wrong SET of overnight units | **REFUTED** | D-1 pairs model and bench on the SAME keys; **0 plants dropped** in any year (31/31/30 paired). |
| (d) **benchmark basis** | **REFUTED** | both sides are the same CAMPD plant set with the bench's own class labels; class energy ratio 0.91 / 0.91 / 0.95. |
| (a) too few PRB plants cycling overnight | **TRUE as description, NOT causal** | see §2 |

**The miso-101 §5 CANCELLATION mechanism does NOT apply here.** Off-peak
profile coherence `std(Σ) / Σ std` is **0.984 / 0.981 / 0.939** (model) and
**0.971 / 0.972 / 0.922** (actual): both sides are essentially in phase, so the
class composite is a faithful sum of per-plant amplitudes, not a cancellation
residual. Phase coherence also matches (model 0.68/0.62/0.55 vs actual
0.67/0.62/0.53) — **the model is not out of phase, it is under-amplitude.**

**It is NOT the miso-89 phenomenon.** Seasonal `cv_ratio`:

| season | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| winter | 0.416 | 0.453 | 0.374 |
| shoulder | 0.457 | 0.411 | **0.274** |
| summer | 0.488 | 0.526 | 0.384 |

The miss is present in EVERY season and is **worst in winter/shoulder**, in the
h0–h14 window. miso-89's instrument is a **summer HE16–18** ~10 GW under-derate.
Different window, different season, opposite ranking — **separable**, and
consistent with miso-96 §4's finding that the night half is not covered by the
miso-89 data block.

## 2. The root cause: the off-peak PRICE wave, not the coal fleet's response

**The COAL_PRB dispatch amplitude ratio IS the off-peak price amplitude ratio:**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| off-peak **price** CV ratio (model / actual RT, body-censored $200) | **0.460** | **0.530** | **0.331** |
| off-peak **COAL_PRB dispatch** CV ratio (the failing D-1 gate) | **0.467** | **0.476** | **0.318** |

**The fleet is not under-responsive — it is over-responsive.** Regressing PRB MW
on price over off-peak hours: model slope **372 / 151 / 248** MW per $ against
the actual fleet's **157 / 167 / 88**. The model's coal is **2.4× / 0.9× / 2.8×**
the real fleet's price-responsiveness. Any lever that steepens the coal offer
surface pushes a variable that is already too large — this is why no
offer-curve lever is admissible here.

Counterfactual (model's OWN fleet slope, actual's price wave): `cv_ratio`
0.465 → **0.876** (2023) and 0.317 → **0.899** (2025); 2024 goes 0.473 → 0.357
(the linear reconstruction is weakest in the year with the smallest price-wave
gap and the closest slope match — recorded as the noisy case, not suppressed).

## 3. Which units, and which mechanism owns them

Per-plant within-day CV (mean over online days), model vs CAMPD:

* **100 % of the byte-flat PRB plants are REGULATED**, in all three years
  (9 / 8 / 10 plants, **47 / 46 / 50 %** of class energy, model within-day CV
  ≤ 0.02 against a measured 0.13–0.68).
* Pooled over 2023–25, **all MISO coal ranks**:

| group | plant-yrs | TWh/yr | ACTUAL within-day CV | MODEL within-day CV |
|---|--:|--:|--:|--:|
| REGULATED | 119 | 167.1 | **0.197** | **0.073** |
| MERCHANT | 15 | 28.5 | **0.134** | **0.351** |

**The model INVERTS the observed flexibility ordering.** Reality: regulated coal
cycles *more* within the day than merchant (0.197 vs 0.134). Model: regulated
cycles *less*, by 4.8× (0.073 vs 0.351). Within COAL_PRB alone the two groups are
measured statistically indistinguishable (0.262 regulated vs 0.231 merchant).
**There is no support in MISO's own conduct for the claim that regulated coal is
less within-day flexible than merchant coal** — which is exactly what the
committed-band discount asserts.

The owning mechanism is `coal_committed_takeorpay_regulated` (armed in the
keeper): a regulated plant's `_committed` band passes `1 − contract_share` of
its fuel, and `contract_share` is **1.00 for 13 of 17** MISO PRB plants checked.
With `coal_mustrun_per_plant` beneath it, **~55 % of each regulated plant bids
VOM-only in all 8760 hours**. Coal is therefore absent from the overnight
marginal stack, gas CC sets the trough at ~its SRMC ($27.19 / 24.91 / 33.76
model vs $19.42 / 18.43 / 26.87 actual), and the price wave every other class
reads is compressed. Corroborated on the supply mix (EIA-930): at h2 the model
runs **+2,379 / +2,956 MW** more coal and **−3,705 / −4,141 MW** less gas than
reality (2023 / 2025), while wind, solar, nuclear and hydro all match.

This is miso-96 §5's attribution, now measured at plant grain and with the
price-wave mechanism identified.

## 4. The arm, and why it is NOT a keeper candidate

**Arm B = control + `coal_committed_takeorpay_sunk_fixed=true`** (single delta).
It suppresses the committed-band discount; the `_mustrun` band's `1 − share`
is untouched.

**Off-queue rationale (rule 26 duty (a)).** The MISO lever queue's item 1 is the
**minimum-take LP constraint**. It is not built here because miso-96 §7's own
second hard constraint is unresolved: the constraint needs a contract tonnage
that is **not** the same year's measured receipts, and EIA-923 publishes
deliveries, not contract terms — setting min-burn from `share × measured
receipts` would pin the model's annual coal energy to ≈ actual, which rule 13
`[R-MEASURED]` forbids outright. Until a forward-regenerable tonnage exists that
lane cannot be built honestly. This arm is the **control arm that lane will
need**, re-taken on a keeper four revisions newer than miso-96's base and with
§2–§3's new evidence.

**Pre-registered structural verdict, stated before the solve:** this arm is
**structurally incomplete by construction and is NOT a keeper candidate whatever
the gates do.** Removing the discount removes *two* jobs at once — the category
error (an annual volume obligation priced as an hourly marginal subsidy, rule 17:
a discount with no window) **and** a real behaviour (regulated self-commitment,
SOM Table 7: 53–56 % of coal starts self-committed). Rule 1 `[R-STRUCT]` cuts
both ways: a mechanism that deletes a real market behaviour is not made a keeper
by a gate improvement. The arm is registered as **diagnostic evidence**.

## 5. Falsifiable predictions

| id | prediction |
|---|---|
| **P1** | C7 `COAL_PRB` `cv_ratio` RISES in all three years vs control. |
| **P2** | 2023 and 2024 PASS the 0.50 bound; **2025 still FAILS** (its price wave is the most compressed, 0.331). |
| **P3** | C1 fuel-mix FAILS — total COAL falls **20–30 TWh** in 2023 and in 2024. |
| **P4** | C5a CO2 vs eGRID falls **8–12 %** → FAIL. |
| **P5** | The **off-peak PRICE** CV ratio rises by **≥ 0.05** in each year. This is the mechanism test: §2 says the arm must widen the *price* wave, not merely the dispatch wave. If dispatch amplitude rises while the price wave does not, §2's attribution is WRONG. |
| **P6** | The regulated/merchant inversion corrects in direction: model regulated within-day CV rises, and the model's regulated:merchant within-day CV ratio moves from ~0.21 toward ≥ 0.50. |
| **P7** | Determination stays **NOT-YET** (2025 C7 plus the new C1/C5a fails). |
| **P8** | The control reproduces the committed keeper `miso101_tempgrain_B` on every class in every year to < 0.01 %. |

Any prediction that misses is recorded as missed, in the FINDING, with its
direction (miso-101 §5 precedent).

## 6. Method / hygiene

* Years **2023 2024 2025** only (rule 22 `[R-HOLDOUT]`; MISO freeze active, no
  calibration-complete marker). P1 only; P2 archived.
* One process per year per arm (rule 12 `[R-PARALLEL]`: a single MISO per-plant
  LP peaks > 11 GB on a 15 GB box), arms staged **serially**, never interleaved;
  merged with `scripts/probes/pjm119_merge_year_chain.py` then
  `--rebuild-benchmark` per arm (shared `bench/MISO/<year>.json.gz`).
* No `--reuse-solved`: all three years fresh in both arms.
* `legitimacy_diagnostics.py --json-out <bundle>/legitimacy_diagnostics.json`.
* Both arms registered on the backcast dashboard (rule 15 `[R-DASHBOARD]`);
  matrix cell `coal_takeorpay_committed` MISO updated in-session (rule 26 duty b).
