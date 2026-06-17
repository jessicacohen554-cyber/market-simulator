# Reference-price interface — step (1) validation (PJM)

**Status:** pre-LP. The neighbor-price module is built, tested, and validated
against measured data; it is **not yet wired into the dispatch LP**. This note
records what the validation showed so the step-(2) wiring is informed by it.

## What was built

A forecast-grade, ISO-agnostic neighbor reference price
(`src/market_sim/data/neighbor_price.py`), parameterized per ISO by the
`INTERFACE_NEIGHBORS` registry in `config/constants.py`. For each neighbor:

    neighbor_price[h] = (henry_hub[year] + gas_basis) × marginal_heat_rate
                        × load_shape(neighbor_load[h])

Every term is a forecast input (Henry Hub trajectory, neighbor gas basis,
neighbor EIA-930 load) or a physically-pinned structural constant (marginal
heat rate ~7.5, hurdle $3/MWh, interface limit). **Nothing is tuned to the
net-interchange target** — so reproducing the measured net export *without being
told to* is a genuine validation, not a fit.

Neighbors resolve individually where their EIA-930 load extract exists and fall
back per-neighbor to a proxy BA otherwise. PJM today: **MISO** (own extract),
**NYISO** (own extract), **Carolinas** (no `DUK` extract yet → priced on the
`SOCO` load shape). Drop in a `DUK hourly.parquet` and the Carolinas seam lights
up on its own data with no code change.

## What the validation showed (`scripts/validate_neighbor_price.py`)

Run against PJM 2023/24/25, with no LP, on three measured benchmarks:

| benchmark | result |
|---|---|
| **Neighbor price *shape*** (vs actual NYISO LMP) | tracks: hourly corr +0.39 / +0.40 / +0.49 |
| **Neighbor price *level*** (vs actual NYISO LMP) | understates: $23 vs $30, $21 vs $36, $26 vs $61 — gap widens in tight years |
| **Seam direction** (spread sign vs measured net export) | **wrong sign**: predicts PJM imports; PJM exports in 95–98% of hours; hit-rate 2–11% |

### The headline finding

**PJM's structural net export is not a gas-price-spread phenomenon, and a shared
marginal heat rate across regions cannot reproduce it.** On a like-for-like
gas-marginal basis PJM's reference price ($24 / $21 / $27) is *higher* than its
neighbors' ($20 / $17 / $22), because PJM's Marcellus-delivered gas basis
(+$0.67) exceeds MISO's and the Carolinas' (~$0). So the pure gas-basis spread
says PJM should *import* — the exact opposite of the +40 → +18 TWh it actually
exports. PJM exports because its **fleet** (abundant nuclear, coal, and
efficient CCs) sets a clearing price below its neighbors' despite pricier gas;
assigning every region the same 7.5 heat rate erases exactly that
fleet-efficiency difference.

There is a weak positive hour-to-hour signal in the spread (corr +0.15…+0.26 in
2023/24, ~0 in 2025), so the *shape* mechanism (load-driven price) is sound; the
**level/sign** is what fails.

### Implication for step (2) — do NOT fit it away

The physically faithful lever is a **per-region marginal heat rate** (and
possibly supply-curve convexity, `load_shape_exponent` > 1) reflecting each
fleet's marginal efficiency — PJM lower, its neighbors higher — pinned to fleet
data (EIA-860/930 marginal-unit mix), **never to the net-MWh target**. That
keeps the construction forecast-native. The level gap vs actual NYISO LMP also
reflects congestion/scarcity premia outside a gas×HR proxy (NYISO downstate is
an extreme case and a poor heat-rate anchor); MISO and the Southeast are the
better-behaved gas-marginal references to calibrate the per-region heat rate
against.

This is consistent with the prior fitted `EXPORT_TRANCHES`, which only
reproduced PJM's export by pricing the export sinks at the *neighbors' avoided
cost* ($16–36/MWh) — i.e. the neighbors' marginal price, which the flat-HR
reference price undershoots.

## Files

- `src/market_sim/data/neighbor_price.py` — the module (pure, no LP).
- `src/market_sim/config/constants.py` — `NeighborInterface`, `INTERFACE_NEIGHBORS`.
- `scripts/validate_neighbor_price.py` — the validation report.
- `tests/test_neighbor_price.py` — 15 unit + integration tests.
