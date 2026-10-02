# PRECOMMIT — NWPP-NEXT-19 arm G: `gas_daily_shape` on keeper #20, 2019–2025

Fixed before any solve. Owner card 2026-10-02: "Both: wire + gas shards". Evidence:
`FINDING-nwppnext19-price-census-phase0-2026-10-02.md`.

## 1. The arm (one key)

Keeper #20 (`2026-10-01-nwppnext16c-combined-vintage`), each year replayed from **its own leg bundle**, with exactly one change:
`--set gas_daily_shape=true`. Nothing else moves.

| year | leg SHA (keeper #20) |
|---|---|
| 2019 | `1e4bd215c635aa876ab3ad75f8fb4657f4e47cec` |
| 2020 | `aa60aa43a9e27da9c7e14a8c7bcf09db1ad4dcc6` |
| 2021 | `3b38fefe402b5168c1557459a28978eb9274ed92` |
| 2022 | `11bb59fbf0d6a4b8716362f0e8c2f1899a601d11` |
| 2023 | `a54c7b97a9c588564bab90746f2dbbc44fd56838` |
| 2024 | `91f0bc2928bd348ac48f9d13c6fce7b3c8b460e8` |
| 2025 | `1a41ba5122095ef749302ddf2cb9d67f4fe89dfe` |

**Mechanism.** The measured Henry Hub daily spot, placed on its true trade date, mean-preserving per month
(`data/fuel/hubs.py::gas_daily_shape_factors`). `plant_prices.py` re-carries it onto every F923-overwritten gas plant-month, so
each plant's measured monthly delivered level is unchanged. Only the within-month daily swing is added.

**Rule checks.**
- Rule 13: measured, and forward-reproducible (a forward year takes a representative daily shape).
- Rule 14: HH is the only free public daily gas print. The NW hubs have no public daily series (FINDING §1).
- Rule 17: no floor.
- Rule 19: no other mechanism shapes NWPP gas within the month; the zonal basis is additive and mean-zero.
- Rule 24: a registered ScenarioConfig key, on by default in CAISO, NYISO, NEISO and MISO.

## 2. G-DRIFT (rule 29(b))

Shards pin a commit made of keeper #20's code pin `33014efc27296bf78842c4a50f311fe191c82b07` plus documentation files only
(this PRECOMMIT and the shard prompts). **Code drift: none.** Libraries: the `requirements.txt` pins (1.14.0 / 3.0.3 / 24.0.0 /
2.13.4), the same as keeper #20's legs. Every difference from keeper #20 is the arm's.

## 3. Expectation (ex ante, recorded so the result cannot reshape it)

Small. The HH shape can add a between-day price SD of about $1–4, against a measured $8–34 (FINDING §1b). The largest effect
should be January 2024. **C4 coal 2023 (r 0.669, NRMSE 0.313) is not expected to clear.** A clear would be surprising, and
would be checked for a mechanism before it is believed.

## 4. Hard stops per shard (any miss = STOP, no push)

1. `git rev-parse HEAD` equals the pin. Library versions are 1.14.0 / 3.0.3 / 24.0.0 / 2.13.4.
2. sha256 of the four NEXT-16 inputs (shard prompt STEP 1).
3. The `scenario_config` diff against the leg's own `run_config.json` is exactly `gas_daily_shape` (False → True).
4. Arm live: in `hourly/unit_hourly_<Y>.parquet`, at least one gas_cc unit's `mc` varies within a month (SD > 0.01 $/MWh).
   This is false for keeper #20.
5. P1 summed demand: 279.581 / 292.940 / 289.358 / 298.960 / 280.261 / 290.216 / 302.532 TWh, ±0.05.
6. Keeper log lines are present: `coal per-yard budget`, `coal take floor`, `coal monthly pile`, `NWPP Path 76 (Alturas)`.
7. The bundle has `dispatch/<Y>_P1.parquet` and `hourly/{class_hourly,system,hydro_cascade,unit_hourly}_<Y>.parquet`.
8. The LP is feasible.

## 5. Composition and decision

- **Compose.** Run `scripts/probes/_nwpp42_compose_span.py --skip-diagnostics` (2023 leg first) into `nwppnext19g_span`. Then
  run legitimacy diagnostics, the attestation, `dashboard_add_run --no-prune`, and `calibration_verdict --json`. Diff the
  verdict against keeper #20 per (criterion, year, key) record.
- **Decision rule** (owner standing ruling): promote if structural integrity improves, even if a gate regresses. Report every
  regression at full magnitude.
  - The arm adds a measured, admissible input that the keeper lacks, so it is a structural improvement on its face.
  - It is NOT a promotion candidate if it:
    - trips rule 20 (forced energy) or C6 (governance), or
    - opens a new failing record that traces to a defect in the arm's own construction. One example would be a shape
      applied to a non-gas class.
  - Promotion and prune go on ONE owner card. The decision is never chosen by C4 coal 2023 (rule 1).
