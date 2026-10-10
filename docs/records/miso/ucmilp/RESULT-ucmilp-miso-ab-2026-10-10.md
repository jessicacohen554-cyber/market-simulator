# RESULT — UC-2-MISO: MILP unit-commitment A/B on the MISO backcast years — **R (kill #3: 2024 unserved +2,760 MWh; T2 wrong sign; C8 ST_GAS and C4 gas control flips). The UC acts on 71–77 of 139–167 gated clusters; the rest is yard coal left to its budget identity (ruling (a)).**

**Lane:** UC-2-MISO, relaunched as UC-2-MISO-R2 (`session_01FZXtSAEvH3DJLVu9bkXD6h`, Opus) after the Fable session `session_016bPoPZ6beefv8kJUn8sQFH`
hit its weekly limit · **Date:** 2026-10-10 · **Branch:** `claude/ucmilp-2-miso-ab-m6z4` (origin/main merged in, no rebase).
**PRECOMMIT:** `PRECOMMIT-ucmilp-miso-ab-2026-10-10.md` + Addenda A–H (F = relaunch pin and G-DRIFT, G = launch, H = legs in + kill #3).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). **Pin solved:** `eab17188c75cd0332f9323ed3464c62bc0cd1848` (main at #7230:
engine uc-1.2, ruling (a), UC-SLIM, FIX-3 crosswalk). **LP in this session:** zero. **Registered:** nothing (E13); the local scoring
registration was moved out of the tree before any commit.

## 0. Headline

**On MISO, with every conduct floor kept, the integer commitment stage acts on less than half the fleet it was built for, and where it
acts it reproduces the SPP stacking failure.** Ruling (a) leaves every all-budget-pinned cluster to its fuel identity. MISO pins every yard
coal row (`coal_fuel_inventory_plant_grain=true`), so the integer set falls from the E1 gate's **167 / 164 / 161 / 144 / 139** clusters to
**71 / 76 / 75 / 77 / 74** (2019 / 2020 / 2021 / 2024 / 2025). The UC therefore commits gas and unpinned coal only.

- **Cycling.** It does what it was built to do: CC_REGULAR starts fall from 1.3–1.6× CEMS to **0.36–0.51×**, and ST_GAS from 4.5–6.4× to
  **0.28–1.07×**. Coal starts do NOT fall (COAL_BIT 3.4–4.4× → 3.7–5.0×); that is the demoted yard coal.
- **Prices.** The price body moves down **$0.0–0.9/MWh**. That clears the 2020 C3a miss by the narrowest margin (**+10.2 → +10.0 %**,
  T1 met). The low-price tail appears where actuals have one (≤ $15 hours **8 → 85** in 2020, **6 → 182** in 2024).
- **Kills and wrong-sign moves.** **Kill #3 fires on 2024** (the 26 Aug heat event sheds **11,117 MWh vs the keeper's 8,357**, +2,760 MWh
  against the 500-MWh gate). **T2 moves the wrong way** (2021 C3b 0.219 → 0.221). Three more control rows flip PASS → FAIL:
  - C8 ST_GAS in 2019 / 2020 / 2025 (26.3 / 20.0 / 20.0 % → 36.9 / 30.6 / 31.5 %), driven by the kept `st_gas_mustrun_per_plant` floor
    whose own forced energy rises **1.3–2.0 TWh/yr**. With MECH 28 removed (R4), 2019 still reads 33.6 % FAIL.
  - C4 gas 2021 (NRMSE 0.291 → 0.306).

**Verdict R** (PRECOMMIT §7: a kill, plus a target past its control). Coverage: 5 of 7 years composed; 2022 stopped at its budget, and
2023 solved clean but its bundle is held in its container (§4).

### 0.1 GATESPEC §6.3 gate table — control (keeper `2026-10-03-closeout-miso-nuc-r`) → arm, every composed year

Rubric 3.20. Both sides were scored on the SAME committed bench parts: the local registration rewrote none, and `git status` was clean
after it. C1 = Δ TWh vs actual (model − actual); 2025 C1 is SKIPPED by the scorer (preliminary EIA-923) and is shown for magnitude only.
`*` C3c CAVEAT → FAIL is the probe's missing attestation (C6 UNATTESTED, named ex ante in §3), not a status move by the model; the
magnitudes are in the cell.

| year | C1 (Δ TWh, control → arm) | C3a mean LMP | C3b NRMSE | C3c hours > $300 (model / actual) | C4 gas | C8 ST_GAS (as printed; MECH 28 inside) | C8 ST_GAS, MECH 28 removed (R4) | unserved MWh | reading |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | CC_REGULAR +3.17 → +0.67; COAL_PRB +4.56 → +4.73; **ST_GAS −8.71 → −7.82 FAIL → PASS**; CT_PEAKER +2.01 → +2.10 | +6.2 → +6.3 % PASS | 0.091 → 0.095 PASS | 0 → 8 / 17 CAVEAT → FAIL* | NRMSE 0.196 → 0.202 PASS | **26.3 → 36.9 % PASS → FAIL** | 33.6 % (FAIL) | 0 → 0 | **flip** (C8) |
| 2020 | CC_REGULAR −1.24 → −2.66; COAL_PRB +3.87 → +4.13; ST_GAS −7.09 → −7.54 (0.46 TWh headroom left); COAL_BIT −4.66 → −4.45 | **+10.2 → +10.0 % FAIL → PASS** | 0.147 → 0.146 PASS | 0 → 1 / 8 PASS | 0.201 → 0.210 PASS | **20.0 → 30.6 % PASS → FAIL** | 26.7 % (PASS) | 0 → 0 | T1 met; C8 flips as printed only |
| 2021 | CC_REGULAR −8.15 → **−12.98** (FAIL → FAIL, 4.8 TWh worse); COAL_PRB +5.03 → +3.58; ST_GAS −5.36 → −4.03 | −8.4 → −9.1 % PASS (0.9 pt headroom left) | **0.219 → 0.221 FAIL** (wrong sign) | 0 → 3 / 48 CAVEAT → FAIL* | **0.291 → 0.306 PASS → FAIL** | SKIPPED (< 2 % of load) | — | 0 → 0 | **T2 breached; flip** (C4) |
| 2024 | CC_REGULAR +2.61 → +0.61; ST_GAS −2.43 → −6.05; CT_PEAKER −4.64 → −5.07; CC_CHP −1.40 → −2.66 | +2.5 → −0.4 % PASS | 0.082 → 0.082 PASS | 7 → 7 / 37 CAVEAT → FAIL* | 0.151 → 0.179 PASS | 14.9 → 29.4 % PASS | 26.9 % | **8,356.9 → 11,116.8** | **kill #3** |
| 2025 | (SKIPPED) CC_REGULAR +5.58 → +2.29; COAL_PRB −4.31 → −5.56; ST_GAS −4.25 → −5.94 | −3.8 → −5.2 % PASS | 0.085 → 0.091 PASS | 9 → 9 / 88 CAVEAT → FAIL* | 0.173 → 0.195 PASS | **20.0 → 31.5 % PASS → FAIL** | 29.9 % (PASS) | 0 → 0 | C8 flips as printed only |
| 2022 | not solved: budget stop (§4) | | | | | | | | — |
| 2023 | solved, bundle in container (§4) | | | | | | | 0 (reported) | not scored |

The CT_PEAKER C8 conditional pass survives every year (forced share 0.76 / 0.91 / 0.34 / 0.36, grounded as in the control). C2 and C5a
read PASS → PASS. Determination (5-year span, not comparable to the keeper's 7): **NOT-YET → NOT-YET**; the arm reads 7 scored / 2 target
/ 5 FAIL, inflated by the probe's unattested C6 and C3c.

### 0.2 GATESPEC §6.1 wall rows

Standard solve container, 4 cores, `MARKET_SIM_HIGHS_THREADS=1`. Baseline = the same shard's own P0 + P1 (the PRECOMMIT §5 proxy; the
armed P1 is heavier than a gate-off P1).

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** | integers/window (integer set of gate) | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| MISO 2019 | 1,456.5 | 649.5 | 3,713.3 (9.25 / 15.88) | 807.0 | 5,438.8 | **3.73** | 2,556 (71 of 167) | 1 / 13.8 | 9.6e-4 | 0 | 13.32 |
| MISO 2020 | 1,332.1 | 551.5 | 3,489.3 (8.74 / 15.24) | 780.6 | 5,084.2 | **3.82** | 2,736 (76 of 164) | 1 / 13.8 | 9.7e-4 | 0 | 13.32 |
| MISO 2021 | 1,728.4 | 750.1 | 3,199.6 (7.89 / 13.24) | 978.3 | 5,175.6 | **2.99** | 2,700 (75 of 161) | 1 / 12.8 | 9.5e-4 | 0 | 13.33 |
| MISO 2022 | — | 3,559.6 | 284 of 365 windows logged, all Optimal (12.1 / max 50 through w260) | not reached | > 6,900 | — | — (77 of —) | 1 / — | — | 0 | — |
| MISO 2023 | 1,172.5 | 560.0 | 3,188.8 (7.89 / 14.63) | 612.5 | 4,649.2 | **3.97** | 2,664 (74 of 147) | 1 / 15.0 | 9.4e-4 | 0 | 13.33 |
| MISO 2024 | 922.5 | 447.8 | 3,676.6 (9.21 / 19.07) | 474.7 | 4,827.0 | **5.23** | 2,772 (77 of 144) | 1 / 20.6 | 9.4e-4 | 0 | 13.33 |
| MISO 2025 | 1,262.9 | 594.6 | 2,665.9 (6.76 / 13.58) | 668.3 | 4,154.6 | **3.29** | 2,664 (74 of 139) | 1 / 18.0 | 9.7e-4 | 0 | 13.33 |

Notes on the table:
- Every solved window was Optimal: 2,190 of 2,190 in the six full years, plus 284 of 284 in 2022.
- W2: 0 time-limit hits. W4: 0 infeasible windows. The defect-5 collision that killed every year at `2f872a62` is gone.
- Slim window on: about 66 k solved columns per window.
- Every container touched the 13.36 GiB cgroup cap and spilled 3.3–4.5 GiB to swap; no OOM kill was logged.
- **D-2 is ruled at 3×** (plan §8.1). Five of six ratios are above it; the ratios are reported, not judged.
- 2022's P0 alone took 3,560 s (Addendum D: 1,706 s at the old pin), which by itself sinks it under the 115-min budget.
- 2023's row is from its shard report (bundle not fetched).

## 1. The pre-fixed readings, answered (PRECOMMIT §§2–5)

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | 2020 C3a | +10.2 % FAIL (24.21 vs 21.97) | **+10.0 % PASS** (24.17) | ≤ +10.1 % | **met** (by 0.04 $/MWh; the "weak in magnitude" case UC-0 named) |
| T2 | 2021 C3b | 0.219 FAIL | **0.221** | ≤ 0.2095 | **breached: wrong sign** |
| T3 | M4 reserve dormancy 2024 / 2025 (2023 unscored) | model 0.999 / 0.998 vs actual 0.415 / 0.492; mean MCP $0.23 / 0.17 vs $2.54 / 3.12 | **0.999 / 0.997; $0.29 / 0.23** | sign | right sign, negligible magnitude (as SPP, NYISO) |
| T4 | hours ≤ $15, model / actual (M3) | 2020 8 / 1,021 = 0.008; 2024 6 / 597 = 0.010; other years 0 | **2020 85 / 1,021 = 0.083; 2024 182 / 597 = 0.305**; 2019 / 2021 / 2025 still 0 (of 231 / 38 / 58) | sign | **right sign**; lower-tercile error falls in every year (4.76 → 4.28, 5.08 → 4.57, 7.31 → 6.19, 5.34 → 3.54, 8.40 → 6.86 $/MWh) |
| T5 | online capacity / ASM | reframed ex ante | `online_mw` is in `uc_schedule_<y>.parquet` (slim span); ASM comparator not built in this lane | — | reported as available, not measured |
| control | no PASS → FAIL flip; unserved ≤ +500 MWh; every P1 Optimal; no new D-4 FAIL | — | **C8 ST_GAS 2019 / 2020 / 2025, C4 gas 2021 flip; 2024 unserved +2,760 MWh**; P1 Optimal ×5 (+2023); **one new D-4 FAIL row**: plant 1439, 2020 (the keeper's rows for plant 990 2019–21 and plant 1081 2019 persist; the keeper's plant 1122 rows for 2023/2025 clear in 2025) | zero | **breached → kill #3** |
| S1 | MECH 28 share | 0 | CC_REGULAR 3.5–6.5 % (3.6–6.0 TWh/yr); ST_GAS 1.6–4.2 % (0.3–0.8 TWh) | R4 | — |
| S2 | starts vs CEMS (M1) | CC 1.28–1.57×; COAL_PRB 1.33–2.79×; COAL_BIT 3.3–4.4×; ST_GAS 4.5–6.4× | **CC 0.36–0.51×; ST_GAS 0.28–1.07×; COAL_PRB 1.09–3.00×; COAL_BIT 3.7–5.0×** | toward CEMS | gas: overshoots below CEMS (as SPP / NYISO); coal: unchanged or worse (yard coal demoted) |
| S3 | online capacity | — | see T5 | — | — |
| S4 | integer set | UC-0 M6: 159 clusters | E1 gate 139–167 → **integer set 71–77** after ruling (a) (65–96 all-budget-pinned clusters demoted per year); FIX-3 crosswalk re-keyed 3 clusters to measured params | reported | the UC acts on 43–53 % of the gate set |
| S5 | CC ↔ coal swap | — | **no CC → coal swap**: CC_REGULAR −1.4 to −4.8 TWh, COAL_PRB −1.5 to +0.3, COAL_BIT −0.4 to +0.2. Where the CC energy goes was not decomposed here; it is not coal. A plausible reason, not tested: the SPP swap needed coal integers, and ruling (a) removed them | reported | — |
| W1–W5 | cost | — | §0.2; uplift **0.91 / 0.82 / 1.49 / 0.67 / 0.79 %** of energy cost ($161 M / 124 M / 341 M / 125 M / 209 M) | W3 ≤ 2 % | W2, W3, W4 met; W5 no OOM |
| kill #1 | infeasible window | fired ×7 at `2f872a62` (Addendum D) | **none at the pin** | — | not fired |
| kill #2 | non-determinism | — | not exercised (one completed run per year) | — | — |
| kill #3 | control flip | — | **fired** (2024 unserved; C8; C4) | — | **R** |

**The stacking, measured (D-2 rows, TWh; control → arm).** `st_gas_mustrun_per_plant` forced energy: 2019 4.84 → 6.51, 2020 4.32 → 5.64,
2021 5.23 → 7.21, 2024 3.52 → 5.50, 2025 4.18 → 5.84. The UC decommits ST_GAS between floor hours (starts collapse 5×); the kept p25 floor
then binds on more of the class's remaining energy. This is the interaction PRECOMMIT §1 named "the hard case", and it is the same sign and
size SPP arm A showed (+1–1.2 TWh). It is the mechanism behind every C8 flip. **The 2024 unserved increase** sits in the same 26 Aug event
the keeper already sheds in (hours 5701–5706). The arm sheds in more zone-hours (West ×3, Plains, Illinois, Indiana vs West, Indiana, East)
and dumps 416 MWh the keeper does not. The mechanism was not traced in this lane (a zero-LP read of the 2024 `uc_schedule` vs the keeper's online MW in hours 5690–5710 is the next step). The hypothesis is less online headroom at the peak under the UC's day-ahead commitment.

## 2. Coverage and composition

- **2022 — budget stop, no bundle** (`session_01JwPkP9JprGyHhyhUBouxvK`, archived):
  - P0 took 3,560 s, and the UC stage logged 284/365 windows, all Optimal, when the shard hit the pre-registered 115-min budget.
  - The detached solve then ended on its own at about 16:35Z after window 283, with no traceback or exit code. Cause unknown: an OOM or a
    harness group kill; no memory line was logged.
  - The budget was not raised (§5 rule); nothing was written or lost.
- **2023 — solved, bundle held in its container** (`session_01WNeaDPLLqcuKm3C1xa3aif`, NOT archived):
  - The solve finished exit 0: 365/365 Optimal, 0 unserved, 74 of 147 integers. Its report has the wall row above and class TWh / prices.
  - GitHub refused the push: `dispatch/2023_P1.parquet` is 107,801,580 B, over the 100 MB file limit.
  - The shard split it losslessly (3 parts, sha256 `f0b881477933621f2be238188804ded2ab1b2e9aa39746fcf9025919f7df091b`, re-verified).
  - Committing the parts needed either a soft reset of its own unpushed commit (`d0a8481c`) or a restore onto a fresh branch. Its
    auto-mode classifier refused both, and neither the shard nor this lane routed around the refusal.
  - **The owner can unblock it** by approving, in that session, the commit + push onto `claude/ucmilp-miso-2023b`. Until then 2023 is
    unscored, and it is lost if that container is reclaimed. Per UC-DESK, the lane did not wait on it: the verdict is R on 2024 already.
- **Composition deviations, disclosed** (the SPP / NYISO / CAISO precedent):
  - The committed `_ucmilp_compose_span.py` aborts on `gas_price_override` and lacks the shared-frame respan.
  - A scratch copy (committed for audit as `data/ucmilp_miso_span/readings/compose_miso_scratch.py.txt`) adds three things:
    `gas_price_override` plus the keeper's two per-year reserve flags in `PER_YEAR_FIELDS`; the keeper's `config_partition_overrides`
    carried into `meta.json`; and the W0 composer's `_respan_shared_inputs`, called after `meta.json` exists.
  - No repo script was edited. The composite was built at `results/calibration/ucmilp_miso_dryrun` (gitignored) and is the scored span.
- **Recipe gate:** passed on all five legs. Every keeper-recorded field is equal; the extra fields the legs record are the `uc_*` defaults,
  `coal_sync_floor_release=False` and the 13 default-off fields of Addendum H.
- **Scoring artefacts:**
  - `dashboard_add_run.py --no-prune` wrote a sidecar and payload solely so `calibration_verdict.py` would score the composite. Both were
    moved out of the tree (scratchpad) and never committed, and no bench part changed.
  - A first registration attempt died silently in an unswapped 16 GB container; it was rerun after `prepare_solve_container.py`.

## 3. D-6 card (verbatim-ready)

> **UC-2-MISO (keeper + `unit_commitment_milp=true`, every conduct floor kept, pin `eab17188`): R.** 5 of 7 years composed (2022 budget
> stop; 2023 solved, bundle held in its container). Under ruling (a) the UC acts on **71–77 of 139–167** gated clusters: MISO's yard-pinned
> coal keeps its budget identity, so the stage commits gas and unpinned coal only.
>
> **What it fixes:**
> - Gas cycling: CC starts 1.3–1.6× → 0.36–0.51× CEMS; ST_GAS 4.5–6.4× → 0.28–1.07×.
> - Price body $0.0–0.9/MWh lower; 2020 C3a +10.2 → +10.0 % (FAIL → PASS, the narrowest possible).
> - The ≤ $15 tail where actuals have one: 2020 8 → 85 h, 2024 6 → 182 h.
> - Lower-tercile error down every year.
>
> **What it breaks:**
> - 2024 sheds 2,760 MWh more than the keeper in the 26 Aug event (kill #3).
> - The kept ST_GAS p25 floor stacks with the UC (+1.3–2.0 TWh/yr forced): C8 ST_GAS PASS → FAIL in 2019 / 2020 / 2025 (2019 also with
>   MECH 28 removed).
> - C4 gas 2021 PASS → FAIL.
> - C3b 2021 moves the wrong way (0.219 → 0.221).
> - Coal cycling is untouched.
>
> **Cost and housekeeping:**
> - 3.0–5.2× the year's own P0+P1 (3× ruled); uplift 0.7–1.5 %.
> - Every window Optimal; defect 5 is fixed.
>
> **Options:** (a) **record R, stage default-off for MISO** (recommended); (b) hold for a floors-off MISO arm (the SPP-B analogue:
> `st_gas_mustrun_per_plant=false`). SPP-B showed the UC alone under-commits steam gas, so (b) is not expected to clear C1 ST_GAS. It would
> also leave the yard-coal integers demoted unless ruling (a) is revisited. (c) hold.

## 4. Where each bundle is and what a promotion would cost

| artefact | where | promotable? |
|---|---|---|
| five leg bundles (full, incl. `dispatch/<y>_P1.parquet` 92.6–103.6 MB, and `unit_hourly_<y>` 90–99 MB, which rode along under the out-dir negation and stays off `main`) | `claude/ucmilp-miso-2019` @ `8e3e53b4` · `-2020` @ `98578010` · `-2021` @ `7b3575a3` · `-2024` @ `4bbbe13b` · `-2025` @ `3521f9f1` (all parented on the pin) | yes in form (rule 34); **no promotion proposed** |
| 2023 bundle | the 2023 shard container only (local commit `d0a8481c` + scratchpad backup) | not until pushed |
| composed span (5 years) | slim copy in this PR: `docs/records/miso/ucmilp/data/ucmilp_miso_span/`; `readings/` holds the control and arm `calibration_verdict --json`, M1/M3/M4 for both arms, the shard wall lines and the scratch composer | not registered (E13) |

**Cost of the attempt:** 7 span containers at `eab17188` (69–121 min each), on top of the 7 at `2f872a62` and 2 bench containers recorded
in Addenda A–D. **Cost to reproduce the arm:** seven shards of about 80–90 min each, and 2022 needs a budget of at least about 3.5 h.
Promotion is not recommended. Shard branches are transport (rule 33); the owner may cut the five `claude/ucmilp-miso-<y>` branches when
this PR merges (a session cannot, 403).

## 5. Routed findings

1. **GitHub's 100 MB file limit vs rule 34 for MISO.** MISO's `dispatch/<y>_P1.parquet` is 92–108 MB, so a year above 100 MB cannot be
   pushed whole, and auto-mode refused the history edits a split needs once a commit exists. The shard prompt should split before the
   first commit (`split -b 50000000` plus a sha256, a `.gitignore` line for the original). The shard's out-dir negation should also
   re-ignore `unit_hourly_<y>.parquet`. → `shard_prompt.py` owner.
2. **`_ucmilp_compose_span.py`** still lacks `gas_price_override` / per-year partition fields and the respan (now the fourth lane to work
   around it). → engine lane.
3. **MISO 2022 P0 wall** has doubled since the first pin (1,706 → 3,560 s), and it alone breaks a 2-h shard. → UC-SPEED / desk.
4. **The PRECOMMIT §1 recipe gate** listed only the UC fields; default-off fields absent from the keeper's record must be named in the
   template (Addendum H).

## Log entry

- 2026-10-10 · UC-2-MISO-R2 `session_01FZXtSAEvH3DJLVu9bkXD6h` (Opus) · `claude/ucmilp-2-miso-ab-m6z4` · zero LP in the parent · relaunch
  at `eab17188` under Addendum F (pin moves, nothing else) · 7 shards: 5 legs solved and pushed (2019 / 2020 / 2021 / 2024 / 2025), 2022
  budget stop, 2023 solved but held in its container (100 MB file limit + classifier) · every window Optimal, 0 time-limit hits · integer
  set 71–77 of 139–167 (ruling (a)) · T1 met (+10.2 → +10.0 %), T2 wrong sign, T3/T4 right sign · kill #3: 2024 unserved +2,760 MWh; C8
  ST_GAS 2019/2020/2025 and C4 gas 2021 flips; the kept ST_GAS floor stacks +1.3–2.0 TWh/yr · wall 3.0–5.2× · uplift 0.7–1.5 % ·
  **verdict R**; matrix cell `unit_commitment_milp` × MISO stamped R.
