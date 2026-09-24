# FINDING — SOCO-60 [filed as soco-60b] (2026-09-23): the last failing row was a benchmark boundary defect; SOCO's two hydro repairs are merged

> **FILE NAMES.** A concurrent session (`claude/soco-60-hydro-keeper-reecxj`) also took the name SOCO-60 and merged its own `PRECOMMIT-soco-60-2026-09-23.md`, `_soco60_phase0.py`, `soco60_compose_span.py` and `gen_soco60_attestation.py` first. This lane's records were renamed `soco-60b` / `soco60b` on rebase; content is unchanged. That session was running the same hydro-merge arm this lane had already solved.

**Lane** SOCO-60 · **DATA PROFILE** soco · **Model** Opus (rule 27; scope wrote `src/` and `scripts/`).
**Control of record** keeper `2026-09-22-soco-h4-hydro-ror` (`results/calibration/soco_h4_ror_span`),
rule 29 (b) form 4. Its per-year legs were recovered at zero LP, and all 12 hourly sidecars are
byte-identical to the committed composite.
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-60b-2026-09-23.md`, pushed at `f8e534e6` (§1–§4) and
`71a23bb0` / `eab5c585` (addendum B), each before the solves it covers.
**Registered run** `2026-09-23-soco60-boundary-span` (bundle `results/calibration/soco60_boundary_span`).
**PROMOTED TO KEEPER 2026-09-23** on the owner's ruling (§10).

---

## 1. HEADLINE

1. **The precondition failed, and the owner ruled.** `main` named SOCO hydro-4's keeper, not
   SOCO-59's; SOCO-59's promotion never merged. The owner chose **option 3, merge the two recipes**.
2. **The merge is clean.** SOCO-59's `hydro_eia930_monthly` repair sits on the keeper's
   `hydro_ror_split` as one pipeline. 2023/2024 are byte-identical to the keeper. 2025 hydro goes
   6.329 → 5.920 TWh. **7 of 7 predictions confirmed.**
3. **2024 CC_REGULAR was failing on a BENCHMARK boundary defect, not a dispatch one.** SOCO's
   benchmark included the former Gulf Power plants, which EIA-930 SOCO has excluded since at least
   2019. It also subtracted a 6.35 TWh biomass "fold" that SOCO's EIA-930 gas cell does not contain.
   Together these scaled every SOCO fossil class down ×0.918. Repaired, 2024 CC_REGULAR reads
   **+4.43 TWh / +2.7 pp, PASS**. Before the repair it read +9.80 / +3.6 pp, FAIL.
4. **Every criterion passes: C1 14/14 · free 10/10, C2 / C4 / C6 / C8 PASS, C3 unscorable.** The
   scorer's literal output is `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`. It certifies no price, and per
   §5.8 house rule it is **not cited as SOCO's determination**.
5. **The flip is benchmark-side, and it applies to the keeper too.** Re-scored on the repaired bench
   parts, the incumbent keeper reads the same 14/14. The arm's own dispatch moves ≤ 0.023 TWh per
   class, and per-plant allocation is unchanged. The model still over-dispatches CC by 4.4 TWh and
   misallocates ~11 TWh across CC plants (§5).
6. **Three rows got worse on the repaired bench, and they are reported, not absorbed.** 2024 COAL_PRB
   −2.37 → −4.59, 2024 COAL_BIT −0.80 → −1.89, 2023 COAL_BIT −1.24 → −2.12 TWh, and CT_PEAKER is up in
   both years. The uniform scale had been hiding a model coal under-dispatch.

## 2. THE MERGED HYDRO RECIPE (PRECOMMIT §1–§3)

| # | prediction | outcome |
|---|---|---|
| P1 | 2023/2024 hourly sidecars byte-identical to control legs | **CONFIRMED** (all 8 files) |
| P2 | 2025 hydro 5.915–5.926 TWh | **CONFIRMED** 5.920 |
| P3 | 2025 CC_REGULAR 109.26–110.22 | **CONFIRMED** 109.837 |
| P4 | 2025 CT_PEAKER 4.95–5.67 | **CONFIRMED** 5.066 |
| P5 | 2025 ST_GAS 2.06–2.37 | **CONFIRMED** 2.221 |
| P6 | 2025 coal within ±0.15 of 48.342 | **CONFIRMED** 48.458 |
| P7 | 2025 unserved ≤ 287 MWh, ≤ 2 h | **CONFIRMED** 267.4 MWh, 2 h (2025-07-29, the routed net-export peak) |
| P8 / P9 | statuses and CC row unmoved on the old bench | superseded by addendum B (the bench itself was repaired) |

The 2025 repin clips 5 RoR plant-months at nameplate, losing 5.4 GWh (0.09 % of hydro). This is
recorded, not repaired.

## 3. THE BENCHMARK DEFECTS (ADDENDUM B)

**Where the gap was.** The 2024 CC_REGULAR "actual" was 104.91 TWh. The EIA-923 net generation of
the 18 CC plants the model carries is 110.31. The model's own plant-level CC total is 114.71.

**B1 — plant boundary.** The benchmark's membership is eGRID 2023 `BACODE`. It admits the former Gulf
Power plants: Lansing Smith 643 (CC, 3.97 TWh in 2024), Gulf Clean Energy Center 641, Pea Ridge 7715,
Perdido 57502, and three solar plants. EIA-860 codes them to FPL from vintage 2024. The model's own
fleet census (current 860, `BA == SOCO`) and its demand (EIA-930 SOCO demand + metered net exports =
930 SOCO net generation) never carried them.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| 930 / 923 fossil, **without** them | 0.997 | 1.008 | 1.004 | 1.006 | 1.002 | 0.981 |
| 930 / 923 fossil, with them | 0.962 | 0.971 | 0.968 | 0.973 | 0.965 | 0.943 |

**B2 — gas fold refuted.** The reconcile subtracted `OTHER + biomass − 930 Other` = 6.35 TWh (2024)
from the EIA-930 gas target. That subtraction assumes the 930 gas cell carries that much biomass. It
does not. SOCO 930 gas vs the 923 gas classes of in-BA plants, CHP included:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| 930 gas / 923 gas (TWh) | 125.06 / 127.88 | 125.88 / 126.08 | 120.99 / 121.89 | 130.64 / 130.96 | 129.59 / 130.23 | 126.08 / 129.54 |

SOCO's 923 biomass is 82–84 % CHP-flagged and 60 % black liquor: pulp-mill recovery boilers the BA
does not meter.

**Neither repair crosses on its own.** B1 alone leaves 2024 CC_REGULAR at +9.28 TWh, because the fold
still fires the reconcile at ×0.956. B2 alone reaches +5.62 TWh / +3.0 pp and still fails on share.
Each rests on its own six-year EIA-930 evidence.

**Implementation** (zero free parameters):
- `constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE = {"SOCO": True}`, consumed at
  `run_calibration_full._iso_plant_ids`. This is the one seam the benchmark frame, its class shares and
  the must-run injection read. It is declared at `False`, so **SOCO's cache key moves**: 185 surface
  rows, 1 moved. No other ISO moves.
- `benchmark_semantics.EIA930_GAS_FOLD_REFUTED = {"SOCO"}` (benchmark only).
- Tests: `tests/unit/data/test_iso_membership_ba_recode.py`, plus
  `test_gas_foldin_deflation_refuted_ba_is_zero`.

## 4. ADDENDUM B PREDICTIONS

| # | prediction | outcome |
|---|---|---|
| Q1 | 2024 CC_REGULAR +4.41 ± 0.05 TWh / +2.7 ± 0.1 pp, PASS | **CONFIRMED** +4.43 / +2.7 |
| Q2 | 2023 CC_REGULAR +2.04 / +1.2 pp | **CONFIRMED** +2.05 / +1.3 (+2.30 after rebasing onto miso-267's CAMPD-backfill operating-window change on `main`, a benchmark-only hunk) |
| Q3 | 2023 ST_GAS −5.50 / −2.3 pp | **CONFIRMED** −5.50 / −2.3 |
| Q4 | 2024 ST_GAS −4.91 / −1.9 pp | **CONFIRMED** |
| Q5 | 2024 COAL_PRB −4.58 / −1.6 pp (worse) | **CONFIRMED** −4.59 |
| Q6 | COAL_BIT −2.12 / −1.89 (worse) | **CONFIRMED** |
| Q7 | CT_PEAKER +5.22 / +1.73 (worse) | **CONFIRMED** +5.23 / +1.73 |
| Q8 | dispatch: biomass −0.017 / −0.015 / 0…−0.015; every other class \|Δ\| ≤ 0.02 TWh | **PARTIAL**: biomass −0.0174 / −0.0145 / 0.0000 exact; **2024 CC_REGULAR +0.0228 breaches the 0.02 band** |
| Q9 | C1 14/14 | **CONFIRMED** |

**Record: 15 confirmed, 1 partial, 0 falsified** (P1–P7 and Q1–Q9, with P8/P9 superseded).

## 5. CHECKS D / E / F

- **D — every scored row's margin, repaired bench.** The thinnest row is **2024 CC_REGULAR share:
  +2.7 pp of ±3.00, a 0.3 pp margin**. Next are 2023 ST_GAS −2.3 pp and 2023 CT_PEAKER +2.2 pp
  (0.7–0.8 pp). C4 is unchanged from the keeper (2024 coal NRMSE 0.240, r 0.847). C8: ST_GAS 2023 is
  15.9 % forced, a lower bound.
- **E — per-plant allocation, Σ\|model − 923\|** (ex-Gulf actuals; keeper → arm B):
  - CC_REGULAR: 10.887 → 10.886 (2023), 11.089 → 11.073 (2024);
  - coal: 6.294 → 6.297, 9.730 → 9.743;
  - ST_GAS: 5.424 → 5.423, 4.911 → 4.910.

  The class-level pass sits on an unchanged ~11 TWh CC misallocation. The over-dispatched tail is E B
  Harris +2.0, Tenaska Lindsay Hill +1.7, H Allen Franklin +1.5 and Central Alabama +0.9 TWh. The
  under-dispatched side is Thomas A Smith −1.1 and Jack McDonough −0.6 TWh.
- **F.** If the only argument for B1 or B2 were that 2024 CC_REGULAR passes, neither would be
  taken. Both stand on EIA-930's own SOCO accounting from 2019 to 2024, and both make the coal rows
  worse.

## 6. THE FOUR NAMED CC LEADS — not opened

Capacity basis, net interchange, ST/CC fuel separation and the CC tail were not needed to explain the
class row. They remain the right leads for the **per-plant** misallocation in §5 E. Two of them are
now measured:
- **Model CC pmax vs EIA-860 summer, 2024.** Totals are 18,652.9 vs 18,699.3 MW across the model's
  18 plants. The fleet is not over-rated in aggregate, so a summer-derate lever has little TWh in
  reach at class level.
- **Model demand.** It is EIA-930 SOCO net generation, so the interchange lead reduces to "SOCO
  exports what it meters".

## 7. ROUTED

1. **CC per-plant misallocation (~11 TWh/yr).** This is the real remaining CC defect. Leads: the
   over-dispatched tail above, and heat rate is already measured at 16/18 plants (SOCO-57).
2. **Coal under-dispatch, now visible.** 2024 COAL_PRB −4.59 and COAL_BIT −1.89 TWh on the repaired
   bench.
3. **ST_GAS.** 2023 is −5.50 TWh; SOCO-54 §4's fuel separation is still open.
4. **2025 unserved 267 MWh (2 h).** At the 2025-07-29 peak, model demand equals EIA-930 demand plus
   13 TWh/yr of metered net exports. The demand basis is routed.
5. **Other ISOs.** Neither repair transfers (rule 25). Any ISO whose eGRID BA codes lag its current
   EIA-860 codes has the same exposure; the matrix row is seeded `U` everywhere else.
6. **D79 note.** The membership row was declared at its pre-arm value on purpose, so SOCO's key moves.
   SOCO is not in `PINNED_SURFACE_ROWS_BY_ISO`.

## 8. COST AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: zero.** Six shards, one year each, ~8–13 min wall each (solves 93–122 s, peak
  8.0–9.6 GiB). All six were archived after fetch, checkout and verification.
- **On `main` once this PR merges:** the candidate bundle `results/calibration/soco60_boundary_span`
  (17 files, rule-15 shape), its sidecar and run payload, and SOCO's repaired bench parts. **A
  promotion from that state costs zero re-solves.**
- **Per-plant layer** (`dispatch/`, `floors/`): only in the gitignored legs on this container. Leg
  SHAs are provenance only (rule 33 (d)):
  - arm M: 2023 `176758278c39ced804b12ce932ee7046ff7d7bfe`, 2024
    `4f39643a6795c308bf3bd0dbd5ca71603da307d6`, 2025 `00a013232bb54754aa2717073f70098a2a4e2f9b`;
  - arm B: 2023 `02b50bfcfd03e0644170b537162dbeea75ea3885`, 2024
    `1f129c954ac094dbf0cb782461b7f591b80e3b09`, 2025 `df1d5eb0c4c04fc48ba49538ae132f1810651ca8`.

  Cost any later need for the per-plant layer as a re-solve: 3 × ~2 min LP.
- **Arm M (the hydro half alone) was not registered.** Its 2023/2024 legs are byte-identical to the
  keeper, its 2025 leg equals arm B's 2025 leg exactly, and its numbers are all in §2. Registering it
  at this HEAD would have scored a pre-B1 injection against a post-B1 benchmark. This is a stated
  departure from rule 15's letter; I can register it on request.
- **Gate noise, machine-verified:**
  - `check_registry_payload_parity` is RED locally only, on 11 gitignored legs with 0 tracked files;
  - `audit_keepers` E13 × 2: `2026-09-20-soco53g-prb-own-iso` (unruled, the **fourteenth** lane)
    and this candidate;
  - `check_bench_freshness`: SOCO's parts are fresh; 21 other-ISO parts are STALE, all pre-existing;
  - 11 pre-existing failures in the touched test files are identical on `main`.

## 9. THE PROMOTION QUESTION (rule 31)

**Recommendation: promote `2026-09-23-soco60-boundary-span`.** It carries the recipe you asked for (both
hydro repairs), and its benchmark boundary is right on six years of EIA-930 evidence.

**Against it:**
- The C1 pass is a benchmark effect that the current keeper also inherits once these bench parts land.
- The 0.3 pp share margin is thin.
- Coal now reads worse.

**If promoted**, rule 35 prunes `2026-09-22-soco-h4-hydro-ror` (years covered: 2023–2025, same set),
at zero LP. **If declined**, the bench repair still stands, and the keeper's reading still changes.

**Standing E13:** `2026-09-20-soco53g-prb-own-iso` still awaits a ruling. The standing recommendation
is to decline it.

## 10. THE PROMOTION — EXECUTED 2026-09-23 ON THE OWNER'S RULING

The owner ruled, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."* It was recommended (§9), so it
was promoted.

Rule 35 was executed in order:
- **(b)** Enumerated the year union over all four SOCO sidecars first: {2023, 2024, 2025}.
- **(c)** The incoming span covers that union.
- **(e)** Wrote the designation (`superseded.reason` captures the outgoing lineage and the E11
  `composed_from` rename), rebuilt `build_status --iso SOCO`, and confirmed `audit_keepers` E1 passes.
- **(a)** Only then ran `prune_iso_runs.py --iso SOCO --keep 2026-09-20-soco53g-prb-own-iso
  --force-uncite`. It removed `2026-09-22-soco-h4-hydro-ror` and `2026-09-22-soco59-hydro-split`;
  SOCO-59's recipe is a strict subset of the incoming one, and the owner's "merge" ruling superseded
  its own promotion.

Other promotion notes:
- **Kept (unruled):** `2026-09-20-soco53g-prb-own-iso`. `audit_keepers` E13 fires for it alone.
- SOCO has no `calibration-complete.json` entry to re-key.
- The matrix shard and §5.8 header are re-stamped.
- Before promoting, the branch was rebased onto `main` @ `0d6cc473`, which carries SOCO-59's merged
  records and miso-267's benchmark change. The keeper was re-registered at that HEAD.

## Log entry

```
## soco-60 — 2026-09-23

THE PRECONDITION FAILED AND THE OWNER RULED. main named SOCO hydro-4's keeper
(2026-09-22-soco-h4-hydro-ror); SOCO-59's promotion never merged. Owner: option
3, merge the two recipes. SOCO-59's unique records were rescued onto main.

MERGED HYDRO. SOCO-59's hydro_eia930_monthly (+ backfill 2024, PS-split row)
on the keeper's hydro_ror_split, one pipeline. 2023/2024 byte-identical to the
keeper; 2025 hydro 6.329 -> 5.920 TWh; 7/7 predictions confirmed.

THE LAST FAILING ROW WAS A BENCHMARK DEFECT. 2024 CC_REGULAR's actual (104.91)
sat 5.4 TWh below the EIA-923 of the model's own 18 CC plants (110.31). B1:
eGRID 2023 admitted the former Gulf Power plants (Lansing Smith, Gulf Clean
Energy Center, Pea Ridge, Perdido, 3 solar) that EIA-860 recodes to FPL from
vintage 2024 and that EIA-930 SOCO has excluded 2019-2024 (930/923 fossil
0.997-1.008 without them, 0.943-0.973 with). B2: the gas-fold deflation took
6.35 TWh of "folded biomass" off SOCO's 930 gas target; SOCO 930 gas <= 923 gas
every year, so the fold does not exist (biomass is 82-84 % CHP, 60 % black
liquor). Together they removed a x0.918 scale from every fossil class.
Repairs: constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE={SOCO: True} (one
seam; injection -0.017/-0.015 TWh biomass; SOCO key moves) and
benchmark_semantics.EIA930_GAS_FOLD_REFUTED={SOCO}. New matrix row
iso_membership_current_ba_recode.

RESULT (run 2026-09-23-soco60-boundary-span, CANDIDATE). C1 14/14 · free
10/10, C2/C4/C6/C8 PASS, C3 unscorable, grade 5/5/0, DOF 12/1. 2024
CC_REGULAR +9.80/+3.6pp FAIL -> +4.43/+2.7pp PASS (share margin 0.3 pp). THE
FLIP IS BENCHMARK-SIDE: the incumbent keeper on the repaired parts reads the
same; dispatch moves <= 0.023 TWh/class; per-plant CC misallocation unchanged
at ~11 TWh. WORSE, reported: 2024 COAL_PRB -2.37 -> -4.59, COAL_BIT -0.80 ->
-1.89 TWh, CT_PEAKER up both years. Predictions 15 confirmed / 1 partial
(Q8: 2024 CC +0.0228 vs a 0.02 band) / 0 falsified. Scorer's literal output
PHYSICALLY-CALIBRATED (PRICE UNSCORED) is not cited as SOCO's determination.
The four named CC leads were not needed; they stay the leads for per-plant
allocation. PROMOTED 2026-09-23 on the owner's ruling; h4-ror and soco59-hydro-split pruned (rule 35).
E13 for soco53g re-raised, fourteenth lane. Records:
docs/handoffs/PRECOMMIT-soco-60b-2026-09-23.md,
docs/handoffs/FINDING-soco-60b-2026-09-23.md (filed as 60b: a concurrent
session also named SOCO-60 merged first), scripts/gen_soco60b_attestation.py,
scripts/probes/_soco60b_phase0.py, scripts/probes/soco60b_compose_span.py.
```
