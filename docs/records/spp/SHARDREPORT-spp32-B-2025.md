# SHARD REPORT — SPP-32 arm B SCREEN (2025)

Shard: **SPP-32 SHARD B**. One year, one throwaway screen bundle
(`results/calibration/spp32_B_2025`, rule 29 `[R-SCREEN]` — never registered,
never committed). This markdown file is the only artifact that left the
container.

Arm under test: SPP keeper 9 recipe **+ `unit_outage_short_windows=true` AND
`unit_outage_short_windows_gas=true`** (COAL + GAS short-window scope).

---

## 1. Revision and hard stops

`git rev-parse HEAD` → `dce9398314b146d9110baad6b3e3adcc999b0c5f`

| stop | check | observed | verdict |
|---|---|---|---|
| **1** | HEAD == `dce9398314b146d9110baad6b3e3adcc999b0c5f` | exact match | **PASS** |
| **2** | control `results/calibration/spp27_span/run_config.json` signature | see below | **PASS** |
| **3** | the two CAMPD short-window extracts | see below | **PASS** |

No `git pull`, no `git rebase`, no sync, no merge of `origin/main` was performed.

### Hard stop 2 — control config signature (`spp27_span/run_config.json` → `scenario_config`)

| field | required | observed |
|---|---|---|
| `mustrun_window_commitment_grain` | true | `True` |
| `unit_outage_short_windows` | false | `False` |
| `offer_curve_by_group.CC_REGULAR.committed` | 0.93 | `0.93` |
| `offer_curve_by_group.CC_REGULAR.econ_low` | 0.93 | `0.93` |
| `offer_curve_by_group.CC_REGULAR.econ_high` | 0.93 | `0.93` |
| `offer_curve_by_group.CC_REGULAR.peak` | 0.93 | `0.93` |
| `wefor_multiplier` | 0.7 | `0.7` |
| `mode` | "backcast" | `"backcast"` |
| `hindcast` | false | `False` |

All nine match. Two notes, neither a mismatch against the stop list and
neither "fixed":

- `CC_REGULAR` also carries the two **structural** shares `econ_low_share: 0.5`
  and `pct_peaking: 8.0` alongside the four band multipliers. The four
  multipliers the stop names are exactly 0.93 each.
- `unit_outage_short_windows_gas` is **absent** from the control's
  `scenario_config` (the stop did not require it). It is a newer
  `ScenarioConfig` field than the keeper's config snapshot; the replay adds it.

### Hard stop 3 — the two extracts

| file | required | observed | verdict |
|---|---|---|---|
| `data/raw/campd-unit-outages-short-SPP.csv` | 621 lines / 620 data rows, all `plant_group` COAL | 621 lines, 620 data rows, `{COAL: 620}` | **PASS** |
| `data/raw/campd-unit-outages-shortgas-SPP.csv` | 2,838 data rows; CC_REGULAR 2204 / ST_GAS 608 / CC_CHP 26 | 2,838 data rows; `{CC_REGULAR: 2204, ST_GAS: 608, CC_CHP: 26}` | **PASS** |

---

## 2. The solve

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2025 \
  --out-dir results/calibration/spp32_B_2025 \
  --set unit_outage_short_windows=true \
  --set unit_outage_short_windows_gas=true \
  --note "SPP-32 arm B SCREEN (2025): keeper 9 recipe + unit_outage_short_windows=true AND unit_outage_short_windows_gas=true (COAL+GAS scope). Throwaway screen bundle, never registered."
```

- **exit code: 0**
- **wall time: 138 seconds**

Environment: no `.venv` present, so
`python3 -m pip install --ignore-installed PyYAML -r requirements.txt` was run
once (first attempt succeeded, no retry needed) and `python3` was used.
`requirements.txt` was not edited. `scripts/hydrate_data.py --profile spp`
reported this is a FULL clone — every blob already local, nothing to hydrate.

---

## 3. THE DERATE LINE — verbatim

The overlay **fired**. The line appears twice (once per pass, P0 and P1),
byte-identical both times:

```
INFO: short unit-outage derate (SPP 2025): 218 plant-tranches derated (< 5-day baseload-coal windows)
```

**218 plant-tranches derated.**

Context — the adjacent `>= 5-day` overlay line, unchanged by this arm, for
scale:

```
INFO: unit-outage derate (SPP 2025): 303 plant-tranches derated
```

### The gas scope really entered — the log string alone does not prove it

The trailing parenthetical `(< 5-day baseload-coal windows)` is a **static
format string** in `src/market_sim/data/fleet/arrays.py` (~line 1370); it says
"baseload-coal" whether or not `gas_scope` was passed, so the 218 could in
principle have been coal-only. A zero-LP call to
`market_sim.data.outages.unit_outage_short_derate_factors(2025, 8760, iso="SPP")`
settles it at both scopes:

| `gas_scope` | `(plant, group)` keys returned | breakdown |
|---|---|---|
| `False` | 23 | COAL 23 |
| `True` | **55** | COAL 23 · CC_REGULAR 18 · ST_GAS 13 · CC_CHP 1 |

So the gas family adds **32 plant-groups** on top of the 23 coal ones — the
COAL scope is unchanged (23 either way, i.e. the widening genuinely stacks
nothing on coal, as the function's docstring claims), and the arm's 218
derated **generator tranches** are the fan-out of all 55 plant-groups across
the per-plant tranche split. Both `--set` flags were therefore load-bearing, as
the shard prompt said.

---

## 4. P1 annual TWh by class

From `results/calibration/spp32_B_2025/hourly/class_hourly_2025.parquet`,
`pass == "P1"`, `sum(mw) / 1e6`. Control column = keeper 9, 2025, P1 (supplied
in the shard prompt; **not tuned toward or away from**).

| klass | arm B (TWh) | control (TWh) | Δ |
|---|---|---|---|
| wind | 122.0286 | 122.0210 | +0.0076 |
| COAL_PRB | 78.9808 | 80.4149 | **-1.4341** |
| CC_REGULAR | 33.0623 | 34.9097 | **-1.8474** |
| CT_PEAKER | 18.0015 | 14.2422 | **+3.7593** |
| nuclear | 15.7804 | 15.7804 | -0.0000 |
| ST_GAS | 11.5669 | 12.0198 | -0.4529 |
| hydro | 8.8205 | 8.8204 | +0.0001 |
| COAL_LIGNITE | 6.7714 | 6.7981 | -0.0267 |
| solar | 2.3248 | 2.3244 | +0.0004 |
| CC_CHP | 1.8779 | 1.9343 | -0.0564 |
| CT_CHP | 1.1698 | 1.1487 | +0.0211 |
| biomass | 0.9490 | 0.9490 | +0.0000 |
| OTHER | 0.4891 | 0.4891 | -0.0000 |
| ST_CHP | 0.2035 | 0.1760 | +0.0275 |
| oil | 0.0018 | 0.0000 | +0.0018 |
| **TOTAL** | **302.0282** | **302.0280** | **+0.0002** |

Every class in the parquet is listed; `pass` contains only `P1` (the bundle
carries no P0 rows in this sidecar).

---

## 5. P1 system metrics

From `results/calibration/spp32_B_2025/hourly/system_2025.parquet`,
`pass == "P1"` (zones: `SPP-North`, `SPP-South`; 17,520 rows = 2 zones × 8,760 h).

| metric | arm B | control |
|---|---|---|
| total `slack` | **10,911.0219 MWh** | 0.0000 MWh |
| total `dump` | 0.0000 MWh | 0.0000 MWh |
| total `demand` | 301.8402 TWh | 301.8402 TWh |
| load-weighted mean price `sum(price*demand)/sum(demand)` | **33.1683** | 28.7893 |
| mean over hours of MAX zonal price | 34.5715 | — |
| MAX zonal price | **2000.0000** | 73.7731 |
| count of hours with max zonal price > 200 | **18** | 0 |

### Monthly load-weighted mean price (hour 0 = 2025-01-01 00:00)

| month | $/MWh |
|---|---|
| 01 | 41.7184 |
| 02 | 35.7015 |
| 03 | 24.9109 |
| 04 | 22.6112 |
| 05 | 28.4207 |
| 06 | 29.6368 |
| 07 | 34.2319 |
| 08 | 30.6596 |
| 09 | 37.6832 |
| 10 | 35.4259 |
| 11 | 29.1657 |
| 12 | 43.8373 |

---

## 6. Arm `run_config.json` → `scenario_config`

| field | arm B | control |
|---|---|---|
| `unit_outage_short_windows` | `True` | `False` |
| `unit_outage_short_windows_gas` | `True` | *absent* |
| `mustrun_window_commitment_grain` | `True` | `True` |
| `wefor_multiplier` | `0.7` | `0.7` |
| `offer_curve_by_group.CC_REGULAR` | `{committed 0.93, econ_high 0.93, econ_low 0.93, peak 0.93, econ_low_share 0.5, pct_peaking 8.0}` | identical |

**`offer_curve_by_group` is byte-identical to the control's** — verified by
comparing `json.dumps(..., sort_keys=True)` of the whole mapping, not just the
`CC_REGULAR` entry: `True`. No offer-curve channel was touched (rules 1/13).

Full `scenario_config` diff against the control, for completeness — differing
shared keys:

| key | control | arm B | why |
|---|---|---|---|
| `unit_outage_short_windows` | `false` | `true` | **the arm** |
| `weather_year` | `2023` | `2025` | the control config snapshot is the span's first year; this shard solves 2025 |
| `gas_price_override` | `2.54` | `3.52` | per-year value the replay sets for 2025 |

Keys present in the arm and absent from the control:
`unit_outage_short_windows_gas` (`True` — the arm) and
`mustrun_chp_btm_holdout` (`False`, i.e. at its default — a `ScenarioConfig`
field newer than the keeper's snapshot, inert here).

---

## 7. What surprised me

### **SLACK IS NON-ZERO: 10,911.0219 MWh. The control's is 0.0000 MWh.**

This is a real adequacy signal and I am not absorbing it. It is the headline
result of this screen, ahead of any dispatch delta.

- **All of it is in `SPP-South`** (`SPP-North` slack = 0.0000 MWh).
- It lands in **12 hours**, in three tight clusters, every one of them priced
  at VOLL 2000 $/MWh:

| cluster | hours | slack MWh |
|---|---|---|
| 2025-09-15 13:00–15:00 | 6181–6183 | 537.26 · 598.63 · 411.21 |
| 2025-10-06 14:00–16:00 | 6686–6688 | 695.36 · 1,113.96 · 1,073.02 |
| 2025-12-21 09:00–14:00 | 8505–8510 | 30.18 · 1,268.89 · 2,038.54 · 1,425.23 · 1,247.21 · 471.53 |

- The 18 hours above 200 $/MWh are all at 2000 exactly, i.e. the VOLL
  slack price, and they bracket the 12 slack hours (four more hours at 2000
  with zero slack — binding at the margin without spilling).
- Consequence for the price metrics: the load-weighted mean rises
  28.7893 → 33.1683 (+4.379, +15.2 %) and the max zonal dual goes
  73.7731 → 2000.0000. **The entire price move is scarcity-driven**, not a
  merit-order shift — the September/October/December clusters are what moved
  the annual mean.

Other things worth stating plainly:

1. **The dispatch response has the direction the mechanism's arithmetic
   implies, and the magnitude is much larger on gas than the coal-only arm
   could produce.** Derating short gas outage windows pushes 1.85 TWh out of
   CC_REGULAR, 0.45 out of ST_GAS and 1.43 out of COAL_PRB, and 3.76 TWh of it
   lands on CT_PEAKER. The footprint is confined to thermal classes the
   overlay claims: wind/solar/hydro/nuclear/biomass/OTHER move by ≤ 0.008 TWh
   (rounding and the storage/flow seam), and the totals match to +0.0002 TWh.
2. **`oil` goes 0.0000 → 0.0018 TWh and `ST_CHP` +0.0275 TWh.** Small, but oil
   starting from an exact zero in the control means the arm pulled in a class
   the control never needed — the same stress the slack reports.
3. **`dump` stayed exactly 0.0000 MWh** in both arms, so nothing here is a
   negative-price/oversupply artifact.
4. The legitimacy-diagnostics gate reported **FAIL** on the replayed bundle
   (`WARNING: legitimacy diagnostics gate FAIL on the replayed bundle`), with
   D-5, D-9 and D-10 individually PASS in the printed report. I did not chase
   this down — out of shard scope, and the artifact was still written to
   `results/calibration/spp32_B_2025/legitimacy_diagnostics.json`.
5. The `unit_outage_short_derate_factors` signature takes `hours` as an **int**
   (`hours: int = HOURS_PER_YEAR`), not an hour array — worth knowing for
   anyone writing a zero-LP probe against it. Nothing was edited.

### One thing the parent needs to action (the rule 29(c) / rule 31 seam)

**The screen bundle `results/calibration/spp32_B_2025/` is NOT gitignored.**
`git check-ignore -v results/calibration/spp32_B_2025/run_config.json` returns
NOT IGNORED, and `.gitignore` covers `/results/<ISO>/` cache dirs and several
named scratch families but no pattern reaching a `results/calibration/spp32_*`
bundle. It is therefore sitting as untracked (`??`) in `git status`.

That is harmless from this shard — I staged and committed exactly one file and
the bundle never reaches `main` from here — but it is the exact collision rule
29 `[R-SCREEN]` clause (c) records: the duty is discharged by `.gitignore`, not
by `rm` (rule 31 `[R-RETAIN]`), and the ignore entry does not currently exist.
**The parent owns this seam.** A `.gitignore` line for the SPP-32 screen bundle
family would discharge clause (c) properly; I did not add one because this
shard is permitted to commit one file only, and adding it would have been a
second.

### Housekeeping

No file under `src/` or `scripts/` was modified. No result was deleted (rule 31
`[R-RETAIN]`) — the screen bundle `results/calibration/spp32_B_2025/` is on
local disk, untracked, and **will not survive this container's reclamation**.
If the parent wants arm B's numbers to be reproducible without a re-solve, that
has to be acted on while this session is alive. Nothing under `results/`,
`frontend/data/backcast/`, `CLAUDE.md`, `calibration-complete.json` or any
keeper shard was committed or touched. No PR was opened. The solve was run
once, with exactly the flags above, and not re-run with variants.
