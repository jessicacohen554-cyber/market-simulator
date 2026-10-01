# SHARDREPORT — SPP-36 shard 1 of 3 (year 2023)

**OUTCOME: NO SOLVE. The shard STOPPED on a pre-existing `scripts/` defect at the pinned
revision. No bundle was produced, nothing was registered, and the SPP-36 chain is BLOCKED for
every shard and every year until the defect is repaired by a lane authorized to edit `scripts/`.**

This shard did not patch anything (rule 27 `[R-PUSH]` model-assignment / shard prompt: "ANY edit
under `src/` or `scripts/` — if something looks broken, STOP and report it, do not patch it").

---

## 1. Revision and hard stops

`git rev-parse HEAD` → `25160fed20777238d20ee7aa8bf508a6ee557686`

| Hard stop | Verdict | Evidence |
|---|---|---|
| **1 — pinned revision** | **PASS** | HEAD is exactly `25160fed20777238d20ee7aa8bf508a6ee557686`. No pull, rebase, sync or merge was performed at any point. |
| **2 — control config signature** | **PASS** | See table below. |
| **3 — the extract** | **PASS** | `data/raw/campd-unit-outages-short-SPP.csv` = 621 lines / 620 data rows; `Counter({'COAL': 620})` — every row `plant_group` COAL. Not re-derived (rule 23 `[R-FROZEN-DERIVE]`). |

### Hard stop 2 detail — `results/calibration/spp27_span/run_config.json` → `scenario_config`

| Field | Required | Observed | |
|---|---|---|---|
| `mustrun_window_commitment_grain` | true | `True` | PASS |
| `unit_outage_short_windows` | **false** | `False` | PASS |
| `wefor_multiplier` | 0.7 | `0.7` | PASS |
| `mode` | "backcast" | `'backcast'` | PASS |
| `hindcast` | false | `False` | PASS |
| `campd_per_unit_attribution` | false | `False` | PASS |
| `campd_outage_merit_order_guard` | false | `False` | PASS |
| `offer_curve_by_group.CC_REGULAR` | committed/econ_low/econ_high/peak = 0.93 | `committed 0.93 · econ_low 0.93 · econ_high 0.93 · peak 0.93` | PASS |

Note on CC_REGULAR: the stored dict is
`{'committed': 0.93, 'econ_low': 0.93, 'econ_high': 0.93, 'peak': 0.93, 'econ_low_share': 0.5, 'pct_peaking': 8.0}`.
All four **band multipliers** are exactly 0.93 as the hard stop requires. The two extra keys are the
**structural shares** (`econ_low_share`, `pct_peaking`), which are not band multipliers and which the
hard stop does not enumerate — they are present on every group in this keeper's mapping. This is a
PASS, not a mismatch.

Control `offer_curve_by_group` (whole mapping) `json.dumps(..., sort_keys=True)` SHA-256:
`090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`
(recorded so the eventual arm can be compared byte-for-byte — see §6.)

---

## 2. The command, exit code, wall time

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2023 \
  --out-dir results/calibration/spp36_span \
  --set unit_outage_short_windows=true \
  --note "SPP-36 span year 2023: keeper 9 recipe + unit_outage_short_windows=true (COAL scope). Owner promotion ruling 2026-09-12. Chain link 1 of 3."
```

- **Exit code: 1** (uncaught `TypeError`).
- **Wall time: 29 s.** It died in fleet build → first solve dispatch, well before any LP work.
- `unit_outage_short_windows_gas` was NOT passed (matrix cell `R` for SPP), as instructed.
- Environment: no `.venv` present, so `python3 -m pip install --ignore-installed PyYAML -r requirements.txt`
  was run once (succeeded first try), and `python3` was used. `requirements.txt` was not edited.

### The traceback, verbatim

```
INFO: solving SPP 2023 (hours=8760, Henry Hub=$2.54/MMBtu, commitment=False)
Traceback (most recent call last):
  File "/home/user/market-simulator/scripts/replay_keeper.py", line 986, in <module>
    main()
  File "/home/user/market-simulator/scripts/replay_keeper.py", line 949, in main
    run_dir = rcf.solve_and_persist(**kwargs)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/user/market-simulator/scripts/run_calibration_full.py", line 5491, in solve_and_persist
    result, context, result_p1, p2_state = run_year(
                                           ^^^^^^^^^
TypeError: run_year() got an unexpected keyword argument 'unit_outage_window_hour_grain'
```

---

## 3. The overlay log line — **NOT PRESENT**

**The line `short unit-outage derate (SPP 2023): N plant-tranches derated` NEVER APPEARED.**

**However, this is NOT evidence that the overlay failed to fire, and it does NOT void the SPP-36
mechanism.** The process died at the `run_year(...)` *call site* — the very first statement of the
solve, reached immediately after `INFO: solving SPP 2023` — which is *upstream* of anywhere the
overlay could log. The overlay was never given the chance to run. The mechanism is untested by this
shard, in either direction. Only 37 lines of log were produced in total, all of them fleet-build
warnings plus the traceback; `grep -n "grain"` over the whole log matches only the traceback line.

---

## 4–5. Arm dispatch, price and system numbers — **UNAVAILABLE**

No `results/calibration/spp36_span/hourly/*` was written. The only thing the run created is an
**empty** `results/calibration/spp36_span/dispatch/` directory. Per rule 31 `[R-RETAIN]` nothing was
deleted; per the shard prompt nothing under `results/` was committed.

The control numbers were read anyway (zero-LP, from the committed keeper) so the parent has the
baseline in hand and the next attempt only needs the arm column.

### Control — keeper 9 `spp27_span`, 2023, `pass == "P1"`

`class_hourly_2023.parquet`, annual TWh = `sum(mw)/1e6`:

| klass | Control TWh |
|---|---:|
| wind | 113.7294 |
| COAL_PRB | 65.6343 |
| CC_REGULAR | 41.8267 |
| nuclear | 16.9270 |
| CT_PEAKER | 15.7601 |
| ST_GAS | 9.6983 |
| hydro | 8.3441 |
| COAL_LIGNITE | 7.1781 |
| CC_CHP | 1.8472 |
| CT_CHP | 1.2030 |
| biomass | 1.1014 |
| solar | 0.5875 |
| OTHER | 0.5072 |
| ST_CHP | 0.2922 |
| oil | 0.0000 |
| **TOTAL** | **284.6364** |

`system_2023.parquet`:

| Metric | Control |
|---|---:|
| total `slack` | **0.0000 MWh** |
| total `dump` | 0.0000 MWh |
| total `demand` | 284.5182 TWh |
| load-weighted mean price `sum(price*demand)/sum(demand)` | 25.3716 |
| MAX zonal price | 59.3126 |
| hours with max zonal price > 200 | 0 |

Monthly load-weighted mean price (hour 0 = 2023-01-01 00:00):

| Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 30.9887 | 21.8387 | 21.5219 | 15.2953 | 23.9649 | 27.1043 | 29.4520 | 31.0644 | 27.3616 | 22.5628 | 24.0971 | 24.1142 |

These reproduce the three values the shard prompt supplied as known (slack 0.0000, max zonal dual
59.3126, hours > $200 = 0) **exactly**, which confirms the control bundle and the reader script agree.

---

## 6. Arm `scenario_config` — **UNAVAILABLE**

No `run_config.json` was written for the arm, so the required fields cannot be reported and the
`offer_curve_by_group` byte-identity comparison against the control **could not be performed**. The
control-side hash is recorded in §1 so the next attempt can settle it in one line.

---

## 7. What surprised me — the defect, and why it blocks the whole chain

**`slack` could not be checked** (no arm). The control's 2023 slack is 0.0000 MWh, as stated.

The real finding is the defect. It is **pre-existing at the pinned revision, unconditional, and
unrelated to this shard's `--set`**:

- `run_year` is defined at `scripts/run_calibration.py:512`. It takes **302** parameters and has
  **no `**kwargs`** and no `*args` (verified by AST).
- `solve_and_persist` calls it at `scripts/run_calibration_full.py:5491` with **297 keyword
  arguments and no `**` spread**. Binding those 297 names against the 302 accepted names leaves
  exactly one unmatched: **`unit_outage_window_hour_grain`**.
- That kwarg is passed at `run_calibration_full.py:5723` as a **plain, unconditional** element of the
  call expression — it is not inside any `if`. So the `TypeError` fires on **every** invocation of
  `solve_and_persist`, for **every ISO and every year**, whatever flags are set. My `--set
  unit_outage_short_windows=true` neither caused nor influenced it.
- Introduced by **`3497a1d8`** — *"Add unit_outage_window_hour_grain: the DETECTED-hour outage window
  (nyiso-229)"*, Sat Sep 12 2026, an ancestor of the pinned HEAD. Its stat shows it touched
  `run_calibration_full.py`, `scenarios.py`, `data/fleet/arrays.py`, `data/outages.py`,
  `data/resolved_inputs.py`, the matrix shards and a new test — **but NOT `scripts/run_calibration.py`**,
  where `run_year` lives. The parameter was added to the caller and to the config, and never to the
  callee.
- The keeper `spp27_span` records `git_sha 09d9fc00`, i.e. it was solved before this landed — which is
  why the control bundle exists and the replay of it does not.

**Blast radius.** Both entry points are dead, not just mine:
`replay_keeper.py::main` → `solve_and_persist`, and `run_calibration_full.py::main` (line 13902) →
`solve_and_persist`. `run_replay_bundle` (line 9022) only builds the kwarg conditionally, but it
feeds the same `solve_and_persist`, which then passes it on unconditionally. **No LP can be solved at
this revision through either runner**, so SPP-36 shards 2 and 3 will fail identically, and so will any
other lane replaying a keeper at this HEAD.

**The repair is one line** — add `unit_outage_window_hour_grain: bool | None = None` (or equivalent)
to `run_year` in `scripts/run_calibration.py` and thread it to the config, mirroring how the sibling
`unit_outage_*` flags are handled. **This shard did not make that change**, because `scripts/` is
outside a shard's remit and the fix belongs to a lane that can also re-run the test the introducing
commit shipped (`tests/data/test_unit_outage_window_hour_grain.py`). Note also that the CI/test suite
evidently did not catch a broken production solve path, which may be worth the parent's attention
separately.

**Recommended next step for the parent:** get `scripts/run_calibration.py` repaired and pinned at a
NEW sha, then relaunch all three SPP-36 shards against it. Nothing from this shard needs to be redone
— the control numbers in §4–5 are reusable as-is.
