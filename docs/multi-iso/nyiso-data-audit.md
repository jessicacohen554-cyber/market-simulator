# NYISO Data Audit

Companion to `docs/sessions/multi-iso/07-nyiso-prompt-pack.md` (archived) and the upload manifest
there (U1–U7). Each section is owned by the pack that filled it.

> **Scope note.** Started by **P1 (unit-outage windows)** with §3 (CEMS
> coverage / unit-outage detection); §4 added by **P7 (gas + RGGI)**. **P0
> (Stage E, 2026-06-11)** filled §1 (calibration reference), §2 (fleet sanity),
> and §5 (upload-manifest status). Done together with the NEISO audit
> (`neiso-data-audit.md`) in one pass — both ISOs share
> `scripts/data/build_calibration_reference.py` + `calibration_reference.json`.

## 1. Calibration reference — extended for NYISO 2023 + 2025 (P0)

`scripts/data/build_calibration_reference.py` now derives NYISO (and NEISO)
alongside ERCOT/PJM/CAISO. NYISO uses a per-ISO year override
(`CALIBRATION_YEARS_BY_ISO["NYISO"] = (2023, 2025)`) with BA code `NYIS`.
**2024 is deliberately deferred** — the 2024 EIA-930/923/860 reference data all
exist (and the script would emit a clean 2024 block today), but the backcast
*year* is gated on the `NY_2024` CAMPD extract (upload U1), so 2024 enters the
override only when that lands, matching doc-07 §2.

Written artifacts:

- `data/raw/_validation-source/calibration_reference.json` — NYISO blocks for
  2023/2025: EIA-930 demand stats (`data/eia_hourly/NYIS hourly.parquet`),
  measured Henry Hub, EIA-923 by-fuel `generation_twh` (now including the
  **large hydro** and the **oil** columns — see §1a), EIA-860 wind/solar
  December totals + 5-zone shares + monthly ramps, and the eGRID 2023
  `BACODE=NYIS` generation/emissions benchmark.
- `data/raw/_validation-source/NYISO_{2023,2025}_renewable_capacity.csv` — per-zone,
  per-month EIA-860 operable wind/solar capacity.

Headline reference values:

| Year | Demand (TWh) | Peak (MW) | HH ($/MMBtu) | Wind Dec (MW) | Solar Dec (MW) | EIA-923 gas cc/ct/st (TWh) | Nuclear (TWh) | **Hydro (TWh)** | **Oil (TWh)** |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | 147.1 | 30,206 | 2.54 | 2,738 | 1,645 | 49.5 / 4.6 / 9.7 | 27.5 | **28.4** | **0.42** |
| 2025 | 151.6 | 31,857 | 3.52 | 2,868 | 2,930 | 45.4 / 3.4 / 11.5 | 28.4 | **21.0** | **1.06** |

eGRID 2023 NYIS benchmark (headline): gas_cc 45.0 TWh / gas_ct 19.3 TWh
(eGRID's heat-rate CC/CT split lumps no-heat-rate gas into CT, unlike the
prime-mover-based 923 split — 923 is the more reliable class benchmark),
hydro 28.0 TWh, nuclear 27.5 TWh, oil 0.50 TWh, biomass 2.58 TWh; CO2 totals
gas_cc 16.25 + gas_ct 10.36 + biomass 1.33 + oil 0.26 ≈ **28.2 Mt**.

### 1a. Hydro + oil added to the EIA-923 benchmark (code change this session)

The shared `_eia923_generation` masks previously emitted only
coal/gas_cc/gas_ct/gas_st/nuclear/wind/solar — fine for ERCOT/PJM/CAISO, but
NYISO's ~25–30 TWh/yr of Niagara/St-Lawrence hydro and the winter dual-fuel
oil burn are first-order and *must* be benchmarked. Two scoped additions:

- **hydro** = EIA-923 fuel code `WAT` + prime mover `HY` (conventional hydro
  only; pumped storage `WAT`/`PS`, which nets negative, is excluded — it is
  storage, not energy, per doc-07 design decision 2).
- **oil** = fuel codes `DFO`/`RFO`/`JF`/`KER`/`WO`/`PC`, any prime mover.

These are gated through `_EIA923_EXTRA_FUELS_BY_ISO = {NYISO, NEISO}`, so the
already-calibrated ERCOT/PJM/CAISO `generation_twh` blocks are untouched
(hydro/oil are negligible or unbenchmarked there). eGRID already mapped
`HYDRO`/`OIL` generically, so the eGRID benchmark needed no change beyond the
new `NYIS`/`ISNE` BACODE entries.

### 1b. Regression guard — verified, with the known ERCOT/PJM drift finding

The merged `calibration_reference.json` was diffed against the committed
version: **every ERCOT/PJM/CAISO block and all top-level fields are
byte-identical** (zero removed/changed lines; the only additions are the
NYISO/NEISO `isos` and `egrid_benchmark` entries). The committed
ERCOT/PJM/CAISO renewable-capacity CSVs were left untouched.

**Finding (backlog, ERCOT/PJM-owned — same item as caiso-data-audit §1b):**
re-running the script at HEAD *would* shift the committed ERCOT/PJM blocks,
because the ERCOT topology gained a **`Northeast`** zone (committed ERCOT CSVs
carry 6 zones, current `iso_configs` has 7) and the EIA-860 parquets were
rebuilt, both *after* the ERCOT/PJM reference was last generated (2026-06-10).
The committed ERCOT/PJM artifacts are therefore one config/EIA-860 vintage
stale. To honor the byte-identical guard this session **preserved** the
committed ERCOT/PJM/CAISO blocks verbatim (load committed JSON → insert only
NYISO/NEISO → re-dump) and restored the ERCOT/PJM CSVs from HEAD. Re-baselining
ERCOT/PJM belongs to an ERCOT/PJM calibration session, not this NY/NE pack.
CAISO (regenerated 2026-06-11) is current and reproduces byte-identically.

### 1c. Known caveats on the NYISO blocks

- **2025 `generation_twh` is a lower bound.** The `f923_2025` zip is the
  early-release M-file; annual-only respondents are absent. NYIS shows it
  clearly: 2025 hydro 21.0 TWh (vs 28.4 in 2023) and solar 0.66 TWh (vs 2.05)
  are light because most hydro/small-solar reporters have not yet filed. All 12
  months are present — this is respondent coverage, not a partial year. Demand
  (EIA-930) is complete; only the 923 by-fuel mix is preliminary. **P11/P12
  must treat the 2025 fuel-mix targets as preliminary** and re-run the script
  when the final 2025 EIA-923 lands. (ERCOT/PJM/CAISO 2025 carry the same
  national caveat.)
- **Demand is net load** (playbook §8.1): EIA-930 NYIS demand is net of NY's
  growing, downstate-concentrated BTM PV wedge. Backcasts model front-of-meter
  resources only; forecast gross-up is the build-once BTM module.

## 2. Fleet sanity — `get_iso_config("NYISO")` + NYIS BA filter (P0)

`load_fleet_from_csv("NYISO", get_iso_config("NYISO"))` (the per-plant EIA-860
path; wind/solar/hydro/storage load via their own machinery and are excluded
here):

- **460 LP generators, 151 distinct plants, 30,405 MW** fossil + nuclear:

| Class | MW | Units |
|---|---|---|
| gas_ct | 12,432 | 172 |
| gas_cc | 11,349 | 122 |
| nuclear | 3,326 | 4 |
| **oil** | **2,906** | **58** |
| biomass | 392 | 104 |

- **Oil is prominent (2,906 MW)** and **dual-fuel is dominant: 17,098 MW
  across 51 plants** carry an EIA-860 oil/gas switch flag
  (`dual_fuel_plant_groups`) — the winter gas→oil switching machinery P13
  activates. This is the headline NYISO fleet feature.
- **Zone distribution (MW):** Upstate_West 7,835 / Capital_Hudson 7,991 /
  Lower_Hudson 111 / NYC 9,292 / Long_Island 5,176. **No unassigned plants**
  (zero fallback-zone warnings). `Lower_Hudson` is generation-thin by design —
  a downstate load pocket whose largest former unit (Indian Point) is retired;
  mid-Hudson steamers (Roseton/Danskammer/Bowline) land in Capital_Hudson.
  P2/P10 should confirm this aggregation reproduces the downstate price
  separation.
- **States:** NY 28,891 MW (149 plants) + **NJ 1,513 MW (2 plants)** —
  **Bayonne Energy Center** (ORIS 56964) and **Linden Cogen** (ORIS 50006),
  both physically in NJ but in the **NYIS** balancing authority, injecting into
  NYISO Zone J (NYC) via HVDC. Correctly included; not an error.
- **Indian Point confirmed ABSENT** from the 2023+ fleet (Units 2/3 retired
  2020/2021). The 4 nuclear units are FitzPatrick (844 MW), Nine Mile Point 1
  (620) & 2 (1,283), and Ginna (579) — ~3.3 GW upstate, matching doc-07
  design decision 6.

### 2a. Comparison vs published totals (NYISO Gold Book)

The fleet loader covers fossil + nuclear only; renewables, hydro, and storage
load through their own machinery (P4/P5/P6). Reconstructed nameplate:
fossil+nuclear 30.4 GW + wind 2.7 + solar 1.6 + hydro (~5.7 GW nameplate:
Niagara ~2.7, St-Lawrence ~0.9, conventional ~2.1) + Blenheim-Gilboa PS ~1.2 ≈
**~42 GW nameplate**, which sits above the published **37,375 MW summer
generating capability** (2024) — expected, since summer capability is
weather/age-derated below nameplate.

| Class | Model | Published benchmark | Verdict |
|---|---|---|---|
| Fossil + nuclear | 30,405 MW | NYISO Gold Book 2024: ~37.4 GW *total* summer capability (incl. hydro/VRE/storage, derated) | reconciles once companion fleets + derate applied |
| Nuclear | 3,326 MW (4 units) | FitzPatrick + Nine Mile 1&2 + Ginna, ~3.3 GW | ✓ Indian Point retired |
| Wind | 2,738 MW (Dec-2023) | eGRID 2023 NYIS: 2,738 MW (923 CF cross-check 4.77 TWh) | ✓ |
| Solar | 1,645 MW (Dec-2023) | utility-scale only; BTM excluded (net-load) | ✓ direction |

Source: [NYISO 2024 Load & Capacity Data Report (Gold Book)](https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Public.pdf);
[NYISO Power Trends / 2024 summer assessment](https://www.nyiso.com/power-trends)
(summer generating capability 37,375 MW; RNA generating capability 37,595 MW).
Note: nyiso.com returns 403 from this environment (EIA/ISO hosts blocked,
playbook §2), so the per-zone Gold Book capacity table could not be pulled
directly; the headline summer-capability figure is from the public Power Trends
material, and the in-repo eGRID 2023 workbook (`BACODE=NYIS`) serves as the
EPA fleet benchmark.

## 3. CEMS coverage

`states_for_iso("NYISO")` is **NY only**, so every NYISO-fleet fossil plant
that carries Part-75 CEMS reports under a NY state-year extract. Diff against
`data/raw/campd-unit-level/NY_<year>.parquet`:

| State-year | Unit-level extract | Notes |
|---|---|---|
| `NY_2023` | **present** | feeds `campd-unit-outages-NYISO.csv` (857 windows) |
| `NY_2024` | **missing** (upload U1) | 2024 stays statistical-availability-only |
| `NY_2025` | **present** | feeds `campd-unit-outages-NYISO.csv` (764 windows) |

2024 is the only NY gap. Until `NY_2024.parquet` lands (manifest U1, P0/P1),
an `outage_source="historic"` NYISO 2024 run carries no measured windows and
degrades to the statistical WEFOR/POF availability model for that year
(`unit_outage_derate_factors(2024, iso="NYISO")` returns `{}`; the fleet
assembly logs the "no outage windows cover NYISO 2024" warning by design).

**P0 fossil-state note (2026-06-11):** assembling the fleet surfaced **2 NJ
plants** — Bayonne Energy Center + Linden Cogen (1,513 MW, 5% of fossil),
NYIS-BA injections into Zone J (§2). `NJ_{2023,2024,2025}` CAMPD extracts *do*
exist in `campd-unit-level/`, so these have CEMS data available, but
`campd.ISO_STATES["NYISO"] = ("NY",)` means the NYISO outage derivation does
not read NJ — those plants run on statistical availability. Low priority; a
one-line `ISO_STATES` change + `derive_campd_unit_outages.py --iso NYISO`
rerun would fold them in (P1 follow-up candidate).

### Unit-outage detection coverage (P1, verified 2026-06-11)

`campd-unit-outages-NYISO.csv` (**1,621 windows: 857 in 2023, 764 in 2025,
44 facilities**) regenerates **byte-identically** from the committed
`NY_2023`/`NY_2025` extracts via
`python scripts/data/derive_campd_unit_outages.py --iso NYISO --years 2023 2024 2025`
(2024 emits zero windows — "no unit-level extract for NY 2024"). The committed
file is current.

**No coal in NYISO → only the event-based rule fires.** NYISO's fossil fleet
is load-following gas combined cycle plus oil/gas peakers and legacy
gas-steam — essentially no coal. Every CAMPD unit in the NY extracts reports
`primaryFuelInfo = "Pipeline Natural Gas"` (zero `"Coal"`), so the unit-level
detector routes **every** unit to the event-based rule
(`detect_outages_eventbased`, every-hour CF < 2% (`ST_GAS_CF_PEAK`) sustained
≥ 120 h). The coal real-run rule (`detect_outages`, sustained CF > 5% for
≥ 24 h) has **no NYISO targets** — `campd-unit-outages-NYISO.csv` carries
**zero `COAL`-group rows** (groups present: `CC_REGULAR`, `CC_CHP`, `ST_GAS`,
`ST_CHP`, `CT_CHP`).

**Spot-check — known load-following steamers / CCs.** An independent detector
replay (reading the parquet directly, not via the script) on the four named
fleets reproduced their windows and confirmed the every-hour CF < 2% rule
holds inside every detected window, in both 2023 and 2025:

| Plant | ORIS | Group | Fuel | Rule | Windows hold every-hour<2% |
|---|---|---|---|---|---|
| Ravenswood Generating Station | 2500 | CC_REGULAR | pipeline gas | event-based | ✔ (34/2023, 30/2025) |
| Astoria Generating Station | 8906 | ST_GAS | pipeline gas | event-based | ✔ (58/2023, 41/2025) |
| Roseton Generating LLC | 8006 | ST_GAS | pipeline gas | event-based | ✔ (21/2023, 17/2025) |
| Danskammer Generating Station | 2480 | ST_GAS | pipeline gas | event-based | ✔ (17/2023, 17/2025) |
| Bowline Generating Station | 2625 | ST_GAS | pipeline gas | event-based | ✔ (28/2023, 16/2025) |

The long windows on Astoria/Roseton/Danskammer/Bowline (multi-month dead
spans) are the correct signature of old oil/gas-dual-fuel steamers that sit
idle for most of the year — genuine zero-output periods the event-based rule
flags as derates, not economic part-loading (any single hour ≥ 2% CF breaks a
window). Astoria Energy (55375, CC_REGULAR) and the modern CCs (Athens,
Cricket Valley, Empire) show shorter, maintenance-shaped windows instead.

### Fossil capacity: CEMS history vs. statistical availability

NYISO fossil fleet by model group (`load_fleet_from_csv("NYISO")` pmax), and
the share whose plant has CEMS unit-outage history (appears in the CSV):

| Class | Fleet MW | Plants | CEMS-covered | Outage overlay |
|---|---|---|---|---|
| CC_REGULAR | 7,040 | 23 | 91% | applied (event-based) |
| CC_CHP | 4,309 | 17 | 78% | applied (event-based) |
| ST_GAS | 8,902 | 11 | 95% | applied (event-based) |
| ST_CHP | 470 | 3 | 66% | applied (event-based) |
| CT_CHP | 446 | 14 | 79% | **none** — CTs dispatch economically (`_generic_unit_outage_target` returns `None`) |
| CT_PEAKER | 2,614 | 42 | 12% | **none by design** — peakers dispatch economically |
| **All fossil** | **23,781** | | **81%** | |
| **Overlay-eligible (CC + ST_GAS/CHP)** | **20,721** | | **90%** | |

The unit-level derate actually applies to the CC + gas-steam fleet (CTs are
excluded at overlay time): `unit_outage_derate_factors(2023, iso="NYISO")`
returns **43 derated `(plant, group)` bins** (same in 2025; empty in 2024),
covering **16,828 MW = 71% of all fossil** capacity. The remaining
overlay-eligible capacity (~10%) is plants that ran clean enough to emit no
window in those years, or whose plant code has no CEMS extract — they stay on
statistical availability. CT peakers and CT-CHP (3,060 MW combined) are
statistical by design.

NYISO carries **no facility-level extract** (`campd-outages-NYISO.csv` is
absent): the per-unit derate is the complete CAMPD-derived outage source, as
with CAISO, so the facility-summed overlay (`outage_masks_for_year`) returns
empty and there is no double-counting.

### Overlay wiring (verified)

`data/outages.py` picks the NYISO CSV up under `outage_source == "historic"`
exactly as PJM/CAISO do: `unit_outage_csv_for_iso("NYISO")` →
`campd-unit-outages-NYISO.csv`; `unit_outage_derate_factors(..., iso="NYISO")`
routes through `_generic_unit_outage_target` + `_iso_plant_capacity` (per-plant
EIA-860 nameplate denominator). A `--hours 48` NYISO 2023 smoke run
(`scripts/run_calibration.py --iso NYISO --year 2023 --hours 48`) loads the
overlay end-to-end — `fleet.generators_to_fleet_arrays` logs **"unit-outage
derate (NYISO 2023): 79 plant-tranches derated"** (43 `(plant, group)` bins
fan out to 79 LP generator-tranches). The run then stops at an **unrelated**
`COAL_PRICE_BASE['NYISO']` `KeyError` in `data/fuel.py` — a fuel-price config
gap owned by the fuel pack (P7), not P1; it fires after the outage overlay has
already loaded.

## 4. Gas pricing, winter basis & RGGI (P7, verified 2026-06-11)

### Measured monthly gas vs. the +0.55 basis seed

`gas_monthly_actuals` is now **default-on for NYISO** (as CAISO), so backcasts
price gas at the EIA-923 volume-weighted ISO-month delivered cost with the
nearby-plant/state fallback rather than Henry Hub + the flat +0.55
`GAS_BASIS_DIFFERENTIAL` seed. All 12 months report receipts in every year
(2023–2025), so the measured series fully overrides the shaped trajectory.

The measured ISO-average **monthly** basis (delivered − measured Henry Hub) and
its delta to the +0.55 seed:

| Year | Avg monthly basis | Δ vs +0.55 seed | Winter spike (delivered $/MMBtu) |
|------|-------------------|------------------|-----------------------------------|
| 2023 | +0.66             | **+0.11**        | Jan **$10.02** (HH $3.27), Feb $5.62 |
| 2024 | +0.49             | **−0.07**        | Jan $5.91, Dec $5.28              |
| 2025 | +0.89             | **+0.34**        | Jan **$8.54**, Dec **$8.20**      |

The annual-average deltas are small (±0.1–0.3), confirming the +0.55 seed is a
fair *annual* number (it matches the quantity-weighted +0.53/+0.44/+0.55 in
`constants.py`, which leans toward the high-volume summer low-basis months). But
the **monthly** series is the point: the implied winter basis reaches **+$2.7
to +$6.8** in Jan/Feb/Dec — exactly the Transco Z6 NY blowout a single annual
scalar flattens, and the gas-side input the dual-fuel switch (P13) keys off.

### Winter basis (U4) — NOT landed; falls back to 923

`data/raw/gas_basis_by_iso_month.csv` is still the **header-only
template** (zero rows) — the named-hub (Transco Z6 NY / Iroquois) leg is a
paywalled ICE/Platts product (see `data-acquisition-report.md` §1c), so **U4
has not landed.** `data.fuel.load_winter_gas_basis()` is wired and tested to
read it the moment rows appear (per-ISO monthly hub basis, downstate layer),
but until then it returns `None` and the gas path **falls back to the measured
EIA-923 ISO-month series** above. That series already carries a strong winter
shape (Jan-2023 $10.02 vs HH $3.27), just not the full *downstate-only* spike
that the hub-specific basis would add for NYC/Long-Island plants. Limitation
recorded; activation path is "fill `gas_basis_by_iso_month.csv` (U4), then the
loader layers it onto the downstate gas path for P13."

### RGGI carbon — active (default-on)

`STATE_CARBON_PRICE_BY_ISO["NYISO"]` = `{2023: 13.49, 2024: 20.71, 2025: 22.09}`
($/tCO2), the annual simple mean of each year's four quarterly RGGI auction
clearing prices (citations in `constants.py` and `parameter-citations.md`).
Default-on for NYISO backcasts via the same `resolve_carbon_price` machinery
CAISO uses (`carbon_price=0` → state program). At a ~0.40 tCO2/MWh gas-CC rate
this adds ~$5.4/MWh (2023) → ~$8.8/MWh (2025) to in-state fossil MC — within
doc-07 design-decision-4's ~$5–9/MWh band. RGGI carries **no border adjustment**
on imports (contrast CARB), so the NYISO import node is unaffected. ERCOT/PJM
stay carbon-free and CAISO keeps its CARB prices — all unchanged.

## 5. Upload manifest status (doc-07 U1–U7) (P0)

| # | Item | Destination | Status |
|---|------|-------------|--------|
| U1 | CAMPD unit-level `NY_2024.parquet` | `data/raw/campd-unit-level/` | **missing** — gates the 2024 backcast year + 2024 outage windows; 2023/2025 present |
| U2 | DA+RT hourly zonal LBMP (WEST/CAPITL/N.Y.C./LONGIL) 2023–2025 | `data/raw/lmp-data/NYISO/` | **landed 2026-06-12** — P10 price calibration done (scored against `actual_lmp.json` + `actual_lmp_hourly_NYISO.parquet`; see archived `docs/sessions/multi-iso/nyiso-backcast-2023.md` §3) |
| U3 | Zonal hourly load A–K 2023–2025 | `data/raw/zone-specific-demand/NYISO/` | **missing** — zonal load stays on static Gold-Book shares (0.365/0.175/0.06/0.28/0.12) until landed (P8) |
| U4 | Transco Z6 NY / Iroquois delivered gas basis 2023–2025 | cite into `constants.py` / gas path | **missing** — `gas_basis_by_iso_month.csv` is header-only; gas falls back to measured EIA-923 (see §4). Downstate winter spike not yet fully captured (P7/P13) |
| U5 | Niagara/St-Lawrence + Blenheim-Gilboa monthly generation (optional) | `data/raw/nyiso-hydro/` | **not needed yet** — EIA-923 monthly hydro is in-repo (P4 refinement only) |
| U6 | RGGI allowance prices 2023–2025 (optional) | cite into `STATE_CARBON_PRICE_BY_ISO` | **satisfied (web-search)** — RGGI auction clearing prices cited; active default-on (see §4) |
| U7 | Central-East / Total-East / Dunwoodie-South interface flows + limits (optional) | `data/raw/iso-specific-transmission/NYISO/` | **missing** — TTCs stay on Tier-3 Gold-Book seeds (P10 validation) |

U3–U4 unblock the remaining pack items (U2 landed 2026-06-12); the Stage-E
reference and fleet/CEMS audit are complete without them.

## 6. Out-of-scope observations for the backlog

- ERCOT/PJM calibration-reference staleness vs the new `Northeast` zone +
  EIA-860 vintage (§1b) — ERCOT/PJM-owned re-baseline.
- NJ CEMS (Bayonne/Linden) not wired into NYISO outage derivation (§3) — a
  small (5%) optional coverage gap.
- 2025 EIA-923 early-release respondent coverage (§1c) — national, re-run on
  the final file.
## 5. Dual-fuel winter switching (P13, verified 2026-06-11)

### Activation

The national dual-fuel machinery (`fleet.dual_fuel_plant_groups` detection,
the `oil` fuel type + `OIL` offer curve, `fuel.apply_dual_fuel_pricing`) is
**activated for NYISO** by setting `dual_fuel_switching` in the backcast config
(`_calibration_config`) for the winter-switching cluster — **PJM (existing) +
NYISO + NEISO**. Default-off for every other ISO (ERCOT/CAISO/MISO/SPP), so
their dispatch stays byte-identical (the ERCOT/PJM/CAISO regression guard). No
new LP code: the switch is an objective-only `min(gas_price, oil_price)` on the
fuel-price array, which `assemble_mc` multiplies by the unit's (gas) heat rate.

### Detection — NYISO dual-fuel units (EIA-860 Multifuel schedule)

`dual_fuel_plant_groups()` reads the committed EIA-860 Multifuel schedule
(`data/raw/eia-860/eia860_multifuel_operable.parquet`), flagging every
gas-primary (`Energy Source 1 = NG`) operable unit whose **"Switch Between Oil
and Natural Gas?" = Y** field is set, classed with the same canonical
`classify_plant` the fleet loaders use. Intersected with the NYISO model fleet
this matches **177 gas tranches / ~17.1 GW** of switch-capable capacity — the
downstate CT/ST oil-backup fleet doc-07 design decision 3 calls out:

| Plant | Code | Group | Switch cap (MW) | ES-2 backup |
|-------|------|-------|-----------------|-------------|
| Ravenswood | 2500 | CC_REGULAR | 1947 | DFO |
| Northport | 2516 | ST_GAS | 1592 | RFO |
| Roseton | 8006 | ST_GAS | 1222 | RFO |
| Bowline Point | 2625 | ST_GAS | 1160 | RFO |
| Astoria Generating Station | 8906 | ST_GAS | 923 | RFO |
| Linden Cogen | 50006 | CC_CHP | 915 | (NYISO-serving) |
| Bethlehem Energy Center | 2539 | CC_REGULAR | 813 | KER/RFO |
| E F Barrett, East River, Astoria Energy I/II, … | — | CT/ST | (balance) | DFO/RFO |

Source: EIA-860 (2023 release) Multifuel schedule, in-repo. Distillate (DFO) /
residual (RFO) fuel-oil backup; oil parity is `OIL_PRICE_PER_MMBTU = $18/MMBtu`
(distillate/residual delivered, `constants.py`, EIA "cost of fuel-oil delivered
to the electric power sector"), refined per month by the measured EIA-923
Schedule 5 Petroleum receipt series (`iso_monthly_oil_prices`).

### Switch logic & validation (Jan-2023 smoke window)

When the unit's delivered **gas** price exceeds **oil** parity the tranche bids
on oil; otherwise on gas. Validated on the real NYISO 2023 fleet:

- Mechanism is live: 177 tranches (17.1 GW) recognized and routed through
  `apply_dual_fuel_pricing` under the NYISO backcast config.
- On the **ISO-average measured 923 gas** the January gas leg is ~$10–12/MMBtu
  — **below** the ~$16/MMBtu Jan-2023 oil parity — so the switch is correctly
  wired but **does not bind** on the ISO-average series (0 binding hours).

### U4 caveat — winter validation limited until the Transco Z6 basis lands

The downstate **Transco Z6 NY / Iroquois** winter blowout (U4) is the leg that
pushes NYC/Long-Island delivered gas *above* oil parity; the ISO-average 923
series (§4) averages it away. U4 has **not landed**
(`gas_basis_by_iso_month.csv` carries no NYISO rows — paywalled ICE/Platts).
So: the dual-fuel **mechanism is activated and unit-tested** (parity switch +
ERCOT/PJM/CAISO-unchanged guard), but **winter binding cannot be validated
against the EIA-923/930 oil column until U4 fills the downstate hub basis** and
`apply_hub_basis_overlay` lifts the downstate gas leg past parity. Activation
path: fill U4 → the hub-basis overlay raises downstate winter gas → the already
-wired switch binds and prices Ravenswood/Astoria/Bowline off oil in cold snaps.

## 6. Upload manifest status (doc-07 U1–U7)

_P0 (Stage E) — to be written. P1-relevant: **U1 (`NY_2024.parquet`)** is the
only blocker for the 2024 backcast year and its outage windows; 2023 + 2025
are complete and current. **U4 (gas basis)** and **U6 (RGGI prices)** status:
U6 satisfied by web-search (RGGI auction results, cited); U4 still absent —
gas falls back to measured 923 (see §4), so the P13 dual-fuel switch is wired
but winter-validation-limited (see §5)._
