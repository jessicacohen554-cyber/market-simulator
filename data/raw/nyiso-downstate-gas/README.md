# nyiso-downstate-gas (raw source pointer)

The `nyiso-downstate-gas` curated datatype (daily downstate NYISO delivered-gas
index, **per zone**, for the LM6000 CT peaker fleet) is built from measured series
that live under `data/raw/gas-prices/`. Curated by
`scripts/curate_nyiso_downstate_gas.py` via `scripts/lib/nyiso_downstate_gas.py`.

## Source files (all under `data/raw/gas-prices/`)

| File | Role | Source | Cadence |
|------|------|--------|---------|
| `transco_z6_ny_daily.csv` | pipeline-hub daily spot the peakers buy their commodity at | EIA Natural Gas Weekly Update "New York" spot (NGI Daily GPI); `scripts/fetch_transco_daily_spot.py` | daily (trading days) |
| `henry_hub_daily.csv` | Henry Hub daily spot (provenance component) | EIA DNAV `RNGWHHD`; `scripts/fetch_eia_gas_prices.py` | daily (trading days) |
| `nyiso_downstate_ldc_transport_monthly.csv` | monthly per-LDC non-firm transportation delivery rate (the adder over the hub) | National Grid KEDNY SC-22 / KEDLI SC-19 "Statement of Non-Firm Demand Response Sales and Transportation Rates" (`statnfdr` PDFs); `scripts/fetch_nyiso_downstate_ldc_transport.py`; see `SOURCES_nyiso_downstate_ldc_transport.md` | monthly |

(The v1 statewide `nyiso_downstate_ct_gas_basis_monthly.csv` — EIA `N3050NY3`
citygate − Transco — is retained for the legacy monthly `nyiso_downstate_ct_gas_basis`
adder path but is **superseded** for the daily re-grounding by the per-LDC
transport series below.)

## Construction (schema v2 — per zone)

```
delivered_gas[zone][day] = transco_z6_ny[day] + ldc_transport_adder[zone][month]
```

The interruptible peakers are **transportation** customers: they buy their
commodity at the market hub (Transco Z6 NY **daily** spot, captures cold-snap
blowouts on the exact days they run) and pay their local LDC a **non-firm
transportation delivery charge** to move it from the city gate to the plant. That
delivery rate is the measured "Total Monthly Tier 1 Transportation Service" rate
each downstate LDC publishes every month:

| zone | LDC | service class |
|------|-----|---------------|
| `NYC` | KEDNY (Brooklyn Union Gas) | SC-22 C&G Non-Firm Transportation, Tier 1 |
| `Long_Island` | KEDLI (KeySpan Gas East) | SC-19 Non-Firm Demand Response Transportation, Tier 1 |

Every component is a measured, forward-native market/tariff input that regenerates
for a forward year and responds to changed conditions (the delivery rate steps at
rate cases and carries monthly delivery-rate adjustments) — rule-13 admissible.
Nothing is fitted to a price/volume residual. This supersedes the v1 statewide
firm-citygate premium (the peakers are transport, not firm-sales, customers, and
the LI gas island vs the NYC system carry materially different delivery costs;
CLAUDE.md rules #11/#12/#13, gap register G-13).

Non-trading days in the daily hub series are linearly interpolated onto every
calendar day. The monthly LDC transport adder is broadcast to each day of its
month.

## DATA NEEDED

- Nothing blocking. The source files are committed and cover 2023–2025.
- **Sharpening (optional, not blocking):** a true *daily* downstate city-gate
  commodity index (Transco Z6 NY / Iroquois Z2 from ICE/Platts/NGI) is already
  used for the hub leg; the LDC transport adder is inherently monthly/rate-case
  (a tariff delivery charge), so monthly is the correct native cadence for it.
- Forward years: extend `transco_z6_ny_daily.csv` and
  `nyiso_downstate_ldc_transport_monthly.csv` as new months land
  (`python scripts/fetch_nyiso_downstate_ldc_transport.py`), then re-run
  `python scripts/curate_nyiso_downstate_gas.py`.

## ISO coverage

Only NYISO has a downstate LDC-island non-firm peaker construct. Other ISOs have
no analog (energy-only ERCOT, firm-transport CC fleets elsewhere) and register no
spec — see `scripts/lib/nyiso_downstate_gas.REGISTRY`.
