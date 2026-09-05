# PREREG miso-220 — THE NON-STEAM FOSSIL OFFER LIFT (×1.10, steam gas held): a KEEPER CANDIDATE under the owner's 2026-09-05 ruling, aimed at C3a-2025 and pre-registered to fail on CT_PEAKER (2026-09-05)

**Pushed BLIND. No LP has been solved on this config. Nothing below is written after
a number was read.** Every prediction, band and kill is fixed here before the arm runs.

**Keeper / control:** `2026-09-05-miso-217-intermphys` (bundle
`results/calibration/miso217_intermphys_B`) — determination **NOT-YET on C3a-2025
alone (−12.3 %)**, C3c ledgered 3/3, C6 attested 41/2. Rule 29(b) form 4: the
keeper's committed bundle IS the control; **no control solve.** Rule 22: 2023–2025
only, one `--year 2023 2024 2025` invocation, one bundle.

---

## 1. THE OWNER RULING THIS ARM RESTS ON, recorded verbatim in substance

The owner ruled on 2026-09-05, in response to the miso-218 rejection:

> *"We should definitely be able to fit the fossil offer curves to the price… as long
> as it's the same config across the 3 years it is fine to do. And we can keep steam
> gas as is and do 1.1x for all the rest of fossil. The offer curve multipliers are
> meant to allow us to tune on price & adjust merit order."*

and, asked to scope "steam gas", selected **`ST_GAS` + `ST_GAS_INTERMEDIATE`** (the two
duty-split halves of one steam-gas cohort, split at miso-217), and **the level arm alone
first** rather than bundling the peak-band reshape.

**What this changes, stated plainly.** miso-218 was rejected on two independent grounds:
(a) rule 1 `[R-STRUCT]` — a level scalar identified against a price residual is not a
keeper mechanism; and (b) it broke a load-bearing C1 cell. **The owner's ruling
disposes of (a)** — the band multipliers are declared the intended tuning channel, and
one config held across all three years is the discipline that separates tuning from
per-year fitting. **(b) is untouched and is what this PREREG is built to test.** The
arm is therefore registered as a **KEEPER CANDIDATE**, not a rule-13 probe.

**What the ruling does NOT license, and this arm does not do:** no per-year config, no
sweep of the factor against the gates (miso-218 §closing refused exactly that, and
that refusal stands), no touching `phys_*` (measured physics), no touching
`econ_low_share` / `pct_peaking` (structural shares — the peak-band reshape is a
separate later question, per the owner's second answer).

## 2. THE DELTA — one channel, thirteen rows, fully enumerated

`offer_curve_by_group`, passed as a FULL explicit table via
`replay_keeper --set` (the documented `prb_overrides` seam, applied after
`backcast_config` merges the per-ISO curves — the same channel miso-218 used).
Source of truth: `scripts/probes/_miso220_offer_table.py`.

**×1.10 on `committed` / `econ_low` / `econ_high` / `peak`** for: `CC_REGULAR`,
`CC_INTERMEDIATE`, `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `CT_INTERMEDIATE`, `COAL`,
`COAL_PRB`, `COAL_BIT`, `COAL_LIGNITE`, `COAL_WC`.
**HELD byte-identical:** `ST_GAS`, `ST_GAS_INTERMEDIATE`.
**Never scaled anywhere:** `phys_*`, `econ_low_share`, `pct_peaking`.

Within-class band ratios are preserved exactly for every lifted class (a common factor
cancels), so merit order is preserved *within* each lifted class; what moves is the
lifted classes against the held steam-gas pair — the intended merit-order adjustment.

**S-1 IS ALREADY MEASURED AND PASSES, and it is the check that could have voided the
arm.** The keeper records only ONE explicit `offer_curve_by_group` row
(`ST_GAS_INTERMEDIATE`); the rest resolve implicitly. A full explicit table is a single
delta only if its unlifted half reproduces that implicit resolution exactly.
`_miso220_liveness.py` measures **max |Δmc| = 0.0 across all 2,923 tranches** on 2025
between the keeper's own construction and `BASELINE_TABLE`. **S-2** likewise passes:
**1,604 tranches move, 0 of them in a held class, 0 outside the covered classes**,
74,251.8 MW lifted; cap-weighted offer moves `CC_REGULAR` +9.29 %, `CT_PEAKER` +7.54 %,
`COAL` +6.53 %, `CC_CHP` +8.58 %, `CT_CHP` +7.48 %, `ST_GAS` **+0.00 %**.

## 3. WHAT THIS CHANNEL CANNOT REACH — declared, not discovered later

Three fossil-or-fossil-adjacent blocks have **no `offer_curve_by_group` entry** and are
therefore unlifted **by omission, not by design**. Adding entries would be a second
delta and a new tuning surface, so this arm leaves them and says so:

| block | capacity (2025) | note |
|---|---:|---|
| `oil` | **3,278.8 MW** | fossil; on the legacy override/CSV path |
| `biomass` | 1,865.7 MW | |
| `ST_CHP` | 698.3 MW | its own C1 class (−2.861 / −2.869 / −2.184 TWh) |

This matters because the unlabeled block already holds a marginal unit in **1 of 2025's
15 object hours** (07-28 HE19, $180.99). Lifting CT_PEAKER while oil stays put makes oil
relatively cheaper at the top of the stack, so some marginal energy may migrate to oil
and blunt the price effect. **P-1's band is set wide enough to absorb that; if the
pass-through lands below the band, oil migration is the first thing to measure.**

## 4. THE PHASE-0 EVIDENCE THIS ARM IS AIMED BY (already committed, `_miso220_marginal_class.json`)

`CT_PEAKER` holds the margin in **24 of the 45 object hours** (2023/24/25 = 8/7/9),
`CT_PEAKER|econ` alone in 22. `ST_GAS` holds it in **4 of 45**. Merit-order
reconstruction residual ≤ $0.07 / $0.48 / $1.18, so this is the measured marginal unit,
not an inference. **That is the whole case for holding steam gas:** it is not the price
setter in these hours, and it is the class the model most under-produces
(2024 −7.155 TWh), so holding it should let it gain share rather than lose it.

## 5. PREDICTIONS — scored against interest, bands fixed now

**P-1 (pass-through).** miso-218's uniform ×1.10 measured +7.23 / +7.49 / +6.82 %.
Holding ~11.0 GW of steam gas back should give slightly less. **Predict system
load-weighted price rises +5.5 % to +7.5 % in each of the three years.**

**P-2 (C3a, the target).** Keeper +1.1 / −2.9 / −12.3 %, band ±10 %.
 * **P-2a: all three years land inside ±10 %.**
 * **P-2b (decisive for the lane): C3a-2025 lands in [−8.0 %, −5.0 %]** — i.e. the
   standing failure closes.
 * **P-2c (the tightest): C3a-2023 lands in [+6.5 %, +9.0 %]** and does NOT exit above
   +10 %. Under uniform ×1.10 it reached +8.402 %; holding steam gas should give less.

**P-3 — THE DECISIVE MECHANISM TEST, and the one I most expect to be judged on.**
My claim is that holding steam gas does not merely spare `ST_GAS` but *helps* it: it
becomes relatively cheaper, gains dispatch, and moves toward actual. Uniform ×1.10 sent
`ST_GAS`-2024 the other way (−7.155 → **−8.030**, the cell that killed miso-218).
**Predict `ST_GAS`-2024 lands in [−6.8, −5.0] TWh — strictly better than the keeper's
−7.155 — and `ST_GAS`-2023 (−2.402) and -2025 (−5.820) both improve too.**
**If `ST_GAS`-2024 lands at or worse than −7.155, my mechanism story is REFUTED**, and
the arm's whole rationale for excluding steam gas is wrong even if the gates pass.

**P-4 — THE NAMED RISK, and the most likely kill.** `CT_PEAKER` is lifted while its
nearest competitor is not, so it loses share on top of the uniform effect. Keeper
−5.934 / −3.634 / −3.276 TWh; uniform ×1.10 already sent 2023 to −7.086 (0.914 TWh of
band left). **Predict `CT_PEAKER`-2023 lands in [−8.5, −7.0] TWh — I am explicitly
predicting it MAY EXIT the ±8.00 band, which would fire K-1 and reject the arm.**
This is the mirror image of miso-218's `ST_GAS` exit and I am naming it before the solve
rather than after.

**P-5.** `CC_REGULAR`-2024 (keeper +7.947, only 0.053 TWh of headroom) moves the SAFE
way, into [+5.5, +7.5] TWh, as it did under uniform ×1.10 (+6.564).

**P-6 (the tail — pre-committed as a NON-claim).** The phase-0 ladder shows the price
pinned inside a ~15 GW near-flat `CT_PEAKER|econ` block with the whole stack topping out
near $490 against actuals to $1,782, and an implied marginal-to-actual multiplier of
4.07 / 7.12 / 8.28. **Predict C3c hours above $200/MWh move 3 / 7 / 0 → 3 / 7 / ≤2
against an actual 30 / 37 / 88 — i.e. essentially unchanged.** This arm targets the
MEAN. **No tail claim will be made from it whatever it returns.**

**P-7 (C8).** Forced share rises on every lifted class (a smaller class against the same
floors) — `CT_PEAKER` 0.228 / 0.1573 / 0.1319 rises in all three, 2025 crossing 0.15 —
while **`ST_GAS`'s forced share FALLS** in all three (0.1479 / 0.1555 / 0.2070), because
it dispatches more. A rise in `ST_GAS` C8 would be a second sign P-3 is wrong.

## 6. KILLS — pre-committed, and the promotion rule

* **K-1 — any C1 `fuelmix` cell flips PASS → FAIL.** `CT_PEAKER`-2023 is named ex ante
  (P-4) as the most likely; naming it does NOT exempt it. Firing K-1 REJECTS the arm,
  exactly as `ST_GAS`-2024 rejected miso-218.
* **K-2 — any C3a year outside ±10 %.**
* **K-3 — `ST_GAS`-2024 no better than the keeper's −7.155 TWh** (mechanism refuted).
  K-3 does not by itself reject a gates-clean arm, but it is reported at full magnitude
  in the headline and voids the "holding steam gas helps it" rationale.
* **K-4 — C6 reads UNATTESTED.** A replay writes no attestation; `gen_miso220_attestation.py`
  runs BEFORE scoring. (miso-217's instrument condition, closed in advance.)
* **K-5 — determination worse in class than NOT-YET on C3a-2025 alone.**

**PROMOTION RULE, fixed now:** promote to keeper iff **K-1, K-2, K-4 and K-5 are all
silent AND C3a-2025 lands inside ±10 %.** K-3 firing alone does not block promotion but
is headlined as a refuted rationale. Anything else → register as a candidate, keeper
unchanged, and report why.

## 7. Instruments, committed before the solve

* `scripts/probes/_miso220_offer_table.py` — the tables, with the ratio/hold assertions.
* `scripts/probes/_miso220_liveness.py` → `_miso220_liveness.json` — S-1/S-2/S-3.
* `scripts/probes/_miso220_marginal_class_phase0.py` → `_miso220_marginal_class.json` — §4.
* `scripts/probes/_miso220_ab_gates.py` → `_miso220_ab_gates.json` — the scorer, on the
  `_miso217_ab_gates.py` pattern, with the full 24-cell C1 table frozen from the
  control's own `calibration_verdict.py --json` (§Appendix).
* `scripts/gen_miso220_attestation.py` — run before scoring (K-4).

## Appendix — the control's frozen numbers (from `calibration_verdict.py --json`)

**C3a:** 2023 model 33.21 / actual 32.85 = **+1.1 % PASS**; 2024 31.37 / 32.30 =
**−2.9 % PASS**; 2025 39.87 / 45.46 = **−12.3 % FAIL**.

**C1 `fuelmix`, model − actual TWh, band ±8.00:**

| class | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC_CHP | −0.914 | +0.417 | +1.787 |
| CC_REGULAR | −2.288 | **+7.947** | −2.061 |
| COAL_BIT | −2.272 | −3.390 | −1.465 |
| COAL_LIGNITE | −0.568 | −0.744 | −0.726 |
| COAL_PRB | +1.071 | −2.159 | −4.231 |
| CT_PEAKER | **−5.934** | −3.634 | −3.276 |
| ST_CHP | −2.861 | −2.869 | −2.184 |
| ST_GAS | −2.402 | **−7.155** | −5.820 |

**C8 forced share:** CT_PEAKER 0.2280 / 0.1573 / 0.1319 (budget 0.15);
ST_GAS 0.1479 / 0.1555 / 0.2070 (budget 0.30); CC_REGULAR 0.0 / 0.0 / 0.0.
