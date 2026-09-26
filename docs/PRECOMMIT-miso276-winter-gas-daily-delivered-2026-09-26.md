# PRECOMMIT — miso-276: winter-month daily DELIVERED gas (owner ruling D1), armed on the miso-275 keeper

```
LANE    : miso-276 (MISO lever queue §5.4; D1, owner-ruled 2026-09-26)
KEEPER  : 2026-09-26-miso-275-cc-exempt (results/calibration/miso275_span, 2019-2025), legs solved at e5acf0fe
ARM     : keeper recipe + ONE new field: miso_winter_gas_daily_delivered = true
CONTROL : none solved. G-DRIFT e5acf0fe..<pin> (§3); the keeper bundle IS the control (rule 29(b) form 4)
SHARDS  : 7 arm legs, one year each 2019-2025 (rules 34(c), 36), pinned to this document's commit SHA
DATA    : DATA PROFILE: miso — no intake; every series is already on disk (FINDING-miso276 §3)
DOF     : +0. Zero fitted scalars. The hub mapping is the published miso_zonal_gas_hub.csv; the adder is
          the frozen miso-225 per-plant variable transport (already ledgered as a measured input)
```

## 1. The owner rulings

Both were taken in this session on 2026-09-26.

1. **D1, storm-month gas convention:** "Daily delivered price" — the measured daily hub/delivered price through
   Uri, spike days included (taken at the miso-275 sitting, PRECOMMIT-miso275 §7.1).
2. **MidCon source:** "Chicago proxy" (option selected: *"MISO-South on Henry Hub daily; West/Plains on Chicago
   daily as the nearest measured hub (declared rule-14 proxy)"*). No free daily MidCon series exists
   (FINDING-miso276 §3).

## 2. The mechanism

`miso_winter_gas_daily_delivered` (new, default off, byte-identical off, matrix row `winter_gas_daily_delivered`
added in every ISO shard). **Scope:** Dec/Jan/Feb — the replaced overlay's own scope, so no storm threshold is
chosen.

In those months only, every MISO gas row = **its zone's measured daily hub + its plant's measured variable
transport**:
- MISO-South: Henry Hub daily (trade-date placed);
- Chicago-hub zones and West/Plains: Chicago Citygate daily (flow-date placed);
- the adder is the miso-225 frozen-derive intercept, walked down its declared fallback ladder.

Rule 19 (supersede, never stack): on the written cells the old `miso_winter_citygate_daily` shape overlay and the
mean-zero zonal increment are skipped. Dual-fuel oil parity still runs after. Every non-winter cell is
byte-identical (asserted by test and by the §4 footprint).

It is refused together with `miso_gas_marginal_commodity_pricing`, which already reprices every month. The hook
lives in both `resolve_fuel_prices` and the inline `run_calibration.run_year` chain (the path a backcast actually
takes, per miso-224 Addendum A).

## 3. G-DRIFT (rule 29(b)) — keeper legs `e5acf0fe` vs the pin

`git diff e5acf0fe <pin> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference scripts/replay_keeper.py`

### 3a. Audit, every hunk from `main` (the arm's own hunks are the delta in §2)

| hunk group | class | reason |
|---|---|---|
| `scenarios.py` new fields `unit_outage_unit_fuel_routing`, `caiso_intertie_gap_fill_measured_dam`, `cc_eia923_identity_emission_basis`, `unit_outage_netload_mask_repair` | INERT | all default `False`, absent from the keeper recipe; the shard check (`fields new since keeper` must sit at default) enforces it |
| `outages.py` / `arrays.py` / `resolved_inputs.py` unit-fuel routing and net-load-mask companions; ERCOT hour-grain mask | INERT | gated on the two default-off fields; the hour-grain branch is `iso == "ERCOT"` |
| `campd_bins.py` `measured_cc_identity_heat_rates`, `_plant_gas_co2_per_mmbtu` | INERT | gated on `cc_eia923_identity_emission_basis`; only CAISO carries an identity row |
| `eia930/envelopes.py`, `interchange/caiso.py`, CAISO `data/raw/reference` files | INERT | CAISO intertie paths / CAISO artifacts |
| `scripts/lib/outage_detect.py` (`"SPP": "SWPP"`), `bundle_io.py` provenance capture | INERT | an SPP derive-time key; input-capture bookkeeping, not a solve read |
| `scripts/lib/key_provenance.py`, `forecast_parity_registry.py` | INERT | cache-key provenance and forecast bookkeeping |
| `run_calibration.py` `resolve_coal_budget_arms` | INERT | re-expresses the same MISO gates (pooled limb MISO-only, both backcast-only); the MISO keeper arms both limbs, so both are still built |
| `run_calibration.py` + `coal_fuel_inventory.py` `reconcile_floors_to_yard_budget` (neiso-117) | **INERT, measured** | ungated for any ISO arming the yard rows, so it reaches MISO. It scales floors only where a yard's floor draw exceeds its budget. Zero-LP on the keeper fleet, every year: **0 rows scaled** (83 / 75 / 74 / 69 / 57 / 54 / 57 yards, 2019–2025). The shard log must not carry `floors scaled` (S-4) |

**All hunks INERT, so form 4 holds and the keeper bundle is the control.** No control solve is earned.

## 4. Zero-LP footprint on the keeper's fuel array (fleet_only rebuild, flag off vs on)

Cap-weighted gas fuel price $/MMBtu, off → on:
- **Every year 2019–2025:** every non-winter cell and every non-gas row is byte-identical (model 365-day calendar).

**2021:**

| zone | Feb calm days | Feb 13–16 storm | Jan | Dec |
|---|---|---|---|---|
| MISO-West | 13.67 → 5.46 | 19.05 → 66.45 | 3.37 → 3.43 | 4.45 → 4.51 |
| MISO-Plains | 11.86 → 5.75 | 18.22 → 104.90 | 3.17 → 3.54 | 4.91 → 4.62 |
| MISO-Illinois | 1.97 → 8.31 | 37.97 → 99.25 | 3.56 → 6.20 | 4.95 → 7.28 |
| MISO-Indiana | 1.50 → 5.51 | 36.91 → 117.91 | 2.93 → 3.22 | 4.59 → 4.30 |
| MISO-East | 1.23 → 5.30 | 26.85 → 94.26 | 2.98 → 3.12 | 4.21 → 4.21 |
| MISO-South | 20.81 → 5.14 | 32.48 → 111.47 | 3.17 → 2.87 | 5.28 → 3.95 |

- Traded Feb-2021 calm-day levels: Chicago $2.5–4.0, HH $2.6–3.7. The arm lands every zone at hub plus transport.
- **Illinois sits highest** because three Illinois CT peakers carry measured transport of $7.5–12.9 in the frozen,
  ruled table (Venice 913, Goose Creek 55496, Raccoon Creek 55417, all low-burn peaker prints). It is declared and not
  changed (rule 23).
- **Other storm months:** Jan-2022 Plains 35.86 → 5.12 and Illinois 15.02 → 7.95 (the old level smear);
  Dec-2022 (Elliott) every northern zone rises 6.7–8.8 → 9.8–13.0.

Full per-year, per-zone table: `results/calibration/_miso276_winter_gas_footprint.json`
(`scripts/probes/_miso276_winter_gas_footprint.py`).

## 5. Predictions (directions only, fixed before any shard)

1. **Feb-2021 calm days:** Chicago zones rise to the traded level; West/Plains/South fall from their F923 storm
   smear to ~hub + transport. Non-storm February price falls toward actual (model 47.7 vs ~28).
2. **Feb-2021 storm days (13–16):** gas rises in the Chicago-priced zones (the $129.52 print, now reaching West and
   Plains too) and falls in South (HH).
   - **Declared hazard (miso-269 §2):** storm-week price moved 158 → 317 vs 141 actual when only the Chicago zones
     took the print. Expect storm-week price above actual.
   - The owner ruled the spike days in, so this selects nothing.
3. **C3b 2021:** direction not predicted. It is the net of prediction 1 (improves) and prediction 2 (worsens).
4. **Other winters (Jan-2024 Heather, Dec-2022 Elliott, calm winters):** calm winter months move little (the old
   shape factor was ~1 there). Storm months move toward the daily print.
5. **Non-winter months:** byte-identical fuel. Dispatch changes only through storage and hydro coupling across the
   season boundary.

## 6. Decision rule (fixed now)

Recommend promotion iff every structural gate holds:
- **S-1 recipe:** every leg is the keeper plus exactly this one field; pinned inputs; the pinned hydro classifier;
  every miso-275 log marker plus `MISO winter daily delivered gas (` present; the old
  `MISO winter citygate daily (` line **absent** (superseded).
- **S-2 single delta:** fuel moves only in Dec/Jan/Feb gas cells, which the §4 footprint checks at zero LP.
- **S-3 slack:** an arm year with more slack than the keeper is reported with its hours.
- **S-4 drift:** no leg log carries `floors scaled` from the neiso-117 yard reconcile (§3a).

C1–C8 are reported per year, both ways, at full magnitude. Under the owner's standard (*"If it's an improvement
structural or calibration then promote yes"*) this arm is a **structural** repair: it removes gas priced below the
traded commodity (rule 14). A worse C3b 2021 does not retract it (rule 1), and a better one does not validate it.
Promotion is the owner's (rule 31).

## 7. The arm command (per year Y, one shard each)

```
python scripts/replay_keeper.py results/calibration/miso275_span --years <Y> \
  --set miso_winter_gas_daily_delivered=true \
  --out-dir results/calibration/miso276_arm_<Y> \
  --note "miso-276 arm <Y>: winter daily delivered gas (owner rulings D1 + Chicago proxy 2026-09-26)"
```

Shard check: `scripts/probes/_miso276_shard_check.py --leg results/calibration/miso276_arm_<Y> --year <Y> --log <log>`.
