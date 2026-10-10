# RESULT — UC-2-ERCOT: A/B of the MILP unit-commitment stage on ERCOT, 2026-10-10

**Verdict: R. Kill #3 fired on stage 1: one real control flip. The flip is marginal and it sits beside a real gain.**
The flip is 2024 C3b price shape, 0.198 PASS → **0.201 FAIL** against a ≤ 0.20 band (+0.003). PRECOMMIT §3 named this row in
advance as the one with the least headroom (0.002). In the same year the UC moves C3a price mean from −11.3 % FAIL to
**−6.3 % PASS**. It also clears the 2019 C3b miss (0.216 → 0.078) and meets the T2 and T3 target bars in both target years. The rule was
fixed before any number existed, so the verdict is R. It should not be read as a clean loss (§4).
Stage 2 (2021, 2022, 2023): **not run, verdict reached** (Addendum C item 3). Nothing registered; nothing promoted; nothing deleted.

Lane `UC-2-ERCOT`; this RESULT by UC-2-ERCOT-R2 (`session_01XuAMGVx2AbZ1PikaqHeTG7`, Opus), which took over from the Fable
session `session_012x78eXKGe21mGbQeVK54Z6`. Desk UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`). PRECOMMIT and Addenda A–D:
`PRECOMMIT-ucmilp-ercot-ab-2026-10-10.md`. **Pin `eab17188c75cd0332f9323ed3464c62bc0cd1848`** (uc-1.2 + UC-1-FIX-3; G-DRIFT in
Addendum D: control INERT). Arm: `replay_keeper.py results/calibration/closeout_ercot_l1_span --years <y> --set
unit_commitment_milp=true --set ercot_gas_commitment_bridge=false`. Control: the keeper `2026-10-02-closeout-l1-coal-fuel`'s
committed bundle (rule 29(b)).

## 1. Gate table (control → arm; `calibration_verdict.py`, rubric 3.20; per (criterion, key, year))

| year | criterion | control | arm | read |
|---|---|---|---|---|
| 2024 | **C3b price shape** | 0.198 PASS | **0.201 FAIL** | **PASS → FAIL: kill #3** |
| 2024 | C3a price mean | −11.3 % FAIL | **−6.3 % PASS** | FAIL → PASS (§2 declared this row a cost expected to worsen; it improved) |
| 2019 | C3b | 0.216 FAIL | **0.078 PASS** | FAIL → PASS |
| 2020 | C3b | 0.208 FAIL | 0.204 FAIL | right sign, at the T3 bar |
| 2025 | C3b | 0.125 PASS | 0.082 PASS | better |
| 2019 / 2020 / 2025 | C3a | +6.2 / +2.5 / −9.2 % PASS | +0.1 / +6.9 / −2.2 % PASS | 2025's tight row (0.8 pt headroom) moved to 7.8 pt |
| 2019 / 2020 | C1 CC_REGULAR | +9.21 / +10.17 TWh FAIL | +8.31 / +9.29 FAIL | right sign |
| 2019 / 2020 | C1 COAL_PRB | −10.79 / −11.85 TWh FAIL | −9.15 / −10.28 FAIL | right sign |
| 2024 | C1 CC_REGULAR / COAL_PRB / ST_GAS | −4.45 / −0.97 / −1.22 TWh PASS | −4.39 / +0.15 / −4.78 PASS | no flip |
| 2025 | C1 COAL_PRB | +0.87 PASS | +1.05 PASS | no flip (the named tight row) |
| 2019 | C3c tail | 90 vs 106 h (0.85×) PASS | 76 h (0.72×) PASS | above the 53 h flip line |
| 2020 / 2024 / 2025 | C3c | CAVEAT 22 / 11 / 0 h | "FAIL" 23 / 15 / 0 h | **attestation artefact** (§8 of the PRECOMMIT): the magnitudes moved up or held; not a flip |
| 2020 | C8 ST_GAS | 23.6 % PASS | 36.9 % as scored → **22.3 % with MECH 28 removed (R4)** | not a flip under R4 |
| 2019 / 2024 / 2025 | C8 ST_GAS | 17.6 / 15.6 / 21.1 % PASS | 28.0 / 25.5 / 29.0 % as scored; 18.2 / 18.2 / 15.6 % under R4 | no flip |
| all | P1 status · unserved | Optimal · 0 MWh | Optimal · **0 MWh** | met |
| all | determination | NOT-YET | NOT-YET (UNATTESTED artefact) | reported, not gating |

Flip count, real: **1** (2024 C3b). Raw diff: `data/ucmilp_ercot_span/readings/flipdiff.txt`; R4: `readings/c8_r4.txt`.

## 2. Target readings (PRECOMMIT §2; M1–M4 by `_ucmilp_benefit_screen.screen_year` on the arm span)

| # | reading | control | arm | bar | met? |
|---|---|---|---|---|---|
| T1 | CC_REGULAR starts vs CEMS, 2019 | 491 vs 3,070 (0.16×) | **369 (0.12×)** | ratio ∈ [0.40, 2.5] | **wrong sign** |
| T1 | CC_REGULAR starts vs CEMS, 2020 | 1,901 vs 3,489 (0.55×) | **811 (0.23×)** | ratio ∈ [0.74, 1.35] | **wrong sign** |
| T2 | M2(b) CC online at near-min-load while CEMS off, 2019 | 9.34 TWh | 3.09 | ≤ 4.67 | met |
| T2 | same, 2020 | 8.94 TWh | 4.39 | ≤ 4.47 | met |
| T3 | C3b 2019 / 2020 | 0.216 / 0.208 | 0.078 / 0.204 | ≤ 0.208 / ≤ 0.204 | met / met at the bar |
| T4 | C1 CC 2019 / 2020 | +9.21 / +10.17 | +8.31 / +9.29 | ≤ +8.6 / ≤ +9.1 | met / short (right sign) |
| T4 | C1 PRB 2019 / 2020 | −10.79 / −11.85 | −9.15 / −10.28 | ≥ −9.4 / ≥ −9.9 | met / short (right sign) |
| T5 | ≤ $15 hour ratio 2019 / 2020 / 2024 / 2025 | 0.14 / 0.36 / 0.34 / 0.26 | 0.23 / 0.41 / 0.30 / 0.24 | sign up | up / up / down / down |
| T5 | < $0 hour ratio | 0.04 / 0.00 / 0.07 / 0.02 | 0.00 / 0.17 / 0.00 / 0.00 | sign up | mixed |
| T6 | reserve dormancy share (model vs actual) | 0.96–1.00 | 0.95 / 0.97 / 0.995 / 0.999 | falls | no move |

**The UC decommits the CC fleet; it does not start it more.** CC_REGULAR starts fall in every year (2019 491 → 369, 2020 1,901
→ 811), further from CEMS (3,070 / 3,489). The same stage removes most of the near-min-load CC hours (T2). The keeper's CC
over-run therefore shows up as fewer, longer runs, not as the measured cycling. T1 alone would read R under §7.1, independently of the kill.

## 3. Structure and cost readings

| # | reading | 2019 | 2020 | 2024 | 2025 |
|---|---|---|---|---|---|
| S1 | MECH 28 (`uc_schedule`) forced TWh: CC_REGULAR / ST_GAS | 2.25 / 1.18 | 3.14 / 1.48 | 4.41 / 1.01 | 3.58 / 1.60 |
| S1 | kept `st_netload_drag` and the drag's share of ST_GAS | 28.0 − 9.8 = 18.2 % | 22.3 % | 18.2 % | 15.6 % |
| S2 | ST_GAS starts, model vs CEMS (control model) | 446 vs 1,011 (2,032) | 434 vs 952 (2,377) | 380 vs 736 (2,409) | 273 vs 981 (2,339) |
| S2 | COAL_PRB starts vs CEMS (control) | 92 vs 17 (87) | 211 vs 23 (166) | 70 vs 40 (59) | 27 vs 31 (28) |
| S4 | integer clusters / clusters; class-fallback no-load | 62 / 141; 49 | 61 / 141; 50 | 61 / 139; 49 | 61 / 140; 49 |
| S5 | ST_GAS short-on energy (runs < UT) | 4.14 → 0.90 TWh | 5.04 → 0.77 | 4.32 → 0.84 | 3.61 → 0.30 |

ST_GAS swings from over-cycling at 2.0–3.3× CEMS to under-cycling at 0.3–0.5× CEMS; min-up removes the drag's short runs (S5).
Coal starts are **not reachable by this arm**: under uc-1.2 the eleven yard-pinned coal clusters carry no integer (Addendum
B.2). The coal rows keep their incumbent floors, and 2019 shows 62 integer clusters rather than 61 (cause not traced; the demotion is
per-year on the budget pin, so one cluster presumably was not fully pinned in 2019).

**Wall (GATESPEC §6.1; ratio = total ÷ the shard's own P0+P1, the declared proxy):**

| year | P0 s | UC s (pass 1 + pass 2) | P1 s | total s | ratio | MILP mean / p95 s | nodes p50 / p95 | gap p95 | TL hits | warm feasible | integers/window | peak RSS GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 250.2 | 8,993 + 8,697 | 327 + 287 | 18,756 | **21.7×** | 23.5 / 63.7 | 15 / 124 | 9.9e-4 | 0 | 0 / 365 | 2,232 | 12.19 |
| 2020 | 281.1 | 8,955 + 8,453 | 251 + 205 | 18,341 | **24.9×** | 22.8 / 50.1 | 20 / 99 | 9.6e-4 | 0 | 0 / 365 | 2,196 | 13.36 (cgroup) |
| 2024 | not captured | 6,989 (pass 2 skipped) | 372 | not captured | ≈ 9–10× (UC ÷ P1 + typical P0) | 18.4 / 41.9 | 21 / 106 | 9.4e-4 | 0 | 0 / 365 | 2,196 | 11.4 (UC) |
| 2025 | 510.3 | 8,470 (pass 2 skipped) | 463.1 | 9,603 | **9.9×** | 22.5 / 64.5 | 15 / 132 | 9.9e-4 | 0 | 0 / 365 | 2,196 | 12.61 |

**The double-UC cost.** ERCOT's adaptive-expectation step re-solves the year when it finds spike days. In 2019 and 2020 that
reran the whole UC stage (pass 2 ≈ pass 1, about 2.4 h each). In 2024 and 2025 the check skipped pass 2. FIX-2 measured the
2020 pass-2 schedule as identical to pass 1 (0 of 61 × 8,016 cells differ), so reusing the pass-1 schedule would halve the
2019/2020 wall: 21.7× → ≈ 12× and 24.9× → ≈ 13×. Against the owner's 3× (D-2, "Keep 3×; fund speedup"): reported, not judged.
The warm start is rejected in every window (`warm_feasible` 0 / 1,460), as the L1 gate found.

**W3, uplift share: not computable as specified; an engine finding.** `uc_uplift_<y>` totals $103.9 M (0.77 % of energy
cost) in 2024 and $139.3 M (0.80 %) in 2025. In 2019 and 2020 it reads **$15.0 B and $13.6 B** (84 % and 133 % of energy
cost). Cause, read from `unit_marginal_<y>`: the UC's per-unit-hour floor (MECH 28, `mlf·p̄·u`) is applied to every member
row of a cluster. ERCOT's CAMPD-binned plants split into committed / economic / `_peak…_peak5` tranches, and the peak
tranches carry the keeper's authorized peak-band offer multiplier. In 2019, **5.81 TWh** of floored output ran on tranches
offered at a median $2,821/MWh (CC_REGULAR 5.31 TWh, 155 units; ST_GAS 0.50 TWh). `uplift_from_bundle` prices that energy at
the P1 offer `mc`, assuming it equals `mc_base` on integer clusters. D-3 zeroes the markup on those clusters but not the
offer-band multiplier, so the assumption fails. In 2024 the same pattern is 1.13 TWh. Two consequences, routed to the engine
lane, not fixed here (this lane edits no `src/`):
(1) the uplift sidecar overstates make-whole wherever offer bands exceed 1.0;
(2) the floor allocation itself forces the most expensive tranches of a committed plant to run, where a merit-order fill of
the cluster floor would load the cheap tranches first. Dispatch cost is not the scored object here (prices are the duals and
the floors are bounds), but (2) is a structural question for any ERCOT arming.

## 4. D-6 card (verbatim-ready)

> **ERCOT, `unit_commitment_milp`: record R with evidence.** At uc-1.2 (`eab17188`), arm = UC on + gas bridge off, every other
> floor kept, four stage-1 years (2019, 2020, 2024, 2025), all 1,460 windows Optimal, 0 unserved. **One control flip, and it
> is marginal:** 2024 C3b 0.198 → 0.201 against a 0.20 band. In the same run the UC turns 2024 C3a from −11.3 % FAIL to −6.3 %
> PASS, 2019 C3b from 0.216 FAIL to 0.078 PASS, and meets the M2(b) and C3b target bars in 2019 and 2020. Against that: CC
> starts move **away** from CEMS (0.16× → 0.12× in 2019; 0.55× → 0.23× in 2020), because the UC removes the near-min-load
> hours by decommitting, not by cycling. Coal is outside the arm (yard-pinned, no integer). The wall is 9.9–24.9× P0+P1
> against the 3× ruling (≈ 12–13× if pass 2 reused pass 1). The floor allocation loads peak-band tranches (5.8 TWh in 2019),
> which corrupts the uplift sidecar.
> Options: **record R (recommended)** · hold for an allocation fix (merit-order floor fill + uplift at `mc_base`) and a pass-2
> schedule reuse, then a fresh PRECOMMIT · promote on structure (not supported: T1 wrong sign, a pre-declared kill fired).

## 5. Bundles and cost

| artefact | where | promotable? |
|---|---|---|
| stage-1 legs (full, incl. `dispatch/<y>_P1.parquet`; `unit_hourly` left out per rule 15) | `claude/ucmilp-ercot-d-2019` `dd7fe8a8` · `-d-2020` `35d9d189` · `-d-2024` `2631ed81` · `-d-2025` `7814b011` (all parented on `eab17188`) | in form (rule 34); not recommended. Four of seven years, so a promotion would need 2021–2023 solved (≈ 3 × 8–11 h at this engine) |
| composed span `results/calibration/ucmilp_ercot_span` (4 years) | slim copy in this PR: `docs/records/ercot/ucmilp/data/ucmilp_ercot_span/` (21 MB: hourly sidecars incl. `uc_schedule`, `uc_uplift`; `uc_solve_log_<y>.json`; `meta.json`, `metrics.json`, `run_config*.json`; regenerated `legitimacy_diagnostics.json`; `readings/` = control and arm `calibration_verdict --json`, arm M1–M6, flip diff, R4 table, and the three scratch scripts) | not registered (E13) |
| `dc3860be` evidence legs (2024, 2025; Addendum B.2) | `claude/ucmilp-ercot-2024` `0c76c8c3` · `claude/ucmilp-ercot-2025` `df87a9be`; untracked from this lane branch on UC-DESK's ruling (17:38Z) | never scored |

**Composition, disclosed (PRECOMMIT §8).** A scratch copy of `_ucmilp_compose_span.py` (shipped in `readings/compose_ercot.py`;
no repo script edited):
- `PER_YEAR_FIELDS` ∪ the 13 fields on which the keeper's own `run_config_<y>.json` files disagree;
- an assertion that each leg's recipe equals the keeper's same-year recipe except for the two arm fields; fields new since the
  keeper, at their default, are allowed, as is the rule-26-deleted `unit_outage_dispatched_bin_live_denominator`;
- `_w0_compose_span._respan_shared_inputs`, called after `meta.json` is written.

Scoring used a local `dashboard_add_run.py --no-prune`. Its sidecar and payload were moved out of the tree and never committed;
no bench part changed. Both composer gaps remain routed to the engine lane.

**Cost.** Four span containers, 2.7–5.2 h each: about 16 container-hours with two UC passes in 2019 and 2020. Zero LP in the
parent. The four stage-1 shards were launched and archived after verification (rule 33); none are left alive. Earlier in the
lane: the `dc3860be` round (7 legs; 2 complete, 5 killed or budget-stopped) and three L1 bench runs. The owner may delete
`claude/ucmilp-ercot-d-{2019,2020,2024,2025}`, `claude/ucmilp-ercot-{2019,…,2025}` and
`claude/ucmilp-bench-ercot-2020-L1gate` once this PR merges (a session cannot: 403).

**Promotion question:** none is proposed. The lane recommends recording `R`. The local bundles do not survive this
container; the leg branches above hold the bytes.

## Log entry

- 2026-10-10 · UC-2-ERCOT (Fable `session_012x78eX…` → Opus R2 `session_01XuAMGVx2AbZ1PikaqHeTG7`) ·
  `claude/ucmilp-2-ercot-ab-e4w1` · zero LP in the parent.
  - Engine defects found by the lane's shards: L1 gate defects #3 (time-major TTC) and the bench harness; w118 (#5) and the
    P1-seam kill at `dc3860be`, both fixed in uc-1.2.
  - Relaunch at `eab17188`, staged (Addendum C): stage 1 = 2019/2020/2024/2025, 1,460/1,460 windows Optimal, 0 unserved.
  - **Kill #3 → R**: 2024 C3b 0.198 → 0.201 (band 0.20); offset by 2024 C3a −11.3 → −6.3 % (FAIL → PASS) and 2019 C3b
    0.216 → 0.078.
  - T1 wrong sign: CC starts fall further below CEMS. T2 and T3 met.
  - Wall 9.9–24.9× P0+P1. The double UC pass costs about 2× in 2019/2020.
  - Floor allocation loads peak-band tranches and corrupts the uplift sidecar (routed).
  - Stage 2 not run: verdict reached. Nothing registered; slim span under `docs/records/ercot/ucmilp/data/`; ERCOT cell
    `unit_commitment_milp` U → R.
