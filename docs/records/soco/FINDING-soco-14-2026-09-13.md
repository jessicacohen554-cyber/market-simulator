# FINDING — SOCO-14: BA membership of FERC-714 respondents 107, 210, 186

**Lane:** SOCO-14 · **Date:** 2026-09-13 · **Branch:** `claude/soco-14-ba-membership-038erj`
(cut at pinned `33a7c961`) · **Profile:** `shared` · **Charter:**
`docs/multi-iso/soco-addition-plan-2026-09.md` §3 card S3, §5 row SOCO-14, §7 gate **G22** ·
**Premise:** `docs/handoffs/FINDING-soco-11-2026-09-13.md` §3.

This lane FINDS AND CITES. It derived no share, wrote no parquet, ran no solve, and decided
nothing (rules 23 `[R-FROZEN-DERIVE]`, 13 `[R-MEASURED]`).

## 0. VERDICT — three respondents, reported separately

| respondent | inside SOCO BA? | citation | what the citation actually supports |
|---|---|---|---|
| **107 Oglethorpe Power** | **YES** | NERC/SERC public compliance audit report **NCR01248**, Executive Summary **p. 3** — *"The Reliability Coordinator (RC), **Balancing Authority (BA)**, and Transmission Operator for GSOC is **Southern Company Services, Inc. – Transmission**."* | Oglethorpe's resources and its 38 member EMCs' load are scheduled and dispatched by **GSOC**, which is the registered **LSE/TOP** and whose **BA is SCS-Trans** — EIA BA code **`SOCO`**, BA ID 18195. That is exactly the load respondent 107's planning-area series measures. Currency and the load side are carried by Oglethorpe's own FY2024/FY2025 10-K (Control Area Compact with Georgia Power) and by EIA-861 2024 (37 of 38 members coded `BA = SOCO`). |
| **210 MEAG Power** | **YES** | MEAG Power **Annual Information Statement FY2024**, dated **2025-05-22**, printed **pp. 25–26** — *"…to maintain the integrity of the ITS and **the Southern Company Balancing Authority Area**…"*; *"MEAG Power controls the other non-nuclear resources in **the Balancing Authority Area of The Southern Company**…"*; and the counterfactual *"…upon the termination of the PSSA, to form or become part of **another balancing authority area**…"* | MEAG's own continuing-disclosure document places **MEAG's Territorial Load** inside the Southern Company Balancing Authority Area, and names Georgia Power as the supplier of the Control Area (BA) services that deliver it. This is the load claim, in MEAG's own words, not an inference. Corroborated by EIA-861 2024 (48 of 49 Participants coded `BA = SOCO`). |
| **186 Southern Power** | **NO — NOT ESTABLISHED** | **none found** | Nothing located identifies where respondent 186's FERC-714 **planning-area load** sits. The two documents that come closest support a *different* claim: the **IIC** (Southern Co 10-K Exhibits 10(b)1 / 10(e)1) makes Southern Power a party to the Southern electric system's central-dispatch contract, and **EIA-860** shows **11 of its 53 plants** in SOCO — i.e. *part of its generating fleet is in the footprint*, which is **not** the load claim. See §3. |

### GATE G22

> **G22 = FAIL.** Two of three respondents are cited; **Southern Power (186) is a documented NO**,
> so the six-respondent premise under card S3 is not fully sourced and the card returns to the owner.

That is the designed behaviour, not a lane failure. Scope of the gap, stated so the desk can size
it: 186 is **3.211 / 3.401 / 3.084 TWh** in 2023/2024/2025 — **1.3–1.4 %** of the BA's metered
demand — and the **five**-respondent sum (3 OpCos + 107 + 210) *is* fully cited, closing SOCO-11's
residual to **3.03 / 2.92 / 1.26 %**. The desk decides what follows; this lane does not.

---

## 1. Oglethorpe (107) — the chain, each link cited

| # | link | source | URL |
|---|---|---|---|
| 1 | Oglethorpe's resources are scheduled and dispatched by **GSOC**, and Oglethorpe purchases from GSOC the services GSOC buys from Georgia Power **under the Control Area Compact**, which Oglethorpe co-signed | Oglethorpe Power Corp **FY2024 Form 10-K** (filed 2025-03-31), Item 1, *"OGLETHORPE POWER CORPORATION – Relationship with Georgia System Operations Corporation"* and *"…Members' Relationship with Georgia Transmission and Georgia System Operations"* (printed p. 13). Identical text in the **FY2025 10-K** (filed 2026-03-27) — so the arrangement is current | `https://www.sec.gov/Archives/edgar/data/788816/000162828025015552/opc-20241231.htm` · `https://www.sec.gov/Archives/edgar/data/788816/000078881626000009/opc-20251231.htm` |
| 2 | **GSOC's Balancing Authority is Southern Company Services, Inc. – Transmission**; GSOC itself is registered only as **LSE** and **TOP** | NERC / SERC **public compliance audit report, NCR01248 Georgia System Operations Corporation**, report dated 2014-08-07, Executive Summary **p. 3** | `https://www.nerc.com/pa/comp/Audit%20Repots%20DL/2014_Public_SERC_GSOC-OP.pdf` |
| 3 | **SCS-Trans** is registered for the BA function and *"performs the RC, BA, TOP and TP functions for APC, GPC and MPC"* | NERC / SERC public compliance audit report **NCR01166 / 01247 / 01273 / 01320** (Alabama Power, Georgia Power, Mississippi Power, SCS-Trans), report dated 2021-11-30, Executive Summary **p. 3** | `https://www.nerc.com/globalassets/our-work/reports/regional-audit-reports-of-registered-entities/serc/2022/ncr01166_01247_01273_01320_southern_serc_pub_2021_op-rev1-11-2022.pdf` |
| 4 | **SCS-Trans is EIA BA code `SOCO`**, BA ID **18195**, covering AL / FL / GA / MS — and it is the **only** BA in EIA's own 2024 BA registry serving the Georgia footprint besides TVA, DUK, SCEG and SEPA | EIA-861 2024 final, `Balancing_Authority_2024.xlsx`, sheet *Balancing Authority* | `https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip` |
| 5 | **37 of Oglethorpe's 38 member EMCs carry `BA Code = SOCO`** in EIA-861 2024 (the 38th, Three Notch EMC, reads `SEPA`) | EIA-861 2024, `Sales_Ult_Cust_2024.xlsx` sheet *States* (32 members) + `Short_Form_2024.xlsx` sheet *861S* (6 members). Member list from the FY2024 10-K, *"OUR MEMBERS AND THEIR POWER SUPPLY RESOURCES – Member Demand and Energy Requirements"* | as above |
| 6 | **154 / 154** distinct (state, county) pairs those 38 members serve lie **inside** the SOCO BA's own 252-county footprint | EIA-861 2024 `Service_Territory_2024.xlsx` × PUDL `out_ferc714__respondents_with_fips` respondent 142, 2024 (157 GA + 60 AL + 23 MS + 12 FL = 252) | `https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__respondents_with_fips.parquet` |

**Independent identity check that the 714 series is the member load** (not something else):
EIA-861 2024 `Operational_Data` gives Oglethorpe summer peak **10,341 MW**, winter peak
**10,489 MW**; the committed 714 parquet's 2024 maximum for respondent 107 is **10,489 MW** — the
same number, from a different EIA form.

**Currency.** Link 2 is a 2014-vintage audit; it is the most recent public NERC document naming
GSOC's BA that this lane could find. Its currency for 2023–2025 rests on links 1, 3, 4 and 5, all
of which are 2024–2026 vintage and all of which say the same thing.

## 2. MEAG (210) — MEAG says it itself

Source: **Municipal Electric Authority of Georgia, Annual Information Statement for the Fiscal
Year Ended December 31, 2024**, dated **May 22, 2025**, filed under SEC Rule 15c2-12.
`https://www.meagpower.org/wp-content/uploads/2025/05/MEAG-2024-Annual-Information-Statement.pdf`
(5,442,616 B; sha256 `11037256b4002424a534c3e4aa7b2e2a22136d6a8cb0859a8be7657b14070632`).
Printed **pp. 25–26** (PDF pp. 30–31), section *Pseudo Scheduling and Services Agreement*.
Transcription committed: `data/raw/soco-planning/transcriptions/MEAG_2024_Annual_Information_Statement_PSSA_pp24-27.txt`.

Three passages, verbatim:

> (e) MEAG Power controls the other non-nuclear resources in **the Balancing Authority Area of
> The Southern Company** ("Southern Company"), the parent company of GPC, to which MEAG Power
> has ownership rights, all to meet MEAG Power's requirements.

> The term "MEAG Territorial Control Area Services" means those Control Area Services that are
> needed (a) to effectuate **the delivery of power to MEAG Power's Territorial Load**, as defined
> in the PSSA; and (b) to maintain the integrity of the ITS and **the Southern Company Balancing
> Authority Area** during such transactions.

> GPC has agreed to cooperate with MEAG Power to develop agreements to permit MEAG Power, upon
> the termination of the PSSA, **to form or become part of another balancing authority area** for
> dispatching and scheduling its generating units to match its loads should MEAG Power elect to do so.

The third is what makes the first two dispositive rather than atmospheric: the counterfactual
"**another** balancing authority area" is only meaningful if MEAG is currently inside one, and the
document names which. The MEAG Territorial Control Area Services are defined as exactly the BA
services required to deliver **MEAG's Territorial Load** while preserving the integrity of the
Southern Company BA Area.

The same three passages appear, near-identically worded, in the **FY2022** AIS (dated 2023-06-09,
printed pp. 30–32), so the language is not a one-year artifact.

**Corroboration, EIA-861 2024:** **48 of MEAG's 49 Participants** carry `BA Code = SOCO`; the 49th,
**Fort Valley Utility Commission**, reads `SEPA`. **51 / 51** distinct (state, county) pairs the 49
Participants serve lie inside the SOCO BA's 252-county footprint. Participant list:
`https://www.meagpower.org/participants/overview/`.

**Identity check:** EIA-861 2024 `Operational_Data` gives MEAG summer peak **2,399 MW**; the
committed 714 parquet's 2024 maximum for respondent 210 is **2,399 MW**.

## 3. Southern Power (186) — a documented NO, and why

**No source found states, or implies, where respondent 186's FERC-714 planning-area load is.**
Four independent things were checked; each returns nothing, and two actively cut against the
assumption.

**(a) The form itself has no such field.** FERC Form No. 714 **Part I – Schedule 1 (Identification
and Certification)** asks a respondent to check *Balancing Authority Area* **or** *Planning Area*
and to name the one it is. The instructions say only: *"iv. Planning Area. Enter/verify the name
of the planning area reporting. If the planning area and balancing authority area are identical,
then these names may be identical."* **There is no field in which a planning-area respondent
identifies the balancing authority it sits in.** This is the structural reason PUDL cannot
attribute one, and it applies to 107 and 210 as well — which is why those two had to be sourced
from outside the form.
Sample form: `https://www.ferc.gov/sites/default/files/2020-06/sample-form.pdf` (p. 1).
Instructions: `https://www.ferc.gov/sites/default/files/2020-06/form-714-instructions.doc`
(§I.B *Who Must Submit*, §III *Definitions*, §IV.A).

**(b) The schedule that WOULD answer it is behind the one URL still blocked.** Form 714
**Part III – Schedule 1** is titled *"Electric Utilities That Compose the Planning Area"* — the
filed roster of who is in respondent 186's planning area. PUDL does not ETL that schedule (it
carries Part III Schedule 2 hourly demand, the forecast, and respondent IDs only), and FERC's own
bulk CSVs are **403** from this egress (§5). **This is the single item that would settle 186**, and
it is a fetch, not a judgement — see §7 routing.

**(c) EIA gives 186 nothing to attach to.** PUDL/EIA classify respondent 186 as
`respondent_type = utility` with **no** `balancing_authority_code_eia`, **no** counties, in every
year 2019–2025. Southern Power is **absent from EIA-861 entirely** — no retail sales, no service
territory — so the member/participant containment test that carried 107 and 210 cannot be run at
all for 186.

**(d) The generation claim is true for a minority of the fleet, and is the wrong claim anyway.**
EIA-860 (`data/raw/eia-860/eia860_plant.parquet`, 2025 Early Release) shows **"Southern Power Co"
(EIA utility ID 17650)** operating **53 plants across 15 balancing authorities in 13 states**:

| BA | plants | | BA | plants | | BA | plants |
|---|---:|---|---|---:|---|---|---:|
| CISO | 12 | | SOCO | **11** (9 GA, 2 AL) | | ERCO | 8 |
| SWPP | 6 | | DUK | 3 | | NEVP | 3 |
| WACM | 2 | | CPLE / EPE / IID / ISNE / MISO / PJM / PSEI / SPA | 1 each | | | |

So **42 of 53 plants are outside SOCO**. "Its generation is in the footprint" is false as a general
statement — and even where true it speaks to generation, not to planning-area load.

**(e) What the series actually looks like.** Respondent 186's demand is a nearly **flat block**,
unlike every other respondent in the set (2024, committed parquet):

| respondent | mean MW | load factor | monthly range (× annual mean) | diurnal range (× mean) |
|---|---:|---:|---|---|
| 186 Southern Power | 387 | **0.795** | **0.84 – 1.10** | **0.95 – 1.04** |
| 183 Georgia Power | 10,323 | 0.624 | 0.86 – 1.18 | 0.83 – 1.11 |
| 107 Oglethorpe | 5,162 | 0.492 | 0.79 – 1.27 | 0.76 – 1.20 |

No weather signature, no diurnal signature. Whatever respondent 186 reports, it is **not a
territorial load** of the kind the other five report. Under the form's own definition — *"Net
Energy for Load (Planning Area): the amount of energy required by the reported utility or group of
utilities' retail customers in the system's service area plus the amount of energy supplied to
full and partial requirements utilities (wholesale requirements customers) plus … losses"* — and
Southern Power having no retail customers, the residual reading is wholesale-requirements service.
**This lane does not assert that**; it records that the shape is inconsistent with a territorial
load and that no source identifies the customers or their location.

**The honest summary for 186:** the IIC establishes that Southern Power is a party to the Southern
electric system's central dispatch. That supports *"Southern Power's Southern-footprint generation
is dispatched inside the SOCO BA."* It does **not** support *"Southern Power's FERC-714
planning-area load is inside the SOCO BA,"* which is the claim gate G22 asks for.

## 4. Two things in the record that this lane found do not hold up

Both are reported because G22's evidence chain leans on them. Neither is this lane's to resolve.

### 4.1 The PowerSouth half of the falsifier — its *stated reason* is not clean for 2023–2025

SOCO-11 §3.3 and the committed `SOURCES.md` say PowerSouth and Tallahassee *"run their own
balancing authorities (`AEC`, `TAL`)"*. Measured:

| check | Tallahassee (34) | PowerSouth (1) |
|---|---|---|
| PUDL `respondent_type`, 2023–2025 | `balancing_authority`, code `TAL` | `balancing_authority`, code **`AEC`** |
| EIA-861 `Balancing_Authority` BA registry | listed, **2019 and 2024** | listed **2019**, **ABSENT 2021 / 2022 / 2023 / 2024** |
| EIA-861 2024 `BA Code` on its own utility rows | — | **`SOCO`** (Demand_Response and Energy_Efficiency rows) |
| its footprint vs SOCO's 252 counties | Leon FL — **outside** | 50 AL/FL counties (2019) — **all 50 inside** |

So: **Tallahassee is clean.** **PowerSouth is not.** EIA's own BA registry stopped listing `AEC`
after 2019 and EIA-861 now codes PowerSouth's utility rows to `SOCO`, while PUDL still classifies
it as the `AEC` balancing authority through 2025. The two EIA-derived products disagree, in the
window that matters.

This does **not** overturn the overshoot — the measured −2.28 / −2.41 / −4.15 % is unaffected, and
it remains the operative evidence that the last two respondents are outside the metered SOCO
demand. What it overturns is the *sentence used to explain* the overshoot. Whoever next quotes the
falsifier should quote the overshoot, not the "own BA" reason, until this is settled.

It also shows the **county-containment test is necessary but not sufficient**: AEC's own footprint
sits entirely inside SOCO's 252 counties, so geography alone cannot separate a nested BA from its
host. That is why §1 and §2 rest on the NERC audit and the MEAG AIS, with containment as
corroboration only.

### 4.2 "GSOC's Balancing Authority Area" — a vendor claim, contradicted by the primary sources

A PCI Energy Solutions press release states GSOC performs *"Real-time scheduling and balancing for
GSOC's Balancing Authority Area (BAA)"*
(`https://www.pcienergysolutions.com/news/georgia-system-operations-corporation-selects-pci-platform-for-power-scheduling-operations-optimization/`).
Taken literally that would put Oglethorpe outside SOCO. It is contradicted by two primary sources:
the NERC/SERC audit (GSOC registered **LSE + TOP**; its **BA is SCS-Trans**) and EIA's 2024 BA
registry (**68 BA codes; no GSOC**, and no Georgia BA besides SOCO/TVA/DUK/SCEG/SEPA). GSOC's own
CEO, testifying to FERC in 2016, describes GSOC as *"registered with NERC as a Transmission
Operator"* and Southern Company Services as *"GSOC's Reliability Coordinator"*
(`https://www.ferc.gov/sites/default/files/2020-08/FordGeorgiaSystemOperations.pdf`, pp. 1–2).
Recorded so the next lane does not re-litigate it.

## 5. Blocked / probed — exact URLs and statuses (2026-09-13)

| URL | method | status | note |
|---|---|---|---|
| `https://www.ferc.gov/sites/default/files/2020-06/Form-714-csv-files.zip` | HEAD | **403** | SOCO-11's URL, 403 again. **Holds the Part III Schedule 1 roster that would settle respondent 186** |
| `https://www.ferc.gov/industries-data/…/form-no-714-annual-electric/data` | HEAD | **403** | SOCO-11's URL, 403 again |
| `https://www.ferc.gov/` | HEAD | **403** | SOCO-11's URL, 403 again |
| `https://www.ferc.gov/sites/default/files/{2021-06,2023-06}/Form-714-csv-files.zip`, `…/form714-database.zip` | HEAD | **403** | guessed alternates, all refused |
| `https://www.ferc.gov/sites/default/files/2020-06/sample-form.pdf` | GET | **200** | 325,570 B — **the FERC block is not uniform**; static files that exist are served |
| `https://www.ferc.gov/sites/default/files/2020-06/form-714-instructions.doc` | GET | **200** | 110,592 B |
| `https://www.ferc.gov/sites/default/files/2020-08/FordGeorgiaSystemOperations.pdf` | GET | **200** | 83,471 B |
| `https://zenodo.org/api/records?q=ferc714` | GET | **403** | egress proxy's own error page; PUDL's raw-714 archive (DOI `10.5281/zenodo.4127100`) unreachable from here — the second route to the Part III roster |
| `http://web.archive.org/web/…/form-no-714-annual-electric/data` | GET | **403** | Wayback also refused; WebFetch declines the host outright |
| `https://www.sec.gov/cgi-bin/browse-edgar?…` | GET | **429** | rate threshold; **worked at 200 on `data.sec.gov` and `/Archives/` with a contact User-Agent**, per SEC policy |
| `https://www.oglethorpepower.com/` | GET | **000** | connection failed; `opc.com` is the live host and EDGAR served the filings |

Nothing in this FINDING was transcribed from memory. Every quoted value carries the URL and page
above. **A negative is recorded as a negative** — the 403 on FERC's bulk CSV stopped that item, as
the SOCO-12 discipline requires, and is not worked around.

## 6. Files landed

| path | note |
|---|---|
| `data/raw/zone-specific-demand/SOCO/SOURCES.md` | **APPENDED** — new section "BA membership of respondents 107, 210 and 186 (lane SOCO-14)" beneath SOCO-11's eight-respondent table. **No existing line edited.** |
| `data/raw/soco-planning/NERC_SERC_Public_Audit_GSOC_NCR01248_2014.pdf` | new, tracked, 138,763 B |
| `data/raw/soco-planning/NERC_SERC_Public_Audit_Southern_NCR01166-01247-01273-01320_2021.pdf` | new, tracked, 707,103 B |
| `data/raw/soco-planning/FERC_Form_714_sample_form.pdf` | new, tracked, 325,570 B |
| `data/raw/soco-planning/transcriptions/MEAG_2024_Annual_Information_Statement_PSSA_pp24-27.txt` | new, tracked — the 5.4 MB AIS payload stays untracked per the corpus convention |
| `data/raw/soco-planning/transcriptions/FERC_Form_714_instructions.txt` | new, tracked — `.doc` payload untracked |
| `data/raw/soco-planning/README.md` | **APPENDED** — SOCO-14 rows in the tracked/untracked table + a section |
| `data/raw/soco-planning/SHA256SUMS.txt` | **APPENDED** — SOCO-14 block |
| `docs/handoffs/FINDING-soco-14-2026-09-13.md` | this file |

No `src/`, `scripts/`, `tests/`, `frontend/`, plan, ledger or `docs/calibration-log/soco.md` edit.
SOCO-11's committed parquet and its existing `SOURCES.md` text untouched. No matrix cell moved
(rule 28 — this lane tests no mechanism). No CI workflow added. No solve run.

## 7. Routed to the desk

1. **G22 FAILS on respondent 186 alone.** Card S3's six-respondent premise is not fully sourced.
   107 and 210 are cited to primary documents; 186 is not. The card returns to the owner.
2. **One fetch would settle 186, and this lane could not make it.** Form 714 **Part III Schedule 1,
   "Electric Utilities That Compose the Planning Area"**, for respondent 186. Both routes are
   blocked from this egress (FERC bulk CSV 403; Zenodo 403). A lane with a different egress, or a
   FERC eLibrary retrieval of Southern Power Company's filed Form 714, closes it either way — and a
   NO from that document is as useful as a YES.
3. **The falsifier's stated reason needs repair** (§4.1). PowerSouth's `AEC` BA is carried by PUDL
   through 2025 but was dropped from EIA-861's BA registry after 2019, and EIA-861 codes
   PowerSouth's own rows to `SOCO`. Quote the overshoot, not the "own BA" sentence, until resolved.
   Tallahassee is clean and can be quoted as-is.
4. **County containment is corroboration, never proof** (§4.1). AEC's 50-county footprint sits
   entirely inside SOCO's 252 — a nested BA passes the test. Wherever SOCO-11's 59/59, 155/155,
   23/23 containment figures are quoted, this limit should be quoted with them.
5. **Respondent 186 is not a territorial load** (§3(e)): flat, load factor 0.795, no weather or
   diurnal signature. If the desk ever does fold it in, it contributes level and essentially no
   shape — that is a fact SOCO-32 will need whatever G22 resolves to.
6. **Two EIA-861 `SEPA` codings inside the cited sets** — Three Notch EMC (an Oglethorpe member)
   and Fort Valley Utility Commission (a MEAG Participant). SEPA is a federal power marketer, not a
   load-balancing area with territorial demand; the coding most likely reflects predominant
   supplier. Reported at full magnitude rather than smoothed away; neither changes a verdict, since
   both entities' load is inside their G&T's / joint-action agency's planning area, which is what
   the NERC audit and the MEAG AIS place in SOCO.

## Log entry

```
### soco-14 — 2026-09-13 — BA membership of FERC-714 respondents 107 / 210 / 186

GATE G22 = FAIL, 2 of 3 cited.

Oglethorpe (107) YES: NERC/SERC public compliance audit NCR01248 p.3 -- "The
Reliability Coordinator (RC), Balancing Authority (BA), and Transmission
Operator for GSOC is Southern Company Services, Inc. - Transmission." GSOC
schedules and dispatches Oglethorpe's resources and is the registered LSE for
the 38 member EMCs (OPC FY2024/FY2025 10-K, Control Area Compact with Georgia
Power). SCS-Trans is EIA BA code SOCO / BA ID 18195 (EIA-861 2024). 37 of 38
members coded BA=SOCO in EIA-861 2024; 154/154 member counties inside the SOCO
BA's 252-county footprint. Cross-check: EIA-861 Operational_Data winter peak
10,489 MW == the 714 series' 2024 maximum.

MEAG (210) YES, in MEAG's own words: Annual Information Statement FY2024
(dated 2025-05-22, printed pp.25-26) places MEAG's Territorial Load inside "the
Southern Company Balancing Authority Area", and the PSSA's exit clause speaks of
MEAG later joining "another balancing authority area". 48 of 49 Participants
coded BA=SOCO; 51/51 counties inside. Cross-check: EIA-861 summer peak 2,399 MW
== the 714 series' 2024 maximum.

Southern Power (186) NO -- documented. FERC Form 714 has no field in which a
planning-area respondent names its BA (sample form p.1 + instructions IV.A);
PUDL/EIA give 186 no BA code, no counties, no EIA-861 presence at all; EIA-860
shows 42 of its 53 plants OUTSIDE SOCO, in 15 BAs across 13 states, so "its
generation is in the footprint" is false as stated and is the wrong claim
regardless; and its 714 series is a flat ~390 MW block (LF 0.795, diurnal
0.95-1.04x) that is not a territorial load. The document that would settle it,
Part III Schedule 1 "Electric Utilities That Compose the Planning Area", is in
FERC's bulk CSVs -- 403 from this egress, as at the SOCO-11 charter -- and
Zenodo (PUDL's raw archive) is 403 too. Routed as one fetch.

Also routed: the falsifier's STATED reason does not hold for 2023-2025 --
EIA-861's BA registry dropped AEC (PowerSouth) after 2019 and now codes
PowerSouth's own rows to SOCO, while PUDL still classifies it AEC through 2025.
The measured overshoot is unaffected; the explanation is. And county containment
is corroboration only: AEC's 50-county footprint sits entirely inside SOCO's 252,
so a nested BA passes that test.

No share derived, no parquet written, no solve, no matrix cell moved.
```
