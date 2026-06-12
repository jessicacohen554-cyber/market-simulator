# NYISO P11 — Smoke backcast 2023 (structural gap report)

Branch `claude/nyiso-p11-smoke`. Smoke year **2023** (full CEMS; 2024 blocked on
`NY_2024`, upload U1). Prereqs P0–P9 + P13 merged; **P10 held on the LMP upload
(U2)** — so price calibration is **level-only** this pass (no actual-LBMP
duration or zonal-spread comparison). Per playbook §6, this pack runs
calibration but tunes **structure before knobs** and does **not** touch
offer-curve bands while a structural row is red.

Commands:
```
python scripts/run_calibration.py      --iso NYISO --year 2023 --commitment
python scripts/run_calibration_full.py --iso NYISO --year 2023 --commitment \
       --out-dir results/calibration/nyiso_smoke_2023
# diagnostic (hypothesis confirmation, separate bundle):
python scripts/run_calibration_full.py --iso NYISO --year 2023 --commitment \
       --priced-interchange --out-dir results/calibration/nyiso_smoke_2023_priced
```

## Headline

The 2023 energy-only backcast over-generates **+16% on total** (147.31 vs
126.96 TWh EIA-923), concentrated entirely in gas (gas 80.11 vs 63.79 TWh,
+25.6%). **This is one structural miss, not a fleet of band errors:** NYISO is a
~16%-of-load net importer (actual net interchange **−23.45 TWh**, EIA-930) and
the default backcast serves **0 TWh** of imports, so the ~24 TWh import wedge is
displaced onto in-state gas. Hydro (−0.1%), nuclear (−0.1%) and wind (−3.6%)
are dead-on. **No offer band was tuned.**

Confirmation: re-running with `--priced-interchange` (the P9 node, 5 tranches /
5900 MW) reclaims the whole wedge — gas 80.11 → **55.51 TWh** (−13% vs 923),
net interchange 0 → **−25.41 TWh** (vs −23.45 actual; import-hours 100% match,
diurnal corr +0.80), total 147.31 → 121.75 TWh, avg price $71 → $40/MWh — with
**no band change**. That is the structural-before-knobs proof: the gas_ct +81% /
gas_st +113% / CO2 +57% reads in the energy-only run are interchange symptoms.

## Benchmark comparison (P0 table)

Generation TWh — energy-only smoke (`nyiso_smoke_2023`) vs `--priced-interchange`
diagnostic vs benchmarks:

| fuel | model (energy-only) | model (+priced) | EIA-923 | EIA-930 |
|---|---|---|---|---|
| gas (cc+ct+st) | 80.11 (+25.6%) | **55.51 (−13.0%)** | 63.79 | 61.00 |
| nuclear | 27.49 (−0.1%) | 27.49 | 27.52 | 24.00 |
| hydro | 28.38 (−0.1%) | 28.38 | 28.40 | 26.84 |
| wind | 4.60 (−3.6%) | 4.60 | — | 4.60 |
| solar | 1.94 (−5.0%) | 1.94 | — | 0.00 |
| oil | 0.15 (−64%) | 0.00 | 0.42 | 2.17 |
| biomass | 2.43 | 1.62 | — | — |
| **TOTAL** | **147.31 (+16.0%)** | **121.75 (−4.1%)** | 126.96 | 118.61 |

- **Net interchange:** actual −23.45 TWh / −2677 MW avg (EIA-930). Energy-only
  model 0.00; priced model −25.41 TWh / −2901 MW (duration RMSE 442 MW, diurnal
  corr +0.80; over-imports ~8% and the low-import tail is off — p99 model −2100
  vs actual −705 — a P9 tranche/export-sink shape refinement).
- **CO2 (fast-run):** model 44.38 Mt vs eGRID 2023 ≈ 28.2 Mt (+57%) —
  proportional to the gas over-gen; closes with imports.
- **Price level:** energy-only avg $70.99/MWh, priced avg $40.34/MWh, 0 negative
  hours. **Not validated** — P10/LMP (U2) held this pass.

## Ranked gap list (structural checklist order)

| # | Structural row | Status | Finding | Owning pack |
|---|---|---|---|---|
| 1 | demand / net-load | 🟢 | Served = demand 147.05 TWh; front-of-meter convention correct. Zonal shares are **Tier-3 Gold-Book static** (U3 zonal load not uploaded — noted, not a smoke blocker). | P8 (U3 refresh) |
| 2 | **net interchange** | 🔴 **dominant** | Backcast serves **0** net imports vs actual **−23.45 TWh**; ~24 TWh dumped on gas. Confirmed: priced node closes it. | **P9** |
| 3 | hydro + storage throughput | 🟢 | Hydro 28.38/28.40 TWh, budget honored, seasonal shape kept; nuclear −0.1%. PS 0.41–0.97 TWh, BESS 0.08–0.11 TWh plausible but **unbenchmarked** (no EIA-930 BAT/PS column in this BA extract). | — (P5 benchmark data gap) |
| 4 | gas + RGGI level | 🟡 | RGGI $13.49/t active. Gas priced at the **flat Henry-Hub $2.54 seed** — `--gas-monthly-actuals` **not** enabled here, and winter basis (U4) absent. Level unvalidatable (P10 held). | **P7** (enable measured 923 gas + U4 basis) |
| 5 | dual-fuel / outage coverage | 🔴 | Dual-fuel machinery active (385 tranches / 15.9 GW capped at oil parity) but oil **0.15 → 0.00 TWh** vs 0.42 (923) / 2.17 (930). Flat $2.54 gas never spikes past distillate parity → switch never fires. Outage overlay healthy (318 plant-tranches derated from CEMS). | **P13 + P7** (needs U4 winter basis) |
| 6 | offer-curve bands | ⏸️ **not tuned** | Rows 2/4/5 red/amber → bands untouched per playbook. gas_ct +81% / gas_st +113% (energy-only) collapse to within tolerance once imports are served. | P2/P12 (after structure) |

### NYISO-specific watch items
- **Hydro displacement** 🟢 — lands at budget; neither over- nor under-displaced.
- **Downstate congestion separation** ⚪ **not validated** — modeled zonal spread
  ~$0.5 (energy-only) / ~$1.5 (priced); interfaces non-binding. Cannot compare to
  actual J−A / K−A LBMP spreads — **P10 (U2 LMP) held**. File to P10; interface
  TTCs may need U7.
- **Winter dual-fuel** 🔴 — see row 5; gated on U4 winter gas basis.

## Recommended next actions (owning pack per fix)
1. **P9 — serve interchange in NYISO backcasts.** Either make the priced
   import/export node default-on for NYISO backcast years, or fold the measured
   EIA-930 net-interchange schedule into NYISO demand (PJM precedent, §8.2).
   Then refine tranche/export-sink shape (low-import tail; ~8% over-import).
   *This is the gate — nothing downstream calibrates until imports are served.*
2. **P7 — enable `--gas-monthly-actuals` for NYISO** and layer the U4 Transco
   Z6 / Iroquois winter basis; this unblocks both the gas price level and the
   dual-fuel switch.
3. **P13 — re-validate winter oil switching** once U4 lands (Jan/Feb oil should
   be non-trivial: EIA-930 shows ~365 / ~454 GWh).
4. **P10/U2 + P8/U3** — upload hourly LBMP and zonal load to unblock price
   level, downstate-separation, and measured zonal shapes.
5. **Only after structure is green (P12):** offer-curve band tuning.
