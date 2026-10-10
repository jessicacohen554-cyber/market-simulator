# PRECOMMIT — UC-2-MISO: pre-registered A/B of the MILP unit-commitment stage on every MISO backcast year, 2026-10-10

**Written and pushed BEFORE any span shard exists.** Every reading, bar, kill and budget below is fixed here and
fails closed; nothing is moved after a number comes in (GATESPEC §7.1, rule 1(c) by analogy). Lane
`UC-2-MISO` (session `session_016bPoPZ6beefv8kJUn8sQFH`, Fable), branch `claude/ucmilp-2-miso-ab-m6z4` off
`origin/main` `2f872a62`. Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on 2026-10-10 under the owner's
direction *"launch shards for other ISOs to test"*. Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7;
plan `docs/uc-milp-program-plan-2026-10.md` §3 (UC-2), §8.1 (R3–R5). Structure copied from the SPP precedent
`docs/records/spp/ucmilp/PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (+ Addenda A–D) so the two ISOs read side by side.
**Off the close-out plan's lever sequence (§3.3 MISO) by charter**: the UC program is the owner's cross-ISO test, not a
MISO close-out lever; the ledgered MISO misses (C1 ST_GAS 2019, C3b 2021 February, C3c tails, West/Plains congestion)
are not expected to move and are not read as targets.

## 0. Preconditions (checked before this file was written, zero LP)

| check | result |
|---|---|
| `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` at the pin ≥ 1 | **6** |
| the MISO keeper's `run_config.json` arms nothing in `UC_REFUSED_ALWAYS` (15 fields) | every refused field reads `False` — **0 armed** (`miso_gas_ecomin_online_floor=false`, `miso_commitment_posture=false`) |
| `UC_REFUSED_BY_RULING` at the pin | empty (no D-5 ruling commit for any ISO) |
| the control bundle and the keeper shard are unchanged since the SPP pin (`git diff --stat ae224faf 2f872a62 -- results/calibration/closeout_miso_nuc_span frontend/data/backcast/keepers/MISO.json`) | **0 files differ** |
| tooling byte-identical since the SPP pin (`shard_prompt.py`, `replay_keeper.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `scripts/probes/_ucmilp_compose_span.py`) | **0 lines differ**; only `scripts/diagnostics/bench_uc_ladder.py` moved (+19/−2, bench harness) |
| MISO golden, gate off | **PASS (engine-inert) by zero-LP input identity, all seven years** (`FINDING-ucmilp-golden-miso-recipe-gap-2026-10-04.md` §3): the faithful per-year recipe (`replay_keeper --years <y>`, which applies `enforce_single_recipe_partition`) gives `run_energy_solve` identical inputs at the keeper basis `f98c4564`, at main-without-UC and at the engine branch; the 2023–25 golden FAIL was the golden harness dropping the per-year reserve overlay, not drift |
| the control re-scored at HEAD (`calibration_verdict.py results/calibration/closeout_miso_nuc_span`, rubric 3.20) | reproduces the registered grade summary **8 scored / 4 target / 1 ledgered / 3 FAIL, NOT-YET** (fuelmix 2019 ST_GAS, 2021 CC_REGULAR; price_mean 2020; price_shape 2021) |
| benchmark freshness (`check_bench_freshness.py` tier) | **STALE BENCHMARK warning**: the seven MISO parts (`frontend/data/backcast/bench/MISO/<y>.json.gz`) do not reproduce under the builder at HEAD (payload fingerprint `1b89b7110328`). Disclosed, not fixed (not this lane's region; a `--rebuild-benchmark` is a keeper lane's step). Control and arm are scored against the SAME committed parts, so every control → arm delta is apples to apples; the absolute C1 actuals carry the warning |

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** MISO's designated keeper `2026-10-03-closeout-miso-nuc-r`, bundle
  `results/calibration/closeout_miso_nuc_span`, seven year-isolated legs 2019–2025 solved at
  `f98c456401918eba82c338676e303a90004bb94c`; its committed `metrics.json`, `legitimacy_diagnostics.json`, `hourly/*`
  and the status part `frontend/data/backcast/status/MISO.js` are the control readings.
- **Pin (every shard): `2f872a62a7cccadb6800555c11a73745dcdb89a4`** = `origin/main` at the merge of PR #7218 (engine
  uc-1.1 + UC-1-FIX + the UC-SPEED lean preset). `source_revision` is this full SHA, never a branch. The pin does not chase
  main.
- **Arm — ONE logical delta:** `replay_keeper.py results/calibration/closeout_miso_nuc_span --years <y>
  --set unit_commitment_milp=true`. **The "offs" set is EMPTY**: D-5 for MISO (desk-set under the owner's direction; owner
  may override) = keeper recipe + `unit_commitment_milp=true` + OFF for every `UC_REFUSED_ALWAYS` field the keeper arms —
  and the keeper arms none (precondition row 2), so the validator refuses nothing and no second `--set` exists. Every
  `uc_*` field stays at its declared default and is **never swept**:

  | field | value | source |
  |---|---|---|
  | `unit_commitment_milp` | `true` | the arm |
  | `uc_window_hours` / `uc_lookahead_hours` | 24 / 12 | DESIGN §3 (plan E2) |
  | `uc_mip_rel_gap` | 1e-3 | DESIGN §3 (plan E4) |
  | `uc_window_time_limit_s` | 600 | DESIGN §3 declared placeholder |
  | `uc_integer_scope` / `uc_noload_source` / `uc_boundary_mode` | `physics` / `campd_regression` / `p0_targets` | DESIGN §1.1, §1.2, §2.2 |
  | `uc_prefixing` | `false` | DESIGN §2.3 |
  | `uc_solver_preset` | **`lean`** (new since the SPP A/B, registry default) | UC-SPEED FINDING §3: paired equivalence PASS on 62/62 window problems vs the uc-1.1 path (max rel. objective delta 8.9e-4 < the 1e-3 gap); −23 % / −7 % wall |

- **Rule-19 census, MISO (UC-0 FINDING §4; keeper D-2 rows at HEAD).** Every floor is KEPT, mirroring SPP arm 1 (owner
  R5) so results compare across ISOs:

  | kept floor | class | keeper forced energy, TWh/yr (share of class) | stacking risk SPP showed |
  |---|---|---|---|
  | `st_gas_mustrun_per_plant` (measured p25 level, `st_gas_mustrun_oom_level`, `mustrun_layup_window_mask`) | ST_GAS | 4.84 / 4.32 / 5.23 / 5.21 / 3.32 / 3.52 / 4.18 (26.3 / 20.0 / 31.3 / 28.5 / 15.4 / 14.9 / 20.0 %); the C8 cap is 30 % and 2019 sits 3.7 pt under it | **the hard case**: under the UC the SPP floor's own forced energy ROSE 1–1.2 TWh/yr and C8 ST_GAS crossed the cap in four years (SPP RESULT §1); the UC and the kept floor stack |
  | `coal_mustrun_per_plant` + `coal_mustrun_online_pmin` (measured yard-grain floors) and `reliability_floor` | COAL_BIT / COAL_PRB | reliability_floor 0.13–0.93 / 0.01–0.68 TWh (≤ 1.2 %) | **CC energy → coal**: SPP moved 6–8 TWh/yr from CC_REGULAR to COAL_PRB (no-load and start paid once, 36-h min-up keeps coal online through troughs); MISO's control C1 has CC_REGULAR 2021 already FAIL (−8.15) and COAL_PRB 2021/2022 at +5.03 / +5.72 of ±8.00 |
  | `ct_netload_drag` (the D-2 name at HEAD for the CT limb of `reliability_floor`, declared window h14–21) | CT_PEAKER | 10.19 / 6.80 / 8.44 / 7.29 / 5.84 / 4.26 / 4.50 TWh (98.9 / 79.4 / 93.3 / 86.7 / 49.0 / 31.9 / 36.4 %), grounded above the 15 % budget every year on the D-4 window + D-1 shape route | CT is not an integer class (fast start, rule 18); a change in the grounding route (D-1 profile r / CV ratio) is a C8 flip |
  | physical: `nuclear_mustrun`, `chp_steam`, `hydro_min_flow`, `hydro_ror_flat`, `firm_import` | — | D2-exempt | untouched |

  `miso_commitment_posture` (R, SPP-102/103 analogue; UC-0: the posture relaxation held 3.7–4.2× the measured online
  capacity) stays off and is not re-tested; `miso_gas_ecomin_online_floor` (I, miso-286) stays off. The UC respects every
  kept floor as an input (DESIGN §5); D-2 attributes each under its own id and the UC schedule under MECH 28.
- **Per-year recipe (FINDING golden-miso-recipe-gap).** The keeper's `meta.json` carries a `config_partition_overrides`
  block: 2023, 2024 and 2025 add `miso_measured_reserve_requirements=true` and `miso_reserve_online_gated=true` (the
  `miso_rbdc_regspin` reserve family); every year carries its own `gas_price_override`, `weather_year` and
  `gas_offer_margin_anchor`. `replay_keeper.py --years <y>` applies `enforce_single_recipe_partition` and
  `flipped_default_overlay`, so the shard command carries them. **Verification gate per leg (§8):** the leg's
  `run_config_<y>.json` `scenario_config` must equal the keeper's `run_config_<y>.json` `scenario_config` except for
  `unit_commitment_milp` and the ten `uc_*` fields (absent from the keeper, present at their defaults in the leg); any other
  differing field is a recipe break and the leg is not composed.
- **Pricing (owner ruling R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC objective;
  make-whole in `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (owner ruling R4, D-4):** UC min-load energy is REPORTED under MECH 28 and not budgeted. As in SPP, the scorer at
  this pin budgets `uc_schedule` energy in the D-2 share; the RESULT recomputes C8 with MECH 28 removed beside the scored row.
- **D-2 ceiling (owner, 2026-10-09 "Keep 3×; fund speedup"):** the wall ratio is REPORTED per year against the 3× ceiling,
  never judged by this lane (a ratio above it is a cost finding, GATESPEC §7.3).
- **Not a matrix re-test (rule 28).** The cell this lane feeds is `unit_commitment_milp` × MISO (minted `U` by UC-1); the
  integer commitment state is a different object from the relaxed posture (`miso_commitment_posture`, R) and from the
  EcoMin floor (`miso_gas_ecomin_online_floor`, I). §5.4 DO-NOT-REDO honoured: no `miso_coal_night_floor`, no
  `internal_congestion_split`, no offer-band retune, no second `--set`.
- **DOF (rule 21):** zero free parameters added (UC-0 FINDING §5: physics S / UT / DT / mlf per class from CAMPD plant-basis
  run lengths and the measured min-load fractions; no-load = CAMPD per-unit intercept × delivered fuel, class-mean-per-MW
  fallback share reported from `uc_solve_log_<y>.json clusters[].src`). The keeper's authorized price tuning
  (`offer_curve_by_group`: ×1.10 on eight non-steam fossil classes, CC/ST_GAS at the pre-lift table) rides unchanged.

## 2. Target readings (fixed ex ante; bar = half the distance to the gate band, the closeout convention)

Control values are the keeper's registered records (rubric 3.20, `calibration_verdict.py --json` at HEAD). "met" is
decided on the composed span's `calibration_verdict.py` output and the zero-LP re-measurement of UC-0's M1/M3/M4 on the
arm bundle (`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported, pointed at
`results/calibration/ucmilp_miso_span` — the board's conventions).

| # | reading | control | sign expected | bar (met iff) |
|---|---|---|---|---|
| T1 | MISO 2020 C3a mean LMP (model/actual − 1; 24.21 vs 21.97 $/MWh) | **+10.2 %** FAIL (band ±10 %) | negative (body down) | arm ≤ **+10.1 %** (half of the 0.2-pt distance; the band itself is ≤ +10.0 %). The bar is small by construction: the magnitude is reported, and a move of ≥ 1 pt is the one UC-0 §3 called "confirmed in direction, weak in magnitude" |
| T2 | MISO 2021 C3b NRMSE | **0.219** FAIL (≤ 0.20) | down | arm ≤ **0.2095** |
| T3 | M4 reserve dormancy 2023 / 2024 / 2025 (share of hours with model reserve MCP < $1) vs the MISO ASM RT MCP | model 1.000 / 0.999 / 0.998 vs actual 0.346 / 0.415 / 0.492; mean MCP model $0.00 / 0.23 / 0.17 vs actual $2.34 / 2.54 / 3.12 | dormancy share falls; mean MCP rises | sign only; magnitude reported (MISO is the program's reserve-pricing target; 2019–22 unmeasurable, MISO purged the ASM files) |
| T4 | low-price-hour count ratio model/actual, hours ≤ $15 (M3), 2020 and 2024 (the two years with ≥ 500 actual hours) | 2020: 8 / 1,021 = 0.008 · 2024: 6 / 597 = 0.010; every other year 0 model hours | rises toward 1 | sign only; magnitude reported for every year |
| T5 | online capacity vs the measured series | the GATESPEC names "MISO ASM cleared" as the comparator. **What is on disk** (`data/raw/MISO-AS/asm_rt_cleared_mw_<2023–25>.parquet`) is cleared RESERVE MW by region × product (reg / spin / supp / str), not an online-capacity series; no online-MW series exists in the repo for MISO | — | reframed ex ante, as SPP S3 was: (a) the arm's `online_mw` from `uc_schedule_<y>.parquet` is reported against the keeper's available MW (model-internal); (b) the arm's reserve provision by product vs the ASM cleared MW 2023–25 is reported as the ASM-side comparator. Neither is an input |

**Expected costs, declared, not kills (UC-0 F2 analogue; SPP RESULT §0).** The UC's price-body shift was DOWN in every
SPP year ($0.4–2.9/MWh). MISO's model-LOW years are 2021 (C3a −8.4 %, PASS with **1.6 pt** headroom), 2022 (−6.9 %, 3.1 pt)
and 2025 (−3.7 %, 6.3 pt). A SPP-sized shift takes 2021 through its band: that is a control flip (§3, kill #3) and is named
now so it cannot be re-read as a surprise. Model-high years that a trough fix helps: 2020 (T1), 2019 (+6.2 %), 2023
(+4.8 %), 2024 (+2.5 %).

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered MISO year, any criterion, any class row** (`calibration_verdict.py`
per-(criterion, key, year) status diff vs the keeper). A CAVEAT → FAIL on C3c through the model (a magnitude move) counts
as a flip; the attestation artefact below does not. A grounded-above-budget C8 row (CT_PEAKER 2020–2025) that loses its
grounding is a flip. The rows with the least headroom, named now:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| 2021 | C3a | −8.4 % PASS | **1.6 pt** | model-low; a body-down shift crosses it |
| 2022 | C3a | −6.9 % PASS | 3.1 pt | model-low |
| 2025 | C3a | −3.7 % PASS | 6.3 pt | model-low, train tier |
| 2019 / 2023 / 2024 | C3a | +6.2 / +4.8 / +2.5 % PASS | 3.8 / 5.2 / 7.5 pt | model-high: body down helps |
| 2020 | C3b | 0.147 PASS | 0.053 | shape may re-order |
| 2022 / 2019 | C3b | 0.127 / 0.091 PASS | 0.073 / 0.109 | shape |
| 2020 | C1 ST_GAS | −7.09 TWh PASS (±8.00, ±3 pp) | **0.91 TWh** | the kept floor's class; SPP's ST_GAS composition moved |
| 2021 / 2022 | C1 ST_GAS | −5.36 / −5.67 TWh PASS | 2.64 / 2.33 TWh | same |
| 2022 | C1 CC_REGULAR | −5.48 TWh PASS | 2.52 TWh | CC → coal is the SPP direction; 2021 already FAIL (−8.15), 2019 +3.17, 2020 −1.24, 2023 −0.87, 2024 +2.61 |
| 2022 / 2021 | C1 COAL_PRB | +5.72 / +5.03 TWh PASS | 2.28 / 2.97 TWh | coal gains under the UC in SPP |
| 2022 / 2020 | C1 COAL_BIT | +5.21 / −4.66 TWh PASS | 2.79 / 3.34 TWh | same |
| 2024 / 2022 / 2021 | C1 CT_PEAKER | −4.64 / −4.60 / −4.11 TWh PASS | 3.36 / 3.40 / 3.89 TWh | CT rose 0.9–2.4 TWh in SPP |
| 2019 | C8 ST_GAS | 26.3 % PASS (cap 30 %) | **3.7 pt** | the stacking risk (§1); 2020 / 2025 20.0 %, 2021 31.3 % and 2022 28.5 % are immaterial (< 2 % of load, not gated) |
| 2020–2025 | C8 CT_PEAKER | grounded above budget (D-4 window clear; profile r 0.89–0.98, CV ratio 1.8–2.3) | — | the conditional pass must survive |
| 2020 | C3c | PASS (model 0 h vs 8 h, small-count |Δ| ≤ 10 h) | 10 h | a model tail > 18 h flips it |
| 2019 / 2021 / 2022 / 2023 / 2024 / 2025 | C3c | CAVEAT, ledgered (0 / 0 / 0 / 0 / 7 / 9 h vs 17 / 48 / 116 / 30 / 37 / 88 h) | — | **artefact named now** (SPP Addendum D item 3): the probe span carries no `calibration_attestation.json`, so C6 reads UNATTESTED and the rule-22 ledger route is unavailable → CAVEAT reads FAIL on the arm whatever the model does. Compared on magnitude only; not a flip |
| 2025 | C1 (all classes) | SKIPPED (preliminary EIA-923 vintage) | — | not gated on either side |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper; no new D-4 FAIL row
beyond the keeper's own (plant 990 reliability_floor × ST_GAS 2019; the `st_gas_mustrun_per_plant` conduct rows).

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, COAL_PRB, COAL_BIT, COAL_LIGNITE, ST_GAS) and ISO-wide | 0 (no UC) | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28; C8 recomputed with and without MECH 28 (R4) |
| S2 | starts per plant-year vs CEMS (UC-0 M1, on-threshold 1 % of available cap), 2019…2025 | CC_REGULAR 2,291 / 2,893 / 3,304 / 2,974 / 2,877 / 2,437 / 2,552 vs CEMS 1,783 / 1,902 / 2,403 / 2,692 / 2,036 / 1,726 / 1,622 (1.1–1.5×) · COAL_PRB 768 / 903 / 435 / 438 / 530 / 509 / 538 vs 275 / 332 / 327 / 301 / 283 / 275 / 241 (1.3–2.8×) · COAL_BIT 535 / 485 / 362 / 235 / 288 / 252 / 282 vs 156 / 123 / 83 / 149 / 105 / 72 / 85 (1.6–4.4×) · ST_GAS 2,058 / 2,423 / 1,749 / 1,791 / 1,903 / 1,766 / 1,854 vs 407 / 380 / 369 / 569 / 291 / 396 / 405 (3.1–6.5×) — the model over-cycles every slow class | `screen_year` M1 on the arm; `uc_schedule_<y>.parquet` Σ`v` per cluster as the engine's own count. Sign expected: every class's starts fall toward CEMS; SPP overshot to 0.5–0.8× (CC) and 0.14–0.4× (coal, ST_GAS) — reported either way |
| S3 | online capacity (T5 reframed) | — | `online_mw` vs keeper available MW; reserve provision vs ASM cleared MW 2023–25 |
| S4 | integer set and fallback shares | UC-0 M6: **159 MISO plant clusters, 90.4 GW, 5,724 integers per 36-h window** — the largest UC in the program (PJM 155 / 5,580) | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| S5 | the CC ↔ coal energy swap | C1 rows above | ΔTWh by class vs control, every year |

## 5. Cost readings (reported; D-2 ceiling 3× is reported, never judged here)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all seven years |
| W1-denominator | the keeper bundle records no P0/P1 seconds. **Declared proxy (SPP precedent):** baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line, so ratio = total / (P0 + P1) in one container. Known on-record MISO LP wall for scale only: MISO 2023 P0 320 s + P1 254 s, total 675 s, peak RSS 13.3 GB, 29.6 M columns (`wallclock-baseline-2026-07.md` §3a via ASSESSMENT §5) | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` ÷ Σ_t λ_P1 × load (wholesale energy cost from `hourly/system_<y>.parquet`) | ≤ **2 %** (sanity; SPP read 1.0–4.4 %) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise §6 kill) |
| W5 | **memory**: MISO peaks at the 13.34 GiB cgroup cap in P0 (UC-0: 13.3 GB; `prepare_solve_container.py` provisions swap). The UC stage itself is small (SPP: 4–5 GB) | an OOM kill (return code −9) in any leg = STOP and report (the PJM goldens OOM'd); never a relaunch with a changed setting |

**Shard budget rule (fixed now, value filled in Addendum A after the L1 gate):** budget per shard =
ceil(1.3 × the L1-month extrapolation), where the extrapolation = the bench capture's P0+P1 seconds + 365/31 × the January
rolled-month wall + a P1 re-solve (= the capture's P1 share) + 10 min of hydrate/regenerate/push, in minutes. If the bench
gives no usable number the budget is **90 min**. One shard commit ≤ 20 min of runtime (rule 32); a shard approaching the
budget with no artifact stops and reports.

## 6. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"): an
   engine defect, routed to UC-DESK, never a tuning invitation.
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed runs of
   the same recipe-year. With one shard per year this is exercised only if a relaunched shard (PENDING > 45 min rule) and
   its predecessor both complete; otherwise recorded "not exercised".
3. **A control flip** (§3) in any registered year.

## 7. Verdict rule (fixed) and the D-6 card

- **K candidate** — T1 and T2 met, T3/T4 signs right, no kill, every leg Optimal: recommend the owner's D-6 card read
  "promote on structure"; the lane never promotes (rule 31; UC-4 is the desk's slot).
- **R** — any target reading moves the wrong way past its control (C3a 2020 up, C3b 2021 up), or any kill fires.
- **I** — no kill, no wrong-sign move, but |Δ| below the bar on T1 and T2 (GATESPEC §7.2: "the relaxation was already tight
  here" is a finding).
- Mixed: the verdict is the worst of the target rows, stated row by row; the declared 2021/2022/2025 cost is reported beside
  it. The determination (`iso_determination`) is reported, not gating: MISO is NOT-YET on the keeper's open rows and stays
  so unless every failing row clears, which no reading here predicts.
- The RESULT carries the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve plan (rules 16, 32–36)

- **L1 gate first (task 0; new, from SPP's two engine defects).** One bench shard at the pin, MISO 2020: rung L1 (one
  window, `--save-capture`) then rung L2 over January alone with the base arm (`--months 1 --arms ""`, 31 rolling windows,
  `uc_solver_preset` lean), model `claude-opus-5-5`, budget 60 min, branch `claude/ucmilp-bench-miso-2020-L1`. **Pass iff
  window 0 is Optimal and all 31 January windows complete with 0 time-limit hits, `gap_max` within `uc_mip_rel_gap` and no
  exception.** Otherwise STOP and report; no span. Launched 2026-10-10 00:48Z as `session_0116uJFx8cCqjmBxMRcWAMF6`
  BEFORE this file was pushed (the gate precedes the PRECOMMIT by charter; it reads nothing this file fixes). Its numbers
  land in Addendum A together with the budget.
- **Seven shards, 2019–2025**, one year each, `claude/ucmilp-miso-<y>`, out-dir `results/calibration/ucmilp_miso_<y>`,
  prompts from `scripts/shard_prompt.py --iso MISO --all-years --sha 2f872a62a7cccadb6800555c11a73745dcdb89a4
  --lane ucmilp-miso --bundle results/calibration/closeout_miso_nuc_span --set unit_commitment_milp=true --budget <A>
  --note "ucmilp-miso: UC A/B"`, each appended with the lane addendum: confirm `hourly/uc_schedule_<y>.parquet`,
  `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json` and `hourly/unit_marginal_<y>.parquet` are in the pushed tree;
  report the GATESPEC §6.1 wall row (the `log_year_phase_timing` line + `uc_solve_log_<y>.json summary`); an OOM kill or a UC
  hard stop is a successful report. Committed as `docs/records/miso/ucmilp/shard-prompts-ucmilp-miso.txt`.
  `create_session` per year: `source_revision` = the pin, model `claude-opus-5-5`, tag `ucmilp:UC-2-MISO-shard`.
  PENDING > 45 min: archive and relaunch.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_miso_<y>` non-empty; check out; verify
  `dispatch/<y>_P1.parquet` + the three UC files + `unit_marginal_<y>`; verify the per-year recipe (§1); THEN
  `archive_session` (rule 33).
- **Compose and score, zero LP, at the pin:** `scripts/probes/_ucmilp_compose_span.py` at the pin still aborts on
  `gas_price_override` (the keeper records it per year) and lacks `_respan_shared_inputs` (SPP Addendum D items 1–2, routed
  to the engine lane, not landed). **Declared workaround, as SPP:** a scratch copy of the committed composer with
  `gas_price_override` added to `PER_YEAR_FIELDS` and the keeper composer's `_respan_shared_inputs`
  (`_closeoutsppnuc_compose_span.py`) applied to the span's `meta.json`; no repo script is edited; everything else is the
  committed script's logic. Then `calibration_verdict.py --json` on control and arm, `legitimacy_diagnostics.py`
  regenerated, the M1/M3/M4 re-measurement. The parent runs no LP.
- **No dashboard registration** (desk ruling on the SPP probe: audit E13 admits only keepers or folded runs). The slim span
  (hourly sidecars incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`, `uc_solve_log_<y>.json`, regenerated
  `legitimacy_diagnostics.json`, `metrics.json`, `run_config_<y>.json`, `meta.json`) goes under
  `docs/records/miso/ucmilp/data/ucmilp_miso_span/`; the full leg bundles stay on their shard branches (rule 31: nothing
  deleted). Never promote.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-miso-ab-<date>.md`: §6.3 gate table first, wall rows, every reading
  answered, kills checked, verdict, D-6 card, where each bundle is and what a promotion costs, `## Log entry`); the MISO
  matrix cell `unit_commitment_milp` stamped with verdict + citation as the last commit after rebasing; ONE PR, not merged
  by this lane (UC-DESK merges); `send_message` UC-DESK with the gate table first, then the wall rows.

## 9. G-DRIFT — main at the pin vs the keeper's basis `f98c4564` (zero LP, rule 29(b))

- `scripts/solve_surface_register.py --diff f98c4564 2f872a62`: *"339 → 342 names; 0 value(s) moved, 3 added
  (`NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR`, `NWPP_MEMBER_LOCAL_TZ`, `NWPP_SEAM_IN_SERVICE_UTC`; they move no key), 0 removed —
  NO VALUE MOVED"*. `src/market_sim`: 31 files, +5,573/−63 over the whole span.
- `f98c4564 → d62ae1a7` (main-without-UC): **INERT for MISO by measured input identity** — the golden-MISO FINDING §2
  compared the faithful per-year recipe's `run_energy_solve` inputs at the basis and at main at atol = rtol = 0, all seven
  years, identical; the only differences were five default-off fields absent at the basis.
- `d62ae1a7 → ae224faf`: the SPP Addendum C table re-read for MISO — the UC engine (LIVE on the gate-on path only, the arm);
  closeout-PJM-w3 `nuclear_winter_capability_basis` (PJM-gated, default off, absent from the MISO recipe); closeout-ERCOT-w3
  `coal_perplant_cliff_split` (ERCOT-gated); **closeout-MISO-w3 `miso_seam_neighbour_hourly_full_span`** (default `False`,
  read only by `model/interchange/miso.py` under the flag, ABSENT from the keeper's `run_config.json`, unarmed in
  `iso_configs`) → INERT; closeout-SOCO-w3 `diagnostic_coal_metered_online_floor` (identity wrap when off) → INERT.
- `ae224faf → 2f872a62` (this lane's own classification, on the objects):

  | content | files | MISO classification |
  |---|---|---|
  | UC-SPEED lean preset (#7218) | `model/uc/{solve,window,schedule}.py`, `pipeline/uc.py`, `scenarios.py` `uc_solver_preset: str = "lean"` (registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `'lean'`, born at the fast value and dropped from the hash there), `scripts/lib/uc_bench.py` | LIVE on the gate-on path only (the arm); paired-equivalent to the uc-1.1 path (UC-SPEED §3). Off-gate: byte-inert |
  | closeout-CAISO-w6 / ERCOT-w6 measured CHP BTM share | `scenarios.py` `caiso_chp_btm_measured` / `ercot_chp_btm_measured` (default `False`), `data/chp.py` (`measured_chp_btm_pct_for_iso` returns `{}` for every ISO but NYISO/CAISO/ERCOT), `data/fleet/assembly.py` (`chp_btm_measured_armed(config)` False for MISO), `run_calibration_full.py` `_btm_frame` args + CLI, `config/paths.py` EIA-923 disposition constants | **INERT**: ISO-gated in code, default off, ABSENT from the MISO recipe |
  | bench harness | `scripts/diagnostics/bench_uc_ladder.py` (+19/−2) | bench only |

  Nothing is LIVE for MISO outside the UC stage. The control is therefore the committed bundle unchanged (rule 29(b)); no
  control solve.

## 10. DO NOT REDO

Everything in `docs/mechanism-testing-matrix.md` §5.4's DO-NOT-REDO (`miso_coal_night_floor` I, `internal_congestion_split`
G/O, every R/I/G cell without new evidence); `miso_commitment_posture` (R) is not re-run in any form;
`miso_gas_ecomin_online_floor` (I) stays off; no `uc_*` value other than the declared defaults; no second `--set`; no
control solve; no offer-band retune; no NEISO/NYISO span.

## Addendum A (2026-10-10 01:55Z, before any span shard exists) — the L1 gate PASSED; the budget is 109 min

**Bench shard** `ucmilp-bench-miso-2020-L1` at the pin, model `claude-opus-5-5`: first launch (`session_0116uJFx8cCqjmBxMRcWAMF6`,
00:48Z) stopped at its own hard stop 3 — the container had no `.venv` (`uv sync` never ran; `pyarrow` missing); nothing solved,
nothing pushed, archived. Relaunch (`session_012an4XfAv35RRQKJw8KqVxM`, 00:55Z) with `uv sync` as step 0 and every step under
`uv run python3`; nothing else changed. Results on `claude/ucmilp-bench-miso-2020-L1` `2db7198152d2c0bc8e18b4a8471167bab9c8a036`
(`results/bench/uc/miso_2020_L1/l1.json`, `miso_2020_L2m1/l2.json`, console logs). Archived after fetch and read (rule 33).
**Lesson carried into every span-shard prompt:** step 0 `uv sync` if `.venv` is absent; every python step as `uv run python3`.

| gate element | reading | pass? |
|---|---|---|
| window 0 (L1, h0–36) | **Optimal**, 20.02 s MILP (build 0.13 s), 33 nodes, gap 9.1e-4, 5,904 integers / 149,220 columns / 31,594 rows, warm start accepted, 58 guard rows; relaxation 3.02 s; integrality gap $55,865 (0.87 % of the window objective); Δ committed energy −23.6 GWh vs the P1 slice; starts 42 vs 205 in the P1 slice | yes |
| January rolled month (L2 base arm, `lean`) | **31 / 31 windows**, wall 307.0 s, MILP Σ 300.3 s (p50 8.96, p95 15.17, max 19.82 s), nodes p50 / p95 **1 / 13.5** (MISO branches; SPP solved every window at the root), zero-node share 0, **0 time-limit hits**, gap_max 9.98e-4 ≤ 1e-3, no exception; phase sums setup 120.0 / presolve 118.0 / root LP 38.9 / tail 138.7 s | yes |
| census | 336 clusters, **164 integer**, 1,231 fleet rows, W = 24, L = 12 (UC-0's M6 said 159 plant clusters; the engine's integer set is 164) | reported |
| capture (one P0 + P1 of MISO 2020 at the keeper recipe) | `log_year_phase_timing`: data_prep 47.9 / **solve_p0 501.3** / markup 66.0 / **solve_p1 138.2** / results_write 77.9 / total 831.3 s; `capture_wall_s` 722.8 | reported |
| memory | preflight `before: ceiling 13.36 GiB, swap 0.0, 16.3 GiB free disk, 4 cpus`; `swap: added 10 GiB → 23.4 GiB total` (0.6 GiB under the 24 GiB target, warning only); `cgroup_peak_rss_gib=13.36, cgroup_peak_rss_plus_swap_gib=16.44, process_vmhwm_gib=13.32` — RAM at the cap, ~3 GiB spilled to swap, not killed; UC stage RSS 2.62 GB | reported (W5 live risk: every leg will touch the cap) |

**Budget (the §5 rule, numbers in):** extrapolation = P0 + P1 (501.3 + 138.2 = 639.5 s) + 365/31 × 307.0 s (3,614.3 s UC) +
a P1 re-solve (138.2 s) + 600 s overhead = 4,992 s = **83.2 min**; × 1.3 = 108.2 → **budget 109 min per shard**. Expected stage
ratio at the shard, total/(P0+P1) ≈ (501 + 3,614 + 138 + 66 + 78) / 640 ≈ **6.9×** (reported, not judged; D-2 ceiling 3×).
The MILP per window is ~3× SPP's (9.7 vs 3.0 s mean) on ~1.8× the integers (5,904 vs 3,312) and with branching (p95 13.5 nodes).

Prompts generated with `--budget 109` and committed as `docs/records/miso/ucmilp/shard-prompts-ucmilp-miso.txt`; readings, bars,
kills and the verdict rule of §§2–7 are unchanged.

## Addendum B (2026-10-10 01:56Z) — launch record

Seven span shards launched 01:53–01:56Z at the pin `2f872a62`, model `claude-opus-5-5`, tag `ucmilp:UC-2-MISO-shard`, prompts =
`shard-prompts-ucmilp-miso.txt` (commit `ace67246`; the "PER YEAR" wording is the text as launched): 2019 `session_011btcKiUP9SV8CwD1frxESQ` ·
2020 `session_01MaGZYCkVzevC6MrhZowr2M` · 2021 `session_01TMV8TKm9EC9nUVX5RsiB5j` · 2022 `session_01PyziKkUq9u83cKMQz1SzoD` ·
2023 `session_015qt5jGxEdY529gMRR8e1YG` · 2024 `session_01RkDeuTxQWJ4ccMUNPcHwn9` · 2025 `session_01TNU8C6Be2nVyEvcZEpgu2e`.
Bench shards archived: `session_0116uJFx8cCqjmBxMRcWAMF6` (no .venv, nothing pushed), `session_012an4XfAv35RRQKJw8KqVxM` (results on
`claude/ucmilp-bench-miso-2020-L1` `2db7198`). Nothing in §§1–7 changed.

## Addendum C (2026-10-10 02:00Z) — UC-DESK's engine-defect-3 heads-up, checked zero-LP: MISO is NOT hit; the pin stands

UC-DESK (01:53Z): the UC window does not slice a time-major `(T, n_links)` `ttc` / `ttc_import` (ERCOT's first window build
fails with a `(8760, n) → (36, n)` broadcast). Checked for MISO without an LP: (a) `pipeline/ttc.py` returns a 2-D `ttc` only
for NYISO (`apply_iso_monthly_ttc`: `if iso != "NYISO": return ttc`); `ttc_import` is set only on ERCOT's measured-GTC path
(`pipeline/spec.py` UNSET elsewhere); no MISO path assigns a 2-D `ttc` (`run_calibration_full.py`, `interchange/core.py`,
`interchange/miso.py`, `pipeline/kwargs.py`). (b) MISO's hourly seam limits ride inside `interface_groups` as per-link `(T,)`
arrays, whose last axis is `T`, so `model/uc/window.py::_slice_obj` slices them. (c) Live evidence at the pin: the L1 gate
built and solved window 0 and all 31 January windows on MISO 2020 (Addendum A) — the first window build is where ERCOT fails
— and every MISO year shares the same interchange construction (the per-year overlay changes only the reserve flags and the
gas price). No re-pin; nothing in §§1–7 changed. If a span shard nonetheless fails at its first window build, that is kill #1's
engine-defect route: record, stop, route to UC-DESK.

## Addendum D (2026-10-10 02:45Z) — KILL #1 fired on MISO 2020 at the pin: window 129 Infeasible; recorded, routed, no re-tune

Shard `ucmilp-miso-2020` (`session_01MaGZYCkVzevC6MrhZowr2M`) stopped at 02:39:57Z, 36 min in (P0 473 s; UC prepared 336 clusters,
164 integer, 1,231 fleet rows, W = 24, L = 12; windows 0–128 solved), on the engine's hard stop, verbatim:

```
market_sim.model.uc.window.UcWindowInfeasible: UC window 129 [3096, 3132) solve ended Infeasible with no feasible incumbent
(149220 columns, 31580 rows, 164 integer clusters); LP relaxation: Infeasible; a-priori contradictory rows: min_down=1;
carried starts above n: 0; floor above min-down: 1
```

raised at `pipeline/uc.py:396 run → model/uc/solve.py:460 solve_window` inside `p1_fleet_prep`. Not defect 3 (Addendum C): the
window built and 129 windows solved before it. The engine's own diagnosis names one contradictory min-down row and one
"floor above min-down" conflict with no carried-starts overflow: a kept floor (D-5 keeps `st_gas_mustrun_per_plant`, the coal
yard floors and `reliability_floor` / the CT drag) asserts a cluster online inside its carried min-down — the UC-0 §4 hard case,
here as a hard infeasibility rather than a C8 share. **Kill #1 (PRECOMMIT §6): recorded; the shard pushed nothing and was archived
(rule 33, nothing to fetch); no `uc_*` value moves; routed to UC-DESK 02:44Z.** The six other shards (2019, 2021–2025) stay
running as evidence of whether the conflict is year-specific; each outcome is recorded here. Relaunch rule (the SPP Addendum A
form): when the engine carries a fix, the pin moves to that full SHA and NOTHING else changes (same recipe, same single `--set`,
same `uc_*` defaults, readings, bars, kills, budget); if the resolution is instead a D-5 re-ruling (a floor switched off for MISO),
that is an ARM change and needs the owner's card before any relaunch — the readings would then be re-pre-registered against it.

**Addendum D, continued (02:50Z) — the infeasibility is systematic across MISO years at the pin.** Four of seven shards stopped on
the same signature (every one raised at `pipeline/uc.py:396 → model/uc/solve.py:460` inside `p1_fleet_prep`; no OOM; nothing pushed;
all four archived after their reports were read, rule 33):

| year | window | exception tail (verbatim) | census | P0 s |
|---|---|---|---|---|
| 2020 | 129 [3096, 3132) | `LP relaxation: Infeasible; a-priori contradictory rows: min_down=1; carried starts above n: 0; floor above min-down: 1` | 336 / 164 int / 1,231 rows | 473 |
| 2021 | 30 [720, 756) | `… min_down=2; carried starts above n: 0; floor above min-down: 2` | 330 / 161 / 1,211 | 702 |
| 2023 | 227 [5448, 5484) | `… ceiling=2, min_down=2; carried starts above n: 0; floor above min-down: 2` | 322 / 147 / 1,127 | 385 |
| 2025 | 135 [3240, 3276) | `… ceiling=2, min_down=2; carried starts above n: 0; floor above min-down: 2` | 316 / 139 / 1,097 | 515 |

2019, 2022 and 2024 were still in their UC stage at 02:45Z; their outcomes are recorded below when they report. The engine's
per-cluster diagnosis (`model/uc/diagnose.py` `clusters_floor_above_min_down`: plant code, `n`, `dt_h`, `u_lower`) is built on the
exception but never printed, so no log names the colliding plants; a zero-LP identification needs the P0 capture and is the engine
lane's. Reading: `u_lower > n − hist_w` — a floor-derived online need exceeds the units the carried min-down leaves; in 2023/2025 the
ceiling rows collide too. The MISO arm keeps every conduct floor (D-5), so the UC's min-down physics and a kept floor contradict at a
window boundary; SPP's kept floors never produced this. Routed to UC-DESK 02:49Z with the two resolutions named (engine fix → re-pin
under this addendum's rule; D-5 re-ruling → owner card, re-pre-registration). The L1 gate passed because no January 2020 window
carried the collision; the earliest MISO collision is window 30 of 2021.

## Addendum E (2026-10-10 02:52Z) — the desk's ruling on kill #1: route (a), engine fix; the arm stays as declared; relaunch held

UC-DESK (02:51Z), verbatim: *"route (a), engine. Chartered UC-1-FIX-2 (session_01VQbdDQky4y91ytyky1UEge, Opus) for defect 5 (floor
need vs carried min-down / ceiling). No D-5 re-ruling — the arm stays as declared. Let the 3 remaining shards finish and report
(evidence), push nothing new; hold the relaunch until I send the fix's merge SHA (Addendum D rule: pin moves, nothing else)."*
So: no `--set` changes, no floor switched off, no new shard; 2019 / 2022 / 2024 run to their own stop and are recorded; the
relaunch happens at the merge SHA UC-DESK names, under Addendum D's rule (pin moves, nothing else), after the Addendum-C-style
zero-LP read of what moved between the pins.

**Addendum D, closed (03:20Z) — 7 of 7 MISO years stop on the same signature at the pin.** The three remaining shards reported;
all seven are archived (rule 33; nothing pushed by any shard, nothing to fetch):

| year | window (hours; calendar) | exception tail (verbatim) | census (clusters / integer / rows) | P0 s |
|---|---|---|---|---|
| 2019 | 186 [4464, 4500); 5–6 Jul | `… ceiling=3, min_down=3; carried starts above n: 0; floor above min-down: 3` | 338 / 167 / 1,251 | 488 |
| 2020 | 129 [3096, 3132); 10–11 May | `… min_down=1; carried starts above n: 0; floor above min-down: 1` | 336 / 164 / 1,231 | 473 |
| 2021 | 30 [720, 756); 31 Jan–1 Feb | `… min_down=2; carried starts above n: 0; floor above min-down: 2` | 330 / 161 / 1,211 | 702 |
| 2022 | 190 [4560, 4596); 9–10 Jul | `… ceiling=2, min_down=2; carried starts above n: 0; floor above min-down: 2` | 328 / 157 / 1,185 | 1,706 |
| 2023 | 227 [5448, 5484); 16–17 Aug | `… ceiling=2, min_down=2; carried starts above n: 0; floor above min-down: 2` | 322 / 147 / 1,127 | 385 |
| 2024 | 312 [7488, 7524); 8–9 Nov | `… ceiling=1, min_down=1; carried starts above n: 0; floor above min-down: 1` | 320 / 144 / 1,134 | 363 |
| 2025 | 135 [3240, 3276); 16–17 May | `… ceiling=2, min_down=2; carried starts above n: 0; floor above min-down: 2` | 316 / 139 / 1,097 | 515 |

Every exception reads `LP relaxation: Infeasible` and `carried starts above n: 0`; the count of "floor above min-down" clusters equals
the count of contradictory min-down rows in every year (1–3), and where ceiling rows also contradict their count matches too. The
collision is year-round (January to November), so it is not a seasonal floor window. Shards wrote nothing to the log between
`UC stage prepared` and the traceback (the engine has no per-window progress line), so the time-to-failure is only bounded: 36 min
(2020, window 129) to 62 min (2022, window 190, with a 1,706-s P0). Memory: every container at 18.4 GiB ceiling+swap, UC-stage RSS
~10 GB, no OOM kill. Shard sessions, all archived: 2019 `session_011btcKiUP9SV8CwD1frxESQ`, 2020 `session_01MaGZYCkVzevC6MrhZowr2M`,
2021 `session_01TMV8TKm9EC9nUVX5RsiB5j`, 2022 `session_01PyziKkUq9u83cKMQz1SzoD`, 2023 `session_015qt5jGxEdY529gMRR8e1YG`,
2024 `session_01RkDeuTxQWJ4ccMUNPcHwn9`, 2025 `session_01TNU8C6Be2nVyEvcZEpgu2e`. Cost of the attempt: 7 containers, 29–62 min each,
plus the two bench containers. No span exists; nothing is scored; the matrix cell stays `U` until the relaunch (Addendum E).

## Addendum F (2026-10-10, before any relaunch shard exists) — the relaunch: pin moves to `eab17188`, nothing else changes

Lane taken over as **UC-2-MISO-R2** (Opus, this session) from the Fable session `session_016bPoPZ6beefv8kJUn8sQFH`, which hit the
weekly Fable limit before relaunching. UC-DESK named the fix's merge SHA. Addendum D's relaunch rule applies verbatim: **the pin moves
and nothing else does** — same recipe, same single `--set unit_commitment_milp=true`, empty offs set, every `uc_*` field at its
declared default, readings, bars, kills, verdict rule and the §5 budget rule of §§1–8 unchanged. `origin/main` was merged into this
branch (merge, not rebase).

**New pin (every shard): `eab17188c75cd0332f9323ed3464c62bc0cd1848`** = `origin/main` at the merge of PR #7230 (UC-1-FIX-2). What it
carries for this lane: engine **uc-1.2** (defect-5 guard on the pinned window fleet, `model/uc/window.py`); **ruling (a)**, a cluster
whose members are ALL budget-pinned carries no integer (`params.demote_budget_pinned`; MISO's yard coal is pinned by
`coal_fuel_inventory_plant_grain=true`, so on the 2021 gate the integer set went **161 → 75**, 86 demoted — the UC acts on gas and
unpinned coal only, and that count is stated per year in the RESULT headline from `engine.integer_gate_size` /
`integer_set_size`); the slim-expand inf-cap NaN fix; a per-window INFO log line; **FIX-3** (#7229) uc-params keyed by EIA plant
code through `campd_crosswalk.camd_to_eia_plant`; **UC-SLIM** (#7222, `uc_slim_window`, born `True`). Gate evidence (FIX-2 FINDING
§5.0): MISO 2021 at uc-1.2 `e4a57362`, **365/365 windows Optimal** (w30 and w129 Optimal), 0 time-limit hits, MILP mean / p95 / max
6.2 / 11.4 / 37.4 s, UC 2,568 s, P1 solved, **0 unserved**. The FIX-2 FINDING §5.1 seam defect (MISO P1 infeasible after a complete
UC stage under the uc-1.1 guard) is the one ruling (a) removes; if a leg's P1 is nonetheless infeasible, that is kill #1's engine route.

**G-DRIFT `2f872a62 → eab17188` (zero LP, rule 29(b)).** `scripts/solve_surface_register.py --diff 2f872a62 eab17188`: *"342 → 342
names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*. Every changed hunk on the backcast path, classified:

| content | files | MISO classification |
|---|---|---|
| UC engine uc-1.2: defect-5 guard on the pinned window fleet, ruling (a) demotion, per-window log, diagnosis printing | `model/uc/{window,params,solve,diagnose}.py`, `pipeline/uc.py` (`UC_ENGINE_VERSION = "uc-1.2"`) | **LIVE on the arm only.** Reached solely through `pipeline/solve.py:675` (`if getattr(config, "unit_commitment_milp", False)`) and `runner.py:4175` (same gate); neither hunk changed. Control: INERT |
| UC-SLIM exact window reduction + inf-cap NaN fix | `model/uc/slim.py` (new), `window.py`, `solve.py`; `scenarios.py` `uc_slim_window: bool = True`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `True` (born and dropped from the hash there), TIER_TAGS 1 | **LIVE on the arm only**, exact (same feasible set and optimum; paired equivalence PASS, SLIM FINDING). Added to the arm table of §1 as a declared default, never swept. Control: INERT (the field is read only inside the UC stage) |
| FIX-3 uc-params CAMD → EIA crosswalk | `data/campd_crosswalk.py` (`load_crosswalk` refactor of `crosswalk_of_record`, same output; new `camd_to_eia_plant`), `scripts/lib/uc_params/__init__.py`, `uc_params/ercot.py`, `scripts/lib/clean_profiles.py` (uc-params raw inputs + crosswalk, PUDL), `uc-params.schema.yaml` | **The uc-params VALUES move for the re-keyed MISO clusters** (FIX-3 commit `121cee93`, zero LP: MISO measured clusters 190 → 193, integer 103 → 104 on the uc_solve_log census) — the arm's cluster physics for those plants switch from class fallback to their measured rows; rule 23: a join-bug fix, not a re-fit. uc-params is read only by `model/uc/params.py` under the gate; `camd_to_eia_plant` has no caller outside the uc-params derive; `crosswalk_of_record`'s only in-`src` caller is the `classify_remap_rows` audit (changes no solve). Control: INERT. The miso hydrate profile carries `data/raw/reference/camd-eia-crosswalk` (4 files) and `data/raw/pudl` (3), checked by `hydrate_data.resolve_files` |
| UC-2-SPP-B coal sync floor release | `scenarios.py` `coal_sync_floor_release: bool = False` (registered at `False`), `data/fleet/arrays.py::_compose_min_gen_floors` (`coal_sync_any … and not _coal_sync_release`) | **INERT**: default off, ABSENT from the MISO recipe, armed by no `iso_configs`; off, the historical branch is taken verbatim. Not armed on this lane's arm either (no second `--set`) |
| bench harness | `scripts/lib/uc_bench.py`, `scripts/diagnostics/bench_uc_ladder.py` | bench only |
| tests, docs, matrix rows, other lanes' records and slim spans | `tests/**`, `docs/**`, `CHANGELOG.md`, `data/dictionary/data-dictionary.md` | no solve path |

**Solve surface on the control reads 0**; the two new fields sit at their registered defaults, so no committed cache key moves.
Nothing is LIVE for MISO outside the UC stage: the control is the committed keeper bundle unchanged (rule 29(b)); no control solve.

**Two mechanical consequences, declared now (not a reading change):**
1. **Recipe verification gate (§1).** The allowed differing fields between a leg's `scenario_config` and the keeper's are now
   `unit_commitment_milp`, every `uc_*` field at its declared default (including `uc_slim_window = True`), and
   `coal_sync_floor_release = False` (a new default-off field the keeper predates). Any other differing field is a recipe break and
   the leg is not composed.
2. **Budget (§5 rule, new numbers in).** Measured at the gate and Addendum A/D: P0 ~600 s (Addendum D range 363–1,706 s), P1 ~800 s
   (the UC-armed P1 is heavier than the 138 s gate-off capture), UC ~2,500 s (2,568 s at the 2021 gate). Extrapolation = P0 + P1
   (1,400 s) + UC (2,500 s) + a P1 re-solve (800 s) + 600 s overhead = 5,300 s = 88.3 min; × 1.3 = 114.8 → **budget 115 min per
   shard**. Memory: every leg touches the 13.36 GiB cgroup cap in P0 (~13 GiB RSS) and spills to swap; an OOM kill is W5's stop.
   Shards run the replay detached (`nohup setsid … &`, polled from the log) so no tool-call ceiling ends it before the budget.

Prompts regenerated at the new pin (`scripts/shard_prompt.py … --sha eab17188c75cd0332f9323ed3464c62bc0cd1848 --budget 115`; the base
text is byte-identical to Addendum A's apart from the SHA and the budget) and committed over
`docs/records/miso/ucmilp/shard-prompts-ucmilp-miso.txt` (the launched pin-1 text stays in git history at `ace67246`).

## Addendum G (2026-10-10 14:18Z) — relaunch record

Seven span shards launched 14:18:04–14:18:10Z at the pin `eab17188c75cd0332f9323ed3464c62bc0cd1848`, model `claude-opus-5-5`, tag
`ucmilp:UC-2-MISO-shard`, prompts = `shard-prompts-ucmilp-miso.txt` at `b30a7fc3` (Addendum F text): 2019 `session_01NrZdEVbUPDbuh28pKQ7V7F` ·
2020 `session_01XEjFwLBv4SGDAHw3a6JQW4` · 2021 `session_01NiDuJaNBaLqyRLhdskUEZ7` · 2022 `session_01JwPkP9JprGyHhyhUBouxvK` ·
2023 `session_01WNeaDPLLqcuKm3C1xa3aif` · 2024 `session_01GyYoFNeXCFi5CabPjAS87u` · 2025 `session_01CW8CEfZ5YikyVowxaLCLME`.
Nothing in §§1–8 changed.

## Addendum H (2026-10-10 16:00Z) — four legs in; the recipe gate's field set, stated; KILL #3 fires on 2024 (unserved +2,760 MWh)

**Legs fetched, verified, archived (rule 33).** Each parented on the pin, 21 files, `dispatch/<y>_P1.parquet` + `uc_schedule` / `uc_uplift`
/ `unit_marginal` / `uc_solve_log` present; every window Optimal (365/365), 0 time-limit hits, exit 0, no OOM (every leg at the 13.36 GiB cap,
3.3–4.3 GiB in swap):

| year | branch @ SHA | shard | integer gate → set (demoted all-pinned) | P1 unserved MWh (keeper) |
|---|---|---|---|---|
| 2020 | `claude/ucmilp-miso-2020` @ `985780105b7293d8536fb8447935169f42f50752` | `session_01XEjFwLBv4SGDAHw3a6JQW4` | 164 → 76 (88) | 0 (0) |
| 2021 | `claude/ucmilp-miso-2021` @ `7b3575a34ca5a4c1ddb4878e077d3d2ba43bf4ba` | `session_01NiDuJaNBaLqyRLhdskUEZ7` | 161 → 75 (86) | 0 (0) |
| 2024 | `claude/ucmilp-miso-2024` @ `4bbbe13b32c98128b7a493a4728ca3266a928788` | `session_01GyYoFNeXCFi5CabPjAS87u` | 144 → 77 (67) | **11,116.8 (8,356.9)** |
| 2025 | `claude/ucmilp-miso-2025` @ `3521f9f141aa910d170d1b5c38ac0f68722c63f6` | `session_01CW8CEfZ5YikyVowxaLCLME` | 139 → 74 (65) | 0 (0) |

**Recipe gate (§1 / Addendum F), stated precisely.** Every field the keeper's `run_config_<y>.json` records is equal in each leg
(`gas_price_override`, `gas_offer_margin_anchor`, `weather_year`, and for 2023–25 the two reserve flags included). The legs additionally
record 13 fields the keeper predates, each `False`, each at its registered default in `_CACHE_KEY_OPTIONAL_FIELDS`, armed by no
`iso_configs` entry and born before the first pin `2f872a62` (so inside the §9 G-DRIFT span that classified the control INERT):
`caiso_chp_btm_measured`, `caiso_dsw_daytime_lateevening_unprinted_arm`, `coal_perplant_cliff_split`, `diagnostic_coal_metered_online_floor`,
`ercot_chp_btm_measured`, `miso_seam_neighbour_hourly_full_span`, `nuclear_winter_capability_basis`, `nwpp_coi_pnw_delivery_basis`,
`nwpp_path76_served_schedule`, `nwpp_seam_in_service_vintage`, `nwpp_served_schedule_zonal_attribution`, `pjm_elliott_measured_outage_overlay`,
`zonal_loss_demand_reconciliation`. The §1 sentence ("except `unit_commitment_milp` and the ten `uc_*` fields") omitted this class; it is a
default-off field absent from the keeper's record, not a recipe difference, and the gate is read as passing. Disclosed, not a reading change.
(The legs write `run_config.json` only, no `run_config_<y>.json`; the composer copies it per year.)

**KILL #3 (§3 "also gating": unserved up by ≤ 500 MWh vs the keeper) fires on MISO 2024: +2,759.9 MWh.** Both runs shed load in the same
event, hours 5701–5706 (26 Aug 2024, the heat peak): keeper 5 zone-hours (West, Indiana, East), 8,356.9 MWh; arm 6 zone-hours (West ×3,
Plains, Illinois, Indiana), 11,116.8 MWh, plus 416.4 MWh of dump the keeper does not have. Recorded per §6; no re-tune, no relaunch, no
`uc_*` change. The verdict rule (§7) makes the lane **R** whatever the remaining readings show. The three shards still solving (2019, 2022,
2023) were already launched and are left to finish as evidence (Addendum D precedent); no new LP is started. The span is still composed
and scored zero-LP so the RESULT carries the full gate table.
