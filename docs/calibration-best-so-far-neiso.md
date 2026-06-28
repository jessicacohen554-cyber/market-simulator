# NEISO calibration — best config so far

> **DETERMINATION (2026-06-28, scorer): CALIBRATED-WITH-CAVEATS** for the
> registered keeper `neiso-38-merrimack-availability` (bundle
> `results/calibration/neiso_40_floor_outage_exempt_3yr`, years 2023/24/25).
> This supersedes `neiso-37-weather-floor` (and the earlier `neiso-33`/`neiso-23`).
> The gas family (C2), system mean LMP (C3a), price shape (C3b), dispatch
> correlation (C4), CO2 vs eGRID (C5a) and governance (C6) all PASS; no
> offer/adder/pin/haircut was tuned to a residual and the model is not pinned
> to either actual. The grade is capped at CALIBRATED-WITH-CAVEATS by the three
> carried accepted caveats below (one HARD categorization item + two structural
> model-miss items that close only via a documented future build, never via a fit)
> plus a newly **documented** coal/ST_GAS winter-energy under-run (within the C1
> per-class band, so non-gating) in the same fuel-inventory/reliability family.

## What the keeper is

`neiso-38` = the `neiso-37` weather-floor recipe (measured Algonquin /
EIA-MA-citygate **daily** gas-hub basis overlay + dual-fuel oil re-attribution +
EIA-930-pinned hydro budget with 2024 plant-capacity backfill + biomass/OTHER
measured must-run + historic CAMPD outage overlay + storage vintage ramp + the
dual-limb temperature-correlated reliability floor `neiso_temp_reliability_floor`)
**plus ONE correctness fix:** `neiso_floor_outage_exempt` (default ON).

**The fix (CLAUDE.md #11).** The CAMPD unit-outage overlay was *zeroing* the lone
Merrimack-class COAL unit (Plant_Code 2364) and the lone ST_GAS unit, so the
temperature floor's `frac × available` bound — and any economic dispatch — was
structurally capped at ~0 and **no** downstream lever (floor, daily-basis
economics, or the gas-coldsnap derate) could recover the coal/steam energy. Two
overlay bugs, both specific to a winter cold-snap peaker: (1) the outage detector
defines an outage as a sustained CF < 5% gap ≥ 2 days — a rule built for
*baseload* coal/CC — so for a unit that runs only on cold snaps (sub-10% annual
CF) it misreads the unit's **economic idleness** as a forced outage; (2) the
derate fraction `unit_capacity_mw / plant_capacity_mw` is taken against the 108 MW
model bin while the CSV's unit capacities are the real ~460 MW Merrimack plant
(units 1+2 = 113.6 + 345.6 MW), so a *single* coal-unit "outage" over-derates the
bin past full and clips availability to zero. Measured directly: **Merrimack COAL
availability was 0 of 8760 h in 2024** (a unit that actually generated 0.24 TWh),
3% of hours in 2023, 22% in 2025. The fix **exempts** the two floor classes
(COAL, ST_GAS) from the unit-outage overlay when the temperature floor governs
them — exactly as `ct_mustrun_per_plant` exempts its reliability-floor units from
the WEFOR/planned-outage derate — because the floor's commitment fraction is
regressed from each unit's *own* measured CAMPD CF, which already nets out real
maintenance downtime; re-applying the CF-gap overlay on top double-counts it.
This is a **correctness fix, not a fit**: the exemption is binary, its magnitude
is governed by the floor's unchanged measured-CF coefficients, and the model
still *under-runs* coal afterward (not pinned).

**Attribution** (apples-to-apples on identical current-main code, no-fix control
`neiso_39_nofix_control_3yr` with `--no-neiso-floor-outage-exempt`): coal
grid-delivered 0.006/0.000/0.043 → **0.058/0.113/0.234 TWh** (the 2024 control of
exactly 0.000 is the bug made visible); ST_GAS recovers too; gas family / mean
LMP / CO2 / CC_REGULAR all held or improved (CC_REGULAR slightly *lower*, helping
the C1 item) — a Pareto fix.

**Rejected this session:** the `neiso_gas_coldsnap_derate` lever (the candidate
structural lever for the residual broad-winter coal) is **byte-identical** to this
keeper on coal/gas/price across all three years (`neiso_probe_coldsnap_derate`).
It fires (72/144/304 cold-window hours, frac up to the 0.20 cap) but NEISO is not
capacity- or reserve-short even on cold snaps — the ~6.8 GW dual-fuel fleet stays
available on oil — so removing a small gas slice neither lifts the price nor pulls
in coal. It stays **default-OFF** (never enabled in this keeper), confirming
neiso-37's finding.

Headline (model vs actual): gas family 53.39/57.89/60.67 vs EIA-930
52.75/56.91/59.76 (+1.2%/+1.7%/+1.5%, C2 PASS); system mean LMP
34.62/39.10/68.29 vs RT 35.70/39.50/65.89 (−3.0%/−1.0%/+3.6%, C3a PASS);
CO2 −0.5%/−0.3%/+3.3% vs eGRID (C5a PASS — 2025 +3.3% is marginally above
neiso-37's +2.4% because the recovered coal adds ~0.1 Mt, still in band).

## The three carried accepted caveats

### 1. C1 CC_REGULAR gas-vs-OTHER fold-in categorization — HARD (2023 & 2024)
- 2023: model 51.61 vs deflated EIA-930 50.63 TWh (+0.98 TWh); 2024: 56.13 vs
  54.66 TWh (+1.47 TWh).
- The gas **family** is in-band (C2 PASS). The per-class C1 gate trips because the
  EIA-930 "Natural Gas" cell is deflated by the ~1.6 TWh of geothermal+biomass
  NEISO folds into it (`reconcile_vintage_classes`); the model books that
  OTHER/biomass residual as its own measured must-run rows and serves the
  un-foldable remainder with marginal CC, so ~1 TWh lands on CC_REGULAR. This is
  the EIA-923-vs-EIA-930 OTHER categorization difference, now visible per-class
  under the bidirectional reconcile. **Closable only by reconciling the OTHER/NG
  fold-in on both sides — never by injecting the residual or scaling CC to the
  deflated benchmark (that is fitting).** This is the single accepted HARD caveat.
- The availability fix slightly *lowers* CC_REGULAR (the recovered coal displaces
  a little marginal gas), so the item is marginally smaller than neiso-37's
  (+1.05/+1.61 → +0.98/+1.47 TWh). `neiso-37` was the first NEISO bundle scored
  against the deflated benchmark; the prior `neiso-33`/`neiso-36` slim bundles
  predated the reconcile and masked it.

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
- model 0.72 vs actual 2.08 TWh (−65.5%).
- Arbitrage throughput tracks the peak-to-trough price spread, compressed because
  the LP caps the cold-hour tail at oil-parity (see #2). The reserve co-opt and
  gas-availability derate built this session do not widen the spread in the
  backcast (`reserve_price=0`), and the Merrimack availability fix does not touch
  the price spread, so this is **not** a storage-model error — it closes only when
  the winter fuel-inventory scarcity rent is recovered via the forward-faithful
  oil-burn-budget constraint, never via a storage or offer tune.

## The newly documented caveat (non-gating)

### 4. Coal + ST_GAS winter-energy under-run — MODEL MISS (structural)
- COAL_BIT model 0.058/0.113/0.234 vs actual 0.181/0.238/0.271 TWh; ST_GAS
  0.051/0.021/0.029 vs 0.206/0.107/0.304 TWh. Each per-class miss is **within the
  C1 per-class absolute band** (±~0.96–1.04 TWh), so it does **not** trip the C1
  gate — but it is a real, persistent under-run, previously undocumented and
  largely masked by the availability bug fixed in this keeper.
- The availability fix removed a definite overlay bug that had *erased* the energy
  (control coal 0.006/0.000/0.043 → 0.058/0.113/0.234), but a residual under-run
  remains, **largest in the low-gas years 2023/2024**. Mechanism: the energy-only
  LP runs Merrimack and the lone steam unit only at the temperature-floor
  commitment plus the few hours delivered gas is dear enough to put coal
  (HR 11.337 × coal fuel ≈ $30–45/MWh) genuinely in merit; in 2023/24 Henry Hub
  was $2.5/$2.2 and gas-CC out-competed coal most of the winter, so the LP holds
  coal near the floor. The real units ran more — a winter fuel-security /
  local-reliability commitment (oil/coal/steam held online against multi-day
  cold-snap gas-deliverability risk) the cost-based merit order cannot see: the
  **same** unobserved winter-scarcity driver behind #2 (price tail) and #3
  (storage spread).
- The candidate forward-faithful lever (`neiso_gas_coldsnap_derate`) was tested
  and does **not** close it (byte-identical — NEISO not reserve-short). Closable
  only by the documented future build that makes the winter oil/coal reliability
  commitment forward-reproducible (a fuel-inventory / seasonal-reliability
  constraint whose shadow price lands on the tightest cold hours), **never** by
  cranking the floor slope/cap (regressed from measured CF, must not be tuned to a
  TWh residual) or an offer adder. The **108 MW model bin** for Merrimack (vs the
  real ~460 MW plant) also bounds the maximum recoverable coal — a separate
  fleet-representation item noted for follow-up.

## Hydro note (required measured flags)

Hydro 8.70/7.33/5.11 TWh comes from the EIA-930 monthly budget pin plus a 2024
plant-capacity backfill: the 2025 EIA-923 vintage lists only 5 of ~166 hydro
plants, so without `--hydro-backfill-year 2024 --hydro-eia930-monthly` the LP
burns ~5 TWh of phantom gas. Both flags are required and both are measured inputs.

## Reproduce

```
python scripts/calibration_verdict.py results/calibration/neiso_40_floor_outage_exempt_3yr

# Solve from scratch (neiso_temp_reliability_floor AND neiso_floor_outage_exempt
# are both default-ON for NEISO; the explicit flag only records it in run_config):
python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025 \
  --commitment --hydro-backfill-year 2024 --hydro-eia930-monthly --gas-hub-basis-daily \
  --neiso-floor-outage-exempt

# No-fix control (the availability bug made visible: 2024 coal = 0.000 TWh):
python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025 \
  --commitment --hydro-backfill-year 2024 --hydro-eia930-monthly --gas-hub-basis-daily \
  --no-neiso-floor-outage-exempt --out-dir results/calibration/neiso_nofix_control
```
