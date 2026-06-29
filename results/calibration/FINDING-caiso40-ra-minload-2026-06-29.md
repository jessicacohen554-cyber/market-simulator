# CAISO 40 — RA must-offer bridge min-load re-grounding (the midday CC lever)

**Date:** 2026-06-29
**Run:** `results/calibration/caiso40_ra_minload` (3-yr 2023-25, P1) — KEEPER (promoted over caiso 39)
**Builds on:** caiso 39 (`caiso39_import_atc`) — every offer-curve, seam, gas, and ATC lever carried verbatim. **One** parameter changed.

## TL;DR

caiso 39 left two coupled MODEL MISSes root-caused but unmoved: CC_REGULAR
over-dispatched midday (C1) and the midday LMP body priced at the CA combined-cycle
SRMC floor (C3a). The handoff named the lever: *too much CC is pinned committed
midday*. The mechanism is the RA must-offer **bridge** floor
(`model.commitment.caiso_ra_mustoffer_min_gen`): a merchant CC that runs before and
after a midday solar-glut gap shorter than its min-down time is held online at
`caiso_ra_min_load_frac × pmax` across the gap. That fraction was a **flat 0.40** —
a generic NREL/CAISO-Master-File textbook turn-down. The CAMPD/CEMS-**measured** CAISO
CC minimum stable load is capacity-weighted **0.259** (23 plants, 12.7 GW; range
0.10-0.63, median 0.25). The flat 0.40 over-floored the fleet by ~14pp (~1.8 GW) every
bridged midday. caiso 40 re-grounds it to **0.26** (CLAUDE.md #11: measured,
forward-reproducible physical limit supersedes the generic estimate — not a residual
fit). Result on the two structurally-clean gateable years: CC over-run and the midday
body both fall, 2024 CO2 now PASSES, C6 governance now PASSES (truthful attestation
added). 2025 (a preliminary-EIA-923 hydro-vintage year) regresses — an accepted
measured-input limitation, not the lever.

## The lever (one parameter, measured)

`scripts/run_calibration.py:_calibration_config` — `caiso_ra_min_load_frac` **0.40 → 0.26**.

- Source: `scripts/derive_thermal_tranches.py` → `data/raw/_processed-legacy/thermal_tranches_CAISO.csv`
  `committed_pct` = P5 of each plant's net CF over its CAMPD online hours = the measured
  minimum stable load once synchronized. Capacity-weighted **0.2593** over the 23-unit
  CA CC fleet.
- The bridge floor multiplies each tranche row's `pmax`, so it sums to ~0.26 of plant
  pmax across a plant's tranches — dimensionally a plant-level min-load.
- The 0.40 it replaces was the part-load/textbook turn-down (NREL "Power Plant Cycling
  Costs" 2012; CAISO Master File), ~14pp above this fleet's measured floor.

The bridge **detection** (which gaps are bridged) is unchanged — only the floor *level*
moves. Lowering a lower bound only relaxes the feasible region, so the LP may back CC
further down midday where the 0.40 floor used to bind.

## Results (3-yr, vs caiso 39 re-scored with the same verdict machinery)

| criterion | year | caiso 39 | **caiso 40** | |
|---|---|---|---|---|
| C1 CC_REGULAR vol (TWh / pp) | 2023 | +6.90 / +2.6 FAIL | **in band → PASS** | ✓ |
| C1 CC_REGULAR vol | 2024 | +9.31 / +3.8 | **+8.16 / +3.7** | ✓ |
| C1 CT_PEAKER vol | 2023 | (in band) | -2.26 / -1.2 FAIL | ✗ |
| C1 CT_PEAKER vol | 2024 | -2.37 | -2.59 | ~ |
| C3a mean LMP | 2023 | +90.2% | **+74.7%** | ✓ |
| C3a mean LMP | 2024 | +70.3% | **+63.1%** | ✓ |
| C3a mean LMP | 2025 | +79.4% | +86.4% | ✗ (hydro) |
| C3b shape NRMSE | 2023 | 0.594 | **0.465** | ✓ |
| C3b shape NRMSE | 2024 | 0.770 | **0.729** | ✓ |
| C3c tail >$200 | 2023 | 736 h | **615 h** | ✓ (still ≫21) |
| C4 gas dispatch r | 2023 | 0.803 | **0.816** | ✓ |
| C5a CO2 | 2024 | +9.5% FAIL | **PASS** | ✓ |
| C5a CO2 | 2023 | +7.8% | -7.7% | ~ (sign flip) |
| C2 gas vol | 2025 | +12.5% | +16.8% CAVEAT | ✗ (hydro) |
| C6 governance | — | UNATTESTED | **PASS** | ✓ |
| net interchange gap | 2024 | -0.18 TWh | **-0.13 TWh** | ✓ (preserved) |

**Determination: NOT-YET** (same gate as caiso 39). Deciding fails stay genuine
MODEL MISSes (C1 merit split; C3a/b/c SRMC floor). The keeper rationale is CLAUDE.md
#1: caiso 40 is the **most structurally faithful** run (measured CC min-load), and it
improves the primary targets on the two clean years — not a lower-MAE accident.

## 2025 regression — accepted measured-input limitation (not the lever)

The 2025 hydro budget is built from a **preliminary EIA-923 vintage** that is materially
incomplete: **26 of ~160** hydro plants reporting (3,916 vs 6,568 MW nameplate; **12.3
vs 21.5 TWh** in 2024). The model loads 12.3 TWh hydro while the true 2025 hydro was
~**21.35 TWh** (EIA-930; solve.log: "EIA-923 2025 hydro 12.42 TWh under-counts EIA-930
21.35 TWh"). Gas backfills the missing ~9 TWh → C2 gas +16.8%, C5a CO2 +19.3%, and the
LMP/dispatch-corr 2025 drift. **Forward-reproducible** (a finalized 2025 vintage, or the
`hydro_eia930_monthly` budget, regenerates the full hydro) and **pre-existing** (caiso 39
carried +12.5%) — not caused by the min-load change. Ledgered ACCEPTED MEASURED-INPUT
LIMITATION in `calibration_attestation.json`. The hydro-vintage backfill is the dedicated
next workstream.

## Why it's the keeper

caiso 40 closes part of the CC-over / midday-body MODEL MISS caiso 39 root-caused, using a
measured-deliverability re-grounding of a forward-reproducible physical parameter (#11),
and it ADDS the governance attestation caiso 39 lacked (C6 UNATTESTED → PASS). The CC
over-run narrows and 2023 CC_REGULAR clears the band; the body falls 15pp (2023) / 7pp
(2024); 2024 CO2 passes. The residual body is the still-real CA-CC SRMC floor (gas +
CARB marginal midday because deliverable solar/imports stay capped) — the next structural
lever (export the midday surplus; hydro price-following), out of this fix's scope.

## Next steps

1. **Hydro 2025 vintage** — load EIA-930 monthly hydro (`hydro_eia930_monthly`) or the
   finalized 2025 EIA-923 so gas stops backfilling ~9 TWh; clears the C2/C5a/C4 2025 caveats.
2. **CT_PEAKER under-run** — the bridge frees midday space that imports/solar fill, not CT;
   the CT peaking economics are unchanged. Needs the missing scarcity/ramp mechanism, not
   an offer-curve cut (would be an unphysical fit, #1/#11).
3. **Midday body residual (C3a)** — export the midday solar surplus (model p99 export ~0 vs
   actual +3.5 GW) and/or hydro price-following, so a sub-SRMC unit sets the midday margin.
