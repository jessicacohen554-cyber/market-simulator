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

## 7. THE SCREEN — 2023, **ALL FIVE GATES PASS**

Bundle `results/screen/pjm_ep_level_2023` (gitignored, rule 31 — kept on disk, never deleted).
Solve: matrix build 19.0 s, cold solve 321.8 s / 414,796 simplex iterations, warm 183.1 s.
Peak RSS **12.47 GB against a 15.7 GiB container**, with **2 GB of the provisioned swap in use** —
i.e. §A6's diagnosis confirmed in practice: without `prepare_solve_container.py` this solve is
SIGKILL'd, exactly as the predecessor was.

| gate | measured | verdict |
|---|---|---|
| **G-1** direction/magnitude | gas array −0.3721 $/MMBtu, DOWN in 12/12 months (§2) | **PASS** |
| **G-2** confinement | non-gas fuel price max \|Δ\| **0.0**; non-coal-non-gas offer max \|Δ\| **0.0** (§2, §2c) | **PASS** |
| **G-3** rule 19, replaced not blended | armed ISO series = EP level to **0.0000000000**, 12/12 months | **PASS** |
| **G-4** no load-bearing PASS → FAIL | scored below | **PASS** |
| **G-5** LP integrity | **slack max 0.0, dump max 0.0, slack sum 0.0, dump sum 0.0** | **PASS** |

### 7a. G-4 — scored through the real scorer, on the COMMITTED bench

A screen bundle is never registered, so `calibration_verdict.py` cannot resolve it by run id. The
arm's payload was therefore built in memory through the supported path
(`render_calibration_html.build_payload`) and scored by `determine_from_artifacts` against the
**committed** `frontend/data/backcast/bench/PJM/2023.json.gz` — the same actuals the keeper's own
verdict was scored on. **Nothing was written under `frontend/`.**

| criterion | tier | keeper 2023 | **arm 2023** |
|---|---|---|---|
| C1 fuelmix | load-bearing | PASS | **PASS** |
| C2 sysvol | load-bearing | PASS | **PASS** |
| C3a price_mean | load-bearing | PASS | **PASS** |
| C3b price_shape | load-bearing | PASS | **PASS** |
| C3c price_tail | supporting | PASS | **PASS** |
| C4 dispatch_corr | supporting | PASS | **PASS** |
| C8 forced_share | protective | PASS | **PASS** |
| C6 governance | protective | UNATTESTED | UNATTESTED |

`grade_summary` **{scored 7, target_grade 7, commercial_grade 0, ledgered 0, fails 0}** — identical
to the keeper's. **Zero criteria fail; nothing flips PASS → FAIL. G-4 PASSES.** C6 reads UNATTESTED
because neither a screen bundle nor the pruned keeper bundle carries an attestation — the keeper's
own bundle-local `metrics.json` reads UNATTESTED for the same reason, so this is a property of the
artifacts, not of the arm.

### 7b. THE DISPATCH — differenced against the keeper's committed hourlies, with the drift bands applied

Read off `pjm_debugb_inputclock_A/hourly/class_hourly_2023.parquet` (rule 15's stated purpose) vs the
arm's. **"Separable" applies the PRECOMMIT's pre-registered bands: ±0.25 %, ±2.4 % for CT_PEAKER.**

| class | keeper TWh | arm TWh | Δ | Δ % | separable from HEAD drift? |
|---|---|---|---|---|---|
| **CC_REGULAR** | 322.289 | 330.612 | **+8.323** | +2.58 % | **YES** |
| **ST_GAS** | 10.826 | 13.536 | **+2.710** | +25.03 % | **YES** |
| CT_CHP | 1.292 | 1.867 | +0.574 | +44.45 % | YES (tiny absolute) |
| CC_CHP | 8.577 | 8.515 | −0.061 | −0.72 % | YES |
| ST_CHP | 0.987 | 0.994 | +0.007 | +0.73 % | YES |
| **COAL_BIT** | 103.712 | 103.820 | +0.108 | +0.10 % | **no — inside the drift band** |
| COAL_PRB | 3.143 | 2.926 | −0.218 | −6.93 % | YES |
| COAL_WC | 5.751 | 5.219 | −0.532 | −9.26 % | YES |
| **CT_PEAKER** | 19.363 | 19.377 | +0.014 | +0.07 % | **no — inside the 2.4 % CT band** |
| import (net) | −27.468 | −31.426 | −3.959 | +14.41 % | YES |
| VIRTUAL_INC | 19.049 | 14.847 | −4.201 | −22.06 % | YES |
| VIRTUAL_DEC | −11.651 | −13.883 | −2.233 | +19.16 % | YES |
| nuclear / wind / solar / hydro / biomass / oil / OTHER | — | — | **+0.000** | 0.00 % | — (exactly unchanged) |
| **TOTAL** | 787.924 | 788.456 | +0.532 | +0.07 % | — |

### 7c. THE PRE-REGISTERED COAL PREDICTION WAS RIGHT, AND THE HANDOFF'S WAS NOT

**Total coal: 112.606 → 111.965 TWh, −0.641 TWh (−0.57 %).** Coal is **essentially FLAT with a
slight DOWNWARD bias** — which is **exactly** what §2c derived from the offer arrays before any LP
(the coal offer falls 3.057 while gas falls 3.259, so the merit-order gap moves +0.202 *against*
coal), and it **contradicts the handoff's and FINDING §5b's "coal UP"**.

The largest coal component, COAL_BIT, moves **+0.10 %** — *inside* the pre-registered drift band, so
it is **not separable from HEAD drift** and is not claimed in either direction. The separable coal
movement is COAL_PRB −6.93 % and COAL_WC −9.26 %, both down. Channel 1 (cheaper gas displacing coal)
wins over channel 2 (the PRB sigmoid cheapening coal offers), which the 51.794 % census made possible
and a ~100 % census would have foreclosed.

The other side of the same coin: **CC_REGULAR +8.323 TWh** and **ST_GAS +2.710 TWh** — gas takes the
share. Net **imports fall 3.959 TWh** (PJM exports more), coherent with a cheaper PJM stack. The DA
virtual layer responds as pjm-158 measured it would: net cleared virtual position 7.398 → 0.964 TWh
against a −2.36 $/MWh price move, ~+2.7 GW·h per $/MWh in the direction pjm-158's dNet/dλ predicts.

### 7d. C3a — REPORTED AT FULL MAGNITUDE, and it is a large improvement

| | load-weighted mean LMP $/MWh | error vs actual 29.58 |
|---|---|---|
| committed keeper | **31.4124** | **+6.19 %** |
| **arm** | **29.0536** | **−1.78 %** |
| Δ | **−2.3587** | absolute error **1.83 → 0.53 $/MWh** |

**Stated plainly and not dressed up:** the move is **larger than I predicted**. The PRECOMMIT
registered "−0.5 to −2.0 $/MWh"; the measurement is **−2.36**, overshooting my own band by 0.36, and
it carries PJM from 6.2 % *over* actual to 1.8 % *under* it. The error shrinks by 71 %, but the sign
flips, and a mechanism that overshoots its pre-registered magnitude is reported as such rather than
banked as a win. **Rule 1 `[R-STRUCT]`: this is not why the change lands.** It lands because it is the
measured delivered gas price (rule 14 `[R-ACCURATE]`), and it would land if C3a had got worse.

**C3b did not break.** It scores PASS on the arm, which was the pre-registered risk and the criterion
that killed ercot-254. PJM was the program's highest-risk ISO for it (§(c) of the PRECOMMIT), and the
protections held: the largest admitted monthly gap is 1.42 $/MMBtu against ERCOT's 49.53, and
`gas_daily_shape` is armed so the monthly level is redistributed by the measured daily swing.

---

## 8. THE TRAINING SPAN — registered as `2026-09-09-pjm-fuelvintage-ep-level`

**ONE bundle, ONE `--years 2023 2024 2025` invocation, years sequential** (rules 16 `[R-ALLYEARS]` /
12 `[R-PARALLEL]`). Bundle `results/calibration/pjm_fuelvintage_A`. Registered in this session per
rule 15 `[R-DASHBOARD]`.

### 8a. Every scored criterion PASSES in all three years

| criterion | tier | verdict |
|---|---|---|
| C1 fuelmix | load-bearing | **PASS** (D-10 free-class: **C1 all 16/16 · free 12/12**) |
| C2 sysvol | load-bearing | **PASS** |
| C3a price_mean | load-bearing | **PASS** |
| C3b price_shape | load-bearing | **PASS** |
| C3c price_tail | supporting | **PASS** |
| C4 dispatch_corr | supporting | **PASS** |
| C6 governance | protective | **PASS** |
| **C8 forced_share** | protective | **FAIL** — **see §8c: NOT this arm's** |

C5a CO2 (reported-only): +1.2 % / −0.8 % / +4.8 %.

### 8b. C3a across the span — reported at full magnitude, two years better and one worse

Model load-weighted mean LMP vs the committed bench **RT** actual (the branch C3a takes for PJM):

| year | actual RT | keeper | keeper err | **arm** | **arm err** | Δ |
|---|---|---|---|---|---|---|
| 2023 | 28.44 | 31.4124 | **+10.45 %** | **29.0536** | **+2.16 %** | −2.3587 |
| 2024 | 29.53 | 31.1074 | **+5.34 %** | **29.6929** | **+0.55 %** | −1.4144 |
| 2025 | 42.89 | 42.3790 | **−1.19 %** | **41.6390** | **−2.92 %** | −0.7400 |

**2023 and 2024 improve markedly; 2025 gets WORSE** (−1.19 % → −2.92 % error), because the keeper was
already slightly *under* actual there and the seam pushes it further under. All three stay inside the
±10 % band and C3a passes, but the 2025 degradation is a real cost and is stated, not buried. The
per-year move tracks the input delta exactly as the mechanism's own arithmetic says it should
(annual fuel Δ −0.770 / −0.469 / −0.189 $/MMBtu → price Δ −2.36 / −1.41 / −0.74 $/MWh), which is the
signature of a real operand rather than a fitted one.

**C3b PASSES in all three years** — the pre-registered risk, and the criterion that killed ercot-254.

### 8b2. Dispatch across the span

| year | COAL (TWh) | Δ % | CC_REGULAR | Δ % | ST_GAS | Δ % |
|---|---|---|---|---|---|---|
| 2023 | 112.606 → 111.964 | **−0.57 %** | 322.289 → 330.612 | +2.58 % | 10.826 → 13.536 | +25.03 % |
| 2024 | 114.179 → 111.858 | **−2.03 %** | 335.649 → 338.596 | +0.88 % | 10.854 → 13.161 | +21.25 % |
| 2025 | 142.768 → 144.791 | **+1.42 %** | 334.330 → 333.455 | −0.26 % | 17.079 → 19.090 | +11.77 % |

Coal is **small and mixed** — down in two years, up in one — i.e. essentially flat, which is the
zero-LP §2c prediction and **not** the handoff's uniform "coal UP". Slack and dump are **exactly 0.0**
in all three years.

### 8c. THE C8 FAILURE IS **NOT** THIS ARM'S — measured three ways, not asserted

The scorer reads **C8 FAIL on 2025 ST_GAS: 41.3 % forced, "above the 30 % cap and NOT grounded"**,
with the D-4 provenance leg failing on **`st_netload_drag`** (plants 3131, 3138, 3148, 3775, 593) —
a min-gen drag mechanism **the fuel seam does not touch at all**.

Before attributing that to the arm I checked what the keeper does under the *same* generator. The
keeper's committed `legitimacy_diagnostics.json` carries **12 D-4 rows**; HEAD's generator produces
**~210**. That is a change in `scripts/legitimacy_diagnostics.py`'s **D-4 per-unit conduct** check,
not a change in dispatch.

| artifact | D-2 | D-4 |
|---|---|---|
| keeper, **as committed** (old generator) | passed **False**, 42 rows, **3 fails** (CT_PEAKER 16.2/16.4/16.7 % > 15 %) | passed **True**, **12 rows**, 0 fails |
| **keeper, REGENERATED at HEAD** | passed True, 28 rows, 0 fails | **passed False, 208 rows, 38 fails** |
| **arm, at HEAD** | passed True, 35 rows, 0 fails | **passed False, 211 rows, 35 fails** |

**The keeper fails D-4 at HEAD MORE than the arm does (38 vs 35 failures.)** And scoring the
incumbent keeper's own registered artifacts with the regenerated diagnostics swapped in:

| the incumbent keeper `2026-08-15-pjm-162-inputclock`, scored… | determination | C8 |
|---|---|---|
| …with its **committed** diagnostics | **CALIBRATED** | PASS |
| …with **HEAD's** diagnostics | **NOT-YET** | **FAIL** |

**Conclusion: PJM's designated keeper does not survive its own C8 gate under the diagnostics
generator now on `main`.** That is a **pre-existing latent condition on `main`**, surfaced here, and
it is **independent of this session's change** — the arm inherits it and, on the D-4 count, inherits
slightly less of it. **This is escalated, not absorbed:** it is not the fuel seam's to fix, it affects
the incumbent keeper's standing determination, and it should be routed to PJM's own lane (or the
governance lane) as its own charter. Rule 1 `[R-STRUCT]` is untouched either way — the seam lands
because it is the more accurate measured input, not because of any gate.

### 8d. Governance

C6 **PASSES** on a written attestation
(`results/calibration/pjm_fuelvintage_A/calibration_attestation.json`) that records: **ONE config
delta** (`gas_electric_power_monthly_level: False → True`); **ZERO free parameters added** — the DOF
ledger is carried **verbatim** from the incumbent (`n_entries 19`, `n_residual 6`), because the blend
weights are a rule-23 frozen EIA-860 derive, the conversion is EIA's published 1.036 MMBtu/Mcf, and
the two admission conditions were declared ex ante and **never swept**; **NO `authorized_price_tuning`
block**, because this is not an offer-curve band multiplier and no value in it was chosen by looking
at a residual; the rule-19 replacement verified to 0.0000000000; the impaired-form-4 control posture;
and the C3a overshoot stated as an overshoot.

---

## 9. THE VALIDATION TOUCHPOINTS — `2026-09-09-pjm-fuelvintage-touchpoints`

2020 / 2021 / 2022 on the keeper's frozen recipe, under PJM's `complete` marker with
`--holdout-authorized`. **2019 was neither attempted nor designed around** (locked tier, `final`
empty, freeze ACTIVE). Stamped to the keeper (rule 30(a)) so it FOLDS into the keeper's own year
selector rather than appearing as a second card; status part rebuilt for the per-year ladder
(rule 30(b)).

Unlike the training span, these three years carry the **retiree-window widening LIVE** —
+8,094.5 / +5,687.1 / +4,535.9 MW, 80.1 % Conventional Steam Coal. Both fixes are carried together
with **no attribution arms** (owner instruction), so nothing here separates the fleet fix from the
fuel seam.

| criterion | verdict |
|---|---|
| C2 sysvol, C4 dispatch_corr, C6 governance | **held** (PASS) |
| **C8 forced_share** | **IMPROVED** — in-sample FAIL → **holdout PASS** |
| C1 fuelmix | degraded — 2020 COAL_BIT +21.10 TWh / CC_REGULAR +9.16; 2021 CC_REGULAR +27.59 / ST_GAS +8.17; 2022 CC_REGULAR +24.84 / ST_GAS +8.97 |
| C3a | degraded — 2020 **+21.0 %**, 2022 **−13.0 %**; **2021 PASSES** |
| C3b | degraded — 2020 NRMSE 0.232, 2022 0.270; **2021 PASSES** |
| C3c | ledgered CAVEAT on 2021/2022 (rubric v3.6) |

**2021 is the strongest rung** — it passes C3a and C3b outright.

**Rule 30(c): none of this downgrades PJM.** The ISO's determination is the train-tier verdict and
nothing else, and rule 22 makes a validation number iterable model-SELECTION evidence that must
never be quoted as a certified out-of-sample skill number.

**One reading worth carrying forward:** C8 is the single criterion that moves *the other way* —
it PASSES on all three holdout years while the train tier fails it on 2025 ST_GAS. That is further
evidence that the C8 failure is the `main`-side D-4 generator condition of §8c rather than anything
this recipe does.

---

## 10. SOLVE STATE — every bundle on disk

*(Updated as each arm completes.)*

| arm | years | bundle | status |
|---|---|---|---|
| **S** screen | 2023 | `results/screen/pjm_ep_level_2023` | **DONE — all five gates PASS** |
| **T** training | 2023 2024 2025 | `results/calibration/pjm_fuelvintage_A` | **DONE — REGISTERED `2026-09-09-pjm-fuelvintage-ep-level` and PROMOTED to PJM's keeper** |
| **TP** validation | 2020 2021 2022 | `results/calibration/pjm_fuelvintage_TP` | **DONE — REGISTERED `2026-09-09-pjm-fuelvintage-touchpoints`, stamped/folded to the keeper** |
| H1 shard | 2020 2021 | `results/pjm_fuelvintage_H1_shard` | cloud shard done; its push omitted the bundle-root `system.parquet` the payload builder needs, so it is NOT registrable here — superseded by TP, RETAINED on disk |
| H2 shard | 2022 | branch `claude/pjm-fuelvintage-1-h2` | same limitation; superseded by TP |

**Rule 31 `[R-RETAIN]`: nothing is deleted.** The bundle families are gitignored, which is what
discharges rule 29(c), and they stay on local disk. **This container is ephemeral — see §9.**
