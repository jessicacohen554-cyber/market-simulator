# HANDOFF — BASIS-1: all-ISO benchmark-basis measurement (who owns the combined EIA-930 fossil gap)

```
SESSION BASIS-1 — cross-ISO benchmark lane (owner card "Status quo + route", SCORER-COAL-1, 2026-09-29)
DATA PROFILE: shared  (widen per ISO for campd-unit-level; ISOs in scope: NWPP, SPP, MISO first, then every ISO)
MODEL: Opus or Fable
CLAUDE.md is binding. Pay particular attention to rules 1, 14, 19, 23. This lane runs NO LP solve and lands NO scorer change.

DIRECTIONS (owner, standing)
- Present every decision for the owner as clickable decision cards (AskUserQuestion), NEVER as inline text.
- When done: create a PR, rebase, and merge it. Archive any sessions you launched. Say which branches can be deleted.

WHY
- render_calibration_html.reconcile_vintage_classes scales every fossil class by one factor k when EIA-923
  gas+coal(+oil) is outside ±3 % of EIA-930. SCORER-COAL-1 measured every keeper
  (docs/handoffs/RESULT-scorer-coal1-reconcile-options-2026-09-29.md) and found that the gap sits on a
  DIFFERENT fuel in different ISOs:
  - NWPP 2019–24: on gas (−10 to −12 TWh/yr);
  - SPP 2023–25: on coal, because 930 books coal near CEMS gross (SPP-87);
  - MISO 2019: in 930's coal cell, which is known to be unreliable.
  So neither "coal at 923" nor "coal at CEMS×k" is right ISO-agnostically. The owner kept the status quo
  pending this measurement.

WHAT TO MEASURE (zero LP; committed bench parts + CAMPD unit-level + EIA-923/930 loaders)
For every ISO and every year 2019–2025:
1. Coal basis: EIA-930 coal against CEMS gross and against EIA-923 net, using the hourly OLS slope and
   intercept (the SPP-87 method, scripts/probes/_spp87_benchmark_reconcile.py). Result: which basis each
   BA books coal on.
2. Gas coverage: EIA-923 gas against EIA-930 gas against CEMS gross for non-CHP gas (the SPP-88 method).
   Flag coverage breaks such as SPP's 2024 "Gas Self" step.
3. For each year the reconcile fires (17 ISO-years, table §1 of the RESULT): split the combined gap into
   coal-basis, gas-coverage and residual, each with its source.
Then design an ISO-agnostic attribution rule that reads only MEASURED per-family basis evidence, and
state it BEFORE re-scoring (rule 1). Re-score every keeper with scripts/probes/_scorercoal1_reconcile_options.py
extended by the new option, and put the choice to the owner as a decision card.

NOT IN SCOPE
- Any solve, promotion, or change to the model's coal output basis. The model-side question (SPP model
  coal on gross) belongs to the ISO lanes.
- NWPP plant-basis demand (derive_nwpp_plant_basis_energy.py reads classFull by family). Flag any move,
  and argue it as a data change under rule 23; do not re-derive it here.
```
