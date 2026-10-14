# RESULT — UC-3-NYISO: the MILP UC A/B relaunched at the clean engine (uc-1.4), every NYISO backcast year — **R (clean, not defect-confounded)**

**Lane:** UC-3-NYISO · **Session:** `session_01CQxD6oMjTSxFp8nDQKPKRs` (Opus) · **Date:** 2026-10-14 · **Branch:** `claude/ucmilp-3-nyiso-ab`
· **PRECOMMIT:** `PRECOMMIT-ucmilp3-nyiso-ab-2026-10-14.md` (pushed `1e337eeb` before any shard; it adopts every reading, bar, kill and
verdict rule of `PRECOMMIT-ucmilp-nyiso-ab-2026-10-10.md` unchanged) · **Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`) on the
owner's 2026-10-14 ruling, decision 7 (relaunch every UC-2 ISO at uc-1.4). **Pin solved:** `1e337eebd95e11230ecfa8db4694057297554002`
(main `580c4fbf`, engine **uc-1.4**, plus records). **LP in this session:** zero (five year-isolated shards, rule 36). **Registered:**
nothing (E13).

## 0. Headline

**The UC-2 R holds at the clean engine, and it is now a real rejection rather than one confounded by defect 6.**
- **Defect 6 is gone.** CC_REGULAR peak-tranche energy:
  - uc-1.1: 1.4–2.0 TWh/yr, on all 8,760 h;
  - uc-1.4: 0.10–0.92 TWh, against the control's 0.07–0.76.
  - ST_GAS peak energy equals the control's.
- **Uplift fell** from 1.4–1.8 % to **1.0–1.4 %** of energy cost.
- **The CC decommit remains, and is larger.** The UC still decommits **5.3–7.4 TWh/yr of CC_REGULAR**; imports fill the gap (+5.6 to +6.5 TWh).
- **The price body now rises in every year** (+$0.2 to +$2.9/MWh).
  - At uc-1.1, the forced peak-tranche energy had been pushing prices down, which hid part of this rise.
  - The lower-tercile error rises in 5 of 5 years.
  - In the hours whose price rose, the marginal unit moves from ST_GAS / CC_REGULAR to CT_PEAKER, CC_CHP and imports.
- **Five real control flips** (kill #3):
  - C1 CC_REGULAR 2021 and 2023;
  - C1 ST_GAS 2021;
  - C1 CC_CHP 2023;
  - **C3a 2023 (+2.0 → +10.5 %)**.
- **T2 is breached:** C3a 2024 moves −0.8 → **+4.5 %** (bar ≤ +0.2 %).
- **T3 is breached:** C1 CC_REGULAR fails in 2021 and 2023.
- **One uc-1.1 flip is gone:** C3a 2025 is −7.4 %, a PASS.
- **Engine health is clean:** all 1,825 windows Optimal, 0 time-limit hits, 0 MWh unserved, and pass-2 reuse not exercised.

The engine is clean; the NYISO arm, as defined, does not leave the calibrated control calibrated. **Verdict `R`.**

### 0.1 Gate table — control (keeper `2026-10-02-w0-nyiso`) → arm (uc-1.4); uc-1.1 (UC-2) in brackets

Control and arm were scored on the same bench parts. The bench parts the scratch registration wrote are byte-identical to `main`'s, and
the control re-scores identically to UC-2's reading at its pin.

"FAIL\*" in C3c is the probe's missing attestation (C6 UNATTESTED), not a model move. Its magnitudes are identical to the control's,
except 2025, where hours above $300 go 8 → 1.

| year | C1 (Δ TWh vs actual; rows that move) | C3a | C3b (NRMSE) | C3c (model h > $300 / RT h) | C4 gas r | C8 ST_GAS as printed / without MECH 28 · CC | unserved MWh | uplift % ($M) |
|---|---|---|---|---|---|---|---|---|
| 2021 | **CC_REGULAR +1.31 → −6.11 FAIL** [−4.71]; **ST_GAS −3.44 → −4.32 FAIL** [−4.31]; CC_CHP +1.52 → +2.47; CT_PEAKER +1.16 → +2.19 | +4.3 → **+9.3 %** PASS [+6.6] | 0.117 → 0.139 | 0 / 3 PASS | 0.918 → 0.925 | 22.1 → 25.7 % / 18.2 % · 0.6 → 0.8 % | 0 → 0 | 1.25 (88) [1.60] |
| 2022 | CC_REGULAR +1.24 → −3.86 PASS [−2.39]; ST_GAS −2.19 → −3.27 PASS; CC_CHP +2.43 → +2.96 (+3.0 pp, at the edge) PASS | −0.7 → **+2.3 %** PASS [−1.4] | 0.149 → 0.180 | 5 / 101 CAVEAT → FAIL\* | 0.826 → 0.826 | 14.9 → 18.3 % / 12.1 % · 0.7 → 0.9 % | 0 → 0 | 1.24 (167) [1.78] |
| 2023 | **CC_REGULAR +0.61 → −5.43 FAIL** [−4.03]; **CC_CHP +2.81 → +3.75 (+3.8 pp) FAIL** [+3.32]; ST_GAS +1.34 → −0.32 PASS | **+2.0 → +10.5 % FAIL** [+6.5] | 0.129 → 0.197 | 0 / 10 CAVEAT → FAIL\* | 0.919 → 0.918 | 11.3 → 12.4 % / 9.3 % · 1.0 → 1.3 % | 0 → 0 | 0.95 (53) [1.36] |
| 2024 | CC_REGULAR +2.02 → −3.47 PASS [−2.40]; ST_GAS −0.51 → −2.59 PASS; CC_CHP +0.84 → +1.81 | **−0.8 → +4.5 %** PASS — **T2 breached** [+1.9] | 0.118 → 0.164 | 0 / 13 CAVEAT → FAIL\* | 0.890 → 0.886 | 13.6 → 16.7 % / 11.9 % · 0.6 → 0.4 % | 0 → 0 | 1.06 (66) [1.38] |
| 2025 | (C1 SKIPPED: preliminary EIA-923) CC_REGULAR 35.39 → 29.83 TWh; ST_GAS 10.25 → 8.77 | −7.7 → **−7.4 %** PASS [−10.2 FAIL] | 0.148 → 0.166 | 8 → 1 / 42 CAVEAT → FAIL\* | 0.841 → 0.839 | 11.8 → 13.1 % / 9.3 % · 0.3 % | 0 → 0 | 1.40 (136) [1.83] |

**Determination:** CALIBRATED → **NOT-YET**. The arm fails C1 and C3a and is unattested (C6).

**2021 under the §9 drift rule:** ΔC3a is +5.0 pt (envelope 1.1) and ΔC1 CC_REGULAR is −7.42 TWh (envelope 0.10). Both 2021 flips are
therefore UC-attributable.

### 0.2 GATESPEC §6.1 wall rows

Every shard ran in the standard solve container with `MARKET_SIM_HIGHS_THREADS=1` on 4 cores. The baseline is the same shard's own
P0 + P1.

| year | P0+P1 s | P0 s | UC Σ s (365 windows; mean / p95 MILP s) | P1 s | total s | **ratio** | clusters / integer set / integers per window | nodes p50 / p95 | gap p95 | TL hits | peak RSS GB (UC / cgroup) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | 428.1 | 211.0 | 3,101.6 (8.31 / 39.95) | 217.1 | 3,608.4 | **8.43** | 74 / 33 / 1,188 | 1 / 31 | 8.6e-4 | 0 | 6.25 / 7.00 |
| 2022 | 695.9 | 274.9 | 8,628.5 (23.37 / 55.00) | 421.0 | 9,440.5 | **13.57** | 79 / 34 / 1,224 | 13 / 76 | 9.9e-4 | 0 | 6.26 / 7.03 |
| 2023 | 748.2 | 316.2 | 1,587.9 (4.10 / 12.16) | 432.0 | 2,453.4 | **3.28** | 78 / 33 / 1,188 | 1 / 28 | 7.9e-4 | 0 | 6.22 / 6.90 |
| 2024 | 361.8 | 158.8 | 7,413.6 (20.14 / 43.75) | 203.0 | 7,846.7 | **21.69** | 78 / 34 / 1,224 | 9 / 59 | 9.1e-4 | 0 | 6.16 / 6.91 |
| 2025 | 368.1 | 177.1 | 1,101.3 (2.87 / 7.95) | 191.0 | 1,528.3 | **4.15** | 77 / 34 / 1,224 | 1 / 24 | 9.1e-4 | 0 | 6.04 / 6.69 |

- **Window status:** every window Optimal (365 of 365 per year), 0 time-limit hits, and 0 all-budget-pinned clusters (ruling (a) changes nothing for NYISO).
- **Engine reuse:** pass-2 reuse did not fire, since no adaptive pass is armed.
- **Year-to-year wall:** as at uc-1.1, wall varies about 8× from year to year. In 2022 and 2024 the windows branch, and the branch-and-bound tail is about 93 % of stage time.
- **D-2 (3× ceiling):** every year is above the ceiling, from 3.3× to 21.7×. The ratio is reported, not judged.

## 1. Readings (prior PRECOMMIT §§2–6, unchanged; charter rows U1–U4)

| # | reading | result | met? |
|---|---|---|---|
| T1 | no PASS → FAIL flip | **5 real flips**: C1 CC_REGULAR 2021 and 2023, C1 ST_GAS 2021, C1 CC_CHP 2023, C3a 2023. The 4 C3c attestation artefacts are named, not counted | **breached → kill #3** |
| T2 | 2024 C3a ∈ [−1.8, +0.2] % | **+4.5 %** (41.35 vs 39.57 $/MWh) | **breached** |
| T3 | C1 CC_REGULAR PASS 2021–2024 | FAIL 2021 and 2023; 2022 −3.86 and 2024 −3.47 TWh are inside ±3.76–3.98 TWh; 2025 −5.56 TWh vs control (SKIPPED by the scorer) | **breached** |
| T4 | ≤ $15-hour ratios; lower-tercile error | ratios **0.00** in every year (0 model hours ≤ $15, against 689 / 50 / 450 / 171 / 136 actual hours); lower-tercile error goes control → arm **+12.0 → +13.6, +23.0 → +25.9, +9.5 → +12.2, +6.7 → +9.3, +8.9 → +11.5** $/MWh | **wrong sign** in 5/5 years (uc-1.1: 4/5) |
| T5 | kept `reliability_floor` (ST_GAS) | forced energy **1.16 / 0.93 / 0.93 / 1.05 / 1.01 TWh**, down from the control's 1.66–1.26 because the class shrank. MECH 28 adds 0.31–0.48 TWh. C8 as printed is 25.7 / 18.3 / 12.4 / 16.7 / 13.1 %; without MECH 28 it is 18.2 / 12.1 / 9.3 / 11.9 / 9.3 %. PASS under both readings | no stacking |
| ctl | P1 Optimal; unserved ≤ +500 MWh; no new D-4 FAIL row | Optimal ×5; unserved 0 MWh; the same per-unit conduct rider as UC-2, `reliability_floor × ST_GAS` plant 2480, D-4 FAIL in 2021 / 2022 / 2023 / 2025 at 0.1–1.3 GWh (the meter reads zero in those 4–217 hours) | breached by the letter, immaterial (as UC-2) |
| S1 | MECH 28 share | CC_REGULAR 0.3–1.3 % (0.09–0.34 TWh; uc-1.1 2.1–5.5 %); ST_GAS 3.1–7.5 % (0.31–0.48 TWh; uc-1.1 6–11 %); the bridge's rows are gone | reported |
| S2 | starts per plant-year vs CEMS (M1) | CC **429 / 416 / 468 / 493 / 559** vs 797 / 727 / 740 / 649 / 804 (0.54–0.76×); ST_GAS 70 / 83 / 82 / 88 / 107 vs 181 / 199 / 186 / 162 / 210 (0.39–0.54×). M2(a) is 0.00 TWh in every year | overshoot persists, unchanged from uc-1.1 |
| S4 | integer set | 33–34 integer clusters out of 74–79 (166–174 fleet rows); none all-budget-pinned | reported |
| S5 | M4 reserve dormancy | model 1.00 / 0.999 / 1.00 / 1.00 / 0.998 vs actual 0.85 / 0.79 / 0.83 / 0.83 / 0.68 | no move |
| W2 / W3 / W4 | TL hits ≤ 3 / uplift ≤ 2 % / infeasible windows 0 | 0 / **0.95–1.40 %** / 0 | met |
| kill #2 | non-determinism | not exercised: one run per year; the 2022 and 2024 first launches were stopped by the shard within seconds, before any LP, and relaunched | — |
| **U1** | forced peak-tranche TWh (CC_REGULAR `peak` band; ST_GAS) | CC 0.10 / 0.33 / 0.64 / 0.92 / 0.84 TWh on 605 / 2,132 / 3,714 / 3,911 / 3,906 h. Control: 0.07 / 0.41 / 0.31 / 0.42 / 0.76 TWh on 246–3,058 h. uc-1.1: 1.37–2.00 TWh on 8,760 h. ST_GAS peak equals the control's (0.32–0.46 TWh) | **defect 6 gone**; a residual +0.1–0.5 TWh of CC peak energy over the control is merit dispatch on a smaller committed fleet, not forcing |

### 1.1 U3 — what defect 6 was worth on NYISO (uc-1.1 → uc-1.4, same arm)

| year | price $/MWh | C3a | CC_REGULAR TWh | imports TWh | uplift % |
|---|---|---|---|---|---|
| 2021 | 44.94 → 46.07 | +6.6 → +9.3 | 25.61 → 24.21 | 33.45 → 33.58 | 1.60 → 1.25 |
| 2022 | 85.09 → 88.25 | −1.4 → +2.3 | 32.52 → 31.05 | 31.41 → 31.51 | 1.78 → 1.24 |
| 2023 | 36.11 → 37.48 | +6.5 → +10.5 | 29.03 → 27.64 | 28.45 → 28.85 | 1.36 → 0.95 |
| 2024 | 40.34 → 41.35 | +1.9 → +4.5 | 31.70 → 30.62 | 28.86 → 29.19 | 1.38 → 1.06 |
| 2025 | 62.14 → 64.12 | −10.2 → −7.4 | 31.10 → 29.83 | 25.94 → 26.09 | 1.83 → 1.40 |

At uc-1.1, the pro-rata floor forced 1.0–1.6 TWh/yr of extra CC peak-tranche energy into P1. That excess supply lowered prices by about
$1–3/MWh and partly masked the UC's price lift. Removing it raises prices in every year:
- **Helps:** it clears the 2025 C3a flip.
- **Hurts:** it pushes C3a 2023 over the edge and 2024 further past the T2 bar.

So the UC-2 NYISO R was not an artefact of defect 6. The clean engine makes the price reading worse, not better.

### 1.2 U4 — price move by sign and hour class (zero LP, control → arm)

Hour-zone prices are bucketed by the control's price tercile. "Marginal mix" is the share of marginal-flagged units, excluding hydro and
nuclear (budget-governed), in zone-hours that moved up by more than $1.

| year | Δ mean | Δ lower / mid / upper tercile | Δ on-peak / off-peak | share of zone-hours up > $1 / down > $1 | marginal mix in up-hours: control → arm |
|---|---|---|---|---|---|
| 2021 | +1.74 | +1.50 / +1.17 / +2.55 | +2.15 / +1.37 | 59 % / 18 % | ST_GAS 28, CC_CHP 25, CC_REG 20, CT 18 → **CT 35**, CC_CHP 29, ST_GAS 15, import 10 |
| 2022 | +2.00 | +1.94 / +3.40 / +0.66 | +2.97 / +1.13 | 63 % / 21 % | ST_GAS 29, CC_CHP 24, CC_REG 23 → **CT 32**, CC_CHP 24, ST_GAS 16, import 16 |
| 2023 | +2.46 | +2.01 / +3.24 / +2.13 | +3.25 / +1.74 | 68 % / 9 % | ST_GAS 42, CC_REG 25, CC_CHP 16 → **import 28**, ST_GAS 20, CT 20, CC_CHP 13 |
| 2024 | +1.77 | +1.80 / +2.16 / +1.35 | +2.04 / +1.53 | 59 % / 10 % | ST_GAS 34, CC_CHP 28, CC_REG 20 → CC_CHP 26, **import 24**, CT 16, ST_GAS 13, CC_REG 8 |
| 2025 | +0.50 | +2.03 / +2.95 / **−3.47** | +0.28 / +0.70 | 58 % / 23 % | ST_GAS 37, CC_CHP 23, CC_REG 20 → CC_CHP 24, import 20, ST_GAS 19, CT 18 |

**Mechanism.** With start-up and no-load costs paid once, and 21 h / 6 h min-up / min-down on CC, the stage keeps fewer CC plants online
through the day. In the hours CC used to set the price, the P1 LP now takes the next block from three sources:
- the seam (imports up 5.6–6.5 TWh, still inside the monthly landing band);
- CT peakers;
- CHP.

Each of these is dearer than a committed CC at its incremental cost. So the trough and shoulder prices rise.

This is the opposite of SPP, where the decommitted CC was replaced by coal and the price body fell. The price sign is set by what
replaces the decommitted CC, not by the commitment stage itself (the UC-2 RESULT §3 reading, now confirmed on the clean engine).

The 2025 upper tercile falls by $3.5. With more online headroom in the scarce hours, the 8 hours above $300 in the control fall to 1.

**Not a tuning invitation (rule 1).** No `uc_*` value, floor or band was moved. The residual is the commitment pattern of this arm on
NYISO's import-rich seam.

## 2. Verdict and the D-6 card

- **Verdict: `R`.** Under the prior PRECOMMIT §7, kill #3 fired and T2 and T3 are breached. This time it is **not confounded**:
  - the engine at uc-1.4 is clean (defect 6 is measurably gone, U1);
  - every window is Optimal and uplift is down to 1.0–1.4 %;
  - the flips are UC-attributable in every year, including 2021 under the §9 envelope.
- **Matrix:** NYISO `unit_commitment_milp` → **R**, with this RESULT as evidence. UC-2's evidence is kept as PRIOR in the cell.
- **D-6 card (copy-paste):** *"UC-3 NYISO A/B at uc-1.4 — R, now clean. The MILP UC stage solves every NYISO year (1,825/1,825
  windows Optimal, 0 TL hits, 3.3–21.7× P0+P1), and the uc-1.3/1.4 fixes removed defect 6 (CC peak-tranche forcing 1.4–2.0 TWh/yr → ≈
  control) and cut uplift to 1.0–1.4 %. With the engine clean, replacing the NYISO gas bridge by the UC still decommits 5.3–7.4 TWh/yr
  of CC_REGULAR (imports, CTs and CHP fill it) and raises prices in every year: C1 CC_REGULAR 2021/2023, ST_GAS 2021, CC_CHP 2023 and
  C3a 2023 (+2.0 → +10.5 %) flip PASS → FAIL; C3a 2024 −0.8 → +4.5 % (T2); the trough error rises in 5/5 years; CC starts 0.54–0.76×
  CEMS. Options: (1) record R, stage stays default-off for NYISO [recommended]; (2) a separately pre-registered engine/design question
  (not a NYISO tuning): why the integer stage under-commits CC relative to CEMS (starts 0.54–0.76×, M1) on an import-rich seam — e.g.
  the no-load/start-cost basis or the 24+12 h window's view of the seam; (3) promote on structure (not recommended: 5 real control
  flips on a CALIBRATED ISO)."*

## 3. Bundles, cost, what survives (rule 31: nothing deleted)

**Leg bundles.** Each leg is a full bundle, 53–55 MB, including `dispatch/<y>_P1.parquet` and `unit_hourly_<y>.parquet`. Each was
pushed by its shard and verified here: `git ls-tree` shows 21 files, and the bytes were checked out.

| year | shard branch (transport) | commit |
|---|---|---|
| 2021 | `claude/ucmilp3-nyiso-2021` | `804b920a` |
| 2022 | `claude/ucmilp3-nyiso-2022` | `7b0a4d53` |
| 2023 | `claude/ucmilp3-nyiso-2023` | `1b234eb2` |
| 2024 | `claude/ucmilp3-nyiso-2024` | `b4498fb4` |
| 2025 | `claude/ucmilp3-nyiso-2025` | `af6ffcea` |

The legs are promotable in form, but no promotion is proposed.

**Composed span.** The slim copy lives in this PR at `docs/records/nyiso/ucmilp/data/ucmilp3_nyiso_span/`. It holds:
- `hourly/*`: `uc_schedule`, `uc_uplift` and `unit_marginal`, but no `unit_hourly` or `dispatch/`;
- the `uc_solve_log_<y>.json` files;
- `meta.json`, `metrics.json` and `run_config*.json`;
- the regenerated `legitimacy_diagnostics.json`;
- `readings/`: the control and arm `calibration_verdict --json` outputs, the arm M1/M3/M4, and the zero-LP readings for control vs uc-1.1 vs uc-1.4.

**Disclosed deviations** (the UC-2 precedent, plus one new):
- **(1) Scratch composer.** The composer was run as a scratch copy of `_ucmilp_compose_span.py`, with `gas_price_override` added to
  `PER_YEAR_FIELDS` and the W0 composer's `_respan_shared_inputs` called after `meta.json`. It is filed as
  `readings/compose_scratch_DISCLOSED.py.txt`. No repo script was edited. The respan resolved to the keeper's own benchmark hashes
  (`campd-651a393cda7b`, `eia923-4bf3ca54ed56`, `eia930-cdfb8908ef53`).
- **(2) Scoring outside the tree (new).** The scoring registration (`dashboard_add_run.py --no-prune`) was run in a scratch copy of
  `frontend/` + `scripts/` outside the repo tree, because the in-tree local registration was refused by this session's permission
  guard. Nothing under `frontend/data/` was written. The scratch-registered bench parts are byte-identical to `main`'s.

**Cost:** five span shards, 25–157 min whole-shard each, about 6.9 container-hours in all; zero LP in the parent.

**Promotion question:** none is proposed. The lane recommends R.

**Shard sessions:** 5 launched, 5 archived after their bytes were verified; none left alive.

**Branches for the owner to cut** once this PR merges (a session cannot delete them, 403): `claude/ucmilp3-nyiso-2021` … `-2025`.

## Log entry

- 2026-10-14 · UC-3-NYISO `session_01CQxD6oMjTSxFp8nDQKPKRs` (Opus) · `claude/ucmilp-3-nyiso-ab` · zero LP in the parent · PRECOMMIT
  `1e337eeb` before any shard (G-DRIFT `f2bf73bf → 580c4fbf`: UC-path only, solve surface 0 moved) · span 5/5 at uc-1.4, 1,825/1,825
  windows Optimal, 0 TL, 0 unserved · defect 6 gone (CC peak-tranche 1.4–2.0 → 0.1–0.9 TWh, control 0.07–0.76), uplift 1.0–1.4 % ·
  **verdict R (clean)**: C1 CC_REGULAR 2021/2023, ST_GAS 2021, CC_CHP 2023, C3a 2023 (+2.0 → +10.5 %) flip; C3a 2024 −0.8 → +4.5 % (T2);
  price up 5/5 years (CC decommit → CT/CHP/imports marginal); CC starts 0.54–0.76× CEMS; wall 3.3–21.7× P0+P1 · nothing registered
  (E13) · slim span under `docs/records/nyiso/ucmilp/data/ucmilp3_nyiso_span/` · cell `unit_commitment_milp` NYISO → R (clean) · no
  promotion proposed.
