# PRECOMMIT — UC-4-NEISO: arm U4 (UC MILP + DA-forecast commitment demand + per-unit `ut_h`/`mlf` + reserve u-gate) on every NEISO backcast year, engine uc-1.7, 2026-10-15

**Written and pushed BEFORE any shard exists.** Every bar, kill and reading below is fixed here and fails closed; nothing
moves after a number comes in (GATESPEC §7.1). No tuning; nothing is chosen from results.

- **Lane:** UC-4-NEISO (Opus), branch `claude/ucmilp-4-neiso`, chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`),
  plan `docs/uc-milp-program-plan-2026-10.md` §11 r14 (main `ca90d2e8`, #7265) and §12.
- **Protocol:** `docs/records/governance/uc-milp-2026-10/GATESPEC-uc-milp-testing-protocol-2026-10-03.md` §5–§7.
- **Lineage:** `PRECOMMIT-ucmilp-neiso-ab-2026-10-10.md` §§1–8 and Addenda F/G; UC-3 record
  `RESULT-ucmilp3-neiso-ab-2026-10-14.md` (+ Addendum, uc-1.5: R, defect-free).
- NEISO is a **CALIBRATED CONTROL**. The no-flip bar is the main reading. Nothing here can promote (rule 31); the lane
  records and recommends.

## 1. Control, pin, arm

- **Control (rule 29(b), no control solve):** keeper `2026-10-02-w0-neiso`, bundle `results/calibration/w0_neiso_span`
  (2019–2025, solved at `306f2c00`). Its committed bundle, re-scored zero-LP on the same bench parts as the arm, is the
  control column.
- **Pin:** engine **uc-1.7** at `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365`. Shards run at this branch's head SHA after this
  file lands, which is the pin plus docs only (main `ca90d2e8` = pin + plan r14; this commit = + this PRECOMMIT).
- **Arm U4 — the recipe, exactly:**

  ```
  replay_keeper.py results/calibration/w0_neiso_span --years <y> \
      --set unit_commitment_milp=true --set uc_commitment_demand_source='"da_forecast"'
  ```

  | mechanism (charter) | how it enters U4 | source |
  |---|---|---|
  | `unit_commitment_milp` on | `--set` | UC-3 structurally preferred arm (NEISO has one UC arm) |
  | `uc_commitment_demand_source = "da_forecast"` | `--set` | r13 ruling 1; #7260 |
  | per-unit `ut_h` / `mlf` | data, no field: `data/clean/uc-params/NEISO` regenerated in each shard from `scripts/lib/uc_params` at the pin; carried by SolveEpochs 2026-10-15a/b (key-moving only for UC-armed configs) | r13 ruling 2 + owner ruling 2026-10-15 (full-hour LSL); #7262, #7264 |
  | reserve co-optimization as the keeper defines it | already in the keeper recipe: `energy_reserve_coopt = true`, `neiso_dynamic_reserve_requirements = false`. The uc-1.6 u-gate (`pmax·a·u/n` headroom for integer members) rides on it with no field | #7253; FIX-6 FINDING table: NEISO "already armed; gains only the u-gate" |
  | SPP spin share, MISO VLR | **not admitted** (SPP-only / MISO-only fields; refused or inert in NEISO) | r14 |

  Every other `uc_*` field at its registry default (24/12 h windows, gap 1e-3, 600 s window limit, `physics` scope,
  `campd_regression` no-load, `p0_targets` boundary, prefixing off, `lean` preset). D-5: the keeper arms no
  `UC_REFUSED_ALWAYS` field, so nothing is switched off; every kept floor is as in PRECOMMIT §1. The keeper's
  authorized price tuning (0.9547 fossil level, 88-scalar band surface) rides unchanged. **DOF added: 0.**

## 2. Phase 0 (zero LP, computed before this file)

**DA-forecast increment, NEISO (EIA-930 ISNE `Demand forecast − Demand`, after the 30 % QA cut;
`commitment_demand.ba_forecast_error_mw`, before the loader's T&D gross-up):**

| year | mean MW | mean |err| MW | top-100-load-hour mean MW | p5 / p95 MW | TWh/yr | QA-dropped h |
|---|---|---|---|---|---|---|---|
| 2019 | −188.7 | 308.0 | +9.9 | −980 / +344 | −1.65 | 0 |
| 2020 | −170.5 | 296.1 | +0.1 | −853 / +373 | −1.49 | 0 |
| 2021 | −183.1 | 295.1 | +144.7 | −874 / +337 | −1.60 | 0 |
| 2022 | −137.8 | 301.8 | +256.1 | −876 / +437 | −1.21 | 0 |
| 2023 | −140.5 | 292.7 | +7.8 | −860 / +393 | −1.23 | 0 |
| 2024 | −233.0 | 336.4 | +3.4 | −1046 / +311 | −2.04 | 0 |
| 2025 | −217.1 | 306.3 | +42.2 | −891 / +294 | −1.90 | 3 |

ISO-NE's day-ahead forecast runs **below** metered load on average (−1.2 to −2.0 TWh/yr) and ≈ 0 at peak (except 2021/22).
So, unlike SPP/MISO, `da_forecast` should commit *less* off-peak, not more. This is a stated expectation, not a bar.

**Per-unit `uc-params` for NEISO** (FINDING-ucdata-ut-unit-basis-2026-10-15 §§2, 6): CC `ut_h` p50/p90 17→14 / 88→60 h;
ST_GAS 19→20 / 31→24 h; coal 50→29 h. CC `mlf` p50 0.34→0.56; ST_GAS 0.18→0.30; coal 0.22→0.48. Higher min-load per
committed unit and shorter min-up both act on the whole-unit ceiling the UC-3 decomposition named.

## 3. G-DRIFT (zero LP)

**Keeper basis → UC-3 pin** is recorded in PRECOMMIT §0 and Addenda F/G: gate-off INERT, NEISO 0 keys moved. This section
covers **`2dd69d5a` (UC-3 uc-1.5 pin) → `7dbfe20f` (pin)**, 26 files in `src/` + solve-path scripts:

| hunk | files | classification for NEISO |
|---|---|---|
| uc-1.6 reserve u-gate | `model/uc/window.py`, `pipeline/uc.py` | **LIVE, gate-on only** — NEISO co-opts reserves, so integer members' headroom becomes `pmax·a·u/n` |
| uc-1.7 commitment demand | `data/commitment_demand.py`, `pipeline/uc.py`, `config/scenarios.py`, `constants.py` | **LIVE, gate-on only, armed by the `--set`** |
| `load_zone_weights` extracted from `load_demand` | `data/eia930/demand.py` | **INERT**: pure function extraction, same calls, same arithmetic (read hunk-by-hunk); the P1 demand is byte-identical |
| per-unit `ut_h` / `mlf` | `scripts/lib/uc_params/__init__.py`; epochs 2026-10-15a/b in `results/cache.py`, `config/solve_surface.py` | **LIVE, gate-on only** (data); the epochs' `requires` gate leaves every UC-off key, the keeper's included, unmoved |
| SPP synchronized reserve | `model/reserves/spec.py`, `model/lp/model.py` (`reserve_synchronized` kwarg, `None` by default), `pipeline/solve.py` (`p1_kwargs_overrides`, `{}` unless a sync class exists), `pipeline/uc.py` | **INERT for NEISO**: the field is SPP-only; with no synchronized class the overrides dict is empty and the P1 kwargs are untouched |
| VLR pocket rows | `model/uc/pocket.py`, `model/uc/window.py`, `model/uc/diagnose.py`, `data/vlr_pocket_groups.py`, `scripts/lib/vlr_pocket_groups/*`, `scripts/data/curate_vlr_pocket_groups.py` | **INERT for NEISO**: MISO-only, default off, no row built when off |
| `model/uc/params.py` (comment only), `model/lp/__init__.py` (passes `reserve_synchronized`, default `None`) | — | INERT; read hunk-by-hunk |
| forward DF profile | `scripts/data/derive_load_forecast_error.py`, `curate_load_forecast_error.py`, `clean_profiles.py` | INERT for a backcast (forecast lane only; the backcast reads EIA-930 raw) |
| `scripts/lib/key_provenance.py` | — | INERT (census tool) |
| solve surface | `solve_surface_register.py --diff 2dd69d5a 7dbfe20f`: *"342 → 345 names; 0 value(s) moved, 3 added … NO VALUE MOVED"* (the 3 added are the new constants, inert at default) | no key reached |

Every LIVE hunk is on the gate-on path; the keeper (the control) is untouched, so no control solve (rule 29(b)).

## 4. Pass bars and kills (fixed; GATESPEC §5, applied as in the UC-3 record)

**Kills — any one ⇒ record in the RESULT and STOP; no re-tune, no second arm:**

1. **An infeasible window** or the engine's "no incumbent" stop, in any year (engine defect → UC-DESK).
2. **A non-deterministic schedule:** `uc_schedule_<y>.parquet` hash differs between two completed runs of the same
   recipe-year (exercised only if a relaunched leg and its predecessor both complete; else "not exercised").
3. **A control flip:** any PASS → FAIL on any gated criterion, key or class row in any year, arm vs control scored on the
   same bench parts; or **|ΔC3a 2023| > 1 pp**.

**Also gating (a breach is R):**

- every leg's P1 `Optimal`;
- **unserved energy ≤ keeper + 500 MWh** in every year;
- no new D-4 FAIL row.

**Verdict rule:**

- **R** — any kill fires; or C3b worsens by > 0.02 in any year; or C3a moves away from 0 by > 1 pp in any year; or any
  gating line above is breached.
- **K candidate** — no R trigger, every leg Optimal, AND CC_REGULAR starts/CEMS closer to 1 than the control in ≥ 4 of 7
  years, AND T2 (count ratio of hours ≤ $15, model/actual) rises in ≥ 4 of 7 years. The card then reads "promote on
  structure" for the owner; the lane never promotes.
- **I** — otherwise.
- **Probe artefacts (declared):** C6 UNATTESTED and C3c CAVEAT → FAIL from the missing attestation are artefacts when the
  magnitude is identical (UC-2 Addendum B). They are not flips.
- Coverage: a year lost to the memory gate (§6) is a coverage gap. The verdict is stated on the years solved, and the gap
  is named; a kill on any solved year still fires.

## 5. Readings (reported; the D-6 card reads them)

| # | reading | instrument |
|---|---|---|
| G | §6.3 gate table, control → U4, every year (C1 class rows, C2, C3a, C3b, C3c, C4, C6, C8, D-2 MECH 28 share) | `calibration_verdict.py` on the composed span vs the control re-score |
| S2 | **CC_REGULAR and ST_GAS starts ÷ CEMS** per year (UC-0 M1 convention; COAL_BIT reported too) | `screen_year` M1 on the arm; Σ`v` from `uc_schedule_<y>` |
| U | **uplift** = Σ`uplift_usd` ÷ Σ λ_P1 × load; sanity bar ≤ 2 % (reported) | `hourly/uc_uplift_<y>.parquet` |
| W | wall row (GATESPEC §6.1): P0, UC Σ, P1, total, ratio to the same shard's P0+P1, time-limit hits (≤ 3/365), peak RSS | `log_year_phase_timing`, `uc_solve_log_<y>.json` |
| D | commitment demand actually used: `engine.commitment_demand` (source, mean / top-100 median increment, QA-dropped hours) vs §2 | `uc_solve_log_<y>.json` |
| P | price by load tercile, load-weighted mean, T1/T2/T3 (PRECOMMIT §2) | composed `hourly/system_<y>` |
| C8 | as scored and with MECH 28 removed | regenerated `legitimacy_diagnostics.json` |
| X | **U4 vs UC-3 uc-1.5** per year: price, C3a, C3b, CC starts/CEMS, integer-plant output, control energy above the arm's P1 ceiling. Reported as the joint effect of the four mechanisms; no per-mechanism attribution is claimed | `docs/records/neiso/ucmilp/data/ucmilp3_neiso_uc15_span/` |

## 6. Execution (rules 16, 32–36)

- **Seven shards, 2019–2025**, one year each, out-dir `results/calibration/ucmilp4_neiso_u4_<y>`, branch
  `claude/ucmilp4-neiso-u4-<y>`. Prompts: `scripts/shard_prompt.py --iso NEISO --all-years --sha <this branch head>
  --lane ucmilp4-neiso-u4 --bundle results/calibration/w0_neiso_span --set unit_commitment_milp=true
  --set uc_commitment_demand_source='"da_forecast"' --budget 720`, plus a lane addendum (memory gate; engine checks
  `engine.version == uc-1.7`, `engine.fields.uc_commitment_demand_source == "da_forecast"`, `engine.commitment_demand.source
  == "da_forecast"`; UC files in tree; > 100 MB split; a UC hard stop or OOM is a successful report). Committed as
  `shard-prompts-ucmilp4-neiso-u4.txt`. `create_session`: model `claude-opus-5-5`, `source_revision` = the full SHA,
  tag `ucmilp:UC-4-NEISO-shard`.
- **Launch serially, ~5 min apart.**
- **Memory gate ≥ 22.4 GiB** (ceiling + swap from `prepare_solve_container.py`'s `swap:` line); below it the shard stops
  before any data step. A blocked year gets ≤ 4 relaunches ~30 min apart, then is a **coverage gap** with the attempt log.
- **Budget 720 min** per leg (cost cap only).
- **On each report:** fetch; `git ls-tree -r <sha> -- results/calibration/ucmilp4_neiso_u4_<y>` non-empty; check out;
  verify `dispatch/<y>_P1.parquet`, `hourly/uc_schedule_<y>`, `hourly/uc_uplift_<y>`, `uc_solve_log_<y>.json`,
  `hourly/unit_marginal_<y>` bytes present; THEN archive (rule 33).
- **Compose and score** exactly as PRECOMMIT §8 (a)–(e): composer with the declared `gas_price_override` per-year
  deviation, keeper-lineage `_respan_shared_inputs`, diagnostics regenerated; local `dashboard_add_run.py --no-prune`
  build, scored, everything under `frontend/data/` reverted before commit (E13; nothing registered).
- **Exit:** `RESULT-ucmilp4-neiso-u4-<date>.md`, slim span `docs/records/neiso/ucmilp/data/ucmilp4_neiso_u4_span/`,
  NEISO matrix cell for the arm stamped; one records-only PR, not merged by the lane; report to UC-DESK.

## 7. DO NOT REDO

No offer-band retune; no `neiso_dynamic_reserve_requirements` / `dam_availability_rebasis` re-test; no control solve; no
third `--set`; no `uc_*` value other than the two above; no per-mechanism ablation arm (the charter names one arm).

## Addendum A (2026-10-15 10:45Z, after launch, before any leg result) — launch record, FIX-8 hold, memory-gate ruling

No bar, kill, reading or recipe changes. This records process facts only.

- **Prompts:** `shard-prompts-ucmilp4-neiso-u4.txt` (commit `3ab0b1e9`). The SOLVE line's second `--set` is single-quoted, because bash would otherwise strip the JSON quotes `replay_keeper` needs.
- **Launch 1, 09:56–10:08Z:** 2019 (`session_01CakQES`), 2020 (`session_01LZqWFb`), 2021 (`session_01GuU6FZ`). 2019 was first created with a placeholder prompt; the full prompt followed by message.
- **UC-DESK hold FIX-8, 10:09Z:** `da_forecast` raises at `commitment_demand.py:254` for ISOs whose import pseudo-zone is appended to the demand. All three shards were stopped. Nothing was pushed and no leg branch exists. The stop is logged as a defect hold, not a memory relaunch.
- **NEISO is unaffected:**
  - 2019 passed UC prep before it was stopped: `UC commitment demand (da_forecast, eia930_da_forecast): -189 MW mean increment, 0 QA-dropped hours`, then `UC stage prepared: 61 clusters, 18 integer`. The raise sits before that log line.
  - `HQ_import` is a configured zone of `get_iso_config('NEISO')`, not an appended one. The increment and the demand both carry 5 zones.
  - `eia930.load_zone_weights` gives `HQ_import` a **maximum weight of 0.0 in every hour, 2019–2025**, so its increment is exactly 0. Every hour's weights sum to 1.0.
  - UC-DESK accepted this at 10:11Z ("continue at 7dbfe20f"). No re-pin.
- **Memory-gate ruling (UC-DESK, 10:19Z):** the gate passes iff the printed ceiling + swap rounds to ≥ 22.4 GiB (raw ≥ 22.35). The standard 13.36 + 9.0 = 22.36 GiB container passes. The 2021–2025 prompts carry this wording.
- **Launch 2, all at `43bc180e`:**

  | year | session | launched |
  |---|---|---|
  | 2019 | `session_01BYXcr8563mzSAskNzvDhFW` | 10:11Z |
  | 2020 | `session_015koVxfzEmdvPD9TcbADfqz` | 10:17Z |
  | 2021 | `session_01BXU3AbtzQndDxEJg8dJkgD` | 10:22Z |
  | 2022 | `session_01B1pvMUBTNN9c8SjD6zUGE2` | 10:28Z |
  | 2023 | `session_013z3111kB5xpKgdCvGrZkRt` | 10:33Z |
  | 2024 | `session_01RnG1qA2JVdBo4LMhZ96wyi` | 10:39Z |
  | 2025 | `session_01QJSpD4bsyen8DPVYNkXjNE` | 10:44Z |

## Addendum B (2026-10-15 12:57Z, before any leg result) — lane prompt error; corrected relaunch order; attempt ledger

No bar, kill, reading or recipe changes.

- **The prompt error (this lane's).** The launch-2 prompts and their a2 relaunches ran `uv sync` (lane STEP 0) before `prepare_solve_container.py`. The template's hard stop 2 says to run the prepare step FIRST. Swap is provisioned from free disk, and after `uv sync` the containers reported 6.7 GiB free. So 2020/21/22/24/25 printed 16.4–17.4 GiB and stopped at the gate, twice each (10 sessions). Nothing was pushed, and every session is archived.
- **UC-DESK ruling, 12:36Z.** a1 and a2 for those five years are a lane prompt error. They do **not** count as memory attempts.
- **Attempt cap.** The 4-attempt cap restarts with the corrected order. A year that reaches 3 of 4 holds its 4th attempt; it is recorded "held pending owner gate ruling", not as a coverage gap. The gate stays at 22.4 GiB until the owner rules.
- **The correction.** `prepare_solve_container.py` is stdlib-only. The corrected prompts run it with system `python3` as the very first command, before `uv sync` or any data step. UC-DESK cautions that other lanes still see 17.4 GiB at boot with prepare first, so the corrected launches may show the container's own allowance.
- **Corrected attempt 1, all at `43bc180e`:**

  | year | session | launched |
  |---|---|---|
  | 2020 | `session_01GjLbAcPzWfuUdePvi9rWQ7` | 12:35Z |
  | 2021 | `session_01MfeujyTSMEpzQtZP55iQun` | 12:41Z |
  | 2022 | `session_01FZRM859PyD5nD6p1Giva71` | 12:46Z |
  | 2024 | `session_01PK7VhWP5miNDN2wnB8bitA` | 12:51Z |
  | 2025 | `session_015z1WqocpdnxG5DJdHSxPUq` | 12:57Z |

- **Still solving from launch 2:** 2019 (`session_01BYXcr8`, 22.36 GiB) and 2023 (`session_013z3111`, 22.36 GiB).

## Addendum C (2026-10-15 15:25Z) — attempt ledger, engine-performance stop, infrastructure loss, FIX-9 hold

No bar, kill, reading or recipe changes. No leg has produced a bundle. Nothing has been composed, scored or judged.

| year | outcome so far | memory attempts (corrected order) |
|---|---|---|
| 2019 | Solved UC windows 0–254, then **lost to a container reclaim ~14:28Z** while the shard session was idle (`session_01BYXcr8`). UC-DESK ruled it an infrastructure loss: not a memory attempt, not a verdict. | 0 |
| 2020 | Gate-blocked at 17.4 GiB on corrected attempts 1 and 2. | 2/4 |
| 2021 / 2022 / 2024 / 2025 | Gate-blocked at 17.4 GiB on corrected attempt 1. | 1/4 each |
| 2023 | **Engine-performance stop at 13:27Z** (UC-DESK ruling), 64/365 windows in 2 h 41 m, ~15 h projected against the 720-min budget (`session_013z3111`). | 0 |

- **Engine finding (zero LP).** Against UC-3 uc-1.5 on the same windows, U4 MILP time is 7.0× (2019, w0–254) and 4.6× (2023, w0–63). Branch-and-bound nodes rise ~10–15× on an identical integer set (61/18 and 70/22 clusters). There are 3 time-limit hits per ~100 windows, against 0 in UC-3. Evidence is in `data/ucmilp4_fix9_evidence/`.
- **FIX-9.** UC-DESK chartered FIX-9 (`session_018AWf6q`): an ablation bench that separates the u-gate, per-unit `mlf`/`ut_h`, and DA demand on captured NEISO windows.
- **Hold.** Every NEISO launch is held until FIX-9 reports.
- **Standing shard rule (UC-DESK, 15:20Z).** A shard running a detached solve keeps its session alive. It re-arms its watcher, or schedules a `send_later`, at intervals of 90 min or less, and never ends a turn on a watcher that expires before the solve does. Every relaunch prompt carries this rule.
