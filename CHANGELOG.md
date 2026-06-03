# Changelog

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
