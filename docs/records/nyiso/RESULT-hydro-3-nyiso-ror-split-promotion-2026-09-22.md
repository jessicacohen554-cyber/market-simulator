# RESULT — hydro-3: `hydro_ror_split` promoted as NYISO keeper; determination falls to NOT-YET

**Session** hydro-3 (orchestrator; four year-isolated shards). **Date** 2026-09-22/23.
**New keeper** `2026-09-22-nyiso-hydro3-ror-split` (bundle `results/calibration/hydro3_nyiso_ror_span`).
**Superseded** `2026-09-20-nyiso247-fuel-invariance-disarm`, pruned in this session (rule 35 (a)).
**Owner rulings (verbatim):** `1` (promote, with the 2022 G2 miss attributed to the seam), then *"Is
this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates
regress that may still be a keeper."*

## Verdict

- **Structure:** the flat run-of-river class moves hydro toward the measured NYISO actual. The legs
  reproduce hydro-1's arm B exactly (R1).
- **Cost:** 2023 ST_GAS crosses the C1 share edge by 0.02 TWh. C3c is then no longer a lone
  failure, so the determination falls **CALIBRATED → NOT-YET**.
- **The pre-registered stop (PRECOMMIT P-A/P-B) FIRED** and was reported. The owner ruled promote
  with that on the table.

## Hydro shape (P1, conventional hydro, vs outgoing keeper vs NYISO actual)

| year | hydro TWh (G2) | p05 MW | p95 MW | actual p05 / p95 |
|---|---|---|---|---|
| 2022 | 25.554 → 25.522 (**−0.123 %**) | 1,725 → 1,725 | 4,002 → 3,937 | 1,940 / 3,958 |
| 2023 | 26.590 → 26.584 (−0.024 %) | 2,057 → 2,077 | 3,996 → 3,982 | 2,127 / 3,892 |
| 2024 | 26.739 → 26.739 (0.000 %) | 1,859 → 1,907 | 4,120 → 4,098 | 2,016 / 3,977 |
| 2025 | 24.059 → 24.059 (0.000 %) | 1,473 → 1,472 | 4,024 → 3,947 | 1,580 / 3,907 |

**The 2022 G2 breach is seam spill, not the nameplate clip.** See
`FINDING-hydro-3-nyiso-2022-g2-is-seam-spill-2026-09-22.md`: the outgoing keeper already spilled
629 GWh in 2022, during nyiso-237's fabricated ≤ $0 Upstate_West hours.

## Rubric, full span 2022–2025

| criterion | outgoing | incoming |
|---|---|---|
| C1 fuel mix | PASS (2023 ST_GAS +3.59 TWh / +3.0 pp) | **FAIL (2023 ST_GAS +3.61 TWh / +3.0 pp, share out of band)** |
| C2 volume, C3a mean LMP, C3b shape, C4, C6, C8 | PASS | PASS (C8 2022 −3.9 → −3.8 %) |
| C3c tail (h > $300, model vs actual) | 16/0/0/3 vs 101/10/13/42, lone → ledgered | 17/0/0/3, not lone → FAIL |
| **Determination** | **CALIBRATED** | **NOT-YET** |

## Method

- **Shards:** four, pinned `57e3c77f`, running `replay_keeper.py … --set hydro_ror_split=true`.
  Both warm-start knobs were off.
- **G-DRIFT** from 42d75053 to aaaaeb61: all inert.
- **Composition:** `scripts/probes/hydro3_compose_span.py` (it asserts the delta on every leg).
- **Attestation:** `scripts/gen_hydro3_attestation.py`, with the DOF ledger rebuilt. Zero DOF.

## Retrievability (rule 34 (e))

- **On `main`:** the composite slim bundle, the registry sidecar and the run payload. That is
  enough to re-score and to render the dashboard.
- **Legs and `dispatch/`:** gitignored. A re-registration from scratch costs a re-solve of about
  4 × 5 min across parallel shards. The shard SHAs in `.gitignore` are provenance, not a
  recovery route.

## Next lever

- **2023 ST_GAS over-dispatch.** It moved to the band edge under nyiso-247 and sits 0.02 TWh past
  it now. Restoring any margin there returns NYISO to CALIBRATED, with C3c auto-ledgered again.
- **The 2022 spill** stays with the Central-East seam (owner-gated, nyiso-224).
