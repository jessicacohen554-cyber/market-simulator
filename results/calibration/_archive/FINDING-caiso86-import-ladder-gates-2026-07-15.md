# FINDING (caiso-86 measured import ladder, 2026-07-15): the measured WECC-corridor import ladder is NOT admissible via Q-Q duration coupling — the cheapest DSW solar rung is not year-stable (CV 0.99), so the derive-first honesty gates FAIL and the lever is NOT solved

**Session:** caiso winter-pricing bundles, 2026-07-15 (bundle 3 / the banked
caiso-83 / G-26 / issue #1350 / audit C-6 lane). **Derive-first, no LP solved.**

## 1. What was attempted

`scripts/derive_caiso_import_tranches.py` — the CAISO analogue of the NEISO
Q-Q seam-ladder derivation (`scripts/derive_neiso_import_tranches.py`) — was
written to replace the STATIC-FITTED `$/MWh` values in
`interchange_config.IMPORT_TRANCHES["CAISO"]` / `IMPORT_TRANCHES_BY_YEAR["CAISO"]`
(Tier-3 contract-cost proxies with no primary source, the open G-26 item) with a
measured, forward-reproducible derivation:

- **Flows:** per-corridor net import on the model clock from the measured
  EIA-930 CISO interchange (`WECC_PNW` = COI/Path-66 proxy hub MALIN, `WECC_DSW`
  = Path-46/WOR proxy hub PALOVRDE), via `CAISO_CORRIDOR_DIBA` /
  `_caiso_interchange_model_clock`.
- **Prices:** the measured Malin / Palo Verde intertie DA LMPs
  (`wecc_intertie_lmp_hourly_CAISO.parquet`; 2024/25 100% covered, 2023 77% —
  no Jan/Feb, handled by the pooled-distribution fallback).
- **Coupling:** each rung at cumulative-capacity midpoint `L` is priced at the
  DA hub-price quantile whose exceedance duration equals the measured duration
  of corridor net import exceeding `L` — the anti-monotone Q-Q coupling the
  NEISO / MISO / PJM seam ladders use.

The rung capacities follow the existing ladder's corridor breakpoints (the
measured depth-in-surplus evidence, caiso-82 §3: south-corridor p95 4.7/5.4/5.5
GW, year-stable); only the PRICES were re-derived.

## 2. The honesty gates (run BEFORE any solve — caiso-81 precedent)

Per-year derived rung prices ($/MWh):

| rung | 2023 | 2024 | 2025 | CV | gate |
|---|---|---|---|---|---|
| PNW_hydro_base | 61.6 | 43.2 | 42.5 | 0.18 | ok |
| PNW_midC | 90.5 | 89.1 | 62.0 | 0.16 | ok |
| **DSW_solar_PV** | **14.7** | **1.3** | **2.4** | **0.99** | **FAIL** |
| DSW_CCGT | 36.5 | 28.2 | 25.5 | 0.16 | ok |
| DSW_CT | 62.7 | 44.9 | 44.0 | 0.17 | ok |

- **Year-stability (CV ≤ 0.20): FAIL** — 4 of 5 rungs are year-stable (a
  revealed supply curve), but the cheapest DSW rung swings by a factor of ~11×
  across years.
- **LOYO (worst held-out rung error ≤ 25%): FAIL** on all three held-out years
  (2023 87%, 2024 580%, 2025 224%) — the error is dominated by DSW_solar_PV.

## 3. Why the cheapest DSW rung is not measurable this way

The DSW_solar_PV rung sits at a low cumulative level (~900 MW) that the corridor
net import exceeds in ~80–90% of hours, so the Q-Q coupling prices it at the
**~10th–15th percentile of the Palo Verde hub distribution** — the volatile low
tail dominated by midday solar-glut hours, where the desert-SW import price
swings between near-zero and negative and moves with the regional solar build
year to year (2023 a high-price year, 2024/25 progressively lower). That tail is
a real market feature, but it is **not a year-stable rung** the forward ladder
can carry, and the LOYO confirms it does not reproduce out-of-year. Adjusting
the rung placement or the quantile to make it pass would be tuning the method to
the gate — the exact residual-fitting the derive-first discipline forbids.

## 4. Disposition

**Bundle 3 (caiso-86) is NOT solved** (derive-first gate failure — the handoff's
explicit fail path). The static-fitted DSW/PNW price rungs remain labelled
STATIC-FITTED-PENDING-MEASURED (G-26 stays open). The four stable rungs
(PNW_hydro_base, PNW_midC, DSW_CCGT, DSW_CT) ARE measurable and year-stable, so a
**partial** measured ladder (measure the four grounded rungs, keep the solar rung
as an explicitly-labelled price-taker floor) is a defensible future design — but
that is a mixed measured/fitted ladder and a design call for the owner, not a
lever to force now. The derive script is committed as reusable infrastructure so
the gates re-run when the intertie-LMP source extends (rule 23).

The 2024/25 soft-month M-regime residual that caiso-84 exposed (May +81%, Jun
+41% in 2023; the analogous soft months in 2024/25) therefore remains open on
the import-ladder lane; caiso-85 (scarcity import-headroom) addresses the local
C3c tail on a separate, admissible mechanism.
