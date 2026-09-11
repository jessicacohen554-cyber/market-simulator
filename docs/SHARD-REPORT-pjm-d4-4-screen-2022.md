# SHARD REPORT — pjm-d4-4 stage-2 SCREEN, PJM 2022, one arm

**Shard:** `pjm-d4-4`, ONE YEAR (2022), ONE ARM.
**Arm:** `unit_outage_short_windows_gas=true` (gas sub-5-day CAMPD outage-window scope).
**Control:** the COMMITTED keeper bundle `results/calibration/pjm_d4_2_TP` (2020-2021-2022), 2022 leg.
**Arm bundle:** `results/calibration/pjm_d4_4_screen_2022` — a THROWAWAY screen probe (rule 29 clause 2).
Never registered, never committed; on local disk only, gitignored by `.gitignore:1757`
(`results/calibration/pjm_d4_*/`). NOT deleted (rule 31 `[R-RETAIN]`).
**Date:** 2026-09-10. **Pinned SHA:** `57c3557e923dfb689c80f8e0b3ea310e196ea291`.

## Hard stops (checked first, in order — all PASSED)

1. `git rev-parse HEAD` = `57c3557e923dfb689c80f8e0b3ea310e196ea291`. Never pulled, rebased or synced.
2. `grep -c unit_outage_short_windows_gas src/market_sim/config/scenarios.py` = **6** (bar: >= 6).
3. `wc -l data/raw/campd-unit-outages-shortgas-PJM.csv` = **1860** (1,859 rows + header).
4. `results/calibration/pjm_d4_2_TP/meta.json` exists; its git sha reads **`5f133fd5`**.
   NOTE for the parent's record: the key is the FLAT `meta.json["git_sha"]`, not a nested
   `git.sha` — `meta["git"]` does not exist and reads `None`. `basis_sha` =
   `5f133fd595aeb8d6c88058b566fce4b4e8b56e19`.

**Arming confirmed in the solve log:**
`INFO: short unit-outage derate (PJM 2022): 721 plant-tranches derated`. The log STRING still reads
"(< 5-day baseload-coal windows)" even with the gas scope armed — cosmetic only; the envelope census
in item 1 shows the gas rows are in. No edit was made to correct it (shard scope).

**Solve:** one invocation, `scripts/replay_keeper.py results/calibration/pjm_d4_2_TP --years 2022
--set unit_outage_short_windows_gas=true --out-dir results/calibration/pjm_d4_4_screen_2022`, exit 0.
`/usr/bin/time` does not exist in this container, so peak RSS was sampled from `ps` instead
(item 7); no script was patched to work around it.

---

## 1. S-1 — availability-envelope depth: BOTH EXPECTATIONS MET

**Method note (why not read from the bundles).** The committed control is a SLIM keeper bundle and
carries **no availability array** — only `hourly/` (class, class_band, reserve_family, storage,
system). The arm bundle DOES carry one (`hourly/unit_hourly_2022.parquet`, 27,191,040 rows, column
`cap_mw = pmax x availability`). Reading one side from a solved sidecar and the other not at all is
not a comparison, so the envelope was measured at **ZERO LP on both sides**: the keeper recipe's PJM
2022 fleet was rebuilt twice through `run_calibration.run_year(fleet_only=True)` with the field off
(control) and on (arm), and the envelope computed as `sum_g pmax_g * (1 - availability[g,t])` over
fossil-thermal `plant_group`s. Fossil-thermal registry pmax: **149,819.9 MW**.
Tail set: the **92** hours of 2022 with `rt > 200` in `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`.

| PJM fossil-thermal UNAVAILABLE MW | control | arm | arm - control | expectation | verdict |
|---|---|---|---|---|---|
| annual mean | 51,988.3 | 53,038.1 | **+1,049.8** | +1,185 +/-15 % -> [1,007.3, 1,362.8] | **INSIDE** (low end) |
| mean over the 92 `rt > 200` hours | 41,789.9 | 46,113.5 | **+4,323.6** | +4,570 +/-20 % -> [3,656.0, 5,484.0] | **INSIDE** |

Per-`plant_group` annual-mean delta — the input-layer confinement is EXACT (gas only):

| plant_group | control | arm | delta |
|---|---|---|---|
| CC_REGULAR | 15,420.6 | 16,404.6 | **+984.0** |
| CC_CHP | 205.5 | 249.5 | +44.1 |
| ST_GAS | 5,350.5 | 5,370.4 | +19.9 |
| ST_CHP | 40.1 | 41.9 | +1.8 |
| CT_PEAKER | — | — | **0.0** |
| COAL_BIT / COAL_PRB / COAL_WC / all other fossil | — | — | **0.0** |

The rule-19 disjointness claim (`< MIN_DAYS` vs `>=`, coal scope vs gas scope) holds exactly at the
input layer: no coal group and no CT_PEAKER row moves by any amount.

## 2. S-2 — confinement: every class whose annual P1 TWh moved by more than 0.001

| class | control TWh | arm TWh | delta TWh |
|---|---|---|---|
| CC_REGULAR | 323.9474 | 319.6919 | **-4.2555** |
| CT_PEAKER | 15.3324 | 17.0174 | **+1.6850** |
| COAL_BIT | 142.7099 | 143.6299 | **+0.9200** |
| VIRTUAL_DEC | -21.7187 | -21.0569 | +0.6618 |
| ST_GAS | 8.2465 | 8.6815 | +0.4350 |
| import | -22.9888 | -22.6669 | +0.3219 |
| VIRTUAL_INC | 8.7052 | 8.9191 | +0.2139 |
| COAL_PRB | 10.3463 | 10.4969 | +0.1506 |
| CC_CHP | 7.4854 | 7.3343 | -0.1511 |
| CT_CHP | 1.3519 | 1.4040 | +0.0521 |
| COAL_WC | 6.5766 | 6.6132 | +0.0366 |
| ST_CHP | 1.0979 | 1.0906 | -0.0073 |
| oil | 0.0180 | 0.0202 | +0.0022 |

Unmoved (delta 0.0000): `nuclear`, `wind`, `solar`, `hydro`, `biomass`, `OTHER`.
The derate touches gas only; the coal / import / virtual movement is re-dispatch substitution for the
4.26 TWh of CC withdrawn, not a second footprint.

## 3. S-3 — the claimed effect: **FAILED against its bar**

The three raw numbers, model thermal averaged over the **92** hours of 2022 with actual `rt > 200`:

| quantity | GW |
|---|---|
| **ARM** model thermal | **89.339** |
| **CONTROL** model thermal | **89.930** |
| **CAMPD meter** (given in the shard prompt) | **80.100** |

- control gap = 89.930 - 80.100 = **+9.830 GW**
- arm gap = 89.339 - 80.100 = **+9.239 GW**
- fall from the control gap = **0.592 GW**

**Bar: a fall of >= 2.0 GW. Measured fall 0.592 GW. S-3 FAILED.**

Companion measures (same class set):
- 26 hours `rt > 500`: control 89.185 -> arm **88.146** GW, delta **-1.039 GW** (against the parent's
  stated +11.1 GW gap, implying a meter of ~78.09 GW, the new gap is ~+10.06 GW).
- all 8,760 hours: control 59.031 -> arm **58.902** GW, delta **-0.129 GW**.
- The effect IS correctly tail-localised (-0.59 GW in the 92 hours, -1.04 GW in the 26 hours, vs
  -0.13 GW all-hours) — the right shape, an order of magnitude too small.

**On +9.7 vs +9.830 — which is right, and why they differ.** My +9.830 is computed from the committed
sidecars with the class set stated explicitly: `class_hourly_2022.parquet`, `pass == P1`, summing
CC_REGULAR + CC_CHP + CT_PEAKER + CT_CHP + ST_GAS + ST_CHP + COAL_BIT + COAL_PRB + COAL_WC + oil,
meaned over the 92 tail hours, minus 80.100. It is reproducible from committed artifacts.
The parent's own prompt states the control as **89.9 GW** and the meter as **80.1 GW**, whose
difference is **9.8**, not 9.7 — so the +9.7 is inconsistent with the parent's other two stated
numbers and looks like a stale or mis-carried figure rather than a different measurement.
For completeness, the class-set sensitivity (control gap / arm gap / fall):

| class set | control gap GW | arm gap GW | fall GW |
|---|---|---|---|
| full (incl. CHP + oil) — **the number above** | +9.830 | +9.239 | 0.592 |
| excluding `oil` | +9.786 | +9.186 | 0.600 |
| excluding CHP classes | +8.313 | +7.683 | 0.630 |
| excluding CHP and `oil` | +8.269 | +7.630 | 0.639 |

**No variant reproduces 9.7** (nearest is 9.786, which rounds to 9.8). More important: **the S-3
verdict is FAIL under every variant** — the largest fall any convention produces is 0.639 GW against
a 2.0 GW bar — so the discrepancy is immaterial to the outcome and is reported only so the parent can
correct its record.

## 4. S-4 — every criterion, arm and control, 2022, regressions at full magnitude

**Method note (why the criteria were re-scored, not read).** `scripts/replay_keeper.py` writes NO
`metrics.json`, and the COMMITTED control's `metrics.json` carries only run-level statuses (label /
tier / status per criterion) with **no per-year numeric values**. So both sides were scored with
`scripts/calibration_verdict.py` against the registered payload `2026-09-10-pjm-d4-2-touchpoint` and
`frontend/data/backcast/bench/PJM/2022.json.gz`, substituting for each bundle (a) its own class TWh
(applied as a delta on `gmModel`, which cancels the payload's grid-delivered basis adjustment) and
(b) its own `lmp` block **rebuilt exactly** from its `hourly/system_2022.parquet` — `p` =
load-weighted zonal mean, `d` = annual demand TWh, `pMon`/`dMon` monthly, on the same construction
the payload uses.

**Validation of that method, before any arm number is quoted:** the rebuilt control `p` reproduces
the committed payload to the cent in all 8 demand-carrying zones (AEP_Ohio 64.45, ATSI 64.93,
Central_PA 64.06, ComEd 62.63, Dominion 66.64, EMAAC 66.87, SWMAAC 68.12, West_APS 64.52;
`PJM_external` carries zero demand and keeps its payload value), and the re-scored control
reproduces the committed verdict exactly — C1 FAIL on CC_REGULAR, C2 PASS, C3a -11.9 %, C3b 0.262,
C3c FAIL 3h vs 92h, C4 PASS.

### C3a — mean LMP (load-bearing)

| | status | model | actual | magnitude |
|---|---|---|---|---|
| control | **FAIL** | 65.24 | 74.07 | **-11.9 %** |
| arm | **FAIL** | 66.13 | 74.07 | **-10.7 %** |

Tolerance +/-10 % target / +/-10 % commercial. Improves by 1.2 pp; still FAIL.

### C3b — price duration / shape (load-bearing)

| | status | NRMSE | tolerance |
|---|---|---|---|
| control | **FAIL** | **0.262** | <= 0.20 target / <= 0.20 commercial |
| arm | **FAIL** | **0.246** | same |

Improves by 0.016; still FAIL.

### C3c — price tail / scarcity, RT hourly (supporting)

| | status | magnitude |
|---|---|---|
| control | **FAIL** | model 3h [energy-only LMP] vs RT actual 92h (0.03x, > $200) |
| arm | **FAIL** | model **3h** vs RT actual 92h (**0.03x**, > $200) |

**Unchanged.** DA diagnostic (not gated, both sides): model 3h vs DA actual 73h.

### C1 — fuel-mix by class, grid-delivered (load-bearing). Flips: **pass->fail NONE, fail->pass NONE**

| class | control status | control magnitude | arm status | arm magnitude |
|---|---|---|---|---|
| CC_REGULAR | **FAIL** | +26.82 TWh, share +2.1 pp (volume out of band) | **FAIL** | +22.56 TWh, share +1.6 pp (volume out of band) |
| CC_CHP | PASS | +2.01 TWh, +0.2 pp | PASS | +1.86 TWh, +0.2 pp |
| CT_PEAKER | PASS | -3.13 TWh, -0.4 pp | PASS | -1.45 TWh, -0.2 pp |
| ST_GAS | PASS | +2.46 TWh, +0.3 pp | PASS | **+2.89 TWh, +0.3 pp** (REGRESSION) |
| ST_CHP | PASS | -1.16 TWh, -0.1 pp | PASS | **-1.17 TWh, -0.1 pp** (REGRESSION, trivial) |
| COAL_PRB | PASS | +0.42 TWh, +0.0 pp | PASS | **+0.57 TWh, +0.0 pp** (REGRESSION) |
| COAL_BIT | PASS | +6.60 TWh, +0.3 pp | PASS | **+7.52 TWh, +0.4 pp** (REGRESSION) |
| COAL_WC | PASS | -0.10 TWh, -0.0 pp | PASS | -0.07 TWh, -0.0 pp |

Model vs actual TWh for the failing cell: CC_REGULAR model 323.947 -> 319.692 against actual 297.130.

### C2 — system volume, gas / coal families (load-bearing)

| family | control | arm |
|---|---|---|
| gas | **PASS**, model 356.11 vs actual 329.12 (C1 flags: CC_REGULAR) | **PASS**, model **353.81** (C1 flags: CC_REGULAR) |
| coal | **PASS**, model 159.63 vs actual 152.72 (all classes in band) | **PASS**, model **160.74** (REGRESSION) |

### C4 — fleet hourly dispatch correlation (supporting)

| | gas | coal |
|---|---|---|
| control | PASS, r=0.931, NRMSE=0.132 | PASS, r=0.937, NRMSE=0.149 |
| arm | **not independently re-measurable** | **not independently re-measurable** |

Stated honestly rather than copied: the payload carries a COMMITTED hourly fit that a class-TWh
delta cannot move, so a re-score returns the control's own C4 rows for both sides. That is an
artifact, not a measurement. Direct bound instead, from the two bundles' own hourly series:
arm-vs-control hourly **r = 0.99897 (gas fleet)** and **r = 0.99943 (coal fleet)**; gas mean
40,806.1 -> 40,550.2 MW, rms difference 545.7 MW, max |diff| 3,158.6 MW; coal mean 18,222.9 ->
18,349.3 MW, rms difference 295.6 MW, max |diff| 3,561.0 MW. Any true C4 movement is negligible
against the r >= 0.70 / NRMSE <= 0.30 gates.

### C8 — forced-energy share, D-2 (protective). No gate flip; every share falls

Regenerated `legitimacy_diagnostics.json` in the arm bundle vs the control's committed one; gate
thresholds byte-identical on both sides (`d2_peaker_max_share` 0.15, `d2_merchant_max_share` 0.30,
exempt CC_CHP/CT_CHP/ST_CHP/nuclear).

| class | mechanism | control share | arm share | control TWh | arm TWh |
|---|---|---|---|---|---|
| CT_PEAKER | ct_netload_drag | 0.2177 | **0.1865** | 3.3066 | 3.1414 |
| CT_CHP (exempt) | chp_steam | 0.2359 | 0.2220 | 0.3714 | 0.3594 |
| ST_GAS | st_netload_drag | 0.1573 | **0.1358** | 1.2555 | 1.1405 |
| CC_CHP (exempt) | chp_steam | 0.1518 | 0.1478 | 1.1480 | 1.0967 |
| ST_CHP (exempt) | chp_steam | 0.0488 | 0.0467 | 0.0374 | 0.0354 |
| CC_REGULAR | cc_mustrun_per_plant | 0.0291 | 0.0261 | 9.4294 | 8.3498 |
| CC_REGULAR | reliability_floor | 0.0001 | 0.0001 | 0.0470 | 0.0464 |
| COAL | coal_mustrun | 0.0059 | 0.0056 | 0.9434 | 0.8935 |
| COAL | reliability_floor | 0.0006 | 0.0005 | 0.0905 | 0.0846 |
| COAL | chp_steam | 0.0000 | 0.0000 | 0.0043 | 0.0042 |
| (system) | nuclear_mustrun | 1.0000 | 1.0000 | 272.1868 | 272.1868 |

Every non-exempt forced share moves DOWN or holds. The committed control's C8 reads PASS; nothing in
the arm can flip it in the adverse direction. Note the arm's diagnostics carry the standard
`fleet_only` reconstruction caveat ("the P2 RA must-offer bridge floor is NOT included, so CC/CT
forced shares are lower bounds") — the same caveat applies to the control's committed file, so the
comparison is like-for-like.

### C6 — governance gate (protective)

| | status |
|---|---|
| control | **PASS** (committed `calibration_attestation.json`) |
| arm | **UNSCOREABLE — no attestation** |

A `replay_keeper` probe bundle writes no `calibration_attestation.json`, so C6 cannot be scored on
the arm. Flagged rather than reported as a pass. This is expected for a throwaway screen and is not
a defect of the mechanism.

### Determination-level summary

No criterion changes status in either direction on either side. The control's committed 2022
determination (NOT-YET; fails fuelmix, price_mean, price_shape; C3c a ledgered caveat; C2/C4/C6/C8
PASS) is unchanged by the arm.

## 5. S-5 — model price tail hours, arm and control

| basis | control > $200 / > $500 | arm > $200 / > $500 |
|---|---|---|
| load-weighted system price | **0 / 0** | **0 / 0** |
| simple zone-mean price | **0 / 0** | **0 / 0** |
| **max zonal LMP** (the basis C3c and the payload's `ordc.hoursGt200` use) | **3 / 0** | **3 / 0** |
| actual RT | 92 / 26 | 92 / 26 |

Supporting price statistics:

| | control | arm |
|---|---|---|
| mean, load-weighted | 63.312 | **64.074** |
| mean, simple zone-mean | 62.605 | **63.320** |
| p99, simple zone-mean | 113.27 | **120.81** |
| max hour, simple zone-mean | 169.99 | **181.57** |
| max zonal LMP, any zone/hour | **247.50** | **247.50** |

The max zonal LMP is byte-identical because that hour is set by an oil unit whose own `mc` is
247.50 $/MWh (visible in the arm's `unit_hourly_2022.parquet`), i.e. the ceiling here is a marginal
offer, not a scarcity price. The arm lifts the middle of the distribution (p99 +7.5 $/MWh) without
adding a single hour above $200 on any system basis.

## 6. S-6 — reserve families: the recorded prediction is FALSIFIED (and the control baseline is CONFIRMED)

From `hourly/reserve_family_2022.parquet`, `pass == P1`, 8,760 hours per family per bundle:

| bundle | family | hours dual > 0 | max dual $/MW | min dual | min(held - requirement) MW | hours shortfall > 0 | max shortfall MW |
|---|---|---|---|---|---|---|---|
| **CONTROL** | pjm_primary | **0** | -0.000000 | -0.000000 | 0.000000 | 0 | 0.000 |
| **CONTROL** | pjm_primary_mad | **0** | -0.000000 | -0.000000 | 0.000000 | 0 | 0.000 |
| **ARM** | pjm_primary | **0** | -0.000000 | -0.000000 | 0.000000 | 0 | 0.000 |
| **ARM** | pjm_primary_mad | **2** | **12.259206** | -0.000000 | 0.000000 | 0 | 0.000 |

**The CONTROL shows ZERO non-zero-dual hours in 2022 in BOTH families** — count of hours with
`dual != 0` (not merely `> 0`) is 0 for both. The parent's read of the committed baseline is
**correct** and needs no correction.

**What is contradicted is the parent's prediction about the ARM.** The prediction was 0.00 in all
8,760 hours, both families. Measured: `pjm_primary_mad` binds in **2 of 8,760** hours.

Those two hours, and where they fall:

| hour index | family | dual $/MW | requirement MW | held MW | held - req | shortfall | inside the 92 `rt > 200` hours? | inside the 26 `rt > 500`? | actual RT $/MWh |
|---|---|---|---|---|---|---|---|---|---|
| 5294 | pjm_primary_mad | 11.420989 | 2,721.600 | 2,721.600 | 0.000 | 0.0 | **YES** | no | 369.54 |
| 5295 | pjm_primary_mad | 12.259206 | 2,722.500 | 2,722.500 | 0.000 | 0.0 | **YES** | no | 410.24 |

**Both binding hours are inside the 92 target hours** — 2 of 92 (2.2 %). `held == requirement` to the
MW and shortfall is 0.0 in both, so this is a binding-at-requirement rent, not an ORDC shortfall.

Why the parent's headroom arithmetic did not predict it: the requirement is not flat. Over 2022
`pjm_primary` requirement ranges 2,317.1 - 4,224.5 MW (mean 2,663.3) and `pjm_primary_mad` ranges
2,305.9 - 4,224.5 MW (mean 2,662.4); the binding hours sit at ~2,722 MW of requirement, i.e. nowhere
near the 4,224.5 MW maximum the prediction used. The constraint that binds is therefore locational /
deliverability-shaped within the `_mad` family, not the system-wide headroom balance the ~14.4 GW
figure describes. The model price in those hours does move: hour 5294 zone-mean 169.99 -> **181.57**,
hour 5295 161.32 -> **179.35**, with max zonal 247.50 in both arms (the oil-offer ceiling above).

This is the first non-zero PJM reserve dual measured in this lane, and it is the one gate the parent
pre-registered that the arm actually lit.

## 7. S-7 — cost

| | |
|---|---|
| wall clock, whole invocation | **24 min 13 s** (2026-09-10T19:58:57Z -> 20:23:10Z) |
| year 2022 phase total | 1,415.3 s |
| data_prep | 101.6 s |
| **P0 solve** | **892.1 s** (cold, 425,324 simplex iterations, objective 16,406,022,059.1933) |
| markup | 35.9 s |
| **P1 solve** | **282.6 s** (warm, 122,915 simplex iterations, objective 18,242,455,261.9152) |
| results_write | 103.1 s (bench 44.9 s, sidecars 38.5 s, frames 10.6 s, parquet 7.3 s) |
| matrix build | 16.5 s |
| **peak RSS, model self-report** | **13.31 GB** ("year 2022 memory after release: peak=13.31 GB") |
| **peak RSS, sampled from `ps`** | **13.94 GB** (13,942,788 KB) |
| container | 15.7 GiB RAM + 8.0 GiB swap added by `prepare_solve_container.py` |
| bundle size on disk | 196 MB |

The solve exceeded the 20-minute rule-32(b) shard budget by ~4 minutes. It completed; no artifact was
half-written and nothing was pushed mid-solve. A PJM year fits this budget only marginally, and P0
(892 s) is where it goes — worth knowing before the six-shard full span is launched.

---

## Reading of the screen (offered, not decided)

- The mechanism does what its own arithmetic says: S-1 lands inside BOTH pre-registered bands
  (+1,049.8 MW annual, +4,323.6 MW in the tail), the input-layer footprint is confined exactly to the
  gas plant_groups it claims, the dispatch effect is correctly tail-localised, and the reserve dual
  lights in the target hours.
- No non-target load-bearing criterion flips, in either direction. C3a and C3b both improve
  (-11.9 % -> -10.7 %; 0.262 -> 0.246), and C1's failing cell narrows (+26.82 -> +22.56 TWh).
- **But the card's own effect gate FAILS**: 0.592 GW of a 9.830 GW tail gap closed against a 2.0 GW
  bar, the model still forms 0 tail hours on any system price basis (3 on the max-zone basis,
  unchanged), and C3c is untouched at 3h vs 92h.
- The regressions are real and are not softened here: coal reabsorbs most of the displaced CC energy
  (COAL_BIT +0.92 TWh, COAL_PRB +0.15, ST_GAS +0.44), and C2 coal moves 159.63 -> 160.74 TWh against
  152.72 actual.

A screen may kill an arm; it may never promote one. On the pre-registered structural gate as written
(S-3 >= 2.0 GW), **this arm does not clear it**. Whether the S-1/S-6 evidence justifies re-specifying
the gate rather than dropping the arm is the parent's call, and then the owner's — not this shard's.

## Bundle state and the rule-31 promotion question

`results/calibration/pjm_d4_4_screen_2022/` (196 MB) is on LOCAL DISK ONLY. It is gitignored, was
never committed, never registered, and has NOT been deleted. **This container is ephemeral: the
bundle does not survive the session.** Under rule 29 clause 2 the screen year is re-solved inside the
full span anyway, so letting it go costs one re-solve of 2022 (~24 min) and nothing else. The
promotion decision is the owner's; this shard makes no move on it either way.
