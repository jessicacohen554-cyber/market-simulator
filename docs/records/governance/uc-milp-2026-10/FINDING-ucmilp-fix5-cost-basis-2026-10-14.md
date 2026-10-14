# FINDING — UC-1-FIX-5: the UC cost basis double-counts no-load (candidate defect 7) — **confirmed; fixed in uc-1.5; the CAISO 2023 repro recovers 5.3 of 8.2 TWh of CC**

Lane UC-1-FIX-5 (Opus), 2026-10-14, chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). Pin `a81b9683`; branch
`claude/ucmilp-fix5-cost-basis`. Phase 0 zero LP; one repro shard (CAISO 2023). Nothing registered, nothing deleted.
Scripts and readings: `data/fix5/` (`cost_basis_zero_lp.py` → `cost_basis_<iso>_<y>.json`; `double_count_usd.py` → `double_count_usd.txt`).

## 0. Answer

1. **Confirmed, from code.** The UC objective for an integer cluster is `nl·u + Σ mc_base·P`.
   - `mc_base` = tranche heat rate × fuel + VOM + emissions. The tranche heat rate is `base_hr × band` (`data/fleet/assembly.py`), and
     `base_hr` is an **average** operating rate (CAMPD heat input ÷ load). Every ISO solves on CAMPD bins; the bands are multiples of
     that average (`phys_committed` = `avg_committed_p50`; ERCOT's CC committed = DAM all-in Min Gen Cost).
   - An average rate at full output is `a/p̄ + b` (OLS identity). So the energy term already carries `a·P/p̄` of no-load heat, and
     `noload_cost_per_unit_h` adds `a·u` on top.
   - **Double count = `a·P/p̄`:** zero at P = 0, the whole no-load at full output.
2. **Size** (Σ `nl·P1/p̄`, from the bundles; every UC-armed ISO examined shows it, and the CC double count is 7–15 % of UC CC energy cost):

   | ISO-year (engine) | CC $M | % of UC CC energy cost | $/MWh | ST_GAS $M (%) | coal |
   |---|---|---|---|---|---|
   | CAISO 2023 (uc-1.4) | 307 | 12.4 % | 7.22 | 0.20 (6.7 %) | 0.47 (11 %), 1 cluster, 17 MW |
   | ERCOT 2019 (uc-1.4) | 148 | 7.2 % | 1.11 | 18.3 (4.7 %) | none (demoted, budget-pinned) |
   | MISO 2024 (uc-1.2) | 250 | 8.2 % | 1.65 | 28.2 (5.2 %) | none (demoted) |
   | NEISO 2019–25 (uc-1.4, UC-3-NEISO span) | 80–367 / yr (2023: 129) | 11.6–13.1 % | 2.39–10.22 (2023: 3.66) | ≈ 0 (≤ 0.06) | none |
   | NYISO 2021–25 (uc-1.4, UC-3-NYISO span) | 65–230 / yr (2023: 65) | 9.8–14.7 % | 2.35–7.30 (2023: 2.35) | 10–25 / yr (3.3–4.1 %) | none |

   For reference, the explicit no-load is 13.9–14.8 % of CAISO CC UC energy cost in every year 2019–25 (uplift sidecars). In ERCOT 2019 it is
   10.9 % (CC) and 13.5 % (ST), matching UC-BANDS-ERCOT §2. In MISO 2024–25 it is 9.4–10.1 %.
3. **Start cost: no double count on integer clusters.**
   - `UcStage.zero_markup` zeroes the P1 amortized start markup on every integer member, so start is paid once, in the UC.
   - The "startup proxy" committed bands are CT (non-integer) and ST. CT keeps the P1 markup and the proxy stacked together, but that is a
     pre-existing P1 issue already routed by UC-BANDS-ERCOT §2, not the UC.
   - ST's committed band is 0.81 (CAISO) / 0.91 (ERCOT), *below* the average rate, so it carries no start cost.
4. **Fix (rule 19, one place): `uc-1.5`.** Integer members' UC energy moves to the incremental basis:

   `mc_uc[g,t] = mc_base[g,t] − (a_c/p̄_c) · max(mc_base[g,t] − vom_g, 0) / hr_g`

   (`UcClusterParams.incremental_energy_cost`). The explicit no-load stays.
   - Effect: at full output the UC cost equals the as-offered curve. Below full output it adds the measured part-load penalty
     `a·(1 − P/p̄)`.
   - Fuel-free or part-passthrough tranches lose proportionally less.
   - The same array is the uplift cost side and the pre-fixing anchor cost.
   - P1 is untouched (pure LP on the bid curve). There is no new field, no new tunable and no derive re-run.
   - The mechanism matrix gets no row, because no ScenarioConfig field was added.

## 1. Cost per MWh against fuel truth (zero LP)

Per unit-hour, on each bundle's own P1 offers and no-load $. Values are capacity-weighted over integer clusters with a regression no-load.
- **Truth** = `(a + b·P)·p_eff + vom·P`: the CAMPD per-unit OLS line (2023–25, the derive's screen), slope included. `p_eff` is the
  cluster's own $/MMBtu.
- **P_hi** = top of the non-peak curve. ERCOT's 2019 ×151 peak tranche would otherwise swamp a full-output average.

| ISO · class (mlf, a/p̄ MMBtu/MWh, b/avg) | point | truth | uc-1.4 (avg + NL) | drop NL (option A) | **uc-1.5** |
|---|---|---|---|---|---|
| CAISO CC (0.23, 1.17, 0.81) | Pmin | 139.5 | 150.5 (+7.9 %) | 58.3 (−58 %) | **141.6 (+1.5 %)** |
| | P_hi | 62.9 | 75.9 (+21 %) | 60.4 (−4 %) | **67.0 (+6.5 %)** |
| CAISO ST_GAS (0.07, 0.65, 0.73) | Pmin | 305.3 | 326.4 (+6.9 %) | 86.6 (−72 %) | **321.6 (+5.3 %)** |
| | P_hi | 82.2 | 107.2 (+30 %) | 90.4 (+10 %) | **102.3 (+24 %)** |
| ERCOT CC 2019 (0.29, 0.95, 0.84) | Pmin | 24.2 | 25.3 (+4.9 %) | 11.7 (−51 %) | **24.1 (−0.4 %)** |
| | P_hi | 13.6 | 22.8 (+68 %) | 19.8 (+45 %) | **21.5 (+58 %)** |
| ERCOT ST_GAS 2019 (0.09, 0.64, 0.87) | Pmin | 74.7 | 78.2 (+4.6 %) | 28.8 (−61 %) | **76.7 (+2.6 %)** |
| | P_hi | 30.0 | 36.3 (+21 %) | 31.7 (+6 %) | **34.8 (+16 %)** |
| MISO CC 2024 (0.40, 0.72, 0.89) | Pmin | 24.9 | 27.1 (+8.9 %) | 19.3 (−23 %) | **25.3 (+1.4 %)** |
| | P_hi | 19.7 | 22.4 (+13 %) | 19.7 (−0.4 %) | **20.5 (+3.8 %)** |
| MISO ST_GAS 2024 (0.16, 0.72, 0.87) | Pmin | 63.6 | 67.1 (+5.6 %) | 30.1 (−53 %) | **65.3 (+2.8 %)** |
| | P_hi | 30.6 | 35.3 (+15 %) | 31.2 (+2 %) | **33.5 (+9.6 %)** |
| NEISO CC 2023 (0.34, 1.15, 0.79) | Pmin | 56.7 | 60.5 (+6.7 %) | 30.8 (−46 %) | **56.2 (−0.8 %)** |
| | P_hi | 36.7 | 42.5 (+16 %) | 32.8 (−11 %) | **38.3 (+4.3 %)** |
| NYISO CC 2023 (0.33, 1.47, 0.78) | Pmin | 61.7 | 66.1 (+7.2 %) | 23.6 (−62 %) | **60.5 (−2.0 %)** |
| | P_hi | 30.8 | 35.9 (+17 %) | 24.4 (−21 %) | **30.3 (−1.5 %)** |
| NYISO ST_GAS 2023 (0.11, 0.59, 0.87) | Pmin | 204.1 | 210.8 (+3.3 %) | 37.9 (−81 %) | **209.0 (+2.4 %)** |
| | P_hi | 48.8 | 55.7 (+14 %) | 38.1 (−22 %) | **53.9 (+10 %)** |

**Read.**
- **uc-1.5 is within 3 % of truth at Pmin everywhere** (CAISO ST +5 %).
- **What remains at P_hi is the band surface, not the cost basis:**
  - ERCOT CC econ_high is 1.324;
  - CAISO and MISO ST econ bands sit above the measured average;
  - P_hi excludes the 8–15 % peak share, so part of the part-load penalty is still there.

  The ERCOT band question belongs to UC-BANDS-ERCOT.
- **Option A (drop the explicit no-load) is refuted by the data.** The bands carry no part-load shape: CAISO CC committed is 1.0, against a
  measured average at LSL of 1.10. Dropping the no-load under-prices a unit held at Pmin by 23–72 %.
- **The regression identity holds.** `1 − (a/p̄)/avg` predicts the measured slope ratio:

  | ISO · class | predicted | measured |
  |---|---|---|
  | CAISO CC | 0.84 | 0.81 |
  | ERCOT CC | 0.88 | 0.84 |
  | MISO CC | 0.90 | 0.89 |

**NEISO (UC-DESK question, UC-3-NEISO PR #7244).** The double count works in the same direction as NEISO's decommitment, but it is a
different effect from the discrete-unit ceiling.
- **The double count:** it over-charges every online CC unit-hour by `a·P/p̄`. That is 12 % of UC CC energy cost, $3.66/MWh in 2023, and
  the largest share of any ISO measured here. Removing it makes holding a CC online cheaper.
- **The ceiling:** a multi-unit plant committed in whole units of `p̄` cannot carry the relaxed P1 part-load output. That is physical,
  and uc-1.5 keeps it.
- **The split between the two is unknown.** Neither part of NEISO's 6.6–9.0 TWh/yr can be attributed zero LP. Only a NEISO uc-1.5 leg can
  measure it; CAISO 2023 is this lane's one repro.

## 2. Why this form (the charter's decision rule)

| criterion | incremental via `a/p̄` (built) | CAMPD-slope column | drop explicit NL |
|---|---|---|---|
| measured | yes (uc-params `a`, fleet `p̄`, `hr`) | yes, but needs a new uc-params column and a re-derive | bands only; not measured part-load |
| consistent with P1's bid curve | yes: same band shape; equals P1's offer at full output | no: commits on cost and dispatches on bands | yes |
| truth at Pmin / P_hi | within 3 % / band residual | exact by construction | −23 to −72 % / ≈ |
| new field / tunable | none | a schema column | none |

## 3. G-OFF and G-DRIFT (zero LP)

- **G-OFF: INERT by construction.** Every changed hunk sits behind `unit_commitment_milp`:
  - `pipeline/uc.py` is imported only inside the armed branch of `pipeline/solve.py`, which is byte-identical;
  - `model/uc/params.py` gains a new method called only from the UC stage, the bench and uplift;
  - `model/uc/uplift.py` and `scripts/lib/uc_bench.py` are UC-only.

  The solve surface is unmoved, because no registry value changed. Fast lane: 11,694 passed, 0 failed.
- **G-DRIFT UC-3-CAISO pin `87c23363` → this lane:**
  - main `580c4fbf..a81b9683` adds only `scripts/data/derive_ercot_sced_uc_bands.py`, which is not on the solve path (INERT);
  - this lane's hunks are LIVE, gate-on only, and they are the fix under test.

  The UC-3-CAISO 2023 leg is therefore the control for the repro. The keeper `closeout_caiso_w1_a2_span` is the gate-off control.
- **Tests** (`tests/unit/model/uc/test_cost_basis.py`): 1 cluster, 24 h, known `a`/`b`. Unit cost equals fuel truth at Pmin and at Pmax; the
  full-output cost equals the as-offered curve; non-members and fuel-free rows are untouched; the solved window objective decomposes to fuel
  truth. `test_floor_merit_fill` uplift test re-based to `mc_uc`.

## 4. Repro shard — CAISO 2023, UC-3-CAISO arm, uc-1.5

**Run.** Shard `session_01AwFD64Q23SdKoDpzxuH4QN`, pin `f92d01ea181fbdeeda9532ed41ecc450fd6f1f20`, prompt
`data/fix5/shard-prompt-ucmilp-fix5-caiso-2023.txt`.
- **Bundle:** `claude/ucmilp-fix5-caiso-2023` @ `a2635bd6937522e2359cea0a90c8609305d21c48`, 20 files (108 MB). It includes
  `dispatch/2023_P1.parquet` and the four UC sidecars. `engine.version` reads `uc-1.5`.
- **Scoring:** the pin's `calibration_verdict.py` on the committed CAISO 2023 bench part. The leg was registered locally and the
  registration was removed before commit. The same path re-scores the UC-3 uc-1.4 leg to exactly its RESULT numbers.

| 2023 | keeper (control) | UC-3 leg, uc-1.4 | **FIX-5 leg, uc-1.5** |
|---|---|---|---|
| C1 CC_REGULAR (TWh, vs 51.84 actual) | 50.77, −1.07 PASS | 42.57, −9.27 **FAIL** | **47.88, −3.96 PASS** |
| C1 CT_PEAKER (vs 4.13) | 2.99, −1.14 PASS | 5.58, +1.45 PASS | **3.71, −0.43 PASS** |
| imports TWh (P1 class) | 34.31 | 39.42 | **36.24** |
| C3a load-weighted price (vs $54.17 RT) | $58.27, +7.6 % PASS | $63.17, +16.6 % **FAIL** | **$60.37, +11.4 % FAIL** |
| C3b monthly NRMSE | 0.117 PASS | 0.216 **FAIL** | **0.158 PASS** |
| C3c hours > $200 (vs 47) | 51 PASS | 88 PASS | **73 PASS** |
| C4 gas r / NRMSE | .912 / .235 PASS | .910 / .271 PASS | **.916 / .248 PASS** |
| C5a CO2 vs eGRID (reported) | −6.3 % PASS | −12.0 % FAIL | −8.7 % CAVEAT |
| CC_REGULAR starts, model / CEMS 3,222 | 9,528 (2.96×) | 2,306 (0.72×) | **2,521 (0.78×)** |
| CC energy in sub-min-up runs | — | 3.2 % | 2.3 % |
| uplift, $M (% of Σλ·load) | — | 20.7 (0.16 %) | 18.7 (0.15 %) |
| explicit no-load paid, $M | — | 357 | 481 (more units online) |
| windows Optimal / TL / infeasible | — | 365 / 0 / 0 | 365 / 0 / 0 |
| wall P0 / UC / P1 s (UC ÷ (P0+P1) + 1) | — | 499 / 2,372 / 658 (3.10×) | 502 / 1,919 / 662 (**2.65×**) |
| MILP s mean / p95; nodes p50 / p95 | — | 6.20 / 16.80; 1 / 57.8 | 4.95 / 9.37; 1 / 24 |
| peak RSS UC / cgroup GB | — | 7.52 / 8.51 | 7.53 / 8.54 |

**Read.** One year only, so this is a direction reading, not a verdict.
- **The fix moves CAISO 2023 back toward the control on every gate that uc-1.4 broke.**
  - CC decommitment shrinks from −8.2 to −2.9 TWh against the keeper, and C1 CC flips back FAIL → PASS.
  - Imports fall by 3.2 TWh and CTs by 1.9 TWh.
  - C3b flips back FAIL → PASS.
  - C3a recovers 5.2 of the 9.0 points the UC added, but is still FAIL at +11.4 %.
- **Starts stay physical:** 0.78× CEMS, against the keeper's 2.96×. The fix restores commitment without bringing back the bridge's cycling.
- **The fix is not the whole story.** The remaining +$2.1/MWh over the keeper, and the C3a FAIL, fit the UC-3 RESULT §2 reading:
  - the keeper's C3a pass depends on bridge-held CC;
  - the missing import-price object is a CAISO calibration-lane question.
- **Solve cost:** wall drops 3.10× → 2.65×, and no window hit the time limit.
- **Matrix and verdict:** no cell is stamped here. The CAISO `unit_commitment_milp` verdict is UC-3's A/B over seven years (PR #7243, uc-1.4).
  An uc-1.5 relaunch is the desk's call (D-6).

## Log entry

- 2026-10-14 · UC-1-FIX-5 · `claude/ucmilp-fix5-cost-basis` · defect 7 confirmed from code. The average-rate offer carries `a·P/p̄` of no-load
  that the UC also paid explicitly: CAISO 2023 CC $307 M (12.4 %), ERCOT 2019 CC $148 M (7.2 %), MISO 2024 CC $250 M (8.2 %). Start: no double
  count. Fix uc-1.5: integer members' UC energy less `a/p̄` heat; P1 untouched; G-OFF inert. CAISO 2023 repro (`a2635bd6`): CC
  −9.27 → −3.96 TWh (FAIL → PASS), C3a +16.6 → +11.4 % (still FAIL; keeper +7.6 %), C3b 0.216 → 0.158 (PASS), starts 0.72 → 0.78× CEMS,
  imports −3.2 TWh, wall 3.10 → 2.65×. NEISO and NYISO added to the no-load table at the desk's request.
