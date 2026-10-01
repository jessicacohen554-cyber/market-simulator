# FINDING — lane SOCO-12 (IRP / SERC / SEEM / NRC documents + fuel prices), 2026-09-13

Charter: `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-12, §6 rows 4
and 6–8, §3 cards S5 / S6 / S8. Branch `claude/soco-12-docs-a41f`, cut off
`origin/main` at `2c2fc065`. Model: Opus `claude-opus-5`. Data profile: `shared`.
**Zero solves** (rule 32 `[R-SHARD]` — this lane never runs an LP; it did not
need to).

---

## 0. The two answers the desk asked for first

### 0.1 LTLF — **NOT BLOCKED. Gate G12 is MET, with a real edition and vintage.**

> **edition `Budget 2025 (B2025) / 2025 IRP` · vintage `2025` · horizon 2025–2044
> · 60 rows committed at `data/raw/load-forecast/soco/soco.csv`, parsing and
> `validate_tidy`-clean through the package's own `parse_unified_csv`.**

The forecast is Georgia Power's **"Budget 2025 Load and Energy Forecast"**, filed
as Technical Appendix Volume 1 §1 of the **2025 Integrated Resource Plan**
(Georgia PSC Docket **56002**, document **221233**, filed **2025-01-31**;
approved by the Commission **2025-07-15**, order filed 2025-07-31). It names
itself and its horizon in its own executive summary, so neither the edition nor
the vintage is inferred. It carries **summer peak, winter peak and energy** for
twenty years, on a declared `net` basis for the peaks. `scripts/lib/load_forecast`'s
`test_specs_declare_an_edition_and_a_vintage` is satisfied (edition non-empty,
vintage 2025 ≥ 2020, `default_basis="net"` ∈ `BASES`) — verified by dry-running
the real parser and validator against a throwaway in-memory spec, because
`scripts/lib/load_forecast/soco.py` is **SOCO-20's** file and this lane must not
write it.

**The one qualification, and it is material rather than fatal.** The forecast is
**Georgia Power Company**, not the SOCO footprint. The same workbook carries a
**System** column — the IIC companies, i.e. SOCO — and **every System cell is
`REDACTED`** in the public disclosure, in all four summary sheets and in
`Energies`. So the datatype covers roughly **half the footprint by peak**, and
the other half is not publicly forecast at all: §5 below establishes that
**Alabama Power files no public IRP**, because Alabama has no IRP statute.
Nothing here is grossed up to the footprint; a SOCO-wide forward peak is a
*construction* SOCO-20/SOCO-32 must declare. The measured SOCO-wide peak
**history** does exist and is much better evidence — §1.3.

### 0.2 SEEM — the charter's finding is **substantially CORRECT on the conclusion that matters, and WRONG as stated.** Three corrections.

Plan §2.6 says SEEM is *"live since November 2023"* and *"publishes participation
and matched-volume statistics and, deliberately, **no price**"*.

| # | Charter | Measured 2026-09-13 | Where |
|---|---|---|---|
| 1 | live since **November 2023** | **November 2022** | SEEM FAQ: *"The market launched in November 2022."* Corroborated by the 2023/2024/2025 annual audit reports (*"SEEM began operating in November 2022"*) and by the auditor's monthly-report series, which starts **2022-11** |
| 2 | publishes **no price** | **SEEM's own site publishes no price; its Independent Market Auditor does, monthly, publicly, back to 2022-11** | see below |
| 3 | (not anticipated) | **FERC accepted a settlement on 2026-01-05 under which SEEM WILL post average HOURLY price data** | press release, tracked |

**What SEEM itself publishes, page by page, all checked through the WordPress
REST API on 2026-09-13:** the "Public Data" page (`/reports/`) returns
**`"This content is restricted."`** — free registration, but a wall from here;
and the three informational-report pages that would carry price all read
**"No reports available at this time."** (`/public-hourly-informational-reports/`
id 1171, `/public-daily-informational-reports/` id 1166,
`/publicmonthlyinforeports/` id 1144). SEEM's own FAQ routes price away from
itself: *"the bilaterally-agreed transaction prices will be made available to the
public via **existing FERC reporting**"* — **independent corroboration of card S2
option (a), the FERC-EQR route, from SEEM's own mouth.**

**What the auditor publishes, and it is a genuine price series:** the "Public
Monthly Auditor Reports" page (`/auditor-reports/`, id 1433) is **public with no
login** and carries monthly reports **2022-11 → 2026-07** plus annual reports for
2023, 2024 and 2025. Every annual report has a section headed **"SEEM Prices"**
with a figure "Monthly Clearing Prices and Natural Gas Costs" (monthly
weighted-average settlement price, peak and off-peak, with daily min/max
whiskers); the monthly reports carry a **daily** average clearing-price chart and
a cleared/uncleared/avg-price table. In text:

| Year | Cleared volume | Weighted-avg price, all segments | Range by segment |
|---|---|---|---|
| 2023 | 704,000 MWh | **~$30/MWh** | $10–$80/MWh |
| 2024 | 1,055,000 MWh | **~$23/MWh** | $9–$61/MWh |
| 2025 | 1,303,000 MWh | **~$32/MWh** | $19–$91/MWh |
| 2026-07 (monthly) | ~90,000 MWh trailing avg | **$35/MWh** | — |

**Why this does NOT rescue the price problem, and card S2 still stands exactly as
written.** Four reasons, each disqualifying on its own:

1. **It is SEEM-wide, not SOCO.** SEEM spans ~24 members across 12 states — Duke,
   TVA, Dominion, Santee Cooper, LG&E/KU, AECI, the Florida entities and the
   Georgia co-ops as well as the three Southern OpCos. A platform average is not
   a Southern Company price, and the auditor says so itself: *"the average prices
   by segment ranged from $19/MWh to $91/MWh … the value of transactions can vary
   significantly by path."* A 4.8× spread across segments in one year is the
   measure of how little the average constrains any one location.
2. **It is monthly, and chart-borne below that.** Three of the rubric's four
   load-bearing criteria are scored on **hourly** duals (C3a mean, C3b shape, C3c
   tail). A monthly mean cannot score C3b or C3c at all.
3. **It prices a 15-minute residual-economy exchange, not the footprint's
   energy.** 1.3 TWh cleared across all of SEEM in 2025 against **239 TWh** of
   SOCO demand — about **0.5 %**, and that is SEEM-wide, so SOCO's share is a
   fraction of it. This is the price of the marginal bilateral top-up, not of
   serving load.
4. **The hourly posting is prospective and not yet live.** The FERC-accepted
   settlement (2026-01-05) obliges SEEM to *"publicly post the average hourly
   price data for transactions made on the platform during the prior hour"* — it
   is not retroactive to 2023–2025, and as of 2026-09-13 the hourly page is
   still empty.

**What it IS good for, and this is a real contribution to SOCO-13:** an
**independent public anchor** for the STOP gate. SOCO-13's charter asks for
*"a RECONCILIATION against at least one INDEPENDENT public anchor … with the
tolerance stated as a number"*, and names *"any published SEEM or Southern
disclosure SOCO-12 finds"* as a candidate. The three annual figures above are
that candidate: measured, public, and produced by a third party under FERC-
approved market rules. The tolerance is SOCO-13's to pre-register; the caveats in
(1)–(3) are why it can only ever be a **boundedness** check on an EQR index, never
the benchmark itself. **Rule 13 `[R-MEASURED]` / plan gate G17 bite here and the
answer is no: a SEEM-wide monthly average must never be written to
`actual_lmp_hourly_SOCO.parquet`.**

---

## 1. Got / blocked

| # | Item | Status | Landed at |
|---|---|---|---|
| 1 | Georgia Power IRP (most recent) | **GOT** — 2025 IRP, full public disclosure (103.7 MB zip) + the approving PSC order | `data/raw/soco-planning/` (5 transcriptions) |
| 1 | Alabama Power IRP | **NOT FOUND — and it does not exist**, see §5 | recorded, README §5 |
| 1 | SERC assessment covering the footprint | **GOT** — SERC 2024–2026 Regional Risk Report **and** NERC 2025 LTRA SERC-Southeast panel | `transcriptions/SERC_*`, `transcriptions/NERC_*` |
| 1 | Southern Company fleet / capacity disclosures | **GOT** — Form 10-K FY2022–FY2025, targeted extracts | `transcriptions/Southern_Company_10-K_extracts_FY2022-FY2025.txt` |
| 1 | SEEM public reports | **GOT** — annual 2023/24/25, monthly 2026-07, FAQ, FERC settlement release | `data/raw/soco-planning/` |
| 1 | PRM by season | **GOT** — winter **26.0 %** / summer **20.0 %** long-term (25.5 / 19.5 short-term), System-level | README §1 |
| 1 | Peak-load history | **GOT** — 2022–2025 system maxima with dates | README §2 |
| 1 | Resource plan | **GOT** — approved 2025 IRP actions, order-cited | README §4a |
| 1 | **Inter-OpCo transfer limit** | **NOT PUBLIC — structurally, not incidentally.** The OpCos are one pooled dispatch under the IIC | README §4b — **this makes the card S3 TTC Tier-3** |
| 2 | SEEM price answer | **GOT, with three corrections** | §0.2 |
| 3 | NRC licence + SLR, 8 reactors | **GOT** | `data/raw/nuclear-license-status/soco.csv` |
| 4 | LTLF with edition + vintage | **GOT — G12 MET** | `data/raw/load-forecast/soco/soco.csv` |
| 5 | EIA delivered gas AL/GA/MS | **GOT, with a 2025 gap in GA and MS** | `data/raw/gas-prices/` |
| 5 | Pipeline basis + public index | **GOT (basis) / measured NO (index)** | `SOURCES_soco_gas.md` |
| 6 | Confirmed retirements | **GOT — and the finding is that the record is one of REVERSALS** | §6, README §6 |
| — | Mississippi Power 2024 IRP | **NOT RETRIEVED** — Mississippi PSC not swept | open item, §7 |
| — | Alabama PSC full-text document search | **NOT SWEPT** — the portal exists and was reached | open item, §7 |

Nothing was **blocked** by a host in the 403/404 sense that stops an item. Four
URLs returned non-200 and all four are recorded with their status in
`data/raw/soco-planning/SOURCES.md` §6; none of them was the only route to
anything. No value in any committed file came from memory.

### 1.3 The peak-load history, because it is the most reusable thing this lane found

From Southern Company's own Form 10-K, Item 2, one sentence per year:

| Year | System maximum demand | Date | Season | Realized reserve margin |
|---|---|---|---|---|
| 2022 | 37,035 MW | 2022-06-15 | summer | 20 % |
| 2023 | 36,919 MW | 2023-08-14 | summer | 19 % |
| 2024 | **38,194 MW** (all-time) | **2024-01-17** | **winter** | **16 %** |
| 2025 | 37,006 MW | **2025-01-22** | **winter** | 20 % |

**Two of the three backcast years peak in January, and the all-time system
maximum is a winter event.** That is the answer to the charter's *"the footprint
may be winter-peaking in some years — say which, with the evidence"*, and it sits
beside two other true statements that a careless reader would think contradict
it: Georgia Power **alone** is forecast to stay summer-peaking (B2025 §1.1, and
the committed CSV shows summer > winter in all 20 years), and NERC classifies
SERC-Southeast as *"a summer-peaking assessment area"*. The reconciliation is that
**adequacy binds in winter while energy peaks in summer** — which is exactly why
the Winter TRM (26 %) sits 6 points above the Summer TRM (20 %), and why NERC's
2029 probabilistic risk lands in *"winter mornings … and nights. December shows
the most risk, followed by January."* Full treatment: README §2.

Scope caveat SOCO-10 must carry: the 10-K figure *"excludes demand served by
capacity retained by MEAG Power, OPC, and SEPA"*, while EIA-930 `SOCO Demand`
does not. The two are different quantities; reconciling them is a finding, not a
bug.

---

## 2. Transcribed values — every number, with its citation

All page/table references are in `data/raw/soco-planning/README.md`, which is the
values table proper (this is its index). Nothing below is rounded from a
different number or carried from memory.

| Value | Number | Source |
|---|---|---|
| Winter Target Reserve Margin, long-term | **26.00 %** | 2024 Reserve Margin Study, Executive Summary RECOMMENDATIONS |
| Summer Target Reserve Margin, long-term | **20.00 %** | same |
| Short-term (inside 3 yr) adjustment | **−0.5 %** → winter 25.5 %, summer 19.5 % | same; reconciles cell-for-cell with the IRP summary workbook's System column, 2025–2027 |
| Winter EORM / Summer EORM (expected case) | 22.75 % / 18.25 % | same |
| Winter 1:10 LOLE threshold | 25.75 % | same |
| Summer TRM Floor at 26 % winter | 19.55 % | same |
| Peak weather sensitivity | +11.1 % hot summer, **+24.5 % cold winter** | same |
| Load-forecast error on peak | +5.2 % / −6.1 % | same |
| System max demand 2022 / 2023 / 2024 / 2025 | 37,035 / 36,919 / **38,194** / 37,006 MW | 10-K FY2022–FY2025, Item 2 |
| Realized reserve margin 2022–2025 | 20 / 19 / **16** / 20 % | same |
| Fleet nameplate at 2025-12-31, by OpCo | AL **13,822.077** · GA **14,789.068** · MS **4,017.874** · Southern Power 12,647.880 · SEGCO 1,019.680 · **System 46,296.579 MW** | 10-K FY2025, Item 2 |
| Generating mix 2025 | **20 % coal / 51 % gas / 19 % nuclear** (2007: 70/15/14) | 10-K FY2025, Item 1 |
| Coal retired since 2010 / converted since 2015 | >6,700 MW / 3,700 MW | same |
| External transfer capability into the System | MISO-South **1,791** (S) / **2,374** (W) MW; TVA **480 / 478** MW; 11 more rows | 2024 Reserve Margin Study, Tables I.1–I.2 |
| GPC peak forecast 2025 → 2044 | summer 17,802.1 → 30,513.9 MW; winter 16,264.2 → 28,543.7 MW | IRP summary workbook (committed CSV) |
| GPC energy forecast 2025 → 2044 | 95,293.9 → 194,890.0 GWh | same, **unit-corrected** — see §4 |
| Approved nuclear uprates | Hatch 1-2 **+58 MW**, Vogtle 1-2 **+54 MW** | GA PSC 2025 IRP Order; MW from IRP Main Doc printed p. 59 |
| Approved gas uprates | McIntosh 10-11 **+194 MW**, 1A-8A **+74 MW**; 380 MW over 14 units | IRP Main Doc printed p. 59 |
| NERC SERC-SE Reference Margin Level | **15.0 %** flat 2026–2035 | NERC 2025 LTRA printed p. 120 |
| NERC SERC-SE Anticipated Reserve Margin | 40.1 % (2026) → 21.0 % (2035) | same |
| SERC-SE coal capacity | 12,403 MW in plans; **11,145 MW from 2028** with announced-not-planned retirements | NERC 2025 LTRA printed p. 121 |
| SEEM cleared volume / avg price 2023–2025 | 704 / 1,055 / 1,303 GWh; ~$30 / ~$23 / ~$32 per MWh | SEEM annual audit reports |
| EIA delivered gas to EP, annual mean | AL 3.083 / 2.817 / 4.242 · GA 3.233 / 2.971 / **n/a** · MS 2.830 / 2.711 / **n/a** $/Mcf | EIA `N3045<ST>3` |
| 8 nuclear licence expiries | Hatch 1 **2054-08-06** / Hatch 2 **2058-06-13** (post-SLR) · Farley 1 2037-06-25 · Farley 2 2041-03-31 · Vogtle 1 2047-01-16 · Vogtle 2 2049-02-09 · Vogtle 3 2062-08-03 · Vogtle 4 2063-07-28 | NRC info-finder / COL-holder pages |

---

## 3. NRC (charter item 3) — `data/raw/nuclear-license-status/soco.csv`

Eight rows, one per reactor, all Southern Nuclear Operating Co. The CSV parses
and passes `validate_tidy` through the package's own reader (dry-run with a
throwaway in-memory spec — `scripts/lib/nuclear_license_status/soco.py` is
SOCO-20's file and was not created).

| Plant | Unit | EIA | MW | Docket | Current expiry | Stage | SLR |
|---|---|---|---|---|---|---|---|
| Joseph M. Farley | 1 | 6001 | 888.2 | 50-348 | **2037-06-25** | renewed_60 | **announced_intent** — expected Apr–May 2027 (LOI ML26048A183, NOI 2026-02-16). NOT filed |
| Joseph M. Farley | 2 | 6001 | 888.2 | 50-364 | **2041-03-31** | renewed_60 | same |
| Edwin I. Hatch | 1 | 6051 | 924.0 | 50-321 | **2054-08-06** | **slr_granted_80** | **GRANTED 2026-06-11** |
| Edwin I. Hatch | 2 | 6051 | 924.0 | 50-366 | **2058-06-13** | **slr_granted_80** | same |
| Vogtle | 1 | 649 | 1215.0 | 50-424 | **2047-01-16** | renewed_60 | **none** — absent from every section of the NRC SLR list |
| Vogtle | 2 | 649 | 1215.0 | 50-425 | **2049-02-09** | renewed_60 | none |
| Vogtle | 3 | 649 | 1114.0 | 52-025 | 2062-08-03 | original (Part 52 COL) | none |
| Vogtle | 4 | 649 | 1114.0 | 52-026 | 2063-07-28 | original (Part 52 COL) | none |

**Expiries inside the 2026–2050 model horizon: SIX of eight** — Farley 1 and 2,
Vogtle 1 and 2, and Hatch 1 and 2 **on their pre-SLR dates** (2034-08-06 /
2038-06-13). Hatch's SLR, granted 2026-06-11, is the only granted SLR in this
footprint and it moves 1,848 MW from inside the horizon to outside it. **Vogtle 1
and 2 — 2,430 MW — expire inside the horizon with no SLR of any kind on file**,
and Farley 1-2 (1,776.4 MW) with an announced intent only. A SOCO forecast that
assumes 8,282 MW of firm nuclear through 2050 assumes outcomes the instrument
record does not support for 4,206.4 MW of it. (SPP-12 recorded the identical
class of finding for Cooper and Wolf Creek.)

Three details worth not rediscovering:

- **Vogtle 3 and 4 are not on the info-finder.** They are Part 52 COL units at
  `/reactors/new-reactors/large-lwr/col-holder/vog{3,4}`, and their expiries are
  *"40 years after NRC Commission Finding in 10 CFR 52.103(g)"*, not 40 years
  after licence issuance.
- **A reported, unresolved discrepancy on Hatch.** The NRC info-finder pages still
  display the **pre-SLR** expiries (2034 / 2038) as of 2026-09-13, four months
  after the SLR decision. The CSV carries the post-SLR dates (the repo's
  established `slr_granted_80` convention — entry-to-SLR-period + 20 yr, which is
  also what the NRC's own Completed-Applications row prints) and the notes column
  records the lag as a publication lag, not a conflicting instrument.
- **The Georgia PSC approved uprates** at Hatch 1-2 (+58 MW) and Vogtle 1-2
  (+54 MW) in the 2025 IRP order. The MW are published at **two-unit** granularity
  only, so each is carried **once**, on that plant's unit-1 row, with both rows
  saying so — no per-unit split is invented.
- **Card S8 corroborated**: EIA-860 gives Vogtle 3 operating **2023-07** and
  Vogtle 4 **2024-04**, both inside the backcast window, which is the within-year
  COD the fleet vintage machinery has to resolve.

---

## 4. Gas (charter item 5)

Three per-state CSVs + their three source workbooks + `SOURCES_soco_gas.md`,
built the SPP-11 way from the **key-free** EIA dnav route (`EIA_API_KEY` is unset
in this container, exactly as plan §2.4 predicted). **Cross-checked against the
committed all-state table (SPP-49): 108 of 108 state-months agree exactly, 0
mismatches**, including which months are `NA`.

**The real gap: GA and MS publish nothing for 2025** (last published month
2024-12); AL is complete through 2025-12. That falls inside the backcast span, so
a 2025 SOCO solve has a measured delivered-gas price for **Alabama only**.
Whatever SOCO-32 does about it is a declared modelling choice in its own
derivation; nothing is filled in here.

**Pipeline basis — the plan's naming is correct on both legs.** Southern Company
Gas holds a **50 % equity interest in Southern Natural Gas Company, L.L.C.
("SNG")**, the system-wide transporter (10-K FY2025 Item 1); **Transco** reaches
northwest Georgia through the jointly-owned **Dalton Pipeline**, a 115-mile
Transco extension leased through 2042 (10-K Item 2 note (e)).

**Is a public daily or monthly index for that basis reachable? Measured NO.**
Both free EIA routes that feed the other ISOs' daily series were swept:
the Natural Gas Weekly Update's compact spot table carries exactly **Henry Hub,
New York, Chicago, Cal. Comp. Avg.** — no Southeast row; and the daily "Select
Spot Prices" region map has **no Southeast region at all** (its nearest is
Louisiana / Henry Hub). This is `SOURCES_miso_citygate.md`'s "MichCon daily is NOT
available free" one footprint over: the daily index at SOCO's own basis is a
paywalled ICE/NGI product. The monthly state series is the reachable measured
input, and **a SOCO winter-gas tail overlay has no free daily source behind it
today** — which matters more here than elsewhere, because §1.3 says the
footprint's recent peaks are January events.

**One unit correction, declared.** The IRP summary workbook's `Energies` sheet is
headed "GWh" and its cells are **MWh** (95.3 million "GWh" for 2025 would be
~2.5× total US generation). The anchor that forces the correction is inside the
same filing: B2025 §1.2.1, *"an average growth of 7,900 GWh each year from
2024-2034"*, against the workbook's implied 8,750 **GWh**/yr read as MWh — same
order; read as GWh it is 8,750,000 GWh/yr. The committed CSV carries
published-cell ÷ 1000 labelled `gwh`, and every affected row says so in its own
`source_page`. Rule 14 `[R-ACCURATE]`: real data used, misalignment documented in
place.

---

## 5. Alabama Power — **there is no public IRP, and that is the finding**

The charter asks for *"the most recent Alabama Power and Georgia Power IRP
filings"*. Georgia's is landed in full. **Alabama Power files no public
integrated resource plan, because Alabama has no IRP statute.** The Alabama PSC's
own Electricity Policy Division page describes its jurisdiction over the state's
single electric IOU entirely in terms of the **Rate Stabilization and
Equalization ("RSE")** ratemaking mechanism and rate/service review; it names no
resource-planning docket, no IRP requirement and no periodic resource filing.
Contrast Georgia, whose IRP is statutory — the PSC order recites *"approval
pursuant to O.C.G.A. § 46-3A-1 through 11 ('IRP Act')"*. `alabamapower.com` has
no resource-planning page (404).

**What covers Alabama Power instead, and it is substantial:** the **2024 Reserve
Margin Study is a Southern Company System study** that explicitly includes Alabama
Power, so the seasonal TRMs in §2 are footprint-wide and not Georgia-only; and the
FY2025 10-K carries Alabama Power's fleet total (13,822.077 MW) and its unit-level
retirement positions. What does **not** exist publicly is an Alabama Power load
forecast or capacity-expansion plan. That is why `load-forecast/soco/soco.csv` is
a Georgia Power series, and it is a limitation to state on the record rather than
paper over.

---

## 6. Confirmed retirements (charter item 6) — **the record is one of REVERSALS**

The admissibility bar is CLAUDE.md step 0: *an enforceable public instrument with
a date*. Applying it to this footprint produces an unusual result, and it is the
finding rather than a shortfall in the sweep.

**Executed and dated (step-0 admissible):**

- Georgia Power *"Retired Plant Wansley Units 1-2 and 5A and Plant Boulevard Unit
  1 on **August 31, 2022**"*.

**Reversed by an enforceable order:**

- The **2022 IRP Order**'s decertification of **Plant Scherer Unit 3** and **Plant
  Gaston Units 1-4 and A** by 2028-12-31 was superseded by the **2025 IRP Order**
  (Docket 56002/56003, filed 2025-07-31): *"The extended operation of Plant
  Scherer Unit 3 and Plant Gaston Units 1-4 and A beyond December 31, 2028, shall
  be approved."* Georgia Power's own footnote: *"the Company is **not pursuing
  retirement** of Plant Gaston Units 1-4 and A and Plant Scherer Unit 3 by
  December 31, 2028."*

**Reversed by company decision (FY2025 10-K):**

- **Plant Barry Unit 5** (700 MW) — 2021 ADEM NOPP to retire; now *"a decision was
  made to convert Plant Barry Unit 5 from coal to natural gas and to continue
  operating Plant Barry Unit 5 beyond December 31, 2028."*
- **SEGCO Plant Gaston Units 1-4** (1,000 MW) — NOPP to retire by 2028-12-31; now
  *"expects to operate Plant Gaston Units 1 through 4 through December 31, 2034."*
- **Plant Daniel Unit 2** — Mississippi Power notified the Mississippi PSC on
  **2025-01-09** of intent *"to extend the retirement date of Plant Daniel Unit 2
  and potentially extend the retirement dates of other fossil steam units beyond
  their current 2028 retirement dates"* to serve ~600 MW of new load.

**Announced, NOT instrument-bound — a different admissibility class, recorded as
such and NOT promoted:**

- **Plant Bowen Units 1-2** (1,400 MW) and **Plant Scherer Unit 3** (614 MW at
  75 %) under 2021 Georgia EPD NOPPs — but the 2025 IRP recommends *continued
  operation of Plant Bowen Units 1-4*, and the 10-K states that *"decisions
  related to retirement or continued operation of units are subject to Georgia
  PSC approval."*
- **Plant Greene County Units 1-2** — Alabama Power expects to retire its 60 %
  (300 MW) by end-2028, Mississippi Power its 40 % per its 2024 IRP, with the
  10-K's own hedge: *"The ultimate outcome of this matter cannot be determined at
  this time."*

**The rule this establishes for SOCO, and it should be written into the step-0
loader's SOCO source note:** a **Notice of Planned Participation** under the ELG
rule is an *environmental compliance election*, freely revocable, and is **NOT** a
step-0 instrument — the record above contains two NOPPs reversed and a third
overtaken by an IRP recommendation. The enforceable dated instrument in this
footprint is a **state-PSC order** (Georgia PSC decertification under the IRP Act;
Mississippi PSC on an MPC IRP; **Alabama has no equivalent**), or a retirement
already executed. This is precisely the case CLAUDE.md's step-1b **reversal
registry** exists for, and SOCO is the ISO where it will earn its keep.

For completeness, NERC's forward view as a capacity delta rather than a unit
list: SERC-Southeast coal is **12,403 MW flat 2026–2030** in system plans and
**11,145 MW from 2028** on the *"capacity with additional generator retirements"*
line — a **1,258 MW** announced-not-planned gap — while the panel states
*"SERC-Southeast is not expected to retire additional generation during this
time."*

**No `confirmed-retirements` CSV was written.** The charter asked this lane to
find the instruments; the registry file and its per-ISO module are SOCO-20's, and
on the evidence above the admissible SOCO row set is **very small** (Wansley/
Boulevard 2022, already executed and pre-window). Writing a row set that mostly
records reversals is a design decision for the registering lane, and the evidence
it needs is all here and in README §6.

---

## 7. Open items this lane did not close

1. **Mississippi Power's 2024 IRP** — cited repeatedly by the 10-K, never
   retrieved. The Mississippi PSC docket system was not probed. Low cost, real
   value: it is the only OpCo-level resource plan besides Georgia's.
2. **Alabama PSC full-text document search** — `pscpublicaccess.alabama.gov`
   reachable (200), an ASPX app, not swept. §5's conclusion rests on the PSC's own
   description of its jurisdiction, which is strong but is not the same as a
   negative docket sweep.
3. **Georgia Power's hourly load profile for 2021–2023** ships inside the IRP zip
   (`Hourly Load Profile Data.xlsx`; 2023 sheet 8,748 hourly values, max
   16,720.166 MW). That is a **measured zonal load series for the Georgia Power
   zone** and belongs to SOCO-11/SOCO-32 — flagged, not landed, because those are
   not this lane's files.
4. **B2025 large-load / data-centre rows.** The forecast isolates a large-load
   external adjustment (24,300 MW pipeline through the mid-2030s, 7,300 MW
   committed) but publishes it chart-borne; no `component="large_load"` rows were
   transcribed. A lane willing to do a chart read can add them.
5. **SEEM "Public Data"** is behind a free registration. If the desk wants to know
   whether that page carries anything the auditor reports do not, someone has to
   register. SOCO-12 did not create an account.

---

## 8. Rules

- **5 `[R-NO-MAGIC]`** — every transcribed value carries URL + page/table, in
  `data/raw/soco-planning/README.md` and in each CSV's own `source_doc` /
  `source_page` / `notes` column. No value came from memory.
- **13 `[R-MEASURED]`** — everything landed is a *reproducible input*, never an
  answer: NRC licence dates, published PRMs, a published forward load forecast,
  measured delivered fuel prices. §0.2 explicitly refuses the one thing here that
  could have become a forbidden proxy (a SEEM-wide average written as SOCO's
  hourly price).
- **14 `[R-ACCURATE]`** — the two places real data was adjusted are declared in
  place with the anchor that forces the adjustment: the `Energies` unit correction
  (§4) and Hatch's post-SLR expiry against a lagging info-finder page (§3).
- **27 `[R-PUSH]`** — no existing source file ≥300 lines was rewritten; every file
  this lane touched is **new**. Post-push blob verification is recorded in §9.
- **28 `[R-MECH-MATRIX]`** — **not engaged.** This lane tested no mechanism, added
  no `ScenarioConfig` field and registered no run, so it owes no matrix cell.
- **32 `[R-SHARD]`** — no LP was run and none was needed.
- **Collision rules (plan §8.0)** — this lane touched **no shared record**: not
  the plan, not the ledger, not `soco.md`, not `CHANGELOG.md`, not any matrix
  shard, not `src/`, not `scripts/lib/*/`, not `tests/`, not another ISO's data,
  not `frontend/data/forecast/**`. Its record is this FINDING plus the new data
  files listed in §9.

---

## 9. Files added (all new; nothing modified)

```
data/raw/soco-planning/README.md                      (the values table)
data/raw/soco-planning/SOURCES.md                     (URLs, re-fetch, host probes)
data/raw/soco-planning/SHA256SUMS.txt
data/raw/soco-planning/SEEM_FERC_Settlement_Press_Release_2026-01-12.pdf
data/raw/soco-planning/SEEM_Auditor_Annual_Report_2025.pdf
data/raw/soco-planning/transcriptions/  (14 .txt)
data/raw/nuclear-license-status/soco.csv              (8 rows)
data/raw/load-forecast/soco/soco.csv                  (60 rows)
data/raw/load-forecast/soco/SOURCES.md
data/raw/gas-prices/eia_delivered_gas_{AL,GA,MS}_monthly_2023-2025.csv
data/raw/gas-prices/eia_N3045{AL,GA,MS}3m_2026-09-13.xls
data/raw/gas-prices/SOURCES_soco_gas.md
docs/handoffs/FINDING-soco-12-2026-09-13.md           (this file)
```

---

## Log entry

*(For the desk to append verbatim to `docs/calibration-log/soco.md` — a shared
record this lane must not edit, plan §8.0 rule 1.)*

## 2026-09-13 — SOCO-12: planning corpus, NRC, LTLF, gas (W1, zero-LP)

**Gate G12 is MET.** The SOCO long-term load forecast is Georgia Power's
**Budget 2025 (B2025)**, vintage **2025**, horizon 2025–2044, filed with the 2025
IRP (GA PSC Docket 56002, doc 221233, 2025-01-31) and approved 2025-07-15 — 60
rows at `data/raw/load-forecast/soco/soco.csv`, parser- and validator-clean.
Caveat on the record: it is **Georgia Power only**; the workbook's Southern
Company **System** column is REDACTED throughout, and **Alabama Power files no
public IRP** (Alabama has no IRP statute), so roughly half the footprint has no
public forward load forecast.

**Card S2 / SEEM — the charter's finding is corrected in three ways but its
operative conclusion stands.** SEEM launched **November 2022**, not 2023. SEEM's
own site publishes **no price** (its three informational-report pages all read
"No reports available at this time"; "Public Data" is registration-gated), but its
**Independent Market Auditor publishes monthly clearing prices publicly, back to
2022-11** — ~$30 (2023), ~$23 (2024), ~$32 (2025) per MWh, SEEM-wide. And a
FERC-accepted settlement (2026-01-05) obliges SEEM to post **hourly** average
prices prospectively; the page is still empty. None of it is a SOCO hourly
benchmark — it is SEEM-wide, monthly, and prices ~0.5 % of SOCO demand — so
**card S2 stands unchanged**, with the auditor figures newly available to SOCO-13
as its independent reconciliation anchor. SEEM's own FAQ routes price to FERC
reporting, corroborating the EQR route.

**Card S6 — seasonal PRM, measured.** Southern Company System Target Reserve
Margin: **winter 26.0 %, summer 20.0 %** long-term (25.5 / 19.5 inside three
years), from the *2024 Reserve Margin Study of the Target Reserve Margin for the
Southern Company System* (Jan 2025), whose scope is exactly the IIC companies.
Winter is the binding season by the study's own words. **The footprint's 2024 and
2025 annual maxima are January events** (38,194 MW on 2024-01-17 is the all-time
system maximum; 2022 and 2023 peaked in summer), while Georgia Power alone stays
summer-peaking — adequacy binds in winter, energy peaks in summer.

**Card S3 — there is NO published inter-OpCo transfer limit, structurally.** The
Operating Companies *"function as a single, integrated public-utility system"*
under the IIC and are *"committed and dispatched as a common System without regard
to the ownership of each generating facility"*. They are not separately-dispatched
areas, so any three-zone topology registers **Tier-3, non-binding** TTCs on the
SPP-20 precedent. External seam transfer capabilities **are** published (MISO-South
1,791/2,374 MW, TVA 480/478 MW, eleven more rows) — card S4's input.

**Confirmed retirements — the record is one of reversals.** Only Wansley 1-2/5A
and Boulevard 1 (2022-08-31) are executed-and-dated. The 2022 IRP Order's Scherer 3
and Gaston 1-4/A retirements were **superseded by the 2025 IRP Order**; Barry 5 and
SEGCO Gaston 1-4 were reversed by company decision; Daniel 2's date is being
extended. **An ELG Notice of Planned Participation is NOT a step-0 instrument** —
the enforceable instrument here is a state-PSC order, and Alabama has none.

**NRC** — eight reactors landed at `data/raw/nuclear-license-status/soco.csv`.
**Six of eight expiries fall inside the 2026–2050 horizon.** Hatch 1-2 hold the
footprint's only granted SLR (2026-06-11, → 2054/2058); Farley 1-2 have an
announced intent only (expected Apr–May 2027); **Vogtle 1-2 (2,430 MW) expire
2047/2049 with no SLR of any kind on file**. Georgia PSC approved uprates of
+58 MW (Hatch 1-2) and +54 MW (Vogtle 1-2).

**Gas** — AL/GA/MS delivered-to-electric-power monthly series landed from the
key-free EIA dnav route; 108/108 cells reconcile with the committed all-state
table. **GA and MS publish nothing for 2025** — a real in-window gap. The
footprint's basis is **Southern Natural Gas** (50 % Southern Company Gas) plus
**Transco** into northwest Georgia via the Dalton Pipeline; **no free public daily
index exists at either**, measured against both EIA daily/weekly tables.

FINDING: `docs/handoffs/FINDING-soco-12-2026-09-13.md`. Zero solves.
