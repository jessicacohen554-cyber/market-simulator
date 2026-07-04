# Probability-Bounds Implementation Prompt Pack — 2026-07

Model-assigned, paste-one-per-session implementation prompts for the design in
`docs/handoffs/probability-bounds-plan-2026-07.md`. Each is a self-contained brief for a
fresh Claude Code session. Read the plan doc first — these prompts assume its §-numbers.

**Model key** (matches `docs/fable-prompt-pack-2026-07.md`): `[OPUS]` complex
implementation/refactor; `[SONNET]` well-scoped implementation, tests, docs.

**Every session inherits** (do not repeat in-session): obey `CLAUDE.md` non-negotiables —
rule 1 (structure first, never tune to a residual), rule 5 (cite every number), rule 7
(parquet per scenario-year), rule 12 (sequential years, ≤2 concurrent invocations),
rule 13/14 (measured-data admissibility — the structural prior widens the band, never
recenters the point forecast), rule 22 (**no solves/scoring/intake for 2022 or
H1-2026**), rule 24 (no off-registry knobs — every lever in `ScenarioConfig`/`constants.py`
and echoed to `run_config.json`). LP-only (no MIP, no Pyomo/PuLP, no scipy.optimize).
Work on a feature branch, add tests, commit+push per the CLAUDE.md 413 workflow.

**Dependency order:** PB-1 → {PB-0, PB-2} → PB-3 → PB-4 → PB-5. PB-0 and PB-2 are
parallel once PB-1 lands.

---

## PB-1 `[SONNET]` — New uncertainty levers (foundation, no solves)

```
Add the ScenarioConfig fields and constants the probability-bounds machinery needs, as
plumbing only — no sampler, no matrix yet. Read docs/handoffs/probability-bounds-plan-
2026-07.md §1.1, §1.2, §2.1, §2.5 item 4 first.

Add these ScenarioConfig fields (src/market_sim/config/scenarios.py), all with
default-NEUTRAL values so every existing config and every keeper is byte-unchanged, each
with a citation comment (rule 5) and registered in the field-tier map near line 3218:
  - gas_price_factor: float = 1.0      # multiplies the selected gas_price_path trajectory
  - demand_growth_percentile: float = 0.5
  - tech_cost_path: str = "mid"        # "low"/"mid"/"high" -> ATB Advanced/Moderate/Conservative
  - tech_cost_percentile: float = 0.5
  - policy_bundle: str = "current"     # "current"/"tight"/"rollback"; resolves per §1.2

Add constants (src/market_sim/config/constants.py):
  - TECH_COST_MULTIPLIERS: per-tech capex+learning multipliers for ATB Advanced/Moderate/
    Conservative on NEW_ENTRY_COSTS (constants.py:1735+). Cite NREL ATB 2024 core-metric
    cases per tech.

Wire the resolvers (pure functions, resolved values must land in run_config.json — no
hidden state):
  - gas_price_factor multiplies the resolved HENRY_HUB trajectory in the fuel path. CRITICAL
    (rule 13): assert/force gas_price_factor == 1.0 in backcast mode — it is a forecast-only
    uncertainty lever and must never become a backcast tuning channel. Add a test that a
    backcast config with gas_price_factor != 1.0 raises.
  - tech_cost_path/percentile scales NEW_ENTRY_COSTS at config-build time.
  - policy_bundle resolves to the underlying fields (carbon_price_path, state_carbon_pricing
    freeze, ira_*_last_year offsets) per §1.2; the RESOLVED fields go into run_config.json.

demand_growth_percentile does piecewise-linear interpolation low<->mid<->high on
DEMAND_GROWTH_RATES (both eras move together); 0.0=low, 0.5=mid, 1.0=high.

Do NOT add datacenter_load_gw — it is gated on PP-3.3 (load-shape adders) and out of scope.
Tests: neutral defaults reproduce today's resolved config exactly (golden test on a keeper
config's resolved fields); each lever moves the intended quantity monotonically; backcast
gas_price_factor guard. No solves.
```

---

## PB-0 `[SONNET]` — Scenario matrix (deterministic range)

```
Build the AEO/IPM-style scenario matrix from docs/handoffs/probability-bounds-plan-2026-07.md
§1. Depends on PB-1 (policy_bundle + tech_cost_path levers). Read §1.2 (the 13 named cases),
§1.3, and config/scenarios.py:3484 (SweepDefinition) first.

Extend SweepDefinition (do NOT write a new engine — PP-1.1's instruction) with a named-case
mode: a `cases: {name: {field: value}}` mapping, mutually exclusive with the existing
`sweep:` cartesian mode. Add configs/scenario_matrix.yaml with the 13 cases exactly as in
§1.2 (REF, GAS-LO/HI, LOAD-LO/HI, POL-TIGHT/ROLLBACK, TECH-LO/HI, RET-FAST/SLOW,
CORNER-HI-EMIT, CORNER-LO-EMIT).

Add a runner entrypoint `market-sim matrix --config <base.yaml> --matrix
configs/scenario_matrix.yaml --iso ERCOT --workers 2`: one invocation per case internally
(years SEQUENTIAL within a case, rule 12), <=2 cases concurrent. Members cache by config
hash (reuse the existing per-scenario-year parquet cache, rule 7).

Output results/ensemble/<matrix_id>/matrix.parquet (per-case emissions trajectory 2026-2050)
+ a min/max envelope + a markdown summary. LABEL every artifact "deterministic scenario
range - NOT a probability band" (§1.3).

Forecast mode only, start year 2026 - no 2022/H1-2026 (rule 22). Test the matrix expansion
(13 cases, correct field overrides per case) without solving. Do a 1-year 2-case smoke solve
on ERCOT to confirm the pipeline, then stop - the full 13-case batch is a PB-5 concern.
```

---

## PB-2 `[OPUS]` — Multivariate LHS + copula sampler (core machinery)

```
Build the multivariate uncertainty sampler from docs/handoffs/probability-bounds-plan-
2026-07.md §2. Depends on PB-1. Read §2.1-§2.5 and src/market_sim/ensemble.py (keep its
ProcessPoolExecutor + per-member config-hash cache + _summarize_year reuse) first.

New module src/market_sim/uncertainty.py:
  - UncertaintySpec dataclass: continuous marginals (gas lognormal sigma-schedule per §2.2,
    load uniform, tech uniform), the Spearman correlation matrix (§2.3), discrete-dim weights
    (weather/hydro/policy per §2.1), n, seed. Loaded from a committed YAML spec.
  - sample_draws(spec) -> list[DrawRecord]: PURE sampling, no I/O, fully unit-testable.
    scipy.stats.qmc.LatinHypercube (scipy is in-stack; only scipy.optimize is banned) for the
    stratified U; z=Phi^-1(U); convert Spearman->Pearson via r_P=2*sin(pi*rho_S/6); Cholesky;
    correlated uniforms -> marginal ppfs. Discrete dims: own stratified LHS columns through
    weighted bins. Record seed + full matrix + spec hash in the returned metadata.
  - draw_to_config(base_config, draw) -> ScenarioConfig via the PB-1 levers.

Gas marginal (§2.2): sigma_y anchored front (EIA STEO Henry Hub CI / NYMEX implied vol,
cite the STEO vintage) and back (AEO low/high as 2050 P10/P90, assumption A-1); linear
interpolation between; floored at the AEO-case spread so the band never narrows below the
scenario range. One z per draw = persistent path shock (A-7).

Generalize ensemble.py: weather_ensemble_configs -> sample_ensemble_configs(base, spec);
run_weather_ensemble -> run_ensemble(configs, workers) with the weather-only path kept as a
thin backwards-compatible wrapper. CHANGE the worker default from cpu_count-1 to
min(2, cpu_count-1) (ensemble.py:123) - the current default is a latent rule-12 OOM once
members are forecast solves. Member identity becomes a draw-id string.

CLI: market-sim ensemble --config base.yaml --sampler configs/uncertainty_ercot.yaml
--draws 64 --seed 7 --workers 2 --out-dir results/ensemble/ercot_v1 (keep --weather-years).
Emit draws.parquet + metrics.parquet (§4.1) - emissions_mt first, reuse _summarize_year.
Report P10/P50/P90 + a bootstrap CI per quantile + n on every metric; estimator = numpy
Hyndman-Fan type 7, documented (§2.4). Drop the ddof=0 / 3-point percentile logic.

Tests: sample_draws reproduces bit-identical draws for a fixed seed; recovered rank
correlation on n=2000 draws matches the spec matrix within tolerance; LHS stratification
(one draw per stratum per dim); backcast configs rejected. Add configs/uncertainty_ercot.yaml
as the reference spec (all §2.3 correlations + §2.1 weights, each cited). Do a small n=4
smoke solve on ERCOT to confirm end-to-end, then stop.
```

---

## PB-3 `[OPUS]` — Structural-error prior + convolution (published band)

```
Fold the model's structural error into the published band per docs/handoffs/probability-
bounds-plan-2026-07.md §3. Depends on PB-2's metrics.parquet schema. The input data already
exists: the D-7 statistical-mode bundles for all six ISOs (results/calibration/
{ercot32,caiso,pjm,nyiso,neiso,miso}*_statmode_2026-07; see docs/statistical-mode-
results-2026-07.md). Read §3.1-§3.4 first.

New module src/market_sim/structural_prior.py:
  - fit_prior(statmode_bundles, actuals) -> StructuralPrior: for each ISO, eps_{i,y} =
    ln(emissions_model / emissions_actual) over y in {2023,2024,2025} from the STATMODE
    bundles (NOT the overlay-on keepers - keeper error is overlay-carried and understates,
    §3.2). Per-ISO bias b_i = mean_y(eps), noise s_i = sd_y(eps). Pool noise across ISOs;
    carry n=3 parameter uncertainty as Student-t(nu=2) location b_i scale
    sqrt(s_pooled^2 * (1+1/3)) - the prior MUST be wider than the plug-in normal, never
    narrower. Store the fit inputs (bundle ids, per-ISO/per-year eps) in the prior artifact.
  - CRITICAL (rule 13, §3.2): do NOT recenter the point forecast. eps enters with its
    non-zero mean so the published band is asymmetric around the model path and covers the
    known bias. Subtracting b_i would be an answer-key channel - a test must assert the P50
    point path is NOT shifted by the prior.
  - convolve(metrics, prior, K=25) -> bands: MC product in log space, n parametric draws x K
    structural draws of emissions*exp(eps); published quantiles P5/P10/P25/P50/P75/P90/P95
    from the pooled n*K sample (§3.3).
  - A horizon-widening term lambda(h) (variance multiplier growing with years-out) set to 0
    and flagged UNMEASURED until PP-0.3 (capacity hindcast) supplies a number. Every band
    carries a "dispatch-conditional - excludes fleet-path structural error" label until then
    (§3.4 item 1).

Write bands.parquet with layer in {scenario_envelope, parametric, parametric_plus_
structural} (§4.1) so the parametric-only band stays inspectable next to the published one.
Record the prior version + fit inputs + estimator note + dispatch-conditional flag in
ensemble_meta.json.

Document every assumption A-1..A-8 (§7) and the §3.4 limitations in a methodology note
docs/probabilistic-emissions-methodology.md. State honestly: this is dispatch-conditional
until PP-0.3; statmode eps is still in-sample-optimistic (A-6) pending PP-0.2. No solves -
this is post-processing of existing bundles. Tests: prior wider than plug-in normal; P50
not shifted; convolution recovers input spread when eps=0; asymmetry when b_i != 0.
```

---

## PB-4 `[SONNET]` — Output surface (fan chart + storage)

```
Build the forecast-band output surface from docs/handoffs/probability-bounds-plan-2026-07.md
§4. Depends on PB-2/PB-3 schemas. Read §4.1, §4.2 first.

Storage (§4.1): finalize results/ensemble/<ensemble_id>/ with draws.parquet, metrics.parquet,
bands.parquet, ensemble_meta.json exactly per the §4.1 table. Bands recompute from
metrics.parquet + the prior via a pure function (cheap, re-runnable, separately auditable).

Display (§4.2): a fan-chart page docs/codebase-site/forecast-bands.html reading committed
payloads frontend/data/forecast/<ensemble_id>.js - SAME committed-payload pattern as the
backcast dashboard (deploy-workflow-owned manifests untouched; follow the CLAUDE.md 413 push
workflow for payload commits). Render toggleable layers: scenario-matrix envelope (dashed),
parametric P10-P90 fan, published (+structural) P10-P90 fan, P50 path, and the 13 named-case
lines as thin references.

ENFORCE the label rules in the page header from ensemble_meta.json (§4.2): show "n=... draws";
show "dispatch-conditional - excludes fleet-path error" whenever lambda(h)==0/UNMEASURED; show
"deterministic scenario range" when only the matrix layer exists. The chart must never display
a band the metadata cannot defend. Also emit a plain markdown P10/P50/P90-by-year table for
reports. Match the DESIGN_SYSTEM.md styling and pass the accessibility-audit skill (light+dark).
No solves.
```

---

## PB-5 `[OPUS]` — First production ERCOT band run + registration

```
Produce and publish the first real probability-bounded emissions forecast (ERCOT, the
calibrated reference). Depends on PB-0..PB-4 all landed. Read the whole plan doc, esp. §5
(runtime budget) and §6 (sequencing).

STEP 0 (mandatory, rule 12): measure ONE real 25-year (2026-2050) ERCOT forecast member
end-to-end - wall-clock/year and peak anon-RSS - and re-size the batch before launching
anything. The §5 estimates extrapolate the D-7 4-5 min/year; confirm on a real forecast
member (fleet evolution runs, unlike a backcast). If memory forces concurrency 1, say so.

Then, forecast mode only (start 2026, NEVER 2022/H1-2026, rule 22):
  1. Run the 13-case scenario matrix (PB-0) -> deterministic envelope.
  2. Run the n=64 sampler (PB-2) with configs/uncertainty_ercot.yaml -> parametric band.
     Batch is resumable via per-member config-hash cache; use cross-year warm-start
     (docs/cross-year-warmstart.md) if it helps reach the count.
  3. Run the mandatory sensitivity members at gas-load rho = 0 and +0.6 (assumption A-2)
     and report the band delta.
  4. Fold the structural prior (PB-3) -> published dispatch-conditional band.
  5. Publish via PB-4: forecast-bands.html + frontend/data/forecast/ercot_v1.js, committed
     per the CLAUDE.md 413 workflow. Lead with the headline P10/P50/P90 2030 and 2050
     emissions numbers and the "dispatch-conditional" caveat.

Deliverable is the committed band artifacts + payload + a short report
(docs/probability-bounds-ercot-2026-07.md) stating the numbers, the assumptions ledger
result (esp. the rho sensitivity), and what the dispatch-conditional label means. Do NOT
tune anything to make the band look a particular width (rule 1). If the band is wider than
the "+/-10%" target, that IS the finding - report it honestly. Other ISOs follow once ERCOT
is validated; MISO needs the concurrency-1 / pooled-reserve decision from §2.4.
```

---

## Cross-cutting notes for every implementer

- **The band widens; the point never moves.** Any code path where the structural prior or a
  correlation choice shifts the P50 emissions path is a rule-13 bug. The P50 is the model's
  forecast; uncertainty machinery only expresses how sure we are of it.
- **Every published band self-describes its coverage.** `ensemble_meta.json` is the source of
  truth for labels; the chart and the markdown reader both derive their caveats from it. A
  band whose metadata says `lambda(h)==0` is dispatch-conditional, full stop.
- **Nothing here touches 2022 or H1-2026** - not the weather pool, not the structural fit,
  not any solve. The structural prior uses 2023-2025 statmode error only; the quarantined
  years are scored exactly once at the sanctioned moment (rule 22), which is when the prior
  gets its first out-of-time re-fit.
- **Seeds, specs, and matrices are recorded.** Reproducibility is a rule-24 requirement, not
  a nicety: seed, UncertaintySpec hash, correlation matrix, and structural-prior version all
  land in `ensemble_meta.json` / `run_config.json`.

*Companion to `docs/handoffs/probability-bounds-plan-2026-07.md` (design). Produced
2026-07-04, Fable F-1 session.*
