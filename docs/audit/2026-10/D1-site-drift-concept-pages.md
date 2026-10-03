# D1 — Codebase-site concept pages: drift audit (2026-10-03, HEAD d7ff7c2)

Scope: index, mental-model, data-pipeline, fleet-offer-curves, lp-core, solving-pricing, network, capacity-evolution, policy-scarcity, config-reference, js/iso-configs-table.js, js/viz-config-table.js. Checked: region count/list, rule count, P2 posture, bridges, COAL class, evolution order, arm defaults, year spans, warm-start defaults, `module::function` references. Pages not listed under "Changes" carried no drift on those axes.

## Changes

- index.html: stat card "6 ISOs modelled — ERCOT … NEISO" → "9 Regions modelled — … SPP, NWPP, SOCO" (src/market_sim/config/iso_configs.py:2475-2496 `ISO_CONFIGS`).
- config-reference.html (`iso` field): "ERCOT, CAISO, PJM, MISO, NYISO, or NEISO" → nine regions (iso_configs.py:2475-2496).
- config-reference.html (`state_carbon_pricing`): "Only CAISO 2023-2025 is registered" → CAISO/NYISO/NEISO 2023-2025 registered, PJM gated series (src/market_sim/config/scenarios.py:4434-4442; src/market_sim/policy/cap_and_trade.py:136-137, 282-294).
- lp-core.html (Warm-Starting & Cross-Year Basis): "on for the backcast … default-on in the calibration CLIs" → off by default on both paths, rule 36 (src/market_sim/pipeline/solve.py:22, :536; scripts/run_calibration.py:8787-8789 "Owner ruling 2026-09-19 (miso-262): default OFF"; CLAUDE.md rule 36). Closing sentence "forecast years solve cold" → every year solves cold.
- capacity-evolution.html (§1): "The Six Steps … six sequential steps" (1 known retirements, 2 economic, 3 known additions, 4 CCS, 5 entry, 6 backstop) → the 0–7 order (src/market_sim/model/capacity_evolution/__init__.py:6-17; ccs.py:3; adequacy.py:3; CLAUDE.md "Capacity evolution"). Summary cards re-numbered: Steps 0–3 Exits, Steps 4–5 Entry, Step 6 Backstop.

## Verified, no edit needed

- P0→P1 only, P2 archived behind `--enable-legacy-p2`: index.html, mental-model.html, solving-pricing.html, config-reference.html already state it.
- Three P1-native bridges: solving-pricing.html.
- No `COAL` class string on any audited page.
- `reserve_margin_build_enabled` default off: capacity-evolution.html:289.
- Forecast span 2026–2050: index.html stat card.
- `module.py::function` references on the audited pages resolve in src/ or scripts/.
- No "holdout" / "locked test" text on audited pages.

## Found but not resolved

- capacity-evolution.html: the animated flowchart (`#capacity-flow-container`, `#step-explanation`, its JS step data) still renders the old six-step sequence; re-ordering the animation data is a visual rewrite beyond a surgical edit. Prose and summary cards are corrected.
- capacity-evolution.html summary card still says CCS retrofits "target gas-CCs with ≥15yr remaining life" and the reliability floor "× 1.15" — not verified against capacity_evolution/ccs.py and retirements.py within budget.
- src/market_sim/pipeline/solve.py:60 docstring ("the calibration CLIs default ON" for `MARKET_SIM_WARMSTART_XYEAR`) is stale against run_calibration.py:8787-8789 — code docstring, out of this task's scope.
- index.html quotes no module/line counts (nothing to reconcile with 224 files); line totals differ by counting method (`wc -l` sum = 198,108 at HEAD vs the 120,675 figure given to this audit).
- lp-core.html / solving-pricing.html retain measured wallclocks from 2026-07/08 (P0 133–219 s, 5.6× cross-year speedup) — presented as historical measurements with provenance, left as is.
