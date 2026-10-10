# PRECOMMIT — UC-2-ERCOT: pre-registered A/B of the MILP unit-commitment stage on every ERCOT backcast year, 2026-10-10

**Written and pushed BEFORE any span shard exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing moves after a number comes in (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-2-ERCOT` (session
`session_012x78eXKGe21mGbQeVK54Z6`, Fable), branch `claude/ucmilp-2-ercot-ab-e4w1` off `origin/main`
`2f872a62a7cccadb6800555c11a73745dcdb89a4` (the pin). Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on
2026-10-10 under the owner's direction *"launch shards for other ISOs to test"*. Protocol:
`docs/records/governance/uc-milp-2026-10/GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7; plan
`docs/uc-milp-program-plan-2026-10.md` §3 (UC-2), §8.1 (R3–R6, D-2 "Keep 3×; fund speedup", D-6 SPP "Record R + test
floors-off arm"). Structure copied from the SPP precedent `docs/records/spp/ucmilp/PRECOMMIT-ucmilp-spp-ab-2026-10-04.md`
(+ Addenda A–D) and its RESULT (PR #7207), whose three lessons this lane applies: **bench L1 first** (§0.1), **the composer
gaps are worked around in a scratch copy and disclosed** (§8), **no dashboard registration** (§8; audit E13 is keeper-only).

**Off-plan statement (RUNBOOK §1).** The close-out plan §3.5 ranks ERCOT's next levers 0a–6 (coal pile, West import rating,
the SCED account). This lane is the UC program's wave 3 (plan §9) under the owner's direction above, not a §3.5 step; nothing
in §3.5 is skipped or re-ordered by it.

## 0. Preconditions (checked before this file was written; zero LP in this session)

| check | result |
|---|---|
| engine on `main` at the pin: `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` at `2f872a62` | **6** (engine PR #7194 + UC-1-FIX #7201 + UC-SPEED #7218 merged; `uc_solver_preset` default `"lean"`) |
| the ERCOT keeper's `run_config_<y>.json` arms members of `UC_REFUSED_ALWAYS` (15 fields) | **exactly one**: `ercot_gas_commitment_bridge = true` in every year; `ercot_commitment_posture = false`; every other refused field `false`/`null` |
| the arm validates at the pin (zero LP: `ScenarioConfig(**run_config_2020.scenario_config).with_overrides(...)`) | `with_overrides(unit_commitment_milp=True)` alone → `ValueError` naming `ercot_gas_commitment_bridge` (rule 19 by refusal); with `ercot_gas_commitment_bridge=False` added → **accepted**; `uc_*` resolve to the declared defaults (§1) |
| the bridge's sub-fields the keeper records (`ercot_gas_bridge_startup`, `_da_horizon`, `_min_load_frac 0.574`) stay recorded | consumed only inside `pipeline/commitment.py` behind `ercot_gas_commitment_bridge and iso == "ERCOT"` (lines 503, 583) → inert when the parent is off |
| the keeper bundle at the pin is the registered keeper | `frontend/data/backcast/registry/2026-10-02-closeout-l1-coal-fuel.json` → bundle `results/calibration/closeout_ercot_l1_span`, years 2019–2025; the bundle's `run_config_<y>.json`/`meta.json`/`metrics.json` are the promotion's own files, added after the solve basis (§6) and unchanged since |
| the control re-scored at the pin reproduces its registered record | `calibration_verdict.py results/calibration/closeout_ercot_l1_span` at `2f872a62` (rubric 3.20): every magnitude in §3 equals the keeper shard's frontier rows (`keepers/ERCOT.json`: C1 CC +9.21/+10.17, PRB −10.79/−11.85, C3b 0.216/0.208, 2024 C3a −11.3 %); `check_bench_freshness.py --iso ERCOT`: 7 parts, **0 STALE**, all reproduce at HEAD |
| ERCOT golden (gate off) at the engine SHA `ec758d64` | **PASS** (plan §11, UC-DESK r03) — the engine's off path reproduces this keeper |

### 0.1 The L1 gate (new, from SPP's two engine defects) — one bench shard, rung L1 + one rolled month, BEFORE any span shard

Shard `ucmilp-bench-ercot-2020-L1gate` (`session_01147Y52oCQXRi7tn7sjJCzg`, Opus, launched 00:46Z at the pin; prompt
committed as `shard-prompt-ucmilp-ercot-bench-L1.txt`): `bench_uc_ladder.py --iso ERCOT --year 2020 --rung L1` then `--rung L2
--months 1 --rolling --arms ""` (base arm only, rolling January), both with `--set ercot_gas_commitment_bridge=false` (the
validator refuses the gate beside the keeper's bridge). **Pass line: window 0 `Optimal` AND 31/31 January windows `Optimal`.**
Fail ⇒ STOP, report to UC-DESK, no span shard.

**Run 1 (00:46–01:07Z): STOPPED with a clear report, no window solved.** Two bench-harness defects, both confirmed at the pin
by this lane's zero-LP read: (1) `bench_uc_ladder.py` built the capture without the `--set` overrides (`capture_year` accepts
`overrides=`; the call site did not pass them), so the keeper replay ran bridge-armed (the log: *"ERCOT gas commitment bridge:
4618 unit-hours floored (0.63 TWh)"* — the control's own 2020 figure, §1); (2) `YearCapture.save` pickled the P1 hook closures
(`AttributeError: Can't pickle local object 'build_ercot_gas_bridge_p1_preps.<locals>._fleet_prep'`). The capture itself
completed (P0 218.8 s, P1 454.7 s, memory peak 12.07 GiB). **Fix (this lane, Fable, rule 27; commit `ad5a74d9` on the lane
branch):** the call site passes `overrides=`, routed through both channels as `replay_keeper`'s `--set` loop does (the bridge
flag is also a `solve_and_persist` kwarg the keeper's meta carries, so a prb-only override would be re-stomped — the ERCOT-65
class); `save()` drops `hooks`, which no rung reads. The bench harness is not on the solve path (`scripts/lib/uc_bench.py`,
`scripts/diagnostics/bench_uc_ladder.py`): **the span pin stays `main` `2f872a62`**; only the bench shard runs at the lane SHA.
Routed to UC-DESK for the engine lane to port. Run 2 is relaunched at `ad5a74d9` with the same pass line.

**Run 3 (`97e33b54`, 01:51–02:28Z): PASS.** Bridge OFF (no "gas commitment bridge … floored" line; in its place *"UC stage
prepared: 141 clusters, 72 integer (937 fleet rows), W=24 L=12"*). Capture P0 529.2 s, P1 263.5 s (phase total 981 s; peak RSS
11.59 GiB). **L1 window 0 (h0–36): Optimal**, MILP 4.90 s, 1 node, gap 6.7e-6, 2,592 integers / 89,928 columns / 14,313 rows,
integrality gap $82,185 (MILP −3,860,551 vs relaxation −3,942,736), Δ committed energy −3,746 MWh vs the P1 slice, starts 12 vs
144, warm start accepted. **Rolled January, base arm: 31/31 windows solved** (every window a finite objective, max gap 9.8e-4,
0 time-limit hits, 0 infeasible; the L2 record carries no per-window `status` field, so "Optimal" is inferred from gap ≤ 1e-3
and no limit hit — a harness gap to report), MILP s p50/p95/max 15.6 / 49.9 / 75.6, nodes p50/p95 16 / 78 (no rolled window
solved at the root), Σ MILP 670.8 s (wall 678.2 s), **warm start accepted 0/31** (E3 did not fire on the rolled path — a cost
finding for UC-DESK, not a kill). Records: `data/bench/ercot_2020_l1.json`, `ercot_2020_l2_jan_rolled.json`,
`ercot_2020_l2_jan_profile.md` (leg `0008523d` on `claude/ucmilp-bench-ercot-2020-L1gate`). Gate condition (a) **met**.

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** ERCOT's designated keeper `2026-10-02-closeout-l1-coal-fuel`, bundle
  `results/calibration/closeout_ercot_l1_span`, seven year-isolated legs 2019–2025 solved at
  `106d6bb737488f4086151907b4dbc4a45ee17306` (2026-10-02T14:27Z; `run_config.json git.basis_sha`). Its committed
  `metrics.json`, `legitimacy_diagnostics.json`, `hourly/*` and the status part are the control readings. The keeper is
  ERCOT's **owner config partition** (2024–2025 forward offer bands; vintage-gated market-design fields per year — §8 lists
  the 13 per-year fields); `replay_keeper.py --years <y>` applies each year's recorded overlay
  (`config_partition_overlay`) before the `--set` loop, so every leg replays its own year's recipe plus the arm.
- **Pin (every shard):** `origin/main` `2f872a62a7cccadb6800555c11a73745dcdb89a4` (merge of PR #7218: engine uc-1.1 +
  UC-1-FIX + the UC-SPEED lean preset). `source_revision` is this full SHA, never a branch. The pin does not chase `main`.
- **Arm — ONE logical delta (D-5 ERCOT, desk-set under the owner's direction, owner may override):**
  `replay_keeper.py results/calibration/closeout_ercot_l1_span --years <y> --set unit_commitment_milp=true
  --set ercot_gas_commitment_bridge=false`. The second `--set` is not a second lever: it is the rule-19 substitution the
  validator demands (`UC_REFUSED_ALWAYS`), the only refused field the keeper arms. Every `uc_*` field stays at its declared
  default and is **never swept**:

  | field | value | source |
  |---|---|---|
  | `unit_commitment_milp` | `true` | the arm |
  | `ercot_gas_commitment_bridge` | `false` | rule-19 substitution (DESIGN §5; `UC_REFUSED_ALWAYS`) |
  | `uc_window_hours` / `uc_lookahead_hours` | 24 / 12 | DESIGN §3 (plan E2) |
  | `uc_mip_rel_gap` | 1e-3 | DESIGN §3 (plan E4) |
  | `uc_window_time_limit_s` | 600 | DESIGN §3 declared placeholder; SPP A/B 0 hits of 2,555 windows |
  | `uc_integer_scope` / `uc_noload_source` / `uc_boundary_mode` | `physics` / `campd_regression` / `p0_targets` | DESIGN §1.1, §1.2, §2.2 |
  | `uc_prefixing` | `false` | DESIGN §2.3 (E5 unproven on a full year) |
  | `uc_solver_preset` | `"lean"` | registry default since UC-SPEED (`FINDING-ucmilp-speed-window-solve-profile-2026-10-09.md` §3: paired equivalence PASS, 62/62 windows) |

- **Kept floors (every other floor STAYS, mirroring SPP arm 1 so results compare across ISOs):**

  | kept field | mechanism (D-2 id) | control forced share of class energy, 2019 → 2025 | stacking risk named now |
  |---|---|---|---|
  | `ercot_coal_min_config_floor = true` | `coal_min_config` (UC-0 §4 **hard case**: a measured minimum-configuration floor — one unit of a multi-unit station online) | COAL_LIGNITE 8.3 / 8.9 / 4.8 / 3.0 / 6.4 / 7.3 / 8.4 %; COAL_PRB 9.8 / 14.9 / 3.3 / 5.6 / 8.2 / 8.4 / 2.5 % | the UC's integer unit count per coal plant expresses the same floor; both may bind on the same plant-hours. Reported under their own ids; no stacking budget is applied (R4) |
  | `gas_st_netload_drag = true` (+ `netload_drag_layup_window_mask`, `netload_drag_prior_year_commitment_index`) | `st_netload_drag` (UC-0 §4 **hard case**: a conduct-shaped part-load drag with a declared window) | ST_GAS 17.6 / 23.6 / 21.9 / **28.7** / 18.7 / 15.6 / 21.1 % | **the SPP pattern**: the kept `st_gas_mustrun_per_plant` floor's own forced energy rose 1–1.2 TWh/yr under the UC and pushed C8 ST_GAS over 30 % in four years. ERCOT 2022 sits 1.3 pts under the cap: a C8 ST_GAS flip is the named risk (§3) |
  | `coal_mustrun_per_plant = true` | the coal `_mustrun` band (measured per-plant) | inside the coal rows above | same object class as SPP's kept `coal_mustrun`; coal may rise further (SPP: +3.5 to +7 TWh/yr COAL_PRB) — here that is the direction C1 2019/2020 needs (§2 T4) |
  | `reliability_floor = true` | `reliability_floor` (RUC analogue; UC-0 §4 "stays") | CC_REGULAR 0.1–0.2 %; CT_PEAKER 3.3 / 7.1 / 0 / 5.5 / 14.5 / 1.1 / 1.2 % (immaterial class, reported not gated) | binds inside the UC's online envelope; reported |
  | `cc_committed_per_plant = true`, `cc_committed_offer_margin = true` | the CC committed tranche (an offer-curve share, not a floor) | not a D-2 row; it is most of UC-0 M2(b) (CC online ≤ 0.67 × cap while CEMS is off: 9.3 TWh in 2019 of which the bridge forces 0.15) | D-3: amortized markup zeroed on integer clusters; the UC may decommit the whole plant (committed tranche included). T2 measures it |
  | `chp_steam` (CC_CHP / CT_CHP host steam) | exempt class (D-2 `d2_exempt_classes`) | CC_CHP 20–49 %, CT_CHP 15–37 % | `*_CHP` excluded from the integer set (GATESPEC §1) — unchanged |

  The bridge the arm removes forced 0.15 / 0.63 / 2.78 / 2.93 / 1.26 / 1.31 / 1.92 TWh of CC_REGULAR (0.1–2.4 % of class
  energy) and carries 13 / 7 / 16 / 17 / 14 / 12 / 14 pre-existing D-4 conduct-rider failures per year in the control; those
  rows disappear with it (a D-4 row that vanishes is not a "new D-4 FAIL row").
- **Pricing (R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC objective; make-whole in
  `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (R4, D-4):** UC min-load energy is REPORTED under MECH 28 and not budgeted. The scorer at the pin budgets
  `uc_schedule` in the D-2 share (SPP RESULT §1): C8 is therefore reported both as the scorer prints it and with MECH 28
  removed, and a C8 flip counts only if it survives the R4 adjustment.
- **D-2 (owner, 2026-10-09, "Keep 3×; fund speedup"):** the wall ratio is reported per year against 3×; this lane reports
  the ratio and does not judge it (UC-DESK charter).
- **Not a matrix re-test (rule 28).** ERCOT cells: `gas_commitment_bridge` **K** (trough diagnosis §7), `online_capacity_envelope`
  **R** (ERCOT-107/108; ercot83 posture probe), the posture family default-off (spec §1.6, `ercot_commitment_posture`). None
  is re-tested here: the integer commitment state is a different object from a P0-detected bridge, a relaxed posture and an
  online-capacity envelope (plan §6; GATESPEC §5 "integer state is the new evidence"). The cell this lane feeds is
  `unit_commitment_milp` (ERCOT: `U`, minted by UC-1), stamped from the RESULT as this branch's last commit. DO-NOT-REDO
  honoured (`docs/mechanism-testing-matrix.md` §5.1): no `coal_offer_level_rebasis`, no `ercot_as_held_location` /
  `ercot_artificial_shortage_pricing`, no `temp_dependent_derate`, no `measured_chp_heat_rates` on the bin path, no offer-band
  retune, no `--set` beyond the two-field delta.
- **DOF (rule 21):** zero free parameters added. Every UC parameter is measured or published (UC-0 FINDING §5: NREL start
  costs; no-load = CAMPD per-unit intercept × delivered fuel, ERCOT no-load fit 188–197 of 191–203 units, R² 0.97–0.98,
  class-mean fallback 4 CC / 3–4 ST_GAS / 0–1 coal plants, reported from `uc_solve_log_<y>.json clusters[].src`). The keeper's
  authorized price tuning (`offer_curve_by_group`, incl. the 2024–2025 forward partition's peak bands) rides unchanged.

## 2. Target readings (fixed ex ante; bar = half the distance to the gate band or to 1, the closeout convention)

Control values are the keeper's committed records (rubric 3.20) and UC-0's census on the keeper
(`results/phase0/xiso/_ucmilp_benefit_screen.json`, `isos.ERCOT.years`). "met" is decided on the composed span's
`calibration_verdict.py` output and the zero-LP re-measurement of UC-0's M1/M2/M3/M4 on the arm bundle
(`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported, pointed at `results/calibration/ucmilp_ercot_span` —
the same conventions as the board; on-threshold 1 % of available cap).

| # | reading | control | sign expected | bar (met iff) |
|---|---|---|---|---|
| T1 | CC_REGULAR starts per year, model vs CEMS (M1), 2019 and 2020 — the two bridge-over-hold years | 2019 **491 vs 3,070** (0.16×, \|ln\| 1.83); 2020 **1,901 vs 3,489** (0.55×, \|ln\| 0.60) | toward CEMS, from below | \|ln(model/CEMS)\| halves: 2019 ≤ **0.92** (ratio in [0.40, 2.5]); 2020 ≤ **0.30** (ratio in [0.74, 1.35]). An overshoot past 1 (SPP: CC crossed to 0.6× CEMS) is scored by the same \|ln\| |
| T2 | M2(b): CC_REGULAR online at ≤ (mlf + 0.10)·cap while CEMS is off, TWh, 2019 and 2020 | 2019 **9.34**; 2020 **8.94** | down | 2019 ≤ **4.67**; 2020 ≤ **4.47** (half). Reach bound stated now: the bridge itself forces only 0.15 / 0.63 TWh, so the bar is met only if the UC also decommits the committed tranche the bridge did not hold; a right-sign move short of the bar reads I, not R |
| T3 | C3b monthly NRMSE, 2019 and 2020 (band ≤ 0.20) | 2019 **0.216** FAIL; 2020 **0.208** FAIL | down | 2019 ≤ **0.208**; 2020 ≤ **0.204** |
| T4 | C1 CC_REGULAR and COAL_PRB, 2019 and 2020 (band ±8 TWh & ±3 pp) | 2019 CC **+9.21** / PRB **−10.79**; 2020 CC **+10.17** / PRB **−11.85** (all FAIL) | CC down, PRB up (the SPP direction, CC → coal, is the direction these rows need) | CC 2019 ≤ +8.6, 2020 ≤ +9.1; PRB 2019 ≥ −9.4, 2020 ≥ −9.9 (half the distance to ±8) |
| T5 | M3 low-price-hour count ratios model/actual (≤ $15 · < $0), every year | 2019 0.14 · 0.04; 2020 0.36 · 0.00; 2021 0.01 · 0.02; 2022 0.00 · 0.02; 2023 0.15 · 0.29; 2024 0.34 · 0.07; 2025 0.26 · 0.02 | both rise toward 1 | sign only; magnitude reported |
| T6 | M4 reserve dormancy (model share of hours with reserve MCP < $1 vs actual; mean MCP) | model 0.96–1.00 vs actual 0.00–0.01 (2019–23), 0.26 (2024), 0.52 (2025); mean MCP model $8 / $1.75 / $67 / $43 / $114 / $13 / $0.3 vs actual $29 / $12 / $312 / $19 / $26 / $6 / $3 | dormancy share falls; mean MCP toward actual | sign only; magnitude reported (SPP: no move) |

**Expected cost, declared, not a kill (UC-0 F2; charter):** the model-LOW years. 2023 C3a **−24.7 %** (owner-signed
configuration-exception CAVEAT, non-downgrading; the carve-out year) and 2024 C3a **−11.3 %** (FAIL) are expected to move
further from the band when the trough body falls. Reported as a cost with their C3b direction; FAIL → FAIL and CAVEAT → worse are
not flips. The two PASS rows with the least headroom are **kill rows**, not cost rows, and are named in §3.

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered ERCOT year, any criterion, any class row** (`calibration_verdict.py` per-(criterion,
key, year) status diff vs the keeper). The rows with the least headroom, named now so the reading cannot be re-interpreted:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| 2025 | C3a | −9.2 % PASS | **0.8 pt** | model-low; a trough fix moves it toward the edge (SPP flipped every model-low year) |
| 2022 | C3a | −8.4 % PASS | 1.6 pts | model-low, 2022 gas |
| 2019 / 2020 / 2021 | C3a | +6.2 / +2.5 / +0.8 % PASS | 16–11 pts | body down helps; a reach past −10 % is not credible |
| 2024 | C3b | 0.198 PASS | **0.002** | shape may re-order; the lowest-headroom row on the board |
| 2022 | C3b | 0.178 PASS | 0.022 | shape |
| 2021 / 2025 | C3b | 0.066 / 0.125 PASS | ≥ 0.075 | — |
| 2022 | C8 ST_GAS | 28.7 % PASS (cap 30 %) | **1.3 pts** | the SPP stacking pattern (kept drag + UC); counted only if it survives the R4 adjustment (MECH 28 removed) |
| 2020 / 2021 / 2025 | C8 ST_GAS | 23.6 / 21.9 / 21.1 % PASS | 6–9 pts | same |
| 2024 / 2022 / 2023 / 2021 | C1 CC_REGULAR | −4.45 / −3.47 / +1.38 / −0.83 TWh PASS | 3.5–7 TWh | CC energy falls under the UC (SPP −5 to −8 TWh/yr): 2024 is the tight row |
| 2021–2025 | C1 COAL_PRB | −2.01 / −1.38 / −2.47 / −0.97 / +0.87 TWh PASS | ≥ 5.5 TWh | coal rises under the UC (SPP +3.5 to +7): 2025 is the tight row (7.1 TWh) |
| 2019 / 2023 | C3c | 90 vs 106 h (0.85×) / 138 vs 181 h (0.76×) PASS (band 0.5–2×) | 37 h / 47 h to 0.5× | scarcity hours fall if the online envelope relaxes; a move below 53 h (2019) or 91 h (2023) is a flip |
| 2020 / 2021 / 2022 / 2024 / 2025 | C3c | CAVEAT, ledgered (22 / 651 / 94 / 11 / 0 h vs 56 / 258 / 196 / 53 / 31) | — | the probe bundle carries no attestation, so these read FAIL by artefact (§8); the magnitudes are compared directly and a CAVEAT → FAIL by artefact is not a flip |
| 2023 | C3a / C3b | CAVEAT (owner configuration exception; −24.7 %, 0.393) | — | same artefact; declared cost rows (§2) |
| every year | C2, C4, C6 | PASS | — | C6 reads UNATTESTED on the probe (artefact) |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper (control: 0 in every year);
no NEW D-4 FAIL row (the control's own rows: `gas_commitment_bridge` 7–17/yr — vanish with the bridge; `st_netload_drag` 1–2/yr;
`reliability_floor` 1/yr; `chp_steam` 1–2/yr — pre-existing). The determination (`iso_determination`) is reported, not gating:
ERCOT is NOT-YET on the keeper's open rows and stays so unless every failing row clears, which no reading here predicts.

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, COAL_PRB, COAL_LIGNITE, ST_GAS) and ISO-wide; the kept floors' own shares beside it | 0 (no UC); kept floors as in §1 | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 and the kept ids |
| S2 | starts per plant-year vs CEMS (M1) for every slow class | CC in T1; COAL_PRB 87 / 166 / 13 / 26 / 42 / 59 / 28 vs 17 / 23 / 30 / 29 / 38 / 40 / 31 (model over-cycles coal 2019/2020); COAL_LIGNITE 53 / 85 / 73 / 55 / 32 / 83 / 32 vs 23 / 15 / 17 / 20 / 9 / 20 / 13; ST_GAS 2,032 / 2,377 / 1,754 / 1,412 / 2,051 / 2,409 / 2,339 vs 1,011 / 952 / 1,042 / 1,329 / 936 / 736 / 981 | `screen_year` M1 on the arm; `uc_schedule_<y>.parquet` Σ`v` per cluster as the engine's own count. Sign expected: coal and ST_GAS starts down toward CEMS (SPP: the UC under-cycled every slow class — reported either way) |
| S3 | online capacity vs the measured online series | — | comparator = the 60-Day SCED telemetered HSL of online thermal resources (`scripts/lib/sced_corpus_instruments.py::load_corpus_year`), where the corpus year is on disk after hydration; years without a full-year corpus are SKIPPED and named; the arm's `online_mw` from `uc_schedule_<y>.parquet` is also reported against the keeper's available MW (model-internal) |
| S4 | integer set and fallback shares | UC-0 M6: 73 ERCOT plant clusters, 59.7 GW; integers per 36-h window 1,548 CC + 288 PRB + 108 LIG + 612–684 ST_GAS | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| S5 | M1 short-on energy, ST_GAS (runs shorter than UT = 24 h) | 4.14 / 5.04 / 3.35 / 2.09 / 4.16 / 4.32 / 3.61 TWh = 29 / 42 / 27 / 17 / 25 / 25 / 29 % of class energy (UC-0 F4: the drag's runs are short) | `screen_year` M1 on the arm; expected to fall under min-up |

## 5. Cost readings (reported; D-2 ratios reported against 3×, never judged here)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all seven years |
| W1-denominator | the keeper bundle records no P0/P1 seconds. **Declared proxy** (SPP precedent): baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line, so ratio = total / (P0 + P1) in one container. Beside it, the on-record ERCOT rows of `docs/records/misc/wallclock-baseline-2026-07.md` §WALLCLOCK 3a (2023: P0 174.7 + P1 25.0 = 199.7 s; 2024: 159.4 s; 2025: 166.2 s; older recipe) | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` ÷ Σ_t λ_P1 × load (from `hourly/system_<y>.parquet`) | ≤ **2 %** (sanity; SPP 1.0–4.4 %) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise §6 kill #1) |
| W5 | the D-2 ratio vs the 3× ceiling, per year | reported, not judged (owner "Keep 3×; fund speedup"; SPP 5.1–10.2× at uc-1.1, 7.1× lean) |

**Budget (fixed by the rule declared before the bench): ceil(1.3 × (P0+P1 capture + 12 × January UC Σ s + build) / 60) =
ceil(1.3 × (529.2 + 263.5 + 12 × 670.8 + 12 × 2.5) / 60) = **193 min** per span shard** (the rolled year extrapolates to
≈ 8,050 s of MILP against ≈ 790 s of P0+P1, a D-2 ratio near 11× before the P1 and write phases; January is one month of
thirty-one windows, so a summer window set that runs longer than 1.3 × January is the declared risk, and a shard that reaches the
budget with no bundle stops and reports). The span prompts are regenerated at the pin with this budget.

## 6. G-DRIFT: `main` at the pin vs the keeper's solve basis (rule 29(b): a zero-LP code audit; LIVE only earns a control solve, which this lane does not run)

Basis `106d6bb737488f4086151907b4dbc4a45ee17306` → pin `2f872a62a7cccadb6800555c11a73745dcdb89a4`: 175 files on the
backcast path (`src/market_sim`, the four orchestrators, `scripts/lib`), of which the UC stage is new
(`model/uc/*`, `pipeline/uc.py`, `scripts/lib/uc_bench.py`, `scripts/lib/uc_params/*`). Four instruments, strongest last:

| instrument | result | classification |
|---|---|---|
| `scripts/solve_surface_register.py --diff 106d6bb7 2f872a62` | *"336 → 342 names; 1 value moved, 6 added, 0 removed"* — moved: `NUCLEAR_MONTHLY_CF_BY_YEAR` (re-keys MISO, NWPP, PJM, SOCO, SPP); added: `NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR`, five `NWPP_*` seam series. **per-ISO totals: ERCOT 0** | INERT for ERCOT: no ERCOT key moved; the ERCOT row of `NUCLEAR_MONTHLY_CF_BY_YEAR` is byte-equal at both SHAs (compared by value, instrument 2) |
| every `ScenarioConfig` default at both SHAs (sparse `src/` worktree at the basis; compared by `repr`) | 25 fields added, all default `False` or the `uc_*` defaults; **none** named by `iso_configs` ERCOT `default_scenario_overrides`, **none** in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, **none** present in the keeper's `run_config_<y>.json` (dropped from `cache_key()` at default). 1 removed: `unit_outage_dispatched_bin_live_denominator` (recorded `false` in every keeper year; `replay_keeper._RULE26_DELETED_UNCONDITIONAL` carries it). 5 "moved": the `*_path` defaults, which differ only by the repo root of the worktree (derived from `__file__`) | INERT: added-at-default and absent from the recipe; the deleted knob was off; the path defaults are the same files |
| every top-level constant at both SHAs, compared by value (sha256 of the JSON) | 6 added (the surface's six); 3 "moved": `CAMPD_BINNING_ISOS` (same six members, set order), `RGGI_MEMBER_STATES_BY_YEAR` (same members per year, frozenset order; no TX, never read by ERCOT), `NUCLEAR_MONTHLY_CF_BY_YEAR` (ERCOT row identical; other ISOs' rows moved); the shard's run of the probe also lists `EIA930_PS_FOLDED_INTO_WAT` (`{MISO, PJM}` at both SHAs, frozenset order) | INERT |
| every hunk on the LP-construction and solve path, read (the probe below does not cover them): `model/lp/layout.py` (`kron_hours`, a documented byte-identical replacement of `sp.kron(eye(T), block)`), `model/lp/{rows,reserve_rows}.py` (call-site swaps to it), `model/lp/model.py` (basis-status object array; float32 copies without a float64 intermediate), `model/storage.py` (CAISO envelope quantile by reshape, same floats), `model/lp/hydro_cascade.py` (one copy fewer), `pipeline/solve.py` (**the one LIVE hunk, intended: the `unit_commitment_milp` gate** — at `False` no statement runs; `zonal_loss_demand_reconciliation` default off), `pipeline/year.py` + `pipeline/commitment.py` (`diagnostic_coal_metered_online_floor` default off, returns the prep unchanged; SOCO campaign-floor one-pass refactor, SOCO-gated), `pipeline/backcast_config.py` (`caiso_ra_min_load_frac` 0.26 → 0.570 for CAISO only; ERCOT keeps 0.40, which the keeper records), `results/scarcity.py` (formatting only), `results/emissions.py` (row-wise CO2 over the same scalars), `results/export.py` (`emergency_band` summary rows), `run_calibration.py` (NWPP seam limits/vintage, SPP MMU pool, MISO seam full-span, SOCO take floor and `COAL_PLANT_GRAIN_ISOS += SOCO`: every hunk ISO-gated off ERCOT or default off; the reliability-floor lay-up roster hunk sits behind `reliability_floor_layup_window_mask`, which the keeper records `false`, and excludes ERCOT by name), `run_calibration_full.py` (`_btm_frame` ERCOT branch behind `ercot_chp_btm_measured`, default off, and the measured artifact `chp_btm_share_measured_ERCOT.csv` does not exist at the pin, so both share maps are the keeper's; `check_bench_freshness.py --iso ERCOT`: 7 parts reproduce, 0 STALE; the UC artifact drain behind the gate) | INERT with reason, except the gated UC hunk, which is the arm |
| **instrument 3 — the LP's actual inputs, rebuilt at both SHAs** (`scripts/probes/_closeout_ercot_w6_gdrift_identity.py`, the ERCOT-w6 precedent: two `fleet_only` rebuilds per year on the keeper's OWN recipe with its per-year partition overlay, `market_sim` from a sparse worktree at the basis in one arm and from the pin in the other, one shared data tree, every LP-visible array and the demand differenced by sha256) — covers the fleet-build side this reading does not (`data/fleet/{arrays,assembly,eia860,floors,legacy_bins,models}.py`, `data/{outages,coal,campd,chp,cod_ramp,emission_rates,renewables,eia923}.py`, `data/eia930/*`, `data/fuel/*`) | run in the zero-LP shard `ucmilp-ercot-gdrift` (`session_01WbdnGHvCUqWQ5xw14uW3TL`, Opus, launched 00:51Z at the pin; prompt committed as `shard-prompt-ucmilp-ercot-gdrift.txt`; DATA PROFILE ercot) | **ALL LP INPUTS BIT-IDENTICAL, 2019–2025** (shard report 01:10Z; `results/phase0/ercot/_ucmilp_ercot_gdrift_identity.json`, leg commit `1d87f818`, checked out onto the lane branch): 105 LP-visible arrays + demand per arm over the seven years, empty mismatch list. The probe's own instruments 1–2 agree with this lane's (the five `*_path` "changes" are the worktree root; one more constant it lists, `EIA930_PS_FOLDED_INTO_WAT`, is `frozenset({MISO, PJM})` at both SHAs — frozenset order only, and no ERCOT reader). The probe's `not_covered` (LP construction, solve, post-`fleet_only`) is closed by the hunk reading in the row above. Rule-for-the-span condition (b) **met** |

**Rule for the span (fixed now):** the span shards launch only after the L1 gate (§0.1) passes AND instrument 3 reads
*ALL LP INPUTS BIT-IDENTICAL* on every year. Any year reading INPUTS DIFFER is a LIVE hunk: the lane STOPS, records the mismatch
list in an addendum and routes it to UC-DESK (a control solve is the desk's call, never this lane's — rule 29(b)).

## 7. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"): an engine
   defect, routed to UC-DESK, never a tuning invitation (the SPP Addendum A/C route: a new pin needs a new addendum BEFORE any
   relaunch; readings, bars, kills and budget never move).
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed runs of the
   same recipe-year. Exercised only if a relaunched shard (PENDING > 45 min) and its predecessor both complete; otherwise
   "not exercised".
3. **A control flip** (§3) in any registered year.

## 7.1 Verdict rule (fixed) and the D-6 card

- **K candidate** — T1, T2, T3 and T4 met in both target years, T5/T6 signs right, no kill, every leg Optimal: recommend the
  owner's D-6 card read "promote on structure"; the lane never promotes (rule 31; UC-4 is the desk's slot).
- **R** — any target reading moves the wrong way past its control (CC starts further from CEMS, M2(b) up, C3b 2019/2020 up,
  C1 2019/2020 CC up or PRB down), or any kill fires.
- **I** — no kill, no wrong-sign move, but |Δ| below the bar on T1–T4 (GATESPEC §7.2: "the relaxation was already tight here"
  is a finding).
- Mixed: the verdict is the worst of the target rows, stated row by row; the declared costs (2023/2024 C3a) are reported beside
  it. The RESULT carries the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve plan (rules 16, 32–36) and the composition deviations, declared now

- **Seven shards, 2019–2025**, one year each, `claude/ucmilp-ercot-<y>`, out-dir `results/calibration/ucmilp_ercot_<y>`,
  prompts from `scripts/shard_prompt.py --iso ERCOT --all-years --sha 2f872a62a7cccadb6800555c11a73745dcdb89a4 --lane
  ucmilp-ercot --bundle results/calibration/closeout_ercot_l1_span --set unit_commitment_milp=true
  --set ercot_gas_commitment_bridge=false --budget <§5> --note "ucmilp-ercot: UC A/B"`, each appended with: confirm
  `hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json` and `hourly/unit_marginal_<y>.parquet`
  are in the pushed tree; report the GATESPEC §6.1 wall row (the `log_year_phase_timing` line + `uc_solve_log_<y>.json summary`).
  Committed as `shard-prompts-ucmilp-ercot.txt`. `create_session` per year: `source_revision` = the pin, model `claude-opus-5-5`,
  tag `ucmilp:UC-2-ERCOT-shard`. PENDING > 45 min: archive and relaunch.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_ercot_<y>` non-empty; check out; verify
  `dispatch/<y>_P1.parquet` + the three UC files; THEN `archive_session` (rule 33).
- **Compose and score, zero LP, at the pin:** `_ucmilp_compose_span.py` at the pin will ABORT on this keeper (SPP Addendum D §1,
  generalised): its `PER_YEAR_FIELDS` lacks `gas_price_override` and the ERCOT keeper additionally records 12 fields per year by
  design — the owner config partition and the vintage-gated market-design fields: `offer_curve_by_group` (2024–2025 forward
  bands), `ercot_offer_swcap_clip`, `ercot_swcap_effective_hourly`, `ercot_swcap_vintage`, `ercot_zonal_spread_ep_referenced`,
  `ercot_load_resource_reserve_from_year`, `ercot_reserve_supply_cap_from_year`, `ordc_lolp_shift_sigma`, `ordc_mcl_mw`,
  `ordc_voll`, `voll`, `weather_year`. **Declared workaround:** a scratch copy of the composer (no repo script edited) whose per-year
  set = `PER_YEAR_FIELDS` ∪ {every field on which the keeper's own `run_config_<y>.json` disagree}, computed from the control
  bundle, with one added assertion: on every per-year field each arm leg's value equals the keeper's value for that year, so the
  recipe delta is exactly the two arm fields; plus the keeper composers' `_respan_shared_inputs` (`_w0_compose_span.py`) so the
  span's benchmark frames are rebuilt over the whole span (expected to resolve to the keeper's own frame hashes). Then
  `calibration_verdict.py`, `legitimacy_diagnostics.py` (regenerated, never copied), the M1/M2/M3/M4 re-measurement. The parent
  runs no LP. Both composer gaps stay routed to UC-DESK for the engine lane's composer.
- **Attestation artefact (SPP Addendum D §3):** the probe carries no `calibration_attestation.json`, so C6 reads UNATTESTED and
  the rule-22 / configuration-exception ledger routes are unavailable: C3c 2020–2022/2024/2025 and C3a/C3b 2023 read FAIL by
  artefact. The RESULT marks them and compares magnitudes directly.
- **Registration: NONE on the dashboard** (UC-DESK ruling 2026-10-10 on the SPP RESULT: audit E13 admits only keepers or folded
  runs; the ERCOT-w4 #7202 precedent). The slim span goes under `docs/records/ercot/ucmilp/data/ucmilp_ercot_span/` (`metrics.json`,
  `meta.json`, `run_config*.json`, `legitimacy_diagnostics.json`, `uc_solve_log_<y>.json`, `hourly/{class_band_hourly,class_hourly,
  system,storage,reserve_family,uc_schedule,uc_uplift}_<y>.parquet`; `unit_marginal_<y>.parquet` (27 MB/yr for ERCOT) stays on
  the leg branches and is named there). Never promote; never delete a bundle (rule 31). One PR; UC-DESK merges.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-ercot-ab-<date>.md`: the §6.3 gate table first, control → arm, every year;
  the wall rows; every reading answered; kills checked; the verdict K-candidate/R/I; the D-6 card text; where each bundle is and
  what a promotion would cost; `## Log entry`); the ERCOT `unit_commitment_milp` cell stamped with verdict + citation as the last
  commit after rebasing; `send_message` UC-DESK with the gate table first, then the wall rows.

## 9. DO NOT REDO

Everything in `docs/mechanism-testing-matrix.md` §5.1's DO-NOT-REDO; no posture (`ercot_commitment_posture`) in any form; no
`online_capacity_envelope`; no `uc_*` value other than the declared defaults; no third `--set`; no control solve; no NEISO/NYISO
span (the UC-2 control lanes'); no dashboard registration; no promotion.

## Addendum A (2026-10-10 01:55Z) — engine defect #3 from the L1 gate; the bench moves to the lane SHA; the span pin is a desk question

**L1 gate run 2 (`b61f0279`, 01:22–01:43Z): STOPPED with a clear report.** The harness fixes held (bridge OFF confirmed:
no "gas commitment bridge … floored" line; `replay/run_config.json` records `ercot_gas_commitment_bridge: false`; capture P0
440.0 s, P1 215.9 s, peak RSS 11.58 GiB; UC prep *141 clusters, 72 integer (937 fleet rows), W=24 L=12*). Both rungs then
crashed at the FIRST window build, before any MILP:

```
src/market_sim/model/lp/bounds.py:194  col_upper[:, _flow_off:_slack_off] = ttc_arr
ValueError: could not broadcast input array from shape (8760,10) into shape (36,10)
```

**Root cause (confirmed by this lane's read at the pin):** `model/uc/window.py::_slice_obj` sliced only arrays whose LAST
axis is `T`. ERCOT's hourly `ttc` / `ttc_import` (the measured GTC overlay) are time-major `(T, n_links)`, a form
`lp/bounds.py` accepts beside the static `(n_links,)`; they reached the 36-hour window unsliced. SPP has no hourly link
limit, which is why its A/B never hit it. **The third engine defect found by a shard** (SPP found two), and the L1 gate did
exactly what it was added for: no span shard was spent.

**Fix (this lane, Fable, rule 27; commit `97e33b54` on the lane branch; blob of the 967-line module verified on the remote):** a
2-D array whose leading axis is `T` is sliced on that axis; hour-minor arrays and static vectors untouched. Unit test
`tests/unit/model/uc/test_window_slice_time_major.py` (the slicer, and `slice_window_inputs` with an hourly `ttc`); the UC
unit suite 36/36 and the model window/bounds/dispatch suite 184/184 pass. The hunk is inside the UC stage, gated behind
`unit_commitment_milp` (G-DRIFT: INERT at the keeper's default; the control is untouched).

**Pins, restated.** Bench run 3 runs at `97e33b54` (the lane SHA: pin + two harness fixes + this engine fix). The SPAN pin is
no longer `main 2f872a62` as §1 declared: `2f872a62` cannot solve an ERCOT UC window. The choice is UC-DESK's (engine owner;
the SPP Addendum A/C route): **(a)** the desk ports `97e33b54`'s hunk to `main` and the span pins that `main` SHA, or **(b)**
the span pins the lane SHA `97e33b54` itself (the diff from `main` is the three fixes above and the lane's docs, nothing else
on the solve path). Either way the span prompts are regenerated at the chosen SHA before launch; readings, bars, kills and
the budget rule do not move. Routed to UC-DESK at 01:55Z with the defect, the patch and this question.

**UC-DESK ruling (01:52Z, verbatim):** *"accepted. Porting 97e33b54 + bench half of ad5a74d9 to main now (branch
claude/ucmilp-fix-window-slice, head 3caa07dd, blobs verified). I'll send the merge SHA when CI is green — pin span shards on
that main SHA (G-DRIFT lane SHA→main: expect only the doc/record delta). Bench run 3 at 97e33b54 is fine to continue; its
numbers carry over (engine bytes identical)."* → route **(a)**: the span pins the desk's merge SHA on `main`; the span prompts
are regenerated at it; the bench numbers from `97e33b54` carry (engine bytes identical, to be confirmed by `git diff` of
`src/` between `97e33b54` and the merge SHA before launch).

**UC-DESK (01:59Z, verbatim):** *"#7221 merged. PIN = dc3860bef44f8ac0e322f92da94fd6c011bec381 (engine bytes = your
97e33b54; bench harness = ad5a74d9 half). G-DRIFT 2f872a62→pin: UC window slice + bench harness LIVE on arm only, control
INERT; plus docs-only #7220. Record addendum, then launch span shards."* → **SPAN PIN = `dc3860be`** (`main`). Verified by this
lane, with one correction to the desk's line: `git diff 97e33b54 dc3860be -- src/ scripts/lib/uc_bench.py
scripts/diagnostics/bench_uc_ladder.py` is NOT empty. The UC engine (`model/uc/*`, `pipeline/uc.py`) and the bench harness ARE
byte-identical to the lane SHA the bench runs at; `main` additionally carries PR #7219 (`coal_sync_floor_release`, UC-2-SPP-B,
owner ruling D-5b): a new `ScenarioConfig` field, default `False`, cache-key registered, and one hunk in
`data/fleet/arrays.py::_compose_min_gen_floors` gated behind it (*"Off, the historical branch is taken verbatim"*). The ERCOT
keeper does not record it and the arm does not set it → **INERT for both control and arm** (G-DRIFT instrument 1: added at
default, absent from the recipe). `2f872a62 → dc3860be` therefore carries the three fixes, #7219 (inert here) and docs (#7220,
the SPP RESULT's records). The seven span prompts are regenerated at `dc3860be` (`shard-prompts-ucmilp-ercot.txt`). The span launches once the
L1 gate (bench run 3, in flight) reports its pass line — the gate's purpose does not change with the pin.

## Addendum B (2026-10-10 04:40Z) — KILL #1 on the 2020 span leg (§7.1): UC window 118 infeasible

**Shard `ucmilp-ercot-2020` (`session_01Y1MSsw7nq6jweLCUL3Urn6`, pin `dc3860be`, 02:43–03:56Z): STOPPED on §7 kill 1, nothing
pushed, archived.** P0 364 s (219,638 simplex iterations); UC prep *141 clusters, 72 integer (937 fleet rows), W=24 L=12*;
windows 0–117 (Jan 1 → Apr 27) solved; **window 118 [2832, 2868) (Apr 28 00:00 → Apr 29 12:00, leap year)
`UcWindowInfeasible`: no feasible incumbent, LP relaxation ALSO Infeasible** (89,928 columns, 14,359 rows, 72 integer clusters).
Engine diagnosis verbatim: *"a-priori contradictory rows: min_down=1; carried starts above n: 0; floor above min-down: 1"*.

**Reading (zero-LP, from `model/uc/diagnose.py::diagnose_window` at the pin):** `floor_above_min_down` counts cells where
`u_lower > n − hist_w`, i.e. the window's floor needs more units of a cluster online in some hour than the cluster has NOT
held offline by shutdowns carried in from the previous window's committed hours (`hist_w`, min-down holds). The one
contradictory `min_down` row is that cell's hold row against the floor's lower bound; the relaxation is infeasible before any
integrality. This is a floor (a P1 fleet prep composed upstream of the UC hook — `coal_min_config`, `st_netload_drag`,
`reliability_floor`, or the availability-scaled pmin of a `_mustrun` band) demanding output inside a carried min-down hold:
the collision the look-ahead min-down guard rows (`units_needed_for_floor`, reach `dt_max − 1` beyond the window end;
FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04) exist to prevent, so a case they do not cover. Rule 17/19 territory
(a floor binding where the commitment physics says the unit is offline), inside the engine. **Engine defect #4 class**; the
dump (`_dump_window`) is not written on the production path (`debug_dump_dir=None`), so naming the cluster and the floor needs
either a bench re-run of window 118 with `--dump-dir` or a production dump switch — the engine lane's call. Routed to UC-DESK
04:33Z with the question: relax a floor that falls inside a carried hold (floor loses, logged under its D-2 id) or extend the
guard reach to the floor horizon.

**Consequences for this lane (fixed by §7):** no re-tune, no second arm, **no relaunch of 2020 at this pin**. The other six legs
(2019, 2021–2025) run on; a leg that completes is fetched, verified and kept (rule 31); a leg that hits the same kill is recorded
here. A seven-year span cannot be composed without 2020 (rule 16), so the A/B's gate table is NOT scorable at `dc3860be`; the
RESULT reports what the legs that finished show (structure and cost readings per year) and the kill. The relaunch route is the
SPP Addendum A/C route: the engine lane's fix lands on `main`, UC-DESK sends the new pin, this file gets Addendum C with the
new pin, the 2020 leg (and any other killed leg) relaunches there, and legs solved at `dc3860be` carry only if the fix is
byte-inert on their windows (the desk's G-DRIFT call, else all seven relaunch). The L1 gate's January-only roll is recorded as
the gate's limit: a window-118-class collision is a mid-year event the gate cannot see.

**UC-DESK rulings (04:33Z and 04:34Z, verbatim):** *"that is engine defect 5 (same signature as MISO 7/7 and NEISO 2021/2023).
UC-1-FIX-2 (session_01VQbdDQky4y91ytyky1UEge) has it root-caused: the min-down guard read floor needs on the unpinned year
fleet as ceil(floor/p̄); inside a window, budget-pinned rows (and derated availability) need more units. Fix (uc-1.2, option
a: guard reads the window/pinned fleet with the row-(a) count; no floor yield) is in validation. Answer to your question: guard
extension, not floor relaxation. Let the other six legs run; send your zero-LP census of hours 2832–2868 to UC-1-FIX-2 directly
(useful as a third ISO check). Relaunch failed years on the fix's merge SHA (Addendum A rule: pin moves, nothing else)."* and
*"all seven relaunch at the fix's merge SHA. The uc-1.2 guard change touches the guard rows of every window, so it is not
byte-inert on solved legs, and one span = one engine. Keep the dc3860be legs as evidence (not scored). The fix's diagnosis text
now names plant/family/n/dt, so no dump switch is needed."* → the span at `dc3860be` is evidence only; **Addendum C will carry
the uc-1.2 merge SHA as the new pin and all seven legs relaunch there**; readings, bars, kills and the budget rule do not move.

**UC-1-FIX-2 (04:37Z, verbatim):** *"your census fits. All 11 yards being budget rows means every ERCOT coal cluster is pinned
inside a window: availability = P0/pmax, so row (a) needs u = n wherever P0 > 0. The uc-1.1 guard read the unpinned year fleet
and could not see that. The availability steps at 2856 also change row (a)'s per-unit capacity p̄·a; uc-1.2 counts the need as
⌈floor/(p̄·a)⌉ on the window's own fleet. Validation shard for ERCOT 2020 at f2c7166a (uc-1.2): session_01M6wvBm27qR66hrxksg9oKe
(arm: unit_commitment_milp=true, ercot_gas_commitment_bridge=false)."* The census is at `data/census_w118_2020.txt`. The lane
waits for the uc-1.2 merge SHA (Addendum C) and the six `dc3860be` legs in flight.

### Addendum B.2 (05:20Z) — KILL #2 on the 2019 leg; 2024 and 2025 legs complete at `dc3860be`

**2019 (`session_019138zrzCoLCMQd4A5C5qiF`): STOPPED on §7 kill 1, a different signature.** Every UC window solved (365 windows,
Σ MILP 6,257 s, mean 17.0 s, nodes p50 13, 0 time-limit hits; 73 integer clusters / 954 rows); the **P1 dispatch LP built on the
UC schedule is Infeasible** — cold rebuild on the floored fleet, 0 simplex iterations (HiGHS presolve found the bounds
contradictory): `model/lp/model.py:1419 RuntimeError: dispatch LP has no feasible primal solution (status: Infeasible)`. P0 266.9 s.
Nothing pushed; archived. Reading: the UC's per-unit-hour bounds (MECH 28) collide with another P1 row family on the full-year
LP — the candidates the shard named are derated availability, the coal monthly pile ceiling (a budget row the window pins to P0
but the year LP does not) and the reserve headroom cap. The engine lane's call whether uc-1.2 (which changes the guard's unit
count, not the P1 bounds) covers it; routed to UC-DESK and UC-1-FIX-2 with the traceback.

**2024 (`0c76c8c3`) and 2025 (`df87a9be`): COMPLETE**, fetched blobless, all five artifacts verified in the pushed trees, checked out
onto this container (22 and 21 files). Wall rows (GATESPEC §6.1; evidence only — the span is not scorable at this pin):

| year | P0 s | UC Σ MILP s (windows / mean / p95 / max) | P1 s | total s | ratio total/(P0+P1) | nodes p50/p95 | gap p95 | TL hits | warm | integers/window | peak RSS GiB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2024 | 368.9 | 6,482 (365 / 17.8 / 38.8 / —) | 359.7 | 7,404 | **10.2** | 17 / 79 | 9.5e-4 | 0 | 365/365 | 2,556 | 12.63 |
| 2025 | 493.0 | 6,660 (365 / 18.3 / 48.9 / 235.8) | 454.9 | 7,807 | **8.2** | 17 / 126 | 9.8e-4 | 0 | 365/365 | 2,556 | 12.69 |

Both: 0 unserved MWh; **52 of 139–140 clusters on the class-mean no-load fallback** (count `none → 1`, up/down from the class
table; 87–88 on measured `uc-params`) — far above UC-0's 4–8 fallback plants, a parameter-coverage finding for UC-DESK. 2025's
regenerated `legitimacy_diagnostics.json` reads **D-2 ST_GAS 32.6 %** of class energy (3.71 of 11.39 TWh: `st_netload_drag` 2.07 +
`uc_schedule` 1.65) — the §3 kill-row candidate (2022 C8 ST_GAS was named; 2025 sat at 21.1 %), to be read under R4 with MECH 28
removed (17.9 % → no flip) when a scorable span exists; D-4 `reliability_floor × CT_PEAKER` 93.4 % off-window (pre-existing
class, control 77.9 % in 2019). The `**` negation pushed `unit_hourly_2024.parquet` (84 MB), `2024_P1_fleet.parquet` and
`floors/` on the 2024 leg (the 2025 shard unstaged its `unit_hourly`); neither enters the slim records.

**UC-DESK (05:21Z, verbatim):** *"kill #2 (2019, P1 infeasible after a full UC) matches the MISO P1-seam defect UC-1-FIX-2 found:
yard-pinned coal clusters (ERCOT arms coal_fuel_inventory_plant_grain + monthly pile) were committed as integers, MECH 28
floored P1 at mlf·p̄·u, and the floors exceeded the year LP's pile/budget rows. The desk ruled option (a), folded into uc-1.2 at
e4a57362: a fully budget-pinned cluster carries no integer, so no MECH 28 floor. One relaunch of all seven legs on the uc-1.2
merge SHA; no second fix expected. The ERCOT 2020 gate shard at e4a57362 is running. The 52/140 no-load fallback coverage is a
separate parameter-coverage finding; I'm passing it to the engine lane."* → both kills are one engine release (uc-1.2); the
Addendum C pin is its merge SHA. **Structural note for the RESULT:** under uc-1.2 ERCOT's eleven yard-pinned coal clusters carry
no integer, so MECH 28 governs CC_REGULAR and ST_GAS only and the coal rows keep their incumbent floors (`coal_min_config`, the
`_mustrun` band) — §2 T4 (coal up under the UC) and §4 S2 (coal starts toward CEMS) are then read as "not reachable by this
arm" rather than as UC outcomes.

### Addendum B.3 (06:50Z) — 2021, 2022, 2023 hit the 193-minute budget inside the UC stage: the §5 risk realised

| year | P0 s | UC progress at the stop | measured MILP | stop |
|---|---|---|---|---|
| 2021 | 320 | > 9,780 s in UC, windows unknown (no per-window log until the stage ends) | — | budget; process left running, extended to 8 h total (until 10:53Z) for its wall row |
| 2022 | 494 | **120 of 365 windows** (Jan 1 → Apr 30) in 11,584 s | Σ 9,321 s; mean 77.7 / p50 61.6 / p95 227.6 / max 297.4 s; nodes p50/p95 **86 / 541**; gap p95 9.9e-4; 0 time-limit hits; warm incumbent 120/120 but `warm_feasible` **0/120**; 93 % of MILP time in the post-root tail; 30-window blocks 1,922 / 2,250 / 1,768 / 3,381 s | killed by the shard at budget; projected ≈ 28,000 s MILP for the year (3.5× the January extrapolation) |
| 2023 | 444 | ≈ 10,500 s in UC, unfinished | — | SIGINT at budget inside HiGHS `run()` |

**Reading.** The §5 budget rule extrapolated January 2020 (31 windows, p50 15.6 s) to the year; 2024 and 2025 fit it (Σ 6,482 /
6,660 s) and 2019's UC did too (6,257 s), but 2021–2023 run ≈ 3.5× slower per window, with the B&B tail (nodes p95 541 vs the
gate's 78) carrying 93 % of the time and the warm start rejected in every window (`warm_feasible` 0 — E3 does not help on
ERCOT's hard windows, the gate's own finding). A rolled 2022 year is ≈ 8 h of MILP on one core; the D-2 ratio for those years
projects to **≈ 30×** against the owner's 3× (a cost finding for the speedup lane, not a kill). **Budget for the Addendum C
relaunch (fixed now, from the measured 2022 rate): 2021, 2022, 2023 at ceil(1.3 × (494 + 28,400 + 455 + 10 % build) / 60) =
680 min; 2019, 2020, 2024, 2025 at 193 min** (their UC fits: 6,257 / ≈ 6,500 / 6,482 / 6,660 s). uc-1.2 removes the eleven
yard-pinned coal clusters from the integer set (72 → 61), which can only shorten the windows. None of the three legs produced a
bundle; 2022's partial UC log is quoted above (its checkpoints under `results/uc-checkpoints/` died with the container).

## Addendum C (pre-declared 06:55Z, before the uc-1.2 merge SHA exists) — the relaunch: staged, at the uc-1.2 pin

**UC-DESK ruling (06:49Z, verbatim):** *"Staged launch, pre-declared in Addendum C before any number: at the merge SHA launch
2019/2020/2024/2025 first, 193 min each. If a kill fires on those four (kill #1 or #2, or kill #3 on ≥1 real control flip under
your PRECOMMIT's flip rule), the verdict is R and 2021–2023 are not launched; record them as 'not run: verdict reached' (rule 16
doesn't bite, since nothing is registered). If no kill fires, launch 2021–2023 at 680 min. Reason: the 3× ruling governs arming,
not A/B runs, but 24 core-hours on years that can't change an R is waste."*

Fixed now, before any number:

1. **Pin:** the uc-1.2 merge SHA on `main`, `<<PIN_C>>`, filled in by the lane the minute UC-DESK sends it, with the same
   G-DRIFT check as Addendum A (the `src/` diff from `dc3860be` must be the uc-1.2 release and nothing else on the ERCOT solve
   path; anything else is classified before launch).
2. **Stage 1:** 2019, 2020, 2024, 2025 at 193 min each, the same two-field arm, prompts regenerated at the pin with the lane
   addenda. Each leg is fetched, verified (five artifacts) and checked out before its shard is archived.
3. **Stage-1 gate:** kill #1 (an infeasible window / no incumbent), kill #2 (the P1 LP infeasible after the UC), or **kill #3 — a
   §3 control flip** read on the four legs' own `calibration_verdict.py` rows against the keeper's (a PASS → FAIL on any
   registered criterion, class row, year, excluding the attestation artefacts named in §8). Any one ⇒ **verdict R**, 2021–2023
   recorded as *not run: verdict reached*, RESULT written on the four legs.
4. **Stage 2:** no kill on stage 1 ⇒ 2021, 2022, 2023 at 680 min each (Addendum B.3), then the seven-leg composition, the
   verdict and the RESULT as §8 says.
5. Readings (§2), bars, kills (§7), the budget rule's measured replacement (B.3) and the composition workaround (§8) do not move.
   The `dc3860be` legs (2024, 2025 complete; 2022's partial UC log) stay evidence, never scored.

**2021 update (06:50Z):** the leg is lost — the shard's container was recycled while the session sat idle after its 06:06Z
budget report (fresh boot, process gone, not an OOM: RSS 8.2 of 13.4 GiB), so the extension bought nothing; UC had run > 9,780 s
unfinished; nothing pushed; archived. Two harness lessons written into the Addendum C prompts: a shard with a multi-hour solve
keeps its session active (a re-armed Monitor) until the process exits, and the per-window log line stays a routed engine ask.

## Addendum D (2026-10-10, written before any stage-1 shard exists) — `<<PIN_C>>` filled: the uc-1.2 pin, G-DRIFT, stage-1 budgets

Lane relaunched by **UC-2-ERCOT-R2** (Opus; this session takes over from the Fable session, which hit the weekly limit).
Branch `claude/ucmilp-2-ercot-ab-e4w1`, `origin/main` merged in (merge, not rebase).

**Pin (Addendum C item 1).** **PIN_C = `eab17188c75cd0332f9323ed3464c62bc0cd1848`** (`main`, merge of PR #7230,
UC-1-FIX-2). It carries uc-1.2 (desk ruling (a), `e4a57362`: a fully budget-pinned cluster carries no integer — ERCOT
72 → 61 integer clusters of 141), the slim-window NaN fix (`7688a68a`: unbounded merged members filled last), the per-window
INFO log line, and UC-1-FIX-3 (#7229: uc-params keyed by EIA plant code via the CAMD↔EIA crosswalk; Kiamichi OK 55501 read
as an ERCOT facility; Hidalgo and Arthur von Rosenberg now joined). **Gate on record** (FINDING-ucmilp-fix2-floor-mindown
§5, at PR head `7688a68a`, whose `src/` equals the pin's): ERCOT 2020 end-to-end 365/365 Optimal (w118 Optimal, 35.9 s,
65 nodes), 0 time-limit hits, P1 solved with 0 unserved and 0 NaN cells, pass-1 and pass-2 `u`/`v`/`w` identical on hours
0–8015, wall ≈ 249 min (UC 6,994 + 7,030 s; P1 244 + 229 s).

**G-DRIFT `dc3860be` → `eab17188` (zero LP; rule 29(b)).** 300 files change; 284 are `tests/` and `docs/` (records,
findings, the slim span of other lanes). The 16 others, every hunk classified:

| file | hunk | control (keeper recipe, gate off) | arm |
|---|---|---|---|
| `model/uc/{window,slim,solve,diagnose,params}.py`, `pipeline/uc.py` | uc-1.2 guard on the window's pinned fleet (⌈floor/(p̄·a)⌉), all-budget-pinned clusters demoted from the integer set, slim expand NaN fix, per-window INFO log, diagnosis text | **INERT**: imported only under `if getattr(config, "unit_commitment_milp", False)` (`pipeline/solve.py:675`) | LIVE (intended: the release) |
| `config/scenarios.py` | new field `uc_slim_window: bool = True` + its `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` / `TIER_TAGS` entries | **INERT**: born at its registered default, dropped from `cache_key()` there; read only inside the UC stage; absent from the keeper's `run_config_<y>.json` | LIVE at default (`True`, the slim path the gate validated) — not a `--set`, not swept |
| `data/campd_crosswalk.py` | `crosswalk_of_record()` refactored onto `load_crosswalk(paths)` (same canonical paths); new `camd_to_eia_plant()` | **INERT**: no caller on the solve path (`grep`: only `scripts/lib/uc_params`); `crosswalk_of_record` is the audit helper, unchanged in output | LIVE through uc-params only |
| `scripts/lib/uc_params/{__init__,ercot}.py`, `data/dictionary/schema/uc-params.schema.yaml`, `data-dictionary.md`, `scripts/lib/clean_profiles.py` | FIX-3: plants keyed by EIA plant code; `extra_facilities` (Kiamichi); two raw inputs added to the `uc-params` clean source | **INERT**: `data/clean/uc-params` is consumed only by `model/uc/params.py` behind the gate | LIVE (intended: measured no-load / mlf / UT / DT for Hidalgo, AvR, Kiamichi replace class-mean fallback) |
| `scripts/lib/uc_bench.py`, `scripts/diagnostics/bench_uc_ladder.py` | bench harness | not on the solve path | not on the solve path |
| `CHANGELOG.md` | prose | — | — |

No `constants.py`, `iso_configs.py`, `model/lp/*`, `data/fleet/*` or orchestrator hunk. **Control INERT**: the keeper's
committed bundle remains the control (rule 29(b)); no control solve. The arm differs from Addendum A's only by the uc-1.2
release and FIX-3 parameters, which is the purpose of the relaunch; the arm's recipe delta stays the two `--set` fields.

**Shards (Addendum C items 2–4; the per-shard numbers below replace Addendum C's 193 min for stage 1, per UC-DESK's
relaunch instruction).**

| stage | years | budget per shard | why |
|---|---|---|---|
| 1 | 2019, 2020, 2024, 2025 | **300 min** | the measured gate wall (≈ 249 min for 2020, both passes running the UC) × 1.2; Addendum C's 193 min predates the two-pass finding and would stop a green 2020 |
| 2 (only if no kill on stage 1) | 2021, 2022, 2023 | **680 min** | Addendum B.3, unchanged |

Out-dirs `results/calibration/ucmilp_ercot_d_<y>`, branches `claude/ucmilp-ercot-d-<y>` (new names: the `dc3860be` legs on
`claude/ucmilp-ercot-<y>` stay evidence, never scored, never overwritten). Prompts: `shard-prompts-ucmilp-ercot-d.txt`
(`shard_prompt.py` at the pin + lane addenda). New in the addenda: the solve runs **detached** (`nohup … &`, log under
`/tmp`, a re-armed Monitor until `EXIT`) because the shard tool kills a foreground process at 120 min, and the session stays
active until the process exits (the 2021 container-recycle lesson); `hourly/unit_hourly_<y>.parquet` is unstaged before the
commit (rule 15). Readings (§2), bars, kills (§7), the stage-1 gate (Addendum C item 3) and the composition workaround (§8)
do not move.

**D.1 — stage 1 launched 14:14Z at `eab17188`** (model Opus, tag `ucmilp:UC-2-ERCOT-shard`): 2019 `session_01FqeWwxWUjaiV3F7i278YM6`,
2020 `session_01FpPuQW4mMNburhWVsD9L8X`, 2024 `session_016FDZqY7NXFW6Y88oXt4gqm`, 2025 `session_01SDmBkrN2ghak9yPgQeoyFE`;
300 min each; branches `claude/ucmilp-ercot-d-<y>`.

**D.2 (15:05Z, before any leg finishes) — budgets extended.** At 15:00Z the pace on pass 1 was: 2019 ~0.9 min/window
(projected ≈ 11 h with both UC passes), 2020 ~33 s/window (≈ 7 h), 2024 ~18 s/window (≈ 4 h, fits), 2025 not yet read.
**UC-DESK (15:01Z, verbatim):** *"approved. Extend 2019 and 2020 to 720 min and record it as Addendum D.2 before any leg
finishes. A budget is a cost line, not a reading. Extend 2025 too if its pace projects over 300 min, under the same addendum.
In the RESULT, report the wall rows including the double-UC cost (pass 2 identical to pass 1 per the FIX-2 FINDING)."*
→ 2019 and 2020 run to **720 min**. 2025 runs to 720 min if its shard projects over 300 min. 2024 stays at 300 min.
Readings, bars and kills do not move.
