# PRECOMMIT — miso-288: zero-LP pre-check of the coal budget at yard grain only (pooled monthly limb off), written before it is measured

```
LANE    : miso-288 (owner ruling "2022 coal-scarcity study", miso-287 §6)
KEEPER  : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span, 2019-2025), unchanged
LP      : none. Fleet-only rebuilds + keeper committed P1 hourly sidecars + run payload
PROBES  : scripts/probes/_miso288_coal_scarcity.py (phase 0, measured, below)
          scripts/probes/_miso288_yard_precheck.py  (written AFTER this file is pushed)
STATUS  : pre-registration. No number in §4 exists yet.
```

## 1. Phase 0: how the real 2022 fleet expressed its coal shortage (measured)

Sources: EIA-923 Sch. 2 stocks + Sch. 5 receipts (plants in the MISO BA), CAMPD hourly gross
load (coal-primary units at those plants), ILLINOIS.HUB DA LMP, IMM 2022 State of the Market
report (Potomac Economics, §IV.H and §VI.B). Output `results/calibration/_miso288_coal_scarcity.json`.

1. **Offer adders, on part of the fleet.** IMM: coal conservation "raised the costs of a large share
   of the coal fleet"; by 2022 "most coal-fired resources experiencing fuel and reagent supply
   issues reflected the conservation measures in their reference levels" (p.99). Figure 26
   (digitized, of ~47 GW coal): **~11–22 GW subject to conservation in Jan–Sep 2022** (Mar ~11,
   Aug ~22), falling to ~6 GW by December. So scarcity was priced **as an opportunity-cost adder
   on roughly 25–45 % of coal capacity**, not on the whole fleet.
2. **Seasonal draw, not flat burn.** 2022 implied burn (k tons): Apr 8,577, Jul 14,389, Aug 13,285,
   Oct 8,355. Stocks rose Jan→May (24.2→26.9 Mt), fell Jun→Aug to 22.3 Mt (63 days on hand), and
   rebuilt Sep→Nov. Same shape in every year 2019–2024. The pile was never run down: the 2022
   minimum was 63 days (2021: 58).
3. **No derate or dark-unit signature.** Units with zero monthly op-hours and the monthly
   output-ceiling ratio (0.91–0.94) are in line with 2021 and 2023.
4. **Night/day shape is not the error.** Summer night/day coal ratio, real vs keeper: 2022 Jul
   0.75 vs 0.71, Aug 0.72 vs 0.72. The keeper is short of summer coal in **all** hours (Jul: real
   29.3/39.0 GW gross night/day vs keeper 22.6/31.9), and long in May and Sep–Nov.
5. **Price.** 2022 night medians, keeper P1 vs hub: Jun 59.3/51.2, Jul 65.2/52.9, Aug 68.4/62.0,
   Oct 44.7/36.5, Nov 41.6/32.3.

Reading: the LP's **form** (a dual acting as an offer adder) matches how the real fleet expressed
scarcity. Its **grain** does not. The pooled monthly limb (`coal_fuel_inventory`, flat `B/12`)
prices a fleet-wide adder, and forces a flat monthly profile that the measured burn contradicts
in every year. The per-yard annual rows (`coal_fuel_inventory_plant_grain`, K) are the grain the
IMM describes: only the yards that are short carry a dual.

## 2. The candidate: YARD (a config flip, no code)

Keep `coal_fuel_inventory_plant_grain = true`; set `coal_fuel_inventory = false`. The resolver
already permits either limb alone (`run_calibration.resolve_coal_budget_arms`; neiso-117 runs yard
rows alone). Summed over yards the annual budgets equal the pooled annual budget
(`build_coal_plant_budget` docstring), so **the annual identity is kept and only its flat month
grain is removed** (rule 19: one mechanism, one limb retired, nothing stacked). Zero new
parameters; same measured inputs and the same forward story (rule 13). The miso-287 pooled carry is
not re-tested: YARD changes the partition, the carry did not.

Stated risk, from miso-287: removing the month grain lets short yards move burn into summer. The
real short yards conserved **through** September. So YARD may over-run summer coal. §4 guards it.

## 3. The pre-check (zero LP)

Per year 2019–2025, fleet-only rebuild of the keeper recipe, the `_miso287` P1 bid stack
(base cost + startup markup) cleared hourly at the keeper's P1 LP quantity (wind, solar, biomass,
OTHER excluded):

- **Emulator.** Each binding row is a $/MMBtu adder `λ` × HR on the coal rows it covers.
  Coal row `g` carries `λ_pool[m(t)]` (if pooled-rowed) `+ λ_yard[yard(g)]`. The `λ` vector is
  found by projected subgradient on the row violations until every row is within 1 % of its cap
  (or 200 iterations; the residual violation is reported).
  - **INC** (incumbent): pooled monthly `B/12` rows + per-yard annual rows.
  - **YARD** (candidate): per-yard annual rows only.
- **Gate V.** INC must reproduce the keeper's P1 **2022 night (h0–5) median within ±$1.5** (P1 =
  $48.05) **and** the keeper's 2022 annual coal TWh within ±5 %. Otherwise the emulator does not
  describe the LP: the lane stops, no shard.
- **Bench coal** = run payload `volErr` COAL_* `a` (EIA-923 basis), summed over zones.

## 4. Kill rule (fixed now)

No shard unless **all** hold:

1. Gate V passes.
2. YARD moves the **2022 night median down by ≥ $2.0** vs INC.
3. YARD moves no year's night median **up** by more than $0.5 vs INC.
4. **Quantity guard (the carry's failure mode).** YARD 2022 Jul+Aug coal ≤ **1.10 × bench** Jul+Aug,
   and in every year |YARD annual coal − bench| ≤ |INC annual coal − bench| + 5 TWh.

If 1–4 hold: PRECOMMIT the seven per-year shards (miso-280 template §7/§8), launched on the owner's
card. If any fails: FINDING, matrix, owner card. **No threshold moves after the probe runs.**

## 5. What this does not claim

- C3a is a mean over all hours. The mean shift vs hub is reported, not gated.
- It does not test a minimum-stock floor or a per-yard monthly pile. Both would need a new
  identification (a days-of-burn source, or MISO's own contract census). They are named in the
  FINDING if YARD dies.
