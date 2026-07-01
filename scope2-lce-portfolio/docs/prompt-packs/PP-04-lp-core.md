# PP-04 — LP Core

**Upstream:** PS-02 (premium/netting), PS-04 (matching semantics).
**Targets:** `src/lce_portfolio/lp.py`.
**Status:** done (both modes, energy balance, gen ceiling, cyclic SOC, power/energy
bounds, premium & matching constraints, IPM solve, duals).

## Build / deepen

1. **Netting (PS-02).** Implement the decided excess-credit rule: fixed `f`,
   hourly/ISO-varying `f`, curtailment cap (a separate `curtail[t]` var with zero
   credit beyond a volume), and REC handling. Update `net_cost` + the premium row.
2. **Matching (PS-04).** Confirm/adjust the matching identity; if storage
   provenance matters, add the accounting. If residual carbon is reported, add an
   emissions-rate parameter and expose per-hour residual (feed PP-06).
3. **Cost representation (PS-01).** If pay-per-MWh is supported, branch the
   objective/premium terms accordingly.
4. **Hydro budget (PS-05).** Add the monthly-energy budget constraint for existing
   hydro (vectorized, per the market-sim pattern — copied, not imported).
5. **Duration-as-variable (PS-03, optional).** If storage duration becomes a
   decision, split power/energy build variables and adjust bounds.

## Invariants (keep)

- Fully vectorized construction — **no Python loop over hours** in the matrix.
- Prices/marginals from **row duals**. IPM + crossover-off for the storage
  network (see ADR 0003); revisit if exact vertex solutions are needed.
- `storage_epsilon` throughput tiebreak retained.

## Acceptance

`test_lp_trivial` (1 resource, 1 zone, 24 h) hits a hand-computed optimum;
`test_lp` covers energy-balance feasibility, SOC cyclicity, cap binding, and
premium/matching constraint correctness on a small multi-resource case.
