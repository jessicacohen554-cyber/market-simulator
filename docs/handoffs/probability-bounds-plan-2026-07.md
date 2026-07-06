# Probability-Bounds Program Plan — 2026-07

**What this is.** The design for giving the emissions forecast a defensible probability
band. Produced by the F-1 planning session of `docs/fable-prompt-pack-2026-07.md`;
companion prompts in `docs/handoffs/probability-bounds-prompts-2026-07.md`. **Status:**
PB-0 through PB-4 machinery has since landed (`matrix.py` scenario matrix, `uncertainty.py`
multivariate sampler, `structural_prior.py` structural-error convolution, plus `ensemble.py`'s
existing weather-year draws) — PB-5, the production ERCOT band run, has not.

**Source findings.** `docs/fable-repo-audit-2026-07.md` §J-T4 (probability machinery open:
`ensemble.py` weather-only, no LHS/copula, mass-cap unbuilt),
`docs/model-audit-2026-06.md` §4.2 + §6 items 4–5 (no MC/LHS, no correlation, n=3
percentiles have no statistical content), and
`docs/model-audit-prompt-pack-2026-06.md` PP-1.1 / PP-1.2 / PP-1.3.

**The problem in one sentence.** Today the only propagated uncertainty is the weather
year — three draws (`WEATHER_YEAR_POOL = (2023, 2024, 2025)`, `constants.py:2319`;
`ensemble.py` varies only `weather_year`) — so any "±10 %" emissions target carries no
confidence statement: gas price, load growth (including the data-center block), technology
cost, and policy path are all pinned at their "mid" selectors, and the model's own
structural error is not represented at all.

---

## 0. Design constraints (inherited, non-negotiable)

1. **LP-only runtimes, rule-12 memory discipline.** Years inside one invocation always
   solve sequentially; ~2 concurrent invocations max (per-plant multi-zone LPs use several
   GB each). Measured evidence (statmode D-7 session, 15 GB / 4-core box): ERCOT ≈ 4–5
   min/year, ~6.2 GB peak anon-RSS; MISO's per-generator-reserve keeper config exceeded
   15 GB solo. A 25-year forecast member (2026–2050, `START_YEAR`/`END_YEAR`,
   `constants.py:2309-2310`) is therefore **≈ 1.7–2.5 h of solve time** on ERCOT-class
   configs. Every sizing decision below is derived from this.
2. **Holdout quarantine (rule 22).** No solves, no scoring, no data intake for 2022 or
   H1-2026. Forecast solves start at year 2026 and are never scored against H1-2026
   actuals until an ISO's calibration-complete marker exists. The weather-year pool and
   the structural-error fit use 2023–2025 only.
3. **No off-registry knobs (rule 24), every number cited (rule 5).** Every new lever is a
   `ScenarioConfig` field or `constants.py` entry with a citation; sampler spec, seed,
   correlation matrix, and policy weights are echoed into `run_config.json` /
   `ensemble_meta.json`.
4. **No tuning to residuals (rules 1, 11, 13).** The structural-error prior *widens the
   band*; it never recenters the point forecast (a bias correction fitted to backcast
   residuals would be an answer-key channel). Distribution parameters derive from cited
   external sources (AEO cases, NYMEX implied vol, ATB ranges) or from the already-run
   statistical-mode probes — never from "what makes the band look right."
5. **Honest labels.** Three distinct claims, never conflated: a **deterministic scenario
   range** (§1), a **parametric probability band** (§2), and a **published probability
   band** (§2 ⊕ §3). Until the capacity hindcast (PP-0.3) lands, the published band is
   labelled **dispatch-conditional** (§3.4).

---

## 1. The scenario matrix (PP-1.1) — deterministic range, ship first

### 1.1 Axes and levels

All axes are existing `ScenarioConfig` levers except T (new lever) and the data-center
block (gated on PP-3.3):

| Axis | Lever | Levels | Source of levels |
|---|---|---|---|
| **G** gas price | `gas_price_path` (exists, `scenarios.py:45`) | low / mid / high | `HENRY_HUB_TRAJECTORIES` = AEO2025 High-Oil-and-Gas-Supply / Reference / Low-Oil-and-Gas-Supply (`constants.py:673`; upgrade to API-pulled AEO2026 per PP-3.2 item 2 when it lands) |
| **L** load growth | `demand_growth_path` (exists, `scenarios.py:62`) | low / mid / high | `DEMAND_GROWTH_RATES` per-ISO near/long eras — EIA STEO Jul 2025, ERCOT CDR Dec 2024, CAISO IEPR 2024, PJM Load Forecast 2024, NYISO Gold Book 2024 (`constants.py:597+`) |
| **DC** data-center block | `datacenter_load_gw` (**new**, gated on PP-3.3's flat-adder mechanism) | per-ISO 0 / mid / high GW | ISO large-load interconnection queues (ERCOT CDR large-load queue; PJM/ISO queue reports). Until PP-3.3 lands, the LOAD-HI level is the documented proxy for the DC boom — `DEMAND_GROWTH_RATES` "high" already embeds it in the near era |
| **P** policy bundle | **new named bundles** over existing fields | current / tight / rollback | See §1.2 |
| **T** technology cost | `tech_cost_path` (**new**) | low / mid / high | NREL ATB 2024 Advanced / Moderate / Conservative capex+learning multipliers on `NEW_ENTRY_COSTS` (`constants.py:1735+`); new `TECH_COST_MULTIPLIERS` constant with per-tech citations |
| **R** retirement posture | `retirement_aggressiveness` (exists, `scenarios.py:67`) | low / mid / high | existing per-fuel threshold scalers |

Weather year and hydro year are **not** matrix axes — they are robustness dimensions and
belong to the sampler (§2). Matrix cases pin the default weather year; the envelope is
labelled "at reference weather."

**Policy is a bundle, not independent axes.** Varying `carbon_price_path` and the IRA
phase-out years independently produces incoherent worlds (e.g. federal carbon price plus
early IRA repeal). Three named bundles map onto existing fields:

- **current** — `carbon_price_path="zero"`, `state_carbon_pricing=True` (CA cap-and-trade,
  RGGI as registered), IRA credits at legislated defaults
  (`ira_wind_solar_last_year=2027` etc., `scenarios.py:163-180`).
- **tight** — `carbon_price_path="mid"` (RFF mid path, `CARBON_PRICE_PATHS`,
  `constants.py:1200`), IRA horizons extended (+5 yr on each `ira_*_last_year`).
- **rollback** — `carbon_price_path="zero"`, state programs frozen at their last measured
  allowance price (no escalation), IRA sunset pulled 2 yr earlier.

The bundle is a new `ScenarioConfig` field `policy_bundle: str = "current"` that resolves
to the underlying fields at config-build time (a resolver function, not hidden state — the
resolved fields land in `run_config.json`).

### 1.2 Named cases (13, not a factorial)

The full cross is 3×3×3×3×3 = 243 cases — unaffordable and uninformative. AEO/IPM
practice is a reference plus one-at-a-time side cases plus a few coherent corners:

| Case | G | L | P | T | R |
|---|---|---|---|---|---|
| REF | mid | mid | current | mid | mid |
| GAS-LO / GAS-HI | low/high | mid | current | mid | mid |
| LOAD-LO / LOAD-HI | mid | low/high | current | mid | mid |
| POL-TIGHT / POL-ROLLBACK | mid | mid | tight/rollback | mid | mid |
| TECH-LO / TECH-HI | mid | mid | current | low/high | mid |
| RET-FAST / RET-SLOW | mid | mid | current | mid | high/low |
| CORNER-HI-EMIT | low | high | rollback | high | low |
| CORNER-LO-EMIT | high | low | tight | low | high |

CORNER-HI-EMIT is the coherent emissions ceiling (cheap gas + DC-boom load + no carbon +
expensive clean + sticky fossil); CORNER-LO-EMIT the floor. Corners bound the envelope so
the one-at-a-time cases can be read as attribution.

### 1.3 Engine and outputs

- **Reuse `SweepDefinition`** (`scenarios.py:3484`) — it is a cartesian expander today;
  extend it with a `cases: {name: {field: value}}` mapping (named-case mode, mutually
  exclusive with `sweep:`). One YAML file `configs/scenario_matrix.yaml` defines the 13
  cases. No new sweep engine (PP-1.1's explicit instruction).
- **Runner entrypoint** `market-sim matrix --config <base.yaml> --matrix
  configs/scenario_matrix.yaml --iso ERCOT --workers 2` — one invocation per case
  internally (years sequential), ≤2 cases concurrent (rule 12/16-style concurrency).
- **Output:** per-case emissions trajectory table (2026–2050) + min/max envelope, as
  `results/ensemble/<matrix_id>/matrix.parquet` and a markdown/JSON summary. Labelled
  **"deterministic scenario range — not a probability band"** in every artifact.

### 1.4 Cost

13 cases × ~2 h (ERCOT-class member) ÷ 2 concurrent ≈ **~13 h wall-clock per ISO** — an
overnight batch. Member results cache by config hash, so re-summarizing and resuming are
free. Heavier ISOs (PJM per-plant multi-zone) may need the concurrency dropped to 1 for
memory (measure first — PB-5 step 0).

---

## 2. The multivariate sampler (PP-1.2) — the parametric band

### 2.1 What is sampled vs scenario-switched

**Sampled (continuous, LHS + Gaussian copula):**

| Dim | New lever | Marginal | Source |
|---|---|---|---|
| gas price level | `gas_price_factor: float = 1.0` — multiplies the selected `gas_price_path` trajectory in every year | lognormal, one persistent shock per draw: `factor_y = exp(σ_y · z)`, single z per member | σ schedule per §2.2 |
| load growth | `demand_growth_percentile: float = 0.5` — piecewise-linear interpolation low↔mid↔high on `DEMAND_GROWTH_RATES` (both eras move together) | uniform on [0, 1] over the low↔high range (the published low/high are treated as the range bounds, not tail quantiles — assumption A-3) | EIA STEO / ISO forecast low-high spread already encoded in `DEMAND_GROWTH_RATES` |
| data-center block | `datacenter_load_gw` (gated on PP-3.3) | triangular(min = signed-agreement queue, mode = ISO forecast, max = total active queue) | ISO large-load queue reports; per-ISO constants with citations |
| tech cost | `tech_cost_percentile: float = 0.5` — interpolates ATB Advanced↔Moderate↔Conservative multipliers | uniform on [0, 1] | NREL ATB 2024 core-metric spread |

**Sampled (discrete, stratified LHS columns, probability-weighted):**

| Dim | Lever | Levels & default weights | Note |
|---|---|---|---|
| weather year | `weather_year` (exists) | uniform over `WEATHER_YEAR_POOL` (2023/2024/2025) | pool is thin (n=3); 2022 joins **only** after quarantine lifts. Intaking more pre-2022 weather years is a cheap widening — separate data-intake task |
| hydro year | `hydro_year` (exists) | dry 0.25 / normal 0.5 / wet 0.25 | material for CAISO; weights from the climatology behind `HYDRO_YEAR_MULTIPLIER` — cite when set |
| policy bundle | `policy_bundle` (new, §1.2) | current 0.50 / tight 0.25 / rollback 0.25 | **weights are a disclosed judgment input**, client-adjustable in the spec file, never hardcoded |

**Held fixed in sampler v1:** `retirement_aggressiveness` stays "mid". PP-1.2 lists it,
but it is a *model-structure* dial, not an input with a source-justified distribution —
sampling it would double-count with the structural-error term (§3), which already absorbs
fleet-evolution error. It remains a matrix axis (§1) where it is honestly a scenario.
Revisit after PP-0.3 measures the capacity layer's actual skill.

### 2.2 The gas marginal — σ schedule with two cited anchors

AEO cases nearly converge in the front years (2026 low/mid/high = $2.70/$3.40/$3.60,
`constants.py:673+`) while real near-term uncertainty is large; conversely options
markets say nothing about 2050. So σ_y is anchored at both ends:

- **Front (2026–2028):** σ from NYMEX Henry Hub options implied volatility — use EIA
  STEO's published Henry Hub confidence intervals, which EIA derives from NYMEX futures
  options implied vol (EIA STEO, "Market Prices and Uncertainty Report" methodology).
  Store the derived σ with the STEO vintage cited.
- **Back (2050):** treat the AEO low/high cases as the P10/P90 of the 2050 marginal
  (assumption A-1, disclosed): σ_2050 ≈ ln(8.70/4.80)/1.2816 ≈ 0.46 upside,
  ln(4.80/3.05)/1.2816 ≈ 0.35 downside — a two-piece lognormal (or single σ ≈ 0.41 with
  the asymmetry documented; decide in implementation with the simpler option preferred).
- **Between:** linear interpolation of σ_y; and σ_y is floored at the AEO-case-implied
  spread so the band never narrows below the scenario range.

One z per draw = a **perfectly persistent path shock** (no mean reversion, no
year-to-year wiggles). That is deliberate: annual-emissions bands are driven by the
sustained price level, not month-scale noise, and a persistent shock is the conservative
(widest) choice for trajectory quantiles. Disclosed as assumption A-7.

### 2.3 Correlation structure — Gaussian copula, rank-specified

Correlations are specified as Spearman rank correlations in an explicit, documented
matrix in the spec file, converted to Pearson for the Gaussian copula via
r_P = 2·sin(π·ρ_S/6):

| Pair | ρ_S | Evidence / rationale |
|---|---|---|
| gas ↔ load | **+0.3** (sensitivity runs at 0 and +0.6) | Demand-side coupling: incremental load (data centers) is served substantially by gas-fired generation, raising gas burn and price — the mechanism EIA's STEO 2025 data-center narrative describes, and the direction AEO2025's own cross-case structure encodes (the High Economic Growth case carries both higher electricity demand and a higher Henry Hub path than Reference; High/Low Oil-and-Gas Supply move price with demand near-unchanged). The +0.3 magnitude is **structured judgment anchored to that AEO cross-case ordering, not an estimated statistic** — historical annual price-vs-load correlation is confounded by the shale supply shock and unusable as-is. Disclosed as assumption A-2 and sensitivity-swept. |
| gas ↔ weather-year | 0 (omitted) | Real short-run coupling exists (freeze-offs — Uri), but the model's forecast fuel input is an annual trajectory; within-year gas-weather co-movement is not representable without sub-annual forward gas machinery. **Disclosed limitation** — the band understates joint cold-snap tails. Backcast-only basis machinery exists but is not a forecast methodology (CLAUDE.md forecast/backcast split). |
| load ↔ weather-year | mechanically coupled already | the weather draw sets the load *shape*; the growth dims scale it. No copula term needed. |
| tech ↔ (gas, load) | 0 | no defensible cited source for a sign; independence disclosed. |
| policy ↔ continuous dims | 0 in v1 | a policy↔load link (electrification policy raises load) is plausible but unsourced; omitted and disclosed. |

Mechanics: `scipy.stats.qmc.LatinHypercube` (scipy is in-stack; the ban is on
`scipy.optimize`) → U (n×d, stratified) → z = Φ⁻¹(U) on the continuous block → Cholesky
of the converted matrix → correlated uniforms → marginal ppfs. Discrete dims use their
own stratified columns mapped through weighted bins. Fixed default seed; seed, spec hash,
and the full matrix recorded in `ensemble_meta.json`.

### 2.4 Draw count — what is affordable

- **Default n = 64 LHS draws** (configurable 50–100, PP-1.2's floor). With LHS
  stratification and a smooth monotone response, n=64 gives materially tighter P10/P90
  estimates than 64 plain-MC draws; report a **bootstrap CI on each published quantile**
  from the member sample so the sampling noise is itself visible (this replaces any
  claim that n is "enough" — the CI shows what it is).
- **Cost:** 64 members × ~2 h (ERCOT-class, 25 years sequential) ÷ 2 concurrent ≈
  **~2.7 days wall-clock per ISO**. Affordable as a scheduled batch; per-member
  config-hash caching makes interrupted batches resumable and re-summarizing free.
  Cross-year warm-starting (`docs/cross-year-warmstart.md`) is the accelerator to reach
  n=100 if needed.
- **Per-ISO rollout:** ERCOT first (calibrated reference, cheapest). MISO's
  per-generator-reserve config cannot run 2-concurrent on a 15 GB box (D-7 evidence:
  >15 GB solo) — MISO ensembles either use the pooled-reserve forecast config or run at
  concurrency 1; decide when MISO's turn comes.
- The quantile estimator is numpy's default linear interpolation (Hyndman–Fan type 7),
  documented in the methodology note with n attached to every published quantile —
  answering the audit's "drop ddof=0 / 3-point percentiles" item.

### 2.5 Where it hooks into `ensemble.py`

Keep the module's proven skeleton (parallel `ProcessPoolExecutor` + per-member
config-hash caching + `_summarize_year` reuse); generalize the member axis:

1. **New module `src/market_sim/uncertainty.py`** — `UncertaintySpec` (marginals,
   Spearman matrix, discrete weights, n, seed) loaded from a committed YAML spec;
   `sample_draws(spec) -> list[DrawRecord]` (pure sampling, no I/O — unit-testable);
   `draw_to_config(base_config, draw) -> ScenarioConfig`.
2. **`ensemble.py` generalizes** `weather_ensemble_configs` → `sample_ensemble_configs
   (base, spec)` returning `dict[draw_id, ScenarioConfig]`; `run_weather_ensemble` →
   `run_ensemble(configs, workers)` with the weather-only path kept as a thin wrapper
   (backwards-compatible CLI). Member identity moves from weather-year int to a draw-id
   string; cache keys already include every sampled field via the config hash.
3. **Worker default changes from `cpu_count - 1` to `min(2, cpu_count - 1)`**
   (`ensemble.py:123`) — the current default is a latent OOM under rule 12 the moment
   members are forecast solves on per-plant ISOs; the weather ensemble only survived it
   because n=3.
4. **New `ScenarioConfig` fields** (all rule-24 registered, default-neutral so every
   existing config is unchanged): `gas_price_factor=1.0`, `demand_growth_percentile=0.5`,
   `tech_cost_path="mid"`, `tech_cost_percentile=0.5`, `policy_bundle="current"`,
   (`datacenter_load_gw=0.0` with PP-3.3). Guard: `gas_price_factor` must be ignored (or
   asserted =1.0) in backcast mode — it is a forecast-uncertainty lever, never a backcast
   tuning channel.
5. **CLI:** `market-sim ensemble --config base.yaml --sampler configs/uncertainty_ercot.yaml
   --draws 64 --seed 7 --workers 2 --out-dir results/ensemble/ercot_v1` (the existing
   `--weather-years` path stays).

---

## 3. The structural-error prior (PP-1.3) — from parametric band to published band

### 3.1 Why the decomposition is clean

The **D-7 statistical-mode probes already exist for all six ISOs**
(`docs/statistical-mode-results-2026-07.md`; bundles
`results/calibration/{ercot32,caiso,pjm,nyiso,neiso,miso}*_statmode_2026-07`; dashboard
ids `2026-07-04-statmode-d7-probe-ercot32`, `2026-07-03-*-statmode-d-7`). Statistical
mode turns off every measured overlay but **keeps realized annual gas price, load, and
weather** — so its emissions error measures exactly *model error given true inputs*.
That is precisely the term that convolves with §2's *input* uncertainty without
double-counting: the parametric layer owns "we don't know the inputs," the structural
layer owns "given the inputs, the model is wrong by this much."

### 3.2 Fitting the prior

Let ε_{i,y} = ln(emissions_model / emissions_actual) for ISO i, backcast year
y ∈ {2023, 2024, 2025}, from the **statmode** bundles (not the overlay-on keepers —
keeper error is overlay-carried and would understate; D-7 magnitudes, e.g. PJM
+22.6–26.6 %, MISO +10.5–21.6 %, CAISO +13–17 %, ERCOT ±2.4 %, NYISO −2.2 %, are the
honest dispatch-skill prior).

- **Decompose per ISO:** bias b_i = mean_y(ε_{i,y}) and noise s_i = sd_y(ε_{i,y}).
  D-7 shows bias is persistent (same sign across years within an ISO), so b_i is real
  signal, not noise.
- **Small-sample honesty:** n=3 years per ISO. Pool the noise scale across ISOs
  (s² = pooled within-ISO variance) and carry parameter uncertainty explicitly:
  ε_i ~ Student-t(ν = 2) location b_i, scale √(s² · (1 + 1/3)) — the fat tails and the
  +1/3 term encode that both moments are estimated from three points. (Exact form
  finalized in implementation; the requirement is that the prior must be *wider* than
  the plug-in normal, never narrower.)
- **No recentering.** The point forecast (P50 of the parametric layer) is **not**
  bias-corrected — subtracting b_i would be feeding a measured outcome back in (rule 13's
  forbidden side). Instead ε enters with its non-zero mean, so the published band is
  *asymmetric around the model path* and covers the known bias. A client reading the band
  sees where the model probably sits relative to truth without the model pretending the
  bias away.

### 3.3 Convolution

Monte Carlo product, in log space, per ISO per forecast year: for each of the n
parametric draws attach K = 25 independent ε draws → an n×K sample of
`emissions · exp(ε)`; published quantiles (P5/P10/P25/P50/P75/P90/P95) come from the
pooled n×K sample. Simple, estimator-documented, no closed-form assumptions. Both layers
are stored (§4), so the parametric-only band remains inspectable next to the published
band.

### 3.4 What the prior does NOT yet cover — stated honestly

1. **Capacity-path error.** ε is measured on one-year backcasts with a frozen fleet; the
   forward emissions trajectory also depends on the fleet-evolution layer, whose skill is
   **unmeasured** (PP-0.3 capacity hindcast unbuilt — audit gate 3; J-register T1). The
   code carries a horizon-widening term λ(h) (variance multiplier growing with years-out)
   that is **set to 0 and flagged UNMEASURED** until PP-0.3 produces a number. Until
   then every published artifact is labelled **"dispatch-conditional band — excludes
   fleet-path structural error."** PP-0.3 is the gate on dropping that label, matching
   the audit's gate list (items 1–3 before 4–5 are quotable).
2. **Stationarity (A-4).** 2023–2025 dispatch error is assumed representative of
   2026–2050 dispatch error for a *given* fleet/inputs. Untestable until holdouts are
   scored; the quarantined 2022/H1-2026 one-shot scoring (rule 22) will be the first
   out-of-time check of ε itself — the prior is re-fit only at that sanctioned moment.
3. **Independence of ε from the drivers (A-5).** The statmode sample is far too small to
   estimate state-dependent error (e.g. "model is worse in high-gas years"); ε is drawn
   independent of the parametric draw. Disclosed.
4. **In-sample offer curves (A-6).** Statmode keeps the keeper's offer-curve multipliers,
   which were tuned on the same 2023–2025 years — ε is therefore still *optimistic*. The
   leave-one-year-out harness (PP-0.2) is the refinement that would firm this; noted as a
   follow-on, not a blocker for v1 (the direction of the error is disclosed: the true
   band is at least as wide).
5. **Weather-gas joint tails (from §2.3).** Understated by construction; disclosed.

---

## 4. Output surface

### 4.1 Computation and storage (parquet per scenario-year preserved)

Per-member results stay exactly where they are — the existing per-scenario-year parquet
cache (rule 7); the ensemble layer only *reads* members. New per-ensemble directory
`results/ensemble/<ensemble_id>/`:

| File | Contents |
|---|---|
| `draws.parquet` | one row per draw: draw_id, every sampled input value, member cache_key, config hash |
| `metrics.parquet` | long format (draw_id, year, metric, value) — `emissions_mt` first, plus the existing `_SCALAR_METRICS` and per-fuel generation_twh from `_summarize_year` |
| `bands.parquet` | (year, metric, layer, quantile, value, n, bootstrap_lo, bootstrap_hi) with layer ∈ {scenario_envelope, parametric, parametric_plus_structural} |
| `ensemble_meta.json` | UncertaintySpec (marginals, Spearman matrix, weights), seed, n, K, structural-prior version + fit inputs (statmode bundle ids), estimator note, label (dispatch-conditional flag) |

Bands are recomputed from `metrics.parquet` + the prior by a pure function — cheap,
re-runnable, and auditable separately from the solves.

### 4.2 Display

- **Fan chart page** on the codebase site: `docs/codebase-site/forecast-bands.html`,
  reading committed payloads `frontend/data/forecast/<ensemble_id>.js` — the same
  committed-payload pattern as the backcast dashboard (deploy-workflow-owned manifests
  untouched; follow the CLAUDE.md 413 push workflow for payload commits).
- Rendered layers, visually distinct and individually toggleable: scenario-matrix
  envelope (dashed bounds), parametric P10–P90 fan, published (⊕ structural) P10–P90
  fan, P50 path, and the 13 named-case trajectories as thin reference lines.
- **Label rules enforced in the page header**, driven by `ensemble_meta.json`: "n=…
  draws"; "dispatch-conditional — excludes fleet-path error" until PP-0.3; "deterministic
  scenario range" when only the matrix layer exists. The chart never shows a band the
  metadata can't defend.
- The per-run CLI also emits a plain markdown summary table (P10/P50/P90 by year) for
  reports.

---

## 5. Runtime & memory budget (rule 12), consolidated

| Workload | Members | Est. wall-clock (ERCOT-class) | Notes |
|---|---|---|---|
| Scenario matrix (§1) | 13 | ~13 h @ 2 concurrent | overnight; per-case cache |
| Sampler v1 (§2) | 64 | ~2.7 d @ 2 concurrent | resumable; warm-start is the n=100 enabler |
| Structural fit + convolution (§3) | 0 solves | minutes | pure post-processing of existing statmode bundles + `metrics.parquet` |

All estimates extrapolate the D-7 measured 4–5 min/year; **PB-5 step 0 measures a real
single forecast member first** and re-sizes before any batch is launched. Concurrency
never exceeds 2 (1 for MISO-pergen / PJM if measurement says so); years within a member
always sequential; the ensemble worker default is capped accordingly (§2.5 item 3).

---

## 6. Sequencing and dependencies

```
PB-1 levers (new ScenarioConfig fields + constants)   [no deps]
PB-0 scenario matrix (needs policy bundle + tech lever from PB-1)
PB-2 sampler core (needs PB-1)
PB-3 structural prior + convolution (needs PB-2 output schema; statmode bundles exist)
PB-4 output surface (needs PB-2/PB-3 schemas)
PB-5 first production ERCOT band run (needs PB-0..PB-4)
External gates:
  PP-0.3 capacity hindcast  → removes the "dispatch-conditional" label (λ(h) measured)
  PP-3.3 load-shape adders  → activates the datacenter_load_gw dimension
  PP-0.2 LOYO harness       → firms the structural prior (A-6)
  PP-3.2(2) AEO2026 API pull → replaces chart-eyeballed gas anchors under the same lever
  W0-P1 CO2-rate model      → improves the *level* the band wraps; independent of the machinery
```

The matrix (PB-0) ships value first — an AEO-comparable side-case table — while the
sampler lands. Nothing here solves or scores 2022/H1-2026; nothing here tunes any
parameter against a residual.

---

## 7. Assumptions ledger (what a reviewer should attack)

| ID | Assumption | Where | Mitigation / test |
|---|---|---|---|
| A-1 | AEO low/high gas cases ≈ P10/P90 of the 2050 marginal | §2.2 | sensitivity: treat as P25/P75 (wider σ) in one sweep; disclosed either way |
| A-2 | gas↔load Spearman +0.3, judgment anchored to AEO cross-case ordering | §2.3 | mandatory sensitivity members at ρ=0 and ρ=+0.6; report band delta |
| A-3 | published ISO low/high load forecasts span the plausible range (uniform, not tails) | §2.1 | DC block (PP-3.3) explicitly extends the upper range beyond the published high |
| A-4 | dispatch error stationary 2023-25 → 2026-50 | §3.4 | one-shot holdout scoring re-fits ε at the sanctioned moment |
| A-5 | ε independent of the parametric draw | §3.4 | untestable at n=3 yr; disclosed |
| A-6 | statmode ε optimistic (in-sample offer curves) | §3.4 | PP-0.2 LOYO refinement; direction disclosed |
| A-7 | gas shock perfectly persistent (single z per draw) | §2.2 | conservative (widest) for trajectory quantiles; disclosed |
| A-8 | policy weights 0.50/0.25/0.25 are a judgment input | §2.1 | explicit spec input, client-adjustable, echoed in outputs |

---

*Produced 2026-07-04 (Fable F-1 session). Design only — no solves were run, no parameters
changed. Implementation prompts: `docs/handoffs/probability-bounds-prompts-2026-07.md`.*
