# RESULT — nyiso-223 shard, year 2025 (hub-daily unpriced-day gap fill, ARM)

**Shard:** `nyiso223-y2025-r2` (relaunch) · **Session:** nyiso-223 · **ISO:** NYISO · **Year:** 2025 only
**Base SHA:** `ce4779ecd62db3c732e0d0cd7b910b80bc23ed99`
**Arm:** `replay_keeper.py results/calibration/nyiso_fuelvintage_A --years 2025 --set nyiso_hub_gap_month_level=true`
**Bundle (local, gitignored, NOT deleted — rule 31 `[R-RETAIN]`):** `results/calibration/nyiso223_gapfill_2025/`
**Control:** the keeper's own committed 2025 sidecars, `results/calibration/nyiso_fuelvintage_A/hourly/` (rule 29 `[R-SCREEN]` (b), form 4 — no control solve spent).

---

## 0. Gates

**Hard stops** — all PASS. `git rev-parse HEAD` = `ce4779ec…`; keeper `meta.json` `iso == NYISO`;
`grep -c nyiso_hub_gap_month_level src/market_sim/config/scenarios.py` = 4.

**Clean-tree fix (as directed).** `curate_capacity_deliverability.py --isos NYISO` (35 rows) and
`curate_nyiso_interface_flows.py` (9 partitions) were the only two curated datatypes the solve
needed — **no third missing datatype was named**, so no iteration was required. `curate_lmp.py` was
NOT touched (`scripts/` edits forbidden; the solve does not need `lmp`).

**Pre-solve gate (zero LP)** — all four numbers match the PRECOMMIT exactly:

| quantity | expected | measured |
|---|---|---|
| annual mean off → on | 5.5602 → 5.5602 | **5.5602 → 5.5602** |
| Dec 22–31 off → on | 7.256 → 7.256 | **7.256 → 7.256** |
| hours moved | 6552 | **6552** |
| max \|Δ\| | 7.587 | **7.587** |

**Post-solve signature** — all PASS: `nyiso_hub_gap_month_level` **true**;
`offer_curve_by_group.CC_REGULAR.peak` **2.25**, `.pct_peaking` **8.0**;
`nyiso_gas_commitment_bridge` **true**; `nyiso_dynamic_reserve_requirements` **true**;
`meta.json` iso **NYISO**, years **[2025]**.

**Runtime:** solve start 02:41:47 UTC → artifacts 02:53:38 UTC ≈ **11 min 51 s**, inside the 20-min
shard budget (rule 32 `[R-SHARD]` (b)).

---

## 1. Model annual mean LMP

| basis | arm | keeper | Δ |
|---|---:|---:|---:|
| **load-weighted across the 5 load zones** | **58.5074** | 58.3573 | **+0.1501** |
| **equal-hour mean of the 5 load zones** | **59.3874** | 59.2440 | **+0.1434** |
| equal-hour mean incl. `NYISO_external` (6 zones) | 58.8898 | — | — |

Load zones = `Capital_Hudson`, `Long_Island`, `Lower_Hudson`, `NYC`, `Upstate_West`.
`NYISO_external` carries zero demand and is excluded from the load-weighted figure.
Total P1 demand 151.5898 TWh.

> **CORRECTION (added after the first push).** The line that stood here said C3a/C3b were *not
> computable* for want of an `lmp` clean partition. **That was wrong.** The C3a/C3b scorers do not
> read the `lmp` clean datatype at all — they read the **committed** benchmark
> `frontend/data/backcast/bench/NYISO/2025.json.gz` (`bench.avgLMP.rt_lw` / `rt_lw_mon`), which is
> in the repo. Both criteria are therefore scorable at zero LP cost, and **§1b below scores them.**
> The sibling 2022 shard's identical conclusion should be re-checked on the same grounds.

**Basis warning on the two numbers above.** Neither figure in the table is the C3a basis. The
scorer's "system load-weighted mean LMP" is the demand-weighted mean over **all (zone, hour)
cells** — per zone `p_z = Σ_t p_zt·d_zt / Σ_t d_zt`, then `_wmean` across zones by zone total
demand. The 58.5074 above is instead the *equal-hour average of the hourly load-weighted price*,
a different (and materially lower) statistic. Verified: the per-zone hourly-LW basis reproduces the
keeper's committed payload `lmp[z].p` to rounding on all six zones (Capital_Hudson 63.677 vs
63.68, Long_Island 65.153 vs 65.15, Lower_Hudson 64.461 vs 64.46, NYC 63.573 vs 63.57,
NYISO_external 56.257 vs 56.26, Upstate_West 57.006 vs 57.01). **Use §1b, not §1, for anything
compared against the scorer.**

## 1b. C3a and C3b — SCORED (correct basis, committed bench)

Benchmark: `bench.avgLMP.rt_lw` = **66.43 $/MWh** (the v2.4 like-for-like load-weighted RT actual —
top of the scorer's basis ladder, so this is the gated comparison, not a fallback).

| criterion | keeper | **arm** | Δ | band | verdict |
|---|---:|---:|---:|---|---|
| **C3a** mean LMP, model | 61.60 | **61.72** | +0.12 | — | — |
| **C3a** % error vs rt_lw 66.43 | −7.27 % | **−7.09 %** | **+0.18 pt toward actual** | ±10 % | **PASS → PASS** |
| **C3b** monthly NRMSE | 0.1596 | **0.1579** | **−0.0017 (better)** | ≤0.20 | **PASS → PASS** |

Monthly load-weighted model vs the committed `rt_lw_mon` actual:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| keeper | 96.44 | 81.19 | 49.06 | 42.08 | 36.29 | 55.44 | 67.56 | 50.53 | 44.07 | 46.14 | 54.63 | 97.14 |
| **arm** | **97.67** | 81.15 | 49.04 | 42.08 | 36.30 | 55.27 | 67.57 | 50.36 | 44.10 | 46.14 | **55.14** | 97.14 |
| **actual** | 111.20 | 99.40 | 46.98 | 40.65 | 33.73 | 78.42 | 79.63 | 45.63 | 40.43 | 45.68 | 55.07 | 98.12 |

**Both gates move the right way.** The model runs *low* on the annual mean (−7.3 %), so the arm's
+$0.12 is toward the actual, not away from it; and November — the arm's largest structural mover
after January — goes 54.63 → **55.14** against an actual of **55.07**, i.e. from −0.44 to **+0.07**,
essentially onto the number. January improves 96.44 → 97.67 against 111.20 (still the dominant
residual: the model does not reproduce the Jan/Feb/Jun/Jul spikes, which is a pre-existing keeper
defect the arm neither causes nor fixes).

**No gate regresses on 2025.** The "structural integrity improves but gates regress" tradeoff does
not arise here — structure improves *and* both scored price gates improve.

---

## 2. Model monthly means (load-weighted ISO price), arm vs keeper

| month | keeper LW | **arm LW** | Δ LW | keeper EQ | **arm EQ** | Δ EQ |
|---|---:|---:|---:|---:|---:|---:|
| Jan | 94.470 | **95.898** | **+1.428** | 96.866 | **98.268** | **+1.402** |
| Feb | 79.789 | **79.755** | −0.034 | 81.080 | **81.047** | −0.033 |
| Mar | 48.410 | **48.397** | −0.013 | 49.645 | **49.633** | −0.012 |
| Apr | 41.303 | **41.304** | +0.000 | 42.544 | **42.545** | +0.000 |
| May | 35.823 | **35.844** | +0.021 | 37.490 | **37.497** | +0.007 |
| **Jun** | 49.779 | **49.652** | **−0.128** | 50.213 | **50.081** | **−0.132** |
| Jul | 64.813 | **64.819** | +0.006 | 64.915 | **64.921** | +0.006 |
| Aug | 48.237 | **48.153** | −0.084 | 48.289 | **48.212** | −0.078 |
| Sep | 42.957 | **42.996** | +0.039 | 42.962 | **43.002** | +0.040 |
| Oct | 45.418 | **45.423** | +0.005 | 45.661 | **45.666** | +0.005 |
| **Nov** | 53.879 | **54.416** | **+0.536** | 54.647 | **55.136** | **+0.488** |
| **Dec** | 96.015 | **96.016** | **+0.000** | 97.226 | **97.229** | **+0.004** |

Hours with \|ΔLW\| > $0.01: **6233**; max \|ΔLW\| **$38.29**.

### 2b. CORRECTION to the shard brief's target-window claim

The brief said *"June and November are where this year's gap fill bites (max |Δ| 7.587)"*. Measured
per month, that is **wrong about which month carries the 7.587**: the largest per-day gas move in
2025 is in **January**, and January is also where the price response is largest.

| month | gas off | gas on | Δ mean | hours moved | max \|Δ\| $/MMBtu |
|---|---:|---:|---:|---:|---:|
| Jan | 14.0948 | 14.0948 | +0.0000 | 744 | **7.587** |
| Feb | 7.3958 | 7.3958 | +0.0000 | 672 | 1.331 |
| Mar | 4.8080 | 4.8080 | +0.0000 | 744 | 0.226 |
| **Apr** | 4.2352 | 4.2352 | +0.0000 | **0** | 0.000 |
| May | 3.7743 | 3.7743 | −0.0000 | 744 | 1.120 |
| Jun | 3.7125 | 3.7125 | −0.0000 | 720 | 0.874 |
| Jul | 4.2935 | 4.2935 | −0.0000 | 744 | 0.074 |
| Aug | 3.6210 | 3.6210 | +0.0000 | 744 | 1.100 |
| Sep | 3.2395 | 3.2395 | −0.0000 | 720 | 0.050 |
| **Oct** | 3.7248 | 3.7248 | +0.0000 | **0** | 0.000 |
| Nov | 4.6192 | 4.6192 | −0.0000 | 720 | 0.618 |
| **Dec** | 9.1743 | 9.1743 | +0.0000 | **0** | 0.000 |

**Mean preservation holds MONTH BY MONTH, not merely annually** — every month's off/on mean is
identical to 4 decimal places, which is a stronger statement than the annual gate makes and is the
arm's central structural claim. December, April and October have **zero** moved hours (their prints
reach month-end), so **December is a clean internal control and it moved +0.000 / +0.004** — i.e.
the price response is entirely attributable to the redistributed days.

---

## 3. C3c — price tail

| quantity | arm | keeper |
|---|---:|---:|
| model hours, **load-weighted ISO price** > $300 | **3** | 3 |
| model hours, **any load zone** > $300 | **3** | 3 |
| model hours, any zone incl. external > $300 | **3** | 3 |
| **model maximum zonal price** | **$323.5304** | $323.5304 |

Actual 2025: **42 h**. The arm reproduces the keeper's C3c position **exactly** — the gap fill moves
neither the tail-hour count nor the maximum. Per-zone maxima (arm):
Long_Island 323.530 · NYC 323.529 · Lower_Hudson 320.540 · Capital_Hudson 308.999 ·
Upstate_West / NYISO_external 297.413.

---

## 4. C1 per-class TWh — and the two bases differ, as the 2022 shard warned

**Basis A — C1 grid-delivered** (`hourly/class_hourly_2025.parquet`, pass P1, minus the
`btm.parquet` `btm_twh` column for the three CHP classes). This is the basis the scorer's
"C1 fuel-mix by class (grid-delivered)" label names.

| class | keeper busbar | **arm busbar** | Δ | btm_twh | **arm grid-delivered** |
|---|---:|---:|---:|---:|---:|
| CC_REGULAR | 35.3355 | **35.2990** | −0.0364 | 0 | **35.2990** |
| nuclear | 28.3416 | **28.3416** | 0.0000 | 0 | **28.3416** |
| hydro | 24.0589 | **24.0589** | 0.0000 | 0 | **24.0589** |
| import | 19.3577 | **19.3677** | +0.0100 | 0 | **19.3677** |
| CC_CHP | 20.3967 | **20.3536** | −0.0431 | 1.4177 | **18.9359** |
| ST_GAS | 9.3331 | **9.3673** | +0.0342 | 0 | **9.3673** |
| wind | 7.0487 | **7.0487** | 0.0000 | 0 | **7.0487** |
| OTHER | 1.9483 | **1.9483** | 0.0000 | 0 | **1.9483** |
| CT_CHP | 1.6839 | **1.6841** | +0.0001 | 0.0000 | **1.6841** |
| CT_PEAKER | 1.3179 | **1.3432** | **+0.0253** | 0 | **1.3432** |
| oil | 1.2835 | **1.2859** | +0.0024 | 0 | **1.2859** |
| ST_CHP | 1.4469 | **1.4504** | +0.0035 | 0.3380 | **1.1124** |
| solar | 0.9813 | **0.9813** | 0.0000 | 0 | **0.9813** |
| biomass | 0.6724 | **0.6724** | 0.0000 | 0 | **0.6724** |
| COAL_BIT | 0.0000 | **0.0000** | 0.0000 | 0 | **0.0000** |
| COAL_PRB | 0.0000 | **0.0000** | 0.0000 | 0 | **0.0000** |
| **TOTAL** | **153.2063** | **153.2023** | **−0.0040** | 1.7557 | **151.4466** |

`dispatch/2025_P1.parquet` grouped by `klass` reproduces the busbar column **exactly** — the two
artifacts agree; only the BTM subtraction separates busbar from grid-delivered.

### 4b. CRITICAL — the D-2 `class_total_twh` column is a DIFFERENT basis

The 2022 shard's ~1 TWh CC_REGULAR discrepancy **reproduces in 2025**. The parent must difference
like against like.

| class | **D-2 `class_total_twh` (arm)** | class_hourly busbar (arm) | gap | D-2 keeper | D-2 Δ |
|---|---:|---:|---:|---:|---:|
| CC_REGULAR | **34.0057** | 35.2990 | **−1.2933** | 34.0414 | −0.0357 |
| CC_CHP | **20.5998** | 20.3536 | +0.2462 | 20.6421 | −0.0423 |
| ST_GAS | **11.8222** | 9.3673 | **+2.4549** | 11.7842 | +0.0380 |
| CT_CHP | **3.1147** | 1.6841 | +1.4306 | 3.1105 | +0.0042 |
| CT_PEAKER | **1.1461** | 1.3432 | −0.1971 | 1.1240 | +0.0221 |
| ST_CHP | **0.0899** | 1.4504 | −1.3605 | 0.0902 | −0.0003 |
| hydro | **24.0589** | 24.0589 | 0.0000 | 24.0589 | 0.0000 |
| (blank — nuclear/import pool) | **36.2308** | — | — | 36.2308 | 0.0000 |

The D-2 column is the **fleet-only reconstruction** basis (`run_year(fleet_only=True)`), which
carries a different class attribution than the dispatch sidecar. **Do not mix the two columns in a
single arm-vs-keeper difference.** Arm-vs-keeper *within* D-2 is internally consistent and is the
right-hand pair of columns above.

---

## 5. C8 — forced share by class (D-2), with mechanism breakdown

**D-2 verdict: PASS** (all four scored classes under their caps).

| class | forced TWh | class_total TWh | forced share | limit | verdict |
|---|---:|---:|---:|---:|---|
| CC_REGULAR | 0.1566 | 34.0057 | **0.46 %** | 30 % | pass |
| CT_PEAKER | 0.0000 | 1.1461 | **0.00 %** | 15 % | pass |
| ST_GAS | 2.1302 | 11.8222 | **18.02 %** | 30 % | pass |
| hydro | 0.0000 | 24.0589 | **0.00 %** | 30 % | pass |

Keeper for comparison: CC_REGULAR 0.45 %, CT_PEAKER 0.00 %, ST_GAS 18.13 %, hydro 0.00 % — the arm
moves ST_GAS forced share **−0.11 pt** and CC_REGULAR **+0.01 pt**.

**Per-mechanism breakdown (all D-2 rows, arm):**

| class | mechanism | forced TWh | share of class |
|---|---|---:|---:|
| (blank pool) | `nuclear_mustrun` | 28.3416 | 78.23 % |
| (blank pool) | `firm_import` | 7.8840 | 21.76 % |
| CC_CHP | `chp_steam` | 0.0654 | 0.32 % |
| CC_REGULAR | `nyiso_gas_commitment_bridge` | 0.1566 | 0.46 % |
| CT_CHP | `chp_steam` | 0.0030 | 0.10 % |
| ST_CHP | `chp_steam` | 0.0120 | 13.37 % |
| ST_GAS | `reliability_floor` | 2.1181 | 17.92 % |
| ST_GAS | `nyiso_gas_commitment_bridge` | 0.0121 | 0.10 % |
| hydro | `hydro_min_flow` | 6.6025 | 27.44 % |

CC_CHP / CT_CHP / ST_CHP / nuclear are D-2 exempt classes. hydro's `hydro_min_flow` energy is
reported but does not enter the summary's forced share (0.00 %).

**Stated shares are LOWER BOUNDS** — the artifact's own note: floors were reconstructed via
`run_year(fleet_only=True)`, so the P2 RA must-offer bridge floor (needs the P1 solution) is not
included, and CC/CT forced shares are therefore lower bounds. One floored pseudo-unit row
(`u:NYISO_external_HQ_hydro`, plant_code ≤ 0) is scored under the floor-energy convention
(PREREG-caiso155 §3), so its TWh is an upper bound on at-floor dispatch.

---

## 6. Equal-hour mean model price — June / November / December

| month | **arm EQ** | keeper EQ | Δ | gas hours moved | gas max \|Δ\| |
|---|---:|---:|---:|---:|---:|
| **June** | **50.081** | 50.213 | **−0.132** | 720 | 0.874 |
| **November** | **55.136** | 54.647 | **+0.488** | 720 | 0.618 |
| **December** | **97.229** | 97.226 | **+0.004** | **0** | **0.000** |

**December is the control and it behaves as a control**: zero moved gas hours ⇒ +$0.004 on an
$97 month (4 parts in 100,000). June and November both move, in **opposite directions**, at
comparable gas-move magnitude — which is the signature of *redistribution* rather than a level
shift. (January, not shown in the brief's window, is the larger mover: +$1.402 EQ on a 7.587
max-\|Δ\| month — see §2b.)

---

## 7. Legitimacy diagnostics — gate verdict

**Overall: FAIL**, on **D-4 only**. Every other diagnostic passes.

| diagnostic | arm | keeper (2025) |
|---|---|---|
| D-1 diurnal shape | **PASS** | PASS |
| D-2 forced-energy attribution | **PASS** | PASS |
| **D-4 off-window binding** | **FAIL (1 row)** | **FAIL (1 row — same row)** |
| D-5 forecast/backcast parity | **PASS** | PASS |
| D-9 overlay quarantine | **PASS** | PASS |
| D-10 free-class-only rescore | **PASS** | PASS |

**The single failing D-4 row (arm):**

> `2025 reliability_floor × ST_GAS`: plant **8006** is floored for **0.0011 TWh** (0.1 % of the
> mechanism's forced energy) while its own measured median output over the **19 hours** the floor
> actually binds for it (inside h0–23) is **0.000 MW** (52.6 % of them at zero) — the meter says it
> is offline in at least half the hours the floor asserts it must be online (per-unit conduct rider).

**This failure is PRE-EXISTING in the keeper, not introduced by the arm.** The keeper's own 2025
D-4 carries the identical row for the identical plant and mechanism (0.0010 TWh, 17 binding hours,
58.8 % at zero). The arm changes the row's magnitude by +0.0001 TWh and its binding-hour count by
+2 h. **The arm does not open a new D-4 failure and does not close the existing one.**

D-4 notes (arm): the ct_only vintage guard extended the flag from sibling-year vintages for 9
plants (2682, 50744, 50978, 52168, 54041, 54131, 54592, 54593, 7314); the per-unit conduct rider
skipped 3 floored plants carrying the benchmark's CT-only CEMS flag (2493, 50978, 7314).

D-10 note: 2/2 NYISO wind/solar (year, fuel) rows are `delivered_pinned` — advisory-only C1 rows
that measure plumbing, never model skill.

---

## 8. Did class energy move materially? — the mean-preservation-in-dispatch test

2025 carries the **largest per-day gas move of any year** (max \|Δ\| $7.587/MMBtu, in January), so
this is the strongest available test of the arm's claim that redistributing unpriced days preserves
the mean *in dispatch*, not merely in the fuel array.

**It passes, and by a wide margin.**

- **Total generation moves −0.0040 TWh on 153.2 TWh — 2.6 parts per 100,000.**
- **Every zero-marginal-cost and must-run class is byte-identical**: nuclear, hydro, wind, solar,
  biomass, OTHER, COAL_BIT, COAL_PRB all move **0.0000 TWh**.
- The **entire** response is a merit-order reshuffle inside the gas stack plus imports:

| class | Δ TWh | Δ % |
|---|---:|---:|
| CC_CHP | −0.0431 | −0.21 % |
| CC_REGULAR | −0.0364 | −0.10 % |
| ST_GAS | +0.0342 | +0.37 % |
| **CT_PEAKER** | **+0.0253** | **+1.92 %** |
| import | +0.0100 | +0.05 % |
| ST_CHP | +0.0035 | +0.24 % |
| oil | +0.0024 | +0.19 % |
| CT_CHP | +0.0001 | +0.01 % |

The gas-family classes sum to roughly −0.045 TWh against +0.045 TWh of ST_GAS / CT_PEAKER / oil /
import pickup — displacement, not creation. **CT_PEAKER's +1.92 % is the largest relative move**
and is the one number worth the parent's attention: it is 25 GWh on a 1.3 TWh class, consistent
with the January gas spike days pushing a handful of CC hours up past peaker offers, and it is the
mechanism by which the annual mean price rises +$0.15 while the *fuel* mean is preserved exactly.

**Interpretation.** Mean-preserving in fuel ⇏ mean-preserving in price, because dispatch is convex
in fuel price: redistributing a month's gas cost onto its true daily shape (rather than holding the
last print flat) raises cost in the expensive hours more than it lowers it in the cheap ones. The
arm's higher price and +1.9 % peaker energy are that convexity, and they are **structural, not
fitted** — the fuel array's monthly means are unchanged to 4 decimals in all 12 months.

**And the convexity points the right way.** The model's standing 2025 error is that it prices
**too low** (C3a −7.3 %), so a mechanism that raises price through genuine within-month cost
dispersion moves toward the actual for a structural reason rather than a fitted one. That is the
rule 1 `[R-STRUCT]` case for the arm: it would be admissible even if the residual had worsened,
and on 2025 it does not worsen.

## 8b. RECOMMENDATION (this shard's own reading — not a promotion)

**On 2025 evidence: YES, a keeper candidate.** Rationale, in the order rule 1 wants it:

1. **Structure first.** The mechanism is mean-preserving in the fuel array in **all 12 months** to
   4 decimals, confined to unpriced days, with three months (Apr/Oct/Dec) untouched as a built-in
   control that measures zero response. No new tuning surface, no adder, no residual-fitted value.
2. **No structural regression.** D-1/D-2/D-5/D-9/D-10 all PASS; the single D-4 failure is the
   keeper's own pre-existing plant-8006 row, unchanged in kind.
3. **No forcing regression.** C8 shares move ≤0.11 pt; ST_GAS *improves* (18.13 → 18.02 %).
4. **Gates improve rather than regress.** C3a −7.27 → **−7.09 %**; C3b 0.1596 → **0.1579**; C3c
   byte-identical (3 h, $323.53).
5. **Dispatch is undistorted.** Total generation moves 2.6 ppm; every must-run and zero-MC class is
   byte-identical; the entire response is a gas-stack reshuffle.

**Why this shard nonetheless CANNOT promote it** — a hard blocker, not a judgement call:

- **Rule 16 `[R-ALLYEARS]` forbids a single-year keeper.** This bundle is **2025 only**. NYISO's
  keeper span is `--year 2023 2024 2025` in ONE bundle. The 2023 and 2024 arms do not exist in this
  container, so there is nothing to compose.
- **Rule 32 `[R-SHARD]` (d) gives registration to the PARENT, once, after the shards land** — and
  this shard's brief forbids `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`,
  `prune_iso_runs.py` and every path under `frontend/data/backcast/**` by name.
- **The 2025 bundle is gitignored and dies with this container**, so even a composed keeper would
  need the bytes re-solved unless the parent acts while a container holds them.

**What promotion actually needs:** the 2023 and 2024 arms (~12 min of LP each, one shard per year
under rule 32(b)), composed with this 2025 arm into one bundle by the parent, then registered and
keeper-designated in the parent. This shard's numbers stand as the 2025 leg of that decision.

---

## 9. What this shard did NOT do

- **C3a/C3b ARE scored** — see §1b. (The brief's premise that they were unavailable was wrong; the bench is committed. No `lmp` clean partition was needed or built, and `curate_lmp.py` was not touched.)
- Did not touch `curate_lmp.py` or anything else under `src/` or `scripts/`.
- Did not register anything on any dashboard, did not run `dashboard_add_run.py`,
  `build_manifest.py`, `build_status.py` or `prune_iso_runs.py`, did not touch
  `frontend/data/backcast/**`, did not open a PR.
- **Did not delete any result.** `results/calibration/nyiso223_gapfill_2025/` is on local disk and
  gitignored (rule 31 `[R-RETAIN]`). **It will not survive container reclamation** — if the parent
  or owner wants it promoted, it must be composed and registered from this container, or re-solved
  (~12 min of LP for this year).
