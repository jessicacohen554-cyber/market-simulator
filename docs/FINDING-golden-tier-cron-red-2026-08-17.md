# FINDING — golden-data-tier first cron firing RED: neiso-97 curate_lmp dtype defect, BLOAT-S2 untrack CLEARED

**Date:** 2026-08-17 · **Session:** DEBUG-TRIAGE (`claude/golden-data-tier-cron-debug-5r45sh`)
**Event:** `golden-data-tier.yml` run **31999181985** (schedule, 2026-08-17
05:48 UTC, head `6cc332e`, main) — the workflow's FIRST scheduled firing —
failed at step 5 "Provision data/clean". Pre-chartered as a watch item:
`docs/handoffs/debug-sweep-2026-08.md` §A.7/§B.3 ("a red there is a NEW
finding, not the known OOM — triage per the DEBUG-A protocol and route").

## 0. Verdict, one paragraph

The failing read is **not a read at all — it is a crash in
`scripts/data/curate_lmp.py`**, and the BLOAT-S2 untrack (PR #4047) is
**CLEARED**: no corpus it untracked is involved, no §4.8 evidence pass missed
a reader, and no charter remedy (revert-restore) applies. The red is the
first execution anywhere of the neiso-97 NEISO SMD DST repair
(`a2b5e3d`, PR #4043, merged 02:34 UTC — three hours before the cron):
`_neiso_flat24_repair` relabels the true spring-forward HE02 row by assigning
the **string** `"02"` into the `Hr_End` column, but the 2018–2023 flat-24
workbook vintage — the only vintage that reaches the relabel — has an
all-numeric `Hr_End` that `pd.read_excel` yields as **int64**, and
pandas 3.0.3 (the uv.lock pin, unchanged since before neiso-97) raises
`TypeError: Invalid value '02' for dtype 'int64'` instead of silently
upcasting. Fixed by relabeling with the integer `2` (parses to the identical
hour downstream), with the unit test corrected to build the real dtype.

## 1. Failure profile (from the run's job 95296191095 logs)

- Step 5 ran `scripts/regenerate_clean.py` over nine datatypes; **eight
  passed** (confirmed-retirements, reference, fleet, ancillary-services,
  load, generation, renewables, nyiso-interface-flows — including every
  consumer of corpora #4047 touched: the eia-930-hourly load/generation
  curations are green in the failing log). **`[FAIL] lmp: exit 1`** →
  "1/9 datatype(s) failed" → step exit 1 at ~5 min.
- Traceback: `curate_lmp.py:381 curate → :304 parse_neiso_file → :286
  _neiso_flat24_repair → g.loc[g.index[1], "Hr_End"] = "02"` →
  `pandas.errors.LossySetitemError` → `TypeError: Invalid value '02' for
  dtype 'int64'`. The file being parsed is the first NEISO workbook in
  sorted order, `data/raw/lmp-data/NEISO/2018_smd_hourly.xlsx` (first sheet
  `ISO NE CA`, spring-forward 2018-03-11); all six 2018–2023 flat-24
  workbooks carry the same defect and would fail identically.
- Steps 6 (emissions provision) and 7 (pytest tier) were SKIPPED; step 8's
  loud-failure guard failed **as designed** ("tier-report.xml does not exist
  — pytest died before writing it; the tier did not run"). The guard did its
  job: the red is loud, attributed, and not a silent skip.

## 2. Root cause

`a2b5e3d` ("Repair the NEISO SMD 2018-2023 DST-naive workbook clock (audit
row O8, neiso-97)") added the flat-24 repair to BOTH workbook readers. In
`curate_lmp._neiso_flat24_repair`, the spring-forward branch drops the
fabricated phantom row and relabels the true HE02 record:

```python
g.loc[g.index[1], "Hr_End"] = "02"   # str into an int64 column
```

The relabel only ever executes on flat-24 vintage sheets (2024+ true-shape
DST days have 23/25 rows and never enter the `len(g) == 24` branch), and
that vintage's `Hr_End` is all-numeric — `pd.read_excel` yields int64.
Under pandas 3.0.x the historical silent-upcast path for a lossy `.loc`
setitem is removed (`Block.setitem → coerce_to_target_dtype(...,
raise_on_upcast=True)`), so the first spring-forward day of the first sheet
raises. pandas 3.0.3 was already the lock pin when neiso-97 developed
(uv.lock last touched by #3971), so this was never version drift — the code
path simply had never run against a real workbook.

**Why neiso-97's validation missed it (two independent gaps that overlap):**

1. The session's keeper re-solve and byte-verification exercised
   `derive_actual_lmp`, which reads the workbooks via openpyxl row lists —
   no pandas setitem anywhere in that path. It was verified for real and is
   correct on main.
2. The unit test for the curate path (`CurateFlat24RepairTest` in
   `tests/test_neiso_smd_dst_repair.py`) built its synthetic frames with
   `Hr_End` as zero-padded **strings** → object dtype → the str assignment
   succeeded. The test validated the repair's placement logic while
   modelling the wrong dtype, so the suite was green while every real
   2018–2023 workbook crashed.

`curate_lmp`'s NEISO path was never executed end-to-end between `a2b5e3d`
landing (02:34 UTC) and the cron (05:48 UTC) — the cron was the first run.

## 3. The prime suspect, formally cleared: PR #4047 (BLOAT-S2 untrack)

Checked per the triage duties, not assumed:

- **`git diff --name-status 45fd439^1 45fd439`** (the #4047 merge): the
  untrack touched `eia-930` (82 D), `campd-unit-level` (35 D), `data/raw/PJM`
  (13 D), `storage-as-awards` (12 D), `iso-specific-transmission` (2 D) —
  **zero paths under `data/raw/lmp-data/`**. `lmp-data` non-golden FAILED
  its §4.8 evidence pass and stayed tracked whole
  (`docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md` §5) — the charter
  worked as designed for the very corpus the crash lives in.
- **Workflow sparse/provision list vs untracked paths:** every `data/raw`
  path the sparse checkout references was verified still tracked at head
  `6cc332e`, including the two that overlap #4047's corpora:
  `eia-930/eia_generation_profiles.parquet` (kept — hand-assembled `eia_*`
  files stayed) and `campd-unit-level/*_2023.parquet` (kept — only the 2018
  vintage was untracked). The NEISO workbooks 2018–2025 are all tracked.
- **Positive evidence from the failing run itself:** the load and generation
  curations, which read `eia-930-hourly`, completed green in the same step.

No evidence pass missed a reader; no corpus fails its proof; the charter's
revert-restore remedy does not apply.

## 4. The 2026-08-16 history rewrite, ruled out

The failure has no cache/pin component: checkout of `6cc332e` succeeded
(fresh `actions/checkout@v4`, tag-pinned actions unaffected by the repo's own
rewrite), `uv sync` succeeded, and the crash is a deterministic traceback in
tip-of-main code that reproduces locally on a fresh full clone with the same
pinned pandas. No cache key appears anywhere in the failure path.

## 5. Fix (this branch) and verification

**Fix:** relabel with the integer hour —
`g.loc[g.index[1], "Hr_End"] = 2` — dtype-safe in the int64 column and
semantically identical downstream (`astype(str)` → `"2"` → digit-strip →
`to_numeric` → 2, the same hour the string `"02"` produced). One-line
behavior delta vs shipped `a2b5e3d`: crash → works as signed. No numeric
change beyond what the owner-signed neiso-97 repair already adjudicated, so
this executes an existing signed decision rather than opening a new
solve-affecting one (clean-lmp consumers, e.g. `neighbor_price`, see exactly
the repaired series neiso-97 specified; the committed actuals/bench were
produced by the verified `derive_actual_lmp` path and are untouched).

**Test:** `CurateFlat24RepairTest._day` now builds `Hr_End` as int64 —
matching what `pd.read_excel` yields for the vintage that reaches the
relabel — and the spring test asserts the dtype survives the repair
(no silent upcast), so the exact slip-through mode is pinned.

**Verified:**

- `tests/test_neiso_smd_dst_repair.py` — 7/7 pass (previously green while
  the corpus crashed; now green modelling the real dtype).
- All eight real NEISO workbooks parse, with the design shapes: 2018–2023
  spring 23 rows/node (phantom dropped, true HE02 present), fall 23 (pair-
  mean dropped by design), 8758 rows/node (8782 leap); 2024–2025 untouched
  true-shape 23/25, full 8760/8784.
- The exact CI step-5 command (`regenerate_clean.py … lmp …`): green, 44 lmp
  partitions written.
- Full local replay of the CI job (step 5 all nine datatypes → step 6
  emissions 2023 → step 7 pytest tier serial → step 8 loud-failure guard):
  see §7.

## 6. Proof and follow-up

Per the charter's D3 clause the BLOAT-S2 post-merge proof was "the first
weekly golden-tier cron green" — that firing is now spent red on an
unrelated defect. After this fix merges, the proof is a re-run:
**recommended, one `workflow_dispatch` of `golden-data-tier.yml`** (spends
an authorized dispatch) rather than waiting a week with a red proof
mechanism standing. The BLOAT-3 follow-on ledger entry
(`docs/bloat-removal-plan-2026-08.md` §9) and the release-plan §8 ledger
carry matching annotations.

## 7. Local full-job replay record

Replay of the four job steps on a full clone (15 GB RAM / 4 CPU, pandas
3.0.3, serial pytest), same commands as the workflow. Status at the fix
commit — the replay runs in-session and this section is finalized by a
follow-up commit when it completes:

- Step 5 (nine datatypes): `[ ok ]` through six at commit time —
  **lmp included, post-fix** (and separately green standalone, §5);
  generation/renewables/nyiso-interface-flows still running.
- Tier collection at HEAD: 49 tests collected under
  `-m "slow or integration or fulldata"`, zero collection errors.
- Steps 6–8 (emissions 2023, pytest tier, loud-failure guard): pending in
  the same replay. The binding proof remains the CI re-run of §6 either
  way.
