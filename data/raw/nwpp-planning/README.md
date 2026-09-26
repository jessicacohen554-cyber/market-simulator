# `nwpp-planning` — NWPP/WECC planning & resource-adequacy source documents

Opened **2026-09-13** by lane **NWPP-12**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-12, manifest rows
7–11; FINDING `docs/handoffs/FINDING-nwpp-12-2026-09-13.md`). Modelled on
`data/raw/spp-planning/README.md`, which is this directory's template.

Exact URLs and every HTTP status this session observed: `SOURCES.md`.
Checksums of every fetched artifact, tracked or not: `SHA256SUMS.txt`.

**No value in this file came from memory.** Every number below is quoted from a
document in this directory (or, for the four `transcriptions/` sources, from the
committed text of one) and carries its printed page. Where a number could not be
sourced, the row says so and stays empty — it is never filled with a plausible
figure.

## What is and is not tracked

| Artifact | Size | Tracked? |
|---|---|---|
| 7 × WRAP Business Practice Manuals (BPM 101/102/103/108/109/204/210) | 0.62–0.95 MB each | **yes** |
| `WPP_Joint_WRAP_Statement_2025-09-29.pdf` | 0.04 MB | **yes** |
| `IdahoPower_2025_IRP_Final.pdf` + Appendices A and D | 4.0 / 0.84 / 3.6 MB | **yes** |
| `PSE_2023_Electric_Progress_Report_Ch{6,7}_*.pdf` | 1.3 / 0.73 MB | **yes** |
| `NVEnergy_2024_Joint_IRP_Volume1.pdf` (transmittal + 29-volume index) | 1.33 MB | **yes** |
| WECC 2024 Path Rating Catalog — Public Version | 10.9 MB | no — `transcriptions/2024_Path_Rating_Catalog_Public_v2.txt` |
| PacifiCorp 2025 IRP Vol. 1 | 13.4 MB | no — `transcriptions/PacifiCorp_2025_IRP_Vol1.txt` |
| PacifiCorp 2025 IRP Update (2026-03-31) | 13.4 MB | no — `transcriptions/PacifiCorp_2025_IRP_Update_2026-03-31.txt` |
| PGE 2023 CEP/IRP (revised 2023-06-30) | 15.9 MB | no — `transcriptions/PGE_2023_CEP-IRP_REVISED_2023-06-30.txt` |
| NorthWestern 2026 Montana IRP (public) | 7.5 MB | no — `transcriptions/NorthWestern_2026_MT_IRP_public.txt` |
| NV Energy 2024 Joint IRP Vol. 6 (load forecast / fuel) | 8.4 MB | no — `transcriptions/NVEnergy_2024_Joint_IRP_Volume6_LoadForecast.txt` |
| Avista 2025 Electric IRP | 5.8 MB | no — `transcriptions/Avista_2025_Electric_IRP.txt` |

The seven untracked payloads follow the repo's **corpus conversion** convention
(`docs/bloat-removal-plan-2026-08.md` §4): the bulk payload stays out of the
tree, the `README` + `SOURCES.md` + `SHA256SUMS.txt` + a full text
transcription stay in it, and **re-fetch is the recovery route** — every URL in
`SOURCES.md` was verified working on 2026-09-13. Tracked total ≈ 17 MB;
transcriptions ≈ 4.6 MB.

`transcriptions/*.txt` are **`pypdfium2`** `get_text_range()` output, unedited,
page markers `=====PDFPAGE n=====` where *n* is the **PDF** page. Extraction
tooling and its one material limit (image-rendered tables return nothing) are in
`SOURCES.md` §6.

---

# 1. WECC published path ratings — manifest row 7, card **N5**

Source for every row: **WECC 2024 Path Rating Catalog — Public Version**,
Studies Subcommittee (`transcriptions/2024_Path_Rating_Catalog_Public_v2.txt`).
In this document **the printed page number equals the PDF page number**
(verified: Path 1 is printed p. 8 and PDF page 8), so one page citation serves
both.

Rating categories, quoted from printed p. 6: **Accepted Rating** — *"A project
rating that has been reviewed and accepted by WECC members … This is a
comprehensive rating including both the simultaneous and non-simultaneous
transfer capabilities."*; **Existing Rating** — *"Transmission path ratings that
were known and used in operation as of January 1, 1994."*; **Other** — *"A
transmission path rating, either proposed or planned, that is not an accepted or
existing rating."* The catalogue's own scope note, same page: *"All information
in this catalog was provided, and should continue to be provided,
voluntarily."*

## 1.1 The paths the charter named

| Path | Name (catalogue title, verbatim) | Category | Printed p. | Transfer limits, verbatim |
|---|---|---|---|---|
| **3** | Northwest–British Columbia [Revised January 2013] | Accepted | 10 | N→S **3,150 MW** · S→N **3,000 MW** |
| **4** | West of Cascades–North [Revised January 2020] | **Other** | 11 | E→W **10,700 MW** · W→E **10,700 MW** |
| **8** | Montana-to-Northwest [Revised January 2013] | Accepted | 15 | E→W **2,200 MW** · W→E **1,350 MW** |
| **14** | Idaho-to-Northwest [Revised March 2022] | Accepted | 17 | E→W **2,400 MW** · W→E **1,200–1,340 MW**; seasonal: **2,400 MW Winter**, **2,300 MW** (unlabelled row), **1,200–1,340 MW Spring/Summer/Fall** |
| **20** | Path C (Pre-Gateway) [Revised January 2014] | Accepted | 23 | N→S **1,600 MW** · S→N **1,250 MW** |
| **27** | Intermountain Power Project DC Line [Revised January 2015] | Accepted | 28 | NE→SW **2,400 MW** · SW→NE **1,400 MW** |
| **35** | TOT 2C [Revised January 2018] | Accepted | 36 | N→S **600 MW** · S→N **580 MW** |
| **65** | Pacific DC Intertie (PDCI) [Revised February 2018] | Existing | 62 | N→S **3,220 MW** · S→N **3,100 MW** |
| **66** | California–Oregon Intertie (COI) | Existing | 63 | N→S **4,800 MW** · S→N **3,675 MW** |

> **Transcription note on Path 14.** The extracted text of the W→E cell reads
> `1,200–13,40 MW`. The seasonal block immediately below it on the same page
> reads `1,200–1,340 MW`, so the first is a digit-transposition artefact of the
> PDF text layer and the true value is **1,200–1,340 MW**. Recorded here rather
> than silently corrected. The middle seasonal row (`2,300 MW`) carries no
> season label in the text layer; a consumer needing it should read the PDF.

## 1.2 Neighbouring footprint paths the catalogue also rates

Not named in the charter, but each bears on a card N5 boundary or on what the
five-zone topology cannot express.

| Path | Name | Category | p. | Limits |
|---|---|---|---|---|
| **5** | West of Cascades–South [Rev. Jan 2020] | Other | 12 | E→W **7,200** · W→E **7,200 MW** |
| **6** | West of Hatwai [Rev. Nov 2007] | Accepted | 13 | E→W **4,277 MW** · W→E **Not defined** |
| **16** | Idaho–Sierra [Rev. Feb 2017] | Existing | 19 | N→S **500** · S→N **360 MW** |
| **17** | Borah West [Rev. Jan 2013] | Accepted / Other | 20 | E→W **2,557** · W→E **1,600 MW** (Other Rating) |
| **18** | Montana–Idaho [Rev. Jan 2015] | Accepted / Existing | 21 | N→S **383** · S→N **256 MW** |
| **19** | Bridger West (Pre-Gateway) [Rev. Feb 2015] | Accepted / Other | 22 | E→W **2,400** · W→E **1,250 MW** (Other Rating) |
| **55** | Brownlee East [Rev. Jan 2018] | Accepted | 54 | W→E **1,915 MW** · E→W **Not Rated** |
| **71** | South of Allston [Rev. March 2024] | Other | 65 | N→S **2,725 to 3,100 MW** (single range, no reverse row) |
| **75** | Hemingway–Summer Lake [Rev. Jan 2018] | Accepted | 68 | E→W **1,500** · W→E **550 MW** |
| **80** | Montana Southeast [Rev. Feb 2017] | Other | 73 | N→S **600** · S→N **600 MW** |
| **83** | Montana Alberta Tie Line [Rev. Jan 2018] | Accepted | 76 | (ratings per NorthWestern, §3 below: 325 MW southbound / 300 MW northbound) |
| **85** | Aeolus West Path (Post Gateway) [Added March 2021] | Accepted | 78 | E→W **2,670** · W→E **1,816 MW** |
| **86** | West of John Day [Added March 2021] | Accepted | 79 | E→W **4,760 MW** · W→E **Not Rated** |
| **87** | West of McNary [Added March 2021] | Accepted | 80 | E→W **4,925 MW** · W→E **Not Rated** |
| **88** | West of Slatt [Added March 2021] | Accepted | 81 | E→W **4,760 MW** · W→E **Not Rated** |

## 1.3 Path → card N5 boundary — and the boundary that has no path

**How the mapping was made, and its one soft joint.** The catalogue defines each
path by its **transmission lines and substation terminals**; it does **not** name
balancing authorities. Card N5's zones are groups of **balancing authorities**
(plan §2.5: no EIA-930 sub-BAs exist, so a zone may not split a BA). So every
row below is a reading of terminal ownership onto the BA map, not a quotation.
Rows whose terminals are unambiguous (a single owner on each end) are marked
**firm**; rows where the catalogue's own line list spans more than one owner on
one side are marked **soft** and say why.

Card N5 zones, for reference: **NW** = BPAT·PSEI·SCL·TPWR·CHPD·DOPD·GCPD
(+AVRN generation) · **OR** = PGE·PACW (+GRID generation) · **INLAND** =
IPCO·AVA·NWMT·WAUW · **EAST** = PACE · **SNV** = NEVP.

| Card N5 boundary | Published WECC path? | Which | Reading |
|---|---|---|---|
| **NW ↔ OR** | **NO — none** | — | **See §1.4. This is the finding.** |
| **NW ↔ INLAND** | **yes, three, none of which is the whole boundary** | Path **8** (2,200/1,350), Path **6** (4,277/n.d.), Path **14** (2,400/1,200–1,340) | soft. Three different BA pairs — 8 is NWMT↔BPA, 6 is BPA↔AVA (its line list names AVA terminals explicitly: Westside, Dry Creek, N. Lewiston, Harrington, Lind, Dry Gulch), 14 is IPCO↔BPA. A single link TTC is an **aggregation of three rated paths**, and saying so is the rule-14 documentation the link needs |
| **INLAND ↔ EAST** | **yes** | Path **20** "Path C" (1,600/1,250) | soft. Path C's terminals span the Idaho–Utah seam, but **PacifiCorp's own southeastern-Idaho territory is inside the `PACE` BA**, so part of Path C is PACE-internal. Direction convention: the catalogue's N→S is Idaho→Utah, i.e. **INLAND→EAST = 1,600 MW** |
| **EAST ↔ SNV** | **yes, and it is the clean one** | Path **35** TOT 2C (600/580) | **firm**. One line, Red Butte (PacifiCorp, SW Utah) – Harry Allen (NV Energy, near Las Vegas). N→S = EAST→SNV |
| **INLAND ↔ SNV** | **yes** | Path **16** Idaho–Sierra (500/360) | **firm**. One line, Midpoint (Idaho Power) – Humboldt (NV Energy, northern Nevada). N→S = INLAND→SNV. See §1.5 on the zone's name |
| **OR ↔ INLAND** | **not separately rated** | — | The Oregon-side terminals of Path 14 (Summer Lake, La Grande, Harney) are BPA substations, so Path 14 books to NW↔INLAND, not OR↔INLAND. No catalogue path rates a PGE/PACW ↔ IPCO/AVA/NWMT interface on its own |
| **NW ↔ SNV** | **yes — CORRECTED 2026-09-26 (NWPP-NEXT-6)** | Path **76** "Alturas Project" (300/300), printed p. 69 | **firm by BA pair.** One 345 kV line, Hilltop–Fort Sage (NV Energy). This row previously read "not adjacent", which Path 76 falsifies. The Hilltop 230 kV side is PacifiCorp-owned (HIFLD: Hilltop Tap–Warner 230 kV), but EIA-930 books NEVP's interchange on this seam against **BPAT** (−246 … +182 MW in 2023–2025; NEVP reports no PACW leg), and zones are BA groups, so it books NW ↔ SNV, not OR ↔ SNV. Modelled behind the gated `ScenarioConfig.nwpp_path76_alturas_link` |
| **NW ↔ EAST**, **OR ↔ EAST**, **OR ↔ SNV** | n/a | — | Not adjacent in the catalogue's path set |

**External seams — rated, but not internal boundaries.** Four of the charter's
paths connect the footprint to something **outside** it, so they size an
interchange, never a card N5 link:

| Path | Seam | Limits |
|---|---|---|
| 3 | NW ↔ **BC Hydro** (Canada — ruled OUT of the footprint by card N1) | 3,150 / 3,000 |
| 65 PDCI | NW (Celilo, BPA) ↔ **Sylmar / LADWP** | 3,220 / 3,100 |
| 66 COI | NW (Malin / Captain Jack, BPA) ↔ **PG&E / CAISO** | 4,800 / 3,675 |
| 27 IPP DC | EAST-adjacent (Intermountain, Delta UT) ↔ **Adelanto / LADWP** | 2,400 / 1,400 |

> **Path 27 does not book to a card N5 boundary at all, and the reason matters.**
> The Intermountain Power Project (EIA plant 6481, Delta UT) is filed in EIA-860
> under balancing authority **`LDWP`**, not `PACE` — measured this session off
> `data/raw/eia-860/eia860_plant.parquet`. IPP is therefore **outside the
> 17-BA footprint** even though it sits inside Utah, and its DC line is an
> LADWP-internal delivery path. A lane that books Path 27 as a PACE export is
> double-counting a plant this model does not own.

> **Path 66 COI is already in this repo, on the other side of the seam.**
> `config/iso_configs.py:570` gives CAISO `TransferLink(WECC_import → NP15,
> ttc_mw=4800.0)` and the comment at `:555` cites *"(California–Oregon Intertie)
> ~4,800 MW into NP15"* — the same number as this catalogue's Path 66 N→S rating.
> Recorded for card **N4**'s double-count exposure. **Rule 25 `[R-ISO-SCOPE]`:
> this lane changed nothing on the CAISO side and proposes nothing there.**

**Within-zone paths — rated, and inexpressible in a five-zone topology.** Eight
rated paths lie wholly inside one card N5 zone: Paths **4** (10,700 MW),
**5** (7,200), **71** (2,725–3,100), **86** (4,760), **87** (4,925), **88**
(4,760) inside/across **NW**–**OR**; Paths **17** (2,557) and **55** (1,915)
inside **INLAND**; Paths **19** (2,400) and **85** (2,670) inside **EAST**;
Paths **18** (383) and **80** (600) inside **INLAND** (Path 80's southern
terminals are WAPA's Yellowtail and Crossover — `WAUW` is an INLAND member —
with a PacifiCorp limb, so part of Path 80 is INLAND↔EAST). The point for the
desk: **the largest published constraints in this footprint (Paths 4, 87, 86, 88
at 4.8–10.7 GW) are BPA-internal east–west cuts that a whole-BA zoning cannot
represent at all.** That is a property of the zoning, not a data gap, and it
should be stated on a first keeper rather than discovered later.

## 1.4 **NWPP-NW ↔ NWPP-OR has no published WECC path rating. This is a positive finding, not a gap in the search.**

The desk expected this and deliberately did not assert it. It is confirmed:
**there is no path in the 2024 catalogue that rates a BPAT/PSEI/SCL/TPWR/CHPD/
DOPD/GCPD ↔ PGE/PACW interface.** The catalogue's Table of Contents was read in
full (printed pp. 2–5, all 89 numbered path slots including the 24 marked
`[Deleted]`), and the Pacific-Northwest paths it does carry are of a different
kind:

- **Paths 4 and 5** ("West of Cascades–North/South") are **east-to-west cuts**
  across the Cascades, not BA interfaces. Path 5's own line list (printed p. 12)
  mixes BPA-internal 500 kV (Big Eddy–Ostrander, Ashe–Marion, John Day–Marion)
  with BPA→PGE limbs (Big Eddy–McLoughlin, Big Eddy–Chemawa, Big Eddy–Troutdale,
  Jones Canyon–Santiam) **and** a PGE-internal limb (Round Butte–Bethel) in one
  rating. Its 7,200 MW is therefore not a BPAT↔PGE number and must not be used
  as one.
- **Paths 71, 86, 87, 88** (South of Allston; West of John Day / McNary / Slatt)
  are likewise BPA-internal cuts along the Columbia.

The physical reason is stated rather than assumed: BPA's system and the
PGE/PacifiCorp-West systems interconnect at **many** points around the Portland
and Willamette Valley load centre, so there is no single rated interface to
publish. **A dense multi-point interconnection is exactly the case WECC's path
process does not produce a number for.**

**Consequence for NWPP-20 under rule 14 `[R-ACCURATE]`.** The NW↔OR link is
**Tier-3 (calibration) — verify**, in the convention of
`docs/multi-iso/04-transmission-zones-and-congestion.md` ("All proposed link MW
values start **Tier 3 (calibration) — verify**, then move to Tier 1/2 once
sourced and validated against binding frequency"). The misalignment to document
in place is the one above: *no rated interface exists because the
interconnection is multi-point*. That is a documented absence with a physical
reason, which is a better basis for a Tier-3 value than a number borrowed from
Path 5.

**Tiering for the rest, on the same convention:**

| Boundary | Tier at registration | Why |
|---|---|---|
| EAST ↔ SNV | **Tier 1 candidate** | one rated path, one line, unambiguous terminals (Path 35) |
| INLAND ↔ SNV | **Tier 1 candidate** | ditto (Path 16) |
| INLAND ↔ EAST | **Tier 2** | Path 20 is rated, but is Pre-Gateway and partly PACE-internal — reconcile, document |
| NW ↔ INLAND | **Tier 2** | three rated paths aggregate onto one link; the aggregation is the documented reconciliation |
| **NW ↔ OR** | **Tier 3** | **no published rating exists** (this section) |

A Tier-1/2 promotion still requires the binding-frequency validation that
convention asks for, which this lane cannot supply — there is no NWPP
congestion archive (card **N2**).

## 1.5 Two structural notes for card N5, measured this session

1. **`NWPP-SNV` is a misnomer, and Path 16 is why it matters.** `SPPC` (Sierra
   Pacific Power, northern Nevada) **does not exist as a separate EIA-930
   balancing authority** — measured off
   `data/raw/eia-930/EIA930_BALANCE_2024_Jan_Jun.parquet`, whose 61 BAs include
   `NEVP` and no `SPPC`. So `NEVP` is **all of NV Energy, northern and southern
   Nevada**, and the zone card N5 names "SNV" spans the state. Path 16's Nevada
   terminal (Humboldt) is in **northern** Nevada and is nonetheless inside this
   zone. The mapping in §1.3 is correct; the **name** invites a reader to
   mis-file it, and NV Energy's own IRP is a *joint* Nevada Power + Sierra
   Pacific filing (§4.5) which confirms the single-company framing.
2. **Two Montana EIA-930 BAs are outside the plan's 17.** The same measurement
   shows `GWA` and `WWA` in the 2024 BALANCE file. Neither is in the charter's
   footprint list and card N1 is **RULED** (all 17), so this lane proposes no
   change — **routed to NWPP-10 / the desk** as an observation only.

---

# 2. WRAP — manifest row 8, card **N7**

## 2.1 The binding-season answer, with its citation

**WRAP's first binding season is Winter 2027–2028, beginning 1 November 2027.**
It is therefore **entirely outside the 2023–2025 backcast window**, and WRAP is
a **forecast-side object only** for this program.

Source: `WPP_BPM_109_Transition_Period_V3.0_2026-03.pdf` (Version 3.0, "Annual
BPM Review", 2026-03-19 — revision history, printed p. 1). Printed page = PDF
page − 1 throughout this document.

Printed **p. 3** (PDF p. 4), §1 Introduction, verbatim:

> *"The Forward Showing (FS) Program of the Western Resource Adequacy Program
> (WRAP) provides for a four-year Transition Period, commencing in Summer 2025
> Binding Season and ending after Winter 2028-2029 Binding Season. All
> Participants will participate in the Summer 2025 and Winter 2026-2027 Binding
> Seasons and all Binding Seasons in between as Non-Binding Participants. From
> Winter 2027-2028 all Participants will be Binding (excepting any Critical Mass
> provisions) and subject to certain charges for failure to meet or cure
> compliance obligations associated with Binding participation in the WRAP…"*

Printed **p. 4** (PDF p. 5), §2 Background, verbatim:

> *"All Participants will be subject to Binding participation obligations
> starting November 1, 2027 (for the Winter 2027-2028 Binding Season), but the
> Transition Period rules allow each Participant the option to elect to also
> participate one season earlier as a Binding Participant in Summer 2027."*

Printed **pp. 4–5** (PDF pp. 5–6), §3 and Table 1, verbatim:

> *"The Transition Period consists of the Summer Seasons for 2025, 2026, 2027,
> and 2028, and the Winter Seasons for 2025-2026, 2026-2027, 2027-2028, and
> 2028-2029. The Winter 2027-2028 Binding Season beginning November 1, 2027,
> will be the first Binding Season for all Participants whose Western Resource
> Adequacy Program Agreement (WRAPA) is effective on September 15, 2026, unless
> a Participant selects Summer 2027 as its first Binding Season. Transition
> Period provisions will continue to apply until March 15, 2029…"*

| Period (BPM 109 Table 1) | Participation |
|---|---|
| Summer 2025 → Winter 2026-2027 | Non-Binding participation only |
| **Summer 2027** | Both Binding and Non-Binding (opt-in one season early) |
| **Winter 2027-2028 → Winter 2028-2029** | **Binding participation only** |
| Summer 2029 onwards | Binding only; all standard WRAP requirements |

The early-binding election is gated on dates (printed p. 5, §3.1): a WRAPA
executed **on or before 2026-01-15** with notice by the same date, or one
executed after that and on or before **2026-09-15** with notice by its WRAPA
effective date. A deferral of the first binding season by up to two seasons is
possible but needs **75 % of both House and Senate vote tallies** of the first
binding season's Binding Participants (printed p. 6, §4.2).

Two independent corroborations from participants' own filings, both already in
this directory:

- PacifiCorp 2025 IRP Vol. 1, printed **pp. 105–106**: *"WRAP is currently
  operational with non-binding requirements and has plans in place to enable
  fully binding operations in Summer 2027 for participants that provide notice
  of their intent by January 2026. All participants will be binding for Winter
  2027-2028 (i.e. starting November 2027)."* Same page adds the exit rule:
  *"If a WRAP Participant chooses to exit the program, a two-year exit period
  applies. Current WRAP Participants have until October 31st, 2025, to exit the
  program without being subject to a financially binding season."*
- Idaho Power 2025 IRP Appendix D, printed **p. 6**: *"…14 MW of WRAP capacity
  benefit was included in the portfolio reliability modeling beginning in 2027 —
  the currently assumed date of binding participation — and continuing each year
  through the planning period."*

`WPP_Joint_WRAP_Statement_2025-09-29.pdf`, printed p. 1: *"The Western Resource
Adequacy Program (WRAP) continues to make progress toward its first binding
operational season in Winter 2027/28…"*

## 2.2 Seasons, and the subregion definition card N5 should see

**WRAP season definitions** — NorthWestern 2026 MT IRP, printed **p. 148**:
*"The WRAP defines the summer season as June 1 through September 15 and the
winter season as November 1 through March 15."* (Same paragraph notes a PRM Task
Force proposal to redefine winter as 20 November – 28/29 February, *"not been
finalized at this time"*.) PacifiCorp 2025 IRP Vol. 1 printed p. 104 states the
same seasons in months: *"summer (June through September) and winter (November
through March)"*.

**WRAP's own two-subregion cut** — `WPP_BPM_102_FS_Reliability_Metrics_V3.0_2026-03.pdf`
§4.1, printed **pp. 6–7** (PDF pp. 7–8). LOLE simulations, and therefore the
FSPRMs, are run **separately per subregion**:

| Subregion (current) | Component Balancing Authority Areas, verbatim |
|---|---|
| **Northwest** (Zones 1, 2, 3, 4) | Avista Corporation · BC Hydro and Power Authority · Bonneville Power Authority · Chelan County PUD #1 · **Douglas County PUD #1** · Grant County PUD #2 · **NorthWestern Energy** · PacifiCorp West · Portland General Electric · Puget Sound Energy · Seattle City and Light · Tacoma Power |
| **Southwest and East** (Zones 5, 6, 7, 8, 11) | Arizona Public Service · Basin Electric · Black Hills · **Idaho Power Company** · NV Energy · **PacifiCorp East** · Public Service Company of New Mexico · Salt River Project |

And, verbatim, *"Beginning with the Winter 2027–2028 Binding Season, the LOLE
Study to determine the FSPRM values will reflect the following, updated
Balancing Authority Areas"* — **Idaho Power moves from Southwest-and-East into
the Northwest Subregion** (which becomes Zones 1, 2, 3, 4, 5).

> **Why the desk should read this against card N5.** WRAP's operator-defined cut
> puts **NorthWestern Energy and Avista in the Northwest**, with **Idaho Power**
> in Southwest-and-East until Winter 2027-28. Card N5's `NWPP-INLAND` groups
> IPCO·AVA·NWMT·WAUW together, which no WRAP subregion does. Reported, not
> argued: card N5 is the desk's to rule, and WRAP's cut is an adequacy-study
> boundary, not a transmission one.

## 2.3 Which of the 17 BAs are participants

Two sources, and they do not agree exactly; both are recorded rather than
reconciled.

**(a) The WRAP programme page** (`westernpowerpool.org/about/programs/western-resource-adequacy-program`,
read 2026-09-13) displays **22** participant logos: Arizona Public Service ·
Avista · Bonneville Power Administration · Calpine · Chelan County PUD ·
Clatskanie PUD · Eugene Water and Electric Board · Grant County PUD · Idaho
Power Company · NV Energy · NorthWestern Energy · PacifiCorp · Portland General
Electric · Powerex · Public Service Company of New Mexico · Puget Sound Energy ·
Salt River Project · Seattle City Light · Shell Energy · Tacoma Power · The
Energy Authority · Tucson Electric Power Company.

Mapped onto the charter's 17 BAs — **13 of 17 are covered by a participant**:

| BA | Participant | | BA | Participant |
|---|---|---|---|---|
| AVA | Avista | | PACE | PacifiCorp (East) |
| BPAT | Bonneville Power Administration | | PACW | PacifiCorp (West) |
| CHPD | Chelan County PUD | | PGE | Portland General Electric |
| GCPD | Grant County PUD | | PSEI | Puget Sound Energy |
| IPCO | Idaho Power Company | | SCL | Seattle City Light |
| NEVP | NV Energy | | TPWR | Tacoma Power |
| NWMT | NorthWestern Energy | | | |

**Not covered by a logo:** `DOPD`, `AVRN`, `GRID`, `WAUW`. Calpine, Powerex,
Shell Energy and The Energy Authority are marketers rather than BAs; APS, PNM,
SRP and Tucson Electric are Desert-Southwest participants outside this
footprint; Clatskanie PUD and EWEB are Oregon utilities inside the BPAT BA.

**(b) BPM 102 §4.1 (§2.2 above) lists "Douglas County PUD #1" as a component BA
of the Northwest Subregion**, i.e. `DOPD` **is** inside the WRAP Region even
though it carries no logo on the programme page. The two sources answer
different questions (programme membership vs. the BAAs whose load and generation
the LOLE study covers) and **this lane does not resolve which governs** — it is
flagged for the desk.

**"From when" is only partly answerable from public documents.** The joint
statement says the signatories have *"actively participated in WRAP since its
inception in 2019"*, and BPM 109 keys binding status to a WRAPA effective on
2026-09-15 — but **no public WPP document found in this session states a
per-participant accession date**, so that column is left empty rather than
inferred. The one dated, signed commitment list is
`WPP_Joint_WRAP_Statement_2025-09-29.pdf` (printed p. 2), whose **11
signatories** are: Arizona Public Service · Avista · Bonneville Power
Administration · Chelan Public Utility District · Clatskanie Public Utility
District · Northwestern Energy · Powerex · Puget Sound Energy · Salt River
Project · Tacoma Power · Tucson Electric Power. Its own p. 1 caveat: *"the
participants signing this statement represent only a portion of the utilities
committed to WRAP's long-term success."*

## 2.4 The forward showing requirement

`WPP_BPM_103_FS_Capacity_Requirements_V4.0_2026-03.pdf`, printed **p. 5**
(PDF p. 6), Equation 1:

```
FS Capacity Requirement            = FS Capacity Requirement Unadjusted
                                     + Contingency Reserve Adjustment
FS Capacity Requirement Unadjusted = (P50 Peak Load Forecast) x (1 + FSPRM)
Contingency Reserve Adjustment     = CR_Adj_Generation + CR_Adj_Load
```

Timing, from PacifiCorp's summary (2025 IRP Vol. 1, printed **p. 104**):
*"seven months prior to the start of a winter or summer season, [participants]
must submit a forward showing demonstrating they have resources and transmission
to cover their load and planning reserve margin requirements."*

Components, all BPM 103:

- **P50 Peak Load Forecast** (printed pp. 6–8): winter = the **median** of the
  last five winter seasons' maximum peaks for the three Seasonal Peak Months
  (Dec/Jan/Feb), and the median of the respective monthly values for November
  and March; summer = that median scaled by a **Load Forecast Ratio** (each
  month's five-year average peak ÷ the largest such average).
- **Load Growth Factor** (printed p. 9): *"The established growth rate is
  currently set at 1.1%."* A participant may request an alternative that moves
  its P50 peak by **≥ 5 %** in the highest-forecast month.
- **Contingency Reserve** (printed p. 9): the LOLE study assumes a proxy
  requirement of *"six percent (6%) of the Regional P50 Peak Load Forecast
  across the WRAP Region"*, while BAL-002-WECC-3 requires *"three percent (3%)
  of hourly integrated load and three percent (3%) of hourly integrated
  generation"* — the adjustment reconciles the two per participant.
- **Resource side** (BPM 102): each resource earns a monthly **Qualifying
  Capacity Contribution** — ELCC for VERs and storage, a NERC-GADS seasonal
  EFOF for thermal, capacity-critical-hour history for run-of-river hydro
  (NorthWestern 2026 MT IRP printed pp. 147–149 summarises the methodology).

**Published FSPRM values, by month.** BPM 102 defines the method but the numbers
come from each season's LOLE study. Two participants print them:

| Source | Season | Values |
|---|---|---|
| NorthWestern 2026 MT IRP, **Table 39**, printed **p. 150** — "2025 Summer FS total portfolio capacity" | Summer 2025 | June **26.2 %** · July **14.5 %** · August **16.1 %** · September **14.2 %** (against monthly loads 1,090 / 1,224 / 1,208 / 1,083 MW) |
| PacifiCorp 2025 IRP Vol. 1, printed **p. 131** | 2025 IRP | *"the 14.4 percent PRM for July and 16.8 percent PRM for December **adopted from WRAP** for the 2025 IRP"* |

These are the closest thing to a published `PLANNING_RESERVE_MARGIN_BY_ISO`
input the footprint has, and they are **monthly and subregional by
construction** — there is no single WRAP-wide PRM number to transcribe.

## 2.5 The holdback requirement

`WPP_BPM_204_Holdback_Requirement_V3.0_2026-03.pdf`. It is a **mechanism, not a
percentage** — there is no fixed holdback number to transcribe, and a lane
looking for one should stop here rather than keep searching.

Printed **p. 3** (PDF p. 4), verbatim: *"The Holdback Requirement is a MW
quantity, determined on the Preschedule Day, that a Participant is required to
be capable of converting into an Energy Deployment on a given hour of the
Operating Day."* Printed **p. 4**: *"…that a surplus Participant is required to
have availability for delivery as an Energy Deployment on a given hour of the
Operating Day."*

The chain, per BPM 204 §§3–6 (printed pp. 4–7):

1. **Preschedule Day**: each participant submits hourly forecasts of load, VER
   output, run-of-river output, contingency-reserve requirement and forced
   outage (BPM 202). The **Sharing Calculation** returns each participant
   surplus, deficient, or neither.
2. A **deficient** participant opts in, capped at its own negative Sharing
   Calculation result; failing to opt in forfeits any Energy Deployment.
3. **Voluntary Holdback** is allocated first (pro rata when over-offered), and
   once allocated is *"deemed to be a binding obligation"* exposed to Energy
   Delivery Failure Charges.
4. Any residual need is allocated to **surplus** participants pro rata: a
   Participant Sharing Ratio (its surplus ÷ the subregion's total surplus)
   multiplied by (requested Holdback Capacity − Voluntary Holdback). Allocation
   differs for a subregion with and without a **Central Hub**.

During **Non-Binding** seasons (BPM 109 printed p. 6, §4.1) participants are
*"not subject to Deficiency Charges under the FS Program, or to mandatory
Holdback Requirements as a result of a positive Sharing Calculation result,
mandatory Energy Deployments, or Delivery Failure Charges"* — which is the whole
reason §2.1's date decides whether WRAP is in-window at all.

---

# 3. Transmission — what a participant's own filing adds to §1

NorthWestern's 2026 Montana IRP §6.2 is the most useful transmission text found
in this intake, because it **independently restates four WECC path ratings and
then says what they are worth operationally**.

| Path | NorthWestern's statement, printed page | Rating |
|---|---|---|
| **8** Montana–Northwest | p. 119: *"Path 8 consists of two 500 kV lines, six 230 kV lines, and three 115 kV lines… The east-to-west (export) rating of Path 8 is 2200 MW."*; p. 120: *"The west-to-east (import) rating on Path 8 is 1350 MW, and the TTC varies by season based on loading in the Flathead Lake area."* | 2,200 / 1,350 — matches the catalogue |
| **18** Montana–Idaho | p. 120: *"The TTC and rating of Path 18 is 383 MW in the southbound (export) direction and 256 MW northbound (import)."* | 383 / 256 — matches |
| **80** Montana Southeast | p. 121: *"Path 80 is rated to 600 MW for both north-to-south (export) and south-to-north (import) flows. However, the transfer capacity on Path 80 is significantly lower due to transmission constraints in both Montana and Wyoming."* | 600 / 600 — matches |
| **83** MATL | p. 121: *"The path is rated at 325 MW southbound and 300 MW northbound."* | 325 / 300 |

**The rule-14 point, in the operator's own words** (printed **p. 122**, §6.2.4):

> *"The ATC is the transmission that is available for customers' use after
> considering existing rights and obligations… **ATC is much less than TTC** and
> can change from time to time. There is also competition for ATC from multiple
> types of transmission customers."*

and printed **p. 119**: *"NorthWestern does not own all the transmission
capacity shown on these paths. Since NorthWestern does not own all the
transmission capacity, the capacity is not necessarily available to NorthWestern
Supply to import energy onto the system… relying solely on imports is a risky
and expensive approach to addressing supply capacity shortages."*

The per-path ATC numbers are in **Figure 42**, which is an image and did not
transcribe (`SOURCES.md` §6). So a WECC path rating is a **TTC ceiling**, and
the model's `ttc_mw` on a link seeded from one is an upper bound that the real
market does not reach — worth saying on the first keeper rather than treating
the catalogue number as a delivered limit.

Two further NorthWestern facts a seam lane will want (printed p. 120):
the **Montana Intertie Agreement** with BPA governing Eastern Intertie rates and
capacity *"terminates September 30, 2027"*, extended by contract *"for a 5-year
term, with rollover rights, from October 1, 2027, to October 1, 2032"*; and
(printed p. 123) the 2023 Loss of Colstrip study *"assumed that Colstrip
capacity served 444 MW of designated load in Montana"* and concluded that
*"reliance on off-system imports to completely replace the energy in the BA
associated with Colstrip is not a reliable or realistic assumption."*

---

# 4. IRP values table — manifest row 9

One block per utility. **Planning reserve margin by season**, **peak-load
history**, **resource plan**, **announced coal exit dates** and **published
internal transfer limit**, each with printed page. Where the source does not
publish the item, the row says **not published** and stops.

## 4.1 PacifiCorp — 2025 IRP (filed 2025-03-31) + 2025 IRP Update (filed 2026-03-31)

Covers **both** `PACE` (card N5 `NWPP-EAST`) and `PACW` (`NWPP-OR`).

| Item | Value | Citation |
|---|---|---|
| **PRM, summer** | **14.4 %** (July) | Vol. 1, printed **p. 131**: *"the net system obligation calculated above multiplied by the 14.4 percent PRM for July and 16.8 percent PRM for December adopted from WRAP for the 2025 IRP"* |
| **PRM, winter** | **16.8 %** (December) | same |
| **Peak forecast** | **Table 6.1, Forecasted System Summer Coincident Peak Load, before EE (MW)**: 2025 **11,318** · 2026 11,270 · 2027 11,425 · 2028 11,553 · 2029 11,690 · 2030 11,844 · 2031 12,104 · 2032 12,193 · 2033 12,363 · 2034 12,575 · 2035 12,819 · 2036 13,134 · 2037 13,404 · 2038 13,693 · 2039 13,978 · 2040 14,279 · 2041 14,581 · 2042 15,008 · 2043 15,237 · 2044 **15,518** | Vol. 1, printed **p. 114**; the preceding sentence gives the *"compound annual growth rate (CAGR) of **1.67 percent** over the period 2025 through 2044"* |
| **Peak history** | **not published in Vol. 1** as a historical series (Table 6.1 is forecast-only) | — |
| **Resource plan** | Coal→gas conversion of **562 MW**; exit of PacifiCorp's share of **386 MW** of minority-owned coal; retirements of **220 MW at Dave Johnston** and **156 MW of Naughton** gas conversion by end of horizon; **Jim Bridger Units 3 and 4 convert to carbon capture in 2030, operate 12 years of tax-credit eligibility, retiring in 2043**; *"The balance of the coal units continues to operate through the end of the study horizon."* Near-term EE 610 MW and DR 83 MW, 2025–2028 | Vol. 1, printed **pp. 9–10** |
| **Coal exit dates** | Action plan, Vol. 1 printed **p. 13**: **Colstrip 3 & 4** — *"PacifiCorp will continue to work with co-owners to develop the most cost-effective path toward an exit from the Colstrip project in Montana by **2030**"*; **Craig Unit 1** — *"preferred portfolio target exit date of **December 31, 2025**"*; **Naughton Units 1 and 2** — *"continue the process of converting… to natural gas as initiated in Q2 2023… Natural gas operations are anticipated to commence **spring of 2026**"*, South Ash Pond closure initiated *"no later than the end of December 2025 when coal operations cease"* and completed *"by October 17, 2028"* | as cited |
| **Internal transfer limit** | **partial.** Vol. 1 printed p. 131 states the principle — *"the PacifiCorp system is planned for and dispatched on a system basis **up to the limits of the transfer capability between the two areas**"* — and Tables 6.14/6.15 carry a per-year **"Transfers"** line for the East area (2025 −274 MW, 2026 −1,440, 2027 −1,361, 2028 −1,096, 2029 −902, 2030 −631, 2031 −476, 2032 −421, 2033 −380, 2034 −277). **The East↔West transfer *capability* MW is not stated anywhere in Vol. 1's text**, and the bubble-to-bubble capabilities are in **Figure 8.3**, an image that does not transcribe | Vol. 1 printed pp. 131–132, 190 |
| **Modelled topology** | Figure 8.3 bubble names **do** transcribe: Central OR · Bridger · 4 Corners · Utah South · NUT · Goshen · Montana · Colorado · Palo Verde · Yakima · BorahPop · Walla Walla · Mona · Mid-C · Mead (Harry Allen) · McNary · Wyoming East · Trona · Chehalis · Willamette Valley/Central Coast · South OR/N. California · COB · Hemingway · BPA NITS · Wyoming Central · Clover · Portland/N. Coast · Wyoming North · Summer Lake · NOB · Longhorn · Wasatch Front | Vol. 1 printed **p. 190** |

Two caveats PacifiCorp states itself and which a consumer must carry: the
regional-haze **Jim Bridger Consent Decree** heat-input limits are modelled
(Idaho Power's account of the same instrument is §4.2); and *"PacifiCorp is
reevaluating the timing and needs analysis underlying **B2H** because of factors
such as changed native load growth and a lack of capacity available on
neighboring transmission systems"* (Vol. 1 printed p. 190).

The **2025 IRP Update** (filed 2026-03-31) is the newer vintage, but its load
forecast lives in **Figures 1.5/1.6 and Appendix A**, neither of which
transcribes, so the tabular peak series above remains the 2025 IRP's.

## 4.2 Idaho Power — 2025 IRP (June 2025)

| Item | Value | Citation |
|---|---|---|
| **PRM** | **Not published as a fixed percentage.** Printed p. 7 of App. D: *"the company uses the PRM and ELCC inputs to the Aurora LTCE model to calibrate with the RCAT"*, and p. 8: *"the company developed minimum seasonal PRM targets for the 20-year planning period"* — the seasonal values are a model-calibration output shown in a figure, not a published table. The binding reliability standard **is** published: *"Idaho Power plans to meet an LOLE threshold of **0.1 event-days per year**"* | App. D printed **pp. 7–8** |
| **Peak history** | **Summer record 3,793 MW, Monday 22 July 2024 at 7 p.m.** · **Winter record 2,719 MW, 16 January 2024 at 9 a.m.** | printed **pp. 88–89** |
| **Peak forecast (Table 8.2, MW)** | 10th / **50th** / 95th percentile — 2024 actual 3,793 · 2026 3,845/**3,934**/4,040 · 2027 4,130/**4,220**/4,326 · 2028 4,369/**4,458**/4,564 · 2029 4,569/**4,658**/4,764 · 2030 4,682/**4,772**/4,878 · 2031 4,859/**4,949**/5,054 · 2035 5,073/**5,162**/5,268 · 2040 5,255/**5,345**/5,451 · 2045 5,428/**5,517**/5,623. Growth 2026–2045 **1.8 %** | printed **p. 89** (full 20-year table) |
| **Energy forecast (Table 8.1, aMW)** | 2026 1,983/**2,102**/2,243 … 2045 3,124/**3,260**/3,426; growth 2026–2045 **2.3 %** (50th) | printed **p. 87** |
| **Resource plan (Table 1.1 preferred portfolio, MW)** | Coal exits **−134 (2026)**, **−350 (2030)**, subtotal **−484**; conversion gas 611; new gas 550; wind 700; solar 1,445; 4-hr storage 835; 100-hr storage 50; transmission **B2H (2028)** and **SWIP-N (2029)**; DR 20; EE 287 + 58. Total 4,071 MW, portfolio cost $10,965 M | printed **p. 5** |
| **Coal exits** | *"Conversion of **Valmy units 1 and 2** from coal to natural gas **by summer 2026**"* (listed under *"Actions Committed to before the 2025 IRP"*); *"Coordinate with PacifiCorp on the future of **Bridger units 3 & 4**"* — PacifiCorp's plan is CCS in 2030 operating *"as a coal plant through 2042 and then retire"*, Idaho Power's is a gas conversion; *"the companies will work together to determine the future"* | printed **pp. 5–7** |
| **Jim Bridger instrument** | *"On February 14, 2022, Wyoming and PacifiCorp filed a **Consent Decree in the Wyoming State District Court**, settling potential State compliance claims with the State Implementation Plan (SIP)… The Consent Decree required PacifiCorp to submit a new permit application and a proposed SIP revision within two months, reflecting heat input limits consistent with the **conversion of Bridger units 1 and 2 to natural gas generation by January 1, 2024**. In April 2022, PacifiCorp submitted the new permit application and proposed SIP revision… In 2024, the EPA partially approved and partially disapproved the proposed SIP revision. However, on May 1, 2025, EPA granted the company's request for reconsideration"* | printed **p. 17** |
| **Internal transfer limit** | **not published** in the main report's text | — |
| **Hydro basis** | *"Idaho Power continues the practice of using **50th-percentile future streamflow conditions for the Snake River Basin**"*, modelled in RiverWare (headwaters→Brownlee, then through the Hells Canyon Complex) plus **ESPAM v2.2**, over water years **1981–2018** adjusted to present conditions | printed **p. 90** |

## 4.3 Avista — 2025 Electric IRP (filed 2024-12-31)

| Item | Value | Citation |
|---|---|---|
| **PRM, summer** | **16 %**, May through September | printed **p. 82**; restated printed p. 4: *"Avista uses a 24% planning reserve margin above its expected monthly peak load in the winter and 16% in summer months to identify when it should acquire new capacity."* |
| **PRM, winter** | **24 %**, October through April | same |
| **Peak history** | *"By 2024, summer peak load was **8.8 % higher** and winter peak loads were **12.2 % higher** than 2014 actual peak load"* (peaks adjusted for demand curtailment) | printed **p. 4** |
| **Load growth** | Annual energy 2014→ flat at **0.09 %/yr**; 2026 loads **4.5 %** above 2023 (+50 aMW); 20-year average **0.91 %/yr**, last 10 years **1.4 %**; **summer peak +1.14 %/yr, winter peak +1.12 %/yr** over 20 years, last 10 years **1.7 %**. 2026 load forecast **1,165 aMW** against **1,569 aMW** normal-weather generating capability | printed **pp. 4–5** |
| **Resource plan / retirements** | *"Avista's **Colstrip ownership will end December 31, 2025**"*; **222 MW of Colstrip Units 3 & 4 transferred to NorthWestern Energy** at end-2025, replaced by hydro PPAs with **Chelan PUD** and **Columbia Basin Hydro** plus a **100 MW Clearwater Wind** PPA; first long-term short position **2030**, driven by the assumed retirement of the **66 MW Northeast CTs** in Spokane (*"Northeast's air permit expires December 31, 2032"*) | printed **pp. 4, 75, 76** |
| **Internal transfer limit** | **not published** | — |

## 4.4 NorthWestern Energy — 2026 Montana IRP (public version)

| Item | Value | Citation |
|---|---|---|
| **PRM** | **Takes WRAP's**, monthly, and picks the binding month: *"NorthWestern relies on the resource accreditations and PRMs that are used in the WRAP FS for long-term planning"*, and *"chooses the monthly PRM that results in the highest load plus PRM for a particular season."* **Table 39, 2025 Summer FS**: June **26.2 %** · July **14.5 %** · **August 16.1 %** (selected) · September **14.2 %**; monthly loads 1,090 / 1,224 / 1,208 / 1,083 MW; load+PRM 1,375 / 1,401 / **1,403** / 1,236 MW; portfolio QCC 1,519 / 1,423 / **1,404** / 1,427 MW | printed **pp. 147, 150** |
| **Other PRM figures printed** | Load-and-resource tables elsewhere in the IRP are labelled *"LF + 16.1 % PRM"*, *"LF + 20.9 % PRM"*, *"LF + 10.4 % PRM"* and *"LF + 19.9 % PRM"* — different seasons/cases of the same WRAP construct | printed pp. 155 ff. |
| **Peak history** | **partial** — Table 29 *"Peak Loads and Imports 2024"* (printed p. 116) and Figure 48 *"NorthWestern's historic summer and winter retail peak load shape"* (p. 139) are **images** and did not transcribe | — |
| **Resource plan** | Base Case *"assumes **Colstrip retires according to its project book life on December 31, 2042**, and includes NorthWestern's acquisition of **Avista's 222-megawatt (MW) Colstrip share starting on January 1, 2026**"*; the IRP also runs early-retirement scenarios (MATS, GHG, a 2035 retirement) and a sensitivity on Puget's 370 MW share | printed **p. 20** ("Base Case"), plus §§7.5, 7.7 |
| **Transfer limits** | §3 above — Paths 8, 18, 80, 83, plus the ATC-vs-TTC statement and the Montana Intertie Agreement dates | printed pp. 119–123 |

## 4.5 NV Energy — 2024 Joint IRP (filed 2024-05-31, PUCN Docket 24-05041)

A **joint** Nevada Power + Sierra Pacific filing in **29 volumes**; Volume 1 is
the transmittal letter and index, Volume 6 the load-forecast narrative and
technical appendix LF-1.

| Item | Value | Citation |
|---|---|---|
| **Planning period** | 2025–2044 (20-year), action plan 2025–2027, energy supply plan 2025–2027 | Vol. 1 printed p. 3 |
| **PRM** | **Not published as an NV Energy target.** Volume 6 discusses NERC's **Anticipated / Prospective Reserve Margin** definitions in the context of the NERC LTRA, not a company PRM | Vol. 6 printed **p. 25** |
| **Peak/energy forecast** | **partial — Table LF-1 "Annual Native Energy (GWh) and Peak (MW)" is an image and did not transcribe.** The narrative gives: 2025–2027 retail-energy CAGR **1.9 %** (Nevada Power 1.1 %, Sierra 3.3 %), energy **+2,059 GWh**, coincident-peak CAGR **0.9 %**, **system peak +226 MW**; 2025–2044 retail-energy CAGR **2.9 %** (NP 1.9 %, Sierra 4.4 %), energy **+27,164 GWh**, coincident-peak CAGR **2.2 %** (NP 1.4 %, Sierra 4.9 %), **system peak +4,811 MW** (NP +2,480, Sierra +2,381) | Vol. 6 printed **pp. 3–4** |
| **Large load** | *"these customers have requested approximately **7,600 MW** of capacity additions, with nearly 6,500 MW at Sierra and 1,180 MW at Nevada Power. **Twelve of these projects are bundled-service high load factor data centers requesting 5,900 MW of capacity by 2033.** Consistent with past practice, these requests are scaled down in the retail load forecast, but still incorporate **13,288 GWh** of load growth over the next 10 years"* — concentrated in the **Tahoe-Reno Industrial Center** (Sierra) and **Apex** (Nevada Power) | Vol. 6 printed **p. 3** |
| **Coal / Valmy** | **not found in the volumes landed.** North Valmy appears only as a docket reference in the Vol. 1 index (*"TRAN-2 IRPA4 – Valmy LSAP 2018"*) | — |
| **Diversity note** | *"the Companies' peak demands may be lower than the combined sum of the individual system peaks at Sierra and Nevada Power due to diversity between the two systems"* | Vol. 6 printed p. 3 |

## 4.6 Portland General Electric — 2023 CEP/IRP (revised 2023-06-30)

**PGE has no 2025 or 2026 IRP.** Its current filed and partially-acknowledged
plan is the 2023 Clean Energy Plan / Integrated Resource Plan.

| Item | Value | Citation |
|---|---|---|
| **PRM** | **The 10 % / 12.5 % / 15 % figures in Appendix G are NOT PGE's system PRM** and must not be transcribed as one. Printed **p. 499**: *"This analysis uses three planning margins, 10 percent, 12.5 percent, and 15 percent. The three margins set the high (10 percent), reference (12.5 percent), and low (15 percent) **market power assumption** cases."* They parameterise how much **Northwest market capacity** PGE may count on, not its own reserve requirement. PGE's own requirement is stated as WRAP-derived (printed **p. 64**: *"The program will calculate the required planning reserve margin (PRM) to meet the LOLE target for each month of the binding seasons."*) | printed **pp. 499, 501** |
| **Market capacity result** | Reference-case heavy-load-hour market availability: **summer 0 MW in every year**; winter **200 MW** 2023–2025, **150 MW** 2026–2030. High case winter 300 → 250 MW; low case 150 → 50 MW. PGE's share of any Northwest surplus is *"the ratio of PGE's peak load to the Northwest region's peak load – **roughly 10 percent**"* | printed **pp. 500–501** |
| **Peak** | *"a 200 MW reduction in capacity need represents 5 percent of PGE's **peak load of approximately 4,000 MW**"* (footnote 315); PGE became summer-peaking — *"system load broke prior records on four days, making PGE a summer peaking utility"*. **Table 104 "Peak load forecast by Need Future and season, MW" (printed p. 469) did not transcribe** | printed **p. 284** (footnote 315); Table 104 at printed p. 469 |
| **Coal** | **Boardman closed 2020** — *"In 2020, PGE ceased operations at Oregon's last coal-fired plant"*; remaining coal is *"our ownership share of units 3 and 4 of the Colstrip plant in Montana"* | printed **p. 18** |

## 4.7 Puget Sound Energy — 2023 Electric Progress Report (filed 2023-03-31)

**PSE has no 2025 electric IRP.** Washington's 2024 legislation replaced the
separate gas and electric IRPs with a single **Integrated System Plan**, PSE's
first due **2027**; the 2023 Electric Progress Report (an update to the 2021
IRP) is the most recent filed electric plan. Two chapters are landed here.

| Item | Value | Citation |
|---|---|---|
| **Reliability standard** | *"We apply a **five percent loss of load probability** metric in the resource adequacy study, which means we plan our system to have an expected loss of load event occur **once in 20 years**."* | Ch. 7 printed **p. 7.3** |
| **PRM by season (Table 7.1)** | 2027 Winter (2021 IRP) **20.7 %** · 2031 Winter (2021 IRP) **24.2 %** · **2029 Winter 23.8 %** · **2029 Summer 21.2 %** · **2034 Winter 23.9 %** · **2034 Summer 26.1 %**. Additional perfect capacity need (MW): 907 · 1,381 · 1,272 · 1,875 · 1,746 · 2,856 | Ch. 7 printed **p. 7.3** |
| **Seasonality** | *"although PSE is a **winter-peaking utility**, the additional perfect capacity need is higher in summer. This high summer need means there are fewer resources available in the summer than in the winter, not that the summer peak is higher than the winter peak."* First report to model the PRM for winter **and** summer | Ch. 7 printed **pp. 7.3–7.4** |
| **Energy forecast** | *"grow at an average annual growth rate (AARG) of **1.8 percent** from 2024 to 2045… from **2,551 aMW in 2024 to 3,699 aMW in 2045**"* | Ch. 6 printed **p. 6.1** |
| **Peak forecast** | *"base peak demand before additional DSR to increase at a **1.7 percent** annual growth rate, from **4,753 MW in 2024 to 6,717 MW in 2045**"* | Ch. 6 printed **p. 6.1** |
| **Peak definition** | *"The peak demand forecast uses a **1-in-2 seasonal peak minimum or maximum temperature** during all peak hours."* Forecasts include climate change: *"Warming temperatures decrease energy usage in the winter and increase it in the summer."* | Ch. 6 printed **pp. 6.7, 6.1** |
| **Coal** | not covered in the two chapters landed | — |

---

# 5. What is NOT here

| Item | Status | Why |
|---|---|---|
| NWPP-NW ↔ NWPP-OR path rating | **does not exist** | §1.4 — a finding, not a block |
| PacifiCorp East↔West transfer capability MW | **partial** | stated as a concept, never as a number, in Vol. 1 text; Figure 8.3 is an image |
| PacifiCorp coal/gas unit end dates (Tables 1.2, 6.2, 6.3) | **partial** | image tables; the narrative equivalents are transcribed in §4.1 |
| NorthWestern per-path ATC (Figure 42), peak-load table (Table 29) | **partial** | image tables |
| NV Energy Table LF-1 annual energy and peak | **partial** | image table; narrative CAGRs transcribed in §4.5 |
| PGE Table 104 peak load forecast | **partial** | image table |
| Per-participant WRAP accession dates | **not published** | §2.3 |
| A single WRAP-wide PRM number | **does not exist** | §2.4 — FSPRMs are monthly and per subregion by construction |
| Idaho Power seasonal PRM percentages | **not published** | §4.2 — a model-calibration output shown in a figure |

Nothing in the "partial" rows is blocked by a host: every document is public and
reachable (`SOURCES.md`), and every one is a **table rendered as an image**. A
follow-up that needs those cells should plan on an image-extraction route (or a
hand transcription), not another fetch.

---

## Related directories

- `data/raw/nuclear-license-status/nwpp.csv` — Columbia Generating Station, from
  the NRC pages cited in `SOURCES.md` §4.
- `data/raw/load-forecast/nwpp/` — the footprint LTLF assembled from §4 above,
  with the assembly documented in that directory's `SOURCES.md`.
- `data/raw/gas-prices/SOURCES_nwpp_gas.md`,
  `data/raw/coal-prices/SOURCES_nwpp_coal.md` — the per-zone fuel basis.
