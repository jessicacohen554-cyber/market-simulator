# PRECOMMIT — UC-4-SPP: arm U4 (UC on uc-1.7, floors off, DA-forecast commitment, reserve co-opt + ≥½ spinning share), every SPP backcast year, 2026-10-15

**Written and pushed before any shard of this lane exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing moves after a number comes in (GATESPEC §7.1; rule 1(c) by analogy). Lane `UC-4-SPP` (Opus), branch
`claude/ucmilp-4-spp` off `main` `ca90d2e8` (desk r14, PR #7265). Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`),
plan §11 r14: *"UC-4 chartered: all six UC ISOs on uc-1.7 at `7dbfe20f`, each with every new mechanism the ISO admits …"*.

**Why this is not a re-test (rule 28).** The `unit_commitment_milp` × SPP cell reads R on uc-1.5 evidence
(`RESULT-ucmilp3-spp-2026-10-14.md`). Four owner-ruled mechanisms have landed since (r13, all "recommended"), each aimed at
UC-DIAG's ranked under-commitment causes and none present in UC-3: DA-forecast commitment demand (#7260, uc-1.7), per-unit
`ut_h` (#7262, epoch 2026-10-15a), per-unit `mlf` (#7264, epoch 2026-10-15b), the SPP ≥½-spinning sub-row (#7261) seen by the
uc-1.6 u-gate (#7253). This is new evidence; the arm is one recipe, fixed below.

## 0. Preconditions (zero LP, at the pin)

| check | result |
|---|---|
| keeper `frontend/data/backcast/keepers/SPP.json` | `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span`, years 2019–2025 |
| keeper bundle, keeper shard, `iso_configs.py` unchanged since UC-3's pin: `git diff --quiet 2dd69d5a 7dbfe20f -- results/calibration/closeout_spp_nuc_span frontend/data/backcast/keepers/SPP.json src/market_sim/config/iso_configs.py` | **identical** (exit 0) |
| branch head vs pin: `git diff --quiet 7dbfe20f HEAD -- src scripts` | identical (the branch adds `docs/` only) |
| every U4 field exists at the pin | `unit_commitment_milp`, `st_gas_mustrun_per_plant`, `coal_sync_floor_release`, `energy_reserve_coopt`, `spp_spinning_reserve_share`, `uc_commitment_demand_source` (admissible `("actual","da_forecast")`, `scenarios.py:4466`) |
| DA-forecast coverage, SPP (`SWPP`) | 2019–2025 all present (FINDING-ucmilp-fix7 §3: QA-dropped 0–69 h/yr; mean increment −0.24 … +2.07 GW) |
| the recipe has run once, at an earlier pin | SPIN repro SPP 2020 (arm B + co-opt + spin, no DA forecast, uc-1.6) and FIX-7 repro SPP 2020 (arm B + DA forecast, uc-1.7); both P1 Optimal. **Never jointly**: U4's 2020 is the first joint solve |

## 1. Pin, control, arm

- **Pin (charter):** `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (engine `uc-1.7`). Shards pin **this branch's head after this file is
  pushed**, whose `src/`+`scripts/` equal the pin's; `source_revision` is that full 40-char SHA.
- **Control (rule 29(b), no control solve):** keeper bundle `results/calibration/closeout_spp_nuc_span`, its committed `metrics.json`,
  `legitimacy_diagnostics.json`, `hourly/*`.
- **Comparators (read, never re-solved):** UC-3 arm B uc-1.5 (`docs/records/spp/ucmilp/data/ucmilp3_spp_b_span/`) — U4's nearest
  ancestor; UC-3 arm A uc-1.5 (`…/ucmilp3_spp_a_span/`).
- **Arm U4 — the exact recipe** (`replay_keeper.py results/calibration/closeout_spp_nuc_span --years <y>` plus):
  ```
  --set unit_commitment_milp=true
  --set st_gas_mustrun_per_plant=false
  --set coal_sync_floor_release=true
  --set energy_reserve_coopt=true
  --set spp_spinning_reserve_share=true
  --set uc_commitment_demand_source='"da_forecast"'
  ```
  - Lines 1–3 are UC-3 arm B verbatim (owner ruling D-5b V2; "floors off" = no `st_gas_mustrun_per_plant` floor, no
    `MECH_COAL_MUSTRUN` sync floor). The UC's integer commitment (MECH 28) is the one mechanism carrying slow-unit commitment (rule 19).
  - Line 4: the SPP keeper arms **no** co-opt (`energy_reserve_coopt=false` in its `run_config`), so "reserve co-opt as the keeper defines
    it" is empty for SPP; the charter's SPP line arms it explicitly. The reserve design is the pin's SPP design in
    `model/reserves/spec.py` (pooled contingency family, unchanged since the keeper). Matrix: `energy_reserve_coopt` × SPP is **I**
    (0 bind hours without UC); under UC the uc-1.6 u-gate ties integer members' headroom to `u`.
  - Line 5: ≥½ of the requirement as a synchronized class-1 family at the $250/MW Spinning VRL (`SPP_RSG_SPIN_MIN_SHARE` 0.5,
    `SPP_SPINNING_RESERVE_VRL` 250; SPP RSG p.5), restricted by the UC stage to integer members.
  - Line 6: r13 ruling 1. P1 still clears on actual load; prices stay P1's duals (rule 4).
  - Per-unit `ut_h` / `mlf`: no field. They arrive through `data/clean/uc-params/SPP`, which each shard rebuilds at the pin
    (`regenerate_clean.py --solve-profile SPP`); epochs 2026-10-15a/b re-key every UC-armed config (`solve_surface.SolveEpoch.requires`).
    The shard reports the epoch ids from its `solve_surface.json`.
  - Rule-19 substitutions: none further (the keeper arms no bridge, no posture; scarcity overlay is off in the keeper).
- **Solver path:** the pin's registered defaults (`uc_solver_preset="lean"`, `uc_slim_window=true`), as UC-3. Every other `uc_*` field at
  its declared default, never swept (window/look-ahead 24/12, `uc_mip_rel_gap` 1e-3, `uc_window_time_limit_s` 600, scope `physics`,
  no-load `campd_regression`, boundary `p0_targets`, `uc_prefixing=false`). Pricing R3 and rule-20 R4 unchanged. The keeper's authorized
  price tuning (`offer_curve_by_group`, all bands 0.93) rides unchanged.
- **DOF (rule 21):** zero added. Every value above is a boolean, an enum chosen by owner ruling, or a published constant already on `main`.

### 1.1 G-DRIFT `2dd69d5a → 7dbfe20f` (zero LP; prior drift classified in UC-3 Addendum A and earlier)

18 commits. Outside `docs/` and `tests/`, 36 paths. On the backcast path:

| file(s) | hunk | control (UC off) | arm |
|---|---|---|---|
| `model/uc/{window,pocket,params,diagnose}.py`, `pipeline/uc.py` | uc-1.6 u-gated reserve headroom; uc-1.7 commitment demand; spin-share class restricted to integer members; VLR pocket rows | **INERT**: gated import (`pipeline/solve.py`, `runner.py`, `run_calibration_full.py` import `pipeline.uc` only under `unit_commitment_milp`) | **LIVE**, intended. `pocket.py` (VLR) is MISO-only and off |
| `pipeline/solve.py` +11 | UC-stage P1 kwargs override | **INERT**: inside the `_uc_stage` branch | LIVE (spin class restriction into P1) |
| `model/lp/model.py` +22 | `reserve_synchronized` kwarg, default `None` | **INERT**: default None, no row/column change | LIVE (with line 5) |
| `model/reserves/spec.py` +70 | SPP spin family; early return when `spp_spinning_reserve_share` off | **INERT**: off path returns the prior single-family design (`eligible.reshape(1,-1)`), and the keeper has no co-opt | LIVE |
| `data/eia930/demand.py` ±70 | `load_zone_weights` extracted from `load_demand` | **INERT**: pure refactor, identical arithmetic | also reused by the commitment demand |
| `data/commitment_demand.py` (new), `config/constants.py` (`COMMITMENT_DF_*`, `VLR_GROUP_MIN_COMMITTED_UNITS`), `scenarios.py` (new fields, defaults off/`"actual"`) | new fields and their reader | **INERT**: defaults off; registered in `_CACHE_KEY_OPTIONAL_FIELDS` at their defaults | LIVE (line 6) |
| `config/solve_surface.py`, `solve_surface_declared.py`, `results/cache.py` | epochs 2026-10-15a/b, `requires="unit_commitment_milp"` | **INERT**: an epoch with `requires` skips a config with the UC off | re-keys the arm |
| `scripts/lib/uc_params/__init__.py` | per-unit `ut_h`/`mlf` derivation | **INERT**: `uc-params` read only by `model/uc/params.py` | LIVE (data) |
| `scripts/data/*load_forecast_error*`, `*vlr_pocket_groups*`, `scripts/lib/clean_profiles.py`, `regenerate_clean.py`, `scripts/lib/key_provenance.py`, `render_data_dictionary.py`, `data/raw/vlr-pocket-groups/`, schemas, `.gitignore`, `CHANGELOG.md` | data intake / dictionary / docs | not on the control's solve path | `load-forecast-error` read by line 6 |

**The control is INERT; the keeper bundle remains the control; no control solve is owed.**

## 2. Readings (fixed ex ante)

Per year, **control → U4** (and U4 vs UC-3 arm B, descriptive), from `calibration_verdict.py` (rubric 3.20) over the composed span:

1. **Gate table:** C1 per class (CC_REGULAR, COAL_PRB, COAL_LIGNITE, ST_GAS, CT_PEAKER), C2, C3a, C3b, C3c (magnitude), C4, C8 (scored / R4),
   determination.
2. **Targets (UC-3's bars, unchanged):** T1 2020 C3a ≤ +18.85 % (control +27.7 %); T2 2019 C3a ≤ +11.15 % (+12.3 %); T3 2020 C3b ≤ 0.2725
   (0.345); T4 M3 low-price ratios rise (sign); T5 M4 reserve dormancy falls (sign; with co-opt on, read the class-0 and class-1 MCPs).
3. **Unserved:** U4 ≤ control + 500 MWh in every year (hard bar, part of the verdict).
4. **Starts ÷ CEMS (M1), reported per year:** CC_REGULAR and ST_GAS (also COAL_PRB, COAL_LIGNITE), control vs U4. Reported, not gated.
5. **Reserve:** class-0 / class-1 bind hours and mean MCP; committed slow headroom at the top-100 actual-price hours.
6. **DA-forecast seam:** Σ P1 `Dump` MWh per year (over-commitment cost of a positive forecast bias); 2025 (mean +2.07 GW) is the year to watch.
7. **Engine / cost:** windows Optimal; time-limit hits (≤ 1 %); uplift = Σ make-whole ÷ Σ λ_P1·load (≤ 2 %, sanity); forced peak-tranche TWh
   (> 0.1 TWh in any year → reported to UC-DESK as a defect-6 recurrence); wall ÷ (P0+P1) (cost finding, never a defeat); peak RSS.
8. **Price-move diagnosis** (zero LP, descriptive, never tuned on) for any year with |ΔC3a| > 2 pp or |ΔC3b| > 0.02 vs the control:
   UC-3 §2's four steps (Δ LMP by hour class; marginal mix; Δ online MW; attribution to decommitment / trough body / reserve dual).

## 3. Kills (GATESPEC §5; any ⇒ record, no re-tune, every year still scored)

1. **Infeasible window** or "no incumbent": engine defect. That leg stops; window index, hours, traceback to UC-DESK. This lane patches no `src/`.
2. **Non-deterministic schedule:** `uc_schedule_<y>.parquet` hash differs between two completed runs of the same year. Exercised only if a
   relaunch and its predecessor both complete; else "not exercised".
3. **Control flip:** any PASS → FAIL vs the keeper on any year, criterion or class row (C3c CAVEAT → FAIL from the missing attestation is the
   known artefact, compared on magnitude). New D-4 FAIL rows are counted with this kill. The absence of the control's
   `st_gas_mustrun_per_plant` D-4 rows is expected, not a reading.
4. **Unserved** > control + 500 MWh in any year (charter bar).

## 4. Verdict rule

- **K candidate:** T1, T2, T3 met; T4/T5 signs right; no kill; every leg Optimal. The lane recommends a D-6 "promote on structure" card;
  it never promotes (rule 31).
- **R:** any kill, or any of T1–T3 moves the wrong way past the control.
- **I:** no kill, no wrong-way move, |Δ| below the bar on T1–T3.
- **Mixed:** worst of the target rows, stated row by row, with the rule-1 reading (engine, calibration or structure).
- A year lost after 4 relaunches is a **coverage gap**; the verdict is read on the solved years and says so.
- Matrix: `unit_commitment_milp` × SPP cell stamped with the U4 verdict and citation (SPP shard only).

## 5. Solve plan (rules 16, 32–36)

- **7 shards**, 2019–2025, one year each, solved alone (rule 36), **launched serially ~5 min apart**. Out-dir
  `results/calibration/ucmilp4_spp_u4_<y>`, branch `claude/ucmilp4-spp-u4-<y>`. Prompts from
  `scripts/shard_prompt.py --iso SPP --year <y> --sha <branch head> --lane ucmilp4-spp-u4 --bundle results/calibration/closeout_spp_nuc_span
  --set …(§1) --budget 720`, plus the UC-3 lane appendix (UC files and `unit_marginal` in the pushed tree; files > 100 MB split; field values,
  preset, slim, engine version, floor-row count = 0; GATESPEC §6.1 wall row; kill #1 stop), plus: the `solve_surface.json` epoch ids, the
  `reserve_family` sidecar in the tree, and **a memory hard stop: if the preflight's ceiling + swap is < 22.4 GiB, STOP before any data step
  and report** (charter gate). Prompts committed as `shard-prompts-ucmilp4-spp.txt`.
- **Budget:** 720 min LP wall per shard (UC-3 legs ran 15–32 min). One shard commit ≤ 20 min runtime (rule 32).
- **Blocked year:** a shard that stops at the memory gate or stays PENDING > 45 min is archived and relaunched, at most **4 relaunches ~30 min
  apart**; then the year is a recorded coverage gap with its attempt log.
- **Each leg:** fetch; `git ls-tree -r <sha> -- <out-dir>` non-empty; check out; verify `dispatch/<y>_P1.parquet`, `uc_schedule`, `uc_uplift`,
  `uc_solve_log`, `unit_marginal` bytes; then archive (rule 33).
- **Compose and score in the parent (zero LP):** `_ucmilp_compose_span.py` with UC-3's disclosed scratch-copy workaround (per-year
  `gas_price_override`; keeper `_respan_shared_inputs`; `--restore-shared-inputs`); `calibration_verdict.py` via local probe registration
  (`dashboard_add_run.py --no-prune`, excluded in `.git/info/exclude`, **never committed**); regenerated `legitimacy_diagnostics.json`; M1/M3/M4.
- **Records-only PR** (not merged; UC-DESK merges): this file, the prompts, the RESULT, the slim span under
  `docs/records/spp/ucmilp/data/ucmilp4_spp_u4_span/` (no `dispatch/`, no `unit_hourly`), the SPP matrix cell.
- No registration (E13), no promotion, nothing deleted (rule 31).

## 6. DO NOT REDO

`docs/mechanism-testing-matrix.md` §5.7's list. `spp_commitment_posture` (R) in no form. No `uc_*` value other than the declared defaults.
No `--set` beyond §1. No control solve. No re-solve of a UC-3 leg. No second arm, no sweep of which mechanism to drop.

## Addendum A (2026-10-15, before any number was read) — launch record and the desk's gate-wording ruling

PRECOMMIT pushed as `b14efcf7` and prompts as `d5b289d6` (blob-verified) before any shard. Shards pin
`b14efcf79ec1f1cf045f17e2c7ed8df8866fe846`, model `claude-opus-5-5`, tag `ucmilp:UC-4-SPP-shard`, launched serially ~5 min apart.
UC-DESK ruling 10:19Z (all UC-4 lanes): the 22.4 GiB gate passes iff the printed ceiling+swap rounds to ≥ 22.4 (raw ≥ 22.35), so the
standard 13.36 + 9.0 = 22.36 container passes. Prompts for 2024 onward carry that wording; the recipe and every other line are unchanged.

| year | attempt 1 | attempt 2 |
|---|---|---|
| 2019 | `session_01PFiFm2tqTdHZdHbuGXCBC6` solved (22.36) | — |
| 2020 | `session_013185fkroSi8eioHWR63Lda` solved (22.36) | — |
| 2021 | `session_0132cr1ysVtosNmgW2JavPU9` blocked 18.4 | `session_01HsfdP3e2G1eaMJYbNUcKzA` blocked 17.4 |
| 2022 | `session_01MGeNGRitpcBnp9RBUR3Fk2` blocked 17.4 | `session_01E3jPSwKEcspVCgAnxpkp4b` blocked 17.4 |
| 2023 | `session_01VDPF1nn49J7fJZybe3YLvz` blocked 18.4 | `session_016ct9KBLWz3TWxRo1haDKRE` launched |
| 2024 | `session_01QYGk3HB3AEPUpKWivcU6ex` blocked 17.4 | `session_01Bmewqv7BWZphdcQAWo1eqk` launched |
| 2025 | `session_01H7oDaAuQY41cjK2qpPhKrY` passed (solving) | — |

## Addendum B (2026-10-15 11:14Z, before any number was read) — memory gate re-based by UC-DESK

UC-DESK ruling, verbatim: *"gate_ISO = 1.5 × max observed cgroup peak (rss+swap) over all solved UC legs of that ISO, rounded up to 0.1 GiB.
This is an infra safety factor, not a model parameter; solve-surface inert. SPP: 1.5 × 8.48 = 12.8 GiB."* The SPP gate is therefore
**printed ceiling+swap ≥ 12.8 GiB**, effective for every launch after this addendum is pushed. Attempts already spent stay counted; the
≤ 4-relaunch cap is unchanged. Any leg whose cgroup peak exceeds 12.8 GiB, or that OOMs, stops the lane's launches and is reported to
UC-DESK; the lane never raises the gate. Every solved leg's cgroup peak is reported in the RESULT. Recipe, readings, bars, kills and
verdict rule are unchanged.

Evidence (cgroup peak / process VmHWM, GiB; UC-3 from `RESULT-ucmilp3-spp-2026-10-14.md` §2.4, UC-4 from the shards' `memory peak:` lines, swap peak 0.00):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| UC-3 A | 8.47 / 4.75 | 8.46 / 5.35 | 8.39 / 5.61 | 8.36 / 4.73 | 8.45 / 4.67 | 7.88 / 5.63 | 8.47 / 4.72 |
| UC-3 B | 8.32 / 4.79 | 7.82 / 5.67 | **8.48** / 5.67 | 8.48 / 5.63 | 7.99 / 5.59 | 7.99 / 4.74 | n/a |
| UC-4 U4 | 7.88 / 6.01 | 7.85 / 7.01 | — | — | — | — | — |

## Addendum C (2026-10-15 12:40Z, before the span was scored) — 12.8 GiB gate withdrawn; 2023 held

After Addendum B, the 2021 and 2022 attempt-3 shards were launched under the 12.8 GiB wording and the running 2024 attempt-2 shard
was told of it. This session's permission classifier then refused a further launch under 12.8 (it treats lowering a gate on a
peer-session message as unsafe); the lane did not work around it. UC-DESK (12:35Z): *"the 12.8 GiB gate is withdrawn until the
owner rules, and every launch is on 22.4 … the 2021/2022 attempt-3 legs ran under 12.8 before the withdrawal; their results stand
if they solved within measured memory. For any year at 3/4 attempts, HOLD the 4th attempt … record 'held pending owner gate
ruling', not a gap."*

| year | container (ceiling + swap) | gate in force | cgroup peak GiB | result |
|---|---|---|---|---|
| 2021 (att 3) | 13.36 + 4.0 = 17.4 | 12.8 | 7.98 | solved, `99bda9b6` |
| 2022 (att 3) | 13.36 + 4.0 = 17.4 | 12.8 | 8.11 | solved, `a3062c45` |
| 2024 (att 2) | 13.36 + 4.0 = 17.4 | 12.8 (by message) | 8.44 | solved, `df677899` |
| 2023 | att 3 `session_0129ry7ewc3o2y58Z6ZSBX89` and att 4 `session_01BydsXKM9zQ5BgBDmNZ7qQo` blocked at 17.4 under 22.4 | 22.4 | — | **held pending owner gate ruling** (3 of 4 relaunches spent) |

Every solved leg peaked ≤ 8.44 GiB, inside measured SPP memory (max 8.48). Readings, bars, kills and verdict rule are unchanged;
the RESULT is read on the six solved years and says so.
