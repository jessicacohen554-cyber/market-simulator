# SHARDREPORT — SPP-36 shard 1 of 3 (relaunch): span year 2023

Arm bundle: `results/calibration/spp36_span` (year 2023 only)
Control: `results/calibration/spp27_span` (SPP keeper 9), year 2023, P1
Recipe: keeper 9 + `unit_outage_short_windows=true` (COAL scope). Chain link 1 of 3.

## 1. Revision and hard stops

`git rev-parse HEAD` = `706aa5475a44e2bb87326a556833f326f926160b`

| Hard stop | Result |
|---|---|
| 1 — pinned revision `706aa547…` | **PASS** (exact match; no pull/rebase/sync performed) |
| 2 — `tests/unit/pipeline/test_run_year_kwarg_binding.py` | **PASS** — `4 passed in 0.56s` |
| 3 — control config signature | **PASS** — all nine fields as specified (see below) |
| 4 — `data/raw/campd-unit-outages-short-SPP.csv` | **PASS** — 621 lines / 620 data rows, `plant_group` COAL on all 620 |

Hard stop 3 detail, read from `results/calibration/spp27_span/run_config.json`:

```
mustrun_window_commitment_grain : True     OK
unit_outage_short_windows       : False    OK
wefor_multiplier                : 0.7      OK
mode                            : backcast OK
hindcast                        : False    OK
campd_per_unit_attribution      : False    OK
campd_outage_merit_order_guard  : False    OK
offer_curve_by_group.CC_REGULAR : committed 0.93 · econ_low 0.93 · econ_high 0.93 · peak 0.93   OK
```

Environment note: no `.venv` existed, so dependencies were installed with
`python3 -m pip install --ignore-installed PyYAML -r requirements.txt` and `python3` used.
`requirements.txt` was **not** edited. `pytest` is not in `requirements.txt`, so it was
additionally pip-installed in order to execute hard stop 2; no repo file was changed.

## 2. The solve

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2023 \
  --out-dir results/calibration/spp36_span \
  --set unit_outage_short_windows=true \
  --note "SPP-36 span year 2023: keeper 9 recipe + unit_outage_short_windows=true (COAL scope). Owner promotion ruling 2026-09-12. Chain link 1 of 3."
```

Exit code **0**. Wall time **174 s**.

Container preflight (runner-owned, `--no-container-preflight` NOT passed):

```
INFO: container preflight: memory ceiling 13.34 GiB (…/claude-code-bash/memory.limit_in_bytes; MemTotal 15.70 GiB), swap 0.0 GiB, target ceiling+swap 24 GiB
INFO: container preflight: provisioned 9 GiB swap at /swapfile-marketsim — ceiling 13.34 + swap 9.0 = 22.3 GiB
INFO: container preflight: solve profile MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1
WARNING: container preflight: ceiling+swap 22.3 GiB is below the 24 GiB target; a per-plant ISO-year LP (MISO, PJM) may be OOM-killed here
INFO: memory peak: cgroup_peak_rss_gib=5.15, cgroup_peak_rss_plus_swap_gib=5.15, process_vmhwm_gib=4.60, process_vmswap_now_gib=0.00
```

The 24 GiB-target warning is inert here — SPP is not a per-plant ISO and the solve peaked at
5.15 GiB, well under the 13.34 GiB ceiling with no swap touched.

## 3. The overlay log line — VERBATIM

```
INFO: short unit-outage derate (SPP 2023): 80 plant-tranches derated (< 5-day baseload-coal windows)
```

It appears **twice** (log lines 72 and 95 — once per pass, P0 and P1), identically.
**The overlay fired.** The chain is not void on this leg.

For scale, the pre-existing long-window overlay in the same run reports
`unit-outage derate (SPP 2023): 302 plant-tranches derated`; the short-window overlay adds 80.

## 4. Annual TWh per class, P1 (`hourly/class_hourly_2023.parquet`, `sum(mw)/1e6`)

| klass | arm | control | delta |
|---|---:|---:|---:|
| CC_CHP | 1.8527 | 1.8472 | +0.0055 |
| CC_REGULAR | 42.5693 | 41.8267 | **+0.7425** |
| COAL_LIGNITE | 6.8735 | 7.1781 | **−0.3046** |
| COAL_PRB | 63.9116 | 65.6343 | **−1.7227** |
| CT_CHP | 1.2143 | 1.2030 | +0.0113 |
| CT_PEAKER | 16.6146 | 15.7601 | **+0.8545** |
| OTHER | 0.5072 | 0.5072 | 0.0000 |
| ST_CHP | 0.3097 | 0.2922 | +0.0175 |
| ST_GAS | 10.0952 | 9.6983 | **+0.3970** |
| biomass | 1.1014 | 1.1014 | 0.0000 |
| hydro | 8.3441 | 8.3441 | 0.0000 |
| nuclear | 16.9270 | 16.9270 | 0.0000 |
| oil | 0.0000 | 0.0000 | 0.0000 |
| solar | 0.5875 | 0.5875 | 0.0000 |
| wind | 113.7294 | 113.7294 | 0.0000 |
| **TOTAL** | **284.6374** | **284.6364** | +0.0010 |

Every control value reproduces the known-good figures in the shard brief exactly, to 4 dp.

Direction: coal down 2.0273 TWh (COAL_PRB −1.7227 + COAL_LIGNITE −0.3046), gas up 2.0108 TWh
(CC_REGULAR +0.7425 + CT_PEAKER +0.8545 + ST_GAS +0.3970 + CHP classes +0.0343). Energy-limited
and zero-MC classes (wind, solar, nuclear, hydro, biomass, OTHER, oil) are untouched to 4 dp,
as a coal-scoped availability derate should leave them.

## 5. System, P1 (`hourly/system_2023.parquet`)

`system_2023.parquet` is per zone-hour (`year, pass, zone, hour, price, slack, dump, demand, reserve_price`).
"MAX zonal price" is the max over all zone-hour rows; "hours > 200" counts hours whose **max across
zones** exceeds 200.

| metric | arm | control |
|---|---:|---:|
| total `slack` | **0.0000 MWh** | 0.0000 MWh |
| total `dump` | 0.0000 MWh | 0.0000 MWh |
| total `demand` | 284.5182 TWh | 284.5182 TWh |
| LW mean price `sum(price*demand)/sum(demand)` | **25.7428** | 25.3716 |
| MAX zonal price | 61.4221 | 59.3126 |
| hours with max zonal price > 200 | **0** | 0 |

**`slack` is 0.0000 MWh** — matching the control exactly. No loss of load.

Monthly load-weighted mean price (hour 0 = 2023-01-01 00:00):

| month | arm | control |
|---|---:|---:|
| 1 | 31.6073 | 30.9887 |
| 2 | 22.6475 | 21.8387 |
| 3 | 21.8400 | 21.5219 |
| 4 | 15.4452 | 15.2953 |
| 5 | 24.2152 | 23.9649 |
| 6 | 27.3221 | 27.1043 |
| 7 | 29.8787 | 29.4520 |
| 8 | 31.4403 | 31.0644 |
| 9 | 27.6653 | 27.3616 |
| 10 | 22.9455 | 22.5628 |
| 11 | 24.3838 | 24.0971 |
| 12 | 24.4197 | 24.1142 |

Every month moves up, by +0.15 to +0.81 $/MWh; the
largest lifts are January (+0.6186) and February (+0.8088).

## 6. Arm `scenario_config`

```
unit_outage_short_windows        : True
unit_outage_short_windows_gas    : False      <- NOT passed; matrix cell R for SPP, stays off
unit_outage_window_hour_grain    : False
mustrun_window_commitment_grain  : True
wefor_multiplier                 : 0.7
offer_curve_by_group.CC_REGULAR  : {'committed': 0.93, 'econ_low': 0.93, 'econ_high': 0.93,
                                    'peak': 0.93, 'econ_low_share': 0.5, 'pct_peaking': 8.0}
```

`offer_curve_by_group` whole-mapping comparison, `json.dumps(..., sort_keys=True)`:

- arm SHA-256: `090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`
- control SHA-256 (as stated in the brief): `090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`

**Byte-identical — confirmed by direct string equality of the whole mapping, not only the hash.**
No offer-curve channel moved on this leg.

## 7. Surprises

1. **`legitimacy diagnostics gate FAIL` on the replayed bundle** — the runner emitted
   `WARNING: legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written;
   C7/C8 score from its contents)`. It is **D-4 off-window binding**, and it is **pre-existing in
   the control**, not introduced by this overlay: the arm's 2023 D-4 has 4 FAIL rows, all
   `st_gas_mustrun_per_plant × ST_GAS`, window `h0-23`, plants 1230 / 1235 / 1271 / 3008; the
   committed control bundle carries the **same four 2023 rows** (12 FAIL across its three years).
   Off-window shares are essentially unchanged (1230: 0.0057 → 0.0056; 1235: 0.0054 → 0.0054;
   1271: 0.0024 → 0.0024; 3008: 0.0146 → 0.0147). The mechanism is ST_GAS must-run, unrelated to
   the COAL-scoped short-outage overlay. D-1, D-2, D-5, D-9 and D-10 all PASS. Flagged, not acted
   on — scoring is the parent's job.
2. **Total generation rises 0.0010 TWh while demand is bit-identical.** Coal −2.0273 TWh is not
   quite offset by gas +2.0108 TWh at 4 dp; the residual is round-trip/loss accounting, ~0.4 ppm
   of load. Noted only because the deltas otherwise net so cleanly.
3. **The overlay's price signature is uniform across the year**, not concentrated in the months one
   might expect coal outages to bite hardest. Every one of the twelve months moves up, and the two
   largest lifts are January and February — winter, when the derated PRB tranches are most
   load-bearing.
4. `replay_keeper.py` announces `replaying results/calibration/spp27_span (SPP [2023, 2024, 2025])`
   in its first log line even under `--years 2023`; only 2023 artifacts were produced. Cosmetic.

## 8. What was NOT done

No edits under `src/` or `scripts/`. No re-derivation of the extract. No gas scope. No registration
(`dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, anything under
`frontend/data/backcast/**`) — the parent's job at the end of the chain. No PR. No deletions under
`results/` (rule 31 `[R-RETAIN]`): the full bundle, including `dispatch/`, `unit_hourly_2023.parquet`,
`network_2023.parquet`, `floors/`, `btm.parquet`, `flows.parquet`, `storage.parquet` and
`system.parquet`, remains on this container's local disk **uncommitted** and will not survive
container reclamation. `hourly/reserve_family_2023.parquet` was not produced by this solve, so it is
not in the commit; `legitimacy_diagnostics.json` was produced and is included.
