# RESULT — R-ERCOT-20: simple-cycle GTs split out of three CC plants — PROMOTED; ISO stays NOT-YET

- **Owner decision card, answer verbatim:** *"Promote (Recommended)"*.
- **Keeper:** `2026-09-30-r-20-gt-split` (bundle `results/calibration/r_ercot20_span`, 2019–2025). It supersedes `2026-09-30-r-19-eia-923`.
- **Records:**
  - PRECOMMIT: `PRECOMMIT-r-ercot-20-gt-split-2026-09-30.md` (pinned SHA `bf7c1228b9450aea0bb020c48f8d5ccafdae9190`).
  - Phase 0: `FINDING-r-ercot-20-2024-c3a-and-gt-in-cc-2026-09-30.md`.
  - D-4 design, held by the owner: `DESIGN-r-ercot-20-d4-day-grain-drag-mask-2026-09-30.md`.

## What changed

**Rule 14 capacity boundary.** Three ERCOT plants modelled as CC_REGULAR also hold simple-cycle GTs, and the model priced those GTs on the CC econ ramp. They now sit in their own CT_PEAKER split-child rows (the Parish / Barney Davis precedent):

| Plant | GT MW moved to CT_PEAKER |
|---|---|
| T H Wharton 3469 → 34693 | 526.3 |
| Sand Hill 7900 → 79003 | 308.4 |
| Colorado Bend 56350 → 563503 | 74.0 (COD 2023) |

- GT outage windows no longer derate the CC parents.
- The CC committed % is re-based so the committed block keeps the same MW on the CC-only nameplate.
- The recipe is byte-equal (`config_partition_overrides` identical). Zero DOF added. Offer multipliers untouched.

## Per year, keeper r-19 → r-20 (P1, `calibration_verdict --years`)

| Year | Determination | C3a | LW $/MWh | C3b | C3c h>$200 (model/actual) | C1 CC_REG | C1 ST_GAS | C1 COAL_PRB | C1 CT_PEAKER | C8 ST_GAS | Slack | h > $1k |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 val | NOT-YET → NOT-YET | +23.9 → +25.7 % | 57.67 → 58.51 | 0.538 → 0.566 | 121 → 123 / 106 | +9.70 → +8.03 F | +3.06 → +3.67 | −9.48 → −9.05 F | −4.34 → −3.88 | 18.1 → 16.7 % | 0 → 0 | 41 → 41 |
| 2020 val | NOT-YET → NOT-YET | +5.6 → +7.1 % | 26.83 → 27.20 | 0.229 → 0.236 | 39 → 39 / 56 | +12.39 → +10.81 F | +2.62 → +3.19 | −11.60 → −11.04 F | −3.32 → −3.04 | 24.5 → 22.5 % | 0 → 0 | 3 → 3 |
| 2021 val | CAL → CAL | +4.6 → +5.1 % | 173.56 → 174.46 | 0.067 → 0.073 | 667 → 668 / 258 (ledgered) | −0.54 → −1.78 | −0.22 → +0.27 | −1.51 → −1.41 | −0.73 → −0.19 | 22.7 → 20.9 % | 4,145 → 5,325 MWh | 123 → 123 |
| **2022 val** | **CAL → NOT-YET** | −8.7 → −7.7 % | 68.54 → 69.28 | 0.167 → 0.160 | 97 → 101 / 196 | **−7.69 → −8.83 F** | −1.08 → −0.67 | +5.93 → +5.99 | −1.57 → −0.95 | 30.1 → 28.3 % | 0 → 0 | 19 → 19 |
| 2023 hold | NOT-YET → NOT-YET | −19.8 → −18.5 % | 52.11 → 53.01 | 0.289 → 0.270 | 155 → 160 / 181 | +3.72 → +1.53 | −1.14 → −0.49 | −2.18 → −1.72 | −1.36 → −0.39 | 19.6 → 18.1 % | 0 → 0 | 38 → 38 |
| **2024** | **NOT-YET → CAL** | **−10.7 → −9.9 %** | 27.84 → 28.10 | 0.190 → 0.188 | 13 → 14 / 53 (ledgered) | −1.37 → −3.79 | −1.59 → −0.87 | −1.21 → −0.56 | −0.98 → −0.09 | 16.4 → 14.9 % | 0 → 0 | 1 → 0 |
| 2025 | CAL → CAL | −9.8 → −8.2 % | 32.92 → 33.51 | 0.130 → 0.119 | 0 → 0 / 31 (ledgered) | −0.70 → −2.67 | −3.02 → −2.36 | +3.65 → +3.81 | −1.84 → −0.85 | 22.2 → 20.0 % | 0 → 0 | 0 → 0 |

Notes:
- The C1 band is ±8.00 TWh.
- 2025 C1 for CC_REGULAR, ST_GAS and CT_PEAKER is SKIPPED by the scorer (EIA-923 completeness).

**Split plants, 2024 dispatch:**

| Plant | TWh |
|---|---|
| Wharton CC | 3.17 |
| Wharton GT | 0.29 |
| Sand Hill CC | 1.75 |
| Sand Hill GT | 0.15 |
| Colorado Bend CC | 2.80 |
| Colorado Bend GT | 0.03 |
| **Three plants** | **11.41 → 8.19** (EIA-923 ≈ 5.2) |

## Prediction scorecard (PRECOMMIT §5)

| Prediction | Outcome |
|---|---|
| 2024 C3a −10.5 to −9.4 % | **HIT** (−9.9 %, flips CALIBRATED) |
| 2022 C1 CC_REGULAR −9.0 to −8.1, FAIL | **HIT** (−8.83) |
| 2025 C3a −9.7 to −8.6 % | **HIT** (−8.2 %, just past the band's favourable end) |
| 2023 C3a −19.8 to −19.0 % | **MISS**, better than predicted (−18.5 %) |
| 2019 C3a +24.0 to +25.0 % | **MISS**, worse (+25.7 %) |
| 2020 C3a +5.7 to +6.6 % | **MISS**, worse (+7.1 %) |
| 2021 C3a +4.7 to +5.6 % | HIT (+5.1 %) |
| CC_REGULAR net −0.5 to −1.6 TWh/yr | **MISS** in 2021/2023/2024/2025 (−1.2 to −2.4). The efficient CCs back-filled less than assumed; coal and ST_GAS took part of it. |
| CT_PEAKER +0.3 to +1.0 TWh/yr | HIT (+0.29 to +0.96) |
| LW +0.1 to +0.7 $/MWh | HIT except 2021 (+0.90) and 2023 (+0.90) |
| C3b ±0.02 | MISS in 2019 (+0.028) and 2023 (−0.019, favourable) |
| Split plants 2024: 6–8 TWh | Slightly above (8.19) |
| GT children 0.1–0.6 TWh | HIT, low (0.03–0.29) |
| Slack / h > $1k | HIT except 2021 slack +1,180 MWh (±100 predicted) |

## Standing state and next object

**ISO NOT-YET:**
- 2023 carve-out: owner hold, k=33.
- 2022 held-out miss on C1 CC_REGULAR, which downgrades under rule 30(c) as amended 2026-09-30.
- 2019/2020 validation remain NOT-YET.

**Next objects:**
1. **2022 CC_REGULAR under-run (−8.83 TWh).** 2022 is the high-gas-price year: COAL_PRB is +5.99 while CC is short. The split exposes this; it does not cause it.
2. **Wharton's CC half still runs 3.17 TWh against 0.56 actual.** Its base heat rate is eGRID's plant average (10.43, GT-inclusive); the measured CAMPD CC rate is flagged `steam_not_metered`. A CC-only EIA-923 heat rate (CT + CA fuel / generation ≈ 9.5) is the candidate input.
3. **Silas Ray (3559).** Its 61 MW GT was not split, because the EIA-923 class override and the `mixed_fossil_plants` relabel would mismatch the benchmark. Routed.
4. **D-4 day-grain drag mask.** Designed and held by owner ruling.

## Promotion (rule 35)

1. **Year union before the prune** (both sidecars): {2019 … 2025}. The incoming keeper covers all seven.
2. **Re-keyed:**
   - `keepers/ERCOT.json` (all three configs + `r_ercot20_extension`)
   - `calibration-complete.json` (`keeper_rekey_2026_09_30_r20`; marker stays withdrawn)
   - `forecast/program-status.json`, ERCOT gate (a) only
   - `status/ERCOT.js`
   - ERCOT matrix shard (keeper/gates stamp + `measured_ct_heat_rates` evidence)
   - `mechanism-testing-matrix.md` §5.1
3. **`audit_keepers` between promotion and prune:** only the expected E13, on r-19.
4. **`prune_iso_runs --iso ERCOT --force-uncite`** removed r-19 (sidecar, payload, bundle). After the prune, `audit_keepers` reads 0/0.

## Where the bytes are (rule 34(e))

- **On `main` with the promotion:** `results/calibration/r_ercot20_span` (slim bundle with hourly sidecars), its registry sidecar and its run payload.
- **Legs** (provenance only, rule 33(d); shard branches are transport). All shards are archived. A leg not on `main` costs a re-solve (~16–25 min each).

| Year | Commit |
|---|---|
| 2019 | `4d20cb13398afb1079a7b3ab2563ea33a376bf81` |
| 2020 | `fb7b333ca115871ee3fde8f663e6a81375be1bcd` |
| 2021 | `59caa88085fa90040b6ecbaf535213c7d2f24e74` |
| 2022 | `d7f8082be5ea63f67ac7956bbc8cfd876a1b6881` |
| 2023 | `f94d4806d6ff603faa3208e1f0db079ef8e54bf8` |
| 2024 | `0bc8822ad8768610e46a53f31425a03d836a9c2c` |
| 2025 | `a4a5bcea35add67af59e8feda8b38627cd15f8de` |

**Refs for the owner to delete** (sessions cannot delete refs, rule 33(f)):
- `claude/r-ercot20-arm-{2019..2025}`
- `claude/r-ercot19-arm-{2024,2025}`
- `claude/r-ercot19b-arm-{2019,2020,2021r,2022,2023,2024,2025}`
- `claude/r-ercot19c-arm-{2019,2020,2021,2022r,2023,2024,2025}`
