# PREREG miso-205 — re-do miso-203's G-E driver characterisation on the REPAIRED instrument (2026-09-03)

**Session:** miso-205, branch `claude/miso-203-ge-repaired-clock-7jdcxd`.
**Keeper at open: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested
(ledger 41/2, n_residual 2).

**Pushed BEFORE any adjudicating statistic is computed.** No number in §3–§5
below has been measured at the time of writing; §1's baselines are prior
sessions' published records, read as inputs.

**This is a ZERO-SOLVE phase 0.** Rule 22 `[R-HOLDOUT]` — 2023/2024/2025 only;
MISO holds no `complete`/`final` marker and the locked-test freeze is active.
Committed artifacts only.

---

## 1. Why this session exists, and what it inherits as settled

miso-204 §6 established that both committed probes
(`_miso202_c3a_2025_anatomy` blocks a2/a4, `_miso203_scarce_hour_identity`)
build their hourly actual as an **eight-hub equal-weighted mean on the RAW EST
hour-ending index**, while the series C3a is actually scored against —
`actual_lmp_hourly_MISO.parquet`, i.e. `bench.avgLMP.rt`/`rt_lw` — is
**INDIANA.HUB on the model's fixed-CST non-leap 8760**. The defect is a constant
**−1 h**, plus a further **−24 h after Feb 28 of a leap year**; it is invisible
in the annual mean (so **C3a itself is unaffected**) and fatal to hour-matching,
because MISO RT's lag-1 autocorrelation is only **0.39 / 0.37 / 0.44**.

**Inherited as settled, and NOT re-adjudicated here** (miso-204 §6.5, published):

| year | mean hour-of-day, committed | mean hour-of-day, **repaired (CST)** | in h18–h21, repaired | in h15–h18, repaired | committed ∩ repaired |
|---|---:|---:|---:|---:|---:|
| 2023 | 14.40 | **11.67** | 1 / 15 | 1 / 15 | 2 / 15 |
| 2024 | 17.07 | **15.73** | 3 / 15 | 9 / 15 | 1 / 15 |
| 2025 | 18.33 | **15.87** | 4 / 15 | 11 / 15 | 4 / 15 |

So miso-203 §8's *hour-of-day* claims are already corrected. What is **UNMEASURED
on the repaired instrument** — and is this session's entire charter — is the
**driver** characterisation: load / wind / solar / net load / net-load 3-h ramp /
dry-bulb, their percentile ranks, the contrast against the top gross-load hours,
and the overlaps.

**The miso-203 baselines this session adjudicates against** (`_miso203_scarce_hour_identity.json`,
committed, measured on the DEFECTIVE hour set):

| 2025 | scarce hours | top-15 gross-load hours | all Jun–Jul |
|---|---:|---:|---:|
| load | 105,843 | 117,415 | 86,370 |
| wind | 5,965 | 5,758 | 7,969 |
| **solar** | **1,859** | **11,435** | 4,639 |
| net load | 98,018 | 100,223 | 73,762 |
| net-load 3-h ramp | 1,875 | 5,364 | 26 |
| dry-bulb | 30.8 °C | 32.7 °C | 24.9 °C |
| mean hour-of-day | 18.3 | 14.5 | 11.5 |

Percentile ranks in Jun–Jul: 2023 load p83.2 / net load p80.4 / dry-bulb p79.2;
2024 p83.8 / p83.6 / p84.7; 2025 **p88.4 / p94.3 / p89.6**.
Overlaps with the top-15 of each driver: 2023 **0 / 0 / 0**; 2024 3 / 4 / 1;
2025 **0 / 4 / 0**.

Seam baseline (`FINDING-miso202` §2 A-4, measured on the same defective set, and
**model-side only** — no committed hourly interchange actual exists for MISO):
in the 15 hours against the other 1,449 Jun–Jul hours the keeper dispatches
CT_PEAKER 13,120.9 MW (**+8,783.4**), **import 6,351.3 MW (+3,844.4)**, ST_GAS
5,087.0 MW (+2,826.5), COAL_PRB +2,174.8, wind −2,023.9, solar −2,808.5.

Location baseline (`_miso203_summer_peak_anchor_phase0.json` `g_c` `p1`): the
scarce hours sit **BELOW** the EIA summer-peak-demand rating condition in
**18 of 18 zone-years**, by 1.4–8.4 °C (2025: −1.45 to −3.45 °C by zone).

---

## 2. The instrument

`scripts/probes/_miso205_ge_repaired_clock.py` → `results/calibration/_miso205_ge_repaired_clock.json`.

* **Object set (OBJ):** top 1 % of Jun–Jul hours of
  `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`,
  `hub == "INDIANA.HUB"`, column `rt` — the committed artifact miso-204 verified
  at max|diff| 1.3e-05 / 2.7e-05 / 5.9e-05 against `actual_lmp_hourly_MISO.parquet`.
  **The raw `data/raw/lmp-data/MISO/*.csv.gz` staging is NOT re-derived** — that
  re-derivation is the defect.
* **Drivers:** identical construction to `_miso203_scarce_hour_identity.py` —
  `load` and model `price` from the keeper's `hourly/system_<year>.parquet` (P1),
  `wind`/`solar` from `hourly/class_hourly_<year>.parquet` (P1),
  dry-bulb from `market_sim.data.eia_loader.iso_zone_hourly_drybulb`. These are
  already on the model's clock and are **unaffected** by the LMP defect; only the
  hour SET moves.
* **Anchors** for the location re-check are READ from
  `_miso203_summer_peak_anchor_phase0.json` `g_a_anchor`, not re-derived.

---

## 3. Gates and their decision rules, fixed now

### N-1 — the reconstruction must reproduce miso-204's published object set (PRE-CONDITION)

**Decision rule.** The OBJ set's mean hour-of-day must equal miso-204 §6.5's
published **11.67 / 15.73 / 15.87** to ±0.01, its h18–h21 counts **1 / 3 / 4**
and h15–h18 counts **1 / 9 / 11** exactly, and the 2025 set's 15 CST stamps must
equal §6.4's table exactly. **If N-1 fails, the session STOPS at the failure and
reports it** — a reconstruction that does not reproduce the reference measures
nothing (the miso-204 N-3 / miso-203 N-0 discipline).

### N-2 — the comparison set must be miso-203's own (PRE-CONDITION)

The top-15 gross-load Jun–Jul set is defined on **model drivers** and therefore
does **not** move with the clock repair. **Decision rule.** My
`top_gross_load_hours` driver row must reproduce miso-203's committed row
**exactly** (all six values, all three years). A mismatch means my driver
pipeline differs from miso-203's and **no contrast in §4 is comparable** —
report and stop the contrast leg.

### G-A (charter a) — where the repaired hours sit in their own driver distributions

Reported, not gated: load / wind / solar / net load / net-load 3-h ramp /
dry-bulb, each hour's percentile rank in its own **Jun–Jul** distribution (and,
as miso-203 did, in **Jun–Sep**), plus the per-hour table.

### G-B (charter b) — the contrast against the 15 highest gross-load Jun–Jul hours

Reported on the same six drivers, all three years.

### G-C (charter c) — overlap with the top-15 load / net-load / dry-bulb hours

Reported per year.

### G-D (charter d) — the STATED verdict on miso-203 §8, claim by claim

Each claim is adjudicated by a rule fixed **now**. 2025 unless stated.

| id | miso-203 §8 claim | SURVIVES iff | REFUTED iff |
|---|---|---|---|
| **C3** | "11.6 GW less gross load, but only 2.2 GW less net load" | load gap ≥ 8.0 GW **and** net-load gap ≤ 4.0 GW | load gap < 8.0 GW |
| **C4** | "solar collapses 11,435 → 1,859 MW" | OBJ solar ≤ 3,500 MW | OBJ solar > 6,000 MW (PARTLY in between) |
| **C5** | "zero of 15 are top-15 load hours" | overlap = 0 | overlap ≥ 2 (MARGINAL at 1) |
| **C6** | "zero of 15 are top-15 dry-bulb hours" | overlap = 0 | overlap ≥ 2 (MARGINAL at 1) |
| **C7** | "only 4 of 15 are top-15 net-load hours" | overlap ≤ 6 | overlap ≥ 9 |
| **C8** | "net load p94.3 > load p88.4 — a net-load object, not a load object" | netload pctile ≥ p90 **and** netload pctile > load pctile | netload pctile < p90 **or** netload pctile < load pctile |
| **C10** | "the tail is an EVENING NET-LOAD RAMP" | OBJ 3-h net-load ramp exceeds the all-Jun–Jul mean by ≥ +2,000 MW | excess < +2,000 MW |

C1 ("13 of 15 in h18–h21") and C2 (the monotone 14.4 → 17.1 → 18.3 migration) are
**already corrected by miso-204 §6.5** and are inherited, not re-adjudicated.

### G-E — the LOCATION argument, re-checked on the repaired hours

The charter's binding constraint *"any capability-removal mechanism keyed to heat
or to peak load is aimed at hours the object is not in"* rests on miso-203's
18/18 zone-years below the rating anchor, measured on the defective hour set.

**Decision rule.** The location argument **SURVIVES** iff the repaired OBJ hours'
zone-mean dry-bulb is **below** the zone-year anchor in **≥ 15 of 18** zone-years
**and** the 2025 six-zone mean gap is **negative**. It is **WEAKENED** at 10–14 of
18, and **REFUTED** at ≤ 9 of 18 or a positive 2025 mean gap. Either way the
result is **stated**, per the charter.

### G-F — the D-2 5(i) seam object, re-measured before it is quoted to the owner

Queue item 2's `+3,844 MW` was measured on the defective set. Re-measure, on the
repaired OBJ hours against the other Jun–Jul hours, the P1 class-dispatch deltas
for **import**, CT_PEAKER, ST_GAS, COAL_PRB, wind, solar.

**Decision rule.** This is **descriptive and model-side only** (no committed
hourly MISO interchange actual exists), exactly as miso-202 labelled it. It
**licenses nothing** and is produced solely so the owner is quoted a number
measured on the right hours. **No admissibility argument is made here.**

---

## 4. Predictions, scored against interest — WITH SIGNS

miso-204's P3 gave congestion a magnitude and no sign, and the unpredicted
negative sign is the only reason its instrument forensic exists. Every prediction
below therefore states a **direction** as well as a magnitude.

| # | prediction (2025 unless stated) | direction | conf. |
|---|---|---|---:|
| **P1** | OBJ mean solar is **HIGHER** than miso-203's 1,859 MW, by **≥ +1,500 MW** | **↑ increase** | 0.80 |
| **P2** | the gross-load gap (top-load − OBJ) **SHRINKS** from 11,572 MW to **< 8,000 MW** | **↓ decrease** | 0.65 |
| **P3** | OBJ load percentile **RISES** above p88.4 | **↑ increase** | 0.70 |
| **P4** | OBJ net-load percentile **FALLS** from p94.3 but stays **≥ p88** | **↓ decrease, bounded** | 0.55 |
| **P5** | overlap with top-15 gross-load hours is **≥ 1**, i.e. C5's "zero" breaks | **↑ from 0** | 0.50 |
| **P6** | the LOCATION argument **SURVIVES**: below the anchor in **≥ 15/18** zone-years, and the 2025 mean gap stays **NEGATIVE** | **negative gap** | 0.75 |
| **P7** | the OBJ 3-h net-load ramp is **HIGHER** than miso-203's 1,875 MW (the repaired hours sit on the climb, not the plateau) | **↑ increase** | 0.60 |
| **P8** | the seam import excess stays **POSITIVE** and **≥ +2,500 MW** | **↑ positive** | 0.70 |
| **P9** | *(against interest)* **≥ 2 of the 3 core claims C3 / C8 / C10 SURVIVE** — I expect the evening-ramp framing to weaken, so I am predicting against my own expectation to make the miss legible | **survive** | 0.45 |
| **P10** | this session arms a mechanism or spends an LP solve | — | **0.10** |

---

## 5. Traps, each with a pre-committed counter-measurement

* **TRAP 1 — I rebuild the object set differently from miso-204 and silently
  measure a third thing.** *Counter:* N-1, asserted against §6.5's published
  hour-of-day statistics and §6.4's 2025 stamp table **before any driver number
  is read**. Stop on failure.
* **TRAP 2 — percentile ranks are population-dependent.** *Counter:* report both
  Jun–Jul and Jun–Sep exactly as miso-203 did; adjudicate C8 on **Jun–Jul**, its
  own basis.
* **TRAP 3 — the comparison set silently moves too.** *Counter:* N-2, byte
  reproduction of miso-203's `top_gross_load_hours` row.
* **TRAP 4 — ties at the 99th percentile change n.** *Counter:* report `n` per
  year; if `n ≠ 15` anywhere, adjudicate on the actual set and say so explicitly
  rather than truncating to 15.
* **TRAP 5 — I re-derive the rating anchors and get miso-203's G-A wrong.**
  *Counter:* the anchors are **read** from `g_a_anchor`, and asserted equal to the
  published 2025 values (MISO-West 32.249 … MISO-South 35.674) before G-E runs.
* **TRAP 6 — the seam number reads as a residual.** *Counter:* G-F is labelled
  model-side descriptive in the record itself; no benchmark exists and none is
  implied.
* **TRAP 7 — NaNs in the scoring reference distort the top-1 % cut.** *Counter:*
  report the Jun–Jul NaN count per year and whether any NaN sits in the OBJ
  region.
* **TRAP 8 — I read a licence into a descriptive block.** *Counter:* the stop
  rule below, pre-committed.

---

## 6. Stop rule

This session **arms nothing and solves nothing** unless **both**: (i) G-D's
surviving claims re-aim the queue at a family whose matrix cell is `O` or `U`,
**and** (ii) that lever clears the miso-203 discipline — bounded at the object's
own percentile in its own driver **before** a solve is spent.

The charter's binding constraints are inherited and not re-litigated:
`ordc_scarcity_overlay` `G` (miso-163 §1–§4, structural), `internal_congestion_split`
`G` (miso-78/79/80, NO-BUILD fundamental), `zonal_loss_surface` `R`, the ambient/
capability-removal family CLOSED on **location** (miso-203) and reach (miso-139),
the unit-outage overlay family exhausted as a C3a route (miso-202), the seam
object **NAMED, NOT CHARTERED** pending the owner's admissibility ruling, and
`measured_ramp_capability` `U` but blocked on an unanswered primary-source
question about whether MISO prices a ramp product at all. **P10 = 0.10 reflects
that I expect to end at the finding.**

**Rule 28(a):** no cell adjudicated `R`/`I`/`G` is re-tested here. **Rule 28(b):**
no mechanism is tested, so no cell verdict moves; the cells this session re-aims
toward carry an amended evidence citation in **MISO's shard only**. **Rule 28(c):**
no `ScenarioConfig` field is added. **Rule 25:** only MISO's shard/keeper/status
files are touched. **Rule 15:** a zero-solve session registers no run.
