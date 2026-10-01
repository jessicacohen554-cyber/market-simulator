# HANDOFF — CAISO scorer: the plant-allocation coverage gap (caiso-282)

Written by caiso-281, 2026-09-14. Evidence is measured, from committed artifacts only, and is
reproducible with `scripts/probes/_caiso281_two_objects.py`.

## The object

**No criterion in the rubric sees within-fleet plant allocation.** `CRITERIA` carries eight
entries (C1, C2, C3a, C3b, C3c, C4, C6, C8); the only hourly-dispatch criterion is **C4**, and
`calibration_verdict._cems_gas_hourly_fit` **sums over plants before** calling `_pearson_nrmse`.
So C4 scores a FLEET-TOTAL series, and a plant-for-plant swap at constant fleet total cancels
exactly.

Measured on the CAISO keeper `2026-09-12-caiso-275-gascoupling`, 2025:

| | |
|---|--:|
| fleet bias (what C4 sees) | **+0.41 %** (model 5,334 vs actual 5,313 MW) |
| per-plant errors surviving aggregation (`rho_agg`) | **0.383** (2022: 0.363) |
| material plants off > 50 % on annual energy | **11 of 28** |
| median absolute per-plant annual error | **17.5 %** |

Worst offenders, all offsetting: Alamitos **+120 %**, Panoche **−94 %**, Huntington Beach
**+92 %**, Von Raesfeld **−87 %**, Moss Landing **+86 %**.

**~62 % of per-plant absolute error cancels in aggregation and is scored by nothing.** A keeper can
have half its material gas fleet individually wrong by more than half and still pass C4.

This is a **coverage gap, not a bug** — C4 does exactly what it says. Nothing is miscomputed.

## What is already adjudicated — do not re-open

* **Panoche (−94 %)** is the DECLARED PERMANENT RESIDUAL (owner ruling 2026-09-06, caiso-261):
  un-groundable from the public record, no floor/pin/window may be built to reach it. It must be
  EXCLUDED from any new criterion's failing set, or the criterion re-litigates a closed decision.
* **C7 diurnal shape was RETIRED** (v3.1, 2026-08-06) on the finding that no commercial-grade
  comparable gates diurnal-shape accuracy. Any new criterion must clear that same bar or it will
  be retired for the same reason. **Have the argument before building it.**
* **C5a/C5b/C5c were removed** because their actuals are not measured for every scored year.
  CAMPD per-plant hourly IS measured for every scored year, so a plant-allocation criterion does
  not fail on that ground — but say so explicitly rather than assuming it.

## The job

1. **Build the measurement, ungated first.** Per-plant hourly model-vs-CAMPD from the committed
   payload/bench (`plants[].m` / `plants[].campd`, uint8 CF% of `npl`). Report per-ISO and
   per-plant. `_caiso281_two_objects.py` already decodes both sides — reuse it, do not re-derive.
2. **Establish whether it discriminates.** Run it over EVERY registered keeper in every ISO. If
   all seven ISOs look equally bad, it is a model-class property and gating it would fail every
   keeper at once — which is a finding, not a criterion. If CAISO is an outlier, say by how much.
   **This step decides whether the rest is worth doing.**
3. **Only then propose a gate, to the OWNER.** Adding a scored criterion is a rubric change and an
   owner act (`docs/calibration-determination-rubric.md` §9 records every prior amendment as one).
   Propose tier, threshold, materiality floor and exclusion set with the step-2 evidence attached.
   **Do not add a criterion unilaterally.**

## Two smaller items, both real

* **`rt_lw` weighting is undocumented and it cost me an hour.** Bench `avgLMP` carries `rt`
  (equal-hour) and `rt_lw` (load-weighted). Reconstructing `rt_lw` with the MODEL's demand gives
  **83.759** against the committed **84.490** for CAISO 2022; the hourly series is right (simple
  mean reproduces `rt` **79.07** at **79.072**). The weight is ACTUAL load, not model demand.
  Document it at the `avgLMP` construction site so the next reconstruction does not misfire.
* **A stale rule-22 gate in `scripts/data/fetch_caiso_public_bids.py`.** `main()` rejects
  `--years` outside 2023-2025 citing "CLAUDE.md rule 22", but `[R-HOLDOUT]` was REMOVED 2026-09-09
  and any year may now be solved and fetched. `--start/--end` bypasses it, which is why the
  2020-2022 backfill works, but the message cites a rule that no longer exists. One-line fix.

## Rules that bind this lane

* Rule 27 `[R-PUSH]`: `scripts/calibration_verdict.py` is ~3.7k lines. Edit locally, push exact
  on-disk bytes, verify the blob after any push touching it. Opus or Fable only.
* Rule 1 `[R-STRUCT]`: a criterion is chosen for what it measures, NEVER for which keepers it
  passes or fails. Fix the threshold before you see the per-ISO spread, not after.
* Rule 26 `[R-DELETE]`: if a criterion is rejected, delete it — do not leave it computed-but-off.
* Do not touch another ISO's keeper shard (rule 25 `[R-ISO-SCOPE]`).

## State you are inheriting

CAISO keeper `2026-09-12-caiso-275-gascoupling` — CALIBRATED 2023-2025, single ledgered C3c.
caiso-281 spent ZERO LP, promoted nothing, moved no cell. Its results:
`docs/RESULT-caiso281-two-objects-not-one-and-the-bias-is-a-basis-artifact-2026-09-13.md`
(the 2022 price miss and the 2025 gas miss are different objects; the marginal-HR bias does not
survive the DA basis) and the RTM public-bid intake
(`docs/PRECOMMIT-caiso281-rtm-offer-surface-intake-2026-09-13.md`), 11 quarters of 2023-2025
committed under `results/rtm-intake/caiso281/`, with a 2020-2022 backfill in flight.
