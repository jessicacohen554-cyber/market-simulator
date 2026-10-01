# FINDING — NYISO-NEXT-15 phase 0: the pooled import node lands imports on the wrong side of Central East (ZERO LP)

- **Session:** NYISO-NEXT-15, the orchestrator. No LP, no shard.
- **Keeper read:** `2026-09-30-nyisonext14-total-east-span` + stamped 2021. Its P1 network/system sidecars were read from the NEXT-14 leg commits (provenance SHAs: `docs/records/nyiso/RESULT-nyiso-next14-total-east-cutset-2026-09-30.md` §3).
- **Probe:** `scripts/probes/nyisonext15_landing_phase0.py` → `results/phase0/nyiso/_nyisonext15_phase0.json`.
- **Question (queue item 1):** why does the Total-East link bind in the wrong hours, with a $2–8 spread where the market shows $20–56?

## 1. The market's Central East binds when Total East flow is high, and the model's link carries too little then

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| market CE-binding share of h | 19.2 % | 10.0 % | 4.4 % | 2.5 % | 3.6 % |
| measured TOTAL EAST, binding h / other h (MW) | 4,197 / 3,553 | 4,556 / 3,017 | 3,777 / 2,970 | 5,212 / 3,166 | 5,039 / 3,058 |
| model link flow, binding h / other h (MW) | 3,719 / 3,086 | 3,479 / 2,745 | 3,059 / 2,446 | 3,557 / 2,488 | 3,674 / 2,575 |
| model link / its limit in binding h | 0.78 | 0.70 | 0.72 | 0.67 | 0.69 |
| CE on TE slope (corr) | 0.54 (0.88) | 0.46 (0.91) | 0.34 (0.80) | 0.51 (0.91) | 0.53 (0.94) |

- CE carries a near-fixed fraction of Total East and binds when Total East is high. The posted CE limit is not the driver: binding is *less* likely when the limit is low.
- In those hours the model's link runs 0.5–1.6 GW below measured Total East, at 67–78 % of its own limit. **No cap construction can make it bind there;** the flow is missing.

## 2. Where the flow goes: the pooled node is zone-blind

Annual mean MW, pooled `NYISO_external` border links vs each link's measured P-32 attributed schedule (PAR split, NE AC row on its own node):

| model − measured | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| Capital_Hudson | +188 | +211 | +139 | +108 | +35 |
| NYC | +219 | +187 | +246 | +150 | +153 |
| Long_Island | +117 | +118 | +113 | +138 | +115 |
| **Upstate_West** | **−373** | **−320** | **−308** | **−375** | **−264** |

- The monthly EIA-930 band pins only the pooled node's **total**. The LP lands that volume where the zonal price is highest: the three downstate links sit at their p90 envelopes in 96–99 % of hours.
- Result: 400–560 MW of import arrives **east of the Central-East cutset** that really arrives west of it. Upstate is short by the same amount, so less has to cross the cutset, and the link's flow and congestion rent fall.
- In the market's binding hours the upstate import gap is 480–750 MW (2022, 2024), about half the link's shortfall. The rest is generation and load (not examined here).

## 3. Construction and feasibility

- **Approved by the owner (decision card 1):** band each pooled border link monthly on its own measured schedule; replace the pooled band (rule 19); keep ±2 %.
- **The EIA-930-share split is infeasible.** EIA-930 and the P-32 sum differ by up to 15 % in a month. Scaling Long_Island's share by the EIA-930 total overshoots the sum of its own hourly caps by 44 GWh (2022) and 86 GWh (2023).
- **P-32 per link is feasible in every month of every year.** The band and the p90 envelope share one source. The smallest upper headroom is 1.9 GWh (Long_Island, 2025). Owner decision card 2: "P-32 per link".
- **Cost, stated:** the pooled annual total moves from EIA-930 to the P-32 sum: 33.06 → 32.39, 31.82 → 30.49, 27.93 → 26.77, 26.19 → 26.51, 24.84 → 25.00 TWh (2021–2025). Declared as a rule-14 alignment.

## 4. What this does not address

- The other half of the binding-hour link shortfall (upstate generation and load) is not examined here.
- The CENTRAL EAST sub-cutset inside TOTAL EAST is still one zonal link capped at a TOTAL EAST level.
