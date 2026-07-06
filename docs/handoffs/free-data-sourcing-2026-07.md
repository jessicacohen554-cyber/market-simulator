# Free-Data Sourcing Memo — 2026-07-06

**Filed:** 2026-07-06, branch `claude/free-data-downstate-hsl-sourcing-17wuko`.
**Scope:** Three data gaps currently blocked on paid subscriptions (ICE, Platts, SNL).
For each: free public sources identified, proposed approximation method, and
rule-13 admissibility verdict. No code or data intake this session.

**Rule-13 test (verbatim):** "could this same quantity be produced for a forward
year from forward drivers, and would it respond to changed conditions?" If yes →
admissible. If the only way to match is tuning to the residual → forbidden.

---

## Summary Table

| # | Gap | Free Source(s) | Proposed Approximation | Rule-13 Verdict |
|---|-----|----------------|------------------------|-----------------|
| 1 | Downstate NY delivered gas basis (Algonquin CG, Transco Z6 NY, Iroquois Z2) | EIA-923 monthly plant-level delivered cost + EIA N3050NY3 statewide citygate + EIA Weekly Transco Z6 NY daily (already in repo) | Henry Hub + structural monthly basis (EIA citygate − HH) + daily shape from Transco Z6 NY scrape | **ADMISSIBLE** |
| 2 | NYISO downstate condition-varying reserve requirement (SENY/NYC locational) | NYISO OASIS RT cleared reserves (free), Ancillary Services Manual rules, NYISO tariff/OATT filings | Reconstruct from published static base + thunderstorm-alert event log + largest-contingency formula | **GENUINELY-UNGETTABLE** (partial reconstruction possible; see §2) |
| 3 | ERCOT resource-level HSL (60-Day SCED Disclosure) | ERCOT NP3-965-ER "60-Day SCED Disclosure Reports" — Gen Resource Data with HSL/LSL/Base Point per resource, 5-min | Direct download: free registration (email-verified, zero cost) at apiexplorer.ercot.com → subscription key → bulk ZIP download | **ADMISSIBLE** |

---

## 1. Downstate NY Delivered Gas Basis

### 1.1 The Gap

The NYISO CT-offer gas anchor needs a downstate delivered-gas price that
captures: (a) the LDC city-gate premium over the pipeline hub (Transco Z6 NY),
(b) daily cold-snap blowouts, and (c) the interruptible rate class the peakers
actually face. The paid products (ICE daily, Platts Gas Daily, NGI Daily GPI)
provide this at Algonquin Citygate, Transco Zone 6 NY, and Iroquois Zone 2.

### 1.2 Free Sources Identified

| Source | URL | Cadence | Format | Years | License | Truly Free |
|--------|-----|---------|--------|-------|---------|-----------|
| **EIA Henry Hub daily spot** | https://www.eia.gov/dnav/ng/hist/rngwhhdD.htm (XLS); also FRED `DHHNGSP` | Daily (trading days) | XLS / CSV / JSON | 1997–2026 | US gov public domain | YES |
| **EIA N3050NY3 — NY State citygate monthly** | https://www.eia.gov/dnav/ng/hist/n3050ny3m.htm ; API v2 `natural-gas/pri/sum` | Monthly | XLS / JSON | 1989–2026 | US gov public domain | YES |
| **EIA N3045NY3 — NY delivered to electric power monthly** | Same API route, series `N3045NY3` | Monthly | JSON | 2001–2026 | US gov public domain | YES |
| **EIA Natural Gas Weekly Update archive — Transco Z6 NY daily** | `https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/` (structured "Spot Prices" table, "New York" row) | Daily (5 trading days per weekly page) | HTML (scrape) | 2008–2026 | US gov page; **data is NGI-sourced** (see §1.4) | YES to scrape; redistribution of the underlying NGI series has an open licensing flag (`docs/data-licensing.md` §5) |
| **EIA Natural Gas Weekly Update archive — Algonquin Citygate daily** | Same archive pages, narrative prose (not the structured table) | ~2 hard-dated prints/week (densest in winter) | HTML narrative (regex scrape) | 2008–2026 | Same as above | YES to scrape; same NGI caveat |
| **EIA-923 Schedule 2 — plant-level delivered fuel cost** | https://www.eia.gov/electricity/data/eia923/ | Monthly | ZIP/XLSX | 1999–2025 | US gov public domain | YES |
| **Pipeline EBBs (Iroquois, Algonquin/Enbridge, Transco/Williams)** | Iroquois: https://ebb.tceconnects.com/infopost/ ; Algonquin: https://infopost.enbridge.com/infopost/AGHome.asp?Pipe=AG ; Transco: https://www.1line.williams.com/Transco/index.html | Daily | HTML/CSV | varies | Free (FERC-mandated) | YES — but **no commodity spot prices posted**; capacity/flow/tariff only |
| **FERC Form 552** | https://www.ferc.gov/industries-data/natural-gas/industry-forms/form-no-552-download-data | Annual | DB tables | 2008–present | US gov public domain | YES — but useless (transaction metadata, not prices) |
| **NY PSC tariff filings (Con Edison GCF, National Grid)** | https://documents.dps.ny.gov/public/MatterManagement/CaseMaster.aspx ; Con Ed: https://www.coned.com/en/accounts-billing/your-bill/rate-information | Monthly | Unstructured PDF | varies | Public filings | YES — but extraction requires OCR/manual work per filing |

### 1.3 What the Repo Already Has (the stand-in)

The repo already exploits the best available free sources:

- `data/raw/gas-prices/transco_z6_ny_daily.csv` — EIA Weekly structured table, daily
  (`scripts/fetch_transco_daily_spot.py`)
- `data/raw/gas-prices/algonquin_citygate_daily.csv` — EIA Weekly narrative, ~2/week
  (`scripts/fetch_algonquin_daily_spot.py`)
- `data/raw/gas-prices/henry_hub_daily.csv` — EIA DNAV (`scripts/fetch_eia_gas_prices.py`)
- `data/raw/gas-prices/transco_z6_iroquois_monthly.csv` — monthly Iroquois level
  (`scripts/fetch_nyiso_gas_narrative.py`)
- `data/raw/gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv` — derived: EIA N3050NY3
  (statewide) minus Transco Z6 NY, floored at 0
  (`scripts/fetch_nyiso_downstate_gas_basis.py`)

### 1.4 Proposed Approximation & Admissibility

**Method: Henry Hub + structural monthly LDC-premium basis + daily pipeline-hub shape.**

The CT-offer gas anchor for NYISO downstate zones is built as:

```
delivered_gas[zone, day] = henry_hub_daily
                         + transco_z6_ny_daily_basis     (pipeline hub premium over HH)
                         + downstate_ldc_premium_monthly (EIA citygate − Transco monthly)
```

Where:
- `henry_hub_daily` — measured (backcast) or AEO trajectory (forecast). Free, EIA.
- `transco_z6_ny_daily_basis` — measured daily from EIA Weekly scrape (backcast);
  forward: structural seasonal pattern (winter pipeline congestion) that responds to
  pipeline capacity additions/demand growth. Free, already in repo.
- `downstate_ldc_premium_monthly` — EIA N3050NY3 (NY citygate) minus Transco Z6 NY
  monthly. This is the LDC distribution-system adder that covers transportation to the
  gate, storage, and supply-mix effects. Forward: projects as a structural premium
  driven by pipeline capacity vs heating demand. Free, already in repo.

**For Iroquois Zone 2 specifically:** The free daily Iroquois print does not exist in
any systematic downloadable form. The EIA Weekly narrative occasionally quotes Iroquois
in winter weeks but not systematically. The best free proxy is: monthly Iroquois level
(from `transco_z6_iroquois_monthly.csv`) + Transco Z6 NY daily *shape* (proportional
allocation of the monthly mean to trading days). This demonstrably under-reads
constrained winter months (Dec-2024: reconstruction ~$3.16 vs actual ~$9+), but it is
the best the free world offers without ICE/NGI.

**Rule-13 verdict: ADMISSIBLE.**

Each component is a measured physical/market input:
- Henry Hub: regenerates from AEO/futures forwards; responds to gas supply/demand.
- Transco Z6 NY daily basis: regenerates from seasonal pipeline-congestion pattern;
  responds to Transco expansion/retirement, demand changes.
- LDC citygate premium: regenerates from tariff structure + pipeline capacity;
  responds to infrastructure investment, heating-degree-day trends.

None of these components are tuned to the NYISO price residual. The approach
measures delivered fuel cost from observable market/tariff data. It would produce
different values if gas supply changed, if pipeline capacity expanded, or if winter
demand patterns shifted — exactly the rule-13 "responds to changed conditions" test.

**What would NOT be admissible:** fitting the basis differential to match the
observed NYISO LMP-minus-model residual, or adding an hourly adder calibrated to
close the CT dispatch gap.

### 1.5 Known Limitations of the Free Proxy

1. **Statewide, not downstate-specific:** N3050NY3 blends upstate LDCs with Con Ed /
   National Grid downstate. The downstate premium is diluted by cheaper upstate gas.
   EIA-923 plant-level data for specific downstate plants (if available for the target
   LM6000 fleets) can sharpen this.
2. **Monthly, not daily:** The LDC premium is monthly — it cannot capture the
   intra-month cold-snap blowouts where interruptible gas goes to distillate parity.
   The daily Transco shape helps, but the true downstate LDC intraday is paywalled.
3. **Interruptible vs firm:** The EIA citygate is a firm+interruptible blend. The
   peakers face interruptible-only tariff rates (SC-9/SC-13 class), which spike harder
   on constrained days. The PSC filings could sharpen this but require manual PDF extraction.
4. **NGI licensing flag:** The Transco Z6 NY daily and Algonquin daily series that
   EIA displays are NGI-proprietary data. `docs/data-licensing.md` §5 flags this for
   owner review. The series are scrapable from a US government page but their
   redistribution rights are unclear.

### 1.6 Recommended Intake Path

No new intake needed — the approximation is already wired. For improvement:

- **Datatype:** `gas_delivered_cost` (existing, under `data/dictionary/schema/`)
- **Extension:** Add a downstate-specific EIA-923 plant-level filter to
  `scripts/fetch_nyiso_downstate_gas_basis.py` that isolates Zone-J/K plants (Bayonne,
  Equus, Edgewood, Glenwood Landing) from the public EIA-923 form — these are the
  target fleet. If they appear in the public file (≥200 MW plants only; the ask-A5
  series in `nyiso-data-asks-2026-07.md` notes they may be non-reporters as merchants),
  their delivered cost is the tightest free proxy for the interruptible rate.
- **Schema:** no schema change; same `date, hub, price_usd_mmbtu` contract.

---

## 2. NYISO Downstate Condition-Varying Reserve Requirement

### 2.1 The Gap

Issue #1344: the static published locational reserve requirements (NYCA 2,620 /
East 1,200 / SENY ~1,100 / NYC 1,000/500 MW) never bind in the model because
in-pocket capacity is 3–8× the requirement even at minimum availability. The real
NYISO enforces a *condition-varying* requirement that rises during thunderstorm
alerts, gas contingencies, large-unit trips, and forecast uncertainty — it is this
dynamic requirement that makes the downstate reserves scarce and produces the
>$300 price tail (10–42 hours/year measured vs 0–7 modeled).

### 2.2 Free Sources Investigated

| Source | URL | What It Contains | Truly Free |
|--------|-----|------------------|-----------|
| **NYISO MIS — AS clearing prices** | http://mis.nyiso.com/public/ (P-5 = DA, P-6B = RT) | DA/RT reserve clearing prices by region (WEST, EAST, SENY, NYC) and product (10-min spin, 10-min non-sync, 30-min). Hourly DA, 5-min RT. | YES (CSV download, no login) |
| **NYISO Ancillary Services Manual** | https://www.nyiso.com/documents/20142/2226333/Ancillary+Services+Manual.pdf | Rules for setting reserve requirements; IRM-derived base + operating procedures | YES |
| **NYISO OATT Rate Schedule 4** | Via FERC eLibrary or NYISO tariff page | Per-capability-year locational reserve requirements (static values) | YES |
| **NYISO operations announcements** | https://www.nyiso.com/system-operations (Notifications/Alerts archive) | Thunderstorm Alert declarations (start/end timestamps), MEOP notices | YES |
| **NYISO MIWG/BIC presentations** | https://www.nyiso.com/committees (archives) | Methodology descriptions, requirement derivations | YES |
| **NYISO Dynamic Reserves proposal (Oct 2023)** | https://www.nyiso.com/documents/20142/40696384/20231019%20MIWG%20-%20Dynamic%20Reserves.pdf | Explicitly confirms current requirements are **"fixed quantities"** | YES |
| **Establishing Zone J Operating Reserves (MIWG 2019)** | https://www.nyiso.com/documents/20142/4461032/NYC%20Reserves%2001-15-19%20ICAP%20MIWG%20PRLWG.pdf | Derivation of the NYC 500/1000 MW values | YES |

**Critical finding: NYISO does NOT publicly post reserve requirement MW quantities or
cleared reserve quantities as a downloadable dataset.** The MIS public menu (reports
P-0 through P-930) carries reserve *prices* but NOT requirement or cleared MW. You
cannot even tell from public data when a locational requirement is binding
(confirmed by Galarneau, LinkedIn, re: NYISO ASDC binding indicators).

### 2.3 Critical Research Finding: Requirements Are Largely Static

**The NYISO MIWG Dynamic Reserves presentation (October 2023) explicitly states that
current locational requirements are "fixed quantities" with only "minor changes for
time of day or weather alerts."**

This reframes the gap. The published static requirements are:

| Region | 10-min Total | 30-min Total | Basis |
|--------|-------------|-------------|-------|
| NYCA | 1,310 MW | 2,620 MW | 2× largest single contingency |
| East (F–K) | ~600 MW | 1,200 MW | Locational nesting share |
| SENY (G–K) | ~500 MW | ~1,000 MW | Locational nesting share |
| NYC (J) | 500 MW | 1,000 MW | Zone J 2nd-largest contingency (2019 filing) |

These values change **only** when the largest contingency changes (large unit
retirement/addition) — they do not vary hourly. Operator-discretionary adjustments
(TSA, gas contingency) are "minor" per NYISO's own documentation and are NOT
published as a systematic series.

**Implication for issue #1344:** The model already HAS the static requirements
(hardcoded in `config/reserve_config.py`). The problem — that these never bind
(capacity is 3–8× the requirement) — is NOT caused by a missing dynamic requirement
series. The static requirements are the requirements. The scarcity pricing observed
in actuals (NYC reserve price > $0 in 3,082 hours in 2024) comes from NYISO's
**Ancillary Service Demand Curve (ASDC)** mechanism — a probabilistic pricing
function that sets positive reserve prices even when the hard MW requirement is met,
analogous to ERCOT's ORDC. The model's existing RCPF overlay
(`results/rcpf.py`) already represents this, but as a post-solve adder rather than
an in-LP demand curve.

The root cause of the model's reserve-not-binding gap is likely one of:
1. The ASDC demand curve is not represented in-LP (only as a post-solve overlay)
2. The commitment mechanism that forces units offline (reducing available reserves
   to near the requirement) is absent in the pure-LP formulation
3. Both — the handoff analysis (`nyiso-downstate-reserve-incidence-2026-06.md`)
   already concluded "the grounded fix is unit commitment"

### 2.4 Upcoming Change: Dynamic/Uncertainty Reserves (mid-2026)

FERC approved NYISO's "Uncertainty Reserve Requirements" in July 2025 (effective
~June 2026). This WILL introduce condition-varying requirements based on historical
forecast-error distributions for load/wind/solar. Key details:
- Additive new product layer on top of existing operating reserves
- Formulaic (deterministic from published forecast-error data) — reconstructable
- The existing static locational structure persists underneath
- Once effective, NYISO may begin publishing the hourly requirement as data

This does not help for the 2023–2025 backcast window.

### 2.5 Rule-13 Assessment

**The static requirements** (OATT Rate Schedule 4): ADMISSIBLE. Published tariff
input, regenerates each capability year from IRM/fleet changes.

**A condition-varying hourly series** (the original ask): The research shows this
series effectively does not exist as a meaningful time-varying quantity for 2023–2025.
The requirements are static. The "dynamic" adjustments are minor, operator-
discretionary, and unpublished — they have no systematic record and no forward driver.

**The demand-curve scarcity pricing** (ASDC): This IS what produces the measured
reserve prices. It is formulaic (published step functions in NYISO tariff), it
regenerates forward, and it responds to conditions. It is rule-13-admissible and
is already partially represented via the RCPF overlay. Strengthening the in-LP
ASDC representation is the structurally correct path — not hunting for a non-existent
dynamic requirement series.

### 2.6 Verdict: GENUINELY-UNGETTABLE (condition-varying requirement); REFRAMED

| Component | Status | Verdict |
|-----------|--------|---------|
| Static published requirements (NYCA / East / SENY / NYC) | Already in model (`reserve_config.py`) | ADMISSIBLE — already present |
| Condition-varying hourly requirement series | Does not exist in meaningful form; requirements are static | GENUINELY-UNGETTABLE (but also not the root cause) |
| ASDC demand-curve parameters (the scarcity pricing mechanism) | Published in NYISO tariff (step functions) | ADMISSIBLE — the correct mechanism to strengthen |
| Cleared reserve quantities by region | NOT posted on MIS or OASIS | GENUINELY-UNGETTABLE free |
| Thunderstorm Alert event log | Public announcements archive | ADMISSIBLE (minor effect; low priority) |

**Net assessment:** The "condition-varying reserve requirement" that issue #1344
hypothesizes is not a data gap — it is a mechanism gap. The requirements are static
and already in the model. The scarcity pricing comes from the ASDC demand curve,
not from a higher dynamic requirement. The structurally correct path is to
strengthen the in-LP ASDC/RCPF representation (rule-1-first: right mechanism
before tuning), not to acquire a non-existent hourly requirement series. The TSA/gas-
contingency discretionary adjustments are genuinely ungettable and genuinely minor.

### 2.7 Recommended Path

The data-acquisition path (Ask B in `nyiso-data-asks-2026-07.md`) should be
**deprioritized** — the series it requests likely does not exist even at NYISO, because
the requirements are static. Instead:

1. **Confirm the ASDC parameters** are correctly captured in `reserve_config.py`'s
   NYISO RCPF step functions (the tariff publishes these; check current capability
   year's filing).
2. **Evaluate moving the RCPF from post-solve overlay to in-LP demand curve** — this
   is the mechanism that would make reserves price correctly and is a structural
   improvement (rule #1).
3. **Register this finding** against issue #1344: the blocker is reframed from
   "missing data" to "missing mechanism" (ASDC in-LP).

---

## 3. ERCOT Resource-Level HSL (60-Day SCED Disclosure)

### 3.1 The Gap

The model needs per-resource HSL (High Sustained Limit) for ERCOT renewables to
compute uncurtailed potential. The existing 2023 source (UMass
nodal-curtailment-analysis dataset, derived from 60-Day SCED) covers only 2023.
The 2024/2025 intake was blocked (`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`)
on ERCOT API credentials.

### 3.2 Free Source Confirmed

| Field | Detail |
|-------|--------|
| **Data product** | NP3-965-ER "60-Day SCED Disclosure Reports" |
| **Product page** | https://www.ercot.com/mp/data-products/data-product-details?id=NP3-965-ER |
| **Classification** | Audience: Public; Security Classification: Public |
| **Archive URL** | https://data.ercot.com/data-product-archive/NP3-965-ER |
| **API endpoint** | `https://api.ercot.com/api/public-reports/np3-965-er/60_sced_gen_res_data` |
| **File within ZIP** | `60d_SCED_Gen_Resource_Data_*.csv` |
| **Update cadence** | Daily (60-calendar-day lag from real-time) |
| **Format** | ZIP → CSV |
| **Years available** | Active since 2011-01-29; display/archive window ~4 years rolling (covers 2022–2026) |
| **Terms** | ERCOT raw-data redistribution: permitted without notices (`docs/data-licensing.md` §3) |

### 3.3 ZIP Structure & File Naming

One ZIP per operating day, posted 60 calendar days after the operating day.

**ZIP contents** (6–9 CSVs per daily bundle):

| File prefix | Content |
|-------------|---------|
| `60d_SCED_Gen_Resource_Data` | **Generation resource dispatch** (the target file) |
| `60d_Load_Resource_Data_in_SCED` | Load resource (CLR) dispatch |
| `60d_ESR_Data_in_SCED` | Energy Storage Resource data (added ~2025) |
| `60d_SCED_SMNE_GEN_RES` | Settlement Metered Net Energy |
| `60d_SCED_AS_Offer_Updates_in_OpPeriod` | AS offer update counts |
| `60d_SCED_Resource_AS_OFFERS` | Full AS offer curves |
| `60d_HDL_LDL_ManOverride` | HDL/LDL manual override summary |
| `60d_SCED_QSE_Self_Arranged` | QSE self-arranged AS |
| `60d_SCED_EOC_Updates_in_OpHour` | Energy offer curve updates |

**CSV filename date format:** `60d_SCED_Gen_Resource_Data-DD-MMM-YY.csv`
(e.g., `60d_SCED_Gen_Resource_Data-03-FEB-26.csv`).

**Size:** ~200k+ rows per day (≈700 resources × 288 SCED intervals). Daily ZIP
estimated 50–200 MB compressed. Full multi-year archive is TB-scale.

**Archive depth:** Active display window = 1,462 days (~4 years); data.ercot.com
archive retains at least 7 years. Data exists since 2011-01-29 (nodal market
launch + 60 days).

### 3.4 Relevant Columns (Gen Resource Data)

| # | Column | Use |
|---|--------|-----|
| 1 | SCED Timestamp | 5-min interval timestamp |
| 4 | Resource Name | Per-resource identifier |
| 5 | Resource Type | Wind / Solar / other |
| 8 | **HSL** | High Sustained Limit (max sustained MW) |
| 9 | HASL | High Ancillary Service Limit |
| 10 | HDL | High Dispatch Limit (5-min ramp feasible) |
| 11 | **LSL** | Low Sustained Limit (min MW when online) |
| 14 | **Base Point** | SCED dispatch instruction (MW) |
| 15 | Telemetered Net Output | Actual measured real-time output |
| 22–23 | SCED1/SCED2 Offer Curves | MW/Price segment pairs (up to 10 segments each) |
| 24–27 | Startup offers + Min Gen Cost | Commitment economics |

HSL for wind/solar resources IS the uncurtailed potential — the maximum the
resource can produce given current wind/sun. `HSL - Base Point` = curtailment
instruction. This is exactly what `scripts/build_ercot_hsl.py` needs.

**Post-RTC+B columns (Dec 5, 2025 onward):** Ramp Rate Up/Down, per-product AS
Capabilities, per-product AS Awards — extends the file width but does not change
the HSL/LSL/Base Point columns the renewable HSL build uses.

### 3.5 Access Method

**The data product requires free registration — NOT fully credential-free.**

Despite the "Public" classification, all programmatic access paths require:

1. **Register** at https://apiexplorer.ercot.com (free: email + name + password,
   email verification)
2. **Subscribe** to the NP3-965-ER product (free, in the API Explorer portal)
3. **Obtain** a subscription key (shown in your profile after subscribing)
4. **Authenticate** via ERCOT's Azure B2C OAuth endpoint to get a 1-hour ID token:
   ```
   POST https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/
        B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token
   ```
5. **Call** the API with `Ocp-Apim-Subscription-Key` header + `Authorization: Bearer`

The legacy MIS (mis.ercot.com) also requires SiteMinder market-participant login.
There is **no unauthenticated bulk-download route** — the repo's prior attempt
(`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`) confirmed this for both the
legacy and new portals.

**However:** The registration is genuinely free (zero cost, no market-participant
status required, no NDA, no approval process beyond email verification), and the
ERCOT terms explicitly permit redistribution of raw data. This makes it a
"free-as-in-beer registration wall" rather than a subscription paywall.

### 3.6 Alternative: GridStatus (open-source intermediary)

The `gridstatus` Python library (https://github.com/gridstatus/gridstatus, BSD-3
license) already implements the full ERCOT API authentication flow and parses the
60-Day SCED Gen Resource Data into clean DataFrames. If a human registers an ERCOT
API account and provides credentials as environment variables, the existing
`scripts/build_ercot_hsl.py` could be adapted to use `gridstatus` as the fetch
layer — no custom auth code needed.

### 3.7 Rule-13 Admissibility

**ADMISSIBLE.** HSL is a measured physical input: the maximum sustained power a
resource can produce at each 5-minute interval, determined by real-time wind speed /
solar irradiance / mechanical availability. It regenerates for a forward year as the
renewable capacity factor profile (from weather) × installed capacity × availability.
It responds to changed conditions (a new wind farm raises system HSL; a turbine outage
lowers it). It is never the model's own output fed back as input.

### 3.8 Recommended Intake Path

- **Datatype:** `ercot_hsl` (existing; schema already defined, builder at
  `scripts/build_ercot_hsl.py`)
- **Drop zone:** `data/raw/ercot-hsl/np6/` (existing convention; the builder already
  handles NP4-732/737 files placed there)
- **Action required:** A human registers a free ERCOT API Explorer account, then
  either:
  - **(a)** Downloads NP4-732-CD (wind) and NP4-737-CD (solar) hourly CSVs manually
    from the Data Portal for 2024–2025 and drops them under `data/raw/ercot-hsl/np6/`.
    `python scripts/build_ercot_hsl.py --year 2024 2025` processes them with zero code
    changes.
  - **(b)** Provides the subscription key + credentials as env vars so a fetch script
    can pull via the API (the `60_sced_gen_res_data` endpoint, filtered by
    `resourceType=WIND,SOLAR`). This is the richer source (5-min per-resource vs
    hourly system-wide) but requires more parsing.
  - **(c)** Uses `gridstatus` with credentials to fetch programmatically.

**No code changes required for path (a).** The builder's NP6 path already works.

---

## Cross-Cutting Notes

### Pipeline EBBs Do Not Post Commodity Prices

A common misconception: FERC Order 637 mandates that interstate pipeline EBBs post
*capacity* and *operational* data (available/reserved capacity, scheduled flows, gas
quality, tariff rates). They do NOT post commodity spot/index prices. Those come
exclusively from price-reporting agencies (NGI, Platts/S&P, ICE) that survey
bilateral physical trades. No free pipeline-EBB route to daily gas basis prices exists.

### The NGI Licensing Flag

The repo's best free daily gas series (Transco Z6 NY, Algonquin Citygate) are
NGI-proprietary data displayed on EIA's government page. They are scrapable and the
repo already scrapes them, but `docs/data-licensing.md` §5 flags redistribution rights
as unresolved. This memo does not resolve that finding — it notes that the *data* is
free to access (no login, no subscription, on a .gov page) but the *intellectual
property* belongs to NGI/Hart Energy, not EIA.

### Free ≠ No-Registration

ERCOT's NP3-965-ER is "free" (zero cost, public classification, redistribution
permitted) but requires account creation. For this project's automated environment,
that means a human must register once and provide credentials. This is materially
different from the ICE/Platts paywall ($10k+/year subscriptions) and should not be
conflated with "credential-blocked" in the same sense.
