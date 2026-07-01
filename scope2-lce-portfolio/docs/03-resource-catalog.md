# 03 — Resource Catalog

The clean/low-carbon resources available to the LP, their cost basis, and the
knobs that govern them. Numbers live in `data/lcoe/resource_costs.csv`, sourced from
NREL ATB 2024 (generation and Li-ion storage) and DOE Long-Duration Storage Shot /
Hydrogen Program (LDES, hydrogen). This doc explains *what* each resource is and
*how* it enters the model.

## Generation resources (`cost_basis = capex_fixed`)

| resource | role | notes |
|---|---|---|
| `solar_pv` | variable | utility PV; hourly shape from profiles; ATB 2024 utility-scale; capex ~$850–1450/kW |
| `onshore_wind` | variable | land-based wind; shape includes multi-day lulls; ATB 2024; capex ~$1100–1650/kW |
| `offshore_wind` | variable | fixed-bottom offshore; higher CF (~0.45), higher cost; ATB 2024; capex ~$3200–5200/kW; inactive by default |
| `geothermal` | firm | hydrothermal/EGS; flat baseload; ATB 2024 blend; capex ~$4500–6800/kW |
| `nuclear_new` | firm | new SMR/large reactor; ATB 2024 FOAK; capex ~$6000–9000/kW; life 40 yr |
| `nuclear_existing` | firm | procure existing output at going-forward cost (~$25–30/MWh) plus EAC premium (~$4/MWh); capped per ISO (ADR 0008) |
| `hydro_existing` | flexible | existing hydro; going-forward cost (~$22–32/MWh) plus EAC premium (~$3/MWh); monthly energy budget per ISO (ADR 0008); capped per ISO |

Cost basis: overnight capex ($/kW) annualized with CRF = `r(1+r)^n / ((1+r)^n - 1)` where
`r = config.discount_rate` and `n = life_yr` (default life_yr=30 for generation, 40 for nuclear).
This gives `fixed_mwyr` ($/MW-yr), a **pay-for-capacity** treatment where capacity is paid
whether or not it runs, penalizing over-build and curtailment.

## Storage resources

**Fixed-duration Li-ion** (`cost_basis = capex_fixed`):

| resource | duration | rte | role | notes |
|---|---|---|---|---|
| `battery_4h` | 4 h | 0.86 | diurnal shifting | ATB 2024 4h system; capex ~$900–1550/kW (bundled power+energy); life 15 yr |
| `battery_8h` | 8 h | 0.85 | evening ramp / longer shift | ATB 2024 8h system; capex ~$1700–2900/kW; life 15 yr |

Cost is an **all-in annualized $/MW-yr** for power+energy at the listed fixed duration,
annualized with CRF (same as generation).

**Split-storage** (`cost_basis = split_storage` — power and energy chosen independently):

| resource | duration range | rte | role | notes |
|---|---|---|---|---|
| `ldes` | 50–150 h | 0.52 | multi-day lulls | iron-air/flow class; power capex ~$900–1600/kW, energy capex ~$15–55/kWh (very cheap energy) |
| `hydrogen` | 24–500 h | 0.38 | seasonal / very long | salt-cavern/tank storage; power capex ~$1500–3200/kW, energy capex ~$3–18/kWh; enables cheap seasonal buffering |

Split-storage carries separate power ($/kW-yr) and energy ($/kWh-yr) annualized costs;
the LP chooses `build_mw` (power) and `build_energy_mwh` (energy capacity) independently
within per-tech duration bounds. Efficiency is modeled as `η = √rte` split evenly across
charge/discharge; life 25 yr (ADR 0006).

## Per-resource capacity caps

Every resource has a build cap from `data/caps/resource_caps.csv` (per-ISO eligibility
and bounds). Precedence is `PortfolioConfig.resource_caps_mw` > caps table > `cap_max_default_mw`.
Caps reflect the user requirement: e.g. make existing nuclear available but cap it at the
procurable fleet size (~50% of existing fleet per ISO), or bound new solar to an
interconnection/land limit (e.g. ERCOT 60 GW solar potential). Floors (`resource_floors_mw`)
express already-committed or must-take existing PPAs. Per-ISO caps are specified in ADR 0009.

## Selecting active resources

The minimal example runs `solar_pv`, `onshore_wind`, `battery_4h`
(`active_minimal = 1`). Any subset is selectable via
`PortfolioConfig.active_resources`; unset defaults to the `active_minimal` flag.

## Cost sensitivity

`PortfolioConfig.lcoe_sensitivity ∈ {low, mid, high}` picks the cost column:
- **Low:** NREL ATB 2024 Advanced (technology learning / optimistic financing)
- **Mid:** NREL ATB 2024 Moderate (realistic central case)
- **High:** NREL ATB 2024 Conservative (downside / regulatory cost)

Run all three to bound the frontier. The low/mid/high spread reflects NREL's consensus ranges
across experts and technologies, grounded in peer-reviewed cost databases.
