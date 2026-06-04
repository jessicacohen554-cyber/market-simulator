# Changelog

## 2026-06-04 (PJM backcast: per-plant fuel costs, CAMPD outages, capacity payments)

Makes the PJM 2023/2024 backcast bind to real per-plant data instead of the
energy-only stub. Every change defaults off / no-op for ERCOT, whose fleet,
fuel costs and outage overlay are bit-for-bit unchanged (verified: identical
F923 rows, no oil units, both new flags off, full suite green).

- **National EIA-923 fuel-cost table.** `scripts/process_f923_fuel_costs.py`
  now defaults to all balancing authorities (was `--ba ERCO`), so PJM plants
  and the **Petroleum (oil)** fuel group flow through; it also carries each
  plant's `state` and drops anomalous receipts outside a per-fuel plausibility
  band (gas ≤ $200, petroleum ≤ $120, coal ≤ $60 /MMBtu — set above the real
  ~$118/~$59/~$27 maxima in this window so legitimate constrained-winter gas
  survives while order-of-magnitude data-entry errors, e.g. gas at
  $99,241/MMBtu in May, are removed). 98 bad receipts dropped; the 25 ERCOT
  plants' rows are byte-identical.
- **Oil priced from EIA-923.** `data/fuel.py` maps `oil → "Petroleum"`, so
  oil-fired units pay their own measured monthly delivered cost where reported
  (flat `OIL_PRICE_PER_MMBTU` otherwise). ERCOT has no oil dispatch units, so
  this is a no-op there.
- **"Nearby plant" fuel-cost fallback (`nearby_fuel_price_fallback`).** A
  gas/coal/oil plant with no EIA-923 cost of its own for a month is filled —
  before the Henry Hub / coal / oil trajectory — from the quantity-weighted
  average of the other plants that reported: its own state first (≥
  `nearby_fuel_price_min_state_plants`), else its model zone, restricted to the
  ISO's own fleet. Essential for merchant-heavy PJM, where PA/NJ/DE plants file
  almost no Schedule-5 cost. Off for ERCOT (its plants overwhelmingly report).
- **ISO-generic CAMPD historic-outage overlay.** EIA-860 generators now carry
  `plant_code`, `plant_group` and `state` (previously unset for every non-ERCOT
  ISO, which silently disabled both the F923 lookup and the outage overlay).
  `scripts/derive_campd_outages.py --iso PJM` derives
  `inputs/raw-data/campd-outages-PJM.csv` from the CAMPD CEMS state extracts
  (building nameplate/group from the EIA-860 fleet); the overlay reads a
  per-ISO `campd-outages-{ISO}.csv` (ERCOT keeps its legacy file + bin
  intersection, unchanged). The CAMPD loader now also reads unit-level uploads
  from `inputs/raw-data/campd-unit-level/{STATE}_{YEAR}.parquet` (flat dir
  first, so ERCOT/PA/NJ/MD/DE/IL are unchanged even where TX appears in both;
  unit rows are summed to the facility). PJM's full state footprint is listed;
  states whose parquet is not yet uploaded (currently OH, WV, KY, VA, NC, MI)
  skip with a warning and keep statistical availability until added. The PJM
  outage extract presently covers PA/NJ/MD/DE/IL/IN/DC (70 plants).
- **Note:** the EIA-923 *fuel-cost* parquet is regenerated national (the
  feature's input); the *generation* parquet is kept at its prior ERCOT scope
  (it only feeds hydro/offline reference-building, not PJM dispatch) — rebuild
  it national with `process_f923_fuel_costs.py --ba ""` when needed.
- **Per-plant calibration fleet (`plant_level_fleet`).** Non-ERCOT calibration
  runs the EIA-860 fleet at full per-plant granularity (no efficiency-bin
  aggregation) so plant identity reaches dispatch — required for the per-plant
  fuel cost and outage overlay to bind. Off by default (forward runs keep the
  faster aggregated fleet); ERCOT is unaffected (it builds from CAMPD bins).
- **Module M1: capacity-payment revenue.** `capacity.py` adds a per-ISO
  resource-adequacy payment (net-CONE × UCAP, gated on `MARKET_DESIGN`) to the
  thermal retirement and new-entry economics, so PJM/NYISO/ISO-NE/CAISO units
  are no longer over-retired on energy margin alone. Zero for energy-only ERCOT.
- **Effect on the PJM 2024 backcast:** outage overlay zeroes 233 coal/CC
  tranches (64 plants); 241 generators price from their own EIA-923 cost and
  1,119 gap-fill from nearby plants; modeled coal falls 149.4 → 140.5 TWh
  toward the ~122/116 actuals. The per-plant solve is slower (minutes, larger
  LP) — acceptable for a backcast.

## 2026-06-04 (storage daily-cycling toggle)

- **Added the `storage_daily_cycling` foresight toggle.** A new LP constraint
  family (`dispatch._build_storage_daily_cycle_rows`) optionally pins each
  storage unit's SOC back to its day-start level every 24 h, so storage cannot
  arbitrage across days — bounding the single-LP perfect-foresight advantage to
  within-day spreads (the realistic limit for short-duration storage). Off by
  default (annual-cyclic, unchanged). Exposed as `ScenarioConfig.storage_daily_cycling`
  and `run_calibration_full.py --storage-daily-cycling`; recorded in each run's
  `meta.json`/`run_config.json`. Covered by `TestStorageDailyCycling`.

## 2026-06-03 (storage backcast RTE fix + perfect-foresight docs)

- **Fixed: storage RTE override now reaches the backcast.** `load_eia860_storage`
  hard-coded round-trip efficiency from the `STORAGE_TECHS["li_ion_4hr"]`
  constant (0.86), so a calibration sweep of `config.storage_rte_4hr` (e.g. the
  0.85 in the run configs) never changed the backcast battery fleet — the lever
  was silently decoupled from the model. It now reads RTE through `_storage_rte`,
  matching the forward new-entry path; the function takes `config` and the
  calibration call site passes it. Magnitude is small (√0.86→√0.85) but the
  knob now actually binds.
- **Documented the storage perfect-foresight assumption.** The full 8760-hour
  horizon is solved as one LP, so storage is co-optimized against the whole
  year's prices (an upper bound on realized arbitrage that over-flattens net
  load). Added the limitation and the standard mitigations (daily SOC cycling
  caps, rolling/receding horizon, day-ahead+real-time, price-taker pass,
  stochastic, empirical haircut) to `model-methodology-spec.md` §storage and a
  note in `dispatch.build_constraints`. Bounded for the short-duration 2023
  fleet by the `SOC ≤ energy_cap` constraint; grows with long-duration storage.

## 2026-06-03 (storage + offer-curve docs)

- Documented the storage new-entry overhaul (PR #180): the value stack
  (duration-sized arbitrage net of cycling degradation **+** resource-adequacy
  capacity value via the per-ISO `MARKET_DESIGN` registry, net-CONE × ELCC ×
  saturation derate), tech-diversified build budget, and per-tech learning
  curves. Methodology spec §5.5 was updated in that PR; this pass aligns
  `claude.md`, the multi-ISO market-design catalogue (`MARKET_DESIGN` registry
  note), and `docs/binning-methodology.md` (smooth N-slice offer curve now
  spanning CC/coal/CT/ST, exponent p=3 — runs 25–26).
- **Parameter-citation registry back-filled — CI green.** Added
  `scripts/generate_parameter_registry.py`, which reuses the validator's exact
  `expected_param_ids()` derivation, preserves the 133 curated entries, and
  registers the 401 missing parameters with values plus citations harvested
  from each constant's inline comment. `validate_parameters.py` now exits 0.
  534 entries total; 232 auto-entries are flagged `needs-citation` (no dated
  primary source in the comment) for later human review. The human view
  `docs/parameter-citations.md` is now rendered from the registry by the same
  generator, so the two stay consistent — re-run after adding constants.

## 2026-06-03

- **Documentation reconciliation.** Realigned the prose docs with the as-built
  code after the code had outpaced them. Methodology spec, `claude.md`, the
  calibration logs and the multi-ISO baseline now reflect: the opt-in
  three-solve unit-commitment layer (still pure LP, no MIP), CAMPD per-plant
  binning with tranche-based rising offer curves (ERCOT default), config-driven
  retirement plus the CCS-retrofit pathway, forecast-vs-backcast outage
  modelling, hydro monthly energy budgets, EAC/REC attribute credits, and the
  seven registered ISO topologies (ERCOT, CAISO, PJM, MISO, SPP, NYISO, NEISO).
- Added the `/sync-docs` skill — a manually-invoked, end-of-session doc
  reconciler (deliberately not a hook) with a code→doc map.
- Roadmap noted: derive forecast-mode spring/autumn maintenance shaping from
  historic outage data (replacing the flat shoulder-POF heuristic).
- Documented the per-plant tranche-config system added across the run5–run24
  calibration series (`inputs/plant-tranche-config.csv`,
  `plant_tranche_config_path`, `cc_peaking_per_plant`,
  `fleet.load_plant_tranche_config`/`plant_tranche_bands`): an optional
  per-plant **five-slice rising offer curve** (Econ split into Low/High) that
  overrides the per-group tranche defaults for flagship-plant calibration.
  See `docs/binning-methodology.md` and methodology spec §3.3.

## 2026-05-16

- Phase 0 started.
