# PRECOMMIT — UC-5-SPP: arms U4b (U4 on the R16 MTLF DA basis) and U5 (U4b + RUC), every SPP backcast year, 2026-10-18

**Written and pushed before any shard of this lane exists.** Every reading, bar, kill and budget below is fixed here and fails
closed; nothing moves after a number comes in (GATESPEC §7.1). Lane `UC-5-SPP` (Opus), branch `claude/ucmilp-5-spp` off `main`
`60e7c6fa` (engine `uc-1.10`). Chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner rulings R12 (RUC approved),
R15 (DA-schedule digest reuse + identity adoption), R16 (SPP DA basis = MTLF vintage at ≤ 13:00 CPT D-1), R18 (two arms), r16
ruling 1 (SPP memory gate 10.6 GiB); `docs/uc-milp-program-plan-2026-10.md` §8.1. Design and draft:
`DESIGN-ucmilp-ruc-stage-2026-10-16.md` §4. DF evidence: `FINDING-ucmilp-df-audit-2026-10-16.md`.

**Why this is not a re-test (rule 28).** `unit_commitment_milp` × SPP reads R on U4 (uc-1.7, EIA-930 DF basis). Two things are
new since: the commitment demand is now SPP's own MTLF (R16; the EIA-930 DF carried a +4 % / +11.7 % reporting uplift outside
2023-09-02…2025-05-06) and the RUC pass exists (uc-1.9). `uc_reliability_commitment` × SPP is `U` (never tested).

## 0. Preconditions (zero LP, at the pin)

| check | result |
|---|---|
| keeper `frontend/data/backcast/keepers/SPP.json` | `2026-10-03-closeout-spp-nuc-keeper`, bundle `results/calibration/closeout_spp_nuc_span`, 2019–2025 |
| keeper bundle, keeper shard, `iso_configs.py` unchanged U4 pin → this pin (`git diff --quiet 7dbfe20f 60e7c6fa -- …`) | **identical** (all three) |
| branch vs pin: `src/` + `scripts/` | identical (this branch adds `docs/` only) |
| fields at the pin | U4's six + `uc_reliability_commitment`, `uc_ruc_load_basis` (admits `"iso_intraday_forecast"`, SPP backcast only), `uc_da_schedule_reuse_bundle` |
| MTLF vintages | `load-forecast-vintages` SPP 2019–25 intaken (#7279), in the SPP clean profile (`clean_profiles.py`, `only_for=("SPP",)`); no fallback, the loader raises |
| U4 digest | U4 logs record `engine.input_digest` with `input_digest_opaque_types = []` (2024 checked), so a same-pin leg can certify reuse |

## 1. Pin, control, comparator, arms

- **Pin:** `60e7c6fa754e14d4259ac6abfca6a53874834e72` (`uc-1.10`). U4b shards pin **this branch's head after this file is
  pushed**. U5 shards pin the branch head after the U4b reuse files (§1.3) are pushed. `src/` + `scripts/` equal the pin in both.
- **Control (rule 29(b), no control solve):** keeper bundle `results/calibration/closeout_spp_nuc_span`.
- **Comparator (read, never re-solved):** U4 (`docs/records/spp/ucmilp/data/ucmilp4_spp_u4_span/`, uc-1.7; 2023 never solved).

### 1.1 Arm U4b — U4 verbatim at the pin

`replay_keeper.py results/calibration/closeout_spp_nuc_span --years <y>` plus:
```
--set unit_commitment_milp=true
--set st_gas_mustrun_per_plant=false
--set coal_sync_floor_release=true
--set energy_reserve_coopt=true
--set spp_spinning_reserve_share=true
--set uc_commitment_demand_source='"da_forecast"'
```
The only intended change vs U4 is the R16 basis, inherited as the code default for SPP under `"da_forecast"`. The pin also
carries uc-1.8 (FIX-8 zone mapping, FIX-9 lean LP heuristics); see §1.4 for what that confounds.

### 1.2 Arm U5 — U4b + RUC

U4b's six lines plus:
```
--set uc_reliability_commitment=true
--set uc_ruc_load_basis='"iso_intraday_forecast"'
--set uc_da_schedule_reuse_bundle='"docs/records/spp/ucmilp/data/ucmilp5_spp_u4b_span"'
```
- RUC basis: SPP's MTLF vintage in force at the last 4-h ID-RUC cycle at least one cycle before the hour (R14; Protocols §4.4.1).
- **DA reuse (R15, a declared rule-36 exception):** each U5 leg reads `u_DA` from its own year's U4b leg. The stage raises on a
  digest mismatch, an opaque digest part or a missing year; the shard **stops and reports, never re-solves**.
- **DOF (rule 21):** zero added. Booleans, owner-ruled enums, a provenance path, and Protocols-cited clock constants already on `main`.

### 1.3 Reuse transport

After U4b composes, the lane commits the slim U4b span (no `dispatch/`, no `unit_hourly`) to `docs/records/spp/ucmilp/data/ucmilp5_spp_u4b_span/`.
It holds `uc_solve_log_<y>.json` and `hourly/uc_schedule_<y>.parquet` per year, copied byte-for-byte from the leg bundles
(sha256 checked against each shard branch). U5 shards pin that commit, so the reuse source is in the tree at a full SHA; no shard
fetches another branch.

### 1.4 G-DRIFT `7dbfe20f` (U4) → `41cd55dc` → `60e7c6fa` (zero LP; backcast path only)

| commit / file | hunk | control (UC off) | U4b | U5 |
|---|---|---|---|---|
| FIX-8 `7c93273e`: `data/commitment_demand.py`, `zone_names` plumbing in `pipeline/{solve,year,uc}.py`, `runner.py`, `scripts/run_calibration.py` | DA increment mapped onto runtime zones by name | **INERT**: `zone_names` read only inside the UC stage | **INERT-with-reason**: SPP's runtime zones are the configured zones, so the increment is bit-identical wherever uc-1.7 built a schedule (uc.py note) | same |
| FIX-9 `41cd55dc`: `model/uc/solve.py` `lean` preset | LP heuristics on | **INERT** | **LIVE** (solver path; each window optimum may move within `uc_mip_rel_gap` 1e-3) | LIVE |
| uc-1.9 `890a7834`: `scenarios.py` 3 fields (defaults off / `"actual"` / `""`, cache-key optional) | RUC + reuse fields | **INERT** | **INERT** (off) | **LIVE** |
| uc-1.9: `pipeline/solve.py` RUC block | P1a screen → P1b | **INERT** (`_uc_stage is None`) | **INERT** (`ruc_armed` False) | **LIVE** |
| uc-1.9: `model/uc/window.py` `u_floor`, `model/uc/schedule.py` `copy`/`from_frame` | add-only bound; schedule rebuild | **INERT** | **INERT** (`u_floor=None` in every DA window; new methods uncalled) | **LIVE** |
| uc-1.9: `pipeline/uc.py` `reliability_commitment`, `adopt_committed`, `UC_DA_DIGEST_VERSION`, RUC uplift columns | RUC pass; cross-run reuse; digest version pinned `uc-1.8` | **INERT** | **INERT** for the solve (the digest moves; nothing reads it without reuse) | **LIVE** |
| uc-1.10 `60e7c6fa`: `data/commitment_demand.py` (`FORECAST_ERROR_BASES`, `VintageClock`), `data/load_forecast_vintages.py`, `constants.py` (`SPP_MARKET_TIMEZONE`, `SPP_DA_RUC_FORECAST_CUTOFF_HOUR_LOCAL` 13, `SPP_ID_RUC_CYCLE_HOURS` 4), `pipeline/uc.py` intraday basis | SPP DA basis = MTLF ≤ 13:00 CPT D-1; ID-RUC basis | **INERT** (read only by the UC stage) | **LIVE** (R16, intended) | **LIVE** (+ ID-RUC basis) |
| `solve_surface.py` epoch `2026-10-18a` (`requires="unit_commitment_milp"`, SPP/CAISO), `solve_surface_declared.py`, `results/cache.py` (comment) | re-key | **INERT** (`requires` gate) | re-keys | re-keys |
| `scripts/lib/clean_profiles.py`, `regenerate_clean.py`, `scripts/lib/load_forecast_vintages/*`, `scripts/data/curate_load_forecast_vintages.py` | vintage intake into the SPP profile | not on the control's solve path | LIVE (data the basis reads) | LIVE |
| `scripts/data/derive_load_forecast_error.py` | forward profile on MTLF (R19) | INERT | **INERT** (forecast mode only) | INERT |
| `scripts/legitimacy_diagnostics.py` `run_d4_uc_ruc` | D-4 `uc_ruc` row | scoring; no row without a `ruc` block | no row | scored |
| `scripts/render_data_dictionary.py`, `scripts/lib/uc_bench.py` | docs / bench | off-path | off-path | off-path |

**The control is INERT; the keeper bundle remains the control; no control solve is owed.** U4b vs U4 is *basis + FIX-9*:
FIX-9 moves each window only within the MIP gap, so a U4b − U4 move larger than gap noise is read as the basis effect, and the
RESULT says so rather than claiming a clean isolation. U5 vs U4b is the RUC alone: same pin, same DA schedule by digest.

## 2. Readings (fixed ex ante)

Per year, **control → U4 → U4b → U5**, from `calibration_verdict.py` (rubric as on `main`) over each composed span:

1. **Gate table:** C1 per class (CC_REGULAR, ST_GAS, COAL_PRB, COAL_LIGNITE, CT_PEAKER), C3a, C3b, C3c (magnitude), C8 (ST_GAS), unserved MWh, determination.
2. **Reserve:** reserve-shortfall hours (any family; spin, contingency), P1 slack hours, spin sub-row binding hours.
3. **Basis:** commitment-demand mean increment and under-forecast hours per year (from `uc_solve_log`).
4. **RUC (U5):** trigger hours / days (slack vs reserve), episodes, swept windows, added unit-hours and added floor TWh by class
   (`ruc` block; D-4 `uc_ruc` row), RUC uplift $M (`ruc_start_usd` + `ruc_noload_usd`) and share of total uplift.
5. **Starts ÷ CEMS (M1):** CC_REGULAR, ST_GAS, COAL_PRB, COAL_LIGNITE.
6. **Engine / cost:** windows Optimal, time-limit hits, uplift % of Σλ·load, wall (P0, UC, P1a, RUC, P1b), cgroup peak.

**Contrasts:** U4b vs U4 = basis effect (with the FIX-9 caveat above); U5 vs U4b = RUC effect.

## 3. Identity adoption (R15)

A U4b year is **adopted as U5** (no U5 leg) iff its committed P1 sidecars show **zero trigger hours**: `system_<y>` P1 slack
summed over zones ≤ the trigger tolerance (HiGHS `primal_feasibility_tolerance`, 1e-7) in every hour, **and** `reserve_family_<y>`
P1 `shortfall_mw` ≤ 1e-7 in every hour. Argument: U5's DA schedule is U4b's (digest), so its P1a is U4b's P1; with no trigger
the stage returns P1a unchanged (`reliability_commitment` → `None`). The RESULT states the proof per year (max slack, max
shortfall, from the committed sidecars). **Only trigger years are solved in U5.**

## 4. Bars (U5 vs U4b, on U5's trigger years)

| # | reading | bar |
|---|---|---|
| B1 | reserve-shortfall hours, summed over trigger years and per year | ≤ ½ × U4b |
| B2 | unserved MWh, summed and per year | ≤ ½ × U4b (a year with U4b unserved 0 must stay 0) |

**Structural reading:** "RUC closes the DA-forecast seam" = B1 and B2 met, no kill. Price gates (C3a/C3b) are reported, not barred.

## 5. Kills (any ⇒ record and stop that arm, no re-tune)

1. An infeasible or time-limited RUC window (U5).
2. Add-only violation: `u_final < u_DA` in any cluster-hour. Checked twice: the stage's own raise, and zero-LP in the parent
   (U5 leg `uc_schedule.u` ≥ U4b leg `uc_schedule.u`, every row).
3. Unserved > control + 500 MWh in any year (control = keeper, 0 MWh in every year).
4. Non-determinism on a repeated leg (a relaunched year completing twice with different `uc_schedule` hashes). A U5 digest
   mismatch against U4b is reported as a determinism or recipe finding (stop that leg; never re-solve without reuse).

**Arm scope.** Kills 1, 2 and 4 stop the arm they fire in. **Kill 3 on U4b** records U4b as R but does **not** stop U5: the seam
U5 tests is exactly that shortfall (R18 charters the sequence). Kill 3 on U5 stops U5. A DA-window infeasibility in U4b is a
GATESPEC engine kill and stops U4b and U5.

A leg reclaimed by the container or blocked at the memory gate is a coverage stop, not a kill.

## 6. Verdicts

- **Vs keeper (GATESPEC kill #3), per arm:** **R** on any PASS → FAIL flip on any year / criterion / class row (C3c CAVEAT → FAIL
  from the missing attestation compared on magnitude) or on kill 3. Otherwise **K candidate** if U4's targets T1–T3 are met
  (2020 C3a ≤ +18.85 %, 2019 C3a ≤ +11.15 %, 2020 C3b ≤ 0.2725), **I** if none moves past its bar, mixed stated row by row. The
  lane recommends; it never promotes (rule 31).
- U4's 2025 flips (C3b, C1 ST_GAS) are **not** predetermined for U4b: R16 removes the 2025 +11.7 % uplift, so 2025's commitment
  demand changes.
- **RUC verdict (matrix `uc_reliability_commitment` × SPP):** K-structural if B1 and B2 are met with no kill; R on any kill; I if
  no year triggers (nothing to test) or the bars move < ½.

## 7. Solve plan (rules 16, 32–36)

- **U4b: 7 shards**, 2019–2025, one year each, launched serially ~5 min apart. Out-dir `results/calibration/ucmilp5_spp_u4b_<y>`,
  branch `claude/ucmilp5-spp-u4b-<y>`.
- **U5: one shard per trigger year**, out-dir `results/calibration/ucmilp5_spp_u5_<y>`, branch `claude/ucmilp5-spp-u5-<y>`.
- Prompts from `scripts/shard_prompt.py` (recipe above, budget 720) plus a lane appendix: memory gate, UC file checks, files
  > 95 MB split, recorded fields, wall row, kill-1 stop, keep-alive. Committed as `shard-prompts-ucmilp5-spp.txt`.
- **Memory gate (r16 ruling 1):** printed ceiling + swap ≥ **10.6 GiB** at boot, else stop before any data step. A leg whose
  cgroup peak exceeds 10.6 GiB or OOMs stops the lane's launches and goes to UC-DESK; the lane never re-bases.
- **Attempts (r15/r16):** at most 4 per year. After the 3rd failed attempt, the 4th is **held** and reported to UC-DESK; a held
  year is "held", never called a gap.
- **Wall vs reclaim (~70–75 min after launch):** U4 legs ran 30–60 min total LP (2024: 60 min), plus ~5–10 min data steps.
  Projected U4b: 35–70 min; **2024 is at the edge**. U5 trigger leg: P0 + digest + P1a + RUC + P1b ≈ 10–25 min (DA windows
  reused). A leg reclaimed before its bundle is pushed counts as an attempt; the lane stops and reports rather than splitting a year.
- **Keep-alive:** shards re-arm their log watcher or a `send_later` at ≤ 90 min (25 recommended) while the solve runs.
- **Each leg:** fetch; `git ls-tree -r <sha> -- <out-dir>` non-empty; check out; verify `dispatch/<y>_P1.parquet`, `uc_schedule`,
  `uc_uplift`, `uc_solve_log`, `unit_marginal`, `reserve_family` bytes; then archive (rule 33).
- **Compose and score in the parent (zero LP):** `_ucmilp_compose_span.py` with UC-4's disclosed scratch workaround;
  `calibration_verdict.py` via local probe registration (`.git/info/exclude`, never committed); regenerated
  `legitimacy_diagnostics.json`.
- **Records-only PR** on `claude/ucmilp-5-spp` (not merged; UC-DESK merges): this file, prompts, RESULT, slim spans
  `ucmilp5_spp_u4b_span/` and `ucmilp5_spp_u5_span/` (U5 slim = solved trigger years; adopted years cited to U4b), SPP matrix cells
  `unit_commitment_milp`, `uc_reliability_commitment`, `uc_commitment_demand_source`. No registration, no promotion, nothing
  deleted (rule 31).

## 8. DO NOT REDO

No `--set` beyond §1. No `uc_*` value other than the declared defaults and §1.2. No control solve. No re-solve of a U4 leg.
`uc_ruc_load_basis="actual"` is not run (R14 chose the measured basis). No U5 leg without reuse.

## Addendum A (2026-10-18, before any U5 shard) — U4b launch record, trigger years, reuse transport, zero-LP expectation

UC-DESK (03:09Z) accepted §§1–5 as written, including the kill scope, and asked that every U4b − U4 table say **basis + FIX-9**.

**U4b legs** (pin `7b13f521`; one attempt each, none reclaimed, every gate passed; all 365/365 windows Optimal, 0 time-limit hits):

| year | session | leg commit | wall s | cgroup peak GiB | trigger h / days | U4b unserved MWh |
|---|---|---|---|---|---|---|
| 2019 | `session_014oueodLWfePRw4LXvcTAGV` | `9d02bc67` | 3,706 | 8.46 | 10 / 5 | 137 |
| 2020 | `session_01SC7d9mKVdgnAFca3riEvNU` | `30503285` | 2,895 | 7.97 | 6 / 4 | 0 |
| 2021 | `session_01B7Q3ztAtDyQ4SUC83Xe1UH` | `7785a5fd` | 2,092 | 8.75 | **0 / 0** | 0 |
| 2022 | `session_01QbueK2mGJu4XR1VEdi6oN8` | `f2192a33` | 2,782 | 8.21 | 13 / 5 | 761 |
| 2023 | `session_01YUyQrKV8NTWJjUaQxCKVmL` | `e42a97b3` | 2,387 | 8.19 | 49 / 15 | 2,656 |
| 2024 | `session_01NMArKz58zYF1XY4Df3etfy` | `22481a70` | 5,025 | 7.91 | 20 / 6 | 0 |
| 2025 | `session_014xZVNTVCnwBrCpthLh9iLk` | `491d3bb2` | 2,612 | 7.92 | 17 / 5 | 3,623 |

- **Kill 3 fires on U4b** (unserved > 500 MWh: 2022, 2023, 2025). Per §5 that records U4b R and does not stop U5.
- **Identity adoption (§3):** 2021 only. Committed sidecars: max P1 slack 0.0, max `reserve_family` shortfall 0.0 (≤ 1e-7). U5 2021 ≡ U4b 2021.
- **U5 legs:** 2019, 2020, 2022, 2023, 2024, 2025.
- **Reuse transport (§1.3):** `docs/records/spp/ucmilp/data/ucmilp5_spp_u4b_span/{uc_solve_log_<y>.json, hourly/uc_schedule_<y>.parquet}`,
  each byte-identical to its leg branch blob (`git hash-object` = `git rev-parse <leg>:<path>`), `input_digest_opaque_types = []` every year.

**Zero-LP expectation, written before any U5 number (not a bar).** At U4b's trigger hours: need = slack + largest family shortfall;
DA and ID-RUC errors = MTLF − actual (`ba_forecast_error_mw`, `day_ahead` / `intraday`); "ID covers" = hours where the ID-RUC forecast
is above the DA forecast by at least the need.

| year | trigger h / days | max need MW | DA err mean MW | ID err mean MW | ID covers |
|---|---|---|---|---|---|
| 2019 | 10 / 5 | 637 | −1,768 | −752 | 8 of 10 |
| 2020 | 6 / 4 | 385 | −1,298 | −187 | 6 of 6 |
| 2022 | 13 / 5 | 531 | −1,025 | −634 | 12 of 13 |
| 2023 | 49 / 15 | 969 | −2,245 | −1,072 | 45 of 49 |
| 2024 | 20 / 6 | 1,305 | −2,039 | −992 | 17 of 20 |
| 2025 | 17 / 5 | 1,522 | −2,905 | −2,428 | **7 of 17** |

Expected: B1/B2 met in 2019–2024; 2025 is the year the ID-RUC forecast itself misses, so the RUC may not halve it. The bars are unchanged.

## Addendum B (2026-10-18 05:20Z, after U5 2024 and before any other U5 leg) — the Addendum A expectation was mis-specified

**Disclosure:** this is written after the U5 2024 leg reported, and before U5 2019, 2020, 2022, 2023 and 2025 were launched. Bars, kills
and verdict rules are unchanged; only the zero-LP *expectation* is corrected.

**U5 2024 (leg `efb35e9d`):** DA schedule reused by digest (`25fb53ab…`). RUC: 20 trigger hours, 52 windows, all Optimal, 151 unit-hours
added (CC 24, coal 61, ST_GAS 66), 9.35 GWh added floor, 0 MWh outside the swept hours. **None of the added unit-hours falls in a trigger
hour**, and the P1b reserve shortfall equals U4b's in every family-hour (max |Δ| 0.0 MW).

**Why Addendum A's "ID covers" column was the wrong test.** P1a at actual load is short by `need`, so the DA schedule already serves
`actual − need`. A RUC window on the ID-RUC basis is short only where the ID-RUC demand exceeds that, i.e. ID err > −need. Addendum A
compared the ID error with the DA error instead. The right count, from the same committed sidecars and loader:

| year | trigger h | RUC-visible h (ID err > −need) | visible need MW·h / total need MW·h |
|---|---|---|---|
| 2019 | 10 | 1 | 285 / 2,609 |
| 2020 | 6 | 3 | 815 / 1,309 |
| 2022 | 13 | 0 | 0 / 1,500 |
| 2023 | 49 | 8 | 2,764 / 22,105 |
| 2024 | 20 | 5 | 1,482 / 9,618 |
| 2025 | 17 | 4 | 658 / 7,801 |

The RUC on the measured ID-RUC basis can see at most 0–62 % of the shortfall (≤ 15 % outside 2020). Where it can see it, it adds a slow
unit only if avoiding the reserve demand-curve penalty is worth the unit's start + no-load + minimum-load cost over its min-up time (coal
median `ut_h` 60 h). Revised expectation for the five unsolved years: **B1 and B2 not met** (2020 the only plausible exception). This
is a reading of the measured basis and the commitment-cost objective, not a reason to change either.

## Addendum C (2026-10-18, after all legs) — launch record, arm U5

U5 legs pinned `c2fe7670`, one attempt each, none reclaimed, every gate passed, digest reuse matched 6/6:
2024 `session_017tpwd9fV4StmzxJcUBMkBu` `efb35e9d` · 2023 `session_01GNqBRVSNwWRaZQ1ukxnA3m` `593e4bc0` · 2025 `session_01EGuVLtbnt6iYBBjvnrqb16` `b2e94988` ·
2019 `session_01QsjMStjBgpYZXynLPNAEsu` `f9399a0d` · 2020 `session_01XhoXwoJ3Tcs2KsKcrWpo4M` `33822e75` · 2022 `session_01CPJEACLcrWHXyPddKDHeLe` `5a08ee13`.
Readings and verdicts: `RESULT-ucmilp5-spp-2026-10-18.md`.
