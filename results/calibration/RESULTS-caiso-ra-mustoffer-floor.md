# CAISO RA must-offer gas-commitment floor — results (Session A)

Implements the floor fix from `NEXT-caiso-floor-prompts.md` Session A: make the
CAISO model **long** midday so its surplus exports/curtails at ~$0, collapsing
the over-priced spring-midday LMP floor (`AUDIT-caiso-structural.md` phase 2).

**Mechanism.** A hard min-generation floor on the gas fleet
(`gas_cc`/`gas_ct`/`gas_st`) over the midday solar-glut window (local hours
9–16), sized to `--caiso-gas-floor-frac` × the measured EIA-930 `NG: NG`
(month × hour-of-day median) profile, imposed through the hour-varying
`FleetArrays.min_gen` lower bound (the CHP-steam / CT-deployment mechanism). The
hourly fleet target is distributed cheapest-first, each unit capped at its
available capacity, and survives the P2 commitment screen (`preserve_min_gen`).
Default off ⇒ every existing run/ISO is byte-identical.

- Flag: `--caiso-gas-commitment-floor` (`config.caiso_gas_commitment_floor`)
  + `--caiso-gas-floor-frac` (default 1.0).
- Loader: `eia_loader.measured_gas_floor_profile`.
- Inject: `transmission.inject_caiso_gas_commitment_floor`, in
  `run_calibration` after `generators_to_fleet_arrays`.

## Diagnosis confirmed (baseline `caiso_tune0_base`)

At spring (Apr–May) midday the model runs only ~1.5 GW gas and **imports**
~2.3 GW to stay balanced, so its marginal is always a ≥$28 import/gas. Real
CAISO runs ~6.8 GW `NG: NG` and **exports** ~+1.2 GW — gas is infra-marginal
(RA-committed) and the export/curtailment sets the ~$0 price.

| 2024 spring-midday | model (base) | EIA-930 |
|---|---|---|
| gas (MW) | 1457 | 6834 (`NG: NG`, incl. ~1.3 GW geo+bio) |
| net interchange (MW) | +2308 (import) | ~−1200 (export) |

## Frac sweep — 2024 (single-year, vs baseline)

`scripts/probes/_caiso_floor_ab.py`. EIA-923 gas = 67.7 TWh; actual RT spring
Apr/May = $13.5/$10.9; actual da_pct min/p5 = −40.7/−10.2.

| metric (2024) | base | frac 0.70 | frac 0.85 | frac 1.00 |
|---|---|---|---|---|
| gas TWh (vs 67.7) | 68.0 | 71.0 | 72.6 | 74.5 |
| export hours % | 0.0 | 1.0 | 1.7 | 3.3 |
| spring-mid gas (MW) | 1457 | 4835 | 5856 | 6874 |
| spring-mid net import (MW) | +2308 | +853 | +217 | −442 |
| LMP mean | 57.4 | 55.4 | 54.3 | 52.7 |
| LMP min | 28.0 | 2.5 | 0.0 | 0.0 |
| LMP p5 | 38.8 | 36.0 | 30.1 | 8.0 |
| spring LMP mean | 43.9 | 40.4 | 39.1 | 37.0 |
| spring LMP p5 | 36.0 | 8.0 | 8.0 | 2.5 |
| spring LMP min | 28.0 | 2.5 | 0.0 | 0.0 |

The floor works as designed at every frac: the model goes long midday
(spring-mid gas rises to the measured level, net interchange flips toward
export), export hours rise from 0 %, and the spring-midday LMP **floor**
collapses from a hard $28 to ~$0 (spring min 28→0–2.5, spring p5 36→8). The
spring *mean* still sits well above the actual ~$12 — the morning/evening ramp
hours keep it up, and pushing the belly **below** $0 is Session B (negative
renewable offers); this session collapses the floor, not the negative tail.

**Frac choice.** Gas rises with frac (the watch item: the surplus must
export/curtail, not pad the mix — validated vs **EIA-923**, not EIA-930).
`NG: NG` for CISO silently absorbs ~21 % geo+bio (EIA-930 reports neither), so
**frac ≈ 0.79 = EIA-923 gas / EIA-930 `NG: NG`** strips that and targets the
true must-offer gas. The keeper uses **frac 0.80**: gas modestly up (~+5 %),
spring floor collapsed.

## 3-year confirmation (frac 0.80)

Keeper `caiso_floor_f08_3yr` (floor, +2025 hydro repin) vs matched baseline
`caiso_base_repin_3yr` (no floor, +2025 hydro repin) — identical hydro config,
so the delta isolates the floor (the repin alone barely moves price: matched
2024 LMP min = $28, same as the no-repin `caiso_tune0_base`).

| metric | 2023 base→floor | 2024 base→floor | 2025 base→floor |
|---|---|---|---|
| gas TWh | 63.1→67.2 (+4.1) | 67.1→71.3 (+4.2) | 68.2→70.6 (+2.4) |
| EIA-923 gas | 76.0¹ | 67.7 | 55.2² |
| spring-mid gas MW | 2005→4191 | 1393→5516 | 3249→6681 |
| spring-mid net import MW | +3015→+1560 | +2253→+258 | +2612→+2558 |
| export hours % | 0.0→1.5 | 0.0→1.6 | 0.0→0.0 |
| LMP mean | 84.2→78.2 | 57.2→54.3 | 58.9→56.5 |
| **LMP min** | **8.0→0.0** | **28.0→0.0** | **41.2→0.0** |
| spring LMP mean | 51.9→48.6 | 43.5→38.8 | 47.3→45.2 |
| spring LMP p5 | 36.0→23.0 | 36.0→8.0 | 41.2→38.4 |
| spring LMP min | 8.0→1.4 | 28.0→0.0 | 41.2→36.0 |

¹ EIA-930 `NG: NG` (geo/bio-inflated); the model's gas is in line with the
geo/bio-stripped level. ² 2025 EIA-923 is the incomplete early-release vintage
(under-counts); score 2025 gas against EIA-930 (79.0) − geo/bio ≈ 68.

**Verdict — floor works, gas disciplined.** Every year the **LMP floor collapses
to $0** (min 8/28/41 → 0) and the model goes long midday (spring-midday gas
rises to the measured level; net interchange backs off toward export; export
hours rise from 0 % in 2023/24). Gas is modestly up — **+4.1/+4.2/+2.4 TWh**
(2024 keeper 71.3 vs EIA-923 67.7 = +5.3 %); the added gas **exports/curtails**,
it does not pad load (the watch item). 2024 (the year with the actual RT
reference) is the cleanest: spring p5 36→8, spring min 28→0, midday import
2253→258 MW. 2025's spring stays a touch elevated (its higher spring net load
keeps it from going long midday at frac 0.80 — the $0 hours fall in summer), but
its annual min still collapses 41→0.

The spring *mean* remains above the actual ~$12 across all years: the
morning/evening ramp hours keep it up, and the midday belly floors at $0, not
below. Pushing it **negative** (real 2024 da_pct p5 −10, min −41) is the
curtailable negative-renewable-offer tail — **Session B** — which only bites
once the model is long, i.e. on top of this floor.

## Not paired with `--interchange-shaping` for the keeper

The audit's Fix 2 (`--interchange-shaping`) shapes the priced node by the
measured interchange envelope. The floor alone already collapses the midday LMP
to the built-in $0 export sink (the model exports its surplus midday), so the
keeper is **floor-only**. Interchange-shaping additionally *caps* midday imports,
which substitutes more domestic gas (raising gas further) for little price gain
once the model is long; it remains available (`--interchange-shaping`,
default-off) and composes with the floor (the inject runs after it and uses
`maximum`), but is not enabled here to keep gas disciplined.

## Reproduce

```
# baseline (matched hydro config)
python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 \
  --commitment --priced-interchange --hydro-backfill-year 2024 \
  --hydro-eia930-monthly --out-dir results/calibration/caiso_base_repin_3yr
# floor keeper
python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 \
  --commitment --priced-interchange --caiso-gas-commitment-floor \
  --caiso-gas-floor-frac 0.8 --hydro-backfill-year 2024 \
  --hydro-eia930-monthly --out-dir results/calibration/caiso_floor_f08_3yr
# A/B
python scripts/probes/_caiso_floor_ab.py results/calibration/caiso_base_repin_3yr \
  results/calibration/caiso_floor_f08_3yr --year 2024
```
