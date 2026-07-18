# ISO Model Unification & Codebase Streamlining Plan

**Status 2026-07.** Phases 0-2 and the module halves of Phase 4 are effectively
landed: `config/reserve_config.py` (Phase 1), `config/interchange_config.py`
(Phase 2), and `data/fleet.py::build_dispatch_fleet` (Phase 4) all exist and are
ISO-complete — `runner.py` (the forecast orchestrator) drives all six ISOs through
each. What Phase 4 (and, implicitly, Phases 1-2) left undone is migrating the
**second consumer**, `run_calibration.py` (the backcast orchestrator), onto these
same modules — that is a different axis, owned by
`docs/handoffs/orchestrator-unification-plan-2026-07.md`. Per that plan's §2.3, the
composition boundary is: **this plan is the producer** (make each module
ISO-complete) and **the unification plan is the second consumer** (point backcast
at it) — sequence any shared-module work module-universal-first,
orchestrator-migration-second. **Phase 6 (large file decomposition)** must wait
until orchestrator-unification's **Stage 7** completes, since decomposing
`fleet.py`/`constants.py`/`transmission.py`/`scarcity.py` while the backcast
orchestrator still holds inline copies of code this plan's producer modules
replace risks touching code the unification plan is about to delete. Phase 3
(clean-Parquet) and Phase 5 (P2 legacy label / scarcity generalization) touch
neither the orchestrator seam nor the solve core and may run before, after, or
interleaved with the unification plan.

## Context

The market simulator (44,895 LOC in `src/market_sim/`) models hourly electricity dispatch across 6 ISOs (ERCOT, CAISO, PJM, MISO, NYISO, NEISO). The core LP is already ISO-agnostic — `dispatch.py` has zero `if iso ==` branches. But the orchestration layers that *feed* the LP (reserve setup, interchange modeling, data loading, fleet construction) have grown ISO-specific code paths: 47 `if iso ==` branches across the codebase, 6 separate `*_reserve_coopt_inputs()` functions (~1,500 lines in scarcity.py), 6 separate `*_zonal_load_shares()` functions, and CAISO-only interchange code (~500 lines in transmission.py). The result is a codebase where adding a new ISO or cross-porting a feature requires scattered surgery rather than configuration.

**Goal:** Refactor into a single universal model where every feature is available to every ISO, toggled on/off via config. Enforce clean Parquet data loading. Move P2 commitment to labeled legacy. Reduce LOC. Maintain byte-identical mathematical results for all existing runs.

---

## Audit Findings Summary

### What's Already Good (Don't Touch)
- **dispatch.py** (2,501L): ISO-agnostic LP builder. Zero branching. The gold standard.
- **commitment.py** (888L): ISO-agnostic P0→P1 startup markup + P2 commitment screen.
- **storage.py** (937L): ISO-agnostic fleet builder + SOC dynamics.
- **Policy modules** (carbon.py, rps.py, eac.py, ira.py): Pure data-driven lookups into per-ISO registries. No code branching.
- **ISOConfig model** (iso_configs.py): Clean Pydantic topology + VOLL + interface limits. Well-structured.

### What Needs Unification

| Area | Current State | Lines Affected | Problem |
|------|--------------|----------------|----------|
| **Reserve co-opt** | 6 separate `*_reserve_coopt_inputs()` in scarcity.py, 200L if/elif chain in runner.py | ~1,700L total | Each ISO has its own function returning the same `dispatch_kwargs` shape |
| **Interchange/import model** | CAISO has per-hub corridor model (~500L), others use generic reference-price seam | ~800L in transmission.py | Two parallel systems producing identical Generator objects |
| **Zonal load shares** | 6 separate `*_zonal_load_shares()` in eia_loader.py | ~450L | Identical interface, different file parsers |
| **Fleet construction** | ERCOT uses CAMPD binning (load_campd_bins), others use fleet_to_bins | ~200L in runner.py | Two fleet-loading paths doing the same job |
| **Scarcity pricing** | ERCOT post-solve ORDC overlay in runner.py + scarcity.py | ~400L | Feature exists only for ERCOT; should be available to all |
| **Raw data loading** | 52 `pd.read_csv` calls in data/ modules | scattered | Should all go through clean Parquet seam |

### Feature Availability Matrix (Current → Target)

| Feature | Today | Target |
|---------|-------|--------|
| Energy+reserve co-opt | 5/6 ISOs (not CAISO) | All 6 (CAISO defaults off) |
| Multi-product AS cascade | ERCOT only | All (most default off) |
| Nested locational reserves | NYISO+NEISO | All (config-driven zone masks) |
| Per-hub corridor interchange | CAISO only | All (generic corridor model) |
| Border carbon pricing | CAISO only | All (defaults to 0) |
| Deliverable supply cap | PJM only | All (config-driven) |
| Online-gated reserves | PJM+NYISO | All (config toggle) |
| CAMPD per-plant binning | ERCOT only | All (config toggle) |
| Post-solve ORDC overlay | ERCOT only | All (config toggle) |
| Capacity market revenue | 5/6 ISOs | All (MARKET_DESIGN registry, already done) |
| Firm external imports | MISO only | All (config toggle) |

---

## Phased Refactoring Plan

### Phase 0: Safety Net (Pre-Requisite)
**Goal:** Establish regression baselines so every subsequent phase can prove mathematical equivalence.

**Work:**
1. Run the existing backcast suite for all 6 ISOs (2023-2025 where available) and snapshot the full output Parquet files (dispatch, prices, generation mix, emissions)
2. Create a lightweight `scripts/regression_check.py` that compares two result directories column-by-column with configurable tolerance (default: 1e-6 absolute for MW, 1e-4 relative for prices)
3. Add a CI-friendly test that runs a minimal single-zone, 24-hour smoke test for each ISO and asserts exact match against golden output

**Files:** `scripts/regression_check.py` (new, ~150L), `tests/test_regression_smoke.py` (new, ~100L)
**LOC change:** +250L (net add — this is infrastructure)
**Risk:** Low. Read-only baseline capture.
**Verification:** Run the regression checker against itself (A==A).

---

### Phase 1: Reserve Co-Optimization Unification
**Goal:** Replace 6 ISO-specific `*_reserve_coopt_inputs()` functions + the 200-line if/elif chain in runner.py with a single `build_reserve_coopt_inputs(config, fleet_arrays, hours, zone_names)` function dispatched by a `ReserveDesign` config object.

**Why first:** This is the largest single divergence (~1,700 lines) and the cleanest to unify because all 6 functions already return the same `dispatch_kwargs` shape. The LP side (`_build_reserve_rows` in dispatch.py) needs zero changes.

**Design:**
- Add a `ReserveDesign` dataclass to `config/reserve_config.py` (new file) with fields:
  - `families: list[ReserveFamily]` — each family = (name, requirement_mw, zone_mask, ordc_steps, eligible_mask, class_label, online_gated, online_rho)
  - `storage_eligible: bool`
  - `supply_cap: Optional[np.ndarray]`
- Each ISO's existing `*_reserve_coopt_inputs()` becomes a builder that populates `ReserveDesign` from ISO-specific parameters (ERCOT ORDC curve, PJM shortfall steps, NYISO RCPF tiers, etc.)
- A single `build_reserve_dispatch_kwargs(design: ReserveDesign, fleet_arrays, hours)` function converts the design into the `dispatch_kwargs` dict
- Runner.py's if/elif chain becomes: `design = get_reserve_design(config, fleet_arrays, hours, zone_names); dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))`
- The ISO-specific builders move from scarcity.py into `config/reserve_config.py` as classmethod-style factories

**Files modified:**
- `config/reserve_config.py` (new, ~300L — ReserveDesign + ReserveFamily dataclasses + universal builder)
- `results/scarcity.py` — extract ~1,200L of per-ISO reserve builders into reserve_config.py; ~400L of ERCOT ORDC curve/LOLP math stays (it's physics, not orchestration)
- `runner.py` — replace 200L if/elif chain with ~15L unified call
- `config/constants.py` — move reserve-product constants into reserve_config.py where they're consumed

**LOC change:** Net -400 to -600L (shared builder logic replaces 6 duplicated return-assembly blocks; per-ISO physics stays)
**Risk:** Medium. Must verify that the ReserveDesign→dispatch_kwargs transformation is numerically identical for every ISO. The ERCOT multiproduct cascade and NYISO nested locational families are the most complex cases.
**Verification:** Run regression_check.py for all 6 ISOs against Phase 0 baselines. Zero tolerance on dispatch volumes; 1e-6 on prices.

---

### Phase 2: Interchange Model Unification
**Goal:** Replace the CAISO-specific per-hub corridor model and the generic reference-price seam with a single configurable `InterchangeModel` that handles both patterns via configuration.

**Design:**
- Define `InterchangeSpec` in a new `config/interchange_config.py`:
  - `corridors: list[Corridor]` — each corridor = (name, zone, import_tranches, export_cap, ttc_mw, carbon_adder)
  - `reference_price_neighbors: list[NeighborSpec]` — each neighbor = (iso, seam_tranches, hub_pricing_fn)
  - `firm_imports: list[FirmImport]` — (name, zone, capacity_mw, shape_fn)
  - `monthly_reconciliation: Optional[ReconciliationBand]`
- CAISO's per-hub split becomes 2 corridors (PNW/DSW) instead of a separate code path
- PJM/MISO/NYISO/NEISO's reference-price seam becomes corridors with a single endpoint
- MISO's Manitoba firm import becomes a `FirmImport` entry
- NYISO's monthly reconciliation becomes a `ReconciliationBand` entry
- A single `build_interchange_fleet(spec: InterchangeSpec, ...)` replaces the scattered builders

**Files modified:**
- `config/interchange_config.py` (new, ~200L)
- `model/transmission.py` — consolidate ~800L of CAISO-specific + generic reference-price code into ~400L unified builder. The incidence/TTC/interface math stays untouched.
- `runner.py` — replace ~60L of interchange setup branching with ~10L config-driven call

**LOC change:** Net -400 to -500L
**Risk:** Medium-High. The CAISO corridor model has subtle per-hour envelope logic (solar deliverability derate, gas coupling). Must verify CAISO backcast is byte-identical.
**Verification:** Full 6-ISO regression check. CAISO is the canary — any breakage shows up there.

---

### Phase 3: Data Loading — Clean Parquet Enforcement
**Goal:** Eliminate all 52 `pd.read_csv` calls in data modules. Every data load goes through clean Parquet (the `read_clean()` seam).

**Why Phase 3:** Phases 1-2 unified the model logic. This phase unifies the data pipeline. Order matters because the data loading changes must not interact with the model logic changes.

**Sub-phases:**

#### Phase 3A: Zonal Load Shares (eia_loader.py)
- Replace 6 separate `*_zonal_load_shares()` functions (~450L) with a single `load_zonal_shares(iso, year, zone_names)` that reads from `data/clean/load/{iso}/zonal_shares_{year}.parquet`
- Create curation script `scripts/data/curate_zonal_shares.py` that converts each ISO's raw format (PJM CSV, ERCOT XLSX, CAISO TAC, NYISO zonal, NEISO SMD, MISO sub-BA) into the common Parquet schema: columns = zone names, index = hour (0-8759)
- Add schema to `data/dictionary/schema/zonal_shares.schema.yaml`

**LOC change:** -300L in eia_loader.py, +200L in curation script = net -100L in model code

#### Phase 3B: Weather Data
- Replace 6 ISO-specific weather CSV loaders (~200L in eia_loader.py) with a single `load_weather(iso, year)` reading from `data/clean/weather/{iso}/weather_{year}.parquet`
- Schema: columns = (zone, tmax_c, tmin_c, load_weighted_temp_c), index = date

**LOC change:** -150L in eia_loader.py, +150L in curation script = net -150L in model code

#### Phase 3C: Fuel Prices
- Replace gas/coal price CSV loading in fuel.py (~300L of `pd.read_csv`) with clean Parquet reads
- Schema: per-ISO monthly hub basis + per-plant EIA-923 delivered cost → `data/clean/fuel/{iso}/fuel_prices_{year}.parquet`

**LOC change:** -200L in fuel.py, +200L in curation script = net -200L in model code

#### Phase 3D: Outages, Fleet, Reference Data
- Convert remaining CSV loaders in outages.py, zone_assignment.py, fleet.py, cod_ramp.py, egrid.py
- Each gets a curation script and clean schema

**LOC change:** -200L across data modules

**Total Phase 3 LOC change:** -650L in model code, +600L in curation scripts
**Risk:** Low-Medium. Each sub-phase is independently verifiable. The clean Parquet must be numerically identical to the raw CSV parse.
**Verification:** For each sub-phase: run regression_check.py for all ISOs. Also add a unit test per curation script that round-trips raw→clean→load and asserts value equality.

---

### Phase 4: Fleet Construction Unification
**Goal:** Merge the two fleet-loading paths (CAMPD binning for ERCOT, fleet_to_bins for others) into a single configurable pipeline.

**Design:**
- CAMPD per-plant binning becomes the default for all ISOs that have CAMPD data (ERCOT already, CAISO/PJM/MISO/NYISO/NEISO have unit-level parquets)
- `fleet_to_bins` becomes the fallback for ISOs or years without CAMPD data
- A single `build_dispatch_fleet(config, iso, year)` function in fleet.py handles the choice via `config.use_campd_bins` (already exists as a ScenarioConfig field)
- The runner.py coal-aggregation branching (lines 395-419) collapses into the unified fleet builder

**Files modified:**
- `data/fleet.py` — refactor `load_campd_bins()` and `fleet_to_bins()` into a shared interface; extract the 200L of runner.py fleet-setup logic into fleet.py
- `runner.py` — replace ~50L of fleet-loading branching with `build_dispatch_fleet()` call

**LOC change:** Net -200 to -300L
**Risk:** Medium. CAMPD binning for non-ERCOT ISOs is new territory — must verify that `fleet_to_bins` results are preserved when `use_campd_bins=False`.
**Verification:** Regression check all ISOs. Also run ERCOT with `use_campd_bins=False` and a non-ERCOT with `use_campd_bins=True` as sanity probes.

---

### Phase 5: P2 Commitment → Legacy Label + Scarcity Overlay Generalization
**Goal:** (a) Label P2 commitment as a legacy/optional path. (b) Generalize the ERCOT-only post-solve ORDC scarcity overlay to all ISOs.

#### 5A: P2 Legacy Label
- P2 commitment (`compute_commitment()` + `apply_commitment_with_coal_pin()`) is already gated by `config.commitment_enabled` (default off). The code stays — it's correct and tested — but gets explicit `# LEGACY: P2 commitment screen` labeling.
- Add `config.commitment_enabled` deprecation warning when True: "P2 commitment is a legacy feature; prefer energy_reserve_coopt for accurate unit commitment."
- Move the P2 block in runner.py (lines 1209-1320) under a clearly labeled `# === LEGACY: P2 Commitment Screen ===` section.

**LOC change:** +10L (deprecation warning + labels). No code removed — it's legacy, not dead.
**Risk:** None. Labeling only.

#### 5B: Generalize Scarcity Overlay
- The ERCOT post-solve ORDC overlay (runner.py lines 1332-1377 + scarcity.py `ordc_adder()`, `reserve_headroom()`, `scarcity_prices()`) currently runs only for ERCOT.
- Generalize `scarcity_prices()` to accept any ISO's reserve headroom + ORDC curve parameters.
- Gate via `config.scarcity_price_overlay` (new field, defaults True for ERCOT, False for others).

**LOC change:** Net -50L (remove ERCOT-only guard, make the existing functions accept generic parameters)
**Risk:** Low. The overlay is post-solve and doesn't affect dispatch; only affects reported prices and capacity economics.
**Verification:** ERCOT regression check (overlay ON). Other ISOs regression check (overlay OFF, no change).

---

### Phase 6: Large File Decomposition & Dead Code Removal
**Goal:** Break the 3 largest files into cohesive modules. Remove dead code. Target: reduce total LOC from ~44,900 to ~38,000-40,000.

#### 6A: fleet.py Decomposition (6,903L → ~5,500L)
- Extract coal-specific logic (supply class, take-or-pay, PRB sigmoid, lignite) into `data/coal.py` (~800L)
- Extract CHP logic (overrides, BTM pct, pmin CF) into `data/chp.py` (~400L)
- Extract offer-curve / tranche logic (split_coal_tranches, split_gas_tranches, plant_tranche_bands, _offer_curve_for_group, _econ_split_for_group) into `data/offer_curves.py` (~600L)
- The remaining fleet.py (~4,100L) handles Generator model, FleetArrays, binning, zone assignment, and fleet loading — still large but cohesive.

**LOC change:** Net -400L from removing duplicated helpers across the split + dead code in tranche logic.

#### 6B: constants.py Decomposition (3,968L → ~2,500L)
- Move IMPORT_TRANCHES / EXPORT_TRANCHES / IMPORT_TRANCHES_BY_YEAR (~1,200L) into `config/interchange_config.py` (already created in Phase 2)
- Move reserve-product constants into `config/reserve_config.py` (already created in Phase 1)
- Dead code: remove any tranche definitions for year-ISO combos that are never used (audit needed)

**LOC change:** Net -500L (move + dead code removal)

#### 6C: scarcity.py Decomposition (2,549L → ~1,200L)
- After Phase 1, the per-ISO reserve builders have moved to reserve_config.py (~1,200L moved)
- Remaining scarcity.py: ERCOT ORDC curve math, LOLP, generalized scarcity overlay (~1,200L)
- Remove any dead ERCOT-specific helpers that were superseded by the unified reserve design

**LOC change:** Net -200L (dead code removal after Phase 1 extraction)

#### 6D: transmission.py Cleanup (2,921L → ~2,200L)
- After Phase 2, CAISO-specific corridor code consolidated into unified model (~400L removed)
- Remove commented-out fallback paths
- Remove any dead inject_* functions no longer called

**LOC change:** Net -300L

#### 6E: eia_loader.py Cleanup (2,941L → ~2,200L)
- After Phase 3, the 6 zonal_load_shares functions and weather loaders removed (~600L)
- Remove any dead interchange helpers

**LOC change:** Net -300L

**Total Phase 6 LOC change:** -1,700L
**Risk:** Medium. File decomposition can break imports. Grep for every moved function's callers.
**Verification:** Full test suite (`pytest tests/`). Import resolution check (`python -c "import market_sim"`). Regression check all ISOs.

---

## LOC Reduction Summary

| Phase | Estimated Reduction | Running Total |
|-------|-------------------|---------------|
| Phase 0 (safety net) | +250L | 45,145 |
| Phase 1 (reserve unification) | -500L | 44,645 |
| Phase 2 (interchange unification) | -450L | 44,195 |
| Phase 3 (clean Parquet) | -650L | 43,545 |
| Phase 4 (fleet unification) | -250L | 43,295 |
| Phase 5 (P2 legacy + scarcity) | -40L | 43,255 |
| Phase 6 (decomposition + dead code) | -1,700L | 41,555 |
| **Total** | **-3,340L** | **~41,500L** |

Conservative estimate. Aggressive dead-code sweeps in Phase 6 could push to ~39,000-40,000L.

---

## Wallclock Efficiency Opportunities

Identified during audit — implement as low-risk improvements within each phase:

1. **Warm-start already exists** (runner.py line 1173): P1 reuses P0's basis. Verify this is enabled by default. ✓ Already done.
2. **Sparse matrix assembly**: `_build_reserve_rows` in dispatch.py builds COO then converts to CSC. If Phase 1's unified reserve builder can pre-compute the sparsity pattern, the CSC conversion is faster.
3. **Parquet column pruning**: Clean Parquet loads should use `columns=` parameter to only read needed columns (reduces I/O for large fleet tables).
4. **Fleet array pre-allocation**: `generators_to_fleet_arrays()` builds lists then converts to numpy. Pre-allocating arrays by known fleet size saves GC pressure.
5. **Interchange pricing vectorization**: `inject_reference_price_mc` loops over neighbors; could batch into a single vectorized operation.

These are implementation details, not architectural changes — fold them into the relevant phase's PR.

---

## Phase Prompt Packs

Each prompt pack is designed for a new session to develop detailed, meticulous implementation prompts for that phase.

### Phase 0 Prompt Pack: Safety Net

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md for the project rules and architecture.

TASK: Build a regression baseline and smoke-test suite for ISO model refactoring.

CONTEXT: We are about to refactor the ISO model architecture across 6 phases.
Before any changes, we need:

1. A regression checker script (scripts/regression_check.py) that:
   - Takes two result directory paths
   - Loads all year_*.parquet files from each
   - Compares every numeric column with configurable tolerances
     (default: 1e-6 absolute for MW quantities, 1e-4 relative for prices)
   - Reports PASS/FAIL per column with max deviation
   - Returns exit code 0 on pass, 1 on fail
   - Handles missing files gracefully (report, don't crash)

2. A smoke test (tests/test_regression_smoke.py) that:
   - For each of the 6 ISOs (ERCOT, CAISO, PJM, MISO, NYISO, NEISO):
     creates a minimal ScenarioConfig (1 zone, 2 generators, 24 hours)
     and runs solve_dispatch directly (not the full runner)
   - Asserts the LP solves successfully and prices are non-negative
   - Uses pytest fixtures for the fleet/demand setup
   - Runs in <10 seconds total

3. A baseline capture script (scripts/capture_baseline.py) that:
   - Takes --iso and --out-dir arguments
   - Runs run_scenario_iso for the given ISO in backcast mode
   - Saves the output Parquet files to the specified directory
   - Can be run in parallel for multiple ISOs

RULES:
- Follow the existing test patterns in tests/
- Use the existing ScenarioConfig and solve_dispatch interfaces
- Don't modify any existing source files
- All new files go in scripts/ or tests/

OUTPUT: The three files above, with clear docstrings explaining usage.
```

### Phase 1 Prompt Pack: Reserve Co-Optimization Unification

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md for the project rules. Read the refactoring plan at
/root/.claude/plans/can-you-do-a-twinkly-corbato.md for full context.

TASK: Unify the 6 ISO-specific reserve co-optimization input builders into
a single config-driven system. Mathematical results must be byte-identical.

CONTEXT: The dispatch LP (dispatch.py _build_reserve_rows) is already
ISO-agnostic — it consumes these kwargs:
  reserve_requirement, reserve_eligible, ordc_penalties, ordc_step_widths,
  reserve_storage, reserve_balance_zone_mask, reserve_balance_ordc_counts,
  reserve_balance_class, reserve_headroom_eligible, reserve_headroom_products,
  reserve_online_gated, reserve_online_rho, reserve_supply_cap

Currently, 6 separate functions in results/scarcity.py build these kwargs
for each ISO, and runner.py lines 970-1164 has a 200-line if/elif chain
that calls the right one. All 6 return subsets of the same dict.

DESIGN:
1. Create src/market_sim/config/reserve_config.py with:
   - ReserveFamily dataclass: (name, requirement, zone_mask, ordc_steps,
     ordc_penalties, eligible_mask, class_label, online_gated, online_rho)
   - ReserveDesign dataclass: (families: list[ReserveFamily],
     storage_eligible: bool, supply_cap: Optional[ndarray])
   - get_reserve_design(config, fleet_arrays, hours, zone_names) -> ReserveDesign
     This dispatches to per-ISO builder functions (which can be private helpers
     in the same file, carrying the physics from scarcity.py)
   - build_reserve_dispatch_kwargs(design: ReserveDesign) -> dict
     Converts the design into the dispatch_kwargs dict

2. Move the per-ISO reserve physics from scarcity.py into reserve_config.py:
   - ERCOT: ORDC demand curve steps, LOLP params, multiproduct AS cascade
   - PJM: 2-step vertical ORDC, deliverable supply cap
   - NYISO: nested locational families (NYCA/East/SENY/NYC), spin class
   - NEISO: nested 3-level families (30m/10m/10m-spin), RCPF
   - MISO: system-wide pool, RBDC curve
   - Leave the LOLP math and ORDC curve evaluation in scarcity.py (they're
     physics utilities, not orchestration)

3. Replace runner.py lines 970-1164 with:
   if getattr(config, "energy_reserve_coopt", False):
       design = get_reserve_design(config, fleet_arrays, hours, zone_names)
       dispatch_kwargs.update(build_reserve_dispatch_kwargs(design))

4. Move reserve-product constants from constants.py into reserve_config.py
   (ERCOT_AS_*, PJM_ORDC_*, NYISO_RCPF_*, NEISO_RCPF_*, MISO_RBDC_*)

CRITICAL CONSTRAINTS:
- The dispatch_kwargs dict produced for each ISO MUST be numerically identical
  to what the old per-ISO function produced. Write tests that call both old and
  new, and assert np.allclose on every array.
- Don't change dispatch.py at all — the LP builder is untouched.
- Don't change the ScenarioConfig fields — the feature toggles stay the same.
- Keep the existing ERCOT multiproduct vs single-product toggle working.

VERIFICATION:
- Run scripts/regression_check.py for all 6 ISOs against Phase 0 baselines
- Add tests/test_reserve_config.py that tests get_reserve_design for each ISO
- Run the full test suite (pytest tests/) — zero new failures

FILES TO READ FIRST:
- src/market_sim/results/scarcity.py (lines 948-end: all *_reserve_coopt_inputs)
- src/market_sim/runner.py (lines 960-1170: the if/elif chain)
- src/market_sim/model/dispatch.py (lines 687-1040: _build_reserve_rows)
- src/market_sim/config/constants.py (grep for ORDC, RCPF, RBDC, AS_)
```

### Phase 2 Prompt Pack: Interchange Model Unification

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md and the refactoring plan at
/root/.claude/plans/can-you-do-a-twinkly-corbato.md.

TASK: Unify CAISO's per-hub corridor interchange model and the generic
reference-price seam into a single configurable interchange system.
Mathematical results must be byte-identical.

CONTEXT: Two parallel interchange systems exist in model/transmission.py:
A) CAISO per-hub corridor: build_caiso_per_hub_intertie() /
   build_caiso_bidir_intertie() / split_caiso_import_node_per_hub() /
   inject_caiso_per_hub_intertie_prices() / build_caiso_corridor_flow_groups()
   ~500 lines of CAISO-only code producing Generator objects for the
   PNW and DSW import corridors with signed flow and gas coupling.
B) Generic reference-price seam: build_reference_price_node() /
   inject_reference_price_mc() / inject_reference_price_firm_export() /
   inject_reference_price_firm_import() — used by PJM/MISO/NYISO/NEISO.

Both produce the same output: Generator objects injected into fleet_arrays
with MC arrays set per-hour.

Additionally: MISO has firm Manitoba hydro imports (build_miso_firm_imports),
NYISO has monthly net-interchange reconciliation bands.

DESIGN:
1. Create src/market_sim/config/interchange_config.py with:
   - Corridor dataclass: (name, zone, import_tranches, export_cap_mw,
     ttc_mw, carbon_adder, gas_coupling_fn, solar_derate_fn)
   - NeighborSpec dataclass: (iso, seam_tranches, hub_pricing_fn, firm_cap_mw)
   - InterchangeSpec dataclass: (corridors, neighbors, firm_imports,
     monthly_reconciliation)
   - get_interchange_spec(config, iso) -> InterchangeSpec
   - build_interchange_fleet(spec, ...) -> list[Generator]

2. CAISO's 2-corridor split becomes InterchangeSpec with
   corridors=[Corridor("PNW", ...), Corridor("DSW", ...)]
3. PJM/MISO/NYISO/NEISO become InterchangeSpec with
   neighbors=[NeighborSpec(...) for each in INTERFACE_NEIGHBORS[iso]]
4. MISO Manitoba becomes a firm_import entry
5. NYISO reconciliation becomes monthly_reconciliation entry

CRITICAL: The CAISO corridor model has per-hour envelope logic
(forward_corridor_atc_envelope, solar deliverability derate,
gas coupling via inject_caiso_import_gas_coupling). These must
be preserved as Corridor callback functions, not flattened.

FILES TO READ FIRST:
- src/market_sim/model/transmission.py (all 2921 lines — understand both paths)
- src/market_sim/runner.py (lines 184-240: interchange setup)
- src/market_sim/config/constants.py (IMPORT_TRANCHES, EXPORT_TRANCHES,
  INTERFACE_NEIGHBORS, CAISO_PER_HUB_*)

VERIFICATION:
- Run regression_check.py for all 6 ISOs. CAISO is the canary.
- Add tests/test_interchange_config.py
```

### Phase 3 Prompt Pack: Clean Parquet Enforcement

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md and the refactoring plan.

TASK: Eliminate all direct CSV/Excel reads from the model code (src/market_sim/data/).
Every data load goes through clean Parquet via read_clean(). This is split into
4 sub-phases; tackle them in order.

CONTEXT: Currently 52 pd.read_csv/pd.read_excel calls load raw data directly.
A clean seam (scripts/lib/clean_io.py, read_clean/write_clean) exists but is
opt-in via MARKET_SIM_USE_CLEAN env var. After this phase, the model code
ALWAYS reads from clean Parquet. The curation scripts (scripts/data/curate_*.py)
become the mandatory ETL step.

SUB-PHASES:

3A: Zonal Load Shares (eia_loader.py)
- Replace 6 *_zonal_load_shares() functions with a single
  load_zonal_shares(iso, year, zone_names) -> np.ndarray
- Create scripts/data/curate_zonal_shares.py that reads each ISO's raw format
  and writes data/clean/load/{iso}/zonal_shares_{year}.parquet
- Schema: columns = zone names (str), index = hour 0..8759, values = float share
- Add data/dictionary/schema/zonal_shares.schema.yaml

3B: Weather Data
- Replace 6 ISO weather CSV loaders with load_weather(iso, year) -> pd.DataFrame
- Create scripts/data/curate_weather.py
- Schema: columns = (zone, tmax_c, tmin_c, load_weighted_temp_c), index = date

3C: Fuel Prices
- Replace gas/coal CSV loading in fuel.py with clean reads
- Create scripts/data/curate_fuel_prices.py
- Schema: per-ISO monthly hub basis + per-plant delivered cost

3D: Outages, Fleet Reference, Zone Assignment
- Convert remaining CSV loaders in outages.py, zone_assignment.py, fleet.py,
  cod_ramp.py, egrid.py to clean reads
- Create curation scripts for each

CRITICAL CONSTRAINTS:
- The clean Parquet must produce numerically identical values to the raw CSV parse
- Add round-trip tests: raw -> curate -> read_clean -> assert equals raw parse
- Remove the MARKET_SIM_USE_CLEAN env var gating — clean is now mandatory
- Keep the raw data in data/raw/ as the immutable source — clean is derived

FILES TO READ FIRST:
- scripts/lib/clean_io.py (the clean seam)
- data/dictionary/ (existing schemas)
- Each data module's CSV loading functions (grep pd.read_csv)
- Existing curate_*.py scripts (pattern to follow)

VERIFICATION:
- Round-trip test per curation script
- Regression check all ISOs after each sub-phase
```

### Phase 4 Prompt Pack: Fleet Construction Unification

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md and the refactoring plan.

TASK: Merge the two fleet-loading paths (CAMPD binning for ERCOT,
fleet_to_bins for others) into a single configurable pipeline.

CONTEXT: runner.py has two fleet-construction paths:
- ERCOT (line 315): load_campd_bins() → per-plant bins
- Others (line 326): load_fleet_from_csv() → fleet_to_bins() → aggregate bins
Plus coal-aggregation branching at lines 395-419.

Both paths produce the same output: a list of Generator objects ready for
generators_to_fleet_arrays(). The branching is in the runner, not the model.

DESIGN:
1. Create a single build_dispatch_fleet(config, iso, year, ...) -> list[Generator]
   function in fleet.py that:
   - If config.use_campd_bins and CAMPD data exists for this ISO: load_campd_bins()
   - Else: load_fleet_from_csv() → fleet_to_bins()
   - Handles coal aggregation, dual-fuel, CHP corrections, emission rates
   - Returns a ready-to-use fleet list

2. Runner.py fleet setup (lines 300-420) collapses to:
   fleet = build_dispatch_fleet(config, iso, year, ...)

3. The use_campd_bins ScenarioConfig field already exists — keep it.
   Add CAMPD data presence detection for non-ERCOT ISOs.

FILES TO READ FIRST:
- src/market_sim/data/fleet.py (load_campd_bins, fleet_to_bins, bins_to_fleet)
- src/market_sim/runner.py (lines 300-420: fleet construction)
- src/market_sim/config/constants.py (CAMPD_BINNING_ISOS)

VERIFICATION:
- Regression check all ISOs
- Test ERCOT with use_campd_bins=False (must match old fleet_to_bins path)
- Test a non-ERCOT ISO with use_campd_bins=True (new capability)
```

### Phase 5 Prompt Pack: P2 Legacy + Scarcity Generalization

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md and the refactoring plan.

TASK: (A) Label P2 commitment as a legacy feature. (B) Generalize the
ERCOT-only post-solve ORDC scarcity overlay to be available for all ISOs.

PART A — P2 LEGACY LABEL:
- P2 commitment (compute_commitment + apply_commitment_with_coal_pin) is
  already gated by config.commitment_enabled (default False).
- Add a logger.warning deprecation notice when commitment_enabled=True
- Add section comments in runner.py: # === LEGACY: P2 Commitment Screen ===
- Do NOT delete the code — it's correct and tested, just not the primary path
- Update the ScenarioConfig docstring for commitment_enabled to say "Legacy"

PART B — SCARCITY OVERLAY GENERALIZATION:
- The post-solve ORDC overlay (runner.py lines 1332-1377) only runs for ERCOT.
  It calls scarcity.scarcity_prices() which calls ordc_adder() and
  reserve_headroom(). These functions are already generic — they take
  LOLP params and produce price adders.
- Add config.scarcity_price_overlay (bool, default: True for ERCOT via
  ISOConfig.default_scenario_overrides, False for others)
- Remove the `if iso == "ERCOT"` guard. Gate on the config flag instead.
- Ensure scarcity_prices() can accept any ISO's ORDC/LOLP parameters.

FILES TO READ:
- src/market_sim/runner.py (lines 1209-1380: P2 + scarcity)
- src/market_sim/results/scarcity.py (ordc_adder, reserve_headroom, scarcity_prices)
- src/market_sim/model/commitment.py (compute_commitment, apply_commitment_with_coal_pin)

VERIFICATION:
- ERCOT regression check (scarcity overlay ON, same as before)
- Other ISOs regression check (scarcity overlay OFF, same as before)
- Full test suite passes
```

### Phase 6 Prompt Pack: Decomposition & Dead Code Removal

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md and the refactoring plan.

TASK: Break the largest files into cohesive modules and remove dead code.
Target: reduce total src/ LOC from ~41,500 (after Phases 1-5) to ~39,000-40,000.

This phase has 5 sub-tasks. Do them IN ORDER — each one is a separate commit.

6A: fleet.py Decomposition (6,903L → ~5,500L)
- Extract into data/coal.py: _derived_coal_supply, _eia860_retiree_coal_supply,
  coal_supply_class, _derived_coal_takeorpay, coal_takeorpay_share,
  _coal_class_for, coal_chp_overrides, coal_sync_online_frac (~800L)
- Extract into data/chp.py: chp_overrides, chp_btm_pct, chp_pmin_cf,
  _chp_by_plant, _correct_caiso_chp_steam_credit_hr (~400L)
- Extract into data/offer_curves.py: split_coal_tranches, split_gas_tranches,
  _coal_tranches, _offer_curve_for_group, _econ_split_for_group,
  _econ_curve_steps, plant_tranche_bands, _bands_from_shares (~600L)
- Update all imports across the codebase (grep for every moved function)

6B: constants.py Decomposition (3,968L → ~2,500L)
- Move IMPORT_TRANCHES / EXPORT_TRANCHES / IMPORT_TRANCHES_BY_YEAR into
  config/interchange_config.py (created in Phase 2)
- Move reserve-product constants into config/reserve_config.py (Phase 1)
- Audit for unused constants and remove them

6C: scarcity.py Cleanup (after Phase 1 extraction)
- Remove any dead per-ISO reserve builders that were superseded
- Consolidate remaining ORDC/LOLP math into a clean module

6D: transmission.py Cleanup (after Phase 2)
- Remove dead CAISO-specific builders superseded by unified interchange
- Remove commented-out code blocks

6E: eia_loader.py Cleanup (after Phase 3)
- Remove dead zonal_load_shares functions superseded by clean pipeline
- Remove dead weather loader functions

CRITICAL: For each sub-task:
1. Grep for every function/constant you move to find ALL callers
2. Update imports in every file that references the moved item
3. Run pytest tests/ after each sub-task
4. Run python -c "from market_sim import runner" to verify import resolution

VERIFICATION:
- Full test suite passes after each sub-task
- Regression check all ISOs after the full phase
- No import errors
```

---

## Dependency Graph

```
Phase 0 (safety net)
  ↓
Phase 1 (reserve unification)  ──→ Phase 6C (scarcity cleanup)
  ↓
Phase 2 (interchange unification) → Phase 6B (constants cleanup), Phase 6D (transmission cleanup)
  ↓
Phase 3 (clean Parquet) ──────────→ Phase 6E (eia_loader cleanup)
  ↓
Phase 4 (fleet unification) ──────→ Phase 6A (fleet decomposition)
  ↓
Phase 5 (P2 legacy + scarcity)
  ↓
Phase 6 (decomposition + dead code) — depends on all above
```

Phases 1, 2, 3, 4 can potentially overlap (they touch different files) but sequential execution is safer. Phase 6 MUST come last since it cleans up what the earlier phases created.

---

## Risk Assessment

| Phase | Risk | Mitigation |
|-------|------|------------|
| 0 | None | Additive only |
| 1 | Medium — ERCOT multiproduct + NYISO locational nesting are complex | Per-ISO comparison tests; run both old and new paths and diff |
| 2 | Medium-High — CAISO corridor model is intricate | CAISO regression is the gatekeeper; keep old code until verified |
| 3 | Low — Pure data pipeline, no model logic changes | Round-trip tests for each curation script |
| 4 | Medium — CAMPD binning for non-ERCOT is untested territory | Default off for non-ERCOT; regression check with default config |
| 5 | Low — P2 is labeling only; scarcity overlay is post-solve | ERCOT regression for overlay; others unchanged |
| 6 | Medium — File moves break imports | Grep all callers; run import smoke test |
