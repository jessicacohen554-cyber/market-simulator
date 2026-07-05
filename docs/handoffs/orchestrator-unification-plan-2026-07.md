# Orchestrator Unification Plan — Backcast ↔ Forecast Solve Core (2026-07)

**Audit ref:** `docs/fable-repo-audit-2026-07.md` §E, AR-1 (HIGH), AR-2, AR-5, AR-6.
**Companion workstreams (reconciled below, do NOT double-fix):**
`docs/audit-wiring-iso-gaps/` (per-mechanism parity patches, 2026-06-29),
`docs/iso-model-unification-plan.md` (ISO-branching-within-`src/`, different axis).
**Status:** design only — no code changes in this document. Stages are sized for
separate sessions; a complete Stage-1 implementation prompt is at the end.

---

## 1. The diagnosis, reframed

The audit describes AR-1 as "lift the ~4,000-line backcast core (`_calibration_config`
+ `run_year`) out of `scripts/` into `src/market_sim/calibration/`." That framing is
correct in spirit but **out of date on the facts**, and the difference changes the plan.

What actually exists today (verified 2026-07-04):

- The package **already contains three extracted, ISO-agnostic shared cores**, all of
  which `runner.py` (the forecast orchestrator) fully consumes:
  1. **Reserve co-optimization** — `config/reserve_config.py::get_reserve_design` +
     `build_reserve_dispatch_kwargs`. **Both** orchestrators call it
     (`runner.py:802-818`, `run_calibration.py:4363-4623`). ✅ genuinely unified.
  2. **Interchange / imports** — `config/interchange_config.py::get_interchange_spec` +
     `build_interchange_fleet`. **Only `runner.py` calls it** (`runner.py:192-193`).
  3. **Dispatch-fleet build** — `data/fleet.py::build_dispatch_fleet`. **Only
     `runner.py` calls it** (`runner.py:491`).

- `run_calibration.py::run_year` was migrated onto **reserve_config only**. For
  interchange it still calls the low-level builders directly
  (`build_reference_price_node` `:2845`, `build_caiso_per_hub_intertie` `:2853`,
  `build_caiso_bidir_intertie` `:2862`, `build_miso_firm_imports` `:2886`,
  `build_import_generators` `:2876`, `extend_with_import_node` `:2893`,
  `split_caiso_import_node_per_hub` `:2939`). For fleet it builds inline
  (`load_campd_bins` `:3222`, `fleet_to_bins`/`bins_to_fleet` `:3299-3318`,
  `aggregate_fleet` `:3319`, `generators_to_fleet_arrays` `:3401`).

- The **P0/P1/P2 solve loop and the base `dispatch_kwargs` assembly are duplicated
  near-verbatim** in both orchestrators (`runner.py:746-1035` ≈ `run_year:4282-5014`).
  They are currently *in sync* — the cross-year-warm-start A/B
  (`docs/cross-year-warmstart.md`) proved the two produce bit-identical objective,
  prices, and total generation on the same inputs — but nothing *keeps* them in sync.

**So AR-1 is not a from-scratch extraction. It is: finish pointing the second
(backcast) consumer at the shared cores that already exist, extract the one core that
is still duplicated (the solve loop), and delete the parallel copies.** The drift the
audit flags (CAISO bidir intertie / solar-shape / gas-coupling, NEISO coldsnap — all
wired only in `run_calibration.py`) lives precisely in the two blocks that were *not*
migrated: inline interchange and inline fleet. Per-mechanism patching (the
`audit-wiring-iso-gaps` approach) keeps re-opening because every new overlay added to
those inline blocks is a fresh divergence. **This plan's value is closing the drift
channel by construction: after it, there is one interchange builder, one fleet builder,
one solve loop, each called from both orchestrators, so a new overlay is reachable from
both paths the moment it is added — whether it *fires* is then a config-gate decision
(auditable in one place), never a code-presence accident.**

### 1.1 What "wired to both by construction" does and does not mean (rule 12)

Unifying the *code path* does **not** force every measured backcast overlay onto the
forecast. Each overlay's gate is a `ScenarioConfig` field; a measured-data overlay
(weather-year pin, EIA-923 monthly fuel, historic outages, measured TTC-by-year, CARB/
RGGI carbon, NEISO measured oil receipts, CAISO/NYISO measured import-hub LMP) stays
**default-off in the forecast config** exactly as today. What changes is that the
divergence becomes *intentional and centralized* (a field set differently in
`backcast_config` vs the forecast defaults) instead of *accidental and scattered* (a
mechanism that physically exists in only one of two 5,000-line files). CLAUDE.md rule 12
(measured data admissible only as a reproducible forward-responsive input, never a
pinned outcome) is unaffected — it governs which gate is on, not which file the code
lives in.

---

## 2. Reconciliation with the two existing workstreams

### 2.1 `docs/audit-wiring-iso-gaps/` (per-mechanism parity, 2026-06-29) — 15/16 landed

Verified against current `runner.py` / `run_calibration.py`. **Do not re-fix the
landed items.** Absorb only the one open item and the post-inventory drift.

| Gap | Mechanism | Status | Proof |
|-----|-----------|--------|-------|
| A1 | Hydro monthly budget in forecast | **LANDED** | `runner.py:491,783-784`; extracted to `fleet.build_dispatch_fleet` |
| A2 | NEISO reserve co-opt in runner | **LANDED** (generalized via reserve_config) | `runner.py:802-818` |
| A3 | PJM reserve supply cap | **LANDED** | `runner.py:819-836`; `reserve_config.py:995,1008` |
| A4 | PJM reserve online-gating | **LANDED** | `runner.py:837-840` |
| **A5** | **ERCOT single-product reserve supply cap** | **OPEN** | `_ercot_design` (`reserve_config.py:384`) sets no `supply_cap`; only `_ercot_multiproduct_design` does (`:676,755`). Forecast single-product ERCOT still uncapped. |
| A6 | Negative renewable offer floor | **LANDED** | `runner.py:662-667` |
| A7 | Reference-price interface | **LANDED** | `interchange_config.py:815`; `runner.py:625-648` |
| A8 | CT/ST netload drag floors | **LANDED** | `runner.py:544-579` |
| A9 | CAISO solar deliverability derate | **LANDED** | `runner.py:713-745` |
| A10 | CAISO RA must-offer P2 trigger | **LANDED** | `runner.py:913-914` |
| A11 | NYISO import-node reconciliation (forecast) | **LANDED** | `runner.py:677-698,791-797` |
| A12 | `split_gas_tranches` non-CAMPD path | **LANDED** | `fleet.py:6531` inside `build_dispatch_fleet` |
| A13 | MISO reserve co-opt in calibration | **LANDED** | `run_calibration.py:4644-4663` |
| B4 | NYISO year-varying TTC in topology | **LANDED** | `iso_configs.py:709` (+ backcast override retained) |
| C2 | Pumped storage in forecast builder | **LANDED** | `runner.py:312-316` |
| C3 | `storage_vintage_ramp` in forecast | **LANDED** | `runner.py:443-455` |

**Absorption:** **A5** folds into **Stage 2** — add `ercot_rtolcap_supply_cap_mw(...)`
to `_ercot_design` in `reserve_config.py`. Because reserve_config is already shared,
one edit fixes both paths simultaneously; this is the model for the entire plan. It is
scored under the same keeper re-solve guard (ERCOT keeper
`2026-07-03-ercot32-ordc-total-rtolcap` runs multiproduct, so this changes only a
single-product forecast path — verify with a single-product ERCOT trivial case, not the
keeper).

### 2.2 Post-inventory drift — proof that per-mechanism patching does not converge

Five overlays landed *after* the 2026-06-29 inventory (mostly via merge `46cb72e`,
2026-07-02). Their wiring status today:

| Overlay | File | Gate | Wired in | Bucket |
|---------|------|------|----------|--------|
| MISO firm imports (Manitoba) | `transmission.py:3403,3466`; `interchange_config.py:763` | `miso_firm_imports` | **BOTH** (runner `:649-658`, cal `:2886,3723`) | already-shared |
| NEISO cold-snap derate | `transmission.py::inject_neiso_gas_coldsnap_derate` | `neiso_gas_coldsnap_derate` | **cal only** (`run_calibration.py:3640-3657`) | **accidental drift** |
| CAISO bidirectional intertie | `transmission.py::build_caiso_bidir_intertie` | `caiso_bidir_intertie` | **cal only** (`:2862,4053`) | **accidental drift** |
| CAISO import solar-shape | `transmission.py::inject_caiso_import_solar_shape` | `caiso_import_solar_shape` | **cal only** (`:4147`) | **accidental drift** |
| CAISO import gas-coupling | `transmission.py::inject_caiso_import_gas_coupling` | `caiso_import_gas_coupling` | **cal only** (`:4130`) | **accidental drift** |

MISO firm imports landed in both because it was routed through the shared
`interchange_config` spec. The four that drifted are all in the **inline interchange
block** (CAISO trio) and **inline fleet-availability block** (NEISO coldsnap) —
i.e. exactly the two blocks not yet migrated. This is the convergence failure the plan
eliminates: **Stage 5 (interchange unification) makes the CAISO trio reachable from
both paths by construction; Stage 6 (fleet unification) does the same for NEISO
coldsnap.** No per-mechanism runner.py edit is written for any of them — that is the
anti-pattern.

### 2.3 `docs/iso-model-unification-plan.md` — orthogonal axis, defined composition boundary

That plan unifies **ISO-specific branching *within* a `src/` module** (make one
`interchange_config`/`reserve_config`/`fleet` builder handle all six ISOs by config).
This plan unifies **which *orchestrator* calls those modules** (make both `runner.py`
and `run_calibration.py` share one solve core). The two are perpendicular and compose
cleanly with one ordering rule:

> **A package module must be ISO-complete (iso-model-unification's job) before the
> second orchestrator is pointed at it (this plan's job).**

Status of that dependency:

- **Reserve (their Phase 1):** landed and ISO-complete; both orchestrators already on
  it. Nothing owed.
- **Interchange (their Phase 2):** the *module* `interchange_config` exists and is
  ISO-complete (runner drives all six ISOs through it). Their Phase 2 is effectively
  done at the module level. **My Stage 5 migrates the backcast consumer onto it** — this
  is the piece their plan's Phase 2 left implicit (it migrated only the forecast side).
- **Fleet (their Phase 4):** `build_dispatch_fleet` exists and runner drives all ISOs
  through it. **My Stage 6 migrates the backcast consumer.**
- **Their Phase 3 (clean-parquet), Phase 5 (P2 legacy label), Phase 6 (file
  decomposition):** touch neither the orchestrator seam nor the solve core. They can run
  **before, after, or interleaved** with this plan on any file this plan does not lock
  during a stage. Recommended: run their Phase 6 decomposition *after* this plan's Stage
  7, because decomposing `scarcity.py`/`constants.py`/`transmission.py` while the
  backcast orchestrator still has inline copies risks touching code this plan is about to
  delete.

**Net:** the two plans do not collide. Where they touch the same module (interchange,
fleet, reserve) iso-model-unification is the *producer* (make the module universal) and
this plan is the *second consumer* (point backcast at it). Sequence any shared-module
work module-universal-first, orchestrator-migration-second.

---

## 3. Parity matrix — every mechanism, classified

Three buckets: **BOD** = backcast-only-by-design (measured overlay, rule 12 — correctly
divergent, should be a config gate not a code fork); **DRIFT** = accidental drift (in one
code path with no config reason — a latent bug the plan removes); **FOD** =
forecast-only-by-design (capacity evolution and its inputs — correctly divergent).

### 3.1 Backcast-only-by-design (BOD) — measured overlays, keep as config gates

These are legitimate per CLAUDE.md rule 12 (each is a reproducible, forward-responsive
input in principle, but is fed measured historical values in backcast). They must remain
*gated* off in the forecast config, and after unification the gate is the *only*
divergence — the code that consumes them is shared.

| Mechanism | run_calibration.py | Gate (field) | Notes |
|-----------|--------------------|--------------|-------|
| Weather-year pin | `1075` | `weather_year` | Pins load/VRE profiles to the calibration year |
| T&D gross-up off (net-gen demand) | `1082` | `td_loss_factor=0.0` | EIA-930 is generation-side |
| Federal carbon = 0 → measured state carbon | `1087` | `carbon_price` | CAISO→CARB, NY/NE→RGGI measured allowance |
| Gas monthly/daily actuals (EIA-923) | `1094,1221` | `gas_monthly_actuals` | Measured ISO-month delivered gas |
| Gas hub-basis overlay (AGT/SoCal) | `1236,3765` | `gas_hub_basis_overlay` | Measured citygate basis |
| Zonal gas basis (NY/ERCOT/PJM/MISO) | `3772-3792` | `*_zonal_gas_basis` | Measured intra-ISO basis |
| Plant monthly fuel pricing (EIA-923) | `3755` | `coal_plant_monthly_pricing`, gas equiv | Per-plant delivered cost |
| Coal take-or-pay from data (MISO) | `1419` | `coal_takeorpay_from_data` | EIA-923 Sch-5 contracted share |
| Historic outage overlay (facility CAMPD) | `1739` | `historic_outage_overlay` (`HISTORIC_OUTAGE_OVERLAY_BY_ISO`) | ERCOT on; PJM off (double-count) — already a registry in both paths |
| Outage source = historic | `1290` | `outage_source` | Pins measured coal/CC outage windows |
| EIA-860 vintage pin | `1081,2788` | `eia860_vintage_year` (backcast only) | Year-matched fleet snapshot; **runner.py already honors it** (`:236-240`) |
| Retired-within-window units | `3211` | `mode=="backcast"` | Mid-window exits aged out via COD ramp; **runner.py already has it** (`:293-295`) |
| Year/month-varying interface TTC | `2797,3000` | `NYISO_INTERFACE_TTC_BY_YEAR/MONTH` | Measured AC-Transmission upgrade; forecast uses upgraded static value (B4 landed) |
| ERCOT measured GTC limits (NP6-86) | `3010` | `ercot_gtc_limits_measured` | Hourly export limit from measured HSL |
| MISO seasonal CIL/CEL | `3048` | (always, MISO) | Measured seasonal deliverability caps |
| PJM measured internal TTC | `2981` | `pjm_congestion` | Measured postings |
| Interchange shaping (EIA-930 diurnal) | `3462` | `interchange_shaping` | Measured import/export diurnal |
| MISO/PJM seam flow/export caps (EIA-930 BA-BA) | `3482-3577` | `*_seam_flow_limit/_export_limit` | Measured tie-line envelopes |
| CAISO measured import-hub LMP seam | `4001,4072` | `caiso_import_hub_prices`, `caiso_perhub_firm_base` | Measured WECC hub LMP — **keeper CAISO-51 headline mechanism**; forecast substitutes the reference-price seam (A7, wired) |
| NYISO measured import-hub LMP | `4108` | `nyiso_import_hub_prices` | Measured PJM/ISO-NE DA LMP; forecast substitutes reference-price seam |
| NYISO import-node reconciliation (measured band) | `3673` | `nyiso_import_reconciliation` (backcast band) | Forecast mode uses `nyiso_forward_net_import_twh` (A11 landed) |
| CARB border carbon on imports | `2815` | (CAISO, priced block) | Measured CARB allowance × EF |
| NEISO oil-burn budget (measured receipts variant) | `4216` | `neiso_oil_burn_budget` | **Superseded** by `neiso_winter_fuel_inventory` (forward-native Component A) — the measured-receipts variant is the inadmissible one per rule 12; ensure it stays default-off |
| CAISO gas commitment floor (EIA-930 NG:NG) | `1292,3578` | `caiso_gas_commitment_floor` | **default-off** measured-outcome probe (rule 12 inadmissible) — keep deleted-means-deleted watch |
| ERCOT AS reservation from measured award | `4188` | `storage_as_commitment` | Measured up-AS; forecast uses endogenous co-opt |
| ERCOT env-gated gas mechanisms | `1116-1216` | `os.environ` (diagnostic) | Default-off measured probes — **rule-23/24 concern**, see §4 |

### 3.2 Accidental drift (DRIFT) — the bugs the plan removes by construction

| Mechanism | Where | Gate (field exists?) | Missing from | Removed by |
|-----------|-------|----------------------|--------------|-----------|
| CAISO bidirectional intertie | `run_calibration.py:2862,4053` | `caiso_bidir_intertie` ✓ | forecast (runner) | **Stage 5** (interchange unification) |
| CAISO import solar-shape | `:4147` | `caiso_import_solar_shape` ✓ | forecast | **Stage 5** |
| CAISO import gas-coupling | `:4130` | `caiso_import_gas_coupling` ✓ | forecast | **Stage 5** |
| NEISO cold-snap derate | `:3640` | `neiso_gas_coldsnap_derate` ✓ (+ coeff fields) | forecast | **Stage 6** (fleet unification) |
| ERCOT single-product reserve supply cap (A5) | `reserve_config.py:_ercot_design` | `ercot_reserve_supply_cap` ✓ | forecast single-product | **Stage 2** (reserve fix) |
| Cross-year warm-start (built, unused by forecast) | `dispatch.py:1982-2639` | env `MARKET_SIM_WARMSTART_XYEAR` | forecast P0 | **Stage 3** makes it *wireable* to both; §8 says keep it gated OFF on forecast |
| `caiso_ra_min_load_frac` getattr fallback 0.40 ≠ field/keeper 0.26 | `run_calibration.py:4865` vs field default `scenarios.py:603` and `_calibration_config:1320` | field ✓ | (latent — fires only if a config bypasses `_calibration_config`) | **Stage 7** (getattr→field fold) |

All DRIFT gate-fields already exist in `ScenarioConfig` (verified). So the fix is never
"add a field" — it is "route both orchestrators through the one code path that reads the
field." That is what makes each removal a *pure structural* change with a config-gated,
default-off forecast behavior (dispatch-neutral for every existing keeper).

### 3.3 Forecast-only-by-design (FOD) — capacity evolution and its feed

Correctly absent from the backcast path (backcast builds each year's fleet independently
from data; it does not evolve). These stay in the forecast wrapper, not the shared core.

| Mechanism | runner.py | Notes |
|-----------|-----------|-------|
| Economic retirement + new-entry + CCS retrofit | `evolve_fleet` `:379-400` | Consumes `prior_results` |
| Planned additions (EIA-860 pipeline) | `:329-339` | forecast mode only |
| Renewable pool growth | `:404-407` | endogenous wind/solar cap growth |
| Storage new-entry value-stack screen | `:432-440` | prior-year prices |
| Cumulative learning curves (Wright's Law) | `:457-482` | `CumulativeDeployment` |
| Forecast hydro budget (`forecast_budget=True`) | via `build_dispatch_fleet` | normal-water-year climatology, not measured pin |
| Reference-price seam as *import substitute* | `:625-648` | forward-grade replacement for measured import-hub LMP |
| `prior_results` dict threading (12 keys) | `:1123-1150` | **AR-2** — becomes `PriorYearResults` (Stage 1) |

### 3.4 Shared solve core — duplicated, currently in-sync (the extraction target)

| Block | runner.py | run_calibration.py | Stage |
|-------|-----------|--------------------|-------|
| Base `dispatch_kwargs` assembly | `746-786` | `4282-4324` | **Stage 2** |
| Import-node band update | `791-797` | `4325-4335` | Stage 2 |
| Reserve co-opt block (already both call `reserve_config`) | `802-851` | `4344-4700` | Stage 2 (thin wrapper) |
| P0/P1 solve + monthly markup + warm-start | `860-905` | `4713-4746` | **Stage 3** |
| P2 commitment (CAISO RA bridge, NYISO synch reserve, ERCOT AS-adequacy, coal-pin) | `908-1033` | `4767-5014` (`_commitment_pass`) | **Stage 4** |
| Post-solve ORDC scarcity overlay (econ-price only) | `1076-1121` | external `derive_*` scripts | keep in forecast wrapper (see §7 note) |

---

## 4. `getattr(config, ...)` audit (AR-5 / rule 24) — mostly latent, one real trap

`run_calibration.py` has 88 `getattr(config, ...)` reads; `runner.py` 17. **Every gated
flag audited resolves to a real `ScenarioConfig` field** (verified for
`neiso_gas_coldsnap_derate`, `caiso_bidir_intertie`, `caiso_import_solar_shape`,
`caiso_import_gas_coupling`, `caiso_perhub_firm_base`, `nyiso_import_hub_prices`,
`ercot_reserve_supply_cap`, the coldsnap coefficients, etc.). So the getattr pattern is
**defensive, not an off-registry channel** — the fallback literal is dead code today. Two
real issues remain:

1. **`caiso_ra_min_load_frac`**: field default `0.40` (`scenarios.py:603`),
   `_calibration_config` overrides to `0.26` (`:1320`), but `_commitment_pass` reads
   `getattr(cfg, "caiso_ra_min_load_frac", 0.40)` (`:4865`). Today the field is always
   present so `0.26` wins — but any config path that bypasses `_calibration_config`
   (e.g. the future shared core constructed directly) would silently use `0.40`. Fold to
   a plain attribute read in **Stage 7**; the `0.40` fallback is a re-armable answer key
   (rule 26) and must be deleted, not zeroed.
2. **NEISO coldsnap coefficients** (`neiso_gas_derate_t0_c/slope/cap`) are read via
   getattr with literals `-7.0/0.018/0.20` (`:3647-3649`) and are **not set in
   `_calibration_config`** — the getattr literals *are* the operative values. These must
   become explicit fields with those defaults (Stage 6, when coldsnap moves onto the
   shared fleet path) so they appear in `run_config.json` (rule 20: every tunable in the
   config and the run record).

The **env-var ERCOT gas knobs** (`ERCOT_ZONAL_GAS`, `ERCOT_GAS_FLOOR`, etc.,
`:1116-1216`) are genuine off-registry channels (rule 24 violation) but are all
**default-off diagnostic probes**. They are out of scope for the neutrality-critical
stages; flag them for a separate cleanup (fold to `ScenarioConfig` fields or delete) and
note that no keeper enables them.

---

## 5. Target architecture

```
src/market_sim/
  pipeline/                         ← NEW shared solve core (both orchestrators call it)
    __init__.py
    spec.py        → DispatchSpec, ReserveSpec           (frozen dataclasses, AR-5)
    prior.py       → PriorYearResults                     (typed, replaces 12-key dict, AR-2)
    result.py      → YearSolveResult                      (what the core returns)
    kwargs.py      → build_base_dispatch_kwargs(spec), apply_reserve_coopt(...)   (Stage 2)
    solve.py       → run_energy_solve(...)  # P0/P1 + markup + warm-start          (Stage 3)
    commitment.py  → run_commitment_pass(...) # P2: CAISO RA / NYISO synch / AS-adeq (Stage 4)
    backcast_config.py → backcast_config(iso, year, hours, flags) [ex-_calibration_config] (Stage 7)
    overlays.py    → measured backcast overlays (fuel pins, TTC-by-year, coldsnap gate wiring) (Stage 7)

  runner.py            → FORECAST front-end: forecast fleet source + evolve_fleet +
                         calls pipeline.solve.run_energy_solve / run_commitment_pass
  model/dispatch.py    → unchanged LP builder (+ cross-year warm-start already here)

scripts/
  run_calibration.py       → thin BACKCAST front-end: pipeline.backcast_config + measured
                             overlays + calls the same pipeline.* core; returns context
  run_calibration_full.py  → unchanged role (bundle write + scoring); imports the five
                             seam symbols from pipeline instead of run_calibration
```

**Naming decision:** the audit suggested `src/market_sim/calibration/`, but the core is
**not calibration-only** — both forecast and backcast consume it. Calling it
`calibration/` would re-import the very confusion this plan removes. Use
**`pipeline/`** for the shared solve core; keep the genuinely backcast-specific pieces
(`backcast_config`, measured `overlays`) as clearly-named modules *inside* it. (Alt
names considered: `orchestration/`, `solve/`. `pipeline/` reads best against the
existing `model/`, `data/`, `config/`, `results/` siblings.)

**Where the contract types land:** `DispatchSpec`/`ReserveSpec` (solve-core inputs),
`PriorYearResults` (cross-year forecast state, produced by the core, consumed by
`capacity.evolve_fleet`), and `YearSolveResult` (core output) all live in
`pipeline/`. `PriorYearResults` is forecast-facing but belongs with the core because the
core produces it and it defines the forecast↔core contract.

**What each front-end becomes:**
- `runner.py` (`run_scenario_iso`): resolve forecast config → per year { build/evolve
  fleet, resolve fuels, `pipeline.run_energy_solve`, optional `pipeline.run_commitment_pass`,
  post-solve ORDC overlay for next-year economics, `evolve_fleet` } → thread
  `PriorYearResults`.
- `run_calibration.py` (`run_year`): `pipeline.backcast_config` → apply measured
  overlays → build fleet via shared `build_dispatch_fleet` → `pipeline.run_energy_solve`
  / `run_commitment_pass` → return `(result, context, result_p1, p2_state)` for
  `run_calibration_full` to persist and score.

The `for year` loops, the capacity evolution, and the bundle/scoring layer stay in the
front-ends (they are legitimately mode-specific). Only the **per-year solve** is shared.

---

## 6. Staged migration — sized for separate sessions

Every stage is a **pure refactor with a byte-identity regression gate** (§7). Stages are
ordered safe-scaffolding-first, drift-closing-unification-later, so the risky stages (5,
6) land on top of a proven-neutral shared core.

| Stage | Title | Touches | Risk | Drift closed | Neutrality standard |
|-------|-------|---------|------|--------------|---------------------|
| **0** | Regression harness + golden keeper baselines | `scripts/`, `tests/` (add only) | none | — | establishes the gate |
| **1** | `pipeline/` skeleton + `DispatchSpec`/`ReserveSpec`/`PriorYearResults`; retype runner's `prior_results` dict | `runner.py`, new `pipeline/` | low | — (AR-2) | **byte-identical** |
| **2** | Extract `build_base_dispatch_kwargs` + `apply_reserve_coopt`; **fold A5** into `_ercot_design` | `runner.py`, `run_calibration.py`, `reserve_config.py`, `pipeline/kwargs.py` | low-med | A5 | byte-identical (+ single-product ERCOT trivial case for A5) |
| **3** | Extract P0/P1 solve + markup + warm-start → `pipeline/solve.py`; both call it | both, `pipeline/solve.py` | med | — | byte-identical |
| **4** | Extract P2 commitment core → `pipeline/commitment.py`; both call it | both, `pipeline/commitment.py` | med | — | byte-identical |
| **5** | **Interchange unification**: migrate `run_calibration` onto `interchange_config.get_interchange_spec`/`build_interchange_fleet`; fold CAISO bidir/solar-shape/gas-coupling into the spec | `run_calibration.py`, `interchange_config.py` | **high** | CAISO bidir + solar-shape + gas-coupling | tolerance-bounded (CAISO keeper canary) |
| **6** | **Fleet unification**: migrate `run_calibration` onto `fleet.build_dispatch_fleet`; route NEISO coldsnap + netload-drag through shared path; coldsnap coeffs → fields | `run_calibration.py`, `fleet.py` | med-high | NEISO coldsnap | tolerance-bounded (all-ISO keepers) |
| **7** | Move `_calibration_config`→`pipeline/backcast_config.py`; `run_calibration_full` imports from `pipeline`; getattr→field fold (fix `caiso_ra_min_load_frac`, delete `0.40`); env-knob flag | `run_calibration.py`, `run_calibration_full.py`, `pipeline/`, `scenarios.py` | low-med | rule-24 latent trap | byte-identical |

**Post-Stage-7:** `run_calibration.py`'s `run_year` is a thin front-end; the ~2,600-line
body is gone. `run_calibration_full.py` imports the solve seam from `pipeline`. The
CAISO/NEISO drift overlays are reachable from the forecast (default-off gates). Then
iso-model-unification's Phase 6 (file decomposition) can safely run.

**Why this order is neutral stage-by-stage:**
- Stages 1-4 and 7 are **pure code motion** — the same statements execute in the same
  order, just relocated behind a call. The cross-year-warm-start A/B already proved the
  two solve loops compute identical results on identical inputs, so hoisting the common
  body cannot move a number. Standard: **exact byte-identity** (objective relΔ = 0,
  every price Δ = 0, every dispatch Δ = 0 — stricter than the warm-start tolerance
  because the solve path itself is unchanged).
- Stages 5-6 **swap the builder** (inline → shared `interchange_config`/
  `build_dispatch_fleet`). The shared builder must emit byte-identical `Generator`
  objects / MC arrays / availability. Any residual is float reassociation only;
  standard: **tolerance-bounded** (atol 1e-9 on MC/availability arrays, price Δ ≤ 1e-9
  $/MWh, plus the ≤0.0033% marginal-tie reshuffle the warm-start doc characterizes).
  These are the only stages where a diff above machine-epsilon is *permitted*, and each
  must document the exact arrays that reassociate and why they cannot change the optimum.

---

## 7. Regression guard — provably dispatch-neutral, stage by stage

### 7.1 The gate (runs before merge of every stage)

1. **Golden keeper re-solve, one bundle per ISO** (6 total), all within the 2023-2025
   quarantine window (keepers already are):
   `ERCOT 2026-07-03-ercot32-ordc-total-rtolcap`, `CAISO caiso-51-firm-base`,
   `PJM pjm-76-outage-fix`, `NYISO nyiso-41-hub-prices`, `NEISO neiso-47-fast-start`,
   `MISO miso-39-reserve-pergen`. Re-solve each with the *frozen keeper `run_config`*
   before and after the stage; diff with:
   - `scripts/regression_check.py <before> <after>` — column-wise, `--atol 0 --rtol 0`
     for Stages 1-4/7 (byte-identity), `--atol 1e-9 --rtol 1e-9` for Stages 5-6.
   - `scripts/diff_warmstart_bundles.py <before> <after> <year>` — per-`plant_code`
     annual/hourly MW, to localize any reshuffle and confirm it is marginal-tie-only.
2. **Trivial cases** (CLAUDE.md testing pattern): 1-gen / 1-zone / 24-hour LP per ISO,
   asserting solve success, non-negative prices, and — for Stages 2-4 — that the shared
   core's `dispatch_kwargs` equals the pre-refactor inline dict key-for-key
   (`np.array_equal` on every array). This is the fast CI-able guard; the keeper re-solve
   is the slow authoritative one.
3. **Quarantine + registry gates** (already implemented, currently CI-orphaned — wire
   them into the stage checklist per TC-1): `scripts/legitimacy_diagnostics.py --keepers`
   and `scripts/audit_keepers.py` must pass (no solve year outside 2023-2025; no
   off-registry knob introduced). Stage 7 additionally asserts no new `getattr(config,
   ..., <literal>)` in the offer/solve path (rule 24) and that the env-knob probes remain
   default-off.

### 7.2 Neutrality standard by stage type (restated as an acceptance contract)

| Stage type | Objective | Zonal price | Per-unit dispatch | Justification |
|------------|-----------|-------------|-------------------|---------------|
| Pure code motion (1-4, 7) | relΔ = 0 | Δ = 0 | Δ = 0 | same statements, same order |
| Builder swap (5, 6) | relΔ ≤ 1e-12 | Δ ≤ 1e-9 $/MWh | Σ\|Δ\| ≤ 0.0033% of gen, `total gen Δ ≈ 0` | float reassociation + marginal-tie reshuffle only; LP optimum is basis-independent |

A stage that cannot meet its row is **not neutral and does not merge** — the diff is a
discovered behavior change, not an acceptable cost (CLAUDE.md rule 1: never reach a
number through a mechanism that isn't real; here, never let a "refactor" silently move
dispatch).

### 7.3 What Stage 0 must build (extending existing tooling)

`scripts/regression_check.py`, `scripts/capture_baseline.py`,
`scripts/diff_warmstart_bundles.py` already exist. Stage 0 adds:
- `scripts/capture_keeper_goldens.py` — re-solve all six keepers from their frozen
  `run_config.json`, write the P1 dispatch/price/flow/system frames to a golden dir
  (parallelize per ISO, ≤2 concurrent for per-plant multi-zone LPs per CLAUDE.md rule 8;
  years sequential within an invocation).
- `tests/test_regression_smoke.py` — the per-ISO trivial-case suite (may already exist
  per iso-model-unification Phase 0; verify and extend, do not duplicate).
- A one-line `make regression-gate STAGE=n` that runs check + smoke + quarantine and
  prints PASS/FAIL — the same command each stage's session runs before pushing.

### 7.3.1 Stage 0 — DELIVERED (2026-07-05)

Built on `claude/regression-gate-stage-0-umopup`, add-only: nothing under
`runner.py`, `run_calibration*.py`, `dispatch.py`, or `ScenarioConfig` changed.

**Reconstruction route (decided after inspecting the format).** `run_config.json`
records neither an argv nor the full solve-arg set — its `calibration_flags`
block is a ~30-key *curated* subset, and its `scenario_config` block is the
*resolved* 357-key config (an output, not the inputs). The faithful source is
each bundle's **`meta.json`**, which echoes the passed `solve_and_persist`
kwargs directly (~134 keys, one per parameter). So the capture is **programmatic
from `meta.json`**: signature-introspect `solve_and_persist`, fill each parameter
from its `meta.json` value, and apply the four recorded-name aliases
(`commitment_screen_coal`→`screen_coal`, `coal_bit_passthrough_sigmoid`→
`coal_bit_sigmoid`, `coal_prb_sigmoid_overrides`→`prb_overrides`,
`coal_bit_sigmoid_overrides`→`bit_overrides`). Params absent from a keeper's
`meta.json` are left at default — verified benign: the ~8 never-recorded params
are uniformly absent across all six keepers, i.e. default for every one of them.

**What was built**
- `scripts/capture_keeper_goldens.py` — re-solves each keeper at HEAD from its
  frozen bundle (resolved via the registry sidecar's `bundle` field, *not* the
  empty id-named dir), determinism-pinned (`MARKET_SIM_HIGHS_THREADS=1`,
  `MARKET_SIM_WARMSTART=1`, `MARKET_SIM_WARMSTART_XYEAR=0`), full year span in one
  invocation (rule 15), writing the bundle to
  `results/regression-goldens/<stage-tag>/<ISO>/` plus a hashes-only
  `manifest.json`. **Fidelity oracle:** the golden's freshly-written `meta.json`
  must replay every recorded keeper flag identically — a hard fail otherwise, so
  a silently-dropped flag cannot produce a worthless golden. `scenario_config`
  drift vs the frozen keeper is reported *informationally* (goldens are
  current-HEAD baselines, not byte-reproductions of the July-3 bundles — the
  only observed NEISO drift is `offer_curve_by_group`, i.e. base-curve constants
  that moved since 07-03). `--all` fans out ≤2 concurrent per-ISO subprocesses
  (rule 8 memory cap); years sequential within each.
- `scripts/regression_gate.py` — one command, four checks, single PASS/FAIL,
  exit 0/1: (1) golden bundle diff reusing `regression_check.compare_parquet`
  over `dispatch/<year>_{P1,P2}.parquet` + `system/flows/storage.parquet`;
  (2) `diff_warmstart_bundles.py` per-`plant_code` reshuffle localization
  (informational); (3) `pytest tests/test_regression_smoke.py`;
  (4) `legitimacy_diagnostics.py --keepers` + `audit_keepers.py`. Tolerance via
  `--mode byte` (atol=rtol=0, Stages 1-4/7) or `--mode builder` (1e-9,
  Stages 5-6) per §7.2, overridable with `--atol/--rtol`.
- `tests/test_regression_smoke.py` — already existed (iso-model-unification
  Phase 0); **verified** (24 tests: all six ISOs × solve-success +
  non-negative-price + energy-balance + bounds, ~2 s). Not duplicated.
- `.gitignore` — `/results/regression-goldens/*/*/` (multi-GB bundles never
  committed — 413-safe); `<stage-tag>/manifest.json` stays tracked.

**The exact gate command every later stage runs** (before pushing that stage):

```
# 1. baseline at the stage's start commit (before touching code):
python scripts/capture_keeper_goldens.py --all --stage-tag stageN-before
# 2. land the stage's refactor, then re-capture:
python scripts/capture_keeper_goldens.py --all --stage-tag stageN-after
# 3. the gate (byte-identity for pure code motion, Stages 1-4/7):
python scripts/regression_gate.py \
  --before results/regression-goldens/stageN-before \
  --after  results/regression-goldens/stageN-after --mode byte
#    builder-swap stages (5-6) instead: --mode builder
```

For a single keeper substitute `--iso <ISO>` for `--all`. The gate also runs
standalone (smoke + quarantine only) with no `--before/--after`.

**Validation**
- **A/A byte-identity:** NEISO (cheapest keeper — 4 zones + HQ) captured twice
  at `THREADS=1` (`aa-run1`, `aa-run2`); `regression_gate --mode byte` between
  them: <!-- AA_RESULT --> **byte-identical — every dispatch/price/flow column
  Δ = 0, reshuffle 0.000%** (result table in the session report).
- **Six-ISO Stage-1 before baseline:** captured as `stage1-before`; the
  hashes-only `results/regression-goldens/stage1-before/manifest.json` is the
  committed deliverable (git SHA + env pins + per-file content hashes + per-ISO
  fidelity summary).

**Known caveat (pre-existing, out of Stage-0 scope).** `audit_keepers.py`
reports one FAIL on `origin/main` independent of Stage 0 —
`S1: frontend/data/backcast/status.js is stale vs the current verdicts`
(status.js is byte-identical to main here; I changed nothing under
`frontend/data/backcast/`). Refreshing it needs `scripts/build_status.py`, which
writes a committed `frontend/data/backcast/` file the Stage-0 guardrails
prohibit touching. The neutrality-critical gates — the golden diff, the smoke
suite, `legitimacy_diagnostics --keepers` (holdout quarantine intact), and
audit_keepers' own holdout check — all pass. A stage session (or the owner)
should run `build_status.py` so the gate is end-to-end green.

---

## 8. Cross-year warm-start — the forecast-P0 decision

**Recommendation: unify first, then keep it gated OFF on the forecast path — do not wire
it into forecast P0 as part of this migration.**

Rationale, from `docs/cross-year-warmstart.md` (measured, not assumed):
- The mechanism (`CrossYearBasis` + `apply/export_cross_year_basis`,
  `dispatch.py:1982-2639`) is built, tested, and used **only** by the calibration loop,
  **default-off** (`MARKET_SIM_WARMSTART_XYEAR=1`). runner.py never calls it (AR-6
  "built but unused").
- It is **bit-neutral within a year** but **non-neutral on the forecast trajectory**:
  the ≤0.0033% marginal-tie reshuffle it induces is read by `capacity.evolve_fleet`'s
  per-unit retirement screen (`Σ price·dispatch`, `Σ (price−mc)·dispatch`), and can tip a
  unit across the retire/keep threshold, changing the *next* year's fleet. Measured drift
  was bounded but real (up to 0.39 $/MWh in some years, bit-identical in others).
- Therefore adopting it on the forecast P0 trades trajectory-neutrality for speed — an
  unacceptable swap for a mechanism whose premise is neutrality.

**What unification changes (the payoff):** once Stage 3 puts P0/P1 behind the shared
`pipeline.run_energy_solve`, cross-year warm-start becomes **trivially wireable to the
forecast for free** (same code, thread an `xyear_cache` through runner's year loop) — it
stops being "built but unused." But it should ship **gated OFF on the forecast path**,
with the gate documented, until the **unblocking prerequisite** lands: make the capacity
screen depend only on basis-independent quantities (prices, system totals) rather than
per-unit marginal-tie dispatch. That is a separate economics change (warm-start backlog
#4) with its own validation — explicitly *not* a warm-start change and *not* in scope
here. Stage 3's deliverable therefore includes: (a) the shared solve core accepts an
optional `xyear_cache`; (b) the backcast front-end passes it (preserving today's
behavior); (c) the forecast front-end leaves it `None` with a comment pointing at this
section and the capacity-screen prerequisite.

---

## 9. Stage 1 — complete implementation prompt

Copy-paste the block below as the opening prompt for the Stage-1 session.

```
You are working on the market-simulator repo at /home/user/market-simulator.
Read CLAUDE.md (project rules — especially #1 structure-first, #24 no off-registry
tuning channels, #26 deleted-means-deleted) and
docs/handoffs/orchestrator-unification-plan-2026-07.md (this plan) in full before
touching code. You are executing STAGE 1 ONLY. Do not start Stage 2+.

BRANCH: develop on claude/orchestrator-unification-plan-slw9it (create from latest
origin/main if it does not exist locally). Commit with clear messages; push with
git push -u origin <branch>. Do NOT open a PR unless asked.

GOAL (Stage 1): Create the shared solve-core package skeleton and introduce three typed
contract objects, with ZERO change to any solved number. This stage is pure typing +
scaffolding: it must be byte-identical on every keeper re-solve.

WHAT TO BUILD:

1. New package src/market_sim/pipeline/ with __init__.py and:
   - spec.py:
       @dataclass(frozen=True) DispatchSpec — a frozen bundle of the ~40 arguments the
       dispatch LP + base dispatch_kwargs consume (wind_cf/cap, solar_cf/cap, voll,
       incidence, ttc, interface_groups, link_bidirectional, storage_* arrays, wind_mc/
       solar_mc, storage_discharge_*, rps_target, storage_daily_cycle_hours,
       hydro_gen_idx, hydro_monthly_energy, T). Mirror the dict assembled at
       runner.py:746-786 EXACTLY — same keys, same values. Add a method
       `.to_dispatch_kwargs() -> dict` that returns precisely that dict so call sites can
       swap `dict(...)` for `DispatchSpec(...).to_dispatch_kwargs()` with no value change.
       DO NOT change dispatch.py's signature; this is an assembly-side container only.
       @dataclass(frozen=True) ReserveSpec — a thin typed wrapper over the reserve
       co-opt kwargs that reserve_config.build_reserve_dispatch_kwargs already returns
       (reserve_requirement, reserve_eligible, reserve_supply_cap, reserve_online_gated,
       reserve_online_rho, reserve_headroom_*, reserve_pergen_*, ordc_*,
       reserve_balance_*). Provide `.merge_into(dispatch_kwargs: dict) -> None`. Again:
       no value change — it wraps the existing dict.
   - prior.py:
       @dataclass PriorYearResults — a typed replacement for the 12-key untyped dict
       threaded across years in runner.py:1123-1150 (AR-2). Fields, one per current key:
       fleet_arrays, dispatch_result, prices, peak_demand, planned_additions, mc_cost,
       rps_shadow_price, retrofit_log, storage_power_mw, wind_cap_mw, solar_cap_mw,
       storage_firm_mw. Add `.get(key, default=None)` and `__getitem__` shims so any code
       still reading it dict-style keeps working during the transition (grep confirms the
       consumers: runner.py:371,412,434 and capacity.evolve_fleet). Types from the actual
       producers — do not invent optionality that isn't there.
   - result.py:
       @dataclass YearSolveResult — placeholder for the shared core's return type used in
       Stages 3-4 (result, result_p1, context, p2_state). Define the fields now (typed),
       but nothing calls it yet in Stage 1. Docstring points at Stages 3-4.

2. Refactor runner.py's per-year prior_results dict (built at ~1123-1150, consumed at
   ~371, 412, 434 and passed to capacity.evolve_fleet) to construct and thread a
   PriorYearResults instance instead of a bare dict. Because of the __getitem__/.get
   shims, evolve_fleet and every reader keep working unchanged. Confirm by grep that
   NO reader is missed. Do not change evolve_fleet's internals in this stage.

WHAT NOT TO TOUCH:
- dispatch.py (the LP builder) — unchanged.
- run_calibration.py / run_calibration_full.py — unchanged in Stage 1 (they migrate in
  Stages 2-7). DispatchSpec/ReserveSpec are introduced but only WIRED into the shared
  core later; in Stage 1 they exist and are unit-tested, and optionally runner.py's base
  dispatch_kwargs assembly may be rewritten to `DispatchSpec(...).to_dispatch_kwargs()`
  IF AND ONLY IF the resulting dict is asserted equal key-for-key to the old one. If in
  any doubt, leave runner's assembly alone and just land the containers + PriorYearResults
  — the container wiring is Stage 2.
- Any solved number. This stage changes types, not math.
- ScenarioConfig fields, getattr gates, env knobs — those are Stage 7.

TESTS (add, must pass):
- tests/test_pipeline_spec.py: construct a DispatchSpec from a known small fixture,
  assert .to_dispatch_kwargs() equals the hand-written dict np.array_equal on every
  array and == on every scalar. Same for ReserveSpec.merge_into.
- tests/test_pipeline_prior.py: PriorYearResults round-trips as both attribute and
  dict access; .get() matches dict.get() semantics.
- Extend/verify tests/test_runner.py still passes (it mocks the LP; the PriorYearResults
  swap must not break the mock — adjust the mock to the typed object if needed).

REGRESSION GATE (run before pushing — this is the neutrality proof):
- Re-solve at least ERCOT and one non-ERCOT keeper (e.g. MISO miso-39-reserve-pergen)
  from their frozen results/calibration/<id>/run_config.json, before and after your
  change, and diff with:
    python scripts/regression_check.py <before_dir> <after_dir> --atol 0 --rtol 0
  It MUST report byte-identity (zero deviation) on every column. If it does not, your
  change moved a number — find and remove the difference; a Stage-1 change that is not
  byte-identical is wrong by definition. Keep re-solves within 2023-2025 (quarantine).
- Run pytest tests/ — zero new failures.
- Run python -c "from market_sim import runner; from market_sim import pipeline" to
  confirm import resolution.

DELIVERABLE: the pipeline/ package (spec.py, prior.py, result.py, __init__.py), the
runner.py prior_results→PriorYearResults refactor, the three test files, all green, with
a byte-identity regression report pasted into the commit message or PR-less push note.
Report the headline (byte-identical: yes/no, tests: N passed) and STOP — do not begin
Stage 2.
```

---

## 10. Decisions log (for the sessions that follow)

- **Package name `pipeline/`, not `calibration/`** — the core is shared, not
  backcast-only; §5.
- **A5 (ERCOT single-product supply cap)** fixed in `reserve_config._ercot_design`, not
  hand-wired into runner — one edit, both paths; Stage 2.
- **CAISO bidir/solar-shape/gas-coupling + NEISO coldsnap** are fixed *by unification*
  (Stages 5/6), never by a bespoke runner.py edit — that is the anti-pattern this plan
  exists to end; §2.2.
- **Measured backcast overlays stay divergent, but as config gates in `backcast_config`,
  not as code forks** — rule 12 respected; §1.1, §3.1.
- **Cross-year warm-start**: unify so it's wireable to both, ship gated OFF on forecast,
  document the capacity-screen prerequisite; do not wire forecast P0 here; §8.
- **Neutrality standard is stricter for pure-motion stages (byte-identity) than for
  builder-swap stages (1e-9 + marginal-tie reshuffle)** — a diff above the stage's row is
  a bug, not a cost; §7.2.
- **Compose with iso-model-unification module-universal-first, orchestrator-second**;
  run its file-decomposition Phase 6 *after* this plan's Stage 7; §2.3.
- **env-var ERCOT gas knobs** are a real rule-24 violation but are default-off probes —
  separate cleanup, not in the neutrality-critical path; §4.
