# FINDING — lane NWPP-12: WECC path ratings, WRAP, IRPs, NRC, LTLF, fuel, retirements

**Lane:** NWPP-12 (`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-12,
§3 cards N5/N7, §6 manifest rows 7–11). **Date:** 2026-09-13.
**Model:** Opus `claude-opus-5`. **DATA PROFILE:** `shared`.
**Branch:** `claude/nwpp-12-docs-plan-ftlv5u`. **Base:** work was done at
`origin/main` `4d9c3251` and **rebased onto `33a7c961`** before pushing (§8.0
collision rule 3), which is after siblings NWPP-10, NWPP-11 and NWPP-13 landed.
Both are this lane's own base shas, re-measured rather than taken from the
desk's `c93b0d27` pin (§8.0 collision rule 6). No file this lane wrote exists on
`origin/main` at either sha — checked, no collision.

---

## 0. THE THREE ANSWERS THE DESK ASKED FOR FIRST

### 0.1 The LTLF — gate **G12**, and it is NOT a blocker

**A citable long-term load forecast exists for this footprint, with an edition
and a vintage ≥ 2020. It exists only as an ASSEMBLY from participant IRPs,
because the Northwest Power Pool publishes no footprint-wide long-term load
forecast — it is a pool of 17 balancing authorities, not an ISO, and issues no
Gold Book / CELT / LTLF / ITP equivalent.** The assembly is landed at
`data/raw/load-forecast/nwpp/nwpp.csv` (83 rows) with the assembly rule, its
coverage and every publisher that supplies no row documented in
`data/raw/load-forecast/nwpp/SOURCES.md`. **Declared for NWPP-20's
`scripts/lib/load_forecast/nwpp.py`: `edition = "Participant IRP assembly (2025
cycle)"`, `vintage = 2025`, `default_basis = "unspecified"`.** `vintage` is 2025
because that is the newest constituent publication that actually supplies a row
(NorthWestern's 2026 Montana IRP is newer and supplies none — its load tables
are images).

**W2 is not blocked. But the gate passes with a caveat the desk must see, and
the caveat is coverage, not existence:**

| Publisher | Rows | BA(s) | 2024 share of footprint demand |
|---|---|---|---|
| PacifiCorp 2025 IRP | 20 (`summer_peak_mw` 2025–2044) | PACE + PACW | 25.40 % |
| Idaho Power 2025 IRP | 61 (`annual_peak_mw`, 2024 actual + 2026–2045 × 3 percentiles) | IPCO | 6.43 % |
| PSE 2023 Electric Progress Report | 2 (`annual_peak_mw` 2024, 2045) | PSEI | 8.53 % |
| **Total** | **83** | **4 of 17 BAs** | **40.36 %** |

**`BPAT` — the largest BA at 20.26 % of footprint demand — supplies no row,
because BPA is a federal power marketing administration and files no IRP.** Four
further publishers (NorthWestern, NV Energy, PGE, Avista) publish the series but
only as **images**, so they are an extraction problem, not a fetch problem
(§5.3). Nothing was scaled, summed or interpolated to close the 60 % gap; doing
so would be a derivation this lane refuses to make silently.

### 0.2 WRAP's first binding season — card **N7**'s gating fact

**Winter 2027–2028, beginning 1 November 2027. The desk's expectation is
CONFIRMED: binding post-dates the 2023–2025 backcast window by two years, so
WRAP is a FORECAST-SIDE OBJECT ONLY for this program.**

Citation: `WPP_BPM_109_Transition_Period_V3.0_2026-03.pdf`, printed **p. 4**,
verbatim: *"All Participants will be subject to Binding participation
obligations starting **November 1, 2027** (for the Winter 2027-2028 Binding
Season), but the Transition Period rules allow each Participant the option to
elect to also participate one season earlier as a Binding Participant in
**Summer 2027**."* The optional early-binding season (Summer 2027) also
post-dates the window. Full quotations, Table 1 of the transition schedule, the
opt-in date gates and two independent participant corroborations (PacifiCorp
printed pp. 105–106; Idaho Power App. D printed p. 6) are in
`data/raw/nwpp-planning/README.md` §2.1.

**What this means concretely for a 2023–2025 backcast:** BPM 109 printed p. 6
§4.1 — during Non-Binding seasons a participant is *"not subject to Deficiency
Charges under the FS Program, or to mandatory Holdback Requirements… mandatory
Energy Deployments, or Delivery Failure Charges"*. So **no WRAP obligation
binds in any scored year**, and the backcast reliability floor must rest on the
participants' own IRP reserve margins — which is what card N7 anticipated, and
which §2.2 of this finding supplies.

### 0.3 Which card N5 boundaries have a published path rating — card **N5**

The WECC **2024 Path Rating Catalog — Public Version** was obtained (83 pp.) and
every path relevant to this footprint transcribed with its printed page
(`data/raw/nwpp-planning/README.md` §1). Against card N5's five zones:

| Boundary | Published rating? | Which | Tier |
|---|---|---|---|
| **NWPP-NW ↔ NWPP-OR** | **NO — none exists** | — | **Tier 3, documented** |
| NWPP-NW ↔ NWPP-INLAND | yes — **three**, none the whole boundary | Path 8 (2,200/1,350), Path 6 (4,277/n.d.), Path 14 (2,400/1,200–1,340) | Tier 2 (aggregation documented) |
| NWPP-INLAND ↔ NWPP-EAST | yes | Path 20 "Path C" (1,600/1,250) | Tier 2 (Pre-Gateway; partly PACE-internal) |
| NWPP-EAST ↔ NWPP-SNV | yes, and it is clean | Path 35 TOT 2C (600/580) | **Tier 1 candidate** |
| NWPP-INLAND ↔ NWPP-SNV | yes, and it is clean | Path 16 Idaho–Sierra (500/360) | **Tier 1 candidate** |
| NWPP-OR ↔ NWPP-INLAND | not separately rated | — | Tier 3 |

**The desk's expected finding is CONFIRMED and it is a positive result, not a
failed search.** There is no path in the catalogue rating a
BPAT/PSEI/SCL/TPWR/CHPD/DOPD/GCPD ↔ PGE/PACW interface. The full 89-slot table of
contents was read. The Pacific-Northwest paths WECC does rate there — Paths 4
and 5 ("West of Cascades–North/South"), 71 ("South of Allston"), 86/87/88 ("West
of John Day / McNary / Slatt") — are **east-to-west cuts across the Columbia and
the Cascades**, not BA interfaces; Path 5's own line list mixes BPA-internal
500 kV, BPA→PGE limbs **and** a PGE-internal limb in one 7,200 MW rating, so it
is not a BPAT↔PGE number and must not be used as one. The physical reason: BPA
and the PGE / PacifiCorp-West systems interconnect at **many** points around
Portland and the Willamette Valley, and a dense multi-point interconnection is
precisely what WECC's path process does not produce a number for.

**So NWPP can have a better TTC story than SPP got — on four of its five
boundaries.** SPP registered a 48,700 MW placeholder with nothing behind it
(`docs/calibration-log/spp.md`); NWPP registers **two boundaries on a single
rated line each**, two more on rated paths needing a documented reconciliation,
and exactly **one** Tier-3 link whose Tier-3-ness has a **physical reason on the
record**. Under rule 14 `[R-ACCURATE]`, a documented absence with a stated cause
is a materially stronger basis for a calibration value than a number borrowed
from an adjacent path.

---

## 1. Got / blocked

| # | Item | Status | Landed at |
|---|---|---|---|
| 1 | WECC published path ratings (Paths 3, 4, 8, 14, 20, 27, 35, 65, 66 + 15 neighbours) | **GOT** | `data/raw/nwpp-planning/README.md` §1; `transcriptions/2024_Path_Rating_Catalog_Public_v2.txt` |
| 1b | Path → card N5 boundary mapping incl. the NW↔OR absence | **GOT** | README §1.3, §1.4 |
| 2 | WRAP first binding season, with citation | **GOT** | README §2.1 |
| 2b | WRAP participants — which of the 17 BAs | **GOT (13 of 17)**, with one unreconciled discrepancy | README §2.3 |
| 2c | WRAP participants — *from when* | **NOT PUBLISHED** | README §2.3 |
| 2d | Forward showing requirement | **GOT** | README §2.4 |
| 2e | Holdback requirement | **GOT** — it is a mechanism, not a percentage | README §2.5 |
| 3 | IRPs ×7: PRM by season | **GOT for 5 of 7** (PacifiCorp, Avista, NorthWestern, PSE, + WRAP monthly); **not published** for Idaho Power and NV Energy | README §4 |
| 3b | IRPs: peak-load history | **PARTIAL** — Idaho Power only; the rest are image tables | README §4, §5 |
| 3c | IRPs: resource plan | **GOT for 6 of 7** | README §4 |
| 3d | IRPs: announced coal exit dates | **GOT** | README §4; `coal-prices/SOURCES_nwpp_coal.md` §4 |
| 3e | IRPs: published internal transfer limit | **PARTIAL** — NorthWestern yes (§3 of README); PacifiCorp states the concept but never the MW | README §3, §4.1 |
| 4 | NRC licence expiry + SLR, Columbia Generating Station | **GOT** | `data/raw/nuclear-license-status/nwpp.csv` |
| 5 | LTLF with edition + vintage ≥ 2020 | **GOT (assembled)** | `data/raw/load-forecast/nwpp/nwpp.csv` + `SOURCES.md` |
| 6 | Gas basis per zone | **GOT (mapping + measured spread)**; **NO free series** for Stanfield/Opal/Kern River | `data/raw/gas-prices/SOURCES_nwpp_gas.md` |
| 6b | Coal basis per plant | **GOT for 8 plants**; **NO data** for Colstrip or Centralia | `data/raw/coal-prices/SOURCES_nwpp_coal.md` |
| 7 | Confirmed retirements — enforceable instruments | **PARTIAL — one instrument found (Jim Bridger 1&2 Consent Decree); the rest are IRP intentions** | `coal-prices/SOURCES_nwpp_coal.md` §4 |

**Zero items were blocked by a host.** Every document named in the charter was
reachable and fetched; `wecc.org`, `westernpowerpool.org`, `nrc.gov`,
`pacificorp.com`, `docs.idahopower.com`, `myavista.com`,
`northwesternenergy.com`, `nvenergy.com`, `pse.com` and
`downloads.ctfassets.net` all returned 200. Every "PARTIAL" above is one of two
things, and the distinction matters for what a follow-up should do:

- **a table rendered as an IMAGE** (§5.3) — the document is public and in the
  corpus; the cells need image extraction or a hand read, not another fetch;
- **a quantity the publisher genuinely does not print** (§5.4) — no follow-up
  will find it, and inventing it is what the corpus exists to prevent.

Four 404s were recorded (not blocks — wrong paths, all resolved):
`nrc.gov/info-finder/reactors/colu` (the correct slug is **`wash2`**),
`westernpowerpool.org/about/program/wrap`,
`portlandgeneral.com/about/info/iso-and-regulatory/integrated-resource-planning`,
`pse.com/en/IRP/Current-IRP-Process`. All in `nwpp-planning/SOURCES.md`.

---

## 2. Transcribed values table

Every value below is quoted from a document in `data/raw/nwpp-planning/` and
carries its printed page there. This is the index; the quotations are in
`data/raw/nwpp-planning/README.md`.

### 2.1 WECC path ratings (README §1.1–§1.2)

| Path | Name | Category | p. | Limits (MW) |
|---|---|---|---|---|
| 3 | Northwest–British Columbia | Accepted | 10 | N→S 3,150 · S→N 3,000 |
| 4 | West of Cascades–North | Other | 11 | E→W 10,700 · W→E 10,700 |
| 5 | West of Cascades–South | Other | 12 | 7,200 · 7,200 |
| 6 | West of Hatwai | Accepted | 13 | E→W 4,277 · W→E not defined |
| 8 | Montana-to-Northwest | Accepted | 15 | E→W 2,200 · W→E 1,350 |
| 14 | Idaho-to-Northwest | Accepted | 17 | E→W 2,400 · W→E 1,200–1,340; winter 2,400 |
| 16 | Idaho–Sierra | Existing | 19 | N→S 500 · S→N 360 |
| 17 | Borah West | Accepted/Other | 20 | 2,557 · 1,600 |
| 18 | Montana–Idaho | Accepted/Existing | 21 | N→S 383 · S→N 256 |
| 19 | Bridger West (Pre-Gateway) | Accepted/Other | 22 | 2,400 · 1,250 |
| 20 | Path C (Pre-Gateway) | Accepted | 23 | N→S 1,600 · S→N 1,250 |
| 27 | Intermountain Power Project DC | Accepted | 28 | NE→SW 2,400 · SW→NE 1,400 |
| 35 | TOT 2C | Accepted | 36 | N→S 600 · S→N 580 |
| 55 | Brownlee East | Accepted | 54 | W→E 1,915 · E→W not rated |
| 65 | Pacific DC Intertie | Existing | 62 | N→S 3,220 · S→N 3,100 |
| 66 | California–Oregon Intertie | Existing | 63 | N→S 4,800 · S→N 3,675 |
| 71 | South of Allston | Other | 65 | N→S 2,725–3,100 |
| 75 | Hemingway–Summer Lake | Accepted | 68 | E→W 1,500 · W→E 550 |
| 80 | Montana Southeast | Other | 73 | 600 · 600 |
| 85 | Aeolus West (Post Gateway) | Accepted | 78 | E→W 2,670 · W→E 1,816 |
| 86 | West of John Day | Accepted | 79 | E→W 4,760 |
| 87 | West of McNary | Accepted | 80 | E→W 4,925 |
| 88 | West of Slatt | Accepted | 81 | E→W 4,760 |

### 2.2 Planning reserve margin by season (README §4)

| Utility | Summer | Winter | Source |
|---|---|---|---|
| **PacifiCorp** | **14.4 %** (July) | **16.8 %** (December) | 2025 IRP Vol. 1 p. 131 — *"adopted from WRAP for the 2025 IRP"* |
| **Avista** | **16 %** (May–Sep) | **24 %** (Oct–Apr) | 2025 Electric IRP pp. 4, 82 |
| **PSE** | 2029 **21.2 %**, 2034 **26.1 %** | 2029 **23.8 %**, 2034 **23.9 %** | 2023 EPR Ch. 7 p. 7.3 (5 % LOLP ⇒ 1-in-20-year target) |
| **NorthWestern** | takes WRAP's monthly: Jun **26.2 %**, Jul **14.5 %**, Aug **16.1 %**, Sep **14.2 %** (2025 Summer FS) | uses the month giving the highest load+PRM | 2026 MT IRP pp. 147, 150 (Table 39) |
| **Idaho Power** | **not published** (a model-calibration output; the published standard is **LOLE 0.1 event-days/yr**) | same | 2025 IRP App. D pp. 7–8 |
| **NV Energy** | **not published** as a company target | same | 2024 Joint IRP Vol. 6 p. 25 |
| **PGE** | **not published**; the 10/12.5/15 % in Appendix G are **market-power** assumptions, not PGE's PRM | same | 2023 CEP/IRP pp. 499, 501, 64 |

> **The single most consumable answer for card N7** is PacifiCorp's, because it
> is a published, per-season, **WRAP-derived** number that a
> `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` entry can cite directly: **14.4 %
> summer / 16.8 % winter.** Note what it is: WRAP's own FSPRM as one participant
> adopted it, not a footprint-wide constant — WRAP's FSPRMs are **monthly and
> per subregion by construction** (README §2.4), so no single WRAP-wide PRM
> number exists to transcribe.

### 2.3 Peak-load history and forecast (README §4)

| Utility | Value |
|---|---|
| Idaho Power | **summer record 3,793 MW, 2024-07-22 19:00**; **winter record 2,719 MW, 2024-01-16 09:00**; forecast to 5,517 MW (50th) by 2045 |
| PacifiCorp | system summer coincident peak **11,318 MW (2025) → 15,518 MW (2044)**, CAGR **1.67 %** |
| PSE | base peak **4,753 MW (2024) → 6,717 MW (2045)**, **1.7 %**/yr; energy 2,551 → 3,699 aMW, 1.8 %/yr; **winter-peaking** but summer capacity need is higher |
| Avista | summer peak **+8.8 %** and winter peak **+12.2 %** vs 2014 actual, by 2024; forecast summer **+1.14 %**/yr, winter **+1.12 %**/yr |
| NV Energy | 2025–2044 coincident-peak CAGR **2.2 %**, system peak **+4,811 MW**; **7,600 MW** of large-load requests, **5,900 MW** of it twelve data centres by 2033 |
| PGE | *"peak load of approximately 4,000 MW"* (footnote); now summer-peaking |
| NorthWestern | Table 29 is an image — **not transcribed** |

### 2.4 Coal exits — and the instrument-vs-intention line the charter asked for

Full table with quotations: `data/raw/coal-prices/SOURCES_nwpp_coal.md` §4.

**The only enforceable public instrument with a date that this lane found is the
Jim Bridger Consent Decree**: *"On February 14, 2022, Wyoming and PacifiCorp
filed a Consent Decree in the Wyoming State District Court… reflecting heat input
limits consistent with the conversion of Bridger units 1 and 2 to natural gas
generation by January 1, 2024"* (Idaho Power 2025 IRP printed p. 17). It meets
CLAUDE.md's step-0 bar.

Everything else is an **IRP intention** and is recorded as one — including two
that **contradict each other**: PacifiCorp plans a Colstrip exit *"by 2030"*
while NorthWestern's Base Case has *"Colstrip retires according to its project
book life on December 31, 2042"*. Idaho Power's North Valmy gas conversion "by
summer 2026" is filed under *"Actions Committed to before the 2025 IRP — **Not
for Regulatory Acknowledgment**"*, i.e. the utility itself declines to call it
an instrument.

**Two instruments this lane did NOT obtain, named so a follow-up goes straight
to them rather than re-searching:** Washington's coal-transition statute
governing **Centralia** (the plan's 229.5 MW / 2027 EIA-860 row could not be tied
to a document here), and **Washington's CETA**, the driver behind the Avista and
PacifiCorp Washington-allocated Colstrip exits at end-2025 — referenced
repeatedly in the Avista and PGE IRPs but never with a section number, so nothing
is recorded as a CETA citation. Neither is blocked; both are simply not fetched.

### 2.5 Fuel — the measured result, which is the strongest evidence this lane produced

Measured off the **committed** `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`
(EIA-923 Schedule 2), restricted to the 17 footprint BAs via
`eia860_plant.parquet`, 2023–2025, quantity-weighted. 1,524 rows, 38 plants.

**Gas, $/MMBtu by card N5 zone:** INLAND **3.400** · OR **3.267** · NW **4.092**
· SNV **4.513** · EAST **4.564**. By BA: **NWMT 1.815** · PGE 3.267 · PSEI 3.749
· IPCO 3.903 · BPAT 4.386 · NEVP 4.513 · PACE 4.564.

> **A 2.51× internal gas spread.** A single `NWPP` gas hub is not a
> simplification, it is an error the size of the fuel cost. And `NWPP-INLAND`'s
> own average (3.400) describes neither of its two gas-burning members (NWMT
> 1.815, IPCO 3.903).

**Coal, $/MMBtu per plant:** Jim Bridger **3.252** · Hunter 3.315 · Dave Johnston
**1.192** · Bonanza 3.021 · Huntington 3.440 · Wyodak **1.378** · Naughton 2.590
· North Valmy **4.950**. The basin split is legible in the price: PRB ≈ $1.0–1.4
(corroborated by five out-of-footprint WACM Wyoming plants at 0.960–1.387),
southwest-Wyoming Green River / Kemmerer ≈ $2.6–3.3, Uinta ≈ $3.0–3.4,
rail-delivered Nevada $4.95. **Jim Bridger costs 2.7× Dave Johnston though both
are Wyoming PacifiCorp plants** — so a per-state coal price is wrong here and
coal must be priced per plant.

> **And the gap: Colstrip (6076) and Centralia (3845) have ZERO rows in that
> table, in any year, for any fuel group** — verified explicitly. Those are
> 2,377.3 MW of the footprint's 8,910.2 MW coal fleet (**26.7 %**), and they are
> the **entire** coal fleet of zones `NWPP-INLAND` and `NWPP-NW`. Colstrip is
> mine-mouth (Rosebud Mine adjoins it); this lane did not establish which
> reporting exemption applies and does not guess. Three follow-up routes,
> ordered, are in `coal-prices/SOURCES_nwpp_coal.md` §3 — the best is
> NorthWestern's own **Figure 61 "Estimated Colstrip fuel cost"** (2026 MT IRP
> printed p. 163), which exists and is exactly this quantity but is an image.

**Stanfield, Opal and Kern River have no free public daily or monthly series
reachable from this session** — established, not assumed: EIA's Natural Gas
Weekly Update table carries **four** points only (Henry Hub, New York, Chicago,
Cal. Comp. Avg.), a string search of the rendered page returns zero hits for all
three, EIA's dnav spot series is Henry Hub only, and
`eia.gov/naturalgas/xls/ice_natgas-2023final.xlsx` is **404**. **Sumas** is the
exception and is **already committed** (`gas-prices/sumas_weekly.csv`, fetcher
`scripts/data/fetch_sumas_weekly.py`), scraped from the EIA weekly *narrative*.

---

## 3. Three things the desk did not ask for and should see

### 3.1 Card N4 — the CAISO seam number is already in this repo, on the other side

`config/iso_configs.py:570` gives CAISO `TransferLink(WECC_import → NP15,
ttc_mw=4800.0)`, and the comment at `:555` cites *"(California–Oregon Intertie)
~4,800 MW into NP15"*. **That is exactly the 2024 catalogue's Path 66 N→S
rating** (README §1.1). So CAISO's import link is already seeded from a WECC
path rating whose counterparty is this footprint — which is the double-count
card N4 names, now with a specific number attached to it. **Rule 25
`[R-ISO-SCOPE]`: this lane changed nothing on the CAISO side and proposes
nothing there.** Routed to the desk / the CAISO lane as evidence only.

### 3.2 Card N5 — three structural notes, all measured

1. **`NWPP-SNV` is a misnomer.** `SPPC` does **not** exist as a separate EIA-930
   balancing authority — measured off
   `data/raw/eia-930/EIA930_BALANCE_2024_Jan_Jun.parquet`, whose 61 BAs include
   `NEVP` and no `SPPC`. `NEVP` is **all of NV Energy, north and south**, which
   is why Path 16's *northern* Nevada terminal (Humboldt) is correctly inside a
   zone named "SNV", and why NV Energy files a **joint** Nevada Power + Sierra
   Pacific IRP. The mapping is right; the name invites a mis-file.
2. **WRAP's own subregion cut disagrees with card N5's `NWPP-INLAND`.** BPM 102
   §4.1 puts **NorthWestern Energy and Avista in the Northwest Subregion** and
   **Idaho Power in Southwest-and-East** (moving to Northwest from Winter
   2027-28), while `NWPP-INLAND` groups IPCO·AVA·NWMT·WAUW. Reported, not
   argued — WRAP's is an adequacy-study boundary, not a transmission one, and
   card N5 is the desk's to rule.
3. **The largest published constraints in this footprint are invisible to a
   whole-BA zoning.** Paths 4 (10,700 MW), 87 (4,925), 86 and 88 (4,760) are
   BPA-**internal** east–west cuts. A five-zone whole-BA topology cannot
   represent them at all. That is a property of the zoning rather than a data
   gap, and belongs on a first keeper's determination basis rather than being
   discovered in W4.

### 3.3 A rule-14 caveat in the operator's own words

NorthWestern 2026 MT IRP printed **p. 122**: *"**ATC is much less than TTC** and
can change from time to time. There is also competition for ATC from multiple
types of transmission customers."* And printed p. 119: *"NorthWestern does not
own all the transmission capacity shown on these paths… relying solely on
imports is a risky and expensive approach."* So a WECC path rating is a **TTC
ceiling**: a link seeded from one is an upper bound the real market does not
reach. The per-path ATC numbers are in Figure 42 — an image.

---

## 4. Files this lane wrote

| File | New? | What |
|---|---|---|
| `data/raw/nwpp-planning/README.md` | NEW | the transcribed-values corpus: WECC paths + boundary mapping, WRAP, 7 IRPs, what is not here |
| `data/raw/nwpp-planning/SOURCES.md` | NEW | every URL + HTTP status + fetch date; the four 404s; the extraction-tooling note |
| `data/raw/nwpp-planning/SHA256SUMS.txt` | NEW | sha256 of all **21** fetched PDFs, tracked and untracked |
| `data/raw/nwpp-planning/*.pdf` (14) | NEW | tracked payloads < 5 MB |
| `data/raw/nwpp-planning/transcriptions/*.txt` (7) | NEW | `pypdfium2` text of the 7 payloads ≥ 5 MB, which are **not** tracked (corpus-conversion convention) |
| `data/raw/nuclear-license-status/nwpp.csv` | NEW | Columbia Generating Station |
| `data/raw/load-forecast/nwpp/nwpp.csv` | NEW | 83 LTLF rows |
| `data/raw/load-forecast/nwpp/SOURCES.md` | NEW | the assembly rule, coverage, and every publisher supplying no row |
| `data/raw/gas-prices/SOURCES_nwpp_gas.md` | NEW | zone→hub map, the measured spread, the reachability negative |
| `data/raw/coal-prices/SOURCES_nwpp_coal.md` | NEW | per-plant coal price, basin split, the Colstrip/Centralia gap, exits |
| `data/raw/gas-prices/README.md` | edited | **one added table row** pointing at `SOURCES_nwpp_gas.md` |
| `data/raw/coal-prices/README.md` | edited | **one added table row** pointing at `SOURCES_nwpp_coal.md` |
| `docs/handoffs/FINDING-nwpp-12-2026-09-13.md` | NEW | this file |

**No shared record touched** (§8.0 rule 1): not the plan, not the ledger, not
`docs/calibration-log/nwpp.md`, not `CHANGELOG.md`, not
`docs/mechanism-testing-matrix.md`, not any matrix shard. **No `src/`, no
`scripts/`, no `scripts/lib/*/`, no `tests/`, no other ISO's data, no `soco*`
file, no `frontend/`.** This lane tested no mechanism, so **no matrix cell moves**
(rule 28) and no `ScenarioConfig` field is added (rule 24 / gate G8).

Corpus size: **22 MB** total — ~17 MB tracked payloads + 4.6 MB transcriptions.
Seven payloads ≥ 5 MB (75 MB) were converted to transcriptions and dropped, per
`docs/bloat-removal-plan-2026-08.md` §4; re-fetch is the recovery route and every
URL was verified working today.

---

## 5. What a follow-up needs to know

### 5.1 The extraction limit is the binding constraint on this intake, not egress

`pypdfium2` recovers flowed text and ruled tables but returns **nothing** for a
table rendered as an image. Every "PARTIAL" in §1 that is not a
publisher-doesn't-print case is this. **`pdfminer.six` and `pypdf` are both
unusable in this container**: the installed `cryptography` wheel raises
`pyo3_runtime.PanicException` on import and `pypdf`'s crypt-provider fallback
catches only `ImportError`. A follow-up that installs a working PDF stack, or an
image-extraction route, recovers all of §5.3 in one pass.

### 5.2 Route notes that cost this lane time

- **`wecc.org`'s site search is a Drupal AJAX view.** `/search?keys=…` returns
  200 with the page shell and **zero result rows**, so `curl` cannot find a
  document through it. Go via `/sites/default/files/documents/…` or
  `/wecc-document/<id>`.
- **NRC info-finder slugs are not guessable.** Columbia Generating Station is
  **`wash2`** (WNP-2 heritage); `colu` is a 404. Take slugs from
  `/reactors/operating/list-power-reactor-units.html`.
- **`westernpowerpool.org/private-media/…` needs no authentication** despite the
  path segment. All eight WRAP PDFs fetched anonymously.

### 5.3 The image tables, in priority order for whoever gets an extractor

1. **NV Energy Vol. 6 Table LF-1** (annual native energy and peak 2025–2044) —
   the largest LTLF gap after BPAT.
2. **PGE Table 104** (peak load forecast by Need Future and season, printed
   p. 469).
3. **NorthWestern Figure 61** (estimated Colstrip fuel cost, printed p. 163) —
   closes the largest coal-price gap.
4. **NorthWestern Figure 42** (per-path TTC **and ATC**) — turns §3.3's
   qualitative caveat into numbers.
5. **PacifiCorp Figure 8.3** (bubble-to-bubble transfer capabilities) and
   **Tables 1.2 / 6.2 / 6.3** (coal and gas unit end dates).

### 5.4 Quantities no follow-up will find, because they are not published

- A **footprint-wide NWPP long-term load forecast** (§0.1).
- A **single WRAP-wide PRM** (README §2.4 — FSPRMs are monthly and per subregion).
- **Per-participant WRAP accession dates** (README §2.3).
- **Idaho Power's seasonal PRM percentages** (a model-calibration output).
- A **NWPP-NW ↔ NWPP-OR path rating** (§0.3).

### 5.5 One discrepancy this lane deliberately did not resolve

The WRAP programme page's 22 participant logos **omit Douglas County PUD**,
while BPM 102 §4.1 lists *"Douglas County PUD #1"* as a component BA of the
Northwest Subregion. The two answer different questions — programme membership
vs. the BAAs the LOLE study covers — and picking one would be a judgement this
lane is not chartered to make. Flagged for the desk (README §2.3).

---

## 6. ROUTED TO NWPP-DESK — seven CI gates are red on `main`, none of them this lane's

Recorded here because the charter's closing line says to route rather than reach
outside this lane's regions, and because a desk reading PR #6111's red CI should
not have to re-derive this.

All **seven** checks that failed on this lane's head `984887cb`
([run 34768364840](https://github.com/jessicacohen554-cyber/market-simulator/actions/runs/34768364840))
are **pre-existing on the base branch**. This PR's diff is 32 files — `data/raw/**`
additions, two `data/raw/*/README.md` table rows, one `docs/handoffs/` file — with
**zero** Python and nothing under `src/`, `scripts/`, `config/`, `tests/` or
`frontend/`.

| Check | Reports | Owner |
|---|---|---|
| Ruff lint + format | `scripts/gen_nyiso229_attestation.py` F401 unused `numpy`, F841 unused `drift` | NYISO lane |
| Structural refactor guards | `scripts/run_calibration_full.py` references missing `scripts/test_recorded_config_gas_anchor_mirror.py` | script owner |
| Pinned default cache key | NYISO solve surface moved `1eefed492204fab7` (209 rows) → `bd2b4657f9b5df7e` (210) | NYISO lane |
| FR-22 backcast→forecast parity | NYISO `gas_offer_margin_zonal_anchor_vintage` armed with no orchestrator consumer and no registry declaration | NYISO lane |
| FR-21 forecast-board staleness | gate-(a) provenance: MISO, NYISO, SPP `gate.a_keeper_marker` cite superseded keepers | MISO / NYISO / SPP desks |
| Keeper-integrity gates | MISO E3 + four E13 superseded registered runs (rule 35 `[R-PROMOTE]` prune); S1 status stale for ERCOT / CAISO / NEISO / MISO | MISO promoting session + desks |
| **Fast test tier** | **20 failed, 2 errors, 9,416 passed** — see below | ERCOT / NEISO / SPP / NYISO |

**The seventh check was the one that could plausibly have been this lane's, so it
was checked properly rather than assumed.** This PR adds
`load-forecast/nwpp/nwpp.csv` and `nuclear-license-status/nwpp.csv` for an ISO
with **no spec module yet** (`scripts/lib/*/nwpp.py` are NWPP-20's), and a
curation suite that globbed the raw tree instead of the spec registry would fail
on exactly that. It does not:

- `grep -rl "NWPP\|nwpp" tests/` returns **nothing** — no test references NWPP.
- The three suites that DO read these directories **pass with the new files
  present**: `uv run pytest tests/curation/test_curate_load_forecast.py
  tests/curation/test_curate_nuclear_license_status.py
  tests/unit/config/test_data_profiles_tokens.py` → **49 passed in 1.39 s**. Both
  curation suites iterate the **spec registry**, never the raw directory, so an
  ISO with no spec module is not visited.
- None of the failing suites reads any path this PR touches (checked per file).

Ten of the named failures reproduce locally at this branch's head
(`uv run pytest …` → 10 failed, 90 passed): seven ERCOT golden-manifest
provenance rows, the ERCOT `ercot_ep_gas_basis_receipts_fallback` replay-keeper
kwarg, the NEISO `test_neiso_includes_mystic_cc` (`'oil' != 'gas_cc'`), and one
worth naming on its own —

> **`tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none`
> is a STALE TEST that NWPP-20 will meet again.** It asserts
> `get_rps_target("SPP", 2030) is None` under the comment *"SPP is not modeled"*.
> SPP was registered on 2026-09-06 (SPP-20) and now carries an RPS floor, so it
> returns `0.0`. The test needs a genuinely unregistered stand-in — **and
> whatever it is changed to must not be `"NWPP"`, which stops being unregistered
> at W2.** Flagged for whoever fixes it, and for NWPP-20's §2.3 pin list.

The two `test_cache_config_agreement.py` **errors** (missing
`shard-artifacts/nyiso223/2022/run_config.json`) do **not** reproduce locally —
that suite's 90 tests pass here — so they are a CI checkout/artifact condition,
not a code failure.

**Two of the other six were reproduced directly, on bytes identical to
`origin/main`** — stronger
evidence than a re-run and it cost seconds:

- `scripts/gen_nyiso229_attestation.py` is byte-identical between `origin/main`
  and this branch (`git diff --quiet origin/main HEAD -- <file>` passes), and
  `ruff check` on it reports the same two errors locally.
- `scripts/test_recorded_config_gas_anchor_mirror.py` does not exist on
  `origin/main` either, and `scripts/run_calibration_full.py` is identical here.

**No fix is ported, and the reason is the charter rather than judgement.** Every
fix lives in a path this lane is told not to touch (`src/`, `scripts/`,
`scripts/lib/*/`, `tests/`, another ISO's data) or in another ISO's keeper shard,
which §8.0 collision rule 1 puts off-limits and which rule 35 `[R-PROMOTE]` (a)
scopes to the **promoting** lane's own ISO. The one permitted CI re-run was
deliberately **not spent**: these are deterministic assertion failures on
unchanged bytes, so a re-run returns the identical result while billing runner
minutes on a private repo (CLAUDE.md, *GitHub Actions — never offload work to
CI*).

**Two of these are gate G24's own failure mode, arriving early.** The MISO E13
rows are exactly what plan §7 gate G24 was written to stop — *"Measured at this
desk's r#2 pin: E13 is already failing for MISO (×4) and SPP (×1)"* — and the
gate-(a) provenance failures are the same supersession one layer up. SPP's E13 has
since cleared; MISO's four have not. Nothing for NWPP to do until it has a keeper,
but the desk should know the board is red before NWPP-40 tries to register onto it.

---

## Log entry

*(For NWPP-DESK to append verbatim to `docs/calibration-log/nwpp.md` — this lane
did not write that file, per §8.0 collision rule 1.)*

## 2026-09-13 — NWPP-12: planning corpus landed; WRAP is out of window; the NW↔OR link has no rating

Lane **NWPP-12** (Opus, `DATA PROFILE: shared`, branch `claude/nwpp-12-docs-plan-ftlv5u`,
base `4d9c3251`) landed the `data/raw/nwpp-planning/` corpus (21 PDFs fetched, 14
tracked, 7 converted to transcriptions; 22 MB) plus four registry-data files.
FINDING: `docs/handoffs/FINDING-nwpp-12-2026-09-13.md`. Nothing was blocked by a
host; every "partial" is an image-rendered table in a public document already in
the corpus.

Three facts every later NWPP session inherits:

- **WRAP binds from Winter 2027-2028, beginning 1 November 2027** (BPM 109
  printed p. 4, verbatim in the corpus README §2.1), with an optional Summer
  2027 early election. **Both post-date 2023–2025, so no WRAP obligation binds in
  any scored year** — card N7's backcast floor rests on participant IRP reserve
  margins, and the most consumable published pair is PacifiCorp's **14.4 %
  summer / 16.8 % winter**, itself *"adopted from WRAP"* (2025 IRP Vol. 1
  p. 131). There is **no single WRAP-wide PRM**: FSPRMs are monthly and per
  subregion by construction.
- **`NWPP-NW ↔ NWPP-OR` has no published WECC path rating, and the reason is
  physical** — BPA and PGE/PacifiCorp-West interconnect at many points, so WECC
  rates east–west *cuts* (Paths 4, 5, 71, 86, 87, 88) rather than a BA
  interface. It registers **Tier-3 with the absence documented**. Four of the
  five boundaries **do** have ratings: EAST↔SNV (Path 35, 600/580) and
  INLAND↔SNV (Path 16, 500/360) are single-line and Tier-1 candidates;
  INLAND↔EAST (Path 20, 1,600/1,250) and NW↔INLAND (Paths 8/6/14 aggregated) are
  Tier-2. Never tune a Tier-3 link to a price residual (rules 1 / 13 / 14), and
  note NorthWestern's own warning that **ATC is much less than TTC** (2026 MT
  IRP p. 122) — a path rating is a ceiling, not a delivered limit.
- **This footprint has a 2.51× internal gas spread and a bimodal coal basis**,
  measured off committed EIA-923 receipts over the 17 BAs: gas **NWMT 1.815 →
  PACE 4.564 $/MMBtu**; coal **Dave Johnston 1.192 (PRB) vs Jim Bridger 3.252
  (Green River)** though both are Wyoming PacifiCorp plants. A single NWPP gas
  hub or a per-state coal price is an error the size of the fuel cost.
  **Colstrip and Centralia carry NO measured delivered coal price in any year —
  26.7 % of the footprint's coal capacity, and the entire coal fleet of zones
  INLAND and NW.**

Gate **G12** (LTLF) **passes**: `data/raw/load-forecast/nwpp/nwpp.csv`, edition
`"Participant IRP assembly (2025 cycle)"`, vintage **2025**, 83 rows — but from
**three publishers covering 40.36 % of footprint demand**, with **BPAT (20.26 %)
absent because BPA files no IRP**. Nothing was scaled to close the gap.
