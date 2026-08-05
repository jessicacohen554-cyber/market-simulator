# FINDING (pjm-157): the CC gas-elasticity object **does not survive Phase 0**. PJM's coal↔CC switching is measured CORRECT (in-sample slope ratio **0.959**); **80 % of the 2022 CC surplus is a thermal-LEVEL error**, and the level is set by two non-generation terms — the DA virtual layer and net interchange

**Session:** pjm-157 (the pjm-156 2022-touchpoint hand-back)
**Date:** 2026-08-05
**Verdict:** the chartered object **RE-POINTS**. The handoff's decisive claim — "the
model's CC fleet is gas-price-INELASTIC" — is **refuted on the model's own
in-sample data**. Phase-0 step 1 does not clear the CC object; it dissolves most
of it.
**Deliverable:** a **documented refusal to arm a mechanism this session, with
cause** (§6), plus two re-pointed objects and one bench question (§5).
**LP solves this session: ZERO.** Every number below is read from committed
artifacts — the `pjm2022_touchpoint` and `pjm152_collapse_A` hourly sidecars, the
two run payloads, the per-year `bench/PJM/*.json.gz`, `data/raw/eia-930/`, and
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`.
**Holdout freeze (rule 22):** respected absolutely. 2022 was **not** solved,
scored or re-registered; nothing was tuned on, against, or in response to the
2022 residual. Every identification below is measured **in-sample on 2023–2025**.

---

## §0 — the verdict in one table

| Phase-0 step | question | result | object survives? |
|---|---|---|---|
| **0.1** energy balance | which term absorbs the fossil surplus? | on a self-closing EIA-930 basis the model's **total** 2022 generation error is **+3.9 TWh (+0.5 %)**, not +30. The terms that move are **net interchange (−18.3 TWh of missing exports)** and the **DA virtual layer (+11.1 TWh of phantom demand)** | **NO — re-points** |
| **0.2** elasticity | is the model's coal↔CC switching under-elastic? | **NO.** In-sample slope model **0.0781** vs actual **0.0814** → ratio **0.959** over 36 months spanning gas/coal ratios 1.00–2.51. In 2022 the model is *over*-elastic (ratio **1.414**) | **NO** |
| **0.3** fuel inputs | did 2022 gas resolve to 2022 prices? | **YES.** PJM-footprint delivered gas **$7.14/MMBtu** (2022) vs $3.81 (2023); Dec **$9.76**, Aug **$8.97**; gas/coal ratio **1.35 → 2.80**. 972 plant-month reporters vs 977/959/941 | n/a — clean |
| **0.4** pooled vintage | hidden 2022 asymmetry in the pooled artifacts? | bounded at **≲3 TWh and WRONG-SIGNED** for the CC object | n/a — cannot be the cause |

**The one number that replaces the handoff's one number.** The 2022 `CC_REGULAR`
error decomposes into the *level* of total (coal + CC) thermal energy and the
coal↔CC *switching share*:

| yr | T_model | T_actual | ΔT | coal share model | coal share actual | Δ pp | **CC err** | **from LEVEL** | **from SHARE** | level % |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **2022** | 468.1 | 437.5 | **+30.64** | 32.62 | 33.71 | −1.09 | **+25.40** | **+20.31** | +5.09 | **80 %** |
| 2023 | 434.8 | 432.4 | +2.45 | 25.89 | 26.23 | −0.34 | +3.28 | +1.81 | +1.47 | 55 % |
| 2024 | 449.6 | 444.5 | +5.11 | 25.39 | 25.95 | −0.56 | +6.32 | +3.78 | +2.54 | 60 % |
| 2025 | 477.1 | 458.4 | **+18.67** | 29.92 | 29.41 | +0.51 | +10.73 | **+13.18** | −2.45 | 123 % |

Read the last row first: **the same level defect is already present IN-SAMPLE in
2025 at 65 % of 2022's magnitude (+13.18 of a +10.73 CC error), in a year that
PASSED C1.** That is the identifiable-without-2022 outcome the handoff asked for
— and it is not an elasticity defect.

**What of the elasticity object survives:** the 2022 coal share is **1.09 pp** below
actual, worth **+5.09 TWh** of the +25.40 CC error (**20 %**), against an in-sample
share error of −0.34/−0.56/+0.51 pp. Real, but a fifth of the claimed size, and
*not* a slope deficiency (§2).

---

## §1 — Phase 0.1: the energy-balance reconciliation

`scripts/probes/_pjm157_energy_balance.py`. Model terms are the P1 sidecars;
measured is EIA-930 `PJM_region` (`D`, `NG`, `TI`). Units TWh.

| term | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| model physical generation (excl. virtuals & import) | 838.74 | 807.99 | 830.70 | 872.00 |
| + storage discharge | 4.85 | 4.87 | 5.81 | 5.46 |
| **= model NG-equivalent** | **843.59** | **812.86** | **836.52** | **877.46** |
| model zonal demand (LP RHS) | 810.19 | 784.82 | 812.74 | 843.19 |
| + storage charge | 6.06 | 6.08 | 7.26 | 6.82 |
| **= model D-equivalent** | **816.25** | **790.90** | **820.00** | **850.01** |
| model net export (`import` class) | 13.42 | 27.50 | 20.42 | 23.18 |
| model net virtual withdrawal (DEC−INC) | **+11.12** | −7.45 | −6.55 | +0.91 |
| measured `D` | 808.03 | 782.93 | 813.22 | 843.08 |
| measured `NG` | 839.65 | 822.80 | 845.77 | 875.74 |
| measured `TI` (+ = net export) | 31.67 | 39.86 | 32.58 | 17.98 ⚠ |
| **Δ NG-equivalent** | **+3.94** | −9.94 | −9.25 | +1.72 |
| **Δ D-equivalent** | +8.22 | +7.97 | +6.78 | +6.93 |
| **Δ net export** | **−18.25** | −12.36 | −12.16 | +5.20 ⚠ |
| **Δ virtual** | **+11.12** | −7.45 | −6.55 | +0.91 |
| balance residual | +2.85 | +1.91 | +2.65 | +3.37 |

⚠ **2025's 930 `TI` is not usable**: `NG − TI − D = +14.68` (the other three years
close to ≤0.04). pjm-135 measured 2025 net export as **32.93 TWh** from PJM's own
published tie-line file; on that basis 2025's Δ net export is **−9.75**, not +5.20.
The bench's own `interchange` row carries the broken 930 figure (§5, question C).

The identity closes exactly in each year:
`Δ NG-equiv = Δ D-equiv + Δ virtual − Δ export_gap + residual`
(2022: 8.22 + 11.12 − 18.25 + 2.85 = **+3.94** ✓).

### What each candidate term does

- **Demand — CLEARED.** Model zonal demand rises **+25.37 TWh** from 2023 to 2022
  against a measured **+25.10**: a **0.27 TWh** delta error on a 25 TWh move. The
  `D-equivalent` offset (+8.22/+7.97/+6.78/+6.93) is a **constant** structural
  term across all four years — the model's demand series is 930 `D`, which already
  contains PJM's pumped-storage pumping load, while the model *also* charges its
  own PS storage. Worth flagging (it is ~7 TWh/yr of double-counted pumping in
  **every** year, in-sample included) but it carries **no 2022 asymmetry** and
  therefore explains none of the holdout regression.
- **Nonfossil — CLEARED.** `nuclear` −0.1/−0.7/−0.6/−0.6 %; `wind` and `solar`
  0.0 % in every year (pinned). Model `hydro` is 8.97/8.90/8.86/8.46 TWh — stable,
  and on the **corrected** EIA-923 `HY` basis that pjm-143 landed. **Do not read
  the bench's `classFull.hydro` (16.0 TWh) as a model shortfall**: that cell is
  930 `NG: WAT`, which for PJM is conventional hydro *plus* pumped-storage gross
  discharge (PJM files no `NG: PS` column) — exactly the contamination pjm-143
  removed. The model's PS lives in the storage layer (4.85 TWh discharge).
- **BTM — CLEARED.** The CHP classes carrying BTM are small and stable
  (`CC_CHP` 7.18/8.57/8.04/6.78, `CT_CHP` 1.14/1.29/1.53/1.23); the bench's
  per-plant `btm` field is zero for every PJM plant in all four years.
- **Net interchange — DOES NOT CLEAR.** The model under-exports by **18.25 TWh**
  in 2022 against **12.36 / 12.16 / 9.75** in-sample. This is **already a chartered
  PJM defect**: pjm-135 §0 M4 — *"the `import` class **is** the LP's net
  interchange … the star node supplies PJM with 7.1–11.1 TWh/yr the real seam did
  not — and **nothing in the model constrains it**"*, hourly R² negative every
  year. 2022 widens a known in-sample defect by ~6 TWh. Note the **sign**:
  under-exporting *reduces* the model's generation requirement, so this term is a
  partial **offset** to the CC surplus, not its cause.
- **DA virtual layer — DOES NOT CLEAR, and is the term that flips.** See §1.1.

### §1.1 — the DA virtual layer's net clearing swings 18.57 TWh and breaks its own invariant

`ScenarioConfig.pjm_da_virtual_bids` renders the measured hourly submitted
INC/DEC curves as LP pseudo-units. They are **not physical** — no bench class
matches them, C1's `_gen_totals` ignores them by construction — but they **are**
columns on the energy balance, so their net clearing is real MWh the physical
fleet must serve or displace.

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `VIRTUAL_INC` cleared (supply) | +9.54 | +19.01 | +20.86 | +17.66 |
| `VIRTUAL_DEC` cleared (withdrawal) | −20.66 | −11.56 | −14.31 | −18.57 |
| **net cleared** | **−11.12** | **+7.45** | **+6.55** | **−0.91** |
| gross turnover | 30.21 | 30.57 | 35.18 | 36.23 |
| **pjm-105 reference: net cleared at ACTUAL DA prices** | *(not measurable here)* | **−0.68** | **−0.95** | **+1.32** |
| **model deviation from reference** | — | **+8.13** | **+7.50** | **−2.23** |

The reference row is the mechanism's **own rule-13 admissibility argument**
(`virtual_bids.py` module docstring, citing pjm-105 /
`docs/FINDING-pjm-midmerit-level-2026-07.md` §7): *"the annual net of the whole
curve cleared at actual DA prices is ≈ 0 … vs the one-sided clamp's
+10.3/+14.8/+17.2 TWh of phantom demand"*. That near-zero is precisely what
distinguishes the symmetric net form from the **condemned** pjm-101 gross-INC and
pjm-102 clamped constructions.

**The model does not clear it at ≈ 0.** It clears **+8.13 / +7.50 / −2.23 TWh**
away from the reference **in the tuned years** — i.e. two of the three in-sample
years already carry a phantom-energy deviation of the same order as the clamped
form the project rejected. Gross turnover is flat (30–36 TWh) across all four
years, so this is **not** a curve-mass change; it is the **clearing point** moving.

**Why it moves: the layer is a price-error → quantity-error amplifier.** Decoding
the run payloads' `lmpDeltaHr` (model − actual hourly $/MWh) and conditioning the
net clearing on its sign:

| yr | hours model UNDER actual | net virtual in those hours | hours model OVER | net virtual in those hours | MAE dLMP $/MWh | corr(dLMP, net) |
|---|---:|---:|---:|---:|---:|---:|
| **2022** | 2,654 | **−9.12** | 5,922 | −1.77 | **20.61** | +0.124 |
| 2023 | 2,140 | −2.94 | 6,336 | +10.42 | 9.20 | +0.298 |
| 2024 | 2,608 | −4.64 | 5,921 | +11.21 | 10.50 | +0.301 |
| 2025 | 2,866 | −7.80 | 5,667 | +7.14 | 13.97 | +0.206 |

The sign relation is consistent in **all four years**: hours where the model's
price sits below actual clear net virtual **demand**; hours above clear net
**supply**. 2022's hourly price MAE is **$20.61 — 2.2× the in-sample 9.20/10.50**
— which is the same C3b price-shape failure the touchpoint reported, and the
layer converts it into **11.12 TWh of phantom load** that the CC fleet serves.

**This makes C1 (a quantity gate) conditional on C3b (a price gate), with a gain
that scales with the price level.** In-sample, where C3b passes comfortably at a
$29–44 price level, the coupling is invisible. At 2022's $67 level with a failing
C3b, it dominates.

---

## §2 — Phase 0.2: the elasticity measurement (in-sample, unrestricted) — the decisive refutation

The handoff asserts 2022 is "the only year with a large enough fuel excursion to
expose" the defect. **That is false at monthly resolution.** PJM-footprint
delivered gas reaches **$6.63 (Jan-2023)**, **$5.88 (Jan-2024)** and **$6.69
(Jan-2025)** — 2022-magnitude gas months, fully **in-sample**. The in-sample
gas/coal ratio spans **1.00 → 2.51**; 2022 spans 2.20 → 3.40. The overlap is
large enough to identify the switching response without touching 2022.

Actual monthly class energy is reconstructed from the committed bench's per-plant
`campd` blobs. **Fidelity check on `CC_REGULAR`: −0.02 / −0.00 / +0.00 / −0.00 %
against the committed `c_ann`** — exact.

Regressing the coal share of (coal + `CC_REGULAR`) on `ln(delivered gas / delivered coal)`:

| sample | model slope | actual slope | **model/actual** | model r | actual r |
|---|---:|---:|---:|---:|---:|
| **IN-SAMPLE 2023–25 (n=36)** | 0.0781 | 0.0814 | **0.959** | 0.488 | 0.516 |
| HOLDOUT 2022 (n=12) | 0.2519 | 0.1782 | **1.414** | 0.538 | 0.516 |
| all 48 months | 0.0833 | 0.0824 | 1.010 | 0.586 | 0.643 |

Annual coal-share error (model − actual), percentage points:

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| mean | **−0.04** | +0.13 | −0.42 | +0.41 |
| MAE | 2.03 | 1.33 | 1.34 | 1.33 |

**Conclusions.**
1. The model's fuel-switching elasticity is right **to 4 %** in-sample, over 36
   months and a 2.5× ratio range.
2. In 2022 the model is **over**-elastic (1.414), not under-elastic. It switches
   *harder* than the market did.
3. The model's monthly coal-share error in 2022 has a **mean of −0.04 pp**, the
   smallest of the four years.
4. The **annual** share error (−1.09 pp, §0) is a small level-of-share offset, not
   a slope deficiency, and is worth **5.09 of the 25.40 TWh** CC error.

**The handoff's direction-of-change evidence, re-read.** From 2023 to 2022 the
model moved **+33.03 TWh** into `COAL_BIT` against a measured **+33.08** — a
**0.15 % error on a 33 TWh fuel-switching swing**. That *is* the gas-price
elasticity the handoff says is missing, and the model has it. The handoff's
"model cut CC only ~7 TWh vs the market's ~29" is arithmetically correct but is
a statement about the **level** of thermal energy, not about switching: the
market's CC fell because PJM's *total* thermal call fell, and the model's did not
— because of §1.

---

## §3 — Phase 0.3: the 2022 fuel input resolves correctly (no silent fallback)

PJM-footprint (OH PA NJ MD DE VA WV IL IN KY MI NC DC) EIA-923 quantity-weighted
delivered price, $/MMBtu:

| month | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| Jan | 6.37 | 6.63 | 5.88 | 6.69 |
| Aug | **8.97** | 3.04 | 2.73 | 3.53 |
| Dec | **9.76** | 4.09 | 4.39 | 5.52 |
| **annual gas** | **7.14** | 3.81 | 3.37 | 4.37 |
| **annual coal** | 2.55 | 2.83 | 2.76 | 2.63 |
| **gas/coal ratio** | **2.80** | 1.35 | 1.22 | 1.66 |
| reporters (plant-months) | 972 | 977 | 959 | 941 |

The 2022 series is present, monthly, at full reporter density, and carries the
whole shock including the December spike. `run_config.json` confirms the recipe is
byte-identical to the keeper apart from the year: `gas_monthly_actuals=True`,
`gas_plant_monthly_fuel_pricing=True`, `pjm_zonal_gas_basis=True`,
`hindcast_fuel_variant=realized`, `gas_prices={'2022': 6.45}` (Henry Hub 2022
annual). **No pooled or stale vintage fallback.** A fuel-input bug is excluded.

---

## §4 — Phase 0.4: bounding the pooled-vintage asymmetry

Both flagged artifacts are **physical machine constants**, not year-varying market
quantities, which is why pooling is defensible in the first place:

- **`measured_ct_heat_rates`** — `campd_ct_heat_rates_PJM.csv`, `years =
  "2023-2024-2025"`, 71 PJM CT plants, all `flag == "ok"`. Loaded MMBtu per net
  MWh; median `model_over_measured` **0.991** (the artifact is near-neutral in
  aggregate; mean 0.992, IQR 0.957–1.019).
- **`measured_ramp_capability`** — EIA-860 Schedule 3.1 `"10M"` fast-start
  nameplate (a reported machine category) floored under a CAMPD hourly ramp
  envelope. The clean partition is gitignored and absent from this container, so
  it is bounded empirically rather than re-derived.

**Empirical bound.** The only class the CT heat-rate artifact prices is
`CT_PEAKER`:

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| `CT_PEAKER` model − actual, TWh | **−3.20** | −0.49 | −0.75 | +2.98 |

2022's error sits ~2.5 TWh outside the in-sample range, so the pooled vintage
could plausibly own **≲3 TWh**. But the **sign is wrong for the CC object**: the
model runs `CT_PEAKER` too **low**, so correcting it would displace `CC_REGULAR`
**downward**. The pooled artifacts cannot cause a CC surplus; at most they offset
~3 TWh of it. **Reported as instructed, and the bound is small and adverse.**

*(Adjacent, not from these artifacts: `ST_GAS` is +4.38 in 2022 vs
+1.47/−2.82/+0.64 in-sample — old steam gas running harder in the highest-gas
year, the opposite of the physical expectation. ~4 TWh, logged for §5.)*

---

## §5 — where the lane re-points

**Object A — the DA virtual layer clears away from its own admissibility
invariant, IN-SAMPLE.** Deviation from the pjm-105 actual-DA-price reference is
**+8.13 / +7.50 / −2.23 TWh** in 2023/24/25. The mechanism's rule-13 case rests on
that annual net being ≈ 0; it is not. **Identifiable and testable entirely on
2023–2025.** Note carefully what the fix is **not**: the layer clearing
endogenously against the model's own dual is the *correct*, admissible design —
pinning its cleared volume to a measured outcome would be a straight rule-13
violation and would recreate the condemned pjm-102 clamp. The deviation is a
**symptom of the hourly price error**, so the root object is the price shape, and
the virtual layer is the channel that converts a C3b error into a C1 error. The
honest open question is whether a layer with that gain belongs in a keeper at all
while C3b is unconverged.

**Object B — net interchange, already chartered at pjm-135.** Model under-exports
by 12.36 / 12.16 / 9.75 TWh in-sample and 18.25 in 2022; hourly R² negative every
year; *"nothing in the model constrains it"*. This is the single largest term in
the 2022 balance. It is **not a new object** and this session opens nothing on it.

**Question C — the bench's 2022 coal basis must be resolved before anyone reads
the 2022 C1/C2 coal rows.** EIA-930 `COL` minus the bench's CAMPD grid-delivered
coal, on an **identical 42-plant / 38,003 MW census in 2022 and 2023**:

| | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| 930 `COL` | 166.95 | 120.68 | 122.40 | 145.83 |
| bench CAMPD coal (`c_ann`) | 147.46 | 113.41 | 115.35 | 134.81 |
| **gap** | **+19.49** | +7.26 | +7.05 | +11.02 |
| gap / 930 `COL` | **11.7 %** | 6.0 % | 5.8 % | 7.6 % |

The in-sample gap scales at 6–8 % of coal output; at 2022's output that predicts
10–13 TWh, against an observed **19.5**. The 2022 gap is **~7–9 TWh wider than the
in-sample relationship**, on the *same plants*. This is why the two bases disagree
about the sign of the model's coal error in 2022 (**+5.1 TWh** against the bench's
42 plants; **−14.2 TWh** against 930 `COL`), and it is a **bench/coverage**
question, not a dispatch question. The 2022 CAMPD facility extract is not in this
container (`data/raw/campd-facility-level/` holds 2023–2025 only), so it could not
be closed here.

**Also logged, unopened:** the ~7 TWh/yr double-counted pumped-storage pumping
load (§1), present in every year including in-sample; and `ST_GAS` +4.38 (§4).

---

## §6 — refusal to arm a mechanism this session, with cause

**No mechanism is armed, no A/B is pre-registered, no `ScenarioConfig` field is
added, and no matrix cell changes state.** Cause:

1. **The chartered object dissolved.** The session was chartered to fix CC
   gas-price inelasticity. That defect is measured **absent** in-sample (slope
   ratio 0.959) and **inverted** in 2022 (1.414). Arming a CC mechanism now would
   be building against a refuted diagnosis — and any CC adder or elasticity knob
   sized to the 2022 residual is barred outright by rules 1 / 13 / 26, as the
   handoff itself states.
2. **The surviving objects are not mine to arm.** Object B is already chartered
   (pjm-135). Object A's *root* is the C3b price shape, and PJM's price-formation
   frontier is **owner-declared at pjm-142** with the diurnal-amplitude family
   **CLOSED** and the overnight gas commitment bridge **`R`**. Opening a
   price-shape mechanism here would re-enter a closed lane without owner
   authorization.
3. **Object A cannot be fully diagnosed from committed artifacts.** Completing it
   needs the 2022 `hrl_da_incs_decs` corpus to compute that year's own
   actual-DA-price reference and confirm it is ≈ 0. That corpus is gitignored,
   absent from this container, and re-fetching it is **out-of-training data intake
   requiring explicit owner authorization** (rule 22, channel 1). The in-sample
   half (+8.13/+7.50/−2.23) **is** established and needs no new data.
4. **Question C is a prerequisite, not a follow-up.** While the 2022 coal basis is
   unexplained, the two available bases disagree on the *sign* of the model's 2022
   coal error. Arming anything sized against either would be sizing against an
   unresolved measurement.

A measured refusal is a full result. What this session delivers is the
**re-pointing** and the **in-sample identification** (§1.1, §2), which is what
makes the next session cheap and legal.

### Recommended next session (for the owner to charter)

Scope it to **Object A, in-sample only**: quantify the DA virtual layer's
deviation from its pjm-105 invariant across 2023–2025, and test — as a
pre-registered, leave-one-year-out A/B on 2023–2025 — whether the keeper is
better described **with the layer disarmed** than with a layer whose net clearing
runs ±8 TWh from its own admissibility anchor. That is a rule-1 structural
question (is this mechanism *real* as implemented?), it needs no new data, and it
never touches 2022. Question C should be settled first or in parallel, since it
governs whether the 2022 C1 coal rows are readable at all.

---

## §7 — rules and governance

- **Rule 22 (holdout):** no solve, no score, no registration of 2022 or any
  out-of-training year. The freeze (`holdout-freeze.json`, re-armed 2026-08-05) is
  intact and was not lifted, tested or worked around. Every identification is
  in-sample.
- **Rules 1 / 13 / 26:** nothing was fitted to the 2022 residual; no adder, knob,
  haircut or off-registry channel was introduced.
- **Rule 25 `[R-ISO-SCOPE]`:** no NEISO parameter, verdict or finding was
  transplanted. The shared NEISO/PJM December miss is noted in the handoff and is
  **not** used as evidence here.
- **Rule 21 `[R-FORCED-BUDGET]`:** the C8 `CT_PEAKER` 31.1 % grounded pass is a
  clean pass and was **not** treated as a defect. The `CT_PEAKER` numbers in §4
  are an input bound, not a forcing claim.
- **Rule 28 `[R-MECH-MATRIX]`:** this session is **OFF-QUEUE BY NECESSITY** — PJM's
  lever queue was cleared at pjm-153 and its price-formation frontier is
  owner-declared at pjm-142. This opened a **new object from holdout evidence**,
  not a re-test of a closed cell; the diurnal-amplitude family and the overnight
  gas commitment bridge (`R`, pjm-142) were **not** re-opened. **No mechanism was
  tested, so no cell changes state and no matrix edit is due** (duty (b) fires on
  a *test*; duty (c) on a *new field* — neither occurred).
- **Rule 15 `[R-DASHBOARD]`:** no run was produced, so there is nothing to
  register. The pjm-156 touchpoint remains registered as-is.
- **Availability parity:** not re-litigated, as instructed.

---

## §8 — reproduction

All committed-artifact reads; none solves an LP.

```
scripts/probes/_pjm157_energy_balance.py        # §1 four-year balance, class totals, §5 question C
scripts/probes/_pjm157_virtual_channel.py       # §1.1 virtual clearing + lmpDeltaHr channel
scripts/probes/_pjm157_switching_elasticity.py  # §2 monthly panel, elasticity, decomposition
scripts/probes/_pjm157_fuel_and_vintage.py      # §3/§4 delivered fuel + pooled-artifact bound
```

All four were executed this session and reproduce every figure quoted above.

Inputs: `results/calibration/pjm2022_touchpoint/hourly/*`,
`results/calibration/pjm152_collapse_A/hourly/*`,
`frontend/data/backcast/runs/{2026-08-05-pjm-2022-touchpoint,2026-08-04-pjm-152-collapse}.js`,
`frontend/data/backcast/bench/PJM/{2022..2025}.json.gz`,
`data/raw/eia-930/PJM_{region,fueltype}_2022.parquet`, `data/raw/PJM_{region,fueltype}.parquet`,
`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`,
`data/raw/_processed-legacy/campd_ct_heat_rates_PJM.csv`.
