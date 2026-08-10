# PREREG — miso-149: is the standing all-months CC under-dispatch an OVERLAY OVER-REMOVAL, and is MAY the same object or a different one?

**Session:** miso-149, 2026-08-10, branch `claude/miso-149-calibration-whwlu0`.
**Phase 0 — DIAGNOSIS FIRST.** No arm is authorised by this document; §9 fixes the
one narrow condition under which one could be, and the default is
**report-and-escalate** (the miso-147 / caiso-187 precedent).

**Keeper at entry:** `2026-08-09-miso-148-basis-aware`
(bundle `results/calibration/miso148_basis_B`).

**Concurrent-session check at open:** zero open MISO PRs (only
`claude/ercot-185-fault3-partial-layer-9nhbcx` is open), zero other remote MISO
branches. Re-checked at close.

---

## 0. §0 re-verification — from committed artifacts, not from the prompt

`scripts/calibration_verdict.py --run-id 2026-08-09-miso-148-basis-aware`, run at
HEAD `aa61791e` on committed artifacts only (no solve):

* **Determination `NOT-YET`**, rubric 3.2, scorable years 2023/2024/2025.
* **FAIL set `{C3a, C3b}`** — C3a 2025 **−15.6 %**; C3b 2025 **NRMSE 0.212**
  (gate 0.200). C3a/C3b 2023 and 2024 do not appear in the failure list, i.e.
  they PASS.
* **C3c** CAVEAT in all three years, **ledgered 1/1 SPENT** (`ACCEPTED
  MEASURED-INPUT LIMITATION`). The tail motivates nothing in this session.
* **C1 PASS** (2025 per-class SKIPPED — preliminary EIA-923), **C2 PASS** (2025
  gas/coal SKIPPED, descriptive `−9.9 % / +3.4 %`), **C4 PASS**, **C6 PASS**,
  **C8 PASS** with `ST_GAS` grounded-above-budget **34.1 / 35.8 / 48.4 %** and a
  **CT_PEAKER-2023** grounded entry at **16.8 %**.
* **Rule 22:** `frontend/data/backcast/calibration-complete.json` `complete` block
  holds **NEISO, NYISO, PJM only**; `final` holds no ISO. **MISO holds NO marker
  ⇒ 2023–2025 ONLY**, one invocation, all three years (rule 16).

The prompt's §0 is confirmed in every particular. Nothing below is read from the
prompt.

---

## 1. The two objects this session is chartered on, and why they are one instrument

The owner directive is the **2024/2025 mean-LMP level miss**. The queue head is:

* **Object A — the all-months CC commitment/displacement residual** (item 11 L3,
  left as OBSERVATION and NOT armed by miso-148). After the summer availability
  repair, S1-2025 `AV_CC − A_CC` still reads **−1,755 MW** (was −2,614) while the
  Jun–Sep MONTHLY deficit is essentially closed (−373 / −369 / −77 / +419 MW).
  S1 spans twelve months; its non-summer half is unexplained.
  `M_CC − A_CC` is negative in **every month of every year** (−2.0 to −7.3 GW).
* **Object B — the May object.** May-2025 over-prices **+12.4 %**, and miso-148
  MEASURED that the summer mechanism moves it by **−0.006 $/MWh**, i.e. not at
  all (2025 monthly Δ `0,0,0,0,−0.006,−1.836,−2.448,−1.403,−1.276,−0.003,0,0`).
  The May cause is **UNIDENTIFIED**. May's `AV_CC − A_CC` is
  **+1,074 (2023) / −50 (2024) / −1,201 (2025)**.

**The unifying, falsifiable claim this session tests.** Both objects share one
sign-definite symptom that no outage statistic can justify: **the model asserts a
CC capability BELOW what the same plants demonstrably GENERATED in the same
hours** (`AV < A`). In a historic backcast MISO's CC availability is

```
availability = statistical(1 − WEFOR, age escalation, basis-aware flat summer derate)
               × ufac(>=5-day CAMPD unit-outage windows)
               × sfac(unit_outage_short_windows, ARMED)
               × mgfac(unit_outage_maxgen_events, ARMED)
```

(`src/market_sim/data/fleet/arrays.py`; the MISO keeper's `meta.json` arms
`outage_source="historic"`, `coal_drop_pof=True`, `unit_outage_short_windows`,
`unit_outage_maxgen_events`; `unit_partial_outage_windows` is OFF;
`wefor_residual` is **unset ⇒ None**, so the FULL statistical WEFOR applies on
top of the measured overlay for `_POF_DROP_GROUPS` = {CC_REGULAR, CC_CHP,
ST_GAS, ST_CHP}). **Hypothesis H:** the all-months CC deficit is an
**over-removal by this availability stack** — i.e. the overlay layers remove
capacity-hours the CEMS record shows were producing — and **May is the same
over-removal with a spring-maintenance-window shape**, not a separate physics.

**H is directly falsifiable against the plants' own CEMS record, with ZERO
degrees of freedom and NO LP.** That is what this session measures.

### 1.1 DO-NOT-REDO, discharged (rule 28(a))

Checked against the charter's carried list and the §5.4 queue. This session does
**not** touch: the quantity family; the merit-order family (incl.
`gas_offer_margin` re-identification); congestion; item 5; floors; the
offer-LEVEL hypothesis; the offer-side class bridge; price-threshold splits; the
88-hours arithmetic; a LEVEL adder; `*_lw` re-derivation; trough pricing; the
CT/CC/coal bridge; seam classes; a fitted trough adder; the CC committed band
1.005; the coal deep-discount; the SOM PDF unit-hour corpus; FERC EQR; Michigan
PSCR; `cc_nameplate_summer_derate`; `miso_cc_coal_rebalance`; the exhausted
scarcity-tail list; re-deriving the miso-147 composition/monthly tables; the
January cold-snap candidates; CEMS/dispatch **bridging** (this session BRIDGES
NOTHING — it reads CEMS as a **falsification bound on an availability input**,
never as a dispatch target); **the summer flat-derate double count** (repaired
and promoted at miso-148 — not re-opened, `summer_derate_basis_aware` not swept
and not parameterised); the L2 merchant-CC population/rating audit; the
industrial-CHP/BTM boundary as "missing capacity"; and it does **not** expect any
summer-availability mechanism to move May.

**No prior MISO adjudication of `wefor_residual`, of the overlay's removal
magnitude, or of an overlay-vs-CEMS contradiction exists** — grep of
`results/calibration/`, the §5.4 queue and the matrix returns none for MISO.

### 1.2 Rule 25 `[R-ISO-SCOPE]` — what caiso-187 is, and what it is NOT here

`results/calibration/FINDING-caiso187-wefor-overlay-2026-08-09.md` measured the
*same instrument* on CAISO and **inverted its own charter's premise**: for CAISO
CC the overlay removes **24–35 % of capacity-hours against a ~10 % published
planned-plus-forced expectation**, so `max(0, W_c − X_c) = 0` and a
`wefor_residual` relief is immaterial there; it escalated on Branch C.

**That verdict does NOT transfer and is NOT evidence about MISO** (rule 25). It
enters MISO's lane as **`U` — untested**. What transfers is the **method**: the
frozen `residual_c = max(0, W_c − X_c)` identification and the idea of measuring
the overlay's own removal through the SHIPPED loader. Every MISO number below is
derived from MISO's own fleet, MISO's own extracts and MISO's own CEMS. **ERCOT's
0.02 and PJM's 0.015 `wefor_residual` values are neither adopted nor used as
evidence.**

---

## 2. Instruments, fixed before any measurement

* **Footing (reproduce-before-extend).** `_miso147_footing.py`,
  `_miso147_headroom.py`, `_miso147_january.py` re-run at HEAD and diffed
  field-by-field against their committed copies. These point at
  `KEEPER = results/calibration/miso132_ccmin_B` (hard-coded in
  `scripts/probes/_miso143_stack.py`), which is the keeper they were written
  against; that is why they reproduced with zero diffs at miso-148 and it is the
  correct footing target. **DISCLOSED (§10): the footing re-run was launched
  before this PREREG was pushed.** It is a re-execution of committed probes that
  produces no new statistic and adjudicates nothing; every *new* measurement in
  §3 was designed, and is executed, after the push.
* **New measurements target the CURRENT keeper**, `miso148_basis_B`, via a new
  module `scripts/probes/_miso149_overlay.py` that re-points the keeper without
  mutating the shared miso-143/147 modules (so footing stays reproducible). It
  calls `_miso143_stack.hygiene()` at every entry point (miso-140b §6) and reuses
  `_miso147_strata.py` for strata, the C3a weight, the CAMPD unit loader (direct
  per-state `campd-unit-level` reads, NEVER `campd.load_campd_hourly`; the
  str→int `facilityId` cast; the IL/TX facility-level shadow) and the
  gross→net parasitic factor.
* **The overlay is always read through the SHIPPED loaders**
  (`outages.unit_outage_derate_factors`, `unit_outage_short_derate_factors`,
  `unit_outage_maxgen_derate_factors`) with the keeper's own arguments — never a
  re-implementation — so what is measured is the overlay **the LP actually
  applies**.
* **One capacity convention throughout:** model capability is **NET**
  (`pmax × availability`, the fleet's own basis); CAMPD gross is converted with
  the pipeline's own per-family parasitic factor (`family_parasitic_factor`), the
  same conversion miso-147 used. No other basis appears.

---

## 3. Gates — pre-registered, with pre-committed branches

### G-F — footing (GATING; must PASS before any reading)

**G-F1** `_miso147_footing.json`, **G-F2** `_miso147_headroom.json`, **G-F3**
`_miso147_january.json` each reproduce with **ZERO field diffs** (exact equality
on floats as serialised; any diff is reported with its magnitude).
**On FAIL → `BRANCH-FOOTING-FAIL`:** the instrument, not the object, is the
finding; report the drift, measure whether it reaches CC availability, and make
no claim about either object this session.

### G-1 — THE CONTRADICTION CENSUS (GATING; adjudicates H)

Per family F ∈ {CC, CT, ST_GAS, ST_COAL}, per year, per month, at **plant-hour
grain**:

```
C_ph = model NET capability of plant p in hour h   = Σ_g∈(p,F) pmax_g × availability_g[h]
A_ph = CAMPD observed NET output of plant p, hour h = gross_ph × parasitic_F
contradiction_ph = max(0, A_ph − C_ph)             # the model asserts an incapability CEMS refutes
```

Reported as (a) mean MW over all hours, (b) mean MW over S1, (c) monthly mean MW,
(d) the count of contradicted plant-hours and the number of distinct plants,
(e) the share of the family's capacity-hours affected.

**Only plants present on BOTH sides enter** — a plant absent from the model fleet
is a population question, already adjudicated at miso-148 L2 (industrial CHP /
BTM boundary, `NOT` missing capacity), and is **excluded and reported
separately** so this census can never re-litigate it.

**Pre-committed decision rule, fixed before the number exists.** Let `Kcc` be the
2025 all-hours mean CC contradiction MW.

* **B-1 `overlay_over_removal`** — `Kcc ≥ 500 MW` **and** the monthly profile is
  non-summer-material (at least four non-Jun–Sep months ≥ 300 MW). H is
  supported: the all-months deficit is an availability over-removal.
* **B-2 `immaterial`** — `Kcc < 500 MW`. H is REFUSED at the availability layer;
  Object A is **not** an availability defect and G-3's displacement split becomes
  the load-bearing reading.
* **B-3 `summer_only`** — `Kcc ≥ 500 MW` but concentrated in Jun–Sep. This would
  mean miso-148's repair is incomplete rather than that a new object exists;
  reported as such and **not** used to re-open `summer_derate_basis_aware`.

The 500 MW bar is set now, from the object's own scale (the residual S1 deficit
is 1,755 MW; 500 MW is the smallest slice that could carry a material share of
it) and from miso-147's materiality floor convention (`max(300 MW, 5 %)`), not
from any measured contradiction value.

### G-2 — ATTRIBUTION: WHICH LAYER CAUSES IT (GATING for any mechanism claim)

The census is recomputed with each layer removed, one at a time, holding all
others at the keeper's setting: (i) statistical only (all three overlays = 1),
(ii) without `mgfac`, (iii) without `sfac`, (iv) without `ufac`, (v) with the
statistical WEFOR replaced by the caiso-187 frozen `residual_c = max(0, W_c −
X_c)`. Each is reported as the contradiction MW it leaves.

`W_c` = the model's OWN unfitted `THERMAL_AVAILABILITY` WEFOR base + age
escalation, capacity-weighted over the **MISO** fleet, `wefor_multiplier` held at
1.0 and **not re-derived** (rule 23 `[R-FROZEN-DERIVE]`). `X_c` = `1 −`
capacity-weighted mean of the **product** of the three shipped overlay
multipliers, pooled 2023–2025. **G-NODOUBLE:** a class with `X_c = 0` gets no
relief (`residual_c = W_c`), so the arithmetic can never invent headroom where
the overlay removed nothing. **G-SCOPE:** only `_POF_DROP_GROUPS` are eligible;
CT classes are never relieved (they have no overlay coverage and keep the full
statistical model) — any CT mismatch is reported as an open observation and not
acted on.

**A mechanism claim requires a NAMED layer carrying ≥ 60 % of `Kcc`.** Below
that the cause is distributed and the finding is "no single layer owns it" —
reported, not engineered around (rule 19 `[R-ONE-MECH]`: I will not stack a new
relief on an unattributed residual).

### G-3 — DOES OBJECT A EXIST AS A DISPLACEMENT OBJECT AT ALL? (GATING for the queue)

miso-147 measured `E − M ≈ 2,131 MW` of model CC "available AND in-merit **at the
REAL price**" and undispatched. **At the model's OWN price an LP optimum leaves
no such capability undispatched except through a nameable blocker**, so this
number cannot by itself establish a commitment/displacement object. Split it, on
the keeper's own committed sidecars:

1. **out-of-merit at the model's own zonal price on the BID basis** (P1 bids
   `mc_base + markup`, both in the fleet pack) — this is the **price-level /
   offer-surface object (item 9)**, not a commitment object;
2. **in-merit at the system price but out-of-merit at its own ZONAL price** —
   congestion;
3. **reserve-held** — from `reserve_family_<year>.parquet` (the only artifact in
   which a locational family's binding is observable);
4. **unexplained residual**.

**Pre-committed rule:** if leg 1 carries **≥ 60 %** of the 2,131 MW, then
**Object A DISSOLVES INTO ITEM 9** and I will say so plainly — the queue's
"commitment/displacement" framing is then a restatement of the level miss, not an
independent object. If legs 2+3 carry ≥ 40 %, a genuine blocker exists and is
named. This is pre-registered as an **against-interest** test: it can retire my
own charter's priority-1 object.

### G-4 — THE MAY SPLIT (GATING for Object B)

May-2025's `AV_CC − A_CC = −1,201 MW` is attributed to four pre-named, mutually
exclusive sources, each measured independently:

* **(a) the 2025 fleet under-carry** — the 9 EIA-860 rows / **594.7 MW** that were
  `OP` in `vintage_2024` and are dropped in 2025 (576.2 MW Cottonwood Energy,
  55358), measured as their May-2025 CEMS output;
* **(b) overlay over-removal** — G-1's May CC contradiction MW;
* **(c) COD ramp** (`cod_ramp_enabled`, default on) — May-2025 CC capacity
  withheld by the vintage ramp;
* **(d) residual** — unattributed.

**Pre-committed branches.** **M-1 `vintage_blocked`:** (a) ≥ 40 % of 1,201 MW.
Then May is **substantially the cross-ISO 2025-vintage defect**, that lane blocks
this one, and — per the charter — **I say so and stop rather than widen scope
(rule 25)**; no MISO mechanism is proposed for May. **M-2 `overlay_may`:** (b) ≥
40 %; May is the same object as A and inherits its mechanism. **M-3 `open`:**
neither reaches 40 %; May stays unidentified and is reported as such. The
2023/2024 May columns are measured identically as the **against-interest
control** — May-2023 has `AV−A = +1,074` and is not over-priced, so any May story
must explain the year pattern, not just 2025.

---

## 4. My prior — two-sided, numeric, falsifiable, scored against interest in the FINDING

| # | statement | P |
|---|---|---:|
| P1 | G-1 returns **B-1** (`Kcc ≥ 500 MW`, non-summer-material) | **0.60** |
| P2 | `Kcc` (2025, all-hours mean CC contradiction) lands in **[300, 2500] MW** | 0.70 |
| P3 | G-2 names a single layer carrying ≥ 60 % of `Kcc` | 0.45 |
| P4 | If P3 fires, that layer is `mgfac` **or** `sfac` (the two armed sub-5-day/event layers), NOT the ≥5-day `ufac` | 0.55 |
| P5 | MISO's `X_cc` **exceeds** `W_cc` (so `residual_cc = 0` and a `wefor_residual` relief is immaterial for MISO CC, as it was for CAISO) | **0.55** |
| P6 | G-3 leg 1 carries ≥ 60 % ⇒ **Object A dissolves into item 9** | **0.55** |
| P7 | G-4 returns **M-1 `vintage_blocked`** | 0.40 |
| P8 | G-4 returns **M-3 `open`** (May stays unidentified this session) | 0.35 |
| P9 | This session ends with **NO LP and NO arm** | **0.75** |

P5 and P6 are both stated **against my own lane's interest**: P5 predicts the
tidiest available mechanism is unavailable, and P6 predicts my priority-1 object
is not an object. Both are scored explicitly in the finding whatever they return.

---

## 5. Traps, each with its pre-committed counter-measurement

1. **The parasitic/gross–net basis.** A gross-vs-net slip manufactures a
   contradiction of ~5 % of CC output (~1 GW) out of nothing.
   *Counter:* the census is run on BOTH bases and both are reported; the verdict
   uses NET only, and B-1 must hold on the net basis alone.
2. **Plant-code / family crosswalk misses** (the miso-141/143 "unmapped klass
   reads zero" trap). *Counter:* the model-side klass vocabulary is asserted
   exactly (`EXPECTED_KLASSES`); every CAMPD plant with no model counterpart and
   every model plant with no CAMPD counterpart is **counted and reported**, never
   silently dropped, and excluded from the census both ways.
3. **A contradiction that is really the CC-steam-part or CHP boundary.**
   *Counter:* CC_CHP/CT_CHP/ST_CHP are reported as their own rows; the headline
   `Kcc` is quoted for **CC_REGULAR + CC_CHP** and also for **CC_REGULAR alone**,
   and B-1 must hold on `CC_REGULAR` alone too.
4. **Hour-alignment / timezone.** A one-hour or DST shift creates spurious
   contradictions at ramp edges. *Counter:* the census is re-run at ±1 h and the
   verdict must survive both; the diurnal profile of the contradiction is
   reported (an alignment artifact is ramp-hour-concentrated, a real over-removal
   is not).
5. **`cc_capacity_reconcile` is a deliberate measured cap** (7 plants, 2,713.8 MW
   to CAMPD demonstrated peak, miso-148 T6). It is a *cap at* demonstrated peak,
   so it cannot by construction assert capability below demonstrated output —
   *counter:* reconciled plants are flagged and their contribution to `Kcc` is
   reported separately; if they dominate, the census has a construction bug and
   B-1 is withheld.
6. **Reading CEMS as a dispatch target (rule 13).** *Counter, structural:* the
   only use of CEMS here is as a **lower bound on an availability INPUT** — "a
   plant that generated X MW was capable of at least X MW". No output is compared
   to CEMS, no unit is pinned, and no residual is fitted. Any mechanism that
   *emerged* from this would be an availability input with a forward analogue
   (the statistical stack), never a dispatch pin.
7. **Confirmation pressure toward an arm.** *Counter:* §9 makes
   report-and-escalate the default and P9 states at 0.75 that nothing is solved.

---

## 6. Kill gates — pre-registered; a breach is REPORTED AT FULL MAGNITUDE AND ESCALATED, never silent, never auto-fatal

These bind **only if §9's narrow arm condition fires**. With no solve they are
**not reached** — untouched, not "passing".

* **C3b-2025 NRMSE ≤ 0.212 AND MUST NOT RISE.** It is already failing its 0.200
  gate; a lever that pushes it further is escalated with the magnitude stated.
  Recovering it below 0.200 is a legitimate secondary objective but **never a
  fitting target**.
* **C3b 2023/2024 stay PASS** (0.082 / 0.125). **C3a 2023/2024 stay PASS**
  (−1.98 / −8.03 %).
* **MAY 2025** (+12.4 % over): its May effect is reported **explicitly, in $ and
  %, whatever the sign**. A mechanism that does not report its May effect has not
  been measured.
* **C1/C2 PASS** on gated years; 2025 descriptive vs EIA-930 only.
* **C8:** no material class's forced share rises; no D-4 breaks. ST_GAS is at
  48.4 % (2025) and CT_PEAKER-2023 at 16.8 % — headroom is thin.
* **C3c 1/1 SPENT** — the tail may not motivate anything. **Fail set ⊆ {C3a, C3b}.**
* **AGAINST-INTEREST BOUND (carried, binding).** 2023 carries nearly the same CC
  gap and **C3a-2023 PASSES**. I do **not** predict, claim or size any repair to
  close 2025's −15.6 %, and no number in the finding will be offered as progress
  against the level miss unless a solved arm shows it.

---

## 7. Solve plan and the decision rule — fixed in advance

**Default: NO SOLVE.** This is a Phase-0 diagnosis session.

**The single narrow condition under which an arm is authorised** — all four must
hold, and each is a gate above, not a judgement made afterwards:

1. **G-F PASSES** (footing reproduces);
2. **G-1 returns B-1** (`overlay_over_removal`, non-summer-material);
3. **G-2 names a single layer carrying ≥ 60 % of `Kcc`**; and
4. a **ZERO-CONTINUOUS-DOF** correction to that layer exists — a boolean over a
   data predicate, or a value fully determined by a frozen formula over committed
   data (rule 21 `[R-DOF]`). **A tolerance, fraction, threshold or scale I would
   have to choose is disqualifying** and sends the session to escalate.

If authorised: a **same-HEAD zero-delta CONTROL first**, then **ONE** mechanism
arm, each `--year 2023 2024 2025` in a **single invocation** (years sequential,
rule 12), both registered on the dashboard (rule 15) whatever they show. Any new
`ScenarioConfig` field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` **with its
declared default in the same commit** (verified by
`scripts/check_cache_key_registration.py` and
`tests/regression/test_persisted_identity.py`) and carries its matrix row in the
same PR (rule 28(c)).

**Promotion rule.** No promotion is contemplated by this document. If an arm ran
and improved structural integrity while regressing gates, that is an **escalation
to the owner** under the standing 2026-08-09 guidance — reported at full
magnitude, never silently promoted, never silently reverted — and it would
additionally require leave-one-year-out scoring within 2023–2025 (rule 22) before
any promotion could be proposed.

---

## 8. Disclosure (§10)

* The **footing re-run was launched before this PREREG was pushed** (§2). It
  re-executes committed probes and produces no new statistic; all §3 measurements
  are designed and run after the push.
* **MISO's designated keeper is not bit-reproducible at HEAD** (miso-148 K0, max
  |Δ| 912.5 MW, ~0.1 % of annual dispatch, scorecard essentially unchanged; HEAD
  drift, proven not to be that session's edits). This session **inherits that
  caveat and does not re-litigate it**. Consequence, binding: **no
  arm-vs-committed-keeper delta will be quoted anywhere**; a control is solved
  first if anything is solved at all.
* **Known-red at HEAD, not this session's and not a reason to stop** (verified at
  base 51d4e98 by miso-148):
  `tests/regression/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`,
  `test_soundness.py::TestEndToEnd::test_capacity_evolution_changes_fleet`, and 4
  `test_export` cases. If this session writes any source file, it re-runs the
  same selection against the reverted files to confirm it adds no NEW failures.
* **Data blockers, stated rather than worked around.** EIA-923 2025 is
  PRELIMINARY, so C1/C2 2025 are ungated and descriptive only. There is **no
  `data/raw/eia-860/vintage_2025/`**, so the 2025 fleet falls back to the
  canonical release which re-flags rows `OA`; `carry_operating_mothballs` is armed
  but **cannot fire for 2025** (its `vintage_<year>` precondition is unmet), and
  **9 rows / 594.7 MW** that were `OP` in `vintage_2024` are dropped — 576.2 MW of
  it Cottonwood Energy (55358), which CAMPD shows generating 4.70 TWh at p99
  1,140 MW in 2025. It is a live rule-14 defect in the one year carrying the level
  miss, its fix is **cross-ISO by construction**, and **this session will not fix
  it inside a MISO arm** (rule 25). G-4 measures how much of Object B it blocks.
* **Rule 22:** MISO holds no marker; only 2023–2025 are touched, in one
  invocation if anything is solved.
* **Rule 28(b)/(c):** the matrix cell and the §5.4 stamp are updated in **this**
  session whatever the outcome, rejections and no-arm outcomes included; a
  no-arm session mints **no cell verdict** (the miso-143…147 precedent) but does
  stamp the queue.
