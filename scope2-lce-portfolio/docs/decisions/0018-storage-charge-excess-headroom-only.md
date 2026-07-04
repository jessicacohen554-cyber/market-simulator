# 0018 — Divert-and-backfill diagnostic + `excess_headroom_only` charge policy

- **Status:** accepted
- **Date:** 2026-07-04
- **Session:** storage-modeling audit 2026-07 (`docs/storage-modeling-audit-2026-07.md`, §2.4)
- **Implemented by:** `lp.py` (`divert_backfill_mwh`, `solve_with_charge_policy`, `EXCESS_HEADROOM_TOL_MWH`), `config.py` (`storage_charge_policy`), `cli.py` (`--storage-charge-policy`), `outputs.py` (frontier parquet), `report.py` (ADR 0014 report)

## Context

ADR 0017 added `storage_charge_policy = "excess_clean_only"`: the per-hour rows
`Σ_s chg[s,t] + excess[t] ≤ Σ_r gen[r,t]` that stop storage from charging on
grid purchases or re-selling them. It left a **documented, accepted residual**:
"divert-and-backfill." In a single hour the LP may charge storage from clean
generation while grid purchases serve the load those MWh could have served —
the provenance row only bounds `chg + excess` by *total* clean generation, not
by clean generation *net of same-hour load*. The accounting stays honest (those
buys count unmatched and carry residual CO₂, ADR 0007/0013), but a buyer who
wants true excess-headroom-only charging has no way to get it, and no way to
even *see* how much divert-and-backfill a given frontier point carries.

The strict per-hour rule is `chg_t ≤ max(0, Σ gen_t − load_t)`. The `max(0, ·)`
on the right of a `≤` is **nonconvex**, so it cannot be a static LP row — and
the tool is LP-only (ADR 0003; no MIP/binaries). So the requirement can't be
expressed as one more constraint block; it needs a different mechanism.

## Options considered

1. **Static rows `chg_t − Σ gen_t ≤ −load_t` (i.e. `Σ gen_t ≥ load_t + chg_t`).**
   Linear, but wrong: they force generation ≥ load in *every* hour, even hours
   with no charging at all — over-restrictive, and infeasible whenever the
   portfolio legitimately leans on grid purchases. Rejected.
2. **Binaries / MIP** to encode the `max(0, ·)` exactly. Forbidden by the
   LP-only house design (ADR 0003). Rejected.
3. **Iterative cut loop around the ADR 0017 LP.** Keep the `excess_clean_only`
   rows; solve; find hours where storage both charged and bought from the grid;
   pin those hours' charge columns to zero (a column upper bound) and re-solve;
   repeat until none remain. Each solve is a pure LP; each hour is cut at most
   once, so it terminates in ≤ `T` iterations (in practice ≤ 3). Chosen.

## Decision

Two changes, both landing under `storage_charge_policy`:

- **Diagnostic (all policies, always on).** Every solve reports
  `divert_backfill_mwh = Σ_t min(Σ_s chg[s,t], grid_buy[t])` on
  `PortfolioResult`, in the frontier parquet, and in the ADR 0014 report
  (per setpoint). Zero means charging never coincided with a grid purchase.
- **New policy `"excess_headroom_only"`.** The ADR 0017 rows PLUS the option-3
  cut loop (`lp.solve_with_charge_policy`). An hour is "offending" when both
  `Σ_s chg[s,t]` and `grid_buy[t]` exceed `EXCESS_HEADROOM_TOL_MWH = 1e-3`
  MWh — a tolerance chosen to sit well above the crossover-off IPM's ~1e-6 MWh
  interior-point noise (ADR 0003) and well below any meaningful energy quantity.
  Offending hours are pinned (`chg` upper bound 0) and the LP re-solves.

This is a **conservative** restriction of the true nonconvex set: pinning a
whole hour's charging also removes any legitimate same-hour surplus charging it
carried, so the result can *under-use* storage relative to the true optimum. It
never *overstates* matching — the returned portfolio always satisfies strict
no-charging-while-grid-serves-load (up to tolerance).

## Consequences

- New config value flows into run metadata automatically (`asdict(config)`);
  CLI `--storage-charge-policy excess_headroom_only` overrides a config file
  (CL-1 pattern). `sweep.run_sweep` routes every solve through
  `solve_with_charge_policy`, so all other policies pass straight through to a
  single `build_and_solve` — no new rows or cuts when not selected.
- `divert_backfill_mwh` is now a column of the frontier parquet and a field of
  the ADR 0014 report payload (hover + table view), for every policy.
- Under `excess_headroom_only`, frontier premiums are generally ≥ those under
  `excess_clean_only` at the same matching (more storage value given up), and
  matching at a given premium can only fall or stay equal — the price of
  closing the divert-and-backfill residual.
- Isolation boundary unchanged: zero `market_sim` imports; the change touches
  only `scope2-lce-portfolio/`.
- Defers: a tighter (non-whole-hour) cut that pins only the divert *quantity*
  rather than the whole hour — would recover some of the conservative loss but
  needs a per-hour partial-charge bound the current column-pin mechanism can't
  express. Add only if a use case demands the extra storage utilization.

## Validation (2026-07-04)

`docs/excess-headroom-validation-2026-07.md` (driver
`examples/validate_excess_headroom.py`, raw
`docs/excess-headroom-validation-2026-07.json`) ran the three policies over one
Mode-B ERCOT sweep on real 2024 CF shapes:

- **On unstressed inputs** (flat reference load, modest-spread synthetic LMP)
  cheap renewables dominate, grid buys → 0, and divert-and-backfill never fires
  (≤0.06 MWh) — all three policies coincide, so the strict variant is free. It is
  best understood as a **scarcity-regime** safeguard, not an always-on cost.
- **Under a synthetic ERCOT-scale scarcity overlay** the cut loop works at full
  8760-hour scale, all solves Optimal: it removes the `excess_clean_only`
  residual (35–66 MWh → ~0.1 MWh, the tolerance floor) at a consistent **~+27
  $/MWh premium and ≤0.4 pp matching**. The cost is dominated by **forced grid
  backfill from the whole-hour column pin** (grid_buy jumps 161 → 3,490 MWh at
  target 0.80) — direct empirical motivation for the deferred partial-charge cut
  above.
- The validation also surfaced (and fixed) a pre-existing ADR 0017-era solver
  bug: crossover-off IPM returned `Unknown` on degenerate loose-target faces,
  zeroing achievable frontier points. `_solve_highs` now retries once with
  crossover on (see `docs/01-lp-formulation.md` Solver notes).
