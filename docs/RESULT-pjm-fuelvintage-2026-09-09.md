# RESULT — PJM: the measured monthly gas LEVEL + the 2019-2022 retiree window

**Session:** `pjm-fuelvintage-1` · **Date:** 2026-09-09 · **Branch:** `claude/pjm-fuelvintage-1`
**PRECOMMIT (registered before any LP):** `docs/PRECOMMIT-pjm-fuelvintage-2026-09-09.md`
**Keeper / control (G-CTRL form 4, IMPAIRED — see PRECOMMIT (a)):** `pjm_debugb_inputclock_A`
= run `2026-08-15-pjm-162-inputclock`.

> **Owner ruling §A7 (2026-09-09), verbatim: _"these should be promoted as keepers on both 860 and gas
> shape counts regardless of inertness."_** This session promotes; it does not decide. Every number
> below is reported at full magnitude, misses included, and **none of it gates the promotion**.

---

## 1. HEADLINE — the phase-0 census, and why it changes the expected value of this promotion

**The F923 per-plant print path owns 51.794 % of PJM's gas capacity-hours in 2023 — not ~100 %.**

§A2 named that print path as *"THE MOST LIKELY WAY THIS ARM COMES BACK INERT"*, and MISO's own matrix
cell records **100 %** print ownership. **PJM is not that case.** Measured through the real path
(`run_year(..., fleet_only=True)` off the keeper's `meta.json` → `apply_plant_monthly_fuel_prices` →
its returned `(n_gen, T)` written-cell mask, gas rows only, `pmax`-weighted):

| PJM 2023 | |
|---|---|
| generators in the LP | 3,789 |
| gas rows / gas capacity | **1,744 / 100,451.1 MW** |
| **print-path-owned share of gas capacity-hours** | **51.794 %** |
| print-path-owned share of cells, unweighted | 49.871 % |
| rows owned in all 8,760 h | 780 (47,285.5 MW) |
| **rows the print path NEVER touches** | **844 (46,825.4 MW — 46.6 % of gas capacity)** |
| rows partially owned | 120 |

**So ~48 % of PJM's gas fleet prices off this seam directly.** The promotion is worth materially more
in PJM than the inert case §A2 feared.

---

## 2. THE INPUT-SIDE SCREEN GATES — measured at **ZERO LP COST**, all three PASS

Rule 29 `[R-SCREEN]` clause (0): an arm with a computable pre-solve gate does not reach a solve until
that gate passes. G-1, G-2 and G-3 are properties of the fuel arrays, not of dispatch, so all three
were computed without solving anything — arm vs control built through the identical
`run_year(..., fleet_only=True)` path, the arm armed through the same `prb_overrides` channel
`replay_keeper --set` uses.

| gate | claim | measured | verdict |
|---|---|---|---|
| **G-1** | the delivered gas array moves in the direction and order of magnitude the pre-solve arithmetic implies | capacity-weighted gas array **3.0827 → 2.7105 $/MMBtu**, **Δ −0.3721**; **DOWN in 12 of 12 months** (−0.144 to −0.660); 964 of 1,744 gas rows move, **53,165.6 of 100,451.1 MW** | **PASS** |
| **G-2** | confinement — non-gas fuel prices move **exactly** 0.0 | **max \|Δ\| = 0.0** over all **2,045** non-gas rows; **0** rows moved | **PASS** |
| **G-3** | rule 19 `[R-ONE-MECH]` — the armed level **REPLACED** the F923 receipt level, never blended | armed ISO `_gas_series` monthly means vs `iso_electric_power_monthly_level('PJM', 2023)`: **max \|Δ\| = 0.0000000000**, **12/12 months exactly equal** | **PASS** |

### 2a. An identity that falls out, and independently confirms both the census and the seam

The seam moves the **ISO series** by its full amount; the per-plant print path then overwrites the
share the census measured. So the **generator array** should move by the ISO delta scaled by the
*un*-owned share — a prediction with no free parameter:

| quantity | value |
|---|---|
| ISO `_gas_series` annual, control → arm | 3.2649 → 2.4903 |
| **ISO series annual Δ** | **−0.7746** $/MMBtu *(FINDING §3 predicts −0.770 — agreement 0.005)* |
| census: share the print path owns | 0.51794 |
| **predicted generator-array Δ** = −0.7746 × (1 − 0.51794) | **−0.3734** |
| **measured generator-array Δ** | **−0.3721** |
| **agreement** | **0.0013 $/MMBtu (0.3 %)** |

The census fraction predicts the realized array move to three decimal places. That is strong
structural evidence that the seam does exactly what its docstring says and that the census is
measuring the right mask — obtained without a single LP solve.

### 2b. What the census does to the coal prediction (registered in the PRECOMMIT before the solve)

The seam reaches PJM's dispatch by two channels that push **opposite ways on coal**:

1. **DIRECT** (per-generator gas price, ~48 % reachable): cheaper gas ⇒ gas CC moves down the stack ⇒
   **coal DOWN**, prices down.
2. **INDIRECT** (the ISO `_gas_series` keys the **coal PRB passthrough sigmoid**, armed in the keeper):
   a lower gas series ⇒ lower coal passthrough ⇒ coal offers fall ⇒ **coal UP**.

The handoff and FINDING §5b predict **coal UP** — channel 2 dominating, which is coherent only if
channel 1 is throttled. **The census says channel 1 is roughly half open, so it is not.** The
PRECOMMIT records, before any dispatch was seen, that a coal move in **either** direction is
consistent with the mechanism and that **neither sign will be read as a success**.

### 2c. CHANNEL 2 MEASURED — the coal offer DOES fall, but the merit order barely moves

The two channels of §2b are separable at zero LP cost, because they act on different arrays. G-2 already
showed the coal **fuel price** moves **exactly 0.0**, so channel 2 can only appear in the assembled
**offer** (`mc_base`). Measured on the same `fleet_only` arm/control pair, capacity-weighted, per hour:

| class | rows | capacity | `mc_base` control | arm | **Δ $/MWh** | Δ % | rows moved | MW moved |
|---|---|---|---|---|---|---|---|---|
| **coal** | 553 | 49,371.7 MW | 23.782 | 20.725 | **−3.057** | **−12.85 %** | 393 | 33,156.4 |
| **gas** | 1,744 | 100,451.1 MW | 40.168 | 36.909 | **−3.259** | −8.11 % | 964 | 53,165.6 |
| **other** | 1,492 | 81,420.0 MW | 84.448 | 84.448 | **0.000** | 0.00 % | **0** | **0.0** |

**Three readings, all pre-solve:**

1. **Channel 2 is LIVE and large.** The coal offer falls 12.85 % on two-thirds of PJM's coal capacity,
   driven entirely by the PRB passthrough sigmoid reading the lower ISO `_gas_series` — because the
   coal *fuel price* itself does not move at all (G-2). This is exactly the indirect route §2b
   enumerated, and it is now measured rather than argued.
2. **But the MERIT ORDER barely moves, and it moves the *other* way.** Coal falls −3.057 and gas falls
   −3.259, so the coal-minus-gas offer gap goes **−16.386 → −16.184**, a change of **+0.202 $/MWh**:
   coal becomes marginally **less** competitive against gas, not more. **The two channels very nearly
   cancel.**
3. **G-2's confinement is stronger than the gate asked for.** 1,492 non-coal, non-gas rows / 81,420 MW
   move **exactly** 0.0 in the assembled offer, not merely in the fuel price.

**So the pre-solve prediction, on the mechanism's own arithmetic, is: coal ≈ FLAT with a slight
DOWNWARD bias, and prices down by roughly 3 $/MWh on the marginal offer.** That **contradicts the
handoff's and FINDING §5b's confident "coal UP"**, which assumed channel 1 was throttled by the print
path. It is recorded here **before any LP**, which is precisely what rule 29 `[R-SCREEN]` clause (0)
exists to extract — an arm's structural behaviour, established for the cost of two fleet builds.

---

## 3. THE FLEET FIX (Card A) — inert in 2023-2025, **PROVEN not asserted**

Measured off `data/raw/eia-860/eia860_generator_retired_within_window.parquet` (1,094 rows), PJM only
(393 rows / 19,703.0 MW net summer). A row contributes months to solve year *Y* only if
`planned_retirement_year >= Y`.

| solve year | 2019 | 2020 | 2021 | 2022 | **2023** | **2024** | **2025** |
|---|---|---|---|---|---|---|---|
| rows the widening ADDS | 205 | 151 | 108 | 78 | **0** | **0** | **0** |
| MW added | 13,294.9 | 8,094.5 | 5,687.1 | 4,535.9 | **0.0** | **0.0** | **0.0** |

All 205 added rows carry `planned_retirement_year <= 2022`. Reproduces the handoff's PJM figures
**exactly**, which is an independent check on the whole chain. Class mix: **Conventional Steam Coal
10,649.9 MW (80.1 %)**, gas-CC 968.6, petroleum liquids 547.4, gas-ST 431.1, gas-CT 364.5, landfill
gas 168.0, wood 83.0, batteries 47.6.

**§A5 item 2 (the partial-plant double-count) cannot occur in PJM:** `partial_plant_exit_carry` is
absent from the keeper's `run_config.json` (i.e. `False`), so the channel is disarmed in every run
this session solves; and `_partial_plant_exit_rows` returns `None` for every BA in this container.

**§A9 (the plant-356 "COD defect") was not re-litigated**, per instruction.

---

## 4. THE CONTROL POSTURE — a negative result, stated rather than papered over

**G-DRIFT (rule 29(b)) is NOT RUNNABLE for PJM.** The keeper's recorded `git_sha` `457ae04` does not
resolve at HEAD and has no `citation-commit-map.txt` entry (it predates the 2026-08-16 history
rewrite by one day); deepening the clone 506 → 5,553 commits does not recover it. Session **pjm-177
reached the identical conclusion earlier the same day**. The nearest defensible surrogate base
(`acf784ec`, 33 minutes before the keeper's solve) is **221 files / 187,385 insertions** from HEAD on
the audited paths — not a "costs seconds" audit, and claiming it all INERT unread would be exactly the
unbacked heuristic rule 29(b) refuses, in the permissive direction.

**And there is measured LIVE drift.** pjm-177 spent the same-HEAD control this earned and published:
every class within **≤0.25 %** of the committed keeper *except* **CT_PEAKER −2.34 %**
(19.363 → 18.911 TWh) — *"HEAD drift in a class this mechanism never touches, which form-4
differencing would have charged to the arm."*

**Posture adopted, and no control solve spent:** form 4 is used but declared **IMPAIRED**, because
(a) the handoff forbids a control solve explicitly (§2c/§A6), (b) under §A7 the differencing **sizes**
the promotion rather than selecting it, and (c) the drift is already published for the screen year at
today's HEAD. **Pre-registered consequence, fixed before the solve:** any keeper-differenced class move
within **±0.25 %** — **±2.4 % for CT_PEAKER** — is **NOT SEPARABLE** from HEAD drift and is reported as
such, never claimed for or against the arm.

---

## 5. GATE BASELINE (§8), re-measured on this tree

`pytest tests/scoring` → **16 failed, 1,536 passed, 8 skipped**. This tree changes **no source code**
(the diff against `origin/main` is two docs and a `.gitignore` block), so **all 16 are pre-existing and
this session adds none** — matching §A3's corrected baseline of 16 exactly.

---

## 6. A SETUP COST THE PROGRAM HAS NOT RECORDED

A fresh container needs, before its first PJM LP: `hydrate_data.py --profile pjm` (2.3 GB);
**`regenerate_clean.py` over ~55 datatypes** (`data/clean` is gitignored and ships **empty**); **and a
re-fetch of `data/raw/pjm-da-virtuals/`**, a gitignored DataMiner corpus that `virtual_bids.py`
**hard-fails** on rather than silently no-op (`pjm_da_virtual_bids` is armed in the PJM keeper), i.e.
`scripts/data/fetch_pjm_da_virtuals.py` for every solve year. That is on the order of **1.5-2 hours of
non-LP setup per container**, and §A1's five-shard plan pays it **five times**. This is worth folding
into the next handoff's shard template.

---

## 7. SOLVE RESULTS

*(Filled in as each arm completes — see §8 for the state of every bundle on disk.)*
