# PRECOMMIT nwpp-47 — arm `nwpp_grid_carried_wind_served` on the NWPP keeper

Written before any leg exists. Evaluator: `scripts/probes/_nwpp47_gates.py`, committed with this doc.
Evidence: `FINDING-nwpp-47-2026-09-22.md`.

## 1. The arm

- Recipe: keeper `2026-09-22-nwpp46-hydro-envelope`, replayed through `scripts/replay_keeper.py` from
  its own `meta.json` (so `--hydro-backfill-year 2024` rides along), with **one** change:
  `--set nwpp_grid_carried_wind_served=true`.
- No other field moves, and the offer bands are untouched.
- Rule 36: three single-year shards (2023, 2024, 2025), each with its own container and `--out-dir`,
  pinned to a full 40-character SHA. The parent composes with `scripts/probes/_nwpp42_compose_span.py`
  and runs `--restore-shared-inputs` before scoring. The parent runs zero LP.
- Rule 34(a): every shard pushes its full bundle, including `dispatch/<y>_P1.parquet`, using a
  `.gitignore` negation and a plain `git add`.
- Budget: ~60–90 min per year, up to ~3 h for 2024. Wall clock ~3 h in parallel.

## 2. The only input that moves (zero LP, `load_demand`)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| LP demand, keeper | 270.461 | 277.649 | 288.698 |
| LP demand, arm | 272.535 | 279.821 | 290.700 |
| Δ (= GRID's pool-carried wind) | **+2.074** | **+2.171** | **+2.002** |

Hourly Δ ranges from −8 to +498 MW, spread by load share. Everything else in the LP is byte-identical
by construction.

## 3. G-DRIFT (rule 29(b) form 4): keeper `87201a18` → base `336006c9`

Solve-path diff:
- `model/lp/model.py`, `model/lp/p0_cache.py`, `pipeline/solve.py`: the PERF-C S6 content-addressed
  P0 cache. It is env-gated by `MARKET_SIM_P0_CACHE`, **default off**, and the shards don't set it.
  **INERT.**
- `config/paths.py`: one path constant. **INERT.**

Every hunk is INERT, so the keeper's committed bundle is the control and no control solve is spent.
My branch adds the gated field; off, it is byte-identical (unit-tested).

## 4. Prediction, in C1's own units (reported, never a gate)

- Total P1 generation rises by the demand Δ (±0.1 TWh; storage losses).
- The recovered energy lands on the marginal thermal classes. Hydro, wind, solar, nuclear, biomass and
  OTHER are pinned to measured budgets or profiles, so they shouldn't move.
- **CC_REGULAR absorbs 0.5–1.0 of Δ** in every year. Coal together takes ≤ 0.3.
- **2023 C1 CC_REGULAR: −8.641 → [−7.60, −6.57] TWh** against the ±8.00 band.
- The rest of the gap (−7.6 / −10.0 / −7.1 TWh system) stays. It is FINDING §3's 930 under-book,
  which this arm doesn't touch.

Rule 1 `[R-STRUCT]`: the arm stands on the hourly identity (FINDING §2), not on C1. If C1 still
fails, the arm is still right. If C1 passes, that doesn't close §3.

## 5. Kill limbs (coded in the evaluator; either one means the run is not evidence)

- **PLUMBING / INERT:** the P1 demand Δ differs from §2 by more than 0.010 TWh, or total generation
  moves by less than 1.5 TWh in any year.
- **OVERSHOOT:** total generation moves by more than 2.6 TWh in any year, or any pinned class moves by
  more than 0.10 TWh, or any single class moves by more than 2.5 TWh.

Self-test: running the keeper against itself fires PLUMBING/INERT in all three years, as it should.

## 6. Retention

Shard bundles are pushed to shard branches (rule 34). The parent lands the composed bundle on `main`
only if the owner promotes (rules 31/33(f)). Promotion is the owner's call.
