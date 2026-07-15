# capacity-market-avoidable-cost-rate (raw)

Published default/generic Avoidable Cost Rate (ACR — a going-forward-cost
concept) benchmarks by technology class. See the schema header
(`data/dictionary/schema/capacity-market-avoidable-cost-rate.schema.yaml`) for
the full column contract.

This is the identification source for reconciling the model's FOM-only
going-forward-cost (GFC) construction (`ScenarioConfig.fixed_om_*` /
`retirement_fom_multiplier_*`) against a published bar
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §1.3, RD-4) —
an RC-0B identification question, never a fit target. **No model wiring
happens in this intake pass.**

## Layout

One subdirectory per ISO; each holds a single **unified CSV** named
`<iso>.csv` with exactly the canonical columns:

```
iso,source_type,technology_class,capacity_bin,cost_component,value,unit,vintage,source_doc,source_page
```

`scripts/curate_capacity_market_avoidable_cost_rate.py` reads each subdir and
writes the clean partition
`data/clean/capacity-market-avoidable-cost-rate/<ISO>/…parquet`.

- `source_type` ∈ {pjm_manual18_default, monitoring_analytics_som} — PJM's own
  default ACR table vs. the Independent Market Monitor's separately-published
  benchmark. Both are captured so RC-0B can compare them.
- `cost_component` ∈ {gross_acr, avoidable_capital_recovery, avoidable_fixed_om,
  avoidable_variable_om, net_acr}.
- `technology_class` / `capacity_bin` carry the source's own native label —
  no fixed controlled vocabulary (PJM's own breakdown doesn't map 1:1 onto
  `config/plant_taxonomy.py`'s dispatch fuel classes).
- Leave a value cell blank (drop the row) rather than guess an unpublished
  number.

## Per-ISO status & sources

| ISO | subdir | construct | status |
|-----|--------|-----------|--------|
| PJM | `pjm/` | Manual 18 / Tariff default gross ACR + Monitoring Analytics SOM avoidable-cost tables | see `pjm/README.md` |

Only PJM is in scope for this intake pass (RD-4). The shape is ISO-agnostic —
a future session may add another ISO's analogous published benchmark
additively (e.g. MISO's Module E-1 process), without touching this schema.
