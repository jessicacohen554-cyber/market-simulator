# RESULT — NYISO-NEXT-18: the mid-vintage retiree carry (Indian Point 3) — 2026-09-30

- **Session:** NYISO-NEXT-18 (orchestrator; no LP in this container).
- **Phase 0:** `docs/FINDING-nyiso-next18-upstate-price-phase0-2026-09-30.md`.
- **Pre-registration:** `docs/PRECOMMIT-nyiso-next18-retiree-carry-2026-09-30.md`, merged in PR #6940 before any shard. Pin `6e0bd8b59bb1fcd17a21813aa92106a148ff57ab`.
- **Arm:** the NEXT-16 keeper recipe plus `mid_vintage_exit_carry`, `fleet_zone_vintage_coords` and `retiree_vintage_status_scope`, all true. Zero free parameters.
- **Registered (rule 15):**
  - `2026-09-30-nyisonext18-retiree-carry-span` (2022–2025): **CALIBRATED**, with C3c the lone ledgered caveat.
  - `2026-09-30-nyisonext18-retiree-carry-2021`: **CALIBRATED**. The keeper's 2021 run is NOT-YET.
- **Pre-registered rule: NOT PROMOTABLE AS WRITTEN.** G-6 fails in 2021 on one new D-4 row. Every other gate passes in every year.
- **Promotion is the owner's decision** (rule 31). NEXT-16 stays keeper until then.

## 1. Gates (arm vs the NEXT-16 keeper's committed bundles, form 4)

Record: `results/calibration/_nyisonext18_gates.json`.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| **G-1** leg acceptance (pin, 3-field delta, resolved inputs = keeper) | pass | pass | pass | pass | pass |
| **G-2** zone demand = keeper (≤ 0.1 GWh) | pass | pass | pass | pass | pass |
| **G-3** nuclear | Jan–Apr **+0.4 %** vs fuel mix (keeper −23.5 %); May–Dec = keeper | = keeper | = keeper | = keeper | = keeper |
| **G-4** P1 slack, GWh (keeper) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| **G-5** C6 / C8 | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS | PASS / PASS |
| **G-6** new D-4 rows | **bridge × ST_GAS 8906** | none | none | none | none |

**G-6 detail.** Astoria (8906) is floored by `nyiso_gas_commitment_bridge` for 1.2 GWh over 16 hours in 2021. It is metered at zero in 62.5 % of those hours. The same (mechanism, plant) row already fails in the NEXT-16/17 lineage (2022 and 2023). It is a known bridge conduct row, queue item 2. It is new to 2021 only because restoring Indian Point 3 re-shapes downstate commitment in Jan–Apr.

## 2. Reported (not gating)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| C3a, keeper → arm | **+11.1 → +9.2 %** (FAIL → PASS) | +2.6 → +2.4 % | +5.4 → +5.4 % | −1.1 → −1.1 % | −8.6 → −8.6 % |
| C3b NRMSE, keeper → arm | **0.178 → 0.147** | 0.159 → 0.158 | 0.132 → 0.132 | 0.117 → 0.117 | 0.147 → 0.147 |
| Upstate_West LW $, Jan–Apr, keeper → arm | 39.11 → 36.86 | 79.81 → 79.52 | = | = | = |
| NYC LW $, annual, keeper → arm | 44.62 → 43.91 | 85.86 → 85.63 | = | = | = |
| CE-binding hours, Capital − Upstate spread $: keeper / arm / measured | 2.11 / 2.04 / 19.12 | 4.66 / 4.65 / 48.03 | 1.77 / 1.77 / 17.73 | 3.74 / 3.74 / 21.42 | 6.09 / 6.09 / 35.94 |

- **The prediction held** (PRECOMMIT §5).
  - 2021 Jan–Apr prices fall about $2.3/MWh system-wide.
  - 2022 moves by ≤ 0.3 $/MWh; 2023–2025 are unchanged to the cent.
  - The CENTRAL EAST spread does not move. That object is still open (FINDING §1): the model's Upstate_West price is the eastern price carried over a link that does not bind.
- **2021 C3a crosses the ±10 % band on a measured-input repair, not a tuned value.** The remaining +9.2 % is mostly the CENTRAL EAST object.
- **Scoring basis.** Registration re-rendered the 2021–2023 bench parts for the arm's plant membership (Nassau Energy re-zoned UW → NYC; Astoria GT added in 2023). Those parts were **not** committed, so the keeper's view is unchanged. The arm re-scores CALIBRATED on both runs against the committed bench.

## 3. Legs (rule 36; provenance SHAs only, rule 33 (d))

| year | shard commit | files |
|---|---|---|
| 2021 | `0e599f30c0f324db773655fddf096a3ff954626a` | 17 |
| 2022 | `75ca0439c8eb8812c9b8e2a205476f876c93d4f9` | 17 |
| 2023 | `4dd67b9c4b28c5c1cde4f90a367207a84a51d5d2` | 17 |
| 2024 | `1615927d1258917c3d28978935b8b2df306c2ef0` | 17 |
| 2025 | `ba0ea8d71dca7c5eb8f48d3ea5d1788778bd83f2` | 17 |

- **Composition:** zero LP (`scripts/probes/nyisonext18_compose_span.py`). The span's shared benchmark inputs were rebuilt to the four-year frames; all ten hash-equal the keeper's.
- **Retrievability (rule 34 (e)):**
  - On `main`: both registered bundles in rule-15 shape (`results/calibration/nyisonext18_{span,2021}`: hourly sidecars, meta, metrics, diagnostics, attestation) and their run payloads.
  - Not on `main`: the per-year `dispatch/` parquets, by the repo-wide ignore. A promotion needs only what is on `main`. Re-deriving a unit-level question would cost a re-solve, about 6 min of LP per year.

## 4. Owner question

Promote `2026-09-30-nyisonext18-retiree-carry-span`, with the 2021 run stamped to it, despite the G-6 row? Or decline it?
