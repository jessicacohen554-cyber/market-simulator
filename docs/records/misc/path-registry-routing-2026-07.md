# Path-registry routing + spec_from_file_location closure (2026-07-26)

> Status: RECORD (frozen) — session record of the path-registry hygiene lane.
> Executes items 1–3 of the session chartered off
> `docs/handoffs/inputs-dead-path-inventory-2026-07.md` ("Out of scope" §);
> item 4 (keeper_store.py's CLI) was owner-adjudicated 2026-07-26 to STAY and
> was not touched.

## 1. The authoritative re-census (measured this session, not inherited)

Method: AST walk of every `scripts/data/*.py` — maximal `/`-operator chains
rooted at a module-level repo-root binding, string segments split on `/` —
so line-wrapped chains and single-string `REPO / "data/raw/x"` spellings
count, which the 2026-07-26 grep estimate (~150/97) missed. Two site classes:

* **Hand-rolled registry bypasses: 158 sites across 100 files** (plus 3
  single-string-spelling files the first census pass missed → 103 files
  converted in total). All resolved correctly; hygiene, not defects.
* **CWD-relative literals (real defects, the charter's item-2 class): 10
  sites across 7 files** — `derive_nyiso_import_ladder` (the chartered one,
  import-time), `build_capacity_actuals` (2), `derive_ercot_zonal_lmp` (2),
  `derive_interface_limits`, `derive_nyiso_central_east_ttc`,
  `derive_ttc_limits` (2 — one of which, `Path("data/reference")`, was
  *doubly* dead: CWD-relative AND the pre-W1 spelling of what W1 moved to
  `data/raw/reference`, so the curated-dir fallback could never fire),
  `derive_coal_max_cf` (a CWD-relative string argument).

Both classes are now ZERO in `scripts/data/`: every runtime path composes on
a `config/paths.py` name. Provenance/label strings (curate_* `source=`
fields, help text) are data, not resolution, and were left alone — as was
`derive_offer_curve_jacobian`'s git pathspec (adjudicated D1 in the
inventory doc).

## 2. What the registry gained

23 new directory constants in `config/paths.py` (ERCOT_MIS_DIR, ERCOT_AS_DIR,
NYISO_AS_DIR, NEISO_AS_DIR, NYISO_DIR, LMP_DATA_DIR, CAISO_DAM_OUTAGES_DIR,
PJM_OUTAGES_DIR, MISO_GENERATION_OUTAGES_DIR, NRC_REACTOR_STATUS_DIR,
NUCLEAR_LICENSE_STATUS_DIR, NEISO_OPERABLE_CAPACITY_DIR, CAMPD_UNIT_LEVEL_DIR,
CAMPD_FACILITY_LEVEL_DIR, STORAGE_AS_AWARDS_DIR, NEW_BUILD_COST_BENCHMARKS_DIR,
FUEL_FORWARD_BENCHMARKS_DIR, EIA_AEO_DIR, EIA_930_INTERCHANGE_DIR,
TRANSFER_CONSTRAINT_BINDING_DIR, TRANSMISSION_EXPANSION_DIR, NREL_ATB_DIR,
ERCOT_WEATHER_DIR). Adjudication for loose FILES at the data/raw root: a
single-consumer file composes as `RAW_DATA_DIR / "<name>"` at its call site —
the same idiom the src data modules use (`data/fuel/hubs.py`,
`data/outages.py`, …) — rather than growing a one-line constant each; the
repo-root/data/raw math is what the registry owns.

Acceptance bar: the rewriter evaluated every site's OLD expression against
the repo root and its replacement against the live registry and asserted
equality per site (all pass); post-apply re-census reports zero remaining
sites. `MARKET_SIM_DATA_ROOT` unset ⇒ byte-identical resolution by
construction; the CWD-relative fixes are byte-identical for the repo-root
invocation and *newly correct* for every other CWD.

## 3. spec_from_file_location: tail closed

The five README-listed live chains (`regression_gate`, `export_tranche_config`,
`bench_warmstart_xyear`, `build_offer_curve_overrides`,
`derive_caiso_supply_consistent_demand`) are converted to canonical
`scripts.*` package imports. Before switching, a both-paths harness loaded
each target via the old file-load AND the package import in one process and
compared every consumed attribute (`compare_parquet`; `_henry_hub_actual`,
`_load_reference`, `_calibration_config`, `run_year`; `_GAS_GROUPS`,
`_gas_foldin_deflation`) — all identical objects or byte-identical source.
Zero live call sites remain outside frozen `archive/`/`probes/`. No
`__init__.py` added under `scripts/` (PEP-420 stays load-bearing).

## 4. Discovered, recorded, deliberately NOT fixed here

1. **`bench_warmstart_xyear.capture()`'s spy seam has rotted** —
   `run_calibration` no longer exports a module-level `solve_dispatch` (the
   solve moved into `market_sim.pipeline.solve` at the orchestrator
   extraction), so `rc.solve_dispatch` raises AttributeError on BOTH import
   forms, equally. The conversion is behavior-neutral; a capture rerun needs
   the spy re-pointed at the pipeline seam first. Committed capture pickle
   and recorded bench numbers unaffected. Noted in the function docstring.
2. **Bare top-level sibling imports** (9 live scripts: `import
   run_calibration_full as rcf` in replay_keeper, audit_eia923_completeness
   and the three top-level miso probe drivers; `from run_calibration import
   run_year` late imports in derive_nyiso_rcpf_overlay, derive_ordc_overlay,
   derive_pjm_offer_surface, derive_pjm_ordc_overlay). Same
   second-copy hazard as spec_from_file_location if the canonical `scripts.*`
   name is also loaded in-process. Recorded in scripts/README.md; converting
   them is open work — NOT part of the closed tail.

## 5. Verification record (before → after, both measured this session)

| Gate | Before (main @ ce90f6b) | After |
|---|---|---|
| ruff check . | 22 errors / 4 files | 22 errors / same 4 files (none touched here) |
| ruff format --check . | clean | clean |
| ci_refactor_guards.py | import-walk OK; script-refs OK (8 tolerated) | identical |
| compileall src scripts | OK | OK |
| 9-file facade + persisted-identity set | 73 passed, 5 subtests | 73 passed, 5 subtests |
| cache_key pin | `edbc1b103207170a` | untouched (no ScenarioConfig change; test_persisted_identity green) |
| Fast tier (`-n 2`, CI expression) | 23 failed + 1 collection error, 5167 passed | see §5.1 |

### 5.1 Fast-tier failure sets: stable set byte-identical; pollution family flaps

Three full-tier runs, sorted FAILED/ERROR line sets diffed pairwise:

* **before** (base, main @ ce90f6b): 24 lines (23 failed + 1 collection
  error) — the advisory-tier backlog, i.e. the triage doc's 26+1 minus the
  three §6.2 order-dependent tests that happened not to fire on that run.
* **after run 1** (all session commits): 37 lines = the SAME 24 **plus 13
  `tests/test_storage.py` EIA-860 battery-fleet/vintage-ramp tests** — every
  one passes in isolation on the same tree.
* **after run 2** (identical tree as run 1): 27 lines = the SAME 24 **plus
  exactly the 3 `tests/test_fleet.py` tests** the triage doc §6.2 already
  documents as the order-dependent pollution family (they also pass in
  isolation, re-verified).

Reading: the stable failure set is **byte-identical before → after** (both
after-run diffs are pure additions over it — nothing went red, nothing went
green), so this session contributes zero delta. The flapping members are the
known xdist-order-dependent pollution class (`-n 2` load-stealing reshuffles
the schedule every run; the fleet loaders' lru_cache poisoning documented in
the triage §6.2). **New observation for that family's eventual bisect:** the
`test_storage.py` EIA-860 fleet family (13 tests incl.
`TestEIA860{CAISO,NEISO,NYISO}BatteryFleet`, `TestEIA860PumpedStorage`,
`TestStorageVintageRamp`) is a further member of the same class — observed
red in one full-tier schedule on a tree where it passes in isolation and
passed in the other two schedules, including on the base tree's run. It
shares the suspected mechanism (eia860-fed, cache-backed fleet loads).
