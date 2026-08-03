# FFR-3A — FAILED LEG DEBRIS. **NOT A RUN. NOT A RESULT. NEVER REGISTER THIS.**

These four files are the aborted first attempt at the FFR-3A T1-F battery
(2026-08-03). They are kept **only** as primary evidence for the blocker written up
in `docs/handoffs/ffr-t1-regate-2026-08-02.md` §6.1. Nothing here was solved,
scored, registered, or cited as a measurement.

## What happened

Two T1-F legs (NEISO, NYISO; 2026–2030) were launched and died within ~33 s on:

```
RuntimeError: confirmed-retirements: clean partition for <ISO> is absent while
confirmed_exits_enabled is on in forecast mode. data/clean is derived and
gitignored, so a fresh checkout has no registry; refusing to silently degrade
to the economic screen (W1-B B3: ERCOT's 2026 fleet gains 477 MW — V H Braunig
backlog)
```

`data/clean` was **entirely empty** on this container. That is the blocker; the
loader behaved correctly by failing loud rather than silently degrading.

## How to read these files WITHOUT being misled

Each `full_horizon_summary.json` is honest — it carries the full `error` string,
`"n_solved_years": 0`, `"solved_years": []` and a null `cache_key`.

**The console line in the `.log` files is the trap.** Both print:

```
invariants: 0 FAIL, 0 WARN
```

Invariant scoring over a **zero-year** run passes trivially, so a hard failure
reads as a clean gate at a glance. **Key on `n_solved_years`, never on the
invariant line.**

## Before re-running the battery

Run `scripts/regenerate_clean.py` to completion and confirm it finished — it
executes ~50 per-datatype curation scripts sequentially and is a **prerequisite,
not a step**. The battery specification (per-ISO posture flags included) is fixed
in `docs/handoffs/ffr-t1-regate-2026-08-02.md` §4.3, §5 and §6.

Delete this directory once a real battery has run; it has no value beyond the
blocker record.
