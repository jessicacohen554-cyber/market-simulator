# HP-02b — Finish the pull-out bundle: MISO / NYISO / NEISO 2024 LMP + CO₂-rate exports

**Model:** Sonnet · **Depends on:** HP-02 (merged) · **Parallel-safe with:** HP-03
**Targets:** `data/bundled/lmp/`, `data/emissions/`, `PLAN.md` §6,
`docs/handoff/README.md`

HP-02 (PR #1547) bundled all six CF profiles but only landed the
ERCOT/CAISO/PJM bridge re-solves; its commit message promised
"PJM/MISO/NYISO/NEISO follow in a subsequent commit" and MISO/NYISO/NEISO
never arrived. This closes that gap.

Paste the block below into a fresh Claude Code session on
`jessicacohen554-cyber/market-simulator`.

```text
You are finalizing the standalone Scope 2 LCE portfolio tool in
scope2-lce-portfolio/ (repo jessicacohen554-cyber/market-simulator). Develop
on a fresh branch off latest origin/main named scope2/hp-02b-remaining-isos
(or your session's designated branch); push there; open NO pull request.

GOAL
Produce and commit the three missing pull-out data bundles — MISO, NYISO,
NEISO, year 2024 — exactly matching the ERCOT/CAISO/PJM bundles HP-02
committed: data/bundled/lmp/<ISO>_2024_bau_lmp.csv (+ .provenance.json
sidecar) and data/emissions/<ISO>_2024_fossil_avg_co2_rate.parquet.

CONTEXT (read first)
- data/bundled/lmp/ERCOT_2024_bau_lmp.csv.provenance.json — the exact
  sidecar schema and posture to replicate (backcast_validation_only,
  source keeper id, load-weighted zonal collapse per ADR 0011).
- docs/validation-2026-07-05-ercot-2024-backcast.md and
  docs/validation-2026-07-05-5iso-backcast-extension.md — the bridge
  re-solve procedure (per-ISO re-solve from the ISO's calibration keeper;
  the 5-ISO memo covers MISO/NYISO/NEISO specifics and the
  container-memory workaround for ~16 GB solve peaks).
- frontend/data/backcast/keepers.json (parent repo) — each ISO's CURRENT
  keeper. NOTE: the MISO keeper flipped on 2026-07-06 to the miso-42
  coal-econ ablation twin (PR #1544) — use the keeper as of YOUR run time,
  and record its id in the sidecar.
- scripts/build_fossil_avg_co2_rate.py — reads the bridge run's dispatch
  Parquet (market_sim_fleet schema metadata) and writes the rate file.

PROCEDURE / DISCIPLINE
1. One ISO at a time, sequentially — never parallel year- or ISO-solves in
   one process (memory; repo rule 12). A bridge re-solve is minutes-long.
   If two separate invocations are truly independent you may background at
   most 2, but MISO's ~16 GB peak means it should run alone.
2. These are 2024-only diagnostic bridge solves under the ADR 0015
   backcast-validation carve-out (repo rule 16 note: NEVER register them on
   the calibration dashboard; they are not keepers). Zero edits to
   run_calibration.py / runner.py — a one-off bridge script is fine and
   stays uncommitted, same as HP-02's.
3. Collapse zonal LMPs load-weighted to one ISO price (ADR 0011; zero-load
   hour falls back to simple mean) — mirror the existing sidecar's
   "collapse" field. Validate each CSV: 8760 rows per ISO, hour 0..8759,
   finite prices; record lmp_mean/min/max + annual_load_twh in the sidecar.
4. Run each rate export through scripts/build_fossil_avg_co2_rate.py from
   the bridge dispatch output; validate nonnegative, full calendar.
5. Sanity-check each new bundle end-to-end: a real-ISO CLI run (bundled
   LMP + committed profiles + generated reference load) must produce a
   report.html — e.g.
   python run_portfolio.py --load data/reference/reference_load_100mw.csv \
     --lmp data/bundled/lmp/MISO_2024_bau_lmp.csv --iso MISO --deltas 1 5 20
   (generate the reference load first if absent). Also run
   scripts/verify_standalone.sh once at the end — it must still pass.
6. Docs in the SAME session: update PLAN.md §6 (flip the MISO/NYISO/NEISO
   gap note to committed) and the docs/handoff/README.md HP-02b/pull-out
   rows. Never leave the status table stale — that omission is why this
   prompt exists.

PUSH DISCIPLINE
Binary files (the emissions Parquets) go through plain `git push` in a
small commit rebased on origin/main — HP-02 proved mcp__github__push_files
mangles bytes >= 0x80 (UTF-8 re-encoding), so do NOT push Parquets through
it. CSVs/docs may use either channel. If a git push 413s once, split the
commit smaller (one ISO per commit) rather than retrying the big pack; use
push_files only for text files.

INVARIANTS
- No `import market_sim` in the tool (grep guard); the bridge script lives
  outside scope2-lce-portfolio/ or is deleted before commit.
- Never modify anything under the parent repo's data/raw/.
- python -m pytest tests/ -q green from scope2-lce-portfolio/ before each
  commit. No PRs, no raw model IDs in commits/code. Imperative
  present-tense commit messages. Finish by listing the bundle inventory
  (files, sizes, keeper ids) and the passing verify output.
```
