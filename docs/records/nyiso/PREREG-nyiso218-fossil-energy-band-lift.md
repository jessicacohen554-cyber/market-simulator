# PREREG nyiso-218 — the +3.0 % fossil ENERGY-band offer lift (owner rulings R1/R2, 2026-09-07)

**Session:** nyiso-218, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-hr6c08`, on `main` at `bfbb0b6a`. **Date:** 2026-09-07.
**Keeper (and G-CTRL form-4 control):** `2026-09-07-nyiso-213-summer-seam`, bundle
`results/calibration/nyiso213_summer_seam`.
**Instruments:** `scripts/probes/nyiso218_offer_lift_phase0.py` (zero-LP phase 0, ALREADY RUN —
see §0), `scripts/probes/nyiso218_screen_gates.py` (the screen scorer, written before the screen
solves).
**Machine record of phase 0:** `results/calibration/_nyiso218_offer_lift_phase0.json`.

**THIS COMMIT IS PUSHED BEFORE THE SCREEN SOLVE RUNS.** Every prediction in §5 and every gate in
§6 is written here first and is not edited afterwards. A gate that misses is reported as a RESULT,
never restated.

---

## 1. What this session is, and what it is not

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED**, grade 7/8,
**zero** failing criteria across 2023–2025, with C3c the lone ledgered caveat. Nothing here is a
"fix a failure" session. It executes an **OWNER-DIRECTED price-level move through the rule-1
`[R-STRUCT]` authorized channel**, and then opens a named structural object (the hydro shape
residual, §8).

### The two owner rulings that scope it (2026-09-07, the nyiso-217 sitting)

> **(R1)** SCOPE = THE THREE ENERGY BANDS ONLY. Multiply `committed`, `econ_low` and `econ_high`
> by EXACTLY 1.03 on every fossil group in NYISO's `offer_curve_by_group`. EVERY `peak` BAND IS
> FROZEN AT ITS CURRENT VALUE.

> **(R2)** SCREEN ON ONE YEAR FIRST, then decide.

R1 is a deliberate override of the naive "uniform" reading, taken to keep the standing DO-NOT-REDO
line intact: CC_REGULAR `peak` 2.25 does not move (nyiso-194 killed 2.25→2.50 on shape; nyiso-195
killed the econ ramp DOWN to its phys basis on direction; `phys_peak == peak`). Neither do 4.0
(CT_PEAKER), 4.2 (ST_GAS) or any other `peak`. `phys_*` (measured physics) and the structural
shares (`econ_low_share`, `pct_peaking`) are untouched — rule 1 forbids both absolutely.

### The channel is the only admissible one, and every condition binds

Rule 1 `[R-STRUCT]`'s 2026-09-05 carve-out and rule 13 `[R-MEASURED]`'s single exception:

* **(a)** `offer_curve_by_group` band multipliers ONLY. A fuel-price rescale is **forbidden** —
  nyiso-216 established the NYISO zonal gas basis is MEASURED and CORRECT and is not the defect,
  and rule 13 forbids rescaling a measured input so the output lands on actuals. No adder, offset,
  haircut or load proxy, however motivated.
* **(b)** ONE CONFIG ACROSS EVERY SCORED YEAR. A per-year value is per-year fitting and is refused.
* **(c)** **3.0 % IS SET EX ANTE AND IS FROZEN.** It is declared here before the solve and is
  **NEVER SWEPT** against the gates — no 2 % / 3 % / 4 % ladder, no keeping the one that passes.
  **If 3.0 % misses, that is the result.**
* **(d)** Merit-order change across classes is an INTENDED effect, not a defect.
* **(e)** The run's attestation must carry the `authorized_price_tuning` block naming the channel,
  the value, the band scope and both owner rulings (C6 FAILS without it), and the multiplier is a
  **free parameter in the DOF ledger** (rule 21 `[R-DOF]`) whose identification source is
  *"price residual, authorized channel (rules 1/13 amendment 2026-09-05; band scope + screen
  order, owner rulings 2026-09-07)"* — **not** a measured source. Per rule 21's R-AY
  cross-reference its presence does not by itself make the residual it closes an open root-cause
  issue, and no gate moves.

### Rule 22 `[R-HOLDOUT]` — the sharpest constraint here

The owner's stated motivation is *"bring 2022 into the 10 % range"*. **2022 is a validation
holdout. It may MOTIVATE — that is exactly rule 22's touchpoint loop step 2→3, diagnose on the
touchpoint, re-train on 2023–2025, re-test — but it is NEVER THE TARGET, it is never gated on, and
no number is identified against it.** The determination is the **TRAIN-TIER (2023–2025) verdict and
nothing else** (rule 30(c) `[R-TOUCHPOINT-FOLD]`); a held-out year can neither certify nor
decertify. The screen year is not 2022 under any circumstance. 2022 appears in §0 and §5 as a
**reported projection on an already-spent rung read from its COMMITTED sidecar**
(`nyiso213_tp2022`, stamped) — no new 2022 solve, no new 2022 score, and no gate.

---

## 2. Environment, provenance and the pre-existing baseline (all re-measured, none inherited)

| item | measured this session |
|---|---|
| `main` at session start | `bfbb0b6a` (the handoff named `12e71b89`; four commits landed since) |
| keeper `cache_key` at HEAD, **live** `ScenarioConfig.cache_key()` | **`95d4d8d167373eb7`** — unchanged from `71e62675` / `12e71b89`; capx D79's solve-surface fingerprint has not moved NYISO's key |
| keeper mode / hindcast | `mode="backcast"`, `hindcast=False` → `capacity_screen_peak_measured_hindcast` coerced to the frozen `False` |
| `gas_offer_net_revenue_margin` | **True**, anchor **3.9046 $/MMBtu** — this is the single most important fact in §0 |
| fleet instrument validation | `nyiso196_rebuild_checks.py --year 2024` exit **0**, `git status --porcelain -uno` **EMPTY** (byte-identical reproduction) |
| named pre-existing test set | `test_gate_a_provenance` · `test_cc_summer_derate_reconciled_basis` · `test_holdout_render_parity` · `test_campd_bins` · `test_bench_stamp_ast` → **84 passed, 2 skipped, 0 FAILED** |

**A correction to the handoff, measured not assumed.** The handoff records **1 pre-existing
failure** in that set (`test_gate_a_provenance::test_live_board_passes`, SPP's superseded keeper).
At this HEAD it **PASSES**: `main` moved and SPP's board is consistent again. The set is clean, so
any failure I introduce is mine.

---

## 3. §0 — EVERYTHING ALREADY IN HAND before the predictions in §5 were written

Rule 29 `[R-SCREEN]` step 0 legitimately precedes this PREREG; a PREREG that hides its priors is
weaker evidence. The complete list:

**Carried in from the handoff (not measured by me):**

* **C-1** C3a `price_mean` model/actual: 2022 71.01/81.12 = **−12.46 % FAIL**; 2023 33.65/32.25 =
  **+4.34 % PASS**; 2024 40.15/38.12 = **+5.33 % PASS**; 2025 61.58/66.43 = **−7.30 % PASS**.
* **C-2** C3b `price_shape` (bar ≤ 0.20): 2022 **0.229 FAIL**; 2023 0.122; 2024 **0.179**; 2025 0.160.
* **C-3** C3c: CAVEAT in all four years (ledgered; rule 22 standing rule + rubric v3.6).
* **C-4** C2 sysvol gas: 2022 / 2023 / 2024 PASS; 2025 SKIPPED (preliminary EIA-923 vintage).
* **C-5** The keeper's band table, and that NYISO coal is 0.0 TWh in every year.
* **C-6** nyiso-217's closures, nyiso-216's, nyiso-215's, and the DO-NOT-REDO list.

**Measured by me in phase 0, BEFORE §5 was written:**

* **C-7 — the effective curve carries 13 fossil groups**, not the 8 the handoff lists:
  `CC_CHP`, `CC_INTERMEDIATE`, `CC_REGULAR`, `COAL`, `COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`,
  `COAL_WC`, `CT_CHP`, `CT_INTERMEDIATE`, `CT_PEAKER`, `ST_GAS`, `ST_GAS_INTERMEDIATE`.
  All 13 are lifted (39 band values), including the coal groups the handoff calls inert.
* **C-8 — `ST_CHP` is FOSSIL and has NO `offer_curve_by_group` entry at all**, so the authorized
  channel **provably does not reach it**. Reported here rather than discovered later; it is not a
  gap I may close by inventing an entry (that would be a new tuning channel, rule 24 `[R-REGISTRY]`).
* **C-9 — three of the eight gas groups are NEVER RESOLVED in this keeper.**
  `cc_intermediate_split`, `ct_intermediate_split` and `st_gas_intermediate_split` are all
  **false**, so `CC_INTERMEDIATE` / `CT_INTERMEDIATE` / `ST_GAS_INTERMEDIATE` are unreachable;
  the five coal groups carry 0.0 TWh. Phase-0 Part A confirms it by execution: the **moved set is
  exactly `{CC_CHP, CC_REGULAR, CT_CHP, CT_PEAKER, ST_GAS}`** in every year. The other eight are
  lifted for config uniformity and are inert.
* **C-10 — THE CENTRAL STRUCTURAL FACT, and it breaks the handoff's arithmetic.** The keeper arms
  `gas_offer_net_revenue_margin` at a **3.9046 $/MMBtu anchor**. Under it a tranche's cost is
  `phys × HR_base × fuel(t) + markup_hr × anchor` where `markup_hr = max(0, mult − phys) × HR_base`
  (`offer_curves.apply_gas_offer_margin`, applied upstream of the `fleet_only` exit). So a +3 %
  band lift becomes a **fixed $/MWh margin at the anchor**, `+0.03 × mult × HR_base × anchor` —
  **not** a 3 % proportional scaling of marginal cost. Two consequences, both measured:
  (i) the absolute price response is nearly YEAR-INVARIANT while the percentage response shrinks
  as the price level rises; (ii) bands whose registered bid sits **below** their measured `phys_*`
  clip to zero markup both before and after the lift (`CC_CHP.committed` 0.90 vs `phys` 1.210;
  `ST_GAS.committed` 1.05 vs `phys` 1.104) and move only through the fuel-scaled multiplier form.
* **C-11 — the phase-0 offer-array construction check PASSES in all four years**:
  `peak` rows moved **0**, `mustrun`/`sync` rows moved **0**, non-fossil rows moved **0**; the
  moved bands are exactly `{committed, econlo, econhi, econ}`.
* **C-12 — the phase-0 price-setting census and passthrough prediction** (§4 table).
* **C-13 — the phase-0 instrument reproduces C3a's committed model statistic** to
  **±0.006 $/MWh** in all four years (33.648 / 40.148 / 61.586 / 71.007 against the payload's
  33.65 / 40.15 / 61.58 / 71.01), so the prediction is on the criterion's own basis.
* **C-14 — the hydro §8 measurement** (model vs EIA-930 `NG: WAT`), carried in from the handoff.

---

## 4. G-CTRL is form 4, and G-DRIFT validates it — NO CONTROL SOLVE IS SPENT

Rule 29(b): the keeper's **COMMITTED** bundle is the control. The code question — "did anything on
the backcast solve path move since the keeper's `git_sha`?" — is answered by a **code-level drift
audit at zero LP cost**, recorded here before the arm solves.

`git diff 51f2fc2d bfbb0b6a -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
→ **26 files**, and every hunk classifies **INERT** for a NYISO `mode="backcast"` run:

| files | classification | reason |
|---|---|---|
| `constants.py` (SPP_GAS_BRIDGE_*), `floor_mechanisms.py`, `pipeline/commitment.py`, `pipeline/__init__.py`, `pipeline/year.py`, `runner.py`, `run_calibration.py`, `run_calibration_full.py`, `solve_surface_declared.py`, `scripts/lib/confirmed_retirements/spp.py`, `data/_validation-source/*SPP*` | **INERT** | SPP-44 bridge wiring + SPP-42 coal identity. Every entry point gates on `iso == "SPP"` and on `spp_gas_commitment_bridge`, a new field with dataclass default `False`, declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` and **absent from the keeper recipe**. |
| `pipeline/backcast_config.py` | **INERT** | the only hunk is the `_SPP_OFFER_CURVE` coal refactor, inside `if iso.upper() == "SPP"`. |
| `config/constants.py` (CAISO nuclear 2022), `fuel_trajectories.py` (CAISO carbon 2022), `model/interchange/spec.py` | **INERT** | caiso-262 2022 rows in CAISO-keyed dicts. |
| `data/fuel/__init__.py`, `data/fuel/basis/__init__.py`, `data/fuel/basis/ercot.py` | **INERT** | ERCOT `ercot_zonal_spread_ep_referenced` (new field, default `False`, declared, absent from the keeper recipe) and its ERCOT-only basis branch. |
| `config/scenarios.py` | **INERT** | exactly three new fields: the two above, plus `capacity_screen_peak_measured_hindcast` (capx D76 Q58) whose `__post_init__` **coerces back to the frozen `False` whenever `not config.hindcast`** — and this keeper is `hindcast=False`. |
| `results/cache.py`, `pipeline/persist.py` | **INERT** | a re-key ledger docstring, and an additive `environment.cache_key_path_roots` record block that `cache_key` never reads. |
| `scripts/lib/key_provenance.py` | **INERT** | new file, imported only by `scripts/check_key_provenance.py`; not on the solve path. |
| `data/raw/_validation-source/caiso-supply-consistent-demand/*` | **INERT** | CAISO artifacts. |
| `data/eia930/actuals.py` | **INERT** | **unchanged since `12e71b89`** (`git diff` empty), and nyiso-217 discharged it for the benchmark, fleet and VRE-profile paths alike. |

**Corroborated by execution, not only by reading:** the keeper's own `scenario_config` hashes to
**`95d4d8d167373eb7`** under the LIVE `cache_key()` at this HEAD — the same key it carried at
`71e62675` and `12e71b89`. **All hunks INERT ⇒ form 4 is valid and no control solve is earned.**

---

## 5. §5 — THE PREDICTIONS. Written before the screen solved, and not edited afterwards

### 5.1 The measured phase-0 passthrough (Part B), on C3a's own basis

The marginal tranche is identified two ways, both reported: **`inzone`** (best `mc_base` match among
rows in the zone whose price is being set — the physically-grounded identification, since a unit
must be deliverable to the zone it prices) and **`system`** (best match among all rows — a
robustness check that ignores deliverability and inflates its own match rate by enlarging the
candidate pool). Predicted Δ is the demand-weighted mean of the matched tranche's own Δmc,
aggregated exactly as `score_price_mean` aggregates: zonal demand-weighted mean price, then
weighted across zones by zonal demand.

| year | fossil energy-band price-setting share (inzone / system) | predicted Δ mean price $/MWh (inzone / system) | as % of level |
|---|---|---|---|
| **2023** | **0.7815** / 0.7954 | **+0.6418** / +0.6715 | +1.91 % / +2.00 % |
| 2024 | 0.7315 / 0.7803 | +0.6384 / +0.7259 | +1.59 % / +1.81 % |
| 2025 | 0.6368 / 0.8148 | +0.6609 / +0.8665 | +1.07 % / +1.41 % |
| *2022 (motivation only, not a target, not a gate)* | *0.7478 / 0.7431* | *+0.8511 / +0.8410* | *+1.20 % / +1.18 %* |

### 5.2 THE SCREEN YEAR IS **2023**, and it is chosen by footprint, never by residual

The declared criterion is the handoff's literal one — **the year with the largest fossil
energy-band price-setting share** — read under the **`inzone`** identification, which is chosen on
*identification validity* and not on the year it produces: the marginal unit setting a zone's price
must be deliverable to that zone, whereas `system` matching searches all ~810 rows and therefore
reports a 91–99 % "clean match" partly as an artifact of pool size. Under it:
**2023 (0.7815) > 2024 (0.7315) > 2025 (0.6368) ⇒ screen year 2023.**

**Stated in place because it cuts against a residual-selection reading rather than for it:** 2023
is the **SMALLEST**-|residual| training year (+4.34 %), so this choice cannot be residual-driven.
And stated in place because it cuts the other way: under the `system` mode the ranking inverts to
2025 (0.8148), which is also the largest-|residual| year, and the predicted **absolute** Δ is
largest in 2025 under both modes. A reader preferring either of those statistics would screen 2025.
I am naming the criterion and the mode here, before the solve, precisely so that choice is not
available to me afterwards.

### 5.3 Sign and magnitude predictions, INCLUDING ONE THAT HURTS THE PREFERRED ANSWER

* **P1 (construction — ALREADY MEASURED, reported not predicted).** The offer-array delta is
  exactly zero on every `peak`, `mustrun`, `sync` and non-fossil row, and non-zero only on
  `committed`/`econlo`/`econhi`/`econ` rows of the five reachable groups. **FIRES** in all four
  years (C-11). A non-zero peak delta would have been a stop-the-line construction bug.
* **P2 (direction).** The screen year's measured Δ load-weighted mean price is **positive**.
  A raise-only lift on the price-setting classes cannot lower the mean. **Falsified by** any
  negative or zero measured Δ.
* **P3 (magnitude).** The measured Δ on 2023 lands in **[+0.32, +1.34] $/MWh** — the ex-ante
  ×0.5…×2.0 window on the two phase-0 predictions (+0.6418 / +0.6715). **Falsified by** anything
  outside it. This is the gate that tests whether the mechanism does what its own arithmetic says.
* **P4 (the year-invariance signature — THE PREDICTION THAT HURTS).** Because the margin is
  anchored (C-10), the effect is a near-constant **$/MWh**, not a constant **%**. I predict the
  realized Δ is **larger in absolute $ in 2025 than in 2023** and yet **smaller as a percentage**.
  This hurts the preferred answer directly: it means the lift buys the LEAST relative correction
  exactly where the residual is most negative, and it is why §5.4 projects what it projects. If
  instead the realized response is ≈ +3 % of the price level in every year, **my whole reading of
  the mechanism in C-10 is wrong** and I will say so.
* **P5 (confinement).** The aggregate annual energy of the five moved classes does not **rise**,
  total system generation is conserved to within 0.5 %, and `ST_CHP` — fossil but unreachable by
  the channel (C-8) — moves by no more in absolute TWh than the moved-class aggregate.
  **Falsified by** any of the three.

### 5.4 THE PROJECTED C3a, STATED BEFORE THE SOLVE — INCLUDING THAT IT PROBABLY MISSES THE MOTIVATION

Applying §5.1's predicted Δ to the committed C3a means (inzone / system):

| year | keeper C3a | projected model | actual | **projected C3a** | verdict |
|---|---|---|---|---|---|
| 2023 | +4.34 % | 34.29 / 34.32 | 32.25 | **+6.33 % / +6.42 %** | inside ±10 % |
| 2024 | +5.33 % | 40.79 / 40.88 | 38.12 | **+7.00 % / +7.23 %** | inside ±10 %, **the tightest** (~2.8 pp of headroom) |
| 2025 | −7.30 % | 62.24 / 62.45 | 66.43 | **−6.31 % / −5.99 %** | inside ±10 % |
| *2022 (motivation, NOT a target)* | *−12.46 %* | *71.86 / 71.85* | *81.12* | ***−11.41 % / −11.42 %*** | ***STILL OUTSIDE ±10 %*** |

**So the headline pre-solve statement, made here rather than after the fact: on the measured
arithmetic, +3.0 % on the three energy bands does NOT bring 2022 into the ±10 % band.** It closes
about **1.05 pp of a 2.46 pp gap**. The value is nevertheless frozen at 3.0 % under condition (c)
and **will not be re-picked** — sweeping it to find the value that clears 2022 is exactly the
fitted-mechanism selection rule 1 exists to forbid, and doing it against a *held-out* year would
additionally breach rule 22. If the owner wants a different value, that is an owner act taken on
the passthrough ratio this session reports, not a search I run.

The handoff's own arithmetic risk note assumed **~1:1 passthrough** (2024 → ~+8.5 %). **That
assumption is measured false here** — the realized passthrough is ~0.53–0.67 of it, for the
structural reason in C-10 — which is why 2024's headroom is ~2.8 pp rather than ~1.5 pp, and why
2022 does not close.

---

## 6. §6 — THE SCREEN GATES. STRUCTURAL, STOP-ONLY, AND NONE IS GATED ON C3a

Scored by `scripts/probes/nyiso218_screen_gates.py` on ONE instrument against the keeper's
committed bundle (G-CTRL form 4). **The screen may KILL the arm; it may NEVER promote one**, it
contributes to no determination, and **it is never gated on the target residual** — a screen that
reads "did C3a improve" is fitted-mechanism selection done one year at a time.

* **S-1 — recipe identity.** The arm's `scenario_config` differs from the keeper's ONLY in
  `offer_curve_by_group`, and there in **exactly 39 band values** (13 groups × 3 energy bands),
  every one at a ratio of **exactly 1.03** (|ratio − 1.03| ≤ 1e-9). Any other live field, any
  moved `peak`/`phys_*`/share, or any count ≠ 39, **FAILS** — instrument invalid, not a result.
  The `--year` selection keys `weather_year` / `gas_price_override` are excluded, and that
  exclusion set is closed.
* **S-2 — passthrough direction and order of magnitude.** P2 ∧ P3: measured Δ positive AND inside
  [+0.32, +1.34] $/MWh. **FAIL kills the arm.**
* **S-3 — footprint confinement.** P5's three limbs, all required.
* **S-4 — no NON-TARGET load-bearing criterion flips PASS → FAIL.** Gated on **C1, C2, C4** only,
  as the handoff enumerates. **C3a, C3b and C3c are REPORTED at full magnitude and gate nothing** —
  C3a because it is the target; **C3b because it is a price-LEVEL-family criterion moved by the
  same authorized channel, so gating on it would make this a price gate through the back door.**
  That is a stated decision, not an omission, and C3b's 2024 margin (0.179 against a 0.20 bar) is
  reported whatever it does. C8 is **NOT COMPUTABLE** for an unregistered screen bundle (it needs
  `legitimacy_diagnostics.json`, written only by the register path) — reported, never faked; the
  arm moves no floor, share or availability, so the forced VOLUME is untouched by construction.
* **S-5 — the price tail, REPORTED ONLY.** Never a gate: C3c is the standing ledgered caveat.

### The outcome partition — EXHAUSTIVE, with the closure attached to each branch

Let **K** = "S-1 or S-2 or S-3 or S-4 fails".

* **(A) K is true — SCREEN KILLS THE ARM.** Report the kill as the session's result. **Do not
  spend the remaining years. Do not re-pick a value.** Report the measured $/MWh-per-1 %-band
  passthrough ratio per year so the owner can choose the next value from evidence, as an owner act.
* **(B) ¬K, and the full span lands with 2023/2024/2025 all inside ±10 % on C3a.** Keeper
  candidate. D-5(b) attaches: re-verify the determination **artifact-only**
  (`calibration_verdict.py --run-id`, never a solve) BEFORE re-keying `complete.NYISO.keeper`; a
  **worse** determination STOPS the promotion and escalates (Q5). Then re-test 2022 by replaying
  the NEW keeper recipe, register, stamp
  (`stamp_touchpoint_holdout.py --run-id <tp> --keeper-id <new>`), `build_status.py --iso NYISO`,
  and re-key forecast gate (a) — ALL IN THE SAME PR.
* **(C) ¬K, the span lands, but a TRAINING year goes out of band on C3a** (2024 is the named
  risk). The arm is **NOT** a keeper; the keeper stays at `2026-09-07-nyiso-213-summer-seam`;
  report at full magnitude with the passthrough ratio. **Do not search for a value that threads
  both.**
* **(D) ¬K, the span lands, every training year in band, but a NON-C3a criterion regresses out of
  band on the full span** (the screen year cleared but another year did not). Same disposition as
  (C): not a keeper on my recommendation, reported at full magnitude, and the decision goes to the
  owner — rule 31 `[R-RETAIN]` forbids me from acting on my own not-promotable reading by
  destroying the evidence.
* **(E) The screen or span cannot be solved at all** (environment, OOM, a driver refusal). Report
  what blocked it and what was and was not established. No number is guessed.

**A gate that lands in a gap between these branches is a RESULT and will be reported as the
defect, not papered over** (the nyiso-215 P2 and nyiso-217 P3 standard).

---

## 7. Rule 31 `[R-RETAIN]` and rule 29(c) — how the bundles are handled

The screen bundle `results/calibration/_nyiso218_screen_2023/` (and any full-span bundle) is
**`.gitignore`d in this commit, before it is written.** That discharges rule 29(c) in full — the
duty is to keep it out of `main`, never to erase it from disk — and it satisfies rule 31: nothing
is deleted until the owner has ruled on promotion. Every number this session will ever cite from a
screen bundle is written into the PREREG/FINDING, so the record is the doc.

**This container is ephemeral.** Any un-promoted bundle sits on local disk only and will not
survive session reclamation; the final report states the promotion question explicitly.

---

## 8. Step 2 — the declared successor object (hydro shape), scoped here, not prejudged

Measured from committed artifacts (model = keeper `hourly/class_hourly_<yr>.parquet` P1
`klass == 'hydro'`; actual = EIA-930 `NG: WAT`): volume error −2.18 / −0.82 / −0.15 / −0.19 % in
2022–2025 while hourly **r** sits at **0.694 / 0.677 / 0.757 / 0.723**. Purely a **shape** defect,
**flat across all four years** (so 2022's 0.694 is not a 2022 effect), identifiable **entirely on
the training tier with ZERO rule-22 exposure**. Basis verified, not assumed: NYISO is in neither
`EIA930_PS_FOLDED_INTO_WAT` nor `EIA930_PS_SPLIT_COMPLETE_FROM`, so `NG: WAT` is
conventional-hydro only and Blenheim-Gilboa is booked under the model's `storage` klass —
conventional-only on both sides.

The question is **not** "arm the hydro shape mechanism": `hydro_dispatch_envelope`,
`hydro_min_flow_floor` and `nyiso_hydro_reserve_eligible` are **already armed** in the keeper,
`hydro_ror_split` is **G** (governance-refused, nyiso-111) and `hydro_budget_nameplate_aware` is
**I** (provably inert, nyiso-107) — none may be re-tested without new evidence. The question is
**why r stays at ~0.7 with all three armed**, and it is nyiso-92's residual, not a fresh failure.
Rule 13's forward test — *"could this same quantity be produced for a forward year from forward
drivers, and would it respond to changed conditions?"* — is applied in writing to any successor
construction, and rule 14 cuts both ways: a more accurate hydro shape that makes the PRICE fit
worse stays, and the worse fit becomes a root-cause question.

---

## 9. Rule 28 `[R-MECH-MATRIX]`

The band multipliers are registered on the `offer_curve_by_group` **base row**, not a row of their
own. NYISO's shard cell for that row is re-stamped in the same session the lift is tested,
whatever the verdict.
