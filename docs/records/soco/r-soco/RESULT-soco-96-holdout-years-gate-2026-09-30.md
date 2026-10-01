# RESULT — soco-96 Part A: held-out years gate the ISO determination (rubric v3.13)

**Date:** 2026-09-30 · **Session:** soco-96 · **LP cost:** zero (scorer-side only)

## Ruling

Owner instruction 2026-09-30, verbatim: *"Shouldn't be considered calibrated if holdout years miss."*
This reverses CLAUDE.md rule 30 `[R-TOUCHPOINT-FOLD]` (c) as ruled 2026-09-05 ("A HELD-OUT YEAR
NEVER DOWNGRADES THE ISO").

Owner decision cards, same sitting (verbatim option labels):

| card | ruling |
|---|---|
| Caveat budget across keeper + folded runs | **Per run, worst-of** |
| Folded touchpoint not solved on the current recipe | **Counts; flagged stale** |
| Markers | **Also withdraw frontiers** |

## What changed

- `scripts/calibration_verdict.py::iso_determination` (new): the ISO determination is the worst
  over the keeper's designated scopes (every `config_partition` config on its designated span,
  whatever its `tier`; else the keeper's whole span) plus every run folded to it through
  `holdout.keeper`. Each scope is scored by the unchanged `determine()` under its own caveat
  budget. The basis line names each non-clean scope's years and failing criterion-years. A folded
  run whose solve basis sha differs from the keeper's still gates and is flagged `stale`.
  `RUBRIC_VERSION` is now `"3.13"`.
- `scripts/build_status.py` and `scripts/audit_keepers.py` (M1b) both read that function. The
  ercot-255 exclusion of `tier: validation` configs is gone from both.
- Untouched: `determine_from_artifacts` (every band, tier, ledger row, both caveat budgets, the
  v3.6 C3c out-of-training limb).

## Measured impact (pre-change scorer vs v3.13, committed artifacts, no solve)

Run-level determinations: **0 of 11** registered runs move.

| ISO | before | after | what moves it |
|---|---|---|---|
| CAISO | CALIBRATED | **NOT-YET** | folded 2019/2020/2021 (`…-caiso-r18-dswgas-touchpoints`): fuelmix 2019–21, dispatch_corr 2019–21, price_mean 2021 |
| MISO | CALIBRATED | **NOT-YET** | config validation-2020-2022 (2019–2022): fuelmix 2019, price_shape 2021/2022, price_mean 2022 |
| NYISO | CALIBRATED | **NOT-YET** | folded 2021 (`…-nyisonext16-winter-spread-2021`): price_mean 2021 |
| SPP | CALIBRATED | **NOT-YET** | config validation-2019-2022: price_mean 2019/2020, price_shape 2020, fuelmix 2021/2022, dispatch_corr 2021/2022 |
| NEISO | CALIBRATED | CALIBRATED | one 2019–2025 bundle; every year passes |
| ERCOT | NOT-YET | NOT-YET | basis now also names the 2019–2022 carve-out config (fuelmix 2019/2020, price_mean 2019, price_shape 2019/2020) |
| NWPP, PJM, SOCO | NOT-YET | NOT-YET | unchanged |

No stale folded rung exists today: the CAISO and NYISO touchpoints were solved at the same basis
sha as their keeper spans (`d757b216`, `38ea5423`).

## Markers revoked

- `calibration-complete.json`: `complete.CAISO` and `complete.SPP` moved to `withdrawn` (standing
  Q5 rule: a `complete` marker cannot stand on a NOT-YET keeper). `complete` now holds NEISO and
  PJM only.
- Forecast board `program-status.json`: CAISO and SPP gate (a) `pass → fail`,
  `marker_complete true → false`.
- Keeper shards: the `frontier` blocks of CAISO and NYISO renamed `frontier_withdrawn_2026_09_30`
  (text kept verbatim, withdrawal note added). NEISO's and PJM's frontier blocks stand.
- Not touched: PJM's `complete` marker already stood on a NOT-YET keeper before this change.
  The owner's card left it alone; it's flagged for the PJM lane.

## Lane follow-ups (each ISO's own lane, not done here)

- **CAISO, MISO, NYISO, SPP:** the headline is now NOT-YET. The per-ISO mechanism-matrix `gates`
  stamps still describe a CALIBRATED keeper. Re-stamp in the ISO's own shard at its next session
  (rule 28).
- **PJM:** `complete` stands on a NOT-YET keeper (pre-existing Q5 inconsistency).
- **Re-entry** of any withdrawn marker or frontier is a new explicit owner declaration, on a keeper
  whose v3.13 determination (every registered year) reads CALIBRATED.
