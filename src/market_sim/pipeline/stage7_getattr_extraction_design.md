# Stage 7 — `getattr(config, …)` → explicit-field extraction (DESIGN ONLY)

Engineering companion to §11 of
`docs/handoffs/orchestrator-unification-plan-2026-07.md`. **Design only — no
behavior change, no solve is run to produce this note.** Stage 7 does not start
until Stage 6 completes (memory-host-blocked on G-40; see the
`STAGE6_GATE_RESULT` marker).

## Why this stage exists (rules 24 & 26)

Every `getattr(config, "field", <literal>)` on the solve path carries a **second
copy of a default** that lives outside `ScenarioConfig`/`constants.py` and never
appears in `run_config.json`. §4 of the plan verified that *today* every gated
flag resolves to a real `ScenarioConfig` field, so the fallback literal is dead
code — **but a dead literal is a re-armable answer key** (rule 26): the moment a
field is renamed, deprecated, or a config is constructed off the
`_calibration_config` path, the `getattr` silently substitutes the shadow
literal and the solve changes with nothing in the run record to show it. Rule 24
("no off-registry tuning channels") wants the field declaration to be the single
source of every default; rule 26 wants deprecated knobs *deleted, not zeroed*.

Stage 7 folds all `getattr(config, …, literal)` reads on the solve path to plain
attribute reads (`config.field`), makes `pipeline/backcast_config.py` the single
typed construction site for the backcast config, and deletes the
`caiso_ra_min_load_frac` `0.40` fallback outright.

## Inventory (measured at this branch)

`grep -rE "getattr\((config|cfg)\s*," src/market_sim/` → **288** reads on the
solve path. Split:

- **~216 boolean gates** — `getattr(config, "flag", False/True/None)`. Field
  always present ⇒ literal is dead. Mechanical fold to `config.flag`; cannot move
  a number.
- **72 non-boolean literal fallbacks** — the answer-key risks. Every one of the
  72 fields **is already declared in `ScenarioConfig`** (verified field-by-field),
  so each fold is byte-identical for a real config. Three sub-buckets:

### Bucket A — always-present context reads (fold, low risk)
Structural fields that are never absent from a real config; the literal is pure
defensive dead code.

| Field | Fallback | Sites |
|-------|----------|-------|
| `iso` | `"ERCOT"` | fleet.py ×7, offer_curves.py ×4 |
| `mode` | `"forecast"` | fleet.py ×10, scarcity.py ×3, runner.py, interchange_config.py |
| `weather_year` | `0` | fleet.py ×5 |
| `outage_source` | `"statistical"` | fleet.py ×3 |
| `carbon_price` | `0.0` | interchange_config.py:812 |
| `carbon_price_path` | `"zero"` | cap_and_trade.py:229 |

### Bucket B — real numeric/string tunables (fold; these are the rule-26 traps)
Each duplicates its field default; a config bypassing `_calibration_config`
would silently pick up the shadow literal.

| Field | Fallback | Site(s) |
|-------|----------|---------|
| **`caiso_ra_min_load_frac`** | **`0.40`** | **pipeline/commitment.py:133 — DELETE (see below)** |
| `ercot_as_adequacy_frac` | `1.0` | pipeline/commitment.py:265 |
| `ercot_as_critical_frac` | `0.0` | reserve_config.py:738 |
| `ercot_as_n_ramp` | `12` | reserve_config.py:739 |
| `ercot_ecrs_requirement_from_year` | `2023` | reserve_config.py:656 |
| `ercot_load_resource_reserve_from_year` | `2023` | reserve_config.py:663/837/1014 |
| `ercot_storage_as_reserve_from_year` | `2025` | reserve_config.py:672/877/1022 |
| `ercot_reserve_supply_cap_from_year` | `2023` | scarcity.py:1308 |
| `ercot_market_design` | `"auto"` | scarcity.py:630 |
| `pjm_reserve_online_rho` | `1.0` | reserve_config.py:1302 |
| `rtcb_reliability_deployment_mw` | `0.0` | scarcity.py:653 |
| `battery_dispatch_adder` | `0.0` | storage.py:135/381 |
| `caiso_solar_deliverability_k` | `0.15` | runner.py:1102 |
| `caiso_solar_deliverability_floor` | `0.50` | runner.py:1103 |
| `caiso_solar_shape_nl_hi_pct` | `30.0` | transmission.py:2077 |
| `caiso_solar_shape_nl_lo_pct` | `10.0` | transmission.py:2078 |
| `renewable_keep_running_value` | `20.0` | transmission.py:2084, commitment.py:125 |
| `st_gas_intermediate_cf_threshold` | `50.0` | offer_curves.py:267 |
| `ct_intermediate_cf_threshold` | `50.0` | offer_curves.py:274 |
| `cc_intermediate_cf_threshold` | `50.0` | offer_curves.py:281 |
| `ct_mustrun_floor_frac` | `1.0` | fleet.py:1056 |
| `ct_deployment_floor_frac` | `1.0` | fleet.py:1074 |
| `reliability_deployment_floor_frac` | `1.0` | fleet.py:1097 |
| `committed_ramp_spread` | `0.0` | fleet.py:6749 |
| `offer_curve_smoothing_n` | `0` | fleet.py:6595 |
| `offer_curve_smoothing_exp` | `1.0` | fleet.py:6596 |
| `nearby_fuel_price_min_state_plants` | `2` | fuel.py:3531 |

### Bucket C — path/string literals (fold)
| Field | Fallback | Site |
|-------|----------|------|
| `campd_bins_path` | `str(CAMPD_BINS_CSV)` | fleet.py:1390 |
| `control_retrofit_path` | `""` | fleet.py:5060 |
| `cc_capacity_reconcile_path` | `""` | fleet.py:5857 |

### Already handled / out of scope
- **NEISO coldsnap coeffs** (`neiso_gas_derate_t0_c/_slope_per_c/_cap`) — the §4
  item-2 getattr literals `-7.0/0.018/0.20` are **gone** as of Stage 6 (§7.3.8):
  now plain `ScenarioConfig` fields with NERC-cited defaults. No Stage-7 work.
- **env-var ERCOT gas knobs** (`ERCOT_ZONAL_GAS`, `ERCOT_GAS_FLOOR`, …) — genuine
  rule-24 off-registry channels but default-off diagnostic probes; a **separate**
  cleanup (fold to fields or delete), not folded here. No keeper enables them.
- `getattr(config, k)` / `getattr(config, field)` **without a literal** (e.g.
  scenarios.py:3904 offset map, capacity.py FOM-field indirection, eac.py:158) —
  dynamic field indirection, not a shadow default; left as-is.

## The `caiso_ra_min_load_frac` deletion (rule 26, explicit)

- Field default: `scenarios.py:896` → `caiso_ra_min_load_frac: float = 0.40`.
- Backcast override: `run_calibration.py:1314` (`_calibration_config`) →
  `caiso_ra_min_load_frac=0.26` — the CAISO keeper's live value.
- Solve-path read: `pipeline/commitment.py:133` →
  `float(getattr(cfg, "caiso_ra_min_load_frac", 0.40))`.

Today the field is always present so `0.26` wins; the `0.40` literal is dead. But
it is a **re-armable answer key**: any future core constructed off the
`_calibration_config` path (exactly what this migration builds) would silently
run `0.40`. **Stage 7 replaces the read with `float(cfg.caiso_ra_min_load_frac)`
and deletes the `0.40` fallback.** The field's own `0.40` default in
`scenarios.py` stays — that is the legitimate, run-config-surfaced registry
default; what dies is the *duplicate* literal buried in the solve path. Deleted,
not zeroed.

## Target module skeleton (`pipeline/backcast_config.py`, `pipeline/overlays.py`)

`_calibration_config` (`run_calibration.py:1021`) moves verbatim to
`pipeline/backcast_config.backcast_config(iso, year, hours, flags, …)` and stays
the **single typed construction site** for the backcast `ScenarioConfig`: every
backcast override (incl. `caiso_ra_min_load_frac=0.26`, `ct_netload_drag` slope/
intercept/cap, etc.) is set there explicitly, so nothing on the solve path relies
on a `getattr` default and `run_config.json` captures the full field set (rule
20/24). `pipeline/overlays.py` holds the measured backcast overlays
(fuel pins, per-year TTC, coldsnap gate wiring) as gates on those explicit
fields — never as code forks (rule 12). `run_calibration_full.py` imports the
config seam from `pipeline` instead of `run_calibration`.

## Byte-identity gate (what Stage 7 must pass)

Stage 7 is **pure code motion** ⇒ the §7.2 exact standard, not the builder-swap
1e-9 tolerance:

1. **Solve byte-identity, all gate-able keepers.**
   `scripts/regression_gate.py --mode byte`, before = a fresh pre-Stage-7 golden
   of the current keepers, after = the Stage-7 branch. Acceptance: objective
   relΔ = 0, **every price Δ = 0, every dispatch Δ = 0** across ERCOT / CAISO /
   NEISO (15 GB box); PJM / MISO on the G-40 ≥24 GB host; NYISO after its
   deliverability-partition recapture. Because every folded field's default
   equals the deleted literal for a real config, and `backcast_config` sets each
   backcast override explicitly, the fold cannot move a number.
2. **The CAISO keeper is the load-bearing leg.** caiso-51 sets
   `caiso_ra_mustoffer=True`, so it actually exercises `commitment.py:133`. Its
   zero-Δ byte gate is the specific proof that deleting the `0.40` fallback moved
   nothing (`0.26` was already winning). A gate that skipped a
   `caiso_ra_mustoffer` keeper would not test the deletion.
3. **Config-construction parity (pre-solve).** For each keeper `meta.json`,
   `backcast_config(...)` must return a `ScenarioConfig` equal **field-for-field**
   to the pre-Stage-7 `_calibration_config` output. This proves the move dropped
   or altered no field before a solve is even run.
4. **Static anti-regression guard (CI).** A test asserting **zero**
   `getattr\((config|cfg),\s*"[^"]+",\s*[^)]*\)` with a non-`k`/`field`
   dynamic-name argument remain on the solve path — so the answer keys cannot
   creep back (rules 24/26 enforced, mirroring §7.2's D-9 overlay-quarantine
   gate). The boolean gates fold in the same sweep and are covered by the same
   grep-gate.
