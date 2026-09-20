# RESULT — SPP-51 / `R-bc`: the literal object was killed at phase 0; the real one is a thermal floor that repairs PRICE and does not close C1

**Lane** SPP-51 · **PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-51-curtailment-lp-constraint-2026-09-20.md`
+ `PRECOMMIT-spp-51-ADDENDUM-window-2026-09-20.md`, **both pushed before any solve**
(`f80de3e1`, `0a7f5c06`) · **Base** `608cb21f` · **Keeper** `2026-09-16-spp-42-commitment-feasibility`
**UNCHANGED** · **Rung** `2026-09-19-spp-49-benchmark-membership` **UNCHANGED** ·
**Nothing registered, nothing pruned, nothing deleted.**

**LP spent:** 7 shards × 2 legs (control + arm), one shard per year (rules 32 `[R-SHARD]` / 36
`[R-YEAR-ISOLATION]`). The parent ran no LP. Scoring probe
`scripts/probes/_spp51_score_arm.py`; phase-0 probes `_spp51_{price_tail,floor_window,floor_level,
price_regime_hourmatched,c8_forced_share,floor_prediction}*.py`.

---

## 0. Headline

1. **`R-bc` as chartered is dead, and phase 0 is where it died** — which is what the charter asked
   for. A per-hour wind constraint row `W[z,t] ≤ K[z,t]` defines the **identical feasible region**
   as lowering the bound, so its dual never enters λ: it is the SPP-63 ceiling renamed. The only
   wind-side row whose dual does reach λ is a cross-hour energy budget, and it fails rule 13
   `[R-MEASURED]`'s forward test *and* pushes the price the wrong way. **No LP was spent proving
   this.**
2. **The charter's price premise was inverted, and that is what re-aimed the lane.** The model has
   **3–6× too FEW** negative-price hours, not too many (2025: 176 model vs **1,018** actual RT).
   The SPP-63 ceiling took 167 → **0**, away from the market.
3. **The real object is SPP's missing thermal min-load floor**, armed through two existing,
   measured, default-off gates — `coal_mustrun_online_pmin` + `coal_sync_srmc_tranche`. **Zero new
   fields, zero new free parameters, zero code changed, SPP-only.**
4. **IT WORKS ON PRICE, AND THAT IS THE RESULT.** Against its own same-HEAD control, in all six
   years solved so far: **C3a improves in 6 of 6**, **C3b improves in 5 of 6** (2025 **0.196 →
   0.159**, off the edge of its 0.20 band), **negative-price hours roughly DOUBLE** (+180 to +268,
   toward the market's ~1,000), **slack FALLS** (2024 1,295.7 → 802.8 MWh), dump stays 0.000, and
   the **zero-coal collapse is ELIMINATED — 151–290 h/yr → 0 in every year.**
5. **IT DOES NOT CLOSE C1, and I predicted that before solving.** It closes **4.8 %** of the fossil
   miss (predicted ~8.5 %). Worse: the coal it adds comes from **GAS, not from wind** (+2.196 TWh
   coal against only **−0.384 TWh** wind), so it makes the already-short `ST_GAS` row **more**
   short and pushes summed |C1 error| **UP in the three years where coal was already long**.
6. **My own predictions were wrong in two places and I am reporting both.** P-1 understated the
   coal gain by **2.6×**; and my ADDENDUM **revised a correct prediction into an incorrect one** —
   it said more negative hours was "now doubtful, possibly ~0 change", and they doubled. §2.
7. **Free result, and SPP owed it: the rule 36(f) contamination in SPP is ZERO.** Control
   (year-isolated, HEAD) − keeper (committed) is **0.0000 TWh** in 2019/2021/2022 and **±0.0028
   TWh** in 2023/2024/2025 — and that residue is a pure `COAL_PRB ↔ COAL_LIGNITE` reclassification
   summing to zero. §6.

---

## 1. What was solved

Each shard ran **two** `replay_keeper.py` legs at one pinned HEAD (`f80de3e1`) on its own year:
a **CONTROL** (keeper recipe, unchanged) and an **ARM** (`--set coal_mustrun_online_pmin=true
--set coal_sync_srmc_tranche=true`). Single-delta by construction — the recipe is the keeper's,
and the only difference is the two booleans.

**Why control solves at all (rule 29 `[R-SCREEN]` (b)), stated before the result:** both SPP
registered runs **predate** the rule 36 warm-start flip (`cb1e60b7`) and were solved as single
multi-year invocations, so the committed keeper was not a like-for-like control for a
year-isolated solve at HEAD; the solve-path drift was also large and live on this lane's own files
(`1f586ed7..HEAD`: 62 files, +8,701 lines, incl. `renewables.py`, `lp/bounds.py`, `lp/costs.py`,
`floor_mechanisms.py`).

**Honest postscript: the measurement says form 4 would have been fine.** §6 finds the drift is
~0. The six control legs (~6 × 150 s) bought certainty that could not be had at zero LP given
8,701 changed lines, plus the rule-36(f) measurement SPP owed. I would spend them again, and I am
recording that they turned out to be unnecessary.

---

## 2. THE PREDICTION SCORECARD — scored against what was pushed before the solve

| # | pre-registered | measured (6 yrs) | verdict |
|---|---|---|---|
| P-1 | coal **+0.849** TWh/yr, range 0.02–1.38 | **+2.196** (2.081–2.280) | **WRONG — 2.6× low, outside the range in EVERY year** |
| P-2 | wind **−0.6 to −0.9** TWh/yr | **−0.384** (0.000 to −0.589) | **WRONG — too large a shed predicted; 2019 is exactly 0.000** |
| P-3 | closes **~8.5 %** of C1 | **4.8 %** | right in kind, **half** the magnitude |
| P-4 | negative hours **UP** *(ADDENDUM revised to "doubtful, ~0")* | **+180 to +268, a doubling** | **ORIGINAL RIGHT; MY ADDENDUM REVISION WRONG** |
| P-4b | *(ADDENDUM)* zero-coal hours "will largely REMAIN" | **151–290 → 0, eliminated** | **WRONG** |
| P-5 | C3a **DOWN** | **−0.28 to −1.80, all 6 years** | **CONFIRMED** |
| P-6 | C3b **DOWN** | better in **5 of 6**; 2025 0.196 → 0.159 | **CONFIRMED** (2021 0.213 → 0.245 worse) |
| P-7 | min price stays **−26.000** | **exactly −26.000**, both legs, all years | **CONFIRMED** |
| C8 | D-2 forced share ≪ 30 %, "loose bound 29.5–44.9 % will read lower" | **4.41–15.26 %**, D-2 `passed` unchanged | **CONFIRMED** |

### 2.1 Where my ADDENDUM went wrong, and why — because it is the instructive part

The addendum measured that the floor's top-k window is ranked on **system LOAD**, that no SPP
plant reaches the 0.99 all-hours override, and that the aggregate floor is therefore **0.840 GW**
in the lowest-load decile and **0.000 GW** in the lowest-load hour — while the zero-coal collapse
lives in the bottom 6–14 % of **load**. From that I concluded the floor could not reach the
oversupply hours, and revised P-4/P-4b accordingly.

**The measurement was right; the inference was wrong.** I conflated **load** rank with **net-load**
rank. SPP's oversupply hours are low-**net**-load — high wind — and most of them are perfectly
ordinary **mid-load** hours, sitting well inside the window. So the floor binds there, forces coal
on, pushes wind to the margin, and prices at −26.000. That is precisely why negative hours doubled
and why the zero-coal count went to zero, both of which I had talked myself out of.

**What the addendum got right stands, and it is the successor.** The floor's *level at the bottom*
is still far too shallow: the arm's coal minimum is **0.15 %–1.93 %** of its own annual max against
the real SPP PRB fleet's **8.1 %–17.5 %**. The collapse is stopped, not the shallowness repaired.
R-bd (net-load ranking) is still the named successor, now for the **level**, not the reach.

---

## 3. What the mechanism did — arm minus control, one HEAD, TWh

| year | COAL_PRB | COAL_LIGNITE | CC_REGULAR | CT_PEAKER | ST_GAS | **wind** | solar |
|---|---|---|---|---|---|---|---|
| 2019 | +1.903 | +0.178 | −1.427 | −0.487 | −0.074 | **0.000** | 0.000 |
| 2021 | +1.923 | +0.293 | −0.940 | −0.514 | −0.106 | **−0.549** | −0.006 |
| 2022 | +1.896 | +0.326 | −0.919 | −0.522 | −0.157 | **−0.589** | −0.003 |
| 2023 | +1.876 | +0.272 | −0.839 | −0.549 | −0.220 | **−0.499** | −0.006 |
| 2024 | +1.964 | +0.316 | −0.837 | −0.807 | −0.255 | **−0.338** | −0.006 |
| 2025 | +1.996 | +0.236 | −0.855 | −0.679 | −0.299 | **−0.330** | −0.020 |

**THE ENERGY COMES FROM GAS, NOT FROM WIND.** Mean coal **+2.196 TWh**, mean wind **−0.384 TWh** —
**83 % of the coal gain is displaced gas.** In 2019 wind moves **exactly 0.000** and the whole
+2.081 TWh of coal is gas displacement.

**This is the load-bearing negative result for the curtailment hypothesis.** The lane was chartered
on the arithmetic identity that SPP's wind excess (+10.14 TWh) equals its fossil miss (−9.99 TWh).
A thermal floor does **not** convert one into the other: it moves the **coal/gas merit order** and
leaves the wind excess essentially intact (−0.38 of +10.14 = **3.8 %**).

---

## 4. Price — the half that works

| year | lw price ctl → arm | Δ | **h < $0 ctl → arm** | Δ | **actual RT h < $0** | min price | slack ctl → arm |
|---|---|---|---|---|---|---|---|
| 2019 | 22.387 → 22.105 | −0.282 | 0 → 0 | 0 | 547 | −/− | 0 → 0 |
| 2021 | 40.167 → 38.364 | **−1.803** | 243 → **511** | +268 | 1,108 | −26.000 | 0 → 0 |
| 2022 | 43.682 → 42.159 | −1.524 | 294 → **518** | +224 | 995 | −26.000 | 501.3 → **274.6** |
| 2023 | 25.766 → 24.681 | −1.085 | 237 → **489** | +252 | 992 | −26.000 | 0 → 0 |
| 2024 | 26.370 → 25.338 | −1.033 | 225 → **405** | +180 | 1,172 | −26.000 | 1,295.7 → **802.8** |
| 2025 | 30.323 → 29.064 | −1.258 | 176 → **401** | +225 | 1,018 | −26.000 | 240.6 → **76.9** |

`dump` is **0.000 MWh** in every leg of every year, and **slack FALLS** wherever it was non-zero —
so the arm adds no new forcing on either channel.

**C3a / C3b, scored with the scorer's own functions against the committed bench:**

| year | C3a ctl → arm | C3b ctl → arm | C3b status |
|---|---|---|---|
| 2019 | 22.39 → 22.11 | 0.125 → **0.114** | PASS → PASS |
| 2021 | 40.17 → 38.36 | 0.213 → 0.245 | FAIL → FAIL *(the one regression)* |
| 2022 | 43.68 → 42.16 | 0.213 → **0.206** | FAIL → FAIL |
| 2023 | 25.76 → 24.68 | 0.177 → **0.166** | PASS → PASS |
| 2024 | 26.37 → 25.34 | 0.170 → **0.156** | PASS → PASS |
| 2025 | 30.32 → 29.06 | 0.196 → **0.159** | PASS → PASS |

**No criterion flips status in either direction.** C3a passes in all six years both ways; C3b's two
FAILs (2021, 2022) were already failing on the rung. The 2025 move is the largest and takes the
keeper's tightest year off the edge of its band.

### 4.1 The structural repair, which is the point under rule 1 `[R-STRUCT]`

| year | h with coal = 0, ctl → arm | coal min ÷ its own annual max, ctl → arm |
|---|---|---|
| 2019 | 0 → 0 | 0.0656 → 0.0648 |
| 2021 | **248 → 0** | 0.0000 → 0.0193 |
| 2022 | **290 → 0** | 0.0000 → 0.0056 |
| 2023 | **207 → 0** | 0.0000 → 0.0149 |
| 2024 | **181 → 0** | 0.0000 → 0.0100 |
| 2025 | **151 → 0** | 0.0000 → 0.0015 |

The model no longer takes SPP's entire PRB fleet — must-run band included — to exactly 0.0 MW.
**Reported at full magnitude: the repair is incomplete.** The real fleet floors at **8.1–17.5 %**
of its own max; the arm reaches **0.15–1.93 %**. It removes the *impossible* state without
reproducing the *observed* one.

---

## 5. C1 — where it costs, reported at full magnitude

| year | Σ\|class error\| ctl → arm | Δ | fossil miss ctl → arm | closed |
|---|---|---|---|---|
| 2019 | 32.476 → **28.477** | **−3.999** | −9.391 → −9.388 | +0.004 |
| 2021 | 28.639 → 30.280 | **+1.641** | −6.263 → −5.629 | +0.634 |
| 2022 | 33.344 → 36.565 | **+3.221** | −6.733 → −6.136 | +0.597 |
| 2023 | 26.512 → **25.436** | −1.076 | −8.727 → −8.220 | +0.507 |
| 2024 | 29.430 → **28.325** | −1.105 | −10.859 → −10.512 | +0.347 |
| 2025 | 36.639 → 38.542 | +1.903 | −9.199 → −8.838 | +0.361 |

**Mean fossil miss closed +0.408 TWh/yr of −8.529 = 4.8 %.** Summed |C1 error| improves in
2019/2023/2024 and worsens in 2021/2022/2025 — **exactly the three years where COAL_PRB was
already LONG** (+5.178 / +7.855 / +3.606), so adding ~2 TWh of coal overshoots further. `ST_GAS`,
SPP's most persistent C1 row, gets **worse in all six years** (−0.074 to −0.299).

Under rule 1 `[R-STRUCT]` none of this is disqualifying — *"a real market behaviour stays in even
if it makes the fit worse"* — and the mechanism was chartered on the fleet fact, not the residual.
But it is reported as what it is: **this is not SPP's C1 closer, and in half the years it moves
C1 the wrong way.**

---

## 6. The rule 36(f) measurement SPP owed — contamination is ZERO

`control (year-isolated, HEAD)` − `keeper (committed, multi-year, warm-start ON)`, TWh:

| year | COAL_PRB | COAL_LIGNITE | CC_REGULAR | CT_PEAKER | ST_GAS | wind | solar |
|---|---|---|---|---|---|---|---|
| 2019 / 2021 / 2022 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2023 | +0.0028 | −0.0028 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2024 | −0.0023 | +0.0023 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2025 | −0.0021 | +0.0021 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

Rule 36(f) states the artifact's size in SPP is **UNMEASURED**. It is now measured: **zero to
within a ±0.003 TWh `COAL_PRB ↔ COAL_LIGNITE` reclassification that sums to 0.0000.** This
simultaneously bounds **HEAD drift** — 8,701 changed lines across 62 solve-path files move SPP's
backcast by nothing. **SPP's keeper and rung carry no cross-year contamination and need no
re-solve on rule 36's account.** No other ISO's lane is implicated (rule 25 `[R-ISO-SCOPE]`).

---

## 7. Governance

* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`:** zero new fields, zero new free parameters. Both gates
  are existing registered `ScenarioConfig` booleans with CLI flags; every number consumed
  (`mustrun_online_pct`, `online_frac`, the take-or-pay share) is a measured column of the
  committed `thermal_tranches_SPP.csv`, not re-derived (rule 23 `[R-FROZEN-DERIVE]`). **Nothing
  was swept**, and no gate was re-read after the fact.
* **Rule 20 `[R-FORCED-BUDGET]` / C8:** D-2 `coal_mustrun` forced share **4.41–15.26 %** against
  the 30 % merchant cap. D-2's `passed` verdict is **identical in control and arm** in all six
  years (2022 fails in BOTH — pre-existing, not caused by this arm). Because the class is under
  budget, rule 20's conditional-pass escalation is not triggered and **no `D4_WINDOWS` entry is
  owed**. The control carries **no `coal_mustrun` row at all**, confirming SPP had zero coal
  floors.
* **Rule 19 `[R-ONE-MECH]`:** SPP's first commitment floor — it replaces nothing and stacks on
  nothing (`reliability_floor=false`, `class_commitment_overrides={}`,
  `reliability_floor_overrides={}` in the keeper). Reconciled with the already-armed
  `vre_curtailment_oversupply_allocation` as SPP-51c required.
* **Rule 25 `[R-ISO-SCOPE]`:** per-run CLI, SPP only, **no code changed**, so every other ISO is
  byte-identical by construction. PJM's and MISO's verdicts on this family were **not** transferred
  (rule 28(d)); SPP derived its band from its own artifact.
* **Rule 28 `[R-MECH-MATRIX]`:** the two gates are sub-scalars of the `coal_mustrun_per_plant`
  family row, not absent rows — a correction this lane pushed to its own PRECOMMIT (§9) **before
  any result was read**. SPP's cell of that row moves `U` → tested, in this session.
* **Rules 32/34/36:** parent ran no LP; one shard per year; each shard pushed its **full** bundle
  including `dispatch/<year>_P1.parquet`, verified by the parent with `git ls-tree` before any
  archive (rule 34(d)).
* **`[R-HOLDOUT]` removed:** no year is protected, so every number here is model-**SELECTION**
  evidence and none of it is a certified out-of-sample skill claim.

---

## 8. Successors

* **R-bd — the floor's LEVEL at the bottom, via a net-load ranking.** The arm's coal minimum is
  0.15–1.93 % of its own annual max against the real fleet's 8.1–17.5 %. `fleet/arrays.py:2884-2903`
  ranks the top-k window on **system load**; the physically right driver is **net** load, and it
  regenerates forward (more wind → lower net load → more cycling), so it is rule-13 admissible.
  **Not done here** because that function is shared and PJM/MISO runs arm this family — it needs
  its own gate and its own PRECOMMIT.
* **R-be — the price floor below −26 is structurally unreachable.** Model minimum is exactly
  `−ira_ptc_wind` = −26.000 with `dump_cost ≈ 26.001` capping it; the market goes below −26 in
  22–118 h/yr. No floor, ceiling or allocation reaches this.
* **R-ba — the ST_GAS / CT_PEAKER merit-order inversion**, now with **new evidence against
  deferring it**: this arm makes ST_GAS worse in all six years. It is untouched by this object and
  is the strongest remaining C1 candidate.
* **The wind excess itself remains open and is NOT closed by this lane.** −0.384 of +10.144 TWh is
  3.8 %. The `vre_reference_rate_curtailment_grossup` cell stays `U`.

---

## 9. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`), asked explicitly

**All twelve bundles are RETRIEVABLE and none is at risk** — each shard pushed its full bundle to
its own branch and the parent verified `dispatch/<year>_P1.parquet` is present in the tree
(`git ls-tree`), so a promotion from this state costs **zero re-solves**. Recovery is by immutable
SHA (rule 33(d)): `claude/spp51-2019` `f2d4626ffed6866b5e92aaacbaed1b8235d02a34`, `-2021`
`3d039cbfc160e1a9a3083df4b2f3d6f8c7990820`, `-2022` `c54547cae01ab358feafb8d1687d8e72ef43762c`,
`-2023` `bffc45f93de50c13aafeb89312e602035cf86b4f`, `-2024` `395ce757ad14ab59bb0862d0a04abea888810ab2`,
`-2025` `d3afa88d54acba652100bbad8ea6fffc9e8773c3`.

**The question: promote the coal synchronization floor into SPP's keeper recipe?**

**The case FOR** — it is a rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]` repair of a measured
falsehood: 12 of 24 SPP coal plants carry no min-load band at all, the model takes the whole PRB
fleet to exactly 0.0 MW for 151–290 h/yr where the real fleet never goes below 8.1 %, and the arm
**eliminates that state entirely**. It improves C3a in 6 of 6 years and C3b in 5 of 6, **doubles**
the negative-price hours toward a market that has 3–6× more of them, **reduces** slack, adds no
dump, keeps D-2 far under budget, costs **zero free parameters**, and **flips no criterion in
either direction**.

**The case AGAINST** — it closes only 4.8 % of C1, takes its energy from gas rather than wind
(so it does not touch the object the lane was chartered on), makes `ST_GAS` worse in all six
years, and pushes summed |C1 error| **up** in 2021/2022/2025.

**This session's reading, which is a recommendation and not a decision: PROMOTE.** Rule 1 is
explicit that a structurally-correct mechanism is not judged by the residual, and the price
evidence is one-directional across six independent years. But the C1 cost is real and is stated
above at full magnitude rather than buried, and the owner routinely rules the other way on exactly
this trade — which is why the question is asked here rather than pre-empted.

**If promoted**, rule 35 `[R-PROMOTE]` applies: the year union is **2019–2025 (seven years)** —
enumerated here BEFORE any prune, per 35(b) — so the incoming keeper must carry all seven, and
2020 must land first.
