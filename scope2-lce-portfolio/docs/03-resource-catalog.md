# 03 — Resource Catalog

The clean/low-carbon resources available to the LP, their cost basis, and the
knobs that govern them. Seed numbers live in `data/lcoe/resource_costs.csv` and
are **ATB-ballpark placeholders** pending PS-01 (generation pricing) and PS-03
(storage costing). This doc explains *what* each resource is and *how* it enters
the model; it is not the final cost source.

## Generation resources (`cost_basis = lcoe_mwh`)

| resource | role | notes / open questions |
|---|---|---|
| `solar_pv` | variable | utility PV; hourly shape from profiles |
| `onshore_wind` | variable | shape includes multi-day lulls |
| `offshore_wind` | variable | higher CF, higher cost; off in minimal set |
| `geothermal` | firm | flat baseload clean |
| `nuclear_new` | firm | new build / SMR; wide cost band |
| `nuclear_existing` | firm | procure existing output at going-forward cost; **capped** (PS-05) |
| `hydro_existing` | flexible | monthly energy budget to be added; existing only |

LCOE → annualized fixed cost via `fixed_mwyr = lcoe · cf_assumed · 8760`. This is
a **pay-for-capacity** treatment (capacity is paid whether or not it runs, so
over-building to dump surplus is penalized). A PPA-style pay-per-MWh alternative
is on the table in PS-01.

## Storage resources (`cost_basis = fixed_mwyr`)

| resource | duration | rte | role |
|---|---|---|---|
| `battery_4h` | 4 h | 0.86 | diurnal shifting |
| `battery_8h` | 8 h | 0.85 | evening ramp / longer shift |
| `battery_12h` | 12 h | 0.84 | overnight bridging |
| `ldes_100h` | 100 h | 0.55 | multi-day lulls; cheap energy, low RTE |
| `hydrogen` | 200 h | 0.35 | seasonal / very long; low RTE |

Storage cost is an **all-in annualized $/MW-yr** for power+energy at the listed
duration. The power/energy capital split, degradation, and cycling adder are
PS-03 decisions; the current single-number-per-tech form is a simplification.

## Per-resource capacity caps

Every resource has a build cap (`cap_max_default_mw` in the table, overridable per
run via `PortfolioConfig.resource_caps_mw`). This is the user requirement: e.g.
make existing nuclear available but cap it at the procurable fleet size, or bound
new solar to an interconnection/land limit. Floors (`resource_floors_mw`) express
already-committed capacity. Regional resource-potential ceilings are PS-06.

## Selecting active resources

The minimal example runs `solar_pv`, `onshore_wind`, `battery_4h`
(`active_minimal = 1`). Any subset is selectable via
`PortfolioConfig.active_resources`; unset defaults to the `active_minimal` flag.

## Cost sensitivity

`PortfolioConfig.lcoe_sensitivity ∈ {low, mid, high}` picks the cost column. Run
all three to bound the frontier. The low/mid/high spread is itself a modeling
statement (technology-learning and financing assumptions) — document the chosen
source in PS-01/PS-03.
