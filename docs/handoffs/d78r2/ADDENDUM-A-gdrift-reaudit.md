# ADDENDUM A — capx D78-R2: the rebase, and the G-DRIFT RE-AUDIT over the new range

**Pushed BEFORE the first LP.** No leg had started when `main` moved (the
`data/clean` rebuild was still running), so this is a rebase *before* the lane's
first solve, not between two legs — the strictest case the PRECOMMIT §5 rebase
discipline allows and the only one in which no LP is discarded.

## A.1 What happened

`origin/main` advanced **`e6a0402f` → `b22b91c3` (45 commits)** while the
`data/clean` rebuild ran. Two facts about that range matter to this lane:

1. **This lane's own STEP 0 + PRECOMMIT + instrument repair were MERGED into
   `main`** as PR **#5209** (`dcfabcd1`). `git rebase origin/main` therefore
   fast-forwarded the branch onto `b22b91c3` with **zero commits replayed and
   zero lost** — verified: `bf97317f`, `2aa9d1e3`, `8e68a471`, `ae5a3355` are all
   contained in `origin/main`, `exempt_unit_ids` is absent from the screen's
   signature at HEAD, and the PRECOMMIT is present at HEAD. Per the merged-PR
   rule the branch now carries follow-up work restarted from `main`.
2. **capx D65-B-R's batch landed** (`a2103019`, PR #5218), which is the
   PRECOMMIT §8 precondition on the arm's registration ordering.

## A.2 The re-audit — `e6a0402f..b22b91c3`, `constants.py` FIRST

```
git diff --stat e6a0402f..b22b91c3 -- src/market_sim/config/constants.py
→ (empty)
```

Solve-path surface, 11 files / +1437 −48:

| file | Δ | verdict | reason |
|---|---:|---|---|
| `model/capacity_evolution/retirements.py` | 69 | **INERT** | **this lane's own STEP 0**, established inert in PRECOMMIT §1 (unreachable branch, no field, keys unmoved) |
| `model/capacity_evolution/evolve.py` | 12 | **INERT** | same commit |
| `config/scenarios.py` (comment hunks) | 8 of 29 | **INERT** | same commit — comments only |
| `config/solve_surface.py` | +406 (new) | **INERT** — *measured* | capx D79 (owner ruling Q54). `moved_rows("PJM")` = `{}` and `SOLVE_EPOCHS` = `()`, so neither `__solve_surface__` nor `__solve_epochs__` enters any key |
| `config/solve_surface_declared.py` | +577 (new) | **INERT** — *measured* | the frozen declaration D79 landed at every row's live hash |
| `config/scenarios.py` (`cache_key`) | 21 of 29 | **INERT** — *measured* | the two dunder keys are absent from every config today; proven below |
| `results/cache.py` | 42 | **INERT** | additive `solve_surface.json` stamp beside `config.yaml` + epoch-ledger prose; no decision path |
| `scripts/run_capacity_hindcast.py` | +5 | **INERT** | additive `solve_surface` block in `meta.json` |
| `pipeline/persist.py` | +7 | **INERT** | additive `solve_surface` block in `run_config.json`, top-level, outside `scenario_config` |
| `results/export.py` | +5 | **INERT** | additive block in the export payload |
| `scripts/lib/forecast_provenance.py` | 38 | **INERT** | scorer-side provenance reader; adds one recorded field, reads nothing the LP writes |
| `data/raw/reference/miso_ct_netload_drag.json` | +295 (new) | **INERT** | **another ISO's artifact** — a PJM run never reads it (rule 25) |

**ZERO LIVE hunks. No control solve is earned by drift**, and both legs still
solve at one HEAD (`b22b91c3`) by construction.

## A.3 The D79 verdict is MEASURED, not taken from its own comment

D79 changes `cache_key()` itself, so "it moved zero keys" is exactly the kind of
claim a lane must not accept on the changing party's word. This lane already owns
the instrument to check it: `docs/handoffs/d78r2/keys_probe.py`, whose output at
**pristine `e6a0402f`** is committed as `keys_probe_origin_main.json`. Re-run at
`b22b91c3`:

```
diff keys_probe_origin_main.json keys_at_b22b91c3.json
→ IDENTICAL
```

So at the new HEAD the control still resolves **`a9c66d8ea25acb9d`** (= the
registered bare `pjm-t1h`), the arm still **`bb6a60239d69508b`**, every backcast
key per ISO and `ScenarioConfig()` = `547053bdfccd4264` are unmoved. Independently:
`moved_rows("PJM")` returns `{}` and `SOLVE_EPOCHS` is the empty tuple, so the
mechanism cannot inject a key for this config at all.

## A.4 What does NOT change

No gate, edge, declared class, classification rule, STOP or flip-condition limb in
the PRECOMMIT moves. The declared leg keys of §1/§5 are re-confirmed at the new
HEAD rather than re-declared. W0 stays dropped for the reason §4 gave.

One artifact-level consequence is recorded rather than ignored: every bundle
written at this HEAD now carries an additive `solve_surface` block in `meta.json`,
`run_config.json` and a `solve_surface.json` beside `config.yaml`. It is present
in **both** legs identically, is not a ledger block, and is not read by
`window_compare2.py` — so the whole-ledger diff is unaffected.
