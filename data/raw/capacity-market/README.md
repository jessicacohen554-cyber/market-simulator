# capacity-market (raw)

Published capacity-market design parameters and outcomes for the five
capacity-market ISOs (PJM, NYISO, ISO-NE, MISO, CAISO), feeding the CR-1
sloped-demand-curve mechanism and CR-3.1 ELCC-accreditation work in
`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §3-4.
ERCOT is excluded throughout (energy-only, no capacity market — its adequacy
revenue is owned by the ORDC/AS-co-opt lane instead, per the plan §3.5).

Three sibling datatypes, each with its own schema and curation script (schema-
first; `data-intake` skill recipe):

| datatype | subdir | schema | curate script | admissibility |
|---|---|---|---|---|
| `capacity-market-demand-curve` | `demand-curve/` | [`capacity-market-demand-curve.schema.yaml`](../../dictionary/schema/capacity-market-demand-curve.schema.yaml) | `scripts/curate_capacity_market_demand_curve.py` | published market-design **input** (rule 13) |
| `capacity-market-auction-price` | `auction-price/` | [`capacity-market-auction-price.schema.yaml`](../../dictionary/schema/capacity-market-auction-price.schema.yaml) | `scripts/curate_capacity_market_auction_price.py` | published **outcome** — validation observable, NEVER a fit target |
| `capacity-market-elcc` | `elcc/` | [`capacity-market-elcc.schema.yaml`](../../dictionary/schema/capacity-market-elcc.schema.yaml) | `scripts/curate_capacity_market_elcc.py` | published market-design **input** (rule 13) |

## Layout

```
data/raw/capacity-market/
  demand-curve/<iso>/<iso>.csv    # net-CONE, IRM, price cap, sloped curve points
  auction-price/<iso>/<iso>.csv   # auction/spot clearing-price history, delivery year <= 2026/27
  elcc/<iso>/<iso>.csv            # ELCC / accreditation ratings, by penetration where published
```

`<iso>` ∈ {pjm, nyiso, isone, miso, caiso}. Each subdir's own `README.md`
carries the authoritative source URLs, per-ISO status, and caveats; the
`DATA NEEDED` line marks anything not yet committed — never guess a value to
fill a gap. See `docs/handoffs/capacity-market-intake-2026-07.md` for the
sources this intake round could not fetch (login-walled, blocked, or simply
not yet located) and needs a manual download for.

## Why three datatypes, not one

`capacity-market-demand-curve` and `capacity-market-elcc` are both
rule-13-admissible **inputs** — published market-design parameters that would
regenerate for a forward year and respond to changed conditions (a new BRA's
planning parameters, a new ELCC filing). `capacity-market-auction-price` is a
published **outcome** — a validation observable the model's implemented
demand-curve mechanism is compared against (CR-2 / T3.1), never pinned to or
fit against (CLAUDE.md rules 1/13). Splitting them keeps that admissibility
distinction visible in the data contract itself, not just in a comment.

## Governance note (rule 22)

`capacity-market-auction-price` restricts intake to delivery years
<= 2026/27 (enforced by `validate_tidy` in
`scripts/lib/capacity_market_auction_price/__init__.py`) — later delivery
years have not cleared yet at the time of this intake round. This is ordinary
published-outcome data, not a backcast/forecast solve, so it carries none of
the holdout-quarantine restrictions in CLAUDE.md rule 22 on its own; the cutoff
exists solely so a later delivery year's real auction outcome can't be
silently absorbed into this file before anyone has decided how it will be
used.
