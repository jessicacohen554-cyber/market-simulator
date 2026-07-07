# PJM 84 — online-gated deliverable reserve co-opt (G-20b)

**Probe (not a keeper). Keeper stays pjm-83-srmc-reground.** Full span 2023–2025,
one bundle, years sequential. Branch `claude/pjm-scarcity-price-formation-jran5q`.

## What was run

pjm-83 keeper recipe **verbatim** (`run_pjm84_online_gated_reserve.py`) + two
Phase-2 deltas that thin the reserve co-opt's *supply* toward PJM's real
synchronized-reserve product:

- `pjm_reserve_online_gated=True` — zone-aggregate reserve row becomes
  `R[z] − ρ·Σ_g P[g] ≤ 0` (ρ=1.0), so an idle (P≈0) unit backs **no** spinning
  reserve (`dispatch._build_reserve_rows:1311-1319`). This is the genuine
  "reserve ∝ online output" online-gate the G-20b brief describes.
- `measured_ramp_capability=True` — `FleetArrays.ramp10` reconciled against the
  measured ramp-capability datatype (EIA-860 "10M" fast-start floor + CAMPD CEMS
  1-h envelope ceiling; intake `data/clean/ramp-capability/PJM`, 749 plants),
  feeding the keeper's `pjm_reserve_supply_cap` deliverable cap.

**Not** the brief's third flag `pjm_reserve_pergen`: in `reserve_config.py:1285`
the pergen branch **returns before** the online-gate logic (mutually exclusive),
and pergen's joint `ΣP+R ≤ Σcap` headroom lets idle in-pool capacity back
reserve — which is exactly why the pjm-81 pergen probe fired only 1 h/3 yr. The
online-gate is the lever that actually removes the phantom idle headroom.

## Result — structurally-faithful NON-FIRE

Instrumented from `system.parquet` (reserve dual + energy dual) and
`dispatch/<yr>_P1.parquet` (fuel mix, online output):

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| reserve dual > 0 (h) | **0** | **0** | **0** |
| C3c energy tail > $200 (h) — model | **0** | **0** | **0** |
| C3c actual tail > $200 (h) | 6 | 18 | 59 |
| max energy LMP ($/MWh) | 63.0 | 56.5 | 129.4 |
| measured Primary req (mean MW) | 3284 | 3612 | 3538 |
| deliverable supply cap (mean MW) | 38 793 | 39 325 | 39 213 |
| effective reserve supply, min hour (MW) | 11 114 | 20 967 | 30 635 |
| min supply / req ratio | **3.4×** | **5.8×** | **8.7×** |
| min margin (supply − req, MW) | 7 830 | 17 355 | 27 097 |

**The reserve requirement never binds** — reserve dual is $0 in all 26,280 hours.
C3c energy tail is identical to the pjm-83 keeper (0 h all years).

### No dispatch distortion (rules 1 / 11)

Fuel mix vs pjm-83 keeper (model TWh): the co-opt did not re-dispatch to buy
scarcity — consistent with the $0 dual.

| fuel | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas Δ | +0.45 | +0.67 | +0.09 |
| coal Δ | +0.12 | +0.15 | −0.00 |
| nuclear Δ | +0.00 | +0.00 | +0.00 |

(gas < 0.2%; coal/nuclear byte-comparable.)

## Verdict — path A vs path B

**Path A (the LP-linear online-gate proxy) is insufficient.** `R ≤ ρ·Σ P` at the
documented ρ=1.0 ties reserve to *total* online output (tens of GW), not to online
*deliverable headroom*; even at the tightest hour the effective reserve-supply
bound sits 3.4×/5.8×/8.7× above the ~3.3–3.6 GW requirement, so the published
vertical two-step ORDC never engages and the co-opt dual stays $0.

**Path B is required:** an online commitment binary — or the P2 `fa_p2`
availability screen (which ERCOT uses to zero idle slow-start capacity out of the
reserve RHS) — to scope the ~39 GW deliverable cap down to the ~10 GW
online-deliverable slice (the `pjm-reserve-ordc.md` bind-gate measure). Only then
does online-deliverable reserve fall below the requirement in the genuine tail
hours.

This confirms the G-20 diagnosis empirically at the online-gated scoping: **PJM
scarcity is blocked on LP tightness (commitment posture), not on reserve
structure, memory, or ramp data** — all three are now confirmed non-blocking. The
requirement is not made to bind by lowering the curve, inflating the penalty, or
netting a headroom offset (rule 11); the honest outcome is a clean $0.

Note (G-20a boundary): C3c scores the raw energy-only LP dual, which is unlifted
here because reserves never bind — so there is no reserve price to settle into the
LMP. The G-20a settlement-scoring rescore is moot for this run (nothing to settle).
