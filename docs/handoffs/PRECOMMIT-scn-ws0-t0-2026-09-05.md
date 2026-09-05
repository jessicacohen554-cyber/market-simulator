# PRECOMMIT — SCN-WS0 paired T0 (NEISO 2026)

Rule 29 `[R-SCREEN]` precommit, written and pushed **before** the lane's only
solve. Lane: SCN-WS0 (`claude/scn-ws0-k7m2-8743yi`), charter
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-0 / §7 "WS-0".

## 1. What is being solved, and what it is for

| | |
|---|---|
| **ISO** | NEISO |
| **Solve year** | **2026**, and only 2026 (a T0: one solve-year) |
| **Arms** | **REF** (`configs/scenarios/neiso_scenario_base_2026_2030.yaml` posture, window narrowed to 2026) vs **CARB** (`--set carbon_price_delta=25`) |
| **Concurrency** | the two arms are separate invocations with separate `--out-dir`s, launched together (rule 12 `[R-PARALLEL]`, ≤2 concurrent); each arm's own year loop is sequential and each arm is one year anyway |
| **Mode** | forecast (`ScenarioConfig.mode="forecast"`), so rule 22 `[R-HOLDOUT]` is not engaged — 2026 is a forecast year, no measured H1-2026 actual is read or scored |

**This T0 is not a mechanism test.** `carbon_price_delta` is a long-registered
field with a settled semantics (additive on the resolved carbon signal, after
`policy.carbon.resolve_carbon_price`'s whole precedence chain). Nothing about
it is under adjudication here. The pair exists to **exercise the new
accounting and reporting surface end to end on a real solve** — the emissions
grain, the widened matrix frame, `report_scenario_deltas.py`,
`collate_scenario_campaign.py`, the `--set` override and the `scenario`
registration kind. **No matrix cell moves and none may**: no mechanism is
tested, so no mechanism's verdict changes (rule 28 `[R-MECH-MATRIX]` duty (b)
is not triggered).

## 2. Expected response — sign, order of magnitude, footprint

Declared here, before the solve, so the STOP gate cannot be written to fit it.

- **Sign.** CO2 **falls** in CARB relative to REF, or is unchanged. A carbon
  adder raises the marginal cost of every emitting unit in proportion to its
  own rate, so it can only re-order the stack toward lower-rate units at a
  given load; NEISO load is identical in both arms (no demand axis is touched).
  A CO2 *rise* would be a defect, not a result.
- **Order of magnitude.** Small. $25/tCO2 on a gas-dominated NEISO stack moves
  a gas-CC unit's marginal cost by roughly its rate x 25 ≈ $9/MWh and an oil/ST
  unit's by more, so the re-ordering is **within the fossil stack** (coal and
  oil losing to gas) plus a modest thermal-vs-import shift. Expect a CO2 delta
  in the **low single-digit percent** of NEISO's annual total, not tens of
  percent: nothing in a single dispatch year can rebuild the fleet, and 2026's
  fleet is common to both arms.
- **Footprint.** Confined to (a) generation and CO2 **by fossil fuel class**,
  (b) the **import** tranches, whose merit-order position moves against a
  more expensive thermal stack, and (c) **prices**, which rise. Zero-carbon
  classes (nuclear, wind, solar, hydro) may shift only through the residual
  they are dispatched against, and their own emissions delta is exactly zero
  by construction (their rate is zero).
- **Unserved energy** is expected to be **unchanged**. A carbon adder changes
  merit order, not availability; a case whose CO2 falls because load was shed
  has not decarbonized, which is precisely why `unserved_mwh` now rides beside
  the CO2 line.

## 3. The STOP gate — structural, and it can only kill

Pre-registered, arithmetic/structural, and **never keyed on a residual**. The
gate has nothing to say about whether any number is "good"; it asks only
whether the new accounting reports the solve faithfully. It **may kill the
lane's deliverable; it may never promote anything**, contributes to no
determination, and is not a calibration verdict.

The arm is KILLED if any of these fails on either arm:

1. **The by-fuel grain partitions the total.** `Σ emissions_by_fuel_mt` equals
   `emissions_mt` to the summary's declared rounding grain (the dicts round at
   6 dp Mt, the scalar at 4).
2. **The by-zone grain partitions the same total.** `Σ emissions_by_zone_mt`
   equals `Σ emissions_by_fuel_mt` to 6 dp — the two are the same product
   grouped differently, so any disagreement is a grouping bug.
3. **The import line stays outside the total.** `import_co2_mt_reported` is
   reported, is not zero on NEISO (the HQ/NB/NYISO seams carry real energy),
   and is **not** included in `emissions_mt`: the by-fuel `import` entry is
   exactly 0.0, because the LP holds import emission rates at zero by design.
4. **The delta table reproduces the arithmetic.** For every fuel and zone, the
   report's `*_delta` equals CARB's own value minus REF's own value read
   straight from the two summaries; the cumulative CO2 delta equals the sum of
   the per-year deltas (trivially, one year); and the campaign rollup's
   single-ISO total equals that ISO's own `emissions_mt`.
5. **No non-target load-bearing criterion flips.** Both arms solve to Optimal
   for 2026 and the forecast invariants the runner scores do not go from pass
   to fail between REF and the arm for any reason attributable to this lane's
   accounting changes (which touch no LP row, no objective coefficient, no
   cache key).

**Additionally, and separately from the gate**, a CO2 delta of the wrong SIGN
(CARB above REF) is reported as a finding against the *model*, not as a gate
failure of this lane — it would be evidence about `carbon_price_delta`'s
behaviour on NEISO, which is SCN-WS1a/WS-1b's subject, and this lane would
route it rather than act on it.

## 4. Control provenance (rule 29 (b))

**Not applicable — no committed control is being differenced.** Both arms are
solved in this session, at the same HEAD, on the same config apart from the one
`--set` field, so G-CTRL form 4 (difference against a keeper's committed
numbers) is not used and no `G-DRIFT` audit is owed. The control here is a
control *solve*, which clause (b) permits — what it forbids is spending one to
establish HEAD drift against a keeper, which is not what this is.

## 5. Cost

Two NEISO invocations, one solve-year each, run concurrently. Wall and peak RSS
are recorded in `docs/handoffs/FINDING-scn-ws0-2026-09-05.md` when they land.
