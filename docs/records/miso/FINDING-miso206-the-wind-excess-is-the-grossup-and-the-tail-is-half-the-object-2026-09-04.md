# FINDING miso-206 — the MISO wind excess is the curtailment gross-up and nothing else, REFUSED on the bound in the object's own hours; and the record repair shows the 15-hour tail is **half** of the C3a-2025 Jun–Jul object, not all of it (2026-09-04)

**Session:** miso-206, branch `claude/miso-wind-availability-backcast-yr4i67`.
**Keeper at open AND at close: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2, n_residual 2).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`. NO SCORING ARTIFACT CHANGED. NO CELL VERDICT MOVED** (one new base
row minted for an existing unregistered construction, §10).

**PREREG** `results/calibration/PREREG-miso206-wind-availability-object-hours-2026-09-04.md`,
pushed at **`f55af87f`** before any object-hour statistic, with a §0 disclosure
of the two numbers the instrument pre-condition had already produced, three
reproduction pre-conditions, ten predictions each carrying a sign against its
own normal population, a magnitude rule (P6) with a mechanism rule beside it
(P7), five record-repair rules, and eight traps with counter-measurements.

**Instruments** `scripts/probes/_miso206_wind_availability_phase0.py` (record
`_miso206_wind_availability_phase0.json`); the repaired
`scripts/probes/_miso202_c3a_2025_anatomy.py` and
`scripts/probes/_miso203_scarce_hour_identity.py` (records regenerated in place,
pre-repair blocks preserved under `pre_repair_defective_clock`).

---

## 1. Headline

1. **The instrument reproduces production exactly.** The measured MISO wind,
   rebuilt independently from the raw `EIA930_BALANCE` bulk files on the
   model's fixed-CST clock, matches the production loader at
   **max|diff| = 0.0 MW on every hour the archive carries**, in all three years
   (§3). The production wind BOUND equals `EIA-930 delivered ÷ (1 − 0.048947)`
   at **0.0000 MW in 8,760 / 8,760 hours** of every year, and the keeper's P1
   wind sits **on** that bound in every one of them — endogenous curtailment
   **0.0 MWh**, ratio model/measured **1.051466 in every hour** (min = max).
2. **The standing "~+5 TWh/yr" wind excess is the Potomac reference-rate
   gross-up and nothing else**: **+4.720 / +5.057 / +5.092 TWh** (2023/2024/2025),
   a constant **5.15 %** of the measured series in every hour of the year. It is
   a LEVEL object that lives in every hour equally; it has no shape and no
   scarce-hour concentration.
3. **In the C3a object hours the excess is 262 / 285 / 251 MW** — **0.6 / 0.7 /
   0.8 %** of miso-203 G-D's broad reserve margin and **1.7 / 2.4 / 4.5 %** of the
   armed-class idle. **Even removing ALL model wind in those hours** (5,359 /
   5,822 / 5,120 MW) reaches only **12.5 / 15.2 / 16.8 %** of the margin — under
   the 25 % licensing line in every year. At the largest hour of 2025
   (`07-28 HE18`, actual $1,782.55 vs model $161.39) the excess is **175 MW**.
   **REFUSED. DEAD, like the ambient derate. No solve spent** (§6–§7).
4. **The wind DEFICIT in the object's hours is a measured fact, not a model
   error**: the EIA-930 series itself sits at hour-of-day-matched **p54.5 / p36.1 /
   p36.5** there, and the model's ranks are identical to the digit because its
   wind is a constant multiple of the measurement. The "low-wind set" is what
   MISO's wind did; the model reproduces it plus 5 %. Solar, the control, is
   identical to the measurement in every object hour (diff **0.0 MW**).
5. **THE SECOND DELIVERABLE PRODUCED THE SESSION'S RESULT.** Routing the two
   wrong-clock records through the C3a comparator (INDIANA.HUB on the model
   clock) reproduces miso-205 exactly (R-2 max|diff| **0.0**; R-3 import excess
   **3,673.0** vs miso-205's 3,673.3) — and **R-4 FAILS against prediction**: on the
   series C3a is scored against, the top-1 % hours carry **48.4 %** of the Jun–Jul
   2025 mean gap, not the **99.9 %** miso-202 §2 published and every session since
   has quoted. The pre-repair "entirely a tail" reading was an artifact of the
   eight-hub equal-weighted basis, which sits **$8.7/MWh BELOW INDIANA.HUB and
   $7.1 below MISO's own system energy price** across Jun–Jul 2025, cancelling
   the body of the gap and leaving only the 15 hours (§8).
6. **What the Jun–Jul 2025 object actually is, on the C3a comparator**: a mean
   gap of **−13.44 $/MWh** (load-weighted model 39.96 vs INDIANA.HUB 53.40;
   system energy price 51.81, so **88 % of it is energy**, not hub basis). By
   band of the actual price: the lower half of hours is **over-priced (+3.71)**,
   p50–75 flat (−0.15), the **p75–p99 shoulder (351 h) carries −10.71 = 80 %**,
   and the **p99+ tail (15 h) carries −6.30 = 47 %**. The top decile carries
   **110 %** of the net gap. By hour of day, the body gap (the 1,449 non-tail
   hours) is **+8 to +9 overnight (h00–h03)** and **−14 to −24 across h11–h20** —
   i.e. miso-130's two-sided July diurnal compression, now measured on the
   scoring comparator. **"C3a-2025 is not closable by anything that moves the
   price LEVEL" survives only as "not by a UNIFORM level move"** — a daytime
   shoulder that is under-priced for ten hours a day for 61 days is not a
   15-hour tail, and no lever aimed at 15 hours can reach 80 % of the gap.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **N-1** BALANCE rebuild reproduces production *(PRE-CONDITION)* | **PASS on every archive-carried hour, all three years** — max\|diff\| 0.0 / 0.0 / 0.0 MW, r = 1.000000 at k = 0. **TRAP 1 FIRED on the first run and was diagnosed** (§3.1) |
| **N-2** bound ≡ delivered/(1−r), P1 on the bound *(PRE-CONDITION)* | **PASS** — 0.0000 MW; 0 curtailed hours; ratio 1.051466 min = max, every year |
| **N-3** object set reproduces miso-205 *(PRE-CONDITION)* | **PASS** — thresholds 121.43 / 159.01 / 373.02; 2025's 15 stamps exact; 0 object hours in any archive hole |
| **P1** excess by hour set = 0.048947 × model wind | **RIGHT** — OBJ 262.3 / 285.0 / 250.6 (pred. 262 / 285 / 251); top-15 359.8 / 281.8 / 281.8 (360 / 282 / 282); Jun–Jul 297.5 / 416.6 / 390.0 (298 / 417 / 390) |
| **P2** measured ranks identical to the model's | **RIGHT** — Jun–Jul p45.5 / p34.5 / p32.4, h-o-d p54.5 / p36.1 / p36.5, to the digit |
| **P3** sign vs own h-o-d population | **RIGHT** — 2024/2025 BELOW (p36.1 / p36.5 < 40); 2023 ORDINARY (p54.5 ∈ [45, 60]) |
| **P4** solar control | **RIGHT** — diff 0.0 MW in 15/15 hours every year; 2025 h-o-d p48.1 |
| **P5** annual excess | +4.720 / +5.057 / **+5.092** (PREREG §0 read +5.096 off the bench's `e930.wind`; the production loader's own annual sum is 98.941 TWh, 3 GWh above the bench's strict-frame 98.938 — the ffilled last hour, §3.3) |
| **P6 THE BOUND** | **RULE FIRES, every year** — 0.0061 / 0.0074 / 0.0082 of the broad margin; total removal 0.1254 / 0.1517 / 0.1677 < 0.25 |
| **P7 mechanism rule** | **NOT an availability object** — 0.0261 / 0.0153 / 0.0105 of the net-load elevation, vs the 0.10 line |
| **P8** headroom liveness | 0 curtailed hours in Jun–Jul, 0 in the object, 0 hours with model price ≤ 0 |
| **P9** form defect named, not chartered | done (§7) |
| **P10** verdict REFUSED, nothing armed | **RIGHT** |
| **R-0** clock repair leaves a0/a1/a3 byte-identical | **PASS** (then a SEPARATE, disclosed month-mask repair moves 2024 slightly, §8.1) |
| **R-1** thresholds / stamps | **PASS** |
| **R-2** identity reproduces miso-205's drivers | **PASS, exact (0.0 in every driver, every year)** |
| **R-3** anatomy a4 import within ±150 MW of +3,673.3 | **PASS** — 3,673.0 |
| **R-4** repaired tail share ≥ 0.95 | **FAIL — 0.4835.** The session's result (§8) |
| **T2** the 2025 extract's missing hour | **AS PREDICTED**: `2025-12-31 HE24`, production ffills 15,164 MW where the archive measures 13,588; outside Jun–Jul |
| **T3** "with Integrated Battery Storage" wind | 0.0 MW in every year |
| **T4** leap-year 2024 | N-1/N-2 hold on the Jun–Jul 2024 hours (max\|diff\| 0.0) |

---

## 3. The instrument — what asserting it against production turned up

### 3.1 TRAP 1 fired: the BALANCE file's MISO "Data Date" is an EST label

The first rebuild keyed the local year on the archive's own `Data Date` /
`Local Time at End of Hour` columns and reproduced production at **r = 1.000000
only at a one-hour lag** (k = +1; 0.989 at k = 0; 8,756 of 8,760 hours differing).
Joined at identical UTC stamps the two sources are **byte-identical** (wind and
demand diff 0.0), so the discrepancy is entirely a label: for MISO the archive's
local columns are **EST** (MISO's market time; UTC − 5 all year, 24 hours on every
day), while the model's calendar, the C3a scoring reference and the production
renewable frame for 2022–2025 are **fixed CST** (UTC − 6). Re-keyed on
`UTC − 6 h` the rebuild reproduces production exactly. Anyone building a MISO
hourly series from the BALANCE archive must key on UTC, never on its date columns.

### 3.2 The committed extract's own labels are vintage-inconsistent (NAMED)

`data/raw/eia-930-hourly/MISO hourly.parquet`: rows for **2018–2021 and 2026**
(BALANCE-sourced) carry EST labels and their local year starts at **UTC 06:00**;
rows for **2022–2025** (API-sourced) carry America/Chicago labels and the year
starts at **UTC 07:00** (fixed CST). The training years are on the model's clock.
The **2019–2021 touchpoint years would load demand and renewables ONE HOUR EARLY**
against the CST-converted LMP reference. Named, not chartered — rule 22: those
years are not solvable for MISO, and the fix belongs to the extract builder.

### 3.3 Two archive holes and one production fill, all outside the object

| year | BALANCE archive hole (wind column) | extract missing hour (production fills) |
|---|---|---|
| 2023 | none | none |
| 2024 | `06-30 HE24` – `07-01 HE23` (24 h, the H1/H2 file seam) | none |
| 2025 | `07-24 HE01` – `HE23` (23 h) | `12-31 HE24` — ffilled 15,164 MW vs measured 13,588 |

The production extract carries measured values through both holes; the object
hours (15 per year) intersect neither. The 2025 fill is what puts the loader's
annual wind 3 GWh above the bench.

---

## 4. Deliverable (a) — levels and ranks, per year

Model P1 wind vs EIA-930 measured wind (MW, means over the set), the excess, and
the measured series' percentile within Jun–Jul and hour-of-day matched. The
model's ranks are omitted because they are identical to the measured ones (P2).

| year | set | model wind | measured | **excess** | meas. pct Jun–Jul | meas. pct h-o-d | model solar − measured |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | OBJ (15 h) | 5,359 | 5,097 | **262** | p45.5 | **p54.5** | 0.0 |
| 2023 | top-15 gross load | 7,350 | 6,990 | 360 | — | p68.6 | 0.0 |
| 2023 | all Jun–Jul | 6,078 | 5,780 | 298 | — | — | 0.0 |
| 2024 | OBJ | 5,822 | 5,537 | **285** | p34.5 | **p36.1** | 0.0 |
| 2024 | top-15 gross load | 5,758 | 5,476 | 282 | — | p38.6 | 0.0 |
| 2024 | all Jun–Jul | 8,512 | 8,096 | 417 | — | — | 0.0 |
| 2025 | OBJ | 5,120 | 4,870 | **251** | p32.4 | **p36.5** | 0.0 |
| 2025 | top-15 gross load | 5,758 | 5,476 | 282 | — | p36.7 | 0.0 |
| 2025 | all Jun–Jul | 7,969 | 7,579 | 390 | — | — | 0.0 |

The excess is **5.15 % of whatever the wind is** — larger in the windy Jun–Jul
mean than in the low-wind object hours. There is no hour set in which the model
holds more wind than 1.0515 × the measurement, and none in which it holds less.

The measured wind deficit in the object hours against the Jun–Jul mean is
**684 / 2,558 / 2,709 MW** — the 719 / 2,690 / 2,848 miso-205 reported for the
model, deflated by the same 5 %.

---

## 5. Deliverable (b) — the annual excess

| year | model P1 wind | EIA-930 wind | **excess** | model / measured |
|---|---:|---:|---:|---:|
| 2023 | 96.435 TWh | 91.715 | **+4.720** | 1.05147 |
| 2024 | 103.308 | 98.251 | **+5.057** | 1.05147 |
| 2025 | 104.034 | 98.941 | **+5.092** | 1.05147 |

Confirmed: the standing figure is the reference-rate gross-up `1 / (1 − r)`,
`r = 0.048947` (Potomac Economics SOM, firm 2023 + 2024 rows), applied by
`_forecast_uncurtailed_cf` and never taken back by the LP. Solar's bound equals
its delivered series exactly (max|diff| 0.0000) and P1 solar sits on it.

---

## 6. Deliverable (c) — THE BOUND, pre-committed and then measured

Margins READ from `_miso203_summer_peak_anchor_phase0.json::g_d_reserve_binding`;
ceiling from `_miso202_c3a_2025_anatomy.json::a3_ceiling` (Jun–Jul model max
$183.22, 0.0 MWh unserved, ORDC shortfall 3 h of 8,760 — unchanged).

| year | OBJ excess | broad margin (min) | excess / margin | armed idle | excess / armed | total-removal ceiling | ceiling / margin | line |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 262 MW | 42,736 | **0.6 %** | 15,789 | 1.7 % | 5,359 | 12.5 % | 25 % |
| 2024 | 285 | 38,375 | **0.7 %** | 11,752 | 2.4 % | 5,822 | 15.2 % | 25 % |
| 2025 | 251 | 30,533 | **0.8 %** | 5,621 | 4.5 % | 5,120 | 16.8 % | 25 % |

**The 2025 object, hour by hour** (measured percentiles of the EIA-930 wind):

| CST stamp | actual | model_lw | model wind | measured | **excess** | pct Jun–Jul | pct h-o-d | solar (model = measured) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 06-17 HE18 | 543.2 | 49.5 | 5,057 | 4,809 | 248 | 33.2 | 41.0 | 5,678 |
| 06-23 HE18 | 838.9 | 85.3 | 9,913 | 9,428 | 485 | 72.5 | 73.8 | 6,651 |
| 06-23 HE19 | 1,046.7 | 127.6 | 7,484 | 7,118 | 366 | 54.4 | 59.0 | 2,241 |
| 06-24 HE11 | 382.7 | 52.8 | 4,870 | 4,632 | 238 | 31.3 | 44.3 | 10,454 |
| 06-24 HE12 | 406.3 | 58.5 | 4,081 | 3,881 | 200 | 22.7 | 27.9 | 10,498 |
| 06-24 HE16 | 390.1 | 64.6 | 3,240 | 3,081 | 159 | 15.3 | 16.4 | 7,881 |
| 06-24 HE17 | 451.4 | 64.6 | 3,344 | 3,180 | 164 | 16.3 | 14.8 | 7,020 |
| 06-24 HE18 | 1,202.0 | 64.6 | 3,200 | 3,043 | 157 | 14.8 | 18.0 | 5,344 |
| 06-24 HE19 | 775.0 | 68.5 | 3,104 | 2,952 | 152 | 13.8 | 18.0 | 1,911 |
| 07-15 HE16 | 413.3 | 50.6 | 6,863 | 6,527 | 336 | 48.5 | 50.8 | 9,741 |
| 07-22 HE18 | 643.7 | 48.3 | 8,475 | 8,060 | 415 | 62.1 | 59.0 | 7,954 |
| **07-28 HE18** | **1,782.5** | **161.4** | 3,581 | 3,406 | **175** | 18.4 | 21.3 | 7,668 |
| 07-28 HE19 | 683.2 | 183.2 | 4,080 | 3,880 | 200 | 22.7 | 31.1 | 2,212 |
| 07-28 HE20 | 388.7 | 97.5 | 4,529 | 4,307 | 222 | 27.7 | 34.4 | 46 |
| 07-30 HE14 | 826.9 | 44.9 | 4,984 | 4,740 | 244 | 32.5 | 37.7 | 8,257 |

Six of the fifteen — including the year's largest hour — are genuinely
low-wind for the time of day (h-o-d p14–p21); the 06-24 block is a four-hour
run at 3.0–3.3 GW of measured wind. The model has those hours right to within
150–165 MW. **Note against the story**: the two highest-priced June hours
(06-23 HE18/HE19, $839 / $1,047) are HIGH-wind hours (p74 / p59) — the object is
not uniformly a low-wind set even in 2025.

---

## 7. Deliverable (d) — the verdict, and the form defect NAMED

**REFUSED on the bound (P6, every year, by two orders of magnitude on the
excess and by 8–13 pp even at total removal), and not an availability object
on the mechanism rule (P7: 1.0–2.6 % of the net-load elevation).** Nothing is
armed, no field is created, no LP is spent. The cell for the construction is
minted `K` in MISO with this evidence (§10), because the construction is live in
every MISO keeper; the *lever* — re-shaping or removing its headroom in the
object's hours — is dead and gets no cell.

**P9, the form defect, NAMED and not chartered.** The gross-up applies one
annual rate to every hour, so it places 4.9 % of curtailment headroom in hours
where real curtailment is essentially zero (curtailment is a low-price,
congested-hour phenomenon; the object hours price at $380–1,780). In those hours
the headroom is phantom supply of exactly the size measured above. The correct
form is a price- or congestion-conditioned rate (rule 14's reconciled-data
clause: the annual aggregate is the only published measurement, and it is
misaligned to the hourly grain). Two facts keep it a defect and not a lever: (i)
by P6 no form can reach the marginal stack in the object hours; (ii) the LP
never exercises the headroom anywhere (0 curtailed hours in 8,760 × 3), so what
the gross-up actually does in this keeper is add a flat **+5.1 TWh/yr** of wind
that displaces thermal energy in every hour equally — a LEVEL bias in the wind
class (C1 wind is advisory-only, so it is not gated) and a small downward
pressure on the annual price level. That is owned by nobody's scarce-hour
charter and by rule 1 is not to be tuned against a residual.

---

## 8. The record repair — and what it found

Both generator probes now read the committed `actual_lmp_hourly_zonal_MISO.parquet`
(`INDIANA.HUB`, `rt`), the series C3a is scored against, on the model's clock;
their pre-repair hour-matched blocks are preserved inside each record under
`pre_repair_defective_clock`. The identity record's repaired `scarce_hours`
drivers reproduce miso-205's `obj_hours_REPAIRED` **exactly** (R-2), its
model-driver blocks are byte-identical (R-0), and the anatomy's annual blocks are
byte-identical under the clock step (R-0). The seam row, repaired: import excess
**1,477 / 1,850 / 3,673 MW** (pre-repair 2,008 / 1,684 / 3,844); the anatomy's
2025 solar row flips sign exactly as miso-205 §7 reported (−2,808.5 → +1,614.4).

### 8.1 A second, separate defect in the anatomy probe (disclosed)

Its month mask came from `pd.date_range(f"{year}-01-01", periods=8760)`, which in
a leap year carries Feb 29 and labels every model hour after Feb 28 one day
early — the 2024 "Jun–Jul" window ran May 31 00:00 – Jul 30 23:00 on the model
clock (`a1` too). Repaired to the fixed non-leap clock AFTER R-0 was scored on
the clock-only step; 2023/2025 unchanged, 2024 moves: a1 Jun–Jul share
0.6145 → 0.6198, a2 mean gap −3.859 → −3.642, top-1 % share 0.770 → 0.816, a4
import excess 1,809.4 → **1,850.2** (miso-205: 1,850.4 — the two instruments now
agree to 0.2 MW).

### 8.2 R-4 FAILS: the 15-hour tail is half the Jun–Jul 2025 object

A-2 on the C3a comparator (model zone-mean, the block's own basis):

| year | actual mean | model mean | mean gap | top-1 % contribution | **share** | pre-repair share (8-hub, EST clock) |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 31.76 | 32.17 | +0.42 | −1.55 | *(model over-prices the body, under-prices the tail)* | −0.46 |
| 2024 | 33.25 | 29.60 | −3.64 | −2.90 | **0.80** | −2.95 |
| 2025 | **53.40** | 39.88 | **−13.53** | **−6.54** | **0.48** | **0.999** |

**Why the published number was 99.9 %.** The pre-repair actual was the
eight-hub equal-weighted mean, whose Jun–Jul 2025 mean is **44.67** — $8.7 below
INDIANA.HUB and **$7.1 below MISO's own system energy price (51.81, miso-204's
record)**, because the equal-weighted hubs carry large negative congestion in
summer (miso-204 G-1 measured it: OBJ mean MCC −108.8). That basis cancelled the
body of the gap and left the tail. INDIANA.HUB, by contrast, sits **$1.6 above
the system energy price** in Jun–Jul 2025 — so on the C3a comparator the Jun–Jul
object is **88 % energy price**, and the hub-basis wedge the owner's item 5
carries annually (+$2.44) is a small part of the summer object.

### 8.3 A-2b — where in the distribution the gap lives (post-hoc, no gate)

Contribution of each band of the ACTUAL Jun–Jul price to the mean gap
(`Σ(model − actual)/n`, so the bands sum to the gap); model load-weighted,
actual INDIANA.HUB:

| year | p0–50 | p50–75 | p75–90 | p90–95 | p95–99 | **p99–100** | mean gap | top-decile share |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | **+3.80** | +0.83 | −0.19 | −0.61 | −1.88 | −1.49 | +0.45 | — |
| 2024 | **+3.14** | +0.77 | −0.70 | −1.13 | −2.72 | −2.90 | −3.53 | 1.91 |
| 2025 | **+3.71** | −0.15 | **−2.23** | **−2.65** | **−5.83** | **−6.30** | **−13.44** | **1.10** |

Same year on the hub-error-only twin (eight hubs, model clock): +4.31 / +1.09 /
−0.63 / −1.29 / −3.59 / −4.60, gap −4.71 — the shoulder shrinks by 70 % and the
tail by 27 %, which is the whole difference between the two readings.

Three things the table says, all three years:

* **The model over-prices the lower half of summer hours** by +$3–4/MWh of
  mean-gap contribution, every year. That is the overnight overshoot
  (h00–h03: +7.7 / +8.9 / +8.6 in 2025) miso-130 measured at the July grain.
* **The gap opens at p75, not p90.** In 2025 the p75–p99 shoulder — 351 hours —
  carries **−10.71**, 80 % of the net gap; the p99+ tail carries **−6.30**, 47 %.
  A lever that reaches only the 15 hours reaches less than half of it.
* **The body gap is diurnal.** 2025, load-weighted model vs INDIANA.HUB, the
  1,449 non-tail Jun–Jul hours by hour of day: h00 +7.7, h01 +8.9, h02 +8.6,
  h03 +4.8, h08 −6.7, h10 −10.0, h11 −13.6, **h12 −19.7, h13 −19.7**, h14 −13.8,
  h15 −15.7, h16 −18.0, **h17 −23.7**, h18 −19.5, h19 −18.7, h20 −17.5, h21 −0.9.
  2024 has the same shape at a third of the amplitude (h15 −14.6, h01 +6.9).

**What this corrects, and what it leaves standing.** miso-202 §2's "*entirely
a TAIL miss … the top 1 % of actual hours — 15 hours — carry 99.9 % of the mean
gap; the other 1,449 contribute −0.00*" is **withdrawn** as an instrument
artifact; the §5.4 header and the miso-206 charter's binding clause
("*C3a-2025 IS NOT CLOSABLE BY ANYTHING THAT MOVES THE PRICE LEVEL*") inherit
the correction: **not by a UNIFORM level move** (the lower half is already too
high), but the object is a **top-decile, daytime shoulder plus a 15-hour tail**,
and the shoulder is the larger half. What stands: miso-204's G-1 (the tail is
ENERGY — and so is the shoulder, §8.2); miso-205's drivers (unchanged, R-2
exact); the model's ceiling ($183.22, 0 unserved); the ordering of the object
hours. **The lane has spent four sessions bounding levers against a 15-hour
object that is half the object.**

---

## 9. My prior, scored against interest

| # | prediction | conf. | measured | verdict |
|---|---|---:|---|---|
| P1 | excess = 0.0489 × model wind, by set | 0.97 | to ±0.4 MW | **RIGHT** (identity) |
| P2 | ranks identical | 0.97 | identical | **RIGHT** (identity) |
| P3 | 2024/25 BELOW h-o-d normal; 2023 ORDINARY | 0.85 | p36.1 / p36.5; p54.5 | **RIGHT** |
| P4 | solar control identical | 0.95 | 0.0 MW, 15/15 | **RIGHT** |
| P6 | bound refuses, every year | 0.95 | 0.6–0.8 %; 12.5–16.8 % at total removal | **RIGHT** |
| P7 | not an availability object | 0.90 | 1.0–2.6 % | **RIGHT** |
| P8 | 0 curtailed hours | 0.95 | 0 | **RIGHT** |
| P10 | nothing armed, no LP | 0.95 | nothing, none | **RIGHT** |
| R-0..R-3 | repairs reproduce | — | exact / 0.3 MW | **RIGHT** |
| **R-4** | repaired tail share ≥ 0.95 | — | **0.4835** | **WRONG — the result** |
| T1 | clock trap: rebuild at 0.0 | — | fired, EST label, diagnosed, then 0.0 | **half-right** |
| T2 | 2025 missing hour = 12-31 HE24 | — | exactly | **RIGHT** |

**Read honestly: P1–P8 were arithmetically determined by the §0 identity and
were never at risk** — the PREREG said so. The two live questions were P6/P7
(right, and never close) and the record repairs, where **the one prediction I
wrote about the inherited characterisation (R-4) was wrong**, and it was the
only line in the PREREG that tested a prior session's headline rather than my
own construction. **That is now FIVE consecutive MISO sessions whose most useful
output came from the part of the prior that was wrong or absent.** The discipline
the charter asked for — a mechanism rule beside every magnitude rule, signs
against own populations — held; what it did not cover is *re-testing the
inherited object statement itself on the repaired instrument*. R-4 did that
almost by accident, as a robustness check on a repair. **The successor's
discipline: when an instrument is repaired, re-score every headline the old
instrument produced, and pre-register each as a claim that may fail.**

Two things found that no line predicted: the BALANCE archive's EST labelling
(§3.1) and the anatomy's leap-year month mask (§8.1). Both are instrument
defects that would have silently mis-keyed any future MISO hour-matched work.

---

## 10. What this licenses — nothing armed, and the re-aimed queue

**No lever is licensed and none is proposed.** PREREG §6's stop rule applied:
P6 fired and P7 read NOT an availability object, so the branch is refusal.

1. **Queue item 1 is DISCHARGED and REFUSED.** The wind-availability object in
   the object's hours is 251 MW against a 30.5 GW margin; the +5 TWh/yr excess
   is a flat 5.15 % level construction with no scarce-hour concentration. The
   construction gets a base row and a `K` cell in MISO (it is live in the
   keeper); its form defect (P9) is named in the row. **DO NOT RE-OPEN** without
   a form that is price-conditioned AND an argument for how ~250 MW reaches a
   $1,000 hour.
2. **THE OBJECT IS RE-CHARACTERISED, and this outranks every other queue
   item until absorbed.** On the C3a comparator the Jun–Jul 2025 gap is
   −13.44 $/MWh, 88 % energy; the 15-hour tail is **47 %** of it and the
   **p75–p99 daytime shoulder is 80 %** (the lower half is over-priced +28 %).
   Every bound argued "at the object's own hours" since miso-202 (miso-203
   G-D, miso-205, this session's P6) was argued against the tail half only.
   The **shoulder half is a DIFFERENT population**: 351 hours, h10–h20, actual
   $60–370, model $44–69, the diurnal compression object (`diurnal_price_amplitude`
   cell **G** on miso-89 / miso-114 / miso-130 grounds — this is NEW EVIDENCE
   about its WEIGHT in the scored residual, not a re-test of the cell, and it
   is raised, not re-opened). Any successor lever is to be bounded against BOTH
   populations, and a lever that reaches the shoulder is worth more than one
   that reaches the tail.
3. **Queue item 5 (the single-hub comparator, OWNER) gains a datum that cuts
   both ways**: annually INDIANA.HUB carries +$2.44 over the system MEC
   (miso-204), but in Jun–Jul 2025 only **+$1.6**, while the eight-hub mean the
   lane had been reading sits **$7.1 BELOW the MEC**. The summer object is not a
   locational artifact; the annual wedge lives mostly outside summer. Owner item,
   not acted on.
4. **Queue item 2 (the D-2 5(i) seam object)** — now re-measured on the
   corrected anatomy at **+3,673 MW** (2025), +1,850 (2024, agreeing with
   miso-205 to 0.2 MW), +1,477 (2023). Still model-side descriptive; the
   admissibility ruling is outstanding. Unchanged in status.
5. **Queue item 3 (a ramp product)** — the shoulder finding is a further
   objection: an h10–h20 under-pricing of ten hours a day is not a ramp window.
6. **Three instrument defects NAMED, not chartered**: (i) the BALANCE archive's
   MISO date columns are EST (§3.1) — key on UTC; (ii) the committed extract's
   2018–2021/2026 rows are EST-labelled while 2022–2025 are CST (§3.2) — the
   touchpoint years load one hour early; (iii) `pd.date_range`-derived month
   masks are a leap-year trap in every probe that uses them (§8.1) — the
   miso-205 `_hour_month` construction is the correct form.

---

## 11. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, no run to register (the miso-131…139
/ miso-179 / miso-194 / miso-203 / miso-204 / miso-205 zero-solve precedent).
Keeper unchanged at `2026-09-03-miso-202-unitclip`.
**Rule 28(b)/(c) `[R-MECH-MATRIX]`** — base row `vre_reference_rate_curtailment_grossup`
minted for an existing unregistered construction (no `ScenarioConfig` field
added), with a cell in all six shards: MISO `K` carrying this evidence; ERCOT
and CAISO `.` (HSL-covered, dormant); PJM/NYISO/NEISO `.` (delivered profile).
No other ISO verdict taken (rule 28(d)). `diurnal_price_amplitude` carries an
amended evidence citation in MISO's shard only; its `G` is untouched.
**Rule 28(a)** — no `R`/`I`/`G` cell re-tested or re-opened.
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; the 2019–2021 label defect is
named from the extract's metadata, no out-of-training year read or scored.
**Rule 13 `[R-MEASURED]`** — inputs are production loaders, committed sidecars
and committed prior records, read as a diagnostic; nothing enters a solve.
**Rule 1 `[R-STRUCT]`** — no residual moved; nothing armed.
**Rule 25** — only MISO's shard carries a verdict; the other five carry the
rule-28(c) cell line only.
**Rule 27 `[R-PUSH]`** — three probe files edited locally (one new; the anatomy
probe crosses 300 lines with A-2b and is blob-verified after push); no ≥300-line
file rewritten from response content.
