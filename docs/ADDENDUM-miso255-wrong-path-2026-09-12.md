# ADDENDUM 2 to PRECOMMIT-miso255-measured-sil — **the arm was wired to the FORECAST path
# and was silently inert in every backcast replay. A shard caught it.**

**Written and pushed BEFORE the re-launched shards solve** (rule 29 `[R-SCREEN]`). No screen year,
gate, gate value or direction check from the PRECOMMIT §2/§3 is renegotiated. Only the pin moves.

## 1. THE DEFECT

`ScenarioConfig.miso_import_sil_measured_envelope` was consumed in exactly one place:
`src/market_sim/runner.py::run_scenario_iso`. **That is the forecast/scenario front end.** The
backcast/calibration path — `scripts/run_calibration.py::run_year`, which is what
`replay_keeper.py` and `run_calibration_full.solve_and_persist` drive — **builds its own
`interface_groups`** (line ~3146) and never enters `run_scenario_iso` at all.

So the flag parsed, routed through both `--set` channels, appeared correctly in the recorded
`run_config.json`, moved the cache key, and **changed nothing in the LP**. A screen shard would
have solved a byte-identical copy of its own control and reported it as an arm.

`run_calibration.py` already carries a comment recording this exact trap for a different
mechanism — "…ONLY into runner.py::run_scenario_iso — the forecast/scenario path — so a …
`pipeline.solve.run_energy_solve`, silently ignored the flag." I walked into it anyway.

**It was found by SHARD miso255-sil-2021 (the first relaunch), which investigated instead of
assuming and reported: "SIL flag unused in backcast path — wiring out of shard scope; parent must
add consumer and re-pin SHA."** That is rule 32(c)(7) working exactly as intended — a shard that
stops with a clear report is a success. Its sibling independently stopped at **HARD STOP 4**, the
G-1 liveness marker, which is the gate that exists for precisely this failure and which caught it
from the other direction. Both shards are archived; neither pushed anything.

**Cost:** four shard-solves' worth of container time, no bad artifact, no wrong number, nothing
registered. The pre-registered liveness gate did its job.

## 2. THE REPAIR

Three parts, all structural, no gate touched:

1. **The consumer now exists on the backcast seam**, immediately after the MISO seasonal CIL/CEL
   block in `run_calibration.py`, gated `iso == "MISO" and config.miso_import_sil_measured_envelope`,
   with the same `logger.info` marker text the shards grep for and an explicit `logger.warning`
   naming the run as **NOT an armed run** when no envelope resolves.
2. **The injector is re-keyed off the list that BUILT the groups.** It previously located
   `MISO_simultaneous_import` by index into `iso_config.interface_limits`. On the backcast path
   that is wrong: the MISO seasonal block rebuilds `interface_groups` from
   `static_limits + seasonal_groups`, so the config's own list addresses a DIFFERENT row. The
   signature is now `apply_miso_measured_sil_envelope(interface_groups, limits, …)` and
   `run_calibration.py` threads a new `effective_interface_limits` that is reassigned wherever the
   groups are rebuilt. Had I only added the consumer without this, the repair would have replaced
   the wrong interface row — a worse defect than the one it fixed, and silent.
3. **A guard that would have caught it**:
   `tests/iso/miso/test_miso_measured_sil_envelope.py::test_the_backcast_path_consumes_the_flag_not_only_the_forecast_path`
   asserts both entry points reference the injector AND that the backcast call passes
   `effective_interface_limits` (checked by AST, not by string match). A gated mechanism no
   backcast reads is an unregistered tuning channel in spirit (rule 24 `[R-REGISTRY]`).

**Unchanged and re-verified:** 190 MISO tests pass; all four committed MISO bundles keep their
cache keys byte-identical (`fefc0cdea485423b` / `244d810e992fcd33` / `466a72f1eafd28b7` /
`d92fa22309158cf4`); the flag is still default-off and every other ISO still a no-op by
construction and by test.

## 3. WHAT THIS SAYS ABOUT THE PRECOMMIT

**G-1 is vindicated and stays exactly as written.** It was put in as the cheap check against a
silently unarmed run, and it caught a silently unarmed run on its first outing. The AST
call-binding check that caught ADDENDUM 1's defect and the G-1 marker that caught this one are now
both mandatory pre-solve hard stops in the shard prompt.

**The 2022-B shard could not be interrupted** (the auto-mode classifier refused). It is solving the
unarmed tree and will stop at HARD STOP 4 with the marker absent, which is the correct outcome and
costs nothing beyond its own container time. Its result must NOT be read as an arm.

## 4. A SECOND, UNRELATED REPORT TO CARRY FORWARD

Shard miso255-sil-2022 (first relaunch) also reported **`ENOSPC`** — disk exhaustion on its
container, alongside the inert-flag stop. Not diagnosed here and not this lane's object; recorded
so a successor does not treat it as new. The runner's own container preflight provisions swap up to
24 GiB bounded by free disk (`scripts/lib/solve_container.py`), so a container that is already
short on disk can fail there rather than in the LP.
