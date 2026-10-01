# FINDING — ERCOT-116: half the ~19 pp coal seasonal term IS the statistical availability model; the other half is a within-envelope merit-order bias the estimate was masking

**Date** 2026-07-26 · **ISO** ERCOT · **Years** 2023–2025 (one invocation, years sequential) ·
**Arm** `ercot116_coal_avail_on_keeper` = the ercot115 keeper + `ercot_thermal_dam_availability_coal`
(single delta, `replay_keeper`) · **Run id** `2026-07-26-ercot116-coal-avail-probe` ·
**Pre-commit** `PRECOMMIT-ercot116-coal-avail-on-keeper-2026-07-26.md` (pushed at `b144573`
with the mechanical scorer `scripts/probes/ercot116_seasonal_shape.py` BEFORE any year was solved) ·
**Determination** NOT-YET (rejected probe; keeper unchanged)

## 1. The question and the no-LP answer that preceded the solve

ERCOT-116 asked: **what is the statistical coal-availability model silently compensating
for?** The charter's suggested first move — decompose the ERCOT-112 arms BY MONTH from
committed sidecars, no solve — settled the decisive question before any LP ran:

* In the keeper, the matched-price-band excess seasonal lift (model summer-minus-shoulder
  utilization lift minus actual, at MATCHED absolute price) is **19.2 / 18.6 / 20.6 pp**.
* In ERCOT-112 arm B (measured coal envelope, old code) it is **7.4 / 10.6 / 11.5 pp** —
  and arm B's level break is **uniform**: positive in every price band of both seasons of
  all three years (+2.9 to +18.0 pp). Shape fixed, level broken, effects separable.
* The measured driver is real: the measured live/rating coal fraction is **0.10–0.13
  HIGHER in Jun–Sep than in the shoulder** (real coal takes planned outages in
  spring/fall); the statistical estimate misses that asymmetry.

## 2. The arm (G0: armed and biting)

Both overlays fired in all three years (`coal econ marginal-HR floor` 3/3;
`COAL plant-grain redistribution — 10 crosswalked plant(s), 0 unmapped tranche(s)` 3/3,
median class targets 0.827 / 0.787 / 0.757), both flags recorded in `run_config.json`,
solved at `b144573` on the current (`ff0109c`-corrected) base. Coal moved
+6.8 / +9.2 / +12.9 TWh vs the keeper — armed, biting, not inert.

## 3. Verdict against the pre-committed gates (`ercot116_seasonal_shape.py`)

| year | excess keeper→arm (pp) | spread keeper→arm | annual ratio keeper→arm | C3a keeper→arm (pp) | C3c keeper→arm (h, act) |
|---|---|---|---|---|---|
| 2023 | 19.18 → **10.04** (−9.1) | +0.435 → **+0.233** | 0.953 → 1.061 | −16.6 → −24.2 | 72 → 49 (181) |
| 2024 | 18.57 → **12.87** (−5.7) | +0.591 → **+0.400** | 0.975 → 1.132 | +1.3 → −5.7 | 13 → 7 (53) |
| 2025 | 20.59 → **13.38** (−7.2) | +0.333 → **+0.230** | 0.951 → 1.154 | +1.5 → −4.1 | 1 → 1 (31) |

| gate | result |
|---|---|
| **G0** arming + bite | **PASS** (3/3 + 3/3 lines; +6.8/+9.2/+12.9 TWh) |
| **G1** matched-band excess falls ≥ 5.0 pp every year | **PASS** (−9.1 / −5.7 / −7.2) |
| **G2** ratio spread narrows every year, mean ≥ 0.10 | **PASS** (−0.202 / −0.191 / −0.103; mean 0.165) |
| **G3** scarcity/price not degraded (C3a ≤ 2.0 pp, C3c ≤ 5 h) | **FAIL** (C3a degrades 7.6 / 7.0 / 5.6 pp) |
| **G4** LOYO — G1+G2 in all three years | **PASS** (3/3) |

**Shape gates pass everywhere; the price-level gate fails everywhere. REJECTED as a
keeper candidate; the finding stands.** Registered NOT-YET: C1 COAL_PRB 2025 +8.66 TWh
out of band (C1 15/16, free 11/12), C3a energy-only −35.2/−14.5/−13.0 %, C4 2024 coal
r = 0.864 with NRMSE 0.301. The keeper remains `2026-07-26-ercot115-coal-marginal-hr`.

## 4. What ERCOT-116 establishes

1. **Roughly half the ~19 pp seasonal term is the statistical coal-availability model's
   seasonal profile.** Swapping in the measured envelope (a rule-13 measured input —
   physical committed capability, reproducible forward) removes 5.7–9.1 pp of the
   excess and 0.10–0.20 of the monthly-ratio spread, in every training year, on the
   current base. Under rule 14 this is the estimate's *seasonal* error, now measured.
2. **The other half is within-envelope over-dispatch at matched price, and the estimate
   was silently compensating for it at the LEVEL.** With the true (measured) envelope,
   coal over-runs +6.8–12.9 TWh annually and suppresses the load-weighted price by
   5.6–7.6 pp. The statistical estimate's too-tight shoulder envelope was absorbing —
   hiding — a real merit-order bias: the ERCOT-113 displacement result
   (corr(dCoal, dGas) = −0.93 to −0.97, offset ~100 %) says the surplus coal is exactly
   the missing gas, i.e. coal is priced too cheap *relative to gas* in the $10–30 mid-merit
   range where both are marginal. That bias, not availability, is the residual seasonal
   term's owner: summer has more mid-merit hours, so a season-invariant merit-order bias
   expresses seasonally.
3. **No promotion is recommended.** The measured-envelope arming stays available and
   default-off; the keeper is unchanged. Per rules 1/13/14 the estimate may not be
   defended *because* it fits better — it survives only until the merit-order bias it
   compensates is fixed, at which point the measured envelope should be re-armed and is
   expected to pass. That is the successor lane's exit criterion.

## 5. The successor lane (ERCOT-117 candidate charter)

**Find the coal-vs-gas mid-merit ranking bias that the statistical availability estimate
is compensating for.** Concretely measurable, no-LP first:

* The model's full-passthrough coal SRMC tops out near **$28/MWh** while the real
  fleet's top submitted DAM coal offer is **~$21** (ERCOT-112 §6) — the model's coal
  offer curve is too WIDE at the top yet dispatches too MUCH: the bias is therefore in
  the low/mid tranches (take-or-pay share, PRB sigmoid floor 0.76, lignite floor 0.675)
  or in the gas side of the ranking (envelope-pinned gas classes' offer levels), not in
  the coal curve's reach. The F923 delivered-fuel-price receipts question is the named
  measured lead.
* The per-band signature to reproduce: arm B's gap vs the measured envelope is +9–29 pp
  in the $15–25 bands (both seasons) — the exact bands where coal and CC gas cross.
* Gate any candidate on the ERCOT-116 metrics (matched-band excess + spread + C3a),
  with the measured envelope ARMED — the compensator must not be re-tuned around the
  estimate (rule 14).

## 6. Declared-not-counted, honoured

No price-MAE argument was made in either direction; the annual level regression was
predicted in the pre-commit and is reported as the discovered-bug signal, not grounds to
revert the measured input (rules 1/13/14); the ≥$300 scarcity set was not read as
evidence (C3c falling 72→49 in 2023 is the price-suppression side-effect, reported under
G3, not a tail claim).
