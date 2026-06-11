# NYISO Data Audit

Companion to `docs/multi-iso/07-nyiso-prompt-pack.md` and the upload manifest
there (U1–U7). Each section is owned by the pack that filled it.

> **Scope note.** This file was started by **P1 (unit-outage windows)** with
> §3 (CEMS coverage / unit-outage detection). Sections 1–2 (calibration
> reference, fleet sanity) and 4 (upload-manifest status) are P0's to write or
> refresh; they are stubbed here so the section numbering matches
> `caiso-data-audit.md`.

## 1. Calibration reference

_P0 (Stage E) — to be written._

## 2. Fleet sanity

_P0 (Stage E) — to be written._

## 3. CEMS coverage

`states_for_iso("NYISO")` is **NY only**, so every NYISO-fleet fossil plant
that carries Part-75 CEMS reports under a NY state-year extract. Diff against
`inputs/raw-data/campd-unit-level/NY_<year>.parquet`:

| State-year | Unit-level extract | Notes |
|---|---|---|
| `NY_2023` | **present** | feeds `campd-unit-outages-NYISO.csv` (857 windows) |
| `NY_2024` | **missing** (upload U1) | 2024 stays statistical-availability-only |
| `NY_2025` | **present** | feeds `campd-unit-outages-NYISO.csv` (764 windows) |

2024 is the only gap. Until `NY_2024.parquet` lands (manifest U1, P0/P1),
an `outage_source="historic"` NYISO 2024 run carries no measured windows and
degrades to the statistical WEFOR/POF availability model for that year
(`unit_outage_derate_factors(2024, iso="NYISO")` returns `{}`; the fleet
assembly logs the "no outage windows cover NYISO 2024" warning by design).

### Unit-outage detection coverage (P1, verified 2026-06-11)

`campd-unit-outages-NYISO.csv` (**1,621 windows: 857 in 2023, 764 in 2025,
44 facilities**) regenerates **byte-identically** from the committed
`NY_2023`/`NY_2025` extracts via
`python scripts/derive_campd_unit_outages.py --iso NYISO --years 2023 2024 2025`
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

`inputs/raw-data/gas_basis_by_iso_month.csv` is still the **header-only
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

## 5. Upload manifest status (doc-07 U1–U7)

_P0 (Stage E) — to be written. P1-relevant: **U1 (`NY_2024.parquet`)** is the
only blocker for the 2024 backcast year and its outage windows; 2023 + 2025
are complete and current. **U4 (gas basis)** and **U6 (RGGI prices)** status:
U6 satisfied by web-search (RGGI auction results, cited); U4 still absent —
gas falls back to measured 923 (see §4)._
