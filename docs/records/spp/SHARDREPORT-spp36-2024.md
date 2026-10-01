# SHARD REPORT — SPP-36 shard 2 of 3 — span year **2024**

Arm: SPP keeper 9 (`spp27_span`) recipe + `unit_outage_short_windows=true` (COAL scope).
Out-dir: `results/calibration/spp36_2024`. Independent year; the parent composes.

## 1. Hard stops

`git rev-parse HEAD` → `706aa5475a44e2bb87326a556833f326f926160b`

| # | Check | Verdict |
|---|---|---|
| 1 | HEAD == `706aa5475a44e2bb87326a556833f326f926160b` | **PASS** (exact) |
| 2 | `pytest tests/unit/pipeline/test_run_year_kwarg_binding.py -q` | **PASS** — `4 passed in 0.81s` |
| 3 | Control `spp27_span/run_config.json` signature | **PASS** — all 9 fields as specified |
| 4 | `data/raw/campd-unit-outages-short-SPP.csv` | **PASS** — 621 lines / 620 data rows, `plant_group` COAL on all 620 (`uniq -c` → `620 COAL`). Not re-derived. |

Hard stop 3 detail, read from the control's `scenario_config`:
`mustrun_window_commitment_grain` `True` · `unit_outage_short_windows` `False` ·
`offer_curve_by_group.CC_REGULAR` `{committed 0.93, econ_low 0.93, econ_high 0.93, peak 0.93}`
(plus the structural `econ_low_share 0.5`, `pct_peaking 8.0`) · `wefor_multiplier` `0.7` ·
`mode` `"backcast"` · `hindcast` `False` · `campd_per_unit_attribution` `False` ·
`campd_outage_merit_order_guard` `False`.

Environment: no `.venv` present, so `python3 -m pip install --ignore-installed PyYAML -r requirements.txt`
(clean first try, no retry needed) and `python3`. `requirements.txt` not edited. Clone was full; hydration a no-op.

## 2. The command

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2024 \
  --out-dir results/calibration/spp36_2024 \
  --set unit_outage_short_windows=true \
  --note "SPP-36 span year 2024: keeper 9 recipe + unit_outage_short_windows=true (COAL scope). Owner promotion ruling 2026-09-12. Independent year 2 of 3; the parent composes."
```

**Exit code 0. Wall time 188 s.** No `--reuse-solved`. `unit_outage_short_windows_gas` never passed.

Container preflight (runner's own, unmodified): ceiling 13.34 GiB, 9 GiB swap provisioned → 22.3 GiB
(the runner WARNs this is under its 24 GiB target; irrelevant here — SPP is not per-plant).
`memory peak: cgroup_peak_rss_gib=5.19, cgroup_peak_rss_plus_swap_gib=5.19, process_vmhwm_gib=4.67, process_vmswap_now_gib=0.00`.

## 3. The derate log lines — **the overlay FIRED**

Verbatim, both passes (P0 at log lines 65–66, P1 at 87–88; identical in each):

```
INFO: short unit-outage derate (SPP 2024): 73 plant-tranches derated (< 5-day baseload-coal windows)
```

adjacent line, for scale:

```
INFO: unit-outage derate (SPP 2024): 298 plant-tranches derated
```

So the short overlay adds **73** plant-tranches against the base overlay's **298** — the leg is live, not void.

## 4. Annual TWh by class, P1 (`sum(mw)/1e6`, 4 dp)

| klass | arm TWh | control TWh | Δ (arm − ctl) |
|---|---:|---:|---:|
| CC_CHP | 1.8921 | 1.8832 | +0.0089 |
| CC_REGULAR | 42.4803 | 41.6791 | **+0.8012** |
| COAL_LIGNITE | 6.1807 | 6.5622 | **−0.3815** |
| COAL_PRB | 58.5803 | 60.6077 | **−2.0274** |
| CT_CHP | 1.2481 | 1.2367 | +0.0114 |
| CT_PEAKER | 19.4420 | 18.0986 | **+1.3433** |
| OTHER | 0.5987 | 0.5987 | 0.0000 |
| ST_CHP | 0.4263 | 0.3996 | +0.0267 |
| ST_GAS | 13.0946 | 12.8748 | +0.2197 |
| biomass | 1.1803 | 1.1803 | 0.0000 |
| hydro | 8.9666 | 8.9666 | 0.0000 |
| nuclear | 15.0157 | 15.0157 | 0.0000 |
| oil | 0.0035 | 0.0030 | +0.0005 |
| solar | 1.1941 | 1.1941 | 0.0000 |
| wind | 120.7005 | 120.7003 | +0.0002 |
| **TOTAL** | **291.0038** | **291.0008** | **+0.0030** |

Coal loses **2.4089 TWh** (PRB 2.0274 + lignite 0.3815); gas takes essentially all of it
(CT_PEAKER +1.3433, CC_REGULAR +0.8012, ST_GAS +0.2197, CHP/oil +0.0475 = +2.4117).
The +0.0030 TWh total gap is the added slack plus rounding.

## 5. System, P1

**Hour count actually read: 8,760** — *not* 8,784. The 2024 bundle is an 8,760-hour year
(rule 8 `[R-8760]` fixes T=8760; the control's 2024 is the same), 17,520 rows = 8,760 h × 2 zones
(SPP-North, SPP-South). Every number below uses 8,760. Month labels map hour *h* →
`2024-01-01 00:00 + h hours`, so the series runs to Dec 30 23:00.

| metric | ARM | control |
|---|---:|---:|
| total `slack` MWh | **1295.6995** | 370.1017 |
| hours with slack > 0 | **4** | 2 |
| total `dump` MWh | 0.0000 | 0.0000 |
| total `demand` TWh | 290.8868 | 290.8868 |
| load-weighted mean price `sum(price*demand)/sum(demand)` | **26.3509** | 25.4676 |
| MAX zonal price | 2000.0000 | 2000.0000 |
| hours with max zonal price > 200 | **8** | 5 |

Monthly load-weighted mean price (ARM, then control):

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ARM | 44.8998 | 21.7070 | 12.4445 | 15.8860 | 21.5548 | 26.0394 | 27.5051 | 28.6198 | 28.2896 | 29.7243 | 23.2025 | 30.5477 |
| ctl | 43.0168 | 21.2324 | 12.2229 | 15.6614 | 21.3165 | 25.5514 | 27.1911 | 28.1481 | 26.7440 | 26.4644 | 22.7400 | 29.5102 |

Every month rises. Largest moves: **October +3.2599** and **September +1.5456** — i.e. the shoulder
months, which is where a short-window coal-outage overlay should bite.

## 6. Arm `scenario_config`

| field | value |
|---|---|
| `unit_outage_short_windows` | **`true`** (the arm) |
| `unit_outage_short_windows_gas` | `false` (never passed; matrix cell `R` for SPP) |
| `unit_outage_window_hour_grain` | `false` |
| `mustrun_window_commitment_grain` | `true` |
| `wefor_multiplier` | `0.7` |
| `offer_curve_by_group.CC_REGULAR` | `{committed 0.93, econ_low 0.93, econ_high 0.93, peak 0.93, econ_low_share 0.5, pct_peaking 8.0}` |
| `mode` / `hindcast` | `"backcast"` / `false` |

`sha256(json.dumps(offer_curve_by_group, sort_keys=True))` =
`090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`
— **this MATCHES the control's stated hash exactly.** The offer surface is untouched; the only
delta is the outage overlay.

## 7. Surprises — **read the slack line first**

**SLACK IS UP, substantially. The arm sheds 1295.6995 MWh in 4 hours against the control's
370.1017 MWh in 2 hours — 3.50× the energy and 2 extra hours.** Direction: **more slack.**

The control's two slack hours are a strict subset of the arm's four, and they deepen:

| hour | timestamp (h→2024-01-01+h) | zone | ARM slack MWh | ctl slack MWh |
|---:|---|---|---:|---:|
| 7070 | 2024-10-21 14:00 | SPP-South | 61.5152 | — (0) |
| 7071 | 2024-10-21 15:00 | SPP-South | 506.2794 | 128.8843 |
| 7072 | 2024-10-21 16:00 | SPP-South | 611.0817 | 241.2173 |
| 7073 | 2024-10-21 17:00 | SPP-South | 116.8232 | — (0) |

One contiguous SPP-South block on **21 October 2024**, all four hours at VOLL $2,000 — the same
event the control already had, widened by one hour on each side and roughly quadrupled in depth.
October is also the month whose price moves most (+3.2599). That is coherent with the overlay's
own mechanism: short (<5-day) coal outage windows land in shoulder season, and SPP-South was
already on the edge there. It is not a new failure mode — it is the existing one, bigger.

Other notes:
- Hours above $200 go 5 → 8, consistent with the same event widening.
- The control reproduced its stated numbers to the digit (slack 370.1017, dump 0.0000,
  max zonal 2000.0000, hours>200 = 5), so the differencing base is confirmed good.
- Load is byte-identical between arm and control (290.8868 TWh), as expected — the overlay
  touches supply only.
- No `hourly/reserve_family_2024.parquet` was written by this bundle, so it is not in the commit.
  `legitimacy_diagnostics.json` was written and is committed.
- No judgement offered on promotion: this shard measures, the parent composes and scores.
