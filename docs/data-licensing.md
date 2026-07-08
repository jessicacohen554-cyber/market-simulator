# Data licensing and redistribution

This repo commits roughly 2.5 GB of downloaded electricity-market, fleet, and
weather data under `data/raw/` (see `data/README.md` for the layout). This
document states, for every source family, who publishes it, what its actual
license/use terms are (with a citable URL), and whether this repo's
committed copies are permitted, attributed, or conditional. It does **not**
delete or move any committed data — see §6 for the two findings that need
owner review before any action is taken.

Method: each source's terms were fetched directly from the publisher's own
site (not inferred from habit), and every `data/raw/` subdirectory was
traced to the source family it actually belongs to via the fetch/curate
script that produces or consumes it (each `data/raw/<dir>/README.md` cites
its specific producing script and, where one exists, the exact upstream
URL). Findings below are dated 2026-07 and should be re-checked if a
publisher's terms page changes.

## 1. U.S. federal government data — EIA, EPA (public domain)

**Applies to:** `data/raw/eia-860/`, `eia-930/`, `eia-930-hourly/`,
`eia-930-interchange/`, `campd-unit-level/`, `campd-facility-level/`,
`campd-outages*.csv`, `campd-unit-outages*.csv`, `fleet-egrid/`, the
EIA-sourced files in `gas-prices/` (`henry_hub_daily.csv`,
`henry_hub_monthly.csv`, `eia_citygate_IL_MI_monthly_2023-2025.csv`), the
EIA-derived rows of `gas_basis_by_iso_month.csv` / `nyiso_zonal_gas_hub.csv`
/ `ercot_zonal_gas_hub.csv` / `miso_zonal_gas_hub.csv`, and
`data/raw/coal-prices/` (EIA Annual Coal Report region/rank f.o.b.-mine
prices + BLS coal PPI — see that directory's own README for the BLS
statutory basis, same public-domain rule, different agency).

- **U.S. government works are public domain** under 17 U.S.C. §105 — this is
  a statutory rule, not a discretionary grant, and covers both EIA and EPA.
- **EIA Copyright & Reuse Policy**: "U.S. government publications are in the
  public domain and are not subject to copyright protection." Users "may use
  and/or distribute any of our data, files, databases, reports, graphs,
  charts, and other information products." Attribution is requested, not
  required. URL: <https://www.eia.gov/about/copyrights_reuse.php> (API terms:
  <https://www.eia.gov/opendata/documentation.php>).
- **EPA Standard Open Data License**: "All data produced by the U.S. EPA is
  by default in the public domain and is not subject to domestic copyright
  protection under 17 U.S.C. § 105." URL:
  <https://edg.epa.gov/epa_data_license.html>. No CAMPD-specific terms page
  exists beyond API rate limits (1,000 req/hr, 500 rows/page) — CAMPD
  inherits the general EPA public-domain policy.
- **eGRID** (fleet-egrid/): EPA's own eGRID FAQ states "eGRID data is
  produced by the United States Environmental Protection Agency (EPA) under
  the public domain and is available for use both non-commercially and
  commercially." URL: <https://www.epa.gov/egrid/frequent-questions-about-egrid>.
- **BLS Producer Price Index** (`coal-prices/bls_coal_ppi.csv`, series
  WPU051 / PCU2121--2121--): the same 17 U.S.C. §105 statutory public-domain
  rule applies to all federal statistical agencies, not just EIA/EPA; BLS's
  own linked-data/API terms state its published data is freely reusable, no
  registration or license required. URL:
  <https://www.bls.gov/developers/api_signature_v2.htm>. **Important
  distinction from §5 below:** this is BLS's *own* index calculation (not a
  third party's data BLS is merely hosting), so it carries none of the NGI
  carve-out risk that flags the gas-price weekly-archive series.

**Redistribution:** **Permitted, no restriction.** Attribution appreciated
but not legally required. This is the largest single share of committed raw
data (EIA-930, EIA-860, CAMPD unit/facility-level CEMS) and it is
unconditionally clear.

**Caveat — EIA's own carve-out.** EIA's copyright policy explicitly excludes
"documents, illustrations, photographs, or other information resources
contributed or licensed by private individuals, companies, or organizations"
that EIA republishes but doesn't own. This matters for §5 below: not
everything displayed on an EIA web page is itself EIA's public-domain work.

## 2. NOAA GHCN weather data (public domain / CC0)

**Applies to:** `caiso-weather/`, `ercot-weather/`, `miso-weather/`,
`neiso-weather/`, `nyiso-weather/`, `pjm-weather/` (all built by
`scripts/fetch_zone_temperature.py` from NOAA GHCN-Daily station records).

- NOAA's AWS Open Data Registry listing: GHCN-Daily is released under
  **CC0-1.0 Universal Public Domain Dedication** — "There are no
  restrictions on the use of the data." URL:
  <https://registry.opendata.aws/noaa-ghcn/>.
- NOAA/NCEI's general policy: "environmental data and information produced
  by NOAA or any Federal agency are available fully and openly to data
  users... These data are in the public domain in the United States." URL:
  <https://www.ncei.noaa.gov/archive>. Attribution to NOAA is requested for
  unaltered reuse; altered data may not be represented as unaltered NOAA
  data (not a legal redistribution restriction).

**Redistribution:** **Permitted, no restriction.**

## 3. ERCOT (MIS reports / 60-day disclosure)

**Applies to:** `ercot/` (2-Day and 60-Day AS/DAM disclosure, NP6-345/346
load-by-zone, NP4-33 ASPLAN, NP6-323 SCED price adders), `ercot-AS/`,
`ercot-hsl/`, `ercot-weather/` is NOAA not ERCOT, `ercot-outages.csv`,
`ercot_electric_power_gas_price.csv`, `ercot_zonal_gas_hub.csv`, the ERCOT
rows of `reference/` (`*ACTUALSYSLOADWZNP6345*.zip`,
`tx-jan-aug23-unit-outages.csv`), `zone-specific-demand/`'s ERCOT files, and
ERCOT's slice of `iso-specific-transmission/` / `capacity-deliverability/`.

- **ERCOT Terms of Use, §5**: "The publicly available contents of this
  website may be used, reproduced, and redistributed, provided that the
  contents are not modified and that you maintain all copyright and other
  notices..." — then an explicit carve-out for raw data: **"Notwithstanding
  the foregoing, raw data provided in public portions of this website may be
  used, reproduced, and redistributed in compilations, charts, and analyses
  without maintaining such notices."** Everything is provided "AS IS" with
  disclaimed warranties. URL: <https://www.ercot.com/help/terms> (API/Data
  Portal terms mirror this: <https://www.ercot.com/help/terms/data-portal>).

**Redistribution:** **Permitted.** ERCOT's own text names exactly this use
case ("raw data... redistributed") without even requiring notices to be
carried. Lowest-risk of the six ISOs.

## 4. PJM DataMiner2 — ⚠️ FINDING FOR OWNER REVIEW

**Applies to:** `ISO-specific-gen-data/` (PJM generation-by-fuel), `PJM-AS/`
(ancillary services / reserve market results), `iso-specific-transmission/`'s
PJM transfer-limit CSVs, `lmp-data/`'s `PJM_<year>_rt_da_monthly_lmps.csv`,
`zone-specific-demand/`'s `PJM<year>_hrl_load_metered.csv`,
`pjm_zonal_gas_hub.csv`'s PJM citygate basis, and (gitignored, not committed)
`pjm-energy-offers/`.

- **PJM DataMiner2 Terms of Use** (the actual signed agreement PDF, §1
  "Permitted Use"): "you may use the Data and the Tools for your internal
  business use or commercial purposes, including publishing and making
  derivatives of the Data. **Members may republish data, however
  non-members are specifically prohibited from republishing data.**" §7:
  PJM asserts the compiled Data/Tools are "an original compilation... trade
  secrets of PJM." URL:
  <https://www.pjm.com/-/media/etools/edatafeed/data-license-agreement-edata-feed-data-miner-2.ashx>
  (linked from <https://dataminer2.pjm.com/> and
  <https://www.pjm.com/markets-and-operations/etools/data-miner-2.aspx>).

**Redistribution:** **Conditional — this is a binding contractual term, not
a copyright notice, and it conflicts with committing bulk DataMiner2-derived
files to a public repository unless this project (or its data-fetching
maintainer) is a PJM Member.** Non-member republication is explicitly
prohibited by name.

**Finding for the owner:** confirm whether the account used to pull PJM
DataMiner2 data (`fetch_pjm_energy_offers.py`, and whatever process produced
the manually-sourced `ISO-specific-gen-data/PJM_*.csv` and `PJM-AS/*`
parquets) is a PJM Member with republication rights. If not, the committed
PJM DataMiner2-derived files (`ISO-specific-gen-data/`, `PJM-AS/`,
`iso-specific-transmission/pjm/`, `lmp-data/PJM_*_rt_da_monthly_lmps.csv`,
`zone-specific-demand/PJM*_hrl_load_metered.csv`) should be reviewed for
removal from the public repo (with the existing fetch/refetch instructions
kept so anyone with their own DataMiner2 access can regenerate them
locally) — **no files have been deleted as part of this documentation pass**;
this is flagged for a decision, not acted on. PJM data intaken from EIA-930
directly (which is EIA's own public-domain republication, not a DataMiner2
pull) is unaffected — see §1.

## 5. Gas price series — ⚠️ split verdict, one subset flagged

**Applies to:** `gas-prices/`.

Tracing each committed file to its actual source (via each fetch script's
own docstring):

| File | Actual source | Status |
|---|---|---|
| `henry_hub_daily.csv`, `henry_hub_monthly.csv` | EIA series `RNGWHHD`, EIA API v2 | Public domain (§1) |
| `eia_citygate_IL_MI_monthly_2023-2025.csv` | EIA series `N3050IL3`/`N3050MI3`, EIA API v2 | Public domain (§1) |
| `algonquin_citygate_daily.csv`, `caiso_citygate_daily.csv`, `transco_z6_ny_daily.csv`, `transco_z6_iroquois_monthly.csv` | **NGI's Daily Gas Price Index** (Natural Gas Intelligence, a Hart Energy brand) | See below |

EIA's own Natural Gas Weekly Update page
(<https://www.eia.gov/naturalgas/weekly/>) displays a "Spot Prices
($/MMBtu)" table (Henry Hub / New York / Chicago / California Composite
Average) captioned **"Source: NGI's Daily Gas Price Index."** This project's
own `scripts/fetch_caiso_citygate_daily.py` independently confirms the same
fact in its docstring ("the same free daily print... NGI Daily GPI compiled
by Bloomberg"). EIA is displaying, not republishing as its own — this is
precisely the third-party carve-out EIA's copyright policy names (§1). NGI's
own site (<https://www.naturalgasintel.com/services/daily-gpi/>) is a
subscription product with its own copyright notice; no redistribution grant
for this data was found.

**Redistribution:** Henry Hub and the EIA-native citygate series are public
domain. **`algonquin_citygate_daily.csv`, `caiso_citygate_daily.csv`,
`transco_z6_ny_daily.csv`, and `transco_z6_iroquois_monthly.csv` are a
proprietary third-party index (NGI's Daily Gas Price Index) republished via
a free EIA display page, not released into the public domain by its actual
owner (NGI/Hart Energy).** `nyiso_downstate_ct_gas_basis_monthly.csv` and the
NEISO rows of `gas_basis_by_iso_month.csv` inherit the same concern — the
NYISO downstate basis is derived in part from `transco_z6_iroquois_monthly.csv`,
and `scripts/fetch_eia_gas_prices.py`'s own docstring already flags the
NEISO AGT index as "ISO-NE's licensed... index" (see §7).

**Finding for the owner:** confirm with NGI/Hart Energy whether EIA's
free display implies a redistribution grant (unlikely on the terms found),
or treat these four files as not-redistributable and keep them gitignored /
locally-fetched-only going forward (they already regenerate from the
existing `fetch_algonquin_daily_spot.py` / `fetch_transco_daily_spot.py` /
`fetch_caiso_citygate_daily.py` / `fetch_nyiso_gas_narrative.py` scripts, so
removing the committed copies loses nothing but convenience). **No files
have been removed as part of this documentation pass.**

## 6. CAISO OASIS — terms unclear, needs owner review

**Applies to:** `caiso-curtailment/`, `caiso-hsl/`, `lmp-data/CAISO/`,
`zone-specific-demand/CAISO/`, CAISO's slice of `capacity-deliverability/`.

- **CAISO Privacy & Terms of Use**: "CAISO owns all right, title and
  interest in and to the CAISO API and CAISO Data" (defined broadly as "any
  and all data and other intellectual property in which CAISO may claim
  proprietary rights"). Redistribution of website materials is barred
  "except (i) as authorized in these Terms of Use, (ii) as expressly
  authorized in the materials... or (iii) as expressly authorized in writing
  by the California ISO." A separate clause notes some materials are "freely
  available for public use consistent with the... Public Records Act" with
  attribution, but this carve-out is not explicitly tied to OASIS market
  data in the text found. URL: <https://www.caiso.com/privacy-terms-of-use>.

**Redistribution:** **Unclear / conditional.** No OASIS-specific clause was
found plainly permitting bulk redistribution of raw market data (unlike
ERCOT's explicit raw-data carve-out). California's Public Records Act
generally favors public availability of ISO market data, which weighs
toward lower risk than PJM's explicit ban, but this is not confirmed by the
ToU text itself. **Needs direct confirmation from CAISO** (e.g., via their
customer/stakeholder contact channel) before asserting a redistribution
right; until then, treat as conditional.

## 7. NYISO, ISO-NE, MISO — terms unclear or unverified

**NYISO** (`NYISO/`, `NYISO-AS/`, `lmp-data/NYISO/`,
`zone-specific-demand/NYISO/`, NYISO's slice of `capacity-deliverability/`
and `confirmed-retirements/`): NYISO's Legal Notice
(<https://www.nyiso.com/legal-notice>) is a JavaScript single-page app whose
full text could not be cleanly retrieved by automated fetch — treat the
following as **partially unverified**. Confirmed language: "Access to this
Web site does not confer any license or ownership interest... and the NYISO
hereby expressly reserves such rights and property in its entirety," plus a
narrower confirmed ban on redistributing images/video as stand-alone files.
No clause explicitly permitting or forbidding bulk redistribution of
tabular market data was located. NYISO publishes these reports under
FERC-tariff public-disclosure obligations, which favors public
consumption, but that is not the same as an explicit license.
**Recommend a manual (human, browser) visit to
<https://www.nyiso.com/legal-notice> to get the current full text before
treating this as resolved.**

**ISO-NE** (`neiso-weather/` is NOAA not ISO-NE; NEISO's slice of
`lmp-data/NEISO/`, `confirmed-retirements/`, `winter-fuel-inventory/isone/`):
ISO-NE's Legal and Privacy page (<https://www.iso-ne.com/legal-privacy>)
states "The Content is protected by copyright under United States laws. Any
duplication of the Content or non-personal use may violate copyright,
trademark, and other laws," and requires emailing `info@iso-ne.com` for
permission to reuse any graph/chart/image. No carve-out for raw market data
tables was located. This project's own code already treats one ISO-NE-
adjacent gas index as licensed (see §5's AGT note) — consistent with leaning
restricted here. **Needs direct confirmation from ISO-NE** before treating
ISO-NE-original data as freely redistributable.

**MISO** (`miso-pra/`, `miso-wind-shape/` is NASA POWER not MISO,
`miso-weather/` is NOAA not MISO, `lmp-data/MISO/`, MISO's slice of
`capacity-deliverability/` and `confirmed-retirements/`): both MISO terms
pages (`misoenergy.org/meet-miso/legal-and-privacy/` and
`.../terms-and-conditions/`) returned HTTP 403 to automated fetch —
**UNVERIFIED, needs a manual (human, browser) check.** Search-indexed
snippets show a copyright claim over site materials and a ban on automated
scraping (relevant since MISO's own site access has repeatedly 403'd this
project's fetch scripts too — see `miso-hsl/README.md` and
`miso-pra/SOURCES.md`). Do not assume redistribution permission for
MISO-original data pending that manual check.

**Redistribution verdict for all three:** **Terms unclear — flagged for
owner review, not acted on.** Unlike ERCOT (explicit permission) and PJM
(explicit denial), NYISO/ISO-NE/MISO's own market/planning data has no
clearly located clause either way. This is lower urgency than the PJM and
NGI findings above (no explicit prohibition was found), but should be
resolved with a direct manual check of each ISO's current terms page,
or by contacting each ISO's stakeholder-relations channel, before this
document can respond "yes" instead of "unclear."

## 8. Hand-curated / derived-from-public-filings data

**Applies to:** `confirmed-retirements/`, `capacity-deliverability/`,
`winter-fuel-inventory/`, `miso-pra/`, `miso-wind-shape/` (NASA POWER, CC0 /
public-domain-equivalent per NASA's open data policy), `_processed-legacy/`,
`_validation-source/`, `reference/`.

These directories are model-side derived artifacts or hand-transcribed
extracts from primary public documents (court dockets, PUC/FERC filings,
ISO planning-report PDFs, statute text) rather than bulk downloads of a
single licensed data product. Each cites its specific primary-document
source inline (see each directory's own README, e.g.
`confirmed-retirements/README.md`'s per-row docket citations). Public court
filings, PUC/FERC dockets, and government-statute text are public records;
NASA POWER data is public-domain per NASA's open-data policy
(<https://www.nasa.gov/nasa-brand-center/images-videos/>, "NASA content...
is generally not subject to copyright"). No redistribution concern was
identified for this category.

## Summary table

| Source family | Redistribution | Confidence |
|---|---|---|
| EIA / EPA (EIA-860/923/930, CAMPD, eGRID, coal-prices ACR) | Permitted, public domain | High |
| BLS (coal PPI, `coal-prices/bls_coal_ppi.csv`) | Permitted, public domain | High |
| NOAA GHCN weather | Permitted, public domain (CC0) | High |
| ERCOT MIS / 60-day disclosure | Permitted (explicit raw-data carve-out) | High |
| **PJM DataMiner2** | **Conditional — non-members barred; owner review needed** | High |
| **NGI-sourced gas price series** (Algonquin, Transco Z6, CAISO composite, NYISO/NEISO basis) | **Proprietary third party; owner review needed** | High |
| CAISO OASIS | Unclear/conditional; needs direct confirmation | Medium |
| NYISO | Unclear; ToU text partially unverifiable by automated fetch | Low — manual recheck needed |
| ISO-NE | Unclear, leans restricted; needs direct confirmation | Medium |
| MISO | Unverified; ToU pages blocked automated fetch | Needs manual check |
| Hand-curated from public filings (retirements, capacity-deliverability, winter-fuel) | Permitted (public records) | High |

**No data has been deleted, moved, or altered as a result of this
document.** The two highest-priority findings — PJM DataMiner2's explicit
non-member republication ban, and the NGI-sourced subset of `gas-prices/` —
are flagged above for the repo owner's decision, per this lane's scope
(document, don't act). The three "unclear" ISOs (CAISO, NYISO, ISO-NE) and
MISO's unverified status are lower-urgency but should be resolved with a
manual terms-page check before this doc can upgrade them to a firm verdict.
