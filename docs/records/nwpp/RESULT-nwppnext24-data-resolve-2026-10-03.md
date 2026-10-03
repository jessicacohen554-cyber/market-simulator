# RESULT — NWPP-NEXT-24: keeper recipe replayed unchanged at main HEAD (rule-14 data re-solve), 2019–2025

PRECOMMIT: `PRECOMMIT-nwppnext24-data-resolve-2019-2025-2026-10-03.md`. Phase 0:
`FINDING-nwppnext24-coi-depth-phase0-2026-10-03.md` (COI depth closed, C3a tail-day decomposition). Probe run
`2026-10-03-nwpp-next-24-head` (bundle `results/calibration/nwppnext24_span`, composed from the seven legs). The control
is keeper `2026-10-03-nwpp-next-23-coi`.

## Legs (pin `23beba2ac9c1baa00f276a6723e5af47217739ff`, branch `claude/nwppnext24-pin`)

| year | leg SHA | branch |
|---|---|---|
| 2019 | `496574b169b46e7dcc6284786ec9a9d02371a9fc` | `claude/nwppnext24-2019` |
| 2020 | `43f25662d535a58972c89e5eae68d473d4ecfb70` | `claude/nwppnext24-2020` |
| 2021 | `9a25bc07ba59d5e557205b85447181f2a2063d6f` | `claude/nwppnext24-2021` |
| 2022 | `1a26d839b8686cfc8266aae757b17c494dec4721` | `claude/nwppnext24-2022` |
| 2023 | `ae3ca67d75adb09b7b0405f40167ff315a287f4d` | `claude/nwppnext24-2023` |
| 2024 | `ea696a77e5f76da63f04f4609b4935d5e30f2ec1` | `claude/nwppnext24-2024` |
| 2025 | `81189d3cd8cd9a7625f5d75165d2000144f014e5` | `claude/nwppnext24-2025` |

Every leg's parent is the pin. Every shard passed hard stops (a)–(h). The parent re-verified each leg from its bytes:

- the `scenario_config` diff against the keeper's year config is **empty**;
- demand frames match the keeper to 0.001 TWh;
- `hydro_backfill_year` is 2024.

**Procedure incident.** The parent's prompt generator renamed the replay source to a nonexistent
`nwppnext24_span`. Five first-wave shards stopped cleanly on the missing path and pushed nothing. They were archived
and relaunched as r2 from prompt commit `16c21b4c`, at the same pin. The 2019 shard noticed the typo, relaunched once on
`nwppnext23_span` (the PRECOMMIT's source), and was kept: its recipe diff is empty like every other leg. 2021 sat
PENDING three times before its fourth launch started.

## Data effect (P1 class TWh, NEXT-24 − keeper)

| year | nuclear | COAL_BIT | COAL_PRB | CC_REGULAR | CT_PEAKER | price $/MWh |
|---|---:|---:|---:|---:|---:|---|
| 2019 | +0.40 | −1.06 | −0.17 | +0.20 | +0.35 | 29.31 (29.15) |
| 2020 | +0.95 | −1.96 | −0.35 | +1.09 | +0.05 | 23.65 (23.53) |
| 2021 | +0.05 | −0.37 | −0.04 | +0.34 | 0.00 | 37.25 (37.23) |
| 2022 | +1.39 | −0.01 | 0.00 | −0.76 | −0.14 | 53.57 (54.61) |
| 2023 | 0.00 | 0.00 | −0.06 | +0.03 | 0.00 | 46.68 (46.67) |
| 2024 | 0.00 | −0.26 | +0.02 | +0.10 | +0.03 | 29.34 (29.29) |
| 2025 | 0.00 | −0.17 | 0.00 | +0.09 | +0.02 | 31.61 (31.60) |

- **Nuclear.** Columbia's measured 2019–22 monthly CF replaces the fleet smear. Nuclear energy changes by +0.05 to
  +1.39 TWh. That moves 2022 gas down by 0.76 TWh and lowers the price by $1.0.
- **Coal stocks.** The 2015–17 yard maxima reshape the take floor and pile ceiling. Bituminous coal falls by up to
  1.96 TWh (2019–20), and gas CC fills the gap.

Seam net export, TWh: COI 11.68 / 14.81 / 15.35 / 17.31 / 4.94 / 10.42 / 6.89 (keeper 11.75 / 14.90 / 15.37 / 17.02 /
4.95 / 10.46 / 6.91); BC 2023–25 17.64 / 13.25 / 4.88; NEVP 9.50 / 10.70 / 11.21 / 8.83 / 4.24 / 9.18 / 5.72. Every
seam-year keeps its sign.

## Gate (b): verdict diff against keeper `2026-10-03-nwpp-next-23-coi`

Both runs are scored on the same benchmark render (the bench parts regenerated at HEAD by this registration). Both are
NOT-YET. **FAIL records 9 → 9, zero status flips.**

| record | keeper | NEXT-24 | |
|---|---|---|---|
| C1 CC_REGULAR 2019 | +11.97 TWh (share +3.26 pp) FAIL | **+12.17 (+3.34 pp) FAIL** | regression 0.20 TWh |
| C1 CC_REGULAR 2024 | +14.80 (+3.91 pp) FAIL | **+14.90 (+3.95 pp) FAIL** | regression 0.10 TWh |
| C1 CC_REGULAR 2025 | +7.90 PASS | +7.99 PASS | regression 0.09 TWh; band 8.00 |
| C1 CC_REGULAR 2020 | +5.65 PASS | +6.74 PASS | regression 1.09 TWh |
| C4 gas 2019 | r 0.657 / NRMSE 0.348 FAIL | **r 0.651 / 0.359 FAIL** | regression |
| C4 gas 2023 | 0.533 / 0.379 FAIL | 0.534 / 0.379 FAIL | flat |
| C4 gas 2024 | 0.791 / 0.342 FAIL | 0.789 / 0.344 FAIL | regression 0.002 |
| C4 coal 2019 | 0.801 PASS | 0.791 PASS | regression 0.010 |
| C4 coal 2022 | 0.747 PASS | **0.758 PASS** | improvement |
| C4 coal 2025 | 0.816 PASS | 0.821 PASS | improvement |
| C3a 2023 / 2024 / 2025 | −11.6 / −27.9 / −1.6 % | −11.6 / −27.8 / −1.6 % | flat |
| C3b 2023 / 2024 / 2025 | 0.225 / 0.791 / 0.127 | 0.225 / 0.791 / 0.127 | flat |

The other C1 rows move by at most 1.96 TWh (COAL_BIT 2020 +0.22 → −0.43 pp share). All stay PASS.

**Benchmark re-render, disclosed separately (not this run).** The NWPP bench parts on main were rendered before a
CHP / behind-the-meter reattribution and the COAL_LIGNITE group landed on main. Re-rendered at HEAD, measured
CC_REGULAR moves +0.12 TWh in 2025 (56.302 → 56.419; CC_CHP −0.117) and −0.04 TWh in 2019. That flips the keeper's CC
2025 record **FAIL (+8.02) → PASS (+7.90)** against the 8.00 TWh band. On the old render the NEXT-24 run reads +8.11
TWh, FAIL. Like-for-like, the flip count is zero on either render. The committed keeper metrics (10 FAIL) become 9
once its verdict is re-read on the HEAD render.

## Gate (c): rule 20 and legitimacy

- D-2: 0 forced energy in every class-year. PASS.
- D-1 failures: 13 (keeper 14).
- C6 governance: PASS. The attestation is `scripts/gen_nwppnext24_attestation.py` (NEXT-23 generator, no new free
  parameter).

## Reading and recommendation

This is a pure data re-solve. The recipe is byte-identical, and two measured inputs replace older ones:

- the 2015–17 coal-stock record, which completes the yard-maximum history the pile reads;
- Columbia's measured monthly CF, which replaces a fleet smear.

Both are rule-14 improvements in input accuracy. The gas-side regressions (CC 2019 +0.20, 2020 +1.09, 2024 +0.10 TWh;
C4 gas 2019 r −0.006) are where the measured inputs push the existing over-run. They are reported at full magnitude
and change no status. Under the owner's standing ruling (promote if structural integrity improves, even if a gate
regresses), this is a promotion candidate: the keeper would otherwise carry inputs main no longer has.

## Bundles and cost of a promotion

- Each leg's full bundle, including `dispatch/<Y>_P1.parquet` and `hourly/unit_hourly_<Y>.parquet`, is on its shard
  branch at the SHA above. The parent holds the bytes.
- The composed span carries the `hourly/` sidecars, including `unit_marginal_<Y>` for every year.
- A promotion is one `promote_keeper.py` run once the desk hands over the NWPP slot. It prunes the
  `2026-10-03-nwpp-next-23-coi` stores.

## §Promotion (2026-10-03)

The close-out desk (session_01ALecU5Wjde4tkbLrnMExT9) granted the NWPP slot. The desk ruling was "rule-14 data
re-solve of the R-48 structure, recipe diff empty, zero flips", recorded in plan §5.0.

- **Merge.** `origin/main` was merged into `claude/nwppnext24`. Main was still at `b54e1d84`, the pin's base, so
  **G-DRIFT is empty**.
- **Promotion run.** `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext24_span`:
  - preflight clean;
  - outgoing exceptions ledger empty;
  - registration, attestation and DOF ledger;
  - `keepers/NWPP.json` and the `program-status.json` gate-(a) marker re-keyed to `2026-10-03-nwpp-next-24-head`;
  - status rebuilt (NWPP NOT-YET);
  - pre-audit with only E13 tolerated, then the outgoing three stores pruned (`2026-10-03-nwpp-next-23-coi`,
    `nwppnext23_span`);
  - strict audit clean;
  - parity OK (9 runs, 9 bundle dirs).
- **Not deleted.** `scripts/gen_nwppnext23_attestation.py` is kept: it is the base `gen_nwppnext24_attestation.py`
  imports.
