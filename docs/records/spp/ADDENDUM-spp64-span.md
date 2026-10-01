# ADDENDUM — SPP-64 SPAN shard. Heartbeat: pin verified, nothing solved yet.

**Lane** SPP-64 SPAN · **Branch** `claude/spp64-span` ·
**Pin** `c7b42eca7a689aac80fded16fc306745cb460c4e` — verified with `git rev-parse HEAD` at session
start, before any command that could move it. No `fetch` / `pull` / `rebase` / `merge` has been run
and none will be until the final push, which will merge `origin/main` and resolve **only in this
lane's own files**.

**Charter** `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`, plus
`docs/handoffs/ADDENDUM-spp-64-g2-arithmetic-2026-09-10.md` (the G-2 pre-solve correction),
`docs/handoffs/RESULT-spp64-screen-2023.md` (six of six §6 STOP gates PASS — the span is
authorised), `docs/handoffs/FINDING-spp-64-2026-09-10.md`.

## What this shard will run

Exactly one LP invocation, three years, sequential in one process (rules 12 `[R-PARALLEL]` /
16 `[R-ALLYEARS]`):

```
python3 scripts/replay_keeper.py results/calibration/spp62_span \
  --years 2023 2024 2025 --out-dir results/calibration/spp64_span \
  --set st_gas_mustrun_per_plant=true
```

~440 s expected. Control is the keeper's **committed** bundle `results/calibration/spp62_span`,
**differenced, never re-solved** (rule 29(b) form 4; the G-DRIFT audit is PRECOMMIT §7 and returned
all-INERT). `results/calibration/spp64_*/` is gitignored at `.gitignore:1914`, which is what
discharges rule 29(c). **Rule 31 `[R-RETAIN]`: nothing will be `rm`'d.**

## Then, in this session

1. `python3 scripts/gen_spp64_attestation.py` — without it the bundle scores C6 UNATTESTED for a
   plumbing reason (`replay_keeper.py --out-dir` does not propagate the attestation). The DOF ledger
   is inherited UNCHANGED at n_entries 3 / n_residual 2: this arm adds **zero** free parameters
   (PRECOMMIT §8).
2. `python3 scripts/calibration_verdict.py results/calibration/spp64_span` — determination and every
   criterion reported at full magnitude, per year.
3. The three adjudications the charter routed to the span, in all three years:
   (i) the **D-4 unit-conduct rider** — the 2023 screen carried 4 FAILs (plants 1230/1235/1271/3008,
   0.0595 TWh, 2.56 % of forced energy) flipping `D4.passed` True→False where the keeper had none;
   rule 17 `[R-FLOOR-WINDOW]` calls a floor binding where its own driver evidence says the unit is
   offline **a bug by definition**;
   (ii) rule 20 `[R-FORCED-BUDGET]` — D-2 forced share per year against `d2_merchant_max_share` 0.30
   (2023 screen: 0.1962);
   (iii) D-1 `profile_r` ≥ 0.80 and `cv_ratio` ≥ 0.50 per year.
4. Registration under rule 15 `[R-DASHBOARD]` **whatever the verdict says** — keeper or rejection —
   in this session, plus the rule 28 `[R-MECH-MATRIX]` cell for `st_gas_mustrun_per_plant` in
   **SPP's shard only** and the `docs/calibration-log/spp.md` entry (spp-25).

## What this shard will NOT do

Promote a keeper or touch `frontend/data/backcast/keepers/SPP.json` — **promotion is the OWNER's
call**; this lane recommends and never acts. Re-cut any gate or bar. Re-solve the control. Arm
`st_gas_mustrun_p25_level`, touch `offer_curve_by_group`, or add any parameter. Write another ISO's
files. Add a `complete` marker or a `frontier` declaration.

**Nothing is solved at the time of this commit.** Every number in the RESULT will be re-derived in
this session from artifacts.
