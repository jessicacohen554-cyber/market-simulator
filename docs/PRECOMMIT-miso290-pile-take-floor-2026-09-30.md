# PRECOMMIT — miso-290: per-yard monthly coal pile + MISO contract take floor, pre-check written before it is measured

```
LANE    : miso-290 (owner ruling "Pile + take floor (Recommended)", miso-289 §6)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds + keeper committed P1 hourly sidecars + run payload
PROBE   : scripts/probes/_miso290_pile_floor_precheck.py
          --census      : identification only (measured, §3; no price computed)
          --solver-test : INC + PILE0 (the miso-289 arms) on the revised solver (§4; no candidate)
          default       : INC / CAND emulation (run AFTER this file is pushed)
STATUS  : pre-registration. §3 census and §4 solver test measured; no CAND price or dispatch exists.
```

## 1. The candidate (CAND)

One row family replaces the pooled flat `B/12` limb (`coal_fuel_inventory`, rule 19): the per-yard
cumulative month-end pile (NWPP-NEXT-8 `build_coal_monthly_pile`, ratable receipts), bounded on **both**
sides — the coherent inventory band `S_floor <= pile_m <= S_max`:

    max(0, S_dec - S_max + m/12 * C) * hc  <=  sum_{g at yard, t <= end of m} HR[g] P[g,t] (+ shortfall)
                                           <=  S_dec*hc + m/12 * R  -  S_floor

- **Ceiling** = miso-289's (`S_floor` = `min(d_min/365 * R, S_dec)`, unchanged). **Decided ex ante: the
  minimum-stock term STAYS.** Reason (structure, not result): the pile is one stock with a lower operating
  limit and an upper capacity; the floor side is the capacity limit on contract receipts, the ceiling side
  the operating minimum. Dropping either leaves a one-sided pile. One variant only; not swept.
- **Floor** = the NWPP-NEXT-7/8 construction with MISO's own census: contract receipts can only be absorbed
  into the pile up to the most it has held; the rest must be burned. **SOFT**, each yard's shortfall priced
  at its own delivered coal cost (`coal_take_shortfall_price`, the fuel price the model already charges
  those units). A shortfall enters every later month-end row, as in the LP.
- **Rule 19.** CAND disarms `coal_takeorpay_from_data` and `coal_committed_takeorpay_regulated` (both armed
  in the keeper). The contract is carried once, by the floor's dual; `resolve_coal_take_floor` raises on
  the stack, so this is the construction, not a choice. CAND therefore clears on a rebuilt offer stack.

## 2. Identification (rule 13, rule 21 — fixed before measuring)

Per yard row (the keeper's `coal_yard_groups`) and solve year `Y`:

- **`C`** = the yard's mean annual contract tonnage (EIA-923 Page 5, purchase types C/NC/T =
  `TAKE_PURCHASE_TYPES`) over **the same two prior years that size its receipts rate `R`**
  (`build_coal_plant_budget`, `n_rate_years = 2`). Same window, same divisor, so `C <= R` by construction.
  (NWPP used `Y-1` only; the two-year window is chosen for coherence with `R` and is not a transfer.)
- **`S_max`** = the yard's largest month-end stock over `[Y-3, Y-1]` (EIA-923 Page 2). **Window coverage,
  stated before measuring:** stocks start 2018, so 2019 uses 2018 only and 2020 uses 2018-2019. A shorter
  window can only LOWER `S_max`, which raises the floor; that is reported, not corrected. Since `Y-1` is
  in the window, `S_dec <= S_max`, and with `S_floor <= S_dec` and `C <= R` the floor never exceeds the
  min-stock ceiling.
- **`S_dec`**, **`hc`**: the budget's own (Dec `Y-1` stock; quantity-weighted rate-window heat content).
- **Shortfall price**: per yard, `coal_take_shortfall_price` (year-mean delivered coal $/MMBtu, weighted by
  `HR x pmax`). No new quantity.
- Missing input: no Dec `Y-1` stock or no receipts in the window → no floor (never substituted).
- **Clips** (the NWPP ones, fixed): floor ≤ ceiling, floor ≤ what the yard's rowed units can burn by
  month-end.
- **Forward story.** `C` and `S_max` regenerate from the prior years' Page 5 / Page 2 in any year; in a
  forecast, from the contract book carried forward and the model's own simulated pile.
- **DOF ledger.** `C`, `S_max`, `S_dec`, `hc`, shortfall price: measured, prior years. `SMAX_WINDOW = 3`:
  structural declaration (same as miso-289's `WINDOW`). `N_RATE_YEARS = 2`: the budget's own. Zero fitted.

## 3. Census (measured with `--census`, identification only)

CENSUS_TABLE

## 4. The emulator and the solver fix

The miso-289 emulator (P1 bid stack = `mc_base` + startup markup, cleared hourly at the keeper's P1 LP
quantity excluding wind, solar, biomass and OTHER; markup from the incumbent's floors, shared by every arm;
must-run floors reconciled to each arm's own rows). Cumulative rows: hour `t` of yard `y` carries
`HR * nu[y, month(t)]`, `nu = revcumsum(lam - mu)`, `lam >= 0` ceiling duals, `mu >= 0` floor duals, `nu`
clipped below at `-shortfall_price` (the soft floor: where it binds the deficit is paid and carried
forward, not counted as a violation).

**Solver fix (fixed here, before CAND is cleared).** miso-289's projected subgradient left one cumulative
row oscillating (PILE0 residual 0.83, CAND 0.49 at 200 iterations; INC 0.019). Revised: per-coordinate
adaptive steps start at $2.0/MMBtu per unit relative violation (miso-289: up to $5), halve on a sign
flip, grow ×1.1 capped at the start value; 240 iterations; tail dual averaging over the second half; the
returned point is the lowest-residual of every iterate and the averaged duals (selected on feasibility
only, never on price). Validated on the two non-candidate arms:

SOLVER_TABLE

**Convergence gate (new, fixed now).** A CAND year counts as PASSING only if its returned residual is
≤ **0.05**. A non-converged CAND year cannot pass; a FAIL verdict with residual > 0.05 is reported with
its residual and still stops the lane.

**Gate V (as miso-289):** INC monthly coal within **±1.5 TWh** of the keeper's P1 monthly coal in every
month, annual within **±3 %**, in every year run. INC − keeper P1 night median is reported (shared level
bias); every price criterion is a **CAND − INC** delta.

## 5. Kill rule (fixed now)

2022 is run first. If 2022 fails V, K1, K3, K4 or K5, the lane stops there. Otherwise 2019–2021 and
2023–2025 are run and every criterion is checked in every year.

- **K1.** 2022 CAND night (h0–5) median ≤ INC − **$2.0**.
- **K2.** No year's CAND night median > INC + **$0.5**.
- **K3.** Jul+Aug CAND coal ≤ **1.10 × bench** Jul+Aug, in every year where CAND has a binding row.
- **K4.** Every year: |CAND annual coal − bench| ≤ |INC annual coal − bench| + **5 TWh**.
- **K5 (winter guard — how miso-289 died).** Every year: |CAND Jan–Apr coal − bench Jan–Apr| ≤
  |INC Jan–Apr coal − bench Jan–Apr| + **3 TWh**.

All pass (and converged) → build default-off (un-gate the take floor / monthly pile for MISO on this
census; matrix cells in the same PR), then the seven year-isolated shards (miso-280 template §7/§8, rules
34(c)/36). Any fail → FINDING, matrix, owner card. **No threshold, window, variant or month set moves after
the CAND run starts.** Bench coal = run payload `volErr` COAL_* `a` (EIA-923 basis).

## 6. What this does not claim

- C3a is a mean over all hours; the mean shift is reported, not gated.
- A surviving candidate's deltas are emulator deltas; the shards are still owed.
- It does not address why ~86 % of coal MW sits under a binding yard (miso-288 §4(b), offer-level,
  data-gated).
