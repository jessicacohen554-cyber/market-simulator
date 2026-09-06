# `spp-planning` — SPP planning & market-design source documents

Opened **2026-09-06** by lane **SPP-12** (`docs/multi-iso/spp-addition-plan-2026-09.md`
§5 row SPP-12, manifest rows 10–13). Every document here was fetched that day from
`www.spp.org`, which is **fully reachable** — unlike `portal.spp.org`, whose data
products are blocked (see any `data/raw/spp-*/SOURCES.md`).

Exact URLs: `SOURCES.md`. Checksums of every fetched artifact, tracked or not:
`SHA256SUMS.txt`.

## What is and is not tracked

| Artifact | Size | Tracked? |
|---|---|---|
| `SPP_Planning_Criteria_v5.0A.pdf` | 1.7 MB | **yes** |
| `spp-system-interfaces-stakeholder-reference-guide.pdf` | 0.7 MB | **yes** |
| `Long_Term_PRM_Policy_Paper.pdf` | 0.17 MB | **yes** |
| 2025 ITP Assessment Report | 14.3 MB | no — `transcriptions/2025_ITP_Report_v1.0.txt` |
| ASOM 2023 / 2024 / 2025 | 6.2 / 6.4 / 6.1 MB | no — `transcriptions/ASOM_*.txt` |
| Integrated Marketplace Protocols 119 | 8.3 MB zip | no — `transcriptions/Integrated_Marketplace_Protocols_119.txt` |

The four untracked payloads follow the repo's **corpus conversion** convention
(`docs/bloat-removal-plan-2026-08.md` §4, and the same delete-not-archive
discipline CLAUDE.md states for superseded per-run scripts): the bulk payload
stays out of the tree, the `README` + `SHA256SUMS.txt` + a full text
transcription stay in it, and **re-fetch is the recovery route** — every URL in
`SOURCES.md` was verified working on 2026-09-06. The lane's own charter allows
this: it asks for "PDFs **or** page-cited transcriptions".

`transcriptions/*.txt` are `pdfminer.six` `extract_text` output, unedited. Page
breaks are `\x0c`, so the *n*-th form-feed-delimited chunk is PDF page *n*; every
citation below gives the **printed** page (the two coincide in the Protocols and
differ by a front-matter offset in the ITP and ASOM PDFs, so both are given where
they differ).

---

## Transcribed values — the reason this directory exists

Everything below is quoted from the documents in this directory. **No value here
came from memory.** Two of them contradict assumptions carried in the SPP
addition plan; those are flagged and are the SPP-10 / owner-card corrections.

### 1. Planning Reserve Margin — manifest row 12

`SPP_Planning_Criteria_v5.0A.pdf`, §4 "Planning Reserve Margin", printed **p. 10**
(pdf page 11). SPP East and SPP West BAAs each carry a **separate Base PRM**, and
the criteria state them per season per year, not as one standing number:

| BAA | Season | Year | Base PRM |
|---|---|---|---|
| East | Summer | 2026 | **16 %** |
| East | Summer | 2027 | **16 %** |
| East | Summer | 2028 | **16 %** |
| East | Summer | 2029 | **17 %** |
| East | Winter | 2026/2027 | **36 %** |
| East | Winter | 2027/2028 | **36 %** |
| East | Winter | 2028/2029 | **36 %** |
| East | Winter | 2029/2030 | **38 %** |
| West | Summer | 2027 | **19 %** |
| West | Winter | 2027/2028 | **40 %** |

Verbatim: *"The SPP East BAA Base PRM shall be sixteen percent (16%) for the 2026,
2027, and 2028 Summer Season and thirty six percent (36%) for the 2026/2027,
2027/2028, and 2028/2029 Winter Season. Beginning in the Summer Season of 2029,
the SPP East BAA Base PRM shall be seventeen percent (17%) for the 2029 Summer
Season and thirty eight percent (38%) for the 2029/2030 Winter Season. The SPP
West BAA Base PRM shall be nineteen percent (19%) for the 2027 Summer Season and
forty percent (40%) for the 2027/2028 Winter Season."*

> **CORRECTION — plan §6 row 12.** The plan records the value to look up as
> *"PRM (15 % since PY2023; winter PRM from 2026)"*. The current criteria say
> **16 %** summer for 2026–2028 (17 % from 2029) and a **36–38 % winter** PRM for
> East. The winter half of the plan's note is right in kind; the 15 % is not the
> live number. SPP-10's values table and any `PLANNING_RESERVE_MARGIN_BY_ISO`
> entry take the table above, and the model zone(s) card P1 registers must be
> mapped to **East vs West BAA** before a single PRM is applied — SPP does not
> have one system-wide PRM. The SPP RTO footprint this program models is the
> **East** BAA; the West BAA is the WEIS/Western area.

Base PRM is set against a probabilistic **LOLE** study, run separately for each
BAA, over Accredited Capacity of wind/solar/storage plus demonstrated net
capability of conventional resources. Background on the policy's direction:
`Long_Term_PRM_Policy_Paper.pdf`.

### 2. Offer caps and floors — manifest row 12

`transcriptions/Integrated_Marketplace_Protocols_119.txt`, §8.2.5 "Offer Caps and
Floors", printed **pp. 356–357** (Version 119, effective 7/17/2026):

| # | Parameter | Value |
|---|---|---|
| (1) | **Safety-Net Energy Offer Cap** | **$1,000/MWh** |
| (2) | Virtual Energy Offer Cap | $2,000/MWh |
| (3) | Import/Export Transaction Offer Cap | $2,000/MWh |
| (4) | Regulation-Up Service Offer Cap | $500/MW |
| (5) | Regulation-Down Service Offer Cap | $500/MW |
| (6) | Contingency Reserve Offer Cap | $100/MW |
| (7) | Energy Offer Floor | −$500/MWh |
| (8) | Regulation-Up Service Offer Floor | −$500/MW |
| (9) | Regulation-Down Service Offer Floor | −$500/MW |
| (10) | Regulation-Up Mileage Offer Floor | $0 |
| (11) | Regulation-Down Mileage Offer Floor | $0 |
| (12) | Contingency Reserve Offer Floor | −$100/MW |
| (13) | Start-Up Offer Floor | $0.0 |
| (14) | No-Load Offer Floor | $0.0 |
| (15) | Uncertainty Reserve Offer Cap | $1,000/MW |
| (16) | Uncertainty Reserve Offer Floor | $0/MW |

An offer above the safety-net cap is not forbidden — it is **cost-verified**.
Printed p. 344: *"Market Participants that have Resources with short-run marginal
costs greater than the Safety-Net Energy Offer Cap … may submit an Energy Offer
Curve using the same guidelines for development of the Resource's Mitigated
Energy Offer Curve … The Energy Offer Curve above $1,000/MWh must be equal to the
Mitigated…"* — i.e. the FERC Order 831 shape: a $1,000 soft cap with verified
incremental cost above it.

> **CORRECTION — plan §3 card P5.** The card proposes `voll=2000.0` and cites it
> as the "FERC 831 offer cap". SPP's **physical energy** offer cap is
> **$1,000/MWh**; the $2,000 caps in §8.2.5 apply to **virtual** bids/offers and
> to **import/export transactions**, neither of which is a dispatchable resource
> offer. The $2,000 figure is Order 831's *hard* cap on cost-verified offers, not
> SPP's posted cap. The card is the owner's to rule; this is the measured input it
> should be ruled against.

### 3. Violation Relaxation Limits (VRL) — manifest row 12

Same document, §4.1.4 + **Exhibit 4-1 "VRL Values"**, printed **pp. 70–72**. These
are SPP's constraint-relaxation price steps — the object that sets its scarcity
ceiling, and the SPP analogue of an ORDC/penalty stack:

| # | Constraint type | VRL |
|---|---|---|
| (1) | Resource Capacity | **$100,000/MW** |
| (2) | Global Power Balance | **$50,000/MW** |
| (3) | Resource Ramp | **$5,000/MW** |
| (4a) | Operating Constraint, **not** M2M-coordinated | **$1,500/MW** at each loading band: >100–101 %, >101–102 %, >102–103 %, >103–104 %, and >104 % |
| (4b) | Operating Constraint, M2M-coordinated | MISO's Shadow Price, per §3.1 of the SPP-MISO JOA |
| (5) | Spinning Reserve Constraint | **$250/MW** |

Verbatim on the ordering: *"A higher VRL value is an indication of the relative
priority for enforcing the constraint type. For example, the VRL value assigned to
a ramp rate limit exceeds that assigned to a flowgate limit indicating that the
flowgate constraint should be relaxed before the ramp rate constraint."*

Note (4a): every loading band carries the **same** $1,500 — the transcription is
not truncated, the steps genuinely do not escalate in this version. And (4b) is
why SPP's congestion ceiling on M2M flowgates is *MISO's* shadow price, which is a
real cross-seam coupling any SPP congestion work has to respect.

Card **P5** asks whether to seed SPP scarcity like NEISO. The plan's own reasoning
— that SPP scarcity is VRL/reserve-shortage-driven rather than a winter-gas
overlay — is confirmed by the table above: the binding ceiling in an SPP
shortage is the **$250/MW spinning-reserve VRL** and the **$50,000/MW global
power balance** VRL, not a fuel-cost overlay.

### 4. SPP coincident peak load by model year — manifest row 13

`transcriptions/2025_ITP_Report_v1.0.txt`, Figure 2.1 "Coincident Peak Load by
Model Year", printed **p. 43** (pdf page 43). This is the peak series curated into
`data/raw/load-forecast/spp/spp.csv`; see that directory's `SOURCES.md` for the
chart-read caveat, which is material and is not repeated here.

| Study year | Coincident peak |
|---|---|
| 2026 | 61.7 GW |
| 2029 | 66.5 GW |
| 2034 | 69.8 GW |
| 2044 | 76.4 GW |

### 5. N↔S transfer capability and SPS tie ratings — manifest row 11, **NOT FOUND**

> **SWEPT 2026-09-06 by lane SPP-13 — see §7 below.** All four candidates named at the end of
> this section were fetched and read; none is public. Nothing in this section was changed.

The plan expects the ITP report to carry a transfer-capability table to transcribe
(`_spp_config`'s N↔S TTC, and the SPS tie ratings). **The 2025 ITP Assessment
Report does not contain one.** It is a project-portfolio document — needs,
projects, costs, staging, benefit-cost — and its SPS content (§4.6 "Southwestern
Public Services (SPS) Area Additional Considerations" p. 120, §7.3.9 "SPS" p. 202,
Table 7.1 "SPS Projects" p. 204) is a project list, not a rated interface. A
regex sweep for transfer-capability MW ratings over all 300+ pages returns only
one hit, and it is about *generator* transfer capability as a siting-rank
criterion (p. 52).

So manifest row 11 is **still open** and stays a manual-manifest row. It is not
blocked by a host — `www.spp.org` is fully reachable — it is blocked by not yet
knowing which SPP document carries the number. Candidates a follow-up should try,
in order: the **ITP Manual v3.3**
(`/Documents/77209/ITP Manual Version 3.3.pdf`), which defines the assessment's
transfer-analysis methodology and may name the studied interfaces; the
**20-Year Assessment Report / Manual** (`/Documents/69814/`, `/Documents/59716/`);
and the ITP Postings folder (`/spp-documents-filings/?id=31491`). Until one lands,
rule 14 `[R-ACCURATE]` governs: a reconciled estimate may be used **only** with
the misalignment documented in place, and the real value opened as a root-cause
item — never buried in a guess.

---

## Related directories

- `data/raw/spp-hsl/` — the wind-curtailment series transcribed out of the three
  ASOM editions here.
- `data/raw/load-forecast/spp/` — the peak series from §4 above, in the curated
  `load-forecast` datatype shape.
- `data/raw/spp-{hourly-load,genmix,binding-constraints,or-mcp}/` — the blocked
  `portal.spp.org` products.

---

## Appended 2026-09-06 by lane SPP-13 — the FTP route (rows 5–9) and the row-11 sweep

Charter: `docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-13 (card **P11**).
FINDING: `docs/handoffs/FINDING-spp-13-2026-09-06.md`. URLs and checksums: `SOURCES.md`,
`SHA256SUMS.txt`. Transcriptions added here are **`pypdf` `extract_text`** output (page
markers `=====PDFPAGE n=====`), not `pdfminer` as the earlier ones — `pdfminer` would not
import in the session; the docx text is `word/document.xml` with tags stripped, one paragraph
per line. All unedited.

### 6. The FTP public-data route — DOCUMENTED, ANONYMOUS, and blocked only by this session's egress

`SPP_Public_Data_Access_20230707.pdf` (v3.0, July 2023), printed p. 2, verbatim:
*"Programmatic (API) access to public data is via FTP."* — Production
**`ftp://pubftp.spp.org`**, Member Test `ftp://pubftp-mte.itespp.org`.

`SPP_Markets_Public_Data_Guide_v35.docx`, "FTP Site Access" (p. 11), verbatim: *"User:
anonymous · Password: <use an email address>"*. **No Marketplace credential is required for
the FTP route** — the `X-SPP-UI-Token` that blocks `portal.spp.org` (SPP-12 §2) is a property
of the web UI, not of the data.

| Product | FTP folder (PRD) | File grammar (guide pp. 12–22) |
|---|---|---|
| RTBM LMP by settlement location | `ftp://pubftp.spp.org/Markets/RTBM/LMP_By_SETTLEMENT_LOC/` | `RTBM-LMP-SL-YYYYMMDDHHMM.csv` (5-min) · `RTBM-LMP-DAILY-SL-YYYYMMDD.csv` · **`RTBM-LMP-MONTHLY-SL-YYYYMM.csv`** · `YYYY-RTBM-LMP-SL-ANNUAL-ROLLUP.csv` (zipped) |
| DA LMP by settlement location | `ftp://pubftp.spp.org/Markets/DA/LMP_By_SETTLEMENT_LOC/` | `DA-LMP-SL-YYYYMMDDHHMM.csv` · **`DA-LMP-Monthly-SL-YYYYMM.csv`** |
| RTBM binding constraints | `ftp://pubftp.spp.org/Markets/RTBM/BINDING_CONSTRAINTS/` | `RTBM-BC-YYYYMMDDHHMM.csv` (5-min) · `RTBM-DAILY-BC-YYYYMMDD.csv` · monthly/yearly rollups per the DA grammar |
| DA binding constraints | `ftp://pubftp.spp.org/Markets/DA/BINDING_CONSTRAINTS/` | `DA-BC-YYYYMMDDHHMM.csv` · `DA-BC-MONTHLY-YYYYMM.csv` · `DA-BC-YEARLY-YYYY.zip`; `By_Day/` under each month |
| DA congestion $ by constraint | `ftp://pubftp.spp.org/Markets/DA/Congestion-Constraint` | `CONGESTION-CONSTRAINT-YYYYMM.csv` (monthly) |
| Hourly load by area | `ftp://pubftp.spp.org/Operational_Data/HourlyLoad/` | `DAILY_HOURLY_LOAD-YYYYMMDD.csv` (deleted after roll-up) · **`HOURLY_LOAD-YYYYMM.csv`** |
| Peak load by month | `ftp://pubftp.spp.org/Operational_Data/Peak_Load/` | `Peak_Load_by_Month.csv` (replaced monthly) |
| Generation mix historical | `ftp://pubftp.spp.org/Operational_Data/GEN_MIX/` | `GenMix_YYYY_SPP.csv` · `GenMixYTD_SPP.csv` · `GenMix365_SPP.csv` · `GenMix2Hour_SPP.csv` (+ `_SWPW`) |
| DA MCP | `ftp://pubftp.spp.org/Markets/DA/MCP/` | `DA-MCP-YYYYMMDDHHMM.csv` (daily, hourly rows) |
| RTBM MCP | `ftp://pubftp.spp.org/Markets/RTBM/MCP/` | `RTBM-MCP-YYYYMMDDHHMM.csv` (5-min) · `RTBM-MCP-DAILY-YYYYMMDD.csv` · `RTBM_MCP_YYYY.csv` (zipped) |
| VER curtailment (5-min) | `ftp://pubftp.spp.org/Operational_Data/VER_Curtailment/` | `VER-Curtailments-YYYYMMDD.csv` |
| Historical tie flow | `ftp://pubftp.spp.org/Operational_Data/TIE_FLOW_HISTORICAL` | `TieFlows_<MON><YEAR>-SPP.csv` (monthly, 1-min) |
| Permanent / temporary flowgates | `ftp://pubftp.spp.org/Operational_Data/Flowgates/Permanent%20Flowgates/` (…`Temporary Flowgates/`, `Archived Temporary Flowgates/`) | `Flowgates.csv` · `Temp_Flowgate.csv` · `Temp_Flowgate_Archive.csv` |

Guide p. 8 (the "Data Locations Summary" head-note), verbatim: *"Public Data files will be zipped (.zip) after 2 years."* — so the
2023 monthly files are inside a yearly zip, exactly as the portal route already assumed
(`scripts/data/build_spp_lmp_reference.py` docstring).

**Probed 2026-09-06 from this session — the route is transport-blocked here, not refused by
SPP.** The session's egress is an HTTPS `CONNECT` relay; a `CONNECT pubftp.spp.org:21` tunnel
opens (`200 Connection Established`) but **no FTP banner ever arrives** and the relay closes
the tunnel after ~36 s with 0 bytes sent / 0 payload bytes received. The discriminating
control: `CONNECT ftp.gnu.org:21` and `CONNECT ftp.debian.org:21` — two known-live anonymous
FTP servers that greet on connect — behave identically (no banner within 20 s). Ports 443 and
990 on `pubftp.spp.org` reset immediately after the TLS ClientHello; plain `http://` returns
the relay's own `503 upstream connect error`; the `WebFetch` tool answers *"Unsupported
protocol ftp:"*. Conclusion: **the egress relays TLS-on-443 only; FTP (server-speaks-first,
plaintext, port 21) cannot traverse it from any session with this network policy.** No
credential is missing. Full probe log: FINDING §1.

**What that means for the builder.** `scripts/data/build_spp_lmp_reference.py` was NOT
edited: the charter allowed an FTP transport only if the route worked from here, and it does
not. The exact FTP paths the flag would use are the first two rows of the table above; the
monthly-SL grammar is identical to the portal's (`{DA-LMP-Monthly,RTBM-LMP-MONTHLY}-SL-YYYYMM.csv`),
so the parse step is unchanged.

### 7. Row 11 — N↔S transfer capability and SPS tie ratings: SWEPT, NOT PUBLIC

All four candidates SPP-12 §5 named were fetched and read in the charter's order. **None
states an N↔S MW figure or an SPS tie MW rating.** Per document:

1. **ITP Manual v3.3** (76 pp., `ITP_Manual_v3.3.pdf`). A methodology manual. Its §2.2.3
   "Constraint Assessment" (printed p. 25) defines how the constraint list is built for the
   economic model, and §4 defines a flowgate's congestion score (footnote 27, printed p. 30:
   *"The shadow price represents the potential reduction in total SPP production costs if the
   limit on a congested flowgate could be increased by 1 MW"*); it names no interface and
   states no rating. FCITC appears only as the generator-outlet-facility screen
   (§2.2.2.3, printed p. 24).
2. **2022 20-Year Assessment Report v1.0** (102 pp., text only — 5.3 MB payload not tracked).
   A project-portfolio report. North–south flow is discussed **qualitatively** — e.g. §5.3.9
   *Potter County Interchange–Tolk Station 345 kV*, printed p. 84: *"the north-south flow from
   this area into southern/central Texas becomes disrupted"* — with no transfer-capability
   MW anywhere in the document. Its only "transfer capability" usage is the siting-rank ratio
   (printed p. 33: *"sited at the top 15% ranked sites in the region by ratio of transfer
   capability"*), the same object SPP-12 found in the 2025 ITP report.
3. **20-Year Assessment Manual** (17 pp., `20_Year_Assessment_Manual.pdf`). Printed p. 12,
   verbatim: *"Unless other information is available, each constraint's rating will be
   selected based upon the applicable Rating A (normal rating) or Rating B (emergency rating)
   in the power flow model."* — i.e. ratings live in the (CEII) powerflow model, not in the
   manual. DC ties are §"DC Ties and Lines" (printed p. 10), no MW.
4. **ITP Postings folder** (`?id=31491`, 781 documents). Swept by title for transfer /
   interface / tie / rating / constraint / SPS / manual. The only hits are the per-cycle
   **Constraint Assessment** transmittals (2015–2026). The two current ones were fetched:
   - *2025 ITP Constraint Assessment Final Posting for Approval* (12-02-2024), p. 1: the
     approved list includes *"4) Interfaces and Nomograms"* and *"Ratings for the
     **MHEB_SPC_W, MHEX_S, SPPSPSTIES, and SPSNMTIES** and select monitored elements have
     been relaxed to allow for the event files to reasonably simulate congestion"*. **This is
     the first public naming of the SPS tie interfaces as ITP-modelled objects**
     (`SPPSPSTIES` = SPP↔SPS ties; `SPSNMTIES` = SPS↔New Mexico ties). The ratings
     themselves are in `2025 ITP Constraint Assessment Recommendation.xlsx`, posted to
     **GlobalScape → ITP → NCD (CEII, RSD) → NDA**, marked *"CONTAINS CONFIDENTIAL AND
     PROTECTED MATERIAL … DO NOT RELEASE"*.
   - *2026 ITP Constraint Assessment Posting (East Interconnection)* (02-04-2026): same
     structure (`2026 ITP Constraint Assessment_02042026.xlsx`, same GlobalScape path,
     NDA-gated).

**Verdict for card P11 / SPP-20:** the N↔S transfer capability and the SPS tie ratings are
**not public on `www.spp.org`** — they exist as rows of an NDA/CEII workbook. Rule 14
`[R-ACCURATE]` therefore governs exactly as SPP-12 §5 said: SPP-20 registers a **Tier-3
reconciled estimate with the misalignment documented in place**, and the real value stays an
open root-cause item. Two things this sweep adds for that estimate: the interface names to
cite (`SPPSPSTIES`, `SPSNMTIES`), and the fact that the measured substitute — the RTBM
binding-constraint archive's `Real Time Effective Limit` column per flowgate (schema in
`../spp-binding-constraints/README.md`) — is public on the FTP route and is the SPP-53 input.
