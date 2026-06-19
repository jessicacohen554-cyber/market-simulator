# CAISO formula-based operating-reserve withholding — 2024 findings

**Feature:** `ScenarioConfig.as_reserve_formula` (default off, CAISO-only) /
`run_calibration_full.py --as-reserve-formula`.
**Code:** `fleet.caiso_operating_reserve_mw` + the CAISO branch in
`generators_to_fleet_arrays`. **Tests:** `tests/test_as_withholding.py`
(`TestCaisoReserveFormula`).

## What it does

A published-standard, no-fitted-constants upward operating-reserve requirement,
withheld from the gas top-of-merit energy headroom (the same `_withdraw_top_of_merit`
path used for measured ERCOT up-AS / PJM Primary Reserve):

```
R(t) = max(MSSC, 0.067 * load(t)) + 0.01 * load(t)
```

* **Contingency** = WECC MORC: greater of the most-severe single contingency
  (`MSSC` = largest single online unit nameplate — the model resolves this to the
  **1,122 MW Diablo Canyon unit**; imports/wind/solar excluded as non-credible
  single contingencies) or 6.7 % of load (5 % hydro + 7 % thermal for CA's mix).
* **Regulation-up** ≈ 1 % of load. Reg-Down (downward) is excluded — it withholds
  no upward energy offer.

At a 35 GW evening load, `R(t) ≈ max(1122, 2345) + 350 ≈ 2.7 GW`.

## 2024 before/after (vs `actual_lmp.json` `rt_mon`)

Baseline: `--commitment --priced-interchange`. On: same + `--as-reserve-formula`.
System price = mean-across-zones of `system.parquet`, P2 pass
(`scripts/probes/_caiso_asformula_compare.py`).

| metric | base | formula | Δ |
|---|---|---|---|
| annual mean LMP | 57.43 | 57.43 | +0.00 |
| max LMP | 83.74 | 83.74 | +0.00 |
| MAE vs rt_mon | 25.46 | 25.46 | +0.00 |
| midday floor (hr 10–15) | 51.65 | 51.65 | +0.00 |
| evening tail (hr 17–21) | 61.19 | 61.19 | +0.00 |

Only **16 of 8 760 hours** move at all; the **largest LMP change is +$0.31**.
The evening tail and the midday floor are both unchanged.

## Why it is a near-no-op on this baseline (structural, not a bug)

The withholding fires correctly (`as_reserve_formula=True` is recorded; ~2.7 GW
is withdrawn from gas top-of-merit), but **CAISO 2024 is gas-long** in the model:

* Peak gas dispatch is **16.8 GW against ~28.9 GW nameplate (58 %)**; median gas
  dispatch is ~8 GW.
* In the top-50 highest-price hours, gas runs at only ~9.4 GW and imports at
  ~6.1 GW — **neither is near its cap**. The $83.74 ceiling is simply the priciest
  *dispatched* import/gas tranche; the system never runs short.
* That leaves **12–19 GW of idle gas headroom**, which dwarfs the ~2.7 GW reserve.

`_withdraw_top_of_merit` removes the *most expensive* gas headroom first — in a long
system that is exactly the idle peaker capacity sitting **above** the marginal
price-setter. The withdrawal lands entirely on capacity that was not being
dispatched, so the margin (mid-merit gas / the import-ceiling tranche) never moves.

Pure top-of-merit **capacity** withholding can only lift a system that is *tight*
(e.g. ERCOT at scarcity, where reserves and energy compete for the last MW). It
cannot lift a system with 12+ GW of idle gas — and no *defensible* reserve quantity
(~2.7 GW) would change that. This is precisely the "longness / marginal-offer
problem handled by other workstreams" called out in
`AUDIT-caiso-structural.md` (phase 2) and `NEXT-caiso-floor-prompts.md`: the AS
fix is not the lever for CAISO's over-supply.

## Status

The scaffold is **correct, tested, default-off and byte-identical when off** —
ready to be activated once either:

1. the separate longness/floor workstream tightens the system (removes the import
   over-supply / RA must-offer + negative-bid floor), so the ~2.7 GW reserve
   actually competes with the marginal unit; or
2. it is replaced with **measured OASIS cleared-AS MW** (`AS_REQ` / `AS_RESULTS`)
   in a genuinely binding regime — the formula is the placeholder until the
   remote-env outbound-network block on OASIS is lifted.

It is deliberately left **off** on the calibration baseline: turning it on today
neither helps nor hurts (16 hrs, +$0.31), and using it to force a lift would
"paper over the floor," which the structural audit explicitly warns against.
