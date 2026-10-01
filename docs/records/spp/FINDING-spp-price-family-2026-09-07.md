# FINDING — SPP PRICE FAMILY: the screen **KILLS** the offer-curve arm on its structural leg, *while the arm improves both target criteria*. The price family is **two objects, not three**, and only one is reachable by this channel.

**Lane:** SPP PRICE-FAMILY. **Branch:** `claude/spp-price-family-calibration-de9ddj`. **DATA PROFILE: spp.**
Pre-registration: `PRECOMMIT-spp-price-family-2026-09-07.md`, pushed **before any LP**.
**NOTHING ARMS. No bundle is registered. The SPP keeper `2026-09-07-spp-2-crosswalk-hydro` is unchanged.**
One screen solve was spent (2025). The remaining years were **not** spent, per rule 29.

---

## 0. Verdict

| | result |
|---|---|
| **What the C3a/C3b miss is** | the model's **mid-stack is ~10 % too dear, load-weighted**. Against the $200-capped actual it is **+16.6 / +10.8 / +12.5 %** in 2023/2024/2025 — failing in *all three* years, not the one the scorer shows. |
| **What drives SPP's price surface** | **LOAD, not fuel.** `corr(monthly actual price, delivered gas) = +0.2720` vs `corr(price, load) = +0.7791`; implied market-HR **CV 0.3874**. SPP **inverts** PJM (0.9531 / 0.2449 / 0.082). |
| **Arm — a derived `offer_curve_by_group` band quadruple** | **KILLED by the screen on G-2.** It moved the price **level** exactly as predicted (−9.05 % vs −10.08 % predicted, G-1 PASS) and did **not steepen the stack**: ratio 1.6214 → **1.6298, +0.5 %**, against the required ≥ 1.783. |
| **Why** | a **uniform quadruple applied to every class is a LEVEL lever, not a SHAPE lever**. Measured: the arm/control price ratio is **0.9070–0.9151 across the entire load range, a 0.81 pp spread**. The surface moved DOWN; it did not ROTATE. |
| **C3c** | a **different object** — only **3/42, 5/59, 3/68** of the >$200 hours are in the top 5 % of load, at market heat rates **79–93×** gas. Unmoved by the arm (1 → 1 h), as predicted. Routed to **SPP-55**. |
| **C1 2024** | **not reachable by this channel** — a `pct_peaking` structural share rule 1(a) forbids it from touching. The arm moved CT_PEAKER −0.247 TWh against a −9.9 TWh miss. |

**The headline result is a refusal.** The arm takes C3a 2025 from **+7.2 % to −2.5 %** and C3b from
**0.1894 to 0.1708**. Both improve. **It is rejected anyway**, because the pre-registered structural
gate says it did not do the thing it was declared to do. Promoting it on the residual alone is
exactly the fitted-mechanism selection rule 1 `[R-STRUCT]` exists to forbid, and the carve-out's
condition (c) refuses a multiplier selected by which criterion it makes pass.

---

## 1. Phase 0 — the decomposition (zero LP, on the committed keeper bundle)

Method: `FINDING-pjm-price-tail-2026-09-07.md`. Inputs: SPP's committed keeper hourlies
(`spp42_crosswalk_B`), SPP's hourly RT LMP (`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`
— reproduces the scorer's 42 / 59 / 68 hours >$200 exactly), SPP's own delivered gas
(EIA `N3045KS3` / `N3045OK3`, $/Mcf ÷ 1.037). 36 pooled months.

| statistic | **ACTUAL SPP** | MODEL | PJM 2021 |
|---|---|---|---|
| `corr(monthly price, delivered gas)` | **+0.2720** | +0.6969 | +0.9531 |
| `corr(monthly price, monthly load)` | **+0.7791** | +0.5984 | +0.2449 |
| implied market heat rate **CV** | **0.3874** | 0.2514 | 0.082 |
| `corr(implied market HR, delivered gas)` | **−0.6012** | — | −0.0235 |

**SPP inverts PJM on every line.** The model is *more* fuel-coupled (+0.697) than the market it
reproduces (+0.272). So `gas_monthly_actuals` / `gas_daily_shape` **cannot be the C3a/C3b cause** —
a real rule-14 question, answered negatively for *this* residual and left open as an input question.

**The tail is a merit-order outcome, not a shortage outcome.** Zero slack and zero dump in all
8,760 hours of 2023 and 2024; 2025 carries one slack hour (89.3 MWh). `scarcity_pricing_enabled`,
`scarcity_price_overlay` and `energy_reserve_coopt` are all `False` — SPP has **no scarcity
mechanism of any kind**.

### 1.1 The mechanism, named

Every band of every class SPP dispatches is **1.0** in the shared default, so a plant's four
tranches are **price-identical** and the LP loads them proportionally. The keeper's own band
ledger (2023):

| class | committed | econ_low | econ_high | **peak** |
|---|---|---|---|---|
| `CC_REGULAR` | 12.41 TWh / 8,578 h | 12.41 / 8,663 | 12.42 / 8,660 | **4.18 TWh / 8,624 h** |
| `CT_PEAKER` | 1.43 / 8,752 | 9.02 / 8,759 | 8.13 / 8,759 | **1.42 TWh / 8,759 h** |
| `COAL_PRB` | 14.10 / 8,689 | 16.70 / 8,731 | 13.65 / 8,729 | **1.27 TWh / 8,723 h** |

**A peak band that runs in 8,759 of 8,760 hours is not a peak band.**

### 1.2 Market heat rate by system-load percentile

| load pct | 0-10 | 10-25 | 25-50 | 50-75 | 75-90 | 90-95 | 95-98 | 98-99.5 | 99.5-100 |
|---|---|---|---|---|---|---|---|---|---|
| measured | 6.81 | 5.53 | 5.42 | 5.64 | 7.33 | 9.49 | 10.66 | 12.14 | **13.61** |
| model | 7.89 | 7.70 | 7.92 | 7.96 | 9.19 | 11.32 | 12.23 | 13.01 | **13.59** |

**Correction against this lane's own first reading, recorded rather than quietly dropped:** the
model's stack is **not flat** on this axis — it rises +72 % against the measured +100 %, and at the
top the two agree to 0.2 %. An earlier monthly-tercile statement (+2 % vs +37 %) was **confounded
by the gas axis** and is **withdrawn**. The correct statement: the model is too dear everywhere
below the top ~2 % of hours, worst in the middle (25-75 pct, +41 to +46 %).

### 1.3 The tail is a separate object

The 60 highest measured RT hours per year:

| year | median price | median measured **market HR** | median **load pctile** | >$200 hours also in the **top 5 % of load** |
|---|---|---|---|---|
| 2023 | $234.60 | **84.10** | 43.7 | **3 of 42** |
| 2024 | $244.25 | **92.77** | 84.4 | **5 of 59** |
| 2025 | $313.35 | **79.29** | 40.3 | **3 of 68** |

System median market HR is 5.3–7.1. **SPP's spikes happen at ordinary load at 80–93× gas.** No band
multiplier reaches them without making the whole stack ~10× dearer.

---

## 2. G-DRIFT (rule 29(b)) — no control solve was spent

`git diff 33034499 HEAD -- src/market_sim scripts/… data/raw/_validation-source data/raw/reference`
→ 11 files. Ten classify **INERT for SPP backcast** (CAISO nuclear-CF / carbon / DSW-depth 2022 rows
= another ISO's branch and a year SPP does not solve; capx D76 `capacity_screen_peak_measured_hindcast`
= behind the `config.hindcast` predicate a `mode="backcast"` run never enters, and `cache.py`'s own
census lists SPP's `*-plain-backcast` key `989da50bbf0f99d8` **UNMOVED**; the SPP area-LMP parquet is
scoring-side; `pipeline/backcast_config.py` is the keeper's own spp-42 change, which it solved WITH).

**One hunk is LIVE:** `data/eia930/actuals.py`, SPP-41's `NG:` unit-slip screen, which touches the
LP's delivered wind bound. **Bounded by measurement to 2023 alone** — running the screen over the
SWPP frame: **2023** NaNs exactly one hour (`NG: WND` h3907 = 3,589,445 MW vs a 22,597 MW p99.9),
removing **3.5894 TWh**; **2024 removes 0.0000 TWh; 2025 removes 0.0000 TWh.**

⇒ For 2025 the audit is all-INERT, **form 4 is valid**, and the keeper's committed bundle is the
control. **Addendum**, re-run against `origin/main` (41 commits ahead of this lane's base): the only
new solve-path hunks are `ercot_zonal_spread_ep_referenced` (new `ScenarioConfig` bool, **default
`False`**, absent from SPP's recipe) and its ERCOT-only implementation in `data/fuel/basis/ercot.py`
— both **INERT for SPP**, so form 4 survives the rebase.

---

## 3. The arm, as declared and as applied

Declared ex ante in the PRECOMMIT §4.1, unchanged: **`committed 0.845 / econ_low 0.794 /
econ_high 1.018 / peak 1.118`**, one config for all years, derived as the load-weighted measured
market heat rate (RT LMP capped at $200) ÷ the model's, per band stack-position, pooled 2023-2025.

**One correction between declaration and solve, disclosed:** the declared class list named
`ST_CHP`, which has **no registered base curve** in SPP's resolved `offer_curve_by_group`; the merge
created an entry with no `econ_low_share` and the first launch died with `KeyError: 'econ_low_share'`.
The list was narrowed to the **10 registered classes SPP dispatches** (`CC_REGULAR, CC_CHP, CT_CHP,
CT_PEAKER, ST_GAS, COAL_LIGNITE, COAL_PRB, COAL_BIT, COAL_WC, COAL`). **The values did not change.**
The three `*_INTERMEDIATE` curves were left untouched — they carry a separately-identified
ERCOT-lineage shape, and all three splits (`cc_/ct_/st_gas_intermediate_split`) are **`False`** in
SPP's recipe, so they are provably unreachable.

Verified on the arm's own `run_config.json`: `CT_PEAKER` keeps `econ_low_share=0.526, pct_peaking=7.0`;
`COAL_PRB` keeps `econ_low_share=0.55`; `CC_INTERMEDIATE` is unchanged at `peak=2.25`. **No `phys_*`,
no structural share, no new adder** — rule 1(a) satisfied by inspection.

Pre-declared cache keys (corrected arm, computed on the solved window): 2023 `e849e29da8bafb06`,
2024 `7452a721e47fce6e`, **2025 `02b65eb58d6e4326`**; controls `82d7cb4c4214fad3` /
`bc2a307f96da7e17` / `8cc2254194c87b50`.

---

## 4. THE SCREEN — 2025, graded against the pre-registered STOP gate

Screen year **2025**, named in the PRECOMMIT before it ran, on the mechanism's **largest own
footprint** (re-priced energy 911.3 M$ vs 787.2 / 732.6) — and note against interest, 2025 is a year
where C3a currently **PASSES** (+7.2 %) while 2023 is the worst residual (+14.1 %).

| leg | requirement | measured | verdict |
|---|---|---|---|
| **G-1** direction/magnitude | LW mean in **[25.47, 28.47]** (predicted −10.08 %) | 29.971 → **27.258** (**−9.05 %**) | **PASS** |
| **G-2** steepening | MHR(>95 pct)/MHR(25-75 pct) **≥ 1.783** (control 1.6214; measured SPP 2.1088) | **1.6298 (+0.5 %)** | **STOP** |
| **G-3** footprint | non-thermal move < 1 %, unserved ≤ 200 MWh | wind/solar/nuclear/hydro **0.000 %**; unserved **90.6 MWh**; dump 0.0 | **PASS** |

**G-2 is the leg that matters and it fails decisively.** The mechanism was declared as a stack-shape
repair; it delivered a level shift.

### 4.1 The evidence for *why* — the arm did not rotate the surface

Load-weighted price by load percentile, 2025:

| load pctile | hrs | control $ | arm $ | **arm/control** | measured $ |
|---|---|---|---|---|---|
| 0-10 | 876 | 24.973 | 22.652 | **0.9070** | 25.558 |
| 10-25 | 1,307 | 25.954 | 23.599 | **0.9092** | 22.712 |
| 25-50 | 2,197 | 27.999 | 25.442 | **0.9087** | 22.381 |
| 50-75 | 2,190 | 29.442 | 26.735 | **0.9081** | 27.034 |
| 75-90 | 1,314 | 34.194 | 31.167 | **0.9115** | 31.608 |
| 90-95 | 438 | 35.407 | 32.201 | **0.9095** | 39.490 |
| 95-98 | 271 | 35.037 | 32.064 | **0.9151** | 39.768 |
| 98-100 | 167 | 37.476 | 34.134 | **0.9108** | 44.375 |

**The ratio is 0.9070–0.9151 across the whole range — a 0.81 pp spread.** A near-constant multiplier
at every load level.

**The structural reason, which is the transferable result.** Applying the *same* quadruple to *every*
class preserves the between-class merit order. Within a plant the tranches do now order strictly
(0.794 < 0.845 < 1.018 < 1.118, where before they were all identical), but the **marginal** unit at
any load level is set by the *between-class* stack, which did not rotate — so every hour's price
scaled by roughly the same factor. **To steepen SPP's stack the multipliers must differ ACROSS
classes**, or the band *shares* must change — and the shares (`econ_low_share`, `pct_peaking`) are
structural, which rule 1(a) forbids this channel from touching.

### 4.2 Reported at full magnitude — what the arm WOULD have delivered (2025)

| criterion | control | **arm** | actual | gate |
|---|---|---|---|---|
| **C3a** mean LMP | 29.971 (**+7.2 %**) | **27.258 (−2.5 %)** | 27.957 | ±10 % |
| **C3b** monthly NRMSE | 0.1894 | **0.1708** | — | ≤ 0.20 |
| **C3c** hours >$200 | 1 | **1** | 68 | [0.5×, 2×] |

Thermal energy moves (TWh): `COAL_PRB` +0.439, `COAL_LIGNITE` +0.180, `CC_REGULAR` +0.018,
`CT_CHP` −0.018, `CC_CHP` −0.028, `ST_CHP` −0.047, `CT_PEAKER` **−0.247**, `ST_GAS` −0.297.
The CT→CC direction is right and the **magnitude is trivial** against 2024's −9.9 TWh miss —
independent confirmation that C1 is not reachable through this channel.

**Both target criteria improve and the arm is rejected anyway.** That is the gate working.

---

## 5. Honest disclosures

1. **A superseded first derivation.** The same ratios were first computed on **medians, uncapped**:
   `0.774 / 0.699 / 0.793 / 0.900` (~0.75 uniform equivalent, ≈ −14 to −20 % on C3a). Superseded on
   method — C3a is a *load-weighted* mean, and the >$200 surface is SPP-55's object, so crediting the
   offer curve with it would double-count — **not** on what it scored.
2. **A coupling diagnostic that preceded the revised derivation.** A uniform-multiplier table
   (0.70…1.00 against the C3a band) was run to test whether the model's mean depends on the missing
   tail. It answered that (it does not: the measured tail is only 0.53 / 0.76 / 1.32 $/MWh, i.e.
   2.2 / 3.1 / 4.7 % of the measured LW mean). It is **not** the selection instrument, but it ran
   *before* the revised derivation, which is the uncomfortable ordering, so it is disclosed.
   The derivation was run **once** and not adjusted after its prediction was seen.
3. **A construction limitation in the derivation itself.** It maps *system-load* percentiles onto
   *within-plant* tranche positions. That mapping is weakest at the bottom, and it shows: it yields
   `econ_low` (0.794) **cheaper than** `committed` (0.845), inverting the intended physical ordering
   of a min-load block. Stated at the time of declaration, not after the result.
4. **A monitoring error in this session.** `pgrep -f "run_calibration_full.py --iso SPP"` matched this
   lane's own monitor wrapper, so several status readings reported "still solving" after the python
   process had already died. Corrected in the open.
5. **The screen solve was OOM-killed in its post-solve report stage** (7.5 GB RSS, no traceback).
   **The LP itself completed** and wrote every hourly sidecar, so G-1/G-2/G-3 are graded from
   `system_2025.parquet` and `class_hourly_2025.parquet` — the same artifacts the scorer reads.
   **G-4 (C2/C4) was therefore NOT evaluated**, and this finding does not claim it. It does not
   change the verdict: **G-2 is a STOP on its own**, and G-4 could only have added a second one.

---

## 6. What this leaves for the next lane

- **`offer_curve_by_group` is adjudicated `R` for SPP as a UNIFORM quadruple** — the level moves, the
  shape does not. **A per-class differentiated curve is a DIFFERENT, still-open question** and this
  finding does not close it. Whoever opens it must derive the class differentiation from SPP's own
  data and pre-register how, because a per-class quadruple has far more freedom and is
  correspondingly easier to fit.
- **C3c → SPP-55 (VRL-based scarcity design).** §1.3 is its measured target: spikes at ordinary load
  at 79–93× gas, in a model with no scarcity mechanism at all and zero slack/dump.
- **C1 2024 → a `pct_peaking` question.** 92.6 % of a CT's capacity sits outside its `peak` band.
  That is a structural share, not this channel's.
- **The gas-series question stays OPEN**, not closed: `gas_monthly_actuals` / `gas_daily_shape` are
  `False` and `data/raw/spp_zonal_gas_hub.csv` exists and is unarmed. §1 shows they are not the
  C3a/C3b cause; none was tested as an arm.
- **Rule 29(c):** the screen bundle `results/calibration/spp_price_screen_ARM/` is **deleted before
  merge**. Every number this lane cites from it is in this document.
