# 0020 — Annual EAC time series + market-indexed (`lmp_ppa`) attribute basis

- **Status:** accepted
- **Date:** 2026-07-07
- **Session:** scope-2 EAC diagnosis + wiring
- **Implemented by:** `resources.py` / `config.py` / `lp.py` / `profiles.py` /
  `data/eac/eac_prices.csv` / `data/lcoe/resource_costs.csv`

## Context

The tool priced clean attributes (EACs) only for existing nuclear/hydro, as a
single flat `$/MWh` scalar folded into VOM; new-build resources carried no
attribute at all, and CCS was a `capex_fixed` build with the §45Q credit netted
into its VOM. The owner asked for (a) an **annual** EAC price series
(year-indexed, flat-feedable) for wind, solar, offshore wind, existing
nuclear/hydro, nuclear uprates, run-of-river hydro, and CCS; (b) the ability to
procure wind/solar on an attribute basis, not only build them; and (c) CCS
priced as **LMP + clean EAC premium**, with §45Q accruing to the project owner
(out of scope here). Hourly matters through *when* a resource generates, but the
EAC itself is annual, not hourly.

## Options considered

1. **Hourly EAC series** — one price per (resource, hour). Rejected: the owner
   wants annual EAC granularity; hourly attribute prices are not a real market
   and would over-parameterize.
2. **Flat scalar only (status quo)** — no trajectory. Rejected: cannot express a
   declining wind/solar attribute or a CCS ramp.
3. **Annual `(resource, year)` series resolved to the run year, plus a new
   market-indexed cost basis** — chosen.

## Decision

- **Annual EAC series.** `data/eac/eac_prices.csv` carries `(resource, year,
  eac_mwh)`. It resolves to the run's `config.year` by exact match, else the
  latest year at or before it (forward-fill a sparse trajectory), else the
  earliest. Precedence: `config.eac_premium_mwh` override > series > table
  `eac_premium_mwh` column. A flat single value and a full trajectory are both
  expressible; `eac_prices_file=""` disables the series (table columns only).
- **New `lmp_ppa` cost basis** (market-indexed attribute PPA): the buyer pays the
  **hourly LMP** for energy plus the EAC premium. `fixed_mwyr=0` and VOM carries
  only the EAC; energy is added per-hour in the LP via a `lmp_indexed` flag, so
  the resource's **net portfolio premium is exactly its EAC** (energy nets
  against the avoided grid purchase). Used for CCS, nuclear uprate, run-of-river
  hydro, and attribute-basis wind/solar/offshore.
- **CCS reframed** onto `lmp_ppa`: no capex in the LP, no 45Q-in-VOM (both accrue
  to the project owner; the EAC is derived from them via ADR 0021). The ADR 0012
  admissibility threshold and residual-emission reporting are unchanged.
- **Attribute wind/solar** reuse their build twin's CF shape via
  `profiles.SHAPE_ALIAS` (`onshore_wind_ppa → onshore_wind`, etc.).

## Consequences

- New resources: `nuclear_uprate`, `hydro_ror`, `onshore_wind_ppa`,
  `solar_pv_ppa`, `offshore_wind_ppa` (plus per-ISO caps rows).
- Build-basis wind/solar/offshore keep their **endogenous** premium
  (LCOE − hourly-LMP value), so "cheaper new-build in high-cost hours lowers the
  premium" is unchanged. Attribute-basis variants instead price at a flat EAC.
- `gas_cc_ccs_new`/`gas_cc_ccs_retrofit` switch from `capex_fixed` to `lmp_ppa`;
  the pre-ADR-0020 capex+45Q comparison test is superseded.
- Follow-up: EAC series values are illustrative placeholders pending per-ISO
  breakeven derivation (ADR 0021).
