# RESULT R-CAISO-20 — overnight clean rung armed in unprinted years (owner ruling) (2026-09-30)

**Outcome:** built, solved in 7 shards and **PROMOTED on structure** under the rule pre-registered in
`PRECOMMIT-r-caiso-20-2026-09-30.md` §6.
- New keeper: `2026-09-30-caiso-r20-overnight`, bundle `rcaiso20_A_span`, 2022–25.
- Fold: `2026-09-30-caiso-r20-overnight-touchpoints`, bundle `rcaiso20_A_tp_2019_2021`, 2019–21.
- Pruned under rule 35: `2026-09-30-caiso-r18-dswgas` and its fold.
- Year set: 2019–2025, before and after (rule 35 (b)/(c)).
- **Provenance:** this is an OWNER RULING (card 2026-09-30, "Arm overnight rung pre-2021"), not a measured admission. It is
  declared as such in the attestation, the matrix cell and the keeper note.

## Decision rule check (PRECOMMIT §6)
| Condition | Result |
|---|---|
| (a) 2022–25 reproduce the incumbent and stay CALIBRATED | **Met.** Max \|Δ class TWh\| = 0.0000 and max \|Δ price\| = 0.00 in every leg; the single ledgered caveat is C3c 2024 |
| (b) Every shard passes its hard stops, and 2019–21 show the arm | **Met.** Hard stop 3 passed in all 7 legs. DSW_overnight_clean runs 7.28 / 6.31 / 5.88 TWh in 2019 / 20 / 21 |
| Backstop: whole-year \|DSW error\| grows in any fold year | **Not triggered.** It falls in every year |

G-DRIFT against pin `d757b216`: all hunks INERT (PRECOMMIT §8). The keeper's cache key is unchanged.

## Reported: the fold

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| DSW net import, model TWh (EIA-930) | 31.4 → **35.4** (44.7) | 21.3 → **26.8** (41.9) | 29.9 → **30.7** (40.9) |
| DSW error, whole year | −13.3 → **−9.3** | −20.6 → **−15.2** | −11.0 → **−10.2** |
| DSW error, hod 0–5 | −3.83 → **+0.30** | −7.36 → **−1.93** | −2.06 → **−1.25** |
| C1 CC_REGULAR TWh (EIA-923) | 50.6 → 46.8 (36.1) | 65.5 → 60.7 (43.1) | 59.9 → 59.3 (49.2) |
| C4 gas r / NRMSE | 0.870/0.454 → 0.888/**0.390** | 0.889/0.470 → 0.887/**0.413** | 0.847/0.369 → 0.852/**0.360** |
| C3a 2021 mean LMP (actual 50.87) | 57.21 → 57.20 | | |

- **The overnight gap closes as intended.** In 2019 it overshoots slightly (+0.3 TWh). The first-order estimate was
  +7.1 / +8.7 / +3.1 TWh added; realised net additions are +4.0 / +5.5 / +0.8, because the clean rung displaces the
  DSW gas blocks and PNW imports as well as in-state gas.
- The fold stays NOT-YET on the same three criteria: C1, C4, and C3a 2021.
- Under rubric v3.13 the ISO determination stays NOT-YET on the fold.

## Ledgered: the remaining fold DSW residual is DATA-AVAILABILITY LIMITED (link 2)

| DSW error, TWh | Total | h0–5 | h6–17 | h18–23 | Jan–Apr | May–Dec |
|---|--:|--:|--:|--:|--:|--:|
| 2019 | −9.29 | +0.30 | −5.44 | −4.15 | −1.40 | −7.89 |
| 2020 | −15.15 | −1.93 | −6.34 | −6.88 | −3.92 | −11.23 |
| 2021 | −10.21 | −1.25 | −2.65 | −6.32 | −7.02 | −3.19 |

- What remains is daytime and evening DSW import, which the surplus, daytime and late-evening clean rungs carry in
  2021–25.
- OASIS serves no Palo Verde print before 2021-04-27. Each of those rungs needs a raw print for its trigger:
  - surplus and daytime need the raw hub against the gas floor;
  - late-evening needs the measured DA − hub spread.
- With only the formula hub, none of them has an admissible trigger (R-CAISO-19 FINDING §3), and no other measured
  source exists in the repo.
- **This residual is ledgered as data-availability limited, not as an open model defect.** It closes only if a pre-2021
  hourly Palo Verde print becomes available.
- The 2021 h18–23 part overlaps the known evening under-price, which is the next link (R-CAISO-21).

## The span (2022–25): unchanged
- C3a: 91.72 / 57.59 / 36.28 / 36.70, against actual 84.49 / 54.17 / 34.65 / 34.42.
- C4 gas NRMSE: 0.252 / 0.247 / 0.247 / 0.288.
- C3c 2024: 0 h against 35 h (ledgered).

## Retrievability (rule 34(e))
- The keeper and fold bundles are committed on `main` in this lane's PR.
- The per-year legs `rcaiso20_A_{Y}` are local and gitignored.
- Leg SHAs, for provenance only (rule 33(d)): any leg not on `main` would cost a re-solve.

  | Year | SHA |
  |---|---|
  | 2019 | `fe270e64e6ba0ce82786f37e6baa0e7bc0394693` |
  | 2020 | `616bef4e01e8bf6468336cfd9f9a94caedede279` |
  | 2021 | `c1040fa26244dc5624eb421d4e2a56795e8886f7` |
  | 2022 | `61d906e991cef109fff528a66b2e0c15687fd30a` |
  | 2023 | `73a23796b32ae4f30d5ee9ff0468616f97b89e82` |
  | 2024 | `dca3b0d6c13c29e5c1fcdd5e8de4042cdbf7e55a` |
  | 2025 | `dd25e43f7b3c2d58c10595b864e3c50d6a546445` |

## Transparency note
The carried governance flag `levers_trace_to_measured_input` stays true. The depth and pricing are measured, but the
2019–21 arming window is a transfer authorised by the owner ruling, which the attestation's `attested_by` text declares.
If the owner wants that flag to read false for the fold, it is a one-line change to the attestation. It is not made
here because the ruling is recorded as the identification source.

## Operational notes
- All 7 shards finished inside budget. The 2025 shard (50-min budget) finished in about 32 min.
- The per-year prompts were read by the shards from the immutable SHA `220e2696`
  (`docs/handoffs/r-caiso-20/shards/`).
