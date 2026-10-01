# PRECOMMIT — R-NYISO-2021: extend the NYISO keeper to 2021 on corrected backcast inputs — 2026-09-25

**Session:** R-NYISO-2021 (ORCHESTRATOR, rule 32 `[R-SHARD]` (a): this container runs no LP).
**Keeper:** `2026-09-24-nyiso-r-inputs-860vintage` (bundle `results/calibration/rnyiso_span`, solved at
basis `e95436d5024fc14096eed558d6dd15a65128e524`, registered 2022–2025, determination NOT-YET on C1 + C3c).
**Precondition: MET.** PR #6587 (I-NYISO, `NYISO_reserve_requirements_{2019,2020,2021}.csv`) merged
2026-09-25T01:46Z. This lane is cut from `7c77894386f8d5b391250e3b03ffd4c0f8757d91` (main).
**Parent docs:** `docs/PRECOMMIT-r-nyiso-backcast-inputs-2026-09-24.md` (recipe §1, checks §6, data
blocks §5) and `docs/RESULT-r-nyiso-backcast-inputs-2026-09-24.md` (§8 promotion).
**Phase-0 evidence (zero LP, committed):** `results/calibration/_rnyiso2021_phase0_census.json`
(`scripts/probes/_rnyiso_phase0_census.py --years 2021`).

---

## 0. Headline, fixed before any solve

1. **The recipe is the keeper's recipe, replayed on 2021. Nothing is tuned.** Offer curves are the
   keeper's (rule 1 `[R-STRUCT]` (c)); zero new DOF.
2. **2021 is a held-out year of the keeper, registered as a run STAMPED to the keeper** (rule 30
   `[R-TOUCHPOINT-FOLD]` (a)), never composed into the keeper bundle and never a second card.
3. **A held-out result never changes the ISO determination** (rule 30 (c)). It is reported at full
   magnitude and not re-tuned on.
4. **2019 and 2020 stay DATA-BLOCKED** (NYISO solar reads the NEISO row of
   `eia_generation_profiles.parquet`, which starts at 2021; I-NYISO FINDING §2.4 carries the owner
   options). No solar-shape substitute is used for any year.

## 1. The recipe

One shard (rule 36 `[R-YEAR-ISOLATION]`), pinned to this document's commit SHA:

```
uv run python scripts/replay_keeper.py results/calibration/rnyiso_span --years 2021 \
  --set eia860_vintage_tracks_solve_year=true --set measured_coal_heat_rates=true \
  --set measured_st_heat_rates=true --set measured_cc_heat_rates=true \
  --out-dir results/calibration/rnyiso_2021
```

The four `--set` flags restate what the keeper's `meta.json` already carries (and the HEAD backcast
defaults); they keep the F1 posture visible in `run_config.json`. `measured_ct_heat_rates`,
`measured_chp_heat_rates`, `hydro_ror_split` and `nyiso_dynamic_reserve_requirements` are ON from the
keeper recipe. `replay_keeper` pins both warm-start knobs OFF. Gas: Henry Hub 2021 = $3.72
(`calibration_reference.json` `henry_hub_actual`).

**The one 2021-specific input** is `data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_2021.csv`
(#6587), read by the armed `nyiso_dynamic_reserve_requirements`. Loaded here through
`load_nyiso_reserve_requirements(2021, 8760)`: 7 families × 8,760 h. `nyca_10min_spin` 655,
`nyca_10min_total` 1,310, `nyca_30min_total` 2,620, `east_10min_total` 1,200 MW (flat);
`nyc_10min_total` mean 494.5 / max 500; `nyc_30min_total` mean 989 / max 1,000;
`seny_30min_total` mean 1,459.5 / max 1,800, with the SENY step regime switching at the sourced
2021-06-17 effective date (FERC ER21-625-003). Zero-MW hours are measured relaxations (82 h NYC-10,
97 h SENY in 2021; 49 h each in 2022, same construction). It enables the 2021 solve; at the keeper's
basis the file did not exist, so there is no 2021 result for it to drift from.

## 2. Phase-0 census (zero LP, `run_year(fleet_only=True)` on the keeper recipe)

| 2021 | pre (keeper's pre-F1 posture) | post (what the shard solves) |
|---|---|---|
| EIA-860 source | canonical `eia-860` (2025ER + COD ramp) | **`vintage_2021`** |
| thermal MW | 28,201.4 | **26,950.4** |
| class-table-priced MW | 295.7 | **35.1** |
| COAL MW | 1,487.0 (Somerset, Dunkirk, Cayuga) | **0** |
| ST_GAS MW / HR | 8,902.4 / 16.97 | 8,870.9 / **15.81** |
| CC_REGULAR MW / HR | 7,405.6 / 8.56 | 7,387.1 / 8.56 |
| CC_CHP MW / HR | 3,686.4 / 9.91 | 3,623.6 / 9.70 |
| CT_PEAKER MW / HR | 3,034.0 / 14.62 | 3,132.0 / 14.53 |
| oil MW / HR | 2,991.7 / 15.39 | 3,213.9 / **21.16** |

Post matches the parent PRECOMMIT §2 2021 row exactly (26,950.4 / 35.1). The residual class-table MW
are fuel cells and Lincoln Medical oil (1.9–7.8 MW each). Oil's 21.2 MMBtu/MWh is the year-matched
eGRID 2021 rate on low-CF peakers (parent §2). Dunkirk is status OS in `vintage_2021` and not admitted.
Hydro classifier (`curate_hydro_plant_modes.py --iso NYISO`, regenerated this session): **94
run-of-river / 70 reservoir** (the keeper's).

## 3. G-DRIFT (rule 29 (b)), `e95436d5` → `7c778943`

Scope: `git diff e95436d5 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source
data/raw/reference data/raw/NYISO-AS` — 68 files across 10 merges (#6594, #6599, #6581, #6595, #6598,
#6603, #6588, #6589, #6605, #6611).

- **Coal-subclass elimination (#6611):** the bare `COAL` class becomes the four subclasses throughout
  (taxonomy, eia860, campd_bins, arrays, outages, offer curves, reserves spec, scarcity, constants
  `MIN_STABLE_PCT_PHYSICAL`, `THERMAL_AVAILABILITY`, commitment). **INERT for NYISO**: no NYISO unit
  is coal in 2020–2024; non-coal classes pass through unchanged. The keeper's `offer_curve_by_group`
  carries `COAL` **and** all four subclasses, so `_retire_bare_coal_class` **folds (drops) the bare
  `COAL` key**. Measured on the resolved 2021 config: that is the only difference, and all 12 remaining
  groups are byte-equal to the keeper's. `offer_curve_overrides` / `offer_curve_deltas` are `{}`.
- `custom-bin-assignments.csv` (10 ERCOT rows), `campd_bins` per-year re-resolution: **INERT**,
  ERCOT-only branches.
- `eia860._mid_vintage_exit_rows_from_window`: **INERT**; `mid_vintage_exit_carry` is off.
- Short-window gas scope: **INERT**; both short-window flags are off in the keeper.
- SOCO BA boundary (`ba_membership`, `ISO_BA_JOINS`, sign windows), CISO hydro backfill, other ISOs'
  2019 ladders / RGGI shares / carbon / nuclear CF: **INERT**, other-ISO or 2019-only branches. NYISO's
  RGGI price and 2021 membership are unchanged.
- Provenance / plumbing (`key_provenance`, cache prose epochs, `translate_legacy_coal_keys`,
  `iso_config` in the fleet-only return, `paths`): **INERT**.
- `_validation-source`: **no NYISO key moved** (`calibration_reference.json` touches NWPP / SOCO /
  `generated` only; `actual_lmp` touches CAISO / MISO only).
- `NYISO-AS/requirements`: 2019–2021 **added**; 2022–2025 byte-identical.
- **LIVE hunks for the NYISO backcast: none.**

**Empirical confirmation (zero LP):** the fleet arrays (`pmax`, `heat_rate`, `availability`, `vom`,
`pmin`) rebuilt from the keeper recipe in a worktree at the basis `e95436d5` and at HEAD are
**byte-identical**: 2022 fingerprint `c7e87b7ea424c8ac` both sides (803 units); 2021
`4fe19445fa4346f7` both sides (805 units). (Both sides read this session's `data/clean`.)

**Cache key:** `moved_rows('NYISO')` now carries 7 rows (the coal-vocabulary tables plus the 2019 RGGI
row). This is a cache miss, not a different LP.

**Form 4 stands:** the keeper's committed 2022–2025 bundle remains a valid control; no control solve.

## 4. Scoring inputs (not a solve blocker, stated so it is not discovered later)

- NYISO LBMP RT actuals, EIA-923 monthly and EIA-930 cover 2021 (parent §5).
- `calibration_reference.json` carries **no NYISO 2021 block** (its builder lists NYISO 2022–2025). It
  is report/scoring-side only; no solve path reads it (checked: `run_calibration` reads it in
  `_report_year` only, plus the Henry Hub table, which has 2021). If registration requires it, the
  block is added through `scripts/data/build_calibration_reference.py` with the other ISO-years
  reproduced byte-identically. Recorded in the RESULT either way.

## 5. Leg acceptance (the parent refuses the leg if any check fails)

Run with `scripts/probes/rnyiso_compose_span.py --check-only --legs results/calibration/rnyiso_2021`,
`PIN` = this document's commit SHA, `KEEPER` = `rnyiso_span`.

- **S0, pin.** `run_config.json` `git.basis_sha` equals the pinned SHA and `dirty` is false.
- **S1, config signature.** `eia860_vintage_tracks_solve_year`, `measured_{ct,coal,st,cc,chp}_heat_rates`,
  `hydro_ror_split` true; `unit_partial_outage_windows`, `unit_outage_short_windows`,
  `unit_outage_short_windows_gas` false. The offer-curve block equals the keeper's **after folding the
  bare `COAL` key** (`FOLDED_KEYS`, §3). No other difference is admitted.
- **S2, inputs.** `campd_unit_outages.sha256 == ee778a87…aa21fa`; `thermal_tranches.sha256 ==
  a3bbd6ef…d8376` (the keeper's own `resolved_inputs`).
- **S3, fleet signature.** From `dispatch/2021_P1.parquet`: **zero coal-class units / 0 MWh**.
- **S4, hydro classifier.** 94 run-of-river / 70 reservoir.

## 6. Reporting (full magnitude, 2021)

C1–C8 and the per-year determination; class TWh vs EIA-923 (EIA-930 for wind); load-weighted hourly
price bias and MAE vs the RT actual; the §2 census. For context only, the keeper's 2022–2025 rows beside
it, never as a comparison that re-tunes anything.

**Pre-registered expectations**, fixed so they cannot be written to fit the result:

- **ST_GAS** is priced ~7 % below its pre-F1 rate (16.97 → 15.81) and **over-dispatch is the expected
  direction**, as in every keeper year (2023 +4.99 TWh is the open lever-queue item). A C1 ST_GAS FAIL
  in 2021 is the known limitation travelling, not a new finding.
- **COAL 0 MWh** (actual 2021 NYISO coal ≈ 0).
- **Oil** at the eGRID 2021 rate (21.2 MMBtu/MWh) is expected to dispatch little.
- **C3c** is expected to CAVEAT (held-out year, rubric v3.6: lone-failure condition dropped).
- **No gate is a stop condition.** A regression is reported and routed, never recovered by a
  multiplier (rule 1 (c)).

## 7. Duties

- Rule 33: fetch → check out → verify (S0–S4) → archive the shard; record the leg by full SHA as
  provenance only.
- Rule 30 (a)/(b): `dashboard_add_run.py --no-prune`, then `stamp_touchpoint_holdout.py --run-id <2021>
  --keeper-id 2026-09-24-nyiso-r-inputs-860vintage`; `build_status.py --iso NYISO`.
- Rule 35 (f): `audit_keepers --iso NYISO`, E13 must pass (the 2021 run is stamped to the keeper).
- Rule 28 (b): NYISO matrix shard evidence (2021 extends the exercised years of the F1 cells and
  `nyiso_dynamic_reserve_requirements`).
- Rule 33 (f) / 34 (e): the registered 2021 bundle (with `dispatch/`) lands on `main` through this
  lane's PR.
- Rule 31: no promotion question arises (the keeper is unchanged); the 2021 run folds to it.
