# STANDING DATA ASK (opened 2026-07-26, miso-90) — MISO generation-outage data at UNIT or FUEL grain

**Status:** OPEN. Blocking. No session may treat this as closed until a source
clears §4.

**Authority:** Owner decision 2026-07-26 (option 2 of the miso-89 three-way
determination), opened alongside the C3b-2025 ledger entry (option 1). This
charter is cited by that entry
(`results/calibration/miso88_egrid_hr/calibration_attestation.json`,
`price_shape`/2025) as the one thing that would reopen the lane honestly.

**This is a DATA ask, not a build charter.** It specifies what would have to
exist before any mechanism could be built. Until a source clears §4, the correct
behaviour is rule 24: report and stop.

---

## 1. What is blocked, and by exactly what

Two independent MISO defects are blocked on the same missing datum.

**(a) C3b-2025 — a ~10 GW summer-peak fossil under-derate.** Model fossil derate
at Jun/Jul HE16–18 is flat across years (20.07 / 19.07 / 20.83 GW, +1.76 GW into
2025) while MISO's own published offline record jumps 35.10 / 33.27 / 45.59 GW
(+12.32). The offset is stable at ~14.6 GW in 2023/2024 and breaks to 24.76 GW in
2025. Established by difference-in-differences, so it needs no cross-fuel
attribution (miso-87 respected). 2025 was not hot (zone-mean summer-peak TMAX
29.6 / 29.2 / 29.8 °C) and gas was cheap — it was a supply-side event.
Evidence: `results/calibration/FINDING-miso89-diurnal-spread-compression-2026-07.md` §7.

**(b) CT measured-availability — 22.39 GW carrying no measured derate at all.**
Not a fetch gap: an *identification* exclusion. A CT down-window cannot be
certified a forced outage versus out-of-merit-at-peak, so every **output-derived**
source is structurally incapable of measuring it.
Evidence: `results/calibration/FINDING-miso90-ct-availability-identification-2026-07.md`.

**The single blocking fact for both:** the only MISO-public outage record is
aggregate. MISO's daily Multiday Operating Margin Forecast Report
(`docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx`, `OUTAGE` sheet) tabulates
offline MW by operating **region** (North / Central / South / system) × **cause
type** (Derated / Forced / Planned / Unplanned) — **with no unit or fuel
identity**, and no coverage before 2023-01-01. Already intaken
(`data/raw/miso-generation-outages/`, `src/market_sim/data/miso_outages.py`);
its grain is the constraint, not its availability.

Two charters have already proved that this aggregate cannot be pushed down onto
units without inventing the attribution — miso-85 (uniform attribution: REJECTED,
over-derates CTs into a manufactured 138 h >$200 tail and under-derates coal by
+28.3 TWh COAL_PRB) and miso-87 (cross-fuel attribution: REFUTED at charter on
two independent grounds). **Neither is to be reopened by this ask.**

## 2. The required datum — specification

A source clears this ask only if it delivers **all** of A–D.

| | requirement | why |
|---|---|---|
| **A** | **Capability, not output.** The record must state *available* or *offered* MW (or an outage keyed to a unit), never be inferred from observed generation. | §1(b): output-derived detection is degenerate for run-when-called units. This one criterion rejects CAMPD, EIA-923 and every derivative of either. |
| **B** | **Unit or fuel-class grain.** Per-unit, or per (fuel class × region). Region × cause is what we already have and is insufficient. | Defeats the miso-85/87 attribution trap: with fuel grain the model never has to guess a split. |
| **C** | **Year-specific and season-resolved.** Must distinguish 2025 from 2023/2024 and must resolve the summer peak. A multi-year rolling class average cannot see §1(a), which is entirely a *change* between years. | The defect is a difference-in-differences; a static rate is blind to it by construction. |
| **D** | **MISO footprint, 2023–2025 minimum.** Ideally 2018–2026 to serve the holdout ladder. | Rule 16: keepers score all three training years in one bundle. |

**Note on (C) vs what the model already uses.** The statistical fallback already
consumes NERC-GADS class averages (`constants.py:986-994`: gas_cc 0.05, gas_ct
0.06, gas_st 0.07, coal 0.08 …). Those are **static annual EFORs**. Re-importing
another static class average would satisfy B and D but **fail C** and would move
nothing. The ask is specifically for a *time-varying, year-specific* series.

### 2a. The named parameter this ask must replace (added by miso-91)

The concrete deliverable a clearing source buys is a **measured seasonal
forced-outage shape** to replace `SUMMER_WEFOR_SHARE = 0.30`
(`config/fuel_trajectories.py`; re-homed there by miso-91 from
`data/fleet/arrays.py::_SUMMER_WEFOR_SHARE`, now declared in the MISO keeper's
DOF ledger with an open root cause). It sets the fraction of a unit's WEFOR
applied in the summer peak, redistributing the rest into the shoulder months.

**Why it is the right target.** It is the single largest undeclared free
parameter on the availability path, and it is material at the scale of the defect
this ask exists to close. Measured by miso-91 (no LP), under the keeper's flags it
governs **all six non-coal thermal classes** — COAL is exempt, since
`coal_drop_pof=True` drops summer WEFOR outright — adding, versus a
no-reallocation baseline: ST_GAS +14.70 pp, ST_CHP +5.60, CT_PEAKER +4.29,
CC_REGULAR +3.15, CT_CHP +3.06, CC_CHP +2.52 of summer availability. Against the
committed per-class nameplates that is **≈3.9 GW of MISO summer-peak capability
at a uniform fleet age of 18 y, ≈4.6 GW at 28 y, ≈5.8 GW at 38 y** — the same
order as the ~10 GW under-derate ledgered as C3b. (This corrects the miso-90
finding, which scoped the parameter to CT_PEAKER alone.)

**What a clearing source must additionally deliver to retire it.** On top of A–D:

| | requirement | why |
|---|---|---|
| **E** | **Seasonal split of FORCED outages specifically** — planned and forced separated, not a combined unavailability rate. | The parameter reallocates WEFOR only; POF is separately grounded by the measured `MAINTENANCE_MONTHLY_SHAPE`. A combined rate cannot identify it. |
| **F** | **Enough class coverage to span the six governed groups**, or an explicit statement of which it covers. Partial coverage is usable — it narrows the DOF — but must not be silently generalised to the uncovered classes. | Per-class deltas differ by ~6× (ST_GAS vs CC_CHP); one class's shape is not the fleet's. |

**And the sign is the live question, not a formality.** For *planned* outages,
shifting maintenance away from the peak is well-founded. For *forced* outages the
reallocation runs **opposite** to the physics — forced outages correlate
*positively* with heat and high load, so a share below 1.0 encodes the reverse of
the expected physical sign. A clearing source should therefore be read as
**testing whether the mechanism has the right sign at all**, not merely as
recalibrating its magnitude. A source showing summer forced-outage rates at or
above the annual mean would mean the current treatment is directionally wrong for
the forced component — a structural finding, and per rule 1 `[R-STRUCT]` one that
stands whatever it does to the fit.

**Reminder on acceptance-test part 4.** As with the rest of this ask, a source
that clears the grain but shows **no** 2025 summer step has *refuted* the miso-89
finding rather than enabled it. Report that outcome; do not discard the source.

## 3. Candidate sources — to be assessed, none yet cleared

Ranked by prior plausibility. **Every entry is a hypothesis for an intake
session to verify against §2 — none has been confirmed to exist in the required
form, and this charter does not assert that any of them does.**

1. **NERC GADS-derived class series.** GADS reporting is mandatory for
   conventional units above the size threshold and is unit-resolved at source,
   but unit-level data is confidential; NERC publishes aggregates. **To verify:**
   whether any public GADS product is resolved to *year × season × unit type* for
   a MISO-overlapping region, rather than the multi-year rolling class averages
   the model already uses. Clears A and B by construction; **C is the open
   question and the likely failure point.**
2. **Potomac Economics MISO State of the Market (annual, public).** MISO's IMM
   has unit-level data and publishes outage analysis. **To verify:** whether any
   published figure or appendix resolves outages by *fuel class* (not merely by
   outage type) at monthly-or-finer resolution, and whether the underlying series
   is obtainable rather than only rendered in a chart. If a fuel × month series
   exists it clears A–D directly and is the single best candidate.
3. **MISO resource-adequacy / accreditation postings.** Module E / PRA
   accreditation uses unit forced-outage statistics (XEFORd-family). **To
   verify:** whether any per-unit or per-class outage-rate input is published
   with the auction results, and at what vintage. Likely annual — a **C** risk.
4. **A MISO data request.** MISO's stakeholder process can be asked directly for
   a fuel-class × month offline series derived from the same record behind the
   MOM report. Slow, but it is the one path that can be specified to meet §2
   exactly rather than hoping an existing product happens to.

**Explicitly ruled OUT, do not re-attempt:** the MOM aggregate with any
attribution rule (miso-85/87); CAMPD CEMS at CT grain (fails A);
the EIA-923 monthly fallback (fails A, and excludes peakers by its own
construction); `gt_ambient_derate` (measured provably inert for MISO — 0 h above
its 35 °C reference at summer peak in any year); `temp_dependent_derate`
(refuted for the ERCOT gas fleet 2026-07-09); `unit_partial_outage_windows`
(premise fails — MISO already carries 95.4 % coal / 90.1 % CC unit-level
coverage).

## 4. Acceptance test

A candidate is accepted only on a written finding that answers all of:

1. **§2 A–D**, each with the actual field names, grain and year span — not a
   description of the publication.
2. **Rule 13 admissibility:** could this same quantity be produced for a
   *forward* year from forward drivers, and would it respond to changed
   conditions? If it is measured-only with no forward analogue it is a
   **backcast/calibration overlay only** and must be gated as such (the existing
   `miso_native_outage_source` pattern), never presented as forecast methodology.
3. **It is an INPUT, not an OUTCOME** (rule 13's forbidden half): it must not be
   the price/volume residual, nor anything rescaled so the model's *output* lands
   on actuals.
4. **Does it reproduce the §1(a) difference-in-differences independently?** A
   source that clears A–D but shows *no* 2025 summer step has **refuted** the
   finding rather than enabled it — that outcome is to be reported as such, not
   discarded.

## 5. Rule-22 intake protocol

* Training years **2023–2025** are unrestricted.
* Any **out-of-training** year (2018–2022, 2019 and H1-2026 locked) requires its
  own **explicit, session-logged owner authorization**, appended verbatim to
  `intake_log` in `frontend/data/backcast/calibration-complete.json`, and is
  validated **no-LP only** (byte-identity / loader-resolvability / row counts).
* **MISO carries NO calibration-complete marker.** Solve, score and dashboard
  registration of any out-of-training year stay fully quarantined regardless of
  intake; CI (`quarantine-gates`) enforces this independently.

## 6. What this ask must not become

* **Not** a licence to reopen miso-85 or miso-87. Those are refuted on their own
  terms; a new *source* is required, not a new *attribution rule* over the old one.
* **Not** a licence for an offer adder, a summer multiplier, or a residual-tuned
  band (rules 1/10) — no matter what the incoming data shows.
* **Not** a reason to re-tune `_SUMMER_WEFOR_SHARE = 0.30` by hand. That
  parameter is uncited and undeclared (see the miso-90 CT finding §4) and should
  be **declared in the DOF ledger** now; it may only be *re-derived* from a
  source that clears §4, and per rule 23 `[R-FROZEN-DERIVE]` the commit must cite
  the data change, never a residual.
* **Not** a blocker on unrelated MISO work. C3b-2025 is ledgered; the keeper
  stands at CALIBRATED-WITH-CAVEATS. This ask governs whether that ledger entry
  can ever be *retired*, not whether MISO can proceed.

## 7. Governance note — the budget is now saturated

Ledgering C3b took MISO's non-protective ledgered-caveat budget to **3/3** (C3a
mean LMP, C3b price shape, C3c price tail; `MAX_LEDGERED_CAVEATS = 3`). **No
further load-bearing MISO criterion can be ledgered without exceeding budget and
forcing the determination back to NOT-YET.** The next load-bearing miss must be
*built*, not documented — which is what makes this ask load-bearing rather than
housekeeping.

## 8. Candidate assessment, xiso-4 (2026-08-04) — candidate 2 CLOSED

**No LP, no solve, no intake.** Every document below was read in a scratch
directory for assessment only; nothing was written under `data/raw/`, so no
rule-22 intake authorization was required or claimed.

**Framing correction, stated up front: this ask is DEFECT-motivated, not
GATE-motivated.** C3b (`price_shape`) **PASSES** on the current MISO keeper
`2026-08-04-miso-124-dualfuel-rearm` — re-derived at xiso-4 with
`scripts/calibration_verdict.py --run-id` on committed artifacts, not asserted.
MISO's sole FAIL is C7 (`shape`); `price_mean` and `price_tail` are CAVEATs.
§1(a) and §7 above were written when C3b was ledgered as a live miss, and that
framing no longer holds. The ~10 GW summer-peak derate defect and the undeclared
`SUMMER_WEFOR_SHARE = 0.30` DOF are both still real — this ask stands on those,
not on a failing gate. Do not cite it as gate work.

### Candidate 2 — Potomac Economics MISO SOM: **CLOSED, fails §2B**

Assessed against the **2025 MISO State of the Market Report** (body, 152 pp.,
published 2026-07) and its **Analytic Appendix** (157 pp.):

| figure | content | grain |
|---|---|---|
| Figure 25 (body) | Generation Outages, 2023–2025 | **subregion** × outage type |
| Figure A71 (appendix) | monthly avg planned + unplanned outage rates, 2024–2025 + 3-yr annual averages; splits normal-planned / short-notice-planned / short-term-unplanned / long-term-unplanned. **Full outages only — explicitly excludes partial outages and deratings.** | MISO-wide, **month** × outage type |
| Figures A154–A156 | Real-Time Deratings and Forced Outages, 2025 | **region** (Central / South / North) |

Scored against §2: clears **A** (ticket-based, not output-derived), **C**
(monthly, year-specific, 2023–2025) and **E** (planned vs forced separated).
**FAILS B** — there is **no fuel-class resolution of outages anywhere** in
either document. The grain delivered is region × cause × month, which is
*exactly what the model already holds* from the MOM report (§1) and exactly the
grain miso-85 and miso-87 proved cannot be pushed onto units.

§3 ranked this "the single best candidate… if a fuel × month series exists it
clears A–D directly." **It does not exist.** Candidate 2 is closed, on the one
criterion this ask exists for. Do not re-open it, and do not re-attempt an
attribution rule over it (miso-85/87 remain closed).

### Candidate 3 — RA / accreditation: partially visible, does **not** clear

SOM **Figure 34 / A119** publishes **UCAP by fuel type × Local Resource Zone**,
from the 2025–26 PRA summer and winter seasons; UCAP "account[s] for forced
outages and intermittency." Clears **A, B, D**. **Fails C and E:**

* it is a **two-season planning accreditation over a historical lookback** — a
  rolling class average, which §2C's own note says "would satisfy B and D but
  fail C and would move nothing";
* it **combines forced outage with intermittency** rather than isolating the
  forced component (fails E, which the `SUMMER_WEFOR_SHARE` replacement needs);
* the SOM renders only UCAP/ICAP **shares** in an inset table, not the
  underlying MW series.

Direct MISO PRA postings could not be checked: `misoenergy.org` and
`cdn.misoenergy.org` both return **403** from the session environment
(`docs.misoenergy.org` works, which is why the already-intaken MOM reports are
reachable and the PRA results are not). Candidate 3 stays **open but
downgraded** — as published it fails C and E.

### Candidate 1 — NERC GADS: **UNRESOLVED, explicitly not refuted**

`nerc.com` serves the GADS Reports page; the public product family is
*Generating Unit Statistical Brochures*. The brochure links are JS-rendered and
did not resolve from this environment — **Chromium cannot traverse the session's
agent proxy at all** (`example.com` fails with `ERR_CONNECTION_RESET`
identically to any other host, with and without explicit proxy args). §3's prior
— that these are multi-year rolling class averages and therefore fail C — is
**untested and is NOT recorded as refuted here.**

### Candidate 4 — MISO data request: unchanged

A stakeholder process, not a fetch. After candidate 2's closure this is now the
**leading** route: per §3 it is "the one path that can be specified to meet §2
exactly rather than hoping an existing product happens to."

### Net

No source clears. The ask stays **open**, with candidate 2 closed, candidate 3
downgraded, and candidate 1 blocked on an environment limitation rather than on
evidence. **A session chartered to finish candidate 1 needs working browser
egress** — worth knowing before one is scheduled.
`docs/handoffs/xiso-4-queue-ratchet-2026-08-04.md` §3(b).
