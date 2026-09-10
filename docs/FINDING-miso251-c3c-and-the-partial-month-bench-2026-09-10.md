# FINDING — miso-251: MISO's C3c needs no fix, and the thing that WOULD have broken its 2022 rung

**Session miso-251, 2026-09-10. ZERO LP in this document** — every number below is measured on
committed artifacts at HEAD.

---

## 1. THE C3c QUESTION — ANSWERED, WITH NO CODE CHANGE

Owner, 2026-09-10: *"For c3c miss on backcast calibration rubric, it should not create a calibrated
with caveats tag. C3c is an acceptable gate miss for this model class and it should still read
calibrated, so miso needs a fix."*

**That is already the live rule and MISO already reads it.** Rubric v3.3 (owner amendment
2026-08-17, rule 22 `[R-C3C]`) made a ledgered C3c non-downgrading, and
`calibration_verdict.py::_apply_c3c_standing_rule` + the determination block implement it. Measured
on the designated keeper `2026-09-09-miso-250-ep-gas`:

| scope | determination | reasons |
|---|---|---|
| **run (2023-2025)** | **`CALIBRATED`** | 1 ledgered caveat … **NOT determination-downgrading under rubric v3.3**: C3c price tail |
| 2023 | `CALIBRATED` | same |
| 2024 | `CALIBRATED` | same |
| 2025 | `CALIBRATED-WITH-CAVEATS` | **`unscored criteria: fuelmix, sysvol`** ← the cause; then the same non-downgrading C3c line |

### 1.1 What is actually producing the one "with caveats" string

`CALIBRATED-WITH-CAVEATS` appears **exactly once** in MISO's whole status part: the **2025 per-year
row**. C3c does not put it there. All **8 of 8** MISO C1 classes are `SKIPPED` on the *preliminary
2025 EIA-923 vintage* —

```
CC_REGULAR   7/41 prior plants missing (83% reporting)
CC_CHP      11/24 (54%)      CT_PEAKER  73/98 (26%)
ST_GAS       9/28 (68%)      ST_CHP     36/67 (46%)
COAL_PRB     6/40 (85%)      COAL_BIT   plant-months 92% present
COAL_LIGNITE no per-class actual
```

— so the C1 criterion itself is `SKIPPED`, which cascades to C2 (`sysvol` reads the C1 family), and
the *unscored-criteria* route downgrades. That route is one v3.3 **explicitly preserved**: "every
OTHER route to a caveat still downgrades: commercial-band target misses, protective-gate caveats,
**unscored criteria** and data-blocked years are untouched."

### 1.2 It is not MISO-specific, and it is not a defect

Same 2025 row, same cause, across the fleet: **CAISO, NEISO, NYISO and MISO all read
`CALIBRATED-WITH-CAVEATS` on 2025.** ERCOT escapes only because enough of its C1 classes still
score. This is the annual EIA-923 publication lag arriving in the scorer exactly as designed.

**No scorer change is made for it.** Making the unscored-criteria route non-downgrading would be a
real gate loosening the owner did not ask for and that v3.3 deliberately refused; and dropping C3c
from `caveats.ledgered` would violate rule 22 guard (d), which requires the miss stay listed,
budgeted and named at full magnitude *on a `CALIBRATED` run*. The row clears itself when EIA
publishes the final 2025 EIA-923 — nothing in the model has to move.

### 1.3 What this means for the holdout ladder

On an out-of-training year rubric **v3.6** drops the lone-failure condition, so a C3c miss on
2020/2021/2022 is a ledgered CAVEAT whatever else that year does. **C3c can never be the reason a
MISO touchpoint rung fails to read `CALIBRATED`.**

---

## 2. THE REAL DEFECT, FOUND WHILE PREPARING THE 2022 RUNG

MISO 2022's committed hub-price bench is **partially staged** — the raws stop at **2022-11-11 RT**
and **2022-12-09 DA** (`docs.misoenergy.org` aged the rest off before it could be fetched). The
intake recorded that faithfully in `da_cov` / `rt_cov`. What it produced in `*_mon` is the problem:

| month | RT actual (`rt_mon`) | RT coverage |
|---|---|---|
| Jan-Oct | 53.97 … 60.18 | **1.0000** |
| **Nov** | **38.41** | **0.3653** (11 days) |
| **Dec** | **22.82** | **0.0013** — ***ONE HOUR*** |

**December 2022 is Winter Storm Elliott.** A model December that prices Elliott was about to be
scored against a $22.82/MWh "December actual" built from a single staged hour — and C3b **squares**
that difference, so the two stub months would have dominated the NRMSE outright. The scorer's
existing like-for-like mask could not see it: it dropped only months whose actual is `None`, and
these are non-`None`.

**A MISO 2022 verdict scored that way would have measured the staging hole, not the model** — in
either direction, and the direction is not knowable in advance. It had to be fixed *before* the
rung was scored, not after seeing the number.

### 2.1 The repair — a coherence repair of a convention the scorer already declares

`score_price_mean` already says the model must be masked to the actual's calendar. The repair is to
make "the actual's calendar" mean what the intake published rather than what `is None` happens to
catch:

* **`_covered_months(actual_mon, cov_mon)`** — a month participates when its mean is present **and**,
  where a coverage vector exists, at least `PRICE_MONTH_COVERAGE_MIN` of its hours are staged.
  Absent a coverage vector this is *exactly* the pre-existing `is not None` test.
* **`_annual_from_months`** — on the masked path the **actual moves too**, hour-weighted over the
  same months. The committed annual averages every staged hour, partial months included; leaving it
  un-masked would put the two sides back on different calendars, which is the thing the mask exists
  to prevent.
* Applied in **C3a** (`score_price_mean`), its **DA diagnostic**, and **C3b**
  (`score_price_shape`), which had no calendar mask at all.
* The coverage vectors are read from the committed `actual_lmp.json` — **not** added to the bench
  payload. That was the first design and it was measured and rejected: the bench part's payload
  fingerprint covers the builder's output shape, so adding one key marked **31 of 31** committed
  bench parts of **every** ISO stale at once. Reading the same committed reference the part is built
  from changes no part and no fingerprint (re-verified: `0 STALE` after).

### 2.2 The threshold cannot be a fitted choice, and that is measured

The published record is **bimodal with nothing in the middle** — all 120 committed monthly coverage
values:

```
<= 0.3653 : MISO 2022 rt Nov 0.3653 / rt Dec 0.0013 / da Dec 0.2903 ; MISO 2026 H2 all 0.0000
>= 0.9911 : SPP 2024 rt Feb 0.9911 ; SPP Jan 0.9919 x6 ; MISO 2026 Jun 0.9986 ; 96 months at 1.0000
(0.3653, 0.9911) : ZERO months
```

Every threshold in that open interval selects the **identical** set, so the value cannot be tuned
toward an outcome (rules 1 `[R-STRUCT]` / 21 `[R-DOF]`). `PRICE_MONTH_COVERAGE_MIN = 0.90` sits
inside it. A test (`test_coverage_threshold_sits_in_an_empty_interval`) **fails** if a future intake
ever lands a month near the threshold — which is exactly when the value stops being outcome-neutral
and needs re-deciding rather than silently keeping its partition.

### 2.3 Measured effect: ZERO

* **0 of 33 registered runs change** — determination, every criterion status and every magnitude
  string byte-identical, scored before and after against a full snapshot.
* **0 of 31 bench parts** disturbed (`check_bench_freshness.py`: `0 STALE`, unchanged).
* No LP ran; no bundle was re-solved; every keeper re-scores in place.
* The **only** ISO-year in the repo the mask can reach is **MISO 2022**, which had no registered run
  when the repair landed. That is not a coincidence — it is why the repair could be made *before*
  the rung was scored, and why it is a plumbing fix rather than a gate move.

### 2.4 What it does NOT do

It does not widen a band, change a tier, add a caveat route, or make any miss smaller. On MISO 2022
it makes C3a and C3b measure **the ten fully-staged months** instead of ten months plus two staging
stubs — and both records say so in their own `metric` string, naming the months dropped, so a reader
sees the reduced calendar rather than inferring a full year. The honest statement of what a MISO
2022 price verdict is worth stays on the rung: **it is a ten-month comparison**, and it excludes the
single most extreme price event of that year.
