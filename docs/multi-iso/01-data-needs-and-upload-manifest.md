# Data Needs & Upload Manifest

> **Update 2026-06-22:** §2 is resolved — EIA-930 hourly parquets now exist for
> all seven ISOs (`data/eia_hourly/`). §3 is **rewritten below** for the
> `data/raw/campd-unit-level/` unit-level layout: 34 states × 2023–2025 are
> present; PJM, MISO and ISO-NE are complete; only SPP's NE/NM/OK/WY remain.
> MISO's final gap (LA_2023) was filled 2026-06-22 — see
> `docs/multi-iso/miso-data-audit.md`. §4 gas basis is largely superseded for
> *backcasts* by
> measured per-plant EIA-923 monthly costs (`gas_monthly_actuals`, PJM
> 2026-06); hub-basis series remain relevant for NYISO/NEISO winter
> spikes and forecasts. Current per-ISO upload lists live in the prompt
> packs (CAISO: `06-caiso-prompt-pack.md` §2) per the v2 playbook
> (`05-backcast-playbook.md` §2).

Status: **planning**. This enumerates every data file each ISO needs to reach
an ERCOT-equivalent backcast, its source, whether it already exists in the
repo, and exactly what must be uploaded. Pairs with the Stage C/D/E checklist
items in `00-iso-addition-protocol.md`.

Target backcast years follow ERCOT: **2021–2025** (some series only run
2023–2025 depending on availability).

---

## 1. Data categories and how ERCOT uses each

The ERCOT backcast is driven by six data families. Each new ISO needs the same
six. The calibration-reference schema (per ISO-year, in
`data/raw/_validation-source/calibration_reference.json`) makes the requirement exact:

```
isos.<ISO>.<year> = {
  demand:        { avg_mw, min_mw, peak_mw, total_mwh, total_twh },
  generation_twh:{ coal, gas_cc, gas_ct, gas_st, nuclear, solar, wind, ... },
  henry_hub_actual: <float>,
  renewables: {
    wind:  { december_total_mw, zone_shares{zone:..},
             monthly_capacity_mw{zone:[12]}, monthly_ramp:[12] },
    solar: { ... same shape ... }
  }
}
```

| # | Data family | Source | Granularity | Repo location | Drives |
|---|-------------|--------|-------------|---------------|--------|
| 1 | **EIA-930 hourly** (demand + generation-by-fuel) | EIA Hourly Electric Grid Monitor | hourly, per BA | `data/eia_hourly/<BA> hourly.parquet` | demand series, renewable CF shaping, fuel-mix benchmark |
| 2 | **EIA-860** generator inventory | EIA-860 annual | annual, national | `data/raw/eia-860/`, `eia8602024.zip` | fleet, plant coords, BA codes, renewable capacity |
| 3 | **EIA-923** monthly gen + fuel cost | EIA-923 annual | monthly, national | `data/raw/f923_*.zip`, `data/raw/_processed-legacy/eia923_*.parquet` | fuel costs, generation reconciliation |
| 4 | **CAMPD / CEMS hourly** emissions | EPA CAMPD | hourly, per unit, downloaded **per state-year** | `data/raw/<ST>_<year>.parquet` | emission rates, heat-rate bins, coal must-run calibration |
| 5 | **eGRID** plant database | EPA eGRID | annual, national | `data/fleet/egrid2023_data_rev2 2.xlsx`, `data/raw/egrid2024_data.xlsx` | plant→zone (lat/lon/FIPS/BA), emissions benchmark |
| 6 | **Gas price** (Henry Hub + regional basis) | EIA / ICE | annual scalar (+ monthly shape) | `calibration_reference.json` | marginal cost of gas units |

Families 2, 3, 5 are **national** files already in the repo — they cover all
ISOs automatically once the BA filter and zone map exist (Stage B/C). The
per-ISO upload burden is concentrated in families **1, 4, and 6**, plus the
topology/profile data in doc 04.

---

## 2. EIA-930 hourly — REQUIRED upload, one file per ISO

Only `data/eia_hourly/ERCO hourly.parquet` exists today. Each ISO needs its
own, matching that file's schema (the `renewables.py` loader expects the
EIA-930 normalized per-fuel generation distribution + the demand series).

| ISO | EIA-930 BA code(s) | File to upload | Status |
|-----|--------------------|----------------|--------|
| ERCOT | `ERCO` | `ERCO hourly.parquet` | **present** |
| CAISO | `CISO` | `CISO hourly.parquet` | **present** |
| PJM | `PJM` | `PJM hourly.parquet` | **present** |
| NYISO | `NYIS` | `NYIS hourly.parquet` | **present** (2023–Q1 2025; 2025 full year needed for NYISO 2025 backcast) |
| ISO-NE | `ISNE` | `ISNE hourly.parquet` | **present** |
| MISO | `MISO` | `MISO hourly.parquet` | **present** |
| SPP | `SWPP` | `SWPP hourly.parquet` | **present** |

Each file must span all target backcast years and carry, at minimum, hourly
demand and the per-fuel generation series (coal, gas, nuclear, hydro, wind,
solar, oil, other) so the loader can build CF distributions and the fuel-mix
benchmark. **Action:** download from the EIA Grid Monitor bulk API/CSV and
convert to parquet (mirror the ERCO file's columns).

---

## 3. CAMPD / CEMS hourly — per-state, now in `campd-unit-level/`

> **Updated 2026-06-22.** This section previously described the old flat
> `data/raw/<ST>_<year>.parquet` layout and a large MISO/PJM gap that no longer
> exists. The authoritative **unit-level** CEMS extracts (one row per
> *unit*-hour, carrying `unitId` — the input the per-unit outage detector
> `scripts/data/derive_campd_unit_outages.py` consumes) now live in
> **`data/raw/campd-unit-level/<ST>_<year>.parquet`**. See
> `docs/multi-iso/miso-data-audit.md` for the MISO acquisition record.

CEMS is downloaded **by state-year** (`<ST>_<year>.parquet`). A plant counts
toward an ISO via its BA code (eGRID/EIA-860), so an ISO needs CEMS for **every
state that contains plants in its BA** — state boundaries don't equal ISO
boundaries, so several states are shared across ISOs.

**Present today in `campd-unit-level/` (all years 2023, 2024, 2025):**
`AR, CA, CT, DC, DE, IA, IL, IN, KS, KY, LA, MA, MD, ME, MI, MN, MO, MS, MT,
NC, ND, NH, NJ, NY, OH, PA, RI, SD, TN, TX, VA, VT, WI, WV` (34 states).

| ISO | States with plants in footprint (approx.) | Present (campd-unit-level, 2023–2025) | **Missing — upload** |
|-----|-------------------------------------------|---------------------------------------|----------------------|
| ERCOT | TX | TX | — |
| CAISO | CA (+ small NV/AZ imports) | CA | (NV, AZ if needed) |
| NYISO | NY | NY | — |
| ISO-NE | CT, MA, ME, NH, RI, VT | CT, MA, ME, NH, RI, VT | — |
| PJM | DE, IL(ComEd), IN, KY, MD, MI, NC, NJ, OH, PA, TN, VA, WV, DC | all 14 | — |
| MISO | AR, IA, IL, IN, KY, LA, MI, MN, MO, MS, ND, SD, TX, WI | **all 14** | — (LA_2023 was the last gap, filled 2026-06-22) |
| SPP | AR, IA, KS, LA, MN, MO, MT, ND, NE, NM, OK, SD, TX, WY | AR, IA, KS, LA, MN, MO, MT, ND, SD, TX | **NE, NM, OK, WY** |

Notes:
- **MISO is complete:** all 14 footprint states now have 2023–2025 unit-level
  CEMS. The final gap, `LA_2023`, was downloaded from the EPA CAMPD bulk-files
  API and written to `data/raw/campd-unit-level/LA_2023.parquet` (schema-
  identical to `LA_2024.parquet`); re-running the MISO unit-outage derivation
  added 136 LA-2023 outage windows across 42 units (see the MISO data audit).
- Shared states (IL, TX, MO, etc.) sit in two ISOs; CEMS is filtered by BA, not
  state, so one extract serves both — no duplication needed.
- **SPP** is the only remaining gap: `NE, NM, OK, WY` (all years) are not yet in
  `campd-unit-level/`.
- The **exact** state set per ISO should still be derived programmatically after
  Stage C: assemble the fleet for the BA, list distinct plant states, diff
  against files present in `campd-unit-level/`.

---

## 4. Gas price / regional basis — REQUIRED per ISO

ERCOT uses Henry Hub directly (Gulf-proximate). Other ISOs trade at a basis to
Henry Hub that materially changes gas-unit marginal cost — especially the
Northeast, which can spike far above HH in winter.

| ISO | Representative gas hub(s) | Basis vs Henry Hub | Action |
|-----|--------------------------|--------------------|--------|
| ERCOT | Henry Hub / Houston Ship Channel | ~flat | have |
| CAISO | PG&E Citygate, SoCal Border | + modest | source monthly basis |
| PJM | TETCO M3, Transco Z6 (non-NY), Dominion South | +/– seasonal | source monthly basis |
| NYISO | Transco Z6 NY, Iroquois | **large winter +** | source monthly basis (critical) |
| ISO-NE | Algonquin Citygate (AGT) | **large winter +** | source monthly basis (critical) |
| MISO | Chicago Citygate, MichCon, Henry | small +/– | source monthly basis |
| SPP | Panhandle, SoCal/Midcontinent | small +/– | source monthly basis |

**Action:** extend `calibration_reference.json` and the gas-price path system
(`ScenarioConfig.gas_price_path`, `data/fuel.py`) to support a per-ISO regional
gas series, or a Henry-Hub-plus-basis adder. Northeast winter basis is the
single biggest fidelity item for NYISO/ISO-NE price calibration.

---

## 5. Zonal load disaggregation — multi-zone ISOs only

Single-zone ISOs (CAISO_main, NYISO start, NEISO start) take EIA-930 demand
directly. Multi-zone ISOs need demand split to zones via `load_share`
(static) and ideally a zonal hourly shape:

| ISO | Zonal load source | Action |
|-----|-------------------|--------|
| ERCOT | NP6-345-CD actual load by weather zone | done (`derive_load_shares.py`) |
| PJM | PJM Metered Load / State of the Market zonal peaks | source zonal hourly load CSV |
| MISO | MISO Market Reports — regional (North/Central/South) load | source regional load |
| SPP | SPP zonal/area load | source area load |
| NYISO | NYISO zonal load (11 zones A–K) | source if/when NYISO goes multi-zone |
| ISO-NE | ISO-NE load-zone metered load (8 zones) | source if/when NEISO goes multi-zone |

`scripts/data/derive_load_shares.py` is the ERCOT template; generalize it to take
an ISO + zonal-load file and emit the `load_share` set + a topology check.

---

## 6. Renewable capacity + HSL — per ISO

`build_calibration_reference.py` derives, per ISO-year, year-end and monthly
wind/solar capacity by zone from **EIA-860** (national, present) — so capacity
*amounts* need no new upload, only the zone-assignment logic (Stage B). What is
ISO-specific is the **uncurtailed potential profile (HSL)**:

- ERCOT uses the NP6 HSL dataset (`scripts/data/build_ercot_hsl.py`) to feed the
  dispatch *uncurtailed* wind/solar so it re-curtails under modeled limits,
  one parquet per backcast year. 2023 builds from the UMass 60-Day-SCED
  dataset (auto-downloaded); **2024+ needs an upload**: ERCOT MIS wind/solar
  power-production reports (NP4-732-CD / NP4-737-CD hourly actuals, or
  NP4-733-CD / NP4-738-CD 5-minute actuals — both carry system-wide actual
  GEN and actual HSL), dropped as csv/zip under
  `data/raw/ercot-hsl/np6/`, then re-run the script. Years with a
  built parquet also get the modeled-vs-reported curtailment headline table
  in the calibration reports (the CAISO P6 pattern).
- Other ISOs' HSL analogues, and hydro, are detailed in
  `04-transmission-zones-and-congestion.md` §4. Where no HSL exists, the
  fallback is the EIA-930 delivered-generation distribution (already curtailed),
  which `renewables.py` handles today.

---

## 7. Hydro & pumped storage — material for several ISOs

Hydro is currently fuel code 6 but is dispatched as a flat thermal block with no
energy budget. That is acceptable where hydro is small (ERCOT) but **not** for:

| ISO | Hydro relevance | Data needed |
|-----|-----------------|-------------|
| NYISO | Very high (Niagara, St. Lawrence ~tens of TWh) | monthly hydro energy budget + min/max MW |
| CAISO | High, very seasonal (snowpack-driven) | monthly energy budget, pumped-storage params |
| MISO | Moderate (upper Midwest) | monthly energy budget |
| SPP | Low–moderate | monthly energy budget |
| ISO-NE | Moderate (+ pumped storage, e.g. Northfield) | monthly budget, PSH params |

**Source:** EIA-923 monthly hydro generation (present) gives the energy budget;
EIA-860 gives nameplate. Pumped storage is in EIA-860 as a distinct prime
mover. The *modeling* gap (energy-budget constraint, PSH as storage) is a
market-design module — see doc 02 §6 and doc 03 Pack E.

---

## 8. Consolidated upload checklist

```
MUST UPLOAD (per ISO):
[ ] EIA-930 hourly parquet            data/eia_hourly/<BA> hourly.parquet
[ ] Missing-state CEMS parquets       data/raw/<ST>_<year>.parquet
[ ] Regional gas basis series         (NE/NY critical)
[ ] Zonal hourly load (multi-zone)    for load_share + zonal shape
[ ] TTC / interface limits            see doc 04 (multi-zone)
[ ] Renewable HSL / uncurtailed       see doc 04 (where available)
[ ] ERCOT NP6 HSL reports 2024-2025   data/raw/ercot-hsl/np6/
[ ] Hydro monthly energy budget       (NYISO, CAISO, ISO-NE esp.)

ALREADY NATIONAL / NO UPLOAD:
[x] EIA-860 inventory (2024 + history)
[x] EIA-923 monthly gen + fuel cost
[x] eGRID 2023 + 2024 plant database
```

Single biggest blockers, in order: (1) the seven EIA-930 hourly files; (2) the
SPP/MISO CEMS state coverage; (3) Northeast regional gas basis; (4) zonal load
for PJM/MISO/SPP. Everything else reuses national files or is derivable.
