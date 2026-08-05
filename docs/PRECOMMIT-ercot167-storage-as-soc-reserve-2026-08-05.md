# PRECOMMIT — ercot-167: measured storage AS SOC reservation (`ercot_storage_as_soc_reserve`)

Committed BEFORE any solve (the ercot-162/165 discipline). Charter: mechanism-testing-matrix §5.1
**item 10** (owner-chartered at ercot-166; the `FINDING-ercot162-storage-rt-surface-refuted` §2 named
successor — "the AS/energy split of storage capability at scarcity", a QUANTITY object, not an offer
price). Owner execution directive (2026-08-05, this session): run all 3 years, **but 2023 had a
different market design for scarcity pricing, so test 2023 separately before running all 3
sequentially.**

## 0. Mechanism (single delta; zero fitted scalars)

`ercot_storage_as_soc_reserve=true` floors each ERCOT battery unit's SOC at

    soc_min(t) = pro-rata_by_energy_cap[ Σ_p share_p(t) × duration_p × committed_award(t) ]

- `committed_award(t)` = the SAME `storage` series `storage_as_commitment` already docks from the
  discharge power cap (`ercot_<year>_as_by_restype_hourly.parquet`) — one measured award basis for
  both the power side and the energy side (rule 19).
- `share_p(t)` = measured per-product PWRSTR award shares (RegUp / RRS / ECRS / NonSpin), new derive
  `scripts/data/derive_ercot_storage_as_products.py` (reconstruction reproduces the committed total
  EXACTLY for 2023/2024, max|diff| 0.0 MW; 2025's committed file is an older vintage, which is why
  shares×committed — never the raw per-product MW — is the consumption convention).
- `duration_p` = the co-opt's own published constants `ERCOT_AS_PRODUCT_DURATION_H` = (1, 1, 2, 4) h
  (Nodal Protocols §3.17.3 ESR SOC requirements; already cited in `docs/parameter-citations.md`).
- Guards: requires `storage_as_commitment` (validated), mutually exclusive with
  `ercot_storage_as_endogenous` (validated); missing series → all-zero floor (inert); clip at unit
  energy caps. Forward story: forecast prices the split endogenously (G5 lane) — this measured
  record is backcast-only capability input, never a pinned outcome (rule 13: the award is a
  procurement quantity that regenerates forward via the endogenous split, and the model dispatches
  *beneath* it — nothing pins output to actuals).
- Composition (rule 19 map, all pre-existing mechanisms unchanged): `storage_as_commitment` docks
  award POWER; `ercot_storage_as_deployment` floors the measured award DRAW-DOWN as ramp discharge
  (award(t) declines → BOTH the power dock and this SOC floor release automatically — same series);
  `ercot_storage_as_product_credit` nets the REQUIREMENT side. This adds the missing ENERGY-side
  reservation the power dock's own docstring names ("this reserves *power*, not state of charge —
  the first-order constraint that binds in the scarcity hours where the LP over-discharges").

## 1. Phase-0 measured facts (all from committed corpora, no solve)

- 2023, at the 61 actual RT >$1000 hours: batteries held **2,125 MW** of awards (p50) = **2,705 MWh
  frozen** of the fleet's ~4.1 GWh → ~350–470 MW sustainable over the scarcity evening. The
  delivery-2023 SCED corpus telemetry (PWRSTR TNO): the real fleet discharged **423 MW mean**
  (p50 327; HSL capability 3,277 MW). The keeper's LP discharges **666 MW mean** (p50 695) there —
  +243 MW over the measured actual. Aug 17–20h all days: actual 338 vs model 599.
- Product means (MW), 2023 / 2024 / 2025: RegUp 269/342/382; RRS 844/1,065/1,280; ECRS 120/573/523;
  NonSpin 15/167/640. Fleet SOC-freeze mean 1,414 / 3,224 / 5,265 MWh.
- 2025 (EIA-930 NG:BAT full coverage): model over-discharges the evening peak (18/19/20h net:
  +462/+1,268/+660 MW vs actual) while still charging at 15–16h; annual model 4.40 vs actual 5.45
  TWh net-discharge basis (−19%).
- 2023 regime note (the owner's point): ECRS launched 2023-06-10 and ran under CONSERVATIVE
  NON-RELEASABLE deployment until the 2024-08-01 reform (`ercot_ecrs_conservative_deployment`,
  armed). No new regime constant is introduced here: the measured award series itself carries the
  2023 design (what was held is what the DAM cleared), and the deployment draw-down mechanism
  already carries the release conduct. This is why 2023 is probed separately first.

## 2. The runs (rule 16 full-span for the A/B; rule 12 sequential — 15 GB box, ~10 GB/solve)

1. **PROBE (2023-only, THROWAWAY diagnostic — rule 16: never registered on the dashboard):**
   `python scripts/replay_keeper.py results/calibration/ercot165_unpooled_share_B
   --out-dir results/calibration/_ercot167_probe23 --year 2023
   --set ercot_storage_as_soc_reserve=true` — validates mechanism engagement, feasibility, and the
   G1 direction on the distinct-design year before spending the full span. Deleted or left
   unregistered; findings recorded in the session log only.
2. **Run A — control, fresh same-HEAD replay** (ercot150-K2 lesson): full span
   `--year 2023 2024 2025`, config UNCHANGED, `--out-dir results/calibration/ercot167_control_A`.
3. **Run B — arm**: same, plus `--set ercot_storage_as_soc_reserve=true`,
   `--out-dir results/calibration/ercot167_socreserve_B`.
   Both A and B are registered on the dashboard whatever the outcome (rule 15).

## 3. Pre-registered gates (verdicts read A→B; kill gates bind, no post-hoc softening)

- **G1 (target, 2023):** battery discharge in the 61 actual >$1000 hours moves DOWN from ~666 MW
  toward the measured 423 MW (report mean/p50; PASS if the A→B move is ≥ 40% of the gap toward
  actual, i.e. B ≤ ~570 MW; a move past actual below ~300 MW is an over-shoot flag, reported).
- **G2 (KILL — the ercot-162 volume collapse guard):** 2025 model net-discharge ÷ EIA-930 NG:BAT
  ≥ **0.70** on the arm (A currently ≈ 0.81; the ercot-162 refuted arm hit 0.24). Also report 2024
  on its covered window.
- **G3 (KILL — zero-spurious):** per year, spurious tail hours (model settlement >$200 where actual
  RT ≤ $200) must NOT increase A→B.
- **G4 (KILL — no-regress):** C1, C2, C4, C8 hold PASS in B; C3a/C3b 2024 and 2025 within ±1.0 pp /
  ±0.02 NRMSE of A; C7 gains no NEW failing rows (the 2023 COAL_LIGNITE cv-leg is expected
  unchanged — different mechanism).
- **G5 (KILL — no fabricated shed):** count of hours with system slack > 1 MW must not increase
  A→B in any year (A has 4 in 2023).
- **Report-only:** C3c counts per year (58/20/0 baseline — the rubric-v3.0 model-class ledger
  entries go inert on any PASS); the 2023 monthly Aug/Sep bias; evening 17–20h HOD gap movement
  (all years); the storage sidecars' discharge HOD shift vs the 930-BAT 2025 shape.
- **DOF ledger:** free_parameters_added = 0 (award series measured; durations published; shares
  measured; allocation pro-rata). LOYO (rule 22): the mechanism carries no cross-year fitted
  parameter — each year consumes its own measured series — so leave-one-year-out reduces to the
  per-year gate table above; any promotion decision reads it per-year.

## 4. DO-NOT-REDO honored

No offer-price transplant (`ercot_storage_rt_offer_surface` stays R / off); no aggregate energy
cap (ercot-159 R); no per-hour telemetered-HSL cap (rule-13 forbidden); no re-grain of the
envelope family (ERCOT-107/108 bistable). The endogenous duration gate (G5 forecast lane) is
untouched and stays default-off.
