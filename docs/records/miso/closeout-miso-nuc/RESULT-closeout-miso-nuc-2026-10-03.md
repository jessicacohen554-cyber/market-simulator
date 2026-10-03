# RESULT closeout-miso-nuc — MISO nuclear 2019–2022 at measured data, seven-year re-solve (R-43)

Lane `claude/closeout-miso-nuc-b`, 2026-10-03.

**Authority.** Owner ruling **R-43**, `docs/backcast-closeout-plan-2026-10.md` §5.0, "Full repair + 7 MISO shards".

**Run.** `2026-10-03-closeout-miso-nuc-r`, bundle `results/calibration/closeout_miso_nuc_span`, years 2019–2025.
- It is registered as a **probe** (rule 15) and has not been promoted.
- The PRECOMMIT and G-DRIFT were written before any LP and live in this folder.

**Bottom line.** All five structural kills pass, so the PRECOMMIT's decision rule is to **recommend promotion**. The fit gets worse in two places, both predicted by the zero-LP sizing:
- C1 CC_REGULAR 2021 goes PASS → FAIL.
- C3a 2020 goes PASS → FAIL.

Under R-43 and rule 14, these worse readings become MISO's baseline.

## 1. What was solved

**Data repair.** Merged on `main` as PR #7129, merge `f98c456401918eba82c338676e303a90004bb94c`; this is the pin.
- `NUCLEAR_MONTHLY_CF_BY_YEAR["MISO"]` gains 2019–2022 rows. They come from the frozen derive.
- The NRC daily extract `data/raw/nuclear-availability-MISO.csv` is re-derived over 2019–2025:
  - Duane Arnold (through 2020) and Palisades (through 2022) are uncovered pass-through rows.
  - The River Bend 2019 NRC rename is aliased.
  - Every 2023–25 row is byte-identical.
- SolveEpoch `2026-10-03d` (backcast MISO).

**Recipe.** The keeper `2026-10-02-w0-miso-fix2` (`w0_miso_span`) is replayed with no `--set`, one year per shard (rule 36), all seven at the pin.

**Recipe diff (K4).** Per year, the composer's field-by-field check and the parent's own diff agree. The only differences from the keeper's `run_config_<Y>.json` are two fields registered after the keeper solved:
- `spp_mmu_offer_repair`
- `nwpp_seam_measured_limits`

Both are recorded at their default `False` where the keeper has them absent. No recorded value differs.

### Shards

Each leg was verified before it was archived:
- 17 files;
- `dispatch/<Y>_P1.parquet` and `hourly/unit_marginal_<Y>.parquet` present;
- bytes held locally;
- only its own bundle path plus `.gitignore` changed against the pin.

| Year | Shard branch @ commit (transport, rule 33) | Dispatch (zstd-9 re-encode) | Unserved |
|---|---|---|---|
| 2019 | `claude/closeout-miso-nuc-2019` @ `49a12811f920fad8fe8032390c299dab6f901084` | 65,994,089 B · 31,334,520 rows | 0 |
| 2020 | `claude/closeout-miso-nuc-2020` @ `3f6f250edeeca38fca0d541bf34bb53d64b70a6f` | 97,951,885 B (SNAPPY, under the limit) | 0 |
| 2021 | `claude/closeout-miso-nuc-2021` @ `ae3ae1a4dc072c0b10bbea7fd4a115ae1254af37` | 75,006,436 B · 30,957,840 rows | 0 |
| 2022 | `claude/closeout-miso-nuc-2022` @ `e8d0b133f50ac09579d2e870d8b17ffaf4704c25` | 70,179,433 B · 30,817,680 rows | 0 |
| 2023 | `claude/closeout-miso-nuc-2023` @ `b373485b48d5e63206a0673366c0b0f3a5b96a07` | 65,621,860 B · 30,362,160 rows | 0 |
| 2024 | `claude/closeout-miso-nuc-2024` @ `c27b5ffbb0ab4e690383d0f57e8e49cfb962a8e5` | 74,180,449 B · 30,125,640 rows | 8,356.9 MWh (= keeper) |
| 2025 | `claude/closeout-miso-nuc-2025` @ `f60532f3f9c1a543fd5c5fcacc83708995cf3d0a` | 57,588,266 B · 29,932,920 rows | 0 |

### Transport

A MISO SNAPPY `dispatch/<Y>_P1.parquet` comes out at 101–107 MB. GitHub's GH001 pre-receive limit refused the 2019, 2021, 2023 and 2024 pushes.

The desk approved a transport-only step, **option A**:
- Re-encode only that file with pyarrow zstd level 9.
- Assert `Table.equals` and schema-with-metadata equality against the SNAPPY original.
- Keep the original on the shard's disk.

So the committed dispatch legs for 2019 and 2021–2025 are **zstd-9 re-encodings of the SNAPPY originals, with byte-equal tables**. The codec is not a solve input, and rule 34 is satisfied.

How the legs got there:
- **2024** applied the step after a soft reset of its never-pushed commit.
- **2019, 2021 and 2023** were re-solved in fresh shards that encode before their first commit. A classifier refused `git reset --soft` in the first 2023 shard, so that route was not used again.
- **2025 and 2022** encoded before their first commit.

**Desk item, not for this lane:** the PJM/MISO dispatch writer should emit zstd. SNAPPY at 98–107 MB sits on the GH001 limit.

### Compose

`scripts/probes/_w0_compose_span.py --pinned-sha f98c4564…` composed the seven legs into `closeout_miso_nuc_span`.
- The recipe check passes.
- There is one SHA and one solve surface.
- `legitimacy_diagnostics.json` was regenerated over the composite.

## 2. The repair does what it claims

Model nuclear against EIA-923, plant-matched (FINDING §2), in TWh:

| Year | Keeper | This run | EIA-923 | Miss: keeper → now |
|---|---|---|---|---|
| 2019 | 97.58 | 102.62 | 102.26 | −4.6 % → **+0.3 %** |
| 2020 | 97.57 | 95.18 | 95.11 | +2.6 % → **+0.1 %** |
| 2021 | 93.61 | 96.48 | 95.69 | −2.2 % → **+0.8 %** |
| 2022 | 89.94 | 91.69 | 91.35 | −1.5 % → **+0.4 %** |

Two reactors confirm the daily overlay is applied:
- Duane Arnold's September 2020 capacity is 0 MW. The keeper had 542.5 MW; NRC shows the plant dark after the 2020-08-10 derecho.
- Palisades' 2021 hourly capacity has correlation **1.00** with the NRC daily series. The keeper's was −0.12.

**The desk's 2021 "0 reactor(s)" log line.** The 2021 shard logged "nuclear unit-availability overlay (2021): 0 reactor(s)". That line is not the solve's overlay:
- The extract carries 1,561 rows for 2021: 13 reactors × 92 days, plus Palisades × 365.
- At the pin the loader returns 14 keys, and every key matches a fleet `unit_id`.
- The 2021 leg's `unit_marginal` shows the overlay applied (Palisades r = 1.00).

The line comes from a different call in that log. Separately, the monthly table rows set every uncovered date.

**Known limit (not a defect of this repair).** The frozen WEDGE_TOL / SCALE_CLIP drop most 2019–22 months from the daily extract:
- daily timing survives in 1 / 3 / 3 / 4 months of 2019–22;
- the same mechanism keeps 4 / 6 / 7 months in 2023–25.

In the dropped months the fleet-level anchor row stands. Example: Callaway still runs in January 2021 although EIA-923 shows it offline January–July. That miss is a per-unit timing error under a correct fleet total.

**Where the nuclear change went** (class Δ TWh, from the hourly class sidecars):

| Year | ΔNuc | ΔCC_REG | ΔPRB | ΔBIT | Δimport | ΔCC_CHP | ΔST_GAS |
|---|---|---|---|---|---|---|---|
| 2019 | +5.03 | −1.57 | −1.14 | −0.72 | −0.76 | −0.48 | −0.13 |
| 2020 | −2.39 | +0.86 | +0.47 | +0.22 | +0.39 | +0.05 | +0.20 |
| 2021 | +2.87 | −1.32 | −0.60 | −0.34 | −0.26 | −0.12 | −0.09 |
| 2022 | +1.75 | −0.95 | −0.04 | −0.02 | −0.46 | −0.18 | +0.01 |

All cells are class totals from the hourly sidecars, keeper → this run.

## 3. Full per-year criterion table against the keeper

Scored with `calibration_verdict.py`. The keeper is attested; this probe is not. Promotion writes the attestation and carries the keeper's exceptions ledger forward (rule 35). So the governance row and the C3c "CAVEAT→FAIL" rows below are an artefact of the missing attestation: every C3c magnitude is unchanged.

**PASS → FAIL flips caused by the data, at full magnitude:**

| Row | Keeper | This run | Band | Pre-fixed reading |
|---|---|---|---|---|
| **C1 CC_REGULAR 2021** | −6.83 TWh, share −0.7 pp — PASS | **−8.15 TWh, share −0.9 pp — FAIL** | ±8.00 TWh | −8.5 / −8.9, FAIL |
| **C3a 2020** | +9.6 % — PASS | **+10.2 % — FAIL** | ≤ ±10 % | +8.9 … +10.2 %, at the ceiling |

**Failing rows that were already FAIL:**

| Row | Keeper | This run | Pre-fixed |
|---|---|---|---|
| C1 ST_GAS 2019 | −8.60 TWh | **−8.71 TWh** (further out by 0.11) | ≈ −9.10 / −9.16 |
| C3b 2021 NRMSE | 0.213 | **0.219** | ≈ 0.221 |

**Other C1 rows, 2019–2022.** All are still PASS. Changes greater than 0.3 TWh, keeper → this run, in TWh:

| Year | Changes |
|---|---|
| 2019 | CC_REGULAR +4.66 → +3.17; COAL_PRB +5.70 → +4.56; COAL_BIT −2.07 → −2.79; CC_CHP −4.77 → −5.25 |
| 2020 | CC_REGULAR −2.03 → −1.24; COAL_PRB +3.40 → +3.87 |
| 2021 | COAL_PRB +5.63 → +5.03; COAL_BIT −0.92 → −1.26 |
| 2022 | CC_REGULAR −4.55 → −5.48 |

No COAL_PRB 2022 flip: +5.76 → +5.72. The FINDING's B/cheapest bracket (+8.11) did not materialise.

**C2 sysvol:** PASS in every year. The 2021 gas family now carries a C1 flag on CC_REGULAR.

**C3a, the other years:** all PASS.
- 2019: +7.2 → +6.2 %.
- 2021: −7.8 → −8.4 %.
- 2022: −6.8 → −6.9 %.
- 2023–25: unchanged.

**C3b, the other years:** all PASS.
- 2019: 0.102 → 0.091.
- 2020: 0.149 → 0.147.
- 2022: 0.131 → 0.127.

**C3c:** magnitudes unchanged in every year (model 0 / 0 / 0 / 0 / 7 / 9 h vs RT actual 17 / 48 / 116 / 30 / 37 / 88 h). The keeper's ledgered caveat carries at promotion.

**C4 dispatch_corr:** PASS in every year. The largest move is 2021 gas, r 0.839 → 0.824.

**C8 forced share:** PASS in every year. Moves are ≤ 1.3 pp, all GROUNDED where above cap.

**Determination.** The keeper reads NOT-YET (C1, C3b). After promotion this run reads **NOT-YET**:
- C1: ST_GAS 2019 and CC_REGULAR 2021;
- C3a 2020;
- C3b 2021.

That is one load-bearing year-row worse on C1 and one on C3a, both as predicted.

## 4. Structural kills (PRECOMMIT §4)

| Kill | Condition | Result |
|---|---|---|
| K1 | Any new unserved energy versus the keeper | **PASS.** 0 MWh in every year except 2024's 8,356.9 MWh, which is identical to the keeper's 2024 leg. The PRECOMMIT's "keeper 0 MWh" wording was wrong for 2024; the kill is against the keeper. |
| K2 | C6 governance | **PASS at promotion.** UNATTESTED is the pre-promotion state (SOCO precedent); `promote_keeper.py` attests. |
| K3 | C8 forced share | **PASS** |
| K4 | Recipe diff is anything other than the data repair | **PASS** (§1) |
| K5 | E-INERT for 2023–25 | **PASS.** The `system`, `class_hourly` and `unit_marginal` sidecars are `DataFrame.equals` the keeper's in 2023, 2024 and 2025. |

On K5, one diagnostic note. The regenerated `legitimacy_diagnostics.json` reads the 2023–25 CT_PEAKER D-1 profile slightly differently: r 0.975 → 0.972 and CV ratio 1.782 → 1.933 in 2023. Forced shares are identical. The cause is the legitimacy script at the pin regenerating over identical hourly data, not the solve.

## 5. Recommendation and promotion cost

**Recommendation.** By the ex-ante decision rule: **promote**.
- The kills pass.
- The repair moves nuclear to within ±0.8 % of EIA-923 in every repaired year.
- The fit-negative readings (C1 CC_REGULAR 2021, C3a 2020, ST_GAS 2019 −8.71, C3b 2021 0.219) become MISO's baseline (R-43, rule 14).

**Where the bundle is.**
- The slim composed bundle `results/calibration/closeout_miso_nuc_span` is committed on this lane branch with the registry sidecar and run payload. It holds the hourly sidecars, including `unit_marginal` for every year, the run configs, meta and diagnostics.
- The full `dispatch/<Y>_P1.parquet` legs live on the seven shard commits above. Those are transport only and are cut when this lane's PR merges.

**What a promotion costs.** `promote_keeper.py` would:
- attest, carrying forward the `2026-10-02-w0-miso-fix2` exceptions ledger, with the C3c entries re-measured;
- designate, fold and re-key;
- prune the outgoing `w0_miso_span` stores (MISO only).

Promotion slot: requested from the desk. Promotions are serialised, and nothing has been run here.
