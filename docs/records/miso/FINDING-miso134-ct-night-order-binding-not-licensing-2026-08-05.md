# FINDING — miso-134: MISO's `CT_PEAKER` July-night deficit IS an ORDER object and the constraint DOES bind — and the only zero-DOF lever is still REFUSED, because the swap is a CATEGORY ERROR and the class is already at annual parity

**Session:** miso-134, 2026-08-05, branch `claude/miso-134-calibration-ys5txh`,
off `origin/main` at `57120845`.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED.** MISO keeper unchanged at
**`2026-08-05-miso-132b-cc-committed`** (bundle `results/calibration/miso132_ccmin_B`,
**NOT-YET**, sole FAIL C7 `COAL_PRB` 2025 `cv_ratio` 0.338 vs 0.50, ledgered
caveats 2/3 {C3a, C3c}). Rule 22 `[R-HOLDOUT]`: 2023–2025 only — MISO holds no
marker; no 2022 / 2019 / H1-2026 year was solved, scored or read.

**Pre-registration** `results/calibration/PREREG-miso134-ct-peaker-night-order-screen-2026-08-05.md`,
committed and pushed at **`06918ca1`** *before* any adjudicating statistic.
**Probe** `scripts/probes/_miso134_ct_night_order_screen.py`; **record**
`results/calibration/_miso134_ct_night_order_screen.json`.

**Lane:** charter option **(a)** — the new-evidence ORDER-dimension screen on the
`CT_PEAKER` overnight row of `FINDING-miso133-overnight-identity-basis-2026-08-05.md`
§4 (**−854 / −691 / −666 MW** at July night h0–5, grid-delivered both sides).

---

## 1. Headline

Five consecutive MISO lanes died because the thing they targeted turned out not
to be there: granularity was inert at the gated grain (miso-131), the reserve
constraint was 9× slack (miso-132(a)), the overnight capability was ~41 GW idle
(miso-133). **This one is different. The object is real, it is an ORDER object,
and the constraint BINDS.**

The `CT_PEAKER` econ band is offered at a **residual-identified** 1.0 × base heat
rate over a measured incremental burn of 0.687/0.691, and under the armed
`gas_offer_net_revenue_margin` form that gap is a fuel-invariant **$7.32/MWh**
cap-weighted margin (median **$10.98/MWh** on the 11,050.6 MW that carries one).
Removing it in full brings **2,944.6 / 3,299.5 / 4,130.5 MW** of CT capacity into
merit at the keeper's own July-night prices — **3.4× / 4.8× / 6.2×** the
miso-133 §4 shortfall. **S-2 PASSES in 3 of 3 years.** What prices MISO's peakers
out of the July night is now named and measured.

**And the arm is REFUSED anyway**, on the pre-registered S-3 bar, in 3 of 3 years
(the bar needed only 2). The refusal is not close and it is not a compute
limitation:

> The model's `CT_PEAKER` is **already at 0.988 / 0.949 of EIA-923 actual**
> annual energy. The full swap multiplies its price-taking energy by
> **2.29 / 2.17 / 2.12**. There is **+4.70 / +0.23 / +0.95 TWh** of room to
> parity and the lever wants ~20–30.

Behind the arithmetic is a harder result that closes the lane permanently
(§4): **the proposed swap is a category error.** `marg_econ_low_p50` = 0.687 is
the measurand for **`phys_econ_low`** — and the keeper already carries it there,
exactly. It is *not* the measurand for the offer multiplier.

---

## 2. Verdicts against the pre-registered bars

| bar | result |
|---|---|
| **S-0** construction validity (GATING) | **PASS.** Assembled CT capacity **22,281.8 MW** vs the 22,291.8 MW reference — **−0.04 %** against a ±2 % bar. Cap-weighted plant-grain base heat rate **12.0351**, reproducing miso-117b's published 12.0351 **exactly**. 516 CT plants. Price-taking reconstruction of the keeper's own July-night CT dispatch: 629.2 / 1,779.5 / 1,875.6 MW against the keeper's 321.0 / 1,257.9 / 1,350.1 MW ⇒ the bound runs **1.96× / 1.42× / 1.39×** hot, disclosed and used in §3. |
| **S-1** markup census | econ band **17,977.9 MW** at cap-weighted **$7.321/MWh**; committed band **$0.000** (already measured-grounded at 1.025 = `phys_committed`); peak band $75.67 — the deliberate MISO-cap scarcity wall, **not touched by the arm**. July-night cap-weighted availability 0.8112. |
| **S-2** reachability (THE BAR) | **PASS 3/3.** See §3. |
| **S-3** C1 counter-risk | **REFUSAL FIRES 3/3.** See §3. |
| **S-4** identification (declared UNGATED) | residual margin is **3.14×** MISO's own measured start recovery (**$7.321** vs **$2.335**/MWh cap-weighted, 654 tranches carrying a measured run horizon); **4.70×** on the markup-carrying tranches alone. Descriptive — no verdict taken from it. |
| **S-5** two grains | **THE GRAINS DISAGREE**, reported not buried (§5). Plant/tranche grain governs by pre-registration and PASSES; class grain FAILS. |
| **S-6** displacement (gates the C7 CLAIM only) | **SUPPORTED 2023/2024, FAILS 2025** — the only C7-failing year (§6). |

**Decision, per PREREG §4.3: S-2 PASS + S-3 refusal ⇒ ARM REFUSED.** K1 honoured
(nothing sized on any Δ; no field created). K5 honoured (no tuned Δ was
computed or proposed). K7 honoured (no artifact re-derived). K8 honoured (no
adjudicated cell re-opened).

---

## 3. The two numbers that decide it

**S-2 — the constraint binds.** `R(Δ_max)`, mean MW of CT capacity newly at or
below its own zone's keeper-solved price over July nights, at the full
econ-band swap:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `R(Δ_max)` MW | **2,944.6** | **3,299.5** | **4,130.5** |
| miso-133 §4 shortfall MW | 854 | 691 | 666 |
| multiple | **3.4×** | **4.8×** | **6.2×** |

Even discounted by the S-0-measured price-taking bias (÷1.96/1.42/1.39) it is
1,502 / 2,332 / 2,974 MW — still 1.8× / 3.4× / 4.5×. The 2025 reachability curve
is smooth and the shortfall is crossed at **Δ ≈ $3.2/MWh**, well inside the
$7.32 available: 190 MW at $1, 621 at $3, 1,225 at $5, 2,038 at $7, 3,324 at $10.

**S-3 — and that is exactly why it is refused.** The pre-registered annual leg
plus a disclosed, tighter refinement. The raw price-taking bound adds
**25.9 / 30.8 / 26.9 TWh/yr** to a 12.6–17.1 TWh class, which is loose because it
ignores the demand constraint entirely. The **ratio estimator**
`E_pt(Δ_max) / E_pt(0)` carries the same bias in numerator and denominator, so it
cancels:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| ratio estimator ×    | **2.29** | **2.17** | **2.12** |
| keeper model TWh     | 14.496 | 19.062 | 17.479 |
| EIA-923 actual TWh   | 19.199 | 19.296 | 18.425 |
| keeper C1 ratio      | 0.755 | **0.988** | **0.949** |
| **predicted arm C1 ratio** | **1.73** | **2.14** | **2.01** |
| headroom to parity TWh | +4.70 | **+0.23** | **+0.95** |

The lever would roughly **double** a class that is already within 1.2 % (2024)
and 5.1 % (2025) of its measured annual energy. The refusal does not depend on
either estimator's calibration: any pass-through above ~5 % of the price-taking
bound breaks 2024.

---

## 4. Why the lane is CLOSED and not merely blocked — the category error

The pre-registered arm was modelled on miso-132(b), and the analogy fails on
inspection. **miso-132(b) swapped a PROXY for its own MEASURAND**: the registered
`committed: 1.20` was a generic "part-load ~30–40 % premium" *claim about* the
min-load block-average burn, and `avg_committed_p50` = 1.005 **is** that burn.
One measurand, one slot, zero DOF, strictly better.

**Here the measurand is already in its slot.** `marg_econ_low_p50` / `_high_p50`
= 0.687 / 0.691 are the measurands for **`phys_econ_low` / `phys_econ_high`**,
and the keeper carries them there **exactly**. The offer multiplier `econ_low` is
a *different quantity* — by the margin form's own construction it is
`phys + margin`, and the margin's measurand is **offer conduct**, not incremental
burn. Setting `econ_low := phys_econ_low` therefore does not import a
measurement; it **asserts that a MISO peaker offers its energy at marginal burn
with zero net-revenue margin.** That claim:

1. has **no measured support at MISO** — no MISO submitted-offer corpus at the
   grain that would identify it was found or used here;
2. is **contradicted by the class's own annual volume** — at the incumbent markup
   `CT_PEAKER` lands at **0.988 / 0.949** of EIA-923, i.e. the level is
   approximately *right*, which is positive evidence *for* a non-zero margin; and
3. would be **rule 1 `[R-STRUCT]`-forbidden**: reaching a night number through a
   mechanism that is not real. Real peakers do not bid at marginal burn.

So the finding is **not** "the markup is wrong and we cannot afford to fix it."
It is: **the markup has not been shown wrong, the one zero-DOF change available
is not the measurement it appears to be, and the only thing that would hit the
night target is a tuned partial Δ — which K5 and rules 1/24 forbid in advance.**
Under rule 20 `[R-DOF]`, *"a residual that can only be closed by a tuned value is
an open root-cause issue, not a parameter"* — that is exactly this residual's
status, and naming it as such is the result.

**What the object actually is.** The model carries approximately the **right
annual CT energy in the wrong HOURS**: 0.95–0.99 of actual over the year, 666–854
MW short at July night, 6.1 % dispatched there. The residual margin is
fuel-invariant **and hour-invariant** by construction, so removing it moves every
hour by the same $/MWh — which is why S-2 and S-3 fire together. **A LEVEL lever
cannot fix an HOUR-DISTRIBUTION defect.**

---

## 5. The grain disagreement, recorded rather than buried

S-5 pre-registered both grains and declared the plant grain governing. They
disagree, and the disagreement is instructive:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| class-grain cap-wtd econ offer, July night ($/MWh) | 54.03 | 43.64 | 50.61 |
| class-grain load-wtd price, July night ($/MWh) | 28.23 | 25.50 | 34.08 |
| gap | 25.80 | 18.14 | 16.53 |
| Δ_max available | 7.321 | 7.321 | 7.321 |
| class-grain verdict | FAIL | FAIL | FAIL |
| **plant/tranche-grain verdict** | **PASS** | **PASS** | **PASS** |

The class average says the swap cannot reach; the tranche grain says 2.9–4.1 GW
enters. Both are correct about different things: the cap-weighted *average* offer
of a 22 GW ladder is dominated by its expensive tail, while the MW that actually
enters is the cheap end. This is **miso-117b's lesson recurring on a different
quantity** — *"a class-average heat rate is the wrong statistic for a dispatch
prediction"* — and it generalises: **a class-average OFFER is the wrong statistic
for a reachability prediction.** Had this screen been run at the class grain
alone it would have returned the opposite verdict on S-2.

---

## 6. S-6 — the C7 claim fails independently, in the year that matters

MW-weighted share of the newly-entering CT capacity priced below the **hour's
own** marginal `COAL_PRB` econ offer:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| entering CT offer p50 ($/MWh) | 23.94 | 21.58 | **28.91** |
| marginal PRB econ offer p50 ($/MWh) | 28.09 | 26.06 | **28.00** |
| **entering MW share below marginal PRB** | **0.993** | **0.972** | **0.279** |

In 2023 and 2024 essentially all of the entering CT would undercut the marginal
coal block. **In 2025 — the one year C7 `COAL_PRB` fails — only 27.9 % would**,
and the entering band's p50 sits *above* the marginal PRB block. So even on an
S-2 PASS the lever could not have been claimed as a C7 instrument, independently
of the S-3 refusal. Per the PREREG the C7 claim is **not admissible** and is not
made.

This is the miso-130 regime statistic seen from a third direction: 2025's gas
re-pricing lifts the whole gas stack past the cheap-PRB majority, so a gas-side
order lever reaches the *price* but not the *block*.

---

## 7. S-4, banked and ungated

MISO's measured start recovery on the same tranches
(`startup_cost / fast_start_run_hours`, `campd_ct_run_lengths_MISO.csv`, 654
tranches) is **$2.335/MWh** cap-weighted. The residual econ margin is
**3.14×** that on the whole econ band and **4.70×** on the markup-carrying
tranches alone. MISO arms **both** mechanisms simultaneously
(`tranche_startup_amortization` + `_measured_runs` + `_conditional_runs`, all
ledgered measured-physical, **and** `gas_offer_net_revenue_margin`).

**No verdict is taken from this** — it was declared ungated in advance and
nothing here is sized on it. It is banked for whoever next examines MISO's gas
offer identification. Rule 25 `[R-ISO-SCOPE]`: CAISO's structurally identical
measurement (its `CT_PEAKER` margin 2.19–7.86× its own measured $3.85 start
recovery, the ground on which `tranche_startup_amortization` CAISO went `U → G`)
is cited as precedent for *making the comparison* and **transfers no verdict**;
MISO's number is measured on MISO's own artifacts and MISO arms both mechanisms
where CAISO arms one.

---

## 8. The generalisable lesson — **BINDING IS NOT LICENSING**

miso-132(a) taught *"a missing market rule is not automatically a binding one"* —
measure the constraint's slack before building. **miso-134 is its mirror image,
and it is the harder half:** this constraint **does** bind, comfortably, in
exactly the hours it was recruited for — and the lever is still refused, because
**a lever that binds in the target window also binds in every other window.**

> **Before arming a lever that clears its target-hour bar, measure what it does
> OUTSIDE the target window — on the same fleet assembly, with no LP.** A class
> already at annual parity cannot absorb a level lever, however well the level
> lever reaches at night.

And the second half, which is why the closure is permanent rather than
compute-blocked: **check that the "measured" value you are importing is the
measurand of the slot you are putting it in.** A physical-basis measurement
(`phys_*`) and an offer multiplier are different quantities; a swap between them
is not a rule-14 `[R-ACCURATE]` upgrade, it is an un-evidenced conduct claim
wearing a measurement's clothes.

The family now reads: miso-129 *a signature is not a cause* → miso-131 *a
plant-grain signature is not a class-grain defect* → miso-132(a) *a missing rule
is not a binding one* → miso-133 *measure the slack, on one basis* → **miso-134
*binding is not licensing, and a level lever cannot fix an hour-distribution
defect*.**

---

## 9. Consequences for the queue

1. **The `CT_PEAKER` econ-band LEVEL lane is CLOSED on identification** (§4), not
   on compute and not on the C1 arithmetic alone. **DO NOT re-open it** by
   proposing the same swap with more memory, and **DO NOT** propose a partial Δ —
   K5 and rules 1/24 forbid it in advance, and §4 removes its premise.
2. **The miso-133 §4 `CT_PEAKER` row is now attributed**: it is an
   **hour-distribution** defect on a class at annual parity, not a level defect.
   The class-grain object is stated and handed forward with its size (§3, §4).
3. **NAMED, NOT CHARTERED — the only admissible successor shape.** Any future CT
   lever at MISO must be **hour-organizing**, not level: the incumbent margin is
   hour-invariant by construction and that is precisely why it cannot deliver.
   Its binding prerequisite is an **identification for within-day MISO CT offer
   conduct that is not the C7 residual** — MISO publishes no submitted-curve
   corpus at the grain the `measured_offer_surface` family needs, and without
   such a source the mechanism is a rule-21/24 fitted path and inadmissible.
   That prerequisite is a **data question**, and this session neither answers nor
   assumes it.
4. **The `CT_PEAKER` bench-coverage question stays closed** — miso-133 §5 already
   established that the residual gap is real machines CEMS cannot see, so no
   bench-repair charter is owed and none is opened here.
5. **A matrix hygiene observation, NAMED not chartered and NOT edited:** the
   `measured_offer_surface` row's `cells` string is `KKRUGI` (MISO = **`U`**)
   while its own `note` prose says *"MISO cell R inherits only the MISO-specific
   refusal of SOM deep-discount premise (MISO-53)"*. The two disagree about
   MISO's status. This session tested no part of that row, so under rule 28(b) it
   stamps nothing there; the discrepancy is flagged for the session that next
   touches it. It matters for consequence 3, whose successor would land on that
   row.
6. **DO-NOT list carried forward, unchanged and extended by §9.1:** no fitted
   trough adder; no 2025-specific lane (miso-128); no capability-side overnight
   lever (miso-133 §6); no re-opening of offer granularity (miso-131), reserve
   online-gating (miso-132(a)), the seam price/ceiling/floor classes
   (miso-114/123), take-or-pay / period-budget / minimum-take (miso-127b),
   within-band slope (miso-129), trough marginal-unit VOLUME (miso-115),
   self-commitment forcing removal (miso-102), or the CC committed band
   (miso-132(b), measured-grounded at 1.005); do not re-tune
   `coal_mustrun_online_pmin` (miso-127); do not touch
   `gas_offer_margin_zonal_anchor` (MISO `I`).
7. **The standing continuation for C7-2025 is unchanged**: the coal offer LEVEL
   route via the ex-ante contract-tonnage data ask
   (`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md`), still
   environment-blocked on the Form 580 count and calendar-blocked until
   2026-10-30, with the **Michigan PSCR state lead still UNSPENT** — charter
   option (b), untouched by this session and inherited exactly as the ask left
   it. The miso-89/90 Jun/Jul-2025 under-derate stays instrument-blocked.
