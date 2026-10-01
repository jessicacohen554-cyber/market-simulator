# FINDING + PRECOMMIT — the measured monthly gas LEVEL is PROVABLY INERT on MISO's keeper, and the premise that motivated it is wrong for MISO

**Session:** miso-249 (`miso-fuelvintage-1`) · **Date:** 2026-09-09 · **ZERO LP.**
**Scope:** MISO ONLY. No other ISO's shard, keeper, log or calibration-complete entry is touched.
**Branch:** `claude/miso-fuelvintage-1` off `origin/main` `87ad084b`.
**Task:** `docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md` PROMPT 2 (MISO) + ADDENDUM A1–A4, plus the launch prompt's ADDITIONS 0–5.

> **NO SOLVE WAS SPENT AND NONE WILL BE.** The rule 29 `[R-SCREEN]` clause-(0) pre-solve gate the
> prompt's ADDITION 1 named — measure the F923 print-path coverage before spending an LP — **fires**,
> and it fires at the strongest possible strength: not "mostly inert" but **byte-identical**. No run
> was registered because no run exists (rule 15 `[R-DASHBOARD]` has no object here). No keeper moved.
> Every committed MISO bundle is byte-identical at HEAD.

---

## 0. Bottom line

| | |
|---|---|
| **Phase-0 print coverage** (the number the prompt asked for FIRST) | **100.000 %** of MISO gas capacity-hours are print-derived, in **2023, 2024 AND 2025** — every one of 1,609 / 1,616 / 1,614 gas rows, all 8,760 hours, all 12 months. |
| **The arm's effect on the LP** | **ZERO. Byte-identical.** `mc_base` and `fuel_prices` differ in **0 of 28,329,840 / 28,303,560 / 28,181,520 cells**, max abs 0.0. A full deep-diff of the entire fleet-only state finds **0 differing leaves**. |
| **Verdict** | **INERT (`I`)** on MISO's designated keeper. The screen is not reached; the full span is not spent. |
| **The seam itself works** | It reproduces the FINDING's pre-registered §3 table to ~0.0005 $/MMBtu. The mechanism is correct; it has **no live consumer** on MISO's recipe. |
| **THE PREMISE IS WRONG FOR MISO** | `FINDING-xiso` §1a's "model monthly CV = 0.094 in every year" is measured on `_gas_series`, **a series no MISO gas unit pays**. The price the fleet actually pays has CV **0.1388 / 0.2473 / 0.1721** and tracks the measured N3045 blend to within **0.04–0.20 $/MMBtu in every month**. MISO already carries a measured monthly gas level — by the per-plant F923 route. |
| **All three named successors are DEAD or MISDIRECTED** | (i) the F923 fallback target reaches **0.000 %** of gas cap-hours; (ii) both coal sigmoids are OFF on the keeper; (iii) the corroborator is an admissibility filter, not a coverage filler. §6. |
| **The thing the prompt called OUT OF REACH is IN REACH** | EIA-923 Schedule-5 covers **Louisiana in all 12 months of 2019, 2020 and 2021** — and every MISO footprint state, every month, coverage **1.000 in every year 2019–2025**. It prices Uri: MISO **Feb-2021 = 13.90 $/MMBtu** (LA alone **16.10**) vs the model's 4.42. §7. |

---

## 1. Provenance — the reconstruction is the keeper's whole recipe

Every measurement below is built through the **only sanctioned fleet-only reconstruction**
(`replay_keeper.run_year_kwargs` + `derived_run_year_inputs`, caiso-243 §7.3 / caiso-248), never a
name-filtered `meta` dict.

* `run_year_unreachable(meta)` = **`{}`** — there is **no** non-default recorded solve kwarg a
  fleet-only rebuild fails to carry. The rebuild *is* the recipe the keeper solved on.
* Bundle: `results/calibration/miso247_fullspan_K`, keeper `2026-09-09-miso-247-p19-posture`
  (`frontend/data/backcast/keepers/MISO.json`, re-read at HEAD — the keeper did **not** move at
  miso-248, which was a screen).
* Keeper gas recipe, read from `run_config.json` → `scenario_config` (never `meta.json`, which is a
  CLI echo — `FINDING-xiso` §1's own correction):
  `gas_plant_monthly_fuel_pricing True` · `gas_monthly_actuals False` · `gas_hub_basis_overlay False`
  · `gas_daily_shape True` · `gas_seasonality True` · `miso_zonal_gas_basis True` ·
  `miso_zonal_gas_basis_skip_923_priced True` · `miso_winter_citygate_daily True` ·
  `f923_gas_price_plausibility_screen True` · `gas_electric_power_monthly_level` **absent** (the run
  predates the field; default `False`).

**G-CTRL / G-DRIFT (rule 29(b)).** Not load-bearing here and deliberately not relied on: the A/B
below is a **same-HEAD** control — control and arm are both rebuilt at `87ad084b` and differ by the
single flag — which is strictly stronger than form 4's differencing against committed numbers,
because no HEAD drift can enter a difference taken at one commit. The diff scope is recorded for
the file: `git diff b668d88d HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference` = 17 files, +1,067 / −90, of which the seam's own
new module (`data/fuel/electric_power.py` +172), its weight table
(`reference/iso-gas-capacity-state-weights.csv` +52) and its two call sites (`resolve.py` +16,
`trajectories.py` +26) are this program's own landing.

---

## 2. THE PHASE-0 GATE (rule 29 `[R-SCREEN]` clause (0)) — print coverage

`apply_plant_monthly_fuel_prices` runs **after** the seam and returns the `(n_gen, T)` mask of cells
it wrote. Measured over gas generators, **capacity-weighted**, on the keeper's own config:

| year | gas rows | gas cap (MW) | cap-hour written share | rows any-written | rows all-written | per-month share |
|---|---|---|---|---|---|---|
| 2023 | 1,609 | 69,078.756 | **1.000000** | 1,609 / 1,609 | 1,609 / 1,609 | 1.0 in all 12 |
| 2024 | 1,616 | 69,189.704 | **1.000000** | 1,616 / 1,616 | 1,616 / 1,616 | 1.0 in all 12 |
| 2025 | 1,614 | 68,613.441 | **1.000000** | 1,614 / 1,614 | 1,614 / 1,614 | 1.0 in all 12 |

The mechanism matrix's own MISO `zonal_gas_basis` note (miso-213) already recorded "100 % of MISO
gas capacity-hours are print-derived"; this is an **independent** measurement of the same mask and
it agrees exactly. The solve log's own line agrees a third time: *"MISO zonal gas basis (2025): …
100.0% of gas cells skipped as print-derived."*

### 2a. Where that 100 % comes from — the decomposition that kills successor (i)

Re-measured with `nearby_fuel_price_fallback` disarmed, so the mask is own-print only:

| year | own F923 print | nearby-pool fill | **terminal trajectory default** |
|---|---|---|---|
| 2023 | 68.5337 % | 31.4663 % | **0.000000 %** |
| 2024 | 67.8093 % | 32.1907 % | **0.000000 %** |

The per-fuel trajectory default — the thing the seam would replace if it were wired as the F923
fallback chain's terminal level — reaches **exactly zero** MISO gas capacity-hours. Successor (i) is
measurably inert before it is built.

---

## 3. THE DECISIVE GATE — the arm is byte-identical in the LP's own inputs

Control and arm rebuilt at the same HEAD; the arm adds **only**
`gas_electric_power_monthly_level=True`, routed through the same `prb_overrides` channel
`replay_keeper --set` uses. The `fleet_only` exit returns the **assembled P0 objective the LP is
handed** — `mc_base` (fuel + VOM + carbon + NOx + EAC + coal tranches, every pricing overlay
applied) and `fuel_prices`. Byte-identical `mc_base` ⇒ byte-identical LP, with no solve.

| year | `mc_base` shape | `mc_base` n_diff | `fuel_prices` n_diff | non-gas n_diff | gas n_diff | max abs |
|---|---|---|---|---|---|---|
| 2023 | (3234, 8760) | **0** | **0** | 0 | 0 | 0.0 |
| 2024 | (3231, 8760) | **0** | **0** | 0 | 0 | 0.0 |
| 2025 | (3217, 8760) | **0** | **0** | 0 | 0 | 0.0 |

**Deep diff of the ENTIRE fleet-only state** (every returned object — `fleet`, `fleet_arrays`,
`storage_units`, `storage`, `storage_power_cap`, `wind_cf`, `wind_cap`, `solar_cf`, `solar_cap`,
`wind_mc`, `solar_mc`, `demand`, `mc_base`, `fuel_prices` — recursed through arrays, dataclasses,
dicts and object `__dict__`s): **0 differing leaves** in 2023 and in 2024. The only `ScenarioConfig`
field that moves is **the flag itself**.

### 3a. The seam DOES fire — on a series nothing consumes

| year | `_gas_series` cells changed | annual mean control → arm | max month gap | FINDING §3's pre-registration |
|---|---|---|---|---|
| 2023 | 8,760 / 8,760 | 2.8392 → **3.0187** (+0.1795) | **1.0003** (Jan) | +0.179, max gap 1.000 (Jan) ✓ |
| 2024 | 8,760 / 8,760 | 2.4893 → **2.5580** (+0.0687) | **1.5513** (Jan) | +0.069, max gap 1.551 (Jan) ✓ |
| 2025 | **0** | 3.8190 → 3.8190 | 0.0000 | **inert by coverage (basket 0.40)** ✓ |

The mechanism reproduces its own pre-registered table to **~0.0005 $/MMBtu**. It is not broken —
it is unconsumed. **2025's predicted byte-identity is CONFIRMED at zero LP**, which is the ADDITION-2
STOP check discharged without spending the year.

### 3b. Why `_gas_series` reaches nothing — every consumer gate, on the keeper

| `_gas_series` consumer | gate | keeper value |
|---|---|---|
| coal passthrough sigmoid (prb) | `coal_prb_passthrough_sigmoid` | **False** |
| coal passthrough sigmoid (bit) | `coal_bit_passthrough_sigmoid` | **False** |
| PRB follower tier | `coal_prb_passthrough_tiered` | **False** |
| gas-offer-margin anchor re-resolution (pjm-169 F4) | `gas_offer_margin_anchor_vintage` | **False** |
| zonal anchor | `gas_offer_margin_zonal_anchor` | **False** |
| MISO measured offer surface | `miso_offer_surface_measured` | **False** |
| MISO anchored spread graft | `miso_offer_spread_anchored` | **False** |

`gas_offer_net_revenue_margin` **is** True, but its anchor is the frozen window value (3.0492
$/MMBtu, as the solve log reports) — the `_gas_series` re-resolution is gated on
`gas_offer_margin_anchor_vintage`, which is False. That is confirmed empirically, not just by
reading: the zero `mc_base` diff is exactly the statement that the anchor did not move.

---

## 4. Rule 19 `[R-ONE-MECH]` — the interaction worked out IN WRITING (PROMPT 2 card 0(d))

The prompt required this be settled before solving. It was, and it is what predicted the result.

| mechanism | level or spread? | interacts with this LEVEL? |
|---|---|---|
| `miso_zonal_gas_basis` | **mean-zero spread**, additive, annual per-zone | **orthogonal** — cannot move a level |
| `miso_zonal_gas_basis_skip_923_priced` | a *mask consumer*, not a price term | **orthogonal to the seam**: the print mask depends only on F923 availability + the plausibility screen's own N3045 reference, never on the incoming `fuel_prices`, so arming the seam cannot change which cells are print-derived. Confirmed: identical masks in both arms. |
| `miso_winter_citygate_daily` | **shape**, mean-preserving *within month* (it divides out the national daily shape and multiplies in Chicago's) | **orthogonal** — preserves whatever level sits underneath |
| `gas_daily_shape` | **shape**, mean-preserving per month | orthogonal (different timescale; the seam module says so) |
| **`gas_plant_monthly_fuel_pricing` (the F923 print path)** | **LEVEL**, per plant, per month | **SUPERSEDES THE SEAM ENTIRELY.** It runs after it and overwrites 100.000 % of gas cells. **This is the answer.** |

**The rule-19 ordering in `data/fuel/electric_power.py` is correct as written** — *national annual <
state-average monthly < measured hub index* — but it is **incomplete**: it does not name the
**per-plant F923 print**, which is a fourth and *more local* measured level that sits above all
three. On MISO that omission is the whole result. Recommended (not made here, it is a shared-module
edit): add the print path to that ordering as *state-average monthly < per-plant measured receipts*,
so the next ISO's lane reads the supersession before it spends a phase 0.

---

## 5. THE PREMISE CORRECTION — MISO already has a measured monthly gas level

`FINDING-xiso` §1a's fingerprint table gives MISO **0.094 in all of 2019–2025** and reads it as
"MISO's gas price shape is identical in Winter Storm Uri and in a mild spring." That statistic is
computed on `_gas_series`. **No MISO gas unit pays `_gas_series`.** Measured on `fuel_prices` — the
array the LP actually prices on — capacity-weighted:

| year | **PAID** monthly cv | PAID annual | `_gas_series` cv | measured N3045 blend cv | N3045 annual |
|---|---|---|---|---|---|
| 2023 | **0.1388** | 3.1343 | 0.0943 | 0.1481 | 3.0205 |
| 2024 | **0.2473** | 2.6676 | 0.0938 | 0.2552 | 2.5542 |
| 2025 | **0.1721** | 3.9029 | 0.0943 | — (inadmissible) | — |

Month by month, PAID vs the measured N3045 blend ($/MMBtu):

```
2023 paid  4.3335 3.6198 3.1015 2.7136 2.6542 2.7374 3.0390 3.0480 3.0520 3.1169 3.1427 3.0524
2023 N3045 4.2663 3.5220 3.0043 2.6229 2.5372 2.6218 2.8948 2.9240 2.9739 2.9722 3.0162 2.8901
2023 gap   +0.067 +0.098 +0.097 +0.091 +0.117 +0.116 +0.144 +0.124 +0.078 +0.145 +0.127 +0.162

2024 paid  4.4923 2.5457 2.0703 2.0279 2.3727 2.6283 2.4088 2.3235 2.5807 2.4629 2.5497 3.5486
2024 N3045 4.4148 2.4164 1.9818 1.9896 2.2351 2.4557 2.3041 2.2183 2.3838 2.4838 2.4184 3.3488
2024 gap   +0.078 +0.129 +0.089 +0.038 +0.138 +0.173 +0.105 +0.105 +0.197 −0.021 +0.131 +0.200
```

**The two series agree to 0.04–0.20 $/MMBtu in 23 of 24 months, with a uniformly positive sign.**
That is the physically expected relationship: plant receipts carry delivered transport that a
state-wide average partly averages away. MISO's paid January is 4.49 against an April of 2.03 — a
2.2× within-year swing, not a fixed climatological shape.

**So MISO is not "one of only two ISOs whose keeper carries no measured monthly gas level at all."**
It carries one, by a route `FINDING-xiso` §1's table has no column for: `gas_plant_monthly_fuel_pricing`.
That table reads `gas_monthly_actuals` / `gas_hub_basis_overlay` / zonal basis only. This is the same
correction pattern as §1 itself, one level further down: §1 corrected a `meta.json` reading with
`run_config.json`; this corrects a `_gas_series` reading with `fuel_prices`.

Stated plainly and at full magnitude, per rules 1 / 14: **there is no monthly-gas-LEVEL defect to
repair in MISO 2023–2025.** The seam is a correct mechanism aimed at a defect this ISO does not have
in the years it may solve.

---

## 6. The three named successors, adjudicated on measurement

The prompt (ADDITION 1) named three and asked for a recommendation, not a build. None survives:

1. **"Make the seam the LEVEL the F923 fallback chain falls back to."** **DEAD, measured.** §2a: the
   terminal default reaches **0.000 %** of MISO gas capacity-hours. Own print 68.5 %, nearby pool
   31.5 %, default 0.0 %.
2. **"The coal-sigmoid gas key alone."** **DEAD on this keeper.** Both sigmoids are `False`
   (passthrough flat 1.0). Reaching it means arming a *different* mechanism, and even then it would
   never touch a gas unit's offer — it would move coal's, which is a coal question, not this one.
3. **ercot-261's corroborator pattern.** **MISDIRECTED, and the prompt's hope for it is refuted.**
   ADDITION 4 hoped it "could rescue MISO's Louisiana coverage hole." It cannot, by construction:
   the corroborator is an **admissibility filter** that holds out a month whose survey print
   disagrees with an independent receipts measurement and substitutes that year's *corroborated*
   mean. It needs a printed month to test. Louisiana 2019–2021 prints **nothing** in N3045 — there
   is no month to corroborate. It solves "the print is not a price" (the ercot-254
   within-February-smearing class), not "there is no print."

   **But its second instrument is the answer** — see §7.

---

## 7. WHAT THE PROMPT CALLED OUT OF REACH IS IN REACH — and it is already on disk

ADDITION 4 states MISO's Feb-2021 defect (11.245 $/MMBtu, ~84 $/MWh — the program's largest in-scope
defect) is "NOT FIXABLE from this source and NOT SOLVABLE by you," because EIA prints no N3045 month
for Louisiana in 2019–2021. **The first half is right; the second half is right only of *this*
source.** The corroborator's own second instrument — **EIA-923 Schedule-5 quantity-weighted plant
receipts** — measures the identical quantity and is already loaded by MISO's print path on every
solve (`data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`).

**Month coverage, EIA-923 Schedule-5 Natural Gas, every MISO footprint state, 2019–2021:**

| AR | IA | IL | IN | KY | **LA** | MI | MN | MO | MS | MT | ND | SD | TX | WI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 12 | 12 | 12 | 12 | 12 | **12** | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |

— in **each** of 2019, 2020 and 2021. Blended on the **same** MISO gas-capacity weights the seam
uses, footprint coverage is **1.000 in every year 2019–2025** (N3045's is 0.30–0.34 in 2019–2021 and
0.40 in 2025):

| year | annual $/MMBtu | monthly cv | Jan | **Feb** |
|---|---|---|---|---|
| 2019 | 2.7268 | 0.1433 | 3.5929 | 3.1263 |
| 2020 | 2.2847 | 0.1374 | 2.2913 | 2.1414 |
| **2021** | **4.9897** | **0.5709** | 2.9975 | **13.9023** |
| 2022 | 6.5996 | 0.1698 | 5.2115 | 5.3837 |
| 2023 | 3.1582 | 0.1543 | 4.4694 | 3.8112 |
| 2024 | 2.6107 | 0.2264 | 4.2094 | 2.5773 |
| 2025 | 3.7753 | 0.1525 | 4.8437 | 4.6031 |

Louisiana alone, 2021: `3.15 16.10 2.81 2.95 3.19 3.49 4.12 4.40 5.32 5.96 5.88 4.16`. **Uri is in
the data, at the state the prompt correctly identified as the one that matters.** The 2023/2024
blend (3.1582 / 2.6107) also lands within 0.03–0.06 of what the fleet actually pays (3.1343 /
2.6676), which is the consistency check that the blend is the right object — as it must be, since
the paid price is built from these same receipts plant by plant.

### 7a. Three things that must be said with it, or the recommendation is dishonest

1. **A MONTHLY form would reproduce ercot-254's failure exactly.** Applying 13.90 $/MMBtu to all 672
   February-2021 hours when the real spike was ~5 days is the *identical* defect
   `RESULT-ercot254` §3b diagnosed (C3c 234 → 688 h against 258 actual). **Do not build MISO's 2021
   repair at monthly resolution.** ercot-254 §6 already named the successor form: a **daily** series.
   For MISO that means daily hub settlements (Chicago Citygate is already intaken and armed as a
   *shape*; a Gulf/MidCon daily would be the new intake), or the corroborator's filter form.
2. **MISO cannot spend 2021.** It holds no `complete` marker; `holdout_policy.registration_refusals`
   refuses 2020/2021/2022 at both the launch and the registration gate. So this is **blocked on an
   owner marker decision, not on data**. Preparing the input is unrestricted (rule 22: "what is held
   out is the SCORE, never the DATA"); *looking at the answer* is the spend.
3. **It is not obviously a 2023–2025 lever at all.** §5 shows the paid level already tracks the
   measured blend to ±0.2 $/MMBtu in the training years. The F923-blend route's value is
   concentrated in **2021**, i.e. in a year MISO may not currently score.

---

## 8. Governance ledger

* **Rule 29 `[R-SCREEN]`** — clause (0) discharged and it **killed the arm**. Screen year 2024 was
  named ex ante on the mechanism's own footprint (max month gap 1.551 vs 2023's 1.000), never a
  residual; the screen was never reached because the zero-LP gate settled it first, which is exactly
  the order the rule prescribes. No screen bundle, no control bundle, no full span.
* **Rule 31 `[R-RETAIN]`** — **nothing to retain.** No solve was run, so no bundle exists, on disk or
  otherwise. The retention question is moot this session; the promotion question is asked in §9.
* **Rule 15 `[R-DASHBOARD]`** — **no object.** The rule registers *completed runs*; this session
  completed none. Nothing was registered and nothing was pruned. This document is the record.
* **Rule 16 `[R-ALLYEARS]`** — untouched. No fragment was registered because no bundle was produced.
* **Rule 21 `[R-DOF]`** — the seam carries **zero** free parameters (frozen EIA-860 weight derive,
  the EIA 1.036 MMBtu/Mcf heat content, two ex-ante admission conditions). Nothing was swept.
* **Rule 22 `[R-HOLDOUT]`** — **no out-of-training year was solved, scored or registered.**
  `--holdout-authorized` was never passed. §7's coverage measurement is **data preparation**, which
  rule 22 as amended 2026-08-06 places explicitly outside the spend.
* **Rule 28 `[R-MECH-MATRIX]`** — MISO's cell `gas_electric_power_monthly_level` moved **O → I** with
  this citation. Only `docs/codebase-site/data/mechanism-matrix/MISO.js` was edited.
* **Rule 12 `[R-PARALLEL]` / ADDITION 2** — the three shard sessions (S / T1 / T2) were **not
  launched**. Launching them would have spent ~35–70 min of LP per arm to reproduce a difference
  already proved to be exactly zero.
* **The retiree window (commit `7934e92c`) is credited with NOTHING**, as instructed: it adds MISO
  189 units / 9,127.8 MW in 2019–2022 and **0 MW** in any year MISO may solve. Had a solve run, it
  would have been a pure fuel A/B. `FINDING-xiso` §2a.
* **ADDITION 5 baselines, re-measured on THIS tree** — §10.

---

## 9. THE PROMOTION QUESTION, ASKED EXPLICITLY (rule 31)

**There is nothing to promote, and that is the recommendation.**
`gas_electric_power_monthly_level` should stay **BUILT and default-OFF** for MISO. Arming it would
change the run's cache key and re-key the bundle while solving a **byte-identical LP** — a
declaration in `run_config.json` that the run prices gas on a measured state blend, when 100.000 %
of its gas cells are priced by the per-plant print instead. That is a provenance defect of exactly
the class caiso-157 / caiso-188 fought (a bundle advertising a mechanism that never ran), so arming
it is worse than neutral.

**The two questions that ARE for the owner:**

1. **Should MISO's lane build the EIA-923 Schedule-5 blended monthly level (§7)?** It is the only
   route measured to reach Feb-2021, it needs no new intake (the parquet is already on disk and
   already read every solve), and it carries the same zero-DOF construction. **But it must not be
   built at monthly resolution (§7a.1), and MISO cannot score the year it would fix (§7a.2).**
2. **Should MISO be granted a `complete` marker?** Stated as the prompt directs — *said, not acted
   on*. MISO is the only ISO in this program that cannot touch 2020–2022, so its largest known
   defect is unreachable by construction. I have not passed `--holdout-authorized`, have not solved
   any out-of-training year, and have changed no marker file.

---

## 10. ADDITION-5 gate baselines, re-measured on this tree (`87ad084b`)

Reported so the next lane does not attribute a pre-existing red to this branch. This branch changes
**one** matrix shard file and adds **one** doc; it touches no source, no test and no config.

| gate | baseline on this tree | attribution |
|---|---|---|
| `pytest tests/scoring` | see §10a | pre-existing; this branch adds none |
| `check_cache_key_registration --base origin/main` | RED, `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` | pre-existing on `main` (ADDENDUM A3) |
| `build_status --check --iso CAISO` / `audit_keepers --iso CAISO` | RED | CAISO's lane's, rule 25 — not touched |
| `check_mechanism_matrix` | see §10a | — |

### 10a. Measured

* **`pytest tests/scoring` → `16 failed, 1532 passed, 12 skipped` (129.72 s).** This is **exactly**
  ADDENDUM A3's corrected baseline of 16 (not the launch prompt's older "15"), so **this tree adds
  none and this branch adds none**. The 16: `test_backcast_artifacts` (1),
  `test_ff_readiness_battery` (4), `test_forecast_parity` (2), `test_gate_a_provenance` (1),
  `test_golden_manifest_provenance` (7), `test_registration_marker_gate` (1).
* **`check_mechanism_matrix.py --base origin/main` → EXIT 0**, both before and after the MISO cell
  edit: integrity OK across the base row + 7 ISO shards, keeper stamps match, §5.x prose headers
  match, gap / shared / absent-shared ratchets OK. The 12 anchor warnings are emitted by the tool
  itself as *"pre-existing, not this PR."* `node --check` on the edited shard: syntax OK.
* **Files this branch changes:** `docs/codebase-site/data/mechanism-matrix/MISO.js` (one cell) and
  this document. **No source, no test, no config, no keeper shard, no `calibration-complete.json`,
  no other ISO's anything.**
