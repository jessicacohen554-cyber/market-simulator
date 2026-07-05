# Probabilistic Emissions Methodology — the published band

**What this documents.** How the emissions forecast's probability band is built and what
each layer may honestly claim. Design: `docs/handoffs/probability-bounds-plan-2026-07.md`
(the plan; §-references below are to it). Implementations: PB-1/PB-2 levers + sampler
(`src/market_sim/uncertainty.py`, `src/market_sim/ensemble.py`) and PB-3 structural prior
(`src/market_sim/structural_prior.py`, this session, 2026-07-05).

**Three claims, never conflated** (plan §0.5):

| Layer (`bands.parquet` `layer` column) | Claim | Status |
|---|---|---|
| `scenario_envelope` | deterministic scenario range — not a probability band | PB-0, not yet emitted |
| `parametric` | probability band over *input* uncertainty (gas, load, tech, weather, hydro, policy), given a correct model | landed (PB-2) |
| `parametric_plus_structural` | the **published band**: parametric ⊕ the model's own measured dispatch error | landed (PB-3, this doc §2–3) |

Every published artifact carries the label **"dispatch-conditional band — excludes
fleet-path structural error"** until the W2-P5/PP-0.3 capacity hindcast measures the
fleet-evolution layer's skill (§4 item 1).

---

## 1. The parametric layer (PB-2, summary)

`n` LHS + Gaussian-copula draws over the §2 dimensions produce `n` full forecast solves;
`bands.parquet` publishes Hyndman–Fan type-7 quantiles with the member count `n` and a
1000-resample bootstrap 90% CI attached to every quantile. See `ensemble.py` /
`uncertainty.py` docstrings and plan §2. Everything below *adds* to this surface; nothing
below modifies it.

## 2. The structural prior (PB-3)

### 2.1 Fit inputs — statmode, not keepers

For each ISO, `eps_{i,y} = ln(emissions_model / emissions_actual)` for
y ∈ {2023, 2024, 2025} (`STRUCTURAL_PRIOR_YEARS`), from the **D-7 statistical-mode
bundles** (`docs/statistical-mode-results-2026-07.md`) — the probes that turn off every
backcast-only measured overlay while keeping realized gas/load/weather. Their error is
*model error given true inputs*, which is exactly what convolves with the parametric
layer without double-counting (plan §3.1). The overlay-on keepers would understate:
keeper error is overlay-carried (plan §3.2).

The emissions pair per ISO-year is the committed C5a scoring pair: model fossil CO2 from
the statmode run payload (`frontend/data/backcast/runs/<id>.js`, `years[y].co2.model`)
and actual fossil CO2 from the shared bench part (`bench/<ISO>/<y>.json.gz`,
`bench.co2.egrid`), both booked at the same measured per-class CO2 intensities — so the
prior measures the same skill gap the dashboard publishes.

Fitted values (artifact `results/ensemble/structural-prior/structural_prior_v1.json`):

| ISO | eps 2023 | eps 2024 | eps 2025 | bias b_i | own sd s_i | t-scale | basis |
|---|---|---|---|---|---|---|---|
| ERCOT | +0.0012 | −0.0245 | +0.0380 | **+0.0049** | 0.0314 | 0.0483 | current (re-scored) |
| PJM | +0.2359 | +0.2322 | +0.2038 | **+0.2240** | 0.0176 | 0.0483 | current (re-scored) |
| MISO | +0.1400 | +0.0995 | +0.1959 | **+0.1451** | 0.0484 | 0.0559 | current (re-scored) |
| CAISO | +0.0298 | +0.1210 | +0.1554 | **+0.1021** | 0.0649 | 0.0749 | **STALE pending W3-P1** |
| NYISO | +0.0330 | −0.0227 | −0.0153 | **−0.0017** | 0.0302 | 0.0483 | **STALE pending W3-P1** |
| NEISO | −0.0344 | −0.0334 | +0.0386 | **−0.0097** | 0.0419 | 0.0484 | **STALE pending W3-P1** |

Pooled noise s_pooled = 0.0419 (sqrt of the mean within-ISO ddof-1 variance). D-7's
qualitative finding is visible directly: ERCOT's dispatch-skill prior is tight and
near-unbiased; PJM's is a persistent +22–26% coal-side over-count; MISO/CAISO carry
double-digit positive bias.

### 2.2 Form — small-sample honesty (plan §3.2)

Per ISO: `eps_i ~ Student-t(nu=2, loc=b_i, scale=sqrt(max(s_pooled², s_i²)·(1+1/3)))`.

- **nu=2 and the +1/3 inflation** encode that both moments come from three points; the
  t2's infinite variance makes every central interval strictly wider than the plug-in
  Normal(b_i, s_i) — the PB-3 hard requirement, asserted per-ISO by
  `tests/test_structural_prior.py::test_prior_wider_than_plugin_normal_every_iso`.
- **max(s_pooled, s_i)**: pooling borrows strength for the typical ISO but never shrinks
  an ISO noisier than the pool (CAISO, s_i=0.065) below its own plug-in sd.
- **No recentering (rule 13, plan §3.2).** b_i is *carried, never subtracted*. The point
  forecast — the parametric layer's P50 — is untouched; the published band is asymmetric
  around the model path and covers the known bias. Subtracting b_i would feed a measured
  outcome back into the number being validated (an answer-key channel).
  `test_p50_point_path_not_shifted_and_band_asymmetric` and
  `test_appends_layer_without_touching_parametric_rows` assert both halves.

All parameters are registered constants (`constants.py` `STRUCTURAL_PRIOR_*`, rule 24)
and re-derive **only** when the fit inputs change (W3-P1 re-solves, or the rule-22
one-shot holdout scoring) — never in response to a residual (rule 23).

### 2.3 Convolution (plan §3.3)

`structural_prior.convolve`: Monte-Carlo product in log space — each of the `n`
parametric members' `emissions_mt` values gets K=25 (`STRUCTURAL_PRIOR_K`) independent
eps draws, `emissions · exp(eps)`; published quantiles P5/P10/P25/P50/P75/P90/P95
(`PUBLISHED_BAND_QUANTILES`) from the pooled n·K sample per year. Rows land in
`ensemble.compute_bands`'s exact schema with `layer="parametric_plus_structural"`,
appended into the same `bands.parquet` by `append_structural_layer` (idempotent; the
parametric rows are never modified). The bootstrap CI block-resamples parametric
*members* (each keeping its K structural draws), so the reported sampling noise reflects
the member count, not the free-to-grow K. Only `emissions_mt` is convolved — the prior
was fitted on emissions error and claims nothing about prices or other metrics.

A horizon-widening variance term λ(h) exists in the code
(`StructuralPrior.sample(..., horizon_years=h)`) and is **pinned at 0, status
UNMEASURED** (`STRUCTURAL_PRIOR_LAMBDA_H`), until the capacity hindcast supplies a
number. Do not set it without citing that measurement.

## 3. Emissions-basis staleness (2026-07-05 situation)

The six statmode bundles were solved and registered 2026-07-03/04, **before** the W2-P1
emissions fixes merged (PR #1371, 2026-07-05: `fff2c34` R2 physical-HR CO2 booking,
`968cead` quarantine-row strip, `d3077a4` forward estimator). Per the W0-P4 design
(`docs/handoffs/forecast-validation-program-2026-07.md` §0/§3.2):

- **Carbon-zero ISOs (ERCOT / PJM / MISO): re-scored, current.** R2 provably does not
  touch their solve (carbon = $0 ⇒ the CO2 rate never enters `mc`), so only the scoring
  needed re-checking. The no-solve re-score path: recompute model CO2 = Σ_class
  gmModel·intensity and actual CO2 = Σ_class classFull·intensity from the committed
  artifacts under the current basis. Verified in this session, two ways:
  1. the C5a scoring-rate rows for 2023–2025 in
     `data/raw/_processed-legacy/fossil_co2_rates.parquet` are **content-identical** at
     HEAD vs the pre-registration SHA (`8b8293c`) — the 07-04 holdout intake (`a0faf74`)
     only *added* 2022/2026 rows (which nothing here reads, rule 22), and `968cead` only
     stripped rows from `plant_emission_rates.parquet`, which the scoring fast-path does
     not consult when `fossil_co2_rates.parquet` covers the year;
  2. `fit_prior` recomputes both sides per ISO-year at fit time and refuses on any
     mismatch beyond 5-dp intensity rounding (`rescore="verified-identical"` in the
     artifact). An ERCOT full intensity re-derivation from a committed EIA-923 anchor
     (`run124_storage_as_keeper`) reproduced the stored intensities exactly.
- **Carbon-priced ISOs (CAISO / NYISO / NEISO): STALE, flagged.** R2 moves their merit
  order (the CO2 rate enters `mc`), so their statmode *solves* — not just scores — are
  stale, and no post-processing can repair that. Their priors are fitted from the stale
  bundles and flagged `basis_stale: true` / `"stale-pending-W3-P1"` in the artifact and
  in every `ensemble_meta.json` their prior touches. The W3-P1 session owns the
  re-solves; the prior artifact records the emissions-basis identity (label + sha256 of
  the scoring-rate artifact) and every input bundle id, so the re-fit is a clean swap:
  re-run `fit_prior` with the three swapped run ids and save a v2 artifact.

**ERCOT's prior — the PB-5 input — is basis-current.**

## 4. What the published band does NOT yet cover (plan §3.4, stated honestly)

1. **Capacity-path error.** eps is measured on one-year backcasts with a frozen fleet.
   The fleet-evolution layer's skill is unmeasured (capacity hindcast unbuilt), λ(h)=0
   UNMEASURED, and every artifact is labelled **dispatch-conditional**. PP-0.3/W2-P5 is
   the gate on dropping the label.
2. **Stationarity (A-4).** 2023–2025 dispatch error is assumed representative of
   2026–2050 for a given fleet/inputs. First out-of-time check is the rule-22 one-shot
   holdout scoring; the prior re-fits only at that sanctioned moment.
3. **eps independent of the drivers (A-5).** n=3 years cannot support state-dependent
   error (e.g. "worse in high-gas years"); eps is drawn independent of the parametric
   draw. Disclosed.
4. **In-sample offer curves (A-6).** Statmode keeps the keeper's offer-curve
   multipliers, tuned on the same 2023–2025 years — **the statmode eps is
   in-sample-optimistic and the true band is at least as wide.** The PP-0.2
   leave-one-year-out harness is the refinement; direction disclosed, not a v1 blocker.
5. **Weather–gas joint tails.** The copula omits gas↔weather coupling (§2.3 of the
   plan); joint cold-snap tails are understated by construction.
6. **Basis staleness (§3 above).** CAISO/NYISO/NEISO priors pending W3-P1.

## 5. Assumptions ledger (plan §7, A-1..A-8)

| ID | Assumption | Where it enters | Mitigation / test |
|---|---|---|---|
| A-1 | AEO low/high gas cases ≈ P10/P90 of the 2050 marginal | gas σ back-anchor (`uncertainty.py`) | sensitivity sweep treating them as P25/P75; disclosed |
| A-2 | gas↔load Spearman +0.3 (judgment anchored to AEO cross-case ordering) | copula matrix | mandatory sensitivity members at ρ=0 and +0.6 |
| A-3 | published ISO low/high load forecasts span the plausible range (uniform) | load marginal | DC block (PP-3.3) extends the upper range when it lands |
| A-4 | dispatch error stationary 2023-25 → 2026-50 | structural prior (§4.2) | one-shot holdout scoring re-fits eps at the sanctioned moment |
| A-5 | eps independent of the parametric draw | `convolve` | untestable at n=3 yr; disclosed |
| A-6 | statmode eps optimistic (in-sample offer curves) | structural prior fit | PP-0.2 LOYO refinement; direction disclosed — band is a floor on width |
| A-7 | gas shock perfectly persistent (single z per draw) | gas marginal | conservative (widest) for trajectory quantiles; disclosed |
| A-8 | policy weights 0.50/0.25/0.25 are a judgment input | discrete sampler weights | explicit spec input, client-adjustable, echoed in outputs |

PB-3 additions to the ledger: the **max(s_pooled, s_i) + t2 + (1+1/3)** prior form is a
deliberately conservative small-sample choice (wider than every plug-in alternative
considered, per the hard requirement); the **member-block bootstrap** attributes
sampling noise to members only; **K=25** is a variance-reduction knob with no effect on
the band's center or its published width in expectation.

## 6. Artifact & provenance surface

- Prior artifact: `results/ensemble/structural-prior/structural_prior_v1.json` —
  schema-versioned; records per-ISO eps/model/actual by year, bias/noise/scale, the
  statmode run ids + bundle paths, the carbon/staleness flags, and the emissions-basis
  identity (label + `fossil_co2_rates.parquet` sha256).
- Ensemble surface: `append_structural_layer` rewrites `bands.parquet` (structural rows
  replaced idempotently, parametric rows untouched) and stamps `ensemble_meta.json` with
  `structural_prior` (nu, K, seed, fit years, λ status, fit inputs, staleness) and the
  dispatch-conditional label — the fan-chart page (PB-4) renders labels from that
  metadata, so the chart can never show a band the metadata can't defend.
- No solve, no scoring, and no data intake touched 2022 or H1-2026 in the PB-3 session;
  `fit_prior` hard-errors on any fit year outside {2023, 2024, 2025} (rule-22 guard,
  tested).
