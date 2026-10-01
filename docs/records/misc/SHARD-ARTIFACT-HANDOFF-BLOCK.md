# The shard artifact-handoff block — paste this into every solve-shard prompt

**Standing appendix to rule 32 `[R-SHARD]`.** Owner directive, 2026-09-10 (session ercot-265):
*"Each shard should commit to Main so give me an append block to direct the sessions so you don't
have to rerun."*

## Why this exists — two failures it prevents

1. **A cloud shard's final message is NOT readable by the parent.** Rule 32(c)(5) says "tell it
   what to REPORT … the parent may never get to read its disk," but it does not say the parent may
   be unable to hear the report either. In ercot-265 five shards solved correctly, reported their
   numbers in chat, and the parent could reach **none** of them: cloud sessions are not
   peer-addressable via `SendMessage` and this build has no `list_events`. The numbers had to be
   recovered by firing one-shot triggers back into the idle containers. **A shard's report is only
   durable if it is PUSHED.**
2. **A committed per-year bundle dir turns the parity gate RED.**
   `scripts/check_registry_payload_parity.py` sweeps every top-level DIRECTORY under
   `results/calibration/` and fails any that maps to no registry sidecar. ercot-262 left five such
   dirs on `main` and ercot-264 left two. The staging path below is **not** swept, so artifacts are
   durable without breaking CI.

## Sizing, measured

A slim per-year artifact set is **~3 MB**: six `hourly/` sidecars (system 812 KB, class_band_hourly
676 KB, class_hourly 500 KB, reserve_family 216 KB, storage 63 KB, adaptive 8 KB) plus the bundle's
root JSONs (~700 KB). The `.gitignore` slim-bundle rules already exclude `dispatch/`, `floors/`,
root `*.parquet`, `unit_hourly_*` and `network_*` — the heavy regenerable intermediates. A 3 MB
pack is comfortably inside `git push` territory (Git & Pushing measured a 435 KB single-blob push
with no 413; the 413 rationale applies to ~120 MB bundle dirs).

---

## THE BLOCK — substitute `<LANE>` and `<YEAR>`, paste verbatim

```text
## DURABLE ARTIFACT HANDOFF — COMMIT YOUR RESULTS TO MAIN (owner directive)

Your container is ephemeral. Anything left only on your local disk dies with it and forces a
full re-solve. Your bundle is not finished until it is PUSHED. Do this AFTER the solve and
AFTER you have scored it — it is the last thing you do.

Branches in this repo auto-merge to main and are deleted within minutes, so pushing your branch
IS committing to main. You do not open a PR and you do not merge anything yourself.

### STEP 1 — write your metrics file
Write results/shard-staging/<LANE>/<YEAR>/METRICS-<LANE>-<YEAR>.json with every number your
prompt asked you to report, plus:
  "git_sha", "config_delta_vs_keeper", "leg_verified" {the config signature you checked},
  "keeper_control" {the control values you were given},
  "keeper_control_verified" {those values AS YOU RECOMPUTED THEM from committed artifacts —
     if any differs from what you were given, say so explicitly and difference against YOURS},
  "deltas_arm_minus_keeper", "criterion_status_moves".
Use the string "unavailable" for anything you cannot read. NEVER estimate a number.

### STEP 2 — copy ONLY the slim artifacts
mkdir -p results/shard-staging/<LANE>/<YEAR>/hourly
cp results/calibration/<YOUR_OUT_DIR>/*.json  results/shard-staging/<LANE>/<YEAR>/
cp results/calibration/<YOUR_OUT_DIR>/hourly/*_<YEAR>.parquet \
                                              results/shard-staging/<LANE>/<YEAR>/hourly/
DO NOT copy dispatch/, floors/, root *.parquet, unit_hourly_*, network_*, or solve.log.

### STEP 3 — SIZE CHECK, hard stop
du -sm results/shard-staging/<LANE>/<YEAR>
Over 10 MB means you copied something you should not have. STOP, do not push, report what is
oversized.

### STEP 4 — stage EXPLICITLY, never by directory
git checkout -b claude/<LANE>-<YEAR>
git add -f results/shard-staging/<LANE>/<YEAR>
git status --short
git status --short MUST show ONLY paths under results/shard-staging/<LANE>/<YEAR>/. If it shows
ANYTHING else — any file under src/, scripts/, frontend/, or another bundle — STOP and do not
push. Do not try to fix it.

### STEP 5 — commit and push
git commit -m "<LANE> <YEAR>: solved artifacts + metrics (shard handoff)"
git push -u origin claude/<LANE>-<YEAR>
If the push fails with HTTP 408 or 500 that is HTTP/2 negotiation and NOT a size problem: run
`git config http.version HTTP/1.1` and retry before concluding anything. Retry network failures
up to 4 times with backoff 2s, 4s, 8s, 16s.

### STEP 6 — confirm and report
Report the branch name, the commit sha, `du -sm` of the staged dir, and the exact staging path.
The parent reads your artifacts from that path, not from your disk.

### WHY THIS PATH AND NOT results/calibration/
check_registry_payload_parity.py sweeps every top-level DIRECTORY under results/calibration/ and
fails any that maps to no registry sidecar. A per-year shard bundle committed there is an
unregistered dir and turns that gate RED — this has already happened twice (ercot-262,
ercot-264). results/shard-staging/ is not swept. The PARENT composes the per-year staging dirs
into ONE bundle, registers that, and then removes the staging tree; git history remains the
record (rule 15).

### STILL FORBIDDEN — unchanged
`git add -A` / `git add .`; ANY edit under src/ or scripts/; dashboard_add_run.py,
build_manifest.py, build_status.py, prune_iso_runs.py, or anything under
frontend/data/backcast/** (registration is the parent's job, once, at the end); opening a pull
request; deleting any result (rule 31 [R-RETAIN]) — leave your bundle on local disk as well.

A shard that stops with a clear report is a SUCCESS; a shard that repairs infrastructure is a
FAILURE.
```

---

## The parent's side of the seam

After the shards land, the parent (which still solves nothing, rule 32(a)):

1. `git fetch origin main` and read `results/shard-staging/<LANE>/<YEAR>/` for each year.
2. Compose the per-year artifacts into ONE bundle under `results/calibration/<composite>/`.
3. `stamp_config_partition.py --check`, then `calibration_verdict.py` on the composite — the
   determination comes from the scorer, never from arithmetic in the report.
4. Register once (rule 15) — `dashboard_add_run.py`, then the keeper shard + `build_status.py`
   if it is a promotion.
5. **Remove the staging tree in the same session** once the composite is registered, so
   `results/shard-staging/` never accumulates. Git history is the record.

## What this does NOT change

Rule 32(c)(6) still forbids a shard from registering anything, editing `src/` or `scripts/`,
touching `frontend/data/backcast/**`, opening a PR, or deleting a result. This block changes
exactly one thing: **a shard now pushes its own slim artifacts to a staging path instead of
leaving them to die with its container.** If the owner wants this folded into rule 32's text in
`CLAUDE.md` rather than living here as an appendix, that is a one-line amendment and an owner act.
