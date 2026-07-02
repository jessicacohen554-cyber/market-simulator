# 00 — Overview & Problem Framing

## The question

Corporations pursuing **Scope 2** emissions reductions increasingly commit to
**24/7 carbon-free energy (CFE)** — matching their electricity consumption with
clean generation *in every hour*, not just on an annual net basis. This tool
answers the procurement-planning version of that goal:

> Given a facility/company hourly load and the prevailing wholesale prices
> (LMPs), what portfolio of clean & low-carbon resources + storage achieves the
> **highest hourly CFE matching** for a given **cost premium above wholesale**?

We sweep the premium ($1, $2, $5, $7, $10, $20, … any value) and report the
matching % reachable at each, plus the resource mix that gets there.

## Why "premium above wholesale"

The baseline (BAU) cost of serving load is simply buying every MWh at the
wholesale LMP. A clean portfolio changes that cost: it adds capital for clean
resources + storage, avoids some grid purchases, and can sell surplus clean
generation back at wholesale. The **premium** is the net increase per MWh of load:

```
premium ($/MWh) = (portfolio net cost − BAU cost) / total load MWh
```

Framing the objective around premium (not absolute cost) makes results portable
across ISOs and load shapes and directly answers "what does another 9 of
matching cost me?"

## Why the LMP coupling matters

Grid purchases in unmatched hours and surplus sales both settle at the hourly
LMP. So the optimizer intrinsically values matching **expensive** hours (avoided
purchases are worth more there) and building resources whose output correlates
with high-price hours (surplus sells for more). This is the mechanism the user
asked for — "target higher-cost LMP hours to minimize the premium" — and it falls
out of the LP for free, without any special heuristic.

## What's in the portfolio

Clean/low-carbon **generation**: existing & new nuclear (SMR), onshore &
offshore wind, utility solar, geothermal, existing hydro, **gas CC+CCS** (both new and retrofit).
**Storage**: 4 & 8-hour Li-ion (fixed-duration), long-duration LDES (50–150 h, power/energy split),
and hydrogen (24–500 h, power/energy split). Each resource carries a **low/mid/high**
cost and a **capacity cap** the user can set (e.g. "existing nuclear available up to N MW").
Gas CC+CCS counts fully toward hourly matching if it clears the ADR 0012 threshold (capture > 90%,
residual < 50 kg CO₂/MWh), with residual stack emissions tracked separately. Fuel cost reflects
IRA §45Q carbon credits (default 85 $/tCO₂, per-ISO delivered gas prices).

## Relationship to the market simulator

This tool **consumes** the market simulator's BAU hourly LMP output; it does not
recompute the market. It is fully standalone (no `import market_sim`) and never
modifies the core. See `README.md` for the isolation boundary and `PLAN.md` for
the build plan.

## Two modes

- **Mode A — premium-cap (default):** fix a premium budget, maximize hourly
  matching. "How matched can we get for $X?"
- **Mode B — matching-target:** fix a matching goal, minimize the premium.
  "What does 90% (or strict 24/7) cost?"

The math for both is in `01-lp-formulation.md`.
