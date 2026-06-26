# CAISO EOR cogen power-only heat-rate correction (2026-06)

## Summary

The three big Kern-County enhanced-oil-recovery (EOR) topping cogens —
**Kern River (10496), Sycamore (50134), Midway Sunset (52169)** — were
over-dispatched by the model: it ran them flat at ~88% capacity factor
(~3.7 TWh combined in 2024) versus their measured ~0.8 TWh (EIA-923 CF
0.05–0.14, and declining as California EOR winds down). This was the
dominant CAISO **CT_CHP** C1 fuel-mix failure (model 6.95 vs actual 3.49
TWh in 2024, +3.46 — outside the ±2.18 TWh band).

## Root cause

An EOR cogen is a gas turbine whose exhaust raises injection steam for
thermal oil recovery; electricity is a byproduct. EIA-923 reports a
**steam-credited** plant heat rate (Kern River 5.80, Sycamore 5.99, Midway
Sunset 5.09 MMBtu/MWh — *below* an efficient combined cycle ~7) because the
steam fuel is credited out of the electrical heat rate. The model then
priced these units as cheap baseload and ran them flat.

## Fix

`fleet._correct_caiso_eor_power_hr` lifts the CT_CHP rows of those three
plants to their **power-only** heat rate — charge all the fuel to
electricity (no steam credit). For a topping cycle that is the simple-cycle
gas-turbine heat rate, ~1.8× the steam-credited blend
(`CAISO_EOR_TOPPING_FACTOR = 1.8`), landing them at ~9–11 MMBtu/MWh — the
CT_PEAKER simple-cycle band where their power island physically sits. They
then clear on price like a peaker rather than as baseload.

This is a measured-physics heat-rate correction (the topping steam-credit
ratio is forward-derivable turbine physics and responds to changed
gas/steam conditions — admissible under CLAUDE.md #11/#12), the same kind of
correction as `MIXED_FACILITY_STEAM_HR`. It is **not** tuned to the residual:
the multiplier is the steam-credit ratio, applied to the three named plants
only, never to land CT_CHP on a target.

## Result (2024 probe, per-plant multi-zone)

| class       | before | after | actual | band ±2.18 |
|-------------|-------:|------:|-------:|:----------:|
| CT_CHP      |  6.95  |  3.54 |  3.49  | PASS (+0.05) |
| CC_REGULAR  | 56.64  | 58.65 | 53.21  | FAIL (+5.44) |
| CT_PEAKER   |  2.72  |  2.73 |  5.00  | FAIL (−2.27) |
| CC_CHP      |  9.01  |  9.02 |  9.91  | PASS         |
| ST_GAS      |  1.39  |  1.41 |  0.14  | PASS         |

CT_CHP goes FAIL→PASS. The freed energy backfills almost entirely onto
**CC_REGULAR** (+2 TWh) rather than imports, because the model is long on
domestic gas and short on imports — most acutely in the **evening ramp**
(hours 16–21), where net imports collapse (h18 model net ~0.85 GW; gross
import ~2.9 GW is offset by ~2 GW of uneconomic evening *export* on the
priced bidirectional corridors). The EOR over-dispatch was masking this:
removing it relocates the same ~+5 TWh domestic-gas-over / import-under from
CT_CHP onto CC_REGULAR.

## Open item (next session) — the C1↔C3 unlock

CC_REGULAR over (+) ↔ CT_PEAKER under (−) ↔ C3 LMP over (+47–69%) and the
616 h >$200 scarcity tail are one coupled problem: **the model under-imports
in the evening ramp and over-runs domestic gas.** Suspects:

- the priced per-hub bidirectional corridors permitting ~2 GW of uneconomic
  evening export (net evening import suppressed → CC backfills);
- the corridor ATC import ceiling / import-tranche pricing in hours 16–21;
- CC_REGULAR clearing ahead of both imports and CT_PEAKER on the evening
  ramp.

Attacking the evening import representation should pull CC_REGULAR down
(C1), lift CT_PEAKER toward its local-RA level, and cut the LMP level and
scarcity tail (C3) together. The EOR power-only HR correction is the
structurally-correct merit fix and stays in (CLAUDE.md #1/#11); it sharpens
the residual onto the import/corridor representation rather than burying it
in a mispriced cogen.

## Negative result on file

A gas-commitment-floor netting/scoping change (scope the RA must-offer floor
to the flexible CC_REGULAR + CT_PEAKER fleet and net the CHP steam floor out
of the measured NG:NG target) was trialled and **rejected**: it made
CC_REGULAR worse (59.3 / 60.5 TWh vs 58.7 with the original floor), because
the CHP steam floors are ~0 in the artifact, so the netting subtracts nothing
and the scoping simply shifts the midday floor target onto CC_REGULAR. The
floor is not the binding constraint midday (model midday gas 21.3 > floor
19.2 TWh); the CC backfill is a merit/import effect, not a floor effect.
