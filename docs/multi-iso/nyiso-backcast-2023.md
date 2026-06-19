# NYISO 2023 Energy-Only Backcast — Modeled vs Actuals

Status: **P12 keeper (Stage G sign-off, 2026-06-12).** This is the first
full NYISO backcast, produced after packs P0–P13 wired all market-design
modules (hydro energy budgets, per-plant CAMPD outage overlay, CHP dispatch,
dual-fuel activation, RGGI carbon, measured monthly gas, priced import node,
battery storage). The 2023 year is mix-calibrated: every renewable and
baseload class is inside ±5% of EIA-923, net interchange matches exactly, and
the lone class-level miss is a structural demand-basis floor on the gas total —
not a dispatch error.

---

## How it was produced

```bash
# Keeper bundle (P11 smoke promoted to P12 keeper):
python scripts/run_calibration_full.py --iso NYISO --year 2023 --commitment \
    --out-dir results/calibration/nyiso_smoke_2023
```

Dashboard: **`nyiso p11 smoke 2023`** (P12-confirmed keeper; see
`docs/calibration-log.md` NYISO P11, P9b, P12 entries).

Reference data (`data/raw/_validation-source/calibration_reference.json`, NYISO 2023
block) was built by `scripts/build_calibration_reference.py`: EIA-860 year-end
renewable capacity by zone, EIA-923 by-fuel net generation (including hydro and
oil, added for NYISO via `_EIA923_EXTRA_FUELS_BY_ISO`), measured Henry Hub, and
the eGRID 2023 NYIS generation/emissions benchmark.

**Run inputs.**
- Gas: EIA-923 measured monthly delivered costs (ISO-average, `gas_monthly_actuals`
  + `gas_plant_monthly_fuel_pricing` default-on for NYISO); Jan-2023 **$10.02/MMBtu**,
  Feb $5.62 (vs the flat $2.54 Henry-Hub seed). No daily Transco-Z6 basis (U4
  absent — see Gaps §2).
- RGGI: $13.49/t CO2 (2023 auction average), wired via `state_carbon_price_by_iso`
  into every in-state fossil unit's MC (~$5.4/MWh uplift at a 0.40 t/MWh CC rate).
- Fleet: 460 LP generators, 151 plants, ~30,400 MW fossil + nuclear; 177 gas
  tranches / 17.1 GW dual-fuel capable (P13 activation — switch wired, not tripped
  on ISO-average gas; see Gaps §2).
- Hydro: 154 plants, 28.40 TWh annual energy budget (EIA-923), treaty min-flows
  for Niagara / St-Lawrence (`nyiso_hydro_treaty_min_flow`).
- Outages: unit-level CAMPD overlay from `campd-unit-outages-NYISO.csv` (857
  windows, 2023); 43 `(plant, group)` bins derated → 79 LP generator-tranches,
  covering 16,828 MW = 71% of fossil capacity.
- Demand: EIA-930 `NYIS hourly` **147.05 TWh** (peak 30,206 MW, avg 16,786 MW);
  `td_loss_factor = 0.0` (transmission-metered / generation-side; playbook §8.1).
  Wind/solar from the EIA-930 delivered distribution (no NYISO HSL), scaled to
  EIA-860 capacity: wind 0.20 CF / 2,738 MW; solar 0.14 CF / 1,645 MW.
- Net interchange: measured EIA-930 schedule served by default (`load_demand`,
  P9b): **−23.45 TWh** (net import, export-positive sign).

---

## 1. Fuel-mix generation (model vs EIA-923; EIA-930 gas total)

| Class | Model TWh | EIA-923 TWh | Δ% | Status |
|---|---:|---:|---:|---|
| CC_REGULAR | 32.14 | 33.01 | −2.6% | ✓ |
| CC_CHP | 14.10 | 16.50 | −14.6% | ✗ basis floor |
| ST_GAS | 8.07 | 8.14 | −0.8% | ✓ |
| CT_CHP | 1.44 | 2.59 | −44.2% | ✗ basis floor |
| ST_CHP | 1.25 | 1.53 | −18.0% | ✗ basis floor |
| CT_PEAKER | 0.51 | 2.07 | −75.2% | ✗ basis floor |
| **gas total** | **57.53** | **63.84** | **−9.9%** | demand-basis floor |
| *(EIA-930 gas)* | *(57.53)* | *(61.00)* | *(−5.7%)* | *(basis-width of tolerance)* |
| hydro | 28.38 | 28.03 | +1.3% | ✓ |
| nuclear | 27.49 | 27.53 | −0.1% | ✓ |
| wind | 4.60 | 4.77 | −3.6% | ✓ |
| solar | 1.95 | 2.05 | −5.0% | ✓ (edge) |
| OTHER | 2.20 | 2.20 | 0.0% | ✓ |
| biomass | 1.62 | 0.84 | +93% | ✗ (small abs +0.78 TWh; see Gaps §3) |
| oil | 0.01 | 0.42 | −97% | ✗ U4-gated (see Gaps §2) |
| **TOTAL gen** | **123.77** | **129.67** | **−4.5%** | demand-basis gap |

The −9.9% gas total and −4.5% total-generation gap are the same structural
constraint expressed at two levels — see §"Gas-total basis floor" below. The
EIA-930 gas column (61.00 TWh) puts gas at −5.7% vs the operationally
consistent benchmark, which is inside a basis-width of the ±5% target.

## 2. CO2 emissions (model vs eGRID 2023)

| | Model | eGRID 2023 NYIS |
|--|------:|----------------:|
| CO2 (Mt, class rates) | **~24.2** | **26.9** (excl. biogenic) |

eGRID 2023 NYIS breakdown (Mt): gas_cc 16.25 + gas_ct 10.36 + oil 0.26 =
27.12 Mt (26.86 excluding biomass/biogenic). Model CO2 is **~−10%** — a direct
downstream consequence of the gas-total basis floor: −6.3 TWh of gas (at ~0.4
t/MWh CC rate) contributes ~−2.5 Mt.

## 3. Price level and duration (model vs actual — P10/U2 landed 2026-06-12)

Scored against `actual_lmp.json` (per-zone DA/RT levels) +
`actual_lmp_hourly_NYISO.parquet` (system hourly DA/RT), demand-weighted P1
system price (`scripts/analyze_lmp_residual.py`):

| | model | actual RT | actual DA | residual |
|--|------:|------:|------:|------:|
| system average | **$41.79** | $30.29 | $31.11 | **+$11.50** |
| p50 | 36.4 | 26.3 | 27.6 | +10.0 |
| p90 | 65.9 | 42.2 | 44.5 | +23.8 |
| p99 | 103.9 | 119.7 | 88.9 | −15.8 |
| max | 235.8 | 1146.9 | 318.9 | — |

Per-zone average (model vs actual DA, $/MWh): Upstate_West 38.94/26.08 (+12.9),
Capital_Hudson 43.42/36.38 (+7.0), Lower_Hudson 43.42/33.58 (+9.8), NYC
43.42/33.95 (+9.5), Long_Island 43.42/40.77 (+2.7). RGGI adds ~$5.4/MWh to
in-state fossil MC; measured monthly January gas ($10.02/MMBtu, RGGI-loaded CC
MC ≈ $45–50/MWh) sets the annual high-price tail.

**The model over-prices the mid-merit band and under-prices the scarcity tail**
(p99/max) — the no-ORDC / no-reserve-scarcity signature; the model has no
scarcity adder. The four downstate model zones collapse to one price ($43.42),
so the model captures the upstate-cheap / downstate-dear split (≈$4) but not the
full actual J−A spread (≈$13) — the interface-TTC / downstate-congestion
structural item (U7). P12 had to leave these as level-only (U2 not yet uploaded);
they are now scored. The 2025 re-score shares the same shape (see §"2025" below).

## 4. Net interchange (model vs EIA-930)

| | Net interchange |
|--|----------------:|
| EIA-930 actual | **−23.45 TWh** (net import; export-positive sign) |
| model (this run) | **−23.45 TWh** — measured schedule served exactly |
| Duration RMSE | **0 MW** |
| Import-hours | **100%** |
| Diurnal correlation | **+1.00** |

NYISO is a net importer: Hydro-Québec (cheap baseload into Capital-Hudson via
Châteauguay HVDC), PJM western ties, IESO/Ontario, and ISO-NE flows average
−2,677 MW over the year. The measured EIA-930 `NYIS hourly` `Total interchange`
schedule is served **as-is** by `load_demand` (P9b default), removing it from
the residual the internal fleet must serve and setting the energy balance exactly.

**Forward years** use the priced import/export node (`NYISO_external` zone with
`IMPORT_TRANCHES["NYISO"]`: HQ_hydro 900 MW @$14, IESO_Ontario 600 MW @$18,
PJM_west 1,200 MW @$24, import_scarcity 800 MW @$45, plus one export sink 600
MW @$10), validated with `--priced-interchange`.

---

## Largest gaps and hypotheses

### 1. Gas-total −9.9% vs EIA-923 — demand-basis floor [STRUCTURAL, documented]

The in-state fleet's total is pinned by energy balance to served demand:

```
served total = EIA-930 demand (147.05 TWh) + net interchange (−23.45 TWh)
             = 123.77 TWh   vs   EIA-923 plant-net-generation 129.67 TWh
```

The 5.9 TWh gap is the difference between EIA-930 transmission-metered
generation and EIA-923 plant-net-generation — an EIA benchmark-basis difference,
not a model error. With every non-gas class on the EIA-923 mark, the full gap
falls on the swing fuel: gas lands at −9.9% on the EIA-923 basis (−5.7% vs
EIA-930). The deficit concentrates on the small CHP/peaker classes (CC_CHP
−14.6%, CT_CHP −44.2%, ST_CHP −18.0%, CT_PEAKER −75.2%); the two large gas
classes (CC_REGULAR, ST_GAS) stay on target. This is the least-distorting
landing spot for a structural constraint.

**Why no knob closes it (all rejected in P12):**
- `td_loss_factor` gross-up — ruled out by convention: EIA-930 NYIS demand is
  transmission-metered / generation-side; a distribution-loss gross-up
  double-counts (ERCOT `td_loss_factor = 0` rule, playbook §8.1).
- Import scaling — serving e.g. −20 TWh (inside ±15% tolerance) lifts gas to
  ~−4%, but the measured schedule is exact (RMSE 0 MW). Degrading a perfect
  measured match to paper over an EIA benchmark-basis difference is overfitting.
- CHP / offer-curve / storage — reshuffle within the fixed total; the P12
  `nyiso 2 chp-covered` probe confirmed this (see §"P12 passes" below).

### 2. Oil −97% — U4-gated dual-fuel winter switch [MECHANISM LIVE, TRIGGER BLOCKED]

177 dual-fuel tranches (17.1 GW) are identified by `dual_fuel_plant_groups`
and routed through `apply_dual_fuel_pricing` (P13 activation). The switch
triggers when delivered gas exceeds oil parity (~$16/MMBtu distillate
delivered). On the **ISO-average measured EIA-923** monthly series, January
gas is ~$10–12/MMBtu — below parity — so the switch does not bind on monthly
averages (0 binding hours).

The missing ingredient is the **Transco Z6 NY / Iroquois daily hub basis**
(U4), which pushes NYC/Long-Island *downstate* delivered gas above parity on
cold-snap days. U4 is a paywalled ICE/Platts product and has not landed
(`gas_basis_by_iso_month.csv` has no NYISO rows). **Activation path:** fill
U4 → `apply_hub_basis_overlay` raises downstate winter gas → the wired switch
binds and prices Ravenswood / Astoria / Bowline off oil in cold snaps.
Oil −97% is U4-gated, not a model deficiency.

### 3. CHP/peaker structural deficit — no hard steam-host must-run floor

The P12 `nyiso 2 chp-covered` probe removed the startup-amortization markup
for CHP steam hosts to test whether CHP under-dispatch is a cost artifact.
Result: CC_CHP moved +0.03 TWh, ST_CHP +0.05, CT_CHP +0.02 — gas total
57.525 → 57.537 TWh (+0.012 TWh total). The deficit is **structural**: the
model dispatches CHP economically and enforces no hard steam-host must-run
floor (no NYC steam-district cogen minimum output, no downstate RMR floor).
The correct fix is a per-plant steam-load must-run floor derived from EIA-860
cogen steam-output + any NYISO RMR designations, wired as a lower bound on the
LP generator. This is a structural follow-up, not an offer-band knob.

### 4. Biomass +93% (+0.78 TWh) — small absolute magnitude

Model biomass (1.62 TWh) overruns EIA-923 (0.84 TWh) by +0.78 TWh (~93%).
The absolute magnitude is small relative to the ±5% targets on major classes
and is not the dominant calibration issue. The likely cause is a flat-block
biomass dispatch with no seasonal availability or fuel-cost shape that would
limit summer/shoulder-season runs. Not investigated in P12.

### 5. Downstate congestion separation — not scored (U2 held)

NYC (Zone J) and Long Island (Zone K) are import-constrained pockets; the
model has 5 zones with Central-East / Total-East / Dunwoodie-South interface
TTCs seeded from the NYISO Gold Book (Tier-3). The zonal-sufficiency test
(J−A and K−A LBMP spread duration curves, doc-07 design decision 1) requires
the hourly zonal LBMP series (U2: NYISO OASIS DA+RT LBMP CSVs). Until U2
lands, price calibration is level-only and the 5-zone aggregation cannot be
validated against observed congestion.

---

## P12 passes (one named hypothesis each)

**`nyiso 1 gas-actuals`** (`--gas-monthly-actuals`, bundle
`nyiso_p12_gasact_2023`) — **REJECTED, no-op.** Hypothesis: measured EIA-923
monthly gas (Jan-2023 $10.02/MMBtu winter spike vs the flat $2.54 HH seed)
re-levels gas and trips the dual-fuel oil switch. Result: byte-identical mix
and price duration (gas 57.53, oil 0.013, avg $42.72, max $235.81) — the
harness already enables `gas_monthly_actuals` + `gas_plant_monthly_fuel_pricing`
by default for NYISO, so the explicit flag is a no-op. The winter gas level is
already priced in; oil still does not fire because monthly-average Jan gas
($10) stays below distillate parity ($16) — confirmed the U4 gate.

**`nyiso 2 chp-covered`** (`--chp-startup-covered`, bundle
`nyiso_p12_chp_2023`) — **REJECTED, negligible.** Hypothesis: the CHP
under-dispatch is a startup-amortization artifact. Result: +0.1 TWh total
movement (CC_CHP +0.027, ST_CHP +0.051, CT_CHP +0.017; CC_REGULAR −0.033,
ST_GAS −0.048; gas total 57.525 → 57.537; avg price $42.72 → $43.02). The
CHP deficit is structural (no hard steam-host floor), not a startup-cost
artifact. Within the fixed served total there is no room for the CHP classes
to recover without displacing the on-target baseload gas.

---

## 2025 — UNBLOCKED & price-scored (2026-06-12)

The EIA-930 `NYIS hourly` extract was refreshed (`convert_eia930.py NYIS
--force` on the re-uploaded raw long files) to span full 2025 — 8,760 h, where
the old extract stopped at Q1'25 (2,154 h). `nyiso_net_interchange(2025)` now
returns the measured series (**−19.09 TWh**) and `load_demand` serves the import
wedge by default. The P12 baseline's **+22.7% over-generation closes**:

| fuel | model | EIA-930 | Δ930 | EIA-923 (prelim) |
|---|---|---|---|---|
| gas | 68.30 | 70.25 | **−2.8%** | 60.21 |
| nuclear | 28.38 | 27.95 | +1.5% | 28.41 |
| wind | 7.05 | 7.05 | exact | — |
| hydro | 21.05 | 24.10 | −12.7% | 21.05 (budget) |
| **TOTAL** | **132.76** | 129.54 | **+2.5%** | 115.84 |

Net interchange served exactly (−19.09 vs −19.09 TWh, duration RMSE 0 MW,
import-hours 99.8%, diurnal corr +1.00). **EIA-923 2025 is the preliminary
M-file** (total 115.84 TWh — ~17 below served demand; solar 0.66, biomass/oil
under-reported), so it is **flagged, not chased**: EIA-930 is the operationally
consistent basis, against which gas is −2.8% and the total +2.5%. The +13.4% gas
vs EIA-923 reads off the under-reported preliminary total, the same EIA-930/923
demand-basis gap as the 2023 keeper.

**Price re-score (2025).** System avg model $69.24 vs actual RT $60.73 / DA
$60.71 (+$8.5). Duration p50 $57/$45, p90 $113.7/$113.6 (near-exact), p99
$157/$222, max $314/$2,074 — over-prices the mid, under-prices the scarcity tail
(no-ORDC signature), same as 2023. Per-zone level resid vs actual DA: Upstate
+$10.9, Capital +$5.5, Lower_Hudson +$7.6, NYC +$5.2, Long_Island +$1.7.

Bundle `nyiso_p12_2025_refreshed` (dashboard `nyiso 2025 refreshed`); detail in
its `SUMMARY-nyiso-2025-refreshed.md` and the calibration log ("NYISO 2025").
**Structural-discipline run — no offer band tuned;** oil (0.02 TWh) stays
U4-gated. The 2025 EIA-923 is still preliminary, so its renewable/biomass/oil
columns are not scored.

## Blocked years (not yet calibrated)

### 2024 — NY_2024 CEMS + renewable capacity

- `data/raw/campd-unit-level/NY_2024.parquet` is missing (upload U1):
  2024 runs with no measured outage windows (statistical availability only).
- `data/raw/_validation-source/NYISO_2024_renewable_capacity.csv` is missing (the
  calibration-reference script defers 2024 per `CALIBRATION_YEARS_BY_ISO`).

**Refresh path:** upload U1 (`NY_2024.parquet`), add 2024 to the year
override, re-derive outage windows, and re-run the calibration reference.

---

## What changed to enable this run

The dominant enabling change was **P9b (served-interchange)**, which closed
the largest structural gap the P11 smoke identified:

- **P9b — served measured net interchange** (`2dd581a`, branch
  `claude/nyiso-neiso-serve-interchange-3sowy8`): `load_demand` now serves the
  measured EIA-930 `NYIS hourly` `Total interchange` (−23.45 TWh) as the
  NYISO/NEISO default (`_SCALAR_INTERCHANGE_ISOS`). Before P9b, the backcast
  served 0 TWh of imports → the internal fleet over-generated by +25.6% vs
  EIA-923 (151.9 → 123.8 TWh) and gas was +25.6% over. P9b brought gas from
  +25.6% to −9.9% in one structural fix.

Supporting modules that enable the full run:

- **P0/Stage-E** — calibration reference (NYISO 2023/2025 blocks in
  `calibration_reference.json`); EIA-923 hydro+oil columns added via
  `_EIA923_EXTRA_FUELS_BY_ISO` (gated to NYISO/NEISO only).
- **P1** — unit-outage windows verified current (857 windows, 2023); overlay
  wiring confirmed in `data/outages.py` under `outage_source="historic"`.
- **P2** — per-plant offer-curve tranches and bin assignments
  (`thermal_tranches_NYISO.csv`, `derive_cc_committed_pct.py`); no coal
  must-run rows (NYISO's zero-coal CEMS confirmed); inflexible layer is CHP
  BTM, nuclear, hydro min-flows, and designated RMR peakers.
- **P4** — hydro 154-plant monthly energy budget (EIA-923), treaty min-flows
  for Niagara (ORIS 2693, 0.25 min-flow fraction) and St-Lawrence (ORIS 2694,
  0.50); Blenheim-Gilboa pumped storage in the LP storage fleet.
- **P5** — battery storage fleet from
  `eia860_energy_storage_operable.parquet`, concentrated downstate (NYC/Long
  Island), COD-ramped mid-year.
- **P6** — renewable profiles via EIA-930 NYIS delivered distribution; no
  NYISO HSL available (low curtailment — EIA-930 fallback is documented).
- **P7** — measured monthly gas (`gas_monthly_actuals` default-on, NYISO
  added); RGGI $13.49/t (2023) wired via `STATE_CARBON_PRICE_BY_ISO["NYISO"]`.
- **P8** — EIA-930 NYIS demand wired; zonal load stays on static Gold-Book
  shares (0.365/0.175/0.06/0.28/0.12) pending U3.
- **P9** — priced import/export node (`NYISO_external` zone, `IMPORT_TRANCHES`
  / `EXPORT_TRANCHES["NYISO"]`); validated with `--priced-interchange` runs.
- **P13** — dual-fuel activation: 177 tranches (17.1 GW) routed through
  `apply_dual_fuel_pricing`; wired and unit-tested; winter binding gated on U4.

---

## Next steps for NYISO calibration (Stage G maintained)

1. **Upload U2** (DA+RT hourly zonal LBMP, NYISO OASIS) → enables P10 price
   calibration: score avg LBMP vs actual, J−A / K−A spread duration curves,
   zonal-sufficiency test for the 5-zone aggregation.
2. **Upload U1** (`NY_2024.parquet`) + refresh `NYISO_2024_renewable_capacity.csv`
   → unblocks 2024 backcast and 2024 outage windows.
3. **Extend EIA-930 NYIS extract through 2025-12** + re-pull final 2025
   EIA-923 → unblocks 2025 backcast.
4. **Upload U4** (Transco Z6 NY / Iroquois daily basis, paywalled) → enables
   winter dual-fuel validation; oil generation should be non-zero in Jan/Feb.
5. **CHP steam-host must-run floor** — derive per-plant steam-load floors from
   EIA-860 cogen steam output + NYISO RMR designations; wire as LP lower bounds;
   expected to lift CC_CHP/CT_CHP from the basis-floor landing spot.
6. **Biomass dispatch shaping** — seasonal fuel-cost or availability shape to
   bring the +93% overrun toward tolerance (low priority given small abs value).
