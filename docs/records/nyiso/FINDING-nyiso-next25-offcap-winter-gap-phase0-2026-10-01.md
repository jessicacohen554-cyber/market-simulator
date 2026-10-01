# FINDING — NYISO-NEXT-25 phase 0: the off-cap winter gap is east of Central East, and the daily gas construction compresses ordinary days in spike months

```
LANE      : NYISO-NEXT-25 (orchestrator, rule 32 (a)). Zero LP in this document.
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021 stamped). Unchanged.
PROBES    : scripts/probes/nyisonext25_offcap_winter_gap.py      -> results/phase0/nyiso/_nyisonext25_offcap_winter_gap.json
            scripts/probes/nyisonext25_compression_census.py     -> results/phase0/nyiso/_nyisonext25_compression_census.json
            scripts/probes/nyisonext25_print_level_bracket.py    -> results/phase0/nyiso/_nyisonext25_print_level_bracket.json
MEASURED  : NYISO DA zonal LBMP with loss / congestion components (fetch_nyiso_zonal_lmp.py --kind da, 2021-2025;
            gitignored, regenerable); Transco Z6 NY daily prints (committed); keeper + NEXT-23 sidecars (committed).
```

Population: J/F/D days on which the NYC dual-fuel cap does not bind (NEXT-24's test). NYC, model − DA.

## 1. The NYC off-cap gap is not an NYC gap

Split: NYC gap = Upstate_West gap + (missing Capital − Upstate spread) + (missing NYC − Capital spread).

| $/MWh, off-cap winter days | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| days | 89 | 80 | 89 | 85 | 79 |
| NYC gap, keeper | +0.1 | −8.5 | −0.3 | −5.0 | **−13.2** |
| NYC gap, NEXT-23 arm | +0.8 | −11.3 | −0.8 | −4.6 | **−18.5** |
| Upstate_West level | +13.8 | +17.6 | +6.6 | +1.7 | −0.6 |
| Capital − Upstate spread deficit | −17.9 | −41.1 | −12.6 | −6.2 | **−19.1** |
| NYC − Capital spread deficit | +4.2 | +15.1 | +5.7 | −0.5 | +6.4 |
| DA F − E spread (Capital − Mohawk Valley) | 19.1 | 43.3 | 12.7 | 6.4 | 18.3 |
| of which DA congestion | 17.9 | 41.0 | 12.2 | 6.0 | 17.0 |

- In 2025 Upstate_West is right (−0.6). Every zone east of Central East is under: Capital_Hudson −19.7,
  Lower_Hudson −10.5, NYC −13.2, Long_Island −21.6.
- The missing spread is **Central East congestion** in the measured DA (93–96 % of F − E is congestion).
- Hour bands, 2025: the gap sits in the shoulders (07–10 −19.6, 17–21 −25.4), not overnight (−5.5).

## 2. The narrow question: is the model's winter delivered gas below what DA implies?

On average, no: off-cap MW-weighted NYC gas is within ±$0.7 of Z6 in every year. **By month, yes, and
the cause is structural, not a data level.**

`_nyiso_hub_daily_gas_prices` builds each day as `hub_level × factor`. The factors are the Z6 prints
divided by the **trade-day** mean (the statistic `hub_level` is), then renormalised to a **calendar-day**
mean of 1.0. A Friday or holiday print covers 3–4 flow days. When a spike sits on such a package, the
calendar mean exceeds the trade-day mean, and every ordinary day of the month is scaled by
`c = trade_mean / calendar_mean`.

| winter month | 2022-01 | 2022-02 | 2022-12 | 2024-01 | 2024-12 | 2025-01 | 2025-02 | 2023-02 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `c`, trade-dated (keeper) | 1.02 | 0.97 | 0.93 | **0.82** | 0.98 | **0.78** | 0.91 | 1.14 |
| `c`, flow-dated (NEXT-23 arm) | 0.94 | 0.90 | **0.80** | **0.83** | 0.93 | **0.65** | 0.95 | 1.09 |
| keeper NYC gap, month ($/MWh) | −6.9 | −16.4 | −12.1 | −7.8 | −9.5 | **−32.0** | −12.3 | −4.9 |

- Across the 15 winter months, corr(`c`, NYC gap) = **0.65** trade-dated and **0.84** flow-dated.
- Jan 2025 worked case: ordinary days carry 0.80 × Z6 (1/7: Z6 $15.00, model $11.95; 1/22: $17.54 vs $13.95).
  The MLK package days that absorb the mean are then clipped by the oil cap ($20–27), so the month's mean
  is not even preserved after the cap.
- This is why NEXT-23's flow-date arm **worsened** 2025. Flow-dating spreads the $97.90 print over four
  days, so `c` falls from 0.78 to 0.65.

**Two levels for one commodity.** The NYC / Long Island CT peakers are already **set** to the raw Z6 print
plus LDC transport (`apply_nyiso_downstate_ct_gas_daily`, no renormalisation). The CC and ST_GAS units in
the same zones get `print × c`. Off-cap Jan 2025: CT_PEAKER $11.47 vs CC_REGULAR $5.98.

**Not re-proposing nyiso-248.** nyiso-248 found the daily signal armed and its *shape* not attenuated.
Its comparator was deliberately level-free ("nothing here can be read as a level claim"). This is a level
defect, and it is new evidence.

## 3. The repair and its bracket (zero LP)

`nyiso_gas_daily_print_level` (new, default off, zero parameters): skip the calendar renormalisation in
both branches. A priced day = `hub_level × print / trade_mean`, which for NYC is the Z6 print itself.
- Byte-identical off (unit test).
- Solve surface unchanged: 228 = 228 rows, same hash.
- It is symmetric: Feb 2023 (`c` = 1.14) moves **down**.

Bracket on the keeper (dual-fuel cap on). `lo` = zone CC HR × Δgas; `hi` = price × gas ratio:

| annual avg error vs DA | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| NYC, keeper | +1.6 | −1.6 | +0.7 | −4.1 | −9.1 |
| NYC, bracket lo / hi | +1.6 / +1.6 | −1.3 / −1.2 | +0.1 / −0.4 | −2.5 / −1.5 | **−6.7 / −5.0** |
| Capital_Hudson, keeper → bracket | −6.3 → −6.2 | −14.9 → −14.4 | −8.3 → −9.6 | −4.5 → −1.9 | −11.1 → **−6.5** |
| Upstate_West, keeper → bracket | +39.7 → +39.8 | +37.5 → +38.0 | +22.2 → +21.1 | +3.0 → +5.0…+6.5 | −1.6 → +0.7…+4.0 |

- 2023 winter worsens: NYC −3.3 → −5.7…−7.7 %.
- Upstate_West rises because it takes the same Z6 shape times its zone ratio.
- The bracket is not a solve. The LP decides (PRECOMMIT).

## 4. What it does not close

The Central East congestion deficit (§1) remains. It is ledgered as a model-class limitation (NEXT-20;
re-open only on hourly sub-zonal/PAR injections or published shift factors). The repair moves gas
**levels**; it does not add a CE constraint. Rule 1: no fitted markup or band; the
`offer_curve_by_group` channel is not invoked.
