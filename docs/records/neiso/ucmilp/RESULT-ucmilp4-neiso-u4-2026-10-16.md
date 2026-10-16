# RESULT — UC-4-NEISO: arm U4 at engine uc-1.8 on NEISO (solved 2020–2021) — **R: C3a moves away from 0 by 1.65 pp in 2021; no gated flip; CC starts move away from CEMS in both years**

**Lane:** UC-4-NEISO · **Session:** `session_01FoAQpHpMAwKdf4fmMqoZWT` (Opus) · **Date:** 2026-10-16 · **Branch:** `claude/ucmilp-4-neiso`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`).
**PRECOMMIT:** `PRECOMMIT-ucmilp4-neiso-u4-2026-10-15.md` §§1–7 plus Addenda A–D. Addendum D re-pins to uc-1.8 `41cd55dc`. Shards solved at `282150d5`, which is that pin plus docs only.
**Status: FINAL (UC-DESK ruling 2026-10-16 00:28Z).** This was first composed as an interim reading under the desk's 2026-10-15 ruling. The desk then accepted R for NEISO U4: the pre-registered K bars fail in 0 of 2 years whatever the held years show, so the verdict does not depend on the gate ruling. 2019 is infra-held and 2022–25 gate-held. Both stay relaunchable at `41cd55dc` and are not needed for the verdict.
**LP in this session:** zero.
**Registered:** nothing (E13). Scoring used a local sidecar and payload (`2026-10-15-uc-4-neiso-u4`), both removed before this commit. No bench part changed.

## 0. Coverage

| year | state | evidence |
|---|---|---|
| 2019 | **held: repeated infra reclaim** (desk ruling 2026-10-15) | Four solves lost to container restarts, none with an error line (§4) |
| 2020 | **solved** | `claude/ucmilp4-neiso-u4-2020` @ `20b60349d3bb3f1feccdd8576c62d0e7332a6fb8` |
| 2021 | **solved** | `claude/ucmilp4-neiso-u4-2021` @ `1744c4f2f3670d3b79c12d890a959cffd1562d9f` |
| 2022–2025 | **held pending owner gate ruling** | Each year is at 3 of 4 memory attempts; relaunchable at `41cd55dc` (Addenda C–D) |

These verdicts are stated on 2020–2021 only. Kill #3's 2023 bar cannot be exercised.

## 1. Gate table, control → U4 (rubric 3.20, same bench parts)

- **Control:** keeper `2026-10-02-w0-neiso`, re-scored at HEAD. It reproduces the UC-3 record's control column exactly: C3a, T1, T2 and starts.
- **U4:** `results/calibration/ucmilp4_neiso_u4_span`, composed 2020–21 and respanned.

| year | C1 | C2 | C3a | ΔC3a | C3b NRMSE | C3c (> $300 h, model / RT) | C4 gas r / NRMSE | C8 CC_REGULAR forced, scored | unserved MWh | uplift % |
|---|---|---|---|---|---|---|---|---|---|---|
| 2020 | PASS → PASS | PASS → PASS | −1.23 → −0.76 % | +0.47 (toward 0) | 0.111 → 0.114 | PASS → PASS (0 / 0) | 0.961 / 0.117 → 0.964 / 0.111 | 1.7 → 4.3 % PASS | 0 → 0 | 0.24 |
| 2021 | PASS → PASS | PASS → PASS | +2.85 → **+4.50 %** | **+1.65 (away)** | 0.120 → 0.135 (+0.015) | PASS → PASS (0 / 2) | 0.960 / 0.107 → 0.963 / 0.102 | 1.2 → 3.5 % PASS | 0 → 0 | 0.13 |

- **Determination:** control CALIBRATED; U4 NOT-YET, on C6 UNATTESTED only. This is the declared probe artefact.
- **C8:** shown as scored, with MECH 28 included. The MECH 28-removed split was not recomputed in this lane.
- **D-4:** the FAIL set is identical to the control's (2021 `chp_steam` plant 54605).
- **D-1:** not gated, reported only. 2020 COAL_PRB goes FAIL → pass. 2020 COAL_BIT and 2021 COAL_PRB stay FAIL, as in the control. No row is added.

## 2. Readings (PRECOMMIT §5)

Order in every cell: 2020 · 2021.

| # | reading | control | U4 | UC-3 uc-1.5 (X) |
|---|---|---|---|---|
| S2 | CC_REGULAR starts ÷ CEMS (2,190 · 2,474) | 1.187 · 0.998 | **1.278 · 0.928** (further from 1 in both years) | 1.152 · 0.890 |
| S2 | ST_GAS starts (CEMS 80 · 150) | 301 · 764 | 347 · 619 | — |
| S2 | COAL_BIT starts (CEMS 36 · 16) | 24 · 120 | 24 · 118 | — |
| S2 | UC Σ`v` (cluster starts), cc / st_gas | — | 1,461 / 3 · 1,987 / 12 | 881 / 0 · 1,213 / 9 |
| U | uplift ÷ energy cost | — | 0.24 % ($5.57 M) · 0.13 % ($6.29 M) | 0.11 · 0.09 % |
| D | DA increment used: mean / top-100 median MW, QA-dropped h | — | −170.5 / −88.5, 0 · −183.1 / +76.0, 0 (matches phase 0 §2) | n/a (actual) |
| P | load-weighted price $/MWh | 24.83 · 49.13 | 24.95 · 49.92 | 25.06 · 49.85 |
| P | low-load tercile | 20.39 · 39.64 | 21.02 · 41.12 | 21.02 · 40.84 |
| P | high-load tercile | 28.27 · 56.21 | 27.83 · 56.44 | 28.05 · 56.54 |
| T1 | M3 lower-tercile mean error $/MWh | +6.74 · +11.15 | +7.26 · +11.94 (away) | +7.28 · +11.84 |
| T2 | hours ≤ $15, model / actual | 0.020 · 0.006 | 0.000 · 0.006 (falls · flat) | 0.015 · 0.006 |
| T3 | hours < $0, model (actual 29 · 30) | 0 · 1 | 0 · 1 | 0 · 1 |
| X | C3a / C3b | −1.23 / 0.111 · +2.85 / 0.120 | −0.76 / 0.114 · +4.50 / 0.135 | −0.32 / 0.114 · +4.35 / 0.134 |

**What these readings show.**
- **Starts.** U4 nearly doubles the UC's cluster starts against uc-1.5 (Σ`v` cc ×1.6), consistent with per-unit `ut_h` cutting CC min-up from p50 17 h to 14 h. CC plant starts then overshoot CEMS in 2020 and fall further below it in 2021. The UC-3 starts gain is lost in both years.
- **Price.** The price body still rises against the control, in the low tercile by +$0.6 and +$1.5. Against uc-1.5, U4 is within ±$0.3 in every cell.
- **DA demand.** The forecast runs below load off-peak (−170 to −183 MW). That did not lower the trough, which is what §2 expected it to do: T1 and T2 move away from the control in both years.
- **Attribution.** The four mechanisms act jointly. No per-mechanism attribution is claimed (§5 X).
- **Not computed in this lane:** the X rows for integer-plant output and control energy above the arm's P1 ceiling.

## 3. Wall (GATESPEC §6.1)

Both legs ran on the same solver path (lean preset with FIX-9 LP heuristics). Pass-2 reuse did not fire.

| year | P0 s | UC Σ s (mean / p95 MILP s) | P1 s | total s | **total ÷ (P0+P1)** | integer / clusters | nodes p50 / p95 | gap p95 | TL hits | non-opt windows | peak RSS GiB (cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2020 | 76.3 | 4,099.6 (11.16 / 32.20) | 79.2 | 4,297.3 | **27.6** | 19 / 64 | 1 / 51 | 9.99e-4 | 0 | 0 | 5.16 |
| 2021 | 78.2 | 2,993.6 (8.13 / 19.38) | 75.4 | 3,194.7 | **20.8** | 22 / 68 | 1 / 5 | 9.98e-4 | 0 | 0 | 5.49 |

- **Ratio to uc-1.5:** 1.96× in 2020 and 1.05× in 2021 (uc-1.5 ran 14.1× and 19.9×).
- **Windows:** 730 / 730 Optimal.
- **Memory:** the peak is 5.2–5.5 GiB, far below the 22.4 GiB gate (Addendum C).

## 4. Process and infrastructure

- **2019.** Four solves were lost, none with a Traceback, Error, MemoryError or Killed line.

  | run | launched | died | lived | reached |
  |---|---|---|---|---|
  | uc-1.7 | — | ~14:28Z | — | window 254 |
  | uc-1.8 attempt 1 | 21:22:58Z | ~22:31Z | ~68 min | window 325 |
  | uc-1.8 attempt 2 | 22:33:28Z | ~23:48Z | ~75 min | window 361 of ~365 |
  | uc-1.8 attempt 3 | 23:51:54Z | 23:56:40Z–00:19Z | — | window 14 |

  - Per-attempt log mtimes, window counts and last lines: `data/ucmilp4_infra_2019/README.md`.
  - On each relaunch, the fresh boot showed `uptime` "up 0 min" and the swap was gone.
  - Attempts 1 and 2 had a background watcher running and survived about 70–75 min. Attempt 3 had only a 25-min `send_later` and died about 5 min after the shard's turn ended.
  - **Pattern (shard's observation, not adjudicated):** `send_later` alone does not hold a container. A running background task holds it for up to about 70–75 min.
  - A UC year at this wall (≥ 50 min of UC plus P0 and P1) does not fit that window reliably. This is the infra-log evidence the desk asked for.
- **Memory gate.** 2022–2025 stay at 3 of 4 attempts, held pending the owner's ruling (Addendum C). NEISO's actual peak is a quarter of the gate.
- **Bundles (rules 31, 34).** The 2020 and 2021 bundles are pushed in full on their shard branches (SHAs in §0). They were verified with `git ls-tree` and the bytes restored locally before composing. The slim span is committed at `docs/records/neiso/ucmilp/data/ucmilp4_neiso_u4_span/`:
  - root JSONs and `uc_solve_log_<y>`;
  - `hourly/` class, system, storage, `uc_schedule` and `uc_uplift`;
  - `readings_u4.py` / `.json`.

  The composed full span stays local and gitignored. Nothing is deleted.
- **Composition.** A scratch wrapper (`_ucmilp_compose_span.py` plus `gas_price_override` in the per-year set) applies `_hydro5_compose_span._respan_shared_inputs`, as in UC-3 §8 (a)/(b). `legitimacy_diagnostics.json` was regenerated over 2020–21.

## 5. Verdict, matrix, D-6 card

- **Verdict: `R` on 2020–2021** (§4 rule).
  - C3a moves away from 0 by 1.65 pp in 2021.
  - No gated flip. No infeasible window (kill #1 not fired).
  - Kill #2 not exercised: no relaunched leg completed twice.
  - Kill #3's 2023 bar is not exercisable (held).
  - C3b moves by +0.003 and +0.015, under the 0.02 bar.
  - The K-candidate bars fail independently: CC starts are closer to CEMS in 0 of 2 years, and T2 rises in 0 of 2.
- **Matrix:** NEISO `uc_commitment_demand_source` moves U → **R (2020–21 solved, joint U4 arm; desk-accepted)**. NEISO `unit_commitment_milp` stays R (UC-3).
- **D-6 card (copy-paste):**

  > "UC-4 NEISO, arm U4 (UC + DA-forecast commitment demand + per-unit ut_h/mlf + reserve u-gate) at uc-1.8 — R on 2020–21 (2019 held: repeated container reclaim; 2022–25 held pending the memory-gate ruling). 730/730 windows Optimal, 0 TL, 0 MWh unserved, make-whole 0.13–0.24 %, wall 21–28× P0+P1, peak 5.5 GiB. No gated flip; C3a +2.85 → +4.50 % in 2021 (+1.65 pp away; R), 2020 −1.23 → −0.76 %. U4 ≈ UC-3 uc-1.5 on price (±$0.3/MWh) but loses the starts gain: CC starts/CEMS 1.187 → 1.278 and 0.998 → 0.928, further from 1 in both years; T1/T2 move away. The DA forecast's off-peak under-forecast did not lower the trough. Options: (1) record R and stop U4 for NEISO [recommended: on 2020–21 U4 does not change the UC-3 picture]; (2) finish 2019/2022–25 after the gate ruling for a full-span record (≈ 1 h of UC per year; needs a container that survives > 75 min)."
