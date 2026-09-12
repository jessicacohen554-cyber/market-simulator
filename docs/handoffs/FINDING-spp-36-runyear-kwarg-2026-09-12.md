# FINDING — STOP-THE-LINE: `run_year()` could not be called at HEAD. Every ISO's solve path was dead, and no test caught it.

**Found by** SPP-36 shard 1 (2023), which **stopped and reported instead of patching** — the shard
contract working exactly as rule 32 `[R-SHARD]` (c)(7) intends · **Verified independently in the
parent by AST before any repair** · **Repaired here** (rule 27 `[R-PUSH]` model assignment: a session
writing `scripts/run_*.py` is Opus/Fable; this one is Opus) · **LP spent: ZERO.**

## 1. THE DEFECT

`scripts/run_calibration_full.py::solve_and_persist` calls `run_year(...)` at **line 5491** with 297
keyword arguments and no `**` spread. `run_year` is defined once, at
**`scripts/run_calibration.py:512`**, takes **302** parameters and declares **no `**kwargs` and no
`*args`**. Binding the 297 names against the 302 accepted ones left exactly one unmatched:

```
TypeError: run_year() got an unexpected keyword argument 'unit_outage_window_hour_grain'
```

The kwarg is passed at `run_calibration_full.py:5723` as a **plain, unconditional** element of the
call expression — not inside any `if`. So the error fired on **every** `solve_and_persist`
invocation, for **every ISO and every year, whatever flags were set**, ~29 s in, before any LP work.

**Blast radius: both production entry points were dead** — `run_calibration_full.main` and
`replay_keeper.main`. `run_replay_bundle` builds the kwarg conditionally but feeds the same
`solve_and_persist`, which then passes it on unconditionally. **No LP could be solved at this
revision by any lane.**

**Introduced by `3497a1d8`** — *"Add unit_outage_window_hour_grain: the DETECTED-hour outage window
(nyiso-229)"*, 2026-09-12. Its diffstat touches `run_calibration_full.py`, `scenarios.py`,
`data/fleet/arrays.py`, `data/outages.py`, `data/resolved_inputs.py`, all seven matrix shards and a
199-line test — **but not `scripts/run_calibration.py`**, where the callee lives. The parameter was
added to the caller and to the config and never to the callee.

## 2. WHY NOTHING CAUGHT IT

The introducing commit shipped `tests/unit/data/test_unit_outage_window_hour_grain.py` — **15 cases,
all green, both before and after this repair**. None of them calls the solve path. The feature was
tested; the *binding* was not. `run_year` takes ~300 keywords across two runner modules of 7.3 k and
14 k lines, and a real call is minutes of LP, so nothing cheap exercised it.

## 3. THE REPAIR — two hunks in `scripts/run_calibration.py`, mirroring the sibling flags exactly

1. `unit_outage_window_hour_grain: bool | None = None,` added to `run_year`'s signature, immediately
   after `unit_outage_short_windows_gas` (302 → 303 parameters).
2. The matching `if unit_outage_window_hour_grain is not None: config = config.with_overrides(...)`
   block, placed next to `unit_outage_short_windows_gas`'s and carrying the same reason its siblings
   carry — *this* is the SOLVE path for the flag; `run_calibration_full`'s `_recorded_config` only
   records it, so an override missing here would solve the control twice.

**Byte-inert for every existing config**: the default is `None`, so no override is applied and no
`ScenarioConfig` value moves. No cache key changes (the field was already registered in
`_CACHE_KEY_OPTIONAL_FIELDS` and `_..._DEFAULTS` at `"False"` by the introducing commit). No keeper
re-scores. Zero free parameters (rule 21 `[R-DOF]`).

**Verified after the repair, by AST**: the set of keywords passed at the `run_year` call site minus
the set `run_year` accepts is now **empty**.

## 4. THE GUARD — `tests/unit/pipeline/test_run_year_kwarg_binding.py` (new)

Static, stdlib-only, milliseconds: parse both runner modules, collect the keywords at every literal
`run_year(...)` call site, and require each to be a declared parameter of the single `run_year`
definition. Plus two anti-vacuity cases — the call sites must still exist, and `run_year` must not
grow a `**kwargs` catch-all (which would swallow this class of bug silently).

**Proven against the defect, not merely written**: on the unrepaired tree it fails with exactly
`assert not ['unit_outage_window_hour_grain']`; on the repaired tree all four cases pass.

## 5. SCOPE, AND WHAT THIS LANE DID NOT DO

- **Nothing else was touched.** No behaviour change, no flag armed, no default flipped, no ISO's
  config moved. `unit_outage_window_hour_grain` remains `False` by default and reaches a
  `-perunitmerithour-<ISO>.csv` companion that exists only for NYISO.
- **The nyiso-229 feature is neither endorsed nor adjudicated here** — this lane restored the call
  binding it broke. Its matrix cells stay where nyiso-229 put them.
- **No `rm`, nothing deleted** (rule 31 `[R-RETAIN]`). SPP-36 shard 1 wrote only an empty
  `results/calibration/spp36_span/dispatch/` and committed nothing under `results/`.
- The shard's own control re-read (keeper 9, 2023, P1) reproduced the three values its prompt
  supplied as known — slack 0.0000 MWh, max zonal dual 59.3126, hours > $200 = 0 — confirming the
  control bundle and the reader agree. Those numbers are reusable; **nothing from shard 1 needs
  redoing** beyond the solve it never got to run.

## 6. CONSEQUENCE FOR SPP-36

The chain is unblocked at a NEW pinned SHA and all three shards relaunch against it. The
`PRECOMMIT-spp-36-shortwindow-span-2026-09-12.md` G-DRIFT audit is **unaffected in substance** — it
classified this same nyiso-229 change INERT *for the arm's numerics*, which remains true: the flag is
default-off and gated on two flags SPP has `False`. What the audit did not and could not detect is
that the change had broken the **call binding** for everyone. **A G-DRIFT hunk can be numerically
inert and still be fatal**; that is worth carrying forward into the next lane's audit, and it is the
one lesson here that generalises.
