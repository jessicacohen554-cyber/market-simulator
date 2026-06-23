# MISO import node (miso2 importnode) — run summary

**Determination: NOT-YET** (governance gate unattested; C2/C3a/C4/C5a still out
of band). This is a **PROBE**, not a keeper — see "Result" for why.

## What this run adds vs miso1 baseline
A **forecast-grade reference-price interchange node** for MISO (Module M4),
ported from the existing CAISO/NYISO/NEISO/PJM mechanism — NOT new LP structure.
MISO was energy-only (net interchange pinned at 0); it is in reality a large net
importer (EIA-930 −37.91 / −23.08 / −18.96 TWh, 2023-25).

Three real seams, each priced from the **neighbor's own** forward drivers (gas ×
heat-rate × its EIA-930 load shape), the LP clearing the volume on the spread vs
MISO's own LMP — nothing tuned to the net-MWh target (CLAUDE.md #1/#12):
- **PJM** → MISO-Central, 7,300 MW (PJM Data Miner tie-flow p99.5, the mirror of
  the PJM build's MISO seam). HR 12.3 = mean of PJM's MEASURED RT-LMP/HH ratio
  (11.2/13.5/12.2, against the actual Henry Hub).
- **SPP** → MISO-North, 4,000 MW (MISO/SPP JOA M2M; Tier 3). HR 10.0 (estimate,
  SPP IMM SOM ~$25.6/$22.8 / HH; ratios 10.1/10.4/~9.7).
- **SERC/South** → MISO-South, 3,000 MW (Entergy↔SERC; Tier 3). HR 12.0
  (estimate, ~$30 SERC bilateral / HH; ratios 11.8/12.3/11.9, SOCO load shape).

Wiring: `REFERENCE_PRICE_DEFAULT_ISOS = {MISO}` makes the node active on MISO's
plain run command; PJM stays opt-in, ERCOT byte-identical (no neighbor registry).
Manitoba Hydro (firm hydro into MISO-North, MISO's single largest real import
source) is **deliberately excluded** — firm hydro has no gas-margin price
analogue and no EIA-930 extract, so it cannot enter this gas×HR seam; a separate
firm-import block is the documented next step.

## Correctness fix made en route (rule #12)
`HENRY_HUB_TRAJECTORIES[2025]` held a **stale 2.88** forecast value while the
2025 actual Henry Hub is **3.52** (already in calibration_reference.henry_hub_
actual, and what MISO's own gas burn uses). The neighbor-price seam reads the
trajectory, so the stale value under-priced every neighbor by ~22% in 2025.
Updated 2025 → 3.52 (consumed only by the backcast neighbor seam; forecasts start
2026, ERCOT has no seam → ERCOT bit-for-bit unchanged). The PJM HR anchor was
re-derived against the corrected gas (12.3, was an erroneous 13.2 from the stale
value).

## Result (model vs EIA-930 actual)
| year | model net-interchange | actual (export +) | model LMP | actual LMP |
|------|----------------------:|------------------:|----------:|-----------:|
| 2023 | +0.1 TWh (balanced)   | −37.91 (import)   | 28.71     | 31.79      |
| 2024 | −7.5 TWh (importing)  | −23.08            | 25.49     | 30.80      |
| 2025 | +45.0 TWh (exporting) | −18.96            | 36.78     | 42.85      |

The node is structurally correct, measured-anchored, and clears bidirectionally
(it imports ~27/31/15 TWh **and** exports ~28/23/60 TWh). But **MISO's modeled
LMP is too low** (the pre-existing −6/−14/−13% level miss, unchanged from miso1):
sitting below correctly-priced neighbors, the seam **exports MISO's over-cheap
energy** instead of importing. So net interchange does NOT move toward EIA-930
(2024 imports modestly; 2023 balances; 2025 over-exports), and mean LMP does NOT
rise (C3a still −15%/−12%, essentially unchanged).

Per CLAUDE.md #1 the mechanism **stays in** even though the residual moved the
wrong way; the neighbor prices are **not** tuned down to manufacture imports
(#12). The real root causes for the next pass:
1. **MISO price level** — the offer-curve/level calibration that leaves MISO's
   LMP 6–14% low; until MISO's price clears at/above its neighbors in the hours
   it should, a correctly-priced seam cannot import.
2. **Firm-hydro imports** — Manitoba Hydro (~10–15 TWh/yr into MISO-North) is the
   structural reason MISO is a net importer, and is outside any gas-margin seam.

## Phase-0 diagnostics (filed, NOT fixed inside this work)
1. **C5a CO2 −43/−45/−37% (METRIC/SCOPE bug, file separately).** The scorecard's
   per-class CO2 *intensity* (render_calibration_html build_payload →
   egrid.class_co2_intensity) is computed only over plants present in
   egrid.fossil_co2_rate_map, then applied to the FULL EIA-923 class generation.
   MISO fossil plants missing a CEMS/eGRID rate (cf. "28 of 1975 MISO gens not in
   eGRID lookup") are dropped from the intensity but not the denominator → a
   near-uniform multiplicative undershoot. A benchmark-coverage bug, not a
   dispatch miss. Fix = add MISO fallback CO2 rates / reconcile the plant set.
2. **C1 COAL_BIT −63 TWh 2025 (MISCLASSIFICATION, file separately).** No
   `coal_supply_MISO.csv` exists; fleet.py only derives coal supply classes for
   ERCOT/PJM/NEISO. MISO coal falls through to the EIA-860 `energy_source`
   fallback, where Illinois-Basin/Appalachian bituminous coded `SUB` is tagged
   COAL_PRB (C1 shows COAL_PRB −132 TWh / COAL_BIT −63 TWh in 2025). Fix = derive
   + validate MISO coal supply classes from EIA-923 Schedule-5 receipts; not a
   cheap/clearly-correct in-place edit.

## Pre-existing registry note
`scripts/validate_parameters.py` is non-gating (no CI workflow runs it) and
already FAILs on 125 stale entries — including the existing `interface_neighbors.
PJM`, `import_zone.*`, and the merged `market_design.MISO`/`coal_price_base.MISO`.
The new MISO constants carry full sourced inline comments (the source of truth);
a registry refresh is left as its own pass.
