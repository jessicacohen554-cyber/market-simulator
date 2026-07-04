# Raw: winter-fuel-inventory

Forward-derivable capacity/logistics inputs that size a winter-season (Nov–Mar)
oil-burn energy budget for the fuel-constrained fleet — component A of
`docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md`. Curated into the
tidy `winter-fuel-inventory` clean datatype by
`scripts/curate_winter_fuel_inventory.py` (schema:
`data/dictionary/schema/winter-fuel-inventory.schema.yaml`).

**Admissibility (CLAUDE.md #11/#13).** This datatype carries physical/market
INPUTS only — quantities that regenerate for a forward year from forward drivers
(tank size, contract delivery rate, boiler firing rate, fleet roster) and
respond to changed weather/fleet. Measured burn/delivery **outcomes** (the
rejected F923 petroleum *receipts* — deliveries-to-tank, 1–2 plants reporting)
are **inadmissible** as budget drivers and must NOT be intaken here. See
`docs/multi-iso/neiso-winter-fuel-data-audit.md`.

## Two sources feed one schema

### 1. EIA-860 (per-plant, derived programmatically — no files added here)

Read from the committed `data/raw/eia-860/` snapshot (data year 2024) by
`scripts/lib/winter_fuel_inventory/derive_eia860_rows`:

- **`oil_limb_capacity` (MW, winter, dual_fuel)** — `Net Winter Capacity with
  Oil (MW)` from `eia860_multifuel_operable.parquet`, summed per plant over
  oil/gas-switch-capable generators. This is the dual-fuel gas fleet's oil-limb
  MW (the coverage hole that killed the neiso-40 monthly-F923 probe).
- **`firing_rate` (bbl/hr, annual, oil)** — `Firing Rate Using Petroleum (0.1
  Barrels per Hour)` from
  `eia860_enviro_equip_boiler_info_design_parameters.parquet`, summed per plant
  over boilers. Header unit is **tenths of a barrel per hour**, rescaled ÷10 to
  bbl/hr. Bounds how fast a plant can draw down its tank.

**EIA-860 does NOT publish on-site petroleum tank capacity (bbl/MMBtu).** The
plan's item-1 premise ("EIA-860 fuel-storage fields → tank capacity") is only
partly met: EIA-860 gives the oil-limb MW roster and the boiler firing rate, but
tank capacity / start-of-season fill / delivery rate come from the ISO-NE
studies (source 2). `Storage Limits?` (multifuel) and `Natural Gas Storage` /
`Liquefied Natural Gas Storage` (plant) are Y/N flags, not capacities. See the
audit doc.

### 2. ISO-NE studies + program filings (fleet/system/program, hand-curated CSV)

`isone/isone.csv` — canonical columns (`iso,entity,entity_type,plant_code,`
`season,delivery_year,metric,value,unit,fuel_kind,source_doc,source_page`), one
row per figure, each with an exact citation. `#`-prefixed lines are comments.
Populate from these public ISO-NE reports:

- **Operational Fuel-Security Analysis (OFSA), ISO New England, Jan 2018** —
  start-of-winter oil inventory assumption, tank capacities, oil re-supply /
  replenishment delivery-rate cap, LNG injection rate.
- **21st-Century Energy Security / Energy Security Improvements (ESI) filings,
  ISO-NE, 2018–2020** — start-of-season stored-fuel and delivery-rate
  assumptions.
- **Program / retention filings** — Mystic cost-of-service agreement (units 8 &
  9 + Everett LNG); ISO-NE Winter Reliability Program (2013/14–2017/18) oil/coal
  steam unit lists — for the `winter_program_member` roster consumed by
  component B's fuel-secure classes (COAL_BIT, ST_GAS).

## DATA NEEDED

- [ ] `isone/isone.csv` fleet/system rows: OFSA start-of-winter oil inventory,
      tank capacity, and delivery-rate cap (with page citations). Any figure not
      confidently published in a public ISO-NE report is left out and listed
      here, not guessed.
- [ ] `isone/isone.csv` program rows: Mystic + Winter Reliability Program unit
      lists (`winter_program_member`, value=1, unit=flag), keyed by EIA-860
      plant code where identifiable.
- [ ] Other ISOs: no analog intaken yet. PJM/MISO span partial states, so their
      EIA-860 derivation needs a plant-level membership resolver (a custom
      `parse` hook), not a state filter — additive when needed.
