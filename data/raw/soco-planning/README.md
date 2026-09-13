# `soco-planning` — Southern Company / SOCO planning & market-design source documents

Opened **2026-09-13** by lane **SOCO-12** (`docs/multi-iso/soco-addition-plan-2026-09.md`
§5 row SOCO-12, manifest rows 6 and 8). FINDING:
`docs/handoffs/FINDING-soco-12-2026-09-13.md`. Built on the
`../spp-planning/README.md` template.

**SOCO is a balancing authority, not an ISO** (plan §1). It publishes no market
rulebook, no offer cap, no tariff-borne PRM and no LMP, so this corpus has a
different centre of gravity from `spp-planning`: the planning evidence lives in
**state-PSC IRP filings**, **SEC Form 10-K**, **NERC/SERC assessments** and the
**SEEM auditor's** public reports, not in a market protocol.

Exact URLs, the re-fetch commands and every host probe: `SOURCES.md`. Checksums
of every fetched artifact, tracked or not: `SHA256SUMS.txt`.

## What is and is not tracked

| Artifact | Size | Tracked? |
|---|---:|---|
| `SEEM_FERC_Settlement_Press_Release_2026-01-12.pdf` | 38 KB | **yes** |
| `SEEM_Auditor_Annual_Report_2025.pdf` | 457 KB | **yes** |
| Georgia Power 2025 IRP public disclosure (`2025_irp_public_disclosure.zip`) | **103.7 MB** | no — 5 transcriptions |
| Georgia PSC 2025 IRP Order (Docket 56002/56003) | 12.8 MB pdf + docx | no — `transcriptions/GA_PSC_2025_IRP_Order_56002_56003.txt` |
| SERC 2024–2026 Regional Risk Report | 6.5 MB | no — `transcriptions/SERC_2024-2026_Regional_Risk_Report.txt` |
| NERC 2025 Long-Term Reliability Assessment | 7.8 MB | no — `transcriptions/NERC_2025_LTRA_SERC-Southeast_pp120-125.txt` (the SERC-SE panel only) |
| Southern Company Form 10-K, FY2022–FY2025 | 15–20 MB each | no — `transcriptions/Southern_Company_10-K_extracts_FY2022-FY2025.txt` |
| SEEM auditor annual reports 2023 / 2024, monthly 2026-07 | 0.4–0.6 MB each | no — transcriptions |

The untracked payloads follow the repo's **corpus conversion** convention
(`docs/bloat-removal-plan-2026-08.md` §4): the bulk payload stays out of the tree,
the `README` + `SHA256SUMS.txt` + a full text transcription stay in it, and
**re-fetch is the recovery route** — every URL in `SOURCES.md` was verified
working on 2026-09-13. The lane's charter allows this: it asks for "PDFs **or**
page-cited transcriptions".

`transcriptions/*.txt` from PDFs are **`pypdf` `extract_text`** output with page
markers `=====PDFPAGE n=====` (the SPP-13 convention; the *n*-th marker is PDF
page *n*, which for these documents differs from the **printed** page by a
front-matter offset — both are given below where they differ). Transcriptions
from `.docx` are `word/document.xml` with tags stripped, one paragraph per line
and table rows rendered `cell | cell`. All unedited.

---

# Transcribed values — the reason this directory exists

Everything below is quoted from the documents in this directory. **No value here
came from memory.** Three of them correct assumptions carried in the SOCO
addition plan; those are flagged and are the owner-card corrections.

## 1. Planning reserve margin BY SEASON — the card S6 answer

`transcriptions/2024_Reserve_Margin_Study_Southern_Company_System.txt` — *"An
Economic and Reliability Study of the Target Reserve Margin for the Southern
Company System"*, **January 2025**, filed as Georgia Power 2025 IRP Technical
Appendix Volume 1 §2. Its scope is **exactly the SOCO footprint**, stated on its
own first page:

> *"The Reserve Margin Study includes the companies that participate in the
> Intercompany Interchange Contract ("IIC"). Specifically, the Reserve Margin
> Study includes **Alabama Power Company, Georgia Power Company, Mississippi
> Power Company, and the portion of Southern Power Company included in the IIC**
> (collectively, the "Operating Companies")."*

**RECOMMENDATIONS**, verbatim from the Executive Summary:

> *"Maintain the current **26.00%** as the Winter TRM · Increase the Summer TRM
> to **20.00%** · Apply a short-term reserve margin that is **0.5% lower** than
> the long-term reserve margins"*

Those three lines reconcile **exactly** with the machine-readable target-reserve-
margin column of `GPC and System IRP Summary Data - 2025 IRP PUBLIC
DISCLOSURE.xlsx` (sheets `Summary - Winter` / `Summary - Summer`, column
`System`), which is public even though the rest of the System column is redacted:

| Delivery year | Winter TRM, System | Summer TRM, System | Winter TRM, GPC | Summer TRM, GPC |
|---|---|---|---|---|
| 2025 · 2026 · 2027 | **25.5 %** | **19.5 %** | 24.6059 % | 18.5757 % |
| 2028 … 2044 | **26.0 %** | **20.0 %** | 25.1348 % | 19.0853 % |

(2025–2027 are the "inside three years" short-term band at long-term − 0.5 %.)

Supporting numbers from the same study, each with its Executive-Summary sentence:

| Quantity | Value | Where |
|---|---|---|
| Winter Economic Optimum Reserve Margin (EORM), expected case | **22.75 %** | *"the EORM occurs at a winter reserve margin of 22.75%"* |
| Summer EORM, expected case | **18.25 %** | *"the EORM for the Summer TRM is 18.25%"* |
| Winter 1:10 LOLE threshold | **25.75 %** (curve crosses *"slightly above the 25.50%"*) | *"The TRM should be equal to or greater than the 25.75% 1:10 LOLE threshold"* |
| Summer TRM Floor at a 26 % Winter TRM | **19.55 %** | *"the Summer TRM Floor … must be at or above 19.55%"* |
| Summer-equivalent of the 26 % Winter TRM | **24.76 %** | *"The equivalent summer reserve margin that corresponds to the 26% Winter TRM is 24.76%"* |
| Prior Summer TRM (superseded) | **16.25 %** | *"Compared to the current 16.25% summer TRM"* |
| Weather sensitivity of peak | **+11.1 %** hot summer, **+24.5 %** cold winter | *"The System's peak demand can be as much as 11.1% higher in a hot summer year and 24.5% higher in a cold winter year"* |
| Load-forecast error on peak | **+5.2 % / −6.1 %** | *"peak demand may be up to 5.2% more than forecasted or as low as 6.1% less"* |
| Reliability model | **SERVM**, 1:10 LOLE annual criterion | *"The Company used the Strategic Energy and Risk Valuation Model ("SERVM")"* |

**Why the winter number is the bigger one**, in the study's own words:
*"Since winter is the constraining season for reliability on the System due to
additional winter-only reliability concerns, the Winter TRM was considered
first"*, and *"winter is the dominant season for annual reliability"*.

**The independent outside number, for contrast, NOT as a substitute.** NERC's
2025 LTRA sets a **Reference Margin Level of 15.0 %, flat 2026–2035**, for the
**SERC-Southeast** assessment area, against an Anticipated Reserve Margin falling
40.1 % (2026) → 21.0 % (2035)
(`transcriptions/NERC_2025_LTRA_SERC-Southeast_pp120-125.txt`, printed p. 120).
SERC-SE is *"all or portions of Georgia, Alabama, and Mississippi"* — close to,
but not identical with, the SOCO BA, and its 15 % is NERC's own generic reference,
not Southern's planning target. **`PLANNING_RESERVE_MARGIN_BY_ISO["SOCO"]` should
take the 2024 Reserve Margin Study's seasonal TRMs, not the LTRA's 15 %.**

## 2. Is the footprint winter-peaking? — measured, and the answer is "in 2024 and 2025, yes"

This is the plan's own open question (*"the footprint may be winter-peaking in
some years — say which, with the evidence"*), and the evidence is a single
disclosure Southern Company repeats every year in Item 2 of its Form 10-K
(`transcriptions/Southern_Company_10-K_extracts_FY2022-FY2025.txt`):

| Year | System maximum demand | Date | Season | Realized reserve margin |
|---|---|---|---|---|
| 2022 | 37,035 MW | **2022-06-15** | summer | 20 % |
| 2023 | 36,919 MW | **2023-08-14** | summer | 19 % |
| 2024 | **38,194 MW** — the **all-time** maximum | **2024-01-17** | **WINTER** | **16 %** |
| 2025 | 37,006 MW | **2025-01-22** | **WINTER** | 20 % |

Scope, stated on the disclosure: *"the traditional electric operating companies,
Southern Power Company, and SEGCO … These amounts exclude demand served by
capacity retained by MEAG Power, OPC, and SEPA."* So it is the IIC footprint
(≈ the SOCO BA) **less** the MEAG/OPC/SEPA retained slices — a caveat SOCO-10's
census must carry, since EIA-930 `SOCO Demand` does *not* make that exclusion.

**Three readings that all have to be held at once, and they do not contradict:**

1. **The SYSTEM's two most recent annual maxima are January events**, and the
   all-time maximum (38,194 MW, 2024-01-17) is a winter one. Two of the three
   backcast years are therefore winter-peaking on realized load.
2. **Georgia Power alone is forecast to stay summer-peaking.** B2025 §1.1:
   *"it is evident that Georgia Power is expected to remain a summer-peaking
   utility over the forecast horizon. The difference between summer and winter
   peaks in Budget 2025 ranges from approximately 1,500 MW to over 2,400 MW."*
   Its own records: all-time peak **17,985 MW on 2007-08-09**; highest winter peak
   **16,458 MW on 2024-01-17**. The committed
   `../load-forecast/soco/soco.csv` reproduces this — summer exceeds winter in
   **all 20** forecast years.
3. **NERC classifies SERC-Southeast as *"a summer-peaking assessment area"***
   (LTRA p. 120). That is a forecast-basis classification of a wider area.

The reconciliation is that **adequacy binds in winter while energy peaks in
summer** — which is precisely why the Winter TRM (26 %) is 6 points above the
Summer TRM (20 %), and why the 2029 LTRA probabilistic risk lands *"in winter
mornings (7:00-8:00 a.m.) and nights (10:00 p.m.-12:00 a.m.). **December** shows
the most risk, followed by **January**"* (LTRA p. 123). A SOCO model that carries
only a summer adequacy season will mis-state this footprint.

## 3. Peak-load history — see §2

The measured series above (2022–2025) is the peak-load history this corpus
carries; Georgia Power's own two records are in §2 reading (2). No longer
history was landed: the 10-K's own "all-time" line reaches back only as far as
the record standing in each filing year, and EIA-930 `SOCO hourly.parquet`
(already committed) is the better source for an hourly-derived history over
2023–2025. **Note for SOCO-10**: the 10-K peak and the EIA-930 peak are
*different quantities* (the MEAG/OPC/SEPA exclusion above), so a reconciliation
between them is a finding, not a bug.

## 4. Resource plan and the transfer-limit question (card S3)

### 4a. The resource plan

`transcriptions/GPC_2025_IRP_Main_Document.txt`, Chapter 8, and the Georgia PSC's
approving order (`transcriptions/GA_PSC_2025_IRP_Order_56002_56003.txt`). The
**approved** 2025 IRP actions, from the order's own ordering paragraphs:

- *"The extended operation of Plant Scherer Unit 3 and Plant Gaston Units 1-4 and
  A beyond December 31, 2028, shall be approved."*
- *"Approval of incremental capacity at Plant Hatch Units 1-2 and Plant Vogtle
  Units 1-2"* — **58 MW** and **54 MW** respectively (IRP Main Document printed
  p. 59), available as early as winter 2028/2029. Carried into
  `../nuclear-license-status/soco.csv`.
- *"Amendment to the certificate at Plant McIntosh Units 10-11 and 1A-8A for
  incremental capacity"* — **194 MW** (Units 10-11, by winter 2028/2029) and
  **74 MW** (Units 1A-8A, some as early as winter 2027/2028); **380 MW total
  across 14 upgraded units**.
- *"The authority to pursue the **natural gas co-firing** compliance pathway as
  the 111 GHG Rule strategy for Plant Bowen and Plant Scherer."*
- Hydro modernization across nine facilities totalling **665 MW** preserved, plus
  a projected incremental **16 MW** at Goat Rock Units 3-6.
- RFPs for **1,000 MW** utility-scale renewables and **100 MW** distributed
  generation (2 × 50 MW).

The forward capacity position the plan is solving is in the same workbook as §1:
GPC winter capacity need runs **−601.9 MW (2025) → +8,948.1 MW (2031) → +21,822.0
MW (2044)**; summer **−897.9 MW (2025) → +8,277.2 MW (2031) → +20,536.0 MW
(2044)** (MG0 scenario, excluding generic expansion resources).

### 4b. THE INTER-OPERATING-COMPANY TRANSFER LIMIT: **NOT PUBLIC — and that is a structural fact, not a gap in the sweep**

Card S3 asks for *"any published transfer limit between the operating
companies"*. **There is none, and the reason is that the Operating Companies are
not separately-dispatched areas.** IRP Main Document Appendix G, verbatim:

> *"Georgia Power is a member of the Southern Company Pool, which consists of the
> Operating Companies. **The Operating Companies function as a single, integrated
> public-utility system** through adherence to the Southern Company System
> Intercompany Interchange Contract ("IIC"), an agreement on file with FERC."*
> (§G.1)
>
> *"The generating assets of all the Operating Companies in the Pool are
> committed and dispatched as a common System **without regard to the ownership
> of each generating facility**. Subject to operational constraints and
> reliability considerations, the lowest cost generation assets are dispatched
> during each hour to meet the total needs of the customers of all the Operating
> Companies."* (§G.5)

Alabama Power, Georgia Power and Mississippi Power are three retail companies
inside **one** balancing authority under **one** central economic dispatch — they
are not control areas with rated ties between them. Sweeps performed and their
results (all negative): the 2025 IRP Main Document (167 pp.), the 2024 Reserve
Margin Study, the B2025 Load and Energy Forecast and the PSC order were regex-
swept for *transfer capability / transfer limit / import limit / tie limit /
intercompany transfer*. **Every hit is an EXTERNAL transfer capability** (§4c) or
the IIC's own coordination language. Internal transmission constraints certainly
exist physically; like SPP's N↔S rating they live in the (CEII) powerflow model,
not in a public document.

**Consequence for card S3, which is exactly the SPP-20 precedent**: if the owner
rules three zones, the inter-OpCo TTCs register **Tier-3, documented, and
non-binding**, rule 14 `[R-ACCURATE]`'s misalignment exception documented in
place, with the real value an open root-cause item (the plan's SOCO-54 lever).
Nothing in this corpus lets them be set from a published number.

### 4c. EXTERNAL transfer capability — the card S4 input, which IS published

2024 Reserve Margin Study, Tables I.1 (Summer) and I.2 (Winter), "Simulation
Regions Summary". `Avg TC` = *Average Transfer Capability into Southern Company
System (MW)*; `CBM` = Capacity Benefit Margin into the System (MW).

| Region | Summer RM modelled | Summer peak (MW) | Summer Avg TC | Summer CBM | Winter RM modelled | Winter peak (MW) | Winter Avg TC | Winter CBM |
|---|---|---:|---:|---:|---|---:|---:|---:|
| Duke | 24 % | 18,837 | 34 | 100 | 22 % | 18,129 | 407 | 100 |
| FPL | 31 % | 27,088 | 96 | 250 | 45 % | 22,299 | 153 | 250 |
| FPLNW | 28 % | 2,389 | 546 | – | 24 % | 2,246 | 1,164 | – |
| JEA | 37 % | 2,767 | 88 | – | 22 % | 2,913 | 141 | – |
| MEAG | 32 % | 2,447 | **Unlimited** | – | 39 % | 2,306 | **Unlimited** | – |
| MISO-South | 39 % | 33,858 | **1,791** | 300 | 34 % | 29,967 | **2,374** | 300 |
| OPC | 21 % | 11,115 | **Unlimited** | – | 36 % | 10,240 | **Unlimited** | – |
| Progress Carolinas | 37 % | 13,549 | – | – | 23 % | 14,735 | – | – |
| Progress FL | 29 % | 10,971 | 31 | – | 25 % | 11,233 | 50 | – |
| Santee Cooper | 18 % | 5,082 | 280 | – | 6 % | 5,506 | 533 | – |
| SCEG | 49 % | 4,966 | 59 | – | 33 % | 4,932 | 126 | – |
| TAL | 41 % | 631 | 12 | – | 64 % | 583 | 20 | – |
| TVA | 17 % | 32,332 | **480** | 250 | 15 % | 31,964 | **478** | 250 |

Read the two **Unlimited** rows carefully: MEAG and OPC are Georgia wholesalers
*inside* the same control area, not seams. The genuine external seams by size are
**MISO-South** (1,791 / 2,374 MW) and **TVA** (480 / 478 MW), with Duke, Santee
Cooper, SCEG and the Florida BAs an order of magnitude smaller. The study also
records that these were calibrated, not assumed: *"This calibration benchmarked
modeled energy with actual, eight-year average, non-PPA market transactions into
and out of the Southern Company region."*

## 5. Alabama Power and Mississippi Power — **NO PUBLIC IRP EXISTS FOR ALABAMA**

Card S6 and the lane charter both name *"the most recent Alabama Power and
Georgia Power IRP filings"*. Georgia's is §1/§4 above. **Alabama Power files no
public integrated resource plan, because Alabama has no IRP statute.** The
Alabama PSC's own Electricity Policy Division page
(`https://psc.alabama.gov/electricity/`, fetched 2026-09-13) describes its
jurisdiction over the state's single electric IOU entirely in terms of the **Rate
Stabilization and Equalization ("RSE") ratemaking mechanism** and rate/service
review; it names no resource-planning docket, no IRP requirement and no periodic
resource filing. Contrast Georgia, whose IRP is compelled by statute — the PSC
order recites *"approval pursuant to O.C.G.A. § 46-3A-1 through 11 ('IRP Act')"*.

**What covers Alabama Power instead, and it is better than nothing:** the 2024
Reserve Margin Study (§1) is a **Southern Company System** study that explicitly
includes Alabama Power, so the seasonal TRMs are footprint-wide; and the FY2025
10-K carries Alabama Power's fleet total (**13,822.077 MW**) and its unit-level
retirement positions (§6). What does **not** exist publicly is an Alabama Power
load forecast or capacity-expansion plan. That is the honest state of the card S6
/ G12 evidence and it is why `../load-forecast/soco/soco.csv` is a **Georgia
Power** series carrying the whole datatype.

Mississippi Power **does** file an IRP with the Mississippi PSC (the FY2025 10-K
cites its **2024 IRP** repeatedly, §6 below). SOCO-12 did not retrieve it — the
Mississippi PSC docket system was not swept, and that is an open item, not a
block.

## 6. Confirmed retirements — the step-0 admissibility finding

Full analysis, per-unit, with the admissibility class of each instrument, is
FINDING §6. The headline for this corpus: **the SOCO footprint's fossil-exit
record over 2021–2025 is one of ANNOUNCEMENTS BEING REVERSED**, and the only
enforceable dated instruments point the *other* way.

- **Executed and dated** (CLAUDE.md step-0 admissible): Georgia Power *"Retired
  Plant Wansley Units 1-2 and 5A and Plant Boulevard Unit 1 on **August 31,
  2022**"* (IRP Main Document, 2022 IRP Action Plan status).
- **Reversed by an enforceable order**: the 2022 IRP Order's retirement of
  **Plant Scherer Unit 3** and **Plant Gaston Units 1-4 and A** by 2028-12-31 was
  superseded by the **2025 IRP Order** — *"The extended operation of Plant Scherer
  Unit 3 and Plant Gaston Units 1-4 and A beyond December 31, 2028, shall be
  approved."* Georgia Power's own footnote: *"As requested in this 2025 IRP, the
  Company is **not pursuing retirement** of Plant Gaston Units 1-4 and A and Plant
  Scherer Unit 3 by December 31, 2028."*
- **Reversed by company decision** (FY2025 10-K): **Plant Barry Unit 5** (700 MW)
  — a 2021 ADEM NOPP to retire, now *"a decision was made to convert Plant Barry
  Unit 5 from coal to natural gas and to continue operating Plant Barry Unit 5
  beyond December 31, 2028"*; **SEGCO Plant Gaston Units 1-4** (1,000 MW) — NOPP
  to retire by 2028-12-31, now *"expects to operate Plant Gaston Units 1 through
  4 through December 31, 2034"*.
- **Reversal in progress**: Mississippi Power notified the Mississippi PSC on
  **2025-01-09** *"of its intent to extend the retirement date of Plant Daniel
  Unit 2 and potentially extend the retirement dates of other fossil steam units
  beyond their current 2028 retirement dates in order to serve recently signed
  economic development loads of approximately 600 MWs."*
- **Still planned, not yet instrument-bound**: **Plant Bowen Units 1-2**
  (1,400 MW) and **Plant Scherer Unit 3** (614 MW at 75 %) under 2021 Georgia EPD
  NOPPs — but the 2025 IRP recommends *continued operation of Plant Bowen Units
  1-4*, and the 10-K states plainly that *"decisions related to retirement or
  continued operation of units are subject to Georgia PSC approval"*. **Plant
  Greene County Units 1-2** — Alabama Power expects to retire its 60 % (300 MW)
  by end-2028 and Mississippi Power its 40 % per the 2024 IRP, with the 10-K's own
  hedge: *"The ultimate outcome of this matter cannot be determined at this
  time."*

**The admissibility rule this establishes for SOCO**, and it is the finding: a
**Notice of Planned Participation** under the ELG rule is an *environmental
compliance election*, freely revocable, and **not** a step-0 instrument — the
record above shows two of them reversed. The enforceable dated instrument in this
footprint is a **state-PSC order** (Georgia PSC decertification under the IRP Act;
Mississippi PSC on an MPC IRP; Alabama has no equivalent), or an executed
retirement already on the books. The fleet-transition aggregate, for context
(FY2025 10-K): *"retiring over 6,700 MWs of coal-fired generating capacity since
2010 and converting 3,700 MWs of generating capacity from coal to natural gas
since 2015"*, with the mix moving 70 % coal / 15 % gas / 14 % nuclear in 2007 →
**20 % coal / 51 % gas / 19 % nuclear in 2025**.

NERC's LTRA carries the forward view as a capacity delta rather than a unit list:
SERC-Southeast coal is **12,403 MW flat 2026–2030** in system plans, and
**11,145 MW from 2028** on the *"capacity with additional generator retirements"*
line — *"Generators that have announced plans to retire but have yet to be
included in system plans"* — a **1,258 MW** announced-not-planned gap, and the
panel states *"SERC-Southeast is not expected to retire additional generation
during this time."*

## 7. SEEM — what it actually publishes

The full answer, with the charter correction, is FINDING §2 and it is the
load-bearing input to owner card **S2**. In one table, all from this directory:

| Surface | Public? | Carries a price? | Granularity |
|---|---|---|---|
| SEEM **Public Data** page (`/reports/`) | **registration-gated** ("This content is restricted") | unknown from outside | — |
| SEEM **Public Hourly / Daily / Monthly Informational Reports** pages | yes | **"No reports available at this time."** on all three, 2026-09-13 | — |
| SEEM **Independent Market Auditor** monthly + annual reports | **yes, no login** | **YES** | monthly avg clearing price; daily-average price charts |
| FERC **EQR** | yes | yes | per transaction |

SEEM's own FAQ routes price to FERC: *"the bilaterally-agreed transaction prices
will be made available to the public via **existing FERC reporting**"* — which is
independent corroboration of the plan §2.6 / card S2 option (a) EQR route.

Auditor price figures, for use as SOCO-13's **independent reconciliation anchor**
(they are SEEM-wide, not SOCO-specific — see the FINDING for why that matters):

| Year | Cleared volume | Weighted-average price, all segments | Range by segment |
|---|---|---|---|
| 2023 | 704,000 MWh | **~$30/MWh** | $10–$80/MWh |
| 2024 | 1,055,000 MWh | **~$23/MWh** | $9–$61/MWh |
| 2025 | 1,303,000 MWh | **~$32/MWh** | $19–$91/MWh |

## 8. SERC / NERC assessment identity

`transcriptions/SERC_2024-2026_Regional_Risk_Report.txt` is SERC's own
publication and is a **risk register, not a resource-adequacy assessment** — it
carries no reserve margin. Its value here is the footprint's institutional
identity: *"**Southern Company Services (SCS) is the Reliability Coordinator for
the Southeast subregion (SeRC)**"*, one of six RCs across SERC's seven subregions
(the others: FRCC for FL-Peninsula, MISO for MISO-Central and MISO-South, TVA for
Central, VACAR South for East, PJM for PJM). The adequacy numbers are NERC's, in
`transcriptions/NERC_2025_LTRA_SERC-Southeast_pp120-125.txt` (§1 above, plus the
SERC-SE capacity-by-fuel table 2026–2030 and the ProbA results: EUE 0.0 MWh in
2027, 0.4 MWh in 2029, LOLH 0.001 h/yr in 2029).

---

## Related directories

- `../load-forecast/soco/` — the B2025 peak and energy series transcribed out of
  the same Georgia Power IRP filing, in the curated `load-forecast` shape.
- `../nuclear-license-status/soco.csv` — Farley / Hatch / Vogtle licence expiries
  and SLR status, and the Georgia-PSC-approved nuclear uprates from §4a.
- `../gas-prices/SOURCES_soco_gas.md` — the AL/GA/MS delivered-gas series, the
  SNG / Transco Zone 4 basis finding, and the measured "no free daily index"
  result.
