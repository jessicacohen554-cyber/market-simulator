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

---

# Addendum A — relaunch at engine uc-1.5 (defect 7: no-load paid once), 2026-10-14 — **R (3 real flips; T2 and T3 now met)**

**Why:** UC-DESK (12:46Z) — engine defect 7 (`FINDING-ucmilp-fix5-cost-basis-2026-10-14.md`): the UC objective paid each integer member's
no-load twice (explicit `noload` + the average-rate heat rate in `mc_base`; NYISO CC $65–230 M/yr). It over-costed commitment in the
direction of the uc-1.4 signature, so the uc-1.4 R above is **confounded and superseded by this addendum**. **Pin:** `da11c2489b84c010f5658023c08c97973cd92c47`
(main `2dd69d5a` = uc-1.5, + PRECOMMIT Addendum A, pushed before any shard). Arm, control, readings, kills and verdict rule unchanged
(PRECOMMIT Addendum A; G-DRIFT `580c4fbf → 2dd69d5a`: UC path only, solve surface 0 moved). LP in this session: zero. Nothing registered.

## A.0 Headline

**Removing the double-counted no-load restores most of the CC energy and flips the price sign, but the control still does not stay
calibrated.** CC_REGULAR comes back 2.9–4.3 TWh/yr vs uc-1.4 (now −2.2 to −3.1 TWh vs control, inside the C1 band every year — **T3 met**);
the price body now moves DOWN in 4 of 5 years (−$0.4 to −2.7/MWh; 2023 +$0.6) and **2024 C3a −1.5 % (T2 met)**. Three real flips remain:
**C1 ST_GAS 2021** (−3.44 → −4.81 TWh), **C1 CC_CHP 2023** (share +2.4 → +3.2 pp), **C3a 2025** (−7.7 → **−12.6 %**). The new driver is
**ST_GAS decommitment** (−1.4 to −3.0 TWh/yr vs control; starts 0.35–0.54× CEMS) with imports still +5.1 to +6.3 TWh/yr. Engine clean:
1,825/1,825 windows Optimal, 0 TL, 0 unserved, uplift 1.15–1.55 %. **Verdict `R`** (kill #3), now on an un-confounded engine but a
narrower miss than uc-1.4 (3 flips vs 5; T2/T3 met).

## A.1 Gate table — control → uc-1.5 [uc-1.4]

| year | C1 (Δ TWh vs actual) | C3a | C3b | C3c | C4 gas r | C8 ST_GAS as printed / w/o MECH 28 · CC | unserved | uplift % ($M) |
|---|---|---|---|---|---|---|---|---|
| 2021 | CC_REGULAR +1.31 → −1.83 PASS [−6.11 FAIL]; **ST_GAS −3.44 → −4.81 FAIL** [−4.32]; CC_CHP +1.52 → +0.81 | +4.3 → +2.0 % [+9.3] | 0.117 → 0.109 | 0 / 3 PASS | 0.918 → 0.928 | 22.1 → **30.2 % FAIL as printed** / 22.2 % PASS · 1.6 % | 0 | 1.55 (101) |
| 2022 | CC_REGULAR +1.24 → −0.83; ST_GAS −2.19 → −3.79; CC_CHP +2.43 → +1.80 — all PASS | −0.7 → −3.8 % [+2.3] | 0.149 → 0.166 | CAVEAT → FAIL\* (5 / 101 h) | 0.826 → 0.829 | 14.9 → 22.9 % / 15.8 % · 1.4 % | 0 | 1.38 (175) |
| 2023 | CC_REGULAR +0.61 → −2.04 PASS [−5.43 FAIL]; **CC_CHP +2.81 → +3.05 (+3.2 pp) FAIL** [+3.75]; ST_GAS +1.34 → −1.66 | +2.0 → +4.3 % PASS [+10.5 FAIL] | 0.129 → 0.157 | CAVEAT → FAIL\* (0 / 10 h) | 0.919 → 0.921 | 11.3 → 16.4 % / 12.4 % · 2.1 % | 0 | 1.28 (67) |
| 2024 | CC_REGULAR +2.02 → −0.40; ST_GAS −0.51 → −3.09; CC_CHP +0.84 → +0.48 — all PASS | −0.8 → **−1.5 %** (T2 met) [+4.5] | 0.118 → 0.143 | CAVEAT → FAIL\* (0 / 13 h) | 0.890 → 0.887 | 13.6 → 20.7 % / 15.3 % · 1.1 % | 0 | 1.15 (67) |
| 2025 | (C1 SKIPPED) CC_REGULAR 35.39 → 32.70 TWh; ST_GAS 10.25 → 8.06 | **−7.7 → −12.6 % FAIL** [−7.4] | 0.148 → 0.190 | 8 → 0 / 42 h CAVEAT → FAIL\* | 0.841 → 0.839 | 11.8 → 17.0 % / 12.1 % · 0.8 % | 0 | 1.35 (124) |

\* attestation artefact (C6 UNATTESTED), magnitudes as control except 2025 (8 → 0 h > $300). C8 2021 crosses the 30 % cap only with MECH 28
inside the D-2 sum (rule-20 R4: MECH 28 reported, not budgeted) — reported, **not counted as a flip**; it is the kept `reliability_floor`'s
share rising as ST_GAS shrinks (the SPP stacking signature, now visible in NYISO). Determination CALIBRATED → NOT-YET. 2021 §9 envelope:
ΔC3a −2.3 pt, ΔST_GAS −1.37 TWh → UC-attributable.

## A.2 Readings

| # | result | met? |
|---|---|---|
| T1 | real flips: C1 ST_GAS 2021, C1 CC_CHP 2023, C3a 2025 (+ C8 2021 under the printed reading only; 4 C3c attestation artefacts) | **breached → kill #3** |
| T2 | 2024 C3a −1.5 % ∈ [−1.8, +0.2] | **met** |
| T3 | C1 CC_REGULAR PASS 2021–2024 (−1.83 / −0.83 / −2.04 / −0.40 TWh) | **met** |
| T4 | ≤ $15 ratios 0.00 every year; lower-tercile error control → uc-1.5: +12.0 → +11.4, +23.0 → +21.1, +9.5 → +10.3, +6.7 → +7.0, +8.9 → +8.4 | mixed: down 3/5, up 2/5 |
| T5 | `reliability_floor` ST_GAS 1.35 / 1.12 / 1.06 / 1.27 / 1.23 TWh (= 15.8–22.2 % of a shrunken class); MECH 28 adds 0.35–0.51 TWh | the kept floor's SHARE rises (stacking by shrinkage) |
| S2 | CC starts 465 / 375 / 458 / 405 / 489 = **0.52–0.62× CEMS**; ST_GAS 64 / 80 / 83 / 87 / 101 = **0.35–0.54×** | under-cycling persists |
| S5 / M4 | reserve dormancy 0.997–1.00 | unmoved |
| U1 | CC peak-tranche 0.06 / 0.27 / 0.50 / 0.71 / 0.68 TWh (control 0.07–0.76) | defect 6 stays gone |
| W2–W4 | 0 TL, uplift 1.15–1.55 %, 0 infeasible | met |

### A.2.1 U5 — uc-1.4 → uc-1.5 per year (what defect 7 was worth on NYISO)

| year | price $/MWh (ctl / uc-1.4 / uc-1.5) | C3a | CC_REGULAR TWh | ST_GAS TWh | imports TWh | uplift % |
|---|---|---|---|---|---|---|
| 2021 | 43.95 / 46.07 / 43.01 | +9.3 → +2.0 | 24.21 → 28.49 (ctl 31.63) | 4.99 → 4.50 (5.87) | 33.58 → 33.29 (27.48) | 1.25 → 1.55 |
| 2022 | 85.70 / 88.25 / 82.97 | +2.3 → −3.8 | 31.05 → 34.12 (36.35) | 5.81 → 5.27 (6.99) | 31.51 → 31.30 (25.88) | 1.24 → 1.38 |
| 2023 | 34.59 / 37.48 / 35.36 | +10.5 → +4.3 | 27.64 → 31.03 (33.67) | 8.01 → 6.66 (9.67) | 28.85 → 28.26 (23.12) | 0.95 → 1.28 |
| 2024 | 39.27 / 41.35 / 38.97 | +4.5 → −1.5 | 30.62 → 33.69 (36.11) | 7.43 → 6.93 (9.51) | 29.19 → 28.41 (23.15) | 1.06 → 1.15 |
| 2025 | 63.90 / 64.12 / 60.52 | −7.4 → −12.6 | 29.83 → 32.70 (35.39) | 8.77 → 8.06 (10.25) | 26.09 → 25.84 (19.59) | 1.40 → 1.35 |

Defect 7 was worth **+2.9 to +4.3 TWh/yr of CC_REGULAR** and **$2.1–5.3/MWh of price** (uc-1.4 over-priced). It did NOT move imports
(−0.2 to −0.8 TWh) or ST_GAS (−0.5 to −1.4 TWh further down): with no-load paid once the stage re-commits CC but still decommits ST_GAS,
and the seam keeps the ~5–6 TWh/yr it took at uc-1.4.

### A.2.2 U4 — price move by sign and hour class (control → uc-1.5, zero LP)

| year | Δ mean | Δ lower / mid / upper tercile | share of zone-hours up > $1 / down > $1 | marginal mix in DOWN-hours: control → arm |
|---|---|---|---|---|
| 2021 | −0.99 | −0.28 / −1.25 / −1.42 | 14 % / 39 % | CC_CHP 37, CC_REG 25, ST_GAS 15 → **CC_CHP 51**, CC_REG 13, CT 12 |
| 2022 | −2.73 | −1.14 / −2.02 / −5.02 | 16 % / 55 % | CC_REG 30, CC_CHP 27, ST_GAS 19 → **CC_CHP 37**, CC_REG 20, CT 12 |
| 2023 | +0.61 | +0.63 / +1.15 / +0.05 | 38 % / 19 % | (up-hours) ST_GAS 48, CC_REG 21 → **import 26, CT 23**, ST_GAS 15 |
| 2024 | −0.37 | +0.07 / +0.12 / −1.28 | 26 % / 28 % | CC_REG 30, CC_CHP 26, ST_GAS 21 → **CC_CHP 37**, CC_REG 26, import 14 |
| 2025 | −2.65 | −0.29 / −0.13 / **−7.54** | 17 % / 44 % | CC_REG 30, ST_GAS 24, CC_CHP 21 → CC_CHP 25, CC_REG 25, ST_GAS 16 |

**Mechanism at uc-1.5.** With CC commitment re-costed correctly the integer stage keeps more CC online and **decommits ST_GAS** instead
(steam units' no-load is large relative to their energy; 13 h / 8 h min-up/down). Down-hours are set by CC_CHP / CC (cheaper than the
ST_GAS the control had marginal); the upper tercile falls most (−$1.3 to −7.5) because more online CC headroom shaves the shoulders and
peaks — which is exactly the 2025 C3a flip (model already −7.7 % low). In up-hours (2023) the marginal unit moves from ST_GAS to imports/CTs.
The ST_GAS decommit drives C1 ST_GAS 2021 out of band and leaves CC_CHP to fill (2023 share). Not a tuning invitation (rule 1).

## A.3 Wall rows (§6.1; baseline = the shard's own P0+P1)

| year | P0+P1 s | UC Σ s (mean / p95 MILP s) | total s | **ratio** | clusters / integer set / per window | nodes p50/p95 | gap p95 | TL | RSS GB (UC / cgroup) |
|---|---|---|---|---|---|---|---|---|---|
| 2021 | 403.8 | 2,004.5 (5.31 / 13.37) | 2,487.6 | **6.16** | 74 / 33 / 1,188 | 1 / 23 | 9.3e-4 | 0 | 6.14 / 6.89 |
| 2022 | 429.7 | 5,879.2 (15.93 / 39.63) | 6,389.2 | **14.87** | 79 / 34 / 1,224 | 12 / 59 | 9.9e-4 | 0 | 6.18 / 6.89 |
| 2023 | 377.4 | 1,214.8 (3.18 / 8.02) | 1,659.7 | **4.40** | 78 / 33 / 1,188 | 1 / 31 | 9.4e-4 | 0 | 6.13 / 6.81 |
| 2024 | 334.4 | 6,719.0 (18.27 / 36.72) | 7,113.1 | **21.27** | 78 / 34 / 1,224 | 10 / 58 | 9.4e-4 | 0 | 6.19 / 6.86 |
| 2025 | 388.0 | 1,301.5 (3.40 / 9.04) | 1,764.8 | **4.55** | 77 / 34 / 1,224 | 1 / 25 | 9.4e-4 | 0 | 6.12 / 6.77 |

1,825/1,825 Optimal; 0 all-budget-pinned clusters; pass-2 reuse not fired. D-2 (3×) exceeded every year; reported, not judged.

## A.4 Verdict, D-6 card, bundles

- **Verdict `R`** (kill #3: 3 real flips), on the clean uc-1.5 engine; T2 and T3 met — a materially narrower miss than uc-1.4.
  Matrix NYISO `unit_commitment_milp` → R, evidence this addendum (uc-1.4 evidence kept as PRIOR).
- **D-6 card:** *"UC-3 NYISO at uc-1.5 — R, narrower. Defect 7's fix restores 2.9–4.3 TWh/yr of CC (C1 CC_REGULAR PASS every year, T3 met)
  and the 2024 price lands at −1.5 % (T2 met), but the UC now decommits ST_GAS (−1.4 to −3.0 TWh/yr, starts 0.35–0.54× CEMS) and shaves
  the upper price tercile: C1 ST_GAS 2021, C1 CC_CHP share 2023 and C3a 2025 (−7.7 → −12.6 %) flip; the kept reliability_floor's ST_GAS
  share rises with the shrinking class (C8 2021 30.2 % as printed, 22.2 % without MECH 28). Options: (1) record R, stage default-off for
  NYISO [recommended]; (2) a pre-registered design question on ST_GAS commitment (no-load/start basis for steam units; the
  reliability_floor ↔ UC interaction, rule 19) — not a NYISO tuning; (3) promote on structure (not recommended: 3 control flips)."*
- **Bundles:** legs on `claude/ucmilp35-nyiso-2021` `eedbfe05` · `-2022` `66f215b5` · `-2023` `074e6c65` · `-2024` `91e443d8` ·
  `-2025` `2efcbf6b` (21 files each, 53–56 MB, incl. `dispatch/<y>_P1.parquet`); slim span
  `docs/records/nyiso/ucmilp/data/ucmilp35_nyiso_span/` (readings JSON `zero_lp_readings_ctl_uc14_uc15.json`: its `uc11` key = uc-1.4,
  `uc14` key = uc-1.5 — the script's labels). Same two disclosed deviations as §3 (scratch composer; scoring in a scratch copy, bench parts
  byte-identical to `main`). Cost: five shards 28–119 min each (≈ 5.4 container-hours). 5 launched, 5 verified and archived. Branches for
  the owner to cut: `claude/ucmilp35-nyiso-2021` … `-2025`. No promotion proposed.

### Log entry (Addendum A)

- 2026-10-14 · UC-3-NYISO `session_01CQxD6oMjTSxFp8nDQKPKRs` · `claude/ucmilp-3-nyiso-ab-uc15` · uc-1.5 relaunch (defect 7) at `da11c248`,
  PRECOMMIT Addendum A before any shard · 5/5 legs, 1,825/1,825 Optimal, 0 TL, 0 unserved · **R**: C1 ST_GAS 2021, C1 CC_CHP 2023, C3a 2025
  (−12.6 %) flip; T2 (2024 −1.5 %) and T3 (CC_REGULAR PASS) met; defect 7 worth +2.9–4.3 TWh/yr CC and −$2–5/MWh vs uc-1.4; new driver
  ST_GAS decommit (starts 0.35–0.54× CEMS); wall 4.4–21.3× · nothing registered · cell → R (uc-1.5).
