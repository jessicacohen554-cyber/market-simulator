# NEISO calibration — best config so far

> **DETERMINATION (2026-06-27, scorer): CALIBRATED-WITH-CAVEATS** for the
> registered keeper `neiso-37-weather-floor` (bundle
> `results/calibration/neiso_37_tempfloor_dailybasis_hydrofix_3yr`, years
> 2023/24/25). This supersedes the prior keepers `neiso-33` and `neiso-23`.
> The gas family (C2), system mean LMP (C3a), price shape (C3b), dispatch
> correlation (C4), 2025 CO2 vs eGRID (C5a) and governance (C6) all PASS; no
> offer/adder/pin/haircut was tuned to a residual and the model is not pinned
> to either actual. The grade is capped at CALIBRATED-WITH-CAVEATS by the three
> accepted caveats below — one HARD categorization item and two structural
> model-miss items that close only via a documented future build, never via a fit.

## What the keeper is

`neiso-37` = the `neiso-33` recipe (measured Algonquin / EIA-MA-citygate **daily**
gas-hub basis overlay + dual-fuel oil re-attribution + EIA-930-pinned hydro
budget with 2024 plant-capacity backfill + biomass/OTHER measured must-run +
historic outage overlay + storage vintage ramp) **plus** the dual-limb
temperature-correlated reliability floor (`neiso_temp_reliability_floor`:
CT_PEAKER hot-limb on load-weighted TMAX, COAL/ST_GAS cold-limb on TMIN,
coefficients regressed from measured CAMPD capacity factors — physical
temperature→commitment rules, not TWh-residual fits).

Restoring the measured **daily** hub overlay (`--gas-hub-basis-daily`) is what
`neiso-36` accidentally dropped: with only the flat monthly hub, within-month
cold-day Algonquin spikes never crossed distillate parity, the physical dual-fuel
gas→oil switch never tripped, modeled oil collapsed ~1.6→0.05 TWh and relabeled
onto gas-CC (gas-family C2 +4.3%, FAIL). With the daily overlay restored the
switch trips on the real cold-day prints, 2025 oil returns to 1.60 TWh and the
gas family lands 60.85 vs EIA-930 59.76 (+1.8%, C2 PASS).

Headline (model vs actual): gas family 53.44/58.00/60.85 vs EIA-930
52.75/56.92/59.76 (+1.3%/+1.9%/+1.8%, C2 PASS); system mean LMP
34.65/39.16/68.50 vs RT 35.70/39.50/65.89 (−2.9%/−0.9%/+4.0%, C3a PASS);
2025 CO2 23.67 vs eGRID 23.11 Mt (+2.4%, C5a PASS).

## The three accepted caveats

### 1. C1 CC_REGULAR gas-vs-OTHER fold-in categorization — HARD (2023 & 2024)
- 2023: model 51.68 vs deflated EIA-930 50.63 TWh (+1.05 TWh); 2024: 56.27 vs
  54.66 TWh (+1.61 TWh).
- The gas **family** is in-band (C2 PASS). The per-class C1 gate trips because the
  EIA-930 "Natural Gas" cell is deflated by the ~1.6 TWh of geothermal+biomass
  NEISO folds into it (`reconcile_vintage_classes`); the model books that
  OTHER/biomass residual as its own measured must-run rows and serves the
  un-foldable remainder with marginal CC, so ~1 TWh lands on CC_REGULAR. This is
  the EIA-923-vs-EIA-930 OTHER categorization difference, now visible per-class
  under the bidirectional reconcile. **Closable only by reconciling the OTHER/NG
  fold-in on both sides — never by injecting the residual or scaling CC to the
  deflated benchmark (that is fitting).** This is the single accepted HARD caveat.
- Note: the prior `neiso-33`/`neiso-36` slim bundles predated this reconcile, so
  their committed bench masked this item; `neiso-37` is the first NEISO bundle
  scored against the deflated benchmark and documents it.

### 2. C3c price tail > $300/MWh — MODEL MISS (all three years)
- model 0h vs actual 15h / 8h / 20h; system max pinned at the dual-fuel
  oil-parity cap (~$258/MWh).
- On cold days dual-fuel units switch to oil (`apply_dual_fuel_pricing`) and the
  marginal price can't exceed oil parity, so the energy-only LP produces 0 hours
  > $300. Two faithful ISO-NE scarcity structures were built and tested this
  session and **do not bind** in 2023–25: (a) in-LP operating-reserve
  co-optimization on the published NEISO RCPF requirements
  (`neiso_reserve_coopt_inputs` / `energy_reserve_coopt`) and (b) a
  temperature-dependent winter gas-availability derate
  (`inject_neiso_gas_coldsnap_derate`). NEISO is simply not operating-reserve-short
  in these years — the ~6.8 GW dual-fuel fleet stays available on oil and
  imports/hydro/storage/floored-steam keep reserve headroom above the
  1,800/1,200 MW requirements even with a 20% cold-window gas derate
  (`reserve_price` stays 0). Both are kept as default-off infrastructure that
  binds in tighter forecast years.
- The real residual driver is **winter fuel-inventory scarcity rent** (oil/peaker
  units rationing limited on-site distillate over a multi-day cold snap). A
  cold-day oil **adder** would be a forbidden residual fit (distillate is a global
  liquid fuel whose commodity price does not spike like pipeline gas basis). The
  only forward-faithful fix is modeling the oil fleet as **inventory-limited** (a
  seasonal oil-burn budget like hydro, whose shadow price *is* the scarcity rent,
  lands on the tightest hours, and is condition-responsive) — a documented future
  build, not closable by an adder/offer tune.

### 3. C5b storage throughput — MODEL MISS (2025, downstream of #2)
- model 0.73 vs actual 2.08 TWh (−64.9%).
- Arbitrage throughput tracks the peak-to-trough price spread, compressed because
  the LP caps the cold-hour tail at oil-parity (see #2). The reserve co-opt and
  gas-availability derate built this session do not widen the spread in the
  backcast (`reserve_price=0`, storage 0.73→0.78 TWh), so this is **not** a
  storage-model error — it closes only when the winter fuel-inventory scarcity
  rent is recovered via the forward-faithful oil-burn-budget constraint, never via
  a storage or offer tune.

## Hydro note (required measured flags)

Hydro 8.70/7.33/5.11 TWh comes from the EIA-930 monthly budget pin plus a 2024
plant-capacity backfill: the 2025 EIA-923 vintage lists only 5 of ~166 hydro
plants, so without `--hydro-backfill-year 2024 --hydro-eia930-monthly` the LP
burns ~5 TWh of phantom gas. Both flags are required and both are measured inputs.

## Reproduce

```
python scripts/replay_keeper.py results/calibration/neiso_37_tempfloor_dailybasis_hydrofix_3yr
python scripts/calibration_verdict.py --run-id 2026-06-27-neiso-37-weather-floor

# Solve from scratch (neiso_temp_reliability_floor is default-ON for NEISO):
python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025 \
  --commitment --hydro-backfill-year 2024 --hydro-eia930-monthly --gas-hub-basis-daily
```
