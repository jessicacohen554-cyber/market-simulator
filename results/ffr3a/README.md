# FFR-3A lane record — run outputs here are **gitignored and unregistered**

This directory is the `--out-dir` root for the FFR-3A T1 re-gate battery
(2026-08-03). Everything under it except this file is **gitignored**, matching the
convention for every other forecast lane (`/results/ffr1a/`, `/results/full-horizon/`,
`/results/d9-ab/`, …): forecast legs are registered to `frontend/data/forecast/` via
`scripts/register_forecast_run.py`, **never** as tracked bundles here (CLAUDE.md rule 15).

**Nothing in this directory is a registered result.** The lane's findings live in
`docs/handoffs/ffr-t1-regate-2026-08-02.md`.

## History of this directory

**First attempt — aborted (blocker).** Two T1-F legs (NEISO, NYISO) were launched and died
within ~33 s because `data/clean` was **entirely empty** on a fresh container:

```
RuntimeError: confirmed-retirements: clean partition for <ISO> is absent while
confirmed_exits_enabled is on in forecast mode. data/clean is derived and
gitignored, so a fresh checkout has no registry; refusing to silently degrade
to the economic screen (W1-B B3: ERCOT's 2026 fleet gains 477 MW — V H Braunig
backlog)
```

The loader was right to fail loud. Those four debris files were briefly committed as
evidence and are now untracked — superseded by a real run, with the error preserved verbatim
above and in the handoff §6.1.

**Blocker cleared.** `scripts/regenerate_clean.py` completed: **50 datatypes, 0 failures,
≈55 min wall, 446 parquet files / 1.6 GB**, dominated by the CAMPD `emissions` extract at
~26.5 M rows per year. This is a **prerequisite, not a step** — budget for it.

## Reading a leg's output without being misled

Each `full_horizon_summary.json` is honest: on failure it carries the full `error` string,
`"n_solved_years": 0`, `"solved_years": []` and a null `cache_key`.

**The console line in the `.log` files is the trap.** A failed leg still prints:

```
invariants: 0 FAIL, 0 WARN
```

because invariant scoring over a **zero-year** run passes trivially — a hard failure reads as
a clean gate at a glance. **Key on `n_solved_years`, never on the invariant line.**

## Battery posture (handoff §4.3)

Neither available flag reproduces the shipped per-ISO capacity arm for all six ISOs, so the
battery splits them — this reproduces the **shipped** arm everywhere using existing flags
only, executing no unsigned decision:

* `--golden-posture` → ERCOT, PJM, CAISO, NEISO, MISO
* plain default (no flag) → **NYISO** (production ships NYISO curve-OFF)

Rule 12: light ISOs pair, PJM solo, MISO solo, PJM and MISO never co-run, years sequential
within an invocation, ≤5 solve-years per invocation.
