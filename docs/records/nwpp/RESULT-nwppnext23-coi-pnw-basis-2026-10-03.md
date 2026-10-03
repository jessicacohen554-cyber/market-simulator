# RESULT — NWPP-NEXT-23: COI export leg on CAISO's PNW delivered-cost basis, 2019–2025

PRECOMMIT: `PRECOMMIT-nwppnext23-coi-pnw-basis-2019-2025-2026-10-03.md`. Phase 0:
`FINDING-nwppnext23-price-level-phase0-2026-10-03.md`. Probe run `2026-10-03-nwpp-next-23-coi` (bundle
`results/calibration/nwppnext23_span`, composed from the seven legs). The keeper is the control.

## Legs (pin `33dc564771e1006ce69ffd2789053107ed4801cc`, branch `claude/nwppnext23-pin`)

| year | leg SHA | branch |
|---|---|---|
| 2019 | `6d69a0e80656d4dff860b79d185930e71d3106c7` | `claude/nwppnext23-2019` |
| 2020 | `e4c42ddccabe5fee509caebbb1e9c132ecb412f2` | `claude/nwppnext23-2020` |
| 2021 | `626484cc6b3c2b4e1522370cf642cf46395dc67c` | `claude/nwppnext23-2021` |
| 2022 | `974c0aab1c9f04fc8d5cf767818da67ca9b6a819` | `claude/nwppnext23-2022` |
| 2023 | `c151a1a1ba3562943ce6b1f864f978cd460989ed` | `claude/nwppnext23-2023` |
| 2024 | `10565f565722df520cb565884accc865d8254c2e` | `claude/nwppnext23-2024` |
| 2025 | `8e84c05110f45f21b42428f586e52cf617445ca6` | `claude/nwppnext23-2025` |

Every shard hard stop (a)–(h) passed. The parent re-verified each leg from its bytes:

- `scenario_config` diff vs the keeper's year config is exactly `nwpp_coi_pnw_delivery_basis` None→True.
- Demand frames match within 0.006 TWh.
- COI excess is 0.0 MW in both directions, in every year.
- `hydro_backfill_year` is 2024.

The first 2019 shard never left PENDING. It was archived unstarted and relaunched at the same pin.

## Gate (a) structural: PASS · (a″) direction: PASS

Net TWh, export-positive; model (r) / measured. The keeper's values are in brackets.

| seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| COI | 11.75 (0.745) [13.56] / 7.03 | 14.90 (0.595) [17.13] / 15.26 | 15.37 (0.607) [16.58] / 12.11 | 17.02 (0.643) [17.85] / 12.50 | 4.95 (0.397) [6.57] / 1.13 | 10.46 (0.540) [12.42] / 2.15 | 6.91 (0.569) [9.03] / 3.03 |
| NEVP | 9.55 † [9.36] | 10.75 [10.69] | 11.20 [11.06] | 8.71 [8.69] | 4.25 [4.02] / 7.56 | 9.22 [9.05] / 9.08 | 5.75 [5.56] / 9.40 |
| BC | | | | | 17.64 [17.59] / 9.48 | 13.27 [12.90] / 7.51 | 4.90 [4.37] / 2.77 |
| priced sum | 21.3 [22.9] | 25.6 [27.8] | 26.6 [27.6] | 25.7 [26.5] | 26.8 [28.2] | 33.0 [34.4] | 17.6 [19.0] |

† NEVP 2019 is the exempted near-zero leg.

- COI falls in every year, by −0.83 to −2.23 TWh, as pre-registered. The price-taker predicted 10.81 / 14.01 / 14.65 /
  16.70 / 3.79 / 9.62 / 6.02, and the LP response is about 60 % of that, as expected, because the NW price falls with
  it.
- Every priced seam-year keeps the measured sign, and every r is > 0.
- Part of the COI volume leaves through BC instead: +0.05 / +0.37 / +0.53 TWh in 2023–25.
- The wheel is 2.80 / 1.71 / 2.17 TWh (keeper 2.85 / 1.74 / 2.15).

## Gate (b): verdict diff against keeper `2026-10-03-nwpp-next-22b-w0`, per (criterion, year, key)

Both runs are NOT-YET. **Failing records: 10 → 10, with zero status flips in either direction.**

| record | keeper | NEXT-23 | |
|---|---|---|---|
| C1 CC_REGULAR 2019 | +12.65 TWh FAIL | +11.94 FAIL | closer |
| C1 CC_REGULAR 2024 | +15.39 FAIL | +14.80 FAIL | closer |
| C1 CC_REGULAR 2025 | +8.86 FAIL | +8.02 FAIL | closer |
| C4 gas 2019 | r 0.661 / NRMSE 0.355 FAIL | 0.657 / 0.348 FAIL | r −0.004, NRMSE better |
| C4 gas 2023 | 0.538 / 0.382 FAIL | 0.533 / 0.379 FAIL | r −0.005, NRMSE better |
| C4 gas 2024 | 0.796 / 0.353 FAIL | 0.791 / 0.342 FAIL | r −0.005, NRMSE better |
| C3a 2023 | −10.4 % FAIL | **−11.6 % FAIL** | regression, 1.2 pp |
| C3a 2024 | −27.1 % FAIL | **−27.9 % FAIL** | regression, 0.8 pp |
| C3a 2025 | −0.4 % PASS | **−1.6 % PASS** | regression, 1.2 pp |
| C3b 2023 | 0.216 FAIL | **0.225 FAIL** | regression |
| C3b 2024 | 0.789 FAIL | 0.791 FAIL | flat |
| C3b 2025 | 0.127 PASS | 0.127 PASS | flat |
| C4 coal 2019–2025 | all PASS (2023 0.770) | all PASS (2023 0.767) | flat (±0.008) |

**Reading.** The arm does what phase 0 measured, at its pre-registered size, and no more. COI over-export falls by
1–2 TWh, and gas CC by 0.6–1.7 TWh. The NW price falls by $0.3–0.5/MWh, because NW keeps the energy it no longer
exports. That deepens the 2023–24 price-mean miss by about 1 pp. The fuel-mix and gas-dispatch failures are untouched
in status: the residual over-export is the **depth** (FINDING §E: measured flow saturates near 600–800 MW at any
spread), not the hurdle.

## Gate (c): rule 20 and legitimacy

- D-2: 0 forced energy in every class-year. PASS.
- D-1 failures: 14 (keeper 14).
- C6 governance: PASS.

## G-DRIFT between the pin and main (at RESULT time)

- **LIVE (data), not in this run.** closeout-SOCO-3 merged EIA-923 coal stocks for 2015–17 into the coal-stocks
  datatype (#7132). NWPP's take floor and monthly pile read S_max over curated years ≤ Y−1, so yard maxima rise in 65
  NWPP plant-years 2019–25. Examples: Boardman 400→999 kt, Bonanza 511→1,013, Valmy (8224) 456→765, plant 3845
  1,014→1,396. This run predates it, and its scoring stands at the pin. **The next NWPP solve must re-solve against
  it.**
- **Keeper change pending.** The close-out anchor lane holds the NWPP promotion slot under owner ruling R-48. Its
  keeper `2026-10-03-closeout-nwpp-anchor-roster` (legs at `dad1205a`) sits within 0.01 TWh of the NEXT-22b keeper,
  with 0 flips. This pin already carries its anchor CSV.

## Matrix

`nwpp_coi_pnw_delivery_basis`: **O** (solved, structural gate PASS, zero flips, C3a −0.8 to −1.2 pp). Promotion is
the owner's ruling.

## Bundles and cost of a promotion

- Each leg's full bundle, including `dispatch/<Y>_P1.parquet` and `hourly/unit_hourly_<Y>.parquet`, is on its shard
  branch at the SHA above.
- The parent holds the bytes. The composed span is local and gitignored.
- A promotion waits for the desk to hand over the NWPP slot, after the anchor lane. It then merges main and re-runs
  G-DRIFT against the anchor keeper.
- The recipe is then checked for replay at HEAD (preflight 0d), which checks the config recipe. The coal-stocks merge
  is a data delta, so it does not trip 0d. It does mean a replay at HEAD would not reproduce this bundle
  byte-for-byte. That is the same class as the anchor CSV the anchor lane promoted across, and it is named here so the
  next NWPP solve re-solves against it.
