# CO2-first emissions plan: CAMPD-grounded forward rates — 2026-07-04

**Owner direction (2026-07-04):** CO2 accuracy is the objective; NOx/SO2 are secondary. For
existing units, forecast CO2 rates must be grounded in historic measured CAMPD plant
performance — not frozen pooled values, not generic heat-rate constants. This handoff resolves
audit EM-3's provenance question, designs the intake + rate model, validates it empirically
(leave-one-year-out within 2023–2025), and re-ranks the remaining `docs/fable-repo-audit-2026-07.md`
§A items CO2-first. **Nothing here is implemented** — the implementation prompt is in §8.

---

## 1. Data inventory (what exists today)

### 1.1 Raw CAMPD extracts

| Dir | Grain | Columns | Coverage | Size |
|---|---|---|---|---|
| `data/raw/campd-unit-level/` | **hourly, per unit** | stateCode, facilityName, facilityId, unitId, date, hour, **opTime**, grossLoad (MW), steamLoad, so2Mass (lb), co2Mass (short ton), noxMass (lb), heatInput (MMBtu), primaryFuelInfo, unitType, programCodeInfo | 34 states × 2023–2025; **plus 15 states × 2022 and × 2026-Q1 (holdout intake, QUARANTINED — untouched here)** | 362 MB |
| `data/raw/campd-facility-level/` | **hourly, per facility** | as above minus unitId/opTime/fuel/unitType/program | 13 states × 2023–2025 (TX, CA, NY/NJ, NEISO, PJM-east) | 78 MB |

There is **no annual CAMPD dataset on disk** — everything annual is derived from hourly. There
is **no start-count column** anywhere; starts are derived from `gross_mw > 1 MW` off→on
transitions (`campd._startup_factors`, `_ONLINE_MW`). Op-hours, heat input, gross gen and the
three pollutant masses are all present at both grains. `market_sim/data/campd.py` prefers
facility-level per state (ERCOT/TX reads facility files), falling back to unit-level; unit rows
are facility-summed downstream, with the CA split-plant remap (`CAMPD_UNIT_PLANT_REMAP`) the
only unit-identity consumer today besides the CT run-length artifact.

### 1.2 The live rate artifact is stale, TX-only, and carries quarantined rows

`data/raw/_processed-legacy/plant_emission_rates.parquet` (consumed by
`use_plant_emission_rates=True` via `fleet.py:4555-4623`):

- **TX-only** — 131 plants. The other five ISOs have **zero** plant-rate coverage and book CO2
  at tranche bid heat rate × fuel factor (see R2/EM-4 below).
- **Pooled `year==0` rows sum 2023+2024 only** (verified: Limestone pooled gross 12,650,593 =
  6,712,412 + 5,938,181). 2025 never entered the pool — the audit's "pooled 2023-25" description
  is generous; the live rates are a stale two-year pool.
- **Per-year rows for 2022 and 2026 are present** (appended by the holdout-intake follow-up
  commit a0faf74). They do **not** contaminate the pooled row, but quarantined-year rates
  sitting in a live model input are a re-arm surface (rule 26 spirit). Any re-derivation must
  exclude them until ERCOT's calibration-complete marker exists; this plan's history is
  **2018–2021 + 2023–2025 only**.
- W A Parish (3470) is the only `mixed`-flagged ERCOT plant and is skipped by the override —
  **4.6–6.3% of keeper model thermal GWh** has no measured rate solely because facility-level
  CEMS blends its coal and gas units. Unit-level history dissolves this exclusion (§3).

Coverage of the current ERCOT keeper (`ercot_ordc_total_rtolcap_v1`): 95.4 / 95.3 / 93.7% of
model thermal GWh carries a measured plant rate in 2023/2024/2025; the remainder is Parish.

### 1.3 Simulated-operation outputs available in keeper bundles

Keeper bundles persist per-plant-year `plant_hourly_fit.parquet` (`model_gwh`, `campd_gwh`,
`campd_op_hours`, `cap_mw`, r/NRMSE) and `plant_cf_bands.parquet` (10-band CF-duration
histograms, model vs CAMPD). **Simulated start counts are not persisted** — hourly per-plant
dispatch is not stored, so run-length analysis is only possible at solve time. The
implementation must persist per-plant model starts + op-hours into the bundle (cheap columns on
`plant_hourly_fit`); until then, operation-conditioning uses (model_gwh, CF-band distribution),
which is what the LOYO below does.

---

## 2. Rate-model design

### 2.1 Chosen design

Per plant (the model's unit of dispatch), the forward CO2 rate is:

1. **Base: gen-weighted trailing average** of annual CAMPD net CO2 intensity over the
   available history (2018–2021 + 2023–2025, growing as years land):
   `rate = Σ_y co2_kg[y] / Σ_y net_mwh[y]` over a trailing window (window length re-validated
   by the LOYO harness once the 7-year history exists; with 3 years, all-years gen-weighted won).
2. **Operation-conditioned refinement, envelope-gated (rule-13 preferred form):** when the
   plant's MODEL-simulated operation for the target year (total gen, starts, CF-duration shape)
   falls **outside the envelope** of its historical operating points, replace the base with the
   nearest-neighbor historical year's rate — distance on normalized (annual gen, starts,
   CF-band distribution L1). Inside the envelope, keep the base: with near-duplicate history
   years, picking a single year discards averaging and costs more variance than the
   conditioning recovers (measured directly in the LOYO: the oracle NN loses to the average on
   2023/2024 targets).
3. **Unit-composition mask (the concrete payoff of unit-level intake):** history is built per
   CEMS **unit**, then aggregated to the plant over only the units present in the target-year
   fleet. A plant that retires a unit (or a Parish-style coal+gas facility whose bins split by
   fuel) gets a forward rate from the surviving/matching units' history, not the blended
   facility rate. This removes the `mixed` exclusion and makes retirements move the rate — a
   forward driver no facility-level pool can express.
4. **Class fallback for CEMS-uncovered plants and new entrants:** per-class (plant_group ×
   fuel) rate distributions derived from the same CAMPD annual observations (gen-weighted
   class median for entrants; documented percentile choice), replacing generic
   `heat_rate × FUEL_CO2_FACTOR` constants.

**Mode policy (resolves EM-3):** `use_plant_emission_rates` stays on in both modes; the
*source* is mode-aware. Backcast years use the target year's own measured rate (a reproducible
physical input, exactly analogous to CAMPD outage windows and delivered fuel prices — the
forward analogue is this estimator). Forecast years use the estimator above. This gives the
backcast clean MWh-error attribution (rate error ≈ 0 by construction) while the estimator's
skill is certified separately by the committed LOYO harness — never by the keeper fit.

**Where the rate binds:** in zero-carbon-price ISOs the CO2 rate is reporting-only, so the
conditioned refinement can run **post-solve** (no circularity with dispatch). In carbon-priced
ISOs (CAISO/RGGI) the merit order uses the base estimator; the reporting rate applies the
conditioned refinement post-solve. The ~2% gap between the two is far below the allowance-cost
signal and avoids a fixed-point iteration (rule: one-pass).

### 2.2 Weighting justification (empirical)

Gen-weighted beat simple-mean and recency-weighted at every target year (LOYO wMAPE 2.20% vs
2.28% vs 2.46%). Gen-weighting is also the physically right prior: high-output years carry more
combustion hours per rate observation (tighter estimate) and dominate the CO2 that the rate
multiplies. Recency-weighting has no support in a 3-year history; re-examine with 7 years
(aging/retrofit drift) via the same harness before adopting.

### 2.3 Per-unit vs per-class support (validation verdict)

The data supports **per-unit (per-plant) conditioning in nearest-neighbor form**, not
per-class regression: the class delta-regression variant (rate deviation ~ CF deviation,
pooled per class) *degraded* accuracy (2.88% vs 2.20% base), while per-plant NN improved it.
Operation-rate coupling is real but weak and heterogeneous (CC_REGULAR corr(rate_dev, cf_dev)
= −0.33; CT_PEAKER +0.25 vs cf, +0.20 vs starts; CHP ≈ 0) — a pooled slope mis-transfers
across plants. Class-level information enters only as the entrant/uncovered fallback
distribution, never as a conditioning slope.

---

## 3. LOYO validation evidence (2023–2025, ERCOT/TX, 126 plants with 3 clean years)

Method: for each target year Y, predict every plant's net CO2 intensity from the other two
years' history; estimator (b) conditions on the **keeper's simulated operation** for Y
(`ercot_ordc_total_rtolcap_v1`: model_gwh + model CF-band distribution vs history CAMPD
actuals). Scored net-gen-weighted. `frozen` = the committed pooled artifact (in-sample for
2023/2024 targets — it contains them; 2025 is the only honest column for it, where it is
*identical* to a_gw by construction). Harness: to be committed as `scripts/loyo_co2_rates.py`
(run this session from scratchpad; quarantined years never read).

**Gen-weighted |rate error| % / fleet CO2 bias % (at actual generation):**

| Target | frozen (leaky) | a_gw avg | a_sm simple | a_rw recency | b_nn oracle-op | **b_nn sim-op** | b_reg class |
|---|---|---|---|---|---|---|---|
| 2023 | 0.86 / −0.11 | 2.01 / −0.49 | 2.12 / −0.50 | 2.37 / −0.63 | 2.35 / +0.11 | 1.94 / +0.00 | 2.68 / −0.18 |
| 2024 | 0.86 / +0.11 | 1.89 / +0.07 | 1.96 / −0.02 | 2.23 / −0.12 | 2.34 / +0.16 | 2.09 / −0.05 | 2.31 / +0.25 |
| **2025 (clean)** | 2.70 / +0.35 | 2.70 / +0.35 | 2.75 / +0.41 | 2.77 / +0.38 | 2.65 / +0.36 | **2.42 / −0.24** | 3.67 / +0.83 |
| ALL | 1.47 | 2.20 / −0.02 | 2.28 | 2.46 | 2.45 | **2.15 / −0.10** | 2.88 |

Key readings:

- **Plant CO2 rates are highly persistent**: within-plant across-year rate CV median 1.3%,
  p90 6.2%. Even the plain multi-year average holds plant-level rate error to ~2.2% and fleet
  CO2 bias below 0.5% — rate error is a small contributor against the ±10% asset-level
  objective; MWh error dominates. This bounds the stakes honestly.
- **Sim-conditioned NN is the best fair estimator** (2.15% all, and 2.42% vs 2.70% on the only
  clean year), *despite* using the model's imperfect simulated operation — i.e. conditioning
  survives realistic operation error. Structure (rule 13) and accuracy point the same way.
- **Naked NN is not free**: the oracle-operation NN *loses* to the average on 2023/2024
  targets (variance cost of discarding the second year). Hence the envelope gate in §2.1 —
  condition only when simulated operation leaves the historical envelope, which is exactly
  when the average is least defensible and the forecast needs the response most.
- 2025 is harder for everything (fleet turnover + a preliminary-vintage year) — consistent
  with the keeper's C2 caveat.
- By class, everything is tight (1.3–2.1%) except `OTHER` (2.6–4.8%, small gen share).

**Startup CO2 materiality (EM-5), measured:** Σ(starts × per-start incremental CO2) = 31.3 /
29.4 / 35.5 kt vs ~192 Mt annual — **0.015–0.018%**. Even a model that cycles units 10× too
hard stays under 0.2%. EM-5 is immaterial for CO2 and is demoted to an optional reporting
adder once model starts are persisted.

---

## 4. Data-intake spec (extend annual history to 2018)

Follows the `data-intake` skill recipe; raw is immutable; schema-first.

1. **Fetch 2018–2021 hourly unit-level extracts** with the existing
   `scripts/fetch_campd_unit_level.py` (completed-year per-state bulk files, no code change
   needed to fetch): all 34 states already present for 2023–2025, years `2018 2019 2020 2021`.
   ≈136 new state-year parquets, est. +0.4–1.0 GB. Push via `mcp__github__push_files` in
   per-year batches (413 discipline, CLAUDE.md Git section). `EPA_API_KEY` recommended over
   DEMO_KEY for 136 bulk files.
2. **Add a quarantine guard to the fetcher** (small code change): refuse `--year 2022` and
   `--year 2026` unless `--holdout-intake` is passed with an ISO whose
   `calibration-complete.json` marker exists (rule 22). Today the guard would have blocked
   nothing retroactively but prevents the next accidental intake.
3. **New curated datatype `emissions-unit-annual`** (this is the "annual unit-level CAMPD
   emissions + operations" product — derived, small, queryable; the hourly raw stays the
   source of truth):
   - `data/dictionary/schema/emissions-unit-annual.schema.yaml` — key `[plant_id, unit_id,
     year]`; columns: state, plant_id, unit_id, year, primary_fuel, unit_type, gross_mwh,
     steam_load_klbh_sum, co2_kg, nox_kg, so2_kg, heat_mmbtu, op_hours, **starts**,
     co2_source (measured/partial_backfill/heat_backfilled), mw_source (measured/heat_proxy).
   - `scripts/curate_emissions_unit_annual.py` — reads only `data/raw/campd-unit-level`
     (facility-level states get facility-grain rows with `unit_id="ALL"`), reuses
     `campd._normalize_campd` / `_startup_factors` / CO2 backfill logic, writes through
     `clean_io.write_clean(..., year=Y)`, **hard-skips 2022/2026 files** even though they sit
     on disk. Registered in `regenerate_clean.py DATATYPES`; tmp-CLEAN_DIR test with a tiny
     fixture (1 unit, 48 h, one start).
   - `data/raw/campd-unit-level/README.md` gains the 2018–2021 layout + `DATA NEEDED` lines.
4. **Re-derive the rate artifact for all six ISOs** from the annual datatype:
   `plant_emission_rates` v2 keyed (iso, plant_id, unit_id, year) with per-year rows only —
   **no baked pooled row** (the estimator pools at consumption time, per §2.1), no 2022/2026
   rows, parasitic net conversion per existing `compute_parasitic_factors` (needs EIA-923
   2018–2021, already on disk via `eia-923` raw — verify, else add to DATA NEEDED).
5. **Persist simulated operation**: extend the calibration/forecast output writer to add
   `model_starts` and `model_op_hours` columns to `plant_hourly_fit.parquet` (run-length
   analysis of the in-memory hourly dispatch at solve time; no new files).

---

## 5. Ranked fixes (CO2-first), with files, tests, expected impact

| # | Item | Files | Test | Expected CO2 impact |
|---|---|---|---|---|
| **R1** | Rate model + intake (§2–§4): 2018–2021 intake, `emissions-unit-annual` datatype, per-unit history → plant forward rate (gen-weighted base + envelope-gated NN conditioning + unit-composition mask), mode-aware source, all-ISO artifact, LOYO harness committed as `scripts/loyo_co2_rates.py` | `scripts/fetch_campd_unit_level.py`, new schema+curate, `scripts/derive_plant_emissions.py`, `src/market_sim/data/campd.py`, `fleet.py:4547-4623`, new `src/market_sim/data/emission_rates.py`, bundle writer | curate fixture test; LOYO harness re-run gates the estimator; unit test: retired-unit mask shifts Parish rate | Fixes provenance (EM-3); Parish +5–6% GWh coverage in ERCOT; five ISOs go from 0%→measured coverage; forecast rates respond to operation |
| **R2** | **EM-4** tranche price-wall contamination: book `emission_rate_co2` at the plant's *physical* HR (or measured plant rate), never the bid-tranche HR; entrant/uncovered class defaults from CAMPD class distributions (R1 artifact) | `fleet.py:6298` (`get_emission_rate(fuel, tr_hr)` → physical basis), `offer_curves.py` legacy bands, entrant construction in `capacity.py` | assert no generator's CO2 rate embeds a >1.0 pricing multiplier; entrant rate == class median fixture | Removes ×1.10–1.55 peak-tranche CO2 inflation for every CEMS-uncovered plant, all legacy-bin ISOs, **all forecast new entrants** (grows toward 2050) |
| **R3** | **EM-8** gross/net basis check: measured rates are per-net (parasitic-scaled) and model MWh are net — verified consistent *when* R2 books at measured rates; add a regression assertion + document the one residual gross-basis path (bin HR derivation is a cost input, not an emissions input, post-R2) | `campd.py`, `fleet.py`, `docs/binning-methodology.md:18` | unit assertion: rate applied × model net MWh reproduces CAMPD co2_kg on a fixture plant within backfill tolerance | Guards the 2–4% (gas) / 7–10% (coal) bias class from ever re-entering; no level change expected today |
| **R4** | **EM-6** carbon-price seam: forecast years for CAISO/NYISO/NEISO default to $0 while backcast uses measured CARB/RGGI — decide + wire a default forward allowance trajectory (config-registered, cited; e.g. last measured real price held flat as the floor case) so forecast merit order isn't calibrated-with/forecast-without | `policy/carbon.py:23,66-84`, `constants.py` (trajectory), `scenarios.py` | forecast-year resolve_carbon_price > 0 for program ISOs unless explicitly zeroed | Removes a structural backcast/forecast dispatch seam in 3 ISOs; CO2 impact via coal/gas ordering in RGGI-adjacent imports |
| **R5** | **EM-7** CHP consistency: `compute_must_run_emissions` books BTM CO2 at `get_emission_rate(fuel, hr_weighted)` while the same plant's grid tranches use measured rates; use the plant's measured rate when covered; replace the forecast `must_run_cf=0.85` fabricated-BTM fallback with historical measured BTM share × class CF | `results/emissions.py:100-178`, `data/chp.py` | fixture: covered CHP plant's BTM rate == grid rate | Consistency fix, ~1–3% on CHP-heavy plant-level CO2; small system-level |
| **R6** | **EM-5** startup CO2: measured bound is 0.015–0.018% of annual — **defer**; once R1's `model_starts` persist, add an optional reporting-only adder (Σ model_starts × measured `startup_co2_kg`) behind a default-off flag | `results/emissions.py`, bundle writer | — | ≤0.02% now; bounded ≤0.2% even at 10× cycling error |
| **R7** | **EM-1/EM-2** NOx/SO2 — **cheap unit-contract bug fix now, full wiring explicitly deferred to a later wave**: `apply_plant_emission_rates` writes tonnes/MWh into `nox_rate` while `plant_financials.py:71-72,376` consumes `nox_rate_lb_mwh` (~2204× under-cost). Fix = one canonical unit (tonnes/MWh) + explicit conversion at the plant_financials boundary + field rename. Full NOx/SO2 export/scoring/dashboard wiring is NOT in this wave. | `fleet.py:4577,4620`, `results/plant_financials.py` | unit test asserting a known plant's NOx variable cost in $/MWh | None on CO2; kills a silent 3-orders-of-magnitude financials error |

Sequencing: R1 → R2 (R2's class defaults come from R1's artifact) → R3 assertion → R7 (independent, cheap, do early) → R4 → R5. R6 rides on R1's start persistence.

## 6. CLAUDE.md L21 vs rule 13 — resolution (in writing)

**Contradiction:** CLAUDE.md L21 lists "plant-specific CEMS emission rates" among overlays that
are "backcast/calibration only; never treat them as the forecast methodology," while rule 13's
admissibility test admits any measured quantity that regenerates from forward drivers and
responds to changed conditions. `use_plant_emission_rates=True` un-gated in forecast (EM-3)
currently violates the letter of L21.

**Resolution:** measured CAMPD rates *as used in §2* pass rule 13's test and are admissible in
forecast. The forward rate is produced from forward drivers (the unit's own multi-year
measured history + the model's simulated operation for the forecast year) and responds to
changed conditions (a unit the model cycles harder maps to its high-start historical years; a
retired unit drops out of the plant's composition mask). What L21 correctly forbids is the
*same-year pinned* form — using year-Y measurements inside year-Y — which has no forward
analogue *as a forecast method*. It remains admissible **as a backcast physical input** on
exactly the same footing as CAMPD outage windows and delivered fuel prices: measured input in
backcast, estimator-generated analogue in forecast.

**Proposed L21 wording** (replace the emission-rates item in the overlay list):

> Historic overlays — CAMPD outage windows, F923 delivered fuel prices, **same-year
> plant-specific CEMS emission rates**, weather-year pinning — are **backcast/calibration
> only**; never treat them as the forecast methodology. (Forecast-year emission rates for
> existing units are *derived from* multi-year CAMPD history conditioned on model-simulated
> operation — a rule-13-admissible measured input, not an overlay; see
> `docs/handoffs/emissions-co2-rate-plan-2026-07.md`.)

## 7. Out of scope / explicitly deferred

- Full NOx/SO2 wiring (export, verdict scoring, dashboard columns) — later wave (R7 note).
- SCR/scrubber retrofit and degradation trajectories to 2050 (EM-3's tail): the trailing-window
  average picks up realized drift as history grows; a policy-driven retrofit channel is a
  separate design.
- No new calibration solves were run and none are needed for this plan; the LOYO used the
  existing ERCOT keeper bundle only. The 2022/2026 rows in the committed artifact and the
  holdout-intake files on disk were not read by any analysis here.

## 9. Implementation results (2026-07-04)

The plan is implemented on branch `claude/co2-emissions-plan-2026`. Deliverables:
`scripts/fetch_campd_unit_level.py` quarantine guard; `emissions-unit-annual`
datatype (schema + `scripts/curate_emissions_unit_annual.py` + register + test);
`src/market_sim/data/emission_rates.py` estimator (`forward_plant_co2_rate` a/b/c/d
+ `class_median_rates`) with `CO2_RATE_*` constants; `scripts/loyo_co2_rates.py`
harness; fixes R2/R3/R7; governance.

**LOYO reproduction (committed harness, ERCOT, 3-year history 2023–2025, keeper
`ercot_ordc_total_rtolcap_v1`, 131 plants / 388 plant-years).** Pooled
gen-weighted |rate error| % (mean over target years):

| frozen (leaky) | a_gw | a_sm | a_rw | b_nn_oracle | b_nn_sim | b_reg |
|---|---|---|---|---|---|---|
| 1.66 | **2.10** | 2.16 | 2.29 | 2.25 | 2.31 | 2.37 |

The **qualitative §3 ranking reproduces**: `a_gw` (gen-weighted average) is the
strong base; simple-mean, recency and the class delta-regression `b_reg` are all
worse (b_reg *degrades*, as §2.3 predicted); `frozen` is best only because it is
in-sample/leaky for 2023–2024. Exact digits differ from the §3 scratchpad table
(a_gw 2.10 vs 2.20, etc.) because this committed harness assembles history from
the `emissions-unit-annual` roll-up (unit-summed to plant, per-plant-year
parasitic net conversion) and reads CF-band shapes from the keeper bundle — a
different, reproducible construction. The `b_nn_*` columns here run the NN
**always on** (gate = 0), which the plan flags is *not* the shipped config: naked
NN is no free win (2.31 ≥ 2.10), exactly the evidence motivating the envelope
gate.

**Gate decision (acceptance).** On the 3-year history every plant's operating
points are near-duplicate, so the envelope-gated conditioner (`CO2_RATE_*`
constants) fires almost never and collapses to `a_gw`; the always-on NN does not
beat `a_gw`. Per the plan's escape hatch, **the estimator ships as pure `a_gw`**
— `constants.CO2_RATE_CONDITIONING_ENABLED = False`. The 7-year held-in re-run
(after the 2018–2021 intake lands) is the test that may open the gate; until it
demonstrably beats `a_gw`, the gate stays closed. Constants
(`CO2_RATE_TRAILING_WINDOW_YEARS = 0` → all years won at 3 years;
`CO2_RATE_ENVELOPE_GATE_L1 = 0.5`; class median percentile 50) are frozen against
backcast residuals and re-derive only on a CAMPD data update (rule 23).

**Intake status.** The 2018–2021 34-state hourly unit-level fetch runs via the
committed `scripts/fetch_campd_unit_level.py` (DEMO_KEY rate-limits to ~25/hr, so
it is paced in the background). The `emissions-unit-annual` datatype and the
committed `plant_emission_rates_v2` artifact are re-derived over whatever history
has landed; the 7-year held-in LOYO re-run and the gate re-evaluation happen once
2018–2021 are complete. The raw ~0.5 GB of binary parquet is **not** force-pushed
(push_files is text-only; a single git pack that size 413s) — it is landed and
regenerable from the fetcher; the consumed derived artifacts carry the rates. See
`data/raw/campd-unit-level/README.md`.

**Remaining follow-ups (explicitly deferred, "if time permits" per §8):** R4
(carbon-price forward trajectory, EM-6), R5 (CHP measured-rate consistency + BTM
share, EM-7), R6 (default-off startup-CO2 reporting adder — now unblocked by the
persisted `model_starts`).

## 9.1 Wave-2 results (2026-07-05, branch `claude/co2-emissions-plan-2026-wave2`)

**R4 (EM-6) — already resolved, no new code.** The forecast carbon-price seam was
closed by the parallel `emissions-mass-cap-plan` (`policy/cap_and_trade.py`):
`projected_price` anchors on the last measured CARB/RGGI clearing price and
escalates at the program's published floor-band rate (`CARB_FLOOR_ESCALATION`
0.07, `RGGI_RESERVE_ESCALATION` 0.07), and `resolve_carbon_program` returns that
projected adder for forecast years unless an explicit non-`zero`
`carbon_price_path` is chosen. The R4 acceptance test already exists and passes
(`test_cap_and_trade.py::test_forecast_carries_projected_nonzero`,
`::test_explicit_rff_path_wins_in_forecast`). No duplicate mechanism was added
(CLAUDE.md rule 15 — one mechanism per phenomenon).

**R5 (EM-7) — done.** `results/emissions.compute_must_run_emissions` now books
behind-the-meter CO2 at the plant's measured v2 `(plant, fuel-class)` rate when
covered — identical to its grid tranches — falling back to the fuel-class default
only when uncovered. The forecast flat-`0.85` CF fallback is replaced by
`measured_class_cf`, a gen-weighted op-hours utilization per CHP class, keyed off
the CEMS **steam-load** signature (`steam_load_klbh_sum > 0`, now carried into the
v2 artifact) split by `unit_type`. Wired in `runner.py` (forecast path) via
`_chp_measured_co2_inputs`; the backcast `_btm_frame` discards `mr_co2_tons`, so
the change is forecast-only. Tests: BTM==grid rate, class-CF fallback,
`measured_class_cf`.

**R6 (EM-5) — done, default-OFF.** `results/emissions.startup_co2_tons`
(`model_starts × measured startup_co2_kg / 1000`) is a reporting-only column added
to `plant_hourly_fit` only when a bundle sets
`ScenarioConfig.startup_co2_reporting` (default `False`, TIER_TAGS tier 3). Never
in the dispatch LP; bounded ≤0.2 % of annual CO2 even at 10× cycling error. No
default-config change.

**Intake (D1) status.** Wave-2 completed the 2018 34-state fetch (VA VT WI WV
landed; 2018 now 34/34) and is fetching 2019–2021 in the background, paced under
the DEMO_KEY ~25/hr ceiling (no `EPA_API_KEY` available in this environment). Raw
parquets land + push in small per-batch git commits (base = latest main; the
2018 batch was 11 MB, no 413).

**Parasitic / EIA-923 (D2) — DATA NEEDED.** `eia923_monthly_generation.parquet`
covers **2022–2026 only**; the raw `f923_*.zip` for 2018–2021 are not on disk and
the EIA archive URL is unreachable through this environment's proxy. The v2
derive already falls back to each plant's **pooled** measured parasitic factor for
uncovered years (a slowly-varying station-service fraction — the physically right
prior), so the 2018–2021 rates are well-founded; refining them needs the EIA-923
intake (recipe in `data/raw/campd-unit-level/README.md`).

**Gate decision (D3) — RESOLVED 2026-07-05, see §9.5.** The 7-year held-in LOYO
ran for ERCOT + PJM once the intake completed: the conditioning gate stays
**CLOSED** (pure `a_gw` base) and the trailing window is set to **2 years** from
the forward-chained sweep. Full tables and reasoning in §9.5; the constants
re-derive only on a CAMPD data update (rule 23), never on a keeper's CO2 fit.

## 9.2 Wave-3 results (2026-07-05, branch `claude/chp-btm-share-measured-oo8dye`)

**R5 (EM-7) — BTM share, now done.** Wave-2 closed the CO2-rate half of R5 but
left the forecast BTM-share fallback sizing `mr_mw` off the sector-keyed
default (`data.chp.chp_btm_pct`, baked into each bin's `pct_mr` at fleet-build
time) rather than a per-plant measurement. This wave adds the `chp-btm-share`
clean datatype (`scripts/curate_chp_btm_share.py`,
`data/dictionary/schema/chp-btm-share.schema.yaml`): per (iso, plant, CHP
class), `btm_share = (eia923_net_mwh − campd_net_mwh) / eia923_net_mwh`, pooled
across every available non-quarantined year, from the already-committed
`plant_emission_rates_v2` (CAMPD grid-net generation, steam-reporting units
only) and `eia923_monthly_generation` (EIA-923 Page-1 net class generation)
processed-legacy artifacts. Both sides are measured and independent of the
model's own dispatch (rule 13).

`data.chp.measured_btm_share_by_plant(iso)` reads the artifact through the
`scripts.lib.clean_io` seam; `runner._chp_measured_co2_inputs` resolves it only
for **forecast** years and threads it into
`compute_must_run_emissions(..., btm_share_by_plant=...)`, which now uses the
measured share (falling back to the bin's own `pct_mr` when a plant is
uncovered) in **both** its measured-share and measured-CF-fallback branches —
previously only the measured-share (backcast-style `total_gen_by_plant`) branch
consumed `btm_share_by_plant` at all. The backcast path
(`run_calibration_full.py::_btm_frame`) is untouched — it keeps sizing its own
`share_by_plant` from `chp_btm_pct` directly, per the acceptance scope. No
default CO2/dispatch change where the artifact is absent (the clean partition
must be curated per ISO via `scripts/curate_chp_btm_share.py` /
`scripts/regenerate_clean.py`).

## 9.3 Wave-3 results (2026-07-05, branch `claude/nox-so2-wiring-2026-wave3`)

**R7 full NOx/SO2 wiring — done.** Wave-2 fixed only the NOx unit contract
(tonnes/MWh canonical + the `plant_financials` boundary conversion + field
rename). This wave lands the full NOx/SO2 wiring §5 R7 / §7 deferred, with CO2
unchanged (byte-identical v2 CO2 columns after re-derive) and no dispatch/merit
change — NOx/SO2 are secondary.

- **Artifact.** `scripts/derive_plant_emissions_v2.py` now carries `nox_kg`,
  `so2_kg` and their net-basis intensities (`nox_kg_per_mwh_net`,
  `so2_kg_per_mwh_net`) alongside CO2; NOx/SO2 masses come straight from the
  `emissions-unit-annual` datatype (which already had them), `fillna(0)` so gas
  units keep their legitimate ~0 SO2. Re-derived on the **current committed
  3-year v2** (2023–2025) — E1's refreshed 7-year v2 had **not** landed
  (committed v2 years = [2023, 2024, 2025]); re-run the derive when it does.
- **Estimator.** `emission_rates.measured_plant_rates(..., pollutant=…)` and
  `class_median_rates(..., pollutant=…)` select the mass column; the mode /
  trailing-window / composition-mask / gen-weighted-class-median policy is
  identical across all three pollutants. No new tunable (rule 24) — the class
  percentile is the shared `CO2_RATE_CLASS_MEDIAN_PERCENTILE`.
- **Fleet apply.** `fleet._measured_plant_rate_map_v2` returns
  `(co2, nox, so2)` triples and `apply_plant_emission_rates_v2` books all three
  at the measured tonnes/MWh-net rate; CO2/NOx set only when positive (keep the
  fuel default otherwise), SO2 always set — mirroring the legacy
  `apply_plant_emission_rates`. Merit order unaffected (the LP objective already
  carried `nox_rate`; SO2 price defaults to 0). The R7 `plant_financials` NOx
  $/MWh unit test still passes (the 2204× financials bug stays fixed).
- **Scoring.** `scripts/score_backcast_shape_emissions.py` scores model-vs-CAMPD
  NOx and SO2 masses beside CO2 (secondary/reporting gates, never keeper gates),
  reading intensities from the v2 artifact via `config/paths` — which also fixes
  its pre-W1 stale `inputs/` paths (the script was broken before this wave). The
  SO2 coal/gas table is the sharpest independent dispatch-mix check because coal
  SO2 intensity dwarfs gas.
- **Tests.** `test_emission_rates.py`: measured NOx rate × net MWh reproduces
  CAMPD `nox_kg` on a fixture plant, NOx mode policy matches CO2, entrant NOx ==
  class median, gas SO2 == 0 / coal SO2 > 0. `test_campd.py`:
  `apply_plant_emission_rates_v2` books measured NOx/SO2 (Parish coal/gas split).
  Full `tests/` suite green except 11 failures pre-existing on `origin/main`
  (verified in a clean worktree — R2/EM-4 stale `test_tranche_hr` emission
  ordering, CAISO-bins, export fake-solve, etc.; none touched by this wave); ruff
  clean; legitimacy + audit_keepers diagnostics PASS.
- **Out of scope (unchanged from §7).** No new calibration solves; the eGRID-based
  CO2 *verdict* payload (`render_calibration_html.py` / `calibration_verdict.py`)
  is a different actual source (eGRID, not CAMPD masses) and no eGRID NOx/SO2
  payload exists — the CAMPD-mass scored comparison lives in the shape-emissions
  scorer, the natural CO2-parallel path. Dashboard columns follow from that
  scorer's output.

## 9.4 Production-wiring gap found during docs sweep (2026-07-05)

A doc/code reconciliation pass found that `emission_rates.forward_plant_co2_rate` — the
full a/b/c/d estimator described in §2.1 — is called only from `scripts/loyo_co2_rates.py`
and its tests. The production path (`fleet.py::apply_plant_emission_rates_v2` →
`emission_rates.measured_plant_rates`) implements only pieces **(a)** the gen-weighted
trailing average and **(c)** the unit-composition mask. Piece **(b)**, the envelope-gated
NN conditioning, is doubly inert in production — `CO2_RATE_CONDITIONING_ENABLED` is `False`
(per the §9 gate decision) *and* the code path that would consult it is never invoked.
Piece **(d)**, the class-distribution fallback (`class_median_rates`), has no production
caller at all: CEMS-uncovered plants still fall back to the generic
`get_emission_rate(fuel, base_hr)` heat-rate default (the pre-plan mechanism), and new
entrants still take the static per-vintage `constants.CO2_RATES[tech][bin]` table — plan
§5 R2's claim that "entrant/uncovered class defaults [come] from CAMPD class distributions"
is accurate for the *design* but not yet for the *shipped* wiring. `class_median_rates` is
implemented and unit-tested (`tests/test_emission_rates.py`) and ready to wire in; doing so
is a small, well-scoped follow-on (swap the two fallback call sites in `fleet.py` /
`model/capacity.py::_make_new_generator` to consult it) that has not yet been scheduled to
a wave. No source change made here — this section documents the gap `model-methodology-spec.md`
§3.3 now also states explicitly. This holds unchanged after the §9.3 NOx/SO2-wiring wave,
which extended `measured_plant_rates`/`class_median_rates` with a `pollutant` selector but
did not add any new production caller of `class_median_rates` or `forward_plant_co2_rate`.

Separately, §9.3's own NOx/SO2 wiring is a different scope than `docs/fable-repo-audit-2026-07.md`
EM-1 (full NOx/SO2 wiring: export, verdict scoring, dashboard columns). §9.3 wires the
measured-rate artifact into the LP's marginal cost (mirroring CO2) and a standalone
diagnostic scorer (`scripts/score_backcast_shape_emissions.py`); it does not touch
`results/emissions.py` or `results/export.py` — `compute_so2` still does not exist anywhere
in `src/`, `compute_nox` still has no production caller, and `export_scenario_json` (the
payload the interactive dashboard actually reads) still exports CO2 only
(`emissions_mt`). EM-1 is updated to **PARTIALLY RESOLVED** in the audit doc to reflect
this, not closed.

## 9.5 7-year LOYO gate + window decision (2026-07-05, wave-3 E1 close-out)

The 2018–2021 intake completed (136/136 state-years; zero fetch failures) and the
v2 artifact re-derived over all six ISOs × 7 years (29,435 unit-year rows, 1,141
plants; 2018–2021 net conversion on each plant's pooled parasitic factor — the
EIA-923 gap and fallback are documented in §9.1 and the campd README). The
committed harness gained three rule-23 sweep capabilities (`--forward-chain`,
`--window-sweep`, `--gate-sweep`); the constants below were chosen ONCE from it.

**Symmetric LOYO, pooled gen-weighted wMAPE % (ERCOT, keeper sim-op; 889
plant-years / 140 plants):**

| a_gw | a_gw_w2 | a_gw_w3 | a_gw_w4 | a_gw_w5 | a_rw | a_sm | b_nn_oracle | b_nn_sim | b_gated_sim g0.1/0.25/0.5/1 | b_reg | frozen (leaky) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **2.89** | 3.35 | 3.17 | 2.96 | 2.91 | 3.09 | 3.15 | 2.84 | 2.96 | 2.93 / 2.93 / 2.89 / 2.89 | 2.94 | 2.43 |

**Forward-chained (targets predicted from strictly-prior years — the production
direction), per-target wMAPE %:**

| Target | ERCOT a_gw | ERCOT a_gw_w2 | PJM a_gw | PJM a_gw_w2 |
|---|---|---|---|---|
| 2021 | 3.22 | **3.16** | 3.07 | **2.67** |
| 2023 | 2.86 | **2.45** | 5.27 | **4.20** |
| 2024 | 2.68 | **2.24** | 4.67 | **3.78** |
| 2025 | 2.74 | **2.50** | 4.34 | **2.75** |

**Decisions (constants set once, frozen against residuals — rule 23):**

1. **Conditioning gate stays CLOSED** (`CO2_RATE_CONDITIONING_ENABLED = False`).
   The envelope-gated **sim**-conditioned estimator never beats plain `a_gw` on
   ERCOT — the only ISO whose keeper persists simulated operation — at any swept
   gate (2.89–2.93 vs 2.89). PJM's 0.03 pp gated edge (3.48 vs 3.51) is
   **oracle**-operation (no PJM bundle persists `plant_hourly_fit`, so its "sim"
   column degrades to actual-op) and is not a demonstrable sim-conditioned win.
   Per the §8/§9 escape hatch the estimator ships as the pure trailing
   gen-weighted average. The oracle ceiling (2.84 vs 2.89 symmetric) bounds what
   better sim-op persistence could recover — small.
2. **Trailing window set to 2 years** (`CO2_RATE_TRAILING_WINDOW_YEARS: 0 → 2`).
   This is the §2.2-mandated 7-year re-examination. In the forward-chained
   direction — the only direction whose "trailing" semantics match production
   use — w2 wins **8/8** per-target wMAPE comparisons across ERCOT+PJM (pooled
   ERCOT 2.59 vs 2.88; PJM 3.35 vs 4.34), monotone in window length
   (w2<w3<w4<w5<all), and improves fleet-tons bias on 7/8 targets (e.g. PJM 2025
   1.21 % vs 2.07 %): measured plant rates drift with age/retrofits, so recent
   years are more predictive. The symmetric LOYO prefers all-years only because
   a "trailing" window for an early target selects the years *furthest* from it
   — a backward-prediction artifact, not evidence against the window.
3. `CO2_RATE_ENVELOPE_GATE_L1` stays 0.5 (documented sweep value; inert while
   the gate is closed). The 2018–2021 history remains fully load-bearing for the
   drift measurement, the class-median fallback distributions, the NOx/SO2
   rates, and any future gate re-examination — the w2 base simply weights the
   most recent two years.

**PJM sim-op caveat (honest limitation):** no PJM calibration bundle on disk
persists `plant_hourly_fit.parquet`, so PJM contributed history-based and
oracle-op evidence only; the sim-conditioning verdict rests on ERCOT. If a
future PJM keeper persists sim-op, the gate re-examination may be re-run — as a
CAMPD/bundle *data* update under rule 23, never against a keeper's CO2 fit.

## 9.6 `use_plant_emission_rates_v2` flip decision memo (2026-07-06, Lane L-8, G-39)

**Gap.** `scenarios.py:389` still defaults `use_plant_emission_rates_v2=False`
although its own stated precondition — the 7-year CAMPD history intake, the
LOYO gate/window sweep, and the all-six-ISO v2 artifact re-derive — landed in
§9.5 (2026-07-05). This is a decision memo only: no flag flip, no keeper
artifact, no solve happened in this pass (rule 12/16 scope; owner decides).

### What flipping actually changes

The mode-aware source (§2.1) swaps from the legacy artifact
(`plant_emission_rates.parquet`: TX-only, 131 plants, a stale two-year pool,
zero coverage for CAISO/PJM/MISO/NYISO/NEISO — §1.2) to the v2
per-(iso, plant, unit, year) artifact (all six ISOs, 2018–2021 + 2023–2025
history, gen-weighted **2-year** trailing base, conditioning gate **closed**,
unit-composition mask). Concretely, per ISO:

- **ERCOT** — already has real plant rates today (v1). The delta is narrow:
  the unit-composition mask dissolves the W A Parish `mixed`-fuel exclusion
  (+4.6–6.3% of keeper thermal GWh gains a measured rate instead of a
  fuel-class default), the live artifact drops the 2022/2026 quarantined rows
  that sit (unused but present) in the legacy file — a rule-26-spirit
  re-arm-surface closure — and the trailing window narrows from a stale
  frozen 2-year pool to a rule-23-governed rolling 2-year window.
- **CAISO / NYISO / NEISO / PJM / MISO** — v2 is these ISOs' **first** measured
  plant-specific CO2 rate in backcast; today they fall back to the generic
  `heat_rate × FUEL_CO2_FACTOR` default for every plant. This is a real
  accuracy gain (measured beats estimated, per rule 10) with no forward-basis
  cost (rule 13 already certifies the estimator; §9.5's LOYO holds it to
  ~2–3% wMAPE against held-in years).

### The actual re-gate cost: dispatch-inert for 3 of 6 keepers

`emission_rate_co2` enters the LP objective **only** through
`assemble_mc`'s `emission_rate × carbon_price` term. In the calibration
harness, `_calibration_config` sets the **federal** `carbon_price=0.0` and
falls through to `resolve_carbon_price`'s state-program lookup
(scenarios.py / `_calibration_config` docstring). That lookup returns:

| ISO | Backcast state carbon price | v2 flip touches the LP? |
|---|---|---|
| ERCOT | $0 (no program) | **No** — reporting-only |
| PJM | $0 (no program) | **No** — reporting-only |
| MISO | $0 (no program) | **No** — reporting-only |
| CAISO | measured CARB ($28–35/t) | **Yes** — merit order can shift |
| NYISO | measured RGGI ($13–22/t) | **Yes** — merit order can shift |
| NEISO | measured RGGI ($15–24/t) | **Yes** — merit order can shift |

`nox_price` is `0.0` everywhere by default (no keeper enables a NOx cost), so
the NOx/SO2 columns v2 also carries are reporting-only across all six ISOs
regardless of carbon pricing.

This is **not a new finding invented for this memo** — it is exactly the
mechanism the 2026-07-05 R2 physical-heat-rate re-basis re-gate
(`docs/handoffs/co2-keeper-regate-2026-07-05.md`) already measured and
banked: "Carbon-zero ISOs (ERCOT/PJM/MISO): `emission_rate_co2` never enters
`mc`... Re-score = provable no-op," while CAISO/NYISO/NEISO were re-solved via
`scripts/replay_keeper.py` and registered as **PROBEs** (`...-co2re-probe`),
never as keeper swaps, pending the owner's deliberate re-gate. The v2 flip is
the same shape of change and should follow the same procedure:

1. **ERCOT / PJM / MISO — cheap, no solve.** Re-score each keeper's already-
   persisted per-plant generation through the v2 rate map (no LP re-solve,
   since dispatch is provably unaffected) and register the result as a PROBE
   (rule 15) so the improved CO2 coverage is visible on the dashboard without
   waiting on anything else. This can happen independently and immediately —
   it carries zero risk to any committed dispatch/price number.
2. **CAISO / NYISO / NEISO — a real re-solve, SH effort.** A byte-faithful
   `replay_keeper.py` re-solve (all scored years, 2023–2025) per ISO, ≤2
   concurrent per-plant multi-zone invocations (rule 12), registered first as
   a PROBE to measure the actual CO2/price/generation delta before any keeper
   swap decision — exactly the R2 template. All three of these keepers are
   *already* flagged STALE-VS-HEAD or mid-re-gate for unrelated reasons
   (CAISO: G-11 undiagnosed drift; NYISO: nyiso-41 stale-vs-HEAD pending the
   #1344 peaker-scarcity structure; NEISO: verified HEAD-reproducible per the
   2026-07-06 checklist entry above but still subject to its own C7/winter-fuel
   work).

### Recommended sequencing: ride along, don't force a wave

**Do not spend a standalone SH re-gate wave on this flag alone.** Every
carbon-priced keeper that would need a real re-solve is already scheduled for
(or blocked pending) its own HEAD re-gate for unrelated structural reasons
(§ above; see also `docs/handoffs/co2-keeper-regate-2026-07-05.md`'s running
per-ISO log and gap-register G-11/G-13/G-15/G-16). Folding
`use_plant_emission_rates_v2=True` into whichever re-solve each of those waves
already performs:

- amortizes the one unavoidable SH cost (a keeper re-solve) across two
  improvements instead of paying it twice;
- keeps rule 21's ablation-twin discipline coherent — a new keeper's
  zero-forcing ablation twin should already reflect whatever rate basis the
  keeper itself uses, so bundling avoids a twin re-solve of its own;
- matches the precedent the R2 physical-HR change already set (folded into
  the same re-gate wave rather than solved as an isolated diff).

**Concrete recommendation:**

1. Land the two cheap ERCOT/PJM/MISO PROBE re-scores now (no gate, no
   dependency on anything else) — pure dashboard-truthfulness upside.
2. Do **not** flip the default globally today. Instead, the *next* session
   that re-gates CAISO, NYISO, or NEISO (for whatever structural reason
   triggers it) should include `use_plant_emission_rates_v2=True` in that
   run's `run_config.json` and evaluate the combined delta — never re-solve
   the same ISO twice to isolate the two changes; an ablation-style
   `emission_rate_co2 = get_emission_rate(fuel, tr_hr)` (v2-off) twin re-solve
   during that same session isolates the flip's own contribution if the owner
   wants the attribution split, mirroring the R2 doc's `ablation − resolve`
   technique.
3. Once all three carbon-priced ISOs have re-gated under v2 at least once
   (whether as a promoted keeper or a still-STALE probe), flip the
   `scenarios.py:389` default to `True` and update its comment (the current
   comment — "Default OFF keeps the legacy pooled-artifact path until the
   7-year history lands" — is now stale per G-57's stale-comment finding;
   ERCOT/PJM/MISO have already re-scored clean by that point, so a global
   flip is then a no-op everywhere except a config it was already true for).
   This ordering means the flag flips only after every ISO it can actually
   move has been evaluated at least once — never a blind global default
   change with three ISOs unevaluated.

### W10 retrofit-channel activation conditions (explicit, per task scope)

The forward emission-control retrofit channel
(`docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md`) is
**triple-gated** and this memo's v2 decision does not change that gating:

```
control_retrofit_forward == True   AND   use_plant_emission_rates_v2 == True   AND   mode == "forecast"
```

Flipping `use_plant_emission_rates_v2` (gate 2 of 3) removes only one of the
three gates. `control_retrofit_forward` (gate 1) is its own independent
`ScenarioConfig` field, default `False`, and **stays off** regardless of the
v2 decision above. The reason is upstream of the v2 question: the retrofit
channel's default control-type map
(`constants.CONTROL_RETROFIT_TYPE_MAP`) is **NOx/SO2 only** (SCR/SNCR/wet
and dry FGD/DSI — CO2/carbon-capture is deliberately excluded, owned instead
by the CCS retrofit screen per rule 15) — but the fleet forecast path today
writes only a forecast **CO2** rate map end-to-end
(`apply_plant_emission_rates_v2` sets `emission_rate_co2` only; §9.4's
production-wiring-gap note is explicit that `class_median_rates` and the
full a/b/c/d estimator have no NOx/SO2 production caller yet). Turning
`control_retrofit_forward` on today would step a rate map
(`emission_rate_nox`/`emission_rate_so2`) that the fleet builder does not yet
forecast-populate from v2 at all — the override would have nothing live to
multiply against in the production path. **Recommendation: leave
`control_retrofit_forward` off until the E2 NOx/SO2 forward-rate wave lands**
(the wave that gives `apply_plant_emission_rates_v2` a forecast NOx/SO2 output
symmetric with its CO2 one); at that point the retrofit channel's override
function and EIA-860 loader are already built and unit-tested
(`tests/test_emission_rates.py::TestControlRetrofitForward`,
`TestLoadAnnouncedControls`) and E2 only needs to wire the existing
`apply_control_retrofits(rates_nox, controls, year, "nox")` /
`(..., "so2")` calls into the same seam CO2 already uses — no new mechanism.
This is unconditional on the v2 flip decision above: even in a world where
`use_plant_emission_rates_v2` is flipped on for all six ISOs tomorrow, W10
stays inert until E2 ships.

## 8. Implementation prompt

```
Implement the CO2-first emissions plan in docs/handoffs/emissions-co2-rate-plan-2026-07.md
(read it first, plus CLAUDE.md rules 1, 13, 14, 22 and docs/fable-repo-audit-2026-07.md §A).
CO2 accuracy is the objective; NOx/SO2 are secondary. Work on a feature branch; do not launch
any multi-year calibration solves; 2022 and H1-2026 are under FULL quarantine — no reads, no
fetches, no rows in any derived artifact.

Deliverables, in order:

1. INTAKE (plan §4). Fetch CAMPD hourly unit-level extracts for 2018-2021 for all 34 states
   already covered 2023-2025, using scripts/fetch_campd_unit_level.py unchanged (completed-year
   per-state bulk files; set EPA_API_KEY). Land data/raw/campd-unit-level/<ST>_<YEAR>.parquet;
   push via mcp__github__push_files in per-year batches (never retry a 413 git push). Add a
   quarantine guard to the fetcher: refuse --year 2022/2026 unless --holdout-intake <ISO> is
   passed AND frontend/data/backcast/calibration-complete.json carries that ISO's marker.
2. DATATYPE (data-intake skill recipe, all 8 steps). New curated datatype emissions-unit-annual:
   schema data/dictionary/schema/emissions-unit-annual.schema.yaml, key [plant_id, unit_id,
   year], columns per plan §4.3 including op_hours and starts (gross_mw > 1 MW off->on
   transitions, campd._startup_factors convention) and co2_source backfill provenance.
   scripts/curate_emissions_unit_annual.py reads only data/raw/campd-unit-level (facility-grain
   states -> unit_id="ALL"), hard-skips 2022/2026 files, writes via clean_io.write_clean,
   registers in regenerate_clean.py, tmp-CLEAN_DIR test with a tiny fixture.
3. RATE ARTIFACT + ESTIMATOR (plan §2). Re-derive per-plant rates for ALL SIX ISOs from the
   annual datatype into a v2 artifact keyed (iso, plant_id, unit_id, year) with per-year rows
   only (no baked pooled row; parasitic net conversion as today; extend parasitic factors to
   2018-2021 using EIA-923 those years). New module src/market_sim/data/emission_rates.py:
   forward_plant_co2_rate(history, sim_op, fleet_units) implementing (a) gen-weighted trailing
   average over available history, (b) envelope-gated nearest-neighbor conditioning on
   simulated operation (normalized annual gen + starts + CF-band L1; condition ONLY when sim
   operation falls outside the plant's historical envelope), (c) unit-composition mask (rate
   aggregated over only units present in the target-year fleet — this replaces the mixed-plant
   exclusion; W A Parish 3470 must gain separate coal/gas bin rates), (d) class-distribution
   fallback (gen-weighted class median) for uncovered plants and new entrants. Mode policy:
   backcast years consume the target year's measured rate; forecast years consume the
   estimator; wire through use_plant_emission_rates / apply_plant_emission_rates
   (fleet.py:4547-4623) with the merit-order rate = base estimator and the conditioned
   refinement applied post-solve for reporting (no fixed-point iteration). Persist model_starts
   and model_op_hours into plant_hourly_fit.parquet via run-length analysis of the in-memory
   dispatch (vectorized, no hour loops).
4. VALIDATION HARNESS. Commit scripts/loyo_co2_rates.py (generalized from the plan §3 method:
   estimators a_gw/a_sm/a_rw/b_nn_oracle/b_nn_sim/b_reg + frozen baseline, gen-weighted rate
   wMAPE and fleet tons bias, per class), reading history 2018-2021+2023-2025 and any keeper
   bundle's plant_hourly_fit/plant_cf_bands for simulated operation. Re-run it with the full
   7-year history for ERCOT and at least PJM; record results in the doc; the envelope-gate
   threshold and trailing-window length are chosen ONCE from this harness and cited as
   constants (rule 23 — they re-derive only when source data updates). Keep the estimator
   frozen against backcast residuals; a keeper's CO2 fit never tunes it.
5. FIXES R2, R3, R7 (plan §5). R2: emissions at physical heat rate, offers at bid heat rate —
   change fleet.py:6298 (and the legacy offer_curves.py band path + capacity.py entrant
   construction) so emission_rate_co2 never embeds a tranche pricing multiplier; entrant and
   uncovered-plant rates come from the CAMPD class distributions of step 3. Add the R3
   gross/net assertion test. R7: fix the NOx unit contract (fleet.py writes tonnes/MWh,
   plant_financials.py:71-72,376 consumes lb/MWh — pick tonnes/MWh canonical, convert at the
   plant_financials boundary, rename the field, unit test). Full NOx/SO2 wiring is OUT OF
   SCOPE this wave. R4 (carbon-price forward trajectory) and R5 (CHP measured-rate
   consistency + BTM share) follow if time permits, in that order; R6 (startup CO2 reporting
   adder, default-off) only after model_starts persist.
6. GOVERNANCE. Update CLAUDE.md L21 exactly per plan §6 wording. Strip the 2022/2026 rows from
   the committed plant_emission_rates artifact when re-deriving (v2 must not contain them).
   Every new tunable (envelope threshold, window length, class-median percentile) appears in
   ScenarioConfig/constants.py with citations (rule 24). Add tests per plan §5 table. Run the
   full test suite and ruff. /sync-docs at the end (methodology spec emissions section,
   binning-methodology, parameter-citations, data dictionary). Commit in small logical units;
   push data via push_files, source via git push.

Acceptance: LOYO harness reproduces plan §3 numbers on the 3-year history before extending;
with 7-year history, the shipped configuration (base + envelope-gated conditioning) must beat
plain a_gw on held-in LOYO or the gate stays closed (estimator ships as pure a_gw — say so in
the doc rather than forcing the conditioner). No solve year outside 2023-2025 appears in any
registered bundle; scripts/legitimacy_diagnostics.py --keepers and scripts/audit_keepers.py
must stay green.
```
