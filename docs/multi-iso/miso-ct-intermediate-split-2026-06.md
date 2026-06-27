# MISO CT_PEAKER classification audit + intermediate-duty offer split (2026-06)

## The miss

Run-14 keeper (`bit_takeorpay_sigmoid`) C1 fuel-mix: `CC_REGULAR` +14–21 TWh
**over**, `CT_PEAKER` −22–24 TWh **under**, with gas under-running its EIA-923
benchmark (2023 model gas 214.8 vs 249.0). The under-run CT energy was spilling
onto the cheaper CC fleet and onto imports.

## The audit — they are NOT mislabeled combined cycles

Hypothesis going in: the always-on `CT_PEAKER` units (≈half the 79-unit MISO CT
fleet run at measured median CF 50–150%, baseload-like) are combined-cycle or
cogeneration plants mislabeled as peakers, carrying the steep peaker offer and
never clearing.

**Cross-check against EIA-860 (prime mover + technology) refutes this.** Every
one of the 79 MISO `CT_PEAKER` units — including the named offenders 57842
Wabash Valley, 55718 Dean, 61144 Astoria, 55234 Audrain, 55029 De Pere, 56604
Hardin County, 976 Marion, 7844 Minnesota River — is a genuine **simple-cycle
GT or IC** unit:

- Prime mover `GT` (gas combustion turbine) or `IC` (internal-combustion
  engine); **none** report a combined-cycle prime mover (`CA`/`CS`/`CT`/`CC`).
- Technology = "Natural Gas Fired Combustion Turbine" / "…Internal Combustion
  Engine"; none "…Combined Cycle".
- None are CHP-flagged; none have an operable solid-fuel gasifier (Wabash
  Valley's IGCC coal gasifier is retired — only an NG GT remains operable;
  Marion's coal steam units are already a separate `COAL` klass).

So the prime-mover **classification is correct** — `classify_plant`
(`config/plant_taxonomy.py`) buckets them rightly. What differs is their **duty
cycle**: MISO has a large population of intermediate / near-baseload
simple-cycle CTs (modern efficient frames, load-pocket and capacity-contracted
units) that the single steep peaker offer curve mis-prices.

## Root cause

The one `CT_PEAKER` offer curve (committed 1.55× / econ 1.27–1.98× / peak
13.15×) was calibrated for **true peakers**: the committed band is a deliberate
start-cost-recovery hurdle that keeps low-CF peakers from parking in-merit. An
always-running intermediate CT amortizes its one start over thousands of hours,
so that hurdle is wrong for it — it prices the unit's baseload energy *above*
the CC fleet, the LP never clears it, and CC over-runs to fill the gap.

## The fix — measured-duty offer split (`ct_intermediate_split`)

A simple-cycle CT whose measured CAMPD median CF (`thermal_tranches_MISO.csv`
`median_cf`) is ≥ `ct_intermediate_cf_threshold` (default **50**, 45 units /
9.5 GW / 52% of CT capacity) is routed to a flatter **`CT_INTERMEDIATE`** offer
curve (committed 1.00 / econ 1.00–1.20 / peak 3.00) instead of the steep
true-peaker curve. True peakers (median CF < 50, e.g. 1206 Summit Lake, 7925
Lakefield Junction) keep `CT_PEAKER`.

- Cohort: `fleet.ct_intermediate_plants(iso, threshold)` (lru-cached, derived
  from the tranche CSV); routing: `fleet._offer_curve_for_group`.
- Gate: `ScenarioConfig.ct_intermediate_split` (default off, keepers unchanged);
  CLI `--ct-intermediate-split` / `--ct-intermediate-cf-threshold`.

**Admissibility (CLAUDE.md #1/#11/#12):** the median CF assigns an offer
*shape* (a structural duty-role classification), never pins measured output. It
regenerates per unit and year from CAMPD and responds to changed conditions (a
unit that stops running intermediate falls out of the cohort) — the same basis
as the `ST_GAS_PEAKER_PLANTS` carve-out. The classification fix is structural
(right mechanism), not an offer tuned to the residual.

## Result (3-year, `--ct-intermediate-split` on top of the run-14 levers)

<!-- FILL: 3-year fuel-mix deltas vs keeper -->

2024 smoke (single-year diagnostic, not registered):

| metric | keeper | split-on | EIA-923 |
|---|---|---|---|
| gas TWh | 226.16 | 233.65 | 257.84 |
| coal TWh | 178.18 | 174.67 | 175.13 |
| total gen | 631.70 | 635.68 | (EIA-930 net gen 636.07) |
| energy-balance drift | −4.37 ⚠ | −0.39 ✓ | ±3.0 tol |

Gas under-run cut ~24%, coal corrected to near-exact, total-gen energy balance
back inside tolerance. Imports fall (domestic CTs serve load instead of
over-importing).

## Open / not addressed here

- **C3c scarcity tail** (0 h > $200) is unchanged: it needs an ORDC/scarcity
  adder MISO lacks, not a lower peaker offer. Lowering the true-peaker peak
  block raises CT *volume* but cannot create a price tail without scarcity
  pricing — that mechanism is a separate structural gap.
- True-peaker `CT_PEAKER` band (peak 13.15) left as-is; the intermediate split
  carries the volume correction.
