# RESULT: UC-MISO-VLR arm V, the VLR load-pocket commitment requirement replacing the ST_GAS per-plant floor

**Verdict: R** under PRECOMMIT §4.3 (kill #3). The year coverage is **2019–2021**. 2022–2025 are a **coverage gap**: no
container large enough could be obtained (§4). UC-DESK ruling (i), 2026-10-15 08:22Z: stop and record.

- **PRECOMMIT:** `PRECOMMIT-ucmiso-vlr-2026-10-15.md`, with Addendum 0 (operational V-2 / V-4) and Addendum A (pin,
  G-DRIFT, confound). It was written and pushed before the build PR and before any shard.
- **Build:** #7263, merged by UC-DESK at `3a55fa75ba10c62f38a3038367ed6a31f583859a`; every shard is pinned there.
- **Control:** the committed keeper bundle `closeout_miso_nuc_span` (rule 29(b)).
- **Comparator:** UC-3-MISO arm B (uc-1.5, ST_GAS floor off, no VLR).
- **Nothing was registered or promoted** (E13). Scoring used a local probe registration that was moved out of the tree
  before any commit.
- Lane session `session_01Y72HzBZvQKmeimJ5aWUoYj`.

## 0. Headline

The VLR rows do the structural job they were designed for:
- each pocket's on-share matches CEMS within ±0.05 in DSG, WOTAB and Western;
- where a row binds, the metered units are online in 95–100 % of those hours.

The arm still fails on two counts, and restores only part of the floor:
- **(1)** The C4 gas 2021 cell flips PASS → FAIL (NRMSE 0.291 → 0.308, bar 0.30). This is kill #3. **The flip belongs to
  the UC stage, not the VLR rows:** arm A (0.310) and arm B (0.306) flip the same cell.
- **(2)** The rows **under-cycle the pocket steamers** (V-3 FAIL in 2019 and 2021). They hold units on continuously, where
  the real units rotate.
- **(3)** They restore **about one fifth** of the energy the per-plant floor carried: 17 / 20 / 19 % of keeper − arm B
  on the plant basis. This matches the zero-LP sizing in the FINDING.

## 1. Readings, 2019–2021

Arm V runs at **uc-1.6 with per-unit `ut_h`**. Arm B ran at uc-1.5 with plant `ut_h` (Addendum A confound). V − B therefore
mixes the VLR rows, uc-1.6 and per-unit `ut_h`. Only V-2, V-3 and V-4 read the VLR rows alone.

**Binding (§3):**

| id | reading | 2019 | 2020 | 2021 | bar | reads |
|---|---|---|---|---|---|---|
| V-1 | P1 unserved / dump (MWh) | 0 / 0 | 0 / 0 | 0 / 0 | ≤ keeper + 500 | pass |
| V-2 | Σu ≥ 1 on-share, model vs CEMS: DSG | 0.932 vs 0.940 | 0.959 vs 0.944 | 0.822 vs 0.810 | ±0.15 | pass |
| V-2 | WOTAB | 1.000 vs 0.952 | 0.989 vs 0.995 | 1.000 vs 1.000 | ±0.15 | pass |
| V-2 | Western | 1.000 vs 1.000 | 0.927 vs 0.939 | 1.000 vs 0.973 | ±0.15 | pass |
| V-3 | pocket ST_GAS starts ÷ CEMS (all 4 sets) | 57 / 129 = **0.44** | 124 / 111 = 1.12 | 20 / 136 = **0.15** | [0.5, 2.0] every year | **FAIL 2019, 2021** |
| V-4 | binding hours with every eligible unit CEMS-dark: DSG / WOTAB / Western | 0.0 / 4.8 / 0.0 % | 2.5 / 0.0 / 0.0 % | 3.2 / 0.0 / 2.7 % | FAIL ≥ 50 % | pass |
| V-4 | Amite South (declared expected, not binding) | 4.1 % | 18.5 % | **61.4 %** | — | 2021 fails, as declared |
| V-5 | C8 ST_GAS forced share | 6.2 % | 4.1 % | 8.4 % (immaterial class) | ≤ cap | pass |

**Kill #3 (§4.3),** PASS → FAIL vs keeper on C1 non-ST_GAS / C3a / C3b / C4:
- **C4 gas 2021: r 0.824 / NRMSE 0.291 PASS → 0.820 / 0.308 FAIL.** No other cell flips.
- Arm A reads 0.310 and arm B 0.306 on the same cell, so it is the UC stage's flip (desk ruling).
- The C3c 2019 / 2021 CAVEAT → FAIL rows are the known unattested-span artefact (UC-2 §3). By magnitude, model > $200
  hours are 0 / 5 h vs control 0 / 0 h; they are not counted.

**Targets (with the confound beside them):**

| id | reading | 2019 | 2020 | 2021 | bar | reads |
|---|---|---|---|---|---|---|
| T-1 | C1 ST_GAS vs EIA-923 (TWh): arm B → V | −13.61 → −12.74 | −13.14 → −11.87 | −10.47 → −9.36 | narrows ≥ 0.7 | **met** (+0.87 / +1.27 / +1.11) |
| T-2 | C3a 2019 | +13.3 % → **+9.1 %** | — | — | toward 0 | **met** |

**Reported, not binding:**
- **C1 ST_GAS vs keeper:** −8.71 / −7.09 / −5.36 → −12.74 / −11.87 / −9.36 TWh. 2020 and 2021 go PASS → FAIL. This is
  rule-19 replacement, reported only, per the UC-3 Addendum-0 convention.
- **C1 CC_REGULAR:** +2.14 / −1.43 / −10.10. The 2021 row was already FAIL in the control.
- **C1 COAL_PRB:** +7.91 / +6.21 / +5.41. These are in band; arm B's 2019 out-of-band reading returns to band.
- **C3a:** +9.1 / +13.8 / −4.4 % (control +6.2 / +10.2 / −8.4). 2020 is FAIL in both.
- **C3b:** 0.114 / 0.177 / 0.203 (control 0.091 / 0.147 / 0.219; arm B 0.190 / 0.188 / 0.197).
- **ST_GAS plant basis** (`unit_marginal`, TWh):

  | | 2019 | 2020 | 2021 |
  |---|---|---|---|
  | keeper | 13.33 | 16.64 | 10.83 |
  | arm B | 3.61 | 5.87 | 1.26 |
  | V | 5.30 | 8.05 | 3.05 |
  | restored, (V − B) ÷ (keeper − B) | **17 %** | **20 %** | **19 %** |
  | pocket plants, B → V | 2.09 → 4.46 | 4.21 → 6.65 | 0.97 → 2.83 |

- **Make-whole on the pocket plants** (energy cost − revenue, > 0, from `uc_uplift`): $25.0 M / $15.3 M / $49.3 M. Total UC
  make-whole is $30.5 M / $21.0 M / $79.0 M. These are order-of-magnitude comparable to the IMM's DA VLR RSG for MISO South
  (2022: $25.2 M; 2022 SOM Fig. 22). That is a comparator, never an input.
- **Engine, per leg:**
  - uc-1.6; 365 / 365 windows Optimal; 0 time-limit hits.
  - `engine.vlr_pocket` = the 4 sets of Addendum 0 (n_req 1 / 1 / 1 / 2), unmatched `WOTAB:C`.
  - `pocket_rows` ≥ 96 in every window; `pocket_sets_skipped` = 0.
  - UC stage 3,708 / 4,892 / 3,716 s.
  - Memory peak 16.91 / 16.74 / 16.64 GiB (RSS + swap), on 13.36 + 9.0 GiB containers.

## 2. Reading

- **What holds.**
  - The requirement's form and its pocket→plant map work as designed. The UC carries one or two pocket steamers through the
    day exactly where the meter says they ran (V-2), and binds almost nowhere the meter is dark (V-4) outside Amite South.
  - Amite South's 2021 binding against a dark meter is the exposure declared ex ante: new in-pocket CCs relieved it after
    2020, and the structural minimum cannot see that.
  - The energy restored (+1.7 to +2.2 TWh/yr plant basis) matches the zero-LP sizing. What remains of the ST_GAS gap
    (≈ −9 to −13 TWh vs EIA) is out-of-merit dispatch above min-load. A commitment requirement does not represent that
    (FINDING §4). The CEMS-LSL `mlf` gap is routed to UC-DATA-UT.
- **Open structural item: V-3 under-cycling.**
  - With N = 1 per group and no rotation, the cheapest feasible schedule keeps the same unit on for days or weeks. In the
    real fleet, units alternate, and each start relieves another unit.
  - Pocket starts are 0.15–0.44× CEMS in 2019 and 2021.
  - **A forward fix is a min-run / rotation question** (unit-level min-up / min-down physics, or a per-unit duty-share
    reading), **not a level change**. N stays the ruling's structural minimum.
  - This is not a tuning invitation.
- **The kill.** C4 gas 2021 fails on the UC stage's CC under-commitment signature that every UC-3 lane recorded. The VLR rows
  change ST_GAS, not CC. The verdict is R per the PRECOMMIT as written. **The R is not a rejection of the VLR form.** MISO
  re-enters at the UC-4 round on the combined engine (DA-forecast commitment + per-unit `ut_h` / `mlf` + VLR) (desk ruling).

## 3. Verdict → matrix

`vlr_pocket_commitment` (MISO): **U → R**, citing this RESULT, with these qualifications:
- the R is by kill #3, a UC-stage flip;
- V-2 and V-4 pass;
- V-3 fails (under-cycling);
- coverage is 2019–21.

`scuc_load_pocket_commitment` (MISO) stays **G**. This lane tested the new field, not that row.

## 4. Coverage gap and attempt log

The keeper carries 2019–2025 (rule 16). Arm V solved 2019, 2020 and 2021. 2022–2025 never reached a solve: every container
offered for them came up at 16.4–17.4 GiB (ceiling 13.36 GiB, swap capped by free disk), below the 22.4 GiB gate.

Ruling history:
- **(b)** a larger pool was not available (desk).
- **(c)** lowering the gate was refused: 2023–25 add the reserve families, and arm B ran out of memory on exactly these
  containers.
- **(a)** bounded relaunches were stopped by ruling (i) after kill #3, because no further year could change the verdict.

Full log: `data/ucmiso_vlr_readings/attempt_log.tsv`.

| year | attempts | container GiB (mem + swap) | outcome |
|---|---|---|---|
| 2019 | 1 | 22.36 | solved `5af6176b` |
| 2020 | 1 | 22.36 | solved `180823b9` |
| 2021 | 1 | 22.36 | solved `d076c401` |
| 2022 | 3 | 17.4 / 16.4 / 17.4 | gate stop ×3 |
| 2023 | 3 | 16.4 / 16.4 / 17.4 | gate stop ×3 |
| 2024 | 2 | 16.4 / 16.4 | gate stop ×2 |
| 2025 | 2 | 16.4 / 16.4 | gate stop ×2 |

Every container that cleared the gate was launched before 05:35Z; all ten launched later were short. No gate-stopped shard
read data, solved or pushed anything. All are archived.

## 5. Where the evidence is; what a promotion would cost

| what | where | status |
|---|---|---|
| 3 leg bundles (full, incl. `dispatch/<y>_P1`; 2019 / 2021 P1 split into sha256-verified parts) | `claude/ucmiso-vlr-v-2019` @ `5af6176b`, `-2020` @ `180823b9`, `-2021` @ `d076c401` | shard branches are transport (rule 33); the owner cuts them |
| slim span | `data/ucmiso_vlr_readings/span_v_2019_2021/` (system, uc_schedule, uc_uplift, unit_marginal, uc_solve_log, run_config, regenerated diagnostics, meta, metrics) | in this PR |
| readings | `data/ucmiso_vlr_readings/`: verdict JSONs (control; V 2019–21), `v_reads_2019_2021.json` + `v_reads.py.txt`, attempt log, leg ledger, scratch composer | in this PR |
| composite | `results/calibration/ucmiso_vlr_v_span_partial` in the lane container (local exclude; never committed, rule 29(c)) | lost with the container |

- **No promotion is proposed** (R, partial span, comparator confounded).
- **To complete 2022–25:** four shards on ≥ 22.4 GiB containers, about 2–2.5 h each (2022 had a 720 min budget), at the
  same pin. Not useful before UC-4.

## 6. D-6 card (verbatim-ready)

> **UC-MISO-VLR arm V (pin `3a55fa75`, uc-1.6 + per-unit `ut_h` + VLR rows, ST_GAS per-plant floor off): R, 2019–21.**
> Kill #3 on C4 gas 2021 (0.291 → 0.308); arms A and B flip the same cell (a UC-stage flip).
>
> **The VLR rows work as structure.** Pocket on-share matches CEMS within ±0.05 in DSG, WOTAB and Western. Binding is
> grounded (≤ 5 % dark) outside Amite South (2021: 61 %, declared). They restore ~1/5 of the floor's energy (+1.7–2.2 TWh/yr).
> T-1 is met (C1 ST_GAS +0.9–1.3 TWh vs B) and T-2 is met (2019 C3a +13.3 → +9.1 %).
>
> **Open item: under-cycling** (pocket starts 0.15–0.44× CEMS in 2019 and 2021), a min-run / rotation question.
>
> 2022–25 are a coverage gap: 10 gate stops at 16.4–17.4 GiB. Revisit at UC-4 on the combined engine.

## Log entry

- 2026-10-15 · UC-MISO-VLR · pin `3a55fa75` (#7263; main also carries #7253 uc-1.6 and #7262 per-unit `ut_h`).
  - 13 shard launches → 3 legs. 2019–21 solved and verified; 2022–25: 10 memory-gate stops, coverage gap.
  - **R** by kill #3 (C4 gas 2021, a UC-stage flip).
  - V-2 / V-4 pass; V-3 fails (under-cycling, open item).
  - T-1 / T-2 met; ~1/5 of the floor energy restored.
  - Matrix `vlr_pocket_commitment` (MISO) U → R. Nothing registered.
