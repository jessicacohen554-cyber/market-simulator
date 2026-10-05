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

## Addendum A (2026-10-04 21:55Z, before any number exists) — STOP on an engine defect at the pin; relaunch rule

All seven shards (launched 21:29Z at `6d47c762`; sessions `session_01Y27spXDj2YyEtEGwPS4M7e` 2019,
`session_01LNdYgisFGFddimKkCtgUm6` 2020, `session_014vfQ7ZmDu8GBDghRDCZniH` 2021, `session_01XtGth8hnAAQSu32eoHtqHX` 2022,
`session_01HHz1ioHN63RzNcKxegtdK8` 2023, `session_01EU1SBoX87EWLiiaaCfYbYM` 2024, `session_01UT7Fiv8NtLUGvbCK4eLhoF` 2025)
crashed identically 4–5 min into the solve, after P0 (82–231 s) and the January UC windows:

```
src/market_sim/pipeline/uc.py:363, in UcStage.run
    sched.checkpoint(self.artifact_dir, next_month, self._log(windows, sched, partial=True))
AttributeError: 'UcStage' object has no attribute 'artifact_dir'
```

Verified against the source at the pin: `UcStage.__init__` sets `self.checkpoint_dir` (uc.py:206) and nothing assigns
`artifact_dir`; line 363 is its only reference; it fires on the first month-end checkpoint with `write=True` (the default),
so every ISO-year with the gate on dies there. The gate-off goldens cannot see it. UC stage census before the crash:
218–226 clusters, 83–86 integer, 384 fleet rows (2023: 218/86; 2024: 221/83; 2019: 226). The 2024 shard's container
preflight warning (13.36 GiB + 5 GiB swap = 18.4 GiB < 24 GiB target, naming MISO/PJM) is a warning only, not the cause.

- **Classification:** GATESPEC §5 engine-defect route (not an infeasible window, not non-determinism, not a control flip).
  No kill fired; no number exists; nothing is tuned. Routed 21:55Z to UC-1-FINISH (`session_01CghV9pMqkD5TDmYicDuMCx`,
  owner of `claude/ucmilp-1-engine-mcst`) and to UC-DESK. This lane does not edit `src/`.
- **Shards:** each stopped per its hard stops and pushed nothing (no `claude/ucmilp-spp-*` branch exists); all seven
  archived 21:55Z (rule 33: nothing to fetch).
- **Relaunch rule (fixed now):** when the engine branch carries the fix, the pin moves to that full SHA and NOTHING else
  changes — same recipe, same single `--set`, same `uc_*` defaults, same readings, bars, kills and budget as §§1–7; the
  new pin and the `grep -c unit_commitment_milp` / tooling-unchanged checks are recorded in Addendum B before the
  relaunch. Arm-vs-control deltas remain UC-only only if the SPP golden still reproduces at the new pin; if the fix
  commit touches anything outside the UC stage (`model/uc/`, `pipeline/uc.py`, their tests), the addendum says so and
  the desk decides whether a golden re-check is needed before the A/B is scored.

## Addendum B (2026-10-04 22:15Z, before any number exists) — the relaunch pin, ruled

**Pin for the relaunch: `c8690022bf5024d5fee469abc2663b1c61a3ee49`** (`claude/ucmilp-1-engine-mcst`, PR #7194, rebased onto
`origin/main` `d62ae1a7`; owner-desk ruling UC-DESK 22:10Z, verbatim: *"ruling — option (1), relaunch now, at
c8690022bf5024d5fee469abc2663b1c61a3ee49, NOT 6c530a58 … Your zero-LP G-DRIFT is accepted as the evidence; no SPP
re-golden"*). Readings (§2), control rule (§3), structure and cost readings (§4–§5), kills (§6), verdict rule (§7),
`uc_*` defaults (§1) and the 120-min budget are UNCHANGED. The pin is the only change.

**What moved between the pins (zero LP, verified on the objects):**

| content | files | SPP classification |
|---|---|---|
| the Addendum A fix | `src/market_sim/pipeline/uc.py:363` `self.artifact_dir` → `self.checkpoint_dir` (one token; `artifact_dir` now has 0 references) | LIVE on the gate-on path, the fix itself |
| gate-on tests | `tests/unit/model/uc/test_stage_pipeline.py` (+27, then +29/−8: two month-ends crossed with checkpoints on, three sidecars), `tests/unit/model/uc/test_window_captured.py` (+34) | tests, not solve path |
| shard hygiene | `.gitignore` +4: `results/uc-checkpoints/` (the E9 scratch checkpoints, so a shard's `git status --short` proof stays clean) | not solve path |
| two FINDINGs | `docs/records/governance/uc-milp-2026-10/FINDING-ucmilp-golden-{miso-recipe-gap,nwpp-pjm-zero-lp}-2026-10-04.md` | docs |
| **main's advance** `e8570532..d62ae1a7` carried in by the rebase (155 files) | `440ad144` NWPP-NEXT-27 `nwpp_path76_served_schedule` (`scenarios.py`, `runner.py`, `run_calibration*.py`, `pipeline/ttc.py`, `data/eia930/{demand,envelopes}.py`); `90cea720` closeout-PJM-elliott `pjm_elliott_measured_outage_overlay` (`scenarios.py`, `data/fleet/arrays.py`, new `data/pjm_elliott_outages.py`, `run_calibration_full.py`); desk/registry/frontier docs and the matrix anchor-digit repairs | **INERT for SPP**: (a) both fields default `False` at the pin (`scenarios.py:21933`, `:15219`); (b) ISO-gated in code (`arrays.py` `_iso == "PJM"`, `ttc.py` `iso == "NWPP"`, the NWPP served-schedule path in `demand.py`/`envelopes.py`); (c) armed nowhere — no `iso_configs` override, ABSENT from the SPP keeper's `run_config.json`, so dropped from `cache_key()` at default |

- `scripts/solve_surface_register.py --diff`: `6d47c762 → 6c530a58`, `d62ae1a7 → 6c530a58` and `d62ae1a7 → c8690022` all read
  *"341 → 341 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*.
- `scripts/shard_prompt.py`, `calibration_verdict.py`, `legitimacy_diagnostics.py`, `replay_keeper.py`, `dashboard_add_run.py`,
  `results/calibration/closeout_spp_nuc_span/**` and `frontend/data/backcast/keepers/SPP.json` are byte-identical between
  the pin and `origin/main` `d62ae1a7`; `scripts/probes/_ucmilp_compose_span.py` is present at the pin;
  `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` = 6.
- The control is therefore unchanged (main's keeper bundle, rule 29(b)); the SPP golden stands on `ec758d64` as before and
  the desk ruled no re-golden. Prompts regenerated with `--sha c8690022…` and re-committed as
  `shard-prompts-ucmilp-spp.txt` (the 6d47c762 prompts stay in history at `b2167930`).

## Addendum C (2026-10-05 00:35Z, before any number exists) — the third pin, after the window-infeasibility fix

**Pin for the relaunch: `ae224fafdda926bf8817afee385bd6cedc470120`** = `origin/main` at the merge of PR #7201 (lane UC-1-FIX,
engine uc-1.1), ruled by UC-DESK 00:22Z: *"the fix is merged. Pin = main ae224faf… Relaunch now under the Addendum A rule."*
Readings (§2), control rule (§3), structure and cost readings (§4–§5), kills (§6), verdict rule (§7), `uc_*` defaults (§1) and
the 120-min budget are UNCHANGED. A second infeasible window is kill #1 again: record and stop.

**The defect this pin fixes** (RESULT §1, step 3; `FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04.md`): at `c8690022` every SPP
year raised `UcWindowInfeasible` (no feasible incumbent). Root cause per the FINDING, proved on real data: the carried min-up /
min-down history was enforced as a separate `u` column bound while the in-window Rajan–Takriti rows summed only the window's own
starts/stops, so the kept history could accumulate more starts within one min-up than the plant has units; the next window's carried
bound exceeded `n`, the bound repair lifted `u` above `n`, and `w + u ≤ n` became contradictory (windows 156/284 in the desk's
summary). This lane's first lead (the floor-derived `u` bound vs the P0 feasibility clip) is **refuted** by the FINDING §2 (zero
contradicting cluster-hours). Fix: the history enters the Rajan–Takriti rows as RHS constants, plus a look-ahead min-down guard;
no slack, no penalty, no tolerance. L1 proof in a shard: SPP 2020 window 0 Optimal, 4.2 s, gap 5e-9.

**What moved `c8690022 → ae224faf`, classified for SPP (zero LP, on the objects):**

| content | files | SPP classification |
|---|---|---|
| the UC fix (PR #7201) | `model/uc/{window,solve,params}.py`, new `model/uc/diagnose.py`, `pipeline/uc.py` (+818/−49 across UC files), `tests/unit/model/uc/test_window_carry_rows.py` | LIVE on the gate-on path — the fix itself and its diagnostics; the arm's only live change |
| engine PR #7194 merged (`681b71cf`) | the engine files already at `c8690022`; `floor_mechanisms.py` MECH 28; the gated hunk in `pipeline/solve.py`, drains in `runner.py` / `run_calibration_full.py` | gate-on path, unchanged from Addendum B |
| closeout-PJM-w3 (#7193, `41a9e2d9`, `bc163dbc`, `007ace12`) | `nuclear_winter_capability_basis: bool = False`; `data/fleet/arrays.py` `_apply_nuclear_winter_basis` under `_iso == "PJM" and config.nuclear_winter_capability_basis and mode == "backcast"`; `constants.NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR` (PJM key only) | **INERT**: default off, PJM-gated, ABSENT from the SPP recipe, unarmed in `iso_configs` |
| closeout-ERCOT-w3 (#7197, `9d06ad03`) | `coal_perplant_cliff_split: bool = False`; `data/fleet/assembly.py` `_coal_cliff_split_frac` under `getattr(config, "iso") == "ERCOT"` and the flag; `legacy_bins.py` helper | **INERT**: default off, ERCOT-gated, ABSENT, unarmed |
| closeout-MISO-w3 (#7198) | `miso_seam_neighbour_hourly_full_span: bool = False`; `model/interchange/spec.py` +97 — `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_FULL_SPAN_BY_YEAR` and `…_SPP_FULL_SPAN_BY_YEAR` tables (MISO's seam ladder; the `"SPP"` keys are MISO's neighbour, read only by `model/interchange/miso.py` under the flag); `run_calibration.py` rule-19 refusal | **INERT**: default off, consumed only by the MISO interchange path, ABSENT, unarmed |
| closeout-SOCO-w3 (#7196/#7199/#7200) | `diagnostic_coal_metered_online_floor: bool = False` (never promotable, rule 13); `data/coal_metered_online.py` (new); `pipeline/commitment.py` `wrap_coal_metered_online_diagnostic_prep` (returns the prep unchanged when off); `pipeline/year.py` + `run_calibration_full.py` wrap calls; `floor_mechanisms.py` MECH 29; `legitimacy_diagnostics.py` +8 (a D-4 window row for MECH 29 only) | **INERT**: default off, the wrap is an identity when off, ABSENT, unarmed; the scorer change adds a window for an id this run never emits |
| closeout-SPP-w3 records (#7195) | `docs/records/spp/*`, `results/phase0/spp/*`, matrix shard text | docs and phase-0 JSON only |
| solve surface | `solve_surface_register.py --diff d62ae1a7 → ae224faf`: *"341 → 342 names; 0 value(s) moved, 1 added (`NUCLEAR_MONTHLY_CF_UNCLIPPED_BY_YEAR`, moves no key), 0 removed — NO VALUE MOVED"* | no ISO's key reached |
| tooling and control | `shard_prompt.py`, `calibration_verdict.py`, `replay_keeper.py`, `dashboard_add_run.py`, `iso_configs.py`, `results/calibration/closeout_spp_nuc_span/**`, `keepers/SPP.json` byte-identical to `d62ae1a7`; `_ucmilp_compose_span.py` present; `grep -c unit_commitment_milp scenarios.py` = 6; `artifact_dir` 0 references | control unchanged (rule 29(b)) |

Nothing is LIVE for SPP outside the UC stage. Prompts regenerated with `--sha ae224faf…` and re-committed as `shard-prompts-ucmilp-spp.txt`
(the `6d47c762` and `c8690022` prompts stay in history at `b2167930` and `c72748dc`).

## Addendum D (2026-10-05, after the legs landed; disclosure of two zero-LP composition deviations — no reading, bar or kill changed)

1. `scripts/probes/_ucmilp_compose_span.py` at the pin aborted: *"DISAGREE gas_price_override"* — the keeper records the gas price per year
   (`run_config_<y>.json`, 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52 $/MMBtu) and the keeper's own composer (`_closeoutsppnuc_compose_span.py`)
   declares `YEAR_INDEXED = {"weather_year", "gas_price_override"}`; the UC composer's `PER_YEAR_FIELDS` lists `gas_price` (None everywhere) but not
   `gas_price_override`. The legs carry exactly the keeper's per-year values. The lane ran a scratch copy of the composer with `gas_price_override` added to
   that set (no repo script edited; `scripts/` is not this lane's); everything else in the compose is the committed script's logic.
2. Registration (`dashboard_add_run.py`) needs the benchmark frames in `results/calibration/_shared/SPP/`, which a shard cannot push (gitignored sibling).
   `run_calibration_full.py --restore-shared-inputs` refused because the span's `meta.json` (copied from the 2019 leg) recorded one-year frame hashes. The
   keeper composer carries `_respan_shared_inputs` for exactly this (miso-267); the UC composer does not. The lane applied the keeper composer's function to
   the span's meta: the re-spanned hashes are the keeper's own (`campd-8b15fb193a60`, `eia923-ada99c7451fd`, `eia930-c3bec7e7b952`), so the arm is scored on
   the control's benchmark basis; restore then verified every frame against its recorded hash.
3. The probe carries no `calibration_attestation.json` (attestation is a promotion step), so C6 reads UNATTESTED and the rule-22 C3c ledger route is
   unavailable: C3c CAVEAT → FAIL in 2019–2022 is an artefact and is marked as such in the RESULT; the C3c magnitudes are compared directly.
4. Both composer gaps (per-year `gas_price_override`; the respan step) are routed to UC-DESK for the engine lane's composer.
