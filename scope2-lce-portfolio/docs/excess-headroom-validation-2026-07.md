# ADR 0018 `excess_headroom_only` validation — ERCOT, three policies

- **Date:** 2026-07-04
- **ADR:** [0018](decisions/0018-storage-charge-excess-headroom-only.md)
- **Driver:** `examples/validate_excess_headroom.py`
- **Raw results:** `docs/excess-headroom-validation-2026-07.json`
- **Scope:** `scope2-lce-portfolio/` only — zero `market_sim` imports (real ERCOT
  CF shapes are read from the market-sim data tree by `scripts/build_profiles.py`
  as a file, never by importing the package).

## Goal

Run a single Mode B (matching-target) sweep three times — once under each
`storage_charge_policy` (`arbitrage` / `excess_clean_only` /
`excess_headroom_only`) against **identical** load, LMP and CF inputs — and
compare the frontier (matching% vs premium) plus the ADR 0018
`divert_backfill_mwh` diagnostic, to quantify what the strict excess-headroom
variant costs relative to the divert-and-backfill it removes.

## Inputs & honesty caveat

- **Load:** the deterministic stylized 100 MW flat data-center reference load
  (`scripts/make_reference_load.py`).
- **CF shapes:** real per-ISO 2024 EIA-930 wind/solar shapes for ERCOT
  (`scripts/build_profiles.py`, `profile_source == real`).
- **LMP:** the synthetic ISO-keyed dummy (`data/inputs/bau_lmp_2026_dummy.csv`).
  The market-sim BAU **forecast is on hold** (`PLAN.md` §10), so no real priced
  LMP exists to price against. **Premiums here are therefore NOT priced results.**
  What *is* valid is the **cross-policy comparison**: all three policies see the
  same inputs within a scenario, so the divert-and-backfill removed and the
  matching/premium *deltas* between policies are a controlled contrast even
  though the absolute premium level is a dummy-LMP artifact.

Because the flat load + modest-spread dummy LMP let cheap renewables dominate
(the portfolio goes ~100% clean at every target with near-zero grid buys),
divert-and-backfill **never fires** on that base case — a legitimate null
result, but one that quantifies nothing. So a second **scarcity-stress**
scenario overlays a synthetic ERCOT-scale scarcity price ($2,500/MWh, within the
ORDC/HCAP range) on the 200 tightest residual-load hours — the high-load /
low-renewable hours where a clean portfolio is most grid-exposed and storage
most wants charging it can only get by diverting. This is the 8760-hour analogue
of the unit-test's `$5/$500` divert case.

## Result 1 — base (dummy LMP): the mechanism does not fire

| target | policy | match% | divert_bf (MWh) | grid_buy (MWh) |
|-------:|--------|-------:|----------------:|---------------:|
| 0.80 | arbitrage | 99.97 | 0.06 | 295 |
| 0.80 | excess_clean_only | 100.00 | 0.00 | 0 |
| 0.80 | excess_headroom_only | 100.00 | 0.00 | 0 |
| 0.95 | excess_clean_only | 99.99 | 0.02 | 125 |
| 0.95 | excess_headroom_only | 99.99 | 0.02 | 125 |
| 1.00 | (all three) | 100.00 | 0.00 | 0 |

Premium is a constant **−580.2 $/MWh** across every target and policy (clean
build hugely undercuts the dummy BAU). Divert-and-backfill is ≤0.06 MWh out of
~876,000 MWh of annual load everywhere, so **all three policies coincide** —
`excess_headroom_only` costs nothing because there is nothing to remove. On real
ERCOT shapes with a flat load and no scarcity signal, the divert-and-backfill
residual ADR 0018 targets is simply not present.

## Result 2 — scarcity stress: the mechanism fires and is quantified

200 hrs @ $2,500/MWh on the tightest residual-load hours. All solves Optimal.

| target | policy | match% | premium | divert_bf (MWh) | grid_buy (MWh) |
|-------:|--------|-------:|--------:|----------------:|---------------:|
| 0.80 | arbitrage | 80.00 | −24,321 | **175,200** | 175,200 |
| 0.80 | excess_clean_only | 99.98 | −3,463.5 | 59.9 | 161 |
| 0.80 | excess_headroom_only | 99.60 | −3,436.1 | **0.12** | 3,490 |
| 0.95 | arbitrage | 95.00 | −24,004 | 43,800 | 43,800 |
| 0.95 | excess_clean_only | 99.98 | −3,463.5 | 66.3 | 170 |
| 0.95 | excess_headroom_only | 99.79 | −3,436.1 | 0.08 | 1,860 |
| 0.99 | excess_clean_only | 99.99 | −3,463.5 | 35.1 | 98 |
| 0.99 | excess_headroom_only | 99.97 | −3,436.1 | 0.11 | 252 |
| 1.00 | (all three) | 100.00 | −3,463.5→−23,898 | 0.00 | 0 |

Reading it:

1. **`arbitrage` is the maximum-divert baseline.** It charges storage straight
   from the grid to sell into the $2,500 scarcity hours (`divert_bf == grid_buy`,
   up to 175,200 MWh) and only bothers to hit the exact matching target — the
   grid-trading behavior the two restricted policies exist to forbid.
2. **`excess_clean_only` (ADR 0017) already removes ~99.97% of it** (175,200 →
   ~60 MWh) by blocking grid charging, leaving the small documented
   divert-and-backfill residual (35–66 MWh) the diagnostic was added to expose.
3. **`excess_headroom_only` (ADR 0018) removes the final residual** — 60 → 0.12
   MWh, i.e. down to the `EXCESS_HEADROOM_TOL_MWH = 1e-3` floor — via the cut
   loop, **and it does so at 8760-hour ERCOT scale, all solves Optimal.**

**Cost of the strict variant (vs `excess_clean_only`, per setpoint):**

| target | divert removed (MWh) | Δ matching (pp) | Δ premium ($/MWh) | Δ grid_buy (MWh) |
|-------:|---------------------:|----------------:|------------------:|-----------------:|
| 0.80 | 59.8 | −0.38 | +27.4 | +3,329 |
| 0.95 | 66.3 | −0.19 | +27.4 | +1,691 |
| 0.99 | 35.0 | −0.02 | +27.4 | +155 |

The strict cut costs a **consistent ~+27 $/MWh premium and ≤0.4 pp matching** to
remove the last tens of MWh of divert-and-backfill. The tell is the **grid_buy
column jumping** (161 → 3,490 MWh at target 0.80): because the cut pins the
*whole* offending hour's charging to zero, storage that could legitimately have
charged from same-hour surplus in that hour is lost, and the load it would have
served is backfilled from the grid instead. This is exactly the **conservative
under-use** ADR 0018 predicted — and empirically motivates the ADR's deferred
tighter cut (pin only the divert *quantity*, not the whole hour), which would
recover most of that +3,329 MWh of forced grid buys.

## Side finding — solver robustness fix (shipped)

The base sweep initially reported `excess_clean_only` /
`excess_headroom_only` as **`Unknown` / 0% matched at the two loosest targets**
(0.80, 0.90) while succeeding at 0.95+ — backwards, since a looser matching
target is an easier problem. Root cause: on the **degenerate / high-dimensional
optimal face** those loose targets create (≈100% matching achievable many
equivalent ways), the crossover-off IPM (`ADR 0003`, left off for speed) stops
at an interior point it cannot certify and returns model status `Unknown`, which
`build_and_solve`'s `solve_ok` gate then zeroes — silently dropping an achievable
frontier point to 0% matched. Confirmed by re-solving with crossover on
(→ Optimal, 100%).

Fix (`lp._solve_highs`): when the crossover-off solve returns anything other
than `Optimal`, **re-solve once with `run_crossover=on`** to certify the vertex.
The retry fires only on the rare non-Optimal path, so the happy-path speed is
unchanged, and a genuinely infeasible/unbounded model still surfaces its status.
Covered by `test_solve_highs_crossover_fallback` /
`test_solve_highs_no_retry_when_optimal`. This is an ADR 0017-era issue the
validation surfaced, not an ADR 0018 behavior.

## Reproduce

```bash
cd scope2-lce-portfolio
../.venv/bin/python scripts/make_reference_load.py
../.venv/bin/python scripts/build_profiles.py --iso ERCOT --year 2024 --market-sim-root ..
# base (mechanism does not fire):
../.venv/bin/python examples/validate_excess_headroom.py --iso ERCOT --out base.json
# scarcity stress (mechanism fires, tradeoff quantified):
../.venv/bin/python examples/validate_excess_headroom.py --iso ERCOT \
    --scarcity-hours 200 --scarcity-price 2500 --out stress.json
```

## Takeaways

- The ADR 0018 cut loop **works as specified at full 8760-hour ERCOT scale**:
  it drives divert-and-backfill to the tolerance floor in ≤3 solves, all Optimal.
- Its cost is small but real (~+27 $/MWh, ≤0.4 pp matching in the stress case)
  and is dominated by **forced grid backfill from the whole-hour column pin** —
  concrete evidence for prioritizing the deferred partial-charge cut if a use
  case needs the strict policy without the storage under-use.
- On realistic-but-unstressed inputs (flat load, no scarcity), divert-and-backfill
  is negligible and the strict policy is free — so `excess_headroom_only` is best
  understood as a **scarcity-regime** safeguard, not an always-on cost.
- A pre-existing solver-robustness bug (crossover-off `Unknown` on degenerate
  loose-target faces) was found and fixed as a byproduct.
