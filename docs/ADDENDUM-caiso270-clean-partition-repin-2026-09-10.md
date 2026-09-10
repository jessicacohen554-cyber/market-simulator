# ADDENDUM to PRECOMMIT-caiso270 — the attempt-1 shard fleet, the defect that stopped it, and the re-pin

**Session caiso-270, 2026-09-10.** Amends `docs/PRECOMMIT-caiso270-keeper-restore-2026-09-10.md` §5.
**Written and pushed BEFORE the rev2 shards' first LP**, so nothing here can be shaped by a result.

## §A1 — The pin moves: `d75812c4…` → the SHA of this commit

The four attempt-1 shards (`claude/caiso270-keeper-{2022,2023,2024,2025}`) **all failed before producing a
bundle**, on ONE defect, and all four have been interrupted and archived. Nothing about the arm, the recipe,
the gate or the collision register changes — only the setup block. The rev2 fleet re-uses **the same four
branch names and the same four out-dirs**, which archiving freed.

## §A2 — THE DEFECT IS MINE: the PRECOMMIT's setup block omitted the clean-partition build

`data/clean/` is **derived and gitignored**, so a fresh container starts empty. The CAISO keeper arms
`capacity_deliverability_limits`, and before the LP is built both solve paths call
`market_sim.data.input_completeness.check_clean_partitions(config, iso, strict=True)`. In `strict` mode —
which is exactly what the calibration lane uses — a missing partition is **FATAL BY DESIGN**:

> `CAISO: 1 armed mechanism(s) have no usable input data, so they would silently no-op and the run would
> advertise a mechanism that never ran: capacity_deliverability_limits needs
> data/clean/capacity-deliverability/CAISO (falls back to the baked simultaneous-import cap (a fitted
> scalar)) … STRICT mode (the calibration lane): a DECLARED fallback is fatal here too, because a keeper
> that solved on the fallback while its run_config advertised the published input is the caiso-188 defect.`

**The guard is right and it saved the run.** Its own recorded history is the reason: *caiso-157 — an absent
partition re-armed a retired fitted import scalar across five keeper promotions (rules 20 `[R-DOF]` / 24
`[R-REGISTRY]`); caiso-188 — it recurred on the designated keeper because the guard was never wired to a
solve path.* Had the shards forced past it, they would have produced a bundle that solved on a **fitted
scalar** while its `run_config` advertised the published MIC cap. That bundle would have been discarded.

Measured in the parent, at zero LP cost, against the keeper's own two recipes: **exactly ONE** armed
mechanism is missing its partition. `outage_source` (CAMPD unit outages) is **present**; `hydro_ror_split`
is **not armed**.

## §A3 — The fix, verified in the parent BEFORE the rev2 fleet launched

    PYTHONPATH=.:src python3.11 scripts/data/curate_capacity_deliverability.py

writes 5 partitions (CAISO 386 rows, ISONE 15, MISO 776, NYISO 35, PJM 155). After it:

| check | measured |
|---|---|
| `check_clean_partitions(cfg, "CAISO", strict=True)` on `caiso_fuelvintage_span` | **PASSES** |
| the same on `caiso_fuelvintage_tp2022` | **PASSES** |
| `resolve_seam_import_cap(cfg, "CAISO", 2022, …)` | `cap_mw=**15780.0**, source=**'mic_partition'**` — **byte-identical to the value the predecessor bundle records in its own `run_config.json` `resolved_inputs.seam_import_cap`** |
| the same for 2024 | `cap_mw=16452.0, source='mic_partition'` |

That last row is the load-bearing one: the rebuilt partition reproduces the keeper's **own recorded resolved
input exactly**, so the rev2 shards start from the same seam cap the keeper solved on.

**`PYTHONPATH=.` is not enough** — it raises `ModuleNotFoundError: No module named 'market_sim'`, because
`pip install -r requirements.txt` does not install the package and the sources live under `src/`. The
build command printed by the guard's own error message omits `src`. **Noted, NOT repaired**: it is a message
string in `src/market_sim/data/input_completeness.py`, outside this lane's scope (rule 25 `[R-ISO-SCOPE]`
is not the issue; rule 32(c)(6) keeping shards and this lane out of shared `src/` is), and it blocks nothing
now that the correct command is in the shard prompt.

## §A4 — What the attempt-1 shards were worth, stated plainly

**All four reported a blocker; none diagnosed it correctly, and two mis-stated the deliverable.**

* Y2022 and Y2025 both concluded *"`curate_capacity_deliverability.py` missing"*. **It is not missing** — it
  is at that exact path in the tree they cloned. What is missing is its *output*.
* Y2025's own status line said both *"shard 2025 solved"* and *"blocked at ~30s"*. Those cannot both be true.
* **Y2023 armed a waiter for `metrics.json`** — a file the solve **never writes**. `metrics.json` is produced
  by `dashboard_add_run.py`, which the shard prompt forbids. It was waiting for something that could not
  arrive. The rev2 prompt names the real completion signal: `meta.json` + `hourly/system_<year>.parquet`.
* Y2023 and Y2024 both **backgrounded the solve and ended their turn**, going idle mid-LP. The rev2 prompt
  requires the solve to run in the **foreground** under `timeout 2400`.

This is the intended posture (rule 32(c)(6)-(7): a shard reports, the parent owns `src/` and `scripts/`) and
it worked — the shards' value was **the signal that something was wrong**, which is exactly what a
stop-and-report is for. Every claim above was re-verified against the source in the parent before any action;
none was acted on as given.

## §A5 — Cost, stated rather than buried

Four shard containers spent ~10–22 minutes each and produced **no LP and no artifact**; the attempt-1 fleet
is a total loss and its four sessions are archived. **No result was deleted** (rule 31 `[R-RETAIN]`) — there
was none to delete, and no bundle reached any branch. The parent spent **zero LP** throughout (rule 32(a)).

**The lesson, for the next lane:** the caiso-269 bind check proves the *config* binds; it does not prove the
*container* can solve. A fresh container starts with an empty `data/clean/`, so **a phase-0 item belongs
beside the bind check: run `check_clean_partitions(cfg, iso, strict=True)` against the recipe and build every
partition it names, in the PRECOMMIT, before a shard launches.** That check is now §A3 and it costs seconds.
