# ISO-NE qualified-capacity / EFORd-derate research (R5b)

Research-only session, 2026-07-15. **No model code was edited or wired this
session** -- `src/market_sim/` was not touched, no LP was run, nothing was
committed/pushed. This directory holds only the raw research findings and
citations; it is not curated/schema'd data (no CSV -- the deliverable here is
qualitative: a documented answer to a specific tariff-mechanism question, with
one clean numeric time series as a byproduct).

If a sibling `nyiso/` subdirectory exists alongside this one, it was created
by a different, concurrent session and was not read or touched by this one.

## Research question

Does ISO-NE's Forward Capacity Auction "Qualified Capacity" (QC) -- the
capacity value a resource is accredited at for the capacity market -- apply
an EFORd-style forced-outage derate *at qualification time* (the way this
repo's own supply ledger derates thermal capacity by `(1 - EFORd)`), or does
ISO-NE instead price availability/outage risk *separately* through
Pay-for-Performance (PFP), with QC itself closer to an undiscounted seasonal
claimed-capability figure? A "yes, QC is EFORd-derated" answer would mean the
repo's derate has a real ISO-NE analogue; a "no" answer would flag a
double-derate/representation mismatch worth documenting for a future session.

## Answer (well-evidenced, from primary tariff text)

**No.** For an Existing Generating Capacity Resource (non-intermittent), ISO-NE's
own Tariff defines Qualified Capacity as **the median of the resource's own
last five years of Seasonal Claimed Capability (SCC) ratings** -- a
demonstrated/claimed-output figure -- with **no EFORd or forced-outage term
anywhere in the formula**. Verbatim, ISO New England Transmission, Markets and
Services Tariff, Market Rule 1, Section III.13.1.2.2.1.1 ("Summer Qualified
Capacity"), effective 2025-05-03, Docket No. ER25-2149-000:

> "The summer Qualified Capacity of an Existing Generating Capacity Resource
> that is not an Intermittent Power Resource shall be equal to the median of
> that Existing Generating Capacity Resource's summer Seasonal Claimed
> Capability ratings from the most recent five years, as of the fifth
> Business Day in October of each year, with only positive summer ratings
> included in the median calculation."

(Section III.13.1.2.2.1.2, same effective date, is the parallel Winter
Qualified Capacity provision, keyed to winter SCC ratings and the fifth
Business Day in June.) A full-text search of the extracted ~600 KB of Section
III.13/III.14 tariff text (235 PDF pages) for "EFORd" and "Equivalent Forced
Outage" returns **zero matches** -- the term does not appear anywhere in the
Forward Capacity Market tariff sections that define qualification, auctions,
or settlement.

So: **EFORd exists at ISO-NE, but it lives in a different, aggregate-level
process, not in any individual resource's own accredited QC number.**
Individual forced-outage/availability risk is instead priced ex-post, at the
resource level, through Pay-for-Performance. This is exactly the hypothesis
the research question posed as the "separate PFP pricing" alternative, and it
is what the primary tariff text shows.

### Where EFORd actually is used: system-wide ICR-setting, not individual QC

ISO-NE's **Installed Capacity Requirement (ICR) Reference Guide** (Revision
2.0, effective 2021-09-15) documents the GE MARS probabilistic reliability
simulation used to translate the region's 0.1 days/year LOLE planning
criterion into the aggregate capacity requirement (ICR) that the Forward
Capacity Auction then procures. In that simulation:

> "Existing Capacity Resources (other than Intermittent Power Resources) are
> modeled at their existing summer Qualified Capacity (QC)" (Section 5.5.1)

> "A non-intermittent Generating Capacity Resource's equivalent forced outage
> rate demand (EFORd) assumption is calculated based on the resource's
> average five-year historical data from the ISO's database of NERC's
> Generator Availability Database System (GADS). ... The GE MARS model
> includes a representative EFORd and allotment of maintenance hours for all
> non-intermittent Generating Capacity Resources." (Section 5.6.1)

In other words: each resource is fed into the *reliability model* at its full
claimed-capability QC value, **and** the model separately carries that same
resource's EFORd as a probability-of-unavailability parameter, to compute how
much *aggregate* claimed capacity the region must procure so that the
fleet-wide probabilistic reliability target is met. EFORd inflates the
**system-wide ICR** (how much total QC New England buys), not any individual
resource's own QC (how much that resource itself is accredited/paid for).
Intermittent Power Resources are explicitly modeled differently (QC is
already their historical median output during defined "Intermittent
Reliability Hours," so "no EFORd or maintenance hours are allocated to these
resources" -- Section 5.6.2); Active/Passive Demand Resources and most Import
Capacity Resources are similarly handled outside the EFORd mechanism (Sections
5.6.3-5.6.5); non-IPR standalone battery storage is assigned a flat 5% EFORd
default pending more fleet data (Section 5.7.2).

### Where forced-outage/performance risk IS individually priced: Pay-for-Performance

Pay-for-Performance is explicitly a **two-settlement construct** layered on
top of QC, not a modification of QC itself. From ISO-NE's own FCM PFP
training module ("Introduction to ISO-NE Forward Capacity Market (FCM)
Pay-For-Performance (PFP)," 2018-03-19/23, Andrew Gillespie, Principal
Analyst -- citing Market Rule 1 Section 13 as the authoritative source):

> "Capacity Payment = Base payment [paid for by demand (load), based on
> capacity supply obligation (e.g., at FCA price), **never negative**] +
> Performance payment [a transfer between suppliers, based on system
> conditions and resource performance during a scarcity condition, **may be
> negative, zero, or positive**]"

The **Base Payment** is the QC-and-clearing-price product -- undiscounted for
forced-outage risk, matching the QC finding above. The **Performance
Payment** is where individual availability risk actually gets priced, ex
post, only during real scarcity intervals.

**Capacity Scarcity Condition (CSC) -- primary tariff definition**, Market
Rule 1, Section III.13.7.2.1, effective 2024-03-01, Docket No. ER22-983-000:

> "A Capacity Scarcity Condition shall exist in a Capacity Zone for any
> five-minute interval in which the Real-Time Reserve Clearing Price for
> that entire Capacity Zone is set based on the Reserve Constraint Penalty
> Factor pricing for: (i) the Minimum Total Reserve Requirement; (ii) the
> Ten-Minute Reserve Requirement; or (iii) the Zonal Reserve Requirement...
> provided, however, that a Capacity Scarcity Condition shall not exist if
> the Reserve Constraint Penalty Factor pricing results only because of
> resource ramping limitations that are not binding on the energy dispatch."

**Capacity Performance Payment Rate (PPR) -- primary tariff schedule**,
Market Rule 1, Section III.13.7.2.5, effective 2024-03-01, Docket No.
ER22-983-000 (a full historical-to-current schedule, verbatim):

| Capacity Commitment Period | PPR |
|---|---|
| June 2018 - May 2021 | $2,000/MWh |
| June 2021 - May 2024 | $3,500/MWh |
| June 2024 - May 2025 | $5,455/MWh |
| June 2025 - May 2026 and thereafter (current) | **$9,337/MWh** |

A Massachusetts Attorney General's Office comment letter filed with ISO-NE's
Markets Committee (hosted on iso-ne.com, dated for the 2026-05-12/14 meeting)
confirms the current $9,337/MWh figure and that ISO-NE has itself proposed
cutting it to **$3,500/MWh** (a ~62.5% reduction) in a forthcoming standalone
FERC petition, on the grounds that the rate -- set high after the 2014/2015
polar-vortex event -- now produces "penalties that far exceed what is
necessary to incentivize reliability," while empirically having only a
"muted effect" on FCA clearing prices as it escalated from $5,455 to $9,337
between FCA 15 and FCA 16. Settlement mechanics, same source:

> "Performance Payment = PPR x (ACP - Br x CSO)" where ACP = Actual Capacity
> Provided (energy/reserves actually delivered during the scarcity interval),
> Br = the system-wide Balancing Ratio (load+reserves / total CSO) for that
> interval, and CSO = the resource's own Capacity Supply Obligation.

This confirms the mechanism directly prices individual under/over-performance
during real scarcity events, independent of and in addition to the
undiscounted Base Payment -- i.e., ISO-NE's forced-outage/availability risk
pricing is a real-time, ex-post, resource-specific financial settlement, not
an ex-ante haircut to the resource's capacity value.

## Important dating caveat: the FCM itself is sunsetting

The current tariff text (version effective 2026-03-31, Docket No.
ER26-925-000) states directly, in the opening paragraph of Section III.13:

> "The final Forward Capacity Auction was held in February 2024 for Capacity
> Supply Obligations associated with the Capacity Commitment Period beginning
> June 1, 2027 and no Forward Capacity Auctions shall be held thereafter."

The QC-via-median-SCC and PFP mechanisms described above are the mechanism
**currently in force through the last Capacity Commitment Period (2027-2028,
"FCA18")**, and are what this session confirmed from the tariff. What
replaces the FCM after that (ISO-NE's capacity-accreditation-reform /
"Resource Capacity Accreditation" work is the likely successor process, per
general awareness, but this was **not independently researched or cited this
session** -- it was outside R5b's scope) is an open question for whichever
future session next touches this topic. Do not assume the QC/PFP structure
above persists past the CCP2027-2028 delivery year without re-checking.

## Sources

### Rendered directly this session (primary tariff text)

- **ISO New England Transmission, Markets and Services Tariff, Market Rule 1,
  Section III.13 & III.14** ("Forward Capacity Market" / adjoining section),
  tariff version effective 2026-03-31, Docket No. ER26-925-000:
  `https://www.iso-ne.com/static-assets/documents/regulatory/tariff/sect_3/mr1_sec_13_14.pdf`
  (235 pages; downloaded with `curl`, text extracted with `pymupdf`/`fitz`;
  full-text-searched for "EFORd", "Qualified Capacity", "Seasonal Claimed
  Capability", "Capacity Scarcity Condition", and "Performance Payment
  Rate"). Individual clause effective dates/dockets differ by subsection and
  are cited inline above (III.13.1.2.2.1.1/.2 -> 2025-05-03, ER25-2149-000;
  III.13.7.2.1 and III.13.7.2.5 -> 2024-03-01, ER22-983-000) since ISO-NE
  stamps each amended clause with its own effective date within the combined
  document.
- **ISO-NE PUBLIC Installed Capacity Requirement (ICR) Reference Guide**,
  Revision 2.0, effective 2021-09-15:
  `https://www.iso-ne.com/static-assets/documents/2021/06/icr-reference-guide.pdf`
  (48 pages; same download/extraction method). Note this explanatory guide's
  own revision is dated 2021 -- older than the tariff text above -- but its
  core finding (EFORd lives in the GE MARS/ICR simulation, not in QC) is
  independently corroborated by the current (2026) tariff's complete absence
  of "EFORd" from the QC-defining sections, so the conclusion is not resting
  on a stale document alone.
- **"Introduction to ISO-NE Forward Capacity Market (FCM) Pay-For-Performance
  (PFP)"**, ISO-NE customer training module, 2018-03-19/23, Andrew Gillespie
  (Principal Analyst, Market Development):
  `https://www.iso-ne.com/static-assets/documents/2018/06/2018-06-14-egoc-a4-0-iso-ne-fcm-pay-for-performance.pdf`
  (21 pages). Explains the two-settlement construct and worked examples;
  2018-era numbers (PPR=$2,000/MWh; illustrative RCPF figures TMNSR=$1,500/MWh,
  TMOR=$1,000/MWh) are historical -- current PPR is $9,337/MWh per the tariff
  schedule above; RCPF current values were not re-checked this session (out
  of R5b's scope -- RCPF is defined in Market Rule 1 Section III.2.7A(c),
  not Section III.13/14, so it wasn't in the document fetched).
- **Massachusetts Attorney General's Office comments on the PPR reduction
  proposal**, filed with ISO-NE's Markets Committee, hosted on iso-ne.com,
  dated for the 2026-05-12/14 meeting:
  `https://www.iso-ne.com/static-assets/documents/100035/a04_mc_2026_05_12-14_ma_ago_comments_ppr.pdf`
  (3 pages). Confirms current/proposed PPR figures and FCA15/FCA16 context.

### Consulted but only summarized via WebFetch (not independently full-text-rendered)

- ISO-NE FCM Participation Guide, "Qualified Capacity for CSO Bilateral
  Periods and Reconfiguration Auctions":
  `https://www.iso-ne.com/markets-operations/markets/forward-capacity-market/fcm-participation-guide/qualified-capacity-post-fca`
  -- describes how *already-qualified* QC values carry forward into
  post-FCA reconfiguration auctions/bilaterals; cites Market Rule 1 Section
  III.13.4.2. Consistent with, but not the source of, the primary finding
  above (that page covers post-FCA re-use of QC, not the original
  qualification formula).
- ISO-NE FCM Participation Guide, "About FCM Pay-for-Performance (PFP)
  Rules": `https://www.iso-ne.com/markets-operations/markets/forward-capacity-market/fcm-participation-guide/about-fcm-pay-for-performance-pfp-rules`
  -- plain-language PFP overview, consistent with the tariff text above.
- ISO-NE memo, "Updates to EFORd / Forced Outage Rate Calculations" (CAR-SA
  related): `https://www.iso-ne.com/static-assets/documents/100028/a03.1b_mc_rc_10.15-16_car-sa_updates_to_eford_forced_outage_rate_calculations_memo.pdf`
  -- downloaded (21 pages, `isone_eford_memo.pdf`/`.txt` in this session's
  scratchpad, not copied into the repo) but only lightly mined; confirms
  EFORd methodology detail (the FOHd/EFDHd formula components) without
  contradicting the QC-vs-ICR separation above. A future session digging
  into the CAR-SA (Capacity Accreditation Reform) successor mechanism should
  start here.
- KilowattLogic news summary of the PPR cut proposal:
  `https://kilowattlogic.com/news/iso-ne-capacity-performance-payment-rate-60-percent-cut-2026`
  -- secondary, corroborating context only; WebFetch could not extract exact
  figures from it (the MA AGO comments PDF above is the actual numeric
  source).

## MANUAL DOWNLOADS NEEDED / gaps

- **RCPF (Reserve Constraint Penalty Factor) current values.** Defined in
  Market Rule 1 Section III.2.7A(c), which is outside the III.13/III.14 PDF
  fetched this session. Not blocked, just not pursued -- out of R5b's direct
  scope (the CSC trigger *definition* was needed and found; the specific
  dollar penalty factors that operationally set CSC frequency were not).
- **ISO-NE's post-FCM/CAR-SA successor capacity-accreditation design.** The
  tariff itself flags that no FCA is held after the CCP2027-2028 delivery
  year (see dating caveat above); this session did not research what
  replaces QC/PFP. No specific URL was even attempted -- flagged as a full
  open item, not a fetch failure.
- No HTTP errors or fetch failures were logged for ISO-NE this session --
  every primary/quasi-primary URL listed above rendered successfully on the
  first or second attempt (contrast with the PJM/MISO deactivation-notice
  research in `../../deactivation-notice-periods/README.md`, which hit
  repeated blocks).
