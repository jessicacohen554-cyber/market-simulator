# PRECOMMIT: SPP-86, coal outage share on the extract's own basis (7-year arm, no control solve)

Lane: SPP-86. Phase 0: `FINDING-spp-86-coal-floor-conduct-2026-09-26.md`.
Keeper: `2026-09-26-spp-85-netload-mask`, bundle `results/calibration/spp85_arm_span` (2019–2025),
`basis_sha` `0ff620d11d91797313f5f565b5e94ff3b123330b`. Session base: `origin/main` `9149be2c`.

**Written before any price effect of this change was computed.** The only numbers in hand are
availability and floor quantities (FINDING §1–§2) and the keeper's own committed scores.

## 1. The change (frozen now; rule 23)

- **Defect.** A coal row's removed share is `unit_capacity_mw / cap[bin]`, which takes the numerator
  from the extract and the denominator from the fleet. A single-unit plant fully out stays 2.6–2.9 %
  available (Holcomb 108), and the `coal_mustrun` floor binds on that residual at a dark meter (D-4
  per-unit conduct FAIL in 2019/20/21/22/24). Where the extract basis exceeds the bin, a unit removes
  more than its share.
- **Change.** New `ScenarioConfig.unit_outage_coal_extract_basis_share`, default False, in
  `_CACHE_KEY_OPTIONAL_FIELDS`. It widens nyiso-196's existing extract-basis construction
  (`_extract_basis_index`) from the CC groups to the coal family, and nothing else. The CC flag
  keeps its own scope. It is threaded into the standard, short and partial layers and both lay-up
  readers. Non-ERCOT. The loader raises if it is combined with `unit_outage_dispatched_bin_denominator`.
  Byte-inert off (unit tests; `tests/unit/data/test_unit_outage_coal_extract_basis_share.py`).
- **Frozen settings changed: NONE.** Same extracts (sha256 pinned in the shard check), same windows,
  same filter. Only the share basis moves. Nothing swept; no alternative basis computed.
- **Basis (rule 14 / 23).** The extract's own published `unit_pct_of_plant`, plus SPP's published coal
  outage as the direction check: the keeper's excess over it after SPP-85 was 0.61–2.48 GW, and this
  change moves 0.19–0.32 GW toward it. Never the residual.
- **Matrix.** A row, plus a cell in all nine ISO shards (rule 28(c)). SPP cell `O`, others `U`.

## 2. Zero-LP LP-input delta (FINDING §2)

- Coal availability rises +0.188 to +0.317 GW mean, every year; 1.65–2.77 TWh (PRB + LIG) available.
- The placed coal must-run floor rises +0.38 to +1.00 TWh (the incumbent floor on restored capacity).
- Holcomb's full-window availability and floor both go to 0.0.
- `pmax`, heat rate and VOM are byte-identical; no non-coal row moves.

## 3. G-DRIFT (rule 29(b)): `0ff620d1` → this PR's pinned SHA — **all INERT, form 4, no control solve**

`git diff 0ff620d1 HEAD -- src/market_sim scripts/run_calibration*.py scripts/replay_keeper.py
scripts/lib data/raw/_validation-source data/raw/reference`. At session base, 19 files, every hunk
INERT for SPP:

| hunk | why INERT for SPP |
|---|---|
| `paths.py` / `eia860.py` / `outages.py` / `runner.py` / `run_calibration.py` standby admission (`admit_standby_units`) | default-off flag, absent from the keeper recipe: `eia860_operable_statuses()` is `{"OP"}` and `_fleet_cache_dir_key()` equals `str(active_eia860_dir())` |
| `outages.unit_outage_active_units(hour_grain=)`, `arrays.py:2243` | ERCOT-only event-cap branch |
| `fuel/*` `apply_miso_winter_gas_daily_delivered` | MISO branch, default-off flag |
| `coal_fuel_inventory.reconcile_floors_to_yard_budget` + its `run_calibration.py` call | runs only under `coal_fuel_inventory_plant_grain`, off in the keeper |
| `heat_rate_years.union_fleet(klass=)` | derive-time helper; the `None` default is byte-identical |
| `key_provenance.py`, `forecast_parity_registry.py` | accounting / forecast registry, not the solve path |
| `scenarios.py` (+2 fields) | both default-off and absent from the recipe |
| `caiso-supply-consistent-demand/*` | another ISO's artifact |

Plus this PR's own hunks: the new field only, off by default.

**The committed keeper IS the control.** Arm legs are differenced against `spp85_arm_span`'s committed
per-year numbers. The shard check diffs the arm recipe against the keeper's `run_config_<Y>.json`.
That file was written after the COAL-SUB key translation (solved at `0ff620d1`), so SPP-85's bare-`COAL`
false alarm cannot recur.

## 4. Solve plan (rules 32 / 34 / 36)

- **Seven shards, one per year, 2019–2025** (SPP's full registered year set), each pinned to this doc's
  commit SHA:
  ```
  python scripts/replay_keeper.py results/calibration/spp85_arm_span --years <Y> \
    --out-dir results/calibration/spp86_arm_<Y> \
    --note "SPP-86 arm <Y>: coal outage share on the extract's own basis" \
    --set unit_outage_coal_extract_basis_share=true
  python scripts/probes/_spp86_shard_check.py --year <Y> --leg results/calibration/spp86_arm_<Y>
  ```
- **Push.** The full bundle, including `dispatch/<Y>_P1.parquet`, goes to `claude/spp86-<Y>` via a
  `.gitignore` negation plus a plain `git add` (rule 34(a)).
- **Parent.** Composes with `_rspp_compose.py --side arm --require unit_outage_coal_extract_basis_share=true`,
  attests, runs `build_dof_ledger --iso SPP --check`, scores, and registers if the owner promotes. It
  lands the composite on `main` before merge (rule 33(f)).

## 5. Expectations (directional; declared so they cannot be fitted)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all seven legs: recipe = keeper + exactly the one field; six extract sha256 match; the resolved CAMPD path is the `-netloadmask-` extract. |
| E2 | Arm − keeper, COAL (PRB + LIG) TWh **rises in every year**, bounded by §2's Δ available TWh. |
| E3 | Arm − keeper, demand-weighted price **falls or is flat in every year**. |
| E4 | **D-4: Holcomb 108's `coal_mustrun` per-unit conduct row PASSES in every year** (the lane's structural target). No new D-4 row appears. |
| E5 | C1 COAL_PRB worsens in every year where it is already long (2021/22 validation FAILs worsen; 2023–25 rise). This is the declared cost; the train tier may lose C3a / C1 margin. Reported, not re-tuned. |
| E6 | Slack and dump do not rise materially: capacity is added, never removed, except at 3–4 over-available plants. |

## 6. Recommendation rule (fixed now)

**Recommend PROMOTE iff all hold:**
- (a) E1 on every leg.
- (b) E2 in sign every year.
- (c) E6.
- (d) `build_dof_ledger --iso SPP --check` shows zero new free parameters.
- (e) E4: Holcomb's row passes in all seven years and no new D-4 row appears.

**Gate outcomes are not a criterion in either direction** (rules 1 / 14). A train-tier determination
change is reported at full magnitude and routed, not tuned. Offer multipliers stay at 0.93 everywhere.
The owner rules on promotion (rule 31).

## 7. Standing duties

- Update the SPP cell (`unit_outage_coal_extract_basis_share`) with the verdict and add the §5.7 note
  (rule 28(b)).
- Archive shards once their bytes are fetched and verified (rule 33).
- Delete nothing before the owner rules (rule 31).
- Owner housekeeping (sessions cannot delete refs): `claude/rspp-2019…2025`, `claude/spp85-2019…2025`,
  and after this lane `claude/spp86-2019…2025`.
