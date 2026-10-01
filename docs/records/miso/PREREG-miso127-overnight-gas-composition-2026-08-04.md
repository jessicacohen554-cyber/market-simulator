# PREREG — miso-127: the overnight gas COMPOSITION measurement (miso-114 §6's named bounded NO-LP step)

**Session:** miso-127 (dispatch label `pjm-154-cross-iso-queue`; the PJM lane had
no owner answer, so this is Lane B — MISO, the last ISO with a failing
criterion). **Branch** `claude/pjm-154-cross-iso-queue-5e2frp`.

**This file is committed and pushed BEFORE any adjudicating statistic is
computed.** Nothing below was measured first and written up after. Feasibility
checks that preceded it are named in §7 so the boundary is auditable.

**NO LP IS SOLVED. NO KEEPER MOVES. NO MECHANISM IS ARMED.** Every number comes
from committed artifacts. Rule 22 `[R-HOLDOUT]`: **2023, 2024, 2025 only** —
MISO holds **no** `complete` marker (`calibration-complete.json` `complete` =
NEISO/NYISO/PJM) and the holdout spend freeze is **active**, which outranks the
markers anyway.

---

## 1. The object, and why it is the queue item

MISO's keeper `2026-08-04-miso-126-steampart-b` is **NOT-YET** on a single
failing criterion: **C7 `COAL_PRB` shape**. §5.4 of the mechanism matrix has
**no named, un-adjudicated, non-data-blocked lever** — both known routes to C7
are dead (receipts-derived tonnage ruled inadmissible at miso-103; no ex-ante
contractual series at plant grain at miso-104), and the whole regulated-PRB
self-commitment family is spent (miso-111 `R`, miso-112 `R`, miso-113 `I`).

What §5.4 *does* carry is **two bounded NON-solve steps**. This session takes
the second: **miso-114 §6's CAMPD `CT_PEAKER` + `ST_GAS` overnight-online
measurement**. It is on-queue, it is no-LP, and it sits directly on the C7
residual's own causal chain:

* **miso-113** established C7 `COAL_PRB` is **not a coal-conduct defect** — the
  class's night level, volume (C1 16/16) and phase (`profile_r` 0.97–0.99) are
  all right. What is missing is the **dispersion of the overnight price
  signal** (model off-peak p10 $29.71 vs actual hub p10 $17.95). Repricing,
  splitting and flooring the band all left `cv_ratio` unmoved.
* **miso-114** decomposed that signal: **64 / 71 / 73 %** of the model's
  overnight p10 gap to MINN.HUB is the congestion-**FREE** system **ENERGY**
  component, and within it defect (a) is a near-flat **+$4 to +$8 LEVEL offset
  across net-load deciles 0–8** — *the signature of a mispriced marginal unit*.
* miso-114 measured the **model** side of the trough only: at h1–3 the model
  fills a 1.5–1.7 GW import hole and a 3.4–3.9 GW gas hole with 2.6–3.7 GW of
  extra coal **while keeping 1,907 / 2,415 / 2,350 MW of `CT_PEAKER` + `ST_GAS`
  online**. It could not measure the market side, because **EIA-930 does not
  split gas by prime mover**.

**The question this session answers, and only this one:** does MISO's own
metered record run that much `CT_PEAKER` + `ST_GAS` overnight? If the model
holds expensive peaker/steam capacity overnight that the real market does not —
while being *short* gas overall — then the model's overnight marginal machine
is **structurally the wrong machine**, and the +$4–8 level offset has a
**composition** identification rather than a price one.

**What this session does NOT do.** It proposes no mechanism, arms nothing and
sizes nothing. Δ (defined in §3) is a **residual**; rules 13 `[R-MEASURED]`,
21 `[R-DOF]` and 24 `[R-REGISTRY]` forbid sizing any adder, scalar, haircut or
floor on it. See KILL-4.

---

## 2. Construction (committed artifacts only, matched-plant)

**Measured side.** `frontend/data/backcast/bench/MISO/<year>.json.gz`,
per-plant `campd` — the dashboard's own committed class actual, with the
model's own zone and class assignment already applied. Decoded exactly as
`scripts/migrate_bench_multiclass.py::_decode`: base64 → `uint8` → rescaled so
the series sums to the entry's `c_ann`. This is the sanctioned path; the class
actual is **never** re-derived by summing raw CAMPD over a hand-built roster.

**Model side.** `frontend/data/backcast/runs/2026-08-04-miso-126-steampart-b.js`,
per-plant `m`, same encoding, rescaled to `m_ann` — the **keeper's own**
registered payload. The class aggregate
`results/calibration/miso126_steampart_B/hourly/class_hourly_<year>.parquet`
(P1) is carried alongside as an independent cross-check of the matched-plant
sum.

**Matched population.** Only plant-or-slice keys present in **both** the bench
entry set (with a `campd` series and `nodata` false) **and** the payload. This
is what removes coverage bias: MISO's sub-25-MW peakers are below the CEMS
reporting threshold, so an unmatched comparison would read the model long by
construction. Matching makes the two sides the *same machines*.

**Window.** Hour-of-day ∈ **{1, 2, 3}** on the model's own 8760 chronological
index (leap day dropped), which is miso-114's "h1–3".

**Classes.** Primary: `CT_PEAKER` + `ST_GAS` (the two miso-114 named).
Reported alongside: `CC_REGULAR`, `CC_CHP`, `CT_CHP`, `ST_CHP`.

**Known quantization, declared up front.** The bench/payload encoding is
`uint8` percent-of-nameplate (`scripts/render_calibration_html.py::_b64`,
clip 0–250, rounded), i.e. 1 % of plant nameplate per step, then rescaled to
the annual total. Rounding is ~unbiased and independent across plants, so at
class-aggregate scale its contribution is O(single MW) against a GW-scale
statistic. §5's P6 reports the realised bound rather than assuming it.

---

## 3. Pre-registered properties, each with its falsifier

**P1 — PHASE-ALIGNMENT CONTROL. Must pass or the measurement is VOID.**
`COAL_PRB` — the class whose keeper `profile_r` is already 0.97–0.99 — must
reproduce that on *this* construction: Pearson r between the 24-point model and
measured hour-of-day mean profiles ≥ **0.90** in **all three** years, matched
plants. **Falsifier:** any year < 0.90 ⇒ the two 8760 indexes are not
phase-aligned; report VOID and publish no other statistic.

**P2 — COVERAGE CONTROL.** The matched population must carry ≥ **90 %** of each
reported class's payload annual energy (`m_ann`). **A class below 90 % is
REPORTED but NOT gated** — its Δ is descriptive only and cannot carry P3.

**P3 — THE ADJUDICATING STATISTIC.**
Δ_overnight ≡ (model − measured) **mean MW over hour-of-day 1–3**, matched
plants, for **`CT_PEAKER` + `ST_GAS` combined**, per year.

* **MATERIAL** iff |Δ| ≥ **500 MW** in ≥ **2 of 3** years.
* **Direction is the test of miso-114's reading.**
  * Δ > 0 (model **LONG** expensive gas overnight) **CONFIRMS** the
    mispriced-marginal-unit reading and names a **composition** defect.
  * Δ < 0 (model **SHORT**) **FALSIFIES** it — the model is not holding
    expensive gas overnight and the +$4–8 level offset must originate
    elsewhere. Record the falsification; **do not re-frame it into a
    confirmation.**
* |Δ| < 500 MW in ≥ 2 of 3 years ⇒ **IMMATERIAL**; the object closes on
  measurement and **no successor is chartered from it** (rule 19
  `[R-ONE-MECH]` forbids manufacturing one).

**Why 500 MW, declared before measurement.** miso-105 §(c) measured the model's
own overnight stack slope at **1.85 / 1.79 / 1.56 GW per $/MWh**. 500 MW is
therefore ≈ **$0.3/MWh** against the +$8.53 / +$7.01 / +$8.54 energy-component
gap miso-114 measured — ≈ 3–4 % of it. Below that a composition swap cannot be
a material part of the level offset **regardless of sign**, so it is the honest
floor for "material". The bar is set from a published prior measurement, not
from anything computed in this session.

**P4 — CLASS ATTRIBUTION (reported, not gated).** Δ split `CT_PEAKER` vs
`ST_GAS` separately, and reported next to `CC_REGULAR`/`CC_CHP`. This makes the
composition claim falsifiable **in its own arithmetic**: if the model is long
peaker/steam *and* miso-114's 3.4–3.9 GW all-gas hole is real, the model must
be **short CC by a comparable or larger amount**. A long-peaker/long-CC result
would be internally incoherent and is reported as such.

**P5 — ARITHMETIC CLOSURE (coherence check, not a gate).** The six fossil-gas
class Δs must sum to the all-gas Δ on the same matched population to within
**1 MW**. This is an identity; a breach means a construction bug and the run is
re-done, not reinterpreted.

**P6 — QUANTIZATION BOUND (reported).** The realised worst-case contribution of
the `uint8` encoding to the P3 statistic, computed as the matched population's
per-hour rounding half-step summed in quadrature. Reported so the reader can
see P3 clears it, not asserted.

---

## 4. KILL rules

* **KILL-1.** P1 fails in any year ⇒ **VOID**. Publish the control failure and
  nothing else.
* **KILL-2.** P3 immaterial ⇒ the lane **CLOSES ON MEASUREMENT**. No cell moves
  to a mechanism verdict, no successor is chartered, no re-run, no re-derive
  (rule 23 `[R-FROZEN-DERIVE]`).
* **KILL-3.** P3 material but **Δ < 0** ⇒ miso-114's mispriced-marginal-unit
  reading is **FALSIFIED**. The finding records the falsification and
  redirects; **no mechanism is proposed in this session.**
* **KILL-4 (binding whatever P3 returns).** Nothing here licenses arming
  anything. **No adder, scalar, haircut or floor may be sized on Δ** — Δ is a
  residual (rules 13 / 21 / 24). Any mechanism P3 might motivate needs its
  **own** charter with its **own** forward-regenerable identification, derived
  from MISO's own record (rule 25 `[R-ISO-SCOPE]`: no verdict is imported from
  another ISO).
* **KILL-5.** This session registers **no run** (nothing is solved, so rule 15
  has nothing to register) and **promotes no keeper**. The MISO keeper stays
  `2026-08-04-miso-126-steampart-b`.

---

## 5. The miso-121 DO-NOT-REDO, carried forward explicitly

miso-121 established, and this session is bound by it: **binding is not
marginality**, and an offer-delta percentile over-predicted a realised price
effect by five orders of magnitude. **P3 measures ONLINE ENERGY, not
marginality.** A material Δ therefore establishes a **composition** fact and
**does not by itself establish a price effect** — the price leg would be a
separate, separately-identified question. This prereg does not claim otherwise
and no downstream sentence may read P3 as a price result.

Likewise miso-119's and miso-122's: `max_abs_class_hour_mw` is not a mechanism
magnitude at MISO and is not used here.

---

## 6. Deliverables

* `results/calibration/FINDING-miso127-overnight-gas-composition-2026-08-04.md`
* probe `scripts/probes/_miso127_overnight_gas_composition.py` (committed)
* machine record `results/calibration/_miso127_overnight_gas_composition.json`
* mechanism-matrix cell + evidence stamped in **this** session (rule 28(b)) —
  an **audit/measurement** stamp where one is warranted, never a mechanism
  verdict, since no mechanism is tested.
* `docs/calibration-log/miso.md` entry; next number **miso-128**.

---

## 7. Feasibility checks that PRECEDED this prereg (auditable boundary)

For honesty about what was looked at before pre-registering, these and only
these were run: existence and schema of the bench file, its `groups`/`classFull`
key inventory and encoding; existence and schema of the keeper payload and
`class_hourly_<year>.parquet`; the keeper id and determination; MISO's holdout
marker and the freeze state; §5.4's queue state. **No hour-of-day statistic, no
overnight aggregate and no model-vs-measured comparison of any class was
computed before this file was committed.**
