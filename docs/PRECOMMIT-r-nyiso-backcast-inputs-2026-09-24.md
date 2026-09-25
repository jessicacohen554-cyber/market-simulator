# PRECOMMIT — R-NYISO: re-solve NYISO on corrected backcast inputs (EIA-860 vintage, plant heat rates, CAMPD outages) — 2026-09-24

**Session:** R-NYISO (ORCHESTRATOR, rule 32 `[R-SHARD]` (a): this container runs no LP).
**Charter:** `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.3.6.
**Owner instruction (2026-09-24, verbatim, from the audit):** *"every backcast year 2019–2025 runs on
the year-correct EIA-860 vintage, plant-specific heat rates (never the asset-class table), and granular
CAMPD outage data."*
**Precondition:** MET. F1 (#6572) and F2 (#6569) are both merged; this lane is cut from
`9210075392a128d14a5efb168ab1f9955a9b6946` (main after both merged).
**Incumbent:** `2026-09-22-nyiso-hydro3-ror-split` (bundle `results/calibration/hydro3_nyiso_ror_span`,
solved at `57e3c77f`, registered 2022–2025).
**Phase-0 evidence (zero LP, committed with this doc):** `scripts/probes/_rnyiso_phase0_census.py` →
`results/calibration/_rnyiso_phase0_census.json`.

---

## 0. Headline, fixed before any solve

1. **The recipe is the incumbent keeper's recipe, replayed at HEAD. Nothing is tuned.** The offer-curve
   multipliers (`offer_curve_overrides`, `offer_curve_deltas`, every band) are byte-identical to the
   keeper's (rule 1 `[R-STRUCT]` (c): an input correction is never re-tuned against the gates).
2. **What changes is F1 alone** (G-DRIFT, §3): the year-matched EIA-860 vintage and the
   measured coal / ST / CC heat rates switch ON (CT and CHP were already on and now read per-year rows).
   **F2 changes nothing NYISO reads**: the armed std extract is byte-identical to the keeper's.
3. **Years solved: 2022, 2023, 2024, 2025** — exactly the ISO's registered year set (rule 35 (b)), so
   nothing shrinks.
4. **Years NOT solved: 2019, 2020, 2021 — DATA-BLOCKED on two inputs, both still absent at HEAD.**
   This is not a benchmark gap: NYISO LBMP actuals and EIA-930 fuel mix exist for all three years (§5).
   The two missing inputs are an all-ISO shared artifact and a NYISO-only intake. Neither can be
   worked around without changing the recipe for those years, and a per-year recipe variant is refused
   (§5). They are routed as intakes, not attempted.

## 1. The recipe

`scripts/replay_keeper.py results/calibration/hydro3_nyiso_ror_span --years <Y>` plus these explicit
overrides, which make the F1 posture visible in `run_config.json`. They only restate the HEAD backcast
defaults and have no other effect:

```
--set eia860_vintage_tracks_solve_year=true
--set measured_coal_heat_rates=true
--set measured_st_heat_rates=true
--set measured_cc_heat_rates=true
```

`measured_ct_heat_rates` and `measured_chp_heat_rates` are already `true` in the keeper's recipe and stay
so.

**Arms from the charter, and what happens to each:**

| charter item | disposition | reason |
|---|---|---|
| ADD measured ST, CC (F1) | **ON** (default + explicit `--set`) | F1 default; artifacts now exist for NYISO (`campd_{st,cc}_heat_rates_NYISO.csv`, 10 ST / 14 CC plants) |
| measured coal | **ON** | F1 default. It reaches only 2019 (Somerset, 676 MW) and the canonical 2025 snapshot's zero-availability coal (§2) |
| rule-19 precedence vs the eGRID repairs | **CONFIRMED, NO CODE CHANGE** | §4. One plant overlaps (Bethlehem 2539), and there the measured CC row is a steam-metering artifact that its own per-year guard refuses in 6 of 7 years. The existing order already lands the correct rate |
| perunitmerithour std extract (2019–26) | **ARMED, unchanged** | sha256 `ee778a87…aa21fa`, byte-identical to the keeper's `resolved_inputs` |
| short-coal (`unit_outage_short_windows`) | **stays I, not armed** | `campd-unit-outages-short-NYISO.csv` has 0 data rows at HEAD (F2 §2: no NYISO coal passes the baseload guard in 2019–2025). The I verdict (nyiso-93 / nyiso-173) was measured on the file, not on heat rates, so D1/D2 does not contaminate it |
| short-gas (`unit_outage_short_windows_gas`) | **stays I, not armed** | The nyiso-227 I verdict is a HEADROOM census on the 2023–2025 keeper: ST_GAS binds in 0 of 8,760 h with 1.3–2.2 GW of unused headroom. Those years ran on the canonical snapshot, where NYISO thermal was 6 % class-table, not the 100 % D1 vintage state. So the evidence is not D1-contaminated and there is no new evidence to re-test (rule 28 (a)). F2's new `-shortgas-NYISO` file (149–206 windows/yr) is reported in §2 but not consumed |
| unit partial-derate (`unit_partial_outage_windows`) | **NOT armed; cell is I, not U** | The charter lists it as U, but the NYISO shard records it under the `unit_outage_short_windows` row, measured I (nyiso-173 §2.1). `campd-partial-outages-NYISO.csv` is still header-only at HEAD (F2 §2, 0 windows 2019–2025). Arming it would change the key for zero behaviour, so it is left off |

## 2. Phase-0 census (zero LP, `run_year(fleet_only=True)` on the keeper recipe)

`pre` = the six F1 flags forced to the keeper's posture (canonical 2025ER snapshot, CT + CHP measured
only). `post` = HEAD defaults, i.e. exactly what a shard solves. 2019/2020 were built with
`--diagnostic-solar-substitution`, which the thermal fleet does not read (§5).

**(a) EIA-860 vintage resolved**

| year | pre | post |
|---|---|---|
| 2019–2024 | canonical `eia-860` (2025ER + COD ramp) | `vintage_<Y>` |
| 2025 | canonical | canonical. There is no `vintage_2025`; it joins eGRID 2024 |

**(b) Thermal MW, and MW priced at a `HEAT_RATE_BINS` class-table value** (the audit's §3a heuristic,
tranche-weighted)

| year | thermal MW pre → post | class-table MW pre → post |
|---|---|---|
| 2019 | 28,203.5 → 26,689.8 | 295.6 → **0.0** |
| 2020 | 28,199.8 → 26,865.7 | 291.8 → **18.4** |
| 2021 | 28,201.4 → 26,950.4 | 295.7 → **35.1** |
| 2022 | 28,218.9 → 26,896.6 | 295.7 → **50.6** |
| 2023 | 28,218.9 → 26,522.8 | 295.7 → **50.6** |
| 2024 | 28,226.3 → 26,556.4 | 299.4 → **56.3** |
| 2025 | 28,226.3 → 28,226.3 | 299.4 → 299.4 |

**Residual class-table plants, post, 2022–2024:** every one is a fuel cell or a small behind-the-fence CT
with no eGRID heat rate in any vintage and no CAMPD stack: Lincoln Medical 4–6 MW oil; the SWM, Bloom
(Altice, Orbit), Sneden 18A/18B, Yates 3245, Certain Solar, Altice-Hicksville, Equinix and Apple Staten
Island fuel cells (1.6–7.8 MW each); Albany Medical Center cogen 3.7 MW (2024). **2025 adds** Hofstra
(2.0), General Mills (3.2), Iola (3.9) and **Dunkirk coal 234 MW**. The Dunkirk MW is inert, see the
coal note below.

**MW-weighted heat rate by class, post** (MMBtu/MWh, pre → post), where F1 moves it materially:

| class | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **ST_GAS** | **16.97 → 15.77** | **16.97 → 15.78** | **16.97 → 15.80** | **16.97 → 15.69** |
| CC_CHP | 9.88 → 9.66 | 9.83 → 9.65 | 9.94 → 9.98 | 9.94 → 9.94 |
| CC_REGULAR | 8.53 → 8.59 | 8.53 → 8.51 | 8.53 → 8.53 | 8.53 → 8.51 |
| CT_PEAKER | 14.55 → 14.61 | 14.56 → 14.68 | 14.62 → 14.77 | 15.02 → 15.02 |
| oil | 15.39 → 15.78 | 15.39 → 15.37 | 15.39 → 15.45 | 15.39 → 15.39 |

In 2019–2021, oil moves from 15.39 to 21.2–22.3 because the year-matched eGRID 2019–2021 rates apply to
low-CF oil peakers.

**Fleet composition moves** (pre → post MW, the largest):

- **COAL 1,487 → 0 in 2020–2024.** Somerset 676, Dunkirk 520 and Cayuga 291 had all retired by 2020.
  Under the pre-F1 canonical-plus-COD-ramp fleet they were present, and **the incumbent keeper
  dispatched 0.665 TWh of `COAL_PRB` in 2022** (from its committed `class_hourly_2022`). NYISO burned no
  coal in 2022, so that energy was phantom. The year-matched vintage removes it.
- **2019 COAL 1,487 → 804:** Somerset is still operating, correctly.
- **2025 COAL stays at 1,487 MW** (canonical snapshot) with **zero availability in every hour**
  (measured on `fleet_arrays`: 0.0 TWh available). It cannot dispatch. It is a residual of the canonical
  snapshot, reported here and not repaired by this lane.
- Cricket Valley 1,087 MW is absent in 2019 (COD 2020), correctly. Astoria GT oil 439 → 0 (2023–24).
  Gowanus CT 282 → 548–562. Sithe Independence 1,158 → 1,086. Nassau Energy 50 → 0 (2022–24).

**(c) CAMPD outage families** (windows starting that year / annual-mean MW removed)

| family | file | armed | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|
| std ≥ 5 d | `-perunitmerithour-NYISO` | **yes** (unchanged, sha256 `ee778a87…`) | 540 / 10,611 | 519 / 10,919 | 526 / 8,614 | 512 / 9,398 | 519 / 8,294 | 461 / 8,505 | 492 / 8,696 |
| lay-up | `-layup-NYISO` | yes (companion) | 430 / 2,328 | 332 / 1,420 | 411 / 2,723 | 317 / 1,488 | 389 / 3,116 | 404 / 2,396 | 353 / 2,313 |
| EIA-923 | `-e923-NYISO` | yes (companion) | — | — | 1 / 107 | — | — | 4 / 14 | — |
| short-coal | `-short-NYISO` | no (I) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| partial | `campd-partial-outages-NYISO` | no (I) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| short-gas | `-shortgas-NYISO` (new, F2) | no (I) | 149 / 206 | 188 / 285 | 146 / 243 | 206 / 372 | 136 / 208 | 133 / 192 | 169 / 281 |

## 3. G-DRIFT (rule 29 (b)), `57e3c77f` → `92100753`

Audit scope: `git diff 57e3c77f HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source
data/raw/reference`. That covers 28 files; `replay_keeper.py`, `_validation-source` and `reference`
have no diff. Each hunk is classified below.

- **LIVE BY DESIGN, F1:**
  - the six backcast-default flips plus the `__post_init__` coercion (`scenarios.py`);
  - `campd_bins._measured_rate_map` (solve-year row, else pooled);
  - `heat_rate_year` threading in `eia860.py` / `chp.py`;
  - the eGRID resolver (`data/egrid.py`), with the boundary repair now reading the active dir's vintage;
  - the retiree / mothball measured-HR kwargs (`run_calibration.py`);
  - the regenerated `vintage_2018…2024` and canonical EIA-860 parquets (canonical now joins eGRID 2024);
  - the NYISO measured artifacts: CT and CHP re-derived; CC, ST and coal new.
- **LIVE BY DESIGN, F2:** only `campd.ISO_MERIT_PANEL_STATES` (SPP / SOCO), which is **inert for
  NYISO**.
- **INERT:**
  - the new fields `coal_fuel_inventory_plant_grain`, `campd_dark_unit_year_windows`,
    `nwpp_grid_carried_wind_served` and `demand_balance_screen`: each defaults to False, is absent from
    the recipe and is not in the flip list;
  - the per-yard coal budget rows (`lp/rows.py`, `lp/model.py`, `pipeline/spec.py`,
    `coal_fuel_inventory.py`): gated on an unset budget;
  - SOCO-59/60 constants and BA recode, the RGGI tables, NWPP interchange, runner forecast paths and
    cache-ledger prose.
- **LIVE-OTHER: none.**
- **Benchmark-side, not solve-side:** miso-267 reordered `_benchmark_eia923_frame` (oil re-attribution
  first; negative rows; COD back-fill window). This can move NYISO's **scored C1 actuals**. The
  comparison in §6 therefore separates benchmark drift from solve drift. The old keeper's committed C1
  is reported as committed, and where it matters the keeper is re-scored on the HEAD benchmark
  (zero LP).

**Form 4 is valid: the incumbent's committed bundle is the control. No control solve is spent.**

## 4. Rule 19: measured CAMPD rates vs the eGRID repairs

**Load order at HEAD** (`fleet/eia860.py`):

1. the eGRID family rate (frame level);
2. the measured CT / coal / ST / CC swaps (row loop);
3. the measured CHP swap;
4. the eGRID identity swap;
5. the eGRID steam-collapse swap, which skips any generator repriced by CHP or identity and any
   family-covered plant.

**Overlap census, 2022–2025, identical every year:**

- measured CC ∩ identity (7784, 57664): **∅**;
- measured ST ∩ identity: **∅**;
- measured ST ∩ steam-collapse: **∅**;
- measured CC ∩ steam-collapse: **{2539 Bethlehem}**;
- measured CC ∩ family: {2500, 50292};
- measured ST ∩ family: {2490, 2500, 2511, 2516, 2517, 8906}.

In the family overlaps the measured class-scoped swap runs after the frame-level family rate, so
**the measured rate wins** there. That is the charter's intent.

**Bethlehem is the one plant where the measured rate must NOT win**, and the code already does the
right thing:

- **The measured CC per-year rows, 2019–2025, are refused by their own boundary guard in 6 of 7
  years.** 2019–2022 fail as `steam_not_metered`: the CAMPD-gross / EIA-923-net ratio is 0.66–0.82,
  i.e. the steam turbine is not in the meter. 2024–2025 fail as `boundary_above_band` (1.53).
- **The only `ok` year is 2023**, which is the vintage in which **EIA-923's steam-generator filing
  collapsed** (CA net 267,718 MWh, against 1.46–1.76 TWh in every other year). That is precisely what
  the eGRID steam-collapse mechanism (nyiso-189) was built for, so the 2023 denominator is itself the
  defect.
- **The pooled row passes (ratio 0.977) only because it averages the two failure directions**, giving
  9.18 MMBtu/MWh. That is a combustion-turbine rate presented as a CC rate: the plant's real rate is
  ≈ 6.9, and its own pre-collapse eGRID vintages 2018–2021 give PLHTRT 6.86–6.94.
- **Order today:** the steam-collapse swap runs last and 2539 is not in its skip set, so the solve gets
  **6.877**. The tranche-weighted post-F1 census reads 7.30–7.32 in every year.

**Changing the order to "measured wins" would inject a wrong 9.18–10.33 at an 813 MW CC.** Rule 14
`[R-ACCURATE]` keeps the accurate input, and rule 19 is satisfied: one rate per plant, set by one
mechanism. **No code change.** No other NYISO plant shows the pooled-passes-while-years-fail
pattern, in any of the CC / ST / CT / coal artifacts.

**Routed cross-ISO (F1 follow-up, not this lane):** the pooled row's boundary guard can pass by
averaging years that fail in opposite directions. An ISO whose eGRID repair does not cover such a
plant would apply the wrong rate.

## 5. Years 2019–2021: DATA-BLOCKED (named per rule 34 (c)), routed

Both blocks were first measured in `docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md` and
are re-measured unchanged at HEAD:

| year | binding input | status at HEAD | scope |
|---|---|---|---|
| 2019, 2020 | `data/raw/eia-930/eia_generation_profiles.parquet` starts at **2021** | Still absent. NYISO reports 0 solar to EIA-930 in every year, so its solar shape falls to this table's NEISO donor row, and that row does not exist before 2021. The donor's own hourly extract (`ISNE hourly`) does **not** reproduce the table: best r = 0.98 at a 2 h shift, not byte-identical. A substitute would be a different construction, not the same one extended | all-ISO shared artifact with **no producer script** (hand-assembled, per the eia-930 README) |
| 2019, 2020, 2021 | `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_<Y>.csv`, needed by `nyiso_dynamic_reserve_requirements` (armed) | Still 2022–2025 only. The mechanism refuses to fall back to static requirements *by design* | NYISO-only intake (Ask B) |

**Benchmarks are NOT the blocker.** `actual_lmp_hourly_NYISO.parquet` carries 8,760 h for every year
2018–2026. `NYISO/fuel-mix` and `interface-flows` carry 2018–2026. EIA-930 BALANCE carries 2019–2026.

**What is refused, and why:** running 2019–2021 with a substituted solar shape, or with
`nyiso_dynamic_reserve_requirements` disarmed. Either one is a per-year recipe variant, i.e. a
different model on those years. A held-out-year number built that way would be quoting a different
configuration.

**The route** is two intakes. Each must reproduce an existing year before it may emit a new one:

1. rebuild `eia_generation_profiles` 2019/2020, all ISOs, additively, 2021–2025 byte-identical;
2. extend the Ask-B NYISO reserve-requirement series back to 2019. The LRR regime before 2021-12-04
   differs (the SENY 30-min requirement was flat 1,300 MW, per the NYISO-AS README), and that has to
   be sourced, not assumed.

## 6. The solve and the checks, fixed before any number

**Shards (rule 36 `[R-YEAR-ISOLATION]`): four, one per year 2022 / 2023 / 2024 / 2025**, each pinned to
this document's commit SHA. Each runs the §1 command with `--out-dir results/calibration/rnyiso_<Y>`
and pushes its FULL bundle, including `dispatch/<Y>_P1.parquet`, to `claude/r-nyiso-<Y>` (rule 34 (a):
a `.gitignore` negation plus a plain `git add`). Both warm-start knobs are OFF (`replay_keeper` pins
them).

**Leg acceptance** (the parent refuses a leg that fails any of these):

- **S0, pin.** The leg's `run_config.json` `git.basis_sha` equals the pinned SHA and is not dirty.
- **S1, config signature.** `scenario_config` has `eia860_vintage_tracks_solve_year`,
  `measured_{ct,coal,st,cc,chp}_heat_rates` and `hydro_ror_split` all true, and
  `unit_partial_outage_windows`, `unit_outage_short_windows` and `unit_outage_short_windows_gas` all
  false. The offer-curve block (top-level `offer_curve_overrides` / `offer_curve_deltas`,
  and `scenario_config.offer_curve_by_group`, every band) is byte-equal to the keeper's.
- **S2, inputs.** `resolved_inputs.campd_unit_outages.sha256 == ee778a87…aa21fa` and
  `thermal_tranches.sha256 == a3bbd6ef…d8376`.
- **S3, fleet signature.** From `dispatch/<Y>_P1.parquet`: **zero COAL units in 2022–2024**, where the
  pre-F1 fleet had 27. In 2025 there are 27 COAL tranches and 0.0 MWh of COAL.
- **S4, hydro classifier.** 94 run-of-river / 70 reservoir (the keeper's).

**Reporting, all at full magnitude, per year, old keeper vs re-solve:**

- C1–C8 and the determination;
- class TWh deltas;
- price MAE and bias;
- the §2 census deltas.

**Pre-registered expectations**, stated so they cannot be written to fit the result:

- **ST_GAS** heat rate falls about 1.2 MMBtu/MWh (−7 %) in every year, so ST_GAS gets cheaper and
  **its dispatch should rise**. 2023 ST_GAS already sits past the C1 share edge (+3.61 TWh, +3.0 pp).
  **C1 is therefore expected to stay FAIL or worsen in 2023** and may cross into other years.
- **2022 COAL_PRB falls 0.665 → 0 TWh.**
- **No gate is a stop condition.** This lane corrects inputs and does not select them. A gate that
  regresses is reported and root-caused (rule 14). It is **never recovered by re-tuning a multiplier**.
  Promotion is the owner's decision, and this session only asks it (rule 31).

## 7. Duties

- **Rule 15:** register the composed 2022–2025 run.
- **Rule 28 (b):** update the NYISO shard cells touched:
  - `eia860_vintage_tracks_solve_year` and `measured_{coal,st,cc}_heat_rates`, which are exercised by
    solve for the first time;
  - `unit_outage_short_windows` and `_gas`, re-confirmed I with the F2 coverage;
  - the Bethlehem precedence note on `egrid_steam_collapse_heat_rates`.
- **Rule 33:** archive each shard once its bytes are verified here.
- **Rule 33 (f):** what must survive lands on `main`.
- **Rule 31:** **ASK the promotion question.** This session never promotes and never prunes.
