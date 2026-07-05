# Probabilistic Emissions Methodology (PB-3)

**What this documents.** How the emissions forecast earns a *published* probability
band, and — just as importantly — what that band does **not** yet cover. It is the
methodology note for the structural-error prior and convolution
(`src/market_sim/structural_prior.py`), the third layer of the probability-bounds
program designed in `docs/handoffs/probability-bounds-plan-2026-07.md` (§3) and
specified in `docs/handoffs/probability-bounds-prompts-2026-07.md` (PB-3).

**Code is the source of truth.** Where this note and the module disagree, fix the
note. Every number below is a `constants.py` entry with a citation (rule 5); no
distribution parameter is tuned to make a band a particular width (rule 1).

---

## 1. Three claims, never conflated

The program produces three distinct statements about the emissions trajectory, and
each output artifact is labelled with exactly the one it can defend (plan §0 item 5):

| Layer | Claim | Owned by |
|---|---|---|
| `scenario_envelope` | **deterministic scenario range** — min/max over 13 named AEO/IPM-style cases | PB-0 (matrix) |
| `parametric` | **parametric probability band** — "we don't know the *inputs*" (gas, load, tech, weather, hydro, policy), sampled by LHS + Gaussian copula | PB-2 (sampler) |
| `parametric_plus_structural` | **published probability band** — the parametric band convolved with "given the inputs, the *model* is wrong by this much" | **PB-3 (this note)** |

The clean decomposition (plan §3.1): the parametric layer owns input uncertainty; the
structural layer owns model error *given true inputs*. The two convolve without
double-counting because the structural term is measured from the D-7
statistical-mode probes, which hold the realized inputs fixed.

---

## 2. The structural-error prior

### 2.1 Source — a measured, reproducible input

The prior is fit from the committed **D-7 statistical-mode probes** for all six ISOs
(`docs/statistical-mode-results-2026-07.md`; run ids in
`constants.STATMODE_PROBE_RUNS`). Statistical mode strips every measured backcast
overlay (historic outages, CT/reliability deployment floors, WEFOR residual relief,
per-plant monthly coal pricing) but **keeps realized annual gas price, load and
weather**. Its emissions error is therefore exactly *model error given true inputs* —
the honest dispatch-skill prior, not the overlay-carried keeper error, which would
understate it (§3.2; the keeper's overlays are what turn a hard miss into a
tolerable-looking near-miss).

The fit inputs are two committed, reproducible sources (`load_statmode_residuals`):

- **model** CO2 (system fossil, Mt): `frontend/data/backcast/runs/<statmode-id>.js`
  → `years[y].co2.model`.
- **actual** CO2 (system fossil, Mt): `frontend/data/backcast/bench/<ISO>/<y>.json.gz`
  → `bench.co2.egrid` (the same denominator the dashboard's C5a CO2 criterion scores
  against).

Both re-derive only when those probes update (rule 23), never in response to a
residual. Only 2023–2025 are read — 2022 and H1-2026 stay under full quarantine
(rule 22), and `fit_prior` **rejects** any bundle carrying a non-fit year.

### 2.2 The fit

For ISO *i*, backcast year *y* ∈ {2023, 2024, 2025}:

```
ε_{i,y} = ln(emissions_model / emissions_actual)
b_i      = mean_y(ε_{i,y})          # persistent bias — same sign across years (§3.2)
s_i      = sd_y(ε_{i,y})            # ddof=1 sample noise
```

The measured biases (fit off the committed probes) reproduce the D-7 report: PJM
≈ +0.22, MISO ≈ +0.15, CAISO ≈ +0.10 (model runs high on coal-heavy fleets), ERCOT
≈ 0, NYISO/NEISO ≈ 0.

**Small-sample honesty** (n = 3 years/ISO). The noise scale is *pooled* across ISOs
and carries the parameter uncertainty explicitly, so the prior is strictly **wider**
than the plug-in normal, never narrower:

```
s_pooled² = Σ_i (n_i − 1) s_i² / Σ_i (n_i − 1)          # pooled within-ISO variance
scale     = √( s_pooled² · (1 + 1/n) )                   # +1/n predictive inflation, n=3
ε_i ~ Student-t(ν = 2) · scale + b_i                     # fat tails (ν=2)
```

Both the ν = 2 fat tails and the (1 + 1/3) inflation make the fitted quantile
spread exceed a plug-in `N(b_i, s_pooled)` at every symmetric quantile — asserted in
`tests/test_structural_prior.py::test_prior_wider_than_plugin_normal`. Parameters:
`STRUCTURAL_PRIOR_STUDENT_T_NU`, `STRUCTURAL_PRIOR_FIT_YEARS`,
`STRUCTURAL_PRIOR_VERSION`.

### 2.3 No recentering — the band widens, the point never moves

`ε` enters the convolution with its **non-zero** mean `b_i`. It is **not** subtracted
from the point forecast: doing so would feed a measured outcome back into the forecast
(rule 13's forbidden side). Consequences, both intentional:

- The **headline point forecast stays the parametric-layer P50** — the model's own
  forecast. The structural layer is written *alongside* the parametric rows in
  `bands.parquet`, never over them, so folding the prior leaves the parametric P50
  byte-identical (asserted: `test_p50_point_path_not_shifted_by_prior`). Any code path
  that shifts the parametric P50 is a rule-13 bug.
- The **published band is asymmetric around the model path** and honestly covers the
  known bias: a client reading the PJM band sees the model's demonstrated +22 %
  dispatch bias carried forward as spread, not a model that pretends the bias away
  (asserted: `test_asymmetric_when_bias_nonzero`).

### 2.4 Convolution

Log-space Monte-Carlo product, per ISO per forecast year (§3.3): each of the *n*
parametric draws is paired with `K = STRUCTURAL_PRIOR_CONVOLUTION_K` (= 25)
independent `ε` draws → an *n × K* sample of `emissions · exp(ε)`. Published quantiles
P5/P10/P25/P50/P75/P90/P95 come from the pooled *n · K* sample (numpy Hyndman–Fan
type-7, `n` reported per quantile). When `ε ≡ 0` the sample recovers the parametric
spread (asserted: `test_zero_prior_recovers_input_spread`). Both layers are stored, so
the parametric-only band stays inspectable next to the published one (plan §4.1).

---

## 3. What the published band does NOT yet cover (§3.4) — stated honestly

1. **Fleet-path (capacity) error.** `ε` is measured on one-year backcasts with a
   *frozen* fleet; the forward trajectory also depends on the capacity-evolution
   layer, whose skill is **unmeasured** (PP-0.3 capacity hindcast unbuilt). The code
   carries a horizon-widening term `λ(h)` (`STRUCTURAL_PRIOR_HORIZON_LAMBDA`) pinned to
   **0 and flagged UNMEASURED**. While it is 0, `StructuralPrior.is_dispatch_conditional()`
   is True and **every published band is labelled "dispatch-conditional — excludes
   fleet-path structural error."** Dropping that label is gated on PP-0.3 supplying a
   measured `λ(h)`; it is never a tuned value.
2. **Stationarity (A-4).** 2023–2025 dispatch error is assumed representative of
   2026–2050 dispatch error for a given fleet/inputs. Untestable until the quarantined
   2022/H1-2026 holdouts are scored **exactly once** at the sanctioned moment (rule 22)
   — that is the first out-of-time check of `ε`, and the only moment the prior is re-fit.
3. **ε independent of the drivers (A-5).** The n = 3 sample is far too small to
   estimate state-dependent error ("worse in high-gas years"); `ε` is drawn
   independent of the parametric draw. Disclosed.
4. **In-sample offer curves (A-6).** Statmode keeps the keeper's offer-curve
   multipliers, tuned on the same 2023–2025 years, so `ε` is still **optimistic** — the
   true band is at least as wide. The PP-0.2 leave-one-year-out harness is the
   refinement; direction of the error is disclosed, not a blocker for v1.
5. **Weather–gas joint tails (A-8/§2.3).** The parametric layer omits the gas↔weather
   copula term (no sub-annual forward gas machinery), so the joint cold-snap tail is
   understated. Disclosed limitation.

---

## 4. Assumptions ledger (A-1 … A-8)

The full ledger a reviewer should attack (plan §7). A-1/A-2/A-3/A-7 are parametric-layer
(PB-2) assumptions; A-4/A-5/A-6/A-8 bear directly on this note's prior.

| ID | Assumption | Where | Mitigation / test |
|---|---|---|---|
| A-1 | AEO low/high gas cases ≈ P10/P90 of the 2050 marginal | PB-2 §2.2 | sensitivity: treat as P25/P75 in one sweep; disclosed |
| A-2 | gas↔load Spearman +0.3, judgment anchored to AEO cross-case ordering | PB-2 §2.3 | mandatory ρ=0 / ρ=+0.6 sensitivity members; report band delta |
| A-3 | published ISO low/high load spans the plausible range (uniform, not tails) | PB-2 §2.1 | DC block (PP-3.3) extends the upper range |
| A-4 | dispatch error stationary 2023-25 → 2026-50 | **§3.4.2** | one-shot holdout scoring re-fits ε at the sanctioned moment |
| A-5 | ε independent of the parametric draw | **§3.4.3** | untestable at n=3 yr; disclosed |
| A-6 | statmode ε optimistic (in-sample offer curves) | **§3.4.4** | PP-0.2 LOYO refinement; direction disclosed |
| A-7 | gas shock perfectly persistent (single z per draw) | PB-2 §2.2 | conservative (widest) for trajectory quantiles; disclosed |
| A-8 | policy weights 0.50/0.25/0.25 are a judgment input | PB-2 §2.1 | explicit spec input, client-adjustable, echoed in outputs |

Additional prior-specific structural assumptions, disclosed here:

- **Noise pooled across ISOs.** `s_pooled²` treats the six ISOs' dispatch-skill noise
  as exchangeable to buy degrees of freedom against n = 3. Bias stays per-ISO (it is
  persistent and ISO-specific); only the *noise scale* is pooled.
- **CO2 residual as the structural proxy.** The prior is fit on system fossil CO2
  log-error and applied to the emissions band only — other metrics stay parametric.

---

## 5. Output surface & reproducibility

Written by `ensemble.export_sampler_ensemble(..., prior=…)` (and recomputable, without
solving, by the pure `ensemble.bands_from_metrics(metrics, seed, iso, prior)`):

- `bands.parquet` — `(year, metric, layer, quantile, value, n, bootstrap_lo,
  bootstrap_hi)` with `layer ∈ {scenario_envelope, parametric,
  parametric_plus_structural}`. The published layer is emissions-only.
- `ensemble_meta.json` — the `structural_prior` block (`StructuralPrior.as_dict()`):
  version, estimator note, ν, fit years, pooled noise, per-ISO residuals with their
  statmode run ids, `horizon_lambda` status, the `dispatch_conditional` flag, the
  emissions-basis identity, and the per-ISO staleness flags (§6). The
  `label` derives its caveats from those flags, so the fan chart never shows a band the
  metadata cannot defend (plan §4.2).
- **Fitted prior artifact** — `write_prior_artifact` commits the full fit record to
  `results/ensemble/structural-prior/<version>.json` (one file per prior version), so
  every re-fit lands as a new, diffable artifact next to its predecessor.

CLI: `market-sim ensemble --config base.yaml --sampler configs/uncertainty_ercot.yaml
--out-dir results/ensemble/ercot_v1 --structural-prior` folds the prior in;
omitting the flag emits the parametric layer only.

---

## 6. Emissions-basis staleness (2026-07-05) — carbon-zero re-scored, carbon-priced flagged

The six D-7 statmode probes were solved and registered 2026-07-03/04, **before** the
W2-P1 emissions fixes merged (PR #1371, 2026-07-05: `fff2c34` R2 physical-HR CO2
booking, `968cead` quarantine-row strip). The prior's fit inputs therefore predate the
current emissions basis, and the W0-P4 design
(`docs/handoffs/forecast-validation-program-2026-07.md` §0/§3.2) splits the
consequence by carbon pricing:

- **Carbon-zero ISOs (ERCOT / PJM / MISO): re-scored, basis-current.** R2 provably
  does not touch their solve (carbon = $0 ⇒ the CO2 rate never enters `mc`), so only
  the scoring needed re-checking. `rescore_carbon_zero` executes the no-solve re-score
  at fit time: recompute model CO2 = Σ_class `gmModel`·intensity and actual CO2 =
  Σ_class `classFull`·intensity from the committed artifacts and refuse to fit on any
  mismatch beyond 5-dp intensity rounding. Verified two ways on 2026-07-05: (a) the
  C5a scoring-rate rows for 2023–2025 in
  `data/raw/_processed-legacy/fossil_co2_rates.parquet` are **content-identical** at
  HEAD vs the pre-registration SHA (`8b8293c`) — the 07-04 holdout intake (`a0faf74`)
  only *added* quarantined 2022/2026 rows, which nothing here reads (rule 22), and
  `968cead` only stripped rows from `plant_emission_rates.parquet`, which the scoring
  fast-path does not consult when `fossil_co2_rates.parquet` covers the year; (b) the
  runtime re-score reproduces every committed value
  (`rescore: "verified-identical"` in the artifact).
- **Carbon-priced ISOs (CAISO / NYISO / NEISO,
  `STRUCTURAL_PRIOR_CARBON_PRICED_ISOS`): STALE, flagged.** R2 moves their merit order
  (the CO2 rate enters `mc`), so their statmode *solves* — not just scores — are
  stale, and no post-processing can repair that. Their residuals are fitted from the
  stale bundles and flagged `basis_stale: true` / `"stale-pending-W3-P1"` in the
  artifact, in `ensemble_meta.json`, and on the band label. Because the pooled noise
  mixes every fitted ISO's variance, the label carries the staleness caveat even for a
  basis-current ISO's band.
- **The W3-P1 re-fit is a clean swap.** The artifact records the emissions-basis
  identity (label + sha256 of `fossil_co2_rates.parquet`) and every input run id;
  when W3-P1 re-solves the three carbon-priced statmode probes at HEAD, updating
  `STATMODE_PROBE_RUNS` and re-running `default_prior` + `write_prior_artifact`
  produces the successor artifact with the flags cleared.

**ERCOT's prior — the PB-5 input — is basis-current** (bias +0.005, re-score verified).

*Produced for PB-3, 2026-07. Design: `docs/handoffs/probability-bounds-plan-2026-07.md`
§3. Fit inputs: the committed D-7 statmode probes
(`docs/statistical-mode-results-2026-07.md`).*
