# RESULT — SPP-51 / `R-bc`: the literal object was killed at phase 0; the real one is a thermal floor that repairs PRICE and does not close C1

**Lane** SPP-51 · **PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-51-curtailment-lp-constraint-2026-09-20.md`
+ `PRECOMMIT-spp-51-ADDENDUM-window-2026-09-20.md`, **both pushed before any solve**
(`f80de3e1`, `0a7f5c06`) · **Base** `608cb21f`.

**PROMOTED ON THE OWNER'S RULING, in session, verbatim: "Promote then Archive your stale shards and
give me a handoff prompt."** Incoming keeper **`2026-09-20-spp-51-coal-sync`**
(`spp51_syncfloor_span`, 2023–2025, **CALIBRATED**), with **`2026-09-20-spp-51-syncfloor-rung`**
(`spp51_syncfloor_rung`, 2019–2022) stamped to it. Outgoing keeper
`2026-09-16-spp-42-commitment-feasibility` and rung `2026-09-19-spp-49-benchmark-membership`
pruned under rule 35 `[R-PROMOTE]` (a). **This session RECOMMENDED promotion and did not act until
the ruling** (rule 31 `[R-RETAIN]`).

**LP spent:** 7 shards × 2 legs (control + arm), one shard per year (rules 32 `[R-SHARD]` / 36
`[R-YEAR-ISOLATION]`). The parent ran no LP. Scoring probe `scripts/probes/_spp51_score_arm.py`;
composition `scripts/probes/_spp51_compose_span.py`; attestation `scripts/gen_spp51_attestation.py`.

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
4. **IT WORKS ON PRICE, AND THAT IS THE RESULT.** Against its own same-HEAD control, over all seven
   years: **C3a |error| improves in 6 of 7**, **C3b improves in 6 of 7** (2025 **0.196 → 0.159**,
   off the edge of its 0.20 band), **negative-price hours roughly DOUBLE** (+129 to +268, toward
   the market's ~1,000), **slack FALLS** wherever non-zero (2024 1,295.7 → 802.8 MWh), dump stays
   0.000, and **the zero-coal collapse is ELIMINATED — 41–290 h/yr → 0 in every year.**
   **No criterion flips status in either direction, in any year.**
5. **IT DOES NOT CLOSE C1, and I predicted that before solving.** It closes **4.4 %** of the fossil
   miss (predicted ~8.5 %). Worse: the coal it adds comes from **GAS, not from wind** (+2.205 TWh
   coal against only **−0.350 TWh** wind), so it makes the already-short `ST_GAS` row **more** short
   in all seven years and pushes summed |C1 error| **UP in the three years where coal was already
   long**.
6. **My own predictions were wrong in two places and I am reporting both.** P-1 understated the coal
   gain by **2.6×**; and my ADDENDUM **revised a correct prediction into an incorrect one** — it
   said more negative hours was "now doubtful, possibly ~0 change", and they doubled. §2.
7. **Free result, and SPP owed it: the rule 36(f) contamination in SPP is ZERO.** Control
   (year-isolated, HEAD) − keeper (committed) is **0.0000 TWh** in 2019–2022 and **±0.0028 TWh** in
   2023–2025 — and that residue is a pure `COAL_PRB ↔ COAL_LIGNITE` reclassification summing to
   zero. §6.

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
~0. The seven control legs bought certainty that could not be had at zero LP given 8,701 changed
lines, plus the rule-36(f) measurement SPP owed. I would spend them again, and I am recording that
they turned out to be unnecessary.

**One shard stalled.** The first 2020 shard went idle between its two legs and never pushed; it was
relaunched and completed. No result was lost and nothing was salvaged from the stalled container.

---

## 2. THE PREDICTION SCORECARD — scored against what was pushed before the solve

| # | pre-registered | measured (7 yrs) | verdict |
|---|---|---|---|
| P-1 | coal **+0.849** TWh/yr, range 0.02–1.38 | **+2.205** (2.081–2.280) | **WRONG — 2.6× low, outside the range in EVERY year** |
| P-2 | wind **−0.6 to −0.9** TWh/yr | **−0.350** (0.000 to −0.589) | **WRONG — too large a shed predicted; 2019 is exactly 0.000** |
| P-3 | closes **~8.5 %** of C1 | **4.4 %** | right in kind, **half** the magnitude |
| P-4 | negative hours **UP** *(ADDENDUM revised to "doubtful, ~0")* | **+129 to +268, a doubling** | **ORIGINAL RIGHT; MY ADDENDUM REVISION WRONG** |
| P-4b | *(ADDENDUM)* zero-coal hours "will largely REMAIN" | **41–290 → 0, eliminated** | **WRONG** |
| P-5 | C3a **DOWN** | \|error\| better in **6 of 7**; 2022 worse | **CONFIRMED** |
| P-6 | C3b **DOWN** | better in **6 of 7**; 2021 worse | **CONFIRMED** |
| P-7 | min price stays **−26.000** | **exactly −26.000**, both legs, all years | **CONFIRMED** |
| C8 | D-2 forced share ≪ 30 %, "loose bound 29.5–44.9 % will read lower" | **4.41–17.69 %**, D-2 verdict unchanged | **CONFIRMED** |

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
is still far too shallow: the arm's coal minimum is **0.15 %–2.53 %** of its own annual max against
the real SPP PRB fleet's **8.1 %–17.5 %**. The collapse is stopped, not the shallowness repaired.
R-bd (net-load ranking) is still the named successor, now for the **level**, not the reach.

---

## 3. What the mechanism did — arm minus control, one HEAD, TWh

| year | COAL_PRB | COAL_LIGNITE | CC_REGULAR | CT_PEAKER | ST_GAS | **wind** | solar |
|---|---|---|---|---|---|---|---|
| 2019 | +1.903 | +0.178 | −1.427 | −0.487 | −0.074 | **0.000** | 0.000 |
| 2020 | +1.950 | +0.308 | −1.146 | −0.633 | −0.292 | **−0.144** | −0.001 |
| 2021 | +1.923 | +0.293 | −0.940 | −0.514 | −0.106 | **−0.549** | −0.006 |
| 2022 | +1.896 | +0.326 | −0.919 | −0.522 | −0.157 | **−0.589** | −0.003 |
| 2023 | +1.876 | +0.272 | −0.839 | −0.549 | −0.220 | **−0.499** | −0.006 |
| 2024 | +1.964 | +0.316 | −0.837 | −0.807 | −0.255 | **−0.338** | −0.006 |
| 2025 | +1.996 | +0.236 | −0.855 | −0.679 | −0.299 | **−0.330** | −0.020 |

**THE ENERGY COMES FROM GAS, NOT FROM WIND.** Mean coal **+2.205 TWh**, mean wind **−0.350 TWh** —
**84 % of the coal gain is displaced gas.** In 2019 wind moves **exactly 0.000** and the whole
+2.081 TWh of coal is gas displacement.

**This is the load-bearing negative result for the curtailment hypothesis.** The lane was chartered
on the arithmetic identity that SPP's wind excess (+10.14 TWh) equals its fossil miss (−9.99 TWh).
A thermal floor does **not** convert one into the other: it moves the **coal/gas merit order** and
leaves the wind excess essentially intact (−0.35 of +10.14 = **3.4 %**).

---

## 4. Price — the half that works

| year | lw price ctl → arm | Δ | **h < $0 ctl → arm** | Δ | **actual RT h < $0** | slack ctl → arm |
|---|---|---|---|---|---|---|
| 2019 | 22.387 → 22.105 | −0.282 | 0 → 0 | 0 | 547 | 0 → 0 |
| 2020 | 20.378 → 19.714 | −0.664 | 41 → **170** | +129 | 936 | 0 → 0 |
| 2021 | 40.167 → 38.364 | **−1.803** | 243 → **511** | +268 | 1,108 | 0 → 0 |
| 2022 | 43.682 → 42.159 | −1.524 | 294 → **518** | +224 | 995 | 501.3 → **274.6** |
| 2023 | 25.766 → 24.681 | −1.085 | 237 → **489** | +252 | 992 | 0 → 0 |
| 2024 | 26.370 → 25.338 | −1.033 | 225 → **405** | +180 | 1,172 | 1,295.7 → **802.8** |
| 2025 | 30.323 → 29.064 | −1.258 | 176 → **401** | +225 | 1,018 | 240.6 → **76.9** |

`dump` is **0.000 MWh** in every leg of every year, the minimum price is **exactly −26.000** in
both legs of every year with a negative hour, and **slack FALLS** wherever it was non-zero — so the
arm adds no new forcing on either channel.

**C3a / C3b, scored with the scorer's own functions against the committed bench:**

| year | C3a ctl → arm (\|error\|) | status | C3b ctl → arm | status |
|---|---|---|---|---|
| 2019 | +7.4 % → **+6.0 %** | PASS → PASS | 0.125 → **0.114** | PASS → PASS |
| 2020 | +23.4 % → **+19.3 %** | FAIL → FAIL | 0.316 → **0.273** | FAIL → FAIL |
| 2021 | +7.5 % → **+2.7 %** | PASS → PASS | 0.213 → 0.245 | FAIL → FAIL *(the C3b regression)* |
| 2022 | −0.9 % → −4.4 % | PASS → PASS *(the C3a regression)* | 0.213 → **0.206** | FAIL → FAIL |
| 2023 | +2.5 % → **−1.8 %** | PASS → PASS | 0.177 → **0.166** | PASS → PASS |
| 2024 | +3.6 % → **−0.4 %** | PASS → PASS | 0.170 → **0.156** | PASS → PASS |
| 2025 | +6.0 % → **+1.6 %** | PASS → PASS | 0.196 → **0.159** | PASS → PASS |

**No criterion flips status in either direction.** The model is too EXPENSIVE in six of seven years
and the arm reduces that overshoot in every one of them; 2022, the one year the model was already
slightly cheap, gets cheaper. The 2025 C3b move is the largest and takes the keeper's tightest year
off the edge of its band.

### 4.1 The structural repair, which is the point under rule 1 `[R-STRUCT]`

| year | h with coal = 0, ctl → arm | coal min ÷ its own annual max, ctl → arm |
|---|---|---|
| 2019 | 0 → 0 | 0.0656 → 0.0648 |
| 2020 | **41 → 0** | 0.0000 → 0.0253 |
| 2021 | **248 → 0** | 0.0000 → 0.0193 |
| 2022 | **290 → 0** | 0.0000 → 0.0056 |
| 2023 | **207 → 0** | 0.0000 → 0.0149 |
| 2024 | **181 → 0** | 0.0000 → 0.0100 |
| 2025 | **151 → 0** | 0.0000 → 0.0015 |

The model no longer takes SPP's entire PRB fleet — must-run band included — to exactly 0.0 MW.
**Reported at full magnitude: the repair is incomplete.** The real fleet floors at **8.1–17.5 %**
of its own max; the arm reaches **0.15–2.53 %**. It removes the *impossible* state without
reproducing the *observed* one.

---

## 5. C1 — where it costs, reported at full magnitude

| year | Σ\|class error\| ctl → arm | Δ | fossil miss ctl → arm | closed | ST_GAS ctl → arm |
|---|---|---|---|---|---|---|
| 2019 | 32.476 → **28.477** | **−3.999** | −9.391 → −9.388 | +0.004 | −4.588 → −4.662 |
| 2020 | 38.485 → **34.639** | **−3.846** | −7.628 → −7.482 | +0.146 | −4.891 → −5.183 |
| 2021 | 28.639 → 30.280 | **+1.641** | −6.263 → −5.629 | +0.634 | −3.943 → −4.048 |
| 2022 | 33.344 → 36.565 | **+3.221** | −6.733 → −6.136 | +0.597 | −5.168 → −5.324 |
| 2023 | 26.512 → **25.436** | −1.076 | −8.727 → −8.220 | +0.507 | −5.062 → −5.281 |
| 2024 | 29.430 → **28.325** | −1.105 | −10.859 → −10.512 | +0.347 | −7.115 → −7.370 |
| 2025 | 36.639 → 38.542 | +1.903 | −9.199 → −8.838 | +0.361 | −8.655 → −8.954 |

**Mean fossil miss closed +0.371 TWh/yr of −8.400 = 4.4 %.** Summed |C1 error| improves in
2019/2020/2023/2024 and worsens in 2021/2022/2025 — **exactly the three years where COAL_PRB was
already LONG** (+5.178 / +7.855 / +3.606), so adding ~2.2 TWh of coal overshoots further. `ST_GAS`,
SPP's most persistent C1 row, gets **worse in all seven years**.

Under rule 1 `[R-STRUCT]` none of this is disqualifying — *"a real market behaviour stays in even
if it makes the fit worse"* — and the mechanism was chartered on the fleet fact, not the residual.
But it is reported as what it is: **this is not SPP's C1 closer, and in three of seven years it
moves C1 the wrong way.**

---

## 6. The rule 36(f) measurement SPP owed — contamination is ZERO

`control (year-isolated, HEAD)` − `keeper (committed, multi-year, warm-start ON)`, TWh:

| year | COAL_PRB | COAL_LIGNITE | every other class |
|---|---|---|---|
| 2019 / 2020 / 2021 / 2022 | 0.0000 | 0.0000 | 0.0000 |
| 2023 | +0.0028 | −0.0028 | 0.0000 |
| 2024 | −0.0023 | +0.0023 | 0.0000 |
| 2025 | −0.0021 | +0.0021 | 0.0000 |

Rule 36(f) states the artifact's size in SPP is **UNMEASURED**. It is now measured: **zero to
within a ±0.003 TWh `COAL_PRB ↔ COAL_LIGNITE` reclassification that sums to 0.0000.** This
simultaneously bounds **HEAD drift** — 8,701 changed lines across 62 solve-path files move SPP's
backcast by nothing. **SPP's keeper and rung carried no cross-year contamination and needed no
re-solve on rule 36's account.** No other ISO's lane is implicated (rule 25 `[R-ISO-SCOPE]`).

---

## 7. Governance

* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`:** zero new fields, zero new free parameters —
  **machine-confirmed**, `build_dof_ledger.py --iso SPP` emits **5 entries / 3 residual** on both
  bundles with the same five entry names as keeper 12's. `offer_curve_by_group` is **byte-identical**
  to keeper 12's in both (SHA-256 `090abd79…`), so the rule-1 authorized price-tuning channel was
  not touched, re-cut or swept. Both gates were already registered `ScenarioConfig` booleans with
  CLI flags.
* **Rule 23 `[R-FROZEN-DERIVE]`:** `thermal_tranches_SPP.csv` is **read, never regenerated** — no
  derive script ran in this lane.
* **Rule 20 `[R-FORCED-BUDGET]` / C8:** D-2 `coal_mustrun` forced share **4.41–17.69 %** against the
  30 % merchant cap. D-2's `passed` verdict is **identical in control and arm** in all seven years
  (2022 fails in BOTH — pre-existing). The control carries **no `coal_mustrun` row at all**,
  confirming SPP had zero coal floors. Class under budget, so rule 20's conditional-pass escalation
  is not triggered and no `D4_WINDOWS` entry is owed.
* **Rule 19 `[R-ONE-MECH]`:** SPP's first commitment floor — replaces nothing, stacks on nothing.
  Reconciled with the already-armed `vre_curtailment_oversupply_allocation` as SPP-51c required.
* **Rule 25 `[R-ISO-SCOPE]`:** per-run CLI, SPP only, **no code changed**, so every other ISO is
  byte-identical by construction. PJM's and MISO's verdicts on this family were **not** transferred
  (rule 28(d)).
* **Rule 22 `[R-C3C]`:** the incoming keeper reads **CALIBRATED** with a single ledgered C3c caveat
  — the same determination and the same lone blemish as the outgoing keeper.
* **Rules 32/34/36:** parent ran no LP; one shard per year; each shard pushed its **full** bundle
  including `dispatch/<year>_P1.parquet`, verified by the parent with `git ls-tree` before any
  archive (rule 34(d)).
* **`[R-HOLDOUT]` removed:** no year is protected, so every number here is model-**SELECTION**
  evidence and none of it is a certified out-of-sample skill claim.

---

## 8. Successors

* **R-bd — the floor's LEVEL at the bottom, via a net-load ranking.** The arm's coal minimum is
  0.15–2.53 % of its own annual max against the real fleet's 8.1–17.5 %. `fleet/arrays.py:2884-2903`
  ranks the top-k window on **system load**; the physically right driver is **net** load, and it
  regenerates forward (more wind → lower net load → more cycling), so it is rule-13 admissible.
  **Not done here** because that function is shared and PJM/MISO runs arm this family — it needs
  its own gate and its own PRECOMMIT.
* **R-ba — the ST_GAS / CT_PEAKER merit-order inversion**, now with **new evidence against
  deferring it**: this arm makes ST_GAS worse in all seven years. It is untouched by this object and
  is the strongest remaining C1 candidate.
* **R-be — the price floor below −26 is structurally unreachable.** Model minimum is exactly
  `−ira_ptc_wind` = −26.000 with `dump_cost ≈ 26.001` capping it; the market goes below −26 in
  22–118 h/yr.
* **The wind excess itself remains open and is NOT closed by this lane.** −0.350 of +10.144 TWh is
  3.4 %. The `vre_reference_rate_curtailment_grossup` cell stays `U`.

---

## 9. The promotion, as executed

**Owner ruled PROMOTE in session.** Order followed per rule 35 `[R-PROMOTE]` (e) — promote, verify,
then delete:

1. **Year union enumerated BEFORE any prune** (35(b)): **2019–2025, seven years**, the union of
   `2026-09-16-spp-42-commitment-feasibility` (2023–2025) and
   `2026-09-19-spp-49-benchmark-membership` (2019–2022).
2. **Incoming keeper registered and verified present** — `2026-09-20-spp-51-coal-sync`
   (2023–2025, **CALIBRATED**, one ledgered C3c caveat) plus `2026-09-20-spp-51-syncfloor-rung`
   (2019–2022) stamped to it under rule 30 `[R-TOUCHPOINT-FOLD]` (a), so **the incoming keeper
   covers the full union** (35(c)) and no year drops off SPP's report.
3. **`scripts/audit_keepers.py` run between the promotion and the prune** (35(e)).
4. **Outgoing keeper and rung pruned** through `scripts/prune_iso_runs.py --iso SPP` (35(a)),
   SPP only.

**Why two registered runs rather than one seven-year bundle:** SPP's keeper and rung carry
genuinely different configs (`mid_vintage_exit_carry` is True on the rung, default-False on the
keeper), so composing all seven years into one bundle would manufacture a config partition SPP does
not have. Each composite carries **one** config internally, which is why no
`stamp_config_partition.py` call is owed here — unlike the MISO case the compose script is adapted
from.
