# FINDING — SPP MERIT ORDER: **BOTH ARMS REFUSED AT PHASE 0, ZERO LP SPENT.** SPP's market-heat-rate rotation is not reachable by any offer-curve lever, and the measurement says why.

**Lane:** SPP MERIT-ORDER. **Model:** Opus. **Date:** 2026-09-07.
**Branch:** `claude/spp-merit-order-mhr-rotation-cbx1pu`, fresh off `origin/main` `e042a9f5`.
**Pre-registration:** `PRECOMMIT-spp-merit-order-2026-09-07.md` (same commit; §0 discloses the order of work).
**Control:** the committed keeper `2026-09-07-spp-3-screened-input` / `results/calibration/spp43_screened_B`
(`git_sha 623184f3`), rule 29(b) **form 4**, G-DRIFT clean for all three years (PRECOMMIT §1.2).
**DATA PROFILE: spp.**

**NOTHING ARMS. NO LP WAS SOLVED. No bundle was created, none registered, the keeper is unchanged,
and the shard cells move on measurement, not on a residual.**

---

## 0. Verdict

| | result |
|---|---|
| **The target** | steepening ratio `MHR(>95 pct)/MHR(25–75 pct)`: measured **2.3375 / 2.0993 / 2.1069**, keeper **1.5620 / 1.5163 / 1.6187**. Two legs, opposite signs: the model is **+29.0 / +25.5 / +13.8 %** too dear in the middle **and −13.9 / −9.4 / −12.6 %** too cheap at the top. |
| **ARM A** — `tranche_startup_amortization` + v3 measured runs (MEASURED, zero DOF) | **REFUSED at phase 0.** At its own MAXIMUM markup it moves the ratio **+0.15 / +0.68 / +1.01 %** against a pre-registered **≥ +10 %**, and RAISES the level **+2.3 / +2.3 / +1.9 %** — the wrong direction for C3a. Adding the un-computable CC-peak leg at a generous bound makes rotation **negative** in two years. |
| **ARM B** — a PER-CLASS differentiated `offer_curve_by_group` (the question the price-family lane left open) | **REFUSED at phase 0.** Derived from SPP's own realized prices, it moves the ratio **+4.01 / +2.03 / +3.31 %** against **≥ +10 %**, on an instrument that is measured to **over-state rotation ≈ 4×**. It is the price-family lane's result again: a **level** lever (−13.9 / −13.9 / −14.8 %) with a few percent of rotation attached. |
| **ARM 2 of the handoff** (`pct_peaking`) | **DEAD at zero LP, for a reason that dissolves the question.** Every SPP band multiplier is **1.0**, so a plant's four tranches are **price-identical** and moving capacity between them cannot move a price: a large perturbation (CT 7.0 → 40.0, CC 8.0 → 30.0) moves the LP's supply curve by **3.83 MW** and total pmax by **5.16 of 59,613 MW**. |
| **Why no offer lever works** | **there is no regime to separate.** `CT_PEAKER` is the marginal class in **24–27 %** of SPP's MEDIAN-load hours and 49–60 % of its top hours. A per-class multiplier therefore lifts the middle nearly as much as the top. |
| **And the middle is not a price object** | at mid load the model leaves **3,084 / 3,725 / 2,829 MW** of *available* coal and **3,271 / 2,898 / 3,261 MW** of *available* CC unused while running 1,898 / 2,678 / 2,399 MW of peakers. That is a **dispatch/merit** fact, not an offer-level fact. |
| **The new measured lead, routed** | SPP's `ST_GAS` fleet pays a **+29.3 % / +0.1 % / +7.9 %** delivered-gas premium over the `CT_PEAKER` fleet, and the ST_GAS energy under-run tracks it: **−7.49 / −5.12 / −10.27 TWh**. A rule-14 measured-input question, not this lane's channel. |

**The headline is a refusal reached without spending a single LP minute** — which is rule 29 clause 0
working exactly as written. A three-year SPP screen is ~75 minutes of LP per arm; two arms and their
controls would have been several hours to reach the same answer.

---

## 1. Phase 0 — the target, reproduced on the current keeper

SPP's own hourly RT LMP (`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`) over SPP's own
KS/OK delivered gas (EIA `N3045KS3` / `N3045OK3`, $/Mcf ÷ 1.037), against the keeper's committed
`hourly/system_<year>.parquet` on the identical system-load-percentile axis:

| year | steepening measured | steepening keeper | MHR mid meas / model | MHR hi meas / model |
|---|---|---|---|---|
| 2023 | **2.3375** | 1.5620 | 6.7093 / 8.6485 (**+29.0 %**) | 15.6829 / 13.5089 (**−13.9 %**) |
| 2024 | **2.0993** | 1.5163 | 7.1084 / 8.9198 (**+25.5 %**) | 14.9224 / 13.5250 (**−9.4 %**) |
| 2025 | **2.1069** | 1.6187 | 5.8103 / 6.6102 (**+13.8 %**) | 12.2416 / 10.7001 (**−12.6 %**) |

The handoff's 2.1088 / 1.6214 are the price-family lane's 2025 values on the **previous** keeper
`spp42_crosswalk_B`; reproduced here to 0.17 % on keeper-3, which is the degenerate-vertex noise the
SPP-43 keeper shard already documents.

**The deficit is a genuine rotation.** The model is simultaneously too dear where most hours live and
too cheap where prices form — in all three years, with the same sign pattern.

---

## 2. Phase 0 — SPP's model stack is the IDENTITY, and what that forecloses

The keeper's resolved `offer_curve_by_group` reads `committed = econ_low = econ_high = peak = 1.0`
on `CC_REGULAR`, `CC_CHP`, `CT_PEAKER`, `CT_CHP`, `ST_GAS` (the rule-24 generic gas neutralization,
`backcast_config._neutralize_generic_gas_bands`) and on all five `COAL*` keys (the SPP-40 / SPP-42
rule-25 identity correction, `_SPP_COAL_IDENTITY_BANDS`). A plant's four tranches are therefore
**price-identical**.

### 2.1 `pct_peaking` — the handoff's arm 2 — is INERT on price, by measurement

Two on-recipe `run_year(fleet_only=True)` rebuilds of the keeper's 2023, differing ONLY in
`offer_curve_deltas = {"CT_PEAKER": {"pct_peaking": 40.0}, "CC_REGULAR": {"pct_peaking": 30.0}}`
(from 7.0 / 8.0):

| measure | result |
|---|---|
| max &#124;Δ cumulative available MW at any offer level&#124; (91 sampled hours × 2 zones, ~30 GW available) | **3.83 MW** |
| Δ total fleet pmax | **+5.16 MW of 59,613.04 MW (0.0087 %)**, from tranche-granularity rounding |
| rows | 1,151 → 1,170 (tiny tranches created/destroyed by the split) |

Nothing else in SPP's recipe reads the band: `tranche_startup_amortization` is off, no reliability
floor / bridge / drag limb is registered for SPP's gas classes, `must_run_pct` is committed-only, and
the reserve path does not exist for SPP (§6). **The premise "92.6 % of a CT's capacity sits outside
its peak band" describes a partition the model does not price.** The question is not that
`pct_peaking` is forbidden by rule 1(a); it is that it is *empty* while every band is 1.0.

### 2.2 A consequence for the evidence: the marginal-BAND attribution is degenerate

Because a plant's tranches are price-identical, any "which band is marginal" statistic is decided by
row order (it reads `committed` in 68–88 % of hours at every load level). **This lane uses no
band-level attribution as evidence.** Class-level attribution is not degenerate and is used.

---

## 3. Phase 0 — who is marginal, and the fact that kills the offer-lever family

### 3.1 Two independent identifications, agreeing

**Method A** — per zone-hour, the available thermal row whose `mc_base` is closest to the keeper's own
P1 zonal price. Identification quality: median |mc − price| = **$0.0000**; **99.49 / 99.26 / 99.27 %**
of hours within $0.50. **Method B** — capacity-weighted over EVERY available row within **$0.25** of
the price (p50 4–7 rows, p90 12–14 rows; 395–490 MW of available capacity at the median), so no tie-break is involved.

Method B, capacity-weighted share of the margin (Method A agrees within a few points everywhere):

| | COAL_PRB | CC_REGULAR | **CT_PEAKER** | ST_GAS | COAL_LIGNITE |
|---|---|---|---|---|---|
| **MID 25–75 pct** 2023 | .293 | .256 | **.264** | .092 | .025 |
| 2024 | .255 | .275 | **.270** | .095 | .028 |
| 2025 | .324 | .245 | **.244** | .098 | .044 |
| **HI >95 pct** 2023 | .068 | .006 | **.537** | .384 | — |
| 2024 | .132 | .091 | **.487** | .270 | .006 |
| 2025 | .079 | .061 | **.601** | .241 | .008 |

**A simple-cycle peaker sets SPP's model price in a quarter of its MEDIAN-load hours.** In a real
market that essentially never happens, and it is the merit-order defect this lane was named for.

### 3.2 THE STRUCTURAL RESULT — there is no regime for a per-class multiplier to separate

At mid load the margin is a near-even **three-way** mix (coal ≈ CC ≈ CT, each ~25 %); at the top it
is a **two-way** mix (CT ~50 %, ST_GAS ~25 %). Any multiplier applied to a class moves the price in
proportion to how often that class is marginal — so lifting CT lifts the **middle** almost as much as
the **top**. The measured overlap, not the size of the multiplier, is what bounds the rotation. This
is the transferable finding, and it is why §4's derived per-class curve behaves like a level lever.

### 3.3 And the middle is not an offer-price object at all

Class utilisation of the model's OWN available capacity, mean over the hours in each band
(`fleet_only` availability × pmax vs the keeper's `class_hourly`):

| | COAL_PRB avail / gen / util | CC_REGULAR avail / gen / util | CT_PEAKER avail / gen / util |
|---|---|---|---|
| **MID 25–75** 2023 | 9,436.6 / 6,352.3 / **0.673** | 7,365.9 / 4,094.9 / **0.556** | 9,547.8 / 1,897.8 / 0.199 |
| 2024 | 9,599.7 / 5,874.2 / **0.612** | 6,806.8 / 3,908.4 / **0.574** | 9,518.0 / 2,677.8 / 0.281 |
| 2025 | 11,385.6 / 8,556.3 / **0.751** | 6,610.4 / 3,349.0 / **0.507** | 9,699.7 / 2,398.7 / 0.247 |
| **HI >95** 2023 | 14,845.9 / 13,678.6 / 0.921 | 8,384.0 / 8,102.6 / 0.966 | 9,095.6 / 5,077.3 / 0.558 |

At median load the model leaves **3,084 / 3,725 / 2,829 MW** of available coal and **3,271 / 2,898 /
3,261 MW** of available CC idle while dispatching 1.9–2.7 GW of peakers. The mid-stack is expensive
because of **which units the model chooses**, not because of what they are allowed to offer — and no
band multiplier changes a choice between units it scales identically.

---

## 4. THE TWO ARMS, graded on the pre-registered G-ROT gate

### 4.1 The instrument, and its validation against a real LP

Zero-LP **re-clearing predictor** (PRECOMMIT §4.2): the control clears `Q` MW = available thermal
capacity offering ≤ the keeper's own P1 zonal price; the arm re-prices the same rows and the
predicted price is the offer at which the same `Q` clears. Zones pooled when the keeper's own zonal
prices are equal (77.8 / 80.0 / 79.8 % of hours), separate otherwise. **Strict self-check**: with all
multipliers 1.0 the reconstruction must return the keeper's price exactly; the **25.9–28.6 %** of
hours that satisfy it are retained and every other hour is discarded from every statistic.

**Validation on the price-family lane's SOLVED 2025 arm** (uniform `{0.845, 0.794, 1.018, 1.118}`):

| | LP-MEASURED | THIS PREDICTOR |
|---|---|---|
| arm/control price ratio across the load range | 0.9070 – 0.9151 | 0.9147 – 0.9430 |
| LW mean change | **−9.05 %** | **−8.11 %** retained / **−9.12 %** all hours |
| steepening rise | **+0.52 %** | **+2.09 %** |

The level leg matches to 0.1–0.9 pp. **The rotation leg is over-stated ≈ 4×**, reported against
interest: every predicted rotation below must be divided by roughly four to estimate the LP's answer.
G-ROT is applied to the **raw, optimistic** prediction anyway, so the bias can only make the gate
easier to pass — and neither arm passes it even so.

### 4.2 ARM A — `tranche_startup_amortization` + `tranche_startup_measured_runs`

**Why this arm exists, and why rule 19 selects it over a fitted one.** SPP's `CT_PEAKER`/`CT_CHP`
econ+peak and `CC_*` peak rows carry an above-SRMC margin of **exactly $0.00** — every band is 1.0.
This is the same rule-19 enumeration that **REFUSED** the identical mechanism on ERCOT
(`DIAGNOSIS-ercot145-tranche-startup-2026-07-31.md` §1: ERCOT's rows already carried +$13.1 / +$34.9 /
+$292–451 of *fitted* margin against a $2.9–4.0 measured amortization, i.e. stacking), run in the
opposite direction. ERCOT-145's own words: *"Contrast with the four keeper ISOs: there the tranche
rows sit at or below their physical basis … so the amortization added a genuinely missing
component."* **SPP is that regime.** Verdicts never transfer (rule 25) — the *test* does.

**SPP's own artifact, derived by this lane** (rule 23, committed):
`scripts/data/derive_campd_ct_run_lengths.py --iso SPP` →
`data/raw/_processed-legacy/campd_ct_run_lengths_SPP.csv` — **51 facilities / 138 units / 50,460
measured start-to-stop runs**, 2023–2025 pooled, class-fallback median **9.0 h** (per-plant p25 7.0 /
p50 9.0 / p75 11.0 h). SPP's CTs run **longer** than every other ISO's measured fleet (NYISO 4,
CAISO 4, ERCOT 6, PJM 7, MISO 10 h) — which is SPP's own market, and which is precisely why the
measured markup is small. Zero free parameters: published NREL start costs already on the bins, plus
a measured horizon.

**Footprint, from the arm's own `fleet_only` rebuild** (`mc_base` byte-identical to the control,
max |Δ| = 0): **384 rows / 11,600.3 / 11,630.9 / 11,630.9 MW** gain a start-recovery term.

| class | bands | pmax MW | start $/MW | measured horizon | **MAX markup $/MWh (cap-wt)** |
|---|---|---|---|---|---|
| `CT_PEAKER` | econlo + econhi + peak | 10,519.4 / 10,566.4 | 20 | 9.0 h | **2.140 / 2.141 / 2.141** |
| `CT_CHP` | econlo + econhi + peak | 131.9 / 115.5 | 20 | 9.0 h | 0.854–0.868 / 0.660–0.663 |
| `CC_REGULAR` + `CC_CHP` | peak | 949.0 | 50 | v2 P0 basis (not computable at zero LP) | bounded below |

**G-ROT, on the maximum markup the mechanism can produce** (the measured horizon is a *ceiling* the
P0 run length may only shorten, so this is the arm at its most generous):

| year | control | **arm (MAX)** | rise | required | measured | gap closed |
|---|---|---|---|---|---|---|
| 2023 | 1.5653 | 1.5676 | **+0.147 %** | ≥ +10 % | 2.2890 | 0.32 % |
| 2024 | 1.3306 | 1.3396 | **+0.676 %** | ≥ +10 % | 1.9096 | 1.55 % |
| 2025 | 1.6665 | 1.6833 | **+1.008 %** | ≥ +10 % | 2.4828 | 2.06 % |

**STOP — by 10 to 68×.** And the level moves the wrong way: LW mean **×1.0230 / ×1.0228 / ×1.0188**
against a model already too dear.

**The one leg the instrument cannot compute, bounded rather than ignored.** The 949 MW of CC/CC_CHP
peak rows keep the v2 P0 basis. Granting them the same 9 h horizon ($5.56/MWh), and again a punitive
4 h ($12.50/MWh):

| CC-peak horizon | 2023 | 2024 | 2025 |
|---|---|---|---|
| 9 h | **−0.588 %** | **−0.135 %** | +0.696 % |
| 4 h | **−0.952 %** | **−0.443 %** | +2.016 % |

The un-computable leg makes rotation **negative in two of three years**, because CC peak rows are
marginal in mid-load hours too. The refusal is robust to the limitation, not dependent on it.

**Arm A is refused, and the refusal is honest about what it costs:** a measured, zero-DOF,
forward-native mechanism that is `K` on four ISOs and structurally admissible on SPP is nonetheless
**not the object** — SPP's peakers already run long enough that their start recovery is $2/MWh, and
$2/MWh cannot rotate a stack that needs $8–10/MWh of separation.

### 4.3 ARM B — the PER-CLASS differentiated offer curve

**The derivation rule, declared before its values** (PRECOMMIT §3.2): for each class *c*,
`m_c` = LW mean **measured** RT LMP (capped at $200) over the hours the MODEL's marginal class is
*c*, ÷ LW mean **model** price over the same hours, pooled 2023–2025.

| class | marginal hours (pooled) | measured LW $ | model LW $ | **m_c** |
|---|---|---|---|---|
| `CT_PEAKER` | 7,152 | 27.558 | 31.033 | **0.8880** |
| `COAL_PRB` | 6,987 | 19.286 | 24.607 | **0.7838** |
| `CC_REGULAR` | 6,289 | 21.023 | 26.188 | **0.8028** |
| `ST_GAS` | 3,726 | 28.521 | 31.870 | **0.8949** |
| `ST_CHP` | 850 | 23.020 | 27.833 | **0.8271** |
| `COAL_LIGNITE` | 710 | 20.605 | 25.277 | **0.8152** |
| `CT_CHP` | 327 | 21.276 | 26.534 | **0.8019** |

**SPP's own data says the classes are barely differentiated.** The whole set spans **0.784–0.895** —
a 14 % range on a ~0.84 level shift. The peaker-over-coal separation the arm exists to create is
`0.8880 / 0.7838 = 1.133`, **+13.3 %**, against a rotation deficit of ~30 %.

**G-ROT:**

| year | control | **arm B** | rise | required | measured | gap closed | LW arm/ctl |
|---|---|---|---|---|---|---|---|
| 2023 | 1.5653 | 1.6280 | **+4.006 %** | ≥ +10 % | 2.2890 | 8.66 % | **0.8614** |
| 2024 | 1.3306 | 1.3576 | **+2.029 %** | ≥ +10 % | 1.9096 | 4.66 % | **0.8608** |
| 2025 | 1.6665 | 1.7217 | **+3.312 %** | ≥ +10 % | 2.4828 | 6.76 % | **0.8522** |

**STOP — by 2.5 to 5×, before the instrument's measured 4× optimism is taken off.** Corrected for
that bias the expected LP rotation is **+0.5 to +1 %**, i.e. the price-family lane's measured +0.52 %
for the *uniform* quadruple. **Per-class differentiation adds a few tenths of a percent of rotation
and nothing else.**

**This answers the question the price-family lane explicitly left open.** Its FINDING §6 said: *"a
per-class differentiated curve is a DIFFERENT, still-open question and this finding does not close
it."* It is now closed, by measurement, at zero LP: **the per-class form fails the same gate the
uniform form failed, for the same reason (§3.2), and it fails it as a derived construction rather
than a swept one.** The `offer_curve_by_group` cell stays `R` with its scope widened from "uniform
quadruple" to "any per-class or per-band multiplier set".

---

## 5. Reported at full magnitude — and one NEW measured lead, routed not fitted

### 5.1 The C1 gas split has a fuel-price signature

Model minus actual class energy (TWh; actual = `frontend/data/backcast/bench/SPP/<year>` `classFull`):

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| **wind** | **+11.003** | **+11.673** | **+11.798** |
| `CT_PEAKER` | **+6.775** | **+10.056** | **+11.064** |
| `ST_GAS` | **−7.494** | −5.115 | **−10.274** |
| `CC_REGULAR` | −4.261 | **−8.237** | **−10.188** |
| `COAL_PRB` | −2.593 | −4.797 | +2.593 |
| `COAL_LIGNITE` | −1.458 | −2.803 | −2.829 |

The model's own cap-weighted **delivered fuel price**, recovered from `(mc_base − VOM) / heat_rate`
on the `fleet_only` rebuild:

| class | HR (cap-wt) | fuel $/MMBtu 2023 / 2024 / 2025 | mc $/MWh 2023 / 2024 / 2025 |
|---|---|---|---|
| `COAL_PRB` | 10.824 | 1.519 / 1.434 / 1.408 | 21.05 / 20.10 / 19.83 |
| `CC_REGULAR` | 7.945 | 2.999 / 3.085 / 3.398 | 25.86 / 27.32 / 29.09 |
| `CT_PEAKER` | 11.689 | **3.210 / 2.927 / 3.818** | 41.14 / 38.25 / 49.31 |
| `ST_GAS` | 11.747 | **4.149 / 2.930 / 4.118** | 54.18 / 38.81 / 52.57 |

**SPP's gas-steam fleet is charged a +29.3 % / +0.1 % / +7.9 % premium over the peaker fleet for the
same fuel, and its energy under-run tracks that premium (−7.49 / −5.12 / −10.27 TWh, mildest in the
year the premium vanishes).** Both fleets are priced through `gas_plant_monthly_fuel_pricing=True`
(EIA-923 plant-monthly delivered prices, 383 generators from their own plant and 792 gap-filled
from nearby state/zone plants in 2023). Whether the premium is real SPP conduct or a gap-fill
artifact is a **rule-14 `[R-ACCURATE]` measured-input question**, and it is the first thing a C1 lane
should measure. **This lane does not touch it** — it is neither an offer-curve nor a share question,
and nothing here is tuned around it.

### 5.2 Wind is the largest single class error and is not an offer object

**+11.00 / +11.67 / +11.80 TWh** over actual, essentially constant across years, against a delivered
EIA-930 series grossed up by the SPP-32 measured reference curtailment rate with 0.0 % LP
re-curtailment. Reported, routed, untouched.

---

## 6. What is NOT available, checked rather than assumed

`energy_reserve_coopt` is `False` for SPP and **cannot be armed**: `model/reserves/spec.py::
get_reserve_design` enumerates ERCOT / PJM / MISO / NYISO / NEISO / CAISO and **raises `ValueError`
for SPP**. There is no SPP reserve design, no requirement, no ORDC curve. So the entire
**AS-opportunity-cost layer is structurally absent from SPP's energy stack** — the one candidate this
lane found that could plausibly lift the top of the stack by the ~$8–10/MWh the rotation needs, and
it is a **build** lane (SPP publishes its own RTBM reserve MCP at `data/raw/spp-or-mcp/`,
2023–2025), not a screen. **This is the strongest routed lead for the top-of-stack leg** and it is
recorded, not attempted.

---

## 7. Adjudication, and what the next lane inherits

**Matrix cells set this session** (`docs/codebase-site/data/mechanism-matrix/SPP.js`, SPP's shard only):

- `tranche_startup_amortization` **U → R** — refused at phase 0 on its own maximum arithmetic, no LP.
- `tranche_startup_measured_runs` **U → R** — the same refusal (it is the v3 basis of the same arm);
  SPP's measured artifact is committed for any future lane, exactly as ERCOT-145 committed ERCOT's.
- `offer_curve_by_group` stays **R**, evidence widened: the refusal now covers the **per-class**
  form as well as the uniform quadruple, on a derived construction and at zero LP.
- `tranche_startup_conditional_runs` stays **U** — v4 was never part of the arm and is untested.

**What is now closed:** the price-family lane's open question (per-class differentiation), and the
handoff's arm 2 (`pct_peaking`).

**What the measurement says the object actually is**, in the order the evidence supports:

1. **The middle** (the larger leg, +14 to +29 %) is a **dispatch** object — 3 GW of available coal
   and 3 GW of available CC idle at median load while peakers run. Its most promising measured lead
   is the ST_GAS/CT delivered-gas premium of §5.1. **It is not an offer-level object.**
2. **The top** (−9 to −14 %) is an **AS-opportunity-cost / scarcity** object in a model that has
   neither: no reserve design exists for SPP (§6), and `scarcity_pricing_enabled` /
   `scarcity_price_overlay` are both `False`. SPP-55 owns the >$200 half; the sub-$200 top-quintile
   half is the same missing layer.
3. **Neither is reachable by `offer_curve_by_group`**, in any per-band or per-class form, because
   §3.2's marginal-class overlap bounds what any multiplier can do.

**Rule 29(c):** no screen bundle exists, because no screen ran. Every number this lane will ever cite
is in this document and in the PRECOMMIT.
