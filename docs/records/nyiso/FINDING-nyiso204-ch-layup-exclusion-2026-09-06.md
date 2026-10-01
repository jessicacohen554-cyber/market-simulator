# FINDING — nyiso-204: the Capital_Hudson lay-up exclusion **DOES NOT GO**. Phase 0 refuses it twice over — the two candidates *run on the limb's own hot hours*, and the exclusion would strip 65 % of a correctly-floored plant's commitment to remove 200 MWh

**Session:** nyiso-204, NYISO backcast calibration. **Branch:**
`claude/nyiso-204-capital-hudson-layup`, fresh off `main` `5375be8b`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — unchanged by this
session.

**ZERO LP WAS SPENT.** Rule 29 step 0 did exactly what it exists to do: the arm was killed before
it reached a solve. No screen year was pre-registered, because there is no solve to pre-register
for; the statements the charter asked the PREREG to carry are made in §0.1 below instead.

Instruments, both committed and re-runnable:
`scripts/probes/_nyiso204_ch_layup_phase0.py` → `results/calibration/_nyiso204_ch_layup_phase0.json`
(the redistribution) and `scripts/probes/_nyiso204_ch_hotday_driver.py` →
`results/calibration/_nyiso204_ch_hotday_driver.json` (the rule-17 driver test).

---

## 0. Verdict in one paragraph

The proposed arm — add Danskammer 2480 and Roseton 8006 to the `exclude_plant_codes` column of the
Capital_Hudson `ST_GAS` `tmax 31.1` row — is **refused on two independent grounds, either of which
is sufficient**. **(1) The criterion does not hold on this limb.** The exclusion's whole warrant is
that these plants are economically laid up, so a floor binding them is binding a plant its own
driver evidence says is offline. Measured against *this limb's own driver* — zone TMAX > 31.1 °C —
that is false: Roseton runs **56.0 / 70.8 / 79.4 %** of flagged hours at **160 / 287 / 281 MW**
mean, and on the hours the floor actually binds it is **ON** (P(on) 1.000 at 261.6 MW in 2023,
0.625 at 123.8 MW in 2025). Danskammer is weaker but unmistakably heat-responsive, running
**16.4 → 27.0 → 44.0 %** of flagged hours against **2.8 → 3.4 %** of the year, at up to 322 MW.
**(2) Even if the criterion held, the mechanism would move the defect, not remove it.** Under
`cheapest_first` the limb sizes a *zonal* target `0.0973 × Σ available capacity`; the two candidates
are **59.7 %** of Capital_Hudson `ST_GAS` nameplate, so excluding them cuts the target by ~60 % and
the limb's floor energy by **64.8 / 46.5 / 65.0 %** — while the candidates were absorbing only
**3,015 / 189 / 1,365 MWh**. **96–99 % of the change lands on Bethlehem 2625**, a plant that runs
76.8 / 85.0 / 96.2 % of flagged hours and whose conduct nobody has questioned. The cure is 8× to
186× the disease and lands on the wrong plant.

**This also corrects the premise the charter and nyiso-203b §1.3 carried forward** — that 2480 and
8006 "QUALIFY a fortiori" against Port Jefferson 2517. The a-fortiori ordering was computed on
*annual* online share (2.9 % / 14.6 % vs 38.6 %). Conditioned on the driver the limb actually gates
on, **it inverts**: Port Jefferson's hot-day conduct was P(on) 0.932, and Roseton's is 0.56–0.79 —
the same order of magnitude, not a weaker case. §3.2 states this against interest.

---

## 0.1 The statements the charter asked the PREREG to carry

- **THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0** on the keeper; C3c is the
  ledgered, non-downgrading caveat (rubric v3.3 / v3.6) and is **not** an objective. Nothing in this
  session was selected because a residual moved, and no criterion was hunted (rule 1 `[R-STRUCT]`).
- **MARKERS ARE NOT MINE.** `complete` and `frontier` re-entry are explicit **owner** acts. Neither
  marker was edited, prepared, or treated as earned. Card C-19 / Q51 stays parked.
- **The rule-23 `[R-FROZEN-DERIVE]` framing, had the arm gone:** no source data has updated and this
  would not have been a re-derivation. It would have been a **completeness correction** to an
  incomplete census — nyiso-140 censused Long_Island only, and its criterion had never been applied
  to Capital_Hudson — with the criterion and the channel both unchanged. **That argument does not
  get to be made, because §2 shows the criterion itself fails here and §1 shows the channel would
  not have preserved the coefficient's meaning.** The charter said: *"If you cannot make that
  argument stand on its own, the arm does not go."* It does not stand. The arm does not go.
- **Zero `ScenarioConfig` fields, zero DOF entries, zero `src/market_sim/` changes** were made. The
  only files this session adds are two probes, their two JSON outputs, and this finding.

---

## 1. Phase 0 (a)/(b) — the redistribution, measured on the shipped engine

**Method.** Rather than re-implement the limb's day gate, min-event bridging and cheapest-first
fill, the probe calls the **shipped engine** (`model.interchange.core.inject_reliability_floor`)
twice on the same reconstructed fleet — once with the keeper's specs, once with 2480 + 8006 added to
the target row's `exclude_plant_codes` — and diffs `min_gen`. The spec list is built through the
canonical solve-path sequence copied verbatim from `scripts/run_calibration.py` (overrides → drag →
obligation → exclusions), so the limb measured is the limb the keeper's own solve applied. The
redistribution is therefore exact by construction, not by my arithmetic.

**A bug I hit and fixed, recorded because the first numbers were wrong and I nearly believed them.**
`reconstruct_bundle_fleet` runs the solve path's preamble, which **already injects the reliability
floor** ("NYISO 2025: reliability floor — 3 enabled limb spec(s) applied"). `_distribute_group_floor`
composes through `np.maximum`, so re-running the engine on already-floored arrays can only *raise*
`min_gen`: the armed (lower) leg was silently masked and both legs returned byte-identical. The
first cut compounded that by *deriving* the "others" total by subtraction instead of measuring it,
which turned a no-op into a phantom **+3,015 MWh "redistribution onto others"**. Both are fixed —
`min_gen` is reset to `pmin` before each leg, and both sides are now read off the arrays — and the
corrected numbers below are the opposite sign of the phantom.

### 1.1 What the limb does, and what excluding the candidates does to it

| year | flagged h | target (mean/max MW) | floor energy base → armed | change | candidates absorbed | **others** |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 504 | 76.7 / 188.1 | 38,635.8 → **13,590.9** MWh | **−64.8 %** | 3,015.1 → 0 | 35,620.7 → **13,590.9** (−22,029.8) |
| 2024 | 432 | 175.5 / 243.5 | 75,831.3 → **40,602.0** MWh | **−46.5 %** | 189.1 → 0 | 75,642.1 → **40,602.0** (−35,040.2) |
| 2025 | 600 | 150.7 / 236.9 | 90,432.1 → **31,631.7** MWh | **−65.0 %** | 1,365.2 → 0 | 89,066.9 → **31,631.7** (−57,435.2) |

**It is not a redistribution ONTO the other units — it is a de-flooring OF them.** Capital_Hudson
`ST_GAS` is 24 LP rows across three plants; the candidates hold **1,719.3 MW of 2,878.9 MW
nameplate = 59.7 %**. Because `_distribute_group_floor` sizes `target = frac × avail_cap[rows].sum(0)`
over the **post-exclusion** rows, removing them removes ~60 % of the target's own base. The fill was
landing almost entirely on Bethlehem 2625 (the cheapest rows, heat rate 10.70–11.13), so 2625 is
where ~96–99 % of the loss lands:

| year | 2625 floor energy base → armed | share of the total change |
|---|---:|---:|
| 2023 | 35,620.8 → 13,590.9 MWh | 88.0 % |
| 2024 | 75,642.2 → 40,602.0 MWh | **99.5 %** |
| 2025 | 89,066.9 → 31,631.7 MWh | **97.7 %** |

### 1.2 Why that is a coefficient change by the back door (rules 21 / 23)

`floor_pct = 0.0973` is `commit_frac 0.8105 × min_stable_pct 0.12`, identified on n = 65
observations of the **whole class**. Under `pro_rata` — nyiso-140's limb — that coefficient is a
*per-unit* share, so dropping a unit changes membership and nothing else, and nyiso-140 explicitly
verified the coefficient survived (*"Basis-matched hourly p25 excluding 2517 = 0.2666 vs the frozen
0.2620, so floor_pct is UNCHANGED and no free parameter is added (rule 21 `[R-DOF]`)"*).

Under `cheapest_first` the same number multiplies a **zonal aggregate**. Editing the aggregate's
membership rescales the delivered commitment MW by ~60 % **without touching the number and without
any re-derivation** — the delivered target falls from a 76.7–175.5 MW mean to roughly 40 % of that.
That is precisely the kind of silent re-scaling rules 21 `[R-DOF]` and 23 `[R-FROZEN-DERIVE]` exist
to prevent, and it is why the precedent's "membership-only, zero-DOF" framing does **not** carry
across the distribution change. **The precedent transfers in criterion and not in mechanism, exactly
as the charter warned — and the mechanism is where it breaks.**

---

## 2. Phase 0 (d) — the rule-17 `[R-FLOOR-WINDOW]` driver test, which refuses the arm on its own

Rule 17 requires the exclusion be argued against **this limb's** driver. `tmax 31.1` is a
design-cooling-day commitment, so the claim that must hold is *"a laid-up plant does not commit on
hot days either."* nyiso-140 does not supply it — its own Port Jefferson **ran on hot days**
(P(on) 0.932 at TMAX ≥ 30 °C, mean 166.2 MW) and was moved *into* the temperature limbs for exactly
that reason. A plant can be laid up on the year and still be precisely what a hot-day step is for.

Measured on the limb's own gate (zone TMAX > 31.1 °C), CAMPD unit-level hourly `grossLoad`:

| year | plant | | flagged h P(on) | flagged mean MW | flagged max MW | all-year P(on) | all-year mean |
|---|---|---|---:|---:|---:|---:|---:|
| 2023 | **8006 Roseton** | cand | **0.560** | **160.1** | 924.0 | 0.086 | 23.8 |
| 2023 | **2480 Danskammer** | cand | 0.164 | 16.5 | 158.0 | 0.028 | 2.3 |
| 2023 | 2625 Bethlehem | ctrl | 0.768 | 379.1 | 1,161.0 | 0.226 | 111.4 |
| 2024 | **8006 Roseton** | cand | **0.708** | **287.1** | 684.0 | 0.083 | 29.2 |
| 2024 | **2480 Danskammer** | cand | 0.270 | 24.8 | 179.0 | 0.026 | 2.3 |
| 2024 | 2625 Bethlehem | ctrl | 0.850 | 621.9 | 1,169.0 | 0.268 | 154.8 |
| 2025 | **8006 Roseton** | cand | **0.794** | **281.2** | 759.0 | 0.270 | 82.7 |
| 2025 | **2480 Danskammer** | cand | 0.440 | 39.3 | 322.0 | 0.034 | 3.2 |
| 2025 | 2625 Bethlehem | ctrl | 0.962 | 561.9 | 1,047.0 | 0.404 | 235.3 |

**Roseton is not laid up with respect to this driver in any year**, and the gap between its flagged
and annual conduct (0.560 vs 0.086; 0.794 vs 0.270) *is* the temperature response the limb exists to
represent. **Danskammer is heat-responsive too** — 5.9× / 10.4× / 12.9× its annual online rate on
flagged hours, reaching 322 MW. Excluding either from a hot-day step removes a unit from the one
limb its conduct actually supports: the mirror image of the nyiso-140 error, not its analogue.

### 2.1 On the *binding* hours — the exact D-4 statistic, kept separate rather than conflated

The step flags a whole hot day for the zone, but cheapest-first only *binds* a given unit once the
cheaper rows are exhausted, so "flagged" and "binding" are different questions:

| year | plant | binding h | P(on) on binding h | mean MW |
|---|---|---:|---:|---:|
| 2023 | 8006 | 24 | **1.000** | 261.6 |
| 2023 | 2480 | 192 | 0.000 | 0.0 |
| 2024 | 2480 | 24 | 0.000 | 0.0 |
| 2025 | 8006 | 24 | **0.625** | 123.8 |
| 2023/24/25 | 2625 | 288 / 408 / 576 | 0.962 / 0.850 / 0.974 | 459.9 / 621.9 / 548.2 |

Two different things are true and both are reported:

- **For Roseton the exclusion premise is simply false.** The floor binds it in hours it is running at
  124–262 MW; there is no manufactured energy to remove. Its D-4 2025 row is not a lay-up defect.
- **For Danskammer the D-4 row is real** — the floor does bind it in hours it is off — **but "laid
  up" is the wrong diagnosis.** It answers the hot-day driver; what puts a floor on it in hours it
  is off is the *cheapest-first fill order* reaching down the merit stack within a correctly-flagged
  window. Excluding it as laid-up would mis-describe the plant **and** trigger §1's 60 % collapse.

**So the D-4 rows this arm was aimed at are not a membership defect at all**, and the already-armed
membership channel is the wrong instrument for them.

---

## 3. What this closes, and what it does not

### 3.1 Leg (a) is NOT reachable this way

nyiso-203b §1.3 concluded that excluding 2480 + 8006 would remove the 2023 2480 row, the 2024 2480
row (the only `ST_GAS` D-4 failure that year) and the 2025 8006 row, "leaving 2023's 8906 row as the
sole material `ST_GAS` provenance failure". That arithmetic is right about the *rows*; it is the
*route* that fails. Neither plant may be excluded from this limb, so **leg (a) stays open** and the
cheapest route to it named in nyiso-203b is closed. The card
`DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md` remains **UNRULED**; nothing here rules it.

### 3.2 A correction to nyiso-203b, recorded against interest

nyiso-203b §1.3 — and the charter for this session, which carried it verbatim — stated the verdict
**a fortiori**: *"2480 and 8006 have every cell at a zero median AND are online 2.9 % / 14.6 %
against 38.6 % for the plant the owner already excluded, so they cannot be closer calls than the
adjudicated case."* That reasoning is sound on the statistic it uses and **wrong on the statistic
this limb gates on.** Port Jefferson's 38.6 % is an *annual* share; its *hot-day* conduct was
P(on) 0.932. Against that comparand Roseton's 0.560 / 0.708 / 0.794 is the same order of magnitude,
and the ordering that made the case "a fortiori" disappears. The census in
`_nyiso203_d4_layup_census.json` is not wrong — it answers "is this plant laid up on the year?"
correctly. It is the wrong question for a `tmax` step, and this session did not notice that until
the driver test was run.

### 3.3 Deliberately not attempted

- **Re-deriving `floor_pct` on the reduced base** so the delivered target survives the exclusion.
  That is a re-derivation with no source-data trigger (rule 23) and it would need its own
  identification and an owner ruling; it is also moot while §2 stands.
- **Switching the limb to `pro_rata`** so exclusion becomes membership-only. That is a mechanism
  change, not a membership correction, and `cheapest_first` vs `pro_rata` was already adjudicated on
  the NYC limb (nyiso-203: pro-rata **REFUTED** there, ratios 1.22 / 1.25 / 0.57). Not this
  session's to take.
- **Anything aimed at C3b-2024** (0.185 against ≤ 0.20, the model's tightest margin). It was watched,
  not targeted, and no arm reached a solve so it cannot have moved.
- **Astoria 8906 / Saranac 54574** — closed negative three times over and untouched here.
- **Measuring unit-grain C8 for any ISO other than NYISO** (rule 25 `[R-ISO-SCOPE]`).

---

## 4. The successor this measurement actually points at

Stated as a diagnosis, **not** proposed as an arm and **not** pre-registered:

The Capital_Hudson `ST_GAS` D-4 failures are a **fill-order** phenomenon, not a membership one. The
limb correctly flags hot days and correctly sizes a zonal commitment; what it does not do is stop
the cheapest-first fill from reaching a unit that is offline in that particular hour, once the
cheaper rows are capped. In 2023 that put 192 binding hours on Danskammer at P(on) 0.000 while
Bethlehem — running at 459.9 MW mean — was already floored. Any real repair lives on the
*distribution* side (who the zonal target lands on within a correctly-flagged window), and that is a
mechanism question requiring an owner ruling, not a data edit to a membership column.

**The magnitudes are worth stating plainly before anyone spends a solve on it:** the whole defect is
**0.0014 + 0.0002 + 0.0010 TWh** across three years. Rule 20 `[R-FORCED-BUDGET]`'s escalation leg
(a) fails 2024 on **200 MWh**. That is what makes this cell so easy to get wrong — the temptation is
to reach for the cheapest instrument that clears the row, and the cheapest instrument here would
have cost 35 GWh of correctly-floored commitment at the wrong plant.

---

## 5. Governance

| item | state |
|---|---|
| **LP spent** | **none.** Rule 29 step 0 killed the arm pre-solve; no screen year needed pre-registering because no solve was reached |
| **Rule 29(b) G-DRIFT** | **re-validated empirically, not by reading hunks**, as the charter requires: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run at this HEAD leaves `git diff` **CLEAN** — the committed `_nyiso198_rebuild_checks_2024.json` regenerates **byte-identically**. That is what underwrites every phase-0 number here, since all of them come off the same `reconstruct_bundle_fleet` path. *(That probe prints its own `"VERDICT": "STOP"` — the nyiso-198 duct-peaking gate for `cc_duct_peaking_row_scoped`, a different and already-adjudicated arm marked `R` on the matrix. It is part of the committed record and reproduces unchanged; it is **not** a drift signal and nothing here re-opens it.)* |
| **Keeper** | `2026-09-06-nyiso-202-startup-aware`, **unchanged**. No promotion, no re-stamp, no `build_status` / `prune_iso_runs` / gate-(a) re-key owed |
| **Markers** | untouched. `complete` / `frontier` re-entry are owner acts; NYISO stays in `withdrawn` |
| **Rule 1 `[R-STRUCT]`** | no mechanism selected on a residual; NYISO reads fails 0 and none was hunted |
| **Rule 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** | zero fields, zero DOF entries, zero re-derivations; §1.2 is the reason the arm would have breached them |
| **Rule 25 `[R-ISO-SCOPE]`** | NYISO only; no other ISO measured |
| **Rule 26 / 28** | NYISO matrix shard cell updated **in this session** with the rejected outcome, per duty (b) |
| **Rule 15** | nothing registered — no run finished. Git history + this finding are the record |
| **Files added** | 2 probes, 2 JSON outputs, this finding. No `src/market_sim/` change, no CSV edit |

### 5.1 Reported, not fixed — and the charter's expectation is CORRECTED

The charter listed **6 pre-existing failures** at HEAD (`test_forecast_xyear_warmstart_flag.py::
TestFieldRegistration::test_default_cache_key_unmoved` plus four in
`tests/scoring/test_ff_readiness_battery.py`), confirmed at nyiso-203. **Measured at this
session's HEAD (`5375be8b`), five of those six now PASS** — `main` has moved since nyiso-203
(the capx D65-B-R key-pin repair landed in that window). Across all three named files this
session measures **1 failed / 48 passed**, not 6 / 43. Reporting what I measured rather than
repeating what I was told.

**The one that remains is the main-side regression another lane owns**, exactly as the charter
described it:

```
tests/scoring/test_collate_scenario_campaign_common_set.py::
  TestScnCampaignLoadRegression::test_the_repair_holds_over_the_whole_committed_tree
AssertionError: np.float64(101.96690000000001) != 18.83 within 3 places
                (difference 83.1369)
```

`STATUS_COMMON_SET_MT = 18.8300` is a literal at `test_collate_scenario_campaign_common_set.py:247`.
The charter's reading — the SCN-WS5A-LOAD lane landing CAISO as the sixth ISO without updating that
constant — is consistent with the shape of the miss (a whole additional ISO's emissions delta added
to a common-set total). **Not fixed from this lane**, per the charter and rule 25 `[R-ISO-SCOPE]`:
it is neither NYISO's file nor NYISO's number, and silently re-baselining another lane's regression
constant is precisely how a real regression gets buried. Reported for its owner.
