# PRECHECK — caiso-181: IS THE REGENERATED CAISO OUTAGE ENVELOPE **DEPTH-CORRECT**?

**Pushed and blob-verified BEFORE any metric is read.** Nothing in this session's measured
surface — no confrontation share, no contradicted MW-hour, no C1/C2/C3a/C3b/C3c/C4/C6/C8
value, no class energy, no price — had been looked at when this file was written. What HAD
been read, and is reported in §2 as part of the pre-registration rather than concealed, is
**input-side census and SOURCE CODE only**: file existence/row counts/column vocabularies,
one sha256, and the detector's own construction as written in `scripts/`. Those are facts
about an *input* and about the *instrument*; none is a model output and none is a
confrontation result.

Session: caiso-181. Branch `claude/caiso-181-envelope-depth-aw9gpq`. **CAISO ONLY.**
Keeper at session start: `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1,
8 criteria, **C3a the sole FAIL** — 2024 +11.5 %, 2025 +14.7 % RT). DOF ledger 11 / 8.
CAISO does **not** hold `complete` (withdrawn by the owner 2026-08-06).
The **holdout spend freeze is ACTIVE**.

---

## 0. The scope discipline this session binds itself to, stated first

- **2023, 2024, 2025 ONLY.** No other year is solved, scored, registered or read as a
  scored quantity. If any arm solves: one bundle per arm, all three years, rule 16
  `[R-ALLYEARS]`; years sequential inside a run, arms sequential (rule 12 `[R-PARALLEL]`).
- **`calibration-complete.json` and `holdout-freeze.json` are OWNER acts. This session
  writes NEITHER**, in any field, including the `intake_log`.
- **No other ISO's keeper shard, registry sidecar, status part or bench file is touched.**
- **No offer-curve re-tune is opened this session** (§9) — even though rule 23's
  `[R-FROZEN-DERIVE]` re-derive trigger is technically satisfied by the 2026-07-24 data
  change. That is the memo §5 sequencing ruling applied to CAISO, and it is binding here.
- The default expectation is **no LP at all**: Route 1 costs zero solves. An LP is spent
  only if §7 branch **II** fires.
- The re-audit is a **measurement**, not a promotion. The pre-registered expectation is that
  the keeper designation is **UNCHANGED** at the end of it.

---

## 1. The object, and the framing that governs it

### 1a. What caiso-180 left open

caiso-180 measured the 2026-07-24 CAMPD regeneration at **+0.60 / +1.20 / +1.70 pp C3a**
(the guard leg inert at −0.10 pp) and showed the mechanism is a window-**SHAPE** change: the
superseded detector made **fewer but longer** windows (median 14.7–16.6 d), the current one
makes **more and shorter** ones (10.5–11.6 d). The deeper envelope removes CC_REGULAR
(−0.44 / −0.67 TWh in 2024/2025) with ST_GAS / CT_PEAKER backfilling, lifting price exactly
where the model already runs hot. Under rule 14 `[R-ACCURATE]` the accurate envelope stayed
and the residual was filed as an **OPEN ROOT-CAUSE ISSUE**.

Committed envelope depth, per year (`_caiso180_outage_reaudit.json`):
**36.68 / 42.88 / 55.43 M outage MW-h**.

**THE QUESTION THIS SESSION ASKS:** is that depth **CORRECT**, or is the model asserting
unavailability that the units' **own CEMS record contradicts**?

### 1b. THE FRAMING — memo §3, fixed here before any measurement

`DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md` §3 establishes that an over-deep
outage construct and the defect it conceals are **one defect seen from two sides**:
multiplying layers *"hides the fault-3 error by over-derating everywhere; removing the
product exposes it."*

**The CAISO analogue is exact in form.** The STALE envelope fit **BETTER**
(C3a +3.7 / +10.4 / +13.1 vs the current +4.2 / +11.5 / +14.7). Under memo §3 that is the
signature of a **COMPENSATING ERROR PAIR** — it is **NOT** evidence the stale envelope was
right, and it is **NEVER** grounds to revert (rule 14). Two readings are therefore live, and
both are pre-registered here:

- **READING (i) — DEPTH-CORRECT / EXPOSER.** The new envelope is depth-correct, and it
  **EXPOSED a pre-existing over-pricing defect** that the phantom-long windows were masking.
  The +1.1 / +1.6 pp belongs to the offer curves, not to the envelope.
- **READING (ii) — OVER-DERATING / ITSELF-THE-DEFECT.** The new envelope **over-derates**;
  the depth is a construction error and is itself the thing to repair.

**WHAT SEPARATES THEM** — stated in advance so it cannot be chosen afterwards: the
**presence, magnitude and LOCATION of a same-source CEMS contradiction**. Reading (i)
predicts the detector's windows sit on genuinely dead hours, so the confrontation returns
**≈ 0** at the detector's own standard. Reading (ii) predicts windows overlaying hours the
unit's own CEMS shows **generating**, at material magnitude. The two cannot both hold: the
test is against the detector's **OWN SOURCE**, so it is decidable, and §4's bars decide it.

### 1c. WHAT DOES **NOT** TRANSFER from PR #3685 (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d)

The ERCOT-148/149 collision is a **product of two layers**. **CAISO HAS NO SUCH PRODUCT** —
re-verified at caiso-180 §6 and re-confirmed in §2 below: `unit_partial_outage_windows`,
`unit_outage_short_windows` and `unit_outage_maxgen_events` are **all off**, the CAISO
partial and short files are **header-only**, and `campd-partial-outages.csv` (the plant-grain
second layer) is **ERCOT-only**. **CAISO runs the WINDOW LAYER ALONE.**

Binding consequences, fixed here: this session does **not** import the composition question,
does **not** propose a `min()`/product rule, and does **not** treat G-COAL148 as relevant
(CAISO has **zero coal** — §2c). What transfers from the memo is its **DIAGNOSTIC METHOD**
(§3) and its **SEQUENCING RULING** (§9) — **nothing about its verdicts.**

---

## 2. PHASE 0 — the two routes, and what the input census established

### 2a. ROUTE 1 IS AVAILABLE AND NEEDS **NO NEW DATA**

Everything Route 1 requires is committed: the envelope
`data/raw/campd-unit-outages-CAISO.csv` (sha256 **`c4ded33d…f93ff5e`** — **byte-identical to
caiso-180's GUARD/HEAD state**, so this session audits exactly what the keeper reads) and the
source it was derived from, `data/raw/campd-unit-level/CA_{2023,2024,2025}.parquet`.
**Zero intake, zero DOF, zero LP.** PR #3685 is what makes this instrument available;
caiso-180's branch (b) wall does not apply.

### 2b. ROUTE 2's COMPARATOR **EXISTS**, AND IT IS ALREADY CURATED AND COMMITTED

Recorded as a Phase-0 census fact, **before** any comparison is made. CAISO **does** publish a
usable generator outage series, and this repo already intakes it (owner-directed, caiso-104):

| artifact | state |
|---|---|
| `data/raw/caiso-dam-outages/daily/cnog-YYYYMMDD.xlsx` | **1,094 daily snapshots**, tracked in git |
| `data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet` | **794,103 episode rows**, span 2021-05-07 → 2025-12-31, tracked |
| `data/raw/reference/caiso-resource-eia-crosswalk.csv` | 98 RESOURCE ID → (plant_code, plant_group) rows, tracked |
| `market_sim.data.caiso_outages.caiso_dam_outage_derate_factors` | wired loader |
| `ScenarioConfig.caiso_dam_outages` | registered field, **default off** |

Source: CAISO's daily **Curtailed and Non-Operational Generator Prior Trade Date Report**
(sheet `PREV_DAY_OUTAGES`) — OUTAGE MRID, RESOURCE ID, OUTAGE TYPE, CURTAILMENT START/END,
CURTAILMENT MW, RESOURCE PMAX MW, NQC MW. This is the first of the charter's named
candidates ("OASIS Prior Trade Date curtailed-generation / outage reports") and it is the
strongest of the three; the Monthly/Annual Market Performance and DMM reports are not
reached unless it fails.

**Its matrix cell is `U` — UNTESTED, not `R`/`I`/`G`** (`mechanism-matrix.js`,
`ercot_thermal_dam_availability` row, note *"CAISO built untested (caiso_dam_outages)"*).
So consulting it is **not** a DO-NOT-REDO violation. **It remains SECONDARY per the charter**
and is reached **only if Route 1 is ambiguous** (§7 branch III). **No arm arms
`caiso_dam_outages` in this session** — that is a separate mechanism needing its own
pre-registration, D-4 window and cell adjudication, and this session does not take that
authorization by inference.

### 2c. THE INSTRUMENT'S OWN CONSTRUCTION — read from source, and it makes the test razor-sharp

Two code facts establish the predicate. Both are read from `scripts/`, neither is a
measurement.

**(1) 100 % of CAISO's committed envelope is EVENT-BASED, and the event detector's contract
is EXACT-ZERO.** The committed file's `plant_group` vocabulary is
**{CC_CHP, CC_REGULAR, CT_CHP, ST_GAS}** — **no COAL row exists**. The deriver branches on
the *unit's own fuel* (`derive_campd_unit_outages.py`: `elif unit_is_coal[uid]:
detect_outages(...)` **else** `detect_outages_eventbased(...)`), and CAMPD's CAISO population
carries **zero coal** (caiso-180 §6: Natural Gas / Other Gas / Pipeline Natural Gas / Wood).
So every committed CAISO window is produced by `detect_outages_eventbased`, whose docstring
is its contract:

> *"An outage is a maximal run of consecutive hours whose CF stays strictly below `cf_peak`
> for **every** hour … A single hour at/above `cf_peak` breaks the window."*

with `cf_peak = ST_GAS_CF_PEAK = 0.02`. **The detector therefore admits ZERO in-window hours
at CF ≥ 0.02, by construction.** That is a falsifiable, zero-DOF, zero-tolerance
internal-consistency predicate — a sharper instrument than the ERCOT fault-3 original, and
the reason Route 1 is primary.

**(2) THE CSV ROUND-TRIP IS LOSSY, AND IT EXPANDS EVERY WINDOW AT BOTH EDGES.** The detector
works in **HOURS** — a span `[s, e)` on the year clock. The writer drops the hour-of-day:

```python
start = clock[s];  last = clock[e - 1]
"outage_start": start.strftime("%Y-%m-%d"),
"outage_end":   last.strftime("%Y-%m-%d"),
```

and the loader reconstructs **day-granular**, `outage_hour_mask(outage_start, outage_end +
1 day, …)` — i.e. `outage_start` **00:00** through `outage_end` **23:00** inclusive
(`outages.py::_unit_outage_factors_from_events`).

So a span truly beginning at hour 14 of day *D* is derated from hour **0** of day *D*, and a
span truly ending at hour 6 of day *E* is derated through hour **23** of day *E*. Up to
**23 h at each edge** are asserted unavailable that the detector **never detected** — and by
the event-based contract the hour immediately outside a window is a **running** hour, so
those added hours are exactly where CEMS is most likely to show generation.

**HYPOTHESIS H-EDGE, pre-registered from code before measurement:** any contradiction Route 1
finds is **EDGE-CONCENTRATED** — a day-granular quantization seam in the CSV schema — rather
than interior. This is CAISO's structural analogue of ERCOT fault 3 (*a coarser-grained
representation used as a finer-grained ceiling*), and it predicts a **per-window**, not
per-MW-h, error: **more windows ⇒ more edges ⇒ more over-derate**, which is precisely the
direction caiso-180's shape result (fewer/longer → more/shorter) would drive.

**H-EDGE is a hypothesis, not a finding.** It is pre-registered so that an edge-dominated
result cannot be presented as a post-hoc explanation, and so that an **interior**-dominated
result — which would falsify it and indicate a different, deeper defect — is equally
reportable. §4 measures the split; §7 branches on it.

### 2d. Gate states re-confirmed (caiso-180 §6, cited not re-minted — rule 28 DO-NOT-REDO)

`unit_outage_short_windows` **E — empty by construction** (coal-only detector, zero CAISO
coal); `unit_partial_outage_windows` **E — same**; `unit_outage_maxgen_events` **DATA GAP**
(no CAISO registry exists). Not re-tested here, not armed here.

---

## 3. ROUTE 1 — the instrument, specified exactly

**The ercot-172 fault-3 confrontation, ported.** ERCOT's fault 3 is *"a multi-week average
plateau used as an hourly ceiling"* (W A Parish h2827: ceiling 0.3855 vs same-hour CEMS
0.5563; unit-scoped 0.3630 vs 0.7843). CAISO's window layer is a **binary full-stop**, so the
literal plateau fault cannot occur — but its **CLASS** can: a multi-day window asserting
**ZERO** where the unit's own CEMS shows generation.

Probe: `scripts/probes/_caiso181_cems_confrontation.py`. **No LP.** Instruments **REUSED, not
re-implemented**: `derive_campd_unit_outages.build_capacity_index` / `unit_capacity_mw` (the
detector's own CF basis), `campd.CAMPD_UNIT_PLANT_REMAP`, and — for L2 — the shipped loader
`outages.unit_outage_derate_factors(year, iso="CAISO")` itself.
Record: `results/calibration/_caiso181_cems_confrontation.json`.

### 3a. L1 — UNIT-GRAIN INTERNAL CONSISTENCY (the primary measurement)

For every committed window row overlapping 2023 / 2024 / 2025, joined to its own unit's CEMS
series on `(facility_id after CAMPD_UNIT_PLANT_REMAP, unit_id)`, over the **loader's own
reconstruction** (`outage_start` 00:00 → `outage_end` 23:00, clipped to the year):

| quantity | definition |
|---|---|
| `n_hours` | in-window hours on the year clock |
| `share_reported_running` | share of in-window hours with **reported** `grossLoad > 0` |
| `share_above_contract` | share of in-window hours with **CF ≥ 0.02** (`ST_GAS_CF_PEAK`) — *the detector's own break threshold* |
| `share_above_realrun` | share with **CF ≥ 0.05** (`REAL_RUN_CF`) — the stricter "genuinely running" bar |
| `cems_mwh_in_window` | Σ `grossLoad` over in-window hours — **the MW-hours the envelope zeroes that CEMS says ran** |
| `edge` vs `interior` | every quantity split by whether the hour falls on the window's **first or last calendar day** (the H-EDGE seam) vs strictly inside |

**Conventions fixed in advance, each in the conservative direction:**

- **CF basis** = the detector's own `detect_mw` (unit nameplate), obtained by calling the
  deriver's `unit_capacity_mw(...)` — **not** the CSV's `unit_capacity_mw` column, which is
  the steam-augmented *derate* share and would understate CF at combined-cycle CTs.
- **A missing/NaN CAMPD hour is NOT a contradiction.** CAMPD omits non-operating hours; the
  detector zero-fills them. Only a **reported positive gross** counts. This can only
  **under**-count contradictions, never manufacture one.
- **Clock.** Both sides are placed on the same CAMPD `date`+`hour` calendar-year clock — the
  clock the detector was built on — so L1 carries **no timezone ambiguity by construction**.
- **Scope.** The committed envelope file only. Windows moved to
  `campd-unit-outages-layup-CAISO.csv` are **not** in the envelope and are **not** tested.
- **Distribution, not a mean.** Per-window shares are reported as a full distribution
  (p50 / p90 / p99 / max and the count above each bar), and **split by window-duration
  quartile** — caiso-180's shape result predicts any residual concentrates in the **LONGEST**
  windows, which is a falsifiable secondary prediction (§4c).

### 3b. L2 — ENVELOPE-GRAIN "IMPOSSIBLE MW" (the decision-relevant magnitude)

L1 audits the detector; **L2 audits what the LP actually sees**, and is the direct port of
ercot-172's `f_ceiling` vs `f_CEMS`. For each `(plant_code, plant_group)` bin and hour:

- `f_model` = the shipped loader's availability multiplier
  (`unit_outage_derate_factors(year, iso="CAISO")` — **the loader itself, not a
  re-implementation**);
- `f_CEMS` = Σ CAMPD gross of that bin's units in that hour ÷ the bin's plant capacity
  (`outages._iso_plant_capacity("CAISO")`, units routed by
  `outages._generic_unit_outage_target` — the same routing the factors use);
- an hour is **IMPOSSIBLE** when `f_CEMS > f_model`: the model asserts less capability than
  the plant demonstrably produced.

Reported: impossible bin-hours, impossible MW (`(f_CEMS − f_model) × plant_cap`), and
**impossible MW-h as a share of committed envelope depth** (36.68 / 42.88 / 55.43 M).

*L2 inherits a ±1 h alignment uncertainty at window boundaries (CAMPD local standard time vs
the model's year clock). Because the derates are day-granular blocks this can only touch the
two boundary hours of each window, which land in the `edge` bucket regardless. **L1 is the
gating measurement; L2 is the magnitude.*** Stated now, not after.

---

## 4. THE BARS — what magnitude would justify **ANY** change

Fixed before measurement. Sub-bar results are reported at full magnitude and labelled
**immaterial**; they are never rounded to "no effect".

### 4a. B-1 — DETECTOR-CONTRACT VIOLATION (L1, **the primary gate**)

The event-based contract admits **zero** in-window hours at CF ≥ 0.02. Bar:

> **B-1 fires if INTERIOR `share_above_contract` exceeds 0.5 % of interior in-window hours in
> ANY year.**

Rationale for a non-zero bar on an exact-zero contract: the day-granular round-trip and the
zero-fill can leak a handful of hours without a construction defect. 0.5 % is ~1 hour in 200
— far below anything capable of producing a 1.1–1.6 pp price effect, and above pure noise.
**Interior**, because an edge violation is the H-EDGE schema seam (B-3), a different defect
class with a different repair.

### 4b. B-2 — ENVELOPE DEPTH (L2, the materiality bar)

> **B-2 fires if CEMS-contradicted (impossible) MW-h ≥ 5 % of committed envelope depth in ANY
> year.**

Rationale, set from the effect under investigation and **not** from any value read this
session: caiso-180's total A1→A0 depth change was −1.35 / +4.08 / +5.44 M MW-h against depths
of 36.68 / 42.88 / 55.43 M — i.e. **3.7 % / 9.5 % / 10.9 %** of depth — and that change
carried the +0.5 / +1.1 / +1.6 pp C3a. A 5 % depth error is therefore the same order as the
object, which is the right scale for "material".

### 4c. B-3 — THE H-EDGE SPLIT and the duration prediction (diagnostic, **non-gating**)

Reported, never gating, and pre-registered so neither outcome can be chosen post-hoc:

- **EDGE-dominated** (≥ 70 % of contradicted MW-h on first/last calendar days) ⇒ the defect
  is the **day-granular CSV schema**, and the repair is an **hour-granular** derive/schema
  change (§8), not a depth haircut.
- **INTERIOR-dominated** ⇒ H-EDGE is **falsified** and the defect is in the detection rule
  itself — a deeper finding, reported as such.
- **Duration prediction:** contradictions concentrate in the **LONGEST** windows (caiso-180's
  shape result). A concentration in the **SHORTEST** windows falsifies that reading and is
  reported as a falsification, not smoothed over.

### 4d. THE NEISO PRECEDENT IS A **CONSTRAINT, NOT A LEAD** — and Route 1 is immune to it

Charter §9 closed NEISO's 1.29–1.36× over-count as a **DEFINITIONAL SEAM** (published =
*unavailability*; the CEMS detector = *non-operation*), not recoverable by any admissible
discriminator, and neiso-68 showed restoring the envelope would inject phantom dispatch.

**Route 1 is immune by construction**: it compares the detector to the **SAME CEMS record it
is built from**, so a hit is a **CONSTRUCTION ERROR**, not a definitional difference. The
charter §9 seam bounds **Route 2 only** — and if Route 2 is ever reached (§7 branch III), any
CNOG-vs-CAMPD gap must be adjudicated against that seam **first**, and a gap explicable by it
is **not** evidence of a construction defect. Pre-registered so the distinction cannot be
blurred later.

---

## 5. WHAT THIS SESSION MAY NOT DO

- **No offer-curve re-tune** (§9). Binding.
- **No revert to the stale envelope**, in any branch. Rule 14 `[R-ACCURATE]` is explicit that
  a degraded criterion does not revert a correct measured input, and rule 1 `[R-STRUCT]` that
  a structurally-correct input is never judged by whether it improves the fit. The stale
  envelope's better fit is a **compensating-error signature** (§1b), not evidence.
- **No quantity tuned to the C3a residual**, in any form — no adder, no haircut, no
  fitted scalar (rule 13 `[R-MEASURED]`). **C3a is a LIVE FAIL, so a C3a move is REPORTED and
  is NEVER the promotion basis** (rule 1).
- **No off-registry channel** (rule 24 `[R-REGISTRY]`): a repair is a change to the derive and
  its output bytes, never an env var or a CLI-only knob.
- **No mechanism armed** that is not pre-registered here — including `caiso_dam_outages`.

---

## 6. IF A REPAIR IS INDICATED — its form, and the gates it must clear

A repair is a **DERIVE-GRAIN CONSTRUCTION CHANGE under rule 23 `[R-FROZEN-DERIVE]`**: its own
precommit, its own gates, and a **source-data / construction citation** — **never** an
offer-curve adder, **never** a haircut, **never** anything tuned to C3a. The re-derivation
commit cites the **construction defect measured here**, not a residual.

Mirroring the memo's *"carry the protective gate live"* discipline — CAISO's analogue of
G-COAL148 is the **C1 free-class fuelmix on CC_REGULAR / ST_GAS / CT_PEAKER**, whose
caiso-180 moves are on record (CC_REGULAR −0.11 / −0.44 / −0.67 TWh; ST_GAS +0.03 / +0.13 /
+0.07; CT_PEAKER +0.02 / +0.04 / +0.06 for A1→A0):

| gate | bar | fires ⇒ |
|---|---|---|
| **G-CAISO180** (the protective band) | a repair restores **more CC_REGULAR than the entire regeneration removed**: ΔCC_REGULAR > **+0.11 / +0.44 / +0.67 TWh** (2023/24/25) | **FAIL the arm** — it has over-corrected past the whole leg it claims to repair |
| **G-C1** | C1 free-class fuelmix must stay **PASS** on every free class, all three years | **FAIL the arm** |
| **G-DEPTH** | repaired depth must **not fall below the superseded PRE envelope** (38.03 / 38.80 / 49.99 M MW-h) | **FAIL** — a "repair" that undoes more than the regeneration added is a revert in disguise (rules 1 / 14) |
| **G-DOF** | ledger stays **11 / 8**; **zero** new fitted scalars | **FAIL** |
| **G-CONTRACT** | the repaired envelope must itself clear **B-1** (a repair that still violates the detector's own contract is not a repair) | **FAIL** |
| **G-LOYO** | any mechanism-change-driven verdict flip is scored **leave-one-year-out within 2023–2025** before any promotion (rule 22) | required |

**No existing adjudication is repealed unless/until a replacement arm passes its own gates**
(the memo's closing rule, adopted verbatim).

### 6a. CONTROL — MANDATORY IF ANY ARM SOLVES

caiso-180 measured same-head drift at **exactly $0.000**, all three years. A fresh control
must therefore reproduce the keeper **to the cent** — **if it does not, THAT is the finding**
and it is reported at full magnitude as its own result.

- Reproduction is by **`--replay-bundle results/calibration/caiso175_tac_intake`** — the
  documented recipe contract, **never a remembered CLI string**.
- `scenario_config` verified **fail-closed** with the caiso-180 L1/L2/L3 split: **L1** exact
  on the keeper's own key set; **L2** arm-to-arm over the full union; **L3** additive drift
  gated on *code-default* **and** *non-CAISO scope*.
- **REUSE `scripts/probes/_caiso180_arm_identity.py`** — not re-invented.
- **Its §3a leg-2 ordering gate is WITHDRAWN AS MALFORMED** (window count is not envelope
  depth; falsified by caiso-180's own measurement) and is **NOT reinstated**. The pairwise
  **distinctness** check plus the **sha ladder** remain the load-bearing proofs.
- The envelope is a single mutable file: its sha256 is captured **immediately before and
  after** each arm's solve, must equal each other and that arm's intended state, and the file
  is restored to `c4ded33d…f93ff5e` at session end.

---

## 7. VERDICT BRANCHES — fixed before any metric is read

- **BRANCH I — CLEAN.** Neither B-1 nor B-2 fires. The envelope is **DEPTH-CORRECT**:
  **READING (i)** is adopted. The regeneration did not over-derate; the +1.1 / +1.6 pp it
  surfaced is a **pre-existing over-pricing defect the phantom windows were masking**.
  **Register nothing, spend no LP** (charter, explicit), and hand off to the offer-curve
  re-identification with this result as its basis (§9).
- **BRANCH II — REPAIR INDICATED.** B-1 and/or B-2 fires. **READING (ii)** is adopted to the
  extent measured. The repair is built as a rule-23 derive-grain change under §6's gates, an
  arm is solved with the §6a control, and **every arm that solves is registered** (rule 15)
  with its own `legitimacy_diagnostics.json` so **C8 stays SCORED**.
- **BRANCH III — AMBIGUOUS.** B-1/B-2 land near their bars, or the edge/interior split cannot
  be resolved. **Only here is ROUTE 2 reached** — the committed CNOG comparator (§2b),
  adjudicated against the charter §9 definitional seam first (§4d). If nothing usable
  survives that adjudication, **say so plainly and file it** — **no proxy comparator is
  substituted** (the caiso-123 failure mode, forbidden here).
- **BRANCH IV — THE INSTRUMENT FAILS.** If the join cannot be made faithfully (unresolvable
  unit ids, a clock that cannot be reconciled), the session reports a **measurement failure**
  and spends nothing, rather than reporting a number it cannot stand behind.

Branches are not mutually exclusive where they overlap in scope; any co-firing is reported
alongside.

---

## 8. IF THE DEFECT IS H-EDGE — the shape of the repair, named not built

Recorded so the repair cannot be improvised after the numbers land. If B-3 returns
EDGE-dominated, the admissible repair is to **stop losing the detector's own hour resolution
in the CSV round-trip** — carry the window's start/end **hour** through the schema and the
loader instead of re-expanding day-granular dates. Properties that make it admissible:
**zero DOF**, no new parameter, no threshold re-valued, and it is a strict **grain** change of
the ercot-174 BE-1/BE-2/BE-3 class (the deriver's frozen identification constants imported
verbatim, never re-valued — rule 23). Whether it is built **this** session depends on §7; if
built, it takes §6's gates in full, and a byte-equivalence proof that detection itself is
**unchanged**.

---

## 9. SEQUENCING — memo §5, AND IT BINDS THIS SESSION

Memo option **C** is *"re-charter the layer's CONSTRUCTION first, THEN address what sits on
top"*, chosen because A (keep a knowingly-wrong mechanism) and B (fix composition first) were
both dead ends. The CAISO ordering that follows:

> **CONSTRUCTION QUESTION FIRST; OFFER-CURVE RE-DERIVATION LAST.**

**No offer-curve re-tune is opened this session**, even though rule 23's re-derive trigger is
technically satisfied by the 2026-07-24 data change. Retuning offers to absorb +1.1 / +1.6 pp
**before the envelope's depth is adjudicated** would **bury a possible data error inside a
fitted curve** — exactly what rule 14 forbids.

**If Route 1 returns CLEAN (branch I), the offer-curve re-identification becomes the NEXT
session's chartered lever**, on the rule-23 source-data-changed basis, cited to the
2026-07-24 data change.

---

## 10. DO-NOT-REDO carried into this session (rule 28 `[R-MECH-MATRIX]`, duty a)

Not re-opened, not re-tested, not re-derived here:

- **`battery_dispatch_adder` — a PERMANENT DECLARED-RESIDUAL DOF.** All three exits closed
  (caiso-176 confidential-by-tariff; caiso-178 spent; caiso-179 spent and **REFUTED** at
  $28–35/MWh). **Not re-derived** from NREL ATB, NREL cost benchmarks, PNNL-33283 or LFP
  warranties.
- Routing the LP through `_degradation_cost_per_mwh` — closed.
- The **AS-power-reservation family** (caiso-74 / 127 / 129) — closed.
- An **N–S topology lever** (caiso-164 §0/§6) — **FORBIDDEN**.
- `caiso_ps_charge_shape_anchor` — stays **`G`** (input walled).
- **`unit_outage_short_windows` / `unit_partial_outage_windows`** — caiso-180 confirmed
  caiso-136's `I` on a stronger basis (coal-only detectors; CAMPD's CAISO population has
  **zero** coal; Argus Cogen 50 MW = 0.16 % of fleet is not a CAMPD reporter). **Not
  re-tested.**

## 11. KNOWN-OPEN, carried forward unchanged

1. **The N–S congestion majority** — model 5.2 / 2.4 / 2.9 % of the measured NP15–ZP26 basis;
   lever **FORBIDDEN**.
2. **C3a's first named contributor is the WALLED hourly PS water state**
   (`FINDING-caiso140` §B) — owner-level data, not a session lever.
3. **`unit_outage_maxgen_events` is a CAISO DATA GAP** (no registry exists; only MISO's lane
   built one) — a data-intake charter; reported, not armed.
4. The DOF ledger's `battery_dispatch_adder` `root_cause` still needs re-wording to
   *permanent declared residual* by a **keeper-lane** session. Not this one.
5. `curate_dam_public_bids.py` cannot process a full CAISO year (~14.3 GB vs ~15 GB RAM,
   caiso-178). Unfixed; needs a data-contract session. **Nothing here depends on it.**

## 12. Deliverables

`PRECHECK-caiso181-envelope-depth-2026-08-07.md` (this file, pushed and blob-verified first) ·
`FINDING-caiso181-envelope-depth-2026-08-07.md` ·
`scripts/probes/_caiso181_cems_confrontation.py` ·
`results/calibration/_caiso181_cems_confrontation.json` ·
CAISO matrix cell + §5.2 header stamped in **this** session (rule 28 duty b) ·
`docs/calibration-log/caiso.md` entry ·
plus — **only if branch II fires** — registered bundle(s) with `legitimacy_diagnostics.json`
each (rule 15), and the rule-23 repair with its own precommit.
