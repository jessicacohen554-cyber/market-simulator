# `load-forecast` — raw sources

The **published** long-term load forecast each ISO/RTO issues, as the immutable
source files it was published in. This directory is the provenance root for the
`load-forecast` curated datatype
(`data/dictionary/schema/load-forecast.schema.yaml`, curated by
`scripts/data/curate_load_forecast.py`), and it exists so that the model's
load-growth, data-centre and electrification constants are **derived from a
tracked series** rather than hand-transcribed into a comment.

Opened 2026-09-06 by lane **SCN-LOAD** under owner ruling **S4** (card D-4,
`docs/handoffs/scenario-desk-ledger-2026-09.md` §2): *fund the full datatype —
all six published sources*. The gap list it closes is
`docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §4 (G-D4-1 … G-D4-5); the closure
is scored in `docs/handoffs/FINDING-scn-load-2026-09-06.md` against the
prediction in `docs/handoffs/SCOPE-scn-load-2026-09-06.md`.

**Never modified in place.** A new forecast vintage is a NEW file (a new
`edition`/`vintage` in the curated frame), never an edit to one of these.

## Layout

```
data/raw/load-forecast/
  <iso>/                     ercot | caiso | pjm | miso | nyiso | neiso
    <published workbook>     the ISO's own file, byte-identical to the download
    <iso>.csv                the unified CSV (see below), where a source is not
                             machine-readable and its tables were transcribed
    README.md                per-ISO source table + URLs, where one is needed
```

Two intake routes, and each ISO uses whichever its publisher's format allows:

- **Native parse (preferred).** The curation script opens the ISO's own
  `.xlsx` with `openpyxl` (a project dependency) and reads the published table
  directly. A vintage refresh is then *drop in the new workbook and re-run*.
  **ERCOT, CAISO, PJM and NEISO are native.**
- **Unified CSV (transcription).** Where the ISO publishes only a PDF or a
  slide deck, the needed tables are transcribed **once** into `<iso>.csv` with
  the canonical columns, every row carrying `source_doc` + `source_page`, and
  the source document stays here as the provenance record. **NYISO and MISO are
  transcription**, plus the two ERCOT quantities that live only in the
  `.xlsb` (see below). This is the repo's existing convention for publication
  PDFs (`data/raw/NYISO/README.md`: *"transcription sources, not machine
  inputs"*), and it is what keeps the curation script free of a PDF or `.xlsb`
  parser dependency.

Every transcription was produced by machine extraction and **validated against
a number the publication itself prints** before being written — the per-row
`source_page` names the table or slide, and the validations are listed per ISO
below.

## Sources, per ISO

### ERCOT — 2025 Long-Term Load Forecast (posted 2025-04-08)

ERCOT's LTLF page (<https://www.ercot.com/gridinfo/load/forecast>) still lists
**2025** as the current long-term vintage.

| file | source URL | tracked? |
|---|---|---|
| `2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx` | <https://www.ercot.com/files/docs/2025/04/08/2025-ERCOT-Monthly-Peak-Demand-and-Energy-Forecast.xlsx> | yes |
| `ERCOT-Peak-Demand-Scenarios.xlsx` | <https://www.ercot.com/files/docs/2025/04/08/ERCOT-Peak-Demand-Scenarios.xlsx> | yes |
| `Summer-and-Winter-Peaks.xlsx` | <https://www.ercot.com/files/docs/2025/04/08/Summer-and-Winter-Peaks.xlsx> | yes |
| `ErcotAdjustedForecast.xlsb` (48.4 MB) | <https://www.ercot.com/files/docs/2025/04/08/ErcotAdjustedForecast.xlsb> | **NO — gitignored payload** |
| `2025_LTLF_Report.docx` (methodology narrative, no values consumed) | <https://www.ercot.com/files/docs/2025/04/08/2025_LTLF_Report.docx> | not held |

**Two published cases, and they are not a low/mid/high band:** *ERCOT Adjusted*
is ERCOT's own vetted/derated forecast (the central case) and *TSP Provided* is
the un-derated forecast as the transmission service providers reported it (an
upper case). ERCOT publishes **no low case**.

**DATA NEEDED / recovery — `ErcotAdjustedForecast.xlsb`.** The payload is
untracked at tip (corpus idiom, `.gitignore`); `SHA256SUMS.txt` here is the
committed provenance record and **recovery is re-fetch only**:

```
curl -o data/raw/load-forecast/ercot/ErcotAdjustedForecast.xlsb \
  https://www.ercot.com/files/docs/2025/04/08/ErcotAdjustedForecast.xlsb
sha256sum -c data/raw/load-forecast/ercot/SHA256SUMS.txt
```

It is an hourly 8760 × 2025–2044 × 8-weather-zone × 21-component forecast
(`base_economic_<zone>`, `<zone>_ev`, `<zone>_pv`, `<zone>_lfl_forecast`,
`<zone>_contracts`, `<zone>_officer_letters`, `<zone>_net`). Nothing in the
model reads it: the two quantities consumed are curated out of it into tracked
CSVs here, both regenerable from the payload with
`scripts/data/curate_load_forecast.py --rebuild-ercot-xlsb` (which needs the
payload and the `pyxlsb` reader; the committed CSVs make it optional).

- `ercot.csv` — annual per-weather-zone **large-load peak MW**
  (`<zone>_contracts + <zone>_officer_letters`, annual max of the hourly sum;
  these are the TSP-attested Large Load additions, ~73 % data centres per the
  Dec-2025 ERCOT Board System Planning update Item 16.2) and annual per-zone
  **EV energy GWh** (`<zone>_ev`). *Validation:* the 2030 per-zone large-load
  peaks reproduce the aggregation behind `constants.DATACENTER_ZONE_SHARE`
  ["ERCOT"] to within rounding — 52,304 MW here vs the 52,306 MW recorded in
  `FINDING-scn-ws4a-2026-09-05.md`.
- `ercot_ev_hourly_profile_2030.csv` — the normalized 8,760-hour ERCOT-system EV
  charging shape (`ercot_ev`, forecast year 2030, divided by its own annual
  total, so it sums to 1.0). This is the citable hourly shape that lets the
  `ev` electrification layer arm for ERCOT.

### CAISO — CEC California Energy Demand 2025-2045 (2025 IEPR, adopted 2026-01-21)

| file | source URL |
|---|---|
| `CED2025-Baseline-TotalState.xlsx` | <https://efiling.energy.ca.gov/GetDocument.aspx?tn=268179-9&DocumentContentId=105226> |
| `CED2025-Baseline-PGE.xlsx` | <https://efiling.energy.ca.gov/GetDocument.aspx?tn=268179-5&DocumentContentId=105222> |
| `CED2025-Baseline-SCE.xlsx` | <https://efiling.energy.ca.gov/GetDocument.aspx?tn=268179-6&DocumentContentId=105223> |
| `CED2025-Baseline-SDGE.xlsx` | <https://efiling.energy.ca.gov/GetDocument.aspx?tn=268179-7&DocumentContentId=105224> |
| `CED2025-Form-1-1c-DataCenters.xlsx` | <https://efiling.energy.ca.gov/GetDocument.aspx?tn=268504&DocumentContentId=105649> |

Forms consumed: **1.2** (Total Energy to Serve Load, GWh), **1.5** (Historical
and Extreme Temperature Non-coincident Peak Demand, MW — the 1-in-2 column is
the planning case), and **1.1c** (Electricity Deliveries to End Users by Agency,
GWh — **Data Centers Only**).

**The CAISO footprint is `PGE + SCE + SDGE`**, not Total State: LADWP, IID,
SMUD, BUG and NCNC are outside the CAISO balancing authority. The curated frame
carries all four areas (three planning areas + the statewide row) and the
constants are derived from the three-utility sum, with the misalignment
documented (rule 14's named exception: the published boundary is the CEC
planning area, not the CAISO BAA, and Form 1.5 peaks are **non-coincident**, so
their sum slightly exceeds a coincident CAISO peak).

**Form 1.1c publishes TWO data-centre scenarios**, which is what closes the
`DATACENTER_ADDITIONS_MW["CAISO"]` `high := mid` gap: the *Planning Forecast*
allocation (the adopted central case) and the *Local Reliability Scenario*
allocation (materially higher — the case CPUC RA and CAISO local studies use).

**Not published:** a low/mid/high **demand-growth** band. The CED's scenario
axis is over load *modifiers* (AAEE/AAFS/AATE, BTM PV and storage, known loads),
not over economic growth, so CAISO's low/high growth rates stay a documented
band rather than a published series.

### PJM — 2026 Load Forecast Report (posted 2026-01-14)

| file | source URL |
|---|---|
| `2026-load-report-data.xlsx` | <https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report-data.xlsx> |
| `total-load-adjustments-breakdown.xlsx` | <https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/total-load-adjustments-breakdown.xlsx> |

The report PDF (<https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.pdf>,
8.8 MB) is the narrative; every value consumed is in the two workbooks, so it is
not held here.

- `2026-load-report-data.xlsx` — monthly `PEAK_MW` + `ENERGY_GWH` per PJM zone
  and for `PJM_RTO`, **2026–2046**. Annualized by the curation script (energy =
  sum over months, peak = max over months).
- `total-load-adjustments-breakdown.xlsx` — **this workbook IS Table B-9b**, the
  table the D-4 gap list records as never read: *"Total Adjustments to Summer
  Peak Load (MW) for Each PJM Zone and RTO (2026 - 2046)"*, per zone and
  sub-area. Per the report's own §"Load Adjustments", every adjusted zone is
  adjusted for *"growth in data center load"*, with DOM additionally carrying a
  voltage-optimization program, PS additionally port electrification, and EKPC a
  peak-shaving program (EKPC's row is zero throughout).

**Not published:** a low/mid/high band — PJM issues one forecast.

### NYISO — 2026 Gold Book (Load & Capacity Data Report, April 2026)

**The source document is NOT duplicated here.** It already lives at
`data/raw/NYISO/2026-Gold-Book-Public.pdf` as a gitignored corpus payload with
its verified re-fetch URL and `SHA256SUMS.txt` record in
`data/raw/NYISO/README.md`; it was re-fetched and its sha256 re-verified
byte-exact on 2026-09-06 (`43865c1c…b908bf`). `nyiso.csv` here cites that path.

Tables transcribed into `nyiso.csv`, each validated:

| table | content | validation |
|---|---|---|
| **I-1a** (p.17) | NYCA annual energy GWh + summer peak MW + winter peak MW, **Lower / Baseline / Higher**, 2026–2056 | the derived 2026→2031 CAGRs reproduce the edition's own printed CAGR block (−0.16 % / 1.18 % / 2.58 % energy) exactly |
| **I-11b** (p.48) | Electric Vehicle Annual Energy Usage, GWh, by zone A–K, 2026–2056 ("Total Cumulative Impacts") | zone sum equals the published NYCA column in all 31 years |
| **I-13a** (p.54) | Building Electrification Annual Energy Usage, GWh, by zone A–K, 2026–2056 ("Cumulative **Future** Impacts") | zone sum equals the published NYCA column in all 31 years |
| **I-14** (p.59) | Large Load Forecast, annual energy GWh by zone A–K, 2026–2041 | zone sum equals the published NYCA column in all 16 years |

Note on I-14: it is a **large-load** forecast, not a data-centre-only one (Zone C's
ramp is the Micron fab, a semiconductor plant), and the Gold Book states these
values are *already embedded* in the baseline energy and peak forecasts — which
is the same convention the model's DC block assumes when it *relocates* rather
than adds.

### NEISO — ISO-NE 2026 CELT Report (2026-05-01)

| file | source URL |
|---|---|
| `2026_celt.xlsx` | <https://www.iso-ne.com/static-assets/documents/100035/2026_celt.xlsx> |

Sheets consumed: **1.5.1 Peak Loads** and **1.5.2 Energy** (annual net/gross
summer peak, winter peak and net energy for load, 2025 actual + 2026–2035
forecast, with ISO-NE's own printed CAGRs) and **1.7 Electrification Forecast**
(annual energy GWh, summer peak MW and winter peak MW for **Transportation** and
**Heating** electrification, by state and New England total, 2026–2035).

The two standing component decks are the CELT's own linked sources and are not
held here (every value consumed is in sheet 1.7):
<https://www.iso-ne.com/static-assets/documents/100034/heatfx2026final.pdf> and
<https://www.iso-ne.com/static-assets/documents/100034/transfx2026final.pdf>.

**DATA NEEDED — the EV hourly charging shape.** The TEF deck publishes the
hourly charging allocation only as **charts** (slides 19–20, "Allocation of
Hourly Charging by Month"), and sheet 1.7 stops at annual/seasonal. So NEISO's
`ev` adoption anchors are curated but the layer cannot arm: a shape that cannot
be cited is not a parameter (rule 5 `[R-NO-MAGIC]`; the layer registry in
`market_sim.data.datacenter` is fail-closed by design).

**Not published:** a low/mid/high growth band. CELT sheet **1.6 Forecast
Distributions** is a **weather** distribution (P90…P10 peak at milder/hotter
weather around one forecast), not a demand-scenario band — using it as one would
be the basis mismatch rule 14 warns about.

### MISO — 2026 Long-Term Load Forecast Results Summary (LTLF Workshop 2026-04-13)

| file | source URL |
|---|---|
| `2026-LTLF-Results-Summary.pdf` | <https://cdn.misoenergy.org/20260413%20LTLF%20Workshop%202026%20Long%20Term%20Load%20Forecast%20Summary_UPDATED750524.pdf> |

**An edition bump**: `constants.DEMAND_GROWTH_RATES["MISO"]` cited the
**Sept-2025** vintage until this intake (rule 23 `[R-FROZEN-DERIVE]` — the
re-derivation is on the source update).

MISO publishes the LTLF as a **slide deck whose series are charts**, so
`miso.csv` carries (a) values the deck prints in words and (b) series read from
the PDF's own vector path coordinates, calibrated on the axis tick text and
**validated against the deck's printed labels** — the protocol SCN-WS4a
established for slide 21:

| slide | series | validation |
|---|---|---|
| 15 | MISO Net Energy Forecast TWh, Current trajectory 2026–2046 (+ 2020–2025 actuals); Low/High as a 2046 endpoint only | read 2026 = 677.7 vs printed "~678"; 2046 = 1,104.0 vs printed "~1,104"; the High 2046 bar = 1,404.5 vs printed "~1,404" |
| 16 | peak MW forecast-change drivers (2026 124 GW → 2046 184 GW, range 149–232; data centres +32 GW range 22–44; EV +11 GW range 8–14) | printed values, no chart read |
| 21 | Data Centers Net Energy TWh by region, Current trajectory 2026–2046 | read 2026 = 9.4 vs printed 9.6; 2046 = 266.0 vs printed 266 |
| 24 | EV Energy Forecast TWh 2020–2046 | 2026→2046 growth reads 61.8 TWh, inside the deck's own printed Low–High EV range of 47–78 TWh and matching the "62 TWh" figure already cited in `constants.ELECTRIFICATION_LAYERS` |

**One disagreement is carried, not resolved:** the Low 2046 bar reads **903 TWh**
by vector while the slide's callout prints **"~885 – 1,404 TWh"**. The printed
885 is used (rule 14 prefers the publication's own number) and the 903 read is
recorded here and in the lane FINDING.

**DATA NEEDED / BLOCKED — MISO driver-level per-LRZ forecast data.** The 2026
LTLF (slide 6) says MISO published driver-level forecast data; it sits behind
`www.misoenergy.org`, which **403s for this environment** (re-measured
2026-09-06; `cdn.misoenergy.org` does not). It would refine
`DATACENTER_ZONE_SHARE["MISO"]` from a regional to a per-LRZ decomposition.
Until it is reachable the published **regional** decomposition stands
(`FINDING-scn-ws4a-2026-09-05.md` §2).

## The unified CSV

`<iso>.csv` carries exactly the canonical columns of
`data/dictionary/schema/load-forecast.schema.yaml`:

```
iso, edition, vintage, scenario, published_case, area, area_type,
component, metric, year, value, unit, basis, source_doc, source_page
```

`scenario` is the model's canonical `low | mid | high`; `published_case` keeps
the publication's own label verbatim (e.g. "ERCOT Adjusted", "Lower Demand",
"Current Trajectory", "Local Reliability Scenario") so the mapping is never
silent.
