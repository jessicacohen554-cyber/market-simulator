# PRECOMMIT — UC-4-ERCOT: arm U4 (the UC with every landed mechanism ERCOT admits) at uc-1.7, all seven ERCOT years, 2026-10-15

**Written and pushed before any shard of this lane exists.** The readings, bars, kills and budgets below are fixed here. They
do not move after a number arrives (GATESPEC §5, §7.1). Lane `UC-4-ERCOT` (Opus), chartered by UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) at desk sitting r14 (`docs/uc-milp-program-plan-2026-10.md` §11 r14, PR #7265).
Branch `claude/ucmilp-4-ercot`, cut from `main` `7dbfe20f`. This file **inherits**
`PRECOMMIT-ucmilp3-ercot-ab-2026-10-14.md`, which inherits `PRECOMMIT-ucmilp-ercot-ab-2026-10-10.md`. Anything not restated
here is unchanged from those files.

**Why this lane exists.** At uc-1.5, UC-3-ERCOT read **R** with 6 real flips
(`RESULT-ucmilp3-ercot-ab-2026-10-14.md`). The UC held 3.5–5.7 GW less CC online than the keeper, and CC starts ran at
0.11–0.22× CEMS. UC-DIAG ranked the causes of that under-commitment. Since then the owner ruled on them (r13), and four
mechanisms have landed (r14). U4 is the UC-3 structurally preferred arm plus every one of those mechanisms that ERCOT
admits. It asks one question: does the UC still under-commit and raise price once its commitment physics and commitment
demand are measured ones?

## 0. Numbers already public, disclosed before launch

- **The UC-3 uc-1.5 arm** (verdict R; gate table in its RESULT §1) is this arm minus the deltas in §1.2. It is shown beside
  U4 as a reference column. It is **not** the control.
- **No U4 number exists.** No lane has solved ERCOT at uc-1.7. The FIX-7 and SPP-SPIN repros are SPP 2020 only.
- **Zero-LP, this lane's commitment-demand seam.** The ERCOT EIA-930 day-ahead forecast increment
  (`data/commitment_demand.py::ba_forecast_error_mw`, run at this pin, no LP):

| year | QA-dropped h | mean DF − actual (MW) | max (MW) | min (MW) |
|---|---|---|---|---|
| 2019 | 0 | +107 | +9,506 | −5,718 |
| 2020 | 0 | +130 | +9,114 | −4,740 |
| 2021 | 53 | +181 | +13,647 | −10,436 |
| 2022 | 0 | +112 | +8,717 | −13,350 |
| 2023 | 0 | +266 | +9,700 | −7,623 |
| 2024 | 0 | +198 | +13,174 | −6,947 |
| 2025 | 72 | +656 | +11,607 | −9,447 |

  The mean bias is small: ≈ 0.2–0.4 % of ERCOT mean load, and 2025 ≈ 1.3 %. UC-DIAG (#7249) put the peak bias at ≈ 0 for
  ERCOT. **Ex-ante expectation:** DA-forecast commitment is not expected to move ERCOT much. The per-unit `ut_h`/`mlf`
  (FINDING-ucdata-ut-unit-basis-2026-10-15 §§3, 6) and the u-gate are the deltas expected to matter. This is stated so
  that no result can be read as having been predicted after the fact.

## 1. Pin, control, arm

- **Engine pin = `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365`** (`main`, merge of #7260, engine `uc-1.7`). Shards pin **this lane
  branch's head**, which carries only this record file (plus the shard-prompt record) on top of `7dbfe20f`. Its `src/`,
  `scripts/` and `config/` trees are byte-equal to the pin's. `source_revision` is that full 40-char SHA, recorded in
  Addendum A.
- **Control (rule 29(b), no control solve):** keeper `2026-10-02-closeout-l1-coal-fuel`, bundle
  `results/calibration/closeout_ercot_l1_span`, 2019–2025. These are the same bytes UC-3 used; re-scored at its pin, the
  bundle reproduced its record (148/148 rows, 0 diffs).
- **Arm U4 (exact recipe):**

```
replay_keeper.py results/calibration/closeout_ercot_l1_span --years <y> \
  --out-dir results/calibration/ucmilp4_ercot_<y> \
  --set unit_commitment_milp=true \
  --set ercot_gas_commitment_bridge=false \
  --set uc_commitment_demand_source="da_forecast"
```

| mechanism (charter) | how it enters U4 | field / source |
|---|---|---|
| `unit_commitment_milp` on | `--set` | UC-3 arm |
| rule-19 substitution: bridge off | `--set ercot_gas_commitment_bridge=false` | UC-3 arm (the UC gate refuses the bridge) |
| DA-forecast commitment demand (r13 ruling 1) | `--set uc_commitment_demand_source="da_forecast"` | backcast path: measured EIA-930 `ERCO` DF; P1 clears on actual load (rule 4) |
| per-unit `ut_h` (epoch 2026-10-15a) and per-unit `mlf` on CEMS full hours (2026-10-15b) | **no field.** `data/clean/uc-params/ERCOT` is regenerated at the pin (`regenerate_clean.py --solve-profile ERCOT` builds `uc-params`), and both epochs' `requires="unit_commitment_milp"` gate re-keys the arm | data on `main` |
| reserve co-optimization as the keeper defines it, plus the uc-1.6 u-gate | **no field.** The keeper already arms `energy_reserve_coopt=true`, `ercot_multiproduct_as_coopt=true`, `ercot_ordc_total_reserve=true` and the rest of its AS recipe, replayed unchanged. The u-gate (`model/uc/window.py::reserve_headroom_u_terms`) is live whenever co-opt is on and the window has integer clusters | engine uc-1.6 |
| ERCOT-specific additions | **none** — no `vlr_pocket_commitment` (MISO only), no `spp_spinning_reserve_share` (SPP only; refused outside SPP), no other `uc_*` value | charter |

Every other keeper floor stays: `ercot_coal_min_config_floor`, `gas_st_netload_drag`, `coal_mustrun_per_plant`,
`reliability_floor`, the CC committed tranche and `chp_steam`. `uc_*` fields stay at their declared defaults
(`uc_slim_window=true`). Offer bands are **not** touched (rule 1; the band question belongs to UC-BANDS-ERCOT, held for the
owner). **No tuning, nothing chosen from results.**

### 1.1 G-DRIFT, keeper control → pin (zero LP)

UC-3 Addendum C classified every backcast-path hunk up to `2dd69d5a` as INERT for the control. This audit covers
**`2dd69d5a` → `7dbfe20f`**: #7253 uc-1.6, #7260 uc-1.7, #7261 SPP spin, #7262/#7264 uc-params, #7263 VLR, plus
records-only PRs. Outside `docs/`, `tests/`, `results/` and `frontend/`, 36 paths change:

| path | hunk | control (UC off) | arm U4 |
|---|---|---|---|
| `data/eia930/demand.py` | `load_zone_weights` factored out of `load_demand` | **INERT**: a pure extraction; the same calls in the same order return the same `(n_zones, T)` weights; FIX-7 G-OFF hash identical | INERT (P1 demand) and read by the commitment demand |
| `model/lp/model.py` | new kwarg `reserve_synchronized=None`; a guard runs only when it is not None | **INERT**: only `_spp_design` under `spp_spinning_reserve_share` sets it | INERT (ERCOT) |
| `model/reserves/spec.py` | SPP spin constants; `ReserveDesign.synchronized=None`; `_spp_design` branch | **INERT**: SPP-only, default off | INERT |
| `pipeline/solve.py` | `p1_kwargs_overrides` merge | **INERT**: inside the `unit_commitment_milp` block | LIVE only if the stage returns overrides (SPP spin only); `{}` for ERCOT → INERT |
| `config/scenarios.py`, `constants.py`, `solve_surface*.py` | 3 fields (`spp_spinning_reserve_share`, `uc_commitment_demand_source`, `vlr_pocket_commitment`), all default off/`"actual"` and registered at their defaults (no key moves); `COMMITMENT_DF_*`, `VLR_GROUP_MIN_COMMITTED_UNITS` | **INERT**: defaults; epochs 15a/15b `requires` the UC gate | LIVE: `uc_commitment_demand_source` (intended); epochs 15a/15b (intended) |
| `data/commitment_demand.py` | new module | **INERT**: imported only from `pipeline/uc.py` | LIVE (intended) |
| `model/uc/window.py` | uc-1.6 u-gated reserve headroom; VLR pocket rows (gated `vlr_pocket_commitment`) | **INERT** (UC-gated; importer list as UC-3 §1.1) | LIVE: u-gate (intended); VLR rows INERT |
| `model/uc/pocket.py`, `data/vlr_pocket_groups.py` | VLR | INERT | INERT (MISO only, default off) |
| `model/uc/params.py`, `model/uc/diagnose.py` | comment and diagnostic text | INERT | INERT |
| `pipeline/uc.py` | commitment-demand slicing, digest, log; spin restriction; `UC_ENGINE_VERSION="uc-1.7"` | INERT (gated) | LIVE (intended) |
| `scripts/lib/uc_params/*`, `scripts/regenerate_clean.py`, `scripts/lib/clean_profiles.py` | per-unit `ut_h`/`mlf` derivation; new clean sources | **INERT**: `uc-params` is read only by `model/uc/params.py` (UC-gated); `load-forecast-error` is forecast-lane | LIVE through the clean data (intended) |
| `scripts/data/*load_forecast_error*`, `*vlr*`, `scripts/lib/vlr_pocket_groups/*`, `data/raw/vlr-pocket-groups/*`, schemas, dictionary, `key_provenance.py`, `results/cache.py` (epoch prose), `render_data_dictionary.py`, `.gitignore`, `CHANGELOG.md` | data contract, docs, forecast lane | INERT | INERT |

**No LIVE hunk on the control path.** The keeper bundle stays the control, and no control solve is earned. **U4 − UC-3 arm**
= uc-1.6 u-gate + uc-1.7 DA commitment demand + per-unit `ut_h`/`mlf`. All three are intended, so the reference column
differs from U4 by exactly the mechanisms under test.

## 2. Readings (inherited, plus the charter's additions)

- **Targets T1–T6:** inherited (UC-3 §2 → UC-2 §2), same bars. T1 = CC_REGULAR starts vs CEMS, 2019/2020; bar: ratio into
  [0.40, 2.5] / [0.74, 1.35]. T3 = C3b 2019/2020 ≤ 0.208 / ≤ 0.204. T4 = C1 CC/PRB bars. T5 = trough prices toward actual.
- **Control readings / kill rows:** inherited §3 (every registered year; every criterion and class row; attestation
  artefacts per inherited §8 are not flips; R4 = C8 with MECH 28 removed).
- **Per year, control → U4, with the UC-3 uc-1.5 arm as reference:** C1 (every class row), C3a, C3b, C3c, C4, C8 (as scored
  and R4); unserved MWh; uplift % (Σ `uplift_usd` ÷ Σ λ·load); forced `_peak*` TWh (> 0.1 TWh = a defect-6 recurrence,
  reported to the desk); wall ÷ (P0+P1); integer clusters; time-limit hits; P1 dump MWh (the over-commitment cost of
  forecast error, FIX-7 §4).
- **Starts ÷ CEMS, reported per year for CC_REGULAR and ST_GAS (charter), plus COAL_PRB.** Model starts come from
  `uc_schedule` (integer `v`) together with the P1 on-transitions of non-integer members, on the UC-3 convention. The CEMS
  denominator is the per-unit CAMPD start count UC-3 used. Reported, not gated, except T1.
- **Commitment readings (descriptive):** mean CC and ST_GAS online GW, keeper → UC-3 → U4, over all hours, the top-100 load
  hours and actual ≤ $15 hours. The `commitment_demand` row of `uc_solve_log`. The u-gate's binding hours: reserve dual
  > 0 with integer headroom at its `u` cap.
- **Price-move diagnosis** (UC-3 §2 item list, zero LP) for every year with |ΔC3a| > 2 pp or |ΔC3b| > 0.02 vs control.

## 3. Pass bars and kills (GATESPEC §5, fixed ex ante)

**Kills** (any one ⇒ the verdict is R; the other legs still run and are reported, per the UC-3 charter precedent):

1. **An infeasible window or "no incumbent"** (engine defect): that leg stops, and its window index, hours and traceback go
   to UC-DESK. No `src/` patch.
2. **P1 infeasible after the UC:** same handling.
3. **A control flip:** PASS → FAIL against the keeper on any registered year, criterion or class row, under the inherited
   exclusions.
4. **Unserved energy above keeper + 500 MWh in any year** (charter; binding). The keeper carries 3,012.6 MWh in 2021 (Uri)
   and 0 in the other years, so the bars are 3,512.6 MWh for 2021 and 500 MWh for each other year.
5. **Non-determinism:** exercised only if a relaunched leg and its predecessor both complete; schedule hash compared.

**Pass bars (all needed for a K-candidate):** no kill; T1, T3 and T5 not wrong-sign; uplift ≤ 2 % of energy cost per year;
time-limit hits ≤ 1 % of windows. **I** if every target |Δ| is below its bar and there is no kill. Otherwise **R**. The wall
ratio is reported against the owner's 3× ceiling but not judged (D-2 deferred, r09 decision 1).

**Coverage.** A year that never solves (memory gate or budget, §4) is a **coverage gap**, not a kill. The verdict is read over
the solved years and names the gap. With fewer than 7 years, a K-candidate cannot be stated (rule 16); the best possible
reading is "no kill on the solved years".

## 4. Solve plan (rule 32; zero LP in this session)

- **Seven shards, one year each** (rules 16, 36), prompts from `scripts/shard_prompt.py --iso ERCOT --year <y> --sha <lane
  head> --lane ucmilp4-ercot --bundle results/calibration/closeout_ercot_l1_span --set unit_commitment_milp=true --set
  ercot_gas_commitment_bridge=false --set uc_commitment_demand_source="da_forecast" --budget 720`, plus lane addenda
  inherited from UC-3: detached solve, active session, `unit_hourly` unstaged, five UC artefacts required, > 100 MB split,
  kill handling. Out-dirs `results/calibration/ucmilp4_ercot_<y>`, branches `claude/ucmilp4-ercot-<y>`. Prompts are
  committed as `shard-prompts-ucmilp4-ercot.txt`.
- **Budget:** 720 min per shard. UC-3 uc-1.5 legs ran 9,150–22,700 s total, with 2021/2022 the slowest.
- **Memory gate ≥ 22.4 GiB** (charter): hard stop 2 of each shard requires `prepare_solve_container.py`'s `before:`/`swap:`
  lines to show a ceiling + swap ≥ 22.4 GiB. Below that, the shard stops before any data step and reports, which counts as a
  *blocked* attempt. A blocked year gets ≤ 4 relaunches about 30 min apart, then it is recorded as a coverage gap with the
  attempt log.
- **Launch:** serially, about 5 min apart (burst ≥ 7 rate-limits, r11). Model Opus, tag `ucmilp:UC-4-ERCOT-shard`.
- **Each leg:** fetch; `git ls-tree -r <sha> -- <out-dir>` must be non-empty; check out; verify `dispatch/<y>_P1.parquet`
  (or its parts), `uc_schedule`, `uc_uplift`, `uc_solve_log`, `unit_marginal` bytes; then archive (rule 33).
- **Compose and score in the parent, zero LP:** the UC-3 scratch composer (`data/ucmilp3_ercot_span/scripts/`) builds
  `results/calibration/ucmilp4_ercot_span`, with its recipe assertion extended to the third field. Then the local scorer
  (`score_local.py` route, which never writes the repo's `frontend/data`), `calibration_verdict.determine`, regenerated
  `legitimacy_diagnostics.json`, the flip diff and R4. Nothing is registered, promoted or deleted (rules 15, 31; E13).
- **Deliver:** a RESULT beside this file; a slim span under `docs/records/ercot/ucmilp/data/ucmilp4_ercot_span/`; the U4
  evidence in the `unit_commitment_milp` (and `uc_commitment_demand_source`) cells of `mechanism-matrix/ERCOT.js`; one
  records-only PR, which UC-DESK merges; a report to UC-DESK.

## 5. DO NOT DO

No control solve; no fourth `--set`; no `uc_*` value other than the defaults; no posture; no offer-band change; no
registration or promotion; no edit under `src/` or `scripts/`; no LP in this session.
