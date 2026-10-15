# RESULT — UC-4-SPP: arm U4 (uc-1.7: floors off + DA-forecast commitment + reserve co-opt + ≥½ spinning) — **R**; 6 of 7 years solved, 2023 held

**Lane:** UC-4-SPP · **Session:** `session_01UYuwJsRFcDMq9nbgGFJFnc` (Opus) · **Date:** 2026-10-15 · **Branch:** `claude/ucmilp-4-spp`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), plan §11 r14.
**PRECOMMIT:** `PRECOMMIT-ucmilp4-spp-2026-10-15.md`, pushed `b14efcf7` before any shard. Addenda: A (launch record, desk gate wording), B (desk 12.8 GiB gate), C (12.8 withdrawn, 2023 held).
**Pin:** engine `uc-1.7` at `7dbfe20f`. Shards pinned `b14efcf79ec1f1cf045f17e2c7ed8df8866fe846` (`src/`+`scripts/` equal to the pin).
**LP in this session:** zero. **Control:** keeper `2026-10-03-closeout-spp-nuc-keeper` (rule 29(b)). **Rubric:** 3.20. **Not registered** (E13); local probe registration only, never committed.

## 0. Headline

- **Verdict: R.** Kill #3 fires (4 PASS→FAIL flips), and T2 moves the wrong way past the control (2019 C3a +12.3 → **+15.3 %**). T1 and T3 do not move (2020 C3a +27.7 → +27.8 %; C3b 0.345 → 0.345).
- **Against its nearest ancestor (UC-3 arm B, uc-1.5), the new mechanisms pull prices back to the control level:** 2020 C3a +36.7 → +27.8 %, C3b 0.421 → 0.345; 2019 +18.8 → +15.3 %. They do not get below the control.
- **2024 is the new failure: C3a −11.2 → +47.6 %, C3b 0.216 → 0.625, 169 MWh unserved.** It is mechanical, not a tuning issue:
  - All 35 reserve-shortfall hours and all 101 hours above $200 fall where the EIA-930 DA forecast was **below** actual load, by 0.8–3.2 GW (mean −2.1 GW). 2024 is the only SPP year with a negative mean forecast error (−239 MW).
  - The UC commits to the forecast. P1 has no intraday/RUC recommitment of slow units, so the shortfall clears as reserve scarcity (pooled contingency short up to 1.3 GW in 28 h at the $1,100 step; spin short 35 h at $250; LMP up to $2,000).
  - Real SPP covers this gap with its reliability (RUC) and intraday commitment. The model has no such stage. This is a structural gap, not a parameter (rule 1).
- **Commitment physics moved the right way:** CC starts ÷ CEMS 1.7–2.3× → **0.53–1.02×**; the conduct floors' forcing is gone (C8 ST_GAS 16–34 % → 7–20 %; no D-4 FAIL row). ST_GAS is now under-started (0.15–0.53×) and under-generated (−5 to −10.5 TWh).
- **Reserves are no longer dormant for the first time in SPP:** the spin sub-row binds 1,900–3,200 h/yr; M4 dormancy 1.00 → 0.67–0.82 (T5 sign met).
- **Engine clean:** 0 of 2,190 windows infeasible, 0 time-limit hits, defect-6 forced peak energy ≤ 0.001 TWh, uplift 0.26–1.45 %, no new D-4 row.

## 1. Gate table — control → U4, per year (`calibration_verdict.py`, rubric 3.20)

C1 entries are model − actual TWh; **bold** = status change vs control; F = FAIL, P = PASS.

| year | C3a | C3b | C1 CC_REGULAR | C1 COAL_PRB | C1 ST_GAS | C1 CT_PEAKER | C3c (model h > $200 / actual) | C8 ST_GAS | unserved MWh |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | F +12.3 → F **+15.3 %** | P 0.160 → P 0.191 | +2.25 → +1.97 | +0.24 → +0.86 | −4.96 → −7.49 | +1.49 → +3.04 | 0 → 2 / 47 | 18.1 → 6.7 % | 0 → 0 |
| 2020 | F +27.7 → F +27.8 % | F 0.345 → F 0.345 | +1.60 → +2.86 | −3.03 → −3.63 | −3.42 → −6.31 | +6.15 → +7.40 | 0 → 0 / 23 | 15.7 → 6.9 % | 0 → 0 |
| 2021 | P +7.1 → P +7.1 % | P 0.176 → P 0.133 | F −8.92 → **P −6.86** | F +10.98 → F +9.33 | −2.83 → −5.00 | +1.31 → +2.39 | 372 → 354 / 140 | 28.8 → 13.3 % | 0 → 0 |
| 2022 | P −4.8 → P −3.2 % | P 0.175 → P 0.171 | F −9.16 → **P −7.79** | F +10.75 → F +9.00 | −5.18 → −7.61 | −1.39 → +0.83 | 0 → 3 / 99 | 33.8 → 19.5 % | 0 → 0 |
| 2023 | held — not solved | | | | | | | | |
| 2024 | F −11.2 → F **+47.6 %** | F 0.216 → F 0.625 | −5.80 → −6.11 | +0.82 → −1.53 | P −6.31 → **F −10.51** | P +2.36 → **F +8.26** | F 0 → **P 101** / 59 | 18.3 → 6.8 % | 0 → **169** |
| 2025 | P −4.3 → P −3.6 % | P 0.153 → **F 0.220** | −7.86 → −6.22 | +7.39 → +6.76 | P −6.91 → **F −8.61** | −0.05 → +0.40 | 0 → 2 / 68 | 17.7 → 16.2 % | 0 → 0 |

- **Flips vs the keeper (real):**
  - 4 downgrades: C1 ST_GAS 2024 and 2025, C1 CT_PEAKER 2024, C3b 2025.
  - 4 upgrades: C1 CC_REGULAR 2021 and 2022, C3c 2024, C4 gas dispatch correlation 2022.
  - The C3c CAVEAT → FAIL change in 2019–2022 is the known missing-attestation artefact. Magnitudes are compared instead, and they barely move.
- **D-4:** the control's 7 `st_gas_mustrun_per_plant` FAIL rows are gone (expected). No new FAIL row.
- **C1 COAL_LIGNITE** stays PASS in every year (−1.4 to +0.2 TWh, closer to actual than the control in 5 of 6 years). **C4** and **C2** have no other change.
- **Determination:** NOT-YET for both. The control grades 3 of 8 (5 fails); U4 grades 3 of 7 (4 fails), with C6 UNATTESTED as for any probe.
- **Unserved bar** (≤ control + 500 MWh): met in every year. The maximum is 169 MWh, in 2024.

## 2. Pre-registered readings

### 2.1 Targets (UC-3's bars)

| # | bar | control | UC-3 arm B (uc-1.5) | **U4** | reading |
|---|---|---|---|---|---|
| T1 2020 C3a | ≤ +18.85 % | +27.7 % | +36.7 % | **+27.8 %** | not met; no move |
| T2 2019 C3a | ≤ +11.15 % | +12.3 % | +18.8 % | **+15.3 %** | wrong way past the control |
| T3 2020 C3b | ≤ 0.2725 | 0.345 | 0.421 | **0.345** | not met; no move |
| T4 M3 ≤ $15 / < $0 ratios | rise | 2019 0.025 / 0.040; 2020 0.150 / 0.111 | fell | **2019 0.057 / 0.09; 2020 0.196 / 0.204** | sign met; also rises in 2021, 2022 and 2025, falls in 2024 |
| T5 M4 reserve dormancy | falls | 1.00 (MCP $0) | 1.00 | **0.80 / 0.82 (2019 / 2020); 0.67 (2024)** | sign met |

### 2.2 Starts ÷ CEMS (M1, `screen_year`), control → U4

| year | CC_REGULAR | ST_GAS | COAL_PRB | COAL_LIGNITE |
|---|---|---|---|---|
| 2019 | 1.71 → 0.53 | 0.64 → 0.19 | 0.30 → 0.43 | 0.53 → 0.73 |
| 2020 | 1.71 → 0.56 | 0.45 → 0.15 | 0.39 → 0.49 | 0.31 → 0.51 |
| 2021 | 1.90 → 0.72 | 0.61 → 0.20 | 0.53 → 0.85 | 0.33 → 0.79 |
| 2022 | 2.27 → 1.02 | 0.71 → 0.36 | 0.59 → 1.24 | 0.35 → 1.50 |
| 2024 | 1.96 → 0.72 | 0.88 → 0.30 | 0.57 → 0.94 | 0.17 → 2.75 |
| 2025 | 1.73 → 0.65 | 0.67 → 0.53 | 0.65 → 0.96 | 0.09 → 0.96 |

- CC moves from 2× over-cycling toward 1×. UC-3 arm B read 0.46–0.89×, so per-unit `ut_h` and DA commitment bring CC closer to CEMS.
- ST_GAS under-cycles in every year. This is the same residual UC-3 named (steam-gas commitment), and the U4 mechanisms do not close it.
- Coal starts move from below CEMS to about 1×. Lignite overshoots in 2022 and 2024 (3 plants; small counts).

### 2.3 Reserve and the DA-forecast seam

| year | spin sub-row binding h | contingency short h (max MW) | spin short h | DA − actual at the shortfall hours | P1 dump MWh |
|---|---|---|---|---|---|
| 2019 | 2,122 | 0 | 0 | — | 0 |
| 2020 | 1,913 | 0 | 0 | — | 0 |
| 2021 | 2,639 | 0 | 0 | — | 0 |
| 2022 | 2,472 | 0 | 0 | — | 0 |
| 2024 | 3,231 | 28 (1,305) | 35 | −0.8 to −3.2 GW, mean −2.1, 35 of 35 negative | 0 |
| 2025 | 2,249 | 0 | 0 | — | 0 |

The positive forecast bias in the other years (+0.6 to +2.1 GW mean) caused no P1 dump: over-commitment was absorbed at committed floors.

### 2.4 Price-move diagnosis (zero LP)

Change in mean model error by actual-price tercile, U4 − control, in $/MWh:

| year | low tercile | mid tercile | top tercile |
|---|---|---|---|
| 2019 | −0.67 | +0.51 | +1.51 |
| 2020 | −1.51 | −0.04 | +1.16 |
| 2021 | −2.60 | −1.39 | +2.97 |
| 2022 | −2.32 | −0.90 | +3.95 |
| 2024 | +1.45 | +2.13 | **+32.96** |
| 2025 | −1.35 | −0.07 | +1.69 |

- Both ends move toward actual. The control is too high in the trough (+10 to +14) and too low at the top (−6 to −21).
- The load-weighted mean still rises in 2019, because the top-tercile lift outweighs the trough cut.
- Cause, by sign:
  - **Top tercile:** (iii), the reserve dual. The spin sub-row binds at the peak and its price enters the LMP through co-optimization.
  - **Trough:** (ii) in reverse. More coal is online (coal starts and generation up), which lowers the trough.
- **2024** is (iii) at scarcity, driven by the forecast under-shoot (§0).

## 3. Kills and engine

- **#1 (infeasible window):** not fired. 2,190 of 2,190 windows Optimal; 0 time-limit hits; MILP gap p95 ≤ 9.2e-4.
- **#2 (non-determinism):** not exercised. No year completed twice.
- **#3 (control flip):** **fired** (§1).
- **#4 (unserved > control + 500 MWh):** not fired. The maximum is 169 MWh.
- **Defect-6 recurrence check:** forced peak-tranche energy 0.0000–0.0008 TWh/yr, far below the 0.1 TWh report bar.
- **Ruling (a):** integer set = gate set every year (94 / 92 / 88 / 86 / 83 / 82). Some shards counted the non-integer CT clusters as "no integer under ruling (a)"; they are CTs by class, not ruling-(a) drops.
- **Inherited log warning (not a defect of this arm):** each leg logs a caught `resolved_inputs: split-remap probe failed`. The keeper arms `campd_split_remap_companions`, but `campd-unit-outages-maxgen-splitremap-SPP.csv` has never been derived. Routed to UC-DESK as a keeper-recipe data item.

## 4. Cost: uplift, wall clock, memory

| year | uplift $M (% of Σλ·load) | P0 s | P1 s | UC seam s | total s | ÷ (P0+P1) | cgroup peak GiB | container ceiling + swap |
|---|---|---|---|---|---|---|---|---|
| 2019 | 20.2 (0.31 %) | 104.7 | 88.8 | 2,135 | 2,424 | 12.5× | 7.88 | 22.4 |
| 2020 | 27.0 (0.49 %) | 107.4 | 109.1 | 2,205 | 2,521 | 11.6× | 7.85 | 22.4 |
| 2021 | 97.9 (0.91 %) | 136.3 | 119.3 | 1,523 | 1,875 | 7.3× | 7.98 | 17.4 |
| 2022 | 111.1 (0.90 %) | 123.9 | 143.7 | 1,901 | 2,282 | 8.5× | 8.11 | 17.4 |
| 2024 | 28.7 (0.26 %) | 138.8 | 151.6 | 3,174 | 3,612 | 12.4× | 8.44 | 17.4 |
| 2025 | 121.0 (1.45 %) | 104.8 | 104.3 | 1,496 | 1,786 | 8.5× | 8.21 | 22.4 |

- Every year is above the ruled 3× ceiling. That is a cost finding, not a defeat.
- U4 is slower than UC-3 arm B (6.8–9.2×). The spin sub-row adds nodes: p95 12.8–16 vs 7–13.
- Peak memory is at most 8.44 GiB, inside the 8.48 GiB SPP maximum measured in UC-3.

## 5. Coverage gap: 2023 held pending the owner's gate ruling

Seven containers were offered for 2023 across 5 launches; every one provisioned 17.4–18.4 GiB, below the charter's 22.4 GiB gate.

| attempt | session | ceiling + swap |
|---|---|---|
| 1 | `session_01VDPF1nn49J7fJZybe3YLvz` | 18.4 |
| 2 | `session_016ct9KBLWz3TWxRo1haDKRE` | 17.4 |
| 3 | `session_0129ry7ewc3o2y58Z6ZSBX89` | 17.4 |
| 4 | `session_01BydsXKM9zQ5BgBDmNZ7qQo` | 17.4 |

- UC-DESK (12:35Z) held the last relaunch: *"held pending owner gate ruling"*, not a gap.
- 2021, 2022 and 2024 solved in 17.4 GiB containers under the desk's 12.8 GiB rule before it was withdrawn (Addendum C), at peaks of 7.98–8.44 GiB.
- The verdict does not depend on 2023: kill #3 and T2 already fix R.

Gate outcomes across all 14 launches: 3 passed at 22.36 GiB (2019, 2020, 2025); 3 ran under 12.8 at 17.4 GiB (2021, 2022, 2024); 8 blocked at 17.4–18.4 GiB.

## 6. Disclosures

1. **Composition:** a scratch copy of `_ucmilp_compose_span.py`, as in UC-3, with two changes. No repo script was edited.
   - `gas_price_override` was added to `PER_YEAR_FIELDS`.
   - `_closeoutsppnuc_compose_span._respan_shared_inputs` was applied after the first `meta.json` write.

   The six-year span's benchmark frames are content-addressed rebuilds over its own years (`campd-f9bf95263325`, `eia923-6a45beea3fcf`, `eia930-64afaacbd348`). Without 2023 they cannot equal the keeper's 7-year hashes. The per-year benchmark content is the same source data.
2. **Scoring:** `dashboard_add_run.py --no-prune` was run locally for run id `2026-10-15-2026-10-15-ucmilp4` (label parser). The sidecar, payload and frames are excluded via `.git/info/exclude` and **not committed**.
3. **Gate episode** (Addenda B and C): the desk's 12.8 GiB re-base was followed for two launches and one message. This session's permission classifier then refused further launches under it, and the lane reverted to 22.4.
4. **Shards** ran `uv sync` when `.venv` was absent (the documented install route), and left the runner's `_shared/SPP` cache files untracked. No shard edited `src/` or `scripts/`.

## 7. Where everything is

| artefact | where |
|---|---|
| 6 leg bundles (21 files each, full, with `dispatch/`) | `claude/ucmilp4-spp-u4-2019` `e70838df` · `-2020` `3f9fd4f5` · `-2021` `99bda9b6` · `-2022` `a3062c45` · `-2024` `df677899` · `-2025` `21ac9628` |
| slim span (metrics, diagnostics, configs, UC logs, `hourly/` without `unit_hourly`; 26 MB) | `docs/records/spp/ucmilp/data/ucmilp4_spp_u4_span/` |
| composed full span | local only (`results/calibration/ucmilp4_spp_u4_span`); it will not survive the container |
| shard sessions | all 14 verified where solved, then archived (rule 33); none left alive |

- **Promotion:** none proposed (R).
- **Branches for the owner to cut once this PR merges:** `claude/ucmilp4-spp-u4-{2019,2020,2021,2022,2024,2025}`. No 2023 branch exists.

## 8. Rule-1 reading and D-6 card

The remaining SPP gap is **structure, not engine and not calibration**. Two objects are named:

1. **Steam-gas commitment.** ST_GAS is under-started (0.15–0.53× CEMS) and under-generated in every year. This is unchanged since UC-3.
2. **The missing reliability/intraday recommitment stage**, which a forecast-based DA commitment needs. Without it, any year whose forecast runs below actual turns the gap into reserve scarcity (2024).

> **SPP UC-4 (uc-1.7, U4 = floors off + DA forecast + co-opt + ≥½ spin): R.** Prices return to the keeper's level (2020 C3a +27.8 %) from arm B's +36.7 %, but not below it. 2019 is worse (+15.3 %). 2024 blows up (+47.6 %) because the UC commits to a DA forecast 2 GW below actual with no RUC stage. CC cycling is fixed (0.5–1.0× CEMS); ST_GAS still under-commits. Options:
> - record R and close the SPP UC cell (recommended);
> - charter a reliability-commitment (RUC) stage design lane before any further SPP UC arm.

## Log entry

- 2026-10-15 · UC-4-SPP · pin `7dbfe20f` (uc-1.7) · 14 launches; 6 years solved; 2023 held pending the owner's gate ruling.
- Arm U4 **R**: kill #3 (4 flips), T2 wrong way (2019 +15.3 %), T1/T3 flat; 2024 C3a +47.6 % from DA under-forecast scarcity with no RUC stage.
- CC starts 0.53–1.02× CEMS; reserves non-dormant; engine clean; uplift ≤ 1.45 %; wall 7.3–12.5×; memory peak ≤ 8.44 GiB.
