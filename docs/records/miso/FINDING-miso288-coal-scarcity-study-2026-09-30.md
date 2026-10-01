# FINDING — miso-288: the real 2022 MISO fleet priced its coal shortage as an offer adder on part of the fleet. The yard-only candidate is killed by its pre-check. No solve.

```
LANE     : miso-288 (owner ruling "2022 coal-scarcity study", miso-287 §6)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP       : none
PRECOMMIT: docs/PRECOMMIT-miso288-yard-only-precheck-2026-09-30.md (c4ffbefa, pushed before the pre-check probe existed)
PROBES   : scripts/probes/_miso288_coal_scarcity.py  (phase 0: EIA-923 stocks/receipts, CAMPD hourly, hub, keeper)
           scripts/probes/_miso288_yard_precheck.py  (INC vs YARD dual emulation)
OUTPUTS  : results/calibration/_miso288_{coal_scarcity,yard_precheck}.json
SOURCE   : Potomac Economics, 2022 State of the Market Report for the MISO Electricity Markets (June 2023),
           §IV.H (pp.51-52, Figure 26) and §VI.B (p.99). Fetched from potomaceconomics.com; not committed
           (a citation, not a model input).
CELLS    : coal_fuel_inventory K (note), coal_fuel_inventory_plant_grain K (note); no verdict moves
```

## 1. Answer

The real fleet expressed 2022 coal scarcity as an **opportunity-cost offer adder**. The IMM says units put their
conservation plans into their reference levels. That is the same thing the LP's fuel-budget dual does, so the
**form** of the keeper's mechanism is realistic. Two things differ:

| | real 2022 fleet | keeper |
|---|---|---|
| who carries the adder | ~11–22 GW of ~47 GW coal Jan–Sep (IMM Fig. 26), ~25–45 % | pooled monthly rows on all rowed coal, plus 50 of 69 yards binding (43.8 of 53.3 GW) |
| monthly burn shape | seasonal: Apr 8.6, Jul 14.4, Aug 13.3, Oct 8.4 Mt; pile drawn Jun–Aug to 63 days, rebuilt Sep–Nov | flat 20.2–20.9 TWh May–Sep (the `B/12` cap), over the bench in May and Sep–Nov |
| derates / dark units | no signature (ceiling ratio 0.91–0.94, dark units in line with 2021/2023) | n/a |
| summer night/day coal ratio | Jul 0.75, Aug 0.72 | Jul 0.71, Aug 0.72 |

So the keeper is not pulling coal off nights **disproportionately**. It is short of summer coal in all hours
(Jul, gross GW night/day: real 29.3/39.0, keeper 22.6/31.9) and prices a fleet-wide rent the real market carried
on under half the fleet.

## 2. Phase 0 (measured, `_miso288_coal_scarcity.json`)

- **Stocks.** MISO-BA coal stock, January: 2021 37.4 Mt, **2022 24.2 Mt**, 2023 27.3 Mt. 2022 minimum days on
  hand: 63 (Aug). 2021: 58. The pile was never run down in any year.
- **Burn timing.** Summer burn exceeds shoulder burn in every year 2019–2024, and stocks absorb the swing.
  Annual burn 2022: 130.2 Mt, receipts 130.8 Mt.
- **Hub vs keeper night medians, 2022:** Jun 51.2/59.3, Jul 52.9/65.2, Aug 62.0/68.4, Oct 36.5/44.7, Nov 32.3/41.6.
  The night overshoot is in the shoulder months as well as summer.
- **IMM.** Conservation began fall 2021. It fell 40 % by end of Q1 2022, rose through September, and eased after
  September as rail deliveries recovered. The system price-cost mark-up was −0.5 % in 2022, partly because the
  conservation adders sat in the references.

## 3. The pre-check (pre-registered, c4ffbefa)

Candidate **YARD**: keep the per-yard annual rows, set `coal_fuel_inventory=false` (pooled monthly limb off). This
is a config flip that the resolver already allows. Emulator: the rebuilt P1 bid stack at the keeper quantity, with
a λ×HR adder per binding row, λ found by projected subgradient (200 iterations, residual row violation ≤ 2.3 %).

| 2022 | P1 | INC (incumbent) | YARD |
|---|---:|---:|---:|
| night median ($/MWh) | 48.05 | 51.62 | 53.91 |
| mean ($/MWh) | 55.50 | 58.27 | 57.97 |
| annual coal TWh (bench 226.3) | 234.5 | 235.2 | 236.6 |
| Jul + Aug coal TWh (bench 47.5) | 41.7 | 41.7 | **54.0** |
| yards binding / coal MW under a binding yard | — | 50 / 43.8 GW | 52 / 45.7 GW |

INC reproduces the keeper's monthly coal within 1.1 TWh in every month.

**Kill rule, as registered:**

1. Gate V (INC 2022 night median within ±$1.5 of P1, annual coal within ±5 %): **FAIL**, +$3.57 (coal passes).
2. YARD lowers the 2022 night median by ≥ $2.0: **FAIL**, it **raises** it $2.29.
3. No year up by > $0.5: **FAIL** (2022).
4. Jul+Aug ≤ 1.10 × bench (52.3): **FAIL**, 54.0.

**KILLED on all four.** Only 2022 was run: the rule stops the lane at Gate V, and 2022 is the year the lever was
for. Removing the flat month grain does what the miso-287 carry did. The binding yards draw their annual fuel into
summer, summer coal overshoots, and the rent (now on 86 % of coal MW) lifts nights. The real short yards conserved
**through** September. That is the behaviour a minimum-stock or winter-inventory target produces, and neither row
family carries one.

## 4. What this closes, and what it does not

- **Closed.** The keeper's form (a fuel-budget dual acting as an offer adder) is realistic. The pooled carry
  (miso-287) and yard-only grain (here) are both killed. Removing month grain without adding a stock target makes
  2022 worse.
- **Open, not testable here without a new identification:**
  - (a) A per-yard **minimum-stock / winter-inventory target** on a per-yard monthly pile. The pile exists as
    NWPP-NEXT-8, gated to NWPP. The target needs a cited days-of-burn source, never the solve year's own stock
    path (rule 13).
  - (b) Why **~86 % of coal MW** is under a binding yard when the IMM counts ~25–45 % conserving. The per-yard
    budget, Dec(Y-1) stock + prior-two-year receipts, is below base-cost burn at most yards. The real fleet
    burned about that quantity without a fleet-wide rent. So the non-conserving units' **offers** sat above the
    model's base cost. That is the offer-level question miso-285 left open, and it is data-gated: the MISO
    masked offer corpus has no fuel attribute (miso-138 refuted the class bridge).
- **Where MISO stands.** Keeper unchanged. Train 2023–2025 CALIBRATED (C3c ledgered). Full span **NOT-YET** on
  three routed misses: C1 ST_GAS 2019, C3a 2022, C3b 2021. **No frontier.** Routed misses are failures.

## 5. Owner ruling (2026-09-30)

*"Min-stock target design (Recommended)"*. The next lane (miso-289) is a zero-LP design lane. The design is a
per-yard monthly pile (the NWPP-NEXT-8 construction, MISO-gated on its own evidence) plus a minimum-stock /
winter-inventory target. The target is identified from prior-years days-of-burn history, never the solve year's
own stock path. A pre-check with a kill rule comes before any shard. The pile REPLACES the pooled flat `B/12` limb
(rule 19).
