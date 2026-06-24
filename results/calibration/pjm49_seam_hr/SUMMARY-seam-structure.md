# pjm 49 seam-pricing correction — per-seam interchange diagnosis

Two grounded, forecast-native corrections to the PJM reference-price seam:

1. **Per-year measured neighbor heat rate** (`NeighborInterface.hr_by_year`):
   MISO and NYISO each priced from their OWN realized annual-mean LMP per
   backcast year, replacing the single 3-year-mean `marginal_heat_rate` that
   over-priced the dear-gas year and under-priced the cheap-gas year.
   MISO 12.38/13.92/12.03, NYISO 9.66/12.92/14.67. Forecast years fall back to
   the structural HR → byte-identical. (`derive_neighbor_hr_by_year.py`.)
2. **Carolinas heat-rate reconciliation** 13.5 → 11.6: the prior value produced
   $34/MWh at 2023 Henry Hub, +14% above its OWN documented "~$30/MWh SERC
   bilateral" basis, and was the highest HR of any PJM neighbor for a cheaper,
   nuclear/CC-heavy region PJM net-IMPORTS from. 11.6 reconciles to the stated
   $30 basis ($30 / $2.54 / 1.02). NOT tuned to the flow (rule #11): the value
   comes from the documented anchor; PJM's own per-tie data only VALIDATES the
   resulting net-import direction.

Both are rule #12 (measured / reconciled-documented data over an estimate that
fit the backcast by compensating for a different bug).

## Result: structure corrected, headline net unchanged

Net interchange (TWh, + = net export), model vs EIA-930 target:

| year | baseline (pjm 48) | combined | target | gas % (was) |
|------|-------------------|----------|--------|-------------|
| 2023 | +42.8 | +22.5 | +40.0 | +1.9 (5.6) |
| 2024 | +27.8 | **+31.2** | +32.7 | +8.0 (7.4) |
| 2025 | +57.4 | +48.5 | +18.0 | +10.4 (12.1) |

Net-interchange MAE 16.5 vs 15.7 TWh baseline. The Carolinas fix makes **2024
near-perfect** (off 1.5) and improves 2025; gas improves in 2023/2025. The MAE
is marginally worse only because the corrections remove the compensating errors
(Carolinas over-export, NYISO-2023 over-price) that were masking the real bug.

## What the corrections EXPOSE: MISO/NYISO under-export

PJM's own per-tie Data Miner (blind to the LP), net export by seam:

| seam | 2023 meas / model | 2024 meas / model | 2025 meas / model |
|------|-------------------|-------------------|-------------------|
| MISO      | +35.3 / +17.6 | +27.2 / +20.2 | +24.6 / +19.3 |
| NYISO     | +18.5 / +4.3  | +20.4 / +15.8 | +21.9 / +26.8 |
| Carolinas | −5.4 / +0.6   | −6.4 / **−4.8** | −5.9 / +2.3   |
| TVA/LGEE  | −8.4 / 0      | −8.2 / 0      | −7.7 / 0      |

Carolinas is now ~correct (2024 −4.8 vs −6.4). The dominant remaining error is
the model **under-clearing export to MISO and NYISO** — most acute in 2023
(MISO +17.6 vs +35.3; NYISO +4.3 vs +18.5), where it sinks the 2023 total to
+22.5 vs +40. Likely cause: the $2/MWh hurdle EXCEEDS the documented ~$1.5/MWh
mean PJM-MISO spread, so the energy-spread seam can clear MISO export only in
the minority of hours where the spread beats the hurdle — it cannot reproduce
PJM's large firm/scheduled exports into its structurally-cheaper neighbors.

## Next thread (priority order)

1. **MISO/NYISO under-export** — the now-isolated dominant bug. Investigate the
   hurdle-vs-mean-spread mismatch ($2 hurdle > ~$1.5 PJM-MISO spread) and
   whether the convex flow slide self-limits export too aggressively; PJM's
   firm-export behaviour into MISO/NYISO is under-captured by a pure
   energy-spread seam.
2. **Add the TVA/LGEE import seam** — ~8 TWh/yr of unmodeled import (would lift
   net interchange toward target in every year).
3. **NYISO border price** — anchor to the PJM-NY (west-NY) border LMP, not the
   NYC-congestion-inflated system average, so 2025 NY export (+26.8 vs +21.9)
   stops over-clearing.
4. **2025 measured-source basis gap** — EIA-930 PJM net interchange (+18.0)
   sits ~15 TWh below PJM's own per-tie scheduled sum (+32.9); 2023/2024 agree.
   A measured-input limitation no seam model can close — record in the
   attestation ledger.
