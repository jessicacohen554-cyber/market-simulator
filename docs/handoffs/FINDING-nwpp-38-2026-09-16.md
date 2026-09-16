# FINDING — lane NWPP-38: did the PNCA's termination change observable behaviour?

**Lane:** NWPP-38 (desk r#7 charter, 2026-09-16) · **Model:** Opus (`claude-opus-5`) ·
**Base:** `38ecbf0e6217aec7fc8ccdb1de235a55b409c498` (= `origin/main` at session start; the
issuance pinned `02c08154`, `origin/main` had moved to `38ecbf0e` by the time this lane
opened, and collision rule 3 says rebase — so the lane is based on `38ecbf0e` and every
number below is measured there) · **Branch:** `claude/nwpp-38-pnca-discontinuity-a7f3` ·
**DATA PROFILE:** `nwpp` · **Zero LP** (rule 32 `[R-SHARD]`; no solve, so no promotion
question fires under rule 31 `[R-RETAIN]`).

---

## 0. REPORT FIRST — the verdict, and the power of the test

**VERDICT (a): NO MEASURABLE CHANGE.** Across **fourteen scored shape tables spanning five
designs** — a calendar-time difference-in-differences whose window boundary *is*
2024-09-15, a local regression discontinuity at that date, the post-termination window,
the full year, the chain's own hourly coupling structure, and a test aimed directly at the
instrument's operative words — **not one of the 56 treated-group cells reaches the
detection threshold**, in 2024 or in 2025.

| group | cells | max \|z\| 2024 | max \|z\| 2025 | cells at or past the detection threshold (\|z\| ≥ 4.07) |
|---|---:|---:|---:|---:|
| **TREATED** — the coordinated Columbia system (BPAT CHPD DOPD GCPD) | 56 | **2.45** | **3.04** | **0 in 2024, 0 in 2025** |
| CONTROL — independent tributaries (PGE TPWR PACW) | 42 | 4.97 | 10.95 | 1 in 2024, **8 in 2025** |
| reported, in neither group (IPCO SCL AVA NWMT) | 48 | 5.41 | 4.58 | 2 in 2024, 1 in 2025 |

The second and third rows are the point, not a footnote. **The systems the PNCA never
coordinated moved more than the one it did** — PGE's intraday ramp metric is 10.95
pre-period standard deviations from its own mean in 2025, PACW's within-month variability
4.97 in 2024 — while the Columbia mainstem's largest excursion anywhere is 3.04. Whatever
2024 and 2025 did to Pacific Northwest hydro, it did it to the tributaries, and the
coordinated system is the *quiet* one. That is the signature of hydrology, not of an
instrument.

**THE POWER OF THE TEST, since a null is only worth what its power is.** Two error terms
bound this lane, and both are stated rather than buried:

| design | statistic | minimum detectable effect (α = 0.05 two-sided, 80 % power) |
|---|---|---|
| **D** — month-panel DiD, errors clustered on the year (G = 7) | diurnal amplitude `D1` | **0.163 = 22.4 % of its mean** |
| | intraday ramp `D2` | **0.020 = 20.2 % of its mean** |
| | within-month daily CV `M1` | **0.068 = 45.1 % of its mean** |
| | hourly spread `M2` | **0.144 = 16.1 % of its mean** |
| **A / B / C / links / boundary** — one post year scored against five pre years | any per-BA metric | **4.07 × that balancing authority's pre-period SD** (the table above is in those units) |

So: **a change of roughly one fifth in how the Columbia mainstem shapes its water within
a day would have been detected, and was not. A change of a tenth would not have been
detected and this lane cannot rule one out.** For the noisiest metric, within-month
day-to-day variability, the floor is nearer half. The binding constraint is not sample
size in hours — there are 26,303 hours per balancing authority and 29,640 clean
balancing-authority-days — it is that **treatment varies at the level of the year, and
there are seven years.** No amount of hourly data fixes that.

**And the design's own noise floor is larger than the real date's estimate.** Running the
identical estimator on a *fake* termination date of 2022-09-15 returns a bigger and far
more significant "effect" (`D2` +0.0258, t = **+4.76**) than the real 2024-09-15 date
does (`D2` −0.0055, t = −1.17). An estimator that finds more at a date where nothing
happened than at the date where something did is an estimator reporting noise. That
comparison, more than any single coefficient, is why the verdict is (a) and not (b).

**What this closes.** Routed item 5 of `FINDING-nwpp-32-2026-09-14.md` §7 — *"PNCA
terminated 2024-09-15 with no successor text found; NWPP-40's PRECOMMIT should state
it"*. Per the charter's outcome (a), **the declaration in NWPP-40's PRECOMMIT is
sufficient and this item closes.** NWPP-40 states the termination, cites this lane's
power, and proceeds on the monthly budget. No mechanism is proposed here and none is
needed; a post-PNCA operating regime built from inference would be the fitted mechanism
rule 1 `[R-STRUCT]` forbids, and NWPP has no price benchmark against which one could ever
be validated (NWPP-13 read NO).

**Found on the way, and handed over rather than acted on** (§7): the mid-Columbia chain's
hydraulic coupling is **directly measurable and strong** — adjacent-link hourly
correlation of deviations 0.35–0.60 against 0.03–0.21 for control pairs, with a stable
2–3 h lag — which is the quantity `FINDING-nwpp-32` §5(a) item 2 told NWPP-36 it would
have to measure and could not read from any instrument. And **SCL is the one balancing
authority in this footprint that genuinely did change in 2024**, on a whole-year basis
with no discontinuity at 2024-09-15, so it is not a PNCA effect and is routed as its own
question.

---

## 1. Why this lane is a measurement and not a build

`FINDING-nwpp-32-2026-09-14.md` §4 read the 1997 Pacific Northwest Coordination Agreement
in full (117 pp, `grantpud.org`) and established two facts that sit awkwardly together:

1. The PNCA is the instrument that defines **"Period means a calendar month"** — the
   accounting period the repo's hydro budget already uses
   (`hydro_monthly_min[g,m] ≤ Σ_{t∈m} P[g,t] ≤ hydro_monthly_energy[g,m]`).
2. It **terminated 2024-09-15**, i.e. *inside* the 2023-2025 scored window, and no
   successor text was found — the 2026 White Book says owners still supply BPA plant data
   and constraints, but there is no successor agreement to read.

There is no code fix for that and this lane does not invent one. There is nothing to model
*to*: a post-PNCA operating regime assembled from inference would be exactly the fitted
mechanism rule 1 `[R-STRUCT]` forbids, and it could never be falsified here because NWPP
has no price benchmark. What is missing is not a mechanism — it is **evidence about
whether the termination changed observable behaviour at all**, which is a question about
measured data and answerable now, at zero LP cost. That is what follows.

Nothing below is tuned. There is no NWPP residual, none was consulted, and no
`ScenarioConfig` field is read or written (rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 23
`[R-FROZEN-DERIVE]`, 24 `[R-REGISTRY]`).

---

## 2. Identification strategy — fixed BEFORE any metric was computed

This section was written to disk before the first metric ran (scratch `STRATEGY.md`,
2026-09-16) and is reproduced here unchanged in substance, because a design chosen after
seeing the numbers is not a design. The charter asked for exactly this ordering.

### 2.1 The confound, stated first

2024 and 2025 are different water years from 2019-2023. A raw before/after contrast on the
Columbia would confound the instrument with the hydrology, and the answer would be
whichever one the analyst preferred. Four things separate them, and all four are applied:

1. **Every metric is scale-free.** `D1`, `D2`, `M1`, `M2` and the link correlations are
   all ratios to the series' own mean, so the *level* — which is the water year, and which
   the model's monthly budget already fixes by construction — divides out. Only *shape* is
   measured, which is precisely what the budget does **not** fix and what the charter asked
   for: within-month shaping, diurnal amplitude, the plant-to-plant correlation structure
   down the chain, and the lag between adjacent projects.
2. **A control group outside the coordination object.** Tributary systems in the same
   water years, hydraulically independent of the mainstem.
3. **An explicit hydrology covariate.** Design D conditions on `log(month mean MW)`, so
   any residual path from water to shape is absorbed rather than assumed away.
4. **Placebo dates and placebo years.** The same estimator on dates where nothing happened
   bounds the design's own noise.

### 2.2 Groups — read off the budget artifact's own `chain` column, not chosen

`data/raw/nwpp-hydro/nwpp_hydro_budget.parquet` already carries a per-plant `chain`
assignment that NWPP-32 derived from the published ORNL EHA `Water` field. Aggregating it
by balancing authority on the EIA-930 basis (Priest Rapids in GCPD, not BPAT — §3.2 of
that finding) partitions this footprint for us:

| group | balancing authority | conventional-hydro MW | share on the coordinated Columbia system | what it is |
|---|---|---:|---:|---|
| **TREATED** | DOPD | 866.8 | **100 %** | Wells — mainstem position 3 |
| | GCPD | 2,170.0 | **100 %** | Wanapum + Priest Rapids — positions 6, 7 |
| | CHPD | 2,037.8 | **97.1 %** | Rocky Reach + Rock Island — positions 4, 5 |
| | BPAT | 20,736.2 | **92.6 %** | Grand Coulee, Chief Joseph, McNary, John Day, The Dalles, Bonneville + the four lower Snake + Dworshak + Libby |
| **CONTROL** | PGE | 694.2 | 0 % | Deschutes / Willamette / Clackamas |
| | TPWR | 724.8 | 0 % | Nisqually / Cowlitz |
| | PACW | 969.1 | 0 % | Lewis / Rogue / Klamath |
| reported, neither | IPCO | 2,056.7 | Hells Canyon + upper Snake — feeds the mainstem, privately operated storage |
| | SCL AVA NWMT | 2,048.5 / 1,174.1 / 715.7 | mixed: Boundary, Clark Fork and Flathead reach the Columbia only through Canadian storage |
| excluded | WAUW PACE NEVP | — | `FINDING-nwpp-32` §3.2 population mismatch — their EIA-930 hydro is not their EIA-923 plants |
| excluded | PSEI | 340.5 | its 2019-2020 `NG: WAT` is unusable (§3), so it cannot carry a five-year pre-period |
| excluded | AVRN GRID | — | no hydro |

Three of the four treated balancing authorities are *pure* mid-Columbia mainstem. That is
not a convenience of aggregation — DOPD's hydro **is** Wells and GCPD's **is** Wanapum plus
Priest Rapids — so for those two the balancing-authority series is a plant series, and the
BPAT→DOPD→CHPD→GCPD chain is four consecutive mainstem positions at hourly resolution.

The control group is the charter's: NWPP-32 §5(a) names Skagit, Cowlitz, Lewis, Deschutes,
Willamette, Baker and Nisqually as independent tributary systems. **One honest departure
from the charter's list**: Skagit is Seattle City Light, and SCL's hydro is 56.6 % Boundary
on the Pend Oreille, which is downstream of coordinated storage (Albeni Falls, Hungry
Horse). SCL is therefore *not* a clean control and is reported outside both groups rather
than being used as one. Baker is inside PSEI, which the screen removes. Making the control
group cleaner costs it nameplate — 2,728.6 MW against the treated group's 20,736 — and that
cost is accepted, because the metrics are scale-free and a contaminated control is worse
than a small one.

### 2.3 Metrics

Per balancing-authority-day, on clean complete days: **`D1`** diurnal amplitude
`(max − min) / mean` of the 24 hourly MW; **`D2`** intraday ramp `mean |dP/dt| / mean P`.
Per balancing-authority-month, on months with ≥ 26 clean days: **`M1`** within-month
daily-energy coefficient of variation; **`M2`** `(p95 − p5) / mean` of hourly MW.
Per adjacent-pair-month: **`r0`** Pearson correlation of hourly series *after* each series'
own month-by-hour-of-day mean profile is removed — so what is correlated is the deviations,
the hydraulic signal, not the shared diurnal profile any two load-following hydro systems
would show — and **`lag`**, the cross-correlation argmax over ±6 h.

### 2.4 Designs

**A — calendar-time DiD whose boundary IS the date.** `Δ = metric(Sep 15 – Nov 28) −
metric(Jul 1 – Sep 14)`. In 2024 that boundary is 2024-09-15 itself; the same calendar
contrast in 2019-2023 is a placebo, and those five placebos are the reference. Seasonality
differences out by construction.
**A-RD — the local discontinuity.** `metric ~ 1 + x + post + x·post` over ±28 days around
Sep 15, per year. The narrow window removes the year's seasonal path, so `post` is a jump.
**B — the post-termination window.** `metric(Sep 15 – Dec 31)`, pre 2019-2023 vs 2024, 2025.
**C — the full calendar year**, with 2025 entirely post-PNCA.
**D — month-panel DiD**, balancing-authority and calendar-month fixed effects, treated ×
post interaction, errors clustered on the year, run with and without the
`log(month mean MW)` hydrology control. The September-2024 month straddles the date and is
**dropped, never split**.
**Plus the instrument-specific test** of §6, which asks whether the calendar month is still
a special place in the daily-energy series — the PNCA's own operative words.

### 2.5 The pre-declared verdict rule

(a) no metric moves past its MDE in the treated group and the DiD sits inside the placebo
spread; (b) a treated move past MDE that the control does not show; (c) a move present in
both groups, or one the hydrology conditioning absorbs, or one inseparable from the
taxonomy or the screen. **A null or a confounded result is reported as such**, and no
mechanism is proposed in this lane whatever the outcome.

---

## 3. The data, and the screen this lane had to do itself

**The hourly panel is extended to 2019.** The committed per-BA wide extracts
(`data/raw/eia-930-hourly/<BA> hourly.parquet`) begin at **2023** for this footprint
(NWPP-11), which would leave exactly **one** pre-period year — not enough to say what
normal inter-year variation looks like, and therefore not enough to answer the charter's
second question at all. The EIA-930 BALANCE archive those extracts were themselves derived
from covers 2019 onward for all 62 balancing authorities, so the pre-period is extended by
re-doing, for 2019-2022, exactly what `build_nwpp_ba_hourly_from_balance.py` did for
2023-2025 (rule 23 `[R-FROZEN-DERIVE]`: the construction is reused, not re-invented).

**The derive is checked against the committed extract on the overlap and agrees exactly:
0 mismatched hours over 26,303 hours × 12 balancing authorities.** Hour grids are complete
— 8,759 / 8,784 / 8,760 / 8,760 / 8,760 / 8,784 / 8,760 rows per balancing authority per
year, the 2019 shortfall being the single hour whose local date falls in 2018.

**The mid-2024 taxonomy revamp is a real trap here and it is closed by measurement, not by
assumption.** EIA renamed the hydro column at exactly the **2024 H2** file boundary —
`Hydropower and Pumped Storage` → `Hydropower Excluding Pumped Storage` — which is 2.5
months before the PNCA terminated. A basis change that close to the date could masquerade
as an instrument effect. It does not, for two independent reasons: the new taxonomy's
pumped-storage column is **null in every hour of every NWPP balancing authority**, so the
two names carry the same energy on this footprint; and the primary design (A / A-RD)
compares Jul 1 – Sep 14 against Sep 15 – Nov 28 **within** 2024, both halves on the new
taxonomy, while every placebo year has both halves on the legacy one — so the taxonomy
differences out inside each year's contrast by construction.

**The defective hours are screened in this lane, and this lane says so.** The charter's
item 4 is binding and lane NWPP-37 — which is fixing the EIA-930 fuel-column seam (routed
item R-f) — **had not landed at base `38ecbf0e`**: no `FINDING-nwpp-37-*` exists and the
desk's r#7b enumeration of the unscreened call sites is the newest state. There is no
screened column to read, and the `NG: WAT` series has no `(Adjusted)` sibling exposed in
the wide extract. So the screen is done here: a defective hour is `|NG: WAT|` above
1.15 × the balancing authority's EIA-860 conventional-hydro nameplate (930 basis), below
−0.05 × it, or NaN. **Defective hours are dropped, never imputed, and the whole local day
is dropped from every day-level metric** (rule 13 `[R-MEASURED]`: nothing is padded).

| balancing authority | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | note |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| BPAT · IPCO · TPWR | 0 | 0 | 0 | 0 | 0 | 0 | 0 | clean throughout |
| GCPD | 0 | 0 | 0 | 0 | 0 | 1 | 0 | |
| CHPD | 22 | 21 | 23 | 0 | 0 | 1 | 9 | all NaN |
| DOPD | 120 | 1,296 | 0 | 0 | 0 | 0 | 0 | all NaN — costs 86 days of 2020 |
| PACW | 0 | 0 | 3 | 0 | 0 | 0 | 0 | |
| PGE | 27 | 1 | 0 | 0 | 0 | 0 | 0 | |
| SCL | 4 | 1 | 4 | 0 | 0 | 2 | 1 | |
| AVA | 4 | 4 | 0 | 0 | 0 | 1 | **2** | the G20 hours — 810,113 MW at 2025-10-12, 190,346 the next hour |
| NWMT | 34 | 2 | 1 | 0 | 0 | 6 | 4 | |
| *PSEI* | *5,251* | *7,124* | *2* | 0 | 0 | 0 | 0 | **whole-year defect — PSEI is excluded** |

The two AVA hours are the ones `FINDING-nwpp-32` §3.2 named. They are dropped, not
adjusted, and the two days that carry them leave the day panel. **Robustness:** re-running
design D on EIA's own `(Adjusted)` hydro column with all days kept moves the headline
coefficient from `T_post` = **+0.0444** (se 0.0487, t = +0.91) to **+0.0520** (se 0.0497,
t = +1.04) — i.e. not at all, and insignificant either way. The screen is not carrying the
result.

**Artifacts.** `data/raw/nwpp-hydro/nwpp_pnca_day_metrics.parquet`,
`nwpp_pnca_month_metrics.csv`, `nwpp_pnca_links.csv`, documented in
`data/raw/nwpp-hydro/README-nwpp-38.md`, regenerated by
`python scripts/data/measure_nwpp_pnca_discontinuity.py` (deterministic, no network, no
LP). They are measurement outputs: no `src/` module reads them and no config field names
them. NWPP-32's budget artifacts are untouched.

---

## 4. The numbers

Read every table the same way: **`MDE` is the smallest deviation this comparison could
have detected** at α = 0.05 two-sided with 80 % power, and `z` is the deviation in
pre-period standard deviations. `|z| ≥ 4.07` is detection. Anything smaller is a null.

### 4.1 Design A — the contrast whose boundary is 2024-09-15

`Δ = metric(Sep 15 – Nov 28) − metric(Jul 1 – Sep 14)`; 2019-2023 are placebos.

**Diurnal amplitude `D1`:**

| | pre mean | pre SD | MDE | 2024 | z | 2025 | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| **BPAT** | −0.0557 | 0.1386 | 0.5644 | −0.1423 | **−0.62** | −0.1131 | −0.41 |
| **CHPD** | 0.2065 | 0.3221 | 1.3117 | 0.0948 | **−0.35** | −0.1230 | −1.02 |
| **DOPD** | 0.1294 | 0.2327 | 0.9474 | 0.2469 | **+0.51** | 0.0507 | −0.34 |
| **GCPD** | 0.1971 | 0.2153 | 0.8768 | 0.1863 | **−0.05** | 0.0310 | −0.77 |
| PGE | −0.1901 | 0.0991 | 0.4037 | −0.1292 | +0.61 | −0.6721 | **−4.86** |
| TPWR | −0.4535 | 0.1295 | 0.5272 | −0.5873 | −1.03 | −0.5910 | −1.06 |
| PACW | −0.0880 | 0.1311 | 0.5339 | 0.0084 | +0.74 | 0.5313 | **+4.72** |
| SCL | −0.2226 | 0.1721 | 0.7008 | −0.2177 | +0.03 | −1.0100 | **−4.58** |
| AVA | −0.2091 | 0.2214 | 0.9018 | −0.0864 | +0.55 | −0.6379 | −1.94 |
| IPCO | −0.1063 | 0.1163 | 0.4736 | −0.0732 | +0.28 | −0.0083 | +0.84 |
| NWMT | 0.0685 | 0.1482 | 0.6036 | 0.0033 | −0.44 | 0.0135 | −0.37 |

**Intraday ramp `D2`:** the treated group's 2024 deviations are −0.68 (BPAT), −0.65 (CHPD),
+0.31 (DOPD), +0.04 (GCPD). The controls' 2025 deviations are **−10.95** (PGE) and
**+4.82** (PACW).

**As a group DiD** (treated mean − control mean), pre-period 2019-2023 mean 0.3696,
SD 0.1457, **MDE 0.5933**: 2024 deviation **−0.0371 (z −0.25)**, 2025 **−0.1643 (z −1.13)**.
For `D2`: pre mean 0.0405, SD 0.0189, MDE 0.0771; 2024 **−0.0074 (z −0.39)**, 2025 −0.0390.

### 4.2 Design A-RD — the local jump at Sep 15 (±28 d, linear trend either side)

Every year's jump, so the reader can see that a jump estimated at an arbitrary date is
never zero:

| `D1` jump | 2019 | 2020 | 2021 | 2022 | 2023 | **2024** | MDE | z(2024) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **BPAT** | −0.087 | −0.105 | −0.128 | −0.295 | −0.123 | **−0.206** | 0.343 | **−0.70** |
| **CHPD** | +0.011 | −0.017 | −0.524 | −0.119 | +0.042 | **−0.578** | 0.948 | **−1.96** |
| **DOPD** | −0.028 | n/a | −0.389 | −0.487 | −0.203 | **−0.052** | 0.828 | **+1.11** |
| **GCPD** | +0.010 | +0.035 | −0.054 | −0.263 | −0.133 | **−0.116** | 0.492 | **−0.29** |
| PGE | −0.064 | −0.122 | +0.075 | −0.098 | −0.167 | +0.088 | 0.374 | +1.78 |
| TPWR | −0.474 | −0.243 | −0.097 | +0.077 | −0.360 | +0.227 | 0.883 | +2.06 |
| PACW | −0.225 | +0.483 | −0.383 | −0.161 | +0.363 | −0.195 | 1.561 | −0.55 |

2024's mainstem jumps sit inside the placebo range on every link. CHPD's −0.578 is the
largest treated excursion in the lane and it is **1.96 σ** — against a 2021 placebo of
−0.524 at a date on which nothing happened.

### 4.3 Designs B and C — the post-termination window and the full year

**Design B, `metric(Sep 15 – Dec 31)`, treated group:** `D1` z(2024) = −0.79, +0.09, +0.28,
+0.66 for BPAT/CHPD/DOPD/GCPD; z(2025) = **−3.04**, −0.29, −1.05, −0.10 — the treated
group's largest reading anywhere in the lane, and still 1.0 σ short of detection. `D2`
largest treated |z| is 2.32 (BPAT 2025). Controls in the same table: PGE `D2`
z(2025) = **−6.20**, PGE `D1` z(2025) = **−4.44**, PACW level z(2025) = **+4.31**; and on
the full calendar year PACW's annual energy at z(2024) = **−4.81**.

**Design C, full calendar year (2025 is entirely post-PNCA), treated group:**

| metric | BPAT z24 / z25 | CHPD | DOPD | GCPD | largest treated \|z\| |
|---|---|---|---|---|---:|
| `D1` diurnal amplitude | +0.41 / −0.40 | +0.99 / +0.63 | +0.77 / +0.30 | +0.59 / +0.42 | 0.99 |
| `D2` intraday ramp | +0.46 / −0.55 | +1.11 / +0.53 | +0.85 / +0.50 | +0.48 / +0.07 | 1.11 |
| `M1` within-month CV | −1.88 / +1.52 | +2.11 / **+3.01** | +0.89 / +1.53 | +1.02 / +1.44 | 3.01 |
| `M2` hourly spread | +0.01 / −0.11 | +1.10 / +0.82 | +0.54 / +0.18 | +0.71 / +0.70 | 1.10 |

CHPD's `M1` at +3.01 in 2025 is the treated group's largest reading in design C. It is below
the 4.07 threshold; it is in the *second* year after the termination with nothing at the
boundary itself; and PGE's `M1` in the same year is **+5.50** and PACW's 2024 is **+4.97**,
both controls. Reported at full magnitude and not claimed as an effect.

### 4.4 Design D — month-panel DiD with the hydrology control

Balancing-authority and calendar-month fixed effects, treated × post interaction, errors
clustered on the year (G = 7), September 2024 dropped as the straddling month, n = 575.

| metric | water control | `T_post` | se | 95 % CI | MDE | as % of mean |
|---|---|---:|---:|---|---:|---:|
| `D1` | no | +0.0739 | 0.0599 | [−0.0725, +0.2204] | 0.2007 | 27.5 % |
| `D1` | **yes** | **+0.0444** | 0.0487 | **[−0.0749, +0.1636]** | 0.1634 | **22.4 %** |
| `D2` | no | +0.0138 | 0.0081 | [−0.0060, +0.0336] | 0.0271 | 27.7 % |
| `D2` | **yes** | **+0.0099** | 0.0059 | **[−0.0045, +0.0243]** | 0.0198 | **20.2 %** |
| `M1` | **yes** | **−0.0192** | 0.0204 | **[−0.0691, +0.0306]** | 0.0683 | **45.1 %** |
| `M2` | **yes** | **−0.0141** | 0.0429 | **[−0.1190, +0.0908]** | 0.1437 | **16.1 %** |

Every interval spans zero. Two further things are worth naming. **The hydrology control
shrinks the point estimates** — `D1` +0.0739 → +0.0444, `D2` +0.0138 → +0.0099, a third of
each — which is what you expect if the small positive residual is water rather than
regime, and is the direct answer to the charter's hard question. And **the estimates do not
even agree in sign across designs**: design D's `D1` is +0.044 on the full panel, while the
same estimator on a symmetric ±2-year window around the real date gives −0.048. Both
insignificant; an effect that flips sign with the window is not an effect.

### 4.5 The placebo dates — the design's own noise floor

The identical estimator (with the water control, ±2-year symmetric window) at a fake
termination date:

| fake date | `D1` | t | `D2` | t | `M1` | t | `M2` | t |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020-09-15 | −0.0485 | −0.51 | −0.0083 | −0.86 | −0.0193 | −2.29 | −0.0789 | −0.79 |
| 2021-09-15 | +0.0899 | +1.18 | +0.0150 | +1.62 | −0.0040 | −0.24 | +0.0599 | +0.68 |
| **2022-09-15** | **+0.1546** | **+3.37** | **+0.0258** | **+4.76** | +0.0148 | +1.10 | +0.1335 | +2.09 |
| 2023-09-15 | +0.0417 | +0.91 | +0.0141 | +2.04 | −0.0012 | −0.08 | +0.0112 | +0.36 |
| **2024-09-15 (REAL)** | **−0.0476** | **−0.90** | **−0.0055** | **−1.17** | −0.0270 | −1.42 | −0.0924 | −2.84 |

The fake 2022 date produces the largest apparent effect in the table, on both day metrics,
with `t` = +4.76 on the ramp. The real date produces the *smallest* `D1` and `D2`
coefficients of any date tried. This is the honest characterisation of what this estimator
can and cannot see, and it is the reason a small positive `T_post` in §4.4 must not be
read as a finding.

---

## 5. The chain's coupling structure — measured, and stable across the date

Hourly correlation of deviations after each balancing authority's own month-by-hour-of-day
profile is removed, averaged over that year's link-months:

| link | what it physically is | pre mean | pre SD | MDE | 2024 | z | 2025 | z |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **DOPD → CHPD** | Wells → Rocky Reach / Rock Island | **0.602** | 0.077 | 0.315 | 0.541 | −0.78 | 0.604 | +0.03 |
| **BPAT → DOPD** | Grand Coulee / Chief Joseph → Wells | **0.477** | 0.047 | 0.193 | 0.432 | −0.97 | 0.473 | −0.10 |
| **BPAT → GCPD** | the federal projects → Wanapum / Priest Rapids | **0.445** | 0.042 | 0.172 | 0.452 | +0.15 | 0.555 | +2.61 |
| **CHPD → GCPD** | Rocky Reach / Rock Island → Wanapum / Priest Rapids | **0.353** | 0.057 | 0.232 | 0.339 | −0.23 | 0.452 | +1.75 |
| PGE → PACW | two unconnected tributary systems | 0.211 | 0.056 | 0.226 | 0.267 | +1.00 | 0.259 | +0.86 |
| TPWR → PACW | ditto | 0.121 | 0.087 | 0.356 | 0.174 | +0.61 | 0.143 | +0.26 |
| PGE → TPWR | ditto | **0.027** | 0.086 | 0.349 | 0.131 | +1.21 | 0.112 | +0.99 |

And the lag at the cross-correlation peak, in hours: **BPAT → DOPD 2.97**, **DOPD → CHPD
2.73**, CHPD → GCPD 0.95, BPAT → GCPD 0.05 — against control pairs at 1.6, 1.2, −0.5 with
two to three times the year-to-year scatter. Every 2024 and 2025 reading is inside MDE.

**Two things follow, and only the first belongs to this lane.** The coupling did **not**
change across the termination. And, handed to NWPP-36 rather than acted on here: the
mainstem's hydraulic coupling is directly measurable from series already on disk, at
roughly **2.5–3× the correlation of unconnected tributary pairs**, with a **2–3 h lag on
the two upper links** that is stable across seven years. `FINDING-nwpp-32` §5(a) item 2
told NWPP-36 the lag *"is NOT published at mechanism precision … and it is NWPP-36's to
measure, not assume"*, and pointed at the USACE/CROHMS hourly outflow feed. That feed is
still the right source for **per-plant** τ; what this lane establishes is that a
balancing-authority-level estimate exists today for the three mid-Columbia links, is
stable, and is a free consistency check on whatever CROHMS yields. The caveat is stated
plainly: BPAT holds mainstem projects both *above* and *below* the mid-Columbia reach, so
its lag is a mixture and only the DOPD → CHPD figure is a clean two-plant link.

---

## 6. The test aimed at the instrument's own words

The PNCA's operative definition is **"Period means a calendar month"**. If a calendar-month
accounting period binds and then stops binding, the month *boundary* should stop being a
special place in the daily-energy series. That is the most instrument-specific thing
measurable here, so it was measured.

Statistic: daily energy normalised by a **centred 31-day rolling mean**, then
`mean |day-to-day step| on month-end days ÷ the same on days 11-19`. A value of 1.0 means
the boundary is not special at all.

**One construction trap, recorded because it nearly produced a false finding.** Normalising
each day by *its own calendar month's mean* — the obvious choice — injects a mechanical
step at every boundary whenever adjacent months differ in level, and inflates this ratio
from ≈ 1.2 to **2.5–4.0 in every balancing authority, including the pure tributary controls
that have no PNCA at all**. Read uncritically that is "a strong monthly accounting
signature everywhere"; it is an artifact of the denominator. The rolling normalisation
removes it, and the corrected numbers are:

| Jul–Dec half | pre mean | pre SD | MDE | 2024 | z | 2025 | z |
|---|---:|---:|---:|---:|---:|---:|---:|
| **BPAT** | 1.136 | 0.333 | 1.356 | 1.547 | +1.23 | 0.487 | −1.95 |
| **CHPD** | 1.008 | 0.523 | 2.131 | 1.166 | +0.30 | 1.472 | +0.89 |
| **DOPD** | 0.889 | 0.391 | 1.592 | 1.089 | +0.51 | 1.806 | +2.35 |
| **GCPD** | 1.529 | 0.446 | 1.816 | 1.125 | −0.91 | 0.876 | −1.47 |
| PGE | 1.511 | 0.506 | 2.062 | 1.772 | +0.52 | 1.624 | +0.22 |
| TPWR | 1.385 | 0.238 | 0.970 | 0.959 | −1.79 | 0.754 | −2.65 |
| PACW | 1.127 | 0.336 | 1.367 | 0.408 | −2.14 | 1.548 | +1.26 |

As a treated-minus-control DiD over the fourteen half-years, pre-period mean −0.219,
SD 0.426, MDE **±1.406**: 2024 H2 deviation **+0.404 (z +0.95)**, 2025 H1 **+0.204
(z +0.48)**, 2025 H2 **+0.070 (z +0.17)**. Nothing.

Two readings, both worth stating. **The calendar-month boundary was only ever weakly
special** — the corrected ratio sits at 0.9–1.5 against 1.0 for "not special", in the
coordinated and independent systems alike — which is itself information about how much the
model's monthly budget period is doing. And **whatever signature there was did not weaken
after the termination**; if anything the point estimates drift the other way, well inside
noise.

---

## 7. What is NOT explained by the PNCA, and is routed rather than absorbed

**SCL changed in 2024, and it is not this.** Seattle City Light is the one balancing
authority whose 2024 readings clear the detection threshold on shape: design B `D2`
z = **+5.41**, `D1` z = **+3.94**; design C `M2` z = **+4.39**, `D2` z = **+3.70**; and the
change persists into 2025 (`M2` z = +3.59, `D1` z = +2.49). **But it is a whole-year change
with nothing at the boundary**: its design-A contrast reads z = +0.03 and its local jump at
Sep 15 reads z = −0.57. A step that is present across all of 2024 and absent at 2024-09-15
is not a PNCA effect. SCL is 56.6 % Boundary (1,159.7 MW, Pend Oreille) and 43.4 % Skagit;
a plausible reading is a unit or licence-article change at one of them, and its FERC licence
P-2144 was the one instrument `FINDING-nwpp-32` §4 could not retrieve at pondage precision.
**Routed, not diagnosed here** — it is outside this lane's question and outside its files.

**PSEI's 2019-2020 `NG: WAT` is unusable** — 12,376 hours above 1.15 × nameplate, i.e. the
whole of both years. That is a source-side reporting defect two years wide, not the G20
spike class, and it is what removes PSEI from the control group. Worth a line in the R-f
inventory since it is the same column NWPP-37 is working on.

**The 2025 control-group swing is large and unexplained here.** PGE's ramp metric at −10.95
σ and PACW's at +4.82 σ are real movements in small tributary systems in a year this lane
did not set out to explain. They are reported because they set the noise floor the verdict
rests on, not because this lane understands them.

**None of the three is a mechanism proposal.** Under the charter and rule 1 `[R-STRUCT]`,
a future mechanism decision on any of them is the owner's.

---

## 8. Limits — what this lane cannot say

1. **A change smaller than ~20 % of a shaping metric is invisible here** (~45 % for
   within-month variability). A gradual or partial change in operating practice is not
   ruled out, and this lane does not claim it is.
2. **The post period is 15.5 months**, of which 2025 is the only complete year. A regime
   change that phases in over several years would not yet be visible. The measurement
   should be repeated when 2026 lands.
3. **Continuity of practice is a live possibility and would look identical to a null.**
   `FINDING-nwpp-32` §4 records that the 2026 White Book still has owners supplying BPA
   plant data and constraints. If the parties simply kept coordinating in substance after
   the agreement lapsed, this lane's null is the *correct* observation of that — but it
   cannot distinguish "the instrument never mattered for hourly shape" from "the practice
   continued without the instrument". Both imply the same thing for the model, which is why
   outcome (a) closes the item either way.
4. **Two of four treated balancing authorities are plant-pure; BPAT is not.** BPAT is 92.6 %
   coordinated but mixes eleven projects across the mainstem, the lower Snake, the
   Clearwater and the Kootenai, so a change confined to one project inside it would be
   diluted. DOPD (Wells alone) and GCPD (Wanapum + Priest Rapids) carry no such dilution and
   show nothing either.
5. **What would raise the power.** Per-plant hourly discharge from the USACE/CROHMS feed
   (`public.crohms.org`) would replace four balancing-authority series with fifteen project
   series and remove the BPAT aggregation entirely; that is the same source
   `FINDING-nwpp-32` §5(a) already routes to NWPP-36 for τ, so one fetch serves both. More
   pre-period years would help less than it sounds — EIA-930 per-fuel reporting begins in
   2018-2019, so at best two more, against an error term set by the number of years.

---

## 9. Rules

- **Rule 1 `[R-STRUCT]`** — the whole reason this lane is a measurement. No mechanism is
  proposed, nothing is tuned, no residual is consulted (NWPP has none), and the verdict was
  written to the pre-declared rule of §2.5 rather than chosen.
- **Rule 13 `[R-MEASURED]`** — every number is measured EIA-930 generation. Defective hours
  are dropped, never imputed; nothing is padded, rescaled or pinned.
- **Rule 23 `[R-FROZEN-DERIVE]`** — the 2019-2022 extension reuses
  `build_nwpp_ba_hourly_from_balance.py`'s construction verbatim and is verified at 0
  mismatched hours against the committed extract.
- **Rule 24 `[R-REGISTRY]`** — no `ScenarioConfig` field, no env-var knob, nothing that can
  change a solve. `check_mechanism_matrix.py --base 38ecbf0e` exits 0; the warnings it
  prints are pre-existing (NYISO keeper stamp drift, anchor line drift) and belong to other
  lanes. No matrix cell moves, per the charter.
- **Rule 27 `[R-PUSH]`** — one new source file ≥ 300 lines
  (`scripts/data/measure_nwpp_pnca_discontinuity.py`); pushed as exact on-disk bytes over
  `git push` and fetch-back verified (§ below).
- **Rule 32 `[R-SHARD]`** — zero LP. No shard launched, so rules 33 `[R-SHARD-ARCHIVE]` and
  34 `[R-SHARD-PROMOTABLE]` do not engage.
- **Rule 31 `[R-RETAIN]`** — nothing solved, so no promotion question fires. Nothing was
  deleted.
- **Collision rules** — one new FINDING, one new artifact README, three new artifacts, one
  new script. No shared record touched: not the plan, the ledger, the calibration log,
  CHANGELOG, the keeper/gates stamp, or `docs/mechanism-testing-matrix.md`.

**Gates run at `38ecbf0e`:** `ruff check` on the new script — clean;
`check_mechanism_matrix.py --base 38ecbf0e` — exit 0, no new-field registration required;
derive-vs-committed identity — 0 mismatched hours; screen counts reproduced above.
`scripts/regenerate_clean.py` (G22) was **not** run and is not needed: this lane adds no
loader, touches no `data/clean` datatype and runs no `tests/integration` or
`tests/curation` case — its only executable is the standalone measurement script, which
reads `data/raw` directly.

---

## Log entry

**NWPP-38 — PNCA-termination discontinuity: VERDICT (a), NO MEASURABLE CHANGE, with the
power stated.** Base `38ecbf0e` (the issuance's `02c08154` had been superseded; rebased per
collision rule 3). Zero LP. Fourteen scored shape tables across five designs — calendar-time DiD
whose window boundary is 2024-09-15, a ±28-day local RD at that date, seasonal-window and
full-year contrasts, the mainstem's own hourly coupling structure, and a month-boundary
test aimed at the PNCA's operative words *"Period means a calendar month"*. **None of the
56 treated cells (BPAT CHPD DOPD GCPD, 92.6–100 % coordinated-Columbia) reaches detection
in either post year; max |z| 2.45 (2024), 3.04 (2025) against a 4.07 threshold.** Nine of
42 *control* cells (PGE TPWR PACW, 100 % independent tributary) do — PGE's ramp metric at
−10.95 σ in 2025 — so the systems the PNCA never coordinated moved more than the one it
did. Month-panel DiD with a `log(level)` hydrology control: every 95 % CI spans zero, and
the control shrinks each point estimate by a third. The same estimator at a **fake**
termination date of 2022-09-15 returns a larger, more significant "effect" (`D2` t = +4.76)
than the real date (t = −1.17). **Power, stated rather than implied: ~20 % of a shaping
metric (45 % for within-month variability) is the floor, because treatment varies at the
year and there are seven years — not because of any shortage of hours.** Routed item 5 of
FINDING-nwpp-32 §7 therefore **CLOSES**: the declaration in NWPP-40's PRECOMMIT is
sufficient, no mechanism is proposed, and none is needed. Pre-period extended to 2019 by
re-deriving the per-BA hourly panel from the committed BALANCE archive — verified at **0
mismatched hours** against NWPP-11's extract over 26,303 h × 12 BAs. The mid-2024 EIA
taxonomy revamp, 2.5 months before the date, is closed by measurement (the pumped-storage
column is null in every NWPP hour) and by design (the primary contrast is within-taxonomy).
**NWPP-37 had not landed**, so the defective `NG: WAT` hours were screened in-lane
(drop, never impute; whole local day dropped) — result unchanged on EIA's `(Adjusted)`
column. **Handed to NWPP-36:** mid-Columbia hydraulic coupling is directly measurable today
— adjacent-link hourly r of deviations 0.35–0.60 vs 0.03–0.21 for unconnected control
pairs, with a stable 2–3 h lag on BPAT→DOPD and DOPD→CHPD — a free cross-check on the
per-plant τ that CROHMS is still the right source for. **Three items routed, none
diagnosed here:** SCL clears detection in 2024 (`D2` z +5.41) but as a whole-year step with
**nothing at the boundary** (jump z −0.57), so it is not PNCA — candidate is Boundary /
FERC P-2144, the one instrument NWPP-32 §4 could not retrieve; PSEI's 2019-2020 `NG: WAT`
is defective for **both entire years** (12,376 hours), one for the R-f inventory; and the
2025 tributary swing is large and unexplained. New files only: the FINDING,
`scripts/data/measure_nwpp_pnca_discontinuity.py`, three artifacts under
`data/raw/nwpp-hydro/` + their own README. No shared record touched, no matrix cell moved,
no `ScenarioConfig` field, NWPP-32's artifacts untouched.
