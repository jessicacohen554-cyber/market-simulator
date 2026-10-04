# RESULT — UC-2-SPP: MILP unit-commitment A/B on every SPP backcast year — **STOPPED, kill #1 (infeasible UC window) at the ruled pin**

**Lane:** UC-2-SPP · **Session:** `session_01QBeFQCYTmVafRpi7Ujb9gs` (Fable) · **Date:** 2026-10-04 · **Branch:** `claude/ucmilp-2-spp-ab-r7qd`
off `origin/main` `d62ae1a7`. **PRECOMMIT:** `PRECOMMIT-ucmilp-spp-ab-2026-10-04.md` (pushed `719ceac5` before any shard; Addenda A/B before each relaunch).
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner: *"I want tests on backcast years to see if it improves calibration."*
**LP in this session:** zero. Fourteen shards launched, zero bundles produced.

## 0. Headline

**No calibration reading exists. The arm could not be solved at either pin.** The protocol's kill #1 (GATESPEC §5; PRECOMMIT §6.1,
*an infeasible window is an engine defect, not a tuning invitation*) fired in **all seven SPP years** at the desk-ruled pin
`c8690022`. The lane recorded it and stopped: no `uc_*` value was moved, no second arm was tried, no control solve was run.
**This is not an `R` verdict** — an engine defect says nothing about the mechanism's calibration effect — and it is not `I` or `K`.
The `unit_commitment_milp` cell for SPP stays `U` until an A/B solves. The D-6 card reads **hold**.

### 0.1 The GATESPEC §6.3 gate table (control vs arm, every registered year)

| year | C1 | C2 | C3a | C3b | C3c | C4 | C6 | C8 | D-2 MECH 28 share | wall ratio | reading met? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | control PASS / arm — | PASS / — | +12.3 % FAIL / — | 0.160 PASS / — | CAVEAT / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |
| 2020 | PASS / — | PASS / — | +27.7 % FAIL / — | 0.345 FAIL / — | CAVEAT / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |
| 2021 | CC −8.92, PRB +10.98 FAIL / — | PASS / — | +7.1 % PASS / — | 0.176 PASS / — | CAVEAT / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |
| 2022 | CC −9.16, PRB +10.75 FAIL / — | PASS / — | −4.8 % PASS / — | 0.175 PASS / — | CAVEAT / — | gas 0.313 FAIL / — | PASS / — | PASS (ST_GAS 33.8 % grounded) / — | — | — | **no arm** |
| 2023 | PASS / — | PASS / — | −6.4 % PASS / — | 0.176 PASS / — | FAIL / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |
| 2024 | PASS / — | PASS / — | −11.2 % FAIL / — | 0.216 FAIL / — | FAIL / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |
| 2025 | PASS / — | PASS / — | −4.3 % PASS / — | 0.153 PASS / — | FAIL / — | PASS / — | PASS / — | PASS / — | — | — | **no arm** |

Control = keeper `2026-10-03-closeout-spp-nuc-keeper` (`results/calibration/closeout_spp_nuc_span`, rubric 3.18 as registered;
re-scored identically at rubric 3.20 by `calibration_verdict.py` on the committed bundle, zero LP, in this session).
Arm column empty by construction: no P1 ran.

### 0.2 The GATESPEC §6.1 wall rows

| ISO-year | baseline P0+P1 s | P0 s | UC Σ s | P1 s | total s | ratio | integers/window | nodes p50/p95 | gap p95 | time-limit hits | peak RSS GB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| SPP 2019 | — | 89.8 (cold, 76,475 it.) | stopped in window ≈0 | — | — | — | 94 clusters × 36 h | — | — | — | not logged |
| SPP 2020 | — | (P0 solved) | stopped | — | — | — | 92 × 36 | — | — | — | — |
| SPP 2021 | — | (P0 solved, obj 995.6 B) | stopped | — | — | — | 88 × 36 | — | — | — | — |
| SPP 2022 | — | (P0 solved) | stopped | — | — | — | (not reported) | — | — | — | — |
| SPP 2023 | — | 82.9 | stopped | — | — | — | 86 × 36 | — | — | — | — |
| SPP 2024 | — | 79.1 (75,214 it.) | stopped | — | — | — | 83 × 36 | — | — | — | — |
| SPP 2025 | — | (P0 solved) | stopped | — | — | — | (not reported) | — | — | — | — |

What the shards did measure: P0 cold solves of 79–232 s per SPP year on the standard solve container (13.36 GiB ceiling + 10 GiB
swap; `MARKET_SIM_HIGHS_THREADS=1`); UC stage census 218–226 plant clusters, 83–94 integer, 384–401 fleet rows; window size
55,656–57,384 columns × 14,940–17,100 rows (24 + 12 h). Shard wall end to end (clone, hydrate, regenerate, P0, UC stop) 3.4–8.3 min.

## 1. What happened, in order (both pins; every shard report read in full)

| # | time (Z) | event |
|---|---|---|
| 1 | 21:29 | seven shards at `6d47c762` (engine branch tip at charter). **All seven crashed** in the UC stage at the first month-end checkpoint: `pipeline/uc.py:363` `AttributeError: 'UcStage' object has no attribute 'artifact_dir'` (`__init__` sets `checkpoint_dir`; nothing sets `artifact_dir`). January's windows had solved. Pushed nothing. PRECOMMIT Addendum A; routed to UC-1-FINISH and UC-DESK. |
| 2 | 22:06–22:10 | UC-1-FINISH fixed it (one token, `self.checkpoint_dir`), added a gate-on two-month-end regression test, gitignored `results/uc-checkpoints/`, rebased onto main `d62ae1a7`; UC-DESK ruled the relaunch pin **`c8690022bf5024d5fee469abc2663b1c61a3ee49`** and accepted this lane's zero-LP G-DRIFT of the rebase (INERT for SPP; `solve_surface --diff` NO VALUE MOVED). PRECOMMIT Addendum B. |
| 3 | 22:15 | seven shards relaunched at `c8690022`. P0 solved in every year. **All seven raised** `market_sim.model.uc.window.UcWindowInfeasible: UC window solve ended Infeasible with no feasible incumbent (…)` from `model/uc/solve.py:81` via `pipeline/uc.py:335` ← `uc.py:250 (p1_fleet_prep)` ← `pipeline/solve.py:754`. No per-window progress line precedes the raise and the exception carries no window index; the column count (55,728 ÷ 36 = 1,548 per hour) is a full 24 + 12 h window, so it is very likely **window 0**. Pushed nothing. |
| 4 | 22:40 | **kill #1 recorded; lane STOPPED.** Routed to UC-1-FINISH (facts + three diagnostic asks: window index in the exception; an LP-relaxed re-solve on Infeasible to separate row infeasibility from integrality; a `writeModel` dump of the failing window) and to UC-DESK (hold vs close). |

Per-shard facts at `c8690022` (sessions in §5): 2019 `session_016Q25kM55oR9F4vqg6wf4wZ` 57,384 cols / 17,100 rows / 94 int (226 clusters,
401 rows); 2020 `…01MHWSyP87HaQpJXFJtiSu76` 57,384 / 16,740 / 92; 2021 `…01MeWGRZv3JxeZJDc1Upcunw` 56,628 / 16,020 / 88;
2022 `…01CNV2FaVSEWeYvziuEN8JDr` (infeasible; counts not reported); 2023 `…01WNTjYengbMZns2cWSX3BaW` 55,692 / 15,660 (218 clusters, 86 int);
2024 `…0134eBEMbmBA5XWBnvv275zV` 55,728 / 15,120 / 83 (221 clusters, 384 rows); 2025 `…01GXNpmb2dkx3h2Kd6TXkscx` 55,656 / 14,940.
Also logged before the UC stage in every year: `mustrun_commitment_feasibility_clip` released commitment floor on P0 (2024: 75.0 GWh + 6.9 GWh,
86,640 infeasible plant-hours; 2023: 93,768; 2022: 106,632; 2021: 120,432 plant-hours) — the keeper arms `coal_mustrun_per_plant` and
`st_gas_mustrun_per_plant`, kept per owner ruling R5 (D-5). Whether the floor-driven `u` lower bound (`units_needed_for_floor`,
`model/uc/window.py:512–515`) collides with the `ΣP − mlf·p̄·a·u ≥ 0` / `P ≤ p̄·a·u` coupling rows or the window-0 state carry is the
engine lane's diagnosis, not this lane's; it is named here only as the first place to look.

## 2. The pre-fixed readings, answered

| reading | answer |
|---|---|
| T1 2020 C3a ≤ +18.85 % · T2 2019 C3a ≤ +11.15 % · T3 2020 C3b ≤ 0.2725 | **unanswerable** — no arm P1 |
| T4 low-price-hour ratios · T5 M4 dormancy | **unanswerable** |
| 2024 expected cost (C3a model-low) | **unanswerable** |
| control readings (no PASS → FAIL flip) | **not exercised** — no arm; the control re-score at HEAD rubric 3.20 reproduces the keeper's record exactly (0 records differ) |
| S1 MECH 28 share · S2 starts vs CEMS · S3 online capacity · S4 integer set | S4 only: 218–226 clusters, 83–94 integer per year (UC-0 M6 predicted 86 integer clusters, 38.2 GW — consistent); S1–S3 unanswerable (S3's comparator is not on disk regardless, PRECOMMIT §4) |
| W1 wall rows · W2 time-limit hits · W3 uplift share | partial (§0.2): P0 79–232 s; no UC Σ, P1 or ratio |
| **W4 infeasible windows = 0** | **VIOLATED in 7/7 years → kill #1** |
| kill #2 non-determinism | not exercised (no completed pair) |
| kill #3 control flip | not exercised |

## 3. Verdict and the D-6 card

- **Verdict (PRECOMMIT §7): none of K / R / I can be minted.** `R` requires a wrong-sign move or a kill *on evidence about the mechanism*;
  an infeasible window is an engine defect (GATESPEC §5 wording) and carries no information about the UC's calibration effect. The
  SPP `unit_commitment_milp` cell stays **`U`**; this RESULT is its evidence citation that the cell was attempted at two pins and the
  engine could not produce an arm.
- **D-6 card text (copy-paste):** *"UC-2 SPP A/B — HOLD. The MILP UC stage could not solve any SPP year at the engine SHAs 6d47c762
  (checkpoint AttributeError, fixed) or c8690022 (every year: a UC window infeasible with no incumbent, likely window 0). No reading
  exists. Options: (1) hold the lane for a diagnosed engine fix and relaunch under the PRECOMMIT's Addendum A rule (same recipe,
  same readings); (2) close the lane; the cell stays U."*
- **Not a matrix re-test; nothing to stamp.** `spp_commitment_posture` (R), the bridges (R) and the DO-NOT-REDO list were not touched.

## 4. Bundles, cost, and what survives

- **Bundles:** none. Fourteen shards wrote no `dispatch/`, no UC sidecar, pushed no branch (`git ls-remote 'refs/heads/claude/ucmilp-spp-*'`
  is empty). Nothing to retain, nothing to prune (rule 31 satisfied trivially). The control keeper is untouched on `main`.
- **Cost of the attempt:** 14 shard containers × 3–8 min; zero LP in the parent.
- **Cost of the next attempt, once the engine solves a window:** seven year-isolated shards; the per-shard budget stays 120 min
  (PRECOMMIT §5); the prompts regenerate from `scripts/shard_prompt.py` with the new pin; the PRECOMMIT's readings do not move.
- **Promotion question:** moot — there is no candidate. Nothing is proposed for promotion.
- **Shards left alive:** none; all fourteen archived (rule 33, nothing to fetch). No shard branch exists for the owner to delete.

## 5. Provenance

- PRECOMMIT `719ceac5` (blob `c20748f0`) → Addendum A `6dcad5b3` → Addendum B `c72748dc` (blob `74c9866a`); prompts `b2167930` (pin
  `6d47c762`) and `c72748dc` (pin `c8690022`).
- First launch sessions: 2019 `session_01Y27spXDj2YyEtEGwPS4M7e`, 2020 `session_01LNdYgisFGFddimKkCtgUm6`, 2021 `session_014vfQ7ZmDu8GBDghRDCZniH`,
  2022 `session_01XtGth8hnAAQSu32eoHtqHX`, 2023 `session_01HHz1ioHN63RzNcKxegtdK8`, 2024 `session_01EU1SBoX87EWLiiaaCfYbYM`, 2025 `session_01UT7Fiv8NtLUGvbCK4eLhoF`.
- Relaunch sessions: 2019 `session_016Q25kM55oR9F4vqg6wf4wZ`, 2020 `session_01MHWSyP87HaQpJXFJtiSu76`, 2021 `session_01MeWGRZv3JxeZJDc1Upcunw`,
  2022 `session_01CNV2FaVSEWeYvziuEN8JDr`, 2023 `session_01WNTjYengbMZns2cWSX3BaW`, 2024 `session_0134eBEMbmBA5XWBnvv275zV`, 2025 `session_01GXNpmb2dkx3h2Kd6TXkscx`.
- Engine lane: UC-1-FINISH `session_01CghV9pMqkD5TDmYicDuMCx`, branch `claude/ucmilp-1-engine-mcst`, PR #7194.
- Zero-LP instruments validated on the control in this session (ready for the next attempt): `calibration_verdict.py --json` diff per
  (criterion, key, year); UC-0's `screen_year` re-measurement (reproduces the board: 2019 lower-tercile +$13.16, ratios 0.025 / 0.04;
  2020 +$14.27, 0.15 / 0.111); the wall-row / uplift scorer over `uc_solve_log_<y>.json` + `uc_uplift_<y>.parquet`.

## Log entry

- 2026-10-04 · UC-2-SPP `session_01QBeFQCYTmVafRpi7Ujb9gs` (Fable) · branch `claude/ucmilp-2-spp-ab-r7qd` off main `d62ae1a7` · zero LP in the parent ·
  PRECOMMIT `719ceac5` pushed before any shard (targets 2020 C3a ≤ +18.85 %, 2019 C3a ≤ +11.15 %, 2020 C3b ≤ 0.2725; no-flip control; kills) ·
  7 shards @`6d47c762` → engine crash `uc.py:363 artifact_dir` (fixed by UC-1-FINISH) · 7 shards @`c8690022` (desk ruling, rebase G-DRIFT INERT
  for SPP) → **kill #1: UcWindowInfeasible in 7/7 years, no incumbent, ≈window 0** · **STOPPED; no reading; verdict none; cell stays U; D-6 = hold** ·
  no bundle, no shard branch, all 14 shards archived · routed to UC-1-FINISH (window index, LP-relaxed re-solve, model dump) and UC-DESK (hold vs close).
