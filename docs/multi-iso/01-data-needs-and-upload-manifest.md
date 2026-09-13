# Data Needs & Upload Manifest

> **Update 2026-06-22:** §2 is resolved — EIA-930 hourly parquets now exist for
> all seven ISOs (`data/eia_hourly/`). §3 is **rewritten below** for the
> `data/raw/campd-unit-level/` unit-level layout: 34 states × 2023–2025 are
> present; PJM, MISO and ISO-NE are complete; only **SPP's NE/NM/OK** remain.
> *(Corrected 2026-09-06 by lane SPP-10, `docs/multi-iso/spp-data-audit.md` §2.4:
> this read "NE/NM/OK/WY". **WY carries zero EIA-860 plants with
> `Balancing Authority Code == "SWPP"`** and needs no extract; **CO** IS in the
> SPP footprint but holds only 19.5 MW of small solar and zero CEMS-eligible
> units, so it needs none either. Nine files, not twelve — and they hide 44.9 %
> of SPP's CEMS-eligible fossil capacity.)*
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
| SPP | `SWPP` | `SWPP hourly.parquet` | **present** (2015-07 → 2026-05; 8,760/8,784/8,760 rows for 2023/24/25. ⚠ **three defective hours** in the training window and `NG: BAT` 100 % null before 2026 — `spp-data-audit.md` §3.3–§3.4) |
| SOCO *(chartered, not registered)* | `SOCO` | `SOCO hourly.parquet` | **present** — 26,304 rows, a **complete UTC block** 2023-01-01 00:00 → 2025-12-31 23:00 (zero gaps, zero duplicate UTC hours); local-date counts 8,760 / 8,784 / **8,753** for 2023/24/25. **Local columns are `America/Chicago`, DST-aware, hour-ending** — 0 mismatches in 26,304 h (`soco-data-audit.md` §3.4). ⚠ **2025's 7-hour shortfall is a UTC-bounded fetch, not missing data** (§3.2 — extend by 7 h, never pad). ⚠ **Four `NG: NG` ≈ 70 GW artifact hours, 595 h of broken `Demand + TI = NetGen` identity in 2025, one 1-h partial demand dropout — no existing screen catches any of them** (§3.5). ⚠ `NG: BAT`/`PS`/`SNB`/`OES` null before **2024-07-15** (EIA taxonomy cut-over) and again 2024-07-16 → 2025-01-06, so **pumped storage is unobservable for 2023 and most of 2024** (§3.3). No wind in the footprint: `NG: WND` ≡ 0 |

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
| SPP | AR, **CO**, IA, KS, LA, MN, MO, MT, ND, NE, NM, OK, SD, TX (**not WY**) | AR, IA, KS, LA, MN, MO, MT, ND, **NE, NM, OK**, SD, TX | **— (closed 2026-09-06, lane SPP-11)**; CO needs none — no CEMS-eligible unit |
| SOCO *(chartered, not registered)* | **AL, GA, MS, FL** (panhandle; **not MA** — the one `MA` row is a BA-code source defect, `soco-data-audit.md` §2.6a) | **MS only** (2019–2026) | **`AL_2023`, `AL_2024`, `AL_2025`, `GA_2023`, `GA_2024`, `GA_2025`** — plus `AL_2026`/`GA_2026` on the SPP-11 precedent and `FL_2023..2025` (§2.3 priority 3). **THE PROGRAM'S CRITICAL PATH** |

Notes:
- **MISO is complete:** all 14 footprint states now have 2023–2025 unit-level
  CEMS. The final gap, `LA_2023`, was downloaded from the EPA CAMPD bulk-files
  API and written to `data/raw/campd-unit-level/LA_2023.parquet` (schema-
  identical to `LA_2024.parquet`); re-running the MISO unit-outage derivation
  added 136 LA-2023 outage windows across 42 units (see the MISO data audit).
- Shared states (IL, TX, MO, etc.) sit in two ISOs; CEMS is filtered by BA, not
  state, so one extract serves both — no duplication needed.
- **SPP's CEMS gap is CLOSED** (2026-09-06, lane SPP-11 — 16 parquets, OK/NE/NM/WY ×
  2023–2026, schema identical to `KS_2024`). The gap **was** **`NE, NM, OK`**, nine
  files for 2023–2025. Measured footprint, from EIA-860
  `Balancing Authority Code == "SWPP"` (`spp-data-audit.md` §2.4):
  **`WY` is not in the footprint at all** (zero SWPP plants; Wyoming
  SPP-adjacent generation files under `WAUW`, a WECC balancing authority), so the
  four `WY_*` parquets SPP-11 also pulled are **inert for SPP** — harmless, since
  `load_campd_hourly` filters every loaded state to the ISO's own fleet — and
  **`CO` IS** in the footprint but holds 19.5 MW across eight small solar sites with
  no CEMS-eligible unit: list it in `campd.ISO_STATES["SPP"]` for completeness on the
  PJM-`NC` precedent, but do not fetch it. Materiality of the gap that **was** open:
  **44.9 % of SPP's CEMS-eligible fossil MW**, including **61.2 % of gas-CC**,
  **60.1 % of gas-ST**, **37.1 % of coal** and **31.8 % of gas-CT** — which is why it
  was the SPP program's critical path (`spp-addition-plan-2026-09.md` §4).
- **SOCO's CEMS gap is OPEN and is twice as severe as SPP's ever was.** There is
  **no `AL_*`, no `GA_*` and no `FL_*` parquet for any year**; only `MS` is present.
  Measured from EIA-860 `Balancing Authority Code == "SOCO"`
  (`soco-data-audit.md` §2.4), the gap is worth **91.6 % of SOCO's CEMS-eligible
  fossil MW** — 45,797.3 MW of 50,005.0 — including **91.0 % of coal** and
  **90.5 % of gas-CC**. (SPP's equivalent at its own Phase-0 audit was 44.9 %.)
  `campd.ISO_STATES["SOCO"]` should read `("AL", "GA", "MS", "FL")`: FL holds only
  102.0 MW of CEMS-eligible fossil at one industrial-CHP site, but listing it costs
  nothing — `load_campd_hourly` filters every loaded state to the ISO's own fleet —
  and it is what makes the FL footprint adjudication checkable against metered data.
  Fetch route and exact URLs: `soco-data-audit.md` §9 manifest row 1. Lane **SOCO-11**.
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
| SPP | **Panhandle Eastern** (SPP's own MMU reference hub; Southern Star tracks it) | **HH − Panhandle = $0.38 / $0.26 / $0.55 per MMBtu for 2023 / 2024 / 2025** (SPP MMU State of the Market 2025 §4, report p.119) | **cited**; the backcast source is per-plant EIA-923 monthly delivered gas (present: 765/753/662 rows over 66/65/57 SWPP plants). See `spp-data-audit.md` §5 rows 8–8c |
| SOCO *(chartered, not registered)* | **Transco Zone 4** and **Southern Natural Gas (SONAT)** are the charter's candidates — but **which pipeline serves which plant is already on disk, per plant**: `eia860_plant.parquet` carries `Natural Gas Pipeline Name 1/2/3` for every SOCO plant. Read it rather than assuming | **pending SOCO-12** — no basis value is published by Southern; SOCO publishes no market data of any kind | Backcast source is per-plant **EIA-923 monthly delivered fuel cost, already present** (471 / 441 / 471 rows over 30 / 31 / 31 SOCO plants for 2023/24/25). State monthly series to fetch: **`N3045AL3m`, `N3045GA3m`, `N3045MS3m`** → `eia_delivered_gas_<ST>_monthly_2023-2025.csv`. See `soco-data-audit.md` §5 rows 6–7 |

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
| SPP | EIA-930 **sub-BA** hourly demand — 17 SWPP sub-BAs (CSWS EDE GRDA INDN KACY KCPL LES MPS NPPD OKGE OPPD SECI SPRM SPS WAUE WFEC WR) | **done 2026-09-06** (lane SPP-11): `data/raw/zone-specific-demand/SPP/spp_subba_demand_2023-2025.csv`, 447,049 rows, no interior gaps. Grouping candidate and the `EDE` straddle: `spp-data-audit.md` §5 rows 4b–6 |
| NYISO | NYISO zonal load (11 zones A–K) | source if/when NYISO goes multi-zone |
| ISO-NE | ISO-NE load-zone metered load (8 zones) | source if/when NEISO goes multi-zone |
| SOCO *(chartered, not registered)* | **There are NO EIA-930 sub-BAs for SOCO** — the spine is **FERC Form 714 Part 3 Schedule 2** hourly planning-area demand, via the PUDL ETL | **pending SOCO-11**, and the charter's scope needs correcting first: the footprint has **EIGHT** FERC-714 respondents, not three — Alabama Power (2), Georgia Power (183), Mississippi Power (184), Gulf Power (185), **Oglethorpe (107)**, **MEAG (210)**, **PowerSouth (1)** and **"Southern company" (142, `eia_code` 18195 — check this one FIRST, it may be the whole-BA filer)**. The three OpCos **structurally cannot** sum to the BA: Oglethorpe (6,472.2 MW) and MEAG (594.1 MW) serve Georgia load inside the same BA that Georgia Power's planning area excludes, and Georgia Power's own winter peak is 16,284 MW against a BA winter peak of 47,368 MW. Reconcile against the right denominator and report the residual with its attribution. `soco-data-audit.md` §6.2–§6.3 |

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
| SPP | Low–moderate — 3,103.5 MW conventional hydro + 259.2 MW pumped storage (2.9 % of 2025 net generation) | monthly energy budget from EIA-923 (present) |
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

> **SPP status, 2026-09-06 (lanes SPP-10 + SPP-11).** None of the four is still open
> for SPP: **NE/NM/OK CEMS** and **sub-BA zonal load** both landed on 2026-09-06
> (lane SPP-11). SPP's EIA-930 file is present and
> cross-validates against SPP's own published 2025 fuel mix to within 0.14 pp
> on every fuel; its gas basis is cited. SPP's own distinct blockers are ones
> this table never anticipated: **no per-hub (N/S) hourly LMP**, **no
> binding-constraint archive** (both behind a moved `portal.spp.org` API), **no
> N↔S TTC** (OASIS unreachable), and **no long-term load forecast** — the last
> of which is a hard precondition for registration. Full inventory, the
> registry-values table and the manual manifest:
> `docs/multi-iso/spp-data-audit.md`.

> **SOCO status, 2026-09-13 (lane SOCO-10 — chartered, NOT registered).** Two of the
> four blockers are open and one of them is the worst in this table's history.
> **(2) CEMS state coverage: `AL`, `GA` and `FL` are absent for every year** — only
> `MS` is present — which is **91.6 % of SOCO's CEMS-eligible fossil MW** (SPP's
> gap was 44.9 %). **(4) Zonal load: there are NO EIA-930 sub-BAs for SOCO**, so
> the spine is FERC Form 714 and the footprint has **eight** respondents, not
> three. (1) is closed — `SOCO hourly.parquet` is present and cross-validates
> against EIA-923 nuclear to 0.1–0.6 %; (3) is a Gulf-proximate footprint with
> per-plant EIA-923 delivered gas already on disk.
>
> **SOCO's own distinct blocker is one no prior ISO has had: there is no price.**
> Southern Company publishes no LMP, no day-ahead clearing price and no hourly
> index, and SEEM deliberately publishes none — so three of the rubric's four
> load-bearing price criteria have **no benchmark to score against**. That is owner
> card **S2** and it is unresolved; **no neighbouring hub may be substituted**
> (`soco-addition-plan-2026-09.md` §2.6, gate G17). Two further findings that
> belong to no other ISO: the footprint is **two timezones** (closed — the series
> convention is `America/Chicago`, DST-aware, hour-ending, measured 0/26,304
> mismatches), and **2,228 MW of Vogtle 3/4 plus 774 MW of Barry A3 are held
> online up to 15 months early** by `cod_ramp.effective_cod`'s plant-collapsed
> COD, worth **+24.8 % on measured 2023 nuclear**. Full inventory, the
> registry-values table, the zone recommendation and the manual manifest:
> `docs/multi-iso/soco-data-audit.md`.
