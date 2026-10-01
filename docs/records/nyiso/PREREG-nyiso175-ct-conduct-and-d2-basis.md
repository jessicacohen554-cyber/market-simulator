# PRE-REGISTRATION — nyiso-175: the CT deficit, on the instrument nyiso-174 unlocked,
# and the D-2 / `class_hourly` split-basis blocker that stands in front of it

**Session:** nyiso-175 · **Date:** 2026-09-02 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Phase 0, ZERO SOLVE intended.**

This file and `scripts/probes/nyiso175_ct_conduct_and_d2_basis.py` are committed
**before either is run**, in the nyiso-171 / 172 / 173 / 174 discipline. Every
threshold below is a number that can kill a lane, fixed here in advance.

---

## 0. What was already read before this was written, stated so the
## pre-registration is honest

Pre-registration protects the *gated* statistics, not the reading that motivates
them. Before writing this file the session had read, and is not pretending
otherwise:

* the committed `legitimacy_diagnostics.json` D-2 **rows and summary** for the
  keeper (the 13–17× ST_CHP / 1.6–1.8× CT_CHP disagreement nyiso-174 §6 item 3
  already published, plus the fact that the D-2 **summary** carries no CHP row
  at all);
* `scripts/legitimacy_diagnostics.py` — `D2_EXEMPT_CLASSES`, `run_d2`,
  `build_plant_matrices`, `plant_class_rows`, `aggregate_model_plants`,
  `load_payload_plants`;
* `scripts/render_calibration_html.py`'s model-payload emit (the CHP
  behind-the-meter add-back);
* `scripts/data/derive_thermal_tranches.py`'s `_fleet_nameplate_and_group`;
* `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` (the CHP rows);
* East River's EIA-860 generator roster and EIA-923 net generation by prime
  mover;
* the closed CT_PEAKER lane (nyiso-88 / 89 / 90 / 91 / 96).

**None of the gated statistics below has been computed.** A1, A2, B1–B5 and S1–S5
are all uncomputed at the moment of commit.

---

## 1. Object A — the blocker: what basis is D-2's `class_total_twh` on?

nyiso-174 §6 item 3 established that D-2's `class_total_twh` and the keeper's P1
`class_hourly` sidecar disagree about the model's own turbine/steam split by
**13–17×** on `ST_CHP` and **1.6–1.8×** on `CT_CHP` in the opposite direction,
while agreeing on the `CT_CHP + ST_CHP` total to within 2.2 %. Until this is
settled **no model-side per-class CT/ST reading is identified**, so it is
measured first.

**Hypothesis H-A**, three limbs, each read off the code before measuring:

* **H-A(i)** — D-2's dispatch map for a committed bundle is the **run payload**
  (`load_payload_plants`), because `dispatch/<year>_P1.parquet` is gitignored and
  absent from the bundle.
* **H-A(ii)** — the payload's per-(plant, class) model series carries a
  **report-only CHP behind-the-meter add-back** (`render_calibration_html.py`:
  `mw = mw + btm_mwh / T` for `CC_CHP` / `CT_CHP` / `ST_CHP`) that is **not** in
  the LP grid dispatch and therefore **not** in `class_hourly`.
* **H-A(iii)** — `aggregate_model_plants` sums slice keys to **bare plant
  codes** and `plant_class_rows` labels each plant with its **most-common
  non-empty LP-unit `plant_group`**, so a mixed-class plant's whole energy lands
  on one class.

### Gate A1 — does the reconstruction reproduce the committed denominator?

Recompute D-2 at HEAD from committed artifacts only (the diagnostics module's own
path, floors rebuilt by `run_year(fleet_only=True)` — **no LP**) and compare
`class_total_twh` class-by-class, year-by-year, against the committed
`legitimacy_diagnostics.json`.

* **ACCEPT H-A** iff **every** class-year matches within **0.5 %** relative, or
  within **0.005 TWh** absolute for a class under 1 TWh.
* **REJECT** on any miss ⇒ the basis is declared **UNRESOLVED**, nyiso-174 §6
  item 2 (which half of East River carries the must-run) **stays blocked on
  model-side artifacts**, and Object B's East River limb is reported from the
  measured side only.
* **Fallback, pre-registered:** if the recompute cannot run in this container
  (missing raw inputs for the floor rebuild), the same comparison is made against
  a self-contained payload + fleet reconstruction, and the *fallback* result is
  reported as such, at the same 0.5 % threshold, with the LP-unit-vs-generator
  label-grain caveat stated at full magnitude.

### Gate A2 — the sign falsifier (so agreement cannot be coincidental)

H-A must also explain the **direction**. Under H-A(iii) East River (2493) — the
plant nyiso-174 identified, and 65.8 % of the model's `ST_CHP` capacity and
68.6 % of its `CT_CHP` — must land on **`CT_CHP`**, not `ST_CHP`.

* If A1 passes but the reconstruction puts 2493 on `ST_CHP`, the agreement is
  **coincidental** and H-A is **REJECTED**.

### A3 — the rule 20 `[R-FORCED-BUDGET]` hazard, resolved from code

The brief carries forward that D-2's `ST_CHP` `share_of_class` > 1 (2.847 in
2024, 1.795 in 2025) is "a **LIVE HAZARD** for the rule 20 30 % merchant gate".
This is settled by enumeration, not measurement: report whether `CC_CHP`,
`CT_CHP` and `ST_CHP` can ever reach the D-2 **gated summary** and therefore ever
produce a `forced_share` verdict. **Whatever the answer, it is reported at full
magnitude** — a hazard that turns out not to be live is a correction to the
record, and a hazard that is live is escalated.

---

## 2. Object B — the CT deficit, on the newly-available instrument

`CT_PEAKER` runs **−81.5 / −86.2 / −63.7 %** and `CT_CHP` **−27.5 / −38.9 /
−23.4 %** against benchmark. nyiso-174 §4.3 flipped `CT_CHP` from
identification-blocked (anchor 4.933 on 1 unit) to **identifiable** (anchor
**0.892** on 3 units), which is the new evidence that makes this cell
re-openable under rule 28.

**Construction, fixed in advance.** Measured series =
`scripts/lib/campd_measured_classes.py` corrected construction over
`data/raw/campd-unit-level/NY_<year>.parquet`, `grossLoad` filled to zero
explicitly (trap (d)), clock `Etc/GMT+5` (trap (c)). Model series = the keeper's
committed P1 `class_hourly` (rule 15: read, don't replay), **conditional on gate
A1 identifying it as the per-class artifact**. Level anchor = committed bench
`classFull` grid-delivered TWh ÷ CEMS gross TWh, per class per year, applied so
only **shape** is compared (the nyiso-170 §3 basis).

### B1–B4 — the measurements

* **B1** anchors and class totals on the corrected construction, both CT classes,
  all three years.
* **B2 duration-curve decomposition.** Each series sorted descending
  independently; model ÷ anchored-measured at each decile of its own order. A
  **LEVEL** deficit is roughly proportional at every decile; a **CAPABILITY**
  deficit is concentrated in the top deciles; a **COMMITMENT** deficit is
  concentrated at the bottom.
* **B3 hour-matching.** Hourly Pearson `r` between model and anchored measured;
  share of measured class energy falling in hours the model runs the class at
  all; on-hours, starts and run-length distribution at a common online bar (the
  nyiso-90 / 96 construction, so the numbers are comparable to the closed
  record).
* **B4 load-band concentration.** The class deficit apportioned to the nyiso-168
  load bands (0–50 / 50–80 / 80–90 / 90–95 / 95–99 / 99–99.9 / 99.9–100), off the
  keeper's own `system_<year>.parquet` demand.

### B5 — the LEVEL-vs-RESPONSE verdict rule, fixed in advance

For each CT class-year, with `q90m` = model p90, `q90a` = anchored-measured p90:

* **LEVEL-limited** iff `q90m / q90a < 0.70` — the class never reaches the
  output the market's own fleet reached.
* **RESPONSE-limited** iff `q90m / q90a ≥ 0.70` **and** hourly `r < 0.50` — it
  reaches comparable output, in the wrong hours.
* **BOTH** iff `q90m / q90a < 0.70` **and** `r < 0.50`.
* **NEITHER** otherwise — in which case the class deficit is *not* a conduct
  object at hourly grain and the lane says so.

---

## 3. Object C — East River, and the tranche-derive attribution audit

nyiso-174 §6 item 2 named "which half of East River carries the must-run" as the
successor object. The primary record supplies the market's answer directly
(EIA-923 net generation by **prime mover**, GT vs ST, per year), and the model's
answer comes from the payload's `2493:CT_CHP` / `2493:ST_CHP` slices — subject to
H-A(ii)'s add-back, which is measured and disclosed rather than assumed away.

The candidate mechanism, named here so it cannot be invented after the fact:
`derive_thermal_tranches._fleet_nameplate_and_group` attributes a plant's
**facility-summed** CAMPD net to the single group holding the **most nameplate**
at that plant. At a mixed plant that is a guess, and East River's two candidate
groups differ by ~1 % of capacity.

### S2 — the kill condition for the East River attribution lane

The object is real **only if all three hold**:

* **(a)** ≥ **90 %** of the plant's 2023–2025 CAMPD `grossLoad` sits on
  turbine-family units — so the facility-summed series the derive consumed is
  the turbine half's;
* **(b)** the EIA-923 **GT : ST** net-generation ratio is ≥ **2 : 1** in every
  year — so the market's electric output really is turbine-dominated;
* **(c)** the model's own East River split is **inverted** relative to (b): the
  model's `ST_CHP ÷ CT_CHP` energy ratio at this plant exceeds the EIA-923
  `ST ÷ GT` ratio by ≥ **1.5×** in at least two of three years.

**If any of (a), (b) or (c) fails, the East River attribution lane is KILLED and
this session arms nothing.**

### S3 — one plant, or a fleet-wide derive question?

Count the NYISO plants whose `_fleet_nameplate_and_group` primary group differs
from the group carrying ≥ 60 % of the plant's CAMPD energy on the corrected
construction, and size them by measured TWh. **If East River is < 50 % of that
misattributed energy**, the object is a fleet-wide derive question and is
**handed forward, not armed here**.

### S5 — the required-move test

Bound the whole object by the plant's own measured energy: the most a correct
GT/ST attribution could move `CT_CHP` is East River's own EIA-923 GT–vs–model
gap. **If closing it entirely moves C1 `CT_CHP` by less than half of its −23.4 %
2025 error, say so and do not claim the object closes the class.**

---

## 4. S4 — the trap guard, binding on this session

nyiso-170 §5 refused an offer-band re-level (`offer_curve_by_group` stays `K`)
because the composition error is not built from hour-local substitutions;
nyiso-171 §2.5 showed the sign forbids a floor on the CHP side; and
**`CT_PEAKER`'s deficit is already adjudicated to root** — nyiso-90 (run lengths
already correct, starts 2–4× too few), nyiso-91 (98/98/92 % of measured energy
sits in runs the model never begins; the missing starts are deeply out of merit),
nyiso-96 (85.9/81.9/87.7 % of missing online-hours are below the plant's own
SRMC at the model's own price; 53–66 % of measured CT energy clears below bare
SRMC at its own zonal price; `tranche_startup_amortization` → `R`), with the
surviving cause recorded as **NYISO SCUC load-pocket security commitment with
BPCG make-whole — a sub-zonal data-intake and topology question, owner-scoped**.

**This session re-measures `CT_PEAKER` only to confirm that closed diagnosis
reproduces on the corrected construction. No `CT_PEAKER` lever is opened.** If
B2–B5 point at an offer re-level or a CT floor, that is recorded as confirmation
of the closed lines, **not** as a licence to arm one.

---

## 5. Governance

* **Rule 1 `[R-STRUCT]`** — a mechanism is armed only if the primary record
  identifies it; no adder, haircut or markup is built because a residual wants
  one. If an armed repair makes the backcast worse it stays in (rule 14
  `[R-ACCURATE]`) and the root cause is opened.
* **Rule 13 `[R-MEASURED]`** — every input here is a reproducible
  physical/market record used for **classification and attribution**
  identification only. No measured outcome is fed back to force a match.
* **Rule 19 `[R-ONE-MECH]`** — the enumeration (Object C / §6 of the finding)
  runs **before** any proposal, and any repair **replaces** an existing
  mechanism's target rather than stacking a new floor on its residual.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only. NYISO holds no `complete` marker
  (withdrawn 2026-08-30) and is absent from `final`; none is requested.
* **Rule 28** — the tested cells are updated in
  `docs/codebase-site/data/mechanism-matrix/NYISO.js` in this session, including
  ex-ante adjudications and rejections.

**An honest ex-ante adjudication with no solve is a legitimate outcome.** Seven
consecutive NYISO sessions have ended that way; no solve will be manufactured to
have something to register.
