# MISO coal supply-class derivation (miso6 coalclass) — run summary

**Determination: NOT-YET** (PROBE). This run fixes the **C1 coal-class
misclassification** flagged in miso2/miso3 (model coal was all unclassified
generic `COAL`; the EIA-923 benchmark splits MISO coal into PRB/BIT/LIGNITE),
so the model and benchmark now classify coal **identically**. As anticipated by
miso3's lever-3 handoff and CLAUDE.md #13, the price-level fit does **not**
improve — it is essentially unchanged (2025 marginally worse) — and the
remaining over-dispatch of cheap PRB coal is the *discovered bug*: the
ERCOT-calibrated COAL_PRB offer curve is too cheap for MISO. The classification
**stays in** (it is the accurate, measured input); the root cause is filed for
the market-specific MISO coal-curve lever (`claude/miso-coal-curves-*`).

## What this run adds vs miso2/miso3
A derived **`data/raw/_processed-legacy/coal_supply_MISO.csv`** (57 MISO coal
plants → **38 COAL_PRB / 17 COAL_BIT / 2 COAL_LIGNITE**), so MISO coal plants
carry their real EIA-923 fuel rank instead of falling through to generic `COAL`.
`fleet.coal_supply_class` already globs `coal_supply_*.csv`, so no dispatch-code
change was needed — adding the file routes each plant onto its rank's offer
curve and reporting class.

**Data path (W1 fallback).** The W1 layout collapse removed the raw `f923_*.zip`
that `scripts/derive_coal_supply.py` read, and the receipts parquet keeps only
`fuel_group=Coal` (not the rank code). The script now falls back to the
processed `eia923_monthly_generation.parquet`, classifying each coal plant by its
**dominant net-MWh Page-1 `fuel_type`** (BIT/SUB/LIG/WC → `COAL_CODE_TO_SUPPLY`)
— exactly the energy-source signal the EIA-923 benchmark uses, so model and
benchmark bucket each plant the same way by construction. This is an accurate
measured input that regenerates for any forward year (CLAUDE.md #13), not a
fit-to-residual.

## Result — C1 per-class coal alignment (model vs EIA-923 benchmark, TWh)
| year | class | model | benchmark |
|------|-------|------:|----------:|
| 2023 | COAL_PRB | 125.22 | 121.77 |
| 2023 | COAL_BIT | 48.99 | 57.07 |
| 2023 | COAL_LIGNITE | 6.69 | 7.05 |
| 2024 | COAL_PRB | 115.43 | 116.55 |
| 2024 | COAL_BIT | 44.85 | 53.33 |
| 2024 | COAL_LIGNITE | 5.23 | 6.52 |
| 2025 | COAL_PRB | 157.53 | 139.39 |
| 2025 | COAL_BIT | 67.51 | 57.45 |
| 2025 | COAL_LIGNITE | 6.10 | 5.84 |

**Before (miso2/miso3):** all model coal sat in the unclassified `COAL` bucket,
so per-class C1 was structurally broken — 2025 showed COAL_PRB **−132 TWh** /
COAL_BIT **−63 TWh** (the benchmark's PRB/BIT split with ~0 model in those
classes). **After:** the model populates the same PRB/BIT/LIGNITE buckets the
benchmark does; the residual is no longer a *classification* gap but a *level*
gap (total coal slightly over-dispatched, concentrated in COAL_PRB).

## Result — C2/C3a/net interchange (model vs EIA-930 actual)
| metric | 2023 | 2024 | 2025 |
|--------|-----:|-----:|-----:|
| model mean LMP | 28.89 | 25.56 | 36.85 |
| miso2/miso3 LMP | ~28.7/28.86 | ~25.5/25.57 | ~36.8/36.89 |
| actual LMP | 31.79 | 30.80 | 42.85 |
| **C3a (LMP error)** | **−9.1%** | **−17.0%** | **−14.0%** |
| miso3 C3a | −9.2% | −17.0% | −13.9% |
| model net interchange (EIA +=export) | +1.39 | −6.56 | +46.24 |
| miso2/miso3 net interchange | +0.1 | −7.5 | +45.0 |
| actual net interchange | −37.91 | −23.08 | −18.96 |
| model coal (TWh) | 180.90 | 165.51 | 231.14 |

**C3a is essentially unchanged** — 2023 marginally better (−9.1% vs −9.2%), 2024
flat, **2025 marginally worse (−14.0% vs −13.9%, a 0.04 $/MWh drop)**. Net
interchange shifts marginally toward *more export* (the wrong direction vs the
actual import). Both are the expected, tiny signature of routing the 38 PRB
plants onto the cheaper COAL_PRB curve (econ_low 0.77× + the coal_prb
passthrough sigmoid) vs the generic 0.95×. COAL_BIT == generic COAL today, so the
17 BIT plants are unaffected on price; the 2 LIGNITE plants are negligible.

## Discovered bug (CLAUDE.md #13) — filed, NOT fixed here
The classification is correct and measured, so the worse-direction residual is a
**discovered model bug, not a reason to revert**: the model now **over-dispatches
COAL_PRB** (2025 157.5 vs benchmark 139.4 TWh; total coal 231 vs 203) because the
**ERCOT-calibrated COAL_PRB offer curve is too cheap for MISO**. ERCOT's PRB
plants are PRB-by-rail under deep take-or-pay; MISO's sub-bituminous fleet is
more market-bought, so the ERCOT econ_low 0.77× / passthrough sigmoid under-bids
MISO PRB coal, floods it into the stack and depresses the marginal LMP — the same
mechanism that keeps MISO's price ~9–17% low and lets the seam export instead of
import. **Root cause filed for `claude/miso-coal-curves-*`** (market-specific
MISO coal offer curves), the level lever already named in miso3's handoff
(lever 1). Do not bury this back in an inaccurate (all-generic) classification.

## Why this is a PROBE, not a keeper
The structural fix (identical model/benchmark coal classification) is correct and
retained, but it does not move C2/C3a/net interchange toward the actuals (and
nudges them marginally the wrong way), so MISO remains out of band on price level
and interchange. Registered as NOT-YET pending the MISO coal-curve lever and the
firm-hydro (Manitoba) import block (miso3 lever 2).
