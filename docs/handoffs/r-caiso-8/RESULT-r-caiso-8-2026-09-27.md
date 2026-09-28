# RESULT — R-CAISO-8: 2021 partial-year hub pricing promoted; ST_GAS peak registry re-synced; SD import limit censused (2026-09-27)

**PROMOTED `2026-09-27-caiso-r8-partial-year`** (bundle `rcaiso8_A_span`, 2022–2025), CALIBRATED, on the owner's
instruction *"When done promote if a good candidate"*.
- Fold: `2026-09-27-caiso-r8-fold` (bundle `rcaiso8_A_tp_2019_2021`), stamped to the keeper.
- Pruned per rule 35(a): `2026-09-26-caiso-r5-pastoria-co2` and `2026-09-27-caiso-r6-malin-fold`.
- Year set 2019–2025, before and after.
- The complete marker stands (re-keyed; determination re-verified CALIBRATED).

PRECOMMIT: `PRECOMMIT-r-caiso-8-2026-09-27.md` (directions pre-registered; G-DRIFT §6).

## What changed

- **(A) `caiso_intertie_partial_year_measured`** (new, default off, armed in the keeper).
  - A hub is priced at its measured print in every printed hour; the ladder stays only in unprinted hours.
  - Pricing and the clean-depth arming now read one per-hour mask.
  - G-DRIFT: 2021 `mc_base` is the only LP-visible array it moves, 2019–2025.
- **(B) Object 3.** `ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO["CAISO"]` 1.166 → 1.154.
  - The artifact is the side that moved: `df277e89` re-froze CT_PEAKER peak to 1.154 on 2026-09-06, and caiso-257
    re-applied it (`48bcd0ec`). The registry dates from caiso-240 (09-03) and did not follow (rule 23).
  - Footprint: 3 rows (plants 315/335/350, peak tranche, 429 MW), −$0.46 to −$0.53/MWh.
  - Largest annual class change 395 MWh (2022); 2025 byte-identical.
  - `test_caiso_st_gas_peak_measured` now passes.

## Scores (full magnitude)

**2022–2025 (keeper): CALIBRATED.** Every criterion is identical to the outgoing keeper at scored precision.
- C3a: +8.8 / +7.1 / +6.6 / +8.7 %
- C3b NRMSE: 0.110 / 0.114 / 0.125 / 0.112
- C4 gas: r 0.896 / 0.904 / 0.914 / 0.880; NRMSE 0.263 / 0.250 / 0.260 / **0.299** (thin, unchanged)
- C3c: single ledgered caveat, 2024 (0 h vs 35 h)

**2019–2021 (fold, reported only, rule 30(c)): NOT-YET, as before.**

| 2021 | fold before (r6) | after (r8) | pre-registered |
|---|--:|--:|---|
| CC_REGULAR TWh (actual 49.2) | 68.6 | **59.3** | down ✓ |
| total imports TWh | 37.5 | **46.1** | up ✓ |
| DSW net import TWh (EIA-930 40.9) | 15.8 | **29.5** | up ✓ |
| PNW net import TWh (EIA-930 13.6) | 21.8 | **16.5** | down ✓ |
| SP15 mean price $/MWh | 56.4 | **54.2** | down ✓ |
| C1 CC_REGULAR | +19.4 FAIL | **+10.1 FAIL** | |
| C3a mean LMP | +17.6 % FAIL | **+13.5 % FAIL** | down ✓ |
| C3b NRMSE | 0.211 FAIL | **0.158 PASS** | |
| C4 gas NRMSE / r | 0.422 / 0.832 | **0.387 / 0.816** FAIL | NRMSE down ✓ |
| C3c > $200 h (actual 27) | 108 | 108 | |

- 2019 and 2020 are unchanged on every gated score. C1 CC_REGULAR stays +20.4 / +24.8 TWh: no hub print, so the
  STOP stands.
- The remaining 2021 DSW gap is 11.3 TWh: mean −2.9 GW at h17–22, −1.1 GW at h0–6, −0.3 GW at h8–16. The
  split between the unprinted Jan–Apr hours and the rest is not measured here.

Corridor census: `scripts/probes/_rcaiso8_2021_corridor_census.py` → `results/calibration/_rcaiso8/object1_2021_corridors.json`.

## Object 2 — SD import limit (zero LP, no arm)

Probe: `scripts/probes/_rcaiso8_sd_import_census.py` → `results/calibration/_rcaiso8/object2_sd_census.json`.

- **No public, measured, per-year operating SD import limit exists.**
  - CAISO OP 7820 (San Diego Area, "SDGE import" control points) is non-public.
  - The OASIS `PRC_NOMOGRAM` 7820_* constraints are S-Line / IV SPS, not an SD import nomogram.
  - The LCT reports give no normal-condition import figure.
  - WECC Path 44 was deleted in 2015.
- **The LCT `peak − LCR` is not a transfer limit.** In 2020 and 2022 the LCR equals all area resources at peak, so
  the difference is resource-limited.
- **Measured realized import exceeds the LCT cap.** Night lower bound (all in-zone non-solar counted at nameplate,
  so a strict lower bound):

| year | LCT cap MW | lb p50 / p99 / max | night hours lb > cap |
|---|--:|--:|--:|
| 2019 | 386 | 1,036 / 1,643 / 1,908 | 2,773 (95 %) |
| 2020 | 718 | 458 / 1,206 / 1,565 | 784 |
| 2021 | 635 | 424 / 1,155 / 1,351 | 886 |
| 2022 (not landed) | 587 | 69 / 845 / 1,143 | 211 |
| 2023–25 | 1,436 / 2,074 / 2,071 | ≤ 843 p99 | 0 (not tested: battery nameplate grows) |

- The only documented operating-basis number is CAISO's all-lines-in-service SDG&E simultaneous import limit of
  **4,200 MW** (CPUC D.08-12-058 fn 331; a 2008, pre-Sunrise planning assumption; G-1/N-1 3,500).
- A realized-import percentile is **not** admissible as a cap (rules 13/21). It is evidence only.
- **Owner decision** (card): what the SD link should carry. The 2019–21 caps are the ones this finding convicts.

## Owner rulings (decision cards, 2026-09-27)

1. **SD import limit: "Floor at static 1,436".** Keep the per-year LCT caps but never below the documented static
   1,436 MW. Only 2019–21 move. It is a declared rule-14 reconciled estimate, itself exceeded 167 h in 2019. Routed
   to R-CAISO-9.
2. **`EIA930_GAS_FOLD_REFUTED` for CAISO: "Keep as is".** Not flipped; do not re-raise without new evidence.

## Retrievability (rule 34(e))

- On `main`: `rcaiso8_A_span` and `rcaiso8_A_tp_2019_2021` (slim set + hourly sidecars + attestation + diagnostics).
- Per-year legs are gitignored. Provenance SHAs:

| year | shard commit |
|---|---|
| 2019 | `43b093c0f5775b81fef1f12443678e1692ca6747` |
| 2020 | `e7a9c42157cab3c0f8087e0b4d67f96189398256` |
| 2021 | `2b93619a3dc242ec09dfb06800d54ccd1011154f` |
| 2022 | `dce7427c9bf9217e67e8badf2a7e86ca719efaef` |
| 2023 | `f920c4dd5341a03cc58b0f847f5198ad694d8b96` |
| 2024 | `b3bc5fd293979c25c11454678db06587916fce17` |
| 2025 | `3162dbbb729bd2f6d786dc4e62dfdcad8aaa7bbc` |

- These are provenance, not a recovery route (rule 33(d)). Any leg not on `main` costs a ~25 min re-solve.

## Housekeeping

- All 7 shards archived.
- **Process defect, recovered at zero LP.** `prune_iso_runs.py --iso CAISO` without `--keep` also pruned the
  just-stamped new fold. It keeps only the keeper shard's id, not runs stamped to it. The fold was re-composed from
  the local legs and re-registered, with identical numbers.
- The fold's first registration used a label whose shorthand collided with the span's run id and overwrote it; the
  span's files were restored from the commit.
- Successors: pass `--keep <fold id>` to the prune, and give the fold a label whose shorthand differs.
- Leftover branches for the owner to delete:
  - `claude/r-caiso-6`, `claude/r-caiso-6-O2-2019/2020/2021`, `claude/r-caiso-7`
  - `claude/r-caiso-8-A-2019` … `-2025`
  - `claude/r-caiso-8` once merged, if not auto-deleted
