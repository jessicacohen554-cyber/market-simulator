# NYISO 45 — measured-run fast-start amortization + generator-level oil screen (registered, NOT promoted)

nyiso-44 (winter spread + Algonquin ceiling + oil-attribution basis fix +
fast-start amortization) with the two measured mechanisms that ground the CT
offer level left open by commit 0c6c833:

1. **Fast-start amortization v3** (`--tranche-startup-measured-runs`): the
   simple-cycle CT tranches amortize the NREL start cost over the
   CAMPD-measured median start-to-stop run length
   (`scripts/derive_campd_ct_run_lengths.py` →
   `data/raw/_processed-legacy/campd_ct_run_lengths_NYISO.csv`, pooled
   2023–25; per-plant medians 2–9 h, ISO-class fallback 4 h) as the
   amortization-horizon **ceiling** — the endogenous P0 run may only shorten
   it. This removes the v2 circularity nyiso-44 documented (too-cheap offers
   → long P0 blocks → ≈0 markup → the lever self-disables) and is how real
   GT offers form (start recovery over the ex-ante expected run). $2–10/MWh
   of fuel-price-invariant commitment content on every CT tranche.
2. **Generator-level EIA-860 oil-primary screen** (`--oil-primary-bin-fuel`):
   non-ERCOT ISOs resolve the oil-primary set from the raw EIA-860 generator
   sheet's Energy-Source-1 capacity majority (DFO/RFO/KER/JF over GT/IC)
   instead of the ERCOT-only plant registry. **Verified clean:** every NYISO
   gas-CT bin is NG-primary at the generator level — the per-plant fleet
   path already routes KER/DFO-primary units (Holtsville, Wading River,
   Glenwood 2514, Shoreham 2518, …) to raw `oil` units, so the screen flips
   zero NYISO bins. Kerosene mispricing is NOT the CT over-run; the screen
   stands as the flag's generator-level grounding (rule #1, measured basis).

## Result (vs nyiso-44)

- **CT_PEAKER 2024: 4.75 → 4.54 TWh** (actual 2.13); 2023 3.76 / 2025 4.32.
- **C1-2024 ST_GAS: −3.35 → −3.31 TWh — still the HARD FAIL** (model 7.76 vs
  11.07). The CT reduction cleared to CC/imports, not steam; the remaining
  over-run (Bayonne / Equus / Edgewood / Glenwood-Landing 2001–04 LM6000s
  near-baseload on Transco Z6 hub gas) is the ledgered **LI/NYC LDC
  citygate / interruptible delivered-gas premium** — the open data ask.
- **C3a −14.4 / −14.2 / −12.4%** (44: −15.4/−14.9/−13.0) and
  **C3b 0.199 / 0.194 / 0.191** (44: 0.207/0.201/0.195) — the best NYISO
  price scores to date, from honest commitment-cost content only.
- C2-2025 gas, C5a CO2 (−2.7/−5.5/−3.9%), C4, C6 all PASS. C3c 0/0/7h
  unchanged (ledgered frontier).
- **First NYISO bundle to score C7/C8** (`legitimacy_diagnostics.json`
  committed): C7-2024 CT_PEAKER off-peak CV ratio 0.424 (< 0.5) and C8
  forced shares (CT_PEAKER 22.6–28.4% vs 10% cap; ST_GAS 34.0/41.5% in
  2025/2024 vs 30% cap) FAIL — the nyiso-33/34 temperature reliability
  floors' forced energy, now first-class-scored open root causes (rule #20;
  not ledgerable). See `calibration_attestation.json` `_open_items`.

Determination: **NOT-YET** (C1-2024 + C7 + C8 HARD FAILs; C3a/b/c ledgered
caveats exceed the soft budget). Keeper stays
`2026-07-03-nyiso-41-hub-prices`.

## Reproduce

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --nyiso-import-hub-prices --nyiso-iroquois-winter-spread \
  --tranche-startup-amortization --tranche-startup-measured-runs \
  --oil-primary-bin-fuel \
  --out-dir results/calibration/nyiso45_measuredruns
```
