# PERF-B Stage-0 Goldens — Staleness Ledger (2026-08-17)

Snapshot at `main` = `5b89e84` (2026-08-17, post-#4059). Requested by the PERF-B
director as input to the calibration-freeze escalation. Every "current keeper"
cell below was read directly from `frontend/data/backcast/keepers/<ISO>.json` at
this snapshot — none is inferred from PR titles. Golden capture facts come from
`results/regression-goldens/perfb-stage0/manifest.json` history.

## The ledger

| ISO | Golden at HEAD? | Captured against (keeper) | Keeper-shard blob sha at capture | Capture commit (UTC) | Solve tree | Current keeper at HEAD | Shard blob at HEAD | Verdict | Capture predates #4054 merge (03:37:25Z)? | Keeper arms `reliability_floor_plant_exclusions`? | Stale for the #4054 reason? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | yes | `2026-08-15-ercot204-rule26-delete` | `4d45c06` | `dd8b726` 2026-08-16T21:29:46Z | `ec413d20` | `2026-08-16-ercot213-arm-pubanchor` | `8563d73` | **STALE — keeper moved** | yes | no (`ercot213_anchor_B`: `False`; field did not exist in ercot204's config or at `ec413d20` at all) | no |
| CAISO | yes | `2026-08-16-caiso-197-w2-r5` | `2f934a3` | `af1ccb6` 2026-08-17T03:39:34Z | `2dd9dbc` (per commit msg; manifest stamps `9f6ff3e`) | `2026-08-16-caiso-197-w2-r5` | `2f934a3` (identical) | **CURRENT** | yes | no (field absent from recorded config; left at default in the re-solve) | no |
| PJM | **no golden** | — | — | — | — | `2026-08-15-pjm-162-inputclock` | `7154468` | NO GOLDEN (never captured in perfb-stage0; not in #4051 either) | n/a | no (field absent from its recorded config, which predates the mechanism) | n/a |
| MISO | **no golden at HEAD** (other lane's capture open in PR #4051) | #4051: `2026-08-15-miso-159-cod-vintage` | — (branch capture, tree `dd8b7265`) | #4051 head `0315a09` | `dd8b7265` | `2026-08-16-miso-160-wefor-shape` | `b0071e3` | NO GOLDEN at HEAD; **#4051's capture is STALE ON ARRIVAL** (miso-159 → miso-160; miso-161 measured only, no promotion) | yes | no (`miso160_wefor_B`: field absent) | no |
| NYISO | yes | `2026-08-16-nyiso-140-layup-exclusion` | `b78e1b1` | `9f6ff3e` 2026-08-17T03:04:23Z | `2dd9dbc` | `2026-08-16-nyiso-140-layup-exclusion` | `b78e1b1` (identical) | **CURRENT** — see §"#4054 premise, verified" for why the watch item does NOT stale it | yes | **YES** (`nyiso140_exclusion_arm`: `True` — the only armed keeper) | **no — override verified ACTIVE in the capture solve** |
| NEISO | yes | `2026-08-14-neiso-93-envelope` | `52473c7` | `c55d558` 2026-08-17T02:37:04Z | `ebd31a9` | **`2026-08-17-neiso-97-dstrepair`** | `1b948a1` | **STALE — keeper moved** (the handoff's "NEISO likely did NOT move" is wrong; promotion `d25925b` merged via #4055 at 03:37:05Z) | yes | no (`neiso97_dstrepair_A`: `False`) | no |

Headline: **2 STALE (ERCOT, NEISO — keeper movement), 2 CURRENT (CAISO, NYISO),
2 with no golden at HEAD (PJM never captured; MISO pending in #4051 and already
stale on arrival).**

## #4054 premise, verified (the watch item)

The watch item asserted: *"#4054 restored `reliability_floor_plant_exclusions`
in `run_year`, which was a SILENT NO-OP on main until 03:37 UTC. Any golden
captured before that commit ran with that override inert."* The timestamp half
is true — all four captures (and #4051's MISO solve) predate the #4054 merge
(`b65450c`, 2026-08-17T03:37:25Z) — and the column above records it. The
"therefore inert" half does **not** hold for these captures, for two
independently sufficient reasons, both verified in the capture trees:

1. **What was broken was only the named-kwarg channel.** The twin duplicate-
   param fixes (`6bb3a22` + `19f77d4`, per `92c74d7`'s own comment) removed
   `run_year`'s per-param override *block* while the parameter survived. The
   ScenarioConfig **field** and the **application site** —
   `_floor_specs = apply_reliability_floor_plant_exclusions(_floor_specs, config)`
   (`scripts/run_calibration.py:3364` in the `2dd9dbc` tree, `:3368` in
   `ebd31a9`) — were present and functional in every capture tree that had the
   field at all. The capture tool (`scripts/capture_keeper_goldens.py`,
   byte-unchanged between capture and HEAD) replays the keeper's recorded
   `scenario_config` dict verbatim through `config.with_overrides`, so the
   armed value reaches the apply site without ever touching the broken kwarg
   block.
2. **The capture lane's own tree had already restored the param.** `2dd9dbc`
   ("Restore run_year's reliability_floor_plant_exclusions param lost to twin
   fixes", 02:50:38Z) is an ancestor of the NYISO capture commit `9f6ff3e` and
   is the solve tree the NYISO and CAISO captures record.

Consequence per ISO: the only golden whose keeper arms the override is
**NYISO**, and its capture solve ran with the exclusions **ACTIVE** (config
`True` → apply site present), so it is *not* stale for the #4054 reason. Its
manifest row independently corroborates this: it is the only entry with
`recorded_flag_count` 248 / `meta_matched` 257 (the exclusions flag recorded
and matched) and `scenario_config_drift: []`. For ERCOT, the field did not
exist anywhere in its solve tree (`ec413d20`: 0 occurrences in
`run_calibration.py` and `scenarios.py`); for CAISO/NEISO/MISO the keepers do
not arm it, so inertness would have been behavior-neutral regardless.
Residual uncertainty: this is code-state + tool-path evidence; the capture
session's log line ("plant exclusion(s) ARMED") was not committed, so a
belt-and-braces confirmation would be a fidelity-only re-check at HEAD (hash
compare, no solve) — deliberately NOT run now, per the stop order.

## Change (c) status — already landed, no PR needed

`ci.yml` `fast-tests` at this snapshot already carries the full measured
sparse-checkout block **and** `timeout-minutes: 20`; the file is byte-identical
(blob `af34031c`) to the prototype PR head
(`claude/ci-infrastructure-blocker-bp3zv3` @ `e7dad28a`). It landed via
**PR #3964, merged by the owner 2026-08-15T16:56:40Z** — before this cycle's
directive was written. There is nothing left to port and an empty-diff PR is
not possible. Skip-count watch: the validated run 31873178938 (job 94984802917,
"Fast tier with golden-list sparse checkout", 10m36s wall) reports
`6838 passed, 31 skipped, 2 xfailed, 5 warnings, 437 subtests passed in 540.32s`
— **skip count exactly 31, matching the watch number.** (The in-file comment's
"6,837/6,838 … 10m50s job wall" figures cite the earlier probe run; run 2's
completed numbers are the above. Reported, not adjusted.) Hygiene flag for the
owner: #3964 also merged `.github/workflows/perf-a-ci-probe.yml` to main even
though its own header says NOT-FOR-MERGE; it is `workflow_dispatch`-only (no
schedule, no PR trigger) so it burns nothing on its own, but it is a per-task
rig living on main.

## #4051 reconciliation shape (when it merges — no action now)

#4051 (`claude/perf-b-ws3-recheck-9r11sg`, head `0315a09`) rewrote the same
whole-file manifest from the pre-NYISO/CAISO state (`git_sha: "dd8b7265"`,
keepers = {ERCOT, MISO}); main's copy now has {CAISO, ERCOT, NEISO, NYISO}. A
naive take-theirs merge would DROP three captures. Per the standing
append-collision convention: union the `keepers` entries in file order, keep
both lanes' rows whole, and annotate #4051's ERCOT entry as a duplicate of
main's (they are hash-identical — same bundle, same seven content hashes)
rather than dropping either. #4051's MISO row should carry a stale-on-arrival
annotation (captured against miso-159; keeper is miso-160).
