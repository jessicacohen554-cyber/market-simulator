# PRECOMMIT — UC-2-NEISO: pre-registered A/B of the MILP unit-commitment stage on every NEISO backcast year (calibrated control), 2026-10-10

**Written and pushed BEFORE any span shard exists and before the L1 bench has reported.** Every reading, bar, kill
and budget rule below is fixed here and fails closed; nothing moves after a number comes in (GATESPEC §7.1, rule 1(c) by
analogy). Lane `UC-2-NEISO` (session `session_01D9RZoc9NrNhUBJLcYxyJx4`, Fable), branch `claude/ucmilp-2-neiso-ab-n7c2`
off `origin/main` `2f872a62`. Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, 2026-10-10) under the owner's
direction *"launch shards for other ISOs to test"*. Protocol: `GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7;
plan `docs/uc-milp-program-plan-2026-10.md` §3 (UC-2), §8.1; precedent copied in structure:
`docs/records/spp/ucmilp/PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (+ Addenda A–D) and its RESULT (PR #7207).

NEISO is a **CALIBRATED CONTROL** (UC-0 FINDING: lower-tercile error +$9.9/MWh in 2023, C3a headroom −3.0 %). The
no-flip bar is the main reading; there is no fit to improve. Off the close-out plan §3.2 ("NEISO — closed; protect it")
by desk charter: a UC program A/B, not a calibration lever; nothing here can promote (rule 31; UC-4 is the desk's slot).

## 0. Preconditions (checked before this file was written, zero LP)

| check | result |
|---|---|
| `git rev-parse HEAD` == pin `2f872a62a7cccadb6800555c11a73745dcdb89a4` (main at the merge of PR #7218: engine uc-1.1 + UC-1-FIX + UC-SPEED `lean` preset) | yes |
| `grep -c unit_commitment_milp src/market_sim/config/scenarios.py` ≥ 1 | **6** |
| the NEISO keeper's `run_config.json` (`scenario_config`) arms nothing in `UC_REFUSED_ALWAYS` (15 fields) | every refused field reads `False` — **0 armed**; `UC_REFUSED_BY_RULING` is empty at the pin |
| the keeper recipe carries no `unit_commitment_milp` / `uc_*` field (born after the keeper; dropped from `cache_key()` at default) | confirmed |
| NEISO solve surface at the pin = the keeper's recorded surface | fingerprint **`b514541af339c180`, 213 rows, identical**; `moved` set identical (9 rows, same hashes) |
| `solve_surface_register.py --diff 306f2c00 → 2f872a62` (keeper basis → pin) | *"336 → 342 names; 3 moved, 6 added, 0 removed"*; moved rows re-key NYISO ×2, MISO/NWPP/PJM/SOCO/SPP ×1; **NEISO 0** |
| NEISO gate-off golden (UC-1, `ec758d64`, plan §11 r03) | **PASS** → every hunk up to `ec758d64` is byte-inert for NEISO |
| `scripts/probes/_ucmilp_compose_span.py` present at the pin; `shard_prompt.py --iso NEISO --all-years --bundle results/calibration/w0_neiso_span` emits 7 prompts | yes / yes |
| control re-scored at HEAD (`calibration_verdict.py results/calibration/w0_neiso_span`, rubric 3.20) | **CALIBRATED**, grade 8 scored / 7 target / 0 fails / 1 ledgered (C3c), every criterion status equal to the registered record; `check_bench_freshness --iso NEISO` reports all 7 NEISO bench parts **STALE** (payload fingerprint at HEAD `1b89b7110328`, part's unresolvable) — see §8(d) |

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** NEISO's designated keeper `2026-10-02-w0-neiso`, bundle
  `results/calibration/w0_neiso_span`, seven year-isolated legs 2019–2025 solved at `306f2c00` (closeout-B W0 phase 3);
  its committed `metrics.json`, `legitimacy_diagnostics.json`, `hourly/*`, the registered record (status part
  `frontend/data/backcast/status/NEISO.js`) and its zero-LP re-score at HEAD (§0) are the control readings.
- **Pin (every shard, bench included):** `2f872a62a7cccadb6800555c11a73745dcdb89a4`, full SHA, never a branch. Not chased.
- **Arm — ONE logical delta:** `replay_keeper.py results/calibration/w0_neiso_span --years <y> --set unit_commitment_milp=true`.
  Every `uc_*` field at its declared default, never swept:

  | field | value | source |
  |---|---|---|
  | `unit_commitment_milp` | `true` | the arm |
  | `uc_window_hours` / `uc_lookahead_hours` | 24 / 12 | DESIGN §3 (plan E2) |
  | `uc_mip_rel_gap` | 1e-3 | DESIGN §3 (plan E4) |
  | `uc_window_time_limit_s` | 600 | DESIGN §3 declared placeholder |
  | `uc_integer_scope` / `uc_noload_source` / `uc_boundary_mode` | `physics` / `campd_regression` / `p0_targets` | DESIGN §1.1, §1.2, §2.2 |
  | `uc_prefixing` | `false` | UC-SPEED FINDING §3: within gap but one-sided; default stays off |
  | `uc_solver_preset` | `lean` | registry default at the pin (UC-SPEED, paired gate PASS 62/62) |

- **D-5 for NEISO (desk-set under the owner's direction; owner may override):** arm = keeper recipe +
  `unit_commitment_milp=true` + OFF for every `UC_REFUSED_ALWAYS` field the keeper arms. The keeper arms **none** (§0), so
  **nothing is switched off and the delta is the single `--set`.** Every other floor is KEPT, mirroring SPP arm 1 (ruling R5),
  so results compare across ISOs.
- **Kept conduct / obligation floors, named (the SPP stacking risk):** SPP showed a kept conduct floor stacking with the UC
  (`st_gas_mustrun_per_plant` forced energy rose 1–1.2 TWh/yr; CC energy moved to coal; C8 and C1 flipped). NEISO's
  keeper arms, and the UC leaves armed: `reliability_floor` (D-2: CC_REGULAR 3.14 TWh over the span, 0.4–1.7 %/yr; CT_PEAKER
  0.40 TWh), `neiso_winter_fuel_mustrun` (`winter_fuelsec_mustrun`, COAL_BIT 0.027 TWh in 2020 only), `coal_mustrun_per_plant`
  (armed; binds no D-2 row in the control), `cc_committed_per_plant` / `cc_peaking_per_plant` (the measured per-plant committed
  and peaking tranches — bands, not floors; the UC zeroes the markup on its integer clusters, so these tranches' committed
  premium disappears from P1 bids wherever a cluster is integer), `nuclear_mustrun`, `chp_steam`, `hydro_ror_flat`
  (physical/contract, D2-exempt). The stacking channel to watch in NEISO is **CC_REGULAR ↔ CT_PEAKER / ST_GAS / CC_CHP**
  (coal is immaterial: < 2 % of load, C8 SKIPPED), and `reliability_floor` + UC min-load both flooring CC in the same hours
  (rule 19: reported under their own D-2 ids; the UC under MECH 28).
- **Pricing (ruling R3, D-3):** markup zeroed on integer clusters; start and no-load paid once in the UC objective;
  make-whole in `hourly/uc_uplift_<y>.parquet`, never in the LMP (rule 4 untouched).
- **Rule 20 (ruling R4, D-4):** UC min-load energy REPORTED under MECH 28, not budgeted. The scorer at this pin budgets
  `uc_schedule` energy in the D-2 share (SPP RESULT §1); C8 is therefore reported both as scored and recomputed with MECH 28
  removed, as the SPP RESULT did.
- **D-2 ceiling (owner ruling 2026-10-09, "Keep 3×; fund speedup"):** the wall ratio is **reported, not judged** here; UC-SPEED's
  L3 on SPP 2020 reads 7.10× at this preset, so > 3× is the expectation, not a kill.
- **Not a matrix re-test (rule 28).** The cell this lane feeds is `unit_commitment_milp` (NEISO shard reads `U`). Nothing on
  NEISO's DO-NOT-REDO lists is touched: no offer-band retune, no `neiso_dynamic_reserve_requirements` (R), no
  `dam_availability_rebasis` (R), no second `--set`, no control solve, no scarcity-physics arm (close-out §3.2 step 3 is
  another lane's).
- **DOF (rule 21):** zero free parameters added. UC parameters are measured or published (UC-0 FINDING §5; NEISO cluster
  physics in the screen: CC_REGULAR S $50/MW, UT 8 h, DT 6 h, mlf 0.52; ST_GAS $35, 24/8 h, 0.12; COAL_BIT $100, 36/16 h, 0.40);
  the no-load source share (`uc-params` vs class fallback) is reported from `uc_solve_log_<y>.json clusters[].src`. The keeper's
  authorized price tuning (the 0.9547 fossil level and the 88-scalar band surface) rides unchanged.

## 2. Target readings (a control ISO has no fit target; these are the UC-0 M3 / M4 directions, sign reported)

Control values are the UC-0 board's zero-LP measurements on the keeper (`results/phase0/xiso/_ucmilp_benefit_screen.json`,
NEISO rows); "met" is decided by re-running `scripts/probes/_ucmilp_benefit_screen.py::screen_year` (imported, same
conventions) on the composed arm bundle.

| # | reading | control (2019 · 2020 · 2021 · 2022 · 2023 · 2024 · 2025) | sign expected | bar |
|---|---|---|---|---|
| T1 | M3 lower-tercile mean error $/MWh (model − actual RT) | +10.6 · +6.7 · +11.2 · +25.9 · +9.9 · +10.2 · +15.9 | toward 0 (falls) | sign only, every year reported; magnitude reported |
| T2 | M3 count ratio model/actual of hours ≤ $15 | 0.35 · 0.02 · 0.006 · 0.00 · 0.43 · 0.00 · 0.00 | rises toward 1 | sign only |
| T3 | M3 count ratio of hours < $0 | 0.00 · 0.00 · 0.03 · 0.00 · 0.00 · 0.00 · 0.00 | rises toward 1 | sign only |
| T4 | M4 reserve dormancy | **n/a** — NEISO's AS reference (`data/raw/NEISO-AS/reserve-prices/rzpd_final_*.csv`) is not on disk (UC-0 FINDING §6) | — | reported as not measurable; the model's own share of hours with reserve MCP < $1 is reported control vs arm |

**Declared, not a kill:** the lower-tercile excess is offset in NEISO by a negative upper-tercile error (UC-0 F1:
−$7.5 … −$22.6), so a trough fix LOWERS the annual mean. 2023 (−3.0 %) and 2020 (−1.2 %) are the years a body-down move
pushes toward the −10 % edge; this is the binding risk, read by §3, not an invitation to move anything.

## 3. Control readings (fixed; a breach is kill #3, §6) — THE MAIN READING

**No PASS → FAIL flip on any registered NEISO year, any criterion, any class row** (`calibration_verdict.py`
per-(criterion, key, year) status diff, arm vs control scored on the SAME benchmark parts, §8(d)). GATESPEC §5 control
bar: **|ΔC3a| ≤ 1 pp on 2023**; |ΔC3a| is also reported for every year. The least-headroom rows, named now:

| year | criterion | control | headroom | why it is tight |
|---|---|---|---|---|
| 2023 | C3a | −3.0 % PASS (36.94 vs 38.10) | 7.0 pts to −10 %; **1 pp bar** | model-low; body-down moves it toward the edge |
| 2020 | C3a | −1.2 % PASS (24.83 vs 25.14) | 8.8 pts | model-low |
| 2019 | C3a | +6.8 % PASS (34.82 vs 32.59) | 3.2 pts to +10 % | body-down helps; shape may re-order |
| 2024 | C3b | 0.152 PASS | 0.048 | the span's worst shape; a decommit pattern can re-order it |
| 2019–2023, 2025 | C3b | 0.105 / 0.111 / 0.120 / 0.091 / 0.096 / 0.070 PASS | 0.08–0.13 | shape |
| 2019–2024 | C1 CC_REGULAR (±2.78–2.81 TWh & ±3 pp) | −0.69 / +0.52 / −1.19 / −0.37 / −0.11 / −0.21 TWh PASS | ≥ 1.6 TWh | SPP moved 5–8 TWh of CC energy; NEISO's CC fleet is 14 GW / 43–57 TWh |
| 2019–2024 | C1 CT_PEAKER / ST_GAS / CC_CHP | +0.14…+0.58 / −0.11…+0.28 / −0.30…−0.70 TWh PASS | ≥ 2.1 TWh | where decommitted CC energy would land |
| 2025 | C1, C2 | SKIPPED (preliminary EIA-923 vintage) | — | not a flip surface; 2025 is read on C3a/C3b/C4/C8 |
| 2019–2024 | C2 gas | 45.3→46.1 … 58.9→58.8 PASS | — | via C1 |
| every year | C4 gas hourly r / NRMSE | r 0.904–0.961, NRMSE 0.091–0.145 PASS (r ≥ 0.70, NRMSE ≤ 0.30) | — | commitment changes the hourly shape |
| every year | C8 forced share | CC_REGULAR 0.4–1.7 % PASS (cap 30 %) | — | MECH 28 reported not budgeted (R4); the scorer still budgets it — reported both ways |
| 2022 / 2023 / 2025 | C3c | CAVEAT (model 0 h vs RT 117 / 15 / 20 h > $300), the lone ledgered caveat (rule 22) | — | the probe carries no attestation → the scorer reads CAVEAT → FAIL as an **artefact** (SPP Addendum D(3)); magnitudes compared directly; 2019/2020/2021/2024 C3c PASS (small-count) is a real flip only if the model's > $300 hours leave [0.5×, 2×] / the ≤ 10 h band |
| — | C6 governance | PASS | — | reads UNATTESTED on the probe: artefact, declared |

Also gating: every leg's P1 `Optimal`; unserved energy up by ≤ 500 MWh in any year vs the keeper; no new D-4 FAIL row.
Determination (`iso_determination`) is reported, not gating.

## 4. Structure readings (reported; the D-6 card reads them)

| # | reading | control | arm instrument |
|---|---|---|---|
| S1 | MECH 28 share of class energy per year (CC_REGULAR, ST_GAS, COAL_BIT, CT_PEAKER if integer) and ISO-wide; TWh of UC floor | 0 (no UC) | regenerated `legitimacy_diagnostics.json` D-2 rows, id 28 |
| S2 | starts per plant-year vs CEMS (UC-0 M1, on-threshold 1 % of available cap) | CC_REGULAR 2,877/2,743 · 2,600/2,190 · 2,469/2,474 · 2,852/2,682 · 2,822/2,267 · 2,826/2,051 · 2,501/2,195 (1.00–1.38×); ST_GAS 709/73 · 301/80 · 764/150 · 156/38 · 440/52 · 284/66 · 149/20 (3.8–9.7×); COAL_BIT 76/85 · 24/36 · 120/16 · 43/16 · 28/6 · 27/9 · 17/10 | `screen_year` M1 on the arm; Σ`v` per cluster from `uc_schedule_<y>.parquet`. Sign expected: CC and ST_GAS starts down toward CEMS; SPP overshot to 0.5–0.8× CEMS — an overshoot is reported, not judged |
| S3 | online capacity vs a measured online series | NEISO publishes no hourly online-capacity series the repo holds | SKIPPED and named; the arm's `online_mw` from `uc_schedule_<y>.parquet` vs the keeper's available MW is reported (model-internal) |
| S4 | integer set and no-load fallback shares | UC-0 M6: 37 plant clusters, 16.4 GW (CC_REGULAR 29–32 clusters, 13.1–15.1 GW; ST_GAS 2–6; COAL 1–3); 1,080–1,332 integers per 36-h window | `uc_solve_log_<y>.json engine.*`, `clusters[].src` |
| S5 | M2 (a) CEMS online at ≤ (mlf+0.10)·cap while the model is off | CC_REGULAR 0.89–2.10 TWh/yr | re-measured on the arm (UC-0 convention) |

## 5. Cost readings (reported; D-2 ratio reported, never judged here)

| # | reading | bar |
|---|---|---|
| W1 | the GATESPEC §6.1 wall row per year: baseline P0+P1 s, P0 s, UC Σ s (windows, mean, p95 MILP s), P1 s, total s, ratio, integers/window, nodes p50/p95, gap p95, time-limit hits, peak RSS GB | reported for all seven years |
| W1-denominator | NEISO's row in `wallclock-baseline-2026-07.md` §3a predates the W0 recipe and the keeper bundle records no P0/P1 seconds. **Declared proxy (the SPP PRECOMMIT §5 proxy):** baseline P0+P1 = the same shard's own `solve_p0 + solve_p1` from the `log_year_phase_timing` line; ratio = total / (P0 + P1) in one container | stated as a proxy in every row |
| W2 | time-limit hits (`summary.time_limit_hits`) | ≤ 1 % of windows = **≤ 3 of 365** per year |
| W3 | uplift share = Σ `uplift_usd` ÷ Σ_t λ_P1 × load (`hourly/system_<y>.parquet`) | ≤ **2 %** (sanity; SPP read 1.0–4.4 %) |
| W4 | infeasible windows (`windows[].status`) | **0** (otherwise kill #1) |

**Shard budget rule (fixed now; the number is filled by Addendum A from the L1 bench, never after a span number exists):**
budget_min = ceil(1.3 × E / 60) where E = `capture_wall_s` of the bench (one P0 + P1 of NEISO 2023 in the solve container)
+ (365 / 31) × the January base-arm `wall_s` of the L2 rung (31 rolling windows at the registry defaults); if the bench
cannot supply either term, budget = **90 min** (the desk's fallback). One shard commit ≤ 20 min of runtime (rule 32); a shard
approaching the budget with no artifact stops and reports.

## 6. Kills (GATESPEC §5) — any one ⇒ record it in the RESULT and STOP; no re-tune, no second arm

1. **An infeasible window** in any year (`windows[].status` infeasible, or the engine's hard stop "no incumbent"): an engine
   defect, routed to UC-DESK, never a tuning invitation.
2. **A non-deterministic schedule:** the `uc_schedule_<y>.parquet` hash differs between two completed runs of the same
   recipe-year. Exercised only if a relaunched shard (PENDING > 45 min rule) and its predecessor both complete; otherwise
   recorded "not exercised".
3. **A control flip** (§3) in any registered year, or |ΔC3a 2023| > 1 pp.

## 7. L1 gate (desk rule, from SPP's two engine defects) and the verdict rule

- **L1 gate, before any span shard:** one bench shard at the pin (`bench_uc_ladder.py --iso NEISO --year 2023`, rung L1 then
  rung L2 `--months 1 --arms ""`, base arm only, 60-min budget, model `claude-opus-5-5`). PASS iff window 0 is Optimal AND
  31 / 31 January windows are Optimal (no infeasible, no time-limit hit). FAIL ⇒ STOP, report to UC-DESK, no span.
  Launched 2026-10-10 00:45Z as `session_012ycymxYWiMTrKiuCs6PZnW` (branch `claude/ucmilp-bench-neiso-2023-L1L2`); its
  numbers land in Addendum A with the budget.
- **Verdict rule (fixed):**
  - **R** — any kill fires (an infeasible window; non-determinism; a control flip or |ΔC3a 2023| > 1 pp), or C3b worsens by
    > 0.02 in any year without flipping, or C3a moves the wrong way (away from 0) by > 1 pp in any year.
  - **K candidate** — no kill, no wrong-way move above, every leg Optimal, AND the structure moved the right way: S2 CC_REGULAR
    starts/CEMS ratio closer to 1 than the control in ≥ 4 of 7 years AND T2 (≤ $15-hour ratio) rises in ≥ 4 of 7 years. The
    card then reads "promote on structure" for the owner; the lane never promotes.
  - **I** — no kill, no wrong-way move, but the structure bars above are not both met ("the relaxation was already tight here",
    GATESPEC §7.2).
  - Mixed readings are stated row by row; the determination is reported, not gating. The RESULT carries the D-6 card
    verbatim-ready: promote on structure · record R/I with evidence · hold.

## 8. Solve, compose and score plan (rules 16, 32–36; the composition deviations are DECLARED here, not discovered later)

- **Seven shards, 2019–2025**, one year each, `claude/ucmilp-neiso-<y>`, out-dir `results/calibration/ucmilp_neiso_<y>`,
  prompts from `scripts/shard_prompt.py --iso NEISO --all-years --sha 2f872a62a7cccadb6800555c11a73745dcdb89a4
  --lane ucmilp-neiso --bundle results/calibration/w0_neiso_span --set unit_commitment_milp=true --budget <Addendum A>
  --note "ucmilp-neiso: UC A/B"`, each appended with the SPP addendum (confirm `hourly/uc_schedule_<y>.parquet`,
  `hourly/uc_uplift_<y>.parquet`, `uc_solve_log_<y>.json`, `hourly/unit_marginal_<y>.parquet` in the pushed tree; report the
  §6.1 wall row: the `log_year_phase_timing` line and `uc_solve_log_<y>.json summary` verbatim; a UC hard stop is a
  successful report; never a second `--set`). Committed as `shard-prompts-ucmilp-neiso.txt`. `create_session` per year:
  `source_revision` = the pin, model `claude-opus-5-5`, tag `ucmilp:UC-2-NEISO-shard`. PENDING > 45 min: archive and relaunch.
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp_neiso_<y>` non-empty; check out; verify
  `dispatch/<y>_P1.parquet` + the three UC files + `unit_marginal_<y>`; THEN `archive_session` (rule 33).
- **Compose, zero LP, at the pin — two declared deviations from `_ucmilp_compose_span.py` (SPP Addendum D, both open at this pin):**
  (a) the keeper records `gas_price_override` per year (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52 $/MMBtu) and the
  composer's `PER_YEAR_FIELDS` lacks it → the lane runs a **scratch copy** of the composer with `gas_price_override` added to
  that set (no repo script edited; `scripts/` is not this lane's); (b) the composer lacks `_respan_shared_inputs` → the lane
  applies NEISO's own keeper-lineage composer's function (`scripts/probes/_hydro5_compose_span.py::_respan_shared_inputs`)
  to the span's `meta.json`, so the one-year benchmark-frame hashes of the first leg become the span's; the resulting hashes
  are compared with the keeper's own (`campd-8b9518ebc11b`, `eia923-0edb30122b08`, `eia930-37748ca9a57e`, …) and reported.
  `legitimacy_diagnostics.json` is REGENERATED over the composite, never copied.
- **(c) DATA PROFILE deviation, declared:** the respan rebuilds benchmark frames from raw data, so the parent hydrates the
  `neiso` raw profile (≈ 1.3 GB) for that zero-LP step only; the parent runs no LP.
- **(d) Scoring without registering (desk ruling, SPP desk addendum: E13 admits only keepers or folded runs):**
  `calibration_verdict.py` reads a registry sidecar and a run payload, so the lane builds them **locally with
  `dashboard_add_run.py --no-prune`, scores, and reverts everything under `frontend/data/` before committing** — nothing is
  registered on the dashboard; the PR touches no file under `frontend/data/`. Because NEISO's bench parts are STALE at HEAD
  (§0), the local build may rebuild `frontend/data/backcast/bench/NEISO/<y>.json.gz`; **control and arm are scored on the
  same parts** (the control re-scored zero-LP on whatever parts the arm is scored on), the gate table's control column is
  that re-score, and the registered record is shown beside it wherever the two differ. The rebuilt parts are reverted too:
  refreshing the keeper's bench is the desk's/owner's call (nyiso-148 precedent), not this lane's.
- **(e)** the slim span (every `hourly/` sidecar incl. `uc_schedule_<y>`, `uc_uplift_<y>`, `unit_marginal_<y>`,
  `uc_solve_log_<y>.json`, regenerated `legitimacy_diagnostics.json`, `metrics.json`, configs) goes under
  `docs/records/neiso/ucmilp/data/ucmilp_neiso_span/` (the SPP desk's placement); full leg bundles stay on the shard
  branches (rule 31: nothing deleted; rule 34: full bundles pushed).
- **Exit:** RESULT beside this file (`RESULT-ucmilp-neiso-ab-<date>.md`: the §6.3 gate table control → arm every year
  first, the wall rows, every reading answered, kills checked, verdict, D-6 card, where each bundle is and what a promotion
  would cost, `## Log entry`); stamp NEISO's `unit_commitment_milp` cell (verdict + citation) as the last commit after
  rebasing; ONE PR, not merged by the lane; message UC-DESK with the gate table first, then the wall rows.

## 9. DO NOT REDO

No offer-band retune; no `neiso_dynamic_reserve_requirements` / `dam_availability_rebasis` re-test (R, new evidence belongs to
another lane); no scarcity-physics arm; no `uc_*` value other than the declared defaults; no second `--set`; no control solve;
no other ISO; nothing on `src/` or `scripts/`; no dashboard registration; no promotion; no deletion of any bundle.

## Addendum A (2026-10-10 01:10Z, before any span shard exists) — the L1 gate PASSED; the budget by the §5 rule

Bench shard `session_012ycymxYWiMTrKiuCs6PZnW` (Opus) at the pin, branch `claude/ucmilp-bench-neiso-2023-L1L2` `bcd35c32`
(fetched, checked out, verified: `l1.json`, `l2.json`, logs; archived 01:08Z). Container 4 cpus, ceiling 13.36 GiB + 10 GiB swap,
`MARKET_SIM_HIGHS_THREADS=1`; peak RSS 4.89 GiB (capture) / 0.88 GB (L2 stage). The shard ran `uv sync` because the container
had no `.venv` (hard stop 3 fired on the system interpreter, pyarrow absent) — the repo's only install route, not a repair; nothing edited.

| rung | reading | value | gate |
|---|---|---|---|
| L1 (hours 0–35, NEISO 2023) | window 0 status | **Optimal**, 10.34 s MILP, 12 nodes, gap 7.3e-4, 1,332 integers / 35,388 columns / 7,560 rows | **PASS** |
| L1 | integer set | 37 integer clusters of 70 (273 fleet rows); UC-0 M6 said 37 | — |
| L1 | integrality gap | $17,376 on a $5.28 M window objective (0.33 %); LP relaxation 0.23 s | — |
| L1 | Δ vs the P1 slice | committed energy +35.5 MWh; starts 5 (MILP) vs 77 (P1 slice) | — |
| L1 | capture (one P0 + P1 of 2023) | `solve_p0` 76.5 s + `solve_p1` 27.9 s; year total 136.1 s; harness `capture_wall_s` 117.7 s | — |
| L2 (January, base arm = registry defaults, rolling) | windows / statuses | **31 windows, 31 objectives, 0 time-limit hits, 0 infeasible** (`UcWindowInfeasible` raises on an infeasible window; the run exited 0); gap max 9.9966e-4 ≤ 1e-3. The harness records no per-window status string, so "31/31 Optimal" rests on those three facts — stated as such | **PASS** |
| L2 | wall | month 623.6 s; MILP Σ 621.9 s; p50 / p95 / max 10.03 / 63.99 / 148.38 s per window | — |
| L2 | search | nodes p50 / p95 **33 / 544**, zero-node share 0.00; phase sums: presolve 9.9 s, root LP 4.5 s, **tail 606.6 s (97 %)**, 1.66 M LP iterations of which 1.15 M strong branching | — |

Reading, not a judgement: NEISO's January windows do **not** solve at the root as SPP's did (SPP nodes 1/1, 2.6–4.9 s per
window); the NEISO window branches (33–544 nodes) and the branch-and-bound tail is 97 % of the stage. The schedule hash is
`6d1c2823a82b497c`. Nothing is tuned: `uc_window_time_limit_s` stays 600 (max window 148 s), the preset stays `lean`.

**Budget (the §5 rule, computed, not chosen):** E = 117.7 + (365 / 31) × 623.6 = **7,460 s = 124.3 min**; budget = ceil(1.3 × 124.3) =
**162 min** per shard. (The denominator proxy for the §6.1 ratio is the shard's own P0 + P1 ≈ 104 s; the extrapolated ratio is
≈ 70×, far above the D-2 ceiling — reported, not judged, D-2 "Keep 3×; fund speedup".) Prompts regenerated with `--budget 162`
and committed as `shard-prompts-ucmilp-neiso.txt`; seven shards launched after this addendum is pushed.
