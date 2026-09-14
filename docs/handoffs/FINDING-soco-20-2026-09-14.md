# FINDING — SOCO-20: SOCO registered as the ninth region (2026-09-14)

Lane SOCO-20 · model Fable (`claude-fable-5-1`) · branch `claude/soco-20-register-fvj01g` ·
built on `origin/main` tip `d083b0b1` (charter pin `39a1c9a1` is its ancestor; every precondition
landed between the two) · PRECOMMIT `docs/handoffs/PRECOMMIT-soco-20-2026-09-14.md` (`7e6978ee`).
Zero LP (rule 32 `[R-SHARD]` (a): the parent never solves; nothing here needed one).

**Result.** `SOCO` — the Southern Company **balancing authority**, not an ISO — is registered in
`config/iso_configs._ISO_BUILDERS` as the NINTH region, appended last — NWPP (lane NWPP-20) registered
the same day as the eighth and merged first, so this branch was rebased onto it (§0). `get_iso_config("SOCO")
.validate_topology()` is green. The seven incumbent regions' solve-surface fingerprints and keeper
cache keys are byte-identical (§3). No new `ScenarioConfig` field, no default flip, no
`results/cache.py` edit.

---

## 0. Rebase onto `origin/main` after NWPP-20 merged (owner instruction: "Rebase onto main to resolve conflicts for merge")

While this PR was open, PR #6153 (lane NWPP-20, `f2191f5d`) registered the Northwest Power Pool as the
eighth region and touched the same registries. The branch's four working commits were squashed onto the
already-merged PRECOMMIT (`7e6978ee`, auto-merged as PR #6151) and rebased onto `c6c70190`:
**55 conflicted paths** — 47 text files where both lanes appended a block at the same anchor, and the
eight EIA-860 generator parquets both lanes had rescoped. Resolution, mechanical and uniform:

- **Text: the UNION, NWPP first then SOCO** (main's order). Single-line tuples became
  `(..., "SPP", "NWPP", "SOCO")`; appended blocks were concatenated. Six seams where the shared closing
  brace had been common context (`STORAGE_BASE_FLEET_MW`, `NUCLEAR_MONTHLY_CF_BY_YEAR`,
  `DEMAND_GROWTH_RATES`, `QUEUE_CAP_PER_TECH_GW`, `_nwpp_config`'s `return`, `INTERFACE_NEIGHBORS["NWPP"]`)
  were closed by hand; three double-assignment seams (`_MULTI_YEAR_ISOS`, `_EIA860_SUPPLEMENT_ISOS`,
  `load_forecast.iso_modules`, the `calibration-solve.yml` options) were merged into one; one NWPP
  assertion the union had dropped (`test_nwpp_carries_no_default_overrides`) was restored; the
  `_ISO_BUILDERS` / `SUPPORTED_ISOS` comment now reads nine regions, NWPP eighth, SOCO ninth.
- **Parquets: main's NWPP-inclusive frame byte-for-byte + the SOCO rows** (the §4 construction re-run
  against the new base; verified per file with `.equals()` on the non-SOCO slice).
- **NWPP-20's own pins moved by exactly what registering a ninth region means**:
  `test_nwpp_is_the_eighth_registered_region` now asserts NWPP at index 7, SOCO last, nine total (it had
  asserted `SOCO not in SUPPORTED_ISOS` — the state this PR flips); `test_one_to_one_regions_are_byte_identical`
  gains `"SOCO": "SOCO"` (a single-BA region belongs in the scalar map by that test's own rule).
- **G8 re-proved on the rebased head**: `--diff origin/main HEAD` → ERCOT 0, CAISO 0, MISO 0, PJM 0,
  NYISO 0, NEISO 0, SPP 0, **NWPP 0**, SOCO 20 (its own new rows); all seven keepers' `cache_key()`
  byte-identical to the PRECOMMIT §6 baseline; `check_cache_key_registration` ok;
  `check_mechanism_matrix --base origin/main` exit 0 with nine shards.

`_ISO_TO_BA_CODE["SOCO"]` survives NWPP-20's 17→1 inversion unchanged: SOCO is a single balancing
authority, so it sits in the scalar map `ISO_TO_BA_CODE` (derived from `ISO_TO_BA_CODES` for 1:1
regions) exactly as the seven ISOs do.

---

## 1. Preconditions (charter: "confirm, do not re-litigate") — all confirmed at `d083b0b1`

| Precondition | Evidence |
|---|---|
| Cards S1, S3–S9, S11, S12 RULED | `soco-desk-ledger-2026-09.md` r#3/r#4 + the charter's verbatim r#5 five-respondent ruling |
| SOCO-10 / SOCO-11 merged | `FINDING-soco-10`, `FINDING-soco-11`; `data/raw/eia-930*/SOCO hourly.parquet` 26,304 rows; AL/GA CAMPD extracts present |
| G12 met | `data/raw/load-forecast/soco/soco.csv`: 60 rows, edition `Budget 2025 (B2025) / 2025 IRP`, vintage 2025 |
| SOCO-15 COD seam on main | `9398000d` (PR #6127); `cod_ramp.generator_online_mask` prefers the unit's own online year/month |
| SOCO-22 rubric v3.8 on main | `scripts/calibration_verdict.py` carries `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` keyed on the absent `actual_lmp.json` |
| G22 discharged (five respondents) | FERC-714 residual 3.03 / 2.92 / 1.26 % on the five; Southern Power 186 EXCLUDED |

## 2. Plan §2.3 worked row by row

Every row below names what landed, where, and how it was verified. "Verified" means a live call in
this session (`uv run --no-sync python`), not a reading of the diff.

| §2.3 row | What landed | Verified |
|---|---|---|
| **Builders + demand loaders** | `_ISO_BUILDERS["SOCO"] = _soco_config` (appended LAST; `SUPPORTED_ISOS` comment → eight); `DEMAND_LOADERS["SOCO"] = _soco_demand_source` in `data/eia930/demand.py`, same commit (`eb9d015a`) | import-time assert `DEMAND_LOADERS ⊆ SUPPORTED_ISOS` passes; `test_soco_registration::test_registration_set_is_atomic`; `load_demand("SOCO", y)` 2023/24/25 → 239.625 / 249.506 / 252.590 TWh incl. TI |
| **Solve-surface fingerprint** | `SURFACE_ISOS += "SOCO"` in `config/solve_surface.py`, same commit; `solve_surface_declared.py` untouched (a new ISO's rows inside a declared table cannot be declared — SPP-20 R-1 state) | `test_solve_surface` pins `SURFACE_ISOS == SUPPORTED_ISOS`; `--diff origin/main HEAD` → **per-ISO totals ERCOT 0, CAISO 0, MISO 0, PJM 0, NYISO 0, NEISO 0, SPP 0, SOCO 20** (§3) |
| **Interchange** | `INTERFACE_NEIGHBORS["SOCO"]`: eight DEFAULT-OFF `NeighborInterface` blocks `SOCO_TVA / SOCO_MISO / SOCO_DUK / SOCO_SCEG / SOCO_SC / SOCO_FPL / SOCO_FPC / SOCO_TAL` (hurdle 2.0, load-shape exponent 1.0, limits = 2024 Reserve Margin Study winter Avg TC, misalignment to the measured envelope stated in-line); `INTERCHANGE_INJECTIONS["SOCO"] = (apply_reference_price_seam_injections,)` (self-gates off); served schedule = measured EIA-930 Total Interchange via `soco_net_interchange` + `_SCALAR_INTERCHANGE_ISOS["SOCO"]` (card S4) | `soco_net_interchange(y)` → +10.156 / +10.807 / +13.032 TWh (net export; agrees with FINDING-soco-11 to ≤ 0.03 TWh); `test_soco_registration::test_soco_neighbour_registry_is_the_eight_default_off_blocks` (names unique across every ISO) |
| **Constants** | `constants.py`: `NUCLEAR_MONTHLY_CF["SOCO"]` + `NUCLEAR_MONTHLY_CF_BY_YEAR["SOCO"]` {2023, 2024, 2025} (derived, §4), `DEMAND_GROWTH_RATES["SOCO"]` (near 0.100707 / long 0.012559, Georgia Power B2025 only — low = mid = high, disclosed), `DATACENTER_ADDITIONS_MW["SOCO"] = {}`, `ELECTRIFICATION_LAYERS["SOCO"]` empty layers, `RENEWABLE_AVG_CF["SOCO"]` {wind 0.0, solar 0.23}, `RENEWABLE_INSTALLED_MW["SOCO"]` {wind 0.0, solar 5820.0}, `WEATHER_YEAR_POOL_BY_ISO["SOCO"] = (2023, 2024, 2025)`, `VOLUNTARY_BASELINE_ISO_WEIGHT["SOCO"] = None`; each cited in place (rule 5) | `test_iso_coverage` sweep (auto-extended by `ALL_ISOS`) green for SOCO; values table §5 |
| **Capacity market** | `capacity_market.py`: SOCO **ABSENT** from `MARKET_DESIGN`, `MARKET_DESIGN_VINTAGES`, `CAPACITY_CURVE_ELIGIBLE_BY_ISO`, the ELCC/NQC curve registries and `CAMPD_BINNING_ISOS`, each absence documented in a comment block naming card S6; PRESENT in `PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"] = 0.26` (winter; seasonal structure stated), `ADEQUACY_EXTERNAL_TIE_FIRM_MW["SOCO"] = 0.0` (TRM already net of ties), `STORAGE_BASE_FLEET_MW["SOCO"]` {low 110, mid 150, high 920}, `STORAGE_DEPLOYMENT_CEILING_MW["SOCO"] = 23_700`, `STORAGE_ANNUAL_BUILD_CAP_MW["SOCO"] = 500`, `STATE_RPS_FLOORS["SOCO"]` all 0.0, `QUEUE_CAP_GW["SOCO"] = 3.5`, `QUEUE_CAP_PER_TECH_GW["SOCO"]` | `test_soco_registration::test_soco_has_no_capacity_market`; `resolve_capacity_curve_eligible` never reached (no design) |
| **Zone assignment** | `_SOCO_STATE_ZONES = {1: SOCO_AL, 12: SOCO_AL, 13: SOCO_GA, 28: SOCO_MS}`, `_soco_zone` (ValueError on None / out-of-footprint FIPS), `_soco_admits`, `_LARGEST_ZONE["SOCO"] = "SOCO_GA"`, dispatcher branch, `_EIA860_SUPPLEMENT_ISOS += SOCO`, `_eia860_ba_zones` zones SOCO by the `State` column and REJECTS non-footprint rows with a WARNING | lookup = **413 plants** (GA 299 / AL 97 / MS 17); plant 67241 (MA) REJECTED; 55411 Hillabee → SOCO_AL; 7063 McIntosh → SOCO_AL; 6073 → SOCO_MS; `test_zone_assignment` five SOCO tests |
| **`_ISO_TO_BA_CODE`** | `_ISO_TO_BA_CODE["SOCO"] = "SOCO"` (the added r#4 row; bare index at `zone_assignment.py:1194`) | `test_soco_registration::test_balancing_authority_code_round_trips`; `BA_CODE_TO_ISO["SOCO"] = "SOCO"` in `fleet/models.py` closes the reverse map |
| **Renewables / fuel / reserves** | `RENEWABLE_ZONE_ALLOCATION["SOCO"]` {wind SOCO_GA, solar SOCO_GA}; NEW zero-capacity-fuel branch in `load_renewable_profiles` (an ISO whose `RENEWABLE_INSTALLED_MW[fuel] == 0.0` returns zero CF/cap arrays instead of raising "No EIA-930 data" — SOCO has no wind); `GAS_BASIS_DIFFERENTIAL["SOCO"] = 0.64`, `COAL_PRICE_BASE["SOCO"] = 3.2`, `COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU["SOCO"] = 2.83`; `reserves/spec.get_reserve_design` **refuses SOCO by name** (card S5: no AS market) | solar 2024 mean CF 0.223 per zone (`_eia_hourly_cf_profile`); wind arrays all-zero, shape (8760, 3); `test_soco_reserve_design_is_refused_by_name` |
| **Pipeline + runner** | `pipeline/backcast_config.py`: `_SOCO_OFFER_CURVE` = identity 1.0 on every `GENERIC_BASE_OFFER_CURVE` class × band, deep-merged for SOCO (gate G5). `pipeline/kwargs.py:301`, `pipeline/commitment.py:1373`, `runner.py:3274` — **deliberately untouched**: each SPP site is an SPP-only mechanism (co-opt log line — unreachable for SOCO since the reserve design refuses it; `spp_gas_commitment_bridge`; `spp_curtailment_ceiling`), not a per-ISO ladder SOCO falls through | `TestSocoIdentityBands` (3 tests): zero non-identity bands, structural shares generic, ERCOT/SPP untouched |
| **Data leaves** | `campd.ISO_STATES["SOCO"] = ("AL","GA","MS","FL")`; `eia930/frames._ISO_TO_HOURLY_BA["SOCO"]`; `eia930/envelopes.soco_net_interchange`; `eia930/demand._load_soco_hourly_demand` (frame "SOCO", America/Chicago hour-ending, warns on missing hours); `eia930/__init__` re-exports; `fleet/models.BA_CODE_TO_ISO`; `neighbor_price` comment (SOCO neighbours carry no `_HR_GAS_ELASTIC` key); `transmission_expansion.TRANSMISSION_BASE_STATIC_VINTAGE["SOCO"] = 2025`. `config/paths.WIND_SHAPE_DIRS` — **deliberately absent**: absence is the registry's documented no-op (no per-zone wind shape; SOCO has no wind) | `test_eia930_facade` (eight loaders); `test_transmission_facade`; 2025 demand: the 7 trailing UTC-bounded hours bridged by the frame fill and WARNED, never padded |
| **Tail threshold ×3** | **SKIPPED, all three copies** (`calibration_verdict.TAIL_THRESHOLD`, `derive_actual_tail`, `derive_actual_amplitude`) — SOCO-13 read NO price series; each site carries a comment stating the skip and its reason. `calibration_verdict.py` also gains `PINNED_CLASSES_BY_ISO["SOCO"] = _PINNED_CLASSES_COMMON` (the §2.3 row the charter itself names) — **declared here** because the charter otherwise lists that file as SOCO-22's | no `SOCO` key in any of the three dicts (grep) |
| **Multi-year set** | `audit_keepers._MULTI_YEAR_ISOS += SOCO` | `audit_keepers` import OK |
| **Memory classes** | `run_isos_concurrent.IsoMemoryClass("SOCO", peak_gb=6.0, per_plant=True, co_opt=False)` | import OK; class stated per charter |
| **Solve workflow dropdown** | `.github/workflows/calibration-solve.yml` `options += SOCO` (existing `workflow_dispatch` — no new workflow, no cron) | YAML diff 2 lines |
| **Matrix** | SOCO-21's (landed as the eighth shard, `ISO_EV_KEY["SOCO"] = "O"`) — **not touched** | `check_mechanism_matrix.py --base origin/main` exit 0: integrity OK, 9 shards, keeper stamps match |
| **Data profiles** | `configs/data-profiles.yaml`: `SOCO: tokens: [soco]` + profile `soco` (approx_gb 1.3, measured `--list` 1,423 files / 1.3 GB). **The trap re-measured on the real tree**: `soco` is a substring of NO non-SOCO `data/raw` name, so unlike SPP's `spp ⊂ DAMLZHBSPP_*` no delimiter bounding is needed | `test_data_profiles_tokens`: 5 SOCO tests incl. the collision test over `raw_entries()` and the whole-name split-child test |
| **Coverage sweeps** | `test_iso_coverage.ALL_ISOS` auto-extended; SOCO satisfies queue cap, retirement/entry, carbon `None`, and the **no-import-node** branch | all 8-ISO parametrizations green |
| **~22 seven-tuple tests** | 21 tuples extended to eight (`test_storage` ×2, `test_d62` ×2, `test_capacity` ISOS, `test_entry_vre_zone_selection`, `test_ercot_stageb_arming`, `test_miso_rps_region_arming`, `test_iso_override_precedence`, `test_voluntary_demand`, `test_forecast_bundle_xyear_warmstart`, `test_hydro` (+ unlisted count 4→5, commented), `test_outages`, `test_fleet` ×3, `test_regression_smoke`, `test_replay_keeper_strict`, `test_capacity_screen_peak_measured_hindcast`, `test_thermal_elcc_vintage_ratings`, `test_nyiso_st_gas_econ_deleak`, `test_offer_curve_base_parity`, `test_curate_load_forecast`, `test_eia930_facade`, `test_collate_scenario_campaign`, `test_transmission_facade`). Deliberate exclusions: `export_lce_lmp._DUMMY_BASE_LMP` (a price-series fixture; SOCO has no price — SOCO-13) | suites §6 |

### 2.1 What must be visible in code (charter) — where it is

- **BA, not ISO**: `_soco_config` docstring opens with it, carries the Hillabee (plant 55411, SOCO_AL)
  provenance sentence and the TVA exclusion; `zone_assignment` admission rule = SERC + AL/GA/MS/FL.
- **No capacity market**: absence comment blocks in `capacity_market.py` (MARKET_DESIGN, curve, binning).
- **No import node** (G7): three load-carrying zones, no `IMPORT_ZONE`/`IMPORT_TRANCHES` key.
- **Offer bands 1.0** (G5): `_SOCO_OFFER_CURVE`, tested class × band.
- **Two timezones, one clock** (G19): `_soco_config` docstring; loader on `America/Chicago` hour-ending
  (`build_eia930_hourly_from_raw.BA_TIMEZONE["SOCO"]`); 26,304 rows.
- **TTCs cannot bind** (S3): links `SOCO_AL↔SOCO_GA 24,400 MW`, `SOCO_AL↔SOCO_MS 4,300 MW` = the
  smaller side's EIA-860 2025 ER winter capability rounded to 100 MW, misalignment stated as in
  `_spp_config` (a within-BA planning system has no published inter-state path rating).
- **TAIL_THRESHOLD skipped ×3**, documented at each site.

## 3. Gate G8 — the cache-key proof

```
scripts/solve_surface_register.py --diff origin/main HEAD
  305 -> 305 names; 20 value(s) moved, 0 added, 0 removed
  per-ISO totals: ERCOT 0, CAISO 0, MISO 0, PJM 0, NYISO 0, NEISO 0, SPP 0, SOCO 20
```

The 20 SOCO "moves" are SOCO's own NEW rows inside declared by-ISO tables (undeclared — the SPP-20
R-1 gap; no `--declare-iso` route exists, routed §7). Keeper `cache_key()` re-derived from each ISO's
committed `run_config.json` (`frontend/data/backcast/keepers/<ISO>.json` → registry → bundle):

| ISO | keeper | key | vs PRECOMMIT §6 baseline |
|---|---|---|---|
| CAISO | 2026-09-12-caiso-275-gascoupling | `bab5e9b08681e54c` | IDENTICAL |
| ERCOT | 2026-09-09-ercot265-receipts-fallback | `0f89d4c5f45043f7` | IDENTICAL |
| MISO | 2026-09-12-miso-255-sil-measured | `b35a8f20b73a5fbf` | IDENTICAL |
| NEISO | 2026-09-09-neiso-108-fuelvintage | `28266b333667e16f` | IDENTICAL |
| NYISO | 2026-09-13-nyiso-232-st-gas | `93be4aeb93d78283` | IDENTICAL (the charter's `7e0dc0344f297fc2` was nyiso-231's keeper, superseded 2026-09-13) |
| PJM | 2026-09-11-pjm-d4-4-gasoutage | `b05e09c319c2c5f5` | IDENTICAL |
| SPP | 2026-09-13-spp-38-vintage-cache | `6d6205e381e982c2` | IDENTICAL |

`check_cache_key_registration.py`: 846 fields, 301 registered, 305 surface names, all declared, OK.
Pre-existing at the base and NOT this lane's: `moved_rows` already names `NUCLEAR_MONTHLY_CF_BY_YEAR`
for ERCOT and `NUCLEAR_MONTHLY_CF_BY_YEAR` + `STATE_CARBON_PRICE_BY_ISO` for CAISO.

## 4. Two seam repairs the registration required (each a no-op for the seven)

1. **COD-aware nuclear-CF denominator** (`scripts/data/derive_nuclear_monthly_cf.py`). `_nuclear_fleet`
   now returns the fleet pmax ONLINE in each month (a unit counts from its own `online_year/month`,
   inclusive — the SOCO-15 grain) and `derive_monthly_cf` divides by it. Without this, SOCO 2023
   Jan–Mar would read 0.72 / 0.61 / 0.60 against 0.99 / 0.85 / 0.82 on the online basis — the
   mirror image of the phantom SOCO-15 removed, since `_nuclear_monthly` sets availability = CF and
   the COD mask then multiplies. Rule 23 `[R-FROZEN-DERIVE]` scope: the trigger is SOURCE data (two
   in-window CODs in the new fleet), not a residual. `--check ERCOT CAISO PJM MISO NYISO NEISO SPP`
   → "committed table matches" for all seven; `test_soco_registration` pins the flat denominator for
   the seven and the COD steps (2023 m7, 2024 m4) for SOCO.
2. **CAES skip in `load_eia860_storage`**: rows whose Technology contains "Compressed Air" are dropped
   (McIntosh, plant 7063, is the only such row nationally). Card S7 carries it as a 25 MW gas CT in
   the thermal fleet (`_map_fuel_type` `NG`/`CE` → `gas_ct`; `pmax = net summer capacity` = 25 MW,
   the 77 % derate the source states), so the unit is represented once. SOCO 2024 storage fleet:
   SOCO_GA li_ion 146.2 MW / 424.4 MWh, SOCO_MS li_ion 1.5 / 1.5, SOCO_GA pumped_storage 1,306.6 MW /
   13,066 MWh (generator schedule); nothing in SOCO_AL.

Also required: the canonical and seven vintage `eia860_generators.parquet` files carried ZERO SOCO
rows, so `scripts/data/process_eia860.py --rescope-from-parquet` was run over all eight (the SPP-20
`3117f06a` precedent; rule 23 scope trigger). **Its output was NOT strictly additive, and the suite
caught it** (§6): the routine's last line writes the RAW rebuild whenever its columns differ from the
committed table (`df = df[committed.columns] if list(committed.columns) == list(df.columns) else df`),
so on the canonical snapshot and vintages 2020/2023/2024 it DROPPED the eGRID `heat_rate` join (8,101
populated rows on the canonical table), ADDED `planned_retirement_month`, moved
`balancing_authority_code` to the last column, and admitted one non-SOCO row (PJM plant 60781 `PV1`).
Symptoms: `test_fleet` heat-rate pins, `test_egrid_boundary_heat_rate` (Riverside 7.5 ≠ 6.88),
`test_cc_steam_part_reclass`, `test_derive_coal_sigmoid` (MISO prb 0.687 ≠ 0.694). **Repaired before
push** by rebuilding every table as **main's committed frame, byte-for-byte in main's column order and
dtypes, plus the SOCO rows only**, SOCO's plant-level `heat_rate` joined from the committed eGRID
PLNT23 cache (`egrid2023_data_rev2.18751623c0bd0d88.PLNT23.parquet`) under the same
`EGRID_HR_WINDOW_BTU_KWH` filter `_join_egrid_heat_rate` applies (366 / 398 / 379 SOCO rows matched on
canonical / 2023 / 2024; vintage 2020 mirrors main's all-null column). Verified per file: the non-SOCO
slice `.equals()` main's frame. Counts at the pre-rebase base: canonical 19,725 + 788 = 20,513;
vintages 2018–2024 +703 / +711 / +746 / +762 / +791 / +803 / +799. After the rebase onto the NWPP-
inclusive main (§0) the same construction reads canonical 21,655 + 788 = 22,443 and vintages 17,502 /
17,970 / 18,585 / 19,727 / 20,400 / 20,909 / 21,635, the non-SOCO slice again `.equals()` main's frame. The script defect is ROUTED (§7) with this recipe as
the fix — not patched here, since `process_eia860.py` is outside this lane's §2.3 regions.
Thermal fleet loaded: 393 units, 55.09 GW; nuclear 8 units incl. Vogtle 3 (2023-07) and 4 (2024-04)
with their own CODs; hydro 42 gens, 1,523.6 MW.

## 5. Registry values (the PRECOMMIT §4 table, as landed)

| Registry | Value | Source |
|---|---|---|
| zones / load shares | SOCO_AL 0.3510 · SOCO_GA 0.5842 · SOCO_MS 0.0648 | FERC-714 five respondents (2, 183, 184, 107, 210); 186 excluded (r#5) |
| links | AL↔GA 24,400 · AL↔MS 4,300 MW | smaller side's EIA-860 2025 ER winter capability, rounded to 100 |
| `voll` | 61,900 $/MWh | ICE 2 (2025$) 2-h cost/unserved kWh res $5.03 / non-res $100 × EIA-861 2024 BA=SOCO class mix res 0.4009 / non-res 0.5991 → $61,927; 8 h $32,384 and 24 h $19,447 reported; $2,000 only as the documented fallback, never carried silently |
| PRM | 0.26 (winter) | Southern 2024 Reserve Margin Study; seasonal structure stated |
| nuclear CF | 12-month table + {2023, 2024, 2025} by-year | EIA-923 over the COD-aware fleet (§4.1) |
| gas basis / coal | +0.64 $/MMBtu · $3.20/MMBtu · sigmoid min 2.83 | F923 delivered 2023–25 (basis +0.49/+0.64/+0.65; coal 3.548/3.168/2.928) |
| demand growth | near 0.100707 · long 0.012559 | Georgia Power B2025 energy 2026 102,557.4 / 2031 165,701.5 / 2044 194,890.0 GWh (GPC-only, disclosed) |
| renewables | wind 0 MW · solar 5,820 MW, CF 0.23 | EIA-860 census; 2024 measured solar CF 0.2269 |
| storage | base {110, 150, 920} MW · ceiling 23,700 · cap 500/yr | EIA-860 OP batteries 147.7 MW (mid), proposed U/V 775 (high) |
| queue caps | 3.5 GW total; wind 0 / solar 1.0 / gas_cc 1.5 / gas_ct 0.5 / nuclear 1.5 | 2023 demonstrated CODs 3.348 GW; gas_cc 1.507 (Barry A3 774.0 + Lowman 732.7) |
| `ISO_STATES` | ("AL","GA","MS","FL") | FINDING-soco-10 |

## 6. Test census and guards

**How "pre-existing" was established.** Two controls, both zero-LP. (i) `origin/main`'s `src/`,
`scripts/` and `configs/` were checked out INTO THIS TREE (same path roots, same hydrated data — whose
non-SOCO slice is byte-identical to main, §4) and the failing tests re-run; a test that fails there
is main's, not this branch's. (ii) For every cache-key question, one committed `run_config.json` per
ISO × mode (7 ISOs, backcast + forecast, 14 records) was re-keyed under main's code and under HEAD's
in the same tree: **14 / 14 IDENTICAL** — this branch moves no cache key, backcast or forecast, in
any region. (A code-only `git worktree` was tried first and REJECTED as a control for keys: its
different repo root changes `_normalize_cache_key_paths`' sentinel folding and every key with it.)

- Targeted SOCO files (`test_soco_registration` 19, `test_iso_config`, `test_data_profiles_tokens`,
  `test_backcast_config`, `test_zone_assignment`, `test_eia930_facade`, `test_transmission_facade`,
  `test_solve_surface`, `test_iso_coverage`): **293 passed, 0 failed**.
- `ruff check` / `ruff format --check` on every changed `.py`: clean.
- `scripts/check_mechanism_matrix.py --base origin/main`: exit 0 (anchor warnings pre-existing).
- `scripts/check_cache_key_registration.py`: ok (846 fields, 301 registered, 305 surface names).
- `scripts/ci_refactor_guards.py`: import-walk OK; **script-refs 1 FAILURE, PRE-EXISTING on
  `origin/main`** — `scripts/run_calibration_full.py` references the missing
  `scripts/test_recorded_config_gas_anchor_mirror.py` (untouched by this branch; absent from main's
  tree too). Routed §7.
- **Full suites on the pushed state** (`ab4205a9`):

  | Suite | passed | failed | skipped | wall |
  |---|---|---|---|---|
  | `tests/unit` | 5,475 | 7 | 44 (+1 xfail) | 13:00 |
  | `tests/curation` + `tests/regression` | 1,382 | 11 | 15 | 4:48 |

  Every one of the 18 remaining failures is classified in §6.1; **none is this branch's**. Before
  the parquet repair and the two loader fixes the same runs read 14 + 14 failures; the 10 that moved
  are the ones this lane caused and fixed (rows marked "was this branch's" / "fixed by the repair").

### 6.1 Failures remaining after the parquet repair and the two loader fixes — all pre-existing

| Test | Symptom | Control (i) on main's code, same tree | Class |
|---|---|---|---|
| `test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact` | 1.154 ≠ 1.166 | FAILS | artifact/registry drift, both files last touched by PR #6037; neither on this branch |
| `test_fleet::TestLoadRetiredWithinWindow::test_neiso_includes_mystic_cc` | Mystic 7 / GT1 read `oil` | FAILS | retiree parquet (untouched here) carries the oil steam unit and GT1 under plant 1588 |
| `test_fleet_arrays_golden::test_generators_to_fleet_arrays_ercot_2023_golden` | `availability` hash | FAILS | ERCOT `NUCLEAR_MONTHLY_CF_BY_YEAR` already off its declaration at the base (PRECOMMIT §6) |
| `test_capacity::TestGetRPSTarget::test_unregistered_iso_is_none` | `get_rps_target("SPP")` is 0.0 | FAILS | main's `STATE_RPS_FLOORS` carries SPP since SPP-60; test still asserts None |
| `test_persisted_identity::test_solve_surface_fingerprint_is_pinned[NYISO]` | 210 rows ≠ 209 declared | FAILS | NYISO surface row added on main without `--declare` (measured 210 rows at the base, before any edit) |
| `test_key_provenance_exceptions` (3) | 10 NEISO forecast records do not reproduce | FAILS identically (and control ii: recomputed keys IDENTICAL under both codes) | recorded `1c5c40a4…` vs recomputed `aaecf1bb…` on BOTH codes — pre-existing drift of `scn-ws5b-neiso` / `ff-t3-neiso-golden` records, a SIXTEENTH for the NEISO/forecast owner to report, not this lane's to append |
| `test_derive_coal_sigmoid::TestProvenanceFreeze::test_miso_defaults_match_derive` | 0.687 ≠ 0.694 | — | was CAUSED by the non-additive rescope (heat_rate dropped) and is FIXED by the repair (§4); passes on the pushed state |
| `test_egrid_boundary_heat_rate`, `test_cc_steam_part_reclass`, `test_fleet` heat-rate pins | Riverside 7.5 ≠ 6.88 etc. | — | same cause, same fix; pass on the pushed state |
| `test_vintage_retirement_ramp` storage ×3 | `KeyError: 'Technology'` | — | WAS this branch's (CAES filter on a fixture without the column); fixed by the `if "Technology" in df.columns` guard |
| `test_export_lce_lmp::test_every_registered_iso_has_a_dummy_base` | no SOCO row | — | WAS this branch's by construction (the guard enumerates `SUPPORTED_ISOS`); fixed with the placeholder row, documented as never a price claim |
| `test_soundness::TestEndToEnd` (6), `test_export::TestExportScenarioJson` (4), `test_consume_phase3d::EgridZoneAssignmentParity` | `FileNotFoundError` under `data/clean/` | FAILS | environmental: `data/clean` is derived and gitignored and this session did not regenerate it; not a code failure |

### 6.2 CI on PR #6152 (head `926f19dc`) — seven red checks, one of them this branch's

| Check | Failure | This branch? | Evidence |
|---|---|---|---|
| Fast test tier | `test_scenario_campaign_configs` ×3: no `configs/scenarios/soco_scenario_base_{2026_2030,2026_2050}.yaml` | **YES** — the campaign test enumerates `SUPPORTED_ISOS` | FIXED: both REF bases added from the SPP template (mode/iso/horizon only, every other field the shipped default); 21/21 pass |
| Fast test tier | 19 other failures (`test_forecast_parity` ×2, `test_gate_a_provenance`, `test_golden_manifest_provenance` ×7, `test_replay_keeper_strict`, `test_ff_readiness_battery`, `test_audit_keepers_lineage`, `test_calibration_verdict` coverage interval, `test_caiso_per_hub_intertie`, `test_cache_config_agreement` ×2 on an uncommitted `shard-artifacts/` path, plus the §6.1 CAISO / Mystic / SPP-RPS / NYISO rows) | no | same-tree control (i) on `origin/main` `d77a0cc9`'s `src`+`scripts`+`configs`: the failure set is IDENTICAL, 19 = 19 |
| Ruff lint + format | `scripts/gen_nyiso229_attestation.py` F401 `numpy` + unused `drift` | no | file untouched here (0 diff lines); main's own copy fails `ruff check` with the same 2 errors (last touched `54ed3227`) |
| Pinned default cache key | NYISO surface 210 rows ≠ 209 declared | no | §6.1; measured 210 at the base before any edit |
| Structural refactor guards | `run_calibration_full.py` → missing `test_recorded_config_gas_anchor_mirror.py` | no | §6, pre-existing on main |
| Keeper-integrity gates | S1: `status/<ISO>.js` stale vs current verdicts (ERCOT, CAISO, …); E11 warning on the pruned nyiso231 bundle | no | status parts of other ISOs' lanes; this branch touches no `frontend/data/backcast/**` |
| FR-21 forecast-board staleness | gate-(a) markers cite superseded NYISO / SPP keepers (`nyiso-221`, `spp-36`) | no | keeper promotions of 2026-09-12/13; `frontend/data/forecast/**` is a forbidden region for this lane |
| FR-22 backcast→forecast parity | NYISO keeper arms `gas_offer_margin_zonal_anchor_vintage`, `nyiso_st_gas_econ_bands_deleaked` with no registry declaration | no | nyiso-232 promotion; `scripts/lib/forecast_parity_registry.py` is the NYISO lane's |

**After the rebase (§0, head on `c6c70190`):** `tests/curation` + `tests/regression` + `tests/scoring`
read 2,916 passed / 31 failed / 33 skipped. The 31 are the 11 + 19 already classified above plus TWO
new ones that arrived with main itself, not with this branch: `test_clean_io::test_datatype_list_matches_schemas`
and `test_data_dictionary_sync::test_every_schema_has_a_section` both trip on the `coal-stocks`
datatype main's `3857d801` ("Intake `coal-stocks`") added to `data/dictionary/` without the matching
datatype-list / dictionary section — this branch touches neither `data/dictionary/` nor any clean-io
script (0 diff lines). The unit suite on the rebased tree is reported in the log entry.

Note on the branch: `origin/main` `d77a0cc9` is the auto-merge of PR #6151 — the PRECOMMIT commit
`7e6978ee` pushed to this same branch name before the registration commit existed. PR #6152 carries
the registration itself.

## 7. Deliberate exclusions and routed items (STOP-and-route, none applied)

| Item | Owner | Why not here |
|---|---|---|
| `scripts/curate_demand_profile.MODEL_ISOS` | SOCO-31 | curation lane's registry |
| `docs/multi-iso/README.md` seven-ISO prose; `build_status.ISO_ORDER` / `keeper_store` / `render_data_dictionary`; `frontend/data/backcast/keepers/index.json` display order | SOCO-34 / SOCO-40 | dashboard/docs lanes; no SOCO keeper exists yet |
| D79 undeclared SOCO rows (20) | SOCO-DESK (R-1 successor) | no `--declare-iso` route; same state SPP-20 left |
| 2025 tail: 7 trailing UTC-bounded hours | SOCO-11 item [4] | fetch extension, not a loader pad (bridged + WARNED here) |
| Loader-seam fuel spike screen fires on SOCO NG: OIL 2023 (1 h) / 2024 (7 h) and NG: NG 2025 (the four ~70 GW hours); CC pmax reconciliation warnings for plants 6073 / 7897 / 55382 / 57037 | SOCO-31 / SOCO-32 | measured-data defects documented in FINDING-soco-10; no new constant (rule 23) |
| Forecast-mode `derive_cf_profile` on an all-zero wind series | W6 / capx | forecast path; SOCO backcast never enters it |
| VOLL exposure in forecast screens | SOCO-55 | adequacy lane |
| `ci_refactor_guards` script-refs failure (`run_calibration_full.py` → missing mirror script) | whoever owns `scripts/run_calibration_full.py` | pre-existing on main; file outside this lane's regions |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py::test_registry_value_matches_the_committed_artifact` (1.154 ≠ 1.166) | CAISO lane | pre-existing on main: artifact and test both last touched by PR #6037; neither file on this branch |
| ledger r#5 five-respondent ruling not on main | SOCO-DESK | quoted verbatim from the charter |
| **`process_eia860.rescope_generator_table_from_parquet` is not additive when columns differ** (§4): it must append only the new-BA rows to the committed frame, aligned to the committed columns, with `heat_rate` joined from the PLNT23 cache — the recipe this lane applied by hand | SOCO-DESK → data-curation owner | `scripts/data/process_eia860.py` is outside this lane's regions; the committed tables ARE repaired |
| `tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none` asserts `get_rps_target("SPP") is None`, but main's `STATE_RPS_FLOORS` has carried an SPP row since SPP-60 | SPP lane | pre-existing on main (fails identically there, §6); not this branch's file |

Files NOT touched, as chartered: `frontend/data/forecast/**`; every other ISO's keeper shard, log and
matrix shard; `docs/codebase-site/data/mechanism-matrix/**`; the plan; the ledger;
`docs/calibration-log/soco.md`; `results/cache.py`; `ScenarioConfig`. `scripts/calibration_verdict.py`
was touched ONLY for the two §2.3 rows the charter names (`PINNED_CLASSES_BY_ISO["SOCO"]`, the
`TAIL_THRESHOLD` skip comment) — declared above.

## 8. Log entry

```
## soco-20 — 2026-09-14 — SOCO registered as the ninth region (zero-LP)

Lane SOCO-20, Fable claude-fable-5-1, branch claude/soco-20-register-fvj01g, base d083b0b1.
Deliverable: ONE PR — _ISO_BUILDERS["SOCO"] appended last, DEMAND_LOADERS["SOCO"] and
SURFACE_ISOS += SOCO in the SAME commit (eb9d015a), _ISO_TO_BA_CODE["SOCO"]="SOCO"; 22 src
modules, 9 scripts, four new scripts/lib/<pkg>/soco.py specs, the soco data profile, the
calibration-solve dropdown. No solve, no matrix cell, no keeper, no ScenarioConfig field.

REGISTERED AS A BALANCING AUTHORITY. Three geographic zones SOCO_AL/GA/MS on shares
0.3510/0.5842/0.0648 (five FERC-714 respondents, Southern Power 186 EXCLUDED, residual
3.03/2.92/1.26 %); Tier-3 links 24,400 / 4,300 MW that CANNOT bind; no capacity market,
no import node, no AS design (reserves.spec refuses SOCO by name); every offer band 1.0;
VOLL 61,900 $/MWh from ICE 2 on the EIA-861 BA=SOCO class mix; PRM 0.26 winter; McIntosh
CAES a 25 MW gas CT and skipped by the storage loader. Zone lookup 413 plants (GA 299 /
AL 97 / MS 17); plant 67241 (MA) REJECTED. Fleet 393 thermal units / 55.09 GW, 8 nuclear
incl. Vogtle 3 (2023-07) and 4 (2024-04) on their own CODs. Demand 239.6 / 249.5 / 252.6
TWh; net export +10.16 / +10.81 / +13.03 TWh.

G8 HOLDS. solve_surface_register --diff origin/main HEAD: ERCOT 0, CAISO 0, MISO 0, PJM 0,
NYISO 0, NEISO 0, SPP 0 moved (SOCO 20 = its own new rows, undeclared, R-1 state). All
seven keepers' cache_key() re-derived from run_config.json BYTE-IDENTICAL to the PRECOMMIT
§6 baseline (nyiso on 2026-09-13-nyiso-232-st-gas, 93be4aeb93d78283).

TWO SEAM REPAIRS, both no-ops for the seven: derive_nuclear_monthly_cf divides by the
MONTH-ONLINE nuclear pmax (--check: seven committed tables match); load_eia860_storage
drops the one national CAES row. Curated EIA-860 parquets rescoped (+SOCO rows only).

THE RESCOPE WAS NOT ADDITIVE AND THE SUITE CAUGHT IT: --rescope-from-parquet dropped the
eGRID heat_rate join on the canonical + 2020/2023/2024 tables and admitted one PJM row.
Repaired before push as main's frame byte-for-byte + SOCO rows (heat_rate joined from
the PLNT23 cache); script defect ROUTED with the recipe. Suites on the pushed state:
unit 5,475 passed / 7 failed; curation+regression 1,382 / 11. All 18 remaining failures
fail identically with origin/main's code checked out into the same tree (CAISO artifact
drift PR #6037, Mystic oil rows, ERCOT fleet golden, SPP RPS None, NYISO surface 210 vs
209, 10 NEISO forecast key-provenance records, and data/clean FileNotFound x11).

TAIL_THRESHOLD SKIPPED x3 (SOCO-13 read NO price). Routed: D79 undeclared rows, the 7-h
2025 tail fetch, the four ~70 GW NG:NG hours, curate_demand_profile.MODEL_ISOS (SOCO-31),
dashboard ISO_ORDER / keepers index (SOCO-34/40), VOLL in forecast screens (SOCO-55),
the process_eia860 rescope defect. Pre-existing on main, not this lane's:
ci_refactor_guards script-refs (run_calibration_full -> missing mirror script) and the
seven test failures above.
```
