# NEISO calibration — best config so far

> **DETERMINATION (2026-07-06, scorer): NOT-YET — on the caveat budget alone**
> for the registered keeper `2026-07-06-neiso-49-stgas-netload` (bundle
> `results/calibration/neiso_stgas_netload`, years 2023/24/25; ablation twin
> `…-ablation`). **Zero criterion FAILs** — NEISO is the only ISO in that
> state; it is blocked purely by the caveat budget: hard 2 > 1 (C2 gas-2025
> preliminary vintage + C7 ST_GAS diurnal 2023/24) and soft 4 > 2 (C3a, C3b,
> C3c, C5b). This supersedes `neiso-48-ct-floor` (and the stale `neiso-38`
> text this file carried until 2026-07-06).

## What the keeper is

`neiso-49` = the `neiso-48` recipe (measured Algonquin/EIA-MA-citygate **daily**
gas-hub basis overlay + dual-fuel oil re-attribution + EIA-930-pinned hydro
budget with 2024 plant-capacity backfill + biomass/OTHER measured must-run +
historic CAMPD outage overlay + dual-limb temperature reliability floor +
floor-class outage exemption + post-solve ORDC scarcity overlay +
fast-start tranche startup amortization + CC_REGULAR econ band 1.00→1.15 +
the neiso-48 CT_PEAKER tmax-limb scrub) **plus two measured-grounded
structural changes** (2026-07-06):

1. **Connecticut ST_GAS `netload` reliability-commitment limb**
   (`reliability_floor_coeffs_NEISO.csv`): the rule-19 re-grounding of the two
   disabled, unidentified ST_GAS temperature limbs (tmax ρ=0.23, tmin n=8).
   ISO-NE commits the Montville legacy-steam fleet on **tight-system days —
   cold AND hot** (Feb-2023 blast; post-Mystic Jun–Aug 2024/25 heat; Jan/Dec
   2025); daily peak net-load unifies the driver (ρ 0.51, n 329; 90% of the
   100 committed days above the p70; median committed day = p93). Threshold
   p70 = 16.02 GW; floor 0.0336 = commit_frac 0.2796 × physical min-stable
   0.12; all-24h boiler gate, 48 h steam event bridging — the CAISO-CT
   netload-limb precedent. When Component B (`neiso_winter_fuel_mustrun`,
   default off) is co-armed it drops ST_GAS from its scope (rule 24).
2. **NEISO-measured offer bands** (`derive_campd_marginal_hr.py --iso NEISO`,
   the NYISO run-32 convention — measured marginal HR × the ISO's own CC reach
   ratio 1.223): ST_GAS 0.79/0.85/0.89 (a genuinely rising measured ramp),
   CC_CHP 1.15/1.17/1.19; CT_PEAKER econ bands stay neutral —
   measurement-AFFIRMED (NEISO CT marginal HR falls with load; the removed
   ERCOT 1.27→1.98 ramp had no NEISO basis); CT_CHP neutral (n=1).

Effect: **C7 ST_GAS 2025 D-1 passes for the first time** (profile_r 0.844,
cv_ratio 2.87); the 2023 off-peak CV collapse is fixed (35.4 → 4.6); D-2
ST_GAS forced share is 0.0 in all years (the floor is commitment scaffolding,
the dispatch is economic — model 2023 class energy 0.041 TWh ≈ actual 0.041).

## The carried caveats (the budget blockers)

- **C2 (hard):** 2025 gas family +3.0% vs corrected EIA-930 — the preliminary
  2025 EIA-923 vintage (57% reporting) forces the family fallback. Re-score
  when the final vintage lands (checked 2026-07-06: not landed). NOT closable
  by dispatch.
- **C7 (hard):** ST_GAS D-1 2023 (profile_r 0.49 — a real profile now, with a
  genuine midday-vs-evening event-day mis-phase; the keeper's old 0.619
  correlated a 13-hour spiky artifact) and 2024 (cv 0.0 — a flat-floor-only
  year: at $2.19 gas the unit clears no merit hours, the C3a
  price-depression family). Ledgered follow-ups: engine-vs-derivation
  net-load basis (engine flags 27/36/58 days vs ~110/yr on the EIA-930
  basis — notably tracking the actual committed-day counts 22/20/58); steam
  commitment integrality for the sub-min-stable LP sliver
  (`class_commitment_overrides` CAMPD-bin early-return wiring follow-up).
- **C3a/C3b (soft):** −8.3/−7.8% mean LMP (2023/24), 2024 shape NRMSE 0.169.
  The measured bands have now removed the offer-side excuse — the remaining
  depression is scarcity/price formation, not offer grounding.
- **C3c (soft):** 0 h > $300 all years (oil-parity cap; winter scarcity-price
  formation — the #1476 Component-B negative stands: NOT a commitment gap).
- **C5b (soft):** 2025 storage −56.3% (0.91 vs 2.08 TWh) — **deepened from
  −49.3% by neiso-49, disclosed**: the measured-cost steam tranche shaves the
  artificial evening peaks the PS fleet was arbitraging. Closes only
  downstream of scarcity-price formation; never via a storage/offer tune.

## Rejected / negative results on record

- Winter-fuel Component B (winter fuel-security must-run) — structurally
  faithful, **non-binding** (#1476): the fuel-secure fleet is tiny and already
  runs on cold days. Kept default-off; do not re-tune it at C1/C3c/C5b.
- Component A inventory cap — inert until scarcity formation raises the burn.
- `neiso_gas_coldsnap_derate` — byte-identical (NEISO not reserve-short
  2023–25). Default-off infrastructure for tighter forecast years.

## Hydro note (required measured flags)

The 2025 EIA-923 vintage lists only 5 of ~166 hydro plants; without
`--hydro-backfill-year 2024 --hydro-eia930-monthly` the LP burns ~5 TWh of
phantom gas. Both flags are measured inputs and required.

## Reproduce

```
python scripts/calibration_verdict.py results/calibration/neiso_stgas_netload

python scripts/run_calibration_full.py --iso NEISO --year 2023 2024 2025 \
  --commitment --reliability-floor --hydro-backfill-year 2024 \
  --hydro-eia930-monthly --gas-hub-basis-daily --scarcity-price-overlay \
  --tranche-startup-amortization \
  --out-dir results/calibration/neiso_stgas_netload
```
