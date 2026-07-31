# SOURCES — `campd_ct_heat_rates_{ISO}.csv`

Measured per-plant **loaded** heat rates for the model's `CT_PEAKER` class, the
rule-14 [R-ACCURATE] replacement for the eGRID plant-average annual heat rate
the non-ERCOT fleet loader otherwise assigns every combustion turbine.

**Producer:** `scripts/data/derive_campd_ct_heat_rates.py --iso <ISO>`
**Consumer:** `market_sim.data.fleet.campd_bins.measured_ct_heat_rates`, applied
in `market_sim.data.fleet.eia860._rows_to_generators` under
`ScenarioConfig.measured_ct_heat_rates` (default **off**).
**Companion:** `campd_ct_heat_rates_{ISO}_units.csv` (`--detail`), the per-unit
table behind each plant row.

## Upstream sources

| Input | Path | Role |
|---|---|---|
| EPA CAMPD unit-level hourly | `data/raw/campd-unit-level/{STATE}_{YEAR}.parquet` | `grossLoad`, `heatInput`, `unitType` — the measurement |
| CAMPD→ISO state map | `market_sim.data.campd.ISO_STATES` | which state extracts feed the ISO (NYISO = NY + NJ) |
| Parasitic-load factors | `data/raw/_processed-legacy/parasitic_load_factors.parquet` | gross→net conversion, via `campd.pooled_factor_map` |
| Model fleet | EIA-860 via `market_sim.data.fleet.load_fleet_from_csv` | which plant codes carry `CT_PEAKER` capacity, and the eGRID rate being replaced |

All four are already-committed repo sources; this artifact is **derived**, not an
independent download. Regenerate by re-running the producer.

## Method

Per CAMPD unit, over the pooled vintages:

```
cap      = p95 of the unit's own gross load
loaded   = hours with grossLoad >= 0.80 x cap        (>= 50 qualifying hours)
hr_gross = sum(heatInput) / sum(grossLoad) over `loaded`
hr_net   = hr_gross / parasitic_factor(plant)
```

The plant value (`heat_rate`) is the **generation-weighted** mean of its units'
`hr_net`. Only `unitType == "Combustion turbine"` rows are measured, which is
what lets a mixed steam/CT facility contribute its turbines instead of being
dropped as unattributable.

**The gross→net step is not cosmetic.** CAMPD meters *gross* load; eGRID, the
model's heat rate, the LP's dispatched MW and the benchmark's "actual" (built as
`gross × parasitic_factor` by `run_calibration_full._campd_hourly_frame`) are all
*net*. Skipping it overstates the correction by the station-service fraction —
1 % for a bare CT, but 10.2 % at Bayonne Energy Center, the largest plant in the
NYISO class. The factor used here is the same committed map the benchmark uses,
so the derived rate and the generation it is scored against share one convention.

Rows outside the physical simple-cycle band `[6.0, 25.0]` MMBtu/MWh are written
with a `flag` and **excluded from the applied map** — a rate below the band is a
mis-tagged combined cycle, above it a broken meter channel. The loader reads
only `flag == "ok"`.

## Governance

CLAUDE.md rules 13 [R-MEASURED] / 14 [R-ACCURATE] / 24 [R-FROZEN-DERIVE].

A machine's loaded heat rate is a physical characteristic, in the same
admissibility class as the CAMPD min-stable loads (`campd_gas_commitment_params_*`)
and CT run horizons (`campd_ct_run_lengths_*`). It regenerates for a forward year
from the same pipeline and responds to changed conditions — a retrofit moves it,
a new unit carries its design rate — so it is a rule-13-admissible **input**, not
a measured outcome fed back to close a residual. Nothing in it is fitted to a
residual, and no parameter of the construction was chosen by looking at one.

Per rule 24 this artifact re-derives **only when CAMPD publishes new or revised
vintages**, never because a residual moved; the re-derivation commit must cite
the data change.

## Vintages

| ISO | Years pooled | Coverage | Derived |
|---|---|---|---|
| NYISO | 2023–2025 | 19/42 plants, 2,395/2,614 MW (91.6 % of class capacity) | 2026-07-27 |
| ERCOT | 2023–2025 | 34/182 plants, 7,036/8,211 MW (85.7 % of eia860 class capacity; 99.2 % of metered class CT energy on the curated sheet) | 2026-07-31 (ERCOT-146 — NOTE: the consuming flag is INERT on ERCOT's curated-bin fleet path; artifact committed as the physical-HR term of a future measured CT-band re-identification, see `docs/DIAGNOSIS-ercot146-measured-ct-heat-rates-2026-07-31.md`) |

The 23 uncovered plants are the tail below ~45 MW plus fuel cells and small
municipal turbines with no qualifying CEMS-loaded hours; each keeps its eGRID
rate, which is the correct fallback (never a hand number).
