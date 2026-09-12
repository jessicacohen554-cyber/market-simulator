# FINDING (pjm-holdout-phase0): the PJM 2020-2022 holdout misses are ONE allocation
# defect, not three — plus two refuted hypotheses and a corrupt EIA-930 series

**Session** `gov-hydro-seam-1` (continued) · **ISO** PJM · **Date** 2026-09-12
**ZERO LP.** Committed artifacts + measured sources only. Nothing solved, nothing registered,
nothing armed, no shared code changed. **PJM keeper UNCHANGED** —
`2026-09-11-pjm-d4-4-gasoutage`, **CALIBRATED, 8/8, zero caveats, zero fails**.

---

## 1. WHERE PJM'S RUBRIC FAILURES ACTUALLY ARE

PJM's keeper has **no failing criterion**. Every PJM rubric failure is on the **held-out years
2020-2022**, and it is **identical across all four touchpoint runs** ever registered
(`pjm-2022-2021-touchpoints`, `pjm-fuelvintage-touchpoints`, `pjm-d4-2-touchpoint`,
`pjm-holdout-gasoutage-touchpoint`) — so it is structural, not a one-off:

> **C1 `fuelmix` FAIL · C3a `price_mean` FAIL · C3b `price_shape` FAIL**, grade 4/8, NOT-YET.
> (C3c is a ledgered caveat and is ACCEPTED — owner, this sitting. Not a target.)

| year | C1 failing class | C3a (model vs actual) | C3b NRMSE (tol ≤0.20) |
|---|---|---|---|
| 2020 | **COAL_BIT +22.832 TWh** (share +2.3pp) | **+22.3 %** ($25.92 vs $21.20) | **0.243 FAIL** |
| 2021 | **CC_REGULAR +26.313 TWh** (+2.4pp) | PASS (+5.8 %) | 0.118 PASS |
| 2022 | **CC_REGULAR +22.562 TWh** (+1.6pp) | **−10.7 %** ($66.13 vs $74.07) | **0.246 FAIL** |

Rule 30(c): none of this downgrades PJM, which stays **CALIBRATED** on 2023-2025.

## 2. IT IS ONE DEFECT, AND IT IS AN ALLOCATION DEFECT

Full model-vs-actual mix on the committed hourlies (hydro actual on the repaired
gov-hydro-seam-1 basis). **Every pinned non-thermal class matches exactly** — wind, solar,
biomass and OTHER to 0.000 TWh, hydro to +0.08-0.09 TWh (i.e. the hydro repair lands PJM's
conventional hydro essentially on the nose), nuclear within ±3.6 TWh. **The entire error is
inside the thermal stack**, and which class absorbs it tracks the merit order: **coal in
2020's cheap-gas year ($1.94/MMBtu EP level), gas CC in 2021/2022** ($3.59 / $6.47).

So C1, C3a and C3b are not three defects. They are one mis-allocation between coal and gas,
read three ways — the class volumes (C1), the level it clears at (C3a) and its time shape
(C3b). **A lane should target the coal-vs-gas merit split, not the three criteria separately.**

## 3. TWO HYPOTHESES MEASURED AND **REFUTED** — DO NOT RE-TEST THEM

* **(R1) "The measured monthly gas level is missing in the holdout years."** **REFUTED.**
  `data.fuel.electric_power.iso_electric_power_monthly_level("PJM", y)` is present and
  non-`None` for **every** year 2019-2025 (means 2.505 / 1.937 / 3.588 / 6.469 / 2.490 /
  2.380 / 3.745 $/MMBtu). There is no coverage gap and no silent fallback to the flat annual
  Henry Hub number. `gas_electric_power_monthly_level` is armed on the keeper recipe.
* **(R2) "The model's holdout-year demand is ~25-29 TWh too high."** **REFUTED.** Model demand
  equals the measured EIA-930 `D = NG − TI` to **0.04 TWh in 2022, 0.03 in 2023, 0.00 in 2024**,
  and is +1.1 % in 2020. The apparent +25-32 TWh "excess generation" is an artifact of summing
  `classFull` (EIA-923-based) as "actual generation": against **EIA-930 net generation** the
  model's total is within **~1.4 %** in every holdout year. *The total-energy story dissolves —
  which is what sent the diagnosis to allocation (§2).* Net interchange is also close: model
  net export 38.81 TWh vs PJM's measured 41.63 TWh in 2020 (`pjm_net_interchange` is
  export-positive).

## 4. THE LIVE LEAD — a PER-YEAR BASIS SPLIT IN THE C1 ACTUAL ITSELF

`render_calibration_html.reconcile_vintage_classes` scales the **combined fossil** EIA-923
total up to the EIA-930 grid series when `923/930 < VINTAGE_RECONCILE_FRAC` (**0.97**,
`scripts/lib/benchmark_semantics.py:69`). Measured on PJM's committed bench parts:

| year | 923 gas+coal | 930 gas+coal | ratio | **reconcile fires?** | C1 verdict |
|---|---:|---:|---:|:--:|:--|
| 2020 | 456.987 | 461.147 | 0.9910 | **no** | FAIL (coal) |
| **2021** | 478.157 | 495.289 | **0.9654** | **YES** | FAIL (CC) |
| **2022** | 483.689 | 499.663 | **0.9680** | **YES** | FAIL (CC) |
| 2023 | 478.875 | 481.679 | 0.9942 | no | PASS |
| 2024 | 498.790 | 490.666 | 1.0166 | no | PASS |
| 2025 | 515.491 | 512.504 | 1.0058 | no | PASS |

**The reconcile fires in exactly two of the six years, and both are holdout years that FAIL
C1.** PJM's 2021/2022 EIA-923 fossil filings under-count EIA-930 by 3.2-3.5 % where every
passing year is within 0.6 %. So the holdout C1 actual is on a **different construction** from
the training C1 actual — the same defect CLASS as the hydro benchmark seam closed earlier today
(`docs/FINDING-gov-hydro-seam-1-2026-09-12.md`), though not the same seam.

**STATED HONESTLY, BECAUSE IT MATTERS: the reconcile is already helping and is NOT on its own
the explanation.** The committed `classFull` values are POST-reconcile, so 2021's CC actual
279.201 is already scaled up (the raw 923 value is ≈269.55); without the reconcile the model
would read +36 TWh instead of +26.3. So closing the 923/930 gap does not by itself close C1.
What the split establishes is that **a lane cannot compare its 2020-2022 C1 residual against its
2023-2025 one without first accounting for the basis change** — and that the residual's
*apparent* year-shape is partly a benchmark-construction artifact. Quantify it before attributing
anything to the model.

## 5. AN INDEPENDENT DATA DEFECT, FOUND IN PASSING AND **NOT** REPAIRED HERE

**`load_eia_hourly_benchmark("PJM", 2021)["net_gen"]` sums to 4,939.01 TWh against a true
~840 — a ~6× corruption in the committed EIA-930 PJM 2021 extract.** The same year's
`interchange` (37.94 TWh) and the bench part's `e930` gas/coal (311.744 / 183.545) are sane, and
the model's 2021 demand (796.17 TWh) is sane, so the LP did not consume it. **What has NOT been
established is whether anything scored reads that series** — C2 (system volume) is the obvious
candidate. **Open item, owner/next-lane call; do not assume it is inert.**

## 6. WHAT THE NEXT LANE SHOULD NOT DO

* **Do not tune the coal/gas offer spread to close the 2020-2022 residual.** The authorized
  `offer_curve_by_group` channel (rules 1/13 amendment) requires **ONE config across EVERY
  scored year**, set ex ante and never swept against the gates. A per-year gas/coal multiplier
  fitted on the holdout residual is exactly the forbidden fit, and it would break the 2023-2025
  keeper that currently reads 8/8.
* **Do not re-test R1 or R2** (§3) without new evidence.
* **Do not attribute the whole 2020-2022 C1 residual to the model** until §4's basis split is
  quantified per class.

## 7. RULES

Rule 29 `[R-SCREEN]` clause 0 — zero-LP phase 0 first; this card completed with **no LP at
all**, which was the pre-registered good outcome. Rule 30(c) — the held-out years do not
downgrade PJM. Rule 31 `[R-RETAIN]` — nothing solved, nothing to retain. Rule 28
`[R-MECH-MATRIX]` — no mechanism was tested, so no cell verdict moves.
