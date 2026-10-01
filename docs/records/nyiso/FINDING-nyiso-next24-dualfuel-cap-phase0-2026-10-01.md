# FINDING — NYISO-NEXT-24 phase 0: the dual-fuel parity cap is not the 2025 winter C3a lever

```
LANE      : NYISO-NEXT-24 (orchestrator, rule 32 (a))
LP        : none. No shard. No ScenarioConfig field. No code on the solve path. Keeper unchanged.
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021 stamped)
BASIS     : NEXT-23 arm (nyiso_gas_flow_date=true), PR #6984, still held for the owner.
PROBE     : scripts/probes/nyisonext24_dualfuel_cap_footprint.py
            -> results/phase0/nyiso/_nyisonext24_dualfuel_cap_footprint.json, _nyisonext24_mix_scaled_bracket.json
MEASURED  : scripts/data/derive_measured_oil_burn_days.py --iso NYISO (CAMPD, zero parameters; output in
            the session scratchpad and not committed. It re-derives byte-for-byte from the committed CAMPD extracts.)
```

**Method.** A fleet-only rebuild of the keeper recipe with `nyiso_gas_flow_date=true` and
`dual_fuel_switching=false`. That yields the final delivered gas before the cap. A cap-binding
generator-day is a switch-capable gas tranche with gas > oil in any hour, the same test as
`dual_fuel_switch_mask`. Each one is joined to its plant-day measured oil share (an absent day is 0).

## 1. The measured fact holds on the flow-dated series

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| days the cap binds | 2 | 25 | 1 | 8 | 18 |
| MW-wtd measured oil share | 0.08 | 0.37 | 0.38 | 0.16 | 0.32 |
| relief-wtd oil share, MW × (gas − oil) | 0.07 | 0.38 | 0.42 | 0.22 | 0.37 |
| capped MW burning < 1 % oil, relief ≥ $5 | 0.83 | 0.55 | 0.34 | 0.67 | 0.53 |
| MW-days within $1 of parity | 0.00 | 0.07 | 0.00 | 0.03 | 0.02 |

2025 by zone (capped MW burning < 1 % oil): NYC 0.59, Capital_Hudson 0.74, Long_Island 0.33.

- On the flow-dated series this is lower than NEXT-23's 0.73–0.80, which were read off the trade-dated series.
- It is not a near-parity artefact: those days are ≤ 7 % of MW-days.
- **Half or more of the capped MW does not switch when the cap says it would.**

## 2. But the cap is not what under-prices NYC

**(a) Prices on cap-binding days.** NYC days only, NEXT-23 arm daily mean vs DA:

| | 2021 | 2022 | 2023 | 2024 | 2025 | all |
|---|---:|---:|---:|---:|---:|---:|
| NYC binding days | 1 | 10 | 1 | 5 | 11 | 28 |
| DA $/MWh | 89.5 | 201.7 | 161.7 | 134.3 | 195.4 | 181.8 |
| model (arm) | 132.0 | 204.0 | 150.2 | 132.3 | 173.2 | **174.6** |
| model × (measured-mix fuel / cap fuel)¹ | 142.9 | 221.5 | 266.4 | 143.7 | 311.7 | **241.9** |
| \|error\|, arm | 42.5 | 22.7 | 11.5 | 15.2 | 45.8 | **30.8** |
| \|error\|, measured mix¹ | 53.4 | 28.3 | 104.7 | 14.5 | 130.2 | **69.5** |

¹ An upper-bound bracket: it scales the whole day's price by the fuel ratio. It is not a solve.

- On the days the cap binds, the model sits **−$7 (−4 %)** below DA.
- Pricing capped units at their measured mix moves those days to **+33 %** and **doubles** the error.
- The DA-implied fuel, (DA − VOM) / HR, lands below even the cap on the median NYC binding day in every year. That test
  depends on the HR assumed, so it is supporting evidence only. The \|error\| result above does not depend on HR.

**(b) Where the winter gap actually sits.** NYC, model − DA summed over J/F/D, in $·day:

| | cap-binding days | other winter days |
|---|---:|---:|
| 2022 | +23 (n = 10) | −906 (n = 80) |
| 2025 | **−244** (n = 11) | **−1,460** (n = 79) |

In 2025, **86 %** of the NYC winter shortfall is on days the cap does not bind (≈ −$18.5/MWh per day).

**(c) MLK 2025, the extreme case.**
- 1/18–1/19: measured oil share 0.00–0.05 and flow-dated gas at $69.9. Uncapping would price the fleet at $70 gas. DA on
  1/18 was $106; the model is already over DA ($165).
- 1/20–1/21: the plants **did** burn 49–59 % oil, and the model is under DA ($205–221 vs $277–302).

The cap is not the variable that separates those two pairs of days.

## 3. Reading

The parity switch overstates how many units switch. But NYC's clearing prices sit at or below the oil cap, not
above it. So capped units that did not switch were not paying the daily Transco Z6 NY spot. Firm-transport
and contract gas below the spot index is the natural explanation, but it is **not measured here** (F923 delivered
prices are monthly). Both candidate routes in the queue would raise prices on days where the model is already within
−4 % of DA:
- measured-mix pricing, which is symmetric (it uncaps the f = 0 days);
- an oil-burn restriction.

Neither addresses the 86 % of the gap that sits off-cap.

## 4. DECISION CARD (owner)

| | option | cost | what it settles |
|---|---|---|---|
| **A (recommended)** | Close queue item 1 as **not the C3a 2025 lever**. Keep `dual_fuel_switching` K. Leave `dual_fuel_measured_oil_burn` as **U**, carrying this evidence; it was not solved. Re-route the lead to the **off-cap winter gap** (§2b): the 79 non-binding winter days, −$18.5/MWh NYC. | 0 LP | nothing armed |
| B | Solve measured-mix pricing anyway (soco-96 overlay plus explicit f = 0 days), 5 shards. | ~5 shards | confirms §2a with an LP; expected to worsen C3a/C3b |
| C | Build a firm-contract gas representation for non-switching units. | new data intake | requires a measured plant-level contract-gas source. None is on hand, so it is not admissible yet (rule 13/14). |

Rule 1: no fitted markup or band is proposed. The `offer_curve_by_group` channel is not invoked.
