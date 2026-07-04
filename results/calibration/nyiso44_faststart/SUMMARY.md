# NYISO 44 — fast-start tranche pricing probe (registered, NOT promoted)

nyiso-43 (winter spread + Algonquin ceiling + oil-attribution basis fix; see
`results/calibration/nyiso43_ceiling_oilbasis/SUMMARY.md`) plus
`--tranche-startup-amortization` — the ISO-NE Order-825 fast-start pricing
analogue (NREL start costs on the fast-start-capable CT tranches, amortized
into P1 bids by each tranche's own P0 run lengths). NYISO's real market runs
the same structure (GT hybrid / fast-start pricing), so the lever is real,
measured-cost structure with no residual input.

**Probe finding:** the amortization moves CT_PEAKER only 4.90 → 4.75 TWh
(2024; actual 2.13) — with the de-leaked neutral econ bands (commit 0c6c833)
the P0 base-cost pass runs the CTs in long blocks, so the per-MWh amortized
start cost is small. The lever adds honest commitment-cost price content
(C3a −16.2/−15.4/−13.5 → **−15.4/−14.9/−13.0%**; C3b 0.214/0.206/0.200 →
**0.207/0.201/0.195**) but cannot substitute for the missing NYISO CT
offer-level grounding. **C1-2024 ST_GAS −3.35 TWh still FAILs** (MODEL MISS,
not ledgerable) — the blocking, repo-level open item: every NYISO solve on
current main fails it, including a re-solve of the keeper-41 config itself
(verified: CT 4.69 / ST 7.65). C2-2025 −0.1%, C5a −2.6/−5.4/−3.8% all PASS
as in nyiso-43.

Determination: **NOT-YET** (C1-2024 FAIL). Keeper stays
`2026-07-03-nyiso-41-hub-prices` (solved pre-de-leak; its committed artifacts
stand, but it is no longer reproducible on main until the CT offer level is
grounded — closure candidates in the attestation `_open_items`).

## Reproduce

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --nyiso-import-hub-prices --nyiso-iroquois-winter-spread \
  --tranche-startup-amortization \
  --out-dir results/calibration/nyiso44_faststart
```
