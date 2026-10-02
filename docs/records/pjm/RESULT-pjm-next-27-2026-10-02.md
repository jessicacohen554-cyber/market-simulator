# RESULT: PJM-NEXT-27. Coal rows plus per-year `online_frac`, solved at W0: the fractions are dispatch-inert, and S2/S3 fail again

**Keeper unchanged:** `2026-10-02-w0-pjm-fix2` (`w0_pjm_span`). Determination NOT-YET.

**Readings:** `PRECOMMIT-pjm-next-27-2026-10-02.md` §5, fixed before any number existed. Control: `w0_pjm_span`, every
year (§4).

## 1. What ran

- **Arm:** one data delta on main `0663760b`, at `91cd12ceb08e0728c1f64bb3826c1088e2cdf682`.
  - The PJM-NEXT-25 `thermal_tranches_PJM.csv` append (sha256 `31455aaa…`).
  - 60 per-year `online_frac` rows for the 18 appended plants. sha256 `b87a4ac2…`; pooling them reproduces each
    pooled row exactly (18 of 18).
- **Recipe:** `pjmnext16_A_span` plus the ten W0 `--set` fields.
- **G-DRIFT `0663760b → 0d5f3e32`** (the W0 keeper merge, which landed after launch): the only solve-path hunk is
  `neighbor_price.forward_heat_rate`. It applies to SOCO seams and untabulated (forecast) years only, so it is
  **INERT** for a PJM backcast.
- **Wave 1 failed and was relaunched.** Seven shards on full clones:
  - 2020 and 2023 were OOM-killed. The disk was already full, so the runner could add only 3 GiB of swap
    (13.4 + 3 = 16.4 GiB, against 24).
  - 2024 hit a dirty checkout.
  - Three shards never got a container, and one was archived before it started.
  - Nothing was pushed; all were archived.
- **Wave 2:**
  - Each shard ran on a blob-limited clone, with `prepare_solve_container.py --target-gb 24` run **before** any
    data step and a hard stop below 23.5 GiB.
  - All seven passed and pushed their full bundle (17 files, including `dispatch/<Y>_P1.parquet` and
    `hourly/unit_marginal_<Y>.parquet`, each parented on `91cd12ce`).
  - Every bundle was fetched and checked (`ls-tree` count, bytes in hand), and every shard archived.

  | Year | Leg commit (`claude/pjm-next-27-<Y>`, transport) |
  |---|---|
  | 2019 | `42dd7f2b09418ae4c5af440a6242b894a3289780` |
  | 2020 | `06888c7df7f1daff4aefc6daa4766cfb2ba16c51` |
  | 2021 | `7e7166e0497607dea298e4bdd444e5530f64e1f3` |
  | 2022 | `4c24e7824474508d2ed726802a34d308dcc06c02` |
  | 2023 | `9a2b87ce9629ce9038a6cc4dc60c5512a7850983` |
  | 2024 | `cacc6c52c8d87db55e189fbd11ca04d1648b60af` |
  | 2025 | `bfe745f22d6dc48e0d3d4dfb85c690215d7a0a60` |

- **Composed** with `_pjmnext26_compose_span.py`. The recipe check passes. The result is
  `results/calibration/pjm_next_27_span`, local only.
- **Scoring:** the span was registered as a local probe for scoring only, then un-registered. Nothing under
  `frontend/` is committed.

## 2. Readings vs the W0 control

Read with `scripts/probes/_pjmnext27_readings.py` → `results/phase0/pjm/_pjmnext27_readings.json`, plus the composed
`legitimacy_diagnostics.json` and `calibration_verdict.determine`.

| id | reading | result | verdict |
|---|---|---|---|
| S1 | slack + dump ≤ control + 0.01 TWh | equal to the control in every year (0.0002 / 0 / 0 / 0 / 0 / 0.0015 / 0.0011) | **holds** |
| S2 | appended-cohort within-plant gap smaller than the control's in ≥ 2 of 2019–21 | 2019 0.977 vs 0.409 (wider); 2020 0.415 vs 0.542 (narrower); 2021 0.417 vs 0.341 (wider) | **falsified** (1 of 3) |
| S3 | D-2 coal ≤ 30 %; no new coal D-4 conduct failure, 883 / 3149 named | D-2 coal max 12.4 % (COAL_PRB 2020). **New D-4 coal unit-conduct failures:** Waukegan 883 in 2019 (0.091 TWh floored, 54.5 % of its binding hours at zero output), 2020 (0.076; 52.7 %) and 2022 (0.041; 72.9 %); Montour 3149 in 2019 (0.001; 90.8 %). The control has none at either plant. | **falsified** |
| S4 | 2023–25 training-tier C1/C3 unchanged | no criterion flips in any year; model values equal or within rounding (the `price_tail` CAVEAT→FAIL rows are the unattested probe's ledger, not the model) | **holds** |
| P1 | COAL_BIT 2019 and 2021 up 1–6 TWh | +2.44 / +1.04 TWh | as predicted |
| P2 | no failing cell outside COAL_BIT / CC 2019–22 flips to PASS | none | informational |
| F1 | against the NEXT-26 legs, 883 / 3149 off-window falls in 2020 | see §3: the dispatch is the NEXT-26 dispatch | not met |

**Decision rule** (PRECOMMIT §5): S1–S4 do not all hold, so the arm is **not recommended.** The prior stated before
the solve was that S3 would most likely fail again in 2019. It did, and it also fails in 2020 and 2022.

## 3. The finding: the per-year fractions do not change dispatch

Against the PJM-NEXT-26 legs (W0 plus the rows only), the candidate is the same solve outcome:

- **Prices:** in the years compared hour by hour (2020, 2021, 2023) the system price differs by at most 2e-8 $/MWh; slack and dump are identical, and COAL_BIT and
  the appended cohort's TWh match to 0.01 TWh in every year.
- **Floors:** the candidate does carry the new floors. At the 18 plants they are 5.70 / 5.23 / 0.52 TWh in
  2020 / 2021 / 2023, exactly the phase-0 `rows_frac` build, and > 99 % of floored unit-hours sit at their floor.
- **Per-unit MW:** only degenerate reshuffles, up to 85–143 MW within a plant, at identical cost.

**What this means.** The window resizes a floored tranche inside hours the plant runs above its floor anyway. The
coal over-run here is economic (offer-tranche structure), not floor-forced. So the rule-14 repair is real data but
inert for dispatch, and it cannot clear S2. It does not clear S3 either:

- At 883 / 3149 the per-year fraction is close to pooled in 2019 (0.437 vs 0.462; 0.236 vs 0.225).
- In 2022 the plant has no own-year row: Waukegan's 2022 coal capacity is outside the coverage construction's vintage
  fleet, so the pooled 0.462 stands.
- The conduct failure is a **placement** defect. The window takes the top load-ranked hours; the meter is dark in
  over half of them.
- This is the same class pjm-h15 routed to the day-grain successor (`mechanism-matrix/PJM.js`
  `coal_sync_online_frac_per_year` evidence: "window-PLACEMENT defects").

**Rows vs fractions.** Both S2 and S3 failures belong to the NEXT-25 rows: the measured tranche structure gives
the cohort more economic coal, and a floor whose window the meter contradicts. The fractions neither cause nor cure
either.

## 4. Next lever (for the owner card)

Whole-day placement is not the fix. `coal_sync_window_commitment_grain` (pjm-h16) is already K and armed in this
recipe, so these failures occur under day-grain placement. The open structural question is whether the 18 appended
rows should carry a must-run floor where the plant's own meter contradicts it.

- **Option A: hold, and move to closeout wave 1.** Keep the W0 keeper. Run the L2 incremental-HR and R-13
  anchor-vintage PRECOMMITs, which were waiting on the W0 keeper that has now landed. The coal rows stay at the arm
  commit.
- **Option B: conduct-gated must-run membership** for the appended rows. A plant carries the coal sync floor only if
  its own CEMS conduct supports it. That needs a new, zero-DOF, measured admission test, and it would have to clear
  rule 19 against `coal_mustrun_requires_measured_row`.
- **Option C: rows without must-run.** Admit the measured tranche structure but zero the appended plants' sync
  floors. This is a structural choice for the owner. S2 (the cohort's within-plant over-loading) would still be open.

## 5. Bundles and promotion cost

- **Local only:** `results/calibration/pjm_next_27_span` (composed) and the seven legs. The leg commits above are
  transport (rule 33) and go when this PR merges.
- **Nothing from this solve is on `main`**, apart from the derive script, the data artifacts (withdrawn per the
  decision, see the PR), the probes and the records.
- **If the owner promoted anyway:** re-compose from the leg commits, attest, and run `scripts/promote_keeper.py`.
  That needs the gitignored DataMiner2 virtual-bid parquets for preflight 0d.

## 6. Owner ruling

**2026-10-02, PJM-NEXT-27 card: "Hold; closeout wave 1."** Option A. The coal-rows arm is dropped: the W0 keeper
`2026-10-02-w0-pjm-fix2` stays, the 18 appended rows and their per-year `online_frac` stay at arm commit `d3e04d9f`
and are not re-tested without new evidence. The next PJM step is closeout wave 1 (L2 incremental HR, R-13
anchor-vintage), owned by the closeout lane; PJM-NEXT-28 does not duplicate it.
