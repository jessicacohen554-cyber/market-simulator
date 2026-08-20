# RESULT nyiso-147 — the 2023 upstate price root cause is CONFIRMED; the measured-BTM arm is REJECTED-AS-ARMED; the keeper is unchanged

Session nyiso-147. Prereg `PREREG-nyiso147-chp-btm-measured-2026-08-20.md`
committed before the arm solved; phase-0 identification
`FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md`; gates record
`_nyiso147_ab_gates.json`. Both runs registered (rule 15):
**`2026-08-20-nyiso-147-control`** (keeper replay at HEAD, byte-identical P1
prices to `2026-08-19-nyiso-146c-state-scoped`) and
**`2026-08-20-nyiso-147a-chp-btm`** (control + `nyiso_chp_btm_measured`).
Years 2023/2024/2025, one bundle each; holdout freeze ACTIVE and untouched.
**Arm B (the cc_reserve_duty_split re-arm) did NOT solve** — its prereg
condition was arm A passing A-K1–A-K6, and arm A failed three gates.

## 1. THE ROOT CAUSE IS CONFIRMED — one field moves C3a-2023 +8.7 % → +1.5 %

The single delta (the measured Gold-Book/EIA-923 CHP BTM shares replacing the
residual-identified 35 % merchant carve) does exactly what phase 0 predicted
on the object it targeted:

| lw system err | control | arm |
|---|---|---|
| 2023 | **+8.7 %** | **+1.5 %** |
| 2024 | +1.6 % | −6.0 % |
| 2025 | −2.2 % | **−12.2 %** |

| Upstate_West eqh err ($/MWh) | control | arm |
|---|---|---|
| 2023 | +7.63 | +5.22 (−32 %) |
| 2024 | +3.54 | **+0.89 (−75 %)** |
| 2025 | +5.79 | **−0.38 (−93 %)** |

The 2023 upstate overpricing — the object this session was chartered on — is
proven to be bought by the CHP capacity carve: with the plants' measured grid
capacities restored, upstate lands within $1 of the actual in 2024/2025 and
the 2023 system error collapses to +1.5 %. Independence dispatches at its
metered scale (5.5/7.3/7.8 TWh vs 4.0/6.2/6.2 metered) instead of being
capacity-blocked; the phantom BTM add-back collapses 5.93 → 1.70 TWh (CC_CHP
2023).

## 2. WHY IT IS NOT THE KEEPER — the carve was masking two more defects

A-K1 PASS (exactly one field), A-K2 PASS (capacities live to the MW;
add-back collapse on-prediction). The three failures, each a REAL finding:

1. **A-K4 — Selkirk (10725) convicts, exactly as pre-named.** The
   semi-mothballed 754-MW CC (metered 92 GWh in 2024) dispatches **730 GWh
   (7.9×)** once its capacity is restored — a NEW member of the
   merit-order-inversion class (nyiso-145 defect B), on the CHP side where
   `cc_reserve_duty_split` (CC_REGULAR-scoped) cannot reach it. Capacity
   truth without conduct truth manufactures phantom energy.
2. **A-K5 — C1 fails against the arm's own corrected bench.** CC_CHP
   over-runs +5.0 TWh (2023, 2024) and CC_REGULAR under-runs −3.96 TWh
   (2023): the LP runs the restored plants at their offers' implied CF
   (Independence 1.36×/1.19×/1.26× of meter; Linden at its full grid share
   every year), where the real plants cycle at 0.4–0.7 CF on maintenance and
   above-SRMC offer behavior the model does not carry for this class.
3. **A-K5 — C3a-2025 −12.2 % / C3b-2025 NRMSE 0.210.** The dear-gas year's
   control "pass" (−2.2 %) was itself cancellation: the missing ~1.3 GW of
   cheap CHP capability was propping the 2025 level up. Restored, every zone
   falls ~$6 and the year breaks the band. (A-K3's 2023 leg also missed its
   ≥40 % bar at −32 %, though 2024/2025 cleared at −75 %/−93 %.)

**Owner standing clause considered and NOT applied**: this is not "gates
regress on a structurally superior arm" — the regressions are the carve's
masked defects becoming visible, and promoting would swap a CALIBRATED keeper
for a NOT-YET run (C1+C3a+C3b load-bearing failures). The measured artifact
and wiring SHIP regardless (rule 14; default-off), the same disposition as
pjm-146's RGGI adder: built, gated, held pending its co-requisites.

## 3. WHAT THIS LEAVES ON THE QUEUE (the named successors)

1. **CHP conduct** — the restored capacity needs the class's real operating
   behavior before the shares can arm: (a) an idle/lay-up membership leg for
   the CHP fleet (Selkirk first — the nyiso-140/144 zero-cell criterion
   applied beyond the bridge population), and (b) the CC_CHP offer/CF
   question (maintenance + above-SRMC offers for merchant cogens; the
   reserve-duty-split's duty-role logic is the nearest built lineage but is
   CC_REGULAR-scoped).
2. **The 2025 level interaction** — the control's 2025 −2.2 % is now known
   to be ~$6/MWh of masked under-pricing; any future arm that adds cheap
   supply re-exposes it. Its root cause (dear-gas-year offer levels /
   the anchor's year response) is a separate object.
3. The joint object's arm B (`cc_reserve_duty_split` re-arm) remains
   conditioned on a passing repair of the 2023 upstate level; its standing
   prereg gates are untouched.

## 4. REPRODUCTION

```
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso147_armA_recipe --out-dir results/calibration/nyiso147_armA
PYTHONPATH=.:src python scripts/probes/_nyiso147_ab_gates.py
python scripts/calibration_verdict.py --run-id 2026-08-20-nyiso-147a-chp-btm
```
