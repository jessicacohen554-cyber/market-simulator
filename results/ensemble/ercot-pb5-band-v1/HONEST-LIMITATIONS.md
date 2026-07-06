# ERCOT production probability band (PB-5, `ercot-pb5-band-v1`) — honest limitations

This block ships **with** the band, not after it (goal B: survive a hostile
referee). Nothing below is softened. It restates, for this specific run, the
caveats the probability-bounds plan (`docs/handoffs/probability-bounds-plan-2026-07.md`
§3.4, §7) pre-registered, plus two run-specific ones.

## What this run is

The **first real** ERCOT production band: the landed PB-2 sampler
(`market_sim.uncertainty`) + PB-3 structural prior (`market_sim.structural_prior`)
driven end-to-end on real HiGHS, in **forecast mode** (`ScenarioConfig.mode="forecast"`,
set explicitly; no backcast overlays), over the **2026–2032** window — the same
horizon the forecast-validation golden (`tests/golden/ercot_2026_2032.json`) and the
`forecast-invariants.yml` heavy tier already use — replacing the synthetic fixture
(`synthetic-fixture-ercot-v1`) as the fan-chart page's data source. Base config = the
ERCOT forecast reference (legacy heat-rate bins, `use_campd_bins=False`) — the same
structural config the golden pins. Draws come from the committed, cited
`configs/uncertainty_ercot.yaml`; every quantile carries a bootstrap 90% CI so the
sampling noise is visible, not assumed away. The gas-price σ is deliberately kept
anchored to the full 2050 AEO horizon, so the band **width** is the conservative
full-horizon width, not a narrower window-specific one.

## The three pre-registered limitations (stated, not softened)

### (a) λ(h) hindcast conditioning is UNMEASURED — the band is DISPATCH-CONDITIONAL
The PB-3 structural-error prior is fit from the D-7 statistical-mode probes on
**frozen-fleet one-year backcasts** (2023–2025). Its horizon-widening variance
multiplier **λ(h) is pinned to 0 and flagged UNMEASURED**: the prior is **not**
conditioned on measured hourly hindcast error, and the fleet-evolution layer's own
forward skill is **unmeasured** (PP-0.3 capacity hindcast unbuilt). Every band here
is therefore **dispatch-conditional — it excludes fleet-path structural error**. It
covers "we don't know the inputs" (parametric) ⊕ "given the inputs, the model's
*dispatch* is wrong by this much" (structural), but **not** "the fleet trajectory
itself is wrong." The band widens only when λ(h) is measured; it must not be quoted
today as covering fleet-path error.

### (b) the datacenter / large-load uncertainty axis is ABSENT
**CX-4 (the datacenter/large-load block) is UNBUILT** — there is no datacenter load
block anywhere in `src`. The sampler's load-growth axis moves only the published ISO
low/high demand-growth range (`demand_growth_percentile`); it does **not** sample a
separate large-load/datacenter dimension. `datacenter_load_gw` does not exist as a
lever in this run. Consequence: **the upper emissions tail is understated** by exactly
the datacenter boom this model cannot yet represent. The published band is a floor on
the true upper uncertainty, not a bound.

### (c) AEO anchor status — what it certifies and what it does not
The gas-price marginal is anchored on **AEO2025** Henry Hub cases
(`constants.HENRY_HUB_TRAJECTORIES`, High/Reference/Low Oil-and-Gas-Supply): the 2050
low/high are read as the P10/P90 (assumption A-1), giving the AEO-implied σ floor
(~0.464) that dominates the front NYMEX/STEO implied-vol schedule. The demand-growth
range is anchored on the same-vintage ISO/EIA forecasts.
- **Certifies:** the gas and load band *widths* are traceable to cited AEO2025-vintage
  external sources — not to any residual, and not fitted to any measured outcome.
- **Does NOT certify:** the *current* AEO2026 vintage (the PP-3.2(2) API pull is
  unbuilt), nor that the AEO low/high cases themselves span the true tails (A-1/A-3 are
  disclosed judgment assumptions, not measured coverage).

## Two run-specific caveats (full disclosure)

### (d) reduced reporting window (2026–2032) and draw count (n=12) vs the spec batch
The committed spec (`configs/uncertainty_ercot.yaml`) is **n=64 over the full
2026–2050 horizon** — the plan's explicit **~2.7-day scheduled run** (§5), out of
scope for an interactive session. This run is **n=12 over 2026–2032**: a genuine run
of the production machinery on the golden/CI window, with the **bootstrap 90% CI on
every quantile making the small-n sampling noise explicit**, and (per above) the
gas-σ width held at the full 2050 anchor. It is NOT the n=64 / 2050 spec batch;
scaling n and extending to 2050 is a compute/scheduling matter, not a code change
(same seed=7, larger n, `end_year=2050`, re-run the same driver). Do not quote these
quantiles as the n=64 / 2050 band.

### (e) confirmed-retirement channel inert in this run environment
`confirmed_exits_enabled` defaults on, but `scripts.lib.clean_io` is not importable
under the packaged `uv run` path, so the confirmed-exit registry loads empty ("no
confirmed exits for ERCOT"). **This is identical to the environment the golden
reference and the `forecast-invariants.yml` heavy tier run in** (same `uv run` path),
so this band, the re-seeded golden, and the CI regression are mutually consistent — but
the confirmed-retirement forecast channel is inert here and is not exercised by this
band.

## Provenance
- Sampler spec: `configs/uncertainty_ercot.yaml` (seed=7, echoed into `ensemble_meta.json`).
- Structural prior: `market_sim.structural_prior.default_prior()` — pooled D-7 statmode
  residuals over all six ISOs (carbon-priced ISOs flagged `basis_stale`), no solve.
- Artifacts: `draws.parquet`, `metrics.parquet`, `bands.parquet`, `ensemble_meta.json`
  (frozen §4.1 schema) in this directory; page payload `frontend/data/forecast/ercot-pb5-band-v1.js`.
