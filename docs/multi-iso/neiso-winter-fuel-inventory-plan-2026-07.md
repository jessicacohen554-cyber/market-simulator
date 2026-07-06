# NEISO winter fuel-inventory / seasonal-reliability build — scoping proposal (2026-07)

**Status: Component A (the oil seasonal-budget LP rows, `winter_fuel_inventory.py` +
`dispatch.py:_build_oil_budget_rows`) has landed, GATED `neiso_winter_fuel_inventory`
(default off) — a probe run found the inventory cap inert (oil still under-ran). Component
B (winter must-run) remains unbuilt.** This is the scope for the next NEISO
model experiment on record. It is the *only* sanctioned lever for the remaining
NEISO model-miss family, per the neiso-41/43 attestation ("Closable only via the
documented future build (fuel-inventory / seasonal-reliability constraint),
NEVER by cranking the floor slope/cap or by an offer adder") and
`neiso-ps-undercycling-diagnosis-2026-06.md` ("do not touch the storage
formulation to move that number").

## What it must close (and what it cannot)

One structural root cause, four symptoms — all ledgered in
`results/calibration/neiso_closeout/calibration_attestation.json`:

| Symptom | Model vs actual | Criterion |
|---|---|---|
| Winter COAL_BIT under-run | 0.058/0.113/0.234 vs 0.181/0.238/0.271 TWh (2023/24/25), ST_GAS similar | C1 (within band, ledgered MODEL MISS) |
| Scarcity tail collapsed | 0h >$300 vs actual 15/8/20h; LP capped at dual-fuel oil-parity ~$258 | C3c (soft caveat) |
| PS/storage under-cycling | 0.72 vs 2.08 TWh discharged, 2025 | C5b (soft caveat) |
| Storage monthly shape | r=0.237 vs ≥0.5, 2025 | C5c (soft caveat) |

**Determination impact — stated up front so nobody oversells this build:** it
can close the three *soft* caveats. The two *hard* caveats on neiso-43 (C1
CC_REGULAR and C2 2025 sysvol) are EIA-930 gas-cell fold-in / preliminary-vintage
*measurement* issues, explicitly "NOT closable by adjusting model dispatch."
With `MAX_HARD_CAVEATS = 1`, NEISO stays NOT-YET on the hard budget (2/1) even
after this build, until either (a) the final 2025 EIA-923 vintage lands and the
per-class gate replaces the C2 family fallback, or (b) the geothermal+biomass
NG-cell fold-in is reconciled on the benchmark side (a rule-#14
measurement-alignment fix — separate workstream, arguably the cheaper path to
flipping the determination). This build is justified on structural faithfulness
(rule #1), not on the verdict flipping.

## Why the LP misses it

Real ISO-NE winters have two mechanisms the perfect-foresight, unbounded-fuel
LP lacks:

1. **Finite winter fuel inventory.** Oil tanks (and LNG injections) are a
   season-scale *stock* rationed across cold snaps; the shadow price of that
   stock is scarcity rent above oil-parity. The LP prices delivered oil as an
   unlimited flow, so the cold-hour price ceiling is the oil-parity SRMC.
2. **Fuel-security / local-reliability commitment.** ISO-NE commits specific
   steam units (coal + ST_GAS) for winter energy security beyond their energy
   economics (winter reliability programs; Mystic-style retention agreements).
   The LP runs them only at the temperature-floor commitment plus the few hours
   gas is dear enough.

## Proposed build — two coupled components

### A. Seasonal fuel-inventory budget (quantity constraint → endogenous scarcity rent)

A winter-season (Nov–Mar) oil-burn energy budget over the oil-capable fleet:
oil-primary units **plus the dual-fuel gas units' oil limb** (6,831 MW —
the coverage hole that killed the neiso-40 monthly-F923 probe).

- **Constraint:** one row per plant (or per zone-class group) per season:
  Σ oil-fired MWh ≤ inventory_start + delivery_rate × days. Reuses the
  budget-row machinery already built for neiso-40
  (`dispatch.py` oil-burn budget rows, `fuel.py:load_oil_inventory_budget`) —
  the change is the budget's *derivation and horizon*, not new LP plumbing.
- **Derivation (forward-derivable, rule #13 admissibility):** tank capacity and
  start-of-season fill from EIA-860 fuel-storage fields and ISO-NE fuel-security
  studies (Operational Fuel-Security Analysis / 21st-Century Energy Security),
  replenishment as a delivery-rate cap from the same sources. For a forward year
  this regenerates from tank capacity + logistics and responds to changed
  weather/fleet — unlike the rejected F923 *receipts* (deliveries-to-tank
  outcomes, 1–2 plants reporting).
- **Effect:** when a cold snap draws the budget down, the row's dual adds
  scarcity rent to the *persisted LP prices* (not just the post-solve
  econ_prices overlay), lifting the >$300 tail endogenously; PS/battery
  spread-arbitrage and monthly shape recover *as a consequence*.

### B. Seasonal-reliability commitment (winter fuel-security must-run)

A winter-season commitment floor for the fuel-secure classes (COAL_BIT, ST_GAS
— the units ISO-NE actually retains), grounded in ISO-NE winter-program
design, sized from program/retention terms — **not** tuned to the 0.18/0.24/0.27
TWh residual. Implementation sits *alongside* the existing dual-limb
temperature floor (new season-gated limb driver in `RELIABILITY_FLOOR_REGISTRY`
or a distinct seasonal commitment in `commitment.py`) — the existing limbs'
slope/cap are untouched.

## Explicit non-levers (attestation + diagnosis, verbatim constraints)

- No cranking the reliability-floor slope/cap.
- No offer adders, haircuts, or sigmoids tuned to the price/volume residual.
- No storage-formulation changes (adder/duration/RTE) to move C5b — the PS
  number moves only downstream of tail recovery, or not at all.

## Config & validation plan

- New `ScenarioConfig` flags, default **off**: `neiso_winter_fuel_inventory`
  (component A) and a season-gated floor spec (component B); both cited in
  `docs/parameter-citations.md`.
- Probe first: full-span solve `--year 2023 2024 2025`, one bundle, registered
  on the dashboard in-session (calibration-report skill) whatever the outcome.
- Score: C3c/C5b/C5c must move *endogenously*; keeper decision on structural
  faithfulness, not MAE.
- Data intake needed before coding: EIA-860 fuel-storage fields; ISO-NE
  fuel-security study inventory/delivery figures; winter-program unit lists.
  If a needed quantity is only available as a measured outcome (burn, not
  capacity/logistics), it is inadmissible — stop and re-scope.
