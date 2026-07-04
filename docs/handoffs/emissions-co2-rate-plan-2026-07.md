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
