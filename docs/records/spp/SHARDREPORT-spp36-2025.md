# SHARDREPORT — SPP-36 shard 3 of 3, span year 2025

Shard: SPP-36 SHARD 3 of 3 · arm = SPP keeper 9 recipe + `unit_outage_short_windows=true` (COAL scope only).
Control = `results/calibration/spp27_span` (keeper 9), year 2025, P1.
The parent composes; this shard registers nothing and is not a calibration lane.

## 1. Revision and hard stops

`git rev-parse HEAD` → `706aa5475a44e2bb87326a556833f326f926160b`

| hard stop | check | result |
|---|---|---|
| 1 | pinned revision matches `706aa547…160b` exactly; no pull/rebase/fetch performed | **PASS** |
| 2 | `pytest tests/unit/pipeline/test_run_year_kwarg_binding.py -q` → `4 passed in 0.67s` | **PASS** |
| 3 | control `run_config.json` signature (see below) | **PASS** |
| 4 | `data/raw/campd-unit-outages-short-SPP.csv` = 621 lines (620 data rows), `plant_group` COAL on all 620 | **PASS** |

Hard stop 3 detail, read from `results/calibration/spp27_span/run_config.json` → `scenario_config`:

```
mustrun_window_commitment_grain = True
unit_outage_short_windows       = False
wefor_multiplier                = 0.7
mode                            = 'backcast'
hindcast                        = False
campd_per_unit_attribution      = False
campd_outage_merit_order_guard  = False
offer_curve_by_group.CC_REGULAR = {'committed': 0.93, 'econ_low': 0.93, 'econ_high': 0.93,
                                   'peak': 0.93, 'econ_low_share': 0.5, 'pct_peaking': 8.0}
```

All nine required fields match. Nothing was "fixed".

## 2. The solve

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2025 \
  --out-dir results/calibration/spp36_2025 \
  --set unit_outage_short_windows=true \
  --note "SPP-36 span year 2025: keeper 9 recipe + unit_outage_short_windows=true (COAL scope). Owner promotion ruling 2026-09-12. Independent year 3 of 3; the parent composes."
```

- exit code **0**
- wall time **195 s**
- `unit_outage_short_windows_gas` was NOT passed and reads `False` in the arm config (matrix cell `R` for SPP, untouched).
- No `--reuse-solved`, no retry, no flag variation, no edit under `src/` or `scripts/`.

Container/memory (runner-emitted, unmodified runner, no `--no-container-preflight`):

```
INFO: container preflight: memory ceiling 13.34 GiB (/sys/fs/cgroup/memory/process_api/01a0969a-6c7f-7764-afc7-47241d4d8798/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 9 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 9.0 = 22.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 22.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
INFO: memory peak: cgroup_peak_rss_gib=5.44, cgroup_peak_rss_plus_swap_gib=5.44, process_vmhwm_gib=4.91, process_vmswap_now_gib=0.00
```

The 22.3 GiB warning is informational for MISO/PJM per-plant LPs; SPP peaked at 5.44 GiB and was never near the ceiling.

## 3. The derate log lines — VERBATIM

The short overlay **fired**. Both lines appear twice (once per pass, P0 and P1), identical each time:

```
INFO: unit-outage derate (SPP 2025): 303 plant-tranches derated
INFO: short unit-outage derate (SPP 2025): 94 plant-tranches derated (< 5-day baseload-coal windows)
```

Scale: the short leg touches 94 plant-tranches against 303 from the standing unit-outage derate.

## 4. Annual TWh by class — `class_hourly_2025.parquet`, `pass == "P1"`, `sum(mw)/1e6`

| klass | arm | control | delta |
|---|---:|---:|---:|
| CC_CHP | 1.9512 | 1.9343 | +0.0168 |
| CC_REGULAR | 36.3783 | 34.9097 | **+1.4686** |
| COAL_LIGNITE | 6.5890 | 6.7981 | −0.2091 |
| COAL_PRB | 78.0526 | 80.4149 | **−2.3623** |
| CT_CHP | 1.1593 | 1.1487 | +0.0106 |
| CT_PEAKER | 15.9916 | 14.2422 | **+1.7494** |
| OTHER | 0.4891 | 0.4891 | 0.0000 |
| ST_CHP | 0.1818 | 0.1760 | +0.0058 |
| ST_GAS | 11.3395 | 12.0198 | −0.6803 |
| biomass | 0.9490 | 0.9490 | 0.0000 |
| hydro | 8.8204 | 8.8204 | 0.0000 |
| nuclear | 15.7804 | 15.7804 | 0.0000 |
| oil | 0.0002 | 0.0000 | +0.0002 |
| solar | 2.3248 | 2.3244 | +0.0004 |
| wind | 122.0267 | 122.0210 | +0.0057 |
| **TOTAL** | **302.0339** | **302.0280** | **+0.0059** |

Coal (PRB + lignite) falls 2.5714 TWh; gas (CC_REGULAR + CT_PEAKER + ST_GAS + the CHP classes) rises 2.5709 TWh. The footprint is confined to the classes the COAL-scoped overlay can reach and their replacements — no renewable, nuclear or hydro row moves beyond rounding.

## 5. System metrics — `system_2025.parquet`, `pass == "P1"`

| metric | arm | control |
|---|---:|---:|
| total `slack` | **240.5966 MWh** | 0.0000 MWh |
| total `dump` | 0.0000 MWh | 0.0000 MWh |
| total `demand` | 301.8402 TWh | 301.8402 TWh |
| load-weighted mean price `sum(price*demand)/sum(demand)` | **30.0737** | 28.7893 |
| MAX zonal price | **2000.0000** | 73.7731 |
| hours with max zonal price > 200 | **2** | 0 |

Monthly load-weighted mean prices (hour 0 = 2025-01-01 00:00), Jan→Dec, 4 dp:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| arm | 38.9472 | 33.6150 | 24.1896 | 22.2295 | 27.2666 | 28.7535 | 32.5393 | 30.2030 | 28.3705 | 27.6368 | 28.1419 | 35.2383 |
| control | 37.1406 | 32.1788 | 23.4703 | 21.6613 | 26.7988 | 27.9969 | 31.8017 | 29.5803 | 27.6535 | 25.9966 | 27.1779 | 30.4948 |

Every month rises; the largest move is December (+4.7435) and the smallest is April (+0.5682).

## 6. Arm `scenario_config` signature

```
unit_outage_short_windows       = True      <- the arm
unit_outage_short_windows_gas   = False     <- NOT armed, as required
unit_outage_window_hour_grain   = False
mustrun_window_commitment_grain = True
wefor_multiplier                = 0.7
offer_curve_by_group.CC_REGULAR = {'committed': 0.93, 'econ_low': 0.93, 'econ_high': 0.93,
                                   'peak': 0.93, 'econ_low_share': 0.5, 'pct_peaking': 8.0}
```

`sha256(json.dumps(offer_curve_by_group, sort_keys=True))` =
`090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`

**This MATCHES the control's hash exactly.** The whole offer-curve mapping is unchanged from keeper 9; the single moved field is `unit_outage_short_windows`.

## 7. Surprises, and the slack reproduction

**The prior single-year screen reproduces EXACTLY, to 4 dp.**

- slack **240.5966 MWh** — the screen's figure to the digit
- **2 hours** above $200 — the screen's count
- both hours in **SPP-South**, at VOLL $2,000 — the screen's zone and price

The two hours, from `system_2025.parquet` (`slack > 0`):

| zone | hour | slack MWh | price | zonal demand MW |
|---|---:|---:|---:|---:|
| SPP-South | 8507 | 204.9556 | 2000.0 | 18596.5648 |
| SPP-South | 8508 | 35.6410 | 2000.0 | 18596.5648 |

Consecutive hours (8507, 8508 → 2025-12-21 11:00 and 12:00 UTC-naive from an hour-0 = Jan 1 00:00 index), the first ~5.7× the second — a single unserved-energy episode tapering out, not scattered noise. The control's 2025 slack is exactly 0.0000 MWh, so this is entirely the arm's doing. No tuning toward or away from these figures was attempted; the shard ran the one prescribed command once.

Two further observations, reported not adjudicated:

- The load-weighted mean price rises **+1.2844 $/MWh** (28.7893 → 30.0737) on 8,758 hours priced at or below the control's $73.77 ceiling plus 2 hours at VOLL. The 2 VOLL hours alone account for roughly 0.24 of that; the remaining ~1.04 is a broad, every-month lift from coal displaced to gas, not a tail artifact.
- `legitimacy_diagnostics.json` was written, and the replay printed
  `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8 score from its contents)`.
  D-9 overlay quarantine and D-10 free-class provenance both read PASS in the same output. The gate verdict is the parent's to score on the composed bundle — this shard flags it and stops there.

Nothing was repaired, patched, re-derived or deleted. No file under `src/`, `scripts/`, `frontend/data/backcast/**`, `CLAUDE.md`, `calibration-complete.json`, `.gitignore` or any keeper shard was touched.
