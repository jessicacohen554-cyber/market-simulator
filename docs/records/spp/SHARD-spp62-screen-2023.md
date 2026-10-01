# SHARD spp62 — SPP 2023 screen (SPP-62 Shard A)

Rule 29 `[R-SCREEN]` single-year SCREEN of `eia860_vintage_tracks_solve_year=true`
over the R-ay coal-census repair, replayed from the `spp52a_fossil93` keeper recipe.
**Throwaway diagnostic probe — never registered, never a keeper.** Bundle left on disk
per rule 31 `[R-RETAIN]`; the out-dir is gitignored by design.

## Pin

```
$ git rev-parse HEAD
67feede7403240374091cc73a536d836ba6d08c4
```

Matches the required pin. No `git pull` / `rebase` / `merge` / `fetch` was run.

## HARD STOP 1 — the pin

PASS. `HEAD == 67feede7403240374091cc73a536d836ba6d08c4`.

## HARD STOP 2 — the config signature

PASS on every leg.

```
vintage_arm_before = False
CC_REGULAR [0.93, 0.93, 0.93, 0.93]
CC_CHP [0.93, 0.93, 0.93, 0.93]
CT_CHP [0.93, 0.93, 0.93, 0.93]
CT_PEAKER [0.93, 0.93, 0.93, 0.93]
ST_GAS [0.93, 0.93, 0.93, 0.93]
COAL [0.93, 0.93, 0.93, 0.93]
COAL_BIT [0.93, 0.93, 0.93, 0.93]
COAL_LIGNITE [0.93, 0.93, 0.93, 0.93]
COAL_PRB [0.93, 0.93, 0.93, 0.93]
COAL_WC [0.93, 0.93, 0.93, 0.93]
```

Census repair present:

```
$ wc -l data/raw/_processed-legacy/coal_supply_SPP.csv
32 data/raw/_processed-legacy/coal_supply_SPP.csv
$ grep -c "^6193,prb," data/raw/_processed-legacy/coal_supply_SPP.csv
1
```

## HARD STOP 3 — the arm actually armed

PASS.

```
$ .venv/bin/python -c "import json;print(json.load(open('results/calibration/spp62_screen_2023/run_config.json'))['scenario_config']['eia860_vintage_tracks_solve_year'])"
True
```

## The solve

```
.venv/bin/python scripts/replay_keeper.py results/calibration/spp52a_fossil93 \
  --years 2023 \
  --out-dir results/calibration/spp62_screen_2023 \
  --set eia860_vintage_tracks_solve_year=true \
  --note "SPP-62 rule-29 SCREEN: eia860_vintage_tracks_solve_year over the R-ay coal-census repair. Throwaway diagnostic probe, never registered."
```

Wall clock: **150 s = 2.5 minutes** (exit code 0). Well inside the rule 32 `[R-SHARD]`
20-minute shard budget.

## Measurements (verbatim)

```json
{
 "year": 2023,
 "class_twh": {
  "CC_CHP": 1.8535,
  "CC_REGULAR": 42.4877,
  "COAL_LIGNITE": 7.2935,
  "COAL_PRB": 66.8769,
  "CT_CHP": 1.2108,
  "CT_PEAKER": 16.2967,
  "OTHER": 0.5072,
  "ST_CHP": 0.3027,
  "ST_GAS": 7.0867,
  "biomass": 1.1014,
  "hydro": 8.3441,
  "nuclear": 16.927,
  "oil": 0.0,
  "solar": 0.5876,
  "wind": 113.7572
 },
 "bare_COAL_twh": 0.0,
 "total_gen_twh": 284.633,
 "system_demand_twh": 284.5182,
 "C3a_load_weighted_mean_price": 25.6527,
 "C3b_monthly_lw_nrmse": 0.1723,
 "model_monthly_price": [
  31.249,
  22.245,
  21.675,
  15.434,
  24.031,
  27.411,
  29.924,
  31.468,
  27.746,
  22.806,
  24.272,
  24.358
 ]
}
```

## metrics.json

**Not present.** `results/calibration/spp62_screen_2023/metrics.json` does not exist —
`replay_keeper.py` wrote no scoring sidecar for this bundle. The bundle contains:

```
btm.parquet  dispatch/  floors/  flows.parquet  hourly/
legitimacy_diagnostics.json  meta.json  run_config.json  storage.parquet  system.parquet
```

`legitimacy_diagnostics.json` IS present and its D-4 / D-5 / D-9 / D-10 tables all
read PASS (D-10 flags 2023 solar as `delivered_pinned`, advisory-only as usual for SPP).

## Notes for the parent

- Bare `COAL` class is **0.0 TWh** — all SPP coal lands in `COAL_PRB` (66.8769) and
  `COAL_LIGNITE` (7.2935), total coal 74.1704 TWh.
- Total generation 284.633 TWh vs system demand 284.5182 TWh (+0.1148 TWh, 0.04 %).
- Environment note: `pip install -e .` failed twice on a PyPI read timeout inside
  build-dependency isolation; installed with `--no-build-isolation` after adding
  setuptools/wheel to the venv. **No repository file was edited.**
