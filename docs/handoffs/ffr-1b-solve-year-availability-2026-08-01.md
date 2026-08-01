# FFR-1B — Solve-year availability: the fleet ages, measured events stay in backcast

**Session:** FFR-1B `[FABLE]` (forecast-readiness remediation Wave 1, lane L-SCAR;
`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-1B; audit rows FR-7 / FR-8 / FR-12 +
§4 P1-b in `docs/forecast-readiness-audit-2026-07.md`). Branch
`claude/ffr-1b-thermal-forecast-qxdv4y` off `origin/main` @ `40ecb0a`, 2026-07-31→08-01.

**Result.** All three findings closed at every read site; **backcast byte-identity proven on
all six keeper configs (102/102 input-surface hash comparisons identical, §3)**; entrant
age ≥ 0 asserted in a unit test; the T0 forecast probe shows monotone availability aging
(§4). No tuning anywhere: every change is a year-semantics or mode-gate fix; no default
moves, no band widens, no `ScenarioConfig` field is added, no cache key changes. The
cache-epoch bump is deliberately NOT taken here — §W1-X owns the single Wave-1 bump.

Commits: `4886505` (FR-7 + FR-8, `data/fleet/*`), `b86f641` (FR-12, `model/reserves/spec.py`
+ `results/scarcity.py`), `ba49be2` (the single `scenarios.py` `__post_init__` hunk —
**flagged for FFR-1D**, which owns `scenarios.py` this wave; isolated in its own commit to
rebase around or absorb).

---

## 1. What was wrong (one paragraph each)

* **FR-7 (BLOCKER).** `_availability_matrix` keyed the age-based WEFOR/derate escalation on
  `run_year = config.weather_year`. A 2050 solve with the default `weather_year=2024` held
  every unit at its 2024 age for 25 years (systematic availability overstatement), and a
  model-built entrant (`online_year=2035`) got a **negative** age. The solve year was
  already threaded into the function (`year`) but used only for the temperature derate.
* **FR-8 (BLOCKER).** `BIN_FORCED_DERATE_BY_YEAR["N_COAL4"]={2025: 0.67}` (the Martin Lake
  unit-1 turbine fire — a measured single event) was looked up by `weather_year` with no
  mode gate. Backcast was correct (`weather_year == solve year`); the T1-X crossover
  harness pins `weather_year=2025`, so every crossover solve year — realized 2023–2025 and
  forward 2026–2027 — applied a 2025 plant fire it should not. Direct rule 13
  `[R-MEASURED]` violation reachable with zero flags.
* **FR-12 (MED).** A bare `ercot_multiproduct_as_coopt` in forecast fell through to the
  measured AS plan (all-zero for forecast years — zero AS demanded, nothing withheld),
  because the two existing `__post_init__` guards fire only when endogenous storage/thermal
  AS is *also* armed. Adjacent: the reserve/AS layer keyed measured artifacts and
  market-design date gates on `int(config.weather_year)` (frozen 2024/2025 records if armed
  in forecast), and the ERCOT non-releasable-withholding regime test used numeric
  weather-year gates instead of the existing `ercot_market_regime(year, config)` seam
  (RTC+B-obsolete behavior for 2026–2050 if armed).

## 2. Site-by-site disposition table

Legend: **SOLVE** = re-keyed to the solve year (`year` / `sim_year`, weather_year fallback
for legacy callers — value-identical in backcast where the harness pins them equal);
**GATE** = hard-gated backcast-only at the read site (measured record, no forward analogue);
**KEEP** = weather_year retained deliberately (weather/calendar-shape meaning); **ALREADY**
= found correctly gated/mode-aware, no change.

### `src/market_sim/data/fleet/arrays.py`

| Site (symbol) | Meaning | Disposition — why |
|---|---|---|
| `_availability_matrix` age term (`_thermal_outage(gen.plant_group, · − online_year)`) | fleet clock | **SOLVE** (`fleet_year`): the fleet must age through the horizon; entrants get non-negative ages. |
| `_availability_matrix` ST-override age (`gas_st_wefor_base_override` leg) | fleet clock | **SOLVE**: same age semantics, same variable. |
| `_availability_matrix` `BIN_FORCED_DERATE_BY_YEAR` read | measured single-event derate | **GATE + SOLVE key**: `mode=="backcast"` (the dormant-nuclear sibling's exact pattern), keyed by `fleet_year` (== weather_year in backcast). |
| `_td_year` (temp-dependent derate: measured zone dry-bulb/TMAX) | weather shape | **KEEP semantics, comment added** — "the weather 8760 this solve rides": the solve year while on realized/bridged weather (backcast + hindcast realized years, where it must stay aligned with the same year's realized demand), weather_year fallback. A pure-forward year has no measured file and degrades gracefully to the flat class derate; the single-pinned-weather limitation is FR-17's workstream, not this seam. |
| `_amb_year` (`gt_ambient_derate` zone TMAX) | weather shape | **KEEP, comment added** — same keying as `_td_year`. |
| `_apply_outage_overlays` `config.weather_year` reads (CAMPD unit derate, CAISO/MISO DAM precedence, noncampd caps, partial outages, NYSDEC windows, …) | measured backcast overlays | **ALREADY**: all inside `outage_source=="historic"` and/or explicit `mode=="backcast"` gates; in backcast weather_year *is* the calendar year. |
| DAM-availability `_dam_ceil` build + its two water-fill uses (the audit's "3 sibling reads") | measured event ceiling | **ALREADY**: the enclosing `ercot_thermal_dam_availability` block gates on `mode=="backcast"` (+ ERCOT + flag); unreachable in forecast. Documented in the table header (below). |
| `bins_to_fleet` internal `generators_to_fleet_arrays(year=config.weather_year)` | fleet clock | **ALREADY-inert**: its only caller (`build_base_fleet`) discards the returned arrays (`campd_fleet, _ =`); the dispatch arrays are built by the orchestrators with `year=year`. Noted, not touched. |
| `runner.py:1125` / `run_calibration.py:2710` call sites | fleet clock threading | **ALREADY**: runner threads the evolving solve year; the backcast harness passes `config.weather_year`, which it pins to the solve year. Untouched (runner.py is out of this session's scope). |

### `src/market_sim/data/fleet/eia860.py`

`BIN_FORCED_DERATE_BY_YEAR` header now declares BACKCAST-ONLY + solve-year keying and
points at the mode gates. The `N_COAL4` entry is **retained** per its own retirement path
(rule 14: the measured overlay cannot see a unit destroyed before the vintage; the entry
dies only when the outage derive can represent whole-vintage absence or the event moves to
a registry).

### `src/market_sim/model/reserves/spec.py` (+ `results/scarcity.py`)

Two shared helpers carry the whole sweep: `_reserve_solve_year(config, sim_year)` (the
fleet clock; `sim_year` is threaded by both orchestrators, weather_year fallback) and
`_require_backcast_measured(config, flag, what)` (the `gas_price_factor`-style hard error
at the consuming read site). `sim_year` is now threaded into the PJM/MISO/NYISO/NEISO
designs (ERCOT/CAISO already took it).

| Site | Meaning | Disposition — why |
|---|---|---|
| `_ercot_design` ECRS add-on (`ercot_ecrs_requirement_mw`, ASPLANNP433) | measured procurement plan | **GATE + SOLVE key**: all-zero for missing years, so a forecast arming would silently add nothing; no forward formula exists on this (single-product) path. |
| `_ercot_design` ECRS / LR / storage-AS from-year onset gates | calendar onsets | **SOLVE**: published product-launch dates track the horizon, not the weather pin. |
| `_ercot_design` + multiproduct LR credit (`ercot_load_resource_reserve_credit_mw`) | mode-aware credit | **ALREADY** (G4 pattern): measured NP3-911 enrollment in backcast, forward enrollment formula in forecast, `year=sim_year` already threaded. Only its onset gate re-keyed. |
| `_ercot_design` + multiproduct measured storage-AS netting (`ercot_storage_as_reserve_mw`, both design variants) | measured 60-Day-DAM awards | **GATE + SOLVE key**: the forward story is `ercot_storage_as_endogenous` (its own mechanism, excluded at these sites by construction). |
| `_ercot_multiproduct_design` `year` (line ~1220) | fleet clock | **SOLVE** (`_reserve_solve_year`): feeds every date gate + artifact key below. |
| Multiproduct measured AS-plan fallback (`ercot_as_plan_requirement_mw`) | measured plan | **GATE**: a forecast reaching it (forward requirement armed but drivers unthreaded — the case the config-level guards cannot see) now fails loud instead of pricing zero AS. |
| ECRS release-reform window (`ercot_ecrs_conservative_deployment`) | published dated reform (2024-08-01) | **SOLVE**: forward years are post-reform by date; not an RTC+B regime question, so no seam needed. |
| Non-releasable RRS/Reg-Up withholding window (`ercot_nonreleasable_as_withholding`) | market-design regime | **SOLVE + regime seam**: routed through `ercot_market_regime(year, config)` with the new public `RTCB_GOLIVE_YEAR` alias (scarcity.py; = `_RTCB_FIRST_FULL_YEAR − 1`). Auto is value-identical to the old numeric gates for every backcast year; an explicit `ercot_market_design` pin is now honored in both directions (an "ordc"-pinned forward scenario keeps the carve-out; "rtcb" retires it). |
| `ercot_rtolcap_supply_cap_mw` | mode-aware supply cap | **ALREADY** (G4): measured RTOLCAP parquet in backcast, WS-A forward formula in forecast. |
| `_pjm_design` measured requirement family (RTO + MAD + sync, `load_pjm_measured_*`) | measured with designed fallback | **SOLVE**: the loaders return `None` for uncovered years and the design falls back to the fleet-responsive 1.5×MSSC formula — the *documented* forecast path. Solve-year keying makes a forecast year take the formula instead of freezing the pinned weather-year record. |
| `_miso_design` `miso_measured_reserve_requirements` | measured cleared-reservation series | **GATE + SOLVE key**: the loader hard-errors on a missing year by contract (rule-14 mandatory swap — no static fallback), so there is no forward key to give it. |
| `_nyiso_design` `nyiso_dynamic_reserve_requirements` | measured as-enforced series (#1344 intake) | **GATE + SOLVE key**: same loader contract (hard-error, no silent static reversion). |
| `_nyiso_design` LI 30-minute published diurnal (`nyiso_li_30min_requirement_mw`) | published constants on the On-Peak calendar | **KEEP weather_year**: both levels are printed LRR cells, not a record; the year only lays out the weekday/holiday On-Peak mask, and the solve's 8760 hour grid IS the pinned weather-year calendar (demand/weather shapes ride it) — a solve-year mask would misalign with the grid. |
| `_neiso_design` `neiso_dynamic_reserve_requirements` | measured as-enforced series (Limb A) | **GATE + SOLVE key**: same contract as NYISO. |
| `scarcity.py:1258` (`ercot_online_storage_reserve_mw`) and `:1618` (measured RTOLCAP branch) | mode-split measured branches | **ALREADY**: both sit inside explicit `mode=="backcast"`/forward splits (G4). |

### `src/market_sim/config/scenarios.py` (the one permitted hunk — **coordinate with FFR-1D**)

New guard after the two endogenous siblings (so their more-specific messages keep firing):
forecast + `ercot_multiproduct_as_coopt` without `ercot_as_forward_requirement` is a hard
error. No field added, no default moved ⇒ no cache-key movement (verified §3).

## 3. Byte-identity attestation (all six keepers — the acceptance bar)

**Claim.** In backcast the harness pins `weather_year == solve year` and both orchestrators
thread `sim_year=year` / `year=year`, so every SOLVE re-key is value-identical there and
every GATE passes; the diff is a no-op on all keeper-visible inputs.

**Structural half.** Every changed line is (a) a `weather_year → solve_year` substitution
whose two operands are pinned equal in backcast (`run_calibration.py:4471-4473` passes
`sim_year=year`; its fleet build passes `year=config.weather_year`; `pipeline/year.py`
same), or (b) a `mode=="backcast"` gate that keepers satisfy, or (c) a comment/new-error
path unreachable in backcast. The regime seam under `ercot_market_design="auto"` (all
keepers; none pins a design) reproduces the former numeric gates exactly: ordc ⇔ year <
2026, with the 2025 split at `RTCB_GOLIVE_HOUR` unchanged.

**Empirical half** (the FF-1F pattern — no keeper re-solve; scratch probe
`ffr1b_byte_identity.py`, run at `origin/main` @ `40ecb0a` and at the FFR-1B HEAD).
For each of the six keeper bundles' committed `run_config.json` `scenario_config`, for each
keeper year 2023/2024/2025, with the REAL on-disk loaders (CAMPD overlays, DAM
availability, measured reserve series, AS plan, weather files) over a fixed
branch-covering thermal fleet on real zone names:

* `ScenarioConfig.cache_key()`;
* sha256 of `availability` + `min_gen` from `generators_to_fleet_arrays`, threaded
  `year=Y` **and** the `year=None` legacy fallback;
* sha256 of the full `ReserveDesign` surface (every family's requirement / zone_mask /
  penalties / step widths / class, `eligible`, `supply_cap`, per-gen extras) with
  `sim_year=Y` **and** the `sim_year=None` fallback (armed in 5 keepers; the CAISO keeper
  runs no reserve co-opt).

**Result: 102/102 hash/key comparisons identical.** Non-vacuity spot checks at HEAD: the
ERCOT-2025 design contains both `*_withheld` and `*_released` families (the go-live split
executed through the new seam); the synthetic `N_COAL4` coal unit carries the 0.67 Martin
Lake derate in backcast 2025 (mean-availability ratio 0.659 vs an unbinned twin); the MISO
measured requirement is the non-flat series (2,300–3,124 MW); NYISO's measured dynamic
families are non-flat; PJM's per-gen design loaded the measured RTO+MAD requirements.
The keepers do not move. *(Rule 11 contingency — "if any keeper moves, STOP" — not
triggered.)*

## 4. FR-7 evidence — the fleet now ages

**Unit tests** (`tests/unit/data/test_solve_year_availability.py`, 8 tests): entrant age
≥ 0 asserted against the recorded arguments of the outage model (a 2035 entrant in a 2040
solve is aged 5, never −11); monotone availability aging 2026→2050; solve-year-only
dependence (same age ⇒ identical availability at different solve years); `year=None`
fallback bit-identity; and the FR-8 gate in all three postures (backcast applies, forecast
same-calendar-year does not, crossover weather-pin cannot leak) plus the retained
backcast-2025 Martin Lake derate (ratio 0.67 exactly).

**No-LP aging curve** (forecast config, weather pinned 2024; mean availability by solve
year; "legacy" = the frozen weather-year age the old code used for every year):

| unit (online) | 2026 | 2030 | 2035 | 2040 | 2045 | 2050 | legacy (flat, all 25 yr) |
|---|---|---|---|---|---|---|---|
| CC 1998 | 0.858 | 0.846 | 0.832 | 0.817 | 0.802 | 0.787 | 0.864 |
| CT 1995 | 0.775 | 0.756 | 0.731 | 0.707 | 0.682 | 0.658 | 0.785 |
| COAL 1980 | 0.769 | 0.741 | 0.706 | 0.671 | 0.636 | 0.601 | 0.783 |
| ST_GAS 1975 | 0.620 | 0.600 | 0.575 | 0.550 | 0.525 | 0.500 | 0.630 |
| CC entrant 2035 | 0.877 | 0.877 | 0.877 | 0.877 | 0.877 | 0.877 | 0.877 |

The entrant holds its young-age base through 2050 (ages 0–15, below the CC escalation
onset of 20) — flat is *correct* for it; the defect it carried was the negative age, which
the recorded-ages test now excludes. The T0 solve evidence is §5.

## 5. T0 forecast probe (NEISO 2026–2028, 3 solve-years ≤ 5-year cap)

`scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2028` at the FFR-1B
HEAD (defaults; the P-3A probe posture). Registered on the forecast-validation namespace
in this session via `scripts/register_forecast_run.py` (never the backcast registry) —
run id and invariants summary below.

<!-- T0-RESULTS -->

## 6. Pre-existing red / environment notes (rule 11 findings, none caused here)

* **The pinned default cache key has moved on main** (again): `ScenarioConfig().cache_key()`
  = `0e9fce2fb55b889f` at `40ecb0a` vs the `603c2498bf71d21d` pin in
  `tests/regression/test_persisted_identity.py` / `test_forecast_xyear_warmstart_flag.py` /
  two data-lane byte-stability tests. Fails on a CLEAN checkout of main — the audit FR-21
  drift family, for FFR-1D/W1-X, not this diff (my three commits leave the key at
  `0e9fce2fb55b889f`; verified in §3's cache_key hashes).
* 20 test failures pre-exist on clean `40ecb0a` (verified by stash-and-rerun): the 5
  cache-key pins above, `test_fleet_arrays_golden` (stale golden — audit FR-26's family),
  7 × `test_measured_chp_heat_rates`, `test_outages` unknown-ISO case, and 6 ×
  `test_soundness` E2E. This diff adds **zero** new failures; the previously-failing
  suites it touches now pass (`tests/unit/config/test_reserve_config.py` 107 passed,
  `tests/iso` 862 passed, `tests/unit` minus pre-existing red green).
* This container's `data/clean` was empty (derived, gitignored): regenerated
  `ramp-capability` (PJM keeper's `measured_ramp_capability`) and
  `confirmed-retirements` (forecast step-0 loader) via `scripts/regenerate_clean.py` for
  the attestation and the T0. `data/raw/zone-specific-demand/` has no NEISO directory in
  this checkout — the NEISO loader logs "zonal load file not found … skipping" and falls
  back to load-share split; noted for data-presence audits (the T0 is a probe, not a
  scored run).

## 7. Standing-duties ledger

* **Mechanism matrix (rule 28):** no cell verdict changes — no mechanism was probed for
  calibration effect; this session changes *forecast-lane semantics* (measured reserve
  artifacts now hard-gate backcast-only; the withholding window now regime-keyed). No new
  `ScenarioConfig` field ⇒ no new matrix row required (CI duty c). The
  `miso_measured_reserve_requirements` row's note that `_pjm_design` "reads … measured …
  unconditionally" remains true as to *flag*-gating; the PJM loaders are now solve-year-
  keyed with the formula fallback in forecast (this doc is the citation).
* **Cache-epoch:** NOT bumped here (§W1-X owns the single Wave-1 bump; FR-7/FR-8 change
  forecast output under unchanged keys, so stale 2026+ cached bundles must not be reused
  after Wave-1 merges).
* **scenarios.py coordination:** commit `ba49be2` is the single permitted hunk, isolated
  for FFR-1D (file owner this wave) — flagged in the PR body.
* **Holdout (rule 22):** no out-of-training year touched anywhere (probe years 2023–2025
  backcast configs + 2026–2028 forecast T0; forecast mode uses no measured H1-2026
  actuals by construction).
