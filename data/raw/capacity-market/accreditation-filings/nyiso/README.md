# R5a — NYISO's published IRM (ICAP) → UCAP translation methodology

Research-only findings for the question: does NYISO/NYSRC publish an
explicit ICAP-basis-IRM → UCAP-basis-requirement ratio, analogous to PJM's
Forecast Pool Requirement (FPR) or MISO's `(1+PRM_UCAP)/(1+PRM_ICAP)`
conversion? **No CSV, no schema, no model wiring in this pass** — this
directory holds only the raw-document research trail and extracted
formula/parameters, per the task that produced it (2026-07-15 session).

> **UPDATE 2026-07-18 (FF-3D — Option B landed).** The owner selected R5a
> Option B (NYCA-wide static proxy — pairing-adjudication 2026-07-15 §3), and
> this session located and downloaded the "MANUAL DOWNLOADS NEEDED" Appendix D
> table (see the note at the end of that section). The NYCA-wide realized
> translation factor is published in **NYSRC IRM Study Technical Appendices,
> Appendix D §D.1.1, Table D.2 "NYCA ICAP to UCAP Translation"** as the
> **"Derate Factor"** column (the §2.5 NYCA translation factor). The
> most-recently-realized value (2024-2025 capability year) is **0.1321**. It is
> now intaken as `metric=icap_ucap_translation_factor` rows in the sibling
> `../../demand-curve/nyiso/nyiso.csv` (2020-2021 … 2024-2025) and wired as
> `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"] = 1 - 0.1321 =
> 0.8679` (constants.py). The NYCA-wide factor (13.21%) is **~2.5× the NYC
> Locational 5.18%** below — confirming the adjudication's rejection of Option C
> (NYC-as-NYCA proxy) on boundary-mismatch grounds.

## Short answer

**NYISO does not publish a single forward-looking ICAP→UCAP ratio the way
PJM (FPR) or MISO (`PRM_UCAP`/`PRM_ICAP`) do.** Instead, its own ICAP Manual
defines the conversion as a **formula evaluated fresh each Capability
Period from the current fleet's realized aggregate UCAP and ICAP values** —
an accounting identity applied to whatever resources are actually
qualified to sell capacity that period, not a single planning-stage
percentage carried in a demand-curve parameters filing. NYISO calls the
resulting ratio-complement the **"translation factor."** The formula itself
*is* explicitly, formally published (verbatim below); a single numeric
value valid across years is not, because the methodology is designed to
recompute every period.

## The formula (primary source: NYISO ICAP Manual)

**Source:** NYISO "Installed Capacity Manual" (Manual 04), **Version 18.0,
Effective Date 07/07/2026, Committee Acceptance 06/18/2026 BIC** (the
version in effect as of this research, 2026-07-15) —
https://www.nyiso.com/documents/20142/2923301/icap_mnl.pdf
— Sections 2.4, 2.5, 2.6 (manual-internal pages 6-7; PDF pages 62-64 of the
281-page document).

**§2.4 — The NYCA Minimum Installed Capacity Requirement (the ICAP basis):**

> "The NYISO calculates the NYCA Minimum Installed Capacity Requirement in
> megawatts for the Capability Year as the product of the forecasted NYCA
> peak Load and the quantity one (1) plus the NYSRC Installed Reserve
> Margin ('IRM')."

i.e. `ICR_ICAP (MW) = Forecast_NYCA_Peak_Load_MW x (1 + IRM)`. The specific
IRM value is the NYSRC IRM Study Technical Report figure (see the sibling
`../../demand-curve/nyiso/nyiso.csv` `irm` rows for the 2021-2022 through
2025-2026 series).

**§2.5 — The NYCA Minimum Unforced Capacity Requirement (the ICAP→UCAP
translation), quoted verbatim:**

> "For each Capability Period, the NYISO will calculate the NYCA Minimum
> Unforced Capacity Requirement by multiplying the NYCA Minimum Installed
> Capacity Requirement by one (1) minus the NYCA translation factor. The
> NYCA translation factor shall be calculated by taking the quantity one
> (1) minus a value equal to: (a) the total amount of Unforced Capacity
> that all resources electrically located in the NYCA are qualified to
> provide during such Capability Period (as described in Section 4.5 of
> this ICAP Manual), divided by (b) the sum of the Installed Capacity
> values used to determine the Unforced Capacity of such resources for
> such Capability Period."

i.e., in formula form:

```
NYCA_translation_factor = 1 - [ SUM(UCAP of all NYCA-located qualified resources)
                                 / SUM(ICAP values used to derive those UCAP figures) ]

NYCA_Minimum_UCAP_Requirement = NYCA_Minimum_ICAP_Requirement x (1 - NYCA_translation_factor)
                               = NYCA_Minimum_ICAP_Requirement x [ SUM(fleet UCAP) / SUM(fleet ICAP) ]
```

So the "translation factor" is algebraically just **1 minus the system-wide
weighted-average UCAP/ICAP ratio of the qualified fleet** — i.e., the
system-wide capacity-weighted average forced-outage derate (built up from
each unit's own EFORd-based UCAP calculation under ICAP Manual §4.5 /
Attachment J). It is **not** a separately-adopted planning parameter; it
falls out mechanically from the current fleet's own accredited UCAP
ratings, recomputed **twice per Capability Year** (once for the Summer
Capability Period, once for Winter — ICAP Manual §8, "these translations
occur twice during the course of each capability year, prior to the start
of the summer and winter capability periods").

**§2.6 — Locational Minimum Installed Capacity Requirements (the same
mechanism, per Locality):**

> "For each Capability Period, the NYISO will convert the Locational
> Minimum Installed Capacity Requirements of LSEs into Locational Minimum
> Unforced Capacity Requirements by multiplying such Locational Minimum
> Installed Capacity Requirements by the quantity one (1) minus the
> Locational translation factor. The Locational translation factor shall
> be calculated by taking the quantity one (1) minus a value equal to: (a)
> the total amount of Unforced Capacity that all resources electrically
> located in the relevant Locality are qualified to provide during such
> Capability Period ..., divided by (b) the sum of the Installed Capacity
> values used to determine the Unforced Capacities of such resources for
> such Capability Period."

Identical structure, evaluated separately for each of the three
Localities (NYC, LI, G-J) using only the fleet electrically located in
that Locality — so the Locational translation factor differs from the
NYCA-wide one (a Locality with a different generation mix has a different
weighted-average forced-outage rate).

**Unit-level basis (§4.5, cross-referenced by §2.5):** a Generator's own
UCAP = Adjusted Installed Capacity x (1 - the unit's own derating
factor), where the derating factor is generally the unit's own
Equivalent Demand Forced Outage Rate (EFORd) averaged over the two
previous like-Capability-Period values (renewables/storage use an
analogous Capacity Accreditation Factor / Unavailability Factor
construction instead — ICAP Manual §4.5, pp. 65-69 of the PDF). The
translation factor is therefore the *capacity-weighted roll-up* of all
individual units' own accredited derates, not an independently-set
number.

## Worked numeric example (primary source: NYISO training material)

**Source:** NYISO "ICAP Demand Curve" — Intermediate ICAP Course training
deck, presented by Mathangi Srinivasan Kumar (Program Lead, Market
Training, NYISO), dated **May 20-21, 2026**, marked "FOR TRAINING PURPOSES
ONLY" —
https://www.nyiso.com/documents/20142/3036383/ICAP-Demand-Curves.pdf/a16634ed-20c8-0f50-5912-4dd92793cef8
— slides 38-39 ("Translating ICAP Demand Curves to UCAP Values", example:
NYC 2025 Summer Capability Period).

This is the *price-side* analogue of the §2.5/2.6 requirement-side
formula — how NYISO converts a demand curve published on an ICAP basis
into the UCAP-denominated curve actually used to clear the ICAP Spot
Market Auction (which transacts in UCAP MW). Quoted/transcribed from the
slide:

```
UCAP Reference Point = ICAP Reference Point / [ CAF of Peaking Plant x (1 - Derating Factor) ]
                      = $17.37/kW-month / [ 64.9% x (1 - 2.5%) ]
                      = $27.43/kW-month

UCAP Maximum Clearing Price = ICAP Maximum Price / [ CAF of Peaking Plant x (1 - Derating Factor) ]
                             = $41.30/kW-month / [ 64.9% x (1 - 2.5%) ]
                             = $65.23/kW-month

UCAP Required = NYC Forecast Peak Load x LCR x (1 - Derating Factor)
              = 11,004.6 MW x 78.5% x (1 - 5.18%)
              = 8,191.1 MW

UCAP at Zero-Crossing Point = UCAP Required x 118%   (NYC's zero-crossing %)
                             = 9,665.5 MW
```

Here "Derating Factor" (5.18% for NYC, Summer 2025) is the slide's
shorthand for the §2.6 Locational translation factor — confirming the
formula in the Manual is the one actually applied, with a concrete,
dated, in-effect number: **NYC's Locational translation factor for the
Summer 2025 Capability Period was 5.18%.** ("CAF" — Capacity
Accreditation Factor, 64.9% here — is a *different*, unit-specific
factor: the reference peaking-plant technology's own nameplate-to-UCAP
accreditation, used only in the *price* formula, not the aggregate
requirement formula.) No equivalent NYCA-wide or other-Locality/season
worked numeric example was found in this deck or elsewhere in this
research pass — see MANUAL DOWNLOADS NEEDED.

## Qualitative corroboration (NYSRC IRM Study Technical Reports)

Every annual NYSRC IRM Study Technical Report (see
`../../demand-curve/nyiso/nyiso.csv` for the four fetched vintages: 2021,
2022, 2023, 2024/2025 studies) carries a short section titled "NYISO
Implementation of the NYCA Capacity Requirement" (Section 8 in the 2024
IRM Study, https://www.nysrc.org/wp-content/uploads/2023/12/2024-IRM-Study-Technical-Report-11-28-23_ICS_284_clean_bp-approved-12-8-2023.pdf,
PDF p.34) that narrates the same mechanism in plain language and confirms
its direction of movement:

> "Due to lower contribution to reliability, the increase in wind
> resources lowers the translation factor from required ICAP to required
> UCAP which reflects the performance of all resources on the system."

and includes **Figure 8-1, "NYCA Reserve Margins"** (PDF p.35 of the same
report) — a line chart plotting "Required ICAP", "Required UCAP", and
"Existing ICAP" reserve margins (as % of peak load) for **2006-2023**.
Both the ICAP and UCAP margin series are visible and trend independently
(UCAP margins compress relative to ICAP margins over the period, visually
consistent with a shrinking translation factor as wind/solar penetration
rises) — but the chart carries **no printed data-label table**, only
axis gridlines, so no specific year's numeric translation factor was
transcribed from it (digitizing pixel positions off a line chart would be
estimation, not transcription — consistent with this repo's discipline
against fabricated/estimated figures). The text also references
**"Appendix D, Table D.1.1"** as containing the underlying "UCAP reserve
margin trends" numbers, but Appendix D was not located within the Report
Body PDF fetched for this pass (35 pages, ends after Figure 8-1) — it is
likely in the separately-published "Appendices" PDF, which was not
fetched this session (see MANUAL DOWNLOADS NEEDED).

## Why this differs structurally from PJM/MISO

This repo's schema notes (`data/dictionary/schema/capacity-market-demand-curve.schema.yaml`)
already capture PJM's `forecast_pool_requirement` (a single published FPR
= `(1+IRM) x Reference-Resource-Accredited-UCAP-factor`, filed once per
Delivery Year as a BRA planning parameter) and note MISO's analogous fixed
ratio. NYISO's mechanism is **not a peer to those two** — it is not filed
as a forward planning parameter at all, and there is no NYISO row this
research would add to that schema's `forecast_pool_requirement` metric,
because:

1. **PJM/MISO's ratios are single numbers fixed for a whole Delivery/
   Planning Year, published in the same filing as the demand curve
   itself** (so a forecasting model can read one ratio off the same
   document as Net CONE/IRM). NYISO's translation factor is instead an
   **output of the realized UCAP accreditation process**, computed twice
   a year from whichever units actually qualify that period — there is no
   single "the NYISO 2024-2025 ICAP→UCAP ratio" filed anywhere as a
   planning input, because the number does not exist until the
   Capability Period's UCAP accreditation is run.
2. It is **fleet-composition-endogenous by design** — NYISO's own
   materials frame the shrinking translation factor as a *desired
   incentive effect* ("The conversion to UCAP provides financial
   incentives to decrease the forced outage rates while improving
   reliability" — ICAP Manual §8 narrative, also echoed in the IRM Study
   text above), not a static planning assumption to be forecast
   independently of the fleet.
3. Because of (1) and (2), a forecasting model wanting NYISO's UCAP-basis
   requirement for a **future** year cannot simply carry forward a
   published ratio (as it can for PJM's FPR) — it would need to compute
   the same weighted-average-EFORd roll-up documented above from its own
   *forecast* fleet's accredited UCAP/ICAP mix, or use the
   most-recently-realized translation factor (e.g. NYC Summer 2025's
   5.18%, above) as a forward proxy. This research pass makes no
   recommendation on which approach to use — that is a modeling decision
   out of scope for this raw-document intake.

## MANUAL DOWNLOADS NEEDED (blocked or not located this pass)

- **NYSRC IRM Study "Appendices" PDF** — **✅ LOCATED & LANDED 2026-07-18
  (FF-3D).** The 2025-2026 study's Appendices companion is at
  https://www.nysrc.org/wp-content/uploads/2024/12/IRM-Report-Appendices-Final-December-6-2024.pdf
  ("NYSRC: NYCA Installed Capacity Requirement for the Period May 2025 through
  April 2026 — Technical Appendices, December 6, 2024"). The section the Report
  Body calls "Appendix D, Table D.1.1" is **Appendix D §D.1.1 "New York Control
  Area ICAP to UCAP Translation," Table D.2 "NYCA ICAP to UCAP Translation"**
  (PDF p.73) — the "Derate Factor" column IS the §2.5 NYCA translation factor.
  The companion **Table D.1 "Historical NYCA Capacity Parameters"** (PDF p.71)
  carries Base-Case/EC-Approved IRM and the "NYCA Equivalent UCAP Requirement
  (%)" (the UCAP-basis reserve margin), which reconciles the Table D.2 derate:
  `(1 + EC_IRM) × (1 − derate) − 1 = UCAP margin` to ≤0.1pp every year. Landed
  as `icap_ucap_translation_factor` rows in `../../demand-curve/nyiso/nyiso.csv`
  (the recent capability-year window 2020-2021 … 2024-2025, keyed to each row's
  own published ICR% → EC-approved IRM). The Table D.2 "Year" label is a summer
  forecast year with a documented off-by-one/duplicate quirk (two rows labelled
  "2022"), so rows are keyed to capability year via ICR%, not the "Year" cell.
- **A NYCA-wide (not just NYC-locational) worked UCAP-translation
  numeric example** — only the NYC Summer 2025 example (5.18% Locational
  translation factor) was found; no equivalent NYCA-wide, G-J, LI, or
  Winter-period worked example was located in this pass.
- **NYISO's actual per-Capability-Period *published* translation-factor
  value(s)** as a standalone posted number (as opposed to embedded in a
  training-deck worked example or back-derivable from Gold Book ICAP/UCAP
  totals) — the ICAP Manual describes the *calculation procedure* but this
  research did not locate a NYISO web page or filing that tabulates "the
  NYCA translation factor for CY 2021-2022 was X%, for CY 2022-2023 was
  Y%, ..." the way the Demand Curve Reference Points are tabulated in
  `../../demand-curve/nyiso/nyiso.csv`. The NYISO Gold Book (Load &
  Capacity Data, e.g.
  https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Final.pdf)
  likely carries the raw ICAP/UCAP MW totals needed to back-compute this
  per year, but was not opened for that specific purpose this session.

## Citation index

| Source | URL | Used for |
|---|---|---|
| NYISO ICAP Manual (Manual 04), v18.0, eff. 2026-07-07 | https://www.nyiso.com/documents/20142/2923301/icap_mnl.pdf | §2.4/2.5/2.6 formula (verbatim) |
| NYISO "ICAP Demand Curve" Intermediate ICAP Course training deck, 2026-05-20/21 | https://www.nyiso.com/documents/20142/3036383/ICAP-Demand-Curves.pdf/a16634ed-20c8-0f50-5912-4dd92793cef8 | Worked NYC Summer 2025 example |
| NYSRC 2024 IRM Study Technical Report, approved 2023-12-08 | https://www.nysrc.org/wp-content/uploads/2023/12/2024-IRM-Study-Technical-Report-11-28-23_ICS_284_clean_bp-approved-12-8-2023.pdf | §8 narrative + Figure 8-1 (qualitative trend, not transcribed numerically) |
