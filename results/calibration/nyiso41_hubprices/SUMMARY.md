# NYISO 41 — measured-neighbor import pricing (new keeper)

## What this run is

The nyiso-39 keeper config on corrected measured gas data, plus ONE new
structural mechanism: `--nyiso-import-hub-prices`
(`transmission.inject_nyiso_import_hub_prices`). The priced import node's
`PJM_west` / `ISONE_tie` tranches reprice at the **measured hourly PJM /
ISO-NE Day-Ahead system LMP** + the $1 inter-control-area wheeling hurdle
(the same hurdle the PJM↔NYISO `NeighborInterface` spec carries); the residual
`import_scarcity` block takes the hourly max of the two; the `export_surplus`
sink the hourly min − hurdle (wash-free on a destination-blind single sink).
HQ/IESO contract tranches, the monthly EIA-930 reconciliation band, the HQ
firm floor and the 4,350 MW SIL are unchanged.

This replaces the static per-year `IMPORT_TRANCHES_BY_YEAR` ladder — which the
`neighbor_price` module itself documents as "a backcast fit — re-fitted per
year, blind to neighbor fundamentals" — with a measured neighbor
price-formation input (rule #12), the exact NYISO analogue of the accepted
`miso_pjm_lmp_import_pricing` and `caiso_import_hub_prices` mechanisms. The
fitted 2024 ladder (top $79.7) capped the modeled seam exactly when the real
seam repriced with the neighbors: model Dec-2024 mean $35.3 ≈ the $35.4
PJM_west constant while NEISO's measured month averaged $84.5.

## Corrected measured gas data (carried from nyiso-40)

1. **True-date daily quotes** (`fuel._transco_z6_daily_dated`): each measured
   Transco Z6 NY trading-day print lands on its actual calendar day (the prior
   even-spread put the Jan-2024 $23.90 cold-snap print on the 12th instead of
   the 16th and attenuated every peak). Mean-preserving per month.
2. **Monthly hub levels recomputed from the completed daily series**
   (`scripts/fetch_nyiso_gas_narrative.py`, NGWU narrative harvest run on the
   open-egress Actions runner): the committed monthly file's Dec-2024 read
   $2.45 against its own daily series' $3.30 mean (holiday-week archive gap);
   NYISO basis rows re-derived (Dec-2024 +0.16 → +1.00 $/MMBtu).

## Result (vs keeper 39 → this run)

- **C1 / C2 / C4 / C6 all PASS unchanged** (HARD gates clean; gas r high).
- **C3a mean LMP:** −15.6/−19.2/−13.2% → **−13.3/−13.4/−9.5%**.
- **C3b shape NRMSE:** 0.211/0.304/0.203 → **0.209/0.236/0.172**.
- **C3c tail:** 0h/0h/0h → 0h/0h/**7h** (>$300, 2025) — the first NYISO model
  tail hours ever, import-marginal at neighbor heat-wave DA prices.
- **C5a CO2:** 2024 slips to −7.1% (band ±7) — exposed by the corrected
  Dec-2024 hub level; root cause is the ledgered in-city steam under-run
  (ST_GAS −1.4 TWh ≈ −0.6 Mt of the −2.1 Mt gap), see the attestation.
- Determination: **NOT-YET** (soft caveats 4 > budget 2), all ledgered.

## The two remaining open items (both documented, neither closable honestly today)

1. **Eastern-NY winter hub level — DATA-BLOCKED (verified).** The Iroquois Z2
   reconstruction (Transco monthly + SOM *annual* spread) under-reads
   constrained winter months: Dec-2024 ~$4.0/MMBtu modeled vs the ~$9 New
   England complex the Z2 segment (a Connecticut trading point) physically
   trades in; Jan/Feb-2025 likewise. Worth ≈ −$25 (Dec-24) / −$19/−$24
   (Jan/Feb-25) of monthly LMP — the bulk of the residual C3a/C3b miss. The
   fetch workflow **verified no free source exists**: EIA NGWU compact table,
   printer-friendly (`ngpf.asp`) table and 146 weeks of narrative carry zero
   Iroquois prints 2023–2025; the NE dashboard has no data endpoint; NGI/ICE
   are paywalled. The open data ask is a licensed Iroquois Z2 daily/monthly
   series (or NYISO SOM monthly per-hub data).
2. **Reserve-scarcity / RT-adder frontier (ledgered since nyiso-29/31):** the
   co-opt's RCPF ladder cannot bind against idle-capacity headroom credit;
   the >$300 RT tail and the broad energy-only dual undershoot remain.

## Reproduce

nyiso-39 keeper flags + `--nyiso-import-hub-prices`:

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 2024 2025 \
  --gas-monthly-actuals --gas-hub-basis-overlay --gas-hub-basis-daily \
  --priced-interchange --energy-reserve-coopt \
  --nyiso-local-selfsupply --nyiso-firm-imports --nyiso-import-reconciliation \
  --nyiso-import-hub-prices --out-dir results/calibration/nyiso41_hubprices
```
