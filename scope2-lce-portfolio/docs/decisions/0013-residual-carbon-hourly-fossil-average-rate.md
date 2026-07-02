# 0013 — Residual carbon: hourly fossil-only average rate (attributional accounting)

- **Status:** accepted (stakeholder-corrected 2026-07-02); supersedes the
  residual-carbon attribution part of ADR 0007
- **Date:** 2026-07-02
- **Session:** stakeholder correction of ADR 0007's provisional carbon attribution
- **Implemented by:** `intake.py`/`lp.py`/`scripts/build_fossil_avg_co2_rate.py`

## Context

ADR 0007 attributed residual carbon (`residual_co2_tons`) to unmatched grid
purchases at a flat per-ISO **marginal** emission rate, sourced from EPA
eGRID2022 *non-baseload* output emission rates (`data/emissions/marginal_co2.csv`).
That was the wrong accounting methodology for this tool. The tool does
**attributional** GHG accounting — Scope 2 corporate carbon-footprint reporting,
"how much carbon is embodied in the energy this facility actually consumed."
Marginal/non-baseload rates answer a different, **consequential** question — the
incremental impact of a decision (e.g. an efficiency project):

- EPA's own eGRID documentation states that non-baseload rates "are designed
  for marginal-emission analysis (e.g. quantifying the impact of an energy
  efficiency project) and over-state Scope 2 emissions for general consumption."
- The GHG Protocol *Scope 2 Guidance* location-based method uses **average**
  grid emission factors, never marginal ones.

Stakeholder correction (verbatim): "Just use the fossil only average mix
emission rate for the corresponding hour from the market simulator solver so
take that average emission rate and assign to unmatched hours accordingly. That
would be correct for attributional accounting. Marginal rates are only used in
consequential accounting and were doing attributional ghg accounting."

## Options considered

1. **Hourly fossil-only average rate from the market simulator's dispatch
   solve** (chosen) — per hour `t`:
   `rate[t] = Σ_g dispatch[g,t]·emission_rate[g] / Σ_g dispatch[g,t]` over
   fossil generators `g` (tCO₂ emitted by fossil generation that hour ÷ fossil
   MWh that hour; zero-carbon generation excluded from numerator and
   denominator). Hour-varying by construction, consistent with the tool's
   hourly matching semantics; sourced from the same calibrated solve that
   supplies the BAU LMPs (ADR 0011).
2. **Static eGRID non-baseload (marginal) table** — the ADR 0007
   implementation; rejected as a consequential-accounting rate misapplied to
   attributional reporting (EPA caveat above), and a static external table
   that neither varies by hour nor responds to modeled fleet changes.
3. **Flat annual average factor (e.g. eGRID total-output rate)** — right
   accounting family but a scalar: it erases the hourly carbon signal that a
   24/7-matching tool exists to capture (night-time unmatched hours draw a
   different mix than midday ones), and it comes from a data vintage
   disconnected from the modeled year.
4. **Total-system average (fossil + zero-carbon in denominator)** — dilutes
   the rate with zero-carbon baseload that clean buyers already claim through
   their own instruments; the stakeholder specified the fossil-only mix for
   the unmatched residual.

## Decision

**Residual carbon = hourly dot product against the market simulator's
fossil-only average emission rate:**
`residual_co2_tons = Σ_t grid_buy[t] × fossil_avg_co2_rate[t]`.

- **Upstream function:** `market_sim.results.emissions.compute_fossil_avg_rate`
  computes the `(T,)` hourly rate from the dispatch array and per-generator
  emission rates. Fossil generators are identified as `emission_rate > 0`
  (in market_sim only fossil fuels carry a nonzero CO₂ factor). Hours with
  zero fossil dispatch report `0.0` — no fossil generation that hour means
  nothing to attribute at the fossil rate — never `nan`/`inf`.
- **Export contract** (mirrors the ADR 0011 LMP contract): CSV/Parquet with
  columns `(hour, iso, fossil_avg_co2_rate)`, one rate per ISO-hour in
  tCO₂/MWh, produced by `scripts/build_fossil_avg_co2_rate.py` from a cached
  market-sim dispatch result (read directly via pyarrow — never
  `import market_sim`; the rate logic is vendored as
  `lce_portfolio.vendored.fossil_avg_rate`, parity-tested from the market_sim
  test tree).
- **Config/intake:** new `PortfolioConfig.emissions_file` field; intake
  (`intake.emissions_intake`/`prepare_emission_rate`) applies the same rigor
  as the LMP path — missing hour is a hard error (never a zero-fill),
  duplicate `(iso, hour)` rejected, negative rates rejected. `emissions_file
  = None` resolves to an all-zero vector (reporting off — e.g. the SAMPLE
  demo ISO), mirroring the previous no-table-row behavior.
- **Removed:** `data/emissions/marginal_co2.csv`, the
  `lce_portfolio.emissions` marginal-table module
  (`load_marginal_co2`/`resolve_marginal_co2_rate`/`apply_marginal_co2`), and
  the `PortfolioConfig.marginal_co2_ton_per_mwh` scalar field. The eGRID
  non-baseload path is no longer reachable.

**Forecast admissibility (CLAUDE.md rule #11):** unlike the static eGRID
table, the fossil-average rate is a formulaic output of the market simulator's
own solve — it regenerates for every forecast year and responds to changed
fleet, fuel, and dispatch conditions, so the same quantity exists for a
forward year from forward drivers. It is a legitimate model-derived input, not
a measured outcome pinned back in.

## Consequences

- `residual_co2_tons` now reflects *when* the facility is unmatched: night
  hours priced at the night fossil mix, not an annual flat proxy.
- The emissions export joins the LMP export as a per-ISO-year artifact of the
  calibrated market-sim run; both come from the same scenario/year, keeping
  price and carbon signals consistent. Real exports under `data/emissions/`
  are gitignored (reproducible/disposable, like `data/profiles/`).
- `build_and_solve`/`run_sweep` gain a keyword-only `emission_rate` parameter
  (default `None` = reporting off); the positional signature is unchanged, so
  existing callers/tests are unaffected.
- ADR 0007's matching-semantics and storage-provenance decisions stand;
  only its residual-carbon attribution paragraph is superseded.
- Limitation: the single fossil-average series is ISO-wide (single-node tool)
  and, like the LMPs (ADR 0011), price-taker — the clean build does not feed
  back into the grid mix.
