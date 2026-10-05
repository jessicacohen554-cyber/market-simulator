# RESULT — UC-2-SPP: MILP unit-commitment A/B on every SPP backcast year — **R (control flips), targets moved the right way but short of two bars**

**Lane:** UC-2-SPP · **Session:** `session_01QBeFQCYTmVafRpi7Ujb9gs` (Fable) · **Dates:** 2026-10-04 → 2026-10-05 · **Branch:** `claude/ucmilp-2-spp-ab-r7qd`
(rebased onto `origin/main` `ae224faf`). **PRECOMMIT:** `PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (pushed `719ceac5` before any shard; Addenda A–C before each relaunch; Addendum D the composition deviations).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`); owner: *"I want tests on backcast years to see if it improves calibration."*
**Pin solved:** `ae224fafdda926bf8817afee385bd6cedc470120` (main at the merge of PR #7201; engine uc-1.1). **LP in this session:** zero (seven year-isolated shards, rule 36).
**Registered:** `2026-10-05-ucmilp-spp-uc-b` (PROBE, `--no-prune`), bundle `results/calibration/ucmilp_spp_span`. Rubric 3.20 for both arms (the control re-scored at HEAD reproduces its registered record exactly).

## 0. Headline

**The integer commitment stage lowers the SPP price body in every year.** That is the direction the two model-high target years needed:
2019 C3a +12.3 → **+10.3 %** (bar ≤ +11.15 %: **met**), 2020 C3a +27.7 → **+19.0 %** (bar ≤ +18.85 %: **0.16 pt short**), 2020 C3b 0.345 → **0.273**
(bar ≤ 0.2725: **short at the recorded precision**), and the model now produces 3–11× more hours at or below $15 and 4–7× more negative hours.
**But the same body shift pushes every model-low year through its gate**: 2023 C3a −6.4 → −15.9 % and C3b 0.176 → 0.233 both flip PASS → FAIL;
2024 (declared cost) worsens to −22.6 % / 0.344; 2022 and 2025 land at −9.4 % and −10.0 %. The UC also moves ~6–8 TWh/yr from CC_REGULAR to
COAL_PRB (coal online more, CC decommitted), flipping C1 CC_REGULAR 2023/2024/2025 and COAL_PRB 2025 to FAIL, and the kept
`st_gas_mustrun_per_plant` floor binds for 1–1.2 TWh/yr more under the UC, pushing C8 ST_GAS over the 30 % cap in 2021/2022/2023/2025.
**Kill #3 (control flip) fired on real moves → verdict `R`** (PRECOMMIT §7). It is the frontier row SPP-F2's prediction, now measured with integer state:
the commitment form that lowers 2019/20 lowers 2023–25 too; no year-uniform commitment form exists in this model class.

### 0.1 GATESPEC §6.3 gate table — control (keeper `2026-10-03-closeout-spp-nuc-keeper`) → arm, every registered year

| year | C1 (class rows) | C2 | C3a | C3b | C3c | C4 | C8 | D-2 MECH 28 share (CC / PRB / ST_GAS) | wall ratio | reading met? |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | all PASS → all PASS (CC +2.25 → −6.05 TWh; PRB +0.24 → +6.74) | PASS → PASS | +12.3 → **+10.3 %** FAIL → FAIL | 0.160 → 0.143 PASS → PASS | CAVEAT → FAIL* (0 h / 47 h, unchanged) | PASS → PASS | PASS → PASS (ST_GAS 18.1 → 27.7 %) | 2.3 / 1.1 / 1.8 % | 10.2 | **T2 met**; T4 sign right |
| 2020 | all PASS → all PASS (CC +1.60 → −4.99; PRB −3.03 → +3.51) | PASS → PASS | +27.7 → **+19.0 %** FAIL → FAIL | 0.345 → **0.273** FAIL → FAIL | CAVEAT → FAIL* (0 h / 23 h) | PASS → PASS | PASS → PASS (ST_GAS 15.7 → 25.7 %) | 2.8 / 2.4 / 1.8 % | 6.9 | T1 0.16 pt short; T3 0.0005 short; T4 sign right |
| 2021 | CC −8.92 → −13.53 FAIL→FAIL; PRB +10.98 → +12.77 FAIL→FAIL | PASS → PASS | +7.1 → +3.8 % PASS | 0.176 → 0.122 PASS | CAVEAT → FAIL* (372 → 387 h) | PASS → PASS | **ST_GAS 28.8 → 36.8 % PASS → FAIL** | 5.2 / 1.5 / 1.8 % | 8.6 | control: **flip** (C8) |
| 2022 | CC −9.16 → −13.13 FAIL→FAIL; PRB +10.75 → +12.16 FAIL→FAIL | PASS → PASS | −4.8 → −9.4 % PASS | 0.175 → 0.186 PASS | CAVEAT → FAIL* (0 h / 99 h) | gas 0.313 → 0.308 FAIL→FAIL | **ST_GAS 33.8 % grounded → 39.2 % not grounded PASS → FAIL** | 4.9 / 1.5 / 1.7 % | 8.7 | control: **flip** (C8) |
| 2023 | **CC −4.49 → −10.18 PASS → FAIL**; PRB +0.57 → +6.40 PASS | PASS → PASS | **−6.4 → −15.9 % PASS → FAIL** | **0.176 → 0.233 PASS → FAIL** | FAIL → FAIL (0 h / 42 h) | PASS → PASS | **ST_GAS 23.1 → 33.6 % PASS → FAIL** | 3.1 / 2.3 / 2.5 % | 5.1 | control: **4 flips** |
| 2024 | **CC −5.80 → −11.83 PASS → FAIL**; PRB +0.82 → +7.52 PASS | PASS → PASS | −11.2 → −22.6 % FAIL → FAIL (declared cost) | 0.216 → 0.344 FAIL → FAIL | FAIL → FAIL (0 h / 59 h) | PASS → PASS | PASS → PASS (ST_GAS 18.3 → 28.3 %) | 3.0 / 2.7 / 1.9 % | 8.0 | cost as declared; **flip** (C1) |
| 2025 | **CC −7.86 → −13.76 PASS → FAIL; PRB +7.39 → +10.21 PASS → FAIL** | PASS → PASS | −4.3 → −10.0 % PASS (boundary) | 0.153 → 0.174 PASS | FAIL → FAIL (0 h / 68 h) | PASS → PASS | **ST_GAS 17.7 → 31.4 % PASS → FAIL** | 3.9 / 0.9 / 12.0 % | 7.9 | control: **3 flips** |

\* C3c CAVEAT → FAIL in 2019–2022 is a scoring artefact, not a model move: the keeper's C3c entries are ledgered through its `calibration_attestation.json`
(rule 22), the probe bundle carries no attestation (C6 reads UNATTESTED), so the ledger route is unavailable; the magnitudes are identical in 2019/2020/2022
(0 h) and 372 → 387 h in 2021. Every other flip above is real. Determination: NOT-YET → NOT-YET (control grade 3 of 8 scored; arm 1 of 7 scored, 6 FAIL
criteria plus the unattested C6).

### 0.2 GATESPEC §6.1 wall rows (every shard, standard solve container, `MARKET_SIM_HIGHS_THREADS=1`; baseline = the same shard's P0 + P1, PRECOMMIT §5 proxy)

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** total/(P0+P1) | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB (UC stage / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPP 2019 | 172.1 | 87.5 | 1496.1 (4.02 / 5.31) | 84.6 | 1748.0 | **10.2** | 3,384 (94 int. clusters of 226) | 1 / 1 | 5.8e-4 | 0 | 4.13 / 6.85 |
| SPP 2020 | 198.9 | 97.7 | 1106.9 (2.97 / 4.23) | 101.2 | 1367.1 | **6.9** | 3,312 (92 / 219) | 1 / 1 | 5.7e-4 | 0 | 5.09 / 6.92 |
| SPP 2021 | 254.1 | 126.4 | 1825.5 (4.90 / 6.65) | 127.7 | 2175.0 | **8.6** | 3,168 (88 / 208) | 1 / 1 | 8.0e-4 | 0 | 5.07 / 6.90 |
| SPP 2022 | 241.5 | 117.6 | 1749.5 (4.69 / 6.25) | 123.9 | 2098.6 | **8.7** | 3,096 (86 / 219) | 1 / 1 | 8.5e-4 | 0 | 4.11 / 6.89 |
| SPP 2023 | 259.5 | 170.7 | 981.2 (2.63 / 3.64) | 88.8 | 1310.9 | **5.1** | 3,096 (86 / 218) | 1 / 1 | 6.1e-4 | 0 | 4.07 / 6.91 |
| SPP 2024 | 257.6 | 124.3 | 1708.5 (4.58 / 6.13) | 133.3 | 2064.3 | **8.0** | 2,988 (83 / 221) | 1 / 1 | 6.1e-4 | 0 | 4.10 / 6.81 |
| SPP 2025 | 192.1 | 86.9 | 1244.8 (3.34 / 4.56) | 105.2 | 1508.8 | **7.9** | 2,952 (82 / 217) | 1 / 1 | 7.0e-4 | 0 | 4.12 / 7.25 |

Every window Optimal (2,555 of 2,555); every MILP solved at the root (median and p95 node count 1); 0 time-limit hits (W2 met, bar ≤ 3);
no pre-fixing (`uc_prefixing` off, fixed_on = fixed_off = 0). The MILP step is ~2.6–4.9 s per 36-h window; build ≈ 25 s/year. Whole-shard wall
(clone, hydrate, regenerate, P0, UC, P1, push) 33–45 min. **D-2 is UNRULED**: the ratios are reported, not judged; against the plan's proposed
bars (efficient ≤ 1.5×, ceiling ≤ 3×) every year is above the ceiling as the stage is built (sequential windows, one fresh model per window, one thread).

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5)

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | 2020 C3a (model 21.09 → 19.66 vs actual 16.52) | +27.7 % | **+19.0 %** | ≤ +18.85 % | **no — 0.16 pt short** (moved 8.7 of the 8.85 pts) |
| T2 | 2019 C3a (23.40 → 22.99 vs 20.85) | +12.3 % | **+10.3 %** | ≤ +11.15 % | **yes** |
| T3 | 2020 C3b NRMSE | 0.345 | **0.273** | ≤ 0.2725 | **no — 0.0005 short** at the 3-dp precision the scorer records |
| T4 | low-price-hour ratios model/actual (≤ $15 · < $0) | 2019 0.025 · 0.040; 2020 0.150 · 0.111 | 2019 **0.094 · 0.271**; 2020 **0.310 · 0.456** | both rise | **yes** (sign) — every year rises: ≤ $15 to 0.43–0.73 and < $0 to 0.91–1.29 in 2021–2025 |
| T5 | M4 reserve dormancy (model share of hours with MCP < $1 vs actual) | 1.00 vs 0.09 / 0.08 | **1.00** (unchanged) vs 0.09 / 0.08; model mean MCP $0 | falls | **no — no move**: the UC's online-capacity gate did not price SPP reserves |
| cost | 2024 C3a / C3b (model-low) | −11.2 % / 0.216 | **−22.6 % / 0.344** | reported | the declared cost, larger than the 2019/2020 gains |
| control | no PASS → FAIL flip | — | **9 real flips** (2023 C3a, 2023 C3b, C1 CC 2023/2024/2025, C1 PRB 2025, C8 ST_GAS 2021/2022/2023/2025 = 10 incl. C8 2023) + 5 attestation artefacts (C3c ×4, C6) | none | **breached → kill #3** |
| control | every leg Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | — | P1 Optimal ×7; unserved 0.0 MWh in every year (2021 reported 0.0; dump 0.0); D-4 FAIL rows 6 (arm) ⊂ 7 (control), all `st_gas_mustrun_per_plant` plants 1230/3008/6193 pre-existing | — | met |
| S1 | MECH 28 share of class energy | 0 | CC_REGULAR 2.3–5.2 %, COAL_PRB 0.9–2.7 %, ST_GAS 1.7–2.5 % (12.0 % in 2025), COAL_LIGNITE ≤ 0.3 %; 0.9–2.3 TWh of UC floor per class-year | reported (R4: not budgeted) | — |
| S2 | starts per plant-year vs CEMS (M1) | CC 2,073–3,847 vs 1,211–1,728 (1.6–2.3×); PRB 77–285 vs 259–372; ST_GAS 440–868 vs 796–1,351 | **CC 689–1,297 (0.52–0.77×)**; PRB 60–124 (0.23–0.41×); ST_GAS 135–263 (0.14–0.27×) | CC toward CEMS | overshoots: the UC under-cycles every slow class; CC crosses from 1.7× to 0.6× CEMS |
| S3 | online capacity vs SPP portal series | — | comparator not on disk (PRECOMMIT §4); skipped | — | — |
| S4 | integer set, fallback shares | UC-0 M6: 86 integer clusters | 82–94 integer clusters of 208–226 plant clusters; no-load source `uc-params` 122–123 clusters, class fallback 86–103 | reported | — |
| W1 | wall rows | — | §0.2 | reported | — |
| W2 | time-limit hits | — | 0 / 365 every year | ≤ 3 | met |
| W3 | uplift share = Σ make-whole ÷ Σ λ·load | — | 2019 1.0 %, 2020 2.2 %, 2021 3.2 %, 2022 3.0 %, 2023 3.4 %, 2024 4.4 %, 2025 3.0 % ($64 M–$347 M/yr) | ≤ 2 % | **breached 2020–2025** |
| W4 | infeasible windows | — | 0 | 0 | met |
| kill #1 | infeasible window | — | none at `ae224faf` (7/7 at `c8690022`, fixed by UC-1-FIX) | — | not fired |
| kill #2 | non-determinism | — | not exercised (one completed run per year) | — | — |
| kill #3 | control flip | — | **fired** (above) | — | **R** |

**C8 under owner ruling R4 (UC energy reported, not budgeted).** The scorer at this pin budgets `uc_schedule` energy in the D-2 share and has no D-4 window for
it (*"no declared D-4 window: uc_schedule"*). Recomputed from the D-2 rows with MECH 28 removed, ST_GAS forced share still reads **34.9 % (2021), 37.5 % (2022),
31.2 % (2023)**, 19.4 % (2025): the kept `st_gas_mustrun_per_plant` floor's own forced energy rose from 2.17 → 3.11, 2.66 → 3.68, 3.02 → 4.26 and 2.79 → 3.66 TWh.
Three of the four C8 flips survive the R4 adjustment; the UC and the kept ST_GAS floor stack (owner card D-5 kept both; this is the interaction).
The 2021/2023 grounding also fails on the pre-existing plant-3008 conduct row, which the control never reached because its share sat below the cap.

## 2. What the UC did to the dispatch (zero LP, from the composed sidecars)

- **Body down everywhere, tails unchanged.** Lower-tercile mean error (M3) falls from +$9.7…+14.8 to +$0.5…+10.6/MWh; upper-tercile error stays −$7…−28.
  System mean price falls $0.4–2.9/MWh in every year. Scarcity hours (> $200) are unchanged (0 h in six years; 372 → 387 h in 2021).
- **Coal for CC.** CC_REGULAR −5.3 to −8.3 TWh and COAL_PRB +3.5 to +7.0 TWh against the control in every year (2019: CC 46.7 → 39.5 TWh, PRB 78.0 → 82.9);
  CT_PEAKER +0.9 to +2.4 TWh. With no-load and start cost paid once in the UC objective and coal's long min-up/min-down, the stage keeps coal online
  through troughs and shuts CC down: the SPP-89 coal↔CC swap, made larger. C1 CC_REGULAR was already FAIL in 2021/2022 and now fails in 2023–2025 too.
- **Cycling collapses.** CC starts fall 3× (2,073 → 689 in 2019) to 0.52–0.77× CEMS; coal and ST_GAS starts fall further below CEMS.
- **Reserves untouched.** Reserve MCP < $1 in every hour, as in the control: the online-capacity envelope did not create reserve scarcity in SPP.
- **Uplift.** Make-whole 1.0–4.4 % of wholesale energy cost; integer clusters' energy cost $2.0–3.4 B/yr.

## 3. Verdict, the D-6 card, and what the record says about the mechanism

- **Verdict: `R`** (PRECOMMIT §7: a kill fired). T2 met; T1 and T3 moved the right way and stopped just short of their bars; T4 right; T5 did not move.
  The mechanism is structurally real (integer commitment, measured physics, zero free parameters) and the price-body effect is exactly as predicted,
  but it worsens the model-low years by more than it helps the model-high ones and shifts energy from CC to coal against C1.
- **Matrix:** SPP `unit_commitment_milp` → **R**, evidence this RESULT (the desk stamps the cell after the engine merge; integer state is the new
  evidence vs the posture cell, rule 28). The verdict is per-ISO; other ISOs enter as `U`.
- **D-6 card (copy-paste):** *"UC-2 SPP A/B — record R. The MILP UC stage at ae224faf solves every SPP year (365/365 windows Optimal, 0 time-limit hits,
  5–10× the P0+P1 wall). It lowers the price body in every year: 2019 C3a +12.3 → +10.3 % (bar met), 2020 +27.7 → +19.0 % (0.16 pt short), 2020 C3b
  0.345 → 0.273 (0.0005 short), low-price hours ×3–11. The same shift flips 2023 C3a/C3b, C1 CC_REGULAR 2023–25, C1 COAL_PRB 2025 and C8 ST_GAS
  2021–23/25 PASS → FAIL, and worsens 2024 C3a to −22.6 %; CC starts fall to 0.6× CEMS and ~6–8 TWh/yr moves from CC to coal. Options: (1) record R,
  stage stays default-off for SPP [recommended]; (2) hold pending a D-5 re-ruling on stacking the kept ST_GAS floor with the UC and an R4 scorer
  implementation (3 of 4 C8 flips survive both); (3) promote on structure (not recommended: 9 real control flips)."*
- **Not a tuning invitation.** No `uc_*` value was moved; the 0.16-pt and 0.0005 misses are reported as misses (GATESPEC §7.1).
- **For the frontier ledger (SPP-F2):** the reopen condition *"a commitment mechanism that lowers 2019/20 and also lifts 2023–25"* is tested with integer
  state and not met: the UC lowers 2023–25 further. The row's "why" stands.

## 4. Bundles, cost, what survives (rule 31: nothing deleted)

| artefact | where | promotable? |
|---|---|---|
| seven leg bundles (full, incl. `dispatch/<y>_P1.parquet`, 44–48 MB each) | shard branches `claude/ucmilp-spp-2019` `80ef3082` · `-2020` `8b2b6c61` · `-2021` `13e1ca1e` · `-2022` `7a248461` · `-2023` `11f459d8` · `-2024` `03458763` · `-2025` `b35f831a` (all parented on `ae224faf`); checked out locally under `results/calibration/ucmilp_spp_<y>/` | yes in form (rule 34); no promotion recommended |
| composed span `results/calibration/ucmilp_spp_span` (slim: hourly sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`, `uc_solve_log_<y>.json`, regenerated `legitimacy_diagnostics.json`, `metrics.json`) | this branch / PR | registered PROBE `2026-10-05-ucmilp-spp-uc-b` |
| dashboard payload | `frontend/data/backcast/registry/2026-10-05-ucmilp-spp-uc-b.json`, `runs/2026-10-05-ucmilp-spp-uc-b.js` (1.7 MB) | probe |
| shared benchmark frames | `results/calibration/_shared/SPP/` — the span re-pointed to the keeper's own frames (same content hashes `campd-8b15fb193a60`, `eia923-ada99c7451fd`, `eia930-c3bec7e7b952`, already on main) | — |

Cost of the attempt: 21 shard containers (7 crashed at `6d47c762`, 7 infeasible at `c8690022`, 7 solved at `ae224faf`, 33–45 min each); zero LP in the parent.
Cost to reproduce the arm: seven shards at `ae224faf`, ~35–45 min wall each. **Promotion question: none is proposed**; the lane recommends `R`.
Shard branches are transport (rule 33): the owner may delete the seven `claude/ucmilp-spp-<y>` branches once this PR merges (a session cannot, 403).

## 5. Process record (both engine defects, routed and fixed) — see PRECOMMIT Addenda A–D

1. `6d47c762`: 7/7 shards crashed at `pipeline/uc.py:363` (`UcStage.artifact_dir` unset) → fixed by UC-1-FINISH (`4e7b54d5`), merged as PR #7194.
2. `c8690022`: 7/7 shards raised `UcWindowInfeasible` (no incumbent) → UC-1-FIX root cause: the carried min-up/min-down history enforced as a separate `u`
   bound while the Rajan–Takriti rows summed only in-window starts; fixed by carrying the history in the rows' RHS plus a look-ahead min-down guard,
   merged as PR #7201 (`FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04.md`).
3. `ae224faf`: 7/7 legs solved. Composition needed two zero-LP deviations from `_ucmilp_compose_span.py` (Addendum D): `gas_price_override` added to the
   per-year field set (the keeper composer's `YEAR_INDEXED` precedent) in a scratch copy, and the keeper composer's `_respan_shared_inputs` applied so the
   one-year benchmark hashes of the first leg became the span's frames (they resolved to the keeper's own hashes). Both belong in the engine lane's
   composer; routed.
4. Shards: 21 launched, 21 archived; none left alive.

## Log entry

- 2026-10-04/05 · UC-2-SPP `session_01QBeFQCYTmVafRpi7Ujb9gs` (Fable) · `claude/ucmilp-2-spp-ab-r7qd` · zero LP in the parent · PRECOMMIT `719ceac5` before any
  shard; pins `6d47c762` (uc.py:363 crash) → `c8690022` (UcWindowInfeasible 7/7, kill #1 recorded) → `ae224faf` (7/7 solved, 2,555/2,555 windows Optimal) ·
  **verdict R**: 2019 C3a +12.3 → +10.3 % (bar met), 2020 C3a +27.7 → +19.0 % (0.16 pt short), 2020 C3b 0.345 → 0.273 (0.0005 short), low-price hours ×3–11,
  reserve dormancy unmoved; control flips 2023 C3a/C3b, C1 CC 2023–25, C1 PRB 2025, C8 ST_GAS 2021–23/25; CC → coal 6–8 TWh/yr; CC starts to 0.6× CEMS;
  uplift 1.0–4.4 % of energy cost; wall 5.1–10.2× P0+P1 (D-2 unruled) · PROBE `2026-10-05-ucmilp-spp-uc-b` registered · cell `unit_commitment_milp` SPP → R
  (desk stamps) · D-6: record R, stage default-off for SPP · no promotion proposed.
