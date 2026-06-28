# CAISO Step 6 — Interchange Shape Diagnostic (2026-06-28)

**Run:** caiso 34 (`2026-06-28-caiso-34-ixshape`)
**Bundle:** `results/calibration/caiso_step6_ixshape`
**Branch:** `claude/caiso-step6-interchange-shape-ann78m`

## What changed vs step 5 (caiso 33)

Step 5 had all interchange levers OFF (static tranche ladder, fixed prices).
Step 6 re-enables the Lever E interchange mechanisms from caiso 32:

- `--caiso-per-hub-intertie` — splits WECC_import into WECC_PNW (COI/Malin →
  NP15) and WECC_DSW (Path-46/Palo Verde → SP15), each priced at its own
  measured WECC hub LMP + wheel + border carbon
- `--caiso-corridor-flow-limit` — per-(month × hour-of-day) p95 ATC envelope
  from measured EIA-930 BA-to-BA interchange, with asymmetric export caps
- `--caiso-import-gas-coupling` — desert-SW gas import tranches track the
  measured commodity-gas delta

All other step 5 mechanisms retained: RA must-offer commitment (structural,
replaces caiso 32's measured gas commitment floor), CT net-load reliability
drag, solar deliverability derate, CHP steam credit, gas monthly actuals.

**Not used:** `--gas-hub-basis-overlay` (superseded by `gas_monthly_actuals`),
`--caiso-gas-commitment-floor` (replaced by RA must-offer per Rule #1).

## Interchange shape results

### Summary table (P1, vs EIA-930)

| Year | Actual TWh | Model TWh | Err TWh | Dur RMSE | Diurnal r | Pk→Tr mdl | Pk→Tr act | Imp hrs mdl | Imp hrs act |
|------|-----------|-----------|---------|----------|-----------|-----------|-----------|-------------|-------------|
| 2023 | 28.87     | 37.57     | +8.70   | 2278 MW  | +0.97     | 2906 MW   | 5236 MW   | 98.0%       | 85.9%       |
| 2024 | 32.38     | 47.64     | +15.26  | 2878 MW  | +0.77     | 3799 MW   | 4596 MW   | 96.9%       | 89.0%       |
| 2025 | 36.16     | 51.93     | +15.77  | 1971 MW  | +0.75     | 4241 MW   | 4973 MW   | 99.5%       | 90.9%       |

### Improvement vs step 5 baseline

Step 5 (interchange OFF) had:
- Flat diurnal amplitude ~450–960 MW → now 2900–4200 MW (3–6× improvement)
- No diurnal correlation → now r = 0.75–0.97
- 100% import hours → now 97–99% (slight improvement; model still rarely exports)
- 2023 over-import ~15 TWh → now 8.7 TWh (improved); 2024/2025 unchanged at ~15–16 TWh

### Per-corridor breakdown (P1)

**2023** (static ladder — no measured hub data):
| Corridor | TWh   | Mean MW | Pk MW | Tr MW | Pk→Tr | Imp hrs |
|----------|-------|---------|-------|-------|-------|---------|
| WECC_DSW | +26.4 | +3012   | +3501 | +2237 | 1264  | 97.9%   |
| WECC_PNW | +11.2 | +1277   | +1963 | +337  | 1626  | 84.6%   |

**2024** (per-hub measured pricing active):
| Corridor | TWh   | Mean MW | Pk MW | Tr MW | Pk→Tr | Imp hrs |
|----------|-------|---------|-------|-------|-------|---------|
| WECC_DSW | +36.0 | +4112   | +5289 | +2620 | 2669  | 97.1%   |
| WECC_PNW | +11.6 | +1327   | +1987 | +594  | 1394  | 84.2%   |

DSW is the dominant corridor (3× PNW volume); nearly always importing. PNW
shows more diurnal variation (Pk→Tr ~1400–1600 MW) and exports in ~15% of
hours.

## Energy-balance warning

2024 and 2025 flag energy-balance drift exceeding ±3 TWh tolerance:
- 2024: model gen 176.88 vs EIA-930 net gen 190.56 (−13.68 TWh)
- 2025: model gen 173.59 vs EIA-930 net gen 186.37 (−12.78 TWh)

The model under-generates local thermal (gas short by ~8–14 TWh vs EIA-923) and
fills the gap with imports. This is the same root cause as the over-import: the
LP finds import tranches cheaper than local gas SRMC in too many hours.

## Remaining gap — root causes

1. **Import tranche pricing too cheap.** The static ladder ($28–$180/MWh) and
   even measured hub prices are below local gas SRMC in many midday/overnight
   hours, so the LP maximises imports within the ATC envelope. The model
   over-imports by 8.7–15.8 TWh across years.

2. **Model almost never exports.** Actual CAISO exports 9–14% of hours (mostly
   midday solar surplus to WECC_DSW); model exports in only 1–3% of hours.
   Export sinks at $0–$8 WTP rarely clear against local loads + cheap imports
   already flowing in.

3. **Amplitude compression.** Model pk-to-trough is 56–85% of actual. The
   trough (minimum import at midday) doesn't drop low enough because the LP
   doesn't divert enough midday power to exports; the model keeps importing at
   midday (just less).

4. **2023 falls back to static ladder** (no measured hub data for that year),
   which produces better correlation (+0.97) but narrower amplitude than
   2024/2025. The corridor ATC caps do the shaping work; measured hub pricing
   adds volume variation but also more import volume.

## Verdict

The interchange levers (Lever E) are structurally correct and should remain
ON — they produce meaningful diurnal shape that tracks reality (r ≥ 0.75).
The remaining over-import is a **level** problem (tranche pricing), not a
shape problem. Potential future calibration levers:

- Tighter ATC envelope (p90 or p75 instead of p95)
- Higher export WTP (reflecting WECC hub prices for solar-surplus hours)
- Reference-price interface (price imports at CAISO marginal cost, not hub)
- Import carbon adder adjustment (CARB border carbon already included but may
  need per-corridor recalibration)

None of these are implemented in this step — this run establishes the baseline
with the structural interchange mechanisms in place alongside all step 1–5
thermal fixes.
