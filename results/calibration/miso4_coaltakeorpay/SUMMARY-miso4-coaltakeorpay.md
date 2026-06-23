# MISO coal measured take-or-pay (miso4 coal-takeorpay) — run summary

**Determination: NOT-YET (structurally-correct input, fit-neutral).** Replaces
MISO's uniform *assumed* coal take-or-pay with the **measured** EIA-923
Schedule-5 contracted share per plant — the #11/#12-correct input — and in doing
so **refutes the task premise**: MISO coal is **~97% contract** (take-or-pay),
*more* than ERCOT (~71%), not "bituminous / market-bought / less depth." So the
deep sunk coal tranche is correct for MISO, coal offers are **not** the C3a /
import-seam lever, and the fit is unchanged. Per CLAUDE.md #1/#12 the measured
input **stays in** (it is more accurate and forward-reproducible) even though it
does not move the residual; the level/interchange miss belongs to the firm-hydro
import block (landed separately) and the seam, not the coal curve.

## Two findings that re-routed the task

1. **The named lever is architecturally inert for MISO.** The task pointed at
   `offer_curve_by_group["COAL"]`, but **MISO is not in `CAMPD_BINNING_ISOS`**
   (`{ERCOT, CAISO, NEISO, NYISO, PJM}`). So `campd_bins is None` for MISO and
   the runner builds its coal supply curve with **`split_coal_tranches`** (the
   `coal_tranche_*_fuel_passthrough` take-or-pay path, tranches `t1/t2/t3`),
   which never reads `offer_curve_by_group`. A first run editing the offer curve
   produced a byte-for-byte baseline result. The real MISO coal lever is the
   tranche fuel passthrough.

2. **Measured EIA-923 data refutes the "market-bought" premise.** The measured
   take-or-pay file `data/raw/_processed-legacy/coal_takeorpay_MISO.csv`
   (EIA-923 Schedule-5 Purchase Type: contract C / new-contract NC / tolling T
   vs spot S) gives a **tonnage-weighted contracted share of 0.969** for MISO's
   49 coal plants — vs **0.706** for ERCOT and 0.856 for PJM. MISO coal is the
   *most* take-or-pay-heavy of the three, with only 2 spot-heavy plants
   (1167 S:100%, 6213 S:47%). Pricing MISO coal at/above delivered fuel cost
   would contradict this measured structure and chase the residual via an unreal
   mechanism — forbidden by CLAUDE.md #1/#11/#12.

## What this run changes (the structurally-correct version)

Wire `split_coal_tranches` to honour the measured contracted share: when
`coal_takeorpay_from_data` is set, the **sunk first tranche** passes
`1 − contract_share` of its fuel instead of the uniform assumed
`coal_tranche_1_fuel_passthrough` (= 0.0, "100% sunk"). This is the split-fleet
analogue of the must-run adjustment `campd_tranche_fuel_frac` already applies in
the binned path. Enabled for MISO only; ERCOT and the CAMPD-binned ISOs are
untouched (flag off → byte-identical). The fleet already pays measured per-plant
delivered coal prices (`coal_plant_monthly_pricing`); this changes only the sunk
fraction, not the fuel price.

Effect at the plant level: the two spot plants now bid their first tranche at
full delivered fuel and back down — plant 1167's `t1` runs ~56% CF (2023) vs the
near-baseload CF a fully-sunk tranche holds. The ~97%-contract majority is
unchanged (`1 − 1.0 = 0.0`, the prior default).

## Result (model vs EIA-930 actual; run.js / mean-zonal-LMP basis)

| metric (model) | 2023 | 2024 | 2025 |
|----|----:|----:|----:|
| coal TWh | 180.90 | 165.51 | 231.14 |
| &nbsp;&nbsp;miso3 baseline | 181.18 | 166.08 | 231.43 |
| &nbsp;&nbsp;actual | 174.95 | 167.07 | 192.09 |
| gas TWh | 161.94 | 161.46 | 169.10 |
| &nbsp;&nbsp;miso3 baseline | 161.04 | 160.51 | 167.80 |
| &nbsp;&nbsp;actual | 172.00 | 184.63 | 166.32 |
| mean LMP | 29.25 | 26.15 | 37.54 |
| &nbsp;&nbsp;miso3 baseline | 29.15 | 26.12 | 37.54 |
| &nbsp;&nbsp;actual | 31.79 | 30.80 | 42.85 |
| net interchange (EIA +=export) | +1.39 | −6.56 | +46.24 |
| &nbsp;&nbsp;miso3 baseline | +0.14 | −7.47 | +44.98 |
| &nbsp;&nbsp;actual | −37.91 | −23.08 | −18.96 |

ST_GAS dispatch: 4.97 / 5.42 / 5.99 TWh footprint-wide, concentrated in
MISO-South (4.5–5.4 TWh); MISO-North/Central remain ~0.

## Did C2 / C3a / net interchange improve? No — near-null (the point)

- **C2 (coal/gas):** coal −0.3/−0.6/−0.3 TWh, gas +0.9/+0.9/+1.3 TWh —
  directionally toward actual but <1 TWh on ~180 TWh fleets (<0.5%). The
  displaced spot-coal `t1` MWh is picked up by the ample cheaper contract-coal
  headroom elsewhere, so footprint coal is conserved and the merit order /
  marginal unit do not change.
- **C3a (mean LMP):** +0.10 / +0.03 / 0.00 — flat; still ~9 / 15 / 12 % below
  actual. Coal offers are not the level lever.
- **Net interchange:** +1.3 / +0.9 / +1.3 TWh, i.e. marginally *more export* —
  noise-level and, if anything, slightly away from the strongly-importing actual.
  The import-seam gap is unmoved (import hours 53 / 58 / 21 % vs 98 / 91 / 79 %).

## Root cause and next lever (CLAUDE.md #1/#11)

The +20.5 % 2025 coal over-dispatch, ST_GAS≈0 in North/Central, the ~9–15 % low
LMP and the export seam are **not** caused by mis-set coal offers: the measured
data confirms MISO coal genuinely runs deep take-or-pay baseload, which is real
market behaviour and stays in. With coal at its measured-correct cost the
marginal price still sits below the gas fleet, so the level and the import seam
must be carried by **(1) the firm-hydro (Manitoba) import block** (MISO's single
largest real import, ~10–15 TWh/yr, outside any gas-margin seam — landed in main
via #810) and the seam pricing, and **(2)** any gas-side or coal-must-run-floor
review — not the coal offer curve. This run closes the coal-offer hypothesis
with measured data.
