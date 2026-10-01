# FINDING miso-205 — miso-203's G-E, re-done on the repaired clock: the object's **mechanism story inverts** — solar is ABOVE normal in the object's hours, the renewable anomaly is WIND, and the dominant driver is plain LOAD (2026-09-03)

**Session:** miso-205, branch `claude/miso-203-ge-repaired-clock-7jdcxd`.
**Keeper at open AND at close: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2, n_residual 2).

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER
`data/raw/`. NO SCORING ARTIFACT CHANGED. NO CELL VERDICT MOVED.**

**PREREG** `results/calibration/PREREG-miso205-ge-repaired-clock-2026-09-03.md`,
pushed at **`fc8006d9`** BEFORE any adjudicating statistic, with two reproduction
pre-conditions, four charter gates, a location re-check, a seam re-measurement,
**seven claim-by-claim decision rules fixed in advance**, ten predictions **each
carrying a direction as well as a magnitude**, and eight traps with pre-committed
counter-measurements.

**Instrument** `scripts/probes/_miso205_ge_repaired_clock.py`; record
`results/calibration/_miso205_ge_repaired_clock.json`.

---

## 1. Headline

miso-204 established that miso-203's driver characterisation was computed on a
misaligned hour set and was therefore **unmeasured** — neither re-affirmed nor
refuted. Measured now, on the series C3a is actually scored against:

1. **The instrument reproduces exactly.** N-1: the object set's mean hour-of-day
   is **11.67 / 15.73 / 15.87**, its h18–h21 counts **1 / 3 / 4** and h15–h18
   counts **1 / 9 / 11** — miso-204 §6.5 to the digit — and the 2025 set's 15 CST
   stamps match §6.4's table **exactly**. N-2: the top-15 gross-load comparison
   set reproduces miso-203's committed driver row **exactly** in all three years,
   so the contrast is like-for-like.
2. **Four of miso-203 §8's seven testable claims SURVIVE, one is knife-edge, one
   is MARGINAL, and one is REFUTED** — and the refuted one is the mechanism.
3. **THE MECHANISM STORY INVERTS. Solar does not collapse in the object's hours;
   it is ABOVE normal.** miso-203 reported solar at **1,859 MW** against a
   Jun–Jul mean of 4,639. On the repaired hours it is **6,237 MW** — **+34 %
   above** the Jun–Jul mean, and above it in **11 of the 15 hours**. Decomposing
   the net-load elevation over the Jun–Jul mean, solar's contribution **flips
   sign**: miso-203's construction attributed **+11.5 %** of the elevation to a
   solar deficit; the repaired instrument measures **−6.7 %** — solar is *holding
   net load down* in exactly those hours.
4. **The renewable anomaly is WIND, and even that is secondary.** Hour-of-day
   matched (the diurnal cycle removed, so "low for the time of day" is what is
   measured), 2025 solar sits at **p48.1** — statistically ordinary — while wind
   sits at **p36.5** and load at **p83.4**. The net-load elevation is
   **94.8 % load, +11.9 % wind deficit, −6.7 % solar surplus**. Same signs in all
   three years (load 105.1 / 89.8 / 94.8 %, wind +7.2 / +14.5 / +11.9 %, solar
   **−12.2 / −4.3 / −6.7 %**).
5. **The location argument SURVIVES at full strength — the peak-load argument
   does not.** G-E: the object hours sit **BELOW** the summer peak-demand rating
   condition in **18 of 18 zone-years**, 2025 mean gap **−2.11 °C**. But the load
   claim weakens materially: load percentile rises **p88.4 → p92.8**, the
   top-15-load overlap goes **0 → 1**, and **the single largest hour of 2025
   (2025-07-28 HE18, actual $1,782.55 against a model $161.39) sits at load
   p99.3, net load p99.8 and dry-bulb p96.9** — with solar at 7,668 MW, well
   above normal. The charter's binding constraint must be narrowed from *"heat or
   peak load"* to **"heat"**.
6. **The seam number survives the repair and is now quoted on the right hours:
   import excess `+3,673.3 MW`** (2025), against the `+3,844.4` measured on the
   defective set — a **4.4 %** revision. CT_PEAKER **+8,911.7**, ST_GAS
   **+2,755.6**, COAL_PRB **+2,198.3**, wind **−2,877.9**, solar **+1,614.4**.
   Model-side descriptive, exactly as miso-202 labelled it; it licenses nothing.
7. **2023 and 2025 are not the same phenomenon.** The 2023 object is a **midday**
   set (mean hour 11.7, ten distinct days) sitting at only **load p75.4 / net
   load p73.3 / dry-bulb p66.0** — its largest hour, 2023-07-07 HE13 at $354.91,
   is a p73.6-load hour. The 2025 object is a **late-afternoon, near-peak** set at
   p92.8 / p95.6 / p90.2 over **seven** days. Any lever justified on "the object"
   must say which year's object it means.

**What does not change.** The keeper, the determination, every scored artifact,
and the substance: the model prices **$44.90–183.22** in the 2025 object hours
against an actual **$382.73–1,782.55**, and C3a-2025 remains the lane's only
failing criterion.

---

## 2. Verdicts against the pre-registered gates

| gate | result |
|---|---|
| **N-1** reproduce miso-204's object set *(PRE-CONDITION)* | **PASS, all three years.** Mean hour-of-day 11.67 / 15.73 / 15.87 vs 11.67 / 15.73 / 15.87; h18–h21 1 / 3 / 4; h15–h18 1 / 9 / 11; 2025 stamps **exact**. §3 |
| **N-2** the comparison set is miso-203's own *(PRE-CONDITION)* | **PASS, all three years.** Every one of the six `top_gross_load_hours` driver values reproduces the committed row. §3 |
| **G-A** drivers + percentile ranks *(charter a)* | measured, §4 |
| **G-B** contrast vs the top-15 gross-load hours *(charter b)* | measured, §4 |
| **G-C** overlaps *(charter c)* | measured, §4 |
| **G-D** the stated verdict on miso-203 §8 *(charter d)* | **4 SURVIVE (C6, C7, C8, C10), C3 SURVIVES knife-edge, C5 MARGINAL, C4 REFUTED.** §5 |
| **G-E** the location argument, re-checked | **SURVIVES** — 18/18 zone-years below the anchor, 2025 mean gap −2.11 °C. §6 |
| **G-F** the seam object, re-measured | done; **model-side descriptive, licenses nothing**. §7 |
| **TRAP 5** anchors read, not re-derived | **HELD** — reproduces `g_a_anchor` 2025 exactly |
| **TRAP 7** scoring-reference coverage | **CLEAN** — **0** NaN in Jun–Jul in every year (1 NaN in all of 2025, outside Jun–Jul); the committed hub series matches `actual_lmp_hourly_MISO.parquet` to 1.3e-05 / 2.7e-05 / 5.9e-05 |
| **H-1 / H-2** *(POST-HOC, added after G-D resolved, disclosed as such)* | the net-load decomposition and the largest-hour identity — **no gate, licenses nothing**. §5.1, §6 |

**Stop rule honoured as written.** PREREG §6 arms nothing unless G-D re-aims at an
`O`/`U` family **and** the lever clears the miso-203 bounding discipline. It does
not (§8). **Nothing armed, no LP solved. TRAP 8 held.**

---

## 3. N-1 and N-2 — the instrument, asserted before anything was read

| year | mean hour-of-day | miso-204 §6.5 | h18–h21 | ref | h15–h18 | ref | threshold $/MWh | n |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | **11.67** | 11.67 | 1 | 1 | 1 | 1 | 121.43 | 15 |
| 2024 | **15.73** | 15.73 | 3 | 3 | 9 | 9 | 159.01 | 15 |
| 2025 | **15.87** | 15.87 | 4 | 4 | 11 | 11 | 373.02 | 15 |

2025's fifteen CST stamps match miso-204 §6.4's table exactly. **TRAP 4** does not
fire: `n = 15` in every year, no tie at the 99th percentile.

**N-2**, the comparison set that must *not* move (it is defined on model drivers,
which the LMP clock defect never touched): all six values of
`top_gross_load_hours` reproduce miso-203's committed row in all three years —
2025 load 117,415 MW, wind 5,758, solar 11,435, net load 100,223, 3-h ramp 5,364,
dry-bulb 32.7 °C. **The contrast below is therefore like-for-like**, and every
difference from miso-203 is attributable to the object set alone.

---

## 4. G-A / G-B / G-C — the drivers, repaired

**2025**, the year that carries the determination:

| | **OBJ, repaired** | OBJ, miso-203 *(defective)* | top-15 gross-load | all Jun–Jul |
|---|---:|---:|---:|---:|
| load | **109,041** | 105,843 | 117,415 | 86,370 |
| wind | **5,120** | 5,965 | 5,758 | 7,969 |
| **solar** | **6,237** | **1,859** | 11,435 | **4,639** |
| net load | **97,684** | 98,018 | 100,223 | 73,762 |
| net-load 3-h ramp | **4,930** | 1,875 | 5,364 | 26 |
| dry-bulb °C | **31.0** | 30.8 | 32.7 | 24.9 |
| mean hour-of-day | **15.9** | 18.3 | 14.5 | 11.5 |

Percentile rank within Jun–Jul, and the overlaps:

| year | load | net load | dry-bulb | *(miso-203: load / net load / dry-bulb)* | top-15 load | top-15 net load | top-15 dry-bulb |
|---|---:|---:|---:|---|---:|---:|---:|
| 2023 | p75.4 | p73.3 | p66.0 | *p83.2 / p80.4 / p79.2* | 0 | 0 | 0 |
| 2024 | p85.9 | p86.6 | p80.6 | *p83.8 / p83.6 / p84.7* | 1 | 4 | 0 |
| 2025 | **p92.8** | **p95.6** | **p90.2** | *p88.4 / p94.3 / p89.6* | **1** | **3** | **0** |

Two things move in opposite directions from what miso-203 reported: **2025's
drivers are all MORE extreme than stated** (the object is closer to the peak than
reported), while **2023's are all LESS extreme** (p75 load, p66 dry-bulb — an
unremarkable midday set).

### 4.1 The 2025 object, hour by hour

| CST stamp | actual | model_lw | load (pct) | **solar** | net load (pct) | 3-h ramp | °C (pct) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 06-17 HE18 | 543.2 | 49.5 | 101,518 (82.0) | 5,678 | 90,783 (88.7) | 3,283 | 30.0 (85.7) |
| 06-23 HE18 | 838.9 | 85.3 | 113,603 (97.6) | 6,651 | 97,039 (97.0) | 4,359 | 33.3 (98.7) |
| 06-23 HE19 | 1,046.7 | 127.6 | 109,778 (95.1) | 2,241 | 100,053 (98.5) | 5,845 | 32.7 (97.3) |
| 06-24 HE11 | 382.7 | 52.8 | 103,335 (85.6) | 10,454 | 88,011 (83.4) | 11,452 | 27.2 (67.1) |
| 06-24 HE12 | 406.3 | 58.5 | 106,313 (90.2) | 10,498 | 91,734 (90.1) | 12,250 | 28.6 (75.6) |
| 06-24 HE16 | 390.1 | 64.6 | 108,114 (93.2) | 7,881 | 96,993 (96.9) | 2,957 | 31.8 (95.2) |
| 06-24 HE17 | 451.4 | 64.6 | 107,522 (92.4) | 7,020 | 97,158 (97.1) | 1,455 | 31.7 (94.6) |
| 06-24 HE18 | 1,202.0 | 64.6 | 105,825 (89.5) | 5,344 | 97,281 (97.1) | 1,130 | 31.3 (93.5) |
| 06-24 HE19 | 775.0 | 68.5 | 103,323 (85.5) | 1,911 | 98,308 (97.7) | 1,315 | 30.7 (90.6) |
| 07-15 HE16 | 413.3 | 50.6 | 113,489 (97.5) | 9,741 | 96,885 (96.7) | 6,759 | 32.3 (96.4) |
| 07-22 HE18 | 643.7 | 48.3 | 113,184 (97.3) | 7,954 | 96,755 (96.4) | 5,057 | 31.0 (91.9) |
| **07-28 HE18** | **1,782.5** | **161.4** | **117,206 (99.3)** | **7,668** | **105,957 (99.8)** | 4,046 | 32.6 (96.9) |
| 07-28 HE19 | 683.2 | 183.2 | 113,404 (97.4) | 2,212 | 107,112 (99.9) | 5,249 | 32.0 (95.6) |
| 07-28 HE20 | 388.7 | 97.5 | 109,946 (95.4) | 46 | 105,371 (99.7) | 2,527 | 31.1 (92.8) |
| 07-30 HE14 | 826.9 | 44.9 | 109,055 (94.5) | 8,257 | 95,814 (95.2) | 6,268 | 29.3 (80.9) |

**Eleven of the fifteen carry solar above the Jun–Jul mean of 4,639 MW.** Only
three (06-23 HE19, 07-28 HE19, 07-28 HE20) are post-roll-off hours in the sense
miso-203 described, and the largest hour of the year is not among them.

`06-24 HE17 → HE18` is miso-204 §6.4's row and it is worth restating with drivers
attached: the actual goes **$451 → $1,202** while the model does not move at all
(**$64.61 → $64.61**), across an hour in which **load falls** 107,522 → 105,825
and net load is essentially flat. Nothing in the driver set explains that hour.

---

## 5. G-D — the verdict on miso-203 §8, claim by claim

Decision rules fixed in PREREG §3 before any statistic was computed.

| id | claim (2025) | rule | measured | **verdict** |
|---|---|---|---|---|
| **C3** | 11.6 GW less gross load, only 2.2 GW less net load | survives iff load gap ≥ 8.0 GW and net-load gap ≤ 4.0 GW | load gap **8,374**, net-load gap **2,539** | **SURVIVES — knife-edge**, 374 MW over its own line |
| **C4** | solar collapses 11,435 → 1,859 MW | survives ≤ 3,500; refuted > 6,000 | **6,237** | **REFUTED** |
| **C5** | zero of 15 are top-15 load hours | survives = 0; refuted ≥ 2 | **1** | **MARGINAL** |
| **C6** | zero of 15 are top-15 dry-bulb hours | survives = 0; refuted ≥ 2 | **0** | **SURVIVES** |
| **C7** | only 4 of 15 are top-15 net-load hours | survives ≤ 6 | **3** | **SURVIVES** |
| **C8** | net load p94.3 > load p88.4 — a net-load object | survives iff net load ≥ p90 and > load | **p95.6 > p92.8** | **SURVIVES, strengthened** |
| **C10** | the tail is an **evening net-load ramp** | survives iff ramp excess ≥ +2,000 MW | **+4,904** | **SURVIVES on the rule — see below** |

C1 (*13 of 15 in h18–h21*) and C2 (*the monotone 14.4 → 17.1 → 18.3 march*) were
already corrected by miso-204 §6.5 to **4 of 15** and **11.67 → 15.73 → 15.87,
one step then flat**; they are inherited, not re-adjudicated.

**C10's rule passed and my rule was under-specified — stated plainly rather than
banked.** I pre-committed a ramp *magnitude* test and wrote no test of the ramp's
*cause* or its *time of day*. The magnitude is real and large (**4,930 MW against
a Jun–Jul mean of 26**). But **"evening"** is refuted by miso-204 (mean hour 15.9,
4 of 15 in h18–h21) and **"after solar roll-off"** is refuted by C4 and by §5.1
below. And the ramp does not even **discriminate**: the top-15 gross-load hours
carry a **larger** 3-h ramp (**5,364 MW**) than the object hours do. So C10 should
be read as *"the object hours carry a large net-load ramp, as do the ordinary
summer peak hours"* — which is a much weaker statement than the one it inherited.
This is the same failure mode miso-204 named in its P3: **I wrote a magnitude and
omitted the mechanism**, and the omitted half is where the result was.

### 5.1 H-1 — why (POST-HOC, added after G-D resolved, no gate)

Net-load elevation over the Jun–Jul mean, decomposed. A **positive** solar term
would mean solar was *missing*; a **negative** term means solar was *abundant*.

| year | net-load excess | from **load** | from **wind deficit** | from **solar deficit** | solar pct (JJ) | **solar pct, hour-of-day matched** | **wind pct, h-o-d matched** | load pct, h-o-d matched |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 10,050 | 10,559 (**105.1 %**) | 719 (+7.2 %) | **−1,228 (−12.2 %)** | p82.3 | **p55.3** | p54.5 | p63.8 |
| 2024 | 18,590 | 16,694 (**89.8 %**) | 2,690 (+14.5 %) | **−794 (−4.3 %)** | p59.8 | **p38.0** | p36.1 | p69.6 |
| 2025 | 23,922 | 22,671 (**94.8 %**) | 2,848 (+11.9 %) | **−1,598 (−6.7 %)** | p61.3 | **p48.1** | **p36.5** | **p83.4** |

**The hour-of-day-matched columns are the load-bearing ones**, because they remove
the diurnal cycle: they answer *"was this driver unusual **for that time of
day**?"* rather than *"was it unusual for a summer hour?"*. In 2025 solar answers
**p48.1 — dead average**. Wind answers **p36.5 — genuinely low**. Load answers
**p83.4 — genuinely high**. The object's hours are **high-load, low-wind,
ordinary-solar** hours. miso-203's construction, indexed one hour late, sampled
the solar cliff and read a solar story into it.

---

## 6. G-E — the location argument survives; the peak-load argument does not

Re-checked on the repaired hours against miso-203's own anchors (**read**, not
re-derived — TRAP 5 asserts they reproduce `g_a_anchor` exactly):

| year | zones below the anchor | mean gap °C |
|---|---:|---:|
| 2023 | **6 / 6** | −7.78 |
| 2024 | **6 / 6** | −4.12 |
| 2025 | **6 / 6** | **−2.11** |

**18 of 18 zone-years, gap negative in every year — the location argument holds at
full strength, and is the one to cite.** A hinge anchored at the summer
peak-demand rating condition is at its zero point in the object's hours, at any
slope and any admissible anchor. `temp_dependent_derate`'s merchant scope stays
closed on it (and the cell stays `K`, cogen-scoped, per miso-203).

**But the constraint must be narrowed, and this is against the inherited story.**
miso-203's §10 wrote *"any mechanism that works by removing capability in the
hottest **or tightest** hours is aimed at hours the object is not in"*, and the
charter carried it forward as *"keyed to heat **or to peak load**"*. The heat half
survives at 18/18. **The peak-load half does not survive at 2025's strength**:

* load percentile **p88.4 → p92.8**, net load **p94.3 → p95.6**;
* top-15-load overlap **0 → 1**;
* **H-2**: the single largest hour of 2025 — `2025-07-28 HE18`, actual
  **$1,782.55**, model **$161.39** — is at **load p99.3, net load p99.8, dry-bulb
  p96.9**, i.e. essentially *the* peak hour of the summer.

So the honest statement is: **a mechanism keyed to TEMPERATURE is aimed at hours
the object is not in (18/18). A mechanism keyed to PEAK LOAD is no longer excluded
by this measurement in 2025** — though it would still miss 2023's object entirely
(load p75.4), and any such candidate needs its own rule-28(a) argument plus an
account of why the two years differ. **Nothing here re-opens a closed cell**, and
this session opens none.

---

## 7. G-F — the seam object, re-measured on the right hours

Object hours against the other Jun–Jul hours, P1, MW:

| class | 2023 | 2024 | **2025** | *miso-202, defective set* |
|---|---:|---:|---:|---:|
| **import** | +1,477.4 | +1,850.4 | **+3,673.3** | *+3,844.4* |
| CT_PEAKER | +1,423.6 | +5,035.1 | **+8,911.7** | *+8,783.4* |
| ST_GAS | +1,017.3 | +1,374.5 | **+2,755.6** | *+2,826.5* |
| COAL_PRB | +2,165.2 | +4,232.1 | **+2,198.3** | *+2,174.8* |
| wind | −726.5 | −2,717.8 | **−2,877.9** | *−2,023.9* |
| solar | +1,240.5 | +802.2 | **+1,614.4** | *−2,808.5* |

**The seam number is robust to the repair: +3,673.3 MW against +3,844.4, a 4.4 %
revision** — this is the figure to quote to the owner, and it no longer rests on
hours the scored series does not contain. CT_PEAKER, ST_GAS and COAL_PRB are
likewise stable to within a few per cent.

**Why they are stable when only 4 of the 15 hours coincide** — worth recording,
because it cuts both ways: both hour sets are high-net-load sets, and these
classes respond to net load, so their aggregate excess is insensitive to *which*
high-net-load hours are chosen. **Solar is the one row that does not survive** —
it flips from **−2,808.5** to **+1,614.4**, a sign inversion, because solar is the
one driver whose value depends on the hour-of-day and not on the tightness. That
is the whole miso-204 defect in a single row, and it is why aggregate stability is
never evidence that an hour set is right.

**Label, repeated from the record: model-side descriptive only.** No committed
hourly MISO interchange actual exists, so this is not a residual against a
benchmark, exactly as miso-202 §2 A-4 stated. **It licenses nothing and no
admissibility argument is made here.** The D-2 5(i) ruling remains the owner's.

---

## 8. My prior, scored against interest

| # | prediction | dir. | conf. | measured | verdict |
|---|---|---|---:|---|---|
| **P1** | OBJ solar higher than 1,859 MW by ≥ +1,500 | ↑ | 0.80 | **6,237** (+4,378) | **RIGHT, understated** |
| **P2** | gross-load gap shrinks below 8,000 MW | ↓ | 0.65 | **8,374** (from 11,572) | **HALF-WRONG** — direction right, threshold missed by 374 MW. It is also C3's own line, so C3 SURVIVES by that same 374 MW; reported as knife-edge rather than banked |
| **P3** | load percentile rises above p88.4 | ↑ | 0.70 | **p92.8** | **RIGHT** |
| **P4** | net-load percentile **falls** from p94.3, stays ≥ p88 | ↓ | 0.55 | **p95.6 — it ROSE** | **WRONG ON THE SIGN**, the one thing the PREREG made me write down |
| **P5** | top-15-load overlap ≥ 1 | ↑ from 0 | 0.50 | **1** | **RIGHT, by one hour** |
| **P6** | location survives, ≥ 15/18, 2025 gap negative | neg. | 0.75 | **18/18, −2.11 °C** | **RIGHT** |
| **P7** | 3-h ramp higher than 1,875 MW | ↑ | 0.60 | **4,930** | **RIGHT, badly understated** |
| **P8** | seam import excess positive, ≥ +2,500 MW | ↑ | 0.70 | **+3,673.3** | **RIGHT** |
| **P9** | *(against interest)* ≥ 2 of C3 / C8 / C10 survive | — | 0.45 | **all three** | **RIGHT — against my own stated expectation**, which is the point of writing it |
| **P10** | arms a mechanism or spends a solve | — | 0.10 | nothing armed, no LP | **RIGHT** |

**What I did not predict, and it is the session's result.** Ten predictions, and
**not one of them is about solar's SIGN relative to the Jun–Jul mean.** P1 said
solar would be *higher than miso-203 reported* — a statement about the defect's
size — and I never asked the question that mattered: *higher than **normal***.
Crossing 4,639 MW turns "solar collapsed" into "solar was abundant" and inverts
the mechanism, and no line in the PREREG would have caught it. The signed
prediction I *did* write, P4, is the one I got **wrong on the sign**.

**That is now three consecutive MISO sessions whose most useful output came from
the part of the prior that was wrong or absent** — miso-203's P1, miso-204's P3,
and here the absent solar-sign line plus P4's wrong one. The generalisation the
charter drew from miso-204 (*predict the sign, not just the magnitude*) is
correct but **insufficient**: signs must be predicted **against the right
reference**. P4 had a sign and was wrong; the solar question had the right
reference and no prediction at all. **The successor's discipline: for every driver
in a characterisation, pre-commit its sign relative to its OWN normal population,
not relative to a prior session's number.**

**Against interest, plainly stated:** this session's headline correction lands on
miso-203's §8, which is this lane's own work, and it lands on the specific claim
that was most quoted forward — the solar-roll-off mechanism — while leaving the
statistical shell of that claim (C8's net-load object, C10's ramp magnitude, C3's
load/net-load gap) standing. The object is still real, still energy (miso-204),
still in the afternoon; **what it is not is a solar story.**

---

## 9. What this licenses — nothing armed, and the re-aimed queue

**No lever is licensed and none is proposed.** PREREG §6's stop rule applied:

1. **Queue item 1 is DISCHARGED.** The re-characterisation the charter made a
   precondition for every downstream lever is done. Any lever keyed to the
   evening-ramp / solar-roll-off story is keyed to a **refuted** mechanism and
   must be re-argued from §4–§5.
2. **`ordc_scarcity_overlay` stays `G`.** Nothing here touches miso-163 §1–§4's
   structural grounds; a driver characterisation is not evidence against a claim
   about perfect-foresight LPs. Rule 28(a) unmoved.
3. **`temp_dependent_derate`'s merchant scope stays closed, on LOCATION**, now
   re-verified 18/18 on the repaired hours (§6). The cell stays `K`, cogen scope.
4. **Queue item 3 (a ramp-constrained product) is WEAKENED by this session, and
   still NAMED, NOT CHARTERED.** Its window is now re-established as required —
   but the measurement is unhelpful to it: the object's 3-h net-load ramp
   (**4,930 MW**) is **smaller** than the ordinary top-15 gross-load hours'
   (**5,364 MW**), so **ramp does not discriminate the object from the peak hours
   a ramp product would also hit**. That joins the two standing measurements
   against it (miso-156 §7.2, the model under-ramps its own fleet at every
   quantile; miso-153's D-4, reserves inert at the summer peak) and the unanswered
   primary-source question of whether MISO prices a ramp product at all. A phase 0
   must now clear **three** objections, not two.
5. **Queue item 2 (the D-2 5(i) seam object) is re-measured and ready to quote:
   `+3,673.3 MW`** (§7), model-side descriptive. Still **NAMED, NOT CHARTERED**;
   the owner's admissibility ruling is outstanding and this session neither makes
   nor implies an argument for it.
6. **A narrowed constraint, for the successor's lever choice.** "Keyed to heat"
   remains disqualifying (18/18). **"Keyed to peak load" no longer is, in 2025** —
   the object sits at load p92.8 and its largest hour at p99.3. This does **not**
   re-open any cell; it removes an inherited exclusion that the measurement does
   not support, and any candidate must still explain 2023's p75.4 object.
7. **A caution that generalises past this lane.** §7 shows aggregate class
   dispatch was stable across a defect that moved 11 of 15 hours, while the one
   hour-of-day-dependent row (solar) inverted its sign. **Aggregate agreement is
   not evidence that an hour set is correct** — only an hour-of-day-matched or
   stamp-level check is.

---

## 10. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…139 / miso-179 / miso-194 / miso-203 / miso-204 zero-solve
precedent). Keeper unchanged at `2026-09-03-miso-202-unitclip`.
**Rule 28(b) `[R-MECH-MATRIX]`** — **no mechanism was tested, so no cell verdict
moves.** `temp_dependent_derate` and `measured_ramp_capability` carry amended
evidence citations in **MISO's shard only**; no other ISO's shard is touched
(rule 28(d), rule 25).
**Rule 28(a)** — no cell adjudicated `R`/`I`/`G` is re-tested or re-opened.
**Rule 28(c)** — no `ScenarioConfig` field added, so no base row is due.
**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only. MISO holds no `complete`/`final`
marker and the locked-test freeze is active. No out-of-training year was read,
solved, scored or registered.
**Rule 13 `[R-MEASURED]`** — the inputs are the committed C3a scoring reference,
the keeper's committed sidecars and prior sessions' committed records, read as a
**diagnostic characterisation of the object**. Nothing enters a solve.
**Rule 1 `[R-STRUCT]`** — no residual was moved; no mechanism was armed.
**Rule 27 `[R-PUSH]`** — one new probe file; no existing ≥300-line file rewritten.
