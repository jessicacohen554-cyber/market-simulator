# DWR Bulletin 132-22 — SWP plant characteristic tables (extracted rows)

Row-exact extractions of three tables from the California Department of
Water Resources' annual **Bulletin 132-22, "Management of the California
State Water Project"** (published September 2025; reporting year 2021-22) —
the citation source for the SWP plants' pump-side motor ratings, generating
capacities/design flows, and reservoir volumes in
`constants.CAISO_PS_PLANT_PARAMS` (lane 5, caiso-197,
GATESPEC-caiso195-ps-physical-2026-08-11).

## Provenance

- **Publisher:** California Department of Water Resources (DWR), Bulletin
  132 annual series ("Management of the California State Water Project").
- **Document:** Bulletin 132-22, Chapter 1 "The State Water Project".
- **URL:** https://water.ca.gov/-/media/DWR-Website/Web-Pages/Programs/State-Water-Project/Management/Bulletin-132/Bulletin-132/Files/Bulletin-132-22-090825.pdf
- **Retrieved:** 2026-08-16 via `curl` through the environment's configured
  proxy (HTTP 200, application/pdf, 30 MB, 533 pages). The source PDF is
  NOT committed (30 MB); these CSVs carry the three consumed tables
  row-exactly, and the README + URL is the re-fetch path (the
  nerc-gads-eford corpus pattern).
- **License/access:** public DWR annual bulletin, no login/paywall.

## Extraction (page numbers are the bulletin's own, PDF page = +44)

- `pumping_plants.csv` — Chapter 1, SWP pumping plants table (bulletin
  p.9): `Facility / Number of Units / Normal Static Head (feet) / Total
  Flow at Design Head (cfs) / Total Motor Rating (horsepower)`. Only the
  three pumping-generating plants consumed by the lane are carried (the
  full table lists every SWP pumping plant).
- `power_plants.csv` — Chapter 1, Table 1-4 "Power Plant Characteristics,
  By Facility" (bulletin p.10): generating side (units, head, design flow,
  net dependable and nameplate MW).
- `storage_facilities.csv` — Chapter 1, Table 1-1 "Physical Characteristics
  of Primary Storage Facilities" (bulletin p.7): gross capacity
  (acre-feet) for the five reservoirs the lane's energy bounds consume.
  Table footnotes (carried here for completeness): DWR's share of San Luis
  is 1,062,183 AF (jointly owned with USBR); DWR's share of O'Neill
  Forebay is 29,500 AF. The lane uses GROSS volumes (the GATESPEC §4.1
  more-capability direction), with the shares recorded in the PRECHECK.

## Use

`CAISO_PS_PLANT_PARAMS`: Hyatt/Robie Thermalito/Gianelli `pump_mw` =
motor rating hp × 745.7 W/hp (387.0 / 89.5 / 375.8 MW); `energy_mwh` =
reservoir gross AF × (nameplate MW / design-flow cfs × 0.0826446 AF/h per
cfs). Reproduction arithmetic:
`results/calibration/_caiso197_ps_citations.json`.
