# SHARD REPORT — SPP-32 arm A SCREEN (2025)

Shard: SPP-32 SHARD A. One year, one solve, numbers only. Screen bundle is a rule-29
throwaway — **not registered, not committed** (nothing under `results/` leaves this container).

## 1. Revision and hard stops

`git rev-parse HEAD` → `dce9398314b146d9110baad6b3e3adcc999b0c5f`

| Hard stop | Check | Result |
|---|---|---|
| 1 | HEAD == `dce9398314b146d9110baad6b3e3adcc999b0c5f` | **PASS** |
| 2 | Control config signature (`results/calibration/spp27_span/run_config.json`) | **PASS** |
| 3 | `data/raw/campd-unit-outages-short-SPP.csv` = 621 lines / 620 data rows, all `plant_group` COAL | **PASS** |

Hard stop 2 detail, as read from the control's `scenario_config`:

| field | value | expected | verdict |
|---|---|---|---|
| `mustrun_window_commitment_grain` | `True` | true | ok |
| `unit_outage_short_windows` | `False` | false | ok |
| `offer_curve_by_group.CC_REGULAR` | `committed 0.93 · econ_low 0.93 · econ_high 0.93 · peak 0.93` | same | ok |
| `wefor_multiplier` | `0.7` | 0.7 | ok |
| `mode` | `"backcast"` | backcast | ok |
| `hindcast` | `False` | false | ok |

The CC_REGULAR dict also carries the two structural shares `econ_low_share: 0.5` and
`pct_peaking: 8.0`. Those are not band multipliers, are not part of the stated signature, and
were not touched — recorded here only so the next reader is not surprised by the extra keys.

Hard stop 3 detail: `wc -l` = 621; `csv.DictReader` yields 620 rows; `Counter(plant_group)` =
`{'COAL': 620}` — a single value, no other group present.

## 2. The command

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2025 \
  --out-dir results/calibration/spp32_A_2025 \
  --set unit_outage_short_windows=true \
  --note "SPP-32 arm A SCREEN (2025): keeper 9 recipe + unit_outage_short_windows=true (COAL scope only). Throwaway screen bundle, never registered."
```

- **exit code: 0**
- **wall time: 202 seconds** (3 min 22 s)

Environment: no `.venv` existed, so
`python3 -m pip install --ignore-installed PyYAML -r requirements.txt` was run once (first
attempt succeeded, no retries) and `python3` used. `requirements.txt` was not edited.
`scripts/hydrate_data.py --profile spp` reported this is a FULL clone — every blob already
local, nothing to hydrate.

## 3. The derate log line — VERBATIM

The overlay **fired**. The line appears twice (once per fleet build, P0 and P1), identical both
times:

```
INFO: short unit-outage derate (SPP 2025): 94 plant-tranches derated (< 5-day baseload-coal windows)
```

**94 plant-tranches derated.**

For context, the line immediately above it each time is the pre-existing long-window overlay,
unchanged by this arm:

```
INFO: unit-outage derate (SPP 2025): 303 plant-tranches derated
```

## 4. Annual TWh by class (P1), arm vs control

`results/calibration/spp32_A_2025/hourly/class_hourly_2025.parquet`, `pass == "P1"`,
`sum(mw)/1e6`, 4 dp. Every class present in the arm is listed.

| klass | arm A (TWh) | control keeper 9 (TWh) | delta (TWh) |
|---|---:|---:|---:|
| wind | 122.0267 | 122.0210 | +0.0057 |
| COAL_PRB | 78.0526 | 80.4149 | **−2.3623** |
| CC_REGULAR | 36.3783 | 34.9097 | **+1.4686** |
| CT_PEAKER | 15.9916 | 14.2422 | **+1.7494** |
| nuclear | 15.7804 | 15.7804 | 0.0000 |
| ST_GAS | 11.3395 | 12.0198 | **−0.6803** |
| hydro | 8.8204 | 8.8204 | 0.0000 |
| COAL_LIGNITE | 6.5890 | 6.7981 | **−0.2091** |
| solar | 2.3248 | 2.3244 | +0.0004 |
| CC_CHP | 1.9512 | 1.9343 | +0.0169 |
| CT_CHP | 1.1593 | 1.1487 | +0.0106 |
| biomass | 0.9490 | 0.9490 | 0.0000 |
| OTHER | 0.4891 | 0.4891 | 0.0000 |
| ST_CHP | 0.1818 | 0.1760 | +0.0058 |
| oil | 0.0002 | 0.0000 | +0.0002 |

Coal total (PRB + LIGNITE): 84.6416 arm vs 87.2130 control → **−2.5714 TWh**.
Gas total (CC_REGULAR + CT_PEAKER + ST_GAS + CC_CHP + CT_CHP + ST_CHP): 66.8017 arm vs
64.4307 control → **+2.3710 TWh**. The displaced coal lands almost entirely on gas, as a
coal-scoped availability derate should.

## 5. System metrics (P1)

`results/calibration/spp32_A_2025/hourly/system_2025.parquet`, `pass == "P1"`
(17,520 rows = 2 zones × 8,760 h).

| metric | arm A | control | delta |
|---|---:|---:|---:|
| total `slack` (MWh) | **240.5966** | 0.0000 | +240.5966 |
| total `dump` (MWh) | 0.0000 | 0.0000 | 0.0000 |
| total `demand` (TWh) | 301.8402 | 301.8402 | 0.0000 |
| load-weighted mean price ($/MWh) | 30.0737 | 28.7893 | +1.2844 |
| mean over hours of MAX zonal price ($/MWh) | 30.2291 | — | — |
| MAX zonal price ($/MWh) | **2000.0000** | 73.7731 | +1926.2269 |
| hours with max zonal price > 200 | **2** | 0 | +2 |

Monthly load-weighted mean price ($/MWh), hour 0 = 2025-01-01 00:00:

| month | LW mean price |
|---|---:|
| 1 | 38.9472 |
| 2 | 33.6150 |
| 3 | 24.1896 |
| 4 | 22.2295 |
| 5 | 27.2666 |
| 6 | 28.7535 |
| 7 | 32.5393 |
| 8 | 30.2030 |
| 9 | 28.3705 |
| 10 | 27.6368 |
| 11 | 28.1419 |
| 12 | 35.2383 |

## 6. Arm config as solved

From `results/calibration/spp32_A_2025/run_config.json`, `scenario_config`:

| field | arm A | control |
|---|---|---|
| `unit_outage_short_windows` | `True` | `False` |
| `unit_outage_short_windows_gas` | `False` | *absent from the control's serialized config* |
| `mustrun_window_commitment_grain` | `True` | `True` |
| `wefor_multiplier` | `0.7` | `0.7` |
| `offer_curve_by_group.CC_REGULAR` | `{committed 0.93, econ_low 0.93, econ_high 0.93, peak 0.93, econ_low_share 0.5, pct_peaking 8.0}` | identical |

**`offer_curve_by_group` is byte-identical to the control's** — verified by comparing
`json.dumps(..., sort_keys=True)` of the whole mapping, not just the CC_REGULAR entry.
Result: `True`. No offer-curve channel was touched by this arm.

`unit_outage_short_windows_gas` is `False` in the arm and does not appear at all in the
control's `run_config.json`. That is a serialization-vintage difference in the committed
control bundle, not a behavioural one: the field is off in the arm, so the overlay ran
COAL-scope only, which is exactly what the 620 all-COAL extract rows and the
"< 5-day baseload-coal windows" log suffix confirm.

## 7. What surprised me

**SLACK IS NON-ZERO: 240.5966 MWh.** The control has exactly 0.0000. All of it is in
SPP-South, in two consecutive hours on 2025-12-21:

| timestamp | hour | zone | price | slack (MW) | zonal demand (MW) |
|---|---:|---|---:|---:|---:|
| 2025-12-21 11:00 | 8507 | SPP-South | 2000.0 | 204.9556 | 18,596.5648 |
| 2025-12-21 12:00 | 8508 | SPP-South | 2000.0 | 35.6410 | 18,596.5648 |

Those two hours are also the entirety of the "max zonal price > 200" count and the whole of
the 73.77 → 2000.00 jump in the max zonal dual: the price is VOLL, i.e. the LP is short and
paying the slack penalty, not discovering a scarcity price from a real supply stack. 240 MWh
against 301.84 TWh of annual demand is ~0.00008% of energy, so it barely moves the
load-weighted mean — but a keeper with non-zero slack is a different object from one without,
and the parent should treat this as a finding rather than rounding it away. I did not
investigate the cause and did not re-run with different flags.

Two smaller things worth stating plainly:

- **`oil` goes from exactly 0.0000 to 0.0002 TWh.** Trivial in energy, but it means the derate
  pushed the stack far enough up the merit order to touch a class the control never started.
- **The derate line printed twice**, once per fleet build (P0 and P1), with the identical count
  of 94. That is expected — two passes, one fleet construction each — recorded so nobody reads
  the duplicate as 188 tranches.

Nothing was patched, nothing under `src/` or `scripts/` was edited, no result was deleted, no
PR opened, and no dashboard/registry path was touched. The screen bundle
`results/calibration/spp32_A_2025/` remains on local disk, uncommitted, and will not survive
this container.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
