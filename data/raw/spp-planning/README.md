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
