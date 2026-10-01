# FINDING — caiso-187: the WEFOR-vs-overlay charter's premise is **INVERTED BY MEASUREMENT**. There is no CC forced-outage double count to relieve, because the statistical term (3.5 %) is dwarfed by the overlay, which removes **24–35 % of CAISO's combined-cycle capacity-hours against a ~10 % published planned-plus-forced expectation — and is GROWING 45 % in two years.** **BRANCH C fires: no LP, escalate to the owner.**

**Outcome: the chartered instrument cannot deliver what it was authorised to deliver, and
what the measurement found instead is a much larger, differently-located object.** The
pre-registered Branch C — "`X_c ≥ W_c` … a finding about the **overlay**, not a licence to
zero the statistical term. **Report and escalate**" — fires on the two material classes
without ambiguity.

Keeper **UNCHANGED** at `2026-08-09-caiso-184-c1-lpbasis`. DOF ledger **11 / 8**, untouched.
**Zero LP spent. Nothing registered. C3a never read.** No data byte written, no derive
re-run, `THERMAL_AVAILABILITY` not re-derived. Both holdout markers untouched (owner acts).

**Pre-registration:** `PRECHECK-caiso187-wefor-overlay-2026-08-09.md`, commit `f7ea03e`,
**committed before the identification script was written and before any value existed**.
*(Transport caveat, declared: the repository's git remote was unreachable throughout this
session — `push` and `ls-remote` both failing with alternating HTTP 408/500 — so `f7ea03e`
is verified by the local commit chain rather than by a remote round trip. The ordering
guarantee that matters is the parent chain, which is immutable; publication is pending a
retry loop. **No LP was run, so the G-FROZEN precondition on solving was never reached.**)*

Instrument: `scripts/probes/_caiso187_residual_identification.py`.
Record: `_caiso187_residual_identification.json`.

---

## 1. P0-1 — DO-NOT-REDO, discharged

Discharged in PRECHECK §0. Not caiso-186 (`cc_winter_capability_basis` **not armed**), not
`unit_outage_short_windows` / `unit_partial_outage_windows` (caiso-136/180 — coal-only
detector, **0 rows** in the committed CAISO short extract, **not armed and not re-run on
gas**), not caiso-184/183/181 (the extract is **read only**), not any struck lever. No prior
CAISO adjudication of `wefor_residual` exists; ERCOT's 0.02 and PJM's 0.015 are **neither
adopted nor used as evidence** (rule 25 `[R-ISO-SCOPE]`).

---

## 2. WHAT THE CHARTER EXPECTED, AND WHAT THE FROZEN FORMULA RETURNED

PRECHECK §2 fixed the identification **before the value existed**:

```
residual_c = max(0, W_c − X_c)
```

with `W_c` the model's own **unfitted** `THERMAL_AVAILABILITY` rate (multiplier held at 1.0,
not re-derived) and `X_c` the CAMPD overlay's **measured** removal taken through the shipped
`outages.unit_outage_derate_factors` — the overlay the LP actually applies.

Pooled 2023–2025, through the shipped loader:

| class | fleet MW | `W_c` (published) | **`X_c` (overlay, measured)** | `X_c / W_c` | `residual_c` |
|---|---:|---:|---:|---:|---:|
| **CC_REGULAR** | 15 284.8 | 0.050 | **0.2655** | **5.3×** | **0** |
| **CC_CHP** | 1 689.3 | 0.040 | **0.2145** | **5.4×** | **0** |
| ST_GAS | 2 858.8 | 0.210 | **0.0000** | — | 0.210 |

**The expected double count is not there.** For the two material classes the *overlay alone*
already removes five times the published statistical forced-outage rate, so
`max(0, W − X) = 0`: there is nothing for `wefor_residual` to give back beyond the 3.5 pp the
statistical term itself contributes. The instrument the owner authorised is, on this
evidence, **immaterial for CC** — and **inadmissible for ST_GAS**, which has *zero* overlay
coverage and therefore, by the pre-registered G-NODOUBLE, gets **no relief at all**.

---

## 3. WHAT THE MEASUREMENT FOUND INSTEAD — and it is much larger

### 3a. The overlay removes 24–35 % of CC capacity-hours, against ~10 % published

Per year, and **independently cross-checked** by direct integration over the committed
extract (`Σ overlap_hours × unit_capacity_mw ÷ plant_capacity × 8760`), which is not the
loader's code path:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| CC_REGULAR, shipped loader | 0.2157 | 0.2621 | **0.3186** |
| CC_REGULAR, direct count | 0.2421 | 0.2914 | **0.3479** |
| CC_CHP, shipped loader | 0.1634 | 0.2079 | **0.2722** |
| CC_CHP, direct count | 0.2741 | 0.3425 | **0.4177** |

*(The two differ only in the denominator — the loader divides by the full class capacity
including plants with no outage at all; the direct count divides by the capacity of plants
that have at least one. Both are reported; neither is chosen.)*

**The comparison that matters is against planned + forced, not forced alone.** The keeper runs
`coal_drop_pof=True`, so for these classes the statistical **planned**-outage factor is
dropped precisely because the overlay is meant to carry planned outages too. The published
expectation is therefore `POF 0.05 + WEFOR 0.05 ≈ 0.10` for CC_REGULAR. Measured removal is
**2.4× to 3.5× that**, and rising.

### 3b. The growth is the load-bearing signal

`0.216 → 0.262 → 0.319` for CC_REGULAR (loader basis) — **+48 % in two years**, across a
15.3 GW fleet of 28 plants. **Mechanical failure rates do not rise by half in two years on a
fleet this size. Economic displacement does**, and CAISO's combined cycles are precisely the
mid-merit fleet being displaced by solar and storage over exactly this window.

The detector defines an outage as a sustained span of CF < 5 % lasting ≥ 5 days, kept if it
passes a revealed-availability filter or is a full stop (CF < 2 %) for ≥ 5 days. **That test
identifies *downtime*; it does not identify *mechanical unavailability*.** A combined cycle
that is uneconomic for a fortnight in the spring solar surplus produces a span
indistinguishable, on CF alone, from one that is broken.

**caiso-181 does not settle this, and is not contradicted by it.** That session confronted
the outage envelope against CEMS over 599,736 hours and found **zero interior
contradictions** — i.e. in the hours the model asserts a unit is out, CEMS confirms it
produced nothing. That is a statement about **whether the units were down**, and it stands
in full. It is **not** a statement about **why**, and the mechanical-vs-economic question is
exactly the one it did not ask.

### 3c. Seasonality is consistent with EITHER reading — reported, not used

CC_REGULAR outage MW-hours by month (2024, thousands): Jan 1.7, Feb 2.4, **Mar 5.2, Apr 5.6,
May 6.2**, Jun 3.2, **Jul 0.3, Aug 0.8**, Sep 1.8, Oct 1.6, Nov 2.9, Dec 3.3.

That is the classic spring/fall planned-maintenance shape with a summer-peak collapse — **and
it is also exactly the CAISO solar-surplus shape.** In this ISO the two hypotheses predict
the same seasonality, so **this evidence discriminates nothing** and is reported here only so
it is not later mistaken for support of either side.

### 3d. A second, separable observation: ST_GAS

CAISO's **2 858.8 MW** of ST_GAS has **zero** CAMPD overlay coverage in all three years
(0 of 3 plants), yet carries a statistical WEFOR of `0.21 × 0.7 = 0.147`. The `0.21` base is,
by the mechanism matrix's own note, **"fitted to ERCOT's once-through 1950s-60s steamers and
more than 2× every other thermal class"**, and the field built for exactly that problem,
`gas_st_wefor_base_override`, is armed at MISO (0.10) and **`None` at CAISO**. That is an
ERCOT-fitted parameter governing 2.9 GW of a different ISO's fleet. **Recorded as an
observation only** — arming the override would be a separate charter, and adopting MISO's
0.10 would be a rule-25 parameter transfer, which this session does not make.

---

## 4. A DEFECT IN THIS SESSION'S OWN PRE-REGISTRATION, declared

PRECHECK §2 aggregates the per-class residuals into **one capacity-weighted scalar** (the
field is a single `float`), which on this data gives **0.0303** over
`{CC_REGULAR, CC_CHP, ST_GAS}`. But PRECHECK §4's **G-NODOUBLE** and **G-SCOPE** state that a
class with `X_c = 0` **gets no relief**. Applying 0.0303 to ST_GAS would cut its removal from
0.147 to 0.0303 — **a 12 pp capability release to the one class with zero measured overlay
coverage**, which is a direct G-NODOUBLE violation.

**The aggregation rule and the protective gate are mutually inconsistent on this data, and
that is my error, not a discovery.** The fail-closed reading is that the **protective gate
wins** — which would exclude ST_GAS and leave `wefor_residual = 0.0` scoped to
`{CC_REGULAR, CC_CHP}`. **I have deliberately not applied that resolution**, because
BRANCH C is the governing branch and its instruction is to escalate, not to repair a
pre-registration mid-session and proceed. The resolution is put to the owner in §6 instead.

---

## 5. WHY NO LP WAS SPENT

PRECHECK §7 BRANCH C, fixed in advance: *"`X_c ≥ W_c` … **No LP without escalation.** That
would mean the overlay is removing more than the statistical model says exists, which is a
finding about the **overlay**, not a licence to zero the statistical term. Report and
escalate."* It fires on both material classes. Solving here would have priced a
configuration whose own identification says it is immaterial, and would have spent hours to
learn nothing the identification did not already state.

**The direction discipline held, and it mattered here more than anywhere in this lane.**
PRECHECK §5 pre-declared that this lever's expected sign **lowers price**, flattering a
residual already +10.5 % / +13.1 % **over**. Everything in §3 points the same flattering way:
if a meaningful share of that 24–35 % is economic rather than mechanical, correcting it adds
capability and cuts price. **The growth in §3b even tracks the C3a residual's own growth
(+3.7 → +10.5 → +13.1 %).** That co-movement is **suggestive and is NOT evidence** — two
series rising together over three points is not an identification, and quoting it as one
would be precisely the motivated reasoning this pre-registration exists to block. It is
recorded so a later session does not rediscover it and mistake it for proof.

---

## 6. THE OWNER QUESTION — three concrete options, in order of what the evidence supports

1. **AUTHORISE THE OVERLAY MECHANICAL-vs-ECONOMIC IDENTIFICATION (recommended).** The
   detector classifies *downtime*; the model treats it as *unavailability*. Separating the
   two is the object §3 uncovered, it is **not data-blocked** (CAMPD, EIA-930 net load and
   the delivered-fuel merit-order panel are all already on disk, and `outage_detect.py`
   already ships `filter_merit_order_layup` and `build_merit_order_panel` — machinery built
   for exactly this question), and it is where the `wefor_multiplier = 0.7` residual DOF and
   caiso-186's headroom question both actually live. **It must be chartered with the
   direction hazard stated as this session's was**, because its expected sign flatters C3a.
2. **RESOLVE THIS SESSION'S PRE-REGISTRATION DEFECT (§4) AND AUTHORISE THE NARROW ARM.**
   `wefor_residual = 0.0` scoped to `{CC_REGULAR, CC_CHP}`, with `wefor_multiplier` returned
   to 1.0 — the gate-consistent reading of the frozen formula. It retires a residual-fitted
   DOF (**ledger 11 / 8 → 11 / 7**), which is a real governance gain, but it is worth only
   **~3.5 pp of CC availability** and does nothing about §3. Small, clean, and honest.
3. **DECLINE BOTH.** The CAISO in-model queue returns to empty, and the standing routes are
   unchanged: fund the walled hourly PS water-state intake, or rule on a C3a
   `CALIBRATED-WITH-CAVEATS` ledger entry, **which rubric v3.1 still forbids** (C3c is the
   only ledgerable criterion; C3a is load-bearing).

**Option 1 and option 2 are independent and can both be granted**; 2 does not depend on 1,
and 1 supersedes 2 in importance.

---

## 7. GATE TALLY

| gate | verdict |
|---|---|
| **G-NOFIT** | **PASS** — every term published-in-model or counted from a committed artifact; no sweep, no post-hoc adjustment |
| **G-FROZEN** | **PASS (vacuously)** — the value was computed once and written; no solve was reached, so no price could have influenced it |
| **G-NODOUBLE** | **FAIL on ST_GAS** (`X_c = 0` ⇒ no relief), **and the CC classes return `residual = 0`** — the premise is refuted, not the gate merely tripped |
| **G-SCOPE** | **PASS** — CT classes never relieved; `CT_CHP`/`CT_PEAKER`/`COAL` present in the fleet are excluded, and the 527 `CT_CHP` outage rows in the extract are reported as an open observation, not acted on |
| **G-DOF** | **NOT REACHED** — no arm solved, ledger untouched at 11 / 8; the targeted 11 / 7 decrease was not attempted |
| **G-SIXISO** | **PASS** — no other ISO's config, keeper, extract or cell written; ERCOT's 0.02 and PJM's 0.015 neither adopted nor used as evidence |
| **G-C1 / G-PROT / G-LOYO / CONTROL** | **NOT REACHED** — no arm solved; nothing registered, so nothing is unscored on the dashboard |

---

## 8. Known-open, carried forward

1. **The overlay's mechanical-vs-economic identification** (§3) — the object this session
   uncovered; owner option 1.
2. **`wefor_multiplier = 0.7` remains a residual-identified DOF** with its root cause still
   open, and now with a *different* explanation owed than the charter assumed.
3. **ST_GAS carries an ERCOT-fitted 0.21 WEFOR base over 2.9 GW with zero overlay coverage**
   (§3d); `gas_st_wefor_base_override` unarmed at CAISO.
4. **This session's pre-registration defect** (§4) — aggregation vs G-NODOUBLE.
5. **C3a's residual: 2024 +10.5 %, 2025 +13.1 %** — unchanged, never read.
6. **The git remote was unreachable for the whole session** — commits `e1b661d`, `f7ea03e`
   and this one are local-verified with a retry loop armed; **the substantive caiso-186
   commits `7fb3bee1` and `9ee2bd8` are on the remote and API-confirmed.**

---

## 9. Governance

Rule 1 `[R-STRUCT]` — C3a never read; the flattering direction pre-declared as a hazard and
the flattering co-movement in §5 explicitly refused as evidence. Rule 11 — the fitted
`wefor_multiplier` is left as the open root cause it is, with a corrected diagnosis rather
than a buried one. Rule 13 `[R-MEASURED]` — every figure counted from a committed measured
artifact; no measured outcome, price residual or benchmark entered any input or any bar.
Rule 14 `[R-ACCURATE]` — the measured input was preferred and it **refuted the charter**; the
root cause is opened (§6) rather than the estimate re-blessed. Rule 15 / 16 — no run
completed, so none registered. Rule 19 `[R-ONE-MECH]` — the object; the finding is that the
two mechanisms are **not** the two the charter named. Rule 21 `[R-DOF]` — ledger 11 / 8
untouched; the targeted decrease is deferred to the owner. Rule 22 `[R-HOLDOUT]` — no year
solved; freeze respected; both markers untouched. Rule 23 `[R-FROZEN-DERIVE]` —
`THERMAL_AVAILABILITY` **not** re-derived, extract **read only**, no data byte written.
Rule 24 `[R-REGISTRY]` — no new field; no env knob; no hand-edited table. Rule 25
`[R-ISO-SCOPE]` — CAISO only; ERCOT's and PJM's values neither adopted nor used as a check.
Rule 27 `[R-PUSH]` — pre-registration committed before the identification script existed;
remote unreachable, declared in the header rather than glossed. Rule 28 `[R-MECH-MATRIX]` —
duty (a) in §1, duty (b) and the new verdict-bearing `wefor_residual` row in this PR
(duty c), every other ISO carrying no transferred verdict.
