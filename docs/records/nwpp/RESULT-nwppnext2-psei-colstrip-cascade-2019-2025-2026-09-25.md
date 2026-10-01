# RESULT — NWPP-NEXT-2: PSEI Colstrip / non-balance repair, and hydro cascade coverage 2019–2022

**Runs, both registered:**

| Arm | Run id | Bundle | PRECOMMIT |
|---|---|---|---|
| A — PSEI repair | `2026-09-25-nwppnext2-psei-colstrip` | `results/calibration/nwppnext2_span` | `PRECOMMIT-nwppnext2-psei-colstrip-2019-2025-2026-09-25.md` |
| H — A plus the 2019–2022 cascade | `2026-09-25-nwppnext2h-cascade-2019` | `results/calibration/nwppnext2h_span` | `PRECOMMIT-nwppnext2h-cascade-2019-2022-2026-09-25.md` |

**Keeper compared against:** `2026-09-25-nwpp-next-ferc714-partial`.
**Solved by:** 11 year-isolated shards (rule 36), pinned at `2b8a6bc3` (arm A) and `08293271` (arm H 2019–2022).
The parent session ran no LP.
**Status: PROMOTION QUESTION OPEN (rule 31).** Neither arm was promoted, because one year-level gate regresses; see
§2.

## 1. Determination

Both arms read **NOT-YET on {fuelmix, dispatch_corr}**, the same criteria set as the keeper. C2, C6 and C8 PASS.
Price is UNSCORED (rubric v3.8).

| Year | Keeper → arm A → arm H |
|---|---|
| 2019 | Every row PASS in all three. CC_REGULAR +3.06 → **+0.40** → +0.40 TWh. COAL_BIT −3.22 → −3.97 → −4.25. COAL_PRB +4.85 → +4.46 → +4.74. CT_PEAKER −1.28 → −1.53 → −1.52. Coal r 0.769 → 0.764 → 0.765. |
| 2020 | C1 all PASS: CC_REGULAR +3.47 → **+2.48** → +2.46; CT_PEAKER +1.08 → **+0.78** → +0.80. **C4 coal r 0.720 PASS → 0.691 FAIL → 0.691 FAIL.** Gas r 0.848 → 0.846. |
| 2021 | Rows move by ≤ 0.03 TWh; the energy-neutral 336-hour zonal repair. |
| 2022–2025 | **Identical to the keeper**, row for row. These years are the free drift check from the PRECOMMIT, and it holds. |

**Still failing, unchanged:** C1 CC_REGULAR 2022 −11.23 and 2023 −8.32 TWh (the demand-basis gap, still waiting on
the owner), and C4 coal r in 2023–25.

## 2. The 2020 C4 regression, attributed (zero LP)

The corrected C4 benchmark is PSEI minus its double-booked `NG: COL`: 54.090 → 51.938 TWh. The reconstructed old
benchmark is new + PSEI `NG: COL` on the pool clock.

| 2020 coal hourly r | Old benchmark | Corrected benchmark |
|---|---:|---:|
| Keeper model | **0.720** (the recorded value) | 0.707 |
| Arm A model | 0.701 | **0.691** |

- The benchmark correction alone costs −0.010 to −0.013.
- The model change alone costs −0.016 to −0.019. It removes 2.15 TWh of phantom requirement, 0.63 TWh of it from coal.

Neither part is a defect: both inputs were wrong, and rule 14 keeps the correction whatever the fit does. **But it is
a year-level gate regression**, so the owner's standing instruction ("promote if structure improves with no gate
regressions") is not met, and the promotion is put to the owner.

## 3. What each arm adds structurally

**Arm A (rule 14 / 19, zero DOF):**
- PSEI's double-booked Colstrip share is gone. The LP requirement falls by 4.48 TWh in 2019 and 2.15 TWh in 2020.
- The 2021-08 non-balance hours are filled from FERC 714.
- The pool total and its zonal regroup share one member-demand builder. Before this, the 2020 PSEI zonal share was
  drawn from 17.28 TWh of interpolation.

**Arm H:** arm A plus the hydro cascade binding in 2019–2022.
- 5 plants, 5 links, τ frozen from 2023–24 (rule 23).
- It adds 43,800 water-balance rows per year, which were previously absent.
- The only class move is 2019 COAL_BIT → COAL_PRB, 0.28 TWh.

**Recommendation: arm H.** It is arm A plus a mechanism the keeper already arms, now covering its own years with
measured data. Its scores equal arm A's to within 0.3 TWh.

## 4. Retrievability (rule 34(e))

- The slim bundles (JSON, `hourly/`), the registry sidecars, the run payloads and the bench parts land on `main`
  with this lane's PR.
- The full per-year legs, including `dispatch/`, are gitignored and on local disk.
- Leg SHAs are provenance only (rule 33(d)):
  - arm A 2019 `04da2d42`, 2020 `0fdfcd45`, 2021 `40419b9f`, 2022 `f762ac40`, 2023 `d2eb0a45`, 2024 `88567ab5`,
    2025 `bc378d79`;
  - arm H 2019 `7a4ff713`, 2020 `0531e1f0`, 2021 `9109616e`, 2022 `b771edf3`.
- **A promotion needs no re-solve.** The registered runs are complete as committed.
- **All 11 shards are archived** (rule 33).
- **Leftover shard branches, which the owner must delete** (a session cannot delete refs, rule 33(f)(2)):
  - `claude/nwppnext2-{2019..2025}`
  - `claude/nwppnext2h-{2019..2022}`

## 5. Zero-LP findings from this lane

| Item | Finding | Record |
|---|---|---|
| 2 | Mainstem coupling is not worth an LP. The owner already ruled "no solve" on it (NWPP-50); even a perfect mainstem shape leaves C4 failing. | `FINDING-nwppnext2-mainstem-census-2026-09-25.md` |
| 5 | The CT_PEAKER shortfall is price/merit formation shared with the CC-short / coal-long pattern, plus two standby-status CT plants missing from the fleet. | `FINDING-nwppnext2-ctpeaker-2026-09-25.md` |
| — | Standby census: SB units are excluded from the fleet while the benchmark counts their output. NWPP has 598 MW of gas CT (0.25–1.0 TWh/yr), and the gap is systemic across PJM, SPP and MISO. The recommended next arm is a default-off, status-only admission field. | `FINDING-nwppnext2-standby-census-2026-09-25.md` |
| 4 | PSEI's 1.21× basis is an EIA-930 artifact, not a boundary change. | `FINDING-nwppnext2-psei-basis-2026-09-25.md` |
| 3 | Hydro cascade intake, with the rule-23 decision recorded. | `FINDING-nwppnext2-hydro-cascade-2019-2022-2026-09-25.md` |
