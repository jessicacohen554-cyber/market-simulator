# RESULT — R-CAISO-6: 2019–21 fold re-solved on corrected import inputs; C4 midday shape has no lever (2026-09-27)

PRECOMMIT: `PRECOMMIT-r-caiso-6-2026-09-27.md`, pushed at `43381587` / `6810e68e` before any shard. The parent
spent zero LP: 3 shards, one per year (rule 36).

## Headline

- **Keeper unchanged:** `2026-09-26-caiso-r5-pastoria-co2`, CALIBRATED. 2022–25 are byte-identical at HEAD
  (G-DRIFT, PRECOMMIT §3), so no re-solve and no promotion decision is needed there.
- **Object 1 (C4 midday imports): no admissible lever. STOP.** The excess is PNW's missing midday export
  (cells R/G) plus economic imports clearing on price. A per-corridor firm-shape repair was censused at zero LP
  and not armed.
- **Object 2:** a real intake bug was fixed. The MIC parser had dropped Malin 500 for 2018–20.
  - 2019–21 now carry their own firm-import rows and LCT area peaks.
  - The fold was re-solved and re-registered as **`2026-09-27-caiso-r6-malin-fold`** (bundle
    `rcaiso6_tp_2019_2021`), stamped to the keeper. It supersedes `2026-09-27-caiso-r5-xe-keeper`, which is
    pruned.
- **Object 3 (C3c 2024):** characterised; no input defect. The ledgered caveat stands.

## Object 2 — fold before / after (reported only; rule 30(c): these years never gate the ISO)

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| seam-import cap, MW | 12,154 → **15,208** | 12,394 → **15,524** | 15,820 (unchanged) |
| firm block PNW / DSW, MW (was 1,566 / 1,805) | 2,262 / 2,442 | 2,240 / 2,459 | 1,305 / 1,466 |
| CC_REGULAR TWh (actual 36.1 / 43.1 / 49.2) | 62.1 → **56.5** | 70.9 → **67.9** | 67.2 → 68.6 |
| imports TWh | 32.9 → 37.7 | 34.1 → 38.8 | 40.4 → 37.5 |
| C4 gas NRMSE | 0.664 → **0.575** | 0.595 → **0.530** | 0.384 → 0.422 |
| C3a mean LMP, model vs RT 50.87 | — | — | 58.66 → 59.83 (FAIL both) |
| C3b | — | — | 0.189 PASS → **0.211 FAIL** |
| C3c > $200 h (actual 27) | — | — | 90 → 108 (CAVEAT) |
| Determination | NOT-YET | NOT-YET | NOT-YET |

- The pre-registered directions held: CC_REGULAR fell in 2019–20 (+1.3 GW firm, +3 GW seam cap) and rose in
  2021 (−0.6 GW firm).
- **2021 is worse on four scores.** The reason is the measured 2021 RA-import level (DMM Table 9.4, 2,771 MW),
  which is lower than the 2025 static block it replaced. Rule 14: the measured input stays. The worse fit points
  at another miscalibration; it is not a reason to restore the estimate.
- All three years still over-dispatch CC_REGULAR by +19 to +25 TWh. That is the dominant 2019–21 residual, and
  the successor object below.
- C1 / C4 / C8 / C6 otherwise hold; DOF 9/6 carried; offer curves unchanged.

## Object 1 and Object 3

See PRECOMMIT §1 and §5; nothing changed after the shards.

- **Object 1.** Midday excess h8–16: PNW +886 / +1,466 / +1,277 / +1,146 MW; DSW +676 / +581 / +871 / +720 MW
  (2022–25). Measured PNW is a net exporter at midday.
- **Object 3.** 25 of the 35 hours are 13–16 Jan 2024 (gas event, model at 70–85 % of RT). The other 10 are
  RT-only spikes (DA well below RT in 8).

## Promotion (rule 31)

- The keeper is not changed, so there is no promotion question for 2022–25.
- The fold refresh is the same keeper recipe on corrected measured inputs. It was registered, stamped and
  swapped in under the owner's standing instruction.
- **Owner can reverse it:** the prior fold's three stores are in git history at `92479835`.

## Routed, owner decision (not taken)

1. **2022 LA Basin / SD-IV peak_load rows** (Final 2022 LCT: 18,929 / 4,580 MW) exist and are not landed.
   Landing them moves the keeper's 2022 leg: the SD import cap becomes 587 MW vs the static 1,436. That would
   mean one re-solve and a keeper re-composition.
2. **`EIA930_GAS_FOLD_REFUTED` for CAISO** (carried from R-CAISO-5 §6). It raises the 2019–21 CC_REGULAR bench
   targets ≈ +5.5 / +3.9 / +2.4 TWh and moves 2022–25 by nothing.
3. **Stale comments** at `envelopes.py` ~l.614–622 and `calibration_verdict.py` ~l.2131 (carried).
4. **Forecast lane:** the Malin fix and the 2019–21 rows change any CAISO T1-H hindcast that solves 2019–21.
   Those bundles re-solve on their own cadence.

## Retrievability (rules 33/34)

- **On `main` after merge:** `rcaiso6_tp_2019_2021` (slim set + hourly sidecars + attestation + diagnostics),
  its sidecar and its payload.
- **Per-year legs:** gitignored, on this session's disk only; each costs ~20 min to re-solve.
- **Leg provenance:** 2019 `11d774b8f12996441fa8d00c9a1a1db59c540fc5`, 2020
  `daee04299af666298d007cb540642bb93069e41d`, 2021 `e419162ab6c039a8ac72709fd055724d7b832f08`.
- **Shards:** all 4 archived, including a redundant 2020 replacement that was interrupted before it pushed.
- **Leftover branches for the owner to delete:** `claude/r-caiso-6-O2-2019/2020/2021` and
  `claude/r-caiso-5-XE-2019/2020/2021`.
