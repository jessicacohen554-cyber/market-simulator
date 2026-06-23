# MISO Manitoba firm-hydro import (miso5 firmhydro) — run summary

**Determination: KEEPER (structure) / governance NOT-YET on metrics.** The
firm-hydro import block is the structurally-correct mechanism it was built to be —
it moves net interchange toward the EIA-930 actual in **all three years** and
behaves exactly as the physics predicts — so it is **default-ON** for the MISO
backcast. It does NOT close the level gap (C2/C3a still out of band), for the
documented pre-existing reason below; per CLAUDE.md #1 the correct structure
stays in regardless.

## What this run adds vs miso2 importnode baseline
A **separate firm-hydro IMPORT block** for **Manitoba Hydro** (~10–15 TWh/yr of
FIRM contracted hydro into MISO-North) — MISO's single largest real import source
and the structural reason MISO is a net IMPORTER. miso2 deliberately excluded it:
firm hydro has **no gas × heat-rate price analogue**, so it cannot enter the
gas-margin reference-price seam (`INTERFACE_NEIGHBORS["MISO"]` = PJM/SPP/SERC).
This run adds it as the documented next step.

Design (modeled on the NYISO firm-imports mechanism + the import-node wiring):
- A single `fuel_type="import"` pseudo-generator landed **directly in MISO-North**
  (the model zone the Manitoba HVDC / 500 kV ties physically enter), so it is
  counted as net interchange via its fuel type — NOT a gas×HR seam neighbour, and
  NOT entangled with the external-node SPP link.
- Priced as **firm hydro**: a low, near-constant energy offer
  (`MISO_MANITOBA_FIRM_IMPORT_OFFER = $8/MWh`) — well below MISO's gas-set LMP
  (so it clears inframarginally and displaces marginal gas), above the $0 dump
  floor (never games negative-MC credits).
- **Must-flow firm floor** (`inject_miso_firm_imports`, frac 1.0): the contract
  is firm, so the full **1,400 MW** flows every hour regardless of MISO's hourly
  price — verified 1,400 MW × 8,760 h = **12.26 TWh/yr** in every year.
- Volume sourced from the Manitoba Hydro export-contract band (~10–15 TWh/yr,
  midpoint ~12.3 TWh), **NOT fitted to the −38/−23/−19 TWh net-interchange
  residual** (CLAUDE.md #12: a firm contract regenerates for any forward year and
  responds to a changed contract).

Wiring: `MISO_FIRM_IMPORT_DEFAULT_ISOS = {MISO}` (`resolve_miso_firm_imports`)
makes the block active on MISO's plain run command; requires `--priced-interchange`
(MISO default-on). ERCOT byte-identical (no neighbour registry, block MISO-only).

## Result (model vs EIA-930 actual)
| year | net-ix miso2 base | net-ix **miso5** | actual (export +) | mean LMP base→miso5 | actual LMP |
|------|------------------:|-----------------:|------------------:|--------------------:|-----------:|
| 2023 | +0.1 TWh          | **−4.83 TWh**    | −37.91            | 28.71 → **28.54**   | 31.79      |
| 2024 | −7.5 TWh          | **−13.31 TWh**   | −23.08            | 25.49 → **25.27**   | 30.80      |
| 2025 | +45.0 TWh         | **+39.13 TWh**   | −18.96            | 36.78 → **36.40**   | 42.85      |

**Net interchange moved toward the EIA-930 import target in all three years**
(−4.9 / −5.8 / −5.9 TWh), and **mean LMP fell slightly** (−0.17 / −0.22 / −0.38
$/MWh) — both **exactly as predicted**: firm hydro adds cheap supply into
MISO-North, which raises imports while displacing marginal gas (so the LMP edges
down, not up). Reported honestly: the block both lowers LMP and raises imports.

### Why the gap only half-closes (the firm volume is 12.3 TWh, the move is ~6)
The Manitoba block delivers a fixed +12.26 TWh of must-flow import, but the
gas-margin reference seam **re-exports roughly half of it**: flooding cheap firm
hydro into MISO-North makes MISO's LMP even lower, widening the export spread vs
its correctly-priced PJM/SPP/SERC neighbours, so the seam exports ~6–7 TWh more.
Net movement toward actual ≈ 12.3 (firm import) − ~6.4 (induced extra seam
export) ≈ 5–6 TWh/yr. This is the **same pre-existing root cause miso2 filed**:
MISO's modeled LMP sits ~6/−14/−13% below actual, so a correctly-priced seam is
structurally export-biased. The firm block is right and stays in (CLAUDE.md #1);
fully closing C2 needs the **MISO price-level** fix (coal/gas offer-curve
calibration that lifts MISO's LMP to/above its neighbours), not a deeper or
cheaper Manitoba block (which would be fitting to the residual — forbidden #12).
2025 additionally over-generates coal (model 229 vs EIA-930 192 TWh), which the
seam exports — a separate C1 coal-supply/level issue, also pre-existing.

## Determination & default-on decision
The firm Manitoba import is **clearly the right structure** (forward-reproducible,
measured-anchored to the contract band, outside the gas seam, moves the residual
the right way in every year with physically-correct LMP/fuel side-effects), so it
is set **default-ON for MISO** (`MISO_FIRM_IMPORT_DEFAULT_ISOS`). It is a
structural keeper; the governance metrics (C2/C3a) remain out of band because of
the independent MISO price-level miss, which is the next pass.

## Carried forward (pre-existing, NOT this block)
1. **MISO price level** −6/−14/−13% — the coal/gas offer-curve level calibration;
   until MISO clears at/above its neighbours, a correct seam keeps exporting.
2. **2025 coal over-generation** (+37 TWh vs EIA-930) and the MISO coal-supply
   misclassification (no `coal_supply_MISO.csv`; SUB→PRB) miso2 filed.
3. **C5a CO2 benchmark-coverage bug** (28/1975 MISO gens missing eGRID rate).
