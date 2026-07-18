# NEISO winter fuel-inventory — data-intake audit (2026-07)

Records the DATA-INTAKE step of
`docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md` (component A
prerequisites): what measured inputs landed for a seasonal (Nov–Mar) oil-burn
budget, what is missing, and the exact derivation formula. **No model/LP
changes** — this is a data task only. New datatype: `winter-fuel-inventory`
(schema `data/dictionary/schema/winter-fuel-inventory.schema.yaml`, curation
`scripts/data/curate_winter_fuel_inventory.py`, raw
`data/raw/winter-fuel-inventory/`).

## Admissibility posture (CLAUDE.md #11 / #13)

The rule-#13 test — *could this same quantity be produced for a forward year
from forward drivers, and would it respond to changed conditions?* — was applied
to every candidate input. **Only forward-derivable physical/logistics capacity
quantities were intaken.** The measured **outcome** the plan warns about — F923
petroleum *receipts* (deliveries-to-tank, 1–2 plants reporting), the driver of
the rejected neiso-40 probe (`fuel.py:load_oil_burn_budget`) — was **not**
intaken, and neither were the OFSA comparison-only historicals (31.6 Bcf
actually-injected in 2014/15; 1.25 Bcf/d max-observed injection). This datatype
replaces a measured-outcome budget with a capacity+logistics budget.

## The derivation formula (what the budget is built from)

Per plant (or per zone-class group), per winter season:

```
budget_mmbtu = start_fill + delivery_rate × season_days
             = tank_capacity_start_fill  +  replenishment_rate × days
```

with the burn rate bounded above by the physical `firing_rate`, the fleet scope
set by `oil_limb_capacity` (dual-fuel oil limb) + oil-primary units, and
`annual_run_limit` capping total oil days/yr. Barrels convert to MMBtu via the
cited EIA heat contents (`MMBTU_PER_BBL_DISTILLATE = 5.825`,
`MMBTU_PER_BBL_RESIDUAL = 6.287`, constants.py); MMBtu → MWh via each unit's heat
rate. Every term is a forward-regenerable input; none is fitted to the price or
volume residual. **The LP wiring that consumes this is component A — out of
scope here.**

## What landed

### 1. EIA-860 per-plant (derived programmatically from the committed vintage)

`scripts/lib/winter_fuel_inventory/derive_eia860_rows` reads
`data/raw/eia-860/` (data year 2024) and emits, filtered to the six New England
states (ISO-NE footprint, exact):

| metric | rows | total | source field |
|---|---|---|---|
| `oil_limb_capacity` (MW, winter, dual_fuel) | 54 plants | **8,210 MW** | multifuel `Net Winter Capacity with Oil (MW)`, switch-capable, summed per plant |
| `firing_rate` (bbl/hr, annual, oil) | 15 plants | 1,175 bbl/hr | boiler design `Firing Rate Using Petroleum` (0.1 bbl/hr units, ÷10), summed per plant |

**Reconciliation note vs the plan's 6,831 MW.** The plan cites ~6,831 MW for the
dual-fuel gas units' oil limb; the committed EIA-860 vintage yields **8,210 MW
(winter) / 6,616 MW (summer)** across all 54 oil/gas-switch-capable NE plants.
The gap is scope: the plan's figure appears to restrict to *gas-primary*
dual-fuel units (excluding oil-primary steam that is also switch-flagged) and/or
summer ratings. The curated per-plant rows carry the truth at plant granularity;
component A should pick the scope (gas-primary subset vs all switch-capable) when
it sizes the constraint, not re-guess an aggregate.

### 2. ISO-NE fuel-security studies (hand-curated CSV, cited)

`data/raw/winter-fuel-inventory/isone/isone.csv` — from the **Operational
Fuel-Security Analysis (OFSA), ISO New England, Jan 17 2018**
([PDF](https://www.iso-ne.com/static-assets/documents/2018/01/20180117_operational_fuel-security_analysis.pdf)):

| metric | value | unit | citation |
|---|---|---|---|
| `tank_capacity` (fleet oil autonomy) | 10 | days | OFSA p.34 ("most tanks ~10 days' worth of oil") |
| `delivery_rate` (oil re-supply) | 2 | fills/winter | OFSA p.34 & Table 3 (reference; range 1–3) |
| `annual_run_limit` (air-permit oil cap) | 30 | days/yr | OFSA p.34 |
| `season_days` (winter horizon) | 90 | days | OFSA p.35 Table 3 (Dec 1–Feb 28) |
| `oil_fleet_capacity` (dual-fuel) | 8,750 | MW | OFSA p.12 fn3 |
| `oil_fleet_capacity` (oil-only) | 2,200 | MW | OFSA p.12 fn3 |
| `delivery_rate` (LNG system cap) | 1.0 | Bcf/d | OFSA p.34 & Table 3 (ref; range 0.75–1.5) |
| `delivery_rate` (LNG max injection) | 2.04 | Bcf/d | OFSA p.30 |
| `delivery_rate` (Everett/Distrigas) | 0.435 | Bcf/d | OFSA p.30 (sole fuel for Mystic 8&9) |

And from the **Winter Reliability Program (ISO-NE/NEPOOL, winter 2014/15, FERC
ER14-2407)** — the closest published *fleet-wide oil inventory in barrels*, a
program-design logistics target (admissible):

| metric | value | unit | citation |
|---|---|---|---|
| `start_fill` (aggregate target, low) | 2,800,000 | bbl | WRP 2014/15 (ER14-2407) |
| `start_fill` (aggregate target, high) | 3,800,000 | bbl | WRP 2014/15 (ER14-2407) |

Both range bounds are recorded verbatim (no midpoint invented); the downstream
derivation picks.

### 3. Winter-program / retention unit lists (component B's fuel-secure classes)

From the **ISO-NE Mystic Petition for Waiver, May 2018**
([PDF](https://www.iso-ne.com/static-assets/documents/2018/05/iso_petition_for_waiver_of_tariff_provisions.pdf)):

| metric | value | unit | citation |
|---|---|---|---|
| `winter_program_capacity` (Mystic 8&9) | 1,700 | MW | Mystic Petition p.5 |
| `winter_program_member` (plant 1588) | 1 | flag | Mystic Petition pp.3–5 |

## What is missing (DATA NEEDED — gaps, honestly flagged)

- **OFSA fleet start-of-winter oil inventory in barrels/MMBtu.** OFSA states it
  only as an *energy* curve ("Oil Inventory (GWh)", ~5,000 GWh on Dec 1,
  Figure 5 p.36) — no barrels/MMBtu printed. The barrels figure that *did* land
  is the WRP 2.8–3.8 M-bbl program target (above). Converting the OFSA GWh curve
  to fuel MMBtu needs the OFSA workpapers / per-unit tank table. **Not
  fabricated.**
- **Per-unit WRP participant roster.** The oil/coal steam units that actually
  held inventory under the 2013/14–2017/18 program are not published per-unit
  (competitive bid; commitments largely confidential in FERC ER14-2407 /
  ER13-1851). Only Mystic (plant 1588) is citably a program unit. The broader
  fuel-secure roster (Merrimack, Schiller, Canal, Wyman, Middletown, Montville,
  Bridgeport, Newington) is **not** enumerated in any single ISO-NE document —
  component B must assemble it from EIA-860 fuel/prime-mover + ISO-NE FCM
  qualified-capacity lists (a crosswalk, not an intake), NOT guess it.
- **ESI / Inventoried Energy Program oil replenishment cap.** ESI (FERC ER20-1567)
  is a market-design mechanism, not a fuel-inventory study; no fleet inventory or
  refill-cap assumption is published there. IEP (ER19-1428) converts on-hand
  stored oil to MWh but publishes no oil delivery-rate cap in the sources found.
- **Mystic 8 vs 9 individual MW split** (combined 1,700 MW only in the ISO doc).
- **On-site petroleum tank capacity in barrels/MMBtu per plant from EIA-860.**
  **This does not exist in EIA-860** — the plan's item-1 premise is only partly
  met. EIA-860 carries the oil-limb MW (multifuel) and boiler firing rate
  (design params) that landed above, plus Y/N flags (`Storage Limits?`,
  `Natural Gas Storage`, `Liquefied Natural Gas Storage`) — but **no petroleum
  tank capacity field**. Tank sizing comes from the ISO-NE studies (the 10-day
  autonomy + WRP barrel target), not EIA-860.

## Admissibility guard outcome

No re-scope was triggered: every quantity intaken is a forward-derivable
capacity/logistics input. The one place the plan's premise didn't hold (EIA-860
tank capacity) resolved to a *different admissible source* (ISO-NE study tank
autonomy + WRP barrel target), not to a measured outcome — so intake proceeded
without importing any F923-style deliveries/burn as a budget driver.

## Files

- Schema: `data/dictionary/schema/winter-fuel-inventory.schema.yaml`
- Registry lib: `scripts/lib/winter_fuel_inventory/{__init__.py, isone.py}`
- Curation: `scripts/data/curate_winter_fuel_inventory.py` (+ `regenerate_clean.py` DATATYPES)
- Raw: `data/raw/winter-fuel-inventory/README.md`, `isone/isone.csv`
- Constants: `MMBTU_PER_BBL_DISTILLATE/RESIDUAL` (constants.py, EIA MER cited)
- Test: `tests/test_curate_winter_fuel_inventory.py` (8 tests)
- Dictionary: `data/dictionary/data-dictionary.md` (regenerated)
