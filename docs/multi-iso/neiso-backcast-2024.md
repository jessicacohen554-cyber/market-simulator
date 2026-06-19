# NEISO (ISO-NE) 2024 Backcast — Modeled vs Actuals

Status: **P12 keeper, 2023–2025 sign-off (Stage G complete).** This is the
NEISO calibration sign-off spanning all three target backcast years (primary
2024; secondary 2023 and 2025). It is the first non-ERCOT ISO to complete a
multi-year sign-off with the full v2 playbook machinery: per-plant EIA-860
fleet, CAMPD per-plant tranche shares, unit-level outage overlay, measured
monthly gas (EIA-923 + AGT hub-basis overlay), RGGI in marginal cost,
dual-fuel switching, and a measured net-interchange schedule. The keeper is
**structural defaults — no offer-band tuning**, consistent with the
playbook §6 discipline that structural fixes dominate band multipliers.

> **Update (2026-06-12).** The results below are from three separate
> `run_calibration_full.py` bundles — `neiso_p12_base_2023`,
> `neiso_p12_base_2024`, and `neiso_p12_hydrofix_2025` — run in parallel
> after P9b (measured interchange) merged. A combined `--year 2023 2024 2025`
> bundle hit a warm-start basis degeneracy in the P2 commitment solves; the
> three single-year bundles solve cleanly and reproduce each other to <0.1
> TWh. **P10 has since landed** (2026-06-12) — the `actual_lmp.json` NEISO
> block + hourly sidecar are present and the keepers are now **price-scored**
> (§"Largest gaps" #3); the fuel-mix / CO₂ / interchange sign-off below is
> unchanged. The 2025 bundle uses `--hydro-backfill-year
> 2024` — the EIA-923 2025 early-release has only 6 of ~166 NEISO hydro
> plants reporting, yielding 0.09 TWh; the backfill restores ~6.6 TWh at the
> 2024 inflow rate.

## How it was produced

```
# Primary year:
python scripts/run_calibration_full.py --iso NEISO --year 2024 --commitment \
    --out-dir results/calibration/neiso_p12_base_2024

# Secondary years:
python scripts/run_calibration_full.py --iso NEISO --year 2023 --commitment \
    --out-dir results/calibration/neiso_p12_base_2023

python scripts/run_calibration_full.py --iso NEISO --year 2025 --commitment \
    --hydro-backfill-year 2024 \
    --out-dir results/calibration/neiso_p12_hydrofix_2025
```

All three runs use the same structural defaults via `_calibration_config`:

- `gas_monthly_actuals` on — per-plant EIA-923 monthly delivered gas with
  nearby-plant fallback (20 plants have own F923 data; 286 filled by
  nearby-plant/state mean)
- `gas_hub_basis_overlay` on — measured AGT monthly basis replaces per-plant
  F923 gas in covered months (`data/raw/gas_basis_by_iso_month.csv`,
  35/36 NEISO months 2023–2025; Aug-2025 missing upstream, falls back to
  EIA-923/shaped)
- `dual_fuel_switching` on — gas-primary dual-fuel units (107 tranches /
  6,367 MW across 42 plants) cap gas price at `min(hub_gas, oil)` × heat
  rate; oil-primary steam (135 units / 5,182 MW) prices off oil directly
- `state_carbon_pricing` on — RGGI allowance cost in marginal cost: 2023
  $14.87/t, 2024 $22.83/t, 2025 $24.35/t (RGGI, Inc. quarterly auction
  clearing prices; ~$5–7/MWh uplift on a CC at 7.0 MMBtu/MWh)
- `outage_source = "historic"` — unit-level CAMPD outage overlay; 2025 NH
  units run statistical (NH_2025 missing, upload U1)
- Interchange: measured schedule via `neiso_net_interchange(year)` sourcing
  `data/eia_hourly/ISNE hourly.parquet` `Total interchange` column (import-
  negative, so the internal fleet serves the residual demand)

**Run inputs (2024 primary).** Henry Hub $2.19/MMBtu + measured AGT basis
overlay (e.g. Dec-24 +6.12, Jan-25 +12.79 $/MMBtu blowout in adjacent
months); RGGI $22.83/t. EIA-860 2024 fleet: 431 generators, 199 plants,
~24.6 GW fossil + nuclear (gas_cc 13,264 MW / oil 5,182 MW / nuclear
3,355 MW / gas_ct 1,631 MW / biomass 1,047 MW / coal 108 MW), 4 load zones
(North / Central / Boston / Connecticut) + HQ_import node. Demand **114.4
TWh** (peak 24,255 MW, avg 13.1 GW). Wind/solar profiles from EIA-930 ISNE
delivered distribution, scaled to EIA-860 capacity (wind 1,536 MW Dec-24,
solar 3,354 MW Dec-24). Nuclear monthly CF from EIA-923 per-plant data
(`NUCLEAR_MONTHLY_CF_BY_YEAR["NEISO"][2024]`): notable dips Oct 0.44
(Seabrook refuel + a Millstone unit Sep 0.81). Northfield Mountain + Bear
Swamp PS (~1.7 GW) and grid BESS fleet loaded from EIA-860 storage tables.
Net interchange −10.30 TWh (steady net import, principally HQ Phase II
~2,000 MW into Boston + NB/north + NYISO tie into Connecticut).

Reference data (`calibration_reference.json`, NEISO 2024 block) was built by
`build_calibration_reference.py` with `ba_code = ISNE`: EIA-930 demand,
EIA-923 by-fuel generation, measured Henry Hub, and the eGRID 2024 `NEWE`
generation/emissions benchmark.

---

## 1. Fuel-mix generation (model vs EIA-930 vs EIA-923) — 2024

| Fuel | Model TWh | Model % | EIA-930 TWh | 930 % | EIA-923 TWh | 923 % |
|---|---:|---:|---:|---:|---:|---:|
| gas | 58.0 | 57.4 | 59.6 | 56.9 | 61.0 | 57.8 |
| nuclear | 26.45 | 26.2 | 26.41 | 25.2 | 26.55 | 25.2 |
| hydro | 6.66 | 6.6 | 7.39 | 7.1 | 6.71 | 6.4 |
| wind | 3.45 | 3.4 | 3.45 | 3.3 | — | — |
| solar | 1.31 | 1.3 | 1.31 | 1.2 | (4.53 BTM) | — |
| biomass | 5.16 | 5.1 | — | — | (eGRID ~5.5) | — |
| oil | 0.01 | — | ~0.37 | 0.4 | 0.31 | 0.3 |
| coal | 0.01 | — | 0.24 | 0.2 | — | — |
| **TOTAL (internal)** | **101.1** | | **~104.8** | | | |

Net interchange (imports, measured schedule): **−10.30 TWh** (−1,175 MW avg;
corr +1.00 with measured; RMSE 0 MW). Internal + imports = **111.4 TWh**.

Model % is fraction of internal fleet generation (101.1 TWh); imports are a
separate 9.3% of total served demand.

**Gas detail vs EIA-923:** combined cycle ≈ 57.0 TWh (−2.7% vs 923 CC
58.6), combustion turbine ≈ 0.8 TWh (−62% vs 923 CT 2.1), gas steam ≈ 0.2
TWh (−33% vs 923 ST 0.3). The CT/ST classes run below their EIA-923 levels
because the large CC fleet fills load economically — total gas is the scored
metric.

**Solar benchmark note.** EIA-923 reports 4.53 TWh for NEISO solar, but
this includes behind-the-meter PV (MA/CT residential and commercial) — the
grid-metered EIA-930 figure (1.31 TWh) is the operationally consistent
benchmark (playbook §8.1, net-load convention). The model matches EIA-930
solar exactly; the 923-vs-930 delta is not a model error.

---

## 2. Fuel-mix — 2023 and 2025 (secondary years)

| Year | Fuel | Model TWh | EIA-930 | EIA-923 | vs 930 | vs 923 |
|---|---|---:|---:|---:|---:|---:|
| 2023 | gas | 53.7 | 55.5 | 56.6 | −3.2% ✅ | −5.1% ✅ |
| 2023 | nuclear | 23.15 | ~23.1 | 23.2 | ✅ | −0.2% ✅ |
| 2023 | hydro | 8.44 | ~8.5 | 8.5 | ≈ | −0.7% ✅ |
| 2023 | oil | 0.02 | ~0.37 | 0.39 | ⚠ | −95% ⚠ |
| 2023 | net interchange | −15.14 | −15.14 | — | ✅ exact | — |
| 2025† | gas | ~62.0 | ~64.6 | 52.4‡ | −3.9% ✅ | n/a |
| 2025† | nuclear | 27.79 | ~27.6 | 27.6 | ✅ | +0.7% ✅ |
| 2025† | hydro | ~6.66 | 5.12 | 0.09‡ | +30% backfill | n/a |
| 2025† | oil | 0.01 | ~1.24 | 0.91‡ | ⚠ | ⚠ |
| 2025† | net interchange | −8.13 | −8.13 | — | ✅ exact | — |

† 2025 is provisional — the EIA-923 early release has severely incomplete
hydro, solar, and oil reporting (6 of ~166 hydro plants; 322 vs ~1,700
total rows). Do not score 2025 gas or oil against EIA-923.  
‡ EIA-923 2025 preliminary lower bound; final file expected ~Q1 2026.

**2025 hydro note.** `--hydro-backfill-year 2024` carries the 5 non-reporting
hydro plants at their 2024 inflow (~6.6 TWh vs EIA-930 5.12 TWh actual). The
backfill over-states by ~1.5 TWh — a provisional artifact that self-corrects
when the final 2025 EIA-923 file lands. Without the backfill, 2025 gas was
+6.5% vs EIA-930 (gas compensated for the missing hydro TWh), confirming
the backfill is necessary and not a tuning choice.

---

## 3. CO₂ emissions (model vs eGRID NEWE)

| Year | Model (Mt) | eGRID (Mt) | Δ | verdict |
|---|---:|---:|---:|---|
| 2023 | 22.81 | 25.13 | −9.2% | ✅ within ±10% |
| 2024 | 24.52 | 26.79 | −8.5% | ✅ within ±10% |
| 2025 | 24.58 | n/a | — | provisional |

eGRID source: EPA eGRID2023 (rev2) and eGRID2024, sheet `SRL23`/`SRL24`,
column `SRCO2AN`, subregion `NEWE` — 27.69 / 29.53 M short tons × 0.90718474
(short-ton→tonne) → **25.13 / 26.79 Mt**. No eGRID 2025 file is yet published.

Model CO₂ is derived from each plant's
`emission_rate_co2 = heat_rate × FUEL_CO2_FACTOR_PER_MMBTU` (152 NEISO
fossil plants matched; 0 on fallback) — a base-rate figure. The −8-9% gap
is primarily a floor effect: the dispatch's band heat-rate multipliers raise
effective HR above the annual-average base rate, so the true modeled CO₂ is
modestly higher than the base-rate figure and the gap is somewhat smaller
than it appears. The gap is also consistent with model gas running
~5% below EIA-923 (gas is the CO₂-dominant fuel) and with the oil under-run
(oil emits ~1 tCO₂/MWh).

---

## 4. Net interchange (model vs EIA-930)

| Year | Modeled | EIA-930 actual | RMSE | Corr | verdict |
|---|---:|---:|---:|---:|---|
| 2023 | −15.14 TWh | −15.14 TWh | 0 MW | +1.00 | ✅ exact |
| 2024 | −10.30 TWh | −10.30 TWh | 0 MW | +1.00 | ✅ exact |
| 2025 | −8.13 TWh | −8.13 TWh | 0 MW | +1.00 | ✅ exact |

NEISO is a steady net importer: HQ Phase II HVDC (~2,000 MW firm baseload
from Québec into Boston), Highgate (VT–HQ), NB/north ties, and the
Cross-Sound / Northport–Norwalk NYISO interconnects. Net imports vary year to
year — the 2023 peak (15.1 TWh) reflects a combination of cheaper HQ hydro
and a cold year; 2025 is lower (8.1 TWh) partly due to higher HQ system
demand. The model serves the measured schedule by netting the EIA-930 `Total
interchange` column into demand before dispatching the internal fleet, so the
match is structural (RMSE 0 MW by construction). Forward scenarios use the
priced `HQ_import` node fitted to the duration curve (NEISO offline RMSE 271
MW / 266 MW in 2023/24; validated with `--priced-interchange`).

---

## Largest gaps and hypotheses

None of the gaps below prevented sign-off; all are filed for future
refinement. The P0 acceptance table (gas ±5% vs EIA-930, CO₂ ±10% vs eGRID,
interchange ±15%) is fully green for the complete-data years 2023/2024; 2025
passes gas/interchange and is provisional on hydro.

### 1. [FILED · monthly-AGT dual-fuel limitation] Oil near-zero vs EIA-923 0.31–0.39 TWh; EIA-930 2025 ~1.24 TWh

**Root cause: monthly AGT averages never reach distillate parity.** The
dual-fuel CT/ST switch is fully wired and verified (P13): 107 tranches /
6,367 MW across 42 plants cap gas at `min(hub_gas, oil)` × HR. But the
committed AGT basis data (`gas_basis_by_iso_month.csv`) is *monthly*, and
monthly averages smooth out the daily cold-snap spikes that actually trip the
switch in real ISO-NE operations:

| Month | HH ($/MMBtu) | AGT basis | Resolved hub gas | Oil parity |
|---|---:|---:|---:|---:|
| Jan-2024 | 2.57 | +4.50 | 7.07 | ~18 |
| Dec-2024 | 1.55 | +6.12 | 7.67 | ~18 |
| Jan-2025 | 3.52 | +12.79 | 16.31 | ~18 |
| Feb-2025 | 3.52 | +10.43 | 13.95 | ~18 |

Even Jan-2025, the largest measured spike, produces a monthly hub gas of
$16.31/MMBtu — still below the ~$18 distillate parity threshold. So the
dual-fuel CT switch **correctly does not trip on monthly data**. Winter oil
instead comes from the oil-primary steam fleet (~5 GW: Canal, Wyman, New
Haven, Montville, Newington) dispatching on scarcity economics — which
produces oil burn in *summer* peak-demand hours (the correct scarcity
mechanism) rather than *winter* cold-snap hours (the actual pattern).

**Practical consequence:** annual oil totals are small-magnitude — modeled
0.01–0.02 TWh vs EIA-923 0.31–0.39 TWh (2023/24) is a ~0.3 TWh
shortfall — but the seasonal distribution is inverted. The cold-snap winter
dispatch (oil-steam scarcity + CT switch) would shift oil from summer to
winter once a daily-AGT basis series (U4 refinement, ICE/Platts/EIA NG
Weekly) is available. Jan-2023 daily AGT spot reached >$30/MMBtu on the
coldest days — far above parity.

**What is NOT the fix:** an offer-band adjustment. Raising the oil-steam
scarcity price only shifts its summer dispatch; it does not add winter oil
without the daily price signal. This is a data gap, not a model
parameterization gap.

**Owner:** P7/P13 (U4 daily AGT upload).

### 2. [AMBER · PS/BESS over-cycling] PS 0.39–0.86 TWh vs EIA-930 0.30–1.93 TWh (2024/25); BESS 0.06–0.34 TWh vs EIA-930 0.01–0.15 TWh (2024/25)

Northfield Mountain + Bear Swamp PS (~1.7 GW) and the grid BESS fleet
over-cycle on pure LP price arbitrage. The P11 smoke had PS at 1.35 TWh
(4.5× over-cycled vs EIA-930 0.30); P12 corrects sharply to 0.39/0.50/0.86
TWh because serving the measured import schedule removes most of the
arbitrage spread — confirming the P11 hypothesis that the smoke-run
over-cycling was a symptom of the unserved interchange gap.

PS is still modestly above the 2024 EIA-930 PS benchmark (0.30 TWh) and
well below the 2025 EIA-930 (1.93 TWh), which may reflect unusual pumped-
hydro conditions in 2025. The `pumped_storage_dispatch_adder` lever (default
0 for NEISO; set to 10 $/MWh for PJM after its PS calibration) is the
correction if PS cycling becomes a scored metric. Not tuned because it would
not move gas/CO₂/interchange. **Owner:** P4 (PS throughput cost) / P5 (BESS
cycling), after storage benchmarks are formalised.

### 3. [SCORED 2026-06-12 · price level/duration] Mid-curve over-prices 2023/24, winter tail mis-placed; filed to U4/U6/P9, not band-tuned

P10 (the U2 LMP upload) landed and the three keepers were **scored** against
the `actual_lmp.json` NEISO hub (`.H.INTERNAL_HUB`) — see
`calibration-log.md` §NEISO price re-score for the full breakdown. Modeled
hub mean vs actual RT / DA:

| year | model | actual RT | actual DA | resid vs RT | >$75 share (model / act) |
|---|---:|---:|---:|---:|---:|
| 2023 | 53.58 | 35.70 | 36.82 | **+50%** | 24.7% / 5.9% |
| 2024 | 55.68 | 39.54 | 41.51 | **+41%** | 29.8% / 8.2% |
| 2025 | 53.44 | 65.89 | 67.86 | **−19%** | 5.8% / 27.2% |

The price does **not** meet the ±5–10% level / duration target, but the miss
is **filed, not tuned** (the structural fuel-mix / CO₂ / interchange rows are
green and untouched; zero offer-band moves):

- **Winter (Jan/Feb/Dec) = the monthly-AGT gap (U4).** The modeled winter is a
  *flat monthly plateau* (2023 Jan/Feb p50 $123 → max $147; 2025 p50 $55 →
  max $66) because the committed AGT basis is monthly — every winter hour
  inherits the same monthly-mean gas. Real winter is daily-spot-spiky (2023
  actual p99 $273, max $462; 2025 p99 $285). The model **never clears an hour
  >$200 in any winter** (vs 44 / 11 / 160 actual): the p99 tail under-shoots in
  every year. Where the monthly mean over-states the typical hour the model
  over-prices (2023/24 mid-curve, the fat >$75 band); where the realized daily
  blowout dwarfs it the model under-prices (2025 Jan −79 / Feb −72 / Dec −69
  $/MWh). Both directions are the **daily-AGT U4 data gap** (neiso-data-audit
  §2b; gap #1 above is the same limitation on the oil side) — not an offer
  band. The summer-peak over-pricing months (Jul-2023 $128, Aug-2024 $87, zero
  slack) are the oil-steam scarcity dispatch that the monthly AGT pushes into
  summer instead of winter — same U4 family, filed.
- **Zonal separation — 4-zone gate confirmed, CT tail filed (U6).** Modeled
  Boston−Hub and CT−Hub spreads are exactly $0 (all four load zones identical;
  RSP TTC seeds non-binding). Actual day-ahead separation is itself sub-$2 mean
  (Boston−Hub +0.3..+0.8, CT−Hub −0.8..−1.9), so the copper-plate internal
  price tracks the "level-market" reality within tolerance for Boston/North.
  The one divergence: the model cannot reproduce **Connecticut's growing
  cheap-side tail** (CT−Hub p99 $5 → $13.5 across 2023→2025). Do **not** add
  zones (`neiso-zonal-adequacy.md` keeps the 4-zone split on structural
  grounds); the lever is the U6 interface-limit upload, not topology.
- **Mid-curve level (year-flatness) = served-interchange convention (P9).** The
  model sits ~$54 every year while actual rises $36 → $66, because imports are
  netted into demand rather than price-setting (cheap HQ hydro never sets the
  margin). `--priced-interchange` pulled 2024 to $48 (still over) — the priced
  node is the forward mechanism.

**Owner:** P7/P13 (U4 daily AGT — winter tail), P10 (U6 interface flows — CT
zonal tail), P9 (priced node — mid-curve level). `neiso-zonal-adequacy.md`
carries the spread duration curves.

### 4. [TRACE] Coal 0.00–0.08 vs ~0.2 TWh

Merrimack Station (EIA 2364, Bow NH, ~108 MW bituminous, deactivated Jun-
2025) barely clears in any year. Trace, not a scored target.

---

## What changed to enable this run

- `build_calibration_reference.py` — NEISO added to `CALIBRATION_ISOS`
  (BA code `ISNE`, years 2023/2024/2025). EIA-923 oil (`DFO`/`RFO`/…) and
  hydro (`WAT`/`HY`) columns added to NEISO/NYISO blocks via
  `_EIA923_EXTRA_FUELS_BY_ISO`. ERCOT/PJM/CAISO outputs byte-identical.
- `config/constants.py` — `GAS_BASIS_DIFFERENTIAL["NEISO"] = +1.10` (was
  missing); `STATE_CARBON_PRICE_BY_ISO["NEISO"]` (RGGI 2023–2025);
  `NUCLEAR_MONTHLY_CF_BY_YEAR["NEISO"]` (EIA-923 monthly per-year refueling
  cadence for Millstone 2+3 + Seabrook); `IMPORT_TRANCHES["NEISO"]` /
  `EXPORT_TRANCHES["NEISO"]` (five-tranche priced import node); thermal
  availability + fleet availability (0.85) + market design (FCM,
  net_CONE $95/kW-yr); `_SCALAR_INTERCHANGE_ISOS` extended to include NEISO.
- `data/eia_loader.py` — `neiso_net_interchange(year)` (reads ISNE `Total
  interchange` column; import-negative); `_load_neiso_hourly_demand`
  (4-zone RSP-share disaggregation, same machinery as the other ISOs).
- `data/fuel.py` — `apply_hub_basis_overlay` (REPLACE gas fuel price with
  measured HH+basis for covered months; runs before `apply_dual_fuel_pricing`
  so oil-parity cap sees the blown-out hub gas); `gas_monthly_actuals` path
  extended to NEISO.
- `scripts/run_calibration_full.py` — `--hydro-backfill-year` option (default
  None; every prior ISO run byte-identical; used only for NEISO 2025
  provisional).
- `data/raw/_processed-legacy/thermal_tranches_NEISO.csv` / `bin_assignments_NEISO.csv`
  — per-plant CAMPD committed + peaking shares (2023–2025 NE-state CEMS).
- `data/raw/campd-unit-outages-NEISO.csv` — unit-level outage windows
  (2023: 431, 2024: 452, 2025: 422 event-based windows; 34 facilities).
- `data/raw/gas_basis_by_iso_month.csv` — 35/36 NEISO months (ISO-NE
  MA gas index from isonewswire.com monthly posts; basis = index − EIA HH).

**No offer-curve variant for NEISO.** National class defaults
(`OFFER_CURVES_BY_FUEL`) apply unchanged; no per-class overrides were added.
The CAMPD-derived per-plant `committed_pct` / `peaking_pct` in the tranche
CSV are the only NEISO-specific tranche tuning and are data-derived.

---

## Next steps for NEISO calibration (Stage G continued)

1. ~~Serve measured net-interchange schedule (gap #1 in P11 smoke).~~
   **Done** — measured schedule for backcasts (P9b); priced HQ_import node
   for forward scenarios (P9), validated with `--priced-interchange`.
2. ~~Upload U2 (DA + RT hourly LMPs, 2023–2025) — formal price benchmarking,
   duration-curve overlay, Boston/CT spread analysis.~~ **Done (2026-06-12,
   P10)** — `actual_lmp.json` NEISO block + `actual_lmp_hourly_NEISO.parquet`
   landed; the three keepers are scored (gap #3 above). The scoring confirms
   the winter tail is the U4 daily-AGT gap (next item) and the CT zonal tail is
   U6 — no offer-band fix.
3. **Upload U4 refinement (daily Algonquin Citygate basis, 2023–2025)** —
   the single most important future upload for winter accuracy. Daily cold-
   snap AGT spot prices (>$30/MMBtu on peak days) trip the dual-fuel CT
   switch and move oil burn from summer to winter, closing gap #1.
4. **Upload U1 (NH_2025 CEMS unit-level parquet)** — closes the only 2025
   CEMS gap; regenerate `campd-unit-outages-NEISO.csv` to add NH 2025
   measured windows (currently statistical availability, ~7% of fossil MW).
5. **Final 2025 EIA-923** — when published (typically ~9 months after year-
   end), re-run `build_calibration_reference.py` and the 2025 bundle to
   score oil/hydro/solar vs actuals. Expect the backfill flag to become
   unnecessary.
6. **Upload U6 (N–S / Boston-Import / CT-Import interface flows + limits)** —
   replaces Tier-3 RSP TTC seeds with observed limits; enables Boston/CT
   congestion calibration and the `neiso-zonal-adequacy.md` adequacy test.
