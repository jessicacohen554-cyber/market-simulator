# FINDING — `replay_keeper.py` cannot replay the ERCOT keeper at all (blocks the whole MER re-solve batch)

**Lane:** ercot-mer, 2023 shard (solve shard, parent = ERCOT MER orchestrator)
**SHA:** `5017c3602adf7bc9389cf10755fc22833f8f1b2d` (verified; `2ec096633f5624585eb9db1728ebc7c8ca5ccbdf` is an ancestor — the MER commit is present)
**Date:** 2026-09-19
**Outcome:** STOPPED before any LP. No bundle produced, nothing pushed. Zero LP seconds spent.

## What happened

The sanctioned command

```
python3 scripts/replay_keeper.py results/calibration/ercot265_receipts_five_year \
  --years 2023 --out-dir results/calibration/ercot_mer20260919_2023/
```

exited **1** in ~2 s with:

```
meta.json keys not bound to solve_and_persist kwargs: ['ercot_ep_gas_basis_receipts_fallback']
 — extend replay_keeper._REMAP/_IGNORE deliberately; silent drops are the miso-50..53 regression class
```

(plus a benign platform WARNING: bundle `Linux-...-fc-v24`, now `-fc-v37`.)

`results/calibration/ercot_mer20260919_2023/` was never created.

## Root cause — a `build_kwargs` / `apply_config_overlay` asymmetry

Measured at this SHA:

| fact | value |
|---|---|
| `meta.json` top-level `ercot_ep_gas_basis_receipts_fallback` | `True` |
| is a `ScenarioConfig` dataclass field | **yes** |
| is a `solve_and_persist` parameter | **no** |
| in `replay_keeper._REMAP` | no |
| in `replay_keeper._IGNORE` | no |

In the normal CLI path the key is **not** a direct kwarg — `run_calibration_full.py:14247` routes it through the
`prb_overrides=` bag passed to `solve_and_persist` (the enclosing literal opens at `run_calibration_full.py:14191`).

`replay_keeper.py` has that generic dual-channel routing in exactly one place —
`apply_config_overlay` (`replay_keeper.py:421-428`), which writes any `ScenarioConfig` field into
`kwargs["prb_overrides"]`. But the **base recipe** reconstruction, `build_kwargs`
(`replay_keeper.py:285-301`), has no such fallback: a meta key that is not a `solve_and_persist`
parameter goes straight to `unmapped` → `SystemExit` (`replay_keeper.py:299`).

So the per-year `config_partition_overrides` overlay would have routed this key fine; the top-level
base recipe cannot.

## Scope — this is NOT a 2023 problem

`ercot_ep_gas_basis_receipts_fallback` sits at **meta.json top level**, i.e. in the base recipe armed
for every year. `build_kwargs` runs once, before the year loop, so the stop is year-independent.

`meta.years = [2021, 2022, 2023, 2024, 2025]`.

**Every one of the five sibling shards will hit this identical stop.** The batch cannot proceed on any
year until the driver is fixed. The parent should stop the siblings rather than let them burn containers.

## What the fix is (NOT done here — `scripts/` edits are forbidden to a shard)

One deliberate routing extension in `scripts/replay_keeper.py::build_kwargs`: give it the same
`ScenarioConfig`-field → `prb_overrides` fallback `apply_config_overlay` already has, or add an explicit
`_REMAP`-style entry for this key. The driver's own error message prescribes this
("extend replay_keeper._REMAP/_IGNORE **deliberately**").

The deliberateness matters: `build_kwargs`' hard stop exists to prevent the miso-50..53 lossy-reconstruction
class, so a blanket fallback silently widens what a replay will accept. That is an owner/infra call, not a
shard's.

## What was explicitly NOT done

- **No `--set`.** The prompt forbids it, and it would not have helped: the `unmapped` guard fires on the
  meta.json scan regardless of operator overrides.
- **No edit under `src/` or `scripts/`.**
- **No bundle pushed** — there is no bundle. Nothing was deleted (rule 31 `[R-RETAIN]` — nothing existed).

## Numbers owed to the parent, and why they are absent

| asked for | value |
|---|---|
| `container preflight:` / `memory peak:` log lines | **absent** — the runner never reached `ensure_solve_container`; the stop is in argument reconstruction |
| wall seconds | ~2 s to the stop (no LP) |
| P1 load-weighted / simple mean price | **not produced** |
| `marginal_emission_rate` stats | **not produced** |
| slack / dump totals | **not produced** |
| bundle path | **none created** |

The MER column question (HARD STOP 2) is therefore **untested** — this stop is upstream of it and says
nothing either way about the dual's memory behaviour at per-plant scale, which remains unvalidated.

## Environment note (not the blocker)

The container arrived with **no Python dependencies installed** (`numpy` missing on every interpreter).
Resolved with `uv sync --no-dev` into `.venv/` (21 packages, matching `uv.lock`); `git status` stayed clean.
The solve was then invoked as `.venv/bin/python scripts/replay_keeper.py ...`. Sibling shards will need the
same step.

---

# PARENT ADDENDUM — reproduced, root-caused one level deeper, and FIXED (2026-09-19)

**Rescued from shard branch `claude/ercot-mer-2023` @ `63d156e1217667618f7670d06c23e68cc24163b0`**
(rule 33 `[R-SHARD-ARCHIVE]` (f)(1) — a shard's FINDING exists nowhere else). The 2021 and
2022 shards filed the same finding independently at
`c7f2d2a2b93310a0a4e81e9dd74f73c463c62810` and
`1198751ebc44d3f7fabb387a02feefc34eccf1d6`; 2024 and 2025 stopped at the same point.

## All five shards stopped identically. ZERO LP seconds spent.

| year | session | branch @ sha | outcome |
|---|---|---|---|
| 2021 | `session_01XAPSJtKQgkgJFRmxvhKpRE` | `claude/ercot-mer-2021` @ `c7f2d2a2b93310a0a4e81e9dd74f73c463c62810` | stopped, FINDING filed |
| 2022 | `session_01RRhQsYd2hLrTrKcpsFxbKP` | `claude/ercot-mer-2022` @ `1198751ebc44d3f7fabb387a02feefc34eccf1d6` | stopped, FINDING filed |
| 2023 | `session_018sZN9sa47f5PBrKi2jhkLu` | `claude/ercot-mer-2023` @ `63d156e1217667618f7670d06c23e68cc24163b0` | stopped, FINDING filed |
| 2024 | `session_01L44zSgtycE6LNJKk4vrU9k` | `claude/ercot-mer-2024` (no push) | stopped, reported to parent |
| 2025 | `session_013uD117W2qrc3RgxKtcsUYi` | `claude/ercot-mer-2025` (no push) | stopped, reported to parent |

This is the shard contract working exactly as rule 32(c)(7) intends — *"a shard that stops
with a clear report is a SUCCESS"*. Nothing was pushed, nothing was deleted, and no shard
edited `scripts/`.

## Reproduced in the parent, zero-LP

```
build_kwargs(meta)  ->  SystemExit: meta.json keys not bound to solve_and_persist kwargs:
                        ['ercot_ep_gas_basis_receipts_fallback']
```
`is ScenarioConfig field: True` / `is solve_and_persist param: False` / `in _REMAP: False` /
`in _IGNORE: False`. The shards' diagnosis is confirmed in full.

## ONE LEVEL DEEPER THAN THE SHARDS GOT — how the key got there

The shards correctly identified the `build_kwargs` / `apply_config_overlay` asymmetry. The
remaining question was *why this key is at meta top level at all*, and it has a definite answer:

* `solve_and_persist`'s meta literal (`run_calibration_full.py:6851-7245`) **has never emitted
  this key** — `git log -S` finds it introduced in exactly one place, `0ebfc2da`, at
  `run_calibration_full.py:14247`, inside the CLI's **`prb_overrides`** dict.
* The meta literal *does* flatten `prb_overrides` into `coal_prb_sigmoid_overrides`, which
  `_REMAP` maps back to `prb_overrides` — so prb keys normally round-trip fine. The sibling
  key **`ercot_ep_gas_basis_corroborated` is in that bag in this very bundle** and replays
  without complaint.
* `ercot_ep_gas_basis_receipts_fallback` is **not** in the bag. It was stamped at top level by
  the ercot-265 promotion commit `c79e89ef` (2-space indent, beside `model_changes_note`) as a
  provenance record of the `False -> True` arming.

So the blocker is a **hand-stamped provenance key colliding with a strict machine-read
contract** — not a defect in the recipe, and not something a year or a `--set` could route
around.

## Scope, measured

The key sits in the BASE recipe and `build_kwargs` runs once before the year loop, so the stop
is year-independent: **the designated ERCOT keeper has been unreplayable on all five years
since `c79e89ef` (2026-09-10)**. ercot-264's clean five-year reproduction (2026-09-09) predates
the stamp, which is why nothing caught it.

## The fix

`scripts/replay_keeper.py::build_kwargs`, one deliberate **per-key** route to `prb_overrides` —
the channel the CLI arms it through and the consumer reads it from
(`data/fuel/basis/ercot.py:830`, `getattr(config, ...)`) — mirroring the
`coal_plant_monthly_pricing` precedent immediately above it.

**Explicitly NOT a blanket "any ScenarioConfig field falls through to prb_overrides."** That
unmapped hard stop is the miso-50..53 lossy-reconstruction guard; widening it wholesale would
silently admit every future stray key. Verified still firing on an unknown key.

Only a `True` is written, matching the CLI's `True if <flag> else None`: the dataclass default
is already `False`, so a recorded `False` must not fabricate an override.

**One bug found in the fix itself, in review, before it shipped:** the first version used
`setdefault`-and-mutate, which writes through the bag bound straight off
`meta["coal_prb_sigmoid_overrides"]` — mutating the caller's parsed meta.json and contaminating
every later reconstruction from it. That is the exact trap `apply_config_overlay` already
carries a defensive copy for. Corrected to a defensive copy; pinned by
`test_does_not_mutate_the_callers_meta`.

Guards: four new cases in `tests/scoring/test_replay_keeper_strict.py`. Suites green —
`test_replay_keeper_strict` 12 passed; `test_replay_keeper_diagnostics` +
`test_config_partition_replay` + `test_recipe_replay_gates` 32 passed, 6 skipped.

## What is still UNTESTED

**HARD STOP 2 — the `marginal_emission_rate` column — was never reached**, on any year. This
stop is upstream of the LP, so it says nothing either way about the dual's behaviour, and
**the dual's memory cost at per-plant ERCOT scale remains unvalidated** exactly as the owner's
append warned. The re-launched batch is still its first real test.

## Environment note (not the blocker, but every shard paid it)

Shard containers arrive with **no Python dependencies installed**. The shards resolved it with
`uv sync --no-dev` into `.venv/` and invoked `.venv/bin/python scripts/replay_keeper.py`. The
re-launch prompts carry this step so no sibling rediscovers it.
