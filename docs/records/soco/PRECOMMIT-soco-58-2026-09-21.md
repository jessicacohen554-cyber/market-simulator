# PRECOMMIT — SOCO-58 (2026-09-21): the model charges a $100/MW cold start to a boiler its own dispatch holds hot in 100 % of the hours

**Lane** SOCO-58 · **DATA PROFILE** soco · **Model** Opus 5 (rule 27 `[R-PUSH]` — scope writes
`scripts/`).
**Control of record** `2026-09-20-soco57-measured-cc-heat`
(`results/calibration/soco57_measured_cc_hr`), rule 29 `[R-SCREEN]` (b) **form 4**, no control solve.
**Arm** `coal_warm_committed = True` — ONE existing default-off `ScenarioConfig` field
(`scenarios.py:12202`), **zero new fields, zero new artifacts, zero free parameters.**

**Pushed BEFORE any LP is solved.** Every number below is read off the keeper's own committed
hourlies, its committed floor sidecars, and `fleet_only` rebuilds off its own recipe.
**Parent LP cost: ZERO** (rule 32 `[R-SHARD]` (a)).

---

## 1. THE OBJECT, AND WHAT PHASE 0 FOUND

SOCO-57 named this lane's object: 2024 `COAL_PRB` is **−5.781 TWh** short of its actual (−2.4 pp)
and **C4 2024 coal FAILS** at NRMSE 0.309 / r 0.829 against a ≤0.30, ≥0.70 gate, while 2023
(0.258 / 0.882) and 2025 (0.167 / 0.882) both pass.

> **The model charges SOCO's coal fleet a `$100/MW` COLD START — amortized to EXACTLY
> `$100.00/MWh` at four of six plants in 2024 — on a boiler that its own dispatch holds at full
> must-run output in `100.0 %` of the hours the charge applies. The `_committed` tranche is priced
> `$140–177/MWh` into a `$28.27/MWh` market, so `19.8 TWh` of available coal capacity cannot clear,
> and the model's cheap base band has become its dearest band.**

The mechanism is `model/commitment.py::compute_monthly_markup`, and **the code's own comment names
this exact pathology**, in the branch that is default-off here:

> *"Warm-boiler exemption: a CAMPD coal bin with a must-run floor never goes fully dark — its
> `_mustrun` tranche keeps the boiler online — so dispatching the `_committed` tranche is an output
> ramp on a hot unit, not a cold start. **Without this the $100/MW coal start amortized over P0 run
> lengths prices the committed band ABOVE the econ ramp top** (Parish 2024: committed cleared only
> at LMP >= ~$20 vs econ from ~$13 — the run-97b inversion), **turning the design's cheap base band
> into a near-peak band.**"*

### 1.1 The markup, measured on the keeper's own scored solve

Reconstructed as `mc(P1) − mc_base` (the markup is added at the P0→P1 seam, so it is absent from
`mc_base` and invisible on every fleet grain):

| plant | name | class | `mc_base` 2024 | **P1 bid** | **markup** | avail TWh | gen TWh |
|---|---|---|---|---|---|---|---|
| 26 | Gaston | COAL_BIT | 76.958 | **176.958** | **+100.000** | 0.111 | **0.000** |
| 703 | Scherer | COAL_BIT | 57.585 | **157.585** | **+100.000** | 5.147 | **0.000** |
| 6073 | Daniel | COAL_PRB | 41.900 | **141.900** | **+100.000** | 0.135 | **0.000** |
| 6257 | Bowen | COAL_PRB | 40.042 | **140.042** | **+100.000** | 5.597 | **0.000** |
| 3 | Barry | COAL_BIT | 31.056 | 44.812 | +13.756 | 0.200 | 0.002 |
| 6002 | Miller | COAL_PRB | 26.936 | 35.283 | +8.347 | 9.537 | 0.907 |

**20.73 TWh of committed coal capacity, producing 0.909 TWh.** Median system clearing price 2024:
**$28.27/MWh**.

### 1.2 The physics predicate, measured at 100.0 % in ALL EIGHTEEN plant-years

Hours in which a plant's `_committed` tranche carries capacity, and its `_mustrun` tranche is
generating, at what load fraction:

| year | p3 | p26 | p703 | p6002 | p6073 | p6257 |
|---|---|---|---|---|---|---|
| 2023 | 8760/8760 | 2976/2976 | 8760/8760 | 8760/8760 | 5376/5376 | 8232/8232 |
| 2024 | 8760/8760 | 2832/2832 | 8760/8760 | 8760/8760 | 6240/6240 | 8760/8760 |
| 2025 | 8760/8760 | 4008/4008 | 8736/8736 | 8760/8760 | 6456/6456 | 8760/8760 |

**100.0 % in every one, at must-run load fraction 1.00 in every one.** The boiler is never dark when
the committed band could be dispatched. **A cold start is being charged to a unit the model itself
never cools.** This is rule 17 `[R-FLOOR-WINDOW]` read against a bid rather than a floor: the charge
binds in exactly the hours its own driver evidence says the unit is online.

### 1.3 WHY 2024 IS DIFFERENT — a P0 feedback, not an input

`markup = $100/MW ÷ max(avg P0 run length, 1.0 h)`. Inverting it gives each tranche's own P0 run
length:

| year | p3 | p26 | p703 | p6002 | p6073 | p6257 |
|---|---|---|---|---|---|---|
| 2023 | 0.8 h | 0.8 h | 1.0 h | 17.5 h | 1.0 h | 1.0 h |
| 2024 | 7.3 h | 1.0 h | 1.0 h | 12.0 h | 1.0 h | 1.0 h |
| **2025** | **137.0 h** | 0.8 h | **7.9 h** | **769.2 h** | **10.4 h** | **11.4 h** |

At Miller (6002), the fleet's largest coal plant:

| year | price p50 | de-markup `mc` | margin | markup | bid | at p50 |
|---|---|---|---|---|---|---|
| 2023 | $32.10 | $27.95 | +$4.15 | $5.72 | $33.67 | **OUT** |
| **2024** | **$28.27** | **$26.94** | **+$1.33** | **$8.35** | **$35.29** | **OUT** |
| 2025 | $39.57 | $28.01 | +$11.56 | **$0.13** | $28.14 | **IN** |

**The markup is anti-correlated with the year's need for coal.** In 2025 a high gas price lets the
committed tranche run in P0 → long runs → the markup collapses to $0.13 → it clears in P1. In 2024 a
low gas price keeps it out of P0 → zero runs → the markup saturates at $100.00 → it is guaranteed
out of P1. **This is a self-reinforcing lockout that bites hardest in the lowest-price year**, and it
is the mirror image of the v2 circularity `_amortized`'s own docstring records being removed for
fast starts (*"too-cheap offers → long P0 blocks → ≈0 markup → the lever self-disables"*). Coal
carries no `fast_start_run_hours` basis, so coal still runs on v2 — in the direction that
self-REINFORCES.

**2024 is not a year with a different input. It is the year the feedback closed hardest.**

---

## 2. THE HANDOFF'S THREE READINGS, ADJUDICATED ON MEASUREMENT BEFORE ANY LP

### (1) COAL AVAILABILITY / OUTAGES IN 2024 — **REFUSED. It moves the wrong way across years.**

The handoff required the SOCO-56 contradiction test re-run on the current keeper, after the per-unit
crosswalk landed. Done, coal-scoped — hours in which the model's ceiling sits BELOW the plant's own
measured CAMPD output:

| year | fleet TWh forbidden | largest plant | availability TWh | generation TWh | util |
|---|---|---|---|---|---|
| 2023 | 1.295 | 6002 Miller 0.899 | 57.377 | 31.488 | 0.549 |
| **2024** | **2.059** | 6002 Miller 1.224 | 60.566 | 30.478 | 0.503 |
| 2025 | **2.758** | 6002 Miller **1.862** | 60.288 | 46.215 | **0.767** |

**2025 carries the MOST forbidden energy and the LEAST shortfall** — it is the year coal runs
+3.251 TWh OVER. The residue is the CAMPD-gross vs model-net-summer wedge SOCO-56 §3 already
identified as the fleet-wide baseline, and it cannot explain a 2024-specific miss because it is not
2024-specific. **Coal availability is essentially FLAT at 57–61 TWh across all three years while
generation swings 30.5 → 46.2 TWh. Availability is not what changed.** REFUSED, zero LP spent.

### (2) COAL OFFER LEVEL — the handoff's two named instruments stay REFUSED ON SIGN; this lane's object is a **different** offer-level defect

`coal_takeorpay_SOCO.csv` (absent) and `derive_parasitic_load.py` (never run for SOCO) both make
coal MORE expensive, which is the wrong sign for a short `COAL_PRB` — SOCO-56 §2(c) already refused
them on exactly that ground and nothing here re-opens it. **This lane's object is not a fuel cost at
all: it is a fabricated cold-start premium**, and removing it is a repair rather than a level tune.
Stated plainly so no successor conflates the two.

### (3) THE 2025 HYDRO INPUT HOLE — **MEASURED, ROUTED, and NOT armed here (rule 19 `[R-ONE-MECH]`)**

0.327 TWh modelled against 6.012 measured. Phase 0 confirms coal backfills it and adds the number
the handoff did not have: **correcting hydro would push 2025 coal DOWN by up to ~5.7 TWh, which is
the direction that would absorb this arm's 2025 overshoot.** Arming both in one lane would confound
two mechanisms on one phenomenon. **It is this lane's named successor for 2025** and is routed, not
taken.

---

## 3. THE LEVER, AND ITS SCOPE — MACHINE-VERIFIED BEFORE THE SOLVE

`coal_warm_committed = True`, ridden through the generic `prb_overrides` channel:
`scripts/replay_keeper.py results/calibration/soco57_measured_cc_hr --years <Y> --out-dir …
--set coal_warm_committed=true`.

### 3.1 Scope is EXACT — the moved set is precisely the set that pays

The exemption's predicate is `fuel_type == "coal" and must_run_pct > 0`. Measured over the 2024
fleet (327 rows):

| | count |
|---|---|
| coal tranches carrying `startup_cost_per_mw > 0` | **6** (all `_committed`, 3,464.0 MW) |
| of those, exempted by the arm | **6** |
| coal tranches carrying a markup the arm does **NOT** exempt | **0** |
| **non**-coal tranches touched by the arm | **0** |

Zero collateral scope, in both directions.

### 3.2 Rule 19 `[R-ONE-MECH]` AT THE RIGHT GRAIN — and the inverse of SOCO-57's trap

SOCO-57 §4's lasting warning is that *"max|Δ| == 0 is indistinguishable from inert unless something
asserts the resolved value."* **This mechanism reads EXACTLY ZERO on every fleet grain BY
CONSTRUCTION, and that is the CORRECT signature** — it lives entirely at the P0→P1 seam and must not
touch the fleet. Measured, arm vs control, 2024:

| `fuel_prices` | `mc_base` | `pmax` | `availability` | `heat_rate` |
|---|---|---|---|---|
| **0.000000000000** · 0 rows | **0.000000000000** · 0 | **0.000000000000** · 0 | **0.000000000000** · 0 | **0.000000000000** · 0 |

…**while the RESOLVED `scenario_config.coal_warm_committed` reads `False` → `True`.** That assertion
is the whole of the plumbing proof and it is already discharged pre-solve. HARD STOP 3 re-asserts it
on the solved `run_config.json`.

**P0 is byte-identical**, because P0 solves on `mc_base` and `mc_base` does not move. So the
displaced classes' own P0 run lengths — and therefore their own markups — are unchanged: the
mechanism is exactly these six rows' markup and provably nothing else. **One seam, one call site**
(`pipeline/solve.py:518`), not the four the measured-heat-rate family needs.

### 3.3 Rules 21 / 24 / 25 — zero free parameters, zero key moves elsewhere, nothing transferred

`coal_warm_committed` is a registered `ScenarioConfig` boolean, already in the cache key (it is NOT
in `_CACHE_KEY_OPTIONAL_FIELDS`), so arming it re-keys **SOCO's configs only** and no other ISO's key
moves. `build_dof_ledger` already classifies it `measured-physical` with **`n_scalars=0`**. MISO's
keeper arms it; under rule 25 `[R-ISO-SCOPE]` / rule 28 (d) that transfers **nothing**, and every
number in this document is SOCO's own.

**A rule-25 defect in the published record was found in phase 0 and is repaired in this commit.**
`build_dof_ledger.py`'s entry hardcoded MISO's dispatch forensics as the identification source for
*every* ISO, so SOCO arming the gate would have published MISO's evidence as SOCO's. The source is
now per-ISO (`_COAL_WARM_COMMITTED_SOURCE`), SOCO's cites §1.2/§1.3 above, and an unlisted ISO gets
an explicit "NOT IDENTIFIED FOR THIS ISO" rather than someone else's evidence. Not solve-affecting.

---

## 4. RULE 28 `[R-MECH-MATRIX]` (a) — THE GOVERNANCE READING, STATED BEFORE THE SOLVE

`coal_warm_committed` is **not a matrix row**. The base matrix registers it *literally inside* the
`tranche_startup_amortization` row's `def`, as a sub-scalar of that family (rule 28 (c), xiso-3
census). **SOCO's `tranche_startup_amortization` cell is `G` — GOVERNANCE-REFUSED EX ANTE, NO REOPEN
CONDITION** (SOCO-53). This lane must say exactly what it is doing with that cell.

**The `G` verdict's own reasoning:** the mechanism *"is a bid markup only … so its whole effect is to
put start costs INTO THE CLEARING PRICE. SOCO HAS NO CLEARING PRICE … Arming a market-design pricing
rule on a footprint with no market is rule 1 `[R-STRUCT]` verbatim."*

**THE TWO GATES IN THAT FAMILY HAVE OPPOSITE POLARITY, and that is the whole point:**

- `gas_st_startup_cost` **off ⇒ NO markup** (ST_GAS is skipped). SOCO measures its ST_GAS committed
  markup at **exactly −0.000**, confirming the family is genuinely off there.
- `coal_warm_committed` **off ⇒ markup APPLIED.** SOCO measures its coal committed markup at
  **+$100.00**.

**So arming `coal_warm_committed` does not RE-OPEN the `G` cell — it ENFORCES it.** SOCO-53's own
note reasoned "with `tranche_startup_amortization` off the CT_PEAKER econ and peak tranches carry
ZERO start cost", and this lane's measurement corrects a factual premise in it: **the family is not
off for SOCO's coal (or for CT_PEAKER's committed tranche, at +$20.00 on ten plants). It is on by
default, and there is no master gate that turns it off.** A footprint with no clearing price was
carrying $140–177/MWh start-cost bids, which is precisely the thing `G` refuses.

**This lane therefore does NOT flip the cell.** `tranche_startup_amortization` stays **`G`** for
SOCO; what changes is its `ev`, which will record (i) the measurement that the family's coal limb was
default-ON, and (ii) that the warm-boiler exemption was armed as the enforcement of that same `G`.
**This is an ambiguous governance boundary and it is surfaced to the owner in the RESULT rather than
settled by this lane.**

**Deliberately NOT extended to CT_PEAKER.** Ten CT plants carry a +$20.00/MWh committed markup on
implied 1.0 h P0 runs — the same arithmetic. It is **not** taken, for two independent reasons:
`CT_PEAKER` is already **+2.97 TWh OVER** in 2024 so the direction is wrong, and — the reason that
actually binds — **a combustion turbine with no must-run floor genuinely does cold-start**, so no
warm-boiler argument exists for it. Recorded so the scoping reads as physics, not as convenience.

**No cell adjudicated `R`/`I`/`G` is re-tested.** `gas_commitment_bridge` `R`,
`coal_prb_proxy_own_iso` `I`, and the `K` cells (`gas_plant_monthly_pricing`,
`gas_basis_measured_by_year`, `campd_per_unit_attribution`, `measured_cc_heat_rates`) all stand
untouched.

---

## 5. CHECK A — THE DISTANCE, IN $/MWh AND TWh-IN-REACH

The object is **5.781 TWh** (2024 `COAL_PRB`). Committed-tranche headroom that the de-marked-up offer
puts in merit against the hour's own load-weighted clearing price:

| year | reach TWh | of which Miller (6002) | committed gen today |
|---|---|---|---|
| 2023 | 3.342 | 3.323 | 3.290 |
| **2024** | **4.606** | **4.513** | 0.909 |
| 2025 | 4.187 | 0.001 | 10.469 |

**4.606 of 5.781 TWh = 80 % of the object is in reach.** This is the first SOCO lever in five lanes
that can substantially cross its own distance — SOCO-54 §2(b) measured 1 %, SOCO-56 §2(b) needed
~$5/MWh of merit-order movement it could not buy. **Stated ex ante: it does not cross the whole
distance, and the row is not predicted to close.**

The greedy zero-LP re-stack (floors respected, tranche-grain deltas, an upper bound that
SOCO-57 §6 measured as systematically UNDERSTATING the move because it cannot model re-commitment):

| class | 2023 | 2024 | 2025 | direction vs its own C1 gap |
|---|---|---|---|---|
| **COAL** | **+2.965** | **+2.986** | **+3.253** | 2023/2024 **RIGHT**, 2025 **WRONG** |
| `CC_REGULAR` | −0.722 | −0.682 | −0.817 | **RIGHT** (over in all 3) |
| `CT_PEAKER` | −1.712 | −1.709 | −1.846 | **RIGHT** (over in all 3) |
| `ST_GAS` | −0.511 | −0.586 | −0.585 | **WRONG** (short in all 3) |
| nuclear, hydro, solar, wind, CHP | 0.000 | 0.000 | 0.000 | — |

**Three of four fossil classes move toward their actuals in 2023 and 2024.** `ST_GAS` is the one that
moves away, and its cause is separately known and untouched here: SOCO-54 §4 measured a
**$1.0–1.7/MMBtu** delivered-fuel separation between SOCO's gas steam and its CTs (the unmodelled
within-footprint gas dispersion, SOCO-12 §4). Coal correctly under-cutting an over-priced steam fleet
does not create that defect; it exposes it.

---

## 6. CHECK D — EVERY SCORED CRITERION'S MARGIN, NOT C1's

*SOCO-57's own biggest process miss was enumerating C1 only while the row it broke was C4.*
Full ledger, from the committed scorer on the keeper's own artifacts:

| criterion | year | key | value | **margin to gate** |
|---|---|---|---|---|
| **C4** | **2024** | **coal** | r 0.829 / NRMSE **0.309** | **ALREADY FAILING by 0.009** ← the target |
| **C1** | **2023** | **`ST_GAS`** | −6.47 TWh / **−2.71 pp** | **0.71 TWh / 0.29 pp** ← thinnest passing |
| **C4** | **2023** | **coal** | r 0.882 / NRMSE 0.258 | **0.042** of NRMSE |
| C1 | 2023 | `CC_REGULAR` | +6.28 / +2.48 pp | 0.90 TWh / 0.52 pp |
| C1 | 2023 | `CT_PEAKER` | +5.97 / +2.48 pp | 1.21 TWh / 0.52 pp |
| C1 | 2024 | `COAL_PRB` | −5.78 / −2.36 pp | 1.69 TWh / 0.64 pp |
| C1 | 2024 | `ST_GAS` | −5.75 / −2.31 pp | 1.72 TWh / 0.69 pp |
| **C4** | **2025** | **coal** | r 0.882 / NRMSE 0.167 | 0.133 of NRMSE |
| C1 | 2024 | `CT_PEAKER` | +2.97 / +1.18 pp | 4.50 TWh / 1.82 pp |
| C1 | 2023 | `COAL_PRB` | −2.33 / −1.00 pp | 4.85 TWh / 2.00 pp |
| C1 | 2024 | `COAL_BIT` | −0.71 / −0.31 pp | 6.75 TWh / 2.69 pp |
| C1 | 2023 | `COAL_BIT` | −1.24 / −0.53 pp | 5.94 TWh / 2.47 pp |
| C4 | 2023/24/25 | gas | NRMSE 0.102 / 0.132 / 0.088 | 0.198 / 0.168 / 0.212 |
| C2 | 2023, 2024 | gas, coal | PASS (rolls up C1) | — |
| C8 | all | all | `ST_GAS` 0.130/0.130/0.147 | 0.170 / 0.170 / 0.153 vs the 0.30 cap |
| C1 | 2025 | every class | **SKIPPED** (preliminary 923 vintage) | ungated |
| C2 | 2025 | coal | **SKIPPED** — +13.8 % diagnostic | ungated, **reported** |

**THE ROW MOST AT RISK OF BECOMING A NEW FAILURE IS 2023 `ST_GAS`**, at 0.29 pp and 0.71 TWh of
margin, in the direction the arm pushes. At the 1× greedy bound it lands at −2.92 pp (margin
**0.076 pp**); at 2× it lands at −3.14 pp and **FAILS both legs**. That is pre-registered as P4, and
it is named here rather than discovered afterwards.

### 6.1 Why C4 2024 coal is a LEVEL failure wearing a shape gate's clothes

`NRMSE = RMSE / mean(actual)`. Decomposing each coal year against its own EIA-930 hourly series:

| year | model TWh | bench TWh | bias | **bias / mean** | **shape residual** | NRMSE |
|---|---|---|---|---|---|---|
| 2023 | 31.49 | 38.25 | −772 MW | 0.177 | **0.188** | 0.258 |
| **2024** | **30.48** | **40.45** | **−1,135 MW** | **0.246** | **0.186** | **0.309** |
| 2025 | 46.22 | 44.08 | +244 MW | 0.049 | **0.160** | 0.167 |

**The shape residual is nearly identical in all three years (0.188 / 0.186 / 0.160). What differs is
the LEVEL BIAS.** 2024 coal does not fail C4 because its shape is worse than 2025's — it fails
because the model is 9.97 TWh (−24.6 %) short of the series it is scored against. **Adding coal
volume is the direct repair for the failing criterion, and the decomposition says by how much.**

---

## 7. PREDICTIONS — EX ANTE, WITH FALSIFIERS AND MAGNITUDES, BANDS WIDENED ~2×

Per SOCO-57 §6: the greedy re-stack understated all three of its misses, so every band below spans
roughly **[1×, 2.5×] of the greedy bound**, and direction is refused where the bound cannot see it.

| # | prediction | falsifier |
|---|---|---|
| **P1** | **C4 2024 coal FLIPS to PASS. NRMSE 0.309 → `0.20 … 0.28` (point 0.25); r `0.83 … 0.90`** | NRMSE > 0.30, or r < 0.70 |
| **P2** | 2024 `COAL_PRB` improves to `−4.0 … +0.5 TWh` (point −2.7) and `−1.6 … +0.2 pp`; **stays PASS** | outside the band, or FAILS |
| **P3** | 2024 `CC_REGULAR` improves but **STILL FAILS BOTH LEGS**: `+9.0 … +10.6 TWh`, `+3.5 … +4.05 pp` | passes, or worsens past +11.05 |
| **P4** | **2023 `ST_GAS` is the row at risk: `−6.8 … −7.6 TWh`, `−2.85 … −3.19 pp`. IT MAY CROSS TO FAIL — this lane puts that at ~40 % and does not predict which way** | lands outside the band |
| **P5** | 2023 C4 coal **IMPROVES**: NRMSE 0.258 → `0.19 … 0.245` | worsens, or > 0.30 |
| **P6** | 2025 C4 coal **WORSENS but PASSES**: NRMSE 0.167 → `0.19 … 0.28` | > 0.30 (FAIL) |
| **P7** | 2023 `CC_REGULAR` `+4.4 … +5.7 TWh` and `CT_PEAKER` `+2.0 … +4.4 TWh` — both **improve**, both stay PASS | either worsens or fails |
| **P8** | 2024 `CT_PEAKER` improves to `−0.9 … +1.6 TWh`; stays PASS | outside the band |
| **P9** | 2024 `ST_GAS` worsens to `−6.2 … −7.1 TWh` / `−2.5 … −2.85 pp`; **stays PASS** | FAILS |
| **P10** | per-plant coal misallocation Σ\|model−actual\| **FALLS**: 2023 `7.444 → 4.0 … 5.6`, 2024 `13.316 → 8.0 … 10.9`. **2025 direction REFUSED** (Bowen overshoots as Scherer improves) | either 2023 or 2024 rises |
| **P11** | D-1 2024 `COAL_PRB` off-peak `cv_ratio` **RISES** from 0.448 (the model's coal is too flat); band `0.50 … 0.80`, may flip to pass | falls below 0.448 |
| **P12** | **rule 19: EXACTLY 0.000000000000 on all five fleet grains, all three years, zero rows moved**; resolved `coal_warm_committed == true` in all three `run_config.json` | any non-zero grain, or a false resolved value |
| **P13** | C8 PASS in all years; `ST_GAS` forced share rises to `0.14 … 0.20` (its denominator falls) — far under the 0.30 cap. **No COAL row appears in D-2** (the mustrun tranche is offer-curve design, not a floor mechanism), so coal adds no C8 row | C8 fails, or a COAL D-2 row appears |
| **P14** | DOF **6 → 7 entries**, residual **1 unchanged**; the new entry is `coal_warm_committed`, `measured-physical`, **`n_scalars=0`**, citing SOCO's own §1.2/§1.3 measurement | any entry with `n_scalars > 0`, or a MISO citation |
| **P15** | no peer ISO moves: `moved_rows("SOCO") == {}` and no non-SOCO committed run config re-keys | any peer key moves |
| **P16** | 2025 `COAL_PRB`/`COAL_BIT` rise further above their actuals; **both remain SKIPPED/ungated**. C2 2025 coal diagnostic worsens `+13.8 % → +16 … +25 %`, **reported not gated** | either becomes gated, or C2 2025 fails |
| **P17** | **determination stays `NOT-YET`** (2024 `CC_REGULAR` still fails). `grade_summary` fails **2 → 1** if P1 holds and P4 does not cross; **2 → 2** if both | `CALIBRATED` anything, or fails > 2 |
| **P18** | rule 17 `[R-FLOOR-WINDOW]` holds in all 18 coal plant-years — **the arm touches no floor**, so every `min_gen` row is unchanged | any floor row moves |
| **P19** | **P0 is byte-identical to the control**; only P1 bids change | P0 dispatch differs |

**The single most likely way this lane is wrong:** the LP re-commits far more than the greedy bound
can see, coal overshoots, and 2023 `ST_GAS` (P4) plus 2025 C4 coal (P6) both cross — trading one
failing criterion for two. That is the honest downside and it is written here, not in a footnote.

---

## 8. RULE 1 `[R-STRUCT]` / RULE 14 `[R-ACCURATE]` — WHY THIS IS KEPT WHATEVER THE RESIDUAL DOES

**The cost being removed is fictitious, and that is not a judgement call.** A $100/MW cold start is
being charged to a boiler that the model's own dispatch holds at must-run load fraction 1.00 in
**100.0 % of the eighteen plant-years' relevant hours**. Its magnitude is not a physical quantity
either: it is `$100 ÷ max(avg P0 run, 1.0)`, which saturates at exactly $100.00/MWh when a tranche
has zero P0 runs, and collapses to $0.13 when it has many — **anti-correlated with the year's need
for coal**.

Rule 1's test is whether the *mechanism* mirrors the real market. A vertically-integrated,
cost-based utility does not decline to raise output on an already-synchronised boiler because of a
start cost it is not incurring. Rule 14's test is whether the accurate representation is preferred
even when the fit worsens — and here the honest statement is the reverse of the last three lanes:
**this repair is expected to IMPROVE the failing criterion, which is itself a reason for care.**
SOCO-55, -56 and -57 were all promoted on runs whose residual got worse because the input was right.
A lever that improves the fit must clear the same bar, and the bar it clears is §1.2's
100.0 % predicate and §1.3's demonstration that the markup's year-to-year variation is an artifact of
the P0 feedback rather than of any driver. **If the only argument for this arm were that C4 2024 coal
flips, it would not be taken.**

---

## 9. THE SOLVE — THREE SHARDS, ONE YEAR EACH (rule 36 `[R-YEAR-ISOLATION]` (a))

Parent LP cost **ZERO** (rule 32 (a)). Each shard: pinned 40-char SHA, its own `--out-dir`, its own
branch, **pushes its full 16-file bundle** including `dispatch/<y>_P1.parquet` and the bundle-root
`system.parquet` (rule 34 `[R-SHARD-PROMOTABLE]` (a)).

```
scripts/replay_keeper.py results/calibration/soco57_measured_cc_hr \
  --years <Y> --out-dir results/calibration/soco58_arm_<Y> \
  --set coal_warm_committed=true \
  --note "SOCO-58 ARM <Y>: coal_warm_committed=true (warm-boiler committed-band
          exemption; removes the $100/MW cold-start markup from the six coal
          _committed tranches whose mustrun tranche holds the boiler online in
          100.0% of hours), year-isolated (rule 36)"
```

Five hard stops, per the handoff: pinned SHA · the dependency assert · the config signature read back
from `run_config.json["scenario_config"]` **AFTER** the solve (all four inherited deltas **plus**
`measured_cc_heat_rates == true` **plus** `coal_warm_committed == true`, with the resolved
`coal_prb_sigmoid_overrides` still `null`) · block in the foreground · pass `--note`.

**The parent repairs `results/calibration/_shared/SOCO/` after composition**
(`run_calibration_full.py --iso SOCO --rebuild-benchmark <composite>`), since it is gitignored and a
sibling of every shard's out-dir.

**Retrievability (rule 34 (e)):** the control's own per-plant layer was recovered at **zero LP for
the fourth consecutive lane** — `git fetch origin <40-char-sha>` on the SOCO-57 leg SHAs returned 16
files each, and **all twelve committed hourly sidecars verified byte-identical** to the registered
keeper. The retention window remains undocumented, so this is not a durability claim (rule 33 (d)).

---

## 10. WHAT THIS LANE DOES NOT TOUCH

Inherited from SOCO-57 §9 and left open, with this lane's additions marked:

1. The over-dispatched CC tail (Tenaska Lindsay Hill 2.060×, Central Alabama, Ratcliffe, E B Harris).
2. The two boundary-refused CC plants (533 McWilliams, 7946 Wansley U9).
3. The `ST_GAS` denominator (`unit_outage_extract_basis_share`), bounded ≤ 0.0071 TWh.
4. The tranche half of `campd_per_unit_attribution` — still a live landmine.
5. Barry unit 4's fleet row (EIA-860 `BIT`, CAMPD Pipeline Natural Gas). **NEW: phase 0 measures
   Barry's coal at 3.48× (2024) and 5.67× (2025) its own actual — the largest per-plant coal
   over-run in the fleet, and the arm does not touch it.**
6. `derive_parasitic_load.py` for SOCO's coal and gas-steam classes.
7. **SOCO-53b, the 2025 hydro hole — NOW THE NAMED SUCCESSOR** (§2(3)), with its interaction measured.
8. The within-footprint gas dispersion (SOCO-12 §4) — **the named cause of the `ST_GAS` shortfall
   this arm slightly deepens.**
9. **NEW: Scherer (703) and Gaston (26) do not move even after the exemption** — their de-marked-up
   committed bids are $57.58 and $57.54 against a $28.27 price, because Scherer's delivered coal is
   $5.10/MMBtu against Miller's $2.10. A per-plant coal fuel-price question, untouched here.
10. **NEW: CT_PEAKER's committed tranche carries the same +$20.00/MWh 1-hour-run markup at ten
    plants.** Not taken — see §4.
