# Reliability-Floor Rebuild — Session Execution Prompts

Copy-paste prompts for executing the rebuild
(`docs/multi-iso/reliability-floor-rebuild-plan.md`) across parallel and sequential
sessions. **Read the plan first** — these prompts assume it.

## Dependency graph (what runs when)

```
PHASE 1  Foundation (1 session, SEQUENTIAL, must merge first)
   │     engine + config + loader + fetch/derive scripts + station table + tests + removals
   ▼
PHASE 2  Per-ISO data + coefficients (6 sessions, PARALLEL — disjoint files)
   │     2A ERCOT  2B PJM  2C CAISO  2D MISO  2E NYISO  2F NEISO
   ▼     (each writes ONLY its own <iso>-weather CSV + reliability_floor_coeffs_<ISO>.csv)
PHASE 3  Backcast re-solves + dashboard (6 sessions, PARALLEL in pairs — ≤2 per-plant LPs at once)
   │     3A ERCOT  3B PJM  3C CAISO  3D MISO  3E NYISO  3F NEISO
   ▼
PHASE 4  Docs reconcile + keeper audit (1 session, SEQUENTIAL, last)
```

**Why this split is safe to parallelize:** Phase 1 makes the registry **seed from
per-ISO CSVs** (`data/raw/reference/reliability_floor_coeffs_<ISO>.csv`). Phase-2/3
sessions therefore touch only their own ISO's data/bundle files and never edit shared
Python — no merge conflicts. Merge each phase before starting the next.

**Branching:** Phase 1 commits to `claude/temp-reliability-mechanism-yo6zgc`. Each
later session branches off the latest feature-branch HEAD, touches only its files, and
pushes a per-ISO branch for clean merge. Follow CLAUDE.md "Git & Pushing" (push file
content via `mcp__github__push_files`; never loop on a 413'ing `git push`).

---

## PHASE 1 — Foundation (run this ALONE, first)

```
You are in the market-simulator repo (LP electricity-market dispatch simulator). Read
CLAUDE.md (esp. #1/#2/#9/#10/#11) and docs/multi-iso/reliability-floor-rebuild-plan.md
in full before touching code. Work on branch claude/temp-reliability-mechanism-yo6zgc
(fetch origin main, ensure the branch is rebased on latest origin/main first).

GOAL: build the FOUNDATION layer of the reliability-floor rebuild — everything shared
that the per-ISO sessions depend on. Do NOT derive coefficients or run calibrations here.

Implement, in src/market_sim and scripts:

1. STATION TABLE  data/raw/reference/iso_zone_weather_stations.csv
   columns: iso,zone,station_id,weight,station_name
   - Populate EVERY fossil-bearing model zone for all 6 ISOs (ERCOT 6 zones — skip
     Panhandle; CAISO NP15/ZP26/SP15; PJM 8; MISO 3; NYISO 5; NEISO 4). Migrate the
     existing MISO_ZONE_STATIONS / NEISO_TMAX_STATIONS / NYISO station dicts VERBATIM.
     Pick major load-center airport GHCN stations for new zones (see plan §A.3 for the
     starter map; verify each station_id exists at
     https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/<id>.csv
     and has 2023–2025 TMAX/TMIN coverage). Weights = metro load share within the zone.

2. FETCH SCRIPT  scripts/fetch_zone_temperature.py  (--iso ALL|<list> [--start 2023
   --end 2025] [--no-fetch])
   - Reads the station table, fetches NOAA GHCN-Daily (access CSV endpoint above; TMAX/
     TMIN are tenths °C ÷10), load-weights per zone, writes
     data/raw/<iso>-weather/<iso>_zone_temp_daily.csv with schema date,zone,tmax_c,tmin_c.
   - Through the agent proxy. --no-fetch re-derives from a cached raw pull.

3. LOADER  data/eia_loader.iso_zone_tmax(iso, year, hours, zone) -> (tmax, tmin)
   - Collapse _WEATHER_FILES to one canonical per-ISO path
     <iso>-weather/<iso>_zone_temp_daily.csv (per-zone, tmax+tmin). Keep the daily→
     hourly day-of-year broadcast + ffill/bfill. Return None when a forecast year has
     no pinned weather (graceful no-op). Migrate CAISO/NYISO/NEISO callers to per-zone.

4. CONFIG  config/iso_configs.py
   - Replace ReliabilityFloorSpec with the frozen dataclass from plan §C.3:
     {zone, plant_class, driver("tmax"|"tmin"|"netload"), threshold, floor_pct,
      enabled, min_event_hours=24, distribution="cheapest_first"}.
   - RELIABILITY_FLOOR_REGISTRY: build it by READING per-ISO CSVs
     data/raw/reference/reliability_floor_coeffs_<ISO>.csv at import (a loader fn).
     Ship empty stub CSVs (headers only) so the registry is empty until Phase 2.
   config/scenarios.py
   - Keep single `reliability_floor` flag. ADD reliability_floor_overrides: dict[str,
     dict] keyed "<ZONE>:<CLASS>:<driver>" -> {enabled?, floor_pct?, threshold?}.
   - ADD class_commitment_overrides for per-ISO×class min_run/min_down (steam gas).
   - REMOVE the legacy floor fields/bools (plan §D): caiso_ct_*, nyiso_ct_*, nyiso_st_*,
     neiso_temp_*/coldsnap floor coeffs, miso_temp_*, slope/cap/base/t0,
     gas_st_summer_mustrun/gas_st_offsummer_mustrun. (Keep neiso_gas_coldsnap_derate and
     caiso_gas_commitment_floor — different physics, see plan §D.)

5. ENGINE  model/transmission.inject_reliability_floor(fleet_arrays, iso, year, specs,
   zone_names)
   - Rewrite per plan §C.4: for each enabled limb, iso_zone_tmax → daily gate
     (tmax>threshold / tmin<threshold; netload limb uses net_load_mw>threshold) →
     broadcast 24h → (steam) bridge to min_event_hours → frac=floor_pct on flagged
     hours → rows = plant_group==class & zone_idx==zone & pmax>0 →
     _distribute_group_floor (REUSE, transmission.py:2633) → min_gen via np.maximum.
     Returns True iff floored (byte-identical no-op otherwise).
   - DELETE the 5 legacy injectors (inject_caiso_ct/nyiso_ct/nyiso_st/neiso_temp/
     miso_temp_reliability_floor) and their constant dicts. Fold net-load drag in as
     driver="netload" limbs.

6. STEAM MIN-RUN  config/constants.py: raise ST_GAS_COMMITMENT_PARAMS.min_run_hours
   (efficient 12→24, older subcritical 24→48). Thread class_commitment_overrides through
   model/commitment._commitment_params so ISO/class min_run can be overridden.

7. RETIRE-AS-KEEPER (default-off probes, keep code): confirm ct_mustrun_per_plant and
   ct_deployment_overlay default False and are excluded from any keeper config path.

8. DERIVE SCRIPT  scripts/derive_reliability_coeffs.py (--iso <ISO>)
   - Per plan §B: build measured (zone,class) daily CF from CAMPD grossLoad / model bin
     nameplate (reuse _zone_class_daily_cf helpers; map plants→zone via
     bin_assignments_<ISO> / custom-bin-assignments / zone_assignment.build_zone_lookup
     for PJM; class via classify_plant). Compute hot_tmax_c / cold_tmin_c thresholds,
     commit_frac, min_stable_pct, floor_pct=commit_frac×min_stable_pct, plus ρ/n/slope/
     baseline diagnostics. Emit reliability_floor_coeffs_<ISO>.csv (iso,zone,plant_class,
     driver,threshold,floor_pct,enabled,commit_frac,min_stable_pct,rho,n,baseline) and
     append a section to docs/multi-iso/reliability-floor-coefficients.md.
     enabled=True only when ρ≥0.3 AND n≥30 AND floor_pct>baseline; else enabled=False.
     NEVER tune to a price/volume residual; NEVER use measured-CF p97 as the floor.

9. TESTS  tests/test_reliability_floor.py — trivial fleet (1 unit per fossil class, 1
   zone, T=24..72): hot day / cold day / normal day / no-weather forecast fallback.
   Assert min_gen==floor_pct·avail for all 24h on the matching flagged day, ==pmin
   otherwise; a disabled limb is byte-identical; steam min_event_hours bridges
   consecutive flagged days. Run with the repo's .venv python; all tests green.

Verify: import the package, run the new tests + any touched modules' tests. Commit
(small commits per CLAUDE.md Git rules) and push the branch. Do NOT run calibrations.
Report what changed and confirm the registry is empty-but-wired (Phase 2 fills it).
```

---

## PHASE 2 — Per-ISO data + coefficients (6 PARALLEL sessions)

Run after Phase 1 is merged. Each session is independent (disjoint files). Launch all
six; each is light (no LP solve). Generic template — substitute `<ISO>` and the year
span (all use `2023 2024 2025`):

```
You are in the market-simulator repo. Phase 1 of the reliability-floor rebuild is
merged. Read CLAUDE.md (#9/#10/#11) and docs/multi-iso/reliability-floor-rebuild-plan.md
(§A,§B). Branch off the latest claude/temp-reliability-mechanism-yo6zgc HEAD as
claude/temp-reliability-<ISO>-data.

TASK for ISO = <ISO> ONLY (touch only this ISO's files):
1. Fetch weather:  .venv/bin/python scripts/fetch_zone_temperature.py --iso <ISO>
   → writes data/raw/<iso>-weather/<iso>_zone_temp_daily.csv (date,zone,tmax_c,tmin_c,
   all fossil zones, 2023–2025). Spot-check: every zone present, no NaN after fill,
   plausible seasonal range.
2. Derive coefficients:  .venv/bin/python scripts/derive_reliability_coeffs.py --iso <ISO>
   → writes data/raw/reference/reliability_floor_coeffs_<ISO>.csv and appends to
   docs/multi-iso/reliability-floor-coefficients.md.
3. REVIEW the coefficient table HONESTLY (CLAUDE.md #9/#11): for every (zone, class),
   confirm enabled=True only where the temperature/net-load response is real
   (ρ≥0.3, n≥30, floor_pct>baseline). Set weak/insignificant limbs enabled=False —
   do NOT invent a limb to plug a residual. floor_pct must be commit_frac×min_stable_pct
   (physical), never a measured-CF p97 ceiling. Note any class with no physical response.
4. Sanity: load the registry (import iso_configs) and confirm <ISO>'s limbs parse, and
   that a 24-h trivial inject for one flagged day floors as expected.
Commit ONLY: <iso>-weather CSV, reliability_floor_coeffs_<ISO>.csv, the doc section.
Push the per-ISO branch. Report the enabled/disabled limb count per zone×class and the
fit quality, and flag anything surprising. Do NOT edit shared Python or other ISOs.
```

Substitute one of: `ERCOT  PJM  CAISO  MISO  NYISO  NEISO`.

---

## PHASE 3 — Backcast re-solves + dashboard (PARALLEL, ≤2 per-plant LPs at once)

Run after Phase 2 is merged. **Open at most 2 of these at a time** (per-plant multi-zone
LPs use several GB each; CLAUDE.md). Each ISO solves all years in ONE bundle and
registers on the dashboard. Generic template:

```
You are in the market-simulator repo. Phases 1–2 of the reliability-floor rebuild are
merged (engine + per-ISO coefficients live). Read CLAUDE.md (#1, #11, #12, #13) and
docs/multi-iso/reliability-floor-rebuild-plan.md. Branch off latest
claude/temp-reliability-mechanism-yo6zgc HEAD as claude/temp-reliability-<ISO>-solve.

TASK for ISO = <ISO> ONLY:
1. Capture the BEFORE baseline MAE (the current dashboard keeper for <ISO>) for the
   before/after comparison.
2. Solve ALL backcast years in ONE invocation (sequential year loop — never parallel
   years):
   .venv/bin/python scripts/run_calibration_full.py --iso <ISO> --year 2023 2024 2025 \
       --reliability-floor \
       --note "<ISO> reliability-floor rebuild: per-(zone,class) day-gate" \
       --out-dir results/calibration/<iso>_relfloor_rebuild
3. Register on the dashboard via the calibration-report skill (scripts/dashboard_add_run.py
   then build_manifest.py). Label "<iso> N relfloor-rebuild" honoring the top-15-per-ISO
   retention. Commit the per-run bundle + registry sidecar + runs/<id>.js + changed bench
   in the SAME session (push via mcp__github__push_files to avoid 413). The dashboard
   files are the deliverable — do not just narrate metrics.
4. Track MAE before/after. If the residual WORSENED, do NOT revert the mechanism
   (CLAUDE.md #1/#11) — diagnose the real root cause (offer curves, must-run, passthrough,
   fleet/zone assignment) and report it; the structurally-correct floor stays in.
Lead your final reply with the dashboard headline (ISO, years, MAE before→after, keeper
label). Do NOT touch other ISOs or shared Python.
```

Suggested pairing (memory-aware): solve ERCOT alone first (largest), then pairs
{PJM, MISO}, {NYISO, NEISO}, {CAISO}. Adjust to available memory.

---

## PHASE 4 — Docs reconcile + keeper audit (run LAST, alone)

```
You are in the market-simulator repo. Phases 1–3 of the reliability-floor rebuild are
merged and all six ISOs are re-solved and on the dashboard. Branch off latest
claude/temp-reliability-mechanism-yo6zgc HEAD.

1. Run /sync-docs to reconcile docs with the shipped code. Specifically rewrite
   docs/multi-iso/reliability-floor-feature.md and the relevant model-methodology-spec.md
   sections (§1.4 dispatch-time floor injection, §1.7 forecast-vs-backcast, §5.2) to
   describe the NEW mechanism: per-(zone,class) step-function day-gate, driver field
   (tmax/tmin/netload), floor_pct=commit_frac×min_stable_pct, toggleable limbs, steam
   longer min-run. Delete references to the retired window/slope/cap/base mechanism and
   the 5 legacy injectors.
2. Update docs/backcast-measured-data-audit-2026-06.md: record that ct_mustrun_per_plant
   and ct_deployment_overlay are demoted to default-off probes and the p97-CF ceiling is
   gone; confirm no keeper enables an outcome-pinned floor.
3. Run the calibration-keeper-auditor agent to confirm every new keeper's dashboard text
   matches its actual run results; repair drift.
4. Add a CHANGELOG entry. Commit + push (source-only small commits; git push OK, fall
   back to push_files if it 413s).
Report a final summary: per-ISO MAE before→after table and any open root-cause items.
```

---

## Coordinator checklist (between phases)

- After Phase 1: merge to the feature branch; confirm tests green and registry imports
  empty. THEN fan out Phase 2.
- After Phase 2: merge all six per-ISO data branches (disjoint → clean); confirm
  `import iso_configs` builds a non-empty registry for every ISO. THEN fan out Phase 3
  (≤2 per-plant solves at once).
- After Phase 3: confirm all six bundles are on the dashboard. THEN run Phase 4.
