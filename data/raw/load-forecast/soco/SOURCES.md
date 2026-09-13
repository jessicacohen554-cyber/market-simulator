# SOCO load-forecast source — Georgia Power "Budget 2025" (B2025), 2025 IRP

Landed **2026-09-13** by lane SOCO-12 (`docs/handoffs/FINDING-soco-12-2026-09-13.md`;
`docs/multi-iso/soco-addition-plan-2026-09.md` §6 row 7). This row is a **W2
precondition** — plan gate **G12**, "`load_forecast/soco.py` cannot register
without a real edition/vintage". It is met:

| Field | Value |
|---|---|
| **edition** | **`Budget 2025 (B2025) / 2025 IRP`** |
| **vintage** | **2025** — filed with the IRP on **2025-01-31** |
| horizon | 2025 → 2044 (a 20-year forecast, stated as such) |
| default_basis | `net` for the peaks (see "Basis" below) |
| metrics | `winter_peak_mw`, `summer_peak_mw`, `energy_gwh` — 20 years each, **60 rows** |

The forecast document names itself: *"In support of the 2025 Integrated Resource
Plan ('IRP'), this document presents the **Budget 2025 Load and Energy Forecast**
('Budget 2025' or 'B2025'). A twenty-year forecast of energy sales and peak
demand was developed to meet the planning needs of Georgia Power Company … The
baseline forecast was started in the spring of 2024 and completed in the fall of
2024."* (Technical Appendix Volume 1, §1 "Executive Summary Overview".)

## Source and re-fetch

Everything here is inside **one public filing**:

- Georgia PSC **Docket No. 56002**, Georgia Power Company's 2025 Integrated
  Resource Plan. Docket index:
  `https://psc.ga.gov/search/facts-docket/?docketId=56002`
- Document **221233** "2025 Integrated Resource Plan PD", filed **2025-01-31**:
  `https://psc.ga.gov/search/facts-document/?documentId=221233`
- Payload (103,717,722 bytes, `2025_irp_public_disclosure.zip`, sha256
  `d72ddb87723475599f575acbef01438b08f5aacdf712e5f8fcb653d3ff9cbe6a`):
  `https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/221233/102406`
- The **numeric** rows come from the zip member
  `Technical Appendix Volume 2 PUBLIC DISCLOSURE/2 Resource Mix Study PUBLIC
  DISCLOSURE/GPC and System IRP Summary Data - 2025 IRP PUBLIC DISCLOSURE.xlsx`,
  sheets `Summary - Winter`, `Summary - Summer` (block "Net Load (MW)", column
  GPC) and `Energies` (column GPC).
- The **narrative** source-of-record is the zip member
  `Technical Appendix Volume 1 PUBLIC DISCLOSURE/1 Load and Energy Forecast
  PUBLIC DISCLOSURE/B2025 Load and Energy Forecast PUBLIC DISCLOSURE.docx`,
  transcribed to `../../soco-planning/transcriptions/B2025_Load_and_Energy_Forecast.txt`.

The docket JSON API needs an XHR header; the exact call is recorded in
`../../soco-planning/SOURCES.md`. Re-fetch the zip and re-cut the two sheets to
regenerate this CSV. Public record (Georgia PSC).

## Three properties of the source a consumer would otherwise have to infer

**1. The area is GEORGIA POWER, not SOCO — and that is not a substitute.**
`area` is `Georgia Power Company`, `area_type` `planning_area`. The workbook
carries a **System** column beside every GPC column — the Southern Company System
(the IIC companies: Alabama Power, Georgia Power, Mississippi Power and the IIC
portion of Southern Power, i.e. the SOCO footprint) — and in the public
disclosure **every System cell is `REDACTED`**, in all four summary sheets and in
`Energies`. The single exception, and it is a valuable one, is the **Target
Reserve Margin** column, which is public for BOTH GPC and System; those values are
transcribed in `../../soco-planning/README.md` §2, not here (a reserve margin is
not a load-forecast metric).

So this datatype covers roughly **half the footprint by peak** and the other half
is not publicly forecast. Two things follow, and neither is patched here:
(a) a SOCO-wide forward peak must be built by the consumer, declared as a
construction, from GPC plus whatever Alabama Power and Mississippi Power evidence
exists (`../../soco-planning/README.md` §5 records that **Alabama Power files no
public IRP at all**); (b) the measured SOCO-wide peak **history** does exist and
is much better evidence — Southern Company's Form 10-K publishes the system
maximum demand and its date every year (README §3). Nothing in this file is
scaled, grossed-up or extrapolated to the footprint.

**2. Basis is `net`, and the publisher says so.** The peaks are the workbook's
"Net Load (MW)", which is net of the Company's demand-side resources; the B2025
document states the peak forecasts *"include the impacts of electric vehicles and
behind-the-meter solar. In addition, external adjustments have been made to
reflect the impacts of new large load customers, cogeneration, and the impacts of
Company-sponsored Demand Side Management ('DSM') programs."* The `Energies` sheet
draws no net/gross distinction, so those rows carry `unspecified` — the datatype's
honest label for exactly that case, never a silent default onto `net`.

**3. The published case is `MG0` (mid).** The workbook ships two DSM cases, `MG0`
and `111-MG0`; **their Net Load series are byte-identical in every year** (checked
cell by cell at intake — 0 differences in both seasons), so the case choice moves
no load row. `MG0` is carried because it is the sheet the IRP's own summary
tables lead with. The two cases diverge only in the *capacity* columns from 2036,
which this datatype does not carry.

## The one unit correction — declared, with the anchor that forces it

The `Energies` sheet's header reads **"Energies (GWh)"** and its 2025 GPC cell
reads **95,293,917.6**. Those cannot both be right: 95.3 million GWh is ~2.5× total
US annual generation. The cells are **MWh**; the header label is wrong by a factor
of 1,000. The anchor is inside the same filing — B2025 §1.2.1: *"Budget 2025
anticipates an average growth of **7,900 GWh each year** from 2024-2034."* Read as
MWh, the workbook's 2025→2034 step is (174,043.1 − 95,293.9) GWh ÷ 9 = **8,750
GWh/yr**, the same order as the narrative (the small gap is expected: the
narrative is retail *territorial sales*, the workbook is total *requirements*).
Read as GWh it would be 8,750,000 GWh/yr — off by exactly the factor named.

This CSV therefore carries **published-cell ÷ 1000, labelled `gwh`**, and every
affected row says so in its own `source_page`. Rule 14 `[R-ACCURATE]`: the real
data is used, with the misalignment documented in place rather than buried. A
consumer wanting the raw cell can recover it by multiplying by 1,000.

## Rule 13 `[R-MEASURED]` posture

The package's, unchanged: a forward-looking **published input** that regenerates
from the next Budget vintage (B2022 and the 2023 IRP Update are the two prior
editions of this same series, both named in B2025 §1.1 and both re-fetchable from
Georgia PSC dockets 44160 and 55378) and responds to changed conditions. Never a
measured outcome, never a target a model output is pinned to. The historical
peaks quoted in `../../soco-planning/README.md` §3 are a **separate** measured
series and are deliberately NOT written into this datatype as `scenario="actual"`
rows, because they are Southern-Company-System totals while every row here is
Georgia Power — mixing the two areas under one metric is the error this note
exists to prevent.

## Follow-ups for whoever registers `scripts/lib/load_forecast/soco.py` (SOCO-20)

1. `default_basis="net"` matches the peak rows; the energy rows carry
   `unspecified` explicitly, so the spec default never reaches them.
2. There is **no `component="data_center"` row**, deliberately. B2025 isolates a
   large-load *external adjustment* (§1.1, §7) but publishes the pipeline as
   announced-MW figures (24,300 MW of economic-development pipeline through the
   mid-2030s, of which 7,300 MW committed), not as a forecast component in the
   summary workbook. `large_load` rows could be added from B2025 §7 by a lane
   willing to read the figures; SOCO-12 did not, because the numbers there are
   chart-borne.
3. An **hourly** Georgia Power load profile for 2021, 2022 and 2023 ships in the
   same zip (`1 Load and Energy Forecast PUBLIC DISCLOSURE/Hourly Load Profile
   Data.xlsx`; 2023 sheet carries 8,748 hourly values, max 16,720.166 MW). That is
   a **measured zonal load series** and is SOCO-11/SOCO-32's input, not this
   datatype's — flagged here so it is not missed.
