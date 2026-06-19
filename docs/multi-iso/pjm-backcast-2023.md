# PJM 2023 Energy-Only Backcast — Modeled vs Actuals

Status: **first PJM backcast** (Stage G, energy-only). This is the first
non-ERCOT ISO run through the calibration harness. It exercises the generic
dispatch LP and comparison on PJM's 4-zone topology, reusing the ERCOT
machinery and stubbing the ERCOT-only steps (NP6 HSL, coal must-run tuning,
plant-level/CHP/CAMPD diagnostics). The point is to locate the largest gaps and
their causes before any PJM-specific tuning — not to declare PJM calibrated.

> **Update (2026-06-04).** The fuel-mix and price tables below are the
> *original energy-only stub* run (aggregated fleet, single gas-basis scalar,
> no PJM outages). Since then the PJM backcast binds to real per-plant data —
> a per-plant EIA-860 fleet (`plant_level_fleet`), per-plant EIA-923 monthly
> gas/coal/oil costs with a state→zone "nearby plant" fallback
> (`nearby_fuel_price_fallback`), and a CAMPD historic-outage overlay
> (`campd-outages-PJM.csv`). This directly attacks gaps #2a (gas basis) and
> #2b (coal availability) below: in a 2024 re-run the outage overlay zeroes
> 233 coal/CC tranches and modeled coal falls toward the actuals. Numbers here
> will be refreshed once the missing PJM coal-state CAMPD extracts (OH, WV, IN,
> KY, VA) are loaded — today those states keep statistical availability, so the
> overlay covers only PA/NJ/MD/DE/IL. Capacity-payment economics (Module M1)
> are also now wired for multi-year runs (net-CONE × UCAP), though they do not
> affect this single-year dispatch.

## How it was produced

```
# Canonical bundle (dispatch + system prices + EIA-930 benchmark):
python scripts/run_calibration_full.py --iso PJM --year 2023 \
    --out-dir results/calibration/pjm_2023

# Same solve through the generic comparison harness (fuel mix, CO2, prices):
python scripts/run_calibration.py --iso PJM --year 2023
```

Reference data (`data/raw/_validation-source/calibration_reference.json`, PJM block) was
built by `scripts/build_calibration_reference.py` (now PJM-aware):
EIA-860 year-end renewable capacity by zone, EIA-923 by-fuel net generation,
measured Henry Hub, and the eGRID 2023 PJM generation/emissions benchmark.

**Run inputs.** Henry Hub $2.54/MMBtu + PJM gas basis **+0.30** (= $2.84
delivered; `GAS_BASIS_DIFFERENTIAL["PJM"]`, Tier 3 — verify); coal base
$2.30/MMBtu; EIA-860 2023 fleet (1,943 generators across 4 PJM zones); demand
**783.2 TWh** (peak 147.6 GW, avg 89.4 GW, min 36.4 GW). Wind/solar hourly
shape from the EIA-930 delivered distribution (no PJM HSL), scaled to physical
capacity factors wind 0.31 / solar 0.19.

---

## 1. Fuel-mix generation (model vs EIA-930 vs EIA-923)

| Fuel    | Model TWh | Model % | EIA-930 TWh | 930 % | EIA-923 TWh | 923 % |
|---------|----------:|--------:|------------:|------:|------------:|------:|
| coal    |   177.8   |  22.7   |   121.0     | 14.9  |   113.6     | 14.2  |
| gas     |   290.2   |  37.0   |   361.0     | 44.4  |   373.8     | 46.6  |
| nuclear |   272.1   |  34.7   |   273.8     | 33.7  |   272.6     | 34.0  |
| wind    |    29.6   |   3.8   |    29.6     |  3.6  |    28.5     |  3.5  |
| solar   |    14.1   |   1.8   |     9.0     |  1.1  |    14.3     |  1.8  |
| hydro   |     —     |   —     |    15.5     |  1.9  |     —       |  —    |
| oil     |     0.0   |   —     |     2.7     |  0.3  |     —       |  —    |
| **TOTAL** | **784.0** |     | **812.6**   |       | **802.7**   |       |

Gas detail vs EIA-923: combined cycle 288.8 TWh (−14% vs 336.1), combustion
turbine 1.4 TWh (−95% vs 25.5), gas steam 0.0 TWh (−100% vs 12.2).

## 2. CO2 emissions (model vs eGRID PJM)

| | Model | eGRID 2023 PJM |
|--|------:|---------------:|
| CO2 (Mt) | **296.0** | **267.3** |

eGRID by fuel (Mt): coal 114.2, gas-CC 124.6, gas-CT 21.7, oil 2.6, biomass
3.8. Model is **+10.7%** high — a direct consequence of the coal over-dispatch
in §1 (PJM coal emits ~1.0 t/MWh; +57 TWh of extra coal ≈ +57 Mt, partly offset
by the gas under-dispatch).

## 3. Price level and duration (model)

| | $/MWh |
|--|------:|
| system average | **25.4** |
| max / p90 / p50 / p10 / min | 41.0 / 29.6 / 25.3 / 20.7 / −26.0 |
| negative-price hours | 23 |

PJM 2023 actual real-time load-weighted LMP was **≈ $30/MWh** (PJM IMM 2023
State of the Market). The model runs **~15% low**. (No hourly actual LMP series
is in the repo, so only the level and the modeled duration shape are reported;
an hourly PJM LMP upload would let us overlay the full duration curve.)

## 4. Net interchange (model vs EIA-930)

| | Net interchange |
|--|----------------:|
| EIA-930 actual | **+40.0 TWh** net export (+4,564 MW avg) |
| model (this stub run) | **0.0 TWh** (energy-only; no external node) |
| model (since 2026-06-05, M4) | **+40.0 TWh** — measured tie-line schedule |

EIA sign convention: positive = net export. PJM was a large **net exporter** in
2023 (to MISO, NYISO, the Carolinas, TVA). The energy-only LP served only
internal demand (783 TWh), so this stub run could not generate the ~40 TWh PJM
actually exported — at the time, the single biggest structural gap.

**Closed since.** Backcasts serve the *measured* hourly tie-line net export
(`eia_loader.pjm_net_interchange`, attributed per border zone by
`pjm_zonal_interchange`) on top of internal load — the pjm-6 baseline serves
823 TWh and matches the EIA-930 figure exactly. Forward years (no measured
file) are served by the **priced import/export node** (J1, 2026-06-11): a
`PJM_external` zone holding two scarcity import tranches (4 GW @ $46/$60) and
six export sinks (9.8 GW @ $18–42), fitted to the measured 2023
net-interchange duration curve (`scripts/derive_import_tranches.py`;
validation run `results/calibration/pjm_j1_priced` via
`run_calibration_full.py --priced-interchange`).

---

## Largest gaps and hypotheses

Ordered by magnitude. As anticipated, **net interchange** and **gas basis** are
the top two.

1. **Net interchange — model 0 vs +40 TWh actual export (structural).
   [RESOLVED]** The energy-only LP balanced PJM-internal supply to PJM demand
   only. Actual PJM net generation (≈813 TWh) exceeds demand (783 TWh) by the
   export volume plus losses, so the model under-generated by ~the export and
   mis-attributed the shortfall: the marginal export energy is gas, so the
   *real* fleet burns more gas than the model. **Fixed twice over** (see §4):
   backcasts serve the measured tie-line schedule (M4, 2026-06-05); forward
   scenarios get the price-responsive `PJM_external` node (J1, 2026-06-11),
   the generalized CAISO-WECC-node machinery.

2. **Coal +57 TWh / gas −70-to-84 TWh — merit-order inversion.**
   The model baseloads coal ahead of combined cycle; PJM 2023 did the opposite
   (heavy coal-to-gas switching on cheap Marcellus gas, low coal capacity
   factors, retirements). Two compounding causes:
   - **Gas basis (Tier 3 data gap).** PJM gas cost is a single +0.30 $/MMBtu
     scalar that collapses three hubs with opposite signs — the TETCO M3 /
     Transco Z6 eastern *premium* and the Dominion South Marcellus *discount* —
     with strong winter seasonality. A generation-weighted monthly basis would
     change which gas units beat coal in the merit order. This is the highest-
     value PJM parameter to refine.
   - **Coal availability/economics.** PJM coal runs with statistical
     availability and a flat $2.30 base price and *no* PJM historic-outage
     overlay or must-run/retirement modeling (those are ERCOT-only today), so
     it clears far more than its real ~40% capacity factor. The CT/ST gas tail
     (−95% / −100%) is the mirror image: cheap baseload coal plus the low price
     level means peakers never clear.

3. **Price level ~15% low — follows from (2).** Cheap, over-dispatched coal
   sets the marginal price in too many hours. Correcting the gas basis and coal
   economics in (2) should lift the system average toward the ~$30 actual.

4. **CO2 +10.7% high — follows from (2).** The coal over-dispatch is
   CO2-intensive; the gas under-dispatch only partly offsets it.

5. **Hydro (15.5 TWh) and oil (2.7 TWh) not represented.** PJM hydro (~1.9% of
   generation) is not dispatched (the flat-block hydro and energy-budget module
   is pending — doc 02 §6), and oil peakers never clear at this price level.
   Small relative to (1)-(2).

6. **Solar benchmark gap, not a model error.** Model solar (14.1 TWh) matches
   EIA-923 (14.3 TWh) — validating the chosen 0.19 capacity factor — but
   exceeds the EIA-930 hourly series (9.0 TWh). EIA-930 `NG: SUN` under-reports
   PJM utility solar; the EIA-930 distribution still supplies the hour-to-hour
   shape. Read the EIA-930 column as the conservative bound.

---

## What changed to enable this run

- `scripts/build_calibration_reference.py` — PJM added to `CALIBRATION_ISOS`
  and the BA-code maps (PJM→PJM for eGRID and EIA-923). All per-ISO-year
  derivation (EIA-860 zonal capacity, EIA-923 by-fuel, eGRID benchmark) was
  already generic on zone topology. ERCOT outputs are byte-identical.
- `src/market_sim/config/constants.py` — PJM entries added to
  `GAS_BASIS_DIFFERENTIAL` (+0.30, Tier 3 — verify), `COAL_PRICE_BASE` (2.30),
  and `RENEWABLE_AVG_CF` (wind 0.31 / solar 0.19), each cited inline.
- `src/market_sim/data/eia_loader.py` — `load_eia_hourly_benchmark()`, a
  generic per-BA EIA-930 benchmark loader (per-fuel net generation + net
  interchange) tolerant of a BA-year a few hours short of 8760 (PJM 2023).
- `scripts/run_calibration_full.py` — the harness now runs any ISO. ERCOT keeps
  the full plant-level diagnostic unchanged; other ISOs get a generic
  fuel-mix / price / interchange report and skip the ERCOT-only persistence and
  tables. `scripts/run_calibration.py` was already ISO-generic.

## Next steps for PJM calibration (Stage G continued)

1. ~~Add the import/export node and a 2023 net-interchange schedule (gap #1).~~
   **Done** — measured schedule for backcasts (M4) + priced node for forward
   years (J1); see §4.
2. Source a generation-weighted monthly PJM gas basis (gap #2a) to replace the
   single Tier-3 scalar.
3. Add PJM coal must-run / availability (historic-outage overlay analogue) so
   coal capacity factor matches reality (gap #2b).
4. Upload an hourly PJM LMP series to enable a true price duration-curve
   overlay (§3).
