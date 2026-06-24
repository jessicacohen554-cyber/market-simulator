# CAISO COD + retirement ramp — per-class coverage audit (2026-06-24)

Branch: `claude/caiso-phase2-cc-chp-cod-wq4k7n`. Task C: audit that **every**
resource class is ramped from EIA-860 actual month-precise COD **and**
retirement, find/close any class that slips through, and add a per-class
coverage guardrail so a future fleet vintage can't silently drop a class.

## Method

Empirical audit (`scratch_cod_audit.py`, not committed): load the CAISO fleet
the runner builds (`load_fleet_from_csv` + `load_retired_within_window`),
resolve each generator's COD with `cod_ramp.effective_cod`, and tabulate, per
`(fuel, plant_group)`, how many units resolve a known EIA-860 online year and
how many carry a retirement date. Cross-checked against the solved 2024 fuel mix.

## Per-class coverage (CAISO, 2026-06 EIA-860 vintage)

| class (group) | units | MW | COD-known | from cod_map / own |
|---|---|---|---|---|
| gas_cc CC_REGULAR | 92 | 13 708 | **100%** | 92 / 0 |
| gas_cc CC_CHP | 56 | 2 707 | **100%** | 56 / 0 |
| gas_ct CT_PEAKER | 299 | 7 643 | **100%** | 299 / 0 |
| gas_ct CT_CHP | 136 | 1 962 | **100%** | 136 / 0 |
| gas_ct ST_GAS | 10 | 3 777 | **100%** | 10 / 0 |
| coal COAL | 2 | 50 | **100%** | 2 / 0 |
| nuclear | 2 | 2 240 | **100%** | 2 / 0 |
| oil | 27 | 143 | **100%** | 27 / 0 |
| biomass | 184 | 847 | **100%** | 184 / 0 |

**Every dispatchable thermal class the LP builds has 100% month-precise EIA-860
COD.** All resolve through the plant-code `cod_map` (none fall back to the
`Generator.online_year` path or the year-only registry). Retirement coverage is
"low" only because most snapshot units are not retiring — retirements ARE applied
per-unit (see below); the within-window retiree parquet injects the 26 mid-window
CAISO exits (1 066 MW) and they age out on their true EIA-860 retirement month.

## Classes NOT in the thermal LP fleet — where each is ramped

| class | path | COD ramp |
|---|---|---|
| wind, solar | `data/renewables.py` (`vintage_capacity_ramp`) | month-precise per-zone Operating Month/Year — separate, intentional |
| storage (battery) | `data/storage.py` (`storage_vintage_ramp`) | month-precise COD by vintage; pumped-storage year-only |
| hydro | `data/hydro.py` + EIA-930 measured **monthly** budget | aggregate monthly total — already reflects exactly what operated each month; no unit COD to ramp |
| **geothermal** | **dropped** (`_map_fuel_type` returns `None`) | **not unit-modeled — see below** |
| imports (WECC nodes) | synthetic tranches, `plant_code = 0` | **intentionally NOT ramped** (a transmission interface, not a generator) |

### Geothermal — the one class that "slips through", and why it is not a bug

`_map_fuel_type` returns `None` for geothermal, so EIA-860 geothermal generators
are not built as LP units. CAISO's ~11 TWh/yr geothermal (The Geysers) is instead
**absorbed consistently on both sides of the energy balance**:

- EIA-930 reports no separate geothermal for CISO — it is folded into the
  `NG: NG` (gas) column (documented at `eia_loader.py:629`). So the EIA-930 "gas"
  figure (88.0 TWh 2023) already contains geothermal + biomass.
- The model validates gas against **EIA-923 pure gas**, and the solved gas tracks
  it (2023 model 76.15 vs EIA-923 76.04 TWh), with biomass modeled separately
  (5.83 TWh). Net interchange is dead-on (2023 −29.75 vs −28.87; 2025 −36.31 vs
  −36.16). The balance closes **without** a geothermal unit because the demand
  series and the gas/import benchmarks are all on the same geothermal-netted
  basis.

Adding geothermal as a must-run supply block **without** also adding the
geothermal-served load back to demand would over-supply the system and push net
interchange more negative — breaking the won interchange match. Because
geothermal is ~flat baseload, a *consistent* add (supply + its served load) is
~price-neutral on the diurnal shape and does **not** address the midday body
residual. So geothermal stays a documented netting approximation, not a COD gap:
**there is no separate geothermal resource, hence no COD to ramp.** (Modeling
geothermal explicitly is a structural change well outside the COD-ramp scope; it
is logged here as a known approximation, not closed in this task.)

## Partial-plant retirement — handled for CAISO

`load_cod_map` records a plant-level retirement only when **every** unit of a
plant has a planned retirement (whole-plant). A partial retirement leaves the
plant-map entry's retirement `None`. This whole-plant limitation only bites the
ERCOT CAMPD bins (which carry no per-unit retirement of their own). For CAISO —
and every EIA-860 `Generator`-path ISO — `effective_cod` prefers the
**generator's own** `retirement_year/month` over the plant-collapsed date
(`cod_ramp.py:352`), so a unit inside a partially-retiring plant ages out on its
true EIA-860 month. CAISO therefore has no partial-retirement gap.

## The guardrail added

`cod_ramp.class_cod_coverage` + `cod_ramp.log_class_cod_coverage`, called inside
`generators_to_fleet_arrays` right where the COD ramp is applied. It tabulates
per-class COD-date coverage and emits a **WARNING** naming any class whose units
resolve **zero** EIA-860 COD dates — the signal that a fuel/class is silently
bypassing the vintage ramp (a future vintage that drops a class's build dates, or
a new fuel that never reaches `cod_map`, surfaces immediately). Synthetic
non-physical units (`plant_code <= 0`, the import tranches) are excluded by
design. Tests: `tests/test_cod_ramp.py::TestClassCodCoverage` (4 cases, trivial
single-class first). On the live CAISO solve the guardrail is silent (all real
classes covered), confirming the audit.

## Verdict

Every dispatchable EIA-860 resource class CAISO models is month-precision
COD-ramped (100%), retirements apply per-unit (no partial-plant gap), and
renewables/storage ramp through their own month-precise vintage paths. The single
class outside the ramp — geothermal — is a consistent demand-netted approximation
with no separate unit to ramp, not a dropped class. The new per-class coverage
WARNING locks this in so a future fleet vintage cannot silently drop a class.
