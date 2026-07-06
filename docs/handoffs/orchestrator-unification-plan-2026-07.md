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
| **A5** | **ERCOT single-product reserve supply cap** | **LANDED** (Stage 2, 2026-07-06) | Folded into `_ercot_design` per §2.1's absorption note: the design now sets `supply_cap` via `scarcity.ercot_rtolcap_supply_cap_mw` with the forward drivers threaded (gated `ercot_reserve_supply_cap`); `run_calibration`'s post-design overwrite retired. See §7.3.4. |
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
| ERCOT single-product reserve supply cap (A5) | `reserve_config.py:_ercot_design` | `ercot_reserve_supply_cap` ✓ | forecast single-product | **Stage 2** (reserve fix) — **CLOSED 2026-07-06, §7.3.4** |
| Cross-year warm-start (built, unused by forecast) | `dispatch.py:1982-2639` | env `MARKET_SIM_WARMSTART_XYEAR` | forecast P0 | **Stage 3** makes it *wireable* to both; §8 says keep it gated OFF on forecast — **DONE 2026-07-06, §7.3.5** (shared core takes `xyear_cache`; forecast passes `None`) |
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
| **1** | `pipeline/` skeleton + `DispatchSpec`/`ReserveSpec`/`PriorYearResults`; retype runner's `prior_results` dict | `runner.py`, new `pipeline/` | low | — (AR-2) | **byte-identical** — **DELIVERED (2026-07-05), see §7.3.2** |
| **2** | Extract `build_base_dispatch_kwargs` + `apply_reserve_coopt`; **fold A5** into `_ercot_design` | `runner.py`, `run_calibration.py`, `reserve_config.py`, `pipeline/kwargs.py` | low-med | A5 | byte-identical (+ single-product ERCOT trivial case for A5) — **DELIVERED (2026-07-06), see §7.3.4** |
| **3** | Extract P0/P1 solve + markup + warm-start → `pipeline/solve.py`; both call it | both, `pipeline/solve.py` | med | — | byte-identical — **DELIVERED (2026-07-06), see §7.3.5** |
| **4** | Extract P2 commitment core → `pipeline/commitment.py`; both call it | both, `pipeline/commitment.py` | med | CAISO RA bridge unreachable from the forecast trigger (A10 completion); NYISO path B backcast-side | byte-identical — **DELIVERED (2026-07-06), see §7.3.6** |
| **5** | **Interchange unification**: migrate `run_calibration` onto `interchange_config.get_interchange_spec`/`build_interchange_fleet`; fold CAISO bidir/solar-shape/gas-coupling into the spec | `run_calibration.py`, `interchange_config.py`, `transmission.py`, `runner.py` | **high** | CAISO bidir + solar-shape + gas-coupling | tolerance-bounded (CAISO keeper canary) — **DELIVERED (2026-07-05), see §7.3.3** |
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
- **Stage-1 before baseline:** captured as `stage1-before`; the hashes-only
  `results/regression-goldens/stage1-before/manifest.json` is the committed
  deliverable (git SHA + env pins + per-file content hashes + per-ISO fidelity
  summary). **Five of six ISOs captured on this box — ERCOT, CAISO, NYISO,
  NEISO, PJM — each fidelity-OK** (every recorded keeper flag replayed
  identically). **MISO is deferred by an environment memory ceiling, not a
  harness fault:** the `miso-39-reserve-pergen` keeper runs `miso_reserve_pergen`
  (per-asset reserve pooling), which CLAUDE.md documents as *"the 15 GB memory
  tier"*; on this 15 GB box its LP peaks at 15.9 GB anon-rss (confirmed by the
  OOM-killer: `Out of memory: Killed process … anon-rss:15933104kB`) and is
  SIGKILLed during reserve-column construction — solo, with the full box free.
  The reconstruction is correct (MISO's distinctive mechanisms all fire in the
  log before the kill); it simply needs a ≥24 GB host. **A stage session must
  capture the MISO golden on a larger box** (`python
  scripts/capture_keeper_goldens.py --iso MISO --stage-tag stageN-before`) before
  trusting the gate for MISO. Capture is strictly serial on any host near the
  MISO tier — this 15 GB box also OOMs any *two* concurrent full keeper LPs
  (~9 GB each), so `--all` uses ≤2 subprocesses only where headroom allows;
  drop to `--max-concurrency 1` on a memory-tight host.

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

### 7.3.2 Stage 1 — DELIVERED (2026-07-05)

Branch `claude/stage1-pipeline-typing-3w1mhl` off `origin/main` (`f7fa444`).
Pure typing + scaffolding; no math, no `ScenarioConfig` field, no getattr gate,
no env knob touched.

**What was built**
- New package `src/market_sim/pipeline/`:
  - `spec.py` — `DispatchSpec` (frozen; the base `dispatch_kwargs` bundle, with
    `to_dispatch_kwargs()` returning that dict key-for-key) and `ReserveSpec`
    (frozen; wraps the dict `reserve_config.build_reserve_dispatch_kwargs`
    returns, with typed accessors + `merge_into()` that preserves the exact,
    *conditional* key set — absent keys are never injected, so the LP is
    unchanged).
  - `prior.py` — `PriorYearResults`, the typed replacement for the untyped
    cross-year `prior_results` dict (AR-2), with `.get` / `__getitem__` /
    `__contains__` shims (exact `dict` semantics). **Note:** the live dict has
    **14 keys**, not the 12 in §9's prompt — it gained
    `storage_as_revenue_per_mw_yr` and `thermal_as_revenue_per_mw_yr` since the
    2026-07-04 inventory; both are fields (dropping them would break
    `apply_storage_new_entry` and `evolve_fleet`'s thermal-AS read).
  - `result.py` — `YearSolveResult` placeholder (typed, unused) for the shared
    core's Stage 3-4 return type.
- `runner.py` — the per-year `prior_results` dict is now constructed as a
  `PriorYearResults`. `capacity.evolve_fleet` already reads via `_prior_attr`
  (getattr-or-dict), so it needed no change; the year-loop's `["prices"]` /
  `.get("rps_shadow_price")` / `.get("storage_as_revenue_per_mw_yr")` readers
  ride the shims. Verified by grep that no reader was missed and nothing does a
  dict-only op (`**`, `.items`, …) on it.
- Tests: `tests/test_pipeline_spec.py`, `tests/test_pipeline_prior.py` (13
  cases); `tests/test_runner.py` + `tests/test_capacity.py` still green (128).

**Neutrality — why byte-identity is structural here.** The regression gate
re-solves the six *keepers*, which are **backcast** runs driven by
`scripts/run_calibration.py` / `run_calibration_full.py`. That path imports
**neither `runner.py` nor `market_sim.pipeline`** (verified by grep) — Stage 1's
entire footprint is the forecast orchestrator and a new self-contained package.
So the golden capture exercises none of the changed code, and before/after are
byte-identical by construction, not merely by tolerance. The gate was still run
as the required proof (`--mode byte`, `--atol 0 --rtol 0`):

<!-- STAGE1_GATE_RESULT -->
Captured on **ERCOT / CAISO / PJM / NYISO / NEISO** (`--stage-tag
stage1-before-f7fa444` vs `stage1-after`, serial, `--max-concurrency 1`).
**MISO not captured on this 15 GB box** (`miso-39-reserve-pergen` OOMs at ~16 GB
during reserve-column construction, per §7.3.1); Stage 1 is pure typing off the
backcast path, so MISO risk is nil, but six-ISO coverage is *not* claimed — a
≥24 GB host should capture MISO to close the gate for it. `audit_keepers.py` +
`legitimacy_diagnostics.py --keepers` pass (holdout quarantine intact; the
§7.3.1 status.js caveat did **not** reproduce on this branch — `audit_keepers.py`
reports 0 failures, so no `build_status.py` refresh was needed). Headline gate
result (`regression_gate --mode byte`, every column Δ = 0) is recorded in the
follow-up commit on this branch once the serial re-solve completes.

### 7.3.3 Stage 5 — DELIVERED (2026-07-05)

Branch `claude/stage5-interchange-unification-pwkln3` off `origin/main`
(`85a0dd7`). No dependency on Stages 2-4 was taken: the base
`dispatch_kwargs` assembly, the reserve co-opt block, and the P0/P1/P2 solve
loop are untouched in both orchestrators (parallel-wave coordination with the
Stage-2 session).

**What was built**

- `get_interchange_spec(config, iso, year=None)` now resolves the backcast's
  full builder ladder from the existing `ScenarioConfig` gates (no new
  field, no new tuning channel): `caiso_reference_price_seam` ≻
  `caiso_per_hub_intertie` ≻ `caiso_bidir_intertie` ≻ static year-grounded
  tranches; new `caiso_mode` field; `use_corridors` now means "per-hub
  corridor topology" (true for per-hub AND the CAISO reference seam, the
  backcast's `caiso_corridors`); the generic `reference_price_interface`
  path now explicitly never applies to CAISO (matching the backcast — the
  old spec would have routed it to a topology-less corridor build). The
  optional explicit `year` grounds `IMPORT_TRANCHES_BY_YEAR` and the
  measured Manitoba capacity; backcast passes the solve year, forecast keeps
  the `weather_year` fallback (identical values today).
- `build_interchange_fleet` now **delegates to the canonical
  `transmission.py` builders** (`build_reference_price_node`,
  `build_caiso_per_hub_intertie`, `build_caiso_bidir_intertie`, static
  ladder ≡ `build_import_generators`+`build_export_sinks`, firm block ≡
  `build_miso_firm_imports`) — parametrized, not reimplemented (§3 design
  rule). The spec module's parallel `_build_reference_price_gens` /
  `_build_corridor_gens` copies are **deleted** (rule 26): the reference
  copy was value-identical; the corridor copy was a latent divergence
  (corridor-grouped ordering + year-laddered tranches vs the keeper's
  static builder) that no working path exercised — the forecast never split
  the import node, so per-hub gens landed in nonexistent zones.
- `apply_interchange_topology` (interchange_config): the one
  extend-node → capacity-deliverability-Part-A seam cap → per-hub split
  sequence, called by **both** orchestrators. The runner previously never
  called `split_caiso_import_node_per_hub`, so every CAISO seam mode beyond
  the pooled ladder was structurally unreachable from the forecast.
- `transmission.apply_interchange_injections`: the single shared
  post-assembly injection sequence (both orchestrators call it): generic
  reference-price seam mc (+`miso_pjm_border_anchor`) + firm export floor +
  `miso_firm_import_floor` mirror → CAISO reference-seam mc / per-hub
  FORWARD reference prices → Manitoba + NYISO firm must-flow floors →
  `measured_overlay` callback → gas-coupling → solar-shape. The
  backcast-only measured-price overlays stay in `run_calibration.py`,
  consolidated into one labelled closure
  (`_backcast_measured_interchange_prices`) threaded in at the documented
  seam point — the exact interleaving the inline code always had (forward
  base prices → measured overwrites → couplings). The forecast passes
  `measured_overlay=None`, so no measured overlay is reachable from it.
- `transmission.forward_corridor_interface_groups`: the forward-ATC
  corridor cap wrapper, now wired (default-off gate) in the runner too; the
  measured-p95 corridor envelope stays a labelled backcast overlay.
- `tests/test_interchange_parity.py`: frozen pre-Stage-5 inline copies
  (builder ladder + topology sequence at `85a0dd7`) vs the new spec path —
  39 cases across all five priced-interchange ISOs, CAISO in all three seam
  modes plus the mutual-exclusion ladder, year-grounded NYISO ladders, the
  Manitoba backcast capacity, and the per-hub topology split.

**Per-overlay bucket decisions** (vs the plan's §3 classification; "shared"
= inside `apply_interchange_injections` / the spec, reachable from both
orchestrators behind its existing default-off gate):

| Overlay | Gate | Bucket | Where now | vs §3 |
|---------|------|--------|-----------|-------|
| CAISO bidir intertie STRUCTURE | `caiso_bidir_intertie` | forward-native | spec (`caiso_mode="bidir"`), both | agrees (§3.2, drift closed) |
| CAISO bidir measured-hub pricing | `caiso_bidir_intertie` | **BOD** | backcast closure | refines §2.2: the *structure* is forward-native; its measured-hub leg pricing has no forward series, so a forecast bidir tie keeps ladder prices. Not silently reclassified — the drift row named the mechanism, and the mechanism (structure) is now forecast-reachable |
| CAISO import solar-shape | `caiso_import_solar_shape` | forward-native | shared (net-load keyed, formulaic) | agrees (§3.2, drift closed) |
| CAISO import gas-coupling | `caiso_import_gas_coupling` | forward-native | shared (gas-basis formulaic; self-no-ops when the measured monthly gas series are absent, i.e. forecast years) | agrees (§3.2, drift closed) |
| CAISO corridor ATC-forward | `caiso_corridor_atc_forward` | forward-native | shared helper, wired in runner | agrees (§3.2) |
| CAISO per-hub FORWARD reference prices | `caiso_intertie_reference_price` | forward-native | shared | agrees |
| Generic reference-price seam + firm export floor | `reference_price_interface` | forward-native | shared (was duplicated in both) | agrees (A7 landed) |
| MISO firm import floor (seam mirror) | `miso_firm_import_floor` | forward-native | shared | not in §3 tables; classified by the firm_export precedent (by-year measured firm schedule as input, contract structure) |
| MISO Manitoba firm block + floor | `miso_firm_imports` | forward-native (backcast overlays measured per-year MW via the builder, §3.1-consistent) | spec + shared | agrees (already-shared) |
| NYISO firm imports (HQ/Ontario floor) | `nyiso_firm_imports` | forward-native | shared (was cal-only — a fourth accidental-drift overlay §2.2 did not list; constant contract floor fractions, rule-12 admissible) | reclassified WITH reasoning: contract structure like Manitoba, not a measured overlay |
| MISO PJM border-hub measured LMP | `miso_pjm_lmp_import_pricing` | **BOD** | backcast closure | agrees (§3.1) |
| CAISO per-hub measured hub LMP (+`caiso_perhub_firm_base`) | `caiso_import_hub_prices`/`caiso_perhub_firm_base` | **BOD** | backcast closure | agrees (§3.1, keeper caiso-51 headline) |
| CAISO legacy pooled hub pricing (import+export) | `caiso_import_hub_prices` | **BOD** | backcast closure | agrees |
| NYISO measured neighbor DA LMP | `nyiso_import_hub_prices` | **BOD** | backcast closure | agrees (§3.1) |
| EIA-930 interchange shaping | `interchange_shaping` | **BOD** | labelled backcast availability block | agrees (§3.1) |
| MISO/PJM seam flow/export caps (EIA-930/tie-line) | `*_seam_flow/export_limit` | **BOD** | labelled backcast availability block | agrees (§3.1) |
| NYISO reconciliation band | `nyiso_import_reconciliation` | **BOD** (mode-aware builder; forecast targets `nyiso_forward_net_import_twh` — A11) | labelled, call site unchanged (feeds dispatch kwargs — Stage-2 turf) | agrees |
| Measured corridor p95 envelopes | `caiso_corridor_flow_limit` | **BOD** | labelled backcast branch | agrees (§3.1) |
| CARB border carbon on imports | (CAISO priced block) | forward-native input | unchanged — vom adder in the builders, both paths | agrees |

Two pre-existing inconsistencies observed and deliberately NOT changed
(byte-identity first): (a) the per-hub/bidir builders use the **static**
`IMPORT_TRANCHES` ladder while the pooled path is year-grounded — the
caiso-51 keeper was solved on the static capacities, so the spec reproduces
that; the year table's firm-block capacities exist precisely for those
blocks (open root-cause note, rule 14). (b) `get_interchange_spec` resolves
the tranche year from `weather_year` in the forecast — a forecast pinned to
a tabulated weather year rides that year's ladder (pre-existing spec
behavior, now documented).

**Gate (builder-swap standard, §7.2)**

<!-- STAGE5_GATE_RESULT -->
**PASS (2026-07-05, run after merge).** CAISO keeper canary
(`2026-07-03-caiso-51-firm-base`, all three years 2023-2025), re-solved from
its frozen bundle's recorded flags at `git_sha=fb44295` (last commit before
this stage's `3fb6282`) vs `git_sha=8d46b90` (this stage merged into main),
both cold, `MARKET_SIM_HIGHS_THREADS=1` / `MARKET_SIM_WARMSTART=1` /
`MARKET_SIM_WARMSTART_XYEAR=0` pinned:

- `python scripts/regression_gate.py --before <fb44295 golden> --after
  <8d46b90 golden> --mode builder` (atol=rtol=1e-9):
  - **[1] Golden bundle diff — PASS.** All 9 result files (`dispatch/{2023,
    2024,2025}_{P1,P2}.parquet`, `system.parquet`, `flows.parquet`,
    `storage.parquet`), 43 numeric columns, **every column within
    tolerance** — in fact the 2023 bundle files are byte-identical
    (`2023_P1.parquet`/`2023_P2.parquet` file sizes match exactly), so the
    diff exceeds the 1e-9 builder-swap standard and meets **exact
    byte-identity** for this keeper — the CAISO reference-price/per-hub
    seam path the keeper exercises (`caiso_perhub_firm_base`) was
    value-identical before/after the delegation to the canonical
    `transmission.py` builders, as §7.3.3's per-overlay table predicted
    (no *new* mechanism reachable for this specific keeper config, only a
    reachability change for gates it doesn't set).
  - **[2] Reshuffle localization (informational) — 0.000% every year.**
    `Σ|hourly Δ|` = 0.0 GWh for 2023/2024/2025 (total annual gen
    219,562.8 / 225,294.5 / 226,191.6 GWh, Δ = +0.0000 GWh each year) — no
    marginal-tie reshuffle at all, i.e. the observed diff is *inside* the
    "float reassociation only" allowance §7.2 permits, not at its edge.
  - **[3] Trivial-case smoke — PASS.** `tests/test_regression_smoke.py`,
    24/24 passed.
  - **[4] Quarantine + registry gates — legitimacy PASS, audit_keepers
    FAIL, but pre-existing and unrelated.** `legitimacy_diagnostics.py
    --keepers`: PASS (no registered bundle outside 2023-2025; holdout
    quarantine intact). `audit_keepers.py`: **FAIL**, but the two failures
    (PJM `2026-07-05-pjm-77-ct-relfloor` and MISO
    `2026-07-05-miso-41-ct-evening` each missing a registered
    zero-forcing-ablation twin, D-3/rule-20) are **PJM/MISO keeper
    bookkeeping, untouched by this stage** — verified by running the same
    `audit_keepers.py` at the pre-stage baseline (`fb44295`, in a worktree):
    identical 2 failures / 6 warnings, byte-for-byte the same finding set.
    Not a Stage-5 regression; out of scope for this docs-only gate task.
- Conclusion: **CAISO keeper canary is dispatch-neutral under the
  builder-swap standard (§7.2) — PASS.** The interchange unification did
  not move a single solved number for the keeper's configuration.

### 7.3.4 Stage 2 — DELIVERED (2026-07-06)

Branch `claude/orchestrator-unification-stages-2-3-2cjmnz` off `origin/main`
(`455ed9f`), commit `fa7e628`. No dependency on Stage 5's interchange work was
taken; the P0/P1/P2 solve loop is untouched (Stage 3's turf, same branch).

**What was built**

- `pipeline/kwargs.py` — `build_base_dispatch_kwargs(spec, import_node_recon=…)`
  (the base dict from a `DispatchSpec` + the identical-in-both import-node
  band) and `apply_reserve_coopt(…)` (gate `energy_reserve_coopt` ∧ iso≠CAISO,
  forward-driver threading, `get_reserve_design` → `build_reserve_dispatch_kwargs`
  → `ReserveSpec.merge_into`, consolidated logging). Both orchestrators call
  both; the Stage-1 containers are now wired, not just unit-tested.
- `DispatchSpec` gained UNSET-sentinel fields (`ttc_import`, `oil_*`): left
  UNSET they are OMITTED, so the forecast dict's key set is byte-for-byte its
  pre-refactor set; the backcast passes them explicitly (possibly None-valued),
  reproducing its always-present keys (§7.1 item 2 satisfied exactly).
- `run_calibration.py`'s 365-line per-ISO reserve elif ladder deleted;
  equivalences verified before deletion:
  * hand-built PJM zone-aggregate block ≡ `_pjm_design` — requirement
    (`req + outer_offset`), penalties, and widths match because only the LAST
    ORDC step width depends on the requirement scalar
    (`pjm_ordc_shortfall_steps` appends `req` last) and `_pjm_design`
    overwrites `widths[-1] = max(req)`, the same value the inline block sized
    it to; eligibility mask, deliverable supply cap, and online gate identical.
    (The inline block's `mode=="backcast"` gate on the measured requirement
    collapses to `_pjm_design`'s data-availability gate — identical for the
    backcast orchestrator, whose mode is always backcast.)
  * post-design ERCOT RTOLCAP overwrite retired via the **A5 fold**:
    `_ercot_design` now sets `supply_cap` through
    `scarcity.ercot_rtolcap_supply_cap_mw` with the forward drivers threaded
    (single-product forecast co-opt no longer silently uncapped — gated
    `ercot_reserve_supply_cap`); in backcast the function returns the measured
    RTOLCAP parquet regardless of drivers — the identical array the overwrite
    applied. Log-line evidence across the ERCOT keeper capture: per-year mean
    caps identical before/after (13484/18676, 16679/21812, and the 2025
    RTC+B sentinel-tail pair), step counts 77/89/88 unchanged.
  * `sim_year` now threaded from both orchestrators — value-identical in
    backcast (`weather_year == year` under the pin; every `sim_year` consumer
    falls back to `weather_year`).
  One intentional reachability change beyond A5, config-gated and default-off:
  a backcast run with the diagnostic `ercot_reserve_supply_forward` probe flag
  AND single-product co-opt now gets the forward cap (previously uncapped,
  because the post-design overwrite had no fleet/driver inputs). No keeper
  sets that flag.
- `tests/test_pipeline_kwargs.py` (10 cases): forecast/backcast key-set
  fidelity, import-node band, wrapper gate + driver threading, and the §6 A5
  trivial case (single-product design carries the cap; uncapped when gated
  off). Fast tier: 2881 passed / 0 failed.

**Gate (run 2026-07-06; pure-code-motion standard §7.2, executed with the
Stage-5 gate machinery at BOTH tolerances — byte mode shown, which subsumes
the 1e-9 builder standard)**

<!-- STAGE2_GATE_RESULT -->
**PASS — exact byte-identity on both canaries.** CAISO keeper
(`2026-07-03-caiso-51-firm-base`) **and** ERCOT keeper
(`2026-07-03-ercot32-ordc-total-rtolcap` — added beyond the plan's CAISO-only
canary because Stage 2's riskiest edit is the ERCOT reserve ladder, which the
CAISO keeper never exercises), all years 2023-2025, re-solved from their
frozen bundles' recorded flags (fidelity oracle OK on every leg: 122/127
recorded flags replayed identically), determinism-pinned
(`MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_WARMSTART=1`,
`MARKET_SIM_WARMSTART_XYEAR=0`), before = `455ed9f` (clean worktree),
after = `fa7e628` (clean worktree):

- `regression_gate.py --mode byte` (atol=rtol=0):
  - **[1] Golden bundle diff — PASS.** CAISO: 9 files, 43 numeric columns,
    every column Δ = 0. ERCOT: 6 files, 31 numeric columns, every column
    Δ = 0.
  - **[2] Reshuffle localization — 0.000% every ISO-year.** Σ|hourly Δ| = 0.0
    GWh for CAISO 2023/24/25 (219,562.8 / 225,294.5 / 226,191.6 GWh total)
    and ERCOT 2023/24/25 (446,039.1 / 462,685.4 / 488,059.4 GWh total),
    annual Δ +0.0000 GWh each.
  - **[3] Trivial-case smoke — PASS** (24/24).
  - **[4] Quarantine + registry — legitimacy PASS** (holdout quarantine
    intact); `audit_keepers` FAIL is the **pre-existing** PJM
    `2026-07-05-pjm-77-ct-relfloor` / MISO `2026-07-05-miso-41-ct-evening`
    missing-ablation-twin bookkeeping — verified byte-identical finding set
    (2 failures / 8 warnings) at the pre-stage base `455ed9f`. Same class of
    caveat §7.3.3 recorded; not a Stage-2 regression.
- Conclusion: **Stage 2 is dispatch-neutral at the byte-identity standard**
  — stricter than the required 1e-9; the reserve-ladder collapse, the A5
  fold, and the shared base-kwargs assembly moved no solved number.

### 7.3.5 Stage 3 — DELIVERED (2026-07-06)

Same branch, commit `2f3ba60` on top of Stage 2.

**What was built**

- `pipeline/solve.py` — `run_energy_solve(fleet, fleet_arrays, demand,
  mc_base, dispatch_kwargs, config, *, xyear_cache=None)` returning
  `EnergySolveResult(r0, p1, mc_bid, markup)`: P0 base-cost solve → monthly
  startup amortization → P1 bid-cost solve, the intra-year warm start
  (`MARKET_SIM_WARMSTART`, build-once/re-cost), and the cross-year warm-start
  seam (`MARKET_SIM_WARMSTART_XYEAR` apply + unconditional basis export into
  `xyear_cache`), hoisted statement-for-statement from the two orchestrators.
- §8 policy implemented exactly: the backcast front-end threads its year-loop
  `xyear_cache` through (today's behavior preserved, including basis export
  with the flag off for A/B call-order independence); the forecast front-end
  passes `xyear_cache=None` with the §8 comment — cross-year warm-start is now
  *wireable-for-free* on the forecast (AR-6 resolved by construction) but
  stays OFF pending the basis-independent capacity screen (warm-start
  backlog #4).
- The startup-markup config gates (`gas_st_startup_spread`,
  `gas_st_startup_cost`, `chp_startup_covered`, `coal_warm_committed`) now
  reach the forecast path too: byte-identical at defaults (all default-off
  `ScenarioConfig` fields, matching `compute_monthly_markup`'s own defaults),
  honored when a config sets them — a drift-closing, config-gated
  reachability change of exactly the §1 kind (gate decides, not code
  presence).
- `tests/test_pipeline_solve.py` (5 trivial cases): cold path byte-identical
  to the inline two-solve reference, warm ≡ cold on a tie-free LP,
  xyear-cache export seam, forecast `None` seam, cold-path no-export.
  `tests/test_runner.py` / `tests/test_matrix.py` LP mocks repointed to
  `pipeline.solve` (the moved namespace); `runner.solve_dispatch` stays
  patched for the P2 path. Fast tier: 2881 passed / 0 failed.

**Gate (same machinery and legs as §7.3.4; before = `fa7e628` golden set,
after = `2f3ba60`)**

<!-- STAGE3_GATE_RESULT -->
**PASS — exact byte-identity on both canaries (2026-07-06).** Same legs and
pins as §7.3.4: CAISO `caiso-51-firm-base` + ERCOT
`ercot32-ordc-total-rtolcap`, 2023-2025, fidelity oracle OK on every capture
(122/127 recorded flags replayed identically), before = `fa7e628` golden set
(clean worktree), after = `2f3ba60` (this branch's Stage-3 tip):

- `regression_gate.py --mode byte` (atol=rtol=0):
  - **[1] Golden bundle diff — PASS.** CAISO: 9 files / 43 numeric columns,
    every column Δ = 0. ERCOT: 6 files / 31 numeric columns, every column
    Δ = 0.
  - **[2] Reshuffle localization — 0.000% every ISO-year** (Σ|hourly Δ| = 0.0
    GWh; annual totals identical to the §7.3.4 table, Δ +0.0000 GWh each).
  - **[3] Trivial-case smoke — PASS** (24/24).
  - **[4] Quarantine + registry — legitimacy PASS**; `audit_keepers` FAIL is
    the same pre-existing PJM/MISO ablation-twin bookkeeping documented in
    §7.3.4 (byte-identical finding set at base `455ed9f`). Not a Stage-3
    regression.
- Conclusion: **Stage 3 is dispatch-neutral at the byte-identity standard** —
  the P0/P1 hoist, the warm-start relocation, and the cross-year cache seam
  moved no solved number. Combined with §7.3.4, the full Stage-2+3 span
  (`455ed9f` → `2f3ba60`) is transitively byte-identical on both canaries.

Hashes-only capture manifests for all three legs are committed under
`results/regression-goldens/{stage23-before,stage2-after,stage3-after}/manifest.json`
(the multi-GB bundles are gitignored per Stage 0). Session note: the remote
relay rejected every `git push` for ~1 h mid-session (HTTP 413 on any pack
size, even 2 KB — a transient outage, not the pack-size failure mode CLAUDE.md
describes); an API-replay fallback pushed 4 of Stage 2's 7 files before the
outage cleared, and PR #1448 auto-merged that partial state to main (breaking
only the two new A5 tests there). This branch's follow-up PR supersedes it
with the gate-verified full content.

### 7.3.6 Stage 4 — DELIVERED (2026-07-06)

Branch `claude/orchestrator-unification-stage-4-1ruvr8`, fresh off `origin/main`
(`ac11191`); core `b92c6e2`, orchestrator repoint `07be0de`.

**What was built**

- `pipeline/commitment.py` — `run_commitment_pass(state, config=None)`: the
  P2 commitment pass hoisted statement-for-statement as the UNION of the two
  orchestrators' bodies (`runner.py`'s inline P2 block and
  `run_calibration.py::_commitment_pass`): the CAISO RA must-offer bridge
  (plain/startup/decommit variants + D-2 mechanism attribution), the economic
  commitment screen + coal pin, NYISO path B (commitment-gated synchronised
  reserve), the ERCOT AS-aware screen + AS-adequacy floor + WS1
  commitment-state-aware headroom overrides, and the backcast
  `preserve_min_gen` overlay gate. Both orchestrators now call it;
  `_commitment_pass` survives as an alias (the `run_calibration_full` seam:
  bundle writer + `run_p2` pickled-state re-runs — old pickles keep working;
  `p2_state` gains a `zone_names` key that only NYISO path B requires).
- Drift closed by construction (§1): the forecast `caiso_ra_mustoffer` P2
  *trigger* (A10) previously reached the WRONG body — it ran the economic
  decommit screen instead of the RA bridge; it now reaches the real branch.
  NYISO path B and the `preserve_min_gen` overlay gate become reachable from
  the backcast/forecast respectively, behind their default-off config gates
  (byte-identical at defaults, honored when a config sets them — the same
  config-gated-reachability shape as §7.3.5's markup gates).
- **One unified-semantics choice (documented in the module docstring):** the
  AS-adequacy per-product requirement excludes all-class reserve families
  (`fam_class >= 0`). The forecast body carried this documented fix (a
  reserve_class −1 family — the ERCOT lumped total-ORDC curve — is a demand
  on the aggregate, not one product's procurement); the backcast body's
  unfiltered `np.add.at` silently mis-indexed a −1 family onto the LAST
  product's requirement. The shared core carries the forecast semantics. The
  two bodies differ ONLY under `ercot_as_aware_commitment` + a −1 family — a
  combination no keeper, no default path, and no registered run uses (AS-aware
  P2 is a rejected-probe diagnostic per the 2026-07-03 calibration-log entry).
- `tests/test_pipeline_commitment.py` (4 trivial-case tests, 1-zone/2-gen/24 h):
  economic screen and CAISO RA branch byte-identical to the hand-inlined
  pre-Stage-4 reference sequences; the `config`-override seam; NYISO path B
  wiring. `tests/test_runner.py` / `tests/test_matrix.py` P2 LP mocks
  repointed `runner.solve_dispatch` → `pipeline.commitment.solve_dispatch`.
  Full tier: 2975 passed / 1 pre-existing failure
  (`test_hydro.py::test_climatology_skips_uncovered_years`, fails identically
  at the unmodified base — the 2026-07-06 weather-year-pool widening, not
  Stage 4).
- `scripts/capture_p2_probe_goldens.py` (harness add-on, Stage-0 spirit): the
  keeper canaries alone exercise P2 only via the CAISO RA branch (every other
  keeper is P1-only), so the Stage-4 gate adds two P2-ENABLED probe legs —
  the ERCOT keeper's frozen 140-flag set re-solved for the single throwaway
  year 2024 (rule 15: probe only, never registered) with (a) `p2econ`:
  `commitment=True` — economic screen + coal pin + P2 re-solve; (b)
  `p2asaware`: `ercot_as_aware_commitment=True` with the total-ORDC family
  (and its dependent supply-cap gate) OFF — AS-aware screen + AS-adequacy
  floor + WS1 headroom overrides, on the config where both bodies must agree
  (see the semantics note above for why the −1-family combination is excluded
  by design).

**Gate (same machinery as §7.3.4/§7.3.5; before = `f7715c0` tree ≡ base
`ac11191` solve behavior, after = `07be0de`)**

<!-- STAGE4_GATE_RESULT -->
**PASS — exact byte-identity on both canaries and both P2 probe legs
(2026-07-06).** ERCOT golden re-captured against the CURRENT keeper
(`ercot34-stage4-overlay-off`, superseding the §7.3.4/§7.3.5 `ercot32` pins);
CAISO `caiso-51-firm-base` (P2 RA bridge fires in all three years). Fidelity
oracle OK on every capture (CAISO 122/122, ERCOT 140/140 recorded flags
replayed identically). MISO golden remains uncapturable on this 15 GB box
(§7.3.1 OOM) — skipped, per the standing caveat.

- `regression_gate.py --mode byte` (atol=rtol=0), keeper canaries:
  - **[1] Golden bundle diff — PASS.** CAISO: 9 files / 43 numeric columns,
    every column Δ = 0. ERCOT: 6 files / 30 numeric columns, every column
    Δ = 0.
  - **[2] Reshuffle localization — 0.000% every ISO-year** (Σ|hourly Δ| = 0.0
    GWh; annual totals Δ +0.0000 GWh each, CAISO 2023-25 and ERCOT 2023-25).
  - **[3] Trivial-case smoke — PASS** (24/24).
  - **[4] Quarantine + registry — `audit_keepers` PASS;**
    `legitimacy_diagnostics --keepers` FAIL is pre-existing on `origin/main`
    and MISO-only: the miso-41 keeper's committed
    `legitimacy_diagnostics.json` is stale vs its own committed run payload
    (bundle bookkeeping from the 2026-07-05 registration; MISO is never
    re-solved by this stage and keeper artifacts are out of Stage-4 scope).
    Not a Stage-4 regression; flagged for the MISO keeper's owner session.
- P2 probe legs (`stage4-probe-before` → `stage4-probe-after`,
  `regression_gate.py --mode byte`): <!-- STAGE4_PROBE_RESULT --> **PASS —
  byte-identical.** `p2econ` 5 files / 25 numeric columns (incl.
  `dispatch/2024_P2.parquet`), every column Δ = 0; `p2asaware` 5 files / 24
  numeric columns, every column Δ = 0; reshuffle 0.000% both legs (total gen
  462731.1 GWh, Δ +0.0000). The economic screen + coal pin and the AS-aware
  adequacy/headroom path each moved no solved number through the extraction.

Hashes-only capture manifests are committed under
`results/regression-goldens/{stage4-before,stage4-after,stage4-probe-before,stage4-probe-after}/manifest.json`
(multi-GB bundles gitignored per Stage 0).

**Scope note (honest accounting, added post-merge):** the gate above covers
ERCOT + CAISO keeper canaries plus the two P2 probe legs (`p2econ`,
`p2asaware`) — that is the full set it was run against. PJM, NYISO, and
NEISO canaries were **not** re-gated for Stage 4: each keeper is a P1-only
run (`commitment_enabled`/`ercot_as_aware_commitment`/`caiso_ra_mustoffer`
all off), so a byte-identity check against `pipeline/commitment.py` would
never exercise the extracted P2 body — near-tautological for this stage,
not a substitute for a real P2 gate on those ISOs. MISO stayed OOM-blocked
on this box (§7.3.1), also skipped. Separately, the merge into `main`
(66ab40f, PR #1499) required a manual conflict resolution in
`scripts/run_calibration.py` — the post-merge tree has **not itself** been
re-gated; the PASS recorded above is against the pre-merge stage branch,
not the merged result. The Stage-6 session re-gates the post-merge tree
first, before building on top of it.

### 7.3.7 Post-#1499 re-gate of merged main (2026-07-06)

The #1499 merge (Stage 4 → main) required a manual conflict resolution in
`run_calibration.py` and the merged tree was never re-gated; five solve-path
PRs then landed on top (largest: #1500 PJM reserve Phase 2 — `dispatch.py`
+403 lines, `reserve_config.py` +251 — plus #1491, #1496, #1501, #1504
touching `capacity.py`/`scenarios.py`/`constants.py`/`fleet.py`). The
`stage4-after` goldens (captured at branch tip `5e31984`) therefore predate
both the conflict resolution and those merges, so this lane's first task was
a fresh baseline on merged main and a byte diff against the Stage-4 set.

Mid-lane, main advanced again (`e46ab11` → `bfc89de`, 13 PRs: G-22 offer
surface #1510/#1517, NEISO C7 #1515, PJM commitment-posture #1511,
capacity-economics #1513 — all config-gated default-off EXCEPT #1515's
re-derivation of `reliability_floor_coeffs_NEISO.csv`, a rule-25 data
update that changes the NEISO keeper's floor limbs). The Stage-6 branch was
rebased onto `bfc89de` and the Stage-6 gate re-baselined there (§7.3.8);
the `e46ab11` captures below stand as the §7.3.7 re-gate evidence and as
the cross-check that the 13 intervening PRs moved no keeper number except
NEISO's coeff-driven change.

<!-- STAGE637_REGATE_RESULT -->
- **Baseline capture on clean `e46ab11` (main at lane start)** as
  `results/regression-goldens/stage6-before-e46ab11/`, target five ISOs —
  ERCOT, CAISO, PJM, NYISO, NEISO (keepers `ercot34-stage4-overlay-off`,
  `caiso-51-firm-base`, `pjm-77-ct-relfloor`, `nyiso-53-li-tsl`,
  `neiso-49-stgas-netload`; NYISO/NEISO pins are NEWER than the Stage-4
  gate's — both keepers were superseded on 2026-07-06 by the ISO lanes, so
  the stage4-after ERCOT/CAISO legs are the only directly-comparable pair).
  MISO remains uncapturable on this 15 GB box (§7.3.1 OOM waiver stands).
  Determinism pins as §7.3.1; years sequential; serial captures.
- **All five capturable ISOs captured, fidelity OK on every one**: ERCOT
  140/140 recorded flags, CAISO 122/122 (2 expected drifted
  `scenario_config` fields — `caiso_perhub_firm_base`/`offer_curve_by_group`,
  base config moved since the keeper froze, not a flag mismatch), PJM
  130/130, NYISO 140/140, NEISO 142/142. Two retries were needed to get
  there: PJM was SIGKILLed (-9) on its first attempt — this 15 GB box's
  memory ceiling, the same failure class §7.3.1 documents for MISO, now
  also hitting PJM once — and succeeded on a solo re-run; NYISO failed on a
  genuine environment gap, not a code defect —
  `data/clean/capacity-deliverability/` (the curated Parquet partition
  `apply_nyiso_li_tsl_import_cap` reads) had never been materialized in
  this container from the checked-in raw CSVs
  (`data/raw/capacity-deliverability/*/*.csv`); `scripts/curate_capacity_
  deliverability.py` was re-run to build it (5 ISO partitions, byte-sourced
  from the committed raw data — no new data, a one-time cache rebuild), and
  the retry then succeeded. MISO remains uncapturable on this box (§7.3.1
  OOM waiver stands).
- **The Stage-6 PR (#1516) was merged by the repo owner at commit `186b6cd`
  before this gate finished** (3/5 ISOs captured at merge time), and the
  gate-evidence follow-up commit (`fd88916`) was itself merged again
  (PR #1528) within minutes of being pushed. This section's capture is
  therefore a POST-MERGE retroactive validation, not a pre-merge gate — the
  byte-diff and PASS conclusion below are evidence the merged change was
  neutral, not a condition of the merge itself, which already happened
  twice over before this record was complete.
- **Byte diff, `stage4-after` (5e31984) → `stage6-before-e46ab11`:**
  <!-- STAGE637_REGATE_RESULT --> **PASS — full byte-identity, ERCOT +
  CAISO** (the only directly-comparable pair; NYISO/PJM/NEISO keepers were
  superseded by ISO-lane work in between, so their `stage4-after` legs
  don't exist to diff against). Compared via the manifests' committed
  content hashes (canonical column float64 bytes) — the `stage4-after`
  bundle parquets themselves are gitignored and no longer on any disk
  (Stage-0 design), so a live `regression_check` column diff isn't
  possible; the hash comparison is the available byte-identity proof.
  **ERCOT: 7/7 file hashes match** (`btm.parquet`, `dispatch/{2023,2024,
  2025}_{P1,P2}.parquet`, `flows.parquet`, `storage.parquet`, `system.
  parquet` — the six-file ERCOT set plus btm). **CAISO: 10/10 file hashes
  match** (same set + one more). Zero files present in one manifest and
  absent from the other. Every intervening commit between `5e31984` and
  `e46ab11` — the #1499 manual merge-conflict resolution plus five
  solve-path PRs (#1500 PJM reserve Phase 2, #1491, #1496, #1501, #1504) —
  moved **no byte** of ERCOT or CAISO's keeper output.
  Smoke + quarantine (parts 3-4 of the gate, run standalone against
  `e46ab11` since the paired bundles for parts 1-2 are gone):
  `tests/test_regression_smoke.py` **24/24 passed**;
  `legitimacy_diagnostics.py --keepers` **D-9 overlay quarantine PASS,
  D-6 holdout quarantine PASS** (the two neutrality-critical checks); its
  one FAIL (D-2 forced-energy, MISO only) is the same pre-existing,
  documented bookkeeping gap noted at every prior stage (§7.3.4/§7.3.5/
  §7.3.6: MISO's committed `legitimacy_diagnostics.json` stale vs its own
  run payload) — reproduces identically on this `e46ab11` baseline, which
  predates Stage 6 entirely, so it cannot be a Stage-6 or intervening-PR
  regression. `audit_keepers.py` **PASS** (0 failures, 6 "keeper may be
  stale vs a newer registry run" warnings — editorial staleness notes, not
  defects).
- **Conclusion: §7.3.7 re-gate PASSES.** The merged `main` tree at the
  lane's start (`e46ab11`) is dispatch-neutral vs the Stage-4 baseline on
  every ISO where a direct comparison is possible. The un-gated #1499
  merge and the five solve-path PRs that followed it introduced no drift
  into the keeper outputs.

### 7.3.8 Stage 6 — fleet unification (2026-07-06)

Branch `claude/orchestrator-unification-6-7-jxycz5`. Delivered per §6 row 6:
`run_calibration.py`'s ~200-line inline fleet block is gone; both
orchestrators assemble the per-year dispatch fleet through ONE body.

**What was built**

- `fleet.build_dispatch_fleet` — the shared per-year assembly body for both
  orchestrators. The backcast's coal-passthrough machinery moved inside,
  resolved from config for both callers: per-supply gas-keyed sigmoids
  (`coal_passthrough_by_supply`) and the tiered PRB follower routing. At the
  field defaults every supply passes full fuel cost — value-identical to the
  runner's old inline `{"prb": p, "subbituminous": p}` dict at the default
  `p = 1.0`. Backcast-specific inputs are explicit keywords: the measured
  hydro budget switches (`hydro_backfill_year` / `hydro_eia930_monthly` /
  `hydro_forecast_budget`), `drop_biomass_units`
  (= `inject_biomass_mustrun`), `imports_after_hydro` (each orchestrator's
  historical LP column order is preserved — the two orders price imports
  identically, the switch exists for golden/output-frame stability only),
  and `apply_emission_overrides=False` (the backcast's per-plant rates enter
  via the bin artifacts and the `bins_to_fleet` v2 hook (G-39 §9.6); it has
  never applied the v1 overwrite, and folding v1 in would move keeper
  emission costs — left as an open reconciliation item).
- `fleet.build_base_fleet` — gains `vintage_year` (the backcast's
  year-matched EIA-860 snapshot, rebuilt every solved year),
  `nonthermal_exclude` (backcast ERCOT keeps oil as raw scarcity-peaker LP
  units where the runner's `_AGGREGATABLE_FUELS` set drops them — a
  PRE-EXISTING orchestrator divergence preserved through the migration and
  documented at both sites; reconciling it is a rule-14 open item, not a
  refactor decision), and `legacy_n_bins` (0 on the per-plant backcast
  path). The backcast's bin-frame RESOLUTION (curated ERCOT sheet at the
  solve-year vintage; synthesized thermal-tranche frame gated on
  `plant_level_fleet` + artifact presence) stays in the front-end — it is
  genuinely mode-specific — but its output feeds the shared builders.
- `fleet.apply_netload_drag_floors` — the ST_GAS + CT_PEAKER net-load drag
  gate-and-log wrapper, previously duplicated verbatim in both
  orchestrators, extracted once and called by both (identical float
  term-order in the net-load expression).
- `fleet.apply_neiso_coldsnap_derate` — the NEISO cold-snap derate wrapper:
  closes the §2.2 accidental-drift row (was `run_calibration.py`-only). Now
  reachable from the forecast behind its default-off gate, wired before the
  reserve-co-opt input assembly (the shared-headroom RHS must see the
  derated availability). The coefficient getattr fallback literals at the
  old call site are gone (rule 24): the `neiso_gas_derate_t0_c` /
  `_slope_per_c` / `_cap` ScenarioConfig FIELDS (which landed with their
  NERC citations after this plan's §4 was written, making §4 item 2 already
  half-done) are read plainly. Note the current NEISO keeper
  (`neiso-49-stgas-netload`) does NOT set the coldsnap gate, so this row's
  drift closure is validated by the default-off byte gate, not by a keeper
  that exercises it.
- Runner fold-in (#1496 follow-up): the evolution-ledger
  `accredited_firm_capacity_mw` call now passes `iso=iso` — it was the only
  call site still computing the ledger's `reserve_margin` on the legacy
  generic accreditation basis while both capacity-screen sites pass
  `iso=config.iso`.
- Tests: `tests/test_fleet_unification.py` (9 parity/no-op/threading pins);
  `test_biomass_mustrun_injection.py` repointed at the moved
  `fleet._drop_biomass_units`.

**Config-gated reachability changes, all DEAD at every keeper config and at
the forecast defaults** (verified against all six keepers' `meta.json`
before the change; the §7.3.5 "gate decides, not code presence" shape):

| Change | Fires only when | Keeper status |
|--------|-----------------|---------------|
| Backcast synth/legacy paths honor `coal_takeorpay_from_data` (+ sync-mode exclusion) | `coal_takeorpay_from_data=True` on a non-curated-bins backcast | absent (default False) in all six metas |
| Curated-bins takeorpay gains the sync-mode exclusion (runner semantics carried) | `coal_takeorpay_from_data ∧ coal_sync_srmc_tranche` on curated bins | ERCOT keeper: both False |
| Backcast synth-empty fallback honors `gas_offer_curve` | `gas_offer_curve=True` AND empty synthesis | `gas_offer_curve=False` all keepers; synthesis non-empty for all five artifact ISOs |
| Tiered PRB follower gate now applies on non-ERCOT campd paths | sigmoid+tiered set AND the ISO has a characterized `prb_follower` curve | only ERCOT has one (`COAL_SIGMOID_DEFAULTS`); for every other ISO the follower series falls back to the baseload prb curve — value-identical routing |
| Sigmoid-off non-default `coal_prb_passthrough` no longer discounts subbituminous on the runner path | forecast config with `coal_prb_passthrough ≠ 1.0` and sigmoids off | nothing in `src/` sets the field; keepers all run sigmoid-on |
| Coldsnap derate reachable from forecast | `neiso_gas_coldsnap_derate=True` in a forecast config | default off; no keeper sets it |

**Gate (builder-swap standard §7.2, `--mode builder`, atol=rtol=1e-9;
before = `stage6-before-e46ab11`, after = the Stage-7 branch tip `140c61f`
— see §7.3.9 for why the same capture closes both stages' gates at once).**

<!-- STAGE6_GATE_RESULT -->
**PARTIAL PASS — 3/5 ISOs byte-identical (ERCOT, CAISO, NEISO), 2
OOM-waived (PJM, MISO), NYISO status unconfirmed after this rebase.
Stage-6 completion is memory-host-blocked (G-40), NOT a code defect.**
Two independent sessions captured overlapping evidence against the same
`stage6-before-e46ab11` baseline; merged below rather than picking one:

| ISO | Builder-swap byte gate (§7.2, `--mode builder`, atol=rtol=1e-9, before=`stage6-before-e46ab11`) | Status |
|-----|--------|--------|
| ERCOT | **PASS** — captured independently by both sessions, zero-Δ both times; fidelity 140/140 recorded flags. This session's after-capture was at the Stage-7 branch tip (`140c61f`), so it also covers Stage 7 (§7.3.9) | ✅ |
| CAISO | **PASS** — captured independently by both sessions, zero-Δ both times; fidelity 122/122 (the 2 expected `scenario_config` drifts are the §7.3.7-documented `caiso_perhub_firm_base`/`offer_curve_by_group` base-config moves, not flag mismatches — plus a 3rd expected drift from this session's own `cc_outage_derate_from_top` meta-writer fix, §7.3.9) | ✅ |
| NEISO | **PASS** (sibling session only) — zero-Δ; fidelity 142/142 recorded flags vs the §7.3.7 `e46ab11` baseline (validated by the default-off gate, not by a keeper exercising the coldsnap path — see below) | ✅ |
| PJM | **OOM-WAIVED** — the after-side capture SIGKILLs (-9) on this 15 GB box, the same memory-ceiling failure class §7.3.1/§7.3.7 document (PJM's `e46ab11` baseline itself needed a solo re-run to capture). Blocked on the G-40 ≥24 GB host. | ⏸ |
| MISO | **OOM-WAIVED** — uncapturable on this box at every prior stage (§7.3.1 waiver stands); no `stage6-before` baseline exists for it either. Blocked on the same G-40 ≥24 GB host. | ⏸ |
| NYISO | **STATUS UNCONFIRMED** — the sibling session reported a recapture "in progress" (after a one-time `curate_capacity_deliverability.py` rebuild of the `data/clean/capacity-deliverability/` partition that `apply_nyiso_li_tsl_import_cap` reads); this session did not independently verify whether that recapture completed or its result. Baseline fidelity was 140/140. | 🔄 |

**Evidence:** §7.3.7 (`e46ab11`, commit `fd88916`/PR #1528) records the
5-ISO `stage6-before-e46ab11` baseline captures and their fidelity flags
(ERCOT 140/140, CAISO 122/122, PJM 130/130, NYISO 140/140, NEISO 142/142).
The Stage-6 code (#1516) merged at `186b6cd` before this gate finished, and
the Stage-7 code (§7.3.9) merged before ITS gate finished too — both are
POST-MERGE retroactive validations, not conditions of their merges. **Do
not re-mark this RESULT-PENDING or PASS-in-full until PJM+MISO are gated on
the G-40 host and NYISO's status is confirmed.**

### 7.3.9 Stage 7 — backcast-config fold, getattr→field, env-knob kill, meta-writer audit (2026-07-06)

Branch `claude/orchestrator-unification-6-7-jxycz5`, commit `140c61f` (on top
of the Stage-6 work, rebased repeatedly onto main as the fast-moving repo
advanced — final rebase onto `fe7774e`). Delivered per §6 row 7.

**What was built**

- `pipeline/backcast_config.py` — `_calibration_config` moved verbatim
  (renamed `backcast_config`, the public pipeline-package name) along with
  the private offer-curve machinery only it used: `_deep_merge_offer_curve`,
  `_apply_offer_curve_deltas`, `_neutralize_generic_gas_bands`,
  `_GENERIC_NEUTRAL_GAS_CLASSES`, the five per-ISO `_*_OFFER_CURVE` dicts,
  `_MISO_CC_COAL_REBALANCE`. Two of those (`_deep_merge_offer_curve`,
  `_MISO_CC_COAL_REBALANCE`) are ALSO called directly from `run_year`
  (outside the extracted function) and two more
  (`_GENERIC_NEUTRAL_GAS_CLASSES`, `_neutralize_generic_gas_bands`) are
  imported directly by `tests/test_offer_curve_deleakage.py` — both
  `run_calibration.py` and the test keep working via re-imports from the new
  module. `run_calibration.py` also keeps a `_calibration_config =
  backcast_config` alias (the Stage-4 `_commitment_pass` precedent) for the
  handful of probe scripts (`export_tranche_config.py`,
  `build_offer_curve_overrides.py`, `run_miso41_ablation_twin.py`, tests)
  that call `rc._calibration_config(...)` or import the old name directly.
  `run_calibration_full.py` now imports `backcast_config` from
  `market_sim.pipeline` (not from `scripts.run_calibration`) at every one of
  its four call sites. Pure code motion — byte-identical by construction
  (same statements, same order, relocated behind an import).
- getattr→field folds (rule 24; all four verified dead before folding — the
  same `cfg`/`config` object is read via plain, non-getattr attribute access
  elsewhere in the identical function, proving it is never anything but a
  full `ScenarioConfig`): `pipeline/commitment.py`'s
  `caiso_ra_min_load_frac` (:133), `renewable_keep_running_value` (:125),
  `ercot_as_adequacy_frac` (:265); `model/transmission.py`'s
  `renewable_keep_running_value` (:2084). No other `getattr(config, ...,
  <literal>)` site in the offer/solve path was found to reference these
  three specific fields.
- Killed `FORWARD_SKILL_ENV` (gap G-07): `neighbor_price.neighbor_heat_rate`
  now takes an explicit `forward_skill: str | None = None` parameter instead
  of reading `MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL` from the environment.
  Confirmed via repo-wide grep that no keeper, script, or test ever set the
  env var or called the removed `_forward_skill_mode()` helper — the
  parameter's default (`None`) reproduces every existing call site
  byte-identically; a future forward-skill validation experiment passes the
  mode explicitly instead of setting an env var.
- Meta-writer / `recorded_cfg` audit (the G-14 bug class): `meta.json` now
  persists `ercot_zonal_gas_basis` / `ercot_west_netload_gas_shape` /
  `ercot_west_gas_delivered_floor` — env-var-only fields with no
  `solve_and_persist` kwarg at all, read via the same inline
  `backcast_config(...)` pattern `coal_plant_monthly_pricing`/
  `td_loss_factor` already used (the two other named fields,
  `oil_primary_bin_fuel` and `ercot_reserve_supply_forward`, were already
  persisted — landed by another lane before this session reached them).
  Separately, systematically audited every `solve_and_persist` parameter
  that reaches a real `ScenarioConfig` field against `recorded_cfg`'s
  reconstruction chain (the ~380-line `.with_overrides(...)` sequence that
  rebuilds the config `run_config.json` records) and found — beyond the
  explicitly-scoped `caiso_perhub_firm_base` (G-14's own residual) — eight
  more fields the real solve applied via `run_year` but `recorded_cfg`
  silently dropped, so `run_config.json`'s `scenario_config` showed the
  field DEFAULT instead of what the LP solved with:
  `cc_derate_from_top` (missing the `or iso.upper() == "CAISO"` branch —
  verified against the frozen `caiso51_firm_base` keeper's own
  `run_config.json`, which shows `cc_outage_derate_from_top: false` even
  though CAISO always solves it `true` — a live, previously-unnoticed
  instance of exactly this bug), `cc_nameplate_summer_derate`,
  `coal_mustrun_online_pmin`, `coal_sync_srmc_tranche`,
  `gas_st_netload_drag` (+ its `gas_st_drag_overrides` coefficient
  companion), `ordc_lolp_params_path`, `ct_drag_overrides` (the
  `ct_netload_drag` companion), and `coal_lignite_mustrun`/
  `coal_prb_mustrun` (→ `coal_lignite_mustrun_override`/
  `coal_prb_mustrun_override`, passed positionally into `backcast_config`
  by `run_year` but never threaded into `recorded_cfg`'s own
  `backcast_config(...)` call). None of these fixes touch the real solve —
  `run_year`'s own `config.with_overrides(...)` calls already fed the
  correct values to the LP; the fix is scoped entirely to what gets
  WRITTEN to the two JSON audit-trail files.
  Four candidates from the audit were investigated and found to be false
  positives (correctly handled, just under field names the naive scan
  missed): `st_gas_intermediate` (→ `st_gas_intermediate_split` +
  `gas_st_startup_cost` + `gas_st_wefor_base_override`), `curve_smoothing`
  (dynamic `**{...}` unpack), `interchange_shaping_export_only` (present on
  the same source line as `interchange_shaping`, missed by a naive
  line-start regex). Five more are NOT `ScenarioConfig` fields at all
  (`btm_backfill_year`, `ercot_dam_as_overlay`,
  `ercot_dam_as_overlay_from_year`, `ercot_dam_as_scarcity_threshold`,
  `ercot_rtordpa_overlay`, `hydro_backfill_year`, `hydro_eia930_monthly`,
  `hydro_forecast_budget`, `hydro_year`, `priced_interchange`) — plain
  post-solve/builder-function parameters with no `recorded_cfg` home;
  `meta.json`'s existing kwarg echo is the correct and only record for
  them.
- `tests/test_recorded_cfg_fidelity.py` (new, 11 cases + 14 subtests): pins
  every fixed field via the reconstruction PATTERN directly
  (`backcast_config` + the same `with_overrides` calls both `run_year` and
  `recorded_cfg` apply), plus a static guard that each fixed field name is
  still textually present in `run_calibration_full.py`'s `recorded_cfg`/
  `meta` blocks (fails loudly if a future edit silently re-drops one).
  **Scope note (no silent cap):** a fully generic "every `TIER_TAGS` field
  round-trips" test would need `solve_and_persist`'s `recorded_cfg`
  reconstruction (currently inline in a 150+-parameter, real-LP-solve
  function) extracted into a standalone, solve-free callable — a
  substantial refactor judged out of this stage's scope. The audit above
  covered every parameter that reaches `meta`; a parameter never recorded
  in `meta` at all was outside the audit's reach by construction and is a
  residual, unaudited surface for a future session.

**Gate.** Pure-code-motion standard (§7.2: exact byte-identity) applies to
the extraction/getattr/env-knob items; the meta-writer/`recorded_cfg`
fixes change only JSON audit-trail content, never a solve input, so they
carry the same standard trivially. Verified with the SAME capture as
§7.3.8 (this branch's tip already contains Stage 6 + Stage 7 together, so
one gate run closes both):

<!-- STAGE7_GATE_RESULT -->
**PASS on ERCOT + CAISO** — see §7.3.8's gate entry for the full
`regression_gate.py` output (CAISO 43 / ERCOT 30 numeric columns within
`--mode builder` atol=rtol=1e-9, reshuffle 0.000% every ISO-year, smoke
24/24, `legitimacy_diagnostics`/`audit_keepers` both PASS). The same
"PJM/NYISO/NEISO/MISO not independently re-captured this pass" caveat
applies. `pytest tests/` full suite: **3054 passed, 15 skipped, 10
xfailed, 34 xpassed** (pre-rebase run; the rebase onto `fe7774e` introduced
zero conflicts, so the working tree is byte-identical to what that run
exercised — a second post-rebase run would be redundant and was not
re-executed to conserve the box's remaining budget).

**G-40 update (2026-07-06, branch `claude/reserve-coldbuild-memory-opt`) — the
PJM/MISO OOM is a *construction-peak in the builder*, not the solve, and is
partly recoverable without a ≥24 GB host.** Profiled with the new
`scripts/profile_lp_memory.py` (peak anon-RSS, construction-vs-solve split,
per-block nnz). Findings:
- The OOM-killer's "during reserve-column construction" is confirmed: the peak
  is sparse-matrix *assembly*, not HiGHS. Two drivers — (a) the reserve block's
  own `kron` + dense `(n_gen,T)` cap/availability intermediates (~3× the final
  block, the harder residual), and (b) `build_constraints`' **pairwise
  `A = sp.vstack([A, block])` chain**, which re-copies the whole accumulated
  matrix at every optional block, spiking to ~2× the final matrix at the last
  (reserve) stack.
- **The literal Step-2 tactic (rebuild the reserve block as COO int32 triplets)
  does NOT help — it is measurably *worse*:** scipy's `kron` already emits int32
  and is tighter than materializing triplets (benchmarked 2.14 → 2.40 GiB). That
  premise is dead; recorded so it is not re-tried.
- **What does help, byte-identically: a freeing single-pass concat**
  (`dispatch._vstack_csr_free`) replacing the pairwise chain in
  `build_constraints` and both reserve builders. Measured on a representative
  multi-block build (energy|SOC|reserve, 176 M nnz, ~2.1 GB final): peak
  **6.71 → 5.54 GiB (−1.17 GiB, ~17 %)**, full-matrix CSR hash **identical**
  (`9096a36a4f30eb93`). The saving scales with the accumulated-A size at the
  reserve stack, so the real MISO/PJM builds (which also carry hydro + zonal
  reserve-family blocks) should see ≥ that. `tests/test_dispatch_vstack_memory.py`
  pins the byte-identity (incl. the int64-column path); the full dispatch/reserve
  suite (457) stays green, so the Stage-6 builder-swap byte gate is untouched.
- **Not yet confirmed end-to-end:** this container has no `data/clean` MISO/PJM
  partitions and a 16 GB ceiling, so the *keeper* peak can't be measured here —
  run `MARKET_SIM_MEM_DEBUG=1 scripts/profile_lp_memory.py --keeper …` (or the
  real solve) on a data-provisioned box to confirm miso-41/pjm-77 now build+solve
  under 16 GB. If the free-concat alone clears it, **the G-40 ≥24 GB host is not
  required** and PJM/MISO can be gated on the standard box. If it does not, the
  fallback is Step 3 (decouple reserve granularity from fleet granularity — pool
  reserve per zone), which is a **miso-41 keeper modeling change** (re-solve +
  re-pin + rule-1 writeup) and must NOT be done without owner sign-off.

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

---

## 11. Stage 7 — `getattr`→field extraction + `backcast_config` move (DESIGN, not implemented)

**Status: design only. Does not start until Stage 6 completes — Stage 6 is
memory-host-blocked on G-40 (see the `STAGE6_GATE_RESULT` marker, §7.3.8).** No
solve is run to produce this design. Engineering companion with the full
72-row inventory and target module skeletons:
`src/market_sim/pipeline/stage7_getattr_extraction_design.md`.

**PARTIALLY IMPLEMENTED by a concurrent session — see §7.3.9, do not
redo.** A parallel lane on the same branch (`claude/orchestrator-
unification-6-7-jxycz5`) already delivered, tested, and gated (§7.3.9)
item 1 in full (`_calibration_config` → `pipeline/backcast_config.py::
backcast_config`, though `pipeline/overlays.py` for the measured overlays
was NOT split out — the overlays stayed inline in `backcast_config.py`,
an open item if this design's `overlays.py` split is still wanted) and
a **3-row slice** of item 2's Bucket B: `caiso_ra_min_load_frac` (§11.3's
own flagged deletion — done, the `0.40` fallback is gone from
`pipeline/commitment.py:133`), `ercot_as_adequacy_frac`, and
`renewable_keep_running_value` (both its `pipeline/commitment.py` and
`model/transmission.py` sites). **The remaining ~284 solve-path `getattr`
reads (all of Bucket A, the rest of Bucket B, all of Bucket C, and the
~216 boolean gates) are UNTOUCHED** — this design's implementation phase
should fold those and skip the 4 sites above (re-folding them is a no-op,
not a conflict, but redundant). §7.3.9 also independently killed
`FORWARD_SKILL_ENV` (gap G-07, not in this design's inventory — a
different mechanism, `neighbor_price.py`) and ran a `recorded_cfg`/
meta-writer audit (the G-14 bug class, orthogonal to this design's
`getattr` focus). §11.4's byte-identity gate standard (item 4, the static
zero-getattr-literal-fallback CI guard) is NOT yet built for the
remaining 284 reads — still open for this design's implementation phase.

### 11.1 What Stage 7 does

1. **Move `_calibration_config`** (`run_calibration.py:1021`) →
   `pipeline/backcast_config.py::backcast_config(iso, year, hours, flags, …)` and
   make it the **single typed construction site** for the backcast
   `ScenarioConfig`; `pipeline/overlays.py` holds the measured overlays as gates
   on explicit fields (rule 12). `run_calibration_full.py` imports the config
   seam from `pipeline`, not `run_calibration`.
2. **Fold every `getattr(config, …, <literal>)` on the solve path to a plain
   attribute read**, so the field declaration in `ScenarioConfig`/`constants.py`
   is the single source of every default and every tunable appears in
   `run_config.json` (rules 20/24).
3. **Delete the `caiso_ra_min_load_frac` `0.40` fallback** outright (rule 26).

### 11.2 Inventory of the `getattr` fallbacks (measured at this branch)

`grep -rE "getattr\((config|cfg)\s*," src/market_sim/` → **288** solve-path
reads. **Every field is already declared in `ScenarioConfig`** (verified
field-by-field), so §4's finding holds at scale: the pattern is defensive, the
literal is dead *today* — and a dead literal is a re-armable answer key (rule
26). Split:

- **~216 boolean gates** (`…, False/True/None`) — mechanical fold to
  `config.flag`; cannot move a number.
- **72 non-boolean literal fallbacks** — the answer-key risks, in three buckets:
  - **A — always-present context reads** (fold, low risk): `iso` "ERCOT" (×11),
    `mode` "forecast" (×16), `weather_year` `0` (×5), `outage_source`
    "statistical" (×3), `carbon_price` `0.0`, `carbon_price_path` "zero".
  - **B — real numeric/string tunables** (the rule-26 traps): incl.
    `caiso_ra_min_load_frac` `0.40`, `ercot_as_adequacy_frac` `1.0`,
    `ercot_as_critical_frac` `0.0`, `ercot_as_n_ramp` `12`, the ERCOT
    `*_from_year` gates (`2023`/`2025`), `ercot_market_design` "auto",
    `pjm_reserve_online_rho` `1.0`, `rtcb_reliability_deployment_mw` `0.0`,
    `battery_dispatch_adder` `0.0`, `caiso_solar_deliverability_k/_floor`
    `0.15`/`0.50`, `caiso_solar_shape_nl_hi/lo_pct` `30.0`/`10.0`,
    `renewable_keep_running_value` `20.0`, the three `*_intermediate_cf_threshold`
    `50.0`, `ct_mustrun/ct_deployment/reliability_deployment_floor_frac` `1.0`,
    `committed_ramp_spread` `0.0`, `offer_curve_smoothing_n/_exp` `0`/`1.0`,
    `nearby_fuel_price_min_state_plants` `2`. (Full table with sites in the
    companion note.)
  - **C — path/string literals** (fold): `campd_bins_path`
    `str(CAMPD_BINS_CSV)`, `control_retrofit_path` `""`,
    `cc_capacity_reconcile_path` `""`.
- **Already handled / out of scope:** the NEISO coldsnap coeffs (§4 item 2) are
  **already fields** as of Stage 6 (§7.3.8), no work; the env-var ERCOT gas knobs
  are a separate default-off-probe cleanup (§4); bare `getattr(config, k)` /
  `getattr(config, field)` dynamic-name indirection (scenarios.py:3904,
  capacity.py FOM fields, eac.py:158) is not a shadow default and stays.

### 11.3 `caiso_ra_min_load_frac` — the flagged deletion (rule 26)

- Field default `scenarios.py:896` (`= 0.40`); backcast override
  `run_calibration.py:1314` (`= 0.26`, the CAISO keeper's live value); solve-path
  read `pipeline/commitment.py:133` (`getattr(cfg, "caiso_ra_min_load_frac",
  0.40)`). Today `0.26` always wins and the `0.40` is dead — but a core built off
  the `_calibration_config` path (what this migration constructs) would silently
  run `0.40`. **Stage 7 reads `float(cfg.caiso_ra_min_load_frac)` and deletes the
  `0.40` fallback.** The field's `scenarios.py` default stays (the legitimate,
  run-config-surfaced registry default); the *duplicate* solve-path literal dies.
  Deleted, not zeroed.

### 11.4 The byte-identity gate Stage 7 must pass

Stage 7 is **pure code motion** ⇒ the §7.2 **exact** standard, not the
builder-swap 1e-9 tolerance:

1. **Solve byte-identity, all gate-able keepers.** `regression_gate.py --mode
   byte`, before = a fresh pre-Stage-7 golden of the current keepers, after = the
   Stage-7 branch. Acceptance: objective relΔ = 0, **every price Δ = 0, every
   dispatch Δ = 0** — ERCOT/CAISO/NEISO on the 15 GB box; PJM/MISO on the G-40
   ≥24 GB host; NYISO after its deliverability-partition recapture. Because every
   folded field's default equals the deleted literal for a real config, and
   `backcast_config` sets each override explicitly, the fold cannot move a number.
2. **CAISO keeper is the load-bearing leg.** caiso-51 sets
   `caiso_ra_mustoffer=True`, exercising `commitment.py:133`; its zero-Δ gate is
   the specific proof that deleting the `0.40` fallback moved nothing. A gate that
   skipped a `caiso_ra_mustoffer` keeper would not test the deletion.
3. **Config-construction parity (pre-solve).** For each keeper `meta.json`,
   `backcast_config(...)` returns a `ScenarioConfig` equal **field-for-field** to
   the pre-Stage-7 `_calibration_config` output — proves the move dropped/altered
   no field before any solve runs.
4. **Static anti-regression guard (CI).** A test asserting **zero** literal-fallback
   `getattr((config|cfg), "…", <non-dynamic>)` remain on the solve path, so the
   answer keys cannot creep back (rules 24/26, mirroring §7.2's D-9 quarantine
   gate). The boolean gates fold in the same sweep and are covered by the same
   guard.
