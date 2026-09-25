# RESULT — R-ERCOT-2: the CHP heat rate caused the 2023 regression; the missing DAM data caused most of 2019/2020

**PRECOMMIT:** `docs/handoffs/PRECOMMIT-r-ercot-2-dam-backyears-chp-test-2026-09-25.md`.
**Pinned SHA:** `8beff24de53472d4dfe3c1aec6910eb592c00622`, with one year per shard (rule 36).
**Keeper:** `2026-09-24-r-inputs-2019-2025`. It is unchanged, because nothing was promoted.

**Registered, NOT promoted:**
- `2026-09-25-r-ercot2-chp-off` (bundle `results/calibration/r_ercot2_chpoff_span`): the keeper recipe with only `measured_chp_heat_rates=false`, 2019–2025, on the restored data.
- `2026-09-24-r-ercot2-dam-restored` (bundle `results/calibration/r_ercot2_dam_span`): the keeper recipe unchanged. 2019/2020 were re-solved on the restored data; 2021–2025 are the keeper's own legs, whose inputs are byte-identical.

## Headline

1. **CHP-off brings ERCOT back to CALIBRATED on the train tier.**
   - 2023 C3b goes from 0.232 to **0.137**, where the gate is 0.20.
   - {2023–2025}: NOT-YET → **CALIBRATED**. {2024, 2025} stays CALIBRATED. {2023} flips to CALIBRATED.
   - The pre-registered test P2 said "if the CHP composition is the cause, 2023 C3b ≤ 0.20". **P2 is confirmed.**
2. **The restored DAM availability fixes most of 2019/2020:**

   | year | C3a mean | C3b | slack |
   |---|---|---|---|
   | 2019 | +364 % → **+110 %** | 6.41 → 1.99 | 101 GWh → 7 GWh |
   | 2020 | +114 % → **+22 %** | 2.54 → 0.48 | 11 GWh → 0 |

   With CHP-off added, 2019 reaches +101 % and 2020 +20 %. **P3 is confirmed on slack.**
3. **Both 2019 and 2020 are still NOT-YET.** The residual is coal: COAL_PRB is still −10.7 / −13.8 TWh, and CC_REGULAR / ST_GAS are over by the same amount. Coal's offer levels are the ERCOT-144 per-plant SCED curves, measured on later years. That is the named next object.

## Per year (C3a / C3b; the C1 column counts failing classes)

| year | keeper | CHP-off | DAM-restored |
|---|---|---|---|
| 2019 | +364.3 % / 6.410 / 3 | **+101.1 % / 1.850 / 2** | +109.7 % / 1.986 / 2 |
| 2020 | +114.3 % / 2.537 / 3 | **+20.1 % / 0.459 / 3** | +21.9 % / 0.475 / 3 |
| 2021 | +10.0 % / 0.202 / 0 | +9.4 % / 0.203 / 0 | +10.0 % / 0.202 / 0 |
| 2022 | −0.2 % / 0.098 / 0 | −1.8 % / 0.100 / 0 | −0.2 % / 0.098 / 0 |
| 2023 | +2.7 % / **0.232** / 0 | −3.7 % / **0.137** / 0 | +2.7 % / 0.232 / 0 |
| 2024 | +3.7 % / 0.147 / 0 | +1.9 % / 0.141 / 0 | +3.7 % / 0.147 / 0 |
| 2025 | −3.5 % / 0.088 / 0 | −5.2 % / 0.096 / 0 | −3.5 % / 0.088 / 0 |

**Determinations, CHP-off run:**
- train {2023–2025}: **CALIBRATED**;
- 2022: CALIBRATED;
- 2021 / 2020 / 2019: NOT-YET, as validation tier (rule 30(c): these never gate the headline).
- The registered whole-span run-level read is NOT-YET because of the validation years.

## Energy (CHP-off minus keeper, TWh)

CC_CHP is **+2.3 to +4.8** in every year and CC_REGULAR is −0.4 to −4.1. **P1 is half-confirmed:**
- CC_CHP rises, as predicted.
- CT_CHP was predicted to fall, but it rose slightly: **+0.02 to +0.29**. That half of the prediction is refuted and reported as such.

Coal moves by less than 0.5 TWh except in 2019, where CHP-off and the DAM data together add 2.3 TWh.

## Why the CHP rate was wrong for ERCOT (a structural finding, not a residual choice)

- ERCOT's curated bins already carve each CHP plant's host steam into a separate **must-run tranche**: it is removed from LP capacity and its generation added back afterward.
- The F1 power-only rate (eGRID heat with the CHP useful-thermal allocation added back) then charges that steam fuel to the dispatchable power block a second time. That is a rule 19 `[R-ONE-MECH]` double count in this representation.
- The steam-credited eGRID rate, year-matched under the R-ERCOT hierarchy, is the power-side marginal for these bins.
- The other ISOs, which use EIA-860 CHP rows without a separate host-steam tranche, are **not** addressed by this finding (rule 25). It is a statement about ERCOT's bin path only.

## Governance

- **Signatures and inputs:** all 9 legs match their signature and the input sha256 checks, and all 9 shards are archived.
- **Composition:** `stamp_config_partition --check` passes on both composites. The DOF ledger is carried verbatim, and **no multiplier moved**.
- **Matrix:** the ERCOT cell for `measured_chp_heat_rates` goes K → **O** (ruling pending), with this evidence.
- **Data fix:** the DAM restoration and derive-script fix merged with the previous PR.
- **Leftover refs for the owner to delete:** `claude/r-ercot2-{chpoff-2019..2025,dam-2019,dam-2020}`.
- **Retrievability:** both composites are committed on this branch in their rule-15 shape. The per-year legs are on local disk only.

## Promotion — OWNER DECISION NEEDED

**Recommendation: promote `2026-09-25-r-ercot2-chp-off`.** It is the promoted keeper's own recipe with one structural correction and the restored data. It returns the train tier to CALIBRATED and improves every held-out year. The only exceptions are 2022 and 2025, which move by a few tenths of a percent and stay in band.

Promotion would:
- prune the current keeper;
- move the ERCOT headline from NOT-YET back to **CALIBRATED**;
- set the ERCOT `measured_chp_heat_rates` cell to R on the bin path.

`2026-09-24-r-ercot2-dam-restored` is the fallback if you want the data fix without the CHP change. It stays NOT-YET on 2023.
