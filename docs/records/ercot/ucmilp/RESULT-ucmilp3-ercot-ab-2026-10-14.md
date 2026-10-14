# RESULT — UC-3-ERCOT: the UC A/B on all seven ERCOT years at the clean engine (uc-1.5), with uc-1.4 beside it, 2026-10-14

**Verdict: R.** At uc-1.5, the engine with defects 3–7 fixed, kill #3 fires on **6 real control flips**:
- **C3a price mean:** 2019 +6.2 → +17.8 %, 2020 +2.5 → +19.6 %, 2021 +0.8 → +10.2 %.
- **C1 CC_REGULAR energy:** 2021 −0.83 → −8.37 TWh, 2022 −3.47 → −9.69 TWh, 2024 −4.45 → −12.36 TWh.
- **T1 reads the wrong way on its own:** CC starts move further from CEMS (2019 0.16× → 0.11×, 2020 0.55× → 0.22×). So does T3: C3b in 2019/2020 rises 0.216/0.208 → 0.276/0.292.

**The engine is now clean.** Every window is Optimal, unserved energy is 0 above the keeper, no peak tranche is forced on, and uplift is ≤ 0.37 % of energy cost.

**This is a structural R on the gates, not a defect artefact.** The UC decommits 3.5–5.7 GW of CC and 1.0–1.6 GW of ST_GAS against the keeper's online envelope. Prices rise in 88–99 % of hours. Defect 7 (no-load paid twice) explains only about 10 % of that move (§3).

Lane `UC-3-ERCOT` (Opus, `session_01H8yt3XXyGyjjCpkP9jXskU`), chartered by UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on the owner's ruling of 2026-10-14 (desk decision 7). PRECOMMIT: `PRECOMMIT-ucmilp3-ercot-ab-2026-10-14.md` (§0–5 and Addenda A–C.1). It inherits `PRECOMMIT-ucmilp-ercot-ab-2026-10-10.md`.
- **Arm:** keeper `2026-10-02-closeout-l1-coal-fuel` + `unit_commitment_milp=true` + `ercot_gas_commitment_bridge=false`. Every other floor is kept, `uc_*` stay at their defaults, and offer bands are untouched.
- **Control:** the keeper's committed bundle (rule 29(b)). Re-scored at the pin, it reproduces its record: 148/148 rows, 0 diffs.

## 1. Gate table (control → uc-1.4 → **uc-1.5**; `calibration_verdict.py`, rubric 3.20)

uc-1.4 legs are at `580c4fbf` (evidence only, Addendum B). uc-1.5 legs are at `2dd69d5a`, via lane head `2fd5947a`, and carry the verdict. F = FAIL, P = PASS, C = CAVEAT. Full per-year table: `data/ucmilp3_ercot_span/gate_table.md`.

| year | C1 CC_REGULAR (TWh) | C1 COAL_PRB | C3a | C3b | C3c (h > $200; actual) | C8 ST_GAS as scored → R4 |
|---|---|---|---|---|---|---|
| 2019 | +9.21 F → +0.35 P → **+1.13 P** | −10.79 F → −4.37 P → **−4.70 P** | +6.2 % P → +18.8 % F → **+17.8 % F** | 0.216 F → 0.282 F → **0.276 F** | 90 → 111 → **111** (106) P | 17.6 → 22.0 → **22.6 % → 9.3 %** P |
| 2020 | +10.17 F → +1.97 P → **+2.84 P** | −11.85 F → −5.96 P → **−6.36 P** | +2.5 % P → +21.1 % F → **+19.6 % F** | 0.208 F → 0.304 F → **0.292 F** | 22 C → 33 → **31** (56) | 23.6 → 29.2 → **30.2 % F → 14.8 % P** |
| 2021 | −0.83 P → −9.49 F → **−8.37 F** | −2.01 P → +0.35 → **+0.29 P** | +0.8 % P → +12.5 % F → **+10.2 % F** | 0.066 → 0.156 → **0.123 P** | 651 C → 716 → **685** (258) | 21.9 → 22.6 → **24.6 % → 11.7 %** P |
| 2022 | −3.47 P → −11.04 F → **−9.69 F** | −1.38 → −0.84 → **−0.93 P** | −8.4 % P → +12.4 % F → **+8.4 % P** | 0.178 P → 0.200 F → **0.176 P** | 94 C → 180 → **160** (196) | 28.7 → 27.5 → **30.3 % F → 14.4 % P** |
| 2023 | +1.38 → −6.17 → **−5.23 P** | −2.47 → +1.19 → **+1.03 P** | −24.7 % C → −14.8 → **−15.9 %** | 0.393 C → 0.349 → **0.353** | 138 → 148 → **149** (181) P | 18.7 → 20.1 → **21.1 %** P |
| 2024 | −4.45 P → −13.40 F → **−12.36 F** | −0.97 → +4.14 → **+3.81 P** | −11.3 % F → +6.4 % P → **+4.8 % P** | 0.198 P → 0.205 F → **0.198 P** | 11 C → 24 → **21** (53) | 15.6 → 17.8 → **18.4 %** P |
| 2025 | (preliminary EIA-923: skipped) | +0.87 → +1.41 → **+1.37 P** | −9.2 % P → +8.3 % → **+6.3 % P** | 0.125 → 0.112 → **0.098 P** | 0 C → 0 → **0** (31) | 21.1 → 19.0 → **20.4 %** P |

C2, C4 and the other C1 rows: no flip in either span. C4 gas NRMSE improves in 2019–2021 (e.g. 2019 0.104 → 0.084).

**Flip counts.** Read per (criterion, key, year) against the keeper, with the inherited §3/§8 exclusions:

| | uc-1.4 | uc-1.5 |
|---|---|---|
| Raw flips | 9 | 8 |
| Real flips | 9 | **6** |

- **uc-1.4's 9:** C3a 2019–2022, C3b 2022 and 2024, C1 CC 2021, 2022 and 2024.
- **uc-1.5's 8 raw → 6 real.** The two C8 ST_GAS rows (2020 30.2 %, 2022 30.3 %) fall to 14.8 % and 14.4 % with MECH 28 removed, so R4 discounts them.
- **Excluded as attestation artefacts:**
  - C3c CAVEAT → FAIL, and 2023 C3a/C3b CAVEAT → FAIL: the probe carries no attestation, so these rows lose their ledgered or owner-exception status (inherited §8). The magnitudes are in the table.
- **Improvements that uc-1.5 keeps:**
  - C1 CC and PRB in 2019/2020 go from FAIL to PASS (T4 met in both years, both rows).
  - 2024 C3a goes from FAIL to PASS (−11.3 → +4.8 %).
  - C3c tail hours move toward actual in 2020, 2022 and 2024.
- **Gating rows:**
  - Unserved energy: 0 in six years. 2021 has 3,012.6 MWh in the same 6 Uri hours as the keeper, so the delta is 0. *The inherited §3 text "control: 0 in every year" is wrong for 2021. The keeper carries the same 3,012.6 MWh.*
  - Every leg's P1 is Optimal and has 0 NaN cells.

## 2. Target readings (inherited §2), at uc-1.5

| # | reading | control | uc-1.5 | bar | read |
|---|---|---|---|---|---|
| T1 | CC_REGULAR starts vs CEMS, 2019 / 2020 | 491 / 1,901 (0.16× / 0.55×) | **346 / 761 (0.11× / 0.22×)** | ratio into [0.40, 2.5] / [0.74, 1.35] | **wrong sign** (as at UC-2) |
| T2 | M2(b) CC near-min-load while CEMS off, TWh | 9.34 / 8.94 | 4.38 / 4.80 | ≤ 4.67 / ≤ 4.47 | met / short, right sign |
| T3 | C3b 2019 / 2020 | 0.216 / 0.208 | **0.276 / 0.292** | ≤ 0.208 / ≤ 0.204 | **wrong sign** |
| T4 | C1 CC 2019 / 2020; PRB 2019 / 2020 | +9.21 / +10.17; −10.79 / −11.85 | +1.13 / +2.84; −4.70 / −6.36 | ≤ +8.6 / ≤ +9.1; ≥ −9.4 / ≥ −9.9 | **met, all four** |
| T5 | trough prices (actual ≤ $15 hours) | model 16–30 $/MWh vs actual 6–11 | arm adds +1.6 to +7.9 $/MWh in those hours in every year | toward actual | **wrong sign** |
| T6 | reserve MCP / dormancy | — | unchanged (Δ ≤ $0.1) except 2021/2022 (+$5.3 / +$3.7 mean) | falls | no move |

Under §7.1, T1, T3 and T5 each read R on their own. The kill reads R as well.

## 3. What moves the price — zero LP, from the bundles (`data/ucmilp3_ercot_span/scripts/diag_price.py`)

Demand-weighted system price, arm − keeper, by actual-price hour class. The full JSON per year is in `readings15/diag15_<y>.json` and `readings14/diag_<y>.json`.

| year | Δ mean, uc-1.4 → **uc-1.5** ($/MWh) | Δ low third / high third (uc-1.5) | hours up | CC online, keeper → uc-1.5 (GW) | ST_GAS online (GW) |
|---|---|---|---|---|---|
| 2019 | +5.3 → **+4.9** | +2.0 / +9.1 | 92 % | 23.8 → 20.1 | 4.0 → 2.7 |
| 2020 | +4.2 → **+3.8** | +1.6 / +7.6 | 88 % | 23.0 → 19.6 | 3.7 → 2.5 |
| 2021 | +17.8 → **+14.3** | +5.7 / +23.0 | 97 % | 20.9 → 15.8 | 3.7 → 2.8 |
| 2022 | +14.6 → **+11.9** | +7.8 / +17.8 | 99 % | 23.1 → 17.4 | 4.2 → 3.2 |
| 2023 | +6.1 → **+5.5** | +3.8 / +8.6 | 96 % | 24.1 → 20.2 | 4.3 → 2.7 |
| 2024 | +5.2 → **+4.7** | +2.5 / +8.1 | 92 % | 23.6 → 20.0 | 4.3 → 2.8 |
| 2025 | +6.3 → **+5.6** | +4.4 / +7.2 | 96 % | 23.4 → 19.4 | 3.7 → 2.7 |

**Read.** The attribution is descriptive (rule 21: no parameter comes from it).

- **The UC holds 3.5–5.7 GW less CC online than the keeper in every year.** The keeper's online CC is mostly its committed tranche (`cc_committed_per_plant`), plus the gas bridge the arm removes.
- **In high-price hours, the marginal unit moves up the stack.** ST_GAS's share of marginal unit-hours falls from 0.29 to 0.09 (2019) and from 0.29 to 0.16 (2022). CT_PEAKER's rises from 0.10 to 0.26 (2019) and from 0.15 to 0.32 (2022) (`marginal_mix_*`, uc-1.5).
- **In trough hours, PRB coal is marginal more often:** 0.33 → 0.45 of marginal unit-hours in 2019, 0.16 → 0.29 in 2022.
- **Mechanisms (ii) and (i) carry the move:**
  - (ii) the lost near-min-load body. Committed CC at minimum load was depressing troughs.
  - (i) higher-tranche units setting price after decommitment.
  - (iii) reserve duals move only in 2021/2022.
- **Defect 7's share.** uc-1.4 → uc-1.5 lowers Δ mean by $0.4–0.7/MWh in normal years and $2.7–3.5/MWh in the high-gas years. It returns 0.2–0.4 GW of CC online and removes 3 flips (2022 C3a, 2022 C3b, 2024 C3b). The defect explained about 10 % of the price move. The remaining 90 % is the UC itself.

**Rule-1 reading for the D-6 card.** These are reported, not tuned, because offer bands are out of scope for this lane.

- **(a) The commitment pattern is structurally off.** The UC decommits whole plants for long stretches, while CEMS shows CC cycling 3–4× more often than the model does (T1). The real fleet stays online at part load and starts more often. The UC finds it cheaper to stay off.
- **Candidate causes, none tested here:**
  - 50 of 139–141 clusters (6 integer) run on class-fallback no-load and UT/DT.
  - Each plant is one cluster, so a multi-unit CC plant commits as a block.
  - The 24 + 12 h window cannot see weekly cycling value.
  - The keeper's CC committed tranche and its bands were tuned on the bridge structure that the arm removes.
- **(b) The keeper's offer bands interact with the result.** The authorized peak-band multipliers were set ex ante against the keeper's own commitment. With the online envelope 4–6 GW thinner, those bands now set price more often. That is UC-BANDS-ERCOT's question (desk decision 8), not this lane's. Applying the bands unchanged to a different commitment structure is a declared confound, not a fit lever.

## 4. Structure and cost

| year | P0 s | UC s (Σ MILP; mean/p95) | P1 s | total s | ratio total/(P0+P1) | nodes p50/p95 | TL hits | int clusters | uplift ($M; % of λ·load) | pass 2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 269.7 | ≈ 8,320 (8,082; 22.1/58.1) | 654.9 | 9,408.6 | **10.2** | 13/102 | 0 | 62/141 | 24.6; 0.12 % | reused |
| 2020 | 290.7 | 8,012 (7,780; 21.3/55.7) | 660.0 | 9,153.4 | **9.6** | 18/113 | 0 | 61/141 | 42.8; 0.37 % | reused |
| 2021 | 348.5 | 21,312 (21,017; 57.6/205.2) | 820.6 | 22,712.7 | **19.4** | 45/501 | **1** (w290) | 61/139 | 93.8; 0.13 % | reused |
| 2022 | 397.9 | 19,351 (19,100; 52.3/186.6) | 978.0 | 20,932.2 | **15.2** | 54/556 | 0 | 61/139 | 95.0; 0.27 % | reused |
| 2023 | 387.9 | 9,145 (8,837; 24.2/68.3) | 894.7 | 10,657.1 | **8.3** | 18/128 | 0 | 61/139 | 23.0; 0.09 % | reused |
| 2024 | 432.0 | 9,840 (9,508; 26.0/64.0) | 432.2 | 10,900.0 | **12.6** | 17/114 | 0 | 61/139 | 27.3; 0.18 % | skipped |
| 2025 | 880.1 | 13,749 (13,261; 36.3/101.3) | 866.2 | 15,786.0 | **9.0** | 17/133 | 0 | 61/140 | 48.8; 0.26 % | skipped |

- **Wall ratio:** 8.3–19.4× against the owner's 3× (D-2; reported, not judged). 2021/2022 are the slow years: B&B tail p95 of 500+ nodes, about 2× the uc-1.4 UC wall.
- **Time-limit hits:** W2 allows ≤ 3/365; the worst is 1 (2021 window 290, gap 1.12e-3, incumbent held). At uc-1.4, 2021 had 3 hits (Uri windows 45–47).
- **Uplift:** W3 bar ≤ 2 %; every year is met.
- **Defect 6 check:** P1 output on `_peak*` tranches above their zone price is ≤ 0.002 TWh in every year, equal to the keeper's. Defect 6 is not present.
- **Memory:** 2021, 2022 and 2023 reached the 13.36 GiB cgroup ceiling and spilled ≤ 0.22 GiB to swap. No kill, but this is the container's limit for these years.
- **Starts vs CEMS:**
  - ST_GAS: 0.24–0.54×.
  - COAL_PRB: 0.4–7×. Coal is outside the arm (yard-pinned, no integer; ruling (a)), so coal starts track the keeper's.
  - Six integer clusters run on class-fallback parameters every year.
  - D-4 per-unit conduct FAILs (`st_netload_drag`, `chp_steam`, `reliability_floor × CT_PEAKER`) were present in the keeper and are not introduced by the arm.

## 5. D-6 card (verbatim-ready)

> **ERCOT, `unit_commitment_milp`: record R, structural.** At uc-1.5 (`2dd69d5a`, engine defects 3–7 fixed), arm = UC on + gas bridge off, every other floor kept, all seven years: 2,555/2,555 windows solved (1 at the time limit with an incumbent), 0 unserved beyond the keeper, uplift ≤ 0.37 %, no forced peak tranche. **6 control flips:** C3a 2019/2020/2021 (+6.2/+2.5/+0.8 % → +17.8/+19.6/+10.2 %) and C1 CC 2021/2022/2024 (−0.8/−3.5/−4.5 → −8.4/−9.7/−12.4 TWh). Gains: C1 CC and PRB in 2019/2020 FAIL → PASS, and 2024 C3a −11.3 → +4.8 %. The mechanism is the same in every year: the UC holds 3.5–5.7 GW less CC online than the keeper and decommits rather than cycles (CC starts 0.11–0.56× CEMS). Prices rise in ~95 % of hours. Defect 7 explained ~10 % of this. Wall 8.3–19.4× P0+P1 against 3×.
> Options: **record R (recommended)** · hold for a commitment-fidelity lane (measured no-load/UT/DT for the 6 class-fallback integer clusters, unit-level CC clusters, the UC-BANDS-ERCOT bands), then a fresh A/B · promote on structure (not supported: T1/T3/T5 wrong sign, six pre-declared kills).

## 6. Bundles, cost, housekeeping

| artefact | where | promotable? |
|---|---|---|
| uc-1.5 legs (verdict) | `claude/ucmilp3b-ercot-2019` `61010b2f` · `-2020` `ce83e470` · `-2021` `d7a90d59` · `-2022` `e43a3da1` · `-2023` `cd9598e2` · `-2024` `c50a5b36` · `-2025` `8d0c4be6`; 21 files each, `dispatch/<y>_P1.parquet` included, `unit_hourly` left out (rule 15); no file > 100 MB, so none split | in form (rule 34; all seven years); not recommended (R) |
| uc-1.4 legs (evidence) | 2019 = `claude/ucmilp-fix5-ercot-2019` `f832aa52` (reused; Addendum A §1.1, `f998cf47` → `580c4fbf` code-identical) · `claude/ucmilp3-ercot-2020` `2f6b9e1d` · `-2021` `556f9a3e` · `-2022` `4fef5baf` · `-2023` `090b2a35` · `-2024` `bbe10707` · `-2025` `9a0665e8` | evidence only |
| slim span + readings | `docs/records/ercot/ucmilp/data/ucmilp3_ercot_span/` (40 MB): uc-1.5 `meta`, `run_config*`, regenerated `legitimacy_diagnostics.json`, `uc_solve_log_<y>.json`, `hourly/{class_band_hourly,class_hourly,system,storage,reserve_family,uc_schedule,uc_uplift}_<y>`; `readings15/` (arm verdict, flip diff, R4, M1/M2 screen, price diagnosis), `readings14/` (the same for uc-1.4), `gate_table.md`, `wall_rows.md`, `scripts/` | not registered (E13) |

**Composition and scoring, disclosed.**
- **Composer:** the prior lane's scratch composer (`scripts/compose_ercot.py`), with `write_uplift` synced to `main`'s (uplift is never recomputed from a bundle). Its recipe assertion passed on all 14 legs: the delta beyond the two arm fields is only the rule-26-deleted `unit_outage_dispatched_bin_live_denominator`.
- **Scoring:** the local `dashboard_add_run.py --no-prune` route was refused here because it writes `frontend/data/`. Scoring instead used `scripts/score_local.py`. It copies `frontend/data/backcast` into the scratchpad, repoints every path constant there, and refuses to run if any module still points at the repo copy. It then renders, writes the sidecar and runs `calibration_verdict.determine`. The repo's `frontend/data` was never written, and the control re-scores identically by the normal route. Nothing is registered, promoted or deleted (rules 15, 31; E13).

**Cost.**
- 14 solve shards (7 uc-1.4 evidence + 7 uc-1.5) of 2.5–6.3 h each, about 70 container-hours. Zero LP ran in the parent.
- Every shard was archived after fetch and verification (rule 33). None is left alive.
- Branches the owner may cut once the PR merges (a session cannot: 403): `claude/ucmilp3-ercot-{2020..2025}` and `claude/ucmilp3b-ercot-{2019..2025}`.

**Promotion question:** none is proposed; the lane recommends recording R. The local bundles do not survive this container, but the leg branches hold the bytes.

## Log entry

- 2026-10-14 · UC-3-ERCOT (Opus, `session_01H8yt3XXyGyjjCpkP9jXskU`) · `claude/ucmilp-3-ercot-ab` · zero LP in the parent.
  - uc-1.4 span: 7 legs at `580c4fbf` (2019 reused from the FIX-4 repro), 9 flips.
  - Defect 7 (no-load paid twice) was confirmed mid-lane. The desk moved the verdict to uc-1.5 (Addendum B). 7 fresh legs ran at `2dd69d5a` (Addendum C).
  - **R: 6 real flips** (C3a 2019–2021; C1 CC 2021/2022/2024). T1/T3/T5 wrong sign; T2/T4 met.
  - The UC decommits 3.5–5.7 GW CC, prices +$3.8–14.3/MWh. Defect 7 explained ~10 %.
  - Wall 8.3–19.4×. Engine clean: 0 unserved Δ, uplift ≤ 0.37 %, no forced peak tranche.
  - Cell `unit_commitment_milp` R (UC-2 R, superseded by this clean R).
