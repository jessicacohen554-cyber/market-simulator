# RESULT — UC-4-NYISO: arm U4 (UC + DA-forecast commitment demand + per-unit ut_h/mlf + reserve co-opt u-gate), all five NYISO years — **R**

**Lane:** UC-4-NYISO · **Session:** `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · **Dates:** 2026-10-15/16 · **Branch:**
`claude/ucmilp-4-nyiso` · **PRECOMMIT:** `PRECOMMIT-ucmilp4-nyiso-u4-2026-10-15.md`:
- the base PRECOMMIT was pushed at `e7e12823`;
- Addendum A (FIX-8 pin) at `4d48fd67`;
- Addendum B (uc-1.8 pin, 8.8 GiB gate) at `14e862bf`;
- each was pushed before the shards it governs.

**Charter:** UC-DESK r14. **Engines (mixed span, recorded per year):**
- 2021–22 on uc-1.7 + FIX-8, pin `7c93273e`;
- 2023–25 on uc-1.8, pin `41cd55dc`.

PRECOMMIT B.1 classifies FIX-9 as a solver-search change only: same formulation, same 1e-3 gap, same 600 s time limit. **LP in this session:** zero. **Registered:** nothing; the scoring registration was a local probe, moved out of the tree.

## 0. Headline

**R. Kill #3 fires (2 real control flips), and T2 is breached.** The engine is clean:
- 1,825 of 1,825 windows Optimal and 0 time-limit hits;
- 0 MWh unserved;
- uplift 0.92–1.31 %.

Against the uc-1.5 arm (UC-3 Addendum A), the r13/r14 mechanisms change the shape of the miss but do not close it:
- **The DA forecast lowers commitment demand.** It is 0.32–0.43 GW below actual on average, and 0.30–1.04 GW below at the 100 highest-load hours. This matched PRECOMMIT §1.1 exactly in every year.
- **The UC commits less CC.** CC_REGULAR is −3.3 to −4.6 TWh/yr vs the control and −0.7 to −1.8 TWh vs uc-1.5, with CC starts 0.44–0.54× CEMS (uc-1.5: 0.52–0.62×).
- **Imports, CT and CHP fill the gap** (imports +5.3 to +6.4 TWh/yr). Price ends up close to control on average (Δ −1.2 to +1.2 $/MWh), but a CT/import margin raises it in mid-tercile and on-peak hours.
- **Per-unit `mlf` moves the ST_GAS floor.** The UC's own min-load row (MECH 28) now does what the kept `reliability_floor` used to do: `reliability_floor` ST_GAS falls from 15–22 % to 0.4–0.9 % of class energy, and `uc_schedule` carries 19.6–33.2 %. This is not a stack (rule 19): one mechanism replaced the other.
- **ST_GAS starts are unchanged:** 0.37–0.56× CEMS, against 0.35–0.54× at uc-1.5. Per-unit `ut_h` did not lift cycling toward CEMS.

| reading | result | met? |
|---|---|---|
| T1 no PASS→FAIL flip | **C1 ST_GAS 2021** (−3.44 → −4.43 TWh) and **C1 CC_CHP 2023** (share +2.4 → +3.3 pp). Both are the same flips uc-1.5 had. C8 ST_GAS 2021 (33.8 %) is MECH 28 alone, 0.6 % without it, so not counted under the two-reading rule. C3c 2022–25 FAIL\* are attestation artefacts. | **breached → kill #3** |
| T2 2024 C3a ∈ [−1.8, +0.2] % | **+2.8 %** (uc-1.5: −1.5 %) | **breached** |
| T3 C1 CC_REGULAR PASS 2021–24 | −3.31 / −2.49 / −2.72 / −2.22 TWh, all inside ±3.76–3.98 TWh | met |
| ctl | P1 Optimal ×5; unserved 0 MWh every year (bar ≤ 500); D-4 shows only the named rider (`reliability_floor × ST_GAS` plant 2480; 5 rows vs the control's 9) | met |
| W2–W4 | 0 TL; uplift 0.92–1.31 % (≤ 2 %); 0 infeasible windows | met |

The determination over 2021–25 is control CALIBRATED → U4 NOT-YET. **Verdict `R`** under PRECOMMIT §6.

## 1. Gate table — control (keeper `2026-10-02-w0-nyiso`) → uc-1.5 (UC-3 A) → **U4**

| year | engine | C1 CC_REGULAR (TWh vs actual) | C1 ST_GAS | C1 CC_CHP share | C3a | C3b | C3c (h > $300; RT) | C4 gas r | C8 ST_GAS as printed / w/o MECH 28 | unserved | uplift % ($M) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | 1.7 | +1.31 / −1.83 / **−3.31** P | −3.44 / −4.81 F / **−4.43 F** | +1.1 / +1.1 / +1.4 pp | +4.3 / +2.0 / **+5.1 %** | .117 / .109 / .122 | 0 / 0 / 0 (3) P | .918 / .928 / .929 | 22.1 / 30.2 / **33.8 % → 0.6 %** | 0 | 1.31 (88.0) |
| 2022 | 1.7 | +1.24 / −0.83 / **−2.49** | −2.19 / −3.79 / **−3.35** | +2.0 / +2.0 / +2.4 pp | −0.7 / −3.8 / **−0.1 %** | .149 / .166 / .167 | 5 / 5 / 6 (101) CAV / F\* / F\* | .826 / .829 / .835 | 14.9 / 22.9 / 25.6 % → 0.5 % | 0 | 1.13 (149.2) |
| 2023 | 1.8 | +0.61 / −2.04 / **−2.72** | +1.34 / −1.66 / **−1.48** | +2.4 / +3.2 F / **+3.3 pp F** | +2.0 / +4.3 / **+6.5 %** | .129 / .157 / .164 | 0 / 0 / 1 (10) CAV / F\* / F\* | .919 / .921 / .921 | 11.3 / 16.4 / 20.0 % → 0.4 % | 0 | 0.96 (51.2) |
| 2024 | 1.8 | +2.02 / −0.40 / **−2.22** | −0.51 / −3.09 / **−2.63** | +1.0 / +1.3 / +1.7 pp | −0.8 / −1.5 / **+2.8 % (T2)** | .118 / .143 / .173 | 0 / 0 / 0 (13) CAV / F\* / F\* | .890 / .887 / .886 | 13.6 / 20.7 / 23.4 % → 0.9 % | 0 | 0.92 (56.2) |
| 2025 | 1.8 | (C1 skipped: preliminary EIA-923) | — | — | −7.7 / −12.6 F / **−10.0 % P** (edge) | .148 / .190 / .175 | 8 / 0 / 6 (42) CAV / F\* / F\* | .841 / .839 / .838 | 11.8 / 17.0 / 20.9 % → 0.9 % | 0 | 1.26 (118.7) |

\* The C3c FAIL is the probe's unattested governance gate (C6). The model-hour magnitudes are near the control's; this is named, not counted.

### 1.1 Energy, price and the structure readings (zero LP, committed sidecars)

| year | CC_REGULAR TWh ctl / uc-1.5 / U4 | ST_GAS | imports | CT_PEAKER ctl → U4 | LW price $/MWh ctl → U4 (Δ terc low/mid/up) | marginal in up-hours (U4) | lower-tercile err (ctl / uc-1.5 / U4) |
|---|---|---|---|---|---|---|---|
| 2021 | 31.63 / 28.49 / 27.02 | 5.87 / 4.50 / 4.87 | 27.48 / 33.29 / 33.34 | 3.32 → 3.58 | 43.95 → 44.32 (+0.3 / −0.6 / +0.2) | CT 45, CHP 17, import 15 | +12.0 / 11.4 / **12.2** |
| 2022 | 36.35 / 34.12 / 32.47 | 6.99 / 5.27 / 5.69 | 25.88 / 31.30 / 31.43 | 2.40 → 2.79 | 85.70 → 86.16 (+0.5 / +1.2 / −1.5) | CT 43, import 20, CHP 15 | +23.0 / 21.1 / **24.4** |
| 2023 | 33.67 / 31.03 / 30.34 | 9.67 / 6.66 / 6.85 | 23.12 / 28.26 / 28.41 | 0.47 → 0.69 | 34.59 → 36.14 (+0.9 / +1.7 / +1.1) | import 30, CT 26, CHP 13 | +9.5 / 10.3 / **10.7** |
| 2024 | 36.11 / 33.69 / 31.88 | 9.51 / 6.93 / 7.39 | 23.15 / 28.41 / 28.83 | 0.56 → 0.81 | 39.27 → 40.66 (+0.7 / +1.4 / +1.0) | import 27, CT 24, CHP 18 | +6.7 / 7.0 / **8.2** |
| 2025 | 35.39 / 32.70 / 31.57 | 10.25 / 8.06 / 8.32 | 19.59 / 25.84 / 25.96 | 1.31 → 1.13 | 63.90 → 62.33 (+0.3 / +1.6 / **−5.3**) | CT 25, import 25, CHP 21 | +8.9 / 8.4 / **9.3** |

**Starts ÷ CEMS** (M1, same probe as UC-3):

| year | CC_REGULAR U4 (uc-1.5) | ST_GAS U4 (uc-1.5) |
|---|---|---|
| 2021 | 390/797 = 0.49 (0.58) | 67/181 = 0.37 (0.35) |
| 2022 | 351/727 = 0.48 (0.52) | 87/199 = 0.44 (0.40) |
| 2023 | 397/740 = 0.54 (0.62) | 80/186 = 0.43 (0.45) |
| 2024 | 300/649 = 0.46 (0.62) | 91/162 = 0.56 (0.54) |
| 2025 | 356/804 = 0.44 (0.61) | 103/210 = 0.49 (0.48) |

M2(a) is 0.00 TWh every year.

**Commitment demand** (`uc_solve_log`; da_forecast, eia930_da_forecast):

| year | mean increment (MW) | top-100 median (MW) | QA-dropped hours |
|---|---|---|---|
| 2021 | −412 | −1,040 | 0 |
| 2022 | −399 | −649 | 0 |
| 2023 | −324 | −638 | 0 |
| 2024 | −430 | −297 | 49 |
| 2025 | −379 | −836 | 48 |

All five match PRECOMMIT §1.1, which was declared before any shard.

**D-2 by mechanism** (U4): ST_GAS `uc_schedule` takes 33.2 / 25.0 / 19.6 / 22.5 / 20.1 %, and `reliability_floor` 0.6 / 0.5 / 0.4 / 0.9 / 0.9 %. CC_REGULAR `uc_schedule` takes 10.7 / 8.4 / 4.4 / 7.9 / 10.8 %.

**Mechanism read** (not a tuning invitation, rule 1). NYISO's BA day-ahead forecast is below actual load in 84–89 % of hours. Committing against it means less CC is online at peak, a smaller share than uc-1.5 and the control. The P1 LP then fills the gap with imports, CTs and CHP, which set the price in the hours that rise. Mid-tercile and on-peak prices go up, so 2024 C3a moves +2.8 % (T2) and the lower-tercile error is worse than both the control and uc-1.5 in 5 of 5 years.

In 2025 the extra online headroom in scarce hours lowers the upper tercile by $5.3. That brings C3a from uc-1.5's −12.6 % FAIL to −10.0 %, a PASS right at the edge of the band. The C1 CC_CHP 2023 share flip and the C1 ST_GAS 2021 energy flip are the same rows uc-1.5 failed.

The r13/r14 package does not fix the NYISO residual: CC and ST_GAS cycle too little, and imports take 5–6 TWh/yr. It moves price slightly up in the middle of the distribution.

## 2. Engine, wall and memory (GATESPEC §6.1; baseline = the shard's own P0 + P1)

| year | engine | P0+P1 s | UC Σ s (mean / p95 MILP s) | total s | **ratio** | clusters / integer / per window | nodes p50 / p95 | TL | memory peak cgroup / VmHWM / swap GiB |
|---|---|---|---|---|---|---|---|---|---|
| 2021 | uc-1.7 | 419.6 | 6,235 (16.9 / 42.4) | 6,735 | **16.0** | 74 / 33 / 1,188 | 9 / 52 | 0 | 7.00 / 6.72 / 0 |
| 2022 | uc-1.7 | 340.5 | 7,153 (19.4 / 37.8) | 7,561 | **22.2** | 79 / 34 / 1,224 | 20 / 93 | 0 | 6.95 / 6.73 / 0 |
| 2023 | uc-1.8 | 297.5 | 6,008 (16.3 / 54.3) | 6,360 | **21.4** | 78 / 33 / 1,188 | 1 / 33 | 0 | 6.98 / 6.76 / 0 |
| 2024 | uc-1.8 | 358.2 | 15,065 (41.1 / 84.5) | 15,496 | **43.3** | 78 / 34 / 1,224 | 12 / 89 | 0 | 7.03 / 6.72 / 0 |
| 2025 | uc-1.8 | 462.9 | 11,922 (32.5 / 67.9) | 12,480 | **27.0** | 77 / 34 / 1,224 | 5 / 64 | 0 | 7.26 / 6.71 / 0 |

- Across all five years: 1,825 of 1,825 windows Optimal, 0 all-budget-pinned clusters, and pass-2 reuse never fired.
- **The UC stage is 3–12× slower than uc-1.5's** (2,004 / 5,879 / 1,215 / 6,719 / 1,302 s). That is the uc-1.6 reserve u-gate, which NYISO arms because it co-optimises reserves.
- **FIX-9 did not recover the time on 2024–25.** uc-1.8 2024 averages 41 s per window, against uc-1.7 2021–22's 17–19 s on the same windows. A same-year uc-1.7 vs uc-1.8 comparison was not run (§8: no repeat solve).
- The D-2 3× wall ceiling is exceeded every year; this is reported, not judged.
- **Memory:** the measured peak is ≤ 7.26 GiB with no swap ever touched. Under the owner's 1.25× rule this supports the 8.8 GiB NYISO gate.

## 3. Bundles, cost, what survives (rule 31: nothing deleted)

| year | engine | branch (transport) | commit | verified |
|---|---|---|---|---|
| 2021 | uc-1.7 | `claude/ucmilp4b-nyiso-2021` | `86f82682` | 21 files incl. `dispatch/2021_P1`; bytes in hand |
| 2022 | uc-1.7 | `claude/ucmilp4b-nyiso-2022` | `1e9fc3f7` | 21 files; bytes in hand |
| 2023 | uc-1.8 | `claude/ucmilp4c-nyiso-2023` | `32e82ae6` | 21 files; bytes in hand |
| 2024 | uc-1.8 | `claude/ucmilp4c-nyiso-2024` | `d7328ae0` | 21 files; bytes in hand |
| 2025 | uc-1.8 | `claude/ucmilp4c-nyiso-2025` | `0cf22831` | 21 files; bytes in hand |

- **Slim span** in this PR at `docs/records/nyiso/ucmilp/data/ucmilp4_nyiso_span/`:
  - the hourly sidecars, including `uc_schedule`, `uc_uplift` and `unit_marginal` (no `unit_hourly` or `dispatch/`);
  - `uc_solve_log_<y>.json`, `meta`, `metrics`, `run_config*` and the regenerated `legitimacy_diagnostics.json`;
  - `readings/`: control and arm `calibration_verdict --json`, M1/M3/M4, zero-LP readings, and the interim 2021–22 verdict.
- **Disclosed deviations** (the UC-3 precedent):
  1. **Scratch composer:** a copy of `_ucmilp_compose_span.py` with `gas_price_override` in `PER_YEAR_FIELDS` plus the W0 respan. It is filed under `readings/`.
  2. **Probe scoring:** done by a local `dashboard_add_run --no-prune`. Its two `frontend/` files were moved out of the tree, and its bench parts are byte-identical to `main`'s.
  3. **Prompt quoting:** `--set uc_commitment_demand_source='"da_forecast"'` was shell-quoted in the emitted prompts, because `shard_prompt.py` passes `--set` values through verbatim.
- **Cost:** 5 solved legs at 106–258 min whole-shard each, about 12.9 container-hours. Another 13 shards stopped at preflight (memory gate or kill #1), costing about 10 min each.
- **Shards:** 18 launched, 18 archived, none alive.
- **Promotion:** none proposed.
- **Branches to cut** after this PR merges: `claude/ucmilp4b-nyiso-2021`, `-2022`, `claude/ucmilp4c-nyiso-2023`, `-2024`, `-2025`, and `claude/ucmilp-4-nyiso`.

## 4. Matrix

NYISO `unit_commitment_milp` stays **R**, with the U4 evidence added. NYISO `uc_commitment_demand_source` goes **U → R** with this RESULT as evidence: arming it on NYISO lowers commitment at peak and does not leave the control calibrated.

## Log entry

- 2026-10-16 · UC-4-NYISO `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · `claude/ucmilp-4-nyiso` · zero LP in the parent · PRECOMMIT `e7e12823` with addenda A (`4d48fd67`, FIX-8) and B (`14e862bf`, uc-1.8, 8.8 GiB gate), each before its shards.
- Span 5/5: 2021–22 on uc-1.7, 2023–25 on uc-1.8. 1,825/1,825 Optimal, 0 TL, 0 unserved, uplift 0.92–1.31 %.
- **R**: C1 ST_GAS 2021 and C1 CC_CHP 2023 flip; T2 2024 C3a +2.8 %; T3 met. The DA forecast is −0.3…−1.0 GW at peak; CC −3.3…−4.6 TWh/yr vs control; imports +5.3…+6.4 TWh; starts 0.44–0.54× (CC) and 0.37–0.56× (ST_GAS) CEMS. MECH 28 replaces `reliability_floor` for ST_GAS.
- Wall 16–43× P0+P1; memory ≤ 7.26 GiB, no swap.
- Nothing registered. Cells: `unit_commitment_milp` R (unchanged), `uc_commitment_demand_source` U → R.

---

## (Appendix — interim record, superseded by the headline above) UC-4-NYISO: arm U4 at engine uc-1.7 — **KILL #1 (engine defect), no leg solved, no verdict on the arm (interim, defect stop); lane OPEN, awaiting the FIX-8 pin**

**Desk ruling (UC-DESK, 2026-10-15 10:09Z):** a defect stop is not a verdict on the arm; the lane stays open, amends this PRECOMMIT with a
dated pin addendum at the FIX-8 pin and relaunches the full span. The defect stop spends no relaunches; the 2022 memory-gate block counts
as attempt 1 of 4 for 2022.

**Lane:** UC-4-NYISO · **Session:** `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · **Date:** 2026-10-15 · **Branch:** `claude/ucmilp-4-nyiso`
· **PRECOMMIT:** `PRECOMMIT-ucmilp4-nyiso-u4-2026-10-15.md` (pushed `e7e12823` before any shard) · **Charter:** UC-DESK
(`session_01WX9W5tgYMre3Z134LZoGF6`) r14 · **Pin solved:** `7dbfe20fc63a4a16e37640c2d587b93a7fdf3365` (uc-1.7) · **LP in this
session:** zero · **LP in any shard:** zero · **Registered:** nothing (E13).

## 0. Headline

The first leg to reach the UC stage (2021) stopped before any LP, inside the UC stage's preparation:

```
File "src/market_sim/pipeline/uc.py", line 493, in __init__  self.commit: CommitmentDemand = commitment_demand(config, demand)
File "src/market_sim/data/commitment_demand.py", line 254, in commitment_demand  raise ValueError(
ValueError: commitment increment has 5 zones, demand 7
```

PRECOMMIT §5 kill #1 (an exception inside the UC stage is an engine defect): the lane stops, routes the defect to UC-DESK and patches
nothing. **No year was solved, so U4 gets no verdict.** Per UC-DESK, a defect stop stamps no matrix cell: both NYISO cells stay as on
`main` until the final RESULT.

## 1. The defect (zero-LP reading, `7dbfe20f`)

- **The increment.** `commitment_demand()` builds the backcast increment with `backcast_commitment_increment(iso, year,
  get_iso_config(iso))`. That call goes through `eia930.load_zone_weights`, which weights by the ISO's **load zones**. For NYISO those are
  the 5 zones `Upstate_West, Capital_Hudson, Lower_Hudson, NYC, Long_Island`.
- **The demand.** The P1 demand matrix the increment is added to has **7** rows, because it also carries the interchange
  pseudo-zones the NYISO recipe builds (`model/interchange/spec.py::IMPORT_ZONE["NYISO"] = "NYISO_external"`, plus a seam zone).
- **The shape check.** `commitment_demand.py:251–254` compares the two row counts and raises.
- **Scope.**
  - The failure is deterministic for every NYISO year: the zones come from the recipe, not from the data year.
  - UC-1-FIX-7's repro covered only SPP 2020, which has no import pseudo-zone.
  - The same raise is expected in any UC-4 lane whose recipe builds an `IMPORT_ZONE` or seam zone: CAISO `WECC_import`, NEISO
    `HQ_import`, MISO `MISO_external`, PJM, NWPP. This was not tested here. UC-DESK was alerted at 10:12Z.
- **Fix shape, for the engine lane, not done here.** Map the increment onto the demand rows by zone name, with zero rows for zones that
  carry no BA load (external and seam zones). Rule 4 is not affected: P1 still clears on actual load.

The data side is sound. The NYISO EIA-930 day-ahead forecast exists for every year: 0 / 0 / 0 / 49 / 48 hours are dropped by the QA cut.
The PRECOMMIT §1.1 table stands: commitment demand is 0.32–0.43 GW lower on mean, and 0.30–1.04 GW lower at the 100 highest-load hours.

## 2. Gate table (control → U4)

| year | outcome | C1 / C3a / C3b / C3c / C4 / C8 | unserved | uplift | starts ÷ CEMS (CC / ST_GAS) | wall |
|---|---|---|---|---|---|---|
| 2021 | **kill #1** at UC-stage prep, about 3 min, no LP | not scored | — | — | — | — |
| 2022 | memory gate blocked (attempt 1); not relaunched after kill #1 | not scored | — | — | — | — |
| 2023 | shard archived before it reached the stage (halted after kill #1) | not scored | — | — | — | — |
| 2024 | shard archived before it reached the stage (halted after kill #1) | not scored | — | — | — | — |
| 2025 | not launched (halted after kill #1) | not scored | — | — | — | — |

The bars T1–T3 and ctl, the starts ÷ CEMS readings and U6 are all **not evaluable**. The control (keeper `2026-10-02-w0-nyiso`) is
unchanged and CALIBRATED.

## 3. Attempt log (memory gate ≥ 22.4 GiB = ceiling + swap)

| year | attempt | session | launched (Z) | gate | outcome |
|---|---|---|---|---|---|
| 2021 | 1 | `session_01B11znSju38dhBYiNah9YAu` | 09:51 | 13.36 + 9.0 = 22.4 GiB (15.7 GiB free disk), passed | `uc-params` rebuilt (108 clusters, 95 with a no-load fit, 3 class-fallback rows); `replay_keeper` accepted the `"da_forecast"` JSON; **kill #1** about 3 min after launch; nothing pushed |
| 2022 | 1 | `session_014xa7hMEctDfZrymaKTE3ec` | 09:56 | 13.36 + 4.0 = **17.4 GiB** (10.3 GiB free disk), blocked | stopped before any data step; nothing pushed |
| 2023 | 1 | `session_01NfAaPLMLQRpLFmqhn9ZDKD` | 10:02 | — | archived at 10:08 after kill #1 (container still pending) |
| 2024 | 1 | `session_01GWTNNtiCJWBZRLh1oKAa6Y` | 10:07 | — | archived at 10:08 after kill #1 (container still pending) |
| 2025 | — | — | — | — | not launched |

- **Archived:** all four shard sessions. None is left alive.
- **Branches:** no shard pushed one, so none needs cutting.
- **2022 relaunch budget:** the memory-gate block counts as attempt 1 of 4 (desk ruling); 3 remain for the FIX-8 relaunch. The kill-#1
  stop spends no relaunch for any year.

## 4. Disclosed deviations

**Shell quoting of the new `--set` value.** `scripts/shard_prompt.py` passes `--set` values through verbatim. A bare
`uc_commitment_demand_source="da_forecast"` would reach `replay_keeper` as `da_forecast`, which is not valid JSON. The emitted command
therefore carries `--set uc_commitment_demand_source='"da_forecast"'`, and the 2021 shard confirmed that `replay_keeper` accepted it. No
script was edited.

This is a small tooling gap for UC-DESK to note: `shard_prompt.py` does not shell-quote string-valued `--set`s.

## 5. What a relaunch needs (for UC-DESK)

1. An engine fix to `data/commitment_demand.py` (zone-name mapping), with a repro on an ISO that has an import pseudo-zone. This would
   be uc-1.8 or a patch release.
2. The PRECOMMIT then carries forward unchanged, with only the pin replaced. Its G-DRIFT would be extended over the fix commit, which
   should be LIVE on the gate-on path only.
3. Containers that pass the 22.4 GiB gate. One of the two that reached preflight did not.

## Log entry

- 2026-10-15 · UC-4-NYISO `session_01TwaDV4e3y8xUFmUnHeK2HZ` (Opus) · `claude/ucmilp-4-nyiso` · PRECOMMIT `e7e12823` before any shard
  (G-DRIFT `2dd69d5a → 7dbfe20f`: UC path only, solve surface 0 moved; DA-forecast lowers NYISO commitment demand 0.3–1.0 GW at peak) ·
  **kill #1**: `commitment_demand.py:254` "commitment increment has 5 zones, demand 7" (load zones vs P1 demand with interchange
  pseudo-zones) at UC-stage prep, 2021, before any LP · 2022 memory-gate blocked (17.4 GiB) · 2023/2024 archived, 2025 not launched ·
  0 legs solved, no verdict · nothing registered · matrix: no cell stamped (desk ruling: a defect stop is not a verdict).

## Interim B: relaunch at the FIX-8 pin `7c93273e` (PRECOMMIT Addendum A), status at 14:57Z

**FIX-8 works.** Both legs that reached the UC stage solved every window:
- 365/365 windows Optimal and 0 time-limit hits;
- 0 MWh unserved;
- the engine is uc-1.7.

The commitment-demand increments match PRECOMMIT §1.1 exactly. 2021: mean −412.5 MW, top-100 median −1,040 MW. 2022: −398.7 MW and −649 MW.

### Legs solved: verified (`git ls-tree` = 21 files incl. `dispatch/<y>_P1.parquet`; bytes in hand), then the shard archived

| year | commit (transport) | memory peak (cgroup / VmHWM / swap) GiB | wall P0+P1 / UC / total s | ratio | integer clusters / per window | nodes p50 / p95 |
|---|---|---|---|---|---|---|
| 2021 | `86f82682` `claude/ucmilp4b-nyiso-2021` | 7.00 / 6.72 / 0.00 | 419.6 / 6,235 / 6,735 | 16.0 | 33 of 74 / 1,188 | 9 / 52 |
| 2022 | `1e9fc3f7` `claude/ucmilp4b-nyiso-2022` | 6.95 / 6.73 / 0.00 | 340.5 / 7,153 / 7,561 | 22.2 | 34 of 79 / 1,224 | 20 / 93 |

### Memory gate (22.4 GiB, as printed): attempt log

Every block happened at the gate, before any data step: ceiling 13.36 GiB + 4.0 GiB swap = 17.4 GiB, with 10.3–10.9 GiB free disk at boot. Both containers that passed had 15.7 GiB free disk and reached 13.36 + 9.0 = 22.36 GiB.

| year | attempt | session | launched (Z) | outcome |
|---|---|---|---|---|
| 2022 | 1 | `session_014xa7hMEctDfZrymaKTE3ec` | 09:56 | blocked (first launch, pin `7dbfe20f`) |
| 2021 | 1 | `session_012DTFNAUvz4jizsfc2Tfgcp` | 10:40 | passed, **solved** |
| 2022 | 2 | `session_0121bGM2cpm5888aV7whcbT2` | 10:46 | passed, **solved** |
| 2023 | 1 | `session_01L4fvpDNDRh2ZL2u8iPNSY2` | 10:51 | blocked (10.8 GiB disk) |
| 2024 | 1 | `session_01VU2zTChpUQx886CLA68Ncx` | 10:57 | blocked (10.3) |
| 2025 | 1 | `session_01CPHviU3Zn2GvR38BpGaDCQ` | 11:02 | blocked (10.3) |
| 2023 | 2 | `session_012r3gJyn6Fm7gb7FkUoX3ep` | 11:33 | blocked (10.3) |
| 2024 | 2 | `session_019YqMiYbifeD7nusiXUiabv` | 11:39 | blocked (10.3) |
| 2025 | 2 | `session_01Q3mszsMCUdqGSTmAR3UioM` | 11:44 | blocked (10.6) |
| 2023 | 3 | `session_017sBa7ND8g3n5FvYvERXsdN` | 12:14 | blocked (10.9) |
| 2024 | 3 | `session_01VcDNJV8DTRYwmVAM2TFKQd` | 12:20 | blocked (10.4) |
| 2025 | 3 | `session_01M2ucjmrSNLTiwFPmnTXnS3` | 12:25 | blocked (10.3) |

**2023, 2024 and 2025 are HELD, pending the owner's gate ruling, with 3 of 4 attempts used each** (UC-DESK, 12:35Z). Their fourth attempts have not been launched, and **no coverage gap is recorded**.

NYISO's measured need, from the two solved legs and the 10 UC-3 legs:
- cgroup peak ≤ 7.03 GB;
- swap never touched.

Every shard session launched so far has been archived; none is left alive. Composition and scoring wait for the full span or for the desk.
