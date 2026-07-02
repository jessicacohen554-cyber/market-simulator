# 0007 — Matching semantics: annual hourly matching, storage provenance, residual carbon

- **Status:** accepted (matching definition stakeholder-decided 2026-07-01; storage
  provenance & carbon attribution remain provisional per the default-decisions table).
  **Residual-carbon attribution superseded by ADR 0013** (2026-07-02): the ISO
  *marginal* emission rate below was a consequential-accounting method misapplied
  to attributional Scope 2 reporting; unmatched grid purchases are now attributed
  at the market simulator's *hourly fossil-only average* rate — see
  `0013-residual-carbon-hourly-fossil-average-rate.md`. The matching-semantics
  and storage-provenance decisions here stand.
- **Date:** 2026-07-01
- **Session:** PS-04 (Matching Semantics: annual vs strict 24/7; carbon)
- **Implemented by:** PP-04/PP-06

## Context

"24/7 CFE" has competing definitions (strict per-hour, annual average, rolling
annual). The tool's headline metric is annual hourly matching with surplus
excluded. Storage provenance and carbon attribution of unmatched grid purchases
must be explicit to avoid round-trip laundering claims.

## Options considered

1. **Strict per-hour** (every hour grid_buy = 0) — most conservative; raises
   curtailment and over-capacity costs sharply; rarely achievable.
2. **Annual hourly matching** (1 − Σ_t grid_buy_t / Σ_t load_t) — averages out
   mismatches over the year; more economical; current approach (chosen).
3. **Rolling annual** — moving 365-day window; computationally heavier; deferred.

## Decision

**Headline metric = VOLUMETRIC hourly matching** (stakeholder-specified): within
each hour, low-carbon energy counts toward the metric only up to that hour's
load — `matched_t = min(clean_serving_load_t, load_t) = load_t − grid_buy_t` —
and the score is the load-weighted sum **Σ_t matched_t / Σ_t load_t
= 1 − Σ_t grid_buy_t / Σ_t load_t**. It is the *percentage of annual load energy
matched at hourly granularity*, explicitly **not** "% of hours matched at 100%",
and surplus in one hour never spills into another hour's score. Surplus is
**excluded** — surplus clean generation is sold, never counted as matched (24/7
rule); `grid_buy_t ≥ 0` caps per-hour matched at load. Mode B's strict-hourly
variant (per-hour constraint `grid_buy_t ≤ (1−target)·load_t`) remains available
via `strict_hourly_matching` for hard-24/7 studies; it is a constraint option,
not the headline metric.
**Storage provenance:** energy is not tracked by source; charging draws from the
aggregate node and energy bought from the grid (grid_buy) is counted unmatched at
purchase time, even if later discharged to serve load — conservative, no
round-trip laundering. **Residual carbon:** grid_buy is attributed at the ISO
**marginal** emission rate (input, tCO₂/MWh); outputs gain a `residual_co2_tons`
column per sweep point. **Denominator** = gross load (not net of on-site clean).

## Consequences

- Outputs add `residual_co2_tons` and `matching_pct` (annual/strict variants).
- A new input: ISO marginal emission rate (tCO₂/MWh), sourced per ISO.
- PP-06 reports both matching % and residual carbon per frontier point.
- No per-facility tracking needed; aggregate-level matching and carbon suffice.
