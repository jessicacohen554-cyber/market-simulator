# Holdout data-equivalency gap register (2026-07)

Owner-ordered gating deliverable (2026-07-07, gap-register G-19): **no holdout
solve, no holdout score, and no holdout result may be recorded for ANY ISO**
until this register exists and the owner signs off per ISO. It answers, series
by series, the question in the governing handoff
(`docs/handoffs/holdout-data-equivalency-register-handoff-2026-07.md`):

> For each ISO x holdout window (2022; H1-2026): **is the holdout year's input
> set EQUIVALENT to the keeper years' (2023-2025) input set** - same source,
> same series, same granularity, same vintage/derivation recipe - for every
> input the keeper recipe actually consumes and every bench series the verdict
> scores against? "Present" is not the bar; **parity** is.

Grades: **EQUIVALENT** (same source/grain/vintage/recipe as 2023-2025);
**DEGRADED** (present but sparser grain, a different derivation vintage, a proxy
stand-in, partial-year, or a source substitution); **MISSING** (absent);
**ACCEPTED ABSENCE** (a structural absence that also holds in-sample or is
defined away by the scorer, not a gap to fill). Read CLAUDE.md rules 13/14/22/23.

## Summary matrix (ISO x window)

| ISO | 2022 (validation) | H1-2026 (locked test) |
|---|---|---|
| **NEISO** | **EQUIVALENT 21 / DEGRADED 2 / MISSING 1 (non-default limb) / accepted-absence 1** - owner sign-off pending | **BLOCKED** (publication horizon; blocked-until dates below) |
| ERCOT | audited pending (2022 intake landed 2026-07-04, §1.1) | BLOCKED |
| PJM | audited pending (2022 intake landed 2026-07-04, §1.1) | BLOCKED |
| CAISO | MISSING (no holdout intake) | BLOCKED |
| MISO | MISSING (no holdout intake) | BLOCKED |
| NYISO | MISSING for keeper-specific series (2018-H1-2026 measured *inputs* landed 2026-07-10, §1.2); bench MISSING | BLOCKED |

Only the **NEISO** section is authored in this lane (NEISO 2022 data-readiness,
2026-07-12). The other ISOs' sections are their own lanes; their matrix cells
above are a coverage pointer, not an audit verdict.

---

## NEISO

### Keeper recipe audited

The register audits the input **files** the frozen NEISO one-shot keeper recipe
consumes. There is live keeper-identity churn to record (it does **not** change
the audited file set - the recipe is an incremental mechanism stack on one base):

- `calibration-complete.json` names the frozen one-shot keeper
  **`2026-07-08-neiso-54-steamgas-ct`**, with the 2019 + H1-2026 locked test
  already scored once on **`2026-07-07-neiso53-winter-fuelsec-coldsnap`** (rule
  22, stands).
- `keepers.json` now carries **`2026-07-09-neiso-56-reserve-coopt`** as the
  current train-tier keeper (frontier note 2026-07-11).

neiso-53 -> neiso-54 -> neiso-56 share the neiso-50 base recipe (`--commitment
--reliability-floor --hydro-backfill-year 2024 --hydro-eia930-monthly
--gas-hub-basis-daily --scarcity-price-overlay --tranche-startup-amortization`)
plus the three winter fuel-security mechanisms; neiso-54 adds the CT_PEAKER
evening-ramp reliability drag, neiso-56 adds in-LP reserve co-optimization at
**static** requirements (a `ScenarioConfig`/`reserve_config` constant, **not** a
raw file). The one net-new *input file* across the churn is the reserve
requirement series, and only its **dynamic** variant (the neiso-57 Limb A probe,
**not** any keeper) reads a raw file - see the MISSING row. So this audit's
verdicts hold for whichever of neiso-53/54/56 the one-shot is ultimately run on;
the keeper-identity reconciliation itself is flagged to the owner in the exit
criterion below.

All 2022 rows are landed under the 2026-07-12 owner authorization
(`calibration-complete.json` intake_log), MERGE-not-replace, with every
2023-2025 in-sample row asserted byte-frozen before each write (no-LP; no solve).

### Driver inputs

| Input | file / loader | keeper-years (2023-2025) | 2022 | verdict | materiality | fix / note |
|---|---|---|---|---|:--:|---|
| Demand, hourly + zonal | `eia-930/ISNE_region_{year}.parquet`, EIA-930 shares | EIA-930 ISNE hourly | ISNE_region_2022.parquet present; calref demand 116.98 TWh / 24 233 MW peak | EQUIVALENT | high (sets net load) | landed |
| Demand profiles (8760) | `eia-930/eia_demand_profiles.parquet` | 2021-2025 | 2022 within span | EQUIVALENT | high | landed |
| Gas - Henry Hub | `HENRY_HUB_ACTUAL`, calref | measured annual mean | 2022 = 6.45 $/MMBtu | EQUIVALENT | high | landed |
| Gas - monthly AGT basis | `gas_basis_by_iso_month.csv` (`--gas-hub-basis-daily` base) | EIA MA-citygate proxy, 12 mo/yr | 12 months 2022 (Algonquin proxy) | EQUIVALENT | high | landed |
| Gas - **daily AGT basis** | `gas-prices/algonquin_citygate_daily.csv` | EIA Weekly-Update narrative scrape, ~40-50 prints/yr (weekly-anchored) | 62 prints (densified from 38), weekly-anchored | **DEGRADED** | high (winter tail) | see DEGRADED-1 |

### Fleet / overlay inputs

| Input | file / loader | keeper-years (2023-2025) | 2022 | verdict | materiality | fix / note |
|---|---|---|---|---|:--:|---|
| CAMPD unit-level (binning) | `campd-unit-level/{CT,MA,ME,NH,RI,VT}_2022.parquet` | per-state unit-hour | 6 states landed (schema-matched siblings) | EQUIVALENT | high | landed (2026-07-10 intake) |
| CAMPD facility-level | `campd-facility-level/*` | facility-hour | **not materialized** - `campd._read_one` resolves facility from the unit-level extracts (facility-first, unit-level fallback; TX-2023 parity bit-for-bit, F6) | EQUIVALENT | med | no fetch needed (loader fallback verified for MA_2022 = 567k rows) |
| Forward CO2 rate v2 | `_processed-legacy/plant_emission_rates_v2.parquet` | per iso/year | NEISO 2022 frozen-row merge (binary lander) | EQUIVALENT | med | landed by workflow |
| Emission rate v1 (pooled) | `_processed-legacy/plant_emission_rates.parquet` | pooled `year==0` override | pooled `year==0` is year-agnostic (applies to 2022); no 2022-specific rows needed | EQUIVALENT | med | pooled override consumed |
| Fossil CO2 rates (bench + rate) | `_processed-legacy/fossil_co2_rates.parquet` | per year | 2022 on true eGRID2022 vintage | EQUIVALENT | med | landed (F5 intake) |
| F923 coal plant-month pricing | `_processed-legacy/eia923_monthly_fuel_costs.parquet` | plant-month | 2022 present | EQUIVALENT | med (coal is <0.3% of ISO) | landed (F5 intake) |
| **Outage windows** | `campd-unit-outages-NEISO.csv` | committed 968 windows (unknown detector vintage, PR #1593) | +502 2022-start windows, HEAD detector vintage | **DEGRADED** | med | see DEGRADED-2 |
| Zone temps (reliability floor / winter) | `neiso-weather/neiso_zone_temp_daily.csv` | 4 zones, NOAA GHCN, `iso_zone_weather_stations.csv` weights | +1460 rows (2022 from committed h1/h2 splits) | EQUIVALENT | high (winter) | landed |
| Load-weighted temps | `neiso-weather/neiso_load_weighted_temp_daily.csv` | 6-station derive_neiso weighting | +365 rows (6-station re-fetch, frozen recipe) | EQUIVALENT | high (winter) | landed |
| Renewable capacity | `_validation-source/NEISO_2022_renewable_capacity.csv` + calref renewables | EIA-860 operable wind/solar, per-zone-month | 120 rows, EIA-860 vintage | EQUIVALENT | med | landed |
| Hydro monthly budget | EIA-923/930 monthly (`--hydro-eia930-monthly`) | monthly net-gen | ISNE 2022 in `eia923_monthly_generation.parquet` (1567 rows) + ISNE_fueltype_2022 WAT | EQUIVALENT | med | landed |
| Winter fuel-security params | `winter_fuel_inventory` / `neiso_gas_coldsnap_derate` / `neiso_winter_fuel_mustrun` | published WRP ER14-2407 -> IEP ER19-1428 -> OFSA (frozen, forward-derivable) | same published params (no year-specific 2022 file) | EQUIVALENT | low (dormant on 2023-2025) | rule-23 frozen; forward-derivable |
| Reserve co-opt requirement (neiso-56) | `reserve_config` static requirement | `ScenarioConfig` constant | same constant (no raw file) | EQUIVALENT | low (dormant at static req) | config, not data |
| **Dynamic reserve requirement** (neiso-57 Limb A, **non-keeper** probe) | `data/raw/NEISO-AS/requirements/` measured hourly RR | not consumed by any keeper | **raw CSVs absent for ALL years** (only README) | **MISSING** | low (probe engages 1 of 12 2025 tail hrs; not in the frozen keeper) | see MISSING-1 |

### Bench series (scoring targets)

| Bench | file / source | keeper-years | 2022 | verdict | note |
|---|---|---|---|---|---|
| C1 fuel-mix | `eia-930/ISNE_fueltype_2022.parquet` | EIA-930 ISNE by-fuel | COL/NG/NUC/OIL/OTH/SUN/WAT/WND present | EQUIVALENT | landed |
| C2 / C3 generation by-fuel | calref `generation_twh` (EIA-923) | per year | 9 fuels populated (ISNE 2022, 1567 rows) | EQUIVALENT | landed |
| C3 LMP (DA/RT + duration) | `_validation-source/actual_lmp.json` + `actual_lmp_hourly_NEISO.parquet` | SMD hourly per-zone | NEISO 2022 **DA 85.56 / RT 84.92**, full field parity (incl. `_lw`, zones) | EQUIVALENT | JSON via driver; hourly parquet via workflow |
| C3c scarcity tail | `frontend/data/backcast/tail/actual_tail.json` | >$300 DA/RT hour counts | NEISO 2022 **DA 27h / RT 117h** | EQUIVALENT | landed via driver |
| C5a emissions | `fleet-egrid/egrid2022_data.xlsx` | eGRID national | true eGRID2022 vintage present | EQUIVALENT | landed (F5 intake) |
| C5b/C5c storage throughput | EIA-930 storage breakout | 2023-2025 only | EIA-930 storage breakout **does not exist for 2022** in ISNE | ACCEPTED ABSENCE | scorer SKIPs; structural, not a gap (handoff item 6) |

### DEGRADED items (detail)

**DEGRADED-1 - NEISO daily Algonquin gas basis
(`gas-prices/algonquin_citygate_daily.csv`).** Weekly-anchored EIA-narrative
scrape in **all** years (the daily AGT spot is an ICE/Platts paywalled product;
EIA quotes it only in prose). This lane densified 2022 from the closing
session's basic ~38 prints to **62** (`fetch_algonquin_daily_spot.py`: the main
regex now spans the 2022-era change figure - "went up $3.73 from $18.96/MMBtu
last Wednesday to $22.69/MMBtu yesterday" - that the old `[^$]*?` choked on, and
`_AGT_CALDATE` recovers calendar-dated extremes like "$22.81/MMBtu on February
3"), cutting empty pages from 42/99 to 12/99. Verified: the compact EIA "Spot
Prices" table carries **no** Algonquin row in the 2022 pages either, so the
narrative stays the only free/citable source; an undateable high ("a weekly high
of $26.94/MMBtu in advance of the holiday weekend") is left out, never guessed
(rule 14). It stays **DEGRADED, not EQUIVALENT**: still weekly-anchored and
sparse, so days between prints fall back to the monthly plateau - understating
the Jan/Feb 2022 blowouts most, exactly where the winter tail forms. The
2023-2025 rows are keeper inputs and were held **byte-frozen** (123 rows, merge
freeze-proof). Materiality: high for the C3c winter tail. Further densification
is bounded by the prose (summary-stat weeks carry no single dated daily price);
constructing dailies from Henry-Hub + monthly basis is an estimate, not a
measurement (rule 14) - out.

**DEGRADED-2 - NEISO outage-window vintage
(`campd-unit-outages-NEISO.csv`).** The committed file (968 windows) does **not**
reproduce from a default-args re-derivation at HEAD: `derive_campd_unit_outages
--iso NEISO --years 2023 2024 2025` at HEAD gives **965** windows, silently
dropping the 34 Merrimack (2364) coal windows and adding ~30 others (Indian
Orchard, Dartmouth). So the committed in-sample windows are a **different
detector vintage** than a HEAD re-derive (unknown args/code vintage, last
touched PR #1593). This lane appended **only** the 2022-start windows (+502,
HEAD vintage) and left the committed 968 byte-frozen - so 2022 is on a
**different detector vintage than the in-sample windows it will be scored
alongside**. This is a **calibration-owner decision**, not resolved here. Two
options, both changing keeper inputs:

- **(a) Reconstruct the committed recipe** (recover the PR #1593 args/vintage
  that produced 968) and derive 2022 with it - keeps in-sample byte-frozen,
  makes 2022 vintage-matched.
- **(b) Pinned-vintage re-derive of ALL years** at one HEAD vintage
  (2022+2023+2024+2025 together) - vintage-consistent across the span, but
  changes the committed 2023-2025 windows (drops Merrimack), i.e. a keeper input
  change requiring a leave-one-year-out re-gate (rule 22) before promotion.

### MISSING items (detail)

**MISSING-1 - NEISO-AS measured hourly reserve requirements
(`data/raw/NEISO-AS/requirements/`).** The directory holds only a `README.md`;
the measured hourly reserve-requirement raw CSVs are **absent for ALL years**
(token-gated fetch, mirroring the NYISO reserve-price validation-side quarantine
in §1.2). Consequence: the **dynamic-RR limb** (`neiso-57` Limb A probe) cannot
regenerate from raw on a fresh clone. This is **not** a frozen-keeper input - the
promoted keeper (neiso-56) runs reserve co-optimization at **static** requirements
(a config constant), and the frontier note records the dynamic-RR limb as
engaging only 1 of 12 2025 tail hours. So it does **not** block the 2022 one-shot
of the frozen keeper. **Owner decision needed:** whether to commit the raw
NEISO-AS hourly RR exports (so the dynamic-RR limb becomes reproducible for any
future charter), or to leave the limb quarantined as validation-side only. Flag
only; not fixed in this lane.

### H1-2026 (locked test) - BLOCKED

Every H1-2026 NEISO series is publication-blocked (per G-19); rows carry
blocked-until conditions, not verdicts:

| Series | blocked-until |
|---|---|
| CAMPD unit-level / outages / v2 rates (fleet + bench) | EPA CAMPD Q2-2026 hourly posts (Apr-Jun 2026); Q1-only today |
| Delivered gas / daily+monthly AGT basis | EIA delivered-gas May-2026+ publishes |
| `eia_demand_profiles` (8760) | full-year build (F3: partial-year unbuildable by the 8760 contract) |
| Scoring-path registration (`CALIBRATION_YEARS`, bench, actual-tail part) | reference-year registration (F4), at one-shot time |
| LMP / fuel-mix bench | SMD 2026 workbook + EIA-930 ISNE 2026 (EIA-930 is the one series already complete through 2026-06-30) |

H1-2026 is a **locked test** (rule 22, touch-once): its intake and one-shot run
later, exactly once, under the same marker when the data publishes.

---

## Exit criterion

Per the handoff and rule 22, **owner sign-off on this NEISO section** is the exit
gate; only then may the NEISO 2022 one-shot be re-authorized (memo §4-§5 terms
apply verbatim). Two items are surfaced for that sign-off decision, neither
resolved in this data-readiness lane:

1. **Keeper-identity reconciliation** - the one-shot marker names neiso-54 while
   the dashboard keeper is neiso-56; confirm which frozen recipe the 2022
   one-shot runs (the audited *input files* are invariant across them).
2. **Outage-window vintage** (DEGRADED-2) - choose reconstruct-committed-recipe
   vs pinned-vintage-re-derive; the latter is a keeper-input change requiring a
   leave-one-year-out re-gate.

Separately (in its own NEISO/main lane, not this one): the NEISO keeper recipe
at current main no longer reproduces the keeper's registered 2023-25 prices
(+0.22/+0.38/+0.68 $/MWh; dual-fuel tranche count drift after the keeper's solve
commit `7f968f3`). That in-sample repro drift, plus this register's owner
sign-off, are what still block the one-shot; both stay in their own lanes.
