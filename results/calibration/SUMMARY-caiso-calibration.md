# CAISO backcast calibration — diagnosis & iteration log (2026-06-16)

Branch: `claude/caiso-backcast-zonal-tests-34emxa`. Goal: improve CAISO LMP and
generation-mix accuracy across 2023/2024/2025; flag structural needs.

Scratch bundles (`caiso_tune*`, `caiso_probe2_*`) are gitignored and do **not**
survive into a fresh container — re-run the baseline first. A 3-year run is
~27 min; a single year ~9 min. **Iterate on 2024** (it has the LMP reference and
is the middle gas-price year), confirm keepers on 3 years.

Setup: `uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"`.

> **CORRECTION (2026-06-16 structural audit — see
> `AUDIT-caiso-structural.md`):** the "gas target" column below is **EIA-930
> `NG: NG`, which is geo/bio-inflated**. EIA-930 CISO reports *no* geothermal
> (`NG: GEO` 100 % NaN) and no biomass, so its gas figure silently absorbs
> ~8 TWh geothermal (The Geysers) + ~3 TWh biomass that the model (and EIA-923)
> break out separately. On the clean baseline, **model 2024 total gas (67.95)
> matches the EIA-923 reference (67.68) to <0.5 %** — the "−9 gas gap" is a
> benchmark artifact. **Score CAISO gas against EIA-923; do NOT tune the offer
> curve to raise gas toward the EIA-930 number.** (2023 gas *is* genuinely low,
> but from over-import, not gas supply.) The real LMP problem is the over-priced
> midday FLOOR (flat all-hours import + gas_cc never decommitting), not the mix.

## Targets (EIA-930) and baseline errors

| Year | gas target | base gas | net-import target | base import | base LMP | actual LMP |
|---|---|---|---|---|---|---|
| 2023 | 87.8 | 67.7 (−20) | 28.5 | 38.6 (+10 over) | $85.9 | *none* |
| 2024 | 85.4 | 76.2 (−9) | 30.8 | 26.9 (under) | $60.6 | $32.9 |
| 2025 | 79.0 | 81.6 (+2.6) | 35.8 | 33.2 (under) | $65.0 | $33.6 |

Baseline = `caiso_tune0_base` (3-yr, current main, `--commitment --priced-interchange`).

## Core diagnosis (high confidence)

- **LMP ~2× too high; a price-FLOOR problem concentrated in Feb–Dec.** January is
  already accurate (Jan-24 model $63.7 vs actual $67.7); spring/summer is +20…+39
  too high (Apr/May model $48/$48 vs actual $14/$11).
- **Root cause:** in a spring-midday hour with ~17 GW solar, gas_cc stays
  *committed* (~651 MW) and sets the clearing price at the committed-band bid
  (~$36). Gas never decommits through the solar glut, so the model can't reach
  the real near-zero spring prices. Real CAISO exports surplus midday solar
  (interchange swings to +3,500 MW); the model imports 96–100% of hours and
  almost never exports — its interchange and price distributions are far too flat.
- **Import capacities are correct** (achievable best-case net-import matches
  actuals every year via `derive_import_tranches.py` measured-only score); the
  tranche **prices/merit position** are off. Volume error is non-uniform (over in
  2023, under in 2024/25) — the inherent tension of a single static curve across
  three gas-price regimes ($2.54/$2.19/$3.52).

## Structural conclusions

- **Do NOT add a CAISO ORDC overlay or ancillary-services stream for LMP.** Both
  are ERCOT-only capacity/scarcity-tail mechanisms; CAISO is RA-backed ($2,000
  cap, no ORDC) and the model already *over*-prices — a scarcity adder makes it
  worse.
- **No 2023 actual CAISO LMP** (RTM never fetched; OASIS aged out). LMP scoring is
  2024/25 only. Consider a 2023 proxy if needed.

## Jacobian guidance

`python scripts/derive_offer_curve_jacobian.py --iso CAISO` — joint-move recipe
wants CC/gas committed+econ bands ~−0.15 (CC_REGULAR committed 0.92→0.77,
econ_low 1.06→0.91, econ_high 1.27→1.12, ST_GAS committed 0.81→0.72) but **all
moves are trust-region-frozen** (probes only sampled ±0.05). CC_REGULAR is the
dominant high-confidence marginal class. 2023 per-class TWh err (CHP biased low):
CC_REGULAR −4.0, CT_PEAKER −4.1 (under); ST_GAS +3.4, CT_CHP +1.3 (over).

## Iteration log

### iter 1 — CC_REGULAR committed −0.20, econ_low/high −0.15 (2024)
Cmd: `... --offer-curve-delta-json '{"CC_REGULAR":{"committed":-0.20,"econ_low":-0.15,"econ_high":-0.15}}'`
Result (2024): **gas 76.2→83.5** (target 85.4; −9.2→−1.9 — mix nearly fixed).
**LMP 60.6→58.0** (target 32.9 — barely moved). Net import 26.9→20.1 (−10.7 under).
Spring still +33…+38; Jan went −4→−8 (slightly under).
**Conclusion:** lowering the committed *bid* fixes the MIX but not LMP, because the
spring floor stays gas-set — gas never decommits. **LMP needs the decommit/floor
structural fix, not more bid-lowering.** This was applied as a runtime
`--offer-curve-delta-json`, NOT baked into code.

### iter 2 — per-tranche border-carbon EF (clean imports exempt) + iter1 delta (2024)
Code fix (committed): CARB border carbon scaled by per-tranche emission factor, so
clean import blocks (PNW hydro, DSW solar/Palo Verde) pay no border carbon instead of
the flat 0.428 unspecified default. Run also carried iter1's CC offer delta.
Result (2024): **net import 20.1→32.1** (target 30.8 — now ON TARGET; the clean blocks
now beat domestic gas midday as they should). **LMP 58.0→53.5** (spring −$4-5; Apr
46.6→41.9). **But gas 83.5→71.8** (−13.6 — the new imports displaced gas ~1:1) and **Jan
56.3→ −11.4 vs actual** (winter now UNDER-priced).
**Conclusions:**
- Gas and imports trade off serving the same residual load. Model now has gas+import =
  104 TWh; reality is 116 (gas 85 + import 31). The missing ~12 TWh is served by
  over-generation elsewhere — **solar over-absorption** (model curtails 0 vs ~2.5 TWh
  reported; over-flat solar shape → midday net-load never goes negative). **This is a
  STRUCTURAL input problem (solar capacity/shape, BTM, must-run floors, net-load duck
  curve), not an offer-curve problem** — do the structural audit before more tuning.
- iter1's econ_low/econ_high −0.15 cut was too deep for WINTER (Jan now under). The
  spring-targeted lever is the COMMITTED cut; back off the econ cut in a refined keeper.
- The remaining LMP overage (+20-30 Feb-Nov) is still floor-driven: gas stays marginal
  midday because net-load stays positive (solar over-absorbed) and ~3 GW gas/CHP is
  pinned committed.

## Recommended next steps

1. **Spring floor (LMP) — the key lever:** let gas **decommit** midday so near-zero
   solar/curtailment is marginal. Investigate `cc_committed_per_plant` /
   min-stable-load / the P2 commitment screen — too much CC is pinned committed.
   This (not bid level) is what unlocks the spring lows.
2. **Export node reshaping:** make midday surplus *export* (price→$0/$8) instead of
   importing. `derive_import_tranches.py --iso CAISO --year <Y> --bundle <bundle>`
   (bundle mode); watch circularity (anchors to model price). Smaller/pricier cheap
   import tranches + easier exports widen the swing.
3. **2025 hydro −9 TWh** (model 12.3 vs 21.3) — likely a hydro-budget/backfill data
   gap; check `--hydro-backfill-year` and the 2025 EIA-923 hydro vintage.
4. Once a direction is locked, bake **CAISO-specific** offer-curve values into
   `scripts/run_calibration.py` `_calibration_config` (current `econ_low=1.06`/
   `econ_high=1.27` are shared non-PJM/non-ERCOT defaults — give CAISO its own
   branch so NEISO is unaffected). Run a 3-year confirmation, re-derive the
   Jacobian, register the keeper via the `calibration-report` skill.

Commit discipline: scratch bundles gitignored; commit only code/constants/offer-curve
changes, the re-derived Jacobian CSV, and a final registered keeper.

## Determination status — caiso-18 outage-regate BTM re-solve (2026-06-22)

**DETERMINATION: NOT-YET** (scorer: `python scripts/calibration_verdict.py
--run-id 2026-06-21-caiso-18-outage-regate`). C6 governance now PASS (truthful
`calibration_attestation.json` added). BTM regen done: byte-faithful re-solve
(gmModel reproduces the keeper exactly) + `btm.parquet` (CC_CHP 4.26, CT_CHP
1.77 TWh host steam). CC_CHP residual −7.07→−2.82 TWh, and **+0.48 TWh PASS vs
raw EIA-923−BTM** — the over-statement was the BTM artifact the re-gate targeted.
Deciding fails are genuine **MODEL MISSes** (not ledgerable): C2 gas −15.8% vs
the authoritative EIA-930 grid total (CAISO EIA-923 under-reports gas ~25%:
raw923 68.3 / 923−BTM 62.3 / e930 85.4 TWh), and the CC-over / CT-under merit
split — the doc-06 structural midday-import/solar-glut + import/BTM wedge, the
dominant remaining lever. Not chased here (BTM-attestation scope).
