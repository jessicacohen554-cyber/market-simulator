# FINDING — lane NWPP-20: NWPP is registered (the pin flip)

**Lane:** NWPP-20 (desk r#4 charter, 2026-09-14) · **Model:** Fable · **Base:**
`d083b0b14b5c5bfb3aed8877859d309f7ddca4d1` (= `origin/main` at issuance) ·
**Branch:** `claude/nwpp-20-register-hlgraw` · **PRECOMMIT:**
`docs/handoffs/PRECOMMIT-nwpp-20-2026-09-14.md` · **DATA PROFILE:** `nwpp`
(1.3 GB measured; the `code` profile is not enough because the fleet parquet
extension and the pool-frame tests read `data/raw/eia-860` and the 17 member
extracts).

## 0. Result

NWPP is the eighth registered region. `get_iso_config("NWPP").validate_topology()`
is green, `SUPPORTED_ISOS` / `SURFACE_ISOS` / `DEMAND_LOADERS` carry it in the same
commit (gate G1), every §2.3 row is either done or a declared exclusion (§1), gate
G8 holds — **zero moved solve-surface rows for every existing region and all 19
stored keeper configs across the seven incumbent regions re-derive byte-identical
`cache_key()`s** (§2) — and the `ISO_TO_BA_CODE` 17→1 inversion is closed at every
consumer with a codes-tuple plus membership, the curated fleet reproducing the
post-adjudication census **939 plants / 1,930 generators / 98,238.1 MW** (§3).

No solve was run (charter: run no solve). No ScenarioConfig field was added, no
default flipped, `results/cache.py` untouched, nothing added to the scorer.

## 1. Plan §2.3, row by row (re-measured at `d083b0b1`)

Preconditions re-measured at my own base: `SUPPORTED_ISOS` 7, `SURFACE_ISOS` 7,
`mech_matrix.ISO_ORDER` 9, matrix `isos` 9 (PRECOMMIT §1). After this lane:
`SUPPORTED_ISOS` = `SURFACE_ISOS` = `('ERCOT','CAISO','MISO','PJM','NYISO','NEISO','SPP','NWPP')`.
The matrix stays at 9 — NWPP-21 owns it (row "Matrix" below).

| # | §2.3 row | Status | Where / evidence |
|---|---|---|---|
| 1 | Builders + demand loaders (same commit) | **DONE** | `config/iso_configs.py::_nwpp_config` + `_ISO_BUILDERS["NWPP"]`; `data/eia930/demand.py::DEMAND_LOADERS["NWPP"] = _load_nwpp_hourly_demand`; the import-time assert passes. One commit. |
| 2 | Solve-surface fingerprint | **DONE, zero moves** | `config/solve_surface.py::SURFACE_ISOS += "NWPP"`. `config/solve_surface_declared.py` is **not edited**: declarations are per surface NAME (all 305 names already declared — `check_cache_key_registration.py` check 5 passes: "305 solve-surface names across 7 module(s), all declared"), and `moved_rows()` treats a live per-ISO row with no declaration as *not a move* by construction, so `moved_rows("NWPP") == {}` and NWPP's key carries no `__solve_surface__`. §2 has the diff. |
| 3 | Interchange | **DONE** | `model/interchange/registry.py::INTERCHANGE_INJECTIONS["NWPP"]`; `model/interchange/spec.py::INTERFACE_NEIGHBORS["NWPP"]` = CAISO / WECC_SW / WECC_CAN (owner ruling N4; every block `enabled=False` by default); `data/eia930/envelopes.py::nwpp_net_interchange` + `_SCALAR_INTERCHANGE_ISOS["NWPP"]` (served measured schedule). `data/neighbor_price.py::_HR_GAS_ELASTIC` deliberately gains **no** key (its keys are neighbour names; NWPP's three seams price by `hr_by_year` in-window and flat `heat_rate` forward, exactly as SPP's do). |
| 4 | Constants | **DONE** | `config/constants.py`: `NUCLEAR_MONTHLY_CF` + `_BY_YEAR` (Columbia, 2023–2025 measured), `DEMAND_GROWTH_RATES`, `DATACENTER_*`/`ELECTRIFICATION_*` = `{}`, `RENEWABLE_AVG_CF`, `RENEWABLE_INSTALLED_MW`, `WEATHER_YEAR_POOL`, voluntary = `None`. `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` (card N3): not touched — the monthly hydro budget is `build_nwpp_hydro_monthly.py`'s artifact (NWPP-12) and NWPP has no plant-specific period override; the registry default applies. Every value cited in-line (rule 5). |
| 5 | Capacity market — absence | **DONE (absent, documented)** | `config/capacity_market.py`: NWPP absent from `MARKET_DESIGN`, `_CURVE_ISOS`, `_CAPACITY_ISOS` and `CAMPD_BINNING_ISOS`, each absence carrying a card-N7 / N8 comment; present in `STORAGE_BASE_FLEET_MW`, `STORAGE_DEPLOYMENT_CEILING`, `STORAGE_ANNUAL_BUILD_CAP`, `PLANNING_RESERVE_MARGIN_BY_ISO` (0.144, one scalar, two-regime mismatch declared), `ADEQUACY_EXTERNAL_TIE`, `STATE_RPS_FLOORS` (all zero), `QUEUE_CAP_GW`, `QUEUE_CAP_PER_TECH`. |
| 6 | Zone assignment (BA-keyed, not state) | **DONE** | `data/zone_assignment.py`: `_NWPP_BA_ZONES` (17 BA → 5 zones), `_nwpp_admitted(ba, nerc)`, NWPP branches in `assign_zone`, `_eia860_ba_zones`, `_build_zone_lookup_cached`, `plant_state_lookup`; `_zone_from_location` **raises** for NWPP ("zones are whole-BA groups"). Membership pinned equal to `models.NWPP_BAS` by test. |
| 7 | Renewables / fuel / reserves | **DONE / DONE / documented absence** | `data/renewables.py`: `_UNCURTAILED_FALLBACK_ISOS += NWPP`, `RENEWABLE_ZONE_ALLOCATION["NWPP"]`; `config/fuel_trajectories.py`: gas basis −0.19, coal base 2.9, sigmoid backcast gas min 2.00. `model/reserves/spec.py`: **no design** — `energy_reserve_coopt` default `False`, NWPP's contingency reserve is the Reserve Sharing Group with no organized AS market and no published curve (docstring). |
| 8 | Pipeline + runner | **DONE (one gated line) / n/a** | `pipeline/backcast_config.py`: NWPP joins the SPP coal-identity deep-merge (`iso in ("SPP","NWPP")`) so every COAL* band is 1.0 alongside the generic gas neutralization — measured: every class 1.0 on all four bands (§4). `pipeline/kwargs.py`, `pipeline/commitment.py`, `runner.py`, `scripts/run_calibration.py`: their SPP lines gate SPP-only mechanisms (`spp_gas_commitment_bridge`, `spp_curtailment_ceiling`, the SPP reserve family); NWPP carries no mechanism, so no line. |
| 9 | Data leaves | **DONE** | `data/campd.py::ISO_STATES["NWPP"]` (ID MT NV OR UT WA WY); `data/eia930/{frames,demand,envelopes}.py` (POOL frame: `_ISO_TO_HOURLY_BA["NWPP"]="NWPP"`, `_POOL_HOURLY_MEMBERS`, `_POOL_CLOCK_BA="BPAT"`, per-member `_screen_demand_dropouts`, **no** `_screen_demand_spikes`, nothing padded); `data/fleet/models.py::BA_CODE_TO_ISO` (+17) and the new `ISO_TO_BA_CODES` / `ba_codes()` / `NWPP_BAS` / `ISO_NERC_REGION_ADMISSION` / `footprint_plant_mask()`; `data/transmission_expansion.py` vintage 2024. `config/paths.py::WIND_SHAPE_DIRS` gains no entry (NWPP is not a wind-SHAPE ISO). |
| 10 | Tail threshold ×3 | **SKIPPED (declared)** | Card N2 / NWPP-13 read NO price series. `scripts/calibration_verdict.py`, `derive_actual_tail.py`, `derive_actual_amplitude.py` untouched; pinned by `test_no_tail_threshold`. |
| 11 | Multi-year set | **DONE** | `scripts/audit_keepers.py::_MULTI_YEAR_ISOS += NWPP`. |
| 12 | Memory classes | **DONE** | `scripts/run_isos_concurrent.py`: `IsoMemoryClass("NWPP", peak_gb=5.5, per_plant=False, co_opt=False)` (plan §3 default). |
| 13 | Solve workflow dropdown | **DONE** | `.github/workflows/calibration-solve.yml` options += NWPP (dropdown text only; no new workflow). |
| 14 | Matrix | **NOT MINE — NWPP-21** | `mech_matrix.ISO_ORDER` / `ISO_EV_KEY`, base `isos`, `mechanism-matrix/NWPP.js`, shard-migration test: gate G2, one commit, lane NWPP-21. This lane adds no field, so no cell line is owed. `check_mechanism_matrix.py` exit 0 (three pre-existing anchor warnings, not mine). |
| 15 | Dashboard colour | **NOT MINE — NWPP-35** | `--iso-nwpp` is minted there. |
| 16 | Data profiles (token trap) | **DONE, re-measured, pinned** | `configs/data-profiles.yaml`: tokens `nwpp` + the 13 clean BA codes + delimiter-bounded `ava`/`grid`/`pge`/`scl` hourly-interchange forms; profile `nwpp` (approx_gb 1.3 measured). `ava`, `grid`, `pge`, `wpp` refused bare — re-measured at `d083b0b1`, unchanged. Pinned in `tests/unit/config/test_data_profiles_tokens.py`. |
| 17 | Coverage sweeps | **auto-extended, green** | `test_iso_coverage.py` iterates `_ISO_BUILDERS`; NWPP satisfies queue cap, retirement/entry, carbon `None`, the no-import-node branch. |
| 18 | ~22 seven-tuple tests | **DONE** | Seven-tuples extended to eight in 16 test files; facade/curation expected sets updated; `test_hydro` unlisted count 4→5; `test_capacity` stale RPS case SPP→TVA; `test_spp_renewable_inputs` fallback-set pin += NWPP. |
| 19 | Curated fleet parquet | **DONE (extended)** | `data/raw/eia-860/eia860_generators.parquet` + the seven vintage copies extended through `process_eia860.py --rescope-from-parquet`, rewritten to be strictly additive (committed rows byte-identical, Arrow schema identical, appended rows all NWPP: canonical +1,930; vintages +1,703 / 1,704 / 1,757 / 1,775 / 1,812 / 1,831 / 1,893). |

**New per-region leaves** (each package tuple += "nwpp"): `scripts/lib/load_forecast/nwpp.py`
(edition "Participant IRP assembly (2025 cycle)", vintage 2025, `default_basis="unspecified"`,
`covered_peak_mw` rule), `confirmed_retirements/nwpp.py`, `nuclear_license_status/nwpp.py`,
`transmission_expansion/nwpp.py`. `docs/multi-iso/README.md` count → eight regions.

## 2. Gate G8 — the cache-key proof

```
$ python scripts/solve_surface_register.py --diff d083b0b14b5c5bfb3aed8877859d309f7ddca4d1 HEAD
solve surface d083b0b1… -> HEAD
  305 -> 305 names; 0 value(s) moved, 0 added, 0 removed
  NO VALUE MOVED — no ISO's key is reached by a registry change.
```

(The per-ISO projection totals on the working tree read ERCOT 0 / CAISO 0 / MISO 0 /
PJM 0 / NYISO 0 / NEISO 0 / SPP 0; NWPP's 20 live rows have no declaration and are
not moves — row 2 of §1.)

**Keeper `cache_key()` re-derivation** — every `run_config*.json` under the seven
designated keepers' bundles, constructed as `ScenarioConfig(**d["scenario_config"]).cache_key()`
on this branch and on a detached worktree at `d083b0b1`, **19/19 identical**:

| Keeper bundle | Config file | Key (base = branch) |
|---|---|---|
| `caiso275_B_gascoupling_span` | `run_config.json` / `_2023` | `bab5e9b08681e54c` |
| | `run_config_2024.json` | `2e44a9d55550e56a` |
| | `run_config_2025.json` | `3506d4d485ff212e` |
| `ercot265_receipts_five_year` | `run_config.json` / `_forward_2024_2025` | `0f89d4c5f45043f7` |
| | `run_config_carveout_2021_2022.json` | `134b04a671c81d61` |
| | `run_config_carveout_2023.json` | `c30e0c40f1d5dee2` |
| `miso255_sil_keeper` | `run_config.json` / `_2023` | `b35a8f20b73a5fbf` |
| | `_2020` / `_2021` / `_2022` | `3a0d04116c118479` / `bc66008dae312904` / `f378aaf652de32b5` |
| | `_2024` / `_2025` | `dd3ad6888d090e2c` / `4e5ff5fac1b84abf` |
| `neiso108_fuelvintage` | `run_config.json` | `28266b333667e16f` |
| `nyiso232_deleak_span` | `run_config.json` | `93be4aeb93d78283` |
| `pjm_d4_4_A` | `run_config.json` | `b05e09c319c2c5f5` |
| `spp38_span` | `run_config.json` | `6d6205e381e982c2` |

One trap for the next lane that runs this proof: a stored config carries
checkout-absolute paths (`/home/user/market-simulator/data/raw/...`), and
`_normalize_cache_key_paths` folds them to `<repo>` **only against the running
checkout's root**. Computed naively from a worktree at a different path the CAISO
keys read `35114ed717ac5e44 / 345e4226e999e345 / ff0881692f6f69c4` — a path-folding
artifact, not a move (the full payload diff showed exactly the six `*_path` fields
and the root tuple, nothing else). Re-rooting the stored paths onto the worktree
before construction restores identity, which is what the table shows.

## 3. `ISO_TO_BA_CODE` — the 17→1 inversion, closed

**Design (PRECOMMIT §3.1):** `BA_CODE_TO_ISO` stays the many-to-one source of truth
(+17 NWPP codes). `ISO_TO_BA_CODES: dict[str, tuple[str, ...]]` is derived from it
in insertion order; `ba_codes(iso)` is the membership accessor; the scalar
`ISO_TO_BA_CODE` **survives for 1:1 regions only** (a region with >1 code has no
scalar entry, pinned by `test_scalar_inverse_has_no_pool_entry`). Footprint
predicate: `footprint_plant_mask(iso, ba, nerc)` = `ba ∈ ba_codes(iso)` AND, where
`ISO_NERC_REGION_ADMISSION` names one, `nerc == "WECC"` — a registry predicate,
never a per-plant exclusion (drops plant 68906 Pine Forest Solar I, TRE, filed under
DOPD).

| Consumer | Before | After |
|---|---|---|
| `data/hydro.py:610, 642, 687` | `ba == ISO_TO_BA_CODE[iso]` | `ba.isin(ba_codes(iso))` |
| `data/fleet/eia860.py:1686` (`_load_fleet_from_parquet`) | scalar `==` | `isin(codes)` |
| `data/fleet/eia860.py:2626` (retiree window loader) | scalar `==` | `isin(codes)` |
| `data/fleet/eia860.py:2800` (mothball snapshot, `_partial_plant_exit_rows(codes)`, vintage filter) | scalar `==`, `ba_code: str` arg | `isin(codes)`, `codes: tuple` arg |
| `data/fleet/campd_bins.py:168` (oil-primary screen) | scalar `==` | `isin(codes)` |
| `data/zone_assignment.py:1214, 1242, 1450` + own `_ISO_TO_BA_CODE` map | scalar `==` | `_iso_ba_codes(iso)` (scalar map for 1:1 regions, `models.NWPP_BAS` for the pool) |
| `data/zone_assignment.py:874` | `_ISO_TO_BA_CODE["PJM"]` | unchanged — PJM-literal, 1:1 |
| `scripts/data/process_eia860.py` (3 filter sites) | `isin(BA_CODE_TO_ISO)` | `_admit_footprint(df, plant)` — BA ∈ map AND the NERC predicate; refuses loudly if a NERC-predicated region meets a plant frame with no NERC column |
| `scripts/data/curate_fleet.py` | own copy of the map | `_BA_TO_ISO = dict(BA_CODE_TO_ISO)` |
| `scripts/data/curate_hydro_plant_modes.py:218` | single-BA `_load_eha` | concat over `ba_codes(iso)` |
| `scripts/data/derive_egrid_family_heat_rates.py:149` | scalar `==` | `isin(ba_codes(iso))` |
| `scripts/lib/wind_shape.py:178` | `ISO_TO_BA_CODE.get(iso, iso)` | unchanged — reached only for `WIND_SHAPE_DIRS` regions (MISO/ERCOT/SPP), all 1:1 |
| `scripts/data/derive_pjm_rggi_zone_share.py:86` | `_ISO_TO_BA_CODE[iso]` | unchanged — PJM-only derive |
| `scripts/probes/_neiso72_*`, `_miso110_*`, `_miso109_*` | scalar | unchanged — record-only probes on 1:1 regions |
| `scripts/data/build_nwpp_{hydro_monthly,ba_hourly_from_balance}.py` | own `NWPP_BAS` tuple (NWPP-10/12, predate the registry) | unchanged; **routed** (§7) — should import `models.NWPP_BAS` |

**Assertions** (`tests/unit/config/test_nwpp_registration.py`): `len(ba_codes("NWPP")) == 17`
in ruling order; every 1:1 region's `ba_codes(iso) == (ISO_TO_BA_CODE[iso],)` and its
`footprint_plant_mask` is BA-only (`test_one_to_one_regions_are_byte_identical`,
`test_mask_is_ba_only_for_one_to_one_regions`); the curated fleet reproduces
**939 plants / 1,930 generators / 98,238.1 MW** on `nerc == WECC`
(`test_curated_fleet_reproduces_the_post_adjudication_census`). The fleet loads for
2023–2025 (445 thermal units, 29,639.8 MW dispatchable thermal), and the renewables
resolve for all three years.

## 4. Demand and the served schedule — what the LP is handed (measured)

`load_demand("NWPP", y)` (5 zones × 8,760, Pacific local year, per-member dropout
repair, `include_interchange=True` subtracting the served schedule):

| Year | Loader gross TWh | Coincident peak MW | Served TI TWh (export +) | Net-of-TI TWh | Net peak MW |
|---|---:|---:|---:|---:|---:|
| 2023 | 284.206 | 49,290 | −13.745 | 270.461 | 45,430 |
| 2024 | 290.540 | 52,564 | −12.891 | 277.649 | 48,484 |
| 2025 | 293.483 | 50,953 | −4.785 | 288.698 | 45,977 |

Gross − TI = net to the kWh in every year. The gross totals differ from the plan's
§2.5 frame totals (283.97 / 291.56 / 294.86) because those are raw all-hours sums
over 8,751–8,784 rows; the loader is the 8,760-hour local year after the per-member
screen (the NEVP 2025 17-hour dropout repair logs per member, pinned by test).
Served TI construction: PRECOMMIT §3.4 (Σ₁₇(NG_adj − D_adj) − GRID→{PNM,SRP,WALC}).

Offer bands under `backcast_config(y, "NWPP", …)`: COAL / COAL_PRB / COAL_BIT /
CC_REGULAR / CT_PEAKER / ST_GAS / CT_CHP all read committed = econ_low = econ_high =
peak = **1.0** (structural shares untouched). `use_campd_bins` is inert for NWPP:
`assembly.py:1555` gates on `config.use_campd_bins and iso in CAMPD_BINNING_ISOS`,
and NWPP is absent from the set (card N8).

## 5. Suites, guards, checks

`data/clean` was rebuilt in-session before the gates (G22:
`scripts/regenerate_clean.py`, 56 datatypes; `load-forecast` failed once on the
NWPP-12 `nwpp.csv` `#` provenance preamble and was repaired — see the list below —
and `emissions-unit-annual` was OOM-killed (`exit -9`) while two suites ran beside it
and re-run alone). Results on the working tree after every fix in this lane:

| Suite / check | Result | Not this lane's (reproduced on `d083b0b1`, see below) |
|---|---|---:|
| `tests/unit/data` | 2,199 passed, 3 failed → after fixes 2 failed | 2 |
| `tests/unit/{model,policy,pipeline,config,results}` | 3,285 passed, 5 failed → after fixes 0 lane failures (4 were the `confirmed-retirements` partition not yet built; re-run green) | 0 |
| `tests/regression` + `tests/scoring` | 2,024 passed, 33 failed → after clean + fixes: 8 lane-caused fixed, 12 clean-dependent green on re-run, remainder pre-existing | 13 |
| `tests/curation` | 894 passed, 1 failed → extended (Coyote Springs, below) → green | 0 |
| `ruff check` / `ruff format --check` | 2 errors / 3 files, all in files this lane never touched | 2 / 3 |
| `scripts/check_cache_key_registration.py` | ok: 846 fields, 301 registered, 305 surface names all declared | — |
| `scripts/check_mechanism_matrix.py` | exit 0 (3 pre-existing anchor-line warnings) | — |
| `scripts/ci_refactor_guards.py` | import-walk OK; script-refs 1 pre-existing failure | 1 |
| `scripts/audit_keepers.py` | 1 failure (S1, pre-existing), 4 warnings | 1 |
| `solve_surface_register.py --diff` | 0 moved | — |

Lane-caused failures found by the suites and fixed in-lane (each a registration
seam the plan's §2.3 did not name):

- `test_export_lce_lmp::test_every_registered_iso_has_a_dummy_base` →
  `scripts/export_lce_lmp.py::_DUMMY_BASE_LMP["NWPP"] = 36.0` (PLACEHOLDER row,
  like every row there; the SPP-34 precedent).
- `test_scenario_campaign_configs` ×3 → `configs/scenarios/nwpp_scenario_base_{2026_2030,2026_2050}.yaml`
  (the SCN-WS0 reference base: mode/iso/horizon only, byte-parallel to SPP's).
- `test_collate_scenario_campaign::test_the_sum_names_the_isos_it_is_missing` →
  seven-set pin extended to eight.
- `test_spp_renewable_inputs` fallback-set pin → includes NWPP.
- `test_retiree_window_extension` ×2 (`KeyError: 'NERC Region'`) → `_admit_footprint`
  admits on the BA key alone when the plant frame carries no NERC column and no
  NERC-predicated region is present, and refuses loudly otherwise.
- `test_nwpp_pool_frame::test_2025_dropout_repair_runs_per_member` → the pool
  frame is lru-cached; the test now clears every layer before asserting the log.
- `curate_load_forecast` (`ParserError: Expected 2 fields in line 4, saw 3`) →
  `scripts/lib/load_forecast/__init__.py::parse_unified_csv` skips exactly the
  leading `#` preamble lines (never `comment="#"`, which would truncate URL
  fragments in `source_doc`); every other ISO's CSV has zero such lines. NWPP
  partition: 83 rows, 2024–2045, three publisher editions.
- `tests/curation/test_egrid_boundary_heat_rate::test_repair_set_is_minimal` —
  **a real finding, not a pin drift.** The eGRID boundary double-count detector
  (`eia860.py::_egrid_boundary_hr_repairs`, four conditions, self-validating)
  now scans NWPP plants and accepts a second instance: **Coyote Springs (7350,
  PGE, 296 MW CC)**, whose published 13,795.8 Btu/kWh is CEMS facility 7350's
  whole heat input (which also stacks the co-located Coyote Springs II, 7931,
  BPAT, 6 m away, own `PLHTIAN` > 0, own `PLHTRT` 6,894) over the PGE plant's
  generation alone; reconciled **6.918** beside the sibling's 6.894 — the
  Riverside pattern exactly. The pin is extended to `{55641, 7350}` with the
  evidence at the constant, and the function docstring updated.

Pre-existing failures — not this lane's. Reproduced on the untouched `d083b0b1`
worktree where marked (†), otherwise classified by a message that names another
region's superseded keeper / record and by a direct key re-derivation (‡):

- † `test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact` (1.154 ≠ 1.166)
- † `test_fleet::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc` ('oil' ≠ 'gas_cc')
- † `test_persisted_identity::test_solve_surface_fingerprint_is_pinned[NYISO]` (`bd2b4657f9b5df7e ≠ 1eefed492204fab7`, 210 vs 209 rows)
- † `test_fleet_arrays_golden::test_generators_to_fleet_arrays_ercot_2023_golden` (`availability` drift vs the pre-split golden — fails on the base worktree too)
- ‡ `test_key_provenance_exceptions` ×3 — 10 NEISO forecast records (`docs/handoffs/scn-ws5b-neiso/*`, `results/ff-t3-neiso-golden/*`) do not reproduce their stored key. Re-derived on **both** trees: live keys byte-identical branch vs base for every record (e.g. `REF` → `09b7e61d88f83579` on both, stored `1b452c457ca786a6`), so the non-reproduction predates this lane.
- `test_forecast_parity::test_all_seven_keepers_resolve` / `test_check_exits_zero_on_the_current_keepers` — NYISO `gas_offer_margin_zonal_anchor_vintage` + `nyiso_st_gas_econ_bands_deleaked` armed-but-undeclared (the exact condition `.github/workflows/ci.yml` lines 26–27 already records as known) and four ERCOT GAP rows; NWPP has no keeper and is not in the sweep.
- `test_gate_a_provenance::test_live_board_passes` — NYISO and SPP `gate.a_keeper_marker` cite superseded keepers (nyiso-221, spp-36); SPP marker `complete` mismatch.
- `test_ff_readiness_battery::test_marker_state_reflects_committed_markers` — CAISO keeper id `2026-09-12-caiso-275-gascoupling` vs the pinned `2026-09-06-caiso-260-b1-demand`.
- `test_golden_manifest_provenance` ×7, `test_audit_keepers_lineage::test_e11_set_mirrors_replay_ignore`, `test_replay_keeper_strict::test_all_keeper_metas_build` — ERCOT keeper id `2026-09-09-ercot265-receipts-fallback` vs the pinned `2026-09-05-ercot248-two-config-keeper`; ERCOT partition coverage "forward STALE".
- `test_calibration_verdict::PriceAndDispatchTests::test_coverage_threshold_sits_in_an_empty_interval` (`[0.9677] != []`) — scorer, untouched by this lane.
- `ci_refactor_guards.py` script-refs (`run_calibration_full.py` names the missing `scripts/test_recorded_config_gas_anchor_mirror.py`); † `audit_keepers.py` S1 (ERCOT/CAISO/NEISO `status/*.js` stale — other regions' files, this lane may not rebuild them); ruff on three files this lane never touched (`scripts/gen_nyiso229_attestation.py`, `tests/scoring/test_audit_keepers_orphan_runs.py`, `tests/unit/data/test_unit_outage_window_hour_grain.py`).
- `regenerate_clean.py emissions-unit-annual` — `exit -9` (OOM at the 13.34 GiB cgroup ceiling) after writing 2019, twice, once with nothing else running; `scripts/data/curate_emissions_unit_annual.py` reads no ISO registry (`ISO_STATES` / `BA_CODE_TO_ISO` / `SUPPORTED_ISOS` absent), so NWPP cannot reach it. An environment limit, routed (§7).

## 6. What this lane deliberately did not do

- **No solve, no registration, no keeper, no dashboard entry.** NWPP has no
  keeper shard (`frontend/data/backcast/keepers/NWPP.json`), so `keepers/index.json`'s
  display order is untouched — it is edited "when an ISO is added/removed from the
  model" only in the sense of a keeper existing to display, and `iso_list()` would
  otherwise send `audit_keepers` after a shard that does not exist.
- **No scorer change** (`calibration_verdict.py` untouched, no `TAIL_THRESHOLD`).
- **No import node, no capacity market, no reserve design, no per-plant binning.**
- **No new ScenarioConfig field, no default flip, no `results/cache.py`,
  no `solve_surface_declared.py` edit** (row 2).
- **No other region's keeper shard / log / matrix shard, nothing under
  `frontend/data/forecast/**` or `docs/codebase-site/data/mechanism-matrix/**`, no
  plan or ledger edit** (collision rules).

## 7. Routed (outside this lane's scope)

| Item | To |
|---|---|
| `load_demand_meta("NWPP", y)` raises `No EIA-930 data` — the legacy meta parquet and the `demand-profile` clean partition have no NWPP row. Its ONLY consumer is `scripts/data/build_calibration_reference.py` (the scoring reference), which is itself seven-ISO (`ISO` tuple, single-BA eGRID/EIA-923 maps). `curate_demand_profile.MODEL_ISOS` likewise. | the reference-build card (NWPP-3x), with `curate_zonal_shares` |
| `scripts/render_data_dictionary.py::ISO_ORDER` (coverage matrix columns) — docs tooling, seven-ISO | NWPP-35 / docs desk |
| `build_nwpp_hydro_monthly.py` / `build_nwpp_ba_hourly_from_balance.py` carry their own `NWPP_BAS` tuple; should import `models.NWPP_BAS` or be pinned equal by test | NWPP-12 owner |
| BPAT TI identity failure / GRID two-resource-set seam adjudication (PRECOMMIT §3.4) | NWPP-34 / desk |
| VOLL: interim `2000.0` (WEIM hard offer cap); the LBNL-ICE derivation | desk (PRECOMMIT §3.5) |
| `docs/multi-iso/00-iso-addition-protocol.md` count sentence | docs desk |
| NV Energy data-centre load component (`DATACENTER_* = {}` here) | capx |
| D79 no-new-ISO-row limb (a new region's per-ISO surface projection is undeclared by design; whether `--declare-missing` should learn per-ISO dict entries) | cache-key owner |
| Desert Bloom re-vintage review | NWPP-12 owner |
| `audit_keepers` S1 stale `status/*.js` for ERCOT/CAISO/NEISO (pre-existing) | those lanes |
| `regenerate_clean.py emissions-unit-annual` OOM-killed at the 13.34 GiB cgroup ceiling in this container (2019 written, dies on 2020); not NWPP-sensitive | infra / clean-tree owner |
| Keeper-id pins gone stale behind the ERCOT-265 / CAISO-275 / NYISO-232 / SPP-38 promotions (`test_golden_manifest_provenance`, `test_ff_readiness_battery`, `test_gate_a_provenance`, `test_replay_keeper_strict`, `test_audit_keepers_lineage`) | those ISOs' lanes |

## Log entry

`docs/calibration-log/nwpp.md` is a shared record this lane may not create; the
desk appends this:

> **nwpp-20 — 2026-09-14.** NWPP registered as the eighth region on
> `d083b0b1` (PR from `claude/nwpp-20-register-hlgraw`). `_ISO_BUILDERS` +
> `DEMAND_LOADERS` + `SURFACE_ISOS` in one commit; `ISO_TO_BA_CODE` 17→1 inversion
> closed via `ISO_TO_BA_CODES` / `ba_codes()` / `footprint_plant_mask()`, fleet
> 939 / 1,930 / 98,238.1 MW; solve-surface diff 0 moved rows; 19/19 keeper keys
> byte-identical. Five whole-BA zones NW/OR/INLAND/EAST/SNV, WECC-catalogue TTC
> tiers, served measured interchange, no capacity market, no import node, no
> price benchmark, offer bands 1.0, VOLL interim $2,000. No solve. FINDING:
> `docs/handoffs/FINDING-nwpp-20-2026-09-14.md`.
