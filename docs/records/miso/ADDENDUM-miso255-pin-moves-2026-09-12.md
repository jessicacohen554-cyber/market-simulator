# ADDENDUM 1 to PRECOMMIT-miso255-measured-sil — **the pin moves, and why**

**Written and pushed BEFORE the re-launched shards solve** (rule 29 `[R-SCREEN]`). Nothing in
`PRECOMMIT-miso255-measured-sil-2026-09-12.md` §2 (screen years) or §3 (gates, gate values,
direction check) is renegotiated here. Only the pinned SHA and the drift audit move.

## 1. WHY THE FIRST TWO SHARDS WERE KILLED — my own defect, found by the repo's own guard

The first pair (pin `5d341fa90a1680c5c47f1b98e7596810e805c0f7`) was **interrupted before either
finished**, because an AST check of that exact pin found this:

```
run_year params=302  **kwargs=False
kwargs passed that run_year does NOT accept: ['miso_import_sil_measured_envelope']
```

I added the flag to `solve_and_persist`'s signature and to its `run_year(...)` call site in
`scripts/run_calibration_full.py`, and **not** to `run_year`'s own parameter list in
`scripts/run_calibration.py`. Every `solve_and_persist` invocation at that pin would have raised
`TypeError` ~29 s in, before any LP work — both shards were dead on arrival and would have burned
their budget reporting a stop.

**This is the same defect class `nyiso-229` introduced and `SPP-36 shard 1` caught the same day**
(`706aa547` STOP-THE-LINE, `docs/FINDING-spp-36-runyear-kwarg-2026-09-12.md`). I reproduced it
independently, in the same session that read the fix. Recorded here rather than quietly repaired.

**The repair** mirrors the sibling flag `miso_seam_envelope_hour_ending_key` exactly — two hunks in
`run_calibration.py`: the parameter, and the `with_overrides` application. `run_year` now takes 304
parameters and the call binding is intact.

**The guard that should have caught me now does, and I verified it in both directions**:
`tests/unit/pipeline/test_run_year_kwarg_binding.py` (shipped by `706aa547`, which this branch
picked up in the rebase below) **FAILS** on my pre-fix tree with
`assert not ['miso_import_sil_measured_envelope']` and **PASSES** after the repair. Had I rebased
before launching instead of after, the shards would never have gone out.

## 2. REBASE ONTO `f0316092`

`claude/miso-255-cc-cf-tracking-83e0m6` is rebased onto `origin/main` at `f0316092` — **no
conflicts**. The branch's first commit (the phase-0 FINDING) had already merged to main as
`a2465367` and is correctly dropped as a duplicate; the two remaining commits are the arm and the
gate scorer. Every miso-255 artifact is intact.

## 3. G-DRIFT RE-AUDIT — the 24 new main commits, all INERT for MISO

Re-run because the rebase moved the base (rule 29(b): form 4 is only valid while every solve-path
hunk since the controls' `git_sha` is INERT). `git diff 5327e60d f0316092 -- src/market_sim
scripts/run_calibration*.py scripts/lib data/raw/_validation-source data/raw/reference` → **6
files, +168/−1**:

| file | classification |
|---|---|
| `scripts/run_calibration.py`, `scripts/run_calibration_full.py` | `706aa547`'s STOP-THE-LINE repair (restores a call binding that was broken *after* the controls solved) plus the `unit_outage_window_hour_grain` threading. A restored binding cannot change a solve that already worked. INERT. |
| `data/fleet/arrays.py`, `data/outages.py`, `data/resolved_inputs.py`, `config/scenarios.py` | New behaviour behind `unit_outage_window_hour_grain`, `campd_outage_merit_order_guard`, `campd_per_unit_attribution` — **all three default `False`**, and in every MISO recipe each is either explicitly `False` or absent (verified against all three `run_config.json`). NYISO's lane. INERT. |

**Measured, not asserted:** all four committed MISO bundles keep their cache keys **byte-identical
across the rebase** — `miso_fuelvintage_A fefc0cdea485423b`, `miso251_tp2021 244d810e992fcd33`,
`miso251_screen2022 466a72f1eafd28b7`, `miso251_tp2020 d92fa22309158cf4`.

**Verdict unchanged: all hunks INERT ⇒ rule 29(b) form 4 holds, the committed
`miso251_tp2021` / `miso251_screen2022` bundles remain the controls, and NO control solve is
spent.**

## 4. WHAT THE RE-LAUNCHED SHARDS CHANGE

Only the pin. Same two screen years (2021, 2022), same `--set` delta, same six STOP-only gates at
the same pre-registered values, same committed scorer, same controls, same 20-minute budget and the
same mandatory container preflight. **HARD STOP 3 (the G-1 liveness marker) is unchanged and is
still what catches a silently unarmed run** — it would also have caught this defect, one solve
later and at full cost, which is the argument for the AST check going first.
