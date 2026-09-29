# FINDING — soco-86: `mustrun_layup_window_mask` is INERT for SOCO; the "~21 % offline" premise does not reproduce

Lane soco-86, 2026-09-28. Owner ruling (end of soco-85): take the lay-up-mask queue item. **Zero LP.** No PRECOMMIT and no
shards were written, because phase 0 shows that an arm would be byte-identical to the keeper (rule 32(a)). The keeper is
unchanged: `2026-09-28-soco85-gas-daily-shape`, NOT-YET, grade 7 / 4 / 0 / 1 / 2.

Probe: `scripts/probes/_soco86_layup_census.py` (default mode = the mask diff; `--offline`; `--excess`). All rebuilds are
`fleet_only`, on the keeper's own recipe via `replay_keeper.run_year_kwargs(soco85_span/meta.json)`.

## 1. The mask moves nothing, in any year

The field, loader and engine already exist (miso-173). A census of the keeper recipe with and without
`mustrun_layup_window_mask=true`:

| year | lay-up series loaded | pmax / mc / min_gen / availability differ | floor rows moved |
|---|---|---|---|
| 2019–2022 | 0 | no | 0 |
| 2023 | 3 | no | 0 |
| 2024 | 4 | no | 0 |
| 2025 | 2 | no | 0 |

**Why.** `campd-unit-outages-layup-SOCO.csv` (34 rows) is **coal-only**. SOCO-30 recorded the reason: the merit-order guard
needs a gas basis, and `gas_basis_by_iso_month.csv` has zero SOCO rows, so every gas unit drops out of the guard. The Gaston
rows are unit 5 (coal), not the gas boilers 1–4 that carry the ST_GAS floor. The mask therefore touches the coal tranches
only, and SOCO has no per-plant coal must-run floor for it to trim.

**2019–2022.** The file has no rows for those years, so the mask loads 0 series and does nothing. That is not "silently
masked or filled", but it is asymmetric. Moot here, since no year moves.

## 2. The rule-17 exposure is 0.4 %, not 21 %

The "~21 %" came from the soco-83 **greedy** (PRECOMMIT-soco-83 §3), which used a lambda-level floor. The **fleet-built**
floor is confined to the family's measured online windows. It reproduces PRECOMMIT-soco-83 §2's floor TWh exactly
(e.g. 2019: 0.850 / 0.675 / 1.129). Measured against CEMS gas-boiler output, plant grain, 2019–2025:

| cut | TWh (7 yr) | share of 19.086 TWh floor |
|---|---|---|
| Floor in hours where **every** gas boiler at the plant is dark | 0.078 | **0.4 %** |
| … in dark spells < 1 day | 0.012 | 0.1 % |
| … in dark spells 1–5 days | 0.058 | 0.3 % |
| … in dark spells ≥ 5 days (**the only spells any lay-up detector can see**) | **0.009** | **0.05 %** |
| Floor MW **above** the plant's measured gross output (plant is on, but below the floor) | 1.194 | 6.3 % (1.0–15.8 % by plant-year) |

**Ceiling.** Even a perfect gas lay-up companion, re-derived over 2019–2025, could reach at most **0.009 TWh** of floor energy
in seven years. The mechanism class cannot move SOCO.

**The 6.3 %** is part-load. The plant is running, but below the floor level in those hours. The only way to close it would be to
make the floor follow the measured output. Rule 13 forbids that: it pins commitment to an observed outcome.

## 3. Verdict

- Matrix cell `mustrun_layup_window_mask` × SOCO: **I (inert)**. Measured, not argued.
- No solve, no registration, no promotion. `soco85_span` stays the keeper.
- The ST_GAS floor has **no material rule-17 defect**. D-4 was already clean, and this census now puts a number on it.
- DO-NOT-REDO adds: the lay-up mask on SOCO, and any SOCO gas lay-up re-derive whose purpose is the floor (0.009 TWh ceiling).
