# NYISO 43 — winter spread promoted: Algonquin ceiling + oil-attribution basis fix

## What this run is

The nyiso-41 keeper config plus the nyiso-42 reconciled Iroquois winter spread
(`--nyiso-iroquois-winter-spread`), with the two root causes that blocked the
spread's promotion (run-42 items E1/E2) fixed at their source — both measured,
neither touches an offer curve or reads a residual:

1. **Algonquin-Citygate monthly ceiling on the reconciled Iroquois reference**
   (`fuel.nyiso_reconciled_reference_monthly`, rule #14). The AGT-weighted
   re-allocation of the SOM *annual* Iroquois−Transco spread has no per-month
   magnitude anchor, and in the most-loaded months it out-priced the New
   England complex Z2 physically delivers into: Feb-2023 reconstruction
   $13.21/MMBtu vs the measured $8.13 Algonquin month, Jan-2024 $8.60 vs
   $7.68, Jan-2025 $18.60 vs $16.92. Each month is now capped at the measured
   Algonquin Citygate monthly (Henry Hub month + the same measured NEISO basis
   row the weights come from — the series the NEISO keeper itself prices on),
   floored at the committed flat construction so the cap only ever shaves
   scarcity-month excess. The shaved excess re-enters as a year-round *base*
   differential water-filled into months with ceiling headroom, preserving
   the measured SOM ANNUAL spread exactly: the annual total is itself a
   measured datum, and the ceiling proves the scarcity months alone cannot
   carry it — the remainder is by construction the non-scarcity Z2 base
   premium (Waddington/TransCanada supply pricing), ~+$0.8/MMBtu across
   2023's unconstrained months, ~+$0.1-0.2 in 2024/2025. A reconciliation of
   THREE measured series (SOM annual + AGT scarcity shape + Algonquin
   ceiling), no fitted constant. Dec-2024 ($7.50 vs ALG $9.13) and Dec-2025
   ($12.85 vs $14.90) sit *below* the ceiling — their winter level is
   allocation-funded only, unchanged in kind from run-42.

2. **NYISO dual-fuel oil re-attribution turned off — a scoring-basis bug fix**
   (`run_calibration_full.py`, restoring the documented `ScenarioConfig`
   NEISO-only spec). The daily-basis override channel had silently enabled
   `dual_fuel_oil_reattribution` for every ISO since NYISO adopted
   `--gas-hub-basis-daily`, relabelling parity-switched generator-hours
   gas→oil in the scored dispatch. That relabel exists so the model matches
   the benchmark feed's fuel attribution — and only ISNE's EIA-930 feed
   attributes that way. The NYIS feed demonstrably does not: Jan-2025 parity
   switching relabelled 0.80 TWh while the measured NYIS `NG: OIL` carried
   0.031 TWh (2025 total: model 1.55 TWh under the spread vs 0.18 measured);
   conversely 2023 shows 2.17 TWh of NYIS OIL against a 0.42 TWh EIA-923 oil
   class — a static plant-primary attribution that parity hours cannot
   reproduce in either direction. The relabel was therefore scoring a basis
   mismatch against the HARD C2 gas family, not a dispatch error — it was the
   entire run-42 "E2" C2-2025 FAIL (gas −2.5%): the winter gas never left the
   dispatch, it was relabelled. Pricing physics are untouched — dual-fuel
   units still cap at `min(gas, oil)` (`dual_fuel_switching` stays on).

## Run-42 carry-forward items resolved this session

- **E2 (2025 gas burn "suppression") — root-caused, fixed.** The nyiso-41/42
  dispatch diff shows the dearer reconciled winter gas moved 2025 gas
  −0.276 (Feb) / −0.213 (Dec) / −0.086 (Jan) TWh while oil re-attribution
  rose +0.273 / +0.213 / +0.03 — a relabel, not displacement (imports moved
  ≤0.07 TWh/month inside the recon band; shoulder months gained +0.05-0.07
  from the correctly-cheaper eastern gas). Fix #2 above.
- **E3 (Jan-2024 / Feb-2023 winter overshoots) — verified against a measured
  anchor, fixed.** Both months' reconstructions exceeded the measured
  Algonquin Citygate ceiling of the complex (above). Fix #1. Dec-2025 sits
  below the ceiling; its residual is not a reconstruction-magnitude artifact
  the measured data can correct.
- **E1 (shoulder-month undershoot) — decomposed; remains the ledgered
  frontier.** With the spread isolating winter, the Apr-2023 diagnosis shows
  two components: (a) the **east level** — model east zones clear ~$19.9 vs
  actual ~$26 (implied marginal HR ~11.4 vs ~15): the competitive-offer
  markup / reserve-uplift content the run-28/29 probes established cannot be
  grounded without offer disclosure, plus RT reserve scarcity the static
  published requirements (NYCA 2,620/1,310/655; East 1,200; SENY 1,100; NYC
  1,000/500 MW) never bind against idle-capacity headroom credit — the
  `data/raw/NYISO-AS` series carry measured AS *prices*, not a measured
  condition-varying *requirement*, so this stays data-blocked; and (b) an
  **upstate collapse** — Upstate_West prices at the wind margin ($1.4) in
  ~75% of April-2023 hours behind the measured 1,450 MW Central-East TTC
  while the monthly EIA-930 reconciliation band pushes ~830 MW of the
  measured net imports through the upstate link (the NYC/LI node links,
  1,000+1,200 MW, cannot carry the measured net alone). Real upstate held
  ~$22-25 via gross two-way tie flows (IESO/PJM arbitrage) the single
  external node cannot represent without per-interface measured flows/ratings
  — NYISO ATC/TTC external-interface postings or EIA-930 per-DIBA NYIS
  interchange are the documented data ask (neither on disk; the public Gold
  Book redacts tie ratings). The model's zonal load split and in-state
  volumes check out against measured (UW April share 0.365 model vs 0.356
  measured; hydro/nuclear monthly within ±0.15 TWh where the 930 series is
  intact), so the undershoot is price-formation, not energy balance.

## Result (vs keeper 41 / probe 42 → this run)

<!-- FILLED AFTER SCORING -->

## Reproduce

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --nyiso-import-hub-prices --nyiso-iroquois-winter-spread \
  --out-dir results/calibration/nyiso43_ceiling_oilbasis
```

(The ceiling cap and the NEISO-only re-attribution gate are source changes in
this commit, not flags.)
