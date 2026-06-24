# pjm 49 seam-hr-measured — per-seam interchange diagnosis

**Change:** `NeighborInterface.hr_by_year` re-anchors the PJM reference-price
seam to each neighbor's *measured* realized annual-mean LMP per backcast year
(MISO, NYISO), replacing the single 3-year-mean `marginal_heat_rate`. Derived by
`scripts/derive_neighbor_hr_by_year.py`. Forecast years (no entry) fall back to
the structural HR → byte-identical. Rule #12 (measured > estimate).

| neighbor | structural HR | hr_by_year 2023/24/25 |
|----------|---------------|------------------------|
| MISO     | 12.9          | 12.38 / 13.92 / 12.03  |
| NYISO    | 13.1          |  9.66 / 12.92 / 14.67  |
| Carolinas| 13.5 (est.)   | — (no measured LMP)    |

After the fix each seam's constructed reference reproduces the measured neighbor
LMP within rounding (e.g. MISO 2025 $46.0 → $42.9; NYISO 2023 $41.1 → $30.3).

## Result: structurally correct, headline NOT improved

Net interchange (TWh, + = net export), model vs EIA-930 target:

| year | baseline (pjm 48) | hr-fix | target | gas % |
|------|-------------------|--------|--------|-------|
| 2023 | +42.8             | +27.7  | +40.0  | +2.7 (was +5.6) |
| 2024 | +27.8             | +36.6  | +32.7  | +9.0 (was +7.4) |
| 2025 | +57.4             | +53.5  | +18.0  | +11.4 (was +12.1) |

Net-interchange MAE **17.3 vs 15.7 TWh baseline** — slightly worse. Per rule #12
the measured anchor stays in; the worse fit exposes the real cause.

## Root cause: per-seam STRUCTURE (PJM Data Miner per-tie, blind to the LP)

Net export by seam, measured (PJM `import_export_act_sch_interchange`) vs model:

| seam | 2023 meas | 2023 model | 2025 meas | 2025 model | error |
|------|-----------|------------|-----------|------------|-------|
| MISO       | +35.3 | +16.1 | +24.6 | +16.8 | model **under-exports** the biggest real export seam |
| NYISO      | +18.5 | +3.8  | +21.9 | +26.3 | under 2023, over 2025 (NYC-congestion-inflated system avg) |
| Carolinas  | −5.4  | +7.7  | −5.9  | +10.4 | model **wrong direction** (+13..+16), every year |
| TVA/LGEE   | −8.4  | 0     | −7.7  | 0     | **seam not modeled** (~−8 import missing) |

The old over-priced NYISO-2023 seam (ref $41 vs measured $30, +36%) was silently
inflating 2023 export and masking the model's structural under-export there; the
measured anchor removes the mask.

## Measured-source basis gap (2025 only)

EIA-930 PJM net interchange = **+18.0** TWh in 2025, but PJM's OWN per-tie
scheduled sum (all ties, Data Miner) = **+32.9** TWh — a ~15 TWh gap between two
measured sources. In 2023/2024 the two agree (+40.0/+32.9 ≈ EIA-930). No seam
model can reconcile both bases in 2025; document as a measured-input limitation.

## Next thread (in priority order)

1. **Carolinas direction** — biggest, most consistent error (+13..+16 TWh wrong
   sign, all years). Needs a measured Duke/SERC price (FERC-714 hourly system
   lambda) to anchor below PJM without flow-tuning (rule #11 forbids tuning the
   HR to the net-MWh target). HR 13.5 is currently the *highest* of all PJM
   neighbors despite the Carolinas being a cheaper region PJM net-imports from.
2. **Add the TVA/LGEE import seam** — ~8 TWh/yr of unmodeled import.
3. **NYISO border price** — anchor to the PJM-NY (west-NY) border LMP, not the
   NYC-inflated system average, so 2025 NY export stops over-clearing.
4. **MISO under-export** — even at the measured MISO price the model under-clears
   the +25..+35 TWh real export; the annual-mean anchor is too blunt vs the real
   hourly border spreads. Likely needs hourly border anchoring.
