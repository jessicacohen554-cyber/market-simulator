# PRECOMMIT — SPP-104: CT_PEAKER forced outage from SPP's own LOLE-study EFOR (`spp_ct_lole_efor`)

Lane: SPP-104. Owner cards:
- "Build LOLE-EFOR CT swap" (2026-09-30), over the DESIGN's recommendation to record a limit;
- "Solve all 7 years" (2026-09-30), after the zero-LP census.

Design and census: `docs/handoffs/DESIGN-spp-104-ct-outage-2026-09-29.md` (§6 is the built form).
Keeper / control: `2026-09-28-spp-100-chp-scope`, bundle `results/calibration/spp100_arm_span` (git `11b72265`).
**Written before any solve. Nothing below is chosen from a solved number.**

## 1. What is built

- **Field:** `ScenarioConfig.spp_ct_lole_efor` (default False; SPP-only; cache-key optional at `False`; TIER 1).
- **Table:** `constants.SPP_LOLE_GAS_EFOR_BY_SIZE`, the 2023 SPP LOLE Report Tables 9/10 (GADS 2015–2022).
  - Summer: 0.17 / 0.23 / 0.13 / 0.12 / 0.22.
  - Winter: 0.23 / 0.28 / 0.20 / 0.16 / 0.27.
  - Size bins: ≤50 / ≤100 / ≤200 / ≤400 / ≤600 MW.
- **Per plant:** the capacity-weighted mean over its CT_PEAKER units in the EIA-860 roster
  (`outages._iso_plant_unit_capacity`, active vintage).
- **CT_PEAKER availability:** `1 − EFOR(season) − derate − POF(shoulder)`, then the unchanged summer class derate.
  - Summer is Jun–Sep; every other month takes the winter rate.
  - It replaces the WEFOR term only. `wefor_multiplier`, `SUMMER_WEFOR_SHARE` and WEFOR age escalation do not reach a
    CT row. Nothing else moves.
- **Zero free parameters.** The calendar-hour basis is SERVM's own (`ttf = ttr(1−EFOR)/EFOR`, so steady-state
  P(out) = EFOR).

## 2. Prediction (zero LP; DESIGN §6)

- **Roster coverage:** all CT plants resolve in every year (0 fallbacks).
- **CT rated unavailability:** +1.66 to +1.79 GW per year (1.54 → 3.22 GW in 2019; 1.91 → 3.70 GW in 2025).
- **Gas outage-type minus SPP published, arm:** **+0.71 / +1.45 / +2.53 / +3.75 / +1.33 / +0.52 / +2.47 GW**
  (keeper: −1.04 / −0.31 / +0.80 / +1.97 / −0.46 / −1.29 / +0.60).
- **Price:** up in every year. From the SPP-84 sensitivity: ~+0.7 / +1.4 / large (Uri) / ≈0 / +0.6 / +2.6 $/MWh
  (2019–24).

## 3. G-DRIFT (rule 29(b), form 4) — keeper `11b72265` → this PR's base `6b1e7593`

`11b72265 → 82cfdc3e` is SPP-102's audit (PRECOMMIT-spp-102 §3: all INERT). The remaining range
`82cfdc3e → 6b1e7593`, over the rule-29(b) path set:

| commit(s) | files | verdict | reason |
|---|---|---|---|
| R-CAISO-15 `8f94addb` `55ce8970` `f1de7e7f` | `renewables.py`, `model/storage.py`, `paths.py`, `run_calibration*.py` | INERT | `iso == "CAISO"` and `caiso_eia930_clock_repair` gates |
| NWPP-NEXT-10 `a168680b` | `outages.py`, `arrays.py` | INERT | `unit_outage_exit_ym_from_eia860`: default False and absent from SPP's recipe |
| NYISO-NEXT-12/13 `70baf173` `6dd5d81d` | `interchange/nyiso.py`, `run_calibration*.py` | INERT | NYISO topology / NE AC node, NYISO-gated |
| miso-286 `e44fd9fa` | `floor_mechanisms.py`, `pipeline/*`, `runner.py` | INERT | `miso_gas_ecomin_online_floor`: default False, MISO-gated |
| R-ERCOT-15 `3c398753` | `eia860.py` (`COAL_PLANT_COMMISSION_YEAR`: 56257 → 56611 Sandy Creek) | INERT | Sandy Creek is ERCOT; 56611 is not in SPP's fleet. Oklaunion's heat rate is in the ERCOT CSV, outside SPP's read path |
| SPP-102 `196d1e69` `c23608b8` | `lp/rows.py`, `reserves/spec.py`, `pipeline/*`, `run_calibration.py` | INERT | `spp_commitment_posture`: default False and absent from the keeper recipe (not promoted) |
| **this lane** | `constants.py`, `scenarios.py`, `solve_surface_declared.py`, `arrays.py`, `ct_lole_efor.py` | **LIVE only under `spp_ct_lole_efor`** | Default off; cache-key guard and `check_cache_key_registration` clean; the new constant is declared at its registration hash |

All INERT for the keeper recipe, so **the committed keeper is the control** and no control solve is spent.

**Reach, measured on the calibration path.** `run_year` fleet_only with `prb_overrides={"spp_ct_lole_efor": true}`
(the channel `replay_keeper --set` writes) records the field armed. CT rated unavailability is 3.339 GW (2024), against
the census's 3.334.

## 4. Solve plan (rule 36)

- **Seven shards, one per year 2019–2025**, pinned to this PR's merge SHA and launched in one message.
- Each shard runs
  `replay_keeper.py results/calibration/spp100_arm_span --years <Y> --set spp_ct_lole_efor=true
  --out-dir results/calibration/spp104_arm_<Y>`.
- Each shard then runs `scripts/probes/_spp104_shard_check.py` and pushes its full bundle (including
  `dispatch/<Y>_P1.parquet`) to `claude/spp104-<Y>`.
- **The parent solves nothing.** It composes with `_rspp_compose.py --side arm --require spp_ct_lole_efor=true`, then
  regenerates legitimacy diagnostics, attests, registers and scores.

## 5. Expectations (fixed before any solve)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all 7 legs |
| E2 | Every year solves Optimal within the shard budget |
| E3 | No year's unserved energy rises by more than 500 MWh over the keeper |
| E4 | D-4: no FAIL row the keeper does not carry (keeper: 7) |
| E5 | Train tier 2023–25 stays CALIBRATED; no C1/C3a/C3b/C4 status flip in 2023–25 |
| E6 | Rule-14 cross-check: arm gas outage-type within SPP's published gas outage (\|gap\| ≤ keeper's \|gap\|) in a majority of years. **Already measured zero-LP: FAILS in 6 of 7 years** (2019 +0.71 vs −1.04 is the lone improvement) |

**Reported, not gated:** per-year ΔC3a, ΔC3b, class TWh (CT_PEAKER, CC_REGULAR, COAL_PRB) and Δprice. The charter
pre-accepted ~5 pts of C3a damage in 2019/20.

## 6. Recommendation rule (fixed)

- **RECOMMEND PROMOTE** iff E1–E6 all hold (rule 1: structure, i.e. the input agrees with SPP's own measured outage).
- E6 is already known to fail, so the pre-registered recommendation is **AGAINST**. That stands unless the owner rules
  otherwise; the owner decides (rule 31).
- 2019–22 movement is reported at full magnitude and is never the basis.

## 7. Year set (rule 35(b))

SPP's registered years are 2019–2025, all on keeper `2026-09-28-spp-100-chp-scope`. This lane solves all seven.

## 8. Shard check, tested before launch

`scripts/probes/_spp104_shard_check.py` was run on three synthetic 2021 legs built from the keeper:
- the exact recipe with a perturbed price → **PASS**;
- the recipe plus a stray field (`hydro_pondage_bound`) → **FAIL** (RECIPE);
- the exact recipe with a leg identical to the keeper → **FAIL** (ARMED).

Prompt: `docs/handoffs/spp104/shard_prompt_template.txt`.

## Addendum A (2026-09-30, before any solve) — G-DRIFT over the `main` merged into this PR

The PR had a merge conflict (mechanism-matrix anchor digits only), so `origin/main` was merged into the branch. The
shards pin the resulting merge SHA, so the audit now extends over `6b1e7593 → origin/main` (the rule-29(b) path set
plus `scripts/replay_keeper.py`):

| commit | files | verdict | reason |
|---|---|---|---|
| PJM-NEXT-13 `3901ae61` | `fuel/basis/pjm_replacement.py`, `fuel/resolve.py`, `run_calibration.py`, `reference/pjm_*` | INERT | `apply_pjm_replacement_cost_fuel` returns `None` unless `pjm_replacement_cost_fuel` (default False) is set, and raises off PJM. The `resolve.py` skip leg ORs on `repl_cells is not None`, so it is unchanged when off |
| R-ERCOT-17 `2386952f` | `fuel/basis/ercot.py` | INERT | `ercot_south_texas_pooled_basis`: default False, ERCOT basis path |
| NYISO-NEXT-13 `853ff96f` | `scripts/lib/forecast_parity_registry.py` | INERT | Forecast-parity declaration only |

Still all INERT, so the committed keeper remains the control. After the merge: `check_cache_key_registration` ok,
matrix guard exit 0, and the SPP tests pass. The only failing test is the MISO solve-surface pin, which fails the same
way on `main`.
