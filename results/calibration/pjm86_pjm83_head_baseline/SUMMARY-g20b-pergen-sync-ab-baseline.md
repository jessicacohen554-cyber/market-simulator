# PJM 86 — pjm-83 keeper recipe re-solved at HEAD (A/B baseline)

**Probe (not a keeper decision on its own). Keeper stays pjm-83-srmc-reground.**
Full span 2023–2025, one bundle, years sequential. The flag-off partner of
`pjm87_pergen_oppcost`'s per-gen opportunity-cost co-opt A/B, solved on the
same data tree (regenerated `data/clean` + the per-BA EIA-930 PJM demand
rewire, this session).

## What was run

pjm-83 keeper recipe **verbatim** — no mechanism deltas. Exists so the
pjm-87 A/B is single-mechanism (CLAUDE.md rule 19): any move vs the
*committed* pjm-83 bundle is the data tree (demand-profile clean-partition
regen + the per-BA PJM demand rewire), not the reserve mechanism; any move
vs *this* bundle is exactly `pjm_reserve_pergen` + `pjm_reserve_pergen_sync`.

## Result — confirms the known non-fire, same-tree

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| reserve dual > 0 (h) | **0** | **0** | **0** |
| demand-wtd LMP mean ($) | 29.47 | 28.00 | 38.12 |
| demand-wtd LMP max ($) | 58.8 | 124.6 | 102.4 |
| zonal max ($) | 63.0 | 309.8 | 173.7 |

Reserve dual is $0 in all 26,280 hours — the pjm-83/pjm-84/pjm-85 zone-
aggregate-cap result reproduces exactly, confirming the same-tree baseline
is a clean comparison point for pjm-87.

## A/B vs pjm-87 (per-gen opportunity-cost co-opt)

Full C1–C8 verdict (`calibration_verdict.py`) is **criterion-identical**
between this baseline and pjm-87 — no PASS/FAIL/CAVEAT status differs on
any criterion, including C3c (price tail), which FAILs in both. Fuel-mix
(C1) TWh deltas are ≤0.03 TWh/yr per class (CT_PEAKER moves ≤0.01 TWh/yr
either direction) — pjm-87's reserve co-opt does not measurably redispatch
energy at this magnitude. See `pjm87_pergen_oppcost/SUMMARY-g20b-pergen-sync.md`
for the full result and interpretation.
