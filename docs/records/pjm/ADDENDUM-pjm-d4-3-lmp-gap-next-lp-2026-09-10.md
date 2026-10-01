# ADDENDUM pjm-d4-3 — gen-by-fuel conditioned on WHERE the LMP is missing, and the next LP it names

**Zero LP.** Committed artifacts only (keeper payloads, bench parts, `hourly/system_*`,
`hourly/reserve_family_*`) plus `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`.
Owner instruction 2026-09-10: *"look at gen by fuel and when LMP is missing to determine the next
lp to test for PJM."*

## 1. WHERE THE LMP IS MISSING — and it is one place

Hours bucketed by model-minus-actual-RT price error; gen error = model − CAMPD meter, TWh summed
over the bucket's hours.

| 2022 bucket | h | model $ | actual RT $ | err | CC_REGULAR | COAL_BIT | CT_PEAKER |
|---|---|---|---|---|---|---|---|
| **p<10 (model FAR under)** | 876 | **82.4** | **182.5** | **−100.2** | **+4.040** | +1.894 | −0.155 |
| p10-25 | 1314 | 71.8 | 85.4 | −13.6 | +5.191 | +1.726 | −0.378 |
| p25-75 (mid) | 4380 | 59.0 | 54.1 | **+4.9** | **+16.208** | +1.740 | −1.449 |
| p75-90 | 1314 | 56.9 | 43.4 | +13.5 | +4.946 | +0.580 | −0.300 |
| p>90 (model FAR over) | 876 | 62.8 | 41.8 | +21.0 | +3.527 | +0.255 | −0.170 |

**The model prices ABOVE actual through the middle of the distribution and collapses at the top.**
The upper tail is simply absent:

| year | actual h RT>$200 | model h | actual h RT>$500 | model h | tail's $/MWh of the ANNUAL mean | **C3a miss** | **tail as % of miss** |
|---|---|---|---|---|---|---|---|
| 2020 | 2 | 2 | 0 | 0 | 0.07 | +21.0 % (over) | — |
| 2021 | 23 | 4 | 1 | 0 | 0.61 | +5.8 % (over) | — |
| **2022** | **92** | **0** | **26** | **0** | **5.78** | **−8.0 %** ($5.48) | **105 %** |
| 2023 | 6 | 0 | 1 | 0 | 0.19 | +0.8 % | — |
| 2024 | 18 | 0 | 0 | 0 | 0.43 | −2.8 % ($0.81) | 52 % |
| 2025 | 59 | 17 | 9 | 0 | 1.82 | −6.1 % ($2.63) | 69 % |

**2022's entire C3a failure is the missing tail** — 92 hours carry $5.78/MWh against a $5.48/MWh
annual miss, and the 26 hours above $500 carry $4.52 of it on their own. The same 92 hours are
what C3b's NRMSE 0.262 is measuring. **2020 is the opposite defect and is NOT this card**
(model +21.0 % OVER, tail already reproduced 2/2).

## 2. THE MECHANISM THAT SHOULD FORM THE TAIL IS INERT — measured, not inferred

`hourly/reserve_family_2022.parquet`, the only artifact in which a family's binding is observable
(rule 15). PJM runs `pjm_primary` + `pjm_primary_mad`, both `reserve_class 0`:

| year | family | hours dual > 0 | max dual | shortfall hours | min(held − req) | **dual in the actual RT>$200 hours** |
|---|---|---|---|---|---|---|
| 2021 | pjm_primary | **0** / 8760 | −0.00 | 0 | 0.0 | **−0.00** (23 h) |
| **2022** | **pjm_primary** | **0** / 8760 | **−0.00** | **0** | **0.0** | **−0.00** (92 h) |
| **2022** | **pjm_primary_mad** | **0** / 8760 | **−0.00** | **0** | **0.0** | **−0.00** (92 h) |
| 2023 | pjm_primary | 0 / 8760 | −0.00 | 0 | 0.0 | −0.00 |
| 2024 | pjm_primary / _mad | 1 / 14 | 3.53 / 53.12 | 0 | 0.0 | ≤1.60 |
| 2025 | pjm_primary / _mad | 21 / 37 | 189.95 / 91.13 | 0 | 0.0 | 189.95 / 91.13 |

**In 2022 the co-optimisation's reserve dual is exactly zero in 8,760 of 8,760 hours, and `held`
equals `requirement` to the MW in every one** — reserve is free everywhere, including the 92 hours
PJM was pricing at $182 average and the 26 it was pricing above $500.

This matters for governance: `ordc_scarcity_overlay` is `G` in PJM's matrix on the stated ground
that *"the in-LP co-opt already owns the phenomenon with PJM's published two-step ORDC curve
loaded, so an adder would still be a rule-19 stack."* **The owner of the phenomenon produces a
dual of 0.00 in every hour of the year that most needs it.** The refusal's premise is measurably
false in 2021, 2022 and 2023 — which is not an argument for the adder (a stack on an inert
mechanism is still a stack), but is an argument that the co-opt's own operands are the object.

**Why it cannot bind:** the requirement is PJM's measured **Primary** series only — mean
2,663 MW, max 4,224 MW — read through `("Primary","RTO")` of the published ORDC curve
(`model/reserves/spec.py`). Against it the model carries headroom of a different order (§3).

## 3. AND THE HEADROOM IS THE REAL OBJECT — with my own first number CORRECTED

Model thermal dispatch vs the CAMPD meter, in the hours the price is missing:

| | model | meter | **model − meter** |
|---|---|---|---|
| 2022, all hours | 59.0 GW | 54.7 GW | +4.3 GW |
| **2022, actual RT>$200 (92 h)** | **89.9** | **80.1** | **+9.7 GW** |
| **2022, actual RT>$500 (26 h)** | **89.1** | **78.0** | **+11.1 GW** |
| 2022, Winter Storm Elliott Dec 23-24 | 80.9 | 72.9 | +8.0 GW (actual RT averaged **$844**) |
| 2025, actual RT>$200 (59 h) | 95.2 | 88.7 | +6.6 GW |

**The over-dispatch more than DOUBLES in the tail hours** (+4.3 GW average → +9.7/+11.1 GW), i.e.
the model has thermal units running that the meter says were not. That is the same signal as the
CC_REGULAR "hours leg" of RESULT §2, seen from the price side.

**CORRECTION, against my own working note.** A first pass put unused thermal at 43-61 GW in those
hours by differencing bench nameplate (150.6 GW) against dispatch. **That is wrong and overstates
it badly**: pjm-161 measured that the model already asserts **41.7/43.2/41.2 GW** of annual-mean
fossil-thermal outage — *more than PJM publishes for its entire fleet* (33.3/33.0/35.9 GW) — and
pjm-162 measured that **19.2-20.4 % of model fossil nameplate sits at HARD ZERO every day**
(layup / retiree CEMS cap / COD mask / full windows), which PJM's record does not carry as outage
at all. Net of the asserted outage the real headroom in the tail hours is **≈19 GW**, not 43-61.
**The conclusion survives the correction** — 19 GW still swamps a 2.7-4.2 GW requirement, so no
reserve requirement of any defensible size can bind — but the number is restated at its true
size.

## 4. THE NEXT LP — and the DO-NOT-REDO check that shapes it

**The object is the COMPOSITION of PJM's availability envelope at constant level, not its level.**
The level route is closed in both directions and neither closure is re-opened here:

* **Adding outage** contradicts pjm-161's measurement that the model's outage level already exceeds
  PJM's published fleet-wide record. Refused.
* **Removing outage** — `pjm_measured_outage_event_cap` — is **`R`** (pjm-161, both arms
  registered): P4 failed outright, hours>$200 **unchanged** at 3/10/32, top-1 % net-load
  unavailable MW unchanged 23,160 → 23,160. Do not re-test.
* **Restoring capacity** — `dam_availability_rebasis` — is **`G`**, and pjm-162 closed its
  re-open condition ex ante: the restore form is **anti-targeted**, giving capacity back
  (+7.0 to +12.4 GW) precisely where the envelope is already too shallow.
* `temp_dependent_derate` is **`R`** (pjm-95 demotion). Do not re-test.

**What none of those touched is pjm-162's own named root cause**: a fifth of the model's fossil
nameplate is at **hard zero every day** rather than present-and-expensive. In the real market that
block was *available at a high offer* and is what set $500-1,500 in the 26 hours the model prices
at ~$63. Moving it from hard-zero into the stack at its own offer is a **composition** change that
leaves the asserted outage level alone — the one form pjm-161 (remove-only, level) and
pjm-145/162 (restore ceiling, anti-targeted) both left untested.

**Candidate arms, all `U` (untested) in PJM's shard, so no DO-NOT-REDO bar:**
`unit_outage_lp_capacity_basis`, `unit_outage_extract_basis_share`, `unit_outage_per_unit_clip`,
`historic_outage_overlay`.

**Before any LP, the phase-0 that decides it (zero LP, ~90 s):** census the hard-zero block by
cause (layup / retiree CEMS cap / COD mask / full window), by class, and by hour, and intersect it
with the 92 RT>$200 hours. The pre-solve gate writes itself and is structural, not residual: does
the block that is at hard zero in those 92 hours exceed the 19 GW of headroom that currently keeps
the reserve dual at zero? **If it does not, no composition change can form the tail either, and the
card dies at zero LP.** If it does, the screen year is **2022** — by footprint (92 tail hours vs
6-59 elsewhere), not by residual — and the pre-registered gates are the reserve dual becoming
non-zero in those hours and the model−meter thermal gap closing from +11.1 GW, with C3a/C3b
reported and never gated.

**What this card does NOT reach, stated now:** 2020's C1 (COAL_BIT +21.97 TWh) and its C3a
**+21.4 % OVER** are the opposite defect and need their own object; and the chronic online-hours
leg present in the CALIBRATED years (RESULT §2) is only partly the same thing.
