# MISO Data-Acquisition Audit

Date: 2026-06-22. Branch: `claude/miso-data-acquisition-nricv9`.

Closes MISO's remaining raw-data gaps and recommends (does **not** edit) the
MISO `load_share`. All items here are reproducible physical/market inputs
admissible per CLAUDE.md rule #12 (CEMS = unit availability events; metered
demand; auction clearing prices; delivered gas prices) — no values are
fabricated or tuned to any backcast target.

## Status table

| # | Item | Source | Status | File path | Notes |
|---|------|--------|--------|-----------|-------|
| 1a | CEMS LA 2023 (hourly unit-level) | EPA CAMPD bulk-files API (`emissions/hourly/state/emissions-hourly-2023-la.csv`) | **got** | `data/raw/campd-unit-level/LA_2023.parquet` | 692,040 rows, 30 facilities / 79 units, schema-identical to `LA_2024.parquet`. Downloaded with `x-api-key: DEMO_KEY` (project has no EPA key); bulk-file metadata gave the exact S3 path. |
| 1b | MISO unit-outage rebuild incl. LA 2023 | `scripts/data/derive_campd_unit_outages.py --iso MISO --years 2023 2024 2025` | **got** | `data/raw/campd-unit-outages-MISO.csv` | Re-derived. LA-2023 unit-outage windows went **0 → 136** across **42 units** (R S Nelson coal, Coughlin CC, Louisiana 1 CT, etc.); all from real CEMS windows (no full-year fallback). Total rows 2788 → 2924 (+136 = the LA-2023 additions). All 14 MISO states × 3 years now present. |
| 2 | MISO zonal/regional metered load 2023-2025 | EIA-930 Hourly Grid Monitor, sub-BA demand (`region-sub-ba-data`, parent=MISO) | **integrated** | `data/raw/zone-specific-demand/MISO/miso_subba_demand_2023-2025.csv` | 157,471 hourly rows, 6 MISO sub-BAs. Wired as per-zone hourly shapes; see Item 2 integration outcome below. |
| 3 | MISO PRA clearing prices PY 2023/24–2025/26 | MISO auction-summary PDFs (cdn.misoenergy.org) | **blocked** (primary) / **got** (secondary) | `data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv` (+ `SOURCES.md`) | Primary PDFs return HTTP 403 (allowlist). Values transcribed from public secondary reporting (Utility Dive, Enel); see manual manifest for the primary PDF URLs to replace them. |
| 4 | Chicago Citygate + MichCon monthly gas 2023-2025 | EIA citygate state series (proxy) | **got** (proxy) / **blocked** (ICE hub) | `data/raw/gas-prices/eia_citygate_IL_MI_monthly_2023-2025.csv` (+ `SOURCES_miso_citygate.md`) | EIA IL citygate = Chicago proxy; MI citygate = MichCon proxy. The ICE daily hub indices are paywalled/off-allowlist (manual manifest). |
| 5 | Per-zone wind CF shape 2023-2025 | NASA POWER hourly `WS50M` (MERRA-2 reanalysis) at EIA-860 wind-plant locations | **built** | `data/raw/miso-wind-shape/miso_{2023,2024,2025}_wind_zone_shape.parquet` | Distinct North/Central/South wind shapes via turbine power curve; reconciled to EIA-930 MISO-wide aggregate (level not pinned). See model-structure Item 5 below. |
| 6 | North↔Central corridor + Central↔South RDT asymmetry | MISO/SPP JOA (RDT 3,000/2,500 MW); MTEP/OASIS (N↔C, blocked) | **partial** | `config/iso_configs._miso_config` | RDT now an asymmetric one-way link pair (3,000 N→S / 2,500 S→N). N↔C posted TTC is allowlist-blocked (HTTP 403) — documented reconciled estimate. See model-structure Item 6 below. |
| 7 | MISO wind/solar curtailment (HSL) 2023-2025 | MISO Market Reports (misoenergy.org, blocked) → Potomac Economics IMM annual aggregate (got) | **wind wired (reference-rate)** / **solar gap** | `data/raw/miso-hsl/miso_wind_curtailment_annual.csv` | misoenergy.org still HTTP 403, so no hourly HSL parquet. Wind uses the measured IMM annual curtailment rate (~4.9%) via the forecast-uncurtailed gross-up (`_miso_wind_reference_curtailment_rate` → `_UNCURTAILED_FALLBACK_ISOS`); solar keeps delivered (no series). See model-structure Item 7 below (2026-07-21). |

---

## Item 1 — CEMS LA 2023 (closed)

`api.epa.gov` is reachable; the 403 on the bulk endpoints is `API_KEY_MISSING`,
not an allowlist block. The project ships an EIA key but no EPA CAM-API key.
`x-api-key: DEMO_KEY` is accepted for the metadata listing and the bulk file
download (a few requests — well inside the DEMO_KEY rate limit).

Procedure (reproducible):
1. `GET https://api.epa.gov/easey/camd-services/bulk-files` (header
   `x-api-key: DEMO_KEY`) → JSON `items[]`; filter `metadata.dataType==Emissions`,
   `dataSubType==Hourly`, `stateCode==LA`, `year==2023` → s3Path
   `emissions/hourly/state/emissions-hourly-2023-la.csv` (156.5 MB).
2. `GET https://api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-2023-la.csv`
   (same header).
3. Map the bulk CSV's human-readable columns to the EASEY camelCase parquet
   schema of `LA_2024.parquet` and write parquet. Column map:
   `State→stateCode, Facility Name→facilityName, Facility ID→facilityId(str),
   Unit ID→unitId(str), Date→date(ts[ns]), Hour→hour(int64),
   Operating Time→opTime, Gross Load (MW)→grossLoad,
   Steam Load (1000 lb/hr)→steamLoad, SO2 Mass (lbs)→so2Mass,
   CO2 Mass (short tons)→co2Mass, NOx Mass (lbs)→noxMass,
   Heat Input (mmBtu)→heatInput, Primary Fuel Type→primaryFuelInfo,
   Unit Type→unitType, Program Code→programCodeInfo`.

Verification: arrow schema equals `LA_2024.parquet` exactly (16 cols, matching
dtypes); full year 2023-01-01..2023-12-31; non-operating hours kept as NaN
(not zero), matching the 2024 file's null pattern; 38.9 M short tons CO₂,
73.5 M MWh gross.

---

## Item 2 — MISO regional metered load & recommended `load_share`

### Source and region crosswalk

EIA-930 reports MISO demand for six sub-BAs (LRZ groupings). They map to MISO's
**official** North/Central/South regions as:

| Region | EIA sub-BAs | LRZs |
|--------|-------------|------|
| North | `0001` | 1 |
| Central | `0027`, `0035`, `0004`, `0006` | 2,7 / 3,5 / 4 / 6 |
| South | `8910` | 8,9,10 |

(One Jan-1 00:00 boundary hour was de-duplicated out of the raw pull before
aggregation.)

### Metered evidence (2023-2025)

Annual energy (TWh) and energy share, per year:

| Year | North TWh | Central TWh | South TWh | Total | N share | C share | S share |
|------|-----------|-------------|-----------|-------|---------|---------|---------|
| 2023 | 95.0 | 372.1 | 173.8 | 641.0 | 0.1483 | 0.5806 | 0.2711 |
| 2024 | 93.5 | 375.1 | 174.4 | 643.0 | 0.1454 | 0.5833 | 0.2713 |
| 2025 | 96.2 | 383.6 | 178.3 | 658.1 | 0.1461 | 0.5829 | 0.2709 |

System coincident-peak hour and that hour's regional split:

| Year | Peak hour | MISO peak MW | N | C | S | N CP-share | C CP-share | S CP-share |
|------|-----------|-------------|---|---|---|-----------|-----------|-----------|
| 2023 | 2023-08-23 23:00 | 120,781 | 16,621 | 70,290 | 33,870 | 0.1376 | 0.5820 | 0.2804 |
| 2024 | 2024-07-15 22:00 | 114,734 | 14,382 | 69,789 | 30,563 | 0.1254 | 0.6083 | 0.2664 |
| 2025 | 2025-07-29 22:00 | 117,268 | 14,969 | 71,154 | 31,145 | 0.1276 | 0.6068 | 0.2656 |

Non-coincident regional peaks (MW): North ≈ 16.0–17.0 GW, Central ≈ 70.9–72.7 GW,
South ≈ 32.4–33.9 GW.

### Recommended `load_share` (MISO-official regional definition)

3-year averages:

| Region | Energy share | Coincident-peak share | **Current placeholder** |
|--------|-------------|-----------------------|-------------------------|
| MISO-North | **0.147** | 0.130 | 0.28 |
| MISO-Central | **0.582** | 0.599 | 0.46 |
| MISO-South | **0.271** | 0.271 | 0.26 |

**Recommendation:** replace `0.28 / 0.46 / 0.26` with the **energy shares
`0.147 / 0.582 / 0.271`** (drives total zonal MWh in the 8760 dispatch;
coincident-peak shares are within ~0.02 and tell the same story). South is
essentially confirmed (~0.27); the placeholder badly **over-weights North** and
**under-weights Central**.

### ⚠ Zone-definition caveat (must reconcile before integrating)

The recommended shares use MISO's **official** region split, where **North =
LRZ 1 only**. The model's `_miso_config` docstring instead describes
**MISO-North as "MN/IA/WI/ND/SD"** — i.e. LRZ **1 + 2 + 3**, pulling Wisconsin
and Iowa into North. EIA-930 bundles those LRZs across regions
(`0027` = LRZ 2 **+** 7, `0035` = LRZ 3 **+** 5), so the bundled sub-BAs
**cannot cleanly isolate WI/IA** from MI/MO with this source alone. Two clean
resolutions for the integration track:

1. **Redefine the model's MISO-North to LRZ 1 only** (match MISO's published
   North/Central/South) and use `0.147 / 0.582 / 0.271` directly. *(Preferred —
   the source is then exactly reproducible and matches MISO's own regional
   reports.)*
2. **Keep the broad North (LRZ 1+2+3)** and reapportion Central→North using
   **LRZ-level** peaks from the MISO OMS-MISO Survey / PRA zonal demand tables
   (a manual-download item — see manifest). Under that definition North is
   materially larger than 0.147 (it absorbs WI+IA), but the exact split needs
   the LRZ table, which the allowlist currently blocks.

Per CLAUDE.md rule #12 this misalignment is documented rather than buried in a
guessed number; do not silently keep `0.28` to compensate.

### Integration outcome (resolved 2026-06-23)

> **SUPERSEDED 2026-07-02 — six-zone refinement.** The 3-zone mapping below
> is the historical record of the original wiring. The model now uses the
> 1:1 sub-BA partition — `0001`→MISO-West, `0035`→MISO-Plains,
> `0004`→MISO-Illinois, `0006`→MISO-Indiana, `0027`→MISO-East,
> `8910`→MISO-South (shares 0.1466/0.1385/0.0676/0.1340/0.2422/0.2711) —
> per `docs/multi-iso/miso-zonal-refinement-scope.md`.

Wired into the model. The zone-definition caveat was resolved by drawing the
three model bubbles as **whole EIA-930 sub-BA (LRZ) unions** so the load and
transmission partitions coincide (pipe-and-bubble) and the load file drops in
cleanly. The broad wind-rich North is kept (Iowa stays with the wind belt):

| Model zone | Sub-BA group (LRZs) | States | Energy share (2023–25) |
|------------|---------------------|--------|------------------------|
| MISO-North | `0001` + `0035` (1, 3+5) | MN/ND/SD/MT + IA/MO | **0.285** |
| MISO-Central | `0027` + `0004` + `0006` (2+7, 4, 6) | WI/MI + IL + IN/KY | **0.444** |
| MISO-South | `8910` (8+9+10) | AR/LA/MS/E.TX | **0.271** |

The recommended `0.147` North share was for MISO's *official* LRZ-1-only North,
which strips Iowa's load out while the fleet keeps Iowa's wind there — the very
inconsistency rule #12 warns against. Under the sub-BA-aligned definition the
measured shares (`0.285/0.444/0.271`) nearly reproduce the old placeholder, so
the placeholder was closer to right than `0.147`; the real gain is the per-zone
**hourly** shape, not the annual level.

Implementation:
- `eia_loader.miso_zonal_load_shares` reads the sub-BA file, aggregates to the
  three zones per hour (zones now peak at different times), repairs the
  2024-08-26 06:00–08-27 05:00 EIA-930 reporting gap by per-sub-BA ffill/bfill,
  and is wired into `load_demand`.
- `iso_configs._miso_config` static `load_share` fallback set to
  `0.285/0.444/0.271` (used only when the file is absent).
- `zone_assignment._MISO_STATE_ZONES` aligned to the sub-BA boundaries: **WI →
  Central** (bundled with MI in `0027`), **MO → North** (bundled with IA in
  `0035`); the MN/IA/ND/SD wind belt stays in North.

---

## Item 3 — MISO PRA clearing prices (reference; primary source blocked)

Primary MISO PDFs return HTTP 403 (allowlist). Figures below are transcribed
from public secondary reporting and saved to
`data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv`; provenance and the
primary-PDF URLs to substitute are in `data/raw/miso-pra/SOURCES.md`. Prices in
**$/MW-day**.

| Planning Year | Summer | Fall | Winter | Spring | Locational separations |
|---------------|--------|------|--------|--------|------------------------|
| 2023/24 (first seasonal) | 10 | 15 | 2 | 10 | LRZ 9 (LA/E.TX): Fall **59**, Winter **19** |
| 2024/25 | 30.00 | 15.00 | 0.75 | 34.10 | LRZ 5 (Missouri): Fall & Spring **719.81** (= seasonal CONE; 872 MW deficit) |
| 2025/26 | 666.50 | N/Central **91.60**, South **74.09** | 33.20 | 69.88 | annualized: N/Central ≈ **217**, South ≈ **212** |

Trend: near-zero scarcity through 2023/24, isolated zone CONE events in 2024/25
(MO), then a footprint-wide step-change in 2025/26 (summer hit $666.50,
~22× the prior summer) as reserve margins tightened. Useful as the capacity-value
reference for the MISO market-design track.

---

## Item 4 — MISO gas basis (Chicago Citygate / MichCon proxies)

Saved: `data/raw/gas-prices/eia_citygate_IL_MI_monthly_2023-2025.csv` (EIA
monthly citygate, $/Mcf). Annual averages:

| Year | IL citygate (Chicago proxy) | MI citygate (MichCon proxy) |
|------|-----------------------------|------------------------------|
| 2023 | 4.03 | 3.70 |
| 2024 | 3.49 | 3.21 |
| 2025 | 3.84 | 3.80 |

These track Henry Hub closely with a modest positive basis and a winter bump
(IL Jan-2024 5.18, Jan-2025 4.40) — consistent with the doc-01 §4
"Chicago Citygate, MichCon, Henry — small +/–" expectation. **Caveat:** these
are EIA utility-citygate **state averages**, not the **ICE Chicago-Citygate /
MichCon daily trading-hub spot** indices (paywalled / off-allowlist).

**DAILY Chicago Citygate gap — CLOSED via the EIA-weekly proxy (2026-07-17,
miso-72).** `data/raw/gas-prices/miso_citygate_daily.csv` — 680 daily Chicago
Citygate delivered-gas prints 2023-2025 (`date, chicago_citygate_usd_mmbtu,
henry_hub_usd_mmbtu, source`), scraped by `scripts/data/fetch_miso_citygate_daily.py`
from the **"Chicago"** row of the EIA Natural Gas Weekly Update compact spot
table (the same free EIA-displayed NGI Daily GPI table the CAISO/NYISO daily
scripts read; `archivenew_ngwu/YYYY/MM_DD/`). This is genuine **weekday-daily**
granularity (not weekly-broadcast), so the single-Friday cold-snap print lands
on its true calendar day — e.g. the Winter Storm Heather Friday 2024-01-12
Chicago Citygate **$25.82/MMBtu** (+$12.74 over Henry Hub), the regional blowout
the monthly proxy (+$1.82 basis) and national HH both miss. Consumed by the
`miso_winter_citygate_daily` winter fuel-security overlay (`fuel.py`;
`SOURCES_miso_citygate.md`). **MichCon daily still OPEN:** the EIA compact table
carries no MichCon/Michigan row and the narrative never quotes a MichCon daily
print, so lower-Michigan's citygate daily remains the paywalled ICE
manual-download item below; Chicago Citygate is the representative MISO
North/Central winter gas hub for the overlay.

---

## Copy-paste manual-download manifest (allowlist-blocked items)

```text
# Run these from a network that can reach misoenergy.org / ICE, then drop the
# files at the indicated paths and (item 3) re-point the CSV at the primary PDFs.

# --- Item 3: MISO PRA auction-summary PDFs (primary source) ---
# Save under data/raw/miso-pra/
curl -L -o data/raw/miso-pra/2023-24_PRA_Results.pdf \
  "https://cdn.misoenergy.org/2023%20Planning%20Resource%20Auction%20(PRA)%20Results628925.pdf"
curl -L -o data/raw/miso-pra/2024-25_PRA_Results.pdf \
  "https://cdn.misoenergy.org/2024%20PRA%20Results%20Posting%2020240425632665.pdf"
curl -L -o data/raw/miso-pra/2025-26_PRA_Results.pdf \
  "https://cdn.misoenergy.org/2025%20PRA%20Results%20Posting%2020250529_Corrections694160.pdf"

# --- Item 2 caveat: MISO LRZ-level peak demand (only needed if MISO-North is
#     kept as the broad LRZ 1+2+3 definition) ---
# MISO "Regional Forecast and Actual Load" market report (per-region hourly):
#   https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/
#   (file: "Regional Forecast and Actual Load" / "rf_al_YYYYMMDD.xls" daily, or the
#    annual "Historical Regional Forecast and Actual Load" zip)
# OMS-MISO Survey (LRZ coincident-peak demand by zone), annual:
#   https://www.misoenergy.org/planning/resource-adequacy2/
# Save under data/raw/zone-specific-demand/MISO/

# --- Item 4: ICE MichCon daily hub spot (paywalled) ---
# Chicago Citygate DAILY is now proxied from the free EIA NG Weekly table
#   (data/raw/gas-prices/miso_citygate_daily.csv via
#    scripts/data/fetch_miso_citygate_daily.py) — only MichCon daily remains paywalled.
# ICE end-of-day natural-gas indices (subscription) — MichCon (lower Michigan):
#   https://www.ice.com/products/  (MichCon physical gas)
# Or NGI / Platts daily index archives (subscription). Prefer ICE MichCon daily if
# available; the overlay uses Chicago Citygate as the MISO North/Central hub today.
# Save under data/raw/gas-prices/

# --- Item 7: MISO wind & solar curtailment (HSL) reports (allowlist-blocked) ---
# MISO Market Reports — "Wind & Solar Curtailment" (daily/monthly):
#   https://www.misoenergy.org/markets-and-operations/real-time--market-data/market-reports/
#   (misoenergy.org currently returns HTTP 403 from this environment)
# Save under data/raw/miso-hsl/ then build per-year HSL parquets following
# scripts/data/build_caiso_hsl.py (HSL = EIA-930 delivered + reported curtailment).
```

### Reproduce the unblocked pulls

```bash
# Item 1 — LA 2023 CEMS (DEMO_KEY ok for a few requests):
curl -s -H "x-api-key: DEMO_KEY" \
  "https://api.epa.gov/easey/bulk-files/emissions/hourly/state/emissions-hourly-2023-la.csv" \
  -o emissions-hourly-2023-la.csv
# then map columns to the LA_2024.parquet schema (see Item 1 column map).

# Item 1b — rebuild MISO unit outages:
.venv/bin/python scripts/data/derive_campd_unit_outages.py --iso MISO --years 2023 2024 2025

# Item 2 — MISO sub-BA demand (EIA_API_KEY):
#   GET api.eia.gov/v2/electricity/rto/region-sub-ba-data/data/
#     frequency=hourly data[]=value facets[parent][]=MISO start=YYYY-01-01T00 end=(YYYY+1)-01-01T00
#   (paginate offset by 5000; de-dup the year-boundary hour)

# Item 4 — EIA citygate proxies (EIA_API_KEY):
#   GET api.eia.gov/v2/natural-gas/pri/sum/data/
#     frequency=monthly data[]=value facets[series][]=N3050IL3 facets[series][]=N3050MI3

# Item 5 — MISO per-zone wind SHAPE (EIA_API_KEY for the EIA-930 clock; NASA
#   POWER is keyless). Builds data/raw/miso-wind-shape/miso_<year>_wind_zone_shape.parquet:
.venv/bin/python scripts/data/build_miso_wind_shape.py --years 2023 2024 2025
```

---

## Model-structure items (branch `claude/miso-wind-congestion-hsl-*`, 2026-06-23)

These three items fix MISO *market structure*, not raw-data gaps. They follow
the same admissibility test as the rest of this audit (CLAUDE.md #11/#12): every
input is a reproducible physical/market quantity that regenerates for a forward
year and responds to changed conditions — never a value pinned or tuned to a
backcast residual.

### Item 5 — Per-zone wind CF shape (was: one ISO-wide profile for all zones)

**Problem.** MISO wind used ONE EIA-930 MISO-wide hourly `cf_profile` for all
three zones, scaled only by EIA-860 capacity share, so every zone shared one
diurnal/seasonal shape. That is wrong for MISO: the upper-plains **North**
(MN/ND/SD/IA) is driven by the Great-Plains nocturnal low-level jet (overnight
wind maximum, strong winter peak) while the lower-Midwest **Central** and the
Entergy **South** have a flatter, more afternoon-weighted regime.

**Source (forward-admissible).** NASA POWER hourly `WS50M` — 50 m wind speed
from the **MERRA-2 reanalysis** — at each zone's EIA-860 wind-plant locations:
`https://power.larc.nasa.gov/api/temporal/hourly/point` (keyless). A reanalysis
wind field regenerates for any year and responds to changed conditions, so it
passes the rule #11 test; it enters as a *shape*, never a level. The 50 m speed
is lifted to each plant's EIA-860 turbine hub height with the standard
1/7-power-law shear profile and run through a generic IEC-class onshore turbine
power curve (cut-in 3, rated 12, cut-out 25 m/s) to get an hourly CF.

**Boundary mapping.** Wind plants are assigned to the three model zones with the
existing `zone_assignment` geography (the sub-BA-aligned `_MISO_STATE_ZONES`):
North = LRZ 1/3/5 (MN/ND/SD/MT + IA/MO), Central = LRZ 2/4/6/7 (WI/MI + IL +
IN/KY), South = LRZ 8/9/10 (AR/LA/MS/E.TX). The largest 6 plants by nameplate
per zone are the capacity-weighted sample points. **MISO-South has no operable
wind** (the Entergy footprint is ~0 wind capacity) — physically correct; its
shape is a placeholder (cross-zone mean) that the loader weights by ~0 December
wind capacity, so it never contributes to the reconciled aggregate.

**Clock.** NASA POWER is queried in UTC and mapped onto the model's fixed
non-leap 8760-hour clock via the very `UTC time` column the renewable loader
uses (`_eia_hourly_frame_filled` for the MISO BA), so the shape lines up with
`cf_profile` hour-for-hour with no timezone guess.

**Reconciliation (level not pinned).** The per-zone shapes are reconciled to the
measured EIA-930 MISO-wide series by `_redistribute_preserving_total`: the
capacity-weighted zone sum equals the measured `cf_profile` every hour, so
annual energy and the system wind series are unchanged — only the North-vs-
Central split moves. The redistribution is capacity-aware (water-filling): when
a large zone is becalmed it cannot push another zone's CF above 1; the residual
spills to zones with headroom. (This generalizes the CAISO solar path, which is
byte-identical since solar zones co-vary and never overflow.)

**Verification.** Built for 2023/2024/2025. North's night(00-06)/afternoon
(12-18) wind ratio exceeds Central's every year (2023 0.92 vs 0.86; 2024 0.91 vs
0.88; 2025 1.00 vs 0.92) — the nocturnal-jet signature, consistent year over
year.

Files: `scripts/data/build_miso_wind_shape.py`,
`data/raw/miso-wind-shape/miso_{2023,2024,2025}_wind_zone_shape.parquet`,
`renewables._wind_zone_reanalysis_shapes` / `_zone_renewable_shapes` gated by
`_WIND_ZONE_SHAPE_ISOS = {"MISO"}`, `paths.MISO_WIND_SHAPE_DIR`.

### Item 6 — Congestion-corridor limits (the RDT asymmetry + N↔C corridor)

**(a) MISO-North ↔ MISO-Central wind-export corridor.** There is no single
posted TTC for this interface: the model's pipe collapses the many parallel
345 kV ties between the upper Midwest and the lower-Midwest load centers into
one link, while MISO posts limits at the flowgate level (a zone-boundary
misalignment, rule #12). The value is kept as a documented reconciled aggregate
estimate (order-of-magnitude of the summed parallel 345 kV interface, well above
North's ~16 GW coincident peak so the north's wind surplus can clear south).
**DATA NEEDED:** the posted MTEP/OASIS firm transfer capability is an
allowlist-blocked pull (misoenergy.org → HTTP 403); replace the estimate when
the OASIS/MTEP pull is available. Never tune it to a price residual.

**(b) MISO-Central ↔ MISO-South RDT directional asymmetry.** The Regional
Directional Transfer contract path (Midwest↔South wheels across SPP) has
*directional, asymmetric* JOA limits — **3,000 MW north→south vs 2,500 MW
south→north**. Previously modeled as one symmetric 3,000 MW link, which
over-stated south→north transfer by 500 MW. Now encoded as a **pair of one-way
links** (`is_bidirectional=False`, flow in [0, ttc]): Central→South at 3,000 MW
and South→Central at 2,500 MW; the LP's net Central↔South interchange is the
difference of the two, reproducing the asymmetry exactly. Source: MISO/SPP Joint
Operating Agreement, Attach. A — RDT limits; MISO/SPP Coordinated System Plan.

Files: `config/iso_configs._miso_config` (`links` block only),
`tests/test_iso_config.py::test_miso_rdt_contract_path_present`. The LP support
for one-way links is `transmission.get_link_bidirectional_array`.

### Item 7 — HSL / curtailment (wind now on the forecast-uncurtailed reference-rate path, 2026-07-21)

MISO publishes wind & solar curtailment in its Market Reports, but those live on
misoenergy.org, which stays allowlist-blocked here (HTTP 403), so **no hourly
uncurtailed-potential (HSL) parquet is built** — `renewables._hsl_file` returns
`None` for MISO and `data/raw/miso-hsl/` holds no `miso_<year>_hsl_hourly.parquet`.

What *did* land (2026-07-08 collection pass, `data/raw/miso-hsl/`): the Potomac
Economics (MISO IMM) **annual/quarterly** wind curtailment aggregate
(`miso_wind_curtailment_annual.csv` + quarterly + forecast-method CSVs). This is
coarser than CAISO/ERCOT's hourly/5-minute sources — too coarse for an hourly
parquet — but it *is* a measured, forward-reproducible per-tech curtailment
**rate**. MISO wind curtailment is material (~4.9% of potential, ~500-660 MW
average — multi-TWh/yr), comparable to ERCOT/CAISO and well above NYISO's
sub-1%.

**Change (2026-07-21, branch `claude/forecast-uncurtailed-hsl`):** MISO wind is
moved off the delivered-pinned profile onto the **forecast-uncurtailed
reference-rate path** — the same mechanism ERCOT's no-NP6 years use, not a
fabricated hourly series:

- `renewables._miso_wind_reference_curtailment_rate()` reads the annual CSV and
  returns the training-window (2023-2025, rule 22) firm (non-estimate) mean of
  `curtailed / (delivered + curtailed)` ≈ **0.0489** (2023 + 2024). It
  re-derives only when the CSV updates (rule 24) and references no target-year
  outcome, so it cannot pin the backcast (rules 11/13).
- `renewables._reference_curtailment_rate` falls back to that rate for
  `(MISO, wind)`; `MISO` is added to `_UNCURTAILED_FALLBACK_ISOS`.
- Effect: MISO wind's renewable bound is now `forecast_uncurtailed` (delivered
  EIA-930 shape ÷ (1 − rate)); the LP re-curtails endogenously. **MISO solar**
  has no published curtailment series, so it returns no rate and keeps the
  delivered profile (`delivered_pinned`) — an honest gap, not fabricated.

If the misoenergy.org hourly workbooks ever become reachable, build per-year HSL
parquets (`HSL = delivered + reported curtailment`, schema `_HSL_COLUMNS`)
following `scripts/data/build_caiso_hsl.py`; `_hsl_file` picks them up
automatically and upgrades MISO wind from `forecast_uncurtailed` to
`measured_potential`. CAMPD per-plant binning stays OFF for MISO and `pmax`
remains generic EIA-860 net-summer capacity (unchanged).
