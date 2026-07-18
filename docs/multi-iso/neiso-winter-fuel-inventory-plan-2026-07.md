# NEISO winter fuel-inventory / seasonal-reliability build — scoping proposal (2026-07)

**Status: both components have landed and been probed — negative result, not a
keeper.** Component A (the oil seasonal-budget LP rows, `winter_fuel_inventory.py`
+ `dispatch.py:_build_oil_budget_rows`) landed GATED `neiso_winter_fuel_inventory`
(default off) — the 2026-07-04 probe (`neiso-inventorycap-inert-probe`) found the
inventory cap inert (oil still under-ran). Component B (winter fuel-security
must-run, `winter_fuel_inventory.py:apply_winter_fuelsec_mustrun`, GATED
`neiso_winter_fuel_mustrun`, default off, wired into `scripts/run_calibration.py`)
has since also landed and been probed together with Component A (2026-07-06,
dashboard runs `neiso-wfuelsec-ab-v2` / `neiso-wfuelsec-ab-v2off`): A+B alone
do NOT close the C1/C3c/C5b caveats — the small NEISO coal/steam fleet already
runs above min-stable on cold days economically, so the commitment floor is
non-binding. **Update (2026-07-07, G-24):** a third, complementary mechanism —
the gas cold-snap availability derate (`neiso_gas_coldsnap_derate` →
`transmission.inject_neiso_gas_coldsnap_derate`) — was identified and solved
full-span alongside A+B (`2026-07-07-neiso53-winter-fuelsec-coldsnap`, bundle
`neiso53_winter_coldsnap_ab`, against ablation twin
`2026-07-07-neiso53-winter-fuelsec-ablation`). Result: still **DORMANT** on
every *scored* metric (C3c/C5b unmoved vs the twin — see
`docs/calibration-log.md` 2026-07-07 entry for the twin-vs-probe table), so
this REFUTES the "one missing fuel-security mechanism" hypothesis outright;
the residual is now attributed to a NEISO winter capacity-adequacy /
scarcity-price-formation gap, not a fuel-security-mechanism gap. Per rule 1
the owner nonetheless **adopted the full stack into the keeper** (all three
mechanisms are real, forward-derivable ISO-NE winter structure) —
`2026-07-07-neiso53-winter-fuelsec-coldsnap` is the current NEISO keeper
(`frontend/data/backcast/keepers.json`), not neiso-48. This was the scope for
the (now-completed) NEISO model experiment described below. It was the *only*
sanctioned lever for the remaining NEISO model-miss family, per the
neiso-41/43 attestation ("Closable only via the documented future build
(fuel-inventory / seasonal-reliability constraint), NEVER by cranking the
floor slope/cap or by an offer adder") and
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

**Landed** (`winter_fuel_inventory.py:apply_winter_fuelsec_mustrun`, GATED
`neiso_winter_fuel_mustrun`, default off; probed 2026-07-06 — see Status above).

A winter-season commitment floor for the fuel-secure classes (COAL_BIT, ST_GAS
— the units ISO-NE actually retains), grounded in ISO-NE winter-program
design, sized from program/retention terms — **not** tuned to the 0.18/0.24/0.27
TWh residual. Implementation sits *alongside* the existing dual-limb
temperature floor as a distinct seasonal commitment invoked from
`scripts/run_calibration.py` (not `commitment.py`, and not a new
`RELIABILITY_FLOOR_REGISTRY` limb spec as originally scoped) — the existing
limbs' slope/cap are untouched.

## Explicit non-levers (attestation + diagnosis, verbatim constraints)

- No cranking the reliability-floor slope/cap.
- No offer adders, haircuts, or sigmoids tuned to the price/volume residual.
- No storage-formulation changes (adder/duration/RTE) to move C5b — the PS
  number moves only downstream of tail recovery, or not at all.

## Config & validation plan

- `ScenarioConfig` flags **landed**, default **off**: `neiso_winter_fuel_inventory`
  + `neiso_winter_fuel_start_fill_bbl` (component A, cited in
  `docs/parameter-citations.md`) and `neiso_winter_fuel_mustrun` +
  `neiso_winter_fuelsec_min_stable_pct` / `_commit_frac` / `_tmin_c` (component
  B, landed in `config/scenarios.py` but **not yet cited** in
  `docs/parameter-citations.md` — outstanding).
- Probe **done**: full-span solve `--year 2023 2024 2025`, registered on the
  dashboard in-session (calibration-report skill) — component A alone
  (`2026-07-04-neiso-inventorycap-inert-probe`, inert), A+B together
  (`2026-07-06-neiso-wfuelsec-ab-v2` / `-v2off`, negative), and the full A+B+
  cold-snap-derate stack (`2026-07-07-neiso53-winter-fuelsec-coldsnap` /
  `-ablation`, still DORMANT on scored metrics). **Keeper is now
  `2026-07-07-neiso53-winter-fuelsec-coldsnap`** — adopted per rule 1 despite
  the negative result (see Status update above).
- Score: C3c/C5b/C5c were required to move *endogenously* for a keeper
  decision on structural faithfulness (not MAE); scored 2026-07-06 and none of
  the three moved — see Status above.
- Data intake **done**: `data/raw/winter-fuel-inventory/isone/isone.csv` (OFSA
  + Winter Reliability Program figures, hand-curated/cited) plus EIA-860
  derived fields, curated via `scripts/data/curate_winter_fuel_inventory.py` into
  the `winter-fuel-inventory` clean datatype
  (`data/dictionary/schema/winter-fuel-inventory.schema.yaml`). No measured
  burn/receipt outcome was intaken (the F923-receipts approach stayed
  rejected).
