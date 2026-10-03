# RESULT — NWPP-NEXT-25: served schedule placed at its reporting members' zones, 2019–2025

- PRECOMMIT: `PRECOMMIT-nwppnext25-served-schedule-2019-2025-2026-10-03.md`.
- Phase 0: `FINDING-nwppnext25-scarcity-phase0-2026-10-03.md` (C3a tail days, no lever) and
  `FINDING-nwppnext25-cc-served-schedule-phase0-2026-10-03.md` (this lever).
- Probe run `2026-10-03-nwpp-next-25-served`; bundle `results/calibration/nwppnext25_span`, composed from seven legs.
- Control: keeper `2026-10-03-nwpp-next-24-head`, from its committed bundle.

## Legs (pin `d3965589f5d0b400e05560380de64d49ae0c6959`, branch `claude/nwppnext25-pin`)

| year | leg SHA | branch |
|---|---|---|
| 2019 | `ed42110f7058332b3a409bfcc5c0790a538244ff` | `claude/nwppnext25-2019` |
| 2020 | `36c42386d7abf55009c4fc5773d1bf40072ad71d` | `claude/nwppnext25-2020` |
| 2021 | `68cce836ed4cd09cd6be73a80ad1f36a58b977cf` | `claude/nwppnext25-2021` |
| 2022 | `4dd9cc12ad5cd355485b796871fa4287103313f5` | `claude/nwppnext25-2022` |
| 2023 | `5b4c57645c7ec912d82d3dbdad4f83c4fff48f48` | `claude/nwppnext25-2023` |
| 2024 | `c319cb12a5293794a7bdc06a815ecc0dd0ead074` | `claude/nwppnext25-2024` |
| 2025 | `4317885b9e643a4b37e2b7007e22e6791319a3a6` | `claude/nwppnext25-2025` |

Every leg's parent is the pin. The parent re-verified each leg from its own bytes:

- the `scenario_config` diff against the keeper's year config is exactly
  `[('nwpp_served_schedule_zonal_attribution', None, True)]`;
- the five-zone P1 demand equals the keeper's to 0.01 TWh;
- each zone matches the PRECOMMIT table to 0.01 TWh;
- `hydro_backfill_year` is 2024, and `priced_interchange` / `reference_price_interface` are True.

The 2025 shard sat PENDING twice and ran at its third launch.

## What moved (P1, TWh, NEXT-25 vs keeper)

| year | CC_REGULAR | SNV gas | NW gas | OR gas | COI exp | NEVP exp | BC exp | price $/MWh |
|---|---|---|---|---|---|---|---|---|
| 2019 | 62.15 → 62.70 | 31.25 → 29.58 | 17.82 → 18.78 | 10.23 → 10.85 | 11.68 → 11.13 | 9.50 → 10.47 | — | 29.31 → 29.47 |
| 2020 | 58.29 → 59.06 | 31.85 → 27.74 | 11.04 → 13.44 | 10.24 → 11.35 | 14.81 → 13.99 | 10.70 → 11.98 | — | 23.65 → 23.87 |
| 2021 | 56.73 → 56.80 | 28.79 → 22.35 | 13.53 → 16.55 | 13.31 → 14.37 | 15.35 → 14.06 | 11.21 → 12.34 | — | 37.25 → 38.30 |
| 2022 | 49.34 → 48.33 | 26.65 → 18.92 | 13.69 → 16.96 | 12.36 → 15.10 | 17.31 → 15.27 | 8.83 → 10.57 | — | 53.57 → 57.08 |
| 2023 | 59.79 → 57.52 | 24.96 → 21.89 | 18.91 → 20.66 | 14.04 → 14.93 | 4.94 → 2.16 | 4.24 → 5.55 | 17.64 → 17.03 | 46.68 → 49.25 |
| 2024 | 71.81 → 69.68 | 32.26 → 28.11 | 18.79 → 20.01 | 17.49 → 18.08 | 10.42 → 8.97 | 9.18 → 10.13 | 13.25 → 11.36 | 29.34 → 30.35 |
| 2025 | 64.41 → 63.24 | 27.65 → 23.91 | 18.10 → 18.96 | 13.32 → 14.59 | 6.89 → 5.91 | 5.72 → 6.91 | 4.88 → 3.54 | 31.61 → 32.23 |

- **Measured references.** SNV gas = NEVP EIA-930 NG:NG: 22.2 / 22.8 / 22.2 / 20.6 / 20.5 / 21.7 / 20.8. COI measured:
  7.03 / 15.26 / 12.11 / 12.50 / 1.13 / 2.15 / 3.03. NEVP measured: −0.30 / 3.11 / 8.60 / 8.56 / 7.56 / 9.08 / 9.40.
- **Reading.** Zonal placement moves the way the measured data does.
  - SNV gas falls 1.7–7.7 TWh toward NEVP's measured series; in 2022 it now sits 1.7 TWh below.
  - NW/OR gas rises, and COI and BC exports fall every year.
  - The footprint CC total moves less than the zonal shift: −2.3 to +0.8 TWh. SNV's freed capacity partly leaves
    through the NEVP seam instead, at +1.0 to +1.7 TWh.
  - The NEVP seam is now **over** measured in 2019–2020 (10.47 / 11.98 against −0.30 / 3.11) and still under in 2023–25.
  - The residual CC over-run is an NWPP surplus priced at the seams, which the zonal shift does not touch.

## Gate (b): verdict diff against keeper `2026-10-03-nwpp-next-24-head` (same bench render)

Both runs are NOT-YET. **FAIL records 9 → 8; one flip, FAIL → PASS.**

| record | keeper | NEXT-25 | |
|---|---|---|---|
| **C3a 2023** | −11.6 % FAIL | **−3.2 % PASS** | **flip** |
| C3a 2024 | −27.8 % FAIL | −25.3 % FAIL | +2.5 pp |
| C3a 2025 | −1.6 % PASS | +0.3 % PASS | |
| C3b 2023 / 2024 / 2025 | 0.225 / 0.791 / 0.127 | 0.209 / 0.772 / 0.118 | improves (2023 still FAIL, 0.009 over the band) |
| C1 CC_REGULAR 2019 | +12.17 (+3.34 pp) FAIL | **+12.73 (+3.50 pp) FAIL** | **regression 0.55 TWh** |
| C1 CC_REGULAR 2024 | +14.90 (+3.95 pp) FAIL | +12.77 (+3.43 pp) FAIL | −2.13 TWh |
| C1 CC_REGULAR 2025 | +7.99 PASS (knife-edge) | +6.82 PASS | margin regained |
| C1 CC_REGULAR 2020 | +6.74 PASS | **+7.51 PASS** | **regression 0.77 TWh** (band 8.00) |
| C1 CC_REGULAR 2022 / 2023 | −0.98 / +3.57 | −1.99 / +1.30 | |
| C1 CT_PEAKER 2021 | −1.21 | **−1.54** | **regression 0.33 TWh** (PASS) |
| C1 ST_GAS 2024 | −2.56 | **−2.91** | **regression 0.35 TWh** (PASS) |
| C1 COAL_BIT 2023 | +5.15 | +4.56 | |
| C4 gas 2019 | r 0.651 / 0.359 FAIL | **r 0.649 / 0.359 FAIL** | **regression r −0.002** |
| C4 gas 2023 | 0.534 / 0.379 FAIL | **0.533** / 0.359 FAIL | **r −0.001**, NRMSE −0.020 |
| C4 gas 2024 | 0.789 / 0.344 FAIL | 0.797 / 0.316 FAIL | improves |
| C4 gas 2020 | 0.756 / 0.279 | **0.752 / 0.281** | **regression** (PASS) |
| C4 gas 2022 / 2025 | 0.762 / 0.816 | 0.792 / 0.828 | improves |
| C4 coal 2023 / 2024 | 0.766 / 0.796 | **0.756 / 0.783** | **regression** (PASS) |
| C4 coal 2019–2022 | 0.791 / 0.754 / 0.796 / 0.758 | 0.799 / 0.781 / 0.822 / 0.772 | improves |

## Gate (c): rule 20 and legitimacy

- **D-2.** Forced share is 0 in every class-year. PASS.
- **D-1 failures 13 → 16** (regression). New: 2019 COAL_BIT, 2022 CT_PEAKER, 2022 ST_GAS. Removed: none.
- **C6 governance.** PASS. The attestation is `scripts/gen_nwppnext25_attestation.py`: the NEXT-24 generator plus
  this structural key, with zero new free parameters.

## Reading and recommendation

The arm places a schedule the keeper already serves at the zones where its ties physically land. That is a
rule-14 / rule-19 improvement in structure, and zonal gas follows the measured BA series. On the scored records:

- **Gains:** one FAIL → PASS (C3a 2023); C3a/C3b improve in every scored year; CC 2024 −2.1 TWh; CC 2025 leaves the
  knife-edge; C4 gas 2022/2024/2025 and C4 coal 2019–2022 improve.
- **Regressions, at full magnitude:**
  - CC 2019 +0.55 TWh and CC 2020 +0.77 TWh (2020 PASS at +7.51 of 8.00);
  - C4 gas 2019 r −0.002 and 2023 r −0.001;
  - C4 coal 2023/24 −0.010/−0.013;
  - D-1 13 → 16.

Under the owner's standing ruling (promote if structural integrity improves, even if a gate regresses), this is a
**promotion candidate**. The close-out desk session is archived, so the slot decision goes on the owner card.

## Bundles and cost of a promotion

- Each leg's full bundle, including `dispatch/<Y>_P1.parquet` and `hourly/unit_hourly_<Y>.parquet`, is on its shard
  branch above. The parent holds the bytes.
- The composed span carries every `hourly/` sidecar, including `unit_marginal_<Y>` for all seven years.
- A promotion is one `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext25_span`, which prunes the
  `2026-10-03-nwpp-next-24-head` stores. The bundles do not survive this container unless promoted or pushed.

## §Promotion (2026-10-03)

The owner card "Promote" ruled the promotion. The close-out desk session was archived before this lane reached the
slot.

- **Merge.** `origin/main` (4fcad76b) was merged into `claude/nwppnext25`. No `src/` or `scripts/run_*` change came in,
  so G-DRIFT is empty.
- **Staged legs.** They were moved out of `results/calibration` before the run.
- **Promotion run.** `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext25_span`:
  - preflight built `fleet_census_<Y>`;
  - outgoing exceptions ledger empty;
  - attestation and DOF ledger written;
  - `keepers/NWPP.json` and the `program-status.json` gate-(a) marker re-keyed to `2026-10-03-nwpp-next-25-served`;
  - status rebuilt (NOT-YET);
  - audit with only E13 tolerated, then `2026-10-03-nwpp-next-24-head` / `nwppnext24_span` pruned;
  - strict audit clean;
  - parity OK (9 runs, 9 bundle dirs).
- **Not deleted.** `scripts/gen_nwppnext24_attestation.py` is kept: `gen_nwppnext25_attestation.py` imports it.
