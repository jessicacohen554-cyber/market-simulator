# PRECOMMIT — `netload_drag_merit_allocation`: fill the drag mandate cheapest-first (ercot-259)

**Session** ercot-259 · **ISO** ERCOT · 2026-09-08
**Pushed BEFORE any LP was solved** (rule 29 `[R-SCREEN]`). Every gate, the screen
year, the drift audit and all predictions below are registered here, upstream of
the arm. Nothing in this document may be edited after the screen runs; a
correction goes in an addendum.

**Incumbent keeper** `2026-09-08-ercot256-drag-layup-mask`
(`results/calibration/ercot256_five_year_keeper`, `git_sha 92dee13c`, branch
`claude/ercot-2021-rubric-failures-r7fu5d`, merged at `ffc25ece`).

---

## 1. THE MECHANISM, AND WHY IT IS STRUCTURAL

`ScenarioConfig.netload_drag_merit_allocation`, default `False`.

The net-load drag's driver curve produces `floor_frac` — **a fleet capacity
factor** (`docs/ercot-st-gas-netload-drag-2026-06.md`: the ST_GAS fleet's
overnight CF regressed on net load). `apply_netload_reliability_floor` then
applies that one fraction to **every** non-peak tranche's own `pmax`:

```python
target = np.minimum(floor_frac * pmax[g], basis * pmax[g])   # same floor_frac, every g
```

That asserts something the driver never measured: **that every plant is
committed at that fraction in every hour.** Physically the level sits *below*
any boiler's minimum stable load, and real commitment is lumpy — some plants
synchronized at min load, the rest dark.

**When armed**, the same hourly mandate over the same rows is instead **filled
cheapest-first**: commitment blocks (`mustrun`, then `committed`) before any
economic tranche, ascending bid heat rate within a rank, the marginal row taking
the remainder, rows past the fill point carrying **no floor**.

The mandate is the MW the pro-rata path actually **delivers**,
`Σ_g min(floor_frac, basis_g)·pmax_g`, **not** the nominal `floor_frac·Σpmax`.
*(The first cut targeted the nominal figure and the phase-0 census caught it:
the pro-rata path clips every row at its own eligible capacity and drops the
shortfall, so the nominal figure overstates delivered forcing by 20–40 % on the
real ERCOT fleet — 2021: 5.7671 TWh delivered against 7.1171 nominal. Targeting
it would have folded a LEVEL change into an ALLOCATION swap: two mechanisms on
one gate and an unfalsifiable A/B.)*

Rule posture: **19** — no new floor, no membership change, no second mechanism
id; only the level source per row changes, the swap `st_gas_mustrun_level_p25`
already makes. **21** — zero free parameters; block sizes are the frozen binning
artifact's existing tranche capacities, order is the fleet's own bid heat rates.
**2** — vectorized cumulative clip, no loop over hours. **13** — forward-native
(a forecast year has heat rates, a net-load and a tranche structure), so
deliberately NOT in `_BACKCAST_ONLY_OVERLAY_FIELDS`. **1** — it stays a per-row
`min_gen` under the same mech id *precisely so* D-2/D-4 attribution and the C8
forced share stay measurable.

**The alternative that was REFUSED BEFORE BUILD.** One class-level LP constraint
per hour (`Σ_ST_GAS P[g,t] ≥ mandate`, LP picks the units) is the tempting fix
and it would **game the gate**: `run_d2` attributes forced energy from the
per-row `min_gen`/`mechanism` arrays, so a class row carries no mech id, ST_GAS
forced share would report ≈ 0 %, and C8 would PASS **because the diagnostic went
blind, not because the forcing stopped**. A unit test pins the opposite property.

---

## 2. THE DEFECT, MEASURED ON COMMITTED ARTIFACTS (zero LP)

Full record: `docs/handoffs/FINDING-ercot259-c8-allocation-2026-09-08.md`.

`st_netload_drag` is convicted by the D-4 **per-unit conduct rider** of flooring
a plant whose meter reads zero in **every scored year** — 3452 Lake Hubbard in
2021/2022/**2023**, 3491 Handley in 2024/2025 — invisible to the rubric in
2023–25 only because rule 16's escalation fires solely above the 30 % C8 cap.
**The defect is therefore IN-SAMPLE and nothing is identified on 2021**
(rule 22 step 3).

The convicted plant is, five years for five, **that year's least-committed
plant** by CAMPD online fraction. The 2021 error runs **both ways**: the uniform
floor holds Lake Hubbard at **1.22 TWh against 0.36 TWh measured (3.4× OVER)**
while holding V H Braunig, the fleet's workhorse, at **1.50 against 3.72
(0.40× UNDER)** — which is what identifies it as an **allocation** defect rather
than a level one. The drag **curve is exonerated**: 2021 sits inside the 2023–25
spread at every net-load bin, a year it was never fitted on.

---

## 3. PHASE 0 — FOOTPRINT CENSUS (zero LP), AND THE SCREEN YEAR

`run_year(fleet_only=True)` on the keeper's own recipe, both arms, all five
years. "Footprint" = mandated MW **changing hands between plants**.

| year | mandate, uniform | mandate, merit | **aggregate delta** | **footprint** |
|---|---|---|---|---|
| 2021 | 5.7671 TWh | 5.7671 TWh | **0.0000** | 1.1410 TWh |
| 2022 | 7.0023 | 7.0023 | **0.0000** | 1.3075 |
| **2023** | 7.0861 | 7.0861 | **0.0000** | **1.4270** |
| 2024 | 7.0721 | 7.0721 | **0.0000** | 1.1154 |
| 2025 | 5.8192 | 5.8192 | **0.0000** | 0.8056 |

**Aggregate neutrality holds exactly in every year** — the swap is provably
distributional.

### SCREEN YEAR = **2023**

Named **ex ante**, on the mechanism's **own largest footprint** (1.4270 TWh) —
never on the residual. It is also a **training** year, so the screen is
in-sample, and it is a year in which plant 3452 carries a D-4 conduct FAIL.

Per-plant reallocation in 2023 (floor integral TWh / binding hours):

| plant | HR | online % | uniform | merit | delta |
|---|---|---|---|---|---|
| 3612 V H Braunig | 8.49 | 95.4 | 0.9177 / 5,825 | 1.7257 / 5,825 | **+0.8080** |
| 3460 Cedar Bayou | 10.71 | 57.9 | 1.2004 / 5,032 | 1.5066 / 4,932 | +0.3062 |
| 3601 Sim Gideon | 10.90 | 59.1 | 0.5250 / 5,971 | 0.6375 / 4,865 | +0.1125 |
| 3611 O W Sommers | 10.97 | 65.4 | 0.7019 / 5,565 | 0.8008 / 4,069 | +0.0989 |
| **3452 Lake Hubbard** | 11.45 | 42.4 | 0.6994 / 5,017 | **0.3369 / 3,193** | **−0.3625** |
| **3491 Handley** | 12.58 | 48.7 | 1.0055 / 4,918 | **0.4997 / 2,413** | **−0.5058** |
| 3628 R W Miller | 13.02 | 44.5 | 0.3263 / 3,446 | 0.1333 / 1,431 | −0.1930 |
| 34702 W A Parish [ST] | 10.76 | — | 1.1464 / 5,484 | 0.9193 / 5,008 | −0.2271 |
| 56708 CFB Power | 15.83 | — | 0.2877 / 7,011 | 0.1491 / 2,305 | −0.1386 |
| 49392 Barney M Davis [ST] | 10.70 | — | 0.1716 / 2,400 | 0.2263 / 2,386 | +0.0547 |
| 4195 | — | — | 0.1041 / 7,011 | 0.1509 / 3,605 | +0.0468 |

Direction is monotone in cost, as the mechanism's arithmetic requires.

---

## 4. G-DRIFT — the code audit that licenses G-CTRL form 4

`git diff ffc25ece origin/main` over `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/lib`, `data/raw/_validation-source`, `data/raw/reference`: **7 files,
+570/−4**. Classification for an **ERCOT backcast**:

| file | change | verdict | reason |
|---|---|---|---|
| `model/interchange/spec.py` | `MISO_SEAM_LADDER_BY_YEAR`, 4 values ±0.01 | **INERT** | another ISO's branch |
| `runner.py` (+101) | capx D83 bridge-year ledger writer | **INERT** | capacity-evolution path; a `mode="backcast"` run never enters it |
| `config/solve_surface_declared.py` (+2) | two new declared names | **INERT** | cache-key declaration only, no solve behaviour |
| `config/scenarios.py` (+91) | `f923_gas_price_plausibility_screen` (default flipped True) | **INERT** | gate is `gas_plant_monthly_fuel_pricing AND …`; the ERCOT keeper sets that `False`, so the screen never runs |
| `data/fuel/plant_prices.py` (+228) | the same F923 screen | **INERT** | same gate, verified at the call site |
| `config/constants.py` (+32) | `EGRID_CT_HR_PHYSICAL_FLOOR`, `F923_…_BAND` | see below | one is consumed unconditionally |
| `data/fleet/eia860.py` (+114) | `_apply_simple_cycle_hr_floor`, **unconditional** | **see below** | measured, not argued |

**The one hunk that could not be classified by reading.** SPP-49's simple-cycle
heat-rate floor is applied **unconditionally** at the eia860 seam, and it clamps
**4 ERCOT plants — 3612, 55052, 59391, 61643** — including **3612 V H Braunig,
the head of this mechanism's merit order**. ERCOT's tranche heat rates come from
the CAMPD binning artifact (`Plant_Avg_HR_MMBtu_MWh`), not eGRID, so it may not
reach the solve — but that is an argument, and rule 29(b) wants a classification.

It is therefore settled **empirically at zero LP**: the ERCOT 2023 fleet is built
twice at HEAD, once as shipped and once with `_apply_simple_cycle_hr_floor`
no-op'd, and every fleet array the LP consumes is compared
(`pmax`, `pmin`, `heat_rate`, `vom`, `emission_rate`, `nox_rate`, `so2_rate`,
`availability`, `zone_idx`, `fuel_type_idx`, `efficiency_bin`, `plant_code`,
`min_gen`, `unit_ids`).

> **VERDICT: INERT.** Every fleet array is byte-identical between the two builds
> — `pmax`, `pmin`, `heat_rate`, `vom`, `emission_rate`, `nox_rate`, `so2_rate`,
> `availability`, `zone_idx`, `fuel_type_idx`, `efficiency_bin`, `plant_code`,
> `min_gen`, and the 2,320 `unit_ids`. The clamp lands in the eia860 frame but
> ERCOT's tranche heat rates come from the CAMPD binning artifact, so it never
> reaches the solve. The hunk is **provably inert for an ERCOT backcast**, and
> Braunig's position at the head of the merit order is unaffected.

### 4a. AND YET THE SCREEN SPENDS A CONTROL SOLVE ANYWAY — the honest reason

The audit above was taken against `origin/main` at `cbf9be9f`. **`main` has since
advanced 57 commits**, and the same diff now returns **25 files, +1,820/−39**,
including LP-core files this session has not audited — `model/lp/rows.py` (+68),
`model/lp/model.py`, `pipeline/kwargs.py`, `results/cache.py`, `data/hydro.py`,
`model/interchange/{spec,pjm}.py`, `model/capacity_evolution/{ccs,evolve}.py`.

Rule 29(b) permits form 4 only when **every** changed hunk is classified INERT
with its reason cited. Classifying twenty-five files — several of them in the LP
row builder — on argument rather than measurement is exactly the "files changed,
therefore fine" heuristic in reverse, and it is not a classification.

**So the screen is TWO LPs: a 2023 arm and a 2023 control, both at this HEAD**,
and every gate in §5 is read **arm-vs-control**, never arm-vs-keeper. That is
the conservative reading and it costs ~35 minutes; a wrong INERT call would cost
the whole span. The SPP-49 measurement above is retained because it is a real
result and it is the one hunk that could have moved this mechanism's merit order.

**Screen base recipe.** Both arms replay
`results/calibration/ercot256_five_year_keeper` at `--year 2023`, i.e. the
keeper's **forward** config — NOT its 2023 carve-out recipe (`meta.json` only
snapshots the forward config; RESULT-ercot256 §8a). That is deliberate and
harmless for a STOP-only structural screen: **both arms share the same base**, so
the A/B isolates the mechanism, and the pre-solve census in §3 was computed on
the same base. The full span, if the screen clears, reproduces the correct
per-year recipe (legs A–D).

---

## 5. THE SCREEN GATES — STRUCTURAL, STOP-ONLY, AND NEVER READ AGAINST C8

Rule 29: the gate asks whether the mechanism does what its own arithmetic says.
It **may kill the arm; it may never promote one.** None of these is the target
criterion.

| id | gate | STOP condition |
|---|---|---|
| **G1** | **Aggregate neutrality survives the solve.** The class's mandated floor MW per hour is unchanged between arms. | any hour differs by > 0.01 MW |
| **G2** | **The reallocation lands where the pre-solve delta says.** Per-plant drag forced-energy deltas match §3 in **sign** for every plant, and within **±50 %** in magnitude for the five largest movers. | any sign flip, or a top-5 mover outside the band |
| **G3** | **Footprint is confined to what the mechanism claims.** No mechanism other than `st_netload_drag` changes its D-2 forced energy by more than 0.05 TWh. | any other mechanism moves more |
| **G4** | **No non-target load-bearing criterion flips PASS → FAIL**: C1, C2, C3a, C3b, C4. | any PASS → FAIL |
| **G5** | **Feasibility.** Slack and dump stay 0.0000 in both arms. | either non-zero |

**Explicitly NOT gates:** C8 (the target — reading it here would be the
fitted-mechanism selection rule 1 forbids, done one year at a time), C3c, and
the `[7c]` operating-shape report (a standing ERCOT-126 open item, not a rubric
criterion).

---

## 6. PREDICTIONS, REGISTERED BEFORE THE SOLVE

| # | prediction |
|---|---|
| **P1** | 2023 ST_GAS **C8 forced share FALLS** — not because anything is hidden, but because the mandate now lands on units the LP commits anyway, so fewer floored cells actually BIND. Reported, **not gated**. |
| **P2** | Plant **3452's 2023 D-4 conduct row improves**: binding hours fall from 2,869 toward the ~3,193-hour floor-integral footprint, and `measured_zero_share` falls from 0.5936. **Whether it CLEARS is genuinely open** — the fill concentrates 3452 into high-net-load hours, which it was more likely to be running in, but nothing guarantees the remaining hours are non-zero. |
| **P3** | **3612 Braunig's forced energy RISES** (+0.81 TWh of floor integral) and its D-4 row **stays `pass`** (its measured zero-share is 0.0648). |
| **P4** | **3491 Handley and 3628 R W Miller shed forcing** in 2023 (−0.51 / −0.19 TWh of floor integral). |
| **P5** | **System load-weighted LMP FALLS**, by **< $1.00/MWh** — the same mandated MW is carried by cheaper units. |
| **P6** | **ST_GAS class energy moves by < 1.0 TWh** — the mandate is aggregate-neutral, so only the LP's economic response above the floor should move it. |
| **P7** | **No PASS → FAIL on C1/C2/C3a/C3b/C4** (this is G4; registered as a prediction too so a miss is reported rather than absorbed). |

**Reported at full magnitude whatever happens**, including the known weakness
already on the record: Spearman(heat rate, CAMPD online fraction) is
−0.714 / −0.833 / −0.690 in 2021/2023/2024 but only **−0.286 (p = 0.49) in
2025**, where R W Miller — the most expensive plant — ran 88.0 % of hours. Cost
order is right in three of four years and materially wrong in one. It is not
tuned around.

---

## 7. WHAT HAPPENS AFTER THE SCREEN

* **Screen clears every STOP gate ⇒** the full span is solved as ONE invocation,
  `--year 2021 2022 2023 2024 2025`, ONE bundle (rules 16 / 30), reproducing the
  keeper's per-year recipe (RESULT-ercot256 §8a legs A–D). 2021/2022 are
  validation-tier and need `--holdout-authorized`; ERCOT holds `complete` and
  the freeze covers the locked test only.
* **Screen fails any STOP gate ⇒** that is the session's result. The remaining
  years are **not** spent, and the arm is reported as killed.
* The screen bundle is a **throwaway diagnostic probe**: never registered, never
  a keeper, never quoted as a keeper number, and its year is re-solved inside the
  full bundle. Under rule 31 `[R-RETAIN]` it is **gitignored, not deleted**, and
  it stays on local disk until the owner rules on promotion.

---

*Generated by [Claude Code](https://claude.ai/code)*
