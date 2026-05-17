# Building a Generator-to-Parent-Company Ownership Map for U.S. Electricity Generators

This report synthesizes the data architecture of EIA Form 860, the corporate ownership structure of the largest U.S. generation owners as of the 2025–2026 reporting period, the disclosure conventions in SEC 10-K filings, and the major mergers and acquisitions of 2023–2026 that materially change how individual generators map to ultimate parent companies. The intent is to support an analyst building a clean, defensible mapping table that joins EIA-860 plant/generator records to the correct corporate parent, with a particular eye toward ERCOT and CAISO/WECC.

-----

## 1. EIA Form 860 Ownership Data Structure

EIA Form 860 is the U.S. Energy Information Administration’s annual survey of all existing and planned electric generators with at least 1 MW of nameplate capacity that are interconnected to the local or regional grid.  The annual final-release dataset is distributed as a collection of Microsoft Excel workbooks (.xlsx, since 2004; previously VisualFoxPro DBF through 2003), each containing multiple tabs, plus a separate Layout file that documents every published field.

The dataset is organized into a fixed set of schedules whose filenames follow the pattern `N___ScheduleYyyyy.xlsx`, where `yyyy` is the four-digit reporting year:

- **1___Utility** — utility/owner-level identifiers and contact data
- **2___Plant** — plant-level data (plant code/ORIS code, location, balancing authority, NAICS code, regulatory status, etc.)
- **3_1_Generator** — generator-level data, split into three tabs (Operable, Proposed, and Retired and Canceled).  Wind, solar, multi-fuel, and energy-storage detail tables (3_2 through 3_5) hold technology-specific fields.
- **4___Owner** — the **ownership table**, the linchpin for a parent-company mapping
- **6_1_EnviroAssoc** and **6_2_EnviroEquip** — boiler/environmental control associations and equipment data

### The Ownership Table (Schedule 4 / `4___OwnerYyyyy`)

EIA’s documentation is explicit about how Schedule 4 works:

> *“A generator will appear in this file only if it is a jointly owned generator or if the generator is wholly owned by an entity other than the operator. If the generator is not in this file, then it is 100 percent owned by the operator.”*

This is the single most important design fact for anyone building an ownership map: **the Ownership table is sparse, not comprehensive.** Most generators (those wholly owned by their listed operator) do not appear in Schedule 4 at all. To assemble a complete owner-by-generator table you must:

1. Start from the Generator table (3_1) and take `utility_id` / `operator_id` as the default owner at 100%.
1. **Overwrite** with the Owner table (Schedule 4) wherever a row exists for that `(plant_code, generator_id)` pair — including replacing the operator’s implied 100% share with the actual percentages reported.

### Schedule 4 Fields

The Ownership table publishes one row per (plant, generator, owner) tuple, with the following columns (names normalized across recent vintages):

- `utility_id` (EIA-assigned operator code) and `utility_name`
- `plant_code` (the EIA Plant Code, also called the ORIS code) and `plant_name`
- `state`
- `generator_id` (the plant-management-assigned alphanumeric unit ID, e.g., “1”, “GT1”, “CTG-2A”)
- `status` (operating status code)
- `ownership_id` / `owner_utility_id` (EIA’s ID for the owning entity)
- `owner_name`
- `owner_street_address`, `owner_city`, `owner_state`, `owner_zip`
- `percent_owned` (the owner’s fractional share, expressed as a decimal between 0 and 1)

The sum of `percent_owned` across all rows for a given `(plant_code, generator_id)` should equal 1.0 (allowing for rounding). In practice this needs to be validated row-by-row, because EIA does not enforce summation constraints at survey time.

### How EIA-860 Handles Joint Ownership

Joint ownership is handled at the **generator** level, not the plant level. Each individual generator (a single turbine/unit) is reported with its own ownership shares, which means a single power plant can have different ownership splits across its multiple units (common in older joint-action projects). The Form EIA-860 Instructions explicitly require that *“jointly owned plants must be reported only once by their operator or planned operator”*  — i.e., the operator is the sole respondent and is responsible for listing all co-owners and their percentages.

Joint ownership is extremely common in the U.S. fleet, particularly for:

- Large coal plants in the Midwest and Mountain West (e.g., Intermountain, Craig, Hayden, Colstrip, Jim Bridger, Four Corners, San Juan, Navajo before retirement)
- Nuclear plants (e.g., Susquehanna is 90% Talen / 10% Allegheny Electric Cooperative; Vogtle, Palo Verde, South Texas Project, Diablo Canyon, Comanche Peak historically, etc.)
- Western hydro projects and certain renewable projects with tax-equity structures

For tax-equity-financed renewable projects, EIA-860’s `percent_owned` does **not** capture the typical “HLBO” / partnership-flip economic allocation. EIA usually shows the long-term cash-equity owner (e.g., a NextEra Energy Resources subsidiary) at or near 100%, even when tax-equity partners hold significant Class A interests early in the project life. Analysts who care about beneficial ownership beyond legal/operational ownership must reconcile this against 10-K and project finance disclosures.

### Data Access — Current URL and Format

- **Landing page:** `https://www.eia.gov/electricity/data/eia860/` (lists the most recent final and early-release datasets, plus all historical years back to 1990, and the form instructions and Layout file).
- **Format:** A single ZIP archive per release containing one .xlsx workbook per schedule, plus the Layout (data dictionary) and Form Instructions PDFs.
- **Release cadence:** EIA publishes each year’s data in two rounds — an *early release* in summer (typically June) and a *final release* in the fall (typically September–October).  As of mid-2026, the most recent final release covers reporting year 2024; the early release for reporting year 2025 was the most current at the time of writing. EIA also publishes a separate **Form EIA-860M** (Monthly Update to Annual Electric Generator Inventory) for between-cycle updates — useful for catching newly online or recently retired units but with capacity values that are sometimes retroactively revised and considered less reliable than the annual form. 
- **PUDL (Public Utility Data Liberation) project**, maintained by Catalyst Cooperative, ingests, normalizes, and versions EIA-860 (combined with EIA-923, FERC Form 1, and others) and publishes the cleaned tables under stable names like `core_eia860__scd_ownership`, `core_eia860__scd_generators`, and `core_eia860__scd_plants`. PUDL is generally the easiest entry point if you do not want to manage EIA’s year-to-year schema drift, including renamed sheets and changed column orders. PUDL archives are also mirrored on Zenodo. 

**Important data-quality caveat:** EIA periodically changes spreadsheet naming and column structure without warning between vintages, and older “final” data is sometimes revised years later.  Any production ETL pipeline against raw EIA-860 must be defensive about column-name drift.

-----

## 2. Major Energy Company Fleet Compositions (2025–2026)

The following profiles reflect public 10-K, 8-K, investor-presentation, and press-release disclosures through Q1 2026. Capacity figures are **net generation capacity** (the company’s own pro-rata share where partial ownership exists), unless noted as gross or installed.

### Constellation Energy (NASDAQ: CEG)

Constellation was created as the standalone competitive subsidiary of Exelon in the **February 1, 2022 spin-off** of Exelon Generation. It has historically been the largest U.S. nuclear operator, owning or operating 21 nuclear reactors at the time of spin-off, including the Byron, Braidwood, Dresden, LaSalle, Quad Cities, and Clinton plants in Illinois; Limerick and Peach Bottom in Pennsylvania; Calvert Cliffs in Maryland; Nine Mile Point, Ginna, and FitzPatrick in New York; plus the Salem/Hope Creek complex (jointly owned with PSEG, which is the operator). Pre-Calpine, the Constellation fleet was approximately 32 GW, dominated by nuclear, with a smaller fossil and renewable component.

**Crane Clean Energy Center:** Constellation’s pending recommissioning of the former Three Mile Island Unit 1 (Crane)  under a long-term Microsoft PPA adds about 835 MW of nuclear once it returns to service later this decade.

**Calpine acquisition timeline:**

- **January 10, 2025** — definitive agreement announced; equity purchase price $16.4 billion ($4.5B cash + 50M Constellation shares), plus assumption of ~$12.7B of Calpine net debt;  total effective enterprise value of $26.6 billion. 
- **July 24, 2025** — FERC approval received, the last major federal regulatory hurdle (NYPSC and PUCT had previously approved). 
- **November 21, 2025** — Constellation announced senior leadership changes ahead of the expected Q4 2025 close, contingent on DOJ clearance. 
- **January 7, 2026** — Transaction **closed**. Calpine converted to Calpine LLC and became an indirect wholly owned subsidiary  of Constellation Energy Generation, LLC (the operating entity inherited from the Exelon spin-off).

**Required divestitures:** To satisfy FERC and DOJ, Constellation agreed to divest selected PJM and ERCOT assets to LS Power, including York 2, Hay Road, Edge Moor, and the Jack Fusco Energy Center.  Analysts mapping generators in 2026 must apply these divestitures.

**Combined post-close fleet:** Constellation publicly characterized the combined company as having **approximately 60 GW** of generation capacity, spanning nuclear (the largest in the U.S.), natural gas  (predominantly Calpine’s CCGT fleet, the largest natural-gas generator in the U.S.), geothermal (The Geysers in California, ~725 MW), hydro, wind, solar, cogeneration, and battery storage (including the 680 MW Nova battery project  plus additional storage and solar under construction at Calpine sites). Calpine’s standalone footprint added roughly **28 GW** of mostly gas and geothermal capacity, including a large Texas/ERCOT CCGT and cogen portfolio. 

### Vistra Corp (NYSE: VST)

Vistra is the result of the 2016 emergence of TCEH (the legacy Texas Competitive Electric Holdings business unit of Energy Future Holdings/TXU) from bankruptcy as Vistra Energy, the 2018 merger with Dynegy, and a series of subsequent bolt-ons. Its competitive-generation subsidiaries include **Luminant** (Texas/ERCOT thermal and renewables), the legacy **Dynegy** assets in PJM and MISO, and the former **Energy Harbor** nuclear and retail business in PJM.

**Energy Harbor acquisition** (clarifying the user’s question — **Vistra acquired Energy Harbor, not Talen**):

- FERC approved February 16, 2024. 
- **Closed March 1, 2024.** 
- Added approximately **4,000 MW of nuclear**   at three sites in PJM: Beaver Valley (Pennsylvania), Davis-Besse (Ohio), and Perry (Ohio). Combined with Vistra’s existing 2,400 MW Comanche Peak nuclear plant  in ERCOT, this made Vistra the **second-largest competitive nuclear operator**  in the U.S. behind Constellation, with **~6,400 MW** of nuclear. 
- Energy Harbor was itself the post-bankruptcy successor to FirstEnergy Solutions, FirstEnergy’s former competitive generation subsidiary; this lineage is important when joining historical EIA-860 vintages.

**Lotus Infrastructure Partners acquisition:**

- **Closed October 22, 2025.**
- Added seven natural-gas plants totaling approximately **2,600 MW** across PJM, ISO-NE, NYISO,  and **CAISO** — Vistra’s first material entry into California generation ownership.

**Total Vistra fleet (post-Lotus close):** Approximately **41,000 MW** of installed generation capacity prior to the Lotus deal (as Vistra disclosed at the time of the Energy Harbor close in March 2024),  bringing the post-Lotus total to roughly **43,500 MW**. The mix includes:

- Nuclear: ~6,400 MW (Comanche Peak, Beaver Valley, Davis-Besse, Perry)
- Natural gas CCGT and CT: the largest single component
- Coal: declining, concentrated in Luminant ERCOT plants and former Dynegy MISO/PJM plants (Coleto Creek scheduled to retire in 2027  and be repowered with up to 600 MW  of gas)
- Solar: ~340 MW operating 
- Battery storage: ~1,020 MW (second-largest in U.S.),  including the Moss Landing facility in CAISO (notable for a 2025 fire incident)
- Vistra has also announced new gas peaker buildouts (~860 MW  in West Texas) and a Coleto Creek gas repower under the Texas Energy Fund.

### Talen Energy (NASDAQ: TLN)

Talen Energy emerged from Chapter 11 in May 2023 and re-listed on NASDAQ. Talen’s fleet is concentrated in **PJM** (mid-Atlantic) and ERCOT and is anchored by the **Susquehanna Steam Electric Station** — a two-unit, ~2,475–2,500 MW  BWR plant in Salem Township, PA. Susquehanna is **jointly owned**: Susquehanna Nuclear LLC (a Talen subsidiary) holds 90% and Allegheny Electric Cooperative Inc. holds 10%. This joint ownership shows up in EIA-860 Schedule 4 and is a useful test case for any mapping pipeline.

**Total fleet (per company disclosures):** approximately **13.1 GW** of nuclear, natural gas, oil, and coal-fired generation,  primarily in the Mid-Atlantic and Ohio. Talen also retains partial ownership of the Conemaugh and Keystone coal plants (not Talen-operated;  one of Talen’s reporting carve-outs in its safety metrics).

**Talen did *not* acquire Energy Harbor.** That deal was Vistra’s. Talen’s recent transactions are different:

- **March 2024 sale of the AWS data-center campus** (the “Cumulus” data-center business adjacent to Susquehanna) to Amazon Web Services for ~$650M, plus a co-location/PPA structure for nuclear power supply.
- **June 11, 2025** — Restructured/expanded 17-year PPA with AWS for up to **1,920 MW** of carbon-free electricity from Susquehanna,  contracted “front-of-the-meter” (after FERC rejected the original behind-the-meter interconnection structure in November 2024). Talen expects ~$18 billion of revenue across the contract life; ramp profile is 840–1,200 MW in 2029 and 1,680–1,920 MW in 2032, with the contract running to 2042.
- **July 17, 2025** — Talen announced acquisition of two large H-class CCGTs from **Caithness Energy** (the press release characterizes the added capacity as more than the equivalent of another Susquehanna nuclear plant,  i.e., ~2,500 MW). Closing was pending at the time of the latest 8-K disclosures.

### NextEra Energy (NYSE: NEE)

NextEra is a holding company with two principal operating subsidiaries:

- **Florida Power & Light (FPL):** The largest U.S. electric utility by customer count, serving more than 6 million accounts in Florida. As of December 31, 2025, FPL had **35,963 MW** of net generating capacity, dominated by natural gas with growing solar and battery storage (FPL added 2,235 MW of solar in 2024 and another 894 MW in January 2025). FPL also owns Turkey Point and St. Lucie nuclear plants. A January 2026 Florida rate agreement provides annualized base revenue increases of $945 million in 2026 and $705 million in 2027 with an authorized ROE of 10.95%.
- **NextEra Energy Resources (NEER):** The competitive subsidiary and the world’s largest generator of wind and solar electricity on an MWh basis. As of year-end 2025, NEER had **37,505 MW** of total net generating capacity plus **5,177 MW** of battery storage. Mix is wind, solar, nuclear (Duane Arnold under evaluation for recommissioning; 70% NEER ownership of 615 MW gross; Seabrook in New Hampshire; Point Beach in Wisconsin), some gas, and storage. NEER’s renewables backlog approached 30 GW after Q3 2025 additions. 

**Total NEE consolidated:** approximately **80 GW** of net generation and storage capacity at year-end 2025, with both regulated (FPL) and competitive (NEER) businesses. NEER also operates a sizeable rate-regulated transmission business.

### AES Corporation (NYSE: AES)

AES is a global IPP and U.S. utility holding company. Its disclosed global generation portfolio was **32,109 MW** in the 2024 10-K and **34,740 MW** in the 2025 10-K, with **54% from renewables** in 2025.   The U.S. footprint includes:

- **AES Indiana** (formerly Indianapolis Power & Light, IPL): a vertically integrated utility wholly owned by IPALCO  Enterprises, which is in turn 85% owned by AES with CDPQ holding ~15% (the CDPQ stake came via a 2015 deal).
- **AES Ohio** (formerly Dayton Power & Light):  a distribution utility; AES announced a sale of a 30% indirect interest in AES Ohio to CDPQ for ~$546M in September 2024,  with AES Ohio’s own generation share at approximately 103 MW out of a 2,109 MW combined-ownership facility. 
- **AES Clean Energy** — the U.S. competitive renewables developer/owner, with **10,961 MW operating, 3,031 MW under construction, and a 46 GW development pipeline** as of the 2025 10-K. Many AES Clean Energy projects involve **tax-equity partners** — a common reason EIA-860 ownership records may show 100% AES even when economics differ.
- Internationally: AES Chile (3,685 MW),  Panama, Argentina, Colombia, Dominican Republic.

### NRG Energy (NYSE: NRG)

NRG has progressively pivoted from a pure-play IPP into an integrated retail-and-generation business. Following the 2018 portfolio review that took its fleet from ~50 GW down to ~24 GW,  NRG focused on retail (acquiring XOOM in 2018, Stream Energy in 2019, Direct Energy in 2021, and Vivint Smart Home  in 2023).

**LS Power transaction (announced May 12, 2025):**

- Definitive agreement to acquire a premier LS Power generation portfolio at an enterprise value of approximately **$12.0 billion** ($6.4B cash + $2.8B in NRG stock + $3.2B net debt assumed, less ~$0.4B tax-benefit NPV).
- **Doubles NRG’s generation capacity**,  adding approximately 13 GW of largely natural-gas capacity in the Northeast and Texas, plus a leading C&I Virtual Power Plant platform.
- Expected to close **Q1 2026**, subject to HSR, FERC, and NYSPSC approvals. LS Power would own approximately 11% of pro forma NRG post-close with a 6-month lock-up.

**Rockland Capital deal:** Closed April 10, 2025 — NRG acquired 738 MW of flexible natural-gas combined-cycle peaking capacity in Texas for $560 million (~$760/kW).

Pre-LS-Power, NRG’s existing generation footprint had been ~13 GW heavily concentrated in ERCOT (its former Reliant/Texas Genco legacy fleet, including the Limestone and W.A. Parish plants, plus gas peakers), with smaller positions in New York (Astoria), Connecticut (Middletown), and California.

### Duke Energy (NYSE: DUK)

Duke is a regulated-utility holding company. Total combined electric-utility generation capacity is approximately **55,100 MW**,  distributed across:

- **Duke Energy Carolinas:** ~20,800 MW (NC/SC) 
- **Duke Energy Progress:** ~13,800 MW (NC/SC) 
- **Duke Energy Florida:** large fleet anchored by gas and growing solar (~1,500 MW of solar by end of 2024, with $1.5B planned 2025–2027 in 1,050 MW new solar plus 100 MW storage) 
- **Duke Energy Indiana** and **Duke Energy Ohio/Kentucky:** Midwest fleet
- Combined nuclear fleet includes Catawba, McGuire, Oconee, Robinson, Harris, and Brunswick

Duke is an effectively all-regulated business after the divestiture of its competitive merchant generation. The 2024 NCUC-approved Carolinas Resource Plan calls for 3,460 MW of new controllable solar, ≥625 MW of solar-paired battery storage,  3.6 GW of new gas-fired capacity, plus up to 1,100 MW of additional batteries, 1,834 MW of pumped hydro, and 600 MW of advanced nuclear by 2035. 

### Southern Company (NYSE: SO)

Southern is a holding company over **Alabama Power**, **Georgia Power**, **Mississippi Power**, plus **Southern Power** (the competitive wholesale generation subsidiary; 12,500 MW of solar, wind, gas, and clean-alternative capacity sold under long-term contracts in 15 states), and several gas LDCs (Atlanta Gas Light, Chattanooga Gas, Nicor Gas, Virginia Natural Gas).  **Total generating capacity ~44,000 MW** (as of March 2025 fact sheet). 2024 energy mix: **49% natural gas, 18% coal, 19% nuclear, 14% renewables/other**.  Nuclear fleet includes Plant Vogtle Units 1–4 (the new Units 3 and 4 entered service in 2023 and 2024), Plant Farley, and Plant Hatch. Alabama Power’s Plant Barry Unit 8 (727 MW gas CCGT) came online in 2023. 

### Dominion Energy (NYSE: D)

Dominion operates primarily through **Virginia Electric and Power Company (Dominion Energy Virginia)** in PJM and **Dominion Energy South Carolina** (formerly SCANA, acquired 2019). After a series of divestitures (sale of gas LDCs to Berkshire Hathaway Energy in 2020, sale of West Virginia gas utility, exit of the Cove Point LNG general partner stake, sale of Questar Pipeline to Southwest Gas, etc.), Dominion is now a more focused regulated-utility business. Dominion Energy Virginia’s regulated generation fleet is approximately **22,000–24,000 MW** including the North Anna and Surry nuclear stations, a large gas CCGT fleet, the Bath County pumped storage station (the largest pumped-storage facility in the world at ~3,000 MW, jointly owned with FirstEnergy/Allegheny Power), offshore wind under construction (Coastal Virginia Offshore Wind, 2.6 GW, targeted online 2026), and growing utility-scale solar. (Note: Dominion’s exact total has not been independently confirmed against the most recent 10-K in this research pass; analysts should cross-reference the 2025 10-K filed in early 2026.)

### Berkshire Hathaway Energy (BHE) — private, subsidiary of Berkshire Hathaway

BHE owns and operates a regulated-utility-heavy U.S. portfolio:

- **PacifiCorp:** ~10,556 MW  across Pacific Power (OR, WA, CA) and Rocky Mountain Power  (UT, WY, ID). Mix: 56% coal, 24% natural gas, 10% hydro, 10% renewable. (PacifiCorp has also been the subject of substantial wildfire-related litigation in Oregon since 2020, prompting expanded incremental wildfire insurance coverage.)
- **MidAmerican Energy Company** (Iowa): heavy wind buildout, with 6,598 MW of owned wind as of December 2020 disclosures,  plus gas and coal.
- **NV Energy** (Nevada Power and Sierra Pacific Power): Nevada-based regulated utility.
- **BHE Renewables:** ~3,500 MW of owned wind, solar, and geothermal across the U.S.
- **Northern Powergrid** (UK distribution; no U.S. generation impact).

**Total BHE generating capacity:** approximately **29 GW** across ~5.3 million retail customers.  For EIA-860 mapping purposes, the four U.S. subsidiaries (PacifiCorp, MidAmerican, NV Energy/Nevada Power/Sierra Pacific Power, and BHE Renewables) each appear as separate `utility_id` operators and need to be rolled up to the BHE/Berkshire Hathaway parent.

### American Electric Power (NASDAQ: AEP)

AEP is a vertically integrated regulated-utility holding company with operating subsidiaries in 11 states. As of year-end 2025, AEP’s vertically integrated utilities owned approximately **25,400 MW** of generation. The 2025 generation mix was 43% coal and lignite, 22% natural gas, 19% nuclear  (D.C. Cook, two-unit ~2,100 MW PWR plant, owned by Indiana Michigan Power), and 16% renewables.  Subsidiary operating utilities are: AEP Ohio (T&D-only since the Ohio competitive carve-out), Appalachian Power (APCo), Indiana Michigan Power (I&M), Kentucky Power, Public Service Co. of Oklahoma (PSO), Southwestern Electric Power (SWEPCo), AEP Texas (T&D-only in ERCOT after the 2002 Texas restructuring), and Kingsport Power. AEP plans further coal retirements/fuel conversions, including Welsh Units 1 and 3 to natural gas and a 450 MW Hallsville natural-gas plant at the retired Pirkey site, pending CCN approval. 

### Entergy (NYSE: ETR)

Entergy is a regulated-utility holding company with five operating subsidiaries: **Entergy Arkansas, Entergy Louisiana, Entergy Mississippi, Entergy New Orleans, and Entergy Texas** (all in MISO; Entergy Texas is in MISO South, not ERCOT). Total generating capacity is approximately **24,000 MW**,  consisting of:

- ~19,000 MW across 28 active gas, oil, hydro, and coal plants 
- ~5,000 MW of nuclear  across five reactors at four sites: Arkansas Nuclear One (Units 1 & 2), Grand Gulf (Mississippi), River Bend (Louisiana), and Waterford 3 (Louisiana). Entergy formerly operated competitive merchant nuclear units (Indian Point, Pilgrim, Vermont Yankee, FitzPatrick, Palisades) under Entergy Wholesale Commodities; these have all been retired or divested (FitzPatrick to Exelon/Constellation 2017; Palisades to Holtec 2022; Pilgrim retired 2019; Vermont Yankee retired 2014; Indian Point fully retired 2021).
- ~8,600 MW of renewable energy projects operational or in the pipeline.

### Other Major U.S. Generation Owners to Include (>5 GW)

For a comprehensive parent-company map, the following additional entities own or operate large fleets and should not be omitted:

- **Tennessee Valley Authority (TVA):** federal utility, ~33 GW across nuclear (Browns Ferry, Sequoyah, Watts Bar), gas, hydro, coal, and solar
- **Exelon Corporation (NASDAQ: EXC):** post-2022 spin-off, now a T&D-only holding company (BGE, ComEd, PECO, Pepco, Delmarva, ACE) with no merchant generation
- **PG&E Corporation (NYSE: PCG):** owner of Diablo Canyon (~2.2 GW nuclear, life-extended through 2030), Helms pumped storage, hydro, and Humboldt Bay; ~7 GW total generation, plus large PPA portfolio in CAISO
- **Edison International / Southern California Edison:** primarily a transmission and distribution utility post-San Onofre retirement; ~3 GW of owned generation (some hydro, Mountainview gas, Big Creek hydro complex)
- **Xcel Energy (NASDAQ: XEL):** PSCo (CO), NSP-Minnesota, NSP-Wisconsin, SPS (NM/TX in SPP), ~30 GW including Monticello and Prairie Island nuclear
- **PSEG (Public Service Enterprise Group, NYSE: PEG):** ~3.8 GW of nuclear (Salem Units 1 & 2, Hope Creek) operated by PSEG Nuclear; partial owner of Peach Bottom with Constellation; divested its competitive fossil fleet to ArcLight in 2022
- **Evergy (NASDAQ: EVRG):** ~16 GW across KCP&L and Westar territories (KS, MO), including Wolf Creek nuclear (47% ownership)
- **Ameren (NYSE: AEE):** Callaway nuclear plus gas, coal, renewable; ~10 GW
- **WEC Energy Group, CMS Energy, DTE Energy, FirstEnergy** (now a pure T&D play after divesting FirstEnergy Solutions/Energy Harbor), **Eversource, National Grid, PPL** (sold competitive generation business that became Talen in 2015), **Avangrid** (Iberdrola subsidiary, large U.S. renewables platform), **Iberdrola Renewables**, **EDP Renewables North America**, **Engie North America**, **EDF Renewables**, **Brookfield Renewable Partners**, **Clearway Energy** (publicly traded yieldco, ~9 GW renewable + gas; Global Infrastructure Partners is the sponsor and largest shareholder), **Invenergy** (private, one of the largest U.S. independent renewable developers/owners), **Pattern Energy** (private since 2020 CPPIB acquisition), **TerraForm Power** (now part of Brookfield Renewable), **Algonquin Power**, **Capital Power**, **Innergex**, and **LS Power** itself (still has substantial remaining capacity post-NRG divestiture closing).

For ERCOT specifically, the dominant generation owners (post-2026) will be: **Vistra/Luminant, NRG (post-LS Power), Constellation (post-Calpine, post-divestiture), Calpine assets now under Constellation, Talen Energy (small ERCOT footprint), EDF/Engie/RWE/Ørsted on renewables, Pattern/Invenergy/Clearway on renewables, and many utility-owned generation entities (Lower Colorado River Authority, Austin Energy, CPS Energy of San Antonio, Brazos Electric Cooperative, etc.).** Note that AEP Texas and CenterPoint are T&D-only in ERCOT; they do not own generation.

For CAISO/WECC specifically, the dominant generation owners are: **PG&E, Southern California Edison, San Diego Gas & Electric (Sempra), LADWP, SMUD, NV Energy (BHE), PacifiCorp (BHE), Calpine (now Constellation, particularly The Geysers geothermal and CAISO gas CCGTs), NRG, Vistra (Moss Landing + Lotus assets), AES Clean Energy, NextEra Energy Resources, Berkshire Hathaway Energy Renewables, EDF Renewables, Clearway, Avangrid, Engie, Iberdrola, Brookfield, 8minute Solar Energy, and Recurrent/Canadian Solar/Origis.**

-----

## 3. 10-K Filings and Equity Share Ownership

Major energy companies disclose generation-fleet composition in the **“Properties”** section of Item 2 of Form 10-K (and sometimes in Item 1, Business). The level of detail varies materially across companies, but conventions are reasonably consistent:

**Typical structure of generation disclosures in 10-Ks:**

1. **A “Generating Facilities” table** listing each plant (or sometimes each unit) with:
- Plant name and location (state)
- Primary fuel/energy source
- Year of commercial operation
- Net capacity (MW) — usually disclosed as the **company’s pro-rata share** based on ownership percentage
- Sometimes the ownership percentage explicitly, especially for jointly owned plants
- Operating status (operating, in development, retired)
1. **A “Capacity by Fuel Type” summary** — virtually all major IGOs report this at the segment or consolidated level. Categories typically include natural gas, coal, nuclear, hydro, wind, solar, oil, battery storage, and “other.” Many disaggregate gas into CCGT vs. CT/peaking.
1. **A distinction between owned/operated capacity, PPA (purchased power) capacity, and leased capacity:**
- **Owned:** capacity for which the company holds an equity interest (consolidated on the balance sheet at 100% if controlling; equity-method if minority but significant; otherwise just the proportional MW disclosed)
- **Leased:** historically more common in tax-leveraged-lease structures; now relatively rare
- **Purchased (PPA):** capacity under long-term power purchase agreements. Disclosed separately because the company has dispatch rights but no equity ownership. Some companies (notably Southern Power, NextEra, AES) report a “contracted capacity” or “backlog” figure that combines owned-and-operating with under-construction-and-contracted.
1. **For competitive generators (Vistra, NRG, Talen, Calpine, AES competitive):** disclosures emphasize the integrated retail-and-generation balance, fuel hedging, and ISO/RTO concentration.
1. **For regulated utilities (Duke, Southern, AEP, Entergy, FPL, Dominion, BHE subsidiaries):** disclosures often align to the regulatory ratemaking territory, and pro-rata MW is reported because rate base only includes the utility’s ownership share.

**Cross-referencing 10-Ks with EIA-860 ownership percentages — practical workflow:**

1. **Start from EIA-860 Schedule 4** to get the as-reported `(plant_code, generator_id, owner_utility_id, percent_owned)` tuples, supplemented with the implicit 100%-operator rows from Schedule 3.
1. **Use EIA’s `utility_id` (“respondent ID”)** as the primary join key into a utility-to-parent mapping. EIA’s `utility_id` is fairly stable across years for a given legal entity, but it does not roll up to corporate parents automatically. Build a separate `utility_id_to_parent_company` mapping that handles:
- Multiple utility subsidiaries under one holding company (Duke Carolinas + Duke Progress + Duke Florida + Duke Indiana + Duke Ohio/KY → Duke Energy Corp).
- Joint ventures and consortium operators (e.g., STP Nuclear Operating Company operates South Texas Project on behalf of NRG, CPS Energy, and Austin Energy as owners — the operator is *not* an owner).
- Subsidiary renaming after M&A (e.g., Indianapolis Power & Light → AES Indiana; Dayton Power & Light → AES Ohio; Energy Harbor → Vistra subsidiaries; Calpine → Constellation subsidiary).
- Tax-equity partnership structures, where EIA may show a single LLC owner that masks underlying tax-equity-class ownership.
1. **Reconcile against the 10-K Properties section** to validate the parent-company assignment, especially for jointly owned plants. The 10-K usually states the company’s percentage ownership explicitly for nuclear and large coal joint owners.
1. **Use FERC Form 1 and EIA Form 861** for additional ownership clarity, particularly for regulated entities, and the SEC’s EDGAR “List of Subsidiaries” Exhibit 21 for the corporate-tree structure.
1. **Flag M&A transitions** by date: EIA-860 vintage Y reflects ownership *as of December 31 of year Y*. For deals closed in early or mid-year, EIA may publish under either the old or new parent depending on when the transaction was finalized relative to the EIA filing cycle, with the survey instructions asking respondents to report status as of December 31.

-----

## 4. Recent Major Transactions to Track (2023–2026)

The following transactions materially affect any generator-to-parent map and should be applied as overlays on the latest EIA-860 vintage:

|Transaction                                                |Status                                   |Effective Date               |Capacity Affected                                                                                              |Notes                                                                                                        |
|-----------------------------------------------------------|-----------------------------------------|-----------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
|Constellation/Calpine merger                               |**Closed**                               |**Jan 7, 2026**              |~28 GW (Calpine fleet) joining ~32 GW Constellation = ~60 GW combined                                          |Subject to divestitures of York 2, Hay Road, Edge Moor, Jack Fusco Energy Center to LS Power in PJM and ERCOT|
|Vistra/Energy Harbor                                       |Closed                                   |**Mar 1, 2024**              |+4,000 MW nuclear  (Beaver Valley, Davis-Besse, Perry)                                                         |Energy Harbor was the successor to FirstEnergy Solutions                                                     |
|Vistra/Lotus Infrastructure Partners (7 gas plants)        |Closed                                   |**Oct 22, 2025**             |+2,600 MW gas in PJM/NE/NY/**CA**                                                                              |Vistra’s first CAISO generation footprint                                                                    |
|NRG/LS Power generation portfolio                          |**Pending** (definitive agreement signed)|**Expected Q1 2026 close**   |~13 GW additional (doubles NRG fleet); includes Northeast gas, ERCOT gas, C&I VPP                              |$12B EV; LS Power takes ~11% NRG equity                                                                      |
|NRG/Rockland Capital (Texas gas peakers)                   |Closed                                   |**Apr 10, 2025**             |+738 MW gas CCGT peaking in ERCOT                                                                              |$560M; ~$760/kW                                                                                              |
|Talen/Caithness Energy (H-class CCGTs)                     |Announced/Pending                        |**Jul 17, 2025** announcement|~2,500 MW of modern H-class CCGT in Talen’s key markets                                                        |Closing pending                                                                                              |
|Talen sale of Cumulus AWS data-center campus               |Closed                                   |Mar 2024                     |Real estate / data center, not generation                                                                      |Set stage for AWS PPA                                                                                        |
|Talen-Amazon Web Services PPA (restructured)               |Executed                                 |**Jun 11, 2025**             |Up to 1,920 MW of Susquehanna nuclear output contracted FOB-grid through 2042                                  |$18B revenue NPV; ramp to 1,680–1,920 MW by 2032                                                             |
|Constellation–Microsoft PPA (Crane / TMI-1 recommissioning)|Announced Sep 2024                       |Restart targeted ~2028       |~835 MW nuclear restart                                                                                        |Establishes precedent for nuclear-data-center deals                                                          |
|AES Ohio 30% interest sale to CDPQ                         |Announced Sep 2024                       |$546M                        |Minority interest sale                                                                                         |AES retains controlling interest                                                                             |
|AES Brasil divestiture                                     |Closed Oct 2024                          |$630M for 47.3% interest     |International only; does not affect U.S. ownership map                                                         |                                                                                                             |
|Holtec acquisition of Palisades (and announced restart)    |Closed 2022; restart targeted 2025       |~800 MW nuclear              |Acquired from Entergy; Palisades is the first announced U.S. nuclear restart                                   |                                                                                                             |
|Exelon spin-off of Constellation                           |Closed Feb 1, 2022                       |Pre-window, but foundational |All Exelon Generation nuclear and competitive plants moved to Constellation; Exelon retained T&D utilities only|                                                                                                             |

-----

## 5. Practical Caveats for the Mapping Exercise

1. **Timing mismatch.** EIA-860 final data lags reality by ~9–12 months from year-end. As of May 2026, the most recent final dataset is for reporting year 2024 (final release fall 2025), with reporting year 2025 available in early-release form. This means even the most current EIA dataset does *not yet reflect* the January 7, 2026 Constellation/Calpine close, the October 2025 Vistra/Lotus close, or the pending NRG/LS Power deal — all of which require manual overlays.
1. **Operator vs. owner.** EIA-860 records both an *operator* (the entity legally responsible for running the plant, who is also the EIA respondent) and *owners*. These often differ — particularly for nuclear (e.g., STP Nuclear Operating Company is the operator at South Texas Project but owns no equity), municipal/cooperative jointly owned coal plants, and tax-equity-financed renewables. Any mapping must be explicit about which it represents.
1. **Subsidiary rollups.** EIA’s `utility_id` is at the subsidiary level. The mapping to corporate parent requires manual curation. Public sources for the rollup include the SEC Exhibit 21 (List of Subsidiaries) in each 10-K, FERC Form 1, S&P Capital IQ, and PUDL’s `core_pudl__entity_utility_eia` table (which includes parent annotations for major companies).
1. **Tax-equity ownership is generally invisible in EIA-860.** Renewable projects in particular often have HLBO partnerships in which a tax-equity investor (often a money-center bank, an insurance company, or Berkshire Hathaway Energy) holds the majority of cash flows for the first 5–10 years. EIA-860 typically shows only the long-term cash-equity owner.
1. **Yieldco and infrastructure-fund ownership.** Clearway Energy, Brookfield Renewable, Atlantica Sustainable Infrastructure, NextEra Energy Partners (now part of NEE again after the 2024 LP simplification), and various private infrastructure funds (Global Infrastructure Partners, Brookfield Infrastructure, Stonepeak, KKR, EQT, Macquarie, BlackRock GIP, ECP, ArcLight Capital, etc.) hold large portfolios. EIA-860 records the holding LLC, which can be opaque without an Exhibit 21 / Form D / FERC docket cross-reference.
1. **Divestitures driven by antitrust remedies** (e.g., the Constellation/Calpine FERC and DOJ remedy package selling York 2, Hay Road, Edge Moor, and Jack Fusco to LS Power) need to be applied unit-by-unit. These changes often happen at or near close and may not be reflected in EIA-860 until the following reporting year.
1. **Wholesale vs. retail and trading affiliates.** Some companies (Vistra, NRG, Constellation, Calpine, AES) operate large retail/trading affiliates that *do not own generation* but are sometimes co-located in EIA-861 (the demand-side companion). For a generator-to-parent map, only the generation-owning subsidiaries matter, but it is easy to mis-aggregate by EIN or operator name.

-----

## Summary

The minimum viable workflow for a generator-to-parent-company ownership table is: (1) ingest the latest EIA-860 final and early-release vintages with PUDL or a custom ETL; (2) join Schedule 3 (Generator) with Schedule 4 (Ownership) using `(plant_code, generator_id)`, falling back to 100% operator ownership where Schedule 4 has no row; (3) maintain a hand-curated `utility_id` → `parent_company` lookup; (4) overlay M&A events (Constellation/Calpine close 2026-01-07, Vistra/Energy Harbor close 2024-03-01, Vistra/Lotus close 2025-10-22, NRG/Rockland close 2025-04-10, pending NRG/LS Power and Talen/Caithness closes) as date-effective rules; (5) validate against the Properties section of each major company’s 10-K. As of May 2026, the largest U.S. parent fleets by net capacity are approximately NextEra (~80 GW), Constellation post-Calpine (~60 GW), Duke (~55 GW), Southern (~44 GW), Vistra (~43 GW), AES (~35 GW global; substantially U.S.), TVA (~33 GW), Xcel (~30 GW), Berkshire Hathaway Energy (~29 GW), AEP (~25 GW), NRG post-LS Power (~25 GW pro forma), Entergy (~24 GW), Dominion (~23 GW), and Talen (~13 GW), with significant additional capacity held by publicly traded yieldcos, private infrastructure funds, public power authorities, and cooperatives.