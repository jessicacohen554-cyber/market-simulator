# Forward-mode hindcast program (T1-FF) — plan + prompt pack, 2026-07-31

**Owner ask:** "prepare a plan for hindcast including selection of a base year from which to run
the forecast model on historic years, including across the backcast calibration training years
but without the measured data available to the backcast — only the derived parameters or
measurements that will feed the forecast configuration for that ISO."

**Status:** planning doc only. **No LP solved, no parameter or default changed, nothing
registered.** Written against `origin/main` HEAD `7b8c36a` (2026-07-31). Companion to
`docs/forecast-readiness-audit-2026-07.md` (FR-1..FR-27),
`docs/forecast-readiness-prompt-pack-2026-07.md` (the FFR remediation waves), and
`docs/forecast-readiness-peer-review-2026-07.md` (commercial-practice grading). The tier
vocabulary and the §2.1b window cap come from `docs/forecast-development-plan-2026-07.md`.

---

## 1. The question this program answers

The backcast proves the model reproduces a known year **when it is fed that year's measured
overlays** — CAMPD outage windows, F923 delivered fuel, same-year CEMS emission rates, measured
reserve plans, measured demand. The forecast has none of those by construction. So the backcast's
excellent fit does not, by itself, tell us how the model behaves in the configuration we will
actually forecast with.

**T1-FF ("full-forward hindcast") answers exactly that:** run the model in its *forecast*
configuration from a historic base year, evolve and dispatch forward across years whose actuals
we hold (including the 2023–2025 calibration years), and score against those actuals. The gap
between a T1-FF score and the same ISO's keeper backcast score **is the value the measured
overlays carry** — the honest price of forecasting.

This is the in-house analogue of the one institutional capacity-expansion hindcast in the
literature (ReEDS / Cole & Vincent 2019); commercial vendors publish no equivalent
(`docs/rubric-v2-benchmark-memo-2026-07.md`). The peer review's bucket-C item 7 names its absence
as a disclosed limitation — this program is how that limitation closes.

### 1.1 What already exists, and why it is not enough

| Instrument | Window | Inputs on the SCORED years | Gap |
|---|---|---|---|
| **T1-H** capacity hindcast | 2021–2025, vintage 2020, 2022 bridged | **measured**: per-year measured demand loader (`runner.py:1076`), F923 delivered-fuel overlay (`data/fuel/plant_prices.py:361` — the skip is gated `mode != "backcast" and not hindcast`, so `hindcast=True` **keeps** it), realized gas | Validates the *capacity screens*, not the forecast input stack. Answers "can the screens reproduce builds/retirements", not "can the forecast configuration reproduce reality". |
| **T1-X** crossover | 2023–2027, vintage 2023 | 2023–2025 realized; **2026–2027 pure forward drivers** | The input-clean years (2026–27) are precisely the years that are **never scored** (`score_crossover.py`: `SCORED_YEARS = (2023,2024,2025)`, `QUARANTINE_FROM = 2026`). |

**The instrument the owner asked for is the intersection neither covers: pure forward drivers on
years we can score.**

### 1.2 The seam that makes it cheap

One boolean already flips a year between the two input stacks —
`ScenarioConfig.is_crossover_forward_year(year)` (`config/scenarios.py:9389`), defined as
`crossover_forward_year is not None and year >= crossover_forward_year`. **It has no lower
bound**, and its own docstring already specifies the exact semantics this program needs:

> "the years at/after the boundary drop every realized/measured hindcast input and run on forward
> drivers only (growth-scaled demand, AEO fuel, statistical outages, no measured overlays), and
> the boundary year is solved rather than bridged. Returns `False` for a plain hindcast (boundary
> `None`) or an in-sample year, so those paths stay byte-identical."

Its consumers are a closed, grep-verified set of three: measured-demand skip
(`runner.py:1076,1136`), F923 overlay skip (`plant_prices.py:369-370`), gas re-path to AEO
(`data/fuel/trajectories.py:107-110`).

**T1-FF = point that boundary at the base year itself.** No new mechanism, no second input stack,
no parallel code path (rule 19 — one mechanism per phenomenon). The work is in (a) letting the
harness express it, (b) closing the information leaks that only matter once the boundary moves
below 2026, and (c) sourcing as-of-vintage drivers.

---

## 2. The instrument

**Definition.** A T1-FF run is a `mode="forecast"`, `hindcast=True` run with
`crossover_forward_year == start_year`, seeded from an EIA-860 vintage at or before the base
year, with the confirmed-exit information gate cut at `date(vintage, 12, 31)`, dispatching every
year in the window on the forecast input stack, scored **only** on 2023–2025.

**Registration:** `frontend/data/hindcast/` with `meta.kind = "full_forward"` (never the backcast
registry — rule 15; never `frontend/data/forecast/`, which holds T1-F/program artifacts).

### 2.1 Two pre-registered arms

Both arms run per ISO; the pre-registration is written **before** any solve (rule: no post-hoc
arm selection).

| | **Arm R — realized drivers** | **Arm K — as-known drivers** |
|---|---|---|
| Question | *Is the forecast configuration structurally right?* | *What is true ex-ante forecast skill?* |
| Gas | `hindcast_realized` (annual realized Henry Hub) | AEO vintage as-of the base year (`hindcast_asknown_aeo2021` / `…aeo2023`) |
| Demand growth | as-of-vintage rate table | as-of-vintage rate table |
| Weather year | **solve year** (given-weather) | **base year** (pure ex-ante) |
| Everything else | forecast stack | forecast stack |
| New data needed | none | AEO2023 gas + as-of LTLF growth rates (FH-3) |

**Why both.** Arm R isolates structure from driver-forecast error: a model that dispatches well
given the right gas price but badly given a forecast gas price has a *driver* problem, not a
*structure* problem, and the two need different fixes. This is standard weather-normalized /
perfect-foresight-driver validation practice in commercial PCM work. Arm R is rule-13 admissible
— realized annual fuel prices and weather are physical/market inputs with genuine forward
analogues, entering formulaically; they are **not** measured *outcomes* fed back to force a match.

**The three-way read** (per metric, per ISO, per year):

```
keeper backcast err  ──►  Arm R err  ──►  Arm K err
        └── overlay value ──┘   └── driver-forecast error ──┘
                    └──────── total forecast gap ────────┘
```

`score_crossover.py` already computes `input_gap = |forecast_err| / |keeper_backcast_err|`
(`:11-13`); T1-FF reuses it verbatim for both arms.

### 2.2 Weather posture — stated, not assumed

Arm R pins `weather_year = solve year`; Arm K pins `weather_year = base year`. Both are
pre-registered per the peer review's bucket-C item 3 (single-pinned-weather is a disclosed
limitation of any single run). **Hard dependency:** FFR **FR-7** (fleet age keyed to
`weather_year` rather than the solve year) and **FR-8** (a measured 2025 Martin Lake derate
reachable in any run pinned to `weather_year=2025`) both corrupt a weather-pinned historic run.
**No T1-FF solve runs before FFR Wave 1 merges** — same efficiency logic as the FFR pack's rule 1
(running first would burn every comparator twice).

---

## 3. Base-year selection

### 3.1 Recommendation

| Phase | Base | Vintage | Window | Solve-years | Scored | Why |
|---|---|---|---|---|---|---|
| **A** *(first)* | **2023** | 2023 | 2023–2025 | **3** | 2023–2025 | Zero new quarantine surface — every solve year is a training year. All six ISOs have full benches. Proves the machinery end-to-end. Measures 1–3-year-ahead skill. |
| **B** *(after A is clean)* | **2021** | 2020 | 2021–2025 | **4** (2022 bridged) | 2023–2025 | Extends to 3–5 evolution steps using the *existing* T1-H allowances — 2021 solves as a seed and is never scored, 2022 stays evolved-never-solved. Vintage 2020 is the fullest on-disk EIA-860 vintage (30 files vs 10 for 2023). Exercises the post-Uri / fuel-shock regime. |

Both phases comply with the §2.1b ≤5-solve-year cap **by construction**, and with the owner's
standing 3–5-solve-year test instruction.

### 3.2 Refusal record — base year ≤ 2019

Recorded as **refused with reasons**, not deferred, so a later session does not re-litigate it:

- **2019 is locked-test tier** (`scripts/lib/holdout_policy.py:67`, `LOCKED_TEST_YEARS = {2019, 2026}`).
  Solving it spends the single most irreversible resource in the holdout policy — touch-once,
  ever — on a diagnostic. Refused on governance, not feasibility.
- **2018 has no weather year anywhere.** It appears in no ISO's `WEATHER_YEAR_POOL_BY_ISO`
  (`config/constants.py:2989`), and the curated demand-profile artifact starts 2021 (the harness's
  own floor: `run_capacity_hindcast.py:110-113`, *"demand profiles start 2021"*). Raw EIA-930
  goes back to 2018, so this is a data-curation project before it is a harness change.
- **NYISO/PJM 2019–2020 fail end-to-end** — both are outside those ISOs' verified pools (NYIS
  never reports `NG: SUN`; the generation-distribution parquet floors at 2021).

A pre-2021 base would therefore need, in order: EIA-930 demand curation 2018–2020, weather-pool
verification per ISO, `ALLOWED_VINTAGES` extension (data for vintages 2018–2024 is already on
disk), **and** a rule-22 tier decision. That is a separate chartered program, not this one.

### 3.3 Why not simply extend T1-X backward

T1-X's vintage-2023 crossover carries a known harness defect — its own forward-year
over-retirement (FC-1 I6: 25.6 % thermal retired by 2025), described in
`docs/handoffs/ff-t1-gate-2026-07.md` as *"a legacy-bin crossover-harness property, not the T1-F
config."* That defect would follow T1-FF to any base year. **FH-1 must reproduce or refute it at
the T1-FF posture before Phase A results are read as skill** — an over-retiring harness would
make every downstream metric uninterpretable. This is an explicit acceptance gate, not a footnote.

> **GATE RESULT 2026-08-02 — REPRODUCED. FH-4 / Phase A is BLOCKED.** FH-1's probe (ERCOT, base
> 2023, vintage 2023, 2023–2025, Arm R, registered `ercot-2023-2025-t1ff-armr-fh1gate`) retires
> **21.05 GW = 26.8 %** of prior thermal in 2025 — the T1-X 25.6 % property carried over, with
> the full **I6 FAIL / I7 FAIL / I12 WARN** signature. The run is otherwise mechanically clean,
> so the defect sits in the retirement layer upstream of T1-FF and follows the harness posture,
> not the input stack. The probe's dispatch-skill numbers are **gate context only** and must
> never be quoted as T1-FF skill. The block lifts only when a retirement-lane fix (FF-1A R-NEW /
> G-31 grain / the FFR retirement-calibration lane) lands **and** a re-probe passes. Evidence:
> `docs/handoffs/fh-1-full-forward-harness-2026-08.md` §7.

---

## 4. Input disposition — what the forecast stack can actually resolve for historic years

Audited family by family at HEAD. **BLOCKER** = must be fixed before a T1-FF run means anything;
**LEAK** = resolves but imports information from after the base year (an as-of violation);
**DISCLOSE** = resolves degenerately, honestly stated rather than fixed here.

| # | Family | Verdict | Detail | Owner |
|---|---|---|---|---|
| 1 | **Fleet init / EIA-860 vintage** | RESOLVES | `eia860_vintage_year` → `paths.set_eia860_vintage()` (`runner.py:518-522`); vintages 2018–2024 on disk (2018–2022 are the full 30-file sets). Entry growth ladder reads the active vintage (`runner.py:726-733`). Leakage guard `assert_pipeline_from_vintage` already generalizes over vintage. | — |
| 2 | **Planned additions** | **BLOCKER** | `EIA860_OPERABLE_VINTAGE` is a hardcoded `2025` (`data/fleet/models.py:97`) and the additions filter is `df[eff_year > EIA860_OPERABLE_VINTAGE]` (`data/fleet/eia860.py:1809`). A 2021-vintage run reads the 2021 proposed sheet and then **discards essentially every unit in it** — the planned-additions channel silently zeroes. Other consumers to audit in the same fix: `retirements.py:465` (default `vintage` param), `capacity_market.py:1588` (announced horizon). The correct pattern already exists: `_clean_fleet_year` (`models.py:67-85`) derives the year from the active vintage dir. | **FH-1** |
| 3 | **Confirmed exits / announced reversals** | RESOLVES | The one true information gate in the codebase: `confirmed_registry_as_of = date(eia860_vintage_year, 12, 31)` → `load_confirmed_exits(as_of=...)` (`runner.py:667-676`), which drops later-dated **and null-dated** rows. Fires only when `config.hindcast` — fine for T1-FF, flagged for the plain-forecast case. | — |
| 4 | **Outages / availability** | RESOLVES | Forecast default `outage_source="statistical"`: `_thermal_outage(category, age)` is purely age-parameterized, **no calendar-year dependency**, resolves for any year. `correlated_forced_outage` adds weather-driven correlation but `CORRELATED_OUTAGE_CURVE` is **ERCOT-only** (no generic fallback, rule 25). Fidelity note: statistical outages will not reproduce Uri — a Phase-B 2021 ERCOT caveat, stated up front. | — (arm posture) |
| 5 | **Demand — base profile** | PARTIAL | Pool-bounded (`WEATHER_YEAR_POOL_BY_ISO`): ERCOT/NEISO/CAISO/MISO `(2019,2020,2021,2023,2024,2025)`; NYISO/PJM `(2021,2023,2024,2025)`. Fine for both phases; 2018 unavailable. | — |
| 6 | **Demand — growth path** | **CLOSED — mechanism (FH-2) + values (FH-3)** | `DEMAND_GROWTH_RATES` is a two-era scalar table (`constants.py:1604`) derived from **2025/26** LTLF/Gold Book/CELT/IEPR editions, with `DEMAND_GROWTH_TRANSITION_YEAR = 2030` so every historic year takes the `near` rate. ERCOT mid is **8.5 %/yr** — applied 2021→2023 that is **+17.7 %** against roughly +2 % actual. There are no vintage variants. Compounding defect: `_scale_demand` loops `range(weather_year, year)`, so for `year < weather_year` the factor is silently **1.0** (no de-growth, no error). **FH-3 landed the VALUES 2026-08-02**: `DEMAND_GROWTH_RATES_VINTAGES` in `constants.py`, 11 of 12 ISO-vintage cells cited to the editions published at the time (as-of-2021 ERCOT near is **2.0 %/yr**, not 8.5 %). Missing cell: CAISO as-of-2021 (manual download, Phase B only). FH-2's `demand_growth_vintage` field + `resolve_demand_growth_table` resolver landed in PR #3278; FH-3 additionally extended the resolver's refusal to a missing CASE, since most vintage cells carry `mid` alone. | ~~**FH-2** (mechanism)~~ + ~~**FH-3** (values)~~ |
| 7 | **Fuel — gas** | PARTIAL | `hindcast_asknown_aeo2021` (AEO2021 Reference) covers 2021/2023/2024/2025 — the only genuine as-known path, and it is flagged NEEDS CITATION in `docs/parameter-citations.md`. ~~**No AEO2023 equivalent exists**, so Arm K at base 2023 is blocked on intake.~~ **RESOLVED 2026-08-02 (FH-3):** `hindcast_asknown_aeo2023` landed (AEO2023 Reference Table 13, nominal-converted by the edition's own GDP price index) — **Arm K at base 2023 is unblocked**; and `hindcast_asknown_aeo2021` was **corrected** (its old values matched no basis of the AEO2021 series) and cited. Trap: `low/mid/high` start at 2023, and `_hold_flat_extrapolate` holds at the *earliest* knot when no earlier one exists — a pre-2023 year on `mid` silently returns the 2023 value ($2.54 vs 2021 actual $3.91, ~35 % wrong) with no warning. | **FH-3** (values), **FH-1** (guard) |
| 8 | **Fuel — coal / oil** | DISCLOSE | Both trajectory families start **2025**, so `growth_ratio` degenerates to 1.0 and every year ≤2025 resolves to flat `COAL_PRICE_BASE[iso]` / `OIL_PRICE_PER_MMBTU`. Resolves; carries zero historic signal. **FH-3 2026-08-02: the AEO2021/AEO2023 coal + oil series ARE landed** (same raw CSVs as the gas pull, cited) — but the degeneracy is a *mechanism* gap, not a data gap: adding pre-2025 knots to `COAL_PRICE_TRAJECTORIES` would move `anchor_year` and rescale every forecast year 2026-2050 (a default change FH-3 may not make). Needs a `hindcast_asknown_*` coal/oil path + selector, mirroring gas. **DISCLOSE line and the landed series: `docs/handoffs/fh-3-asknown-driver-vintages-2026-08.md` §6.** | ~~FH-3~~ → FH-2 (mechanism) |
| 9 | **Fuel — nuclear / basis** | RESOLVES | Nuclear historical series covers 2006–2024. `GAS_BASIS_DIFFERENTIAL` is a year-invariant per-ISO scalar — resolves for any year, but was derived from 2023–2025 receipts, so applying it to 2021 is an as-of violation in spirit. Disclose. | — |
| 10 | **Renewable CF** | PARTIAL | Pinned to `weather_year` (`runner.py:531`), same pool bound as #5. `vintage_capacity_ramp` scales to EIA-860 COD dates and honours the active vintage. | — |
| 11 | **Hydro** | **LEAK** | `forecast_monthly_hydro` is the correct forward analogue (climatology, not measured level) but `HYDRO_CLIMATOLOGY_YEARS = (2021,…,2025)` is fixed — a 2021-base run builds its climatology from four *future* years, and the window **includes quarantined 2022**. The fix is caller-side: `climatology_years` is already a parameter (`data/hydro.py:214-217`). | **FH-1** |
| 12 | **Emission rates** | **LEAK** | The forecast branch takes the last N years **present in the artifact**, not the last N ≤ target year (`data/emission_rates.py:288-291`: `years = sorted(...); years = years[-window:]`). A 2021 forecast-mode solve derives its CO2 rates from **2024–2025** CAMPD. One-line fix: `years = [y for y in years if y <= target_year][-window:]`. (Also: the artifact carries 2022 rows for PJM/MISO/NEISO and 2026 for NYISO — quarantined years sitting inside a live forecast input.) | **FH-1** |
| 13 | **Capacity prices** | RESOLVES* — **AUDITED CLEAN (FH-2)** | Genuinely vintage-complete for historic delivery years — PJM 2021/22–2027/28, NEISO 2020-21–2027-28, NYISO/MISO 2021-22–2025-26; CAISO/ERCOT have no table (ERCOT energy-only ⇒ 0). *Binds only with the CR-1 clearing gate armed (`--capacity-market-clearing`, per-ISO) **and** `year` threaded to the screens — today `year` reaches the seam only from storage entry (`model/storage.py:1092`); the thermal retirement and entry call sites need auditing. | **FH-2** |
| 14 | **Policy (RPS / carbon)** | PARTIAL/LEAK — **PARTLY CLOSED (FH-2)** | `STATE_RPS_FLOORS` knots start **2026** and `get_rps_target` edge-holds, so every historic year receives the **2026** target. `projected_price` anchors carbon on the 2025 value for any earlier year. `RGGI_MEMBER_STATES_BY_YEAR` covers **2023–2025 only** — a 2021 run cannot express Virginia's 2021 RGGI participation. IRA §45 PTC vintaging (`wind_ptc_vintage_offers`) is genuinely vintage-native and correct. | **FH-2** (smallest-first), else DISCLOSE |
| 15 | **Scoring benches** | RESOLVES for scope | 2023–2025 hourly + annual benches exist for all six ISOs. Pre-2023 is thin (CAISO none before 2023, MISO none before 2022; hourly only NEISO 2022) — **irrelevant, because scoring never leaves 2023–2025.** Capacity-event actuals (`capacity_actuals_*.csv`) span the full window. | — |

**Summary:** two BLOCKERs (#2 planned additions, #6 demand growth), two LEAKs closable in a line
each (#11 hydro window, #12 emission window), one intake dependency (#7 AEO2023 for Arm K), and a
short disclose list (#8 coal/oil flat, #9 basis vintage, #14 policy edge-hold). Nothing is
architecturally missing — which is why this program is tractable.

> **FH-2 UPDATE 2026-08-02 — rows 6 / 13 / 14.** Evidence:
> `docs/handoffs/fh-2-as-of-driver-plumbing-2026-08.md`.
>
> * **Row 6 — mechanism CLOSED, values pending.** `DEMAND_GROWTH_RATES_VINTAGES`
>   (`{as_of_year: {iso: {low|mid|high: {near, long}}}}`) + `ScenarioConfig.demand_growth_vintage`
>   (default `None`, cache-neutral, matrix row `demand_growth_vintage`) + the
>   `resolve_demand_growth_table` seam. **Fail-closed:** an unknown vintage, a vintage missing the
>   run's ISO, or a vintage in backcast mode all RAISE — never a silent fallback to the current
>   table. The registry ships EMPTY, so every vintage request raises until **FH-3** lands the cited
>   per-ISO edition values; **FH-4** then sets `demand_growth_vintage = base_year` on Arm K (not
>   wired here — nothing to select yet). The compounding half is fixed too: `_scale_demand`'s
>   backward span no longer returns a silent 1.0 — it hard-errors in the T1-FF lane and de-grows
>   correctly (exact inverse, logged) elsewhere.
> * **Row 13 — the "needs auditing" premise is STALE; audited clean.** All three screens already
>   thread `year` into `capacity_price_per_firm_mw_yr` (retirement `retirements.py:1736` via
>   `evolve.py:497`; thermal + VRE entry `new_entry.py:902/1012` via `evolve.py:601`; storage
>   `storage.py:1092`), so `resolve_demand_curve_vintage` does select the historic delivery year.
>   Verified on the committed PJM 2021/22–2025/26 anchors (117.37 / 95.08 / 100.36 / 107.01 /
>   83.52 $/kW-yr) and now pinned by regression tests so it cannot silently regress. No default
>   flipped — the CR-1 clearing gate stays owner-armed. One un-threaded consumer found and
>   DISCLOSED: `results/plant_financials.py:537` (reporting only, no decision effect).
> * **Row 14 — partly closed.** LANDED: `RGGI_MEMBER_STATES_BY_YEAR[2021]` (2021 is the seed solve
>   year; without it `per_generator_membership` fell back to the 2025 post-Virginia-exit set) and
>   CAISO's statutory historic RPS knots (2021 → 0.33 SB X1-2, 2024 → 0.44 SB 100, both Pub. Util.
>   Code §399.15(b)(2)(B)); 2026+ knots untouched, and no backcast is affected at all
>   (`backcast_config` sets `rps_enabled=False`). STILL DISCLOSED: the PJM/MISO/NYISO/NEISO RPS
>   knots (their 2026 values are this repo's own load-weighted per-state blends — a historic knot
>   is a cited re-blend, never an interpolation), the carbon `projected_price` anchor (the same
>   back-hold class FH-1 hard-errored for gas; measured 2021 anchors exist but are an
>   owner-authorized intake), and RGGI 2022 (the evolved-never-solved bridge year, rule 22).

---

## 5. Governance — why T1-FF is quarantine-legal

1. **Scoring never leaves 2023–2025.** Both phases score only calibration-window years, so no
   validation or locked-test year is spent. `score_crossover.py`'s `_assert_scoreable_year`
   already enforces the upper bound; FH-1 adds the symmetric lower bound.
2. **2021 solves as a seed, never scored; 2022 is evolved-never-solved.** These are the *existing*
   T1-H allowances (`ALLOWED_SOLVE_YEARS = {2021, 2023, 2024, 2025}`,
   `HINDCAST_BRIDGE_YEARS = {2022, 2026}` at `runner.py:178`), asserted today only in prose
   (plan §7.4) and a local `_validate_window`. **FH-1 moves them into
   `scripts/lib/holdout_policy.py`** so the carve-out is code, not custom.
3. **The holdout freeze does not block this — and the harness must say so explicitly rather than
   self-blocking.** The freeze is read only by
   `scripts/run_calibration_full.py::enforce_holdout_year_gate` (the backcast solve entry point);
   `run_capacity_hindcast.py` never imports `holdout_policy` or reads the freeze file today. That
   invisibility is itself a hole — FH-1 wires the harness to the policy module **with** the
   hindcast allowances encoded, so the outcome is deliberate rather than accidental.
4. **Data intake is unaffected** (rule 22 channel 1, no-LP, owner-logged) — and this program needs
   none for out-of-training *backcast* years anyway.
5. **≤5 solve-years per invocation**, both phases, by construction.

---

## 6. Wave FH — prompt pack

House conventions as the FFR pack: `[FABLE]` = structural/core-writing work, `[OPUS]` = spec'd
execution, solves, intake, plumbing (never Sonnet — rule 27). Sessions within a wave are
file-disjoint parallel unless flagged.

**Sequencing.** FH-1 / FH-2 / FH-3 launch in parallel and may run concurrently with FFR Wave 2.
**FH-4 and FH-5 are gated on FFR Wave 1 merging + §W1-X's cache-epoch bump** (FR-7/FR-8 corrupt
weather-pinned historic runs; a stale epoch would serve pre-fix cached bundles).

**Every prompt implicitly begins:** *Read CLAUDE.md, `docs/hindcast-forward-plan-2026-07.md`
(this doc — your §4 rows and §5), and `docs/forecast-development-plan-2026-07.md` §7 (binds).
Fresh branch off latest `origin/main`; `git config user.email noreply@anthropic.com && git config
user.name Claude`.*

**Every prompt implicitly ends:** *Push via `mcp__github__push_files` or a verified small-pack
`git push`; blob-verify any pushed file ≥300 lines. Register every run on the hindcast namespace
in the producing session (`meta.kind = "full_forward"`) — NEVER the backcast registry. Update the
mechanism-matrix cell for any mechanism tested and add a matrix row for any new `ScenarioConfig`
field, same PR. Findings doc to `docs/handoffs/fh-<id>-<topic>-<date>.md`. No tuning: a residual
closable only by an unidentified value is an open blocker, written up (rules 1/13/14/21). Every
solve invocation ≤5 solve-years.*

### FH-1 [FABLE] — the harness + closing the historic-year leaks

```
[FABLE] FH-1 — Add full-forward hindcast mode (T1-FF) and close the four
information leaks that only bite once the forward boundary drops below 2026

Read (beyond the implicit set): docs/hindcast-forward-plan-2026-07.md §1.2, §2,
§4 rows 2/11/12, §5; scripts/run_capacity_hindcast.py (_validate_window,
build_config, assert_forward_drivers, assert_pipeline_from_vintage);
src/market_sim/config/scenarios.py::is_crossover_forward_year (the seam — read
its docstring, it already specifies this behaviour); scripts/lib/holdout_policy.py;
docs/handoffs/ff-t1-gate-2026-07.md §4.2-4.3 (the I6 over-retirement property).

1. HARNESS MODE. Add --forward-from-base to run_capacity_hindcast.py: sets
   crossover_forward_year = start_year so EVERY solve year runs the forward
   input stack. Generalize _validate_window for it (allow vintage 2020 in this
   mode; keep the 2021 floor, the {2021} seed allowance and the 2022 bridge);
   record mode + arm in meta.json (kind="full_forward", arm, base_year,
   vintage, weather posture). Two arms per §2.1: --arm realized|asknown wires
   the gas path and the weather-year pin (realized -> solve year; asknown ->
   base year). Do NOT invent a second input stack — the seam is the mechanism
   (rule 19).
2. LEAK: planned additions (§4 row 2, a LIVE BUG for any vintage-seeded run).
   Make EIA860_OPERABLE_VINTAGE vintage-derived using the existing
   _clean_fleet_year pattern (data/fleet/models.py:67-85). AUDIT EVERY
   CONSUMER, not just the filter: data/fleet/eia860.py:1809 (the additions
   filter), model/capacity_evolution/retirements.py:465 (default vintage
   param), config/capacity_market.py:1588 (announced horizon). Prove the 2021
   and 2023 vintages now admit their own proposed sheets (count units before/
   after in the findings doc).
3. LEAK: emission-rate window (§4 row 12). data/emission_rates.py:288-291 —
   bound the trailing window by target_year:
   years = [y for y in years if y <= target_year][-window:]. Assert no
   quarantined year (2022, >=2026) can enter a T1-FF solve's rate basis.
4. LEAK: hydro climatology (§4 row 11). Trim climatology_years to <= base year
   at the caller (the parameter already exists in
   data/hydro.py::forecast_monthly_hydro) — and exclude 2022. State in the
   findings doc what a base-2021 climatology is then built from, and if the
   remaining sample is too thin to be credible, say so as a finding rather
   than widening the window.
5. GUARDS. Generalize assert_forward_drivers to assert EVERY solve year at/above
   the boundary (it currently no-ops below 2026) and to cover the demand-loader
   and F923 skips at run time, not only in unit tests. Add a hard error for the
   silent back-hold trap (§4 row 7): resolving a low/mid/high gas path for a
   year below the trajectory's earliest knot must RAISE in T1-FF mode, never
   silently return the earliest knot.
6. GOVERNANCE. Wire the harness to scripts/lib/holdout_policy.py and the freeze
   file, moving the hindcast allowances ({2021} seed, {2022,2026} bridge) out of
   prose into the policy module. Fail closed on anything else. Scoring lower
   bound: no scored year below 2023 (symmetric to the existing >=2026 refusal).
7. HARNESS-DEFECT GATE (§3.3). Before any Phase-A read: reproduce or refute the
   T1-X I6 forward-year over-retirement (25.6% thermal by 2025) at the T1-FF
   posture on ONE ISO, T0 scale. If it reproduces, that is a stop-the-line
   finding — file it; Phase A does not proceed on an over-retiring harness.

ACCEPTANCE: existing T1-H and T1-X behaviour byte-identical when
--forward-from-base is off — attest against the committed ERCOT/PJM crossover
meta + cache keys. If any committed crossover moves, STOP and file it (rule 11).
Do not: change any ScenarioConfig default; touch adequacy.py/evolve.py (FFR
sessions own those); exceed 5 solve-years in any invocation; solve 2022 or any
year <=2019.
Deliver: findings doc with the per-leak before/after, the additions
before/after counts, the byte-identity attestation, and the §3.3 gate result.
```

### FH-2 [OPUS] — as-of driver plumbing

```
[OPUS] FH-2 — Make the demand-growth, capacity-price and policy channels
as-of-vintage addressable (no values, no solve)

Read (beyond the implicit set): docs/hindcast-forward-plan-2026-07.md §4 rows
6/13/14; src/market_sim/config/constants.py (DEMAND_GROWTH_RATES,
DEMAND_GROWTH_TRANSITION_YEAR); src/market_sim/runner.py::_scale_demand;
src/market_sim/config/capacity_market.py (MARKET_DESIGN_VINTAGES,
resolve_demand_curve_vintage).

1. DEMAND GROWTH (the second BLOCKER). Add DEMAND_GROWTH_RATES_VINTAGES keyed
   {as_of_year: {iso: {low|mid|high: {near, long}}}} plus a
   demand_growth_vintage ScenarioConfig field (default None => today's table,
   so every existing run is byte-identical). Register it in the cache key and
   add its matrix row IN THIS PR. FH-3 lands the values; you land the
   mechanism, the resolver and the tests (an unknown vintage must RAISE, never
   fall back silently).
2. _scale_demand BACKWARD NO-OP. runner.py's range(weather_year, year) yields
   an empty range when year < weather_year, silently applying factor 1.0. Make
   it explicit: either scale correctly in both directions or hard-error in
   forecast/T1-FF mode. Silent 1.0 is never acceptable — it is exactly the
   class of defect FR-7/FR-8 belong to.
3. CAPACITY PRICES. Audit whether `year` reaches all three screens (thermal
   retirement capacity_revenue_per_mw_yr, thermal entry, storage entry — today
   only storage threads it, model/storage.py:1092) and thread it where missing,
   so resolve_demand_curve_vintage actually selects the historic delivery-year
   vintage. Verify on the committed PJM 2021/22-2025/26 anchors. No default
   flip: the CR-1 clearing gate stays owner-armed.
4. POLICY, SMALLEST-FIRST. Add the RGGI membership rows for 2021/2022 and any
   historic RPS targets that are PUBLISHED (cited, rule 5). Where no published
   historic value exists (the carbon anchor), leave it and add the line to this
   doc's disclose list — do NOT invent a back-cast target.
Do not: land any driver VALUES (FH-3's); change a default; solve anything.
Deliver: findings doc + the mechanism, tests, cache-key/matrix rows, and a
table of which policy channels became as-of-correct vs stay disclosed.
```

### FH-3 [OPUS] — as-of driver intake (DATA + CITATIONS ONLY, parallel-anytime)

```
[OPUS] FH-3 — Land the as-known driver vintages Arm K needs (data only)

Read (beyond the implicit set): docs/hindcast-forward-plan-2026-07.md §2.1, §4
rows 6/7/8; src/market_sim/config/fuel_trajectories.py (HENRY_HUB_TRAJECTORIES,
the existing hindcast_asknown_aeo2021 entry); docs/parameter-citations.md;
docs/fuel-forward-methodology-2026-07.md. Use the data-intake skill.

1. GAS. Land an AEO2023 Reference Henry Hub trajectory as
   hindcast_asknown_aeo2023 (Arm K, base 2023). Every value cited to the AEO
   table + edition. Also CLOSE the standing citation gap on
   hindcast_asknown_aeo2021 (currently flagged NEEDS CITATION in
   parameter-citations.md) — verify its values against AEO2021 Reference and
   either cite or correct them (rule 23: a value change cites the data, never
   a residual).
2. DEMAND GROWTH VINTAGES. Land as-of-2021 and as-of-2023 near/long growth
   rates per ISO into FH-2's DEMAND_GROWTH_RATES_VINTAGES, from the editions
   published at that time (ERCOT LTLF, PJM LTLF, NYISO Gold Book, ISO-NE CELT,
   MISO LTLF, CEC IEPR). Each ISO-year-case cites its edition and table. Where
   an edition is unreachable, log a MANUAL DOWNLOADS NEEDED row — never
   interpolate a growth rate.
3. COAL/OIL (optional, only if reachable): AEO coal vintages would remove the
   flat-COAL_PRICE_BASE degeneracy (§4 row 8). If not reachable, write the
   disclose line instead and stop — do not synthesize a series.
No solve; no CI workflow; no code beyond the trajectory/table entries FH-2's
mechanism reads.
Deliver: findings doc + parameter-citations.md rows + any MANUAL DOWNLOADS
NEEDED list.
```

### FH-4 [OPUS] ⛔ — Phase A: base-2023 runs, six ISOs, both arms

```
[OPUS] FH-4 — Execute Phase A (base 2023, 2023-2025, Arms R and K, 6 ISOs) and
deliver the three-way skill table

REQUIRES: FH-1 + FH-2 + FH-3 merged; FFR Wave 1 merged and its §W1-X
cache-epoch bump applied (FR-7/FR-8 corrupt weather-pinned historic runs);
FH-1's §3.3 harness-defect gate PASSED. Do not start otherwise — say so and
stop.
STATUS 2026-08-02: DO NOT DISPATCH. FH-1 merged and the §W1-X bump is applied,
but the §3.3 gate FAILED — the I6 over-retirement REPRODUCES at the T1-FF
posture (26.8 % of prior thermal in 2025; I6/I7 FAIL, I12 WARN). See §3.3's
gate-result block and docs/handoffs/fh-1-full-forward-harness-2026-08.md §7.
The block lifts only when a retirement-lane fix lands AND a re-probe passes.

Read (beyond the implicit set): docs/hindcast-forward-plan-2026-07.md §2, §3.1,
§5; scripts/score_crossover.py (the input_gap construction you reuse);
frontend/data/backcast/keepers/<ISO>.json at YOUR HEAD (the comparators — they
move daily, never quote an id from a doc).

1. PRE-REGISTER before solving: per ISO and metric, the expected direction and
   the read you will make, committed in the findings doc skeleton FIRST. No
   post-hoc arm or metric selection.
2. SOLVE: base 2023, window 2023-2025 (3 solve-years per invocation — inside
   the cap), vintage 2023, Arms R and K, six ISOs. Rule 12: years sequential
   within an invocation; <=2 concurrent invocations; PJM and MISO never co-run.
   Reuse cache aggressively; resume killed runs from the per-year cache.
3. SCORE 2023-2025 ONLY, against bench + each ISO's CURRENT keeper backcast
   scores. Produce the three-way table of §2.1: keeper err -> Arm R err ->
   Arm K err, per metric per year, with the two spreads named (overlay value;
   driver-forecast error).
4. REGISTER every run on frontend/data/hindcast/ with meta.kind="full_forward"
   in this session (rule 15).
5. READ IT HONESTLY: a large R-vs-keeper gap is the measured price of the
   overlays and is the program's DELIVERABLE, not a failure to fix. Do not tune
   anything in response (rules 1/13). Anything that can only be closed by an
   unidentified value is an open blocker, written up.
Do not: score any year outside 2023-2025; solve 2022 or <=2019; widen a band;
change a default; exceed 5 solve-years per invocation.
Deliver: findings doc with the pre-registration, the three-way table, per-ISO
narrative, and the honest-limitations list (peer review §4 disclosure text).
```

### FH-5 [OPUS] ⛔ — Phase B: base-2021 horizon extension

```
[OPUS] FH-5 — Execute Phase B (base 2021, 2021-2025, Arms R and K) for the ISOs
where Phase A ran clean; deliver the horizon-degradation table

REQUIRES: FH-4 complete and its results read; run ONLY for ISOs whose Phase A
was clean (an ISO with an unexplained Phase-A anomaly is not extended — fix or
file first).

Read (beyond the implicit set): docs/hindcast-forward-plan-2026-07.md §3.1,
§4 rows 4/11; FH-4's findings doc.

1. SOLVE: base 2021, vintage 2020 (the full 30-file vintage), window 2021-2025
   = 4 solve-years (2021 seed-only, 2022 BRIDGED — evolved, never solved),
   Arms R and K. Inside the cap. Rule-12 scheduling as FH-4.
2. SCORE 2023-2025 ONLY (2021 is a seed and is never scored — this is the
   existing T1-H allowance, now codified by FH-1).
3. DELIVER the horizon-degradation read: 1-year-ahead (Phase A 2023) vs
   2-year (2024) vs 4-year (2025 from a 2021 base) skill, per ISO per metric.
   This is the first measurement of how forecast skill decays with horizon in
   this model — state it plainly, with its caveats.
4. CAVEAT UP FRONT, not in a footnote: statistical outages do not reproduce
   Winter Storm Uri, so ERCOT 2021 dispatch is low-fidelity by construction
   (§4 row 4); and the 2021 hydro climatology is thin after FH-1's as-of trim.
   Neither is a defect to fix here — both are properties to disclose.
Do not: tune; score outside 2023-2025; solve 2022; exceed 5 solve-years.
Deliver: findings doc + registered runs + the horizon-degradation table, and a
recommendation on whether a pre-2021 base is worth chartering (§3.2 refusal
record is the starting position — argue against it only with evidence).
```

---

## 7. What this program does not do

- **It does not replace the backcast.** Calibration stays 2023–2025 with measured overlays; T1-FF
  measures what happens without them. A poor T1-FF score is not a reason to re-tune a keeper
  (rule 1) — it is evidence about forecast-configuration structure.
- **It does not touch validation or locked-test years.** Nothing here spends 2022, 2019, ≤2021
  scoring, or H1-2026. Phase B *solves* 2021 as an unscored seed under the existing T1-H
  allowance and *bridges* 2022 without solving it.
- **It does not schedule a full horizon.** Every invocation is 3–4 solve-years.
- **It does not build a general "vintage mode."** A true as-of-base-year information cutoff across
  ATB/capex, policy and all fuel families does not exist and is not attempted; FH-1/FH-2 close the
  leaks that materially bias *these* windows, and §4 records the rest as disclosed.
