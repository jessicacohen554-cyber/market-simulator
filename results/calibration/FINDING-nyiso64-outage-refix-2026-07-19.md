# FINDING — nyiso-64 corrected-outage re-calibration: the phantom-outage compensation was MISSING EASTERN STRUCTURE, not offer level (2026-07-19)

**Status: keeper pointer advanced to `2026-07-13-nyiso-64-outage-refix` (owner-authorized
this session); determination NOT-YET on 2023 C3a/C3b only; frontier + calibration-complete
marker stay WITHDRAWN pending the named successor levers.**

Successor to `FINDING-neiso-nyiso-phantom-outage-reaudit-2026-07-19.md` (NYISO leg): the
nyiso-62 keeper flipped CALIBRATED-WITH-CAVEATS → NOT-YET when re-solved verbatim on the
corrected CAMPD unit-outage extract (1,598 → 2,641 rows). This lane diagnosed the root
cause and re-calibrated NYISO to the accurate envelope (rule 11: keep the accurate input,
fix the real compensating miscalibration).

## Root cause — what the stale extract was compensating for

The corrected extract adds ~1.4–1.5 GW average derate (up to ~11 GW on August peak days),
dominated by downstate ST_GAS (Port Jefferson, Astoria, Bowline, Roseton, Northport,
Barrett, Arthur Kill) + CC. Window-interior CEMS cross-check: **zero** running hours inside
any of the 2,641 windows (the extract is sound; apparent plant-level contradictions are
date-truncation edge slop of ≤1 day/side, e.g. Bowline 577 MW generating on its window's
start day, 2023-07-05).

Two real structural defects were exposed:

1. **The eastern AC seam landing was missing from the topology.**
   `IMPORT_NODE_LINKS["NYISO"]` funneled every AC seam MW through Upstate_West — BEHIND the
   measured pre-NY-Transco 2023 Central-East limit (monthly 1,450–2,725 MW) — while in
   reality the PJM Ramapo 345 kV ties (Zone G) and the ISO-NE eastern AC ties (Zones F/G)
   land ~2.5 GW EAST of Central-East. On the corrected (tighter) fleet the 2023 model
   starved the east: 227 hours >$20 over DA, eastern zones printing VOLL ($2,000) on
   July/August afternoons with the downstate HVDC links pinned at cap and the upstate
   external link NOT full (Central-East binding). Reality served those hours without the
   outaged units' energy (CEMS-verified) via eastern seam response (e.g. 2023-08-14 17:00
   actual net imports 4.55 GW vs model 2.65 GW). **Fix:** add the eastern landing
   (`Capital_Hudson` 1,600 MW — PJM Ramapo ~1,000 + NE eastern AC ~600; the
   MISO-Illinois/Indiana/East reconciled-split precedent). SIL 4,350 MW and the monthly
   EIA-930 reconciliation band unchanged — the split adds geography, not import energy.
   The Dec-2023 NY Transco upgrade (Central-East 1,750 → 2,850 MW) explains the year
   asymmetry: 2024/2025 had seam headroom and were nearly in-band even before the fix.

2. **The ST reliability-floor coefficients were derived on the stale availability
   denominator.** `derive_nyiso_st_reliability_floor.py` normalizes the measured
   when-available CF by availability *sourced from the unit-outage extract*: the stale
   extract overstated availability, so the measured floors were understated. Re-derived on
   the corrected extract (rule 23 — the coefficient source data changed): NYC base_24h
   0.391→0.496, evening base 0.432→0.533, cap 0.943→1.0(clamp); LI 0.436/0.572/0.815.
   This restores the ST_GAS commitment energy the stale-derived floors under-forced
   (the C1 2024 −3.36 TWh displacement). CT floors don't consume the extract (unchanged).

Zero new free parameters; the DOF ledger carries n_residual=5 unchanged.

## Result — `2026-07-13-nyiso-64-outage-refix` (full 2023–2025 bundle, rule 16)

| criterion | nyiso-63 (corrected, keeper recipe verbatim) | **nyiso-64 (refix)** |
|---|---|---|
| C1 fuel-mix | FAIL (2024 ST_GAS −3.36 TWh) | **PASS 14/14** |
| C3a mean LMP | FAIL 2023 +25.0% lw; DA 2024 +2.2%, 2025 +6.1% | FAIL 2023 **+19.8%** lw; DA 2024 **+0.6%**, 2025 **+4.8%** |
| C3b shape | FAIL 2023 NRMSE 0.385 | FAIL 2023 NRMSE **0.232** |
| C3c tail (RT) | 2023 50h vs 10h (5.0×) | 2023 **31h** vs 10h (3.1×, ledgered) |
| C2/C4/C5a/C6/C7/C8 | — | PASS (C5a commercial-band caveat 2025 +8.3%; C8 ST_GAS 38.7% grounded-above-budget clean pass) |

2023 August mean: 62.4 → 39.4 (DA actual 26.8). The invented VOLL prints collapse; the
remaining 26 >$200 hours are the real July/August heat events.

**LOYO (rule 22):** no fitted parameter; every year improves or holds (C3a 2023
+25.0→+19.8, 2024 +2.2→+0.6, 2025 +6.1→+4.8; C1 2024 FAIL→PASS with 14/14; C3b 2023
0.385→0.232). An `offer_curve_by_group` re-tune against the corrected fleet was considered
and **REJECTED on rule-22 grounds**: 2024/2025 sit at +0.6%/+4.8%, so lowering the (stale-
fleet-fitted) offer bands to close 2023's +19.8% would push the held-out years negative —
the remaining residual is year-specific structure, not an offer level.

## Determination & governance

- **NOT-YET** — the only fails are 2023 C3a (+19.8% lw / +17.3% DA) and C3b (0.232), both
  specific to the pre-NY-Transco Central-East regime. NOT ledgered to
  CALIBRATED-WITH-CAVEATS: two of the three residual drivers are missing model structure
  (below), which an "accepted measured-input limitation" label would misstate.
- **Keeper pointer advanced** nyiso-63 → nyiso-64 (owner authorization in-session:
  "if it's a keeper in your opinion promote"): strictly dominant on the accurate envelope —
  most structurally faithful run (rule 1), not lowest-MAE.
- **Frontier + calibration-complete marker stay WITHDRAWN.** The one-shot holdout stays
  blocked; the locked test (2019, H1-2026) is unspent.

## Named successor levers (expected order of leverage, all admissible)

1. **Measured per-tie eastern seam intake** — size the Capital_Hudson eastern AC landing
   from the Gold Book per-tie table + EIA-930 NYIS↔PJM/ISNE seam flows (the NEISO
   `derive_neiso_import_tranches` p98 method) instead of the conservative 1,600 MW
   aggregate.
2. **SCR/EDRP demand response** — ~1.3 GW registered ICAP special-case resources activated
   on the exact 2023 heat events; no model analogue (published enrollment, forward story).
3. **NYISO hydro reserve eligibility** — reality's East 10-min is heavily hydro/pumped-
   supplied; the co-opt is thermal+storage-only for NYISO (the CAISO design's NREL
   ramp-capability precedent applies).

## Files / reproduce

- Inputs (pushed): corrected floor coefficients
  (`data/raw/reference/reliability_floor_coeffs_NYISO.csv`), eastern seam split
  (`src/market_sim/config/interchange_config.py`).
- The corrected outage extract is DETERMINISTIC and regenerated per clone (previous-session
  precedent — too large for the API push path):
  `python scripts/data/derive_campd_unit_outages.py --iso NYISO` → 2,641 rows. **The
  committed csv is the STALE 1,598-row vintage until a git-push-capable machine commits the
  regenerated file — regenerate before ANY NYISO solve.**
- Bundle: `results/calibration/nyiso64_outage_refix` (replay of the nyiso-62 recipe on the
  corrected inputs; the mechanism changes are code/data-level, so `replay_keeper.py`
  picks them up with no `--set`).
- NYISO replay prerequisite on a fresh clone:
  `PYTHONPATH=. python scripts/data/curate_capacity_deliverability.py`.
