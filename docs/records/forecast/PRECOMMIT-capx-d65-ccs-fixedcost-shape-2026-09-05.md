# PRECOMMIT — capx D65 (Act A): the CCS retrofit's fourth seam, the fixed-cost shape field

**Lane:** capx D65 — BUILD + A/B of D64 §4 **Act A only**. **Branch**
`claude/capx-d65-ccs-scaling-gfzp6c`. **Written 2026-09-05, BEFORE any solve and before
`ccs.py` / `scenarios.py` were touched.** Binding charter: prompt pack §D65 +
`FINDING-capx-d64-2026-09-05.md` §4. Director ledger §0al, issuance row r#41.

**Act B is NOT in this lane.** `ccs_retrofit_vom_adder` stays at its shipped `8.0`; the ATB
extract is not widened; no A2 arm is solved. Ledger §3 read at session start:
**Q47 is `PRESENTED (r#41)`, NOT RULED** — so the charter stands as issued and is not re-cut.

---

## 1. What is built (zero DOF, no constant changed)

| # | item | detail |
|---|---|---|
| 1 | field | `ccs_retrofit_fixed_cost_co2_scaling: bool = False` in `scenarios.py`, beside the D50 field; `__post_init__` validator: `True` REQUIRES `ccs_retrofit_capex_co2_scaling` (no `k` without seam 1) |
| 2 | registration | `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["ccs_retrofit_fixed_cost_co2_scaling"] = "False"`, same commit as the field (the nyiso-119 discipline) |
| 3 | CLI | `--ccs-retrofit-fixed-cost-co2-scaling` / `--no-ccs-retrofit-fixed-cost-co2-scaling` on `run_full_horizon.py`, `default=None` None-sentinel (omitted ⇒ field UNSET); recorded in `run_config.json` via the resolved config |
| 4 | seam | `ccs.py::apply_ccs_retrofit` — `delta_fom_per_mw_yr` becomes the REFERENCE value computed once; per host `delta_fom = delta_fom_ref × (capex_scale if armed else 1.0)`; `mc_post` uses `vom_adder × (capex_scale if armed else 1.0)`; **the conversion applies the SAME scaled adder to `gen.vom`**; the log gains `fixed_cost_scale` and `vom_adder_per_mwh`, and `delta_fom_per_mw_yr` becomes per host |
| 5 | matrix | base row `ccs_retrofit_fixed_cost_co2_scaling` in `mechanism-matrix.js` + one appended cell line in each of the six shards (`U`/`U`; NEISO stamped from A1), LAST commit |

**Design decision, recorded not deferred silently — director ruling r#41 = D64 §4.2 option (i),
DISCLOSE AND DEFER.** `retirements.py::_THERMAL_FOM` reads FOM by fuel type
(`fixed_om_gas_cc_ccs` = 65 $/kW-yr for every `gas_cc_ccs`; `Generator` carries no per-unit FOM),
so a host converted at `k = 1.8` is screened for retirement in later years at the REFERENCE
island's FOM, not its own. Option (ii) — `Generator.fom_adder_per_kw_yr`, set at conversion to
`35 × (k − 1)` and added in the retirement FOM lookup — is a **routed successor**, not this lane's:
it touches the retirement screen and D65 stays one seam. The disclosure is written into the
`ccs.py` comment and the exit finding.

## 2. Pre-declared keys (STOP 4 is a drift check against these)

| leg | recipe | pre-declared key |
|---|---|---|
| control (committed, NOT re-solved) | `neiso-t1f` bare, golden posture | `18515067bf4d2fbe` |
| ScenarioConfig default | field absent | `e5ecd4105ada3e58` (unmoved — the field drops at `"False"`) |
| bare backcast default | field absent | `6a2845e50951394e` (unmoved) |
| A1 arm | control recipe + `ccs_retrofit_fixed_cost_co2_scaling=True` | **declared at build time in the finding, before the solve launches** |

An explicit `False` must keep the control's key (the D44 §2 rows 3–4 mechanic).

## 3. G-CTRL form 4 + G-DRIFT — NO CONTROL SOLVE (rule 29 clause b)

The control is the **committed** `results/ff-t1f-d50/neiso/` bundle at key `18515067bf4d2fbe`
(the D50 arm = the post-Q42 bare key; 39 committed converters, 2028 15 rows / 2,982.2 MW,
2029 12 / 2,996.7, 2030 12 / 2,982.6). Its `run_config.json` records `git.sha = 9e48ff6`,
`dirty: false`, `changed_files: []`.

### 3.1 Config-level drift: NIL (measured, not asserted)

Two independent measurements at HEAD `e5ac39f1`:

1. The control's own stored `config.yaml` re-resolves to **`18515067bf4d2fbe`** — unmoved.
2. `apply_iso_scenario_defaults(reference_config("NEISO", 2026, 2030, cmc, golden_posture=True,
   ccs_retrofit_capex_co2_scaling=True), "NEISO")` at HEAD is **field-identical to the stored
   config across all 784 fields (0 diffs)** and hashes to the same key.

So every config-gated hunk below is provably at the control's value: none of the gates added
since the control's solve is armed for NEISO.

### 3.2 Code-level drift: `git diff 9e48ff6 HEAD -- src/market_sim scripts/run_full_horizon.py scripts/lib`
**58 files, +4,867 / −574. EVERY hunk classifies INERT for this ISO on this recipe. ZERO LIVE.**

| # | files | classification | reason |
|---|---|---|---|
| 1 | `model/capacity_evolution/ccs.py`, `pipeline/reference.py`, `results/cache.py`, `pipeline/timing.py`, `data/benchmark_corridor.py`, `scripts/lib/zonal_sufficiency.py` | INERT | **docstring / comment only** (verified: `cache.py`'s 36 changed lines are all prose; `ccs.py`'s change is the Q42 default sentence) |
| 2 | `config/paths.py`, `config/plant_taxonomy.py`, `data/floor_mechanisms.py`, `data/outages.py`, `data/som_conduct.py`, `data/eia923.py`, `data/miso_outages.py`, `data/reserve_requirements.py`, `results/metrics.py`, `pipeline/result.py`, `pipeline/__init__.py`, `data/benchmark_corridor.py` | INERT | **dead-code removal.** Every removed symbol grepped to **0 live references** in `src/` + `scripts/` (`tag_raised`, `read_clean_outages`, `plant_state_map`, `FORECAST_PARQUET`, `YearSolveResult`, `TX_UNIT_OUTAGES_CSV`, `ERCOT_SCED_INTERVALS_PER_HOUR`, `ERCOT_DC_TIE_CAPABILITY_MW`, `load_reserve_requirements`, `load_benchmark_corridor`; the 3 surviving `is_fossil` hits are a LOCAL variable in `retirements.py`, not the deleted taxonomy helper) |
| 3 | `config/constants.py` | INERT | re-exports of new `capacity_market` symbols; `CCS_RETROFIT_HR_PENALTY_REFERENCE` removed with **0 readers**; `NUCLEAR_MONTHLY_CF_BY_YEAR["ERCOT"][2022]` added (**another ISO's branch AND a backcast year**); MISO siting shares added (**another ISO's branch**) |
| 4 | `data/fuel/{plant_prices,resolve,basis/meanzero,basis/miso}.py` | INERT | the miso-213 `skip_cells` mask, gated `config.iso == "MISO"` **and** `miso_zonal_gas_basis_skip_923_priced` — **another ISO's branch**; the `plant_prices` return-type change is all-False in forecast mode by construction |
| 5 | `data/fuel/hubs.py` | INERT | `spot_coverage` gated on `caiso_citygate_spot_coverage` — **another ISO's branch** |
| 6 | `data/offer_curves.py` | INERT | `_with_intermediate_phys` reached only under `st_gas_/ct_/cc_intermediate_split` **and** `miso_intermediate_gas_offer_margin` — **default-off flags absent from the keeper's recipe** (0-diff config proof) |
| 7 | `data/fleet/{__init__,assembly,eia860}.py` | INERT | `egrid_steam_collapse_heat_rates` gate (default off) **and** a **per-ISO artifact this ISO does not have** — only `egrid_steam_collapse_heat_rates_NYISO.csv` exists, so the loader returns `{}` for NEISO by construction |
| 8 | `model/interchange/spec.py` | INERT | the resolved-carbon border adder sits inside `use_corridors = caiso_per_hub or caiso_ref_seam` — **another ISO's branch**; informational corridor inventory |
| 9 | `model/storage.py`, `model/capacity_evolution/new_entry.py` | INERT | `locality_prices_by_zone` / `locality_cost_ratio_by_zone` default `None`; the runner passes `{}` unless the NYISO `locality_capacity_curves` gate is armed — **default-off gate absent from the recipe** |
| 10 | `model/capacity_evolution/{retirements,adequacy,evolve,__init__}.py`, `config/capacity_market.py` | INERT | the D57 clearing + D59 locality + D51 ratio + D53 sector machinery. Entry predicates all fail for NEISO: `resolve_capacity_market_supply_clearing` → `capacity_market_supply_clearing_by_iso is None`; `retirement_sector_gate` False; `adequacy_accounting_ratio_dated_net` False (resolver returns the identical `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO` value); `MarketDesign.capacity_price_per_firm_mw_yr`'s new short-circuit needs a `ClearedCapacityPrice` duck-type — a float `reserve_position` takes the byte-identical census path. `evolve.py`'s `_econ_sink` line reduces to `{} if _rec else None` when the clearing gate is off |
| 11 | `model/lp/{__init__,model,rows}.py` | INERT | the clean-region row family, entirely behind `clean_region_zone_mask is not None` / `clean_region_on`; NEISO t1f has `federal_ces_enabled=False` and `miso_clean_tier_rows=False`, so the mask is `None`. `_build_rps_region_rows`'s new `region_gen_coeff` defaults `None` ⇒ the pre-existing coefficient path |
| 12 | `policy/{federal_ces,clean_tiers}.py` | INERT | `append_federal_ces_region` returns `state_arrays` **unchanged** when `federal_ces_target_row_active(config)` is False (verified at the function's first statement) |
| 13 | `policy/cap_and_trade.py`, `runner.py` (`carbon_mc_column`) | INERT | returns the scalar `carbon_price` **as the same object** unless `program.zone_share is not None`. Measured: `zone_share` is `None` for CAISO/NYISO/**NEISO**; only PJM carries a footprint — **another ISO's branch** |
| 14 | `pipeline/solve.py` | INERT | the PERF-B `reuse_p0_from` P0-reuse is passed by **`scripts/run_calibration.py` only** (the backcast orchestrator, 2 call sites); `runner.py` never passes it ⇒ `_reuse_p0` False ⇒ the pre-existing path. The added `model is not None` guard sits under `_xwarm`, which forecast bundles run OFF (owner decision D-10). Remaining changes are **timing accounting** |
| 15 | `runner.py` (screen ledger block) | INERT | `screen_peak_demand` / `screen_requirement_mw` / `screen_entering_firm_mw` / `screen_reserve_position` are **additive ledger fields** (decision-neutral, cache-key-neutral, declared so in their own comment); they are written to the evolution ledger and feed no screen |
| 16 | `runner.py` (locality / clearing blocks), `results/export.py` (`demand_response`) | INERT | NYISO-gated; the DR exclusion needs `demand_response` pseudo-generators (NYISO SCR/EDRP) — **a per-ISO object this ISO does not have** |
| 17 | `results/outputs.py` | INERT | `derived_emissions()` fires only in `from_parquet` when the stored file has `has_emissions == False`; a fresh solve writes the array |
| 18 | `matrix.py`, `scripts/lib/{bench_stamp,outage_detect,session_score,reldeploy_zonal_report,capacity_market_demand_curve}` | INERT | scenario-matrix analysis tooling, backcast bench/attestation stamping, CAMPD measured-outage detection — **not on the forecast solve path** |
| 19 | `config/scenarios.py` (+751/−10) | INERT | the ONLY non-comment deletion is the D50 field's `False → True` Q42 flip, which the control already carries **explicitly `True`**. Everything else is new fields + prose. Proven by §3.1's 0-field-diff and key match |
| 20 | `scripts/run_full_horizon.py` (+137) | INERT | CLI surface additions only; `reference_config`'s output is field-identical (§3.1) |

**One INERT-with-note, recorded so the differencing is honest.** `results/export.py` +
`results/emissions.py` add **two NEW reported keys** to the year summary — `import_co2_t`
(import-attributed CO2) and `unserved_mwh` — declared in their own comment as *"Reported-only …
beside `emissions_mt` and NEVER inside it."* No existing metric moves; the arm's summary simply
carries two keys the control's does not, and those two keys are not differenced.

**Conclusion: all hunks INERT ⇒ G-CTRL form 4 is VALID. The committed `neiso-t1f` bundle is the
control and NO control solve is spent.**

## 4. Zero-LP Phase 0 (rule 29 step 0), run BEFORE the arm

Re-run the D64 census arithmetic **through the CODE path** (the new seam's own
`capex_scale` / scaled `ΔFOM` / scaled `vom_adder`), on the committed post-Q42 rebuilt base
fleets, and reproduce `results/calibration/capxd64_fourth_seam_census.json`'s seam-4 column
**to the MW**:

| target | census reference |
|---|---|
| PJM 2029 | `ship_mw` 1,675.478 (5 rows) → `s4_mw` **0** |
| PJM 2030 | 1,675.478 (5) → **0** |
| MISO 2028 / 2029 / 2030 | 45.54 (2) / 379.997 (3) / 529.685 (4) → **0** |
| NEISO 2028–30 | `s4_mw` **12,391.99** (87 rows) |
| NYISO 2028 | `s4_mw` **6,795.34** (65); 2029–30 6,858.41 (67) |
| CAISO 2028–30 | `s4_mw` **13,676.72** (82) |
| ERCOT 2028–30 | **0** |

**Mismatch = STOP** — the arm is not solved.

## 5. The A1 arm, pre-registered

**A1 = NEISO t1f, seam 4 alone** (~8 min): the control recipe + the new field `True`, registered
under a suffixed key with the `-pre-d65` prior preserved. NYISO (12 min) is solved as the second
RGGI witness **only if A1 moves the cap**; GOLDEN-3 **only if** A1 shows the cap unbinding or the
composition moving by more than the cap-packing unit in any year. PJM is **not** an arm (its bare
leg is D60-R2's).

**Pre-registered expectations (falsifiable, NOT gates; D64 §4.4):**
1. NEISO conversions **cap-bound (2,940–3,000 MW) every year** (control: 2,982.2 / 2,996.7 / 2,982.6).
2. The MW-weighted `er` of the 2028 converted set **falls below D50's 0.550**.
3. Every year's set **ranks by `hr`** within the in-merit hosts.
4. ERCOT / MISO, if solved: **0 rows, byte-identical**.

**STOPs (D64 §4.5 — may kill the arm, never promote it):**
1. A **`k = 1` row moving** in any ledger or log field.
2. Seam 4 alone making any **carbon-0 row clear** that the committed keeper did not, or a
   **`k > 1` host converting under A1 that did not convert in the control** in a non-cap-bound
   year (the rule-14-wrong direction).
3. Any **NEISO / NYISO year converting more than the cap**, or **ERCOT / MISO gaining a row**.
4. **Key drift**: a realized key ≠ its pre-declared value, or a collision with a committed key.
5. **Byte-inertness failing** on the committed `neiso-t1f` recipe with the field absent / `False`.

## 6. Governance

- **Rule 22:** forecast mode only, horizon 2026–2030 — no holdout year is touched.
- **Rule 25:** NEISO's matrix cell comes from NEISO's own arm; the other five ship `U`.
- **Rule 27:** every file edited locally and pushed as exact on-disk bytes; blob-verified after
  push for each ≥300-line file (`scenarios.py`, `ccs.py`, the six shards, `run_full_horizon.py`).
- **Registration order:** D60-R2's finding has **NOT** merged at this HEAD (`git log origin/main
  --grep=D60-R2` returns only its PREDECL Addendum D and STATE AT START). Registration and the
  artifact-only re-score therefore **wait**; if it is still unmerged when A1 completes, everything
  else is pushed as a **CHECKPOINT** with what is owed stated explicitly.
- **Collision care:** the field sits in the D50 block of `scenarios.py`; the validator is appended
  at the very END of `__post_init__`, so SCN-WS1a's D34-guard region (~L15557) and SCN-WS2a's
  `federal_ces_*` block (~L15584–15624) are untouched. `ccs.py` is this lane's alone this window.
  `program-status.json` / `ff-verdicts.json` are D60-R2's — not written here.
