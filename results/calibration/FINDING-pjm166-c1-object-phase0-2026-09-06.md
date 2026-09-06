# FINDING — pjm-166: PJM's held-out C1 miss is NOT a merit-order-position object

**Session:** pjm-166 · **Date:** 2026-09-06 · **HEAD:** `ca1bcc70` ·
**Branch:** `claude/pjm-gas-coal-c1-0lm1m8`
**Keeper:** `2026-08-15-pjm-162-inputclock` (bundle `pjm_debugb_inputclock_A`) — **UNCHANGED**
**Touchpoints read:** `2026-09-05-pjm-2022-2021-touchpoints` (bundle `pjm_tp2022_2021_k162`)
**PRECOMMIT:** `PRECOMMIT-pjm166-c1-object-2026-09-06.md` (G-DRIFT audit recorded before any LP)

Everything in §§1–6 is **zero-LP**: committed bench sidecars, the keeper's and the
touchpoint's committed `hourly/` files, the EIA-923 delivered-price parquet, and the EIA-930
hourly extract. No solve produced any of it.

**All C1 figures are on the `classFull` basis** — the gate's own basis, verified by
reproducing the assessment's headline exactly (2021 `CC_REGULAR` +28.7 vs its +28.72). Where
the CAMPD/CEMS census differs materially it is stated; the two bases differ by a stable
+6–7 TWh on `CC_REGULAR` and by ~2× on `ST_GAS` (the three-bases trap pjm-158 recorded).

---

## 0. The answer

> **The dispatch's hypothesis does not survive phase 0.** The held-out miss is **not** a
> coal-vs-CC merit-order-position object, and the premise it rests on is **factually
> inverted**: 2021 and 2022 are the two *most expensive* delivered-gas years and the two
> *cheapest* delivered-coal years of the five, not "the cheapest delivered-gas year".
>
> The miss is an **additive over-generation** — the model builds +19.6 / +26.7 TWh more
> total fossil than measured in the held-out years, against −3.7 / −7.9 in 2023/2024 —
> **not a reordering at constant total**. Model demand matches measured within ±2.2 TWh in
> every year, so demand is not the source.
>
> Exactly **one** model quantity flips sign across the tier boundary: the **DA-virtual
> layer's net cleared position** (+7.40 / +6.48 in-sample vs **−6.14 / −9.91 held-out**).
> That is **pjm-158's own standing warning realized out-of-sample**, on a cell already
> adjudicated `K` and **escalated to the owner** inside the closed price-formation frontier.
> It is re-measured here, **not re-opened as a lever**.

## 1. The gas/coal channel is ruled out — three independent ways

### 1.1 The in-sample elasticity is already right

Coal share of (coal + `CC_REGULAR`) regressed on `ln(delivered gas / delivered coal)`,
36 in-sample months, actual (CAMPD `c_mon`) and model (committed P1 hourly):

| basis | fit | R² | RMSE | mean share |
|---|---|---|---|---|
| **ACTUAL** | `0.2637 + 0.0772·ln(g/c)` | 0.336 | 0.0313 | 0.2686 |
| **MODEL** | `0.2631 + 0.0686·ln(g/c)` | 0.253 | 0.0339 | 0.2674 |

**Slope ratio 0.888; intercept gap −0.0007.** The model's responsiveness to relative fuel
price is ~89 % of measured and its level is identical to four decimals. (pjm-157 measured
0.0781 / 0.0814, ratio 0.959, on a different span construction; both agree the model is not
gas-inelastic in sample.) A slope deficit of 0.0086 applied over the ~0.75 ln-unit
extrapolation to the held-out years buys **0.7 pp of coal share** — a fifth of 2021's gap and
under half of 2022's. **The elasticity cannot carry the miss.**

### 1.2 The premise is inverted — these are the CHEAP-COAL years, not the cheap-gas years

Volume-weighted EIA-923 delivered receipts, PJM plants, annual mean $/MMBtu:

| year | gas | coal | ln(g/c) | **gas rank** | **coal rank** |
|---|---|---|---|---|---|
| **2021** | **4.12** | **2.07** | 0.686 | **4 of 5** | **1 (cheapest)** |
| **2022** | **7.12** | **2.62** | 1.000 | **5 (dearest)** | **2** |
| 2023 | 3.26 | 3.08 | 0.058 | 2 | 5 |
| 2024 | 2.85 | 3.04 | −0.063 | 1 (cheapest) | 4 |
| 2025 | 3.94 | 2.94 | 0.292 | 3 | 3 |

The held-out years sit outside in-sample support (`ln(g/c)` 0.69–1.00 against an in-sample
−0.30…+0.88) because **delivered coal was ~30 % cheaper**, not because gas was cheap.

**This is the sign test, and the miss fails it.** `CC_REGULAR` over-runs by **+28.7 / +22.3
TWh in the two dearest-gas years**, and by only **−3.4 / +0.5 TWh in the two cheapest-gas
years**. An offer-position error that made gas too cheap would over-dispatch gas *most* where
gas is *cheapest*. The observed pattern is the opposite, so a gas offer-position error is the
wrong shape for this residual.

### 1.3 Coal is not saturated — it has headroom and does not take it

Model coal (all three classes) monthly mean as a fraction of its **own annual peak hour**:

| yr | J | F | M | A | M | J | J | A | S | O | N | D | peak MW |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2021** | .63 | .64 | .42 | .33 | .37 | .57 | .66 | **.68** | .40 | **.25** | .30 | .41 | 36,955 |
| 2022 | .87 | .71 | .39 | .37 | .37 | .53 | .66 | .65 | .42 | .26 | .35 | .70 | 33,790 |
| 2023 | .47 | .40 | .41 | .35 | .30 | .38 | .60 | .54 | .42 | .28 | .35 | .42 | 31,277 |

2021's high-`ln(g/c)` autumn months run at **0.25–0.40 of the model's own coal peak**. The
coal fleet is nowhere near a ceiling, and its 2021 peak capability (36.9 GW) is correctly
*larger* than 2023's (31.3 GW), so fleet vintage is not the constraint either. The
`COAL_BIT` −9.45 TWh is **not** a capacity or availability limit.

## 2. What the miss actually is: an additive fossil surplus

Annual TWh, `classFull` basis:

| aggregate | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **ALL FOSSIL Δ (model − actual)** | **+19.6** | **+26.7** | −3.7 | −7.9 | +13.5 |
| `CC_REGULAR` Δ | **+28.7** | **+22.3** | −3.4 | +0.5 | +3.9 |
| COAL (all) Δ | **−12.9** | +2.0 | +0.1 | −1.0 | +5.9 |
| `ST_GAS` Δ | **+8.1** | **+7.7** | +1.9 | −2.2 | +2.3 |
| `CT_PEAKER` Δ | −4.9 | −3.3 | −2.3 | −3.4 | +3.6 |
| hydro Δ | −6.2 | −7.0 | −6.6 | −7.0 | −7.0 |
| nuclear / wind / solar Δ | ≈0 | ≈0 | ≈0 | ≈0 | ≈0 |

And the demand side, against EIA-930 (int32 sentinel hours guarded):

| year | measured demand | model demand | **Δ** |
|---|---|---|---|
| 2021 | 796.0 | 796.2 | **+0.2** |
| 2022 | 808.0 | 810.2 | **+2.2** |
| 2023 | 782.9 | 784.8 | +1.9 |
| 2024 | 813.2 | 812.7 | −0.5 |
| 2025 | 843.1 | 843.2 | +0.1 |

**Two corrections to the standing narrative, both from the assessment's own criterion table:**

1. **"Gas-over / coal-under in the SAME direction on BOTH held-out years" is half right.**
   Gas-over holds in both. **Coal-under is 2021 only** — 2022 coal is **+2.0 TWh, slightly
   over**. The assessment's §3 table already says this (it lists `COAL_BIT` as a 2021 failure
   and not a 2022 one); the §3.1/§5 prose generalised past it.
2. **It is not a swap.** A merit-order reordering moves classes in opposite directions at
   roughly constant total. Here the fossil total itself moves +19.6 / +26.7 TWh while demand
   is right to ±2.2 TWh. Something is adding load or removing supply, not re-ranking it.

The constant deficits — hydro −6 to −7 TWh and oil −1 to −2 TWh in **every** year, in-sample
and out — are real but **tier-neutral**: they cannot explain a boundary they do not cross.

## 3. The one quantity that does cross the boundary — and it is already owner-escalated

The committed class-hourly sidecar carries three **non-physical** rows beside the generation
classes: `import` (negative = net export) and the cleared DA-virtual layer. Net cleared
virtual position, TWh:

| year | `VIRTUAL_INC` | `VIRTUAL_DEC` | **NET** | reading |
|---|---|---|---|---|
| **2021** | +6.89 | −13.02 | **−6.14** | net phantom **DEMAND** |
| **2022** | +10.32 | −20.24 | **−9.91** | net phantom **DEMAND** |
| 2023 | +19.05 | −11.65 | **+7.40** | net phantom **SUPPLY** |
| 2024 | +20.97 | −14.50 | **+6.48** | net phantom **SUPPLY** |
| 2025 | +17.67 | −18.57 | −0.89 | ≈ neutral |

The mechanism's own docstring states its rule-13 admissibility anchor: *"the annual net of
the whole curve cleared at actual DA prices is ≈ 0 (−0.6/−0.9/+1.3 TWh 2023/24/25)"*. The
model clears **+7.40 / +6.48 / −0.89** against that reference — and in the held-out years it
clears **6 to 10 TWh of net virtual DEMAND**, which physical generation must serve. Because
the virtual pseudo-units carry no bench class, the energy they force onto the physical fleet
lands in whichever physical class is marginal — `CC_REGULAR` — and C1 scores it there, as that
class's own error.

**This is not new physics; it is pjm-158's standing warning coming true out of sample.** That
session measured the same defect in sample and recorded, in the matrix cell verbatim:

> *"the basis (+5.8/+4.6/+6.6) and the model's price error (−12.5/−9.6/−5.9) currently OPPOSE
> each other by coincidence, so improving C3b toward RT GROWS this layer's phantom energy
> toward +5 to +7 TWh of phantom DEMAND — toward the condemned pjm-102 clamp, not away from
> it."*

**What pjm-166 adds:** pjm-158 measured 2023–2025 only. The held-out years show the layer on
the **other side of its crossing price**, in the pjm-102 direction, and they are exactly the
two years C1 fails. The sign of the net virtual position agrees with the sign of the fossil
surplus in **5 of 5 years**.

**How much does it explain?** At pjm-158's own measured channel gain — disarming the layer
moved `CC_REGULAR` by +5.220 / +6.848 / +2.689 TWh against net positions of +7.40 / +6.48 /
−0.89, i.e. ≈ 0.7–1.0 TWh of CC per TWh of net virtual — a −6.14 / −9.91 position accounts
for roughly **+6 and +10 TWh**, or **≈ 21 % of 2021's and ≈ 44 % of 2022's** `CC_REGULAR`
miss. The naive cross-year slope is ~2.4 TWh of CC per TWh of virtual, but with n = 5 and
every tier-boundary effect confounded into it, **the mechanism's own measured gain is the
defensible number.** The rest of the miss is not explained by anything measured here, and
this finding does not claim otherwise.

**Robustness — the two columns are the same recipe, verified not assumed.** Diffing
`run_config.json` between the keeper and the touchpoint bundle: **924 shared keys, 12 value
differences**, of which 5 are run metadata (platform, branch, `git.sha`, `basis_sha`) and
**3 are `ScenarioConfig` fields** — `ccs_retrofit_capex_kw` (900.0 vs 1521.4),
`fixed_om_gas_cc_ccs` (25.0 vs 65.0) and `gas_price_override` (2.54 vs 6.45). The first two
are **CCS-retrofit parameters, inert by construction in a `mode="backcast"` run** (the
retrofit screen is gated at `ccs_retrofit_available_year` = 2028, past every backcast year);
the third is a per-year anchor superseded by the measured monthly F923 series each bundle
carries in `calibration_flags.gas_prices.<year>`. Decisively for §3,
**`pjm_da_virtual_bids: True` in BOTH**, with `pjm_da_virtual_surface_path: None` in both — so
the cross-year comparison above is of the same armed mechanism, not of two configurations.

**Governance — this is a re-measurement, not a lever.** Matrix cell `da_virtual_bids` is
**`K`** and stays `K`. pjm-158 adjudicated it: the defect is rule 14 `[R-ACCURATE]`-shaped (a
real measured input misaligned to our representation), its root cause is *"the LP carries ONE
price series, gated as RT, while the curve needs a DA price"*, and that is an **architecture
question inside PJM's owner-declared-closed price-formation frontier (pjm-142), already
escalated to the owner.** Nothing here re-opens it. What is new is evidence for the owner:
the escalated defect is **larger and opposite-signed out of sample**, and it sits on the
criterion that fails there.

## 4. Two candidate objects tested and NOT confirmed

Reported because a negative result is the point of a phase 0, and both would otherwise be
re-tried by the next session.

**(a) `ST_GAS` is not floor-forced — it clears economically.** `ST_GAS` is the second-largest
named 2021 C1 failure (+8.07 TWh / +1.0 pp). Band composition of its 11.87 TWh in 2021:
`econlo` 4.57 + `econhi` 4.47 = **9.04 TWh (76 %) economic**, `committed` 2.79, `peak` 0.03,
`mustrun` **0.00**. Rule 17 `[R-FLOOR-WINDOW]` does not fire — there is no floor binding
outside its window here, because there is essentially no floor.

**(b) The `ST_GAS` ↔ `CT_PEAKER` substitution hypothesis FAILS its own test.** The annual
deltas look like a trade (2021 `ST_GAS` +8.1 against `CT_PEAKER` −4.9; 2022 +7.7 against
−3.3), but monthly correlation of the two deltas does not support it:

| year | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| r(Δ`ST_GAS`, Δ`CT_PEAKER`) | +0.077 | −0.165 | +0.497 | +0.178 | +0.076 |

A month-by-month substitution requires a strong negative correlation. Four of five years are
**positive**. The annual near-offset is coincidence, and **the hypothesis is rejected.**

What does survive as an open observation, not a diagnosis: the model's `ST_GAS` runs at a
near-constant capacity factor of its own peak (0.156 / 0.184 / 0.157 / 0.156 / 0.242) while
the measured class swings 3.8 → 14.8 TWh across the same five years. The model's `ST_GAS`
has little year-to-year responsiveness. That is filed, not pursued — pursuing it from a
held-out year is precisely the fitting rule 22 step 3 forbids.

## 5. What this does NOT establish

Stated against interest, so the next session does not over-read it:

- **The virtual-layer channel is a bound, not an attribution.** It rests on pjm-158's
  measured gain transported across the tier boundary; no A/B was solved here, and none should
  be until the owner rules on the escalated architecture question.
- **~55–79 % of the `CC_REGULAR` miss is unexplained** by anything measured in this session.
- **n = 5 years.** The sign agreement is 5/5, which is suggestive and is not a fitted
  coefficient. No regression on five annual points is quoted as identification.
- **Nothing here is an out-of-sample skill number.** Validation tier is iterable model-
  selection evidence by construction (rule 22).
- **The HEAD-drift confound is open at the time of writing** — the control solve in
  `PRECOMMIT` §3 is the instrument, and §6 below carries its result.

## 6. The same-HEAD in-sample control

*(Result section — filled from `results/calibration/pjm_headctrl_k162` after the solve;
pre-registered thresholds are fixed in `PRECOMMIT` §3 and were written before it ran.)*

**G-DRIFT was attempted first and is structurally undischargeable**: the keeper's recorded
`git_sha` `457ae04` (2026-08-15) does not exist at HEAD and is not in
`docs/governance/citation-commit-map.txt` — it predates the **2026-08-16 history rewrite** by
one day. The clone was deepened to 11,640 commits and the object still does not resolve.
There is **no diff to classify**, which is stronger than NEISO's "too large to classify"; an
unclassifiable diff is treated as LIVE, and a LIVE hunk is what earns a control solve under
rule 29(b). NEISO's INERT verdict does not transfer (rule 25 `[R-ISO-SCOPE]`).

## 7. Recommendation

1. **Do not pull the DA-virtual layer as a lever.** It is `K`, adjudicated, and its root
   cause is owner-escalated inside a closed frontier. §3 is evidence *for* that escalation.
2. **Route §3 to the owner as new evidence on the existing pjm-158 escalation** — the
   phantom-energy defect is opposite-signed and ~2× larger out of sample, and it lands on the
   failing criterion. The question is unchanged; only its measured magnitude is.
3. **Do not tune anything to 2021/2022.** Rule 22 step 3 sends a touchpoint miss back to
   2023–2025 as an object; the object here is a mechanism already under owner review.
4. **Retire the coal↔CC merit-order framing** from the PJM lever queue (§1). Retain the
   `ST_GAS` flat-responsiveness observation (§4) as an in-sample question for 2023–2025.
5. The hydro −6 to −7 TWh and oil −1 to −2 TWh constant deficits are tier-neutral and
   pre-existing, but they are real and unexplained in **every** year, in-sample included.
   They are a separate, in-sample-diagnosable lane and are not this object.
