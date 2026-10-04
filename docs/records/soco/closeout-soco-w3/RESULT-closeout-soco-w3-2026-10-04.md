# RESULT closeout-SOCO-w3 — candidate 1, the BTM mill-cogeneration holdout, 2019–2025

Lane closeout-SOCO-w3, 2026-10-04. Scored against the bars fixed in
`PRECOMMIT-solve-closeout-soco-w3-2026-10-04.md` (pushed at `487bfdb8` before any shard launched). Phase 0:
`FINDING-closeout-soco-w3-phase0-2026-10-04.md`.

**Run.** `2026-10-04-closeout-soco-w3-btm`, bundle `results/calibration/closeout_soco_w3_span`, years 2019–2025.
Registered as a probe on `claude/closeout-soco-w3-reg` only (audit E13 refuses an unpromoted SOCO run on main).
**Not promoted.**

**Recipe.** Keeper `2026-10-03-closeout-soco-3-coalpile` replayed with one override,
`mustrun_chp_btm_holdout=true`. No src change to the solve path. Pin `487bfdb84d775dd81e269727262fe24921cb6073`.
G-DRIFT keeper legs `0629d795` → pin: 0 LIVE / 33 INERT.

## 1. Legs

| Year | Shard branch @ commit (transport only) | Holdout (log / footprint) | Biomass injected (keeper → arm, TWh) |
|---|---|---|---|
| 2019 | `claude/closeout-soco-w3-2019` @ `191d0f39c171741cef012e8118d753d875bc0093` | 8.789 TWh, 72 of 484 rows | 9.489 → 0.936 |
| 2020 | `claude/closeout-soco-w3-2020` @ `7fc049049995099c9f2682655935f4c26cc582df` | footprint 8.695 | 9.916 → 1.445 |
| 2021 | `claude/closeout-soco-w3-2021` @ `c921c37a7adbcf26014aa07861e008e1228591c6` | footprint 8.528 | 9.935 → 1.584 |
| 2022 | `claude/closeout-soco-w3-2022` @ `9de61f56f08ddf55548cf9296a9fa91cc14dfea6` | footprint 8.269 | 9.648 → 1.564 |
| 2023 | `claude/closeout-soco-w3-2023` @ `40b4ad8b9bb1bd13c50177151df519340bb52a23` | footprint 7.378 | 8.804 → 1.565 |
| 2024 | `claude/closeout-soco-w3-2024` @ `b2f88e08d8f91a66b3b4e7cef3cee7e46c1ee339` | footprint 7.999 | 9.301 → 1.488 |
| 2025 | `claude/closeout-soco-w3-2025` @ `e26441af2acae5fb04b25d14021b2c70d39221f0` | footprint 7.120 | 8.45 → 1.486 |

Each leg: 18 files including `dispatch/<Y>_P1.parquet` (8.8–11.2 MB, no re-encode), `mustrun_chp_btm_holdout: true`
at `basis_sha 487bfdb8…`, fetched, bytes held locally, then archived (rule 33). Memory peak ≈ 3.1 GiB. LP ≈ 95 s per
pass.

**Compose.** `scripts/probes/_closeout_socow3_compose.py` (the W0 composer + the one arm field); recipe check passed.

### Benchmark seam: a rebuild-reader defect, fixed in this PR

The composer re-pointed the span at the keeper's shared `eia923` bench (the legs' own armed bench frames live in each
shard's gitignored `_shared/` store and were never pushed). The in-repo rebuild (`--rebuild-benchmark`) then rebuilt
the **un-partitioned** bench: `_build_benchmark_frames` recovered `mustrun_chp_btm_holdout` from the run_config's top
level and `calibration_flags` only, while `replay_keeper --set` records it only in `scenario_config` — the same
defect PJM-NEXT fixed on the sibling `benchmark_membership_vintage_union`. Fixed as
`run_calibration_full._run_config_mustrun_chp_btm` (reads all three blocks) with a fast unit test. Scoring-side only:
the solve path reads the flag through `_caiso_demand_flag`, which already saw the generic bag (the shard logs show the
holdout line). With the fix the rebuilt span bench reads 2019 biomass 0.936 TWh = the injected 0.936, a_gen 246.0 TWh.

Disclosed: `--restore-shared-inputs` on the 2019 leg regenerated the bench to `eia923-9b174391f734` against the
shard-recorded `eia923-97d8b7a5a186`. The regenerated frame carries the holdout and the same class totals; the
shard's bytes were never pushed, so the byte difference cannot be attributed here. The span is scored on the bench
rebuilt in this session (`eia923-f262aa59e76d`).

## 2. Kills

| # | Kill | Reading | Verdict |
|---|---|---|---|
| K1 | unserved or dump > 0 | 0 MWh every year | clear |
| K2 | C8 FAIL / new D-4 failure | `forced_share` PASS every year; ST_GAS forced share **falls** (2019 36.0 → 30.9 %, 2023 42.5 → 34.4 %) | clear |
| K3 | recipe diff beyond the arm | composer check passes | clear |
| K4 | arm not live | holdout line in the shard log; biomass drop equals the footprint in every leg | clear |
| K5 | C2 sysvol FAIL | PASS every year | clear |

## 3. Bars

| Bar | Keeper | Probe | Reading |
|---|---|---|---|
| **T1** C1 CC_REGULAR 2019 | FAIL +3.97 TWh / +3.2 pp | **PASS +6.23 TWh / +2.6 pp** | **met** |
| **T2** C3a 2022 (≥ 2.0 pp) | −13.7 % (ledgered) | **−9.4 % (inside ±10 %)** | **met** (+4.3 pp) |
| C3b 2022 | 0.282 (ledgered) | 0.259 | improves, still > 0.20 |
| Declared C1: COAL_BIT 2019 CAVEAT → PASS | −7.82 TWh, vol band 7.64 | −7.47 TWh / −3.0 pp, vol band 7.38 | **not met**: volume improves 0.35 TWh but the band shrinks with a_gen; prints FAIL (would read as the ledgered caveat once attested) |
| Undeclared C1 PASS → FAIL | — | **CC_REGULAR 2021 +8.63 TWh (vol out), CC_REGULAR 2023 +7.57 TWh (vol out)** | **two undeclared flips** |
| Declared C3 regressions | C3a 2019 +8.7 %, 2020 +8.4 % | **+14.3 %, +14.5 % (FAIL)**; C3b 2019 0.171, 2020 0.175 (PASS) | as declared (restack upper bound was +15.9 / +19.1 %) |

C3a moves toward λ in every other year: 2021 −6.7 → −2.5 %, 2023 −0.4 → +3.8 %, 2024 −6.0 → −1.9 %,
2025 −4.7 → −1.3 %. C4 improves in 10 of 14 rows (coal NRMSE 2019 0.203 → 0.173, 2021 0.177 → 0.156).

**Verdict rule (PRECOMMIT §4): T1 met but C3a 2019/2020 out of band and two undeclared C1 PASS → FAIL → the probe does
not beat the keeper on the gates. It goes to the desk as a rule-1/rule-14 structure-vs-gates card. No promotion slot
is requested.**

## 4. What the solve says (rule 14: a worse fit after real data is a bug elsewhere)

Class energy, probe − keeper (TWh):

| Year | biomass | CC_REGULAR | CT_PEAKER | COAL_PRB | COAL_BIT | ST_GAS |
|---|---|---|---|---|---|---|
| 2019 | −8.55 | +2.26 | +2.95 | +2.36 | +0.35 | +0.65 |
| 2020 | −8.47 | +3.50 | +2.77 | +1.54 | +0.15 | +0.54 |
| 2021 | −8.35 | **+5.28** | +1.63 | +0.86 | +0.47 | +0.31 |
| 2022 | −8.08 | +5.17 | +2.15 | +0.02 | +0.37 | +0.61 |
| 2023 | −7.24 | +2.53 | +3.09 | +0.95 | 0.00 | +0.66 |
| 2024 | −7.81 | +3.77 | +2.70 | +0.77 | +0.15 | +0.44 |
| 2025 | −6.97 | +4.04 | +1.62 | +0.75 | +0.25 | +0.37 |

- The restack assumed CC had no headroom; the LP re-timed hydro and gave CC 30–65 % of the restored net load.
  COAL_BIT gains ≤ 0.47 TWh in any year.
- With the phantom 7–9 TWh of mill cogeneration removed, the model serves the load EIA-930 actually metered, and the
  CC over-run against EIA-923 becomes visible in every year (+3.5 to +8.6 TWh), not only in 2019. The keeper's
  injection was masking it.
- The 2019/2020 price premium over λ grows (+8.7 → +14.3 %) at night, where the keeper already sat +4–6 $/MWh
  over λ. Both point at the same object as frontier row SOCO-F1: the model backs coal down and runs CC at night
  where Southern ran coal at minimum load and backed CC down. The holdout removed the input error that was
  partly compensating for that conduct gap.

## 5. Candidate list after this solve

| Candidate | Disposition |
|---|---|
| 1 `mustrun_chp_btm_holdout` | solved; structure-vs-gates card (above); `SOCO.js` cell U → O |
| 2 EIA-930-reconciled partial holdout (inject the telemetered "Other"; ~1 TWh/yr more than candidate 1) | not built: it restores ≤ 1.2 TWh/yr of the 7–9 TWh, so it cannot undo the CC 2021/2023 flips (+5.3 / +2.5 TWh moved) or bring C3a 2019/2020 back inside ±10 %; it would refine the input, not change the card |
| 3 coal commitment state (energy-path posture port), stacked on this probe | phase 0b, `FINDING-closeout-soco-w3-cc-overrun-2026-10-04.md`: upper bound 0.75–1.66 TWh/yr of held coal, cannot clear CC 2021 (+8.63 vs band 7.10) even at full displacement; the dominant gap is Bowen/Gaston loading at $34–47 offers, a price question whose routes are G/R. Not chartered |
| 4 Wansley 2019 floor hole, spot coal, membership union | closed in earlier records; no new evidence |

The queue is exhausted for this lane with reasons. The structural finding (SOCO's must-run residual is 85–90 %
behind-the-meter, and correcting it exposes a CC over-run in every year) is new evidence for SOCO-F1.

## 6. Promotion cost (if the owner rules "promote on structure")

One `promote_keeper.py` run on `closeout_soco_w3_span` (all seven years, nothing to re-solve). The bench parts
`bench/SOCO/<Y>.json.gz` re-render with the holdout (biomass ≈ 0.9–1.6 TWh, a_gen −7 to −9 TWh), as the
lockstep seam requires. The span already carries `hourly/unit_marginal_<Y>.parquet` for all seven years.
Determination: NOT-YET → NOT-YET (failing rows change from {C1 CC 2019} to {C1 CC 2021, CC 2023,
COAL_BIT 2019, C3a 2019, C3a 2020}; C3a 2022 clears its ledgered caveat).

## 7. Bundles

`results/calibration/closeout_soco_w3_<Y>` (seven legs) and `results/calibration/closeout_soco_w3_span` exist in this
container only (gitignored, kept out of the PR by `.git/info/exclude`). The legs are recoverable by full SHA from the
shard branches above until the lane's PR merges and those branches are cut; the registration and the span's slim set
are on `claude/closeout-soco-w3-reg`. **They will not survive the container.** Nothing was deleted (rule 31).
