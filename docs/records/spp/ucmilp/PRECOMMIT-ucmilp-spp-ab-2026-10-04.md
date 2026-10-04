# PRECOMMIT — UC-2-SPP: pre-registered A/B of the MILP unit-commitment stage on every SPP backcast year, 2026-10-04

**Written and pushed BEFORE any shard exists.** Every reading, bar, kill and budget below is fixed here and
fails closed; nothing is moved after a number comes in (GATESPEC §7.1, rule 1(c) by analogy). Lane
`UC-2-SPP` (session `session_01QBeFQCYTmVafRpi7Ujb9gs`, Fable), branch `claude/ucmilp-2-spp-ab-r7qd` off
`origin/main` `d62ae1a7`. Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on the owner's instruction
*"I want tests on backcast years to see if it improves calibration."* Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md`
§5–§7; plan `docs/uc-milp-program-plan-2026-10.md` §3 (UC-2), §5, §8.1 (R3–R6).

## 0. Preconditions (checked before this file was written)

| check | result |
|---|---|
| `git show 6d47c762:src/market_sim/config/scenarios.py \| grep -c unit_commitment_milp` ≥ 1 | **6** |
| the SPP keeper's `run_config.json` arms nothing in `UC_REFUSED_ALWAYS` (15 fields) | every refused field reads `False` — **0 armed** |
| the keeper bundle is identical at the engine SHA and at `origin/main` (`git diff 6d47c762 origin/main -- results/calibration/closeout_spp_nuc_span`) | **0 files differ** (only `frontend/data/backcast/keepers/SPP.json` gained the signed frontier rows) |
| SPP golden replay at `ec758d64` (UC-1, gate off) | **PASSED exactly** (plan §11, r03) → arm-vs-control deltas are UC-only |

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** SPP's designated keeper `2026-10-03-closeout-spp-nuc-keeper`, bundle
  `results/calibration/closeout_spp_nuc_span`, seven year-isolated legs 2019–2025 solved at
  `8c3ea46192074cfd422fff6532acc035d37297bb`; its committed `metrics.json`, `legitimacy_diagnostics.json`,
  `hourly/*` and the status part `frontend/data/backcast/status/SPP.js` are the control readings.
- **Pin (every shard):** the ENGINE BRANCH SHA `6d47c762d575b6666da6373ba17a3e93ab477f66`
  (`claude/ucmilp-1-engine-mcst`, not yet merged; owner ruling R6, plan §8.1). `source_revision` is this
  full SHA, never a branch.
- **Arm — ONE logical delta:** `replay_keeper.py results/calibration/closeout_spp_nuc_span --years <y>
  --set unit_commitment_milp=true`. Every `uc_*` field stays at its declared default and is **never swept**:

  | field | value | source |
  |---|---|---|
  | `unit_commitment_milp` | `true` | the arm |
  | `uc_window_hours` / `uc_lookahead_hours` | 24 / 12 | DESIGN §3 (plan E2) |
  | `uc_mip_rel_gap` | 1e-3 | DESIGN §3 (plan E4) |
  | `uc_window_time_limit_s` | **600** | DESIGN §3 declared placeholder (D-2 unruled; R3 in DESIGN §8) |
  | `uc_integer_scope` / `uc_noload_source` / `uc_boundary_mode` | `physics` / `campd_regression` / `p0_targets` | DESIGN §1.1, §1.2, §2.2 |
  | `uc_prefixing` | `false` | DESIGN §2.3 (E5 unproven) |

- **Rule-19 substitutions (owner ruling R5, D-5 SPP, verbatim "Keep both floors (Recommended)"):**
  `coal_mustrun_per_plant` and `st_gas_mustrun_per_plant` STAY armed exactly as the keeper arms them. Nothing
  else is switched off: the keeper arms no bridge and no posture (precondition row 2), so the validator refuses
  nothing. The UC respects both floors as inputs (DESIGN §5 "not refused"); D-2 attributes each under its own id
  and the UC schedule under MECH 28.
- **Pricing (owner ruling R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC
  objective; make-whole reported in `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (owner ruling R4, D-4):** UC min-load energy is REPORTED under MECH 28 and not budgeted.
- **Not a matrix re-test (rule 28).** `spp_commitment_posture` reads **R** (SPP-102/103) and `online_capacity_envelope`
  **U/R-adjacent** (SPP-83); `gas_commitment_bridge` / `spp_gas_commitment_bridge` read **R** and are on the
  §5.7 DO-NOT-REDO list. None is re-tested here: the integer commitment state is a different object from the
  relaxed posture and from a P0-detected bridge (plan §6, GATESPEC §5 "integer state is the new evidence").
  The cell this lane feeds is `unit_commitment_milp` (minted `U` by UC-1 in every shard); the desk stamps
  SPP's cell from the RESULT after the engine PR merges. DO-NOT-REDO honoured: no curtailment ceiling, no gas
  bridge, no offer-band retune, no second `--set`.
- **DOF (rule 21):** zero free parameters added. Every UC parameter is measured or published (UC-0 FINDING §5;
  no-load = CAMPD per-unit intercept × delivered fuel, 141/165 SPP units fitted, class-mean-per-MW fallback
  share reported from `uc_solve_log_<y>.json clusters[].src`). The keeper's authorized price tuning
  (`offer_curve_by_group` all bands 0.93) rides unchanged.

## 2. Target readings (fixed ex ante; bar = half the distance to the gate band, the closeout convention)

Control values are the keeper's registered records (status part, rubric 3.18). "met" is decided on the
composed span's `calibration_verdict.py` output and the zero-LP re-measurement of UC-0's M1/M3/M4 on the
arm bundle (`scripts/probes/_ucmilp_benefit_screen.py::screen_year`, imported, pointed at
`results/calibration/ucmilp_spp_span` — same conventions as the board).

| # | reading | control | sign expected | bar (met iff) |
|---|---|---|---|---|
| T1 | SPP 2020 C3a mean LMP (model/actual − 1) | **+27.7 %** FAIL (band ±10 %) | negative (body down) | arm ≤ **+18.85 %** (moves ≥ 8.85 pts) |
| T2 | SPP 2019 C3a | **+12.3 %** FAIL | negative | arm ≤ **+11.15 %** (moves ≥ 1.15 pts) |
| T3 | SPP 2020 C3b NRMSE | **0.345** FAIL (≤ 0.20) | down | arm ≤ **0.2725** |
| T4 | low-price-hour count ratio model/actual, hours ≤ $15 and < $0 (M3), 2019 and 2020 | 2019: 0.025 / 0.04 · 2020: 0.15 / 0.11 | both ratios rise toward 1 in both years | sign only; magnitude reported |
| T5 | M4 reserve dormancy (share of hours with model reserve MCP < $1) vs actual, 2019 and 2020 | model 1.00 vs actual 0.09 / 0.08 (mean MCP model $0 vs actual $5.18 / $5.46) | dormancy share falls; mean MCP rises | sign only; magnitude reported |

**Expected cost, declared, not a kill (UC-0 F2):** SPP 2024 C3a is model-LOW (**−11.2 %**, FAIL) and its C3b
is 0.216 (FAIL). A trough fix lowers the body, so 2024 C3a is expected to move further from the band. It is
reported as a cost, with its C3b direction, and does not by itself decide the verdict (FAIL → FAIL is not a flip).

## 3. Control readings (fixed; a breach is a kill, §6)

**No PASS → FAIL flip on any registered SPP year, any criterion, any class row** (`calibration_verdict.py`
per-(criterion, key, year) status diff vs the keeper). A CAVEAT → FAIL on C3c is a downgrade and counts as a flip.
The years with the least headroom, named now so the reading cannot be re-interpreted later:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| 2021 | C3a | +7.1 % PASS | 2.9 pts | body down helps |
| 2022 | C3a | −4.8 % PASS | 5.2 pts | model-low: a trough fix moves it toward the edge |
| 2023 | C3a | −6.4 % PASS | 3.6 pts | model-low, train tier |
| 2025 | C3a | −4.3 % PASS | 5.7 pts | model-low, train tier |
| 2019 | C3b | 0.160 PASS | 0.040 | shape may re-order |
| 2021–2025 | C3b | 0.176 / 0.175 / 0.176 / —(2024 FAIL) / 0.153 PASS | 0.024–0.047 | shape |
| 2019–2020, 2023–2025 | C1 CC_REGULAR | +2.25 / +1.60 / −4.49 / −5.80 / −7.86 TWh PASS (±8 TWh, ±3 pp) | 2025: 0.14 TWh | CC energy may fall with fewer in-merit CC hours |
| 2019–2022 | C3c | CAVEAT (model 0 h / 372 h > $200) | — | CAVEAT → FAIL is a flip |
| every year | C8 forced share | PASS (ST_GAS 15.7–33.8 %; 2022 grounded conditional) | — | MECH 28 is reported, not budgeted (R4), so C8 cannot move through the UC share; a change through `st_gas_mustrun_per_plant` composition is reported |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper; no new D-4 FAIL row.

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, COAL_PRB, COAL_LIGNITE, ST_GAS) and ISO-wide | 0 (no UC) | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 |
| S2 | starts per plant-year vs CEMS (UC-0 M1, same on-threshold 1 % of available cap) | 2019 CC 2,073 vs 1,211 · 2020 2,385 vs 1,397 · 2021 3,284 vs 1,728 · 2022 3,847 vs 1,693 · 2023 2,876 vs 1,712 · 2024 2,810 vs 1,432 · 2025 2,849 vs 1,651; COAL_PRB 77–285 vs 259–372 (model under-cycles); ST_GAS 440–868 vs 796–1,351 | `screen_year` M1 on the arm; also `uc_schedule_<y>.parquet` Σ`v` per cluster as the engine's own count. Sign expected: CC starts down toward CEMS; coal/ST_GAS starts reported |
| S3 | online capacity vs the SPP portal `hourly-generation-capacity-by-fuel-type` series | SPP-83: keeper +6.9 to +8.9 GW over SPP online thermal on sampled hours | **comparator NOT on disk** (the SPP-82/83 zips were ad hoc downloads; `data/raw` carries none). Reading SKIPPED and named; the arm's `online_mw` from `uc_schedule_<y>.parquet` is reported against the keeper's available MW instead (model-internal, not a measured comparator) |
| S4 | integer set and fallback shares | UC-0 M6: 86 SPP plant clusters, 38.2 GW; no-load fitted 141/165 | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |

## 5. Cost readings (reported; D-2 is UNRULED — ratios are reported, never judged here)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all seven years |
| W1-denominator | SPP has no row in `wallclock-baseline-2026-07.md` §3a and the keeper bundle records no P0/P1 seconds; the only on-record SPP LP wall is FINDING-spp-40 (2024, older recipe): P0 78.7 s + P1 23.3 s. **Declared proxy:** baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line (P0 is the unchanged LP; P1 differs only by bounds), so ratio = total / (P0 + P1) in one container | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` (all cluster-days) ÷ Σ_t λ_P1 × load (ISO wholesale energy cost from `hourly/system_<y>.parquet`) | ≤ **2 %** (sanity) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise §6 kill) |

**Shard budget:** the keeper's own wall is not recorded in its bundle → SPP baseline year = **30 min** (the
declared fallback; the SPP-107 recipe's shards ran 8–11 min wall end to end, so 30 is conservative). Budget per
shard = ceil(3 × 30 + 30) = **120 min**. One shard commit ≤ 20 min of runtime (rule 32); a shard approaching the
budget with no artifact stops and reports.

## 6. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"):
   an engine defect, routed to UC-DESK / UC-1-FINISH, never a tuning invitation.
2. **A non-deterministic schedule:** the schedule hash of `uc_schedule_<y>.parquet` differs between two completed
   runs of the same recipe-year. With one shard per year this is exercised only if a relaunched shard (PENDING
   > 45 min rule) and its predecessor both complete; otherwise recorded "not exercised".
3. **A control flip** (§3) in any registered year.

## 7. Verdict rule (fixed) and the D-6 card

- **K candidate** — T1, T2 and T3 met, T4/T5 signs right, no kill, every leg Optimal: recommend the owner's D-6
  card read "promote on structure"; the lane never promotes (rule 31; UC-4 is the desk's slot).
- **R** — any target reading moves the wrong way past its control (C3a 2019 or 2020 up, C3b 2020 up), or any
  kill fires.
- **I** — no kill, no wrong-sign move, but |Δ| below the bar on T1–T3 (GATESPEC §7.2: "the relaxation was already
  tight here" is a finding).
- Mixed (e.g. T1 met, T2 not): the verdict is the worst of the three target rows, stated row by row; the 2024 cost
  is reported beside it. The determination (`iso_determination`) is reported, not gating: SPP is NOT-YET on the
  keeper's open rows and stays so unless every failing row clears, which no reading here predicts.
- The RESULT carries the D-6 card text verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve plan (rules 16, 32–36)

- **Seven shards, 2019–2025**, one year each, `claude/ucmilp-spp-<y>`, out-dir `results/calibration/ucmilp_spp_<y>`,
  prompts from `scripts/shard_prompt.py --iso SPP --all-years --sha 6d47c762d575b6666da6373ba17a3e93ab477f66
  --lane ucmilp-spp --bundle results/calibration/closeout_spp_nuc_span --set unit_commitment_milp=true --budget 120
  --note "ucmilp-spp: UC A/B"` (the script is byte-identical at the pin and on `main`), each appended with: confirm
  `hourly/uc_schedule_<y>.parquet`, `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json` and
  `hourly/unit_marginal_<y>.parquet` are in the pushed tree; report the GATESPEC §6.1 wall row (the
  `log_year_phase_timing` line + `uc_solve_log_<y>.json summary`). Committed as `shard-prompts-ucmilp-spp.txt`.
  `create_session` per year: `source_revision` = the pin, model `claude-opus-5-5`, tag `ucmilp:UC-2-SPP-shard`.
  PENDING > 45 min: archive and relaunch.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_spp_<y>` non-empty; check out;
  verify `dispatch/<y>_P1.parquet` + the three UC files; THEN `archive_session` (rule 33).
- **Compose and score, zero LP, at the pin:** `scripts/probes/_ucmilp_compose_span.py --iso SPP --leg <y>=ucmilp_spp_<y> …
  --out results/calibration/ucmilp_spp_span` (regenerates `legitimacy_diagnostics.json`, never copies it);
  `calibration_verdict.py results/calibration/ucmilp_spp_span`; `legitimacy_diagnostics.py`; the M1/M3/M4
  re-measurement. The parent runs no LP.
- **Register as a PROBE:** `dashboard_add_run.py --label "ucmilp-spp UC A/B (PROBE)" --no-prune`. Never promote;
  never delete a bundle (rule 31). One PR.
- **Exit:** RESULT beside this file (`RESULT-ucmilp-spp-ab-<date>.md`: gate table first, wall rows, every reading
  answered, kills checked, verdict, D-6 card, where each bundle is and what a promotion costs, `## Log entry`);
  message UC-DESK with the gate table, the wall rows, then the promotion question.

## 9. DO NOT REDO

Everything in `docs/mechanism-testing-matrix.md` §5.7's DO-NOT-REDO (curtailment ceiling, gas bridge, offer-band
retunes); `spp_commitment_posture` (R) is not re-run in any form; no `uc_*` value other than the declared defaults;
no second `--set`; no control solve; no NEISO/NYISO span (those belong to the UC-2 control lanes, not this one).
