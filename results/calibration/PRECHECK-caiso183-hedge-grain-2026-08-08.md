# PRECHECK — caiso-183 ARM B: the H-EDGE derive-**grain** repair

**Pre-registered BEFORE any scored metric is read.** This document fixes the object,
the design, the byte-equivalence obligations, the gates and the falsifiable direction
prediction. It is pushed and blob-verified before the repair is written and before any
LP is spent.

**Session scope:** CAISO only. Keeper `2026-08-06-caiso-175-tac-intake` (**NOT-YET**,
rubric v3.1, 8 criteria, **C3a the sole FAIL** — 2023 +4.2 % PASS, 2024 +11.5 % FAIL,
2025 +14.7 % FAIL, RT, band ±10 %). DOF ledger **11 / 8**. `complete` **NOT held**.
**HOLDOUT SPEND FREEZE ACTIVE** — solve years 2023 + 2024 + 2025 only, one bundle
(rule 16 `[R-ALLYEARS]`), years sequential, arms sequential (rule 12 `[R-PARALLEL]`).
`calibration-complete.json` and `holdout-freeze.json` are **owner acts** and are not
written by this session.

Model: Opus (rule 27 `[R-PUSH]` — scope writes `src/market_sim/` and `scripts/data/`).
Branch: `claude/caiso-183-hedge-grain-89bbuu`. Session basis
`7307c4d822721df0943c28f91542bd78443b5b32`.

---

## 1. THE OBJECT — located exactly, and it is a schema QUANTIZATION seam

`caiso-181` §2 confirmed the defect at **100 % concentration** of unit-grain CEMS
contradictions and sized it at **2.42 / 2.38 / 2.57 %** of envelope depth
(74–81 % of it edge-day), **sub-bar** against that session's 5 % B-2 bar and therefore
**not repaired there**. It filed the repair as its own open item (§5 item 1) needing its
own charter, precommit and gates. This is that charter.

**WRITER** — `scripts/data/derive_campd_unit_outages.py:1417-1437`. Detection is in
**hours**:

```
start = clock[s]
last  = clock[e - 1]
```

but the row is written in **days**:

```
"outage_start": start.strftime("%Y-%m-%d"),
"outage_end":   last.strftime("%Y-%m-%d"),
```

**LOADER** — `src/market_sim/data/outages.py:519-523` (and the identically-conventioned
second consumer at `:849-853`, `unit_outage_active_units`) re-expands the day pair to a
half-open hour window:

```
mask = outage_hour_mask(r.outage_start,
                        pd.Timestamp(r.outage_end) + pd.Timedelta(days=1), ...)
```

i.e. `outage_start` **00:00** → `outage_end` **23:00 inclusive**. Up to **23 h at each
edge** are asserted unavailable that the detector never detected — and by the
event-based contract (`detect_outages_eventbased`, break on any hour at
CF ≥ `ST_GAS_CF_PEAK` = 0.02) the hour immediately outside a window is a **running**
hour. Those are precisely the hours CEMS lights up. caiso-181 measured the maximum
distance of a contradicted hour from a window boundary at **22 h < 24, every year**,
with share-within-24 h **1.0000** — a hard bound, not a tendency.

**The repair is a strict GRAIN change: carry the detected start/end HOUR through the
schema and the loader. Zero DOF. No parameter. No threshold re-valued.** It is the
`ercot-174` BE-1/BE-2/BE-3 class, and that discipline is inherited verbatim.

### 1a. The repair is provably MONOTONE — it can only REMOVE derate

With `h0 = start.hour ∈ [0,23]` and `h1 = last.hour ∈ [0,23]`, the repaired window is

```
[ outage_start + h0 hours ,  outage_end + (h1 + 1) hours )
```

and the incumbent window is `[ outage_start + 0 , outage_end + 24 )`. Since
`0 ≤ h0` and `h1 + 1 ≤ 24`, the repaired window is a **subset of the incumbent window
for every row, unconditionally**. The repair therefore cannot invent unavailability; it
can only stop asserting unavailability the detector never detected. This is asserted
in-deriver (§3c) rather than assumed.

---

## 2. P0-1 — DO-NOT-REDO audit (rule 28 `[R-MECH-MATRIX]` duty a)

**This is NOT a re-test of the settled envelope DEPTH question.** The two are different
objects, and caiso-181 itself separated them:

| | caiso-181's SETTLED question | caiso-183's question |
|---|---|---|
| object | is the **detector** placing windows where CEMS contradicts them? | does the **CSV round-trip** widen windows the detector placed correctly? |
| instrument | L1 same-hour CEMS confrontation, unit grain | schema/loader grain carriage |
| result | **interior contradiction EXACTLY 0** over 599,736 interior in-window hours | **100 %** of contradictions are **edge**, max 22 h < 24 |
| verdict | **DEPTH IS CORRECT — reading (i) adopted, no repair indicated** | filed **UNREPAIRED** as §5 open item 1, "needs its own charter" |

caiso-181's own §5 item 1 names this repair, names its admissible form ("carry the
window's start/end **hour** through the schema and the loader — **zero DOF**"), and
states it is **not** done there. Re-opening depth would mean re-auditing, reverting or
haircutting the envelope; **this session does none of those**. The detector is not
touched, no window is added or removed, no duration floor moves, and no guard constant
is re-valued. The window **count** and the window **(plant, start-day, end-day)** tuples
are asserted **unchanged** (BE-3) — which is the formal statement that the depth
question is untouched.

**If BE-3 fails — i.e. if the change moves any window's identity — the arm STOPS and
reports**, because that would mean the change had reached the detector, which is exactly
the settled object.

Also confirmed **not** re-opened, per the standing DO-NOT-REDO list: `battery_dispatch_adder`
(permanent declared-residual DOF, all three exits closed at caiso-176/178/179);
the measured-offer-surface coverage extension (caiso-182, both identification tests
failed); `_degradation_cost_per_mwh` routing; the AS-power-reservation family
(caiso-74/127/129); every N–S topology lever (caiso-164 §0/§6, **FORBIDDEN**); the
seam/intertie family (caiso-142/143/167, **STRUCK**); `caiso_ps_charge_shape_anchor`
(**G**, input walled); `unit_outage_short_windows` / `unit_partial_outage_windows`
(caiso-180 I — coal-only detectors, **zero coal** in CAMPD's CAISO population).
`caiso_dam_outages` stays **U** and is **NOT armed here**.

---

## 3. THE DESIGN — backward-compatible, per-ISO adoptable, and byte-inert by default

**BINDING CONSTRAINT.** The writer and the loader serve **all six ISOs**. Any change
that alters another ISO's committed extract or its keeper's availability is **out of
scope and FAILS the arm** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d).

### 3a. Writer — a default-OFF emission flag

`derive_campd_unit_outages.py` gains `--hour-grain`, **default OFF**. When absent the
script is **byte-inert**: the same columns, the same values, the same order, the same
bytes. When present it appends two **optional** columns to the extract:

| column | value | range |
|---|---|---|
| `outage_start_hour` | `start.hour`, the hour-of-day of the detected first outage hour | 0–23 |
| `outage_end_hour` | `last.hour`, the hour-of-day of the detected **last** outage hour (inclusive) | 0–23 |

The two columns are appended **after** the incumbent header, so the incumbent
column order and every incumbent value is untouched by construction. Both are written
from the **same `start` / `last` objects** the day strings are already formatted from —
no second detection pass, no re-derivation of anything.

### 3b. Loader — consume WHEN PRESENT, fall back WHEN ABSENT

Both event-grain consumers in `outages.py` (`_unit_outage_factors_from_events`,
`unit_outage_active_units`) route through one new helper that returns the half-open
`[start, stop)` pair:

```
start = Timestamp(outage_start) + Timedelta(hours=int(outage_start_hour))   # absent -> + 0 h
stop  = Timestamp(outage_end)   + Timedelta(hours=int(outage_end_hour) + 1) # absent -> + 24 h
```

**The fallback is the incumbent behaviour by identity, not by approximation:** absent
columns are exactly `outage_start_hour = 0`, `outage_end_hour = 23`, and
`+ (23 + 1) hours ≡ + 1 day`. A row whose hours are NaN takes the same fallback, so a
partially-populated file degrades per-row to the incumbent window rather than erroring.

### 3c. The schema, the clean seam, and the in-deriver assertions

`data/dictionary/schema/unit-outage-events.schema.yaml` gains both columns as
`nullable: true` (the datatype is `allow_additional_columns: false`, so they must be
declared for a CAISO clean partition to validate); `scripts/data/curate_unit_outage_events.py`
passes them through when the source CSV carries them and omits them when it does not.

**Asserted INSIDE the deriver, so a failure is stop-the-line** (ercot-174 discipline):

1. every emitted `outage_start_hour` / `outage_end_hour` is an integer in `[0, 23]`;
2. the **monotone-subset invariant** of §1a holds for every row;
3. the **base-column projection** of the hour-grain frame is `.equals()`-identical to
   the frame the same run would build without the flag — the direct in-process
   statement that the two columns are additive and coupled to nothing.

A `pytest` case covers (1)–(3) and the loader-fallback identity of §3b.

---

## 4. P0-2 / P0-3 — the byte-equivalence obligations

The recipe the committed extracts were built from is fixed and documented
(`README-neiso64.md`, `FINDING-xiso2-…-2026-08-02.md` §4):

```
python scripts/data/derive_campd_unit_outages.py --iso <ISO> \
    --years 2018 2019 2020 2021 2022 2023 2024 2025 2026 --merit-order-guard
```

| leg | statement | bar |
|---|---|---|
| **BE-1** | the **UNMODIFIED** deriver at this head reproduces every committed extract | sha256-identical, all six ISOs |
| **BE-2** | with the hour columns **in the code**, each of the **five non-CAISO** extracts is still sha256-identical to committed **without the flag**, and sha256-identical to its own BE-1 output | byte-for-byte; **a moved byte FAILS the arm** |
| **BE-3** | **DETECTION is unchanged for CAISO**: same window count, same `(plant, start-day, end-day)` tuples, **same order**; only the expressed grain differs | exact; asserted in-deriver **and** in the probe |
| **P0-3** | with **no** hour columns present, the loader's availability mask is **bit-identical** to today's, for every ISO and every solve year | `np.array_equal`, elementwise |

### 4a. DISCLOSED IN ADVANCE — MISO's BE-1 is a KNOWN PRE-EXISTING mismatch

`FINDING-xiso2-outage-artifact-provenance-census-2026-08-02.md` §4 established, **before
this session**, that at HEAD **5 of 6** extracts reproduce byte-identically and **MISO
does not**: re-derivation is a strict **superset**, **+17 windows / 0 lost**, all 17
being **2022 COAL**, and the **layup companion byte-identical** — i.e. windows never
*detected* before, not detected-and-vetoed. That is a data-landing artifact of the
committed MISO blob and has nothing to do with this change.

**So the BE-2 bar for MISO is stated now, before measurement, and is STRICTER than
"identical to committed":** MISO's hour-grain-code-present output must be sha256-identical
to **its own BE-1 output at this head**, which is the only comparison that isolates this
change. The same self-comparison is recorded for all six ISOs. The committed-file
comparison is reported alongside for all six and is expected to read
**5 identical / MISO known-delta**. **A MISO result other than "identical to its own BE-1
output" FAILS the arm.** No MISO file is written; the pre-existing delta is reported, not
repaired, and not this session's object.

### 4b. Which files this session actually writes

**Exactly one data file changes: `data/raw/campd-unit-outages-CAISO.csv`**, re-derived
with `--hour-grain` over the committed span `--years 2018 … 2026` — the same span the
committed file already carries. The other five extracts and the layup companions are
**not re-derived, not rewritten, not touched**.

Re-deriving CAISO across 2018–2026 is **data preparation, not a holdout spend**
(rule 22 `[R-HOLDOUT]`, owner clarification 2026-08-06: *"what is held out is the SCORE,
never the DATA"* — an input is applied **consistently across all years** or it is not an
input). **Solving, scoring and registering remain 2023 + 2024 + 2025 only.**

---

## 5. P0-4 — the DIRECTION is pre-registered as UNKNOWN

The repair **removes** over-derate (§1a: strictly monotone), so it **adds available
capability** and would be expected to **lower** price — into a model already **+11.5 %**
(2024) and **+14.7 %** (2025) **over**. On that reasoning the C3a residual should
**narrow** in 2024 and 2025 and may **widen** in 2023 (which is +4.2 % and already
PASSing).

**That is a prediction, NOT a target.** It is written down so it can be falsified, exactly
as caiso-181's own duration prediction was falsified by its own measurement and reported
as such. **C3a will be reported at full magnitude whichever way it moves**, in all three
years, and a widening will not be smoothed, re-scoped or re-based.

**C3a IS REPORTED, NEVER TARGETED, AND IS NEVER THE PROMOTION BASIS** (rule 1
`[R-STRUCT]` — it is a live FAIL; rule 13 `[R-MEASURED]` — no quantity is tuned to it).
The **only** admissible promotion basis is that **the model no longer asserts
unavailability its own detector never detected** — a rule-14 `[R-ACCURATE]` correctness
statement that stands or falls independently of the residual.

**If the residual does not close, this session says so.** The honest remaining named
contributor is the **WALLED hourly pumped-storage water state**
(`FINDING-caiso140` §B / caiso-141 A2) — an **owner-funded intake decision, not a session
lever**. No close will be manufactured.

---

## 6. GATES — pre-registered, fail-closed, and they FAIL the arm

| gate | statement |
|---|---|
| **G-DOF** | DOF ledger **EXACTLY 11 / 8**. Any increase is an automatic fail. ARM B is zero-DOF, so 11/8 is the correct and achievable bar. *(caiso-182 §5 filed a G-DOF granularity defect for **coverage-type** arms — an owner item that does **not** apply here.)* |
| **G-NOFIT** | **ZERO** new fitted scalars; no threshold re-valued. The frozen detector constants `_MIN_DAYS`, `_SMOOTH_DAYS`, `_CEILING_FRAC`, `_RUN_FLOOR_CF`, `_BASELOAD_CF`, `ST_GAS_CF_PEAK` are imported **verbatim** and diffed against their committed values (rule 23 `[R-FROZEN-DERIVE]`). |
| **G-SIXISO** | BE-2 above: the five non-CAISO extracts **byte-unchanged** (each vs its own BE-1 output; §4a fixes MISO's form in advance). |
| **G-CONTRACT** | The repaired envelope must still clear caiso-181's **B-1** (interior CEMS contradiction ≈ 0). `scripts/probes/_caiso181_cems_confrontation.py` is re-run on the repaired extract; **edge contradictions must COLLAPSE while interior stays 0**. |
| **G-DEPTH** | The repaired depth must **not** fall below the superseded **PRE** envelope — see §6a, which fixes the two readings **now**, before measurement. |
| **G-C1** | **C1 free-class fuelmix PASS** on every free class, all three years. |
| **G-CAISO180** | Protective band: `|ΔTWh|` must not exceed the full regeneration leg it reverses — **CC_REGULAR 0.11 / 0.44 / 0.67**, **ST_GAS 0.03 / 0.13 / 0.07**, **CT_PEAKER 0.02 / 0.04 / 0.06**. Exceeding it = over-corrected past the whole leg. |
| **G-PROT** | **C6 and C8 PASS**; C8 stays **SCORED** (`legitimacy_diagnostics.json` registered with the bundle). |
| **G-LOYO** | Any verdict flip is scored **leave-one-year-out within 2023–2025** BEFORE promotion. |
| **CONTROL** | **MANDATORY if any arm solves** — see §7. |

### 6a. G-DEPTH — a pre-registration integrity note, filed BEFORE measurement

G-DEPTH as chartered is an **absolute floor** at the PRE (A1) envelope depth
**38.03 / 38.80 / 49.99 M MW-h**. Its stated rationale is *"a repair undoing more than
the regeneration added is a revert in disguise"*.

**In 2023 that floor is already breached by the UNREPAIRED keeper**, and this is
arithmetic from caiso-180's own committed record, not a result of anything done here:

| M MW-h | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **A1 PRE** (the G-DEPTH floor) | 38.03 | 38.80 | 49.99 |
| **A0 GUARD** (the committed keeper envelope, unrepaired) | **36.68** | 42.88 | 55.43 |
| A0 − A1 | **−1.35** | +4.08 | +5.44 |

In 2023 the regeneration **removed** 1.35 M MW-h of depth, so the gate's premise — that
the regeneration *added* depth for a repair to undo — does not hold that year, and a
literal reading fails the arm **before the repair does anything at all**.

**Both readings are therefore fixed here, in advance, and BOTH will be reported:**

* **G-DEPTH (literal)** — repaired depth ≥ **38.03 / 38.80 / 49.99**. Reported as
  chartered, with the note that its 2023 leg is breached by the baseline.
* **G-DEPTH′ (delta form, the charter's intent expressed where it is well-defined)** —
  the depth the repair itself removes, `A0 − repaired`, must not exceed
  `|A0 − A1|` = **1.35 / 4.08 / 5.44 M MW-h** for that year. Because the repair is
  monotone (§1a), `A0 − repaired ≥ 0` always, so this is a genuine one-sided bar in all
  three years including 2023.

**G-DEPTH′ is the binding form** and it is non-trivial: caiso-181's measured per-window
edge cost (1,208 / 1,780 / 1,910 MW-h) across the committed 547 / 458 / 635 windows
implies a removal of roughly **0.66 / 0.82 / 1.21 M MW-h**, i.e. ~1.8–2.2 % of depth —
comfortably inside the bar, but not so far inside that the bar cannot bind. **If the
measured removal exceeds G-DEPTH′, the arm FAILS**; if it clears G-DEPTH′ but breaches
the literal 2023 floor for the baseline reason above, that is reported as the
pre-registered arithmetic, not as a pass talked past.

---

## 7. CONTROL — mandatory, and reproduced from the bundle, never from memory

If any arm solves, a **fresh same-head control** is solved first. `caiso-180` **and**
`caiso-181` both measured same-head drift at **exactly $0.000**; the control must
reproduce the keeper **to the cent**, and **if it does not, THAT is the finding** and the
arm's own numbers are not interpretable.

* Reproduced via **`--replay-bundle results/calibration/caiso175_tac_intake`** —
  **never** a remembered CLI string.
* `scenario_config` identity verified fail-closed on the **caiso-180 L1 / L2 / L3**
  split (L1 the pre-registered predicate over the keeper's own 692 keys; L2 arm-to-arm
  identity over the full union; L3 additive schema drift disclosed and gated on
  code-default + non-CAISO scope).
* `scripts/probes/_caiso180_arm_identity.py` is **REUSED**. Its **§3a leg-2 ordering
  gate is WITHDRAWN AS MALFORMED** (window count is not envelope depth) and is **not**
  reinstated.
* The sha ladder is kept: each arm's pre-solve and post-solve sha256 of
  `data/raw/campd-unit-outages-CAISO.csv` must equal each other and that arm's intended
  envelope state. An arm whose envelope moved under it is **void**.

**Arm ladder (sequential, rule 12):**

| arm | envelope | extract sha |
|---|---|---|
| **B0 CONTROL** | committed, day-grain | `c4ded33df08de5927fd58fa7200320353e73ceedfeb0084586ffd2e32f93ff5e` |
| **B1 TREATED** | re-derived, **hour-grain** | recorded at derive time |

---

## 8. STOP CONDITIONS

The session **registers nothing, spends no LP, and files the negative result** if:

1. **P0 establishes the repair cannot be made backward-compatible across all six ISOs**
   (BE-2 / G-SIXISO fails, or the loader fallback of P0-3 is not bit-identical);
2. **BE-3 fails** — the change reached detection, i.e. the settled depth object (§2);
3. **BE-1 fails for CAISO** — this head cannot reproduce the committed extract, so no
   comparison is trustworthy. *(Positive control already observed: the environment
   reproduces `campd-unit-outages-CAISO.csv` at `c4ded33d…`, the caiso-180 A0 sha.)*
4. the **CONTROL** does not reproduce the keeper to the cent — reported as the finding.

## 9. Governance

Rules engaged: 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 14 `[R-ACCURATE]`, 15 `[R-DASHBOARD]`,
16 `[R-ALLYEARS]`, 21 `[R-DOF]`, 22 `[R-HOLDOUT]`, 23 `[R-FROZEN-DERIVE]`,
25 `[R-ISO-SCOPE]`, 27 `[R-PUSH]`, 28 `[R-MECH-MATRIX]`.

No `ScenarioConfig` field is added by this design (the change is a data-grain carriage,
not a mechanism switch), so rule 28 duty (c) is not engaged; duty (b) **is** — the CAISO
matrix cell and the §5.2 header block are updated in **this** session, whatever the
outcome. Every arm that solves is registered (rule 15) with `legitimacy_diagnostics.json`,
all three years in **one** bundle (rule 16). Verdicts never cross an ISO boundary
(rule 28 duty d): nothing measured here fills another ISO's cell, and the other five ISOs
enter as **untested** for the hour-grain adoption.
