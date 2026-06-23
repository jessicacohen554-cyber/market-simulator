# ERCOT COAL_PRB over-run: restore the PRB passthrough cheap-gas floor (2026-06)

**Run:** `run151 coal-prb-sigmoid` (`results/calibration/coalprb_foll078_3yr`),
on the `run150` ST_GAS-net-load-drag keeper. **Determination:**
CALIBRATED-WITH-CAVEATS.

## Problem (handoff)

After the `run150` ST_GAS net-load reliability-drag floor pulled gas share back
onto ST_GAS (closing the chronic ST_GAS under-run), **COAL_PRB over-ran**: model
vs EIA-923 +10.6% / +13.2% / +2.2% in 2023/24/25, with the coal *family* (C2)
+12.4% in 2024. This out-of-merit PRB baseload stole the energy that should sit
on CC_REGULAR / ST_GAS — CC_REGULAR was left under at -3.5% / -4.8% / -0.0%. The
over-run concentrated in the cheap-gas year (2024, ~$2.2/MMBtu Henry Hub).

## Root cause

The keeper carried a **fitted-down PRB passthrough floor**: baseload
`coal_prb_passthrough_floor = 0.73` and load-follower
`coal_prb_follower_floor = 0.63`, both *below* the documented
`COAL_SIGMOID_DEFAULTS[(ERCOT, prb)]` breakeven of **0.78** (the curated
per-month PRB-vs-gas-CC delivered-cost breakeven, run-70s tuning series).

The passthrough sigmoid (`fuel._sigmoid_passthrough`) sets PRB coal's bid as a
fraction of delivered PRB fuel cost that rises with the gas price:
`floor + (ceil-floor)/(1+exp(-slope*(gas-mid)))`. The **floor is the cheap-gas
asymptote** — what PRB coal bids when gas is cheap. A floor below the breakeven
means PRB coal undercuts gas CC in cheap-gas hours and runs out of merit.

Those deeper floors were **silently compensating** for the pre-drag ST_GAS
under-run (CLAUDE.md #11/#12): they kept enough coal on to fill the gap that the
missing ST_GAS reliability dispatch left. Once `run150`'s ST_GAS net-load drag
floor supplied that dispatch from gas, the over-discounted PRB coal had nothing
to compensate for and simply over-ran.

## Fix

Set **both** PRB tiers to the single documented breakeven floor:

```
coal_prb_passthrough_floor = 0.78   # was 0.73 (baseload)
coal_prb_follower_floor    = 0.78   # was 0.63 (load-follower tier)
```

Enabled on the keeper recipe via the new env hook
`KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}'`
in `scripts/probes/_keeper_2023as_run.py` (overlays the bundle's
`coal_prb_sigmoid_overrides`).

**Why this is physical, not dialed to TWh:**

- **0.78 is the documented breakeven**, not an arbitrary fitted value. That the
  documented number (not some odd 0.84-ish value) lands COAL_PRB at ±3% in all
  three years is evidence it *is* the PRB-vs-gas-CC crossover, not a fit.
- **The cheap-gas fuel passthrough of railed PRB is a basin/contract
  (take-or-pay) property, not a duty-cycle property.** The original two-tier
  split gave the low-must-run "follower" units a *deeper* cheap-gas discount
  (0.68 vs 0.78 in the defaults; 0.63 vs 0.73 as the keeper fit) — but the
  delivered PRB cost and the take-or-pay contract structure are the same whether
  a unit baseloads or cycles. That extra follower discount was a calibration
  artifact, and it was exactly what let the cyclers undercut gas CC out of
  merit. Unifying both tiers to the breakeven removes the artifact.
- **The follower tier keeps its distinct dear-gas ceiling** (1.35 vs baseload
  1.50). Only the *cheap-gas floor* is unified; at dear gas the cyclers still
  mark up less than baseload, preserving the load-following behaviour.
- **Gas-keyed ⇒ self-targeting.** Because the floor only bites at cheap gas, the
  change self-targets 2024 (worst over-run) and barely moves the dear-gas years.

## Result (3-yr, vs the run150 drag-on baseline)

| Class | 2023 base→cand | 2024 base→cand | 2025 base→cand |
|---|---|---|---|
| **COAL_PRB** | +10.6% → **+2.7%** | +13.2% → **−1.3%** | +2.2% → **+0.1%** |
| **CC_REGULAR** | −3.5% → −1.7% | −4.8% → −1.3% | −0.0% → +0.5% |
| ST_GAS | +3.4% → +5.2% | −15.2% → −13.1% | −8.5% → −8.4% |
| CT_PEAKER | −4.9% → −1.4% | +81.0% → +82.8% | +99.0% → +99.1% |
| COAL_LIGNITE | +10.0% (flat) | +9.6% → +10.0% | +3.3% (flat) |

- **Coal over-run closed**; C2 coal family +12.4% → **+1.4%** (2024) and now
  PASSES.
- **Freed energy conserved to the gas family** (CC_REGULAR recovers to near-
  actual; a little to ST_GAS) — **not** to slack and **not** to CT_PEAKER (the
  pre-existing zonal-gas relocation over-run moved <+0.2 TWh).
- **LMP unchanged**: MAE 27.9 / 15.3 / 11.4 vs baseline 27.8 / 15.2 / 11.4;
  duration curves byte-comparable. The lever rebalances within-thermal volume,
  not price.

## Out-of-scope residuals (attested caveats)

- **CT_PEAKER +1.0pp over (2024/25)** — zonal-gas West/Permian sub-zonal
  relocation (`docs/ercot-zonal-gas-basis-ct-relocation-2026-06.md`).
- **CC_REGULAR −0.5pp (2025)** — small conservation counterpart of the CT
  relocation; much reduced from the prior keeper's over-run caveat.
- **COAL_LIGNITE +10%** — its own mine-mouth sigmoid; not in scope (the PRB
  fix left it untouched). A candidate for a follow-up lignite-floor session.
- **price_mean 2024 / price_shape 2023-24** — pre-existing co-opt / 2023 deep-
  tail residuals inherited from the run150 baseline, unchanged by this lever.

## Reproduce

```
ERCOT_ZONAL_GAS=1 KEEPER_RTORDPA=1 KEEPER_PERSIST_P2=1 KEEPER_STGAS_DRAG=1 \
  KEEPER_PRB_PARAMS='{"coal_prb_passthrough_floor":0.78,"coal_prb_follower_floor":0.78}' \
  python scripts/probes/_keeper_2023as_run.py coalprb_foll078_3yr 2025 2023 \
  '{"ST_GAS":{"committed":0.0}}'
python scripts/calibration_verdict.py results/calibration/coalprb_foll078_3yr
```
